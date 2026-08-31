"""Fase 9, Plano 03 — adaptador do contrato ADR-004 alimentado por gold_opcoes
(`options_provider_mydata.py`).

O que estes testes protegem:
  • providerStatus/calls/puts/expirations continuam com o MESMO contrato que
    o ADR-004 já define (D-02) — nenhuma tela muda de forma;
  • falha do mydata em opções degrada DIRETO, sem tentar o Yahoo (D-04) —
    `options_provider_yahoo` nunca é importado nem chamado por este módulo;
  • IV/gregas/preço teórico vêm PRONTOS do hub — nenhum recálculo local
    (`black_scholes` não aparece fora de comentário);
  • volatilidade implícita nula é dado legítimo (rotulado em `ivStatus`), não
    erro;
  • `openInterest` é sempre `None` (COTAHIST não publica) — efeito medido
    sobre `liquidity_score`, não presumido;
  • cache de módulo (300s sucesso / 60s erro) poupa cota — duas chamadas
    seguidas ao mesmo (ticker, expiration) fazem UMA ida ao cliente.
  • estouro de orçamento degrada sem tocar a rede e sem cachear a recusa
    (OPTGATE-01 / WR-01 do `09-REVIEW.md`, Fase 0/Plano 02).
Offline: `monkeypatch.setattr(provider.mydata_client, "get_vencimentos"/
"get_options_chain", fake)` — nenhum teste toca rede.
"""
import asyncio

import pytest

from app import mydata_budget, options_provider_mydata as provider
from app.options_quant import liquidity_score


@pytest.fixture(autouse=True)
def _cache_limpo():
    provider._cache.clear()
    # Reset do orçamento em TODO teste deste arquivo, não só nos que testam
    # o gate — a partir desta entrega `get_options` sempre consulta a cota
    # real por baixo (a menos que o teste monkeypatche `pode_gastar`), e os
    # testes de contrato/cache pré-existentes não devem ficar reféns de
    # ordem de execução nem de estado deixado por outro arquivo de teste.
    mydata_budget.reset()
    yield
    provider._cache.clear()
    mydata_budget.reset()


def _linha_petr4(**over):
    base = {
        "dt_pregao": "2026-08-25",
        "contrato": "PETRA320",
        "ticker_objeto": "PETR4",
        "tipo": "CALL",
        "strike": 32.0,
        "dt_vencimento": "2026-09-19",
        "premio": 1.85,
        "melhor_oferta_compra": 1.80,
        "melhor_oferta_venda": 1.90,
        "quantidade_negociada": 5000,
        "preco_objeto": 33.10,
        "taxa_livre_risco": 0.105,
        "volatilidade_implicita": 0.28,
        "situacao_sigma": "invertido",
        "preco_teorico": 1.87,
        "delta": 0.62, "gamma": 0.08, "vega": 0.05, "theta": -0.02, "rho": 0.01,
        "estilo_exercicio": "europeia",
        "proveniencia": {"sha256": "abc123", "arquivo": "COTAHIST_D25082026.TXT"},
    }
    base.update(over)
    return base


def _vencimentos_ok():
    return [
        {"dt_vencimento": "2026-09-19", "contratos": 40, "com_sigma": 35,
         "vence_no_pregao": 0, "menor_strike": 25.0, "maior_strike": 45.0},
        {"dt_vencimento": "2026-10-17", "contratos": 30, "com_sigma": 20,
         "vence_no_pregao": 0, "menor_strike": 25.0, "maior_strike": 45.0},
    ]


def _patch(monkeypatch, vencimentos=None, chain=None, venc_exc=None, chain_exc=None):
    async def fake_vencimentos(ticker, pregao=None, *, fetch_json=None):
        if venc_exc:
            raise venc_exc
        return vencimentos if vencimentos is not None else _vencimentos_ok()

    async def fake_chain(ticker, vencimento=None, pregao=None, tipo=None, *, fetch_json=None):
        if chain_exc:
            raise chain_exc
        return chain if chain is not None else [_linha_petr4()]

    monkeypatch.setattr(provider.mydata_client, "get_vencimentos", fake_vencimentos)
    monkeypatch.setattr(provider.mydata_client, "get_options_chain", fake_chain)


# ---------------------------------------------------------------------------
# Caminho ok
# ---------------------------------------------------------------------------
def test_get_options_ok_devolve_provider_status_ok_e_source_mydata(monkeypatch):
    _patch(monkeypatch)
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["providerStatus"] == "ok"
    assert data["source"] == "mydata"


def test_expirations_saem_da_lista_de_vencimentos_em_ordem(monkeypatch):
    _patch(monkeypatch)
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["expirations"] == ["2026-09-19", "2026-10-17"]


def test_sem_expiration_escolhe_primeiro_vencimento_que_nao_vence_no_pregao(monkeypatch):
    _patch(monkeypatch, vencimentos=[
        {"dt_vencimento": "2026-08-25", "vence_no_pregao": 1},
        {"dt_vencimento": "2026-09-19", "vence_no_pregao": 0},
    ])
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["expiration"] == "2026-09-19"


def test_todos_vencem_no_pregao_escolhe_o_primeiro_da_lista(monkeypatch):
    _patch(monkeypatch, vencimentos=[
        {"dt_vencimento": "2026-08-25", "vence_no_pregao": 1},
        {"dt_vencimento": "2026-08-25", "vence_no_pregao": 1},
    ])
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["expiration"] == "2026-08-25"


def test_expiration_pedido_presente_vai_no_filtro_da_chamada_de_cadeia(monkeypatch):
    chamadas = []

    async def fake_chain(ticker, vencimento=None, pregao=None, tipo=None, *, fetch_json=None):
        chamadas.append(vencimento)
        return [_linha_petr4(dt_vencimento="2026-10-17")]

    async def fake_vencimentos(ticker, pregao=None, *, fetch_json=None):
        return _vencimentos_ok()

    monkeypatch.setattr(provider.mydata_client, "get_vencimentos", fake_vencimentos)
    monkeypatch.setattr(provider.mydata_client, "get_options_chain", fake_chain)
    data = asyncio.run(provider.get_options("PETR4", expiration="2026-10-17"))
    assert chamadas == ["2026-10-17"]
    assert data["expiration"] == "2026-10-17"


def test_expiration_pedido_ausente_da_lista_degrada_com_warning_especifico(monkeypatch):
    _patch(monkeypatch)
    data = asyncio.run(provider.get_options("PETR4", expiration="2099-01-01"))
    assert data["providerStatus"] == "degraded"
    assert "2099-01-01" in data["warning"]
    assert "providerError" not in data


def test_tipo_call_vira_calls_e_optiontype_minusculo(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4(tipo="CALL")])
    data = asyncio.run(provider.get_options("PETR4"))
    assert len(data["calls"]) == 1
    assert data["calls"][0]["optionType"] == "call"
    assert data["puts"] == []


def test_tipo_put_vira_puts_e_optiontype_minusculo(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4(tipo="PUT", contrato="PETRP320")])
    data = asyncio.run(provider.get_options("PETR4"))
    assert len(data["puts"]) == 1
    assert data["puts"][0]["optionType"] == "put"
    assert data["calls"] == []


def test_mapeamento_de_campos_basicos_do_contrato(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4()])
    data = asyncio.run(provider.get_options("PETR4"))
    c = data["calls"][0]
    assert c["lastPrice"] == 1.85
    assert c["bid"] == 1.80
    assert c["ask"] == 1.90
    assert c["volume"] == 5000


def test_open_interest_e_sempre_none(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4()])
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["calls"][0]["openInterest"] is None


def test_iv_nula_nao_degrada_e_ivstatus_carrega_motivo(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4(
        volatilidade_implicita=None, situacao_sigma="sem_premio")])
    data = asyncio.run(provider.get_options("PETR4"))
    c = data["calls"][0]
    assert data["providerStatus"] == "ok"
    assert c["impliedVolatility"] is None
    assert c["ivStatus"] == "sem_premio"


def test_underlying_price_sai_do_primeiro_preco_objeto_nao_nulo(monkeypatch):
    _patch(monkeypatch, chain=[
        _linha_petr4(preco_objeto=None), _linha_petr4(preco_objeto=33.10)])
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["underlyingPrice"] == 33.10


def test_currency_e_sempre_brl(monkeypatch):
    _patch(monkeypatch)
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["currency"] == "BRL"


def test_distance_pct_mesma_formula_do_provider_yahoo(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4(strike=32.0, preco_objeto=33.10)])
    data = asyncio.run(provider.get_options("PETR4"))
    esperado = round((32.0 - 33.10) / 33.10 * 100, 2)
    assert data["calls"][0]["distancePct"] == esperado


def test_distance_pct_none_quando_nao_ha_spot(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4(preco_objeto=None)])
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["calls"][0]["distancePct"] is None


def test_in_the_money_call_quando_spot_maior_que_strike(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4(tipo="CALL", strike=32.0, preco_objeto=33.10)])
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["calls"][0]["inTheMoney"] is True


def test_in_the_money_put_quando_spot_menor_que_strike(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4(tipo="PUT", contrato="PETRP320", strike=34.0, preco_objeto=33.10)])
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["puts"][0]["inTheMoney"] is True


def test_in_the_money_false_quando_nao_ha_spot(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4(preco_objeto=None)])
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["calls"][0]["inTheMoney"] is False


def test_campos_aditivos_gregas_preco_teorico_e_metadados(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4()])
    data = asyncio.run(provider.get_options("PETR4"))
    c = data["calls"][0]
    assert c["theoreticalPrice"] == 1.87
    assert c["greeks"] == {"delta": 0.62, "gamma": 0.08, "vega": 0.05, "theta": -0.02, "rho": 0.01}
    assert c["expiration"] == "2026-09-19"
    assert c["riskFreeRate"] == 0.105
    assert c["exerciseStyle"] == "europeia"


def test_todas_as_chaves_do_contrato_antigo_continuam_presentes(monkeypatch):
    _patch(monkeypatch, chain=[_linha_petr4()])
    data = asyncio.run(provider.get_options("PETR4"))
    c = data["calls"][0]
    for k in ("contractSymbol", "optionType", "strike", "lastPrice", "bid", "ask",
              "change", "percentChange", "volume", "openInterest",
              "impliedVolatility", "inTheMoney", "currency", "distancePct"):
        assert k in c, f"chave {k} sumiu do contrato"


# ---------------------------------------------------------------------------
# Degradação (D-04: sem fallback pro Yahoo)
# ---------------------------------------------------------------------------
def test_sem_pregao_publicado_degrada_sem_provider_error(monkeypatch):
    _patch(monkeypatch, vencimentos=[])
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["providerStatus"] == "degraded"
    assert "providerError" not in data
    assert data["source"] == "mydata"


def test_mydata_indisponivel_degrada_com_provider_error_sem_chamar_yahoo(monkeypatch):
    import app.mydata_client as mc
    _patch(monkeypatch, venc_exc=mc.MydataIndisponivel("mydata quota excedida"))
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["providerStatus"] == "degraded"
    assert "mydata quota excedida" in data["providerError"]


def test_falha_na_cadeia_apos_vencimentos_ok_tambem_degrada(monkeypatch):
    import app.mydata_client as mc
    _patch(monkeypatch, chain_exc=mc.MydataIndisponivel("mydata HTTP 500"))
    data = asyncio.run(provider.get_options("PETR4"))
    assert data["providerStatus"] == "degraded"
    assert "mydata HTTP 500" in data["providerError"]


# ---------------------------------------------------------------------------
# Cache (mesma mecânica do provider Yahoo)
# ---------------------------------------------------------------------------
def test_duas_chamadas_seguidas_mesmo_ticker_fazem_uma_ida_ao_cliente(monkeypatch):
    chamadas = {"n": 0}

    async def fake_vencimentos(ticker, pregao=None, *, fetch_json=None):
        chamadas["n"] += 1
        return _vencimentos_ok()

    async def fake_chain(ticker, vencimento=None, pregao=None, tipo=None, *, fetch_json=None):
        return [_linha_petr4()]

    monkeypatch.setattr(provider.mydata_client, "get_vencimentos", fake_vencimentos)
    monkeypatch.setattr(provider.mydata_client, "get_options_chain", fake_chain)
    asyncio.run(provider.get_options("PETR4"))
    asyncio.run(provider.get_options("PETR4"))
    assert chamadas["n"] == 1


# ---------------------------------------------------------------------------
# Gate de orçamento (OPTGATE-01 / WR-01) — prova de comportamento, não de
# existência: cada teste tem asserção sobre o que NÃO aconteceu (rede não
# tocada, débito não feito) ou sobre o estado observável do payload.
# ---------------------------------------------------------------------------
def test_sem_cota_devolve_degradado_sem_tocar_o_cliente(monkeypatch):
    chamadas_venc = []
    chamadas_chain = []

    async def fake_vencimentos(ticker, pregao=None, *, fetch_json=None):
        chamadas_venc.append(ticker)
        return _vencimentos_ok()

    async def fake_chain(ticker, vencimento=None, pregao=None, tipo=None, *, fetch_json=None):
        chamadas_chain.append(ticker)
        return [_linha_petr4()]

    monkeypatch.setattr(provider.mydata_client, "get_vencimentos", fake_vencimentos)
    monkeypatch.setattr(provider.mydata_client, "get_options_chain", fake_chain)
    monkeypatch.setattr(mydata_budget, "pode_gastar", lambda n=1, now=None: False)

    data = asyncio.run(provider.get_options("PETR4"))

    assert data["providerStatus"] == "degraded"
    assert data["calls"] == []
    assert data["puts"] == []
    assert data["expirations"] == []
    assert data["source"] == "mydata"
    assert "cota" in data["providerError"]
    assert chamadas_venc == []
    assert chamadas_chain == []


def test_sem_cota_nao_debita(monkeypatch):
    debitos = []
    monkeypatch.setattr(mydata_budget, "pode_gastar", lambda n=1, now=None: False)
    monkeypatch.setattr(mydata_budget, "debita", lambda n=1, now=None: debitos.append(n))

    asyncio.run(provider.get_options("PETR4"))

    assert debitos == []


def test_recusa_por_cota_nao_e_cacheada(monkeypatch):
    """Decisão A-07: a recusa por cota não pode envelhecer no cache — assim
    que a cota libera, a MESMA chave (ticker, expiration) serve dado real."""
    _patch(monkeypatch)
    liberado = {"pode": False}
    monkeypatch.setattr(mydata_budget, "pode_gastar", lambda n=1, now=None: liberado["pode"])

    primeira = asyncio.run(provider.get_options("PETR4"))
    assert primeira["providerStatus"] == "degraded"

    liberado["pode"] = True
    segunda = asyncio.run(provider.get_options("PETR4"))
    assert segunda["providerStatus"] == "ok"
    assert segunda["calls"]


def test_caminho_feliz_debita_duas_vezes(monkeypatch):
    """WR-01 (09-REVIEW.md, fechado): `_debita()` agora chama `mydata_budget.
    reservar()`, que REAVALIA `pode_gastar()` sob a mesma trava antes de cada
    debit real — check+debit atômico, não só o pré-filtro de `_gate(2)`.
    `pode_gastar` é chamado 3x (pré-filtro com n=2, depois n=1 duas vezes nos
    dois pontos de commit), não mais 1x."""
    _patch(monkeypatch)
    debitos = []
    consultas_n = []

    def fake_pode_gastar(n=1, now=None):
        consultas_n.append(n)
        return True

    monkeypatch.setattr(mydata_budget, "pode_gastar", fake_pode_gastar)
    monkeypatch.setattr(mydata_budget, "debita", lambda n=1, now=None: debitos.append(n))

    data = asyncio.run(provider.get_options("PETR4"))

    assert data["providerStatus"] == "ok"
    assert debitos == [1, 1]
    assert consultas_n == [2, 1, 1]


def test_vencimento_inexistente_debita_uma_vez(monkeypatch):
    _patch(monkeypatch)
    debitos = []
    monkeypatch.setattr(mydata_budget, "pode_gastar", lambda n=1, now=None: True)
    monkeypatch.setattr(mydata_budget, "debita", lambda n=1, now=None: debitos.append(n))

    data = asyncio.run(provider.get_options("PETR4", expiration="2099-01-01"))

    assert data["providerStatus"] == "degraded"
    assert debitos == [1]


def test_cache_quente_nao_consulta_orcamento(monkeypatch):
    """WR-01 (09-REVIEW.md, fechado): a PRIMEIRA chamada (cache frio) agora
    consulta `pode_gastar` 3x — pré-filtro `_gate(2)` mais a reavaliação
    atômica de `reservar()` em cada um dos dois pontos de commit — não mais
    1x. A SEGUNDA chamada (cache quente) continua sem consultar nada, que é
    o que este teste protege."""
    _patch(monkeypatch)
    consultas = []
    debitos = []
    monkeypatch.setattr(mydata_budget, "pode_gastar", lambda n=1, now=None: consultas.append(n) or True)
    monkeypatch.setattr(mydata_budget, "debita", lambda n=1, now=None: debitos.append(n))

    asyncio.run(provider.get_options("PETR4"))
    asyncio.run(provider.get_options("PETR4"))

    assert consultas == [2, 1, 1]
    assert debitos == [1, 1]


# ---------------------------------------------------------------------------
# Efeito de openInterest ausente sobre o gate de liquidez (medição, não fix)
# ---------------------------------------------------------------------------
def test_liquidity_score_sem_open_interest_de_contrato_liquido_petr4_registra_52_0_passa_do_corte_40(monkeypatch):
    """PETR4, volume alto (5000) e spread apertado (1.80/1.90 ~5.41%),
    openInterest=None (sem fonte no COTAHIST). Score medido: 52.0 — passa do
    corte de 40 usado por `options_api.liquidity_gate`. Sem open interest o
    teto do score cai de 100 para 60 (vol_score até 35 + base 25 -
    spread_penalty mínimo 0), então este caso específico passa, mas
    contratos com volume menor que hoje dependiam de open interest real para
    cruzar o corte podem não passar mais — achado de produto para o
    checkpoint do Plano 09-06, NÃO corrigido aqui (options_quant.py não é
    alterado por este plano)."""
    resultado = liquidity_score(volume=5000, open_interest=None, bid=1.80, ask=1.90)
    assert resultado["score"] == 52.0
    assert resultado["score"] >= 40
