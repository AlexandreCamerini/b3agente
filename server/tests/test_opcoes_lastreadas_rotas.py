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
import inspect
import re
import uuid

import pytest
from fastapi.testclient import TestClient

from app import options_provider_mock, pregao, setups, store, technical_snapshot
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


@pytest.fixture
def _plano_vender(monkeypatch):
    """Leitura técnica de VENDER (risco de queda sobre a posição) — o motor
    propõe `put_protecao` (ou, com `multiperna=1` e caixa insuficiente pra
    put isolada, `collar`)."""
    monkeypatch.setattr(setups, "plano_do_resultado", lambda *a, **k: {"decisao": "VENDER", "lado": "baixa"})


def _pernas_collar_da_cadeia(cli, ticker="PETR4"):
    """Lê a cadeia REAL do provider mock e devolve `(spot, premio_call,
    premio_put)` da MESMA régua de seleção do motor: call de menor strike
    ACIMA do spot (venda), put de maior strike ATÉ o spot (compra) — não
    chutado, para o caixa calculado no teste refletir o que `propor()`
    realmente vai escolher."""
    r = cli.get(f"/api/options/chain/{ticker}")
    assert r.status_code == 200, r.text
    data = r.json()
    spot = data["underlyingPrice"]
    calls_acima = [c for c in data["calls"] if c["strike"] > spot]
    puts_ate = [p for p in data["puts"] if p["strike"] <= spot]
    call = min(calls_acima, key=lambda c: c["strike"])
    put = max(puts_ate, key=lambda p: p["strike"])
    return spot, float(call["lastPrice"]), float(put["lastPrice"])


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


# --- Plano 16-04 — negociação de capacidade `multiperna` na rota de proposta

def test_proposta_sem_multiperna_traz_campos_aditivos_da_fase_16(cli, _expiracao_fixa, _snapshot_sem_setup):
    """`GET .../proposta/PETR4` sem o parâmetro novo: comportamento IDÊNTICO
    ao de antes desta fase (`motivo`/`contratos`), agora com os campos
    aditivos `estrutura`/`caixa`/`precoObjeto` do Plano 16-01 atravessando a
    serialização JSON da rota."""
    uid, headers = _novo_escopo(cli, "12")
    _seed_posicao(uid, qty=300)
    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["motivo"] == "call_coberta"
    assert body["proposta"]["contratos"] >= 1
    assert isinstance(body["proposta"]["estrutura"], dict)
    assert isinstance(body["proposta"]["caixa"], dict)
    assert isinstance(body["proposta"]["precoObjeto"], (int, float))


def test_proposta_vender_caixa_insuficiente_multiperna_liga_collar_sem_quebrar_cliente_publicado(
        cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    """MESMO cenário (VENDER + caixa insuficiente pra put isolada): sem o
    parâmetro, o cliente publicado hoje continua vendo `caixa_insuficiente`
    — nenhuma regressão. Com `?multiperna=1`, o cliente que pediu a
    capacidade recebe o collar inteiro (payoff, duas pernas, caixa)."""
    uid, headers = _novo_escopo(cli, "13")
    _seed_posicao(uid, qty=300)
    spot, premio_call, premio_put = _pernas_collar_da_cadeia(cli)
    cash = max(0.0, 100 * (premio_put - premio_call)) + 0.5
    # As duas desigualdades que a fórmula do plano garante — afirmadas aqui
    # para que, se o mock mudar e a premissa quebrar, o teste falhe dizendo
    # por quê, em vez de passar por acidente.
    assert cash < 100 * premio_put, "put isolada não pode caber no caixa"
    assert cash >= 100 * (premio_put - premio_call), "o débito líquido do collar tem que caber"
    store.put(_conn, "cash", cash, user_id=uid)

    r_sem = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r_sem.status_code == 200
    body_sem = r_sem.json()
    assert body_sem["motivo"] == "caixa_insuficiente"
    assert body_sem["proposta"] is None

    r_com = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers)
    assert r_com.status_code == 200
    body_com = r_com.json()
    assert body_com["motivo"] == "collar"
    p = body_com["proposta"]
    assert p["tipo"] == "collar"
    assert p["contractSymbol"] is None
    assert len(p["pernasContratos"]) == 2
    assert p["estrutura"]["ganho_ilimitado"] is False
    assert p["estrutura"]["perda_ilimitada"] is False


def test_proposta_multiperna_falso_explicito_comporta_como_ausencia(
        cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    """`?multiperna=0` e `?multiperna=false` são o MESMO caminho que a
    ausência do parâmetro — nenhum dos dois libera o collar."""
    uid, headers = _novo_escopo(cli, "14")
    _seed_posicao(uid, qty=300)
    spot, premio_call, premio_put = _pernas_collar_da_cadeia(cli)
    cash = max(0.0, 100 * (premio_put - premio_call)) + 0.5
    store.put(_conn, "cash", cash, user_id=uid)

    for valor in ("0", "false"):
        r = cli.get(f"/api/options/proposta/PETR4?multiperna={valor}", headers=headers)
        assert r.status_code == 200, r.text
        assert r.json()["motivo"] == "caixa_insuficiente", valor


def test_proposta_multiperna_valor_invalido_devolve_422_nunca_500_nunca_collar(
        cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    uid, headers = _novo_escopo(cli, "15")
    _seed_posicao(uid, qty=300)
    r = cli.get("/api/options/proposta/PETR4?multiperna=banana", headers=headers)
    assert r.status_code == 422


def test_proposta_multiperna_com_caixa_folgado_continua_put_protecao(
        cli, _expiracao_fixa, _snapshot_sem_setup, _plano_vender):
    """Caixa folgado + `?multiperna=1`: a put isolada CABE, então o motor
    nunca entra no ramo do collar — `multiperna=1` não muda nada quando a
    porta que ele abriria já estava aberta."""
    uid, headers = _novo_escopo(cli, "16")
    _seed_posicao(uid, qty=300)
    store.put(_conn, "cash", 10_000.0, user_id=uid)
    r = cli.get("/api/options/proposta/PETR4?multiperna=1", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["motivo"] == "put_protecao"
    assert body["proposta"]["contratos"] >= 1


# --- Plano 17-02 — FLOW-04: `source` e `at` na resposta de proposta ---------
# Princípio 3 do CLAUDE.md ("dados de mercado exibem fonte, horário da última
# atualização..."). Mesma convenção já usada por `/api/quotes` (`at`,
# main.py:1339) e pelos technicals (`source`, main.py:1443) — aqui estendida
# à rota de proposta, nos QUATRO caminhos de resposta (proposta completa,
# fechamento, ausência sem_lastro, degradado).

_AT_RE = re.compile(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$")


def test_proposta_bem_sucedida_declara_source_e_at(cli, _expiracao_fixa, _snapshot_sem_setup):
    uid, headers = _novo_escopo(cli, "18")
    _seed_posicao(uid, qty=300)
    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["motivo"] == "call_coberta"
    assert body["source"] == "mock"
    assert _AT_RE.match(body["at"])


def test_proposta_de_fechamento_declara_source_e_at(cli):
    """Ramo `pos_op_aberta` (`proposta_fechar`) — mesmo carimbo, caminho
    distinto do ramo de proposta nova."""
    uid, headers = _novo_escopo(cli, "19")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    contrato = _contract_symbol(cli, "call")
    r_abrir = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 1,
    })
    assert r_abrir.status_code == 200, r_abrir.text

    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "mock"
    assert _AT_RE.match(body["at"])


def test_proposta_sem_lastro_declara_source_e_at(cli):
    """Ausência explicada (`sem_lastro`) também é uma afirmação sobre dado de
    mercado — não some sem carimbo."""
    uid, headers = _novo_escopo(cli, "20")
    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["motivo"] == "sem_lastro"
    assert body["source"] == "mock"
    assert _AT_RE.match(body["at"])


def test_proposta_degradada_declara_source_e_at(cli, monkeypatch):
    """Caminho degradado: `providerStatus == "degraded"`, mas a fonte que
    falhou continua declarada — degradação não é desculpa pra sumir com a
    proveniência."""
    uid, headers = _novo_escopo(cli, "21")
    monkeypatch.setenv("B3_OPTIONS_MOCK_STATUS", "degraded")
    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["providerStatus"] == "degraded"
    assert body["source"] == "mock"
    assert _AT_RE.match(body["at"])


def test_proposta_com_excecao_no_pipeline_mantem_source_ja_capturado(
        cli, monkeypatch, _expiracao_fixa):
    """Exceção depois que a cadeia já foi lida (aqui: `technical_snapshot.get`
    levantando) — `source` continua o valor real já capturado, nunca
    `KeyError`, nunca 500. A fonte é conhecida; apagá-la seria menos honesto
    que declará-la mesmo com o pipeline quebrado no meio."""
    uid, headers = _novo_escopo(cli, "22")
    _seed_posicao(uid, qty=300)

    async def _explode(ticker, period, loader, interval="1d"):
        raise RuntimeError("pipeline técnico quebrado de propósito")

    from app import technical_snapshot
    monkeypatch.setattr(technical_snapshot, "get", _explode)

    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["motivo"] == "degradado"
    assert body["source"] == "mock"
    assert _AT_RE.match(body["at"])


# --- Guardiões FLOW-04 (Plano 17-02) — "guardiões de teste não se apagam";
# reversão deliberada atualiza este guardião com nota, nunca apaga sem mais.

def test_fonte_da_proposta_vem_da_cadeia_e_nunca_de_literal_na_rota(cli):
    """Se a rota chumbar a fonte, o card do usuário passa a mentir de onde
    veio o dado no dia em que o provider mudar — o repositório já teve
    exatamente esse defeito (C-11/C-30 do REPORT-01, comentado em
    `web/src/App.jsx:1649`). `source` PRECISA vir de `chain.get("source")`,
    nunca de um literal escrito no corpo da rota."""
    uid, headers = _novo_escopo(cli, "24")
    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200
    assert r.json()["source"] == "mock"

    from app import main as main_mod
    src = inspect.getsource(main_mod.options_proposta)
    for literal in ('"yahoo"', '"brapi"', '"mydata"'):
        assert literal not in src, f"fonte de provedor chumbada na rota: {literal}"


@pytest.mark.parametrize("cenario", ["sem_lastro", "completa", "degradado"])
def test_toda_resposta_de_proposta_carrega_at_bem_formado(
        cli, monkeypatch, _expiracao_fixa, _snapshot_sem_setup, cenario):
    """Parametrizado sobre os 3 caminhos de resposta já cobertos (ausência,
    proposta completa, degradado): em TODOS, `at` está presente e bem
    formado, e `source` está sempre presente como chave (valor podendo ser
    `None`) — a suíte reprova se qualquer caminho perder o carimbo de
    horário."""
    uid, headers = _novo_escopo(cli, f"25-{cenario}")
    if cenario == "completa":
        _seed_posicao(uid, qty=300)
    elif cenario == "degradado":
        monkeypatch.setenv("B3_OPTIONS_MOCK_STATUS", "degraded")
    # cenario == "sem_lastro": nenhuma posição, nenhum monkeypatch extra.

    r = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "at" in body
    assert _AT_RE.match(body["at"])
    assert "source" in body


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


# --- Plano 16-04 — trava de servidor contra execução de meia estrutura -------
# `store.abrir_call_coberta`/`store.comprar_put_protecao` executam UMA perna
# por chamada; sem esta trava, um corpo de collar postado nesta rota abriria
# só a perna que coubesse no `contractSymbol` único — o usuário ficaria com
# METADE da trava protetora, exposto a um risco diferente do apresentado na
# tela. A trava é do SERVIDOR (mesma disciplina do 403 de Modo Estudo,
# T-14-23): a UI pode ter bug, o servidor recusa igual.

def test_abrir_recusa_estrutura_collar_por_tipo_400_sem_efeito_colateral(cli):
    uid, headers = _novo_escopo(cli, "17")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    option_positions_antes = store.get(_conn, "optionPositions", user_id=uid)
    contrato_call = _contract_symbol(cli, "call")
    contrato_put = _contract_symbol(cli, "put")
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "tipo": "collar", "contratos": 3,
        "pernasContratos": [contrato_call["contractSymbol"], contrato_put["contractSymbol"]],
    })
    assert r.status_code == 400
    assert "mais de uma perna" in r.json()["detail"]
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    assert store.get(_conn, "optionPositions", user_id=uid) == option_positions_antes


def test_abrir_recusa_pernasContratos_de_duas_entradas_mesmo_sem_declarar_tipo(cli):
    """A trava não depende do cliente ser honesto sobre o rótulo `tipo` — a
    presença de DUAS pernas já basta, mesmo que o corpo omita `tipo`."""
    uid, headers = _novo_escopo(cli, "18")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    caixa_antes = store.get(_conn, "cash", user_id=uid)
    option_positions_antes = store.get(_conn, "optionPositions", user_id=uid)
    contrato_call = _contract_symbol(cli, "call")
    contrato_put = _contract_symbol(cli, "put")
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contratos": 3,
        "pernasContratos": [contrato_call["contractSymbol"], contrato_put["contractSymbol"]],
    })
    assert r.status_code == 400
    assert "mais de uma perna" in r.json()["detail"]
    assert store.get(_conn, "cash", user_id=uid) == caixa_antes
    assert store.get(_conn, "optionPositions", user_id=uid) == option_positions_antes


def test_abrir_com_pernasContratos_de_uma_entrada_continua_abrindo_normalmente(cli):
    """A trava NÃO pega a estrutura legítima de uma perna — nenhuma
    regressão nas duas operações já em produção (venda coberta/put)."""
    uid, headers = _novo_escopo(cli, "19")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    contrato = _contract_symbol(cli, "call")
    r = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 1,
        "pernasContratos": [contrato["contractSymbol"]],
    })
    assert r.status_code == 200, r.text


# --------------------------- POST .../lastreada/fechar ------------------------

# ------- GET proposta APÓS abertura: bugfix do checkpoint humano (Plano 08) --
# `propor()` é stateless e re-escolhia o contrato a cada chamada — spot ou
# leitura técnica mudando fazia a proposta divergir do contrato JÁ ABERTO, e o
# front (`posAberta = myOptionPositions.find(p => p.id === proposta.contractSymbol)`,
# App.jsx:3216-3217) parava de casar a posição, sumindo com o CTA "Recomprar/
# fechar". Este teste abre uma call coberta e faz a MESMA rota de proposta
# divergir tecnicamente (snapshot com um setup de alta, que faria `propor()`
# devolver `sem_setup` do zero) — a rota precisa continuar devolvendo o
# MESMO `contractSymbol` já aberto, não a leitura fresca.

@pytest.fixture
def _snapshot_tendencia_alta(monkeypatch):
    """Plano técnico de ALTA/COMPRAR — se a rota ainda chamasse `propor()`
    depois de uma posição já aberta, isto faria a proposta divergir para
    `sem_setup` (decisao COMPRAR não propõe nada, ver `opcoes_lastreadas.
    propor`). Usado só para PROVAR que a rota não passa mais por `propor()`
    quando já existe posição lastreada aberta."""
    async def _fake_get(ticker, period, loader, interval="1d"):
        return {"setups": {"setups": [{"nome": "rompimento_alta", "ativo": True}]}, "close": 40.0}

    monkeypatch.setattr(technical_snapshot, "get", _fake_get)


def test_proposta_apos_abrir_continua_casando_o_mesmo_contrato(cli, _expiracao_fixa, _snapshot_sem_setup):
    """Reprodução literal do achado do developer: abrir, então pedir a
    proposta de novo — o `contractSymbol` tem que ser o MESMO da posição
    aberta, não um novo pick de `propor()`."""
    uid, headers = _novo_escopo(cli, "10")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    contrato = _contract_symbol(cli, "call")
    r_abrir = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 1,
    })
    assert r_abrir.status_code == 200, r_abrir.text

    r_proposta = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r_proposta.status_code == 200
    body = r_proposta.json()
    assert body["proposta"] is not None, body
    assert body["proposta"]["contractSymbol"] == contrato["contractSymbol"]
    assert body["motivo"] == "call_coberta"


def test_proposta_apos_abrir_estavel_mesmo_quando_plano_tecnico_divergiria(
        cli, _expiracao_fixa, _snapshot_tendencia_alta):
    """Mesmo cenário, mas com o plano técnico mockado para o que faria
    `propor()` divergir (decisão COMPRAR → `sem_setup`, contrato nenhum) — a
    proposta de fechamento não deve ser afetada, porque a rota nem chama
    `propor()`/o pipeline técnico quando já existe posição aberta."""
    uid, headers = _novo_escopo(cli, "11")
    _seed_posicao(uid, qty=300)
    _liga_operador(uid)
    contrato = _contract_symbol(cli, "call")
    r_abrir = cli.post("/api/options/lastreada/abrir", headers=headers, json={
        "underlying": "PETR4", "contractSymbol": contrato["contractSymbol"], "contratos": 1,
    })
    assert r_abrir.status_code == 200, r_abrir.text

    r_proposta = cli.get("/api/options/proposta/PETR4", headers=headers)
    assert r_proposta.status_code == 200
    body = r_proposta.json()
    assert body["proposta"] is not None, body
    assert body["proposta"]["contractSymbol"] == contrato["contractSymbol"]
    assert body["motivo"] == "call_coberta"  # NÃO "sem_setup" — propor() nem é chamado


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
