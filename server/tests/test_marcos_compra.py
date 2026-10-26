"""Quick 261026-epr: marcos da COMPRA — fonte única (prévia == gravação),
autorização explícita `protecao: "sem"`, compatibilidade sem `protecao` e
`recalcular` que ignora o gravado. Sem rede (stubs de snapshot/cotação)."""
from app import skill_ref, store
from tests.test_marcos_rotas import _cliente, _pos, _snap  # noqa: F401  (fixture autouse incluída abaixo)
from tests.test_marcos_rotas import _app_main_isolado  # noqa: F401


def test_previa_e_compra_gravam_os_mesmos_marcos(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    pv = c.post("/api/marcos/PETR4", json={"compra": True, "setup": "Rompimento de máxima", "preco": 23.51}, headers=h).json()
    assert pv["valido"] is True, pv
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "meta": {"setup": "Rompimento de máxima"}, "protecao": "motor"}, headers=h)
    assert r.status_code == 200, r.text
    p = _pos(m, uid)
    assert (p["stop"], p["alvo"]) == (pv["stop"], pv["alvo"])
    assert r.json()["marcos"] == {"stop": pv["stop"], "alvo": pv["alvo"]}


def test_previa_sem_setup_usa_protecao_do_motor(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    pv = c.post("/api/marcos/PETR4", json={"compra": True, "preco": 23.51}, headers=h).json()
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "protecao": "motor"}, headers=h)
    assert r.status_code == 200, r.text
    p = _pos(m, uid)
    if pv["valido"]:
        assert (p["stop"], p["alvo"]) == (pv["stop"], pv["alvo"])
    else:
        assert p.get("stop") is None and r.json()["marcos"] is None and r.json()["marcosMotivo"]


def test_protecao_sem_executa_sem_marcos_mesmo_com_setup_valido(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "meta": {"setup": "Rompimento de máxima"}, "protecao": "sem"}, headers=h)
    assert r.status_code == 200, r.text
    p = _pos(m, uid)
    assert p.get("stop") is None and p.get("alvo") is None
    j = r.json()
    assert j["marcos"] is None
    assert j["marcosTexto"] == skill_ref.marcos_plano_txt(None, "compra_sem_marcos_autorizada", ticker="PETR4")


def test_protecao_sem_vale_para_ordem_pendente(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, aberto=False)
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "meta": {"setup": "Rompimento de máxima"}, "protecao": "sem"}, headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["pendente"] is True and j["marcos"] is None
    assert "sem stop e alvo" in j["marcosTexto"]


def test_sem_protecao_no_corpo_mantem_comportamento_antigo(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    # sem setup e sem protecao: nada calculado (antigo)
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["marcos"] is None and r.json()["marcosTexto"] is None
    # com setup: caminho de setup antigo continua gravando
    c2, m2, h2, uid2 = _cliente(monkeypatch)
    r2 = c2.post("/api/buy", json={"t": "PETR4", "qty": 100, "meta": {"setup": "Rompimento de máxima"}}, headers=h2)
    assert r2.status_code == 200, r2.text
    assert r2.json()["marcos"] is not None


def test_recalcular_ignora_o_gravado(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    assert c.put("/api/position/PETR4", json={"stop": 22.0, "alvo": 25.0}, headers=h).status_code == 200
    padrao = c.post("/api/marcos/PETR4", json={"preco": 23.51}, headers=h).json()
    assert padrao["fonte"] == "posicao_gravada" and padrao["stop"] == 22.0
    rec = c.post("/api/marcos/PETR4", json={"preco": 23.51, "recalcular": True}, headers=h).json()
    assert rec["fonte"] != "posicao_gravada"
