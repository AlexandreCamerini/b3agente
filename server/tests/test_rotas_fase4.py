"""Fase 4, Plano 04 — fiação de rotas dos achados FIX-C01/C02/C03 (Médio,
REPORT-01). Este é o único plano da fase que toca `server/app/main.py`.

Por que estes guardiões existem:

  • FIX-C01: `/api/technical/analyze/{ticker}` e `/api/analyze/{ticker}`
    devolviam 502 quando a IA não estava disponível (sem chave BYOK, sem
    cota gerenciada) — o usuário grátis nunca recebia NENHUMA explicação
    depois de operar. Agora as duas rotas devolvem 200 com uma explicação
    determinística (`explicacao_det.montar`), sem consumir cota, sem
    persistir (o reuso por `promptFp` serviria o fallback pra sempre) e sem
    poluir a instrumentação de atividade/assertividade da IA.
  • FIX-C02: `/api/buy`/`/api/sell` devolviam `HTTPException` sem deixar
    rastro — o caso mais educativo (estourou risco, caixa insuficiente)
    ficava invisível no histórico. Agora toda rejeição de conta logada é
    gravada via `store.registrar_rejeicao` ANTES do erro voltar ao cliente,
    sem mover dinheiro nem mudar o contrato de erro HTTP.
  • FIX-C03: não existia comparação com o Ibovespa no Passo 8. Agora
    `GET /api/benchmark/ibov` expõe a série via `benchmark.serie_ibov`, sem
    aceitar símbolo do cliente (T-04-04) e degradando com uma frase única.
"""
import pytest
from fastapi.testclient import TestClient

from app import (
    ai_activity,
    analysis_outcomes,
    benchmark,
    candle_provider,
    db,
    explicacao_det,
    llm,
    main,
    store,
    technical_snapshot,
    yahoo,
)

T = "ZZZZ9"


def _candles(_symbol, rng=None, **_kw):
    async def go():
        cs = [{"date": f"2026-01-01+{i}", "open": 10 + i * 0.1, "high": 10.2 + i * 0.1,
               "low": 9.8 + i * 0.1, "close": 10 + i * 0.1, "volume": 1_000_000}
              for i in range(260)]
        return {"candles": cs, "currency": "BRL"}
    return go()


async def _quote(_t):
    return {"price": 35.9, "change": -0.4}


@pytest.fixture
def cli(monkeypatch):
    monkeypatch.setattr(candle_provider, "get_history", _candles)
    monkeypatch.setattr(yahoo, "get_quote", _quote)
    technical_snapshot.reset()
    with TestClient(main.app) as c:
        yield c
    # limpeza: nenhuma análise deste ticker fica pra trás entre testes
    analyses = store.get(main._conn, "analyses", user_id=None) or {}
    if analyses.pop(T, None) is not None:
        db.kv_set(main._conn, "analyses", analyses, user_id=None)
    technical_snapshot.reset()


# ===========================================================================
# FIX-C01 — /api/technical/analyze/{ticker}
# ===========================================================================

def test_ia_sem_chave_gera_fallback_deterministico_technical(cli, monkeypatch):
    async def _sem_chave(*_a, **_k):
        raise llm.LLMUserError("Nenhuma chave de API disponível para a IA.", code="missing_key")
    monkeypatch.setattr(main.llm, "analyze_structured", _sem_chave)

    r = cli.post(f"/api/technical/analyze/{T}", json={"model": "completo"})
    assert r.status_code == 200
    body = r.json()
    assert body["fonte"] == "deterministico"
    assert body["markdown"], "fallback nunca pode devolver card vazio"
    assert body["iaIndisponivel"]["code"] == "missing_key"


def test_mensagem_do_fallback_nao_vaza_detalhe_tecnico(cli, monkeypatch):
    async def _sem_chave(*_a, **_k):
        raise llm.LLMUserError(
            "Nenhuma chave de API disponível para a IA.", code="missing_key",
            provider="anthropic", model="claude-x")
    monkeypatch.setattr(main.llm, "analyze_structured", _sem_chave)

    body = cli.post(f"/api/technical/analyze/{T}", json={"model": "completo"}).json()
    msg = body["iaIndisponivel"]["mensagem"]
    for vazamento in ("Traceback", "api_key", "sk-", "api.anthropic.com", "openai.com"):
        assert vazamento not in msg


def test_gate_402_pula_a_chamada_de_ia_por_completo(cli, monkeypatch):
    chamadas = {"n": 0}

    async def _explode(*_a, **_k):
        chamadas["n"] += 1
        raise AssertionError("a IA não deveria ser chamada: a cota já negou")
    monkeypatch.setattr(main.llm, "analyze_structured", _explode)
    monkeypatch.setattr(main, "_gate_analise",
                         lambda scope, config, custo=1: (_ for _ in ()).throw(
                             main.HTTPException(402, "Cota diária esgotada.")))

    r = cli.post(f"/api/technical/analyze/{T}", json={"model": "completo"})
    assert r.status_code == 200
    body = r.json()
    assert body["fonte"] == "deterministico"
    assert chamadas["n"] == 0
    assert body["iaIndisponivel"]["code"] == "quota"


def test_gate_erro_diferente_de_402_continua_subindo(cli, monkeypatch):
    monkeypatch.setattr(main, "_gate_analise",
                         lambda scope, config, custo=1: (_ for _ in ()).throw(
                             main.HTTPException(401, "Faça login para continuar.")))
    r = cli.post(f"/api/technical/analyze/{T}", json={"model": "completo"})
    assert r.status_code == 401


def test_fallback_nao_persiste_a_analise(cli, monkeypatch):
    async def _sem_chave(*_a, **_k):
        raise llm.LLMUserError("sem chave", code="missing_key")
    monkeypatch.setattr(main.llm, "analyze_structured", _sem_chave)

    cli.post(f"/api/technical/analyze/{T}", json={"model": "completo"})
    guardado = (store.get(main._conn, "analyses", user_id=None) or {}).get(T)
    assert guardado is None, "o fallback é efêmero — persistir contaminaria o reuso por promptFp"


def test_fallback_nao_alimenta_atividade_nem_outcomes(cli, monkeypatch):
    espioes = {"atividade": 0, "outcomes": 0}

    def _spy_atividade(*_a, **_k):
        espioes["atividade"] += 1
    def _spy_outcomes(*_a, **_k):
        espioes["outcomes"] += 1

    async def _sem_chave(*_a, **_k):
        raise llm.LLMUserError("sem chave", code="missing_key")
    monkeypatch.setattr(main.llm, "analyze_structured", _sem_chave)
    monkeypatch.setattr(main.ai_activity, "registrar_uso", _spy_atividade)
    monkeypatch.setattr(main.analysis_outcomes, "registrar", _spy_outcomes)

    cli.post(f"/api/technical/analyze/{T}", json={"model": "completo"})
    assert espioes == {"atividade": 0, "outcomes": 0}


def test_snapshot_ausente_continua_502_technical(cli, monkeypatch):
    async def _sem_historico(*_a, **_k):
        raise ValueError("sem historico")
    monkeypatch.setattr(main.technical_snapshot, "get", _sem_historico)
    r = cli.post(f"/api/technical/analyze/{T}", json={"model": "completo"})
    assert r.status_code == 502


def test_ia_ok_marca_fonte_ia_technical(cli, monkeypatch):
    async def _ok(*_a, **_k):
        return {"kpis": {"recomendacao": "Aguardar", "conviccao": "Médio"},
                "detail": {}, "proposal": {}, "markdown": "leitura da IA", "text": "leitura da IA"}
    monkeypatch.setattr(main.llm, "analyze_structured", _ok)

    body = cli.post(f"/api/technical/analyze/{T}", json={"model": "completo"}).json()
    assert body["fonte"] == "ia"
    assert body["iaIndisponivel"] is None
    assert body["markdown"] == "leitura da IA"
    # nenhum campo pré-existente desapareceu
    for campo in ("kpis", "detail", "proposal", "snapshotId", "snapshotAt", "promptFp"):
        assert campo in body


def test_gate_402_com_analise_cacheada_reaproveita_em_vez_de_cair_no_fallback(cli, monkeypatch):
    """Decisão de design (não descrita literalmente no PLAN.md): o reuso por
    `promptFp` roda ANTES da checagem de `ia_indisponivel` — servir de graça
    uma leitura de IA que JÁ foi paga não custa nada, então uma negação de
    cota não deveria esconder uma resposta boa que já existe no cache. Este
    guardião trava essa decisão explicitamente (ver SUMMARY, Deviations)."""
    async def _ok(*_a, **_k):
        return {"kpis": {}, "detail": {}, "proposal": {}, "markdown": "leitura cacheada", "text": "leitura cacheada"}
    monkeypatch.setattr(main.llm, "analyze_structured", _ok)
    r1 = cli.post(f"/api/technical/analyze/{T}", json={"model": "completo"})
    assert r1.json()["fonte"] == "ia"

    async def _explode(*_a, **_k):
        raise AssertionError("não deveria ser chamado — o reuso já resolveu, sem gastar IA")
    monkeypatch.setattr(main.llm, "analyze_structured", _explode)
    monkeypatch.setattr(main, "_gate_analise",
                         lambda scope, config, custo=1: (_ for _ in ()).throw(
                             main.HTTPException(402, "Cota diária esgotada.")))

    r2 = cli.post(f"/api/technical/analyze/{T}", json={"model": "completo"})
    assert r2.status_code == 200
    assert r2.json().get("reaproveitada") is True
    assert r2.json()["markdown"] == "leitura cacheada"


# ===========================================================================
# FIX-C01 — /api/analyze/{ticker} (rota legada)
# ===========================================================================

def test_ia_sem_chave_gera_fallback_deterministico_legado(cli, monkeypatch):
    async def _sem_chave(*_a, **_k):
        raise llm.LLMUserError("sem chave", code="missing_key")
    monkeypatch.setattr(main.llm, "analyze", _sem_chave)

    r = cli.post(f"/api/analyze/{T}", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["fonte"] == "deterministico"
    assert body["markdown"]
    assert body["iaIndisponivel"]["code"] == "missing_key"


def test_gate_402_pula_a_chamada_de_ia_legado(cli, monkeypatch):
    chamadas = {"n": 0}

    async def _explode(*_a, **_k):
        chamadas["n"] += 1
        raise AssertionError("a IA não deveria ser chamada")
    monkeypatch.setattr(main.llm, "analyze", _explode)
    monkeypatch.setattr(main, "_gate_analise",
                         lambda scope, config, custo=1: (_ for _ in ()).throw(
                             main.HTTPException(402, "Cota diária esgotada.")))

    r = cli.post(f"/api/analyze/{T}", json={})
    assert r.status_code == 200
    assert r.json()["fonte"] == "deterministico"
    assert chamadas["n"] == 0


def test_snapshot_ausente_continua_502_legado(cli, monkeypatch):
    async def _sem_historico(*_a, **_k):
        raise ValueError("sem historico")
    monkeypatch.setattr(main.technical_snapshot, "get", _sem_historico)
    r = cli.post(f"/api/analyze/{T}", json={})
    assert r.status_code == 502


def test_ia_ok_marca_fonte_ia_legado(cli, monkeypatch):
    async def _ok(*_a, **_k):
        return {"kpis": {}, "detail": {}, "proposal": {}, "markdown": "leitura", "text": "leitura"}
    monkeypatch.setattr(main.llm, "analyze", _ok)
    body = cli.post(f"/api/analyze/{T}", json={}).json()
    assert body["fonte"] == "ia"
    assert body["iaIndisponivel"] is None


# ===========================================================================
# FIX-C02 — /api/buy e /api/sell deixam rastro de rejeição
#
# Isolamento por banco temporário + reimport de `app.main` (mesmo padrão de
# `test_ordens_pendentes_rotas.py`): precisamos de uma conta LOGADA (o balde
# anônimo é compartilhado e nunca registra, T-04-12) com cash/history real,
# sem herdar estado de outros arquivos da suíte.
# ===========================================================================
import importlib
import os
import sys
import tempfile

from app import pregao as pregao_mod


def _client_isolado(monkeypatch):
    d = tempfile.mkdtemp(prefix="b3_rotas_fase4_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    sys.modules.pop("app.main", None)
    m = importlib.import_module("app.main")
    return TestClient(m.app), m


def _registrar(client, email="c02@boris.dev"):
    r = client.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    return r.json()["token"], r.json()["user"]["id"]


def _quote_fake(price):
    async def _q(_t):
        return {"price": price, "change": 0, "source": "fake"}
    return _q


@pytest.fixture(autouse=True)
def _isola_app_main():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def test_buy_caixa_insuficiente_grava_rejeicao_sem_mudar_o_erro(monkeypatch):
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "caixa-buy@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(200000.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers)
    assert r.status_code == 400
    assert r.json()["detail"] == "Caixa insuficiente."

    estado = client.get("/api/state", headers=headers).json()
    assert estado["history"][0]["status"] == "rejeitada"
    assert "Caixa insuficiente" in estado["history"][0]["motivo"]
    assert estado["cash"] == 10000.0, "rejeição não pode mover dinheiro"


def test_sell_sem_posicao_grava_rejeicao_com_pnl_nulo(monkeypatch):
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "sempos-sell@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)

    r = client.post("/api/sell", json={"t": "PETR4"}, headers=headers)
    assert r.status_code == 400
    assert r.json()["detail"] == "Sem posicao em PETR4"

    estado = client.get("/api/state", headers=headers).json()
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada"
    assert entry["type"] == "VENDA"
    assert entry["pnl"] is None


def test_rejeicao_por_falta_de_cotacao_grava_price_none(monkeypatch):
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "semcotacao-buy@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)

    async def _sem_preco(_t):
        return {"price": None}
    monkeypatch.setattr(m.candle_provider, "get_quote", _sem_preco)

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers)
    assert r.status_code == 502

    estado = client.get("/api/state", headers=headers).json()
    entry = estado["history"][0]
    assert entry["status"] == "rejeitada"
    assert entry["price"] is None, "nunca 0 nem 0.0 — CLAUDE.md item 4"


def test_rejeicao_anonima_nao_grava_no_balde_compartilhado(monkeypatch):
    client, m = _client_isolado(monkeypatch)
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(200000.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100})
    assert r.status_code == 400

    estado_anonimo = client.get("/api/state").json()
    assert estado_anonimo["history"] == [], "balde anônimo compartilhado — nunca registra rejeição"


def test_compra_bem_sucedida_grava_status_executada_sem_regressao(monkeypatch):
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "ok-buy@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)
    monkeypatch.setattr(m.candle_provider, "get_quote", _quote_fake(10.0))

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["history"][0]["status"] == "executada"
    assert body["cash"] == 10000.0 - 1000.0
    assert body["positions"][0]["t"] == "PETR4" and body["positions"][0]["qty"] == 100


def test_ticker_normalizado_no_registro_de_rejeicao(monkeypatch):
    """petr4 minúsculo é um ticker VÁLIDO (>=4 chars após normalizar) — a
    rejeição real aqui é falta de cotação; o que este teste trava é que o
    `t` gravado é sempre o normalizado, nunca a string crua do corpo."""
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "normaliza-buy@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)

    async def _sem_preco(_t):
        return {"price": None}
    monkeypatch.setattr(m.candle_provider, "get_quote", _sem_preco)

    r = client.post("/api/buy", json={"t": "petr4", "qty": 100}, headers=headers)
    assert r.status_code == 502

    estado = client.get("/api/state", headers=headers).json()
    assert estado["history"][0]["t"] == "PETR4"
    assert "petr4" not in str(estado["history"][0]["t"])


# ===========================================================================
# FIX-C03 — GET /api/benchmark/ibov
# ===========================================================================

def test_benchmark_ibov_200_com_contrato_esperado(cli, monkeypatch):
    async def _serie(period=None):
        return {"t": "^BVSP", "nome": "Ibovespa", "fonte": "yahoo",
                "candles": [{"date": "2026-08-20", "close": 130000.0}], "asOf": "2026-08-20"}
    monkeypatch.setattr(main.benchmark, "serie_ibov", _serie)

    r = cli.get("/api/benchmark/ibov")
    assert r.status_code == 200
    body = r.json()
    assert {"t", "nome", "fonte", "candles", "asOf"} <= set(body.keys())


def test_benchmark_ibov_indisponivel_502_com_frase_unica(cli, monkeypatch):
    async def _explode(period=None):
        raise benchmark.BenchmarkIndisponivel("Ibovespa: provedor indisponivel no momento.")
    monkeypatch.setattr(main.benchmark, "serie_ibov", _explode)

    r = cli.get("/api/benchmark/ibov")
    assert r.status_code == 502
    assert r.json()["detail"] == "Comparação com o Ibovespa indisponível agora."


def test_benchmark_ibov_mensagem_nao_vaza_detalhe_do_provedor(cli, monkeypatch):
    async def _explode(period=None):
        raise benchmark.BenchmarkIndisponivel(
            "crumb invalido no host query1.finance.yahoo.com (cookie expirado)")
    monkeypatch.setattr(main.benchmark, "serie_ibov", _explode)

    msg = cli.get("/api/benchmark/ibov").json()["detail"]
    for vazamento in ("crumb", "cookie", "yahoo.com", "query1"):
        assert vazamento not in msg


def test_benchmark_ibov_handler_nao_aceita_simbolo_do_cliente():
    import inspect
    sig = inspect.signature(main.benchmark_ibov)
    assert not ({"ticker", "t", "symbol"} & set(sig.parameters.keys())), \
        "a rota não pode aceitar símbolo do cliente (T-04-04) — só benchmark.SIMBOLO"


def test_benchmark_ibov_cache_evita_segunda_chamada_ao_provedor(cli, monkeypatch):
    benchmark.limpar_cache()
    chamadas = {"n": 0}

    async def _fake_yfetch(client, path, params, retries=3):
        chamadas["n"] += 1
        ts = [1735707600, 1735794000]
        return {"chart": {"result": [{
            "meta": {"gmtoffset": -10800, "dataGranularity": "1d"},
            "timestamp": ts,
            "indicators": {"quote": [{"close": [128000.0, 129000.0]}]},
        }]}}
    monkeypatch.setattr(yahoo, "_yfetch", _fake_yfetch)

    r1 = cli.get("/api/benchmark/ibov")
    r2 = cli.get("/api/benchmark/ibov")
    assert r1.status_code == 200 and r2.status_code == 200
    assert chamadas["n"] == 1, "o cache do módulo (TTL 900s) está no caminho da rota"
    benchmark.limpar_cache()


def test_benchmark_ibov_posicionado_antes_do_catch_all(cli):
    """A ordem de `app.mount()` importa nesta base: `/` (catch-all do web_dist)
    tem que continuar sendo o ÚLTIMO mount, senão a rota nova ficaria
    inalcançável atrás dele."""
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert src.index('@app.get("/api/benchmark/ibov")') < src.index('app.mount("/",')
