"""Fase 15, Plano 03 — motor de proposta: limite interno `rastrear()`/`avaliar()`
(ENG-01, ENG-04), mais os adaptadores contrato ADR-004 -> perna de payoff.

Módulo PURO sob teste (`server/app/opcoes_motor.py`): sem rede, sem banco, sem
LLM. Cadeia sintética montada no próprio teste, mesmo padrão de
`test_opcoes_lastreadas_proposta.py`.

Parte 1 (Task 1): `rastrear()` — a régua de seleção já em produção
(liquidez >= 40 + strike extremo), generalizada para N resultados, e o corte
de liquidez com fonte única (`opcoes_motor.LIQUIDEZ_MINIMA`).

Parte 2 (Task 2): `avaliar()` e os adaptadores `perna_de_contrato`/
`perna_de_acao` — o segundo lado do limite interno.
"""
import datetime as dt

from app import opcoes_motor


# ─────────────────────────────────────────────────────────────────────────
# Parte 1: rastrear() — fixtures
# ─────────────────────────────────────────────────────────────────────────

_SPOT = 29.0


def _contrato(symbol, kind, strike, price=1.5, volume=5000, oi=None,
              bid=1.48, ask=1.52, delta=None, **extra):
    """Contrato no formato ADR-004 (`options_provider_mydata._clean_contract`)."""
    d = {
        "contractSymbol": symbol, "optionType": kind, "strike": strike,
        "lastPrice": price, "bid": bid, "ask": ask, "volume": volume,
        "openInterest": oi, "impliedVolatility": 0.3, "inTheMoney": False,
        "currency": "BRL", "distancePct": None,
        "greeks": {"delta": delta, "gamma": None, "vega": None, "theta": None, "rho": None},
        "expiration": "2026-09-30",
    }
    d.update(extra)
    return d


def _cadeia_base():
    """Cadeia sintética do `<behavior>`: spot 29.0, calls 30/32/34, puts
    28/26/24, todos líquidos (liquidity_score = 60.0, acima do corte)."""
    calls = [_contrato(f"C{s}", "call", s) for s in (30, 32, 34)]
    puts = [_contrato(f"P{s}", "put", s) for s in (28, 26, 24)]
    return {"providerStatus": "ok", "underlyingPrice": _SPOT,
            "expiration": "2026-09-30", "expirations": ["2026-09-30"],
            "calls": calls, "puts": puts}


# ─────────────────────────────────────────────────────────────────────────
# Parte 1: rastrear() — testes
# ─────────────────────────────────────────────────────────────────────────

def test_rastrear_call_acima_min_retorna_a_mais_proxima():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "call", "referencia": _SPOT, "relacao": "acima", "criterio": "min"})
    assert len(r) == 1
    assert r[0]["strike"] == 30


def test_rastrear_put_abaixo_ou_igual_max_retorna_a_mais_proxima():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "put", "referencia": _SPOT, "relacao": "abaixo_ou_igual", "criterio": "max"})
    assert len(r) == 1
    assert r[0]["strike"] == 28


def test_rastrear_n2_calls_devolve_na_ordem_do_criterio_min():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "call", "referencia": _SPOT, "relacao": "acima", "criterio": "min", "n": 2})
    assert [c["strike"] for c in r] == [30, 32]


def test_rastrear_n2_puts_devolve_na_ordem_do_criterio_max():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "put", "referencia": _SPOT, "relacao": "abaixo_ou_igual", "criterio": "max", "n": 2})
    assert [c["strike"] for c in r] == [28, 26]


def test_rastrear_n_maior_que_candidatos_devolve_todos_sem_levantar():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "call", "referencia": _SPOT, "relacao": "acima", "criterio": "min", "n": 99})
    assert [c["strike"] for c in r] == [30, 32, 34]


def test_rastrear_exclui_last_price_none_zero_negativo():
    cadeia = {"providerStatus": "ok", "calls": [
        _contrato("X40", "call", 40, price=None),
        _contrato("X41", "call", 41, price=0),
        _contrato("X42", "call", 42, price=-1),
        _contrato("X43", "call", 43, price=1.5),
    ], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min", "n": 10})
    assert [c["strike"] for c in r] == [43]


def test_rastrear_exclui_contrato_com_liquidez_abaixo_do_corte():
    cadeia = {"providerStatus": "ok", "calls": [
        _contrato("Y50", "call", 50, price=1.5, volume=10, oi=None, bid=None, ask=None),
    ], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert r == []


def test_rastrear_inclui_caso_real_mydata_sem_open_interest():
    cadeia = {"providerStatus": "ok", "calls": [
        _contrato("Z60", "call", 60, price=1.5, volume=100, oi=None, bid=1.48, ask=1.52),
    ], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert [c["strike"] for c in r] == [60]


def test_rastrear_liquidez_minima_explicita_sobrescreve_default():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(
        cadeia, {"tipo": "call", "referencia": _SPOT, "relacao": "acima",
                 "criterio": "min", "liquidez_minima": 99})
    assert r == []


def test_rastrear_nenhum_candidato_devolve_lista_vazia_nunca_none():
    cadeia = {"providerStatus": "ok", "calls": [], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert r == []
    assert r is not None


def test_rastrear_cadeia_degradada_devolve_lista_vazia():
    cadeia = _cadeia_base()
    cadeia["providerStatus"] = "degraded"
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert r == []


def test_rastrear_cadeia_invalida_devolve_lista_vazia_sem_excecao():
    assert opcoes_motor.rastrear(None, {"tipo": "call"}) == []
    assert opcoes_motor.rastrear({}, {"tipo": "call"}) == []
    assert opcoes_motor.rastrear("nao-e-dict", {"tipo": "call"}) == []


def test_rastrear_sem_relacao_referencia_nao_filtra_por_spot():
    cadeia = _cadeia_base()
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "max"})
    assert [c["strike"] for c in r] == [34]


def test_rastrear_preserva_chaves_originais_do_contrato_adr004():
    cadeia = {"providerStatus": "ok", "calls": [
        _contrato("PETRA30", "call", 30, delta=0.42, distancePct=3.4)
    ], "puts": []}
    r = opcoes_motor.rastrear(cadeia, {"tipo": "call", "criterio": "min"})
    assert len(r) == 1
    assert r[0]["contractSymbol"] == "PETRA30"
    assert r[0]["greeks"]["delta"] == 0.42
    assert r[0]["distancePct"] == 3.4
    assert set(r[0].keys()) >= {"contractSymbol", "optionType", "strike", "lastPrice",
                                 "bid", "ask", "volume", "openInterest", "greeks", "expiration"}


def test_corte_de_liquidez_tem_fonte_unica(monkeypatch):
    """Guardião ATUALIZADO na Fase 16, Plano 01 (LIB-01/LIB-02): a asserção
    original (`opcoes_lastreadas._LIQUIDEZ_MINIMA is opcoes_motor.LIQUIDEZ_MINIMA`)
    comparava dois rebinds do mesmo literal — não provava que só existia UMA
    régua de corte, só que os dois nomes apontavam pro mesmo inteiro. Esta
    fase apaga o rebind local (`_LIQUIDEZ_MINIMA`) e a implementação
    duplicada (`_candidato_valido`/`_escolher_contrato`) inteiras; o guardião
    passa a provar isso de duas formas mais fortes: (1) nenhum dos dois nomes
    sobrevive no módulo; (2) `propor()` delega a seleção a
    `opcoes_motor.rastrear()` e nunca repassa `liquidez_minima` nos filtros —
    o corte só pode vir do default do motor comum."""
    from app import opcoes_lastreadas

    assert not hasattr(opcoes_lastreadas, "_LIQUIDEZ_MINIMA")
    assert not hasattr(opcoes_lastreadas, "_candidato_valido")

    chamadas = []
    original = opcoes_motor.rastrear

    def _espiao(cadeia, filtros):
        chamadas.append(filtros)
        return original(cadeia, filtros)

    monkeypatch.setattr(opcoes_lastreadas.opcoes_motor, "rastrear", _espiao)

    cadeia = {"providerStatus": "ok", "expiration": "2026-09-30",
              "expirations": ["2026-09-30"], "calls": [],
              "puts": [_contrato("PETRP28", "put", 28.0)]}
    plano = {"decisao": "VENDER", "lado": "baixa"}
    posicao = {"t": "PETR4", "qty": 300, "qtyTravada": 0}
    hoje = dt.date(2026, 8, 31)

    opcoes_lastreadas.propor("PETR4", cadeia, 29.0, plano, posicao, 100000, "operador", hoje)

    assert len(chamadas) >= 1
    assert all("liquidez_minima" not in f for f in chamadas)


# ─────────────────────────────────────────────────────────────────────────
# Parte 2: perna_de_contrato / perna_de_acao / avaliar() — testes
# ─────────────────────────────────────────────────────────────────────────

def test_perna_de_contrato_call_mapeia_campo_a_campo():
    c = {"contractSymbol": "PETRA30", "optionType": "call", "strike": 30,
         "lastPrice": 1.5, "greeks": {"delta": 0.42}}
    p = opcoes_motor.perna_de_contrato(c, "venda")
    assert p == {"contrato": "PETRA30", "tipo": "CALL", "lado": "venda",
                 "strike": 30, "premio": 1.5, "quantidade": 1, "delta": 0.42}


def test_perna_de_contrato_put_vira_tipo_put():
    c = {"contractSymbol": "PETRP28", "optionType": "put", "strike": 28,
         "lastPrice": 0.8, "greeks": {"delta": -0.3}}
    p = opcoes_motor.perna_de_contrato(c, "compra")
    assert p["tipo"] == "PUT"


def test_perna_de_contrato_option_type_desconhecido_levanta_com_symbol():
    c = {"contractSymbol": "PETRX30", "optionType": "warrant", "strike": 30, "lastPrice": 1.5}
    try:
        opcoes_motor.perna_de_contrato(c, "venda")
        assert False, "deveria ter levantado ValueError"
    except ValueError as e:
        assert "PETRX30" in str(e)


def test_perna_de_contrato_sem_premio_levanta_nunca_vira_zero():
    for preco_ruim in (None, 0, -1.5):
        c = {"contractSymbol": "PETRA30", "optionType": "call", "strike": 30, "lastPrice": preco_ruim}
        try:
            opcoes_motor.perna_de_contrato(c, "venda")
            assert False, f"deveria ter levantado ValueError para lastPrice={preco_ruim!r}"
        except ValueError as e:
            assert "PETRA30" in str(e)


def test_perna_de_contrato_sem_greeks_produz_delta_none_sem_levantar():
    c = {"contractSymbol": "PETRA30", "optionType": "call", "strike": 30, "lastPrice": 1.5}
    p = opcoes_motor.perna_de_contrato(c, "venda")
    assert p["delta"] is None

    c2 = {"contractSymbol": "PETRA31", "optionType": "call", "strike": 31,
          "lastPrice": 1.5, "greeks": {"delta": None}}
    p2 = opcoes_motor.perna_de_contrato(c2, "venda")
    assert p2["delta"] is None


def test_perna_de_contrato_quantidade_default_1_e_respeita_argumento():
    c = {"contractSymbol": "PETRA30", "optionType": "call", "strike": 30, "lastPrice": 1.5}
    assert opcoes_motor.perna_de_contrato(c, "venda")["quantidade"] == 1
    assert opcoes_motor.perna_de_contrato(c, "venda", quantidade=3)["quantidade"] == 3


def test_perna_de_contrato_quantidade_nao_positiva_levanta():
    c = {"contractSymbol": "PETRA30", "optionType": "call", "strike": 30, "lastPrice": 1.5}
    try:
        opcoes_motor.perna_de_contrato(c, "venda", quantidade=0)
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        pass


def test_perna_de_acao_monta_perna_de_lastro():
    p = opcoes_motor.perna_de_acao("PETR4", 30.0, 100)
    assert p == {"contrato": "PETR4", "tipo": "ACAO", "lado": "compra",
                 "strike": 0.0, "premio": 30.0, "quantidade": 100, "delta": 1.0}


def test_perna_de_acao_preco_invalido_levanta():
    for preco_ruim in (None, 0, -1.0):
        try:
            opcoes_motor.perna_de_acao("PETR4", preco_ruim, 100)
            assert False, f"deveria ter levantado ValueError para preco={preco_ruim!r}"
        except ValueError:
            pass


def test_avaliar_venda_coberta_duas_pernas():
    pernas = [
        opcoes_motor.perna_de_acao("PETR4", 30.0, 1),
        opcoes_motor.perna_de_contrato(
            {"contractSymbol": "C32", "optionType": "call", "strike": 32, "lastPrice": 1.5}, "venda"),
    ]
    r = opcoes_motor.avaliar(pernas)
    assert r["custo_liquido"] == 28.5
    assert r["ganho_maximo"] == 3.5
    assert r["ganho_ilimitado"] is False
    assert r["breakevens"] == [28.5]


def test_avaliar_collar_tres_pernas_trava_os_dois_lados():
    pernas = [
        opcoes_motor.perna_de_acao("PETR4", 30.0, 1),
        opcoes_motor.perna_de_contrato(
            {"contractSymbol": "C33", "optionType": "call", "strike": 33, "lastPrice": 1.0}, "venda"),
        opcoes_motor.perna_de_contrato(
            {"contractSymbol": "P28", "optionType": "put", "strike": 28, "lastPrice": 0.8}, "compra"),
    ]
    r = opcoes_motor.avaliar(pernas)
    assert r["ganho_ilimitado"] is False
    assert r["perda_ilimitada"] is False


def test_avaliar_sem_pernas_levanta_citando_sem_pernas():
    try:
        opcoes_motor.avaliar([])
        assert False, "deveria ter levantado ValueError"
    except ValueError as e:
        assert "sem pernas" in str(e)


def test_avaliar_saida_contem_chaves_minimas():
    r = opcoes_motor.avaliar([opcoes_motor.perna_de_acao("PETR4", 30.0, 1)])
    esperadas = {"custo_liquido", "fluxo", "ganho_maximo", "perda_maxima", "ganho_ilimitado",
                 "perda_ilimitada", "breakevens", "delta_total", "curva", "pernas", "unidade"}
    assert esperadas <= set(r.keys())


def test_avaliar_perna_sem_delta_declara_soma_parcial():
    pernas = [
        opcoes_motor.perna_de_acao("PETR4", 30.0, 1),
        opcoes_motor.perna_de_contrato(
            {"contractSymbol": "C32", "optionType": "call", "strike": 32, "lastPrice": 1.5}, "venda"),
    ]
    r = opcoes_motor.avaliar(pernas)
    assert r["delta_total"]["pernas_sem_delta"] >= 1
    assert r["delta_total"]["motivo"] is not None


def test_opcoes_motor_nao_importa_camadas_proibidas():
    """Restrição estrutural (Task 2d): só `options_quant`/`opcoes_payoff` e
    stdlib de tipos — sem carteira, banco, sessão, texto de UI ou rede."""
    import ast
    import pathlib

    caminho = pathlib.Path(__file__).parent.parent / "app" / "opcoes_motor.py"
    arvore = ast.parse(caminho.read_text())
    proibidos = {"store", "db", "auth", "skill_ref", "main", "candle_provider",
                 "mydata_client", "httpx", "datetime"}
    encontrados = set()
    for node in ast.walk(arvore):
        if isinstance(node, ast.Import):
            for alias in node.names:
                encontrados.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            modulo = (node.module or "").split(".")[0]
            encontrados.add(modulo)
    assert not (encontrados & proibidos), f"imports proibidos: {encontrados & proibidos}"
