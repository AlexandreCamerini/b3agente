"""Fase 3, C-37 — guardião do alerta ATIVO de kill-switch ligado há N horas.

Origem: o kill-switch do Operador ligado em pregão era um sinal 100%
PASSIVO — só o KPI vermelho na aba Automação denunciava, e alguém precisava
abrir a tela e notar. Foi exatamente esse padrão que produziu o incidente
real: kill-switch ligado sem querer, execução automática de TODA a base
parada por 2,5 dias, heartbeat sempre verde (mascarando "vivo, mas parado"
como "vivo, normal"). Este arquivo cobre:

  - Task 1 (unidade, sem HTTP): `db.user_ids_with_roles`, `db.audit_last`,
    `agent.kill_switch_ligado_desde`, e o hook `agent._alertar_kill_switch`
    (duração conhecida/não-rastreável, gate de pregão, dedupe, reset,
    robustez a exceção, ausência de rota expondo a lista de admins).
  - Task 2 (rota HTTP): payload de `/api/admin/agent/kill-switch` com
    desde/horas/rastreavel.
"""
import asyncio
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

import pytest

from app import agent, audit, db, rbac


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_kill_switch_duracao_test_")
    path = os.path.join(d, "b3_agente.db")
    return db.connect(path)


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    agent.reset_kill_switch_cache()
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    yield
    agent.reset_kill_switch_cache()
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    agent._DB_CONN = None
    agent._DB_ENABLED = False


def _novo_usuario(conn, user_id, email):
    db.insert_user(conn, {
        "id": user_id, "email": email, "provider": "local", "provider_sub": None,
        "pass_hash": None, "name": email.split("@")[0], "created_at": "2026-01-01T00:00:00Z",
    })


def _admin_conn():
    """DB com um usuário admin (role_admin) já concedido — o destinatário
    padrão do alerta."""
    conn = _fresh_db()
    _novo_usuario(conn, "u-admin", "admin@teste.com")
    db.grant_role(conn, "u-admin", rbac.ROLE_ADMIN, "2026-01-01T00:00:00Z", granted_by=None)
    return conn


def _iso_horas_atras(n: float) -> str:
    momento = datetime.now(timezone.utc) - timedelta(hours=n)
    return momento.replace(microsecond=0).isoformat()


class _EspiaPush:
    """Substitui `push.send_to_user`: registra (user_id, titulo, corpo) e
    devolve sent=1 (aparelho fictício sempre entregável), sem HTTP real."""
    def __init__(self):
        self.chamadas = []

    async def __call__(self, conn, user_id, title, body, som=True, prioridade="10",
                        client=None, extra=None):
        self.chamadas.append((user_id, title, body))
        return {"sent": 1, "total": 1, "detalhes": []}


# ============================================================ db.py: consultas
def test_user_ids_with_roles_lista_distintos_por_qualquer_papel():
    conn = _fresh_db()
    _novo_usuario(conn, "u1", "a@teste.com")
    _novo_usuario(conn, "u2", "b@teste.com")
    _novo_usuario(conn, "u3", "c@teste.com")
    db.grant_role(conn, "u1", "role_admin", "2026-01-01T00:00:00Z")
    db.grant_role(conn, "u2", "execucao_automatica", "2026-01-01T00:00:00Z")
    db.grant_role(conn, "u2", "role_admin", "2026-01-01T00:00:00Z")  # u2 tem os dois papéis
    assert sorted(db.user_ids_with_roles(conn, ["role_admin", "execucao_automatica"])) == ["u1", "u2"]


def test_user_ids_with_roles_vazio_quando_ninguem_tem():
    conn = _fresh_db()
    _novo_usuario(conn, "u1", "a@teste.com")
    assert db.user_ids_with_roles(conn, ["role_admin"]) == []


def test_user_ids_with_roles_lista_de_papeis_vazia_devolve_vazio():
    conn = _fresh_db()
    assert db.user_ids_with_roles(conn, []) == []


def test_audit_last_devolve_o_mais_recente_por_entidade_e_campo():
    conn = _fresh_db()
    db.audit_insert(conn, "actor", _iso_horas_atras(2), "agent_kill_switch", None, "on", False, True)
    db.audit_insert(conn, "actor", _iso_horas_atras(1), "agent_kill_switch", None, "on", True, False)
    reg = db.audit_last(conn, "agent_kill_switch", "on")
    assert reg is not None and reg["newValue"] is False  # o registro mais recente (id maior)


def test_audit_last_none_quando_nao_ha_registro():
    conn = _fresh_db()
    assert db.audit_last(conn, "agent_kill_switch", "on") is None


# ==================================================== agent.kill_switch_ligado_desde
def test_ligado_desde_none_quando_desligado():
    conn = _fresh_db()
    assert agent.kill_switch_on() is False
    assert agent.kill_switch_ligado_desde(conn) is None


def test_ligado_desde_devolve_at_quando_ha_registro_de_ligar(monkeypatch):
    conn = _fresh_db()
    agent.configure_db(conn)
    agent.set_kill_switch(True, actor="u-admin")
    esperado = _iso_horas_atras(5)
    db.audit_insert(conn, "u-admin", esperado, "agent_kill_switch", None, "on", False, True)
    assert agent.kill_switch_ligado_desde(conn) == esperado


def test_ligado_desde_none_quando_ligado_por_env_sem_registro(monkeypatch):
    conn = _fresh_db()
    agent.configure_db(conn)
    monkeypatch.setenv("B3_AGENT_KILL", "1")
    assert agent.kill_switch_on() is True
    assert agent.kill_switch_ligado_desde(conn) is None  # sem registro de auditoria — não rastreável


def test_ligado_desde_none_quando_ultimo_registro_e_desligamento():
    conn = _fresh_db()
    agent.configure_db(conn)
    agent.set_kill_switch(True, actor="u-admin")
    db.audit_insert(conn, "u-admin", _iso_horas_atras(3), "agent_kill_switch", None, "on", False, True)
    db.audit_insert(conn, "u-admin", _iso_horas_atras(1), "agent_kill_switch", None, "on", True, False)
    # kill-switch está ligado (override em memória), mas o ÚLTIMO registro de
    # auditoria é um DESLIGAMENTO — não dá pra afirmar "ligado desde" daquele at
    assert agent.kill_switch_ligado_desde(conn) is None


# ========================================================= agent._alertar_kill_switch
def test_duracao_conhecida_titulo_contem_horas(monkeypatch):
    conn = _admin_conn()
    agent.configure_db(conn)
    agent.set_kill_switch(True, actor="u-admin")
    db.audit_insert(conn, "u-admin", _iso_horas_atras(5), "agent_kill_switch", None, "on", False, True)
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **kw: True)
    espia = _EspiaPush()
    monkeypatch.setattr("app.push.send_to_user", espia)
    n = asyncio.run(agent._alertar_kill_switch(conn))
    assert n == 1
    assert len(espia.chamadas) == 1
    _, titulo, corpo = espia.chamadas[0]
    assert "5h" in titulo
    assert "Verifique no portal admin" in corpo


def test_duracao_nao_rastreavel_corpo_diz_variavel_de_ambiente_nunca_0h(monkeypatch):
    conn = _admin_conn()
    agent.configure_db(conn)
    monkeypatch.setenv("B3_AGENT_KILL", "1")  # ativado por env — sem registro de auditoria
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **kw: True)
    espia = _EspiaPush()
    monkeypatch.setattr("app.push.send_to_user", espia)
    n = asyncio.run(agent._alertar_kill_switch(conn))
    assert n == 1
    _, titulo, corpo = espia.chamadas[0]
    assert "variável de ambiente" in corpo
    assert "0h" not in corpo
    assert "0h" not in titulo


def test_fora_do_pregao_nenhum_push(monkeypatch):
    conn = _admin_conn()
    agent.configure_db(conn)
    agent.set_kill_switch(True, actor="u-admin")
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **kw: False)
    espia = _EspiaPush()
    monkeypatch.setattr("app.push.send_to_user", espia)
    n = asyncio.run(agent._alertar_kill_switch(conn))
    assert n == 0
    assert espia.chamadas == []


def test_kill_switch_desligado_nenhum_push_e_dedupe_zerado(monkeypatch):
    conn = _admin_conn()
    agent.configure_db(conn)
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **kw: True)
    db.kv_set(conn, "agentKillSwitchAlerta", {"desde": "algo", "ultimoAvisoTs": time.time()}, user_id=None)
    espia = _EspiaPush()
    monkeypatch.setattr("app.push.send_to_user", espia)
    n = asyncio.run(agent._alertar_kill_switch(conn))
    assert n == 0
    assert espia.chamadas == []
    assert db.kv_get(conn, "agentKillSwitchAlerta", None, user_id=None) == {}


def test_dedupe_duas_execucoes_seguidas_um_fan_out(monkeypatch):
    conn = _admin_conn()
    agent.configure_db(conn)
    agent.set_kill_switch(True, actor="u-admin")
    db.audit_insert(conn, "u-admin", _iso_horas_atras(1), "agent_kill_switch", None, "on", False, True)
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **kw: True)
    espia = _EspiaPush()
    monkeypatch.setattr("app.push.send_to_user", espia)
    n1 = asyncio.run(agent._alertar_kill_switch(conn))
    n2 = asyncio.run(agent._alertar_kill_switch(conn))
    assert n1 == 1
    assert n2 == 0
    assert len(espia.chamadas) == 1


def test_reset_liga_alerta_desliga_liga_de_novo_alerta_de_novo(monkeypatch):
    conn = _admin_conn()
    agent.configure_db(conn)
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **kw: True)
    espia = _EspiaPush()
    monkeypatch.setattr("app.push.send_to_user", espia)

    agent.set_kill_switch(True, actor="u-admin")
    db.audit_insert(conn, "u-admin", _iso_horas_atras(1), "agent_kill_switch", None, "on", False, True)
    assert asyncio.run(agent._alertar_kill_switch(conn)) == 1

    agent.set_kill_switch(False, actor="u-admin")
    db.audit_insert(conn, "u-admin", _iso_horas_atras(0), "agent_kill_switch", None, "on", True, False)
    assert asyncio.run(agent._alertar_kill_switch(conn)) == 0  # desligado: zera o dedupe

    agent.set_kill_switch(True, actor="u-admin")
    db.audit_insert(conn, "u-admin", _iso_horas_atras(0), "agent_kill_switch", None, "on", False, True)
    assert asyncio.run(agent._alertar_kill_switch(conn)) == 1  # novo episódio: avisa de novo


def test_robustez_excecao_no_user_ids_with_roles_nao_propaga(monkeypatch):
    conn = _admin_conn()
    agent.configure_db(conn)
    agent.set_kill_switch(True, actor="u-admin")
    db.audit_insert(conn, "u-admin", _iso_horas_atras(1), "agent_kill_switch", None, "on", False, True)
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **kw: True)

    def _explode(*a, **kw):
        raise RuntimeError("banco indisponível (simulado)")
    monkeypatch.setattr(db, "user_ids_with_roles", _explode)

    n = asyncio.run(agent._alertar_kill_switch(conn))  # não pode propagar
    assert n == 0


def test_scheduler_loop_sobrevive_a_excecao_do_alerta(monkeypatch):
    """Chamada de mais alto nível: o hook pendurado no laço não pode
    derrubar `scheduler_loop` mesmo se `_alertar_kill_switch` propagar."""
    conn = _admin_conn()
    agent.configure_db(conn)

    async def _explode(*a, **kw):
        raise RuntimeError("alerta explodiu (simulado)")
    monkeypatch.setattr(agent, "_alertar_kill_switch", _explode)

    async def _quotes(tickers):
        return {}

    asyncio.run(agent.scheduler_loop(conn, _quotes, once=True))  # não pode propagar


# ================================================ hook ANTES do portão do kill-switch
def test_hook_esta_antes_do_primeiro_gate_de_kill_switch_no_fonte():
    """Assertiva automatizada (não só inspeção visual): o índice da chamada
    `_alertar_kill_switch(` dentro de `scheduler_loop` é menor que o índice
    do primeiro `if not kill_switch_on()` do mesmo laço — senão o alerta
    seria silenciado exatamente pelo estado que precisa denunciar (o mesmo
    erro do heartbeat que mascarou o incidente real)."""
    caminho = os.path.join(os.path.dirname(__file__), "..", "app", "agent.py")
    with open(caminho, encoding="utf-8") as f:
        fonte = f.read()
    idx_loop = fonte.index("async def scheduler_loop(")
    trecho_loop = fonte[idx_loop:]
    idx_hook = trecho_loop.index("await _alertar_kill_switch(")
    idx_gate = trecho_loop.index("if not kill_switch_on()")
    assert idx_hook < idx_gate, "o hook do alerta precisa vir ANTES do gate de kill-switch"


# ============================================ guardião de superfície (T-03-23)
def test_user_ids_with_roles_nao_e_exposto_por_nenhuma_rota():
    caminho = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
    with open(caminho, encoding="utf-8") as f:
        fonte = f.read()
    assert "user_ids_with_roles" not in fonte


def test_query_sql_de_user_ids_with_roles_usa_placeholders_nunca_fstring():
    caminho = os.path.join(os.path.dirname(__file__), "..", "app", "db.py")
    with open(caminho, encoding="utf-8") as f:
        fonte = f.read()
    assert "SELECT DISTINCT user_id" in fonte
    for linha in fonte.splitlines():
        assert not (linha.strip().startswith('f"SELECT') and "user_roles" in linha), \
            f"f-string interpolando a query de user_roles: {linha!r}"
