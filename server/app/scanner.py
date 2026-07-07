"""BLOCO 3 — Radar de mercado (aditivo).

Varre um UNIVERSO de ativos da B3 e descreve, por ativo, as CONDIÇÕES TÉCNICAS
detectadas pelo motor de sinais existente (indicators.py) — com um score de
INTENSIDADE (quantas/quão marcantes são as condições), sem direção nem
recomendação. Guardrail inegociável do produto: nenhum output sugere comprar,
vender ou "entrar agora"; os rótulos são descritivos e educacionais.

Arquitetura (nada novo de infraestrutura):
  • cache-first: cada ativo passa por candle_cache.load (miss=série cheia 2y;
    delta=só o recente; fresh<45s=zero rede) — a 1ª varredura do dia é a única
    cara; as seguintes são quase gratuitas;
  • fetch ESCALONADO: semáforo de concorrência + espaçamento mínimo entre
    chamadas REAIS ao provedor (cache "fresh" não conta), para não tomar 429;
  • motor de sinais REUTILIZADO: indicators.compute/slice_tail — nenhuma
    duplicação de cálculo; o período do usuário (candlePeriod) entra via
    candles.resolve_keep, nunca hardcoded;
  • cache do RESULTADO por (período, universo) com TTL curto — toques
    repetidos no botão não refazem a varredura.

Universo: lista embutida aproximando a composição do IBOV (muda a cada
quadrimestre — atualizar aqui quando a B3 rebalancear), sobreponível por:
  • env B3_SCAN_UNIVERSE="PETR4,VALE3,..." (Railway), ou
  • query ?tickers=PETR4,VALE3 (por chamada, com teto).
Símbolos inexistentes/deslistados não derrubam a varredura: caem em `errors`.
"""
import asyncio
import os
import time
from typing import Optional

from . import candle_cache, indicators, setups, technical_snapshot
from . import candles as candles_mod
from .tickers import normalize_ticker

# Aproximação da composição do IBOV (ativos líquidos da B3). Atualizável a cada
# rebalanceamento quadrimestral; a fonte da verdade operacional pode ser a env
# B3_SCAN_UNIVERSE sem redeploy de código.
DEFAULT_UNIVERSE = [
    "PETR4", "PETR3", "VALE3", "ITUB4", "BBDC4", "BBDC3", "BBAS3", "B3SA3",
    "ABEV3", "WEGE3", "ELET3", "ELET6", "RENT3", "PRIO3", "SUZB3", "EQTL3",
    "RADL3", "VIVT3", "ITSA4", "JBSS3", "BPAC11", "RDOR3", "HAPV3", "LREN3",
    "MGLU3", "RAIL3", "CSAN3", "UGPA3", "VBBR3", "GGBR4", "CSNA3", "USIM5",
    "CMIN3", "BRAP4", "EMBR3", "CYRE3", "MRVE3", "ENGI11", "ENEV3", "EGIE3",
    "CPLE6", "CMIG4", "TAEE11", "CPFE3", "AURE3", "SBSP3", "TIMS3", "TOTS3",
    "BBSE3", "CXSE3", "PSSA3", "SANB11", "MULT3", "IGTI11", "ALOS3", "HYPE3",
    "ASAI3", "CRFB3", "NTCO3", "BEEF3", "MRFG3", "BRFS3", "SLCE3", "SMTO3",
    "RAIZ4", "RECV3", "VAMO3", "FLRY3", "KLBN11", "DXCO3", "BRKM5", "GOAU4",
    "COGN3", "YDUQ3",
]

MAX_UNIVERSE = 120          # teto de símbolos por varredura (env/override)
CONCURRENCY = 4             # chamadas simultâneas ao pipeline por ativo
MIN_FETCH_GAP_S = 0.15      # espaçamento mínimo entre chamadas REAIS ao provedor
SCAN_TTL_S = 60.0           # resultado da varredura vale por 60s (por período+universo)

DISCLAIMER = (
    "Radar educacional: descreve condições técnicas e setups didáticos detectados em "
    "dados passados, sem garantia de resultado e sem qualquer recomendação de "
    "investimento. A confluência mede a ADERÊNCIA do ativo a um padrão de estudo "
    "(percentual de critérios atendidos), não probabilidade de acerto nem atratividade. "
    "Use para estudar como os padrões se formam."
)

_SCAN_CACHE: dict = {}      # "period|t1,t2,..." -> (monotonic_ts, payload)


def reset():
    """Para testes."""
    _SCAN_CACHE.clear()


def get_universe(override: Optional[str] = None) -> list:
    """Resolve o universo: override (query) > env B3_SCAN_UNIVERSE > default.
    Normaliza cada ticker (maiúsculo, sem .SA), remove duplicados e aplica teto."""
    raw = (override or "").strip() or (os.environ.get("B3_SCAN_UNIVERSE") or "").strip()
    if not raw:
        return list(DEFAULT_UNIVERSE)
    out, seen = [], set()
    for piece in raw.split(","):
        t = normalize_ticker(piece)
        if len(t) >= 4 and t not in seen:
            seen.add(t)
            out.append(t)
    return out[:MAX_UNIVERSE] if out else list(DEFAULT_UNIVERSE)


# ---------------------------------------------------------------------------
# Condições técnicas (puro/testável). Rótulos DESCRITIVOS em PT-BR — nunca
# imperativos ("compre", "venda", "entre agora" são proibidos pelo guardrail).
# ---------------------------------------------------------------------------

def _tail(arr, n):
    vals = [x for x in (arr or []) if x is not None]
    return vals[-n:] if vals else []


def _sign_flip(arr, n=3):
    """True se a série trocou de sinal dentro dos últimos `n` valores válidos."""
    vals = _tail(arr, n + 1)
    if len(vals) < 2:
        return False
    signs = [1 if v > 0 else (-1 if v < 0 else 0) for v in vals]
    return any(a != 0 and b != 0 and a != b for a, b in zip(signs, signs[1:]))


def _crossed(a_arr, b_arr, n=5):
    """True se (a-b) trocou de sinal nos últimos `n` pontos onde ambos existem."""
    pairs = [(a, b) for a, b in zip(a_arr or [], b_arr or []) if a is not None and b is not None]
    if len(pairs) < 2:
        return False
    diffs = [a - b for a, b in pairs][-(n + 1):]
    signs = [1 if d > 0 else (-1 if d < 0 else 0) for d in diffs]
    return any(x != 0 and y != 0 and x != y for x, y in zip(signs, signs[1:]))


def detect_conditions(candles: list, ind: dict, summary: dict) -> tuple:
    """Traduz o estado do motor de sinais em (condições[], score 0-100).

    O score soma PESOS de condições ativas — eventos recentes (cruzamentos,
    extremos do período) pesam mais que estados contínuos. É intensidade de
    atividade técnica, não direção. Curto-circuito educacional: rótulos citam
    o indicador e o critério, para o usuário aprender a leitura.
    """
    conds, weights = [], []

    def add(label, w):
        conds.append(label)
        weights.append(w)

    s = summary or {}
    closes = [c.get("close") for c in candles or [] if c.get("close") is not None]
    last_close = closes[-1] if closes else None

    # RSI (estado)
    if s.get("rsiState") == "sobrecomprado":
        add("RSI em sobrecompra (≥ 70)", 15)
    elif s.get("rsiState") == "sobrevendido":
        add("RSI em sobrevenda (≤ 30)", 15)

    # Estocástico (estado + cruzamento recente K/D)
    if s.get("stochState") == "sobrecomprado":
        add("Estocástico em sobrecompra (≥ 80)", 10)
    elif s.get("stochState") == "sobrevendido":
        add("Estocástico em sobrevenda (≤ 20)", 10)
    if _crossed(ind.get("stochK"), ind.get("stochD"), n=3):
        add("Cruzamento recente do estocástico (%K × %D)", 10)

    # MACD (estado do histograma + virada recente)
    if s.get("macdState") == "alta":
        add("Histograma MACD positivo", 5)
    elif s.get("macdState") == "baixa":
        add("Histograma MACD negativo", 5)
    if _sign_flip(ind.get("macdHist"), n=3):
        add("Virada recente do histograma MACD", 20)

    # Médias móveis (tendência + cruzamento recente 20/50 + preço vs SMA20)
    if s.get("trend") == "alta":
        add("SMA20 acima da SMA50 no fim da janela", 5)
    elif s.get("trend") == "baixa":
        add("SMA20 abaixo da SMA50 no fim da janela", 5)
    if _crossed(ind.get("sma20"), ind.get("sma50"), n=5):
        add("Cruzamento recente das médias 20/50", 20)
    if s.get("priceVsSma20") == "acima":
        add("Preço acima da SMA20", 5)
    elif s.get("priceVsSma20") == "abaixo":
        add("Preço abaixo da SMA20", 5)

    # Bandas de Bollinger (fechamento junto às bandas)
    bu, bl = s.get("bbUpper"), s.get("bbLower")
    if last_close is not None and bu is not None and last_close >= bu:
        add("Fechamento na banda superior de Bollinger ou acima", 10)
    elif last_close is not None and bl is not None and last_close <= bl:
        add("Fechamento na banda inferior de Bollinger ou abaixo", 10)

    # Extremos DO PERÍODO escolhido pelo usuário — é o que faz o resultado
    # mudar visivelmente ao trocar 1M/3M/6M/1A/2A na Config.
    if closes and last_close is not None:
        hi, lo = max(closes), min(closes)
        if hi > 0 and last_close >= 0.98 * hi:
            add("Preço próximo da máxima do período analisado", 15)
        if lo > 0 and last_close <= 1.02 * lo:
            add("Preço próximo da mínima do período analisado", 15)

    return conds, min(100, sum(weights))


# ---------------------------------------------------------------------------
# Varredura do universo (assíncrona, cache-first, escalonada)
# ---------------------------------------------------------------------------

# BLOCO B1 — progresso observável (mata a percepção de app congelado): o scan
# grava estado incremental aqui; GET /api/scan/progress expõe para a UI animar.
SCAN_PROGRESS = {"ativo": False, "fase": "", "atual": "", "feitos": 0, "total": 0, "period": "", "ultimos": [], "at": 0.0}


def _progress_reset(total: int, period: str):
    SCAN_PROGRESS.update(ativo=True, fase="varrendo", atual="", feitos=0, total=total, period=period, ultimos=[], at=time.time())


def _progress_tick(symbol: str, cache_status: str = ""):
    SCAN_PROGRESS["feitos"] = min(SCAN_PROGRESS["feitos"] + 1, SCAN_PROGRESS.get("total", 0) or 0)
    SCAN_PROGRESS["atual"] = symbol
    SCAN_PROGRESS["fase"] = "atualizando análise" if cache_status in ("fresh", "delta", "stale") else "aquecendo cache"
    ult = SCAN_PROGRESS.get("ultimos") or []
    SCAN_PROGRESS["ultimos"] = (ult + [symbol])[-3:]
    SCAN_PROGRESS["at"] = time.time()


def _progress_done():
    SCAN_PROGRESS.update(ativo=False, fase="concluído", atual="", at=time.time())


async def run_scan(period: Optional[str] = None, universe: Optional[str] = None,
                   fetch=None, concurrency: int = CONCURRENCY) -> dict:
    """Varre o universo e devolve a lista rankeada por score_tecnico.

    `fetch(symbol, rng)` é o provedor (yahoo.get_history em produção; fake nos
    testes). O espaçamento entre chamadas só é cobrado quando o candle_cache
    decide ir à rede — cache "fresh" atravessa sem custo.
    """
    p = candles_mod.normalize_period(period)
    keep = candles_mod.resolve_keep(p)
    uni = get_universe(universe)

    ck = p + "|" + ",".join(uni)
    now_m = time.monotonic()
    hit = _SCAN_CACHE.get(ck)
    if hit and (now_m - hit[0]) < SCAN_TTL_S:
        return hit[1]

    sem = asyncio.Semaphore(max(1, concurrency))
    gate = {"next": 0.0}
    gate_lock = asyncio.Lock()

    async def throttled(symbol, rng):
        # Espaçamento mínimo entre chamadas REAIS ao provedor (anti-429).
        async with gate_lock:
            now = time.monotonic()
            wait = max(0.0, gate["next"] - now)
            gate["next"] = max(gate["next"], now) + MIN_FETCH_GAP_S
        if wait:
            await asyncio.sleep(wait)
        return await fetch(symbol, rng)

    results, errors = [], []
    _progress_reset(len(uni), p)

    async def scan_one(symbol):
        async with sem:
            try:
                hist = await candle_cache.load(symbol, lambda rng, s=symbol: throttled(s, rng))
                _progress_tick(symbol, hist.get("cacheStatus") or "")
                # FASE 1 (STU): TODO o cálculo por ativo sai do Snapshot Técnico
                # Único — a MESMA fonte que N2/N3 leem. Se o insumo não mudou,
                # o snapshot (e o snapshotId) é reaproveitado.
                snap = technical_snapshot.build(symbol, hist.get("candles") or [], p)
                sres = snap["setups"]
                results.append({
                    "ticker": symbol,
                    "snapshotId": snap["snapshotId"],
                    "snapshotAt": snap["asOf"],
                    "condicoes_detectadas": snap["conditions"],
                    "score_tecnico": snap["scoreTecnico"],
                    "setups": sres["setups"],
                    "veredito": sres["veredito"],
                    "confluencia": sres["confluencia"],
                    "melhorSetup": sres["melhor"],
                    "close": snap.get("close"),
                    "variacaoPeriodoPct": snap.get("variacaoPeriodoPct"),
                    "candles": snap["periodBars"],
                    "cacheStatus": hist.get("cacheStatus"),
                })
            except Exception as e:  # noqa: BLE001 — 1 símbolo ruim não derruba a varredura
                _progress_tick(symbol)
                errors.append({"ticker": symbol, "erro": str(e) or type(e).__name__})

    await asyncio.gather(*(scan_one(s) for s in uni))
    _progress_done()
    # BLOCO B: rankeia por confluência do melhor setup; score de
    # intensidade desempata; ticker estabiliza.
    results.sort(key=lambda r: (-r["confluencia"], -r["score_tecnico"], r["ticker"]))

    payload = {
        "period": p,
        "periodBars": keep,
        "universeSize": len(uni),
        "scanned": len(results),
        "results": results,
        "errors": errors,
        "modelo": [{"nome": n, "descricao": d} for n, d in setups.MODEL_EXPLANATION],
        "disclaimer": DISCLAIMER,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    _SCAN_CACHE[ck] = (now_m, payload)
    return payload
