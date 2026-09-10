"""aba-opcoes F2 (quick 260910-biz) — `GET /leitura/{ticker}` e
`GET /setups/{name}/grafico` pelo caminho HTTP completo, OFFLINE.

O que este arquivo trava, em uma frase cada:
  - rota anônima não toca o serviço (o teto de 2.000/dia é do SERVIDOR);
  - `behavior`/`catalog`/`expirations` viajam VERBATIM, sem reinterpretação;
  - ticker sem setup gravado PULA `evaluate_setups` (gasta 2, não 3);
  - `nao_avaliado` vira 200 com o `reason` byte a byte e ZERO veredito;
  - `sem_setups` não é bloqueio;
  - erro de tool em qualquer um dos três passos vira 422 (o 200-com-bloqueia
    é exclusividade do `/status`);
  - cota cheia recusa ANTES da rede;
  - acerto de cache não gasta cap;
  - `pregao` é `None` quando nenhuma resposta trouxe pregão.

Isolamento e esqueleto herdados de `test_mcp_cap.py` (B3_DB_PATH temporário
+ reset dos caches em memória). Nenhum teste depende de credencial real.
"""
from __future__ import annotations

import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import db, mcp_client, metering, options_mcp_api


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import agent, brapi_budget, managed

    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    mcp_client.reset_cache()
    for env in ("B3_MCP_COTA_USUARIO_DIA", "B3_MCP_RATE_MIN",
                "B3_MCP_COTA_GLOBAL_DIA", "MCP_URL"):
        monkeypatch.delenv(env, raising=False)
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    mcp_client.reset_cache()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_mcp_leitura_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email="dono@teste.com", senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def _espiao_por_tool(monkeypatch, respostas: dict, cache: bool = False):
    """Espião que despacha pelo NOME da tool.

    Mais rico que o `_espiao` da F1 (que responde o mesmo para toda tool)
    porque a `/leitura` chama TRÊS tools diferentes numa requisição só — e a
    afirmação central de dois testes é justamente *qual* delas foi chamada.

    Valor mapeado que seja `Exception` é LEVANTADO; qualquer outro vira o
    `dados` de um `ResultadoTool`. Tool sem mapeamento devolve `{}`.
    """
    chamadas: list = []

    async def _falso(nome, args=None, *, read_timeout_seconds=None):
        chamadas.append((nome, args))
        v = respostas.get(nome, {})
        if isinstance(v, Exception):
            raise v
        return mcp_client.ResultadoTool(v, cache)

    monkeypatch.setattr(mcp_client, "call_tool", _falso)
    return chamadas


def _nomes(chamadas):
    return [n for n, _a in chamadas]


_BEHAVIOR = {
    "trading_date": "2026-08-28", "close": 38.42, "sma21": 37.9, "sma63": 36.4,
    "distance_from_sma21_pct": 1.4, "distance_from_sma63_pct": 5.5,
    "trend": "alta", "rsi14": 58.2, "hv21": 0.31, "hv63": 0.28,
    "range_63_sessions": {"highest": 41.0, "lowest": 33.2},
    "change_21_sessions_pct": 4.1,
}
_CATALOGO = [{"kind": "trava_de_alta", "name": "Trava de alta",
              "thesis": ["alta moderada"], "summary": "risco limitado",
              "risk": "perde o prêmio"}]
_PROPOSTA = {
    "ticker": "PETR4", "trading_date": "2026-08-28", "underlying_price": 38.42,
    "behavior": _BEHAVIOR, "catalog": _CATALOGO,
    "expirations": ["2026-09-19", "2026-10-17"], "next_step": "escolha um vencimento",
}
_REGISTRO = {
    "setup": {"name": "petr4-rompimento", "ticker": "PETR4",
              "description": "close acima da média de 21", "conditions": [],
              "logic": "AND", "consecutive_days": 2,
              "options_intent": "trava de alta", "valid_until": None},
    "status": "ativo",
    "backtest_na_criacao": {"disparos": 7},
}
_LISTA = {"setups": [_REGISTRO], "count": 1}
_AVALIACAO = {
    "trading_date": "2026-08-28",
    "data_freshness": {"quotes": "em_dia", "quotes_age_hours": 12},
    "evaluations": [{"name": "petr4-rompimento", "ticker": "PETR4",
                     "trading_date": "2026-08-28", "status": "avaliado",
                     "conditions": [{"summary": "close > sma21", "met": True}],
                     "conditions_met_today": 1, "streak": 3,
                     "required_streak": 2, "armed": True,
                     "triggered_today": False}],
    "armed": ["petr4-rompimento"], "note": "",
}
_FELIZ = {"propose_option_setups": _PROPOSTA, "list_setups": _LISTA,
          "evaluate_setups": _AVALIACAO}

_GRAFICO = {
    "name": "petr4-rompimento", "ticker": "PETR4", "trading_date": "2026-08-28",
    "description": "close acima da média de 21", "logic": "AND",
    "required_streak": 2, "status": "ativo", "options_intent": "trava de alta",
    "conditions": [{"left": "close", "op": ">", "right": "sma21", "value": None,
                    "label": "close > sma21", "met": [True, False]}],
    "dates": ["2026-05-02", "2026-05-05"], "open": [30.0, 31.0],
    "high": [31.0, 32.0], "low": [29.0, 30.5], "close": [30.5, 31.8],
    "volume": [1000, 1200], "series": {"sma21": [None, 30.9], "rsi14": [None, 55.0]},
    "triggers": [1], "trigger_dates": ["2026-05-05"], "daily": [], "streaks": [],
}


# ------------------------------------------------------------------ 401 ---
def test_rotas_novas_sem_sessao_sao_401_antes_do_cap_e_da_rede(monkeypatch):
    c, _ = _client(monkeypatch)
    chamadas = _espiao_por_tool(monkeypatch, _FELIZ)

    assert c.get("/api/options/mcp/leitura/PETR4").status_code == 401
    assert c.get("/api/options/mcp/setups/x/grafico").status_code == 401
    assert chamadas == [], "rota anônima chegou a tocar o serviço"


# -------------------------------------------------------------- feliz ----
def test_leitura_feliz_devolve_behavior_catalogo_e_setups_verbatim(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao_por_tool(monkeypatch, _FELIZ)

    r = c.get("/api/options/mcp/leitura/petr4", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    corpo = r.json()

    # o que o serviço mandou chega intacto — a rota não reinterpreta nada
    assert corpo["behavior"] == _BEHAVIOR
    assert corpo["catalog"] == _CATALOGO
    assert corpo["expirations"] == ["2026-09-19", "2026-10-17"]
    assert corpo["pregao"] == "2026-08-28"
    assert corpo["fonte"] == "mcp.semente.dev"
    assert corpo["at"].endswith(" BRT")
    assert corpo["ticker"] == "PETR4", "ticker minúsculo na URL não foi normalizado"

    # `propose_option_setups` vai SEM direction/kind — é a forma que devolve
    # behavior/catalog/expirations de uma vez
    assert chamadas[0] == ("propose_option_setups", {"ticker": "PETR4"})
    assert _nomes(chamadas) == ["propose_option_setups", "list_setups", "evaluate_setups"]

    s = corpo["setups"][0]
    assert s["name"] == "petr4-rompimento"
    assert s["status"] == "ativo", "status do REGISTRO trocado pelo da avaliação"
    assert (s["armed"], s["streak"], s["required_streak"]) == (True, 3, 2)
    assert s["conditions"] == [{"summary": "close > sma21", "met": True}]
    assert s["backtest_na_criacao"] == {"disparos": 7}
    assert corpo["setupsNaoAvaliados"] is None
    assert corpo["frescor"]["medido"] is True and corpo["frescor"]["bloqueia"] is False
    assert corpo["frescor"]["classes"][0]["idadeHoras"] == 12
    assert metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp()) == 3


# ------------------------------------------------- economia de chamada ----
def test_ticker_sem_setup_gravado_pula_evaluate_e_gasta_2(monkeypatch):
    """Consumir MENOS que o checado é sempre permitido; o contrário não. Sem
    registro do ticker não há nada a avaliar, e a terceira chamada seria
    queimar o teto compartilhado por uma resposta que ninguém lê."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    outro = {"setups": [{"setup": {"name": "vale-x", "ticker": "VALE3",
                                   "consecutive_days": 2}, "status": "ativo"}],
             "count": 1}
    chamadas = _espiao_por_tool(monkeypatch, dict(_FELIZ, list_setups=outro))

    corpo = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"])).json()
    assert corpo["setups"] == []
    assert "evaluate_setups" not in _nomes(chamadas)
    assert metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp()) == 2
    # sem avaliação, o frescor NÃO se declara em dia
    assert corpo["frescor"]["medido"] is False
    assert corpo["frescor"]["bloqueia"] is True
    assert corpo["frescor"]["warning"] == \
        options_mcp_api.AVISO_FRESCOR_NAO_MEDIDO_NA_LEITURA


# ------------------------------------------------------- nao_avaliado ----
def test_nao_avaliado_e_200_com_reason_verbatim_e_zero_veredito(monkeypatch):
    """[R-15] do PLANO: o gate de frescor do serviço não vira erro nem
    silêncio. E nenhum cartão pode dizer "não armado" — ausência de avaliação
    não é avaliação negativa."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    motivo = ("dado de negociação com 51 h de atraso; a avaliação de setups "
              "exige fechamento do pregão anterior")
    chamadas = _espiao_por_tool(monkeypatch, dict(
        _FELIZ, evaluate_setups={"status": "nao_avaliado", "reason": motivo}))

    r = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["setupsNaoAvaliados"]["reason"] == motivo, "motivo reescrito"
    assert corpo["setups"][0]["avaliacao"] is None
    assert corpo["setups"][0]["armed"] is None
    assert corpo["setups"][0]["streak"] is None
    # `required_streak` cai no valor DECLARADO no setup, não em zero
    assert corpo["setups"][0]["required_streak"] == 2
    assert corpo["frescor"]["bloqueia"] is True
    assert corpo["frescor"]["medido"] is False
    assert corpo["frescor"]["warning"] == motivo
    assert "evaluate_setups" in _nomes(chamadas)


def test_sem_setups_nao_e_bloqueio_de_avaliacao(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao_por_tool(monkeypatch, dict(
        _FELIZ, evaluate_setups={"status": "sem_setups", "note": "nenhum ativo"}))

    corpo = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"])).json()
    assert corpo["setupsNaoAvaliados"] is None, \
        "`sem_setups` virou bloqueio — é ausência de setup, não recusa de avaliar"
    assert corpo["setups"][0]["avaliacao"] is None


# --------------------------------------------------------- sem candles ---
def test_behavior_sem_candles_chega_identico(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao_por_tool(monkeypatch, dict(
        _FELIZ, propose_option_setups=dict(_PROPOSTA,
                                           behavior={"status": "sem_candles"})))

    r = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert r.json()["behavior"] == {"status": "sem_candles"}, \
        "a rota interpretou `sem_candles` em vez de repassar"


# --------------------------------------------------------- erro de tool ---
@pytest.mark.parametrize("tool", ["propose_option_setups", "list_setups",
                                  "evaluate_setups"])
def test_erro_de_tool_em_qualquer_passo_vira_422(monkeypatch, tool):
    """O 200-com-`bloqueia` é exclusividade do `/status`, cuja finalidade é
    reportar estado do dado. Aqui o erro da tool é falha do PEDIDO."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao_por_tool(monkeypatch, dict(_FELIZ, **{
        tool: mcp_client.McpErroDeTool("ticker sem cotações",
                                       available=None, hint="confira o código")}))

    r = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"]))
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "mcp_erro_de_tool"


# ------------------------------------------------------------------ 402 ---
def test_cota_cheia_recusa_a_leitura_sem_tocar_o_servico(monkeypatch):
    c, main = _client(monkeypatch)
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "60")
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao_por_tool(monkeypatch, _FELIZ)
    db.kv_set(main._conn, "mcpUsage",
              {"day": options_mcp_api._dia_sp(), "count": 58, "rl": []}, user_id=uid)

    # 58 + custo 3 estoura 60: a recusa é pelo custo DECLARADO, antes da rede
    r = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"]))
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == "mcp_cota"
    assert chamadas == [], "leitura tocou o serviço com a cota estourada"


# ---------------------------------------------------------------- cache ---
def test_cache_hit_nas_tres_tools_nao_consome_cap(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao_por_tool(monkeypatch, _FELIZ, cache=True)

    assert c.get("/api/options/mcp/leitura/PETR4",
                 headers=_auth(p["token"])).status_code == 200
    assert metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp()) == 0, \
        "acerto de cache cobrou cap — o custo protegido é a chamada ao serviço"


# --------------------------------------------------------------- gráfico ---
def test_grafico_de_setup_devolve_envelope_e_arrays_intactos(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao_por_tool(monkeypatch, {"get_setup_chart": _GRAFICO})

    r = c.get("/api/options/mcp/setups/petr4-rompimento/grafico",
              headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert chamadas == [("get_setup_chart", {"name": "petr4-rompimento"})]
    assert corpo["pregao"] == "2026-08-28"
    assert corpo["fonte"] == "mcp.semente.dev"
    assert corpo["at"].endswith(" BRT")
    # os arrays paralelos são o dado; nenhum deles pode ser reordenado ou podado
    assert corpo["dates"] == _GRAFICO["dates"]
    assert corpo["close"] == _GRAFICO["close"]
    assert corpo["triggers"] == [1]
    assert corpo["trigger_dates"] == ["2026-05-05"]
    assert corpo["series"] == _GRAFICO["series"]
    assert metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp()) == 1


def test_grafico_de_setup_inexistente_vira_422(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao_por_tool(monkeypatch, {
        "get_setup_chart": mcp_client.McpErroDeTool("setup 'nada' não existe",
                                                    available=["petr4-rompimento"],
                                                    hint=None)})

    r = c.get("/api/options/mcp/setups/nada/grafico", headers=_auth(p["token"]))
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "mcp_erro_de_tool"
    assert r.json()["detail"]["available"] == ["petr4-rompimento"]


# ---------------------------------------------------------------- pregão ---
def test_pregao_e_none_quando_nenhuma_resposta_traz_trading_date(monkeypatch):
    """Princípio 4 do CLAUDE.md: dado que falta é dado que falta. Uma data de
    hoje aqui faria a tela carimbar leitura velha como se fosse do pregão."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    sem_data = {k: v for k, v in _PROPOSTA.items() if k != "trading_date"}
    sem_data_av = {k: v for k, v in _AVALIACAO.items() if k != "trading_date"}
    _espiao_por_tool(monkeypatch, dict(_FELIZ, propose_option_setups=sem_data,
                                       evaluate_setups=sem_data_av))

    corpo = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"])).json()
    assert corpo["pregao"] is None

    _espiao_por_tool(monkeypatch, {"get_setup_chart":
                                   {k: v for k, v in _GRAFICO.items()
                                    if k != "trading_date"}})
    g = c.get("/api/options/mcp/setups/petr4-rompimento/grafico",
              headers=_auth(p["token"])).json()
    assert g["pregao"] is None
