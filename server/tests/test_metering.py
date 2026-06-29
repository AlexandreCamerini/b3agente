"""FASE 3 (item 2) — metering da IA gerenciada: cota diária, reset por dia e
rate limit por usuário, isolados por escopo. Stdlib; roda standalone e via pytest.
"""
import os
import tempfile

from app import db, metering


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_meter_")
    return db.connect(os.path.join(d, "b3_agente.db"))


def test_cota_diaria_consome_e_bloqueia():
    conn = _fresh_db()
    uid = "u1"
    for _ in range(3):
        ok, reason = metering.check(conn, uid, quota=3, rate_per_min=100)
        assert ok, reason
        metering.consume(conn, uid)
    # 4ª: cota estourada
    ok, reason = metering.check(conn, uid, quota=3, rate_per_min=100)
    assert ok is False
    assert "limite diário" in reason
    snap = metering.snapshot(conn, uid, 3)
    assert snap["used"] == 3 and snap["remaining"] == 0
    conn.close()


def test_cota_isolada_por_usuario():
    conn = _fresh_db()
    metering.check(conn, "a", quota=2, rate_per_min=100); metering.consume(conn, "a")
    metering.check(conn, "a", quota=2, rate_per_min=100); metering.consume(conn, "a")
    # A estourou; B intacto
    assert metering.check(conn, "a", quota=2, rate_per_min=100)[0] is False
    assert metering.check(conn, "b", quota=2, rate_per_min=100)[0] is True
    assert metering.snapshot(conn, "b", 2)["used"] == 0
    conn.close()


def test_reset_diario():
    conn = _fresh_db()
    uid = "u2"
    # simula uso de ONTEM gravado direto no kv
    db.kv_set(conn, "aiUsage", {"day": "2000-01-01", "count": 99, "rl": []}, user_id=uid)
    # _load deve resetar porque o dia mudou
    ok, _ = metering.check(conn, uid, quota=5, rate_per_min=100)
    assert ok is True
    assert metering.snapshot(conn, uid, 5)["used"] == 0
    conn.close()


def test_rate_limit_por_minuto():
    conn = _fresh_db()
    uid = "u3"
    t0 = 1_000_000.0
    # 3 permitidas na janela; a 4ª no mesmo segundo bloqueia
    for i in range(3):
        ok, _ = metering.check(conn, uid, quota=None, rate_per_min=3, _now=t0 + i * 0.1)
        assert ok is True
    ok, reason = metering.check(conn, uid, quota=None, rate_per_min=3, _now=t0 + 0.4)
    assert ok is False and "Muitas análises" in reason
    # 61s depois a janela deslizou => liberado de novo
    ok, _ = metering.check(conn, uid, quota=None, rate_per_min=3, _now=t0 + 61)
    assert ok is True
    conn.close()


def test_quota_none_ilimitada():
    conn = _fresh_db()
    uid = "u4"
    for _ in range(50):
        ok, _ = metering.check(conn, uid, quota=None, rate_per_min=1000)
        assert ok is True
        metering.consume(conn, uid)
    assert metering.snapshot(conn, uid, None)["remaining"] is None
    conn.close()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE METERING PASSARAM")
