"""Quick 261006-oav (2026-10-06) — a ação do usuário passa na frente da cota.

Incidente (boris.semente.dev, F10-20260819..): rajada de GET /api/options/gate
esgotou o minuto do mydata e POST /api/options/buy devolveu 502 em 2 ms.
Cenários ponta a ponta via TestClient com o provider mydata REAL e o client
falso (sem rede):
  (1) fundo cheio (44/54) -> buy ainda executa, fundo seguinte é recusado;
  (2) teto total cheio (54/54) -> mesmo 502 de hoje + 1 WARNING (cat cota);
  reuso da cadeia first@ (sem rede, sem débito) com idade; idade nula = None.
"""
import asyncio
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import mydata_budget, obslog, options_provider_mydata as opm

EXP = "2099-01-15"
MSG_502 = "Cotação de opções indisponível no momento — tente novamente."
TERMO = {"aceitoEm": "2026-09-13T00:00:00Z", "versao": "1.0"}


class _Client:
    def __init__(self):
        self.venc = 0
        self.chain = 0

    async def get_vencimentos(self, ticker, pregao=None, **k):
        self.venc += 1
        return [{"dt_vencimento": EXP}]

    async def get_options_chain(self, ticker, vencimento=None, pregao=None, tipo=None, **k):
        self.chain += 1
        return [{"contrato": "PETRK30", "tipo": "CALL", "strike": 30.0, "premio": 1.25,
                 "preco_objeto": 30.0, "dt_pregao": "2026-10-05",
                 "quantidade_negociada": 5000}]


@pytest.fixture(autouse=True)
def _isola_app_main():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


@pytest.fixture
def ambiente(monkeypatch):
    d = tempfile.mkdtemp(prefix="b3_cota_reserva_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "mydata")
    sys.modules.pop("app.main", None)
    m = importlib.import_module("app.main")
    client = TestClient(m.app)
    r = client.post("/api/auth/register",
                    json={"email": "cota-reserva@boris.dev", "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    headers = {"authorization": "Bearer " + r.json()["token"]}
    r = client.put("/api/config",
                   json={"descobertoTermo": dict(TERMO), "permitirOpcaoADescoberto": True},
                   headers=headers)
    assert r.status_code == 200, r.text
    fake = _Client()
    monkeypatch.setattr(opm.mydata_client, "get_vencimentos", fake.get_vencimentos)
    monkeypatch.setattr(opm.mydata_client, "get_options_chain", fake.get_options_chain)
    # minuto travado: a janela não vira durante o teste
    monkeypatch.setattr(mydata_budget, "_chave_minuto", lambda now=None: "2026-10-06 10:00")
    opm._cache.clear()
    opm._venc_cache.clear()
    mydata_budget.reset()
    obslog.reset()
    yield client, headers, fake, m
    opm._cache.clear()
    opm._venc_cache.clear()
    mydata_budget.reset()
    obslog.reset()


def _buy(client, headers):
    return client.post("/api/options/buy",
                       json={"underlying": "PETR4", "contractSymbol": "PETRK30",
                             "qty": 100, "expiration": EXP}, headers=headers)


def test_cenario1_fundo_cheio_buy_ainda_executa(ambiente):
    client, headers, fake, _m = ambiente
    mydata_budget.debita(n=44)
    r = _buy(client, headers)
    assert r.status_code == 200, r.text
    assert r.json()["priceUsed"] == 1.25
    assert mydata_budget.snapshot()["gastoMinuto"] == 46
    assert mydata_budget.pode_gastar(1) is False        # fundo recusado
    out = asyncio.run(opm.get_options("VALE3"))
    assert out["providerStatus"] == "degraded"


def test_cenario2_teto_total_cheio_502_identico_e_log(ambiente):
    client, headers, fake, _m = ambiente
    mydata_budget.debita(n=54)
    r = _buy(client, headers)
    assert r.status_code == 502
    assert r.json()["detail"] == MSG_502
    assert fake.venc == 0 and fake.chain == 0
    ev = obslog.recent(cat="cota")
    assert ev and ev[0]["level"] == "warn"
    assert ev[0]["extra"]["janela"] == "minuto"
    assert ev[0]["extra"]["classe"] == "usuario"
    assert ev[0]["extra"]["origem"] == "POST /api/options/buy"


def test_reuso_da_cadeia_first_sem_rede_e_com_idade(ambiente):
    client, headers, fake, _m = ambiente
    chain = asyncio.run(opm.get_options("PETR4"))        # chave first@, contexto fundo
    assert chain["providerStatus"] == "ok" and chain["expiration"] == EXP
    gasto = mydata_budget.snapshot()["gastoMinuto"]
    fake.venc = fake.chain = 0
    r = _buy(client, headers)
    assert r.status_code == 200, r.text
    assert fake.venc == 0 and fake.chain == 0
    assert mydata_budget.snapshot()["gastoMinuto"] == gasto
    j = r.json()
    assert j["priceUsed"] == 1.25
    assert isinstance(j["cotacaoLidaEm"], str)
    assert isinstance(j["cotacaoIdadeS"], int) and j["cotacaoIdadeS"] >= 0
    assert j["pregao"] == "2026-10-05"


def test_idade_desconhecida_e_none_nunca_zero(ambiente, monkeypatch):
    client, headers, _fake, m = ambiente

    async def _sem_carimbo(*a, **k):
        return {"providerStatus": "ok", "underlyingPrice": 30.0, "expiration": EXP,
                "expirations": [EXP], "puts": [],
                "calls": [{"contractSymbol": "PETRK30", "optionType": "call",
                           "strike": 30.0, "lastPrice": 1.25, "volume": 5000}]}
    monkeypatch.setattr(m.options_provider, "get_options", _sem_carimbo)
    r = _buy(client, headers)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["cotacaoIdadeS"] is None and j["cotacaoLidaEm"] is None
    assert "pregao" in j and j["pregao"] is None


def test_sell_com_fundo_cheio_tambem_executa(ambiente):
    client, headers, fake, _m = ambiente
    assert _buy(client, headers).status_code == 200
    opm._cache.clear()
    opm._venc_cache.clear()
    gasto = mydata_budget.snapshot()["gastoMinuto"]
    mydata_budget.debita(n=44 - gasto)
    r = client.post("/api/options/sell", json={"contractSymbol": "PETRK30"}, headers=headers)
    assert r.status_code == 200, r.text
    assert mydata_budget.snapshot()["gastoMinuto"] == 46
