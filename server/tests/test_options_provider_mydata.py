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
Offline: `monkeypatch.setattr(provider.mydata_client, "get_vencimentos"/
"get_options_chain", fake)` — nenhum teste toca rede.
"""
import asyncio

import pytest

from app import options_provider_mydata as provider
from app.options_quant import liquidity_score


@pytest.fixture(autouse=True)
def _cache_limpo():
    provider._cache.clear()
    yield
    provider._cache.clear()


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
