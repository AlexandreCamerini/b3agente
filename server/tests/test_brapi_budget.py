"""ADR-008, Fase 2 (qa/43) — orçamento de requisições da brapi.

O que estes testes protegem:
  • a cota de 15.000/mês é finita e recusa DEBITA cota — o controle é local e
    ANTES da chamada, então o contador tem que ser confiável;
  • consumo só na janela de pregão (seg–sex 10:00–17:15 BRT);
  • fatia estourada consome da reserva; reserva esgotada bloqueia a fatia;
  • SOFT STOP a 80% (degradado → TTL alonga) e HARD STOP no teto do dia;
  • o contador sobrevive a restart (persistência no kv do SQLite);
  • o teto acompanha B3_BRAPI_COTA_MES sem deploy.
Offline: relógio injetado; SQLite em memória.
"""
import sqlite3
from datetime import datetime

import pytest

from app import brapi_budget as bb

TER_11H = datetime(2026, 8, 11, 11, 0, tzinfo=bb.BRT)    # terça, pregão aberto
TER_17H10 = datetime(2026, 8, 11, 17, 10, tzinfo=bb.BRT)  # janela do delta
TER_18H = datetime(2026, 8, 11, 18, 0, tzinfo=bb.BRT)     # pós-janela
SAB_11H = datetime(2026, 8, 15, 11, 0, tzinfo=bb.BRT)     # sábado


@pytest.fixture(autouse=True)
def _limpo(monkeypatch):
    bb.reset()
    bb.configure_db(None, enabled=False)
    monkeypatch.delenv("B3_BRAPI_COTA_MES", raising=False)
    yield
    bb.reset()
    bb.configure_db(None, enabled=False)


def test_teto_e_fatias_derivam_da_cota():
    assert bb.teto_dia() == 15000 // 21 == 714
    assert bb.fatia_limite("spot") == int(714 * 400 / 700) == 408
    assert bb.fatia_limite("delta") == int(714 * 150 / 700) == 153
    soma = sum(bb.fatia_limite(f) for f in ("spot", "delta", "fund"))
    assert bb._reserva_limite() == 714 - soma > 0


def test_cota_ajustavel_por_env_sem_deploy(monkeypatch):
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "2100")
    assert bb.teto_dia() == 100
    assert bb.fatia_limite("spot") == int(100 * 400 / 700)


def test_janela_de_pregao():
    assert bb.em_pregao(TER_11H) is True
    assert bb.em_pregao(TER_17H10) is True       # delta pós-fechamento cabe
    assert bb.em_pregao(TER_18H) is False
    assert bb.em_pregao(SAB_11H) is False


def test_fora_da_janela_nao_gasta():
    assert bb.pode_gastar("spot", now=TER_18H) is False
    assert bb.pode_gastar("spot", now=SAB_11H) is False
    assert bb.pode_gastar("spot", now=TER_11H) is True


def test_fatia_estourada_consome_reserva_e_depois_bloqueia(monkeypatch):
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "210")   # teto 10: spot 5, delta 2, fund 0
    lim_spot = bb.fatia_limite("spot")
    reserva = bb._reserva_limite()
    for _ in range(lim_spot):
        assert bb.pode_gastar("spot", now=TER_11H)
        bb.debita("spot", now=TER_11H)
    # fatia cheia → passa a consumir reserva
    for _ in range(reserva):
        assert bb.pode_gastar("spot", now=TER_11H)
        bb.debita("spot", now=TER_11H)
    assert bb.pode_gastar("spot", now=TER_11H) is False   # reserva esgotada


def test_hard_stop_no_teto_do_dia(monkeypatch):
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "210")   # teto 10
    for _ in range(bb.teto_dia()):
        bb.debita("delta", now=TER_11H)
    assert bb.pode_gastar("delta", now=TER_11H) is False
    assert bb.pode_gastar("spot", now=TER_11H) is False   # teto vale p/ o dia


def test_soft_stop_degrada_aos_80_por_cento(monkeypatch):
    monkeypatch.setenv("B3_BRAPI_COTA_MES", "2100")  # teto 100: spot 57
    lim = bb.fatia_limite("spot")
    quase = int(lim * 0.8)           # ainda ABAIXO do limiar (80% exato de 57 é 45,6)
    for _ in range(quase):
        bb.debita("spot", now=TER_11H)
    assert bb.degradado("spot", now=TER_11H) is False
    bb.debita("spot", now=TER_11H)   # cruza os 80%
    assert bb.degradado("spot", now=TER_11H) is True
    assert bb.pode_gastar("spot", now=TER_11H) is True    # degrada, não bloqueia


def test_contador_sobrevive_a_restart():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    bb.configure_db(conn)
    bb.debita("spot", n=7, now=TER_11H)
    bb.reset()                                   # "restart": memória zera
    bb.configure_db(conn)
    snap = bb.snapshot(now=TER_11H)
    assert snap["fatias"]["spot"]["gasto"] == 7  # veio do kv, não da memória
    assert snap["total"] == 7


def test_dia_novo_zera_o_contador():
    bb.debita("spot", n=5, now=TER_11H)
    qua = datetime(2026, 8, 12, 11, 0, tzinfo=bb.BRT)
    assert bb.snapshot(now=qua)["total"] == 0


def test_snapshot_expoe_previsao_e_verdade_do_header(monkeypatch):
    from app import brapi
    monkeypatch.setitem(brapi.LAST_RATELIMIT, "x-ratelimit-remaining", "14980")
    bb.debita("spot", now=TER_11H)
    s = bb.snapshot(now=TER_11H)
    assert s["fatias"]["spot"]["gasto"] == 1 and s["tetoDia"] == 714
    assert s["headerRateLimit"]["x-ratelimit-remaining"] == "14980"
    assert s["emPregao"] is True


# ---------------------------------------------------------------------------
# Controle de utilização: intervalo → projeção mensal (determinística)
# ---------------------------------------------------------------------------
def test_projecao_e_pura_e_deterministica():
    p = bb.projecao(300, universo_n=65, cota=15000)
    # spot: 65 × (26100//300=87) × 21 = 118755; delta: 65×21=1365; fund: 1365//7=195
    assert p["detalhe"] == {"spot": 118755, "delta": 1365, "fundamentos": 195}
    assert p["chamadasMes"] == 120315
    assert p["cabeNaCota"] is False
    assert p["percentualDaCota"] == round(120315 / 15000 * 100, 1)
    # intervalo mínimo seguro: refresh_max = (15000−1560)/(65×21) ≈ 9,84/pregão
    # → 26100/9,84 ≈ 2652s (+1)
    assert 2600 < p["intervaloMinimoSeguro"] < 2700
    # e o mínimo seguro de fato cabe
    p2 = bb.projecao(p["intervaloMinimoSeguro"], universo_n=65, cota=15000)
    assert p2["cabeNaCota"] is True


def test_projecao_universo_zero_nao_divide_por_zero():
    p = bb.projecao(300, universo_n=0, cota=15000)
    assert p["chamadasMes"] == 0 and p["cabeNaCota"] is True
    assert p["intervaloMinimoSeguro"] is None


def test_intervalo_configuravel_persiste_e_alimenta_snapshot():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    bb.configure_db(conn)
    assert bb.spot_intervalo_s() == 300          # default
    bb.set_spot_intervalo(600)
    bb.reset()                                    # "restart"
    bb.configure_db(conn)
    assert bb.spot_intervalo_s() == 600          # veio do kv
    s = bb.snapshot(now=TER_11H)
    assert s["spotIntervaloS"] == 600
    assert s["projecaoMes"]["intervaloS"] == 600
    assert s["projecaoMes"]["chamadasMes"] == bb.projecao(600, bb._universo_n())["chamadasMes"]


def test_intervalo_minimo_de_30s():
    assert bb.set_spot_intervalo(5) == 30
