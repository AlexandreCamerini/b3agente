"""Quick 260908-ldg (2026-09-08) — Task 2: gate de descoberta em três faixas
(`GET /api/options/gate/{ticker}`), recusas do servidor nas duas rotas de
abertura (`/abrir`, `/abrir-collar`) e o guardião estrutural do agente
autônomo (D-08: nenhum caminho automático abre estrutura de opção).

`options_provider.get_options`/`options_api.get_options` são monkeypatchados
diretamente com cadeias sintéticas — não usamos `B3_OPTIONS_PROVIDER=mock`
aqui porque o mock gera volume fixo (5000, sempre NEGOCIÁVEL); estes testes
precisam controlar a faixa exata de cada contrato."""
import ast
import datetime as dt
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import opcoes_lastreadas, options_api, options_provider, options_provider_mock, setups, store, technical_snapshot
from app.main import app, _conn

_EXP = "2026-10-30"  # dentro da janela elegível de `opcoes_lastreadas.propor` a partir de qualquer `_HOJE` de teste


def _contrato(symbol, kind, strike, price=1.0, volume=5000, oi=None, bid=None, ask=None):
    return {"contractSymbol": symbol, "optionType": kind, "strike": strike, "lastPrice": price,
            "bid": bid, "ask": ask, "volume": volume, "openInterest": oi,
            "impliedVolatility": 0.3, "expiration": _EXP}


def _chain(calls=None, puts=None, status="ok"):
    return {"providerStatus": status, "underlyingPrice": 30.0, "expiration": _EXP,
            "expirations": [_EXP], "calls": calls or [], "puts": puts or []}


def _fake_get_options(chain):
    async def _f(*a, **k):
        return chain
    return _f


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _novo_escopo(cli, slug):
    email = f"gate-ldg-{slug}-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"]["id"], {"Authorization": "Bearer " + body["token"]}


def _liga_operador(user_id):
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id=user_id)


def _seed_posicao(user_id, ticker="PETR4", qty=300, price=30.0):
    store.buy(_conn, ticker, qty, price, user_id=user_id)


# ─────────────────────────────────────────────────────────────────────────
# GET /api/options/gate/{ticker}
# ─────────────────────────────────────────────────────────────────────────

def test_gate_melhor_contrato_negociavel(cli, monkeypatch):
    call = _contrato("ABEVI147W2", "call", 32.0, volume=21100, bid=1.04, ask=0.0)  # 66,5
    monkeypatch.setattr(options_api, "get_options", _fake_get_options(_chain(calls=[call])))
    r = cli.get("/api/options/gate/PETR4")
    assert r.status_code == 200
    body = r.json()
    assert body["liquida"] is True
    assert body["faixa"] == "NEGOCIÁVEL"
    assert body["melhorScore"] == 66.5


def test_gate_melhor_contrato_dificil_ainda_liquida_true_compat(cli, monkeypatch):
    call = _contrato("ABEVI165W2", "call", 32.0, volume=2000, bid=None, ask=None)  # 46,0
    monkeypatch.setattr(options_api, "get_options", _fake_get_options(_chain(calls=[call])))
    r = cli.get("/api/options/gate/PETR4")
    assert r.status_code == 200
    body = r.json()
    assert body["liquida"] is True  # compat: todo consumidor de opGate.liquida continua vendo true
    assert body["faixa"] == "DIFÍCIL"
    assert body["melhorScore"] == 46.0


def test_gate_melhor_contrato_sem_mercado_liquida_false(cli, monkeypatch):
    call = _contrato("B3SAI167W2", "call", 32.0, volume=300, bid=None, ask=None)  # 29,6
    monkeypatch.setattr(options_api, "get_options", _fake_get_options(_chain(calls=[call])))
    r = cli.get("/api/options/gate/PETR4")
    assert r.status_code == 200
    body = r.json()
    assert body["liquida"] is False
    assert body["faixa"] == "SEM MERCADO"
    assert body["melhorScore"] == 29.6


def test_gate_cadeia_vazia_faixa_sem_mercado_score_none_nunca_zero(cli, monkeypatch):
    monkeypatch.setattr(options_api, "get_options", _fake_get_options(_chain()))
    r = cli.get("/api/options/gate/PETR4")
    body = r.json()
    assert body["liquida"] is False
    assert body["faixa"] == "SEM MERCADO"
    assert body["melhorScore"] is None


def test_gate_cadeia_degradada_faixa_sem_mercado_score_none(cli, monkeypatch):
    monkeypatch.setattr(options_api, "get_options", _fake_get_options(_chain(status="degraded")))
    r = cli.get("/api/options/gate/PETR4")
    body = r.json()
    assert body["liquida"] is False
    assert body["faixa"] == "SEM MERCADO"
    assert body["melhorScore"] is None


def test_gate_quote_unavailable_faixa_sem_mercado_score_none(cli, monkeypatch):
    from app import yahoo

    async def _falha(*a, **k):
        raise yahoo.QuoteUnavailable("indisponível")

    monkeypatch.setattr(options_api, "get_options", _falha)
    r = cli.get("/api/options/gate/PETR4")
    body = r.json()
    assert body["liquida"] is False
    assert body["providerStatus"] == "degraded"
    assert body["faixa"] == "SEM MERCADO"
    assert body["melhorScore"] is None


# ─────────────────────────────────────────────────────────────────────────
# POST /api/options/lastreada/abrir
# ─────────────────────────────────────────────────────────────────────────

def _abrir_body(contrato, aceita=None):
    body = {"underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 3,
            "expiration": contrato["expiration"]}
    if aceita is not None:
        body["aceitaLiquidezDificil"] = aceita
    return body


def test_abrir_negociavel_sem_flag_executa(cli, monkeypatch):
    call = _contrato("ABEVI147W2", "call", 32.0, price=1.0, volume=21100, bid=1.04, ask=0.0)  # 66,5
    uid, headers = _novo_escopo(cli, "01")
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)
    monkeypatch.setattr(options_provider, "get_options", _fake_get_options(_chain(calls=[call])))
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json=_abrir_body(call))
    assert r.status_code == 200, r.text


def test_abrir_negociavel_com_flag_true_executa_igual_flag_redundante(cli, monkeypatch):
    call = _contrato("ABEVI147W2", "call", 32.0, price=1.0, volume=21100, bid=1.04, ask=0.0)
    uid, headers = _novo_escopo(cli, "02")
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)
    monkeypatch.setattr(options_provider, "get_options", _fake_get_options(_chain(calls=[call])))
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json=_abrir_body(call, aceita=True))
    assert r.status_code == 200, r.text


def test_abrir_dificil_sem_flag_400_nomeia_faixa(cli, monkeypatch):
    call = _contrato("ABEVI165W2", "call", 32.0, price=1.0, volume=2000, bid=None, ask=None)  # 46,0
    uid, headers = _novo_escopo(cli, "03")
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)
    monkeypatch.setattr(options_provider, "get_options", _fake_get_options(_chain(calls=[call])))
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json=_abrir_body(call))
    assert r.status_code == 400
    assert "DIFÍCIL" in r.json()["detail"]
    assert "confirmação" in r.json()["detail"].lower() or "aceitaLiquidezDificil" in r.json()["detail"]


def test_abrir_dificil_com_flag_true_executa(cli, monkeypatch):
    call = _contrato("ABEVI165W2", "call", 32.0, price=1.0, volume=2000, bid=None, ask=None)  # 46,0
    uid, headers = _novo_escopo(cli, "04")
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)
    monkeypatch.setattr(options_provider, "get_options", _fake_get_options(_chain(calls=[call])))
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json=_abrir_body(call, aceita=True))
    assert r.status_code == 200, r.text


def test_abrir_sem_mercado_com_flag_true_400_mensagem_distinta_da_dificil(cli, monkeypatch):
    call = _contrato("B3SAI167W2", "call", 32.0, price=1.0, volume=300, bid=None, ask=None)  # 29,6
    uid, headers = _novo_escopo(cli, "05")
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)
    monkeypatch.setattr(options_provider, "get_options", _fake_get_options(_chain(calls=[call])))
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json=_abrir_body(call, aceita=True))
    assert r.status_code == 400
    detalhe = r.json()["detail"]
    assert "SEM MERCADO" in detalhe
    assert "DIFÍCIL" not in detalhe  # mensagem distinta da recusa de DIFÍCIL


@pytest.mark.parametrize("flag_invalida", ["false", 1, "sim"])
def test_abrir_dificil_flag_nao_booleana_nao_destrava_por_identidade(cli, monkeypatch, flag_invalida):
    call = _contrato("ABEVI165W2", "call", 32.0, price=1.0, volume=2000, bid=None, ask=None)  # 46,0
    uid, headers = _novo_escopo(cli, "06-" + str(flag_invalida))
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)
    monkeypatch.setattr(options_provider, "get_options", _fake_get_options(_chain(calls=[call])))
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json=_abrir_body(call, aceita=flag_invalida))
    assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────
# POST /api/options/lastreada/fechar — NENHUMA trava de faixa na saída
# ─────────────────────────────────────────────────────────────────────────

def test_fechar_contrato_sem_mercado_continua_fechando(cli, monkeypatch):
    """Assimetria deliberada abrir×fechar (Resolução #4 do orquestrador):
    travar a saída de um contrato ruim prenderia o usuário exatamente onde
    ele mais precisa sair."""
    call_abertura = _contrato("PETRZZZ", "call", 32.0, price=1.0, volume=21100, bid=1.04, ask=0.0)
    uid, headers = _novo_escopo(cli, "07")
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)
    monkeypatch.setattr(options_provider, "get_options", _fake_get_options(_chain(calls=[call_abertura])))
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json=_abrir_body(call_abertura))
    assert r.status_code == 200, r.text

    # Recotação: o MESMO contrato agora está SEM MERCADO (score 20,1).
    call_fechamento = _contrato("PETRZZZ", "call", 32.0, price=1.2, volume=100, bid=None, ask=None)
    monkeypatch.setattr(options_provider, "get_options", _fake_get_options(_chain(calls=[call_fechamento])))
    r = cli.post("/api/options/lastreada/fechar", headers=headers,
                  json={"contractSymbol": "PETRZZZ", "contratos": 3})
    assert r.status_code == 200, r.text


# ─────────────────────────────────────────────────────────────────────────
# POST /api/options/lastreada/abrir-collar — as MESMAS quatro regras, lendo
# a faixa da PROPOSTA RE-DERIVADA (`p["liquidez"]["faixa"]`), nunca do corpo.
# `B3_OPTIONS_PROVIDER=mock` real aqui (não cadeia sintética) — precisamos do
# pipeline completo de `propor(multiperna=True)` re-derivando no servidor.
# ─────────────────────────────────────────────────────────────────────────

@pytest.fixture
def _mock_provider_collar(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "mock")
    monkeypatch.delenv("B3_OPTIONS_MOCK_STATUS", raising=False)
    yield
    monkeypatch.delenv("B3_OPTIONS_PROVIDER", raising=False)
    monkeypatch.delenv("B3_OPTIONS_MOCK_STATUS", raising=False)


@pytest.fixture
def _expiracao_fixa_collar(monkeypatch):
    fixa = dt.date.today() + dt.timedelta(days=30)

    def _fake(hoje, n=3):
        return [fixa]

    monkeypatch.setattr(options_provider_mock, "_proximas_terceiras_sextas", _fake)
    return fixa.isoformat()


@pytest.fixture
def _snapshot_sem_setup_collar(monkeypatch):
    async def _fake_get(ticker, period, loader, interval="1d"):
        return {"setups": {"setups": []}, "close": 38.0}

    monkeypatch.setattr(technical_snapshot, "get", _fake_get)


@pytest.fixture
def _plano_vender_collar(monkeypatch):
    monkeypatch.setattr(setups, "plano_do_resultado", lambda *a, **k: {"decisao": "VENDER", "lado": "baixa"})


def _pernas_collar_da_cadeia_ldg(cli, ticker="PETR4"):
    r = cli.get(f"/api/options/chain/{ticker}")
    assert r.status_code == 200, r.text
    data = r.json()
    spot = data["underlyingPrice"]
    calls_acima = [c for c in data["calls"] if c["strike"] > spot]
    puts_ate = [p for p in data["puts"] if p["strike"] <= spot]
    call = min(calls_acima, key=lambda c: c["strike"])
    put = max(puts_ate, key=lambda p: p["strike"])
    return call, put, float(call["lastPrice"]), float(put["lastPrice"])


def test_abrir_collar_dificil_sem_flag_400_nomeia_faixa(
        cli, monkeypatch, _mock_provider_collar, _expiracao_fixa_collar,
        _snapshot_sem_setup_collar, _plano_vender_collar):
    monkeypatch.setattr(options_provider_mock, "MOCK_VOLUME", 1500)  # ambas as pernas ~50,5 = DIFÍCIL
    uid, headers = _novo_escopo(cli, "collar-01")
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id=uid)
    store.buy(_conn, "PETR4", 300, 30.0, user_id=uid)
    call, put, premio_call, premio_put = _pernas_collar_da_cadeia_ldg(cli)
    cash = max(0.0, 100 * (premio_put - premio_call)) + 0.5
    store.put(_conn, "cash", cash, user_id=uid)

    p = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()["proposta"]
    assert p["tipo"] == "collar"
    assert p["liquidez"]["faixa"] == "DIFÍCIL"

    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"],
        "pernasContratos": [{"contractSymbol": perna["contractSymbol"], "lado": perna["lado"]}
                             for perna in p["pernasContratos"]],
    })
    assert r.status_code == 400
    assert "DIFÍCIL" in r.json()["detail"]


def test_abrir_collar_dificil_com_flag_true_executa(
        cli, monkeypatch, _mock_provider_collar, _expiracao_fixa_collar,
        _snapshot_sem_setup_collar, _plano_vender_collar):
    monkeypatch.setattr(options_provider_mock, "MOCK_VOLUME", 1500)
    uid, headers = _novo_escopo(cli, "collar-02")
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id=uid)
    store.buy(_conn, "PETR4", 300, 30.0, user_id=uid)
    call, put, premio_call, premio_put = _pernas_collar_da_cadeia_ldg(cli)
    cash = max(0.0, 100 * (premio_put - premio_call)) + 0.5
    store.put(_conn, "cash", cash, user_id=uid)

    p = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()["proposta"]
    assert p["liquidez"]["faixa"] == "DIFÍCIL"

    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"], "aceitaLiquidezDificil": True,
        "pernasContratos": [{"contractSymbol": perna["contractSymbol"], "lado": perna["lado"]}
                             for perna in p["pernasContratos"]],
    })
    assert r.status_code == 200, r.text


def test_abrir_collar_negociavel_ignora_flag_do_corpo(
        cli, monkeypatch, _mock_provider_collar, _expiracao_fixa_collar,
        _snapshot_sem_setup_collar, _plano_vender_collar):
    """Default do mock (volume 5000) dá NEGOCIÁVEL nas duas pernas — a flag,
    quando presente, é ignorada (não é erro nem é necessária)."""
    uid, headers = _novo_escopo(cli, "collar-03")
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id=uid)
    store.buy(_conn, "PETR4", 300, 30.0, user_id=uid)
    call, put, premio_call, premio_put = _pernas_collar_da_cadeia_ldg(cli)
    cash = max(0.0, 100 * (premio_put - premio_call)) + 0.5
    store.put(_conn, "cash", cash, user_id=uid)

    p = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()["proposta"]
    assert p["liquidez"]["faixa"] == "NEGOCIÁVEL"

    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"], "aceitaLiquidezDificil": True,
        "pernasContratos": [{"contractSymbol": perna["contractSymbol"], "lado": perna["lado"]}
                             for perna in p["pernasContratos"]],
    })
    assert r.status_code == 200, r.text


def test_abrir_collar_sem_mercado_400_incondicional_mesmo_com_flag(cli, monkeypatch):
    """DEFENSIVO: `rastrear()` (duas passadas) garante que `propor()` nunca
    seleciona uma perna SEM MERCADO — o collar real nunca chega nesta faixa
    hoje. Este teste isola a regra da PRÓPRIA ROTA (não do motor),
    monkeypatchando `opcoes_lastreadas.propor` para devolver um candidato
    collar fabricado com `liquidez.faixa == "SEM MERCADO"`: prova que a
    rota recusa incondicionalmente mesmo que uma mudança futura no motor
    algum dia produza esse caso."""
    uid, headers = _novo_escopo(cli, "collar-04")
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id=uid)
    store.buy(_conn, "PETR4", 300, 30.0, user_id=uid)

    chain_fake = _chain(
        calls=[_contrato("FAKE_CALL", "call", 32.0, price=1.0, volume=100)],
        puts=[_contrato("FAKE_PUT", "put", 28.0, price=0.9, volume=100)],
    )
    chain_fake["underlyingPrice"] = 30.0
    monkeypatch.setattr(options_provider, "get_options", _fake_get_options(chain_fake))

    candidato_fake = {
        "tipo": "collar", "contratos": 1,
        "pernasContratos": [
            {"contractSymbol": "FAKE_CALL", "optionType": "call", "lado": "venda",
             "strike": 32.0, "premioUnitario": 1.0},
            {"contractSymbol": "FAKE_PUT", "optionType": "put", "lado": "compra",
             "strike": 28.0, "premioUnitario": 0.9},
        ],
        "liquidez": {"score": 10.0, "faixa": "SEM MERCADO", "volume": 100, "spreadPct": None, "aviso": None},
    }
    monkeypatch.setattr(opcoes_lastreadas, "propor",
                         lambda *a, **k: {"proposta": candidato_fake, "motivo": "collar",
                                           "candidatos": [candidato_fake]})

    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": 1, "aceitaLiquidezDificil": True,
        "pernasContratos": [{"contractSymbol": "FAKE_CALL", "lado": "venda"},
                             {"contractSymbol": "FAKE_PUT", "lado": "compra"}],
    })
    assert r.status_code == 400
    assert "SEM MERCADO" in r.json()["detail"]


# ─────────────────────────────────────────────────────────────────────────
# Guardião estrutural (D-08): agente autônomo não abre estrutura de opção
# ─────────────────────────────────────────────────────────────────────────

_FUNCOES_DE_ABERTURA = ("abrir_call_coberta", "comprar_put_protecao", "abrir_collar")


def test_agent_nao_chama_nenhuma_funcao_de_abertura_de_opcao():
    """Prova por AST, não por leitura: hoje o agente só LIQUIDA vencidas
    (`liquidar_lastreada_vencida`, `agent.py`). Sem humano para consentir em
    liquidez DIFÍCIL, nenhum caminho automático pode abrir estrutura —
    registrar isso como guardião impede que um caminho automático apareça
    depois sem essa decisão de produto ser revisitada."""
    caminho = Path(__file__).resolve().parent.parent / "app" / "agent.py"
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    chamadas = []
    for node in ast.walk(arvore):
        if isinstance(node, ast.Call):
            alvo = node.func
            nome = alvo.attr if isinstance(alvo, ast.Attribute) else (
                alvo.id if isinstance(alvo, ast.Name) else None)
            if nome:
                chamadas.append(nome)
    for proibida in _FUNCOES_DE_ABERTURA:
        assert proibida not in chamadas, f"agent.py chama {proibida} — caminho automático de abertura"
