"""Fase 27 — as DUAS rotas de listagem de vigias, pelo caminho HTTP completo,
OFFLINE.

O defeito que originou a fase: um setup gravado era indistinguível de um que
nunca existiu, porque não havia rota de listagem e a única leitura filtrava
por ticker. Estas duas rotas são a correção, e elas existem em par porque são
dois CUSTOS diferentes — trocar uma pela outra é o defeito que o ADR-027 §3.3
proíbe (custo de MCP só em clique explícito, nunca ao abrir tela).

O que este arquivo trava, em uma frase cada:
  - `GET /api/options/vigias` NÃO toca o serviço (bomba em `call_tool`) e não
    gasta cap nenhum — é a rota que a aba chama ao ABRIR;
  - escopo anônimo recebe `[]` e não vê o índice de ninguém;
  - `GET /api/options/mcp/setups` com índice vazio gasta 1 e PULA
    `evaluate_setups` — avaliar uma lista vazia queima o teto compartilhado
    por uma resposta que ninguém lê;
  - com 2 vigias gasta 2, e com 10 vigias **continua gastando 2**: a listagem
    não pode virar N chamadas;
  - item do índice que sumiu do armazém volta com `status: None` e MOTIVO —
    sumir é fato a mostrar, não item a apagar em silêncio;
  - registro meu que o índice não conhece volta com `noIndice: false`, nunca
    omitido (um produto que só enxerga o que nasceu depois dele não corrigiu o
    defeito da fase, mudou de assunto);
  - a ordenação põe o `armed` na frente — "quem disparou primeiro", não
    alfabética;
  - setup de OUTRO dono e setup LEGADO não aparecem em nenhuma das duas.

Esqueleto e isolamento herdados de `test_options_mcp_leitura.py` (B3_DB_PATH
temporário + reset dos caches em memória). Nenhum teste depende de rede, de
credencial do MCP nem de chave de LLM.
"""
from __future__ import annotations

import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import mcp_client, metering, opcoes_vigias, options_mcp_api


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
    d = tempfile.mkdtemp(prefix="b3_vigias_rotas_test_")
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


def _usado(main, uid):
    return metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp())


def _espiao_por_tool(monkeypatch, respostas: dict, cache: bool = False):
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


def _indexa(main, uid, nome, ticker="PETR4", criado_em="2026-09-13 09:00"):
    """Grava no índice o que `/setups/confirmar` gravaria, e devolve o nome no
    armazém. Usar o módulo direto (em vez de simular a gravação) mantém estes
    testes sobre a LISTAGEM, que é o que eles medem."""
    nome_servico = opcoes_vigias.nome_no_servico(uid, nome)
    opcoes_vigias.registrar(main._conn, uid, nome_do_usuario=nome,
                            nome_no_servico=nome_servico, ticker=ticker,
                            criado_em=criado_em)
    return nome_servico


def _registro(nome_servico, ticker="PETR4", status="ativo"):
    return {"setup": {"name": nome_servico, "ticker": ticker,
                      "description": "d", "conditions": [],
                      "logic": "AND", "consecutive_days": 2},
            "status": status, "backtest_na_criacao": {"disparos": 7}}


def _avaliacao(*pares):
    """`pares` = (nome_no_servico, armed, streak)."""
    return {"trading_date": "2026-09-12",
            "data_freshness": {"quotes": "em_dia", "quotes_age_hours": 12},
            "evaluations": [{"name": n, "ticker": "PETR4", "status": "avaliado",
                             "armed": a, "streak": s, "required_streak": 2,
                             "conditions": [{"summary": "close > sma21",
                                             "met": bool(a)}]}
                            for n, a, s in pares],
            "armed": [n for n, a, _s in pares if a], "note": ""}


# ═══════════════════════ 1. custo ZERO: GET /api/options/vigias ═══════════
def test_vigias_nao_toca_o_servico_de_opcoes_e_nao_gasta_cap(monkeypatch):
    """É a rota que a aba chama ao ABRIR. Se um dia alguém puxar a leitura do
    `mcp.semente.dev` para dentro dela, o teto compartilhado de 2.000/dia
    passa a ser gasto por ABRIR a tela, sem clique de ninguém (ADR-027 §3.3).

    A bomba vai na porta ÚNICA de saída para o serviço (`mcp_client.call_tool`)
    e não numa tool específica: assim o guardião continua valendo se a chamada
    de cima mudar de nome.
    """
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _indexa(main, uid, "IFR baixo", ticker="VALE3")

    def _bomba(*a, **k):
        raise AssertionError("/api/options/vigias chamou o serviço de opções")

    monkeypatch.setattr(mcp_client, "call_tool", _bomba)

    r = c.get("/api/options/vigias", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["fonte"] == "local"
    assert corpo["at"]
    assert [v["nome"] for v in corpo["vigias"]] == ["IFR baixo"]
    assert corpo["vigias"][0]["ticker"] == "VALE3"
    assert corpo["vigias"][0]["nomeNoServico"] == opcoes_vigias.nome_no_servico(uid, "IFR baixo")
    assert _usado(main, uid) == 0, "uma leitura local cobrou cota do serviço"
    # E nenhum estado: `armed` de ontem exibido como de hoje é afirmação sem
    # medição (princípio 4). Quem quer estado paga a consulta que o mede.
    assert "armed" not in corpo["vigias"][0]
    assert "streak" not in corpo["vigias"][0]


def test_vigias_anonimo_nao_ve_o_indice_de_ninguem(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    _indexa(main, p["user"]["id"], "IFR baixo")

    def _bomba(*a, **k):
        raise AssertionError("rota anônima chamou o serviço de opções")

    monkeypatch.setattr(mcp_client, "call_tool", _bomba)

    r = c.get("/api/options/vigias")
    assert r.status_code == 200, r.text
    assert r.json()["vigias"] == []


def test_vigias_de_um_usuario_nao_aparecem_para_o_outro(monkeypatch):
    c, main = _client(monkeypatch)
    dono = _registra(c)
    outro = _registra(c, email="outro@teste.com")
    _indexa(main, dono["user"]["id"], "só meu")

    r = c.get("/api/options/vigias", headers=_auth(outro["token"]))
    assert r.status_code == 200, r.text
    assert r.json()["vigias"] == [], "o índice de outra conta vazou"


# ═══════════════════ 2. custo 2, declarado: GET /mcp/setups ═══════════════
def test_indice_vazio_gasta_1_e_pula_evaluate(monkeypatch):
    """Consumir MENOS que o checado é sempre permitido; o contrário não. Sem
    vigia meu no armazém não há nada a avaliar, e a segunda chamada seria
    queimar o teto compartilhado por uma resposta que ninguém lê."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao_por_tool(monkeypatch, {"list_setups": {"setups": [], "count": 0}})

    r = c.get("/api/options/mcp/setups", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert r.json()["vigias"] == []
    assert _nomes(chamadas) == ["list_setups"]
    assert _usado(main, uid) == 1
    # Sem avaliação, o frescor NÃO se declara em dia (ADR-027, Decisão 8).
    assert r.json()["frescor"]["medido"] is False


@pytest.mark.parametrize("quantos", [2, 10])
def test_o_custo_e_2_com_dois_vigias_e_continua_2_com_dez(monkeypatch, quantos):
    """**O critério que decide se esta rota presta.** Uma listagem que virasse
    N chamadas esgotaria o teto compartilhado de 2.000/dia com uma carteira
    grande — e o teto é do SERVIDOR, não do usuário. `list_setups` e
    `evaluate_setups` devolvem a base inteira de uma vez; é isso que torna o
    custo fixo, e é isso que este teste trava."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]

    nomes = [_indexa(main, uid, f"vigia {i}") for i in range(quantos)]
    chamadas = _espiao_por_tool(monkeypatch, {
        "list_setups": {"setups": [_registro(n) for n in nomes], "count": quantos},
        "evaluate_setups": _avaliacao(*[(n, False, 0) for n in nomes])})

    r = c.get("/api/options/mcp/setups", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert len(r.json()["vigias"]) == quantos
    assert _nomes(chamadas) == ["list_setups", "evaluate_setups"]
    assert _usado(main, uid) == 2, \
        f"com {quantos} vigias a listagem custou {_usado(main, uid)} — virou N chamadas"


def test_item_do_indice_que_sumiu_do_armazem_volta_com_status_none_e_motivo(monkeypatch):
    """Sumir do armazém é FATO a mostrar, não item a apagar em silêncio. As
    duas verdades (índice × serviço) podem divergir, e a divergência é tratada
    como ESTADO exibido, nunca reconciliada às escondidas."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    vivo = _indexa(main, uid, "ainda existe")
    _indexa(main, uid, "apagado no serviço")

    _espiao_por_tool(monkeypatch, {
        "list_setups": {"setups": [_registro(vivo)], "count": 1},
        "evaluate_setups": _avaliacao((vivo, False, 1))})

    corpo = c.get("/api/options/mcp/setups", headers=_auth(p["token"])).json()
    por_nome = {v["name"]: v for v in corpo["vigias"]}
    assert set(por_nome) == {"ainda existe", "apagado no serviço"}
    sumido = por_nome["apagado no serviço"]
    assert sumido["status"] is None
    assert sumido["motivo"] == options_mcp_api.MOTIVO_FORA_DO_SERVICO
    assert sumido["armed"] is None and sumido["streak"] is None
    assert por_nome["ainda existe"]["status"] == "ativo"
    assert por_nome["ainda existe"]["motivo"] is None


def test_vigia_que_o_indice_nao_conhece_aparece_com_noIndice_false(monkeypatch):
    """Vigia criado ANTES de o índice existir é vigia real. Uma listagem que
    só enxerga o que nasceu depois dela não corrigiu o defeito desta fase,
    mudou de assunto. `criadoEm` vem `None` COM motivo — nunca a data de hoje
    (princípio 4 do CLAUDE.md)."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    orfao = opcoes_vigias.nome_no_servico(uid, "anterior ao índice")

    _espiao_por_tool(monkeypatch, {
        "list_setups": {"setups": [_registro(orfao, ticker="VALE3")], "count": 1},
        "evaluate_setups": _avaliacao((orfao, True, 3))})

    corpo = c.get("/api/options/mcp/setups", headers=_auth(p["token"])).json()
    assert len(corpo["vigias"]) == 1
    v = corpo["vigias"][0]
    assert v["name"] == "anterior ao índice"
    assert v["nomeNoServico"] == orfao
    assert v["noIndice"] is False
    assert v["ticker"] == "VALE3", "o ticker do serviço não foi aproveitado"
    assert v["criadoEm"] is None
    assert v["motivoCriadoEm"] == options_mcp_api.MOTIVO_SEM_DATA
    assert (v["armed"], v["streak"]) == (True, 3)


def test_a_ordenacao_poe_quem_disparou_na_frente(monkeypatch):
    """Decisão do executor (2026-09-13), herdada do protótipo aprovado
    (27-CONTEXT, "Em aberto" item 1): a ordem é "quem disparou primeiro", não
    alfabética. `armed` na frente; entre os não armados, o `streak` maior."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    # Inseridos nesta ordem; o índice fica mais-recente-primeiro.
    a = _indexa(main, uid, "aaa quieto")
    b = _indexa(main, uid, "bbb quase la")
    z = _indexa(main, uid, "zzz armado")

    _espiao_por_tool(monkeypatch, {
        "list_setups": {"setups": [_registro(n) for n in (a, b, z)], "count": 3},
        "evaluate_setups": _avaliacao((a, False, 0), (b, False, 2), (z, True, 5))})

    corpo = c.get("/api/options/mcp/setups", headers=_auth(p["token"])).json()
    assert [v["name"] for v in corpo["vigias"]] == \
        ["zzz armado", "bbb quase la", "aaa quieto"], \
        "a lista saiu alfabética (ou na ordem do serviço) em vez de por disparo"


def test_setup_de_outro_dono_e_setup_legado_nao_aparecem_na_listagem(monkeypatch):
    """As duas exclusões têm razões diferentes: `de outro dono` tem dono
    conhecido e não sou eu; `legado` não tem dono conhecido nenhum e pode nem
    ser do Boris+ (o armazém "é visto por todos os clientes do serviço",
    `rbac.py:29-34`). Decisão do Alex, 2026-09-13. A porta que REMOVE o legado
    continua aberta em `/desativar` — ver `test_opcoes_dsl.py`."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    meu = _indexa(main, uid, "só meu")
    alheio = opcoes_vigias.nome_no_servico("u-de-outra-conta", "vigia do outro")
    legado = "media longa + oscilador esticado"
    assert opcoes_vigias.e_legado(legado) is True
    assert opcoes_vigias.e_legado(alheio) is False, \
        "o registro alheio precisa ser PREFIXADO, senão o teste vira o do legado"

    _espiao_por_tool(monkeypatch, {
        "list_setups": {"setups": [_registro(meu), _registro(alheio),
                                   _registro(legado)], "count": 3},
        "evaluate_setups": _avaliacao((meu, False, 0), (alheio, True, 9),
                                      (legado, True, 9))})

    corpo = c.get("/api/options/mcp/setups", headers=_auth(p["token"])).json()
    nomes = [v["name"] for v in corpo["vigias"]]
    assert nomes == ["só meu"], f"vazou registro alheio ou legado: {nomes}"


def test_setups_sem_sessao_e_401_antes_do_cap_e_da_rede(monkeypatch):
    c, _ = _client(monkeypatch)
    chamadas = _espiao_por_tool(monkeypatch, {"list_setups": {"setups": []}})
    assert c.get("/api/options/mcp/setups").status_code == 401
    assert chamadas == [], "rota anônima chegou a tocar o serviço"
