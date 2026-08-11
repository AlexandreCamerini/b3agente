"""Objetivo 5 — cache de candles: usa cache, busca só o delta, revalida o último."""
import asyncio
from app import candle_cache as cc


def _c(date, close, vol=100):
    return {"date": date, "open": close, "high": close + 1, "low": close - 1, "close": close, "volume": vol}


def test_merge_revalida_e_anexa():
    old = [_c("2026-06-01", 10), _c("2026-06-02", 11), _c("2026-06-03", 12)]
    # 'new' revalida 06-03 (close 12 -> 12.5) e anexa 06-04
    new = [_c("2026-06-03", 12.5), _c("2026-06-04", 13)]
    m = cc.merge_candles(old, new)
    datas = [c["date"] for c in m]
    assert datas == ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"]
    last3 = next(c for c in m if c["date"] == "2026-06-03")
    assert last3["close"] == 12.5          # fresco venceu (revalidação do candle corrente)
    assert m[-1]["close"] == 13            # novo dia anexado


def test_merge_bordas():
    assert cc.merge_candles([], [_c("d1", 1)]) == [_c("d1", 1)]
    base = [_c("d1", 1)]
    assert cc.merge_candles(base, []) == base
    assert cc.merge_candles(None, None) == []


def test_load_miss_depois_delta():
    cc.reset()
    calls = []

    full_2y = {"currency": "BRL", "candles": [_c(f"2026-04-{i:02d}", 10 + i) for i in range(1, 29)]}
    recent_1mo = {"currency": "BRL", "candles": [
        _c("2026-04-27", 99),    # revalida (estava 36 -> agora 99)
        _c("2026-04-28", 99),    # revalida
        _c("2026-04-29", 50),    # novo dia
    ]}

    async def fetch(rng):
        calls.append(rng)
        return full_2y if rng == cc.FULL_RANGE else recent_1mo

    # 1ª carga: MISS, busca série cheia (FULL_RANGE)
    r1 = asyncio.run(cc.load("PETR4", fetch, now=1000.0))
    assert r1["cacheStatus"] == "miss"
    assert calls == [cc.FULL_RANGE]
    assert len(r1["candles"]) == 28

    # 2ª carga logo em seguida (< _MIN_DELTA_INTERVAL): FRESH, sem rebuscar
    r2 = asyncio.run(cc.load("PETR4", fetch, now=1000.0 + 1))
    assert r2["cacheStatus"] == "fresh"
    assert calls == [cc.FULL_RANGE]          # não chamou de novo

    # 3ª carga após o intervalo: DELTA, busca só a janela recente e funde
    r3 = asyncio.run(cc.load("PETR4", fetch, now=1000.0 + 100))
    assert r3["cacheStatus"] == "delta"
    assert calls == [cc.FULL_RANGE, cc.RECENT_RANGE]   # só o recente na 2ª busca
    datas = [c["date"] for c in r3["candles"]]
    assert "2026-04-29" in datas                       # novo dia anexado
    rev = next(c for c in r3["candles"] if c["date"] == "2026-04-27")
    assert rev["close"] == 99                           # último/atual revalidado


def test_load_interval_segmenta_cache():
    cc.reset()

    async def fetch_d(rng):
        return {"currency": "BRL", "candles": [_c("2026-01-01", 10)]}

    async def fetch_w(rng):
        return {"currency": "BRL", "candles": [_c("2026-01-05", 20)]}

    a = asyncio.run(cc.load("VALE3", fetch_d, interval="1d", now=1.0))
    b = asyncio.run(cc.load("VALE3", fetch_w, interval="1wk", now=1.0))
    assert a["cacheStatus"] == "miss" and b["cacheStatus"] == "miss"  # chaves distintas
    assert len(cc.stats()) == 2


def test_load_respeita_teto_de_tamanho():
    cc.reset()
    big = {"currency": "BRL", "candles": [_c(f"d{i:04d}", i) for i in range(cc._MAX + 200)]}

    async def fetch(rng):
        return big

    r = asyncio.run(cc.load("BBAS3", fetch, now=1.0))
    assert len(r["candles"]) == cc._MAX     # não cresce sem limite


# (FASE 5) O runner offline foi movido para o FIM do arquivo: aqui no meio,
# os testes definidos abaixo dele nunca rodavam no modo offline (o Python
# executa de cima para baixo e o globals() ainda não os continha).


# ===== BLOCO A1 — robustez do provedor =====
def test_falha_total_vira_erro_amigavel():
    import asyncio
    from app import candle_cache
    candle_cache._CACHE.clear()

    async def fetch(rng):
        raise RuntimeError("404 Not Found crumb")
    try:
        asyncio.run(candle_cache.load("ELET3", fetch))
        assert False, "deveria falhar"
    except ValueError as e:
        msg = str(e)
        assert "Sem histórico disponível para ELET3" in msg
        assert "404" not in msg and "crumb" not in msg      # nada técnico vaza


def test_retry_em_1y_salva_a_carga():
    import asyncio
    from app import candle_cache
    candle_cache._CACHE.clear()
    calls = []

    async def fetch(rng):
        calls.append(rng)
        if rng != "1y":
            raise RuntimeError("404")
        return {"candles": [{"date": "2026-01-02", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}], "currency": "BRL"}
    r = asyncio.run(candle_cache.load("XPTO3", fetch))
    assert r["candles"] and calls[-1] == "1y"


def test_delta_com_falha_serve_cache_stale():
    import asyncio
    from app import candle_cache
    candle_cache._CACHE.clear()
    ok = {"candles": [{"date": "2026-01-02", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}], "currency": "BRL"}
    state = {"fail": False}

    async def fetch(rng):
        if state["fail"]:
            raise RuntimeError("429")
        return ok
    asyncio.run(candle_cache.load("YYYY3", fetch, now=1000.0))
    state["fail"] = True
    r = asyncio.run(candle_cache.load("YYYY3", fetch, now=1000.0 + 10 * 60))   # após o TTL do delta
    assert r["cacheStatus"] == "stale" and r["candles"]


# ===== FASE 5 — L2 persistente (SQLite) =====
def _fresh_l2():
    import os
    import tempfile
    from app import db
    d = tempfile.mkdtemp(prefix="b3_cc_")
    return db.connect(os.path.join(d, "b3_agente.db"))


def test_l2_persiste_e_reidrata_apos_reboot():
    # write-through no miss; "reboot" (reset da memória) reidrata do SQLite e
    # busca só o DELTA — nunca mais a série cheia.
    import asyncio
    from app import candle_cache
    conn = _fresh_l2()
    candle_cache.reset()
    candle_cache.configure_db(conn)
    calls = []

    async def fetch(rng):
        calls.append(rng)
        return {"currency": "BRL", "candles": [_c(f"2026-05-{i:02d}", 10 + i) for i in range(1, 21)]}

    r1 = asyncio.run(candle_cache.load("PETR4", fetch, now=1000.0))
    assert r1["cacheStatus"] == "miss" and calls == [candle_cache.FULL_RANGE]
    # simula redeploy: memória zerada, SQLite fica
    candle_cache._CACHE.clear()
    r2 = asyncio.run(candle_cache.load("PETR4", fetch, now=2000.0))
    assert r2["cacheStatus"] == "delta"                     # reidratou do L2
    assert calls == [candle_cache.FULL_RANGE, candle_cache.RECENT_RANGE]  # só o delta
    assert len(r2["candles"]) == 20
    candle_cache.configure_db(None)  # não vaza estado para os demais testes
    candle_cache.reset()


def test_l2_desligado_mantem_comportamento_antigo():
    # Sem configure_db (suítes puras), nada toca disco e o miss segue cheio.
    import asyncio
    from app import candle_cache
    candle_cache.configure_db(None)
    candle_cache.reset()
    calls = []

    async def fetch(rng):
        calls.append(rng)
        return {"currency": "BRL", "candles": [_c("2026-05-01", 10)]}

    asyncio.run(candle_cache.load("VALE3", fetch, now=1000.0))
    candle_cache._CACHE.clear()
    asyncio.run(candle_cache.load("VALE3", fetch, now=2000.0))
    assert calls == [candle_cache.FULL_RANGE, candle_cache.FULL_RANGE]  # sem L2 => full de novo


def test_l2_corrompido_degrada_para_miss():
    # Linha inválida no SQLite não derruba: cai no fluxo de miss (série cheia).
    import asyncio
    from app import candle_cache
    conn = _fresh_l2()
    conn.execute("INSERT INTO candle_cache(k, currency, candles, at) VALUES(?,?,?,?)",
                 ("ITUB4@1d", "BRL", "{nao-e-json", 1.0))
    conn.commit()
    candle_cache.reset()
    candle_cache.configure_db(conn)

    async def fetch(rng):
        return {"currency": "BRL", "candles": [_c("2026-05-01", 10)]}

    r = asyncio.run(candle_cache.load("ITUB4", fetch, now=1000.0))
    assert r["cacheStatus"] == "miss" and r["candles"]
    candle_cache.configure_db(None)
    candle_cache.reset()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE CACHE DE CANDLES PASSARAM")


# ---------------------------------------------------------------------------
# ADR-001 — janelas por intervalo e L2 só do diário (itens 5 e 7 do backlog)
# ---------------------------------------------------------------------------

def test_ranges_por_intervalo_respeitam_o_limite_real_do_yahoo():
    """Medido em 30/07/2026: `2y` com `5m` dá HTTP 422 e `1m` só vai até 7d.
    Pedir a janela do diário no intraday seria erro garantido."""
    assert cc.ranges_for("1d") == (cc.FULL_RANGE, cc.RECENT_RANGE)
    assert cc.ranges_for(None) == (cc.FULL_RANGE, cc.RECENT_RANGE)
    assert cc.ranges_for("1m") == ("7d", "1d")       # 1mo com 1m → 422
    assert cc.ranges_for("5m") == ("1mo", "1d")
    assert cc.ranges_for("15m") == ("1mo", "1d")
    assert cc.ranges_for("1h") == ("6mo", "5d")


def test_intraday_nao_persiste_no_l2():
    """ADR-001 (Decisão 4): persistir intraday custaria 1,65 GB/dia de
    reescrita (o blob inteiro é regravado a cada update) para poupar 0,45 s de
    reidratação. O diário continua com write-through."""
    conn = _fresh_l2()
    cc.reset()
    cc.configure_db(conn)
    try:
        assert cc.persiste_no_l2("1d") is True
        assert cc.persiste_no_l2("5m") is False
        assert cc.persiste_no_l2("1m") is False

        async def fetch(rng):
            return {"currency": "BRL", "candles": [_c(f"2026-05-30 1{i}:00", 10 + i) for i in range(5)]}

        asyncio.run(cc.load("PETR4", fetch, interval="5m", now=1000.0))
        # nada foi para o SQLite...
        assert cc._db_get("PETR4@5m") is None
        # ...e o "redeploy" refaz a série cheia, sem reidratar
        cc._CACHE.clear()
        janelas = []

        async def fetch2(rng):
            janelas.append(rng)
            return {"currency": "BRL", "candles": [_c("2026-05-30 10:00", 10)]}

        r = asyncio.run(cc.load("PETR4", fetch2, interval="5m", now=2000.0))
        assert r["cacheStatus"] == "miss"
        assert janelas == ["1mo"]        # janela CHEIA do 5m, não a do diário
    finally:
        cc.configure_db(None)
        cc.reset()


def test_diario_continua_persistindo():
    """Guardião de não-regressão: o L2 do diário é a razão de o módulo existir."""
    conn = _fresh_l2()
    cc.reset()
    cc.configure_db(conn)
    try:
        async def fetch(rng):
            return {"currency": "BRL", "candles": [_c(f"2026-05-{i:02d}", 10 + i) for i in range(1, 6)]}

        asyncio.run(cc.load("VALE3", fetch, now=1000.0))
        assert cc._db_get("VALE3@1d") is not None
    finally:
        cc.configure_db(None)
        cc.reset()


def test_merge_nao_colapsa_velas_intraday_do_mesmo_dia():
    """O bloqueador medido: com `date` sem horário, 617 velas de 15m viravam 22
    chaves. Com a chave completa, 26 velas do MESMO dia continuam 26."""
    dia = "2026-07-30"
    velas = [_c(f"{dia} {10 + i // 4:02d}:{(i % 4) * 15:02d}", 40 + i * 0.1) for i in range(26)]
    m = cc.merge_candles([], velas)
    assert len(m) == 26
    assert len({c["date"] for c in m}) == 26
    # ordenação cronológica pela string
    assert m[0]["date"] == f"{dia} 10:00" and m[-1]["date"] == f"{dia} 16:15"
    # revalidação da última vela continua funcionando na resolução de minuto
    m2 = cc.merge_candles(m, [_c(f"{dia} 16:15", 99)])
    assert len(m2) == 26 and m2[-1]["close"] == 99


# ---------------------------------------------------------------------------
# ADR-008 (Fase 4) — fonte da série no cache e acervo próprio de histórico
# ---------------------------------------------------------------------------
def test_load_registra_e_devolve_a_fonte():
    """`src` = fonte da última escrita. Miss grava a do warmup; delta atualiza
    para a fonte que serviu o recente (com a inversão: warmup yahoo → delta
    brapi). É o metadado que a didática declara — a IDENTIDADE do snapshot não
    muda com a fonte porque o dado diário é idêntico entre elas (validado ao
    vivo em 11/08/2026: 21 pregões de PETR4 com open/close/volume iguais)."""
    cc.reset()
    cc.configure_db(None, enabled=False)

    async def fetch_warmup(rng):
        return {"candles": [{"date": "2026-08-07", "open": 1, "high": 2,
                             "low": 1, "close": 2, "volume": 10}],
                "currency": "BRL", "source": "yahoo"}

    out = asyncio.run(cc.load("PETR4", fetch_warmup, now=1000.0))
    assert out["cacheStatus"] == "miss" and out["source"] == "yahoo"

    async def fetch_delta(rng):
        return {"candles": [{"date": "2026-08-10", "open": 2, "high": 3,
                             "low": 2, "close": 3, "volume": 20}],
                "currency": "BRL", "source": "brapi"}

    out = asyncio.run(cc.load("PETR4", fetch_delta, now=2000.0))
    assert out["cacheStatus"] == "delta" and out["source"] == "brapi"
    # o ACERVO acumula: warmup yahoo + delta brapi na mesma série (errata da
    # decisão 3 do ADR-008 — merge diário entre fontes é permitido)
    assert [c["date"] for c in out["candles"]] == ["2026-08-07", "2026-08-10"]

    # stale (delta falhou) preserva a fonte conhecida
    async def fetch_falha(rng):
        raise RuntimeError("fora do ar")
    out = asyncio.run(cc.load("PETR4", fetch_falha, now=3000.0))
    assert out["cacheStatus"] == "stale" and out["source"] == "brapi"


def test_fonte_sobrevive_ao_l2(tmp_path):
    """O acervo próprio (pedido do Alex, 11/08) mora no L2: série E fonte
    sobrevivem a restart/deploy, inclusive em banco criado ANTES da coluna
    `src` (migração idempotente do db.py)."""
    import sqlite3 as _sq
    from app import db as _db
    conn = _sq.connect(":memory:")
    _db.init_db(conn)   # schema oficial, com a migração da coluna src
    cc.reset()
    cc.configure_db(conn, enabled=True)

    async def fetch(rng):
        return {"candles": [{"date": "2026-08-10", "open": 1, "high": 2,
                             "low": 1, "close": 2, "volume": 10}],
                "currency": "BRL", "source": "brapi"}

    asyncio.run(cc.load("WEGE3", fetch, now=1000.0))
    cc.reset()                      # "restart": L1 esvazia
    async def fetch_nao_chamado(rng):
        raise AssertionError("delta antes da janela mínima não deve buscar")
    out = asyncio.run(cc.load("WEGE3", fetch_nao_chamado, now=1010.0))
    assert out["cacheStatus"] == "fresh" and out["source"] == "brapi"
    cc.configure_db(None, enabled=False)
