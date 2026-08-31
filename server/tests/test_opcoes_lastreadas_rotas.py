"""Fase 14, Plano 03 — as TRÊS rotas HTTP das operações lastreadas, exercitadas
de verdade via `TestClient` (o motor puro já está coberto em
`test_opcoes_lastreadas_proposta.py`; aqui é o fio elétrico: normalização de
ticker, trava de Modo Estudo no SERVIDOR, bloqueio ADR-004, e o público
`public_state` de volta pro chamador).

`B3_OPTIONS_PROVIDER=mock` (via monkeypatch de env) — nunca bate na rede.
`_expiracao_fixa` pina o calendário do provider mock (que por desenho escolhe
a terceira-sexta MAIS PRÓXIMA de "hoje" real) para dentro da janela elegível
de `opcoes_lastreadas.propor` (15..60 dias) — sem isso, o teste da proposta
completa ficaria dependente do dia real em que a suíte roda (a terceira-sexta
mais próxima fica <15 dias de distância por ~2 semanas a cada ciclo mensal).
`_snapshot_sem_setup` substitui `technical_snapshot.get` por um snapshot
sintético determinístico (sem candle real, sem rede) — mesma razão."""
import datetime as dt
import uuid

import pytest
from fastapi.testclient import TestClient

from app import options_provider_mock, pregao, store, technical_snapshot
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
    o motor propõe call_coberta (sem alta a preservar). Sem rede, sem candle
    real: `snap["setups"]`/`snap["close"]` são os dois únicos campos que a
    rota lê do retorno de `technical_snapshot.get`."""
    async def _fake_get(ticker, period, loader, interval="1d"):
        return {"setups": {"setups": []}, "close": 38.0}

    monkeypatch.setattr(technical_snapshot, "get", _fake_get)


@pytest.fixture
def cli():
    with TestClient(app) as c:
        yield c


def _novo_escopo(cli, slug):
    # e-mail único por CHAMADA (não só por teste) — o `_conn` deste processo
    # persiste no `B3_DB_PATH` do worktree entre execuções da suíte; um
    # e-mail fixo colidiria com "já existe uma conta" na segunda rodada local.
    email = f"op-lastr-{slug}-{uuid.uuid4().hex[:10]}@teste.com"
    r = cli.post("/api/auth/register", json={"email": email, "password": "senhaboa123"})
    assert r.status_code == 200, r.text
    body = r.json()
    return body["user"]["id"], {"Authorization": "Bearer " + body["token"]}


def _liga_operador(user_id):
    # Ativar "operador" exige o termo aceito no MESMO patch (Fase 7, F7.1) —
    # mesma disciplina de test_agent_options.py.
    store.set_config(_conn, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id=user_id)


def _seed_posicao(user_id, qty=300, price=30.0):
    store.buy(_conn, "PETR4", qty, price, user_id=user_id)


# --------------------------- GET /api/options/proposta ----------------------

def test_proposta_sem_posicao_devolve_sem_lastro_com_motivo_texto(cli):
    uid, headers = _novo_escopo(cli, "01")
    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["proposta"] is None
    assert body["motivo"] == "sem_lastro"
    assert body["motivoTexto"] and "PETR4" in body["motivoTexto"]


def test_proposta_com_posicao_devolve_contratos(cli, _expiracao_fixa, _snapshot_sem_setup):
    uid, headers = _novo_escopo(cli, "02")
    _seed_posicao(uid, qty=300)
    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["proposta"] is not None, body
    assert body["proposta"]["contratos"] >= 1
    assert body["motivo"] == "call_coberta"


def test_proposta_nunca_cai_em_500_mesmo_sem_posicao_e_sem_cadeia(cli):
    """Sem posição E sem cadeia (env sem mock, default yahoo real sem rede
    no ambiente de teste) — a rota permanece 200, nunca 500."""
    import os
    os.environ.pop("B3_OPTIONS_PROVIDER", None)
    uid, headers = _novo_escopo(cli, "03")
    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200


# --------------------------- POST .../lastreada/abrir ------------------------

def _contract_symbol(cli, tipo="call"):
    """PETR4 no provider mock tem 9 strikes; pega um contrato do tipo pedido."""
    r = cli.get("/api/options/chain/PETR4")
    if r.status_code != 200:
        return None
    data = r.json()
    lista = data.get("calls" if tipo == "call" else "puts") or []
    return lista[0] if lista else None


def test_abrir_em_modo_estudo_devolve_403_e_nao_muda_caixa(cli):
    uid, headers = _novo_escopo(cli, "04")
    _seed_posicao(uid, qty=300)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    contrato = _contract_symbol(cli, "call")
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 1,
    })
    assert r.status_code == 403
    assert "Modo Estudo não executa ordens" in r.json()["detail"]
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes


def test_abrir_em_modo_operador_credita_premio_e_trava_acoes(cli):
    uid, headers = _novo_escopo(cli, "05")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    contrato = _contract_symbol(cli, "call")
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 1,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["priceUsed"] == contrato["lastPrice"]
    assert store.get(_conn, "cash", user_id=uid) > caixa_antes  # prêmio creditado
    pos_petr4 = next(p for p in body["positions"] if p["t"] == "PETR4")
    assert pos_petr4["qtyTravada"] == 100


def test_abrir_com_provedor_degradado_devolve_502_e_nao_muda_estado(cli, monkeypatch):
    uid, headers = _novo_escopo(cli, "06")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    positions_antes = store.get(_conn, "positions", user_id=uid)
    monkeypatch.setenv("B3_OPTIONS_MOCK_STATUS", "degraded")
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": "PETR4MOCK01C", "contratos": 1,
    })
    assert r.status_code == 502
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    assert store.get(_conn, "positions", user_id=uid) == positions_antes


def test_abrir_mais_contratos_do_que_o_lastro_permite_devolve_400(cli):
    uid, headers = _novo_escopo(cli, "07")
    _seed_posicao(uid, qty=100)  # só 1 contrato de lastro livre
    _liga_operador(uid)
    contrato = _contract_symbol(cli, "call")
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 5,
    })
    assert r.status_code == 400


# --------------------------- POST .../lastreada/fechar ------------------------

# --------------------------- POST /api/sell + trava --------------------------

def test_vender_posicao_100_por_cento_travada_via_sell_devolve_400(cli, monkeypatch):
    """Achado da verificação ponta a ponta do 14-08 (Rule 1): `store.sell`
    já recusava e gravava a rejeição no histórico quando `qty_livre(pos) <= 0`
    (test_lastro_trava.py cobre a camada de motor), mas a ROTA `/api/sell` não
    checava o retorno `None` e devolvia 200 silencioso — sem o 400 explícito
    que toda outra rejeição desta mesma rota (sem posição, quantidade
    inválida) já usa. Este teste trava o contrato HTTP que faltava."""
    monkeypatch.setattr(pregao, "in_market_hours", lambda now=None: True)
    uid, headers = _novo_escopo(cli, "09")
    _seed_posicao(uid, qty=100)  # exatamente 1 contrato de lastro, sem sobra
    _liga_operador(uid)
    contrato = _contract_symbol(cli, "call")
    r_abrir = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 1,
    })
    assert r_abrir.status_code == 200, r_abrir.text
    assert r_abrir.json()["positions"][0]["qtyTravada"] == 100  # 100% travado

    caixa_antes = store.get(_conn, "cash", user_id=uid)
    r_vender = cli.post("/api/sell", headers=headers, json={"t": "PETR4"})
    assert r_vender.status_code == 400
    assert "travadas" in r_vender.json()["detail"]
    # posição intocada pela tentativa recusada — nem caixa nem qtyTravada mudam
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    pos_petr4 = next(p for p in store.get(_conn, "positions", user_id=uid) if p["t"] == "PETR4")
    assert pos_petr4["qtyTravada"] == 100


def test_fechar_devolve_caixa_e_destrava(cli):
    uid, headers = _novo_escopo(cli, "08")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    contrato = _contract_symbol(cli, "call")
    r_abrir = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 1,
    })
    assert r_abrir.status_code == 200, r_abrir.text
    caixa_apos_abrir = store.get(_conn, "cash", user_id=uid)

    r_fechar = cli.post("/api/options/lastreada/fechar", headers=headers, json={
        "contractSymbol": contrato["contractSymbol"], "contratos": 1,
    })
    assert r_fechar.status_code == 200, r_fechar.text
    body = r_fechar.json()
    assert store.get(_conn, "cash", user_id=uid) != caixa_apos_abrir  # recompra debitou
    pos_petr4 = next(p for p in body["positions"] if p["t"] == "PETR4")
    assert pos_petr4["qtyTravada"] == 0  # destravou
