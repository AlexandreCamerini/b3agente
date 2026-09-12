"""2026-09-12 — BYOK passa NA FRENTE do gate MENSAL do plano.

Achado a partir de um bloqueio real: a conta bateu as 30 analises/mes do
PLAN_FREE e, ao configurar a PROPRIA chave de LLM, continuou barrada.

A causa e de PRECEDENCIA, nao de politica comercial. `_gate_analise`
consultava `plan.can_analyze(metering.month_used(...))` ANTES de qualquer
verificacao de chave propria, e `month_used` conta EXCLUSIVAMENTE o consumo da
chave do SERVIDOR (`metering.consume` so roda no ramo gerenciado de
`_ai_apply_managed`; com BYOK esse ramo devolve `lambda: None` na primeira
linha). O gate barrava por consumo de um recurso que quem tem chave propria
nao ia usar — enquanto o proprio codigo ja prometia o contrario em duas
frases: o comentario "BYOK utilizavel -> sem cota" em `_ai_apply_managed` e o
texto do 402 falando de "analises do seu plano" para quem nao esta usando a
chave do plano.

O que este arquivo trava, nos DOIS sentidos:

  (1) COM chave propria e ledger ACIMA do limite, o gate NAO nega.
  (2) SEM chave propria e ledger acima do limite, o gate continua negando,
      com a MESMA mensagem de hoje. Este e o guardiao do cap comercial: sem
      ele, a correcao de (1) viraria um furo no teto que protege a chave do
      servidor.
  (3) Sem chave e ABAIXO do limite, o caminho gerenciado continua sendo
      exercido (`metering.check` roda), exatamente como antes.
  (4) Conta `pro` (limite `None`) nunca e barrada, com ou sem chave.
  (5) BYOK nao mexe no ledger mensal — nao conta e nao desconta.

QUAIS FALHARAM NO RED (medido contra o commit anterior, 4 failed / 6 passed):
`test_1`, `test_1b`, `test_1c` e `test_5`. Os tres primeiros sao a correcao
propriamente dita. O `test_5` entra na lista porque so consegue medir o
ledger DEPOIS de atravessar o gate com chave propria — na ordem antiga ele
morria no 402 antes de chegar ao `assert`; e um sub-asserto do caminho novo,
nao uma prova independente de nao-regressao.

QUAIS PASSAM NOS DOIS ESTADOS (e por isso provam AUSENCIA DE REGRESSAO, nao a
correcao): `test_2`, `test_2b`, `test_3`, `test_4[sem_byok]`,
`test_4[com_byok]` e `test_5b`. O `test_2` e o mais importante deles.

Guardrail preservado: `plan.py` nao muda. A assinatura de `can_analyze` e
contrato e o modulo e o hook comercial; a precedencia e decisao do CHAMADOR
(`_gate_analise`) e e la que ela vive. Este plano muda QUANDO o gate mensal e
consultado, nunca O QUE ele mede — nenhum contador novo, nenhuma secao nova.

Isolamento igual a test_fase12_cap_analises.py / test_fase5_gate_mensal.py
(B3_DB_PATH temporario, reimport de `app.main` por teste, reset dos caches em
memoria entre casos) — `_conn` e os caches de `managed`/kill-switch/orcamento
da brapi sao globais de modulo.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


# Mesma definicao de "tem chave" que `_ai_apply_managed` usa
# (`llm.resolve_key(config)`): duas definicoes de BYOK divergem na primeira
# manutencao, entao o teste passa a chave pelo caminho real do config.
CONFIG_COM_BYOK = {"provider": "anthropic", "model": "claude-sonnet-4-5",
                   "apiKey": "sk-chave-propria-de-teste"}
CONFIG_SEM_BYOK = {"provider": "anthropic", "model": "claude-sonnet-4-5"}

MENSAGEM_LIMITE_FREE = "Voce atingiu o limite de 30 analises/mes do plano free."

# Acima do limite de 30/mes do PLAN_FREE por uma margem folgada: o caso nao
# depende da fronteira exata (essa ja e travada em test_fase12_cap_analises).
LEDGER_ESTOURADO = 100

ENV_GERENCIADA = {"B3_MANAGED_LLM_KEY": "chave-do-servidor-de-teste",
                  "B3_MANAGED_LLM_PROVIDER": "openai",
                  "B3_MANAGED_LLM_MODEL": "gpt-4o-mini"}


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import agent, brapi_budget, managed
    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, env=None):
    d = tempfile.mkdtemp(prefix="b3_gate_byok_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    for k, v in (env or {}).items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def _conta_com_ledger(c, main, email, n):
    """Monta o estado real do achado: conta free com `n` analises GERENCIADAS
    ja contadas no mes (o unico ponto de escrita do ledger mensal e
    `metering.consume`, que so roda no ramo gerenciado)."""
    payload = _registra(c, email)
    scope = payload["user"]["id"]
    main.metering.consume(main._conn, scope, custo=n)
    assert main.metering.month_used(main._conn, scope) == n
    return payload, scope


def _espiao_metering_check(monkeypatch, main):
    """Conta chamadas a `metering.check` (o gate da chave do SERVIDOR) sem
    deixar nenhuma negar — quem esta sob teste aqui e o gate MENSAL."""
    chamadas = {"n": 0}

    def _check(*_a, **_k):
        chamadas["n"] += 1
        return (True, None)
    monkeypatch.setattr(main.metering, "check", _check)
    return chamadas


async def _quote_fake(_t):
    return {"t": "PETR4", "name": "Petrobras PN", "price": 35.5, "change": 0.5}


async def _snap_fake(*_a, **_k):
    return {
        "context": {"setupsRadar": {}, "trend": {}, "volatility": {}, "levels": {}},
        "asOf": "2026-09-12", "barraEmFormacao": None, "candles": [],
        "currency": "BRL", "period": "1y", "snapshotId": "fake0001", "periodBars": [],
    }


# ---------------------------------------------------------------------------
# (1) BYOK destrava — O UNICO caso que falha contra o codigo anterior
# ---------------------------------------------------------------------------

def test_1_byok_com_ledger_acima_do_limite_nao_e_barrado(monkeypatch):
    """RED contra o codigo anterior: com a ordem antiga, `plan.can_analyze`
    decidia antes de olhar a chave e levantava 402 aqui."""
    c, main = _client(monkeypatch)
    payload, scope = _conta_com_ledger(c, main, "byok@teste.com", LEDGER_ESTOURADO)

    config, consume = main._gate_analise(scope, dict(CONFIG_COM_BYOK))

    assert config == CONFIG_COM_BYOK, (
        "com chave propria a config do usuario segue intacta — nada de "
        "config gerenciada por cima"
    )
    assert consume() is None, "o consume devolvido com BYOK e no-op"


def test_1b_byok_nao_toca_o_gate_da_chave_do_servidor(monkeypatch):
    """Mesmo com a IA gerenciada habilitada no ambiente, quem tem chave
    propria nao passa pelo `metering.check` — nao reserva nem gasta cota da
    chave do servidor."""
    c, main = _client(monkeypatch, env=ENV_GERENCIADA)
    _payload, scope = _conta_com_ledger(c, main, "byokcheck@teste.com", LEDGER_ESTOURADO)
    chamadas = _espiao_metering_check(monkeypatch, main)

    main._gate_analise(scope, dict(CONFIG_COM_BYOK))

    assert chamadas["n"] == 0, "BYOK nao pode consultar a cota da chave do servidor"


def test_1c_rota_analyze_com_byok_e_ledger_estourado_nao_diz_quota(monkeypatch):
    """O achado como o usuario o vive: a rota real, com a chave propria no
    corpo (caminho do iPhone). A chamada de IA em si e stubada — o que se
    prova e a AUSENCIA da negacao por cota/plano, nao o sucesso da IA."""
    c, main = _client(monkeypatch)
    payload, _scope = _conta_com_ledger(c, main, "byokrota@teste.com", LEDGER_ESTOURADO)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake)
    monkeypatch.setattr(main.technical_snapshot, "get", _snap_fake)

    async def _llm_indisponivel(*_a, **_k):
        raise RuntimeError("provedor fora do ar no teste")
    monkeypatch.setattr(main.llm, "analyze_structured", _llm_indisponivel)

    r = c.post("/api/analyze/PETR4", json={"config": dict(CONFIG_COM_BYOK)},
               headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    indisponivel = r.json().get("iaIndisponivel") or {}
    assert indisponivel.get("code") != "quota", (
        "com chave propria o cap mensal do plano nao pode ser o motivo"
    )
    assert indisponivel.get("mensagem") != MENSAGEM_LIMITE_FREE


# ---------------------------------------------------------------------------
# (2) GUARDIAO DO CAP COMERCIAL — sem BYOK nada muda
# ---------------------------------------------------------------------------

def test_2_sem_byok_com_ledger_acima_do_limite_continua_barrando(monkeypatch):
    """Passa nos DOIS estados do codigo, de proposito. E o teste que impede a
    correcao do caso (1) de virar furo no teto que protege a chave do
    servidor: sem chave propria, o limite mensal do plano continua valendo,
    com a mesma mensagem e o mesmo 402."""
    c, main = _client(monkeypatch)
    _payload, scope = _conta_com_ledger(c, main, "semchave@teste.com", LEDGER_ESTOURADO)

    with pytest.raises(HTTPException) as e:
        main._gate_analise(scope, dict(CONFIG_SEM_BYOK))
    assert e.value.status_code == 402
    assert e.value.detail == MENSAGEM_LIMITE_FREE


def test_2b_config_vazia_tambem_continua_barrando(monkeypatch):
    """Config sem nada (o default de quem nunca abriu a tela de IA) nao pode
    ser lida como 'tem chave' — `resolve_key({})` e falsy e o gate mensal
    segue na frente."""
    c, main = _client(monkeypatch)
    _payload, scope = _conta_com_ledger(c, main, "vazia@teste.com", LEDGER_ESTOURADO)

    with pytest.raises(HTTPException) as e:
        main._gate_analise(scope, {})
    assert e.value.status_code == 402
    assert e.value.detail == MENSAGEM_LIMITE_FREE


# ---------------------------------------------------------------------------
# (3) sem BYOK e abaixo do limite: segue para o gerenciado, como hoje
# ---------------------------------------------------------------------------

def test_3_sem_byok_abaixo_do_limite_segue_para_o_gerenciado(monkeypatch):
    c, main = _client(monkeypatch, env=ENV_GERENCIADA)
    _payload, scope = _conta_com_ledger(c, main, "abaixo@teste.com", 5)
    chamadas = _espiao_metering_check(monkeypatch, main)

    config, consume = main._gate_analise(scope, dict(CONFIG_SEM_BYOK))

    assert chamadas["n"] == 1, "sem chave propria o caminho gerenciado tem de ser exercido"
    assert config.get("keySource") == "managed", "a config efetiva vira a do servidor"
    assert callable(consume)


# ---------------------------------------------------------------------------
# (4) conta pro: limite None nunca barra, com ou sem chave
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("config,rotulo", [
    (CONFIG_SEM_BYOK, "sem_byok"),
    (CONFIG_COM_BYOK, "com_byok"),
])
def test_4_pro_nunca_e_barrado(monkeypatch, config, rotulo):
    c, main = _client(monkeypatch)
    _payload, scope = _conta_com_ledger(c, main, f"pro{rotulo}@teste.com", LEDGER_ESTOURADO)
    main.db.set_user_plan(main._conn, scope, "pro")

    cfg, consume = main._gate_analise(scope, dict(config))
    assert callable(consume)
    assert cfg is not None


# ---------------------------------------------------------------------------
# (5) o ledger nao mudou: BYOK nao conta e nao desconta
# ---------------------------------------------------------------------------

def test_5_byok_nao_conta_e_nao_desconta_no_ledger_mensal(monkeypatch):
    """Este plano muda QUANDO o gate mensal e consultado, nunca O QUE ele
    mede. Depois de uma passagem com chave propria — inclusive chamando o
    `consume` devolvido — `month_used` tem de estar no mesmo numero."""
    c, main = _client(monkeypatch)
    _payload, scope = _conta_com_ledger(c, main, "ledger@teste.com", LEDGER_ESTOURADO)

    _config, consume = main._gate_analise(scope, dict(CONFIG_COM_BYOK))
    consume()

    assert main.metering.month_used(main._conn, scope) == LEDGER_ESTOURADO


def test_5b_escopo_anonimo_continua_degradando_para_o_plano_menos_privilegiado(monkeypatch):
    """Fail-closed (T-03-13/T-03-14): `_plano_do_escopo(None)` degrada para
    `plan.ACTIVE_PLAN` e `month_used` devolve 0 para o balde sem user_id —
    o anonimo passa, mas pelo plano MENOS privilegiado, nunca por um
    superior. A ordem nova nao pode ter criado um atalho aqui."""
    c, main = _client(monkeypatch)
    espiao = {}

    def _spy(used_this_month, plan=None):
        espiao["used"] = used_this_month
        espiao["plano"] = plan
        return (True, None)
    monkeypatch.setattr(main.plan, "can_analyze", _spy)

    config, _consume = main._gate_analise(None, {})

    assert config == {}
    assert espiao["used"] == 0
    assert espiao["plano"] is main.plan.ACTIVE_PLAN
