"""aba-opcoes F1 (ADR-027) — rotas do serviço MCP autenticado.

O que este módulo É: a camada HTTP da aba Opções. Ele decide QUEM pode
chamar (sessão obrigatória), QUANTO pode chamar (cap por usuário/dia,
ancorado em São Paulo) e COMO a falha vira resposta (nada cai no handler
500). Todo o diálogo com o serviço mora em `mcp_client.py`.

O que este módulo NÃO faz: nenhuma conta financeira, nenhum número
fabricado. `pregao` é `None` quando a resposta não traz pregão — princípio 4
do CLAUDE.md: dado que falta é dado que falta, nunca um valor inventado.

Fase 1 entrega SÓ `GET /status`. As rotas de leitura, cadeia, proposta,
possibilidades, veredito e setups são as Fases 2–5 do
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
        warning = "frescor não medido: a classe negociacao_b3 não veio na resposta"
    bloqueia = bool(warning) or (critica is not None and critica.get("situacao") != EM_DIA)

    return {
        "classes": classes,
        "stale": stale,
        "warning": warning or None,
        "bloqueia": bool(bloqueia),
        "bruto": sc,
    }


# --------------------------------------------------------------------------
# Rota.
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
        obslog.log("mcp", "status falhou", level="warn",
                   rota="/api/options/mcp/status", uid=uid, erro=type(e).__name__)
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
        "at": datetime.now(BRT).strftime("%d/%m/%Y %H:%M") + " BRT",
        "frescor": frescor,
        "cap": {
            "usado": metering.used(_conn, uid, section=SECTION, _dia=_dia_sp()),
            "limite": _cota_usuario(),
            "reinicia": RESET_TXT,
        },
    }
