"""Fase 12 (v1.3, ADR-010) — guardião de COMPORTAMENTO do cap de watchlist.

D-01 (12-CONTEXT.md): a Fase 12 ativou `PLAN_FREE["max_watchlist"] = 10`
(Plano 12-01). Este arquivo trava o Plano 12-02, que fechou o bypass real:
`PUT /api/watchlist` recebia a lista FINAL inteira sem passar por gate
nenhum — e é justamente esse endpoint que o front usa no quick-add do push e
na seleção em massa do catálogo (D-02). Sem o Plano 12-02, dava para
ultrapassar 10 ativos pelo catálogo ignorando o limite que o
`POST /api/watchlist/add` já respeitava.

O gate do PUT tem semântica DIFERENTE do POST: ele recebe a lista FINAL
arbitrária e só pode barrar CRESCIMENTO (D-03) — remoção e reordenação nunca
são recusadas, mesmo para uma conta que já está acima do limite (D-04,
grandfather clause: quem já tinha mais de 10 ativos antes da ativação não
perde nada em silêncio).

Isolamento igual a test_fase3_gate_plano.py/test_fase5_gate_mensal.py (B3_DB_PATH
temporário, reimport de app.main por teste) — necessário porque `_conn`/caches
em memória (managed, kill-switch, orçamento brapi) são globais de módulo.
"""
import importlib
import os
import pathlib
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolado(monkeypatch):
    from app import agent, brapi_budget, managed
    original = sys.modules.get("app.main")
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    yield
    brapi_budget.reset()
    agent.reset_kill_switch_cache()
    managed.reset_cache()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def _client(monkeypatch, env=None):
    d = tempfile.mkdtemp(prefix="b3_cap_watchlist_test_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    for k, v in (env or {}).items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    return TestClient(main.app), main


def _registra(c, email, senha="senhaboa123"):
    r = c.post("/api/auth/register", json={"email": email, "password": senha})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token):
    return {"authorization": f"Bearer {token}"}


async def _quote_fake(_t):
    return {"t": "PETR4", "name": "Petrobras PN", "price": 35.5, "change": 0.5}


async def _quotes_fake(tickers):
    return {t: {"t": t, "name": t, "price": 10.0, "change": 0.0} for t in tickers}


def _semeia(main, scope, n):
    """Semeia a watchlist com N tickers do catálogo padrão (sempre 'conhecidos'
    — sobrevivem à normalização de store.set_watchlist sem precisar de
    add_custom). Verifica o tamanho efetivo antes do act de cada teste, senão
    a lista semeada poderia encolher em silêncio e o teste mediria a coisa
    errada."""
    catalogo = main.store.CATALOG_TICKERS
    assert len(catalogo) >= n, f"catálogo padrão só tem {len(catalogo)} tickers, precisa de {n}"
    tickers_n = list(catalogo[:n])
    gravado = main.store.set_watchlist(main._conn, tickers_n, user_id=scope)
    assert len(gravado) == n, f"semeadura encolheu: esperado {n}, gravado {len(gravado)}"
    return tickers_n


# ---------------------------------------------------------------------------
# (a)-(b) fronteira exata: 10 permitido, 11 não
# ---------------------------------------------------------------------------

def test_a_free_10_ativos_put_com_11_devolve_402_com_10_ativos_no_detail(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "free10@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 10)
    catalogo = main.store.CATALOG_TICKERS

    r = c.put("/api/watchlist", json={"tickers": base + [catalogo[10]]}, headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    assert "10 ativos" in r.json()["detail"]


def test_b_free_9_ativos_put_com_10_devolve_200(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "free9@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 9)
    catalogo = main.store.CATALOG_TICKERS

    r = c.put("/api/watchlist", json={"tickers": base + [catalogo[9]]}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    assert len(r.json()["watchlist"]) == 10


# ---------------------------------------------------------------------------
# (c)-(f) D-04 grandfather clause: conta já acima do limite nunca é truncada
# ---------------------------------------------------------------------------

def test_c_grandfathered_15_ativos_put_mesmos_15_reordenados_devolve_200(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "grand15@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 15)

    reordenado = list(reversed(base))
    r = c.put("/api/watchlist", json={"tickers": reordenado}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    assert len(r.json()["watchlist"]) == 15


def test_d_grandfathered_15_ativos_put_com_5_devolve_200_reducao_nunca_bloqueia(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "reduz15@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 15)

    r = c.put("/api/watchlist", json={"tickers": base[:5]}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    assert len(r.json()["watchlist"]) == 5


def test_e_grandfathered_15_ativos_put_com_16_devolve_402_crescer_do_topo_ainda_e_crescer(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "cresce15@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 15)
    catalogo = main.store.CATALOG_TICKERS

    r = c.put("/api/watchlist", json={"tickers": base + [catalogo[15]]}, headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text


def test_f_grandfathered_15_ativos_sem_put_get_state_devolve_15_intactos(monkeypatch):
    """D-04 explícito: a ativação do cap não trunca nem remove nada em
    silêncio — é a leitura de estado, não só o status code, que prova isso."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "intacto15@teste.com")
    scope = payload["user"]["id"]
    _semeia(main, scope, 15)

    r = c.get("/api/state", headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    assert len(r.json()["watchlist"]) == 15


# ---------------------------------------------------------------------------
# (g) CAP-04: conta pro passa de 10 sem recusa
# ---------------------------------------------------------------------------

def test_g_conta_pro_com_10_ativos_put_com_11_devolve_200(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "pro10@teste.com")
    scope = payload["user"]["id"]
    main.db.set_user_plan(main._conn, scope, "pro")
    base = _semeia(main, scope, 10)
    catalogo = main.store.CATALOG_TICKERS

    r = c.put("/api/watchlist", json={"tickers": base + [catalogo[10]]}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    assert len(r.json()["watchlist"]) == 11


# ---------------------------------------------------------------------------
# (h) CAP-01 pelo outro caminho: POST /api/watchlist/add também fechado
# ---------------------------------------------------------------------------

def test_h_free_10_ativos_post_watchlist_add_11o_devolve_402(monkeypatch):
    c, main = _client(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake)
    payload = _registra(c, "add11@teste.com")
    scope = payload["user"]["id"]
    _semeia(main, scope, 10)

    r = c.post("/api/watchlist/add", json={"ticker": "RDOR3"}, headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text


# ---------------------------------------------------------------------------
# (i) CAP-05: não-regressão — depois de uma recusa, o resto do app não degrada
# ---------------------------------------------------------------------------

def test_i_apos_recusa_no_put_resto_do_app_continua_respondendo(monkeypatch):
    c, main = _client(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake)
    monkeypatch.setattr(main.candle_provider, "get_quotes", _quotes_fake)
    payload = _registra(c, "naoregride@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 10)
    catalogo = main.store.CATALOG_TICKERS

    r402 = c.put("/api/watchlist", json={"tickers": base + [catalogo[10]]}, headers=_auth(payload["token"]))
    assert r402.status_code == 402, r402.text

    # redução, na MESMA sessão que acabou de tomar 402, continua liberada
    r_reduz = c.put("/api/watchlist", json={"tickers": base[:5]}, headers=_auth(payload["token"]))
    assert r_reduz.status_code == 200, r_reduz.text

    r_state = c.get("/api/state", headers=_auth(payload["token"]))
    assert r_state.status_code == 200, r_state.text

    r_quotes = c.get("/api/quotes", params={"symbols": "PETR4"}, headers=_auth(payload["token"]))
    assert r_quotes.status_code == 200, r_quotes.text

    r_buy = c.post("/api/buy", json={"t": "PETR4", "qty": 100}, headers=_auth(payload["token"]))
    assert r_buy.status_code == 200, r_buy.text


# ---------------------------------------------------------------------------
# (j) CAP-07: sem linguagem de upgrade/CTA na recusa
# ---------------------------------------------------------------------------

def test_j_detail_do_402_nao_contem_linguagem_de_upgrade(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "semcta@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 10)
    catalogo = main.store.CATALOG_TICKERS

    r = c.put("/api/watchlist", json={"tickers": base + [catalogo[10]]}, headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    detail = r.json()["detail"].lower()
    assert "upgrade" not in detail
    assert "assine" not in detail


# ---------------------------------------------------------------------------
# (k) recusa falsa não existe: tamanho CRU do body != tamanho FINAL efetivo
# ---------------------------------------------------------------------------

def test_k_lista_com_desconhecidos_e_repetidos_nao_gera_recusa_falsa(monkeypatch):
    """9 ativos válidos + 1 novo válido + 1 desconhecido + 2 repetidos —
    tamanho CRU do body é 13, mas o tamanho FINAL efetivo é 10 (9 + 1 novo;
    o desconhecido é filtrado, os repetidos são deduplicados). Se o gate
    comparasse o cru, isto recusaria à toa."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "semfalsopositivo@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 9)
    catalogo = main.store.CATALOG_TICKERS

    body_cru = base + [catalogo[9], "ZZZZ99", base[0], base[1]]
    assert len(body_cru) == 13

    r = c.put("/api/watchlist", json={"tickers": body_cru}, headers=_auth(payload["token"]))
    assert r.status_code == 200, r.text
    assert len(r.json()["watchlist"]) == 10


# ---------------------------------------------------------------------------
# Guardião ESTÁTICO — fecha a CLASSE do bypass, não só a instância
# ---------------------------------------------------------------------------

def _main_source_sem_comentarios() -> str:
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    return "\n".join(line for line in src.splitlines() if not line.strip().startswith("#"))


def test_put_watchlist_referencia_can_add_ticker_nao_e_mais_set_watchlist_puro():
    src = _main_source_sem_comentarios()
    inicio = src.index("def put_watchlist")
    fim = src.index("def ", inicio + 1)
    corpo = src[inicio:fim]
    assert "can_add_ticker" in corpo


def test_plan_can_add_ticker_aparece_exatamente_duas_vezes_no_main():
    """Se um terceiro caminho de escrita de watchlist nascer sem gate, ou se
    alguém duplicar o gate, este guardião grita — mesma classe de bypass que
    o T-12-05/T-12-06 do threat model do Plano 12-02 cobre."""
    assert _main_source_sem_comentarios().count("plan.can_add_ticker(") == 2


def test_frase_de_recusa_nao_duplicada_no_main():
    """A frase de recusa mora só em plan.py (D-05/CAP-07) — main.py nunca
    reescreve a string, sempre reusa o `reason` devolvido pelo hook."""
    assert _main_source_sem_comentarios().count("atingiu o limite") == 0
