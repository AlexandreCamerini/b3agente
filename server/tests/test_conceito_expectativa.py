"""Fase 47 (2026-10-06), plano 47-01, DIDA-01 — conceito `expectativa-matematica`
(números do histórico medido) + verbete KB com o MESMO texto, dois modos."""
import itertools

from app import conceitos, kb

CID = "expectativa-matematica"
FRASE = "Não há dados suficientes para concluir."
ELEG = {"n": 120, "janela": "2025", "expR": 0.084, "estado": "elegivel"}
INEL = {"n": 120, "janela": "2025", "expR": -0.051, "estado": "inelegivel"}


def _tudo(c):
    return " ".join(c["naoAcontece"] + c["oQueE"] + c["oQueAcontece"])


def test_elegivel_ancora_numeros_sem_chave_sobrando():
    corpo = _tudo(conceitos.montar(CID, "educacional", ELEG))
    assert "120" in corpo and "2025" in corpo and "+0,084R" in corpo
    assert "{" not in corpo and "}" not in corpo


def test_inelegivel_usa_menos_unicode_e_paragrafo_proprio():
    corpo = _tudo(conceitos.montar(CID, "educacional", INEL))
    assert "−0,051R" in corpo
    assert "os ganhos não cobriram as perdas" in corpo
    assert "vantagem medida. Ainda é o passado" not in corpo


def test_estados_sem_dado_usam_frase_fixa_sem_resultado_medio():
    for d in ({"n": 7, "estado": "insuficiente"}, {"estado": "nunca_medido"}):
        corpo = _tudo(conceitos.montar(CID, "educacional", d))
        assert FRASE in corpo
        assert "R por ocorrência" not in corpo


def test_sem_dados_so_texto_generico():
    for modo in ("educacional", "operador"):
        c = conceitos.montar(CID, modo, None)
        assert c["oQueE"] == [conceitos.TEXTO_EXPECTATIVA[modo]]
        assert c["oQueAcontece"] == []
        assert "{" not in _tudo(c) and "}" not in _tudo(c)


def test_operador_usa_titulo_e_texto_do_modo():
    c = conceitos.montar(CID, "operador", ELEG)
    assert c["titulo"] == "Expectativa × taxa de acerto"
    assert c["oQueE"][0] == conceitos.TEXTO_EXPECTATIVA["operador"]


def test_campo_fora_da_allowlist_nao_interpola():
    assert "999" not in _tudo(conceitos.montar(CID, "educacional", {**ELEG, "preco": 999}))


def test_dado_invalido_derruba_paragrafo_nunca_vira_zero():
    corpo = _tudo(conceitos.montar(CID, "educacional", {**ELEG, "expR": None}))
    assert "0,000R" not in corpo and "por ocorrência" not in corpo
    corpo = _tudo(conceitos.montar(CID, "educacional", {**ELEG, "expR": True}))
    assert "+1,000R" not in corpo


def test_ilustracao_bate_com_a_formula_e_esta_rotulada():
    esperado = ["+0,6R", "−0,5R"]
    got = []
    for it in conceitos._ILUSTRACAO_EXPECTATIVA:
        v = round(it["acerto"] * it["ganho"] - (1 - it["acerto"]) * it["perda"], 1)
        got.append(conceitos._r_br(v, 1))
    assert got == esperado
    for modo in ("educacional", "operador"):
        t = conceitos.TEXTO_EXPECTATIVA[modo]
        assert all(x in t for x in esperado)
        assert "lustração" in t


def test_linguagem_sem_promessa():
    textos = list(conceitos.TEXTO_EXPECTATIVA.values())
    for modo, est in itertools.product(("educacional", "operador"),
                                       ("elegivel", "inelegivel", "insuficiente",
                                        "nunca_medido", "aposentado")):
        textos.append(_tudo(conceitos.montar(CID, modo, {**ELEG, "estado": est})))
    for t in textos:
        low = t.lower()
        assert "100%" not in t and "garant" not in low and "lucro certo" not in low


def test_setor_registrado_e_analise_intacto():
    s = conceitos.setores()
    assert s["expectativa"] == CID
    assert s["analise"] == "confluencia"


def test_conceitos_antigos_inalterados_pelo_formatador_novo():
    c = conceitos.montar("opc-premio", "educacional",
                         {"ticker": "PETR4", "strike": 36, "premio": 0.85, "premioTotal": 255,
                          "qtd": 300, "venc": "20/11", "estado": "pago"})
    assert "R$ 255,00" in _tudo(c) and "300" in _tudo(c)
    assert conceitos.montar("confluencia", "educacional", None)["id"] == "confluencia"
