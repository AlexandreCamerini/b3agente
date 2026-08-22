"""Serie diaria do Ibovespa (FIX-C03, Plano 04-02) — usada para comparar o
retorno da carteira simulada com o mercado no Passo 8 do storyline (Fase 4).

Reusa `yahoo._yfetch` (cookie/crumb, rotacao de host, backoff — nao
reimplementar a mitigacao de 429 aqui) mas NAO reusa `yahoo.get_history`:
aquela normaliza o ticker via `catalog.py` antes de montar o path, o que
sufixaria `"^BVSP"` como `"^BVSP.SA"` (simbolo invalido). O simbolo do
indice bate direto no path, sem passar por essa normalizacao.

Este modulo NAO consome orcamento da brapi (ADR-008 — brapi e master de
diario/spot de ACAO; indice fica fora desse orcamento).
"""
import time

import httpx

from . import yahoo

# Simbolo HARDCODED — NUNCA vem de parametro de requisicao (T-04-04: sem
# isso a rota vira um proxy aberto para o Yahoo).
SIMBOLO = "^BVSP"

TTL = 900  # 15 min — a curva de patrimonio e diaria, refetch por request
           # so gastaria orcamento de requisicoes externas sem ganho (ADR-008).

_cache: dict = {}  # rng -> (ts, dict do contrato)


class BenchmarkIndisponivel(RuntimeError):
    """Falha TRANSITORIA (rede, granularidade degradada, serie vazia) — mesma
    semantica de `yahoo.QuoteUnavailable`. Mensagem NUNCA carrega `str(e)` cru
    do provedor (T-04-01: nao vazar detalhe interno pro usuario)."""


def limpar_cache() -> None:
    _cache.clear()


async def serie_ibov(period: str | None = None) -> dict:
    """Fechamentos diarios do Ibovespa. Levanta `BenchmarkIndisponivel` em
    qualquer falha (rede, granularidade degradada, serie vazia) — nunca
    inventa/estima um valor no lugar do dado ausente (CLAUDE.md item 4)."""
    from . import candles

    rng = candles.period_to_range(period)

    cached = _cache.get(rng)
    if cached and (time.time() - cached[0]) < TTL:
        return dict(cached[1])

    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            data = await yahoo._yfetch(
                client, "/v8/finance/chart/" + SIMBOLO,
                {"range": rng, "interval": "1d", "includePrePost": "false"},
            )
        result = ((data.get("chart") or {}).get("result") or [None])[0]
        if not result:
            raise BenchmarkIndisponivel("Ibovespa: sem dado do provedor.")
        meta = result.get("meta") or {}
        gran = meta.get("dataGranularity")
        if gran and gran != "1d":
            raise BenchmarkIndisponivel(
                f"Ibovespa: granularidade degradada ({gran}), dado descartado.")
        ts = result.get("timestamp") or []
        q = ((result.get("indicators") or {}).get("quote") or [{}])[0]
        closes = q.get("close") or [None] * len(ts)
        off = meta.get("gmtoffset")
        candles_out = []
        for i, epoch in enumerate(ts):
            close = closes[i] if i < len(closes) else None
            if close is None:
                continue
            candles_out.append({
                "date": yahoo._candle_key(epoch, "1d", off),
                "close": yahoo._round(close),
            })
        if not candles_out:
            raise BenchmarkIndisponivel("Ibovespa: serie vazia.")
    except BenchmarkIndisponivel:
        raise
    except (yahoo.QuoteUnavailable, httpx.HTTPError, KeyError, IndexError, TypeError):
        raise BenchmarkIndisponivel("Ibovespa: provedor indisponivel no momento.")

    out = {
        "t": SIMBOLO,
        "nome": "Ibovespa",
        "fonte": "yahoo",
        "candles": candles_out,
        "asOf": candles_out[-1]["date"],
    }
    _cache[rng] = (time.time(), dict(out))
    return out
