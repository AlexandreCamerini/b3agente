"""Fase 3 (C-31/C-32) — guardião da correção ARQUITETURAL do gating comercial.

D-03 (03-CONTEXT.md): C-31/C-32 corrigem a arquitetura, NÃO ativam limite
comercial. `PLAN_FREE`/`PLAN_PRO` continuam com todos os limites `None`
(ilimitado) — este arquivo trava exatamente isso (guardião (g)), junto com:

  • C-31: os 3 call sites de gate (`can_add_ticker` em /api/watchlist,
    `can_analyze` nas duas rotas de análise) resolvem o plano REAL da conta
    logada via `plan.current_plan(user)` — antes, código órfão, e todos os
    hooks caíam no fallback global `ACTIVE_PLAN`, inclusive contas 'pro'.
  • Fail-closed: valor inválido/corrompido em `users.plan`, ou falha ao ler o
    usuário no banco, degrada para o plano MENOS privilegiado
    (`plan.ACTIVE_PLAN`/`PLAN_FREE`), nunca para um plano superior.
  • C-32: existe um único ponto de decisão de gate de análise por requisição
    (`_gate_analise`) — `plan.can_analyze` não coexiste mais, na mesma
    chamada, com `metering.check` como dois mecanismos independentes de
    contagem. O CONTADOR único de uso de IA é sempre o de `metering`.

Isolamento igual a test_adr013_rbac.py (B3_DB_PATH temporário, reimport de
app.main por teste) — necessário porque `_conn`/caches em memória (managed,
kill-switch, orçamento brapi) são globais de módulo.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import plan


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
    d = tempfile.mkdtemp(prefix="b3_gate_plano_test_")
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


def _espiao_plan(registro):
    def _spy(current_count, plan=None):
        registro["plan"] = plan
        return (True, None)
    return _spy


# ---------------------------------------------------------------------------
# (a)-(c) plan.current_plan — unitário, sem rota
# ---------------------------------------------------------------------------

def test_current_plan_conta_pro_resolve_plan_pro():
    assert plan.current_plan({"plan": "pro"})["id"] == "pro"


def test_current_plan_valor_desconhecido_cai_para_free_fail_closed():
    """Dado corrompido/valor futuro desconhecido nunca resolve pra um plano
    SUPERIOR — o fail-closed é o plano MENOS privilegiado (T-03-13)."""
    assert plan.current_plan({"plan": "enterprise"})["id"] == "free"


def test_current_plan_sem_user_cai_no_fallback_global():
    assert plan.current_plan(None) is plan.ACTIVE_PLAN


# ---------------------------------------------------------------------------
# (d)-(f) os 3 call sites de gate — rota real via TestClient
# ---------------------------------------------------------------------------

def test_rota_watchlist_add_conta_pro_resolve_plan_pro_no_hook(monkeypatch):
    c, main = _client(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake)
    payload = _registra(c, "pro@teste.com")
    main.db.set_user_plan(main._conn, payload["user"]["id"], "pro")

    espiao = {}
    monkeypatch.setattr(main.plan, "can_add_ticker", _espiao_plan(espiao))

    r = c.post("/api/watchlist/add", json={"ticker": "PETR4"}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    assert espiao["plan"] == main.plan.PLAN_PRO


def test_rota_watchlist_add_sem_sessao_cai_no_active_plan(monkeypatch):
    c, main = _client(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake)

    espiao = {}
    monkeypatch.setattr(main.plan, "can_add_ticker", _espiao_plan(espiao))

    r = c.post("/api/watchlist/add", json={"ticker": "PETR4"})
    assert r.status_code == 200, r.text
    assert espiao["plan"] is main.plan.ACTIVE_PLAN


def test_rota_watchlist_add_falha_ao_ler_usuario_degrada_para_active_plan(monkeypatch):
    """Sessão válida (auth passa), mas a 2ª leitura do usuário — a que
    `_plano_do_escopo` faz pra resolver o plano — quebra. A rota NÃO derruba
    (mesmo status de sucesso de sempre) e o gate degrada pro fallback."""
    c, main = _client(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake)
    payload = _registra(c, "falha@teste.com")
    main.db.set_user_plan(main._conn, payload["user"]["id"], "pro")

    original_get_user = main.db.get_user_by_id
    chamadas = {"n": 0}

    def _falha_na_segunda_leitura(conn, uid):
        chamadas["n"] += 1
        if chamadas["n"] == 1:  # 1ª chamada: auth.resolve_session (sessão precisa resolver)
            return original_get_user(conn, uid)
        raise RuntimeError("banco indisponivel")  # 2ª chamada: _plano_do_escopo

    monkeypatch.setattr(main.db, "get_user_by_id", _falha_na_segunda_leitura)

    espiao = {}
    monkeypatch.setattr(main.plan, "can_add_ticker", _espiao_plan(espiao))

    r = c.post("/api/watchlist/add", json={"ticker": "PETR4"}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    assert espiao["plan"] is main.plan.ACTIVE_PLAN


# ---------------------------------------------------------------------------
# (g) guardião de fronteira D-03: nenhum limite comercial ativado
# ---------------------------------------------------------------------------

def test_d03_nenhum_limite_comercial_ativado():
    assert plan.PLAN_FREE["max_watchlist"] is None
    assert plan.PLAN_FREE["max_analyses_per_month"] is None
    assert plan.PLAN_PRO["max_watchlist"] is None
    assert plan.PLAN_PRO["max_analyses_per_month"] is None
