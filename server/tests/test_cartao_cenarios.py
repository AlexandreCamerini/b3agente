"""Fase 46-03 Task 2 — cenarios_da_estrutura / didatica_estrutura sobre o motor puro."""
import pytest

from app import cartao_posicao as cp
from app import opcoes_payoff, skill_ref

VENC = "2026-10-16"


def _acao(qtd, pm):
    return {"tipo": "ACAO", "lado": "compra", "strike": 0, "premio": pm, "quantidade": qtd}


def _perna(tipo, lado, k, premio, qtd):
    return {"tipo": tipo, "lado": lado, "strike": k, "premio": premio, "quantidade": qtd,
            "vencimento": VENC}


def _faixa(entrada):
    """Mesma forma de `estrutura_posicao._faixa`."""
    perfil = opcoes_payoff.perfil_da_estrutura(entrada)
    puts = [p["strike"] for p in entrada if p["tipo"] == "PUT" and p["lado"] == "compra"]
    calls = [p["strike"] for p in entrada if p["tipo"] == "CALL" and p["lado"] == "venda"]
    return {"piso": max(puts) if puts else None, "teto": min(calls) if calls else None,
            "perdaMaxima": None if perfil["perda_maxima"] is None else round(perfil["perda_maxima"], 2),
            "ganhoMaximo": None if perfil["ganho_maximo"] is None else round(perfil["ganho_maximo"], 2),
            "breakevens": [round(b, 2) for b in perfil["breakevens"]],
            "qtdBase": entrada[0]["quantidade"], "qtdPut": 0, "textos": []}


UGPA3 = [_acao(1000, 39.50), _perna("CALL", "venda", 42.25, 1.49, 1000)]
CXSE3 = [_acao(1000, 20.06), _perna("CALL", "venda", 21.02, 0.25, 1000)]
COLLAR = [_acao(100, 50), _perna("PUT", "compra", 45, 1, 100), _perna("CALL", "venda", 56, 1.5, 100)]


def C(entrada=UGPA3, nome="call_coberta", spot=40.10, modo="operador", faixa=None):
    f = _faixa(entrada) if faixa is None else faixa
    return cp.cenarios_da_estrutura(entrada, f, nome, spot, VENC, "UGPA3", modo)


def test_ugpa3_numeros():
    c = C()
    assert c["be"] == 38.01 and c["k"] == 42.25 and c["piso"] is None
    assert c["hoje"] == 40.10
    assert c["altaForte"] == 46.05
    assert c["ateBePct"] == -5.2 and c["ateKPct"] == 5.4
    assert c["vencimentoTexto"] == "16/10"
    assert c["faixaAria"]


def test_cxse3_grade():
    g = {x["chave"]: x for x in C(CXSE3, spot=20.5)["grade"]}
    assert g["be"]["valor"] == 19.81
    assert g["ganho_max"]["valor"] == 1210.0
    assert g["perda_max"]["valor"] == -19810.0


def test_operador_grade_e_payoff():
    c = C()
    assert c["simulador"] is None
    g = c["grade"]
    assert [x["chave"] for x in g] == ["be", "ate_be", "ate_k", "ganho_max", "perda_max", "lastro"]
    d = {x["chave"]: x for x in g}
    assert d["be"]["conta"] == {"formula": "BE = PM − prêmio", "numeros": "39,50 − 1,49 = 38,01"}
    assert d["ganho_max"]["conta"]["numeros"] == "(42,25 − 38,01) × 1.000 = 4.240,00"
    assert d["perda_max"]["valor"] == -38010.0 and d["perda_max"]["formato"] == "moeda_sinal"
    assert d["lastro"]["valor"] == 1000 and d["lastro"]["formato"] == "qtd"
    assert d["ate_be"]["conta"]["numeros"] == "38,01 ÷ 40,10 − 1 = −5,2%"
    assert d["be"]["formato"] == "preco" and d["ate_be"]["formato"] == "pct"
    pts = c["payoff"]["pontos"]
    assert [p["preco"] for p in pts] == sorted({p["preco"] for p in pts})
    assert any(p["preco"] == 38.01 and p["resultado"] == 0.0 for p in pts)
    assert c["payoff"]["aria"]
    assert c["payoff"]["yMin"] == min(p["resultado"] for p in pts)


def test_educacional_simulador():
    c = C(modo="educacional")
    assert c["payoff"] is None and c["grade"] is None
    s = c["simulador"]
    pts = s["pontos"]
    assert len(pts) <= cp.MAX_PONTOS_GRADE
    assert abs(s["passo"] / cp.TICK - round(s["passo"] / cp.TICK)) < 1e-9
    precos = [p["preco"] for p in pts]
    assert precos == sorted(set(precos))
    n = s["nomeados"]
    assert pts[n["equilibrio"]]["preco"] == 38.01 and pts[n["equilibrio"]]["resultado"] == 0.0
    assert pts[n["teto"]]["preco"] == 42.25 and pts[n["teto"]]["resultado"] == 4240.0
    assert pts[n["alta_forte"]]["preco"] == 46.05
    assert pts[n["hoje"]]["preco"] == 40.1

    def zona(preco):
        return min(pts, key=lambda p: abs(p["preco"] - preco))["zona"]
    assert zona(37) == "prejuizo" and zona(40) == "ganho" and zona(43) == "ganho_travado"
    assert s["zonas"]["prejuizo"]["texto"].startswith("Abaixo do equilíbrio")
    assert "perda_travada" not in s["zonas"]
    assert s["min"] == precos[0] and s["max"] == precos[-1]


def test_spot_none():
    c = C(spot=None, modo="educacional")
    assert c["hoje"] is None and c["ateBePct"] is None and c["ateKPct"] is None
    assert c["simulador"]["nomeados"]["hoje"] is None
    assert c["be"] == 38.01 and c["k"] == 42.25 and c["altaForte"] == 46.05
    g = {x["chave"]: x for x in C(spot=None)["grade"]}
    assert g["ate_be"]["valor"] is None and g["ate_be"]["conta"] is None


def test_collar():
    c = C(COLLAR, nome="collar", spot=50, modo="educacional")
    assert c["piso"] == 45 and c["k"] == 56
    s = c["simulador"]
    assert "perda_travada" in s["zonas"]
    assert min(s["pontos"], key=lambda p: abs(p["preco"] - 40))["zona"] == "perda_travada"
    g = {x["chave"]: x for x in C(COLLAR, nome="collar", spot=50)["grade"]}
    assert g["be"]["conta"] is None and g["ganho_max"]["conta"] is None
    assert g["perda_max"]["conta"] is None
    assert g["ate_be"]["conta"] is not None


def test_invalidos():
    f = _faixa(UGPA3)
    assert cp.cenarios_da_estrutura(UGPA3, None, "call_coberta", 40, VENC, "X", "operador") is None
    assert C(faixa={**f, "breakevens": []}) is None
    assert C(faixa={**f, "breakevens": [1.0, 2.0]}) is None
    assert cp.cenarios_da_estrutura([], f, "call_coberta", 40, VENC, "X", "operador") is None
    assert cp.cenarios_da_estrutura(None, f, "call_coberta", 40, VENC, "X", "operador") is None


def test_mesmo_motor_que_opcoes_payoff():
    c = C(modo="educacional")
    for p in c["simulador"]["pontos"][::37]:
        assert p["resultado"] == round(opcoes_payoff.resultado_no_vencimento(UGPA3, p["preco"]), 2)
    for p in C()["payoff"]["pontos"]:
        assert p["resultado"] == round(opcoes_payoff.resultado_no_vencimento(UGPA3, p["preco"]), 2)


def test_teto_de_pontos_preco_alto():
    e = [_acao(100, 480), _perna("CALL", "venda", 500, 5, 100)]
    c = C(e, spot=480, modo="educacional")
    s = c["simulador"]
    assert len(s["pontos"]) <= cp.MAX_PONTOS_GRADE and s["passo"] >= cp.TICK
    # nomeados continuam com o preço exato
    assert s["pontos"][s["nomeados"]["teto"]]["preco"] == 500


def test_didatica_call_coberta():
    e = UGPA3
    c = C(modo="educacional")
    d = cp.didatica_estrutura("call_coberta", _faixa(e), e, c, {"quantidade": 1000, "precoMedio": 39.5},
                              [_perna("CALL", "venda", 42.25, 1.49, 1000)], "UGPA3", "educacional")
    termos = [s["termo"] for s in d["paragrafo"] if "termo" in s]
    assert termos == ["lastro", "call_coberta", "teto", "equilibrio", "piso"]
    casos = {s["termo"]: s for s in d["paragrafo"] if "termo" in s}
    assert casos["piso"]["noSeuCaso"] == skill_ref.cartao_didatica_txt(
        "caso_sem_piso", perdaMaxima="38.010,00")
    for s in casos.values():
        assert s["kb"] == cp.TERMO_KB[s["termo"]] and s["noSeuCaso"]
    assert d["borisExplica"]
    assert all("[[" not in x.get("texto", "") for x in d["paragrafo"])


def test_didatica_composta_e_operador():
    e = UGPA3
    d = cp.didatica_estrutura(None, _faixa(e), e, None, None, [], "UGPA3", "educacional")
    casos = {s["termo"]: s["noSeuCaso"] for s in d["paragrafo"] if "termo" in s}
    assert casos["piso"] == casos["teto"] == skill_ref.cartao_didatica_txt("caso_aguardando")
    assert d["borisExplica"] == skill_ref.cartao_didatica_txt("explica_composta")
    assert cp.didatica_estrutura("call_coberta", _faixa(e), e, C(), None, [], "UGPA3", "operador") is None
