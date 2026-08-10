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


# ===== FASE 8B (B3) — cache do deep é por MODO =====
def test_cache_do_deep_nao_vaza_entre_modos():
    """A leitura da mesa (operador) e a do professor (estudo) são textos
    diferentes do MESMO snapshot — cache de um modo não pode servir o outro;
    e repetir no MESMO modo continua sem repagar."""
    scan_deep.reset()
    calls = []

    async def deep_call(item):
        calls.append(item["ticker"])
        return {"resumo": "ok"}

    payload = {"results": [{"ticker": "AAAA3", "confluencia": 90, "melhorSetup": "x",
                            "setups": [], "veredito": "Estudar alta",
                            "condicoes_detectadas": ["c"], "snapshotId": 42}]}
    asyncio.run(scan_deep.run_deep(payload, 1, "1y", deep_call, modo="estudo"))
    asyncio.run(scan_deep.run_deep(payload, 1, "1y", deep_call, modo="operador"))
    assert len(calls) == 2, "modo diferente deveria repagar (textos distintos)"
    r3 = asyncio.run(scan_deep.run_deep(payload, 1, "1y", deep_call, modo="operador"))
    assert len(calls) == 2 and r3["results"][0]["cache"] is True, "mesmo modo deveria usar o cache"
    # estimate respeita o modo na contagem
    est_est = scan_deep.estimate(payload, 1, "1y", modo="estudo")
    est_novo = scan_deep.estimate(payload, 1, "1y", modo=None)  # legado => estudo
    assert est_est["chamadas"] == 0 and est_novo["chamadas"] == 0  # estudo já pago; None normaliza p/ estudo
    scan_deep.reset()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DO SCAN DEEP PASSARAM")


# ---------------------------------------------------------------------------
# O cache do N1 é GLOBAL (sem user_id). Sem a identidade do LEITOR na chave,
# a leitura escrita para um perfil era servida a outro — e a resposta paga
# com a chave de IA de um usuário ia para outro (BYOK inclusive).
# ---------------------------------------------------------------------------

def test_leitor_fp_separa_perfis_e_modelos():
    from app import scan_deep as sd
    conservador = {"risco": "conservador", "toleranciaPerdaPct": 2, "experiencia": "iniciante"}
    arrojado = {"risco": "arrojado", "toleranciaPerdaPct": 9, "experiencia": "avancado"}
    cfg = {"provider": "anthropic", "model": "claude-haiku-4-5", "keySource": "env"}

    assert sd.leitor_fp(conservador, cfg) == sd.leitor_fp(dict(conservador), dict(cfg))
    assert sd.leitor_fp(conservador, cfg) != sd.leitor_fp(arrojado, cfg), \
        "perfil de risco entra no prompt: leituras diferentes não podem compartilhar cache"
    assert sd.leitor_fp(conservador, cfg) != sd.leitor_fp(conservador, {**cfg, "model": "gpt-4o"})
    assert sd.leitor_fp(conservador, cfg) != sd.leitor_fp(conservador, {**cfg, "keySource": "manual"}), \
        "BYOK e chave gerenciada não podem se servir da mesma resposta"


def test_cache_do_deep_nao_vaza_entre_leitores():
    from app import scan_deep as sd
    sd.reset()
    item = {"ticker": "PETR4", "snapshotId": "abc123", "confluencia": 100}
    a, b = sd.leitor_fp({"risco": "conservador"}, {"model": "m1"}), sd.leitor_fp({"risco": "arrojado"}, {"model": "m1"})
    assert sd._key(item, "1y", "estudo", a) != sd._key(item, "1y", "estudo", b)


def test_estimativa_usa_a_mesma_chave_da_execucao():
    """Se a estimativa e o run_deep divergirem, a UI promete 'já em cache' e o
    deep cobra a chamada mesmo assim."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert src.count("scan_deep.leitor_fp") == 2, "as DUAS rotas do N1 precisam da mesma identidade"
