"""Fase 50 (50-06, D-16) — strikes das opções lastreadas ancorados nos marcos."""
import datetime as dt

from app import opcoes_lastreadas, opcoes_motor, skill_ref

_HOJE = dt.date(2026, 10, 22)
_EXP = (_HOJE + dt.timedelta(days=30)).isoformat()
_SPOT = 21.0


def _c(strike, kind, price=0.5):
    return {"contractSymbol": f"X{kind[0]}{strike}", "optionType": kind, "strike": strike,
            "lastPrice": price, "bid": price - 0.02, "ask": price + 0.02,
            "volume": 1000, "openInterest": 1000, "impliedVolatility": 0.3}


def _cad(calls=(), puts=()):
    return {"providerStatus": "ok", "underlyingPrice": _SPOT, "expiration": _EXP,
            "expirations": [_EXP], "calls": [_c(k, "call") for k in calls],
            "puts": [_c(k, "put") for k in puts]}


def _pos(**kw):
    return {"t": "PETR4", "qty": 300, "qtyTravada": 0, "avg": 20.0, **kw}


_NEUTRO = {"decisao": "NÃO OPERAR", "lado": None}
_BAIXA = {"decisao": "VENDER", "lado": "baixa"}


def _prop(chain, plano, pos, modo="operador", **kw):
    return opcoes_lastreadas.propor("PETR4", chain, _SPOT, plano, pos, 10000.0, modo, _HOJE, **kw)


def test_rastrear_acima_ou_igual_inclui_strike_igual_a_referencia():
    ch = _cad(calls=(22, 23.5, 24))
    r = opcoes_motor.rastrear(ch, {"tipo": "call", "referencia": 23.5, "relacao": "acima_ou_igual",
                                    "criterio": "min", "n": 1})
    assert r[0]["strike"] == 23.5
    r2 = opcoes_motor.rastrear(ch, {"tipo": "call", "referencia": 23.5, "relacao": "acima",
                                     "criterio": "min", "n": 1})
    assert r2[0]["strike"] == 24


def test_call_coberta_ancora_no_alvo():
    out = _prop(_cad(calls=(22, 23, 23.5, 24)), _NEUTRO, _pos(stop=19.0, alvo=23.5))
    p = out["proposta"]
    assert p["strike"] == 23.5
    assert p["ancora"] == {"tipo": "alvo", "valor": 23.5,
                           "texto": skill_ref.marcos_plano_txt("operador", "opcao_ancora_alvo", alvo="23,50")}


def test_call_coberta_usa_menor_strike_acima_do_alvo_sem_igualdade():
    out = _prop(_cad(calls=(22, 23, 24, 25)), _NEUTRO, _pos(stop=19.0, alvo=23.5))
    assert out["proposta"]["strike"] == 24
    assert out["proposta"]["ancora"]["tipo"] == "alvo"


def test_put_protecao_ancora_no_strike_mais_proximo_do_stop_empate_vai_para_baixo():
    out = _prop(_cad(puts=(18, 18.75, 19.25, 20)), _BAIXA, _pos(stop=19.0, alvo=23.5))
    p = out["proposta"]
    assert p["strike"] == 18.75
    assert p["ancora"]["tipo"] == "stop" and p["ancora"]["valor"] == 19.0


def test_put_protecao_strike_mais_proximo_acima_do_stop():
    out = _prop(_cad(puts=(17, 19.1, 20.5)), _BAIXA, _pos(stop=19.0, alvo=23.5))
    assert out["proposta"]["strike"] == 19.1


def test_sem_marcos_cai_no_spot_e_declara():
    out = _prop(_cad(calls=(22, 23.5)), _NEUTRO, _pos())
    p = out["proposta"]
    assert p["strike"] == 22
    assert p["ancora"] == {"tipo": "spot", "valor": _SPOT,
                           "texto": skill_ref.marcos_plano_txt("operador", "opcao_ancora_spot")}


def test_marcos_invalidos_caem_no_spot():
    out = _prop(_cad(calls=(22, 23.5)), _NEUTRO, _pos(stop=23.36, alvo=21.58, avg=23.01))
    assert out["proposta"]["strike"] == 22
    assert out["proposta"]["ancora"]["tipo"] == "spot"


def test_alvo_sem_strike_na_cadeia_cai_no_spot_sem_inventar():
    out = _prop(_cad(calls=(22, 23)), _NEUTRO, _pos(stop=19.0, alvo=30.0))
    assert out["proposta"]["strike"] == 22
    assert out["proposta"]["ancora"]["tipo"] == "spot"


def test_alvo_abaixo_do_spot_nao_ancora():
    out = _prop(_cad(calls=(22, 23)), _NEUTRO, _pos(stop=19.0, alvo=20.5))
    assert out["proposta"]["ancora"]["tipo"] == "spot"


def test_collar_call_segue_o_alvo_e_put_o_stop():
    ch = _cad(calls=(22, 23.5, 24), puts=(18, 18.75, 19.25))
    out = _prop(ch, _BAIXA, _pos(stop=19.0, alvo=23.5), multiperna=True)
    por_tipo = {c["tipo"]: c for c in out["candidatos"]}
    assert por_tipo["put_protecao"]["strike"] == 18.75
    colar = por_tipo["collar"]
    assert colar["strikeCall"] == 23.5 and colar["strikePut"] == 18.75
    assert colar["ancora"]["tipo"] == "alvo"


def test_retornos_negativos_sem_chave_nova():
    assert _prop(_cad(), _NEUTRO, _pos(stop=19.0, alvo=23.5)) == {"proposta": None, "motivo": "sem_contrato_liquido"}
    assert _prop({"providerStatus": "x"}, _NEUTRO, _pos()) == {"proposta": None, "motivo": "degradado"}
