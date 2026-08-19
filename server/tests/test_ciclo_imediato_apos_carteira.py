"""2026-08-07 — ciclo imediato após mexer na carteira.

Origem: o Alex pediu que a avaliação dos gatilhos disparasse NA HORA quando
o usuário compra, vende ou define stop/alvo — em vez de esperar até
`intervalMin` (60min na conta que motivou a investigação toda). Mesmo motor
(agent.run_cycle_for), só o GATILHO DE QUANDO RODAR muda: além do scheduler
periódico, agora também dispara em background logo após PUT /api/position,
POST /api/buy e POST /api/sell.

`agent_mod.run_cycle_for` é substituído por um FAKE que só REGISTRA a
chamada (sem cotação real — este ambiente de teste não tem rede) — o que
importa aqui é PROVAR O GATILHO, não reexercitar o motor do ciclo (isso já
tem cobertura própria em test_fase3_operador.py).

Isolamento: banco temporário via B3_DB_PATH + reimport de app.main (mesmo
padrão de test_gate_cadastro.py) — sem isto o teste sujaria o banco real.
"""
import asyncio
import importlib
import os
import sys
import tempfile
import time

import pytest
from fastapi.testclient import TestClient

from app import pregao as pregao_mod


@pytest.fixture(autouse=True)
def _app_main_isolado():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _cliente(monkeypatch):
    d = tempfile.mkdtemp(prefix="b3_ciclo_imediato_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    monkeypatch.delenv("B3_AGENT_KILL", raising=False)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")

    chamadas = []

    async def _fake_run_cycle_for(conn, scope, quotes_getter, origem="agendado", **kw):
        chamadas.append({"scope": scope, "origem": origem})
        return {"events": [], "executed": 0}

    monkeypatch.setattr(main.agent_mod, "run_cycle_for", _fake_run_cycle_for)
    return TestClient(main.app), main, chamadas


def _espera_background(client):
    # A task roda em segundo plano no loop do TestClient — uma chamada extra
    # (barata, sem side-effect que interesse) força o loop a avançar antes
    # da asserção. time.sleep dá folga real ao scheduler do SO também.
    time.sleep(0.05)
    client.get("/api/health")


def _registrar(client, email):
    r = client.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    return r.json()["token"], r.json()["user"]["id"]


def test_putposition_logado_dispara_ciclo_imediato(monkeypatch):
    client, main, chamadas = _cliente(monkeypatch)
    token, uid = _registrar(client, "imediato1@teste.com")
    headers = {"authorization": f"Bearer {token}"}

    r = client.put("/api/position/PETR4", json={"stop": 39.5}, headers=headers)
    assert r.status_code == 200, r.text
    _espera_background(client)

    disparados = [c for c in chamadas if c["origem"] == "imediato"]
    assert len(disparados) == 1, chamadas
    assert disparados[0]["scope"] == uid


def test_putposition_anonimo_nao_dispara_ciclo_imediato(monkeypatch):
    client, main, chamadas = _cliente(monkeypatch)

    r = client.put("/api/position/PETR4", json={"stop": 39.5})
    assert r.status_code == 200, r.text
    _espera_background(client)

    assert not any(c["origem"] == "imediato" for c in chamadas), \
        "anônimo não tem Operador no servidor — não deve disparar ciclo nenhum"


def test_putposition_com_killswitch_nao_dispara(monkeypatch):
    client, main, chamadas = _cliente(monkeypatch)
    token, uid = _registrar(client, "imediato2@teste.com")
    monkeypatch.setenv("B3_AGENT_KILL", "1")

    r = client.put("/api/position/PETR4", json={"stop": 39.5}, headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    _espera_background(client)

    assert not any(c["origem"] == "imediato" for c in chamadas), \
        "kill-switch global ligado — nenhum ciclo deve rodar, nem o imediato"


def test_buy_logado_dispara_ciclo_imediato(monkeypatch):
    client, main, chamadas = _cliente(monkeypatch)
    token, uid = _registrar(client, "imediato3@teste.com")

    # Fase 2 (02-02): /api/buy passou a ramificar por pregao.in_market_hours()
    # — este teste prova o disparo do ciclo IMEDIATO, que só existe no ramo
    # "mercado aberto"; força aberto para não depender do relógio real da
    # máquina que roda a suíte.
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)

    async def _quote_fake(_t):
        return {"price": 10.0, "change": 0}
    monkeypatch.setattr(main.yahoo, "get_quote", _quote_fake)

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    _espera_background(client)

    disparados = [c for c in chamadas if c["origem"] == "imediato"]
    assert len(disparados) == 1, chamadas
    assert disparados[0]["scope"] == uid


def test_sell_logado_dispara_ciclo_imediato(monkeypatch):
    client, main, chamadas = _cliente(monkeypatch)
    token, uid = _registrar(client, "imediato4@teste.com")
    headers = {"authorization": f"Bearer {token}"}

    # Fase 2 (02-02): mesma razão do teste de compra acima — força mercado
    # aberto para exercitar o ramo IMEDIATO independente do relógio real.
    monkeypatch.setattr(pregao_mod, "in_market_hours", lambda now=None: True)

    async def _quote_fake(_t):
        return {"price": 10.0, "change": 0}
    monkeypatch.setattr(main.yahoo, "get_quote", _quote_fake)

    r = client.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=headers)
    assert r.status_code == 200, r.text
    chamadas.clear()  # a compra acima também dispara — isola a asserção na venda

    r = client.post("/api/sell", json={"t": "PETR4"}, headers=headers)
    assert r.status_code == 200, r.text
    _espera_background(client)

    disparados = [c for c in chamadas if c["origem"] == "imediato"]
    assert len(disparados) == 1, chamadas
    assert disparados[0]["scope"] == uid
