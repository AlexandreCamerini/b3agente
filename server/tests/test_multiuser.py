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
    # 09/08/2026: a carteira passou a começar ZERADA (as posições-demo não
    # tinham sido pagas e inflavam o retorno acumulado — ver defaults.py). O
    # isolamento é o mesmo, provado agora pela compra: só A fica com a posição.
    qa = next(p["qty"] for p in pa["positions"] if p["t"] == "PETR4")
    assert qa == 200                                    # só o que A comprou
    assert pb["positions"] == []                        # B intacto
    # e o caixa de cada um reflete o PRÓPRIO orçamento menos a própria operação
    # (escolher o orçamento com a carteira vazia passou a atualizar o caixa)
    assert pa["cash"] == round(25000.0 - 200 * 40.0, 2)   # 25.000 − 8.000
    assert pb["cash"] == 7000.0                            # Bruno não operou
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


# ---------------------------------------------------------------------------
# Reporte do Alex (09/08/2026): "quando entro com um usuário novo o sistema
# não entra zerado". Causa: no web a conta nova era semeada com uma CÓPIA do
# escopo anônimo/global — um balde único do servidor. Fazia sentido quando
# existia "usar sem conta"; sem ele, só herda sobra (inclusive de terceiros).
# ---------------------------------------------------------------------------

def test_conta_nova_no_web_comeca_limpa_e_nao_herda_o_escopo_anonimo():
    from fastapi.testclient import TestClient
    from app import main

    # sujeira no escopo anônimo, como um servidor em uso teria
    store.buy(main._conn, "PETR4", 300, 36.8, user_id=None)
    store.set_config(main._conn, {"userName": "Anônimo Anterior"}, user_id=None)

    email = "novo_%d@teste.local" % abs(hash(str(main)) % 10**6)
    with TestClient(main.app) as c:
        r = c.post("/api/auth/register", json={"email": email, "password": "senha12345"})
        assert r.status_code == 200, r.text
        st = r.json()["state"]
    assert st["positions"] == [], "conta nova herdou posição do escopo anônimo"
    assert st["history"] == [], "conta nova herdou histórico de outra pessoa"
    assert st["config"]["userName"] != "Anônimo Anterior", "conta nova herdou identidade alheia"
    assert st["cash"] == st["config"]["initialBudget"]


def test_escolher_o_orcamento_atualiza_o_disponivel():
    """"O valor de orçamento disponível continua com problemas de atualização."

    `set_config` gravava `initialBudget` e não tocava no caixa: a pessoa
    escolhia R$ 50.000 no onboarding e seguia com R$ 10.000 para operar.
    """
    conn, _ = _fresh_db()
    store.set_config(conn, {"initialBudget": 50000}, user_id="u1")
    assert store.get(conn, "cash", user_id="u1") == 50000.0


def test_orcamento_nao_reescreve_o_caixa_com_a_simulacao_em_andamento():
    """Com posição aberta o caixa é RESULTADO das operações — sobrescrevê-lo
    inventaria dinheiro no meio do jogo."""
    conn, _ = _fresh_db()
    store.set_config(conn, {"initialBudget": 10000}, user_id="u2")
    store.buy(conn, "PETR4", 100, 40.0, user_id="u2")
    caixa_apos_compra = store.get(conn, "cash", user_id="u2")
    store.set_config(conn, {"initialBudget": 90000}, user_id="u2")
    assert store.get(conn, "cash", user_id="u2") == caixa_apos_compra
