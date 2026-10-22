"""Fase 50 plano 05 — o Operador server-side e os marcos do plano.

Guardião de D-06/D-07/D-08 (entrada automática com marcos e sizing por risco),
D-13 (marco inválido nunca vende), D-14 (gestão padrão: breakeven a 1R +
trailing 2×ATR, só sobe) e D-15 (alvo dinâmico opt-in, medido do stop gerido).
"""
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


def _seed(c, positions, ag=None):
    db.kv_set(c, "positions", positions, user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    db.kv_set(c, "agent", {"autonomous": True, "serverEnabled": True, "mode": "executar",
                           "maxOpsDia": 5, **(ag or {})}, user_id="u1")


def _snap(atr):
    async def getter(_t):
        return {"candles": [], "indicators": {"atr14": [atr]}}
    return getter


def _run(c, prices, snapshot_getter=None):
    async def getter(tickers):
        return {t: {"price": prices.get(t)} for t in tickers}
    return asyncio.run(agent.run_cycle_for(c, "u1", getter, snapshot_getter=snapshot_getter))


def _pos(c, t="PETR4"):
    return next((p for p in db.kv_get(c, "positions", user_id="u1") if p["t"] == t), None)


# ---------------------------------------------------------------------------
# nivel_gestao (puro) — D-14
# ---------------------------------------------------------------------------
def test_gestao_nao_age_antes_de_1r():
    pos = {"avg": 20.0, "stop": 19.0, "stopInicial": 19.0, "gestaoAuto": True}
    assert agent.nivel_gestao(pos, 20.9, {"atr": 0.3}) == (None, None)


def test_gestao_legada_sem_chave_gestaoauto_entra_ligada():
    legado = {"avg": 20.0, "stop": 19.0}
    novo = {"avg": 20.0, "stop": 19.0, "stopInicial": 19.0, "gestaoAuto": True}
    assert agent.nivel_gestao(legado, 20.9, {"atr": 0.3}) == (None, None)
    assert agent.nivel_gestao(legado, 21.0, {"atr": 0.3}) == agent.nivel_gestao(novo, 21.0, {"atr": 0.3})


def test_gestao_legada_com_stop_acima_do_pm_so_trailing():
    pos = {"avg": 23.01, "stop": 23.36, "alvo": 25.0}
    assert agent.nivel_gestao(pos, 24.5, {"atr": 0.30}) == (23.9, "gestao_trailing")
    assert agent.nivel_gestao(pos, 24.5, {}) == (None, None)


def test_gestao_exige_stop_e_avg():
    assert agent.nivel_gestao({"avg": 20.0, "stop": None}, 30.0, {"atr": 0.3}) == (None, None)
    assert agent.nivel_gestao({"avg": None, "stop": 19.0}, 30.0, {"atr": 0.3}) == (None, None)


def test_gestao_em_1r_sobe_para_o_maior_entre_breakeven_e_trailing():
    pos = {"avg": 20.0, "stop": 19.0, "stopInicial": 19.0, "gestaoAuto": True}
    assert agent.nivel_gestao(pos, 21.0, {"atr": 0.3}) == (20.4, "gestao_trailing")
    assert agent.nivel_gestao(pos, 21.0, {}) == (20.0, "gestao_breakeven")
    # trailing abaixo do PM: o breakeven vale
    assert agent.nivel_gestao(pos, 21.0, {"atr": 0.8}) == (20.0, "gestao_breakeven")


def test_gestao_desligada_so_com_false():
    pos = {"avg": 20.0, "stop": 19.0, "stopInicial": 19.0, "gestaoAuto": False}
    assert agent.nivel_gestao(pos, 25.0, {"atr": 0.3}) == (None, None)


# ---------------------------------------------------------------------------
# Ciclo — D-13 (plano inválido)
# ---------------------------------------------------------------------------
INVALIDA = {"t": "PETR4", "qty": 100, "avg": 23.01, "stop": 23.36, "alvo": 21.58}


def _invalidos(events):
    return [e for e in events if e.get("kind") == "warn" and "plano inválido" in e["text"]]


def test_plano_invalido_nao_vende_e_avisa_uma_vez_por_dia():
    c = _conn()
    _seed(c, [dict(INVALIDA)])
    hist0 = list(store.get(c, "history", user_id="u1") or [])
    r1 = _run(c, {"PETR4": 23.51})
    r2 = _run(c, {"PETR4": 23.51})
    assert r1["executed"] == 0 and r2["executed"] == 0
    assert len(_invalidos(r1["events"])) == 1
    assert _invalidos(r2["events"]) == []
    assert _pos(c)["qty"] == 100
    assert list(store.get(c, "history", user_id="u1") or []) == hist0
    assert _pos(c)["stop"] == 23.36            # nem a gestão mexe em plano inválido


def test_plano_invalido_fora_do_pregao_nao_diz_alvo_atingido(monkeypatch):
    c = _conn()
    _seed(c, [dict(INVALIDA)])
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **k: False)
    r = _run(c, {"PETR4": 23.51})
    assert r["events"] == []


# ---------------------------------------------------------------------------
# Ciclo — D-14 (gestão) e monotonicidade
# ---------------------------------------------------------------------------
GERIDA = {"t": "PETR4", "qty": 100, "avg": 20.0, "stop": 19.0, "stopInicial": 19.0,
          "alvo": 30.0, "gestaoAuto": True}


def test_gestao_sobe_o_stop_e_nunca_desce():
    c = _conn()
    _seed(c, [dict(GERIDA)])
    r1 = _run(c, {"PETR4": 21.0}, snapshot_getter=_snap(0.3))
    assert _pos(c)["stop"] == 20.4
    assert any("Gestão" in e["text"] and "20,40" in e["text"] for e in r1["events"])
    _run(c, {"PETR4": 20.8}, snapshot_getter=_snap(0.3))       # 20.2 < 20.4 -> não desce
    assert _pos(c)["stop"] == 20.4


def test_gestao_breakeven_sem_atr_diz_preco_de_entrada():
    c = _conn()
    _seed(c, [dict(GERIDA)])
    r = _run(c, {"PETR4": 21.0})
    assert _pos(c)["stop"] == 20.0
    assert any("preço de entrada" in e["text"] or "preço de entrada" in e["text"].lower() for e in r["events"])


def test_gestao_desligada_nao_mexe_no_stop():
    c = _conn()
    _seed(c, [{**GERIDA, "gestaoAuto": False}])
    _run(c, {"PETR4": 25.0}, snapshot_getter=_snap(0.3))
    assert _pos(c)["stop"] == 19.0


def test_set_position_com_valueerror_vira_warn_e_o_ciclo_segue(monkeypatch):
    c = _conn()
    _seed(c, [dict(GERIDA), {"t": "VALE3", "qty": 50, "avg": 60.0, "stop": 58.0, "alvo": 70.0}])

    def _boom(*a, **k):
        raise ValueError("recusado de propósito")
    monkeypatch.setattr(store, "set_position", _boom)
    r = _run(c, {"PETR4": 21.0, "VALE3": 57.0})
    assert any("recusado de propósito" in e["text"] for e in r["events"] if e["kind"] == "warn")
    assert r["executed"] == 1                                  # VALE3 vendida no stop


def test_alvo_dinamico_mede_do_stop_ja_gerido(monkeypatch):
    c = _conn()
    _seed(c, [{**GERIDA, "alvo": 20.5}], {"rules": {"alvo": True}, "alvoDinamico": True})
    vistos = []
    orig = agent.avaliar_alvo_dinamico

    def _spy(price, pos, ctx=None):
        vistos.append(pos["stop"])
        return orig(price, pos, ctx)
    monkeypatch.setattr(agent, "avaliar_alvo_dinamico", _spy)
    _run(c, {"PETR4": 21.0}, snapshot_getter=_snap(0.8))       # trailing 19.4 < PM -> breakeven 20.0
    assert vistos == [20.0]
