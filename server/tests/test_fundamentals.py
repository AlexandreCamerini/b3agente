"""qa/35 (P3 — spike) — fundamentals.py: parse, score A/B/C e cache.

Tudo SEM rede: parse com fixture do payload real da brapi (capturado no
spike de 10/07/2026, PETR4), fetch injetado no teste de cache. A prova de
rede ao vivo foi feita uma vez na rodada do spike (registrada no qa/35);
o guardião não depende de fonte externa.
"""
import sqlite3
from datetime import datetime, timedelta, timezone

from app import fundamentals as fu
from app import db


def _fresh_db():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("SELECT 1 FROM kv LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT)")
    return conn


# Fixture reduzida do payload REAL da brapi (PETR4, 10/07/2026).
PAYLOAD_PETR4 = {"results": [{
    "symbol": "PETR4", "priceEarnings": 4.750152747660865,
    "summaryProfile": {"sector": "Energy"},
    "defaultKeyStatistics": {"trailingPE": 5.215, "priceToBook": 1.135, "dividendYield": 0.06},
    "financialData": {"returnOnEquity": 0.24267222, "profitMargins": 0.21689811,
                       "totalDebt": 676977000000.0, "ebitda": 230884000000.0,
                       "revenueGrowthAnnual": 0.01369, "earningsGrowthAnnual": 2.0085},
}]}

# Banco (ITUB4): sem totalDebt/ebitda — dívida/EBITDA deve virar None (sem dado).
PAYLOAD_BANCO = {"results": [{
    "symbol": "ITUB4", "priceEarnings": 11.16,
    "summaryProfile": {"sector": "Financial Services"},
    "defaultKeyStatistics": {"dividendYield": 0.08},
    "financialData": {"returnOnEquity": 0.2242, "profitMargins": 0.1209,
                       "totalDebt": None, "ebitda": None},
}]}


def test_parse_brapi_extrai_metricas_do_payload_real():
    f = fu.parse_brapi(PAYLOAD_PETR4)
    assert f["ticker"] == "PETR4"
    assert f["pl"] == 4.750152747660865
    assert f["roe"] == 0.24267222
    assert f["dy"] == 0.06
    assert f["margemLiquida"] == 0.21689811
    assert f["dividaEbitda"] == 2.93          # 676977/230884 arredondado
    assert f["crescReceita"] == 0.01369        # prioriza o anual
    assert f["fonte"] == "brapi"


def test_parse_brapi_banco_sem_divida_ebitda_vira_none():
    f = fu.parse_brapi(PAYLOAD_BANCO)
    assert f["dividaEbitda"] is None           # sem dado ≠ zero — nunca inventa
    assert f["roe"] == 0.2242


def test_parse_brapi_payload_vazio():
    assert fu.parse_brapi({}) is None
    assert fu.parse_brapi({"results": []}) is None


def test_score_fundamento_pilares():
    # PETR4 real: P/L 4.7 ok + ROE 24%/margem ok + dívida 2.93 ok → A
    assert fu.score_fundamento(fu.parse_brapi(PAYLOAD_PETR4)) == "A"
    # banco: 2 pilares com dado (valuation ok + rentabilidade ok), solidez neutra → A
    assert fu.score_fundamento(fu.parse_brapi(PAYLOAD_BANCO)) == "A"
    # 1 pilar ok de 3 → B; 0 → C
    assert fu.score_fundamento({"pl": 10.0, "roe": 0.02, "margemLiquida": 0.001, "dividaEbitda": 5.0}) == "B"
    assert fu.score_fundamento({"pl": 45.0, "roe": 0.01, "margemLiquida": -0.02, "dividaEbitda": 6.0}) == "C"
    # sem NENHUM dado → sem score (nunca chute)
    assert fu.score_fundamento({"pl": None, "roe": None, "margemLiquida": None, "dividaEbitda": None}) is None
    assert fu.score_fundamento(None) is None


def test_get_fundamentals_cacheia_e_respeita_ttl():
    conn = _fresh_db()
    calls = []

    def fake_fetch(t, tok):
        calls.append(t)
        return PAYLOAD_PETR4

    f1 = fu.get_fundamentals(conn, "PETR4", fetch_raw=fake_fetch)
    assert f1["score"] == "A" and len(calls) == 1
    # cache quente: segunda chamada NÃO vai à fonte
    f2 = fu.get_fundamentals(conn, "PETR4", fetch_raw=fake_fetch)
    assert len(calls) == 1 and f2["ticker"] == "PETR4"
    # cache frio (>= TTL): refaz o fetch
    depois = datetime.now(timezone.utc) + timedelta(days=fu.TTL_DIAS + 1)
    fu.get_fundamentals(conn, "PETR4", fetch_raw=fake_fetch, now=depois)
    assert len(calls) == 2
    conn.close()


def test_get_fundamentals_fonte_fora_usa_cache_velho():
    conn = _fresh_db()
    fu.get_fundamentals(conn, "PETR4", fetch_raw=lambda t, tok: PAYLOAD_PETR4)

    def boom(t, tok):
        raise RuntimeError("fonte fora do ar")

    depois = datetime.now(timezone.utc) + timedelta(days=fu.TTL_DIAS + 1)
    f = fu.get_fundamentals(conn, "PETR4", fetch_raw=boom, now=depois)
    assert f is not None and f["ticker"] == "PETR4"  # degrada pro cache, nunca inventa
    # ticker nunca visto + fonte fora → None (sem dado)
    assert fu.get_fundamentals(conn, "WEGE3", fetch_raw=boom) is None
    conn.close()


def test_spike_nao_esta_integrado():
    """Gate do Alex: fundamentals NÃO pode estar ligado em scanner/llm/telas
    antes do OK no mock (integração é F10.2)."""
    import pathlib
    app_dir = pathlib.Path(__file__).resolve().parents[1] / "app"
    for nome in ("scanner.py", "llm.py", "scan_deep.py", "setups.py"):
        src = (app_dir / nome).read_text(encoding="utf-8")
        assert "fundamentals" not in src, f"{nome} importou fundamentals antes do gate!"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE FUNDAMENTALS PASSARAM")
