#!/usr/bin/env python3
"""Medição PONTUAL do que o Yahoo Finance entrega de INTRADAY para tickers `.SA`.

Fase 1 do CHECKOUT-Intraday-Trailing-Web-otimizado.md. Este script NÃO toca
produção: não importa `main`, não abre o banco, não escreve em `/data`, não usa
o `candle_cache`. Ele reusa APENAS a camada de sessão do cliente real
(`server/app/yahoo.py`: cookie + crumb + User-Agent + rotação de host) para que
a medição reflita o que o backend veria de fato.

Fases (selecionáveis; por padrão roda todas):
  matriz  — intervalo × range: o que o Yahoo devolve de verdade (janela máxima real)
  latencia— p50/p95 por intervalo, com repetição
  rajada  — ~74 ativos do universo do Radar em concorrências crescentes
  spark   — /v7/finance/spark: N símbolos em UMA requisição (só close), p/ comparar custo
  cobertura — quais tickers do universo o Yahoo NÃO serve (404), por intervalo
  atraso  — SÓ FAZ SENTIDO COM O PREGÃO ABERTO: distância entre o último candle
            intraday e o relógio. É o número que decide se dá para falar em
            "a condição ocorreu agora" — rode entre 10h e 17h BRT.

Uso:
    server/.venv/bin/python scripts/medir-yahoo-intraday.py --fases matriz,latencia
    server/.venv/bin/python scripts/medir-yahoo-intraday.py --saida /tmp/medicao.json

Saída: tabelas em Markdown no stdout + JSON bruto (--saida).
"""
import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone

import httpx

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "server"))

from app import yahoo as ycli  # noqa: E402  (camada de sessão do cliente real)
from app.scanner import DEFAULT_UNIVERSE  # noqa: E402  (o universo real do Radar)

INTERVALOS = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d"]
RANGES = ["1d", "5d", "7d", "1mo", "3mo", "6mo", "1y", "2y", "max"]
TICKER_PADRAO = "PETR4"
# Liquidez decrescente: mede se o intraday cobre a cauda do universo, não só o topo.
TICKERS_LIQUIDEZ = ["PETR4", "VALE3", "ITUB4", "MGLU3", "COGN3", "AURE3", "IGTI11", "CMIN3"]


async def _raw_chart(client, symbol, interval, rng, extra=None):
    """GET cru em /v8/finance/chart — com crumb/cookie da sessão real, mas SEM
    o retry do cliente: aqui o status de erro é o dado que queremos medir."""
    s = await ycli._ensure_session(client)
    q = {"range": rng, "interval": interval, "includePrePost": "false"}
    if s["crumb"]:
        q["crumb"] = s["crumb"]
    if extra:
        q.update(extra)
    headers = {**ycli.BASE_HEADERS, "Accept": "application/json,*/*"}
    if s["cookie"]:
        headers["Cookie"] = s["cookie"]
    url = ycli.HOSTS[0] + "/v8/finance/chart/" + symbol
    t0 = time.perf_counter()
    try:
        r = await client.get(url, params=q, headers=headers)
    except httpx.HTTPError as e:
        return {"status": 0, "erro": type(e).__name__, "ms": (time.perf_counter() - t0) * 1000, "bytes": 0}
    ms = (time.perf_counter() - t0) * 1000
    out = {"status": r.status_code, "ms": ms, "bytes": len(r.content)}
    if r.status_code != 200:
        out["erro"] = (r.text or "")[:160]
        return out
    try:
        data = r.json()
    except Exception:  # noqa: BLE001
        out["erro"] = "json inválido"
        return out
    chart = data.get("chart") or {}
    if chart.get("error"):
        out["erro"] = json.dumps(chart["error"])[:160]
        return out
    res = (chart.get("result") or [None])[0]
    if not res:
        out["erro"] = "result vazio"
        return out
    ts = res.get("timestamp") or []
    q0 = ((res.get("indicators") or {}).get("quote") or [{}])[0]
    closes = q0.get("close") or []
    vols = q0.get("volume") or []
    validos = [i for i, c in enumerate(closes) if c is not None]
    meta = res.get("meta") or {}
    out.update({
        "n": len(ts),
        "n_validos": len(validos),
        "vol_zerado": sum(1 for v in vols if not v),
        "primeiro": ts[0] if ts else None,
        "ultimo": ts[-1] if ts else None,
        "span_dias": round((ts[-1] - ts[0]) / 86400, 2) if len(ts) > 1 else 0,
        "gmtoffset": meta.get("gmtoffset"),
        "tz": meta.get("exchangeTimezoneName"),
        "granularidade_meta": meta.get("dataGranularity"),
        "range_meta": meta.get("range"),
    })
    if len(ts) > 2:
        deltas = [b - a for a, b in zip(ts, ts[1:])]
        out["passo_mediano_s"] = int(statistics.median(deltas))
    return out


def _iso(ts):
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%MZ")


# --------------------------------------------------------------------------
# Fase MATRIZ — intervalo × range
# --------------------------------------------------------------------------
async def fase_matriz(client, ticker):
    print(f"\n## Matriz intervalo × range — {ticker}.SA\n", flush=True)
    linhas = []
    for iv in INTERVALOS:
        for rg in RANGES:
            r = await _raw_chart(client, ycli.yahoo_symbol(ticker), iv, rg)
            r.update(intervalo=iv, range=rg)
            linhas.append(r)
            ok = "ok" if r.get("n_validos") else f"FALHA({r.get('status')})"
            print(f"  {iv:>4} × {rg:<4} → {ok:<12} n={r.get('n', 0):<5} "
                  f"span={r.get('span_dias', 0):<7} {r.get('ms', 0):.0f}ms "
                  f"{r.get('bytes', 0)/1024:.1f}KB {r.get('erro', '')[:60]}", flush=True)
            await asyncio.sleep(0.25)
    return linhas


# --------------------------------------------------------------------------
# Fase LATÊNCIA — p50/p95 por intervalo, em tickers de liquidez variada
# --------------------------------------------------------------------------
async def fase_latencia(client, intervalos, rng_por_iv, repeticoes):
    print("\n## Latência por intervalo (sequencial, 1 requisição por vez)\n", flush=True)
    out = []
    for iv in intervalos:
        rg = rng_por_iv.get(iv, "5d")
        amostras, bytes_, falhas = [], [], 0
        for i in range(repeticoes):
            tk = TICKERS_LIQUIDEZ[i % len(TICKERS_LIQUIDEZ)]
            r = await _raw_chart(client, ycli.yahoo_symbol(tk), iv, rg)
            if r.get("n_validos"):
                amostras.append(r["ms"])
                bytes_.append(r["bytes"])
            else:
                falhas += 1
            await asyncio.sleep(0.2)
        if amostras:
            amostras.sort()
            reg = {
                "intervalo": iv, "range": rg, "n": len(amostras), "falhas": falhas,
                "p50_ms": round(statistics.median(amostras)),
                "p95_ms": round(amostras[min(len(amostras) - 1, int(len(amostras) * 0.95))]),
                "max_ms": round(max(amostras)),
                "bytes_medio": round(statistics.mean(bytes_)),
            }
        else:
            reg = {"intervalo": iv, "range": rg, "n": 0, "falhas": falhas}
        out.append(reg)
        print(f"  {iv:>4} × {rg:<4} → p50={reg.get('p50_ms', '—')}ms p95={reg.get('p95_ms', '—')}ms "
              f"payload={reg.get('bytes_medio', 0)/1024:.1f}KB falhas={falhas}", flush=True)
    return out


# --------------------------------------------------------------------------
# Fase RAJADA — o universo do Radar (~74) em concorrências crescentes
# --------------------------------------------------------------------------
async def fase_rajada(client, universo, interval, rng, concorrencias, gap):
    print(f"\n## Rajada — {len(universo)} ativos, {interval} × {rng}\n", flush=True)
    out = []
    for conc in concorrencias:
        sem = asyncio.Semaphore(conc)
        resultados = []

        async def um(tk):
            async with sem:
                if gap:
                    await asyncio.sleep(gap)
                return await _raw_chart(client, ycli.yahoo_symbol(tk), interval, rng)

        t0 = time.perf_counter()
        resultados = await asyncio.gather(*[um(t) for t in universo])
        wall = time.perf_counter() - t0
        ok = [r for r in resultados if r.get("n_validos")]
        status = {}
        for r in resultados:
            status[str(r.get("status"))] = status.get(str(r.get("status")), 0) + 1
        lat = sorted(r["ms"] for r in resultados)
        reg = {
            "concorrencia": conc, "n": len(universo), "ok": len(ok),
            "wall_s": round(wall, 2), "status": status,
            "p50_ms": round(statistics.median(lat)) if lat else None,
            "p95_ms": round(lat[int(len(lat) * 0.95)]) if lat else None,
            "max_ms": round(max(lat)) if lat else None,
            "bytes_total": sum(r.get("bytes", 0) for r in resultados),
            "sem_intraday": [r for r in resultados if not r.get("n_validos")],
        }
        out.append(reg)
        print(f"  conc={conc:<3} → {len(ok)}/{len(universo)} ok em {wall:.1f}s "
              f"(p50={reg['p50_ms']}ms p95={reg['p95_ms']}ms) status={status} "
              f"total={reg['bytes_total']/1024/1024:.2f}MB", flush=True)
        await asyncio.sleep(3.0)  # respira entre rajadas
    return out


# --------------------------------------------------------------------------
# Fase SPARK — N símbolos em UMA requisição (só close)
# --------------------------------------------------------------------------
async def fase_spark(client, universo, interval, rng, lotes):
    print(f"\n## /v7/finance/spark — lote único, {interval} × {rng}\n", flush=True)
    out = []
    for tam in lotes:
        alvo = universo[:tam]
        s = await ycli._ensure_session(client)
        q = {"symbols": ",".join(ycli.yahoo_symbol(t) for t in alvo),
             "range": rng, "interval": interval, "indicators": "close",
             "includeTimestamps": "true", "includePrePost": "false"}
        if s["crumb"]:
            q["crumb"] = s["crumb"]
        headers = {**ycli.BASE_HEADERS, "Accept": "application/json,*/*"}
        if s["cookie"]:
            headers["Cookie"] = s["cookie"]
        t0 = time.perf_counter()
        try:
            r = await client.get(ycli.HOSTS[0] + "/v7/finance/spark", params=q, headers=headers)
            ms = (time.perf_counter() - t0) * 1000
            corpo = r.json() if r.status_code == 200 else {}
            res = corpo.get("spark", corpo) if isinstance(corpo, dict) else {}
            itens = res.get("result") if isinstance(res, dict) else None
            if itens is None and isinstance(corpo, dict):
                itens = list(corpo.keys())
            reg = {"lote": tam, "status": r.status_code, "ms": round(ms),
                   "bytes": len(r.content), "simbolos_retornados": len(itens or []),
                   "erro": None if r.status_code == 200 else (r.text or "")[:160]}
        except Exception as e:  # noqa: BLE001
            reg = {"lote": tam, "status": 0, "erro": f"{type(e).__name__}: {e}"[:160]}
        out.append(reg)
        print(f"  lote={tam:<3} → status={reg.get('status')} {reg.get('ms', 0)}ms "
              f"{reg.get('bytes', 0)/1024:.1f}KB símbolos={reg.get('simbolos_retornados')} "
              f"{(reg.get('erro') or '')[:80]}", flush=True)
        await asyncio.sleep(1.0)
    return out


# --------------------------------------------------------------------------
# Fase COBERTURA — quais tickers do universo o Yahoo simplesmente não serve
# --------------------------------------------------------------------------
async def fase_cobertura(client, universo, intervalos):
    print("\n## Cobertura do universo do Radar\n", flush=True)
    out = {}
    sem = asyncio.Semaphore(8)
    for iv, rg in intervalos:
        async def um(tk):
            async with sem:
                r = await _raw_chart(client, ycli.yahoo_symbol(tk), iv, rg)
                return tk, r
        pares = await asyncio.gather(*[um(t) for t in universo])
        faltando = [(tk, r.get("status")) for tk, r in pares if not r.get("n_validos")]
        out[f"{iv}x{rg}"] = faltando
        print(f"  {iv:>3} × {rg:<4} → {len(universo) - len(faltando)}/{len(universo)} servidos; "
              f"sem dado: {[t for t, _ in faltando]}", flush=True)
        await asyncio.sleep(1.5)
    return out


# --------------------------------------------------------------------------
# Fase ATRASO — o feed é "agora" ou é atrasado? (exige pregão aberto)
# --------------------------------------------------------------------------
async def fase_atraso(client, tickers, intervalos):
    print("\n## Atraso do feed (relógio − último candle) — exige pregão ABERTO\n", flush=True)
    agora = time.time()
    hora_brt = datetime.fromtimestamp(agora, tz=timezone.utc).hour - 3
    if not (10 <= hora_brt % 24 < 17):
        print(f"  AVISO: são {hora_brt % 24}h BRT — fora do pregão. O número abaixo mede "
              f"a distância até o fechamento, não o atraso do feed.", flush=True)
    out = []
    for iv in intervalos:
        for tk in tickers:
            r = await _raw_chart(client, ycli.yahoo_symbol(tk), iv, "1d")
            if not r.get("ultimo"):
                continue
            atraso_s = agora - r["ultimo"]
            reg = {"ticker": tk, "intervalo": iv, "ultimo_utc": _iso(r["ultimo"]),
                   "atraso_s": round(atraso_s), "atraso_min": round(atraso_s / 60, 1),
                   "passo_s": r.get("passo_mediano_s")}
            out.append(reg)
            print(f"  {tk:<7} {iv:>3} → último candle {_iso(r['ultimo'])} "
                  f"({reg['atraso_min']} min atrás)", flush=True)
            await asyncio.sleep(0.3)
    return out


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fases", default="matriz,latencia,rajada,spark,cobertura")
    ap.add_argument("--ticker", default=TICKER_PADRAO)
    ap.add_argument("--repeticoes", type=int, default=8)
    ap.add_argument("--intervalo-rajada", default="15m")
    ap.add_argument("--range-rajada", default="5d")
    ap.add_argument("--concorrencias", default="4,8,16")
    ap.add_argument("--gap", type=float, default=0.0, help="pausa por requisição dentro do slot")
    ap.add_argument("--saida", default="")
    args = ap.parse_args()

    fases = [f.strip() for f in args.fases.split(",") if f.strip()]
    rel = {
        "quando_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "quando_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "universo_n": len(DEFAULT_UNIVERSE),
        "fases": fases,
    }
    print(f"# Medição Yahoo intraday `.SA` — {rel['quando_local']}")
    print(f"Universo do Radar: {len(DEFAULT_UNIVERSE)} ativos.")

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        s = await ycli._ensure_session(client)
        print(f"Sessão: cookie={'sim' if s['cookie'] else 'NÃO'} crumb={'sim' if s['crumb'] else 'NÃO'}")
        if "matriz" in fases:
            rel["matriz"] = await fase_matriz(client, args.ticker)
        if "latencia" in fases:
            rel["latencia"] = await fase_latencia(
                client, ["1m", "5m", "15m", "60m", "1d"],
                {"1m": "1d", "5m": "5d", "15m": "5d", "60m": "1mo", "1d": "1mo"},
                args.repeticoes)
        if "rajada" in fases:
            conc = [int(c) for c in args.concorrencias.split(",")]
            r = await fase_rajada(client, list(DEFAULT_UNIVERSE), args.intervalo_rajada,
                                  args.range_rajada, conc, args.gap)
            for reg in r:  # o JSON guarda só o resumo das falhas
                reg["sem_intraday"] = [
                    {"status": x.get("status"), "erro": (x.get("erro") or "")[:100]}
                    for x in reg["sem_intraday"]
                ][:10]
            rel["rajada"] = r
        if "spark" in fases:
            rel["spark"] = await fase_spark(client, list(DEFAULT_UNIVERSE),
                                            args.intervalo_rajada, args.range_rajada,
                                            [10, 20, 25, 40, 74])
        if "cobertura" in fases:
            rel["cobertura"] = await fase_cobertura(
                client, list(DEFAULT_UNIVERSE), [("15m", "5d"), ("1d", "1mo")])
        if "atraso" in fases:
            rel["atraso"] = await fase_atraso(client, TICKERS_LIQUIDEZ[:5], ["1m", "5m", "15m"])

    if args.saida:
        with open(args.saida, "w") as f:
            json.dump(rel, f, indent=2, default=str)
        print(f"\nJSON bruto: {args.saida}")


if __name__ == "__main__":
    asyncio.run(main())
