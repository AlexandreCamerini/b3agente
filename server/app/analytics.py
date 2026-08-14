"""qa/47 — Analytics de comportamento do usuário: ingest genérico + rollup
diário + purga + leitura admin (Fase 1, infra de backend só — sem client SDK,
sem dashboard, ver qa/47-plano-observabilidade-analytics-fase1.md).

Banco SEPARADO (`analytics.db`, mesmo diretório de B3_DB_PATH — ver
`db.default_db_path()`) do banco transacional (`b3_agente.db`): dataset
aditivo e purgável não deve competir pelo WAL/lock do banco que atende toda
rota autenticada do app.

Schema de evento GENÉRICO (`event` livre + `properties` livre) porque a
especificação original de taxonomia (os "12 eventos") foi perdida antes desta
rodada — instrumentar nomes fixos aqui seria inventar dado que a spec talvez
nunca tivesse. A validação de conteúdo (Decisão do escopo proibido) barra
CHAVES conhecidas de PII/dinheiro real em `properties`, não valores — não há
como este módulo saber se um valor de string é um CPF sem a chave dizer isso.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from . import db as db_mod

RETENCAO_DIAS = 90
BRT = timezone(timedelta(hours=-3))

# Chaves de `properties` que NUNCA podem ser aceitas (case-insensitive,
# substring) — o batch inteiro é rejeitado (400), não filtrado em silêncio.
_CHAVES_PROIBIDAS = ("email", "cpf", "senha", "password", "token", "saldoreal", "valorreal", "cartao")

# Telemetria em memória do último rollup (aparece em /api/obs/logs via obslog
# no call site; aqui é só o estado bruto, mesmo padrão de radar_daily.LAST_DAILY).
LAST_ROLLUP = {"date": None, "eventos": None, "purgados": None, "erro": None}


def default_db_path() -> str:
    """qa/47 Decisão 2: MESMO diretório de B3_DB_PATH (dentro do volume
    persistente do Railway), nunca relativo ao cwd do processo."""
    return str((Path(db_mod.default_db_path()).parent / "analytics.db").resolve())


def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or default_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    init_db(conn)
    return conn


class _ThreadLocalConnection:
    """Mesma estratégia de `db._ThreadLocalConnection` — uma conexão SQLite
    por thread do pool do FastAPI (ver db.py para o porquê)."""

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
    return _ThreadLocalConnection(db_path)


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS analytics_events ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " user_id TEXT,"
        " event TEXT NOT NULL,"
        " properties TEXT,"
        " client_ts REAL,"
        " ingested_at REAL NOT NULL,"
        " day TEXT NOT NULL"
        ")"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_day ON analytics_events(day)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_event ON analytics_events(event)")
    # Rollup: sobrevive à purga do dado bruto (RETENCAO_DIAS) — preserva
    # contagem histórica. distinct_users além da retenção vira soma de
    # diários (upper bound), não distinct exato entre dias — ver qa/47.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS analytics_daily ("
        " day TEXT NOT NULL,"
        " event TEXT NOT NULL,"
        " count INTEGER NOT NULL,"
        " distinct_users INTEGER NOT NULL,"
        " PRIMARY KEY(day, event)"
        ")"
    )
    # ADR-012: cache genérico p/ agregados caros do portal admin (ex.
    # eficiência da IA cross-usuário) — 1 linha por chave, recomputada 1x/dia
    # pelo hook do scheduler que "dono" da chave escolher. Evita recálculo
    # síncrono pesado em toda request GET do admin.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS admin_cache ("
        " key TEXT PRIMARY KEY,"
        " value TEXT NOT NULL,"
        " computed_at TEXT NOT NULL"
        ")"
    )
    conn.commit()


def _dia(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=BRT).strftime("%Y-%m-%d")


def _chave_proibida(properties: dict) -> Optional[str]:
    for k in properties or {}:
        kl = str(k).lower()
        if any(proibida in kl for proibida in _CHAVES_PROIBIDAS):
            return str(k)
    return None


def ingest(conn, user_id: Optional[str], events: list, _now: Optional[float] = None) -> dict:
    """Valida e grava um LOTE (tudo ou nada). Levanta ValueError(msg) se o
    formato for inválido ou alguma `properties` tiver chave proibida — o call
    site (rota) traduz isso em 400, sem gravar nada."""
    now = _now if _now is not None else time.time()
    if not isinstance(events, list) or not events:
        raise ValueError("events deve ser uma lista não-vazia")
    linhas = []
    for e in events:
        if not isinstance(e, dict) or not e.get("event"):
            raise ValueError("cada evento precisa de 'event' (string não-vazia)")
        props = e.get("properties") or {}
        if not isinstance(props, dict):
            raise ValueError("properties deve ser um objeto")
        achada = _chave_proibida(props)
        if achada:
            raise ValueError(f"campo proibido em properties: {achada!r}")
        client_ts = e.get("ts")
        try:
            client_ts = float(client_ts) if client_ts is not None else None
        except (TypeError, ValueError):
            client_ts = None
        linhas.append((
            user_id, str(e["event"])[:200], json.dumps(props, ensure_ascii=False),
            client_ts, now, _dia(now),
        ))
    conn.executemany(
        "INSERT INTO analytics_events(user_id, event, properties, client_ts, ingested_at, day) "
        "VALUES(?,?,?,?,?,?)",
        linhas,
    )
    conn.commit()
    return {"accepted": len(linhas)}


def rollup_day(conn, day: str) -> int:
    """Agrega analytics_events do dia em analytics_daily (upsert, idempotente
    — rodar 2x no mesmo dia não duplica). Retorna nº de eventos distintos agregados."""
    rows = conn.execute(
        "SELECT event, COUNT(*), COUNT(DISTINCT user_id) FROM analytics_events "
        "WHERE day = ? GROUP BY event", (day,),
    ).fetchall()
    for event, count, distinct_users in rows:
        conn.execute(
            "INSERT INTO analytics_daily(day, event, count, distinct_users) VALUES(?,?,?,?) "
            "ON CONFLICT(day, event) DO UPDATE SET count = excluded.count, "
            "distinct_users = excluded.distinct_users",
            (day, event, count, distinct_users),
        )
    conn.commit()
    return len(rows)


def purge_older_than(conn, cutoff_day: str) -> int:
    """Apaga analytics_events com day < cutoff_day. NÃO apaga analytics_daily
    — é ele que preserva a contagem além da janela de retenção do dado bruto."""
    cur = conn.execute("DELETE FROM analytics_events WHERE day < ?", (cutoff_day,))
    conn.commit()
    return cur.rowcount


def enabled() -> bool:
    return not os.environ.get("B3_ANALYTICS_OFF")


# --------------------------- cache genérico (ADR-012) -----------------------

def set_cache(conn, key: str, value) -> None:
    conn.execute(
        "INSERT INTO admin_cache(key, value, computed_at) VALUES(?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, computed_at = excluded.computed_at",
        (key, json.dumps(value, ensure_ascii=False), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def get_cache(conn, key: str) -> Optional[dict]:
    row = conn.execute("SELECT value, computed_at FROM admin_cache WHERE key = ?", (key,)).fetchone()
    if not row:
        return None
    return {"value": json.loads(row[0]), "computedAt": row[1]}


async def maybe_run(conn, _now: Optional[float] = None) -> Optional[dict]:
    """Hook do scheduler (agent.py): roda no máximo 1x/dia — agrega ONTEM e
    purga o que passou de RETENCAO_DIAS. NÃO depende do kill-switch do agente
    (esse é sobre execução de ordens; isto é rollup de dado, sem rede)."""
    if not enabled():
        return None
    now = _now if _now is not None else time.time()
    hoje = datetime.fromtimestamp(now, tz=BRT).date()
    if LAST_ROLLUP["date"] == hoje.isoformat():
        return None
    try:
        ontem = (hoje - timedelta(days=1)).isoformat()
        n_eventos = rollup_day(conn, ontem)
        cutoff = (hoje - timedelta(days=RETENCAO_DIAS)).isoformat()
        n_purgados = purge_older_than(conn, cutoff)
        LAST_ROLLUP.update(date=hoje.isoformat(), eventos=n_eventos, purgados=n_purgados, erro=None)
        return dict(LAST_ROLLUP)
    except Exception as e:  # noqa: BLE001 — rollup nunca derruba o laço do agente
        LAST_ROLLUP["erro"] = str(e)[:200]
        print(f"[analytics] rollup diário falhou: {e}")
        return None


# --------------------------- leitura (GET /api/analytics/summary) ----------
# As 3 queries do plano (qa/47): direto de analytics_events (dado bruto, só
# existe dentro da janela de retenção — precisão total nesse intervalo).

def adocao_por_feature(conn, dias: int = 30, _now: Optional[float] = None) -> list:
    now = _now if _now is not None else time.time()
    desde = (datetime.fromtimestamp(now, tz=BRT).date() - timedelta(days=dias)).isoformat()
    rows = conn.execute(
        "SELECT event, COUNT(*), COUNT(DISTINCT user_id) FROM analytics_events "
        "WHERE day >= ? GROUP BY event ORDER BY COUNT(*) DESC", (desde,),
    ).fetchall()
    return [{"event": r[0], "count": r[1], "usuariosDistintos": r[2]} for r in rows]


def funil(conn, passos: Optional[list] = None, dias: int = 30, _now: Optional[float] = None) -> dict:
    """Funil sequencial: um usuário só conta no passo i se também tiver feito
    o passo i-1 num timestamp <=. Default de 2 passos, taxonomia recuperada
    (qa/47): `onboarding_step_completed` (dispara por PASSO — MIN(ts) aqui
    marca "começou o onboarding", não "terminou"; a spec não nomeia o passo
    final) → `trade_simulated`."""
    passos = list(passos) if passos else ["onboarding_step_completed", "trade_simulated"]
    now = _now if _now is not None else time.time()
    desde = (datetime.fromtimestamp(now, tz=BRT).date() - timedelta(days=dias)).isoformat()
    por_passo = []
    for p in passos:
        rows = conn.execute(
            "SELECT user_id, MIN(COALESCE(client_ts, ingested_at)) FROM analytics_events "
            "WHERE day >= ? AND event = ? AND user_id IS NOT NULL GROUP BY user_id",
            (desde, p),
        ).fetchall()
        por_passo.append({uid: ts for uid, ts in rows})
    resultado = []
    ativos: Optional[set] = None
    for i, p in enumerate(passos):
        atual = por_passo[i]
        if ativos is None:
            ativos = set(atual.keys())
        else:
            anterior = por_passo[i - 1]
            ativos = {uid for uid in ativos if uid in atual and atual[uid] >= anterior[uid]}
        resultado.append({"passo": p, "usuarios": len(ativos)})
    return {"passos": resultado}


def shown_vs_dismissed(conn, dias: int = 30, _now: Optional[float] = None) -> list:
    """Convenção de nome (`*_shown` / `*_dismissed`), não lista fixa — a
    spec perdida talvez usasse outra convenção; documentado como premissa."""
    now = _now if _now is not None else time.time()
    desde = (datetime.fromtimestamp(now, tz=BRT).date() - timedelta(days=dias)).isoformat()
    rows = conn.execute(
        "SELECT event, COUNT(*) FROM analytics_events WHERE day >= ? GROUP BY event", (desde,),
    ).fetchall()
    pares: dict = {}
    for event, count in rows:
        if event.endswith("_shown"):
            base, campo = event[: -len("_shown")], "shown"
        elif event.endswith("_dismissed"):
            base, campo = event[: -len("_dismissed")], "dismissed"
        else:
            continue
        pares.setdefault(base, {"feature": base, "shown": 0, "dismissed": 0})[campo] = count
    return sorted(pares.values(), key=lambda r: r["feature"])
