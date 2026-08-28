"""server/tests/test_put_bridge_triagem.py — triagem determinística da put
candidata (Fase 10, Plano 01, Task 2).

Prova de COMPORTAMENTO, não de existência: `triar_put` é função pura sobre o
payload do provedor (formato de `options_provider_mydata`) — nenhuma chamada
de rede, nenhum `httpx`, nenhum `mydata_client`. Cortes: elegibilidade
(estilo de exercício e IV reais, piso de liquidez, strike abaixo do spot),
determinismo, e proveniência anexada sem inventar nada ausente.
"""
from app import put_bridge


def _put(strike, volume=200, iv=0.3, style="americano", symbol=None,
         expiration="2026-09-19", option_type="put", last_price=1.0,
         delta=-0.4):
    symbol = symbol or f"PETRR{int(strike * 10)}"
    return {
        "contractSymbol": symbol,
        "optionType": option_type,
        "strike": strike,
        "lastPrice": last_price,
        "bid": last_price - 0.1,
        "ask": last_price + 0.1,
        "volume": volume,
        "openInterest": None,
        "impliedVolatility": iv,
        "inTheMoney": False,
        "currency": "BRL",
        "distancePct": None,
        "ivStatus": None,
        "theoreticalPrice": None,
        "greeks": {"delta": delta, "gamma": None, "vega": None, "theta": None, "rho": None},
        "expiration": expiration,
        "riskFreeRate": None,
        "exerciseStyle": style,
    }


def _payload(puts=None, calls=None, spot=100.0, provider_status="ok",
             source="mydata", pregao="2026-08-28", provenance=None):
    payload = {
        "ticker": "PETR4",
        "symbol": "PETR4",
        "source": source,
        "providerStatus": provider_status,
        "underlyingPrice": spot,
        "currency": "BRL",
        "expirations": ["2026-09-19"],
        "expiration": "2026-09-19",
        "calls": calls or [],
        "puts": puts or [],
        "pregao": pregao,
    }
    if provenance is not None:
        payload["provenance"] = provenance
    return payload


def test_escolhe_put_mais_proxima_do_colchao():
    payload = _payload(puts=[_put(90), _put(95), _put(98)], spot=100.0)
    candidato, motivo = put_bridge.triar_put(payload)
    assert motivo == ""
    assert candidato["contrato"] == "PETRR950"
    assert candidato["strike"] == 95


def test_determinismo():
    payload = _payload(puts=[_put(90), _put(95), _put(98)], spot=100.0)
    c1, _ = put_bridge.triar_put(payload)
    c2, _ = put_bridge.triar_put(payload)
    assert c1["contrato"] == c2["contrato"]


def test_empate_de_distancia_desempata_por_volume_depois_por_strike():
    # ambas a 2,0 de distância do alvo (95,0): vence maior volume.
    payload_vol = _payload(
        puts=[_put(93, volume=300, symbol="A"), _put(97, volume=100, symbol="B")],
        spot=100.0,
    )
    candidato, _ = put_bridge.triar_put(payload_vol)
    assert candidato["contrato"] == "A"

    # volume igual: vence o menor strike.
    payload_strike = _payload(
        puts=[_put(93, volume=150, symbol="C"), _put(97, volume=150, symbol="D")],
        spot=100.0,
    )
    candidato2, _ = put_bridge.triar_put(payload_strike)
    assert candidato2["contrato"] == "C"


def test_contrato_sem_estilo_de_exercicio_e_pulado():
    payload = _payload(
        puts=[
            _put(95, style=None, symbol="BEST"),      # dist 0, mas sem estilo
            _put(90, style="americano", symbol="SECOND"),  # dist 5, válido
        ],
        spot=100.0,
    )
    candidato, motivo = put_bridge.triar_put(payload)
    assert motivo == ""
    assert candidato["contrato"] == "SECOND"
    assert candidato["puladosSemEstilo"] == 1


def test_contrato_sem_iv_e_pulado():
    payload = _payload(
        puts=[
            _put(95, iv=None, symbol="BEST"),
            _put(90, iv=0.3, symbol="SECOND"),
        ],
        spot=100.0,
    )
    candidato, motivo = put_bridge.triar_put(payload)
    assert motivo == ""
    assert candidato["contrato"] == "SECOND"
    assert candidato["puladosSemIv"] == 1


def test_abaixo_do_piso_de_liquidez_e_pulado():
    payload = _payload(
        puts=[
            _put(95, volume=50, symbol="BEST"),
            _put(90, volume=200, symbol="SECOND"),
        ],
        spot=100.0,
    )
    candidato, motivo = put_bridge.triar_put(payload)
    assert motivo == ""
    assert candidato["contrato"] == "SECOND"
    assert candidato["puladosSemLiquidez"] == 1


def test_strike_acima_do_spot_e_pulado():
    payload = _payload(
        puts=[_put(105, symbol="ABOVE"), _put(90, symbol="BELOW")],
        spot=100.0,
    )
    candidato, motivo = put_bridge.triar_put(payload)
    assert motivo == ""
    assert candidato["contrato"] == "BELOW"


def test_call_nunca_e_candidata():
    payload = _payload(
        puts=[_put(90, symbol="ONLYPUT")],
        calls=[_put(95, symbol="CALLPERFECT", option_type="call")],
        spot=100.0,
    )
    candidato, motivo = put_bridge.triar_put(payload)
    assert motivo == ""
    assert candidato["contrato"] == "ONLYPUT"


def test_payload_degradado_devolve_none_com_motivo():
    payload = _payload(puts=[_put(90)], spot=100.0, provider_status="degraded")
    candidato, motivo = put_bridge.triar_put(payload)
    assert candidato is None
    assert motivo == "fonte degradada"


def test_payload_sem_spot_devolve_none_com_motivo():
    payload = _payload(puts=[_put(90)], spot=None)
    candidato, motivo = put_bridge.triar_put(payload)
    assert candidato is None
    assert motivo == "sem preço do ativo-objeto"


def test_cadeia_sem_puts_devolve_none_com_motivo():
    payload = _payload(puts=[], spot=100.0)
    candidato, motivo = put_bridge.triar_put(payload)
    assert candidato is None
    assert motivo == "sem cadeia de puts"


def test_nenhuma_put_elegivel_devolve_none_com_motivo():
    payload = _payload(puts=[_put(95, volume=50)], spot=100.0)
    candidato, motivo = put_bridge.triar_put(payload)
    assert candidato is None
    assert motivo == "nenhuma put elegível"


def test_candidato_carrega_proveniencia_do_payload():
    provenance = {
        "sha256": "abc123",
        "dt_captura": "2026-08-28T20:05:00Z",
        "captura": "COTAHIST_D28082026.TXT",
    }
    payload = _payload(puts=[_put(90)], spot=100.0, source="mydata",
                        pregao="2026-08-28", provenance=provenance)
    candidato, _ = put_bridge.triar_put(payload)
    assert candidato["fonte"] == "mydata"
    assert candidato["asOf"] == "2026-08-28"
    assert candidato["provSha256"] == "abc123"
    assert candidato["provDtCaptura"] == "2026-08-28T20:05:00Z"
    assert candidato["provCaptura"] == "COTAHIST_D28082026.TXT"

    payload_sem_prov = _payload(puts=[_put(90)], spot=100.0)
    candidato2, _ = put_bridge.triar_put(payload_sem_prov)
    assert candidato2["provSha256"] is None
    assert candidato2["provDtCaptura"] is None
    assert candidato2["provCaptura"] is None
