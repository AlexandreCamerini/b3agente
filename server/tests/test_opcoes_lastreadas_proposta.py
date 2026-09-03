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


# ------------------- Parte 2b: motor comum (Fase 16, Plano 01) --------------
# `propor()` migrou a seleção de contrato para `opcoes_motor.rastrear()`.
# `spot` inutilizável (None/0/negativo/bool/string) precisa degradar
# explicitamente ANTES de chegar em `rastrear()`, porque `rastrear()` IGNORA
# silenciosamente uma `referencia` não-numérica (opcoes_motor.py:95-98) — sem
# a guarda, a proposta escolheria o contrato de menor strike da cadeia
# inteira em vez de degradar (CLAUDE.md princípio 4).

def test_propor_spot_none_devolve_degradado():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), None, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "degradado"}


def test_propor_spot_zero_devolve_degradado():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), 0, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "degradado"}


def test_propor_spot_negativo_devolve_degradado():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), -1, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "degradado"}


def test_propor_spot_bool_devolve_degradado():
    """`True` é subclasse de `int` em Python — vazaria como spot=1 se não
    fosse recusado explicitamente."""
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), True, _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "degradado"}


def test_propor_spot_string_devolve_degradado():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), "30", _PLANO_NAO_OPERAR,
                                  _posicao(), 100000, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "degradado"}


def test_propor_put_empate_de_strike_devolve_ultimo_da_ordem():
    """`rastrear(criterio="max")` ordena ascendente e inverte — o ÚLTIMO
    strike empatado vence, diferente do `max()` local anterior (que devolvia
    o PRIMEIRO). Divergência deliberada (Fase 16, Plano 01): cadeia real da
    B3 não repete strike no mesmo tipo e vencimento, e a régua única
    (compartilhada com o motor comum) vale mais que preservar o desempate
    arbitrário de antes."""
    puts_empatados = [
        _contrato(28.0, "PUT_A", "put"),
        _contrato(28.0, "PUT_B", "put"),
    ]
    r = opcoes_lastreadas.propor("PETR4", _cadeia(puts=puts_empatados), _SPOT, _PLANO_VENDER,
                                  _posicao(), 100000, "operador", _HOJE)
    assert r["proposta"]["contractSymbol"] == "PUT_B"


# --------------- Parte 2c: payoff da estrutura + caixa (Task 2) -------------
# `propor()` passa a montar `estrutura` (perfil de RISCO da posição completa
# ação+opção, via `opcoes_motor.avaliar`) e `caixa` (movimento de caixa de
# HOJE, só das pernas de opção) como campos aditivos — nenhum campo
# pré-existente muda.

def test_propor_venda_coberta_estrutura_tem_ganho_limitado_e_breakeven():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(qty=300), 100000, "operador", _HOJE)
    estrutura = r["proposta"]["estrutura"]
    assert estrutura["ganho_ilimitado"] is False
    assert estrutura["perda_ilimitada"] is False
    assert estrutura["ganho_maximo"] == 3.0  # 32 - 30 + 1 (strike - spot + prêmio)
    assert estrutura["perda_maxima"] == 29.0  # 30 - 1 (spot - prêmio)
    assert estrutura["breakevens"] == [29.0]


def test_propor_venda_coberta_caixa_nao_inclui_a_acao_ja_detida():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(qty=300), 100000, "operador", _HOJE)
    assert r["proposta"]["contratos"] == 3
    assert r["proposta"]["caixa"] == {
        "custoLiquidoUnitario": -1.0, "custoLiquidoTotal": -300.0, "fluxo": "credito",
    }


def test_propor_venda_coberta_preco_objeto_eh_o_spot():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(qty=300), 100000, "operador", _HOJE)
    assert r["proposta"]["precoObjeto"] == 30.0


def test_propor_venda_coberta_pernas_da_estrutura_acao_primeiro():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(qty=300), 100000, "operador", _HOJE)
    pernas = r["proposta"]["estrutura"]["pernas"]
    assert len(pernas) == 2
    assert pernas[0]["tipo"] == "ACAO"
    assert pernas[0]["premio"] == _SPOT
    assert pernas[1]["tipo"] == "CALL"
    assert pernas[1]["lado"] == "venda"


def _put_09():
    """Put de proteção com prêmio 0.9, mesmo padrão de strike/liquidez de
    `_PUTS_PADRAO`, exigido pelos números exatos do bloco `<behavior>` da
    Task 2 (perda_maxima == 2.9 = 30 - 28 + 0.9)."""
    return [_contrato(28.0, "PETR4F28", "put", price=0.9)]


def test_propor_put_protecao_estrutura_tem_ganho_ilimitado_e_perda_limitada():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(puts=_put_09()), _SPOT, _PLANO_VENDER,
                                  _posicao(qty=100), 1_000_000, "operador", _HOJE)
    estrutura = r["proposta"]["estrutura"]
    assert estrutura["ganho_ilimitado"] is True
    assert estrutura["ganho_maximo"] is None
    assert estrutura["perda_ilimitada"] is False
    assert estrutura["perda_maxima"] == 2.9  # 30 - 28 + 0.9


def test_propor_put_protecao_caixa_eh_debito_do_premio():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(puts=_put_09()), _SPOT, _PLANO_VENDER,
                                  _posicao(qty=100), 1_000_000, "operador", _HOJE)
    assert r["proposta"]["caixa"]["fluxo"] == "debito"
    assert r["proposta"]["caixa"]["custoLiquidoUnitario"] == 0.9


def test_propor_campos_preexistentes_intactos_apos_campos_de_payoff():
    r = opcoes_lastreadas.propor("PETR4", _cadeia(calls=_CALLS_PADRAO), _SPOT, _PLANO_NAO_OPERAR,
                                  _posicao(qty=300), 100000, "operador", _HOJE)
    p = r["proposta"]
    assert p["tipo"] == "call_coberta"
    assert p["contractSymbol"] == "PETR4F32"
    assert p["optionType"] == "call"
    assert p["strike"] == 32.0
    assert p["expiration"] == _cadeia().get("expiration")
    assert p["diasParaVencimento"] == 30
    assert p["contratos"] == 3
    assert p["qtyAcoes"] == 300
    assert p["premioUnitario"] == 1.0
    assert p["premioTotal"] == 300.0
    assert p["lastro"] == {"t": "PETR4", "qtyLivre": 300}
    assert set(p["liquidez"].keys()) == {"score", "label"}
    assert p["manchete"].startswith("Vender")
    assert p["didatica"].startswith("Se você tivesse")
    assert [c["k"] for c in p["chips"]] == ["prazo", "strike", "prêmio", "liquidez"]


def test_proposta_fechar_nao_ganha_campos_de_payoff():
    cadeia = _cadeia(calls=[_contrato(32.0, "PETR4F32", "call", price=1.75)])
    pos = {"id": "PETR4F32", "underlying": "PETR4", "optionType": "call", "strike": 32.0,
           "expiration": cadeia["expiration"], "qty": 100, "avg": 1.0, "side": "vendida",
           "lastro": {"t": "PETR4", "qty": 100}}
    r = opcoes_lastreadas.proposta_fechar(pos, cadeia, "operador", _HOJE)
    assert "estrutura" not in r["proposta"]
    assert "caixa" not in r["proposta"]
    assert "precoObjeto" not in r["proposta"]


# ------------------------- Parte 3: proposta_fechar -------------------------
# Bugfix do checkpoint humano do Plano 08: `propor()` é stateless e podia
# devolver um contrato DIFERENTE do já aberto a cada chamada; `proposta_fechar`
# lê o MESMO contrato (por `id`) direto da posição já aberta, sem re-escolher.

def _pos_opcao(id="PETR4F32", underlying="PETR4", optionType="call", strike=32.0,
               expiration=None, qty=100, side="vendida", lastro_qty=None):
    exp = expiration or (_HOJE + dt.timedelta(days=30)).isoformat()
    return {
        "id": id, "underlying": underlying, "optionType": optionType, "strike": strike,
        "expiration": exp, "qty": qty, "avg": 1.0, "side": side,
        "lastro": {"t": underlying, "qty": lastro_qty if lastro_qty is not None else qty},
    }


def test_proposta_fechar_cadeia_degradada_devolve_motivo_degradado():
    r = opcoes_lastreadas.proposta_fechar(_pos_opcao(), {"providerStatus": "degraded"}, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "degradado"}


def test_proposta_fechar_contrato_sumiu_da_cadeia_devolve_motivo_degradado():
    """Contrato aberto (PETR4F32) não está mais na cadeia atual (só PETR4F99
    sobrou) — nunca inventa prêmio a partir de outro contrato."""
    outra_cadeia = _cadeia(calls=[_contrato(99.0, "PETR4F99", "call")])
    r = opcoes_lastreadas.proposta_fechar(_pos_opcao(id="PETR4F32"), outra_cadeia, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "degradado"}


def test_proposta_fechar_sem_last_price_valido_devolve_motivo_degradado():
    cadeia = _cadeia(calls=[{**_contrato(32.0, "PETR4F32", "call"), "lastPrice": None}])
    r = opcoes_lastreadas.proposta_fechar(_pos_opcao(id="PETR4F32"), cadeia, "operador", _HOJE)
    assert r == {"proposta": None, "motivo": "degradado"}


def test_proposta_fechar_call_coberta_devolve_mesmo_contrato_com_premio_atual():
    cadeia = _cadeia(calls=[_contrato(32.0, "PETR4F32", "call", price=1.75)])
    pos = _pos_opcao(id="PETR4F32", side="vendida", qty=100)
    r = opcoes_lastreadas.proposta_fechar(pos, cadeia, "operador", _HOJE)
    assert r["motivo"] == "call_coberta"
    p = r["proposta"]
    assert p["contractSymbol"] == "PETR4F32"
    assert p["tipo"] == "call_coberta"
    assert p["contratos"] == 1
    assert p["premioUnitario"] == 1.75
    assert p["premioTotal"] == round(1.75 * 100, 2)
    assert p["manchete"].startswith("Vender")


def test_proposta_fechar_put_protecao_devolve_mesmo_contrato_com_premio_atual():
    cadeia = _cadeia(puts=[_contrato(28.0, "PETR4F28", "put", price=0.9)])
    pos = _pos_opcao(id="PETR4F28", optionType="put", strike=28.0, side="comprada", qty=200)
    r = opcoes_lastreadas.proposta_fechar(pos, cadeia, "operador", _HOJE)
    assert r["motivo"] == "put_protecao"
    p = r["proposta"]
    assert p["contractSymbol"] == "PETR4F28"
    assert p["tipo"] == "put_protecao"
    assert p["contratos"] == 2
    assert p["premioTotal"] == round(0.9 * 200, 2)
    assert p["manchete"].startswith("Comprar")


def test_proposta_fechar_estavel_mesmo_quando_propor_divergiria():
    """A mesma leitura que faria `propor()` escolher um contrato NOVO (spot
    mudou / plano técnico mudou pra sem_setup) não afeta `proposta_fechar` —
    ela nunca re-escolhe contrato pelo motor comum, só localiza o `id` já
    aberto."""
    cadeia_calls_novas = _cadeia(calls=[
        _contrato(32.0, "PETR4F32", "call", price=2.10),   # contrato já aberto
        _contrato(34.0, "PETR4F34", "call", price=1.20),   # `propor()` picaria outro se spot mudasse
    ])
    pos = _pos_opcao(id="PETR4F32", side="vendida", qty=100)
    r = opcoes_lastreadas.proposta_fechar(pos, cadeia_calls_novas, "operador", _HOJE)
    assert r["proposta"]["contractSymbol"] == "PETR4F32"
    assert r["proposta"]["premioUnitario"] == 2.10


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
