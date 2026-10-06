"""Fase 48 (2026-10-05), plano 48-02, onda 1 — termos clicáveis `prêmio` e
`perda máxima`: conceito com números do caso (conceitos.py) + verbete KB com o
MESMO texto genérico (kb.py), dois modos."""
from app import conceitos, kb

DADOS_PREMIO = {"ticker": "PETR4", "strike": 36, "premio": 0.85, "premioTotal": 255,
                "qtd": 300, "venc": "20/11", "estado": "pago"}
DADOS_PERDA = {"ticker": "PETR4", "piso": 33, "perdaTotal": 1200, "perdaAcao": 4,
               "premio": 0.85, "qtd": 300, "venc": "20/11", "estado": "com_piso"}


def _tudo(c):
    return " ".join(c["naoAcontece"] + c["oQueE"] + c["oQueAcontece"])


def test_premio_ancora_numeros_do_caso_sem_chave_sobrando():
    c = conceitos.montar("opc-premio", "educacional", DADOS_PREMIO)
    corpo = _tudo(c)
    assert "PETR4" in corpo and "300" in corpo
    assert "R$ 255,00" in corpo and "R$ 0,85" in corpo and "R$ 36,00" in corpo
    assert "20/11" in corpo
    assert "{" not in corpo and "}" not in corpo


def test_premio_operador_usa_texto_do_modo():
    c = conceitos.montar("opc-premio", "operador", DADOS_PREMIO)
    assert c["oQueE"][0] == conceitos.TEXTO_OPC["opc-premio"]["operador"]
    assert c["titulo"] == "Prêmio"
    e = conceitos.montar("opc-premio", "educacional", DADOS_PREMIO)
    assert e["oQueE"][0] == conceitos.TEXTO_OPC["opc-premio"]["educacional"]
    assert e["titulo"] != c["titulo"]


def test_perda_maxima_sem_piso_nao_traz_paragrafo_com_piso():
    d = {**DADOS_PERDA, "estado": "sem_piso"}
    corpo = _tudo(conceitos.montar("opc-perda-maxima", "educacional", d))
    assert "Sem piso: se a ação for a zero" in corpo
    assert "Abaixo do piso" not in corpo


def test_perda_maxima_com_piso_nao_traz_paragrafo_sem_piso():
    corpo = _tudo(conceitos.montar("opc-perda-maxima", "educacional", DADOS_PERDA))
    assert "Abaixo do piso de R$ 33,00" in corpo
    assert "Sem piso: se a ação" not in corpo


def test_sem_dados_so_texto_generico_sem_chave():
    for cid in ("opc-premio", "opc-perda-maxima"):
        for modo in ("educacional", "operador"):
            c = conceitos.montar(cid, modo, None)
            corpo = _tudo(c)
            assert "{" not in corpo and "}" not in corpo, (cid, modo)
            assert "R$" not in corpo, (cid, modo)
            assert c["oQueE"] == [conceitos.TEXTO_OPC[cid][modo]]


def test_campo_fora_da_allowlist_nao_interpola():
    d = {**DADOS_PREMIO, "rotuloArmado": "COMPRE AGORA"}
    assert "COMPRE AGORA" not in _tudo(conceitos.montar("opc-premio", "educacional", d))


def test_conceitos_antigos_inalterados_pelo_paragrafo_por_modo():
    dados = {"ticker": "PETR4", "entrada": 38.5, "stop": 37.0, "estado": "armado"}
    for cid in ("gatilho", "stop", "liquidez-opcao"):
        c = conceitos.CONCEITOS[cid]
        for modo in ("educacional", "operador"):
            m = conceitos.montar(cid, modo, dados)
            valores = conceitos._valores(modo, dados, c.get("campos"))
            est = dados["estado"]
            assert m["oQueE"] == conceitos._render(c["oQueE"], valores, est)
            assert m["naoAcontece"] == conceitos._render(c["naoAcontece"], valores, est)
            assert m["oQueAcontece"] == conceitos._render(c["oQueAcontece"], valores, est)
            assert m["titulo"] == c["titulo"][modo]


def test_setores_registrados_apontam_para_conceito_existente():
    s = conceitos.setores()
    assert s["opc_premio"] == "opc-premio"
    assert s["opc_perda_maxima"] == "opc-perda-maxima"
    assert all(cid in conceitos.CONCEITOS for cid in s.values())


# ---------------------------------------------------------------- KB (Task 2)
def _verbete(vid):
    return next(v for v in kb.catalogo() if v["id"] == vid)


def test_verbetes_kb_usam_o_mesmo_texto_do_conceito_nos_dois_modos():
    for vid in ("opc-premio", "opc-perda-maxima"):
        v = _verbete(vid)
        for modo in ("educacional", "operador"):
            assert v["texto"][modo].strip()
            assert v["texto"][modo] == conceitos.TEXTO_OPC[vid][modo]


def test_veja_dos_verbetes_novos_existe_no_catalogo():
    ids = {v["id"] for v in kb.catalogo()}
    for vid in ("opc-premio", "opc-perda-maxima"):
        for alvo in _verbete(vid)["veja"]:
            assert alvo in ids, (vid, alvo)


def test_piso_teto_equilibrio_seguem_como_verbetes_kb():
    ids = {v["id"] for v in kb.catalogo()}
    assert {"opc-piso", "opc-teto", "opc-equilibrio"} <= ids
