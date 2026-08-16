"""Persistencia em SQLite (somente stdlib). Caminho ABSOLUTO e estavel,
independente do diretorio de onde o app e iniciado.

Modelo simples chave-valor: cada secao do estado (config, skill, watchlist,
cash, positions, history, agent) e uma linha com o valor em JSON.
"""
from typing import Optional
import json
import os
import sqlite3
import threading
from pathlib import Path


def default_db_path() -> str:
    """Caminho absoluto e estavel do banco.

    - Se B3_DB_PATH estiver definido, usa-o (resolvido para absoluto).
    - Senao, usa <server>/data/b3_agente.db, derivado da localizacao deste
      arquivo (NAO do cwd), garantindo o mesmo caminho de qualquer diretorio.
    """
    env = os.environ.get("B3_DB_PATH")
    if env:
        return str(Path(env).expanduser().resolve())
    server_dir = Path(__file__).resolve().parent.parent  # .../server
    return str((server_dir / "data" / "b3_agente.db").resolve())


def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or default_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    # FIX (thread-safety): com uma conexão POR THREAD (ver shared()), escritas
    # concorrentes podem colidir no lock do WAL. busy_timeout faz o SQLite
    # esperar (até 5s) em vez de falhar na hora com "database is locked".
    conn.execute("PRAGMA busy_timeout=5000")
    init_db(conn)
    return conn


class _ThreadLocalConnection:
    """FIX (thread-safety): UMA conexão SQLite por thread, atrás da mesma
    interface de `sqlite3.Connection` (delegação via __getattr__).

    Por quê: o FastAPI executa dependências e handlers síncronos num POOL de
    threads (anyio). Uma conexão global criada na thread principal explode com
    `sqlite3.ProgrammingError: SQLite objects created in a thread can only be
    used in that same thread` quando a requisição cai em outra thread — foi a
    causa do 500 intermitente em toda rota autenticada (/api/scan, /auth/me...).

    Cada thread do pool (quantidade limitada e reutilizada) abre a própria
    conexão sob demanda, com WAL + busy_timeout — exatamente o cenário para o
    qual o WAL foi desenhado. Nenhum call site muda: `_conn.execute(...)`,
    `_conn.commit()` etc. continuam idênticos.
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path
        self._local = threading.local()

    def _conn_for_thread(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = connect(self._db_path)
            self._local.conn = conn
        return conn

    def __getattr__(self, name):
        return getattr(self._conn_for_thread(), name)


def shared(db_path: Optional[str] = None) -> _ThreadLocalConnection:
    """Conexão compartilhável entre threads (uma real por thread). Uso: o
    singleton do app em main.py. Testes seguem usando connect(path) direto."""
    return _ThreadLocalConnection(db_path)


def init_db(conn: sqlite3.Connection) -> None:
    # KV global/legado (escopo anônimo). Preservado byte-a-byte: as suítes
    # existentes e o cliente web sem login continuam usando a chave "crua".
    conn.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    # FASE 2 (multiusuário) — schema novo, limpo, com user_id. Aditivo: estas
    # tabelas nascem vazias e não tocam no kv legado.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        " id TEXT PRIMARY KEY,"
        " email TEXT UNIQUE,"
        " provider TEXT NOT NULL,"            # 'email' | 'apple' | 'google'
        " provider_sub TEXT,"                 # subject do provedor OIDC (apple/google)
        " pass_hash TEXT,"                    # só para provider='email' (PBKDF2)
        " name TEXT,"
        " created_at TEXT NOT NULL,"
        " UNIQUE(provider, provider_sub)"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sessions ("
        " token TEXT PRIMARY KEY,"
        " user_id TEXT NOT NULL,"
        " created_at TEXT NOT NULL,"
        " expires_at TEXT NOT NULL,"
        " FOREIGN KEY(user_id) REFERENCES users(id)"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
    # FASE 5 (performance): cache PERSISTENTE de candles. Antes o cache vivia só
    # em memória — cada redeploy do Railway recomeçava do zero e a 1ª varredura
    # rebaixava 2 anos de candles do universo inteiro (a "demora para atualizar").
    # Com o L2 em SQLite (no volume /data), o boot reidrata e só busca o DELTA.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS candle_cache ("
        " k TEXT PRIMARY KEY,"       # "SYMBOL@interval"
        " currency TEXT,"
        " candles TEXT NOT NULL,"    # JSON da série (cap ~600 candles)
        " at REAL NOT NULL"          # epoch da última atualização
        ")"
    )
    # ADR-008 (Fase 4): fonte da última escrita da série ("yahoo" | "brapi").
    # Migração idempotente — bancos existentes ganham a coluna; NULL = legado.
    try:
        conn.execute("ALTER TABLE candle_cache ADD COLUMN src TEXT")
    except sqlite3.OperationalError:
        pass   # coluna já existe

    # ADR-013 — RBAC/entitlements. `plan` é o eixo de MONETIZAÇÃO (ADR-010:
    # free|pro, por conta, recibo validado — sem tela de override manual
    # nesta rodada). Independente do eixo de GOVERNANÇA (user_roles abaixo).
    try:
        conn.execute("ALTER TABLE users ADD COLUMN plan TEXT NOT NULL DEFAULT 'free'")
    except sqlite3.OperationalError:
        pass   # coluna já existe

    # Papel de governança: grupos por MACRO FUNÇÃO de produto (observabilidade,
    # operador_ia, execucao_automatica, llm, fontes_dados, prompts, usuarios) +
    # `role_admin` (bootstrap, união de todos — migração aditiva do
    # `_is_obs_admin` binário de hoje). Many-to-many: um usuário pode acumular
    # vários grupos sem reescrever o modelo.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS user_roles ("
        " user_id TEXT NOT NULL,"
        " role TEXT NOT NULL,"
        " granted_at TEXT NOT NULL,"
        " granted_by TEXT,"            # user_id de quem concedeu; NULL = bootstrap automático
        " PRIMARY KEY(user_id, role),"
        " FOREIGN KEY(user_id) REFERENCES users(id)"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id)")

    # Config de admin editável em runtime (chave/valor JSON), lida ANTES do env
    # var pelos módulos que hoje só leem env (managed.py, agent.py kill-switch).
    # O env continua como piso de bootstrap/infra — nunca removido.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS admin_config ("
        " key TEXT PRIMARY KEY,"
        " value TEXT NOT NULL,"        # JSON
        " updated_by TEXT,"
        " updated_at TEXT NOT NULL"
        ")"
    )

    # Auditoria: TODA escrita de admin (config, fontes de dados, prompts,
    # papéis) grava uma linha aqui — sem opt-out por rota (restrição do ADR).
    conn.execute(
        "CREATE TABLE IF NOT EXISTS admin_audit_log ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " actor_user_id TEXT NOT NULL,"
        " at TEXT NOT NULL,"
        " entity TEXT NOT NULL,"       # ex.: 'admin_config', 'prompt_default', 'user_role'
        " entity_id TEXT,"
        " field TEXT,"
        " old_value TEXT,"
        " new_value TEXT"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_at ON admin_audit_log(at)")

    # ADR-013 (Decisão 5a): override do admin sobre o default GLOBAL de
    # llmPrompts — camada NOVA, por cima do código (`defaults.py` não muda,
    # `catalog.js` não muda, `test_a8ii` não muda). `prompt_default_history`
    # estende o mesmo mecanismo que já existe em `LEGACY_PROMPT_SHA256`
    # (hash do texto ANTIGO => usuário que nunca editou migra pro novo
    # default; quem editou o próprio texto nunca é sobrescrito).
    conn.execute(
        "CREATE TABLE IF NOT EXISTS prompt_defaults_override ("
        " chave TEXT PRIMARY KEY,"
        " texto TEXT NOT NULL,"
        " updated_by TEXT,"
        " updated_at TEXT NOT NULL"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS prompt_default_history ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " chave TEXT NOT NULL,"
        " sha256 TEXT NOT NULL,"
        " texto TEXT NOT NULL,"
        " criado_em TEXT NOT NULL"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt_history_chave ON prompt_default_history(chave, sha256)")
    conn.commit()


def _scoped(key: str, user_id: Optional[str]) -> str:
    """Namespacing das seções por usuário. user_id=None => chave legada/global
    (escopo anônimo: web sem login + suítes de teste)."""
    return key if user_id is None else "u:" + str(user_id) + ":" + key


def kv_get(conn: sqlite3.Connection, key: str, default=None, user_id: Optional[str] = None):
    row = conn.execute("SELECT value FROM kv WHERE key = ?", (_scoped(key, user_id),)).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row[0])
    except (ValueError, TypeError):
        return default


def kv_set(conn: sqlite3.Connection, key: str, value, user_id: Optional[str] = None) -> None:
    payload = json.dumps(value, ensure_ascii=False)
    conn.execute(
        "INSERT INTO kv(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (_scoped(key, user_id), payload),
    )
    conn.commit()


def kv_delete_user(conn: sqlite3.Connection, user_id: str) -> int:
    """Apaga TODAS as seções do kv pertencentes a um usuário (exclusão de conta).
    Não toca no escopo global/legado."""
    # user_id é gerado como hex (secrets.token_hex) — sem curingas de LIKE.
    prefix = "u:" + str(user_id) + ":"
    cur = conn.execute("DELETE FROM kv WHERE key LIKE ?", (prefix + "%",))
    conn.commit()
    return cur.rowcount


# ----------------------------- users / sessions -----------------------------
_USER_COLS = "id, email, provider, provider_sub, name, created_at, plan"


def get_user_by_id(conn: sqlite3.Connection, user_id: str):
    row = conn.execute(
        f"SELECT {_USER_COLS} FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    return _user_row(row)


def get_user_by_email(conn: sqlite3.Connection, email: str):
    row = conn.execute(
        f"SELECT {_USER_COLS}, pass_hash FROM users WHERE email = ?",
        ((email or "").strip().lower(),),
    ).fetchone()
    if row is None:
        return None
    u = _user_row(row[:7])
    u["pass_hash"] = row[7]
    return u


def get_user_by_provider(conn: sqlite3.Connection, provider: str, sub: str):
    row = conn.execute(
        f"SELECT {_USER_COLS} FROM users "
        "WHERE provider = ? AND provider_sub = ?",
        (provider, sub),
    ).fetchone()
    return _user_row(row)


def set_user_plan(conn: sqlite3.Connection, user_id: str, plan: str) -> None:
    """ADR-013: eixo de monetização, por conta. Sem tela de override manual
    nesta rodada (decisão do Alex) — função existe para a migração/uso
    programático (ex.: validação de recibo, quando o ADR-010 ligar isso)."""
    conn.execute("UPDATE users SET plan = ? WHERE id = ?", (plan, user_id))
    conn.commit()


def insert_user(conn: sqlite3.Connection, user: dict) -> None:
    conn.execute(
        "INSERT INTO users(id, email, provider, provider_sub, pass_hash, name, created_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (
            user["id"],
            (user.get("email") or None),
            user["provider"],
            user.get("provider_sub"),
            user.get("pass_hash"),
            user.get("name"),
            user["created_at"],
        ),
    )
    conn.commit()


def update_user_email(conn: sqlite3.Connection, user_id: str, email: str) -> None:
    """FASE 8B (R5): atualiza o e-mail da conta (ex.: usuário refez o
    consentimento da Apple compartilhando o e-mail real no lugar do relay)."""
    conn.execute("UPDATE users SET email = ? WHERE id = ?", ((email or "").strip().lower() or None, user_id))
    conn.commit()


def delete_user(conn: sqlite3.Connection, user_id: str) -> None:
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()


def insert_session(conn: sqlite3.Connection, token: str, user_id: str, created_at: str, expires_at: str) -> None:
    conn.execute(
        "INSERT INTO sessions(token, user_id, created_at, expires_at) VALUES(?,?,?,?)",
        (token, user_id, created_at, expires_at),
    )
    conn.commit()


def get_session(conn: sqlite3.Connection, token: str):
    row = conn.execute(
        "SELECT token, user_id, created_at, expires_at FROM sessions WHERE token = ?",
        (token,),
    ).fetchone()
    if row is None:
        return None
    return {"token": row[0], "user_id": row[1], "created_at": row[2], "expires_at": row[3]}


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()


def list_users(conn: sqlite3.Connection, limit: int = 500) -> list:
    """F5 (admin, só ver): usuários cadastrados, mais recente primeiro. NUNCA
    inclui pass_hash — mesmas colunas de get_user_by_id (sem a senha)."""
    rows = conn.execute(
        f"SELECT {_USER_COLS} FROM users "
        "ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [_user_row(r) for r in rows]


def _user_row(row):
    if row is None:
        return None
    return {
        "id": row[0],
        "email": row[1],
        "provider": row[2],
        "provider_sub": row[3],
        "name": row[4],
        "created_at": row[5],
        "plan": row[6] if len(row) > 6 and row[6] else "free",
    }


# ------------------------------ ADR-013: RBAC -------------------------------
def grant_role(conn: sqlite3.Connection, user_id: str, role: str, granted_at: str, granted_by: Optional[str] = None) -> None:
    conn.execute(
        "INSERT INTO user_roles(user_id, role, granted_at, granted_by) VALUES(?,?,?,?) "
        "ON CONFLICT(user_id, role) DO NOTHING",
        (user_id, role, granted_at, granted_by),
    )
    conn.commit()


def revoke_role(conn: sqlite3.Connection, user_id: str, role: str) -> None:
    conn.execute("DELETE FROM user_roles WHERE user_id = ? AND role = ?", (user_id, role))
    conn.commit()


def roles_for_user(conn: sqlite3.Connection, user_id: str) -> list:
    rows = conn.execute("SELECT role FROM user_roles WHERE user_id = ?", (user_id,)).fetchall()
    return [r[0] for r in rows]


def any_role_granted(conn: sqlite3.Connection) -> bool:
    """Já existe QUALQUER papel concedido? Usado pelo bootstrap para saber se
    a migração automática do `_is_obs_admin` já rodou (idempotência barata,
    sem precisar checar usuário por usuário)."""
    return conn.execute("SELECT 1 FROM user_roles LIMIT 1").fetchone() is not None


# --------------------------- ADR-013: admin_config ---------------------------
def admin_config_get(conn: sqlite3.Connection, key: str, default=None):
    row = conn.execute("SELECT value FROM admin_config WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row[0])
    except (ValueError, TypeError):
        return default


def admin_config_set(conn: sqlite3.Connection, key: str, value, updated_by: str, updated_at: str) -> None:
    payload = json.dumps(value, ensure_ascii=False)
    conn.execute(
        "INSERT INTO admin_config(key, value, updated_by, updated_at) VALUES(?,?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_by = excluded.updated_by, updated_at = excluded.updated_at",
        (key, payload, updated_by, updated_at),
    )
    conn.commit()


# ---------------------------- ADR-013: audit log -----------------------------
def audit_insert(conn: sqlite3.Connection, actor_user_id: str, at: str, entity: str,
                 entity_id: Optional[str], field: Optional[str], old_value, new_value) -> None:
    conn.execute(
        "INSERT INTO admin_audit_log(actor_user_id, at, entity, entity_id, field, old_value, new_value) "
        "VALUES(?,?,?,?,?,?,?)",
        (actor_user_id, at, entity, entity_id, field,
         json.dumps(old_value, ensure_ascii=False) if old_value is not None else None,
         json.dumps(new_value, ensure_ascii=False) if new_value is not None else None),
    )
    conn.commit()


def audit_recent(conn: sqlite3.Connection, limit: int = 200) -> list:
    rows = conn.execute(
        "SELECT id, actor_user_id, at, entity, entity_id, field, old_value, new_value "
        "FROM admin_audit_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    out = []
    for r in rows:
        def _load(v):
            if v is None:
                return None
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return v
        out.append({
            "id": r[0], "actorUserId": r[1], "at": r[2], "entity": r[3],
            "entityId": r[4], "field": r[5], "oldValue": _load(r[6]), "newValue": _load(r[7]),
        })
    return out


# ------------------------- ADR-013: prompts (default) ------------------------
def prompt_override_get_all(conn: sqlite3.Connection) -> dict:
    rows = conn.execute("SELECT chave, texto FROM prompt_defaults_override").fetchall()
    return {r[0]: r[1] for r in rows}


def prompt_override_get(conn: sqlite3.Connection, chave: str):
    row = conn.execute("SELECT texto FROM prompt_defaults_override WHERE chave = ?", (chave,)).fetchone()
    return row[0] if row else None


def prompt_override_set(conn: sqlite3.Connection, chave: str, texto: str, updated_by: str, updated_at: str) -> None:
    conn.execute(
        "INSERT INTO prompt_defaults_override(chave, texto, updated_by, updated_at) VALUES(?,?,?,?) "
        "ON CONFLICT(chave) DO UPDATE SET texto = excluded.texto, updated_by = excluded.updated_by, updated_at = excluded.updated_at",
        (chave, texto, updated_by, updated_at),
    )
    conn.commit()


def prompt_history_add(conn: sqlite3.Connection, chave: str, sha256: str, texto: str, criado_em: str) -> None:
    conn.execute(
        "INSERT INTO prompt_default_history(chave, sha256, texto, criado_em) VALUES(?,?,?,?)",
        (chave, sha256, texto, criado_em),
    )
    conn.commit()


def prompt_history_hashes(conn: sqlite3.Connection, chave: str) -> set:
    rows = conn.execute("SELECT sha256 FROM prompt_default_history WHERE chave = ?", (chave,)).fetchall()
    return {r[0] for r in rows}
