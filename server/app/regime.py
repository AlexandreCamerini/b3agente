"""FASE 2 (A) — Classificador de regime + momentum relativo (Radar N1).

POR QUÊ (o furo que este módulo corrige)
----------------------------------------
O Radar rankeava o universo por `confluencia` do melhor setup. O próprio
`setups.py` define confluência como "percentual ponderado de critérios
atendidos — mede ADERÊNCIA do ativo ao padrão em dados PASSADOS, nunca
probabilidade de resultado". Ou seja: o mercado inteiro era ordenado por
aderência a um padrão, não por vantagem estatística — exatamente a confusão
(taxa de acerto ≠ expectância) que o CLAUDE.md manda evitar.

Pior: o roster que dominava esse ranking (9.x, IFR2, PFR, 123, inside bar,
LW) é a família de price action de curto prazo — a de evidência acadêmica
mais fraca. As duas famílias com melhor evidência OOS reproduzível
(tendência e momentum RELATIVO / força relativa cross-sectional) só entravam
como insumo do `score_tecnico`, que é mero desempate.

O QUE ESTE MÓDULO FAZ
---------------------
Inverte o eixo de seleção:

1. `classificar(snap)` — regime determinístico de UM ativo a partir dos
   indicadores que já existem no snapshot (SMA200, ADX14, DI±, SMA50).
2. `ranquear(resultados)` — calcula o momentum relativo ENTRE os ativos do
   universo (percentil — só possível quando todos os snapshots estão juntos,
   no fim do run_scan) e ordena por (regime alinhado → momentum relativo →
   gatilho de setup ALINHADO ao regime → ticker).

Os setups de price action deixam de ordenar o mercado: viram GATILHO DE
TIMING dentro de um ativo já selecionado pelo regime, e só pontuam quando o
lado do setup coincide com a direção do regime. Reversão à média só é tratada
como gatilho válido em regime lateral.

INVARIANTES PRESERVADAS
-----------------------
- Nenhum número novo nasce na LLM: regime e momentum são cálculo puro.
- A `confluencia` CONTINUA no payload (contrato da UI inalterado) — só deixa
  de ser a chave de ordenação.
- Puro/testável: sem I/O, sem rede, sem relógio. Mesmos snapshots ⇒ mesma
  ordenação (determinístico).
- Degradação declarada: janela sem 200 candles cai para SMA50 e marca
  `base="sma50"`, `confiavel=False`; sem change252 usa change63 e marca
  `momentumParcial=True`. Nunca compensa dado ausente com inferência.
"""
from __future__ import annotations

from typing import Optional

# Limiares de força de tendência (ADX de Wilder — mesma convenção do
# indicators.adxState: >=25 forte, <20 fraca/lateral, 20–25 transição).
ADX_TENDENCIA = 25.0
ADX_LATERAL = 20.0

# Mínimo de candles para o filtro de regime "confiável" via SMA200.
MIN_CANDLES_SMA200 = 200

# Pesos do momentum absoluto (proxy 3–12m; a literatura usa 12-1, aqui usamos
# as janelas que o technical_models já expõe: 63 pregões ~3m, 252 ~12m).
W_CHANGE63 = 0.5
W_CHANGE252 = 0.5

REGIMES = ("tendencia_alta", "tendencia_baixa", "lateral", "indefinido")


# --------------------------------------------------------------------------- #
# 1) Regime de UM ativo (determinístico)
# --------------------------------------------------------------------------- #

def _dir_por_media(close: Optional[float], sma: Optional[float]) -> Optional[str]:
    if close is None or sma is None:
        return None
    return "alta" if close > sma else "baixa"


def classificar(snap: dict) -> dict:
    """Classifica o regime de um ativo a partir do Snapshot Técnico Único.

    Lê SOMENTE campos que o snapshot já produz (indicators.summary):
      close, sma200, sma50, adx14, diPlus, diMinus, candlesAvailable.

    Retorna dict estável:
      {
        "regime": "tendencia_alta"|"tendencia_baixa"|"lateral"|"indefinido",
        "direcao": "alta"|"baixa"|None,     # direção do filtro de média
        "forca": "forte"|"transicao"|"fraca"|None,   # a partir do ADX
        "adx14": float|None,
        "base": "sma200"|"sma50"|None,      # em que média o filtro se apoiou
        "confiavel": bool,                  # SMA200 disponível E n>=200
      }
    """
    ind = (snap or {}).get("indicators") or {}
    summ = (snap or {}).get("summary") or ind  # tolera ambos os formatos
    ctx = (snap or {}).get("context") or {}
    hist = ctx.get("historyStats") or {}

    close = _num(snap.get("close")) or _num((ctx.get("lastCandle") or {}).get("close"))
    sma200 = _num(summ.get("sma200"))
    sma50 = _num(summ.get("sma50"))
    adx = _num(summ.get("adx14"))
    n = hist.get("candlesAvailable") or (snap.get("candlesAvailable"))

    # Base do filtro de direção: SMA200 se houver janela; senão SMA50 (degradado).
    if sma200 is not None and (n is None or n >= MIN_CANDLES_SMA200):
        direcao = _dir_por_media(close, sma200)
        base, confiavel = "sma200", True
    elif sma50 is not None:
        direcao = _dir_por_media(close, sma50)
        base, confiavel = "sma50", False
    else:
        direcao, base, confiavel = None, None, False

    # Força pela leitura do ADX.
    if adx is None:
        forca = None
    elif adx >= ADX_TENDENCIA:
        forca = "forte"
    elif adx < ADX_LATERAL:
        forca = "fraca"
    else:
        forca = "transicao"

    # Combinação regime = direção (média) × força (ADX).
    if direcao is None or forca is None:
        regime = "indefinido"
    elif forca == "forte":
        regime = "tendencia_alta" if direcao == "alta" else "tendencia_baixa"
    elif forca == "fraca":
        regime = "lateral"
    else:  # transição: tendência ainda não confirmada pela força → conservador
        regime = "lateral"

    return {
        "regime": regime,
        "direcao": direcao,
        "forca": forca,
        "adx14": adx,
        "base": base,
        "confiavel": confiavel,
    }


# --------------------------------------------------------------------------- #
# 2) Momentum relativo (cross-sectional) + ordenação do universo
# --------------------------------------------------------------------------- #

def _momentum_bruto(snap: dict) -> tuple[Optional[float], bool]:
    """Momentum absoluto do ativo (%). Retorna (valor, parcial).

    parcial=True quando faltou a janela de 252 (usou só 63) — janela curta.
    """
    ctx = (snap or {}).get("context") or {}
    h = ctx.get("historyStats") or {}
    c63 = _num(h.get("change63dPct"))
    c252 = _num(h.get("change252dPct"))
    if c63 is None and c252 is None:
        return None, False
    if c252 is None:
        return c63, True
    if c63 is None:
        return c252, True
    return W_CHANGE63 * c63 + W_CHANGE252 * c252, False


def _percentis(valores: list[Optional[float]]) -> list[Optional[float]]:
    """Percentil (0–100) de cada valor dentro da lista; None permanece None.

    Empates recebem o mesmo percentil (rank médio). Determinístico.
    """
    idx = [i for i, v in enumerate(valores) if v is not None]
    if not idx:
        return [None] * len(valores)
    ordenados = sorted(idx, key=lambda i: valores[i])
    n = len(ordenados)
    pct: list[Optional[float]] = [None] * len(valores)
    j = 0
    while j < n:
        k = j
        while k + 1 < n and valores[ordenados[k + 1]] == valores[ordenados[j]]:
            k += 1
        rank_medio = (j + k) / 2.0
        p = round(100.0 * rank_medio / (n - 1), 1) if n > 1 else 100.0
        for m in range(j, k + 1):
            pct[ordenados[m]] = p
        j = k + 1
    return pct


def _gatilho_alinhado(resultado: dict, reg: dict) -> bool:
    """O melhor setup direcional coincide com a direção do regime?

    - Regime de tendência: gatilho vale se o lado do setup == direção.
    - Regime lateral: só setups de reversão contam (evidência da reversão à
      média é condicional a mercado lateral); a checagem de "reversão" usa o
      nome do setup (contrato de setups.py).
    - Setup contra o regime NÃO pontua (não somamos sinal desalinhado).
    """
    setups = resultado.get("setups") or []
    if not setups:
        return False
    melhor = setups[0]  # já vem ordenado por confluência em setups.detect_setups
    lado = (melhor.get("lado") or "").lower()
    nome = (melhor.get("nome") or "").lower()
    if reg["regime"] in ("tendencia_alta", "tendencia_baixa"):
        return lado == (reg["direcao"] or "")
    if reg["regime"] == "lateral":
        return "revers" in nome
    return False


# Tier do regime como critério primário de ordenação.
_TIER = {"tendencia_alta": 2, "tendencia_baixa": 2, "lateral": 1, "indefinido": 0}


def ranquear(resultados: list[dict], snaps_por_ticker: dict) -> list[dict]:
    """Ordena os resultados do scanner pelo NOVO eixo e anexa os campos.

    `resultados`      — a lista que o run_scan montou (um dict por ativo).
    `snaps_por_ticker`— {ticker: snapshot} para classificar regime/momentum.

    Anexa a cada resultado (não remove nada — contrato da UI preservado):
      "regime": {...}                # saída de classificar()
      "momentumRelPct": float|None   # percentil cross-sectional (0–100)
      "momentumParcial": bool
      "gatilhoAlinhado": bool
      "radarScore": float            # chave de ordenação, 0–100 + tiers

    Ordena por (tier do regime, momentum relativo, gatilho alinhado,
    -confluencia como desempate FINAL, ticker). A confluência cai de chave
    primária para último critério de desempate.
    """
    # 1) regime + momentum bruto por ativo.
    brutos: list[Optional[float]] = []
    for r in resultados:
        snap = snaps_por_ticker.get(r["ticker"]) or {}
        reg = classificar(snap)
        mb, parcial = _momentum_bruto(snap)
        r["regime"] = reg
        r["_momentumBruto"] = mb
        r["momentumParcial"] = parcial
        brutos.append(mb)

    # 2) percentil cross-sectional (precisa de TODOS juntos — por isso aqui).
    pcts = _percentis(brutos)
    for r, p in zip(resultados, pcts):
        r["momentumRelPct"] = p
        r["gatilhoAlinhado"] = _gatilho_alinhado(r, r["regime"])
        # radarScore: momentum relativo é o corpo; gatilho alinhado dá um empurrão
        # pequeno (timing), nunca domina o eixo de evidência.
        base = p if p is not None else 0.0
        r["radarScore"] = round(base + (5.0 if r["gatilhoAlinhado"] else 0.0), 1)
        r.pop("_momentumBruto", None)

    # 3) ordenação final.
    resultados.sort(key=lambda r: (
        -_TIER.get(r["regime"]["regime"], 0),
        -(r.get("momentumRelPct") or -1.0),
        0 if r.get("gatilhoAlinhado") else 1,
        -(r.get("confluencia") or 0),   # confluência: só desempate final
        r["ticker"],
    ))
    return resultados


# --------------------------------------------------------------------------- #
# util
# --------------------------------------------------------------------------- #

def _num(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
