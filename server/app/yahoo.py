"""Cotacoes via Yahoo Finance (httpx async), com mitigacao do 429:
User-Agent de navegador + cookie + crumb, cotacoes em UMA requisicao agrupada,
retry com backoff e rotacao de host. Historico (~1 mes) por ativo, sob demanda.
"""
import asyncio
import random
import time

import httpx

from .catalog import yahoo_symbol


class QuoteUnavailable(RuntimeError):
    """Falha TRANSITORIA do Yahoo (429/401/403/timeout) — NAO significa que o
    ticker inexiste. As rotas devem responder 'tente novamente', nao '404'."""


HOSTS = ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]
BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

QUOTE_TTL = 120          # segundos
SESSION_TTL = 1800       # segundos

_quote_cache: dict = {}  # symbol -> (ts, data)
_session = {"cookie": "", "crumb": "", "ts": 0.0}
_session_lock = asyncio.Lock()


def _backoff(attempt: int) -> float:
    return min(5.0, 0.6 * (2 ** attempt)) + random.random() * 0.25


async def _build_session(client: httpx.AsyncClient) -> None:
    cookie = ""
    for url in ("https://fc.yahoo.com/", "https://finance.yahoo.com/"):
        try:
            r = await client.get(url, headers={**BASE_HEADERS, "Accept": "text/html,*/*"})
            cookies = "; ".join(f"{k}={v}" for k, v in r.cookies.items())
            if cookies:
                cookie = cookies
                break
        except httpx.HTTPError:
            continue
    crumb = ""
    try:
        r = await client.get(
            "https://query1.finance.yahoo.com/v1/test/getcrumb",
            headers={**BASE_HEADERS, "Accept": "text/plain,*/*", **({"Cookie": cookie} if cookie else {})},
        )
        txt = (r.text or "").strip()
        if r.status_code == 200 and txt and "Too Many Requests" not in txt and len(txt) <= 64:
            crumb = txt
    except httpx.HTTPError:
        pass
    _session.update(cookie=cookie, crumb=crumb, ts=time.time())


async def _ensure_session(client: httpx.AsyncClient, force: bool = False) -> dict:
    async with _session_lock:
        if force or not _session["ts"] or (time.time() - _session["ts"]) > SESSION_TTL:
            await _build_session(client)
        return _session


async def _yfetch(client: httpx.AsyncClient, path: str, params: dict, retries: int = 3) -> dict:
    last_err = None
    for attempt in range(retries + 1):
        s = await _ensure_session(client, force=(attempt > 0 and last_err == 401))
        host = HOSTS[attempt % len(HOSTS)]
        q = dict(params)
        if s["crumb"]:
            q["crumb"] = s["crumb"]
        headers = {**BASE_HEADERS, "Accept": "application/json,*/*"}
        if s["cookie"]:
            headers["Cookie"] = s["cookie"]
        try:
            r = await client.get(host + path, params=q, headers=headers)
        except httpx.HTTPError as e:
            last_err = 0
            await asyncio.sleep(_backoff(attempt))
            continue
        if r.status_code in (429, 401, 403):
            last_err = r.status_code
            if attempt < retries:
                await asyncio.sleep(_backoff(attempt))
                continue
            raise QuoteUnavailable(f"Yahoo HTTP {r.status_code}")
        r.raise_for_status()
        return r.json()
    raise QuoteUnavailable(f"Yahoo: falha apos varias tentativas ({last_err})")


def _map_quote_row(row: dict) -> dict:
    t = str(row.get("symbol", "")).replace(".SA", "")
    price = row.get("regularMarketPrice")
    change = row.get("regularMarketChangePercent")
    prev = row.get("regularMarketPreviousClose")
    if change is None and price is not None and prev:
        change = (price - prev) / prev * 100
    return {
        "t": t,
        "name": row.get("longName") or row.get("shortName") or "",
        "price": price,
        "change": change or 0,
        "previousClose": prev,
        "currency": row.get("currency", "BRL"),
    }


async def _quote_batch(client: httpx.AsyncClient, tickers: list) -> dict:
    symbols = ",".join(yahoo_symbol(t) for t in tickers)
    data = await _yfetch(client, "/v7/finance/quote", {"symbols": symbols})
    rows = (data.get("quoteResponse") or {}).get("result") or []
    out = {}
    for row in rows:
        m = _map_quote_row(row)
        if m["t"]:
            out[m["t"]] = m
    return out


async def _quote_chart(client: httpx.AsyncClient, ticker: str) -> dict:
    data = await _yfetch(client, "/v8/finance/chart/" + yahoo_symbol(ticker), {"range": "1d", "interval": "1d"})
    result = ((data.get("chart") or {}).get("result") or [None])[0]
    if not result:
        raise RuntimeError("sem dados para " + ticker)
    meta = result.get("meta") or {}
    price = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose", meta.get("previousClose"))
    change = (price - prev) / prev * 100 if price is not None and prev else 0
    return {"t": ticker, "price": price, "change": change, "previousClose": prev, "currency": meta.get("currency", "BRL")}


async def get_quotes(tickers: list) -> dict:
    fresh, need = {}, []
    now = time.time()
    for t in tickers:
        c = _quote_cache.get(yahoo_symbol(t))
        if c and (now - c[0]) < QUOTE_TTL:
            fresh[t] = c[1]
        else:
            need.append(t)
    if not need:
        return fresh
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        try:
            got = await _quote_batch(client, need)
        except Exception:
            got = {}
            for t in need:  # fallback: 1 por vez
                try:
                    got[t] = await _quote_chart(client, t)
                    await asyncio.sleep(0.15)
                except Exception as e:
                    got[t] = {"t": t, "price": None, "change": 0, "error": str(e)}
    for t in need:
        data = got.get(t) or {"t": t, "price": None, "change": 0, "error": "sem cotacao"}
        if data.get("price") is not None:
            _quote_cache[yahoo_symbol(t)] = (time.time(), data)
        fresh[t] = data
    return fresh


async def get_quote(ticker: str) -> dict:
    c = _quote_cache.get(yahoo_symbol(ticker))
    if c and (time.time() - c[0]) < QUOTE_TTL:
        return c[1]
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        try:
            batch = await _quote_batch(client, [ticker])
            data = batch.get(ticker)
        except Exception:
            data = None
        if not data or data.get("price") is None:
            data = await _quote_chart(client, ticker)
    if data and data.get("price") is not None:
        _quote_cache[yahoo_symbol(ticker)] = (time.time(), data)
    return data


def _round(x):
    return round(x, 2) if isinstance(x, (int, float)) else None


async def get_history(ticker: str, rng: str = "1mo") -> dict:
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        data = await _yfetch(client, "/v8/finance/chart/" + yahoo_symbol(ticker), {"range": rng, "interval": "1d"})
    result = ((data.get("chart") or {}).get("result") or [None])[0]
    if not result:
        raise RuntimeError("Yahoo: sem historico para " + ticker)
    ts = result.get("timestamp") or []
    q = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    candles = []
    for i, t in enumerate(ts):
        close = (q.get("close") or [None] * len(ts))[i]
        if close is None:
            continue
        candles.append({
            "date": time.strftime("%Y-%m-%d", time.gmtime(t)),
            "open": _round((q.get("open") or [None] * len(ts))[i]),
            "high": _round((q.get("high") or [None] * len(ts))[i]),
            "low": _round((q.get("low") or [None] * len(ts))[i]),
            "close": _round(close),
            "volume": (q.get("volume") or [None] * len(ts))[i],
        })
    return {"t": ticker, "currency": (result.get("meta") or {}).get("currency", "BRL"), "candles": candles}
