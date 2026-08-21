"""ADR-017 — histórico do guardião de entrada automática do Modo Operador.

Até 2026-08-21 este arquivo guardava a suspensão CEGA (`ENTRADA_AUTO_SUSPENSA_ADR017
= True`, agora removida): nenhum setup executava, incondicionalmente, porque a
seleção dinâmica (Bloco 1) ainda não existia (ADR-016: motor perde para o
acaso; IFR2, o único positivo, era modesto demais sozinho).

Em 2026-08-21 (Fase 08, Bloco 4 do ADR-017, Adendo 2), com o Bloco 1 em
produção, a suspensão cega foi substituída por um GATE DE ELEGIBILIDADE: só o
setup do gatilho que a seleção dinâmica mediu como `elegivel is True` na
janela anterior fechada executa. O que este arquivo guarda agora é que o gate
BLOQUEIA nos três casos negativos (`elegivel is False`, `elegivel is None` —
amostra insuficiente/nunca medido —, e setup ausente do snapshot) e no caso de
falha de leitura do ledger (snapshot vazio `{}` falha FECHADO), e LIBERA só em
`elegivel is True`. `test_entrada_automatica.py` cobre a MECÂNICA em si (lote,
orçamento, maxOpsDia, maxValorOp, dedupe com o vigia), com o gate neutralizado
por um snapshot stub elegível.
"""
import asyncio
import os
import tempfile
from datetime import datetime

from app import agent, candles, db, intraday, radar_daily, signal_ledger, store

HOJE = "2026-08-07"
AGORA = datetime(2026, 8, 7, 14, 30, tzinfo=intraday.BRT)
SETUP = "IFR2 (alta)"  # nome real do catálogo (server/app/setups.py:303) —
                        # o lookup do gate é por nome exato, então o guardião
                        # só prova o acoplamento de chave (T-08-08) com um
                        # nome que o catálogo realmente produz.


def _conn(tickers=("PETR4",)):
    d = tempfile.mkdtemp(prefix="b3_entrada_auto_suspensa_")
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    db.kv_set(c, "positions", [], user_id="u1")
    store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                          "appMode": "operador"}, user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    db.kv_set(c, "watchlist", list(tickers), user_id="u1")

    period = candles.normalize_period(None)
    radar_daily.store_result(c, period, {"results": [{
        "ticker": t, "veredito": "Estudar",
        "plano": {"decisao": "COMPRAR", "lado": "alta", "entrada": 38.5,
                  "stop": 36.2, "riscoPorAcao": 2.3, "setup": SETUP},
    } for t in tickers]}, "manual")
    db.kv_set(c, intraday.CHAVE, {
        "at": AGORA.isoformat(), "asOf": f"{HOJE} 14:15", "atLabel": "14:15",
        "universo": len(tickers), "ativos": len(tickers), "comLacuna": 0,
        "resultados": [{"ticker": t, "close": 39.0, "asOf": f"{HOJE} 14:15",
                         "cobertura": 1.0, "lacuna": False, "barraEmFormacao": False}
                       for t in tickers],
        "erros": [],
    }, user_id=None)
    return c


def _run(c):
    ag = {"entradaAuto": True, "allocPct": 5, "maxOpsDia": 3, "maxValorOp": 0}
    par = agent.agent_params(ag, app_mode="operador")
    events = []
    ex = asyncio.run(agent._avaliar_entradas(c, "u1", ag, par, "operador", [],
                                              0, events, agora=AGORA))
    return ex, events


def _hist(**overrides):
    """Shape exato de `signal_ledger._fundir` (server/app/signal_ledger.py:222-246)
    — o stub não pode ser um contrato mais frouxo que o real."""
    base = {"expR": None, "n": 0, "medidoAte": None, "elegivel": None,
            "insuficiente": True, "expRJanela": None, "nJanela": 0,
            "janelaRef": None, "calculadoEm": None}
    base.update(overrides)
    return base


def test_flag_antiga_nao_existe_mais():
    """A suspensão cega foi removida — `agent` não expõe mais o atributo."""
    assert not hasattr(agent, "ENTRADA_AUTO_SUSPENSA_ADR017")


def test_elegivel_true_libera_a_entrada(monkeypatch):
    c = _conn()
    signal_ledger.reset_cache()
    monkeypatch.setattr(signal_ledger, "historico_snapshot",
                         lambda conn, **kw: {SETUP: _hist(elegivel=True, n=2934, expR=0.072)})
    ex, events = _run(c)
    assert ex == 1
    positions = store.get(c, "positions", user_id="u1")
    assert len(positions) == 1 and positions[0]["t"] == "PETR4"
    assert any(e["kind"] == "buy" for e in events)


def test_elegivel_false_bloqueia_em_silencio(monkeypatch):
    c = _conn()
    signal_ledger.reset_cache()
    monkeypatch.setattr(signal_ledger, "historico_snapshot",
                         lambda conn, **kw: {SETUP: _hist(elegivel=False, n=5134, expR=-0.036)})
    ex, events = _run(c)
    assert ex == 0
    assert events == []
    assert store.get(c, "positions", user_id="u1") == []


def test_elegivel_none_amostra_insuficiente_bloqueia_em_silencio(monkeypatch):
    c = _conn()
    signal_ledger.reset_cache()
    monkeypatch.setattr(signal_ledger, "historico_snapshot",
                         lambda conn, **kw: {SETUP: _hist(elegivel=None, insuficiente=True, n=12)})
    ex, events = _run(c)
    assert ex == 0
    assert events == []
    assert store.get(c, "positions", user_id="u1") == []


def test_setup_ausente_do_snapshot_bloqueia_em_silencio(monkeypatch):
    """Setup nunca medido: nem chave no dict — ausência de evidência bloqueia,
    igual a evidência negativa."""
    c = _conn()
    signal_ledger.reset_cache()
    monkeypatch.setattr(signal_ledger, "historico_snapshot", lambda conn, **kw: {})
    ex, events = _run(c)
    assert ex == 0
    assert events == []
    assert store.get(c, "positions", user_id="u1") == []


def test_snapshot_vazio_por_falha_de_ledger_falha_fechado(monkeypatch):
    """`historico_snapshot` real nunca levanta (try/except interno) — uma
    falha de banco vira `{}`, que este teste simula direto: nenhuma entrada
    executa, o gate falha FECHADO, nunca aberto."""
    c = _conn()
    signal_ledger.reset_cache()
    monkeypatch.setattr(signal_ledger, "historico_snapshot", lambda conn, **kw: {})
    ex, events = _run(c)
    assert ex == 0
    assert events == []
    assert store.get(c, "positions", user_id="u1") == []


def test_historico_snapshot_consultado_uma_unica_vez_por_chamada(monkeypatch):
    """Mesmo com vários candidatos na watchlist, `historico_snapshot` só roda
    UMA vez por chamada de `_avaliar_entradas` (leitura fora do laço)."""
    c = _conn(("PETR4", "VALE3"))
    signal_ledger.reset_cache()
    chamadas = {"n": 0}
    def _spy(conn, **kw):
        chamadas["n"] += 1
        return {SETUP: _hist(elegivel=True, n=2934, expR=0.072)}
    monkeypatch.setattr(signal_ledger, "historico_snapshot", _spy)
    ex, events = _run(c)
    assert ex == 2
    assert chamadas["n"] == 1
