"""Fase 3, C-35 — guardião do kill-switch do `timing_watch` (push do gatilho).

Origem: `timing_watch.kill_switch_on()` lia SÓ a env `B3_TIMING_PUSH_KILL`,
nenhuma das abas do portal admin mostrava o estado, e nenhuma rota o expunha
— se ligado por engano, o aviso de gatilho parava para TODA a base e o único
caminho de volta era redeploy. É o mesmo padrão de risco que já produziu o
incidente do kill-switch do agente (ligado sem querer, execução automática
parada por 2,5 dias) — REPORT-01 C-35.

Este arquivo cobre DUAS camadas:
  - Task 1 (unidade, sem HTTP): precedência memória→DB→env, persistência
    entre "processos" (configure_db + reset_kill_switch_cache), tolerância
    do falha do SQLite, funcionamento sem configure_db.
  - Task 2 (rota HTTP, via TestClient): RBAC das duas rotas admin, efeito
    imediato do PUT, audit log na transição, campo em /api/agent/status.
"""
import importlib
import os
import sys
import tempfile

import pytest

from app import db, timing_watch


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_timing_watch_kill_test_")
    path = os.path.join(d, "b3_agente.db")
    return db.connect(path)


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    timing_watch.reset_kill_switch_cache()
    monkeypatch.delenv("B3_TIMING_PUSH_KILL", raising=False)
    yield
    timing_watch.reset_kill_switch_cache()
    monkeypatch.delenv("B3_TIMING_PUSH_KILL", raising=False)
    # devolve o módulo a um estado "sem DB" para não vazar pros próximos testes
    timing_watch._DB_CONN = None
    timing_watch._DB_ENABLED = False


def test_sem_override_e_sem_env_e_desligado():
    assert timing_watch.kill_switch_on() is False


def test_env_liga_sem_override(monkeypatch):
    monkeypatch.setenv("B3_TIMING_PUSH_KILL", "1")
    assert timing_watch.kill_switch_on() is True


def test_env_em_runtime_tem_efeito_imediato_sem_cache(monkeypatch):
    """O resultado do ENV nunca é cacheado em `_KILL_MEM` — mudar a env em
    runtime, sem passar por `set_kill_switch`, tem que valer na hora."""
    assert timing_watch.kill_switch_on() is False
    monkeypatch.setenv("B3_TIMING_PUSH_KILL", "1")
    assert timing_watch.kill_switch_on() is True
    monkeypatch.delenv("B3_TIMING_PUSH_KILL", raising=False)
    assert timing_watch.kill_switch_on() is False


def test_env_aceita_variantes_tolerantes(monkeypatch):
    """Ampliação deliberada (C-35): alinhar com `agent.kill_switch_on`, mais
    tolerante que o `== \"1\"` original do timing_watch."""
    for valor in ("1", "true", "TRUE", "yes"):
        timing_watch.reset_kill_switch_cache()
        monkeypatch.setenv("B3_TIMING_PUSH_KILL", valor)
        assert timing_watch.kill_switch_on() is True, valor
    timing_watch.reset_kill_switch_cache()
    monkeypatch.setenv("B3_TIMING_PUSH_KILL", "0")
    assert timing_watch.kill_switch_on() is False


def test_set_kill_switch_tem_efeito_imediato_na_memoria():
    conn = _fresh_db()
    timing_watch.configure_db(conn)
    assert timing_watch.set_kill_switch(True, actor="u1") is True
    assert timing_watch.kill_switch_on() is True


def test_override_persiste_para_processo_novo():
    """Após set_kill_switch(True), um processo novo (novo connect +
    configure_db + reset_kill_switch_cache) lê True do banco mesmo sem env."""
    d = tempfile.mkdtemp(prefix="b3_timing_watch_kill_test_")
    path = os.path.join(d, "b3_agente.db")
    conn1 = db.connect(path)
    timing_watch.configure_db(conn1)
    timing_watch.set_kill_switch(True, actor="u1")

    # simula processo novo: reconecta e reseta o cache em memória
    timing_watch.reset_kill_switch_cache()
    conn2 = db.connect(path)
    timing_watch.configure_db(conn2)
    assert timing_watch.kill_switch_on() is True


def test_override_do_banco_tem_precedencia_sobre_a_env(monkeypatch):
    conn = _fresh_db()
    timing_watch.configure_db(conn)
    timing_watch.set_kill_switch(False, actor="u1")
    timing_watch.reset_kill_switch_cache()
    monkeypatch.setenv("B3_TIMING_PUSH_KILL", "1")
    # o override False do DB tem que prevalecer sobre a env ligada
    assert timing_watch.kill_switch_on() is False


def test_falha_do_sqlite_na_leitura_nao_propaga_e_cai_pro_env(monkeypatch):
    conn = _fresh_db()
    timing_watch.configure_db(conn)

    def _explode(*a, **kw):
        raise RuntimeError("SQLite indisponível (simulado)")

    monkeypatch.setattr(db, "admin_config_get", _explode)
    # sem env => cai no default (False); a exceção não propaga
    assert timing_watch.kill_switch_on() is False


def test_falha_do_sqlite_na_escrita_nao_impede_efeito_em_memoria(monkeypatch):
    conn = _fresh_db()
    timing_watch.configure_db(conn)

    def _explode(*a, **kw):
        raise RuntimeError("SQLite indisponível (simulado)")

    monkeypatch.setattr(db, "admin_config_set", _explode)
    assert timing_watch.set_kill_switch(True, actor="u1") is True
    assert timing_watch.kill_switch_on() is True


def test_sem_configure_db_funciona_so_memoria_env():
    """Teste isolado / boot parcial: sem configure_db, tudo funciona lendo
    só memória→env, sem tentar tocar no SQLite."""
    assert timing_watch._DB_ENABLED is False
    assert timing_watch.kill_switch_on() is False
    assert timing_watch.set_kill_switch(True, actor="u1") is True
    assert timing_watch.kill_switch_on() is True


# ============================================================= Task 2: rotas
@pytest.fixture(autouse=True)
def _isolado_main(monkeypatch):
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


def _client(monkeypatch):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_timing_watch_kill_route_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    from fastapi.testclient import TestClient
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def test_get_com_permissao_ver_retorna_estado(monkeypatch):
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    r = c.get("/api/admin/timing-watch/kill-switch", headers=_auth(admin["token"]))
    assert r.status_code == 200
    assert r.json() == {"on": False}


def test_get_sem_permissao_e_403(monkeypatch):
    c, main = _client(monkeypatch)
    _registra(c, "dono@teste.com")
    comum = _registra(c, "comum@teste.com")
    r = c.get("/api/admin/timing-watch/kill-switch", headers=_auth(comum["token"]))
    assert r.status_code == 403


def test_put_com_permissao_controlar_liga_na_hora(monkeypatch):
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    h = _auth(admin["token"])
    assert main.timing_watch.kill_switch_on() is False
    r = c.put("/api/admin/timing-watch/kill-switch", json={"on": True}, headers=h)
    assert r.status_code == 200 and r.json()["on"] is True
    assert main.timing_watch.kill_switch_on() is True


def test_put_sem_permissao_controlar_e_403(monkeypatch):
    """O gate real é do backend — não a UI escondendo o botão. `execucao_
    automatica` é um grupo atômico neste RBAC (concede `.ver` e `.controlar`
    juntos, sem grão mais fino) — o caso relevante é: quem NÃO tem o grupo
    (0 permissões, o mesmo estado de um usuário comum) apanha 403 tanto no
    GET quanto no PUT, exatamente como o par do agente já garante."""
    c, main = _client(monkeypatch)
    _registra(c, "dono@teste.com")
    comum = _registra(c, "comum@teste.com")
    h = _auth(comum["token"])
    assert c.get("/api/admin/timing-watch/kill-switch", headers=h).status_code == 403
    assert c.put("/api/admin/timing-watch/kill-switch", json={"on": True}, headers=h).status_code == 403


def test_transicao_grava_audit_log(monkeypatch):
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    h = _auth(admin["token"])
    c.put("/api/admin/timing-watch/kill-switch", json={"on": True}, headers=h)
    audit = c.get("/api/admin/audit", headers=h).json()["eventos"]
    ev = [e for e in audit if e["entity"] == "timing_watch_kill_switch"]
    assert ev and ev[0]["field"] == "on" and ev[0]["newValue"] is True and ev[0]["oldValue"] is False


def test_sem_transicao_nao_grava_audit_log(monkeypatch):
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    h = _auth(admin["token"])
    # já está desligado; ligar para False de novo não é transição
    c.put("/api/admin/timing-watch/kill-switch", json={"on": False}, headers=h)
    audit = c.get("/api/admin/audit", headers=h).json()["eventos"]
    ev = [e for e in audit if e["entity"] == "timing_watch_kill_switch"]
    assert ev == []


def test_agent_status_expoe_timing_watch_kill_switch(monkeypatch):
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    h = _auth(admin["token"])
    st = c.get("/api/agent/status", headers=h).json()
    assert st["timingWatchKillSwitch"] is False
    c.put("/api/admin/timing-watch/kill-switch", json={"on": True}, headers=h)
    st2 = c.get("/api/agent/status", headers=h).json()
    assert st2["timingWatchKillSwitch"] is True
