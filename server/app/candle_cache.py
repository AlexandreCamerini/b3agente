"""Objetivo 5 — cache de candles históricos no servidor.

Candles passados NÃO mudam: armazenamos a série longa por símbolo e, nas próximas
vezes, buscamos no Yahoo apenas o INCREMENTO recente (poucos dias) e SEMPRE
revalidamos o candle mais recente (que muda intradiário). Isso evita rebaixar a
série inteira (2 anos) a cada análise.

Cuidados tratados:
  • o candle do dia corrente NÃO é imutável → a janela recente o sobrescreve;
  • mudança de intervalo segmenta o cache (chave = símbolo + intervalo);
  • limite de tamanho (_MAX) para não crescer sem fim.

FASE 5 (performance): o cache agora tem DOIS níveis.
  L1 = memória do processo (como sempre foi; leitura instantânea).
  L2 = SQLite (tabela candle_cache, no MESMO arquivo do app — volume /data no
       Railway). Reinício/redeploy REIDRATA do L2 e busca só o delta recente,
       em vez de rebaixar 2 anos do universo inteiro — era a principal causa da
       "demora para atualizar" depois de cada deploy.
Falha de SQLite nunca derruba o fluxo: degrada silenciosamente para o modo
memória-apenas (comportamento antigo). Testável offline (test_candle_cache).
"""
import json
import time
from typing import Awaitable, Callable, Optional

from . import db as _dbmod

FULL_RANGE = "2y"      # warmup p/ médias longas na 1ª carga (cache miss)
RECENT_RANGE = "1mo"   # janela buscada nas próximas vezes (delta + revalidação)
_MAX = 600             # ~2,4 anos de pregões; teto de tamanho
_MIN_DELTA_INTERVAL = 45.0  # não rebusca o delta se atualizou há < 45s

_CACHE: dict = {}      # "SYMBOL@interval" -> {"candles":[...], "currency":str, "at":float}

# ------------------------- L2 persistente (SQLite) --------------------------
# OPT-IN explícito: o main.py injeta a conexão no boot (configure_db(conn)).
# Sem injeção (suítes puras, uso avulso do módulo) o comportamento é o antigo:
# memória apenas — nenhum teste passa a tocar disco por acidente.
_DB_ENABLED = False
_DB_CONN = None


def configure_db(conn=None, enabled: bool = True) -> None:
    """Boot/testes: injeta a conexão do L2 (ou desliga a persistência)."""
    global _DB_CONN, _DB_ENABLED
    _DB_CONN = conn
    _DB_ENABLED = bool(enabled and conn is not None)


def _conn():
    return _DB_CONN if _DB_ENABLED else None


def _db_get(k: str) -> Optional[dict]:
    try:
        c = _conn()
        if c is None:
            return None
        row = c.execute("SELECT currency, candles, at FROM candle_cache WHERE k = ?", (k,)).fetchone()
        if not row:
            return None
        candles = json.loads(row[1])
        if not isinstance(candles, list) or not candles:
            return None
        return {"candles": candles, "currency": row[0] or "BRL", "at": float(row[2] or 0)}
    except Exception:  # noqa: BLE001 — L2 é otimização, nunca derruba
        return None


def _db_put(k: str, ent: dict) -> None:
    try:
        c = _conn()
        if c is None:
            return
        c.execute(
            "INSERT INTO candle_cache(k, currency, candles, at) VALUES(?,?,?,?) "
            "ON CONFLICT(k) DO UPDATE SET currency=excluded.currency, candles=excluded.candles, at=excluded.at",
            (k, ent.get("currency", "BRL"), json.dumps(ent.get("candles") or []), float(ent.get("at") or 0)),
        )
        c.commit()
    except Exception:  # noqa: BLE001
        pass


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

    # FASE 5: L1 vazio => tenta reidratar do L2 (SQLite). Série persistida entra
    # como cache existente: o fluxo abaixo busca só o DELTA recente, não os 2 anos.
    if (not ent or not ent.get("candles")):
        persisted = _db_get(k)
        if persisted:
            _CACHE[k] = ent = persisted

    if not ent or not ent.get("candles"):
        # BLOCO A1 — robustez: 404/erro do provedor não pode vazar stack técnico.
        # 1 retry em janela menor (símbolos com histórico curto/instável no Yahoo)
        # e, persistindo, erro LIMPO e amigável para a UI exibir no card.
        try:
            full = await fetch(FULL_RANGE)
        except Exception:  # noqa: BLE001
            try:
                full = await fetch("1y")
            except Exception:  # noqa: BLE001
                raise ValueError(
                    f"Sem histórico disponível para {symbol} no provedor de dados — tente novamente mais tarde ou avalie outro ativo."
                )
        candles = (full.get("candles") or [])[-_MAX:]
        _CACHE[k] = {"candles": candles, "currency": full.get("currency", "BRL"), "at": t}
        _db_put(k, _CACHE[k])  # FASE 5: write-through no L2 (sobrevive a redeploy)
        return {"t": symbol, "currency": _CACHE[k]["currency"], "candles": candles, "cacheStatus": "miss"}

    # já atualizado há pouco: serve do cache sem bater no provedor
    if (t - ent.get("at", 0)) < _MIN_DELTA_INTERVAL:
        return {"t": symbol, "currency": ent.get("currency", "BRL"), "candles": ent["candles"], "cacheStatus": "fresh"}

    # cache hit: busca só a janela recente, funde e revalida o último candle.
    # BLOCO A1: falha do delta NÃO derruba — serve o cache existente (stale).
    try:
        recent = await fetch(RECENT_RANGE)
    except Exception:  # noqa: BLE001
        return {"t": symbol, "currency": ent.get("currency", "BRL"), "candles": ent["candles"], "cacheStatus": "stale"}
    merged = merge_candles(ent["candles"], recent.get("candles") or [])[-_MAX:]
    ent["candles"] = merged
    ent["at"] = t
    if recent.get("currency"):
        ent["currency"] = recent["currency"]
    _db_put(k, ent)  # FASE 5: write-through no L2
    return {"t": symbol, "currency": ent.get("currency", "BRL"), "candles": merged, "cacheStatus": "delta"}
