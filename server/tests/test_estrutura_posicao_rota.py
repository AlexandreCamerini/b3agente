"""Fase 44, Plano 03 — fio elétrico da chave ADITIVA `estrutura` em
`GET /api/options/proposta/{ticker}`. Provider mock, sem rede: o motor puro
já é coberto em `test_estrutura_posicao.py`; aqui se trava a rota (todas as
pernas do ativo, cadeia por vencimento, falha isolada, economia de cotação)."""
import datetime as dt
import uuid

import pytest
from fastapi.testclient import TestClient

from app import candle_provider, db, estrutura_posicao, options_provider_mock, store
from app.main import app, _conn


@pytest.fixture(autouse=True)
def _mock_provider(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "mock")
    monkeypatch.delenv("B3_OPTIONS_MOCK_STATUS", raising=False)
    yield
    monkeypatch.delenv("B3_OPTIONS_PROVIDER", raising=False)
    monkeypatch.delenv("B3_OPTIONS_MOCK_STATUS", raising=False)


@pytest.fixture(autouse=True)
def _expiracao_fixa(monkeypatch):
    fixa = dt.date.today() + dt.timedelta(days=30)
    monkeypatch.setattr(options_provider_mock, "_proximas_terceiras_sextas",
                        lambda hoje, n=3: [fixa])
    return fixa.isoformat()


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _novo_escopo(cli, slug):
    email = f"estr-rota-{slug}-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"]["id"], {"Authorization": "Bearer " + body["token"]}


def _contratos(cli):
    r = cli.get("/api/options/chain/PETR4")
    assert r.status_code == 200, r.text
    d = r.json()
    spot = d["underlyingPrice"]
    call = min((c for c in d["calls"] if c["strike"] > spot), key=lambda c: c["strike"])
    put = max((p for p in d["puts"] if p["strike"] <= spot), key=lambda p: p["strike"])
    return call, put


def _perna(c, tipo, side, exp):
    return {"id": c["contractSymbol"], "underlying": "PETR4", "optionType": tipo,
            "strike": c["strike"], "expiration": exp, "qty": 100, "avg": 0.5,
            "side": side, "lastro": {"t": "PETR4", "qty": 100}}


def _semear_collar(cli, uid):
    store.buy(_conn, "PETR4", 300, 30.0, user_id=uid)
    call, put = _contratos(cli)
    exp = call.get("expiration") or put.get("expiration")
    if not exp:
        exp = cli.get("/api/options/chain/PETR4").json().get("expiration")
    ops = [_perna(call, "CALL", "vendida", exp), _perna(put, "PUT", "comprada", exp)]
    db.kv_set(_conn, "optionPositions", ops, user_id=uid)
    return ops


def _proposta(cli, h):
    r = cli.get("/api/options/proposta/PETR4", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def test_collar_aberto_volta_duas_pernas_e_nome(cli):
    uid, h = _novo_escopo(cli, "collar")
    _semear_collar(cli, uid)
    body = _proposta(cli, h)
    est = body["estrutura"]
    assert est["nome"] == "collar"
    assert len(est["pernas"]) == 2
    for p in est["pernas"]:
        for k in ("tipo", "strike", "vencimento", "quantidade", "lado"):
            assert p[k] is not None, k


def test_sem_opcao_aberta_estrutura_none_e_legado_intacto(cli):
    uid, h = _novo_escopo(cli, "vazio")
    store.buy(_conn, "PETR4", 300, 30.0, user_id=uid)
    body = _proposta(cli, h)
    assert "estrutura" in body and body["estrutura"] is None
    for k in ("proposta", "motivo", "candidatos", "putSemLastro", "source", "at"):
        assert k in body


def test_cadeia_degradada_nunca_some_nem_zero(cli, monkeypatch):
    uid, h = _novo_escopo(cli, "degr")
    _semear_collar(cli, uid)
    monkeypatch.setenv("B3_OPTIONS_MOCK_STATUS", "degraded")
    options_cache = __import__("app.options_provider", fromlist=["x"])
    for nome in ("_cache", "_CACHE"):
        c = getattr(options_cache, nome, None)
        if isinstance(c, dict):
            c.clear()
    body = _proposta(cli, h)
    est = body["estrutura"]
    assert est is not None
    assert est["incompleto"] is True
    assert est["resultado"]["total"] is None
    assert len(est["pernas"]) == 2
    assert est["encerrar"]["permitido"] is False


def test_perna_fora_da_cadeia_fica_sem_cotacao_e_aberta_sem_proposta(cli):
    uid, h = _novo_escopo(cli, "fora")
    store.buy(_conn, "PETR4", 300, 30.0, user_id=uid)
    call, _ = _contratos(cli)
    exp = cli.get("/api/options/chain/PETR4").json().get("expiration") or call.get("expiration")
    fantasma = dict(call, contractSymbol="PETRZ999FANTASMA")
    db.kv_set(_conn, "optionPositions", [_perna(fantasma, "CALL", "vendida", exp)], user_id=uid)
    body = _proposta(cli, h)
    est = body["estrutura"]
    assert est is not None
    assert "PETRZ999FANTASMA" in est["resultado"]["pernasSemCotacao"]
    assert est["resultado"]["total"] is None
    assert body["proposta"] is None
    assert est["abertaSemProposta"] is True
    assert est["motivoSemProposta"] == body["motivo"]


def test_chave_estrutura_presente_em_todos_os_ramos(cli):
    uid, h = _novo_escopo(cli, "ramos")
    assert "estrutura" in _proposta(cli, h)
    _semear_collar(cli, uid)
    assert "estrutura" in _proposta(cli, h)


def test_falha_do_motor_e_isolada(cli, monkeypatch):
    uid, h = _novo_escopo(cli, "falha")
    _semear_collar(cli, uid)
    ref = _proposta(cli, h)

    def _boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(estrutura_posicao, "ler_estrutura", _boom)
    body = _proposta(cli, h)
    assert body["estrutura"] is None
    assert body["proposta"] == ref["proposta"]
    assert body["motivo"] == ref["motivo"]


def test_spot_da_cadeia_nao_gasta_cotacao(cli, monkeypatch):
    uid, h = _novo_escopo(cli, "quote")
    _semear_collar(cli, uid)
    chamadas = []

    async def _quote(t):
        chamadas.append(t)
        return {"price": 1.0}

    monkeypatch.setattr(candle_provider, "get_quote", _quote)
    body = _proposta(cli, h)
    assert body["estrutura"] is not None
    assert chamadas == []
