"""Fase 15, Plano 02 — `opcoes_gatilho.do_plano()`: plano do Radar vira
decisão de avaliar estrutura de opções (ENG-06).

Parte 1 (Task 1): comportamento de `do_plano` — um teste por item do
`<behavior>` do plano, incluindo entrada ausente/malformada/desconhecida.

Parte 2 (Task 2, acrescentada depois): dois guardiões — paridade com
`opcoes_lastreadas.propor()` em produção e proibição estrutural da DSL de
setups do b-mcp.
"""
from app.opcoes_gatilho import do_plano, VIES_PROTECAO, VIES_PREMIO


# ------------------------------ Parte 1: comportamento ------------------------------

def test_vender_lado_baixa_avalia_protecao():
    r = do_plano({"decisao": "VENDER", "lado": "baixa"})
    assert r == {"avaliar": True, "vies": VIES_PROTECAO, "motivo": VIES_PROTECAO}


def test_lado_baixa_sozinho_ja_avalia_protecao():
    """`lado == "baixa"` sozinho já aciona proteção, mesma condição `or` de
    `propor()` hoje — mesmo com decisão COMPRAR."""
    r = do_plano({"decisao": "COMPRAR", "lado": "baixa"})
    assert r["vies"] == VIES_PROTECAO


def test_decisao_aguardar_vence_lado_alta_avalia_premio():
    """A decisão de aguardar confirmação vence o lado, mesma ordem de
    avaliação de `propor()`."""
    r = do_plano({"decisao": "AGUARDAR CONFIRMAÇÃO", "lado": "alta"})
    assert r["vies"] == VIES_PREMIO


def test_decisao_nao_operar_lado_none_avalia_premio():
    r = do_plano({"decisao": "NÃO OPERAR", "lado": None})
    assert r["vies"] == VIES_PREMIO


def test_lado_neutro_avalia_premio():
    r = do_plano({"decisao": "COMPRAR", "lado": "neutro"})
    assert r["vies"] == VIES_PREMIO


def test_decisao_comprar_lado_alta_nao_avalia_nenhuma_estrutura():
    r = do_plano({"decisao": "COMPRAR", "lado": "alta"})
    assert r == {"avaliar": False, "vies": None, "motivo": "sem_setup"}


def test_plano_vazio_nao_avalia():
    r = do_plano({})
    assert r["avaliar"] is False
    assert r["motivo"] == "sem_setup"


def test_plano_none_nao_avalia():
    r = do_plano(None)
    assert r["avaliar"] is False
    assert r["motivo"] == "sem_setup"


def test_plano_texto_nao_levanta_excecao_e_nao_avalia():
    r = do_plano("texto")
    assert r["avaliar"] is False
    assert r["motivo"] == "sem_setup"


def test_plano_numero_nao_levanta_excecao_e_nao_avalia():
    r = do_plano(42)
    assert r["avaliar"] is False
    assert r["motivo"] == "sem_setup"


def test_decisao_e_lado_inventados_nao_caem_em_vies_por_default():
    r = do_plano({"decisao": "decisão inventada", "lado": "lado inventado"})
    assert r["avaliar"] is False
    assert r["motivo"] == "sem_setup"


def test_retorno_tem_exatamente_tres_chaves_e_avaliar_coerente_com_vies():
    casos = [
        {"decisao": "VENDER", "lado": "baixa"},
        {"decisao": "COMPRAR", "lado": "baixa"},
        {"decisao": "AGUARDAR CONFIRMAÇÃO", "lado": "alta"},
        {"decisao": "NÃO OPERAR", "lado": None},
        {"decisao": "COMPRAR", "lado": "neutro"},
        {"decisao": "COMPRAR", "lado": "alta"},
        {},
        None,
        "texto",
        42,
        {"decisao": "x", "lado": "y"},
    ]
    for plano in casos:
        r = do_plano(plano)
        assert sorted(r.keys()) == ["avaliar", "motivo", "vies"]
        assert (r["avaliar"] is True) == (r["vies"] is not None)
