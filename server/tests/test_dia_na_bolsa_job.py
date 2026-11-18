"""server/tests/test_dia_na_bolsa_job.py — guardião do job "Seu dia na bolsa"
(Fase 51, plano 51-05). Sem rede: Yahoo, benchmark, cache e push são mocados."""
import asyncio
import os
import tempfile
from datetime import date, datetime, timedelta, timezone

import pytest

from app import candle_cache, db, dia_na_bolsa as dnb, setups, technical_snapshot

BRT = timezone(timedelta(hours=-3))
HOJE = "2026-10-13"   # terça-feira, dia de pregão


def dt(h, m, dia=HOJE):
    y, mo, d = (int(x) for x in dia.split("-"))
    return datetime(y, mo, d, h, m, 0, tzinfo=BRT)


def _conn():
    return db.connect(os.path.join(tempfile.mkdtemp(), "b3.db"))


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _arquivo(c, data=HOJE, base="2026-10-09", linhas=(), universo=()):
    db.kv_set(c, "radarDailyArquivo:" + data,
              {"data": data, "dataBase": base, "scanAt": None,
               "linhas": list(linhas), "universo": list(universo)}, user_id=None)


def _linha(t="PETR4", setup="rompimento", entrada=10.0, stop=9.0, alvo=12.0):
    return {"ticker": t, "setup": setup, "decisao": "COMPRAR", "tipo": "a mercado (zona)",
            "entrada": entrada, "stop": stop, "alvo": alvo, "entradaAMercado": True, "close": 10.0}


@pytest.fixture(autouse=True)
def _isola(monkeypatch):
    candle_cache.reset()
    yield
    candle_cache.reset()


# ----------------------------------------------------------------- vistos
def test_visto_do_radar_grava_precos_do_arquivo():
    c = _conn()
    _arquivo(c, linhas=[_linha()])
    r = dnb.registrar_vistos(c, "u1", ["petr4"], "radar", dt(11, 0))
    assert r == {"registrados": 1, "semPlano": 0, "ignorados": 0}
    (v,) = dnb.ler_vistos(c, "u1")
    assert (v["ticker"], v["setup"], v["fonte"]) == ("PETR4", "rompimento", "radar")
    assert (v["entrada"], v["stop"], v["alvo"], v["dataBase"]) == (10.0, 9.0, 12.0, "2026-10-09")
    assert v["entradaAMercado"] is True and v["vistoEm"] == HOJE and v["origem"] == "radar"
    # escopo: outra conta não enxerga (T-51-12)
    assert dnb.ler_vistos(c, "u2") == []
    assert db.kv_get(c, dnb.K_VISTOS, None, user_id=None) is None


def test_visto_duplicado_no_mesmo_dia_nao_duplica():
    c = _conn()
    _arquivo(c, linhas=[_linha()])
    dnb.registrar_vistos(c, "u1", ["PETR4"], "radar", dt(11, 0))
    r = dnb.registrar_vistos(c, "u1", ["PETR4"], "watchlist", dt(15, 0))
    assert r["registrados"] == 0
    assert len(dnb.ler_vistos(c, "u1")) == 1


def test_visto_fora_do_arquivo_usa_snapshot_do_cache(monkeypatch):
    c = _conn()
    _arquivo(c, linhas=[])
    cs = [{"date": "2026-10-09", "open": 1, "high": 1, "low": 1, "close": 20.0},
          {"date": "2026-10-12", "open": 1, "high": 1, "low": 1, "close": 21.0}]
    monkeypatch.setattr(candle_cache, "peek", lambda t, i="1d": cs)
    monkeypatch.setattr(technical_snapshot, "build", lambda t, c_, p, interval="1d": {"setups": {}, "close": 21.0})
    monkeypatch.setattr(setups, "plano_do_resultado", lambda s, close=None: {
        "decisao": "COMPRAR", "setup": "pullback", "tipo": "no rompimento do gatilho",
        "entrada": 22.0, "stop": 20.0, "alvo": 26.0})
    r = dnb.registrar_vistos(c, "u1", ["VALE3"], "carteira", dt(11, 0))
    assert r["registrados"] == 1
    (v,) = dnb.ler_vistos(c, "u1")
    assert v["fonte"] == "snapshot" and v["dataBase"] == "2026-10-12"
    assert (v["entrada"], v["stop"], v["alvo"], v["precoBase"]) == (22.0, 20.0, 26.0, 21.0)
    assert v["entradaAMercado"] is False


def test_visto_sem_plano_operavel_ou_sem_dado_conta_semplano(monkeypatch):
    c = _conn()
    _arquivo(c, linhas=[])
    cs = [{"date": "2026-10-12", "open": 1, "high": 1, "low": 1, "close": 21.0}]
    monkeypatch.setattr(candle_cache, "peek",
                        lambda t, i="1d": cs if t == "VALE3" else [])
    monkeypatch.setattr(technical_snapshot, "build", lambda t, c_, p, interval="1d": {"setups": {}, "close": 21.0})
    monkeypatch.setattr(setups, "plano_do_resultado", lambda s, close=None: {"decisao": "AGUARDAR CONFIRMAÇÃO"})
    r = dnb.registrar_vistos(c, "u1", ["VALE3", "ITUB4"], "radar", dt(11, 0))
    assert r == {"registrados": 0, "semPlano": 2, "ignorados": 0}
    assert dnb.ler_vistos(c, "u1") == []


def test_visto_valida_ticker_origem_e_tamanho():
    c = _conn()
    _arquivo(c, linhas=[_linha()])
    r = dnb.registrar_vistos(c, "u1", ["abc", "PETR4;DROP", "PETR4", 123, None], "radar", dt(11, 0))
    assert r["ignorados"] == 4 and r["registrados"] == 1
    with pytest.raises(ValueError):
        dnb.registrar_vistos(c, "u1", ["PETR4"], "cliente", dt(11, 0))
    with pytest.raises(ValueError):
        dnb.registrar_vistos(c, "u1", ["PETR4"] * 61, "radar", dt(11, 0))
    with pytest.raises(ValueError):
        dnb.registrar_vistos(c, None, ["PETR4"], "radar", dt(11, 0))


def test_visto_nao_recebe_preco_do_cliente():
    import inspect
    assert list(inspect.signature(dnb.registrar_vistos).parameters) == [
        "conn", "uid", "tickers", "origem", "agora"]


def test_visto_poda_aberto_com_41_dias():
    c = _conn()
    velho = {"ticker": "VALE3", "setup": "x", "origem": "radar", "vistoEm": "2026-08-30",
             "dataBase": "2026-09-02", "entrada": 1.0, "stop": 0.5, "alvo": 2.0,
             "entradaAMercado": True, "precoBase": 1.0, "fonte": "radar", "estado": None}
    db.kv_set(c, dnb.K_VISTOS, [velho], user_id="u1")
    _arquivo(c, linhas=[_linha()])
    dnb.registrar_vistos(c, "u1", ["PETR4"], "radar", dt(11, 0))
    assert [v["ticker"] for v in dnb.ler_vistos(c, "u1")] == ["PETR4"]


# ======================================================================
# Job de fechamento (J1-J15)
# ======================================================================
from app import benchmark, brapi, llm, pregao, push, radar_daily, snapshot_diario, store, yahoo  # noqa: E402


def _dias(n, fim=HOJE):
    d, out = date.fromisoformat(fim), []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return out[::-1]


def serie(n=260, fim=HOJE, hoje_candle=None):
    """Série diária neutra (alterna 10,0 / 10,2): nenhuma regra de raridade
    dispara. `hoje_candle` substitui campos do ÚLTIMO candle."""
    cs = []
    for i, d in enumerate(_dias(n, fim)):
        c = 10.0 + 0.2 * (i % 2)
        cs.append({"date": d, "open": c, "high": c + 0.05, "low": c - 0.05, "close": c, "volume": 1000})
    if hoje_candle:
        cs[-1].update(hoje_candle)
    return cs


def serie_ibov(fim=HOJE):
    """Alterna 100/101 e fecha hoje em 100,5: |retorno| menor que o p95 e dentro
    da faixa de 52 semanas — nenhuma regra do IBOV dispara."""
    out = [{"date": d, "close": 100.0 + (i % 2)} for i, d in enumerate(_dias(260, fim))]
    out[-1]["close"] = 100.5
    return out


class Rede:
    """Yahoo e benchmark mocados; registra as chamadas, em ordem."""
    def __init__(self, monkeypatch, fim=HOJE, candles=None, ibov_ok=True):
        self.calls, self.ibov_calls, self.fim = [], 0, fim
        self.candles = candles or {}
        self.ibov_ok = ibov_ok

        async def get_history(t, rng="1mo", interval="1d"):
            self.calls.append(t)
            return {"t": t, "currency": "BRL", "candles": self.candles.get(t) or serie(fim=self.fim)}

        async def serie_ibov_(period=None):
            self.ibov_calls += 1
            if not self.ibov_ok:
                raise benchmark.BenchmarkIndisponivel("fora")
            return {"candles": serie_ibov(self.fim)}

        monkeypatch.setattr(yahoo, "get_history", get_history)
        monkeypatch.setattr(benchmark, "serie_ibov", serie_ibov_)


def _conta(c, uid, positions=(), watchlist=()):
    db.kv_set(c, "cash", 1000, user_id=uid)
    db.kv_set(c, "watchlist", list(watchlist), user_id=uid)   # sem isso vale a watchlist padrão
    db.kv_set(c, "positions", [{"t": t, "qty": 100, "avg": 10} for t in positions], user_id=uid)


def _visto(t="PETR4", **kw):
    v = {"ticker": t, "setup": "rompimento", "origem": "radar", "vistoEm": "2026-10-09",
         "dataBase": "2026-10-09", "entrada": 10.0, "stop": 9.0, "alvo": 12.0,
         "entradaAMercado": True, "precoBase": 10.0, "fonte": "radar", "estado": None}
    v.update(kw)
    return v


def _snapshot_ok(c):
    db.kv_set(c, snapshot_diario.K_LAST_RUN, HOJE, user_id=None)


@pytest.fixture(autouse=True)
def _isola_job(monkeypatch):
    dnb._MEMO.update(data=None, series={}, ibov=None, ibovFonte=None)
    for k in ("B3_DIA_NA_BOLSA_OFF", "B3_DIA_NA_BOLSA_HHMM", "B3_DIA_NA_BOLSA_MAX_YAHOO"):
        monkeypatch.delenv(k, raising=False)
    yield


def _card(c, uid):
    return db.kv_get(c, dnb.K_CARD, None, user_id=uid)


def test_j1_sabado_e_j2_feriado_nao_rodam(monkeypatch):
    c = _conn()
    rede = Rede(monkeypatch)
    assert _run(dnb.maybe_run(c, dt(17, 30, "2026-10-17"))) is None            # sábado
    assert pregao.is_holiday(date(2026, 11, 20)) and date(2026, 11, 20).weekday() == 4
    assert _run(dnb.maybe_run(c, dt(17, 30, "2026-11-20"))) is None            # feriado em dia útil
    assert _run(dnb.maybe_run(c, dt(21, 0, "2026-11-20"))) is None            # nem a passada final
    assert rede.calls == [] and rede.ibov_calls == 0


def test_j3_antes_do_horario_e_j4_idempotente(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    Rede(monkeypatch)
    _conta(c, "u1")
    assert _run(dnb.maybe_run(c, dt(17, 10))) is None
    r = _run(dnb.maybe_run(c, dt(17, 25)))
    assert r is not None and dnb.last_run_date(c) == HOJE
    assert _run(dnb.maybe_run(c, dt(17, 50))) is None      # lastRun do dia: não roda de novo


def test_j5_espera_o_snapshot_ate_1740(monkeypatch):
    c = _conn()
    Rede(monkeypatch)
    _conta(c, "u1")
    assert _run(dnb.maybe_run(c, dt(17, 30))) is None      # snapshot ainda não fechou
    assert dnb.last_run_date(c) is None
    assert _run(dnb.maybe_run(c, dt(17, 41))) is not None  # depois de 17:40 segue sem ele
    assert dnb.last_run_date(c) == HOJE


def test_j6_stop_e_alvo_geram_linhas_do_mesmo_formato(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4", "VALE3"])
    Rede(monkeypatch, candles={
        "PETR4": serie(hoje_candle={"open": 10.0, "low": 8.9, "close": 10.0}),
        "VALE3": serie(hoje_candle={"open": 10.0, "high": 12.1, "close": 10.0})})
    _conta(c, "u1")
    db.kv_set(c, dnb.K_VISTOS, [_visto("PETR4"), _visto("VALE3")], user_id="u1")
    _run(dnb.maybe_run(c, dt(17, 30)))
    card = _card(c, "u1")
    assert card["vazio"] is False
    linhas = {l["ticker"]: l for l in card["familias"]["1"]["linhas"]}
    assert linhas["PETR4"]["chave"] == "f1_stop" and linhas["PETR4"]["resultado"] == "stop"
    assert linhas["VALE3"]["chave"] == "f1_alvo" and linhas["VALE3"]["chip"] == "chip_alvo"
    assert set(linhas["PETR4"]) == set(linhas["VALE3"])           # mesmo formato
    assert linhas["PETR4"]["vals"]["R"].startswith("-") and linhas["PETR4"]["vals"]["R"].endswith("R")
    assert linhas["VALE3"]["vals"]["R"].startswith("+")
    assert [l["ticker"] for l in card["familias"]["1"]["linhas"]] == ["PETR4", "VALE3"]
    assert card["familias"]["1"]["placar"]["vals"] == {"X": 2, "Y": 1, "Z": 1, "W": 0}
    assert card["chamadas"]["1"]["chave"] == "chamada_f1"


def test_j7_visto_operado_depois_fica_fora(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    Rede(monkeypatch, candles={"PETR4": serie(hoje_candle={"open": 10.0, "low": 8.9, "close": 10.0})})
    _conta(c, "u1")
    db.kv_set(c, dnb.K_VISTOS, [_visto("PETR4")], user_id="u1")
    db.kv_set(c, "history", [{"date": "12/10/2026 14:00", "type": "COMPRA", "t": "PETR4", "qty": 100,
                              "price": 10.0}], user_id="u1")
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert _card(c, "u1") == {"data": HOJE, "vazio": True}


def test_j8_dia_sem_nada_grava_marcador_vazio_e_payload_sem_card(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    Rede(monkeypatch)
    _conta(c, "u1", positions=["PETR4"])
    db.kv_set(c, dnb.K_CARD, {"data": "2026-10-09", "vazio": False, "familias": {}}, user_id="u1")
    called = []

    async def send(*a, **k):
        called.append(1)
        return {"sent": 1}
    monkeypatch.setattr(push, "send_to_user", send)
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert _card(c, "u1") == {"data": HOJE, "vazio": True}
    p = dnb.payload_para(c, "u1", "estudo", dt(17, 35))
    assert p["card"] is None and called == []
    assert len(p["ultimas4Semanas"]) == 28 and p["ultimas4Semanas"][-1]["data"] == HOJE


def test_j9_ibov_indisponivel_tenta_de_novo_e_na_final_fica_nulo(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    rede = Rede(monkeypatch, ibov_ok=False)
    _conta(c, "u1", positions=["PETR4"])
    db.kv_set(c, "agentLog", [{"time": "13/10/2026 14:10", "kind": "info", "tag": "stop", "t": "PETR4",
                               "text": "x"}], user_id="u1")
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert _card(c, "u1") is None and dnb.last_run_date(c) is None     # pendente: nada parcial
    _run(dnb.maybe_run(c, dt(20, 5)))                                   # passada final
    card = _card(c, "u1")
    assert dnb.last_run_date(c) == HOJE and card["vazio"] is False
    f2 = card["familias"]["2"]
    assert f2["linhas"][0]["chave"] == "f2_stop_executado"
    assert "carteiraIbov" not in f2 or f2["carteiraIbov"]["ibovPct"] is None
    assert "3" not in card["familias"]                                  # sem IBOV, sem regra do IBOV


def test_j10_barra_parcial_do_cache_nao_vale_e_vai_ao_yahoo(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    rede = Rede(monkeypatch)
    _conta(c, "u1", positions=["PETR4"])
    candle_cache._CACHE["PETR4@1d"] = {"candles": serie(), "currency": "BRL",
                                       "at": dt(14, 0).timestamp(), "src": "brapi"}
    r = _run(dnb.maybe_run(c, dt(17, 30)))
    assert rede.calls == ["PETR4"] and r["cacheHits"] == 0


def test_j13_cache_finalizado_zero_yahoo_e_cache_vazio_mesmo_card(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    rede = Rede(monkeypatch)
    _conta(c, "u1", positions=["PETR4"])
    db.kv_set(c, dnb.K_VISTOS, [_visto("PETR4")], user_id="u1")
    candle_cache._CACHE["PETR4@1d"] = {"candles": serie(hoje_candle={"open": 10.0, "low": 8.9, "close": 10.0}),
                                       "currency": "BRL", "at": dt(17, 12).timestamp(), "src": "yahoo"}
    r = _run(dnb.maybe_run(c, dt(17, 30)))
    assert "PETR4" not in rede.calls and r["cacheHits"] == 1
    card_cache = _card(c, "u1")
    # cache vazio: o job busca tudo no Yahoo e produz o mesmo card
    candle_cache.reset()
    dnb._MEMO.update(data=None, series={}, ibov=None)
    db.kv_set(c, dnb.K_LAST_RUN, None, user_id=None)
    db.kv_set(c, dnb.K_FEITAS, None, user_id=None)
    db.kv_set(c, dnb.K_TENTATIVA, None, user_id=None)
    db.kv_set(c, dnb.K_YAHOO_DIA, None, user_id=None)
    db.kv_set(c, dnb.K_VISTOS, [_visto("PETR4")], user_id="u1")
    rede2 = Rede(monkeypatch, candles={"PETR4": serie(hoje_candle={"open": 10.0, "low": 8.9, "close": 10.0})})
    r2 = _run(dnb.maybe_run(c, dt(17, 30)))
    assert rede2.calls == ["PETR4"] and r2["cacheHits"] == 0
    card_y = _card(c, "u1")
    assert card_y["familias"]["1"]["linhas"] == card_cache["familias"]["1"]["linhas"]


def test_j12_sem_barra_de_hoje_nao_gera_card_parcial_e_fecha_as_20h(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    ontem = "2026-10-09"
    rede = Rede(monkeypatch, candles={"PETR4": serie(fim=ontem)})
    _conta(c, "u1", positions=["PETR4"])
    db.kv_set(c, dnb.K_VISTOS, [_visto("PETR4")], user_id="u1")
    r = _run(dnb.maybe_run(c, dt(17, 45)))
    assert r["pendentes"] == 1 and _card(c, "u1") is None and dnb.last_run_date(c) is None
    assert "PETR4" in r["semDado"]
    # < 10 min depois: não martela o Yahoo
    n = len(rede.calls)
    assert _run(dnb.maybe_run(c, dt(17, 50))) is None and len(rede.calls) == n
    # barra aparece: o card sai no ciclo seguinte
    rede.candles["PETR4"] = serie(hoje_candle={"open": 10.0, "low": 8.9, "close": 10.0})
    _run(dnb.maybe_run(c, dt(17, 56)))
    assert _card(c, "u1")["familias"]["1"]["linhas"][0]["ticker"] == "PETR4"
    assert dnb.last_run_date(c) == HOJE


def test_j12b_passada_final_fecha_com_ticker_faltante_fora(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    Rede(monkeypatch, candles={"PETR4": serie(fim="2026-10-09")})
    _conta(c, "u1", positions=["PETR4"])
    db.kv_set(c, dnb.K_VISTOS, [_visto("PETR4")], user_id="u1")
    _run(dnb.maybe_run(c, dt(17, 45)))
    assert dnb.last_run_date(c) is None
    _run(dnb.maybe_run(c, dt(20, 1)))
    assert dnb.last_run_date(c) == HOJE
    assert _card(c, "u1") == {"data": HOJE, "vazio": True}      # sem inventar valor


def test_j14_teto_de_yahoo_respeita_prioridade_e_registra_sem_dado(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    monkeypatch.setenv("B3_DIA_NA_BOLSA_MAX_YAHOO", "5")
    universo = [f"UNIV{i}" for i in range(70)]
    _arquivo(c, universo=universo)
    rede = Rede(monkeypatch)
    _conta(c, "u1", positions=["POS1", "POS2"], watchlist=["WL1", "WL2", "WL3"])
    db.kv_set(c, dnb.K_VISTOS, [_visto("VIS1"), _visto("VIS2")], user_id="u1")
    r = _run(dnb.maybe_run(c, dt(17, 30)))
    assert rede.calls == ["VIS1", "VIS2", "POS1", "POS2"] and rede.ibov_calls == 1
    assert r["yahooChamadas"] == 5
    assert set(r["semDado"]) >= {"WL1", "WL2", "WL3"} and "UNIV0" in r["semDado"]
    ydia = db.kv_get(c, dnb.K_YAHOO_DIA, None, user_id=None)
    assert ydia["chamadas"] == 5 and "WL1" in ydia["semDado"]
    assert dnb.LAST_RUN["yahooChamadas"] == 5 and dnb.LAST_RUN["cacheHits"] == 0
    print("J14 yahooChamadas=%d cacheHits=%d semDado=%d" % (r["yahooChamadas"], r["cacheHits"], len(r["semDado"])))


def test_j14b_segunda_passada_reaproveita_e_nao_passa_do_teto(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    monkeypatch.setenv("B3_DIA_NA_BOLSA_MAX_YAHOO", "3")
    _arquivo(c, universo=[])
    rede = Rede(monkeypatch)
    _conta(c, "u1", positions=["POS1", "POS2"])
    _conta(c, "u2", positions=["POS3"])
    r1 = _run(dnb.maybe_run(c, dt(17, 30)))
    n1 = len(rede.calls) + rede.ibov_calls
    assert n1 == 3 and r1["pendentes"] >= 1 and dnb.last_run_date(c) is None
    _run(dnb.maybe_run(c, dt(17, 45)))
    assert len(rede.calls) + rede.ibov_calls == 3           # nenhuma busca repetida nem nova
    ydia = db.kv_get(c, dnb.K_YAHOO_DIA, None, user_id=None)
    assert ydia["chamadas"] == 3


def test_j15_duas_contas_com_o_mesmo_ticker_uma_busca(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=[])
    rede = Rede(monkeypatch)
    _conta(c, "u1", positions=["PETR4"])
    _conta(c, "u2", positions=["PETR4"])
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert rede.calls.count("PETR4") == 1


def test_j11_zero_brapi_e_zero_llm_no_job(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    Rede(monkeypatch)

    def boom(*a, **k):
        raise AssertionError("brapi/llm proibidos no job")
    for mod in (brapi, llm):
        for nome in dir(mod):
            if nome.startswith(("get_", "fetch", "call", "quote", "history", "analyze")) \
                    and callable(getattr(mod, nome)):
                monkeypatch.setattr(mod, nome, boom)
    _conta(c, "u1", positions=["PETR4"])
    assert _run(dnb.maybe_run(c, dt(17, 30))) is not None


def test_conta_isolada_card_de_a_nao_aparece_para_b(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    Rede(monkeypatch, candles={"PETR4": serie(hoje_candle={"open": 10.0, "low": 8.9, "close": 10.0})})
    _conta(c, "uA")
    _conta(c, "uB")
    db.kv_set(c, dnb.K_VISTOS, [_visto("PETR4")], user_id="uA")
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert _card(c, "uA")["vazio"] is False and _card(c, "uB") == {"data": HOJE, "vazio": True}


def test_payload_ordem_por_modo_atrasado_e_rotulo(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    Rede(monkeypatch, candles={"PETR4": serie(hoje_candle={"open": 10.0, "low": 8.9, "close": 10.0})})
    _conta(c, "u1")
    db.kv_set(c, dnb.K_VISTOS, [_visto("PETR4")], user_id="u1")
    db.kv_set(c, "agentLog", [{"time": "13/10/2026 11:00", "kind": "info",
                               "marcoMotor": {"tipo": "breakeven", "ticker": "VALE3", "stop": 30.5,
                                              "motivo": "gestao_breakeven"}, "text": "x"}], user_id="u1")
    _run(dnb.maybe_run(c, dt(17, 30)))
    est = dnb.payload_para(c, "u1", "estudo", dt(18, 0))
    ope = dnb.payload_para(c, "u1", "operador", dt(18, 0))
    assert est["card"]["ordem"] == [1, 2] and ope["card"]["ordem"] == [2, 1]
    assert est["card"]["chamada"]["chave"] == "chamada_f1" and ope["card"]["chamada"]["chave"] == "chamada_f2"
    assert est["card"]["atrasado"] is False and est["card"]["dataLabel"] == "13/10"
    assert est["convite"] is True and est["fechamento"] == {"ligado": False, "decidido": False}
    # dia seguinte (pregão) depois das 17:30 sem job novo: card velho = atrasado
    amanha = dnb.payload_para(c, "u1", "estudo", dt(17, 45, "2026-10-14"))
    assert amanha["card"]["atrasado"] is True
    antes = dnb.payload_para(c, "u1", "estudo", dt(9, 0, "2026-10-14"))
    assert antes["card"]["atrasado"] is False
    sab = dnb.payload_para(c, "u1", "estudo", dt(18, 0, "2026-10-17"))
    assert sab["card"]["atrasado"] is False
    assert [d["pregao"] for d in sab["ultimas4Semanas"]][-1] is False


def test_famila3_amplitude_ibov_raro_escolhe_mercado(monkeypatch):
    c = _conn()
    _snapshot_ok(c)
    univ = [f"AAAA{i}" for i in range(1, 36)]
    _arquivo(c, universo=univ)
    ibov = serie_ibov()
    ibov[-1]["close"] = ibov[-2]["close"] * 0.93     # queda de 7%: p95 estourado
    rede = Rede(monkeypatch)

    async def serie_ibov_(period=None):
        return {"candles": ibov}
    monkeypatch.setattr(benchmark, "serie_ibov", serie_ibov_)
    _conta(c, "u1")
    _run(dnb.maybe_run(c, dt(17, 30)))
    card = _card(c, "u1")
    fato = card["familias"]["3"]["fato"]
    assert fato["regra"] == "ibov_raro" and fato["selo"] == "selo_p95" and fato["doUsuario"] is False
    assert fato["vals"]["direcao"] == "caiu" and fato["vals"]["pct"].endswith("%")
    p = dnb.payload_para(c, "u1", "estudo", dt(18, 0))
    assert p["card"]["familias"]["3"]["fato"]["conceito"]["rotulo"]


# ======================================================================
# Push de fechamento, "e se" de ontem e hook do scheduler
# ======================================================================
def _cenario_push(monkeypatch, c, quer=True, token=True, modo=None):
    _snapshot_ok(c)
    _arquivo(c, universo=["PETR4"])
    Rede(monkeypatch, candles={"PETR4": serie(hoje_candle={"open": 10.0, "low": 8.9, "close": 10.0})})
    _conta(c, "u1")
    db.kv_set(c, dnb.K_VISTOS, [_visto("PETR4")], user_id="u1")
    if quer:
        push.decidir_fechamento(c, "u1", True)
    if token:
        db.kv_set(c, "pushTokens", [{"token": "abc"}], user_id="u1")
    if modo:
        db.kv_set(c, "pushPrefs", {**push.prefs_for(c, "u1"), "modo": modo}, user_id="u1")
    enviados = []

    async def send(conn, uid, title, body, som=True, prioridade="10", client=None, extra=None):
        enviados.append({"uid": uid, "title": title, "body": body, "som": som,
                         "prioridade": prioridade, "extra": extra})
        return {"sent": 1, "total": 1, "detalhes": []}
    monkeypatch.setattr(push, "send_to_user", send)
    return enviados


def test_push_um_por_dia_com_corpo_da_primeira_familia_do_modo(monkeypatch):
    c = _conn()
    env = _cenario_push(monkeypatch, c, modo="estudo")
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert len(env) == 1
    e = env[0]
    assert e["title"] == "Seu dia na bolsa" and e["extra"] == {"kind": "fechamento"} and "t" not in e["extra"]
    assert e["som"] is False and e["prioridade"] == "5" and "PETR4" in e["body"]
    assert _card(c, "u1")["pushEnviado"] is True
    # segunda passada no mesmo dia: nenhum push novo
    db.kv_set(c, dnb.K_FEITAS, None, user_id=None)
    db.kv_set(c, dnb.K_LAST_RUN, None, user_id=None)
    db.kv_set(c, dnb.K_TENTATIVA, None, user_id=None)
    _run(dnb.maybe_run(c, dt(17, 50)))
    assert len(env) == 1


def test_push_corpo_segue_a_ordem_do_modo_operador(monkeypatch):
    c = _conn()
    env = _cenario_push(monkeypatch, c, modo="operador")
    db.kv_set(c, "agentLog", [{"time": "13/10/2026 11:00", "kind": "info",
                               "marcoMotor": {"tipo": "stop_subiu", "ticker": "VALE3", "stop": 30.5,
                                              "motivo": "gestao_trailing"}, "text": "x"}], user_id="u1")
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert len(env) == 1 and "VALE3" in env[0]["body"] and "PETR4" not in env[0]["body"]


def test_push_sem_convite_aceito_grava_card_e_nao_envia(monkeypatch):
    c = _conn()
    env = _cenario_push(monkeypatch, c, quer=False)
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert env == [] and _card(c, "u1")["vazio"] is False and _card(c, "u1")["pushEnviado"] is False


def test_push_sem_token_nao_envia(monkeypatch):
    c = _conn()
    env = _cenario_push(monkeypatch, c, token=False)
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert env == []


def test_push_prefs_levantando_e_fail_closed(monkeypatch):
    c = _conn()
    env = _cenario_push(monkeypatch, c)

    def boom(conn, uid):
        raise RuntimeError("kv fora")
    monkeypatch.setattr(push, "prefs_for", boom)
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert env == [] and _card(c, "u1")["vazio"] is False


def test_push_teto_de_engajamento_esgotado_nao_envia(monkeypatch):
    c = _conn()
    env = _cenario_push(monkeypatch, c)
    assert push.reservar_engajamento(c, "u1", HOJE, "radar")
    assert push.reservar_engajamento(c, "u1", HOJE, "outro")      # teto de 2 usado
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert env == []


def test_push_card_vazio_nao_envia(monkeypatch):
    c = _conn()
    env = _cenario_push(monkeypatch, c)
    db.kv_set(c, dnb.K_VISTOS, [], user_id="u1")
    _run(dnb.maybe_run(c, dt(17, 30)))
    assert env == [] and _card(c, "u1") == {"data": HOJE, "vazio": True}


def test_e_se_de_ontem_na_segunda_pega_a_sexta_por_ordem_de_ticker():
    c = _conn()
    est = lambda res, em: {"resultado": res, "r": 1.0, "resolvidoEm": em, "aberto": False}  # noqa: E731
    db.kv_set(c, dnb.K_VISTOS, [
        _visto("VALE3", estado=est("stop", "2026-10-09")),
        _visto("PETR4", estado=est("alvo", "2026-10-09")),
        _visto("ABEV3", estado=est("expirou", "2026-10-09")),
        _visto("ITUB4", estado=est("alvo", "2026-10-08"))], user_id="u1")
    # terça 13/10: o pregão anterior é 09/10 (12/10 é feriado)
    r = dnb.e_se_de_ontem(c, "u1", "2026-10-13")
    assert r == {"chave": "corpo_ontem_alvo", "T": "PETR4"}   # ordem de ticker, sem preferir alvo
    assert dnb.e_se_de_ontem(c, "u2", "2026-10-13") is None
    # operado depois: sai
    db.kv_set(c, "history", [{"date": "09/10/2026 15:00", "type": "COMPRA", "t": "PETR4"}], user_id="u1")
    assert dnb.e_se_de_ontem(c, "u1", "2026-10-13") == {"chave": "corpo_ontem_stop", "T": "VALE3"}


def test_agent_tem_hook_do_job_e_marco_motor():
    src = open(os.path.join(os.path.dirname(__file__), "..", "app", "agent.py"), encoding="utf-8").read()
    assert src.count("dia_na_bolsa.maybe_run") == 1 and src.count('"marcoMotor"') == 1
    assert src.index("snapshot_diario.maybe_run") < src.index("dia_na_bolsa.maybe_run") \
        < src.index("ADR-001 (item 7): passada INTRADAY")
