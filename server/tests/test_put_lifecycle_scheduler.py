"""server/tests/test_put_lifecycle_scheduler.py — hook do `put_lifecycle`
pendurado no `scheduler_loop` real (Fase 11, Plano 02, Task 2).

Mesmo padrão de `test_put_bridge_scheduler.py`: banco temp real,
`asyncio.run(agent.scheduler_loop(..., once=True))`, `_gate_basico`
controlando `kill_switch_on`/`in_market_hours`/`list_server_users`/
`pregao.is_trading_day`. `put_lifecycle.maybe_run` é importado LOCALMENTE
dentro de `scheduler_loop` — o monkeypatch precisa mirar
`"app.put_lifecycle.maybe_run"` (módulo de ORIGEM), nunca um atributo no
namespace de `agent`.

DIFERENÇA DELIBERADA em relação ao molde de `put_bridge` (D-EXEC-11-02-01,
ver `.planning/notes/decisoes-autonomas-v1.2.md`): o hook deste plano vive
FORA do `if radar_fetch is not None and not kill_switch_on() and
pregao.is_trading_day():` — por isso, ao contrário de
`test_hook_nao_roda_com_kill_switch_ligado`/`test_hook_nao_roda_em_dia_sem_
pregao`/`test_hook_nao_roda_sem_radar_fetch` de `put_bridge`, aqui o hook
RODA em todos esses cenários (é medição, não execução de ordem — A-11-06,
razão 2, e T-11-10 do threat register)."""
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
    """`radar_daily`/`analysis_outcomes`/`fundamentals`/`put_bridge` viram
    no-ops silenciosos (nunca aparecem em `spy` — o que importa para a
    ordem deste arquivo é só ponte→ciclo de vida). `put_bridge.maybe_run`
    vira no-op que registra em `spy` quando pedido, para
    `test_hook_roda_depois_da_ponte` provar a ordem relativa ao hook novo."""
    async def _radar_daily_noop(*a, **k):
        return None

    async def _analysis_outcomes_noop(*a, **k):
        return None

    async def _fundamentals_noop(*a, **k):
        return None

    async def _signal_ledger_noop(*a, **k):
        return None

    async def _put_bridge_noop(*a, **k):
        if spy is not None:
            spy.append("put-bridge")
        return None

    monkeypatch.setattr("app.radar_daily.maybe_run", _radar_daily_noop)
    monkeypatch.setattr("app.analysis_outcomes.maybe_run", _analysis_outcomes_noop)
    monkeypatch.setattr("app.fundamentals.maybe_warm", _fundamentals_noop)
    monkeypatch.setattr("app.signal_ledger_job.maybe_run", _signal_ledger_noop)
    monkeypatch.setattr("app.put_bridge.maybe_run", _put_bridge_noop)


def test_hook_roda_em_dia_util(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _lifecycle_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.put_lifecycle.maybe_run", _lifecycle_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert len(chamadas) == 1
    assert chamadas[0] is c


def test_hook_roda_com_kill_switch_ligado(monkeypatch):
    """Diferença deliberada de `put_bridge` (D-EXEC-11-02-01): é medição, não
    execução de ordem — roda MESMO com o kill-switch ligado."""
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=True)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _lifecycle_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.put_lifecycle.maybe_run", _lifecycle_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert len(chamadas) == 1


def test_hook_roda_em_dia_sem_pregao(monkeypatch):
    """Diferença deliberada de `put_bridge`: o hook não depende de
    `pregao.is_trading_day()` — o próprio `should_run` interno já rejeita
    fim de semana; um feriado (dia útil == False aqui) ainda tenta rodar,
    sem custo de rede (só cache), então é seguro tentar."""
    c = _conn()
    _gate_basico(monkeypatch, dia_util=False, kill=False)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _lifecycle_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.put_lifecycle.maybe_run", _lifecycle_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert len(chamadas) == 1


def test_hook_roda_sem_radar_fetch(monkeypatch):
    """Diferença deliberada de `put_bridge`: o hook não depende de
    `radar_fetch` — lê só o `candle_cache`, não o Radar ao vivo."""
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _lifecycle_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.put_lifecycle.maybe_run", _lifecycle_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=None, once=True))

    assert len(chamadas) == 1


def test_excecao_do_hook_nao_derruba_a_passada(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False, pregao_aberto=True)
    _neutraliza_vizinhos(monkeypatch)

    async def _lifecycle_explode(conn):
        raise RuntimeError("boom put-lifecycle")

    monkeypatch.setattr("app.put_lifecycle.maybe_run", _lifecycle_explode)

    # Não deve levantar — o try/except próprio do hook absorve a exceção.
    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    # Prova de continuidade: o heartbeat (gravado no TOPO do laço, antes de
    # qualquer hook) foi gravado normalmente.
    hb = db.kv_get(c, "agentHeartbeat", user_id=None)
    assert hb is not None


def test_excecao_do_hook_nao_impede_ponte_nem_vizinhos(monkeypatch):
    """A exceção do ciclo de vida não pode impedir o hook da ponte (que
    roda ANTES) nem indicar qualquer interrupção do restante da passada."""
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False, pregao_aberto=True)
    chamadas_ponte = []

    async def _ponte_spy(conn):
        chamadas_ponte.append(1)
        return None

    async def _radar_daily_noop(*a, **k):
        return None

    async def _analysis_outcomes_noop(*a, **k):
        return None

    async def _fundamentals_noop(*a, **k):
        return None

    async def _signal_ledger_noop(*a, **k):
        return None

    async def _lifecycle_explode(conn):
        raise RuntimeError("boom put-lifecycle")

    monkeypatch.setattr("app.radar_daily.maybe_run", _radar_daily_noop)
    monkeypatch.setattr("app.analysis_outcomes.maybe_run", _analysis_outcomes_noop)
    monkeypatch.setattr("app.fundamentals.maybe_warm", _fundamentals_noop)
    monkeypatch.setattr("app.signal_ledger_job.maybe_run", _signal_ledger_noop)
    monkeypatch.setattr("app.put_bridge.maybe_run", _ponte_spy)
    monkeypatch.setattr("app.put_lifecycle.maybe_run", _lifecycle_explode)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert chamadas_ponte == [1]  # a ponte rodou normalmente, antes do hook que explodiu


def test_hook_roda_depois_da_ponte(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False)
    ordem = []
    _neutraliza_vizinhos(monkeypatch, spy=ordem)

    async def _lifecycle_spy(conn):
        ordem.append("put-lifecycle")
        return None

    monkeypatch.setattr("app.put_lifecycle.maybe_run", _lifecycle_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert ordem == ["put-bridge", "put-lifecycle"]
    assert ordem.index("put-bridge") < ordem.index("put-lifecycle")


def test_status_snapshot_nao_ganha_chave_nova(monkeypatch):
    import json

    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False)
    _neutraliza_vizinhos(monkeypatch)

    async def _lifecycle_noop(conn):
        return None

    monkeypatch.setattr("app.put_lifecycle.maybe_run", _lifecycle_noop)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    snap = agent.status_snapshot(c)
    assert "putLifecycle" not in json.dumps(snap, default=str)
