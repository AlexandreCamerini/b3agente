"""Quick 260915-ndt — `POST /api/options/curadoria/abrir-collar`, o caminho
de EXECUÇÃO de um collar da lista curada ("AS 4 MELHORES OPORTUNIDADES DE
OPÇÕES") que RE-DERIVA pelo MESMO motor que gerou o card
(`opcoes_curadoria`), nunca por `opcoes_lastreadas.propor()`.

Causa raiz fechada (não re-investigar): `opcoes_curadoria.py` gera a lista
curada SEM porta de setup/plano técnico; `POST /api/options/lastreada/abrir-
collar` re-deriva por `opcoes_lastreadas.propor(..., multiperna=True)`, que
EXIGE `decisao`/`lado` favoráveis — com `decisao == "NÃO OPERAR"` o motor
antigo cai no ramo `call_coberta` (nunca `put_protecao`, o ÚNICO lugar onde
`_propor_collar` é chamado), então `resultado["candidatos"]` nunca contém
tipo "collar" e a rota velha 409a TODO collar curado. A rota nova fecha esse
defeito re-derivando pela varredura que gerou o card.

PROVA CENTRAL: o MESMO cenário (Modo Operador, posição com lote livre,
`setups.plano_do_resultado` devolvendo NÃO OPERAR) devolve 409 na rota velha
e 200 na rota nova.

`B3_OPTIONS_PROVIDER` não é usado aqui (diferente de `test_opcoes_collar_
rota.py`, que usa o provider mock via env) — mesmo padrão de
`test_opcoes_curadoria_rota.py`: monkeypatch direto de `options_provider.
get_options`, arquivo autocontido (padrão da casa: não importar fixture de
outro módulo de teste). A cadeia precisa de calls E puts — as fixtures de
`test_opcoes_curadoria_rota.py` usam `puts: []`, que nunca gera collar.

Não-regressão da extração de `_curadoria_scan_posicao` (de dentro de
`_curadoria_top`): verificada por `test_opcoes_curadoria_rota.py` inteiro
continuar passando sem edição — não duplicada aqui, ver `<verify>` do plano
260915-ndt (roda os dois arquivos juntos)."""
import datetime as dt
import inspect
import uuid

import pytest
from fastapi.testclient import TestClient

from app import candle_provider, db, opcoes_curadoria, options_provider, setups, store, technical_snapshot
from app import main as main_mod
from app.main import app, _conn

_EXP = (dt.date.today() + dt.timedelta(days=30)).isoformat()  # dentro de 15..60 dias
_SPOT = 29.0


def _contrato(symbol, strike, option_type, price=1.5, volume=5000, oi=1000, bid=1.48, ask=1.52, expiration=_EXP):
    """Contrato líquido por padrão (score >= 55: volume alto, spread <= 3%) —
    mesmo padrão de `test_opcoes_curadoria_rota.py`, com `optionType`
    parametrizado (a fixture de lá é só-call)."""
    return {
        "contractSymbol": symbol, "optionType": option_type, "strike": strike,
        "lastPrice": price, "bid": bid, "ask": ask, "volume": volume,
        "openInterest": oi, "impliedVolatility": 0.3, "inTheMoney": False,
        "currency": "BRL", "distancePct": None,
        "greeks": {"delta": None, "gamma": None, "vega": None, "theta": None, "rho": None},
        "expiration": expiration,
    }


def _cadeia(underlying, provider_status="ok", spot=_SPOT, expiration=_EXP,
            expirations=None, call_price=1.5, put_price=1.2):
    """Cadeia sintética com UMA call OTM acima do spot e UMA put OTM/ATM
    abaixo do spot, as duas líquidas — o mínimo para
    `opcoes_curadoria.candidatos_da_posicao` gerar um candidato de collar
    (a fixture-irmã de `test_opcoes_curadoria_rota.py` usa `puts: []`, que
    NUNCA gera collar).

    DEVIATION (Fase 39, Plano 01, 2026-09-24, Rule 1 — auto-fix): strikes
    espaçados 3.0 do spot (antes: 1.0), não 1.0 — este arquivo é anterior ao
    piso de probabilidade OTM (D-08) e sua geometria original (call
    spot+1/put spot-1, ~30 dias) fica MUITO perto do dinheiro para o collar
    passar em `probOtm >= 0.60` (`1 - P(call ITM) - P(put ITM)`, calculado
    com os dois pernas próximas do spot fica ~0.31, medido). Widening é
    correção de fixture pré-D-08, não fraqueamento do piso: `PISO_PROB_OTM`
    continua 0.60, nada foi monkeypatchado. Ver SUMMARY do plano 39-01.
    """
    cs = round(spot + 3, 2)
    ps = round(spot - 3, 2)
    calls = [_contrato(f"{underlying}C{cs}", cs, "call", price=call_price, expiration=expiration)]
    puts = [_contrato(f"{underlying}P{ps}", ps, "put", price=put_price, expiration=expiration)]
    return {
        "providerStatus": provider_status, "underlyingPrice": spot,
        "expiration": expiration, "expirations": expirations if expirations is not None else [expiration],
        "calls": calls, "puts": puts, "source": "teste",
    }


def _cadeia_2calls(underlying, spot=_SPOT):
    """Mesma cadeia de `_cadeia`, com uma SEGUNDA call (strike mais alto,
    mais distante do spot) que `rastrear(criterio="min")` NUNCA escolhe —
    dá um `contractSymbol` REAL da cadeia, mas DIFERENTE do proposto, para o
    guardião de perna trocada.

    DEVIATION (Fase 39, Plano 01, 2026-09-24, Rule 1): mesmo motivo/ressalva
    de `_cadeia` acima — strikes alargados para o collar re-derivado passar
    no piso de probabilidade OTM (D-08).
    """
    c1 = round(spot + 3, 2)
    c2 = round(spot + 5, 2)
    ps = round(spot - 3, 2)
    calls = [_contrato(f"{underlying}C{c1}", c1, "call"), _contrato(f"{underlying}C{c2}", c2, "call")]
    puts = [_contrato(f"{underlying}P{ps}", ps, "put")]
    return {
        "providerStatus": "ok", "underlyingPrice": spot,
        "expiration": _EXP, "expirations": [_EXP],
        "calls": calls, "puts": puts, "source": "teste",
    }


def _contador(chains: dict):
    """Mesmo helper de `test_opcoes_curadoria_rota.py`: embrulha
    `options_provider.get_options`, registra `(ticker, expiration)`
    chamados, devolve cadeia degradada para ticker não mapeado."""
    chamados: list[tuple[str, str | None]] = []

    async def _fake(ticker, expiration=None, *a, **k):
        chamados.append((ticker, expiration))
        entry = chains.get(ticker)
        if entry is None:
            return _cadeia(ticker, provider_status="degraded")
        if isinstance(entry, dict) and "providerStatus" not in entry:
            cadeia = entry.get(expiration)
            if cadeia is None:
                return _cadeia(ticker, provider_status="degraded")
            return cadeia
        return entry

    return chamados, _fake


async def _bomba_provider(*a, **k):
    raise AssertionError("options_provider.get_options não deveria ter sido chamado")


@pytest.fixture(autouse=True)
def _quote_fake(monkeypatch):
    # Sem rede: `_spot_from_chain_or_quote` prefere `underlyingPrice` da
    # cadeia, mas `candle_provider.get_quote` é chamado incondicionalmente
    # (mesmo achado de `test_opcoes_curadoria_rota.py`).
    async def _fake(t, *a, **k):
        return {"t": t, "price": _SPOT, "source": "teste"}
    monkeypatch.setattr(candle_provider, "get_quote", _fake)


@pytest.fixture(autouse=True)
def _snapshot_fake(monkeypatch):
    """A rota IRMÃ (`/lastreada/abrir-collar`, exercitada só pela prova
    central) chama `technical_snapshot.get` — mockada para nunca bater na
    rede; o conteúdo não importa porque o teste monkeypatcha
    `setups.plano_do_resultado` direto (fixture abaixo)."""
    async def _fake_get(ticker, period, loader, interval="1d"):
        return {"setups": {"setups": []}, "close": _SPOT}
    monkeypatch.setattr(technical_snapshot, "get", _fake_get)


@pytest.fixture
def _plano_nao_operar(monkeypatch):
    """`setups.plano_do_resultado` devolvendo NÃO OPERAR
    (`setups.DECISAO_NAO_OPERAR`) — o cenário comum em que a leitura técnica
    não endossa collar. Confirmado por leitura de
    `opcoes_lastreadas.propor()`: `decisao == "NÃO OPERAR"` cai no ramo
    `tipo = "call_coberta"` (nunca no ramo `put_protecao`, o ÚNICO lugar em
    que `_propor_collar` é chamado) — `resultado["candidatos"]` nunca tem
    tipo "collar", e a rota velha 409a."""
    monkeypatch.setattr(setups, "plano_do_resultado", lambda *a, **k: {"decisao": "NÃO OPERAR", "lado": None})


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _novo_escopo(cli, slug):
    email = f"curadoria-collar-{slug}-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"]["id"], {"Authorization": "Bearer " + body["token"]}


def _liga_operador(user_id):
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id=user_id)


def _seed_posicao(user_id, ticker="PETR4", qty=300, price=30.0):
    store.buy(_conn, ticker, qty, price, user_id=user_id)


def _seed_pronto(cli, monkeypatch, slug, *, cadeia=None, qty=300, price=30.0):
    """Conta nova em Modo Operador, posição PETR4 com lote livre, cadeia
    (calls+puts líquidas por padrão) servida via monkeypatch. Devolve
    `(user_id, headers, chamados)` — `chamados` é a lista de
    `(ticker, expiration)` que bateram no provider, para os guardiões de
    'sem tocar provider'."""
    uid, headers = _novo_escopo(cli, slug)
    _liga_operador(uid)
    _seed_posicao(uid, qty=qty, price=price)
    chain = cadeia if cadeia is not None else _cadeia("PETR4")
    chamados, fake = _contador({"PETR4": chain})
    monkeypatch.setattr(options_provider, "get_options", fake)
    return uid, headers, chamados


def _id_candidato_collar(cli, headers):
    r = cli.get("/api/options/curadoria", headers=headers)
    assert r.status_code == 200, r.text
    top = r.json()["top"]
    collar = next((c for c in top if c["tipo"] == "collar"), None)
    assert collar is not None, top
    return collar


def _pernas_do_candidato(collar):
    return [{"contractSymbol": p["contractSymbol"], "lado": p["lado"]} for p in collar["pernasContratos"]]


# ─────────────────────────────────────────────────────────────────────────
# PROVA CENTRAL
# ─────────────────────────────────────────────────────────────────────────

def test_central_velha_409_nova_200_no_mesmo_cenario(cli, monkeypatch, _plano_nao_operar):
    uid, headers, chamados = _seed_pronto(cli, monkeypatch, "central")

    collar = _id_candidato_collar(cli, headers)
    pernas = _pernas_do_candidato(collar)
    contratos = collar["contratos"]

    # Assert 1: a rota VELHA re-deriva por propor() e 409a — o bug de hoje,
    # preservado de propósito naquela rota (ela serve um card diferente).
    body_velho = {"underlying": "PETR4", "pernasContratos": pernas, "contratos": contratos}
    r_velha = cli.post("/api/options/lastreada/abrir-collar", json=body_velho, headers=headers)
    assert r_velha.status_code == 409, r_velha.text

    # Assert 2: NO MESMO ESCOPO E CENÁRIO, a rota NOVA re-deriva pelo motor
    # da curadoria (o mesmo que gerou o card) e executa.
    body_novo = {"underlying": "PETR4", "idCandidato": collar["idCandidato"],
                 "pernasContratos": pernas, "contratos": contratos}
    r_nova = cli.post("/api/options/curadoria/abrir-collar", json=body_novo, headers=headers)
    assert r_nova.status_code == 200, r_nova.text
    data = r_nova.json()
    pernas_com_lastro = [p for p in data["optionPositions"] if p.get("lastro")]
    assert len(pernas_com_lastro) == 2, data["optionPositions"]
    assert data["cash"] != 10000.0 - 300 * 30.0  # caixa mudou do valor pós-compra da posição


# ─────────────────────────────────────────────────────────────────────────
# Guardiões de adulteração (ADR-026, Decisão 2)
# ─────────────────────────────────────────────────────────────────────────

def test_id_candidato_que_nao_bate_409_sem_abrir_posicao(cli, monkeypatch):
    uid, headers, chamados = _seed_pronto(cli, monkeypatch, "id-invalido")
    collar = _id_candidato_collar(cli, headers)
    body = {"underlying": "PETR4", "idCandidato": "collar:PETR4:2099-01-01:999.0/111.0",
            "pernasContratos": _pernas_do_candidato(collar), "contratos": collar["contratos"]}
    r = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r.status_code == 409, r.text
    st = cli.get("/api/state", headers=headers).json()
    assert st["optionPositions"] == []


def test_perna_contractSymbol_trocado_409(cli, monkeypatch):
    cadeia = _cadeia_2calls("PETR4")
    uid, headers, chamados = _seed_pronto(cli, monkeypatch, "perna-trocada", cadeia=cadeia)
    collar = _id_candidato_collar(cli, headers)
    pernas_certas = _pernas_do_candidato(collar)
    outro_call_symbol = cadeia["calls"][1]["contractSymbol"]  # real na cadeia, NÃO o proposto
    assert outro_call_symbol != pernas_certas[0]["contractSymbol"]
    pernas_erradas = [{"contractSymbol": outro_call_symbol, "lado": "venda"}, pernas_certas[1]]
    body = {"underlying": "PETR4", "idCandidato": collar["idCandidato"],
            "pernasContratos": pernas_erradas, "contratos": collar["contratos"]}
    r = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r.status_code == 409, r.text


def test_lado_invertido_409(cli, monkeypatch):
    uid, headers, chamados = _seed_pronto(cli, monkeypatch, "lado-invertido")
    collar = _id_candidato_collar(cli, headers)
    pernas_certas = _pernas_do_candidato(collar)
    pernas_invertidas = [
        {"contractSymbol": pernas_certas[0]["contractSymbol"], "lado": "compra"},
        {"contractSymbol": pernas_certas[1]["contractSymbol"], "lado": "venda"},
    ]
    body = {"underlying": "PETR4", "idCandidato": collar["idCandidato"],
            "pernasContratos": pernas_invertidas, "contratos": collar["contratos"]}
    r = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r.status_code == 409, r.text


def test_contratos_diferente_do_re_derivado_409(cli, monkeypatch):
    uid, headers, chamados = _seed_pronto(cli, monkeypatch, "contratos-diff")
    collar = _id_candidato_collar(cli, headers)
    assert collar["contratos"] != 1  # 300 ações livres // 100 = 3
    body = {"underlying": "PETR4", "idCandidato": collar["idCandidato"],
            "pernasContratos": _pernas_do_candidato(collar), "contratos": 1}
    r = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r.status_code == 409, r.text


def test_premio_e_strike_inflados_nao_chegam_a_execucao(cli, monkeypatch):
    uid, headers, chamados = _seed_pronto(cli, monkeypatch, "premio-inflado")
    collar = _id_candidato_collar(cli, headers)
    pernas_infladas = [
        {"contractSymbol": p["contractSymbol"], "lado": p["lado"], "premioUnitario": 9999.99, "strike": 1.0}
        for p in collar["pernasContratos"]
    ]
    body = {"underlying": "PETR4", "idCandidato": collar["idCandidato"],
            "pernasContratos": pernas_infladas, "contratos": collar["contratos"]}
    r = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r.status_code == 200, r.text
    usados = r.json()["premiosUsados"]
    assert len(usados) == 2
    for u in usados:
        assert u["premioUnitario"] != 9999.99
        assert 0 < u["premioUnitario"] < 100  # prêmios reais da fixture (~1-2 reais)


def test_id_candidato_de_tipo_errado_409_sem_abrir_venda_coberta(cli, monkeypatch):
    uid, headers, chamados = _seed_pronto(cli, monkeypatch, "tipo-errado")
    r = cli.get("/api/options/curadoria", headers=headers)
    assert r.status_code == 200, r.text
    call_coberta = next(c for c in r.json()["top"] if c["tipo"] == "call_coberta")
    body = {"underlying": "PETR4", "idCandidato": call_coberta["idCandidato"],
            "pernasContratos": [{"contractSymbol": "X", "lado": "venda"},
                                 {"contractSymbol": "Y", "lado": "compra"}],
            "contratos": 1}
    r2 = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r2.status_code == 409, r2.text
    st = cli.get("/api/state", headers=headers).json()
    assert not any(p.get("lastro") for p in st["optionPositions"])


# ─────────────────────────────────────────────────────────────────────────
# Defesas preservadas (tabela do plano)
# ─────────────────────────────────────────────────────────────────────────

def test_modo_estudo_403_sem_tocar_provider(cli, monkeypatch):
    uid, headers = _novo_escopo(cli, "modo-estudo")
    _seed_posicao(uid, qty=300)
    monkeypatch.setattr(options_provider, "get_options", _bomba_provider)
    body = {"underlying": "PETR4", "idCandidato": "collar:PETR4:qualquer:1/2",
            "pernasContratos": [{"contractSymbol": "X", "lado": "venda"},
                                 {"contractSymbol": "Y", "lado": "compra"}],
            "contratos": 1}
    r = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r.status_code == 403, r.text


def test_lastreada_ja_aberta_409_sem_tocar_provider(cli, monkeypatch):
    uid, headers = _novo_escopo(cli, "ja-aberta")
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)
    db.kv_set(_conn, "optionPositions", [{
        "id": "PETR4C30", "underlying": "PETR4", "optionType": "call", "strike": 30.0,
        "expiration": _EXP, "qty": 100, "avg": 1.0, "side": "vendida",
        "lastro": {"t": "PETR4", "qty": 100}, "abertaEm": "2026-01-01",
    }], user_id=uid)
    monkeypatch.setattr(options_provider, "get_options", _bomba_provider)
    body = {"underlying": "PETR4", "idCandidato": "collar:PETR4:qualquer:1/2",
            "pernasContratos": [{"contractSymbol": "X", "lado": "venda"},
                                 {"contractSymbol": "Y", "lado": "compra"}],
            "contratos": 1}
    r = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r.status_code == 409, r.text
    assert "feche-a antes" in r.json()["detail"]


def test_liquidez_dificil_exige_consentimento(cli, monkeypatch):
    uid, headers, chamados = _seed_pronto(cli, monkeypatch, "liq-dificil")
    # Força a faixa DIFÍCIL no candidato RE-DERIVADO: patch de
    # `opcoes_curadoria.liquidity_score` — binding PRÓPRIO do módulo,
    # distinto do de `opcoes_motor` (que continua vendo o score REAL da
    # fixture líquida, então o contrato ainda passa pelo gate de SELEÇÃO de
    # `rastrear()`; só o bloco `liquidez` exibido/re-derivado nasce
    # DIFÍCIL). Mesma técnica que a nota do plano descreve ("o caso de teste
    # força a faixa por fixture") — sem isto o ramo é hoje praticamente
    # inalcançável (PISO_LIQUIDEZ = NEGOCIÁVEL já filtra o que entra).
    monkeypatch.setattr(opcoes_curadoria, "liquidity_score", lambda *a, **k: {"score": 45.0, "spreadPct": 1.0})

    collar = _id_candidato_collar(cli, headers)
    assert collar["liquidez"]["faixa"] == "DIFÍCIL", collar["liquidez"]

    body = {"underlying": "PETR4", "idCandidato": collar["idCandidato"],
            "pernasContratos": _pernas_do_candidato(collar), "contratos": collar["contratos"]}
    r = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r.status_code == 400, r.text
    assert "aceitaLiquidezDificil" in r.json()["detail"]

    body["aceitaLiquidezDificil"] = True
    r2 = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r2.status_code == 200, r2.text


def test_caixa_insuficiente_400_sem_meia_estrutura(cli, monkeypatch):
    cadeia = _cadeia("PETR4", call_price=1.0, put_price=3.0)  # débito líquido (put > call)
    uid, headers, chamados = _seed_pronto(cli, monkeypatch, "caixa-baixa", cadeia=cadeia)
    db.kv_set(_conn, "cash", 10.0, user_id=uid)  # após a compra da posição, quase zero

    collar = _id_candidato_collar(cli, headers)
    body = {"underlying": "PETR4", "idCandidato": collar["idCandidato"],
            "pernasContratos": _pernas_do_candidato(collar), "contratos": collar["contratos"]}
    r = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r.status_code == 400, r.text

    st = cli.get("/api/state", headers=headers).json()
    assert st["optionPositions"] == []  # atomicidade: nenhuma perna meio-aberta


def test_cadeia_degradada_502_nunca_409(cli, monkeypatch):
    uid, headers = _novo_escopo(cli, "degradada")
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)

    async def _fake(*a, **k):
        return _cadeia("PETR4", provider_status="degraded")
    monkeypatch.setattr(options_provider, "get_options", _fake)

    body = {"underlying": "PETR4", "idCandidato": "collar:PETR4:qualquer:1/2",
            "pernasContratos": [{"contractSymbol": "X", "lado": "venda"},
                                 {"contractSymbol": "Y", "lado": "compra"}],
            "contratos": 1}
    r = cli.post("/api/options/curadoria/abrir-collar", json=body, headers=headers)
    assert r.status_code == 502, r.text


# ─────────────────────────────────────────────────────────────────────────
# Guardião estrutural — a rota não confia no corpo (ADR-026, Decisão 2)
# ─────────────────────────────────────────────────────────────────────────

def test_guardiao_estrutural_rota_nao_le_premio_strike_expiration_do_corpo():
    """`inspect.getsource` sobre a função da rota: prova por FONTE (não por
    comportamento observado) de que a re-derivação é do motor da curadoria e
    nenhum número de execução nasce do corpo — mesma técnica de
    `test_rota_de_collar_nao_le_multiperna_do_corpo`/`test_rota_de_collar_
    nao_usa_premio_do_corpo` (já em produção para a rota irmã).

    Isola o CORPO da função (depois do docstring) antes de comparar: o
    docstring da rota EXPLICA por que ela não usa `opcoes_lastreadas.
    propor()` — o plano exige essa explicação em prosa —, então checar a
    fonte inteira acusaria o próprio comentário. O guardião prova que é o
    CÓDIGO, não a explicação em texto, que nunca chama."""
    fonte = inspect.getsource(main_mod.options_curadoria_abrir_collar)
    partes = fonte.split('"""')
    assert len(partes) >= 3, "função sem docstring — isolamento do corpo não se aplica"
    corpo = '"""'.join(partes[2:])
    assert "opcoes_lastreadas" not in corpo
    assert ".propor(" not in corpo
    assert 'body.get("premioUnitario")' not in corpo
    assert 'body["premioUnitario"]' not in corpo
    assert 'body.get("strike")' not in corpo
    assert 'body["strike"]' not in corpo
    assert 'body.get("expiration")' not in corpo
    assert 'body["expiration"]' not in corpo
