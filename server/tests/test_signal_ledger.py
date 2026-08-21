"""server/tests/test_signal_ledger.py — ledger de sinais resolvidos (ADR-017,
Bloco 1, Decisão 2: "um ledger, duas leituras").

Task 1: schema da tabela `signal_ledger` no banco PRINCIPAL — idempotência de
`init_db`, UNIQUE que impede amostra inflada, índices de varredura.
Task 2/3 acrescentam os testes de `signal_ledger.py` (gravação, agregações,
provedor com cache).
"""
import sqlite3

from app import db, signal_ledger


def _conn(tmp_path, nome="t.db"):
    return db.connect(str(tmp_path / nome))


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


# ===== Task 2 — gravação idempotente e as duas agregações SQL ===============

def test_registrar_linhas_idempotente(tmp_path):
    conn = _conn(tmp_path)
    linha = {"ticker": "PETR4", "setup": "IFR2 (alta)", "lado": "alta",
              "data": "2025-01-10", "resultado": "alvo", "r": 2.0,
              "dataResolucao": "2025-01-15"}
    assert signal_ledger.registrar_linhas(conn, [linha]) == 1
    assert signal_ledger.registrar_linhas(conn, [linha]) == 0
    assert signal_ledger.contar(conn) == 1


def test_registrar_linhas_sem_gatilho_grava_status_e_null(tmp_path):
    conn = _conn(tmp_path)
    linha = {"ticker": "VALE3", "setup": "Rompimento", "lado": "alta",
              "data": "2025-02-01", "resultado": "sem_gatilho", "r": None,
              "dataResolucao": None}
    signal_ledger.registrar_linhas(conn, [linha])
    row = conn.execute(
        "SELECT status, r, data_resolucao FROM signal_ledger WHERE ticker='VALE3'"
    ).fetchone()
    assert row == ("sem_gatilho", None, None)


def test_registrar_linhas_resolvido_grava_status_e_r(tmp_path):
    conn = _conn(tmp_path)
    linha = {"ticker": "ITUB4", "setup": "Suporte", "lado": "baixa",
              "data": "2025-03-01", "resultado": "stop", "r": -1.0,
              "dataResolucao": "2025-03-05"}
    signal_ledger.registrar_linhas(conn, [linha])
    row = conn.execute(
        "SELECT status, r, data_resolucao FROM signal_ledger WHERE ticker='ITUB4'"
    ).fetchone()
    assert row == ("resolvido", -1.0, "2025-03-05")


def test_registrar_linhas_lista_vazia_nao_abre_transacao(tmp_path):
    conn = _conn(tmp_path)
    assert signal_ledger.registrar_linhas(conn, []) == 0
    assert signal_ledger.contar(conn) == 0


def test_registrar_linhas_ignora_linha_com_chave_parcial(tmp_path):
    conn = _conn(tmp_path)
    linha = {"ticker": None, "setup": "S1", "data": "2025-01-01", "resultado": "alvo", "r": 1.0}
    assert signal_ledger.registrar_linhas(conn, [linha]) == 0
    assert signal_ledger.contar(conn) == 0


def test_agregar_cumulativo_estatisticas(tmp_path):
    conn = _conn(tmp_path)
    linhas = [
        {"ticker": "A", "setup": "IFR2 (alta)", "lado": "alta", "data": "2025-01-01",
         "resultado": "alvo", "r": 2.0, "dataResolucao": "2025-01-05"},
        {"ticker": "B", "setup": "IFR2 (alta)", "lado": "alta", "data": "2025-01-02",
         "resultado": "stop", "r": -1.0, "dataResolucao": "2025-01-06"},
        {"ticker": "C", "setup": "IFR2 (alta)", "lado": "alta", "data": "2025-01-03",
         "resultado": "expirou", "r": 0.5, "dataResolucao": "2025-01-10"},
        {"ticker": "D", "setup": "IFR2 (alta)", "lado": "alta", "data": "2025-01-04",
         "resultado": "sem_gatilho", "r": None, "dataResolucao": None},
    ]
    signal_ledger.registrar_linhas(conn, linhas)
    resultado = signal_ledger.agregar_cumulativo(conn)
    setup = resultado["porSetup"]["IFR2 (alta)"]
    assert setup["n"] == 3
    assert setup["somaR"] == 1.5
    assert setup["expR"] == 0.5
    assert setup["acerto"] == 66.7
    assert setup["stops"] == 1
    assert setup["alvos"] == 1
    assert setup["expirou"] == 1
    assert setup["naoAcionados"] == 1
    assert resultado["medidoAte"] == "2025-01-04"
    assert "calculadoEm" in resultado


def test_agregar_cumulativo_grava_no_kv_global(tmp_path):
    conn = _conn(tmp_path)
    signal_ledger.registrar_linhas(conn, [
        {"ticker": "A", "setup": "S1", "lado": "alta", "data": "2025-01-01",
         "resultado": "alvo", "r": 1.0, "dataResolucao": "2025-01-05"},
    ])
    signal_ledger.agregar_cumulativo(conn)
    salvo = db.kv_get(conn, signal_ledger.K_CUMULATIVO, user_id=None)
    assert salvo is not None
    assert "S1" in salvo["porSetup"]


def test_agregar_janela_filtra_por_ano_e_status(tmp_path):
    conn = _conn(tmp_path)
    linhas = [
        {"ticker": "A", "setup": "S1", "lado": "alta", "data": "2025-06-01",
         "resultado": "alvo", "r": 1.0, "dataResolucao": "2025-06-05"},
        {"ticker": "B", "setup": "S1", "lado": "alta", "data": "2024-06-01",
         "resultado": "alvo", "r": 1.0, "dataResolucao": "2024-06-05"},  # ano errado
        {"ticker": "C", "setup": "S1", "lado": "alta", "data": "2025-07-01",
         "resultado": "sem_gatilho", "r": None, "dataResolucao": None},  # status errado
    ]
    signal_ledger.registrar_linhas(conn, linhas)
    resultado = signal_ledger.agregar_janela(conn, 2025)
    assert resultado["porSetup"]["S1"]["n"] == 1


def _linhas_setup(setup: str, n: int, r: float) -> list:
    out = []
    for i in range(n):
        mes = 1 + (i // 28)
        dia = 1 + (i % 28)
        out.append({
            "ticker": "X", "setup": setup, "lado": "alta",
            "data": f"2025-{mes:02d}-{dia:02d}", "resultado": "alvo" if r > 0 else "stop",
            "r": r, "dataResolucao": f"2025-{mes:02d}-{dia:02d}",
        })
    return out


def test_agregar_janela_piso_de_amostra_elegivel_positivo(tmp_path):
    conn = _conn(tmp_path)
    signal_ledger.registrar_linhas(conn, _linhas_setup("S_POS", 40, 1.0))
    resultado = signal_ledger.agregar_janela(conn, 2025)
    setup = resultado["porSetup"]["S_POS"]
    assert setup["n"] == 40
    assert setup["elegivel"] is True
    assert setup["insuficiente"] is False


def test_agregar_janela_piso_de_amostra_nao_elegivel(tmp_path):
    conn = _conn(tmp_path)
    signal_ledger.registrar_linhas(conn, _linhas_setup("S_NEG", 40, -1.0))
    resultado = signal_ledger.agregar_janela(conn, 2025)
    setup = resultado["porSetup"]["S_NEG"]
    assert setup["n"] == 40
    assert setup["elegivel"] is False
    assert setup["insuficiente"] is False


def test_agregar_janela_amostra_insuficiente_nunca_vira_elegivel_false(tmp_path):
    conn = _conn(tmp_path)
    signal_ledger.registrar_linhas(conn, _linhas_setup("S_INSUF", 39, 1.0))
    resultado = signal_ledger.agregar_janela(conn, 2025)
    setup = resultado["porSetup"]["S_INSUF"]
    assert setup["n"] == 39
    assert setup["insuficiente"] is True
    assert setup["elegivel"] is None


def test_agregar_janela_grava_no_kv_com_janela_ref_e_min_n(tmp_path):
    conn = _conn(tmp_path)
    signal_ledger.registrar_linhas(conn, _linhas_setup("S1", 40, 1.0))
    signal_ledger.agregar_janela(conn, 2025)
    salvo = db.kv_get(conn, signal_ledger.K_JANELA, user_id=None)
    assert salvo is not None
    assert salvo["janelaRef"] == "2025"
    assert salvo["minN"] == 40
    assert "calculadoEm" in salvo


# ===== Task 3 — provedor de histórico por setup com cache em processo =======

def _preparar_ledger_completo(conn):
    """Um setup presente nas DUAS agregações (S1), um só na cumulativa (S_CUM —
    sinal de 2024, fora da janela agregada de 2025), um só na janela (S_JAN —
    registrado e agregado DEPOIS de `agregar_cumulativo`, nunca entra em
    K_CUMULATIVO) — cobre os três ramos de `historico_snapshot`."""
    signal_ledger.registrar_linhas(conn, _linhas_setup("S1", 40, 1.0))
    signal_ledger.registrar_linhas(conn, [
        {"ticker": "Z", "setup": "S_CUM", "lado": "alta", "data": "2024-01-01",
         "resultado": "alvo", "r": 1.0, "dataResolucao": "2024-01-05"},
    ])
    signal_ledger.agregar_cumulativo(conn)
    signal_ledger.registrar_linhas(conn, _linhas_setup("S_JAN", 40, 1.0))
    signal_ledger.agregar_janela(conn, 2025)


def test_historico_snapshot_funde_as_duas_agregacoes(tmp_path):
    conn = _conn(tmp_path)
    _preparar_ledger_completo(conn)
    signal_ledger.reset_cache()
    snap = signal_ledger.historico_snapshot(conn)
    assert set(("expR", "n", "medidoAte", "elegivel", "insuficiente",
                "expRJanela", "nJanela", "janelaRef", "calculadoEm")) <= set(snap["S1"])


def test_historico_snapshot_setup_so_na_cumulativa(tmp_path):
    conn = _conn(tmp_path)
    _preparar_ledger_completo(conn)
    signal_ledger.reset_cache()
    snap = signal_ledger.historico_snapshot(conn)
    s_cum = snap["S_CUM"]
    assert s_cum["elegivel"] is None
    assert s_cum["insuficiente"] is True
    assert s_cum["nJanela"] == 0


def test_historico_snapshot_setup_so_na_janela(tmp_path):
    conn = _conn(tmp_path)
    _preparar_ledger_completo(conn)
    signal_ledger.reset_cache()
    snap = signal_ledger.historico_snapshot(conn)
    s_jan = snap["S_JAN"]
    assert s_jan["expR"] is None
    assert s_jan["n"] == 0


def test_historico_snapshot_kv_vazio_devolve_dict_vazio(tmp_path):
    conn = _conn(tmp_path)
    signal_ledger.reset_cache()
    assert signal_ledger.historico_snapshot(conn) == {}


def test_historico_snapshot_usa_cache_dentro_do_ttl(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _preparar_ledger_completo(conn)
    signal_ledger.reset_cache()
    chamadas = {"n": 0}
    original = db.kv_get

    def contado(*a, **kw):
        chamadas["n"] += 1
        return original(*a, **kw)

    monkeypatch.setattr(db, "kv_get", contado)
    signal_ledger.historico_snapshot(conn, now=1000.0)
    apos_primeira = chamadas["n"]
    assert apos_primeira > 0
    signal_ledger.historico_snapshot(conn, now=1000.0 + 10.0)
    assert chamadas["n"] == apos_primeira  # segunda chamada veio do cache


def test_historico_snapshot_rele_apos_ttl_expirar(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _preparar_ledger_completo(conn)
    signal_ledger.reset_cache()
    chamadas = {"n": 0}
    original = db.kv_get

    def contado(*a, **kw):
        chamadas["n"] += 1
        return original(*a, **kw)

    monkeypatch.setattr(db, "kv_get", contado)
    signal_ledger.historico_snapshot(conn, ttl_s=300, now=1000.0)
    apos_primeira = chamadas["n"]
    signal_ledger.historico_snapshot(conn, ttl_s=300, now=1000.0 + 301.0)
    assert chamadas["n"] > apos_primeira


def test_reset_cache_forca_releitura(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _preparar_ledger_completo(conn)
    signal_ledger.reset_cache()
    chamadas = {"n": 0}
    original = db.kv_get

    def contado(*a, **kw):
        chamadas["n"] += 1
        return original(*a, **kw)

    monkeypatch.setattr(db, "kv_get", contado)
    signal_ledger.historico_snapshot(conn, now=1000.0)
    apos_primeira = chamadas["n"]
    signal_ledger.reset_cache()
    signal_ledger.historico_snapshot(conn, now=1000.0 + 1.0)
    assert chamadas["n"] > apos_primeira


def test_historico_snapshot_excecao_de_banco_nao_propaga_sem_cache(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    signal_ledger.reset_cache()

    def explode(*a, **kw):
        raise sqlite3.OperationalError("banco fora do ar")

    monkeypatch.setattr(db, "kv_get", explode)
    assert signal_ledger.historico_snapshot(conn) == {}


def test_historico_snapshot_excecao_de_banco_devolve_cache_anterior(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _preparar_ledger_completo(conn)
    signal_ledger.reset_cache()
    primeiro = signal_ledger.historico_snapshot(conn, now=1000.0)
    assert primeiro != {}

    def explode(*a, **kw):
        raise sqlite3.OperationalError("banco fora do ar")

    monkeypatch.setattr(db, "kv_get", explode)
    # TTL expirado força releitura, que agora explode — deve cair no cache anterior.
    segundo = signal_ledger.historico_snapshot(conn, ttl_s=300, now=1000.0 + 301.0)
    assert segundo == primeiro
