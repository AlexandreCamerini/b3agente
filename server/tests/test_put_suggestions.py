"""server/tests/test_put_suggestions.py — persistência da sugestão de put de
proteção (Fase 10, Plano 01, Task 1).

Prova de comportamento, não de existência: idempotência por
(user_id, ticker, data_pregao), NOT NULL de proveniência mínima
(estilo_exercicio/iv), CHECK estrutural de long-only (option_type='put'), e
isolamento total do `signal_ledger` (ADR-017) — a tabela nova não pode ser
vista pela agregação `GROUP BY setup` que alimenta `regime.ranquear()`.
"""
import sqlite3

import pytest

from app import db, put_suggestions, signal_ledger


def _conn(tmp_path, nome="t.db"):
    return db.connect(str(tmp_path / nome))


def _linha_valida(**overrides):
    linha = {
        "user_id": "u1",
        "ticker": "PETR4",
        "data_pregao": "2026-08-28",
        "setup": "IFR2 (baixa)",
        "lado": "baixa",
        "contrato": "PETRR100",
        "strike": 34.5,
        "vencimento": "2026-09-19",
        "estilo_exercicio": "americano",
        "iv": 0.32,
        "delta": -0.42,
        "premio": 1.15,
        "volume": 250,
        "spot": 36.2,
        "fonte": "mydata",
        "as_of": "2026-08-28",
        "prov_sha256": "abc123",
        "prov_dt_captura": "2026-08-28T20:05:00Z",
        "prov_captura": "COTAHIST_D28082026.TXT",
    }
    linha.update(overrides)
    return linha


def test_registrar_grava_linha_completa_com_proveniencia(tmp_path):
    conn = _conn(tmp_path)
    linha = _linha_valida()
    assert put_suggestions.registrar(conn, linha) == 1
    listadas = put_suggestions.listar(conn)
    assert len(listadas) == 1
    saida = listadas[0]
    assert saida["fonte"] == "mydata"
    assert saida["asOf"] == "2026-08-28"
    assert saida["provSha256"] == "abc123"
    assert saida["provDtCaptura"] == "2026-08-28T20:05:00Z"


def test_regravar_mesma_chave_nao_duplica(tmp_path):
    conn = _conn(tmp_path)
    linha = _linha_valida()
    assert put_suggestions.registrar(conn, linha) == 1
    assert put_suggestions.registrar(conn, linha) == 0
    assert put_suggestions.contar(conn) == 1


def test_usuarios_diferentes_mesmo_ticker_mesmo_dia_coexistem(tmp_path):
    conn = _conn(tmp_path)
    assert put_suggestions.registrar(conn, _linha_valida(user_id="u1")) == 1
    assert put_suggestions.registrar(conn, _linha_valida(user_id="u2")) == 1
    assert put_suggestions.contar(conn) == 2


def test_sem_estilo_exercicio_nao_grava(tmp_path):
    conn = _conn(tmp_path)
    assert put_suggestions.registrar(conn, _linha_valida(estilo_exercicio=None)) == 0
    assert put_suggestions.contar(conn) == 0


def test_sem_iv_nao_grava(tmp_path):
    conn = _conn(tmp_path)
    assert put_suggestions.registrar(conn, _linha_valida(iv=None)) == 0
    assert put_suggestions.contar(conn) == 0


def test_option_type_call_e_rejeitado_pelo_check(tmp_path):
    conn = _conn(tmp_path)
    linha = _linha_valida()
    linha["option_type"] = "call"
    # `registrar` força option_type="put" e nunca lê o campo do input — para
    # provar o CHECK estruturalmente, insere direto via SQL bruto (a mesma
    # forma que uma futura regressão de `registrar` produziria se parasse de
    # forçar o campo).
    cols = ", ".join(c for c, _ in put_suggestions._COLUNAS)
    placeholders = ", ".join("?" for _ in put_suggestions._COLUNAS)
    valores = []
    linha_sql = dict(linha)
    linha_sql["option_type"] = "call"
    linha_sql["estado"] = put_suggestions.ESTADO_INICIAL
    linha_sql["criado_em"] = db._now_iso()
    for coluna, _ in put_suggestions._COLUNAS:
        valores.append(linha_sql.get(coluna))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            f"INSERT INTO {put_suggestions.TABELA}({cols}) VALUES({placeholders})",
            valores,
        )
    assert put_suggestions.contar(conn) == 0


def test_estado_inicial_e_armada(tmp_path):
    conn = _conn(tmp_path)
    put_suggestions.registrar(conn, _linha_valida())
    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "armada" == put_suggestions.ESTADO_INICIAL


def test_ticker_bruto_e_normalizado_na_escrita(tmp_path):
    conn = _conn(tmp_path)
    put_suggestions.registrar(conn, _linha_valida(ticker="petr4.sa"))
    saida = put_suggestions.listar(conn)[0]
    assert saida["ticker"] == "PETR4"


def test_nao_toca_signal_ledger(tmp_path):
    conn = _conn(tmp_path)
    put_suggestions.registrar(conn, _linha_valida(user_id="u1"))
    put_suggestions.registrar(conn, _linha_valida(user_id="u2"))
    assert signal_ledger.contar(conn) == 0
    assert signal_ledger.agregar_cumulativo(conn)["porSetup"] == {}
