"""Provider Yahoo Finance para cadeias de opcoes.

O endpoint de options do Yahoo é não-oficial e pode responder 401/403/429
quando a sessão/crumb expira ou quando o Yahoo bloqueia temporariamente o
ambiente. Por isso este provider NUNCA deixa erro bruto de autenticação vazar
para a UI: tenta usar a mesma sessão robusta de `yahoo._yfetch` e, se falhar,
retorna payload vazio com warning acionável. Isso preserva a UX e mantém o
produto honesto: sem inventar cadeia de opções.
"""
from __future__ import annotations

import datetime as dt
import time
from typing import Optional

import httpx

from .catalog import yahoo_symbol
from .yahoo import HOSTS, QuoteUnavailable, _yfetch

_OPTIONS_TTL = 300
_ERROR_TTL = 60
_cache: dict[str, tuple[float, dict]] = {}


YAHOO_OPTIONS_WARNING = (
    "Yahoo Finance não autorizou ou não retornou a cadeia de opções neste momento. "
    "Isso é comum no endpoint não oficial usado pelo yfinance/Yahoo, especialmente para B3. "
    "Tente novamente em alguns minutos ou use uma fonte especializada de opções."
)


def _date_from_ts(ts: int) -> str:
    return dt.datetime.fromtimestamp(int(ts), tz=dt.timezone.utc).date().isoformat()


def _ts_from_date(s: str) -> Optional[int]:
    try:
        d = dt.date.fromisoformat(s)
        return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())
    except Exception:
        return None


def _empty_payload(ticker: str, symbol: str, expiration: Optional[str], warning: str, error: Optional[str] = None) -> dict:
    payload = {
        "ticker": ticker,
        "symbol": symbol,
        "expirations": [],
        "expiration": expiration,
        "calls": [],
        "puts": [],
        "source": "yahoo",
        "providerStatus": "degraded",
        "warning": warning,
    }
    if error:
        payload["providerError"] = error
    return payload


def _clean_contract(raw: dict, option_type: str, spot: Optional[float]) -> dict:
    strike = raw.get("strike")
    last = raw.get("lastPrice")
    bid = raw.get("bid")
    ask = raw.get("ask")
    iv = raw.get("impliedVolatility")
    dist = None
    if isinstance(spot, (int, float)) and spot > 0 and isinstance(strike, (int, float)):
        dist = round((float(strike) - float(spot)) / float(spot) * 100, 2)
    return {
        "contractSymbol": raw.get("contractSymbol"),
        "optionType": option_type,
        "strike": strike,
        "lastPrice": last,
        "bid": bid,
        "ask": ask,
        "change": raw.get("change"),
        "percentChange": raw.get("percentChange"),
        "volume": raw.get("volume") or 0,
        "openInterest": raw.get("openInterest") or 0,
        "impliedVolatility": iv,
        "inTheMoney": bool(raw.get("inTheMoney")),
        "currency": raw.get("currency"),
        "distancePct": dist,
    }


async def get_options(ticker: str, expiration: Optional[str] = None) -> dict:
    symbol = yahoo_symbol(ticker)
    date_ts = _ts_from_date(expiration) if expiration else None
    key = f"{symbol}:{date_ts or 'first'}"
    hit = _cache.get(key)
    if hit and (time.time() - hit[0]) < _OPTIONS_TTL:
        return hit[1]

    params = {"date": str(date_ts)} if date_ts else {}
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Reusa sessão/cookie/crumb, retry e rotação query1/query2 do módulo de cotações.
            data = await _yfetch(client, f"/v7/finance/options/{symbol}", params, retries=3)
    except QuoteUnavailable as e:
        payload = _empty_payload(ticker, symbol, expiration, YAHOO_OPTIONS_WARNING, str(e))
        _cache[key] = (time.time() - (_OPTIONS_TTL - _ERROR_TTL), payload)
        return payload
    except Exception as e:  # noqa: BLE001
        payload = _empty_payload(
            ticker,
            symbol,
            expiration,
            "Yahoo Finance não retornou cadeia de opções para este ativo/vencimento.",
            str(e),
        )
        _cache[key] = (time.time() - (_OPTIONS_TTL - _ERROR_TTL), payload)
        return payload

    result = (((data or {}).get("optionChain") or {}).get("result") or [])
    if not result:
        payload = _empty_payload(ticker, symbol, expiration, "Yahoo não retornou cadeia de opções para este ativo.")
        _cache[key] = (time.time(), payload)
        return payload

    root = result[0]
    quote = root.get("quote") or {}
    spot = quote.get("regularMarketPrice")
    expirations = [_date_from_ts(x) for x in (root.get("expirationDates") or [])]
    opts = (root.get("options") or [{}])[0]
    chosen_ts = opts.get("expirationDate")
    payload = {
        "ticker": ticker,
        "symbol": symbol,
        "source": "yahoo",
        "providerStatus": "ok",
        "underlyingPrice": spot,
        "currency": quote.get("currency"),
        "expirations": expirations,
        "expiration": _date_from_ts(chosen_ts) if chosen_ts else expiration,
        "calls": [_clean_contract(x, "call", spot) for x in (opts.get("calls") or [])],
        "puts": [_clean_contract(x, "put", spot) for x in (opts.get("puts") or [])],
    }
    _cache[key] = (time.time(), payload)
    return payload
