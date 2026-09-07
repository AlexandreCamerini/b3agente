"""Provider MOCK para cadeias de opções (Fase 14, Plano 01).

Existe para desenvolvimento e teste da mecânica lastreada (CALL coberta / PUT
de proteção) ENQUANTO a virada de produção `B3_OPTIONS_PROVIDER=mydata` não
acontece (14-CONTEXT.md, seção "Timing / dormência" — bloqueada hoje por
pico de requisições/min e WR-01). NUNCA é o default de produção: `mock`
entra só via `B3_OPTIONS_PROVIDER=mock` (env do servidor), o mesmo padrão de
alavanca operacional documentado em `options_provider.py`.

Determinístico por desenho: sem I/O de rede, sem cache, sem leitura de
cotação ao vivo — a mesma entrada (ticker, expiration) sempre devolve o
mesmo payload, byte a byte, o que torna a Fase 14 inteira testável ponta a
ponta sem depender da cadeia real da B3 responder.

Payload no MESMO contrato de `options_provider_yahoo.get_options` (ver
docstring daquele módulo e `14-CONTEXT.md`/`14-01-PLAN.md`, seção
<interfaces>): ticker, symbol, source, providerStatus, underlyingPrice,
currency, expirations, expiration, calls, puts, warning (só degradado),
providerError (opcional, só degradado). Contrato do item de calls/puts:
contractSymbol, optionType, strike, lastPrice, bid, ask, change,
percentChange, volume, openInterest, impliedVolatility, inTheMoney,
currency, distancePct.
"""
from __future__ import annotations

import datetime as dt
import os
from typing import Optional

MOCK_SPOT = {
    "PETR4": 38.00,
    "VALE3": 62.00,
    "ITUB4": 31.00,
}
MOCK_SPOT_DEFAULT = 30.00

# Volume/OI fixos e generosos o bastante para o gate de liquidez
# (`options_quant.liquidity_score`) aceitar todo contrato sintético — ver
# acceptance_criteria do 14-01-PLAN.md ("score >= 40").
MOCK_VOLUME = 500
MOCK_OPEN_INTEREST = 2000
MOCK_IV = 0.35
MOCK_CURRENCY = "BRL"

MOCK_DEGRADED_WARNING = (
    "Cadeia de opções simulada em modo degradado "
    "(B3_OPTIONS_MOCK_STATUS=degraded)."
)


def _terceira_sexta(ano: int, mes: int) -> dt.date:
    """Terceira sexta-feira do mês/ano dados (padrão de vencimento mensal de
    opções B3 — mesma convenção de calendário usada nas cadeias reais)."""
    primeiro = dt.date(ano, mes, 1)
    # weekday(): segunda=0 ... sexta=4
    primeira_sexta = 1 + ((4 - primeiro.weekday()) % 7)
    return dt.date(ano, mes, primeira_sexta + 14)


def _proximas_terceiras_sextas(hoje: dt.date, n: int = 3) -> list[dt.date]:
    """As próximas `n` terceiras-sextas a partir de `hoje`, pulando qualquer
    uma a menos de 20 dias (achado ao vivo, 2026-09-06): `opcoes_lastreadas.
    propor()` só aceita vencimento com `_PRAZO_MIN_DIAS=15 <= dias <= 60`
    (opcoes_lastreadas.py:18-19,234), mas a rota sempre pede `expirations[0]`
    sem alternativa (main.py:2397, `get_options(t)` sem `expiration=`) — nos
    primeiros ~12 dias de cada mês a terceira-sexta do PRÓPRIO mês corrente
    cai abaixo do piso de 15 dias, e a cadeia mock (sem isso) travaria toda
    proposta em `sem_vencimento_elegivel` o mês inteiro, mascarando qualquer
    outro teste. A margem de 20 (não 15) é de propósito: sobra pra decisões
    de calendário não empurrarem a data pra cima do teto por acidente. Só
    afeta `B3_OPTIONS_PROVIDER=mock` — nunca a cadeia real."""
    out: list[dt.date] = []
    ano, mes = hoje.year, hoje.month
    while len(out) < n:
        tf = _terceira_sexta(ano, mes)
        if tf >= hoje + dt.timedelta(days=20):
            out.append(tf)
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return out


def _spot_para(ticker: str) -> float:
    return MOCK_SPOT.get((ticker or "").upper().strip(), MOCK_SPOT_DEFAULT)


def _contrato(ticker: str, indice: int, is_call: bool, spot: float, strike: float) -> dict:
    if is_call:
        last = round(max(0.05, spot - strike) + 0.60, 2)
    else:
        last = round(max(0.05, strike - spot) + 0.60, 2)
    in_the_money = (spot > strike) if is_call else (spot < strike)
    dist = round((strike - spot) / spot * 100, 2) if spot > 0 else None
    sufixo = "C" if is_call else "P"
    return {
        "contractSymbol": f"{(ticker or '').upper().strip()}MOCK{indice:02d}{sufixo}",
        "optionType": "call" if is_call else "put",
        "strike": round(strike, 2),
        "lastPrice": last,
        "bid": round(last - 0.05, 2),
        "ask": round(last + 0.05, 2),
        "change": 0.0,
        "percentChange": 0.0,
        "volume": MOCK_VOLUME,
        "openInterest": MOCK_OPEN_INTEREST,
        "impliedVolatility": MOCK_IV,
        "inTheMoney": bool(in_the_money),
        "currency": MOCK_CURRENCY,
        "distancePct": dist,
    }


def _payload_degradado(ticker: str, expiration: Optional[str]) -> dict:
    return {
        "ticker": ticker,
        "symbol": (ticker or "").upper().strip(),
        "source": "mock",
        "providerStatus": "degraded",
        "underlyingPrice": None,
        "currency": None,
        "expirations": [],
        "expiration": expiration,
        "calls": [],
        "puts": [],
        "warning": MOCK_DEGRADED_WARNING,
    }


async def get_options(ticker: str, expiration: Optional[str] = None) -> dict:
    if os.environ.get("B3_OPTIONS_MOCK_STATUS") == "degraded":
        return _payload_degradado(ticker, expiration)

    spot = _spot_para(ticker)
    expirations = [d.isoformat() for d in _proximas_terceiras_sextas(dt.date.today())]
    escolhido = expiration if expiration in expirations else expirations[0]

    strike_base = round(spot)
    calls = []
    puts = []
    for indice, deslocamento in enumerate(range(-4, 5), start=1):
        strike = strike_base + deslocamento
        calls.append(_contrato(ticker, indice, True, spot, strike))
        puts.append(_contrato(ticker, indice, False, spot, strike))

    return {
        "ticker": ticker,
        "symbol": (ticker or "").upper().strip(),
        "source": "mock",
        "providerStatus": "ok",
        "underlyingPrice": spot,
        "currency": MOCK_CURRENCY,
        "expirations": expirations,
        "expiration": escolhido,
        "calls": calls,
        "puts": puts,
    }
