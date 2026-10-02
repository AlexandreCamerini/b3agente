"""Fase 46.1, Plano 02 — G-08 (causa da falta de prêmio por perna) e MD-03(b)
(corte das compras mais recentes). Motor puro + rota com provedor mock."""
import datetime as dt
import uuid

import pytest
from fastapi.testclient import TestClient

from app import candle_provider, db, options_provider, options_provider_mock, store
from app import estrutura_posicao as m
from app.main import app, _conn

V = dt.date(2026, 10, 16)
HOJE = V - dt.timedelta(days=20)
CALL_ID = "UGPAJ420"
VENC = V.isoformat()


def _call(side="vendida", id_=CALL_ID):
    return {"id": id_, "underlying": "UGPA3", "optionType": "call", "strike": 42.0,
            "expiration": VENC, "qty": 1000, "avg": 0.90, "side": side}


def _ler(ops, contratos, status=None):
    return m.ler_estrutura(ops, "UGPA3", {"t": "UGPA3", "qty": 1000, "avg": 39.5},
                           40.0, contratos, HOJE, "estudo", None, status_cadeias=status)


def _p0(r):
    return r["pernas"][0]


def test_sem_negocio_contrato_sem_ask_nem_last():
    r = _ler([_call()], {CALL_ID: {"contractSymbol": CALL_ID, "bid": 1.0}})
    assert _p0(r)["motivoSemCotacao"] == "sem_negocio"
    assert r["resultado"]["total"] is None


def test_fonte_indisponivel():
    r = _ler([_call()], {}, {VENC: "falha"})
    assert _p0(r)["motivoSemCotacao"] == "fonte_indisponivel"
    assert r["resultado"]["total"] is None


def test_fora_da_cadeia():
    r = _ler([_call()], {}, {VENC: "ok"})
    assert _p0(r)["motivoSemCotacao"] == "fora_da_cadeia"


def test_indeterminada_sem_status():
    assert _p0(_ler([_call()], {}))["motivoSemCotacao"] == "sem_cotacao"
    assert _p0(_ler([_call()], {}, {}))["motivoSemCotacao"] == "sem_cotacao"


def test_cotada_e_lado_invalido_dao_none():
    cot = _ler([_call()], {CALL_ID: {"contractSymbol": CALL_ID, "ask": 1.1}})
    assert _p0(cot)["motivoSemCotacao"] is None
    inval = _ler([_call(side="short")], {}, {VENC: "falha"})
    assert _p0(inval)["motivoSemCotacao"] is None


def test_aditivo_chaves_antigas_presentes():
    p = _p0(_ler([_call()], {}, {VENC: "ok"}))
    for k in ("id", "tipo", "lado", "strike", "vencimento", "quantidade", "premioEntrada",
              "premioAtual", "origemPremio", "origemTexto", "resultado",
              "diasParaVencimento", "liquidez", "encerrar", "motivoSemCotacao"):
        assert k in p
    assert p["motivoSemCotacao"] in m.MOTIVOS_SEM_COTACAO


# ------------------------------ rota ------------------------------

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "mock")
    monkeypatch.delenv("B3_OPTIONS_MOCK_STATUS", raising=False)
    fixa = dt.date.today() + dt.timedelta(days=30)
    monkeypatch.setattr(options_provider_mock, "_proximas_terceiras_sextas",
                        lambda hoje, n=3: [fixa])
    return monkeypatch


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _auth(cli, slug):
    email = f"c461-{slug}-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    b = r.json()
    return b["user"]["id"], {"Authorization": "Bearer " + b["token"]}


def _semear_fantasma(cli, uid):
    store.buy(_conn, "PETR4", 300, 30.0, user_id=uid)
    d = cli.get("/api/options/chain/PETR4").json()
    exp = d.get("expiration") or d["calls"][0].get("expiration")
    c = d["calls"][0]
    op = {"id": "PETRZ999FANTASMA", "underlying": "PETR4", "optionType": "CALL",
          "strike": c["strike"], "expiration": exp, "qty": 100, "avg": 0.5,
          "side": "vendida", "lastro": {"t": "PETR4", "qty": 100}}
    db.kv_set(_conn, "optionPositions", [op], user_id=uid)


def _est(cli, h):
    r = cli.get("/api/options/proposta/PETR4", headers=h)
    assert r.status_code == 200, r.text
    return r.json()["estrutura"]


def test_rota_fora_da_cadeia(cli, mock_env):
    uid, h = _auth(cli, "fora")
    _semear_fantasma(cli, uid)
    e = _est(cli, h)
    assert e["pernas"][0]["motivoSemCotacao"] == "fora_da_cadeia"
    assert e["resultado"]["total"] is None


def test_rota_fonte_degradada(cli, mock_env):
    uid, h = _auth(cli, "deg")
    _semear_fantasma(cli, uid)
    mock_env.setenv("B3_OPTIONS_MOCK_STATUS", "degraded")
    e = _est(cli, h)
    assert e["pernas"][0]["motivoSemCotacao"] == "fonte_indisponivel"
    assert e["resultado"]["total"] is None


def test_rota_excecao_do_provedor(cli, mock_env):
    uid, h = _auth(cli, "exc")
    _semear_fantasma(cli, uid)

    async def boom(*a, **k):
        raise RuntimeError("segredo do provedor")
    mock_env.setattr(options_provider, "get_options", boom)
    r = cli.get("/api/options/proposta/PETR4", headers=h)
    assert r.status_code == 200
    e = r.json()["estrutura"]
    assert e["pernas"][0]["motivoSemCotacao"] == "fonte_indisponivel"
    assert "segredo" not in r.text


def test_default_do_provedor_continua_yahoo(monkeypatch):
    monkeypatch.delenv("B3_OPTIONS_PROVIDER", raising=False)
    assert options_provider.provider_name() == "yahoo"


def test_compras_cortam_as_200_mais_recentes(cli, monkeypatch):
    from app import cartao_posicao
    vistos = {}
    orig = cartao_posicao.leitura_plano

    def espia(pos, preco, compras, modo):
        vistos["compras"] = compras
        return orig(pos, preco, compras, modo)
    monkeypatch.setattr(cartao_posicao, "leitura_plano", espia)
    compras = [{"qty": 1, "price": 10 + i / 100} for i in range(250)]
    item = {"t": "petr4", "qty": 100, "avg": 30, "stop": 28, "alvo": 36, "preco": 32,
            "compras": compras}
    _, h = _auth(cli, "compras")
    r = cli.post("/api/carteira/leitura", json={"posicoes": [item]}, headers=h)
    assert r.status_code == 200
    got = vistos["compras"]
    assert len(got) == 200 and got[0]["price"] == compras[50]["price"]
