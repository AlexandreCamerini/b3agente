"""Provider mydata para cadeias de opcoes (Fase 9, Plano 03 — qa/09).

Substitui a fonte por trás do MESMO contrato `providerStatus` que o ADR-004
já define (D-02): a UI e `options_api.liquidity_gate` não mudam de forma.
IV, gregas e preço teórico vêm PRONTOS do hub (Black-Scholes resolvido do
lado do mydata, `nucleos.py:182-223`) — este módulo NÃO recalcula nada
localmente.

D-04 é explícita e vale para TODO ramo deste arquivo: se o mydata falhar
(quota, 5xx, resposta imprestável), o resultado vai DIRETO para
`providerStatus="degraded"` — NUNCA um fallback para o provedor anterior.
Reintroduzi-lo como fallback anularia o ganho desta migração: aquele
endpoint de opções é não-oficial e responde 401/403/429, exatamente a fonte
instável que esta migração elimina. O provedor anterior fica como código
histórico — alavanca de rollback manual via `options_provider.py` (Task 3),
não caminho automático.
"""
from __future__ import annotations

import time
from typing import Optional

from . import mydata_client
from .tickers import normalize_ticker

_OPTIONS_TTL = 300
_ERROR_TTL = 60
_cache: dict[str, tuple[float, dict]] = {}


MYDATA_OPTIONS_WARNING = (
    "A cadeia de opções vem do acervo oficial da B3 (COTAHIST), publicado "
    "após o fechamento do pregão. Neste momento o hub de dados não "
    "respondeu — tente novamente mais tarde."
)


def _empty_payload(ticker: str, expiration: Optional[str], warning: str, error: Optional[str] = None) -> dict:
    symbol = normalize_ticker(ticker)
    payload = {
        "ticker": ticker,
        "symbol": symbol,
        "expirations": [],
        "expiration": expiration,
        "calls": [],
        "puts": [],
        "source": "mydata",
        "providerStatus": "degraded",
        "warning": warning,
    }
    if error:
        payload["providerError"] = error
    return payload


def _clean_contract(raw: dict, spot: Optional[float]) -> dict:
    """Mapeia uma linha crua de `gold_opcoes` para o contrato do ADR-004,
    mais os campos ADITIVOS que o contrato antigo não tinha (gregas, preço
    teórico, status da IV, proveniência do vencimento). Aditivo, nunca
    substitutivo: nenhuma chave do contrato antigo é removida."""
    strike = raw.get("strike")
    option_type = str(raw.get("tipo") or "").lower()
    dist = None
    if isinstance(spot, (int, float)) and spot > 0 and isinstance(strike, (int, float)):
        dist = round((float(strike) - float(spot)) / float(spot) * 100, 2)
    in_the_money = False
    if isinstance(spot, (int, float)) and spot > 0 and isinstance(strike, (int, float)):
        if option_type == "call":
            in_the_money = spot > strike
        elif option_type == "put":
            in_the_money = spot < strike
    return {
        "contractSymbol": raw.get("contrato"),
        "optionType": option_type,
        "strike": strike,
        "lastPrice": raw.get("premio"),
        "bid": raw.get("melhor_oferta_compra"),
        "ask": raw.get("melhor_oferta_venda"),
        "change": None,  # COTAHIST não publica variação do contrato
        "percentChange": None,
        "volume": raw.get("quantidade_negociada") or 0,
        "openInterest": None,  # SEM FONTE — B3/gold_opcoes não publicam
        "impliedVolatility": raw.get("volatilidade_implicita"),  # nulo é legítimo
        "inTheMoney": in_the_money,
        "currency": "BRL",
        "distancePct": dist,
        # -- aditivos (ganho da migração; nenhum existia no contrato Yahoo) --
        "ivStatus": raw.get("situacao_sigma"),
        "theoreticalPrice": raw.get("preco_teorico"),
        "greeks": {
            "delta": raw.get("delta"),
            "gamma": raw.get("gamma"),
            "vega": raw.get("vega"),
            "theta": raw.get("theta"),
            "rho": raw.get("rho"),
        },
        "expiration": raw.get("dt_vencimento"),
        "riskFreeRate": raw.get("taxa_livre_risco"),
        "exerciseStyle": raw.get("estilo_exercicio"),
    }


async def get_options(ticker: str, expiration: Optional[str] = None) -> dict:
    t = normalize_ticker(ticker)
    key = f"{t}:{expiration or 'first'}"
    hit = _cache.get(key)
    if hit and (time.time() - hit[0]) < _OPTIONS_TTL:
        return hit[1]

    try:
        venc = await mydata_client.get_vencimentos(t)
        if not venc:
            payload = _empty_payload(
                ticker, expiration,
                "Nenhum pregão publicado com opções para este ativo no "
                "acervo oficial da B3.")
            _cache[key] = (time.time() - (_OPTIONS_TTL - _ERROR_TTL), payload)
            return payload

        expirations = [v.get("dt_vencimento") for v in venc]

        if expiration:
            if expiration not in expirations:
                payload = _empty_payload(
                    ticker, expiration,
                    f"Vencimento {expiration} não está disponível para este "
                    "ativo no pregão atual — a lista de vencimentos vem do "
                    "endpoint dedicado do mydata.")
                _cache[key] = (time.time() - (_OPTIONS_TTL - _ERROR_TTL), payload)
                return payload
            escolhido = expiration
        else:
            nao_vence_hoje = [v for v in venc if not v.get("vence_no_pregao")]
            escolhido = (nao_vence_hoje[0] if nao_vence_hoje else venc[0]).get("dt_vencimento")

        linhas = await mydata_client.get_options_chain(t, vencimento=escolhido)

        spot = None
        for row in linhas:
            if row.get("preco_objeto") is not None:
                spot = row.get("preco_objeto")
                break
        pregao = linhas[0].get("dt_pregao") if linhas else None
        provenance = linhas[0].get("proveniencia") if linhas else None

        calls = []
        puts = []
        for row in linhas:
            contrato = _clean_contract(row, spot)
            if contrato["optionType"] == "call":
                calls.append(contrato)
            elif contrato["optionType"] == "put":
                puts.append(contrato)

        payload = {
            "ticker": ticker,
            "symbol": t,
            "source": "mydata",
            "providerStatus": "ok",
            "underlyingPrice": spot,
            "currency": "BRL",
            "expirations": expirations,
            "expiration": escolhido,
            "calls": calls,
            "puts": puts,
            "pregao": pregao,
        }
        if provenance:
            payload["provenance"] = provenance
        _cache[key] = (time.time(), payload)
        return payload
    except Exception as e:  # noqa: BLE001 — D-04: falha vira degradado, NUNCA Yahoo
        payload = _empty_payload(ticker, expiration, MYDATA_OPTIONS_WARNING, str(e))
        _cache[key] = (time.time() - (_OPTIONS_TTL - _ERROR_TTL), payload)
        return payload
