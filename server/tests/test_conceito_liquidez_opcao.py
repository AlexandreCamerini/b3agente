"""Quick 260908-ldg (2026-09-08), Task 2 (D-09) — verbete didático
"liquidez-opcao" em `conceitos.py`: explica a régua de três faixas com custo
zero de LLM, ancorado nos números do card (score/faixa/volume/spreadPct)."""
from app import conceitos


def _tudo(c):
    return " ".join(c["naoAcontece"] + c["oQueE"] + c["oQueAcontece"])


DADOS = {"ticker": "ABEV3", "faixa": "DIFÍCIL", "score": 48.6, "volume": 4800, "spreadPct": 176.47}


def test_liquidez_opcao_esta_no_catalogo():
    assert "liquidez-opcao" in conceitos.ids()
    ids_catalogo = [c["id"] for c in conceitos.catalogo("educacional")]
    assert "liquidez-opcao" in ids_catalogo


def test_montar_com_dados_ancora_ticker_faixa_score():
    c = conceitos.montar("liquidez-opcao", "operador", DADOS)
    corpo = _tudo(c)
    assert "ABEV3" in corpo
    assert "DIFÍCIL" in corpo
    assert "49/100" in corpo  # score arredondado (48,6 -> 49)


def test_numeros_aparecem_formatados_em_pt_br():
    c = conceitos.montar("liquidez-opcao", "operador", DADOS)
    corpo = _tudo(c)
    assert "4.800" in corpo       # volume com ponto de milhar
    assert "176%" in corpo        # spread sem decimais
    assert "4800" not in corpo
    assert "176.47" not in corpo and "176,47" not in corpo


def test_sem_dados_texto_generico_nao_sobra_chave():
    c = conceitos.montar("liquidez-opcao", "educacional", None)
    corpo = _tudo(c)
    assert "{" not in corpo and "}" not in corpo
    assert "R$" not in corpo


def test_primeira_resposta_e_que_o_app_nao_compra_nada():
    c = conceitos.montar("liquidez-opcao", "operador", DADOS)
    assert "não compra" in c["naoAcontece"][0]


def test_volume_ou_spread_ausente_derruba_so_o_proprio_paragrafo():
    """Campo ausente nunca vira estimativa — o parágrafo que dependeria dele
    desaparece, mas o resto do verbete continua íntegro."""
    sem_spread = {"ticker": "ABEV3", "faixa": "NEGOCIÁVEL", "score": 66.5, "volume": 21100}
    c = conceitos.montar("liquidez-opcao", "operador", sem_spread)
    corpo = _tudo(c)
    assert "Spread do livro" not in corpo
    assert "ABEV3" in corpo and "NEGOCIÁVEL" in corpo

    sem_volume = {"ticker": "ABEV3", "faixa": "NEGOCIÁVEL", "score": 66.5, "spreadPct": 2.5}
    c2 = conceitos.montar("liquidez-opcao", "operador", sem_volume)
    corpo2 = _tudo(c2)
    assert "unidades negociadas hoje" not in corpo2
    assert "ABEV3" in corpo2


def test_titulo_difere_entre_operador_e_educacional():
    op = conceitos.montar("liquidez-opcao", "operador", DADOS)
    edu = conceitos.montar("liquidez-opcao", "educacional", DADOS)
    assert op["titulo"] != edu["titulo"]


def test_veja_vazio_nenhum_link_fantasma():
    c = conceitos.montar("liquidez-opcao", "educacional", DADOS)
    assert c["veja"] == []


def test_nao_esta_registrado_em_setores_acesso_e_so_por_chip():
    assert "liquidez-opcao" not in conceitos.SETORES.values()
