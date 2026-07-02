"""Modelos de analise tecnica para alimentar a LLM com dados estruturados.

O modulo calcula/compacta o que e deterministico; a LLM apenas interpreta.
Stdlib-only para manter o deploy simples no Railway e no ambiente local.
"""
from __future__ import annotations

import math
from typing import Iterable

from . import indicators

MODELS = {
    "completo": {
        "label": "Completo",
        "description": "Combina tendência, price action, momentum, volume, volatilidade, suportes/resistências e opções quando disponíveis.",
    },
    "tendencia": {"label": "Tendência", "description": "Médias, estrutura de topos/fundos e direção predominante."},
    "price_action": {"label": "Price Action", "description": "Candles, amplitude, fechamentos, suportes, resistências e rejeições."},
    "momentum": {"label": "Momentum", "description": "RSI, MACD, estocástico e aceleração do movimento."},
    "volume": {"label": "Volume", "description": "Volume relativo, OBV e confirmação do movimento."},
    "volatilidade": {"label": "Volatilidade", "description": "ATR, volatilidade histórica e regime de amplitude."},
    "suporte_resistencia": {"label": "Suporte e resistência", "description": "Níveis recentes, distância do preço e pontos de invalidação."},
    "swing_trade": {"label": "Swing trade educacional", "description": "Leitura de alguns dias/semanas com stop por ATR e níveis técnicos."},
    "opcoes": {"label": "Opções", "description": "Ativo objeto + disponibilidade de cadeia de opções no yfinance."},
}


def normalize_model(model: str | None) -> str:
    key = (model or "completo").strip().lower().replace("-", "_")
    return key if key in MODELS else "completo"


def _r(x, n=2):
    try:
        if x is None or not math.isfinite(float(x)):
            return None
        return round(float(x), n)
    except Exception:
        return None


def _last_valid(arr):
    for x in reversed(arr or []):
        if x is not None:
            return x
    return None


def _pct(a, b):
    if not a or not b:
        return None
    return _r((a - b) / b * 100, 2)


def _historical_volatility(closes: list[float], window: int) -> float | None:
    if len(closes) <= window:
        return None
    rets = []
    for i in range(len(closes) - window + 1, len(closes)):
        if closes[i - 1] > 0 and closes[i] > 0:
            rets.append(math.log(closes[i] / closes[i - 1]))
    if len(rets) < 2:
        return None
    mean = sum(rets) / len(rets)
    var = sum((x - mean) ** 2 for x in rets) / (len(rets) - 1)
    return _r(math.sqrt(var) * math.sqrt(252) * 100, 2)


def _slope(vals: list[float], lookback: int = 5) -> float | None:
    series = [x for x in vals or [] if x is not None]
    if len(series) <= lookback:
        return None
    return _pct(series[-1], series[-1 - lookback])


def _pivots(candles: list[dict], lookback: int = 80, bucket_pct: float = 1.0) -> dict:
    """Extrai níveis simples por agrupamento de máximas/mínimas recentes."""
    recent = candles[-lookback:] if len(candles) > lookback else candles[:]
    if not recent:
        return {"supports": [], "resistances": []}
    last = recent[-1]["close"]
    lows = sorted([c["low"] for c in recent if c.get("low")], reverse=True)
    highs = sorted([c["high"] for c in recent if c.get("high")])

    def cluster(vals: Iterable[float], side: str):
        levels = []
        for v in vals:
            if side == "support" and v >= last:
                continue
            if side == "resistance" and v <= last:
                continue
            if not levels or abs(v - levels[-1]) / last * 100 > bucket_pct:
                levels.append(v)
            if len(levels) >= 4:
                break
        return [_r(x) for x in levels]

    supports = cluster(lows, "support")
    resistances = cluster(highs, "resistance")
    return {"supports": supports, "resistances": resistances}


def _tail_candles(candles: list[dict], n: int = 120) -> list[dict]:
    out = []
    for c in candles[-n:]:
        out.append({
            "date": c.get("date"),
            "open": _r(c.get("open")),
            "high": _r(c.get("high")),
            "low": _r(c.get("low")),
            "close": _r(c.get("close")),
            "volume": int(c.get("volume") or 0),
        })
    return out


def build_context(ticker: str, quote: dict | None, candles: list[dict], model: str = "completo", options_status: dict | None = None, tail_n: int = 120) -> dict:
    model = normalize_model(model)
    candles = indicators.sanitize_candles(candles)
    if not candles:
        return {"ticker": ticker, "model": model, "error": "Sem candles válidos."}
    tail_n = max(20, int(tail_n) if isinstance(tail_n, (int, float)) else 120)

    comp = indicators.compute(candles)
    ind = comp.get("indicators") or {}
    summary = comp.get("summary") or {}
    closes = [c["close"] for c in candles]
    volumes = [c["volume"] for c in candles]
    last = candles[-1]
    first_21 = candles[-22] if len(candles) >= 22 else candles[0]
    first_63 = candles[-64] if len(candles) >= 64 else candles[0]
    first_252 = candles[-253] if len(candles) >= 253 else candles[0]
    piv = _pivots(candles)
    avg_vol_21 = sum(volumes[-21:]) / min(21, len(volumes)) if volumes else None
    rel_vol = (volumes[-1] / avg_vol_21) if avg_vol_21 else None
    atr14 = summary.get("atr14")
    atr_pct = _r((atr14 / last["close"] * 100), 2) if atr14 and last.get("close") else None
    ema9 = _last_valid(ind.get("ema9"))
    ema21 = _last_valid(ind.get("ema21"))
    sma20 = summary.get("sma20")
    sma50 = summary.get("sma50")
    macd_hist = summary.get("macdHist")
    rsi = summary.get("rsi14")

    trend_bias = "lateral/indefinido"
    if last["close"] and ema9 and ema21 and sma50:
        if last["close"] > ema9 > ema21 and last["close"] > sma50:
            trend_bias = "alta"
        elif last["close"] < ema9 < ema21 and last["close"] < sma50:
            trend_bias = "baixa"

    support = piv["supports"][0] if piv["supports"] else None
    resistance = piv["resistances"][0] if piv["resistances"] else None

    stop_reference = None
    target_reference = None
    if support and atr14:
        stop_reference = _r(min(support, last["close"] - atr14))
    elif atr14:
        stop_reference = _r(last["close"] - atr14)
    if resistance:
        target_reference = _r(resistance)
    elif atr14:
        target_reference = _r(last["close"] + 2 * atr14)

    context = {
        "ticker": ticker,
        "source": "yfinance",
        "model": model,
        "modelLabel": MODELS[model]["label"],
        "modelDescription": MODELS[model]["description"],
        "asOf": last.get("date"),
        "quote": quote or {},
        "lastCandle": last,
        "historyStats": {
            "candlesAvailable": len(candles),
            "candlesSentToLLM": min(len(candles), tail_n),
            "change21dPct": _pct(last["close"], first_21["close"]),
            "change63dPct": _pct(last["close"], first_63["close"]),
            "change252dPct": _pct(last["close"], first_252["close"]),
            "high63": _r(max(c["high"] for c in candles[-63:])),
            "low63": _r(min(c["low"] for c in candles[-63:])),
        },
        "trend": {
            "bias": trend_bias,
            "ema9": _r(ema9),
            "ema21": _r(ema21),
            "sma20": _r(sma20),
            "sma50": _r(sma50),
            "priceVsSma20": summary.get("priceVsSma20"),
            "ema9Slope5Pct": _slope(ind.get("ema9") or [], 5),
            "sma20Slope5Pct": _slope(ind.get("sma20") or [], 5),
        },
        "momentum": {
            "rsi14": _r(rsi, 1),
            "rsiState": summary.get("rsiState"),
            "macdHist": _r(macd_hist, 3),
            "macdState": summary.get("macdState"),
            "stochK": summary.get("stochK"),
            "stochD": summary.get("stochD"),
            "stochState": summary.get("stochState"),
        },
        "volume": {
            "lastVolume": int(volumes[-1] or 0),
            "avgVolume21": int(avg_vol_21 or 0),
            "relativeVolume": _r(rel_vol, 2),
            "obvLast": _last_valid(ind.get("obv")),
            "obvSlope21Pct": _slope(ind.get("obv") or [], 21),
        },
        "volatility": {
            "atr14": _r(atr14),
            "atr14Pct": atr_pct,
            "hv21Pct": _historical_volatility(closes, 21),
            "hv63Pct": _historical_volatility(closes, 63),
            "bollingerUpper": summary.get("bbUpper"),
            "bollingerLower": summary.get("bbLower"),
        },
        "levels": {
            "supports": piv["supports"],
            "resistances": piv["resistances"],
            "nearestSupport": support,
            "nearestResistance": resistance,
            "distanceToSupportPct": _pct(last["close"], support) if support else None,
            "distanceToResistancePct": _pct(resistance, last["close"]) if resistance else None,
        },
        "riskPlanReference": {
            "stopReference": stop_reference,
            "targetReference": target_reference,
            "riskPerShare": _r(last["close"] - stop_reference) if stop_reference else None,
            "rewardPerShare": _r(target_reference - last["close"]) if target_reference else None,
        },
        "options": options_status or {"available": None, "reason": "Não consultado para este modelo."},
        "candles": _tail_candles(candles, tail_n),
    }

    # Recorte semântico: mantemos candles sempre, mas destacamos o bloco do modelo escolhido.
    context["focus"] = {
        "tendencia": context["trend"],
        "price_action": {"lastCandle": last, "levels": context["levels"], "volatility": context["volatility"]},
        "momentum": context["momentum"],
        "volume": context["volume"],
        "volatilidade": context["volatility"],
        "suporte_resistencia": context["levels"],
        "swing_trade": {"trend": context["trend"], "levels": context["levels"], "riskPlanReference": context["riskPlanReference"], "volatility": context["volatility"]},
        "opcoes": {"options": context["options"], "underlyingTrend": context["trend"], "underlyingVolatility": context["volatility"]},
        "completo": "Usar todos os blocos.",
    }.get(model)
    return context


def compact_for_response(ctx: dict) -> dict:
    """Payload menor para o cliente: suficiente para auditoria sem poluir a UI."""
    return {
        "ticker": ctx.get("ticker"),
        "model": ctx.get("model"),
        "modelLabel": ctx.get("modelLabel"),
        "asOf": ctx.get("asOf"),
        "historyStats": ctx.get("historyStats"),
        "trend": ctx.get("trend"),
        "momentum": ctx.get("momentum"),
        "volume": ctx.get("volume"),
        "volatility": ctx.get("volatility"),
        "levels": ctx.get("levels"),
        "riskPlanReference": ctx.get("riskPlanReference"),
        "options": ctx.get("options"),
    }
