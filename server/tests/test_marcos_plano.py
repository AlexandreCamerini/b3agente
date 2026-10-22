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


@pytest.mark.parametrize("caso", _CASOS["revalidacao"], ids=_ids(_CASOS["revalidacao"]))
def test_revalidar_na_execucao(caso):
    a = caso["entrada"]
    r = setups.revalidar_na_execucao(a["stop"], a["alvo"], a["preco"], gatilho=a.get("gatilho"), invalidacao=a.get("invalidacao"))
    esp = dict(caso["esperado"])
    trechos = esp.pop("motivoContem", [])
    for t in trechos:
        assert t.lower() in (r["motivo"] or "").lower(), (t, r)
    for k, v in esp.items():
        assert r[k] == (pytest.approx(v, abs=0.006) if isinstance(v, float) else v), (k, r)


@pytest.mark.parametrize("caso", _CASOS["sizing"], ids=_ids(_CASOS["sizing"]))
def test_sizing_por_risco(caso):
    a = caso["entrada"]
    r = setups.sizing_por_risco(a["capital"], a["pct"], a["entrada"], a["stop"], caixa=a.get("caixa"), alloc_pct=a.get("alloc_pct"))
    esp = dict(caso["esperado"])
    for t in esp.pop("avisoContem", []):
        assert t in r["aviso"], (t, r)
    for k, v in esp.items():
        assert r[k] == (pytest.approx(v, abs=0.006) if isinstance(v, float) else v), (k, r)


# ---- Fase 50: plano do Radar (alta) sobre a função única -------------------

def test_plano_operacional_alta_sem_niveis_nao_opera_por_atr():
    p = setups.plano_operacional({"nome": "X", "lado": "alta", "gatilho": 20.0, "invalidacao": 19.0}, close=None)
    assert p["decisao"] == setups.DECISAO_NAO_OPERAR
    assert "ATR" in p["motivo"] and p["stop"] is None and p["alvo2"] is None
    assert p["setup"] == "X" and p["lado"] == "alta"


def test_plano_operacional_baixa_inalterado():
    # caso fixo da regra antiga (short fora do escopo da Fase 50): números idênticos
    s = {"nome": "X", "lado": "baixa", "gatilho": 37.60, "invalidacao": 38.55, "alvoSugerido": None}
    p = setups.plano_operacional(s, close=37.90)
    assert p["decisao"] == setups.DECISAO_VENDER
    assert (p["entrada"], p["stop"], p["alvo1"], p["alvo2"]) == (37.6, 38.55, 36.65, 35.7)
    assert (p["rr1"], p["rr2"], p["riscoPorAcao"]) == (1.0, 2.0, 0.95)


def test_detect_setups_devolve_niveis():
    from app import indicators
    candles = [{"date": "2024-%02d-%02d" % (1 + i // 28, 1 + i % 28), "open": 10 + i * 0.01, "high": 10.3 + i * 0.01,
                "low": 9.8 + i * 0.01, "close": 10 + i * 0.01, "volume": 1000} for i in range(120)]
    cs = indicators.sanitize_candles(candles)
    res = setups.detect_setups(cs, indicators.compute(cs)["indicators"])
    assert set(res["niveis"]) == {"atr", "suportes", "resistencias"}
    assert res["niveis"]["atr"] is not None and res["niveis"]["atr"] > 0


# ---------------------------------------------------------------------------
# Review WR-01 — marcos_da_posicao respeita o preço médio
# ---------------------------------------------------------------------------
_NIV = {"atr": 0.5, "suportes": [22.0], "resistencias": [24.8, 26.0]}


def test_wr01_posicao_no_prejuizo_pula_resistencia_abaixo_do_pm():
    base = setups.marcos_da_posicao(23.0, _NIV)
    assert base["valido"] and base["alvo"] == 24.8          # sem PM: comportamento anterior
    m = setups.marcos_da_posicao(23.0, _NIV, avg=25.0)
    assert m["valido"] and m["alvo"] == 26.0 and m["stop"] == 21.95
    assert setups.validar_marcos(m["stop"], m["alvo"], preco=23.0, avg=25.0) is None


def test_wr01_sem_nivel_acima_do_pm_devolve_invalido_com_motivo():
    m = setups.marcos_da_posicao(23.0, _NIV, avg=30.0)
    assert m["valido"] is False and m["stop"] is None and m["alvo"] is None
    assert "preço médio (R$ 30,00)" in m["motivo"]


def test_wr01_pm_abaixo_do_alvo_nao_muda_nada():
    assert setups.marcos_da_posicao(23.0, _NIV, avg=20.0) == setups.marcos_da_posicao(23.0, _NIV)
