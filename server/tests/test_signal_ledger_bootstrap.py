"""server/tests/test_signal_ledger_bootstrap.py — bootstrap único do ledger de
sinais resolvidos (ADR-017, Bloco 1, Plano 03).

Nenhum teste toca a rede: `carregar_candles`/`yahoo.get_history` são sempre
monkeypatchados. `signal_replay.replay` também é monkeypatchado nos testes de
orquestração para isolar `executar`/`bootstrap_ticker` da mecânica de
detecção de setup (já coberta em `test_signal_replay.py`).
"""
import asyncio

from app import db, signal_ledger, signal_ledger_bootstrap as bootstrap


def _conn(tmp_path, nome="t.db"):
    return db.connect(str(tmp_path / nome))


def _linha(ticker="PETR4", data="2025-01-10", resultado="alvo", r=1.5):
    return {
        "ticker": ticker, "data": data, "t": 10,
        "setup": "IFR2 (alta)", "lado": "alta", "confluencia": 100,
        "tipo": "a mercado", "entrada": 10.0, "stop": 9.5,
        "alvo1": 11.0, "alvo2": 12.0, "rr2": 4.0, "regime": "tendencia_alta",
        "resultado": resultado, "r": r, "dataResolucao": "2025-01-20",
    }


# ===== bootstrap_ticker: idempotência ======================================


def test_bootstrap_ticker_grava_linhas_e_devolve_len_e_novas(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    linhas = [_linha("PETR4", "2025-01-10"), _linha("PETR4", "2025-01-11")]
    monkeypatch.setattr(bootstrap.signal_replay, "replay", lambda *a, **k: linhas)

    n, novas = bootstrap.bootstrap_ticker(conn, "PETR4", candles=[], dias=252)

    assert n == 2
    assert novas == 2
    assert signal_ledger.contar(conn) == 2


def test_bootstrap_ticker_rodado_duas_vezes_nao_duplica(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    linhas = [_linha("PETR4", "2025-01-10"), _linha("PETR4", "2025-01-11")]
    monkeypatch.setattr(bootstrap.signal_replay, "replay", lambda *a, **k: linhas)

    n1, novas1 = bootstrap.bootstrap_ticker(conn, "PETR4", candles=[], dias=252)
    n2, novas2 = bootstrap.bootstrap_ticker(conn, "PETR4", candles=[], dias=252)

    assert n1 == 2 and novas1 == 2
    assert n2 == 2 and novas2 == 0  # mesmos candles -> nada novo, UNIQUE segura
    assert signal_ledger.contar(conn) == 2


def test_total_do_ledger_igual_soma_das_linhas_por_ticker(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    por_ticker = {
        "PETR4": [_linha("PETR4", "2025-01-10"), _linha("PETR4", "2025-01-11")],
        "VALE3": [_linha("VALE3", "2025-01-12")],
    }
    monkeypatch.setattr(bootstrap.signal_replay, "replay",
                         lambda ticker, cs, dias: por_ticker[ticker])

    total_esperado = 0
    for tk, linhas in por_ticker.items():
        n, _ = bootstrap.bootstrap_ticker(conn, tk, candles=[], dias=252)
        total_esperado += n

    assert signal_ledger.contar(conn) == total_esperado == 3


# ===== executar: erro de um ticker não derruba os demais ===================


def test_executar_ticker_com_fetch_quebrado_entra_em_erros(tmp_path, monkeypatch):
    conn = _conn(tmp_path)

    async def carregar_fake(ticker, rng):
        if ticker == "QUEBRADO3":
            raise RuntimeError("Yahoo: sem historico para QUEBRADO3")
        return [{"date": "2025-01-01"}]

    monkeypatch.setattr(bootstrap, "carregar_candles", carregar_fake)
    monkeypatch.setattr(bootstrap.signal_replay, "replay",
                         lambda ticker, cs, dias: [_linha(ticker, "2025-01-10")])

    resumo = asyncio.run(bootstrap.executar(
        conn, ["PETR4", "QUEBRADO3", "VALE3"], anos=1.0, rng="15y", concorrencia=2,
    ))

    assert resumo["tickers"] == 3
    assert len(resumo["erros"]) == 1
    assert resumo["erros"][0]["ticker"] == "QUEBRADO3"
    assert resumo["linhas"] == 2  # PETR4 + VALE3, QUEBRADO3 não contribuiu
    assert resumo["novas"] == 2
    assert signal_ledger.contar(conn) == 2


def test_executar_dry_run_nao_grava_nada(tmp_path, monkeypatch):
    conn = _conn(tmp_path)

    async def carregar_fake(ticker, rng):
        return [{"date": "2025-01-01"}]

    monkeypatch.setattr(bootstrap, "carregar_candles", carregar_fake)
    monkeypatch.setattr(bootstrap.signal_replay, "replay",
                         lambda ticker, cs, dias: [_linha(ticker, "2025-01-10")])

    resumo = asyncio.run(bootstrap.executar(
        conn, ["PETR4", "VALE3"], anos=1.0, rng="15y", concorrencia=2, dry_run=True,
    ))

    assert resumo["linhas"] == 2
    assert resumo["novas"] == 0
    assert signal_ledger.contar(conn) == 0  # dry-run: nada gravado


# ===== main(): --reset e agregações finais ==================================


def test_main_reset_apaga_ledger_antes_da_carga(tmp_path, monkeypatch):
    db_path = str(tmp_path / "t.db")
    conn = db.connect(db_path)
    signal_ledger.registrar_linhas(conn, [_linha("PETR4", "2024-01-10")])
    assert signal_ledger.contar(conn) == 1

    async def carregar_fake(ticker, rng):
        return [{"date": "2025-01-01"}]

    monkeypatch.setattr(bootstrap, "carregar_candles", carregar_fake)
    monkeypatch.setattr(bootstrap.signal_replay, "replay",
                         lambda ticker, cs, dias: [_linha(ticker, "2025-06-10")])
    monkeypatch.setattr(bootstrap.db, "connect", lambda path=None: conn)
    monkeypatch.setattr(
        bootstrap.sys, "argv",
        ["signal_ledger_bootstrap", "--reset", "--tickers", "PETR4",
         "--anos", "1", "--db", db_path],
    )

    bootstrap.main()

    # --reset apagou a linha antiga (2024-01-10); só a nova (2025-06-10) resta.
    assert signal_ledger.contar(conn) == 1
    row = conn.execute("SELECT data_sinal FROM signal_ledger").fetchone()
    assert row[0] == "2025-06-10"


def test_main_grava_agregacoes_ao_final(tmp_path, monkeypatch):
    db_path = str(tmp_path / "t.db")
    conn = db.connect(db_path)

    async def carregar_fake(ticker, rng):
        return [{"date": "2025-01-01"}]

    monkeypatch.setattr(bootstrap, "carregar_candles", carregar_fake)
    monkeypatch.setattr(bootstrap.signal_replay, "replay",
                         lambda ticker, cs, dias: [_linha(ticker, "2025-06-10")])
    monkeypatch.setattr(bootstrap.db, "connect", lambda path=None: conn)
    monkeypatch.setattr(
        bootstrap.sys, "argv",
        ["signal_ledger_bootstrap", "--tickers", "PETR4", "--anos", "1", "--db", db_path],
    )

    bootstrap.main()

    assert db.kv_get(conn, signal_ledger.K_CUMULATIVO, user_id=None) is not None
    assert db.kv_get(conn, signal_ledger.K_JANELA, user_id=None) is not None


def test_main_dry_run_nao_grava_agregacoes(tmp_path, monkeypatch):
    db_path = str(tmp_path / "t.db")
    conn = db.connect(db_path)

    async def carregar_fake(ticker, rng):
        return [{"date": "2025-01-01"}]

    monkeypatch.setattr(bootstrap, "carregar_candles", carregar_fake)
    monkeypatch.setattr(bootstrap.signal_replay, "replay",
                         lambda ticker, cs, dias: [_linha(ticker, "2025-06-10")])
    monkeypatch.setattr(bootstrap.db, "connect", lambda path=None: conn)
    monkeypatch.setattr(
        bootstrap.sys, "argv",
        ["signal_ledger_bootstrap", "--dry-run", "--tickers", "PETR4",
         "--anos", "1", "--db", db_path],
    )

    bootstrap.main()

    assert signal_ledger.contar(conn) == 0
    assert db.kv_get(conn, signal_ledger.K_CUMULATIVO, user_id=None) is None
