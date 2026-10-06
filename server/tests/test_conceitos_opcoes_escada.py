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


# --- Fase 48 (2026-10-05), plano 48-05, onda 2: put protetora e collar --------
DADOS_PUT = {"ticker": "PETR4", "strike": 36, "premio": 0.85, "premioTotal": 255,
             "qtd": 300, "venc": "20/11", "perdaTotal": 855}
DADOS_COLLAR = {"ticker": "PETR4", "strikePut": 36, "strikeCall": 40, "liquido": -75,
                "qtd": 300, "venc": "20/11", "perdaTotal": 900, "ganhoTotal": 1100,
                "estado": "custa"}


def test_put_protetora_ancora_numeros_e_nao_promete():
    for modo in ("educacional", "operador"):
        c = conceitos.montar("opc-put-protetora", modo, DADOS_PUT)
        corpo = _tudo(c)
        assert "PETR4" in corpo and "300" in corpo
        assert "R$ 36,00" in corpo and "R$ 855,00" in corpo
        assert "{" not in corpo and "}" not in corpo
        assert "proteção total" not in corpo.lower().replace("nem proteção total", "")
        assert "sem risco" not in corpo.lower()
    e = conceitos.montar("opc-put-protetora", "educacional", DADOS_PUT)
    assert "limita a perda, não a queda" in _tudo(e)


def test_collar_estado_custa_nao_traz_paragrafo_recebe():
    c = conceitos.montar("opc-collar", "operador", DADOS_COLLAR)
    corpo = _tudo(c)
    assert c["oQueE"][0] == conceitos.TEXTO_OPC["opc-collar"]["operador"]
    assert "um custo que você paga" in corpo and "R$ 75,00" in corpo and "R$ -" not in corpo
    assert "mais que paga a put" not in corpo
    assert "R$ 36,00" in corpo and "R$ 40,00" in corpo
    assert "{" not in corpo and "}" not in corpo


def test_collar_estado_recebe_e_zero():
    rec = _tudo(conceitos.montar("opc-collar", "educacional",
                                 {**DADOS_COLLAR, "liquido": 50, "estado": "recebe"}))
    assert "mais que paga a put" in rec and "um custo que você paga" not in rec
    zero = _tudo(conceitos.montar("opc-collar", "educacional",
                                  {**DADOS_COLLAR, "liquido": 0, "estado": "zero"}))
    assert "paga exatamente a put" in zero


def test_onda2_sem_dados_sem_chave_e_sem_numero():
    for cid in ("opc-put-protetora", "opc-collar"):
        for modo in ("educacional", "operador"):
            corpo = _tudo(conceitos.montar(cid, modo, None))
            assert "{" not in corpo and "}" not in corpo and "R$" not in corpo, (cid, modo)


def test_setores_onda2_registrados():
    s = conceitos.setores()
    assert s["opc_put_protetora"] == "opc-put-protetora"
    assert s["opc_collar"] == "opc-collar"


def test_termos_dos_objetivos_com_setor_existem_em_setores():
    """Todo termo tocável de objetivos() com `setor` aponta para SETORES (e todo
    `kb` para verbete existente) — a tela 2 não pode ter link fantasma."""
    from app import opcoes_escada
    pos = {"qty": 1000, "qtyTravada": 0}
    ids_kb = {v["id"] for v in kb.catalogo()}
    for modo in ("educacional", "operador"):
        for obj in opcoes_escada.objetivos(pos, modo):
            for t in obj["termos"]:
                if t["setor"]:
                    assert t["setor"] in conceitos.setores(), t
                if t["kb"] and ids_kb is not None:
                    assert t["kb"] in ids_kb, t


def test_verbetes_onda2_nos_dois_modos_mesma_fonte_e_veja_valido():
    cat = {v["id"]: v for v in kb.catalogo()}
    for vid in ("opc-put-protetora", "opc-collar"):
        v = cat[vid]
        assert v["texto"] is conceitos.TEXTO_OPC[vid] or v["texto"] == conceitos.TEXTO_OPC[vid]
        for modo in ("educacional", "operador"):
            f = kb.formatar(v, modo)
            assert f["texto"] == conceitos.TEXTO_OPC[vid][modo]
    for v in cat.values():
        for alvo in v.get("veja") or []:
            assert alvo in cat, (v["id"], alvo)
    assert {"opc-put-protetora", "opc-collar"} <= set(cat["opc-premio"]["veja"])
    assert {"opc-put-protetora", "opc-collar"} <= set(cat["opc-perda-maxima"]["veja"])
