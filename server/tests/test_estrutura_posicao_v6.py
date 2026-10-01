"""Fase 46, Plano 04 — `ler_estrutura` ganha `cenarios`/`didatica` (aditivo).

Passa pelo mesmo caminho que o card consome (`estrutura_posicao.ler_estrutura`).
Sem rede, sem banco.
"""
import datetime as dt

import pytest

from app import cartao_posicao
from app import estrutura_posicao as m

V = dt.date(2026, 10, 16)
HOJE = V - dt.timedelta(days=20)


def _call(id_, und, strike, avg, qty=1000, venc=V):
    return {"id": id_, "underlying": und, "optionType": "call", "strike": strike,
            "expiration": venc.isoformat(), "qty": qty, "avg": avg, "side": "vendida"}


def _put(id_, und, strike, avg, qty=1000, venc=V):
    return {"id": id_, "underlying": und, "optionType": "put", "strike": strike,
            "expiration": venc.isoformat(), "qty": qty, "avg": avg, "side": "comprada"}


def _ct(id_, tipo, strike, bid, ask):
    return {"contractSymbol": id_, "optionType": tipo, "strike": strike, "bid": bid,
            "ask": ask, "lastPrice": ask, "volume": 50000, "openInterest": 90000}


def _ugpa3(modo="educacional"):
    return m.ler_estrutura(
        [_call("UGPAJ4225", "UGPA3", 42.25, 1.49)], "UGPA3",
        {"t": "UGPA3", "qty": 1000, "avg": 39.5}, 40.10,
        {"UGPAJ4225": _ct("UGPAJ4225", "call", 42.25, 1.40, 1.50)}, HOJE, modo)


def _cxse3(modo="educacional"):
    return m.ler_estrutura(
        [_call("CXSEJ21", "CXSE3", 21.02, 0.25)], "CXSE3",
        {"t": "CXSE3", "qty": 1000, "avg": 20.06}, 20.40,
        {"CXSEJ21": _ct("CXSEJ21", "call", 21.02, 0.20, 0.30)}, HOJE, modo)


def _itsa4(modo="educacional"):
    # put e call com vencimentos diferentes -> sem faixa (D-08)
    v2 = V + dt.timedelta(days=30)
    return m.ler_estrutura(
        [_call("ITSAJ1", "ITSA4", 11.0, 0.30, venc=V), _put("ITSAV1", "ITSA4", 9.0, 0.20, venc=v2)],
        "ITSA4", {"t": "ITSA4", "qty": 1000, "avg": 10.0}, 10.2,
        {"ITSAJ1": _ct("ITSAJ1", "call", 11.0, 0.25, 0.35),
         "ITSAV1": _ct("ITSAV1", "put", 9.0, 0.15, 0.25)}, HOJE, modo)


# D-02: substitui os testes optionsCalc da spec — o cálculo é do backend.
def test_ugpa3_be_ganho_perda():
    r = _ugpa3()
    assert r["faixa"]["breakevens"] == [38.01]
    assert r["faixa"]["ganhoMaximo"] == 4240.0
    assert r["faixa"]["perdaMaxima"] == 38010.0
    assert r["cenarios"]["be"] == 38.01


# D-02: idem para CXSE3.
def test_cxse3_be_ganho_perda():
    r = _cxse3()
    assert r["faixa"]["breakevens"] == [19.81]
    assert r["faixa"]["ganhoMaximo"] == 1210.0
    assert r["faixa"]["perdaMaxima"] == 19810.0
    assert r["cenarios"]["be"] == 19.81


def test_ugpa3_modo_educacional_tem_simulador_e_didatica():
    r = _ugpa3("educacional")
    assert r["cenarios"]["simulador"] is not None
    termos = [s.get("termo") for s in r["didatica"]["paragrafo"]]
    assert "call_coberta" in termos


def test_ugpa3_modo_estudo_legado_mapeia_para_educacional():
    # a rota passa cfg.appMode ("estudo"); o motor do card fala "educacional"
    r = _ugpa3("estudo")
    assert r["cenarios"]["simulador"] is not None and r["didatica"] is not None


def test_ugpa3_modo_operador_grade_com_conta_e_sem_didatica():
    r = _ugpa3("operador")
    assert r["cenarios"]["grade"][0]["conta"]["numeros"] == "39,50 − 1,49 = 38,01"
    assert r["didatica"] is None


def test_itsa4_sem_be_calculavel_nao_desenha_nada():
    r = _itsa4()
    assert r["faixa"] is None
    assert r["cenarios"] is None
    textos = " ".join(s.get("texto", "") + s.get("noSeuCaso", "")
                      for s in r["didatica"]["paragrafo"])
    assert "aguardando o cálculo do app" in textos
    assert "38" not in textos


@pytest.mark.parametrize("fab", [_ugpa3, _cxse3, _itsa4])
def test_aditividade_contrato_antigo_intacto(fab, monkeypatch):
    novo = fab()
    with monkeypatch.context() as mp:
        def boom(*a, **k):
            raise RuntimeError("falha simulada")
        mp.setattr(cartao_posicao, "cenarios_da_estrutura", boom)
        antigo = fab()
    assert antigo["cenarios"] is None and antigo["didatica"] is None
    extras = {"cenarios", "didatica"}
    assert {k: v for k, v in novo.items() if k not in extras} == \
           {k: v for k, v in antigo.items() if k not in extras}
    assert set(novo) - set(antigo) == set()
    assert extras <= set(novo)
