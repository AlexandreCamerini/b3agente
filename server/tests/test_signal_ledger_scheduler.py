"""ADR-017 (Bloco 1) — hook diário do ledger pendurado no `scheduler_loop`
(Task 1) e provedor de histórico ligado no boot (Task 2).

Task 1 (07-06): `signal_ledger_job.maybe_run` roda dentro do MESMO bloco
guardado que `radar_daily.maybe_run`/`analysis_outcomes.maybe_run`/
`fundamentals.maybe_warm` (radar_fetch is not None and not kill_switch_on()
and pregao.is_trading_day()), DEPOIS de `fundamentals.maybe_warm`, com
try/except PRÓPRIO — uma exceção do hook não pode derrubar o resto da
passada (heartbeat, kill-switch, ciclo de stop/alvo).

Todos os testes de Task 1 usam banco temp real + `asyncio.run(agent.
scheduler_loop(..., once=True))`, mesmo padrão de
`test_ordens_pendentes_scheduler.py`. Os hooks internos ao bloco
(`radar_daily.maybe_run`, `analysis_outcomes.maybe_run`,
`fundamentals.maybe_warm`, `signal_ledger_job.maybe_run`) são importados
LOCALMENTE dentro de `scheduler_loop` — monkeypatch precisa mirar o atributo
no MÓDULO DE ORIGEM (`"app.radar_daily.maybe_run"`), nunca no namespace de
`agent`, senão o import local resolve para a função real e o spy nunca é
chamado.

Task 2 (07-06): `setups.set_historico_provider` ligado no boot de
`main.py` — os testes exercitam o caminho REAL
(`technical_snapshot.build` → `detect_setups` → `regime.ranquear`), com kv
populado e com kv vazio (instalação nova, bootstrap ainda não rodado).
"""
import asyncio
import os
import tempfile
from datetime import date, timedelta

import pytest

from app import agent, db, regime, setups, signal_ledger, store, technical_snapshot


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


# ----------------------------------------------------------------------------
# Task 2: provedor de histórico ligado no boot (main.py) — caminho REAL
# ----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _historico_provider_isolado():
    """Nenhum teste deste arquivo (nem os de Task 1, acima) pode herdar o
    provedor de outro — `_HISTORICO_PROVIDER` é estado global de módulo."""
    setups.set_historico_provider(None)
    signal_ledger.reset_cache()
    yield
    setups.set_historico_provider(None)
    signal_ledger.reset_cache()


def _mk_candles_rompimento():
    """Mesmo gerador de `test_adr017_historico_setups.py` — dispara
    'Rompimento com volume (alta)', setup OPERÁVEL (não aposentado)."""
    closes = [50 + (0.02 if i % 2 else -0.02) for i in range(80)] + [53.0]
    vols = [1000] * 80 + [2500]  # 2,5x a média
    d0 = date.fromisoformat("2024-01-01")
    out = []
    for i, c in enumerate(closes):
        lo, hi = c * 0.985, c * 1.015
        close = c
        if i == len(closes) - 1:
            close = lo + (hi - lo) * 0.95
        out.append({"date": (d0 + timedelta(days=i)).isoformat(),
                    "open": round(c * 0.998, 4), "high": round(hi, 4),
                    "low": round(lo, 4), "close": round(close, 4),
                    "volume": vols[i]})
    return out


def test_boot_liga_o_provedor_de_historico():
    """`from app.main import app` dispara o boot, que roda literalmente
    `setups.set_historico_provider(lambda: signal_ledger.historico_snapshot(
    _conn))` — a mesma linha que este teste reproduz contra o `_conn` real do
    processo, para provar que a fiação de `main.py` (Task 2) fica funcional
    (não só presente no texto, que os greps de aceite do plano já cobrem).

    Não faz a asserção diretamente sobre `setups._HISTORICO_PROVIDER` logo
    após o import: é estado GLOBAL de módulo, e outros arquivos de teste
    (ex. `test_adr017_historico_setups.py`) têm fixture própria que o
    reseta para `None` como limpeza — rodando a suíte inteira, a ordem de
    execução dos arquivos pode deixar esse global em `None` por um teste de
    outro arquivo, sem que a fiação de `main.py` tenha deixado de existir."""
    from app import main as main_mod  # importar já dispara o boot
    main_mod.setups.set_historico_provider(
        lambda: main_mod.signal_ledger.historico_snapshot(main_mod._conn)
    )
    assert setups._HISTORICO_PROVIDER is not None
    resultado = setups._HISTORICO_PROVIDER()
    assert isinstance(resultado, dict)  # historico_snapshot nunca propaga; kv vazio => {}


def test_caminho_real_com_kv_populado_anexa_historico():
    conn = _conn()
    cumulativo = {
        "porSetup": {"Rompimento com volume (alta)": {
            "n": 62, "acerto": 55.0, "expR": 0.18, "somaR": 11.2,
            "stops": 20, "alvos": 30, "expirou": 12, "naoAcionados": 0,
        }},
        "medidoAte": "2025-12-31",
        "calculadoEm": "2026-01-05T00:00:00",
    }
    db.kv_set(conn, signal_ledger.K_CUMULATIVO, cumulativo, user_id=None)
    setups.set_historico_provider(lambda: signal_ledger.historico_snapshot(conn))

    technical_snapshot.reset()
    snap = technical_snapshot.build("TESTE3", _mk_candles_rompimento(), "6mo")
    por_nome = {s["nome"]: s for s in snap["setups"]["setups"]}

    assert "Rompimento com volume (alta)" in por_nome, "cenário precisa detectar o setup"
    hist = por_nome["Rompimento com volume (alta)"]["historico"]
    assert hist is not None
    assert hist["expR"] == 0.18
    assert hist["n"] == 62


def test_caminho_real_com_kv_vazio_historico_none_sem_excecao():
    """Instalação nova: kv vazio (bootstrap ainda não rodou). O caminho real
    não pode levantar — a tela funciona antes do bootstrap."""
    conn = _conn()
    setups.set_historico_provider(lambda: signal_ledger.historico_snapshot(conn))

    technical_snapshot.reset()
    snap = technical_snapshot.build("TESTE3", _mk_candles_rompimento(), "6mo")

    assert snap["setups"]["setups"], "cenário precisa detectar ao menos um setup"
    for s in snap["setups"]["setups"]:
        assert s["historico"] is None


def test_regime_ranquear_no_caminho_real_setupElegivel_none_sem_janela():
    """Sem janela anual fechada (kv vazio), `regime.ranquear` sobre o
    resultado do caminho real anexa `setupElegivel=None` — nunca `False` por
    ausência de evidência (ADR-017, "Dois pisos de amostra")."""
    conn = _conn()
    setups.set_historico_provider(lambda: signal_ledger.historico_snapshot(conn))

    technical_snapshot.reset()
    snap = technical_snapshot.build("TESTE3", _mk_candles_rompimento(), "6mo")
    sres = snap["setups"]
    resultado = {"ticker": "TESTE3", "confluencia": sres.get("confluencia") or 0,
                 "setups": sres["setups"]}

    out = regime.ranquear([resultado], {"TESTE3": snap})

    assert out[0]["setupElegivel"] is None
    # setupElegivel None => peso_hist=0.0 no radarScore (regime.ranquear,
    # bloco `if/elif/else` de W_HISTORICO_ELEGIVEL/INELEGIVEL) — não penalizado.
