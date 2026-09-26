"""Fase 41, plano 41-01 (TELAS-01) — segundo ponto do par registro-front x
PET_TELAS.

Mesmo desenho de `test_a8ii_paridade_defaults_carteira_com_catalog_js`
(`test_auditoria_prompts.py`): lê `web/src/telas.js` como TEXTO, via caminho
relativo a `__file__` — nunca invoca um processo node, nunca import
cross-language. O espelho do lado JS é `web/tests/test_telas_registro.mjs`,
que lê `conceitos.py` como texto. Nenhum dos dois lados importa o outro
(padrão `defaults.py`x`catalog.js`, CLAUDE.md).

D-01: o registro do front e `conceitos.PET_TELAS` têm que ter exatamente o
mesmo conjunto de 8 ids, sem exceção — uma tela fora do registro faz o
assistente falar de uma tela que o front não declara; uma tela fora de
PET_TELAS faz `/api/assistente` responder 400 "Tela desconhecida." na aba
mais nova (o mesmo defeito do achado A1/C3 da Fase 26, agora travado nos
dois lados).
"""
import os
import re

from app import conceitos


def _ler_telas_js():
    caminho = os.path.join(
        os.path.dirname(__file__), "..", "..", "web", "src", "telas.js"
    )
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def test_registro_de_telas_do_front_bate_com_pet_telas():
    """Conjunto de ids do registro == conjunto de conceitos.PET_TELAS."""
    src = _ler_telas_js()
    bloco_m = re.search(r"export const TELAS = Object\.freeze\(\[([\s\S]*?)\n\]\);", src)
    assert bloco_m, "bloco `export const TELAS = Object.freeze([...])` não encontrado em telas.js"
    bloco = bloco_m.group(1)
    ids = re.findall(r'id:\s*"([a-z]+)"', bloco)

    assert len(ids) == 8, f"esperado 8 ids no registro, achou {len(ids)}: {ids}"
    assert len(ids) == len(set(ids)), f"id duplicado no registro: {ids}"

    esperado = set(conceitos.PET_TELAS)
    obtido = set(ids)
    so_registro = obtido - esperado
    so_pet_telas = esperado - obtido
    assert obtido == esperado, (
        "registro de telas do front divergiu de conceitos.PET_TELAS — "
        f"só no registro: {sorted(so_registro)} (fora da allowlist, "
        "/api/assistente responde 400 'Tela desconhecida.'); "
        f"só em PET_TELAS: {sorted(so_pet_telas)} (resumo sem tela "
        "que o front chame)"
    )


def test_pet_telas_nao_tem_duplicata():
    assert len(conceitos.PET_TELAS) == len(set(conceitos.PET_TELAS)) == 8
