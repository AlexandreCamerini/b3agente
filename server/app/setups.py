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
    ]
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
]
