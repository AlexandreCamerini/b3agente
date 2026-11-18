"""server/tests/test_dia_na_bolsa_job.py — guardião do job "Seu dia na bolsa"
(Fase 51, plano 51-05). Sem rede: Yahoo, benchmark, cache e push são mocados."""
import asyncio
import os
import tempfile
from datetime import date, datetime, timedelta, timezone

import pytest

from app import candle_cache, db, dia_na_bolsa as dnb, setups, technical_snapshot

BRT = timezone(timedelta(hours=-3))
HOJE = "2026-10-13"   # terça-feira, dia de pregão


def dt(h, m, dia=HOJE):
    y, mo, d = (int(x) for x in dia.split("-"))
    return datetime(y, mo, d, h, m, 0, tzinfo=BRT)


def _conn():
    return db.connect(os.path.join(tempfile.mkdtemp(), "b3.db"))


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _arquivo(c, data=HOJE, base="2026-10-12", linhas=(), universo=()):
    db.kv_set(c, "radarDailyArquivo:" + data,
              {"data": data, "dataBase": base, "scanAt": None,
               "linhas": list(linhas), "universo": list(universo)}, user_id=None)


def _linha(t="PETR4", setup="rompimento", entrada=10.0, stop=9.0, alvo=12.0):
    return {"ticker": t, "setup": setup, "decisao": "COMPRAR", "tipo": "a mercado (zona)",
            "entrada": entrada, "stop": stop, "alvo": alvo, "entradaAMercado": True, "close": 10.0}


@pytest.fixture(autouse=True)
def _isola(monkeypatch):
    candle_cache.reset()
    yield
    candle_cache.reset()


# ----------------------------------------------------------------- vistos
def test_visto_do_radar_grava_precos_do_arquivo():
    c = _conn()
    _arquivo(c, linhas=[_linha()])
    r = dnb.registrar_vistos(c, "u1", ["petr4"], "radar", dt(11, 0))
    assert r == {"registrados": 1, "semPlano": 0, "ignorados": 0}
    (v,) = dnb.ler_vistos(c, "u1")
    assert (v["ticker"], v["setup"], v["fonte"]) == ("PETR4", "rompimento", "radar")
    assert (v["entrada"], v["stop"], v["alvo"], v["dataBase"]) == (10.0, 9.0, 12.0, "2026-10-12")
    assert v["entradaAMercado"] is True and v["vistoEm"] == HOJE and v["origem"] == "radar"
    # escopo: outra conta não enxerga (T-51-12)
    assert dnb.ler_vistos(c, "u2") == []
    assert db.kv_get(c, dnb.K_VISTOS, None, user_id=None) is None


def test_visto_duplicado_no_mesmo_dia_nao_duplica():
    c = _conn()
    _arquivo(c, linhas=[_linha()])
    dnb.registrar_vistos(c, "u1", ["PETR4"], "radar", dt(11, 0))
    r = dnb.registrar_vistos(c, "u1", ["PETR4"], "watchlist", dt(15, 0))
    assert r["registrados"] == 0
    assert len(dnb.ler_vistos(c, "u1")) == 1


def test_visto_fora_do_arquivo_usa_snapshot_do_cache(monkeypatch):
    c = _conn()
    _arquivo(c, linhas=[])
    cs = [{"date": "2026-10-09", "open": 1, "high": 1, "low": 1, "close": 20.0},
          {"date": "2026-10-12", "open": 1, "high": 1, "low": 1, "close": 21.0}]
    monkeypatch.setattr(candle_cache, "peek", lambda t, i="1d": cs)
    monkeypatch.setattr(technical_snapshot, "build", lambda t, c_, p, interval="1d": {"setups": {}, "close": 21.0})
    monkeypatch.setattr(setups, "plano_do_resultado", lambda s, close=None: {
        "decisao": "COMPRAR", "setup": "pullback", "tipo": "no rompimento do gatilho",
        "entrada": 22.0, "stop": 20.0, "alvo": 26.0})
    r = dnb.registrar_vistos(c, "u1", ["VALE3"], "carteira", dt(11, 0))
    assert r["registrados"] == 1
    (v,) = dnb.ler_vistos(c, "u1")
    assert v["fonte"] == "snapshot" and v["dataBase"] == "2026-10-12"
    assert (v["entrada"], v["stop"], v["alvo"], v["precoBase"]) == (22.0, 20.0, 26.0, 21.0)
    assert v["entradaAMercado"] is False


def test_visto_sem_plano_operavel_ou_sem_dado_conta_semplano(monkeypatch):
    c = _conn()
    _arquivo(c, linhas=[])
    cs = [{"date": "2026-10-12", "open": 1, "high": 1, "low": 1, "close": 21.0}]
    monkeypatch.setattr(candle_cache, "peek",
                        lambda t, i="1d": cs if t == "VALE3" else [])
    monkeypatch.setattr(technical_snapshot, "build", lambda t, c_, p, interval="1d": {"setups": {}, "close": 21.0})
    monkeypatch.setattr(setups, "plano_do_resultado", lambda s, close=None: {"decisao": "AGUARDAR CONFIRMAÇÃO"})
    r = dnb.registrar_vistos(c, "u1", ["VALE3", "ITUB4"], "radar", dt(11, 0))
    assert r == {"registrados": 0, "semPlano": 2, "ignorados": 0}
    assert dnb.ler_vistos(c, "u1") == []


def test_visto_valida_ticker_origem_e_tamanho():
    c = _conn()
    _arquivo(c, linhas=[_linha()])
    r = dnb.registrar_vistos(c, "u1", ["abc", "PETR4;DROP", "PETR4", 123, None], "radar", dt(11, 0))
    assert r["ignorados"] == 4 and r["registrados"] == 1
    with pytest.raises(ValueError):
        dnb.registrar_vistos(c, "u1", ["PETR4"], "cliente", dt(11, 0))
    with pytest.raises(ValueError):
        dnb.registrar_vistos(c, "u1", ["PETR4"] * 61, "radar", dt(11, 0))
    with pytest.raises(ValueError):
        dnb.registrar_vistos(c, None, ["PETR4"], "radar", dt(11, 0))


def test_visto_nao_recebe_preco_do_cliente():
    import inspect
    assert list(inspect.signature(dnb.registrar_vistos).parameters) == [
        "conn", "uid", "tickers", "origem", "agora"]


def test_visto_poda_aberto_com_41_dias():
    c = _conn()
    velho = {"ticker": "VALE3", "setup": "x", "origem": "radar", "vistoEm": "2026-08-30",
             "dataBase": "2026-09-02", "entrada": 1.0, "stop": 0.5, "alvo": 2.0,
             "entradaAMercado": True, "precoBase": 1.0, "fonte": "radar", "estado": None}
    db.kv_set(c, dnb.K_VISTOS, [velho], user_id="u1")
    _arquivo(c, linhas=[_linha()])
    dnb.registrar_vistos(c, "u1", ["PETR4"], "radar", dt(11, 0))
    assert [v["ticker"] for v in dnb.ler_vistos(c, "u1")] == ["PETR4"]
