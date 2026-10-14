"""Paridade servidor x front do patrimonio da conta (quick 261013-u7w, 2026-10-13).

`store.patrimonio_conta` e espelho de `portfolioMetrics` (web/src/finance.js);
os numeros vem de fixtures/patrimonio_conta_paridade.json, lida tambem por
web/tests/test_patrimonio_conta_paridade.mjs."""
import copy
import json
import os
import tempfile

import pytest

from app import db, store

_FIX = os.path.join(os.path.dirname(__file__), "fixtures", "patrimonio_conta_paridade.json")
with open(_FIX, encoding="utf-8") as _f:
    _CASOS = json.load(_f)["casos"]


@pytest.mark.parametrize("caso", _CASOS, ids=[c["nome"][:1] for c in _CASOS])
def test_patrimonio_conta_bate_com_a_fixture(caso):
    r = store.patrimonio_conta(caso["positions"], caso["quotes"], caso["cash"], caso["reservado"],
                               caso["optionPositions"], caso["optionQuotes"])
    esp = caso["esperado"]
    assert round(r["patr"], 2) == esp["patr"]
    assert round(r["posVal"], 2) == esp["posVal"]
    assert round(r["opcoesVal"], 2) == esp["opcoesVal"]
    assert r["semCotacao"] == esp["semCotacao"]
    assert set(r) == {"patr", "posVal", "cash", "reservado", "opcoesVal", "opcoesSemMarcacao", "semCotacao"}


def test_entradas_nao_sao_mutadas():
    caso = copy.deepcopy(_CASOS[1])
    antes = copy.deepcopy(caso)
    store.patrimonio_conta(caso["positions"], caso["quotes"], caso["cash"], caso["reservado"],
                           caso["optionPositions"], caso["optionQuotes"])
    assert caso == antes


def test_semcotacao_sem_duplicar_e_entradas_malformadas():
    r = store.patrimonio_conta(
        [{"t": "PETR4", "qty": 1, "avg": 10}, {"t": "PETR4", "qty": 2, "avg": 10}, "lixo", None],
        None, None, None, None, None)
    assert r["semCotacao"] == ["PETR4"]
    assert r["cash"] == 0 and r["reservado"] == 0
    assert round(r["patr"], 2) == 30


def test_scopes_com_carteira_ignora_legado_e_une_cash_e_positions():
    c = db.connect(os.path.join(tempfile.mkdtemp(), "b3.db"))
    db.kv_set(c, "cash", 10, user_id="u2")
    db.kv_set(c, "positions", [], user_id="u1")
    db.kv_set(c, "cash", 5, user_id="u1")
    db.kv_set(c, "cash", 99, user_id=None)       # balde anonimo legado
    db.kv_set(c, "positions", [], user_id=None)
    assert store.scopes_com_carteira(c) == ["u1", "u2"]
