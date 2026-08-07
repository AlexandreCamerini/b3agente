"""Fase F3 — roteamento KB → LLM em `/api/assistente`, e a rota pública nova
`GET /api/kb/buscar`.

O que estes guardiões travam, e por quê:

  • A KB RESPONDE PRIMEIRO, GRÁTIS, SEM CONTA. Uma pergunta que o catálogo
    determinístico cobre (ex. "o que é ATR") nunca deveria acionar a LLM —
    nem para anônimo, nem para quem estourou o teto. `test_kb_cobre...`
    trava isso forçando `assistente.responder` a explodir se for chamado.
  • SÓ A LLM EXIGE CONTA. Uma pergunta que a KB não cobre (porque cita um
    número específico da tela, algo que o glossário genérico não tem como
    saber) cai para a LLM — e aí sim precisa de sessão, porque `ai_activity`
    grava por `user_id` e o escopo anônimo é UM balde compartilhado.
  • `fonte` DECLARA A ORIGEM nos dois casos — é o contrato que o front usa
    para eventualmente mostrar algo diferente (D5 do plano).
  • `GET /api/kb/buscar` é a mesma busca, exposta direto, pública e sem
    custo — sem o corte de confiança do roteamento (é busca, não decisão).
"""
import asyncio
import os

import pytest
from fastapi.testclient import TestClient

from app import assistente, kb, llm
from app.main import app, current_scope

CFG = {"provider": "anthropic", "model": "claude-opus-5", "keySource": "manual",
       "apiKey": "sk-falsa", "appMode": "estudo"}

PERGUNTA_KB = "o que é ATR?"
# Cita um valor com centavos: presumivelmente sobre um número ESPECÍFICO da
# tela do usuário — o glossário genérico da KB não tem preço de ativo nenhum,
# então esta pergunta precisa da LLM (que recebe o snapshot).
PERGUNTA_FORA_DA_KB = "por que o gatilho está em 43,09 e não em outro preço"


@pytest.fixture(autouse=True)
def _env_limpo():
    chaves = ("B3_ASSISTENTE_OFF", "B3_ASSISTENTE_TETO_BRL", "B3_DIDATICA_OFF")
    antes = {k: os.environ.get(k) for k in chaves}
    for k in chaves:
        os.environ.pop(k, None)
    yield
    for k, v in antes.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


# --------------------------------------------------- kb.resolver (unitário)
def test_resolver_cobre_pergunta_generica_com_confianca():
    r = kb.resolver(PERGUNTA_KB, "educacional")
    assert r is not None and r["fonte"] == "kb" and r["id"] == "ind-atr"


def test_resolver_recusa_pergunta_sobre_numero_especifico():
    assert kb.resolver(PERGUNTA_FORA_DA_KB, "educacional") is None


def test_resolver_recusa_pergunta_vazia_ou_sem_termo_conhecido():
    assert kb.resolver("", "educacional") is None
    assert kb.resolver("qual é a previsão do tempo hoje", "educacional") is None


# --------------------------------------------------------- rota /api/assistente
def test_kb_cobre_pergunta_sem_conta_e_sem_chamar_a_llm(cli, monkeypatch):
    """Sem Authorization nenhum. Se a LLM fosse chamada aqui, o teste falharia
    ANTES de olhar a resposta — é a garantia de que a KB nunca deixa passar
    para o caminho pago quando ela mesma cobre a pergunta."""
    async def _explode(*a, **k):
        raise AssertionError("a LLM não deveria ser chamada: a KB cobre esta pergunta")
    monkeypatch.setattr(assistente, "responder", _explode)

    r = cli.post("/api/assistente", json={"pergunta": PERGUNTA_KB})
    assert r.status_code == 200
    body = r.json()
    assert body["fonte"] == "kb"
    assert body["id"] == "ind-atr"
    assert "ATR" in body["texto"]
    assert isinstance(body.get("veja"), list)


def test_kb_cobre_pergunta_nao_grava_custo_nem_ai_activity(cli, monkeypatch):
    """Segunda prova, por outro ângulo: nem `ai_activity.registrar_uso` nem o
    contador de gasto do assistente (`assistente._somar_gasto`) são tocados
    no caminho KB — os dois só existem dentro de `assistente.responder`, que
    o teste anterior já provou que não é chamado; aqui confirmamos que também
    não sobra nenhum registro novo no ledger para um escopo isolado."""
    from app import ai_activity, db as db_mod
    from app.main import _conn

    escopo_isolado = "escopo-teste-kb-nao-grava"
    antes = ai_activity.snapshot(_conn, escopo_isolado)["hoje"]["custo"]

    r = cli.post("/api/assistente", json={"pergunta": PERGUNTA_KB})
    assert r.status_code == 200 and r.json()["fonte"] == "kb"

    depois = ai_activity.snapshot(_conn, escopo_isolado)["hoje"]["custo"]
    assert depois == antes == 0.0
    assert db_mod.kv_get(_conn, "assistenteGasto", None, user_id=escopo_isolado) is None


def test_kb_nao_cobre_cai_para_llm_com_conta(cli, monkeypatch):
    async def _fake(config, key, system, user, max_tokens):
        return "resposta específica sobre o preço da tela"
    monkeypatch.setattr(llm, "_call_llm", _fake)

    app.dependency_overrides[current_scope] = lambda: "u-kb-llm-fallback"
    try:
        r = cli.post("/api/assistente", json={
            "pergunta": PERGUNTA_FORA_DA_KB,
            "config": CFG,   # BYOK: dispensa cota gerenciada/teto neste teste
            "snapshot": {"ticker": "PETR4", "gatilho": 43.09},
        })
    finally:
        app.dependency_overrides.pop(current_scope, None)

    assert r.status_code == 200
    body = r.json()
    assert body["fonte"] == "llm"
    assert body["texto"] == "resposta específica sobre o preço da tela"
    # os campos do formato antigo continuam presentes (compatibilidade).
    assert "prefixoCacheavel" in body
    assert "restanteHojeBRL" in body


def test_sem_conta_e_sem_kb_cobrindo_exige_auth(cli):
    r = cli.post("/api/assistente", json={"pergunta": PERGUNTA_FORA_DA_KB})
    assert r.status_code in (401, 403), "sem conta e sem KB cobrindo, o teto continua protegido"


# ------------------------------------------------------------- GET /api/kb/buscar
def test_kb_buscar_funciona_sem_auth_e_acha_verbete_relevante(cli):
    r = cli.get("/api/kb/buscar", params={"q": "o que é ATR"})
    assert r.status_code == 200
    body = r.json()
    assert body["resultados"], "deveria achar ao menos um verbete para ATR"
    assert body["resultados"][0]["id"] == "ind-atr"
    assert "ATR" in body["resultados"][0]["texto"]


def test_kb_buscar_respeita_o_modo():
    r_edu = TestClient(app).get("/api/kb/buscar", params={"q": "R:R", "modo": "educacional"})
    r_ope = TestClient(app).get("/api/kb/buscar", params={"q": "R:R", "modo": "operador"})
    assert r_edu.status_code == 200 and r_ope.status_code == 200
    txt_edu = r_edu.json()["resultados"][0]["texto"]
    txt_ope = r_ope.json()["resultados"][0]["texto"]
    assert txt_edu != txt_ope, "os dois modos deveriam trazer textos diferentes"


def test_kb_buscar_sem_termo_devolve_lista_vazia(cli):
    r = cli.get("/api/kb/buscar", params={"q": ""})
    assert r.status_code == 200
    assert r.json()["resultados"] == []
