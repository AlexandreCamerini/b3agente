"""Fase 51 plano 07 — rotas do card "Seu dia na bolsa".

Guardiões: login obrigatório (T-51-19), isolamento por conta (T-51-20),
validação de vistos (T-51-21) e consentimento só pela rota de convite (T-51-22,
D-13: register-token nunca altera `estado_fechamento`)."""
import importlib
import os
import re
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _app_main_isolado():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_dnb_rotas_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email):
    r = c.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    return r.json()["token"], r.json()["user"]["id"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _semear_card(main, uid):
    from app import db, dia_na_bolsa
    db.kv_set(main._conn, dia_na_bolsa.K_CARD, {
        "data": "2026-11-17", "calculadoEm": "2026-11-17T17:30:00-03:00",
        "familias": {"1": {"chave": "x", "vals": {}}, "2": {"chave": "y", "vals": {}}},
        "chamadas": {}}, user_id=uid)


def test_rotas_sem_login_sao_401(monkeypatch):
    c, _ = _client(monkeypatch)
    assert c.get("/api/dia-na-bolsa").status_code == 401
    assert c.post("/api/dia-na-bolsa/vistos", json={"tickers": [], "origem": "radar"}).status_code == 401
    assert c.post("/api/dia-na-bolsa/convite", json={"aceite": True}).status_code == 401


def test_get_devolve_chaves_do_payload(monkeypatch):
    c, _ = _client(monkeypatch)
    tok, _uid = _registra(c, "a@example.com")
    r = c.get("/api/dia-na-bolsa", headers=_h(tok))
    assert r.status_code == 200
    j = r.json()
    assert {"card", "convite", "fechamento", "ultimas4Semanas"} <= set(j)
    assert j["card"] is None
    assert len(j["ultimas4Semanas"]) == 28


def test_get_modo_ordena_familias_e_invalido_vira_estudo(monkeypatch):
    c, main = _client(monkeypatch)
    tok, uid = _registra(c, "a@example.com")
    _semear_card(main, uid)
    op = c.get("/api/dia-na-bolsa?modo=operador", headers=_h(tok)).json()
    assert op["card"]["ordem"][0] == 2
    es = c.get("/api/dia-na-bolsa?modo=estudo", headers=_h(tok)).json()
    assert es["card"]["ordem"][0] == 1
    lixo = c.get("/api/dia-na-bolsa?modo=zzz", headers=_h(tok)).json()
    assert lixo["card"]["ordem"] == es["card"]["ordem"]


def test_isolamento_entre_contas(monkeypatch):
    c, main = _client(monkeypatch)
    _ta, ua = _registra(c, "a@example.com")
    tb, _ub = _registra(c, "b@example.com")
    _semear_card(main, ua)
    assert c.get("/api/dia-na-bolsa", headers=_h(tb)).json()["card"] is None


def test_vistos_valida_origem_e_tamanho(monkeypatch):
    c, _ = _client(monkeypatch)
    tok, _ = _registra(c, "a@example.com")
    r = c.post("/api/dia-na-bolsa/vistos", headers=_h(tok), json={"tickers": ["PETR4"], "origem": "foo"})
    assert r.status_code == 400 and r.json()["detail"]
    r = c.post("/api/dia-na-bolsa/vistos", headers=_h(tok),
               json={"tickers": [f"AAA{i}" for i in range(61)], "origem": "radar"})
    assert r.status_code == 400
    r = c.post("/api/dia-na-bolsa/vistos", headers=_h(tok), json={"tickers": "PETR4", "origem": "radar"})
    assert r.status_code == 400


def test_vistos_valido_ignora_preco_do_corpo(monkeypatch):
    c, _ = _client(monkeypatch)
    tok, _ = _registra(c, "a@example.com")
    r = c.post("/api/dia-na-bolsa/vistos", headers=_h(tok),
               json={"tickers": ["PETR4"], "origem": "radar", "entrada": 1, "stop": 1, "alvo": 999})
    assert r.status_code == 200, r.text
    assert set(r.json()) >= {"registrados", "semPlano", "ignorados"}


def test_convite_grava_consentimento_e_valida_booleano(monkeypatch):
    c, _ = _client(monkeypatch)
    tok, uid = _registra(c, "a@example.com")
    r = c.post("/api/dia-na-bolsa/convite", headers=_h(tok), json={"aceite": False})
    assert r.json()["fechamento"] == {"ligado": False, "decidido": True}
    r = c.post("/api/dia-na-bolsa/convite", headers=_h(tok), json={"aceite": True})
    assert r.json()["fechamento"] == {"ligado": True, "decidido": True}
    for ruim in ({}, {"aceite": "sim"}, {"aceite": 1}):
        assert c.post("/api/dia-na-bolsa/convite", headers=_h(tok), json=ruim).status_code == 400


def test_convite_so_afeta_a_propria_conta(monkeypatch):
    from app import push
    c, main = _client(monkeypatch)
    ta, ua = _registra(c, "a@example.com")
    _tb, ub = _registra(c, "b@example.com")
    c.post("/api/dia-na-bolsa/convite", headers=_h(ta), json={"aceite": False, "uid": ub})
    assert push.estado_fechamento(main._conn, ua) == {"ligado": False, "decidido": True}
    # conta nova nasce ligada e decidida (51-03); a rota de A não mexeu em B
    assert push.estado_fechamento(main._conn, ub) == {"ligado": True, "decidido": True}


def test_register_token_nao_altera_o_consentimento(monkeypatch):
    from app import db, push
    c, main = _client(monkeypatch)
    tok, uid = _registra(c, "a@example.com")
    # zera o estado que a conta nova ganhou, para provar o caso "não decidido"
    db.kv_set(main._conn, "pushPrefs", {}, user_id=uid)
    assert push.estado_fechamento(main._conn, uid) == {"ligado": False, "decidido": False}
    r = c.post("/api/push/register-token", headers=_h(tok),
               json={"token": "", "prefs": {"fechamento": True}})
    assert r.status_code == 200
    assert push.estado_fechamento(main._conn, uid) == {"ligado": False, "decidido": False}
    # conta que aceitou: register-token não desliga
    c.post("/api/dia-na-bolsa/convite", headers=_h(tok), json={"aceite": True})
    c.post("/api/push/register-token", headers=_h(tok),
           json={"token": "", "prefs": {"fechamento": False, "fechamentoDecidido": True}})
    assert push.estado_fechamento(main._conn, uid) == {"ligado": True, "decidido": True}


def test_main_tem_um_unico_call_site_de_decidir_fechamento():
    src = (Path(__file__).resolve().parent.parent / "app" / "main.py").read_text(encoding="utf-8")
    assert len(re.findall(r"decidir_fechamento\(", src)) == 1
