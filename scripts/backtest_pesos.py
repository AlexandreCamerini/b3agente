#!/usr/bin/env python3
"""backtest_pesos.py — pesar setups pelo desempenho histórico funciona?

A ideia testada: em vez de tratar os 13 setups como iguais, usar o desempenho
medido de cada um como peso — o que, na prática, é selecionar/ranquear setups por
skill histórico. (Ponderar a CONFLUÊNCIA por esse peso dá no mesmo: 93% dos
sinais têm confluência 100%, então ela é quase constante e o peso do setup passa
a ser o único termo que varia.)

Técnica legítima — ensemble weighting by historical skill, usada em fundo
sistemático. Só funciona sob uma condição: **persistência**. Setup que foi ruim
no período passado precisa continuar ruim no próximo. Se o ranking embaralha, o
peso de ontem é ruído aplicado ao amanhã.

Armadilha que este script evita: pesar pelo desempenho medido e avaliar na MESMA
amostra é circular e produz número ótimo e falso. Aqui o peso vem sempre de
janela ANTERIOR e a avaliação é out-of-sample, caminhando no tempo.

Duas medições:
  1. Persistência do ranking (Spearman entre janelas consecutivas). É a condição
     necessária — se for ~0, a ideia não tem como funcionar, independente da
     regra de seleção.
  2. A estratégia de fato: a cada janela, seleciona pelos números da janela
     anterior e mede o que aconteceu na seguinte.

Uso: python3 scripts/backtest_pesos.py /tmp/linhas-longo.json
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict


def expectancia(rs):
    return sum(rs) / len(rs) if rs else None


def stats(vals):
    n = len(vals)
    if n < 2:
        return {"n": n}
    m = sum(vals) / n
    var = sum((v - m) ** 2 for v in vals) / (n - 1)
    se = math.sqrt(var / n)
    return {"n": n, "expR": m, "t": m / se if se else 0.0,
            "acerto": 100.0 * sum(1 for v in vals if v > 0) / n}


def spearman(a: dict, b: dict) -> float | None:
    """Correlação de postos entre dois rankings de setup. Só os comuns."""
    comuns = sorted(set(a) & set(b))
    if len(comuns) < 4:
        return None
    def postos(d):
        ordenado = sorted(comuns, key=lambda k: d[k])
        return {k: i for i, k in enumerate(ordenado)}
    pa, pb = postos(a), postos(b)
    n = len(comuns)
    d2 = sum((pa[k] - pb[k]) ** 2 for k in comuns)
    return 1 - (6 * d2) / (n * (n * n - 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("linhas")
    ap.add_argument("--janelas", type=int, default=15, help="quantos períodos")
    ap.add_argument("--min-n", type=int, default=40, help="n mínimo por setup na janela")
    args = ap.parse_args()

    with open(args.linhas) as f:
        sinais = [l for l in json.load(f)["alvo1"]
                  if l["resultado"] in ("alvo", "stop", "expirou")]
    sinais.sort(key=lambda l: l["data"])

    tam = len(sinais) // args.janelas
    cortes = [sinais[i * tam:(i + 1) * tam] for i in range(args.janelas)]
    cortes = [c for c in cortes if c]

    # Expectância por setup em cada janela
    por_janela = []
    for corte in cortes:
        d = defaultdict(list)
        for l in corte:
            d[l["setup"]].append(l["r"])
        por_janela.append({k: expectancia(v) for k, v in d.items() if len(v) >= args.min_n})

    print("=" * 92)
    print("PESAR SETUPS PELO DESEMPENHO HISTÓRICO — a dispersão é persistente?")
    print("=" * 92)
    print(f"\n{len(cortes)} janelas · {tam} sinais cada · "
          f"{cortes[0][0]['data']} → {cortes[-1][-1]['data']}")

    # ---- 1. Persistência ----
    print("\n### 1. Persistência do ranking (condição necessária)")
    print(f"{'transição':<22s} {'Spearman':>10s}  {'setups comuns':>14s}")
    print("-" * 52)
    corrs = []
    for i in range(len(por_janela) - 1):
        r = spearman(por_janela[i], por_janela[i + 1])
        if r is None:
            continue
        corrs.append(r)
        comuns = len(set(por_janela[i]) & set(por_janela[i + 1]))
        print(f"janela {i+1:>2d} → {i+2:<10d} {r:>+10.3f}  {comuns:>14d}")
    if corrs:
        media = sum(corrs) / len(corrs)
        se = math.sqrt(sum((c - media) ** 2 for c in corrs) / (len(corrs) - 1) / len(corrs))
        print(f"\nSpearman MÉDIO: {media:+.3f}  (erro-padrão {se:.3f}, "
              f"t = {media/se:+.2f} contra zero)")
        print(f"positivas em {sum(1 for c in corrs if c > 0)}/{len(corrs)} transições")

    # ---- 2. A estratégia out-of-sample ----
    print("\n### 2. A estratégia: seleciona pela janela anterior, mede na seguinte")
    print(f"{'regra de seleção':<40s} {'n':>8s} {'expR':>9s} {'t':>8s} {'acerto%':>9s}")
    print("-" * 78)

    todos_oos, sel_pos, sel_top3, sel_top1 = [], [], [], []
    for i in range(1, len(cortes)):
        anterior, atual = por_janela[i - 1], cortes[i]
        if not anterior:
            continue
        positivos = {k for k, v in anterior.items() if v is not None and v > 0}
        ordenados = sorted((k for k in anterior if anterior[k] is not None),
                           key=lambda k: -anterior[k])
        top3, top1 = set(ordenados[:3]), set(ordenados[:1])
        for l in atual:
            todos_oos.append(l["r"])
            if l["setup"] in positivos:
                sel_pos.append(l["r"])
            if l["setup"] in top3:
                sel_top3.append(l["r"])
            if l["setup"] in top1:
                sel_top1.append(l["r"])

    for rot, vals in (("TODOS (o produto hoje)", todos_oos),
                      ("Só os que foram POSITIVOS antes", sel_pos),
                      ("Só o TOP 3 da janela anterior", sel_top3),
                      ("Só o TOP 1 da janela anterior", sel_top1)):
        s = stats(vals)
        if not s.get("n") or s["n"] < 2:
            print(f"{rot:<40s} {s.get('n', 0):>8d}   (amostra insuficiente)")
            continue
        print(f"{rot:<40s} {s['n']:>8d} {s['expR']:>+9.3f} {s['t']:>+8.2f} {s['acerto']:>9.1f}")

    # ---- 3. O teto: e se soubéssemos o futuro? ----
    print("\n### 3. Teto teórico — seleção com informação do FUTURO (impossível)")
    print("Serve só para dimensionar o quanto haveria a ganhar se a persistência")
    print("fosse perfeita. Não é resultado alcançável.")
    perfeito = []
    for i in range(1, len(cortes)):
        atual_stats = defaultdict(list)
        for l in cortes[i]:
            atual_stats[l["setup"]].append(l["r"])
        bons = {k for k, v in atual_stats.items()
                if len(v) >= args.min_n and expectancia(v) > 0}
        perfeito.extend(l["r"] for l in cortes[i] if l["setup"] in bons)
    s = stats(perfeito)
    if s.get("n", 0) > 1:
        print(f"\n{'Seleção com bola de cristal':<40s} {s['n']:>8d} {s['expR']:>+9.3f} "
              f"{s['t']:>+8.2f} {s['acerto']:>9.1f}")

    print("\nLeitura: se o Spearman médio for próximo de zero, o ranking de setups")
    print("embaralha entre períodos e o peso histórico é ruído. Nesse caso nem a regra")
    print("de seleção mais esperta ajuda — e a distância até o teto do item 3 mostra")
    print("quanto do ganho aparente vem de olhar para o futuro.")


if __name__ == "__main__":
    main()
