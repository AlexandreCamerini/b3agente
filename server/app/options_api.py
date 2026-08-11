"""Rotas e análise educacional de opcoes."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, Body, HTTPException

from . import candle_provider, indicators, tickers, yahoo
from .options_provider_yahoo import get_options
from .options_quant import black_scholes, breakeven, educational_score, historical_volatility, intrinsic_value, liquidity_score, years_to_expiration

router = APIRouter(prefix="/api/options", tags=["options"])


def _normalize_ticker(s: str) -> str:
    return tickers.normalize_ticker(s)


def _days_to(expiration: Optional[str]) -> int:
    if not expiration:
        return 0
    try:
        d = dt.date.fromisoformat(expiration)
        return max(0, (d - dt.date.today()).days)
    except Exception:
        return 0


def _spot_from_chain_or_quote(chain: dict, quote: Optional[dict]) -> Optional[float]:
    spot = chain.get("underlyingPrice")
    if isinstance(spot, (int, float)) and spot > 0:
        return float(spot)
    if quote and isinstance(quote.get("price"), (int, float)):
        return float(quote["price"])
    return None


async def _technical_context(t: str) -> dict:
    # ADR-008 (Fase 5): ponto único — 1y sai do plano free e roteia pro backup.
    hist = await candle_provider.get_history(t, rng="1y")
    candles = indicators.sanitize_candles(hist.get("candles"))
    closes = [c.get("close") for c in candles if c.get("close")]
    comp = indicators.compute(candles) if candles else {"summary": {}}
    summary = comp.get("summary") or {}
    trend = "lateral/indefinida"
    try:
        ma9 = summary.get("sma9") or summary.get("ma9")
        ma21 = summary.get("sma21") or summary.get("ma21")
        last = closes[-1]
        if last and ma9 and ma21 and last > ma9 > ma21:
            trend = "alta"
        elif last and ma9 and ma21 and last < ma9 < ma21:
            trend = "baixa"
    except Exception:
        pass
    return {
        "candles": candles[-80:],
        "summary": summary,
        "trend": trend,
        "hv21": historical_volatility(closes, 21),
        "hv63": historical_volatility(closes, 63),
    }


def _enrich_contract(c: dict, spot: float, expiration: str, hv21: Optional[float]) -> dict:
    kind = c.get("optionType")
    strike = float(c.get("strike") or 0)
    premium = c.get("lastPrice")
    if not isinstance(premium, (int, float)) or premium < 0:
        bid = c.get("bid") if isinstance(c.get("bid"), (int, float)) else 0
        ask = c.get("ask") if isinstance(c.get("ask"), (int, float)) else 0
        premium = (bid + ask) / 2 if bid > 0 and ask > 0 else 0
    days = _days_to(expiration)
    iv = c.get("impliedVolatility")
    bs = black_scholes(kind, spot, strike, years_to_expiration(days), 0.105, float(iv or hv21 or 0), 0.0) if strike > 0 else None
    liq = liquidity_score(c.get("volume"), c.get("openInterest"), c.get("bid"), c.get("ask"))
    prob_itm = bs.prob_itm if bs else None
    score = educational_score(None, liq, iv, hv21, days, prob_itm)
    out = dict(c)
    out.update({
        "premiumUsed": round(float(premium or 0), 4),
        "daysToExpiration": days,
        "intrinsicValue": intrinsic_value(kind, spot, strike) if strike > 0 else None,
        "timeValue": round(max(0, float(premium or 0) - intrinsic_value(kind, spot, strike)), 4) if strike > 0 else None,
        "breakeven": breakeven(kind, strike, float(premium or 0)) if strike > 0 else None,
        "liquidity": liq,
        "blackScholes": bs.__dict__ if bs else None,
        "educationalScore": score,
    })
    return out


@router.get("/expirations/{ticker}")
async def expirations(ticker: str):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker inválido.")
    try:
        chain = await get_options(t)
    except yahoo.QuoteUnavailable as e:
        raise HTTPException(503, str(e))
    return {"ticker": t, "symbol": chain.get("symbol"), "expirations": chain.get("expirations") or [], "source": chain.get("source"), "warning": chain.get("warning")}


@router.get("/chain/{ticker}")
async def chain(ticker: str, expiration: Optional[str] = None):
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker inválido.")
    try:
        data = await get_options(t, expiration)
        quote = None
        try:
            quote = await candle_provider.get_quote(t)
        except Exception:
            quote = None
        spot = _spot_from_chain_or_quote(data, quote)
        try:
            tech = await _technical_context(t)
        except Exception as e:  # noqa: BLE001
            tech = {"trend": "indisponível", "hv21": None, "hv63": None, "summary": {}, "warning": str(e)}
        if spot and data.get("expiration"):
            data["calls"] = [_enrich_contract(c, spot, data["expiration"], tech.get("hv21")) for c in data.get("calls", [])]
            data["puts"] = [_enrich_contract(p, spot, data["expiration"], tech.get("hv21")) for p in data.get("puts", [])]
        data["underlyingPrice"] = spot
        data["technical"] = {"trend": tech.get("trend"), "hv21": tech.get("hv21"), "hv63": tech.get("hv63"), "summary": tech.get("summary")}
        if tech.get("warning") and not data.get("warning"):
            data["warning"] = "Cadeia de opções carregada, mas o contexto técnico do ativo objeto ficou indisponível temporariamente."
        return data
    except yahoo.QuoteUnavailable as e:
        raise HTTPException(503, str(e))


@router.get("/gate/{ticker}")
async def liquidity_gate(ticker: str):
    """Gate de descobribilidade (proposta v2 §2): a linha de opções no card só
    aparece se o ativo tem ao menos 1 contrato líquido no vencimento mais
    próximo. Best-effort e barato — reusa o cache de 300s do provider (mesma
    chamada de `chain`/`expirations`), sem enriquecer com BSM/técnico (isso só
    roda quando o usuário abre a cadeia completa)."""
    t = _normalize_ticker(ticker)
    if len(t) < 4:
        raise HTTPException(400, "Ticker inválido.")
    try:
        data = await get_options(t)
    except yahoo.QuoteUnavailable:
        return {"ticker": t, "liquida": False, "providerStatus": "degraded"}
    if data.get("providerStatus") != "ok":
        return {"ticker": t, "liquida": False, "providerStatus": data.get("providerStatus")}
    contratos = [*data.get("calls", []), *data.get("puts", [])]
    liquida = any(
        liquidity_score(c.get("volume"), c.get("openInterest"), c.get("bid"), c.get("ask"))["score"] >= 40
        for c in contratos
    )
    return {"ticker": t, "liquida": liquida, "providerStatus": "ok"}


@router.post("/analyze")
async def analyze_options(body: dict = Body(default={})):
    t = _normalize_ticker(str((body or {}).get("ticker") or ""))
    expiration = (body or {}).get("expiration")
    contract_symbol = (body or {}).get("contractSymbol")
    option_type = (body or {}).get("optionType")
    strike = (body or {}).get("strike")
    if len(t) < 4:
        raise HTTPException(400, "Ticker inválido.")
    data = await chain(t, expiration)
    contracts = [*data.get("calls", []), *data.get("puts", [])]
    selected = None
    if contract_symbol:
        selected = next((c for c in contracts if c.get("contractSymbol") == contract_symbol), None)
    if selected is None and option_type and strike is not None:
        selected = next((c for c in contracts if c.get("optionType") == option_type and float(c.get("strike") or 0) == float(strike)), None)
    if selected is None:
        raise HTTPException(404, "Contrato de opção não encontrado na cadeia retornada pelo provedor.")
    risk_flags = []
    if (selected.get("liquidity") or {}).get("score", 0) < 40:
        risk_flags.append("Liquidez fraca ou spread aberto: risco de entrada/saída ruim.")
    if (selected.get("daysToExpiration") or 0) <= 21:
        risk_flags.append("Vencimento curto: theta pode corroer o prêmio rapidamente.")
    if not selected.get("blackScholes"):
        risk_flags.append("Dados insuficientes para estimar Black-Scholes/gregos com confiança.")
    if not risk_flags:
        risk_flags.append("Risco principal: perda total do prêmio pago na simulação comprada.")
    text = (
        "Esta análise é educacional, usa dinheiro fictício e não representa recomendação de investimento.\n\n"
        f"Ativo objeto: {t}. Preço base: {data.get('underlyingPrice')}. Vencimento: {data.get('expiration')}.\n"
        f"Contrato estudado: {selected.get('contractSymbol')} ({selected.get('optionType')} strike {selected.get('strike')}).\n"
        f"Score educacional: {(selected.get('educationalScore') or {}).get('score')} — {(selected.get('educationalScore') or {}).get('label')}.\n"
        "A leitura combina tendência do ativo, liquidez da opção, volatilidade implícita/histórica, gregos e prazo. "
        "Não use este resultado como ordem de compra ou venda; use apenas para estudo e simulação."
    )
    return {"ticker": t, "expiration": data.get("expiration"), "contract": selected, "riskFlags": risk_flags, "markdown": text}
