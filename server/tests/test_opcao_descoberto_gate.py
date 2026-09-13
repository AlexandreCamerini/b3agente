"""Guardião do gate de opção A DESCOBERTO (Fase 29, Plano 01).

O que este arquivo protege:
  • SC-1 — conta nova e conta legada sem a chave nascem/ficam DESLIGADAS;
    nenhuma migração silenciosa para ligado (fail-closed por ausência).
  • SC-2 — `store.buy_option` recusa abrir posição a seco com o flag
    desligado (rejeição registrada, caixa/posições intocados), e
    `POST /api/options/buy` traduz essa recusa em 400 com a mensagem do
    motor — nunca 500, nunca 200.
  • SC-4 — `store.sell_option`/`close_option_vencida` NUNCA são barrados
    pelo flag, mesmo numa posição aberta enquanto ele estava ligado e depois
    desligado. Provado por comportamento E por source assertion (o corpo de
    `sell_option` não pode mencionar o campo do flag).

Padrão da casa: `_fresh_db()` com SQLite temp por teste para os testes de
MOTOR (sem conftest, `test_lastro_trava.py`); `_client_isolado`/`_registrar`/
`_chain_opcao` para os testes de ROTA (`test_fase5_rejeicao_rotas.py`) —
helpers copiados aqui porque a casa não compartilha conftest entre arquivos.
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import db, store


TERMO = {"aceitoEm": "2026-09-13T00:00:00Z", "versao": "1.0"}


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_test_opcao_descoberto_gate_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    return conn, path


def _contract(id_="PETRH340", underlying="PETR4", strike=34.0, expiration="2099-01-01"):
    return {"id": id_, "underlying": underlying, "optionType": "call", "strike": strike,
            "expiration": expiration}


def _liberar(conn, user_id=None):
    store.set_config(conn, {"descobertoTermo": dict(TERMO), "permitirOpcaoADescoberto": True}, user_id=user_id)


# ===========================================================================
# Helpers de ROTA — copiados de test_fase5_rejeicao_rotas.py (sem conftest)
# ===========================================================================

_EXP_OPCAO = "2026-10-30"


def _client_isolado(monkeypatch):
    d = tempfile.mkdtemp(prefix="b3_opcao_descoberto_gate_rota_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    sys.modules.pop("app.main", None)
    m = importlib.import_module("app.main")
    return TestClient(m.app), m


def _registrar(client, email):
    r = client.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    return r.json()["token"], r.json()["user"]["id"]


def _chain_opcao(symbol="PETRK30", price=1.5):
    """Cadeia sintética ADR-004, UM contrato negociável (volume/openInterest
    acima do gate de liquidez, para não bater nele)."""
    return {"providerStatus": "ok", "underlyingPrice": 30.0, "expiration": _EXP_OPCAO,
            "expirations": [_EXP_OPCAO], "puts": [],
            "calls": [{"contractSymbol": symbol, "optionType": "call", "strike": 30.0,
                        "lastPrice": price, "bid": price, "ask": price, "volume": 5000,
                        "openInterest": 3000, "impliedVolatility": 0.3,
                        "expiration": _EXP_OPCAO}]}


@pytest.fixture(autouse=True)
def _isola_app_main():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


# ===========================================================================
# Grupo A — default e fail-closed (SC-1)
# ===========================================================================

def test_conta_nova_nasce_com_flag_desligado():
    conn, _ = _fresh_db()
    cfg = store.get(conn, "config")
    assert cfg["permitirOpcaoADescoberto"] is False
    assert cfg["descobertoTermo"] is None


def test_config_sem_a_chave_e_tratado_como_desligado():
    conn, _ = _fresh_db()
    cfg = dict(store.get(conn, "config"))
    cfg.pop("permitirOpcaoADescoberto", None)
    cfg.pop("descobertoTermo", None)
    db.kv_set(conn, "config", cfg)  # simula config legado, sem backfill
    with pytest.raises(ValueError):
        store.buy_option(conn, _contract(), 100, 1.0)


def test_ligar_sem_termo_nao_liga():
    conn, _ = _fresh_db()
    store.set_config(conn, {"permitirOpcaoADescoberto": True})
    assert store.get(conn, "config")["permitirOpcaoADescoberto"] is False


def test_termo_no_mesmo_patch_liga():
    conn, _ = _fresh_db()
    store.set_config(conn, {"descobertoTermo": dict(TERMO), "permitirOpcaoADescoberto": True})
    assert store.get(conn, "config")["permitirOpcaoADescoberto"] is True


def test_desligar_e_livre_e_preserva_o_termo():
    conn, _ = _fresh_db()
    _liberar(conn)
    store.set_config(conn, {"permitirOpcaoADescoberto": False})
    cfg = store.get(conn, "config")
    assert cfg["permitirOpcaoADescoberto"] is False
    assert isinstance(cfg["descobertoTermo"], dict)


# ===========================================================================
# Grupo B — o gate na compra (SC-2)
# ===========================================================================

def test_buy_option_com_flag_desligado_levanta_e_nao_move_nada():
    conn, _ = _fresh_db()
    cash_antes = store.get(conn, "cash")

    with pytest.raises(ValueError) as exc:
        store.buy_option(conn, _contract(), 100, 1.0)

    assert str(exc.value) == store.MOTIVO_DESCOBERTO_DESLIGADO
    assert store.get(conn, "optionPositions") == []
    assert store.get(conn, "cash") == cash_antes
    h = store.get(conn, "history")[0]
    assert h["status"] == "rejeitada" and h["type"] == "COMPRA"
    assert h["motivo"] == store.MOTIVO_DESCOBERTO_DESLIGADO


def test_buy_option_com_flag_ligado_executa_como_antes():
    conn, _ = _fresh_db()
    _liberar(conn)
    cash_antes = store.get(conn, "cash")

    store.buy_option(conn, _contract(), 100, 1.25, user_id=None)

    opts = store.get(conn, "optionPositions")
    assert len(opts) == 1 and opts[0]["avg"] == 1.25 and opts[0]["qty"] == 100
    assert store.get(conn, "cash") == round(cash_antes - 125.0, 2)
    h = store.get(conn, "history")[0]
    assert "status" not in h  # execução não é rejeição


# ===========================================================================
# Grupo C — fechar NUNCA é barrado (SC-4, o ponto mais importante)
# ===========================================================================

def test_sell_option_com_flag_desligado_executa():
    conn, _ = _fresh_db()
    _liberar(conn)
    store.buy_option(conn, _contract(), 100, 1.0)
    store.set_config(conn, {"permitirOpcaoADescoberto": False})

    pnl = store.sell_option(conn, "PETRH340", 2.5)

    assert isinstance(pnl, (int, float))
    assert store.get(conn, "optionPositions") == []
    assert store.get(conn, "cash") == round(10_000.0 - 100.0 + 250.0, 2)


def test_sell_option_parcial_com_flag_desligado_executa():
    conn, _ = _fresh_db()
    _liberar(conn)
    store.buy_option(conn, _contract(), 200, 1.0)
    store.set_config(conn, {"permitirOpcaoADescoberto": False})

    pnl = store.sell_option(conn, "PETRH340", 2.5, qty=100)

    assert isinstance(pnl, (int, float))
    restante = store.get(conn, "optionPositions")
    assert len(restante) == 1 and restante[0]["qty"] == 100 and restante[0]["avg"] == 1.0


def test_close_option_vencida_com_flag_desligado_executa():
    conn, _ = _fresh_db()
    _liberar(conn)
    store.buy_option(conn, _contract(expiration="2020-01-01"), 100, 1.0)
    store.set_config(conn, {"permitirOpcaoADescoberto": False})

    pnl = store.close_option_vencida(conn, "PETRH340", 0.0)

    assert pnl == -100.0
    assert store.get(conn, "optionPositions") == []


def test_corpo_de_sell_option_nao_menciona_o_flag():
    src = open(os.path.join(os.path.dirname(__file__), "..", "app", "store.py"), encoding="utf-8").read()
    i = src.index("def sell_option")
    j = src.index("def close_option_vencida")
    corpo = src[i:j]
    assert "permitirOpcaoADescoberto" not in corpo


# ===========================================================================
# Grupo D — a rota não é atalho (SC-2, superfície HTTP)
# ===========================================================================

def test_rota_options_buy_flag_desligado_400_com_a_mensagem_do_motor(monkeypatch):
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "descoberto-gate-buy@boris.dev")
    headers = {"authorization": f"Bearer {token}"}

    async def _chain_ok(*a, **k):
        return _chain_opcao()
    monkeypatch.setattr(m.options_provider, "get_options", _chain_ok)

    r = client.post("/api/options/buy",
                    json={"underlying": "PETR4", "contractSymbol": "PETRK30", "qty": 100},
                    headers=headers)
    assert r.status_code == 400, r.text
    assert r.status_code != 500, "exceção crua nunca chega ao cliente"
    assert r.json()["detail"] == m.store.MOTIVO_DESCOBERTO_DESLIGADO

    estado = client.get("/api/state", headers=headers).json()
    assert estado["optionPositions"] == []
    assert estado["cash"] == 10000.0


def test_rota_options_sell_nunca_e_400_por_causa_do_flag(monkeypatch):
    client, m = _client_isolado(monkeypatch)
    token, _uid = _registrar(client, "descoberto-gate-sell@boris.dev")
    headers = {"authorization": f"Bearer {token}"}

    async def _chain_ok(*a, **k):
        return _chain_opcao()
    monkeypatch.setattr(m.options_provider, "get_options", _chain_ok)

    r = client.put("/api/config",
                    json={"descobertoTermo": dict(TERMO), "permitirOpcaoADescoberto": True},
                    headers=headers)
    assert r.status_code == 200, r.text

    r = client.post("/api/options/buy",
                    json={"underlying": "PETR4", "contractSymbol": "PETRK30", "qty": 100},
                    headers=headers)
    assert r.status_code == 200, r.text

    r = client.put("/api/config", json={"permitirOpcaoADescoberto": False}, headers=headers)
    assert r.status_code == 200, r.text

    r = client.post("/api/options/sell", json={"contractSymbol": "PETRK30"}, headers=headers)
    assert r.status_code == 200, r.text
