"""server/tests/test_signal_ledger_bootstrap.py — bootstrap único do ledger de
sinais resolvidos (ADR-017, Bloco 1, Plano 03; retry de 404 + resolução de
tickers do LEDGER-01, Fase 0 v1.2, `00-01-PLAN.md`, Task 2).

Nenhum teste toca a rede: `carregar_candles`/`yahoo.get_history` são sempre
monkeypatchados. `signal_replay.replay` também é monkeypatchado nos testes de
orquestração para isolar `executar`/`bootstrap_ticker` da mecânica de
detecção de setup (já coberta em `test_signal_replay.py`).
"""
import asyncio

import httpx

from app import db, ledger_tickers, signal_ledger, signal_ledger_bootstrap as bootstrap


def _erro_404(url="https://query1.finance.yahoo.com/v8/finance/chart/X.SA"):
    req = httpx.Request("GET", url)
    resp = httpx.Response(404, request=req)
    return httpx.HTTPStatusError("404 Not Found", request=req, response=resp)


async def _sem_sleep(*_a, **_k):
    return None


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


# ===== carregar_candles: retry escopado de 404 (A-03) ========================


def test_carregar_candles_retry_em_404_sucesso_na_segunda_tentativa_nao_vira_erro(monkeypatch):
    chamadas = {"n": 0}

    async def get_history_fake(ticker, rng="1mo", interval="1d"):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            raise _erro_404()
        return {"candles": [{"date": "2025-01-01"}]}

    monkeypatch.setattr(bootstrap.yahoo, "get_history", get_history_fake)
    monkeypatch.setattr(bootstrap.asyncio, "sleep", _sem_sleep)

    candles = asyncio.run(bootstrap.carregar_candles("PETR4", "15y"))

    assert candles == [{"date": "2025-01-01"}]
    assert chamadas["n"] == 2  # 1 falha + 1 retry — não tentou uma terceira vez


def test_carregar_candles_falha_nas_duas_tentativas_continua_erro(monkeypatch):
    async def get_history_fake(ticker, rng="1mo", interval="1d"):
        raise _erro_404()

    monkeypatch.setattr(bootstrap.yahoo, "get_history", get_history_fake)
    monkeypatch.setattr(bootstrap.asyncio, "sleep", _sem_sleep)

    try:
        asyncio.run(bootstrap.carregar_candles("PETR4", "15y"))
        assert False, "esperava HTTPStatusError apos esgotar as tentativas"
    except httpx.HTTPStatusError:
        pass


def test_carregar_candles_erro_nao_404_sobe_na_primeira_tentativa_sem_retry(monkeypatch):
    chamadas = {"n": 0}

    async def get_history_fake(ticker, rng="1mo", interval="1d"):
        chamadas["n"] += 1
        raise RuntimeError("erro qualquer, não é 404")

    monkeypatch.setattr(bootstrap.yahoo, "get_history", get_history_fake)
    monkeypatch.setattr(bootstrap.asyncio, "sleep", _sem_sleep)

    try:
        asyncio.run(bootstrap.carregar_candles("PETR4", "15y"))
        assert False, "esperava RuntimeError sem retry"
    except RuntimeError:
        pass
    assert chamadas["n"] == 1  # decisão A-03: só 404 (ou "sem historico") repete


# ===== executar: resolução via ledger_tickers (exclusão + alias) ============


def test_executar_ticker_excluido_nao_chama_carregar_candles_e_entra_em_excluidos(
    tmp_path, monkeypatch,
):
    conn = _conn(tmp_path)
    chamado_para = []

    async def carregar_fake(ticker, rng):
        chamado_para.append(ticker)
        return [{"date": "2025-01-01"}]

    monkeypatch.setattr(bootstrap, "carregar_candles", carregar_fake)
    monkeypatch.setattr(bootstrap.signal_replay, "replay",
                         lambda ticker, cs, dias: [_linha(ticker, "2025-01-10")])
    monkeypatch.setitem(ledger_tickers.EXCLUIDOS, "TESTEX3", "razão de teste, não vazia")

    try:
        resumo = asyncio.run(bootstrap.executar(
            conn, ["PETR4", "TESTEX3"], anos=1.0, rng="15y", concorrencia=2,
        ))
        assert "TESTEX3" not in chamado_para
        assert resumo["erros"] == []
        assert resumo["excluidos"] == [
            {"ticker": "TESTEX3", "razao": "razão de teste, não vazia"}
        ]
        assert resumo["linhas"] == 1  # só PETR4 contribuiu
        assert signal_ledger.contar(conn) == 1
    finally:
        del ledger_tickers.EXCLUIDOS["TESTEX3"]


def test_executar_ticker_com_alias_busca_pelo_alias_mas_grava_sob_ticker_do_universo(
    tmp_path, monkeypatch,
):
    conn = _conn(tmp_path)
    chamado_com = []

    async def carregar_fake(ticker, rng):
        chamado_com.append(ticker)
        return [{"date": "2025-01-01"}]

    gravado_sob = []

    def bootstrap_ticker_fake(conn_, ticker, candles, dias):
        gravado_sob.append(ticker)
        linhas = [_linha(ticker, "2025-01-10")]
        novas = signal_ledger.registrar_linhas(conn_, linhas)
        return len(linhas), novas

    monkeypatch.setattr(bootstrap, "carregar_candles", carregar_fake)
    monkeypatch.setattr(bootstrap, "bootstrap_ticker", bootstrap_ticker_fake)
    monkeypatch.setitem(ledger_tickers.ALIASES, "TESTOR3", "TESTAL3")

    try:
        resumo = asyncio.run(bootstrap.executar(
            conn, ["TESTOR3"], anos=1.0, rng="15y", concorrencia=2,
        ))
        assert chamado_com == ["TESTAL3"]  # busca pelo símbolo do ALIAS
        assert gravado_sob == ["TESTOR3"]  # grava sob o ticker do UNIVERSO
        assert resumo["excluidos"] == []
        assert resumo["erros"] == []
    finally:
        del ledger_tickers.ALIASES["TESTOR3"]


def test_executar_sempre_tem_chave_excluidos_mesmo_sem_exclusao(tmp_path, monkeypatch):
    conn = _conn(tmp_path)

    async def carregar_fake(ticker, rng):
        return [{"date": "2025-01-01"}]

    monkeypatch.setattr(bootstrap, "carregar_candles", carregar_fake)
    monkeypatch.setattr(bootstrap.signal_replay, "replay",
                         lambda ticker, cs, dias: [_linha(ticker, "2025-01-10")])

    resumo = asyncio.run(bootstrap.executar(
        conn, ["PETR4"], anos=1.0, rng="15y", concorrencia=2,
    ))

    assert resumo["excluidos"] == []
