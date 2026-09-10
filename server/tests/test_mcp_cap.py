"""aba-opcoes F1 (ADR-027) — cap por usuário/dia da aba Opções, pelo caminho
HTTP completo (TestClient), OFFLINE.

O que este arquivo trava, em uma frase cada:
  - a recusa por cota acontece ANTES de tocar o serviço (espião prova);
  - o dia do cap vira em São Paulo, não em UTC;
  - o contador da aba Opções NÃO contamina o balde de análises de IA;
  - cache não gasta cap;
  - erro de tool em `/status` vira 200 com `bloqueia`, não 422;
  - teto do serviço vira 402 com `reinicia`/`escopo` do próprio serviço.

Isolamento igual a `test_adr013_rbac.py` (B3_DB_PATH temporário + reset dos
caches em memória). Nenhum teste depende de credencial real — o
`mcp_client.call_tool` é substituído por um espião em todos eles.
"""
from __future__ import annotations

from datetime import datetime, timezone
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
    d = tempfile.mkdtemp(prefix="b3_mcp_cap_test_")
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


def _espiao(monkeypatch, resultado=None, erro=None):
    """Substitui `mcp_client.call_tool` e registra cada chamada. É o espião
    que prova a afirmação central do cap: a recusa acontece ANTES da rede."""
    chamadas: list = []

    async def _falso(nome, args=None, *, read_timeout_seconds=None):
        chamadas.append((nome, args))
        if erro is not None:
            raise erro
        return resultado if resultado is not None else mcp_client.ResultadoTool({}, False)

    monkeypatch.setattr(mcp_client, "call_tool", _falso)
    return chamadas


_FRESCOR_OK = {"trading_date": "2026-09-08",
               "classes": [{"classe": "negociacao_b3", "situacao": "em_dia"}]}


# ------------------------------------------------------------------ 401 ---
def test_status_sem_sessao_e_401_antes_do_cap(monkeypatch):
    c, _ = _client(monkeypatch)
    chamadas = _espiao(monkeypatch)
    r = c.get("/api/options/mcp/status")
    assert r.status_code == 401
    assert chamadas == [], "rota anônima chegou a tocar o serviço"


# ------------------------------------------------------------------ 503 ---
def test_logado_sem_segredo_e_503_mcp_nao_configurado(monkeypatch):
    c, _ = _client(monkeypatch)
    monkeypatch.delenv("MCP_CLIENT_ID", raising=False)
    monkeypatch.delenv("MCP_CLIENT_SECRET", raising=False)
    p = _registra(c)

    # sem espião: o caminho real tem de morrer em McpNaoConfigurado, dentro
    # do `_access_token`, SEM tocar a rede
    r = c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    assert r.status_code == 503, r.text
    assert r.json()["detail"]["code"] == "mcp_nao_configurado"
    # a mensagem diz o que fazer, sem ecoar valor nenhum
    assert "MCP_CLIENT_ID" in r.json()["detail"]["action"]


# ------------------------------------------------------------------ 402 ---
def test_cota_cheia_recusa_com_402_sem_tocar_o_servico(monkeypatch):
    c, main = _client(monkeypatch)
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "60")
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao(monkeypatch, mcp_client.ResultadoTool(_FRESCOR_OK, False))

    # 60 chamadas gravadas direto no kv — fazer 60 requests só testaria o
    # laço do TestClient, não o cap
    db.kv_set(main._conn, "mcpUsage",
              {"day": options_mcp_api._dia_sp(), "count": 60, "rl": []}, user_id=uid)

    r = c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    assert r.status_code == 402, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "mcp_cota"
    assert detalhe["usado"] == 60 and detalhe["limite"] == 60
    assert detalhe["reinicia"] == "00:00 America/Sao_Paulo"
    # o texto é da ABA, não o copy de BYOK do metering
    assert "BYOK" not in detalhe["message"]
    assert chamadas == [], "a 61ª chamada tocou o serviço mesmo com a cota cheia"


# ------------------------------------------------------------------ fuso ---
def test_dia_do_cap_vira_a_meia_noite_de_sao_paulo_nao_em_utc():
    """02:30 UTC de 10/09 ainda é 23:30 de 09/09 em São Paulo. É essa
    diferença de três horas que o teste trava: com o dia em UTC, o cap do
    usuário zeraria três horas ANTES do teto do serviço (que reinicia às
    00:00 America/Sao_Paulo), e o app liberaria chamada que o serviço já
    estaria recusando."""
    agora = datetime(2026, 9, 10, 2, 30, tzinfo=timezone.utc)
    assert options_mcp_api._dia_sp(agora) == "2026-09-09"
    assert options_mcp_api._mes_sp(agora) == "2026-09"
    # o que `metering._today()` (UTC, sem override) diria no mesmo instante:
    assert agora.strftime("%Y-%m-%d") == "2026-09-10"
    # e depois da virada em SP, o dia acompanha
    assert options_mcp_api._dia_sp(
        datetime(2026, 9, 10, 3, 30, tzinfo=timezone.utc)) == "2026-09-10"


# ------------------------------------------------------- não-contaminação ---
def test_consume_grava_nas_secoes_mcp_e_nao_toca_o_balde_de_ia(monkeypatch):
    """[R-1] do PLANO: sem `month_section` próprio, cada chamada de tool
    queimaria o balde MENSAL de análises do plano comercial (`aiUsageMonth`)
    — o usuário perderia análise de IA por olhar a aba Opções."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao(monkeypatch, mcp_client.ResultadoTool(_FRESCOR_OK, False))

    r = c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text

    assert metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp()) == 1
    assert metering.month_used(main._conn, uid, section="mcpUsageMonth",
                               _mes=options_mcp_api._mes_sp()) == 1
    assert db.kv_get(main._conn, "mcpUsageGlobal", None, user_id=None)["count"] == 1

    # e o balde da IA gerenciada continua intocado
    assert db.kv_get(main._conn, "aiUsageMonth", None, user_id=uid) in (None, {})
    assert metering.month_used(main._conn, uid) == 0
    assert metering.used(main._conn, uid) == 0


# ------------------------------------------------------------------ cache ---
def test_cache_hit_nao_consome_cap(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]

    chamadas: list = []
    estado = {"cache": False}

    async def _falso(nome, args=None, *, read_timeout_seconds=None):
        chamadas.append(nome)
        resultado = mcp_client.ResultadoTool(_FRESCOR_OK, estado["cache"])
        estado["cache"] = True   # da 2ª em diante o cliente serve do cache L1
        return resultado

    monkeypatch.setattr(mcp_client, "call_tool", _falso)

    assert c.get("/api/options/mcp/status", headers=_auth(p["token"])).status_code == 200
    assert metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp()) == 1

    for _ in range(3):
        assert c.get("/api/options/mcp/status", headers=_auth(p["token"])).status_code == 200
    assert metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp()) == 1, \
        "acerto de cache cobrou cap — o custo que o cap protege é a chamada ao serviço"


# ---------------------------------------------------------------- frescor ---
def test_erro_de_tool_no_status_e_200_com_bloqueia_true(monkeypatch):
    """DECISÃO registrada no ADR-027 (e levada ao Alex no SUMMARY): o
    mapeamento geral manda `McpErroDeTool → 422`, mas em `/status` a
    finalidade da rota é REPORTAR o estado do dado. 422 faria a tela não
    saber dizer nada, e "idade desconhecida" viraria silêncio — que o
    usuário lê como "em dia" (princípio 9 do CLAUDE.md)."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, erro=mcp_client.McpErroDeTool(
        "hub MyData inacessível", available=None, hint="tente em alguns minutos"))

    r = c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    frescor = r.json()["frescor"]
    assert frescor["bloqueia"] is True
    assert "hub MyData inacessível" in frescor["warning"]
    assert r.json()["pregao"] is None, "pregão fabricado numa resposta sem pregão"


def test_frescor_sem_a_classe_critica_bloqueia_com_motivo_explicito(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, mcp_client.ResultadoTool(
        {"trading_date": "2026-09-08", "classes": [{"classe": "provento_b3", "situacao": "em_dia"}]},
        False))

    frescor = c.get("/api/options/mcp/status", headers=_auth(p["token"])).json()["frescor"]
    assert frescor["bloqueia"] is True
    assert "negociacao_b3" in frescor["warning"]


def test_frescor_com_classe_critica_atrasada_bloqueia(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, mcp_client.ResultadoTool(
        {"trading_date": "2026-09-05",
         "classes": {"negociacao_b3": {"situacao": "atrasada", "idade_horas": 51}}},
        False))

    corpo = c.get("/api/options/mcp/status", headers=_auth(p["token"])).json()
    assert corpo["frescor"]["bloqueia"] is True
    assert corpo["frescor"]["warning"] is None, \
        "atraso MEDIDO não é 'não medido' — a UI precisa distinguir os dois"
    assert corpo["frescor"]["stale"][0]["classe"] == "negociacao_b3"
    assert corpo["pregao"] == "2026-09-05"


def test_frescor_em_dia_nao_bloqueia_e_devolve_o_bruto_para_a_fase_2(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, mcp_client.ResultadoTool(_FRESCOR_OK, False))

    corpo = c.get("/api/options/mcp/status", headers=_auth(p["token"])).json()
    assert corpo["frescor"]["bloqueia"] is False
    assert corpo["frescor"]["warning"] is None
    assert corpo["frescor"]["bruto"] == _FRESCOR_OK
    assert corpo["fonte"] == "mcp.semente.dev"
    assert corpo["at"].endswith(" BRT")
    assert corpo["cap"] == {"usado": 1, "limite": 60, "reinicia": "00:00 America/Sao_Paulo"}


# ----------------------------------------------------------- teto/erro ----
def test_teto_do_servico_vira_402_com_reinicia_e_escopo(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, erro=mcp_client.McpTetoAtingido(
        "teto diário de 2000 chamadas atingido para boris",
        {"escopo": "global", "reinicia": "00:00 America/Sao_Paulo", "chamadas_hoje": 10000}))

    r = c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    assert r.status_code == 402, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "mcp_teto_servico"
    assert detalhe["reinicia"] == "00:00 America/Sao_Paulo"
    assert detalhe["escopo"] == "global"


def test_indisponivel_vira_503_sem_numero_e_sem_credencial(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, erro=mcp_client.McpNaoAutorizado(
        "o serviço recusou a credencial (MCP_CLIENT_SECRET errado)"))

    r = c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    assert r.status_code == 503, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "mcp_indisponivel"
    # 401/403 e 5xx são a MESMA frase para o usuário: dizer "credencial
    # recusada" na tela não ajuda quem não configura o servidor, e o detalhe
    # já está no obslog para quem configura.
    assert "MCP_CLIENT_SECRET" not in detalhe["message"]
    assert "401" not in detalhe["message"] and "403" not in detalhe["message"]


def test_mcp_url_com_esquema_invalido_vira_503_e_nunca_500(monkeypatch):
    """`url()` levanta `ValueError`, que sem tratamento cairia no handler
    genérico de 500 — o ADR-027 exige que NADA da aba caia nele."""
    c, _ = _client(monkeypatch)
    monkeypatch.setenv("MCP_CLIENT_ID", "boris")
    monkeypatch.setenv("MCP_CLIENT_SECRET", "segredo-de-teste-nao-e-real")
    monkeypatch.setenv("MCP_URL", "http://mcp.exemplo.invalido/mcp")
    p = _registra(c)

    r = c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    assert r.status_code == 503, r.text
    assert r.json()["detail"]["code"] == "mcp_nao_configurado"


def test_env_torta_nao_derruba_a_rota_e_cai_no_default(monkeypatch):
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "banana")
    assert options_mcp_api._cota_usuario() == 60
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "-5")
    assert options_mcp_api._cota_usuario() == 60
    monkeypatch.setenv("B3_MCP_RATE_MIN", "")
    assert options_mcp_api._rate_min() == 20
    monkeypatch.setenv("B3_MCP_COTA_GLOBAL_DIA", "0")
    assert options_mcp_api._cota_global() == 1800
