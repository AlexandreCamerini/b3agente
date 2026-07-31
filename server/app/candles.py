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

# ADR-002 (Decisão 3) — quantas velas cada intervalo tem em UM pregão.
# Medido no Yahoo em 30/07/2026 com PETR4 (pregão 10:00–17:00 BRT):
#   1m=418  2m=210  5m=85  15m=29  30m=15  60m=8  90m=6
# Sem isto, `resolve_keep("1mo")` devolvia 22 — vinte e dois PREGÕES — e com
# interval=15m isso virava 22 VELAS DE 15 MINUTOS: 5,5 horas de contexto para
# quem pediu um mês. Não levantava exceção; só entregava análise curta demais.
BARS_PER_SESSION = {
    "1m": 418, "2m": 210, "5m": 85, "15m": 29, "30m": 15,
    "60m": 8, "1h": 8, "90m": 6,
    "1d": 1, "1wk": 1,
}


def normalize_period(period: Optional[str]) -> str:
    p = (period or "").strip().lower()
    return p if p in PERIOD_BARS else DEFAULT_PERIOD


def bars_per_session(interval: Optional[str]) -> int:
    """Velas do intervalo em um pregão. Desconhecido ⇒ 1 (trata como diário)."""
    return BARS_PER_SESSION.get((interval or DEFAULT_INTERVAL).strip().lower(), 1)


# ADR-001 (item 1d) — LACUNA na série intraday.
#
# Em 31/07/2026 o feed de B3 do Yahoo passou as 3 primeiras horas do pregão sem
# publicar nada e, quando voltou às 13:02, a manhã (10:00–12:45) NÃO foi
# preenchida. A série ficou com um buraco de 2h45 e o app não tinha como saber:
# a instrumentação detecta série VAZIA, não série FURADA. Indicador calculado
# sobre série furada mente com cara de certo.
ABERTURA_MIN = 10 * 60      # pregão da B3 abre às 10:00 BRT
_TOLERANCIA = 1.5           # folga na grade: a vela em formação chega com o
                            # timestamp do último negócio, fora do alinhamento
INTERVALO_MIN = {"1m": 1, "2m": 2, "5m": 5, "15m": 15, "30m": 30,
                 "60m": 60, "1h": 60, "90m": 90}


def _minutos(date_str: str):
    """"AAAA-MM-DD HH:MM" -> (data, minutos do dia). None se for diário."""
    if not isinstance(date_str, str) or " " not in date_str:
        return None
    dia, hora = date_str.split(" ", 1)
    try:
        h, m = hora.split(":")[:2]
        return dia, int(h) * 60 + int(m)
    except (ValueError, IndexError):
        return None


def detectar_lacunas(candles: list, interval: Optional[str] = None) -> dict:
    """Buracos na grade temporal da série intraday. PURO.

    Olha só o ÚLTIMO pregão presente — é onde a lacuna importa para a decisão.
    No diário devolve `temLacuna: False`: lá a grade tem feriado e pregão curto,
    e cobrar regularidade daria falso positivo sem valor.
    """
    passo = INTERVALO_MIN.get((interval or "1d").strip().lower())
    vazio = {"temLacuna": False, "buracos": [], "velasFaltando": 0,
             "inicioTardio": None, "cobertura": None}
    if not passo or not candles:
        return vazio

    pontos = [(_minutos(c.get("date")), c.get("date")) for c in candles]
    pontos = [(p, d) for p, d in pontos if p]
    if not pontos:
        return vazio

    ultimo_dia = pontos[-1][0][0]
    sessao = [(p[1], d) for p, d in pontos if p[0] == ultimo_dia]
    if not sessao:
        return vazio

    buracos = []
    faltando = 0
    for (m1, d1), (m2, d2) in zip(sessao, sessao[1:]):
        salto = m2 - m1
        if salto > passo * _TOLERANCIA:
            n = max(1, round(salto / passo) - 1)
            faltando += n
            buracos.append({"de": d1, "ate": d2, "velasFaltando": n})

    # Início tardio: a série do dia deveria começar na abertura.
    primeiro = sessao[0][0]
    tardio = None
    if primeiro > ABERTURA_MIN + passo * _TOLERANCIA:
        n = max(1, round((primeiro - ABERTURA_MIN) / passo))
        faltando += n
        tardio = sessao[0][1]

    esperadas = max(1, round((sessao[-1][0] - ABERTURA_MIN) / passo) + 1)
    return {
        "temLacuna": bool(buracos or tardio),
        "buracos": buracos[:5],
        "velasFaltando": faltando,
        "inicioTardio": tardio,
        "cobertura": round(len(sessao) / esperadas, 3),
    }


def resolve_keep(period: Optional[str], interval: Optional[str] = None) -> int:
    """Quantas velas exibir/enviar para o período pedido, NO INTERVALO pedido.

    `pregões do período × velas por pregão`. Com `interval="1d"` (o default) o
    resultado é idêntico ao de sempre — o diário não muda em nada.
    """
    return PERIOD_BARS[normalize_period(period)] * bars_per_session(interval)


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
