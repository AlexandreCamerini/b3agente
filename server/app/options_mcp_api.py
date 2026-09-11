"""aba-opcoes F1 (ADR-027) — rotas do serviço MCP autenticado.

O que este módulo É: a camada HTTP da aba Opções. Ele decide QUEM pode
chamar (sessão obrigatória), QUANTO pode chamar (cap por usuário/dia,
ancorado em São Paulo) e COMO a falha vira resposta (nada cai no handler
500). Todo o diálogo com o serviço mora em `mcp_client.py`.

O que este módulo NÃO faz: nenhuma conta financeira, nenhum número
fabricado. `pregao` é `None` quando a resposta não traz pregão — princípio 4
do CLAUDE.md: dado que falta é dado que falta, nunca um valor inventado.

Fase 1 entregou `GET /status`. A Fase 2 (quick 260910-biz) acrescenta
`GET /leitura/{ticker}` e `GET /setups/{name}/grafico`. Cadeia, proposta,
possibilidades, veredito e criação de setups são as Fases 3–5 do
`docs/PLANO-aba-opcoes.md`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from . import mcp_client, metering, obslog

router = APIRouter(prefix="/api/options/mcp", tags=["options-mcp"])

# Fuso local ao módulo, mesmo padrão de `store.py`/`brapi.py`/`obslog.py`: o
# Brasil não tem horário de verão desde 2019, e não existe módulo
# compartilhado de fuso no repo. O container do Railway roda em UTC — sem
# isto, o dia do cap viraria 3 h antes do reset do serviço.
BRT = timezone(timedelta(hours=-3))

# Texto do contrato, literal. O que o usuário lê tem de ser o mesmo horário
# que o serviço de fato usa para zerar o contador dele.
RESET_TXT = "00:00 America/Sao_Paulo"

# Seções PRÓPRIAS de kv. `mcpUsageMonth` separado de `aiUsageMonth` não é
# arrumação: sem ele, uma sessão na aba Opções queimaria o balde mensal de
# análises do plano comercial do usuário (ADR-010) a cada chamada de tool.
SECTION = "mcpUsage"
GLOBAL_SECTION = "mcpUsageGlobal"
MONTH_SECTION = "mcpUsageMonth"

FONTE = "mcp.semente.dev"
CLASSE_CRITICA = "negociacao_b3"
EM_DIA = "em_dia"

# Avisos de frescor, extraídos para constante na F2 (quick 260910-biz): eram
# literal inline dentro de `_frescor`, sem cobertura do guardião imperativo.
# Os dois dizem "não medido" com a razão do não-medido — e nenhum dos dois
# pode ser suprimido na UI, porque "não medido" que vira silêncio é lido
# como "em dia" (ADR-027, Decisão 8).
AVISO_FRESCOR_NAO_MEDIDO = (
    "frescor não medido: a classe negociacao_b3 não veio na resposta"
)
AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA = (
    "frescor não medido nesta leitura: nenhum setup deste ticker foi avaliado"
)
AVISOS = AVISO_FRESCOR_NAO_MEDIDO + "\n" + AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA

_conn = None
_require_user = None


def configure(conn, require_user_dep) -> None:
    """Injeção pelo mesmo padrão de `candle_cache.configure_db` /
    `setups.set_historico_provider`: `main.py` importa este módulo e entrega
    a conexão e a dependency de sessão. O inverso (este módulo importar
    `main`) seria import circular — `require_user` e `_conn` nascem lá."""
    global _conn, _require_user
    _conn = conn
    _require_user = require_user_dep


def require_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """Delegação ao `require_user` de `main.py`, injetado por `configure()`.

    O nome é o mesmo de propósito, e por dois motivos que apontam para o
    mesmo lugar: (a) é literalmente a MESMA checagem de sessão, e (b) é o
    nome que `test_adr013_cobertura_rotas` reconhece como gate de identidade
    — chamar de outra coisa faria a rota parecer "sem gate" para o guardião
    e obrigaria a mexer na allowlist pública, que é exatamente o que não
    pode acontecer numa rota autenticada."""
    if _require_user is None:
        raise HTTPException(503, {
            "code": "mcp_nao_configurado",
            "message": "Serviço de opções não configurado no servidor.",
            "action": "O router não foi fiado no boot (options_mcp_api.configure).",
        })
    return _require_user(authorization)


# --------------------------------------------------------------------------
# Envs — lidas A CADA chamada (o Railway muda env sem redeploy do código, e o
# teste usa `monkeypatch.setenv`). Valor torto cai no default: env inválida
# não pode derrubar a rota nem, pior, desligar o cap.
# --------------------------------------------------------------------------
def _int_env(nome: str, padrao: int) -> int:
    try:
        v = int(os.environ.get(nome) or padrao)
    except (TypeError, ValueError):
        return padrao
    return v if v > 0 else padrao


def _cota_usuario() -> int:
    return _int_env("B3_MCP_COTA_USUARIO_DIA", 60)


def _rate_min() -> int:
    return _int_env("B3_MCP_RATE_MIN", 20)


def _cota_global() -> int:
    return _int_env("B3_MCP_COTA_GLOBAL_DIA", 1800)


# --------------------------------------------------------------------------
# Dia/mês em São Paulo. `agora` só existe para o teste fixar o relógio sem
# monkeypatch de `datetime`.
# --------------------------------------------------------------------------
def _dia_sp(agora: Optional[datetime] = None) -> str:
    return (agora or datetime.now(timezone.utc)).astimezone(BRT).strftime("%Y-%m-%d")


def _mes_sp(agora: Optional[datetime] = None) -> str:
    return (agora or datetime.now(timezone.utc)).astimezone(BRT).strftime("%Y-%m")


# --------------------------------------------------------------------------
# Cap.
# --------------------------------------------------------------------------
def _cap_check(uid: str, custo: int) -> None:
    """Recusa ANTES de chamar o serviço — o teto de 2.000/dia é compartilhado
    por toda a base do Boris, e uma chamada recusada pelo serviço já teria
    custado a viagem."""
    if custo <= 0:
        return
    dia = _dia_sp()
    ok, _motivo = metering.check(
        _conn, uid,
        quota=_cota_usuario(), rate_per_min=_rate_min(), custo=custo,
        cap_global=_cota_global(),
        section=SECTION, global_section=GLOBAL_SECTION, _dia=dia,
    )
    if ok:
        return
    # O `_motivo` do metering é DESCARTADO de propósito: o texto dele fala de
    # BYOK e de "análises com a IA do app", que não é o que aconteceu aqui.
    # Mandar esse copy na aba Opções mandaria o usuário configurar uma chave
    # de LLM que não resolveria nada (§3.2 do PLANO).
    raise HTTPException(402, {
        "code": "mcp_cota",
        "message": "Cota do dia da aba Opções esgotada.",
        "usado": metering.used(_conn, uid, section=SECTION, _dia=dia),
        "limite": _cota_usuario(),
        "reinicia": RESET_TXT,
    })


def _cap_consume(uid: str, custo: int) -> None:
    if custo <= 0:
        return
    metering.consume(
        _conn, uid, custo=custo,
        section=SECTION, global_section=GLOBAL_SECTION,
        month_section=MONTH_SECTION,
        _dia=_dia_sp(), _mes=_mes_sp(),
    )


# --------------------------------------------------------------------------
# Tradução de erro. NADA cai no handler 500.
# --------------------------------------------------------------------------
def _erro_http(e: Exception) -> HTTPException:
    if isinstance(e, mcp_client.McpNaoConfigurado) or isinstance(e, ValueError):
        # ValueError aqui só vem de `mcp_client.url()` com `MCP_URL` de
        # esquema inválido — é estado de configuração do servidor, mesma
        # classe de "falta credencial", e não pode virar 500 opaco.
        return HTTPException(503, {
            "code": "mcp_nao_configurado",
            "message": "Serviço de opções não configurado no servidor.",
            "action": "Defina MCP_CLIENT_ID e MCP_CLIENT_SECRET no Railway.",
        })
    if isinstance(e, mcp_client.McpTetoAtingido):
        return HTTPException(402, {
            "code": "mcp_teto_servico",
            "message": "O serviço de opções atingiu o teto de chamadas do dia.",
            "reinicia": e.data.get("reinicia"),
            "escopo": e.data.get("escopo"),
        })
    if isinstance(e, mcp_client.McpErroDeTool):
        return HTTPException(422, {
            "code": "mcp_erro_de_tool",
            "message": str(e),
            "available": e.available,
            "hint": e.hint,
        })
    # McpNaoAutorizado e McpIndisponivel caem juntos, e o texto NÃO tem
    # número nem nome de credencial: para o usuário final os dois são "não
    # deu agora". O detalhe (que separa "credencial recusada" de "serviço
    # fora do ar") vai só para o obslog, onde o Alex enxerga.
    return HTTPException(503, {
        "code": "mcp_indisponivel",
        "message": "O serviço de opções não respondeu agora. Tente de novo em alguns minutos.",
    })


# --------------------------------------------------------------------------
# Frescor. Tolerante à FORMA: a resposta real de `check_data_freshness` só se
# confirma ao vivo (`test_mcp_vivo.py`), e adivinhar campo seria inventar
# dado. Por isso o `bruto` volta inteiro — a Fase 2 lê a forma real dali sem
# gastar outra chamada.
# --------------------------------------------------------------------------
_CHAVES_COLECAO = ("classes", "class_status", "dados", "status")
_CHAVES_NOME = ("classe", "class", "nome", "name")
_CHAVES_SITUACAO = ("situacao", "status", "estado", "situation")


def _situacao_de(info) -> Optional[str]:
    if isinstance(info, str):
        return info
    if isinstance(info, dict):
        for chave in _CHAVES_SITUACAO:
            v = info.get(chave)
            if isinstance(v, str):
                return v
    return None


def _colecao_de(sc: Optional[dict]):
    for chave in _CHAVES_COLECAO:
        v = (sc or {}).get(chave)
        if isinstance(v, (list, dict)) and v:
            return v
    return None


def _normaliza_classes(colecao) -> list:
    itens = []
    if isinstance(colecao, dict):
        for nome, info in colecao.items():
            itens.append({"classe": str(nome), "situacao": _situacao_de(info), "bruto": info})
    elif isinstance(colecao, list):
        for item in colecao:
            nome = None
            if isinstance(item, dict):
                for chave in _CHAVES_NOME:
                    if item.get(chave):
                        nome = item[chave]
                        break
            itens.append({
                "classe": str(nome) if nome else None,
                "situacao": _situacao_de(item),
                "bruto": item,
            })
    return itens


def _frescor(sc: Optional[dict], erro: Optional[str]) -> dict:
    sc = sc if isinstance(sc, dict) else None
    classes = _normaliza_classes(_colecao_de(sc))
    stale = [c for c in classes if c.get("situacao") != EM_DIA]
    critica = next((c for c in classes if c.get("classe") == CLASSE_CRITICA), None)

    warning = erro or (sc or {}).get("warning")
    if not warning and critica is None:
        # "não medido" NUNCA pode passar por "em dia" (ADR-027, Decisão 8).
        warning = AVISO_FRESCOR_NAO_MEDIDO
    bloqueia = bool(warning) or (critica is not None and critica.get("situacao") != EM_DIA)

    return {
        "classes": classes,
        "stale": stale,
        "warning": warning or None,
        "bloqueia": bool(bloqueia),
        # `medido` (F2, aditiva): a UI precisa separar TRÊS estados — em dia,
        # atrasado com idade real, e não medido. Sem esta chave a tela teria
        # de deduzir "não medido" raspando o texto do `warning`, e um dia o
        # texto muda e a tela passa a afirmar "em dia" por default. Verdadeira
        # só quando a classe crítica veio E nenhum erro de tool atrapalhou.
        "medido": bool(critica is not None and not erro),
        "bruto": sc,
    }


def _frescor_da_avaliacao(evaluate_dados: Optional[dict], chamou_evaluate: bool) -> dict:
    """Frescor do `/leitura` derivado do que `evaluate_setups` JÁ devolveu.

    **Por que não há `check_data_freshness` aqui:** o custo declarado da rota
    no ADR-027 §3.3 é **3**, e `_cap_check(uid, 3)` é a promessa que o
    usuário paga. Uma quarta chamada faria o cap prometer menos do que o
    consumo real — o teto de 2.000/dia é compartilhado por toda a base, e
    subestimar o consumo é exatamente como ele estoura em silêncio. O frescor
    MEDIDO de verdade continua vindo do `/status` (cache 600 s), que a tela
    chama junto. E "não medido" nunca passa por "em dia" (ADR-027, Decisão 8):
    quando não há medição, `medido` é falso e `bloqueia` é verdadeiro.

    Devolve as MESMAS chaves de `_frescor` de propósito: o front tem UM
    renderizador de frescor, não dois que divergem com o tempo.
    """
    dados = evaluate_dados if isinstance(evaluate_dados, dict) else {}
    df = dados.get("data_freshness")

    if isinstance(df, dict) and df:
        situacao = df.get("quotes")
        situacao = situacao if isinstance(situacao, str) else "desconhecido"
        idade = df.get("quotes_age_hours")
        classe = {
            "classe": CLASSE_CRITICA,
            "situacao": situacao,
            # idade real quando o serviço mandou; `None` quando não mandou —
            # nunca 0, que a tela leria como "acabou de atualizar".
            "idadeHoras": idade if isinstance(idade, (int, float)) else None,
            "bruto": df,
        }
        classes = [classe]
        return {
            "classes": classes,
            "stale": [c for c in classes if c.get("situacao") != EM_DIA],
            "warning": None,
            "bloqueia": situacao != EM_DIA,
            "medido": situacao != "desconhecido",
            "bruto": df,
        }

    if chamou_evaluate and dados.get("status") == "nao_avaliado":
        # Gate de frescor do próprio serviço: o `reason` vai VERBATIM, sem
        # reescrita ([R-15] do PLANO). Quem explica o motivo é quem mediu.
        motivo = dados.get("reason")
        return {
            "classes": [],
            "stale": [],
            "warning": motivo if isinstance(motivo, str) and motivo else AVISO_FRESCOR_NAO_MEDIDO,
            "bloqueia": True,
            "medido": False,
            "bruto": dados,
        }

    return {
        "classes": [],
        "stale": [],
        "warning": (AVISO_FRESCOR_NAO_MEDIDO if chamou_evaluate
                    else AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA),
        "bloqueia": True,
        "medido": False,
        "bruto": None,
    }


# --------------------------------------------------------------------------
# Envelope comum e chamada com cap.
# --------------------------------------------------------------------------
def _agora_brt() -> str:
    return datetime.now(BRT).strftime("%d/%m/%Y %H:%M") + " BRT"


def _cap_bloco(uid: str) -> dict:
    return {
        "usado": metering.used(_conn, uid, section=SECTION, _dia=_dia_sp()),
        "limite": _cota_usuario(),
        "reinicia": RESET_TXT,
    }


async def _chamada_com_cap(uid: str, nome: str, args: dict) -> tuple:
    """Uma chamada de tool + o consumo de 1 do cap. Devolve `(dados, cache)`.

    Duas regras de consumo, herdadas do `/status` da F1:
    · **acerto de cache não consome** — o custo que o cap protege é a chamada
      ao serviço, e ela não aconteceu;
    · **chamada que termina em exceção não consome** — inclusive
      `McpErroDeTool`, porque o `_cap_consume` fica depois do `await` e a
      exceção o pula. É uma decisão a avalizar (SUMMARY da F2): dá para
      inverter em uma linha se o Alex preferir cobrar a viagem que a tool
      recusou.
    """
    r = await mcp_client.call_tool(nome, args)
    if not r.cache:
        _cap_consume(uid, 1)
    return (r.dados if isinstance(r.dados, dict) else {}), bool(r.cache)


def _registros_do_ticker(lista: Optional[dict], alvo: str) -> list:
    """Pares `(setup, registro)` de `list_setups` cujo ticker bate com `alvo`.
    Registro torto (sem `setup`, sem ticker) é ignorado — não vira item vazio
    na tela."""
    fora = []
    for item in (lista or {}).get("setups") or []:
        if not isinstance(item, dict):
            continue
        setup = item.get("setup")
        setup = setup if isinstance(setup, dict) else {}
        t = str(setup.get("ticker") or "").strip().upper()
        if not t or t != alvo:
            continue
        fora.append((setup, item))
    return fora


# --------------------------------------------------------------------------
# Rotas.
# --------------------------------------------------------------------------
@router.get("/status")
async def status(user: dict = Depends(require_user)) -> dict:
    """Estado do dado do serviço de opções: pregão, frescor por classe e o
    saldo do cap do dia.

    Erro de TOOL aqui responde **200**, não 422 — decisão registrada no
    ADR-027 ("Decisão de implementação (Fase 1)"). A finalidade de `/status`
    é reportar o estado do dado; devolver 422 faria a tela não saber dizer
    nada, e "idade desconhecida" viraria silêncio, que é o mesmo que "em
    dia" para quem olha. O 422 segue valendo em `_erro_http`, usado pelas
    rotas de leitura das Fases 2+, onde o erro da tool é falha do pedido.
    """
    uid = user["id"]
    _cap_check(uid, 1)

    erro_tool = None
    r = None
    try:
        r = await mcp_client.call_tool("check_data_freshness", {})
    except mcp_client.McpErroDeTool as e:
        erro_tool = str(e)
    except (mcp_client.McpErro, ValueError) as e:
        # `detalhe=str(e)` (achado A-03): o nome da classe sozinho não separa
        # "emissor recusou" de "conexão fechada" de "erro de protocolo", e o
        # diagnóstico ficava dedutivo. É seguro logar: as mensagens do
        # `mcp_client` são livres de segredo por construção (docstring de topo
        # do módulo, e o guardião T-waw-01 em `test_mcp_client.py` prova).
        obslog.log("mcp", "status falhou", level="warn",
                   rota="/api/options/mcp/status", uid=uid,
                   erro=type(e).__name__, detalhe=str(e))
        raise _erro_http(e)

    sc = r.dados if (r is not None and isinstance(r.dados, dict)) else None
    if r is not None and not r.cache:
        # Acerto de cache não gasta cap: o custo que o cap protege é a
        # chamada ao serviço, e ela não aconteceu.
        _cap_consume(uid, 1)

    frescor = _frescor(sc, erro_tool)
    obslog.log("mcp", "status", rota="/api/options/mcp/status", uid=uid,
               cache=bool(r is not None and r.cache), bloqueia=frescor["bloqueia"])

    return {
        # `None` quando a resposta não traz pregão — nunca uma data
        # fabricada (princípio 4 do CLAUDE.md).
        "pregao": (sc or {}).get("trading_date") or (sc or {}).get("pregao") or None,
        "fonte": FONTE,
        "at": _agora_brt(),
        "frescor": frescor,
        "cap": _cap_bloco(uid),
    }


@router.get("/leitura/{ticker}")
async def leitura(ticker: str, user: dict = Depends(require_user)) -> dict:
    """Leitura de um ticker: comportamento recente, catálogo de estruturas,
    vencimentos e os setups GRAVADOS daquele ticker com a avaliação do dia.

    Custo declarado 3 (ADR-027 §3.3): `propose_option_setups`, `list_setups`
    e `evaluate_setups`. A terceira é PULADA quando o ticker não tem nenhum
    setup gravado — consumir menos que o checado é sempre permitido, o
    contrário não.

    Nada aqui é calculado: `behavior`, `catalog`, `expirations`, `conditions`
    e o `reason` do gate de frescor viajam VERBATIM. Campo que não veio é
    `None` — nunca 0, nunca lista inventada (princípio 4 do CLAUDE.md).
    """
    uid = user["id"]
    _cap_check(uid, 3)

    alvo = (ticker or "").strip().upper()
    rota = "/api/options/mcp/leitura/{ticker}"

    passo = "propose_option_setups"
    chamou_evaluate = False
    cache_tudo = True
    try:
        proposta, c1 = await _chamada_com_cap(uid, "propose_option_setups", {"ticker": alvo})
        cache_tudo = cache_tudo and c1

        passo = "list_setups"
        lista, c2 = await _chamada_com_cap(uid, "list_setups", {})
        cache_tudo = cache_tudo and c2
        registros = _registros_do_ticker(lista, alvo)

        avaliacao_dados: Optional[dict] = None
        if registros:
            passo = "evaluate_setups"
            avaliacao_dados, c3 = await _chamada_com_cap(uid, "evaluate_setups", {})
            cache_tudo = cache_tudo and c3
            chamou_evaluate = True
    except (mcp_client.McpErro, ValueError) as e:
        # `McpErroDeTool` INCLUSIVE: aqui o erro da tool é falha do PEDIDO
        # (ticker inexistente, sem cotações), não um estado a exibir — vira
        # 422 por `_erro_http`. O 200-com-`bloqueia` é exclusividade do
        # `/status`, cuja finalidade é justamente reportar estado do dado.
        obslog.log("mcp", "leitura falhou", level="warn", rota=rota, uid=uid,
                   ticker=alvo, passo=passo, erro=type(e).__name__,
                   detalhe=str(e))  # A-03 — ver nota em `/status`
        raise _erro_http(e)

    avaliacoes = {}
    nao_avaliado = None
    if isinstance(avaliacao_dados, dict):
        if avaliacao_dados.get("status") == "nao_avaliado":
            # Gate de frescor do serviço: ninguém foi avaliado. O motivo vai
            # VERBATIM ([R-15]) e NENHUM cartão recebe veredito — "não armado"
            # por ausência de avaliação seria afirmação sem medição.
            nao_avaliado = {"reason": avaliacao_dados.get("reason")}
        else:
            # `sem_setups` NÃO é bloqueio: é a ausência de setup, que a tela
            # já mostra como estado vazio com motivo.
            for av in avaliacao_dados.get("evaluations") or []:
                if isinstance(av, dict) and av.get("name"):
                    avaliacoes[av["name"]] = av

    setups = []
    for setup, registro in registros:
        nome = setup.get("name")
        av = avaliacoes.get(nome) if nome else None
        setups.append({
            "name": nome,
            "ticker": alvo,
            # `status` do REGISTRO (`ativo`/`inativo`). NÃO é o status da
            # AVALIAÇÃO (`avaliado`/`nao_avaliavel`/`expirado`/…), que vive
            # em `avaliacao.status` — confundir os dois faria a tela dizer
            # "ativo" onde o serviço disse "não consegui avaliar".
            "status": registro.get("status"),
            "avaliacao": av,
            "armed": av.get("armed") if av else None,
            "streak": av.get("streak") if av else None,
            # Sem avaliação, o `required_streak` cai no `consecutive_days`
            # DECLARADO no próprio setup — valor que o usuário escreveu, não
            # número calculado. Não é fabricação.
            "required_streak": (av.get("required_streak") if av
                                else setup.get("consecutive_days")),
            "conditions": av.get("conditions") if av else None,
            "backtest_na_criacao": registro.get("backtest_na_criacao"),
        })

    frescor = _frescor_da_avaliacao(avaliacao_dados, chamou_evaluate)
    obslog.log("mcp", "leitura", rota=rota, uid=uid, ticker=alvo,
               setups=len(setups), avaliou=chamou_evaluate,
               cache=cache_tudo, bloqueia=frescor["bloqueia"])

    return {
        "ticker": alvo,
        # `None` quando nenhuma das respostas trouxe pregão — nunca uma data
        # fabricada (princípio 4 do CLAUDE.md).
        "pregao": (proposta.get("trading_date")
                   or (avaliacao_dados or {}).get("trading_date")
                   or None),
        "fonte": FONTE,
        "at": _agora_brt(),
        # Verbatim, sem interpretar: `behavior` pode ser
        # `{"status": "sem_candles"}` e a tela tem estado próprio para isso.
        "behavior": proposta.get("behavior"),
        "catalog": proposta.get("catalog"),
        "expirations": proposta.get("expirations"),
        "setups": setups,
        "setupsNaoAvaliados": nao_avaliado,
        "frescor": frescor,
        "cap": _cap_bloco(uid),
    }


@router.get("/setups/{name}/grafico")
async def setup_grafico(name: str, user: dict = Depends(require_user)) -> dict:
    """Série de candles de um setup gravado, com os índices de disparo.

    **Sem `frescor` nesta rota** — diverge do "toda resposta traz frescor" do
    §3.3 do PLANO, de propósito (decisão travada da F2): o gráfico é o insumo
    do que a leitura JÁ carimbou, e medir frescor aqui exigiria uma segunda
    chamada, quebrando o custo 1 declarado no ADR-027. Quem carimba pregão e
    frescor é o `/leitura` e o `/status`, que a tela chama antes desta.

    Limitação conhecida: nome de setup contendo `/` não resolve aqui —
    `{name}` não é conversor `path`, e transformá-lo em um engoliria o
    `/grafico` do fim da URL. Nome com barra devolve 404 do roteador.
    """
    uid = user["id"]
    _cap_check(uid, 1)

    rota = "/api/options/mcp/setups/{name}/grafico"
    try:
        dados, cache = await _chamada_com_cap(uid, "get_setup_chart", {"name": name})
    except (mcp_client.McpErro, ValueError) as e:
        obslog.log("mcp", "grafico de setup falhou", level="warn", rota=rota,
                   uid=uid, setup=name, erro=type(e).__name__,
                   detalhe=str(e))  # A-03 — ver nota em `/status`
        raise _erro_http(e)

    obslog.log("mcp", "grafico de setup", rota=rota, uid=uid, setup=name, cache=cache)

    # Payload da tool PRIMEIRO, envelope DEPOIS: invertida, a ordem deixaria
    # o `trading_date` do payload sobrescrever o `pregao` do envelope.
    return {
        **dados,
        "pregao": dados.get("trading_date") or None,
        "fonte": FONTE,
        "at": _agora_brt(),
        "cap": _cap_bloco(uid),
    }
