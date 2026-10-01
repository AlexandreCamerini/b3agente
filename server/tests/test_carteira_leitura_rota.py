"""Fase 46, Plano 04 — POST /api/carteira/leitura (rota pura, sem mercado)."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app import candle_provider, options_provider
from app.main import app


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _auth(cli):
    email = f"leitura-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


def _item(**kw):
    d = {"t": "petr4", "qty": 100, "avg": 30, "stop": 28, "alvo": 36, "preco": 32}
    d.update(kw)
    return d


def test_leitura_dentro_do_plano(cli):
    r = cli.post("/api/carteira/leitura", json={"posicoes": [_item()]}, headers=_auth(cli))
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["modo"] in ("educacional", "operador")
    L = b["leituras"]["PETR4"]
    assert L["posicaoNoPlano"] == "dentro" and L["rr"] == 1.0 and L["distStopPct"] == -12.5


def test_modo_define_didatica(cli):
    h = _auth(cli)
    op = cli.post("/api/carteira/leitura", json={"modo": "operador", "posicoes": [_item()]},
                  headers=h).json()
    assert op["modo"] == "operador" and op["leituras"]["PETR4"]["didatica"] is None
    ed = cli.post("/api/carteira/leitura", json={"modo": "estudo", "posicoes": [_item()]},
                  headers=h).json()
    assert ed["leituras"]["PETR4"]["didatica"] is not None


@pytest.mark.parametrize("preco", [None, 0, "abc"])
def test_preco_invalido_nunca_vira_zero(cli, preco):
    r = cli.post("/api/carteira/leitura", json={"posicoes": [_item(preco=preco)]},
                 headers=_auth(cli))
    assert r.status_code == 200
    L = r.json()["leituras"]["PETR4"]
    assert L["preco"] is None
    assert L["rr"] is None and L["distStopPct"] is None and L["resultado"] is None
    assert L["posicaoNoPlano"] is None


def test_preco_ausente(cli):
    it = _item()
    del it["preco"]
    L = cli.post("/api/carteira/leitura", json={"posicoes": [it]},
                 headers=_auth(cli)).json()["leituras"]["PETR4"]
    assert L["preco"] is None


def test_itens_invalidos_sao_ignorados(cli):
    r = cli.post("/api/carteira/leitura",
                 json={"posicoes": ["x", 3, None, _item(t="ab"), _item(t=None), _item()]},
                 headers=_auth(cli))
    assert r.status_code == 200
    assert list(r.json()["leituras"]) == ["PETR4"]


def test_posicoes_nao_lista_400(cli):
    r = cli.post("/api/carteira/leitura", json={"posicoes": "x"}, headers=_auth(cli))
    assert r.status_code == 400


def test_teto_de_60_posicoes(cli):
    r = cli.post("/api/carteira/leitura", json={"posicoes": [_item()] * 61}, headers=_auth(cli))
    assert r.status_code == 400 and "grande demais" in r.text
    r = cli.post("/api/carteira/leitura", json={"posicoes": [_item()] * 60}, headers=_auth(cli))
    assert r.status_code == 200


def test_compras_truncadas_a_200(cli, monkeypatch):
    from app import cartao_posicao
    vistos = {}
    orig = cartao_posicao.leitura_plano

    def espia(pos, preco, compras, modo):
        vistos["n"] = len(compras)
        return orig(pos, preco, compras, modo)
    monkeypatch.setattr(cartao_posicao, "leitura_plano", espia)
    compras = [{"qty": 1, "price": 30}] * 500 + ["lixo"]
    r = cli.post("/api/carteira/leitura", json={"posicoes": [_item(compras=compras)]},
                 headers=_auth(cli))
    assert r.status_code == 200 and vistos["n"] == 200


def test_erro_em_um_item_nao_derruba(cli, monkeypatch):
    from app import cartao_posicao
    orig = cartao_posicao.leitura_plano

    def quebra(pos, preco, compras, modo):
        if pos["t"] == "VALE3":
            raise RuntimeError("boom")
        return orig(pos, preco, compras, modo)
    monkeypatch.setattr(cartao_posicao, "leitura_plano", quebra)
    r = cli.post("/api/carteira/leitura",
                 json={"posicoes": [_item(), _item(t="vale3")]}, headers=_auth(cli))
    assert r.status_code == 200 and list(r.json()["leituras"]) == ["PETR4"]


def test_rota_nao_chama_provedor_de_mercado(cli, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("provedor de mercado chamado")
    monkeypatch.setattr(candle_provider, "get_quote", boom)
    monkeypatch.setattr(options_provider, "get_options", boom)
    r = cli.post("/api/carteira/leitura", json={"posicoes": [_item()]}, headers=_auth(cli))
    assert r.status_code == 200 and r.json()["leituras"]["PETR4"]["rr"] == 1.0
