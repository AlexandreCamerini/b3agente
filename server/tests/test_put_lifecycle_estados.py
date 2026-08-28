"""server/tests/test_put_lifecycle_estados.py — guardião das transições de
estado de `put_suggestions` (Fase 11, Plano 01, Task 1).

Prova de comportamento: `transicionar` é a ÚNICA porta de escrita de estado
e recusa 100% dos destinos não declarados em `TRANSICOES` (incluindo
estados inexistentes e saída de terminal); a proveniência gravada pela
Fase 10 (premio/fonte/prov_*/iv/estilo_exercicio) é comprovadamente
imutável por essa porta; a migração de schema é aditiva e idempotente sobre
um banco com o schema ANTIGO.
"""
import sqlite3

import pytest

from app import db, put_suggestions


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


def _registrar(conn, **overrides):
    put_suggestions.registrar(conn, _linha_valida(**overrides))
    return put_suggestions.listar(conn)[0]["id"]


def test_transicao_armada_para_executada_simulada_ok(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    assert put_suggestions.transicionar(conn, linha_id, "executada_simulada") == 1
    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "executada_simulada"
    assert saida["estadoEm"] is not None


def test_transicao_nao_declarada_e_recusada(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    assert put_suggestions.transicionar(conn, linha_id, "fechada") == 0
    assert put_suggestions.transicionar(conn, linha_id, "monitorada") == 0
    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "armada"


def test_transicao_de_fechada_para_armada_e_recusada(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    assert put_suggestions.transicionar(conn, linha_id, "executada_simulada") == 1
    assert put_suggestions.transicionar(conn, linha_id, "fechada") == 1
    assert put_suggestions.transicionar(conn, linha_id, "armada") == 0
    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "fechada"


def test_transicao_para_estado_inexistente_e_recusada(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    assert put_suggestions.transicionar(conn, linha_id, "qualquer_coisa") == 0
    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "armada"


def test_transicao_sobre_id_inexistente_devolve_zero_sem_levantar(tmp_path):
    conn = _conn(tmp_path)
    assert put_suggestions.transicionar(conn, 999999, "executada_simulada") == 0


def test_transicao_de_terminal_expirada_sem_uso_e_recusada(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    assert put_suggestions.transicionar(conn, linha_id, "expirada_sem_uso") == 1
    assert put_suggestions.transicionar(conn, linha_id, "executada_simulada") == 0
    assert put_suggestions.transicionar(conn, linha_id, "monitorada") == 0
    assert put_suggestions.transicionar(conn, linha_id, "fechada") == 0
    saida = put_suggestions.listar(conn)[0]
    assert saida["estado"] == "expirada_sem_uso"


def test_transicao_de_terminal_fechada_e_recusada(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada")
    put_suggestions.transicionar(conn, linha_id, "fechada")
    assert put_suggestions.transicionar(conn, linha_id, "monitorada") == 0
    assert put_suggestions.transicionar(conn, linha_id, "executada_simulada") == 0


def test_monitorada_para_monitorada_e_permitida_remarcacao_diaria(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada")
    put_suggestions.transicionar(conn, linha_id, "monitorada",
                                  campos={"spot_marcacao": 30.0, "marcada_em": "2026-09-01"})
    assert put_suggestions.transicionar(
        conn, linha_id, "monitorada",
        campos={"spot_marcacao": 29.5, "marcada_em": "2026-09-02"},
    ) == 1
    saida = put_suggestions.listar(conn)[0]
    assert saida["spotMarcacao"] == 29.5
    assert saida["marcadaEm"] == "2026-09-02"


def test_campos_fora_de_colunas_ciclo_sao_descartados_silenciosamente(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    assert put_suggestions.transicionar(
        conn, linha_id, "executada_simulada",
        campos={"premio": 99, "fonte": "falsa", "prov_sha256": "x", "iv": 9},
    ) == 1
    saida = put_suggestions.listar(conn)[0]
    assert saida["premio"] == 1.15
    assert saida["fonte"] == "mydata"
    assert saida["provSha256"] == "abc123"
    assert saida["iv"] == 0.32


def test_motivo_fechamento_fora_do_vocabulario_ad_r005_e_descartado(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada")
    assert put_suggestions.transicionar(
        conn, linha_id, "fechada",
        campos={"motivo_fechamento": "inventado", "preco_fechamento": 2.0},
    ) == 1
    saida = put_suggestions.listar(conn)[0]
    assert saida["motivoFechamento"] is None
    assert saida["precoFechamento"] == 2.0


def test_motivo_fechamento_vencimento_e_aceito(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    put_suggestions.transicionar(conn, linha_id, "executada_simulada")
    put_suggestions.transicionar(
        conn, linha_id, "fechada",
        campos={"motivo_fechamento": "vencimento", "preco_fechamento": 0.0},
    )
    saida = put_suggestions.listar(conn)[0]
    assert saida["motivoFechamento"] == "vencimento"


def test_registrar_pendencia_grava_so_se_null(tmp_path):
    conn = _conn(tmp_path)
    linha_id = _registrar(conn)
    assert put_suggestions.registrar_pendencia(conn, linha_id, "2026-09-01") == 1
    assert put_suggestions.registrar_pendencia(conn, linha_id, "2026-09-05") == 0
    saida = put_suggestions.listar(conn)[0]
    assert saida["pendenteDesde"] == "2026-09-01"


def test_listar_abertas_exclui_terminais_ordem_crescente(tmp_path):
    conn = _conn(tmp_path)
    id1 = _registrar(conn, user_id="u1", ticker="PETR4")
    id2 = _registrar(conn, user_id="u2", ticker="VALE3")
    id3 = _registrar(conn, user_id="u3", ticker="ITUB4")
    put_suggestions.transicionar(conn, id2, "expirada_sem_uso")
    abertas = put_suggestions.listar_abertas(conn)
    ids = [row["id"] for row in abertas]
    assert ids == sorted([id1, id3])
    assert id2 not in ids


def test_listar_devolve_11_chaves_novas_none_em_linha_recem_registrada(tmp_path):
    conn = _conn(tmp_path)
    _registrar(conn)
    saida = put_suggestions.listar(conn)[0]
    chaves_novas = (
        "estadoEm", "executadaEm", "precoEntrada", "spotMarcacao",
        "intrinsecoMarcacao", "marcadaEm", "fechadaEm", "precoFechamento",
        "motivoFechamento", "pnlPorAcao", "pendenteDesde",
    )
    assert len(chaves_novas) == 11
    for chave in chaves_novas:
        assert chave in saida
        assert saida[chave] is None


def test_migracao_idempotente_sobre_schema_antigo_preserva_linha(tmp_path):
    caminho = str(tmp_path / "antigo.db")
    conn_antiga = sqlite3.connect(caminho)
    conn_antiga.execute(
        "CREATE TABLE put_suggestions ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " user_id TEXT NOT NULL,"
        " ticker TEXT NOT NULL,"
        " data_pregao TEXT NOT NULL,"
        " setup TEXT NOT NULL,"
        " lado TEXT,"
        " contrato TEXT NOT NULL,"
        " option_type TEXT NOT NULL,"
        " strike REAL NOT NULL,"
        " vencimento TEXT NOT NULL,"
        " estilo_exercicio TEXT NOT NULL,"
        " iv REAL NOT NULL,"
        " delta REAL,"
        " premio REAL,"
        " volume INTEGER,"
        " spot REAL,"
        " estado TEXT NOT NULL DEFAULT 'armada',"
        " fonte TEXT NOT NULL,"
        " as_of TEXT,"
        " prov_sha256 TEXT,"
        " prov_dt_captura TEXT,"
        " prov_captura TEXT,"
        " criado_em TEXT NOT NULL,"
        " CHECK (option_type = 'put'),"
        " UNIQUE(user_id, ticker, data_pregao)"
        ")"
    )
    conn_antiga.execute(
        "INSERT INTO put_suggestions (user_id, ticker, data_pregao, setup, lado, "
        "contrato, option_type, strike, vencimento, estilo_exercicio, iv, "
        "estado, fonte, criado_em) VALUES "
        "('u1','PETR4','2026-08-28','IFR2 (baixa)','baixa','PETRR100','put',"
        "34.5,'2026-09-19','americano',0.32,'armada','mydata','2026-08-28T00:00:00Z')"
    )
    conn_antiga.commit()
    conn_antiga.close()

    conn = db.connect(caminho)
    db.init_db(conn)
    db.init_db(conn)
    db.init_db(conn)

    colunas = {row[1] for row in conn.execute("PRAGMA table_info(put_suggestions)").fetchall()}
    novas = {
        "estado_em", "executada_em", "preco_entrada", "spot_marcacao",
        "intrinseco_marcacao", "marcada_em", "fechada_em", "preco_fechamento",
        "motivo_fechamento", "pnl_por_acao", "pendente_desde",
    }
    assert novas <= colunas
    assert put_suggestions.contar(conn) == 1
    saida = put_suggestions.listar(conn)[0]
    assert saida["ticker"] == "PETR4"
    assert saida["estadoEm"] is None
