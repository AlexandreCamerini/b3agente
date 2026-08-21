"""ADR-017 (Bloco 1) — hook diário do ledger pendurado no `scheduler_loop`.

Task 1 (07-06): `signal_ledger_job.maybe_run` roda dentro do MESMO bloco
guardado que `radar_daily.maybe_run`/`analysis_outcomes.maybe_run`/
`fundamentals.maybe_warm` (radar_fetch is not None and not kill_switch_on()
and pregao.is_trading_day()), DEPOIS de `fundamentals.maybe_warm`, com
try/except PRÓPRIO — uma exceção do hook não pode derrubar o resto da
passada (heartbeat, kill-switch, ciclo de stop/alvo).

Todos os testes usam banco temp real + `asyncio.run(agent.scheduler_loop(...,
once=True))`, mesmo padrão de `test_ordens_pendentes_scheduler.py`. Os hooks
internos ao bloco (`radar_daily.maybe_run`, `analysis_outcomes.maybe_run`,
`fundamentals.maybe_warm`, `signal_ledger_job.maybe_run`) são importados
LOCALMENTE dentro de `scheduler_loop` — monkeypatch precisa mirar o atributo
no MÓDULO DE ORIGEM (`"app.radar_daily.maybe_run"`), nunca no namespace de
`agent`, senão o import local resolve para a função real e o spy nunca é
chamado.
"""
import asyncio
import os
import tempfile

import pytest

from app import agent, db, store


def _conn():
    d = tempfile.mkdtemp()
    return db.connect(os.path.join(d, "b3.db"))


async def _fake_quotes(tickers):
    return {t: {"price": None} for t in tickers}


async def _fake_radar_fetch(*a, **k):
    return {"candles": [], "currency": "BRL"}


def _gate_basico(monkeypatch, *, dia_util: bool = True, kill: bool = False,
                  pregao_aberto: bool = False):
    """Mesmo padrão de `_sem_operador` em test_ordens_pendentes_scheduler.py:
    controla os gates sem depender do relógio real. `pregao_aberto=False` por
    default evita disparar o bloco intraday inteiro (fora do escopo deste
    teste — o que importa aqui é só o bloco `radar_fetch`)."""
    monkeypatch.setattr(agent, "kill_switch_on", lambda: kill)
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **k: pregao_aberto)
    monkeypatch.setattr(agent, "list_server_users", lambda conn: [])
    monkeypatch.setattr("app.pregao.is_trading_day", lambda *a, **k: dia_util)


def _neutraliza_vizinhos(monkeypatch, spy: list | None = None):
    """`radar_daily`/`analysis_outcomes`/`fundamentals` viram no-ops — só o
    hook do ledger (e, quando pedido, um marcador de ordem) importa aqui."""
    async def _radar_daily_noop(*a, **k):
        if spy is not None:
            spy.append("radar_daily")
        return None

    async def _analysis_outcomes_noop(*a, **k):
        return None

    async def _fundamentals_noop(*a, **k):
        return None

    monkeypatch.setattr("app.radar_daily.maybe_run", _radar_daily_noop)
    monkeypatch.setattr("app.analysis_outcomes.maybe_run", _analysis_outcomes_noop)
    monkeypatch.setattr("app.fundamentals.maybe_warm", _fundamentals_noop)


def test_hook_chamado_uma_vez_em_dia_util_com_radar_fetch(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _ledger_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.signal_ledger_job.maybe_run", _ledger_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert len(chamadas) == 1
    assert chamadas[0] is c


def test_excecao_do_hook_nao_derruba_a_passada(monkeypatch):
    c = _conn()
    store.ensure_defaults(c, user_id="u1")
    _gate_basico(monkeypatch, dia_util=True, kill=False, pregao_aberto=True)
    _neutraliza_vizinhos(monkeypatch)

    async def _ledger_explode(conn):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.signal_ledger_job.maybe_run", _ledger_explode)

    pendentes_chamado = []

    def _scopes_spy(conn):
        pendentes_chamado.append(True)
        return []

    monkeypatch.setattr(store, "scopes_com_pendentes", _scopes_spy)

    # Não deve levantar — o try/except próprio do hook absorve a exceção.
    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    # Prova de continuidade: o bloco de ordens pendentes (que vem DEPOIS do
    # bloco radar_fetch na mesma passada) foi alcançado normalmente.
    assert pendentes_chamado == [True]


def test_kill_switch_ligado_hook_nao_e_chamado(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=True)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _ledger_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.signal_ledger_job.maybe_run", _ledger_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert chamadas == []


def test_dia_nao_util_hook_nao_e_chamado(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=False, kill=False)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _ledger_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.signal_ledger_job.maybe_run", _ledger_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert chamadas == []


def test_sem_radar_fetch_hook_nao_e_chamado(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False)
    _neutraliza_vizinhos(monkeypatch)
    chamadas = []

    async def _ledger_spy(conn):
        chamadas.append(conn)
        return None

    monkeypatch.setattr("app.signal_ledger_job.maybe_run", _ledger_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=None, once=True))

    assert chamadas == []


def test_ordem_radar_daily_antes_do_signal_ledger_job(monkeypatch):
    c = _conn()
    _gate_basico(monkeypatch, dia_util=True, kill=False)
    ordem = []
    _neutraliza_vizinhos(monkeypatch, spy=ordem)

    async def _ledger_spy(conn):
        ordem.append("signal_ledger_job")
        return None

    monkeypatch.setattr("app.signal_ledger_job.maybe_run", _ledger_spy)

    asyncio.run(agent.scheduler_loop(c, _fake_quotes, radar_fetch=_fake_radar_fetch, once=True))

    assert ordem == ["radar_daily", "signal_ledger_job"]
    assert ordem.index("radar_daily") < ordem.index("signal_ledger_job")
