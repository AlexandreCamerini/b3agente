"""Fase 51 (51-04, ENG-05): conceitos `amplitude` e `extremo-52-semanas`.

Gap e volatilidade reaproveitam os verbetes KB existentes; nenhum duplicado."""
import re

from app import conceitos, kb


def _texto(c):
    return " ".join(c["naoAcontece"] + c["oQueE"] + c["oQueAcontece"])


def test_amplitude_estudo_formata_pt_br():
    c = conceitos.montar("amplitude", "educacional",
                         {"fracao": 0.91, "n": 74, "direcao": "queda"})
    assert c and c["id"] == "amplitude"
    assert "Amplitude" in c["titulo"]
    t = _texto(c)
    assert "91%" in t and "74" in t and "queda" in t


def test_extremo_operador_texto_de_mesa():
    c = conceitos.montar("extremo-52-semanas", "operador",
                         {"ticker": "PETR4", "lado": "máxima", "preco": 41.2})
    assert c and c["titulo"] == "Extremo de 52 semanas"
    t = _texto(c)
    assert "PETR4" in t and "R$ 41,20" in t and "máxima" in t


def test_nao_acontece_nos_dois_modos():
    for cid in ("amplitude", "extremo-52-semanas"):
        for modo in ("educacional", "operador"):
            c = conceitos.montar(cid, modo, {})
            na = " ".join(c["naoAcontece"]).lower()
            assert "não compra nem vende" in na
            assert "previsão" in na or "não promete" in na or "não indica" in na


def test_dado_ausente_nunca_vira_zero():
    c = conceitos.montar("amplitude", "educacional", {})
    t = _texto(c)
    assert "0%" not in t and " 0 " not in t
    assert "{" not in t
    c2 = conceitos.montar("extremo-52-semanas", "educacional", {"ticker": "VALE3"})
    assert "R$ 0" not in _texto(c2) and "{" not in _texto(c2)
    # fração fora de 0..1 não formata
    c3 = conceitos.montar("amplitude", "educacional", {"fracao": 91, "n": 74, "direcao": "alta"})
    assert "9100%" not in _texto(c3)


def test_catalogo_lista_os_dois_ids():
    for modo in ("educacional", "operador"):
        ids = {c["id"] for c in conceitos.catalogo(modo)}
        assert {"amplitude", "extremo-52-semanas"} <= ids


def test_sem_vocabulario_proibido():
    for cid in ("amplitude", "extremo-52-semanas"):
        for modo in ("educacional", "operador"):
            t = _texto(conceitos.montar(cid, modo, {"fracao": 0.9, "n": 70,
                                                    "direcao": "alta", "ticker": "X",
                                                    "lado": "máxima", "preco": 10.0}))
            assert not re.search(r"perdeu|oportunidade|garantid", t, re.I)


def test_veja_so_aponta_para_existentes():
    for cid in ("amplitude", "extremo-52-semanas"):
        for v in conceitos.CONCEITOS[cid]["veja"]:
            assert v in conceitos.CONCEITOS


def test_verbetes_kb_reutilizados_existem():
    textos = repr(getattr(kb, "VERBETES", None) or getattr(kb, "ENTRADAS", None) or vars(kb))
    for vid in ("estr-gap", "ind-volatilidade-historica", "ind-atr"):
        assert vid in textos
