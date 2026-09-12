"""25-03 (Fase 2 do `.planning/phases/25-planos-comerciais/25-CONTEXT.md`) —
o guardião de que transformar `plan.py` em catálogo NÃO mudou política.

O critério mais importante deste plano não é o que ele acrescenta, é o que ele
não muda: sem nada configurado, `free` e `pro` se comportam exatamente como
antes. Por isso os valores esperados estão escritos **por extenso** aqui
embaixo (30, 10, `None`, 20, 60, 1.0) em vez de lidos de `plan.py`. A
duplicação é o ponto: um guardião que lê o mesmo dicionário que testa
acompanha qualquer mudança em silêncio e não guarda nada.

O que cada bloco trava, em uma frase:
  1. sem kv e sem env, os cinco limites dos dois planos são os de hoje;
  2. `can_analyze` recusa no mesmo número e com a MESMA frase — é texto que o
     usuário lê;
  3. `can_add_ticker`/`can_grow_watchlist_to` idem, com a semântica `>=` vs `>`
     que as separa;
  4. precedência kv > env > default, um degrau por caso;
  5. `None` (sem limite) e `0` (bloqueia) sobrevivem distinguíveis ao ida e
     volta pelo kv — confundi-los transformaria "plano sem limite" em "plano
     que não funciona";
  6. lixo no kv cai para a camada de baixo e NUNCA desliga o limite —
     desligar por dado corrompido seria o pior modo de falhar;
  7. as funções de produto (D2) são conjunto, e `opcoes.criar_setup` está em
     quem deve ter;
  8. `plan.py` não importa `managed` nem `options_mcp_api` (o import ao
     contrário faria ciclo, e é por isso que `options_mcp_api` é fiado por
     injeção).

Estado anterior, para leitura honesta do que este arquivo prova: os blocos 2 e
3 já passavam antes desta mudança (são não-regressão); 1, 4, 5, 6 e 7 não
compilavam — as funções não existiam.
"""
import ast
import os
import pathlib
import tempfile

import pytest

from app import db, plan

# ---------------------------------------------------------------------------
# Os números de HOJE, escritos à mão. Se alguém mudar um default em
# `plan.py`, este arquivo tem de gritar — não acompanhar.
# ---------------------------------------------------------------------------
HOJE = {
    "free": {
        "max_watchlist": 10,
        "max_analyses_per_month": 30,
        "ia_gerenciada_dia": 20,
        "opcoes_chamadas_dia": 60,
        "assistente_brl_dia": 1.0,
    },
    "pro": {
        "max_watchlist": None,
        "max_analyses_per_month": None,
        "ia_gerenciada_dia": 20,
        "opcoes_chamadas_dia": 60,
        "assistente_brl_dia": 1.0,
    },
}

# As frases de recusa, byte a byte. Elas moram só em `plan.py` (D-05/CAP-07) e
# são o que o usuário lê na tela.
RECUSA_ANALISES_FREE = "Voce atingiu o limite de 30 analises/mes do plano free."
RECUSA_WATCHLIST_FREE = "Voce atingiu o limite de 10 ativos do plano free."


def _banco():
    d = tempfile.mkdtemp(prefix="b3_catalogo_planos_")
    return db.connect(os.path.join(d, "b3_agente.db"))


def _todas_as_envs():
    return {plan.env_key(p, chave)
            for p in plan.PLANOS_POR_ID
            for chave, *_resto in plan.LIMITES_DE_PLANO}


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    """Banco novo por caso e NENHUMA env do catálogo ligada — inclusive as três
    compartilhadas (`B3_MANAGED_DAILY_QUOTA`, `B3_MCP_COTA_USUARIO_DIA`,
    `B3_ASSISTENTE_TETO_BRL`), que podem estar no ambiente de quem roda a
    suíte. A conexão anterior é restaurada no fim porque `app.main`, se já foi
    importado por outro módulo de teste, injetou a dele."""
    anterior = plan._conn
    for env in _todas_as_envs():
        monkeypatch.delenv(env, raising=False)
    plan.configure_db(_banco())
    yield
    plan.configure_db(anterior)


# ===========================================================================
# 1) SEM CONFIGURAÇÃO, NADA MUDA
# ===========================================================================
@pytest.mark.parametrize("plano_id", ["free", "pro"])
def test_sem_kv_e_sem_env_os_limites_sao_os_de_hoje(plano_id):
    lim = plan.limites_do_plano(plano_id)
    assert set(lim) == set(HOJE[plano_id]), (
        "o catálogo ganhou ou perdeu um ponto de controle sem que este "
        "guardião fosse atualizado — a decisão tem de ser consciente")
    for chave, esperado in HOJE[plano_id].items():
        assert lim[chave]["valor"] == esperado, f"{plano_id}.{chave} mudou de valor"
        assert lim[chave]["origem"] == "default", (
            f"{plano_id}.{chave} veio de {lim[chave]['origem']} numa instalação limpa")
        assert lim[chave]["default"] == esperado


def test_o_dict_estatico_que_os_gates_leem_continua_com_os_dois_limites_de_hoje():
    """Os três gates da Fase 12 leem o dict de `current_plan`, não o catálogo —
    é assim até o 25-04. Se esta asserção cair, o comportamento mudou mesmo
    que `limites_do_plano` esteja certo."""
    assert plan.PLAN_FREE["max_watchlist"] == 10
    assert plan.PLAN_FREE["max_analyses_per_month"] == 30
    assert plan.PLAN_PRO["max_watchlist"] is None
    assert plan.PLAN_PRO["max_analyses_per_month"] is None
    assert plan.ACTIVE_PLAN is plan.PLAN_FREE
    assert plan.current_plan(None) is plan.ACTIVE_PLAN
    assert plan.current_plan({"plan": "pro"}) is plan.PLAN_PRO


def test_a_env_de_um_plano_nao_e_a_do_outro_onde_o_valor_ja_difere():
    """`max_watchlist` vale 10 no free e nada no pro: uma env única achataria
    os dois. Os três pontos globais de hoje seguem globais de propósito."""
    assert plan.env_key("free", "max_watchlist") != plan.env_key("pro", "max_watchlist")
    assert plan.env_key("free", "ia_gerenciada_dia") == plan.env_key("pro", "ia_gerenciada_dia")
    assert plan.env_key("free", "ia_gerenciada_dia") == "B3_MANAGED_DAILY_QUOTA"
    assert plan.env_key("free", "opcoes_chamadas_dia") == "B3_MCP_COTA_USUARIO_DIA"
    assert plan.env_key("free", "assistente_brl_dia") == "B3_ASSISTENTE_TETO_BRL"


def test_a_chave_de_kv_carrega_o_id_do_plano_e_os_dois_nao_se_atropelam():
    assert plan.kv_key("free", "max_analyses_per_month") == "planoFree.analisesMes"
    assert plan.kv_key("pro", "max_analyses_per_month") == "planoPro.analisesMes"

    plan.set_limite_do_plano("free", "max_watchlist", 3)
    assert plan.limites_do_plano("free")["max_watchlist"]["valor"] == 3
    assert plan.limites_do_plano("pro")["max_watchlist"]["valor"] is None, (
        "configurar o free mexeu no pro — os dois disputam o mesmo registro")


# ===========================================================================
# 2) can_analyze — mesmo número, mesma frase
# ===========================================================================
def test_can_analyze_permite_em_29_e_nega_em_30_com_a_frase_de_hoje():
    assert plan.can_analyze(29, plan=plan.PLAN_FREE) == (True, None)
    assert plan.can_analyze(30, plan=plan.PLAN_FREE) == (False, RECUSA_ANALISES_FREE)
    assert plan.can_analyze(31, plan=plan.PLAN_FREE)[1] == RECUSA_ANALISES_FREE


def test_can_analyze_no_pro_nao_tem_teto():
    assert plan.can_analyze(30, plan=plan.PLAN_PRO) == (True, None)
    assert plan.can_analyze(10_000, plan=plan.PLAN_PRO) == (True, None)


def test_can_analyze_sem_plano_cai_no_fallback_anonimo_que_e_o_free():
    assert plan.can_analyze(29) == (True, None)
    assert plan.can_analyze(30) == (False, RECUSA_ANALISES_FREE)


# ===========================================================================
# 3) watchlist — os dois hooks, com a diferença `>=` vs `>` preservada
# ===========================================================================
def test_can_add_ticker_permite_em_9_e_nega_em_10_com_a_frase_de_hoje():
    assert plan.can_add_ticker(9, plan=plan.PLAN_FREE) == (True, None)
    assert plan.can_add_ticker(10, plan=plan.PLAN_FREE) == (False, RECUSA_WATCHLIST_FREE)


def test_can_grow_watchlist_to_permite_exatamente_10_e_nega_11():
    """`can_add_ticker` recebe quantos existem ANTES de somar 1 (compara `>=`);
    `can_grow_watchlist_to` recebe o tamanho FINAL (compara `>`). Trocar um
    pelo outro erra por um, em silêncio."""
    assert plan.can_grow_watchlist_to(10, plan=plan.PLAN_FREE) == (True, None)
    assert plan.can_grow_watchlist_to(11, plan=plan.PLAN_FREE) == (False, RECUSA_WATCHLIST_FREE)


def test_watchlist_no_pro_nao_tem_teto():
    assert plan.can_add_ticker(10_000, plan=plan.PLAN_PRO) == (True, None)
    assert plan.can_grow_watchlist_to(10_000, plan=plan.PLAN_PRO) == (True, None)


# ===========================================================================
# 4) PRECEDÊNCIA — kv > env > default, um degrau por caso
# ===========================================================================
def test_so_env_manda_e_a_origem_diz_env(monkeypatch):
    monkeypatch.setenv("B3_PLANO_FREE_ANALISES_MES", "7")
    monkeypatch.setenv("B3_MANAGED_DAILY_QUOTA", "9")
    monkeypatch.setenv("B3_ASSISTENTE_TETO_BRL", "2.5")

    lim = plan.limites_do_plano("free")
    assert (lim["max_analyses_per_month"]["valor"], lim["max_analyses_per_month"]["origem"]) == (7, "env")
    assert (lim["ia_gerenciada_dia"]["valor"], lim["ia_gerenciada_dia"]["origem"]) == (9, "env")
    assert (lim["assistente_brl_dia"]["valor"], lim["assistente_brl_dia"]["origem"]) == (2.5, "env")
    # o que não foi declarado continua no default
    assert lim["max_watchlist"]["origem"] == "default"


def test_kv_vence_a_env_e_a_origem_diz_kv(monkeypatch):
    monkeypatch.setenv("B3_PLANO_FREE_ANALISES_MES", "7")
    plan.set_limite_do_plano("free", "max_analyses_per_month", 4)

    lim = plan.limites_do_plano("free")
    assert (lim["max_analyses_per_month"]["valor"], lim["max_analyses_per_month"]["origem"]) == (4, "kv")


def test_env_muda_em_runtime_sem_reiniciar_o_processo(monkeypatch):
    """A env é lida A CADA leitura de propósito: é como o Railway troca um
    limite sem publicar código. Cachear a env mataria isso em silêncio — daí o
    cache existir só para o valor vindo do kv."""
    assert plan.limites_do_plano("free")["max_watchlist"]["valor"] == 10
    monkeypatch.setenv("B3_PLANO_FREE_WATCHLIST", "5")
    assert plan.limites_do_plano("free")["max_watchlist"]["valor"] == 5, (
        "o cache do kv vazou para a camada de env")


def test_o_valor_do_painel_sobrevive_a_um_processo_novo():
    """`reset_cache_planos()` é o processo novo em miniatura: memória vazia, kv
    intacto. Sem persistência, o painel viraria um ajuste que o próximo deploy
    apaga."""
    plan.set_limite_do_plano("pro", "opcoes_chamadas_dia", 120)
    plan.reset_cache_planos()
    lim = plan.limites_do_plano("pro")
    assert (lim["opcoes_chamadas_dia"]["valor"], lim["opcoes_chamadas_dia"]["origem"]) == (120, "kv")


def test_set_recusa_lixo_em_vez_de_clampar():
    """Divergência deliberada de `options_mcp_api._set_limite`, que faz
    `max(1, int(n))`: lá o clamp protege um teto físico compartilhado; aqui um
    `0` é intenção de produto e um lixo é lixo. Engolir em silêncio faria o
    painel confirmar configuração que não foi a pedida."""
    for ruim in ("banana", "", -1, 3.5, True, [], {}):
        with pytest.raises(ValueError):
            plan.set_limite_do_plano("free", "max_watchlist", ruim)
    with pytest.raises(ValueError):
        plan.set_limite_do_plano("enterprise", "max_watchlist", 5)
    with pytest.raises(ValueError):
        plan.set_limite_do_plano("free", "max_inventado", 5)
    with pytest.raises(ValueError):
        plan.limites_do_plano("enterprise")
    # o formulário manda texto; número em texto é entrada legítima
    assert plan.set_limite_do_plano("free", "max_watchlist", "5") == 5
    assert plan.set_limite_do_plano("free", "assistente_brl_dia", "2.5") == 2.5


# ===========================================================================
# 5) None (sem limite) ≠ 0 (bloqueia)
# ===========================================================================
def test_sem_limite_e_bloqueio_sobrevivem_distinguiveis_ao_ida_e_volta_pelo_kv(monkeypatch):
    """O caso que transformaria "plano sem limite" em "plano que não funciona".
    A env fica declarada de propósito: se `None` fosse lido como "não
    configurado", a resolução cairia nela e a origem diria `env`."""
    monkeypatch.setenv("B3_PLANO_FREE_WATCHLIST", "77")

    plan.set_limite_do_plano("free", "max_watchlist", None)
    plan.reset_cache_planos()
    lim = plan.limites_do_plano("free")
    assert lim["max_watchlist"]["valor"] is None
    assert lim["max_watchlist"]["origem"] == "kv", (
        "`None` gravado virou 'não configurado' e a resolução caiu para a "
        "camada de baixo")

    plan.set_limite_do_plano("free", "max_watchlist", 0)
    plan.reset_cache_planos()
    lim = plan.limites_do_plano("free")
    assert lim["max_watchlist"]["valor"] == 0
    assert lim["max_watchlist"]["origem"] == "kv"


def test_o_gate_le_sem_limite_como_libera_e_zero_como_bloqueia():
    """A consequência do item acima no único lugar que importa: a decisão."""
    sem_limite = {"id": "pro", "max_watchlist": None, "max_analyses_per_month": None}
    bloqueado = {"id": "free", "max_watchlist": 0, "max_analyses_per_month": 0}

    assert plan.can_add_ticker(0, plan=sem_limite) == (True, None)
    assert plan.can_analyze(0, plan=sem_limite) == (True, None)
    assert plan.can_add_ticker(0, plan=bloqueado)[0] is False
    assert plan.can_grow_watchlist_to(1, plan=bloqueado)[0] is False
    assert plan.can_analyze(0, plan=bloqueado)[0] is False


def test_ilimitado_por_env_tambem_vale(monkeypatch):
    """A env só carrega texto; `ilimitado` é como "sem limite" se escreve nela.
    Sem isso, um plano sem teto seria inconfigurável fora do painel."""
    monkeypatch.setenv("B3_PLANO_FREE_WATCHLIST", "ilimitado")
    lim = plan.limites_do_plano("free")
    assert lim["max_watchlist"]["valor"] is None
    assert lim["max_watchlist"]["origem"] == "env"


# ===========================================================================
# 6) LIXO NO KV CAI PARA BAIXO E NUNCA DESLIGA O LIMITE
# ===========================================================================
def test_kv_com_lixo_cai_para_o_default_e_nunca_desliga_o_limite():
    chave_kv = plan.kv_key("free", "max_watchlist")
    for lixo in ("banana", True, False, -5, 3.5, [], {}, "ilimitadoo"):
        db.kv_set(plan._conn, chave_kv, lixo, user_id=None)
        plan.reset_cache_planos()
        lim = plan.limites_do_plano("free")
        assert lim["max_watchlist"]["valor"] == 10, f"kv={lixo!r} não caiu para o default"
        assert lim["max_watchlist"]["origem"] == "default"
        assert lim["max_watchlist"]["valor"] is not None, (
            f"kv={lixo!r} desligou o limite — dado corrompido virou plano sem teto")


def test_kv_com_lixo_cai_para_a_env_quando_ela_existe(monkeypatch):
    monkeypatch.setenv("B3_PLANO_FREE_WATCHLIST", "6")
    db.kv_set(plan._conn, plan.kv_key("free", "max_watchlist"), "banana", user_id=None)
    plan.reset_cache_planos()
    lim = plan.limites_do_plano("free")
    assert (lim["max_watchlist"]["valor"], lim["max_watchlist"]["origem"]) == (6, "env")


def test_env_torta_cai_para_o_default_sem_derrubar(monkeypatch):
    for torta in ("banana", "-3", "", "   ", "1,5"):
        monkeypatch.setenv("B3_PLANO_FREE_WATCHLIST", torta)
        lim = plan.limites_do_plano("free")
        assert (lim["max_watchlist"]["valor"], lim["max_watchlist"]["origem"]) == (10, "default"), \
            f"env={torta!r}"


def test_float_em_ponto_de_controle_inteiro_e_lixo_nao_arredondamento():
    """`3.5 análises/mês` não é 3 nem 4 — é declaração que não faz sentido.
    Arredondar seria inventar o número que o admin não pediu."""
    db.kv_set(plan._conn, plan.kv_key("free", "max_analyses_per_month"), 3.5, user_id=None)
    plan.reset_cache_planos()
    assert plan.limites_do_plano("free")["max_analyses_per_month"]["valor"] == 30


def test_sem_conexao_a_camada_de_kv_fica_inerte_e_a_resolucao_degrada(monkeypatch):
    """Banco ausente é degradação, não erro: sobra env → default. É o que
    acontece num processo que nunca chamou `configure_db`."""
    plan.set_limite_do_plano("free", "max_watchlist", 2)
    plan.configure_db(None)
    monkeypatch.setenv("B3_PLANO_FREE_WATCHLIST", "8")
    lim = plan.limites_do_plano("free")
    assert (lim["max_watchlist"]["valor"], lim["max_watchlist"]["origem"]) == (8, "env")


# ===========================================================================
# 7) FUNÇÕES DE PRODUTO (D2)
# ===========================================================================
def test_funcoes_do_plano_e_conjunto_e_criar_setup_esta_no_pro():
    assert plan.funcoes_do_plano("pro") == {"opcoes.criar_setup"}
    assert plan.funcoes_do_plano("free") == set()
    assert isinstance(plan.funcoes_do_plano("pro"), set)


def test_plano_desconhecido_nao_libera_funcao_nenhuma():
    """Fail-closed, igual ao `current_plan` caindo para `free`."""
    assert plan.funcoes_do_plano("enterprise") == set()
    assert plan.funcoes_do_plano("") == set()


def test_o_conjunto_devolvido_e_copia_e_mexer_nele_nao_muda_o_catalogo():
    fora = plan.funcoes_do_plano("pro")
    fora.add("opcoes.apagar_tudo")
    assert plan.funcoes_do_plano("pro") == {"opcoes.criar_setup"}


def test_as_candidatas_ficam_registradas_e_nao_liberadas():
    """Registradas para que a próxima função de produto não nasça como literal
    solta numa rota; não liberadas porque nenhuma existe."""
    assert set(plan.FUNCOES_CANDIDATAS) == {"agente_autonomo", "analises_ilimitadas"}
    for plano_id in plan.PLANOS_POR_ID:
        assert not (plan.funcoes_do_plano(plano_id) & set(plan.FUNCOES_CANDIDATAS))


def test_o_dict_estatico_do_plano_declara_as_mesmas_funcoes():
    assert set(plan.PLAN_PRO["funcoes"]) == plan.funcoes_do_plano("pro")
    assert set(plan.PLAN_FREE["funcoes"]) == plan.funcoes_do_plano("free")


# ===========================================================================
# 8) FRONTEIRA DE IMPORT
# ===========================================================================
def test_plan_py_nao_importa_managed_nem_options_mcp_api():
    """O catálogo DECLARA limites; quem os aplica é o gate. O import ao
    contrário criaria ciclo — `options_mcp_api` já é fiado por injeção
    justamente por isso. A varredura é por AST, não por `in`, porque a
    docstring cita os dois módulos pelo nome de propósito."""
    arvore = ast.parse(pathlib.Path(plan.__file__).read_text(encoding="utf-8"))
    importados = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(a.name.split(".")[-1] for a in no.names)
        elif isinstance(no, ast.ImportFrom):
            if no.module:
                importados.add(no.module.split(".")[-1])
            importados.update(a.name for a in no.names)
    assert "managed" not in importados
    assert "options_mcp_api" not in importados
    # sanidade: a varredura enxerga de fato o que plan.py importa
    assert "db" in importados


def test_plan_at_least_foi_removida_e_ninguem_ficou_apontando_para_ela():
    """Era órfã desde que nasceu e a docstring citava um `require_plan()` que
    nunca existiu em `main.py`. A D2 escolheu conjunto de funções, não ordem de
    tier; manter os dois mecanismos garantiria o dia da divergência."""
    assert not hasattr(plan, "plan_at_least")
    app_dir = pathlib.Path(plan.__file__).resolve().parent
    for py in app_dir.glob("*.py"):
        texto = py.read_text(encoding="utf-8")
        # a nota de remoção em `plan.py` cita o nome de propósito (é história,
        # e história não se apaga); o que não pode voltar é CHAMADA ou
        # definição.
        assert "plan_at_least(" not in texto, py.name
        assert "def plan_at_least" not in texto, py.name
    # `_ORDEM_PLANO` FICA: tem consumidor real (main.py ordena por ela)
    assert plan._ORDEM_PLANO == ["free", "pro"]
