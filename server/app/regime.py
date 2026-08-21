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
- ADR-017 (Bloco 1): `ranquear` também lê `setup["historico"]`, mas SÓ do
  dict de setup que já chega pronto dentro de `resultados`/`snaps_por_ticker`
  (anexado por `setups.detect_setups` via provedor injetado). Este módulo
  continua sem tocar disco ou serviço externo — a leitura persistida vive
  inteiramente do lado de quem monta o insumo, nunca aqui.
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
    # ADR-017: setup aposentado (faixa catastrófica do backtest, ADR-016) não
    # conta pro gatilho alinhado — mesma regra de detect_setups/melhor.
    operaveis = [s for s in setups if not s.get("aposentado")]
    if not operaveis:
        return False
    melhor = operaveis[0]  # já vem ordenado por confluência em setups.detect_setups
    lado = (melhor.get("lado") or "").lower()
    nome = (melhor.get("nome") or "").lower()
    if reg["regime"] in ("tendencia_alta", "tendencia_baixa"):
        return lado == (reg["direcao"] or "")
    if reg["regime"] == "lateral":
        return "revers" in nome
    return False


# Tier do regime como critério primário de ordenação.
_TIER = {"tendencia_alta": 2, "tendencia_baixa": 2, "lateral": 1, "indefinido": 0}

# ADR-017 (Bloco 1): peso da evidência medida (elegibilidade da janela anual
# fechada) no radarScore. O corpo do score é o percentil de momentum (escala
# 0–100), então ±10 desloca cerca de um decil — suficiente para desempatar no
# eixo de evidência sem inverter o eixo de regime/momentum, que é o que o
# ADR-016 (Adendo 7) validou. gatilhoAlinhado vale +5 (timing); a evidência
# medida pesa o dobro do timing, e nenhum dos dois domina o momentum.
W_HISTORICO_ELEGIVEL = 10.0
W_HISTORICO_INELEGIVEL = -10.0


def _elegibilidade(resultado: dict) -> tuple:
    """Histórico/elegibilidade do melhor setup OPERÁVEL de um resultado.

    Mesma seleção de _gatilho_alinhado (primeiro não-aposentado — a lista já
    vem ordenada por confluência de setups.detect_setups). Devolve
    (historico, elegivel):
      - (None, None) quando não há setup operável ou o setup não tem
        "historico" (nunca medido, ou provedor desligado);
      - (historico, None) quando insuficiente=True OU elegivel is None —
        ausência de evidência NUNCA vira "elegivel=False": amostra pequena
        não é prova de mau desempenho (ADR-017, "Dois pisos de amostra");
      - (historico, bool(elegivel)) no caso normal.
    """
    setups = resultado.get("setups") or []
    operaveis = [s for s in setups if not s.get("aposentado")]
    if not operaveis:
        return None, None
    historico = operaveis[0].get("historico")
    if not historico:
        return None, None
    if historico.get("insuficiente") or historico.get("elegivel") is None:
        return historico, None
    return historico, bool(historico.get("elegivel"))


def ranquear(resultados: list[dict], snaps_por_ticker: dict) -> list[dict]:
    """Ordena os resultados do scanner pelo NOVO eixo e anexa os campos.

    `resultados`      — a lista que o run_scan montou (um dict por ativo).
    `snaps_por_ticker`— {ticker: snapshot} para classificar regime/momentum.

    Anexa a cada resultado (não remove nada — contrato da UI preservado):
      "regime": {...}                # saída de classificar()
      "momentumRelPct": float|None   # percentil cross-sectional (0–100)
      "momentumParcial": bool
      "gatilhoAlinhado": bool
      "setupHistorico": dict|None    # histórico do melhor setup OPERÁVEL (ADR-017 Bloco 1)
      "setupElegivel": bool|None     # elegibilidade da janela fechada anterior
      "radarScore": float            # chave de ordenação, 0–100 + tiers

    Ordena por (tier do regime, momentum relativo, rank de elegibilidade,
    gatilho alinhado, -confluencia como desempate FINAL, ticker). O rank de
    elegibilidade entra ENTRE momentum e gatilho: a evidência medida pesa
    mais que o timing, mas nunca ultrapassa o eixo de regime/momentum
    validado no ADR-016 — esta fase não reabre esse eixo. A confluência cai
    de chave primária para último critério de desempate.
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
        r["setupHistorico"], r["setupElegivel"] = _elegibilidade(r)
        # radarScore: momentum relativo é o corpo; gatilho alinhado dá um empurrão
        # pequeno (timing); a elegibilidade medida soma um termo próprio, nenhum
        # dos dois domina o eixo de evidência (momentum).
        base = p if p is not None else 0.0
        if r["setupElegivel"] is True:
            peso_hist = W_HISTORICO_ELEGIVEL
        elif r["setupElegivel"] is False:
            peso_hist = W_HISTORICO_INELEGIVEL
        else:
            peso_hist = 0.0
        r["radarScore"] = round(base + (5.0 if r["gatilhoAlinhado"] else 0.0) + peso_hist, 1)
        r.pop("_momentumBruto", None)

    # 3) ordenação final.
    def _rank_elegibilidade(r):
        if r.get("setupElegivel") is True:
            return 0
        if r.get("setupElegivel") is None:
            return 1
        return 2

    resultados.sort(key=lambda r: (
        -_TIER.get(r["regime"]["regime"], 0),
        -(r.get("momentumRelPct") or -1.0),
        _rank_elegibilidade(r),
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
