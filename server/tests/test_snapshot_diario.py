"""server/tests/test_snapshot_diario.py — job de snapshot de fechamento (quick 261013-u7w).

Casos J1-J25 do PLAN (+ o caso do `erro` zerado por tick posterior bem-sucedido).
Sem rede: o getter de cotacoes e async, mocado e registra os tickers de cada
chamada; o relogio entra por `now` (ou por `snapshot_diario._agora`)."""
import asyncio
import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from app import agent, db, snapshot_diario as sd, store

BRT = timezone(timedelta(hours=-3))
HOJE = "2026-10-13"   # terca-feira, dia de pregao


def dt(h, m, dia=HOJE):
    y, mo, d = (int(x) for x in dia.split("-"))
    return datetime(y, mo, d, h, m, 0, tzinfo=BRT)


def _conn():
    return db.connect(os.path.join(tempfile.mkdtemp(), "b3.db"))


@pytest.fixture(autouse=True)
def _isola(monkeypatch):
    antes = dict(sd.LAST_RUN)
    for k in ("B3_SNAPSHOT_DIARIO_HHMM", "B3_SNAPSHOT_DIARIO_OFF", "B3_AGENT_INTERVAL_S"):
        monkeypatch.delenv(k, raising=False)
    yield
    sd.LAST_RUN.clear()
    sd.LAST_RUN.update(antes)


def _seed(c, uid, cash=0, positions=(), options=(), reservado=0):
    db.kv_set(c, "cash", cash, user_id=uid)
    db.kv_set(c, "positions", list(positions), user_id=uid)
    if options:
        db.kv_set(c, "optionPositions", list(options), user_id=uid)
    if reservado:
        db.kv_set(c, "pendingOrders", [{"tipo": "COMPRA", "caixaReservado": reservado}], user_id=uid)


def _pos(t, qty=100, avg=30):
    return {"t": t, "qty": qty, "avg": avg}


def _getter(precos, source="brapi"):
    calls = []

    async def g(tickers):
        calls.append(list(tickers))
        return {t: {"price": precos.get(t), "source": source} for t in tickers}
    g.calls = calls
    return g


def _run(c, g, now):
    return asyncio.run(sd.maybe_run(c, g, now))


def _snaps(c, uid):
    return db.kv_get(c, "equitySnapshots", [], user_id=uid)


def _feitas(c):
    return sd._ler_feitas(c, HOJE)


def test_j1_sabado_nao_roda():
    c = _conn(); _seed(c, "u1", 100, [_pos("PETR4")]); g = _getter({"PETR4": 35})
    assert _run(c, g, dt(17, 6, "2026-10-17")) is None and g.calls == []


def test_j2_feriado_em_dia_util_nao_roda():
    c = _conn(); _seed(c, "u1", 100, [_pos("PETR4")]); g = _getter({"PETR4": 35})
    assert _run(c, g, dt(17, 6, "2026-12-25")) is None and g.calls == []


def test_j3_antes_do_horario_nao_roda():
    c = _conn(); _seed(c, "u1", 100, [_pos("PETR4")]); g = _getter({"PETR4": 35})
    assert _run(c, g, dt(17, 4)) is None and g.calls == []


def test_j4_lastrun_de_hoje_no_kv_nao_roda():
    c = _conn(); _seed(c, "u1", 100, [_pos("PETR4")]); g = _getter({"PETR4": 35})
    db.kv_set(c, sd.K_LAST_RUN, HOJE, user_id=None)
    assert _run(c, g, dt(17, 6)) is None and g.calls == []


def test_j5_apos_17_15_fecha_o_dia_sem_chamar_o_getter():
    c = _conn(); _seed(c, "u1", 100); _seed(c, "u2", 100, [_pos("PETR4")]); g = _getter({"PETR4": 35})
    sd._gravar_feitas(c, HOJE, {"u1"})  # 2026-10-13 (quick 261013-u7w): helper em lote
    r = _run(c, g, dt(17, 16))
    assert g.calls == [] and r["perdidasNaJanela"] == 1
    assert sd.LAST_RUN["perdidasNaJanela"] == 1 and sd.last_run_date(c) == HOJE
    assert _snaps(c, "u2") == []


def test_j6_um_getter_por_tick_com_tickers_distintos_ordenados():
    c = _conn()
    _seed(c, "u1", 0, [_pos("PETR4")]); _seed(c, "u2", 0, [_pos("PETR4")])
    _seed(c, "u3", 0, [_pos("VALE3"), _pos("PETR4")])
    g = _getter({"PETR4": 35, "VALE3": 70})
    _run(c, g, dt(17, 6))
    assert g.calls == [["PETR4", "VALE3"]]


def test_j7_ponto_de_fechamento_com_origem_fonte_hora():
    c = _conn()
    _seed(c, "u1", 1000, [_pos("PETR4", 100, 30), _pos("VALE3", 50, 60)], reservado=500)
    r = _run(c, _getter({"PETR4": 35, "VALE3": 70}), dt(17, 6))
    s = _snaps(c, "u1")
    assert len(s) == 1
    assert s[0]["data"] == HOJE and s[0]["origem"] == "fechamento"
    assert s[0]["fonte"] == "brapi" and s[0]["hora"] == "17:06"
    assert s[0]["patrimonio"] == 8500.0           # 1000 + 500 + 3500 + 3500
    assert s[0]["caixa"] == 1000.0 and s[0]["posicoesValor"] == 7000.0
    assert _feitas(c) == {"u1"} and r["pendentesRestantes"] == 0
    assert sd.last_run_date(c) == HOJE


@pytest.mark.parametrize("ruim", [None, 0, "x", True])
def test_j8_ativo_sem_cotacao_valida_nao_grava(ruim):
    c = _conn()
    _seed(c, "u1", 1000, [_pos("PETR4")]); _seed(c, "u2", 1000, [_pos("VALE3")])
    r = _run(c, _getter({"PETR4": ruim, "VALE3": 70}), dt(17, 6))
    assert _snaps(c, "u1") == [] and len(_snaps(c, "u2")) == 1
    assert r["puladasSemCotacao"] == 1 and r["tickersSemCotacao"] == ["PETR4"]
    assert _feitas(c) == {"u2"} and sd.last_run_date(c) is None
    assert sd.LAST_RUN["tickersSemCotacao"] == ["PETR4"]


def test_j9_conta_sem_posicao_grava_curva_plana():
    c = _conn(); _seed(c, "u1", 5000, [], reservado=0); g = _getter({})
    _run(c, g, dt(17, 6))
    s = _snaps(c, "u1")
    assert s[0]["patrimonio"] == 5000.0 and s[0]["fonte"] is None and g.calls == []


def test_j10_so_opcao_avulsa_sem_cotacao_de_contrato_grava():
    c = _conn()
    _seed(c, "u1", 908, [], options=[{"id": "VALEV731W2", "qty": 100, "avg": 0.92}])
    r = _run(c, _getter({}), dt(17, 6))
    assert _snaps(c, "u1")[0]["patrimonio"] == 1000.0 and r["puladasSemCotacao"] == 0


def test_j11_roda_pelo_scheduler_com_kill_switch_ligado(monkeypatch):
    c = _conn(); _seed(c, "u1", 100, [_pos("PETR4", 10, 30)])
    monkeypatch.setattr(agent, "kill_switch_on", lambda: True)
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **k: False)
    monkeypatch.setattr(agent, "list_server_users", lambda conn: [])
    monkeypatch.setattr("app.pregao.is_trading_day", lambda *a, **k: True)
    monkeypatch.setattr(sd, "_agora", lambda: dt(17, 6))

    async def noop(*a, **k):
        return None
    for alvo in ("app.put_lifecycle.maybe_run", "app.put_bridge.maybe_run", "app.signal_ledger_job.maybe_run",
                 "app.radar_daily.maybe_run", "app.analysis_outcomes.maybe_run"):
        monkeypatch.setattr(alvo, noop)
    monkeypatch.setattr("app.fundamentals.maybe_warm", noop)
    g = _getter({"PETR4": 35})
    asyncio.run(agent.scheduler_loop(c, g, interval_s=1, once=True))
    assert g.calls == [["PETR4"]]
    assert _snaps(c, "u1")[0]["origem"] == "fechamento" and _snaps(c, "u1")[0]["hora"] == "17:06"


def test_j12_lote_sem_nenhuma_cotacao_valida():
    c = _conn(); _seed(c, "u1", 1, [_pos("PETR4")]); _seed(c, "u2", 1, [_pos("VALE3")])
    r = _run(c, _getter({}), dt(17, 6))
    assert r["erro"] == "nenhuma cotação válida no lote"
    assert sd.LAST_RUN["erro"] == "nenhuma cotação válida no lote"
    assert _snaps(c, "u1") == [] and _snaps(c, "u2") == []
    assert sd.last_run_date(c) is None and _feitas(c) == set()


def test_j13_getter_que_levanta_nao_propaga():
    c = _conn(); _seed(c, "u1", 1, [_pos("PETR4")])
    sd._gravar_feitas(c, HOJE, {"uX"})  # 2026-10-13 (quick 261013-u7w): helper em lote

    async def quebra(tickers):
        raise RuntimeError("rede fora")
    assert asyncio.run(sd.maybe_run(c, quebra, dt(17, 6))) is None
    assert "rede fora" in sd.LAST_RUN["erro"]
    assert sd.last_run_date(c) is None and _feitas(c) == {"uX"}


def test_erro_e_zerado_por_tick_posterior_com_sucesso():
    c = _conn(); _seed(c, "u1", 1, [_pos("PETR4")])

    async def quebra(tickers):
        raise RuntimeError("rede fora")
    asyncio.run(sd.maybe_run(c, quebra, dt(17, 6)))
    assert sd.LAST_RUN["erro"]
    _run(c, _getter({"PETR4": 35}), dt(17, 10))
    assert sd.LAST_RUN["erro"] is None and len(_snaps(c, "u1")) == 1
    # idem para o erro de lote vazio
    c2 = _conn(); _seed(c2, "u1", 1, [_pos("PETR4")])
    _run(c2, _getter({}), dt(17, 6))
    assert sd.LAST_RUN["erro"] == "nenhuma cotação válida no lote"
    _run(c2, _getter({"PETR4": 35}), dt(17, 10))
    assert sd.LAST_RUN["erro"] is None


def test_j14_escopo_anonimo_legado_e_ignorado():
    c = _conn()
    db.kv_set(c, "cash", 100, user_id=None); db.kv_set(c, "positions", [_pos("PETR4")], user_id=None)
    g = _getter({"PETR4": 35})
    r = _run(c, g, dt(17, 6))
    assert r["contas"] == 0 and g.calls == [] and db.kv_get(c, "equitySnapshots", None, user_id=None) is None


def test_j15_fechamento_substitui_ponto_app_de_hoje():
    c = _conn(); _seed(c, "u1", 1000)
    store.upsert_snapshot(c, {"data": HOJE, "patrimonio": 1}, user_id="u1")
    assert _snaps(c, "u1")[0]["origem"] == "app"
    _run(c, _getter({}), dt(17, 6))
    s = _snaps(c, "u1")
    assert len(s) == 1 and s[0]["origem"] == "fechamento" and s[0]["patrimonio"] == 1000.0


@pytest.mark.parametrize("valor", ["abc", "16:00", "17:15", "17:20", "25:99", ""])
def test_j16_hhmm_invalido_ou_fora_da_janela_cai_no_default(monkeypatch, valor):
    monkeypatch.setenv("B3_SNAPSHOT_DIARIO_HHMM", valor)
    assert sd.janela_hhmm() == "17:05"


def test_j16_hhmm_valido_vale(monkeypatch):
    monkeypatch.setenv("B3_SNAPSHOT_DIARIO_HHMM", "17:10")
    assert sd.janela_hhmm() == "17:10"
    assert sd.should_run(dt(17, 6), None) is False and sd.should_run(dt(17, 10), None) is True


def test_janela_pura_17_14_roda_17_15_fecha():
    assert sd.should_run(dt(17, 14), None) and not sd.should_run(dt(17, 15), None)
    assert sd.deve_fechar(dt(17, 15), None) and not sd.deve_fechar(dt(17, 14), None)
    assert not sd.deve_fechar(dt(17, 16), HOJE) and not sd.should_run(dt(17, 6), HOJE)


def test_j17_desligado_por_env(monkeypatch):
    monkeypatch.setenv("B3_SNAPSHOT_DIARIO_OFF", "1")
    c = _conn(); _seed(c, "u1", 1, [_pos("PETR4")]); g = _getter({"PETR4": 35})
    assert _run(c, g, dt(17, 6)) is None and g.calls == []


def test_j18_status_vem_do_kv_apos_reinicio():
    c = _conn(); _seed(c, "u1", 1000, [_pos("PETR4")])
    _run(c, _getter({"PETR4": 35}), dt(17, 6))
    esperado = dict(sd.LAST_RUN)
    for k, v in list(sd.LAST_RUN.items()):
        sd.LAST_RUN[k] = 0 if isinstance(v, int) and not isinstance(v, bool) else None
    st = agent.status_snapshot(c, interval_s=60)
    assert st["jobs"]["origem"]["snapshotDiario"] == "kv"
    assert set(st["snapshotDiario"]) == set(sd.LAST_RUN)
    for k, v in esperado.items():
        assert st["snapshotDiario"][k] == v, k
    assert st["snapshotDiario"]["gravadas"] == 1 and st["snapshotDiario"]["date"] == HOJE


def test_j19_orcamento_esgotado_no_meio_do_lote():
    c = _conn(); _seed(c, "u1", 1, [_pos("PETR4")]); _seed(c, "u2", 1, [_pos("VALE3")])
    r = _run(c, _getter({"PETR4": 35, "VALE3": None}), dt(17, 6))
    assert len(_snaps(c, "u1")) == 1 and _snaps(c, "u2") == []
    assert r["puladasSemCotacao"] == 1 and r["tickersSemCotacao"] == ["VALE3"]
    assert sd.last_run_date(c) is None


def test_j20_tick_seguinte_so_pega_as_pendentes():
    c = _conn(); _seed(c, "u1", 1, [_pos("PETR4")]); _seed(c, "u2", 1, [_pos("VALE3")])
    _run(c, _getter({"PETR4": 35, "VALE3": None}), dt(17, 6))
    antes = _snaps(c, "u1")
    g2 = _getter({"PETR4": 99, "VALE3": 70})
    r = _run(c, g2, dt(17, 10))
    assert g2.calls == [["VALE3"]]
    assert _snaps(c, "u1") == antes and _snaps(c, "u1")[0]["hora"] == "17:06"
    assert len(_snaps(c, "u2")) == 1 and _snaps(c, "u2")[0]["hora"] == "17:10"
    assert r["pendentesRestantes"] == 0 and sd.last_run_date(c) == HOJE
    assert sd.LAST_RUN["gravadas"] == 2


def test_j21_excecao_numa_conta_nao_derruba_as_outras(monkeypatch):
    c = _conn(); _seed(c, "u1", 1, [_pos("PETR4")]); _seed(c, "u2", 1, [_pos("VALE3")])
    original = store.patrimonio_conta

    def falha_u2(positions, *a, **k):
        if any(p.get("t") == "VALE3" for p in positions):
            raise RuntimeError("conta corrompida")
        return original(positions, *a, **k)
    monkeypatch.setattr(store, "patrimonio_conta", falha_u2)
    r = _run(c, _getter({"PETR4": 35, "VALE3": 70}), dt(17, 6))
    assert len(_snaps(c, "u1")) == 1 and _snaps(c, "u2") == []
    assert r["erros"] == 1 and _feitas(c) == {"u1"} and sd.last_run_date(c) is None
    monkeypatch.setattr(store, "patrimonio_conta", original)
    _run(c, _getter({"PETR4": 35, "VALE3": 70}), dt(17, 10))
    assert len(_snaps(c, "u2")) == 1 and sd.last_run_date(c) == HOJE


def test_j22_janela_encerrada_com_pendentes_fecha_sem_getter():
    c = _conn(); _seed(c, "u1", 1, [_pos("PETR4")])
    _run(c, _getter({}), dt(17, 6))          # falha: nada cotado
    g = _getter({"PETR4": 35})
    r = _run(c, g, dt(17, 16))
    assert g.calls == [] and r["perdidasNaJanela"] == 1
    assert sd.LAST_RUN["perdido"] is False and sd.last_run_date(c) == HOJE
    assert _snaps(c, "u1") == []


def test_j23_nenhum_tick_na_janela_marca_perdido():
    c = _conn(); _seed(c, "u1", 1, [_pos("PETR4")]); _seed(c, "u2", 1)
    g = _getter({"PETR4": 35})
    r = _run(c, g, dt(17, 20))
    assert g.calls == [] and r["perdidasNaJanela"] == 2 and r["perdido"] is True
    assert sd.LAST_RUN["perdido"] is True and sd.LAST_RUN["perdidasNaJanela"] == 2
    assert sd.last_run_date(c) == HOJE


def test_j24_feitas_de_ontem_e_ignorado():
    c = _conn(); _seed(c, "u1", 1000)
    db.kv_set(c, sd.K_FEITAS, {"data": "2026-10-12", "escopos": ["u1"]}, user_id=None)
    _run(c, _getter({}), dt(17, 6))
    assert len(_snaps(c, "u1")) == 1


def test_j25_intervalo_do_laco_cabe_na_janela(monkeypatch):
    c = _conn(); _seed(c, "u1", 1)
    assert agent.status_snapshot(c, interval_s=60)["jobs"]["janelas"]["snapshotDiario"]["intervaloOk"] is True
    monkeypatch.setenv("B3_AGENT_INTERVAL_S", "600")
    j = agent.status_snapshot(c)["jobs"]["janelas"]["snapshotDiario"]
    assert j["intervaloOk"] is False and j["hhmm"] == "17:05" and j["ate"] == "17:15"
    monkeypatch.setenv("B3_AGENT_INTERVAL_S", "300")
    assert agent.status_snapshot(c)["jobs"]["janelas"]["snapshotDiario"]["intervaloOk"] is True


def test_status_nao_vaza_identidade():
    c = _conn(); _seed(c, "u-secreto@x.com", 1000, [_pos("PETR4")])
    _run(c, _getter({"PETR4": 35}), dt(17, 6))
    assert "u-secreto" not in repr(agent.status_snapshot(c)["snapshotDiario"])


# 2026-10-13 (quick 261013-u7w, orquestrador): o conjunto de contas feitas é
# persistido em LOTES (LOTE_FEITAS) e no fim do tick — nunca uma regravação por
# conta (era O(n^2); teste de fumaça com 52.642 contas levou minutos).
def test_feitas_persistido_em_lote_e_no_fim():
    c = _conn()
    n = sd.LOTE_FEITAS * 2 + 7
    for i in range(n):
        _seed(c, f"u{i:04d}", 100)
    escritas = []
    orig = db.kv_set
    def espiao(conn, key, value, user_id=None):
        if key == sd.K_FEITAS:
            escritas.append(len(value["escopos"]))
        return orig(conn, key, value, user_id=user_id)
    db.kv_set = espiao
    try:
        r = asyncio.run(sd.run_tick(c, _getter({}), dt(17, 6)))
    finally:
        db.kv_set = orig
    assert r["gravadas"] == n and r["pendentesRestantes"] == 0
    assert escritas == [sd.LOTE_FEITAS, sd.LOTE_FEITAS * 2, n]
    assert sd._ler_feitas(c, HOJE) == {f"u{i:04d}" for i in range(n)}
