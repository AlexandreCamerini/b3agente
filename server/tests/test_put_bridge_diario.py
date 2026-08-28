"""server/tests/test_put_bridge_diario.py — cruzamento gatilho×carteira,
consulta sequencial à cadeia e gravação com proveniência (Fase 10, Plano 02,
Task 1).

Prova de COMPORTAMENTO: banco temporário real, provedor SEMPRE
monkeypatchado (`app.options_provider.get_options`) — nenhum teste toca a
rede. `radar_daily.get_stored` também é monkeypatchado (`app.radar_daily.
get_stored`) para controlar o resultado EOD sem depender de um scan real.
"""
from __future__ import annotations

import asyncio

from app import db, put_bridge, put_suggestions


def _conn(tmp_path, nome="t.db"):
    return db.connect(str(tmp_path / nome))


def _run(coro):
    return asyncio.run(coro)


# --------------------------------------------------------------------------- #
# Fixtures — radar (gatilho) e carteira (posições)
# --------------------------------------------------------------------------- #

def _setup(nome="IFR2 (baixa)", lado="baixa", confluencia=2, aposentado=False):
    return {"nome": nome, "lado": lado, "confluencia": confluencia, "aposentado": aposentado}


def _resultado(ticker, setups):
    return {"ticker": ticker, "setups": setups,
            "confluencia": max([s.get("confluencia") or 0 for s in setups], default=0)}


def _radar(results):
    return {"results": results, "scanAt": "2026-08-28T08:45:00-03:00"}


def _posicao(ticker, **overrides):
    p = {"t": ticker, "qty": 100, "avg": 30.0}
    p.update(overrides)
    return p


def _carteira(conn, user_id, tickers):
    db.kv_set(conn, "positions", [_posicao(t) for t in tickers], user_id=user_id)


# --------------------------------------------------------------------------- #
# Fixtures — payload do provedor de opções
# --------------------------------------------------------------------------- #

def _put(strike, volume=200, iv=0.3, style="americano", symbol=None,
         expiration="2026-09-19", last_price=1.0, delta=-0.4):
    symbol = symbol or f"X{int(strike * 10)}"
    return {
        "contractSymbol": symbol, "optionType": "put", "strike": strike,
        "lastPrice": last_price, "volume": volume, "impliedVolatility": iv,
        "exerciseStyle": style, "greeks": {"delta": delta},
        "expiration": expiration,
    }


def _payload(ticker, puts=None, spot=100.0, provider_status="ok",
             source="mydata", pregao="2026-08-28", provenance=None,
             provider_error=None):
    payload = {
        "ticker": ticker, "providerStatus": provider_status,
        "underlyingPrice": spot, "puts": puts or [],
        "source": source, "pregao": pregao,
    }
    if provenance is not None:
        payload["provenance"] = provenance
    if provider_error is not None:
        payload["providerError"] = provider_error
    return payload


def _fake_provider(respostas: dict, chamadas: list, reentrancy: dict | None = None):
    async def _fake(ticker, expiration=None):
        chamadas.append(ticker)
        if reentrancy is not None:
            reentrancy["atual"] = reentrancy.get("atual", 0) + 1
            reentrancy["max"] = max(reentrancy.get("max", 0), reentrancy["atual"])
            await asyncio.sleep(0)
            reentrancy["atual"] -= 1
        resp = respostas.get(ticker)
        if isinstance(resp, Exception):
            raise resp
        if resp is None:
            return _payload(ticker, puts=[])
        return resp
    return _fake


def _mock_radar(monkeypatch, radar_payload):
    monkeypatch.setattr("app.radar_daily.get_stored", lambda *a, **k: radar_payload)


def _mock_provider(monkeypatch, respostas: dict, chamadas: list, reentrancy: dict | None = None):
    monkeypatch.setattr("app.options_provider.get_options",
                         _fake_provider(respostas, chamadas, reentrancy))


# --------------------------------------------------------------------------- #
# run_diario — cruzamento gatilho×carteira
# --------------------------------------------------------------------------- #

def test_ticker_no_radar_e_na_carteira_gera_sugestao(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup()])]))
    _carteira(conn, "u1", ["PETR4"])
    chamadas = []
    _mock_provider(monkeypatch, {"PETR4": _payload("PETR4", puts=[_put(90)], spot=100.0)}, chamadas)

    resumo = _run(put_bridge.run_diario(conn))

    assert resumo["sugestoes"] == 1
    assert put_suggestions.contar(conn) == 1
    linha = put_suggestions.listar(conn)[0]
    assert linha["contrato"] == "X900"
    assert linha["strike"] == 90
    assert linha["vencimento"] == "2026-09-19"
    assert linha["estiloExercicio"] == "americano"
    assert linha["iv"] == 0.3


def test_ticker_so_no_radar_nao_gera(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("VALE3", [_setup()])]))
    _carteira(conn, "u1", ["PETR4"])
    chamadas = []
    _mock_provider(monkeypatch, {}, chamadas)

    resumo = _run(put_bridge.run_diario(conn))

    assert put_suggestions.contar(conn) == 0
    assert chamadas == []
    assert resumo["motivo"] == "nenhum gatilho sobre carteira"


def test_ticker_so_na_carteira_nao_gera(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup()])]))
    _carteira(conn, "u1", ["ITUB4"])
    chamadas = []
    _mock_provider(monkeypatch, {}, chamadas)

    resumo = _run(put_bridge.run_diario(conn))

    assert put_suggestions.contar(conn) == 0
    assert chamadas == []
    assert resumo["motivo"] == "nenhum gatilho sobre carteira"


def test_setup_de_alta_nao_dispara(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup(lado="alta")])]))
    _carteira(conn, "u1", ["PETR4"])
    chamadas = []
    _mock_provider(monkeypatch, {}, chamadas)

    _run(put_bridge.run_diario(conn))

    assert put_suggestions.contar(conn) == 0
    assert chamadas == []


def test_setup_aposentado_nao_dispara(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup(aposentado=True)])]))
    _carteira(conn, "u1", ["PETR4"])
    chamadas = []
    _mock_provider(monkeypatch, {}, chamadas)

    _run(put_bridge.run_diario(conn))

    assert put_suggestions.contar(conn) == 0
    assert chamadas == []


def test_dois_usuarios_mesmo_ticker_uma_consulta_duas_linhas(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup()])]))
    _carteira(conn, "u1", ["PETR4"])
    _carteira(conn, "u2", ["PETR4"])
    chamadas = []
    _mock_provider(monkeypatch, {"PETR4": _payload("PETR4", puts=[_put(90)], spot=100.0)}, chamadas)

    resumo = _run(put_bridge.run_diario(conn))

    assert chamadas.count("PETR4") == 1
    assert put_suggestions.contar(conn) == 2
    assert resumo["sugestoes"] == 2


def test_teto_diario_de_tickers(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    tickers = [f"T{i:02d}" for i in range(1, 16)]  # T01..T15
    results = []
    respostas = {}
    for i, t in enumerate(tickers, start=1):
        results.append(_resultado(t, [_setup(confluencia=i)]))
        _carteira(conn, f"u{i}", [t])
        respostas[t] = _payload(t, puts=[], spot=100.0)  # nenhum candidato elegível, só interessa a chamada
    _mock_radar(monkeypatch, _radar(results))
    chamadas = []
    _mock_provider(monkeypatch, respostas, chamadas)

    resumo = _run(put_bridge.run_diario(conn))

    # maior confluência primeiro: T15 (15) .. T06 (6) — os 10 de maior confluência
    esperados = {f"T{i:02d}" for i in range(6, 16)}
    assert len(chamadas) == 10
    assert set(chamadas) == esperados
    assert resumo["tickers"] == 10


def test_consulta_e_sequencial_nunca_concorrente(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    tickers = ["AAA3", "BBB3", "CCC3"]
    results = [_resultado(t, [_setup()]) for t in tickers]
    for t in tickers:
        _carteira(conn, f"u_{t}", [t])
    _mock_radar(monkeypatch, _radar(results))
    respostas = {t: _payload(t, puts=[_put(90)], spot=100.0) for t in tickers}
    chamadas = []
    reentrancy = {"atual": 0, "max": 0}
    _mock_provider(monkeypatch, respostas, chamadas, reentrancy)

    _run(put_bridge.run_diario(conn))

    assert reentrancy["max"] <= 1
    assert len(chamadas) == 3


def test_cota_esgotada_nao_grava_e_nao_levanta(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup()])]))
    _carteira(conn, "u1", ["PETR4"])
    chamadas = []
    payload_recusa = _payload("PETR4", puts=[], spot=None, provider_status="degraded",
                               provider_error="sem cota mydata (60/min · 2.000/dia)")
    _mock_provider(monkeypatch, {"PETR4": payload_recusa}, chamadas)

    resumo = _run(put_bridge.run_diario(conn))

    assert put_suggestions.contar(conn) == 0
    assert resumo["pulados"] == [{"ticker": "PETR4", "motivo": "fonte degradada"}]
    assert resumo["erros"] == []


def test_um_ticker_que_levanta_nao_aborta_os_demais(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    results = [_resultado("PETR4", [_setup(confluencia=5)]),
               _resultado("VALE3", [_setup(confluencia=4)])]
    _mock_radar(monkeypatch, _radar(results))
    _carteira(conn, "u1", ["PETR4"])
    _carteira(conn, "u2", ["VALE3"])
    respostas = {
        "PETR4": RuntimeError("boom"),
        "VALE3": _payload("VALE3", puts=[_put(90)], spot=100.0),
    }
    chamadas = []
    _mock_provider(monkeypatch, respostas, chamadas)

    resumo = _run(put_bridge.run_diario(conn))

    assert put_suggestions.contar(conn) == 1
    assert put_suggestions.listar(conn)[0]["ticker"] == "VALE3"
    assert len(resumo["erros"]) == 1
    assert "PETR4" in resumo["erros"][0]


def test_contrato_sem_estilo_de_exercicio_nao_vira_linha(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup()])]))
    _carteira(conn, "u1", ["PETR4"])
    payload = _payload("PETR4", puts=[_put(90, style=None)], spot=100.0)
    chamadas = []
    _mock_provider(monkeypatch, {"PETR4": payload}, chamadas)

    resumo = _run(put_bridge.run_diario(conn))

    assert put_suggestions.contar(conn) == 0
    assert resumo["pulados"] == [{"ticker": "PETR4", "motivo": "nenhuma put elegível"}]


def test_rodar_duas_vezes_no_mesmo_dia_nao_duplica(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup()])]))
    _carteira(conn, "u1", ["PETR4"])
    chamadas = []
    _mock_provider(monkeypatch, {"PETR4": _payload("PETR4", puts=[_put(90)], spot=100.0)}, chamadas)

    _run(put_bridge.run_diario(conn))
    n1 = put_suggestions.contar(conn)
    _run(put_bridge.run_diario(conn))
    n2 = put_suggestions.contar(conn)

    assert n1 == n2 == 1


def test_radar_vencido_nao_roda(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, None)
    _carteira(conn, "u1", ["PETR4"])
    chamadas = []
    _mock_provider(monkeypatch, {}, chamadas)

    resumo = _run(put_bridge.run_diario(conn))

    assert put_suggestions.contar(conn) == 0
    assert chamadas == []
    assert resumo["motivo"] == "radar do dia indisponível"


def test_proveniencia_gravada_quando_a_fonte_publica(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup()])]))
    _carteira(conn, "u1", ["PETR4"])
    provenance = {"sha256": "abc", "dt_captura": "2026-08-27T21:00:00",
                  "captura": "COTAHIST_D27082026.TXT"}
    payload = _payload("PETR4", puts=[_put(90)], spot=100.0, source="mydata",
                        pregao="2026-08-28", provenance=provenance)
    chamadas = []
    _mock_provider(monkeypatch, {"PETR4": payload}, chamadas)

    _run(put_bridge.run_diario(conn))

    linha = put_suggestions.listar(conn)[0]
    assert linha["provSha256"] == "abc"
    assert linha["provDtCaptura"] == "2026-08-27T21:00:00"
    assert linha["provCaptura"] == "COTAHIST_D27082026.TXT"
    assert linha["fonte"] == "mydata"
    assert linha["asOf"] == "2026-08-28"


def test_proveniencia_ausente_grava_nulo_nunca_placeholder(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup()])]))
    _carteira(conn, "u1", ["PETR4"])
    payload = _payload("PETR4", puts=[_put(90)], spot=100.0)
    chamadas = []
    _mock_provider(monkeypatch, {"PETR4": payload}, chamadas)

    _run(put_bridge.run_diario(conn))

    linha = put_suggestions.listar(conn)[0]
    assert linha["provSha256"] is None
    assert linha["provDtCaptura"] is None
    assert linha["provCaptura"] is None
    assert put_suggestions.contar(conn) == 1  # proveniência mínima (fonte) já é suficiente


def test_ticker_de_posicao_bruto_e_normalizado(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup()])]))
    _carteira(conn, "u1", ["petr4.sa"])
    payload = _payload("PETR4", puts=[_put(90)], spot=100.0)
    chamadas = []
    _mock_provider(monkeypatch, {"PETR4": payload}, chamadas)

    _run(put_bridge.run_diario(conn))

    assert put_suggestions.contar(conn) == 1
    assert put_suggestions.listar(conn)[0]["ticker"] == "PETR4"


def test_balde_anonimo_e_ignorado(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _mock_radar(monkeypatch, _radar([_resultado("PETR4", [_setup()])]))
    db.kv_set(conn, "positions", [_posicao("PETR4")], user_id=None)  # balde anônimo, sem prefixo u:
    chamadas = []
    _mock_provider(monkeypatch, {}, chamadas)

    resumo = _run(put_bridge.run_diario(conn))

    assert put_suggestions.contar(conn) == 0
    assert chamadas == []
    assert resumo["motivo"] == "nenhum gatilho sobre carteira"


# --------------------------------------------------------------------------- #
# maybe_run — gate diário e propagação de exceção
# --------------------------------------------------------------------------- #

def test_maybe_run_respeita_gate_diario(tmp_path, monkeypatch):
    conn = _conn(tmp_path)

    def _boom(conn_arg, now=None):
        raise AssertionError("run_diario não deveria ser chamado")

    monkeypatch.setattr(put_bridge, "run_diario", _boom)

    hoje = put_bridge.datetime.now(put_bridge.BRT).date().isoformat()
    db.kv_set(conn, put_bridge.K_LAST_RUN, hoje, user_id=None)
    assert _run(put_bridge.maybe_run(conn)) is None

    conn2 = _conn(tmp_path, nome="t2.db")
    monkeypatch.setenv("B3_PUT_BRIDGE_OFF", "1")
    assert _run(put_bridge.maybe_run(conn2)) is None


def test_maybe_run_nunca_propaga_excecao(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    monkeypatch.setattr(put_bridge, "should_run", lambda **kw: True)
    monkeypatch.setattr(put_bridge, "enabled", lambda: True)

    async def _boom(conn_arg, now=None):
        raise RuntimeError("boom put-bridge")

    monkeypatch.setattr(put_bridge, "run_diario", _boom)

    resultado = _run(put_bridge.maybe_run(conn))

    assert resultado is None
    assert put_bridge.LAST_RUN["erro"] is not None
    assert "boom put-bridge" in put_bridge.LAST_RUN["erro"]
    assert put_bridge.last_run_date(conn) is None
