"""Fase 12 (v1.3, ADR-010) — guardião de COMPORTAMENTO do cap mensal de
análises de IA.

D-01 (12-CONTEXT.md, Plano 12-01): `PLAN_FREE["max_analyses_per_month"]`
saiu de `None` para `30`. A fiação (`_gate_analise` -> `plan.can_analyze` ->
`metering.month_used`) já existia desde a Fase 5 (C-33), mas nunca tinha sido
exercitada com um limite REAL — até aqui o gate comparava contra `None` e
sempre liberava. Este arquivo complementa `test_fase5_gate_mensal.py` (que
travou o ledger e o call site quando o limite ainda era `None`) provando o
comportamento com o limite ativo: a 31ª análise do mês é negada, a contagem
que decide vem do ledger real de `metering` (não um contador paralelo,
CAP-03), a conta pro não sofre o limite (CAP-04) e nada mais no app degrada
depois da recusa (CAP-05).

ARMADILHA (FIX-C01, Plano 04-04): as duas rotas de análise NÃO devolvem o
código de erro HTTP que `_gate_analise` levanta internamente ao cliente.
Elas capturam essa exceção e devolvem 200 com `fonte: "deterministico"` e
`iaIndisponivel: {"code": "quota", "mensagem": <motivo>}`. Nenhum teste aqui
assere o status de erro nessas rotas.

Isolamento igual a test_fase3_gate_plano.py/test_fase5_gate_mensal.py/
test_fase12_cap_watchlist.py (B3_DB_PATH temporário, reimport de app.main por
teste) — necessário porque `_conn`/caches em memória (managed, kill-switch,
orçamento brapi) são globais de módulo.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import plan
from app import pregao as pregao_mod


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import agent, brapi_budget, managed
    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, env=None):
    d = tempfile.mkdtemp(prefix="b3_cap_analises_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    for k, v in (env or {}).items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


async def _quote_fake(_t):
    return {"t": "PETR4", "name": "Petrobras PN", "price": 35.5, "change": 0.5}


async def _quotes_fake(tickers):
    return {t: {"t": t, "name": t, "price": 10.0, "change": 0.0} for t in tickers}


# FIX-C01 (Plano 04-04): quando o gate nega, a rota SEGUE até buscar o
# snapshot pra montar o fallback determinístico — sem stub aqui os testes
# de gate abaixo bateriam rede de verdade. Snapshot mínimo, sem setup nem
# indicador (o conteúdo do fallback não é o que estes testes verificam).
async def _fake_snap(*_a, **_k):
    return {
        "context": {"setupsRadar": {}, "trend": {}, "volatility": {}, "levels": {}},
        "asOf": "2026-08-29", "barraEmFormacao": None, "candles": [],
        "currency": "BRL", "period": "1y", "snapshotId": "fake0001", "periodBars": [],
    }


MENSAGEM_LIMITE_FREE = "Voce atingiu o limite de 30 analises/mes do plano free."


def _monta_conta_free_com_ledger(c, main, email, n):
    payload = _registra(c, email)
    scope = payload["user"]["id"]
    main.metering.consume(main._conn, scope, custo=n)
    return payload, scope


def _mocka_rota_analise(monkeypatch, main):
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake)
    monkeypatch.setattr(main.technical_snapshot, "get", _fake_snap)


# ---------------------------------------------------------------------------
# (a)-(b) CAP-02: 31ª análise do mês é negada, nas DUAS rotas
# ---------------------------------------------------------------------------

def test_a_free_ledger_30_analyze_nega_com_mensagem_exata(monkeypatch):
    c, main = _client(monkeypatch)
    _mocka_rota_analise(monkeypatch, main)
    payload, _scope = _monta_conta_free_com_ledger(c, main, "trinta@teste.com", 30)

    r = c.post("/api/analyze/PETR4", json={}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["fonte"] == "deterministico"
    assert body["iaIndisponivel"]["code"] == "quota"
    assert body["iaIndisponivel"]["mensagem"] == MENSAGEM_LIMITE_FREE


def test_b_free_ledger_30_technical_analyze_nega_com_mensagem_exata(monkeypatch):
    c, main = _client(monkeypatch)
    _mocka_rota_analise(monkeypatch, main)
    payload, _scope = _monta_conta_free_com_ledger(c, main, "trintatech@teste.com", 30)

    r = c.post("/api/technical/analyze/PETR4", json={}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["fonte"] == "deterministico"
    assert body["iaIndisponivel"]["code"] == "quota"
    assert body["iaIndisponivel"]["mensagem"] == MENSAGEM_LIMITE_FREE


# ---------------------------------------------------------------------------
# (c) fronteira: 29 análises consumidas ainda libera a 30ª
# ---------------------------------------------------------------------------

def test_c_free_ledger_29_analyze_nao_recebe_mensagem_de_limite_de_plano(monkeypatch):
    c, main = _client(monkeypatch)
    _mocka_rota_analise(monkeypatch, main)
    payload, _scope = _monta_conta_free_com_ledger(c, main, "vinteenove@teste.com", 29)

    r = c.post("/api/analyze/PETR4", json={}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    mensagem = (body.get("iaIndisponivel") or {}).get("mensagem")
    assert mensagem != MENSAGEM_LIMITE_FREE, (
        "com 29 análises consumidas a 30ª ainda é permitida — só a 31ª nega"
    )


# ---------------------------------------------------------------------------
# (d) CAP-03 (critério de sucesso 2 do ROADMAP): é o LEDGER que decide
# ---------------------------------------------------------------------------

def test_d1_gate_analise_recebe_o_inteiro_exato_do_ledger_via_espiao(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "espiao@teste.com")
    scope = payload["user"]["id"]
    main.metering.consume(main._conn, scope, custo=7)

    espiao = {}

    def _spy(used_this_month, plan=None):
        espiao["used"] = used_this_month
        return (True, None)
    monkeypatch.setattr(main.plan, "can_analyze", _spy)

    main._gate_analise(scope, {})
    assert espiao["used"] == 7, "o gate tem de receber a contagem real do ledger, não 0 nem outro número"


def test_d2_ignorar_o_ledger_muda_o_resultado_do_gate(monkeypatch):
    """Mesmo cenário do caso (a) — ledger em 30, deveria negar — mas com
    `metering.month_used` forçado a devolver 0. Se o resultado deixar de ser
    negado, prova que é o ledger (não um número fixo) quem decide."""
    c, main = _client(monkeypatch)
    _mocka_rota_analise(monkeypatch, main)
    payload, _scope = _monta_conta_free_com_ledger(c, main, "ignoraledger@teste.com", 30)
    monkeypatch.setattr(main.metering, "month_used", lambda *_a, **_k: 0)

    r = c.post("/api/analyze/PETR4", json={}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    codigo = (body.get("iaIndisponivel") or {}).get("code")
    assert codigo != "quota", "com month_used forçado a 0 o gate de plano não deveria negar mais"


# ---------------------------------------------------------------------------
# (e)-(f) CAP-04: conta pro não sofre o limite mensal
# ---------------------------------------------------------------------------

def test_e_pro_ledger_30_analyze_nao_e_negada_pelo_gate_de_plano(monkeypatch):
    c, main = _client(monkeypatch)
    _mocka_rota_analise(monkeypatch, main)
    payload, scope = _monta_conta_free_com_ledger(c, main, "pro30@teste.com", 30)
    main.db.set_user_plan(main._conn, scope, "pro")

    r = c.post("/api/analyze/PETR4", json={}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    # NÃO assumir iaIndisponivel is None: sem chave de LLM configurada no
    # ambiente de teste a CHAMADA de IA falha por outro motivo — o que se
    # prova aqui é a ausência da negação por cota/plano, não o sucesso da IA.
    assert (body.get("iaIndisponivel") or {}).get("code") != "quota"


def test_f_can_analyze_unitario_pro_libera_free_nega_com_30(monkeypatch):
    c, main = _client(monkeypatch)
    assert plan.can_analyze(30, plan=plan.PLAN_PRO) == (True, None)
    assert plan.can_analyze(30, plan=plan.PLAN_FREE)[0] is False


# ---------------------------------------------------------------------------
# (g) CAP-05: não-regressão — depois de uma recusa, o resto do app continua
# ---------------------------------------------------------------------------

def test_g_apos_recusa_mensal_resto_do_app_continua_respondendo(monkeypatch):
    c, main = _client(monkeypatch)
    _mocka_rota_analise(monkeypatch, main)
    monkeypatch.setattr(main.candle_provider, "get_quotes", _quotes_fake)
    payload, _scope = _monta_conta_free_com_ledger(c, main, "naoregride@teste.com", 30)

    r_negada = c.post("/api/analyze/PETR4", json={}, headers=_auth(payload["token"]))
    assert r_negada.status_code == 200, r_negada.text
    assert r_negada.json()["iaIndisponivel"]["code"] == "quota"

    r_state = c.get("/api/state", headers=_auth(payload["token"]))
    assert r_state.status_code == 200, r_state.text

    r_quotes = c.get("/api/quotes", params={"symbols": "PETR4"}, headers=_auth(payload["token"]))
    assert r_quotes.status_code == 200, r_quotes.text

    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    r_buy = c.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=_auth(payload["token"]))
    assert r_buy.status_code == 200, r_buy.text
    posicoes = r_buy.json()["positions"]
    pos_petr4 = next((p for p in posicoes if p["t"] == "PETR4"), None)
    assert pos_petr4 is not None and pos_petr4["qty"] == 100

    r_outra_analise = c.post("/api/analyze/PETR4", json={}, headers=_auth(payload["token"]))
    assert r_outra_analise.status_code == 200, r_outra_analise.text
    assert r_outra_analise.json()["fonte"] == "deterministico"


# ---------------------------------------------------------------------------
# (h) /api/ai/quota expõe o número real que a Fase 13 vai exibir
# ---------------------------------------------------------------------------

def test_h_ai_quota_free_logada_devolve_month_limit_30_e_used_real(monkeypatch):
    c, main = _client(monkeypatch)
    payload, _scope = _monta_conta_free_com_ledger(c, main, "quota12@teste.com", 12)

    r = c.get("/api/ai/quota", headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["monthUsed"] == 12
    assert body["monthLimit"] == 30


# ---------------------------------------------------------------------------
# (i) D-06: escopo anônimo — o cap mensal nunca dispara na prática
# ---------------------------------------------------------------------------

def test_i_escopo_anonimo_cap_mensal_nunca_dispara(monkeypatch):
    c, main = _client(monkeypatch)
    # metering.month_used devolve 0 pro balde sem user_id — se _gate_analise
    # levantasse a exceção de negação aqui, este teste falharia com ela
    # não capturada. A chamada direta (sem rota) prova o call site puro.
    config, _consume = main._gate_analise(None, {})
    assert config == {}
