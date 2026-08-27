"""Fase 9, Plano 01 — orçamento de requisições do mydata (60/min · 2.000/dia).

O que estes testes protegem:
  • duas janelas independentes — minuto (só memória, fixa) e dia (persistida
    no `kv`, sobrevive a deploy);
  • sem fatias: o cliente serve candles e opções sob uma cota única combinada
    — `pode_gastar()`/`debita()` recebem só `n`, sem nome de fatia;
  • sem gate de pregão: o dado do mydata é EOD e o usuário navega fora do
    horário de pregão — DELIBERADAMENTE não há `em_pregao()` aqui;
  • a cota real (`mydata_client.LAST_QUOTA`) fica ao lado da previsão local em
    `snapshot()` — verdade > previsão, mesma postura de `brapi_budget`;
  • `MARGEM` mantém um teto ÚTIL abaixo do teto real, para nunca bater no 429
    do outro lado.
Offline: relógio injetado (`now`); SQLite em memória para o contador do dia.
"""
import asyncio
import sqlite3
from datetime import datetime

import pytest

from app import mydata_budget as b

MIN_10H00 = datetime(2026, 8, 25, 10, 0, tzinfo=b.BRT)
MIN_10H01 = datetime(2026, 8, 25, 10, 1, tzinfo=b.BRT)
OUTRO_DIA = datetime(2026, 8, 26, 10, 0, tzinfo=b.BRT)


@pytest.fixture(autouse=True)
def _limpo(monkeypatch):
    b.reset()
    b.configure_db(None, enabled=False)
    monkeypatch.delenv("MYDATA_QUOTA_MIN", raising=False)
    monkeypatch.delenv("MYDATA_QUOTA_DIA", raising=False)
    yield
    b.reset()
    b.configure_db(None, enabled=False)


# ---------------------------------------------------------------------------
# quota_min() / quota_dia()
# ---------------------------------------------------------------------------
def test_quota_min_default_e_via_env(monkeypatch):
    assert b.quota_min() == 60
    monkeypatch.setenv("MYDATA_QUOTA_MIN", "30")
    assert b.quota_min() == 30
    monkeypatch.setenv("MYDATA_QUOTA_MIN", "não-numero")
    assert b.quota_min() == 60


def test_quota_dia_default_e_via_env(monkeypatch):
    assert b.quota_dia() == 2000
    monkeypatch.setenv("MYDATA_QUOTA_DIA", "500")
    assert b.quota_dia() == 500
    monkeypatch.setenv("MYDATA_QUOTA_DIA", "não-numero")
    assert b.quota_dia() == 2000


# ---------------------------------------------------------------------------
# Janela do MINUTO
# ---------------------------------------------------------------------------
def test_janela_do_minuto_bloqueia_no_teto_e_libera_no_minuto_seguinte():
    teto = int(b.quota_min() * b.MARGEM)
    for _ in range(teto):
        assert b.pode_gastar(now=MIN_10H00) is True
        b.debita(now=MIN_10H00)
    assert b.pode_gastar(now=MIN_10H00) is False
    assert b.pode_gastar(now=MIN_10H01) is True   # minuto seguinte: reabre


# ---------------------------------------------------------------------------
# Janela do DIA
# ---------------------------------------------------------------------------
def test_janela_do_dia_bloqueia_mesmo_em_outro_minuto_do_mesmo_dia(monkeypatch):
    monkeypatch.setenv("MYDATA_QUOTA_DIA", "3")   # teto util = int(3*0.9) = 2
    b.debita(n=2, now=MIN_10H00)
    assert b.pode_gastar(now=MIN_10H01) is False


def test_virada_de_dia_zera_o_contador_diario():
    b.debita(n=5, now=MIN_10H00)
    assert b.pode_gastar(now=OUTRO_DIA) is True
    snap = b.snapshot(now=OUTRO_DIA)
    assert snap["gastoDia"] == 0


# ---------------------------------------------------------------------------
# Persistência do contador do dia
# ---------------------------------------------------------------------------
def test_contador_do_dia_sobrevive_a_reset_com_configure_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    b.configure_db(conn)
    b.debita(n=7, now=MIN_10H00)
    b.reset()                       # "restart": memória zera
    b.configure_db(conn)
    assert b.pode_gastar(now=MIN_10H00) is True
    snap = b.snapshot(now=MIN_10H00)
    assert snap["gastoDia"] == 7    # veio do kv, não da memória


def test_sem_configure_db_funciona_so_em_memoria():
    b.debita(n=3, now=MIN_10H00)
    snap = b.snapshot(now=MIN_10H00)
    assert snap["gastoDia"] == 3
    # nada persiste: reset zera de vez, sem configure_db para reler
    b.reset()
    assert b.snapshot(now=MIN_10H00)["gastoDia"] == 0


# ---------------------------------------------------------------------------
# aguarda_vaga()
# ---------------------------------------------------------------------------
def test_aguarda_vaga_devolve_true_quando_ha_vaga():
    assert asyncio.run(b.aguarda_vaga(now=MIN_10H00)) is True


def test_aguarda_vaga_com_minuto_cheio_e_timeout_zero_nao_dorme():
    teto = int(b.quota_min() * b.MARGEM)
    b.debita(n=teto, now=MIN_10H00)
    ok = asyncio.run(b.aguarda_vaga(now=MIN_10H00, timeout_s=0))
    assert ok is False


# ---------------------------------------------------------------------------
# snapshot() / degradado()
# ---------------------------------------------------------------------------
def test_snapshot_traz_todos_os_campos_esperados():
    snap = b.snapshot(now=MIN_10H00)
    for campo in ("dia", "quotaMin", "quotaDia", "gastoMinuto", "gastoDia",
                  "headerQuota", "degradado"):
        assert campo in snap


def test_degradado_passa_de_80_por_cento_do_teto_util(monkeypatch):
    monkeypatch.setenv("MYDATA_QUOTA_DIA", "100")   # teto util = 90
    quase = int(90 * 0.8)   # 72, ainda abaixo do limiar
    b.debita(n=quase, now=MIN_10H00)
    assert b.degradado(now=MIN_10H00) is False
    b.debita(n=1, now=MIN_10H00)   # cruza os 80%
    assert b.degradado(now=MIN_10H00) is True
