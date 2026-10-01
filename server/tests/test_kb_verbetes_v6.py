"""Guardião dos 6 verbetes de KB dos termos tocáveis da Carteira v6 (Fase 46, D-09/D-10).

Conteúdo determinístico e genérico, sem promessa de rentabilidade; o Estudo não
usa comprar/vender como verbo de ordem. Guardião não se apaga.
"""
import re

import pytest

from app import kb

IDS = ("opc-lastro", "opc-call-coberta", "opc-teto", "opc-piso", "opc-equilibrio", "mkt-preco-medio")
PROIBIDO = re.compile(r"garant|lucro certo|sem risco|\bsempre\b", re.I)
VERBO_ORDEM = re.compile(r"\bvender\b|\bcomprar\b", re.I)


@pytest.mark.parametrize("vid", IDS)
def test_verbete_existe_com_textos_e_familia(vid):
    v = kb.verbete(vid)
    assert v is not None
    assert v["familia"] == "mercado_b3"
    assert v["termos"]
    for modo in ("educacional", "operador"):
        assert kb.formatar(v, modo)["texto"].strip()


@pytest.mark.parametrize("vid", IDS)
def test_veja_sem_link_morto(vid):
    for alvo in kb.verbete(vid)["veja"]:
        assert kb.verbete(alvo) is not None, (vid, alvo)


@pytest.mark.parametrize("vid", IDS)
def test_textos_sem_promessa_nem_verbo_de_ordem(vid):
    for modo in ("educacional", "operador"):
        texto = kb.formatar(kb.verbete(vid), modo)["texto"]
        assert not PROIBIDO.search(texto), (vid, modo)
    assert not VERBO_ORDEM.search(kb.formatar(kb.verbete(vid), "educacional")["texto"]), vid


def test_catalogo_serve_os_seis_verbetes():
    ids = {v["id"] for v in kb.catalogo_formatado("educacional")["verbetes"]}
    assert set(IDS) <= ids
