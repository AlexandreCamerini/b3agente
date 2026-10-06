"""Fase 48, Plano 06 — rotas da escada de Opções (custo MCP zero).

GET  /api/options/escada/{ticker}   e   POST /api/options/escada/leitura

Provedor de cadeia falso (monkeypatch em `options_provider.get_options`); a
chamada paga do serviço MCP (`options_mcp_api._chamada_com_cap`) é armada
para FALHAR se tocada — é a prova de "custo 0" (T-48-19).
"""
import datetime as dt
import uuid

import pytest
from fastapi.testclient import TestClient

from app import candle_provider, db, options_mcp_api, options_provider, store
from app.main import _conn, app

_EXP = (dt.date.today() + dt.timedelta(days=30)).isoformat()
_EXP2 = (dt.date.today() + dt.timedelta(days=45)).isoformat()
_SPOT = 29.0


def _contrato(symbol, tipo, strike, exp, price=1.5):
    return {
        "contractSymbol": symbol, "optionType": tipo, "strike": strike,
        "lastPrice": price, "bid": price - 0.02, "ask": price + 0.02, "volume": 5000,
        "openInterest": 1000, "impliedVolatility": 0.3, "inTheMoney": False,
        "currency": "BRL", "distancePct": None,
        "greeks": {"delta": None, "gamma": None, "vega": None, "theta": None, "rho": None},
        "expiration": exp,
    }


def _cadeia(ticker, exp=_EXP, expirations=None, com_puts=True):
    calls = [_contrato(f"{ticker}C{k}", "call", k, exp) for k in (30, 31, 32, 33)]
    puts = [_contrato(f"{ticker}P{k}", "put", k, exp) for k in (25, 26, 27, 28)] if com_puts else []
    return {"providerStatus": "ok", "underlyingPrice": _SPOT, "expiration": exp,
            "expirations": expirations if expirations is not None else [_EXP],
            "calls": calls, "puts": puts, "source": "teste", "pregao": "2026-10-02"}


@pytest.fixture(autouse=True)
def _sem_rede(monkeypatch):
    async def _quote(t, *a, **k):
        return {"t": t, "price": _SPOT, "source": "teste"}

    async def _hist(*a, **k):
        raise RuntimeError("sem rede no teste")

    async def _paga(*a, **k):
        raise AssertionError("rota grátis chamou o serviço MCP pago")

    monkeypatch.setattr(candle_provider, "get_quote", _quote)
    monkeypatch.setattr(candle_provider, "get_history", _hist)
    monkeypatch.setattr(options_mcp_api, "_chamada_com_cap", _paga)


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _escopo(cli, com_posicao=True, qty=300):
    email = f"escada-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    b = r.json()
    uid = b["user"]["id"]
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id=uid)
    if com_posicao:
        store.buy(_conn, "PETR4", qty, 25.0, user_id=uid)
    return uid, {"Authorization": "Bearer " + b["token"]}


def _fake(monkeypatch, cadeias=None, erro=False):
    chamados = []

    async def _get(ticker, expiration=None, *a, **k):
        chamados.append((ticker, expiration))
        if erro:
            raise RuntimeError("fonte fora do ar")
        if cadeias is None:
            return _cadeia(ticker)
        return cadeias.get(expiration) or cadeias.get(None)

    monkeypatch.setattr(options_provider, "get_options", _get)
    return chamados


def test_ticker_curto_400(cli, monkeypatch):
    _, h = _escopo(cli)
    _fake(monkeypatch)
    assert cli.get("/api/options/escada/PET", headers=h).status_code == 400


def test_objetivo_fora_da_allowlist_400(cli, monkeypatch):
    _, h = _escopo(cli)
    _fake(monkeypatch)
    assert cli.get("/api/options/escada/PETR4?objetivo=xyz", headers=h).status_code == 400


def test_sem_posicao(cli, monkeypatch):
    _, h = _escopo(cli, com_posicao=False)
    chamados = _fake(monkeypatch)
    r = cli.get("/api/options/escada/PETR4", headers=h)
    assert r.status_code == 200
    j = r.json()
    assert j["estado"] == "sem_posicao" and j["degraus"] == [] and j["motivoTexto"]
    assert len(j["objetivos"]) == 3 and not any(o["disponivel"] for o in j["objetivos"])
    assert chamados == []


def test_hub_sem_objetivo_custo_declarado(cli, monkeypatch):
    _, h = _escopo(cli)
    cad = {None: _cadeia("PETR4", expirations=[_EXP, _EXP2]),
           _EXP2: _cadeia("PETR4", exp=_EXP2, expirations=[_EXP, _EXP2])}
    _fake(monkeypatch, cad)
    r = cli.get("/api/options/escada/PETR4", headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["estado"] == "ok" and j["providerStatus"] == "ok"
    assert [o["disponivel"] for o in j["objetivos"]] == [True, True, True]
    assert j["degraus"] == []
    assert [v["iso"] for v in j["vencimentos"]] == [_EXP, _EXP2]
    assert j["vencimentos"][0]["texto"] == f"{_EXP[8:10]}/{_EXP[5:7]}"
    assert j["comparar"]["vencimentos"] == [_EXP, _EXP2]
    assert j["comparar"]["chamadasPrevistas"] == 2 * 2 + 1
    assert j["posicao"]["qtyLivre"] == 300
    assert j["pregao"] == "2026-10-02" and j["source"] == "teste"
    assert j["precoObjeto"] == _SPOT


@pytest.mark.parametrize("obj", ["proteger", "renda", "collar"])
def test_degraus_por_objetivo(cli, monkeypatch, obj):
    _, h = _escopo(cli)
    _fake(monkeypatch)
    r = cli.get(f"/api/options/escada/PETR4?objetivo={obj}", headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["vencimento"] == _EXP
    assert 1 <= len(j["degraus"]) <= 3
    for d in j["degraus"]:
        assert d["id"]
        assert d["execucao"]["executavel"] is True
        assert d["execucao"]["idCandidato"] == d["id"]
    assert len(j["degraus"]) + len(j["degrausAusentes"]) == 3


def test_vencimento_nao_varrido_sem_estrutura(cli, monkeypatch):
    _, h = _escopo(cli)
    _fake(monkeypatch)
    r = cli.get(f"/api/options/escada/PETR4?objetivo=renda&vencimento={_EXP2}", headers=h)
    assert r.status_code == 200
    j = r.json()
    assert j["degraus"] == [] and j["motivoTexto"]


def test_vencimento_malformado_400(cli, monkeypatch):
    _, h = _escopo(cli)
    _fake(monkeypatch)
    assert cli.get("/api/options/escada/PETR4?objetivo=renda&vencimento=amanha", headers=h).status_code == 400


def test_cadeia_sem_puts_marca_proteger_indisponivel(cli, monkeypatch):
    _, h = _escopo(cli)
    _fake(monkeypatch, {None: _cadeia("PETR4", com_puts=False)})
    j = cli.get("/api/options/escada/PETR4", headers=h).json()
    disp = {o["id"]: o["disponivel"] for o in j["objetivos"]}
    assert disp["renda"] is True and disp["proteger"] is False
    assert next(o for o in j["objetivos"] if o["id"] == "proteger")["motivo"]


def test_fonte_fora_do_ar_degradado_sem_numero(cli, monkeypatch):
    _, h = _escopo(cli)
    _fake(monkeypatch, erro=True)
    r = cli.get("/api/options/escada/PETR4?objetivo=proteger", headers=h)
    assert r.status_code == 200
    j = r.json()
    assert j["estado"] == "degradado" and j["providerStatus"] == "degraded"
    assert j["degraus"] == [] and j["motivoTexto"] and j["precoObjeto"] is None


# ---- POST /leitura ----

_COLLAR = [
    {"tipo": "CALL", "lado": "venda", "strike": 32.0, "premio": 0.8, "contrato": "PETRC32"},
    {"tipo": "PUT", "lado": "compra", "strike": 27.0, "premio": 0.7, "contrato": "PETRP27"},
]


def _corpo(**kw):
    b = {"ticker": "PETR4", "objetivo": "collar", "vencimento": _EXP,
         "pernas": _COLLAR, "precoObjeto": 29.0}
    b.update(kw)
    return b


def test_leitura_celula_nao_executavel_e_sem_provedor(cli, monkeypatch):
    _, h = _escopo(cli)

    async def _proibido(*a, **k):
        raise AssertionError("rota pura chamou o provedor")

    monkeypatch.setattr(options_provider, "get_options", _proibido)
    r = cli.post("/api/options/escada/leitura", json=_corpo(vencimentosExecutaveis=[_EXP]), headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["estado"] == "ok"
    d = j["degrau"]
    assert d["execucao"]["executavel"] is False and d["execucao"]["motivo"]
    assert d["total"]["liquido"] is not None
    assert d["qtdAcoes"] == 300


def test_leitura_sem_posicao(cli, monkeypatch):
    _, h = _escopo(cli, com_posicao=False)
    j = cli.post("/api/options/escada/leitura", json=_corpo(), headers=h).json()
    assert j["estado"] == "sem_posicao" and j["degrau"] is None


def test_leitura_sem_preco_objeto_nao_inventa(cli, monkeypatch):
    _, h = _escopo(cli)
    j = cli.post("/api/options/escada/leitura", json=_corpo(precoObjeto=None), headers=h).json()
    assert j["estado"] == "ok" and j["degrau"]["execucao"]["executavel"] is False


@pytest.mark.parametrize("corpo", [
    {"objetivo": "collar", "pernas": _COLLAR},
    {"ticker": "PETR4", "objetivo": "xyz", "pernas": _COLLAR},
    {"ticker": "PETR4", "objetivo": "collar", "pernas": "x"},
    {"ticker": "PETR4", "objetivo": "collar", "pernas": []},
    {"ticker": "PETR4", "objetivo": "collar", "pernas": _COLLAR + [_COLLAR[0]]},
    {"ticker": "PETR4", "objetivo": "collar", "pernas": [{**_COLLAR[0], "tipo": "FUT"}]},
    {"ticker": "PETR4", "objetivo": "collar", "pernas": [{**_COLLAR[0], "lado": "x"}]},
    {"ticker": "PETR4", "objetivo": "collar", "pernas": [{**_COLLAR[0], "strike": "32"}]},
    {"ticker": "PETR4", "objetivo": "collar", "pernas": [{**_COLLAR[0], "premio": 0}]},
    {"ticker": "PETR4", "objetivo": "collar", "pernas": [{**_COLLAR[0], "premio": True}]},
    {"ticker": "PETR4", "objetivo": "collar", "pernas": [{**_COLLAR[0], "strike": -1}]},
    {"ticker": "PETR4", "objetivo": "collar", "pernas": _COLLAR, "vencimento": "amanha"},
])
def test_leitura_validacao_400(cli, corpo):
    _, h = _escopo(cli)
    r = cli.post("/api/options/escada/leitura", json=corpo, headers=h)
    assert r.status_code == 400, r.text


# ---- Fase 48 gap G-01/G-02 (2026-10-05) ----

def _h(dias):
    return (dt.date.today() + dt.timedelta(days=dias)).isoformat()


# NOTA 2026-10-06 (quick 261006-b1z, decisão do Alex: tirar a restrição de 15 a 60 dias): vencimentos de 4 e 11 dias
# (caso do relato) deixaram de ser "sem vencimento elegível"; o teste virou
# "objetivos disponíveis" (a causa que sobra é sem_estrutura/disponível).
def test_escada_vencimentos_curtos_sao_elegiveis(cli, monkeypatch):
    uid, h = _escopo(cli, qty=100)
    cfg = store.get(_conn, "config", user_id=uid) or {}
    cfg["permitirOpcaoADescoberto"] = True  # só para a fixture poder comprar perna avulsa
    db.kv_set(_conn, "config", cfg, user_id=uid)
    v4, v11 = _h(4), _h(11)
    # Caso ITUB4 do relato: pernas COMPRADAS (sem lastro) do mesmo underlying.
    for sym, tipo, k in (("PETRC4926", "call", 49.26), ("PETRC4976", "call", 49.76),
                         ("PETRP4651", "put", 46.51)):
        store.buy_option(_conn, {"id": sym, "underlying": "PETR4", "optionType": tipo,
                                 "strike": k, "expiration": v4}, 100, 0.5, user_id=uid)
    cad = {None: _cadeia("PETR4", exp=v4, expirations=[v4, v11]),
           v4: _cadeia("PETR4", exp=v4, expirations=[v4, v11]),
           v11: _cadeia("PETR4", exp=v11, expirations=[v4, v11])}
    _fake(monkeypatch, cad)
    r = cli.get("/api/options/escada/PETR4", headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    for o in j["objetivos"]:
        assert o.get("motivoChave") != "sem_vencimento_elegivel"
    assert any(o["disponivel"] for o in j["objetivos"]), j["objetivos"]
    assert (j.get("objetivosMotivo") or {}).get("chave") != "sem_vencimento_elegivel"
    assert j["posicao"]["qtyLivre"] == 100  # perna comprada sem lastro não trava ação


def test_escada_controle_30_dias_objetivos_disponiveis(cli, monkeypatch):
    _, h = _escopo(cli)
    _fake(monkeypatch)
    j = cli.get("/api/options/escada/PETR4", headers=h).json()
    assert [o["disponivel"] for o in j["objetivos"]] == [True, True, True]
    assert j["objetivosMotivo"] is None


def test_escada_elegivel_sem_puts_mantem_sem_estrutura(cli, monkeypatch):
    from app import skill_ref
    _, h = _escopo(cli)
    _fake(monkeypatch, {None: _cadeia("PETR4", com_puts=False)})
    j = cli.get("/api/options/escada/PETR4", headers=h).json()
    p = next(o for o in j["objetivos"] if o["id"] == "proteger")
    assert p["motivoChave"] == "sem_estrutura"
    assert p["dica"] == skill_ref.opcoes_escada_txt("operador", "sem_estrutura_dica")
    assert j["objetivosMotivo"] is None
