"""qa/35 (spike) + qa/36 (F10.2, integração aprovada): fundamentos por ticker.

ESTADO: integrado. O gate do Alex (mock qa/mocks/fundamento-tecnica-v1.html)
foi aprovado — o fundamento entra como FILTRO DE QUALIDADE (score A/B/C) e
contexto, NUNCA gatilho de timing: chip no card, seção no N2 e rebaixamento
de confiança em divergência. A técnica continua mandando no plano.

Fonte PRIMÁRIA (decisão do gate): usebolsai.com — free 200 req/dia,
  header X-API-Key (env BOLSAI_API_KEY), GET /fundamentals/{ticker} com
  indicadores JÁ calculados (pl/pvp/ev_ebitda/roe/roa/roic/net_margin/
  net_debt_ebitda/cagr_5y/lpa/vpa) para ~350 ações — cobre o universo.
Fonte COMPLEMENTAR: brapi.dev — dividend yield (DY) e os 4 tickers
  irrestritos com módulos completos (PETR4/VALE3/ITUB4/MGLU3); o free só
  entrega o pacote cheio nesses 4 (limitação achada no spike, ver qa/35).

Regras invioláveis (limites permanentes do projeto):
  - NENHUM dado inventado: campo indisponível = None ("sem dado" na UI),
    nunca inferência.
  - Fundamento muda por trimestre → cache agressivo em SQLite (kv global,
    sem escopo de usuário — o dado é público): TTL de 7 dias
    (1 fetch/ticker/semana). O SCAN lê só do cache (nunca fetch inline —
    varredura tem que ser rápida); um job semanal aquece o universo. O N2
    (1 ticker por vez) pode buscar inline.
  - Bancos não têm totalDebt/ebitda (ITUB4 → None): dívida/EBITDA fica
    "sem dado" para financeiras — correto, não é bug.

NOTA (validação): o cliente bolsai foi construído contra o formato
DOCUMENTADO da API (fixtures no test_fundamentals.py) — a validação AO VIVO
depende da BOLSAI_API_KEY no Railway (pendência do Alex). O brapi foi
provado ao vivo no spike (qa/35). Sem a chave, get_fundamentals cai no
brapi automaticamente.
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx  # mesma pilha HTTP do resto do backend (yahoo.py) — traz certifi

from . import db

BRAPI_BASE = "https://brapi.dev/api/quote/"
MODULES = "summaryProfile,defaultKeyStatistics,financialData"
BOLSAI_BASE = "https://api.usebolsai.com/api/v1/fundamentals/"
TTL_DIAS = 7          # fundamento muda por trimestre; 1 fetch/ticker/semana
TIMEOUT_S = 12
# Tickers com módulos completos SEM token no free da brapi (validado no spike):
TICKERS_IRRESTRITOS = ("PETR4", "VALE3", "ITUB4", "MGLU3")


def _bolsai_key() -> Optional[str]:
    """Chave da bolsai via env (Railway). Ausente → cai no brapi."""
    k = (os.environ.get("BOLSAI_API_KEY") or "").strip()
    return k or None


def _key(ticker: str) -> str:
    return f"fundamentals:{ticker.upper()}"


def _num(v) -> Optional[float]:
    """Coerção segura: qualquer coisa não-numérica vira None (sem dado)."""
    try:
        f = float(v)
        return f if f == f else None  # NaN → None
    except (TypeError, ValueError):
        return None


def parse_brapi(payload: dict) -> Optional[dict]:
    """Extrai as métricas do JSON da brapi para o formato interno. PURO
    (testável com fixture, sem rede). Campo ausente/nulo = None, sempre."""
    results = (payload or {}).get("results") or []
    if not results:
        return None
    r = results[0]
    dks = r.get("defaultKeyStatistics") or {}
    fin = r.get("financialData") or {}
    prof = r.get("summaryProfile") or {}
    total_debt = _num(fin.get("totalDebt"))
    ebitda = _num(fin.get("ebitda"))
    div_ebitda = round(total_debt / ebitda, 2) if (total_debt is not None and ebitda) else None
    return {
        "ticker": r.get("symbol"),
        "setor": prof.get("sector"),
        "pl": _num(r.get("priceEarnings")) if r.get("priceEarnings") is not None else _num(dks.get("trailingPE")),
        "pvp": _num(dks.get("priceToBook")),
        "roe": _num(fin.get("returnOnEquity")),
        "dy": _num(dks.get("dividendYield")),
        "margemLiquida": _num(fin.get("profitMargins")),
        "dividaEbitda": div_ebitda,
        "crescReceita": _num(fin.get("revenueGrowthAnnual")) if fin.get("revenueGrowthAnnual") is not None else _num(fin.get("revenueGrowth")),
        "crescLucro": _num(fin.get("earningsGrowthAnnual")) if fin.get("earningsGrowthAnnual") is not None else _num(fin.get("earningsGrowth")),
        "referencia": dks.get("mostRecentQuarter") or None,
        "fonte": "brapi",
    }


def parse_bolsai(payload: dict) -> Optional[dict]:
    """Extrai as métricas do JSON da bolsai (GET /fundamentals/{ticker}) para
    o MESMO formato interno de parse_brapi. PURO. A bolsai já entrega os
    indicadores calculados; a bolsai reporta net_debt_ebitda direto (sem a
    conta que a brapi exige). DY não vem no free (recurso PRO) → None,
    completado pela brapi depois. Campo ausente/nulo = None, sempre."""
    d = (payload or {}).get("data") or payload or {}
    if not d or not (d.get("ticker") or d.get("symbol")):
        return None
    return {
        "ticker": d.get("ticker") or d.get("symbol"),
        "setor": d.get("sector") or d.get("setor"),
        "pl": _num(d.get("pl")),
        "pvp": _num(d.get("pvp")),
        "roe": _num(d.get("roe")),
        "dy": _num(d.get("dividend_yield")),  # normalmente None no free
        "margemLiquida": _num(d.get("net_margin")),
        "dividaEbitda": _num(d.get("net_debt_ebitda")),
        "crescReceita": _num(d.get("cagr_revenue_5y")),
        "crescLucro": _num(d.get("cagr_earnings_5y")),
        "referencia": d.get("reference_date") or None,
        "fonte": "bolsai",
    }


def merge_fundamentos(primario: Optional[dict], complemento: Optional[dict]) -> Optional[dict]:
    """Completa lacunas do PRIMÁRIO (bolsai) com o COMPLEMENTO (brapi) —
    campo a campo, só onde o primário está None. Nunca sobrescreve dado
    existente (o primário manda). PURO. Marca a fonte como 'bolsai+brapi'
    quando algo foi complementado."""
    if primario is None:
        return complemento
    if complemento is None:
        return primario
    completou = False
    out = dict(primario)
    for k, v in complemento.items():
        if k in ("ticker", "fonte", "fetchedAt", "score"):
            continue
        if out.get(k) is None and v is not None:
            out[k] = v
            completou = True
    if completou:
        out["fonte"] = f"{primario.get('fonte', '?')}+{complemento.get('fonte', '?')}"
    return out


MIN_PILARES = 2   # score exige ≥2 pilares COM dado (senão "dados insuficientes")

# NOTA (revisão do operador sênior, qa/37): a banda de P/L é ABSOLUTA e
# sector-blind — um growth legítimo (P/L alto) é penalizado e uma cíclica no
# topo do ciclo (P/L baixo) é premiada. É aceitável para um FILTRO A/B/C de
# primeira passada (não é gatilho, não move o plano), mas um refino
# sector-relativo (P/L e P/VP vs. mediana do setor) é trabalho futuro quando
# houver dado setorial confiável. Documentado, não inferido.


def score_fundamento(f: Optional[dict]) -> Optional[str]:
    """Score A/B/C — FILTRO DE QUALIDADE, nunca gatilho de timing (princípio
    do gate). Três pilares, 1 ponto cada; pilar sem dado NÃO pontua nem
    penaliza:
      valuation      → P/L entre 0 e 20;
      rentabilidade  → ROE >= 10% E margem líquida > 0;
      solidez        → dívida/EBITDA <= 3 (sem dado em financeiras → pilar
                       neutro, não conta).
    A/B/C = >=2 / 1 / 0 pontos entre os pilares COM dado. `None` (sem score,
    "dados insuficientes") quando MENOS de MIN_PILARES têm dado — evita rotular
    (e rebaixar a confiança de) um ativo com base numa única métrica, coerente
    com a doutrina do app ('n insuficiente em vez de % enganosa') e o princípio
    #11 do operador (dado insuficiente → sem recomendação definitiva)."""
    if not f:
        return None
    pilares = []
    if f.get("pl") is not None:
        pilares.append(0 < f["pl"] <= 20)
    if f.get("roe") is not None or f.get("margemLiquida") is not None:
        roe_ok = (f.get("roe") or 0) >= 0.10
        mg_ok = (f.get("margemLiquida") or 0) > 0
        pilares.append(roe_ok and mg_ok)
    if f.get("dividaEbitda") is not None:
        pilares.append(f["dividaEbitda"] <= 3.0)
    if len(pilares) < MIN_PILARES:
        return None   # cobertura fina → sem score, nunca uma letra enganosa
    pontos = sum(pilares)
    if pontos >= 2:
        return "A"
    return "B" if pontos == 1 else "C"


def rebaixa_confianca(confianca: Optional[str], score: Optional[str],
                      decisao_operavel: bool) -> tuple:
    """qa/36 (gate): quando a técnica dá decisão OPERÁVEL mas o fundamento é
    fraco (score C), a confiança declarada desce 1 degrau
    (alta→moderada→baixa). Score B: sem efeito. Score A: NÃO promove (o
    fundamento só filtra pra baixo — nunca é gatilho). PURA. Retorna
    (confianca_final, rebaixou: bool). `confianca` já normalizada
    (analysis_outcomes.normalizar_confianca)."""
    ordem = ["baixa", "moderada", "alta"]
    if not decisao_operavel or score != "C" or confianca not in ordem:
        return confianca, False
    i = ordem.index(confianca)
    if i == 0:
        return confianca, False  # já é baixa, não desce mais
    return ordem[i - 1], True


def _fetch_brapi_raw(ticker: str, token: Optional[str] = None) -> dict:
    """I/O de rede isolado (o resto do módulo é puro/injetável)."""
    params = {"modules": MODULES}
    if token:
        params["token"] = token
    r = httpx.get(BRAPI_BASE + ticker.upper(), params=params,
                  headers={"User-Agent": "BolsIA/qa36"}, timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()


def _fetch_bolsai_raw(ticker: str, api_key: str) -> dict:
    """I/O da bolsai (fonte primária). Header X-API-Key obrigatório."""
    r = httpx.get(BOLSAI_BASE + ticker.upper(),
                  headers={"X-API-Key": api_key, "User-Agent": "BolsIA/qa36"},
                  timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()


def _fetch_merged(ticker: str, *, bolsai_key: Optional[str],
                  fetch_bolsai=None, fetch_brapi=None,
                  brapi_complemento: bool = True) -> Optional[dict]:
    """Busca da fonte primária (bolsai) + complemento (brapi para o DY e os 4
    tickers completos). Cada fonte é best-effort: uma fora não derruba a
    outra. `brapi_complemento=False` PULA a brapi — usado no warm em massa
    (não martelar o brapi rate-limited no universo inteiro; o DY é
    complementado depois, sob demanda, no N2). Fetchers injetáveis p/ teste."""
    fetch_bolsai = fetch_bolsai or _fetch_bolsai_raw
    fetch_brapi = fetch_brapi or _fetch_brapi_raw
    primario = None
    if bolsai_key:
        try:
            primario = parse_bolsai(fetch_bolsai(ticker, bolsai_key))
        except Exception:  # noqa: BLE001 — bolsai fora → tenta brapi como primário
            primario = None
    # brapi: complemento (traz DY); vira primário se a bolsai falhou. Pulado no
    # warm em massa se já temos o primário da bolsai.
    complemento = None
    if brapi_complemento or primario is None:
        try:
            complemento = parse_brapi(fetch_brapi(ticker, None))
        except Exception:  # noqa: BLE001
            complemento = None
    return merge_fundamentos(primario, complemento)


def get_fundamentals(conn, ticker: str, *, fetch_merged=None, now=None,
                     force: bool = False) -> Optional[dict]:
    """Fundamentos com cache SQLite (kv GLOBAL — dado público, sem escopo).
    Cache hit (< TTL_DIAS) não toca a rede, salvo `force`. Fonte primária
    bolsai + complemento brapi (BOLSAI_API_KEY via env). `fetch_merged`/`now`
    injetáveis para teste (mesmo padrão de avaliar_pendentes)."""
    now = now or datetime.now(timezone.utc)
    cached = db.kv_get(conn, _key(ticker), None, user_id=None)
    if not force and cached and cached.get("fetchedAt"):
        try:
            if now - datetime.fromisoformat(cached["fetchedAt"]) < timedelta(days=TTL_DIAS):
                return cached
        except ValueError:
            pass  # fetchedAt corrompido → refaz
    if fetch_merged is None:
        key = _bolsai_key()
        def fetch_merged(t):  # noqa: E306 — closure captura a chave do env
            return _fetch_merged(t, bolsai_key=key)
    try:
        f = fetch_merged(ticker)
    except Exception:  # noqa: BLE001 — tudo fora = cache velho se houver
        return cached or None
    if f is None:
        return cached or None
    f["fetchedAt"] = now.isoformat()
    f["score"] = score_fundamento(f)
    db.kv_set(conn, _key(ticker), f, user_id=None)
    return f


def get_cached(conn, ticker: str) -> Optional[dict]:
    """Só o cache — NUNCA vai à rede. É o que o SCAN usa (varredura tem que
    ser rápida). None = ainda não aquecido pelo job semanal."""
    return db.kv_get(conn, _key(ticker), None, user_id=None)


# --- job semanal de aquecimento do cache (padrão radar_daily.maybe_run) ------
LAST_WARM = {"date": None, "aquecidos": 0, "erro": None}


def _hoje_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


WARM_THROTTLE_S = 0.4   # espaçamento entre fetches (respeita rate limit da fonte)
WARM_MAX_POR_RUN = 60   # teto por passada — cobre o universo em 2 dias com folga


def warm_universe(conn, tickers, *, fetch_merged=None, now=None,
                  throttle_s: float = 0.0, limit: Optional[int] = None) -> int:
    """Aquece o cache dos tickers cujo fundamento está ausente ou vencido.
    Retorna quantos foram (re)buscados. Best-effort por ticker. SÍNCRONO e
    BLOQUEANTE de propósito — DEVE rodar via asyncio.to_thread (nunca no event
    loop; ver maybe_warm). `throttle_s` espaça as chamadas à fonte externa;
    `limit` corta a passada (o resto vai no próximo dia)."""
    now = now or datetime.now(timezone.utc)
    # warm em massa usa SÓ a bolsai (não martela o brapi no universo inteiro).
    if fetch_merged is None:
        key = _bolsai_key()
        def fetch_merged(t):  # noqa: E306 — closure captura a chave do env
            return _fetch_merged(t, bolsai_key=key, brapi_complemento=False)
    n = 0
    for t in tickers:
        if limit is not None and n >= limit:
            break
        cached = db.kv_get(conn, _key(t), None, user_id=None)
        fresco = False
        if cached and cached.get("fetchedAt"):
            try:
                fresco = now - datetime.fromisoformat(cached["fetchedAt"]) < timedelta(days=TTL_DIAS)
            except ValueError:
                fresco = False
        if fresco:
            continue
        try:
            if get_fundamentals(conn, t, fetch_merged=fetch_merged, now=now):
                n += 1
                if throttle_s:
                    time.sleep(throttle_s)  # ok: roda em thread, não no event loop
        except Exception:  # noqa: BLE001 — 1 ticker não trava o job
            continue
    return n


async def maybe_warm(conn, tickers) -> Optional[int]:
    """Hook do scheduler: aquece no máximo 1x/dia. CRÍTICO: o warm faz I/O de
    rede BLOQUEANTE (httpx síncrono) — roda em thread (asyncio.to_thread) para
    NÃO congelar o event loop do servidor (senão o app perde a conexão durante
    o job). Só roda se houver BOLSAI_API_KEY: a bolsai é a fonte do universo;
    sem a chave, aquecer via brapi seria inútil (só 4 tickers) e rate-limited."""
    if LAST_WARM["date"] == _hoje_iso() or not _bolsai_key():
        return None
    try:
        n = await asyncio.to_thread(
            warm_universe, conn, tickers,
            throttle_s=WARM_THROTTLE_S, limit=WARM_MAX_POR_RUN)
        LAST_WARM.update(date=_hoje_iso(), aquecidos=n, erro=None)
        return n
    except Exception as e:  # noqa: BLE001 — nunca derruba o laço do scheduler
        LAST_WARM["erro"] = str(e)[:200]
        print(f"[fundamentals] warm falhou: {e}")
        return None
