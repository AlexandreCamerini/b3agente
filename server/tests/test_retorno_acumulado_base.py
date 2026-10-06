"""Quick 261006-dvf (2026-10-06): retorno acumulado com base errada (+10.193 %).

Causa: o servidor carimbava `initialBudget` (10.000) em snapshots NOVOS sobre
uma série herdada sem base (~1.000.000). Agora a base é resolvida na LEITURA
pela própria série (`store.resolver_base_serie`) e só é carimbada na escrita
quando provada (sem operação = caixa).

Paridade: o MESMO fixture é lido por web/tests/test_retorno_acumulado_base.mjs.
"""
import copy
import json
import math
import os
import sys
import tempfile
from pathlib import Path

import pytest

from app import db, store

FIXTURE = Path(__file__).parent / "fixtures" / "retorno_acumulado_casos.json"
CASOS = json.loads(FIXTURE.read_text(encoding="utf-8"))["casos"]


def _ret(base, fim):
    return None if base is None else round((fim - base) / base * 100, 2)


@pytest.mark.parametrize("caso", CASOS, ids=[c["nome"].split()[0] for c in CASOS])
def test_resolver_base_serie_bate_com_o_fixture(caso):
    entrada = copy.deepcopy(caso["snapshots"])
    r = store.resolver_base_serie(entrada)
    e = caso["esperado"]
    assert entrada == caso["snapshots"], "a leitura mutou a série recebida"
    assert r["origem"] == e["origem"]
    assert r["base"] == e["base"]
    assert r["inicio"] == e["inicio"]
    assert r["desde"] == e["desde"]
    ret = _ret(r["base"], caso["fim"])
    assert ret == e["retAcum"]


def test_caso_real_nunca_passa_de_100_pct():
    caso = CASOS[0]
    r = store.resolver_base_serie(caso["snapshots"])
    assert _ret(r["base"], caso["fim"]) < 100


# ---------------- escrita ----------------

def _fresh():
    d = tempfile.mkdtemp(prefix="b3_dvf_")
    conn = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(conn)
    return conn


def _opera(c):
    h = store.get(c, "history", user_id=None) or []
    h.append({"id": "op1", "type": "buy", "ticker": "PETR4", "qty": 1, "price": 10.0})
    db.kv_set(c, "history", h, user_id=None)


def test_sem_operacao_carimba_o_caixa_e_nao_o_patrimonio_enviado():
    c = _fresh()
    store.set_config(c, {"initialBudget": 10000})
    snaps = store.upsert_snapshot(c, {"data": "2026-08-01", "patrimonio": 999999}, user_id=None)
    assert snaps[0]["base"] == 10000


def test_com_operacao_e_serie_vazia_base_e_none():
    c = _fresh()
    store.set_config(c, {"initialBudget": 10000})
    _opera(c)
    snaps = store.upsert_snapshot(c, {"data": "2026-08-01", "patrimonio": 10000}, user_id=None)
    assert snaps[0]["base"] is None


def test_com_operacao_herda_a_base_do_registro_anterior():
    c = _fresh()
    store.set_config(c, {"initialBudget": 10000})
    store.upsert_snapshot(c, {"data": "2026-08-01", "patrimonio": 10000}, user_id=None)
    _opera(c)
    snaps = store.upsert_snapshot(c, {"data": "2026-08-02", "patrimonio": 10100}, user_id=None)
    assert [s["base"] for s in snaps] == [10000, 10000]


def test_serie_legada_sem_base_com_operacao_nunca_recebe_initial_budget():
    c = _fresh()
    store.set_config(c, {"initialBudget": 10000})
    db.kv_set(c, "equitySnapshots", [{"data": "2026-07-01", "patrimonio": 1000000, "caixa": 1, "posicoesValor": 1}], user_id=None)
    _opera(c)
    snaps = store.upsert_snapshot(c, {"data": "2026-07-02", "patrimonio": 1004000}, user_id=None)
    assert snaps[-1]["base"] is None
    assert "base" not in snaps[0] or snaps[0]["base"] is None


def test_orcamento_alterado_sem_operacao_vira_fluxo_com_base_nova():
    c = _fresh()
    store.set_config(c, {"initialBudget": 10000})
    store.upsert_snapshot(c, {"data": "2026-09-01", "patrimonio": 10000}, user_id=None)
    store.set_config(c, {"initialBudget": 50000})
    snaps = store.upsert_snapshot(c, {"data": "2026-09-02", "patrimonio": 50000}, user_id=None)
    assert [s["base"] for s in snaps] == [10000, 50000]
    r = store.resolver_base_serie(snaps)
    assert r["origem"] == "carimbada" and r["base"] == 50000 and r["inicio"] == 1


def test_sem_operacao_considera_opcoes_e_pendentes():
    c = _fresh()
    assert store._sem_operacao(c, None) is True
    db.kv_set(c, "pendingOrders", [{"id": "p1"}], user_id=None)
    assert store._sem_operacao(c, None) is False
