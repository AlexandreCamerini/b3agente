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
    # Nota review WR-02: com a cotação ACIMA do stop o plano inválido continua sem
    # vender (nada rompido); o stop válido por si, porém, protege (teste abaixo).
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


def test_wr02_alvo_invalido_nao_desliga_o_stop_valido():
    c = _conn()
    _seed(c, [dict(INVALIDA)])
    r = _run(c, {"PETR4": 23.30})                 # rompe o stop 23,36; alvo 21,58 é o inválido
    assert r["executed"] == 1 and _pos(c) is None
    assert any("stop atingido" in (e.get("text") or "") or e.get("kind") == "buy" for e in r["events"])


def test_wr02_alvo_invalido_nunca_vira_alvo_atingido():
    c = _conn()
    pos = {"t": "PETR4", "qty": 100, "avg": 25.0, "stop": 22.0, "alvo": 24.0}   # alvo ≤ PM
    _seed(c, [pos], {"rules": {"alvo": True}})
    r = _run(c, {"PETR4": 24.5})                  # >= alvo, mas o alvo é inválido
    assert r["executed"] == 0 and _pos(c) is not None
    assert len(_invalidos(r["events"])) == 1
    r2 = _run(c, {"PETR4": 21.9})                 # stop válido rompe
    assert r2["executed"] == 1


def test_wr02_marcos_efetivos_puro():
    assert agent.marcos_efetivos(dict(INVALIDA))[:2] == (True, False)
    assert agent.marcos_efetivos({"avg": 20, "stop": 19, "alvo": 25}) == (True, True, None)
    assert agent.marcos_efetivos({"avg": 20, "stop": 0, "alvo": 25})[:2] == (False, True)


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
    # Nota review CR-01: o stop gerido (BE) ainda é o que o ciclo entrega à
    # função; o R:R, porém, é medido contra o `stopInicial` (ver testes abaixo).
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


def test_cr01_alvo_dinamico_estende_com_stop_em_breakeven():
    pos = {"avg": 23.50, "stop": 23.50, "stopInicial": 22.50, "alvo": 25.50, "gestaoAuto": True}
    novo, crit = agent.avaliar_alvo_dinamico(25.60, pos, {"atr": 0.5})
    assert novo == 26.25 and "R:R 2.8:1" in crit
    # stop acima do PM (trailing) idem; legado sem stopInicial e stop >= PM não estende
    assert agent.avaliar_alvo_dinamico(25.60, {**pos, "stop": 24.0}, {"atr": 0.5})[0] == 26.25
    legado = {"avg": 23.50, "stop": 23.50, "alvo": 25.50}
    assert agent.avaliar_alvo_dinamico(25.60, legado, {"atr": 0.5}) == (None, None)


def test_cr01_ciclo_estende_alvo_com_gestao_ligada_e_fecha_na_terceira():
    c = _conn()
    pos = {"t": "PETR4", "qty": 100, "avg": 23.50, "stop": 22.50, "stopInicial": 22.50,
           "alvo": 25.50, "gestaoAuto": True}
    _seed(c, [pos], {"rules": {"alvo": True}, "alvoDinamico": True})
    r = _run(c, {"PETR4": 25.60}, snapshot_getter=_snap(0.5))
    p = _pos(c)
    assert r["executed"] == 0 and p["alvo"] == 26.25 and p["alvoExtensoes"] == 1
    assert p["stop"] >= 23.50                                  # gestão levou o stop ao BE ou acima
    assert any("Alvo dinâmico" in e["text"] for e in r["events"])
    db.kv_set(c, "positions", [{**p, "alvoExtensoes": 2, "alvo": 25.0}], user_id="u1")
    r2 = _run(c, {"PETR4": 25.60}, snapshot_getter=_snap(0.5))
    assert r2["executed"] == 1 and _pos(c) is None


# ---------------------------------------------------------------------------
# Entrada automática — D-06/D-07/D-08
# ---------------------------------------------------------------------------
from datetime import datetime

from app import candles, intraday, radar_daily, signal_ledger

HOJE = "2026-08-07"
AGORA = datetime(2026, 8, 7, 14, 30, tzinfo=intraday.BRT)
SETUP = "IFR2 (alta)"


@pytest.fixture
def _elegivel(monkeypatch):
    signal_ledger.reset_cache()
    monkeypatch.setattr(signal_ledger, "historico_snapshot",
                        lambda conn, **kw: {SETUP: {"expR": 0.07, "n": 2934, "elegivel": True,
                                                    "insuficiente": False}})


def _entrada(close, plano, caixa=100000.0, capital=100000.0, pct=1.0, alloc=10, risco_capital=None):
    c = _conn()
    db.kv_set(c, "positions", [], user_id="u1")
    db.kv_set(c, "cash", caixa, user_id="u1")
    db.kv_set(c, "watchlist", ["PETR4"], user_id="u1")
    cfg = db.kv_get(c, "config", user_id="u1")
    cfg["initialBudget"] = capital
    cfg["risco"] = {"pctPorTrade": pct, "capital": risco_capital}
    db.kv_set(c, "config", cfg, user_id="u1")
    radar_daily.store_result(c, candles.normalize_period(None), {"results": [{
        "ticker": "PETR4", "veredito": "Estudar",
        "plano": {"decisao": "COMPRAR", "lado": "alta", "setup": SETUP, **plano}}]}, "manual")
    db.kv_set(c, intraday.CHAVE, {
        "at": AGORA.isoformat(), "asOf": f"{HOJE} 14:15", "atLabel": "14:15", "universo": 1, "ativos": 1,
        "comLacuna": 0, "resultados": [{"ticker": "PETR4", "close": close, "asOf": f"{HOJE} 14:15",
                                        "cobertura": 1.0, "lacuna": False, "barraEmFormacao": False}],
        "erros": []}, user_id=None)
    ag = {"entradaAuto": True, "allocPct": alloc, "maxOpsDia": 3, "maxValorOp": 0}
    par = agent.agent_params(ag, app_mode="operador")
    events = []
    ex = asyncio.run(agent._avaliar_entradas(c, "u1", ag, par, "operador", [], 0, events, agora=AGORA))
    return c, ex, events


PLANO = {"entrada": 20.0, "stop": 19.0, "alvo": 23.5, "alvo2": 23.5, "alvo1": 21.0,
         "riscoPorAcao": 1.0, "gatilho": 20.0, "invalidacao": 19.0}


def test_entrada_compra_com_marcos_do_plano_e_texto_do_buy_intacto(_elegivel):
    c, ex, events = _entrada(20.10, PLANO)
    assert ex == 1
    p = _pos(c)
    assert (p["stop"], p["alvo"], p["stopInicial"], p["gestaoAuto"]) == (19.0, 23.5, 19.0, True)
    buy = [e for e in events if e["kind"] == "buy"][0]
    assert buy["text"].startswith("Entrada automática: PETR4 comprado (")
    assert buy["text"].endswith("a R$ 20.10 — gatilho de entrada atingido.")
    assert any(e["kind"] == "info" and "Marcos do motor gravados em PETR4" in e["text"] for e in events)


def test_entrada_recusa_rr_baixo_ao_preco_executado_e_avisa_uma_vez(_elegivel):
    plano = {**PLANO, "stop": 17.0, "invalidacao": 17.0, "riscoPorAcao": 3.0}
    c, ex, events = _entrada(21.5, plano)          # (23,5-21,5)/(21,5-17)=0,4
    assert ex == 0 and _pos(c) is None
    avisos = [e for e in events if "R:R" in e["text"] and "não executada" in e["text"]]
    assert len(avisos) == 1 and "0,4:1" in avisos[0]["text"]
    ev2 = []
    ag = {"entradaAuto": True, "allocPct": 10, "maxOpsDia": 3, "maxValorOp": 0}
    asyncio.run(agent._avaliar_entradas(c, "u1", ag, agent.agent_params(ag, app_mode="operador"),
                                        "operador", [], 0, ev2, agora=AGORA))
    assert ev2 == []                                # dedupe 1x por ticker/dia


def test_entrada_alem_de_meio_r_do_gatilho_no_preco_executado_nao_persiga(_elegivel):
    plano = {**PLANO, "stop": 18.95, "riscoPorAcao": 1.05}
    c, ex, events = _entrada(20.52, plano)         # timing ainda diz "gatilho"; execução diz não persiga
    assert ex == 0 and _pos(c) is None
    assert any("não persiga" in e["text"] and "não executada" in e["text"] for e in events)


def test_entrada_sizing_por_risco_limitado_pela_alocacao(_elegivel):
    # risco 1000 / 1,10 por ação = 909 -> 900; teto alloc 10% de 100000 / 20,10 = 497 -> 400
    c, ex, _ = _entrada(20.10, PLANO, alloc=10)
    assert ex == 1 and _pos(c)["qty"] == 400
    # sem teto relevante (alloc 100%): 900 pelo risco
    c, ex, _ = _entrada(20.10, PLANO, alloc=100)
    assert ex == 1 and _pos(c)["qty"] == 900


def test_entrada_menos_de_um_lote_nao_compra_e_avisa(_elegivel):
    c, ex, events = _entrada(20.10, PLANO, caixa=10000.0, alloc=10)
    assert ex == 0 and _pos(c) is None
    assert any(e["kind"] == "warn" and "não cobre 1 lote" in e["text"] for e in events)


def test_entrada_capital_vem_de_risco_capital_quando_numerico(_elegivel):
    c, ex, _ = _entrada(20.10, PLANO, capital=10000.0, alloc=100)      # initialBudget 10000 -> 90 ações -> sem lote
    assert ex == 0
    c2, ex2, _ = _entrada(20.10, PLANO, capital=10000.0, alloc=100, risco_capital=100000.0)
    assert ex2 == 1 and _pos(c2)["qty"] == 900


def test_entrada_plano_sem_stop_ou_alvo_numericos_e_recusada_com_motivo(_elegivel):
    plano = {k: v for k, v in PLANO.items() if k not in ("alvo", "alvo2")}
    c, ex, events = _entrada(20.10, plano)
    assert ex == 0 and _pos(c) is None
    assert any("não executada" in e["text"] and "stop e alvo" in e["text"] for e in events)


# ---------------------------------------------------------------------------
# Review WR-03 — âncora do 1R (`stopInicial`)
# ---------------------------------------------------------------------------
def test_wr03_edicao_manual_do_stop_reancora_o_1r():
    c = _conn()
    _seed(c, [dict(GERIDA)])                                   # PM 20, stopInicial 19
    store.set_position(c, "PETR4", stop=19.5, has_stop=True, manual=True, user_id="u1")
    assert _pos(c)["stopInicial"] == 19.5                      # 1R passa a ser 0,5
    assert agent.nivel_gestao(_pos(c), 20.5, {}) == (20.0, "gestao_breakeven")
    # stop >= PM remove a âncora; limpar também
    store.set_position(c, "PETR4", stop=20.2, has_stop=True, manual=True, user_id="u1")
    assert "stopInicial" not in _pos(c)


def test_wr03_ajuste_do_agente_nao_mexe_na_ancora():
    c = _conn()
    _seed(c, [dict(GERIDA)])
    _run(c, {"PETR4": 21.0}, snapshot_getter=_snap(0.3))        # gestão sobe o stop para 20,4
    p = _pos(c)
    assert p["stop"] == 20.4 and p["stopInicial"] == 19.0


def test_wr03_legado_sem_ancora_ganha_stopinicial_na_primeira_avaliacao():
    c = _conn()
    leg = {k: v for k, v in GERIDA.items() if k not in ("stopInicial", "gestaoAuto")}
    _seed(c, [leg])
    _run(c, {"PETR4": 20.5}, snapshot_getter=_snap(0.3))        # < 1R: gestão não age, mas ancora
    assert _pos(c)["stopInicial"] == 19.0
    _run(c, {"PETR4": 21.0}, snapshot_getter=_snap(0.3))
    assert _pos(c)["stop"] == 20.4 and _pos(c)["stopInicial"] == 19.0


def test_in04_stop_nao_ajustado_avisa_uma_vez_por_dia(monkeypatch):
    c = _conn()
    _seed(c, [dict(GERIDA)])

    def _boom(*a, **k):
        raise ValueError("recusado de propósito")
    monkeypatch.setattr(store, "set_position", _boom)
    r1 = _run(c, {"PETR4": 21.0}, snapshot_getter=_snap(0.3))
    r2 = _run(c, {"PETR4": 21.0}, snapshot_getter=_snap(0.3))
    avisos = lambda r: [e for e in r["events"] if "não ajustado" in e["text"]]  # noqa: E731
    assert len(avisos(r1)) == 1 and avisos(r2) == []
