"""Fase 27 — o índice de vigias e o namespacing do nome, OFFLINE e sem rota.

O que este arquivo trava, em uma frase cada:
  - o prefixo NÃO carrega o uid (o nome viaja para um serviço de terceiro e
    fica visível a todos os clientes dele — ADR-027 Decisão 7);
  - prefixar duas vezes não empilha dois prefixos, porque o ida-e-volta
    ensaio → gravação passa o nome por `nome_no_servico` mais de uma vez;
  - o nome de OUTRO dono não vira meu por passar pelas funções deste módulo;
  - o isolamento entre usuários é NÃO-VÁCUO: gravar por dois uids e listar por
    cada um devolve só o dele (é este teste que reprova `e_meu -> True`);
  - legado (sem prefixo nenhum) é reconhecido como tal — é o que mantém um
    órfão removível, decisão do Alex de 2026-09-13;
  - o índice não guarda estado (`armed`/`streak`): estado é medição do
    serviço, e guardá-lo aqui produziria "armado" carimbado de ontem.

Nada aqui toca rede, `mcp_client` ou LLM: o módulo sob teste é puro em
relação à rede e recebe a conexão pronta.
"""
from __future__ import annotations

import sqlite3

import pytest

from app import db
from app import opcoes_vigias as V

UID_A = "u-123"
UID_B = "u-456"


@pytest.fixture()
def conn() -> sqlite3.Connection:
    c = db.connect(":memory:")
    db.init_db(c)
    yield c
    c.close()


# --------------------------- o prefixo -------------------------------------

def test_prefixo_e_estavel_e_distingue_contas():
    assert V.prefixo(UID_A) == V.prefixo(UID_A)
    assert V.prefixo(UID_A) != V.prefixo(UID_B)


def test_prefixo_tem_a_forma_declarada():
    p = V.prefixo(UID_A)
    assert len(p) == V.PREFIXO_TAM + len(V.SEPARADOR)
    assert p.endswith(V.SEPARADOR)
    miolo = p[: V.PREFIXO_TAM]
    assert miolo == miolo.lower()
    assert all(c in "0123456789abcdef" for c in miolo)


def test_prefixo_nao_carrega_o_identificador_da_conta():
    # O nome viaja para fora e fica visível a todos os clientes do serviço:
    # identificador de conta em nome público é vazamento, não organização.
    for uid in (UID_A, "alexandre.camerini@gmail.com", "9f2b"):
        assert uid not in V.prefixo(uid)


# ------------------- ida e volta entre os dois nomes ------------------------

def test_nome_no_servico_prefixa_o_nome_da_pessoa():
    assert V.nome_no_servico(UID_A, "IFR baixo") == V.prefixo(UID_A) + "IFR baixo"


def test_nome_no_servico_e_idempotente():
    # O ensaio devolve o setup para a tela e a tela o manda de volta para
    # gravar. Sem isto, um único ida-e-volta viraria "abcdef12-abcdef12-…".
    uma = V.nome_no_servico(UID_A, "IFR baixo")
    duas = V.nome_no_servico(UID_A, uma)
    assert duas == uma
    assert V.nome_no_servico(UID_A, duas) == uma


def test_nome_de_outro_dono_nao_vira_meu_ao_ser_prefixado():
    do_outro = V.nome_no_servico(UID_B, "IFR baixo")
    meu = V.nome_no_servico(UID_A, do_outro)
    assert meu == V.prefixo(UID_A) + do_outro
    assert V.e_meu(UID_A, meu) is True
    assert V.e_meu(UID_B, meu) is False


def test_nome_do_usuario_desfaz_o_proprio_prefixo():
    assert V.nome_do_usuario(UID_A, V.nome_no_servico(UID_A, "IFR baixo")) == "IFR baixo"


def test_nome_do_usuario_e_idempotente_sem_prefixo():
    assert V.nome_do_usuario(UID_A, "legado sem prefixo") == "legado sem prefixo"
    assert V.nome_do_usuario(UID_A, V.nome_do_usuario(UID_A, "legado sem prefixo")) \
        == "legado sem prefixo"


def test_nome_do_usuario_nao_desfaz_o_prefixo_de_outro():
    do_outro = V.nome_no_servico(UID_B, "IFR baixo")
    assert V.nome_do_usuario(UID_A, do_outro) == do_outro


# --------------------------- de quem é o nome -------------------------------

def test_e_meu_so_para_o_proprio_prefixo():
    assert V.e_meu(UID_A, V.nome_no_servico(UID_A, "x")) is True
    assert V.e_meu(UID_A, V.nome_no_servico(UID_B, "x")) is False
    assert V.e_meu(UID_A, "legado sem prefixo") is False
    assert V.e_meu(None, V.nome_no_servico(UID_A, "x")) is False


def test_e_legado_so_para_nome_sem_prefixo_nenhum():
    # Prefixado é prefixado, mesmo sendo de outra conta: "sem dono conhecido"
    # e "de outro dono" são razões DIFERENTES para não aparecer numa lista.
    assert V.e_legado("IFR baixo") is True
    assert V.e_legado("media longa + oscilador esticado") is True
    assert V.e_legado(V.nome_no_servico(UID_A, "x")) is False
    assert V.e_legado(V.nome_no_servico(UID_B, "x")) is False
    # O setup gravado na Task 0 contra o serviço real: casa o formato, e por
    # isso é "de outro dono" — não legado (medido em 2026-09-13).
    assert V.e_legado("abcdef12-teste-fase-27") is False


def test_e_legado_nao_confunde_hifen_solto_com_prefixo():
    assert V.e_legado("PETR4-IFR") is True
    assert V.e_legado("abcdefg1-x") is True        # 'g' não é hexadecimal
    assert V.e_legado("ABCDEF12-x") is True        # maiúscula não é o formato
    assert V.e_legado("abcdef1-x") is True         # sete, não oito
    assert V.e_legado("abcdef123-x") is True       # nove antes do hífen


# ----------------------------- o índice -------------------------------------

def _registra(conn, uid, nome, ticker="PETR4", criado_em="2026-09-13 10:00"):
    return V.registrar(conn, uid,
                       nome_do_usuario=nome,
                       nome_no_servico=V.nome_no_servico(uid, nome),
                       ticker=ticker, criado_em=criado_em)


def test_registrar_e_listar_guardam_o_que_o_servico_nao_sabe(conn):
    _registra(conn, UID_A, "IFR baixo", ticker="VALE3", criado_em="2026-09-13 09:30")
    itens = V.listar(conn, UID_A)
    assert len(itens) == 1
    item = itens[0]
    # `list_setups` não devolve nada disto: nem o nome da pessoa, nem dono,
    # nem data de criação. É por isso que o índice existe.
    assert item["nome"] == "IFR baixo"
    assert item["nomeNoServico"] == V.nome_no_servico(UID_A, "IFR baixo")
    assert item["ticker"] == "VALE3"
    assert item["criadoEm"] == "2026-09-13 09:30"


def test_o_indice_nao_guarda_estado(conn):
    _registra(conn, UID_A, "IFR baixo")
    item = V.listar(conn, UID_A)[0]
    # Estado é medição do serviço; guardá-lo aqui produziria um "armado"
    # carimbado de ontem exibido como se fosse de hoje (princípio 4).
    assert set(item) == {"nome", "nomeNoServico", "ticker", "criadoEm"}


def test_listar_devolve_o_mais_recente_primeiro(conn):
    _registra(conn, UID_A, "primeiro")
    _registra(conn, UID_A, "segundo")
    _registra(conn, UID_A, "terceiro")
    assert [i["nome"] for i in V.listar(conn, UID_A)] == ["terceiro", "segundo", "primeiro"]


def test_registrar_o_mesmo_nome_substitui_e_nao_duplica(conn):
    _registra(conn, UID_A, "IFR baixo", ticker="PETR4")
    _registra(conn, UID_A, "IFR baixo", ticker="VALE3")
    itens = V.listar(conn, UID_A)
    # O armazém do serviço também não duplica: dois itens aqui para um
    # registro lá seriam duas verdades sobre a mesma coisa.
    assert len(itens) == 1
    assert itens[0]["ticker"] == "VALE3"


def test_remover_tira_do_indice_e_diz_se_tirou(conn):
    _registra(conn, UID_A, "IFR baixo")
    alvo = V.nome_no_servico(UID_A, "IFR baixo")
    assert V.remover(conn, UID_A, alvo) is True
    assert V.listar(conn, UID_A) == []
    # Remover o que não existe é caminho normal (desativar um legado), não erro.
    assert V.remover(conn, UID_A, alvo) is False
    assert V.remover(conn, UID_A, "legado sem prefixo") is False


def test_isolamento_entre_usuarios_nao_e_vacuo(conn):
    # NÃO-VACUIDADE: é este teste que reprova um `e_meu` que devolva sempre
    # True e um `listar` que leia o balde de todo mundo.
    _registra(conn, UID_A, "meu vigia")
    _registra(conn, UID_B, "vigia do outro")

    nomes_a = [i["nome"] for i in V.listar(conn, UID_A)]
    nomes_b = [i["nome"] for i in V.listar(conn, UID_B)]
    assert nomes_a == ["meu vigia"]
    assert nomes_b == ["vigia do outro"]

    do_b = V.listar(conn, UID_B)[0]["nomeNoServico"]
    assert V.e_meu(UID_A, do_b) is False
    assert V.e_meu(UID_B, do_b) is True


def test_remover_de_um_uid_nao_toca_o_indice_do_outro(conn):
    _registra(conn, UID_A, "IFR baixo")
    _registra(conn, UID_B, "IFR baixo")
    # Mesmo nome escrito pelas duas pessoas: nomes no serviço DIFERENTES.
    assert V.listar(conn, UID_A)[0]["nomeNoServico"] \
        != V.listar(conn, UID_B)[0]["nomeNoServico"]
    V.remover(conn, UID_A, V.nome_no_servico(UID_A, "IFR baixo"))
    assert V.listar(conn, UID_A) == []
    assert len(V.listar(conn, UID_B)) == 1


def test_escopo_anonimo_nao_tem_vigia(conn):
    assert V.listar(conn, None) == []
    assert V.listar(conn, "") == []
    # E gravar no escopo anônimo não cria um balde compartilhado por engano.
    V.registrar(conn, None, nome_do_usuario="x", nome_no_servico="x",
                ticker="PETR4", criado_em="2026-09-13")
    assert V.listar(conn, None) == []


def test_indice_corrompido_degrada_para_vazio_e_nao_derruba(conn):
    db.kv_set(conn, V.SECAO, {"forma": "antiga"}, user_id=UID_A)
    assert V.listar(conn, UID_A) == []
    db.kv_set(conn, V.SECAO, ["lixo", 7, None], user_id=UID_A)
    assert V.listar(conn, UID_A) == []
