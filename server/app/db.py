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
def get_user_by_id(conn: sqlite3.Connection, user_id: str):
    row = conn.execute(
        "SELECT id, email, provider, provider_sub, name, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    return _user_row(row)


def get_user_by_email(conn: sqlite3.Connection, email: str):
    row = conn.execute(
        "SELECT id, email, provider, provider_sub, name, created_at, pass_hash FROM users WHERE email = ?",
        ((email or "").strip().lower(),),
    ).fetchone()
    if row is None:
        return None
    u = _user_row(row[:6])
    u["pass_hash"] = row[6]
    return u


def get_user_by_provider(conn: sqlite3.Connection, provider: str, sub: str):
    row = conn.execute(
        "SELECT id, email, provider, provider_sub, name, created_at FROM users "
        "WHERE provider = ? AND provider_sub = ?",
        (provider, sub),
    ).fetchone()
    return _user_row(row)


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
    }
