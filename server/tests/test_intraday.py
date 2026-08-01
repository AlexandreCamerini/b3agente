"""ADR-001 (item 7) — a passada INTRADAY global do servidor.

O que estes testes protegem, tudo tirado dos ADRs:
  • a passada é GLOBAL (kv sem user_id): custo O(1) no número de usuários;
  • roda no intervalo CANÔNICO 15m, dentro do pregão, e só;
  • NÃO toca o caminho do Radar diário — chave de cache e de armazenamento
    próprias;
  • um ativo ruim não derruba a passada;
  • a lacuna da série (item 1d) e o carimbo da barra fechada (item 1b)
    atravessam até o resultado — é o que a interface precisa mostrar.
Offline: o fetch é injetado.
"""
import asyncio
import os
import tempfile
from datetime import datetime, timedelta, timezone

from app import candle_cache, db, intraday, store, technical_snapshot

BRT = timezone(timedelta(hours=-3))


def _conn():
    d = tempfile.mkdtemp()
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    return c


def _velas(horarios, dia="2026-07-31"):
    out = []
    for i, h in enumerate(horarios):
        base = 40 + i * 0.05
        out.append({"date": f"{dia} {h}", "open": base, "high": base + 0.2,
                    "low": base - 0.2, "close": base + 0.05, "volume": 1000 + i})
    return out


def _grade(n, dia="2026-07-31"):
    """Série de 15m alinhada, começando na abertura (10:00)."""
    return _velas([f"{10 + (i * 15) // 60:02d}:{(i * 15) % 60:02d}" for i in range(n)], dia)


def _fetch(series_por_ticker, falha_em=()):
    chamadas = []

    async def f(ticker, rng, interval):
        chamadas.append((ticker, rng, interval))
        if ticker in falha_em:
            raise RuntimeError("provedor fora do ar")
        return {"t": ticker, "currency": "BRL", "candles": series_por_ticker[ticker]}

    f.chamadas = chamadas
    return f


def _limpa():
    candle_cache.reset()
    technical_snapshot.reset()


# ------------------------------ gating ------------------------------------

def test_so_roda_dentro_do_pregao():
    dentro = datetime(2026, 7, 31, 11, 0, tzinfo=BRT)     # sexta, 11h
    fora = datetime(2026, 7, 31, 19, 0, tzinfo=BRT)       # sexta, 19h
    sabado = datetime(2026, 8, 1, 11, 0, tzinfo=BRT)
    assert intraday.should_run(now=dentro, last_ts=None) is True
    assert intraday.should_run(now=fora, last_ts=None) is False
    assert intraday.should_run(now=sabado, last_ts=None) is False


def test_respeita_o_intervalo_minimo_entre_passadas():
    """O laço acorda a cada 300 s; sem o gap, um deploy que reinicie o laço
    dispararia varredura em sequência."""
    agora = datetime(2026, 7, 31, 11, 0, tzinfo=BRT)
    assert intraday.should_run(now=agora, last_ts=1000.0, agora_mono=1000.0 + 10) is False
    assert intraday.should_run(now=agora, last_ts=1000.0,
                               agora_mono=1000.0 + intraday.GAP_MIN_S) is True


def test_kill_switch_proprio(monkeypatch):
    """Desligar o intraday não pode desligar o Operador."""
    monkeypatch.setenv("B3_INTRADAY_OFF", "1")
    assert intraday.enabled() is False
    c = _conn()
    assert asyncio.run(intraday.maybe_run(c, _fetch({}))) is None
    monkeypatch.delenv("B3_INTRADAY_OFF")
    assert intraday.enabled() is True


# ------------------------------ a passada ----------------------------------

def test_passada_grava_global_e_usa_o_intervalo_canonico():
    _limpa()
    c = _conn()
    uni = ["AAAA3", "BBBB4"]
    f = _fetch({t: _grade(220) for t in uni})
    payload = asyncio.run(intraday.run_pass(c, f, universo=uni))

    assert payload["interval"] == "15m"
    assert payload["ativos"] == 2 and payload["erros"] == []
    # GLOBAL: sem user_id. É isto que mantém o custo O(1) em usuários.
    assert db.kv_get(c, intraday.CHAVE, user_id=None) is not None
    assert db.kv_get(c, intraday.CHAVE, user_id="u1") in (None, {}, [])
    # todo fetch pediu 15m
    assert {iv for _, _, iv in f.chamadas} == {"15m"}


def test_um_ativo_ruim_nao_derruba_a_passada():
    _limpa()
    c = _conn()
    uni = ["AAAA3", "RUIM3", "BBBB4"]
    f = _fetch({t: _grade(220) for t in uni}, falha_em={"RUIM3"})
    payload = asyncio.run(intraday.run_pass(c, f, universo=uni))
    assert payload["ativos"] == 2
    assert [e["ticker"] for e in payload["erros"]] == ["RUIM3"]


def test_resultado_carrega_o_carimbo_da_barra_fechada():
    """ADR-001 Decisão 2: sem `asOf` a interface não tem como dizer QUAL barra —
    e a frase vira insinuação de tempo real."""
    _limpa()
    c = _conn()
    velas = _grade(220)
    payload = asyncio.run(intraday.run_pass(c, _fetch({"AAAA3": velas}), universo=["AAAA3"]))
    r = payload["resultados"][0]
    assert r["asOf"] == velas[-2]["date"]            # última FECHADA (item 1b)
    assert r["barraEmFormacao"] == velas[-1]["date"]  # a descartada
    assert r["snapshotId"] and r["veredito"]


def test_lacuna_da_serie_chega_ao_resultado():
    """ADR-001 item 1d: série furada mente com cara de certa — o Radar intraday
    precisa poder marcar o ativo."""
    _limpa()
    c = _conn()
    # começa às 13:00 em vez de 10:00: a manhã sumiu, como em 31/07
    tarde = _velas([f"{13 + (i * 15) // 60:02d}:{(i * 15) % 60:02d}" for i in range(12)])
    payload = asyncio.run(intraday.run_pass(c, _fetch({"AAAA3": tarde}), universo=["AAAA3"]))
    r = payload["resultados"][0]
    assert r["lacuna"] is True
    assert r["cobertura"] < 1.0
    assert payload["comLacuna"] == 1


def test_nao_toca_o_cache_do_radar_diario():
    """O custo do Radar diário tem que ficar EXATAMENTE como está."""
    _limpa()
    c = _conn()
    asyncio.run(intraday.run_pass(c, _fetch({"AAAA3": _grade(220)}), universo=["AAAA3"]))
    chaves = list(candle_cache.stats().keys())
    assert chaves == ["AAAA3@15m"], "a passada não pode criar/alterar a entrada diária"
    assert db.kv_get(c, "radarDaily:1y", user_id=None) is None


def test_resultados_vem_ordenados_por_confluencia():
    _limpa()
    c = _conn()
    uni = ["AAAA3", "BBBB4", "CCCC3"]
    payload = asyncio.run(intraday.run_pass(c, _fetch({t: _grade(220) for t in uni}), universo=uni))
    confs = [r["confluencia"] or 0 for r in payload["resultados"]]
    assert confs == sorted(confs, reverse=True)


def test_get_stored_devolve_a_ultima_passada():
    _limpa()
    c = _conn()
    assert intraday.get_stored(c) is None
    asyncio.run(intraday.run_pass(c, _fetch({"AAAA3": _grade(220)}), universo=["AAAA3"]))
    guardado = intraday.get_stored(c)
    assert guardado["interval"] == "15m" and guardado["ativos"] == 1


def test_maybe_run_nunca_levanta(monkeypatch):
    """O laço do agente NÃO pode cair por causa da passada intraday.

    Força o gate aberto (o teste não pode depender da hora em que roda) e faz o
    provedor explodir de um jeito que `run_pass` não trata — o `gather` captura
    falha por ativo, então aqui o erro tem que vir de fora dele.
    """
    _limpa()
    c = _conn()
    monkeypatch.setattr(intraday, "should_run", lambda **kw: True)
    monkeypatch.setattr(intraday, "get_universe", lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    async def qualquer(ticker, rng, interval):
        return {"candles": []}

    assert asyncio.run(intraday.maybe_run(c, qualquer)) is None   # engoliu
    assert "boom" in (intraday.LAST_PASS["erro"] or ""), "a falha tem que ficar na telemetria"


def test_laco_do_agente_dispara_a_passada_e_respeita_o_gate(monkeypatch):
    """Integração com o `scheduler_loop`: é o elo que faz toda a infraestrutura
    intraday sair do papel. Sem ele, tudo o que foi construído fica dormente."""
    from app import agent as agent_mod
    _limpa()
    c = _conn()
    agent_mod._LAST_INTRADAY["ts"] = None
    monkeypatch.setattr(agent_mod, "in_market_hours", lambda *a, **k: True)
    # `intraday` importa in_market_hours para o PRÓPRIO namespace: sem este
    # segundo patch o teste só passava com o pregão aberto de verdade.
    monkeypatch.setattr(intraday, "in_market_hours", lambda *a, **k: True)
    monkeypatch.setattr(agent_mod, "list_server_users", lambda conn: [])
    monkeypatch.setattr(intraday, "get_universe", lambda: ["AAAA3"])

    f = _fetch({"AAAA3": _grade(220)})

    async def quotes(_tickers):
        return {}

    asyncio.run(agent_mod.scheduler_loop(c, quotes, once=True, intraday_fetch=f))
    guardado = intraday.get_stored(c)
    assert guardado and guardado["ativos"] == 1, "o laço tem que ter rodado a passada"
    assert agent_mod._LAST_INTRADAY["ts"] is not None, "o carimbo do gap tem que ser gravado"

    # segunda passada IMEDIATA é barrada pelo gap mínimo (não queima requisição)
    antes = len(f.chamadas)
    asyncio.run(agent_mod.scheduler_loop(c, quotes, once=True, intraday_fetch=f))
    assert len(f.chamadas) == antes, "o gap mínimo tem que impedir a repetição"


def test_laco_sem_intraday_fetch_nao_muda_nada(monkeypatch):
    """Compatibilidade: quem não injeta o fetch (testes antigos, chamadas
    diretas) continua com o laço exatamente como era."""
    from app import agent as agent_mod
    _limpa()
    c = _conn()
    agent_mod._LAST_INTRADAY["ts"] = None
    monkeypatch.setattr(agent_mod, "in_market_hours", lambda *a, **k: True)
    monkeypatch.setattr(agent_mod, "list_server_users", lambda conn: [])

    async def quotes(_tickers):
        return {}

    asyncio.run(agent_mod.scheduler_loop(c, quotes, once=True))
    assert intraday.get_stored(c) is None
    assert agent_mod._LAST_INTRADAY["ts"] is None
