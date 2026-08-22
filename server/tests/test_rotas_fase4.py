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
import pathlib

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
