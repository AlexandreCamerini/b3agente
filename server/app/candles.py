"""Objetivo 4 — período/intervalo de candles configurável.

Puro/stdlib e testável. O período escolhido pelo usuário define:
  • quantos candles diários são EXIBIDOS no gráfico (keep);
  • quantos candles vão no CONTEXTO da IA (tail_n);
  • a 'range' enviada ao Yahoo no gráfico simples (history).

Os INDICADORES continuam calculados sobre a janela longa de warmup (FETCH_RANGE),
então médias longas (SMA50 etc.) permanecem corretas independentemente do período.
"""
from typing import Optional

# período -> nº aproximado de pregões (candles diários) exibidos/analisados
PERIOD_BARS = {
    "1mo": 22,
    "3mo": 66,
    "6mo": 126,
    "1y": 252,
    "2y": 504,
}
# período -> range aceita pelo Yahoo (gráfico simples /api/history)
PERIOD_RANGE = {
    "1mo": "1mo",
    "3mo": "3mo",
    "6mo": "6mo",
    "1y": "1y",
    "2y": "2y",
}
DEFAULT_PERIOD = "1y"     # mantém o comportamento atual (~252 pregões)
FETCH_RANGE = "2y"        # warmup fixo para médias longas (recorta-se depois)
VALID_INTERVALS = ("1d", "1wk")
DEFAULT_INTERVAL = "1d"


def normalize_period(period: Optional[str]) -> str:
    p = (period or "").strip().lower()
    return p if p in PERIOD_BARS else DEFAULT_PERIOD


def resolve_keep(period: Optional[str]) -> int:
    """Quantos candles diários exibir/enviar para o período pedido."""
    return PERIOD_BARS[normalize_period(period)]


def period_to_range(period: Optional[str]) -> str:
    """Range do Yahoo para o gráfico simples (history)."""
    return PERIOD_RANGE[normalize_period(period)]


def normalize_interval(interval: Optional[str]) -> str:
    i = (interval or "").strip().lower()
    return i if i in VALID_INTERVALS else DEFAULT_INTERVAL

def slice_for_config(candles: list, config: Optional[dict]) -> list:
    """BLOCO C — janela ÚNICA da análise: corta a cauda dos candles conforme o
    candlePeriod escolhido pelo usuário na Config. Todo caminho que envia
    histórico à IA (análise completa, stop/alvo, modelos técnicos) passa por
    aqui ou por resolve_keep — nunca por uma janela fixa."""
    keep = resolve_keep((config or {}).get("candlePeriod"))
    return list(candles or [])[-keep:]
