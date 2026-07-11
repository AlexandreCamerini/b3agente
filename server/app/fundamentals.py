"""qa/35 (P3 — SPIKE, gate pendente): fundamentos por ticker via brapi.dev.

ESTADO: spike. Este módulo prova a fonte e o cache; NÃO está integrado a
scanner/LLM/telas — a integração (chip de score no card, seção "Fundamento"
no N2, rebaixamento de confiança em divergência) é a fase F10.2, somente
após o OK do Alex no mock (qa/mocks/fundamento-tecnica-v1.html).

Fonte primária (spike): brapi.dev.
  - 4 tickers IRRESTRITOS sem token (PETR4/VALE3/ITUB4/MGLU3): todos os
    modules — validado por curl em 10/07/2026 (relatório no qa/35).
  - Plano free COM token: 15k req/mês, 1 ação/req, MAS sem os modules
    financialData/defaultKeyStatistics/dividendos → fora dos 4 tickers de
    teste o free entrega só quote+P/L. LIMITAÇÃO CENTRAL do spike.
Fallback documentado (não implementado — decisão no gate): usebolsai.com
  free, 200 req/dia, header X-API-Key; GET /fundamentals/{ticker} traz
  pl/pvp/ev_ebitda/roe/roa/roic/net_margin/net_debt_ebitda/cagr_5y prontos
  para ~350 ações. Cobre o universo inteiro em 1 dia de cota. Dividendos é
  recurso do plano PRO. Ver qa/35 §P3 para a comparação completa.

Regras invioláveis (limites permanentes do projeto):
  - NENHUM dado inventado: campo indisponível = None ("sem dado" na UI),
    nunca inferência.
  - Fundamento muda por trimestre → cache agressivo em SQLite (kv global,
    sem escopo de usuário — o dado é público): TTL de 7 dias
    (1 fetch/ticker/semana → universo ~100 tickers ≈ 433 req/mês ≈ 3% do
    free da brapi; capacidade não é o gargalo, profundidade é).
  - Bancos não têm totalDebt/ebitda (ITUB4 → None): dívida/EBITDA fica
    "sem dado" para financeiras — correto, não é bug.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx  # mesma pilha HTTP do resto do backend (yahoo.py) — traz certifi

from . import db

BRAPI_BASE = "https://brapi.dev/api/quote/"
MODULES = "summaryProfile,defaultKeyStatistics,financialData"
TTL_DIAS = 7          # fundamento muda por trimestre; 1 fetch/ticker/semana
TIMEOUT_S = 12
# Tickers com módulos completos SEM token no free (validado no spike):
TICKERS_IRRESTRITOS = ("PETR4", "VALE3", "ITUB4", "MGLU3")


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


def score_fundamento(f: Optional[dict]) -> Optional[str]:
    """Score A/B/C — FILTRO DE QUALIDADE, nunca gatilho de timing (princípio
    do gate). Três pilares, 1 ponto cada; pilar sem dado NÃO pontua nem
    penaliza (entra no denominador só se houver dado):
      valuation      → P/L entre 0 e 20;
      rentabilidade  → ROE >= 10% E margem líquida > 0;
      solidez        → dívida/EBITDA <= 3 (sem dado em financeiras → pilar
                       neutro, não conta).
    A/B/C = >=2/3, 1, 0 pontos entre os pilares COM dado; None se nenhum
    pilar tiver dado (sem dado → sem score, nunca chute)."""
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
    if not pilares:
        return None
    pontos = sum(pilares)
    if pontos >= 2:
        return "A"
    return "B" if pontos == 1 else "C"


def _fetch_brapi_raw(ticker: str, token: Optional[str] = None) -> dict:
    """I/O de rede isolado (o resto do módulo é puro/injetável). httpx
    síncrono de propósito: o spike roda fora do event loop; a versão async
    (se aprovada no gate) segue o padrão do yahoo.py."""
    params = {"modules": MODULES}
    if token:
        params["token"] = token
    r = httpx.get(BRAPI_BASE + ticker.upper(), params=params,
                  headers={"User-Agent": "BolsIA/spike-qa35"}, timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()


def get_fundamentals(conn, ticker: str, *, token: Optional[str] = None,
                     fetch_raw=None, now=None) -> Optional[dict]:
    """Fundamentos com cache SQLite (kv GLOBAL — dado público, sem escopo).
    Cache hit (< TTL_DIAS) não toca a rede. `fetch_raw`/`now` injetáveis
    para teste (mesmo padrão de avaliar_pendentes)."""
    now = now or datetime.now(timezone.utc)
    cached = db.kv_get(conn, _key(ticker), None, user_id=None)
    if cached and cached.get("fetchedAt"):
        try:
            idade = now - datetime.fromisoformat(cached["fetchedAt"])
            if idade < timedelta(days=TTL_DIAS):
                return cached
        except ValueError:
            pass  # fetchedAt corrompido → refaz o fetch
    fetch_raw = fetch_raw or _fetch_brapi_raw
    try:
        payload = fetch_raw(ticker, token)
    except Exception:  # noqa: BLE001 — fonte fora = usa cache velho se houver, senão None
        return cached or None
    f = parse_brapi(payload)
    if f is None:
        return cached or None
    f["fetchedAt"] = now.isoformat()
    f["score"] = score_fundamento(f)
    db.kv_set(conn, _key(ticker), f, user_id=None)
    return f
