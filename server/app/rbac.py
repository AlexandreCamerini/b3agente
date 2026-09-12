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
    # ADR-027 §2.7 (aba-opcoes F1, 2026-09-09): o armazém de setups do serviço
    # MCP é ÚNICO e não tem campo `owner` — um setup criado por qualquer conta
    # é visto por todos os clientes do serviço. Enquanto essa lacuna existir,
    # criar/confirmar/desativar setup é permissão nomeada (só `role_admin` a
    # recebe no bootstrap); ler, avaliar e ver gráfico valem para todo usuário
    # logado, sem permissão.
    "opcoes": {"opcoes.criar_setup"},
}

# Bootstrap: quem tinha o gate binário de hoje recebe TODAS as permissões de
# uma vez — equivalente ao "admin total" que _is_obs_admin já concedia.
ROLE_ADMIN = "role_admin"

# 25-02 (Fase 1 do 25-CONTEXT, decisão D1 do Alex, 2026-09-12) — a âncora do
# DONO DO PRODUTO. A diferença para `ROLE_ADMIN` não é de permissão (os dois
# têm exatamente as mesmas, pela união abaixo), é de PERMANÊNCIA:
#   • `role_admin` é bootstrap de governança — concedido e revogado pela rota
#     de papéis como qualquer outro, e quem o tem pode perdê-lo;
#   • `owner` não sai: `revoke_role` recusa (1ª camada) e `ensure_bootstrap_
#     role` reconcede se ele escapar por outro caminho (2ª camada). Defesa em
#     profundidade, porque cada camada cobre o que a outra não cobre — só
#     recusar não alcança escrita direta no SQLite; só reconceder deixa a
#     janela entre a revogação e o próximo request.
# Quem é o dono vem de `B3_OWNER_EMAIL` (`_is_owner`), não da ordem de criação
# das contas.
OWNER = "owner"

# Papéis TOTAIS: as permissões deles são a união DINÂMICA de `GRUPOS`, nunca
# uma lista literal. É o que faz "o dono nunca perde função" continuar
# verdadeiro no dia em que existir um grupo novo — acrescentar uma entrada em
# `GRUPOS` basta, aqui não se mexe.
_PAPEIS_TOTAIS = (ROLE_ADMIN, OWNER)

# Âncora do `owner`, configurável por env. O e-mail não é segredo (não dá
# acesso a nada sozinho — a conta ainda precisa autenticar), mas a âncora é
# configurável para o dia em que o dono do produto mudar de endereço.
OWNER_EMAIL_DEFAULT = "alexandre.camerini@gmail.com"


class PapelIrrevogavel(ValueError):
    """Tentativa de revogar um papel que, por decisão, não sai (hoje só
    `OWNER`). Primeira regra do repositório que declara isso — até 25-02
    `revoke_role` era um `DELETE` cru e NENHUM papel era de fato irrevogável:
    o que salvava o `role_admin` era a reconcessão automática do bootstrap no
    request seguinte, efeito colateral e não regra. Herda de `ValueError` para
    quem já trata erro de domínio desta função genericamente continuar
    funcionando; quem precisa distinguir (a rota, que responde 403 em vez de
    400) captura a classe específica."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def permissoes_do_papel(role: str) -> set:
    if role in _PAPEIS_TOTAIS:
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
    if role not in _PAPEIS_TOTAIS and role not in GRUPOS:
        raise ValueError(f"Papel desconhecido: {role!r}")
    db.grant_role(conn, user_id, role, _now_iso(), granted_by=granted_by)


def revoke_role(conn, user_id: str, role: str) -> None:
    """25-02 (D1, 2026-09-12): `OWNER` não é revogável — a função recusa antes
    de tocar no banco. A regra mora AQUI, e não só na rota, porque a rota é uma
    porta conhecida entre várias possíveis (script de manutenção, rota futura,
    tarefa de migração): quem chamar por outro caminho bate na mesma recusa."""
    from . import db
    if role == OWNER:
        raise PapelIrrevogavel(
            "O papel 'owner' é a âncora do dono do produto e não pode ser revogado."
        )
    db.revoke_role(conn, user_id, role)


def roles_for_user(conn, user_id: str) -> list:
    from . import db
    return db.roles_for_user(conn, user_id)


# --------------------- ADR-013: auditoria filtrada por grupo -----------------
# Mapeamento permissão → `entity` do admin_audit_log que ela dá direito de ver
# (critério: a mesma área/grupo que a permissão administra na UI). Cobre toda
# `entity` hoje gravada por `audit.record(...)` em main.py (grep por
# "audit.record" confirma a lista). observabilidade.ver e operador_ia.ver são
# só-leitura — não geram entrada própria no audit log, por isso não aparecem
# aqui. `role_admin` não precisa de entrada própria: ele já tem TODAS as
# permissões abaixo via `permissoes_do_papel`, então a união natural das
# entidades já cobre o audit log inteiro.
ENTIDADES_POR_PERMISSAO = {
    # 24-17 (2026-09-12): `user_plan` entrou junto de `user_role` porque a
    # rota irmã `POST /api/admin/users/{id}/plan` passou a gravar
    # `audit.record(..., "user_plan", ...)` sob a MESMA permissão. Sem esta
    # entrada o evento é gravado e `entidades_visiveis` o filtra para fora de
    # todo filtro — inclusive o de quem acabou de produzi-lo. São eixos
    # diferentes (governança × plano comercial, ADR-010), mas quem administra
    # contas administra os dois.
    "usuarios.gerenciar": {"user_role", "user_plan"},
    "prompts.editar": {"prompt_default"},
    "llm.configurar": {"config_ia"},
    # 24-15 (2026-09-11): `mcp_cota` entrou junto de `brapi_spot_intervalo`
    # porque é a MESMA classe de decisão — teto de consumo de fonte de dados
    # externa, não governança de IA. Sem esta entrada `audit.record` gravaria
    # a mudança dos tetos da aba Opções e `entidades_visiveis` a filtraria
    # para fora de TODO filtro, inclusive o de quem a produziu.
    "fontes_dados.configurar": {"brapi_spot_intervalo", "mcp_cota"},
    "execucao_automatica.ver": {"agent_kill_switch", "timing_watch_kill_switch"},
    "execucao_automatica.controlar": {"agent_kill_switch", "timing_watch_kill_switch"},
    # ADR-027 §2.7 — ENTROU na Fase 5 (2026-09-11), como a nota anterior
    # previa: `POST /api/options/mcp/setups/confirmar` e
    # `/setups/{name}/desativar` gravam `audit.record(..., "opcoes_setup",
    # ...)`, então a entidade passou a ser HOJE gravada e o contrato deste
    # mapa ("cobre toda `entity` gravada") voltou a valer com ela dentro. Sem
    # esta linha a auditoria existiria e ninguém a veria: `entidades_visiveis`
    # filtra o audit log por este mapa, e o evento cairia fora de todo filtro
    # — inclusive para quem tem a permissão que o produziu.
    "opcoes.criar_setup": {"opcoes_setup"},
}


def entidades_visiveis(conn, user_id: str) -> set:
    """União das entidades do admin_audit_log que o usuário enxerga, pelas
    permissões que tem. Vazio = não vê nenhum evento (mesmo assim só chega
    aqui quem já passou por `require_any_admin_permission`, ou seja, tem
    algum papel administrativo)."""
    out = set()
    for perm in permissions_for_user(conn, user_id):
        out |= ENTIDADES_POR_PERMISSAO.get(perm, set())
    return out


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


def _is_owner(conn, user: dict) -> bool:
    """25-02 (D1, 2026-09-12) — a âncora do dono do produto: `B3_OWNER_EMAIL`,
    default `OWNER_EMAIL_DEFAULT`. Comparação com `strip` e caixa baixa, como
    `_is_admin_bootstrap` já faz.

    DELIBERADAMENTE **sem** o fallback de "primeira conta" que
    `_is_admin_bootstrap` tem — é o achado A-12 da auditoria: eleger o papel
    máximo por `ORDER BY created_at ASC LIMIT 1` faz o dono do produto depender
    de quem se cadastrou primeiro num banco novo. Se o e-mail não bater em
    nenhuma conta, NÃO há owner, e isso é melhor que eleger um por acidente.
    (O `_is_admin_bootstrap` continua com o fallback porque é contrato testado
    do ADR-013; fechar o A-12 para o `role_admin` é decisão separada.)

    A env definida VAZIA significa "sem owner", e não "use o default" — é como
    se desliga a âncora sem editar código. `conn` entra na assinatura por
    simetria com `_is_admin_bootstrap`, e para o dia em que a âncora vier do
    kv; hoje não é lido.
    """
    bruto = os.environ.get("B3_OWNER_EMAIL")
    alvo = (bruto if bruto is not None else OWNER_EMAIL_DEFAULT).strip().lower()
    if not alvo:
        return False
    email = (user.get("email") or "").strip().lower()
    return bool(email) and email == alvo


def ensure_bootstrap_role(conn, user: dict) -> None:
    """Chamado a cada login (mesmo ponto que hoje resolve `_is_obs_admin` por
    request) — se o usuário bate no bootstrap E ainda não tem `role_admin`,
    concede. Idempotente: não faz nada se já tiver o papel. Nunca REVOGA —
    isso ficaria pra uma tela de gestão de usuários futura, não é este ADR.

    25-02 (D1, 2026-09-12): reconcilia TAMBÉM o `OWNER`, e é a SEGUNDA camada
    da defesa em profundidade — se o papel sumir por um caminho que não passa
    por `revoke_role` (escrita direta no SQLite, restauração de backup antigo,
    migração), o próximo request administrativo o devolve. As duas propriedades
    de origem ficam de pé para os dois papéis: nunca revoga, e é idempotente."""
    from . import db
    eh_owner = _is_owner(conn, user)
    eh_admin = _is_admin_bootstrap(conn, user)
    if not eh_owner and not eh_admin:
        return
    atuais = db.roles_for_user(conn, user["id"])
    if eh_owner and OWNER not in atuais:
        db.grant_role(conn, user["id"], OWNER, _now_iso(), granted_by=None)
    if eh_admin and ROLE_ADMIN not in atuais:
        db.grant_role(conn, user["id"], ROLE_ADMIN, _now_iso(), granted_by=None)
