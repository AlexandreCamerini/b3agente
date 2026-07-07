"""FASE 1 — Snapshot Técnico Único (STU).

PROBLEMA: N1 (Radar), N2 (análise completa) e N3 (stop/alvo) montavam cada um
seu próprio insumo — três fetches, três janelas de corte, três formatos — e o
LLM recebia dados diferentes para o MESMO ativo no MESMO dia, gerando
conclusões divergentes.

SOLUÇÃO: para cada (ticker, período) este módulo gera UM snapshot
determinístico com TODOS os insumos — candles da janela do usuário,
indicadores (ADX/DI±, RSI/IFR2, médias 9/21/72/200, ATR, MACD, Bollinger,
estocástico, OBV), condições técnicas + score, setups detectados (clássicos +
os 7 do mercado BR) e o contexto estruturado do N2 — identificado por um
`snapshotId` (hash dos insumos). N1, N2 e N3 leem o MESMO snapshot; se dois
níveis exibem o mesmo id, o usuário sabe que leem os mesmos dados.

Disciplina de cache (mesma do candle_cache): o snapshot só é reconstruído se a
série de candles mudou (fingerprint do último candle). Determinismo garantido:
mesmos candles + mesmo período ⇒ mesmo snapshot, mesmo id.

INVARIANTES preservadas: todo cálculo é determinístico (o LLM só interpreta);
a cotação AO VIVO fica FORA do snapshot (motor de sinais separado dos preços
ao vivo) — quem precisar dela anexa por fora, sem afetar o id.
"""
import hashlib
import json
import time
from typing import Optional

from . import candle_cache, indicators, setups, technical_models
from . import candles as candles_mod

_SNAP_CACHE: dict = {}  # (ticker, period) -> snapshot (validado por fingerprint)


def reset():
    """Para testes."""
    _SNAP_CACHE.clear()


def _fingerprint(cs: list, keep: int) -> str:
    """Identidade da série já saneada: muda se (e só se) o insumo mudou."""
    last = cs[-1]
    first = cs[0]
    return "|".join(str(x) for x in (
        len(cs), keep, first.get("date"), last.get("date"),
        last.get("close"), last.get("high"), last.get("low"), last.get("volume"),
    ))


def _snapshot_id(ticker: str, period: str, fp: str) -> str:
    raw = json.dumps([ticker, period, fp], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]


def _compact_setups(sres: dict) -> list:
    """Versão enxuta dos setups para o prompt do LLM (sem o checklist inteiro)."""
    out = []
    for s in (sres or {}).get("setups") or []:
        out.append({k: s.get(k) for k in (
            "nome", "lado", "confluencia", "gatilho", "invalidacao", "alvoSugerido", "referencia",
        ) if s.get(k) is not None})
    return out


def build(ticker: str, raw_candles: list, period: Optional[str]) -> dict:
    """Constrói (ou reaproveita, se o insumo não mudou) o STU de um ativo.

    Puro em relação à rede: recebe os candles crus (de candle_cache/testes) e
    deriva tudo deterministicamente. Levanta ValueError sem histórico válido.
    """
    p = candles_mod.normalize_period(period)
    keep_req = candles_mod.resolve_keep(p)
    cs = indicators.sanitize_candles(raw_candles or [])
    if not cs:
        raise ValueError("sem histórico para " + ticker)
    fp = _fingerprint(cs, keep_req)
    key = (ticker, p)
    hit = _SNAP_CACHE.get(key)
    if hit is not None and hit.get("_fingerprint") == fp:
        return hit

    full = indicators.compute(cs)
    k = min(len(cs), keep_req)
    sl = indicators.slice_tail(cs, full["indicators"], full["summary"], k)
    # Import tardio: scanner importa este módulo; detect_conditions é pura.
    from .scanner import detect_conditions
    conds, score = detect_conditions(sl["candles"], sl["indicators"], full["summary"])
    sres = setups.detect_setups(sl["candles"], sl["indicators"])
    # Contexto do N2 SEM cotação ao vivo (determinismo + invariante do motor).
    ctx = technical_models.build_context(ticker, None, cs, model="completo", tail_n=k)
    first, last = sl["candles"][0], sl["candles"][-1]
    chg = ((last["close"] - first["close"]) / first["close"] * 100) if first.get("close") else 0.0
    sid = _snapshot_id(ticker, p, fp)
    ctx["snapshotId"] = sid
    ctx["snapshotAt"] = last.get("date")
    ctx["setupsRadar"] = {  # N2 lê os MESMOS setups que o Radar exibiu
        "veredito": sres.get("veredito"),
        "confluencia": sres.get("confluencia"),
        "melhorSetup": sres.get("melhor"),
        "setups": _compact_setups(sres),
    }
    snapshot = {
        "snapshotId": sid,
        "_fingerprint": fp,
        "ticker": ticker,
        "period": p,
        "periodBars": k,
        "asOf": last.get("date"),
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "candles": sl["candles"],
        "indicators": sl["indicators"],
        "summary": full["summary"],
        "conditions": conds,
        "scoreTecnico": score,
        "setups": sres,
        "context": ctx,
        "close": last.get("close"),
        "variacaoPeriodoPct": round(chg, 2),
    }
    _SNAP_CACHE[key] = snapshot
    return snapshot


async def get(ticker: str, period: Optional[str], loader) -> dict:
    """STU cache-first via candle_cache. `loader(rng)` é o fetch injetado
    (produção: lambda rng: yahoo.get_history(t, rng=rng); testes: fake)."""
    hist = await candle_cache.load(ticker, loader)
    snap = build(ticker, hist.get("candles") or [], period)
    return {**snap, "currency": hist.get("currency", "BRL"), "cacheStatus": hist.get("cacheStatus")}
