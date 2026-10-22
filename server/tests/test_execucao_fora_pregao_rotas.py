"""quick 261013-vai — rotas fora do pregão (Tarefa 2).

PUT /api/position grava e não executa; run-now e /api/cycle respondem
"mercado fechado"; as 6 rotas de EXECUÇÃO de opções recusam com 409 sem
consultar o provedor; rotas de leitura e o registro de stop/alvo de opção
seguem livres. Relógio sempre injetado (`.relogio_pregao`).
"""
import asyncio
import importlib
import os
import pathlib
import re
import sys
import tempfile
import time
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import pregao, skill_ref, store
from .relogio_pregao import abrir_pregao, fechar_pregao, fixar_instante

TERMO = {"aceitoEm": "2026-09-13T00:00:00Z", "versao": "1.0"}
OPERADOR = {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"}, "appMode": "operador"}
_EXP = "2026-10-30"
SAB = datetime(2026, 10, 17, 14, 0, tzinfo=pregao.BRT)


@pytest.fixture(autouse=True)
def _app_main_isolado(monkeypatch):
    monkeypatch.delenv("B3_AFTER_MARKET", raising=False)
    monkeypatch.delenv("B3_DEV_MERCADO_ABERTO", raising=False)
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _cliente(monkeypatch):
    d = tempfile.mkdtemp(prefix="b3_exec_fora_pregao_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    sys.modules.pop("app.main", None)
    m = importlib.import_module("app.main")
    return TestClient(m.app), m


def _registrar(client, email, operador=True, m=None):
    r = client.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    uid = r.json()["user"]["id"]
    if operador:
        store.set_config(m._conn, OPERADOR, user_id=uid)
    return {"authorization": "Bearer " + r.json()["token"]}, uid


def _chain(symbol="PETRK30", price=1.5):
    return {"providerStatus": "ok", "underlyingPrice": 30.0, "expiration": _EXP, "expirations": [_EXP],
            "puts": [], "calls": [{"contractSymbol": symbol, "optionType": "call", "strike": 30.0,
                                    "lastPrice": price, "bid": price, "ask": price, "volume": 5000,
                                    "openInterest": 3000, "impliedVolatility": 0.3, "expiration": _EXP}]}


def _sem_provedor(monkeypatch, m):
    chamadas = []

    async def _boom(*a, **k):
        chamadas.append(a)
        raise AssertionError("o provedor de opções não pode ser consultado fora do pregão")
    monkeypatch.setattr(m.options_provider, "get_options", _boom)
    return chamadas


def _opcao_legado(uid, m, id_="PETRK30", underlying="PETR4"):
    from app import db
    db.kv_set(m._conn, "optionPositions", [{
        "id": id_, "underlying": underlying, "optionType": "call", "strike": 30.0,
        "expiration": _EXP, "qty": 100, "avg": 1.0, "stop": None, "alvo": None}], user_id=uid)


def _espera(client):
    time.sleep(0.05)
    client.get("/api/health")


# --------------------------------------------------------------------------
def test_r1_put_position_fechado_grava_e_ciclo_nao_executa(monkeypatch):
    fixar_instante(monkeypatch, SAB)
    client, m = _cliente(monkeypatch)
    h, uid = _registrar(client, "r1@fora-pregao.dev", m=m)
    store.buy(m._conn, "PETR4", 100, 40.0, user_id=uid)
    disparos = []
    monkeypatch.setattr(m, "_disparar_ciclo_imediato", lambda scope: disparos.append(scope))
    # Fase 50 / D-12: a invariante vale para parecer; geometria é validada
    # contra preço (D-11) — cotação coerente (40,00 > stop 38) fixada.
    async def _q(t):
        return {"price": 40.0}
    monkeypatch.setattr(m.candle_provider, "get_quote", _q)
    r = client.put("/api/position/PETR4", json={"stop": 38.0}, headers=h)
    assert r.status_code == 200, r.text
    assert disparos == [uid]  # continua disparando; o portão é do motor
    pos = next(p for p in store.get(m._conn, "positions", user_id=uid) if p["t"] == "PETR4")
    assert pos["stop"] == 38.0

    async def quotes(ts):
        return {t: {"price": 37.5} for t in ts}
    res = asyncio.run(m.agent_mod.run_cycle_for(m._conn, uid, quotes, origem="imediato"))
    assert res["mercadoFechado"] is True and res["executed"] == 0
    assert [p["t"] for p in store.get(m._conn, "positions", user_id=uid)] == ["PETR4"]
    from app import db
    assert any("Mercado fechado" in e["text"] for e in db.kv_get(m._conn, "agentLog", [], user_id=uid))


def test_r2_run_now_fechado_nao_cria_task(monkeypatch):
    fixar_instante(monkeypatch, SAB)
    client, m = _cliente(monkeypatch)
    h, uid = _registrar(client, "r2@fora-pregao.dev", m=m)
    chamadas = []

    async def fake(*a, **k):
        chamadas.append(1)
        return {"events": [], "executed": 0}
    monkeypatch.setattr(m.agent_mod, "run_cycle_for", fake)
    r = client.post("/api/agent/run-now", headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["iniciado"] is False and j["mercadoFechado"] is True
    assert j["mensagem"] == skill_ref.execucao_fora_pregao_txt("operador", "ciclo_fechado", abertura="10:00")
    _espera(client)
    assert chamadas == []
    from app import db
    log = db.kv_get(m._conn, "agentLog", [], user_id=uid)
    assert any(e["text"] == j["mensagem"] and e["kind"] == "info" for e in log)


def test_r2_run_now_aberto_segue_igual_e_kill_switch_409(monkeypatch):
    abrir_pregao(monkeypatch)
    client, m = _cliente(monkeypatch)
    h, uid = _registrar(client, "r2b@fora-pregao.dev", m=m)
    chamadas = []

    async def fake(*a, **k):
        chamadas.append(1)
        return {"events": [], "executed": 0}
    monkeypatch.setattr(m.agent_mod, "run_cycle_for", fake)
    r = client.post("/api/agent/run-now", headers=h)
    assert r.status_code == 200 and r.json()["iniciado"] is True
    _espera(client)
    assert chamadas == [1]
    fechar_pregao(monkeypatch)
    monkeypatch.setattr(m.agent_mod, "kill_switch_on", lambda: True)
    assert client.post("/api/agent/run-now", headers=h).status_code == 409  # prioridade inalterada


def test_r3_api_cycle_fechado(monkeypatch):
    fixar_instante(monkeypatch, SAB)
    client, m = _cliente(monkeypatch)
    h, uid = _registrar(client, "r3@fora-pregao.dev", m=m)
    store.buy(m._conn, "PETR4", 100, 40.0, user_id=uid)
    store.set_position(m._conn, "PETR4", stop=38.0, alvo=None, has_stop=True, has_alvo=False, user_id=uid)

    async def quotes(ts):
        return {t: {"price": 37.5} for t in ts}
    monkeypatch.setattr(m.candle_provider, "get_quotes_exclusive", quotes)
    r = client.post("/api/cycle", headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["mercadoFechado"] is True
    assert j["mensagem"] == skill_ref.execucao_fora_pregao_txt("operador", "ciclo_fechado", abertura="10:00")
    assert j["quotes"]["PETR4"]["price"] == 37.5
    assert [p["t"] for p in j["positions"]] == ["PETR4"]


ROTAS_EXEC = [
    ("buy", "/api/options/buy", {"underlying": "PETR4", "contractSymbol": "PETRK30", "qty": 100}),
    ("sell", "/api/options/sell", {"contractSymbol": "PETRK30"}),
    ("curadoria-collar", "/api/options/curadoria/abrir-collar",
     {"underlying": "PETR4", "idCandidato": "x", "contratos": 1,
      "pernasContratos": [{"contractSymbol": "A", "lado": "venda"}, {"contractSymbol": "B", "lado": "compra"}]}),
    ("lastreada-abrir", "/api/options/lastreada/abrir",
     {"underlying": "PETR4", "contractSymbol": "PETRK30", "contratos": 1}),
    ("lastreada-collar", "/api/options/lastreada/abrir-collar",
     {"underlying": "PETR4", "contratos": 1,
      "pernasContratos": [{"contractSymbol": "A", "lado": "venda"}, {"contractSymbol": "B", "lado": "compra"}]}),
    ("lastreada-fechar", "/api/options/lastreada/fechar", {"contractSymbol": "PETRK30"}),
]


@pytest.mark.parametrize("nome,url,body", ROTAS_EXEC, ids=[r[0] for r in ROTAS_EXEC])
def test_r4_rotas_de_execucao_de_opcoes_recusam_409(monkeypatch, nome, url, body):
    fixar_instante(monkeypatch, SAB)
    client, m = _cliente(monkeypatch)
    h, uid = _registrar(client, f"r4-{nome}@fora-pregao.dev", m=m)
    _opcao_legado(uid, m)
    chamadas = _sem_provedor(monkeypatch, m)
    r = client.post(url, json=body, headers=h)
    assert r.status_code == 409, r.text
    d = r.json()["detail"]
    assert d["code"] == "mercado_fechado"
    assert "10:00" in d["message"] and d["action"]
    assert d["message"] == skill_ref.execucao_fora_pregao_txt("operador", "opcao_bloqueada", abertura="10:00")
    assert chamadas == []
    from app import db
    rej = [x for x in (db.kv_get(m._conn, "history", [], user_id=uid) or []) if x.get("status") == "rejeitada"]
    if nome in ("buy", "sell"):
        assert len(rej) == 1 and rej[0]["type"] == ("COMPRA" if nome == "buy" else "VENDA")
        assert rej[0]["motivo"] == d["message"][:200]
    else:
        assert rej == []  # estrutura multi-perna/proposta: só 409, sem linha no history


@pytest.mark.parametrize("url,body", [
    ("/api/options/lastreada/abrir", {"underlying": "PETR4", "contractSymbol": "PETRK30", "contratos": 1}),
    ("/api/options/lastreada/fechar", {"contractSymbol": "PETRK30"}),
])
def test_r5_modo_estudo_continua_403_antes_do_409(monkeypatch, url, body):
    fixar_instante(monkeypatch, SAB)
    client, m = _cliente(monkeypatch)
    h, uid = _registrar(client, "r5-" + url.rsplit("/", 1)[1] + "@fora-pregao.dev", operador=False, m=m)
    _sem_provedor(monkeypatch, m)
    assert client.post(url, json=body, headers=h).status_code == 403


def test_r6_registrar_stop_alvo_de_opcao_sempre_permitido(monkeypatch):
    fixar_instante(monkeypatch, SAB)
    client, m = _cliente(monkeypatch)
    h, uid = _registrar(client, "r6@fora-pregao.dev", m=m)
    _opcao_legado(uid, m)
    r = client.put("/api/options/position/PETRK30", json={"stop": 0.5, "alvo": 3.0}, headers=h)
    assert r.status_code == 200, r.text
    op = store.get(m._conn, "optionPositions", user_id=uid)[0]
    assert op["stop"] == 0.5 and op["alvo"] == 3.0


def test_r7_guardiao_estrutural_do_helper_nas_rotas():
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    blocos = re.split(r"\n(?=@app\.)", src)
    com_helper = []
    for b in blocos:
        deco = b.split("\n", 1)[0]
        corpo = re.sub(r'"""[\s\S]*?"""', '""', b)  # docstring não conta como chamada
        if re.search(r"(?<!def )_recusar_execucao_fora_do_pregao\(", corpo) and b.startswith("@app."):
            com_helper.append(deco)
            # antes de qualquer consulta ao provedor / re-derivação
            pos = re.search(r"(?<!def )_recusar_execucao_fora_do_pregao\(", corpo).start()
            for marca in ("options_provider.get_options", "_curadoria_scan_posicao(", "opcoes_lastreadas.propor("):
                if marca in corpo:
                    assert pos < corpo.index(marca), f"{deco}: o 409 precisa vir antes de {marca}"
    esperados = {'@app.post("/api/options/buy")', '@app.post("/api/options/sell")',
                 '@app.post("/api/options/curadoria/abrir-collar")',
                 '@app.post("/api/options/lastreada/abrir")',
                 '@app.post("/api/options/lastreada/abrir-collar")',
                 '@app.post("/api/options/lastreada/fechar")'}
    assert set(com_helper) == esperados and len(com_helper) == 6
    assert src.count("def _recusar_execucao_fora_do_pregao(") == 1


def test_r8_pregao_aberto_buy_segue_200(monkeypatch):
    abrir_pregao(monkeypatch)
    client, m = _cliente(monkeypatch)
    h, uid = _registrar(client, "r8@fora-pregao.dev", m=m)

    async def _ok(*a, **k):
        return _chain()
    monkeypatch.setattr(m.options_provider, "get_options", _ok)
    r = client.put("/api/config", json={"descobertoTermo": dict(TERMO), "permitirOpcaoADescoberto": True}, headers=h)
    assert r.status_code == 200, r.text
    r = client.post("/api/options/buy",
                    json={"underlying": "PETR4", "contractSymbol": "PETRK30", "qty": 100}, headers=h)
    assert r.status_code == 200, r.text
