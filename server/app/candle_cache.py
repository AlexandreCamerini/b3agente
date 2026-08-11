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

# ADR-001 — janelas POR INTERVALO. Pedir `2y` com `5m` devolve HTTP 422, e
# `max` com intervalo intraday devolve velas MENSAIS com status 200 (medido em
# 30/07/2026). Os limites abaixo são os máximos REAIS que o Yahoo aceita, com
# folga para SMA200/EMA72 na carga fria.
_RANGES = {
    "1m":  ("7d", "1d"),     # 1m só vai até 7 dias
    "2m":  ("1mo", "1d"),
    "5m":  ("1mo", "1d"),
    "15m": ("1mo", "1d"),
    "30m": ("1mo", "1d"),
    "90m": ("1mo", "1d"),
    "60m": ("6mo", "5d"),    # horário aceita até 2y; 6mo já dá 855 velas
    "1h":  ("6mo", "5d"),
}


def ranges_for(interval: str) -> tuple:
    """(janela cheia, janela do delta) do intervalo. Default = diário."""
    return _RANGES.get(interval or "1d", (FULL_RANGE, RECENT_RANGE))


def persiste_no_l2(interval: str) -> bool:
    """ADR-001 (Decisão 4): o L2 é SÓ do diário.

    O L2 existe para não rebaixar 2 anos de candles diários a cada redeploy.
    Essa razão não transfere para o intraday, onde a janela cheia é UMA
    requisição: reidratar o universo inteiro custou 0,45 s medidos da produção.
    Persistir custaria 1,65 GB/dia de reescrita (o blob inteiro é regravado a
    cada update) para poupar esse 0,45 s. Intraday vive só no L1.
    """
    return (interval or "1d") not in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h")

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
        row = c.execute("SELECT currency, candles, at, src FROM candle_cache WHERE k = ?", (k,)).fetchone()
        if not row:
            return None
        candles = json.loads(row[1])
        if not isinstance(candles, list) or not candles:
            return None
        return {"candles": candles, "currency": row[0] or "BRL",
                "at": float(row[2] or 0), "src": row[3]}
    except Exception:  # noqa: BLE001 — L2 é otimização, nunca derruba
        return None


def _db_put(k: str, ent: dict) -> None:
    try:
        c = _conn()
        if c is None:
            return
        c.execute(
            "INSERT INTO candle_cache(k, currency, candles, at, src) VALUES(?,?,?,?,?) "
            "ON CONFLICT(k) DO UPDATE SET currency=excluded.currency, "
            "candles=excluded.candles, at=excluded.at, src=excluded.src",
            (k, ent.get("currency", "BRL"), json.dumps(ent.get("candles") or []),
             float(ent.get("at") or 0), ent.get("src")),
        )
        c.commit()
    except Exception:  # noqa: BLE001
        pass


def _key(symbol: str, interval: str) -> str:
    return (symbol or "") + "@" + (interval or "1d")


def merge_candles(old: list, new: list) -> list:
    """Funde mantendo 1 candle por CHAVE; `new` SOBRESCREVE `old` na mesma
    chave (revalida o último/atual). Ordenado pela chave, sem fabricar nada.

    A chave é o campo `date`, cuja RESOLUÇÃO acompanha o intervalo: "AAAA-MM-DD"
    no diário e "AAAA-MM-DD HH:MM" (fuso da bolsa) no intraday — ver
    `yahoo._candle_key`. Com data sozinha, 617 velas de 15m viravam 22 chaves e
    96% dos candles sumiam em silêncio. Os dois formatos ordenam
    lexicograficamente na ordem cronológica, e nunca se misturam na mesma
    entrada porque a chave do cache já segmenta por intervalo."""
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
    full_range, recent_range = ranges_for(interval)
    l2 = persiste_no_l2(interval)
    ent = _CACHE.get(k)

    # FASE 5: L1 vazio => tenta reidratar do L2 (SQLite). Série persistida entra
    # como cache existente: o fluxo abaixo busca só o DELTA recente, não os 2 anos.
    # ADR-001: intraday não usa L2 nem na leitura — reidratar custa 1 requisição.
    if l2 and (not ent or not ent.get("candles")):
        persisted = _db_get(k)
        if persisted:
            _CACHE[k] = ent = persisted

    if not ent or not ent.get("candles"):
        # BLOCO A1 — robustez: 404/erro do provedor não pode vazar stack técnico.
        # 1 retry em janela menor (símbolos com histórico curto/instável no Yahoo)
        # e, persistindo, erro LIMPO e amigável para a UI exibir no card.
        try:
            full = await fetch(full_range)
        except Exception:  # noqa: BLE001
            try:
                # Retry em janela menor. No diário era "1y"; no intraday a
                # janela menor é a do delta — "1y" com 5m só devolveria 422.
                full = await fetch("1y" if l2 else recent_range)
            except Exception:  # noqa: BLE001
                raise ValueError(
                    f"Sem histórico disponível para {symbol} no provedor de dados — tente novamente mais tarde ou avalie outro ativo."
                )
        candles = (full.get("candles") or [])[-_MAX:]
        _CACHE[k] = {"candles": candles, "currency": full.get("currency", "BRL"),
                     "at": t, "src": full.get("source")}
        if l2:
            _db_put(k, _CACHE[k])  # FASE 5: write-through no L2 (sobrevive a redeploy)
        return {"t": symbol, "currency": _CACHE[k]["currency"], "candles": candles,
                "cacheStatus": "miss", "source": _CACHE[k]["src"]}

    # já atualizado há pouco: serve do cache sem bater no provedor
    if (t - ent.get("at", 0)) < _MIN_DELTA_INTERVAL:
        return {"t": symbol, "currency": ent.get("currency", "BRL"), "candles": ent["candles"],
                "cacheStatus": "fresh", "source": ent.get("src")}

    # cache hit: busca só a janela recente, funde e revalida o último candle.
    # BLOCO A1: falha do delta NÃO derruba — serve o cache existente (stale).
    try:
        recent = await fetch(recent_range)
    except Exception:  # noqa: BLE001
        return {"t": symbol, "currency": ent.get("currency", "BRL"), "candles": ent["candles"],
                "cacheStatus": "stale", "source": ent.get("src")}
    # ADR-008 (Fase 4, errata da decisão 3): no DIÁRIO o merge entre fontes é
    # PERMITIDO — warmup Yahoo (2y) + delta brapi (1mo) convivem porque ambas
    # entregam o print BRUTO do mesmo pregão (validado ao vivo em 11/08/2026:
    # 21 dias de PETR4 com open/close/volume IDÊNTICOS; o cliente brapi usa
    # `close`, nunca `adjustedClose`). `src` registra a fonte da última escrita
    # — é o acervo próprio de histórico pedido pelo Alex em 11/08: o L2
    # acumula os deltas diários e a série sobrevive a deploy.
    merged = merge_candles(ent["candles"], recent.get("candles") or [])[-_MAX:]
    ent["candles"] = merged
    ent["at"] = t
    if recent.get("source"):
        ent["src"] = recent["source"]
    if recent.get("currency"):
        ent["currency"] = recent["currency"]
    if l2:
        _db_put(k, ent)  # FASE 5: write-through no L2
    return {"t": symbol, "currency": ent.get("currency", "BRL"), "candles": merged,
            "cacheStatus": "delta", "source": ent.get("src")}


# ---------------------------------------------------------------------------
# ADR-008 (controle de utilização): NADA buscado se perde — o spot alimenta a
# vela do dia corrente do ACERVO próprio (a série 1d que o L2 persiste).
# ---------------------------------------------------------------------------
_BRT_OFF = -3 * 3600


def atualiza_vela_do_dia(symbol: str, price, src: str = None,
                         currency: str = None, volume=None, now: float = None) -> bool:
    """Dobra um spot na vela diária de HOJE: high/low esticam, close atualiza.

    Só atua quando a série 1d JÁ EXISTE no cache/L2 — criar uma entrada de
    vela única faria `load()` pular o warmup FULL_RANGE e nascer uma série de
    1 candle. Devolve True se gravou. Não mexe em `at` (não é revalidação de
    série; o delta continua no seu próprio ritmo).
    """
    if not isinstance(price, (int, float)):
        return False
    k = _key(symbol, "1d")
    ent = _CACHE.get(k)
    if (not ent or not ent.get("candles")) and persiste_no_l2("1d"):
        persisted = _db_get(k)
        if persisted:
            _CACHE[k] = ent = persisted
    if not ent or not ent.get("candles"):
        return False
    t = now if now is not None else time.time()
    hoje = time.strftime("%Y-%m-%d", time.gmtime(t + _BRT_OFF))
    p = round(float(price), 2)
    ultima = ent["candles"][-1]
    if ultima.get("date") == hoje:
        ultima["close"] = p
        if isinstance(ultima.get("high"), (int, float)):
            ultima["high"] = max(ultima["high"], p)
        else:
            ultima["high"] = p
        if isinstance(ultima.get("low"), (int, float)):
            ultima["low"] = min(ultima["low"], p)
        else:
            ultima["low"] = p
        if isinstance(volume, (int, float)) and volume >= (ultima.get("volume") or 0):
            ultima["volume"] = volume
    elif ultima.get("date", "") < hoje:
        ent["candles"].append({"date": hoje, "open": p, "high": p, "low": p,
                               "close": p, "volume": volume if isinstance(volume, (int, float)) else 0})
        ent["candles"] = ent["candles"][-_MAX:]
    else:
        return False   # spot mais velho que a série — nunca reescreve o passado
    if src:
        ent["src"] = src
    if currency:
        ent["currency"] = currency
    if persiste_no_l2("1d"):
        _db_put(k, ent)
    return True
