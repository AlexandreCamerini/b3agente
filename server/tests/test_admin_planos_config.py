"""25-05 (Fase 4 do `.planning/phases/25-planos-comerciais/25-CONTEXT.md`) —
`GET`/`POST /api/admin/planos`: ler e configurar os cinco limites (e ver as
funções) de cada plano pelo portal, sem editar o kv à mão.

O que este arquivo trava, e a razão de cada coisa:

  - o gate é `usuarios.gerenciar` (gestão comercial da conta, mesmo eixo de
    `POST /api/admin/users/{id}/plan`), NÃO "qualquer admin" — por isso o caso
    do titular de outra permissão administrativa tomando 403;
  - **prévia não escreve**: o par simular/aplicar é a confirmação da casa, e
    uma prévia que grava é a pior classe de defeito possível num painel —
    o admin acha que simulou;
  - **auditoria por CAMPO**, entidade `plano_config`, `entity_id` = o plano e
    `field` = a chave do limite. Um agregado não responde "quem mudou o quê";
  - a entidade entra em `rbac.ENTIDADES_POR_PERMISSAO` — esquecer isso já
    aconteceu três vezes no repo (`mcp_cota`, `user_plan`, `opcoes_setup`),
    e o efeito é sempre o mesmo: o evento é gravado e `entidades_visiveis` o
    filtra para fora de TODO filtro, inclusive o de quem o produziu;
  - **voltar ao padrão existe e funciona**. Até aqui não havia como LIMPAR um
    limite gravado no kv (`db` não expõe delete de chave global), então uma
    configuração vencia a env para sempre. O caminho é um SENTINELA — linha
    PRESENTE cujo conteúdo significa "não configurado" —, e o que este arquivo
    prova é o efeito observável: depois de restaurar, a origem NÃO é mais
    `kv`. Sem essa asserção, um sentinela que o resolvedor não reconhecesse
    deixaria o valor preso como "kv com valor apagado";
  - `null` explícito = voltar ao padrão; chave OMITIDA = não mexer;
    `ilimitado` = sem limite. As três coisas são diferentes e o teste as separa;
  - `0` continua valor legítimo (bloqueia o ponto de controle), como o 25-03
    garantiu — divergência deliberada da cota de Opções, onde `0` seria o
    freio desligado sobre um teto físico compartilhado.

Isolamento igual a `test_admin_plano_usuario.py` (B3_DB_PATH temporário +
reset dos caches em memória entre testes), com um cuidado a mais herdado do
25-04: as envs do catálogo são APAGADAS, inclusive as três GLOBAIS
(`B3_MANAGED_DAILY_QUOTA`, `B3_MCP_COTA_USUARIO_DIA`,
`B3_ASSISTENTE_TETO_BRL`), que podem estar no ambiente de quem roda a suíte.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import plan, rbac


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import agent, brapi_budget, managed
    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    plan.reset_cache_planos()
    # As envs do catálogo somem: três delas são GLOBAIS e existem de verdade
    # no ambiente de produção/dev, então sem isto o teste mediria a máquina de
    # quem roda em vez do código.
    for pid in plan.PLANOS_POR_ID:
        for chave, *_ in plan.LIMITES_DE_PLANO:
            monkeypatch.delenv(plan.env_key(pid, chave), raising=False)
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    plan.reset_cache_planos()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch):
    monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    d = tempfile.mkdtemp(prefix="b3_planos_config_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


def _admin(monkeypatch):
    """Cliente + headers do admin (1ª conta recebe o bootstrap)."""
    c, main = _client(monkeypatch)
    dono = _registra(c, "dono@teste.com")
    return c, main, _auth(dono["token"])


def _eventos(c, headers, plano=None):
    evs = c.get("/api/admin/audit", headers=headers).json()["eventos"]
    return [e for e in evs
            if e["entity"] == "plano_config" and (plano is None or e["entityId"] == plano)]


def _limite(c, headers, plano, chave):
    return c.get("/api/admin/planos", headers=headers).json()["config"][plano][chave]


# --------------------------------- o gate ------------------------------------
def test_sem_sessao_401(monkeypatch):
    c, _ = _client(monkeypatch)
    _registra(c, "dono@teste.com")
    assert c.get("/api/admin/planos").status_code == 401
    assert c.post("/api/admin/planos", json={"plano": "free"}).status_code == 401


def test_usuario_comum_403(monkeypatch):
    c, _ = _client(monkeypatch)
    _registra(c, "dono@teste.com")
    comum = _registra(c, "comum@teste.com")
    h = _auth(comum["token"])
    assert c.get("/api/admin/planos", headers=h).status_code == 403
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_watchlist": 5}, "aplicar": True}, headers=h)
    assert r.status_code == 403, r.text


def test_outra_permissao_admin_nao_basta(monkeypatch):
    """Prova que o gate é `usuarios.gerenciar` e não "tem algum papel admin" —
    sem esta asserção, trocar a dependency por `require_any_admin_permission`
    passaria despercebido e um editor de prompts mudaria o cap comercial."""
    c, _, h_admin = _admin(monkeypatch)
    editor = _registra(c, "editor@teste.com")
    r = c.post(f"/api/admin/users/{editor['user']['id']}/roles",
               json={"role": "prompts", "acao": "conceder"}, headers=h_admin)
    assert r.status_code == 200, r.text
    h = _auth(editor["token"])
    # o editor É admin de alguma coisa (vê a auditoria), mas não disto
    assert c.get("/api/admin/audit", headers=h).status_code == 200
    r = c.get("/api/admin/planos", headers=h)
    assert r.status_code == 403, r.text
    assert "usuarios.gerenciar" in r.text


def test_com_a_permissao_200(monkeypatch):
    c, _, h = _admin(monkeypatch)
    assert c.get("/api/admin/planos", headers=h).status_code == 200


# ------------------------ o catálogo vem do backend --------------------------
def test_get_publica_planos_limites_e_funcoes(monkeypatch):
    """A UI não escreve lista nenhuma: planos, limites (com rótulo e tipo) e
    funções chegam prontos. Um campo faltando aqui vira lista literal no
    portal, que é a segunda cópia que não acompanha a próxima mudança."""
    c, _, h = _admin(monkeypatch)
    d = c.get("/api/admin/planos", headers=h).json()
    assert d["planos"] == ["free", "pro"]
    chaves_catalogo = [chave for chave, *_ in plan.LIMITES_DE_PLANO]
    assert [L["chave"] for L in d["limites"]] == chaves_catalogo
    for L in d["limites"]:
        assert L["rotulo"] and L["ajuda"], L
        assert L["tipo"] in ("int", "float")
    for pid in d["planos"]:
        assert set(d["config"][pid]) == set(chaves_catalogo)
        for chave, info in d["config"][pid].items():
            assert set(info) >= {"valor", "origem", "env", "kv", "default", "tipo",
                                 "decide", "efetivo"}
    assert d["funcoes"]["pro"] == ["opcoes.criar_setup"]
    assert d["funcoes"]["free"] == []
    assert plan.TXT_SEM_LIMITE == d["textoSemLimite"]


def test_todo_limite_do_catalogo_tem_rotulo_proprio(monkeypatch):
    """Um ponto de controle novo em `LIMITES_DE_PLANO` sem metadado apareceria
    no painel com o nome interno da chave. O teste força a decisão consciente
    em vez de deixar `assistente_brl_dia` virar rótulo de tela."""
    c, _, h = _admin(monkeypatch)
    d = c.get("/api/admin/planos", headers=h).json()
    for L in d["limites"]:
        assert L["rotulo"] != L["chave"], f"limite sem rótulo próprio: {L['chave']}"


def test_origem_default_diz_quem_decide(monkeypatch):
    """O achado do 25-04: `origem: "default"` num limite de PLANO significa
    "quem decide é o resolvedor GLOBAL", não "ninguém configurou nada". Sem
    `decide` publicado, o admin lê `60 · padrão` no free e conclui que o plano
    free define 60 — quando quem manda é o card vizinho."""
    c, _, h = _admin(monkeypatch)
    d = c.get("/api/admin/planos", headers=h).json()
    for pid in d["planos"]:
        for chave, info in d["config"][pid].items():
            assert info["origem"] == "default", (pid, chave, info)
            assert info["decide"] == "global", (pid, chave, info)
    por_chave = {L["chave"]: L for L in d["limites"]}
    # os três que TÊM resolvedor global nomeiam a env que ele lê...
    assert por_chave["opcoes_chamadas_dia"]["global"]["env"] == "B3_MCP_COTA_USUARIO_DIA"
    assert por_chave["ia_gerenciada_dia"]["global"]["env"] == "B3_MANAGED_DAILY_QUOTA"
    assert por_chave["assistente_brl_dia"]["global"]["env"] == "B3_ASSISTENTE_TETO_BRL"
    # ...e os dois que NÃO têm dizem isso explicitamente: ali o default do
    # catálogo é a última palavra mesmo, e a frase na tela é outra.
    assert por_chave["max_watchlist"]["global"] is None
    assert por_chave["max_analyses_per_month"]["global"] is None


def test_limite_configurado_passa_a_decidir_pelo_plano(monkeypatch):
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"opcoes_chamadas_dia": 7}, "aplicar": True},
               headers=h)
    assert r.status_code == 200, r.text
    info = _limite(c, h, "free", "opcoes_chamadas_dia")
    assert info["valor"] == 7 and info["origem"] == "kv"
    assert info["decide"] == "plano"
    assert info["efetivo"] == 7
    # e o outro plano não foi tocado — os dois não disputam o mesmo registro
    assert _limite(c, h, "pro", "opcoes_chamadas_dia")["origem"] == "default"


# ------------------------------- a prévia ------------------------------------
def test_previa_nao_escreve_nada(monkeypatch):
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_watchlist": 3}}, headers=h)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["aplicado"] is False
    assert [(m["campo"], m["de"], m["para"]) for m in d["mudancas"]] == [("max_watchlist", 10, 3)]
    # relendo: nada mudou
    info = _limite(c, h, "free", "max_watchlist")
    assert info["valor"] == 10 and info["origem"] == "default"
    assert _eventos(c, h) == []


def test_previa_sem_mudanca_nao_lista_nada(monkeypatch):
    """Informar o valor vigente não é mudança — mas APLICAR isso fixaria a
    origem no painel, e é por isso que a lista de mudanças compara também a
    origem (o caso irmão está em `test_restaurar_sem_mudar_o_numero...`)."""
    c, _, h = _admin(monkeypatch)
    c.post("/api/admin/planos",
           json={"plano": "free", "limites": {"max_watchlist": 4}, "aplicar": True}, headers=h)
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_watchlist": 4}}, headers=h)
    assert r.json()["mudancas"] == []


# ------------------------------- aplicar -------------------------------------
def test_aplicar_muda_e_audita_um_evento_por_campo(monkeypatch):
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos",
               json={"plano": "free",
                     "limites": {"max_watchlist": 3, "ia_gerenciada_dia": 5},
                     "aplicar": True},
               headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["aplicado"] is True
    assert _limite(c, h, "free", "max_watchlist")["valor"] == 3
    assert _limite(c, h, "free", "ia_gerenciada_dia")["valor"] == 5

    evs = _eventos(c, h, plano="free")
    assert len(evs) == 2, evs
    assert {e["field"] for e in evs} == {"max_watchlist", "ia_gerenciada_dia"}
    assert {e["entityId"] for e in evs} == {"free"}


def test_chave_omitida_nao_altera_nada(monkeypatch):
    c, _, h = _admin(monkeypatch)
    c.post("/api/admin/planos",
           json={"plano": "free", "limites": {"max_watchlist": 3, "ia_gerenciada_dia": 5},
                 "aplicar": True}, headers=h)
    c.post("/api/admin/planos",
           json={"plano": "free", "limites": {"max_watchlist": 9}, "aplicar": True}, headers=h)
    assert _limite(c, h, "free", "max_watchlist")["valor"] == 9
    assert _limite(c, h, "free", "ia_gerenciada_dia")["valor"] == 5
    # e o campo que não mudou não produziu evento de auditoria nenhum
    assert len(_eventos(c, h)) == 3


def test_zero_e_valor_legitimo(monkeypatch):
    """25-03: aqui `0` é intenção de produto ("este plano não acessa isto"),
    ao contrário da cota de Opções, onde `0` seria o freio DESLIGADO sobre um
    teto físico compartilhado."""
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"ia_gerenciada_dia": 0}, "aplicar": True},
               headers=h)
    assert r.status_code == 200, r.text
    info = _limite(c, h, "free", "ia_gerenciada_dia")
    assert info["valor"] == 0 and info["origem"] == "kv"


def test_ilimitado_e_diferente_de_voltar_ao_padrao(monkeypatch):
    """As duas coisas se pareceriam (`null` nos dois lados do fio) e são
    opostas: `ilimitado` é configuração do plano que VENCE o global; voltar ao
    padrão devolve a decisão ao global."""
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_watchlist": plan.TXT_SEM_LIMITE},
                     "aplicar": True}, headers=h)
    assert r.status_code == 200, r.text
    info = _limite(c, h, "free", "max_watchlist")
    assert info["valor"] is None and info["origem"] == "kv"


# --------------------------- voltar ao padrão --------------------------------
def test_null_volta_ao_padrao_e_a_origem_deixa_de_ser_kv(monkeypatch):
    """A limitação herdada do 25-03/25-04: sem isto, um limite gravado uma vez
    vence a env PARA SEMPRE. O que prova o mecanismo é a ORIGEM depois da
    restauração — um sentinela que o resolvedor não reconhecesse deixaria o
    valor preso como "kv com valor apagado"."""
    c, _, h = _admin(monkeypatch)
    c.post("/api/admin/planos",
           json={"plano": "free", "limites": {"max_watchlist": 3}, "aplicar": True}, headers=h)
    assert _limite(c, h, "free", "max_watchlist")["origem"] == "kv"

    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_watchlist": None}, "aplicar": True},
               headers=h)
    assert r.status_code == 200, r.text
    info = _limite(c, h, "free", "max_watchlist")
    assert info["origem"] != "kv", info
    assert info["origem"] == "default"
    assert info["valor"] == 10


def test_restaurar_cai_na_env_quando_ela_existe(monkeypatch):
    """"Voltar ao padrão" é devolver a decisão às camadas de BAIXO, não zerar:
    com a env declarada, é nela que o valor cai — e a origem entrega isso."""
    c, _, h = _admin(monkeypatch)
    c.post("/api/admin/planos",
           json={"plano": "free", "limites": {"max_watchlist": 3}, "aplicar": True}, headers=h)
    monkeypatch.setenv(plan.env_key("free", "max_watchlist"), "7")
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_watchlist": None}, "aplicar": True},
               headers=h)
    assert r.status_code == 200, r.text
    info = _limite(c, h, "free", "max_watchlist")
    assert (info["valor"], info["origem"]) == (7, "env"), info


def test_previa_de_restauracao_mostra_onde_o_valor_vai_cair(monkeypatch):
    """Um "→ (padrão)" sem número faria o admin aplicar sem saber o destino."""
    c, _, h = _admin(monkeypatch)
    c.post("/api/admin/planos",
           json={"plano": "free", "limites": {"max_watchlist": 3}, "aplicar": True}, headers=h)
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_watchlist": None}}, headers=h)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["aplicado"] is False
    assert len(d["mudancas"]) == 1
    m = d["mudancas"][0]
    assert (m["campo"], m["de"], m["para"], m["restaurar"]) == ("max_watchlist", 3, 10, True)
    # e continua sem escrever
    assert _limite(c, h, "free", "max_watchlist")["origem"] == "kv"


def test_restaurar_sem_mudar_o_numero_ainda_audita(monkeypatch):
    """Gravar 10 no free e depois restaurar devolve o MESMO 10 — mas quem
    decide mudou (painel → padrão). Auditar só por valor deixaria essa escrita
    sem registro, que é exatamente o tipo de mudança que ninguém consegue
    explicar depois."""
    c, _, h = _admin(monkeypatch)
    c.post("/api/admin/planos",
           json={"plano": "free", "limites": {"max_watchlist": 10}, "aplicar": True}, headers=h)
    antes = len(_eventos(c, h))
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_watchlist": None}, "aplicar": True},
               headers=h)
    assert r.status_code == 200, r.text
    assert _limite(c, h, "free", "max_watchlist")["origem"] == "default"
    assert len(_eventos(c, h)) == antes + 1


# ------------------------------- validação -----------------------------------
def test_chave_fora_do_catalogo_400(monkeypatch):
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_foguetes": 3}, "aplicar": True}, headers=h)
    assert r.status_code == 400, r.text
    assert "max_foguetes" in r.text


def test_plano_fora_do_catalogo_400_nomeando_os_aceitos(monkeypatch):
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos",
               json={"plano": "platina", "limites": {"max_watchlist": 3}, "aplicar": True}, headers=h)
    assert r.status_code == 400, r.text
    assert "free" in r.text and "pro" in r.text


def test_valor_de_tipo_errado_400_nomeando_o_tipo(monkeypatch):
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_watchlist": "dez"}, "aplicar": True}, headers=h)
    assert r.status_code == 400, r.text
    assert "inteiro" in r.text.lower()
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"assistente_brl_dia": "caro"}, "aplicar": True}, headers=h)
    assert r.status_code == 400, r.text


def test_validacao_e_tudo_ou_nada(monkeypatch):
    """Metade da mudança de pé é pior que nenhuma: o admin não tem como saber
    qual metade. Mesma disciplina de `_cota_opcoes_pedidos`."""
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos",
               json={"plano": "free", "limites": {"max_watchlist": 3, "ia_gerenciada_dia": "lixo"},
                     "aplicar": True}, headers=h)
    assert r.status_code == 400, r.text
    assert _limite(c, h, "free", "max_watchlist")["origem"] == "default"


def test_limites_vazio_400(monkeypatch):
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos", json={"plano": "free", "limites": {}, "aplicar": True}, headers=h)
    assert r.status_code == 400, r.text


# --------------------------- auditoria visível -------------------------------
def test_entidade_plano_config_no_mapa_de_permissoes():
    """`rbac.py` declara que `ENTIDADES_POR_PERMISSAO` cobre toda `entity`
    gravada. Já foi esquecido três vezes (`mcp_cota`, `user_plan`,
    `opcoes_setup`) e o efeito é sempre o mesmo: o evento existe e ninguém o
    vê, nem quem o produziu."""
    assert "plano_config" in rbac.ENTIDADES_POR_PERMISSAO["usuarios.gerenciar"]


def test_evento_visivel_para_quem_tem_a_permissao(monkeypatch):
    """Pelo caminho HTTP, não pela leitura do dicionário: é `entidades_visiveis`
    que filtra `GET /api/admin/audit`."""
    c, _, h_admin = _admin(monkeypatch)
    gestor = _registra(c, "gestor@teste.com")
    r = c.post(f"/api/admin/users/{gestor['user']['id']}/roles",
               json={"role": "usuarios", "acao": "conceder"}, headers=h_admin)
    assert r.status_code == 200, r.text
    h = _auth(gestor["token"])
    r = c.post("/api/admin/planos",
               json={"plano": "pro", "limites": {"max_watchlist": 50}, "aplicar": True}, headers=h)
    assert r.status_code == 200, r.text
    evs = _eventos(c, h, plano="pro")
    assert len(evs) == 1, evs
    assert evs[0]["field"] == "max_watchlist"


# ---------------------- funções do plano (D2 pendente) -----------------------
def test_funcoes_sao_publicadas_com_a_nota_de_que_o_rbac_manda(monkeypatch):
    """D2 NÃO migrou (decisão do Alex no 25-04). A tela mostra a função, e a
    nota impede a leitura errada de que o plano já a libera."""
    c, _, h = _admin(monkeypatch)
    d = c.get("/api/admin/planos", headers=h).json()
    assert "opcoes.criar_setup" in d["funcoes"]["pro"]
    nota = d["notasDeFuncao"]["opcoes.criar_setup"]
    assert "RBAC" in nota
    # e a permissão continua sendo do RBAC — o dia da migração derruba isto
    assert "opcoes.criar_setup" in rbac.GRUPOS["opcoes"]


def test_a_rota_nao_escreve_funcao_nenhuma(monkeypatch):
    """Nenhum controle de escrita existe para funções enquanto a D2 estiver
    pendente — nem pela UI, nem pela rota."""
    c, _, h = _admin(monkeypatch)
    r = c.post("/api/admin/planos",
               json={"plano": "pro", "funcoes": ["opcoes.criar_setup"], "aplicar": True},
               headers=h)
    # sem `limites`, a rota recusa — `funcoes` não é campo aceito
    assert r.status_code == 400, r.text
    assert plan.funcoes_do_plano("free") == set()
