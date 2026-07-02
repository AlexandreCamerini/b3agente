"""Objetivo 5 — cache de candles históricos no servidor.

Candles passados NÃO mudam: armazenamos a série longa por símbolo e, nas próximas
vezes, buscamos no Yahoo apenas o INCREMENTO recente (poucos dias) e SEMPRE
revalidamos o candle mais recente (que muda intradiário). Isso evita rebaixar a
série inteira (2 anos) a cada análise.

Cuidados tratados:
  • o candle do dia corrente NÃO é imutável → a janela recente o sobrescreve;
  • mudança de intervalo segmenta o cache (chave = símbolo + intervalo);
  • limite de tamanho (_MAX) para não crescer sem fim.

Em memória por processo (como o _TECH_CACHE). Reinício do Railway reaquece no
1º acesso (busca cheia). Persistir em SQLite é evolução futura, não necessária
para o ganho de rede.
"""
import time
from typing import Awaitable, Callable

FULL_RANGE = "2y"      # warmup p/ médias longas na 1ª carga (cache miss)
RECENT_RANGE = "1mo"   # janela buscada nas próximas vezes (delta + revalidação)
_MAX = 600             # ~2,4 anos de pregões; teto de tamanho
_MIN_DELTA_INTERVAL = 45.0  # não rebusca o delta se atualizou há < 45s

_CACHE: dict = {}      # "SYMBOL@interval" -> {"candles":[...], "currency":str, "at":float}


def _key(symbol: str, interval: str) -> str:
    return (symbol or "") + "@" + (interval or "1d")


def merge_candles(old: list, new: list) -> list:
    """Funde mantendo 1 candle por data; `new` SOBRESCREVE `old` na mesma data
    (revalida o último/atual). Resultado ordenado por data, sem fabricar nada."""
    by_date = {}
    for c in old or []:
        d = c.get("date")
        if d:
            by_date[d] = c
    for c in new or []:
        d = c.get("date")
        if d:
            by_date[d] = c  # fresco vence (revalidação do candle corrente)
    return [by_date[d] for d in sorted(by_date.keys())]


def reset():
    """Para testes."""
    _CACHE.clear()


def stats() -> dict:
    return {k: {"n": len(v["candles"]), "at": v["at"]} for k, v in _CACHE.items()}


async def load(
    symbol: str,
    fetch: Callable[[str], Awaitable[dict]],
    interval: str = "1d",
    now: float = None,
) -> dict:
    """Retorna {"t","currency","candles","cacheStatus"} usando o cache.

    `fetch(rng)` deve devolver {"candles":[...], "currency":...} do provedor.
    cacheStatus: "miss" (1ª carga, série cheia) | "delta" (só o recente, fundido)
    | "fresh" (atualizado há pouco, sem rebuscar).
    """
    t = now if now is not None else time.time()
    k = _key(symbol, interval)
    ent = _CACHE.get(k)

    if not ent or not ent.get("candles"):
        full = await fetch(FULL_RANGE)
        candles = (full.get("candles") or [])[-_MAX:]
        _CACHE[k] = {"candles": candles, "currency": full.get("currency", "BRL"), "at": t}
        return {"t": symbol, "currency": _CACHE[k]["currency"], "candles": candles, "cacheStatus": "miss"}

    # já atualizado há pouco: serve do cache sem bater no provedor
    if (t - ent.get("at", 0)) < _MIN_DELTA_INTERVAL:
        return {"t": symbol, "currency": ent.get("currency", "BRL"), "candles": ent["candles"], "cacheStatus": "fresh"}

    # cache hit: busca só a janela recente, funde e revalida o último candle
    recent = await fetch(RECENT_RANGE)
    merged = merge_candles(ent["candles"], recent.get("candles") or [])[-_MAX:]
    ent["candles"] = merged
    ent["at"] = t
    if recent.get("currency"):
        ent["currency"] = recent["currency"]
    return {"t": symbol, "currency": ent.get("currency", "BRL"), "candles": merged, "cacheStatus": "delta"}
