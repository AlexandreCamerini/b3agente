#!/usr/bin/env python3
"""backtest_comprado.py — o setup comprado bate segurar a ação?

Por que existe: o ADR-016 mostrou que o lado vendido carrega o prejuízo e que o
comprado é menos ruim (semanal: −0,042R, indistinguível de zero). A leitura
tentadora é "restringir o produto ao lado comprado resolve". Mas o período
medido teve viés de alta estrutural — num mercado que sobe, qualquer coisa
comprada parece boa. Sem separar sinal de beta, "só comprado" vira um jeito caro
de comprar o índice.

Este script faz a comparação PAREADA que decide: para cada sinal comprado, mede
o retorno do trade (entra no gatilho, sai no stop/alvo/fim do prazo) contra o
retorno de simplesmente ter comprado o MESMO papel no MESMO dia e segurado até o
fim do MESMO prazo. Mesmo ativo, mesma janela, mesmo período — o que sobra da
diferença é o que o setup adiciona.

Um terceiro braço (placebo) entra a mercado num dia sorteado, com a mesma
geometria de stop/alvo, para separar "o setup escolhe bem" de "a geometria de
saída é que produz o resultado".

Uso:
    python3 scripts/backtest_comprado.py /tmp/linhas-h10.json
    python3 scripts/backtest_comprado.py /tmp/linhas-semanal.json --intervalo 1wk
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))
from app import indicators  # noqa: E402

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".cache-backtest")
SEMENTE = 42


def _candles(ticker: str, rng: str, intervalo: str) -> list:
    for nome in (f"{ticker}-{rng}-{intervalo}.json", f"{ticker}-{rng}.json"):
        p = os.path.join(CACHE_DIR, nome)
        if os.path.exists(p):
            with open(p) as f:
                return indicators.sanitize_candles(json.load(f))
    return []


def simular(entrada, stop, alvo, janela, a_mercado: bool):
    """Percurso de UMA operação comprada. Devolve (retorno_pct, desfecho) ou None
    quando o gatilho não é tocado dentro do prazo."""
    if not janela:
        return None
    if a_mercado:
        i0 = 0
    else:
        i0 = None
        for i, c in enumerate(janela):
            if c.get("high") is not None and c["high"] >= entrada:
                i0 = i
                break
        if i0 is None:
            return None  # sem gatilho: o trade não existiu

    for c in janela[i0:]:
        lo, hi = c.get("low"), c.get("high")
        if lo is None or hi is None:
            continue
        if lo <= stop:                                   # empate intrabar → stop
            return (stop - entrada) / entrada, "stop"
        if alvo is not None and hi >= alvo:
            return (alvo - entrada) / entrada, "alvo"
    fim = janela[-1].get("close")
    if fim is None:
        return None
    return (fim - entrada) / entrada, "expirou"


def resumo(vals: list) -> dict:
    n = len(vals)
    if n < 2:
        return {"n": n}
    m = sum(vals) / n
    var = sum((v - m) ** 2 for v in vals) / (n - 1)
    se = math.sqrt(var / n)
    return {"n": n, "media_pct": round(100 * m, 3), "se_pct": round(100 * se, 3),
            "t": round(m / se, 2) if se else None,
            "positivos_pct": round(100.0 * sum(1 for v in vals if v > 0) / n, 1)}


def pareado(a: list, b: list) -> dict:
    """t pareado da diferença a−b (mesmos sinais, então as amostras não são
    independentes — o teste tem de ser pareado)."""
    difs = [x - y for x, y in zip(a, b)]
    n = len(difs)
    if n < 2:
        return {"n": n}
    m = sum(difs) / n
    var = sum((d - m) ** 2 for d in difs) / (n - 1)
    se = math.sqrt(var / n)
    return {"n": n, "dif_pct": round(100 * m, 3), "t": round(m / se, 2) if se else None,
            "vence_pct": round(100.0 * sum(1 for d in difs if d > 0) / n, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("linhas")
    ap.add_argument("--intervalo", default="1d", choices=("1d", "1wk"))
    ap.add_argument("--rng", default="", help="range usado no cache (default: 5y ou max)")
    ap.add_argument("--horizonte", type=int, default=10)
    ap.add_argument("--custo-pct", type=float, default=0.0,
                    help="custo round-trip em %% (corretagem+emolumentos+slippage)")
    args = ap.parse_args()
    rng = args.rng or ("5y" if args.intervalo == "1d" else "max")

    with open(args.linhas) as f:
        todas = json.load(f)["alvo1"]
    compradas = [l for l in todas if l["lado"] == "alta"]

    rnd = random.Random(SEMENTE)
    cache: dict = {}
    setup_r, hold_r, plac_r = [], [], []
    desf = defaultdict(int)
    por_setup = defaultdict(lambda: ([], []))
    sem_gatilho = 0

    for l in compradas:
        tk = l["ticker"]
        if tk not in cache:
            cache[tk] = _candles(tk, rng, args.intervalo)
        cs = cache[tk]
        t = l["t"]
        if not cs or t + args.horizonte + 1 >= len(cs):
            continue
        janela = cs[t + 1: t + 1 + args.horizonte]
        if len(janela) < args.horizonte:
            continue

        a_mercado = str(l.get("tipo") or "").startswith("a mercado")
        r = simular(l["entrada"], l["stop"], l["alvo1"], janela, a_mercado)
        if r is None:
            sem_gatilho += 1
            continue
        ret_setup, desfecho = r
        desf[desfecho] += 1

        # Benchmark pareado: comprou o MESMO papel no fechamento do dia do sinal
        # e segurou até o fim do MESMO prazo. Sem stop, sem alvo, sem gatilho.
        p0, p1 = cs[t].get("close"), janela[-1].get("close")
        if not p0 or not p1:
            continue
        ret_hold = (p1 - p0) / p0

        # Placebo: entra a mercado num dia sorteado, mesma geometria relativa.
        tp = rnd.randint(0, len(cs) - args.horizonte - 2)
        pp = cs[tp].get("close")
        if not pp:
            continue
        jan_p = cs[tp + 1: tp + 1 + args.horizonte]
        rp = simular(pp, pp * (1 + (l["stop"] - l["entrada"]) / l["entrada"]),
                     pp * (1 + (l["alvo1"] - l["entrada"]) / l["entrada"]), jan_p, True)
        if rp is None:
            continue

        c = args.custo_pct / 100.0
        setup_r.append(ret_setup - c)
        hold_r.append(ret_hold - c)
        plac_r.append(rp[0] - c)
        por_setup[l["setup"]][0].append(ret_setup - c)
        por_setup[l["setup"]][1].append(ret_hold - c)

    print("=" * 92)
    print(f"SÓ COMPRADO — {args.linhas}  (intervalo {args.intervalo}, "
          f"horizonte {args.horizonte}, custo {args.custo_pct}%)")
    print("=" * 92)
    print(f"\nSinais comprados: {len(compradas)} · avaliados: {len(setup_r)} · "
          f"sem gatilho: {sem_gatilho}")
    print(f"Desfechos: {dict(desf)}")

    print("\n### Retorno médio por operação (%)")
    print(f"{'braço':<38s} {'n':>6s} {'média%':>9s} {'t':>7s} {'positivos%':>11s}")
    print("-" * 76)
    for nome, vals in (("SETUP (entra no gatilho)", setup_r),
                       ("SEGURAR a ação o mesmo prazo", hold_r),
                       ("PLACEBO (dia sorteado)", plac_r)):
        s = resumo(vals)
        if not s.get("n") or s["n"] < 2:
            continue
        print(f"{nome:<38s} {s['n']:>6d} {s['media_pct']:>+9.3f} "
              f"{s['t']:>+7.2f} {s['positivos_pct']:>11.1f}")

    print("\n### Comparações pareadas (mesmos sinais)")
    for nome, a, b in (("SETUP − SEGURAR", setup_r, hold_r),
                       ("SETUP − PLACEBO", setup_r, plac_r)):
        d = pareado(a, b)
        if not d.get("n"):
            continue
        print(f"{nome:<20s} diferença {d['dif_pct']:>+7.3f}%  t = {d['t']:>+6.2f}  "
              f"vence em {d['vence_pct']:.1f}% dos casos")

    print("\n### Por setup — SETUP vs SEGURAR (pareado)")
    print(f"{'setup':<44s} {'n':>6s} {'setup%':>9s} {'segurar%':>10s} {'dif%':>8s} {'t':>7s}")
    print("-" * 88)
    for nome in sorted(por_setup, key=lambda k: -len(por_setup[k][0])):
        a, b = por_setup[nome]
        if len(a) < 30:
            continue
        d = pareado(a, b)
        print(f"{str(nome)[:44]:<44s} {len(a):>6d} {100*sum(a)/len(a):>+9.3f} "
              f"{100*sum(b)/len(b):>+10.3f} {d['dif_pct']:>+8.3f} {d['t']:>+7.2f}")

    print("\nLeitura: se 'SETUP − SEGURAR' não é positivo com significância, o setup")
    print("comprado não adiciona nada sobre ter comprado o papel e esperado — o que")
    print("parecia edge do lado comprado era o mercado subindo.")


if __name__ == "__main__":
    main()
