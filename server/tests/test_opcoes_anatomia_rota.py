"""Fase 49 (2026-10-06) — rota grátis da anatomia da perna; provider mock, sem rede."""
import datetime as dt
import inspect
import uuid

import pytest
from fastapi.testclient import TestClient

from app import anatomia_perna, db, main as main_mod, options_provider_mock, skill_ref, store
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
    email = f"anat-rota-{slug}-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"]["id"], {"Authorization": "Bearer " + body["token"]}


def _semear(cli, uid):
    store.buy(_conn, "PETR4", 300, 30.0, user_id=uid)
    d = cli.get("/api/options/chain/PETR4").json()
    spot = d["underlyingPrice"]
    call = min((c for c in d["calls"] if c["strike"] > spot), key=lambda c: c["strike"])
    put = max((p for p in d["puts"] if p["strike"] <= spot), key=lambda p: p["strike"])
    exp = call.get("expiration") or put.get("expiration") or d.get("expiration")

    def perna(c, tipo):
        return {"id": c["contractSymbol"], "underlying": "PETR4", "optionType": tipo,
                "strike": c["strike"], "expiration": exp, "qty": 100, "avg": 0.5,
                "side": "comprada"}
    ops = [perna(call, "CALL"), perna(put, "PUT")]
    db.kv_set(_conn, "optionPositions", ops, user_id=uid)
    return ops


def _get(cli, h, q="", t="PETR4"):
    return cli.get(f"/api/options/anatomia/{t}{q}", headers=h)


def test_ok_pernas_estrutura_e_acoes(cli):
    uid, h = _novo_escopo(cli, "ok")
    ops = _semear(cli, uid)
    r = _get(cli, h)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["estado"] == "ok" and d["custoMcp"] == 0
    an = d["anatomia"]
    assert {p["id"] for p in an["pernas"]} == {o["id"] for o in ops}
    assert d["estrutura"] is not None
    n = len(an["grade"]["precos"])
    for p in an["pernas"]:
        assert len(p["pontos"]) == n
    assert an["acoes"]["incluidas"] is True
    assert an["acoes"]["precoMedio"] == 30.0


def test_excluir_acoes_e_perna(cli):
    uid, h = _novo_escopo(cli, "exc")
    ops = _semear(cli, uid)
    an = _get(cli, h, "?excluir=ACOES").json()["anatomia"]
    assert an["acoes"]["incluidas"] is False and "ACOES" in an["excluidas"]
    cid = ops[0]["id"]
    an = _get(cli, h, f"?excluir={cid}").json()["anatomia"]
    assert cid in an["excluidas"]
    assert cid not in str(an["total"]["incluidas"])


def test_validacao_de_entrada(cli):
    uid, h = _novo_escopo(cli, "val")
    _semear(cli, uid)
    assert _get(cli, h, "?excluir=NAOEXISTE").status_code == 400
    assert _get(cli, h, "?excluir=" + ",".join(f"X{i}" for i in range(21))).status_code == 400
    assert _get(cli, h, t="AB").status_code == 400


def test_sem_pernas(cli):
    uid, h = _novo_escopo(cli, "sem")
    d = _get(cli, h).json()
    assert d["estado"] == "sem_pernas" and d["motivoTexto"] and d["anatomia"] is None


def test_cadeia_degradada_nao_derruba(cli, monkeypatch):
    uid, h = _novo_escopo(cli, "deg")
    _semear(cli, uid)
    monkeypatch.setenv("B3_OPTIONS_MOCK_STATUS", "degraded")
    r = _get(cli, h)
    assert r.status_code == 200
    d = r.json()
    assert d["estado"] == "ok"
    for p in d["anatomia"]["pernas"]:
        assert isinstance(p["piorCaso"], (int, float))
        assert p["pontos"]
        assert p["hoje"]["valor"] is None and p["hoje"]["motivoTexto"]


def test_erro_do_motor_vira_estado_erro(cli, monkeypatch):
    uid, h = _novo_escopo(cli, "erro")
    _semear(cli, uid)

    def boom(*a, **k):
        raise RuntimeError("x")
    monkeypatch.setattr(anatomia_perna, "ler_anatomia", boom)
    r = _get(cli, h)
    assert r.status_code == 200
    d = r.json()
    assert d["estado"] == "erro"
    assert d["motivoTexto"] == skill_ref.opcoes_escada_txt(d["modo"], "anat_erro")


def test_rota_gratis_sem_cap_nem_mcp():
    src = inspect.getsource(main_mod.options_anatomia)
    assert "_cap_check" not in src and "/mcp/" not in src
    rotas = [r.path for r in app.routes if getattr(r, "path", "").endswith("anatomia/{ticker}")]
    assert rotas == ["/api/options/anatomia/{ticker}"]


def test_isolamento_entre_contas(cli):
    uid, h = _novo_escopo(cli, "a")
    _semear(cli, uid)
    _, h2 = _novo_escopo(cli, "b")
    assert _get(cli, h2).json()["estado"] == "sem_pernas"
