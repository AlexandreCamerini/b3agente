"""quick 261013-vai — nenhuma EXECUÇÃO simulada fora do pregão (motor).

Relógio SEMPRE injetado (`.relogio_pregao`); `B3_DEV_MERCADO_ABERTO` só
aparece no teste da própria flag (A2). Cobre: portão em `_run_cycle_inner`
(F1–F6, A1–A3, T1–T4), aviso deduplicado de ação (D1–D4), vocabulário (S1),
e — acrescentados na Tarefa 1b — vencimento fora do portão (V1–V4), aviso
GENÉRICO de opção (V7–V9, B2) e `somente_vencimento` (T5).
"""
import asyncio
import os
import tempfile
from datetime import date, datetime

import pytest

from app import agent, db, pregao, skill_ref, store
from .relogio_pregao import fixar_instante, injetar_relogio

BRT = pregao.BRT
QUA_14H = datetime(2026, 10, 14, 14, 0, tzinfo=BRT)


@pytest.fixture(autouse=True)
def _env_limpo(monkeypatch):
    monkeypatch.delenv("B3_AFTER_MARKET", raising=False)
    monkeypatch.delenv("B3_DEV_MERCADO_ABERTO", raising=False)


def _conn(modo="operador"):
    d = tempfile.mkdtemp()
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    cfg = {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"}}
    if modo:
        cfg["appMode"] = modo
    store.set_config(c, cfg, user_id="u1")
    return c


def _seed(c, ag=None, positions=None, opts=None):
    db.kv_set(c, "positions",
              positions if positions is not None else
              [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}], user_id="u1")
    db.kv_set(c, "optionPositions", opts or [], user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    db.kv_set(c, "agent", {"autonomous": True, "serverEnabled": True, "mode": "executar",
                            "maxOpsDia": 3, **(ag or {})}, user_id="u1")


def _quotes(prices):
    async def getter(tickers):
        return {t: {"price": prices.get(t)} for t in tickers}
    return getter


def _run(c, prices, **kw):
    return asyncio.run(agent.run_cycle_for(c, "u1", _quotes(prices), **kw))


def _avisos(r):
    return [e for e in r["events"] if e.get("kind") == "warn" and "Mercado fechado" in e.get("text", "")]


def _texto_aviso(modo="operador", ticker="PETR4", motivo="stop"):
    return skill_ref.execucao_fora_pregao_txt(modo, "aviso_diario", ticker=ticker, motivo=motivo)


def _nada_executado(c):
    pos = db.kv_get(c, "positions", user_id="u1")
    assert len(pos) == 1 and pos[0]["t"] == "PETR4" and pos[0]["qty"] == 100
    assert db.kv_get(c, "cash", user_id="u1") == 100000.0
    assert not [h for h in (db.kv_get(c, "history", [], user_id="u1") or []) if h.get("type") == "VENDA"]


FECHADOS = [
    ("F1-noite", datetime(2026, 10, 14, 22, 0, tzinfo=BRT)),
    ("F2-sabado", datetime(2026, 10, 17, 14, 0, tzinfo=BRT)),
    ("F3-feriado", datetime(2026, 11, 2, 14, 0, tzinfo=BRT)),
    ("F4-antes-da-abertura", datetime(2026, 10, 14, 9, 30, tzinfo=BRT)),
    ("F5-call", datetime(2026, 10, 14, 16, 56, tzinfo=BRT)),
    ("F5-zona-morta", datetime(2026, 10, 14, 17, 10, tzinfo=BRT)),
    ("F6-after-sem-optin", datetime(2026, 10, 14, 17, 45, tzinfo=BRT)),
]


def test_pre_condicao_feriado_f3():
    assert pregao.is_holiday(date(2026, 11, 2))


@pytest.mark.parametrize("nome,instante", FECHADOS, ids=[n for n, _ in FECHADOS])
def test_fechado_nao_executa_e_avisa(monkeypatch, nome, instante):
    fixar_instante(monkeypatch, instante)
    c = _conn()
    _seed(c)
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 0
    assert r["mercadoFechado"] is True
    _nada_executado(c)
    assert not [e for e in r["events"] if e.get("kind") == "buy"]
    av = _avisos(r)
    assert len(av) == 1 and av[0]["text"] == _texto_aviso()


def test_a1_after_market_com_optin_executa(monkeypatch):
    monkeypatch.setenv("B3_AFTER_MARKET", "1")
    fixar_instante(monkeypatch, datetime(2026, 10, 14, 17, 45, tzinfo=BRT))
    c = _conn()
    _seed(c)
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 1 and not r.get("mercadoFechado")


def test_a2_dev_forcado_executa_no_sabado(monkeypatch):
    """ÚNICO uso da flag: testando a própria flag (herança de staging)."""
    monkeypatch.setenv("B3_DEV_MERCADO_ABERTO", "1")
    fixar_instante(monkeypatch, datetime(2026, 10, 17, 14, 0, tzinfo=BRT))
    c = _conn()
    _seed(c)
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 1


def test_a3_pregao_vende_pelo_motor(monkeypatch):
    fixar_instante(monkeypatch, QUA_14H)
    c = _conn()
    _seed(c)
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 1
    ev = [e for e in r["events"] if e.get("kind") == "buy"]
    assert len(ev) == 1 and ev[0]["tag"] == "stop"
    assert db.kv_get(c, "positions", user_id="u1") == []


def test_t1_trailing_fechado_nao_sobe_o_stop(monkeypatch):
    fixar_instante(monkeypatch, datetime(2026, 10, 14, 22, 0, tzinfo=BRT))
    c = _conn()
    _seed(c, ag={"rules": {"trailing": True}, "trailingPct": 5})
    _run(c, {"PETR4": 44.0})
    assert db.kv_get(c, "positions", user_id="u1")[0]["stop"] == 38.0


def test_t2_alvo_dinamico_fechado_nao_estende(monkeypatch):
    fixar_instante(monkeypatch, datetime(2026, 10, 14, 22, 0, tzinfo=BRT))
    c = _conn()
    _seed(c, ag={"alvoDinamico": True})
    chamadas = []

    async def snap(t):
        chamadas.append(t)
        return {"candles": [], "indicators": {"atr14": [1.0]}}
    _run(c, {"PETR4": 46.0}, snapshot_getter=snap)
    p = db.kv_get(c, "positions", user_id="u1")[0]
    assert p["alvo"] == 45.0 and not p.get("alvoExtensoes")
    assert chamadas == []  # T4


def test_t3_entradas_so_no_pregao(monkeypatch):
    chamadas = []

    async def espiao(*a, **k):
        chamadas.append(1)
        return a[6] if len(a) > 6 else 0
    monkeypatch.setattr(agent, "_avaliar_entradas", espiao)
    fixar_instante(monkeypatch, datetime(2026, 10, 14, 22, 0, tzinfo=BRT))
    c = _conn()
    _seed(c)
    _run(c, {"PETR4": 40.0})
    assert chamadas == []
    fixar_instante(monkeypatch, QUA_14H)
    _run(c, {"PETR4": 40.0})
    assert chamadas == [1]


def test_d1_dedupe_por_dia_e_por_ticker(monkeypatch):
    fixar_instante(monkeypatch, datetime(2026, 10, 14, 22, 0, tzinfo=BRT))
    c = _conn()
    _seed(c, positions=[
        {"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0},
        {"t": "VALE3", "qty": 100, "avg": 60.0, "stop": 55.0, "alvo": 65.0}])
    r1 = _run(c, {"PETR4": 37.5, "VALE3": 66.0})
    assert len(_avisos(r1)) == 2
    assert {e["text"] for e in _avisos(r1)} == {_texto_aviso(), _texto_aviso(ticker="VALE3", motivo="alvo")}
    kv = db.kv_get(c, "avisoForaPregao", user_id="u1")
    assert kv["data"] == "2026-10-14" and set(kv["chaves"]) == {"acao:PETR4", "acao:VALE3"}
    r2 = _run(c, {"PETR4": 37.5, "VALE3": 66.0})
    assert _avisos(r2) == []
    log = [e for e in db.kv_get(c, "agentLog", [], user_id="u1") if "Mercado fechado" in e["text"]]
    assert len(log) == 2
    fixar_instante(monkeypatch, datetime(2026, 10, 15, 22, 0, tzinfo=BRT))
    r3 = _run(c, {"PETR4": 37.5, "VALE3": 66.0})
    assert len(_avisos(r3)) == 2


def test_d1_sem_breach_nao_avisa_nem_escreve_no_diario(monkeypatch):
    fixar_instante(monkeypatch, datetime(2026, 10, 14, 22, 0, tzinfo=BRT))
    c = _conn()
    _seed(c)
    r = _run(c, {"PETR4": 41.0})
    assert r["events"] == [] and r["mercadoFechado"] is True
    assert not db.kv_get(c, "agentLog", [], user_id="u1")


def test_d2_modo_estudo_usa_texto_educacional(monkeypatch):
    fixar_instante(monkeypatch, datetime(2026, 10, 14, 22, 0, tzinfo=BRT))
    c = _conn(modo=None)
    _seed(c)
    r = _run(c, {"PETR4": 37.5})
    av = _avisos(r)
    assert len(av) == 1 and av[0]["text"] == _texto_aviso("educacional")
    assert av[0]["text"] != _texto_aviso("operador")


def test_d3_abertura_executa_com_gap_e_pnl_do_motor(monkeypatch):
    fixar_instante(monkeypatch, datetime(2026, 10, 14, 22, 0, tzinfo=BRT))
    c = _conn()
    _seed(c)
    _run(c, {"PETR4": 37.5})
    _nada_executado(c)
    fixar_instante(monkeypatch, datetime(2026, 10, 15, 10, 30, tzinfo=BRT))
    r = _run(c, {"PETR4": 36.0})
    assert r["executed"] == 1
    ev = [e for e in r["events"] if e.get("kind") == "buy"][0]
    assert ev["pnl"] == pytest.approx(-400.0)
    h = [h for h in db.kv_get(c, "history", user_id="u1") if h.get("type") == "VENDA"]
    assert h and h[0]["price"] == 36.0


def test_d4_apenas_sinalizar_fechado_avisa_fora_do_pregao(monkeypatch):
    fixar_instante(monkeypatch, datetime(2026, 10, 14, 22, 0, tzinfo=BRT))
    c = _conn()
    _seed(c, ag={"mode": "sinalizar", "autonomous": False})
    r = _run(c, {"PETR4": 37.5})
    assert len(_avisos(r)) == 1
    assert not [e for e in r["events"] if "Sinal do agente" in e["text"]]


def test_s1_vocabulario():
    with pytest.raises(ValueError):
        skill_ref.execucao_fora_pregao_txt("operador", "botao_bloqueado")
    assert "{" not in skill_ref.execucao_fora_pregao_txt("operador", "botao_bloqueado_sem_hora")
    with pytest.raises(ValueError):
        skill_ref.execucao_fora_pregao_txt("operador", "aviso_diario", ticker="X")
    with pytest.raises(KeyError):
        skill_ref.execucao_fora_pregao_txt("operador", "nao_existe")
    assert skill_ref.execucao_fora_pregao_txt("xpto", "ciclo_fechado", abertura="10:00") == \
        skill_ref.execucao_fora_pregao_txt("educacional", "ciclo_fechado", abertura="10:00")
    chaves = {"aviso_diario", "aviso_opcao", "ciclo_fechado", "ciclo_fechado_sem_hora", "status_indeterminado",
              "opcao_bloqueada", "opcao_bloqueada_sem_hora", "opcao_bloqueada_acao",
              "botao_bloqueado", "botao_bloqueado_sem_hora"}
    for modo in ("operador", "educacional"):
        assert set(skill_ref.EXECUCAO_FORA_PREGAO[modo]) == chaves
