"""Fase 5, Plano 01 — FIX-C25: guardião de rota (nível HTTP) dos caminhos de
rejeição de `/api/buy` e `/api/sell`.

INVENTÁRIO (auditado em 2026-08-23, direto contra `server/app/main.py:1800-1960`).
O achado C-25 original (auditoria de 2026-08-18) contava aproximadamente "3
caminhos de rejeição" e o objetivo deste plano fala em "7" — a auditoria
literal aqui encontrou 9 branches HTTP distintas (5 em `/api/buy`, 4 em
`/api/sell`); a diferença é o achado original não separar os dois ramos
dentro/fora de pregão de `/api/buy`, nem os dois sub-casos de "Quantidade
inválida" em `/api/sell`. A tabela abaixo é a contagem real, não a
aproximação do achado.

| # | Rota | Caminho de rejeição | HTTP | Coberto em |
|---|------|----------------------|------|------------|
| 1 | POST /api/buy  | `_normalize_ticker(t)` com menos de 4 chars | 400 "Ticker invalido." | **este arquivo** (novo — era o único não coberto de `/api/buy`) |
| 2 | POST /api/buy  | cotação ausente/`price is None` | 502 "Sem cotacao para X" | `test_rotas_fase4.py::test_rejeicao_por_falta_de_cotacao_grava_price_none` (em pregão) e `test_ordens_pendentes_rotas.py::test_buy_mercado_fechado_sem_cotacao_responde_502_sem_reservar` (fora de pregão) |
| 3 | POST /api/buy  | em pregão, `qty*price > cash` | 400 "Caixa insuficiente." | `test_rotas_fase4.py::test_buy_caixa_insuficiente_grava_rejeicao_sem_mudar_o_erro` |
| 4 | POST /api/buy  | fora de pregão, `pending_orders.CaixaInsuficiente` | 400 (mensagem da exceção) | `test_ordens_pendentes_rotas.py::test_buy_mercado_fechado_caixa_insuficiente_responde_400_sem_gravar` |
| 5 | POST /api/buy  | fora de pregão, `scope is None` | 401 (login exigido) | `test_ordens_pendentes_rotas.py::test_buy_mercado_fechado_sem_sessao_responde_401_sem_gravar` |
| 6 | POST /api/sell | sem posição no ticker | 400 "Sem posicao em X" | `test_rotas_fase4.py::test_sell_sem_posicao_grava_rejeicao_com_pnl_nulo` |
| 7 | POST /api/sell | cotação ausente/`price is None` | 502 "Sem cotacao para X" | **este arquivo** (novo — nenhum arquivo cobria o 502 de `/api/sell`, só o de `/api/buy`) |
| 8 | POST /api/sell | `qty` não convertível para `int` | 400 "Quantidade inválida." | **este arquivo** (novo) |
| 9 | POST /api/sell | `qty` inteiro <= 0 | 400 "Quantidade inválida." | **este arquivo** (novo — regressão conhecida F10-20260819: `0` era falsy e virava venda TOTAL silenciosa antes da correção `is not None`) |

Os 4 caminhos marcados "este arquivo" são os que o inventário confirmou
descobertos — os outros 5 já tinham asserção HTTP em arquivos existentes
(a maior parte fechada pela Fase 4, FIX-C02, que é POSTERIOR à auditoria
original de C-25).

Isolamento: mesmo padrão de `test_rotas_fase4.py` (seção FIX-C02) —
`B3_DB_PATH` num diretório temporário + reimport de `app.main`, para não
herdar estado de outros arquivos da suíte nem escrever no banco real.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import pregao as pregao_mod


def _client_isolado(monkeypatch):
    d = tempfile.mkdtemp(prefix="b3_rejeicao_fase5_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    sys.modules.pop("app.main", None)
    m = importlib.import_module("app.main")
    return TestClient(m.app), m


def _registrar(client, email):
    r = client.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    return r.json()["token"], r.json()["user"]["id"]


def _quote_fake(price):
    async def _q(_t):
        return {"price": price, "change": 0, "source": "fake"}
    return _q


def _sem_cotacao():
    async def _q(_t):
        return {"price": None}
    return _q


@pytest.fixture(autouse=True)
def _isola_app_main():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


# ===========================================================================
# Caminho 1 — /api/buy com ticker curto
# ===========================================================================

def test_buy_ticker_curto_400_ticker_invalido(monkeypatch):
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "ticker-curto@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)

    r = client.post("/api/buy", json={"t": "AB", "qty": 100}, headers=headers)
    assert r.status_code == 400
    assert r.json()["detail"] == "Ticker invalido."

    estado = client.get("/api/state", headers=headers).json()
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada"
    assert entry["type"] == "COMPRA"
    assert entry["price"] is None, "nunca 0 nem 0.0 — CLAUDE.md item 4"
    assert estado["cash"] == 10000.0, "rejeição não pode mover dinheiro"


def test_buy_ticker_curto_anonimo_nao_grava_no_balde_compartilhado(monkeypatch):
    """T-05-03: o balde anônimo é compartilhado entre todos os usuários sem
    login — uma rejeição nele vazaria histórico de um anônimo para outro."""
    client, m = _client_isolado(monkeypatch)
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)

    r = client.post("/api/buy", json={"t": "AB", "qty": 100})
    assert r.status_code == 400

    estado_anonimo = client.get("/api/state").json()
    assert estado_anonimo["history"] == [], "balde anônimo compartilhado — nunca registra rejeição"


# ===========================================================================
# Caminho 7 — /api/sell com cotação indisponível
# ===========================================================================

def test_sell_sem_cotacao_502_apos_montar_posicao(monkeypatch):
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "sell-semcotacao@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)

    # monta a posição com cotação boa antes de derrubar a cotação
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(30.0))
    r = client.post("/api/buy", json={"t": "PETR4", "qty": 200}, headers=headers)
    assert r.status_code == 200, r.text

    monkeypatch.setattr(m.candle_provider, "get_quote", _sem_cotacao())
    r = client.post("/api/sell", json={"t": "PETR4"}, headers=headers)
    assert r.status_code == 502
    assert r.json()["detail"] == "Sem cotacao para PETR4"

    estado = client.get("/api/state", headers=headers).json()
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada"
    assert entry["type"] == "VENDA"
    assert entry["price"] is None, "nunca 0 nem 0.0 — CLAUDE.md item 4"
    # posição intacta: rejeição não pode mover cotas nem caixa
    assert estado["positions"][0]["qty"] == 200


# ===========================================================================
# Caminhos 8 e 9 — /api/sell com `qty` inválida
# ===========================================================================

def test_sell_qty_nao_inteiro_400_quantidade_invalida(monkeypatch):
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "sell-qtynaoint@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(30.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 200}, headers=headers)
    assert r.status_code == 200, r.text
    cash_pos_compra = client.get("/api/state", headers=headers).json()["cash"]

    r = client.post("/api/sell", json={"t": "PETR4", "qty": "abc"}, headers=headers)
    assert r.status_code == 400
    assert r.json()["detail"] == "Quantidade inválida."

    estado = client.get("/api/state", headers=headers).json()
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada"
    assert entry["type"] == "VENDA"
    assert estado["positions"][0]["qty"] == 200, "posição não pode mudar numa rejeição"
    assert estado["cash"] == cash_pos_compra, "rejeição não pode mover caixa"


def test_sell_qty_zero_400_regressao_f10_20260819(monkeypatch):
    """F10-20260819: `int(_qty) if _qty else None` tratava `qty=0` (falsy em
    Python) como "campo ausente" e vendia a posição INTEIRA em silêncio.
    Este teste trava que `qty=0` explícito é REJEITADO, não vira venda total."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "sell-qtyzero@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(30.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 200}, headers=headers)
    assert r.status_code == 200, r.text

    r = client.post("/api/sell", json={"t": "PETR4", "qty": 0}, headers=headers)
    assert r.status_code == 400
    assert r.json()["detail"] == "Quantidade inválida."

    estado = client.get("/api/state", headers=headers).json()
    assert estado["positions"][0]["qty"] == 200, "qty=0 não pode virar venda total silenciosa"
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada" and entry["type"] == "VENDA"
