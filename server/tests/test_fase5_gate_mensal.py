"""Fase 5 (FIX-C33) — guardião do ledger MENSAL de `metering.py` e do call
site do gate de plano em `main.py::_gate_analise`.

Fecha a lacuna estrutural apontada em `plan.py` (contrato de contagem): antes
desta fase, `_gate_analise` chamava `plan.can_analyze(0, plan=plano)` com o
literal `0` hardcoded — inofensivo enquanto `max_analyses_per_month` é
`None` (nenhum limite comercial ativo), mas quebraria silenciosamente no dia
em que o ADR-010 populasse o número (o gate compararia `0 >= limite` sempre,
liberando ou bloqueando todo mundo dependendo da ordem de comparação).

O que este arquivo trava:
  - `metering.month_used` num banco novo devolve 0;
  - `consume()` incrementa o acumulado mensal (respeitando `custo`);
  - a virada de DIA NÃO zera o acumulado do MÊS (registro próprio,
    `MONTH_SECTION`, separado do diário — a classe de bug que existiria se
    o mês vivesse dentro do dict que `_load` zera a cada dia novo);
  - a virada de MÊS zera o acumulado (mês novo começa em 0);
  - o acumulado é isolado por escopo (`user_id`);
  - `_gate_analise` passa o inteiro REAL do ledger a `plan.can_analyze`, não
    mais `0` — guardião de rota (espião) + guardião ESTÁTICO (regex no
    fonte) fechando a CLASSE do erro, não só a instância;
  - `/api/ai/quota` expõe `monthUsed` (inteiro p/ conta logada, `None` p/
    escopo anônimo).

Isolamento igual a `test_fase3_gate_plano.py` (B3_DB_PATH temporário,
reimport de `app.main` por teste, reset dos caches em memória entre casos).
"""
import importlib
import os
import pathlib
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import db, metering


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_gate_mensal_test_")
    return db.connect(os.path.join(d, "b3_agente.db"))


# ---------------------------------------------------------------------------
# (a)-(e) metering.month_used / consume / rollover / isolamento — unitário
# ---------------------------------------------------------------------------

def test_month_used_banco_novo_devolve_zero():
    conn = _fresh_db()
    assert metering.month_used(conn, "u1") == 0
    conn.close()


def test_consume_incrementa_o_acumulado_mensal_respeitando_custo():
    conn = _fresh_db()
    metering.consume(conn, "u1")
    assert metering.month_used(conn, "u1") == 1
    metering.consume(conn, "u1", custo=5)
    assert metering.month_used(conn, "u1") == 6
    conn.close()


def test_virada_de_dia_nao_zera_o_acumulado_do_mes(monkeypatch):
    conn = _fresh_db()
    metering.consume(conn, "u1", custo=3)
    assert metering.month_used(conn, "u1") == 3
    # simula virada de DIA, mesmo mês — o acumulado mensal tem de sobreviver
    monkeypatch.setattr(metering, "_today", lambda: "2026-08-24")
    assert metering.month_used(conn, "u1") == 3
    conn.close()


def test_virada_de_mes_zera_o_acumulado(monkeypatch):
    conn = _fresh_db()
    metering.consume(conn, "u1", custo=7)
    assert metering.month_used(conn, "u1") == 7
    monkeypatch.setattr(metering, "_month", lambda: "2099-01")
    assert metering.month_used(conn, "u1") == 0
    conn.close()


def test_acumulado_mensal_isolado_por_escopo():
    conn = _fresh_db()
    metering.consume(conn, "a", custo=4)
    assert metering.month_used(conn, "a") == 4
    assert metering.month_used(conn, "b") == 0
    conn.close()


def test_snapshot_expoe_month_e_month_used():
    conn = _fresh_db()
    metering.consume(conn, "u1", custo=2)
    snap = metering.snapshot(conn, "u1", quota=10)
    assert snap["monthUsed"] == 2
    assert snap["month"] == metering._month()
    conn.close()


# ---------------------------------------------------------------------------
# (f)-(g) _gate_analise / /api/ai/quota — rota real via TestClient
# ---------------------------------------------------------------------------

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
    d = tempfile.mkdtemp(prefix="b3_gate_mensal_test_")
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


def test_gate_analise_passa_o_inteiro_real_do_ledger_nao_zero(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "gate@teste.com")
    scope = payload["user"]["id"]
    main.metering.consume(main._conn, scope, custo=4)  # monta estado: 4 análises já no mês

    espiao = {}

    def _spy(used_this_month, plan=None):
        espiao["used"] = used_this_month
        return (True, None)
    monkeypatch.setattr(main.plan, "can_analyze", _spy)

    main._gate_analise(scope, {})
    assert espiao["used"] == 4, "gate tem de receber a contagem real do ledger, não 0"


def test_gate_analise_escopo_anonimo_recebe_zero_do_ledger_nao_hardcoded(monkeypatch):
    """Escopo anônimo (`scope=None`) também resolve via `metering.month_used`
    — que devolve 0 para o balde sem user_id — não por um literal `0` fixo
    no call site (a diferença importa: com o número comercial ativo, um
    usuário que JÁ tivesse consumido no balde anônimo não poderia ser
    ignorado silenciosamente por um `0` hardcoded)."""
    c, main = _client(monkeypatch)

    espiao = {}

    def _spy(used_this_month, plan=None):
        espiao["used"] = used_this_month
        return (True, None)
    monkeypatch.setattr(main.plan, "can_analyze", _spy)

    main._gate_analise(None, {})
    assert espiao["used"] == 0


def test_ai_quota_conta_logada_devolve_month_used_inteiro(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "quota@teste.com")
    scope = payload["user"]["id"]
    main.metering.consume(main._conn, scope, custo=3)

    r = c.get("/api/ai/quota", headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["monthUsed"] == 3
    assert body["monthLimit"] is None  # ADR-010 pendente, nenhum limite comercial ativo


def test_ai_quota_escopo_anonimo_devolve_month_used_none(monkeypatch):
    c, main = _client(monkeypatch)
    r = c.get("/api/ai/quota")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["monthUsed"] is None
    assert body["monthLimit"] is None


# ---------------------------------------------------------------------------
# (h) guardião ESTÁTICO — fecha a CLASSE do erro, não só a instância
# ---------------------------------------------------------------------------

def _main_source_sem_comentarios() -> str:
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    return "\n".join(line for line in src.splitlines() if not line.strip().startswith("#"))


def test_main_py_nao_contem_mais_can_analyze_com_zero_hardcoded():
    assert "can_analyze(0" not in _main_source_sem_comentarios()


def test_plan_can_analyze_continua_aparecendo_exatamente_uma_vez_no_main():
    """Guardião pré-existente de `test_fase3_gate_plano.py` — repetido aqui
    porque esta mudança é justamente a que edita a linha que ele trava; se
    ele quebrasse, é aqui que veríamos primeiro."""
    assert _main_source_sem_comentarios().count("plan.can_analyze(") == 1
