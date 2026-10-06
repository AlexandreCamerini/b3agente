"""Guardiao quick 261006-bwv (2026-10-06): a perna de opcao comprada SEM lastro
(`store.buy_option`, "perna avulsa") entra no patrimonio. Caso real: PUT
VALEV731W2, 100 x R$ 0,92 debitou R$ 92 do caixa e sumiu do patrimonio.

Paridade com o front: a MESMA fixture JSON e lida por
web/tests/test_patrimonio_opcao_avulsa.mjs (finance.portfolioMetrics).
"""
import json
import math
import os
import sys
from pathlib import Path

import pytest

from app import db, store

sys.path.insert(0, os.path.dirname(__file__))
from test_ordens_pendentes_rotas import _client, _registrar, _app_main_isolado  # noqa: E402,F401

FIXTURE = Path(__file__).parent / "fixtures" / "patrimonio_opcoes_paridade.json"
CASOS = json.loads(FIXTURE.read_text(encoding="utf-8"))["casos"]


def test_fixture_tem_os_sete_casos_e_o_caso_real():
    assert len(CASOS) == 7
    assert "VALEV731W2" in FIXTURE.read_text(encoding="utf-8")


@pytest.mark.parametrize("caso", CASOS, ids=[c["nome"][:1] for c in CASOS])
def test_valor_opcoes_bate_com_a_fixture(caso):
    r = store.valor_opcoes(caso["optionPositions"], caso["optionQuotes"])
    e = caso["esperado"]
    assert math.isclose(r["valor"], e["opcoesVal"], abs_tol=1e-9)
    assert math.isclose(r["pnl"], e["opcoesPnL"], abs_tol=1e-9)
    assert r["sem_marcacao"] == e["semMarcacao"]
    assert math.isclose(caso["cash"] + caso["reservado"] + r["valor"], e["patr"], abs_tol=1e-9)


def test_valor_opcoes_defensivo():
    assert store.valor_opcoes([], None) == {"valor": 0.0, "pnl": 0.0, "sem_marcacao": 0}
    assert store.valor_opcoes(None, None)["valor"] == 0
    r = store.valor_opcoes([None, "x", {"id": "Z", "qty": "abc", "avg": None}], None)
    assert r["valor"] == 0


def _seed_opcao_avulsa(main, scope, cash_esperado_apos):
    cfg = store.get(main._conn, "config", user_id=scope) or {}
    cfg["permitirOpcaoADescoberto"] = True
    db.kv_set(main._conn, "config", cfg, user_id=scope)


def test_compra_valev731w2_caixa_cai_92_e_patrimonio_do_pet_nao_muda(monkeypatch):
    client, main = _client(monkeypatch)
    token, uid = _registrar(client, "bwv-avulsa@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _seed_opcao_avulsa(main, uid, None)
    cash_antes = client.get("/api/state", headers=headers).json()["cash"]
    antes = client.get("/api/pet/resumo", params={"tela": "evolucao"}, headers=headers).json()

    store.buy_option(main._conn, {"id": "VALEV731W2", "underlying": "VALE3", "optionType": "put",
                                  "strike": 70.0, "expiration": "2026-10-17"},
                     100, 0.92, user_id=uid)

    cash_depois = client.get("/api/state", headers=headers).json()["cash"]
    assert cash_antes - cash_depois == pytest.approx(92.00, abs=1e-6)
    depois = client.get("/api/pet/resumo", params={"tela": "evolucao"}, headers=headers).json()
    assert depois["patrimonio"] == pytest.approx(antes["patrimonio"], abs=1e-6)
    assert any("prêmio de abertura" in linha for linha in depois["fala"])
    # sem perna, a fala nao ganha a ressalva
    assert not any("prêmio de abertura" in linha for linha in antes["fala"])


def test_perna_lastreada_muda_o_patrimonio_do_pet_exatamente_por_valor_opcoes(monkeypatch):
    client, main = _client(monkeypatch)
    token, uid = _registrar(client, "bwv-lastro@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    antes = client.get("/api/pet/resumo", params={"tela": "evolucao"}, headers=headers).json()
    opts = [{"id": "PETR4C100", "side": "vendida", "qty": 100, "avg": 2.0, "lastro": {"t": "PETR4", "qty": 100}},
            {"id": "PETR4M100", "side": "comprada", "qty": 100, "avg": 1.0, "lastro": {"t": "PETR4", "qty": 100}}]
    db.kv_set(main._conn, "optionPositions", opts, user_id=uid)
    depois = client.get("/api/pet/resumo", params={"tela": "evolucao"}, headers=headers).json()
    esperado = store.valor_opcoes(opts, None)["valor"]  # -200 + 100
    assert esperado == pytest.approx(-100.0)
    assert depois["patrimonio"] - antes["patrimonio"] == pytest.approx(esperado, abs=1e-6)


def test_historico_equity_snapshots_intacto(monkeypatch):
    client, main = _client(monkeypatch)
    token, uid = _registrar(client, "bwv-hist@boris.dev")
    headers = {"authorization": f"Bearer {token}"}
    _seed_opcao_avulsa(main, uid, None)
    snaps = [{"data": "2026-10-01", "patrimonio": 10000.0}, {"data": "2026-10-02", "patrimonio": 10050.5}]
    db.kv_set(main._conn, "equitySnapshots", snaps, user_id=uid)
    antes = json.dumps(store.get(main._conn, "equitySnapshots", user_id=uid), sort_keys=True)
    store.buy_option(main._conn, {"id": "VALEV731W2", "underlying": "VALE3", "optionType": "put"},
                     100, 0.92, user_id=uid)
    r = client.get("/api/pet/resumo", params={"tela": "evolucao"}, headers=headers)
    assert r.status_code == 200
    depois = json.dumps(store.get(main._conn, "equitySnapshots", user_id=uid), sort_keys=True)
    assert antes == depois
