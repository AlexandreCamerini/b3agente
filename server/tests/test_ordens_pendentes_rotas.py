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
import threading
import time

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


# =============================================================================
# Task 2 — ramo "fora do pregão -> pendente" em /api/buy e /api/sell (MERC-02/03)
# =============================================================================

def _fechar_mercado(monkeypatch, main=None):
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: False)


def _abrir_mercado(monkeypatch, main=None):
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)


def test_buy_mercado_aberto_nao_regride_comportamento_atual(monkeypatch):
    client, main = _client(monkeypatch)
    token, _uid = _registrar(client, "aberto-buy@boris.dev")
    _abrir_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("priceUsed") == 10.0
    assert body.get("pendente") is not True
    assert len(body["history"]) == 1


def test_buy_mercado_fechado_cria_pendente_reserva_caixa_sem_history(monkeypatch):
    client, main = _client(monkeypatch)
    token, uid = _registrar(client, "fechado-buy@boris.dev")
    _fechar_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))

    cash_antes = 10000.0
    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pendente"] is True
    assert body["order"]["tipo"] == "COMPRA"
    assert body["priceUsed"] is None
    assert body["precoReferencia"] == 10.0
    assert body["history"] == []
    assert body["cash"] == cash_antes - 1000.0
    assert body["caixaReservado"] == 1000.0
    assert len(body["pendingOrders"]) == 1


def test_buy_mercado_fechado_caixa_insuficiente_responde_400_sem_gravar(monkeypatch):
    client, main = _client(monkeypatch)
    token, _uid = _registrar(client, "fechado-caixa@boris.dev")
    _fechar_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=100000.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Caixa insuficiente."

    estado = client.get("/api/state", headers={"authorization": f"Bearer {token}"}).json()
    assert estado["pendingOrders"] == []
    assert estado["cash"] == 10000.0


def test_buy_mercado_fechado_sem_cotacao_responde_502_sem_reservar(monkeypatch):
    client, main = _client(monkeypatch)
    token, _uid = _registrar(client, "fechado-semcotacao@boris.dev")
    _fechar_mercado(monkeypatch)

    async def _sem_cotacao(_t):
        return {"price": None}
    monkeypatch.setattr(main.candle_provider, "get_quote", _sem_cotacao)

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 502

    estado = client.get("/api/state", headers={"authorization": f"Bearer {token}"}).json()
    assert estado["pendingOrders"] == []
    assert estado["cash"] == 10000.0


def test_sell_mercado_fechado_reserva_quantidade_sem_history(monkeypatch):
    client, main = _client(monkeypatch)
    token, _uid = _registrar(client, "fechado-sell@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _abrir_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))
    r = client.post("/api/buy", json={"t": "PETR4", "qty": 200}, headers=headers)
    assert r.status_code == 200, r.text

    _fechar_mercado(monkeypatch)
    r = client.post("/api/sell", json={"t": "PETR4", "qty": 100}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pendente"] is True
    assert body["order"]["tipo"] == "VENDA"
    assert body["order"]["avgReservado"] == 10.0
    assert len(body["history"]) == 1  # só a compra; a venda pendente não gravou history
    pos = next(p for p in body["positions"] if p["t"] == "PETR4")
    assert pos["qty"] == 100


def test_body_pendente_true_durante_pregao_e_ignorado(monkeypatch):
    client, main = _client(monkeypatch)
    token, _uid = _registrar(client, "flag-ignorada@boris.dev")
    _abrir_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100, "pendente": True},
                     headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("pendente") is not True
    assert body["priceUsed"] == 10.0


def test_buy_mercado_fechado_sem_sessao_responde_401_sem_gravar(monkeypatch):
    client, main = _client(monkeypatch)
    _fechar_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100})
    assert r.status_code == 401

    estado = client.get("/api/state").json()
    assert estado["pendingOrders"] == []


def test_sell_mercado_fechado_sem_sessao_responde_401(monkeypatch):
    client, main = _client(monkeypatch)
    _fechar_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))

    r = client.post("/api/sell", json={"t": "PETR4"})
    assert r.status_code in (400, 401)
    # sem posição nenhuma, o erro pode ser 400 "sem posicao" (checagem
    # inicial, fora da trava) OU 401 se a ordem de checagem mudar — o que
    # importa aqui é que NUNCA cria pendente no balde anônimo.
    estado = client.get("/api/state").json()
    assert estado["pendingOrders"] == []


def test_sell_mercado_fechado_sem_sessao_com_posicao_no_balde_anonimo_responde_401(monkeypatch):
    """Variante da anterior que EXERCITA de verdade o ramo `scope is None`
    de `/api/sell` (T-02-07): sem posição, a checagem inicial de `pos` já
    barra com 400 antes de chegar lá — este teste planta uma posição no
    escopo anônimo (`user_id=None`) diretamente pelo motor para provar que,
    mesmo com posição disponível, o mercado fechado + sem sessão nunca cria
    pendente no balde compartilhado."""
    client, main = _client(monkeypatch)
    main.store.buy(main._conn, "PETR4", 100, 10.0, user_id=None)
    _fechar_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))

    r = client.post("/api/sell", json={"t": "PETR4"})
    assert r.status_code == 401

    estado = client.get("/api/state").json()
    assert estado["pendingOrders"] == []
    pos = next(p for p in estado["positions"] if p["t"] == "PETR4")
    assert pos["qty"] == 100  # nada foi reservado/vendido


def test_concorrencia_buy_bloqueia_enquanto_order_lock_esta_seguro(monkeypatch):
    client, main = _client(monkeypatch)
    token, uid = _registrar(client, "concorrencia-buy@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _abrir_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))

    resultados = {}

    def _worker():
        r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers)
        resultados["status"] = r.status_code

    main.store.ORDER_LOCK.acquire()
    try:
        t = threading.Thread(target=_worker)
        t.start()
        time.sleep(0.3)
        cash_durante = main.store.get(main._conn, "cash", user_id=uid)
        history_durante = main.store.get(main._conn, "history", user_id=uid)
        assert cash_durante == 10000.0
        assert history_durante == []
        assert t.is_alive(), "a requisicao deveria estar bloqueada pela trava"
    finally:
        main.store.ORDER_LOCK.release()
    t.join(timeout=5)
    assert not t.is_alive()
    assert resultados.get("status") == 200
    cash_depois = main.store.get(main._conn, "cash", user_id=uid)
    history_depois = main.store.get(main._conn, "history", user_id=uid)
    assert cash_depois == 9000.0
    assert len(history_depois) == 1


def test_concorrencia_sell_bloqueia_enquanto_order_lock_esta_seguro(monkeypatch):
    client, main = _client(monkeypatch)
    token, uid = _registrar(client, "concorrencia-sell@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _abrir_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))
    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers)
    assert r.status_code == 200, r.text

    resultados = {}

    def _worker():
        r = client.post("/api/sell", json={"t": "PETR4"}, headers=headers)
        resultados["status"] = r.status_code

    main.store.ORDER_LOCK.acquire()
    try:
        t = threading.Thread(target=_worker)
        t.start()
        time.sleep(0.3)
        history_durante = main.store.get(main._conn, "history", user_id=uid)
        assert len(history_durante) == 1  # só a compra
        assert t.is_alive(), "a requisicao deveria estar bloqueada pela trava"
    finally:
        main.store.ORDER_LOCK.release()
    t.join(timeout=5)
    assert not t.is_alive()
    assert resultados.get("status") == 200
    history_depois = main.store.get(main._conn, "history", user_id=uid)
    assert len(history_depois) == 2


def test_ordenacao_pendente_executada_depois_compra_imediata_nao_perde_escrita(monkeypatch):
    import asyncio

    from app import pending_orders

    client, main = _client(monkeypatch)
    token, uid = _registrar(client, "ordenacao@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    cash_inicial = 10000.0

    _fechar_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))
    r = client.post("/api/buy", json={"t": "VALE3", "qty": 100}, headers=headers)
    assert r.status_code == 200, r.text
    custo_pendente_reservado = 1000.0
    assert r.json()["cash"] == cash_inicial - custo_pendente_reservado

    async def _price_getter(_t):
        return {"price": 12.0, "source": "fake"}

    asyncio.run(pending_orders.executar_pendentes(main._conn, uid, _price_getter))
    custo_pendente_real = 100 * 12.0

    _abrir_mercado(monkeypatch)
    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers)
    assert r.status_code == 200, r.text
    custo_imediato = 100 * 10.0

    estado = client.get("/api/state", headers=headers).json()
    assert estado["cash"] == round(cash_inicial - custo_pendente_real - custo_imediato, 2)
    assert len(estado["history"]) == 2


def test_sell_revalida_posicao_dentro_da_trava(monkeypatch):
    from app import pending_orders

    client, main = _client(monkeypatch)
    token, uid = _registrar(client, "revalida@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _abrir_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))
    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers)
    assert r.status_code == 200, r.text

    # consome a posição inteira via cancelamento de uma venda pendente
    # simulada diretamente no motor (sem passar por rota), imitando outra
    # thread/execução esvaziando a posição entre a leitura e a escrita.
    pending_orders.criar_venda(main._conn, uid, "PETR4", 100)

    r = client.post("/api/sell", json={"t": "PETR4"}, headers=headers)
    assert r.status_code == 400
    assert "PETR4" in r.json()["detail"]


# =============================================================================
# Task 3 — DELETE /api/orders/pending/{id} (MERC-04) + pet:evolucao
# =============================================================================

def test_delete_pendente_compra_devolve_caixa(monkeypatch):
    client, main = _client(monkeypatch)
    token, _uid = _registrar(client, "cancela-compra@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _fechar_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))
    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers)
    order_id = r.json()["order"]["id"]

    r = client.delete(f"/api/orders/pending/{order_id}", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cash"] == 10000.0
    assert body["caixaReservado"] == 0
    assert body["pendingOrders"] == []


def test_delete_pendente_venda_restaura_posicao(monkeypatch):
    client, main = _client(monkeypatch)
    token, _uid = _registrar(client, "cancela-venda@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _abrir_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))
    r = client.post("/api/buy", json={"t": "PETR4", "qty": 200}, headers=headers)
    assert r.status_code == 200, r.text

    _fechar_mercado(monkeypatch)
    r = client.post("/api/sell", json={"t": "PETR4", "qty": 100}, headers=headers)
    order_id = r.json()["order"]["id"]

    r = client.delete(f"/api/orders/pending/{order_id}", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    pos = next(p for p in body["positions"] if p["t"] == "PETR4")
    assert pos["qty"] == 200
    assert pos["avg"] == 10.0
    assert body["pendingOrders"] == []


def test_delete_pendente_id_inexistente_responde_404(monkeypatch):
    client, main = _client(monkeypatch)
    token, _uid = _registrar(client, "cancela-404@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    r = client.delete("/api/orders/pending/po_inexistente", headers=headers)
    assert r.status_code == 404
    assert "detail" in r.json()


def test_delete_pendente_sem_sessao_responde_401(monkeypatch):
    client, _main = _client(monkeypatch)
    r = client.delete("/api/orders/pending/po_qualquer")
    assert r.status_code == 401


def test_delete_pendente_de_outra_conta_responde_404_e_preserva_a_original(monkeypatch):
    client, main = _client(monkeypatch)
    token_a, _uid_a = _registrar(client, "conta-a@boris.dev")
    token_b, _uid_b = _registrar(client, "conta-b@boris.dev")
    headers_a = {"authorization": f"Bearer {token_a}"}
    headers_b = {"authorization": f"Bearer {token_b}"}
    _fechar_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))
    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers_a)
    order_id = r.json()["order"]["id"]

    r = client.delete(f"/api/orders/pending/{order_id}", headers=headers_b)
    assert r.status_code == 404

    estado_a = client.get("/api/state", headers=headers_a).json()
    assert len(estado_a["pendingOrders"]) == 1
    assert estado_a["pendingOrders"][0]["id"] == order_id


def test_pet_evolucao_patrimonio_inclui_caixa_reservado(monkeypatch):
    client, main = _client(monkeypatch)
    token, _uid = _registrar(client, "pet-evolucao@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    antes = client.get("/api/pet/resumo", params={"tela": "evolucao"}, headers=headers)
    assert antes.status_code == 200, antes.text
    patrimonio_antes = antes.json()["patrimonio"]

    _fechar_mercado(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake_factory(price=10.0))
    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers)
    assert r.status_code == 200, r.text

    depois = client.get("/api/pet/resumo", params={"tela": "evolucao"}, headers=headers)
    assert depois.status_code == 200, depois.text
    body = depois.json()
    assert body["patrimonio"] == pytest.approx(patrimonio_antes)
    assert any("reservad" in linha.lower() for linha in body["fala"])
