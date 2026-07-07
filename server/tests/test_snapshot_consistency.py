"""FASE 1 — ACEITE: Snapshot Técnico Único (technical_snapshot.py).

O contrato central: N1 (Radar) e N2 (análise completa) gerados do MESMO STU
nunca podem ter direção/score conflitantes — e o snapshotId prova para o
usuário que ambos leram os mesmos dados.

Testa (tudo determinístico, sem rede/LLM):
  • determinismo: mesmo insumo ⇒ mesmo snapshot, mesmo id (cache por
    fingerprint); insumo novo ⇒ id novo;
  • N1×N2: o item do scan e o contexto do N2 saem do MESMO snapshot —
    veredito, confluência, melhor setup e id idênticos;
  • N3: o contexto de risco carrega o mesmo snapshotId;
  • janela: períodos diferentes geram snapshots (ids) distintos.
"""
import asyncio

from app import candle_cache, scanner, technical_snapshot


def _run(coro):
    return asyncio.run(coro)


def _reset_caches():
    candle_cache.reset()
    scanner.reset()
    technical_snapshot.reset()
    scanner.SCAN_PROGRESS.update(ativo=False, fase="", atual="", feitos=0, total=0)


def _mk_candles(n=120, up=True, last_close=None):
    out = []
    for i in range(n):
        base = 10 + (i * 0.08 if up else -i * 0.04)
        out.append({"date": f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}",
                    "open": base, "high": base + 0.4, "low": base - 0.3,
                    "close": base + 0.1, "volume": 1000 + i})
    if last_close is not None:
        out[-1]["close"] = last_close
        out[-1]["high"] = max(out[-1]["high"], last_close + 0.1)
        out[-1]["low"] = min(out[-1]["low"], last_close - 0.1)
    return out


async def _fake_fetch(symbol, rng=None):
    return {"candles": _mk_candles(), "currency": "BRL"}


# ------------------------------ determinismo --------------------------------

def test_mesmo_insumo_mesmo_snapshot_id():
    cs = _mk_candles()
    a = technical_snapshot.build("TESTE3", cs, "6mo")
    b = technical_snapshot.build("TESTE3", list(cs), "6mo")
    assert a["snapshotId"] == b["snapshotId"]
    assert a is b  # cache por fingerprint: não recalcula sem necessidade


def test_insumo_novo_gera_id_novo():
    a = technical_snapshot.build("TESTE3", _mk_candles(), "6mo")
    b = technical_snapshot.build("TESTE3", _mk_candles(last_close=25.0), "6mo")
    assert a["snapshotId"] != b["snapshotId"]


def test_periodos_diferentes_ids_diferentes():
    cs = _mk_candles()
    a = technical_snapshot.build("TESTE3", cs, "3mo")
    b = technical_snapshot.build("TESTE3", cs, "1y")
    assert a["snapshotId"] != b["snapshotId"]
    assert a["periodBars"] != b["periodBars"]


def test_sem_historico_levanta_erro_claro():
    try:
        technical_snapshot.build("VAZIO3", [], "6mo")
        assert False, "deveria levantar ValueError"
    except ValueError as e:
        assert "sem histórico" in str(e)


# ------------------------------ ACEITE N1 × N2 ------------------------------

def test_n1_e_n2_leem_o_mesmo_snapshot_sem_conflito():
    """O item do Radar (N1) e o contexto do N2 derivam do MESMO STU:
    id, veredito, confluência e melhor setup são IDÊNTICOS por construção."""
    payload = _run(scanner.run_scan(period="6mo", universe="TESTE3", fetch=_fake_fetch))
    assert payload["results"], payload.get("errors")
    n1 = payload["results"][0]

    snap = _run(technical_snapshot.get("TESTE3", "6mo", lambda rng: _fake_fetch("TESTE3", rng)))
    # mesmo id — o usuário vê "#abc123" nas duas telas e sabe que é o mesmo dado
    assert n1["snapshotId"] == snap["snapshotId"]
    # direção/score NUNCA conflitam
    assert n1["veredito"] == snap["setups"]["veredito"]
    assert n1["confluencia"] == snap["setups"]["confluencia"]
    assert n1["melhorSetup"] == snap["setups"]["melhor"]
    assert n1["score_tecnico"] == snap["scoreTecnico"]
    # o contexto que o N2 manda para a LLM carrega os MESMOS setups do Radar
    sr = snap["context"]["setupsRadar"]
    assert sr["veredito"] == n1["veredito"]
    assert sr["confluencia"] == n1["confluencia"]
    assert snap["context"]["snapshotId"] == n1["snapshotId"]


def test_n3_carrega_o_mesmo_snapshot_id():
    snap = _run(technical_snapshot.get("TESTE3", "6mo", lambda rng: _fake_fetch("TESTE3", rng)))
    ctx = snap["context"]
    assert ctx["snapshotId"] == snap["snapshotId"]
    # blocos que o N3 consome existem e vêm do mesmo objeto
    assert ctx.get("volatility") and ctx.get("levels") and ctx.get("riskPlanReference")


def test_snapshot_estavel_entre_scan_repetido():
    p1 = _run(scanner.run_scan(period="6mo", universe="TESTE3", fetch=_fake_fetch))
    scanner.reset()  # força novo scan; candles não mudaram
    p2 = _run(scanner.run_scan(period="6mo", universe="TESTE3", fetch=_fake_fetch))
    assert p1["results"][0]["snapshotId"] == p2["results"][0]["snapshotId"]


def test_setups_do_snapshot_incluem_campos_operacionais():
    snap = technical_snapshot.build("TESTE3", _mk_candles(), "6mo")
    compact = snap["context"]["setupsRadar"]["setups"]
    for s in compact:
        assert "nome" in s and "confluencia" in s  # gatilho/invalidacao quando existirem


# ---------------------------------------------------------------------------
# Mini-runner para ambientes SEM pytest (padrão do projeto).
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
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
    print("TODOS OS TESTES DE CONSISTÊNCIA DO SNAPSHOT PASSARAM" if fails == 0 else str(fails) + " TESTE(S) FALHARAM")
    sys.exit(0 if fails == 0 else 1)
