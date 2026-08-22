"""Guardião do achado C-05: "diversificação" tinha ZERO ocorrência no produto
inteiro (nem `server/app/*.py`, nem `web/src/*.js`/`*.jsx`, nem `docs/*.md`) —
um dos 13 conceitos obrigatórios da seção "Camada educacional" do CLAUDE.md da
raiz nunca era ensinado. Este arquivo trava que o conceito e o verbete
existem, respondem nos dois modos, e que o catálogo genérico continua sem
vazar número de ativo nenhum (mesma lei de `conceitos.py` inteiro).
"""
from app import conceitos, kb


def test_conceito_diversificacao_existe():
    assert "diversificacao" in conceitos.CONCEITOS


def test_verbete_diversificacao_existe_na_kb_com_familia_plano_risco():
    v = kb.verbete("diversificacao")
    assert v is not None
    assert v["familia"] == "plano_risco"
    assert v["texto"]["educacional"].strip() != ""
    assert v["texto"]["operador"].strip() != ""


def test_catalogo_generico_de_diversificacao_nao_carrega_numero_de_ativo():
    """Mesma lei do catálogo genérico inteiro (`test_conceitos.py::
    test_catalogo_generico_nao_carrega_numero_de_ativo_nenhum`): sem `dados`,
    nenhum valor de CARTEIRA (moeda) pode vazar, e nenhum placeholder pode
    ficar sem interpolar. Constante do produto (o limiar de 50%) não é número
    de ativo — é regra fixa, igual ao `rrMin`/`zona` dos vizinhos."""
    c = conceitos.montar("diversificacao", "educacional", None)
    corpo = " ".join(c["naoAcontece"] + c["oQueE"] + c["oQueAcontece"])
    assert "R$" not in corpo and "{" not in corpo
    assert "PETR4" not in corpo


def test_diversificacao_ancorada_no_card_mostra_ticker_e_percentual():
    c = conceitos.montar("diversificacao", "educacional",
                          {"ticker": "PETR4", "pct": 63})
    corpo = " ".join(c["naoAcontece"] + c["oQueE"] + c["oQueAcontece"])
    assert "PETR4" in corpo
    assert "63" in corpo


def test_diversificacao_responde_nos_dois_modos():
    edu = conceitos.montar("diversificacao", "educacional",
                            {"ticker": "PETR4", "pct": 63})
    ope = conceitos.montar("diversificacao", "operador",
                            {"ticker": "PETR4", "pct": 63})
    assert edu["titulo"] == "Diversificação"
    assert ope["titulo"] == "Diversificação"


def test_diversificacao_deixou_de_ter_zero_ocorrencia_no_produto():
    """C-05: zero ocorrência de "diversific" era o próprio achado."""
    import inspect
    assert "diversific" in inspect.getsource(conceitos).lower()
    assert "diversific" in inspect.getsource(kb).lower()


def test_diversificacao_nao_e_promessa_de_protecao():
    """CLAUDE.md princípio 6/8: sem promessa de resultado/proteção."""
    c = conceitos.montar("diversificacao", "educacional",
                          {"ticker": "PETR4", "pct": 63})
    corpo = " ".join(c["naoAcontece"]).lower()
    assert "garantia" in corpo
