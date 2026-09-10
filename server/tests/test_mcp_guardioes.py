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


# (iv) e (v) entram na Task 3, com o router `options_mcp_api.py` — sem rota
# no repo eles passariam por vacuidade, que é o oposto de guardar.
