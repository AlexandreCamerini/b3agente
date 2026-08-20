#!/usr/bin/env python3
"""backtest_horizonte.py — compara a expectância dos setups em vários horizontes.

Por que existe: o produto avalia em 10 pregões (`analysis_outcomes.HORIZON_PREGOES`)
e o ADR-016 mediu expectância negativa nesse horizonte. A única evidência
quantitativa favorável a um setup do produto na B3 (Pellin, EnANPAD 2022, Setup
9.1) usou gráfico SEMANAL. A hipótese que este script testa: a família não é
inútil — o produto pode estar medindo (e operando) no horizonte errado.

Uso:
    python3 scripts/backtest_horizonte.py /tmp/linhas-h10.json /tmp/linhas-h20.json ...

Os arquivos vêm de `backtest_sinal.py --horizonte N --saida ...`. O horizonte é
lido do nome do arquivo (`-hN.json`) ou da ordem dos argumentos.
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict

MIN_N = 100  # piso para tratar a célula como resultado, não como indício


def stats(linhas: list) -> dict:
    res = [l for l in linhas if l["resultado"] in ("alvo", "stop", "expirou")]
    n = len(res)
    if n < 2:
        return {"n": n}
    rs = [l["r"] for l in res]
    m = sum(rs) / n
    var = sum((r - m) ** 2 for r in rs) / (n - 1)
    se = math.sqrt(var / n)
    return {"n": n, "expR": round(m, 3), "se": se,
            "t": round(m / se, 2) if se else None,
            "acerto": round(100.0 * sum(1 for r in rs if r > 0) / n, 1),
            "naoAcionados": sum(1 for l in linhas if l["resultado"] == "sem_gatilho")}


def celula(s: dict) -> str:
    if not s.get("n") or s["n"] < 2:
        return f"{'—':>16s}"
    marca = "*" if (s["t"] is not None and abs(s["t"]) >= 2 and s["n"] >= MIN_N) else " "
    return f"{s['expR']:>+7.3f}{marca}(n{s['n']:<5d})"


def main():
    caminhos = sys.argv[1:]
    if not caminhos:
        print(__doc__)
        return

    dados = {}
    for c in caminhos:
        m = re.search(r"-h(\d+)\.json$", c)
        h = int(m.group(1)) if m else len(dados) + 1
        with open(c) as f:
            dados[h] = json.load(f)
    hs = sorted(dados)

    for barreira in ("alvo1", "alvo2"):
        rot = "alvo1 (1R)" if barreira == "alvo1" else "alvo2 (projeção do setup)"
        print(f"\n{'=' * 104}\nBARREIRA = {rot}\n{'=' * 104}")

        print(f"\n### Geral por horizonte")
        print(f"{'horizonte':<14s} {'n':>7s} {'expR':>9s} {'t':>8s} {'acerto%':>9s} {'não acionados':>15s}")
        print("-" * 70)
        for h in hs:
            s = stats(dados[h][barreira])
            if not s.get("n"):
                continue
            print(f"{str(h) + ' pregões':<14s} {s['n']:>7d} {s['expR']:>+9.3f} "
                  f"{s['t']:>+8.2f} {s['acerto']:>9.1f} {s['naoAcionados']:>15d}")

        print(f"\n### Por setup × horizonte   (* = |t| ≥ 2 e n ≥ {MIN_N})")
        cab = "".join(f"{'h=' + str(h):>16s}" for h in hs)
        print(f"{'setup':<42s}{cab}")
        print("-" * (42 + 16 * len(hs)))

        setups_all = set()
        for h in hs:
            for l in dados[h][barreira]:
                setups_all.add(l["setup"])

        # ordena pelo n do menor horizonte (o mais populoso)
        base = defaultdict(list)
        for l in dados[hs[0]][barreira]:
            base[l["setup"]].append(l)

        for nome in sorted(setups_all, key=lambda x: -len(base.get(x, []))):
            linha = ""
            for h in hs:
                grupo = [l for l in dados[h][barreira] if l["setup"] == nome]
                linha += celula(stats(grupo))
            print(f"{str(nome)[:42]:<42s}{linha}")

        print(f"\n### Por lado × horizonte")
        for lado in ("alta", "baixa"):
            linha = ""
            for h in hs:
                grupo = [l for l in dados[h][barreira] if l["lado"] == lado]
                linha += celula(stats(grupo))
            print(f"{lado:<42s}{linha}")

    print("\nLeitura: expectância que MELHORA de forma monótona com o horizonte "
          "sugere que\no trade precisa de mais tempo. Expectância que fica negativa "
          "em todos os\nhorizontes elimina a hipótese de 'horizonte errado' para "
          "aquele setup.")


if __name__ == "__main__":
    main()
