"""Fase 50 (plano 50-01) — guardião da função ÚNICA de marcos (stop, alvo,
entrada, R:R, geometria, sizing) em setups.py. A tabela de casos mora em
fixtures/marcos_casos.json e é compartilhada com o espelho do front."""
import json
from pathlib import Path

import pytest

from app import setups

_CASOS = json.loads((Path(__file__).parent / "fixtures" / "marcos_casos.json").read_text(encoding="utf-8"))


def _ids(lista):
    return [c["nome"] for c in lista]


def _confere(obtido, esperado):
    for chave, valor in esperado.items():
        if chave == "motivoContem":
            for trecho in valor:
                assert trecho.lower() in obtido["motivo"].lower(), (trecho, obtido["motivo"])
        elif isinstance(valor, float):
            assert obtido[chave] == pytest.approx(valor, abs=0.006), (chave, obtido)
        else:
            assert obtido[chave] == valor, (chave, obtido)


@pytest.mark.parametrize("caso", _CASOS["marcos"], ids=_ids(_CASOS["marcos"]))
def test_marcos_do_plano(caso):
    a = caso["entrada"]
    m = setups.marcos_do_plano(a["lado"], a["gatilho"], a["invalidacao"], close=a["close"], niveis=a["niveis"])
    _confere(m, caso["esperado"])
    if not m["valido"]:
        # nulo é null, nunca 0.0
        assert m["stop"] is None and m["alvo"] is None and m["rr"] is None


@pytest.mark.parametrize("caso", _CASOS["geometria"], ids=_ids(_CASOS["geometria"]))
def test_validar_marcos(caso):
    a = caso["entrada"]
    if "constante" in a:
        assert getattr(setups, a["constante"]) == caso["esperado"]["motivo"]
        return
    assert setups.validar_marcos(a.get("stop"), a.get("alvo"), preco=a.get("preco"), avg=a.get("avg")) == caso["esperado"]["motivo"]


@pytest.mark.parametrize("caso", _CASOS["rr"], ids=_ids(_CASOS["rr"]))
def test_rr_da_entrada(caso):
    a = caso["entrada"]
    assert setups.rr_da_entrada(a["entrada"], a["stop"], a["alvo"]) == caso["esperado"]["rr"]
