#!/usr/bin/env python3
"""Diagnóstico PONTUAL dos 9 tickers que falham com 404 no bootstrap do ledger
de sinais (LEDGER-01, Fase 0 do milestone v1.2 — `00-01-PLAN.md`).

Este script NÃO toca produção: não importa o módulo do bootstrap do ledger
(`server/app/` + `signal_ledger` + `_bootstrap.py`), não abre banco, não
grava nada em disco além do que o chamador redirecionar via shell
(`> arquivo`). Reusa a camada de sessão do cliente real
(`server/app/yahoo.py`: cookie + crumb + User-Agent + rotação de host), no
mesmo estilo de `scripts/medir-yahoo-intraday.py` (script de medição one-off
deste repo).

Para cada ticker, três sondas EM SEQUÊNCIA (nunca concorrentes — concorrência
é uma das hipóteses sob teste para o 404):

  1. Sonda PRIMÁRIA (Yahoo, direta) — `yahoo.get_history()` repetida
     `--tentativas` vezes, espaçadas `--espaco-s` segundos, forçando sessão
     nova entre tentativas.
  2. Sonda de ALIAS (busca do Yahoo) — só roda se a sonda 1 falhar em TODAS
     as tentativas. Busca candidatos com `/v1/finance/search` pela raiz do
     ticker (sem o dígito final) e testa cada candidato plausível da B3.
  3. Sonda de CONTRAPROVA (provedor configurado, `candle_provider.py`) — só
     roda se a sonda 1 falhar. Se o provedor não tiver token/env localmente,
     registra "contraprova indisponível: <erro>" e segue — não é falha do
     script, e NENHUMA env var é criada/alterada para fazer essa sonda passar.

Saída: JSON no stdout (um registro por ticker) e um resumo legível no stderr.
Nenhuma escrita em arquivo — quem grava o documento de evidência é quem chama
este script, redirecionando a saída.

Uso:
    server/.venv/bin/python scripts/diagnostico-tickers-ledger.py > /tmp/diag.json
    server/.venv/bin/python scripts/diagnostico-tickers-ledger.py \
        --tickers ELET3,BRFS3 --rng 15y --tentativas 3 --espaco-s 2.0
"""
import argparse
import asyncio
import json
import os
import sys
import time

import httpx

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "server"))

from app import candle_provider  # noqa: E402
from app import yahoo as ycli  # noqa: E402
from app import tickers as tks  # noqa: E402

TICKERS_PADRAO = "ELET3,BRFS3,ELET6,JBSS3,CRFB3,NTCO3,CPLE6,MRFG3,EMBR3"

# Dígito(s) finais do símbolo que identificam a CLASSE da ação na B3: ON=3,
# PN=4, PNA/PNB=5/6, units=11. Usado para não aceitar como alias um candidato
# de classe diferente (ex.: ON quando o original era PN).
_CLASSE_RE_SUFFIX_LEN = 2  # cobre "11"; dígito único é o caso comum


def _classe(simbolo: str) -> str:
    s = simbolo.replace(".SA", "")
    if s.endswith("11"):
        return "11"
    return s[-1:] if s and s[-1:].isdigit() else ""


async def _sonda_primaria(ticker: str, rng: str, tentativas: int, espaco_s: float) -> list:
    """Chama `yahoo.get_history()` até `tentativas` vezes, forçando sessão
    nova a cada tentativa (a hipótese de sessão "presa" é uma das candidatas
    ao 404). Registra, por tentativa, exceção (classe + str), status_code
    quando for `httpx.HTTPStatusError`, e a evidência de sucesso."""
    registros = []
    for i in range(tentativas):
        ycli._session["ts"] = 0  # força sessão nova nesta tentativa
        t0 = time.perf_counter()
        try:
            hist = await ycli.get_history(ticker, rng=rng, interval="1d")
            candles = hist.get("candles") or []
            ms = round((time.perf_counter() - t0) * 1000)
            registros.append({
                "tentativa": i + 1,
                "sucesso": True,
                "n_candles": len(candles),
                "primeira_data": candles[0]["date"] if candles else None,
                "ultima_data": candles[-1]["date"] if candles else None,
                "ms": ms,
            })
        except httpx.HTTPStatusError as e:
            ms = round((time.perf_counter() - t0) * 1000)
            registros.append({
                "tentativa": i + 1,
                "sucesso": False,
                "excecao": type(e).__name__,
                "erro": str(e),
                "status_code": e.response.status_code if e.response is not None else None,
                "ms": ms,
            })
        except Exception as e:  # noqa: BLE001 — diagnóstico: qualquer falha é evidência, não crash do script
            ms = round((time.perf_counter() - t0) * 1000)
            registros.append({
                "tentativa": i + 1,
                "sucesso": False,
                "excecao": type(e).__name__,
                "erro": str(e),
                "status_code": None,
                "ms": ms,
            })
        if i < tentativas - 1:
            await asyncio.sleep(espaco_s)
    return registros


async def _sonda_alias(client: httpx.AsyncClient, ticker: str) -> dict:
    """Busca candidatos de renomeação via `/v1/finance/search` pela raiz do
    ticker (sem o dígito final), filtra por bolsa B3 (`exchange == "SAO"`) e
    testa `yahoo.get_history` em cada candidato cuja classe (dígito final)
    bate com a do original."""
    raiz = ticker[:-1] if ticker and ticker[-1:].isdigit() else ticker
    classe_original = _classe(ticker)
    resultado = {"raiz_buscada": raiz, "candidatos": [], "candidatos_testados": []}
    try:
        r = await client.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": raiz, "quotesCount": 15, "newsCount": 0},
            headers=ycli.BASE_HEADERS,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:  # noqa: BLE001
        resultado["erro_busca"] = f"{type(e).__name__}: {e}"
        return resultado

    quotes = data.get("quotes") or []
    candidatos_b3 = [
        q for q in quotes
        if str(q.get("exchange", "")).upper() == "SAO"
    ]
    resultado["candidatos"] = [
        {
            "symbol": q.get("symbol"),
            "shortname": q.get("shortname"),
            "longname": q.get("longname"),
            "exchange": q.get("exchange"),
        }
        for q in candidatos_b3
    ]

    for q in candidatos_b3:
        simbolo = str(q.get("symbol") or "")
        simbolo_sem_sufixo = simbolo.replace(".SA", "")
        if simbolo_sem_sufixo.upper() == ticker.upper():
            continue  # o próprio original não é candidato de alias
        if _classe(simbolo) != classe_original:
            continue  # classe diferente (ON vs PN etc.) não é a mesma série
        teste = {"symbol": simbolo, "shortname": q.get("shortname"), "longname": q.get("longname")}
        try:
            hist = await ycli.get_history(simbolo_sem_sufixo, rng="1mo", interval="1d")
            candles = hist.get("candles") or []
            teste["sucesso"] = bool(candles)
            teste["n_candles"] = len(candles)
            teste["ultima_data"] = candles[-1]["date"] if candles else None
        except Exception as e:  # noqa: BLE001
            teste["sucesso"] = False
            teste["erro"] = f"{type(e).__name__}: {e}"
        resultado["candidatos_testados"].append(teste)
        await asyncio.sleep(0.5)
    return resultado


async def _sonda_contraprova(ticker: str) -> dict:
    """Chama `candle_provider.get_history()` (provedor configurado no
    ambiente local) uma vez. Falha por falta de token/env é esperada e NÃO é
    tratada como falha do script — nenhuma env var é criada/alterada aqui."""
    try:
        hist = await candle_provider.get_history(ticker, rng="1mo", interval="1d")
        candles = hist.get("candles") or []
        return {
            "sucesso": bool(candles),
            "source": hist.get("source"),
            "n_candles": len(candles),
            "ultima_data": candles[-1]["date"] if candles else None,
        }
    except Exception as e:  # noqa: BLE001
        return {"sucesso": False, "nota": f"contraprova indisponível: {type(e).__name__}: {e}"}


async def diagnosticar(ticker: str, rng: str, tentativas: int, espaco_s: float) -> dict:
    reg = {"ticker": ticker}
    reg["sonda_primaria"] = await _sonda_primaria(ticker, rng, tentativas, espaco_s)
    algum_sucesso = any(t.get("sucesso") for t in reg["sonda_primaria"])
    if algum_sucesso:
        # TRANSITÓRIO plausível — não precisa gastar as sondas de alias/contraprova.
        reg["sonda_alias"] = None
        reg["sonda_contraprova"] = None
        return reg
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        reg["sonda_alias"] = await _sonda_alias(client, ticker)
    reg["sonda_contraprova"] = await _sonda_contraprova(ticker)
    return reg


async def main_async(args) -> None:
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    tickers = [tks.normalize_ticker(t) for t in tickers]
    saida = {
        "comando": " ".join(sys.argv),
        "quando_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rng": args.rng,
        "tentativas": args.tentativas,
        "espaco_s": args.espaco_s,
        "registros": [],
    }
    for tk in tickers:
        print(f"--- {tk} ---", file=sys.stderr)
        reg = await diagnosticar(tk, args.rng, args.tentativas, args.espaco_s)
        saida["registros"].append(reg)
        n_ok = sum(1 for t in reg["sonda_primaria"] if t.get("sucesso"))
        print(f"  sonda primária: {n_ok}/{len(reg['sonda_primaria'])} tentativa(s) com sucesso",
              file=sys.stderr)
        if reg["sonda_alias"] is not None:
            n_cand = len(reg["sonda_alias"].get("candidatos") or [])
            n_test = len(reg["sonda_alias"].get("candidatos_testados") or [])
            print(f"  sonda alias: {n_cand} candidato(s) B3 encontrados, {n_test} testado(s)",
                  file=sys.stderr)
        if reg["sonda_contraprova"] is not None:
            print(f"  sonda contraprova: sucesso={reg['sonda_contraprova'].get('sucesso')}",
                  file=sys.stderr)
    print(json.dumps(saida, indent=2, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tickers", default=TICKERS_PADRAO,
                    help="lista separada por vírgula (default: os 9 tickers do achado LEDGER-01)")
    ap.add_argument("--rng", default="15y", help="range do Yahoo na sonda primária")
    ap.add_argument("--tentativas", type=int, default=3, help="tentativas da sonda primária")
    ap.add_argument("--espaco-s", type=float, default=2.0, help="segundos entre tentativas")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
