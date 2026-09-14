"""Fase 30, Plano 02 — `GET /api/options/curadoria` exercitada de verdade via
`TestClient` (o motor puro que ela consome já está coberto em
`test_opcoes_curadoria.py`, Plano 01; aqui é o fio elétrico: partição
elegível/ignorada, contagem de chamadas ao provider, ordem do motor no
payload HTTP, e a ausência de IA/MCP na rota).

O coração deste arquivo é o contador de chamadas a `options_provider.
get_options` — a propriedade "uma busca de cadeia por posição elegível, zero
por posição inelegível, zero por strike extra" (D3, SC-2) só é uma garantia
real se for um teste que quebra, não um comentário. Toda asserção de
contagem aqui é igualdade EXATA (`== N`), nunca `>= 1`.
"""
import datetime as dt
import uuid

import pytest
from fastapi.testclient import TestClient

from app import candle_provider, db, options_provider, store
from app.main import app, _conn

_EXP = (dt.date.today() + dt.timedelta(days=30)).isoformat()  # sempre dentro de 15..60 dias
_SPOT = 29.0


def _contrato(symbol, strike, price=1.5, volume=5000, oi=1000, bid=1.48, ask=1.52):
    """Contrato ADR-004, líquido por padrão (score >= 55) — mesmo padrão de
    `test_opcoes_curadoria.py` (Plano 01)."""
    return {
        "contractSymbol": symbol, "optionType": "call", "strike": strike,
        "lastPrice": price, "bid": bid, "ask": ask, "volume": volume,
        "openInterest": oi, "impliedVolatility": 0.3, "inTheMoney": False,
        "currency": "BRL", "distancePct": None,
        "greeks": {"delta": None, "gamma": None, "vega": None, "theta": None, "rho": None},
        "expiration": _EXP,
    }


def _cadeia(underlying, n_strikes=1, provider_status="ok", spot=_SPOT):
    base = 30
    calls = [_contrato(f"{underlying}C{base + i}", base + i) for i in range(n_strikes)]
    return {
        "providerStatus": provider_status, "underlyingPrice": spot,
        "expiration": _EXP, "expirations": [_EXP],
        "calls": calls, "puts": [], "source": "teste",
    }


def _contador(chains: dict):
    """Embrulha `options_provider.get_options`: incrementa uma lista de
    tickers chamados e devolve a cadeia da fixture (ou uma cadeia degradada
    para ticker não mapeado — nunca KeyError)."""
    chamados = []

    async def _fake(ticker, *a, **k):
        chamados.append(ticker)
        return chains.get(ticker, _cadeia(ticker, provider_status="degraded"))

    return chamados, _fake


@pytest.fixture(autouse=True)
def _quote_fake(monkeypatch):
    # Sem rede: toda cadeia da fixture já traz `underlyingPrice`, então
    # `_spot_from_chain_or_quote` nem chega a usar a cotação — mas o helper
    # chama `candle_provider.get_quote` incondicionalmente, e sem mock a
    # rota bateria na rede real (sandbox sem saída, mesmo achado de
    # test_opcoes_lastreadas_rotas.py 2026-09-07).
    async def _fake(t, *a, **k):
        return {"t": t, "price": _SPOT, "source": "teste"}
    monkeypatch.setattr(candle_provider, "get_quote", _fake)


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _novo_escopo(cli, slug):
    email = f"curadoria-{slug}-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"]["id"], {"Authorization": "Bearer " + body["token"]}


def _liga_operador(user_id):
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id=user_id)


def _trava_parcial(uid, ticker, qty_livre_alvo):
    """`store.buy` sempre arredonda para cima ao lote mínimo de 100
    (`store.py:671`) — não dá para nascer uma posição com menos de 100
    ações por ali. Para simular lote livre < 100 (inelegível), trava
    diretamente `qtyTravada` (mesmo campo que `store.qty_livre` lê), do
    jeito que uma CALL coberta aberta faria."""
    positions = store.get(_conn, "positions", user_id=uid)
    pos = next(p for p in positions if p["t"] == ticker)
    pos["qtyTravada"] = pos["qty"] - qty_livre_alvo
    db.kv_set(_conn, "positions", positions, user_id=uid)


def _seed_carteira_padrao(uid):
    """3 posições: PETR4 (200 livres, elegível), VALE3 (300 livres,
    elegível), ITUB4 (lote 100, todo travado — 0 livre, inelegível)."""
    store.buy(_conn, "PETR4", 200, 25.0, user_id=uid)
    store.buy(_conn, "VALE3", 300, 60.0, user_id=uid)
    store.buy(_conn, "ITUB4", 100, 30.0, user_id=uid)
    _trava_parcial(uid, "ITUB4", qty_livre_alvo=50)  # 50 < 100: inelegível


# ─────────────────────────────────────────────────────────────────────────
# Contagem de chamadas ao provider (SC-2, D3) — o coração deste arquivo
# ─────────────────────────────────────────────────────────────────────────

def test_uma_chamada_por_posicao_elegivel(cli, monkeypatch):
    # SC-2: uma busca de cadeia por posição ELEGÍVEL, zero por inelegível.
    uid, headers = _novo_escopo(cli, "01")
    _liga_operador(uid)
    _seed_carteira_padrao(uid)
    chains = {"PETR4": _cadeia("PETR4", n_strikes=1), "VALE3": _cadeia("VALE3", n_strikes=1)}
    chamados, fake = _contador(chains)
    monkeypatch.setattr(options_provider, "get_options", fake)

    r = cli.get("/api/options/curadoria", headers=headers)
    assert r.status_code == 200, r.text
    assert len(chamados) == 2, f"esperado exatamente 2 chamadas, veio {chamados!r}"
    assert sorted(chamados) == ["PETR4", "VALE3"]
    assert "ITUB4" not in chamados


def test_nenhuma_chamada_extra_por_strike(cli, monkeypatch):
    # SC-2/D3: 8 calls líquidas por ticker (mais que os 5 strikes que o
    # motor pede) não gera nenhuma chamada de rede extra — a enumeração de
    # strikes é aritmética em memória sobre a MESMA cadeia já buscada.
    uid, headers = _novo_escopo(cli, "02")
    _liga_operador(uid)
    _seed_carteira_padrao(uid)
    chains = {"PETR4": _cadeia("PETR4", n_strikes=8), "VALE3": _cadeia("VALE3", n_strikes=8)}
    chamados, fake = _contador(chains)
    monkeypatch.setattr(options_provider, "get_options", fake)

    r = cli.get("/api/options/curadoria", headers=headers)
    assert r.status_code == 200, r.text
    assert len(chamados) == 2, f"esperado exatamente 2 chamadas, veio {chamados!r}"


def test_carteira_sem_posicao_elegivel_zero_chamadas(cli, monkeypatch):
    # SC-2: posição única com lote livre < 100 → `top` vazio, ticker em
    # `ignoradas`, e `get_options` NUNCA é chamado.
    uid, headers = _novo_escopo(cli, "03")
    _liga_operador(uid)
    store.buy(_conn, "ITUB4", 100, 30.0, user_id=uid)
    _trava_parcial(uid, "ITUB4", qty_livre_alvo=50)
    chamados, fake = _contador({})
    monkeypatch.setattr(options_provider, "get_options", fake)

    r = cli.get("/api/options/curadoria", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["top"] == []
    assert "ITUB4" in body["ignoradas"]
    assert chamados == []


def test_carteira_vazia_200_com_listas_vazias(cli, monkeypatch):
    # SC-1: carteira vazia devolve 200, nunca 500, listas vazias.
    uid, headers = _novo_escopo(cli, "04")
    _liga_operador(uid)
    chamados, fake = _contador({})
    monkeypatch.setattr(options_provider, "get_options", fake)

    r = cli.get("/api/options/curadoria", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["top"] == []
    assert body["avaliadas"] == []
    assert chamados == []


# ─────────────────────────────────────────────────────────────────────────
# Ordem do motor + teto de 4 (SC-1)
# ─────────────────────────────────────────────────────────────────────────

def test_ordem_e_do_motor(cli, monkeypatch):
    # SC-1: a ordem da lista vem 100% do motor determinístico (razão
    # prêmio/perda máxima) — nunca de IA nem da ordem de chegada das
    # posições na carteira.
    uid, headers = _novo_escopo(cli, "05")
    _liga_operador(uid)
    _seed_carteira_padrao(uid)
    # PETR4: prêmio alto (razão vencedora). VALE3: prêmio baixo.
    chain_petr = _cadeia("PETR4", n_strikes=0)
    chain_petr["calls"] = [_contrato("PETR4C30", 30, price=3.0)]
    chain_vale = _cadeia("VALE3", n_strikes=0)
    chain_vale["calls"] = [_contrato("VALE3C61", 61, price=0.2)]
    chains = {"PETR4": chain_petr, "VALE3": chain_vale}
    chamados, fake = _contador(chains)
    monkeypatch.setattr(options_provider, "get_options", fake)

    r = cli.get("/api/options/curadoria", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    top = body["top"]
    assert top, "esperava pelo menos 1 candidato no top"
    assert top[0]["contractSymbol"] == "PETR4C30"
    assert top[0]["posicaoNoRanking"] == 1
    razoes = [c["razao"] for c in top]
    assert razoes == sorted(razoes, reverse=True)
    assert list(range(1, len(top) + 1)) == [c["posicaoNoRanking"] for c in top]


def test_teto_de_quatro(cli, monkeypatch):
    # SC-1: 3 posições elegíveis com 5 candidatos cada (15 no pool) → top
    # nunca excede opcoes_curadoria.TOPO (4), mas `candidatosAvaliados`
    # revela o pool inteiro.
    uid, headers = _novo_escopo(cli, "06")
    _liga_operador(uid)
    store.buy(_conn, "PETR4", 200, 25.0, user_id=uid)
    store.buy(_conn, "VALE3", 300, 60.0, user_id=uid)
    store.buy(_conn, "ITUB4", 200, 30.0, user_id=uid)
    chains = {
        "PETR4": _cadeia("PETR4", n_strikes=5),
        "VALE3": _cadeia("VALE3", n_strikes=5),
        "ITUB4": _cadeia("ITUB4", n_strikes=5),
    }
    chamados, fake = _contador(chains)
    monkeypatch.setattr(options_provider, "get_options", fake)

    r = cli.get("/api/options/curadoria", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["top"]) == 4
    assert body["candidatosAvaliados"] == 15
    assert len(chamados) == 3


# ─────────────────────────────────────────────────────────────────────────
# Degradação (ADR-004) — nunca 500 (SC-4 herdado do Plano 01, best-effort)
# ─────────────────────────────────────────────────────────────────────────

def test_degradado_nao_derruba(cli, monkeypatch):
    # SC-4: `get_options` levanta para um ticker → 200, ticker em
    # `degradados`, itens do outro ticker presentes.
    uid, headers = _novo_escopo(cli, "07")
    _liga_operador(uid)
    _seed_carteira_padrao(uid)

    async def _fake(ticker, *a, **k):
        if ticker == "PETR4":
            raise RuntimeError("provider fora do ar")
        return _cadeia("VALE3", n_strikes=1)

    monkeypatch.setattr(options_provider, "get_options", _fake)
    r = cli.get("/api/options/curadoria", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "PETR4" in body["degradados"]
    assert any(c["ticker"] == "VALE3" for c in body["top"])


def test_cadeia_degradada_reduz_lista_sem_500(cli, monkeypatch):
    # SC-4: `providerStatus: "degraded"` numa posição → a outra ainda
    # produz itens; status HTTP 200.
    uid, headers = _novo_escopo(cli, "08")
    _liga_operador(uid)
    _seed_carteira_padrao(uid)
    chains = {
        "PETR4": _cadeia("PETR4", n_strikes=1, provider_status="degraded"),
        "VALE3": _cadeia("VALE3", n_strikes=1),
    }
    chamados, fake = _contador(chains)
    monkeypatch.setattr(options_provider, "get_options", fake)

    r = cli.get("/api/options/curadoria", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "PETR4" in body["degradados"]
    assert any(c["ticker"] == "VALE3" for c in body["top"])


# ─────────────────────────────────────────────────────────────────────────
# Ausência de IA/MCP na rota (SC-1, SC-2)
# ─────────────────────────────────────────────────────────────────────────

def test_sem_ia_na_rota(cli, monkeypatch):
    # SC-1: a resposta não carrega texto de IA; e (guardião estático) o
    # corpo de `options_curadoria` não menciona modelo de linguagem nem
    # metering.
    uid, headers = _novo_escopo(cli, "09")
    _liga_operador(uid)
    _seed_carteira_padrao(uid)
    chains = {"PETR4": _cadeia("PETR4", n_strikes=1), "VALE3": _cadeia("VALE3", n_strikes=1)}
    _, fake = _contador(chains)
    monkeypatch.setattr(options_provider, "get_options", fake)

    r = cli.get("/api/options/curadoria", headers=headers)
    body = r.json()
    assert "texto" not in body
    assert "narrativa" not in body
    assert "markdown" not in body

    import app.main as main_mod
    src = _corpo_da_funcao(main_mod.__file__, "options_curadoria")
    linhas_sem_comentario = [l for l in src.splitlines() if not l.lstrip().startswith("#")]
    blob = "\n".join(linhas_sem_comentario).lower()
    for banido in ("llm", "_gate_analise", "metering"):
        assert banido not in blob, f"{banido!r} não pode aparecer no corpo de options_curadoria"


def test_sem_mcp_na_curadoria(cli):
    # SC-2: guardião estático — nenhuma linha de código (comentários
    # filtrados) do bloco da curadoria em main.py nem de
    # opcoes_curadoria.py menciona mcp_client/options_mcp_api/mcp.semente.dev.
    import app.main as main_mod
    import app.opcoes_curadoria as curadoria_mod

    trecho_main = _corpo_da_funcao(main_mod.__file__, "_curadoria_top") + \
        _corpo_da_funcao(main_mod.__file__, "options_curadoria")
    src_curadoria = open(curadoria_mod.__file__).read()

    for blob in (trecho_main, src_curadoria):
        linhas_sem_comentario = [l for l in blob.splitlines() if not l.lstrip().startswith("#")]
        texto = "\n".join(linhas_sem_comentario)
        for marca in ("mcp_client", "options_mcp_api", "mcp.semente.dev"):
            assert marca not in texto, f"{marca!r} não pode aparecer na curadoria"


def _corpo_da_funcao(caminho_arquivo, nome_funcao):
    """Recorta o corpo textual de `nome_funcao` (de `async def`/`def` até a
    próxima definição de mesma indentação) para guardiões estáticos —
    mesmo estilo de inspeção usada nos guardiões de MCP existentes."""
    linhas = open(caminho_arquivo).read().splitlines()
    inicio = None
    for i, l in enumerate(linhas):
        if l.startswith(f"async def {nome_funcao}(") or l.startswith(f"def {nome_funcao}("):
            inicio = i
            break
    assert inicio is not None, f"função {nome_funcao!r} não encontrada em {caminho_arquivo}"
    fim = len(linhas)
    for j in range(inicio + 1, len(linhas)):
        if linhas[j] and not linhas[j][0].isspace() and not linhas[j].startswith("@"):
            fim = j
            break
    return "\n".join(linhas[inicio:fim])
