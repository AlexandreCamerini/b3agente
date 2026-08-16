"""ADR-013 — RBAC por grupos de macro função + bootstrap aditivo do admin.

Duas dimensões independentes do que já existe: PAPEL de governança (este
módulo) e PLANO comercial (`plan.py`, eixo separado, ADR-010). Um admin pode
nunca ter plano `pro`; um `pro` não ganha nenhuma permissão administrativa
por pagar.

Grupos são nomeados por FUNÇÃO DE PRODUTO reconhecível (Observabilidade,
Operador IA, Execução de ordens automáticas, Mudança de LLM, Fontes de
dados, Prompts, Usuários e papéis) — decisão do Alex (ADR-013), não uma
lista de permissões técnicas soltas. `role_admin` é só o bootstrap: união de
todos os grupos, migração ADITIVA do gate binário `_is_obs_admin` que já
existia (`B3_ADMIN_EMAILS` ou 1ª conta) — ninguém perde acesso que já tinha.

Crescer = acrescentar uma entrada em GRUPOS (ou um grupo novo inteiro) —
nunca reescrever o modelo.
"""
from datetime import datetime, timezone
import os

GRUPOS = {
    "observabilidade": {"observabilidade.ver"},
    "operador_ia": {"operador_ia.ver"},
    "execucao_automatica": {"execucao_automatica.ver", "execucao_automatica.controlar"},
    "llm": {"llm.configurar"},
    "fontes_dados": {"fontes_dados.configurar"},
    "prompts": {"prompts.editar"},
    "usuarios": {"usuarios.gerenciar"},
}

# Bootstrap: quem tinha o gate binário de hoje recebe TODAS as permissões de
# uma vez — equivalente ao "admin total" que _is_obs_admin já concedia.
ROLE_ADMIN = "role_admin"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def permissoes_do_papel(role: str) -> set:
    if role == ROLE_ADMIN:
        out = set()
        for perms in GRUPOS.values():
            out |= perms
        return out
    return set(GRUPOS.get(role) or ())


def permissions_for_user(conn, user_id: str) -> set:
    from . import db
    out = set()
    for role in db.roles_for_user(conn, user_id):
        out |= permissoes_do_papel(role)
    return out


def user_has_permission(conn, user_id: str, perm: str) -> bool:
    return perm in permissions_for_user(conn, user_id)


def grant_role(conn, user_id: str, role: str, granted_by=None) -> None:
    from . import db
    if role != ROLE_ADMIN and role not in GRUPOS:
        raise ValueError(f"Papel desconhecido: {role!r}")
    db.grant_role(conn, user_id, role, _now_iso(), granted_by=granted_by)


def revoke_role(conn, user_id: str, role: str) -> None:
    from . import db
    db.revoke_role(conn, user_id, role)


def roles_for_user(conn, user_id: str) -> list:
    from . import db
    return db.roles_for_user(conn, user_id)


# --------------------------- bootstrap aditivo -------------------------------
def _is_admin_bootstrap(conn, user: dict) -> bool:
    """MESMA lógica que `_is_obs_admin` tinha em main.py antes deste ADR —
    preservada aqui byte a byte para a migração ser garantidamente aditiva:
    quem já era admin continua sendo, sem depender de ninguém rodar um
    script de migração manual."""
    emails = [e.strip().lower() for e in (os.environ.get("B3_ADMIN_EMAILS") or "").split(",") if e.strip()]
    if emails:
        return bool(user.get("email")) and user["email"].lower() in emails
    row = conn.execute("SELECT id FROM users ORDER BY created_at ASC LIMIT 1").fetchone()
    return bool(row) and row[0] == user.get("id")


def ensure_bootstrap_role(conn, user: dict) -> None:
    """Chamado a cada login (mesmo ponto que hoje resolve `_is_obs_admin` por
    request) — se o usuário bate no bootstrap E ainda não tem `role_admin`,
    concede. Idempotente: não faz nada se já tiver o papel. Nunca REVOGA —
    isso ficaria pra uma tela de gestão de usuários futura, não é este ADR."""
    from . import db
    if not _is_admin_bootstrap(conn, user):
        return
    if ROLE_ADMIN in db.roles_for_user(conn, user["id"]):
        return
    db.grant_role(conn, user["id"], ROLE_ADMIN, _now_iso(), granted_by=None)
