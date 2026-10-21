"""quick 261021-spd — ciclo do servidor com posição travada como lastro.

Antes: o ciclo chamava `store.sell` em posição 100% travada a cada tick,
gravando rejeição nova no histórico (a poda por CAP_REJEICOES descartava
rejeições legítimas) e um warn novo no Diário. Agora pré-checa com
`store.qty_livre` e avisa 1x por posição por dia BRT."""
import asyncio
import os
import tempfile

import pytest

from app import agent, db, store

from .relogio_pregao import abrir_pregao


@pytest.fixture(autouse=True)
def _pregao_aberto(monkeypatch):
    abrir_pregao(monkeypatch)


def _conn():
    d = tempfile.mkdtemp()
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                         "appMode": "operador"}, user_id="u1")
    return c


def _seed(c, positions):
    db.kv_set(c, "positions", positions, user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    db.kv_set(c, "agent", {"autonomous": True, "serverEnabled": True, "mode": "executar",
                           "maxOpsDia": 3}, user_id="u1")


def _run(c, prices):
    async def getter(tickers):
        return {t: {"price": prices.get(t)} for t in tickers}
    return asyncio.run(agent.run_cycle_for(c, "u1", getter))


def _lastro(events, t="PETR4"):
    return [e for e in events if e.get("kind") == "warn" and e.get("t") == t and "lastro" in e["text"]]


TRAVADA = {"t": "PETR4", "qty": 100, "qtyTravada": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}


def test_100_travada_nao_vende_nao_rejeita_e_avisa_uma_vez_por_dia():
    c = _conn()
    _seed(c, [dict(TRAVADA)])
    hist0 = list(store.get(c, "history", user_id="u1") or [])
    r1 = _run(c, {"PETR4": 37.5})
    r2 = _run(c, {"PETR4": 37.5})
    assert r1["executed"] == 0 and r2["executed"] == 0
    assert list(store.get(c, "history", user_id="u1") or []) == hist0  # 0 rejeições novas
    assert len(_lastro(r1["events"]) + _lastro(r2["events"])) == 1
    assert int(db.kv_get(c, "agent", {}, user_id="u1").get("opsToday") or 0) == 0
    assert db.kv_get(c, "positions", user_id="u1")[0]["qty"] == 100
    assert db.kv_get(c, "cash", user_id="u1") == 100000.0


def test_travada_nao_aborta_o_laco_segunda_posicao_e_vendida():
    c = _conn()
    _seed(c, [dict(TRAVADA),
              {"t": "VALE3", "qty": 50, "avg": 60.0, "stop": 58.0, "alvo": 70.0}])
    r = _run(c, {"PETR4": 37.5, "VALE3": 57.0})
    assert r["executed"] == 1
    restantes = [p["t"] for p in db.kv_get(c, "positions", user_id="u1")]
    assert restantes == ["PETR4"]
    assert len(_lastro(r["events"])) == 1


def test_virada_de_dia_reavisa(monkeypatch):
    c = _conn()
    _seed(c, [dict(TRAVADA)])
    assert len(_lastro(_run(c, {"PETR4": 37.5})["events"])) == 1
    assert _lastro(_run(c, {"PETR4": 37.5})["events"]) == []
    monkeypatch.setattr(agent, "_today", lambda: "2099-01-01")
    assert len(_lastro(_run(c, {"PETR4": 37.5})["events"])) == 1


def test_parcial_vende_so_o_livre_e_o_evento_cita_a_quantidade():
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 300, "qtyTravada": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}])
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 1
    assert db.kv_get(c, "positions", user_id="u1")[0]["qty"] == 100
    h0 = store.get(c, "history", user_id="u1")[0]
    assert h0["type"] == "VENDA" and h0["qty"] == 200
    compra = [e for e in r["events"] if e.get("kind") == "buy"][0]
    assert "200" in compra["text"] and compra["pnl"] is not None
    assert "travadas" in compra["text"]
