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

# Fase 11 (PUTLIFE-01) — máquina de estado da sugestão. Rótulo literal do
# ROADMAP preservado byte a byte em `ESTADOS_ROTULO` (tokens DB-friendly nas
# chaves, sem espaço/parêntese — string com parêntese em valor de coluna é
# fonte previsível de bug de query, ver A-11-04 do 11-01-PLAN.md).
ESTADOS_ROTULO = {
    "armada": "armada",
    "expirada_sem_uso": "expirada sem uso",
    "executada_simulada": "executada (simulada)",
    "monitorada": "monitorada",
    "fechada": "fechada",
}
ESTADOS = tuple(ESTADOS_ROTULO)
TERMINAIS = ("expirada_sem_uso", "fechada")
TRANSICOES = {
    "armada": ("expirada_sem_uso", "executada_simulada"),
    # monitorada→monitorada é permitida: remarcação diária (spot/intrínseco
    # do dia), não é uma transição de fato — é a MESMA fase do ciclo (A-11-04).
    "executada_simulada": ("monitorada", "fechada"),
    "monitorada": ("monitorada", "fechada"),
    "expirada_sem_uso": (),  # terminal: tupla vazia, nenhum destino declarado
    "fechada": (),           # terminal: tupla vazia, nenhum destino declarado
}
# Vocabulário do ADR-005 reusado verbatim (motivo de fechamento de posição de
# opção real) — esta fase só produz "vencimento", os demais ficam disponíveis
# para o Plano 02/03 sem precisar de outra fonte de verdade.
MOTIVOS_FECHAMENTO = ("stop", "alvo", "vencimento", "manual")
COLUNAS_CICLO = (
    "executada_em", "preco_entrada", "spot_marcacao", "intrinseco_marcacao",
    "marcada_em", "fechada_em", "preco_fechamento", "motivo_fechamento",
    "pnl_por_acao", "pendente_desde",
)

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
    ("estado_em", "estadoEm"),
    ("executada_em", "executadaEm"),
    ("preco_entrada", "precoEntrada"),
    ("spot_marcacao", "spotMarcacao"),
    ("intrinseco_marcacao", "intrinsecoMarcacao"),
    ("marcada_em", "marcadaEm"),
    ("fechada_em", "fechadaEm"),
    ("preco_fechamento", "precoFechamento"),
    ("motivo_fechamento", "motivoFechamento"),
    ("pnl_por_acao", "pnlPorAcao"),
    ("pendente_desde", "pendenteDesde"),
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


def _select_e_mapear(conn, where: list[str], params: list, ordem: str) -> list[dict]:
    """SELECT+mapeamento compartilhado por `listar`/`listar_abertas` — `_COLUNAS`
    continua sendo a fonte única do mapeamento snake_case/camelCase, os dois
    métodos só variam WHERE e ORDER BY."""
    cols_sql = ", ".join(coluna for coluna, _ in _COLUNAS) + ", id"
    sql = f"SELECT {cols_sql} FROM {TABELA}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY {ordem}"
    rows = conn.execute(sql, params).fetchall()
    chaves = [chave for _, chave in _COLUNAS] + ["id"]
    return [dict(zip(chaves, row)) for row in rows]


def listar(conn, user_id: str | None = None, data_pregao: str | None = None) -> list[dict]:
    """Devolve as sugestões gravadas, mais recentes primeiro. Chaves de saída
    em camelCase (dialeto JSON do resto do backend) — a tabela fala
    snake_case internamente, o mapeamento é `_COLUNAS`."""
    where = []
    params: list = []
    if user_id is not None:
        where.append("user_id = ?")
        params.append(user_id)
    if data_pregao is not None:
        where.append("data_pregao = ?")
        params.append(data_pregao)
    return _select_e_mapear(conn, where, params, "id DESC")


def listar_abertas(conn) -> list[dict]:
    """Sugestões cujo estado NÃO é terminal (`TERMINAIS`), em ordem CRESCENTE
    de `id` — é a lista que o Plano 02 varre diariamente para decidir a
    próxima transição de cada linha."""
    placeholders = ", ".join("?" for _ in TERMINAIS)
    where = [f"estado NOT IN ({placeholders})"]
    return _select_e_mapear(conn, where, list(TERMINAIS), "id ASC")


def contar(conn) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {TABELA}").fetchone()[0]


def transicionar(conn, linha_id: int, estado_novo: str, campos: dict | None = None) -> int:
    """ÚNICA porta de escrita de estado de `put_suggestions` (PUTLIFE-01).
    Devolve 1 se a transição foi aplicada, 0 em qualquer recusa (linha
    ausente, estado inexistente, transição não declarada em `TRANSICOES`,
    terminal tentando avançar) — nunca levanta, quem chama decide o que
    logar.

    `campos` é filtrado pela whitelist `COLUNAS_CICLO` ANTES do UPDATE: é
    isso que torna a proveniência gravada pela Fase 10 (premio/fonte/
    prov_*/iv/estilo_exercicio) estruturalmente imutável por esta porta —
    uma chave fora da whitelist é descartada silenciosamente, nunca levanta
    e nunca é gravada."""
    row = conn.execute(
        "SELECT estado FROM put_suggestions WHERE id = ?", (linha_id,)
    ).fetchone()
    if row is None:
        return 0
    estado_atual = row[0]

    if estado_novo not in ESTADOS:
        return 0
    if estado_novo not in TRANSICOES.get(estado_atual, ()):
        return 0

    campos_filtrados = {
        chave: valor for chave, valor in (campos or {}).items() if chave in COLUNAS_CICLO
    }
    if "motivo_fechamento" in campos_filtrados and campos_filtrados["motivo_fechamento"] not in MOTIVOS_FECHAMENTO:
        campos_filtrados.pop("motivo_fechamento")

    sets_sql = ["estado = ?", "estado_em = ?"]
    valores = [estado_novo, db._now_iso()]
    for chave, valor in campos_filtrados.items():
        sets_sql.append(f"{chave} = ?")
        valores.append(valor)
    valores.append(linha_id)

    antes = conn.total_changes
    conn.execute(
        f"UPDATE {TABELA} SET {', '.join(sets_sql)} WHERE id = ?",
        valores,
    )
    conn.commit()
    return conn.total_changes - antes


def registrar_pendencia(conn, linha_id: int, data: str) -> int:
    """A linha não pôde avançar hoje por falta de preço confiável do
    ativo-objeto (ADR-004: nunca marcar sobre dado degradado). Grava
    `pendente_desde` só se ainda estiver NULL — a PRIMEIRA data de pendência
    é a que vale, para o Plano 03 poder provar que nada some em limbo
    silencioso (nenhuma linha fica pendente sem rastro de desde quando)."""
    antes = conn.total_changes
    conn.execute(
        f"UPDATE {TABELA} SET pendente_desde = ? WHERE id = ? AND pendente_desde IS NULL",
        (data, linha_id),
    )
    conn.commit()
    return conn.total_changes - antes
