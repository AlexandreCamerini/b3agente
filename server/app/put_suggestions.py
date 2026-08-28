"""server/app/put_suggestions.py — persistência da sugestão de put de
proteção (Fase 10, Plano 01, Task 1).

Tabela SEPARADA de `signal_ledger` (ver comentário completo em
`db.init_db`, bloco `put_suggestions`, e D-10-A do plano): a agregação do
ADR-017 (`signal_ledger.agregar_cumulativo`) é `GROUP BY setup` sobre a
tabela inteira e não pode enxergar uma linha de opção — misturaria o
denominador `n`/soma `r` que `regime.ranquear()` usa para pesar setups no
Radar. Este módulo nunca importa `signal_ledger`, `agent`, `main` ou `store`.

`registrar` é a ÚNICA porta de escrita e é estruturalmente incapaz de gravar
uma sugestão inventada: falta de `estilo_exercicio`/`iv`/qualquer campo de
`CAMPOS_OBRIGATORIOS` devolve 0 sem tentar INSERT (o NOT NULL do schema
seria a segunda linha de defesa, mas a primeira nunca gasta uma tentativa
com dado incompleto). `option_type` é forçado em código — nunca lido do
input — e o `CHECK(option_type = 'put')` do schema torna uma linha de call
ou opção vendida estruturalmente irrepresentável.
"""
from __future__ import annotations

from . import db
from .tickers import normalize_ticker

TABELA = "put_suggestions"
ESTADO_INICIAL = "armada"

CAMPOS_OBRIGATORIOS = (
    "user_id", "ticker", "data_pregao", "setup",
    "contrato", "strike", "vencimento",
    "estilo_exercicio", "iv", "fonte",
)

# Coluna (snake_case, lado do banco) → chave (camelCase, lado de fora). Uma
# constante única usada tanto pelo SELECT (listar) quanto pelo INSERT
# (registrar) — os dois nunca podem divergir.
_COLUNAS: tuple[tuple[str, str], ...] = (
    ("user_id", "userId"),
    ("ticker", "ticker"),
    ("data_pregao", "dataPregao"),
    ("setup", "setup"),
    ("lado", "lado"),
    ("contrato", "contrato"),
    ("option_type", "optionType"),
    ("strike", "strike"),
    ("vencimento", "vencimento"),
    ("estilo_exercicio", "estiloExercicio"),
    ("iv", "iv"),
    ("delta", "delta"),
    ("premio", "premio"),
    ("volume", "volume"),
    ("spot", "spot"),
    ("estado", "estado"),
    ("fonte", "fonte"),
    ("as_of", "asOf"),
    ("prov_sha256", "provSha256"),
    ("prov_dt_captura", "provDtCaptura"),
    ("prov_captura", "provCaptura"),
    ("criado_em", "criadoEm"),
)


def registrar(conn, linha: dict) -> int:
    """Grava uma sugestão de put. Devolve 1 se a linha é NOVA, 0 se já
    existia (mesma `user_id`/`ticker`/`data_pregao`) ou se a linha estava
    incompleta — nunca levanta por dado ausente, quem chama decide o que
    logar."""
    ticker_norm = normalize_ticker(linha.get("ticker")) if linha.get("ticker") else None
    candidato = dict(linha)
    candidato["ticker"] = ticker_norm

    for campo in CAMPOS_OBRIGATORIOS:
        valor = candidato.get(campo)
        if valor is None or valor == "":
            return 0

    candidato["option_type"] = "put"  # nunca lido do input
    candidato.setdefault("estado", ESTADO_INICIAL)
    candidato["criado_em"] = db._now_iso()

    valores = [candidato.get(coluna) for coluna, _ in _COLUNAS]
    cols_sql = ", ".join(coluna for coluna, _ in _COLUNAS)
    placeholders = ", ".join("?" for _ in _COLUNAS)

    antes = conn.total_changes
    conn.execute(
        f"INSERT OR IGNORE INTO {TABELA}({cols_sql}) VALUES({placeholders})",
        valores,
    )
    conn.commit()
    return conn.total_changes - antes


def listar(conn, user_id: str | None = None, data_pregao: str | None = None) -> list[dict]:
    """Devolve as sugestões gravadas, mais recentes primeiro. Chaves de saída
    em camelCase (dialeto JSON do resto do backend) — a tabela fala
    snake_case internamente, o mapeamento é `_COLUNAS`."""
    cols_sql = ", ".join(coluna for coluna, _ in _COLUNAS) + ", id"
    where = []
    params: list = []
    if user_id is not None:
        where.append("user_id = ?")
        params.append(user_id)
    if data_pregao is not None:
        where.append("data_pregao = ?")
        params.append(data_pregao)
    sql = f"SELECT {cols_sql} FROM {TABELA}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC"
    rows = conn.execute(sql, params).fetchall()
    chaves = [chave for _, chave in _COLUNAS] + ["id"]
    return [dict(zip(chaves, row)) for row in rows]


def contar(conn) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {TABELA}").fetchone()[0]
