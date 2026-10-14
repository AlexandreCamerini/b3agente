"""Convivencia fechamento x app no mesmo dia (D4, quick 261013-u7w, 2026-10-13).

Casos C1-C7 vem de fixtures/snapshot_convivencia_casos.json, lida tambem por
web/tests/test_snapshot_convivencia.mjs (espelho do deviceStore)."""
import json
import os
import tempfile

import pytest

from app import db, store

_FIX = os.path.join(os.path.dirname(__file__), "fixtures", "snapshot_convivencia_casos.json")
with open(_FIX, encoding="utf-8") as _f:
    _CASOS = json.load(_f)["casos"]


def _conn():
    return db.connect(os.path.join(tempfile.mkdtemp(), "b3.db"))


@pytest.mark.parametrize("caso", _CASOS, ids=[c["nome"][:2] for c in _CASOS])
def test_convivencia_fixture(caso):
    c = _conn()
    if caso["inicial"]:
        db.kv_set(c, "equitySnapshots", caso["inicial"], user_id="u1")
    for p in caso["passos"]:
        store.upsert_snapshot(c, {"data": p["data"], "patrimonio": p["patrimonio"]}, user_id="u1", origem=p["origem"])
    final = db.kv_get(c, "equitySnapshots", [], user_id="u1")
    assert [(s["data"], s["patrimonio"], s["origem"]) for s in final] == \
        [(f["data"], f["patrimonio"], f["origem"]) for f in caso["final"]]


def test_registro_ganha_origem_fonte_hora():
    c = _conn()
    out = store.upsert_snapshot(c, {"data": "2026-10-13", "patrimonio": 10, "origem": "fechamento", "fonte": "x", "hora": "99:99"},
                                user_id="u1", origem="fechamento", fonte="brapi", hora="17:06")
    assert out[0]["origem"] == "fechamento" and out[0]["fonte"] == "brapi" and out[0]["hora"] == "17:06"
    # o corpo do cliente nunca define origem/fonte/hora
    out = store.upsert_snapshot(c, {"data": "2026-10-14", "patrimonio": 10, "origem": "fechamento", "fonte": "x", "hora": "99:99"},
                                user_id="u1")
    assert out[-1]["origem"] == "app" and out[-1]["fonte"] is None
    assert len(out[-1]["hora"]) == 5 and out[-1]["hora"][2] == ":" and out[-1]["hora"] != "99:99"


def test_origem_desconhecida_vira_app():
    c = _conn()
    out = store.upsert_snapshot(c, {"data": "2026-10-13", "patrimonio": 10}, user_id="u1", origem="qualquer")
    assert out[0]["origem"] == "app"


def test_app_ignorado_devolve_lista_atual_sem_gravar():
    c = _conn()
    store.upsert_snapshot(c, {"data": "2026-10-13", "patrimonio": 200}, user_id="u1", origem="fechamento", hora="17:06")
    antes = db.kv_get(c, "equitySnapshots", [], user_id="u1")
    out = store.upsert_snapshot(c, {"data": "2026-10-13", "patrimonio": 1}, user_id="u1")
    assert out == antes and db.kv_get(c, "equitySnapshots", [], user_id="u1") == antes
