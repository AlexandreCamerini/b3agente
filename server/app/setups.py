"""BLOCO B — Setups técnicos clássicos (Radar v2). Puro e testável.

Modelo: CONFLUÊNCIA educacional. Cada setup é um padrão didático consagrado de
análise técnica, descrito como um CHECKLIST de critérios objetivos. O grau de
confluência (0–100) é o percentual ponderado de critérios atendidos — mede
ADERÊNCIA do ativo ao padrão em dados PASSADOS, nunca probabilidade de
resultado nem sinal de operação.

Veredito por ativo usa SOMENTE o vocabulário educacional do produto:
  "Estudar alta" · "Estudar baixa" · "Monitorar" · "Sem setup no momento".
Guardrail inegociável: nenhum texto imperativo de operação.

Setups cobertos (melhores práticas didáticas):
  • Pullback à média (alta/baixa): tendência definida (SMA20×SMA50) + preço
    reencontrando a SMA20 + RSI neutro (40–60) — o clássico "correção dentro
    da tendência";
  • Rompimento com volume (alta/baixa): fechamento além do extremo dos últimos
    N candles DO PERÍODO DO USUÁRIO com volume ≥ 1,5× a média de 20;
  • Reversão de sobrevenda/sobrecompra: RSI em extremo + candle de força
    (fechamento no terço da ponta) + estocástico cruzando na direção contrária
    ao extremo;
  • Compressão de volatilidade (contexto, sem direção): largura das Bandas de
    Bollinger no quartil inferior do período — precede expansões.
"""
from typing import Optional

# Janela de "recente" para eventos (cruzamentos etc.), em candles.
RECENT = 3


# ------------------------------ utilitários ---------------------------------

def _last(arr, default=None):
    for v in reversed(arr or []):
        if v is not None:
            return v
    return default


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return (sum(vals) / len(vals)) if vals else None


def _crossed_up(a_arr, b_arr, n=RECENT):
    pairs = [(a, b) for a, b in zip(a_arr or [], b_arr or []) if a is not None and b is not None]
    if len(pairs) < 2:
        return False
    tail = pairs[-(n + 1):]
    return any(p[0] <= p[1] and q[0] > q[1] for p, q in zip(tail, tail[1:]))


def _crossed_down(a_arr, b_arr, n=RECENT):
    pairs = [(a, b) for a, b in zip(a_arr or [], b_arr or []) if a is not None and b is not None]
    if len(pairs) < 2:
        return False
    tail = pairs[-(n + 1):]
    return any(p[0] >= p[1] and q[0] < q[1] for p, q in zip(tail, tail[1:]))


def _crit(label: str, ok: bool, weight: int, obrigatorio: bool = False) -> dict:
    """`obrigatorio=True` marca o critério que DEFINE o setup — sem ele, o
    padrão não existe (ex.: pullback sem tendência é só preço perto da média).
    O setup só conta se todos os obrigatórios estiverem presentes."""
    return {"criterio": label, "ok": bool(ok), "peso": weight, "obrigatorio": bool(obrigatorio)}


def _confluencia(criterios: list) -> int:
    total = sum(c["peso"] for c in criterios) or 1
    got = sum(c["peso"] for c in criterios if c["ok"])
    return round(100 * got / total)


# ------------------------------- setups -------------------------------------

def _ctx(candles: list, ind: dict):
    """Extrai o estado bruto usado pelos setups (uma vez, compartilhado)."""
    closes = [c.get("close") for c in candles or []]
    highs = [c.get("high") for c in candles or []]
    lows = [c.get("low") for c in candles or []]
    vols = [c.get("volume") for c in candles or []]
    last = candles[-1] if candles else {}
    sma20 = _last(ind.get("sma20"))
    sma50 = _last(ind.get("sma50"))
    rsi = _last(ind.get("rsi14"))
    bbu = _last(ind.get("bbUpper"))
    bbl = _last(ind.get("bbLower"))
    close = last.get("close")
    rng = (last.get("high") or 0) - (last.get("low") or 0)
    pos_in_candle = ((close - last.get("low")) / rng) if (rng and close is not None and last.get("low") is not None) else None
    vol_med20 = _mean([v for v in vols[-21:-1] if v]) if len(vols) > 1 else None
    vol_ratio = (vols[-1] / vol_med20) if (vols and vols[-1] and vol_med20) else None
    return {
        "closes": closes, "highs": highs, "lows": lows, "last": last,
        "close": close, "sma20": sma20, "sma50": sma50, "rsi": rsi,
        "bbu": bbu, "bbl": bbl, "pos_in_candle": pos_in_candle,
        "vol_ratio": vol_ratio, "ind": ind,
        # FASE 1 (setups BR): séries/valores extras compartilhados
        "candles": candles or [],
        "ema9_arr": ind.get("ema9") or [],
        "ema21": _last(ind.get("ema21")),
        "sma200": _last(ind.get("sma200")),
        "rsi2": _last(ind.get("rsi2")),
        "adx": _last(ind.get("adx14")),
        "di_plus": _last(ind.get("diPlus")),
        "di_minus": _last(ind.get("diMinus")),
        "atr": _last(ind.get("atr14")),
    }


def _setup_pullback(c, lado: str) -> dict:
    alta = lado == "alta"
    trend_ok = (c["sma20"] is not None and c["sma50"] is not None and
                (c["sma20"] > c["sma50"] if alta else c["sma20"] < c["sma50"]))
    perto_sma = (c["close"] is not None and c["sma20"] and
                 abs(c["close"] - c["sma20"]) / c["sma20"] <= 0.02)
    lado_certo = (c["close"] is not None and c["sma20"] is not None and
                  (c["close"] >= c["sma20"] * 0.98 if alta else c["close"] <= c["sma20"] * 1.02))
    rsi_neutro = c["rsi"] is not None and 40 <= c["rsi"] <= 60
    criterios = [
        _crit("Tendência de %s (SMA20 %s SMA50)" % (("alta", "acima da") if alta else ("baixa", "abaixo da")), trend_ok, 3, obrigatorio=True),
        _crit("Preço reencontrando a SMA20 (±2%)", bool(perto_sma and lado_certo), 3),
        _crit("RSI neutro (40–60) — correção sem perda de força", rsi_neutro, 2),
    ]
    return {"nome": "Pullback à média (%s)" % lado, "lado": lado,
            "criterios": criterios, "confluencia": _confluencia(criterios)}


def _setup_rompimento(c, lado: str) -> dict:
    alta = lado == "alta"
    ref = c["highs"][:-1] if alta else c["lows"][:-1]
    ref = [v for v in ref if v is not None]
    extremo = (max(ref) if alta else min(ref)) if ref else None
    rompeu = (c["close"] is not None and extremo is not None and
              (c["close"] > extremo if alta else c["close"] < extremo))
    vol_ok = c["vol_ratio"] is not None and c["vol_ratio"] >= 1.5
    fechamento_firme = (c["pos_in_candle"] is not None and
                        (c["pos_in_candle"] >= 0.67 if alta else c["pos_in_candle"] <= 0.33))
    criterios = [
        _crit("Fechamento além da %s do período analisado" % ("máxima" if alta else "mínima"), rompeu, 4, obrigatorio=True),
        _crit("Volume ≥ 1,5× a média de 20 candles", vol_ok, 3),
        _crit("Fechamento no terço %s do candle" % ("superior" if alta else "inferior"), fechamento_firme, 1),
    ]
    return {"nome": "Rompimento com volume (%s)" % lado, "lado": lado,
            "criterios": criterios, "confluencia": _confluencia(criterios)}


def _setup_reversao(c, lado: str) -> dict:
    # lado = direção ESTUDADA após o extremo: "alta" reverte sobrevenda;
    # "baixa" reverte sobrecompra.
    alta = lado == "alta"
    extremo_ok = c["rsi"] is not None and (c["rsi"] <= 30 if alta else c["rsi"] >= 70)
    forca = (c["pos_in_candle"] is not None and
             (c["pos_in_candle"] >= 0.67 if alta else c["pos_in_candle"] <= 0.33))
    stoch = (_crossed_up(c["ind"].get("stochK"), c["ind"].get("stochD")) if alta
             else _crossed_down(c["ind"].get("stochK"), c["ind"].get("stochD")))
    criterios = [
        _crit("RSI em %s (%s)" % (("sobrevenda", "≤ 30") if alta else ("sobrecompra", "≥ 70")), extremo_ok, 3, obrigatorio=True),
        _crit("Candle de força (fechamento no terço %s)" % ("superior" if alta else "inferior"), forca, 2),
        _crit("Estocástico cruzando para %s (%%K × %%D)" % ("cima" if alta else "baixo"), stoch, 2),
    ]
    return {"nome": "Reversão de %s" % ("sobrevenda" if alta else "sobrecompra"), "lado": lado,
            "criterios": criterios, "confluencia": _confluencia(criterios)}


def _setup_compressao(c) -> dict:
    ind = c["ind"]
    widths = []
    for u, l, m in zip(ind.get("bbUpper") or [], ind.get("bbLower") or [], ind.get("sma20") or []):
        if u is not None and l is not None and m:
            widths.append((u - l) / m)
    atual = widths[-1] if widths else None
    q1 = sorted(widths)[max(0, len(widths) // 4 - 1)] if len(widths) >= 8 else None
    comprimido = atual is not None and q1 is not None and atual <= q1
    criterios = [
        _crit("Largura das Bandas de Bollinger no quartil inferior do período", bool(comprimido), 3),
        _crit("Histórico suficiente para o cálculo (≥ 8 leituras de banda)", len(widths) >= 8, 1),
    ]
    return {"nome": "Compressão de volatilidade (contexto, sem direção)", "lado": "neutro",
            "criterios": criterios, "confluencia": _confluencia(criterios)}


# =============================================================================
# FASE 1 — Setups testados do mercado brasileiro (detectores puros, sem LLM).
# Cada detector devolve o shape existente + campos operacionais EDUCACIONAIS:
#   gatilho      — nível de rompimento que ativaria o ESTUDO do padrão;
#   invalidacao  — nível que nega o padrão (stop didático);
#   alvoSugerido — projeção didática (R:R 2:1 ou regra própria do setup);
#   referencia   — origem/difusão do setup (auditável em qa/SETUPS.md);
#   backtestavel — True (regras 100% objetivas).
# Nenhum campo é ordem de operação: o LLM traduz para o vocabulário fixo
# ("setup 9.1 detectado → Estudar alta com gatilho em R$ X").
# =============================================================================

def _valid_tail(arr, n):
    vals = [v for v in arr or [] if v is not None]
    return vals[-n:] if len(vals) >= n else []


def _rr2(x):
    return round(float(x), 2) if isinstance(x, (int, float)) else None


def _alvo_rr(gatilho, invalidacao, atr=None, alta=True):
    """Projeção didática: 2× o risco a partir do gatilho; fallback 2×ATR."""
    if gatilho is not None and invalidacao is not None and gatilho != invalidacao:
        risco = abs(gatilho - invalidacao)
        return _rr2(gatilho + 2 * risco if alta else gatilho - 2 * risco)
    if gatilho is not None and atr:
        return _rr2(gatilho + 2 * atr if alta else gatilho - 2 * atr)
    return None


def _mk(nome, lado, criterios, gatilho, invalidacao, alvo, referencia):
    return {
        "nome": nome, "lado": lado, "criterios": criterios,
        "confluencia": _confluencia(criterios),
        "gatilho": _rr2(gatilho), "invalidacao": _rr2(invalidacao),
        "alvoSugerido": alvo, "referencia": referencia, "backtestavel": True,
    }


def _setup_9_1(c, lado: str) -> dict:
    """Setup 9.1 (Stormer): virada da MME9 + rompimento do candle da virada."""
    alta = lado == "alta"
    e = _valid_tail(c["ema9_arr"], 3)
    virou = (len(e) == 3 and
             ((e[1] < e[0] and e[2] > e[1]) if alta else (e[1] > e[0] and e[2] < e[1])))
    last = c["last"]
    ema9 = e[-1] if e else None
    fech_lado = (c["close"] is not None and ema9 is not None and
                 (c["close"] > ema9 if alta else c["close"] < ema9))
    vol_ok = c["vol_ratio"] is not None and c["vol_ratio"] >= 1.0
    criterios = [
        _crit("MME9 virou para %s no último candle" % ("cima" if alta else "baixo"), virou, 4, obrigatorio=True),
        _crit("Fechamento %s da MME9" % ("acima" if alta else "abaixo"), fech_lado, 2),
        _crit("Volume ≥ média de 20 candles", vol_ok, 1),
    ]
    gat = last.get("high") if alta else last.get("low")
    inv = last.get("low") if alta else last.get("high")
    return _mk("Setup 9.1 (%s)" % lado, lado, criterios, gat, inv,
               _alvo_rr(gat, inv, c["atr"], alta), "Alexandre Wolwacz (Stormer)")


def _setup_9_2(c, lado: str) -> dict:
    """Setup 9.2 (Stormer): correção de 1 candle com a MME9 ainda a favor."""
    alta = lado == "alta"
    e = _valid_tail(c["ema9_arr"], 2)
    mme_favor = len(e) == 2 and (e[1] > e[0] if alta else e[1] < e[0])
    cl = [x for x in c["closes"] if x is not None]
    correcao = len(cl) >= 2 and (cl[-1] < cl[-2] if alta else cl[-1] > cl[-2])
    last = c["last"]
    criterios = [
        _crit("MME9 %s (tendência preservada)" % ("subindo" if alta else "caindo"), mme_favor, 3, obrigatorio=True),
        _crit("Candle de correção (fechamento %s que o anterior)" % ("menor" if alta else "maior"), correcao, 3, obrigatorio=True),
        _crit("RSI fora do extremo contrário", c["rsi"] is not None and (c["rsi"] > 30 if alta else c["rsi"] < 70), 1),
    ]
    gat = last.get("high") if alta else last.get("low")
    inv = last.get("low") if alta else last.get("high")
    return _mk("Setup 9.2 (%s)" % lado, lado, criterios, gat, inv,
               _alvo_rr(gat, inv, c["atr"], alta), "Alexandre Wolwacz (Stormer)")


def _setup_9_3(c, lado: str) -> dict:
    """Setup 9.3 (Stormer): retomada após correção, MME9 a favor."""
    alta = lado == "alta"
    e = _valid_tail(c["ema9_arr"], 2)
    mme_favor = len(e) == 2 and (e[1] > e[0] if alta else e[1] < e[0])
    cl = [x for x in c["closes"] if x is not None]
    houve_correcao = len(cl) >= 3 and (cl[-2] < cl[-3] if alta else cl[-2] > cl[-3])
    retomada = len(cl) >= 2 and (cl[-1] > cl[-2] if alta else cl[-1] < cl[-2])
    last = c["last"]
    lows = [x for x in c["lows"] if x is not None]
    highs = [x for x in c["highs"] if x is not None]
    inv = (min(lows[-2:]) if alta else max(highs[-2:])) if (lows if alta else highs) else None
    criterios = [
        _crit("MME9 %s (tendência preservada)" % ("subindo" if alta else "caindo"), mme_favor, 3, obrigatorio=True),
        _crit("Correção no candle anterior", houve_correcao, 2, obrigatorio=True),
        _crit("Retomada (fechamento %s que o anterior)" % ("maior" if alta else "menor"), retomada, 3, obrigatorio=True),
    ]
    gat = last.get("high") if alta else last.get("low")
    return _mk("Setup 9.3 (%s)" % lado, lado, criterios, gat, inv,
               _alvo_rr(gat, inv, c["atr"], alta), "Alexandre Wolwacz (Stormer)")


def _setup_ifr2(c) -> dict:
    """IFR2 (Larry Connors): RSI(2) em sobrevenda com preço acima da MMA200.
    Setup de FECHAMENTO (sem rompimento): saída didática na máxima dos 2
    candles anteriores; Connors não usa stop — invalidação didática por ATR."""
    sobrevenda = c["rsi2"] is not None and c["rsi2"] <= 25
    tendencia = (c["close"] is not None and c["sma200"] is not None and c["close"] > c["sma200"])
    extremo = c["rsi2"] is not None and c["rsi2"] <= 10
    highs = [x for x in c["highs"] if x is not None]
    alvo = _rr2(max(highs[-3:-1])) if len(highs) >= 3 else None
    inv = _rr2(c["last"].get("low") - c["atr"]) if (c["last"].get("low") is not None and c["atr"]) else c["last"].get("low")
    criterios = [
        _crit("RSI(2) ≤ 25 (sobrevenda de curtíssimo prazo)", sobrevenda, 3, obrigatorio=True),
        _crit("Preço acima da MMA200 (filtro de tendência)", tendencia, 3, obrigatorio=True),
        _crit("RSI(2) ≤ 10 (sobrevenda extrema)", extremo, 1),
    ]
    return _mk("IFR2 (alta)", "alta", criterios, c["close"], inv, alvo,
               "Larry Connors — muito testado em ações BR")


def _setup_pfr(c, lado: str) -> dict:
    """PFR (Stormer): mínima mais baixa que as 2 anteriores + fechamento acima
    do anterior (compra); espelho na venda."""
    alta = lado == "alta"
    lows = [x for x in c["lows"] if x is not None]
    highs = [x for x in c["highs"] if x is not None]
    cl = [x for x in c["closes"] if x is not None]
    if alta:
        extremo = len(lows) >= 3 and lows[-1] < lows[-2] and lows[-1] < lows[-3]
    else:
        extremo = len(highs) >= 3 and highs[-1] > highs[-2] and highs[-1] > highs[-3]
    fech = len(cl) >= 2 and (cl[-1] > cl[-2] if alta else cl[-1] < cl[-2])
    forca = (c["pos_in_candle"] is not None and
             (c["pos_in_candle"] >= 0.67 if alta else c["pos_in_candle"] <= 0.33))
    last = c["last"]
    criterios = [
        _crit("%s que os 2 candles anteriores" % ("Mínima mais baixa" if alta else "Máxima mais alta"), extremo, 3, obrigatorio=True),
        _crit("Fechamento %s que o fechamento anterior" % ("acima" if alta else "abaixo"), fech, 3, obrigatorio=True),
        _crit("Fechamento no terço %s do candle" % ("superior" if alta else "inferior"), forca, 1),
    ]
    gat = last.get("high") if alta else last.get("low")
    inv = last.get("low") if alta else last.get("high")
    return _mk("PFR (%s)" % lado, lado, criterios, gat, inv,
               _alvo_rr(gat, inv, c["atr"], alta), "Alexandre Wolwacz (Stormer)")


def _pivots_123(candles: list, lado: str, lookback: int = 12):
    """Estrutura 1-2-3 nos últimos `lookback` candles (pivôs com asa de 1).
    Compra: fundo(1) → topo(2) → fundo mais alto(3). Venda: espelho."""
    cs = [x for x in (candles or [])[-lookback:] if x.get("low") is not None and x.get("high") is not None]
    if len(cs) < 5:
        return None
    fundos = [i for i in range(1, len(cs) - 1) if cs[i]["low"] < cs[i - 1]["low"] and cs[i]["low"] < cs[i + 1]["low"]]
    topos = [i for i in range(1, len(cs) - 1) if cs[i]["high"] > cs[i - 1]["high"] and cs[i]["high"] > cs[i + 1]["high"]]
    if lado == "alta":
        for i3 in reversed(fundos):
            meio = [i2 for i2 in topos if i2 < i3]
            if not meio:
                continue
            i2 = meio[-1]
            antes = [i1 for i1 in fundos if i1 < i2]
            if not antes:
                continue
            i1 = antes[-1]
            if cs[i3]["low"] > cs[i1]["low"]:
                return {"p1": cs[i1], "p2": cs[i2], "p3": cs[i3]}
        return None
    for i3 in reversed(topos):
        meio = [i2 for i2 in fundos if i2 < i3]
        if not meio:
            continue
        i2 = meio[-1]
        antes = [i1 for i1 in topos if i1 < i2]
        if not antes:
            continue
        i1 = antes[-1]
        if cs[i3]["high"] < cs[i1]["high"]:
            return {"p1": cs[i1], "p2": cs[i2], "p3": cs[i3]}
    return None


def _setup_123(c, lado: str) -> dict:
    """123 clássico: fundo(1), topo(2), fundo mais alto(3) → rompimento do 2."""
    alta = lado == "alta"
    piv = _pivots_123(c["candles"], lado)
    estrutura = piv is not None
    gat = (piv["p2"]["high"] if alta else piv["p2"]["low"]) if piv else None
    inv = (piv["p3"]["low"] if alta else piv["p3"]["high"]) if piv else None
    pendente = (estrutura and c["close"] is not None and
                (c["close"] <= gat if alta else c["close"] >= gat))
    criterios = [
        _crit("Estrutura 1-2-3 de %s formada (pivôs objetivos)" % lado, estrutura, 4, obrigatorio=True),
        _crit("Gatilho (ponto 2) ainda não rompido — padrão armado", bool(pendente), 2),
        _crit("Tendência de fundo favorável (SMA20 × SMA50)",
              c["sma20"] is not None and c["sma50"] is not None and
              (c["sma20"] > c["sma50"] if alta else c["sma20"] < c["sma50"]), 1),
    ]
    return _mk("123 de %s" % ("fundo (alta)" if alta else "topo (baixa)"), lado, criterios, gat, inv,
               _alvo_rr(gat, inv, c["atr"], alta), "Clássico, difundido no BR")


def _setup_ponto_continuo(c, lado: str) -> dict:
    """Ponto Contínuo (Dunnigan): preço reencontra a MME21 em tendência
    definida pelo ADX → estudo de retomada na direção da tendência."""
    alta = lado == "alta"
    adx_ok = c["adx"] is not None and c["adx"] >= 25
    di_ok = (c["di_plus"] is not None and c["di_minus"] is not None and
             (c["di_plus"] > c["di_minus"] if alta else c["di_minus"] > c["di_plus"]))
    last = c["last"]
    e21 = c["ema21"]
    toque = (e21 is not None and last.get("low") is not None and last.get("high") is not None and
             (last["low"] <= e21 <= last["high"] or
              (c["close"] is not None and abs(c["close"] - e21) / e21 <= 0.01)))
    criterios = [
        _crit("ADX ≥ 25 (tendência definida)", adx_ok, 3, obrigatorio=True),
        _crit("DI%s dominante (direção da tendência)" % ("+" if alta else "−"), di_ok, 2, obrigatorio=True),
        _crit("Preço reencontrando a MME21 (toque ou ±1%)", bool(toque), 3, obrigatorio=True),
    ]
    gat = last.get("high") if alta else last.get("low")
    inv = last.get("low") if alta else last.get("high")
    return _mk("Ponto Contínuo (%s)" % lado, lado, criterios, gat, inv,
               _alvo_rr(gat, inv, c["atr"], alta), "Dunnigan, popular no BR")


def _setup_inside_bar(c) -> dict:
    """Inside Bar: candle contido no anterior + filtro de tendência (o lado
    estudado é o da tendência; sem tendência definida, o padrão não conta)."""
    cs = c["candles"]
    if len(cs) < 2:
        mae = filho = None
    else:
        mae, filho = cs[-2], cs[-1]
    contido = (mae and filho and mae.get("high") is not None and filho.get("high") is not None and
               filho["high"] <= mae["high"] and filho["low"] >= mae["low"])
    tendencia = None
    if c["sma20"] is not None and c["sma50"] is not None:
        tendencia = "alta" if c["sma20"] > c["sma50"] else ("baixa" if c["sma20"] < c["sma50"] else None)
    alta = tendencia == "alta"
    compress = (contido and (mae["high"] - mae["low"]) > 0 and
                (filho["high"] - filho["low"]) <= 0.6 * (mae["high"] - mae["low"]))
    criterios = [
        _crit("Candle contido no anterior (inside bar)", bool(contido), 3, obrigatorio=True),
        _crit("Tendência definida (SMA20 × SMA50) dando o lado do estudo", tendencia is not None, 3, obrigatorio=True),
        _crit("Compressão forte (amplitude ≤ 60% do candle-mãe)", bool(compress), 1),
    ]
    lado = tendencia or "neutro"
    gat = (mae.get("high") if alta else mae.get("low")) if (mae and tendencia) else None
    inv = (mae.get("low") if alta else mae.get("high")) if (mae and tendencia) else None
    return _mk("Inside Bar (%s)" % (lado if tendencia else "sem tendência"), lado, criterios,
               gat, inv, _alvo_rr(gat, inv, c["atr"], alta), "Clássico")


def _setup_9_4_lw(c, lado: str) -> dict:
    """9.4 / Máximas-Mínimas de Larry Williams: em correção dentro da
    tendência, rompimento da máxima do candle que fez a mínima mais baixa
    (compra); espelho na venda."""
    alta = lado == "alta"
    trend_ok = (c["sma20"] is not None and c["sma50"] is not None and
                (c["sma20"] > c["sma50"] if alta else c["sma20"] < c["sma50"]))
    cs = [x for x in c["candles"][-5:] if x.get("low") is not None and x.get("high") is not None]
    ref = None
    if len(cs) >= 2:
        ref = (min(cs, key=lambda x: x["low"]) if alta else max(cs, key=lambda x: x["high"]))
    correcao = False
    if ref is not None:
        i = cs.index(ref)
        correcao = i > 0 and (ref["low"] < cs[i - 1]["low"] if alta else ref["high"] > cs[i - 1]["high"])
    gat = (ref.get("high") if alta else ref.get("low")) if ref else None
    inv = (ref.get("low") if alta else ref.get("high")) if ref else None
    armado = (gat is not None and c["close"] is not None and
              (c["close"] <= gat if alta else c["close"] >= gat))
    criterios = [
        _crit("Tendência de %s (SMA20 × SMA50)" % lado, trend_ok, 3, obrigatorio=True),
        _crit("Correção com %s de referência identificada" % ("mínima mais baixa" if alta else "máxima mais alta"), bool(correcao), 3, obrigatorio=True),
        _crit("Gatilho ainda não rompido — padrão armado", bool(armado), 1),
    ]
    return _mk("Máx/Mín de Larry Williams — 9.4 (%s)" % lado, lado, criterios, gat, inv,
               _alvo_rr(gat, inv, c["atr"], alta), "Larry Williams")


def _setups_br(c) -> list:
    """Todos os detectores BR (FASE 1), dois lados onde o padrão é espelhável."""
    return [
        _setup_9_1(c, "alta"), _setup_9_1(c, "baixa"),
        _setup_9_2(c, "alta"), _setup_9_2(c, "baixa"),
        _setup_9_3(c, "alta"), _setup_9_3(c, "baixa"),
        _setup_ifr2(c),
        _setup_pfr(c, "alta"), _setup_pfr(c, "baixa"),
        _setup_123(c, "alta"), _setup_123(c, "baixa"),
        _setup_ponto_continuo(c, "alta"), _setup_ponto_continuo(c, "baixa"),
        _setup_inside_bar(c),
        _setup_9_4_lw(c, "alta"), _setup_9_4_lw(c, "baixa"),
    ]


MIN_CONFLUENCIA = 50  # setup só "conta" com metade ponderada dos critérios


def detect_setups(candles: list, ind: dict) -> dict:
    """Avalia todos os setups e produz o veredito educacional do ativo.

    Retorna {setups:[só os com confluência ≥ MIN_CONFLUENCIA, ordenados],
             melhor: setup de maior confluência (ou None),
             veredito: "Estudar alta"|"Estudar baixa"|"Monitorar"|
                       "Sem setup no momento",
             confluencia: a do melhor (0 se nenhum)}.
    Regra do veredito: melhor setup direcional ≥ MIN_CONFLUENCIA define o lado;
    só compressão (neutra) ≥ MIN_CONFLUENCIA => "Monitorar"; nada => "Sem setup".
    """
    c = _ctx(candles, ind)
    todos = [
        _setup_pullback(c, "alta"), _setup_pullback(c, "baixa"),
        _setup_rompimento(c, "alta"), _setup_rompimento(c, "baixa"),
        _setup_reversao(c, "alta"), _setup_reversao(c, "baixa"),
        _setup_compressao(c),
    ] + _setups_br(c)  # FASE 1: setups testados do mercado BR
    def _vale(s):
        # confluência mínima E todos os critérios que DEFINEM o setup presentes
        # (sem isso, mercado lateral "ganhava" pullback só por estar perto da média).
        if s["confluencia"] < MIN_CONFLUENCIA:
            return False
        return all(c["ok"] for c in s["criterios"] if c.get("obrigatorio"))

    ativos = sorted([s for s in todos if _vale(s)], key=lambda s: -s["confluencia"])
    direcionais = [s for s in ativos if s["lado"] in ("alta", "baixa")]
    if direcionais:
        melhor = direcionais[0]
        veredito = "Estudar alta" if melhor["lado"] == "alta" else "Estudar baixa"
    elif ativos:
        melhor = ativos[0]
        veredito = "Monitorar"
    else:
        melhor, veredito = None, "Sem setup no momento"
    return {
        "setups": ativos,
        "melhor": melhor["nome"] if melhor else None,
        "veredito": veredito,
        "confluencia": melhor["confluencia"] if melhor else 0,
    }


# Texto do modelo, exibido na tela "COMO O RADAR ANALISA" (fonte única).
MODEL_EXPLANATION = [
    ("Pullback à média", "Tendência definida pelas médias 20/50 com o preço reencontrando a SMA20 e RSI neutro — a correção didática dentro da tendência."),
    ("Rompimento com volume", "Fechamento além do extremo do período analisado, confirmado por volume acima de 1,5× a média — força saindo de consolidação."),
    ("Reversão de extremos", "RSI em sobrevenda/sobrecompra com candle de força e estocástico cruzando — exaustão do movimento anterior."),
    ("Compressão de volatilidade", "Bandas de Bollinger no quartil mais estreito do período — contexto que costuma anteceder expansões, sem indicar direção."),
    # FASE 1 — setups testados do mercado brasileiro (regras em qa/SETUPS.md)
    ("Setup 9.1 / 9.2 / 9.3 (Stormer)", "Família da MME9: virada da média (9.1), correção de 1 candle (9.2) e retomada após correção (9.3) — sempre com gatilho no rompimento do candle de referência."),
    ("IFR2 (Larry Connors)", "RSI de 2 períodos em sobrevenda com preço acima da MMA200 — repique de curtíssimo prazo dentro da tendência de alta; saída didática na máxima dos 2 candles anteriores."),
    ("PFR (Stormer)", "Mínima mais baixa que os 2 candles anteriores com fechamento acima do anterior — força e reversão no mesmo candle; espelho no lado vendedor."),
    ("123 de fundo/topo", "Fundo (1), topo (2) e fundo mais alto (3) — o estudo se ativa no rompimento do ponto 2; espelho no topo, para o lado vendedor."),
    ("Ponto Contínuo (Dunnigan)", "Preço reencontrando a MME21 com tendência definida pelo ADX — a correção didática até a média em mercado direcional."),
    ("Inside Bar", "Candle contido no anterior com tendência definida — compressão que costuma anteceder o próximo impulso; gatilho nos extremos do candle-mãe."),
    ("Máx/Mín de Larry Williams (9.4)", "Na correção dentro da tendência, o gatilho é o rompimento do extremo do candle que fez a mínima mais baixa (ou máxima mais alta, no lado vendedor)."),
]


# =============================================================================
# FASE 7 (F7.1) — MODO OPERADOR: plano operacional DETERMINÍSTICO.
# Deriva decisão e plano (entrada/stop/alvos/R:R) dos números que os detectores
# acima já produzem — nenhum cálculo novo de indicador, nenhum LLM. O texto é
# direto de propósito (vocabulário do Modo Operador); a UI só o exibe quando
# config.appMode == "operador". Sizing (quantidade por % de risco) fica no
# CLIENTE: o resultado do scan é cacheado e compartilhado entre usuários, e o
# capital de cada um não pode entrar nesse payload.
# Regras da persona (analise-tecnica-b3) aplicadas de forma objetiva:
#   • R:R mínimo 1,5:1 no alvo final — abaixo disso, NÃO OPERAR;
#   • movimento esticado além de meia zona de risco após o gatilho => não
#     perseguir preço (NÃO OPERAR; reentrada só em novo setup);
#   • setup neutro (compressão) => AGUARDAR CONFIRMAÇÃO;
#   • sem setup válido => NÃO OPERAR ("sem vantagem estatística").
# =============================================================================

RR_MINIMO = 1.5          # relação risco-retorno mínima aceitável (alvo final)
ZONA_PERSEGUICAO = 0.5   # até 0,5× o risco além do gatilho ainda dá entrada a mercado

DECISAO_COMPRAR = "COMPRAR"
DECISAO_VENDER = "VENDER"
DECISAO_AGUARDAR = "AGUARDAR CONFIRMAÇÃO"
DECISAO_NAO_OPERAR = "NÃO OPERAR"


def _plano_vazio(motivo):
    return {"decisao": DECISAO_NAO_OPERAR, "motivo": motivo, "setup": None,
            "lado": None, "tipo": None, "entrada": None, "stop": None,
            "alvo1": None, "alvo2": None, "rr1": None, "rr2": None,
            "riscoPorAcao": None}


def plano_operacional(setup, close=None):
    """Plano operacional puro de UM setup detectado (dict do _mk) + preço atual.

    Retorna sempre um dict com `decisao` ∈ {COMPRAR, VENDER, AGUARDAR
    CONFIRMAÇÃO, NÃO OPERAR} e, quando operável: tipo de entrada, entrada,
    stop (invalidação do setup — nunca arbitrário), alvo1 (1R, parcial),
    alvo2 (projeção do setup), rr1/rr2 e riscoPorAcao. `motivo` sempre explica
    a decisão em uma frase direta.
    """
    if not isinstance(setup, dict):
        return _plano_vazio("Sem setup válido — não há operação com vantagem estatística clara neste momento.")
    lado = setup.get("lado")
    if lado == "neutro":
        return {**_plano_vazio(""), "decisao": DECISAO_AGUARDAR, "setup": setup.get("nome"), "lado": "neutro",
                "motivo": "Compressão sem direção definida — aguarde o rompimento definir o lado antes de operar."}
    if lado not in ("alta", "baixa"):
        return _plano_vazio("Setup sem direção — não operar.")
    gatilho = setup.get("gatilho")
    stop = setup.get("invalidacao")
    if gatilho is None or stop is None or gatilho == stop:
        return _plano_vazio("Setup sem gatilho/invalidação numéricos — sem plano executável, não operar.")
    alta = lado == "alta"
    risco = abs(gatilho - stop)
    # coerência geométrica: em compra o stop fica ABAIXO do gatilho (e vice-versa)
    if (alta and stop >= gatilho) or ((not alta) and stop <= gatilho):
        return _plano_vazio("Gatilho e invalidação incoerentes para o lado do setup — não operar.")

    entrada = float(gatilho)
    tipo = "no rompimento do gatilho"
    if close is not None:
        rompido = close >= gatilho if alta else close <= gatilho
        if rompido:
            excedente = abs(close - gatilho)
            if excedente > ZONA_PERSEGUICAO * risco:
                return {**_plano_vazio(""), "setup": setup.get("nome"), "lado": lado,
                        "motivo": "Gatilho já rompido e preço esticado (>0,5R além) — não persiga; espere novo setup ou reteste."}
            entrada = float(close)  # entrada a mercado: risco real conta a partir daqui
            tipo = "a mercado (gatilho já rompido, dentro da zona)"

    alvo2 = setup.get("alvoSugerido")
    if alvo2 is None:
        alvo2 = gatilho + 2 * risco if alta else gatilho - 2 * risco
    alvo1 = gatilho + risco if alta else gatilho - risco
    risco_real = abs(entrada - stop)
    if risco_real <= 0:
        return _plano_vazio("Risco nulo entre entrada e stop — plano inválido, não operar.")
    rr1 = abs(alvo1 - entrada) / risco_real
    rr2 = abs(alvo2 - entrada) / risco_real
    if rr2 < RR_MINIMO:
        return {**_plano_vazio(""), "setup": setup.get("nome"), "lado": lado,
                "motivo": "R:R de %.1f:1 abaixo do mínimo de %.1f:1 — não há operação com vantagem estatística clara neste momento." % (rr2, RR_MINIMO)}

    return {
        "decisao": DECISAO_COMPRAR if alta else DECISAO_VENDER,
        "tipo": tipo,
        "setup": setup.get("nome"),
        "lado": lado,
        "entrada": _rr2(entrada),
        "stop": _rr2(stop),
        "alvo1": _rr2(alvo1),
        "alvo2": _rr2(alvo2),
        "rr1": round(rr1, 2),
        "rr2": round(rr2, 2),
        "riscoPorAcao": _rr2(risco_real),
        "motivo": ("%s %s: entrada %s, stop na invalidação do setup, parcial no alvo 1 (1R) e alvo final com R:R %.1f:1."
                   % (DECISAO_COMPRAR.capitalize() if alta else DECISAO_VENDER.capitalize(),
                      tipo, _rr2(entrada), rr2)),
    }


def plano_do_resultado(sres, close=None):
    """Plano do RESULTADO do detect_setups (o que o scanner anexa por ativo).
    Melhor setup direcional => plano; só neutro => AGUARDAR; nada => NÃO OPERAR."""
    setups_list = (sres or {}).get("setups") or []
    direcionais = [s for s in setups_list if s.get("lado") in ("alta", "baixa")]
    if direcionais:
        return plano_operacional(direcionais[0], close=close)
    if setups_list:
        return plano_operacional(setups_list[0], close=close)
    return _plano_vazio("Nenhum setup com confluência mínima — não há operação com vantagem estatística clara neste momento.")
