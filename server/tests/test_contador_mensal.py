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
