"""Fase 38 (38-05, KB-02) — guardião cross-linguagem de `ANCORAS_KB`
(`web/src/glossario.js`): os 4 `vid` do link "saiba mais" fixo por aba
precisam existir de verdade no catálogo do backend (`kb.py`), com texto não
vazio nos dois modos — senão o link abre uma folha vazia/quebrada.

Mesmo padrão de guardião cross-linguagem já usado no repo para
`defaults.py` <-> `catalog.js` (`test_auditoria_prompts.py`,
`test_a8ii_paridade_defaults_carteira_com_catalog_js`): lê o `.js` do
repositório por caminho relativo a `__file__`, nunca reimplementa a lógica
de negócio, só confere paridade de dado.
"""
import os
import re

import pytest

from app import kb

CHAVES_ESPERADAS = ("evolucao", "radar", "mercado", "opcoes")


@pytest.fixture(autouse=True)
def _flags_limpas():
    """`kb.catalogo()` deriva parte do texto de `conceitos.montar(...)`, que
    respeita `B3_DIDATICA_OFF` — isolado aqui como o resto da suíte já faz em
    `test_kb.py`, para nenhum teste de outro arquivo vazar a flag."""
    antes = {k: os.environ.get(k) for k in ("B3_DIDATICA_OFF", "B3_ASSISTENTE_OFF")}
    for k in antes:
        os.environ.pop(k, None)
    yield
    for k, v in antes.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _extrair_ancoras(src: str) -> dict:
    """Extrai o objeto `ANCORAS_KB = Object.freeze({ chave: "vid", ... })` de
    um texto JS: devolve `{chave: vid}`. Não interpreta JS de verdade — casa
    só o formato literal que `glossario.js` usa (chaves nuas, valores
    string), suficiente para este guardião de paridade."""
    m = re.search(r"ANCORAS_KB\s*=\s*Object\.freeze\(\{(.*?)\}\)", src, re.S)
    assert m, "ANCORAS_KB = Object.freeze({...}) não encontrado no fonte"
    corpo = m.group(1)
    pares = re.findall(r'(\w+)\s*:\s*"([^"]*)"', corpo)
    assert pares, "ANCORAS_KB: nenhum par chave:valor casado no corpo extraído"
    return dict(pares)


def _caminho_glossario() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "..", "web", "src", "glossario.js")


def _ler_glossario() -> str:
    with open(_caminho_glossario(), encoding="utf-8") as f:
        return f.read()


def test_ancoras_kb_tem_exatamente_as_4_chaves_das_abas():
    ancoras = _extrair_ancoras(_ler_glossario())
    assert set(ancoras.keys()) == set(CHAVES_ESPERADAS), \
        f"ANCORAS_KB deveria ter exatamente {CHAVES_ESPERADAS}, achou {sorted(ancoras.keys())}"


def test_cada_vid_de_ancoras_kb_existe_no_catalogo_real():
    ancoras = _extrair_ancoras(_ler_glossario())
    ids_catalogo = {v["id"] for v in kb.catalogo()}
    for chave, vid in ancoras.items():
        assert vid in ids_catalogo, \
            f"ANCORAS_KB.{chave} = '{vid}' não existe em kb.catalogo() — link morto"


def test_cada_vid_de_ancoras_kb_tem_texto_nao_vazio_nos_dois_modos():
    ancoras = _extrair_ancoras(_ler_glossario())
    por_id = {v["id"]: v for v in kb.catalogo()}
    for chave, vid in ancoras.items():
        v = por_id.get(vid)
        assert v is not None, f"ANCORAS_KB.{chave} = '{vid}' não existe no catálogo"
        texto = v.get("texto") or {}
        for modo in ("educacional", "operador"):
            assert texto.get(modo), \
                f"ANCORAS_KB.{chave} = '{vid}': texto vazio no modo '{modo}'"


def test_prova_negativa_extracao_com_id_inexistente_nao_passa_no_catalogo():
    """Prova negativa do próprio guardião: aplicar `_extrair_ancoras` a um
    texto fixo com um id inventado produz um id que de fato NÃO está no
    catálogo — se este teste falhasse (id inventado existisse por
    coincidência ou a extração não capturasse o valor), o guardião acima
    estaria inerte."""
    texto_falso = (
        'export const ANCORAS_KB = Object.freeze({\n'
        '  evolucao: "id-inexistente-38-05",\n'
        '  radar: "confluencia",\n'
        '  mercado: "ind-rsi",\n'
        '  opcoes: "mkt-opcao",\n'
        '});\n'
    )
    ancoras = _extrair_ancoras(texto_falso)
    assert ancoras["evolucao"] == "id-inexistente-38-05"
    ids_catalogo = {v["id"] for v in kb.catalogo()}
    assert ancoras["evolucao"] not in ids_catalogo, \
        "prova negativa furou: o id inventado existe de verdade no catálogo"
