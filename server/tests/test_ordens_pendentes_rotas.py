"""Guardiões de ROTA (TestClient) do motor de ordens pendentes (Fase 2,
plano 02-02, MERC-01..04).

O que trava aqui:
  • `GET /api/market/status` é PÚBLICA (sem Authorization) e não vaza NENHUM
    dado de conta — mesma resposta com ou sem token, e disponível mesmo em
    host gated (T-02-08/T-02-11).
  • `/api/buy` e `/api/sell` decidem "mercado fechado" SÓ por
    `pregao.in_market_hours()` — nunca pelo corpo da requisição (T-02-10) —
    e, fechado, criam ordem pendente com reserva em vez de executar ao preço
    do momento (D-01/D-02/D-05/D-06).
  • O caminho IMEDIATO de compra/venda passa a adquirir a MESMA
    `store.ORDER_LOCK` que `pending_orders`, fechando o lost-update entre a
    requisição HTTP e a execução de pendentes do scheduler (T-02-35).
  • `DELETE /api/orders/pending/{id}` cancela, devolve caixa/posição e é
    escopado por conta (T-02-09, IDOR).
  • `pet:evolucao` soma o caixa reservado ao patrimônio — o assistente nunca
    diverge da tela quando existe ordem pendente.

Isolamento: banco temporário via B3_DB_PATH + reimport de `app.main`, no
MESMO padrão de `test_gate_cadastro.py`/`test_ciclo_imediato_apos_carteira.py`
— sem isto o teste sujaria o banco real e o próximo arquivo da suíte herdaria
o módulo reimportado.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import pregao as pregao_mod


@pytest.fixture(autouse=True)
def _app_main_isolado():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, hosts=None):
    if hosts is None:
        monkeypatch.delenv("B3_GATED_HOSTS", raising=False)
    else:
        monkeypatch.setenv("B3_GATED_HOSTS", hosts)
    d = tempfile.mkdtemp(prefix="b3_ordens_pendentes_rotas_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registrar(client, email="teste@boris.dev"):
    r = client.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    return r.json()["token"], r.json()["user"]["id"]


def _quote_fake_factory(price=10.0, source="fake"):
    async def _quote_fake(_t):
        return {"price": price, "change": 0, "source": source}
    return _quote_fake


# =============================================================================
# Task 1 — GET /api/market/status (MERC-01)
# =============================================================================

_CHAVES_STATUS = {"aberto", "diaDePregao", "abertura", "fechamento", "agoraBRT", "afterMarket"}


def test_market_status_sem_authorization_responde_200(monkeypatch):
    client, _ = _client(monkeypatch)
    r = client.get("/api/market/status")
    assert r.status_code == 200, r.text


def test_market_status_payload_tem_exatamente_as_seis_chaves(monkeypatch):
    client, _ = _client(monkeypatch)
    r = client.get("/api/market/status")
    assert set(r.json().keys()) == _CHAVES_STATUS


def test_market_status_nao_muda_com_token_valido(monkeypatch):
    client, _ = _client(monkeypatch)
    token, _uid = _registrar(client)
    sem_token = client.get("/api/market/status").json()
    com_token = client.get("/api/market/status", headers={"authorization": f"Bearer {token}"}).json()
    assert sem_token == com_token


def test_market_status_reflete_pregao_in_market_hours_e_is_trading_day(monkeypatch):
    client, main = _client(monkeypatch)
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(pregao_mod, "is_trading_day", lambda d=None: False)
    r = client.get("/api/market/status")
    body = r.json()
    assert body["aberto"] is True
    assert body["diaDePregao"] is False


def test_market_status_host_gated_sem_sessao_passa_state_401(monkeypatch):
    client, _ = _client(monkeypatch, hosts="acamerini.app")
    headers = {"host": "acamerini.app"}
    assert client.get("/api/market/status", headers=headers).status_code == 200
    assert client.get("/api/state", headers=headers).status_code == 401
