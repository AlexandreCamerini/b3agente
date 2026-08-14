"""ADR-012 (Fase 3) — eficiência das operações automáticas: campo `origem`
em store.buy/sell/buy_option/sell_option/close_option_vencida, agregação
cross-usuário (automacao.py) e a rota GET /api/analytics/automacao. Mesmo
padrão dos demais arquivos desta série (módulo + TestClient).
"""
import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import analysis_outcomes as ao
from app import analytics, automacao, db, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_automacao_")
    return db.connect(os.path.join(d, "b3_agente.db"))


def _analytics_conn():
    d = tempfile.mkdtemp(prefix="b3_automacao_analytics_")
    return analytics.connect(os.path.join(d, "analytics.db"))


@pytest.fixture(autouse=True)
def _reset_last_cache_refresh():
    automacao.LAST_CACHE_REFRESH.update(date=None, erro=None)
    yield


# ------------------------------ origem (store.py) ---------------------------

def test_buy_grava_origem_manual_por_default():
    conn = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0, user_id="u1")
    h = store.get(conn, "history", user_id="u1")
    assert h[0]["origem"] == "manual"
    conn.close()


def test_buy_grava_origem_automatico_quando_explicito():
    conn = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0, user_id="u1", origem="automatico")
    h = store.get(conn, "history", user_id="u1")
    assert h[0]["origem"] == "automatico"
    conn.close()


def test_sell_grava_origem():
    conn = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0, user_id="u1")
    store.sell(conn, "PETR4", 40.0, user_id="u1", origem="automatico")
    h = store.get(conn, "history", user_id="u1")
    venda = next(e for e in h if e["type"] == "VENDA")
    assert venda["origem"] == "automatico"
    conn.close()


def test_buy_option_e_sell_option_gravam_origem():
    conn = _fresh_db()
    contract = {"id": "PETR4C40", "underlying": "PETR4", "optionType": "CALL", "strike": 40.0, "expiration": "2027-01-15"}
    store.buy_option(conn, contract, 100, 1.5, user_id="u1", origem="automatico")
    store.sell_option(conn, "PETR4C40", 2.0, user_id="u1", motivo="alvo", origem="automatico")
    h = store.get(conn, "history", user_id="u1")
    assert h[0]["origem"] == "automatico" and h[0]["motivo"] == "alvo"  # venda (insert 0) primeiro
    assert h[1]["origem"] == "automatico"  # compra
    conn.close()


def test_close_option_vencida_grava_origem_sistema_nao_automatico():
    conn = _fresh_db()
    contract = {"id": "PETR4C40", "underlying": "PETR4", "optionType": "CALL", "strike": 40.0, "expiration": "2027-01-15"}
    store.buy_option(conn, contract, 100, 1.5, user_id="u1")
    store.close_option_vencida(conn, "PETR4C40", 0.0, user_id="u1")
    h = store.get(conn, "history", user_id="u1")
    venda = next(e for e in h if e["type"] == "VENDA")
    assert venda["origem"] == "sistema"
    assert venda["motivo"] == "vencimento"
    conn.close()


def test_historico_sem_a_chave_origem_nao_e_reescrito():
    conn = _fresh_db()
    h = store.get(conn, "history", user_id="u1")
    h.append({"date": "2026-01-01", "type": "COMPRA", "t": "OLD4", "qty": 100, "price": 10.0, "pnl": None})
    store.put(conn, "history", h, user_id="u1")
    reloaded = store.get(conn, "history", user_id="u1")
    assert "origem" not in reloaded[0]  # entrada antiga não ganha a chave retroativamente
    conn.close()


# --------------------------- scopes_com_history ------------------------------

def test_scopes_com_history_varre_todos_os_escopos():
    conn = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0, user_id="u1")
    store.buy(conn, "VALE3", 100, 60.0, user_id="u2")
    scopes = store.scopes_com_history(conn)
    assert set(scopes) == {"u1", "u2"}
    conn.close()


# ------------------------------ resumo_por_origem -----------------------------

def test_resumo_por_origem_agrega_cross_usuario():
    conn = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0, user_id="u1", origem="manual")
    store.sell(conn, "PETR4", 40.0, user_id="u1", origem="manual")
    store.buy(conn, "VALE3", 100, 60.0, user_id="u2", origem="automatico")
    store.sell(conn, "VALE3", 58.0, user_id="u2", origem="automatico")
    r = automacao.resumo_por_origem(conn)
    assert r["totalOrdens"] == 4
    assert r["porOrigem"]["manual"]["ordens"] == 2
    assert r["porOrigem"]["automatico"]["ordens"] == 2
    assert r["porOrigem"]["manual"]["pnlTotal"] == 200.0     # (40-38)*100
    assert r["porOrigem"]["automatico"]["pnlTotal"] == -200.0  # (58-60)*100
    conn.close()


def test_resumo_por_origem_desconhecida_para_historico_legado():
    conn = _fresh_db()
    h = store.get(conn, "history", user_id="u1")
    h.append({"date": "2026-01-01", "type": "COMPRA", "t": "OLD4", "qty": 100, "price": 10.0, "pnl": None})
    store.put(conn, "history", h, user_id="u1")
    r = automacao.resumo_por_origem(conn)
    assert r["porOrigem"]["desconhecida"]["ordens"] == 1
    conn.close()


def test_resumo_por_origem_pnl_conta_so_vendas():
    conn = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0, user_id="u1")  # pnl None
    r = automacao.resumo_por_origem(conn)
    assert r["porOrigem"]["manual"]["pnlContagem"] == 0
    assert r["porOrigem"]["manual"]["pnlTotal"] == 0.0
    conn.close()


# -------------------------- correlacao_analise_operacao ----------------------

def test_correlacao_vincula_ordem_a_analise_por_snapshot_id():
    conn = _fresh_db()
    ao.registrar(conn, ticker="PETR4", modo="operador", tipo="n1", modelo="x",
                 setup="IFR2", recomendacao="COMPRAR", stop=37.0, alvo=40.0, preco=38.0,
                 snapshot_id="snap1", user_id="u1")
    outs = db.kv_get(conn, "analysisOutcomes", [], user_id="u1")
    outs[0].update(resultado="alvo", rMultiple=2.0, resolvidoEm="2026-08-20")
    db.kv_set(conn, "analysisOutcomes", outs, user_id="u1")
    store.buy(conn, "PETR4", 100, 38.0, user_id="u1", origem="automatico",
              meta={"snapshotId": "snap1"})
    r = automacao.correlacao_analise_operacao(conn)
    assert r["ordensDeEntrada"] == 1
    assert r["comSnapshotVinculado"] == 1
    assert r["coberturaPct"] == 100.0
    assert r["vinculadasComAnaliseRegistrada"] == 1
    assert r["resolvidas"] == 1
    assert r["seguiuAnaliseComSucesso"] == 1
    conn.close()


def test_correlacao_cobertura_parcial_quando_ordem_sem_snapshot():
    conn = _fresh_db()
    store.buy(conn, "PETR4", 100, 38.0, user_id="u1")  # sem meta.snapshotId
    store.buy(conn, "VALE3", 100, 60.0, user_id="u1", meta={"snapshotId": "snap-orfao"})
    r = automacao.correlacao_analise_operacao(conn)
    assert r["ordensDeEntrada"] == 2
    assert r["comSnapshotVinculado"] == 1
    assert r["coberturaPct"] == 50.0
    assert r["vinculadasComAnaliseRegistrada"] == 0  # snapshot não bate com nenhuma análise registrada
    conn.close()


def test_correlacao_sem_ordens_devolve_cobertura_none_nao_zero_falso():
    conn = _fresh_db()
    r = automacao.correlacao_analise_operacao(conn)
    assert r["ordensDeEntrada"] == 0
    assert r["coberturaPct"] is None  # não é 0% (que pareceria "cobertura ruim"), é "sem dado"
    conn.close()


# ------------------------------- maybe_refresh_cache --------------------------

def test_maybe_refresh_cache_popula_e_respeita_gate_diario():
    conn = _fresh_db()
    cache_conn = _analytics_conn()
    store.buy(conn, "PETR4", 100, 38.0, user_id="u1", origem="automatico")
    ok1 = automacao.maybe_refresh_cache(conn, cache_conn)
    assert ok1 is True
    assert analytics.get_cache(cache_conn, "automacao_resumo") is not None
    assert analytics.get_cache(cache_conn, "automacao_correlacao") is not None
    ok2 = automacao.maybe_refresh_cache(conn, cache_conn)
    assert ok2 is None  # já rodou hoje — gate impede recálculo
    conn.close()
    cache_conn.close()


# ================================ rotas (TestClient) =========================
@pytest.fixture(autouse=True)
def _app_main_isolado():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, admin_emails=None):
    if admin_emails is None:
        monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    else:
        monkeypatch.setenv("B3_ADMIN_EMAILS", admin_emails)
    d = tempfile.mkdtemp(prefix="b3_automacao_route_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3_agente.db"))
    sys.modules.pop("app.main", None)
    sys.modules.pop("app.analytics", None)
    sys.modules.pop("app.analysis_outcomes", None)
    sys.modules.pop("app.automacao", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main, d


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["token"], body["user"]["id"]


def test_rota_automacao_e_admin_only(monkeypatch):
    c, _main, _d = _client(monkeypatch)
    token_admin, _ = _registra(c, "dono@teste.com")
    token_comum, _ = _registra(c, "outro@teste.com")
    r_comum = c.get("/api/analytics/automacao", headers={"authorization": f"Bearer {token_comum}"})
    assert r_comum.status_code == 403
    r_admin = c.get("/api/analytics/automacao", headers={"authorization": f"Bearer {token_admin}"})
    assert r_admin.status_code == 200
    body = r_admin.json()
    assert "totalOrdens" in body and "correlacaoAnaliseOperacao" in body and "computedAt" in body


def test_rota_automacao_cold_start_agrega_todos_os_usuarios(monkeypatch):
    c, main, _d = _client(monkeypatch)
    token_admin, uid_admin = _registra(c, "dono@teste.com")
    _token_outro, uid_outro = _registra(c, "outro@teste.com")
    store.buy(main._conn, "PETR4", 100, 38.0, user_id=uid_admin, origem="manual")
    store.buy(main._conn, "VALE3", 100, 60.0, user_id=uid_outro, origem="automatico")
    assert analytics.get_cache(main._analytics_conn, "automacao_resumo") is None
    r = c.get("/api/analytics/automacao", headers={"authorization": f"Bearer {token_admin}"})
    assert r.status_code == 200
    body = r.json()
    assert body["totalOrdens"] == 2
    assert analytics.get_cache(main._analytics_conn, "automacao_resumo") is not None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
