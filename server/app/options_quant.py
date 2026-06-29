"""Modelos quantitativos educacionais para opcoes.
Stdlib-only para manter deploy simples. Nao e recomendacao de investimento.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional

TRADING_DAYS = 252


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def years_to_expiration(days: float) -> float:
    return max(float(days), 0.0) / 365.0


def historical_volatility(closes: Iterable[float], window: int = 21) -> Optional[float]:
    vals = [float(x) for x in closes if isinstance(x, (int, float)) and x > 0]
    if len(vals) < window + 1:
        return None
    tail = vals[-(window + 1):]
    rets = [math.log(tail[i] / tail[i - 1]) for i in range(1, len(tail)) if tail[i - 1] > 0]
    if len(rets) < 2:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(TRADING_DAYS)


@dataclass(frozen=True)
class BlackScholesResult:
    theoretical: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    prob_itm: float


def black_scholes(option_type: str, spot: float, strike: float, t_years: float, rate: float, vol: float, dividend_yield: float = 0.0) -> Optional[BlackScholesResult]:
    """Black-Scholes-Merton para referencia educacional.

    theta e vega retornam por dia e por 1 ponto percentual de volatilidade.
    """
    kind = (option_type or "").lower()
    if kind not in ("call", "put") or spot <= 0 or strike <= 0 or t_years <= 0 or vol <= 0:
        return None
    sqrt_t = math.sqrt(t_years)
    d1 = (math.log(spot / strike) + (rate - dividend_yield + 0.5 * vol * vol) * t_years) / (vol * sqrt_t)
    d2 = d1 - vol * sqrt_t
    df_r = math.exp(-rate * t_years)
    df_q = math.exp(-dividend_yield * t_years)
    if kind == "call":
        price = spot * df_q * _norm_cdf(d1) - strike * df_r * _norm_cdf(d2)
        delta = df_q * _norm_cdf(d1)
        theta_year = (-(spot * df_q * _norm_pdf(d1) * vol) / (2 * sqrt_t)
                      - rate * strike * df_r * _norm_cdf(d2)
                      + dividend_yield * spot * df_q * _norm_cdf(d1))
        rho = strike * t_years * df_r * _norm_cdf(d2) / 100.0
        prob_itm = _norm_cdf(d2)
    else:
        price = strike * df_r * _norm_cdf(-d2) - spot * df_q * _norm_cdf(-d1)
        delta = df_q * (_norm_cdf(d1) - 1.0)
        theta_year = (-(spot * df_q * _norm_pdf(d1) * vol) / (2 * sqrt_t)
                      + rate * strike * df_r * _norm_cdf(-d2)
                      - dividend_yield * spot * df_q * _norm_cdf(-d1))
        rho = -strike * t_years * df_r * _norm_cdf(-d2) / 100.0
        prob_itm = _norm_cdf(-d2)
    gamma = df_q * _norm_pdf(d1) / (spot * vol * sqrt_t)
    vega = spot * df_q * _norm_pdf(d1) * sqrt_t / 100.0
    return BlackScholesResult(
        theoretical=round(max(price, 0.0), 4),
        delta=round(delta, 4),
        gamma=round(gamma, 6),
        theta=round(theta_year / 365.0, 6),
        vega=round(vega, 6),
        rho=round(rho, 6),
        prob_itm=round(max(0.0, min(1.0, prob_itm)), 4),
    )


def breakeven(option_type: str, strike: float, premium: float) -> Optional[float]:
    if strike <= 0 or premium < 0:
        return None
    return round(strike + premium, 4) if (option_type or "").lower() == "call" else round(strike - premium, 4)


def intrinsic_value(option_type: str, spot: float, strike: float) -> float:
    if (option_type or "").lower() == "call":
        return round(max(0.0, spot - strike), 4)
    return round(max(0.0, strike - spot), 4)


def liquidity_score(volume: Optional[float], open_interest: Optional[float], bid: Optional[float], ask: Optional[float]) -> dict:
    v = max(0.0, float(volume or 0))
    oi = max(0.0, float(open_interest or 0))
    b = float(bid or 0)
    a = float(ask or 0)
    spread_pct = None
    spread_penalty = 25
    if a > 0 and b > 0 and a >= b:
        mid = (a + b) / 2
        spread_pct = (a - b) / mid if mid > 0 else None
        if spread_pct is not None:
            spread_penalty = 0 if spread_pct <= 0.03 else 8 if spread_pct <= 0.08 else 18 if spread_pct <= 0.18 else 30
    vol_score = min(35, math.log10(v + 1) * 12)
    oi_score = min(40, math.log10(oi + 1) * 12)
    score = max(0, min(100, vol_score + oi_score + 25 - spread_penalty))
    return {"score": round(score, 1), "spreadPct": round(spread_pct * 100, 2) if spread_pct is not None else None}


def educational_score(technical: Optional[dict], liquidity: dict, iv: Optional[float], hv21: Optional[float], days: int, prob_itm: Optional[float]) -> dict:
    trend_score = 50.0
    if technical:
        tr = str(technical.get("trend") or "").lower()
        if "alta" in tr:
            trend_score = 70
        elif "baixa" in tr:
            trend_score = 60
        elif "lateral" in tr:
            trend_score = 45
    liq = float((liquidity or {}).get("score") or 0)
    vol_score = 50.0
    if iv and hv21:
        ratio = iv / hv21 if hv21 > 0 else 1
        vol_score = 75 if 0.75 <= ratio <= 1.35 else 55 if ratio <= 1.8 else 35
    elif iv:
        vol_score = 55
    greek_score = 50.0
    expiry_score = 35 if days <= 7 else 55 if days <= 21 else 70
    prob_score = 50 if prob_itm is None else max(25, min(80, prob_itm * 100))
    total = 0.25 * trend_score + 0.20 * liq + 0.20 * vol_score + 0.15 * greek_score + 0.10 * expiry_score + 0.10 * prob_score
    label = "risco elevado / cenário fraco" if total < 40 else "cenário indefinido" if total < 60 else "cenário observável" if total < 75 else "cenário tecnicamente interessante para estudo" if total < 90 else "cenário forte para simulação educacional"
    return {"score": round(total, 1), "label": label}
