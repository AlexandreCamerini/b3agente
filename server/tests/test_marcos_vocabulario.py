"""Fase 50 (plano 50-02): vocabulário dos marcos do motor — MARCOS_PLANO.
O espelho byte a byte com copy.js é travado por web/tests/test_vocabulario_espelho.mjs."""
import re

import pytest

from app import skill_ref

MP = skill_ref.MARCOS_PLANO


def test_chaves_identicas_nos_dois_modos():
    assert set(MP["operador"]) == set(MP["educacional"])
    assert len(MP["operador"]) >= 24


def test_placeholders_identicos_nos_dois_modos():
    for k in MP["operador"]:
        a = set(re.findall(r"\{(\w+)\}", MP["operador"][k]))
        b = set(re.findall(r"\{(\w+)\}", MP["educacional"][k]))
        assert a == b, k


def test_txt_interpola_ticker_e_motivo():
    for modo in ("operador", "educacional", "estudo"):
        f = skill_ref.marcos_plano_txt(modo, "plano_invalido_diario", ticker="PETR4", motivo="alvo abaixo da cotação.")
        assert "PETR4" in f and "alvo abaixo da cotação." in f and "{" not in f


def test_placeholder_faltando_levanta_value_error():
    with pytest.raises(ValueError):
        skill_ref.marcos_plano_txt("operador", "plano_invalido_diario", ticker="X")
    with pytest.raises(ValueError):
        skill_ref.marcos_plano_txt("operador", "entrada_recusada", ticker="X", motivo="")


def test_chave_inexistente_levanta_key_error():
    with pytest.raises(KeyError):
        skill_ref.marcos_plano_txt("operador", "nao_existe")


def test_sem_linguagem_de_promessa():
    for modo, d in MP.items():
        for k, v in d.items():
            baixo = v.lower()
            assert "garant" not in baixo, (modo, k)
            assert "lucro certo" not in baixo, (modo, k)
            assert "100%" not in baixo, (modo, k)


def test_cartao_posicao_chaves_novas_e_rotulo_distinto():
    for modo in ("operador", "educacional"):
        assert skill_ref.cartao_posicao_txt(modo, "estado_plano_invalido")
        assert "xx" in skill_ref.cartao_posicao_txt(modo, "plano_invalido_detalhe", motivo="xx")
        assert skill_ref.cartao_posicao_txt(modo, "rr_plano") != skill_ref.cartao_posicao_txt(modo, "rr_atual")
        assert skill_ref.cartao_posicao_txt(modo, "rr_atual") == "R:R restante (do preço atual)"
