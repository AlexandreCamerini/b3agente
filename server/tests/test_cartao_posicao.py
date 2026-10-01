"""Fase 46-03 Task 1 — leitura_plano (motor puro do card v6)."""
import math

import pytest

from app import cartao_posicao as cp
from app import skill_ref

POS = {"t": "PETR4", "qty": 100, "avg": 30, "stop": 28, "alvo": 36}


def L(preco=32, pos=None, compras=None, modo="operador"):
    return cp.leitura_plano(POS if pos is None else pos, preco, compras, modo)


def test_plano_completo_dentro():
    r = L(32)
    assert r["ticker"] == "PETR4"
    assert r["plano"] == "completo"
    assert r["posicaoNoPlano"] == "dentro"
    assert r["distStopPct"] == -12.5
    assert r["distAlvoPct"] == 12.5
    assert r["rr"] == 1.0
    assert r["resultado"] == 200.0
    assert r["variacaoPct"] == 6.7
    assert r["resultadoNoStop"] == -200.0
    assert r["resultadoNoAlvo"] == 600.0
    assert r["reguaAria"]


def test_abaixo_stop_e_acima_alvo_sem_rr():
    r = L(27)
    assert r["posicaoNoPlano"] == "abaixo_stop" and r["rr"] is None
    r = L(37)
    assert r["posicaoNoPlano"] == "acima_alvo" and r["rr"] is None


def test_preco_none_nunca_zero():
    r = L(None)
    for k in ("preco", "resultado", "variacaoPct", "distStopPct", "distAlvoPct", "rr",
              "posicaoNoPlano"):
        assert r[k] is None, k
    assert r["plano"] == "completo"
    # stop/alvo vs PM não dependem do preço
    assert r["resultadoNoStop"] == -200.0


def test_planos_parciais():
    r = L(32, pos={**POS, "alvo": None})
    assert r["plano"] == "so_stop" and r["posicaoNoPlano"] is None and r["reguaAria"] is None
    r = L(32, pos={**POS, "stop": None})
    assert r["plano"] == "so_alvo"
    r = L(32, pos={**POS, "stop": None, "alvo": None})
    assert r["plano"] == "sem_plano"


@pytest.mark.parametrize("bad", [0, -1, "x", True, None, float("nan")])
def test_avg_qty_invalidos(bad):
    r = L(32, pos={**POS, "avg": bad})
    assert r["resultado"] is None and r["variacaoPct"] is None
    assert r["resultadoNoStop"] is None and r["resultadoNoAlvo"] is None
    r = L(32, pos={**POS, "qty": bad})
    assert r["resultado"] is None and r["resultadoNoStop"] is None


def test_gatilho():
    se = {"invalidacao": 31, "lado": "alta"}
    assert L(30, pos={**POS, "setupEntrada": se})["gatilhoStatus"] == "invalidado"
    assert L(32, pos={**POS, "setupEntrada": se})["gatilhoStatus"] == "valido"
    se = {"invalidacao": 31, "lado": "baixa"}
    assert L(32, pos={**POS, "setupEntrada": se})["gatilhoStatus"] == "invalidado"
    assert L(30, pos={**POS, "setupEntrada": se})["gatilhoStatus"] == "valido"
    assert L(None, pos={**POS, "setupEntrada": se})["gatilhoStatus"] is None
    assert L(32)["gatilhoStatus"] is None


def test_nota_pm():
    compras = [{"qty": 60, "price": 29}, {"qty": 40, "price": 31.5}]
    base = skill_ref.cartao_posicao_txt("operador", "nota_pm", pm="30,00",
                                         total="3.000,00", qtd="100")
    assert L(32, compras=compras)["notaPm"] == base
    r = L(32, pos={**POS, "qty": 80}, compras=compras)
    assert r["notaPm"] == base + skill_ref.cartao_posicao_txt("operador", "nota_pm_vendas")
    assert L(32, compras=[])["notaPm"] is None
    assert L(32, compras=None)["notaPm"] is None
    assert L(32, compras=[{"qty": "a", "price": 1}])["notaPm"] is None


def _termos(d):
    return [s["termo"] for s in d["paragrafo"] if "termo" in s]


def test_didatica_estudo_completo():
    r = L(32, modo="educacional")
    d = r["didatica"]
    assert _termos(d) == ["preco_medio", "stop", "alvo", "rr"]
    assert d["borisExplica"]
    for s in d["paragrafo"]:
        if "termo" in s:
            assert s["kb"] == cp.TERMO_KB[s["termo"]]
            assert s["noSeuCaso"]
        assert "[[" not in "".join(s.values())


def test_didatica_sem_rr_e_sem_plano():
    r = L(27, modo="educacional")
    assert _termos(r["didatica"]) == ["preco_medio", "stop", "alvo"]
    r = L(32, pos={**POS, "stop": None, "alvo": None}, modo="educacional")
    assert _termos(r["didatica"]) == ["preco_medio", "stop", "alvo"]
    casos = {s["termo"]: s["noSeuCaso"] for s in r["didatica"]["paragrafo"] if "termo" in s}
    assert casos["stop"] == skill_ref.cartao_didatica_txt("caso_stop_indefinido")
    assert casos["alvo"] == skill_ref.cartao_didatica_txt("caso_alvo_indefinido")


def test_didatica_so_estudo():
    assert L(32, modo="operador")["didatica"] is None


def test_termo_desconhecido_vira_texto():
    segs = cp._segmentos("a [[xyz]] b [[stop]]", {"stop": "caso"})
    assert segs[0] == {"texto": "a "}
    assert {"texto": "xyz"} in segs
    assert segs[-1]["termo"] == "stop"
    assert not any("[[" in s.get("texto", "") for s in segs)


def test_modulo_puro():
    import inspect
    src = inspect.getsource(cp)
    for proibido in ("import httpx", "import sqlite3", "from . import llm",
                     "datetime.now", "date.today"):
        assert proibido not in src
    assert not math.isnan(cp.ALTA_FORTE_FATOR)
