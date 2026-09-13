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
import concurrent.futures
import importlib
import json
import os
import sys
import tempfile
import threading

import pytest
from fastapi.testclient import TestClient

from .fonte_python import main_source_sem_comentarios


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
    """ATUALIZADO em 2026-09-12 (25-06): o `detail` deixou de ser string e virou
    dict (`code`/`message`/`limite`/`usado`) para o app poder renderizar a
    recusa sem adivinhar pela frase. Mudou o CAMINHO de acesso
    (`["detail"]` -> `["detail"]["message"]`), NÃO o conteúdo: a frase de
    `plan.can_grow_watchlist_to` continua sendo o que chega ao usuário — é
    exatamente isso que esta asserção guarda, e por isso ela não foi apagada."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "free10@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 10)
    catalogo = main.store.CATALOG_TICKERS

    r = c.put("/api/watchlist", json={"tickers": base + [catalogo[10]]}, headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    assert "10 ativos" in r.json()["detail"]["message"]


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
    """ATUALIZADO em 2026-09-12 (25-06): varre o `detail` INTEIRO serializado,
    não só a frase. O detail virou dict e uma chave nova poderia trazer CTA de
    upgrade sem que a `message` mudasse — a asserção ficou mais forte, não mais
    fraca, e cobre o que o ADR-010 (decisão 4) proíbe."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "semcta@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 10)
    catalogo = main.store.CATALOG_TICKERS

    r = c.put("/api/watchlist", json={"tickers": base + [catalogo[10]]}, headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    detail = json.dumps(r.json()["detail"], ensure_ascii=False).lower()
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
# (l) WR-03 (12-REVIEW.md): `tickers` truthy não-lista é 400, não 500/zera-silêncio
# ---------------------------------------------------------------------------

def test_l_tickers_string_devolve_400_em_vez_de_zerar_watchlist_em_silencio(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "tickersstring@teste.com")
    scope = payload["user"]["id"]
    _semeia(main, scope, 3)

    r = c.put("/api/watchlist", json={"tickers": "PETR4"}, headers=_auth(payload["token"]))
    assert r.status_code == 400, r.text
    assert len(main.store.get(main._conn, "watchlist", user_id=scope)) == 3


def test_l_tickers_bool_devolve_400_em_vez_de_500_opaco(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "tickersbool@teste.com")

    r = c.put("/api/watchlist", json={"tickers": True}, headers=_auth(payload["token"]))
    assert r.status_code == 400, r.text


# ---------------------------------------------------------------------------
# (m) WR-01 (12-REVIEW.md): read-modify-write sob trava — sem lost update
# ---------------------------------------------------------------------------

def test_m_adds_concorrentes_de_tickers_diferentes_nao_perdem_update(monkeypatch):
    """Antes da trava (WR-01), dois POST /api/watchlist/add concorrentes de
    tickers DIFERENTES liam o mesmo `wl` e o último a escrever `wl + [t]`
    sobrescrevia a adição do outro (lost update) — a mesma classe de bug que
    `store.ORDER_LOCK` existe pra fechar em cash/positions. Usa um Barrier
    pra forçar as duas threads a chegarem no read-check-write o mais perto
    possível uma da outra, maximizando a chance de pegar a janela da corrida."""
    async def _quote_qualquer(t):
        return {"t": t, "name": t, "price": 10.0, "change": 0.0}

    c, main = _client(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_qualquer)
    payload = _registra(c, "raceadd@teste.com")
    scope = payload["user"]["id"]
    headers = _auth(payload["token"])
    barreira = threading.Barrier(2)

    def _add(ticker):
        barreira.wait(timeout=5)
        return c.post("/api/watchlist/add", json={"ticker": ticker}, headers=headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(_add, "ZZZZ1")
        f2 = ex.submit(_add, "ZZZZ2")
        r1, r2 = f1.result(), f2.result()

    assert r1.status_code == 200, r1.text
    assert r2.status_code == 200, r2.text
    persistida = main.store.get(main._conn, "watchlist", user_id=scope)
    assert "ZZZZ1" in persistida
    assert "ZZZZ2" in persistida


def test_m_watchlist_lock_protege_put_e_post_add():
    src = _main_source_sem_comentarios()
    for nome_rota in ("def put_watchlist", "def watchlist_add"):
        inicio = src.index(nome_rota)
        fim = src.index("def ", inicio + 1)
        corpo = src[inicio:fim]
        assert "store.WATCHLIST_LOCK" in corpo, nome_rota


# ---------------------------------------------------------------------------
# Guardião ESTÁTICO — fecha a CLASSE do bypass, não só a instância
# ---------------------------------------------------------------------------

# 2026-09-10 (auditoria A-18): era a 3ª de três cópias de um filtro de
# comentário que deixava passar comentário de CAUDA. Fonte única agora em
# `tests/fonte_python.py`, com corte por `tokenize` (um `#` dentro de string
# literal não pode levar código embora). Alias preserva o nome local.
_main_source_sem_comentarios = main_source_sem_comentarios


def test_put_watchlist_referencia_can_grow_watchlist_to_nao_e_mais_set_watchlist_puro():
    """Reversão deliberada de
    `test_put_watchlist_referencia_can_add_ticker_nao_e_mais_set_watchlist_puro`
    (WR-02, 12-REVIEW.md): o PUT passou a chamar `plan.can_grow_watchlist_to`
    (hook honesto de tamanho FINAL) em vez de reusar `plan.can_add_ticker` com
    o valor sintético `len(final) - 1`. O guardião original travava só a
    CLASSE do bypass ("ainda passa por algum gate, não é set_watchlist
    puro"); esta versão trava o nome certo do gate atual."""
    src = _main_source_sem_comentarios()
    inicio = src.index("def put_watchlist")
    fim = src.index("def ", inicio + 1)
    corpo = src[inicio:fim]
    assert "can_grow_watchlist_to" in corpo


def test_plan_gates_de_watchlist_aparecem_exatamente_uma_vez_cada_no_main():
    """Reversão deliberada de
    `test_plan_can_add_ticker_aparece_exatamente_duas_vezes_no_main` (WR-02,
    12-REVIEW.md): antes os dois call sites (PUT e POST /add) chamavam o
    MESMO hook `plan.can_add_ticker`, então "aparece 2x" bastava como
    guardião único. Agora cada rota tem seu hook honesto
    (`can_grow_watchlist_to` no PUT bulk, `can_add_ticker` no POST
    item-a-item) — o guardião correto é checar CADA um isoladamente. Se um
    terceiro caminho de escrita de watchlist nascer sem gate, ou se alguém
    duplicar um dos dois, esta versão ainda grita — mesma classe de bypass
    que o T-12-05/T-12-06 do threat model do Plano 12-02 cobre."""
    src = _main_source_sem_comentarios()
    assert src.count("plan.can_add_ticker(") == 1
    assert src.count("plan.can_grow_watchlist_to(") == 1


def test_frase_de_recusa_nao_duplicada_no_main():
    """A frase de recusa mora só em plan.py (D-05/CAP-07) — main.py nunca
    reescreve a string, sempre reusa o `reason` devolvido pelo hook."""
    assert _main_source_sem_comentarios().count("atingiu o limite") == 0


# ---------------------------------------------------------------------------
# 25-06: o 402 estruturado das DUAS rotas de watchlist
# ---------------------------------------------------------------------------
# Por que aqui e não num arquivo novo: é o MESMO gate que este arquivo já
# guarda desde a Fase 12; a Fase 25 só mudou a FORMA do corpo do 402. Um
# arquivo separado deixaria as duas metades do mesmo contrato em lugares
# diferentes, e a próxima mudança de forma atualizaria só uma.


def test_25_06_put_devolve_detail_estruturado_com_codigo_e_numeros(monkeypatch):
    c, main = _client(monkeypatch)
    payload = _registra(c, "estruturado_put@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 10)
    catalogo = main.store.CATALOG_TICKERS

    r = c.put("/api/watchlist", json={"tickers": base + [catalogo[10]]}, headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    d = r.json()["detail"]
    assert isinstance(d, dict), d
    assert d["code"] == "watchlist_limite"
    assert d["limite"] == 10
    # `usado` é o tamanho de HOJE (10), NÃO o pedido (11): o mesmo campo é lido
    # por um componente compartilhado no front, e um sentido por rota faria a
    # tela mostrar número certo numa e errado na outra.
    assert d["usado"] == 10


def test_25_06_post_add_devolve_detail_estruturado_com_codigo_e_numeros(monkeypatch):
    c, main = _client(monkeypatch)
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote_fake)
    payload = _registra(c, "estruturado_add@teste.com")
    scope = payload["user"]["id"]
    _semeia(main, scope, 10)

    r = c.post("/api/watchlist/add", json={"ticker": "RDOR3"}, headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    d = r.json()["detail"]
    assert isinstance(d, dict), d
    assert d["code"] == "watchlist_limite"
    assert d["limite"] == 10
    assert d["usado"] == 10


def test_25_06_message_e_a_frase_de_plan_py_verbatim(monkeypatch):
    """O critério que impede esta mudança de virar reescrita de copy: a frase
    que chega ao usuário é BYTE A BYTE a que `plan.py` produz — comparada
    contra a fonte, não contra um literal copiado para cá (que divergiria em
    silêncio na primeira mudança de texto do backend)."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "verbatim@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 10)
    catalogo = main.store.CATALOG_TICKERS

    _allowed, esperado = main.plan.can_grow_watchlist_to(11, plan=main.plan.PLAN_FREE)
    r = c.put("/api/watchlist", json={"tickers": base + [catalogo[10]]}, headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    assert r.json()["detail"]["message"] == esperado


def test_25_06_conta_grandfathered_reporta_o_que_tem_hoje_nao_o_teto(monkeypatch):
    """D-04 (grandfather clause) pelo lado do número publicado: quem tem 15 com
    teto 10 recebe `usado: 15` e `limite: 10`. Truncar `usado` no teto seria
    fabricar um número (princípio 4 do CLAUDE.md) e esconder justamente a
    conta em que os dois valores divergem."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "grandfather402@teste.com")
    scope = payload["user"]["id"]
    base = _semeia(main, scope, 15)
    catalogo = main.store.CATALOG_TICKERS

    r = c.put("/api/watchlist", json={"tickers": base + [catalogo[15]]}, headers=_auth(payload["token"]))
    assert r.status_code == 402, r.text
    d = r.json()["detail"]
    assert d["usado"] == 15
    assert d["limite"] == 10


def test_25_06_o_402_do_gate_de_analise_continua_string(monkeypatch):
    """A fronteira desta mudança. O 402 de `_gate_analise` NÃO virou dict: o
    app lê aquele texto direto (`enrichErrorMessage`/fallback determinístico do
    FIX-C01) e o 25-04 registrou a decisão por escrito. Sem esta asserção, a
    próxima pessoa 'uniformiza' os dois e a tela mostra `[object Object]`."""
    c, main = _client(monkeypatch)
    payload = _registra(c, "analise_string@teste.com")
    uid = payload["user"]["id"]
    # Estoura o mês pelo LEDGER (monkeypatch), não configurando o catálogo:
    # `plan.set_limite_do_plano` grava num cache de MÓDULO que sobrevive ao
    # reimport de `app.main` e vazaria para os outros casos da suíte.
    monkeypatch.setattr(main.metering, "month_used", lambda *_a, **_k: 10 ** 6)
    with pytest.raises(main.HTTPException) as e:
        main._gate_analise(uid, {})
    assert e.value.status_code == 402
    assert isinstance(e.value.detail, str)


def test_25_06_o_codigo_e_a_constante_publicada_nao_um_literal_solto():
    """`COD_WATCHLIST` existe como constante (contrato publicado, lido pelo
    front) e as duas rotas passam pelo MESMO construtor de recusa — duas
    montagens do dict divergiriam no primeiro campo novo."""
    src = _main_source_sem_comentarios()
    assert 'COD_WATCHLIST = "watchlist_limite"' in src
    assert src.count("_recusa_de_watchlist(") == 3  # 1 definição + 2 call sites
