"""25-04 (Fase 3 do `.planning/phases/25-planos-comerciais/25-CONTEXT.md`) —
os gates passam a LER o catálogo de planos, e este arquivo trava o que a
mudança pode estragar.

O 25-03 criou o catálogo (`plan.LIMITES_DE_PLANO`, `plan.limites_do_plano`) e
ninguém o lia. Aqui os cinco pontos de controle passam a resolver pela cadeia

    limite do PLANO (kv por plano → env por plano)
      → override GLOBAL de hoje (admin_config / kv, que o portal já escreve)
        → env global
          → default

e a conciliação mora no CHAMADOR (`main._limite_do_plano`, injetado em
`options_mcp_api`), nunca em `plan.py` — que não pode importar `managed` nem
`options_mcp_api` sem ciclo.

Os seis blocos, na ordem de perigo:

 1. **SEM CONFIGURAÇÃO, NADA MUDA.** É o bloco que impede esta fase de virar
    mudança de política silenciosa. Os cinco limites, com kv vazio, valem
    exatamente o que valiam ontem.
 2. Com limite POR PLANO configurado, é ele que barra — inclusive contra o
    override GLOBAL que o portal já escreve hoje.
 3. **Tetos FÍSICOS e rate/min intocados.** Eles protegem o serviço externo
    compartilhado por toda a base; vendê-los por plano não cria capacidade,
    só transfere a recusa para outro usuário.
 4. **D3 (Alex, 2026-09-12):** o `owner` pula o cap COMERCIAL e continua
    sujeito ao FÍSICO.
 5. A recusa é classificada por CÓDIGO, não pela frase da mensagem.
 6. Fail-closed: escopo anônimo ou falha ao ler o usuário cai no plano MENOS
    privilegiado.

RED medido antes da correção — ver `25-04-SUMMARY.md` para a saída e para
quais casos passavam nos DOIS estados (não-regressão, por desenho).
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import options_mcp_api, plan

# ---------------------------------------------------------------------------
# Os números de HOJE, escritos à mão (mesma disciplina do 25-03): um guardião
# que lê o mesmo dicionário que testa acompanha qualquer mudança em silêncio.
# ---------------------------------------------------------------------------
HOJE_FREE = {
    "max_watchlist": 10,
    "max_analyses_per_month": 30,
    "ia_gerenciada_dia": 20,
    "opcoes_chamadas_dia": 60,
    "assistente_brl_dia": 1.0,
}

# Os tetos que NÃO variam por plano (ADR-010, decisão 2).
RATE_IA_GERENCIADA = 6       # managed.rate_per_min() — freio contra flood
RATE_OPCOES = 20             # options_mcp_api.RATE_MIN_DEFAULT
COTA_GLOBAL_OPCOES = 1800    # options_mcp_api.COTA_GLOBAL_DIA_DEFAULT
TETO_SERVICO_DIA = 2000      # contrato do serviço MCP, base inteira somada

OWNER_EMAIL = "dono@teste.com"


def _envs_do_catalogo():
    return {plan.env_key(p, chave)
            for p in plan.PLANOS_POR_ID
            for chave, *_resto in plan.LIMITES_DE_PLANO}


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    """Isolamento igual ao de `test_fase3_gate_plano.py` (reimport de
    `app.main` por caso, caches de módulo zerados), MAIS o `delenv` das envs
    do catálogo — inclusive as três compartilhadas, que podem estar no
    ambiente de quem roda a suíte e fariam o bloco 1 medir outra coisa."""
    from app import agent, brapi_budget, managed
    original = sys.modules.get("app.main")
    conn_plan = plan._conn
    for env in _envs_do_catalogo():
        monkeypatch.delenv(env, raising=False)
    monkeypatch.delenv("B3_MANAGED_GLOBAL_DAILY_CAP", raising=False)
    monkeypatch.delenv("B3_MCP_RATE_MIN", raising=False)
    monkeypatch.delenv("B3_MCP_COTA_GLOBAL_DIA", raising=False)
    monkeypatch.delenv("B3_MANAGED_RATE_PER_MIN", raising=False)
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    options_mcp_api.reset_limites_cache()
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    options_mcp_api.reset_limites_cache()
    plan.configure_db(conn_plan)
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, env=None):
    d = tempfile.mkdtemp(prefix="b3_gates_por_plano_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    for k, v in (env or {}).items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email="conta@teste.com", senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def _ia_gerenciada_ligada(monkeypatch, main):
    """Sem BYOK e com a IA gerenciada 'habilitada' — só assim
    `_ai_apply_managed` chega a `metering.check`, que é onde a cota diária
    efetiva aparece."""
    monkeypatch.setattr(main.llm, "resolve_key", lambda _cfg: "")
    monkeypatch.setattr(main.managed, "managed_config",
                        lambda: {"provider": "openai", "model": "gpt-4o-mini"})


def _espiao_metering(monkeypatch, main, resposta=(True, None)):
    """Captura os kwargs de CADA `metering.check`. É o único jeito de provar
    de onde veio o número que barra: ler o código não prova, e o valor não
    aparece na resposta HTTP."""
    chamadas = []

    def _check(_conn, _uid, **kw):
        chamadas.append(kw)
        return resposta

    monkeypatch.setattr(main.metering, "check", _check)
    return chamadas


def _mes_usado(monkeypatch, main, n):
    monkeypatch.setattr(main.metering, "month_used", lambda *_a, **_k: n)


# ===========================================================================
# 1) SEM CONFIGURAÇÃO, NADA MUDA — os cinco limites
# ===========================================================================
def test_sem_plano_configurado_o_gate_mensal_barra_no_numero_de_hoje(monkeypatch):
    """`max_analyses_per_month` (1/5). A frase é a de `plan.py`, byte a byte —
    ela é o que o usuário lê na tela."""
    c, main = _client(monkeypatch)
    _ia_gerenciada_ligada(monkeypatch, main)
    _espiao_metering(monkeypatch, main)
    p = _registra(c)
    uid = p["user"]["id"]

    _mes_usado(monkeypatch, main, HOJE_FREE["max_analyses_per_month"] - 1)
    main._gate_analise(uid, {})     # 29/30 passa

    _mes_usado(monkeypatch, main, HOJE_FREE["max_analyses_per_month"])
    with pytest.raises(HTTPException) as e:
        main._gate_analise(uid, {})
    assert e.value.status_code == 402
    assert str(e.value.detail) == (
        "Voce atingiu o limite de 30 analises/mes do plano free.")


def test_sem_plano_configurado_a_watchlist_tem_o_limite_de_hoje(monkeypatch):
    """`max_watchlist` (2/5) — pela rota que o iOS lê, não pelo dict."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    r = c.get("/api/watchlist/quota", headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert r.json()["limit"] == HOJE_FREE["max_watchlist"]
    assert r.json()["planId"] == "free"


def test_sem_plano_configurado_a_cota_da_ia_gerenciada_e_a_de_hoje(monkeypatch):
    """`ia_gerenciada_dia` (3/5) — o número que chega ao `metering.check`."""
    c, main = _client(monkeypatch)
    _ia_gerenciada_ligada(monkeypatch, main)
    chamadas = _espiao_metering(monkeypatch, main)
    _mes_usado(monkeypatch, main, 0)
    p = _registra(c)

    main._gate_analise(p["user"]["id"], {})
    assert chamadas[-1]["quota"] == HOJE_FREE["ia_gerenciada_dia"]


def test_sem_plano_configurado_a_cota_da_aba_opcoes_e_a_de_hoje(monkeypatch):
    """`opcoes_chamadas_dia` (4/5) — o cap por usuário do serviço MCP."""
    c, main = _client(monkeypatch)
    chamadas = _espiao_metering(monkeypatch, main)
    p = _registra(c)

    options_mcp_api._cap_check(p["user"]["id"], 1)
    assert chamadas[-1]["quota"] == HOJE_FREE["opcoes_chamadas_dia"]


def test_sem_plano_configurado_o_teto_do_assistente_e_o_de_hoje(monkeypatch):
    """`assistente_brl_dia` (5/5) — o teto em R$ que a rota entrega ao
    assistente."""
    c, main = _client(monkeypatch)
    p = _registra(c)
    visto = _espiao_assistente(monkeypatch, main)

    r = c.post("/api/assistente",
               json={"pergunta": "por que este ativo caiu tanto hoje",
                     "tela": "ativo", "snapshot": {"ticker": "PETR4"}},
               headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert visto["teto"] == HOJE_FREE["assistente_brl_dia"]


def _espiao_assistente(monkeypatch, main):
    """Captura o teto que a ROTA resolve e entrega a `assistente.responder`.
    A KB é curto-circuitada (`resolver` → None) porque o caminho barato não
    passa por teto nenhum — é o caminho CARO que este teste mede."""
    from app import assistente as assist, kb
    visto = {}

    async def _responder(_conn, _config, _scope, _modo, _tela, _snapshot,
                         _pergunta, byok=False, historico=None, teto=None):
        visto["teto"] = teto
        visto["byok"] = byok
        return {"texto": "ok", "prefixoCacheavel": False, "restanteHojeBRL": None}

    monkeypatch.setattr(kb, "resolver", lambda *_a, **_k: None)
    monkeypatch.setattr(assist, "responder", _responder)
    return visto


# ===========================================================================
# 2) COM LIMITE POR PLANO, É ELE QUE BARRA
# ===========================================================================
def test_limite_mensal_do_plano_vence_o_default(monkeypatch):
    c, main = _client(monkeypatch)
    _ia_gerenciada_ligada(monkeypatch, main)
    _espiao_metering(monkeypatch, main)
    p = _registra(c)
    plan.set_limite_do_plano("free", "max_analyses_per_month", 2)

    _mes_usado(monkeypatch, main, 1)
    main._gate_analise(p["user"]["id"], {})

    _mes_usado(monkeypatch, main, 2)
    with pytest.raises(HTTPException) as e:
        main._gate_analise(p["user"]["id"], {})
    assert str(e.value.detail) == (
        "Voce atingiu o limite de 2 analises/mes do plano free.")


def test_limite_de_watchlist_do_plano_vence_o_default(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    plan.set_limite_do_plano("free", "max_watchlist", 3)

    r = c.get("/api/watchlist/quota", headers=_auth(p["token"]))
    assert r.json()["limit"] == 3


def test_cota_da_ia_gerenciada_do_plano_vence_o_override_global(monkeypatch):
    """A conciliação em UM caso: o painel admin já escreve `llmDailyQuota`
    (override GLOBAL). Configurado o plano, é o plano que manda; sem ele, o
    global continua valendo exatamente como hoje."""
    c, main = _client(monkeypatch)
    _ia_gerenciada_ligada(monkeypatch, main)
    chamadas = _espiao_metering(monkeypatch, main)
    _mes_usado(monkeypatch, main, 0)
    p = _registra(c)
    uid = p["user"]["id"]

    main.db.admin_config_set(main._conn, "llmDailyQuota", 9)
    main.managed.reset_cache()
    main._gate_analise(uid, {})
    assert chamadas[-1]["quota"] == 9, "sem plano configurado o override global manda"

    plan.set_limite_do_plano("free", "ia_gerenciada_dia", 7)
    main._gate_analise(uid, {})
    assert chamadas[-1]["quota"] == 7, "com plano configurado, o plano manda"


def test_cota_da_aba_opcoes_do_plano_vence_o_override_global(monkeypatch):
    c, main = _client(monkeypatch)
    chamadas = _espiao_metering(monkeypatch, main)
    p = _registra(c)
    uid = p["user"]["id"]

    options_mcp_api.set_cota_usuario_dia(9)
    options_mcp_api._cap_check(uid, 1)
    assert chamadas[-1]["quota"] == 9, "sem plano configurado o override global manda"

    plan.set_limite_do_plano("free", "opcoes_chamadas_dia", 5)
    options_mcp_api._cap_check(uid, 1)
    assert chamadas[-1]["quota"] == 5, "com plano configurado, o plano manda"


def test_teto_do_assistente_do_plano_vence_o_default(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    visto = _espiao_assistente(monkeypatch, main)
    plan.set_limite_do_plano("free", "assistente_brl_dia", 2.5)

    r = c.post("/api/assistente",
               json={"pergunta": "por que este ativo caiu tanto hoje",
                     "tela": "ativo", "snapshot": {"ticker": "PETR4"}},
               headers=_auth(p["token"]))
    assert r.status_code == 200, r.text
    assert visto["teto"] == 2.5


def test_plano_pro_e_free_nao_disputam_o_mesmo_limite(monkeypatch):
    """A chave de kv carrega o id do plano — configurar o free não pode mexer
    na conta pro, que é o defeito que dividiria a base inteira num número só."""
    c, main = _client(monkeypatch)
    _ia_gerenciada_ligada(monkeypatch, main)
    chamadas = _espiao_metering(monkeypatch, main)
    _mes_usado(monkeypatch, main, 0)
    p = _registra(c)
    uid = p["user"]["id"]
    plan.set_limite_do_plano("free", "ia_gerenciada_dia", 1)
    plan.set_limite_do_plano("pro", "ia_gerenciada_dia", 99)

    main._gate_analise(uid, {})
    assert chamadas[-1]["quota"] == 1

    main.db.set_user_plan(main._conn, uid, "pro")
    main._gate_analise(uid, {})
    assert chamadas[-1]["quota"] == 99


# ===========================================================================
# 3) TETOS FÍSICOS E RATE/MIN INTOCADOS
# ===========================================================================
def test_teto_global_da_ia_e_o_rate_por_minuto_nao_mudam_com_plano_nenhum(monkeypatch):
    """`global_daily_cap` e `rate_per_min` protegem a chave do SERVIDOR e o
    serviço contra flood. Vendê-los por plano não criaria capacidade — só
    transferiria a recusa para outro usuário."""
    c, main = _client(monkeypatch, env={"B3_MANAGED_GLOBAL_DAILY_CAP": "50"})
    _ia_gerenciada_ligada(monkeypatch, main)
    chamadas = _espiao_metering(monkeypatch, main)
    _mes_usado(monkeypatch, main, 0)
    p = _registra(c)
    for chave in ("ia_gerenciada_dia", "max_analyses_per_month"):
        plan.set_limite_do_plano("free", chave, 999)

    main._gate_analise(p["user"]["id"], {})
    assert chamadas[-1]["cap_global"] == 50, "o teto global saiu do lugar"
    assert chamadas[-1]["rate_per_min"] == RATE_IA_GERENCIADA


def test_teto_global_da_aba_opcoes_e_o_rate_nao_mudam_com_plano_nenhum(monkeypatch):
    c, main = _client(monkeypatch)
    chamadas = _espiao_metering(monkeypatch, main)
    p = _registra(c)
    plan.set_limite_do_plano("free", "opcoes_chamadas_dia", 999)

    options_mcp_api._cap_check(p["user"]["id"], 1)
    assert chamadas[-1]["cap_global"] == COTA_GLOBAL_OPCOES
    assert chamadas[-1]["rate_per_min"] == RATE_OPCOES
    assert options_mcp_api.TETO_SERVICO_DIA == TETO_SERVICO_DIA


def test_o_catalogo_nao_ganhou_os_tetos_fisicos(monkeypatch):
    """Nenhum teto físico virou ponto de controle por plano — se algum entrar
    no catálogo, a decisão tem de ser consciente e passar por aqui."""
    assert set(chave for chave, *_r in plan.LIMITES_DE_PLANO) == set(HOJE_FREE)


# ===========================================================================
# 4) D3 — O OWNER PULA O CAP COMERCIAL, NUNCA O FÍSICO
# ===========================================================================
def test_owner_passa_o_cap_comercial_do_mes(monkeypatch):
    c, main = _client(monkeypatch, env={"B3_OWNER_EMAIL": OWNER_EMAIL})
    _ia_gerenciada_ligada(monkeypatch, main)
    chamadas = _espiao_metering(monkeypatch, main)
    p = _registra(c, email=OWNER_EMAIL)
    uid = p["user"]["id"]
    assert main.rbac.OWNER in main.rbac.roles_for_user(main._conn, uid)

    _mes_usado(monkeypatch, main, 9999)
    main._gate_analise(uid, {})           # não levanta
    assert chamadas, "o owner pulou o cap comercial e o físico junto"


def test_owner_continua_barrado_pelo_teto_fisico(monkeypatch):
    """A metade que importa da D3: o teto físico existe porque o serviço corta
    para a base INTEIRA. Ignorá-lo não cria capacidade — transfere a recusa."""
    c, main = _client(monkeypatch, env={"B3_OWNER_EMAIL": OWNER_EMAIL})
    _ia_gerenciada_ligada(monkeypatch, main)
    _espiao_metering(monkeypatch, main, resposta=(False, "teto global do servidor"))
    p = _registra(c, email=OWNER_EMAIL)

    _mes_usado(monkeypatch, main, 9999)
    with pytest.raises(HTTPException) as e:
        main._gate_analise(p["user"]["id"], {})
    assert e.value.status_code == 402
    assert "teto global do servidor" in str(e.value.detail)


def test_conta_comum_com_o_mes_estourado_continua_barrada(monkeypatch):
    """Não-regressão que passa nos DOIS estados, por desenho: é o que prova
    que a isenção da D3 é do `owner`, e não do gate inteiro."""
    c, main = _client(monkeypatch, env={"B3_OWNER_EMAIL": OWNER_EMAIL})
    _ia_gerenciada_ligada(monkeypatch, main)
    _espiao_metering(monkeypatch, main)
    p = _registra(c, email="comum@teste.com")

    _mes_usado(monkeypatch, main, 9999)
    with pytest.raises(HTTPException) as e:
        main._gate_analise(p["user"]["id"], {})
    assert str(e.value.detail) == (
        "Voce atingiu o limite de 30 analises/mes do plano free.")


def test_sem_owner_configurado_ninguem_pula_o_cap_comercial(monkeypatch):
    """`B3_OWNER_EMAIL` vazia = sem owner (decisão do 25-02). A isenção some
    junto — nada de "sem âncora, todo mundo passa"."""
    c, main = _client(monkeypatch, env={"B3_OWNER_EMAIL": ""})
    _ia_gerenciada_ligada(monkeypatch, main)
    _espiao_metering(monkeypatch, main)
    p = _registra(c, email=OWNER_EMAIL)

    _mes_usado(monkeypatch, main, 9999)
    with pytest.raises(HTTPException):
        main._gate_analise(p["user"]["id"], {})


# ===========================================================================
# 5) A RECUSA É CLASSIFICADA POR CÓDIGO, NÃO PELA FRASE
# ===========================================================================
def test_o_gate_carimba_o_codigo_do_limite_que_barrou(monkeypatch):
    c, main = _client(monkeypatch)
    _ia_gerenciada_ligada(monkeypatch, main)
    p = _registra(c)
    uid = p["user"]["id"]

    _espiao_metering(monkeypatch, main)
    _mes_usado(monkeypatch, main, 9999)
    with pytest.raises(HTTPException) as mensal:
        main._gate_analise(uid, {})
    assert options_mcp_api.codigo_do_limite(mensal.value) == options_mcp_api.COD_PLANO_ANALISES

    _mes_usado(monkeypatch, main, 0)
    _espiao_metering(monkeypatch, main, resposta=(False, "cota diaria estourada"))
    with pytest.raises(HTTPException) as diaria:
        main._gate_analise(uid, {})
    assert options_mcp_api.codigo_do_limite(diaria.value) == options_mcp_api.COD_IA_GERENCIADA


def test_os_dois_codigos_sao_os_que_a_aba_opcoes_ja_publica():
    """Os códigos são CONTRATO com o front da aba Opções (`detail.code`), não
    detalhe interno: escritos à mão aqui para que renomear um deles doa."""
    assert options_mcp_api.COD_PLANO_ANALISES == "plano_analises"
    assert options_mcp_api.COD_IA_GERENCIADA == "ia_gerenciada"


@pytest.mark.parametrize("codigo,texto", [
    # Textos TROCADOS de propósito: o do mensal fala de cota diária e vice-versa.
    # Se a classificação ainda dependesse da frase, os dois casos inverteriam.
    ("plano_analises", "Você atingiu o limite diário de 20 análises."),
    ("ia_gerenciada", "Voce atingiu o limite de 30 analises/mes do plano free."),
])
def test_mudar_a_frase_nao_muda_a_classificacao(monkeypatch, codigo, texto):
    """O defeito que esta fase fecha: `options_mcp_api` classificava o 402
    procurando a substring `"analises/mes"` na mensagem. Mudar a frase de
    `plan.py` — ou traduzi-la — quebrava a classificação EM SILÊNCIO."""
    c, main = _client(monkeypatch)

    def _nega(_scope, _config):
        raise options_mcp_api.marcar_o_limite(HTTPException(402, texto), codigo)

    monkeypatch.setattr(options_mcp_api, "_gate_analise", _nega)
    monkeypatch.setattr(options_mcp_api, "_config_do_usuario", lambda _uid: {})
    with pytest.raises(HTTPException) as e:
        options_mcp_api._gate_de_analise("u1")
    assert e.value.detail["code"] == codigo


def test_402_sem_carimbo_nao_derruba_a_traducao(monkeypatch):
    """Degradação: um 402 vindo de um caminho que ninguém carimbou continua
    virando um `code` válido, nunca 500."""
    c, main = _client(monkeypatch)

    def _nega(_scope, _config):
        raise HTTPException(402, "recusa sem carimbo")

    monkeypatch.setattr(options_mcp_api, "_gate_analise", _nega)
    monkeypatch.setattr(options_mcp_api, "_config_do_usuario", lambda _uid: {})
    with pytest.raises(HTTPException) as e:
        options_mcp_api._gate_de_analise("u1")
    assert e.value.detail["code"] in (options_mcp_api.COD_PLANO_ANALISES, options_mcp_api.COD_IA_GERENCIADA)


def test_o_texto_que_chega_ao_usuario_nao_mudou(monkeypatch):
    """O código é interno. A frase da recusa continua sendo a de `plan.py`."""
    c, main = _client(monkeypatch)
    _ia_gerenciada_ligada(monkeypatch, main)
    _espiao_metering(monkeypatch, main)
    p = _registra(c)
    _mes_usado(monkeypatch, main, 30)

    with pytest.raises(HTTPException) as e:
        main._gate_analise(p["user"]["id"], {})
    assert isinstance(e.value.detail, str), (
        "o detail virou dict e o app mostraria [object Object] na tela")
    assert str(e.value.detail) == (
        "Voce atingiu o limite de 30 analises/mes do plano free.")


# ===========================================================================
# 6) FAIL-CLOSED — plano não resolvido cai no MENOS privilegiado
# ===========================================================================
def test_escopo_anonimo_resolve_os_limites_do_free(monkeypatch):
    c, main = _client(monkeypatch)
    plan.set_limite_do_plano("free", "ia_gerenciada_dia", 4)
    plan.set_limite_do_plano("pro", "ia_gerenciada_dia", 400)

    assert main._limite_do_plano(None, "ia_gerenciada_dia",
                                 main.managed.daily_quota) == 4


def test_falha_ao_ler_o_usuario_degrada_para_o_plano_menos_privilegiado(monkeypatch):
    c, main = _client(monkeypatch)
    p = _registra(c)
    uid = p["user"]["id"]
    main.db.set_user_plan(main._conn, uid, "pro")
    plan.set_limite_do_plano("free", "ia_gerenciada_dia", 4)
    plan.set_limite_do_plano("pro", "ia_gerenciada_dia", 400)

    def _explode(*_a, **_k):
        raise RuntimeError("banco indisponivel")

    monkeypatch.setattr(main.db, "get_user_by_id", _explode)
    assert main._limite_do_plano(uid, "ia_gerenciada_dia",
                                 main.managed.daily_quota) == 4


def test_limite_desconhecido_nao_derruba_o_caminho_de_ia(monkeypatch):
    """Chave fora do catálogo (erro de digitação numa manutenção futura) cai
    no resolvedor GLOBAL em vez de estourar no meio de uma análise."""
    c, main = _client(monkeypatch)
    assert main._limite_do_plano(None, "chave_que_nao_existe",
                                 lambda: 42) == 42


def test_plan_py_continua_sem_importar_managed_e_options_mcp_api():
    """A fronteira do 25-03 sobrevive ao 25-04: a conciliação mora no
    CHAMADOR. Se `plan.py` importar aqueles módulos, o ciclo volta."""
    import ast
    import pathlib

    arvore = ast.parse(pathlib.Path(plan.__file__).read_text(encoding="utf-8"))
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom):
            nomes |= {a.name for a in no.names}
        elif isinstance(no, ast.Import):
            nomes |= {a.name.split(".")[0] for a in no.names}
    assert "managed" not in nomes
    assert "options_mcp_api" not in nomes
