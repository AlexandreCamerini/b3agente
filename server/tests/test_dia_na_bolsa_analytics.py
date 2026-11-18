"""Fase 51-09 (ENG-12): WAU exato, engajamento do card e rota RBAC."""
import json
import sqlite3
import time
from datetime import datetime, timedelta

import pytest

from app import analytics
from tests.test_analytics import _client, _registra, _app_main_isolado  # noqa: F401

NOW = time.time()


def _dia(delta=0):
    return (datetime.fromtimestamp(NOW, tz=analytics.BRT).date() - timedelta(days=delta)).isoformat()


def _conn():
    c = sqlite3.connect(":memory:")
    analytics.init_db(c)
    return c


def _ev(c, uid, event, props=None, delta=0):
    c.execute(
        "INSERT INTO analytics_events(user_id, event, properties, client_ts, ingested_at, day) VALUES(?,?,?,?,?,?)",
        (uid, event, json.dumps(props or {}), None, NOW, _dia(delta)),
    )


def test_wau_conta_usuarios_distintos_em_7_dias():
    c = _conn()
    for u in ("a", "b", "c", "a"):
        _ev(c, u, "session_start", delta=1)
    _ev(c, "d", "session_start", delta=10)
    assert analytics.wau(c, 7, _now=NOW) == 3


def test_engajamento_exploracao_global_e_por_familia_modo():
    c = _conn()
    for i in range(10):
        _ev(c, f"u{i}", "daily_card_shown", {"modo": "estudo", "card": "c1", "familias": "13"})
    for i in range(3):
        _ev(c, f"u{i}", "daily_card_explored", {"modo": "estudo", "card": "c1", "tipo": "x", "familia": "1"})
    r = analytics.engajamento_fechamento(c, 28, _now=NOW)
    assert r["exploracao"]["global"] == {"explorou": 3, "viu": 10, "pct": 30.0, "amostraPequena": True}
    cel = {(x["familia"], x["modo"]): x for x in r["exploracao"]["porFamiliaModo"]}
    assert cel[("1", "estudo")]["explorou"] == 3 and cel[("1", "estudo")]["viu"] == 10
    assert cel[("3", "estudo")]["explorou"] == 0
    assert cel[("1", "estudo")]["amostraPequena"] is True


def test_amostra_pequena_some_com_20_vistos():
    c = _conn()
    for i in range(20):
        _ev(c, f"u{i}", "daily_card_shown", {"modo": "operador", "card": "c", "familias": "2"})
    r = analytics.engajamento_fechamento(c, 28, _now=NOW)
    assert r["exploracao"]["porFamiliaModo"][0]["amostraPequena"] is False


def test_dias_decisao_e_operacoes_por_ativo():
    c = _conn()
    for u in ("a", "b"):
        _ev(c, u, "session_start")
    for d in (0, 1, 2):
        _ev(c, "a", "decision_day", {"modo": "estudo"}, delta=d)
    _ev(c, "b", "decision_day", {"modo": "estudo"})
    for _ in range(4):
        _ev(c, "a", "trade_simulated")
    r = analytics.engajamento_fechamento(c, 28, _now=NOW)
    assert r["diasDecisao"] == {"mediana": 2.0, "media": 2.0, "usuarios": 2}
    assert r["operacoesPorAtivo"] == 2.0
    assert r["series"]["operacoesPorAtivoSemanal"]


def test_operacoes_por_ativo_nulo_sem_wau():
    c = _conn()
    _ev(c, "a", "trade_simulated")
    assert analytics.engajamento_fechamento(c, 28, _now=NOW)["operacoesPorAtivo"] is None


def test_saida_sem_meta_alvo_tone_nem_user_id():
    c = _conn()
    _ev(c, "usuario-secreto", "daily_card_shown", {"modo": "estudo", "card": "c", "familias": "1"})
    txt = json.dumps(analytics.engajamento_fechamento(c, 28, _now=NOW)).lower()
    for proibido in ("meta", "alvo", "tone", "usuario-secreto"):
        assert proibido not in txt.replace("amostrapequena", "")


def test_wau_7d_persiste_na_serie():
    c = _conn()
    assert "wau_7d" in analytics.METRICAS_CONHECIDAS
    analytics.registrar_metricas_diarias(c, _dia(0), {"wau_7d": 5})
    assert analytics.serie_metrica(c, "wau_7d", 7, _now=NOW) == [{"day": _dia(0), "value": 5.0}]


def test_rota_exige_permissao(monkeypatch):
    c, _, _d = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    comum = _registra(c, "outro@teste.com")
    assert c.get("/api/analytics/engajamento", headers={"authorization": f"Bearer {comum}"}).status_code == 403
    r = c.get("/api/analytics/engajamento?dias=500", headers={"authorization": f"Bearer {admin}"})
    assert r.status_code == 200, r.text
    assert r.json()["dias"] == 90
