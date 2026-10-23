"""Fase 50 (50-04): rotas de marcos — PUT /api/position validado (D-11) com
gestaoAuto (D-14), POST /api/marcos/{t} gratuito e POST /api/buy com marcos do
MOTOR calculados no servidor (D-03/D-09). Inclui a regressão do iPhone
(PM 23,01 / cotação 23,51 / stop 23,36 / alvo 21,58)."""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import setups, store

NIVEIS = {"atr": 0.5, "suportes": [22.0], "resistencias": [26.0]}
SETUP = {"nome": "Rompimento de máxima", "lado": "alta", "gatilho": 24.0, "invalidacao": 23.0, "aposentado": False}


def _snap(close=23.51, setups_=None):
    return {"snapshotId": "abc12345", "asOf": "2026-10-21", "generatedAt": "2026-10-21T20:00:00Z",
            "close": close, "setups": {"setups": [SETUP] if setups_ is None else setups_, "niveis": NIVEIS}}


@pytest.fixture(autouse=True)
def _app_main_isolado():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _cliente(monkeypatch, quote=23.51, snap="default", aberto=True):
    d = tempfile.mkdtemp(prefix="b3_marcos_rotas_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    sys.modules.pop("app.main", None)
    m = importlib.import_module("app.main")
    monkeypatch.setattr(m, "_disparar_ciclo_imediato", lambda scope: None)

    async def _q(t):
        if quote is None:
            raise RuntimeError("sem cotação")
        return {"price": quote}
    monkeypatch.setattr(m.candle_provider, "get_quote", _q)

    async def _s(t):
        return _snap() if snap == "default" else snap
    monkeypatch.setattr(m.marcos_servico, "snapshot_canonico", _s)
    from app import pregao
    monkeypatch.setattr(pregao, "in_market_hours", lambda now=None: aberto)
    r = TestClient(m.app).post("/api/auth/register", json={"email": "m@teste.com", "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    h = {"authorization": "Bearer " + r.json()["token"]}
    return TestClient(m.app), m, h, r.json()["user"]["id"]


def _pos(m, uid, t="PETR4"):
    return next((p for p in store.get(m._conn, "positions", user_id=uid) if p["t"] == t), None)


def test_put_recusa_geometria_do_iphone_com_400(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    antes = store.get(m._conn, "positions", user_id=uid)
    r = c.put("/api/position/PETR4", json={"stop": 23.36, "alvo": 21.58}, headers=h)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Stop (R$ 23,36) precisa ficar abaixo do alvo (R$ 21,58)."
    assert store.get(m._conn, "positions", user_id=uid) == antes


def test_put_valido_200_e_grava(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    r = c.put("/api/position/PETR4", json={"stop": 22.0, "alvo": 25.0}, headers=h)
    assert r.status_code == 200, r.text
    p = _pos(m, uid)
    assert p["stop"] == 22.0 and p["alvo"] == 25.0


def test_put_gestao_auto_sem_preco(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=None, snap=None)
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    r = c.put("/api/position/PETR4", json={"gestaoAuto": False}, headers=h)
    assert r.status_code == 200, r.text
    assert _pos(m, uid)["gestaoAuto"] is False


def test_put_sem_cotacao_valida_contra_close_do_snapshot(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=None, snap=_snap(close=23.51))
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    r = c.put("/api/position/PETR4", json={"stop": 23.8}, headers=h)  # stop acima de 23,51
    assert r.status_code == 400, r.text
    # Nota review WR-06 (2026-10-22): fechamento do snapshot NÃO é "cotação atual" —
    # a mensagem diz que é o último fechamento e de quando.
    assert "cotação atual" not in r.json()["detail"]
    assert "último fechamento (em 21/10/2026, R$ 23,51)" in r.json()["detail"]
    assert _pos(m, uid)["stop"] is None


def test_put_sem_cotacao_e_sem_snapshot_recusa_sem_gravar(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=None, snap=None)
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    r = c.put("/api/position/PETR4", json={"stop": 22.0}, headers=h)
    assert r.status_code == 400
    assert r.json()["detail"] == setups.MOTIVO_SEM_PRECO_VALIDAR
    assert _pos(m, uid)["stop"] is None


def test_put_limpar_marcos_nao_precisa_de_preco(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=None, snap=None)
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    r = c.put("/api/position/PETR4", json={"stop": None, "alvo": None}, headers=h)
    assert r.status_code == 200, r.text


def test_marcos_por_setup(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    r = c.post("/api/marcos/PETR4", json={"setup": SETUP["nome"], "preco": 24.0})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["valido"] is True and j["t"] == "PETR4" and j["fonte"] == "setup"
    assert j["stop"] == 22.95 and j["alvo"] == 26.0
    assert j["snapshotId"] == "abc12345"


def test_marcos_setup_inativo(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    j = c.post("/api/marcos/PETR4", json={"setup": "Inexistente", "preco": 24.0}).json()
    assert j["valido"] is False and "não está ativo" in j["motivo"] and j["stop"] is None


def test_marcos_posicao_sem_setup(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    j = c.post("/api/marcos/PETR4", json={"preco": 22.8}).json()
    assert j["fonte"] == "posicao" and j["valido"] is True


def test_marcos_sem_snapshot_502(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, snap=None)
    r = c.post("/api/marcos/PETR4", json={})
    assert r.status_code == 502
    assert "Sem dados técnicos" in r.json()["detail"]


def test_marcos_ticker_invalido_400(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    assert c.post("/api/marcos/AB", json={}).status_code == 400


# ------------------------------ /api/buy ---------------------------------
def _buy(c, h, meta, qty=100):
    return c.post("/api/buy", json={"t": "PETR4", "qty": qty, "meta": meta}, headers=h)


def test_buy_com_setup_nasce_com_marcos_do_servidor_ignorando_meta_forjado(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=24.0)
    meta = {"setup": SETUP["nome"], "lado": "alta", "gatilho": 30.0, "invalidacao": 1.0, "stop": 1.0, "alvo": 999.0}
    r = _buy(c, h, meta)
    assert r.status_code == 200, r.text
    p = _pos(m, uid)
    assert p["stop"] == 22.95 and p["alvo"] == 26.0
    assert r.json()["marcos"] == {"stop": 22.95, "alvo": 26.0}
    assert r.json()["marcosMotivo"] is None


def test_buy_rr_baixo_executa_sem_marcos(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=24.45)
    r = _buy(c, h, {"setup": SETUP["nome"], "lado": "alta"})
    assert r.status_code == 200, r.text
    p = _pos(m, uid)
    assert p is not None and p.get("stop") is None and p.get("alvo") is None
    assert r.json()["marcos"] is None and r.json()["marcosMotivo"]


def test_buy_perseguicao_executa_sem_marcos(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=24.6)
    r = _buy(c, h, {"setup": SETUP["nome"], "lado": "alta"})
    assert r.status_code == 200, r.text
    assert _pos(m, uid).get("stop") is None
    assert "não persiga" in r.json()["marcosMotivo"]


def test_buy_sem_setup_nao_muda(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=24.0)
    r = _buy(c, h, None)
    assert r.status_code == 200, r.text
    assert _pos(m, uid).get("stop") is None
    assert r.json()["marcos"] is None and r.json()["marcosMotivo"] is None


def test_buy_sem_snapshot_executa_sem_marcos(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=24.0, snap=None)
    r = _buy(c, h, {"setup": SETUP["nome"], "lado": "alta"})
    assert r.status_code == 200, r.text
    assert r.json()["marcosMotivo"] == "Sem dados técnicos para calcular os marcos agora."


def test_buy_mercado_fechado_ordem_pendente_leva_marcos(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=24.0, aberto=False)
    r = _buy(c, h, {"setup": SETUP["nome"], "lado": "alta", "gatilho": 99.0})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["pendente"] is True
    assert j["order"]["marcos"]["stop"] == 22.95 and j["order"]["marcos"]["alvo"] == 26.0
    assert j["order"]["marcos"]["gatilho"] == 24.0  # do snapshot, não do meta


def test_wr01_rota_marcos_usa_o_pm_da_posicao_do_servidor(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    store.buy(m._conn, "PETR4", 100, 25.0, user_id=uid)
    # o avg do corpo é ignorado: vale o da posição no servidor
    j = c.post("/api/marcos/PETR4", json={"preco": 22.8, "avg": 1.0}, headers=h).json()
    assert j["valido"] is True and j["alvo"] > 25.0
    assert setups.validar_marcos(j["stop"], j["alvo"], preco=22.8, avg=25.0) is None


def test_wr05_put_ticker_sem_posicao_nao_busca_cotacao(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    chamadas = []

    async def _q(t):
        chamadas.append(t)
        return {"price": 10.0}
    monkeypatch.setattr(m.candle_provider, "get_quote", _q)
    r = c.put("/api/position/XXXX3", json={"stop": 9.0}, headers=h)
    assert r.status_code == 404 and "posição" in r.json()["detail"]
    assert c.put("/api/position/AB", json={"stop": 9.0}, headers=h).status_code == 400
    assert chamadas == []


def test_wr06_editar_so_o_alvo_nao_recusa_por_stop_antigo_vs_preco(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, quote=23.51)
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    r = c.put("/api/position/PETR4", json={"stop": 22.0, "alvo": 25.0}, headers=h)
    assert r.status_code == 200
    # cotação cai abaixo do stop gravado: editar só o alvo continua possível
    async def _q(t):
        return {"price": 21.0}
    monkeypatch.setattr(m.candle_provider, "get_quote", _q)
    r = c.put("/api/position/PETR4", json={"alvo": 26.0}, headers=h)
    assert r.status_code == 200, r.text
    assert _pos(m, uid)["alvo"] == 26.0
    # estrutura segue valendo: alvo abaixo do stop gravado é recusado
    r = c.put("/api/position/PETR4", json={"alvo": 21.5}, headers=h)
    assert r.status_code == 400 and "abaixo do alvo" in r.json()["detail"]


def test_in03_put_stop_nao_numerico_400_ptbr(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    r = c.put("/api/position/PETR4", json={"stop": "abc"}, headers=h)
    assert r.status_code == 400 and r.json()["detail"] == "Stop e alvo precisam ser valores positivos."


def test_put_opcao_stop_nao_numerico_ou_bool_400_ptbr(monkeypatch):
    from app import db
    c, m, h, uid = _cliente(monkeypatch)
    db.kv_set(m._conn, "optionPositions", [{"id": "PETRA100", "qty": 100, "avg": 1.0, "stop": 0.5, "alvo": 2.0}], user_id=uid)
    for ruim in ("abc", True):
        r = c.put("/api/options/position/PETRA100", json={"stop": ruim}, headers=h)
        assert r.status_code == 400 and r.json()["detail"] == "Stop e alvo precisam ser valores positivos.", r.text
    op = store.get(m._conn, "optionPositions", user_id=uid)[0]
    assert (op["stop"], op["alvo"]) == (0.5, 2.0)  # kv inalterado
    r = c.put("/api/options/position/PETRA100", json={"stop": "0,7".replace(",", "."), "alvo": ""}, headers=h)
    assert r.status_code == 200, r.text
    op = store.get(m._conn, "optionPositions", user_id=uid)[0]
    assert (op["stop"], op["alvo"]) == (0.7, None)
