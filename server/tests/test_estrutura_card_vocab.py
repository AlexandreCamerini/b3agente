"""Guardião do vocabulário do card de posição estruturada (Fase 45).

Espelho em web/src/copy.js (`estruturaCard`), travado por
web/tests/test_estrutura_card_espelho.mjs. Guardião não se apaga.
"""
import re

from app import skill_ref

CHAVES = {
    "chip_estrutura",
    "chip_estrutura_generica",
    "lendo",
    "indisponivel",
    "badge_travada_collar",
    "aviso_sem_stop",
}


def test_chip_operador():
    assert skill_ref.estrutura_card_txt("operador", "chip_estrutura", nome="COLLAR") == "ESTRUTURA · COLLAR"


def test_chip_educacional():
    assert skill_ref.estrutura_card_txt("educacional", "chip_estrutura", nome="COLLAR") == "ESTUDO · COLLAR"


def test_modo_estudo_cai_no_educacional():
    assert skill_ref.estrutura_card_txt("estudo", "chip_estrutura", nome="X") == "ESTUDO · X"


def test_chave_inexistente_devolve_none():
    assert skill_ref.estrutura_card_txt("operador", "chave_inexistente") is None


def test_badge_travada_collar_interpola():
    assert (
        skill_ref.estrutura_card_txt("operador", "badge_travada_collar", qty=1000)
        == "1000 travada(s) · lastro da CALL do collar"
    )


def test_conjunto_de_chaves_dos_dois_modos():
    for modo in ("operador", "educacional"):
        assert set(skill_ref.ESTRUTURA_CARD[modo]) == CHAVES


def test_sem_ancoras_proibidas():
    rx = re.compile(r"trava(\(s\))?\s+protetora|abate\s+o\s+custo", re.I)
    for modo, d in skill_ref.ESTRUTURA_CARD.items():
        for k, v in d.items():
            assert not rx.search(v), (modo, k)


def test_educacional_sem_verbo_de_ordem():
    for k, v in skill_ref.ESTRUTURA_CARD["educacional"].items():
        assert not re.search(r"\b(comprar|vender)\b", v, re.I), k


def test_interpolacao_completa_nao_deixa_chaves():
    dados = {"nome": "COLLAR", "qty": 100}
    for modo, d in skill_ref.ESTRUTURA_CARD.items():
        for k in d:
            out = skill_ref.estrutura_card_txt(modo, k, **dados)
            assert "{" not in out and "}" not in out, (modo, k)
