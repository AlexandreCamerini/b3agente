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

    def fake_merged(t):
        calls.append(t)
        return fu.parse_brapi(PAYLOAD_PETR4)

    f1 = fu.get_fundamentals(conn, "PETR4", fetch_merged=fake_merged)
    assert f1["score"] == "A" and len(calls) == 1
    # cache quente: segunda chamada NÃO vai à fonte
    f2 = fu.get_fundamentals(conn, "PETR4", fetch_merged=fake_merged)
    assert len(calls) == 1 and f2["ticker"] == "PETR4"
    # cache frio (>= TTL): refaz o fetch
    depois = datetime.now(timezone.utc) + timedelta(days=fu.TTL_DIAS + 1)
    fu.get_fundamentals(conn, "PETR4", fetch_merged=fake_merged, now=depois)
    assert len(calls) == 2
    conn.close()


def test_get_fundamentals_fonte_fora_usa_cache_velho():
    conn = _fresh_db()
    fu.get_fundamentals(conn, "PETR4", fetch_merged=lambda t: fu.parse_brapi(PAYLOAD_PETR4))

    def boom(t):
        raise RuntimeError("fonte fora do ar")

    depois = datetime.now(timezone.utc) + timedelta(days=fu.TTL_DIAS + 1)
    f = fu.get_fundamentals(conn, "PETR4", fetch_merged=boom, now=depois)
    assert f is not None and f["ticker"] == "PETR4"  # degrada pro cache, nunca inventa
    # ticker nunca visto + fonte fora → None (sem dado)
    assert fu.get_fundamentals(conn, "WEGE3", fetch_merged=boom) is None
    conn.close()


# ===== qa/36 (F10.2): bolsai primária + merge + rebaixamento + warm =====

# Fixture do formato DOCUMENTADO da bolsai (GET /fundamentals/{ticker}).
PAYLOAD_BOLSAI = {"data": {
    "ticker": "WEGE3", "sector": "Bens Industriais", "reference_date": "2026-03-31",
    "pl": 18.4, "pvp": 5.2, "roe": 0.31, "net_margin": 0.17,
    "net_debt_ebitda": -0.3, "cagr_revenue_5y": 0.19, "cagr_earnings_5y": 0.21,
    # DY não vem no free da bolsai:
    "dividend_yield": None,
}}


def test_parse_bolsai_formato_documentado():
    f = fu.parse_bolsai(PAYLOAD_BOLSAI)
    assert f["ticker"] == "WEGE3" and f["fonte"] == "bolsai"
    assert f["pl"] == 18.4 and f["roe"] == 0.31
    assert f["dividaEbitda"] == -0.3      # net_debt_ebitda direto, sem conta
    assert f["dy"] is None                # free não traz DY
    assert fu.parse_bolsai({}) is None
    assert fu.score_fundamento(f) == "A"  # P/L<20 ok + ROE/margem ok + dívida<3 ok


def test_merge_completa_dy_da_brapi_sem_sobrescrever():
    prim = fu.parse_bolsai(PAYLOAD_BOLSAI)             # dy=None
    comp = {"dy": 0.055, "pl": 99.9, "roe": 0.01, "ticker": "WEGE3", "fonte": "brapi"}
    m = fu.merge_fundamentos(prim, comp)
    assert m["dy"] == 0.055                # lacuna preenchida
    assert m["pl"] == 18.4                 # primário MANDA (não sobrescreve)
    assert m["fonte"] == "bolsai+brapi"
    # primário ausente → devolve o complemento inteiro
    assert fu.merge_fundamentos(None, comp) is comp
    assert fu.merge_fundamentos(prim, None) is prim


def test_rebaixa_confianca_so_desce_nunca_promove():
    # decisão operável + score C → desce 1 degrau
    assert fu.rebaixa_confianca("alta", "C", True) == ("moderada", True)
    assert fu.rebaixa_confianca("moderada", "C", True) == ("baixa", True)
    assert fu.rebaixa_confianca("baixa", "C", True) == ("baixa", False)   # não desce mais
    # score B/A: sem efeito (A NUNCA promove)
    assert fu.rebaixa_confianca("moderada", "B", True) == ("moderada", False)
    assert fu.rebaixa_confianca("moderada", "A", True) == ("moderada", False)
    # decisão não operável: fundamento não mexe
    assert fu.rebaixa_confianca("alta", "C", False) == ("alta", False)
    # sem confiança/score: no-op
    assert fu.rebaixa_confianca(None, "C", True) == (None, False)


def test_get_fundamentals_bolsai_primaria_brapi_complemento():
    conn = _fresh_db()

    def fetch_merged(t):
        return fu._fetch_merged(
            t, bolsai_key="fake",
            fetch_bolsai=lambda tk, key: PAYLOAD_BOLSAI,
            fetch_brapi=lambda tk, tok: {"results": [{"symbol": "WEGE3",
                "defaultKeyStatistics": {"dividendYield": 0.055}}]},
        )

    f = fu.get_fundamentals(conn, "WEGE3", fetch_merged=fetch_merged)
    assert f["fonte"] == "bolsai+brapi"
    assert f["pl"] == 18.4 and f["dy"] == 0.055
    conn.close()


def test_warm_universe_pula_fresco_e_aquece_vencido():
    conn = _fresh_db()
    calls = []

    def fake_merged(t):
        calls.append(t)
        return {"ticker": t, "pl": 10.0, "roe": 0.15, "margemLiquida": 0.1,
                "dividaEbitda": 1.0, "fonte": "bolsai"}

    n = fu.warm_universe(conn, ["PETR4", "VALE3"], fetch_merged=fake_merged)
    assert n == 2 and sorted(calls) == ["PETR4", "VALE3"]
    # 2ª passada no mesmo dia: cache fresco → não rebusca
    calls.clear()
    n2 = fu.warm_universe(conn, ["PETR4", "VALE3"], fetch_merged=fake_merged)
    assert n2 == 0 and calls == []
    conn.close()


def test_get_cached_nunca_vai_a_rede():
    conn = _fresh_db()
    assert fu.get_cached(conn, "PETR4") is None       # nada ainda
    fu.get_fundamentals(conn, "PETR4", fetch_merged=lambda t: fu.parse_brapi(PAYLOAD_PETR4))
    c = fu.get_cached(conn, "PETR4")
    assert c and c["ticker"] == "PETR4" and c["score"] == "A"
    conn.close()


def test_integracao_esta_ligada_no_backend():
    """qa/36: o oposto do guardião do spike — agora fundamentals DEVE estar
    integrado: scan enriquecido (main.py), warm no scheduler (agent.py)."""
    import pathlib
    app_dir = pathlib.Path(__file__).resolve().parents[1] / "app"
    main_src = (app_dir / "main.py").read_text(encoding="utf-8")
    assert "_enrich_fundamentos" in main_src, "scan não enriquece com fundamento"
    assert "fundamentals.get_cached" in main_src, "scan deve ler SÓ o cache (get_cached)"
    assert "fundamentals.get_fundamentals(_conn, t)" in main_src, "N2 deve buscar fundamento inline"
    assert "rebaixa_confianca" in main_src, "N2 deve aplicar o rebaixamento"
    agent_src = (app_dir / "agent.py").read_text(encoding="utf-8")
    assert "fundamentals.maybe_warm" in agent_src, "warm job não está no scheduler"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE FUNDAMENTALS PASSARAM")
