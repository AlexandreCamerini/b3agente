"""Fase 16, Plano 02 (LIB-03) — vocabulário canônico da trava protetora
(collar) em `skill_ref.OPCOES_LASTREADAS`.

Parte 1 (Task 1): um teste por item do bloco `<behavior>` do plano — a frase
do collar nos dois modos, registro correto por modo, sem valor sinalizado
interpolado, sem promessa de lucro/garantia.

Parte 2 (Task 2): GUARDIÃO CVM — nenhum arquivo fora de `skill_ref.py` pode
compor a manchete do collar. Mesmo padrão estrutural do guardião b-mcp em
`test_opcoes_gatilho.py` (`ast`, não busca textual, para não reprovar o
próprio comentário que documenta a proibição).

Este guardião NÃO se apaga — reversão deliberada do texto canônico atualiza
o guardião com nota (guardrail do repositório, CLAUDE.md).
"""
import ast
from pathlib import Path

from app import skill_ref


# --------------------------- Parte 1: vocabulário ---------------------------

_DADOS_COLLAR = dict(n="3", ticker="PETR4", strikeCall="32,00", strikePut="28,00", qtyAcoes="300")


def test_collar_operador_fala_como_mesa_verbo_de_ordem():
    frase = skill_ref.opcoes_lastreadas_txt("operador", "collar", **_DADOS_COLLAR)
    assert frase.startswith("Vender")
    assert "PETR4" in frase
    assert "32,00" in frase
    assert "28,00" in frase
    assert "{" not in frase and "}" not in frase


def test_collar_educacional_descreve_condicao_nunca_ordem():
    frase = skill_ref.opcoes_lastreadas_txt("educacional", "collar", **_DADOS_COLLAR)
    assert frase.startswith("Se você tivesse")
    assert "{" not in frase and "}" not in frase


def test_collar_frases_dos_dois_modos_sao_diferentes():
    operador = skill_ref.opcoes_lastreadas_txt("operador", "collar", **_DADOS_COLLAR)
    educacional = skill_ref.opcoes_lastreadas_txt("educacional", "collar", **_DADOS_COLLAR)
    assert operador != educacional


def test_collar_nao_e_servido_pelo_fallback_sem_setup():
    assert skill_ref.OPCOES_LASTREADAS["operador"]["collar"] != skill_ref.OPCOES_LASTREADAS["operador"]["sem_setup"]
    assert skill_ref.OPCOES_LASTREADAS["educacional"]["collar"] != skill_ref.OPCOES_LASTREADAS["educacional"]["sem_setup"]


def test_collar_modo_desconhecido_cai_no_educacional():
    esperado = skill_ref.opcoes_lastreadas_txt("educacional", "collar", **_DADOS_COLLAR)
    obtido = skill_ref.opcoes_lastreadas_txt("modo_inexistente", "collar", **_DADOS_COLLAR)
    assert obtido == esperado


def test_collar_sem_promessa_de_lucro_ou_garantia():
    for modo in ("operador", "educacional"):
        frase = skill_ref.opcoes_lastreadas_txt(modo, "collar", **_DADOS_COLLAR)
        frase_lower = frase.lower()
        for proibida in ("garantido", "lucro certo", "sem risco"):
            assert proibida not in frase_lower


def test_collar_chave_existe_nos_dois_modos():
    assert "collar" in skill_ref.OPCOES_LASTREADAS["operador"]
    assert "collar" in skill_ref.OPCOES_LASTREADAS["educacional"]


def test_vocab_chaves_de_operacao_existem_nos_dois_modos_com_collar():
    """Paridade de chaves entre modos não quebra com a entrada nova."""
    assert sorted(skill_ref.OPCOES_LASTREADAS["operador"]) == sorted(skill_ref.OPCOES_LASTREADAS["educacional"])


# ------------------------- Parte 2: GUARDIÃO CVM -------------------------
# A manchete do collar nasce SÓ em `skill_ref.py`. Nenhum outro arquivo do
# backend ou do front pode compor esse texto — guardrail regulatório (CVM)
# já vigente para call_coberta/put_protecao, estendido aqui para o collar.

_STRINGS_ANCORA_COLLAR = ("trava protetora", "abate o custo")

_RAIZ_APP = Path(__file__).resolve().parent.parent / "app"
_RAIZ_WEB_SRC = Path(__file__).resolve().parent.parent.parent / "web" / "src"


def _docstring_ids_de(arvore):
    """IDs de objeto dos nós `ast.Constant` que são docstring de módulo,
    classe ou função — para excluir da varredura de string literal. Uma
    busca ingênua reprovaria o próprio docstring que explica o guardrail."""
    ids = set()

    def marcar(body):
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            ids.add(id(body[0].value))

    marcar(arvore.body)
    for node in ast.walk(arvore):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            marcar(node.body)
    return ids


def _strings_literais_de_codigo(caminho):
    """Todas as strings literais de CÓDIGO (não docstring, não comentário —
    `ast.parse` já descarta comentário) de um arquivo .py."""
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    ids_doc = _docstring_ids_de(arvore)
    out = []
    for node in ast.walk(arvore):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in ids_doc:
            out.append(node.value)
    return out


def test_nenhum_modulo_backend_fora_do_skill_ref_compoe_manchete_do_collar():
    for caminho in sorted(_RAIZ_APP.glob("*.py")):
        if caminho.name == "skill_ref.py":
            continue
        for literal in _strings_literais_de_codigo(caminho):
            for ancora in _STRINGS_ANCORA_COLLAR:
                assert ancora not in literal, (
                    f"{caminho.name}: a manchete do collar vem SÓ de skill_ref.py "
                    f"(guardrail CVM) — string proibida '{ancora}' encontrada: {literal!r}"
                )


def test_nenhum_arquivo_front_compoe_manchete_do_collar():
    if not _RAIZ_WEB_SRC.exists():
        return
    caminhos = list(_RAIZ_WEB_SRC.glob("*.js")) + list(_RAIZ_WEB_SRC.glob("*.jsx"))
    for caminho in sorted(caminhos):
        texto = caminho.read_text(encoding="utf-8")
        for ancora in _STRINGS_ANCORA_COLLAR:
            assert ancora not in texto, (
                f"{caminho.name}: a manchete do card de decisão vem SÓ do motor determinístico "
                f"(guardrail CVM) — string proibida '{ancora}' encontrada no front"
            )


def test_guardiao_nao_esta_protegendo_texto_que_nao_existe_mais():
    """Prova de que o guardião não é um falso-verde vazio: as duas
    strings-âncora precisam existir de fato em skill_ref.py."""
    texto = (_RAIZ_APP / "skill_ref.py").read_text(encoding="utf-8")
    for ancora in _STRINGS_ANCORA_COLLAR:
        assert ancora in texto
