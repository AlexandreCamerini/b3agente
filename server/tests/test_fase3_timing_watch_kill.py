"""Fase 3, C-35 — guardião do kill-switch do `timing_watch` (push do gatilho).

Origem: `timing_watch.kill_switch_on()` lia SÓ a env `B3_TIMING_PUSH_KILL`,
nenhuma das abas do portal admin mostrava o estado, e nenhuma rota o expunha
— se ligado por engano, o aviso de gatilho parava para TODA a base e o único
caminho de volta era redeploy. É o mesmo padrão de risco que já produziu o
incidente do kill-switch do agente (ligado sem querer, execução automática
parada por 2,5 dias) — REPORT-01 C-35.

Task 1 (este arquivo, unidade, sem HTTP): precedência memória→DB→env,
persistência entre "processos" (configure_db + reset_kill_switch_cache),
tolerância a falha do SQLite, funcionamento sem configure_db. Task 2 (mesmo
arquivo, rotas HTTP) entra numa segunda leva quando as rotas existirem.
"""
import os
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
