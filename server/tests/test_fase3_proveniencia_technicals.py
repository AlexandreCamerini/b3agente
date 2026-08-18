"""Fase 3 (v1.1) — guardião de C-11 e C-30 do REPORT-01.

C-11 (Crítico): o painel técnico afirmava "Fonte: Yahoo Finance" mesmo quando
o dado tinha vindo da brapi — proveniência ATIVAMENTE FALSA, não apenas
ausente. A causa raiz: `candle_cache.load()` sempre devolveu `source` nos 4
caminhos de retorno (miss/fresh/stale/delta), mas `technical_snapshot.get()`
descartava o campo ao montar o snapshot, e a rota `/api/technicals/{ticker}`
nunca incluía `source` no payload.

C-30 (Crítico): quando a fatia `spot` do orçamento brapi passa de 80%, o TTL
do cache tripLica (`candle_provider._spot_ttl()`) e os dados ficam até 3x mais
velhos — sem que nenhum timestamp, badge ou texto avisasse o usuário final.
Este arquivo trava que `/api/technicals/{ticker}` expõe `degradado` (bool) e
que o indicador de orçamento nunca pode derrubar a rota (principio 4 do
CLAUDE.md: "não sei" é False, nunca uma invenção).
"""
import asyncio
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import brapi_budget, candle_cache, candle_provider, technical_snapshot


def _run(coro):
    return asyncio.run(coro)


def _reset_caches():
    candle_cache.reset()
    technical_snapshot.reset()


@pytest.fixture(autouse=True)
def _isolado():
    _reset_caches()
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)
    _reset_caches()


def _client(monkeypatch):
    d = tempfile.mkdtemp(prefix="b3_fase3_technicals_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


# --------------------------------------------------------------------------
# (a)/(b) — technical_snapshot.get() propaga (ou não inventa) `source`
# --------------------------------------------------------------------------

def test_a_snapshot_propaga_source_do_candle_cache():
    async def loader(_rng):
        return {"candles": _mk_candles(), "currency": "BRL", "source": "brapi"}

    snap = _run(technical_snapshot.get("FASE3A", "6mo", loader))
    assert snap["source"] == "brapi"


def test_b_snapshot_nao_inventa_source_quando_ausente():
    async def loader(_rng):
        return {"candles": _mk_candles(), "currency": "BRL"}  # sem "source"

    snap = _run(technical_snapshot.get("FASE3B", "6mo", loader))
    assert snap["source"] is None


def _mk_candles(n=260):
    return [{"date": f"2026-01-01+{i}", "open": 10 + i * 0.1, "high": 10.2 + i * 0.1,
             "low": 9.8 + i * 0.1, "close": 10 + i * 0.1, "volume": 1_000_000}
            for i in range(n)]


# --------------------------------------------------------------------------
# (c)/(d)/(e) — payload de /api/technicals/{ticker}
# --------------------------------------------------------------------------

def test_c_payload_de_technicals_traz_source_e_degradado(monkeypatch):
    c, main = _client(monkeypatch)

    def _candles(_symbol, rng=None, **_kw):
        async def go():
            return {"candles": _mk_candles(), "currency": "BRL", "source": "yahoo"}
        return go()

    monkeypatch.setattr(main.candle_provider, "get_history", _candles)
    r = c.get("/api/technicals/PETR4")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "source" in body and body["source"] == "yahoo"
    assert "degradado" in body and body["degradado"] is False


def test_d_degradado_true_so_quando_provedor_e_brapi_e_fatia_passou_de_80pct(monkeypatch):
    c, main = _client(monkeypatch)

    def _candles(_symbol, rng=None, **_kw):
        async def go():
            return {"candles": _mk_candles(), "currency": "BRL", "source": "brapi"}
        return go()

    monkeypatch.setattr(main.candle_provider, "get_history", _candles)
    monkeypatch.setattr(main.brapi_budget, "degradado", lambda f, now=None: True)

    monkeypatch.setattr(main.candle_provider, "provider_name", lambda: "brapi")
    r = c.get("/api/technicals/VALE3")
    assert r.json()["degradado"] is True

    _reset_caches()
    monkeypatch.setattr(main.candle_provider, "provider_name", lambda: "yahoo")
    r = c.get("/api/technicals/ITUB4")
    assert r.json()["degradado"] is False


def test_e_falha_no_indicador_de_orcamento_nao_derruba_a_rota(monkeypatch):
    c, main = _client(monkeypatch)

    def _candles(_symbol, rng=None, **_kw):
        async def go():
            return {"candles": _mk_candles(), "currency": "BRL", "source": "brapi"}
        return go()

    monkeypatch.setattr(main.candle_provider, "get_history", _candles)
    monkeypatch.setattr(main.candle_provider, "provider_name", lambda: "brapi")

    def _explode(f, now=None):
        raise RuntimeError("orçamento indisponível")

    monkeypatch.setattr(main.brapi_budget, "degradado", _explode)
    r = c.get("/api/technicals/BBAS3")
    assert r.status_code == 200, r.text
    assert r.json()["degradado"] is False


# --------------------------------------------------------------------------
# (f) — leg admin de C-30 (verify-only, web-admin/src/App.jsx:177 já lê isto)
# --------------------------------------------------------------------------

def test_f_candle_provider_snapshot_expoe_degradado_por_fatia_para_o_admin(monkeypatch):
    monkeypatch.setattr(candle_provider, "provider_name", lambda: "brapi")
    snap = candle_provider.snapshot()
    orc = snap["orcamentoBrapi"]
    assert orc is not None
    spot = orc["fatias"]["spot"]
    assert "degradado" in spot and isinstance(spot["degradado"], bool)
