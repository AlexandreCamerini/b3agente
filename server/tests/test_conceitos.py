"""Camada de entendimento (Fase 1) — catálogo determinístico de conceitos.

O que estes guardiões travam:
  • Princípio 1 na didática: campo ausente NUNCA vira estimativa — o parágrafo
    que dependia dele desaparece inteiro.
  • Ordem das respostas: "o que NÃO acontece" primeiro. Quem acabou de ver
    "condição atingida" pergunta antes de tudo se o app comprou alguma coisa.
  • Vocabulário por modo, com a mesma lei do skill_ref.
  • Chave de desligamento: com a flag ligada, a camada some sem deploy de app.
  • Custo zero: nenhum caminho deste módulo chama LLM.
"""
import os

import pytest

from app import conceitos


@pytest.fixture(autouse=True)
def _flags_limpas():
    antes = {k: os.environ.get(k) for k in ("B3_DIDATICA_OFF", "B3_ASSISTENTE_OFF")}
    for k in antes:
        os.environ.pop(k, None)
    yield
    for k, v in antes.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


DADOS = {"ticker": "PETR4", "entrada": 38.5, "stop": 36.2, "estado": "armado",
         "distancia": 0.45, "distanciaEmR": 0.9}


def _tudo(c):
    return " ".join(c["naoAcontece"] + c["oQueE"] + c["oQueAcontece"])


# ---------------------------------------------------------------- Princípio 1
def test_campo_ausente_derruba_o_paragrafo_em_vez_de_estimar():
    """Sem `entrada`, o parágrafo que citaria o preço some — e nenhum outro
    número aparece no lugar dele."""
    c = conceitos.montar("gatilho", "educacional", {"ticker": "PETR4"})
    corpo = _tudo(c)
    assert "38,50" not in corpo
    assert "{entrada}" not in corpo and "{" not in corpo  # nada de placeholder cru
    assert "PETR4" not in corpo  # o parágrafo do ticker citava a entrada junto


def test_numeros_do_card_aparecem_formatados_em_pt_br():
    c = conceitos.montar("gatilho", "educacional", DADOS)
    corpo = _tudo(c)
    assert "R$ 38,50" in corpo and "R$ 36,20" in corpo
    assert "0,9R" in corpo and "R$ 0,45" in corpo
    assert "38.5" not in corpo and "0.9R" not in corpo  # ponto decimal é bug de idioma


def _do_timing(close):
    """Monta os `dados` a partir da saída REAL do timing — não à mão.

    A versão anterior deste teste construía o caso "atingido" no braço, e por
    isso concordava com o bug que ele deveria pegar: `excedenteEmR` volta em
    DOIS estados (timing.py:126 `esticado`, :130 `gatilho`) e o catálogo tinha
    um parágrafo só, com o texto do `esticado`. Fixture escrito à mão não
    consegue reproduzir a distinção que o código de produção faz."""
    from app import timing
    plano = {"decisao": "COMPRAR", "lado": "alta", "entrada": 38.5,
             "stop": 36.2, "riscoPorAcao": 2.3, "setup": "rompimento"}
    r = timing.avaliar(plano, {"close": close, "asOf": "2026-08-05 14:15",
                               "cobertura": 1.0, "lacuna": False})
    return {"ticker": "PETR4", **{k: r.get(k) for k in
                                  ("estado", "entrada", "stop", "distancia",
                                   "distanciaEmR", "excedenteEmR")}}


def test_texto_do_gatilho_difere_do_texto_do_esticado():
    """O caso que originou: `gatilho` e `esticado` carregam o MESMO campo
    (`excedenteEmR`) e pedem leituras OPOSTAS. Um texto só para os dois dizia
    'movimento esticado — não persiga' no instante exato em que a condição
    acabou de valer, que é justamente quando o iniciante abre a explicação."""
    d_gat = _do_timing(38.6)      # cruzou dentro da zona ⇒ gatilho
    d_est = _do_timing(41.0)      # cruzou muito além ⇒ esticado
    assert d_gat["estado"] == "gatilho" and d_est["estado"] == "esticado"
    gat = _tudo(conceitos.montar("gatilho", "educacional", d_gat))
    est = _tudo(conceitos.montar("gatilho", "educacional", d_est))
    assert gat != est, "o mesmo texto para os dois estados ensina o oposto num deles"
    assert "esticado" in est.lower() and "não perseguir" in est.lower()
    assert "esticado" not in gat.lower() and "não perseguir" not in gat.lower()
    assert "a condição valeu" in gat.lower()


# Marcadores do parágrafo CONDICIONAL de cada estado (o resto do texto é comum
# aos três, e frases genéricas como "passou a valer" não servem de sonda).
MARCA = {"armado": "neste momento falta", "gatilho": "a condição valeu",
         "esticado": "longe demais"}


@pytest.mark.parametrize("close,esperado", [(37.0, "armado"), (38.6, "gatilho"), (41.0, "esticado")])
def test_cada_estado_traz_o_SEU_paragrafo_e_nenhum_outro(close, esperado):
    d = _do_timing(close)
    assert d["estado"] == esperado
    corpo = " ".join(conceitos.montar("gatilho", "educacional", d)["oQueAcontece"]).lower()
    assert MARCA[esperado] in corpo
    for outro, marca in MARCA.items():
        if outro != esperado:
            assert marca not in corpo


def test_sem_estado_nenhum_paragrafo_condicional_entra():
    """Catálogo genérico (sem card): nada de afirmar estado que não existe."""
    corpo = " ".join(conceitos.montar("gatilho", "educacional",
                                      {"ticker": "PETR4"})["oQueAcontece"]).lower()
    for marca in MARCA.values():
        assert marca not in corpo


# --------------------------------------------------------- ordem e conteúdo
def test_primeira_resposta_e_que_o_app_nao_compra_nada():
    c = conceitos.montar("gatilho", "educacional", DADOS)
    primeira = c["naoAcontece"][0].lower()
    assert "não compra" in primeira and "ordem" in primeira
    # e ela vem ANTES da definição na estrutura servida ao front
    chaves = list(c)
    assert chaves.index("naoAcontece") < chaves.index("oQueE") < chaves.index("oQueAcontece")


def test_idade_do_dado_esta_no_texto_e_nao_se_gradua_por_experiencia():
    """ADR-001: afirmação de timing carrega a idade. Isso não é 'profundidade'
    — não pode sumir no modo resumido do usuário avançado."""
    for resumido in (False, True):
        c = conceitos.montar("gatilho", "educacional", DADOS, resumido=resumido)
        corpo = " ".join(c["oQueAcontece"]).lower()
        assert "15 minutos de atraso" in corpo
        assert "vela fechada" in corpo or "vela FECHADA".lower() in corpo


def test_resumido_corta_a_definicao_e_PRESERVA_os_numeros_do_card():
    """Quem já sabe o que é um gatilho é exatamente quem não precisa do texto
    de manual — e continua precisando dos números DELE. O corte era ao
    contrário: guardava a definição genérica e jogava fora o preço do card."""
    cheio = conceitos.montar("gatilho", "educacional", DADOS)
    curto = conceitos.montar("gatilho", "educacional", DADOS, resumido=True)
    assert len(curto["oQueE"]) == len(cheio["oQueE"]) - 1
    assert "R$ 38,50" in " ".join(curto["oQueE"])          # o número ficou
    assert cheio["oQueE"][0] not in curto["oQueE"]          # a definição saiu
    assert curto["naoAcontece"] == cheio["naoAcontece"]
    assert curto["oQueAcontece"] == cheio["oQueAcontece"]


def test_resumido_nao_esvazia_bloco_de_um_paragrafo_so():
    c = conceitos.montar("gatilho", "educacional", {"ticker": "PETR4"}, resumido=True)
    assert len(c["oQueE"]) >= 1


# ------------------------------------------------------------- allowlist
def test_chamador_nao_reescreve_o_vocabulario_canonico():
    """`campos` é ALLOWLIST, não documentação. Sem isso, um dict do cliente
    reescreveria o rótulo do modo — e o guardião de verbo de ordem, que varre
    o catálogo ESTÁTICO, não teria como pegar."""
    c = conceitos.montar("gatilho", "educacional",
                         {**DADOS, "rotuloAtingido": "COMPRE AGORA",
                          "rotuloArmado": "x", "nivel": "y"})
    corpo = _tudo(c)
    assert "COMPRE AGORA" not in corpo
    assert "CONDIÇÃO ATINGIDA" in corpo and "CONDIÇÃO ARMADA" in corpo


def test_campo_fora_da_allowlist_e_ignorado():
    c = conceitos.montar("gatilho", "educacional", {**DADOS, "xpto": "<script>"})
    assert "<script>" not in _tudo(c)


def test_todo_placeholder_do_catalogo_tem_de_onde_vir():
    """GUARDIÃO ESTÁTICO. Um `{campo}` que não esteja em `campos` (allowlist),
    em `ROTULOS` ou nas constantes do produto é descartado por `_render` em
    SILÊNCIO — o parágrafo simplesmente nunca renderiza, para ninguém, em
    nenhum estado. O guardião do catálogo genérico não pega: ele só confere
    que não sobrou `{`, que é exatamente o que o descarte produz.

    Com sete conceitos este modo de falha fica invisível na revisão manual."""
    import re
    disponiveis = set(conceitos.ROTULOS["educacional"]) | set(conceitos._constantes())
    for cid, c in conceitos.CONCEITOS.items():
        permitidos = disponiveis | set(c.get("campos") or ())
        for bloco in ("naoAcontece", "oQueE", "oQueAcontece"):
            for p in c[bloco]:
                texto = p[1] if isinstance(p, tuple) else p
                for campo in re.findall(r"\{(\w+)\}", texto):
                    assert campo in permitidos, (
                        f"{cid}.{bloco}: '{{{campo}}}' não está em `campos` nem "
                        "nos rótulos/constantes — o parágrafo nunca vai renderizar")


def test_risco_por_acao_negativo_nao_vira_texto():
    """Achado na verificação ao vivo: com stop no lucro (trailing), `avg - stop`
    fica negativo e o conceito dizia "1R vale R$ -4,12 por ação" — número sem
    significado, justamente no conceito que ensina a medir risco."""
    c = conceitos.montar("r", "educacional", {"ticker": "PETR4", "riscoPorAcao": -4.12})
    assert "-4,12" not in _tudo(c) and "1R vale" not in _tudo(c)
    ok = conceitos.montar("r", "educacional", {"ticker": "PETR4", "riscoPorAcao": 2.3})
    assert "R$ 2,30" in _tudo(ok)


def test_veja_so_aponta_para_conceito_que_existe():
    for c in conceitos.catalogo("educacional"):
        for v in c["veja"]:
            assert v in conceitos.CONCEITOS, f"'veja' aponta para id fantasma: {v}"


# ------------------------------------------------------------------ vocabulário
def test_vocabulario_por_modo_usa_o_rotulo_que_o_usuario_esta_vendo():
    edu = _tudo(conceitos.montar("gatilho", "educacional", DADOS))
    ope = _tudo(conceitos.montar("gatilho", "operador", DADOS))
    assert "CONDIÇÃO ARMADA" in edu and "CONDIÇÃO ATINGIDA" in edu
    assert "PLANO ARMADO" in ope and "GATILHO ATINGIDO" in ope
    assert "PLANO ARMADO" not in edu and "CONDIÇÃO ARMADA" not in ope


def test_modo_desconhecido_cai_no_educacional():
    assert conceitos.montar("gatilho", "xpto", DADOS)["titulo"] == \
        conceitos.montar("gatilho", "educacional", DADOS)["titulo"]


# ------------------------------------------------------- chave de desligamento
def test_flag_desliga_a_camada_inteira_sem_deploy_de_app():
    os.environ["B3_DIDATICA_OFF"] = "1"
    assert conceitos.didatica_ligada() is False
    assert conceitos.montar("gatilho", "educacional", DADOS) is None
    assert conceitos.catalogo("educacional") == []
    # e o assistente é INDEPENDENTE: desligar a didática não o derruba
    assert conceitos.assistente_ligado() is True


def test_flag_do_assistente_e_independente():
    os.environ["B3_ASSISTENTE_OFF"] = "1"
    assert conceitos.assistente_ligado() is False
    assert conceitos.didatica_ligada() is True
    assert conceitos.montar("gatilho", "educacional", DADOS) is not None


# ------------------------------------------------------------------- higiene
def test_id_inexistente_nao_explode():
    assert conceitos.montar("nao-existe", "educacional", None) is None


def test_catalogo_generico_nao_carrega_numero_de_ativo_nenhum():
    for c in conceitos.catalogo("educacional"):
        corpo = _tudo(c)
        assert "R$" not in corpo and "{" not in corpo


def test_nenhum_caminho_do_modulo_chama_llm():
    import inspect
    src = inspect.getsource(conceitos)
    assert "llm" not in src.replace("nenhuma chamada de LLM", "").replace("LLM", "")
