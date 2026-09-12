"""aba-opcoes F1 (ADR-027) — cap por usuário/dia da aba Opções, pelo caminho
HTTP completo (TestClient), OFFLINE.

O que este arquivo trava, em uma frase cada:
  - a recusa por cota acontece ANTES de tocar o serviço (espião prova);
  - o dia do cap vira em São Paulo, não em UTC;
  - o contador da aba Opções NÃO contamina o balde de análises de IA;
  - cache não gasta cap;
  - erro de tool em `/status` vira 200 com `bloqueia`, não 422;
  - teto do serviço vira 402 com `reinicia`/`escopo` do próprio serviço;
  - **o que é reservado e não consumido VOLTA na saída da rota** (quick
    260911-lib, decisão (A) do achado A-07) — e a soma devolvida nunca
    excede a reservada, que seria cota de graça, pior que o defeito.

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


# ====================================================================== #
# Devolução da reserva não consumida — quick 260911-lib, decisão (A) do
# achado A-07. Cada teste abaixo prova UMA das quatro afirmações do plano.
# ====================================================================== #
_PROPOSTA = {"ticker": "PETR4", "behavior": {}, "catalog": [], "expirations": []}
_LISTA_PETR4 = {"setups": [{"setup": {"name": "s1", "ticker": "PETR4",
                                      "consecutive_days": 2},
                            "status": "ativo"}], "count": 1}
_AVALIACAO = {"data_freshness": {"quotes": "em_dia", "quotes_age_hours": 1},
              "evaluations": [{"name": "s1", "armed": True}]}
_LEITURA_FELIZ = {"propose_option_setups": _PROPOSTA,
                  "list_setups": _LISTA_PETR4,
                  "evaluate_setups": _AVALIACAO}


def _espiao_cache_por_tool(monkeypatch, respostas: dict, cache: dict):
    """Espião com `cache` POR TOOL — o `_espiao_por_tool` da F2 tem uma flag
    só, e um dos casos centrais aqui é a leitura MISTA: uma tool pela rede
    (consome) e outra do cache (não consome). Valor `Exception` é levantado."""
    chamadas: list = []

    async def _falso(nome, args=None, *, read_timeout_seconds=None):
        chamadas.append(nome)
        v = respostas.get(nome, {})
        if isinstance(v, Exception):
            raise v
        return mcp_client.ResultadoTool(v, bool(cache.get(nome, False)))

    monkeypatch.setattr(mcp_client, "call_tool", _falso)
    return chamadas


def _reservado(main, uid):
    return metering.reservado(main._conn, uid, section="mcpUsage",
                              _dia=options_mcp_api._dia_sp())


def _usado(main, uid):
    return metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp())


def _resv_global(main):
    g = db.kv_get(main._conn, "mcpUsageGlobal", None, user_id=None) or {}
    return len(g.get("resv") or [])


# --------------------------------------------------------------- (a) -------
def test_leitura_que_reserva_3_e_consome_1_devolve_2(monkeypatch):
    """Prova pelo ESTADO (`metering.reservado`/`used`), não por log: a rota
    reserva o custo declarado 3, consome 1 (só `propose` veio pela rede; o
    ticker não tem setup gravado, então `evaluate` é pulada) e devolve o resto.
    Sem a devolução, 2 unidades ficariam presas por até `RESERVA_TTL_S`."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    # `list_setups` devolve setup de OUTRO ticker => `evaluate_setups` é pulada
    outro = {"setups": [{"setup": {"name": "vale-x", "ticker": "VALE3",
                                   "consecutive_days": 2}, "status": "ativo"}],
             "count": 1}
    chamadas = _espiao_cache_por_tool(
        monkeypatch, dict(_LEITURA_FELIZ, list_setups=outro),
        cache={"propose_option_setups": False, "list_setups": True})

    r = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert "evaluate_setups" not in chamadas

    assert _usado(main, uid) == 1, "o consumo confirmado mudou de valor"
    assert _reservado(main, uid) == 0, (
        "sobrou reserva presa depois da resposta — as 2 unidades checadas e "
        "não consumidas só voltariam por expiração (RESERVA_TTL_S), que é o "
        "defeito A-07 que esta correção fecha")
    assert _resv_global(main) == 0, (
        "reserva presa no registro GLOBAL — o teto de 2.000/dia é de toda a "
        "base; reserva não devolvida lá bloqueia OUTROS usuários")
    # e o `cap` da resposta segue mostrando o CONFIRMADO, não o reservado
    assert r.json()["cap"]["usado"] == 1


# --------------------------------------------------------------- (b) -------
def test_leitura_que_levanta_devolve_a_reserva_inteira(monkeypatch):
    """Falha não SEGURA cota: o 422 sai com a reserva já devolvida, não com
    unidades presas até `RESERVA_TTL_S`.

    **2026-09-11 (24-07, achado F-04):** este teste também afirmava "falha não
    gasta cota" com `usado == 0`, e essa metade deixou de ser verdade por
    decisão do Alex — recusa de TOOL é viagem que o serviço já cobrou, e
    passou a debitar 1. O guardião não foi apagado: trocou o `McpErroDeTool`
    por `McpIndisponivel`, que é uma falha SEM viagem provada e continua
    provando o "não gasta" original, e a asserção de reserva presa (o que o
    teste de fato guarda) segue intacta. O novo critério tem guardião próprio
    em `test_recusa_de_tool_debita_um_porque_a_viagem_aconteceu`."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao_cache_por_tool(
        monkeypatch,
        dict(_LEITURA_FELIZ,
             propose_option_setups=mcp_client.McpIndisponivel("serviço fora do ar")),
        cache={})

    r = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"]))
    assert r.status_code == 503, r.text
    assert _usado(main, uid) == 0, "falha sem viagem provada gastou cota"
    assert _reservado(main, uid) == 0, (
        "a rota levantou e deixou a reserva presa — a devolução na saída do "
        "`with` existe exatamente para o caminho de exceção")
    assert _resv_global(main) == 0


def test_status_que_levanta_devolve_a_reserva(monkeypatch):
    """Mesma afirmação na rota de custo 1, pelo caminho 503."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao(monkeypatch, erro=mcp_client.McpNaoAutorizado("credencial recusada"))

    assert c.get("/api/options/mcp/status",
                 headers=_auth(p["token"])).status_code == 503
    assert _usado(main, uid) == 0
    assert _reservado(main, uid) == 0
    assert _resv_global(main) == 0


# --------------------------------------------------------------- (c) -------
def test_leituras_por_cache_nao_acumulam_reserva_ate_falso_esgotado(monkeypatch):
    """**O cenário que decide esta task** (medido ao vivo antes da correção).

    Com a cota em 6 e o custo declarado 3, DUAS leituras servidas inteiramente
    pelo cache reservavam 6 unidades sem consumir nenhuma, e a terceira
    recusava com 402 `mcp_cota` — "Cota do dia da aba Opções esgotada." com
    `usado: 0` no MESMO corpo, a resposta se contradizendo. Afirmação falsa ao
    usuário, a mesma classe do A-08. Medição antes da correção:

        n  http  codigo     usado  reservado
        1  200   -              0          3
        2  200   -              0          6
        3  402   mcp_cota       0          6

    O laço vai a 4 de propósito: 4 × 3 = 12 reservaria o DOBRO da cota, então
    o teste reprova mesmo se a devolução voltar só parcialmente."""
    c, main = _client(monkeypatch)
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "6")
    monkeypatch.setenv("B3_MCP_RATE_MIN", "20")
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao_cache_por_tool(monkeypatch, _LEITURA_FELIZ,
                           cache={n: True for n in _LEITURA_FELIZ})

    for n in range(1, 5):
        r = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"]))
        assert r.status_code == 200, (
            f"a {n}ª leitura respondeu {r.status_code} ({r.text}) — nenhuma "
            f"chamada ao serviço aconteceu (tudo cache) e o confirmado é "
            f"{_usado(main, uid)}/6: este 402 é um falso esgotado, feito da "
            f"reserva não consumida das leituras anteriores")
        assert _usado(main, uid) == 0, "acerto de cache cobrou cap"
        assert _reservado(main, uid) == 0, (
            f"reserva acumulada depois da {n}ª leitura — é assim que o falso "
            f"esgotado se forma")


# --------------------------------------------------------------- (d) -------
def test_a_soma_devolvida_nunca_excede_a_reservada(monkeypatch):
    """O invariante mais perigoso: devolver a MAIS daria cota de graça, pior
    que o defeito corrigido. O espião soma o que `metering.check` reservou, o
    que `consume` gastou e o que `liberar` devolveu ao longo de uma bateria de
    caminhos (rede, cache, misto, exceção) e confere a aritmética FECHADA:
    devolvido == reservado − consumido. Nunca mais, nunca menos."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]

    reservas, consumos, devolucoes = [], [], []
    check_real = metering.check
    consume_real = metering.consume
    liberar_real = metering.liberar

    def _check(conn, user_id, **kw):
        ok, motivo = check_real(conn, user_id, **kw)
        if ok:
            reservas.append(max(1, int(kw.get("custo") or 1)))
        return ok, motivo

    def _consume(conn, user_id, **kw):
        consumos.append(max(1, int(kw.get("custo") or 1)))
        return consume_real(conn, user_id, **kw)

    def _liberar(conn, user_id, **kw):
        devolucoes.append(max(1, int(kw.get("custo") or 1)))
        return liberar_real(conn, user_id, **kw)

    monkeypatch.setattr(metering, "check", _check)
    monkeypatch.setattr(metering, "consume", _consume)
    monkeypatch.setattr(metering, "liberar", _liberar)

    token = _auth(p["token"])
    # 1) leitura inteira pela rede: reserva 3, consome 3, devolve 0
    _espiao_cache_por_tool(monkeypatch, _LEITURA_FELIZ, cache={})
    assert c.get("/api/options/mcp/leitura/PETR4", headers=token).status_code == 200
    # 2) leitura inteira pelo cache: reserva 3, consome 0, devolve 3
    _espiao_cache_por_tool(monkeypatch, _LEITURA_FELIZ,
                           cache={n: True for n in _LEITURA_FELIZ})
    assert c.get("/api/options/mcp/leitura/PETR4", headers=token).status_code == 200
    # 3) leitura mista: reserva 3, consome 2, devolve 1
    _espiao_cache_por_tool(monkeypatch, _LEITURA_FELIZ, cache={"list_setups": True})
    assert c.get("/api/options/mcp/leitura/PETR4", headers=token).status_code == 200
    # 4) leitura que levanta: reserva 3, consome 0, devolve 3
    _espiao_cache_por_tool(
        monkeypatch,
        dict(_LEITURA_FELIZ,
             propose_option_setups=mcp_client.McpIndisponivel("fora do ar")),
        cache={})
    assert c.get("/api/options/mcp/leitura/PETR4", headers=token).status_code == 503
    # 5) status pela rede (custo 1, consome 1) e 6) status do cache (devolve 1)
    _espiao(monkeypatch, mcp_client.ResultadoTool(_FRESCOR_OK, False))
    assert c.get("/api/options/mcp/status", headers=token).status_code == 200
    _espiao(monkeypatch, mcp_client.ResultadoTool(_FRESCOR_OK, True))
    assert c.get("/api/options/mcp/status", headers=token).status_code == 200

    reservado, consumido, devolvido = sum(reservas), sum(consumos), sum(devolucoes)
    assert reservado == 3 + 3 + 3 + 3 + 1 + 1, reservas
    assert devolvido <= reservado, (
        f"devolvido {devolvido} > reservado {reservado} — isto é cota de "
        f"GRAÇA, pior que o defeito A-07 que a correção fecha")
    assert devolvido == reservado - consumido, (
        f"aritmética aberta: reservado={reservado} consumido={consumido} "
        f"devolvido={devolvido} — sobra presa (a menos) ou cota de graça (a mais)")
    # e o confirmado no kv é exatamente o consumido: `liberar` não toca `count`
    assert _usado(main, uid) == consumido
    assert _reservado(main, uid) == 0 and _resv_global(main) == 0


def test_reserva_toda_consumida_nao_chama_liberar(monkeypatch):
    """Borda que seria cota de graça por descuido: `metering.liberar` normaliza
    `custo` para no MÍNIMO 1 (`max(1, ...)`), então chamá-la com saldo 0
    devolveria uma unidade que ninguém reservou. `devolver()` não pode chamar."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas: list = []
    monkeypatch.setattr(metering, "liberar",
                        lambda *a, **kw: chamadas.append(kw.get("custo")))

    with options_mcp_api._cap_check(uid, 2) as cap:
        cap.consome(1)
        cap.consome(1)
    assert chamadas == [], (
        "`liberar` chamada com saldo zero — `custo=0` vira 1 lá dentro e "
        "devolveria reserva inexistente")
    assert cap.saldo == 0
    assert _usado(main, uid) == 2


def test_devolver_e_idempotente_e_nao_devolve_mais_que_o_reservado(monkeypatch):
    """Devolução explícita + saída do `with` não pode devolver duas vezes. E
    consumir MAIS que o reservado (que rota nenhuma deve fazer) satura o saldo
    em 0 em vez de virar devolução extra — sem esconder o consumo real."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    pedidos: list = []
    liberar_real = metering.liberar

    def _liberar(conn, user_id, **kw):
        pedidos.append(kw.get("custo"))
        return liberar_real(conn, user_id, **kw)

    monkeypatch.setattr(metering, "liberar", _liberar)

    with options_mcp_api._cap_check(uid, 3) as cap:
        assert cap.devolver() == 3
        assert cap.devolver() == 0, "devolveu de novo o que já havia devolvido"
    assert pedidos == [3], pedidos
    assert _reservado(main, uid) == 0

    # consumo além do reservado: o `count` recebe a verdade, o saldo satura
    with options_mcp_api._cap_check(uid, 1) as cap2:
        cap2.consome(2)
        assert cap2.saldo == 0
    assert pedidos == [3], "devolveu com o saldo já zerado"
    assert _usado(main, uid) == 2, "consumo real foi escondido"


# ------------------------------------------------------------- guardião ----
def test_guardiao_toda_rota_usa_cap_check_dentro_de_um_with():
    """O guardião (iv) de `test_mcp_guardioes.py` exige que toda rota CHAME
    `_cap_check`; este exige que a chame como context manager. Sem o `with`, a
    `_Reserva` é criada e jogada fora — a reserva volta a só expirar e o falso
    esgotado ressuscita sem nenhum teste de rota reprovar, porque o caminho
    feliz continua respondendo 200."""
    import ast
    import pathlib

    caminho = pathlib.Path(options_mcp_api.__file__).resolve()
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))

    rotas = {}
    for node in ast.walk(arvore):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            alvo = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(alvo, ast.Attribute) and isinstance(alvo.value, ast.Name) \
                    and alvo.value.id == "router":
                rotas[node.name] = node
    assert rotas, "nenhuma rota encontrada — guardião passaria por vacuidade"

    sem_with = []
    for nome, no in rotas.items():
        ok = False
        for n in ast.walk(no):
            if not isinstance(n, (ast.With, ast.AsyncWith)):
                continue
            for item in n.items:
                ctx = item.context_expr
                if isinstance(ctx, ast.Call) and isinstance(ctx.func, ast.Name) \
                        and ctx.func.id == "_cap_check":
                    ok = True
        if not ok:
            sem_with.append(nome)

    assert not sem_with, (
        f"rota(s) chamando `_cap_check` fora de um `with`: {sem_with!r} — a "
        f"reserva não consumida voltaria a ficar presa até expirar "
        f"(RESERVA_TTL_S), que é o defeito A-07 (quick 260911-lib).")


# ====================================================================== #
# 24-07 (achado F-04) — a viagem que a tool RECUSOU é cobrada.
#
# O serviço conta toda `tools/call` no porteiro, ANTES de executar a tool
# (`~/dev/MCP/servers/mydata/servico.py`, middleware; o contrato confirma:
# "Só `tools/call` conta"). Até 2026-09-11 o Boris debitava só no sucesso: a
# recusa custava o teto compartilhado de 2.000/dia e não custava nada ao cap
# de 60/dia do usuário. Decisão do Alex em 2026-09-11: **cobrar a viagem**.
#
# O critério que estes testes travam é literal: TOCOU A REDE, DEBITOU. Por
# isso a divisão abaixo não é por exceção, é por FATO — houve viagem ou não.
# ====================================================================== #
def test_recusa_de_tool_debita_um_porque_a_viagem_aconteceu(monkeypatch):
    """A tool recusou o pedido: a chamada chegou ao serviço, passou pelo
    contador dele e só depois virou `error`. Não debitar aqui é dar a recusa
    de graça para quem a provocou e cara para a base inteira."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao_cache_por_tool(
        monkeypatch,
        dict(_LEITURA_FELIZ, propose_option_setups=mcp_client.McpErroDeTool(
            "ticker inexistente", available=None, hint=None)),
        cache={})

    r = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"]))
    assert r.status_code == 422, r.text
    assert _usado(main, uid) == 1, (
        "recusa de tool não debitou o cap — a viagem ACONTECEU e o teto "
        "compartilhado de 2.000/dia já foi cobrado pelo serviço (F-04)")
    assert _reservado(main, uid) == 0, "o 422 saiu com reserva presa"


@pytest.mark.parametrize("erro,http", [
    # não houve viagem: falta credencial, o cliente nem abre sessão
    (mcp_client.McpNaoConfigurado("sem MCP_CLIENT_SECRET"), 503),
    # o porteiro recusa ANTES do contador de tools do serviço
    (mcp_client.McpNaoAutorizado("o serviço recusou a credencial"), 503),
    # timeout/5xx: não há PROVA de que o serviço contou, e cobrar por
    # indisponibilidade puniria o usuário pela queda do fornecedor
    (mcp_client.McpIndisponivel("timeout ao falar com o serviço"), 503),
    # o próprio contrato do serviço diz que a chamada recusada por teto não
    # conta — cobrar aqui seria inventar um débito que ninguém fez
    (mcp_client.McpTetoAtingido("teto diário atingido",
                                {"escopo": "global", "reinicia": "00:00"}), 402),
])
def test_as_quatro_falhas_sem_viagem_provada_nao_debitam(monkeypatch, erro, http):
    """O espelho do teste acima, e a metade que impede a "uniformização":
    cobrar o que não se sabe se foi cobrado é o MESMO erro do F-04, invertido.
    Cada motivo está comentado no `_chamada_com_cap` e repetido aqui."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao_cache_por_tool(
        monkeypatch, dict(_LEITURA_FELIZ, propose_option_setups=erro), cache={})

    r = c.get("/api/options/mcp/leitura/PETR4", headers=_auth(p["token"]))
    assert r.status_code == http, r.text
    assert _usado(main, uid) == 0, (
        f"{type(erro).__name__} debitou o cap — ou a viagem não aconteceu, ou "
        f"o próprio serviço declara que não cobrou por ela")
    assert _reservado(main, uid) == 0, "a falha saiu com reserva presa"


def test_status_com_erro_de_tool_segue_200_e_debita_um(monkeypatch):
    """`/status` chama `call_tool` DIRETO (não passa por `_chamada_com_cap`) e
    trata a recusa como ESTADO, respondendo 200 com `frescor.bloqueia` — isso
    não muda. O que muda é o débito: a viagem aconteceu igual, e uma rota
    respondendo 200 é justamente a que ninguém desconfiaria de ter custado."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao(monkeypatch, erro=mcp_client.McpErroDeTool(
        "hub MyData inacessível", available=None, hint=None))

    r = c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert r.json()["frescor"]["bloqueia"] is True
    assert _usado(main, uid) == 1, (
        "erro de tool no /status não debitou — a rota responde 200 e a viagem "
        "aconteceu (F-04)")
    assert r.json()["cap"]["usado"] == 1, (
        "o bloco `cap` da própria resposta contradiz o que foi cobrado")
    assert _reservado(main, uid) == 0


# ====================================================================== #
# 24-15 (pedido do Alex, 2026-09-11) — os três tetos da aba Opções deixam
# de ser só env do Railway.
#
# A ordem é memória → kv → env → default, e cada camada tem uma razão:
#   · kv    — sobrevive a redeploy; é o que faz o painel valer de fato;
#   · env   — continua valendo porque é como o Railway muda um teto sem
#             publicar código (e é o que `monkeypatch.setenv` exercita);
#   · default — o que roda numa instalação limpa, sem nada configurado.
#
# Lixo em qualquer camada cai para a seguinte. Um `0` vindo do banco
# desligaria o freio do teto compartilhado de 2.000/dia do serviço, que é o
# oposto exato do que um limite existe para fazer.
# ====================================================================== #
def test_sem_kv_e_sem_env_os_tres_limites_sao_os_defaults_de_hoje(monkeypatch):
    _client(monkeypatch)
    assert options_mcp_api.cota_usuario_dia() == 60
    assert options_mcp_api.rate_min() == 20
    assert options_mcp_api.cota_global_dia() == 1800

    lim = options_mcp_api.limites()
    assert [lim[k]["valor"] for k in ("cotaUsuarioDia", "rateMin", "cotaGlobalDia")] == [60, 20, 1800]
    assert [lim[k]["origem"] for k in ("cotaUsuarioDia", "rateMin", "cotaGlobalDia")] == ["default"] * 3


def test_so_env_continua_mandando_e_a_origem_diz_env(monkeypatch):
    """Não-regressão do comportamento de HOJE: quem configurou os tetos por
    env do Railway não perde nada com este plano."""
    _client(monkeypatch)
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "9")
    monkeypatch.setenv("B3_MCP_RATE_MIN", "3")
    monkeypatch.setenv("B3_MCP_COTA_GLOBAL_DIA", "99")

    lim = options_mcp_api.limites()
    assert (lim["cotaUsuarioDia"]["valor"], lim["cotaUsuarioDia"]["origem"]) == (9, "env")
    assert (lim["rateMin"]["valor"], lim["rateMin"]["origem"]) == (3, "env")
    assert (lim["cotaGlobalDia"]["valor"], lim["cotaGlobalDia"]["origem"]) == (99, "env")
    assert options_mcp_api._cota_usuario() == 9


def test_env_muda_em_runtime_sem_reiniciar_o_processo(monkeypatch):
    """O `_int_env` é lido A CADA leitura de propósito (o Railway troca env
    sem redeploy do código). Cachear a env em memória mataria isso em
    silêncio — daí o cache existir SÓ para o valor vindo do kv."""
    _client(monkeypatch)
    assert options_mcp_api.cota_usuario_dia() == 60
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "11")
    assert options_mcp_api.cota_usuario_dia() == 11, (
        "a env deixou de valer depois da primeira leitura — o cache do kv "
        "vazou para a camada de env")


def test_kv_vence_a_env_e_a_origem_diz_kv(monkeypatch):
    _client(monkeypatch)
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "9")
    monkeypatch.setenv("B3_MCP_RATE_MIN", "3")
    monkeypatch.setenv("B3_MCP_COTA_GLOBAL_DIA", "99")

    options_mcp_api.set_cota_usuario_dia(40)
    options_mcp_api.set_rate_min(5)
    options_mcp_api.set_cota_global_dia(1200)

    lim = options_mcp_api.limites()
    assert (lim["cotaUsuarioDia"]["valor"], lim["cotaUsuarioDia"]["origem"]) == (40, "kv")
    assert (lim["rateMin"]["valor"], lim["rateMin"]["origem"]) == (5, "kv")
    assert (lim["cotaGlobalDia"]["valor"], lim["cotaGlobalDia"]["origem"]) == (1200, "kv")


def test_set_persiste_no_kv_e_sobrevive_a_um_processo_novo(monkeypatch):
    """`reset_limites_cache()` é o processo novo em miniatura: memória vazia,
    kv intacto. Sem a persistência o painel viraria um ajuste que o próximo
    deploy apaga — que é exatamente o problema que este plano resolve."""
    _client(monkeypatch)
    options_mcp_api.set_cota_usuario_dia(7)
    options_mcp_api.reset_limites_cache()
    assert options_mcp_api.cota_usuario_dia() == 7
    assert options_mcp_api.limites()["cotaUsuarioDia"]["origem"] == "kv"


def test_kv_com_lixo_cai_para_env_ou_default_e_nunca_desliga_o_cap(monkeypatch):
    """Um `0`/negativo/texto no banco não pode virar "sem limite". Cai para a
    camada de baixo, igual a uma env torta."""
    from app import db

    _client(monkeypatch)
    for lixo in (0, -5, "banana", None, True, 3.5, []):
        db.kv_set(options_mcp_api._conn, "mcpCotaUsuarioDia", lixo, user_id=None)
        options_mcp_api.reset_limites_cache()
        assert options_mcp_api.cota_usuario_dia() == 60, f"kv={lixo!r} não caiu para o default"
        assert options_mcp_api.limites()["cotaUsuarioDia"]["origem"] == "default"

    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "9")
    db.kv_set(options_mcp_api._conn, "mcpCotaUsuarioDia", 0, user_id=None)
    options_mcp_api.reset_limites_cache()
    assert options_mcp_api.cota_usuario_dia() == 9
    assert options_mcp_api.limites()["cotaUsuarioDia"]["origem"] == "env"


def test_set_impoe_o_minimo_de_1_no_proprio_codigo(monkeypatch):
    """O mínimo é do CÓDIGO, não da UI: uma cota 0 não é "limite baixo", é o
    freio desligado — e a UI é a camada que menos se pode obrigar a lembrar."""
    _client(monkeypatch)
    assert options_mcp_api.set_cota_usuario_dia(0) == 1
    assert options_mcp_api.set_rate_min(-3) == 1
    assert options_mcp_api.set_cota_global_dia(0) == 1
    assert options_mcp_api.cota_usuario_dia() == 1


def test_os_privados_do_cap_delegam_nas_funcoes_publicas(monkeypatch):
    """Uma fonte de verdade só. Duas portas para o mesmo número divergem na
    primeira manutenção, e a que o `_cap_check` usa é a que decide de fato."""
    _client(monkeypatch)
    options_mcp_api.set_cota_usuario_dia(4)
    options_mcp_api.set_rate_min(2)
    options_mcp_api.set_cota_global_dia(13)
    assert (options_mcp_api._cota_usuario(), options_mcp_api._rate_min(),
            options_mcp_api._cota_global()) == (4, 2, 13)


def test_o_cap_de_verdade_passa_a_obedecer_o_valor_do_painel(monkeypatch):
    """O teste que amarra tudo: mudar pelo painel muda o 402 de verdade, sem
    deploy e sem env."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, mcp_client.ResultadoTool(_FRESCOR_OK, False))
    options_mcp_api.set_cota_usuario_dia(1)

    r1 = c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    assert r1.status_code == 200, r1.text
    r2 = c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    assert r2.status_code == 402, r2.text
    assert r2.json()["detail"]["limite"] == 1


def test_limites_publica_o_teto_do_proprio_servico(monkeypatch):
    """2.000/dia é contrato do serviço (ADR-027), não configuração do Boris —
    e é o número que dá sentido aos outros três."""
    _client(monkeypatch)
    assert options_mcp_api.TETO_SERVICO_DIA == 2000
    assert options_mcp_api.limites()["tetoServicoDia"] == 2000


def test_consumo_global_hoje_le_a_secao_propria_da_aba(monkeypatch):
    """O admin decide olhando o consumo real; o número tem de vir do MESMO
    balde que o cap usa (`mcpUsageGlobal`), não do da IA gerenciada."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, mcp_client.ResultadoTool(_FRESCOR_OK, False))

    assert options_mcp_api.consumo_global_hoje()["used"] == 0
    c.get("/api/options/mcp/status", headers=_auth(p["token"]))
    g = options_mcp_api.consumo_global_hoje()
    assert g["used"] == 1
    assert g["cap"] == options_mcp_api.cota_global_dia()
    assert metering.global_snapshot(main._conn)["used"] == 0, (
        "o consumo da aba Opções vazou para o balde global da IA gerenciada")
