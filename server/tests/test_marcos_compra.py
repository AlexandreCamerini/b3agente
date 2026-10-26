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
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "meta": {"setup": "Rompimento de máxima"}, "protecao": "motor",
                                    "previa": {"stop": pv["stop"], "alvo": pv["alvo"]}}, headers=h)
    assert r.status_code == 200, r.text
    p = _pos(m, uid)
    assert (p["stop"], p["alvo"]) == (pv["stop"], pv["alvo"])
    assert r.json()["marcos"] == {"stop": pv["stop"], "alvo": pv["alvo"]}


def test_previa_sem_setup_usa_protecao_do_motor(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    pv = c.post("/api/marcos/PETR4", json={"compra": True, "preco": 23.51}, headers=h).json()
    previa = {"stop": pv["stop"], "alvo": pv["alvo"]} if pv["valido"] else None
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "protecao": "motor", "previa": previa}, headers=h)
    if pv["valido"]:
        assert r.status_code == 200, r.text
        p = _pos(m, uid)
        assert (p["stop"], p["alvo"]) == (pv["stop"], pv["alvo"])
    else:
        # R1: motor inválido no preço executado nunca compra calado
        assert r.status_code == 409 and r.json()["detail"]["code"] == "previa_mudou"


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


# ---- Plano 02 (R1-R7) ----

def _previa_do_motor(c, h, preco=23.51, setup=None):
    corpo = {"compra": True, "preco": preco}
    if setup:
        corpo["setup"] = setup
    return c.post("/api/marcos/PETR4", json=corpo, headers=h).json()


def test_previa_divergente_da_409_no_caminho_imediato(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    pv = _previa_do_motor(c, h, setup="Rompimento de máxima")
    assert pv["valido"] is True
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "meta": {"setup": "Rompimento de máxima"}, "protecao": "motor",
                                 "previa": {"stop": pv["stop"] - 1, "alvo": pv["alvo"]}}, headers=h)
    assert r.status_code == 409, r.text
    d = r.json()["detail"]
    assert d["code"] == "previa_mudou"
    assert d["mensagem"] == skill_ref.marcos_plano_txt(None, "compra_previa_mudou")
    assert (d["marcos"]["stop"], d["marcos"]["alvo"]) == (pv["stop"], pv["alvo"])
    assert d["marcos"]["precoRef"] == 23.51 and d["marcos"]["calculadoEm"]
    assert _pos(m, uid) is None
    # não é ordem recusada: nada no histórico
    assert store.get(m._conn, "history", user_id=uid) == []


def test_previa_divergente_da_409_no_caminho_pendente(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, aberto=False)
    pv = _previa_do_motor(c, h, setup="Rompimento de máxima")
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "meta": {"setup": "Rompimento de máxima"}, "protecao": "motor",
                                 "previa": None}, headers=h)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "previa_mudou", r.text
    assert store.get(m._conn, "history", user_id=uid) == []
    ok = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "meta": {"setup": "Rompimento de máxima"}, "protecao": "motor",
                                  "previa": {"stop": pv["stop"], "alvo": pv["alvo"]}}, headers=h)
    assert ok.status_code == 200 and ok.json()["pendente"] is True


def test_motor_invalido_no_preco_executado_da_409(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    monkeypatch.setattr(m.marcos_servico, "marcos_para_compra",
                        lambda snap, s, p: {"valido": False, "motivo": "Sem proteção válida.", "stop": None, "alvo": None})
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "protecao": "motor", "previa": None}, headers=h)
    assert r.status_code == 409, r.text
    assert r.json()["detail"]["marcos"]["valido"] is False and r.json()["detail"]["marcos"]["motivo"]
    assert _pos(m, uid) is None


def test_soma_de_lote_com_marcos_proprios_nao_da_409_nem_promete_marcos(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    assert c.put("/api/position/PETR4", json={"stop": 22.0, "alvo": 25.0}, headers=h).status_code == 200
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "protecao": "motor", "previa": None}, headers=h)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["marcos"] is None
    assert j["marcosTexto"] == skill_ref.marcos_plano_txt(None, "compra_marcos_mantidos", ticker="PETR4")
    p = _pos(m, uid)
    assert (p["stop"], p["alvo"]) == (22.0, 25.0) and p["qty"] == 200


def test_store_buy_devolve_se_aplicou_marcos(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    assert store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid) is False
    assert store.buy(m._conn, "VALE3", 100, 20.0, user_id=uid, marcos={"stop": 19.0, "alvo": 23.0}) is True


def test_recalcular_ignora_o_plano_do_card(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch)
    store.buy(m._conn, "PETR4", 100, 23.01, user_id=uid)
    rec = c.post("/api/marcos/PETR4", json={"preco": 23.51, "recalcular": True}, headers=h).json()
    assert rec["fonte"] == "recalculo"
    esperado = m.setups.marcos_da_posicao(23.51, m.marcos_servico._niveis(_snap()), avg=23.01)
    assert (rec["stop"], rec["alvo"]) == (esperado["stop"], esperado["alvo"])


def test_fallback_por_suporte_quando_plano_do_card_reprova_na_execucao(monkeypatch):
    from app import marcos_servico as ms
    snap = _snap()
    ruim = {"valido": True, "fonte": "setup", "stop": 23.50, "alvo": 23.52, "parecer": "", "motivo": None}
    monkeypatch.setattr(ms, "marcos_para_posicao", lambda s, p, avg=None, pos=None: ruim)
    r = ms.marcos_para_compra(snap, None, 23.51)
    assert r["valido"] is False  # sem suporte utilizável: desiste com motivo
    bom = {"valido": True, "stop": 22.5, "alvo": 26.5, "parecer": "", "motivo": None, "rr": 2.0}
    monkeypatch.setattr(ms.setups, "marcos_da_posicao", lambda preco, niveis, avg=None: bom)
    r = ms.marcos_para_compra(snap, None, 23.51)
    assert ms.setups.revalidar_na_execucao(22.5, 26.5, 23.51)["ok"]
    assert r["valido"] is True and r["fonte"] == "posicao"
    assert (r["stop"], r["alvo"]) == (22.5, 26.5)
    assert "não serviu" in r["parecer"]


def test_pendente_com_sem_usa_texto_de_ordem(monkeypatch):
    c, m, h, uid = _cliente(monkeypatch, aberto=False)
    r = c.post("/api/buy", json={"t": "PETR4", "qty": 100, "protecao": "sem"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["marcosTexto"] == skill_ref.marcos_plano_txt(None, "ordem_sem_marcos_autorizada", ticker="PETR4")
