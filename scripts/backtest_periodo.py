#!/usr/bin/env python3
"""backtest_periodo.py — o motor ganha valor quando segurar a ação é ruim?

Por que existe: o ADR-016 mediu 2023–2026, um período de alta, e registrou isso
como limitação. Num mercado que sobe, "vender é ruim" e "segurar bate o setup"
são o resultado esperado — não distinguem motor ruim de período favorável.

Um sistema de trading justifica sua existência justamente quando segurar é
ruim. Este script segmenta por ano e põe lado a lado a expectância do motor e o
retorno de simplesmente ter segurado o mesmo papel pela mesma janela. O retorno
de segurar mede o regime do ano de forma endógena — sem rotular "bull"/"bear"
à mão.

A pergunta que ele responde: nos anos em que segurar deu prejuízo, o motor
entregou resultado?

Uso: python3 scripts/backtest_periodo.py /tmp/linhas-longo.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))
from app import indicators  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backtest_comprado import CACHE_DIR as CACHE_DIR_LOCAL, _candles, simular  # noqa: E402


def _ibov_por_ano() -> dict:
    """Retorno anual do mercado, do primeiro ao último pregão do ano.

    Proxy: BOVA11 (ETF que replica o Ibovespa). O índice em si (`^BVSP`) não é
    alcançável por `yahoo.get_history` — `yahoo_symbol()` sufixa `.SA` e
    `^BVSP.SA` devolve 404. BOVA11 é ticker B3 normal e tem histórico desde 2008.
    """
    import asyncio
    from app import yahoo
    cache = os.path.join(CACHE_DIR_LOCAL, "BOVA11-15y-1d.json")
    if os.path.exists(cache):
        with open(cache) as f:
            cs = json.load(f)
    else:
        cs = (asyncio.run(yahoo.get_history("BOVA11", rng="15y", interval="1d"))
              or {}).get("candles") or []
        os.makedirs(CACHE_DIR_LOCAL, exist_ok=True)
        with open(cache, "w") as f:
            json.dump(cs, f)
    por_ano = defaultdict(list)
    for c in cs:
        if c.get("close"):
            por_ano[str(c["date"])[:4]].append(c["close"])
    return {a: 100.0 * (v[-1] - v[0]) / v[0] for a, v in por_ano.items() if len(v) > 1}


def stats_r(linhas: list) -> dict:
    res = [l for l in linhas if l["resultado"] in ("alvo", "stop", "expirou")]
    n = len(res)
    if n < 2:
        return {"n": n}
    rs = [l["r"] for l in res]
    m = sum(rs) / n
    var = sum((r - m) ** 2 for r in rs) / (n - 1)
    se = math.sqrt(var / n)
    return {"n": n, "expR": round(m, 3), "t": round(m / se, 2) if se else None}


def pareado(a: list, b: list) -> dict:
    difs = [x - y for x, y in zip(a, b)]
    n = len(difs)
    if n < 2:
        return {"n": n}
    m = sum(difs) / n
    var = sum((d - m) ** 2 for d in difs) / (n - 1)
    se = math.sqrt(var / n)
    return {"n": n, "dif": 100 * m, "t": round(m / se, 2) if se else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("linhas")
    ap.add_argument("--rng", default="max")
    ap.add_argument("--intervalo", default="1d")
    ap.add_argument("--horizonte", type=int, default=10)
    args = ap.parse_args()

    with open(args.linhas) as f:
        todas = json.load(f)["alvo1"]

    # Regime do ano pelo ÍNDICE, não pelo retorno dos dias de sinal. Os setups
    # são majoritariamente de reversão e disparam depois de queda, então a
    # janela seguinte a um sinal tem drift positivo por construção — usá-la
    # para rotular o ano classificaria quase todo ano como "mercado a favor".
    ibov = _ibov_por_ano()
    print("Ibovespa por ano (fonte da classificação de regime):")
    print("  " + "  ".join(f"{a}:{v:+.1f}%" for a, v in sorted(ibov.items())))

    cache: dict = {}
    por_ano = defaultdict(lambda: {"todas": [], "long": [], "short": [],
                                   "ret_setup": [], "ret_hold": []})

    for l in todas:
        ano = str(l["data"])[:4]
        b = por_ano[ano]
        b["todas"].append(l)
        (b["long"] if l["lado"] == "alta" else b["short"]).append(l)

        if l["lado"] != "alta":
            continue  # "segurar" só faz sentido contra posição comprada
        tk = l["ticker"]
        if tk not in cache:
            cache[tk] = _candles(tk, args.rng, args.intervalo)
        cs = cache[tk]
        t = l["t"]
        if not cs or t + args.horizonte + 1 >= len(cs):
            continue
        janela = cs[t + 1: t + 1 + args.horizonte]
        if len(janela) < args.horizonte:
            continue
        r = simular(l["entrada"], l["stop"], l["alvo1"], janela,
                    str(l.get("tipo") or "").startswith("a mercado"))
        if r is None:
            continue
        p0, p1 = cs[t].get("close"), janela[-1].get("close")
        if not p0 or not p1:
            continue
        b["ret_setup"].append(r[0])
        b["ret_hold"].append((p1 - p0) / p0)

    anos = sorted(por_ano)
    print("=" * 108)
    print("MOTOR × REGIME DE MERCADO — o setup ganha valor quando segurar é ruim?")
    print("=" * 108)
    print(f"\n{'ano':<6s} {'n':>7s} {'expR':>8s} {'expR long':>11s} {'expR short':>12s} "
          f"{'setup%':>9s} {'SEGURAR%':>10s} {'dif%':>8s} {'t':>7s}")
    print("-" * 108)

    bons, ruins = [], []   # anos em que segurar foi positivo / negativo
    for ano in anos:
        b = por_ano[ano]
        g, lo, sh = stats_r(b["todas"]), stats_r(b["long"]), stats_r(b["short"])
        if not g.get("n") or g["n"] < 30:
            continue
        rs, rh = b["ret_setup"], b["ret_hold"]
        if len(rs) < 30:
            continue
        ms, mh = 100 * sum(rs) / len(rs), 100 * sum(rh) / len(rh)
        d = pareado(rs, rh)
        print(f"{ano:<6s} {g['n']:>7d} {g['expR']:>+8.3f} "
              f"{(lo.get('expR') if lo.get('n', 0) > 1 else float('nan')):>+11.3f} "
              f"{(sh.get('expR') if sh.get('n', 0) > 1 else float('nan')):>+12.3f} "
              f"{ms:>+9.3f} {mh:>+10.3f} {d['dif']:>+8.3f} {d['t']:>+7.2f}")
        (bons if ibov.get(ano, 0.0) > 0 else ruins).append((ano, b, ms, mh))

    def bloco(titulo, grupo):
        if not grupo:
            print(f"\n### {titulo}: nenhum ano nesta categoria")
            return
        todas = [l for _, b, _, _ in grupo for l in b["todas"]]
        longs = [l for _, b, _, _ in grupo for l in b["long"]]
        shorts = [l for _, b, _, _ in grupo for l in b["short"]]
        rs = [x for _, b, _, _ in grupo for x in b["ret_setup"]]
        rh = [x for _, b, _, _ in grupo for x in b["ret_hold"]]
        g, lo, sh = stats_r(todas), stats_r(longs), stats_r(shorts)
        d = pareado(rs, rh)
        print(f"\n### {titulo}")
        print(f"anos: {', '.join(a for a, _, _, _ in grupo)}")
        print(f"  motor (todos)   : expR {g['expR']:+.3f}  (n={g['n']}, t={g['t']:+.2f})")
        if lo.get("n", 0) > 1:
            print(f"  motor comprado  : expR {lo['expR']:+.3f}  (n={lo['n']}, t={lo['t']:+.2f})")
        if sh.get("n", 0) > 1:
            print(f"  motor vendido   : expR {sh['expR']:+.3f}  (n={sh['n']}, t={sh['t']:+.2f})")
        if rs:
            print(f"  setup comprado  : {100*sum(rs)/len(rs):+.3f}% por operação")
            print(f"  SEGURAR a ação  : {100*sum(rh)/len(rh):+.3f}% pela mesma janela")
            print(f"  diferença       : {d['dif']:+.3f} p.p.  (t={d['t']:+.2f})")

    bloco("ANOS EM QUE SEGURAR FOI POSITIVO (mercado a favor)", bons)
    bloco("ANOS EM QUE SEGURAR FOI NEGATIVO (mercado contra)", ruins)

    print("\nLeitura: se o motor continua negativo — e continua perdendo de segurar —")
    print("também nos anos em que segurar deu prejuízo, o resultado do ADR-016 não é")
    print("artefato do período de alta. Se ele vira positivo quando o mercado cai, o")
    print("motor é dependente de regime e o remédio é gating, não abandono.")


if __name__ == "__main__":
    main()
