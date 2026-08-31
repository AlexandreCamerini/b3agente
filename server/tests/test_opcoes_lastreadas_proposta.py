"""Fase 14, Plano 03 — motor de proposta de opções lastreadas (venda coberta
e put de proteção).

Parte 1 (Task 1): vocabulário canônico por modo (`skill_ref.OPCOES_LASTREADAS`
/ `opcoes_lastreadas_txt`) — guardião de registro (Operador ordena, Estudo
descreve condição) e do helper `num_br`.

Parte 2 (Task 2): motor puro `opcoes_lastreadas.propor`/`put_sem_lastro` — sem
rede, sem banco, sem LLM; cadeia sintética montada no próprio teste.
"""
import datetime as dt

from app import skill_ref, opcoes_lastreadas


# --------------------------- Parte 1: vocabulário ---------------------------

def test_vocab_chaves_de_operacao_existem_nos_dois_modos():
    for modo in ("operador", "educacional"):
        assert "call_coberta" in skill_ref.OPCOES_LASTREADAS[modo]
        assert "put_protecao" in skill_ref.OPCOES_LASTREADAS[modo]


def test_vocab_operador_fala_como_mesa_verbo_de_ordem():
    frase = skill_ref.OPCOES_LASTREADAS["operador"]["call_coberta"]
    assert frase.startswith("Vender")
    frase_put = skill_ref.OPCOES_LASTREADAS["operador"]["put_protecao"]
    assert frase_put.startswith("Comprar")


def test_vocab_educacional_descreve_condicao_nunca_ordem():
    frase = skill_ref.OPCOES_LASTREADAS["educacional"]["call_coberta"]
    assert frase.startswith("Se você tivesse")
    frase_put = skill_ref.OPCOES_LASTREADAS["educacional"]["put_protecao"]
    assert frase_put.startswith("Se você tivesse")


def test_vocab_txt_modo_desconhecido_cai_no_educacional():
    esperado = skill_ref.opcoes_lastreadas_txt("educacional", "sem_lastro", ticker="PETR4")
    obtido = skill_ref.opcoes_lastreadas_txt("modo-inexistente", "sem_lastro", ticker="PETR4")
    assert obtido == esperado


def test_vocab_txt_interpolacao_completa_nao_deixa_marcador_solto():
    frase = skill_ref.opcoes_lastreadas_txt(
        "operador", "call_coberta", n="1", ticker="PETR4", strike="30,00", premioTotal="150,00")
    assert "{" not in frase and "}" not in frase


def test_vocab_txt_aliases_sem_setup_caem_na_mesma_frase():
    base = skill_ref.opcoes_lastreadas_txt("operador", "sem_setup", ticker="PETR4")
    for alias in ("tendencia_de_alta", "sem_contrato_liquido", "sem_vencimento_elegivel"):
        assert skill_ref.opcoes_lastreadas_txt("operador", alias, ticker="PETR4") == base


def test_num_br_formata_pt_br_sem_locale():
    assert skill_ref.num_br(1234.5) == "1.234,50"
    assert skill_ref.num_br(0) == "0,00"
    assert skill_ref.num_br(-42.1) == "-42,10"


# ----------------------------- Parte 2: motor -------------------------------

_HOJE = dt.date(2026, 8, 31)
_SPOT = 30.0


def _contrato(strike, symbol, kind, price=1.0, volume=1000, oi=1000, bid=None, ask=None):
    bid = round(price - 0.05, 2) if bid is None else bid
    ask = round(price + 0.05, 2) if ask is None else ask
    return {"contractSymbol": symbol, "optionType": kind, "strike": strike, "lastPrice": price,
            "bid": bid, "ask": ask, "volume": volume, "openInterest": oi, "impliedVolatility": 0.3}


def _cadeia(expiration=None, calls=None, puts=None, status="ok"):
    exp = expiration or (_HOJE + dt.timedelta(days=30)).isoformat()
    return {"providerStatus": status, "underlyingPrice": _SPOT, "expiration": exp,
            "expirations": [exp], "calls": calls or [], "puts": puts or []}


def _posicao(qty=300, qty_travada=0):
    return {"t": "PETR4", "qty": qty, "qtyTravada": qty_travada}


_PLANO_COMPRAR = {"decisao": "COMPRAR", "lado": "alta"}
_PLANO_VENDER = {"decisao": "VENDER", "lado": "baixa"}
_PLANO_NAO_OPERAR = {"decisao": "NÃO OPERAR", "lado": None}

_CALLS_PADRAO = [
    _contrato(32.0, "PETR4F32", "call"),
    _contrato(34.0, "PETR4F34", "call"),
]
_PUTS_PADRAO = [
    _contrato(28.0, "PETR4F28", "put"),
    _contrato(26.0, "PETR4F26", "put"),
]


def test_propor_cadeia_degradada_devolve_motivo_degradado():
    r = opcoes_lastreadas.propor("PETR4", {"providerStatus": "degraded"}, _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "degradado"}


def test_propor_sem_posicao_devolve_motivo_sem_lastro():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), _SPOT, _PLANO_NAO_OPERAR,
                                  None, 100000, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "sem_lastro"}


def test_propor_lastro_parcial_travado_usa_qty_livre_nao_qty_total():
    """300 ações, 200 travadas (CALL coberta já aberta) — 1 contrato, não 3."""
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(qty=300, qty_travada=200), 100000, "operador", _HOJE)
    assert r["proposta"]["contratos"] == 1
    assert r["proposta"]["qtyAcoes"] == 100


def test_propor_plano_comprar_devolve_sem_setup():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO, puts=_PUTS_PADRAO), _SPOT,
                                  _PLANO_COMPRAR, _posicao(), 100000, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "sem_setup"}


def test_propor_plano_vender_propoe_put_com_maior_strike_ate_spot():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(puts=_PUTS_PADRAO), _SPOT, _PLANO_VENDER,
                                  _posicao(), 100000, "operador", _HOJE)
    assert r["motivo"] == "put_protecao"
    assert r["proposta"]["tipo"] == "put_protecao"
    assert r["proposta"]["strike"] == 28.0  # maior strike <= 30.0 (spot)


def test_propor_plano_nao_operar_propoe_call_com_menor_strike_acima_spot():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    assert r["motivo"] == "call_coberta"
    assert r["proposta"]["tipo"] == "call_coberta"
    assert r["proposta"]["strike"] == 32.0  # menor strike > 30.0 (spot)


def test_propor_contratos_iliquidos_devolvem_sem_contrato_liquido():
    calls_iliquidas = [_contrato(32.0, "PETR4F32", "call", volume=0, oi=0, bid=0, ask=0)]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=calls_iliquidas), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "sem_contrato_liquido"}


def test_propor_vencimento_a_5_dias_devolve_sem_vencimento_elegivel():
    exp = (_HOJE + dt.timedelta(days=5)).isoformat()
    r = opcoes_lastreadas.propor("PETR4", _cadeia(expiration=exp, calls=_CALLS_PADRAO), _SPOT,
                                  _PLANO_NAO_OPERAR, _posicao(), 100000, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "sem_vencimento_elegivel"}


def test_propor_put_com_caixa_de_10_reais_devolve_caixa_insuficiente():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(puts=_PUTS_PADRAO), _SPOT, _PLANO_VENDER,
                                  _posicao(), 10.0, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "caixa_insuficiente"}


def test_propor_manchete_muda_com_o_modo_mesma_proposta():
    r_operador = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), _SPOT, _PLANO_NAO_OPERAR,
                                           _posicao(), 100000, "operador", _HOJE)
    r_educacional = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), _SPOT, _PLANO_NAO_OPERAR,
                                              _posicao(), 100000, "educacional", _HOJE)
    assert r_operador["proposta"]["manchete"] != r_educacional["proposta"]["manchete"]
    assert r_operador["proposta"]["manchete"].startswith("Vender")
    assert r_educacional["proposta"]["manchete"].startswith("Se você tivesse")


def test_put_sem_lastro_detecta_posicao_vendida_e_ignora_a_com_lastro_integro():
    option_positions = [
        {"id": "PETR4F28-vendida-lastro", "side": "comprada", "lastro": {"t": "PETR4", "qty": 300}},
        {"id": "PETR4F26-com-lastro", "side": "comprada", "lastro": {"t": "VALE3", "qty": 100}},
    ]
    positions = [
        {"t": "PETR4", "qty": 0},   # ações vendidas depois da compra da put
        {"t": "VALE3", "qty": 200},  # lastro integro
    ]
    ids = opcoes_lastreadas.put_sem_lastro(option_positions, positions)
    assert ids == ["PETR4F28-vendida-lastro"]
