"""25-02 (Fase 1 do `25-CONTEXT.md`, decisão D1 do Alex, 2026-09-12) — o papel
`owner`, a âncora do dono do produto.

Dois fatos MEDIDOS antes deste plano, e que este arquivo trava para que não
voltem:

  1. NENHUM papel era de fato irrevogável — `rbac.revoke_role` era um `DELETE`
     cru, sem condição nenhuma, e o que salvava o `role_admin` de sumir era a
     reconcessão automática do bootstrap no request seguinte (efeito colateral,
     não regra declarada).
  2. O papel máximo dependia de `B3_ADMIN_EMAILS` ou, na ausência dela, da
     conta mais ANTIGA do banco (`ORDER BY created_at ASC LIMIT 1`) — o achado
     A-12 da auditoria. Num banco novo, quem se cadastra primeiro vira dono.

A D1 é defesa em profundidade, e as DUAS camadas têm caso próprio aqui: a rota
recusa (casos 3 e 4) **E** o bootstrap reconcede (caso 5). Só recusar não cobre
escrita direta no banco; só reconceder deixa aberta a janela entre a revogação
e o próximo request.

O caso 2 é o mais importante do arquivo: as permissões do `owner` vêm da UNIÃO
DINÂMICA de `rbac.GRUPOS`, nunca de uma lista literal. Uma lista envelheceria
no primeiro grupo novo e "o dono nunca perde função" viraria mentira
silenciosa. Por isso a união é CALCULADA aqui, e nunca escrita à mão — um teste
com a lista copiada envelheceria junto com o defeito que deveria pegar.

Isolamento igual a `test_adr013_rbac.py` (B3_DB_PATH temporário + reset dos
caches em memória de managed.py/agent.py/brapi_budget.py); o caso 9 é de
unidade, no molde de `test_fase3_kill_switch_duracao.py`.
"""
import asyncio
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import agent, db, rbac

OWNER_EMAIL = "dono@teste.com"
# Uma conta que NENHUM teste registra — serve para desligar o bootstrap de
# `role_admin` da 1ª conta e isolar o que vem SÓ do `owner`.
NINGUEM = "ninguem-registra-esse@teste.com"


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import brapi_budget, managed
    original = sys.modules.get("app.main")
    monkeypatch.delenv("B3_OWNER_EMAIL", raising=False)
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    agent._DB_CONN = None
    agent._DB_ENABLED = False
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, owner_email=OWNER_EMAIL, admin_emails=None):
    """`owner_email=None` deixa `B3_OWNER_EMAIL` AUSENTE (vale o default de
    código, `alexandre.camerini@gmail.com`); `""` a define vazia (sem owner)."""
    if owner_email is None:
        monkeypatch.delenv("B3_OWNER_EMAIL", raising=False)
    else:
        monkeypatch.setenv("B3_OWNER_EMAIL", owner_email)
    if admin_emails is None:
        monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    else:
        monkeypatch.setenv("B3_ADMIN_EMAILS", admin_emails)
    d = tempfile.mkdtemp(prefix="b3_owner_test_")
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


def _uniao_de_grupos(rbac_mod) -> set:
    """A união CALCULADA, nunca escrita à mão — é o contrato que o owner
    precisa cumprir hoje e no dia em que existir um grupo a mais."""
    out = set()
    for perms in rbac_mod.GRUPOS.values():
        out |= perms
    return out


# ============================ 1. todas as permissões ==========================
def test_owner_tem_todas_as_permissoes_pela_uniao_de_grupos(monkeypatch):
    # `B3_ADMIN_EMAILS` aponta para uma conta que ninguém registra: assim a 1ª
    # conta NÃO recebe `role_admin`, e o que sobra vem só do `owner`.
    c, main = _client(monkeypatch, admin_emails=NINGUEM)
    payload = _registra(c, OWNER_EMAIL)
    uid = payload["user"]["id"]
    assert main.rbac.roles_for_user(main._conn, uid) == [main.rbac.OWNER]
    assert set(payload["user"]["permissions"]) == _uniao_de_grupos(main.rbac)


# ====================== 2. permissão futura entra sozinha =====================
def test_permissao_futura_entra_sozinha_nas_do_owner(monkeypatch):
    """O caso que reprova uma lista literal de permissões. Um grupo fictício
    acrescentado a `GRUPOS` em runtime tem de aparecer nas permissões do owner
    sem nenhuma edição no código do papel."""
    c, main = _client(monkeypatch, admin_emails=NINGUEM)
    payload = _registra(c, OWNER_EMAIL)
    antes = set(payload["user"]["permissions"])

    monkeypatch.setitem(main.rbac.GRUPOS, "grupo_que_ainda_nao_existe", {"futuro.mandar"})
    depois = set(c.get("/api/auth/me", headers=_auth(payload["token"])).json()["user"]["permissions"])

    assert depois == antes | {"futuro.mandar"}
    assert depois == _uniao_de_grupos(main.rbac)


# ===================== 3. a rota recusa a revogação do owner ==================
def test_revogar_owner_pela_rota_e_403_e_o_papel_permanece(monkeypatch):
    c, main = _client(monkeypatch)
    dono = _registra(c, OWNER_EMAIL)
    uid = dono["user"]["id"]
    assert main.rbac.OWNER in main.rbac.roles_for_user(main._conn, uid)

    r = c.post(f"/api/admin/users/{uid}/roles",
               json={"role": "owner", "acao": "revogar"}, headers=_auth(dono["token"]))
    assert r.status_code == 403, r.text
    assert "owner" in (r.json().get("detail") or "").lower()
    assert main.rbac.OWNER in main.rbac.roles_for_user(main._conn, uid)


def test_revogar_outro_papel_pela_rota_continua_funcionando(monkeypatch):
    """Não-regressão do caso 3: a recusa é do `owner`, não da rota inteira."""
    c, main = _client(monkeypatch)
    dono = _registra(c, OWNER_EMAIL)
    outro = _registra(c, "suporte@teste.com")
    h = _auth(dono["token"])
    c.post(f"/api/admin/users/{outro['user']['id']}/roles",
           json={"role": "observabilidade", "acao": "conceder"}, headers=h)
    r = c.post(f"/api/admin/users/{outro['user']['id']}/roles",
               json={"role": "observabilidade", "acao": "revogar"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["roles"] == []


# ================== 4. a função de domínio recusa, não só a rota ==============
def test_revoke_role_direto_levanta_para_owner(monkeypatch):
    """A rota é a porta conhecida; a regra mora no módulo. Um chamador novo
    (script, rota futura, tarefa de manutenção) tem de bater na MESMA recusa."""
    c, main = _client(monkeypatch)
    dono = _registra(c, OWNER_EMAIL)
    uid = dono["user"]["id"]

    with pytest.raises(main.rbac.PapelIrrevogavel):
        main.rbac.revoke_role(main._conn, uid, main.rbac.OWNER)
    assert main.rbac.OWNER in main.rbac.roles_for_user(main._conn, uid)

    # e qualquer outro papel continua revogável pela mesma função
    main.rbac.revoke_role(main._conn, uid, main.rbac.ROLE_ADMIN)
    assert main.rbac.roles_for_user(main._conn, uid) == [main.rbac.OWNER]


# ===================== 5. a segunda camada: reconciliação =====================
def test_owner_apagado_direto_no_banco_volta_no_proximo_request(monkeypatch):
    """A camada que cobre o que a recusa da rota não cobre: escrita direta no
    SQLite (`db.revoke_role`, um `DELETE` que não passa por `rbac`). Sem este
    caso ninguém sabe se a reconciliação funciona — e a D1 vira metade."""
    c, main = _client(monkeypatch, admin_emails=NINGUEM)
    dono = _registra(c, OWNER_EMAIL)
    uid = dono["user"]["id"]

    main.db.revoke_role(main._conn, uid, main.rbac.OWNER)
    assert main.rbac.roles_for_user(main._conn, uid) == []

    # a rota administrativa responde 200 porque o bootstrap devolve o papel
    # ANTES do gate de permissão (`require_permission`), no mesmo request
    assert c.get("/api/admin/summary", headers=_auth(dono["token"])).status_code == 200
    assert main.rbac.roles_for_user(main._conn, uid) == [main.rbac.OWNER]


# ============================== 6. idempotência ===============================
def test_bootstrap_do_owner_e_idempotente(monkeypatch):
    c, main = _client(monkeypatch, admin_emails=NINGUEM)
    dono = _registra(c, OWNER_EMAIL)
    uid = dono["user"]["id"]
    usuario = main.db.get_user_by_id(main._conn, uid)

    for _ in range(3):
        main.rbac.ensure_bootstrap_role(main._conn, usuario)

    assert main.rbac.roles_for_user(main._conn, uid) == [main.rbac.OWNER]
    n = main._conn.execute(
        "SELECT COUNT(*) FROM user_roles WHERE user_id = ? AND role = ?", (uid, "owner")
    ).fetchone()[0]
    assert n == 1


# ================= 7. sem e-mail correspondente, NENHUM owner =================
def test_sem_email_correspondente_nao_ha_owner(monkeypatch):
    c, main = _client(monkeypatch, owner_email="nao-e-de-ninguem@teste.com")
    p1 = _registra(c, "primeiro@teste.com")
    p2 = _registra(c, "segundo@teste.com")
    assert main.rbac.OWNER not in main.rbac.roles_for_user(main._conn, p1["user"]["id"])
    assert main.rbac.OWNER not in main.rbac.roles_for_user(main._conn, p2["user"]["id"])
    assert main._conn.execute("SELECT COUNT(*) FROM user_roles WHERE role = 'owner'").fetchone()[0] == 0


def test_a_primeira_conta_nao_vira_owner_por_ordem_de_criacao(monkeypatch):
    """O A-12 não se repete no papel novo: sem `B3_OWNER_EMAIL` vale o default
    de código, e uma conta que não bate nele NÃO é eleita por ser a mais antiga
    — mesmo sendo ela quem recebe o `role_admin` do bootstrap legado."""
    c, main = _client(monkeypatch, owner_email=None)  # env AUSENTE
    p1 = _registra(c, "primeiro@teste.com")
    papeis = main.rbac.roles_for_user(main._conn, p1["user"]["id"])
    assert main.rbac.ROLE_ADMIN in papeis  # o bootstrap legado segue intacto
    assert main.rbac.OWNER not in papeis
    assert main._conn.execute("SELECT COUNT(*) FROM user_roles WHERE role = 'owner'").fetchone()[0] == 0


def test_email_do_owner_ignora_caixa_e_espaco(monkeypatch):
    c, main = _client(monkeypatch, owner_email="  DONO@Teste.com  ", admin_emails=NINGUEM)
    dono = _registra(c, OWNER_EMAIL)
    assert main.rbac.roles_for_user(main._conn, dono["user"]["id"]) == [main.rbac.OWNER]


# ======================= 8. só owner concede owner ============================
def test_role_admin_que_nao_e_owner_nao_concede_owner(monkeypatch):
    """O freio de escalação, um degrau acima do que já existia: `role_admin`
    concede qualquer grupo, mas NÃO distribui a âncora do dono do produto."""
    c, main = _client(monkeypatch, owner_email="nao-e-de-ninguem@teste.com")
    admin = _registra(c, "primeiro@teste.com")  # 1ª conta = role_admin, sem owner
    alvo = _registra(c, "candidato@teste.com")
    assert main.rbac.OWNER not in main.rbac.roles_for_user(main._conn, admin["user"]["id"])

    r = c.post(f"/api/admin/users/{alvo['user']['id']}/roles",
               json={"role": "owner", "acao": "conceder"}, headers=_auth(admin["token"]))
    assert r.status_code == 403, r.text
    assert main.rbac.OWNER not in main.rbac.roles_for_user(main._conn, alvo["user"]["id"])


def test_owner_concede_owner(monkeypatch):
    c, main = _client(monkeypatch)
    dono = _registra(c, OWNER_EMAIL)
    socio = _registra(c, "socio@teste.com")
    r = c.post(f"/api/admin/users/{socio['user']['id']}/roles",
               json={"role": "owner", "acao": "conceder"}, headers=_auth(dono["token"]))
    assert r.status_code == 200, r.text
    assert main.rbac.OWNER in r.json()["roles"]
    me = c.get("/api/auth/me", headers=_auth(socio["token"])).json()
    assert set(me["user"]["permissions"]) == _uniao_de_grupos(main.rbac)


# ============ 9. o owner não some das varreduras por papel ====================
def test_owner_recebe_o_push_de_kill_switch(monkeypatch):
    """`agent.py` monta os destinatários iterando `rbac.GRUPOS` + `ROLE_ADMIN`.
    Papel FORA de `GRUPOS` fica invisível para essa varredura: sem esta linha o
    dono do produto seria o único a não ser avisado de que a execução
    automática da base inteira está parada — exatamente o incidente que o
    alerta existe para não repetir."""
    from app import push  # noqa: F401 — o monkeypatch abaixo é sobre ele

    d = tempfile.mkdtemp(prefix="b3_owner_killswitch_test_")
    conn = db.connect(os.path.join(d, "b3_agente.db"))
    db.insert_user(conn, {
        "id": "u-owner", "email": OWNER_EMAIL, "provider": "local", "provider_sub": None,
        "pass_hash": None, "name": "dono", "created_at": "2026-01-01T00:00:00Z",
    })
    db.grant_role(conn, "u-owner", rbac.OWNER, "2026-01-01T00:00:00Z", granted_by=None)

    agent.configure_db(conn)
    agent.set_kill_switch(True, actor="u-owner")
    monkeypatch.setattr(agent, "in_market_hours", lambda *a, **kw: True)

    chamadas = []

    async def _espia(conn_, user_id, title, body, som=True, prioridade="10", client=None, extra=None):
        chamadas.append(user_id)
        return {"sent": 1, "total": 1, "detalhes": []}

    monkeypatch.setattr("app.push.send_to_user", _espia)
    enviados = asyncio.run(agent._alertar_kill_switch(conn))
    assert enviados == 1
    assert chamadas == ["u-owner"]


# ================================ sanidade ====================================
def test_sanidade_a_uniao_calculada_nao_e_vazia_nem_literal():
    """Uma união vazia aprovaria os casos 1, 2 e 8 por vacuidade."""
    uniao = _uniao_de_grupos(rbac)
    assert len(uniao) >= 9
    assert "usuarios.gerenciar" in uniao
