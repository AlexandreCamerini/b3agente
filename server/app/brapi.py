"""Cliente HTTP da brapi (ADR-008, Fase 1 do qa/43).

Espelha a postura de `yahoo.py` (httpx, timeout, retry curto), sem sessão nem
crumb — a brapi autentica por token no header. O que este módulo NÃO faz:
orçamento de requisições (Fase 2) e spot (Fase 5).

Limites do plano GRATUITO, medidos com token real em 11/08/2026
(`docs/MEDICAO-Brapi-2026-08-11.md` — nada aqui é presunção):
  • 1 ticker por requisição;
  • intervalo permitido: só `1d`;
  • ranges permitidos: 1d, 5d, 1mo, 3mo;
  • cota 15.000/mês, e RECUSA POR PLANO DEBITA COTA — por isso a validação
    acontece AQUI, antes de qualquer chamada de rede (`ForaDoPlano`).
"""
import asyncio
import os
import time

import httpx

from .tickers import normalize_ticker
from .yahoo import INTRADAY_INTERVALS

BASE = "https://brapi.dev/api/quote/"
TIMEOUT_S = 20

# Limites do plano gratuito (medidos). Se o plano mudar, é AQUI que se ajusta.
PLAN_INTERVALS = {"1d"}
PLAN_RANGES = {"1d", "5d", "1mo", "3mo"}

# Fuso da B3. A brapi entrega epoch já alinhado à bolsa (diário = meia-noite
# BRT, medido em 11/08); o offset fixo -3h segue o padrão do resto do app
# (`intraday.BRT`) — o Brasil não tem horário de verão desde 2019.
_BRT_OFF = -3 * 3600


# Última leitura dos headers de cota da PRÓPRIA brapi (verdade > previsão do
# orçamento local). Atualizada a cada resposta HTTP; `brapi_budget.snapshot()`
# expõe no /api/status para reconciliação a olho.
LAST_RATELIMIT: dict = {}


class BrapiIndisponivel(RuntimeError):
    """Falha transitória ou resposta imprestável — quem chama decide degradar."""


class ForaDoPlano(ValueError):
    """Pedido que o plano contratado não cobre. Levantada SEM tocar a rede:
    a brapi debita cota mesmo em recusa (medição de 11/08), então tentar
    para descobrir custaria orçamento. O roteamento (Fase 3) usa isto para
    mandar o pedido ao provedor de backup."""


def _token() -> str:
    return (os.environ.get("BRAPI_TOKEN") or "").strip()


def _candle_key(epoch: int, interval: str) -> str:
    """Identidade da vela no fuso da bolsa (mesma regra de `yahoo._candle_key`):
    diário "AAAA-MM-DD"; intraday "AAAA-MM-DD HH:MM"."""
    fmt = "%Y-%m-%d %H:%M" if interval in INTRADAY_INTERVALS else "%Y-%m-%d"
    return time.strftime(fmt, time.gmtime(epoch + _BRT_OFF))


def _round(x):
    return round(x, 2) if isinstance(x, (int, float)) else None


def valida_plano(rng: str, interval: str) -> None:
    """Guarda client-side. Erro de plano é guardião de teste, não caminho normal."""
    if interval not in PLAN_INTERVALS:
        raise ForaDoPlano(
            f"Intervalo '{interval}' fora do plano gratuito da brapi "
            f"(permitidos: {', '.join(sorted(PLAN_INTERVALS))}). "
            "Intraday é do Yahoo por decisão do ADR-008.")
    if rng not in PLAN_RANGES:
        raise ForaDoPlano(
            f"Range '{rng}' fora do plano gratuito da brapi "
            f"(permitidos: {', '.join(sorted(PLAN_RANGES))}). "
            "Histórico longo/warmup é do Yahoo por decisão do ADR-008.")


async def _fetch_json(symbol: str, params: dict) -> dict:
    """GET com Bearer e retry curto (2 tentativas em timeout/5xx)."""
    headers = {"Authorization": "Bearer " + _token()}
    last = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
                r = await client.get(BASE + symbol, params=params, headers=headers)
            for h in ("x-ratelimit-limit", "x-ratelimit-remaining"):
                if h in r.headers:
                    LAST_RATELIMIT[h] = r.headers[h]
            if r.status_code >= 500:
                last = BrapiIndisponivel(f"brapi HTTP {r.status_code}")
            else:
                try:
                    return r.json()
                except ValueError:
                    raise BrapiIndisponivel(
                        f"brapi HTTP {r.status_code} com corpo não-JSON")
        except httpx.HTTPError as e:
            last = BrapiIndisponivel(f"brapi inacessível: {e!r}")
        await asyncio.sleep(0.4 * (attempt + 1))
    raise last


async def get_history(ticker: str, rng: str = "1mo", interval: str = "1d",
                      *, fetch_json=None) -> dict:
    """Mesmo contrato de `yahoo.get_history`:
    {"t", "currency", "candles": [{date, open, high, low, close, volume}]}.

    `close` vem de `close`, NUNCA de `adjustedClose` — paridade com o Yahoo
    atual; 25/62 velas do ITSA4 divergiam entre os dois (medição 11/08), e é a
    regra "fonte diferente = substituição, nunca merge" que contém isso.
    `fetch_json` é injetável para teste offline.
    """
    valida_plano(rng, interval)
    if not _token():
        raise RuntimeError(
            "BRAPI_TOKEN ausente no ambiente. A brapi é a fonte master do "
            "ADR-008 (era o plano B do ADR-001); sem o token o provedor não "
            "opera — defina a variável no Railway/local ou aponte "
            "B3_CANDLE_PROVIDER de volta para 'yahoo'.")

    symbol = normalize_ticker(ticker)   # brapi usa o ticker SEM sufixo .SA
    fetch = fetch_json or _fetch_json
    data = await fetch(symbol, {"range": rng, "interval": interval})

    if not isinstance(data, dict) or data.get("error"):
        msg = (data or {}).get("message") if isinstance(data, dict) else None
        code = (data or {}).get("code") if isinstance(data, dict) else None
        raise BrapiIndisponivel(
            f"brapi recusou {symbol} ({code or 'sem código'}): {msg or data!r}")

    results = data.get("results") or []
    if not results:
        raise BrapiIndisponivel(f"brapi: sem resultados para {symbol}")
    r = results[0]

    # Guardião de granularidade (mesma regra do Yahoo, yahoo.py:224): servir
    # dado fora do pedido rotulado como se fosse o pedido é pior que falhar.
    used = r.get("usedInterval")
    if used and used != interval:
        raise BrapiIndisponivel(
            f"brapi devolveu granularidade '{used}' para o intervalo "
            f"'{interval}' de {symbol} (range={rng}) — dado fora do pedido, descartado.")

    candles = []
    for v in r.get("historicalDataPrice") or []:
        close = v.get("close")
        if close is None:
            continue
        candles.append({
            "date": _candle_key(int(v["date"]), interval),
            "open": _round(v.get("open")),
            "high": _round(v.get("high")),
            "low": _round(v.get("low")),
            "close": _round(close),
            "volume": v.get("volume"),
        })
    return {"t": symbol, "currency": r.get("currency", "BRL"), "candles": candles}


# ---------------------------------------------------------------------------
# Spot (ADR-008, Fase 5) — cotação atual, 1 ticker por requisição no free
# ---------------------------------------------------------------------------
# Cache COMPARTILHADO entre usuários: o consumo escala com o universo × TTL,
# não com o número de usuários. O TTL é decidido pela fronteira (dinâmico:
# alonga sob soft stop do orçamento) — aqui só se armazena.
_quote_cache: dict = {}   # symbol -> (epoch, payload)
QUOTE_TTL_BASE = 300      # 5 min — meia atualização anunciada do free (15 min)
QUOTE_TTL_DEGRADADO = 900  # 15 min — soft stop da fatia de spot


def tem_token() -> bool:
    return bool(_token())


def quote_cached(ticker: str, ttl: float = QUOTE_TTL_BASE):
    """Cotação do cache compartilhado, se fresca o bastante. NUNCA faz rede."""
    symbol = normalize_ticker(ticker)
    ent = _quote_cache.get(symbol)
    if ent and (time.time() - ent[0]) < ttl:
        return ent[1]
    return None


def _map_quote(r: dict) -> dict:
    """Mesmo contrato de `yahoo._map_quote_row` (paridade de payload)."""
    price = r.get("regularMarketPrice")
    prev = r.get("regularMarketPreviousClose")
    change = r.get("regularMarketChangePercent")
    if change is None and price is not None and prev:
        change = (price - prev) / prev * 100
    return {
        "t": normalize_ticker(str(r.get("symbol") or "")),
        "name": r.get("longName") or r.get("shortName") or "",
        "price": price,
        "change": change,
        "previousClose": prev,
        "currency": r.get("currency", "BRL"),
    }


async def fetch_quote(ticker: str, *, fetch_json=None) -> dict:
    """Busca o spot na brapi (SEMPRE faz rede — quem controla cota/cache é a
    fronteira `candle_provider.get_quote`). Sem parâmetros de range/interval:
    o endpoint puro devolve só a cotação, sem série."""
    if not _token():
        raise RuntimeError(
            "BRAPI_TOKEN ausente no ambiente. A brapi é a fonte master do "
            "ADR-008; sem o token o spot cai no backup.")
    symbol = normalize_ticker(ticker)
    fetch = fetch_json or _fetch_json
    data = await fetch(symbol, {})
    if not isinstance(data, dict) or data.get("error"):
        msg = (data or {}).get("message") if isinstance(data, dict) else None
        code = (data or {}).get("code") if isinstance(data, dict) else None
        raise BrapiIndisponivel(
            f"brapi recusou spot de {symbol} ({code or 'sem código'}): {msg or data!r}")
    results = data.get("results") or []
    if not results:
        raise BrapiIndisponivel(f"brapi: sem cotação para {symbol}")
    q = _map_quote(results[0])
    if q.get("price") is None:
        raise BrapiIndisponivel(f"brapi: cotação sem preço para {symbol}")
    _quote_cache[symbol] = (time.time(), q)
    return q


def reset_quote_cache() -> None:
    """Para testes."""
    _quote_cache.clear()
