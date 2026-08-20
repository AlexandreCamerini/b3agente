#!/usr/bin/env python3
"""backtest_momentum.py — momentum relativo tem edge onde os setups não têm?

Por que existe: o ADR-016 eliminou os 13 setups de price action. O candidato com
maior lastro acadêmico que sobrou é momentum de série temporal / cross-sectional
(Jegadeesh & Titman 1993; Moskowitz, Ooi & Pedersen 2012; replicado pela AQR em
~100 anos). O ADR-009 **já implementou** momentum relativo dentro de
`regime.ranquear()` — mas como critério de ORDENAÇÃO, nunca medido como sinal.
Pode ser que o produto já tenha um sinal que funciona, enterrado como desempate.

Diferença de natureza: isto não é um setup por trade com stop e alvo. É
estratégia de carteira — ranqueia o universo, compra a cesta do topo, rebalanceia
periodicamente. A medição é retorno mensal da carteira contra o universo
equal-weight (o "mercado"), não R-múltiplo.

Formação 12-1: retorno dos últimos 12 meses PULANDO o mês mais recente. O pulo é
padrão na literatura — o último mês carrega reversão de curto prazo, que é efeito
oposto e contamina o sinal.

Uso: python3 scripts/backtest_momentum.py
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
from app.scanner import DEFAULT_UNIVERSE  # noqa: E402

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".cache-backtest")
MES = 21          # pregões por mês
FORMACAO = 252    # janela de formação (12 meses)
PULO = 21         # pula o mês mais recente (reversão de curto prazo)


def carregar(rng: str) -> dict:
    out = {}
    for tk in DEFAULT_UNIVERSE:
        for nome in (f"{tk}-{rng}-1d.json", f"{tk}-{rng}.json"):
            p = os.path.join(CACHE_DIR, nome)
            if os.path.exists(p):
                with open(p) as f:
                    cs = indicators.sanitize_candles(json.load(f))
                if len(cs) > FORMACAO + MES:
                    out[tk] = {c["date"]: c["close"] for c in cs if c.get("close")}
                break
    return out


def stats(vals: list) -> dict:
    n = len(vals)
    if n < 2:
        return {"n": n}
    m = sum(vals) / n
    var = sum((v - m) ** 2 for v in vals) / (n - 1)
    se = math.sqrt(var / n)
    dp = math.sqrt(var)
    return {"n": n, "media": 100 * m, "t": m / se if se else 0.0,
            "sharpe_anual": (m / dp * math.sqrt(12)) if dp else 0.0,
            "positivos": 100.0 * sum(1 for v in vals if v > 0) / n}


def pareado(a: list, b: list) -> dict:
    d = [x - y for x, y in zip(a, b)]
    n = len(d)
    if n < 2:
        return {"n": n}
    m = sum(d) / n
    var = sum((x - m) ** 2 for x in d) / (n - 1)
    se = math.sqrt(var / n)
    return {"n": n, "dif": 100 * m, "t": m / se if se else 0.0,
            "vence": 100.0 * sum(1 for x in d if x > 0) / n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rng", default="15y")
    ap.add_argument("--cesta", type=int, default=10, help="quantos ativos na cesta")
    ap.add_argument("--manutencao", type=int, default=MES, help="pregões até rebalancear")
    args = ap.parse_args()

    precos = carregar(args.rng)
    if not precos:
        print("Sem cache. Rode antes: backtest_sinal.py --rng 15y")
        return

    # Calendário comum: datas em que a maioria dos tickers negociou.
    contagem = defaultdict(int)
    for série in precos.values():
        for d in série:
            contagem[d] += 1
    datas = sorted(d for d, c in contagem.items() if c >= len(precos) * 0.6)

    print(f"universo: {len(precos)} tickers · calendário: {datas[0]} → {datas[-1]} "
          f"({len(datas)} pregões)")
    print(f"formação 12-1 ({FORMACAO} barras, pulando {PULO}) · cesta top/bottom "
          f"{args.cesta} · manutenção {args.manutencao} pregões\n")

    r_top, r_bot, r_uni = [], [], []
    periodos = []

    i = FORMACAO
    while i + args.manutencao < len(datas):
        d_form, d_ini = datas[i - PULO], datas[i]
        d_base = datas[i - FORMACAO]
        d_fim = datas[i + args.manutencao]

        elegiveis = []
        for tk, s in precos.items():
            p_base, p_form, p_ini, p_fim = (s.get(d_base), s.get(d_form),
                                            s.get(d_ini), s.get(d_fim))
            if not all((p_base, p_form, p_ini, p_fim)):
                continue
            elegiveis.append((tk, (p_form - p_base) / p_base, (p_fim - p_ini) / p_ini))

        if len(elegiveis) < args.cesta * 3:
            i += args.manutencao
            continue

        elegiveis.sort(key=lambda x: -x[1])           # por momentum de formação
        top = elegiveis[:args.cesta]
        bot = elegiveis[-args.cesta:]
        r_top.append(sum(x[2] for x in top) / len(top))
        r_bot.append(sum(x[2] for x in bot) / len(bot))
        r_uni.append(sum(x[2] for x in elegiveis) / len(elegiveis))
        periodos.append(d_ini)
        i += args.manutencao

    print("=" * 88)
    print("MOMENTUM RELATIVO — carteira rebalanceada vs universo equal-weight")
    print("=" * 88)
    print(f"\nPeríodos avaliados: {len(r_top)}  ({periodos[0]} → {periodos[-1]})")
    print(f"\n{'carteira':<34s} {'ret médio%':>12s} {'t':>8s} {'Sharpe a.a.':>13s} {'meses+':>9s}")
    print("-" * 80)
    for nome, série in (("TOP momentum (compra)", r_top),
                        ("Universo equal-weight (mercado)", r_uni),
                        ("BOTTOM momentum (o pior)", r_bot)):
        s = stats(série)
        print(f"{nome:<34s} {s['media']:>+12.3f} {s['t']:>+8.2f} "
              f"{s['sharpe_anual']:>+13.2f} {s['positivos']:>9.1f}")

    print("\n### Comparações pareadas (mesmos períodos)")
    for nome, a, b in (("TOP − universo (long-only, o que o produto poderia fazer)", r_top, r_uni),
                       ("TOP − BOTTOM (fator momentum clássico, long-short)", r_top, r_bot)):
        d = pareado(a, b)
        print(f"{nome}\n    {d['dif']:>+7.3f} p.p./período   t = {d['t']:>+6.2f}   "
              f"vence em {d['vence']:.1f}% dos períodos")

    print("\nLeitura: 'TOP − universo' é o que interessa ao produto — ele não vende a")
    print("descoberto. Se não for positivo com significância, momentum relativo também")
    print("não entrega edge implementável aqui, e a lista de candidatos encolhe de novo.")


if __name__ == "__main__":
    main()
