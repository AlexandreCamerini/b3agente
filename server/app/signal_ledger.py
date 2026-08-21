"""server/app/signal_ledger.py — ledger de sinais resolvidos (ADR-017, Bloco 1,
Decisão 2: "um ledger, duas leituras").

Um ledger, duas agregações — NÃO um ledger e duas implementações que podem
divergir:

  1. CUMULATIVA (`agregar_cumulativo`): o histórico exibido junto do setup,
     recalculado a cada sinal resolvido — todo o ledger, sem corte de janela.
  2. POR JANELA FECHADA (`agregar_janela`): a elegibilidade que
     `regime.ranquear()` consome, CONGELADA até a próxima virada de ano.

As duas NÃO podem virar uma agregação só: a por janela usa APENAS o ano
fechado anterior (walk-forward, sem vazamento de futuro — é o mesmo desenho
que `scripts/backtest_pesos.py` validou, Spearman +0,523, t=+7,52 em 15
janelas/15 anos). Misturar as duas leituras reintroduziria o viés que aquele
script existe para evitar: pesar pelo desempenho medido e avaliar na MESMA
amostra é circular e produz número ótimo e falso.

Este módulo não conhece `signal_replay`/`scripts/backtest_sinal.py` — recebe
o formato de linha que o replay já produz (dict com ticker/setup/lado/data/
resultado/r/dataResolucao) e só grava/agrega. Quem chama (bootstrap, hook
diário) é responsável por rodar o replay antes.
"""
from __future__ import annotations

import time
from typing import Optional

from . import db

# Herdado LITERALMENTE de scripts/backtest_pesos.py:69 (`--min-n`, default 40).
# Não é arredondamento nem estimativa: é o piso sob o qual a persistência do
# ranking foi medida (Spearman +0,523, t=+7,52). Mudar este número invalida o
# resultado empírico que justifica pesar setups por desempenho histórico.
MIN_N_JANELA = 40

# Nomenclatura no padrão de radar_daily._key ("radarDaily:<period>") — chaves
# globais no kv (user_id=None: estatística de mercado sobre tickers públicos,
# não dado de conta de usuário).
K_CUMULATIVO = "signalLedger:cumulativo"
K_JANELA = "signalLedger:janela"

# ----------------------------------------------------------------------------
# Gravação idempotente
# ----------------------------------------------------------------------------


def registrar_linhas(conn, linhas: list) -> int:
    """Grava linhas do formato de `signal_replay.replay()`. Devolve o número
    de linhas NOVAS gravadas (idempotente por UNIQUE(ticker, setup, lado,
    data_sinal) — regravar o mesmo sinal não infla `n`).

    `status` deriva de `resultado`: "sem_gatilho" quando o sinal nunca
    acionou (r e data_resolucao gravados como NULL — não houve trade, não há
    o que resolver), "resolvido" nos demais casos (alvo/stop/expirou).

    Linha sem ticker/setup/data é ignorada em silêncio — nunca grava chave
    parcial (violaria a NOT NULL de qualquer forma, mas o filtro evita gastar
    uma tentativa de INSERT por lixo de input)."""
    validas = [l for l in (linhas or []) if l.get("ticker") and l.get("setup") and l.get("data")]
    if not validas:
        return 0
    criado_em = db._now_iso()
    tuplas = []
    for l in validas:
        resultado = l.get("resultado")
        sem_gatilho = resultado == "sem_gatilho"
        status = "sem_gatilho" if sem_gatilho else "resolvido"
        r = None if sem_gatilho else l.get("r")
        data_resolucao = None if sem_gatilho else l.get("dataResolucao")
        tuplas.append((
            l["ticker"], l["setup"], l.get("lado"), l["data"],
            data_resolucao, resultado, r, status, criado_em,
        ))
    # `conn.total_changes` (não o rowcount de executemany, que não é confiável
    # entre versões do sqlite3 com OR IGNORE) — delta antes/depois é o número
    # de linhas que passaram pela UNIQUE, ou seja, as genuinamente novas.
    antes = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO signal_ledger"
        "(ticker, setup, lado, data_sinal, data_resolucao, resultado, r, status, criado_em) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        tuplas,
    )
    conn.commit()
    return conn.total_changes - antes


def apagar_tudo(conn) -> int:
    """Disaster recovery / `--reset` do bootstrap. Devolve quantas linhas saíram."""
    cur = conn.execute("DELETE FROM signal_ledger")
    conn.commit()
    return cur.rowcount


def contar(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM signal_ledger").fetchone()[0]


def data_sinal_maxima(conn, ticker: Optional[str] = None) -> Optional[str]:
    """Usado pelo cursor incremental do hook diário: até onde este ticker (ou
    o ledger inteiro, se ticker=None) já foi avançado."""
    if ticker:
        row = conn.execute(
            "SELECT MAX(data_sinal) FROM signal_ledger WHERE ticker = ?", (ticker,)
        ).fetchone()
    else:
        row = conn.execute("SELECT MAX(data_sinal) FROM signal_ledger").fetchone()
    return row[0] if row else None


# ----------------------------------------------------------------------------
# Agregações
# ----------------------------------------------------------------------------


def _stats_da_linha(n: int, soma_r, ganhos: int) -> dict:
    """Mesma precisão de `scripts/backtest_sinal.agregar` (acerto 1 casa, expR
    3 casas, somaR 1 casa) — o número exibido em produção tem que bater com o
    do harness, é o critério de reprodutibilidade do ADR-017. Feito em Python
    (não `ROUND()` do SQLite) de propósito: o SQL só soma/conta, o
    arredondamento fica na mesma função `round()` que o harness usa, sem risco
    de divergência de borda entre os dois motores de arredondamento."""
    if not n:
        return {"n": 0, "acerto": None, "expR": None, "somaR": None}
    return {
        "n": n,
        "acerto": round(100.0 * ganhos / n, 1),
        "expR": round(soma_r / n, 3),
        "somaR": round(soma_r, 1),
    }


def agregar_cumulativo(conn) -> dict:
    """UMA query agrupando por setup sobre TODO o ledger. `sem_gatilho` fica
    FORA do denominador (n só conta `status='resolvido'`) — contá-lo como
    perda infla a taxa de stop pelo mesmo viés que o ADR-015 corrige. Setup
    sem nenhum resolvido entra com n=0, expR=None, acerto=None — nunca 0.0
    fazendo as vezes de "desconhecido" (regra de casa: null, nunca 0.0)."""
    rows = conn.execute(
        "SELECT setup,"
        " SUM(CASE WHEN status='resolvido' THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN status='resolvido' THEN r ELSE 0 END),"
        " SUM(CASE WHEN status='resolvido' AND r > 0 THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN resultado='stop' THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN resultado='alvo' THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN resultado='expirou' THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN status='sem_gatilho' THEN 1 ELSE 0 END)"
        " FROM signal_ledger GROUP BY setup"
    ).fetchall()
    por_setup = {}
    for setup, n, soma_r, ganhos, stops, alvos, expirou, nao_acionados in rows:
        n = n or 0
        entry = _stats_da_linha(n, soma_r or 0.0, ganhos or 0)
        entry["stops"] = stops or 0
        entry["alvos"] = alvos or 0
        entry["expirou"] = expirou or 0
        entry["naoAcionados"] = nao_acionados or 0
        por_setup[setup] = entry
    payload = {
        "porSetup": por_setup,
        "medidoAte": data_sinal_maxima(conn),
        "calculadoEm": db._now_iso(),
    }
    db.kv_set(conn, K_CUMULATIVO, payload, user_id=None)
    return payload


def agregar_janela(conn, ano: int) -> dict:
    """Mesma forma da cumulativa, restrita a `status='resolvido' AND
    data_sinal` dentro do ano informado — é o corte walk-forward (janela
    ANTERIOR fechada, congelada). `insuficiente` nunca vira `elegivel=False`:
    ausência de evidência não é prova de mau desempenho; a célula cai no
    comportamento atual (sem peso histórico) até acumular amostra (ADR-017,
    "Dois pisos de amostra")."""
    ini, fim = f"{ano:04d}-01-01", f"{ano:04d}-12-31"
    rows = conn.execute(
        "SELECT setup, COUNT(*), SUM(r) FROM signal_ledger"
        " WHERE status = 'resolvido' AND data_sinal BETWEEN ? AND ?"
        " GROUP BY setup",
        (ini, fim),
    ).fetchall()
    por_setup = {}
    for setup, n, soma_r in rows:
        n = n or 0
        exp_r = round((soma_r or 0.0) / n, 3) if n else None
        insuficiente = n < MIN_N_JANELA
        elegivel = None if insuficiente else (exp_r is not None and exp_r > 0)
        por_setup[setup] = {
            "n": n, "expR": exp_r, "elegivel": elegivel, "insuficiente": insuficiente,
        }
    payload = {
        "janelaRef": str(ano),
        "minN": MIN_N_JANELA,
        "calculadoEm": db._now_iso(),
        "porSetup": por_setup,
    }
    db.kv_set(conn, K_JANELA, payload, user_id=None)
    return payload
