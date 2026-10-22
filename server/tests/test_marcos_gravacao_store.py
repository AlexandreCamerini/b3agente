"""Fase 50 (50-03): gravação de marcos no store — set_position validado
(D-11), buy com marcos do motor (D-08/D-09) e regra de lote somado."""
import os
import tempfile

import pytest

from app import db, store


def _fresh():
    conn = db.connect(os.path.join(tempfile.mkdtemp(prefix="b3_marcos_"), "t.db"))
    store.ensure_defaults(conn)
    return conn


def _pos(conn, t="PETR4"):
    return next(p for p in store.get(conn, "positions") if p["t"] == t)


def test_set_position_recusa_geometria_impossivel_caso_real():
    conn = _fresh()
    store.buy(conn, "PETR4", 100, 23.01)
    antes = store.get(conn, "positions")
    with pytest.raises(ValueError, match=r"Stop \(R\$ 23,36\) precisa ficar abaixo do alvo \(R\$ 21,58\)\."):
        store.set_position(conn, "PETR4", stop=23.36, alvo=21.58, has_stop=True, has_alvo=True, preco_ref=23.51)
    assert store.get(conn, "positions") == antes


def test_set_position_so_stop_e_limpar():
    conn = _fresh()
    store.buy(conn, "PETR4", 100, 23.01)
    store.set_position(conn, "PETR4", stop=22.0, has_stop=True, preco_ref=23.51)
    assert _pos(conn)["stop"] == 22.0
    store.set_position(conn, "PETR4", stop=None, alvo=None, has_stop=True, has_alvo=True)
    p = _pos(conn)
    assert p["stop"] is None and p["alvo"] is None


def test_set_position_alvo_abaixo_do_pm_sem_preco_ref():
    conn = _fresh()
    store.buy(conn, "PETR4", 100, 23.01)
    with pytest.raises(ValueError, match="preço médio"):
        store.set_position(conn, "PETR4", alvo=22.5, has_alvo=True)


def test_set_position_gestao_auto():
    conn = _fresh()
    store.buy(conn, "PETR4", 100, 23.01)
    store.set_position(conn, "PETR4", gestao_auto=False)
    p = _pos(conn)
    assert p["gestaoAuto"] is False and p["stop"] is None and p["alvo"] is None


def test_buy_nova_com_marcos():
    conn = _fresh()
    store.buy(conn, "PETR4", 100, 20.0, marcos={"stop": 19.5, "alvo": 23.5})
    p = _pos(conn)
    assert (p["stop"], p["alvo"], p["stopInicial"]) == (19.5, 23.5, 19.5)
    assert p["gestaoAuto"] is True and p["marcosOrigem"] == "motor"


def test_buy_sem_marcos_contrato_atual():
    conn = _fresh()
    store.buy(conn, "PETR4", 100, 20.0)
    p = _pos(conn)
    assert p["stop"] is None and p["alvo"] is None
    assert "gestaoAuto" not in p and "stopInicial" not in p


def test_lote_somado_preserva_marcos_validos_do_usuario():
    conn = _fresh()
    store.buy(conn, "PETR4", 100, 20.0)
    store.set_position(conn, "PETR4", stop=19.0, alvo=25.0, has_stop=True, has_alvo=True)
    store.buy(conn, "PETR4", 100, 21.0, marcos={"stop": 18.0, "alvo": 30.0})
    p = _pos(conn)
    assert (p["stop"], p["alvo"]) == (19.0, 25.0)
    assert p["qty"] == 200


def test_lote_somado_sem_marcos_aplica_os_do_motor():
    conn = _fresh()
    store.buy(conn, "PETR4", 100, 20.0)
    store.buy(conn, "PETR4", 100, 21.0, marcos={"stop": 19.0, "alvo": 26.0})
    p = _pos(conn)
    assert (p["stop"], p["alvo"], p["stopInicial"]) == (19.0, 26.0, 19.0)
    assert p["gestaoAuto"] is True


def test_buy_marcos_invalidos_nao_debita_caixa():
    conn = _fresh()
    cash = store.get(conn, "cash")
    with pytest.raises(ValueError):
        store.buy(conn, "PETR4", 100, 20.0, marcos={"stop": 19.0, "alvo": 19.5})
    assert store.get(conn, "cash") == cash
    assert store.get(conn, "positions") == []


def test_normalizacao_de_qty_manual_preservada():
    conn = _fresh()
    store.buy(conn, "PETR4", 200, 10.0)
    store.buy(conn, "VALE3", 150, 10.0)
    assert _pos(conn, "PETR4")["qty"] == 200
    assert _pos(conn, "VALE3")["qty"] == 200
