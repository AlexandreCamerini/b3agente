"""server/tests/test_put_bridge_scheduler.py — hook do `put_bridge` pendurado
no `scheduler_loop` real (Fase 10, Plano 02, Task 2).

Mesmo padrão de `test_signal_ledger_scheduler.py`: banco temp real,
`asyncio.run(agent.scheduler_loop(..., once=True))`, `_gate_basico`
controlando `kill_switch_on`/`in_market_hours`/`list_server_users`/
`pregao.is_trading_day`. `put_bridge.maybe_run` é importado LOCALMENTE
dentro de `scheduler_loop` — o monkeypatch precisa mirar
`"app.put_bridge.maybe_run"` (módulo de ORIGEM), nunca um atributo no
namespace de `agent`.
"""
import asyncio
import os
import tempfile

import pytest

from app import agent, db


def _conn():
    d = tempfile.mkdtemp()
    return db.connect(os.path.join(d, "b3.db"))


async def _fake_quotes(tickers):
    return {t: {"price": None} for t in tickers}


async def _fake_radar_fetch(*a, **k):
    return {"candles": [], "currency": "BRL"}


def _gate_basico(monkeypatch, *, dia_util: bool = True, kill: bool = False,
                  pregao_aberto: bool = False):
    monkeypatch.setattr(agent, "kill_switch_on", lambda: kill)
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **k: pregao_aberto)
    monkeypatch.setattr(agent, "list_server_users", lambda conn: [])
    monkeypatch.setattr("app.pregao.is_trading_day", lambda *a, **k: dia_util)


def _neutraliza_vizinhos(monkeypatch, spy: list | None = None):
    """`radar_daily`/`analysis_outcomes`/`fundamentals` viram no-ops
    silenciosos (nunca aparecem em `spy` — o que importa para a ordem deste
    arquivo é só ledger→put). `signal_ledger_job.maybe_run` vira no-op que
    registra em `spy` quando pedido, para `test_hook_roda_depois_do_ledger`
    provar a ordem relativa ao hook novo."""
    async def _radar_daily_noop(*a, **k):
        return None

    async def _analysis_outcomes_noop(*a, **k):
        return None

    async def _fundamentals_noop(*a, **k):
        return None

    async def _signal_ledger_noop(*a, **k):
        if spy is not None:
            spy.append("ledger")
        return None

    monkeypatch.setattr("app.radar_daily.maybe_run", _radar_daily_noop)
    monkeypatch.setattr("app.analysis_outcomes.maybe_run", _analysis_outcomes_noop)
    monkeypatch.setattr("app.fundamentals.maybe_warm", _fundamentals_noop)
    monkeypatch.setattr("app.signal_ledger_job.maybe_run", _signal_ledger_noop)


def test_hook_roda_em_dia_util_com_radar_fetch(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _put_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.put_bridge.maybe_run", _put_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert len(chamadas) == 1
    assert chamadas[0] is c


def test_hook_nao_roda_em_dia_sem_pregao(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=False, kill=False)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _put_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.put_bridge.maybe_run", _put_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert chamadas == []


def test_hook_nao_roda_com_kill_switch_ligado(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=True)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _put_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.put_bridge.maybe_run", _put_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert chamadas == []


def test_hook_nao_roda_sem_radar_fetch(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _put_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.put_bridge.maybe_run", _put_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=None, once=True))

    assert chamadas == []


def test_excecao_do_hook_nao_derruba_a_passada(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False, pregao_aberto=True)
    _neutraliza_vizinhos(monkeypatch)

    async def _put_explode(conn):
        raise RuntimeError("boom put-bridge")

    monkeypatch.setattr("app.put_bridge.maybe_run", _put_explode)

    # Não deve levantar — o try/except próprio do hook absorve a exceção.
    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    # Prova de continuidade: o heartbeat (gravado no TOPO do laço, antes de
    # qualquer hook) foi gravado normalmente — o mesmo padrão de prova de
    # `test_signal_ledger_scheduler.test_excecao_do_hook_nao_derruba_a_passada`.
    hb = db.kv_get(c, "agentHeartbeat", user_id=None)
    assert hb is not None


def test_hook_roda_depois_do_ledger(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False)
    ordem = []
    _neutraliza_vizinhos(monkeypatch, spy=ordem)

    async def _put_spy(conn):
        ordem.append("put")
        return None

    monkeypatch.setattr("app.put_bridge.maybe_run", _put_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert ordem == ["ledger", "put"]
    assert ordem.index("ledger") < ordem.index("put")
