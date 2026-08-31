"""Fase 14, Plano 03 — motor de proposta de opções lastreadas (venda coberta
e put de proteção).

Parte 1 (Task 1): vocabulário canônico por modo (`skill_ref.OPCOES_LASTREADAS`
/ `opcoes_lastreadas_txt`) — guardião de registro (Operador ordena, Estudo
descreve condição) e do helper `num_br`.

Parte 2 (Task 2): motor puro `opcoes_lastreadas.propor`/`put_sem_lastro` — sem
rede, sem banco, sem LLM; cadeia sintética montada no próprio teste.
"""
from app import skill_ref


# --------------------------- Parte 1: vocabulário ---------------------------

def test_vocab_chaves_de_operacao_existem_nos_dois_modos():
    for modo in ("operador", "educacional"):
        assert "call_coberta" in skill_ref.OPCOES_LASTREADAS[modo]
        assert "put_protecao" in skill_ref.OPCOES_LASTREADAS[modo]


def test_vocab_operador_fala_como_mesa_verbo_de_ordem():
    frase = skill_ref.OPCOES_LASTREADAS["operador"]["call_coberta"]
    assert frase.startswith("Vender")
    frase_put = skill_ref.OPCOES_LASTREADAS["operador"]["put_protecao"]
    assert frase_put.startswith("Comprar")


def test_vocab_educacional_descreve_condicao_nunca_ordem():
    frase = skill_ref.OPCOES_LASTREADAS["educacional"]["call_coberta"]
    assert frase.startswith("Se você tivesse")
    frase_put = skill_ref.OPCOES_LASTREADAS["educacional"]["put_protecao"]
    assert frase_put.startswith("Se você tivesse")


def test_vocab_txt_modo_desconhecido_cai_no_educacional():
    esperado = skill_ref.opcoes_lastreadas_txt("educacional", "sem_lastro", ticker="PETR4")
    obtido = skill_ref.opcoes_lastreadas_txt("modo-inexistente", "sem_lastro", ticker="PETR4")
    assert obtido == esperado


def test_vocab_txt_interpolacao_completa_nao_deixa_marcador_solto():
    frase = skill_ref.opcoes_lastreadas_txt(
        "operador", "call_coberta", n="1", ticker="PETR4", strike="30,00", premioTotal="150,00")
    assert "{" not in frase and "}" not in frase


def test_vocab_txt_aliases_sem_setup_caem_na_mesma_frase():
    base = skill_ref.opcoes_lastreadas_txt("operador", "sem_setup", ticker="PETR4")
    for alias in ("tendencia_de_alta", "sem_contrato_liquido", "sem_vencimento_elegivel"):
        assert skill_ref.opcoes_lastreadas_txt("operador", alias, ticker="PETR4") == base


def test_num_br_formata_pt_br_sem_locale():
    assert skill_ref.num_br(1234.5) == "1.234,50"
    assert skill_ref.num_br(0) == "0,00"
    assert skill_ref.num_br(-42.1) == "-42,10"
