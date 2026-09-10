"""Fase 15, Plano 04 — guardião de fronteira do motor de opções.

Este arquivo NÃO testa comportamento de negócio (isso já está coberto em
`test_opcoes_payoff.py`, `test_opcoes_gatilho.py`, `test_opcoes_motor.py`).
Ele guarda invariantes de ARQUITETURA — ENG-03 (sem rede ao b-mcp), ENG-04
(limite `rastrear()`/`avaliar()` trocável) e ENG-05 (canal único com
orçamento) — e falha quando alguém abre um caminho novo, mesmo que esse
caminho novo funcione perfeitamente em si mesmo. O objetivo explícito é
reprovar a próxima pessoa que, precisando de "só mais um dado" dentro do
motor de opções, abrir um `httpx.AsyncClient` novo, subir um client MCP, ou
importar `mydata_client` de um módulo que hoje não tem esse acesso — furando
de uma vez o orçamento de requisições do mydata (60/min · 2.000/dia) e o
princípio 4 do CLAUDE.md (o b-mcp serve dado sintético/fixture em produção;
consumi-lo produziria número financeiro inventado).

2026-09-09 (aba-opcoes F1, ADR-027) — REVERSÃO DELIBERADA DO GUARDIÃO B,
registrada aqui em vez de apagada (guardrail do CLAUDE.md: guardião de teste
não se apaga; reversão deliberada atualiza o guardião com nota).

Os DOIS motivos que o ADR-024 deu para proibir `mcp` caíram:
  (a) "o b-mcp serve fixture em produção" — verdade sobre o PORTAL público
      `b-mcp.semente.dev`, e ele continua fixture. `mcp.semente.dev` é OUTRO
      processo, outro domínio, com dado real do MyData (`fonte: "http"`) e
      porteiro na porta (`client_credentials` no `id.semente.dev`);
  (b) "subir um client MCP stdio dentro do uvicorn" — o transporte do
      serviço é **streamable-http** (um POST, uma resposta, `stateless_http`).
      Não há processo filho, não há stdio, não há sessão para gerir.

O que MUDOU nesta data:
  - Guardião A ganhou `httpx2` na lista de imports proibidos: o SDK novo
    trouxe um segundo stack HTTP e o filtro antigo, por igualdade de nome,
    não o via (`"httpx2" != "httpx"`).
  - Guardião B deixou de ser "NENHUM módulo importa `mcp`" e passou a ser
    "EXATAMENTE UM módulo importa `mcp`/`httpx2`: `mcp_client`" (igualdade
    de conjunto, mesmo desenho do Guardião C).
  - Guardião B-requirements INVERTEU: antes proibia a dependência (T-15-SC do
    15-04-PLAN.md), agora EXIGE `mcp>=2.1,<3` e exige que a linha seja
    idêntica nos dois requirements.
  - Guardiões C, D, E e ENG-04 seguem intocados. O Guardião C (canal único do
    hub mydata) se ESTENDE ao canal MCP: `mcp_client` não importa
    `mydata_client`, e a igualdade de conjunto dele já garante isso.

Todos os guardiões ESTRUTURAIS (A, B, C, ENG-04) usam `ast.parse` sobre o
fonte lido com `pathlib.Path` — nunca busca textual. Um comentário citando
"b-mcp", "semente.dev" ou "httpx" para EXPLICAR a proibição (como os módulos
`opcoes_motor.py`/`opcoes_gatilho.py` já fazem) é legítimo e não pode
reprovar a suíte; só `ast.Constant` de tipo str (literais de verdade,
excluindo docstring) contam. O guardião D é de COMPORTAMENTO (monkeypatch,
exercita o caminho real).
"""
from __future__ import annotations

import ast
import inspect
import pathlib

import pytest

from app import mydata_budget, options_provider_mydata as provider
from app import opcoes_motor, opcoes_payoff, opcoes_gatilho

_APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"

_MODULOS_NOVOS_FASE_15 = ("opcoes_payoff", "opcoes_gatilho", "opcoes_motor")

# Redes/protocolos proibidos dentro do limite (Guardião A). "asyncio" entra
# porque o único uso legítimo de I/O assíncrono nestes módulos seria para
# tocar rede — os três são PUROS por desenho (ver docstrings de topo de cada
# um), então nem `asyncio` deveria aparecer.
# 2026-09-09 (ADR-027): "httpx2" acrescentado — o SDK do serviço MCP traz um
# SEGUNDO stack HTTP, e este filtro compara nome de módulo raiz por igualdade,
# então `"httpx2" != "httpx"` passava batido. Os três módulos puros continuam
# proibidos de tocar rede por QUALQUER stack.
_IMPORTS_PROIBIDOS_REDE = {
    "httpx", "httpx2", "requests", "urllib", "urllib3", "socket", "http",
    "aiohttp", "asyncio", "subprocess", "mcp",
}

# Substrings de string literal que indicam referência ao b-mcp (Guardião A).
_STRINGS_PROIBIDAS_BMCP = ("b-mcp", "bmcp", "semente.dev", "http://", "https://")


def _fonte(caminho: pathlib.Path) -> str:
    return caminho.read_text(encoding="utf-8")


def _arvore(caminho: pathlib.Path) -> ast.AST:
    return ast.parse(_fonte(caminho), filename=str(caminho))


def _imports(caminho: pathlib.Path) -> set[str]:
    """Módulos raiz de TODO `ast.Import`/`ast.ImportFrom` do arquivo,
    incluindo imports dentro de função (ast.walk visita o corpo inteiro) —
    inclusive `from . import x` relativo, onde `node.module` é `None` e o
    nome importado vem de `node.names`."""
    mods: set[str] = set()
    for node in ast.walk(_arvore(caminho)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module.split(".")[0])
            else:
                for alias in node.names:
                    mods.add(alias.name.split(".")[0])
    return mods


def _strings(caminho: pathlib.Path) -> list[str]:
    """Todas as `ast.Constant` de tipo `str` do arquivo, EXCETO docstrings
    (módulo/função/classe) — literais de verdade, não texto explicativo.
    Comentário (`#`) nunca vira nó da AST e já sai de graça; docstring
    (`\"\"\"...\"\"\"`) VIRA nó `ast.Constant`, então precisa de exclusão
    explícita por posição estrutural (primeiro `Expr` do corpo de Module/
    FunctionDef/AsyncFunctionDef/ClassDef) — nunca por valor, para não
    mascarar um literal real que reuse o mesmo texto."""
    arvore = _arvore(caminho)
    ids_docstring = set()
    candidatos_docstring = [arvore] + [
        n for n in ast.walk(arvore)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    for no in candidatos_docstring:
        corpo = getattr(no, "body", None)
        if corpo and isinstance(corpo[0], ast.Expr) and isinstance(corpo[0].value, ast.Constant) \
                and isinstance(corpo[0].value.value, str):
            ids_docstring.add(id(corpo[0].value))

    return [
        node.value
        for node in ast.walk(arvore)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and id(node) not in ids_docstring
    ]


def _modulos_app() -> list[pathlib.Path]:
    return sorted(_APP_DIR.glob("*.py"))


# ─────────────────────────────────────────────────────────────────────────
# GUARDIÃO A (ENG-03) — sem import de rede, sem string de URL/b-mcp, nos
# três módulos novos da Fase 15.
# ─────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("nome_modulo", _MODULOS_NOVOS_FASE_15)
def test_guardiao_a_modulo_novo_nao_importa_rede_nem_httpx(nome_modulo):
    caminho = _APP_DIR / f"{nome_modulo}.py"
    mods = _imports(caminho)
    ofensores = mods & _IMPORTS_PROIBIDOS_REDE
    assert not ofensores, (
        f"{nome_modulo}.py importa {sorted(ofensores)} — proibido pelo "
        f"limite ENG-03 (o motor de opções não fala com rede nem com o "
        f"b-mcp). Se você está tentando buscar mais dado aqui dentro, a "
        f"chamada tem que sair do CHAMADOR de rastrear()/avaliar(), nunca "
        f"de dentro do módulo puro.")


@pytest.mark.parametrize("nome_modulo", _MODULOS_NOVOS_FASE_15)
def test_guardiao_a_modulo_novo_nao_referencia_bmcp_por_string(nome_modulo):
    caminho = _APP_DIR / f"{nome_modulo}.py"
    strings = _strings(caminho)
    ofensoras = [
        s for s in strings
        if any(proibida in s for proibida in _STRINGS_PROIBIDAS_BMCP)
    ]
    assert not ofensoras, (
        f"{nome_modulo}.py tem string literal referenciando b-mcp/URL: "
        f"{ofensoras!r} — o limite ENG-03 proíbe até a MENÇÃO por dado "
        f"(não só a chamada), porque é o primeiro passo de alguém montando "
        f"uma URL de verdade depois.")


# ─────────────────────────────────────────────────────────────────────────
# GUARDIÃO B (ENG-03 → ADR-027) — EXATAMENTE UM módulo de server/app/ fala
# com o serviço MCP, e a dependência é declarada nos DOIS requirements.
#
# Versão anterior (ADR-024, até 2026-09-08): "NENHUM módulo importa `mcp`" e
# "`mcp` NÃO está nos requirements". Os dois caíram com o ADR-027 — o motivo
# está na docstring de topo deste arquivo. A FORMA do guardião mudou junto:
# de denylist (fácil de furar acrescentando módulo) para IGUALDADE DE
# CONJUNTO (mesmo desenho do Guardião C), que reprova tanto o módulo novo que
# importa o SDK quanto o desaparecimento silencioso do `mcp_client`.
# ─────────────────────────────────────────────────────────────────────────
_RAIZES_MCP = {"mcp", "httpx2"}
_IMPORTADORES_PERMITIDOS = {"mcp_client"}


def test_guardiao_b_um_unico_modulo_importa_mcp_e_httpx2():
    importadores = {
        caminho.stem for caminho in _modulos_app()
        if _imports(caminho) & _RAIZES_MCP
    }
    assert importadores == _IMPORTADORES_PERMITIDOS, (
        f"conjunto de módulos que importam {sorted(_RAIZES_MCP)} mudou: "
        f"{sorted(importadores)} != {sorted(_IMPORTADORES_PERMITIDOS)} — "
        f"canal paralelo ao serviço MCP detectado (ADR-027, Decisão 1). O "
        f"cap por usuário, o cache L1, o semáforo de concorrência e a "
        f"tradução de erro moram TODOS em `mcp_client.py`; um segundo "
        f"importador fura os quatro de uma vez e queima o teto de 2.000 "
        f"chamadas/dia, que é COMPARTILHADO por toda a base do Boris. Se "
        f"você precisa genuinamente de um módulo novo aqui, a resposta NÃO é "
        f"editar `_IMPORTADORES_PERMITIDOS` — é levar a decisão ao Alex "
        f"(mudança arquitetural).")


def test_guardiao_b_mcp_esta_nos_requirements_e_igual_nos_dois():
    """INVERTIDO em 2026-09-09 (aba-opcoes F1, ADR-027). O teste anterior
    (`test_guardiao_b_mcp_nao_esta_nos_requirements`) PROIBIA a dependência,
    pelo threat T-15-SC do 15-04-PLAN.md; o ADR-027 inverteu a decisão e o SDK
    passou a ser dependência nominal do contrato do serviço. O que este
    guardião protege AGORA é a divergência entre os dois arquivos: produção
    resolvendo uma faixa diferente da que a suíte exercitou é o modo
    silencioso de o build publicado não ser o que foi verificado."""
    server_dir = _APP_DIR.parent
    encontradas = {}
    for nome_arquivo in ("requirements.txt", "requirements-prod.txt"):
        conteudo = (server_dir / nome_arquivo).read_text(encoding="utf-8")
        linhas_mcp = [
            linha.strip() for linha in conteudo.splitlines()
            if linha.strip() and not linha.strip().startswith("#")
            and linha.strip().lower().startswith("mcp")
        ]
        assert len(linhas_mcp) == 1, (
            f"{nome_arquivo} deveria declarar EXATAMENTE uma linha de `mcp`, "
            f"tem {len(linhas_mcp)}: {linhas_mcp} — o ADR-027 exige a "
            f"dependência declarada uma vez só, sem linha duplicada com "
            f"faixa diferente.")
        encontradas[nome_arquivo] = linhas_mcp[0]

    dev = encontradas["requirements.txt"]
    prod = encontradas["requirements-prod.txt"]
    assert dev == prod, (
        f"a linha do `mcp` diverge entre os requirements: {dev!r} (dev/test) "
        f"× {prod!r} (prod) — produção resolveria uma versão do SDK que a "
        f"suíte nunca exercitou.")
    assert ">=2.1" in dev and "<3" in dev, (
        f"a faixa do `mcp` deixou de ser `>=2.1,<3` ({dev!r}) — `>=2.1` é o "
        f"piso que o contrato do serviço nomeia (streamable-http com tupla de "
        f"DOIS fluxos e resposta em snake_case); `<3` trava a próxima major, "
        f"que pode mudar a forma da resposta sem aviso.")


# ─────────────────────────────────────────────────────────────────────────
# GUARDIÃO C (ENG-05) — allowlist do canal único que fala com o hub mydata.
# ─────────────────────────────────────────────────────────────────────────
def test_guardiao_c_canal_unico_para_mydata_client():
    # Allowlist, não denylist: qualquer módulo NOVO que passe a falar com o
    # hub reprova este teste e obriga uma decisão consciente — o orçamento
    # de requisições do mydata (60/min · 2.000/dia) só é defensável enquanto
    # houver um caminho só até `mydata_client.py`. Se este teste falhou
    # porque você genuinamente precisa de um módulo novo aqui, a resposta
    # não é editar a allowlist — é levar a decisão para o Alex (Rule 4 do
    # executor: mudança arquitetural).
    allowlist = {"candle_provider", "options_provider_mydata", "mydata_budget"}
    importadores = {
        caminho.stem
        for caminho in _modulos_app()
        if "mydata_client" in _imports(caminho)
    }
    assert importadores == allowlist, (
        f"conjunto de módulos que importam mydata_client mudou: "
        f"{sorted(importadores)} != allowlist {sorted(allowlist)} — canal "
        f"paralelo ao hub mydata detectado (ENG-05).")


# ─────────────────────────────────────────────────────────────────────────
# GUARDIÃO D (ENG-05) — comportamento: sem cota reservada, nenhuma
# requisição sai. Reusa o padrão de monkeypatch já estabelecido em
# test_options_provider_mydata.py.
# ─────────────────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def _estado_limpo():
    provider._cache.clear()
    mydata_budget.reset()
    yield
    provider._cache.clear()
    mydata_budget.reset()


def test_guardiao_d_reservar_false_impede_toda_requisicao_de_rede(monkeypatch):
    chamadas_venc = []
    chamadas_chain = []

    async def _espiao_vencimentos(ticker, pregao=None, *, fetch_json=None):
        chamadas_venc.append(ticker)
        return [{"dt_vencimento": "2026-09-19", "vence_no_pregao": 0}]

    async def _espiao_chain(ticker, vencimento=None, pregao=None, tipo=None, *, fetch_json=None):
        chamadas_chain.append(ticker)
        return []

    monkeypatch.setattr(provider.mydata_client, "get_vencimentos", _espiao_vencimentos)
    monkeypatch.setattr(provider.mydata_client, "get_options_chain", _espiao_chain)
    monkeypatch.setattr(mydata_budget, "reservar", lambda n=1, now=None: False)

    import asyncio
    data = asyncio.run(provider.get_options("PETR4"))

    assert data["providerStatus"] == "degraded"
    assert chamadas_venc == [], "sem cota reservada, get_vencimentos NUNCA deveria ser chamado"
    assert chamadas_chain == [], "sem cota reservada, get_options_chain NUNCA deveria ser chamado"


# ─────────────────────────────────────────────────────────────────────────
# GUARDIÃO E (ENG-05) — o ponto de commit é `reservar()`, nunca `debita()`
# direto. Regressão exata do WR-01 (PR #28): `debita()` sozinho é
# check-then-act sem lock.
# ─────────────────────────────────────────────────────────────────────────
def test_guardiao_e_debita_do_provider_usa_reservar_nao_debita_direto():
    caminho = _APP_DIR / "options_provider_mydata.py"
    arvore = _arvore(caminho)
    funcao = None
    for node in ast.walk(arvore):
        if isinstance(node, ast.FunctionDef) and node.name == "_debita":
            funcao = node
            break
    assert funcao is not None, "options_provider_mydata._debita não existe mais — guardião desatualizado"

    nomes_chamados = {
        n.attr for n in ast.walk(funcao) if isinstance(n, ast.Attribute)
    }
    assert "reservar" in nomes_chamados, (
        "_debita() não referencia mydata_budget.reservar() — o commit "
        "atômico do WR-01 (PR #28) precisa continuar sendo por reservar(), "
        "não pode virar debita() solto de novo (check-then-act sem lock).")
    assert "debita" not in nomes_chamados, (
        "_debita() chama mydata_budget.debita() DIRETO — é exatamente a "
        "condição de corrida do WR-01 que o PR #28 fechou (check-then-act "
        "sem lock). O commit tem que passar por reservar().")


# ─────────────────────────────────────────────────────────────────────────
# GUARDIÃO ENG-04 — a trocabilidade de rastrear()/avaliar() tem de ser
# ESTRUTURAL, não só documentada em comentário. Três frentes: assinatura
# congelada, allowlist de imports, e ausência de relógio.
# ─────────────────────────────────────────────────────────────────────────
def test_eng04_assinatura_de_rastrear_esta_congelada():
    parametros = list(inspect.signature(opcoes_motor.rastrear).parameters)
    assert parametros == ["cadeia", "filtros"], (
        f"opcoes_motor.rastrear mudou de assinatura para {parametros} — "
        f"ENG-04 exige (cadeia, filtros) exatamente nessa ordem. Renomear "
        f"ou acrescentar parâmetro posicional quebra todo chamador na hora "
        f"da troca pelo b-mcp (find_tradable_options); é por isso que a "
        f"assinatura está congelada.")


def test_eng04_assinatura_de_avaliar_esta_congelada():
    parametros = list(inspect.signature(opcoes_motor.avaliar).parameters)
    assert parametros == ["pernas"], (
        f"opcoes_motor.avaliar mudou de assinatura para {parametros} — "
        f"ENG-04 exige (pernas) exatamente. Renomear ou acrescentar "
        f"parâmetro posicional quebra todo chamador na hora da troca pelo "
        f"b-mcp (evaluate_option_structure); é por isso que a assinatura "
        f"está congelada.")


def test_eng04_limite_trocavel_opcoes_motor_imports_na_allowlist():
    # Um import fora dela significa que o motor passou a depender de
    # estado do Boris (carteira, sessão, texto, relógio) e a troca do
    # CORPO por uma chamada de rede (ADR-024, quando plano-mcp-servico.md
    # for aprovado) deixou de ser possível sem redesenho.
    allowlist = {"options_quant", "opcoes_payoff", "typing", "__future__"}
    caminho = _APP_DIR / "opcoes_motor.py"
    mods = _imports(caminho)
    ofensores = mods - allowlist
    assert not ofensores, (
        f"opcoes_motor.py importa {sorted(ofensores)}, fora da allowlist "
        f"{sorted(allowlist)} — ENG-04 exige que o limite trocável não "
        f"conheça carteira/sessão/db/auth/texto de UI, senão a troca do "
        f"corpo por chamada remota deixa de ser drop-in.")


def test_eng04_limite_trocavel_opcoes_motor_sem_relogio():
    # Relógio dentro do limite tornaria rastrear()/avaliar() não-
    # determinísticas e não-reproduzíveis pelo lado remoto (b-mcp não teria
    # como replicar "agora" do processo do Boris).
    nomes_proibidos = {"datetime", "date", "time", "now", "today"}
    caminho = _APP_DIR / "opcoes_motor.py"
    arvore = _arvore(caminho)
    nomes_usados = {
        n.id for n in ast.walk(arvore) if isinstance(n, ast.Name)
    } | {
        n.attr for n in ast.walk(arvore) if isinstance(n, ast.Attribute)
    } | {
        alias.asname or alias.name.split(".")[0]
        for n in ast.walk(arvore)
        if isinstance(n, (ast.Import, ast.ImportFrom))
        for alias in n.names
    }
    ofensores = nomes_usados & nomes_proibidos
    assert not ofensores, (
        f"opcoes_motor.py referencia {sorted(ofensores)} — relógio dentro "
        f"do limite ENG-04 tornaria rastrear()/avaliar() não-"
        f"reproduzíveis; o dado de tempo (se algum dia precisar) tem que "
        f"vir de fora, como argumento explícito do chamador.")
