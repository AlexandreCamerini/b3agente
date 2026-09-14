"""Fase 30, Plano 01 — guardiões unitários do motor puro de curadoria
(`server/app/opcoes_curadoria.py`).

Módulo PURO sob teste: sem rede, sem banco, sem LLM. Cadeia sintética montada
no próprio teste, mesmo padrão de `test_opcoes_motor.py`.
"""
import datetime as dt
import random

import pytest

from app import opcoes_curadoria, skill_ref

_SPOT = 29.0
_HOJE = dt.date(2026, 9, 13)
_EXPIRATION_OK = "2026-10-05"  # 22 dias de _HOJE — dentro de 15..60


def _contrato(symbol, kind, strike, price=1.5, volume=5000, oi=1000,
              bid=1.48, ask=1.52, **extra):
    """Contrato ADR-004, líquido por padrão (score >= 55)."""
    d = {
        "contractSymbol": symbol, "optionType": kind, "strike": strike,
        "lastPrice": price, "bid": bid, "ask": ask, "volume": volume,
        "openInterest": oi, "impliedVolatility": 0.3, "inTheMoney": False,
        "currency": "BRL", "distancePct": None,
        "greeks": {"delta": None, "gamma": None, "vega": None, "theta": None, "rho": None},
        "expiration": _EXPIRATION_OK,
    }
    d.update(extra)
    return d


def _cadeia(calls=None, puts=None, expiration=_EXPIRATION_OK, provider_status="ok"):
    return {
        "providerStatus": provider_status, "underlyingPrice": _SPOT,
        "expiration": expiration, "expirations": [expiration],
        "calls": calls if calls is not None else [], "puts": puts if puts is not None else [],
    }


def _cadeia_6_calls_liquidas():
    strikes = (30, 31, 32, 33, 34, 35)
    calls = [_contrato(f"C{s}", "call", s) for s in strikes]
    return _cadeia(calls=calls)


def _posicao(qty=200, qty_travada=0):
    return {"t": "PETR4", "qty": qty, "qtyTravada": qty_travada, "pm": 25.0}


# ─────────────────────────────────────────────────────────────────────────
# Pureza — nenhuma chamada de rede
# ─────────────────────────────────────────────────────────────────────────

def test_modulo_nao_importa_camadas_de_rede():
    src = open(opcoes_curadoria.__file__).read()
    for banido in ("options_provider", "httpx", "candle_provider", "import db", "mcp_client"):
        assert banido not in src, f"{banido!r} não pode aparecer em opcoes_curadoria.py"


def test_nenhum_filtro_put_no_arquivo():
    src = open(opcoes_curadoria.__file__).read()
    linhas_sem_comentario = [l for l in src.splitlines() if not l.strip().startswith("#")]
    assert not any('"tipo": "put"' in l for l in linhas_sem_comentario)


# ─────────────────────────────────────────────────────────────────────────
# candidatos_da_posicao() — portas fechadas e enumeração
# ─────────────────────────────────────────────────────────────────────────

def test_seis_calls_liquidas_n5_devolve_5_um_vencimento_strikes_distintos():
    chain = _cadeia_6_calls_liquidas()
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE, n=5)
    assert len(candidatos) == 5
    assert all(c["expiration"] == chain["expiration"] for c in candidatos)
    strikes = [c["strike"] for c in candidatos]
    assert strikes == sorted(strikes)
    assert len(set(strikes)) == len(strikes)


def test_provider_status_degradado_devolve_lista_vazia():
    chain = _cadeia_6_calls_liquidas()
    chain["providerStatus"] = "degradado"
    assert opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE) == []


def test_chain_nao_dict_devolve_lista_vazia():
    assert opcoes_curadoria.candidatos_da_posicao(
        "PETR4", None, _SPOT, _posicao(), "operador", _HOJE) == []


@pytest.mark.parametrize("qty,esperado_vazio", [(99, True), (100, False)])
def test_qty_livre_no_limite_de_um_contrato(qty, esperado_vazio):
    chain = _cadeia_6_calls_liquidas()
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(qty=qty), "operador", _HOJE, n=1)
    if esperado_vazio:
        assert candidatos == []
    else:
        assert len(candidatos) == 1
        assert candidatos[0]["contratos"] == 1
        assert candidatos[0]["qtyAcoes"] == 100


def test_posicao_nao_dict_devolve_lista_vazia():
    chain = _cadeia_6_calls_liquidas()
    assert opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, None, "operador", _HOJE) == []


@pytest.mark.parametrize("spot_ruim", [None, 0, -5.0, True])
def test_spot_invalido_nunca_typeerror_devolve_vazio(spot_ruim):
    chain = _cadeia_6_calls_liquidas()
    assert opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, spot_ruim, _posicao(), "operador", _HOJE) == []


@pytest.mark.parametrize("dias,expiration", [
    (10, "2026-09-23"),  # 10 dias de _HOJE — abaixo de 15
    (90, "2026-12-12"),  # 90 dias de _HOJE — acima de 60
])
def test_vencimento_fora_da_janela_devolve_vazio(dias, expiration):
    chain = _cadeia(calls=[_contrato("C30", "call", 30, expiration=expiration)], expiration=expiration)
    assert opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE) == []


def test_piso_liquidez_explicito_nao_cai_para_dificil():
    # score ~45 (DIFÍCIL, entre 30 e 55): volume baixo, spread apertado.
    contrato_dificil = _contrato("C30", "call", 30, volume=100, oi=0, bid=1.48, ask=1.52)
    chain = _cadeia(calls=[contrato_dificil])
    from app.options_quant import liquidity_score
    score = liquidity_score(contrato_dificil["volume"], contrato_dificil["openInterest"],
                             contrato_dificil["bid"], contrato_dificil["ask"])["score"]
    assert 30 <= score < 55, f"fixture não está na faixa DIFÍCIL (score={score})"
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE)
    assert candidatos == [], (
        "com liquidez_minima explícito (D5), rastrear() NÃO deve cair para a "
        "segunda passada DIFÍCIL — um contrato DIFÍCIL não pode entrar no ranking")


def test_perda_maxima_zero_descarta_candidato_sem_razao_infinita():
    # Strike muito acima do spot com prêmio alto o bastante para que a venda
    # coberta nunca feche no negativo em nenhum ponto simulado (perda_maxima
    # 0.0) — opcoes_payoff classifica isso quando o pior resultado é >= 0.
    contrato_sem_perda = _contrato("C1000", "call", 1000.0, price=950.0)
    chain = _cadeia(calls=[contrato_sem_perda])
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE)
    assert candidatos == []


def test_razao_e_o_arredondamento_esperado():
    chain = _cadeia(calls=[_contrato("C30", "call", 30, price=1.5)])
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE)
    assert len(candidatos) == 1
    c = candidatos[0]
    assert c["razao"] == round(c["premioUnitario"] / c["estrutura"]["perda_maxima"], 6)


def test_manchete_byte_igual_a_skill_ref():
    chain = _cadeia(calls=[_contrato("C30", "call", 30, price=1.5)])
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE)
    c = candidatos[0]
    dados = {
        "n": str(c["contratos"]), "ticker": "PETR4", "strike": skill_ref.num_br(c["strike"]),
        "premioTotal": skill_ref.num_br(c["premioTotal"]), "qtyAcoes": str(c["qtyAcoes"]),
    }
    esperado = skill_ref.opcoes_lastreadas_txt("operador", "call_coberta", **dados)
    assert c["manchete"] == esperado


def test_nenhuma_chamada_de_rede_cadeia_em_memoria_basta():
    # Se este teste passar sem monkeypatch/mocks de rede, a garantia de
    # pureza está satisfeita empiricamente, não só por inspeção de import.
    chain = _cadeia_6_calls_liquidas()
    candidatos = opcoes_curadoria.candidatos_da_posicao(
        "PETR4", chain, _SPOT, _posicao(), "operador", _HOJE, n=3)
    assert len(candidatos) == 3

