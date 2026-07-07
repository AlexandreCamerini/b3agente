"""FASE 2 — isolamento multiusuário, semeadura de first-login e exclusão de conta.

Prova: (1) dados isolados por user_id; (2) o escopo legado/global (sem user_id)
permanece intacto — garantindo que web sem login e as suítes antigas não mudam;
(3) seed_user_from adota o dado local numa conta vazia (decisão B); (4)
delete_user_data apaga só o escopo do usuário.

Roda standalone (`python -m tests.test_multiuser`) e via pytest.
"""
import os
import tempfile

from app import db, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_mu_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)            # escopo legado/global
    return conn, path


def test_escopos_de_usuario_sao_isolados():
    conn, _ = _fresh_db()
    ua, ub = "user_aaa", "user_bbb"
    store.ensure_defaults(conn, user_id=ua)
    store.ensure_defaults(conn, user_id=ub)

    store.set_config(conn, {"userName": "Alice", "initialBudget": 25000}, user_id=ua)
    store.set_config(conn, {"userName": "Bruno", "initialBudget": 7000}, user_id=ub)
    store.buy(conn, "PETR4", 200, 40.0, user_id=ua)

    pa = store.public_state(conn, user_id=ua)
    pb = store.public_state(conn, user_id=ub)
    assert pa["config"]["userName"] == "Alice"
    assert pb["config"]["userName"] == "Bruno"
    # ambos começam com as posições-demo (PETR4 300); a COMPRA de A (200) só
    # afeta A — prova de isolamento sem depender de escopo vazio.
    qa = next(p["qty"] for p in pa["positions"] if p["t"] == "PETR4")
    qb = next(p["qty"] for p in pb["positions"] if p["t"] == "PETR4")
    assert qa == 500          # 300 demo + 200 comprados
    assert qb == 300          # B intacto
    assert pa["config"]["initialBudget"] == 25000.0
    assert pb["config"]["initialBudget"] == 7000.0
    conn.close()


def test_escopo_legado_intacto_com_usuarios():
    conn, _ = _fresh_db()
    # mexe no global (sem user_id) e num usuário; um não contamina o outro
    store.set_config(conn, {"userName": "Anon"})
    store.set_config(conn, {"userName": "Logada"}, user_id="user_x")
    assert store.get(conn, "config")["userName"] == "Anon"          # global
    assert store.get(conn, "config", user_id="user_x")["userName"] == "Logada"
    # chave BYOK isolada por escopo
    store.set_config(conn, {"keySource": "manual", "apiKey": "GLOBALKEY"})
    store.set_config(conn, {"keySource": "manual", "apiKey": "USERKEY"}, user_id="user_x")
    assert store.get(conn, "config")["apiKey"] == "GLOBALKEY"
    assert store.get(conn, "config", user_id="user_x")["apiKey"] == "USERKEY"
    # public_state nunca reexpoe a chave, em nenhum escopo
    assert "apiKey" not in store.public_state(conn)["config"]
    assert "apiKey" not in store.public_state(conn, user_id="user_x")["config"]
    assert store.public_state(conn, user_id="user_x")["config"]["keyStored"] is True
    conn.close()


def test_persiste_por_usuario_apos_reinicio():
    conn, path = _fresh_db()
    store.set_config(conn, {"userName": "Persistente", "apiKey": "K", "keySource": "manual"}, user_id="u1")
    store.buy(conn, "VALE3", 100, 60.0, user_id="u1")
    conn.close()
    conn2 = db.connect(path)               # "redeploy" / reinício
    cfg = store.get(conn2, "config", user_id="u1")
    assert cfg["userName"] == "Persistente"
    assert cfg["apiKey"] == "K"            # chave do usuário sobrevive
    assert any(p["t"] == "VALE3" for p in store.get(conn2, "positions", user_id="u1"))
    conn2.close()


def test_seed_first_login_adota_local_e_nao_reescreve():
    conn, _ = _fresh_db()
    # monta a semente a partir do escopo global (como o web faria no 1º login)
    store.set_config(conn, {"userName": "DoLocal", "apiKey": "LOCALKEY", "keySource": "manual", "initialBudget": 12345})
    store.set_watchlist(conn, ["PETR4", "VALE3"])
    seed = store.export_sections(conn)     # cru, com apiKey
    assert seed["config"]["apiKey"] == "LOCALKEY"

    # 1) conta vazia adota a semente
    seeded = store.seed_user_from(conn, "novo", seed)
    assert seeded is True
    cfg = store.get(conn, "config", user_id="novo")
    assert cfg["userName"] == "DoLocal"
    assert cfg["apiKey"] == "LOCALKEY"     # BYOK preservado na semeadura
    assert set(store.get(conn, "watchlist", user_id="novo")) == {"PETR4", "VALE3"}

    # 2) segundo login NÃO re-semeia (escopo já tem config)
    store.set_config(conn, {"userName": "JaEditado"}, user_id="novo")
    seeded2 = store.seed_user_from(conn, "novo", seed)
    assert seeded2 is False
    assert store.get(conn, "config", user_id="novo")["userName"] == "JaEditado"
    conn.close()


def test_exclusao_de_conta_apaga_so_o_usuario():
    import app.auth as auth
    conn, _ = _fresh_db()
    vai = auth.register_email(conn, "vai@x.com", "senha-forte-123")
    fica = auth.register_email(conn, "fica@x.com", "senha-forte-456")
    store.ensure_defaults(conn, user_id=vai["id"])
    store.ensure_defaults(conn, user_id=fica["id"])
    store.set_config(conn, {"userName": "Vai"}, user_id=vai["id"])
    store.set_config(conn, {"userName": "Fica"}, user_id=fica["id"])
    store.set_config(conn, {"userName": "Global"})
    tok = auth.create_session(conn, vai["id"])

    n = store.delete_user_data(conn, vai["id"])
    assert n > 0
    # escopo do "vai": volta ao default (config some -> get devolve o default)
    assert store.get(conn, "config", user_id=vai["id"])["userName"] == ""
    # linha em users e sessão removidas (cascade)
    assert db.get_user_by_id(conn, vai["id"]) is None
    assert auth.resolve_session(conn, tok) is None
    # "fica" e global permanecem
    assert store.get(conn, "config", user_id=fica["id"])["userName"] == "Fica"
    assert db.get_user_by_id(conn, fica["id"]) is not None
    assert store.get(conn, "config")["userName"] == "Global"
    conn.close()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES MULTIUSUARIO PASSARAM")
