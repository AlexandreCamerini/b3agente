"""Fase 17, Plano 03 (FLOW-02/FLOW-03) — `POST /api/options/lastreada/abrir-collar`,
o caminho de ACEITE de uma trava protetora, exercitado via `TestClient`.

Estes guardiões fecham a "Limitação conhecida — guarda por autoidentificação"
que o `docs/adr/025-collar-e-estrutura-multiperna.md` deixou documentada: a
trava de 400 do Plano 16-04 (rota `/abrir`, single-leg) confia no
`tipo`/`pernasContratos` que o PRÓPRIO CLIENTE declara no corpo, sem
re-derivação server-side — aceitável enquanto nenhum cliente montava corpo
multiperna. Esta rota é exatamente esse cliente: ela NUNCA confia no corpo.
Recalcula a proposta com `opcoes_lastreadas.propor(..., multiperna=True)`
sobre posição/plano/caixa ATUAIS e cruza os `contractSymbol` submetidos
contra essa proposta fresca — os prêmios executados vêm SEMPRE da proposta
re-derivada, nunca do corpo da requisição. Apagar estes guardiões reabre a
limitação do ADR-025 e exige nota explícita.

`B3_OPTIONS_PROVIDER=mock` (via monkeypatch de env) — nunca bate na rede.
Fixtures copiadas de `test_opcoes_lastreadas_rotas.py` (padrão da casa: arquivo
de teste autocontido, não importar fixture de outro módulo de teste)."""
import datetime as dt
import inspect
import uuid

import pytest
from fastapi.testclient import TestClient

from app import candle_provider, options_provider, options_provider_mock, setups, store, technical_snapshot
from app.main import app, _conn


@pytest.fixture(autouse=True)
def _mock_provider(monkeypatch):
    monkeypatch.setenv("B3_OPTIONS_PROVIDER", "mock")
    monkeypatch.delenv("B3_OPTIONS_MOCK_STATUS", raising=False)
    yield
    monkeypatch.delenv("B3_OPTIONS_PROVIDER", raising=False)
    monkeypatch.delenv("B3_OPTIONS_MOCK_STATUS", raising=False)


@pytest.fixture
def _expiracao_fixa(monkeypatch):
    """Fixa a única expiração que o provider mock oferece em 30 dias a partir
    de hoje — dentro da janela elegível (15..60) independente da data real."""
    fixa = dt.date.today() + dt.timedelta(days=30)

    def _fake(hoje, n=3):
        return [fixa]

    monkeypatch.setattr(options_provider_mock, "_proximas_terceiras_sextas", _fake)
    return fixa.isoformat()


@pytest.fixture
def _snapshot_sem_setup(monkeypatch):
    """`plano_do_resultado` de uma lista de setups VAZIA devolve NÃO OPERAR —
    sem rede, sem candle real: `snap["setups"]`/`snap["close"]` são os dois
    únicos campos que a rota lê do retorno de `technical_snapshot.get`."""
    async def _fake_get(ticker, period, loader, interval="1d"):
        return {"setups": {"setups": []}, "close": 38.0}

    monkeypatch.setattr(technical_snapshot, "get", _fake_get)


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _novo_escopo(cli, slug):
    email = f"op-collar-{slug}-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"]["id"], {"Authorization": "Bearer " + body["token"]}


def _liga_operador(user_id):
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id=user_id)


def _seed_posicao(user_id, qty=300, price=30.0):
    store.buy(_conn, "PETR4", qty, price, user_id=user_id)


@pytest.fixture
def _plano_vender(monkeypatch):
    """Leitura técnica de VENDER (risco de queda sobre a posição) — com
    `multiperna=True` e caixa insuficiente pra put isolada, o motor propõe
    `collar`."""
    monkeypatch.setattr(setups, "plano_do_resultado", lambda *a, **k: {"decisao": "VENDER", "lado": "baixa"})


def _pernas_collar_da_cadeia(cli, ticker="PETR4"):
    """Lê a cadeia REAL do provider mock e devolve `(spot, premio_call,
    premio_put)` da MESMA régua de seleção do motor: call de menor strike
    ACIMA do spot (venda), put de maior strike ATÉ o spot (compra)."""
    r = cli.get(f"/api/options/chain/{ticker}")
    assert r.status_code == 200, r.text
    data = r.json()
    spot = data["underlyingPrice"]
    calls_acima = [c for c in data["calls"] if c["strike"] > spot]
    puts_ate = [p for p in data["puts"] if p["strike"] <= spot]
    call = min(calls_acima, key=lambda c: c["strike"])
    put = max(puts_ate, key=lambda p: p["strike"])
    return spot, float(call["lastPrice"]), float(put["lastPrice"])


def _contratos_collar_da_cadeia(cli, ticker="PETR4"):
    """Mesma seleção de `_pernas_collar_da_cadeia`, devolvendo os DOIS
    contratos inteiros (não só o prêmio) — para montar o corpo da requisição."""
    r = cli.get(f"/api/options/chain/{ticker}")
    assert r.status_code == 200, r.text
    data = r.json()
    spot = data["underlyingPrice"]
    calls_acima = [c for c in data["calls"] if c["strike"] > spot]
    puts_ate = [p for p in data["puts"] if p["strike"] <= spot]
    call = min(calls_acima, key=lambda c: c["strike"])
    put = max(puts_ate, key=lambda p: p["strike"])
    return call, put


def _outro_call(cli, ticker, excluir_symbol):
    """Um contrato de CALL real da cadeia, DIFERENTE do informado — usado
    para simular um `contractSymbol` trocado à mão que ainda existe na
    cadeia, mas não é o que a proposta re-derivada escolheria."""
    r = cli.get(f"/api/options/chain/{ticker}")
    data = r.json()
    return next(c for c in data["calls"] if c["contractSymbol"] != excluir_symbol)


def _seed_cenario_collar(cli, uid):
    """Cenário completo que dispara `motivo == "collar"`: Modo Operador +
    VENDER + posição lastreável + caixa que cabe só o débito líquido do
    collar, não a put isolada — mesma fórmula de
    `test_opcoes_lastreadas_rotas.py`."""
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)
    spot, premio_call, premio_put = _pernas_collar_da_cadeia(cli)
    cash = max(0.0, 100 * (premio_put - premio_call)) + 0.5
    assert cash < 100 * premio_put, "put isolada não pode caber no caixa"
    assert cash >= 100 * (premio_put - premio_call), "o débito líquido do collar tem que caber"
    store.put(_conn, "cash", cash, user_id=uid)
    return cash


# --------------------- POST /api/options/lastreada/abrir-collar -------------

def test_collar_em_modo_estudo_devolve_403_sem_tocar_provider(cli, monkeypatch):
    """403 ANTES de qualquer leitura de cadeia — nenhuma requisição ao
    provider é feita."""
    uid, headers = _novo_escopo(cli, "01")
    _seed_posicao(uid, qty=300)
    chamou_provider = {"v": False}

    async def _falha_se_chamado(*a, **k):
        chamou_provider["v"] = True
        raise AssertionError("options_provider.get_options não deveria ser chamado em Modo Estudo")

    monkeypatch.setattr(options_provider, "get_options", _falha_se_chamado)
    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": 1,
        "pernasContratos": [{"contractSymbol": "X", "lado": "venda"}, {"contractSymbol": "Y", "lado": "compra"}],
    })
    assert r.status_code == 403
    assert "Modo Estudo não executa ordens" in r.json()["detail"]
    assert chamou_provider["v"] is False


@pytest.mark.parametrize("pernas", [
    None,
    [],
    [{"contractSymbol": "X", "lado": "venda"}],
    [{"contractSymbol": "X", "lado": "venda"}, {"contractSymbol": "Y", "lado": "compra"},
     {"contractSymbol": "Z", "lado": "venda"}],
])
def test_collar_recusa_corpo_sem_exatamente_duas_pernas(cli, pernas):
    uid, headers = _novo_escopo(cli, "02")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    opts_antes = store.get(_conn, "optionPositions", user_id=uid)
    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": 1, "pernasContratos": pernas,
    })
    assert r.status_code == 400
    assert "Collar exige exatamente duas pernas." in r.json()["detail"]
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    assert store.get(_conn, "optionPositions", user_id=uid) == opts_antes


def test_collar_aceito_com_proposta_fresca_executa_as_duas_pernas(cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    uid, headers = _novo_escopo(cli, "03")
    _seed_cenario_collar(cli, uid)
    p_resp = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers)
    assert p_resp.status_code == 200
    p = p_resp.json()["proposta"]
    assert p is not None and p["tipo"] == "collar"

    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"],
        "pernasContratos": [{"contractSymbol": perna["contractSymbol"], "lado": perna["lado"]}
                             for perna in p["pernasContratos"]],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    opts = body["optionPositions"]
    assert len(opts) == 2
    lados = {o["id"]: o["side"] for o in opts}
    assert lados[p["pernasContratos"][0]["contractSymbol"]] == "vendida"
    assert lados[p["pernasContratos"][1]["contractSymbol"]] == "comprada"
    pos_petr4 = next(pp for pp in body["positions"] if pp["t"] == "PETR4")
    assert pos_petr4["qtyTravada"] == p["contratos"] * 100  # travado UMA vez


def test_collar_indisponivel_agora_devolve_409_sem_efeito_colateral(cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    """Cenário em que a leitura FRESCA do motor não propõe collar (caixa
    folgado o bastante pra put isolada caber sozinha) — 409, estado
    inalterado."""
    uid, headers = _novo_escopo(cli, "04")
    _liga_operador(uid)
    _seed_posicao(uid, qty=300)
    spot, premio_call, premio_put = _pernas_collar_da_cadeia(cli)
    store.put(_conn, "cash", 100 * premio_put + 1000.0, user_id=uid)  # caixa de sobra
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    opts_antes = store.get(_conn, "optionPositions", user_id=uid)

    p_check = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()
    assert p_check["motivo"] == "put_protecao"  # confirma a premissa do cenário

    call, put = _contratos_collar_da_cadeia(cli)
    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": 1,
        "pernasContratos": [{"contractSymbol": call["contractSymbol"], "lado": "venda"},
                             {"contractSymbol": put["contractSymbol"], "lado": "compra"}],
    })
    assert r.status_code == 409
    assert "não está mais disponível" in r.json()["detail"]
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    assert store.get(_conn, "optionPositions", user_id=uid) == opts_antes


def test_collar_contrato_trocado_devolve_409_sem_efeito_colateral(cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    uid, headers = _novo_escopo(cli, "05")
    _seed_cenario_collar(cli, uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    opts_antes = store.get(_conn, "optionPositions", user_id=uid)

    p = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()["proposta"]
    call_esperada = p["pernasContratos"][0]["contractSymbol"]
    call_trocada = _outro_call(cli, "PETR4", call_esperada)

    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"],
        "pernasContratos": [{"contractSymbol": call_trocada["contractSymbol"], "lado": "venda"},
                             {"contractSymbol": p["pernasContratos"][1]["contractSymbol"], "lado": "compra"}],
    })
    assert r.status_code == 409
    assert "não conferem com a proposta recalculada" in r.json()["detail"]
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    assert store.get(_conn, "optionPositions", user_id=uid) == opts_antes


def test_collar_lado_trocado_devolve_409_sem_efeito_colateral(cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    uid, headers = _novo_escopo(cli, "06")
    _seed_cenario_collar(cli, uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    opts_antes = store.get(_conn, "optionPositions", user_id=uid)

    p = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()["proposta"]
    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"],
        "pernasContratos": [
            {"contractSymbol": p["pernasContratos"][0]["contractSymbol"], "lado": "compra"},  # trocado
            {"contractSymbol": p["pernasContratos"][1]["contractSymbol"], "lado": "venda"},   # trocado
        ],
    })
    assert r.status_code == 409
    assert "não conferem com a proposta recalculada" in r.json()["detail"]
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    assert store.get(_conn, "optionPositions", user_id=uid) == opts_antes


def test_collar_quantidade_divergente_devolve_409_sem_efeito_colateral(cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    uid, headers = _novo_escopo(cli, "07")
    _seed_cenario_collar(cli, uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    opts_antes = store.get(_conn, "optionPositions", user_id=uid)

    p = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()["proposta"]
    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"] + 1,
        "pernasContratos": [{"contractSymbol": perna["contractSymbol"], "lado": perna["lado"]}
                             for perna in p["pernasContratos"]],
    })
    assert r.status_code == 409
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    assert store.get(_conn, "optionPositions", user_id=uid) == opts_antes


def test_collar_ignora_premio_do_corpo_e_usa_o_do_servidor(cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    """Corpo com prêmios absurdos declarados junto às pernas — o `cash`
    final bate com os prêmios REAIS do provider mock, nunca com o corpo."""
    uid, headers = _novo_escopo(cli, "08")
    _seed_cenario_collar(cli, uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)

    p = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()["proposta"]
    premio_call_real = p["pernasContratos"][0]["premioUnitario"]
    premio_put_real = p["pernasContratos"][1]["premioUnitario"]
    custo_liquido_real = round(p["contratos"] * 100 * (premio_put_real - premio_call_real), 2)

    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"],
        "pernasContratos": [
            {"contractSymbol": p["pernasContratos"][0]["contractSymbol"], "lado": "venda", "premioUnitario": 999.0},
            {"contractSymbol": p["pernasContratos"][1]["contractSymbol"], "lado": "compra", "premioUnitario": 0.01},
        ],
    })
    assert r.status_code == 200, r.text
    cash_depois = store.get(_conn, "cash", user_id=uid)
    assert round(caixa_antes - cash_depois, 2) == custo_liquido_real


def test_collar_com_cadeia_degradada_devolve_502(cli, monkeypatch):
    uid, headers = _novo_escopo(cli, "09")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    opts_antes = store.get(_conn, "optionPositions", user_id=uid)
    monkeypatch.setenv("B3_OPTIONS_MOCK_STATUS", "degraded")
    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": 1,
        "pernasContratos": [{"contractSymbol": "X", "lado": "venda"}, {"contractSymbol": "Y", "lado": "compra"}],
    })
    assert r.status_code == 502
    assert "Cotação de opções indisponível" in r.json()["detail"]
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    assert store.get(_conn, "optionPositions", user_id=uid) == opts_antes


def test_collar_valueerror_do_motor_vira_400(cli, monkeypatch, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    """Simula caixa consumido por outra requisição ENTRE a re-derivação e a
    execução: `store.abrir_collar` levanta `ValueError`, a rota converte em
    400 com a mensagem do motor — sem esconder o motivo real."""
    uid, headers = _novo_escopo(cli, "10")
    _seed_cenario_collar(cli, uid)
    p = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()["proposta"]

    def _falha(*a, **k):
        raise ValueError("Caixa insuficiente para o collar.")

    monkeypatch.setattr(store, "abrir_collar", _falha)
    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"],
        "pernasContratos": [{"contractSymbol": perna["contractSymbol"], "lado": perna["lado"]}
                             for perna in p["pernasContratos"]],
    })
    assert r.status_code == 400
    assert "Caixa insuficiente para o collar." in r.json()["detail"]


# ------------------- Task 2: hardening e não-regressão da trava de 16-04 -----

def test_rota_de_collar_nao_le_multiperna_do_corpo():
    """A capacidade `multiperna` não é negociável pelo cliente numa rota de
    ESCRITA — só a rota de LEITURA (`GET .../proposta`) negocia isso."""
    from app import main
    fonte = inspect.getsource(main.options_lastreada_abrir_collar)
    assert "multiperna=True" in fonte
    assert 'body.get("multiperna"' not in fonte
    assert "body.get('multiperna'" not in fonte


def test_rota_de_collar_nao_usa_premio_do_corpo(cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    """Inspeção de fonte (a rota não lê prêmio do corpo) + comportamento (um
    corpo com `premioUnitario` absurdo executa com os prêmios do provider
    mock, não com o valor declarado) — as duas metades da mesma garantia."""
    from app import main
    fonte = inspect.getsource(main.options_lastreada_abrir_collar)
    assert 'body.get("premio' not in fonte

    uid, headers = _novo_escopo(cli, "13")
    _seed_cenario_collar(cli, uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    p = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()["proposta"]
    premio_call_real = p["pernasContratos"][0]["premioUnitario"]
    premio_put_real = p["pernasContratos"][1]["premioUnitario"]
    custo_liquido_real = round(p["contratos"] * 100 * (premio_put_real - premio_call_real), 2)

    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"],
        "pernasContratos": [
            {"contractSymbol": p["pernasContratos"][0]["contractSymbol"], "lado": "venda", "premioUnitario": 999.0},
            {"contractSymbol": p["pernasContratos"][1]["contractSymbol"], "lado": "compra", "premioUnitario": 0.01},
        ],
    })
    assert r.status_code == 200, r.text
    cash_depois = store.get(_conn, "cash", user_id=uid)
    assert round(caixa_antes - cash_depois, 2) == custo_liquido_real


def test_rota_antiga_continua_recusando_collar_apos_a_fase_17(cli):
    """Esta fase abre um caminho NOVO, não afrouxa o antigo — `/abrir`
    continua executando uma perna por chamada, e a trava é o que impede o
    vácuo de virar execução parcial silenciosa."""
    uid, headers = _novo_escopo(cli, "11")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    opts_antes = store.get(_conn, "optionPositions", user_id=uid)
    call, put = _contratos_collar_da_cadeia(cli)

    r1 = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "tipo": "collar", "contratos": 1,
        "pernasContratos": [call["contractSymbol"], put["contractSymbol"]],
    })
    assert r1.status_code == 400
    assert "mais de uma perna" in r1.json()["detail"]

    r2 = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contratos": 1,
        "pernasContratos": [call["contractSymbol"], put["contractSymbol"]],
    })
    assert r2.status_code == 400
    assert "mais de uma perna" in r2.json()["detail"]
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    assert store.get(_conn, "optionPositions", user_id=uid) == opts_antes


def test_meia_estrutura_e_impossivel_pela_rota_nova(cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    uid, headers = _novo_escopo(cli, "12")
    _seed_cenario_collar(cli, uid)
    p = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers).json()["proposta"]
    r = cli.post("/api/options/lastreada/abrir-collar", headers=headers, json={
        "underlying": "PETR4", "contratos": p["contratos"],
        "pernasContratos": [{"contractSymbol": p["pernasContratos"][0]["contractSymbol"], "lado": "venda"}],
    })
    assert r.status_code == 400
    assert "Collar exige exatamente duas pernas." in r.json()["detail"]
    assert store.get(_conn, "optionPositions", user_id=uid) == []
