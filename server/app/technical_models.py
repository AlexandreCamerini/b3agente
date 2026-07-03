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


def _candle_patterns(candles: list[dict], lookback: int = 10) -> list[dict]:
    """FASE 1 (N2, família price action): padrões CLÁSSICOS detectados por regra
    determinística na cauda da janela — a LLM interpreta o CONTEXTO (onde o
    padrão apareceu), nunca detecta. Rótulos descritivos, sem verbo de ordem."""
    out = []
    cs = [c for c in (candles or []) if all(c.get(k) is not None for k in ("open", "high", "low", "close"))]
    tail = cs[-lookback:]
    for idx, c in enumerate(tail):
        o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
        rng = h - l
        if rng <= 0:
            continue
        body = abs(cl - o)
        upper = h - max(o, cl)
        lower = min(o, cl) - l
        prev = tail[idx - 1] if idx > 0 else None

        def add(nome, leitura):
            out.append({"padrao": nome, "data": c.get("date"), "leitura": leitura})

        if body <= 0.1 * rng:
            add("Doji", "Indecisão: abertura e fechamento praticamente iguais — corpo ≤10% da amplitude.")
        elif lower >= 2 * body and upper <= 0.3 * rng:
            add("Martelo", "Sombra inferior ≥2× o corpo: rejeição de preços mais baixos na sessão.")
        elif upper >= 2 * body and lower <= 0.3 * rng:
            add("Estrela cadente", "Sombra superior ≥2× o corpo: rejeição de preços mais altos na sessão.")
        if prev is not None:
            po, pc = prev["open"], prev["close"]
            if pc < po and cl > o and cl >= po and o <= pc:
                add("Engolfo de alta", "Corpo de alta envolve o corpo de baixa anterior.")
            elif pc > po and cl < o and cl <= po and o >= pc:
                add("Engolfo de baixa", "Corpo de baixa envolve o corpo de alta anterior.")
    return out[-6:]


def _families(context: dict, summary: dict, patterns: list[dict]) -> dict:
    """FASE 1 (N2): leitura DETERMINÍSTICA por família + síntese de confluência
    ENTRE famílias. A LLM recebe isto pronto e explica — não decide direção.
    Vocabulário fixo educacional: viés 'alta' | 'baixa' | 'neutro'."""
    trend = context.get("trend") or {}
    momentum = context.get("momentum") or {}
    vol = context.get("volatility") or {}
    volu = context.get("volume") or {}
    adx = summary.get("adx14")
    adx_state = summary.get("adxState")

    f_trend = {
        "vies": trend.get("bias") if trend.get("bias") in ("alta", "baixa") else "neutro",
        "leitura": "Preço vs. médias (EMA9/21, SMA50) define o viés estrutural; ADX mede a força.",
        "adx14": adx, "adxState": adx_state,
    }
    mh = momentum.get("macdHist")
    f_mom = {
        "vies": ("alta" if isinstance(mh, (int, float)) and mh > 0 else "baixa" if isinstance(mh, (int, float)) and mh < 0 else "neutro"),
        "leitura": "Histograma MACD dá o sinal principal; RSI/estocástico marcam extremos e divergências.",
        "rsiState": momentum.get("rsiState"), "stochState": momentum.get("stochState"),
    }
    bw = None
    bu, bl = vol.get("bollingerUpper"), vol.get("bollingerLower")
    close = (context.get("lastCandle") or {}).get("close")
    if bu and bl and close:
        bw = round((bu - bl) / close * 100, 2)
    f_vol = {
        "vies": "neutro",  # volatilidade descreve REGIME, não direção
        "leitura": "ATR% e largura das bandas descrevem o regime (compressão × expansão) — calibra stop e ruído esperado.",
        "atr14Pct": vol.get("atr14Pct"), "larguraBandasPct": bw,
        "regime": ("compressão" if isinstance(bw, (int, float)) and bw < 6 else "expansão" if isinstance(bw, (int, float)) and bw > 12 else "normal" if bw is not None else None),
    }
    pa_vies = "neutro"
    if patterns:
        last_p = patterns[-1]["padrao"]
        pa_vies = "alta" if last_p in ("Engolfo de alta", "Martelo") else "baixa" if last_p in ("Engolfo de baixa", "Estrela cadente") else "neutro"
    f_pa = {
        "vies": pa_vies,
        "leitura": "Padrões de candle da janela + posição do preço vs. níveis; o CONTEXTO do padrão pesa mais que o padrão isolado.",
        "padroes": patterns,
    }
    obv_slope = volu.get("obvSlope21Pct")
    f_volu = {
        "vies": ("alta" if isinstance(obv_slope, (int, float)) and obv_slope > 0 else "baixa" if isinstance(obv_slope, (int, float)) and obv_slope < 0 else "neutro"),
        "leitura": "OBV e volume relativo confirmam (ou negam) o movimento do preço — rompimento sem volume não se confirma.",
        "volumeRelativo": volu.get("relativeVolume"), "obvSlope21Pct": obv_slope,
    }
    direcionais = {"tendencia": f_trend["vies"], "momentum": f_mom["vies"], "priceAction": f_pa["vies"], "volume": f_volu["vies"]}
    n_alta = sum(1 for v in direcionais.values() if v == "alta")
    n_baixa = sum(1 for v in direcionais.values() if v == "baixa")
    dominante = "alta" if n_alta > n_baixa else "baixa" if n_baixa > n_alta else "neutro"
    sintese = (
        f"{max(n_alta, n_baixa)} de 4 famílias direcionais com viés de {dominante}"
        if dominante != "neutro" else "Famílias direcionais divididas — sem viés dominante"
    ) + (f"; volatilidade em regime de {f_vol['regime']}." if f_vol.get("regime") else ".")
    return {
        "tendencia": f_trend, "momentum": f_mom, "volatilidade": f_vol,
        "priceAction": f_pa, "volume": f_volu,
        "confluenciaEntreFamilias": {"altaDe4": n_alta, "baixaDe4": n_baixa, "viesDominante": dominante, "sintese": sintese},
    }


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

    # FASE 1 (N2): padrões de candle da janela + leitura por família com
    # síntese de confluência ENTRE famílias — tudo determinístico; a LLM explica.
    patterns = _candle_patterns(context["candles"])
    context["priceActionPatterns"] = patterns
    context["families"] = _families(context, summary, patterns)
    # Validação do contrato de dados (skill analise-tecnica-b3): a LLM é
    # instruída a DECLARAR limitações em vez de compensá-las com inferência.
    vols_missing = any((c.get("volume") in (None, 0)) for c in context["candles"][-20:]) if context["candles"] else True
    context["dataQuality"] = {
        "candles": len(candles),
        "serieCurta": len(candles) < 50,
        "estruturaSemConfianca": len(candles) < 20,
        "volumeAusente": vols_missing,
        "multiTimeframe": False,  # hoje só diário — teto de confiança 'moderada'
        "tetoConfianca": ("baixa" if len(candles) < 20 else "moderada"),
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
