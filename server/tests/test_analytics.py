"""qa/47 — Analytics de comportamento: ingest genérico, rollup diário, purga
de 90 dias e leitura admin (Fase 1, infra de backend). Sem pytest-only: a
parte de módulo roda no mini-runner; a parte de rota usa TestClient (mesmo
padrão de test_admin_summary.py).
"""
import importlib
import os
import sqlite3
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import analytics


def _conn():
    c = sqlite3.connect(":memory:")
    analytics.init_db(c)
    return c


@pytest.fixture(autouse=True)
def _reset_last_rollup():
    analytics.LAST_ROLLUP.update(date=None, eventos=None, purgados=None, erro=None)
    yield


# ------------------------------- caminho do banco ---------------------------
def test_default_db_path_deriva_de_b3_db_path(monkeypatch):
    d = os.path.realpath(tempfile.mkdtemp(prefix="b3_analytics_path_"))
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3_agente.db"))
    assert analytics.default_db_path() == os.path.join(d, "analytics.db")


def test_default_db_path_nunca_relativo_ao_cwd(monkeypatch):
    monkeypatch.delenv("B3_DB_PATH", raising=False)
    assert os.path.isabs(analytics.default_db_path())


# ------------------------------------ ingest ---------------------------------
def test_ingest_aceita_lote_valido():
    c = _conn()
    r = analytics.ingest(c, "u1", [
        {"event": "tela_aberta", "properties": {"tela": "radar"}},
        {"event": "tela_aberta", "properties": {}},
    ])
    assert r["accepted"] == 2
    n = c.execute("SELECT COUNT(*) FROM analytics_events").fetchone()[0]
    assert n == 2


def test_ingest_rejeita_lote_vazio_ou_invalido():
    c = _conn()
    with pytest.raises(ValueError):
        analytics.ingest(c, "u1", [])
    with pytest.raises(ValueError):
        analytics.ingest(c, "u1", "não é lista")
    with pytest.raises(ValueError):
        analytics.ingest(c, "u1", [{"properties": {}}])  # sem 'event'


@pytest.mark.parametrize("chave", ["email", "Email", "cpf", "senha", "password",
                                    "token", "saldoReal", "valorReal", "numeroCartao"])
def test_ingest_rejeita_chave_sensivel_em_properties(chave):
    c = _conn()
    with pytest.raises(ValueError, match="proibido"):
        analytics.ingest(c, "u1", [{"event": "x", "properties": {chave: "qualquer"}}])
    assert c.execute("SELECT COUNT(*) FROM analytics_events").fetchone()[0] == 0, \
        "lote rejeitado não pode gravar NADA, nem os eventos sem a chave sensível"


def test_ingest_aceita_user_id_none_anonimo():
    c = _conn()
    r = analytics.ingest(c, None, [{"event": "onboarding_completed"}])
    assert r["accepted"] == 1


# ------------------------------------ rollup ---------------------------------
def test_rollup_day_agrega_contagem_e_distinct_users():
    c = _conn()
    dia_fixo = 1_800_000_000.0  # timestamp fixo — não depende do relógio real
    analytics.ingest(c, "u1", [{"event": "trade_simulated"}, {"event": "trade_simulated"}], _now=dia_fixo)
    analytics.ingest(c, "u2", [{"event": "trade_simulated"}], _now=dia_fixo)
    analytics.ingest(c, "u1", [{"event": "radar_shown"}], _now=dia_fixo)
    dia = analytics._dia(dia_fixo)
    n = analytics.rollup_day(c, dia)
    assert n == 2  # 2 eventos distintos: trade_simulated, radar_shown
    rows = {r[0]: r for r in c.execute(
        "SELECT event, count, distinct_users FROM analytics_daily WHERE day = ?", (dia,))}
    assert rows["trade_simulated"][1] == 3 and rows["trade_simulated"][2] == 2
    assert rows["radar_shown"][1] == 1 and rows["radar_shown"][2] == 1


def test_rollup_day_e_idempotente():
    c = _conn()
    t = 1_800_000_000.0
    analytics.ingest(c, "u1", [{"event": "x"}], _now=t)
    analytics.rollup_day(c, analytics._dia(t))
    analytics.rollup_day(c, analytics._dia(t))  # roda 2x — não duplica
    n = c.execute("SELECT COUNT(*) FROM analytics_daily WHERE day = ?", (analytics._dia(t),)).fetchone()[0]
    assert n == 1


# ------------------------------------- purga ----------------------------------
def test_purge_remove_so_o_que_passou_da_retencao():
    c = _conn()
    recente = 1_800_000_000.0          # dia "de hoje" no teste
    antigo = recente - 91 * 86400      # 91 dias antes — deve ser purgado
    no_limite = recente - 89 * 86400   # 89 dias antes — NÃO deve ser purgado
    analytics.ingest(c, "u1", [{"event": "a"}], _now=recente)
    analytics.ingest(c, "u1", [{"event": "b"}], _now=antigo)
    analytics.ingest(c, "u1", [{"event": "c"}], _now=no_limite)
    cutoff = analytics._dia(recente - analytics.RETENCAO_DIAS * 86400)
    n = analytics.purge_older_than(c, cutoff)
    assert n == 1
    restantes = {r[0] for r in c.execute("SELECT event FROM analytics_events")}
    assert restantes == {"a", "c"}


# ------------------------------------ maybe_run --------------------------------
def test_maybe_run_agrega_ontem_e_purga_no_maximo_1x_por_dia():
    c = _conn()
    hoje = 1_800_000_000.0
    ontem = hoje - 86400
    analytics.ingest(c, "u1", [{"event": "x"}], _now=ontem)
    import asyncio
    r1 = asyncio.new_event_loop().run_until_complete(analytics.maybe_run(c, _now=hoje))
    assert r1 is not None and r1["eventos"] == 1
    assert c.execute("SELECT COUNT(*) FROM analytics_daily").fetchone()[0] == 1
    r2 = asyncio.new_event_loop().run_until_complete(analytics.maybe_run(c, _now=hoje))
    assert r2 is None, "já rodou hoje — não roda de novo no mesmo dia"


def test_maybe_run_desligado_por_env(monkeypatch):
    monkeypatch.setenv("B3_ANALYTICS_OFF", "1")
    c = _conn()
    import asyncio
    r = asyncio.new_event_loop().run_until_complete(analytics.maybe_run(c, _now=1_800_000_000.0))
    assert r is None


def test_maybe_run_nunca_propaga_excecao(monkeypatch):
    c = _conn()
    monkeypatch.setattr(analytics, "rollup_day", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    import asyncio
    r = asyncio.new_event_loop().run_until_complete(analytics.maybe_run(c, _now=1_800_000_000.0))
    assert r is None
    assert "boom" in analytics.LAST_ROLLUP["erro"]


# --------------------------------- as 3 queries --------------------------------
def test_adocao_por_feature():
    c = _conn()
    t = 1_800_000_000.0
    analytics.ingest(c, "u1", [{"event": "radar_shown"}, {"event": "radar_shown"}], _now=t)
    analytics.ingest(c, "u2", [{"event": "radar_shown"}], _now=t)
    r = analytics.adocao_por_feature(c, dias=30, _now=t)
    item = next(x for x in r if x["event"] == "radar_shown")
    assert item["count"] == 3 and item["usuariosDistintos"] == 2


def test_funil_conta_so_quem_completa_em_sequencia():
    c = _conn()
    t0 = 1_800_000_000.0
    # u1: completa os dois passos, em ordem
    analytics.ingest(c, "u1", [{"event": "onboarding_step_completed", "ts": t0}], _now=t0)
    analytics.ingest(c, "u1", [{"event": "trade_simulated", "ts": t0 + 10}], _now=t0)
    # u2: só o primeiro passo
    analytics.ingest(c, "u2", [{"event": "onboarding_step_completed", "ts": t0}], _now=t0)
    r = analytics.funil(c, dias=30, _now=t0)
    passos = {p["passo"]: p["usuarios"] for p in r["passos"]}
    assert passos["onboarding_step_completed"] == 2
    assert passos["trade_simulated"] == 1


def test_shown_vs_dismissed_casa_por_prefixo():
    c = _conn()
    t = 1_800_000_000.0
    analytics.ingest(c, "u1", [{"event": "nudge_x_shown"}, {"event": "nudge_x_shown"},
                               {"event": "nudge_x_dismissed"}], _now=t)
    r = analytics.shown_vs_dismissed(c, dias=30, _now=t)
    item = next(x for x in r if x["feature"] == "nudge_x")
    assert item["shown"] == 2 and item["dismissed"] == 1


# =============================================================================
# Rotas — mesmo isolamento de test_admin_summary.py (B3_DB_PATH temporário,
# app.main reimportado a cada teste para reler env de módulo).
# =============================================================================
@pytest.fixture(autouse=True)
def _app_main_isolado():
    original = sys.modules.get("app.main")
    yield
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, admin_emails=None, **env):
    if admin_emails is None:
        monkeypatch.delenv("B3_ADMIN_EMAILS", raising=False)
    else:
        monkeypatch.setenv("B3_ADMIN_EMAILS", admin_emails)
    for k, v in env.items():
        monkeypatch.setenv(k, str(v))
    d = tempfile.mkdtemp(prefix="b3_analytics_route_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3_agente.db"))
    sys.modules.pop("app.main", None)
    sys.modules.pop("app.analytics", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main, d


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_post_events_sem_login_e_401(monkeypatch):
    c, _, _d = _client(monkeypatch)
    assert c.post("/api/analytics/events", json={"events": [{"event": "x"}]}).status_code == 401


def test_post_events_aceita_lote_valido(monkeypatch):
    c, _, _d = _client(monkeypatch)
    token = _registra(c, "u@teste.com")
    r = c.post("/api/analytics/events", json={"events": [{"event": "onboarding_completed"}]},
               headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    assert r.json()["accepted"] == 1


def test_post_events_rejeita_chave_sensivel(monkeypatch):
    c, _, _d = _client(monkeypatch)
    token = _registra(c, "u@teste.com")
    r = c.post("/api/analytics/events",
               json={"events": [{"event": "x", "properties": {"email": "a@a.com"}}]},
               headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 400


def test_post_events_estoura_cota_diaria_e_429(monkeypatch):
    c, _, _d = _client(monkeypatch, B3_ANALYTICS_QUOTA_DIA=1)
    token = _registra(c, "u@teste.com")
    headers = {"authorization": f"Bearer {token}"}
    r1 = c.post("/api/analytics/events", json={"events": [{"event": "a"}]}, headers=headers)
    assert r1.status_code == 200
    r2 = c.post("/api/analytics/events", json={"events": [{"event": "b"}]}, headers=headers)
    assert r2.status_code == 429


def test_get_summary_e_admin_only(monkeypatch):
    c, _, _d = _client(monkeypatch)
    token_admin = _registra(c, "dono@teste.com")     # 1º usuário = admin por default
    token_comum = _registra(c, "outro@teste.com")
    r_comum = c.get("/api/analytics/summary", headers={"authorization": f"Bearer {token_comum}"})
    assert r_comum.status_code == 403
    r_admin = c.get("/api/analytics/summary", headers={"authorization": f"Bearer {token_admin}"})
    assert r_admin.status_code == 200
    body = r_admin.json()
    assert "adocaoPorFeature" in body and "funil" in body and "shownVsDismissed" in body


def test_analytics_db_fica_no_mesmo_diretorio_do_b3_db_path(monkeypatch):
    c, _, d = _client(monkeypatch)
    token = _registra(c, "u@teste.com")
    r = c.post("/api/analytics/events", json={"events": [{"event": "x"}]},
               headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert os.path.exists(os.path.join(d, "b3_agente.db"))
    assert os.path.exists(os.path.join(d, "analytics.db")), \
        "analytics.db precisa nascer no MESMO diretório de B3_DB_PATH, não em cwd"
    assert not os.path.exists(os.path.join(os.getcwd(), "analytics.db")), \
        "analytics.db não pode nascer relativo ao cwd do processo"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
