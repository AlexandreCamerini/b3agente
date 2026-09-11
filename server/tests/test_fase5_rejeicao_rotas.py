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
| 10 | POST /api/buy | `qty` inteiro <= 0 | 400 "Quantidade inválida." | **este arquivo** (novo — achado A-00, auditoria de 2026-09-10) |
| 11 | POST /api/buy | `qty` não convertível para `int` | 400 "Quantidade inválida." | **este arquivo** (novo — achado A-00b, auditoria de 2026-09-10) |

Os 4 caminhos marcados "este arquivo" são os que o inventário confirmou
descobertos — os outros 5 já tinham asserção HTTP em arquivos existentes
(a maior parte fechada pela Fase 4, FIX-C02, que é POSTERIOR à auditoria
original de C-25).

ADENDO 2026-09-10 (auditoria A-00/A-00b) — os caminhos 10 e 11 NÃO existiam
quando este inventário foi escrito: eles são a correção do achado, não uma
lacuna de cobertura. A auditoria de 2026-09-10 reproduziu contra o endpoint
real que `POST /api/buy {"t":"PETR4","qty":-500}` devolvia **200 OK** e
executava a ordem (posição de 100 ações, caixa −R$ 3.000), porque
`int(body.get("qty") or 0)` não filtrava nada e `max(100, round(qty/100)*100)`
coagia o negativo para o lote mínimo; e que `qty:"abc"` vazava **500** com o
texto cru do `ValueError`. A mesma guarda já existia em `/api/sell` (caminhos
8 e 9, regressão F10-20260819) e em `/api/options/buy` — só a compra de ação
tinha ficado de fora. O caminho 12 abaixo é o guardião do contrato que a
correção teve de PRESERVAR.

| 12 | POST /api/buy | `qty` AUSENTE do corpo | 200 — compra o lote mínimo de 100 | **este arquivo** (guardião de contrato: `qty` ausente NÃO é `qty` inválido; a correção de A-00 rejeita só o valor explícito <= 0 ou não numérico) |

ADENDO 2026-09-11 (auditoria A-09 + resto do A-00b) — as DUAS rotas de opção
ficaram fora do inventário original porque ele cobria só ação. Os caminhos 13
e 14 fecham isso: `/api/options/sell` devolvia **200 com `priceUsed`** quando
`store.sell_option` retornava `None` (posição lida ANTES do `await` da cadeia
e sumida no intervalo — vencimento liquidado pelo scheduler, venda por outro
caminho), registrando no cliente uma venda que não aconteceu; e
`/api/options/buy` vazava `ValueError` como **500** para `qty` não numérico, o
mesmo vazamento que a quick 260910-mqs fechou em `/api/buy`.

| 13 | POST /api/options/sell | `store.sell_option` devolve `None` (posição sumiu entre a leitura e a venda) | 400 "Sem posição em X" | **este arquivo** (novo — achado A-09; espelha o 400 de `/api/sell` quando `store.sell` devolve `None`) |
| 14 | POST /api/options/buy | `qty` não convertível para `int` | 400 "Contrato de opção inválido." | **este arquivo** (novo — resto do achado A-00b; `qty` ausente/zero/negativo JÁ caía neste mesmo 400, só o não numérico escapava) |

ADENDO 2026-09-11 (auditoria D-1) — o caminho de `qty` de `/api/options/sell`
era a ÚLTIMA ocorrência aberta da armadilha do falsy que F10-20260819 fechou
em `/api/sell`: `int(_qty) if _qty else None` tratava `qty=0` como campo
ausente e `store.sell_option` entende ausente como venda TOTAL — zero pedido
de propósito liquidava o contrato inteiro em silêncio, e `qty` não numérico
vazava `ValueError` como 500. Com os caminhos 15 e 16 as QUATRO rotas da
família (`/api/buy`, `/api/sell`, `/api/options/buy`, `/api/options/sell`)
passam a ter a mesma guarda e a mesma mensagem. O caminho 17 é o guardião do
contrato que a correção teve de PRESERVAR — e que, ao contrário de
`/api/options/buy` (caminho 14), aqui existe de verdade: nesta rota `qty`
ausente É venda total, e é assim que a tela vende (`optionsSell` não manda
`qty` no corpo).

| # | Rota | Caminho de rejeição | HTTP | Coberto em |
|---|------|----------------------|------|------------|
| 15 | POST /api/options/sell | `qty` inteiro <= 0 | 400 "Quantidade inválida." | **este arquivo** (novo — achado D-1; antes `0` virava venda TOTAL e `-500` também, porque `store.sell_option` só honra `qty > 0`) |
| 16 | POST /api/options/sell | `qty` não convertível para `int` | 400 "Quantidade inválida." | **este arquivo** (novo — D-1; antes 500 com o texto cru do `ValueError`) |
| 17 | POST /api/options/sell | `qty` AUSENTE do corpo | 200 — vende a posição INTEIRA | **este arquivo** (guardião de contrato: é o caminho que a tela usa; a correção de D-1 rejeita só o valor explícito) |

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


# ===========================================================================
# Caminhos 10, 11 e 12 — /api/buy com `qty` inválida (auditoria A-00/A-00b,
# 2026-09-10). Espelham os caminhos 8 e 9 da venda: a compra é a rota que
# tinha ficado sem a guarda.
# ===========================================================================

def test_buy_qty_negativo_400_auditoria_a00(monkeypatch):
    """A-00 (CRÍTICO): `POST /api/buy {"qty":-500}` devolvia 200 e EXECUTAVA a
    ordem — `max(100, round(-500/100)*100)` coagia o negativo para o lote
    mínimo, gravando 100 ações e debitando R$ 3.000 de um pedido que a rota
    nunca deveria ter aceitado. Trava o 400 + carteira intacta + rejeição no
    histórico."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "buy-qtyneg@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(30.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": -500}, headers=headers)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Quantidade inválida."

    estado = client.get("/api/state", headers=headers).json()
    assert estado["positions"] == [], "qty negativo não pode virar posição"
    assert estado["cash"] == 10000.0, "rejeição não pode mover dinheiro"
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada"
    assert entry["type"] == "COMPRA"
    assert entry["price"] is None, "nunca 0 nem 0.0 — CLAUDE.md item 4"


def test_buy_qty_zero_400_auditoria_a00(monkeypatch):
    """A-00, mesmo caminho com `qty=0`: zero é falsy em Python, então
    `int(body.get("qty") or 0)` o tratava como campo ausente e a compra saía
    com o lote mínimo. Zero EXPLÍCITO é rejeição, não default."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "buy-qtyzero@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(30.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 0}, headers=headers)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Quantidade inválida."

    estado = client.get("/api/state", headers=headers).json()
    assert estado["positions"] == [], "qty=0 não pode virar compra de lote mínimo"
    assert estado["cash"] == 10000.0, "rejeição não pode mover dinheiro"
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada" and entry["type"] == "COMPRA"


def test_buy_qty_nao_inteiro_400_auditoria_a00b(monkeypatch):
    """A-00b (ALTO): `qty:"abc"` vazava `ValueError` e virava 500 com o texto
    cru da exceção Python no corpo. A venda já devolvia 400 "Quantidade
    inválida." para a MESMA entrada — a compra agora também. Nunca 500."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "buy-qtynaoint@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(30.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": "abc"}, headers=headers)
    assert r.status_code == 400, r.text
    assert r.status_code != 500, "exceção crua nunca chega ao cliente"
    assert r.json()["detail"] == "Quantidade inválida."

    estado = client.get("/api/state", headers=headers).json()
    assert estado["positions"] == []
    assert estado["cash"] == 10000.0, "rejeição não pode mover dinheiro"
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada" and entry["type"] == "COMPRA"


def test_buy_qty_invalida_anonimo_nao_grava_no_balde_compartilhado(monkeypatch):
    """T-05-03/T-04-12: o balde anônimo é compartilhado — a rejeição de A-00
    segue a mesma regra das outras rejeições da rota e não grava nele."""
    client, m = _client_isolado(monkeypatch)
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(30.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": -500})
    assert r.status_code == 400

    estado_anonimo = client.get("/api/state").json()
    assert estado_anonimo["history"] == [], "balde anônimo compartilhado — nunca registra rejeição"
    assert estado_anonimo["positions"] == []


def test_buy_qty_ausente_continua_comprando_lote_minimo_contrato_preservado(monkeypatch):
    """Guardião de CONTRATO (caminho 12), não regressão de A-00: `qty` ausente
    do corpo sempre significou "lote mínimo de 100" nesta rota, e a correção
    de A-00 preserva isso — ela rejeita valor explícito inválido, não muda o
    contrato. Se algum dia o default cair, que caia por decisão explícita."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "buy-qtyausente@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(30.0))

    r = client.post("/api/buy", json={"t": "PETR4"}, headers=headers)
    assert r.status_code == 200, r.text

    estado = client.get("/api/state", headers=headers).json()
    assert estado["positions"][0]["qty"] == 100, "qty ausente = lote mínimo, comportamento de sempre"
    assert estado["cash"] == 7000.0
    assert estado["history"][0]["status"] == "executada"


# ===========================================================================
# Caminhos 13 e 14 — rotas de OPÇÃO (auditoria A-09 e resto do A-00b,
# 2026-09-11). Espelham os caminhos de ação: o 13 é o mesmo 400 de posição
# inexistente que `/api/sell` já levantava, o 14 é a mesma guarda de `qty` não
# numérico que a quick 260910-mqs pôs em `/api/buy`.
# ===========================================================================

_EXP_OPCAO = "2026-10-30"


def _chain_opcao(symbol="PETRK30", price=1.5):
    """Cadeia sintética no formato ADR-004 (mesmo shape de
    `test_gate_liquidez_rotas.py::_chain`), com UM contrato negociável."""
    return {"providerStatus": "ok", "underlyingPrice": 30.0, "expiration": _EXP_OPCAO,
            "expirations": [_EXP_OPCAO], "puts": [],
            "calls": [{"contractSymbol": symbol, "optionType": "call", "strike": 30.0,
                        "lastPrice": price, "bid": price, "ask": price, "volume": 5000,
                        "openInterest": 3000, "impliedVolatility": 0.3,
                        "expiration": _EXP_OPCAO}]}


def test_options_sell_posicao_sumida_400_auditoria_a09(monkeypatch):
    """A-09: a rota lê `pos` ANTES do `await` da cadeia de opções. Se a posição
    desaparecer no intervalo (vencimento liquidado pelo scheduler, venda por
    outro caminho), `store.sell_option` devolve `None` e a rota devolvia
    **200 com `priceUsed`** — o cliente registrava uma venda que não
    aconteceu (princípio 9).

    A corrida é reproduzida de verdade, sem mockar `store`: o fake de
    `get_options` liquida a posição por fora DENTRO do `await`, que é
    exatamente a janela do achado."""
    client, m = _client_isolado(monkeypatch)
    token, uid = _registrar(client, "optsell-sumida@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    chain = _chain_opcao()

    async def _chain_ok(*a, **k):
        return chain
    monkeypatch.setattr(m.options_provider, "get_options", _chain_ok)

    r = client.post("/api/options/buy",
                    json={"underlying": "PETR4", "contractSymbol": "PETRK30", "qty": 100},
                    headers=headers)
    assert r.status_code == 200, r.text
    assert client.get("/api/state", headers=headers).json()["cash"] == 9850.0

    async def _chain_e_liquida_por_fora(*a, **k):
        # o scheduler fecha o contrato enquanto a rota espera a cotação
        m.store.sell_option(m._conn, "PETRK30", 1.5, user_id=uid,
                            motivo="vencimento", origem="sistema")
        return chain
    monkeypatch.setattr(m.options_provider, "get_options", _chain_e_liquida_por_fora)

    r = client.post("/api/options/sell", json={"contractSymbol": "PETRK30"}, headers=headers)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Sem posição em PETRK30"
    assert "priceUsed" not in r.json(), "nunca devolver preço de execução de venda que não ocorreu"

    estado = client.get("/api/state", headers=headers).json()
    vendas = [h for h in estado["history"] if h["type"] == "VENDA"]
    assert len(vendas) == 1, "só a liquidação por fora existe — a rota não pode registrar a 2ª venda"
    assert vendas[0]["motivo"] == "vencimento"
    assert estado["optionPositions"] == []
    assert estado["cash"] == 10000.0, "o prêmio só pode ser creditado UMA vez"


def test_options_buy_qty_nao_inteiro_400_resto_do_a00b(monkeypatch):
    """Resto do A-00b: `qty:"abc"` em `/api/options/buy` levantava `ValueError`
    sem tratamento e virava 500 com o texto cru da exceção. Cai na MESMA
    mensagem de 400 que `qty` ausente/zero/negativo já recebia — e ANTES de
    buscar a cadeia, para um pedido inválido não queimar requisição do
    provedor de opções."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "optbuy-qtynaoint@boris.dev")
    headers = {"authorization": f"Bearer {token}"}

    chamadas = []

    async def _nunca(*a, **k):
        chamadas.append(a)
        return _chain_opcao()
    monkeypatch.setattr(m.options_provider, "get_options", _nunca)

    r = client.post("/api/options/buy",
                    json={"underlying": "PETR4", "contractSymbol": "PETRK30", "qty": "abc"},
                    headers=headers)
    assert r.status_code == 400, r.text
    assert r.status_code != 500, "exceção crua nunca chega ao cliente"
    assert r.json()["detail"] == "Contrato de opção inválido."
    assert chamadas == [], "pedido inválido não busca cadeia de opções"

    estado = client.get("/api/state", headers=headers).json()
    assert estado["optionPositions"] == []
    assert estado["cash"] == 10000.0, "rejeição não pode mover dinheiro"


def test_options_buy_qty_ausente_e_zero_continuam_400_contrato_preservado(monkeypatch):
    """Guardião de CONTRATO: ao contrário de `/api/buy`, nesta rota `qty`
    ausente NUNCA significou "lote mínimo" — sempre foi rejeição (`or 0` +
    `qty <= 0`). A correção do A-00b não pode ter criado um default novo."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "optbuy-qtyausente@boris.dev")
    headers = {"authorization": f"Bearer {token}"}

    async def _chain_ok(*a, **k):
        return _chain_opcao()
    monkeypatch.setattr(m.options_provider, "get_options", _chain_ok)

    for corpo in ({"underlying": "PETR4", "contractSymbol": "PETRK30"},
                  {"underlying": "PETR4", "contractSymbol": "PETRK30", "qty": 0},
                  {"underlying": "PETR4", "contractSymbol": "PETRK30", "qty": -500}):
        r = client.post("/api/options/buy", json=corpo, headers=headers)
        assert r.status_code == 400, (corpo, r.text)
        assert r.json()["detail"] == "Contrato de opção inválido."

    estado = client.get("/api/state", headers=headers).json()
    assert estado["optionPositions"] == []
    assert estado["cash"] == 10000.0


# ===========================================================================
# Caminhos 15, 16 e 17 — /api/options/sell com `qty` inválida (auditoria D-1,
# 2026-09-11). Espelham os caminhos 8 e 9 da venda de AÇÃO: a venda de opção
# era a QUARTA e última rota da família ainda com a armadilha do falsy de
# F10-20260819. O caminho 17 trava o contrato que a correção preservou.
# ===========================================================================

def _monta_posicao_opcao(client, m, monkeypatch, headers, qty=200, price=1.5):
    """Compra `qty` na opção sintética e devolve o estado pós-compra."""
    async def _chain_ok(*a, **k):
        return _chain_opcao(price=price)
    monkeypatch.setattr(m.options_provider, "get_options", _chain_ok)
    r = client.post("/api/options/buy",
                    json={"underlying": "PETR4", "contractSymbol": "PETRK30", "qty": qty},
                    headers=headers)
    assert r.status_code == 200, r.text
    return client.get("/api/state", headers=headers).json()


def test_options_sell_qty_zero_400_d1_mesma_armadilha_f10_20260819(monkeypatch):
    """D-1: `int(_qty) if _qty else None` tratava `qty=0` (falsy em Python)
    como "campo ausente", e campo ausente nesta rota significa venda TOTAL —
    pedir zero liquidava o contrato INTEIRO em silêncio, creditando o prêmio
    de toda a posição. Mesma regressão que F10-20260819 fechou em `/api/sell`.

    A asserção que decide: a posição fica INTACTA. Só o 400 não bastaria —
    é a venda total que precisa provar que não aconteceu."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "optsell-qtyzero@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    estado_compra = _monta_posicao_opcao(client, m, monkeypatch, headers)
    assert estado_compra["optionPositions"][0]["qty"] == 200
    assert estado_compra["cash"] == 9700.0

    r = client.post("/api/options/sell", json={"contractSymbol": "PETRK30", "qty": 0},
                    headers=headers)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Quantidade inválida."
    assert "priceUsed" not in r.json(), "nunca devolver preço de execução de venda que não ocorreu"

    estado = client.get("/api/state", headers=headers).json()
    assert estado["optionPositions"][0]["qty"] == 200, \
        "qty=0 não pode virar venda total silenciosa (D-1 / F10-20260819)"
    assert estado["cash"] == 9700.0, "rejeição não pode creditar prêmio nenhum"
    assert [h for h in estado["history"] if h["type"] == "VENDA" and h.get("status") != "rejeitada"] == [], \
        "nenhuma venda executada pode existir no histórico"
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada" and entry["type"] == "VENDA"
    assert entry["t"] == "PETRK30", "rejeição de opção grava o contractSymbol como `t`"
    assert entry["pnl"] is None


def test_options_sell_qty_negativo_400_d1(monkeypatch):
    """D-1, o caso mais traiçoeiro: `-500` é TRUTHY, então passava pelo `if
    _qty` e chegava em `store.sell_option` como `qty=-500` — que só honra
    `qty > 0` e, para qualquer outro valor, vende a posição INTEIRA. O
    negativo dava exatamente o mesmo estrago do zero, por um caminho
    diferente."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "optsell-qtyneg@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _monta_posicao_opcao(client, m, monkeypatch, headers)

    r = client.post("/api/options/sell", json={"contractSymbol": "PETRK30", "qty": -500},
                    headers=headers)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Quantidade inválida."

    estado = client.get("/api/state", headers=headers).json()
    assert estado["optionPositions"][0]["qty"] == 200, "qty negativo não pode virar venda total"
    assert estado["cash"] == 9700.0, "rejeição não pode creditar prêmio nenhum"
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada" and entry["type"] == "VENDA"


def test_options_sell_qty_nao_inteiro_400_d1(monkeypatch):
    """D-1: `int("abc")` levantava `ValueError` sem tratamento e virava 500
    com o texto cru da exceção no corpo — mesmo vazamento que a quick
    260910-mqs fechou em `/api/buy` e a 260911-15a em `/api/options/buy`.
    Cai na MESMA mensagem de 400 das outras três rotas. Nunca 500."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "optsell-qtynaoint@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _monta_posicao_opcao(client, m, monkeypatch, headers)

    r = client.post("/api/options/sell", json={"contractSymbol": "PETRK30", "qty": "abc"},
                    headers=headers)
    assert r.status_code == 400, r.text
    assert r.status_code != 500, "exceção crua nunca chega ao cliente"
    assert r.json()["detail"] == "Quantidade inválida."

    estado = client.get("/api/state", headers=headers).json()
    assert estado["optionPositions"][0]["qty"] == 200, "posição não pode mudar numa rejeição"
    assert estado["cash"] == 9700.0
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada" and entry["type"] == "VENDA"


def test_options_sell_qty_invalida_anonimo_nao_grava_no_balde_compartilhado(monkeypatch):
    """T-02-07/T-05-03: esta rota não registrava rejeição nenhuma antes de
    D-1 — a correção introduz a PRIMEIRA chamada de `registrar_rejeicao`
    aqui, então precisa nascer com a mesma regra das outras: o balde anônimo é
    compartilhado entre todos os usuários sem login e nunca recebe rejeição."""
    client, m = _client_isolado(monkeypatch)
    _monta_posicao_opcao(client, m, monkeypatch, headers={})

    r = client.post("/api/options/sell", json={"contractSymbol": "PETRK30", "qty": 0})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Quantidade inválida."

    estado_anonimo = client.get("/api/state").json()
    # o histórico do balde anônimo NÃO está vazio (a compra de montagem está
    # lá, executada) — o que não pode aparecer é a REJEIÇÃO.
    assert [h for h in estado_anonimo["history"] if h.get("status") == "rejeitada"] == [], \
        "balde anônimo compartilhado — nunca registra rejeição"
    assert estado_anonimo["optionPositions"][0]["qty"] == 200, "posição do anônimo também fica intacta"


def test_options_sell_qty_ausente_continua_vendendo_tudo_contrato_preservado(monkeypatch):
    """Guardião de CONTRATO (caminho 17), não regressão de D-1: `qty` AUSENTE
    do corpo sempre significou venda TOTAL nesta rota, e é o único caminho que
    a tela usa hoje (`optionsSell` não monta `qty`). A correção de D-1 rejeita
    valor explícito inválido — ela NÃO pode ter transformado ausente em
    rejeição nem em venda parcial. Se um dia esse contrato mudar, que mude por
    decisão explícita, com este teste atualizado junto."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "optsell-qtyausente@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _monta_posicao_opcao(client, m, monkeypatch, headers)

    r = client.post("/api/options/sell", json={"contractSymbol": "PETRK30"}, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["priceUsed"] == 1.5

    estado = client.get("/api/state", headers=headers).json()
    assert estado["optionPositions"] == [], "qty ausente = venda TOTAL, comportamento de sempre"
    assert estado["cash"] == 10000.0, "prêmio dos 200 creditado de volta"
    entry = estado["history"][0]
    assert entry["type"] == "VENDA" and entry["qty"] == 200
    assert entry["motivo"] == "manual" and entry["kind"] == "opcao"


def test_options_sell_qty_parcial_valida_continua_funcionando(monkeypatch):
    """Contraprova da guarda: ela barra só o inválido. `qty=100` sobre uma
    posição de 200 continua sendo venda PARCIAL — o caminho legítimo não pode
    ter sido fechado junto."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "optsell-qtyparcial@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _monta_posicao_opcao(client, m, monkeypatch, headers)

    r = client.post("/api/options/sell", json={"contractSymbol": "PETRK30", "qty": 100},
                    headers=headers)
    assert r.status_code == 200, r.text

    estado = client.get("/api/state", headers=headers).json()
    assert estado["optionPositions"][0]["qty"] == 100, "metade vendida, metade preservada"
    assert estado["cash"] == 9850.0
    assert estado["history"][0]["qty"] == 100
