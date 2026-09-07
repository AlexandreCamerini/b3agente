"""Indicadores tecnicos calculados a partir dos candles (OHLCV).
Puro/stdlib, sem numpy/pandas, para ser testavel e leve.

Cada funcao devolve uma lista alinhada aos candles (None onde ainda nao ha
janela suficiente). compute() junta tudo + um resumo (summary) com o estado
atual de cada indicador para leitura rapida.
"""
from typing import List, Optional


def _r(x, n=2):
    return round(x, n) if isinstance(x, (int, float)) else None


def _pos(v):
    """Numero finito e POSITIVO, senao None (trata 0 e null como ausente)."""
    if isinstance(v, (int, float)) and v == v and v not in (float("inf"), float("-inf")) and v > 0:
        return float(v)
    return None


def sanitize_candles(candles, max_jump: float = 5.0):
    """Limpa candles antes de desenhar/calcular:
    - descarta candle sem fechamento valido (None/0/negativo);
    - quando open/high/low vem ausente/zero, sintetiza a partir do fechamento
      (caso classico do pregao do dia ainda em aberto no Yahoo);
    - garante high >= max(o,c) e low <= min(o,c);
    - descarta outlier absurdo (fechamento > max_jump x ou < 1/max_jump do
      fechamento valido anterior), tipico de dado corrompido que estoura a escala.
    Devolve uma nova lista; nao calcula nada sobre candles invalidos.
    """
    out = []
    prev_close = None
    for c in candles or []:
        close = _pos(c.get("close"))
        if close is None:
            continue
        if prev_close is not None and (close > prev_close * max_jump or close < prev_close / max_jump):
            continue  # provavelmente corrompido — nao deixa esticar o eixo
        o = _pos(c.get("open")) or close
        h = _pos(c.get("high")) or max(o, close)
        lo = _pos(c.get("low")) or min(o, close)
        h = max(h, o, close, lo)
        lo = min(lo, o, close, h)
        vol = c.get("volume")
        if not isinstance(vol, (int, float)) or vol != vol or vol < 0:
            vol = 0
        out.append({
            "date": c.get("date"),
            "open": round(o, 2), "high": round(h, 2), "low": round(lo, 2), "close": round(close, 2),
            "volume": vol,
        })
        prev_close = close
    return out


def sma(vals: List[float], p: int) -> List[Optional[float]]:
    out = [None] * len(vals)
    s = 0.0
    for i, v in enumerate(vals):
        s += v
        if i >= p:
            s -= vals[i - p]
        if i >= p - 1:
            out[i] = s / p
    return out


def ema(vals: List[float], p: int) -> List[Optional[float]]:
    out = [None] * len(vals)
    if len(vals) < p:
        return out
    k = 2 / (p + 1)
    prev = sum(vals[:p]) / p
    out[p - 1] = prev
    for i in range(p, len(vals)):
        prev = vals[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(closes: List[float], p: int = 14) -> List[Optional[float]]:
    out = [None] * len(closes)
    if len(closes) <= p:
        return out
    gains = losses = 0.0
    for i in range(1, p + 1):
        ch = closes[i] - closes[i - 1]
        gains += max(ch, 0.0)
        losses += max(-ch, 0.0)
    ag = gains / p
    al = losses / p
    # qa/39 (QA do operador): série FLAT (ganho=0 E perda=0) é RSI indefinido —
    # convenção neutra 50, não 100 ("sobrecomprado" falso em papel parado).
    def _rsi_val(g, l):
        if l == 0:
            return 50.0 if g == 0 else 100.0
        return 100 - 100 / (1 + g / l)
    out[p] = _rsi_val(ag, al)
    for i in range(p + 1, len(closes)):
        ch = closes[i] - closes[i - 1]
        ag = (ag * (p - 1) + max(ch, 0.0)) / p
        al = (al * (p - 1) + max(-ch, 0.0)) / p
        out[i] = _rsi_val(ag, al)
    return out


def macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    ef, es = ema(closes, fast), ema(closes, slow)
    line = [(a - b) if (a is not None and b is not None) else None for a, b in zip(ef, es)]
    idx = [i for i, x in enumerate(line) if x is not None]
    sig_in = [line[i] for i in idx]
    sig_out = ema(sig_in, signal)
    sigl = [None] * len(line)
    for j, i in enumerate(idx):
        sigl[i] = sig_out[j]
    hist = [(l - g) if (l is not None and g is not None) else None for l, g in zip(line, sigl)]
    return line, sigl, hist


def bollinger(closes: List[float], p: int = 20, k: float = 2.0):
    mid = sma(closes, p)
    up = [None] * len(closes)
    lo = [None] * len(closes)
    for i in range(len(closes)):
        if i >= p - 1:
            window = closes[i - p + 1:i + 1]
            m = mid[i]
            sd = (sum((x - m) ** 2 for x in window) / p) ** 0.5
            up[i] = m + k * sd
            lo[i] = m - k * sd
    return up, mid, lo


def _sma_skipnone(vals, p):
    out = [None] * len(vals)
    for i in range(len(vals)):
        window = [vals[j] for j in range(max(0, i - p + 1), i + 1) if vals[j] is not None]
        if len(window) == p:
            out[i] = sum(window) / p
    return out


def stochastic(highs, lows, closes, kp: int = 14, dp: int = 3):
    k = [None] * len(closes)
    for i in range(len(closes)):
        if i >= kp - 1:
            hh = max(highs[i - kp + 1:i + 1])
            ll = min(lows[i - kp + 1:i + 1])
            k[i] = 100 * (closes[i] - ll) / (hh - ll) if hh > ll else 50.0
    d = _sma_skipnone(k, dp)
    return k, d


def atr(highs, lows, closes, p: int = 14) -> List[Optional[float]]:
    n = len(closes)
    tr = [None] * n
    for i in range(n):
        if i == 0:
            tr[i] = highs[i] - lows[i]
        else:
            tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
    out = [None] * n
    if n > p:
        prev = sum(tr[1:p + 1]) / p
        out[p] = prev
        for i in range(p + 1, n):
            prev = (prev * (p - 1) + tr[i]) / p
            out[i] = prev
    return out


def adx(highs, lows, closes, p: int = 14):
    """FASE 1 (N2, família tendência): ADX(14) + DI+/DI- (suavização de Wilder).
    Mede FORÇA da tendência (não direção): ADX>=25 tendência definida; <20 fraca/
    lateral. Retorna (adx, diPlus, diMinus) alinhados aos candles, None no warmup."""
    n = len(closes)
    none = [None] * n
    if n <= p * 2:
        return none, list(none), list(none)
    tr = [0.0] * n
    pdm = [0.0] * n
    ndm = [0.0] * n
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        up = highs[i] - highs[i - 1]
        dn = lows[i - 1] - lows[i]
        pdm[i] = up if (up > dn and up > 0) else 0.0
        ndm[i] = dn if (dn > up and dn > 0) else 0.0
    atr_s = sum(tr[1:p + 1])
    pdm_s = sum(pdm[1:p + 1])
    ndm_s = sum(ndm[1:p + 1])
    di_p = [None] * n
    di_n = [None] * n
    dx = [None] * n
    for i in range(p, n):
        if i > p:
            atr_s = atr_s - atr_s / p + tr[i]
            pdm_s = pdm_s - pdm_s / p + pdm[i]
            ndm_s = ndm_s - ndm_s / p + ndm[i]
        if atr_s <= 0:
            continue
        dip = 100.0 * pdm_s / atr_s
        din = 100.0 * ndm_s / atr_s
        di_p[i] = dip
        di_n[i] = din
        den = dip + din
        dx[i] = (100.0 * abs(dip - din) / den) if den > 0 else 0.0
    out = [None] * n
    first = p * 2
    vals = [x for x in dx[p:first + 1] if x is not None]
    if vals:
        prev = sum(vals) / len(vals)
        out[first] = prev
        for i in range(first + 1, n):
            if dx[i] is None:
                out[i] = prev
                continue
            prev = (prev * (p - 1) + dx[i]) / p
            out[i] = prev
    return out, di_p, di_n


def obv(closes, volumes) -> List[Optional[float]]:
    n = len(closes)
    out = [None] * n
    if n == 0:
        return out
    acc = 0.0
    out[0] = 0.0
    for i in range(1, n):
        v = volumes[i] or 0
        if closes[i] > closes[i - 1]:
            acc += v
        elif closes[i] < closes[i - 1]:
            acc -= v
        out[i] = acc
    return out


# --------------------------- volume anormal ---------------------------------
# Origem: pergunta "dá para mapear carteiras baleias com o mydata?" (2026-09-07).
# Resposta: não — o COTAHIST é agregado por papel/pregão, sem participante.
# O que o dado permite é detectar que HOUVE dinheiro grande no papel, nunca
# QUEM. Por isso o nome é "volume anormal", deliberadamente não "baleia":
# rebalanceamento de índice, vencimento de opções e ETF produzem o mesmo
# sinal. Rótulo de causa é narrativa, não cálculo (princípio 4/7 do CLAUDE.md).
#
# Convenção da janela: média/desvio dos `p` candles ANTERIORES, excluindo o
# atual — mesma regra de `setups._ctx` (vol_med20). `technical_models.
# build_context` calcula `relativeVolume` incluindo o candle atual na média
# (21 candles com ele dentro); os dois divergem por desenho antigo, não foram
# unificados aqui — esta função é a candidata a fonte única quando isso
# acontecer.
VOL_ANORMAL_RATIO = 2.0   # ≥ 2× a média: anormal
VOL_ACIMA_RATIO = 1.5     # ≥ 1,5×: acima (mesmo corte do "Rompimento com volume")
VOL_ABAIXO_RATIO = 0.5    # ≤ 0,5×: seco


def volume_anormal(volumes, p: int = 20):
    """Devolve (ratio, z) alinhados aos candles.

    ratio[i] = volume[i] / média(volume[i-p:i]); z[i] = (volume[i] - média) /
    desvio populacional da mesma janela. None quando: não há `p` candles
    anteriores; a média da janela é 0 (papel sem negócio — sanitize_candles
    converte volume ausente em 0, então 0 e "sem dado" são indistinguíveis
    aqui e ambos contam como ausente); ou o volume atual é 0/None (mesma
    convenção de `_pos`). z é None também quando o desvio é 0 (janela
    constante — ratio continua válido).
    """
    n = len(volumes)
    ratio = [None] * n
    z = [None] * n
    if n <= p or p <= 0:
        return ratio, z
    for i in range(p, n):
        cur = _pos(volumes[i])
        if cur is None:
            continue
        win = [v if isinstance(v, (int, float)) and v == v and v > 0 else 0.0 for v in volumes[i - p:i]]
        mean = sum(win) / p
        if mean <= 0:
            continue
        ratio[i] = cur / mean
        var = sum((v - mean) ** 2 for v in win) / p
        if var > 0:
            z[i] = (cur - mean) / (var ** 0.5)
    return ratio, z


def volume_state(ratio) -> Optional[str]:
    """Estado categórico a partir da razão — só a razão decide (o z é
    informativo, para a IA explicar a magnitude, nunca critério)."""
    if ratio is None:
        return None
    if ratio >= VOL_ANORMAL_RATIO:
        return "anormal"
    if ratio >= VOL_ACIMA_RATIO:
        return "acima"
    if ratio <= VOL_ABAIXO_RATIO:
        return "abaixo"
    return "normal"


def _last(arr):
    for x in reversed(arr):
        if x is not None:
            return x
    return None


def compute(candles: List[dict]) -> dict:
    o = [c["open"] for c in candles]
    h = [c["high"] for c in candles]
    l = [c["low"] for c in candles]
    c = [c["close"] for c in candles]
    v = [c["volume"] for c in candles]

    sma20 = sma(c, 20)
    sma50 = sma(c, 50)
    sma200 = sma(c, 200)     # FASE 1 (setups BR): filtro de tendência do IFR2
    ema9 = ema(c, 9)
    ema21 = ema(c, 21)
    ema72 = ema(c, 72)       # FASE 1 (setups BR): média intermediária (9.x)
    rsi2 = rsi(c, 2)         # FASE 1 (setups BR): IFR2 de Larry Connors
    bbU, bbM, bbL = bollinger(c, 20, 2.0)
    rsi14 = rsi(c, 14)
    macdL, macdS, macdH = macd(c, 12, 26, 9)
    stochK, stochD = stochastic(h, l, c, 14, 3)
    atr14 = atr(h, l, c, 14)
    adx14, diP, diN = adx(h, l, c, 14)   # FASE 1: força da tendência
    obvv = obv(c, v)
    volR, volZ = volume_anormal(v, 20)   # volume anormal (2026-09-07): inferência sobre dado agregado

    def rr(arr, n=2):
        return [_r(x, n) for x in arr]

    indicators = {
        "sma20": rr(sma20), "sma50": rr(sma50), "sma200": rr(sma200),
        "ema9": rr(ema9), "ema21": rr(ema21), "ema72": rr(ema72),
        "rsi2": rr(rsi2, 1),
        "bbUpper": rr(bbU), "bbMiddle": rr(bbM), "bbLower": rr(bbL),
        "rsi14": rr(rsi14, 1),
        "macd": rr(macdL, 3), "macdSignal": rr(macdS, 3), "macdHist": rr(macdH, 3),
        "stochK": rr(stochK, 1), "stochD": rr(stochD, 1),
        "atr14": rr(atr14), "obv": [int(x) if x is not None else None for x in obvv],
        "adx14": rr(adx14, 1), "diPlus": rr(diP, 1), "diMinus": rr(diN, 1),
        "volRatio20": rr(volR), "volZ20": rr(volZ),
    }

    last_close = _last(c)
    s20, s50 = _last(sma20), _last(sma50)
    r = _last(rsi14)
    mh = _last(macdH)
    sk, sd = _last(stochK), _last(stochD)
    bu, bl = _last(bbU), _last(bbL)
    summary = {
        "close": _r(last_close),
        "rsi14": _r(r, 1),
        "rsiState": ("sobrecomprado" if r is not None and r >= 70 else "sobrevendido" if r is not None and r <= 30 else "neutro"),
        "macdHist": _r(mh, 3),
        "macdState": ("alta" if mh is not None and mh > 0 else "baixa" if mh is not None and mh < 0 else "neutro"),
        "stochK": _r(sk, 1), "stochD": _r(sd, 1),
        "stochState": ("sobrecomprado" if sk is not None and sk >= 80 else "sobrevendido" if sk is not None and sk <= 20 else "neutro"),
        "sma20": _r(s20), "sma50": _r(s50), "sma200": _r(_last(sma200)),
        "trend": ("alta" if (s20 is not None and s50 is not None and s20 > s50) else "baixa" if (s20 is not None and s50 is not None and s20 < s50) else "lateral"),
        "priceVsSma20": ("acima" if (last_close is not None and s20 is not None and last_close > s20) else "abaixo" if (last_close is not None and s20 is not None) else None),
        "bbUpper": _r(bu), "bbLower": _r(bl),
        "atr14": _r(_last(atr14)),
        "adx14": _r(_last(adx14), 1),
        "adxState": (lambda a: "tendência forte" if a is not None and a >= 25 else "tendência fraca/lateral" if a is not None and a < 20 else ("transição" if a is not None else None))(_last(adx14)),
    }
    # Volume anormal — lê o ÚLTIMO candle (não o último não-None): um candle
    # atual sem razão calculável é "sem dado", e herdar o de ontem mentiria.
    vr = volR[-1] if volR else None
    vz = volZ[-1] if volZ else None
    prev_close = c[-2] if len(c) >= 2 else None
    summary.update({
        "volRatio20": _r(vr),
        "volZ20": _r(vz),
        "volState": volume_state(vr),
        "volAnormal": (vr is not None and vr >= VOL_ANORMAL_RATIO),
        # direção do candle em que o volume entrou — "alta"/"baixa" é o que o
        # preço fez, não quem comprou ou vendeu.
        "volDirecao": (None if vr is None or prev_close is None or last_close is None
                       else "alta" if last_close > prev_close
                       else "baixa" if last_close < prev_close else "neutro"),
    })
    return {"indicators": indicators, "summary": summary}


def slice_tail(candles: List[dict], indicators: dict, summary: dict, keep: int) -> dict:
    """Recorta para os ultimos `keep` candles, mantendo os indicadores (que ja
    foram calculados sobre a serie completa, entao continuam validos)."""
    keep = max(1, min(keep, len(candles)))
    start = len(candles) - keep
    out_ind = {k: arr[start:] for k, arr in indicators.items()}
    return {"candles": candles[start:], "indicators": out_ind, "summary": summary}
