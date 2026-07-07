"""FASE 1.4 — testes do aprofundamento IA do Radar (scan_deep, puro/injetado)."""
import asyncio

from app import scan_deep


def _scan_payload():
    return {"results": [
        {"ticker": "AAAA3", "confluencia": 90, "melhorSetup": "pullback", "setups": [], "veredito": "Estudar alta", "condicoes_detectadas": ["x"]},
        {"ticker": "BBBB4", "confluencia": 70, "melhorSetup": "rompimento", "setups": [], "veredito": "Monitorar", "condicoes_detectadas": ["y"]},
        {"ticker": "CCCC3", "confluencia": 50, "melhorSetup": None, "setups": [], "veredito": "Monitorar", "condicoes_detectadas": ["z"]},
        {"ticker": "DDDD3", "confluencia": 0, "melhorSetup": None, "setups": [], "veredito": "Sem setup no momento", "condicoes_detectadas": []},
    ]}


def test_resolve_top_n_prioridade_e_teto():
    assert scan_deep.resolve_top_n(None, None) == 5                       # default
    assert scan_deep.resolve_top_n(None, {"radarAiTopN": 3}) == 3          # config
    assert scan_deep.resolve_top_n(7, {"radarAiTopN": 3}) == 7             # pedido explícito vence
    assert scan_deep.resolve_top_n(99, None) == 10                         # teto
    assert scan_deep.resolve_top_n("abc", {"radarAiTopN": "x"}) == 5       # lixo -> default


def test_select_top_ignora_sem_setup():
    sel = scan_deep.select_top(_scan_payload(), 10)
    assert [r["ticker"] for r in sel] == ["AAAA3", "BBBB4", "CCCC3"]       # DDDD3 fora (nada a aprofundar)
    assert [r["ticker"] for r in scan_deep.select_top(_scan_payload(), 2)] == ["AAAA3", "BBBB4"]


def test_run_deep_cache_por_dia_e_nao_repaga():
    scan_deep.reset()
    calls = []

    async def deep_call(item):
        calls.append(item["ticker"])
        return {"resumo": "leitura", "planoEstudo": "Monitorar"}

    r1 = asyncio.run(scan_deep.run_deep(_scan_payload(), 2, "6mo", deep_call))
    assert r1["analisados"] == 2 and calls == ["AAAA3", "BBBB4"]
    assert all(x["cache"] is False for x in r1["results"])
    r2 = asyncio.run(scan_deep.run_deep(_scan_payload(), 2, "6mo", deep_call))
    assert calls == ["AAAA3", "BBBB4"]                                     # nenhuma chamada nova
    assert all(x["cache"] is True for x in r2["results"])
    # período diferente = cache separado
    asyncio.run(scan_deep.run_deep(_scan_payload(), 1, "1y", deep_call))
    assert calls == ["AAAA3", "BBBB4", "AAAA3"]


def test_estimate_reflete_cache():
    scan_deep.reset()
    est = scan_deep.estimate(_scan_payload(), 3, "6mo")
    assert est["chamadas"] == 3 and est["emCache"] == []

    async def deep_call(item):
        return {"resumo": "ok"}
    asyncio.run(scan_deep.run_deep(_scan_payload(), 2, "6mo", deep_call))
    est2 = scan_deep.estimate(_scan_payload(), 3, "6mo")
    assert est2["emCache"] == ["AAAA3", "BBBB4"] and est2["novasChamadasIA"] == ["CCCC3"] and est2["chamadas"] == 1


def test_erro_em_um_ativo_nao_derruba_o_deep():
    scan_deep.reset()

    async def deep_call(item):
        if item["ticker"] == "BBBB4":
            raise RuntimeError("provedor caiu")
        return {"resumo": "ok"}

    r = asyncio.run(scan_deep.run_deep(_scan_payload(), 3, "3mo", deep_call))
    assert r["analisados"] == 2
    assert [e["ticker"] for e in r["errors"]] == ["BBBB4"]
    assert "recomendação de investimento" in r["disclaimer"]
