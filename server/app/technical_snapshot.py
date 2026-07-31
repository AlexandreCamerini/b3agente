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


def _snapshot_id(ticker: str, period: str, fp: str, interval: str = "1d") -> str:
    """ADR-001 (Decisão 5): o INTERVALO entra na identidade.

    Sem ele, um snapshot diário e um intraday do mesmo ativo e período geram
    ids que não se distinguem, e o `snapshotId` que amarra N1/N2/N3 não diz de
    qual timeframe veio a leitura — a "contradição entre camadas" que o
    masstest existe para pegar. O default "1d" mantém o id de todo o app
    inalterado (o argumento nem entra no hash quando é diário)."""
    campos = [ticker, period, fp] if (interval or "1d") == "1d" else [ticker, period, fp, interval]
    raw = json.dumps(campos, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]


def _compact_setups(sres: dict) -> list:
    """Versão enxuta dos setups para o prompt do LLM (sem o checklist inteiro)."""
    out = []
    for s in (sres or {}).get("setups") or []:
        out.append({k: s.get(k) for k in (
            "nome", "lado", "confluencia", "gatilho", "invalidacao", "alvoSugerido", "referencia",
        ) if s.get(k) is not None})
    return out


def _descarta_barra_em_formacao(cs: list, interval: str) -> tuple:
    """ADR-001 (item 1b): no intraday, a ÚLTIMA vela é descartada.

    Por quê: `candle_cache.merge_candles` revalida a última vela por contrato
    ("fresco vence"), justamente para atualizar o candle corrente. Ou seja, a
    última vela da série é sempre a que ainda está se formando. Com o laço de 5
    min e barras de 15m, cada barra seria lida TRÊS vezes antes de existir de
    verdade — e uma condição vista às 11:32 pode não existir mais às 11:45.

    Por que descartar SEMPRE, e não só quando a barra está aberta: saber se ela
    fechou exigiria o relógio, e o STU é determinístico por contrato (mesmo
    insumo ⇒ mesmo snapshotId). Trocar isso por um snapshot que muda sozinho
    com o tempo quebraria a amarração de N1/N2/N3. O preço é uma barra de
    latência, constante e declarada — barato perto de afirmar que algo ocorreu
    quando ainda pode desocorrer.

    O diário não muda: lá a "vela em formação" é o pregão do dia, o produto já
    é explícito sobre isso, e descartá-la jogaria fora o dia inteiro.
    """
    if (interval or "1d") not in candles_mod.BARS_PER_SESSION or interval in ("1d", "1wk"):
        return cs, None
    if len(cs) < 2:            # série curta demais: descartar deixaria nada
        return cs, None
    return cs[:-1], cs[-1].get("date")


def build(ticker: str, raw_candles: list, period: Optional[str], interval: str = "1d") -> dict:
    """Constrói (ou reaproveita, se o insumo não mudou) o STU de um ativo.

    Puro em relação à rede: recebe os candles crus (de candle_cache/testes) e
    deriva tudo deterministicamente. Levanta ValueError sem histórico válido.

    No INTRADAY analisa só barras FECHADAS (ver `_descarta_barra_em_formacao`).
    """
    p = candles_mod.normalize_period(period)
    # ADR-002 (Decisão 3): a janela é contada em VELAS DO INTERVALO, não em
    # pregões — senão "1mo" com 15m entregava 22 velas (5,5h) em vez de um mês.
    keep_req = candles_mod.resolve_keep(p, interval)
    cs = indicators.sanitize_candles(raw_candles or [])
    if not cs:
        raise ValueError("sem histórico para " + ticker)
    # ADR-001 (1b): antes de QUALQUER cálculo — indicadores, setups e o
    # fingerprint têm que enxergar a mesma série, a das barras fechadas.
    cs, barra_em_formacao = _descarta_barra_em_formacao(cs, interval)
    if not cs:
        raise ValueError("sem barra fechada para " + ticker)
    fp = _fingerprint(cs, keep_req)
    # ADR-001: o intervalo faz parte da CHAVE do cache de snapshot. Antes,
    # (ticker, período) fazia diário e intraday disputarem a mesma entrada.
    key = (ticker, p, interval or "1d")
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
    # ADR-001 (1d): série FURADA mente com cara de certa. A lacuna entra no
    # dataQuality (que a IA já lê) e no topo do snapshot, para a UI poder avisar.
    lacunas = candles_mod.detectar_lacunas(sl["candles"], interval)
    if isinstance(ctx.get("dataQuality"), dict):
        ctx["dataQuality"]["lacunaIntraday"] = lacunas["temLacuna"]
        ctx["dataQuality"]["velasFaltando"] = lacunas["velasFaltando"]
        if lacunas["temLacuna"]:
            # Série furada não sustenta leitura confiante, por mais candles que tenha.
            ctx["dataQuality"]["tetoConfianca"] = "baixa"
    sid = _snapshot_id(ticker, p, fp, interval or "1d")
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
        "interval": interval or "1d",
        "periodBars": k,
        # ADR-001 (1b): `asOf` é a última barra FECHADA — é dela que o produto
        # pode dizer "a condição ocorreu". `barraEmFormacao` é a que foi
        # descartada: existe no payload para a UI/IA poderem ser explícitas
        # ("barra das 11:30, fechada") em vez de insinuar tempo real.
        "asOf": last.get("date"),
        "barraEmFormacao": barra_em_formacao,
        "lacunas": lacunas,
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


async def get(ticker: str, period: Optional[str], loader, interval: str = "1d") -> dict:
    """STU cache-first via candle_cache. `loader(rng)` é o fetch injetado
    (produção: lambda rng: yahoo.get_history(t, rng=rng); testes: fake).

    `interval` segmenta cache de candles E identidade do snapshot (ADR-001)."""
    hist = await candle_cache.load(ticker, loader, interval=interval or "1d")
    snap = build(ticker, hist.get("candles") or [], period, interval=interval or "1d")
    return {**snap, "currency": hist.get("currency", "BRL"), "cacheStatus": hist.get("cacheStatus")}
