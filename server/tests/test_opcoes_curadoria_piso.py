"""Fase 39, Plano 01 — guardião do piso de admissão por probabilidade OTM
(D-08) e ordenação por prêmio anualizado (D-09), com nota de reversão
deliberada: a Fase 31/D-06 continua vigente quanto a NUNCA filtrar por
SINAL do prêmio (put de proteção/collar de débito continuam na varredura) —
o piso desta fase é um critério DIFERENTE (probabilidade de terminar OTM,
D-08), consequência nomeada: put/collar perto do dinheiro raramente passam.

Módulo sob teste é PURO (server/app/opcoes_curadoria.py) — sem rede, sem
banco, sem LLM. Valores esperados vêm de chamar `black_scholes` diretamente
no teste, nunca de número mágico.
"""
import random

import pytest

from app import opcoes_curadoria
from app.options_quant import TAXA_LIVRE_DE_RISCO_REFERENCIA, black_scholes, years_to_expiration


# ─────────────────────────────────────────────────────────────────────────
# vol_do_contrato() — IV do contrato ou fallback para hv21, nunca inventado
# ─────────────────────────────────────────────────────────────────────────

def test_vol_do_contrato_usa_iv_valida():
    assert opcoes_curadoria.vol_do_contrato({"impliedVolatility": 0.3}, hv21=None) == (0.3, "implicita")


@pytest.mark.parametrize("iv_invalida", [None, 0, True, 7.0, -1, 0.005])
def test_vol_do_contrato_iv_invalida_cai_para_historica(iv_invalida):
    assert opcoes_curadoria.vol_do_contrato({"impliedVolatility": iv_invalida}, hv21=0.25) == (0.25, "historica_21d")


def test_vol_do_contrato_sem_iv_e_sem_historica_devolve_none_none():
    assert opcoes_curadoria.vol_do_contrato({"impliedVolatility": None}, hv21=None) == (None, None)


# ─────────────────────────────────────────────────────────────────────────
# prob_otm() — probabilidade de terminar fora do dinheiro, via Black-Scholes
# ─────────────────────────────────────────────────────────────────────────

def test_prob_otm_call_bate_com_black_scholes_direto():
    esperado = round(1 - black_scholes(
        "call", 30.0, 33.0, years_to_expiration(30), TAXA_LIVRE_DE_RISCO_REFERENCIA, 0.3, 0.0
    ).prob_itm, 4)
    assert opcoes_curadoria.prob_otm("call", 30.0, 33.0, 30, 0.3) == esperado


def test_prob_otm_put_bate_com_black_scholes_direto():
    esperado = round(1 - black_scholes(
        "put", 30.0, 27.0, years_to_expiration(22), TAXA_LIVRE_DE_RISCO_REFERENCIA, 0.28, 0.0
    ).prob_itm, 4)
    assert opcoes_curadoria.prob_otm("put", 30.0, 27.0, 22, 0.28) == esperado


def test_prob_otm_vol_none_devolve_none():
    assert opcoes_curadoria.prob_otm("call", 30.0, 33.0, 30, None) is None


def test_prob_otm_dias_zero_devolve_none():
    assert opcoes_curadoria.prob_otm("call", 30.0, 33.0, 0, 0.3) is None


# ─────────────────────────────────────────────────────────────────────────
# premio_anualizado() — (prêmio/spot) × (365/dias)
# ─────────────────────────────────────────────────────────────────────────

def test_premio_anualizado_bate_com_formula():
    assert opcoes_curadoria.premio_anualizado(1.62, 38.82, 23) == round((1.62 / 38.82) * (365 / 23), 6)


def test_premio_anualizado_spot_nao_positivo_devolve_none():
    assert opcoes_curadoria.premio_anualizado(1.0, 0, 30) is None
    assert opcoes_curadoria.premio_anualizado(1.0, -5.0, 30) is None


def test_premio_anualizado_dias_nao_positivo_devolve_none():
    assert opcoes_curadoria.premio_anualizado(1.0, 30.0, 0) is None


# ─────────────────────────────────────────────────────────────────────────
# aplicar_piso() — admissão por probOtm >= 0.60, nunca relaxado em silêncio
# ─────────────────────────────────────────────────────────────────────────

def _cand(idc, prob_otm):
    return {"idCandidato": idc, "probOtm": prob_otm, "premioAnualizado": 0.1}


def test_aplicar_piso_admite_exatamente_no_piso():
    admitidos, contagem = opcoes_curadoria.aplicar_piso([_cand("a", 0.60)])
    assert [c["idCandidato"] for c in admitidos] == ["a"]
    assert contagem == {"admitidosNoPiso": 1, "reprovadosNoPiso": 0, "semProbabilidade": 0}


def test_aplicar_piso_reprova_abaixo_do_piso():
    admitidos, contagem = opcoes_curadoria.aplicar_piso([_cand("a", 0.5999)])
    assert admitidos == []
    assert contagem == {"admitidosNoPiso": 0, "reprovadosNoPiso": 1, "semProbabilidade": 0}


def test_aplicar_piso_none_conta_em_sem_probabilidade_nunca_admite():
    admitidos, contagem = opcoes_curadoria.aplicar_piso([_cand("a", None)])
    assert admitidos == []
    assert contagem == {"admitidosNoPiso": 0, "reprovadosNoPiso": 0, "semProbabilidade": 1}


def test_aplicar_piso_preserva_ordem_de_entrada():
    entrada = [_cand("a", 0.9), _cand("b", 0.7), _cand("c", 0.65)]
    admitidos, _ = opcoes_curadoria.aplicar_piso(entrada)
    assert [c["idCandidato"] for c in admitidos] == ["a", "b", "c"]


def test_aplicar_piso_mistura_os_tres_destinos():
    entrada = [_cand("admite", 0.8), _cand("reprova", 0.5), _cand("semprob", None)]
    admitidos, contagem = opcoes_curadoria.aplicar_piso(entrada)
    assert [c["idCandidato"] for c in admitidos] == ["admite"]
    assert contagem == {"admitidosNoPiso": 1, "reprovadosNoPiso": 1, "semProbabilidade": 1}


# ─────────────────────────────────────────────────────────────────────────
# rankear() — ordem nova por premioAnualizado (D-09), permutação estável
# ─────────────────────────────────────────────────────────────────────────

def _candidato_ranking(symbol, premio_anualizado, premio_unitario=1.0):
    return {
        "tipo": "call_coberta", "contractSymbol": symbol, "idCandidato": symbol,
        "premioAnualizado": premio_anualizado, "premioUnitario": premio_unitario,
        "probOtm": 0.7, "razao": premio_anualizado,
    }


def test_rankear_ordena_por_premio_anualizado_decrescente():
    candidatos = [_candidato_ranking("A", 0.10), _candidato_ranking("B", 0.30), _candidato_ranking("C", 0.20)]
    top = opcoes_curadoria.rankear(candidatos)
    assert [c["contractSymbol"] for c in top] == ["B", "C", "A"]


def test_rankear_por_premio_anualizado_e_estavel_a_permutacao():
    base = [_candidato_ranking(f"C{i}", premio_anualizado=(i * 37) % 11 / 10) for i in range(1, 12)]
    esperado = [c["contractSymbol"] for c in opcoes_curadoria.rankear(base)]
    rnd = random.Random(390139)
    for _ in range(10):
        embaralhado = list(base)
        rnd.shuffle(embaralhado)
        assert [c["contractSymbol"] for c in opcoes_curadoria.rankear(embaralhado)] == esperado


# ─────────────────────────────────────────────────────────────────────────
# exigir_ranking() — extensão do D-08/D-09: recusa nomeando o defeito
# ─────────────────────────────────────────────────────────────────────────

def _top_valido_piso(n=3):
    return [
        {"tipo": "call_coberta", "contractSymbol": f"X{i}", "idCandidato": f"X{i}",
         "premioAnualizado": round(1.0 - i * 0.1, 6), "premioUnitario": 1.0, "razao": 1.0,
         "probOtm": 0.7, "posicaoNoRanking": i + 1}
        for i in range(n)
    ]


def test_exigir_ranking_aceita_top_valido_com_piso():
    opcoes_curadoria.exigir_ranking(_top_valido_piso())  # não levanta


def test_exigir_ranking_recusa_premioanualizado_ausente():
    top = _top_valido_piso()
    del top[0]["premioAnualizado"]
    with pytest.raises(ValueError, match="premioAnualizado"):
        opcoes_curadoria.exigir_ranking(top)


def test_exigir_ranking_recusa_premioanualizado_nao_numerico():
    top = _top_valido_piso()
    top[0]["premioAnualizado"] = "0.5"
    with pytest.raises(ValueError, match="premioAnualizado"):
        opcoes_curadoria.exigir_ranking(top)


def test_exigir_ranking_recusa_premioanualizado_crescente():
    top = _top_valido_piso()
    top[1]["premioAnualizado"] = top[0]["premioAnualizado"] + 1.0
    with pytest.raises(ValueError):
        opcoes_curadoria.exigir_ranking(top)


def test_exigir_ranking_recusa_probotm_ausente():
    top = _top_valido_piso()
    del top[0]["probOtm"]
    with pytest.raises(ValueError, match="probOtm"):
        opcoes_curadoria.exigir_ranking(top)


def test_exigir_ranking_recusa_probotm_abaixo_do_piso():
    top = _top_valido_piso()
    top[0]["probOtm"] = opcoes_curadoria.PISO_PROB_OTM - 0.0001
    with pytest.raises(ValueError, match="probOtm"):
        opcoes_curadoria.exigir_ranking(top)


def test_exigir_ranking_recusa_posicao_fora_de_ordem_com_piso():
    top = _top_valido_piso(2)
    top[0]["posicaoNoRanking"], top[1]["posicaoNoRanking"] = 2, 1
    with pytest.raises(ValueError):
        opcoes_curadoria.exigir_ranking(top)


def test_exigir_ranking_recusa_mais_de_topo_itens_com_piso():
    top = _top_valido_piso(opcoes_curadoria.TOPO + 1)
    with pytest.raises(ValueError):
        opcoes_curadoria.exigir_ranking(top)


# ─────────────────────────────────────────────────────────────────────────
# narrativa_user()/narrativa_system() — vocabulário novo (D-08/D-09)
# ─────────────────────────────────────────────────────────────────────────

def _item_piso(tipo="call_coberta", posicao=1, premio_anualizado=0.5, prob_otm=0.7,
               volatilidade_fonte="implicita", contract_symbol="X1"):
    return {
        "tipo": tipo, "ticker": "PETR4", "contractSymbol": contract_symbol,
        "optionType": "call", "strike": 30.0, "strikeCall": 30.0, "strikePut": 25.0,
        "expiration": "2026-10-05", "diasParaVencimento": 22,
        "contratos": 1, "qtyAcoes": 100,
        "premioUnitario": 1.5, "premioTotal": 150.0,
        "liquidez": {"score": 60, "faixa": "NEGOCIÁVEL", "volume": 100, "spreadPct": 0.01, "aviso": None},
        "estrutura": {"ganho_maximo": 5.0, "perda_maxima": 2.0, "breakevens": [29.0],
                      "custo_liquido": 0, "fluxo": "credito"},
        "razao": premio_anualizado, "premioAnualizado": premio_anualizado, "probOtm": prob_otm,
        "volatilidadeFonte": volatilidade_fonte,
        "manchete": "manchete", "didatica": "didatica",
        "precoObjeto": 29.0, "posicaoNoRanking": posicao,
        "idCandidato": f"{tipo}:PETR4:2026-10-05:{contract_symbol}",
    }


def test_narrativa_user_nao_contem_mais_razao_como_rotulo():
    top = [_item_piso()]
    texto = opcoes_curadoria.narrativa_user(top, "operador")
    assert "razão" not in texto.lower()


def test_narrativa_user_contem_premio_anualizado_e_probabilidade_estimada():
    top = [_item_piso()]
    texto = opcoes_curadoria.narrativa_user(top, "operador")
    assert "prêmio anualizado" in texto.lower()
    assert "probabilidade estimada" in texto.lower()


def test_narrativa_user_diz_historica_quando_fonte_e_historica_21d():
    top = [_item_piso(volatilidade_fonte="historica_21d")]
    texto = opcoes_curadoria.narrativa_user(top, "operador")
    assert "histórica" in texto.lower()


def test_narrativa_system_menciona_piso_e_proibe_certeza():
    texto = opcoes_curadoria.narrativa_system("operador")
    assert "60%" in texto or "0,6" in texto or "0.6" in texto
    assert "certeza" in texto.lower()
