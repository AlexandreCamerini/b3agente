"""Guardião da recalibração de `liquidity_score` para fonte SEM open interest
(quick 260908-dnl, 2026-09-08).

Contexto: com `B3_OPTIONS_PROVIDER=mydata` o COTAHIST não publica open
interest, e a fórmula anterior perdia o `oi_score` inteiro (até 40 pontos) —
teto de 35 contra corte de 40, impossível em qualquer volume. Medido em
produção: os 60 contratos de PETR4 empatavam em 35,0, o melhor com 88.100
unidades negociadas (`docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md`).

Os critérios sintéticos abaixo foram fixados ANTES de olhar as 20 cadeias
reais do catálogo, de propósito: a primeira candidata de fórmula passou em
PETR4/VALE3 e era um pass-through (volume 100 sem livro passava a 51,1). Este
arquivo existe para que a próxima recalibração não repita isso.

As linhas "reais" são contratos congelados da cadeia de produção de
2026-09-08 — volume, bid e ask como o mydata os entregou.
"""
from app.options_quant import liquidity_score

CORTE = 40  # `options_api.liquidity_gate` e `opcoes_motor.LIQUIDEZ_MINIMA`


def _s(volume, oi=None, bid=None, ask=None):
    return liquidity_score(volume, oi, bid, ask)["score"]


# ── o defeito medido: volume alto sem open interest tem que passar ──────────

def test_contrato_real_petr4_88100_sem_livro_passa():
    # PETRI478W2 — 88.100 unidades, bid/ask zerados, OI sem fonte. Antes: 35,0.
    assert _s(88100, None, 0.0, 0.0) >= CORTE


def test_contrato_real_petr4_49300_um_lado_do_livro_passa():
    # PETRU493W2 — livro com um lado só (bid 1.34, ask 0.0): spread desconhecido.
    assert _s(49300, None, 1.34, 0.0) >= CORTE


def test_guardiao_mydata_5000_spread_5pct_passa_com_folga():
    # Mesmo caso do guardião em test_options_provider_mydata.py — era 52,0.
    assert _s(5000, None, 1.80, 1.90) >= CORTE + 20


# ── continua sendo GATE: os critérios que a primeira candidata falhou ───────

def test_um_lote_sem_livro_reprova():
    # 592/592 volumes reais são múltiplos de 100; 100 = negociou UMA vez.
    assert _s(100) < CORTE


def test_contrato_real_abev3_100_livro_vazio_reprova():
    # ABEVU147W2 — passava a 51,1 na primeira candidata (descartada).
    assert _s(100, None, 0.0, 0.04) < CORTE


def test_volume_500_com_um_lado_zerado_reprova():
    # O critério nomeado antes de olhar os dados.
    assert _s(500, None, 0.0, 0.30) < CORTE
    assert _s(500) < CORTE


def test_spread_medido_ruim_reprova_mesmo_com_volume():
    # PETRU441W2 real: 300 unidades, bid 0.03 / ask 0.06 (spread 66%).
    assert _s(300, None, 0.03, 0.06) < CORTE
    # PETRI556 real (PETR3): 300 unidades, bid 0.19 / ask 1.25 (spread 147%).
    assert _s(300, None, 0.19, 1.25) < CORTE


def test_sem_mercado_nenhum_reprova():
    assert _s(0, 0, 0, 0) < CORTE


# ── a fronteira é DELIBERADA, não acidente de arredondamento ───────────────

def test_piso_sem_livro_e_mil_unidades():
    """1.000 = onde a curva de volume ORIGINAL saturava — o autor original
    considerava esse volume "cheio". Número derivado, não tunado. O fixture
    padrão dos testes de opções (`volume=1000, oi=1000`, sem livro) cai
    exatamente aqui; este teste torna isso intencional."""
    assert _s(1000) >= CORTE
    assert _s(900) < CORTE


# ── open interest, quando a fonte publica, SUBSTITUI o volume ───────────────

def test_open_interest_substitui_volume_quando_existe():
    # Caminho Yahoo (rollback): volume zero hoje mas 50.000 em aberto.
    assert _s(0, 50000, 1.00, 1.02) >= CORTE
    # ...e não SOMA: OI igual ao volume não muda a nota.
    assert _s(5000, 5000) == _s(5000, None)


def test_open_interest_nunca_reduz_a_nota():
    assert _s(5000, 0) == _s(5000, None)
    assert _s(5000, 100) == _s(5000, None)


# ── propriedades que a fórmula anterior já tinha e não podem regredir ──────

def test_monotonico_em_volume():
    valores = [_s(v) for v in (0, 10, 100, 500, 1000, 5000, 20000, 100000)]
    assert valores == sorted(valores)


def test_livro_apertado_vale_mais_que_livro_desconhecido():
    assert _s(5000, None, 1.00, 1.02) > _s(5000)


def test_livro_desconhecido_nao_e_pior_que_spread_medido_pessimo():
    # "não sei" ≥ "sei que é péssimo": a penalidade de desconhecido (25) é
    # menor que a de spread > 18% (30). Sem isto, ter dado pioraria a nota.
    assert _s(5000) >= _s(5000, None, 1.00, 1.35)


def test_teto_e_100_e_spread_pct_continua_reportado():
    r = liquidity_score(10**7, 10**7, 1.00, 1.01)
    assert r["score"] <= 100
    assert r["spreadPct"] is not None
    assert liquidity_score(5000, None, None, None)["spreadPct"] is None
