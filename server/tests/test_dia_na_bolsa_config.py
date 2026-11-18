"""Fase 51-06 — config.diasDecisao: uniao, regex, teto, migracao; streak intocado."""
import os
import tempfile

from app import db, store


def _conn():
    d = tempfile.mkdtemp()
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    return c


def _dias(c):
    return store.get(c, "config", user_id="u1")["diasDecisao"]


def test_uniao_ordenada_entre_patches():
    c = _conn()
    store.set_config(c, {"diasDecisao": ["2026-11-17"]}, user_id="u1")
    store.set_config(c, {"diasDecisao": ["2026-11-18"]}, user_id="u1")
    assert _dias(c) == ["2026-11-17", "2026-11-18"]


def test_invalidos_descartados_e_sem_duplicata():
    c = _conn()
    store.set_config(c, {"diasDecisao": ["2026-11-17", "2026-11-17", "17/11/2026", 5, None, "2026-11-1x"]}, user_id="u1")
    assert _dias(c) == ["2026-11-17"]


def test_teto_60_mantem_as_mais_recentes():
    c = _conn()
    datas = [f"2026-{m:02d}-{d:02d}" for m in range(1, 5) for d in range(1, 29)]  # 112
    store.set_config(c, {"diasDecisao": datas}, user_id="u1")
    got = _dias(c)
    assert len(got) == 60
    assert got == sorted(datas)[-60:]


def test_config_antiga_sem_a_chave_migra_para_lista_vazia():
    c = _conn()
    cfg = db.kv_get(c, "config", None, user_id="u1")
    cfg.pop("diasDecisao", None)
    db.kv_set(c, "config", cfg, user_id="u1")
    store.ensure_defaults(c, user_id="u1")
    assert _dias(c) == []


def test_streak_legado_nao_muda():
    c = _conn()
    store.set_config(c, {"streak": {"days": 7, "last": "2026-11-10"}}, user_id="u1")
    store.set_config(c, {"diasDecisao": ["2026-11-18"]}, user_id="u1")
    assert store.get(c, "config", user_id="u1")["streak"] == {"days": 7, "last": "2026-11-10"}
