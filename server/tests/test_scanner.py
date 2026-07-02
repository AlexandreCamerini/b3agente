"""BLOCO 3 — testes do Radar de mercado (scanner.py). Sem rede: o provedor é
um fake que gera séries sintéticas determinísticas.

Trava os contratos:
  • universo: default não-vazio/normalizado; override por env e por parâmetro,
    com dedupe e teto;
  • condições: rótulos educacionais corretos para séries engenheiradas
    (sobrecompra, máxima do período, cruzamentos) e GUARDRAIL — nenhum rótulo
    nem o disclaimer contém linguagem imperativa de operação;
  • varredura: ranking por score, símbolo quebrado cai em `errors` sem derrubar
    o resto, disclaimer sempre no payload, cache do resultado (TTL) e período
    do usuário mudando o recorte (nunca hardcoded).
"""
import asyncio
import re

try:
    import pytest  # Railway/dev: suíte normal do pytest
except ImportError:  # sandbox sem rede: o mini-runner do __main__ assume
    pytest = None

from app import candle_cache, scanner
from app import candles as candles_mod


# ------------------------------ helpers ------------------------------------

def _mk_candles(closes, start="2024-01-01"):
    """Série diária sintética a partir dos fechamentos (OHLC coerente)."""
    out = []
    from datetime import date, timedelta
    d0 = date.fromisoformat(start)
    for i, c in enumerate(closes):
        d = d0 + timedelta(days=i)
        out.append({
            "date": d.isoformat(),
            "open": round(c * 0.995, 2), "high": round(c * 1.01, 2),
            "low": round(c * 0.99, 2), "close": round(c, 2), "volume": 1000 + i,
        })
    return out


def _uptrend(n=120, base=10.0, step=0.15):
    return [base + i * step for i in range(n)]


def _flat_then_spike(n=120, base=50.0):
    closes = [base + (0.05 if i % 2 else -0.05) for i in range(n - 10)]
    closes += [base * (1 + 0.02 * (i + 1)) for i in range(10)]  # estirão final
    return closes


IMPERATIVE = re.compile(r"\b(compre|venda|entre agora|compra já|venda já)\b", re.I)


# ------------------------------ universo ------------------------------------

def test_universe_default_normalizado():
    uni = scanner.get_universe()
    assert len(uni) > 0
    assert len(uni) == len(set(uni))                     # sem duplicados
    assert all(t == t.upper() and ".SA" not in t for t in uni)
    assert "PETR4" in uni and "VALE3" in uni


def test_universe_override_por_parametro_dedupe_e_teto():
    uni = scanner.get_universe("petr4, vale3 ,PETR4.SA, xx")  # dup + lixo curto
    assert uni == ["PETR4", "VALE3"]
    muitos = ",".join("TST" + str(i) + "3" for i in range(300))
    assert len(scanner.get_universe(muitos)) <= scanner.MAX_UNIVERSE


def test_universe_override_por_env():
    import os
    prev = os.environ.get("B3_SCAN_UNIVERSE")
    try:
        os.environ["B3_SCAN_UNIVERSE"] = "itub4,bbas3"
        assert scanner.get_universe() == ["ITUB4", "BBAS3"]
        os.environ["B3_SCAN_UNIVERSE"] = "   "
        assert scanner.get_universe() == list(scanner.DEFAULT_UNIVERSE)  # env vazia => default
    finally:
        if prev is None:
            os.environ.pop("B3_SCAN_UNIVERSE", None)
        else:
            os.environ["B3_SCAN_UNIVERSE"] = prev


# --------------------------- condições/guardrail ----------------------------

def _conditions_for(closes, period="1y"):
    from app import indicators
    cs = indicators.sanitize_candles(_mk_candles(closes))
    full = indicators.compute(cs)
    keep = min(len(cs), candles_mod.resolve_keep(period))
    sl = indicators.slice_tail(cs, full["indicators"], full["summary"], keep)
    return scanner.detect_conditions(sl["candles"], sl["indicators"], full["summary"])


def test_condicoes_uptrend_detecta_maxima_e_tendencia():
    conds, score = _conditions_for(_uptrend())
    joined = " | ".join(conds)
    assert "máxima do período" in joined
    assert "SMA20 acima da SMA50" in joined
    assert 0 < score <= 100


def test_condicoes_sao_educacionais_sem_imperativo():
    for closes in (_uptrend(), _flat_then_spike(), list(reversed(_uptrend()))):
        conds, _ = _conditions_for(closes)
        for c in conds:
            assert not IMPERATIVE.search(c), c
    assert not IMPERATIVE.search(scanner.DISCLAIMER)


def test_score_e_intensidade_nao_direcao():
    # série de queda também pontua (condições de baixa contam igual): o score
    # NÃO é "quão bom para comprar".
    conds_down, score_down = _conditions_for(list(reversed(_uptrend())))
    assert score_down > 0
    assert any("mínima do período" in c for c in conds_down)


# ------------------------------- varredura ----------------------------------

SERIES = {
    "AAAA3": _uptrend(),                 # muitas condições
    "BBBB3": [30.0 + (0.01 if i % 2 else -0.01) for i in range(120)],  # lateral
    "CCCC3": None,                        # provedor falha
}


def _fake_fetch(symbol, rng):
    async def go():
        closes = SERIES.get(symbol)
        if closes is None:
            raise RuntimeError("simulated provider failure")
        return {"candles": _mk_candles(closes), "currency": "BRL"}
    return go()


def _run(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


def _reset_caches():
    candle_cache.reset()
    scanner.reset()


if pytest is not None:
    @pytest.fixture(autouse=True)
    def _clean_caches():
        _reset_caches()
        yield
        _reset_caches()


def test_scan_rankeia_tolera_falha_e_tem_disclaimer():
    payload = _run(scanner.run_scan(period="1y", universe="AAAA3,BBBB3,CCCC3", fetch=_fake_fetch))
    assert payload["disclaimer"] == scanner.DISCLAIMER
    assert payload["universeSize"] == 3 and payload["scanned"] == 2
    assert [e["ticker"] for e in payload["errors"]] == ["CCCC3"]
    scores = [r["score_tecnico"] for r in payload["results"]]
    assert scores == sorted(scores, reverse=True)         # rankeado
    assert payload["results"][0]["ticker"] == "AAAA3"     # uptrend pontua mais
    for r in payload["results"]:
        assert "condicoes_detectadas" in r and "timestamp" not in r  # timestamp é do payload
    assert payload["timestamp"]


def test_scan_respeita_periodo_do_usuario():
    p1 = _run(scanner.run_scan(period="1mo", universe="AAAA3", fetch=_fake_fetch))
    scanner.reset()  # isola o cache de RESULTADO (o de candles pode ficar)
    p2 = _run(scanner.run_scan(period="2y", universe="AAAA3", fetch=_fake_fetch))
    assert p1["periodBars"] == candles_mod.resolve_keep("1mo")
    assert p2["periodBars"] == candles_mod.resolve_keep("2y")
    r1, r2 = p1["results"][0], p2["results"][0]
    assert r1["candles"] < r2["candles"]                  # recorte muda com o período
    assert r1["variacaoPeriodoPct"] != r2["variacaoPeriodoPct"]


def test_scan_cache_ttl_evita_refazer():
    p1 = _run(scanner.run_scan(period="1y", universe="AAAA3,BBBB3", fetch=_fake_fetch))
    p2 = _run(scanner.run_scan(period="1y", universe="AAAA3,BBBB3", fetch=_fake_fetch))
    assert p2 is p1                                        # mesmo objeto: veio do cache


def test_periodo_invalido_normaliza_para_default():
    payload = _run(scanner.run_scan(period="banana", universe="AAAA3", fetch=_fake_fetch))
    assert payload["period"] == candles_mod.DEFAULT_PERIOD


# ---------------------------------------------------------------------------
# Mini-runner para ambientes SEM pytest (ex.: sandbox offline). No Railway/dev
# a suíte roda normalmente pelo pytest; aqui, `python3 tests/test_scanner.py`.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    fails = 0
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        _reset_caches()
        try:
            fn()
            print("ok " + name)
        except AssertionError as e:
            fails += 1
            print("FALHOU " + name + " :: " + str(e))
        except Exception as e:  # noqa: BLE001
            fails += 1
            print("ERRO " + name + " :: " + repr(e))
        finally:
            _reset_caches()
    print()
    print("TODOS OS TESTES DO SCANNER PASSARAM" if fails == 0 else str(fails) + " TESTE(S) FALHARAM")
    sys.exit(0 if fails == 0 else 1)
