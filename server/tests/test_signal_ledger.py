"""server/tests/test_signal_ledger.py — ledger de sinais resolvidos (ADR-017,
Bloco 1, Decisão 2: "um ledger, duas leituras").

Task 1: schema da tabela `signal_ledger` no banco PRINCIPAL — idempotência de
`init_db`, UNIQUE que impede amostra inflada, índices de varredura.
Task 2/3 acrescentam os testes de `signal_ledger.py` (gravação, agregações,
provedor com cache).
"""
from app import db


# ===== Task 1 — schema =======================================================

def test_init_db_cria_signal_ledger_sem_erro(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='signal_ledger'"
    ).fetchone()
    assert row is not None


def test_init_db_e_idempotente_para_signal_ledger(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    db.init_db(conn)  # segunda chamada não pode levantar
    db.init_db(conn)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='signal_ledger'"
    ).fetchone()
    assert row is not None


def test_unique_ticker_setup_lado_data_sinal_impede_duplicata(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    tupla = ("PETR4", "IFR2 (alta)", "alta", "2025-01-10", None, "sem_gatilho",
             None, "sem_gatilho", db._now_iso())
    cur = conn.execute(
        "INSERT OR IGNORE INTO signal_ledger"
        "(ticker, setup, lado, data_sinal, data_resolucao, resultado, r, status, criado_em) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        tupla,
    )
    assert cur.rowcount == 1
    cur2 = conn.execute(
        "INSERT OR IGNORE INTO signal_ledger"
        "(ticker, setup, lado, data_sinal, data_resolucao, resultado, r, status, criado_em) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        tupla,
    )
    assert cur2.rowcount == 0
    n = conn.execute("SELECT COUNT(*) FROM signal_ledger").fetchone()[0]
    assert n == 1


def test_indices_do_signal_ledger_existem(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    nomes = {row[1] for row in conn.execute("PRAGMA index_list('signal_ledger')").fetchall()}
    assert "idx_signal_ledger_setup" in nomes
    assert "idx_signal_ledger_ticker" in nomes
