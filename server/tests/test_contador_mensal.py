"""25-01 — o que o CONTADOR MENSAL significa.

`metering.month_used(conn, uid)` e o numero que `plan.can_analyze` le para
decidir o cap comercial (30 analises/mes no PLAN_FREE, ADR-010). Este arquivo
existe para travar o SIGNIFICADO desse numero: ele conta ANALISE DE IA
GERENCIADA, e so isso.

O achado que o produziu (fase 25, mapeamento de 2026-09-12) tinha dois lados:

  (1) `POST /api/analytics/events` chamava `metering.consume` SEM
      `month_section`. O default do modulo e `MONTH_SECTION = "aiUsageMonth"`
      — exatamente o ledger do gate comercial — e o `custo` ali e
      `result["accepted"]`, o tamanho do LOTE. O cliente envia em lotes de ate
      50 (`web/src/analytics.js`), entao uma sessao de uso do app descontava
      dezenas de "analises" de quem nao analisou nada. Medido no banco local
      antes da correcao: as tres contas com ledger no mes tinham `count`
      EXATAMENTE igual ao numero de eventos de telemetria ingeridos — 100% do
      contador era telemetria, 0% era analise.

  (2) tres rotas que gastam IA (`/api/scan/deep`, `/api/carteira-stopalvo` e
      `/api/assistente`) chamam `_ai_apply_managed` direto e pulam o gate
      mensal. A ATIVACAO do gate nessas tres ficou pendente de decisao do
      dono do produto (ver `25-01-SUMMARY.md`): com o ledger contaminado por
      (1), liga-la hoje barraria contas pelo defeito, nao pelo uso. Os casos
      correspondentes estao aqui como `xfail(strict=True)` — passam a FALHAR
      no dia em que a ativacao acontecer, obrigando quem a fizer a tirar a
      marca em vez de esquecer o guardiao.

Isolamento igual a test_plan_gate_byok.py (B3_DB_PATH temporario, reimport de
`app.main` por teste, reset dos caches em memoria entre casos) — `_conn` e os
caches de `managed`/kill-switch/orcamento da brapi sao globais de modulo.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

# Lote com o MESMO tamanho que o cliente usa (`web/src/analytics.js`, MAX=50):
# o numero importa porque o defeito descontava o lote INTEIRO, nao 1.
LOTE = 50

CONFIG_COM_BYOK = {"provider": "anthropic", "model": "claude-sonnet-4-5",
                   "apiKey": "sk-chave-propria-de-teste"}
CONFIG_SEM_BYOK = {"provider": "anthropic", "model": "claude-sonnet-4-5"}

ENV_GERENCIADA = {"B3_MANAGED_LLM_KEY": "chave-do-servidor-de-teste",
                  "B3_MANAGED_LLM_PROVIDER": "openai",
                  "B3_MANAGED_LLM_MODEL": "gpt-4o-mini"}


@pytest.fixture(autouse=True)
def _isolado():
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
    d = tempfile.mkdtemp(prefix="b3_contador_mensal_test_")
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


def _eventos(n):
    return [{"event": "tela_aberta", "properties": {"tela": "radar"}} for _ in range(n)]


# ---------------------------------------------------------------------------
# (1) TELEMETRIA NAO E ANALISE — o defeito medido
# ---------------------------------------------------------------------------

def test_lote_de_analytics_nao_move_o_contador_mensal(monkeypatch):
    """RED contra o codigo anterior: `month_used` ia de 0 para 50 sem que o
    usuario tivesse pedido uma analise sequer."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "telemetria@teste.com")
    uid = payload["user"]["id"]
    assert main.metering.month_used(main._conn, uid) == 0

    r = c.post("/api/analytics/events", json={"events": _eventos(LOTE)},
               headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    assert r.json()["accepted"] == LOTE

    assert main.metering.month_used(main._conn, uid) == 0, (
        "telemetria consumiu cota de ANALISE — o ledger que `plan.can_analyze` "
        "le e o `aiUsageMonth`, e sem `month_section` propria o `consume` da "
        "rota de analytics cai nele com o tamanho do lote como custo")


def test_lote_de_analytics_conta_no_ledger_MENSAL_proprio(monkeypatch):
    """A telemetria continua contada — em balde proprio. Sem esta assercao a
    correcao poderia ser 'parar de contar', que e outro defeito."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "telemetriames@teste.com")
    uid = payload["user"]["id"]

    c.post("/api/analytics/events", json={"events": _eventos(LOTE)},
           headers=_auth(payload["token"]))

    assert main.metering.month_used(
        main._conn, uid, section=main.ANALYTICS_MONTH_SECTION) == LOTE


def test_lote_de_analytics_continua_contando_no_ledger_DIARIO(monkeypatch):
    """O rate limit da rota (429, protecao contra flood) nao pode ter sido
    desligado por engano — ele le a secao DIARIA, que nao muda de nome."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "telemetriadia@teste.com")
    uid = payload["user"]["id"]

    c.post("/api/analytics/events", json={"events": _eventos(LOTE)},
           headers=_auth(payload["token"]))

    assert main.metering.used(
        main._conn, uid, section=main.ANALYTICS_SECTION) == LOTE


def test_nomes_das_secoes_de_analytics_nao_mudaram(monkeypatch):
    """Historico gravado no kv: renomear a secao perderia o contador de quem
    ja usa o app. As duas antigas sao literais de contrato, nao escolha."""
    _c, main = _client(monkeypatch)
    assert main.ANALYTICS_SECTION == "analyticsEvents"
    assert main.ANALYTICS_GLOBAL_SECTION == "analyticsEventsGlobal"
    assert main.ANALYTICS_MONTH_SECTION == "analyticsEventsMonth"
    assert main.ANALYTICS_MONTH_SECTION != main.metering.MONTH_SECTION, (
        "o ledger mensal da telemetria nao pode ser o mesmo do gate comercial")


# ---------------------------------------------------------------------------
# (2) AS TRES ROTAS ORFAS — pendente de decisao (ver 25-01-SUMMARY.md)
#
# `/api/scan/deep`, `/api/carteira-stopalvo` e `/api/assistente` chamam
# `_ai_apply_managed` direto: CONTAM no ledger mensal (o `consume` do ramo
# gerenciado usa o `MONTH_SECTION` default) mas nao passam pelo gate do plano,
# entao a conta gasta acima do cap sem ser barrada. As tres assercoes abaixo
# descrevem o estado ALVO. Ficam `xfail(strict=True)` porque a ativacao do
# gate foi medida e devolvida como decisao do dono do produto: com o ledger
# contaminado pelo defeito (1), ligar hoje barraria contas pela telemetria
# delas, nao pelo uso. Strict de proposito — no dia da ativacao estes testes
# passam a FALHAR por XPASS, obrigando quem ativar a tirar a marca.
# ---------------------------------------------------------------------------
PENDENTE = ("ativacao do gate mensal nas tres rotas orfas esta pendente de "
            "decisao (25-01, Task 2): o ledger do mes corrente esta "
            "contaminado por telemetria e barraria pelo defeito, nao pelo uso")

LEDGER_ESTOURADO = 100
MENSAGEM_LIMITE_FREE = "Voce atingiu o limite de 30 analises/mes do plano free."


def _conta_com_ledger(c, main, email, n=LEDGER_ESTOURADO):
    """Semeia SO o ledger MENSAL.

    `consume` grava dia + global + mes na MESMA chamada, e semear o mes por
    ele leva o contador DIARIO junto. Com a IA gerenciada ligada, `custo=100`
    estoura o teto de 20/dia da chave do servidor e a rota responde 402 pelo
    teto FISICO — nao pelo cap COMERCIAL de 30/mes, que e o que esta sob
    teste. Os dois 402 sao indistinguiveis pelo status: so a mensagem separa.
    `_dia` fixo no passado resolve na raiz — o registro diario nasce obsoleto
    e `_load` devolve zerado para hoje."""
    payload = _registra(c, email)
    scope = payload["user"]["id"]
    if n:  # `consume` faz `max(1, custo)` — pedir 0 gravaria 1
        main.metering.consume(main._conn, scope, custo=n, _dia="1999-01-01")
    assert main.metering.month_used(main._conn, scope) == n
    assert main.metering.used(main._conn, scope) == 0, (
        "o ledger DIARIO tem de ficar limpo — senao o teste mede o teto fisico")
    return payload, scope


async def _quote_fake(_t):
    return {"t": "PETR4", "name": "Petrobras PN", "price": 35.5, "change": 0.5}


async def _snap_fake(*_a, **_k):
    return {
        "context": {"setupsRadar": {}, "trend": {}, "volatility": {}, "levels": {}},
        "asOf": "2026-09-12", "barraEmFormacao": None, "candles": [],
        "currency": "BRL", "period": "1y", "snapshotId": "fake0001", "periodBars": [],
    }


@pytest.mark.xfail(strict=True, reason=PENDENTE)
def test_scan_deep_barra_quando_o_mes_estourou(monkeypatch):
    c, main = _client(monkeypatch)
    payload, _scope = _conta_com_ledger(c, main, "scandeep@teste.com")

    async def _sem_universo(*_a, **_k):
        return []
    monkeypatch.setattr(main.scanner, "run_scan", _sem_universo)

    r = c.post("/api/scan/deep", json={"config": dict(CONFIG_SEM_BYOK)},
               headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    assert MENSAGEM_LIMITE_FREE in r.text


@pytest.mark.xfail(strict=True, reason=PENDENTE)
def test_carteira_stopalvo_barra_quando_o_mes_estourou(monkeypatch):
    c, main = _client(monkeypatch)
    payload, _scope = _conta_com_ledger(c, main, "stopalvo@teste.com")
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake)
    monkeypatch.setattr(main.technical_snapshot, "get", _snap_fake)

    async def _llm_nunca(*_a, **_k):
        raise AssertionError("a IA foi chamada com o mes estourado")
    monkeypatch.setattr(main.llm, "analyze_carteira", _llm_nunca)

    r = c.post("/api/carteira-stopalvo/PETR4", json={"config": dict(CONFIG_SEM_BYOK)},
               headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    assert MENSAGEM_LIMITE_FREE in r.text


@pytest.mark.xfail(strict=True, reason=PENDENTE)
def test_assistente_barra_quando_o_mes_estourou(monkeypatch):
    c, main = _client(monkeypatch)
    payload, _scope = _conta_com_ledger(c, main, "assistente@teste.com")

    async def _responder_nunca(*_a, **_k):
        raise AssertionError("a IA foi chamada com o mes estourado")
    from app import assistente as assist
    monkeypatch.setattr(assist, "responder", _responder_nunca)

    r = c.post("/api/assistente",
               json={"pergunta": "o que voce acha do meu PETR4 agora, em detalhe?",
                     "tela": "carteira", "config": dict(CONFIG_SEM_BYOK)},
               headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    assert MENSAGEM_LIMITE_FREE in r.text


# ---------------------------------------------------------------------------
# O que JA vale hoje nessas rotas, e que a ativacao nao pode quebrar
# ---------------------------------------------------------------------------

def test_scan_deep_reserva_o_custo_do_top_n_nao_um(monkeypatch):
    """`/api/scan/deep` dispara ate `topN` chamadas de LLM e reserva `custo=n`
    (qa/42). Quando o gate mensal entrar, o MESMO custo tem de ir junto —
    contar 1 onde gasta n trocaria um defeito de medicao por outro."""
    c, main = _client(monkeypatch, env=ENV_GERENCIADA)
    payload, _scope = _conta_com_ledger(c, main, "custon@teste.com", n=0)
    vistos = []

    def _check(*_a, **kw):
        vistos.append(kw.get("custo"))
        return (True, None)
    monkeypatch.setattr(main.metering, "check", _check)

    async def _sem_universo(*_a, **_k):
        return []
    monkeypatch.setattr(main.scanner, "run_scan", _sem_universo)

    c.post("/api/scan/deep", json={"config": dict(CONFIG_SEM_BYOK), "topN": 7},
           headers=_auth(payload["token"]))

    assert vistos and vistos[0] == 7, (
        f"o custo reservado foi {vistos!r} — o gate tem de receber o topN, nao 1")


def test_byok_nao_move_o_contador_mensal_em_nenhuma_das_tres(monkeypatch):
    """O ledger mensal e o da chave do SERVIDOR. Quem traz a propria chave nao
    o move — nem para cima (nao gasta a chave do servidor) nem para baixo."""
    c, main = _client(monkeypatch, env=ENV_GERENCIADA)
    _payload, scope = _conta_com_ledger(c, main, "byoktres@teste.com", n=7)

    for custo in (1, 5):
        _cfg, consume = main._ai_apply_managed(scope, dict(CONFIG_COM_BYOK), custo=custo)
        consume()

    assert main.metering.month_used(main._conn, scope) == 7


def test_as_tres_rotas_ja_CONTAM_no_ledger_mensal_hoje(monkeypatch):
    """Precisao do diagnostico: o defeito (2) e a AUSENCIA DO GATE, nao a
    ausencia de contagem. O `consume` devolvido por `_ai_apply_managed` usa o
    `MONTH_SECTION` default, entao estas rotas ja escrevem no ledger que o
    plano le — elas gastam acima do cap sem serem barradas, e o contador
    registra o excesso. Exercitado por `/api/carteira-stopalvo`, o caminho
    mais curto das tres; o `consume` e o MESMO objeto nas outras duas."""
    c, main = _client(monkeypatch, env=ENV_GERENCIADA)
    payload, scope = _conta_com_ledger(c, main, "contahoje@teste.com", n=0)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake)
    monkeypatch.setattr(main.technical_snapshot, "get", _snap_fake)

    async def _llm_ok(*_a, **_k):
        return {"texto": "resposta de teste"}
    monkeypatch.setattr(main.llm, "analyze_carteira", _llm_ok)

    r = c.post("/api/carteira-stopalvo/PETR4", json={"config": dict(CONFIG_SEM_BYOK)},
               headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    assert main.metering.month_used(main._conn, scope) == 1
