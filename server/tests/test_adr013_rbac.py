"""ADR-013 — RBAC por grupos de macro função + entitlements + audit log.

O que este teste protege:
  - bootstrap ADITIVO: quem já era admin (B3_ADMIN_EMAILS / 1º usuário)
    continua sendo, agora via `role_admin`, sem perder nada;
  - usuário comum não acessa NENHUMA rota admin (nem as 9 que já existiam,
    nem as novas);
  - conceder um grupo dá acesso SÓ àquele grupo, não aos outros (a lição do
    Django/GitHub pesquisados no ADR: papel base + grupo específico, não
    tudo-ou-nada);
  - toda escrita admin grava audit log (config de IA, kill-switch, prompt,
    papel) — sem exceção;
  - stop/alvo NUNCA ganha gate de plano/papel (invariante do CLAUDE.md);
  - edição de prompt do admin nunca sobrescreve edição pessoal do usuário
    (a mesma garantia já teve verificação de unidade em test_auditoria_
    prompts.py; aqui é o caminho HTTP completo).

Isolamento igual a test_admin_summary.py (B3_DB_PATH temporário) + reset dos
caches em memória de managed.py/agent.py/brapi_budget.py entre testes.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient


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


def _client(monkeypatch, admin_emails=None):
    if admin_emails is None:
        monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    else:
        monkeypatch.setenv("B3_ADMIN_EMAILS", admin_emails)
    d = tempfile.mkdtemp(prefix="b3_adr013_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


ROTAS_ADMIN = [
    ("GET", "/api/obs/logs"),
    ("GET", "/api/obs/usage"),
    ("GET", "/api/obs/brapi/projecao"),
    ("GET", "/api/analytics/summary"),
    ("GET", "/api/analytics/ia-eficiencia"),
    ("GET", "/api/analytics/automacao"),
    ("GET", "/api/analytics/tendencias"),
    ("GET", "/api/admin/summary"),
    ("GET", "/api/admin/config/ia"),
    ("GET", "/api/admin/agent/kill-switch"),
    ("GET", "/api/admin/prompts"),
    ("GET", "/api/admin/users"),
]


# --------------------------- bootstrap aditivo -------------------------------
def test_primeiro_usuario_bootstrap_recebe_todas_as_7_permissoes(monkeypatch):
    c, _ = _client(monkeypatch)
    payload = _registra(c, "dono@teste.com")
    perms = set(payload["user"]["permissions"])
    assert perms == {
        "observabilidade.ver", "operador_ia.ver", "execucao_automatica.ver",
        "execucao_automatica.controlar", "llm.configurar",
        "fontes_dados.configurar", "prompts.editar", "usuarios.gerenciar",
    }


def test_usuario_comum_nao_acessa_nenhuma_rota_admin(monkeypatch):
    c, _ = _client(monkeypatch)
    _registra(c, "dono@teste.com")
    payload2 = _registra(c, "comum@teste.com")
    assert payload2["user"]["permissions"] == []
    h = _auth(payload2["token"])
    for metodo, rota in ROTAS_ADMIN:
        r = c.request(metodo, rota, headers=h)
        assert r.status_code == 403, f"{metodo} {rota} deveria ser 403 para usuário comum, veio {r.status_code}"


def test_b3_admin_emails_tem_prioridade_sobre_1o_usuario(monkeypatch):
    c, _ = _client(monkeypatch, admin_emails="admin@teste.com")
    p1 = _registra(c, "primeiro@teste.com")
    p2 = _registra(c, "admin@teste.com")
    assert p1["user"]["permissions"] == []
    assert len(p2["user"]["permissions"]) == 8  # 7 grupos + controlar (execucao_automatica tem 2)


def test_me_tambem_dispara_o_bootstrap_para_sessao_ja_existente(monkeypatch):
    """Cobre o caso de sessão criada ANTES do deploy desta feature — não
    precisa esperar o próximo login de verdade."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "dono@teste.com")
    # remove manualmente o papel pra simular uma sessão "antiga" sem bootstrap
    main.rbac.revoke_role(main._conn, payload["user"]["id"], "role_admin")
    r = c.get("/api/auth/me", headers=_auth(payload["token"]))
    assert r.json()["user"]["permissions"] != []


# ------------------------- concessão granular por grupo -----------------------
def test_conceder_um_grupo_da_acesso_so_aquele_grupo(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    outro = _registra(c, "suporte@teste.com")
    h_admin = _auth(admin["token"])
    h_outro = _auth(outro["token"])

    r = c.post(f"/api/admin/users/{outro['user']['id']}/roles",
              json={"role": "observabilidade", "acao": "conceder"}, headers=h_admin)
    assert r.status_code == 200, r.text
    assert r.json()["roles"] == ["observabilidade"]

    assert c.get("/api/obs/logs", headers=h_outro).status_code == 200
    assert c.get("/api/admin/config/ia", headers=h_outro).status_code == 403
    assert c.get("/api/admin/agent/kill-switch", headers=h_outro).status_code == 403


def test_revogar_grupo_remove_o_acesso(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    outro = _registra(c, "suporte@teste.com")
    h_admin = _auth(admin["token"])
    h_outro = _auth(outro["token"])
    c.post(f"/api/admin/users/{outro['user']['id']}/roles",
          json={"role": "observabilidade", "acao": "conceder"}, headers=h_admin)
    assert c.get("/api/obs/logs", headers=h_outro).status_code == 200
    c.post(f"/api/admin/users/{outro['user']['id']}/roles",
          json={"role": "observabilidade", "acao": "revogar"}, headers=h_admin)
    assert c.get("/api/obs/logs", headers=h_outro).status_code == 403


def test_papel_desconhecido_e_rejeitado(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    outro = _registra(c, "x@teste.com")
    r = c.post(f"/api/admin/users/{outro['user']['id']}/roles",
              json={"role": "super_hacker", "acao": "conceder"}, headers=_auth(admin["token"]))
    assert r.status_code == 400


def test_usuarios_gerenciar_nao_concede_role_admin_a_terceiro(monkeypatch):
    """Achado da auditoria 2026-08-20 (crítico): quem só tem "usuarios.gerenciar"
    conseguia conceder role_admin (todas as 7 permissões) a qualquer conta —
    bypass total do modelo de menor privilégio. Só role_admin pode conceder
    role_admin."""
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    suporte = _registra(c, "suporte@teste.com")
    vitima = _registra(c, "vitima@teste.com")
    h_admin = _auth(admin["token"])
    h_suporte = _auth(suporte["token"])

    c.post(f"/api/admin/users/{suporte['user']['id']}/roles",
          json={"role": "usuarios", "acao": "conceder"}, headers=h_admin)

    r = c.post(f"/api/admin/users/{vitima['user']['id']}/roles",
              json={"role": "role_admin", "acao": "conceder"}, headers=h_suporte)
    assert r.status_code == 403, r.text
    assert c.get("/api/admin/config/ia", headers=_auth(vitima["token"])).status_code == 403


def test_usuarios_gerenciar_nao_concede_role_admin_a_si_mesmo(monkeypatch):
    """Mesmo achado — caminho de autopromoção (concede role_admin à própria conta)."""
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    suporte = _registra(c, "suporte@teste.com")
    h_admin = _auth(admin["token"])
    h_suporte = _auth(suporte["token"])

    c.post(f"/api/admin/users/{suporte['user']['id']}/roles",
          json={"role": "usuarios", "acao": "conceder"}, headers=h_admin)

    r = c.post(f"/api/admin/users/{suporte['user']['id']}/roles",
              json={"role": "role_admin", "acao": "conceder"}, headers=h_suporte)
    assert r.status_code == 403, r.text
    assert c.get("/api/admin/agent/kill-switch", headers=h_suporte).status_code == 403


def test_role_admin_pode_conceder_role_admin(monkeypatch):
    """O freio é só pra quem NÃO é role_admin — quem já é continua podendo
    promover outra conta (senão nunca sairia do bootstrap de 1 admin só)."""
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    outro = _registra(c, "co-admin@teste.com")
    r = c.post(f"/api/admin/users/{outro['user']['id']}/roles",
              json={"role": "role_admin", "acao": "conceder"}, headers=_auth(admin["token"]))
    assert r.status_code == 200, r.text
    assert c.get("/api/admin/config/ia", headers=_auth(outro["token"])).status_code == 200


# ------------------------------- audit log -----------------------------------
def test_config_ia_escreve_e_audita(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    h = _auth(admin["token"])
    r = c.put("/api/admin/config/ia", json={"llmDailyQuota": 42}, headers=h)
    assert r.status_code == 200
    assert r.json()["vigente"]["llmDailyQuota"] == 42

    audit = c.get("/api/admin/audit", headers=h).json()["eventos"]
    ev = [e for e in audit if e["entity"] == "config_ia" and e["field"] == "llmDailyQuota"]
    assert ev, audit
    assert ev[0]["newValue"] == 42
    assert ev[0]["actorUserId"] == admin["user"]["id"]


def test_kill_switch_escreve_e_audita_e_afeta_o_motor(monkeypatch):
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    h = _auth(admin["token"])
    assert main.agent_mod.kill_switch_on() is False
    r = c.put("/api/admin/agent/kill-switch", json={"on": True}, headers=h)
    assert r.status_code == 200 and r.json()["on"] is True
    assert main.agent_mod.kill_switch_on() is True

    audit = c.get("/api/admin/audit", headers=h).json()["eventos"]
    ev = [e for e in audit if e["entity"] == "agent_kill_switch"]
    assert ev and ev[0]["newValue"] is True and ev[0]["oldValue"] is False


def test_brapi_projecao_post_agora_audita(monkeypatch):
    """A rota que já existia como admin-write SEM audit log (ADR-013,
    contexto) — a primeira migrada. Confirma que o audit nasceu junto."""
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    h = _auth(admin["token"])
    c.post("/api/obs/brapi/projecao", json={"intervaloS": 120, "aplicar": True}, headers=h)
    audit = c.get("/api/admin/audit", headers=h).json()["eventos"]
    ev = [e for e in audit if e["entity"] == "brapi_spot_intervalo"]
    assert ev and ev[0]["newValue"] == 120


def test_grant_role_audita(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    outro = _registra(c, "x@teste.com")
    h = _auth(admin["token"])
    c.post(f"/api/admin/users/{outro['user']['id']}/roles",
          json={"role": "prompts", "acao": "conceder"}, headers=h)
    audit = c.get("/api/admin/audit", headers=h).json()["eventos"]
    ev = [e for e in audit if e["entity"] == "user_role" and e["entityId"] == outro["user"]["id"]]
    assert ev and "prompts" in ev[0]["newValue"]


def test_auditoria_e_filtrada_ao_que_a_pessoa_administra(monkeypatch):
    """Achado da auditoria 2026-08-20 (alto): GET /api/admin/audit devolvia o
    log INTEIRO pra qualquer permissão administrativa, quando o ADR-013
    promete "filtrado ao que a pessoa administra". Um editor só de prompts
    não pode ver toggle de kill-switch, config de IA nem quem ganhou papel."""
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    editor = _registra(c, "editor@teste.com")
    h_admin = _auth(admin["token"])
    h_editor = _auth(editor["token"])

    c.post(f"/api/admin/users/{editor['user']['id']}/roles",
          json={"role": "prompts", "acao": "conceder"}, headers=h_admin)
    # gera eventos em entidades FORA do domínio do editor
    c.put("/api/admin/agent/kill-switch", json={"on": True}, headers=h_admin)
    c.put("/api/admin/config/ia", json={"llmDailyQuota": 42}, headers=h_admin)

    audit_admin = c.get("/api/admin/audit", headers=h_admin).json()["eventos"]
    entidades_admin = {e["entity"] for e in audit_admin}
    assert {"agent_kill_switch", "config_ia", "user_role"} <= entidades_admin, \
        "role_admin precisa continuar vendo o log inteiro"

    audit_editor = c.get("/api/admin/audit", headers=h_editor).json()["eventos"]
    entidades_editor = {e["entity"] for e in audit_editor}
    assert "agent_kill_switch" not in entidades_editor
    assert "config_ia" not in entidades_editor
    assert "user_role" not in entidades_editor


# --------------------------------- prompts ------------------------------------
def test_admin_publica_prompt_conta_nova_recebe_usuario_editado_nao_muda(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    editou = _registra(c, "editou@teste.com")
    h_admin = _auth(admin["token"])

    # 'editou' customiza o próprio prompt ANTES do admin publicar
    r = c.put("/api/llm-prompts", json={"carteiraStopAlvo": "MEU TEXTO PESSOAL"},
              headers=_auth(editou["token"]))
    assert r.status_code == 200

    r = c.put("/api/admin/prompts/carteiraStopAlvo", json={"texto": "NOVO DEFAULT DO ADMIN"}, headers=h_admin)
    assert r.status_code == 200

    # conta NOVA recebe o novo default
    nova = _registra(c, "novo@teste.com")
    estado_novo = c.get("/api/state", headers=_auth(nova["token"])).json()
    assert estado_novo["llmPrompts"]["carteiraStopAlvo"] == "NOVO DEFAULT DO ADMIN"

    # quem editou o próprio prompt NUNCA é sobrescrito — relogar dispara o
    # backfill (ensure_defaults) e o texto pessoal continua intocado.
    r = c.post("/api/auth/login", json={"email": "editou@teste.com", "password": "senhaboa123"})
    estado_editou = r.json()["state"]
    assert estado_editou["llmPrompts"]["carteiraStopAlvo"] == "MEU TEXTO PESSOAL"


def test_prompts_get_mostra_override_e_default_de_codigo(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    h = _auth(admin["token"])
    antes = c.get("/api/admin/prompts", headers=h).json()
    assert antes["carteiraStopAlvo"]["temOverride"] is False

    c.put("/api/admin/prompts/carteiraStopAlvo", json={"texto": "X"}, headers=h)
    depois = c.get("/api/admin/prompts", headers=h).json()
    assert depois["carteiraStopAlvo"]["temOverride"] is True
    assert depois["carteiraStopAlvo"]["ativo"] == "X"
    assert depois["carteiraStopAlvo"]["codigoDefault"] != "X"  # o piso de código nunca muda


def test_prompts_put_chave_desconhecida_e_400(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    r = c.put("/api/admin/prompts/naoExiste", json={"texto": "X"}, headers=_auth(admin["token"]))
    assert r.status_code == 400


# ------------------------- invariante: stop/alvo nunca vetado -----------------
def test_stop_alvo_nunca_ganha_gate_de_papel_ou_plano(monkeypatch):
    """Guardrail do CLAUDE.md: papel/plano NUNCA veta stop/alvo. Usuário SEM
    nenhuma permissão administrativa e SEM plano pago continua conseguindo
    armar proteção normalmente."""
    c, _ = _client(monkeypatch)
    _registra(c, "dono@teste.com")
    comum = _registra(c, "comum@teste.com")
    h = _auth(comum["token"])
    assert comum["user"]["permissions"] == []
    assert comum["user"]["plan"] == "free"
    r = c.put("/api/position/PETR4", json={"stop": 30.0, "alvo": 40.0}, headers=h)
    assert r.status_code == 200
    r2 = c.put("/api/options/position/FAKE123", json={"stop": 1.0, "alvo": 2.0}, headers=h)
    assert r2.status_code == 200


# --------------------- correções da revisão de código -------------------------
def test_config_ia_provider_invalido_e_400(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    r = c.put("/api/admin/config/ia", json={"llmProvider": "opnai"}, headers=_auth(admin["token"]))
    assert r.status_code == 400
    assert c.get("/api/admin/config/ia", headers=_auth(admin["token"])).json()["llmProvider"] is None


def test_config_ia_campo_vazio_limpa_o_override(monkeypatch):
    c, _ = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    h = _auth(admin["token"])
    c.put("/api/admin/config/ia", json={"llmProvider": "anthropic"}, headers=h)
    assert c.get("/api/admin/config/ia", headers=h).json()["llmProvider"] == "anthropic"
    r = c.put("/api/admin/config/ia", json={"llmProvider": ""}, headers=h)
    assert r.status_code == 200
    assert c.get("/api/admin/config/ia", headers=h).json()["llmProvider"] is None


def test_config_ia_override_afeta_managed_config_sem_reiniciar(monkeypatch):
    """Achado de revisão: managed.py ganhou cache — confirma que a rota
    admin invalida o cache (senão a mudança só valeria depois de um restart)."""
    monkeypatch.setenv("B3_MANAGED_LLM_KEY", "chave-fake")
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    assert main.managed.managed_config()["provider"] == "openai"
    c.put("/api/admin/config/ia", json={"llmProvider": "anthropic"}, headers=_auth(admin["token"]))
    assert main.managed.managed_config()["provider"] == "anthropic"


def test_global_daily_cap_override_zero_bloqueia_tudo(monkeypatch):
    """Achado de revisão: override=0 virava 'ilimitado' — o oposto do que um
    admin quer ao digitar 0 num incidente de custo. A env B3_MANAGED_
    GLOBAL_DAILY_CAP=0 continua significando ilimitado (guardião pré-
    existente em test_qa42_finops.py) — só o override do admin muda."""
    monkeypatch.setenv("B3_MANAGED_LLM_KEY", "chave-fake")
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    c.put("/api/admin/config/ia", json={"llmGlobalDailyCap": 0}, headers=_auth(admin["token"]))
    assert main.managed.global_daily_cap() == 0


def test_kill_switch_degrada_sem_derrubar_em_falha_do_db(monkeypatch):
    """Achado de revisão: a leitura do DB não tinha try/except — uma falha
    de SQLite propagava e podia pular o ciclo inteiro do scheduler."""
    c, main = _client(monkeypatch)
    _registra(c, "dono@teste.com")

    def _explode(*a, **kw):
        raise RuntimeError("SQLite indisponível (simulado)")

    monkeypatch.setattr(main.db, "admin_config_get", _explode)
    main.agent_mod.reset_kill_switch_cache()
    assert main.agent_mod.kill_switch_on() is False  # nunca levanta, cai pro env (ausente => False)


def test_kill_switch_updated_by_reflete_o_ator(monkeypatch):
    c, main = _client(monkeypatch)
    admin = _registra(c, "dono@teste.com")
    c.put("/api/admin/agent/kill-switch", json={"on": True}, headers=_auth(admin["token"]))
    row = main._conn.execute("SELECT updated_by FROM admin_config WHERE key = ?", ("agentKillSwitch",)).fetchone()
    assert row[0] == admin["user"]["id"]


def test_rota_admin_direto_dispara_bootstrap_sem_passar_por_me(monkeypatch):
    """Achado de revisão: require_permission() não disparava o bootstrap —
    só /api/auth/me e login/registro. Uma sessão que bata direto numa rota
    admin (sem nunca ter chamado /me) precisa do MESMO bootstrap aditivo."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "dono@teste.com")
    # simula uma sessão "antiga": tem token válido mas nunca recebeu role_admin
    main.rbac.revoke_role(main._conn, payload["user"]["id"], "role_admin")
    assert main.rbac.roles_for_user(main._conn, payload["user"]["id"]) == []
    r = c.get("/api/admin/summary", headers=_auth(payload["token"]))  # NUNCA chamou /me antes
    assert r.status_code == 200
