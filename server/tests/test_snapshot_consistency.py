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


# ---------------------------------------------------------------------------
# ADR-001 (Decisão 5) — o INTERVALO faz parte da identidade do snapshot.
# Sem isso, diário e intraday do mesmo ativo disputam a mesma entrada de cache
# e o snapshotId que amarra N1/N2/N3 não diz de qual timeframe veio a leitura.
# ---------------------------------------------------------------------------

def _mk_intraday(n=120):
    """Velas de 15m do MESMO dia — a chave carrega o horário (yahoo._candle_key)."""
    out = []
    for i in range(n):
        base = 40 + i * 0.05
        h, m = 10 + (i // 4), (i % 4) * 15
        out.append({"date": f"2026-07-30 {h % 24:02d}:{m:02d}",
                    "open": base, "high": base + 0.2, "low": base - 0.2,
                    "close": base + 0.05, "volume": 5000 + i})
    return out


def test_intervalo_entra_na_identidade_do_snapshot():
    _reset_caches()
    diario = technical_snapshot.build("TESTE3", _mk_candles(), "6mo")
    intra = technical_snapshot.build("TESTE3", _mk_intraday(), "6mo", interval="15m")
    assert diario["snapshotId"] != intra["snapshotId"], "ids não podem colidir entre timeframes"
    assert diario["interval"] == "1d" and intra["interval"] == "15m"


def test_intraday_nao_despeja_o_snapshot_diario_do_cache():
    """A colisão real: com a chave (ticker, período), pedir o intraday
    invalidava o snapshot diário e vice-versa, num vaivém a cada ciclo."""
    _reset_caches()
    cs = _mk_candles()
    d1 = technical_snapshot.build("TESTE3", cs, "6mo")
    technical_snapshot.build("TESTE3", _mk_intraday(), "6mo", interval="15m")
    d2 = technical_snapshot.build("TESTE3", list(cs), "6mo")
    assert d2 is d1, "o snapshot diário tem que continuar em cache, intocado"


def test_id_do_diario_nao_muda_com_a_entrada_do_parametro():
    """Compatibilidade: o snapshotId de tudo que já existe não pode mudar — ele
    aparece na UI e em análises gravadas. Por isso o intervalo só entra no hash
    quando NÃO é diário."""
    _reset_caches()
    cs = _mk_candles()
    explicito = technical_snapshot.build("TESTE3", cs, "6mo", interval="1d")
    _reset_caches()
    implicito = technical_snapshot.build("TESTE3", cs, "6mo")
    assert explicito["snapshotId"] == implicito["snapshotId"]


# ---------------------------------------------------------------------------
# ADR-001 (item 1b) — o STU intraday analisa só barras FECHADAS.
# A última vela da série é SEMPRE a em formação: `merge_candles` a revalida por
# contrato. Ler um gatilho nela é afirmar algo que ainda pode desocorrer.
# ---------------------------------------------------------------------------

def test_intraday_descarta_a_barra_em_formacao():
    _reset_caches()
    velas = _mk_intraday(120)
    snap = technical_snapshot.build("TESTE3", velas, "6mo", interval="15m")
    assert snap["asOf"] == velas[-2]["date"], "asOf tem que ser a última barra FECHADA"
    assert snap["barraEmFormacao"] == velas[-1]["date"]
    assert snap["candles"][-1]["date"] == velas[-2]["date"]
    # e o preço de referência é o da barra fechada, não o da que está mudando
    # (round: sanitize_candles normaliza em 2 casas)
    assert snap["close"] == round(velas[-2]["close"], 2)


def test_diario_nao_descarta_nada():
    """No diário a 'vela em formação' é o pregão do dia — descartá-la jogaria
    fora o dia inteiro, e o produto já é explícito sobre isso."""
    _reset_caches()
    cs = _mk_candles(120)
    snap = technical_snapshot.build("TESTE3", cs, "6mo")
    assert snap["asOf"] == cs[-1]["date"]
    assert snap["barraEmFormacao"] is None
    assert len(snap["candles"]) == min(len(cs), snap["periodBars"])


def test_gatilho_nao_muda_enquanto_a_barra_se_forma():
    """O ponto da regra: a MESMA barra em formação, com preços diferentes ao
    longo dos 15 minutos, não pode alterar a leitura. Só o fechamento dela —
    que vira a penúltima na leitura seguinte — pode."""
    _reset_caches()
    base = _mk_intraday(120)
    a = technical_snapshot.build("TESTE3", base, "6mo", interval="15m")

    # mesma série, mas a última vela (em formação) disparou 8%: é o cenário que
    # antes mudaria veredito e setups no meio da barra.
    mexida = [dict(c) for c in base]
    mexida[-1] = {**mexida[-1], "close": mexida[-1]["close"] * 1.08,
                  "high": mexida[-1]["high"] * 1.08}
    _reset_caches()
    b = technical_snapshot.build("TESTE3", mexida, "6mo", interval="15m")

    assert a["snapshotId"] == b["snapshotId"], "barra em formação não pode gerar snapshot novo"
    assert a["setups"]["veredito"] == b["setups"]["veredito"]
    assert a["scoreTecnico"] == b["scoreTecnico"]


def test_serie_curta_demais_nao_fica_sem_nada():
    """Descartar a última de uma série de 1 vela deixaria o STU sem insumo —
    melhor manter e deixar o dataQuality reclamar do tamanho."""
    _reset_caches()
    uma = _mk_intraday(1)
    snap = technical_snapshot.build("TESTE3", uma, "6mo", interval="15m")
    assert snap["asOf"] == uma[-1]["date"]
    assert snap["barraEmFormacao"] is None
