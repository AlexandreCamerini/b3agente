"""Persistencia em SQLite (somente stdlib). Caminho ABSOLUTO e estavel,
independente do diretorio de onde o app e iniciado.

Modelo simples chave-valor: cada secao do estado (config, skill, watchlist,
cash, positions, history, agent) e uma linha com o valor em JSON.
"""
from datetime import datetime, timezone
from typing import Optional
import json
import os
import secrets
import sqlite3
import threading
from pathlib import Path


def _now_iso() -> str:
    """Timestamp ISO único para as colunas de auditoria deste módulo — evita
    que cada chamador gere o próprio formato (achado de revisão: agent.py e
    main.py gravavam formatos diferentes na mesma coluna admin_config.updated_at)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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
        " email TEXT UNIQUE,"                 # e-mail de EXIBIÇÃO da conta — pode não bater
        " provider TEXT NOT NULL,"            # com o de toda identidade (ex.: Apple relay).
        " provider_sub TEXT,"                 # LEGADO (2026-08-16): a 1ª identidade da conta,
        " pass_hash TEXT,"                    # mantido só pra quem lê estas colunas direto sem
        " name TEXT,"                         # passar por identities — nunca mais escrito depois
        " created_at TEXT NOT NULL,"          # da migração (db.migrate_identities_from_users).
        " plan TEXT NOT NULL DEFAULT 'free',"
        " UNIQUE(provider, provider_sub)"
        ")"
    )
    # 2026-08-17 — uma conta, VÁRIOS métodos de login. Antes `users` era
    # 1 linha = 1 provedor: Google e Apple com o MESMO e-mail viravam contas
    # diferentes (achado real: `upsert_oauth_user` sabia que colidia e criava
    # uma TERCEIRA conta órfã, sem e-mail, só pra não violar o UNIQUE — ver
    # comentário antigo removido de auth.py). `identities` desacopla "quem é a
    # pessoa" (users) de "como ela provou quem é" (identities, N por pessoa).
    #
    # UNIQUE(provider, provider_sub) protege contra a MESMA identidade OAuth
    # se prender a duas contas; para provider='email', provider_sub fica NULL
    # (SQL trata cada NULL como distinto, então isso não barra nada aqui) — a
    # unicidade de login por senha é o índice parcial abaixo, sobre email.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS identities ("
        " id TEXT PRIMARY KEY,"
        " user_id TEXT NOT NULL REFERENCES users(id),"
        " provider TEXT NOT NULL,"            # 'email' | 'apple' | 'google'
        " provider_sub TEXT,"                 # sub OIDC; NULL para 'email'
        " email TEXT,"                        # e-mail QUE ESTA identidade apresentou
        " pass_hash TEXT,"                    # só para provider='email'
        " created_at TEXT NOT NULL,"
        " UNIQUE(provider, provider_sub)"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_identities_user ON identities(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_identities_email ON identities(email)")
    # só um login por SENHA por e-mail — login social pode repetir e-mail
    # entre identidades da MESMA conta (Google e Apple com o mesmo endereço).
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_identities_email_senha "
        "ON identities(email) WHERE provider = 'email'"
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

    # ADR-017 (Bloco 1, Decisão 2) — ledger de sinais resolvidos ("um ledger,
    # duas leituras"). Vive no banco PRINCIPAL, não em `admin_cache`/
    # `analytics.db` (server/app/analytics.py — esse é só observabilidade do
    # portal admin): o motor de decisão (`detect_setups`, `regime.ranquear`)
    # lê daqui, por request, e não pode depender de um banco separado que
    # existe só para o portal.
    #
    # `status` distingue "sem_gatilho" (o sinal existiu mas nunca acionou) de
    # "resolvido" (barreira tripla bateu alvo/stop ou expirou). `sem_gatilho`
    # fica FORA do denominador da expectância — contá-lo como perda infla a
    # taxa de stop pelo mesmo viés que o ADR-015 corrige (entrada nunca
    # acionada não é uma perda de trade).
    #
    # A UNIQUE(ticker, setup, lado, data_sinal) existe porque o bootstrap
    # (Plano 03) é reexecutável e o hook diário (Plano 04) pode sobrepor o
    # cursor — nenhum dos dois pode inflar `n`, o denominador de toda decisão
    # desta fase. `INSERT OR IGNORE` sobre essa UNIQUE é o que torna
    # `signal_ledger.registrar_linhas` idempotente.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS signal_ledger ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " ticker TEXT NOT NULL,"
        " setup TEXT NOT NULL,"           # nome exato de setups.detect_setups, ex. "IFR2 (alta)"
        " lado TEXT,"                     # "alta" | "baixa" | NULL (setup neutro)
        " data_sinal TEXT NOT NULL,"      # "AAAA-MM-DD" do candle da detecção
        " data_resolucao TEXT,"           # "AAAA-MM-DD" do candle que fechou a barreira | NULL
        " resultado TEXT,"                # "alvo" | "stop" | "expirou" | "sem_gatilho"
        " r REAL,"                        # múltiplo do risco do plano | NULL
        " status TEXT NOT NULL,"          # "resolvido" | "sem_gatilho"
        " criado_em TEXT NOT NULL,"       # ISO UTC (db._now_iso())
        " UNIQUE(ticker, setup, lado, data_sinal)"
        ")"
    )
    # Varredura das duas agregações (por setup, filtrando faixa de datas).
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_signal_ledger_setup "
        "ON signal_ledger(setup, lado, data_sinal)"
    )
    # Avanço do cursor incremental do hook diário (Plano 04): "candles novos
    # deste ticker desde a última execução".
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_signal_ledger_ticker "
        "ON signal_ledger(ticker, data_sinal)"
    )

    # FASE 10 (ponte gatilho→put, Plano 01, D-10-A) — sugestão de put de
    # proteção. TABELA SEPARADA do `signal_ledger` de propósito: a agregação
    # do ADR-017 (`signal_ledger.agregar_cumulativo`) é `GROUP BY setup` sobre
    # a tabela INTEIRA, sem coluna discriminadora de tipo de linha — uma
    # sugestão de put ali dentro poluiria `expR`, o número que
    # `regime.ranquear()` usa para pesar setups no Radar. A chave também não
    # cabe (`UNIQUE(ticker, setup, lado, data_sinal)` identifica um sinal de
    # AÇÃO, não uma put de CONTA com contrato/strike/vencimento/estilo). E o
    # escopo diverge: `signal_ledger` é estatística global de mercado
    # (`user_id=None`), enquanto uma sugestão de put aponta para a posição de
    # UM usuário — misturar os dois é o erro que `db._scoped` existe para
    # evitar.
    #
    # `option_type` fixado por CHECK é a garantia ESTRUTURAL de long-only:
    # não existe forma desta tabela representar uma call, uma venda a
    # descoberto ou uma perna vendida — não há coluna de quantidade, margem,
    # garantia ou lado. `estilo_exercicio`/`iv` são NOT NULL porque isso é o
    # schema traduzindo "nunca assumido localmente" (PUT-01): se a fonte não
    # disser, a linha não nasce, sem default e sem fallback.
    #
    # `estado` nasce 'armada' mas este plano NÃO define transições — a
    # máquina de 5 estados é requisito da Fase 11 (PUTLIFE-01); a coluna já
    # existe agora só para a Fase 11 não precisar de migração de schema.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS put_suggestions ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " user_id TEXT NOT NULL,"
        " ticker TEXT NOT NULL,"              # ativo-objeto NORMALIZADO (CR-01)
        " data_pregao TEXT NOT NULL,"         # "AAAA-MM-DD", data BRT da rodada
        " setup TEXT NOT NULL,"               # nome do detector que disparou
        " lado TEXT,"                         # "baixa" | NULL
        " contrato TEXT NOT NULL,"            # contractSymbol da fonte
        " option_type TEXT NOT NULL,"         # sempre "put"
        " strike REAL NOT NULL,"
        " vencimento TEXT NOT NULL,"
        " estilo_exercicio TEXT NOT NULL,"    # SEM default: se a fonte não diz, não grava
        " iv REAL NOT NULL,"                  # volatilidade implícita real da fonte
        " delta REAL,"                        # pode ser NULL (a fonte nem sempre publica)
        " premio REAL,"                       # lastPrice do contrato
        " volume INTEGER,"                    # quantidade_negociada (D-10-E)
        " spot REAL,"                         # underlyingPrice do payload
        " estado TEXT NOT NULL DEFAULT 'armada',"
        " fonte TEXT NOT NULL,"               # payload["source"], ex. "mydata"
        " as_of TEXT,"                        # payload["pregao"] (dt_pregao do hub)
        " prov_sha256 TEXT,"
        " prov_dt_captura TEXT,"
        " prov_captura TEXT,"
        " criado_em TEXT NOT NULL,"
        " CHECK (option_type = 'put'),"
        " UNIQUE(user_id, ticker, data_pregao)"
        ")"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_put_suggestions_user "
        "ON put_suggestions(user_id, data_pregao)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_put_suggestions_ticker "
        "ON put_suggestions(ticker, data_pregao)"
    )

    _migrate_identities_from_users(conn)
    conn.commit()


def _migrate_identities_from_users(conn: sqlite3.Connection) -> None:
    """Backfill idempotente (2026-08-17): toda `users` SEM nenhuma linha em
    `identities` ganha uma, a partir das colunas legadas (provider/
    provider_sub/pass_hash/email). Roda em TODO boot — barato (o `WHERE NOT
    EXISTS` normalmente não acha nada depois da 1ª vez) e sem passo manual:
    cobre a base de produção sozinha, sem script à parte pra rodar via ssh.

    POR LINHA, nunca em lote: nenhuma outra rotina deste arquivo derruba o
    boot por uma falha auxiliar (mesmo padrão de `candle_cache`/ADR-013 acima
    — try/except e segue). Uma linha ruim (usuário legado com dado
    inconsistente, por exemplo) não pode impedir o processo de subir."""
    try:
        rows = conn.execute(
            "SELECT u.id, u.provider, u.provider_sub, u.pass_hash, u.email, u.created_at FROM users u "
            "WHERE NOT EXISTS (SELECT 1 FROM identities i WHERE i.user_id = u.id)"
        ).fetchall()
    except sqlite3.OperationalError:
        return  # tabela identities ainda não existe neste conn (não deveria, mas nunca derruba)
    for uid, provider, sub, pass_hash, email, created_at in rows:
        try:
            conn.execute(
                "INSERT INTO identities(id, user_id, provider, provider_sub, email, pass_hash, created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (secrets.token_hex(16), uid, provider, sub, email, pass_hash, created_at),
            )
        except sqlite3.Error as e:  # noqa: BLE001 — 1 conta ruim não trava o boot de ninguém
            print(f"[db] migração de identities: {uid[:8]}… falhou: {e}")


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


# ------------------------------- identities ---------------------------------
# 2026-08-17: uma conta (users) pode ter VÁRIAS identidades (métodos de
# login) — Google, Apple, senha, cada uma com seu e-mail próprio. Ver
# comentário completo em init_db(), acima da CREATE TABLE.
_IDENTITY_COLS = "id, user_id, provider, provider_sub, email, pass_hash, created_at"


def _identity_row(row):
    if row is None:
        return None
    return {
        "id": row[0], "user_id": row[1], "provider": row[2], "provider_sub": row[3],
        "email": row[4], "pass_hash": row[5], "created_at": row[6],
    }


def get_identity_by_provider(conn: sqlite3.Connection, provider: str, sub):
    row = conn.execute(
        f"SELECT {_IDENTITY_COLS} FROM identities WHERE provider = ? AND provider_sub {'IS' if sub is None else '='} ?",
        (provider, sub),
    ).fetchone()
    return _identity_row(row)


def get_identity_by_email_senha(conn: sqlite3.Connection, email: str):
    """A identidade de SENHA (provider='email') pro login por e-mail — não
    confundir com `get_user_by_email` (a conta, que pode ter e-mail de OUTRA
    identidade como e-mail de exibição)."""
    row = conn.execute(
        f"SELECT {_IDENTITY_COLS} FROM identities WHERE provider = 'email' AND email = ?",
        ((email or "").strip().lower(),),
    ).fetchone()
    return _identity_row(row)


def find_user_id_by_verified_email(conn: sqlite3.Connection, email: str, exclude_user_id: str = None):
    """Existe ALGUMA identidade (qualquer provedor, de OUTRA conta) com este
    e-mail? Só chamar com e-mail que o PRÓPRIO chamador já confirmou
    verificado (OAuth `email_verified`) — nunca com e-mail auto-declarado
    (cadastro por senha), senão vira sequestro de conta: bastaria digitar o
    e-mail de outra pessoa. `exclude_user_id` serve os dois chamadores: (a)
    identidade NOVA — nada a excluir, a busca é livre; (b) identidade
    EXISTENTE trocando de e-mail — exclui a própria conta, pra achar só
    colisão com conta ALHEIA (mesmo teste de antes: em colisão, mantém)."""
    e = (email or "").strip().lower()
    if not e:
        return None
    row = conn.execute(
        "SELECT user_id FROM identities WHERE email = ? AND user_id != ? LIMIT 1",
        (e, exclude_user_id or ""),
    ).fetchone()
    return row[0] if row else None


def insert_identity(conn: sqlite3.Connection, identity: dict) -> str:
    iid = secrets.token_hex(16)
    conn.execute(
        "INSERT INTO identities(id, user_id, provider, provider_sub, email, pass_hash, created_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (iid, identity["user_id"], identity["provider"], identity.get("provider_sub"),
         identity.get("email"), identity.get("pass_hash"), _now_iso()),
    )
    conn.commit()
    return iid


def update_identity_email(conn: sqlite3.Connection, identity_id: str, email: str) -> None:
    conn.execute("UPDATE identities SET email = ? WHERE id = ?", (email, identity_id))
    conn.commit()


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


def user_ids_with_roles(conn: sqlite3.Connection, roles: list) -> list:
    """Lista de `user_id` DISTINTOS com QUALQUER um dos papéis dados.

    Uso INTERNO (scheduler/alertas do C-37) — NENHUMA rota HTTP deve chamar
    esta função: enumerar quem tem papel administrativo é informação de
    valor para um atacante (T-03-23). `roles_for_user` (acima) continua
    sendo a única consulta exposta por rota, e é por usuário, não a lista
    inteira.
    """
    if not roles:
        return []
    # Nunca f-string com a query inteira (guardião T-03-24): só os
    # placeholders "?" variam com o tamanho da lista, os VALORES sempre
    # viajam parametrizados — nenhum `role` é interpolado no texto do SQL.
    placeholders = ",".join("?" for _ in roles)
    sql = "SELECT DISTINCT user_id FROM user_roles WHERE role IN (" + placeholders + ")"
    rows = conn.execute(sql, list(roles)).fetchall()
    return [r[0] for r in rows]


# --------------------------- ADR-013: admin_config ---------------------------
def admin_config_get(conn: sqlite3.Connection, key: str, default=None):
    row = conn.execute("SELECT value FROM admin_config WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row[0])
    except (ValueError, TypeError):
        return default


def admin_config_set(conn: sqlite3.Connection, key: str, value, updated_by: Optional[str] = None) -> None:
    """`updated_at` é gerado AQUI (não recebido do chamador) — achado de
    revisão: dois chamadores geravam o timestamp cada um com seu próprio
    formato local, gravando valores incompatíveis na mesma coluna."""
    payload = json.dumps(value, ensure_ascii=False)
    conn.execute(
        "INSERT INTO admin_config(key, value, updated_by, updated_at) VALUES(?,?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_by = excluded.updated_by, updated_at = excluded.updated_at",
        (key, payload, updated_by, _now_iso()),
    )
    conn.commit()


def admin_config_delete(conn: sqlite3.Connection, key: str) -> None:
    """Limpa um override — a leitura volta a cair no default do chamador
    (env var). Sem isto não havia como reverter um override ruim."""
    conn.execute("DELETE FROM admin_config WHERE key = ?", (key,))
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


def _audit_load(v):
    if v is None:
        return None
    try:
        return json.loads(v)
    except (ValueError, TypeError):
        return v


def _audit_row_to_dict(r) -> dict:
    """Mesmo shape usado por `audit_recent` e `audit_last` — extraído para
    não duplicar o desempacotamento/`json.loads` das colunas."""
    return {
        "id": r[0], "actorUserId": r[1], "at": r[2], "entity": r[3],
        "entityId": r[4], "field": r[5], "oldValue": _audit_load(r[6]), "newValue": _audit_load(r[7]),
    }


def audit_recent(conn: sqlite3.Connection, limit: int = 200) -> list:
    rows = conn.execute(
        "SELECT id, actor_user_id, at, entity, entity_id, field, old_value, new_value "
        "FROM admin_audit_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [_audit_row_to_dict(r) for r in rows]


def audit_last(conn: sqlite3.Connection, entity: str, field: Optional[str] = None):
    """Registro mais recente (maior `id`) daquela entidade/campo, ou `None`.

    Diferente de `audit_recent`: não varre os últimos N — consulta direto
    pela entidade (e opcionalmente o campo), com `ORDER BY id DESC LIMIT 1`.
    Uso: `agent.kill_switch_ligado_desde` (C-37) precisa só da última
    transição de `entity="agent_kill_switch", field="on"`, não do histórico
    inteiro."""
    sql = "SELECT id, actor_user_id, at, entity, entity_id, field, old_value, new_value FROM admin_audit_log WHERE entity = ?"
    params = [entity]
    if field is not None:
        sql += " AND field = ?"
        params.append(field)
    sql += " ORDER BY id DESC LIMIT 1"
    row = conn.execute(sql, params).fetchone()
    return _audit_row_to_dict(row) if row is not None else None


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
