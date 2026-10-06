"""Fase 49 (2026-10-06) — motor puro da anatomia da perna (ANAT-01/02/03/04/05/08).

Conta conferida à mão: ITUB4 3 pernas em S=48 → −277,00.
  CALL 49,26 (0,21×100) → −21,00 ; CALL 49,76 (0,16×100) → −16,00 ;
  PUT 46,51 (2,40×100) → −240,00 ; soma = −277,00. Ações 100 × (48−40) = +800,00.
Textos esperados vêm de `skill_ref.opcoes_escada_txt` (nunca redigitados).
"""
import datetime as dt
import pathlib

import pytest

from app import anatomia_perna as m
from app import skill_ref

HOJE = dt.date(2026, 10, 6)
A, B, C = "ITUBJ493W2", "ITUBJ498W2", "ITUBV465W2"
ND = "Não há dados suficientes para concluir."


def _op(id_, tipo, strike, avg, qty=100, exp="2026-10-09", side=None, und="ITUB4"):
    d = {"id": id_, "underlying": und, "optionType": tipo, "strike": strike,
         "expiration": exp, "qty": qty, "avg": avg}
    if side is not None:
        d["side"] = side
    return d


def _ops_itub4():
    return [_op(A, "call", 49.26, 0.21), _op(B, "call", 49.76, 0.16),
            _op(C, "put", 46.51, 2.40)]


def _posicao(avg=40.00, qty=100):
    return {"t": "ITUB4", "qty": qty, "avg": avg}


def _ler(ops=None, posicao="padrao", spot=48.0, estrutura=None, modo="educacional",
         excluir=()):
    if posicao == "padrao":
        posicao = _posicao()
    return m.ler_anatomia(_ops_itub4() if ops is None else ops, "ITUB4", posicao,
                          spot, estrutura, HOJE, modo, excluir)


def _idx(anat, preco):
    return anat["grade"]["precos"].index(preco)


def _perna(anat, id_):
    return next(p for p in anat["pernas"] if p["id"] == id_)


def test_valor_pior_caso_equilibrio_por_perna():
    a = _ler()
    esperado = {A: (21.00, -21.00, 49.47), B: (16.00, -16.00, 49.92),
                C: (240.00, -240.00, 44.11)}
    for id_, (val, pior, eq) in esperado.items():
        p = _perna(a, id_)
        assert p["valorPremio"] == val
        assert p["piorCaso"] == pior
        assert p["equilibrio"] == eq
        assert p["piorIlimitado"] is False


def test_prazo_em_dias_corridos_e_variantes():
    a = _ler()
    p = _perna(a, A)
    assert p["dias"] == 3
    assert p["prazoTexto"] == skill_ref.opcoes_escada_txt(
        "educacional", "anat_prazo_dias", dias=3, vencimento="09/10")
    assert p["prazoTexto"] == "vence em 3 dias (09/10)"
    casos = {"2026-10-07": "anat_prazo_amanha", "2026-10-06": "anat_prazo_hoje",
             "2026-10-05": "anat_prazo_vencida"}
    for exp, chave in casos.items():
        r = _ler(ops=[_op(A, "call", 49.26, 0.21, exp=exp)])
        dd = f"{exp[8:]}/{exp[5:7]}"
        assert _perna(r, A)["prazoTexto"] == skill_ref.opcoes_escada_txt(
            "educacional", chave, vencimento=dd)
    r = _ler(ops=[_op(A, "call", 49.26, 0.21, exp=None)])
    pa = _perna(r, A)
    assert pa["dias"] is None
    assert pa["prazoTexto"] == skill_ref.opcoes_escada_txt("educacional", "anat_prazo_sem_data")


def test_frase_e_condicao():
    a = _ler()
    fa = _perna(a, A)["frase"]
    assert "R$ 21,00 (R$ 0,21 × 100)" in fa
    assert "comprar 100 ITUB4 a R$ 49,26" in fa
    assert "até 09/10" in fa
    assert "{" not in fa
    assert "vender" in _perna(a, C)["frase"]
    assert "R$ 49,47" in _perna(a, A)["condicao"]
    assert "{" not in _perna(a, A)["condicao"]


def test_grade_ancoras_ordem_e_indice_inicial():
    g = _ler()["grade"]
    precos = g["precos"]
    assert precos == sorted(set(precos))
    for ancora in (48.00, 49.26, 49.76, 46.51, 49.47, 49.92, 44.11, 40.00):
        assert ancora in precos
    assert len(precos) <= m.MAX_PONTOS_ANATOMIA + 8
    assert precos[g["indiceInicial"]] == 48.00
    assert g["hoje"] == 48.0


def test_pontos_da_perna_batem_com_strike_e_equilibrio():
    a = _ler()
    for id_, k, premio in ((A, 49.26, 0.21), (B, 49.76, 0.16), (C, 46.51, 2.40)):
        p = _perna(a, id_)
        assert len(p["pontos"]) == len(a["grade"]["precos"])
        assert p["pontos"][_idx(a, k)] == round(-premio * 100, 2)
        assert p["pontos"][_idx(a, p["equilibrio"])] == 0.0


def test_total_itub4_sem_acoes_menos_277_e_sem_esta():
    a = _ler(excluir=("ACOES",))
    i = _idx(a, 48.00)
    assert a["total"]["pontos"][i] == -277.00
    assert a["total"]["semEsta"][C][i] == -37.00
    assert _perna(a, C)["pontos"][i] == -240.00
    assert "ACOES" in a["excluidas"]


def test_identidade_total_igual_sem_esta_mais_contribuicao_em_todo_indice():
    for excluir in ((), ("ACOES",)):
        a = _ler(excluir=excluir)
        total = a["total"]
        for id_ in total["incluidas"]:
            p = _perna(a, id_)
            for i, v in enumerate(total["pontos"]):
                assert v == round(total["semEsta"][id_][i] + p["pontos"][i], 2)


def test_acoes_com_preco_medio_entram_no_total():
    a = _ler()
    assert a["acoes"]["incluidas"] is True
    assert a["acoes"]["precoMedio"] == 40.00
    assert a["acoes"]["texto"] == skill_ref.opcoes_escada_txt(
        "educacional", "anat_acoes_dentro", qtd=100, ticker="ITUB4", pm="40,00")
    assert a["total"]["pontos"][_idx(a, 48.00)] == -277.00 + 800.00 == 523.00


def test_acoes_sem_preco_medio_ficam_fora_sem_estimar():
    a = _ler(posicao=_posicao(avg=None))
    assert a["acoes"]["incluidas"] is False
    assert a["acoes"]["pontos"] is None
    assert a["acoes"]["precoMedio"] is None
    assert a["acoes"]["texto"] == skill_ref.opcoes_escada_txt(
        "educacional", "anat_acoes_fora_sem_pm", qtd=100, ticker="ITUB4")
    assert a["total"]["pontos"][_idx(a, 48.00)] == -277.00


def test_excluir_perna_mantem_a_grade():
    base = _ler()
    a = _ler(excluir=(A,))
    assert _perna(a, A)["incluida"] is False
    assert A not in a["total"]["incluidas"]
    assert A not in a["total"]["semEsta"]
    assert a["grade"]["precos"] == base["grade"]["precos"]
    assert a["grade"]["indiceInicial"] == base["grade"]["indiceInicial"]


def test_tudo_excluido_total_vazio():
    a = _ler(excluir=(A, B, C, "ACOES"))
    assert a["total"]["pontos"] is None
    assert a["total"]["motivoTexto"] == skill_ref.opcoes_escada_txt(
        "educacional", "anat_total_vazio")


def test_independencia_de_cotacao():
    com = _ler(spot=48.0)
    sem = _ler(spot=None)
    for id_ in (A, B, C):
        for campo in ("piorCaso", "equilibrio", "valorPremio", "tabela"):
            if campo == "tabela":
                # a tabela pode ganhar a linha do spot; os pontos da perna não mudam
                pc = {(r["preco"]): r["resultado"] for r in _perna(com, id_)[campo]}
                ps = {(r["preco"]): r["resultado"] for r in _perna(sem, id_)[campo]}
                for preco, res in ps.items():
                    assert pc[preco] == res
            else:
                assert _perna(com, id_)[campo] == _perna(sem, id_)[campo]
    assert sem["grade"]["hoje"] is None


def test_call_vendida_perda_ilimitada():
    a = _ler(ops=[_op("V1", "call", 50.0, 1.0, side="vendida")])
    p = _perna(a, "V1")
    assert p["piorCaso"] is None
    assert p["piorIlimitado"] is True
    assert p["piorTexto"] == skill_ref.opcoes_escada_txt(
        "educacional", "anat_pior_ilimitado_nota", ticker="ITUB4")
    assert p["equilibrio"] == 51.00
    assert p["valorPremio"] == 100.00
    assert p["frase"].startswith("Você recebeu R$ 100,00")
    assert "obrigação de vender" in p["frase"]


def test_put_vendida_pior_caso_limitado():
    a = _ler(ops=[_op("V2", "put", 30.0, 1.0, side="vendida")])
    p = _perna(a, "V2")
    assert p["piorCaso"] == -2900.00
    assert p["equilibrio"] == 29.00
    assert "obrigação de comprar" in p["frase"]


@pytest.mark.parametrize("mudanca", [{"strike": None}, {"avg": None}, {"qty": 0},
                                      {"side": "short"}])
def test_perna_invalida_vira_none_e_o_resto_segue(mudanca):
    ruim = dict(_op("RUIM", "call", 49.0, 0.2), **mudanca)
    a = _ler(ops=_ops_itub4() + [ruim])
    p = _perna(a, "RUIM")
    assert p["pontos"] is None and p["piorCaso"] is None and p["equilibrio"] is None
    assert p["incluida"] is False
    assert p["motivoTexto"].startswith(ND)
    assert _perna(a, A)["piorCaso"] == -21.00
    assert a["total"]["pontos"] is not None


def test_vencimentos_diferentes_bloqueiam_so_o_total():
    ops = [_op(A, "call", 49.26, 0.21, exp="2026-10-09"),
           _op(B, "call", 49.76, 0.16, exp="2026-11-13")]
    a = _ler(ops=ops)
    assert a["total"]["pontos"] is None
    assert a["total"]["motivoTexto"].startswith(ND)
    assert "09/10 e 13/11" in a["total"]["motivoTexto"]
    assert _perna(a, A)["pontos"] is not None and _perna(a, B)["pontos"] is not None
    assert a["vencimentoTexto"] is None


def test_hoje_vem_da_estrutura_cotada():
    sem = _ler(estrutura=None)
    assert _perna(sem, A)["hoje"] == {
        "valor": None, "premioAtual": None,
        "motivoTexto": skill_ref.opcoes_escada_txt("educacional", "anat_hoje_sem_estrutura")}
    assert _perna(sem, A)["encerrar"] is None

    estr = {"pernas": [
        {"id": A, "resultado": -5.0, "premioAtual": 0.16,
         "encerrar": {"permitido": True, "motivo": None, "texto": None}},
        {"id": B, "resultado": None, "premioAtual": None, "motivoSemCotacao": "sem_negocio",
         "encerrar": {"permitido": False, "motivo": "premio_indisponivel", "texto": "x"}},
        {"id": C, "resultado": None, "premioAtual": None, "motivoSemCotacao": "inventado"},
    ]}
    a = _ler(estrutura=estr)
    pa = _perna(a, A)
    assert pa["hoje"] == {"valor": -5.0, "premioAtual": 0.16, "motivoTexto": None}
    assert pa["encerrar"]["permitido"] is True
    pb = _perna(a, B)
    assert pb["hoje"]["valor"] is None
    assert pb["hoje"]["motivoTexto"] == skill_ref.opcoes_escada_txt(
        "educacional", "anat_hoje_sem_negocio")
    assert pb["encerrar"]["permitido"] is False
    assert _perna(a, C)["hoje"]["motivoTexto"] == skill_ref.opcoes_escada_txt(
        "educacional", "anat_hoje_sem_cotacao")


def test_modo_operador_usa_vocabulario_proprio():
    ed = _perna(_ler(), A)["frase"]
    op = _perna(_ler(modo="operador"), A)["frase"]
    assert op != ed
    assert op == skill_ref.opcoes_escada_txt(
        "operador", "anat_frase_call_compra", valor="21,00", premio="0,21",
        qtd="100", ticker="ITUB4", strike="49,26", vencimento="09/10")


def test_nenhum_zero_substitui_ausente():
    a = _ler(ops=[_op("RUIM", "call", None, 0.2), _op("V1", "call", 50.0, 1.0, side="vendida")])
    ruim = _perna(a, "RUIM")
    assert ruim["piorCaso"] is None and ruim["equilibrio"] is None
    assert ruim["hoje"]["valor"] is None
    assert _perna(a, "V1")["piorCaso"] is None


def test_outro_underlying_ignorado_e_sem_pernas_devolve_none():
    ops = _ops_itub4() + [_op("PETRX", "call", 40.0, 1.0, und="PETR4")]
    a = _ler(ops=ops)
    assert {p["id"] for p in a["pernas"]} == {A, B, C}
    assert _ler(ops=[_op("PETRX", "call", 40.0, 1.0, und="PETR4")]) is None
    assert _ler(ops=[]) is None


def test_motor_e_puro():
    fonte = (pathlib.Path(m.__file__)).read_text(encoding="utf-8")
    for proibido in ("import httpx", "from .db", "from . import db", "datetime.now",
                     "date.today", "anthropic"):
        assert proibido not in fonte
    assert "opcoes_payoff." in fonte


def test_inf_nan_sao_dado_ausente():
    """IN-01 (49-REVIEW, 2026-10-06): inf/nan não derrubam a grade nem vazam NaN."""
    inf = float("inf")
    ops = [_op(A, "call", inf, 0.21), _op(B, "call", 49.76, 0.16, exp="2026-10-09")]
    a = _ler(ops=ops)
    assert _perna(a, A)["pontos"] is None
    assert _perna(a, B)["pontos"] is not None
    est = {"pernas": [{"id": B, "resultado": float("nan"), "premioAtual": inf}]}
    h = _perna(_ler(estrutura=est), B)["hoje"]
    assert h["valor"] is None and h["premioAtual"] is None
