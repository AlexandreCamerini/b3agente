"""aba-opcoes F5 — criar setup por descrição em português, OFFLINE.

O que este arquivo trava, em uma frase cada:
  - a recusa é do BACKEND: sem `opcoes.criar_setup` as três rotas de escrita
    respondem 403 e não tocam o serviço (o armazém de setups é compartilhado e
    sem dono — quem grava, grava para todos, ADR-027 Decisão 7);
  - sem a fiação de permissão a rota falha FECHADO (503), nunca 200;
  - PT → objeto → ensaio: nada é gravado sem o dry-run e o backtest à vista;
  - `description` é a da PESSOA, mesmo quando a IA a reescreve — é o campo que
    prova o que foi pedido;
  - os `problems` do serviço voltam item a item, na ordem, byte a byte;
  - resposta ilegível da IA vira 422 com o texto CRU rotulado, e nenhum
    `create_setup` — setup fabricado para "salvar" a resposta é o que não pode
    acontecer;
  - dado atrasado (ou não medido) BLOQUEIA criar, e não bloqueia desativar: a
    assimetria é deliberada;
  - criar e desativar deixam rastro em `admin_audit_log`, e a entidade está no
    mapa que o admin enxerga;
  - `tools/list` e `resources/read` são protocolo: NÃO consomem cap;
  - os dois 402 do gate de análise têm texto próprio da aba — nunca o copy de
    BYOK do `metering`;
  - `_system_compilador` é puro e não carrega nenhum indicador hardcodado
    (ENG-06): o vocabulário chega do schema vivo e do texto do serviço.

Esqueleto e isolamento herdados de `test_options_mcp_api.py` (B3_DB_PATH
temporário + reset dos caches em memória). Nenhum teste depende de rede, de
`MCP_CLIENT_SECRET` nem de chave de LLM: `mcp_client.call_tool`,
`list_tools`, `read_resource` e `llm._call_llm` são todos substituídos.
"""
from __future__ import annotations

import importlib
import os
import sys
import tempfile

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import llm, mcp_client, metering, options_mcp_api, rbac


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
    d = tempfile.mkdtemp(prefix="b3_opcoes_dsl_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email="dono@teste.com", senha="senhaboa123"):
    """A PRIMEIRA conta criada vira `role_admin` pelo bootstrap aditivo do
    ADR-013 (sem `B3_ADMIN_EMAILS`, a mais antiga é a admin) — é assim que os
    testes ganham a permissão `opcoes.criar_setup`. A segunda conta é o
    usuário comum, e é ela que prova o 403."""
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def _usado(main, uid):
    return metering.used(main._conn, uid, section="mcpUsage",
                         _dia=options_mcp_api._dia_sp())


# ------------------------------------------------------------- payloads ---
_FRESCOR_EM_DIA = {
    "trading_date": "2026-09-10",
    "classes": {"negociacao_b3": {"situacao": "em_dia", "idade_horas": 14}},
}
# Forma REAL medida no `/status` (ver `test_mcp_cap.py`): coleção como dict,
# com a idade dentro da classe.
_FRESCOR_ATRASADO = {
    "trading_date": "2026-09-05",
    "classes": {"negociacao_b3": {"situacao": "atrasada",
                                  "idade_horas": 53.5, "sla_horas": 30}},
}
_FRESCOR_SEM_A_CRITICA = {
    "trading_date": "2026-09-10",
    "classes": {"provento_b3": {"situacao": "em_dia"}},
}

_BACKTEST = {
    "periodo": {"de": "2024-09-10", "ate": "2026-09-10", "pregoes": 498},
    "pregoes_avaliaveis": 480,
    "pregoes_sem_indicador": 18,
    "disparos": 12,
    "datas_de_disparo": ["2025-03-14", "2025-07-02"],
    "disparos_por_100_pregoes_avaliaveis": 2.5,
    "retorno_apos_disparo": {
        "d+5": {"com_dado": 12, "retorno_medio_pct": 1.8, "retorno_mediano_pct": 1.1},
        "d+10": {"com_dado": 11, "retorno_medio_pct": 2.4, "retorno_mediano_pct": 0.9},
    },
}

# O schema VIVO do serviço. O nome do indicador (`rsi`) mora AQUI e em lugar
# nenhum do `server/app/` — é isso que o teste 15 prova.
_SCHEMA = {
    "type": "object",
    "required": ["name", "ticker", "description", "conditions"],
    "properties": {
        "name": {"type": "string"},
        "ticker": {"type": "string"},
        "description": {"type": "string"},
        "conditions": {
            "type": "array",
            "items": {"properties": {
                "indicator": {"enum": ["rsi", "media_movel", "volume_relativo"]},
                "operator": {"enum": ["<", ">", "cruza_acima"]},
            }},
        },
    },
}
_TEXTO_DO_RESOURCE = (
    "Um setup declara a condição que o vigia procura em cada pregão. "
    "O indicador rsi aceita uma janela; o operador compara com um valor fixo "
    "ou com outro indicador."
)

_DESCRICAO = "quando o rsi de 14 dias cair abaixo de 30 por dois pregões seguidos"

_SETUP_DA_IA = {
    "name": "rsi esticado para baixo",
    "ticker": "VALE3",
    "description": "REESCRITO PELA IA",
    "conditions": [{"indicator": "rsi", "window": 14, "operator": "<", "value": 30}],
    "consecutive_days": 2,
}


def _json_da_ia(setup=None) -> str:
    import json as _json
    return _json.dumps(_SETUP_DA_IA if setup is None else setup, ensure_ascii=False)


# --------------------------------------------------------------- espiões ---
def _espiao(monkeypatch, *, frescor=None, create=None, deactivate=None,
            cache: bool = False):
    """Substitui `mcp_client.call_tool` e registra `(nome, args)`. Valor
    `Exception` é levantado; qualquer outro vira `dados`."""
    frescor = _FRESCOR_EM_DIA if frescor is None else frescor
    chamadas: list = []

    def _resposta(nome, args):
        if nome == "check_data_freshness":
            return frescor
        if nome == options_mcp_api.TOOL_CREATE_SETUP:
            if create is not None:
                return create
            return {"status": "dry_run" if not (args or {}).get("confirm") else "ativo",
                    "name": (args or {}).get("setup", {}).get("name"),
                    "setup_as_interpreted": (args or {}).get("setup"),
                    "backtest": _BACKTEST,
                    "next_step": "confira a interpretação e confirme"}
        if nome == options_mcp_api.TOOL_DEACTIVATE_SETUP:
            if deactivate is not None:
                return deactivate
            return {"status": "inativo", "name": (args or {}).get("name")}
        return {}

    async def _falso(nome, args=None, *, read_timeout_seconds=None):
        chamadas.append((nome, args))
        v = _resposta(nome, args)
        if isinstance(v, Exception):
            raise v
        return mcp_client.ResultadoTool(v, cache)

    monkeypatch.setattr(mcp_client, "call_tool", _falso)
    return chamadas


class _Tool:
    def __init__(self, name, input_schema):
        self.name = name
        self.inputSchema = input_schema


class _Catalogo:
    def __init__(self, tools):
        self.tools = tools


class _Conteudo:
    def __init__(self, text):
        self.text = text


class _Recurso:
    def __init__(self, contents):
        self.contents = contents


# Sentinela: `schema=None` é um CASO do teste (o serviço não publicou o
# schema), não "use o default" — por isso o default não pode ser `None`.
_PADRAO = object()


def _material(monkeypatch, *, schema=_PADRAO, texto=_PADRAO):
    """`tools/list` e `resources/read` falsos, com os objetos do SDK (atributos,
    não dict) — é a forma real que o compilador tem de saber ler. Devolve a
    lista de chamadas, para provar que elas NÃO consomem cap."""
    schema = _SCHEMA if schema is _PADRAO else schema
    texto = _TEXTO_DO_RESOURCE if texto is _PADRAO else texto
    chamadas: list = []

    async def _list_tools():
        chamadas.append(("tools/list", None))
        tools = [_Tool("evaluate_setups", {"type": "object"})]
        if schema is not None:
            tools.append(_Tool(options_mcp_api.TOOL_CREATE_SETUP, schema))
        return mcp_client.ResultadoTool(_Catalogo(tools), False)

    async def _read_resource(uri):
        chamadas.append(("resources/read", uri))
        conteudo = [_Conteudo(texto)] if texto else []
        return mcp_client.ResultadoTool(_Recurso(conteudo), False)

    monkeypatch.setattr(mcp_client, "list_tools", _list_tools)
    monkeypatch.setattr(mcp_client, "read_resource", _read_resource)
    return chamadas


def _ia(monkeypatch, resposta=None, erro=None):
    """LLM FALSA. Registra `(system, user)` de cada chamada — é por eles que os
    testes do `system` montado em runtime afirmam."""
    prompts: list = []

    async def _falso(config, key, system, user, max_tokens):
        prompts.append((system, user))
        if erro is not None:
            raise erro
        return _json_da_ia() if resposta is None else resposta

    monkeypatch.setattr(llm, "_call_llm", _falso)
    return prompts


def _ia_proibida(monkeypatch):
    """Monkeypatch que FALHA o teste se a LLM for chamada."""
    async def _falso(config, key, system, user, max_tokens):
        raise AssertionError("esta rota chamou a LLM, e ela não deve chamar")

    monkeypatch.setattr(llm, "_call_llm", _falso)


def _compila(c, token, **extra):
    corpo = dict({"descricao": _DESCRICAO, "ticker": "PETR4"}, **extra)
    return c.post("/api/options/mcp/setups/compilar", headers=_auth(token), json=corpo)


def _nomes(chamadas):
    return [n for n, _a in chamadas]


# ═════════════════════════════════════════════════════ 1. permissão ═══════
def test_sem_a_permissao_as_tres_rotas_de_escrita_sao_403_e_nao_tocam_o_servico(monkeypatch):
    """O CORAÇÃO do aceite desta fase: a recusa é do BACKEND, não de um botão
    escondido. O armazém de setups do serviço é ÚNICO e sem campo de dono
    (ADR-027, Decisão 7) — um setup criado por qualquer conta é visto por
    todos os clientes, e por isso escrever é permissão nomeada."""
    c, _ = _client(monkeypatch)
    _registra(c)                                    # 1ª conta = admin (bootstrap)
    comum = _registra(c, email="comum@teste.com")   # 2ª conta = usuário comum
    chamadas = _espiao(monkeypatch)
    _material(monkeypatch)
    _ia_proibida(monkeypatch)

    r1 = _compila(c, comum["token"])
    r2 = c.post("/api/options/mcp/setups/confirmar", headers=_auth(comum["token"]),
                json={"setup": dict(_SETUP_DA_IA)})
    r3 = c.post("/api/options/mcp/setups/rsi/desativar", headers=_auth(comum["token"]))

    for r in (r1, r2, r3):
        assert r.status_code == 403, r.text
        assert "opcoes.criar_setup" in r.text, (
            "o 403 não nomeia a permissão — a pessoa fica sem saber o que pedir")
    assert chamadas == [], "rota sem permissão chegou a tocar o serviço"


def test_anonimo_e_401_nas_tres_rotas_de_escrita(monkeypatch):
    c, _ = _client(monkeypatch)
    chamadas = _espiao(monkeypatch)
    _ia_proibida(monkeypatch)

    assert c.post("/api/options/mcp/setups/compilar",
                  json={"descricao": _DESCRICAO, "ticker": "PETR4"}).status_code == 401
    assert c.post("/api/options/mcp/setups/confirmar",
                  json={"setup": dict(_SETUP_DA_IA)}).status_code == 401
    assert c.post("/api/options/mcp/setups/rsi/desativar").status_code == 401
    assert chamadas == [], "rota anônima chegou a tocar o serviço"


def test_sem_a_fiacao_de_permissao_a_rota_de_escrita_falha_fechado(monkeypatch):
    """Falhar ABERTO numa rota de escrita é pior que não ter a rota: sem a
    injeção de `require_permission`, o 503 é a única resposta honesta."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    monkeypatch.setattr(options_mcp_api, "_require_permission", None)

    r = _compila(c, p["token"])
    assert r.status_code == 503, r.text
    assert r.json()["detail"]["code"] == "mcp_nao_configurado"
    assert chamadas == []


def test_a_entidade_de_auditoria_esta_no_mapa_que_o_admin_enxerga():
    """Sem esta linha em `ENTIDADES_POR_PERMISSAO`, `audit.record` gravaria e
    `entidades_visiveis` filtraria o evento para fora de TODO mundo — a
    auditoria existiria e ninguém a veria (ADR-013)."""
    assert options_mcp_api.ENTIDADE_AUDITORIA in \
        rbac.ENTIDADES_POR_PERMISSAO[options_mcp_api.PERM_CRIAR_SETUP]
    assert options_mcp_api.PERM_CRIAR_SETUP in rbac.GRUPOS["opcoes"]


# ═══════════════════════════════════════════════════ 2. PT → DSL → ensaio ═
def test_compilar_devolve_dry_run_com_o_backtest_verbatim(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    material = _material(monkeypatch)
    prompts = _ia(monkeypatch)

    r = _compila(c, p["token"])
    assert r.status_code == 200, r.text
    corpo = r.json()

    assert corpo["status"] == "dry_run", "gravou sem ensaio"
    assert corpo["backtest"] == _BACKTEST, "o backtest foi mexido no caminho"
    assert corpo["backtest"]["disparos"] == 12
    assert corpo["backtest"]["disparos_por_100_pregoes_avaliaveis"] == 2.5
    assert corpo["backtest"]["retorno_apos_disparo"]["d+5"]["retorno_medio_pct"] == 1.8
    assert corpo["backtest"]["retorno_apos_disparo"]["d+10"]["com_dado"] == 11
    assert corpo["proximoPasso"] == "confira a interpretação e confirme"
    assert corpo["fonte"] == "mcp.semente.dev" and corpo["at"].endswith(" BRT")
    assert corpo["pregao"] == "2026-09-10"
    assert corpo["frescor"]["bloqueia"] is False and corpo["frescor"]["medido"] is True

    # `confirm=false` — o ensaio é o desenho, não uma opção do chamador.
    args = dict(chamadas)[options_mcp_api.TOOL_CREATE_SETUP]
    assert args["confirm"] is False

    # O `system` foi montado do material VIVO, não de constante do módulo.
    system, usuario = prompts[0]
    assert _TEXTO_DO_RESOURCE in system
    assert '"rsi"' in system, "o inputSchema não entrou no system"
    assert _DESCRICAO in usuario and "PETR4" in usuario
    assert _nomes(material) == ["tools/list", "resources/read"]


def test_a_description_gravada_e_a_original_e_nao_a_parafrase_da_ia(monkeypatch):
    """A IA devolveu `description: "REESCRITO PELA IA"` e `ticker: "VALE3"`. O
    que chega ao serviço é o que a PESSOA escreveu e o ativo que ela escolheu
    — é esse campo que prova depois o que foi pedido, num armazém sem dono."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _material(monkeypatch)
    _ia(monkeypatch)

    r = _compila(c, p["token"])
    assert r.status_code == 200, r.text

    enviado = dict(chamadas)[options_mcp_api.TOOL_CREATE_SETUP]["setup"]
    assert enviado["description"] == _DESCRICAO
    assert enviado["ticker"] == "PETR4"
    assert _SETUP_DA_IA["description"] not in str(enviado), \
        "a paráfrase da IA sobreviveu em algum campo do setup"
    assert r.json()["descricao"] == _DESCRICAO
    # o resto do objeto é da IA, e continua intacto
    assert enviado["conditions"] == _SETUP_DA_IA["conditions"]
    assert enviado["consecutive_days"] == 2


def test_problems_do_servico_voltam_item_a_item_e_na_ordem(monkeypatch):
    """Reescrever os `problems` tiraria a única informação acionável que a
    pessoa tem — quem valida a semântica é o serviço, não esta camada."""
    problemas = [
        "conditions[0].operator: 'maior_ou_menor' não é um operador aceito",
        "conditions[0].window: 14 é maior que a janela máxima do indicador",
        "valid_until: data no passado",
    ]
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, create=mcp_client.McpErroDeTool(
        "o setup não pôde ser criado", bruto={"error": "o setup não pôde ser criado",
                                              "problems": list(problemas)}))
    _material(monkeypatch)
    _ia(monkeypatch)

    r = _compila(c, p["token"])
    assert r.status_code == 422, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "setup_invalido"
    assert detalhe["message"] == "o setup não pôde ser criado"
    assert detalhe["problems"] == problemas, "os problemas mudaram de ordem ou de texto"


def test_resposta_ilegivel_da_ia_vira_422_com_o_cru_e_nao_chama_create_setup(monkeypatch):
    """Fabricar um setup para "salvar" uma resposta que não é setup seria
    gravar uma coisa que ninguém escreveu."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _material(monkeypatch)
    _ia(monkeypatch, resposta="Claro! Posso ajudar com isso, mas preciso de mais dados.")

    r = _compila(c, p["token"])
    assert r.status_code == 422, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "compilacao_invalida"
    assert detalhe["cru"] == "Claro! Posso ajudar com isso, mas preciso de mais dados."
    assert options_mcp_api.TOOL_CREATE_SETUP not in _nomes(chamadas)


def test_forma_incompleta_vira_422_listando_os_campos_e_nao_chama_create_setup(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _material(monkeypatch)
    _ia(monkeypatch, resposta=_json_da_ia({"name": "x"}))

    r = _compila(c, p["token"])
    assert r.status_code == 422, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "forma_invalida"
    assert sorted(detalhe["faltando"]) == ["conditions", "description", "ticker"]
    assert options_mcp_api.TOOL_CREATE_SETUP not in _nomes(chamadas)


def test_conditions_vazia_e_forma_invalida(monkeypatch):
    """Setup sem condição nenhuma dispararia todo pregão — e o serviço o
    recusaria depois de a viagem já ter sido paga."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _material(monkeypatch)
    _ia(monkeypatch, resposta=_json_da_ia(dict(_SETUP_DA_IA, conditions=[])))

    r = _compila(c, p["token"])
    assert r.status_code == 422
    assert r.json()["detail"]["faltando"] == ["conditions"]
    assert options_mcp_api.TOOL_CREATE_SETUP not in _nomes(chamadas)


def test_descricao_vazia_e_422_antes_de_qualquer_rede(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _material(monkeypatch)
    _ia_proibida(monkeypatch)

    r = _compila(c, p["token"], descricao="   ")
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "descricao_ausente"
    assert chamadas == []

    r = _compila(c, p["token"], ticker="")
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "ticker_ausente"
    assert chamadas == []


def test_erro_de_chave_ou_modelo_vira_400_preservando_code_e_action(monkeypatch):
    """`LLMUserError` já vem sanitizada por `llm.public_error` (nenhuma chave
    em mensagem) — o que a rota preserva é o que o front sabe renderizar."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _material(monkeypatch)
    _ia(monkeypatch, erro=llm.LLMUserError(
        "Nenhum modelo de IA configurado.",
        action="Informe um modelo em Configurações → Modelo de IA.",
        code="missing_model"))

    r = _compila(c, p["token"])
    assert r.status_code == 400, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "missing_model"
    assert detalhe["action"].startswith("Informe um modelo")
    assert options_mcp_api.TOOL_CREATE_SETUP not in _nomes(chamadas)


def test_material_ausente_vira_422_em_vez_de_compilar_de_memoria(monkeypatch):
    """Sem o schema vivo não há compilação: copiar o vocabulário para dentro
    do Boris é exatamente o que o ENG-06 proíbe, e compilar sem ele seria
    compilar de memória."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _material(monkeypatch, schema=None)
    _ia_proibida(monkeypatch)

    r = _compila(c, p["token"])
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "mcp_erro_de_tool"
    assert options_mcp_api.TOOL_CREATE_SETUP not in _nomes(chamadas)


# ════════════════════════════════════════════════════════ 3. frescor ══════
def test_dado_atrasado_bloqueia_criar_com_a_idade_real(monkeypatch):
    """ADR-027, Decisão 8: criar setup sobre dado que ninguém mediu (ou que
    está velho) é fabricar confiança. E o bloqueio vem ANTES da LLM."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch, frescor=_FRESCOR_ATRASADO)
    _material(monkeypatch)
    _ia_proibida(monkeypatch)

    r = _compila(c, p["token"])
    assert r.status_code == 409, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "dado_atrasado"
    assert detalhe["motivo"] == "atrasado"
    assert detalhe["idadeHoras"] == 53.5, "a idade MEDIDA sumiu do 409"
    assert detalhe["slaHoras"] == 30
    assert options_mcp_api.TOOL_CREATE_SETUP not in _nomes(chamadas)


def test_classe_critica_ausente_bloqueia_criar_como_nao_medido(monkeypatch):
    """"Não medido" NUNCA pode passar por "em dia" — e os dois 409 se
    distinguem por `motivo`, não pelo texto."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch, frescor=_FRESCOR_SEM_A_CRITICA)
    _material(monkeypatch)
    _ia_proibida(monkeypatch)

    r = _compila(c, p["token"])
    assert r.status_code == 409, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "dado_atrasado"
    assert detalhe["motivo"] == "nao_medido"
    assert detalhe["idadeHoras"] is None, "idade inventada para um dado não medido"
    assert options_mcp_api.TOOL_CREATE_SETUP not in _nomes(chamadas)


def test_desativar_nao_e_bloqueado_por_dado_atrasado(monkeypatch):
    """A assimetria é deliberada: criar é começar a AFIRMAR, desativar é
    PARAR. Travar o desligamento por dado velho deixaria um setup errado
    vigiando porque a carga do dia falhou."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch, frescor=_FRESCOR_ATRASADO)
    _ia_proibida(monkeypatch)

    r = c.post("/api/options/mcp/setups/rsi%20esticado/desativar",
               headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "inativo"
    assert r.json()["name"] == "rsi esticado"
    # E não gastou chamada de frescor: a rota nem mede.
    assert _nomes(chamadas) == [options_mcp_api.TOOL_DEACTIVATE_SETUP]
    assert _usado(main, p["user"]["id"]) == 1


def test_setup_desconhecido_no_desativar_devolve_known_setups_verbatim(monkeypatch):
    conhecidos = ["rsi esticado", "rompimento de topo"]
    c, _ = _client(monkeypatch)
    p = _registra(c)
    _espiao(monkeypatch, deactivate=mcp_client.McpErroDeTool(
        "setup 'nada' não existe",
        bruto={"error": "setup 'nada' não existe", "known_setups": list(conhecidos)}))

    r = c.post("/api/options/mcp/setups/nada/desativar", headers=_auth(p["token"]))
    assert r.status_code == 422, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == "setup_desconhecido"
    assert detalhe["known_setups"] == conhecidos


# ═══════════════════════════════════════════ 4. confirmar e auditoria ═════
def test_confirmar_nao_chama_llm_e_grava(monkeypatch):
    """O que se grava é o que a pessoa VIU. Recompilar aqui poderia gravar
    outra coisa — e ela teria aprovado a primeira."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _ia_proibida(monkeypatch)

    visto = dict(_SETUP_DA_IA, description=_DESCRICAO, ticker="PETR4")
    r = c.post("/api/options/mcp/setups/confirmar", headers=_auth(p["token"]),
               json={"setup": visto})
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["status"] == "ativo"
    assert corpo["name"] == _SETUP_DA_IA["name"]
    assert corpo["backtest"] == _BACKTEST

    args = dict(chamadas)[options_mcp_api.TOOL_CREATE_SETUP]
    assert args["confirm"] is True
    assert args["setup"] == visto, "o setup foi mexido entre o ensaio e a gravação"


def test_confirmar_sem_setup_ou_com_forma_torta_e_422_antes_da_rede(monkeypatch):
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _ia_proibida(monkeypatch)

    r = c.post("/api/options/mcp/setups/confirmar", headers=_auth(p["token"]), json={})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "setup_ausente"

    r = c.post("/api/options/mcp/setups/confirmar", headers=_auth(p["token"]),
               json={"setup": {"name": "x", "ticker": "PETR4"}})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "forma_invalida"
    assert chamadas == []


def test_auditoria_registra_a_criacao_e_a_desativacao(monkeypatch):
    """Num armazém sem dono, quem gravou é a única resposta possível para "de
    onde veio este setup" (ADR-027, Decisão 7)."""
    from app import audit

    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao(monkeypatch)
    _ia_proibida(monkeypatch)

    visto = dict(_SETUP_DA_IA, description=_DESCRICAO, ticker="PETR4")
    assert c.post("/api/options/mcp/setups/confirmar", headers=_auth(p["token"]),
                  json={"setup": visto}).status_code == 200
    assert c.post(f"/api/options/mcp/setups/{_SETUP_DA_IA['name']}/desativar",
                  headers=_auth(p["token"])).status_code == 200

    eventos = [e for e in audit.recent(main._conn)
               if e["entity"] == options_mcp_api.ENTIDADE_AUDITORIA]
    assert len(eventos) == 2, eventos
    por_novo = {e["newValue"]: e for e in eventos}
    assert por_novo["ativo"]["entityId"] == _SETUP_DA_IA["name"]
    assert por_novo["ativo"]["oldValue"] is None
    assert por_novo["ativo"]["actorUserId"] == uid
    assert por_novo["inativo"]["oldValue"] == "ativo"
    assert por_novo["inativo"]["entityId"] == _SETUP_DA_IA["name"]


# ═══════════════════════════════════════════════════ 5. os três tetos ═════
def test_cota_da_aba_cheia_recusa_antes_de_qualquer_rede(monkeypatch):
    """`mcp_cota` é o teto de CHAMADAS da aba — e o texto dele não fala de
    BYOK, porque chave nenhuma resolve um teto de chamadas."""
    monkeypatch.setenv("B3_MCP_COTA_USUARIO_DIA", "1")
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _material(monkeypatch)
    _ia_proibida(monkeypatch)

    r = _compila(c, p["token"])
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["code"] == "mcp_cota"
    assert chamadas == []


_COPY_DE_BYOK = ("byok", "chave", "modelo de ia", "configurações →", "configuracoes →")


@pytest.mark.parametrize("motivo,esperado", [
    ("Voce atingiu o limite de 30 analises/mes do plano free.", "plano_analises"),
    ("Você atingiu o limite diário de 20 análises com a IA do app. Use sua "
     "própria chave (BYOK) em Perfil → Conta & preferências para análises "
     "ilimitadas, ou volte amanhã.", "ia_gerenciada"),
])
def test_gate_de_analise_nega_com_texto_proprio_da_aba(monkeypatch, motivo, esperado):
    """São DOIS tetos distintos e eles não significam a mesma coisa. O copy do
    `metering` mandaria a pessoa configurar uma chave que não resolve nem o
    limite mensal do plano, nem o teto de chamadas da aba (§3.2 do PLANO)."""
    c, _ = _client(monkeypatch)
    p = _registra(c)
    chamadas = _espiao(monkeypatch)
    _material(monkeypatch)
    _ia_proibida(monkeypatch)

    def _nega(scope, config):
        raise HTTPException(402, motivo)

    monkeypatch.setattr(options_mcp_api, "_gate_analise", _nega)

    r = _compila(c, p["token"])
    assert r.status_code == 402, r.text
    detalhe = r.json()["detail"]
    assert detalhe["code"] == esperado
    baixo = detalhe["message"].lower()
    for marca in _COPY_DE_BYOK:
        assert marca not in baixo, f"o copy de BYOK vazou para a aba Opções: {marca!r}"
    assert options_mcp_api.TOOL_CREATE_SETUP not in _nomes(chamadas)


def test_marca_do_gate_mensal_ainda_existe_em_plan():
    """O gate de análise é ponto ÚNICO e devolve TEXTO, não código: separar
    `plano_analises` de `ia_gerenciada` custa esta marca. Se `plan.py` mudar a
    frase, este teste falha ALTO — em vez de a rota passar a chamar de
    "ia_gerenciada" um limite mensal de plano."""
    from app import plan

    ok, motivo = plan.can_analyze(
        999, plan={"id": "free", "max_analyses_per_month": 30})
    assert ok is False
    assert options_mcp_api._MARCA_DO_GATE_MENSAL in motivo


def test_tools_list_e_resource_nao_consomem_cap(monkeypatch):
    """`tools/list` e `resources/read` são PROTOCOLO: de graça no teto do
    serviço e, por isso, fora do cap por usuário. Uma compilação inteira gasta
    2 — o frescor e o `create_setup` — nunca 4."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    chamadas = _espiao(monkeypatch)
    material = _material(monkeypatch)
    _ia(monkeypatch)

    antes = _usado(main, uid)
    assert _compila(c, p["token"]).status_code == 200
    depois = _usado(main, uid)

    assert len(material) == 2, "o material do compilador não foi buscado"
    assert depois - antes == 2, (
        f"a compilação consumiu {depois - antes} do cap — só o "
        f"`check_data_freshness` e o `create_setup` podem cobrar")
    assert _nomes(chamadas) == ["check_data_freshness",
                                options_mcp_api.TOOL_CREATE_SETUP]


def test_reserva_nao_consumida_volta_quando_o_servico_recusa(monkeypatch):
    """Classe do achado A-07: reservar 2 e consumir 0 sem devolver produziria
    um "cota esgotada" falso algumas chamadas depois."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    _espiao(monkeypatch, frescor=_FRESCOR_ATRASADO)
    _material(monkeypatch)
    _ia_proibida(monkeypatch)

    assert _compila(c, p["token"]).status_code == 409
    assert _usado(main, uid) == 1, "o frescor medido é a única cobrança do 409"
    assert metering.reservado(main._conn, uid, section="mcpUsage",
                              _dia=options_mcp_api._dia_sp()) == 0, \
        "a reserva não consumida ficou presa até expirar"


# ═══════════════════════════════════════════════ 6. ENG-06 (o system) ═════
def test_system_do_compilador_e_puro_e_nao_carrega_indicador_hardcodado():
    """O vocabulário (indicador, operador, padrão) chega do schema VIVO e do
    texto do serviço. Com os dois vazios, `rsi` não aparece em lugar nenhum —
    é isso que prova que nada foi copiado para dentro do Boris (ENG-06)."""
    com_material = options_mcp_api._system_compilador(_SCHEMA, _TEXTO_DO_RESOURCE)
    assert _TEXTO_DO_RESOURCE in com_material
    assert '"rsi"' in com_material and "volume_relativo" in com_material
    assert "cruza_acima" in com_material

    vazio = options_mcp_api._system_compilador({}, "")
    for termo in ("rsi", "volume_relativo", "cruza_acima", "media_movel"):
        assert termo not in vazio.lower(), (
            f"{termo!r} está hardcodado no cabeçalho do compilador — o "
            f"vocabulário tem de vir do serviço, senão envelhece em silêncio")
    assert options_mcp_api.SYSTEM_COMPILADOR_CABECALHO in vazio
