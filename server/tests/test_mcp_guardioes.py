"""aba-opcoes F1 (ADR-027) — guardiões da fronteira do serviço MCP.

Complementa `test_opcoes_fronteira.py`, que guarda os invariantes ANTIGOS
(ENG-03/04/05) e o Guardião B novo (exatamente um importador de
`mcp`/`httpx2`). Aqui ficam os cinco guardiões que nasceram COM o ADR-027:

  (i)   sem literal `"fixture"`, `MYDATA_MODO` ou `b-mcp` nos arquivos da
        fronteira — o portal público continua servindo dado sintético, e o
        ADR-027 só levantou a proibição para o serviço AUTENTICADO;
  (ii)  todo literal de endereço em `mcp_client.py` é um dos dois do
        contrato;
  (iii) nenhum literal com formato de segredo em `server/app/` inteiro;
  (iv)  toda rota `/api/options/mcp/*` passa por `require_user` E pelo cap;
  (v)   todo `metering.consume` do cap leva `month_section="mcpUsageMonth"`.

Estilo AST idêntico ao de `test_opcoes_fronteira.py` — nunca busca textual:
um comentário que CITA a proibição para explicá-la é legítimo e não pode
reprovar a suíte. Os helpers `_imports`/`_strings` são copiados de lá de
propósito (guardião não importa guardião: se um arquivo quebrar, o outro
tem de continuar guardando).
"""
from __future__ import annotations

import ast
import pathlib
import re

import pytest

from .rotas_fastapi import nomes_dependencias, todas_as_rotas

_APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"

# Arquivos da fronteira do ADR-027. Cresce junto com as rotas das Fases 2+.
_ARQUIVOS_DA_FRONTEIRA = ("mcp_client.py", "options_mcp_api.py")


def _arvore(caminho: pathlib.Path) -> ast.AST:
    return ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))


def _modulos_app() -> list[pathlib.Path]:
    return sorted(_APP_DIR.glob("*.py"))


def _imports(caminho: pathlib.Path) -> set[str]:
    """Módulos raiz de TODO import do arquivo, INCLUSIVE os de dentro de
    função — `ast.walk` visita o corpo inteiro."""
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
    """Literais de string de CÓDIGO, excluindo docstring POR POSIÇÃO
    estrutural (primeiro `Expr` do corpo de Module/FunctionDef/
    AsyncFunctionDef/ClassDef) — nunca por VALOR, para não mascarar um
    literal real que reuse o mesmo texto de uma docstring. Comentário (`#`)
    nunca vira nó de AST e já sai de graça."""
    arvore = _arvore(caminho)
    ids_docstring = set()
    candidatos = [arvore] + [
        n for n in ast.walk(arvore)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    for no in candidatos:
        corpo = getattr(no, "body", None)
        if corpo and isinstance(corpo[0], ast.Expr) and isinstance(corpo[0].value, ast.Constant) \
                and isinstance(corpo[0].value.value, str):
            ids_docstring.add(id(corpo[0].value))
    return [
        node.value for node in ast.walk(arvore)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and id(node) not in ids_docstring
    ]


def _caminhos_da_fronteira() -> list[pathlib.Path]:
    return [_APP_DIR / nome for nome in _ARQUIVOS_DA_FRONTEIRA
            if (_APP_DIR / nome).exists()]


# ─────────────────────────────────────────────────────────────────────────
# (i) — a fronteira nova NÃO aponta para o portal de fixture.
# ─────────────────────────────────────────────────────────────────────────
_MARCAS_DE_FIXTURE = ("fixture", "MYDATA_MODO", "b-mcp")


def test_guardiao_i_fronteira_nao_referencia_fixture_nem_o_portal():
    assert _caminhos_da_fronteira(), (
        "nenhum arquivo da fronteira existe — este guardião estaria passando "
        "por vacuidade; atualize `_ARQUIVOS_DA_FRONTEIRA`.")
    ofensores = []
    for caminho in _caminhos_da_fronteira():
        for literal in _strings(caminho):
            for marca in _MARCAS_DE_FIXTURE:
                if marca in literal:
                    ofensores.append((caminho.name, marca, literal))
    assert not ofensores, (
        f"literal de fixture/portal na fronteira do serviço MCP: {ofensores!r} "
        f"— o ADR-027 levantou a proibição do ADR-024 SÓ para o serviço "
        f"autenticado (dado real, `fonte: \"http\"`). O portal público segue "
        f"servindo dado sintético, e consumi-lo produziria número financeiro "
        f"inventado (princípio 4 do CLAUDE.md).")


# ─────────────────────────────────────────────────────────────────────────
# (ii) — o cliente só conhece os dois endereços do contrato.
# ─────────────────────────────────────────────────────────────────────────
def test_guardiao_ii_unicos_enderecos_literais_do_cliente_sao_os_do_contrato():
    """Repare que a régua NÃO é "toda URL": `mcp.semente.dev` SEM esquema é
    rótulo de fonte (a rota devolve isso ao usuário em `fonte`), e é
    legítimo. O que se guarda aqui é o endereço para onde o token pode
    viajar — e ele só pode vir do contrato ou de `MCP_URL` (validada em
    `url()`)."""
    from app import mcp_client

    caminho = _APP_DIR / "mcp_client.py"
    permitidos = {mcp_client.URL_CONTRATO, mcp_client.URL_TOKEN}
    ofensores = [s for s in _strings(caminho) if "://" in s and s not in permitidos]
    assert not ofensores, (
        f"mcp_client.py tem literal de endereço fora do contrato: "
        f"{ofensores!r} — o destino do access token é decidido em UM lugar "
        f"só (`url()`, que exige TLS); endereço solto no código é o começo "
        f"de um canal paralelo sem validação (T-waw-02).")


def test_guardiao_ii_os_dois_enderecos_do_contrato_continuam_presentes():
    """Contra-guardião: se alguém apagar as constantes, o teste acima
    passaria por vacuidade (lista vazia de ofensores)."""
    from app import mcp_client

    literais = _strings(_APP_DIR / "mcp_client.py")
    assert mcp_client.URL_CONTRATO in literais
    assert mcp_client.URL_TOKEN in literais


# ─────────────────────────────────────────────────────────────────────────
# (iii) — nenhum segredo literal em server/app/ inteiro.
# ─────────────────────────────────────────────────────────────────────────
# Chave de máquina legada do contrato (`mcp_<nome>_<token>`, 256 bits em
# base64url) e JWT (o access token do emissor é RS256, começa por `eyJ`).
_FORMATOS_DE_SEGREDO = (
    ("chave de máquina", re.compile(r"mcp_[A-Za-z0-9]+_[A-Za-z0-9_-]{20,}")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}")),
)


@pytest.mark.parametrize("caminho", _modulos_app(), ids=lambda p: p.name)
def test_guardiao_iii_nenhum_literal_com_formato_de_segredo(caminho):
    ofensores = []
    for literal in _strings(caminho):
        for rotulo, padrao in _FORMATOS_DE_SEGREDO:
            if padrao.search(literal):
                ofensores.append((rotulo, literal[:24] + "…"))
    assert not ofensores, (
        f"{caminho.name} tem literal com formato de segredo {ofensores!r} — "
        f"credencial só por env (guardrail do CLAUDE.md e ADR-027, Decisão "
        f"1). Um segredo commitado não se desfaz com um revert: ele já está "
        f"no histórico, e a resposta é rotacionar, não apagar o commit.")


# ─────────────────────────────────────────────────────────────────────────
# (iv) — toda rota do serviço MCP passa por `require_user` E pelo cap.
# ─────────────────────────────────────────────────────────────────────────
# 2026-09-10 (auditoria A-17): estes dois helpers eram cópias locais, com a
# justificativa "guardião não importa guardião" — que continua valendo e é
# atendida de outro jeito: os dois agora lêem de `tests/rotas_fastapi.py`, um
# módulo de INSUMO sem nenhuma asserção, então nenhum guardião depende do
# veredito do outro. Era justamente a DIVERGÊNCIA entre as duas cópias o
# defeito A-17: esta resolvia o router aninhado, a do ADR-013 não, e a do
# ADR-013 — o guardião de segurança — passava cega. Os nomes com `_` são
# preservados: o resto deste arquivo os usa e o histórico cita por nome.
_nomes_dependencias = nomes_dependencias
_todas_as_rotas = todas_as_rotas


def _rotas_do_servico_mcp():
    from app.main import app

    return [r for r in _todas_as_rotas(app.routes)
            if str(getattr(r, "path", "") or "").startswith("/api/options/mcp")]


def _funcoes_de_rota_do_modulo() -> dict:
    """Nome → nó AST das funções decoradas com `@router.<metodo>` em
    `options_mcp_api.py`."""
    fora = {}
    for node in ast.walk(_arvore(_APP_DIR / "options_mcp_api.py")):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            alvo = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(alvo, ast.Attribute) and isinstance(alvo.value, ast.Name) \
                    and alvo.value.id == "router":
                fora[node.name] = node
    return fora


def test_guardiao_iv_toda_rota_mcp_exige_sessao_e_passa_pelo_cap():
    rotas = _rotas_do_servico_mcp()
    assert rotas, (
        "nenhuma rota `/api/options/mcp` registrada no app — este guardião "
        "estaria passando por VACUIDADE, que é o oposto de guardar.")

    funcoes = _funcoes_de_rota_do_modulo()
    assert funcoes, "nenhuma função decorada com @router encontrada em options_mcp_api.py"

    sem_sessao, sem_cap = [], []
    for rota in rotas:
        nomes = _nomes_dependencias(getattr(rota, "dependant", None))
        if "require_user" not in nomes:
            sem_sessao.append((rota.path, sorted(nomes)))

    for nome, no in funcoes.items():
        chamados = {n.id for n in ast.walk(no) if isinstance(n, ast.Name)}
        if "_cap_check" not in chamados:
            sem_cap.append(nome)

    assert not sem_sessao, (
        f"rota(s) do serviço MCP sem `require_user`: {sem_sessao!r} — o "
        f"teto de 2.000 chamadas/dia é do SERVIDOR, não do usuário: rota "
        f"anônima aqui deixa qualquer um queimar a cota de toda a base.")
    assert not sem_cap, (
        f"função(ões) de rota sem `_cap_check`: {sem_cap!r} — sessão sozinha "
        f"não é freio; sem o cap, um laço no cliente de UM usuário logado "
        f"esgota o teto compartilhado (T-waw-03).")


# ─────────────────────────────────────────────────────────────────────────
# (v) — o `consume` do cap NUNCA queima o balde mensal do plano comercial.
# ─────────────────────────────────────────────────────────────────────────
def _constantes_str_do_modulo(arvore) -> dict:
    """Assignments de nível de módulo com valor string literal — permite
    aceitar `month_section=MONTH_SECTION` e ainda assim exigir que o valor
    RESOLVA para `"mcpUsageMonth"`. Aceitar o Name sem resolver deixaria
    `month_section=OUTRA_COISA` passar; exigir o literal na chamada
    duplicaria a constante. Resolver é o único caminho que guarda de fato."""
    fora = {}
    for node in getattr(arvore, "body", []):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for alvo in node.targets:
                if isinstance(alvo, ast.Name):
                    fora[alvo.id] = node.value.value
    return fora


def _chamadas_a_metering_consume(arvore) -> list:
    return [
        n for n in ast.walk(arvore)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr == "consume"
        and isinstance(n.func.value, ast.Name) and n.func.value.id == "metering"
    ]


def _resolve_month_section(chamada, constantes):
    """Valor REAL do `month_section` da chamada, ou `None` se ele não foi
    declarado (ou não é resolvível estaticamente).

    Três formas aceitas, todas resolvidas — nunca só reconhecidas:
      • literal na chamada (`month_section="analyticsEventsMonth"`);
      • constante do próprio módulo (`month_section=MONTH_SECTION`);
      • constante do metering (`month_section=metering.MONTH_SECTION`), que é
        como o caminho de IA de `main.py` declara o balde default SEM
        duplicar o literal — duas cópias do nome divergem na primeira
        manutenção, e uma delas decidiria dinheiro.
    Aceitar o nome sem resolver deixaria `month_section=OUTRA_COISA` passar."""
    kw = {k.arg: k.value for k in chamada.keywords if k.arg}
    valor = kw.get("month_section")
    if isinstance(valor, ast.Constant) and isinstance(valor.value, str):
        return valor.value
    if isinstance(valor, ast.Name):
        return constantes.get(valor.id)
    if isinstance(valor, ast.Attribute) and isinstance(valor.value, ast.Name) \
            and valor.value.id == "metering":
        from app import metering
        resolvido = getattr(metering, valor.attr, None)
        return resolvido if isinstance(resolvido, str) else None
    return None


def test_guardiao_v_consume_do_cap_sempre_leva_month_section_propria():
    caminho = _APP_DIR / "options_mcp_api.py"
    arvore = _arvore(caminho)
    constantes = _constantes_str_do_modulo(arvore)

    chamadas = _chamadas_a_metering_consume(arvore)
    assert chamadas, (
        "nenhuma chamada a `metering.consume` em options_mcp_api.py — este "
        "guardião estaria passando por vacuidade.")

    ofensores = [(c.lineno, _resolve_month_section(c, constantes)) for c in chamadas
                 if _resolve_month_section(c, constantes) != "mcpUsageMonth"]

    assert not ofensores, (
        f"`metering.consume` sem `month_section` própria: {ofensores!r} — o "
        f"default do metering é `aiUsageMonth`, o balde MENSAL de análises "
        f"do plano comercial (ADR-010). Sem a seção própria, cada chamada de "
        f"tool da aba Opções tiraria uma análise de IA do usuário ([R-1] do "
        f"PLANO).")


# ─────────────────────────────────────────────────────────────────────────
# (v-geral) — 25-01: o guardião acima só varria `options_mcp_api.py`, e foi
# por isso que o defeito entrou por `main.py`: a rota de analytics chamava
# `metering.consume` sem `month_section`, caía no default `aiUsageMonth` e
# descontava o LOTE inteiro de telemetria da cota mensal de análises do
# plano comercial. A regra geral não exige um valor único — cada módulo tem
# o seu balde —, exige que o balde seja ESCRITO. O default implícito é a
# armadilha; escolher `aiUsageMonth` de propósito, escrito, é legítimo.
# ─────────────────────────────────────────────────────────────────────────
def _consumes_sem_month_section(arvore, constantes) -> list:
    return [c.lineno for c in _chamadas_a_metering_consume(arvore)
            if not _resolve_month_section(c, constantes)]


def test_guardiao_v_geral_todo_consume_do_app_declara_month_section():
    ofensores, total = [], 0
    for caminho in _modulos_app():
        arvore = _arvore(caminho)
        constantes = _constantes_str_do_modulo(arvore)
        total += len(_chamadas_a_metering_consume(arvore))
        ofensores += [(caminho.name, linha)
                      for linha in _consumes_sem_month_section(arvore, constantes)]

    assert total >= 2, (
        f"só {total} chamada(s) a `metering.consume` em `server/app/` — o "
        f"guardião estaria passando por vacuidade (havia 2 em 2026-09-12).")
    assert not ofensores, (
        f"`metering.consume` sem `month_section` declarada: {ofensores!r}. O "
        f"default do módulo é `MONTH_SECTION = 'aiUsageMonth'`, o ledger que "
        f"`plan.can_analyze` lê pelo `month_used` para decidir o cap comercial "
        f"(30 análises/mês no PLAN_FREE). Quem consome sem escolher o balde "
        f"desconta análise de quem não analisou — foi assim que a telemetria "
        f"passou a comer a cota (25-01). Escreva o balde, mesmo que ele seja "
        f"`metering.MONTH_SECTION`.")


def test_guardiao_v_geral_reprova_um_consume_sem_month_section():
    """SANIDADE do guardião acima: um guardião que nunca reprova nada não
    guarda — e a regra aqui é 'ausência de argumento', o tipo de asserção que
    passa por vacuidade com a maior facilidade. Fonte sintético, sem tocar
    `server/app/`."""
    ofensor = ast.parse("import metering\ndef f(conn, uid):\n"
                        "    metering.consume(conn, uid, custo=50)\n")
    assert _consumes_sem_month_section(ofensor, {}) == [3]

    for forma in ('month_section="analyticsEventsMonth"',
                  "month_section=MINHA_SECAO",
                  "month_section=metering.MONTH_SECTION"):
        ok = ast.parse("import metering\nMINHA_SECAO = 'xUsageMonth'\n"
                       "def f(conn, uid):\n"
                       f"    metering.consume(conn, uid, {forma})\n")
        constantes = _constantes_str_do_modulo(ok)
        assert _consumes_sem_month_section(ok, constantes) == [], forma


# ─────────────────────────────────────────────────────────────────────────
# Guardião de COMPORTAMENTO — a delegação de `require_user` é real, não só
# um nome que agrada o guardião de cobertura de rotas.
# ─────────────────────────────────────────────────────────────────────────
def test_status_sem_authorization_responde_401():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        r = c.get("/api/options/mcp/status")
    assert r.status_code == 401, (
        f"`GET /api/options/mcp/status` sem header respondeu {r.status_code} "
        f"— o `require_user` local de options_mcp_api tem o nome certo mas "
        f"não está delegando de verdade.")
