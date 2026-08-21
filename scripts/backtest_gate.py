#!/usr/bin/env python3
"""backtest_gate.py — regime e volatilidade como GATE de ativação.

Última hipótese viva do lado do Operador. A tese, que é a leitura séria de
"levar em conta dados atuais": cada família de setup só funciona no ambiente
para o qual foi desenhada, e o produto hoje dispara todas em todo lugar.

  - Reversão à média (IFR2, PFR, 123, 9.1) precisa de mercado LATERAL e
    volatilidade alta — é disso que ela extrai o repique.
  - Continuação (9.2, 9.3, 9.4 LW, Ponto Contínuo, Inside Bar, pullback,
    rompimento) precisa de TENDÊNCIA definida e lado ALINHADO com ela.

O `regime.classificar()` já existe e o ADR-009 o usa para ORDENAR o Radar. Aqui
ele vira porta: o sinal desalinhado não é rebaixado, é descartado.

Dimensão nova, nunca medida: volatilidade corrente (ATR14/close no percentil da
própria história do ativo). É o insumo mais "atual" que o snapshot já carrega.

Base: braço de saída FIXO (stop + alvo 1R). O Adendo 5 mostrou que a mecânica do
Operador piora todos os 17 pares sem exceção — se o gate não funciona no braço
mais favorável, não funciona no outro.

Uso: python3 scripts/backtest_gate.py /tmp/linhas-longo.json --rng 15y
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

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".cache-backtest")

REVERSAO = ("IFR2", "PFR", "123 de fundo", "123 de topo", "Reversão", "Setup 9.1")
CONTINUACAO = ("Setup 9.2", "Setup 9.3", "Máx/Mín", "Ponto Contínuo",
               "Inside Bar", "Pullback", "Rompimento")


def familia(nome: str) -> str:
    n = nome or ""
    if any(n.startswith(p) for p in REVERSAO):
        return "reversao"
    if any(p in n for p in CONTINUACAO):
        return "continuacao"
    return "outro"


def stats(vals):
    n = len(vals)
    if n < 2:
        return {"n": n}
    m = sum(vals) / n
    var = sum((v - m) ** 2 for v in vals) / (n - 1)
    se = math.sqrt(var / n)
    return {"n": n, "expR": m, "t": m / se if se else 0.0,
            "acerto": 100.0 * sum(1 for v in vals if v > 0) / n}


def linha(rot, s, largura=46):
    if not s.get("n") or s["n"] < 2:
        print(f"{rot[:largura]:<{largura}s} {s.get('n', 0):>7d}   (amostra insuficiente)")
        return
    flag = "" if s["n"] >= 200 else "  ·n<200"
    print(f"{rot[:largura]:<{largura}s} {s['n']:>7d} {s['expR']:>+9.3f} "
          f"{s['t']:>+8.2f} {s['acerto']:>8.1f}{flag}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("linhas")
    ap.add_argument("--rng", default="15y")
    ap.add_argument("--intervalo", default="1d")
    args = ap.parse_args()

    with open(args.linhas) as f:
        sinais = [l for l in json.load(f)["alvo1"]
                  if l["resultado"] in ("alvo", "stop", "expirou")]

    # Volatilidade corrente: ATR14/close no percentil da própria história.
    cache = {}
    for l in sinais:
        tk = l["ticker"]
        if tk not in cache:
            cs, atrs = [], []
            for nome in (f"{tk}-{args.rng}-{args.intervalo}.json", f"{tk}-{args.rng}.json"):
                p = os.path.join(CACHE_DIR, nome)
                if os.path.exists(p):
                    with open(p) as f:
                        cs = indicators.sanitize_candles(json.load(f))
                    atrs = indicators.compute(cs)["indicators"].get("atr14") or []
                    break
            rel = [(a / c["close"]) if (a and c.get("close")) else None
                   for a, c in zip(atrs, cs)]
            validos = sorted(v for v in rel if v)
            cache[tk] = (rel, validos)
        rel, validos = cache[tk]
        t = l["t"]
        v = rel[t] if t < len(rel) else None
        if not v or not validos:
            l["_vol"] = None
        else:
            pos = sum(1 for x in validos if x <= v) / len(validos)
            l["_vol"] = "alta" if pos >= 0.66 else ("baixa" if pos <= 0.33 else "media")
        l["_fam"] = familia(l["setup"])
        reg = l.get("regime")
        l["_alinhado"] = (
            (reg == "tendencia_alta" and l["lado"] == "alta") or
            (reg == "tendencia_baixa" and l["lado"] == "baixa"))

    cab = f"{'recorte':<46s} {'n':>7s} {'expR':>9s} {'t':>8s} {'acerto%':>8s}"
    print("=" * 88)
    print("GATE DE ATIVAÇÃO — regime e volatilidade como porta, não como desempate")
    print("=" * 88)
    print(f"\n### Linha de base\n{cab}\n" + "-" * 82)
    linha("TODOS os sinais (o que o produto faz hoje)", stats([l["r"] for l in sinais]))

    print(f"\n### Famílias no ambiente que a literatura prevê\n{cab}\n" + "-" * 82)
    rev_lat = [l["r"] for l in sinais if l["_fam"] == "reversao" and l.get("regime") == "lateral"]
    rev_vol = [l["r"] for l in sinais if l["_fam"] == "reversao" and l["_vol"] == "alta"]
    rev_amb = [l["r"] for l in sinais if l["_fam"] == "reversao"
               and l.get("regime") == "lateral" and l["_vol"] == "alta"]
    con_ali = [l["r"] for l in sinais if l["_fam"] == "continuacao" and l["_alinhado"]]
    con_amb = [l["r"] for l in sinais if l["_fam"] == "continuacao"
               and l["_alinhado"] and l["_vol"] in ("baixa", "media")]
    linha("Reversão em LATERAL", stats(rev_lat))
    linha("Reversão em volatilidade ALTA", stats(rev_vol))
    linha("Reversão em LATERAL + volatilidade ALTA", stats(rev_amb))
    linha("Continuação ALINHADA à tendência", stats(con_ali))
    linha("Continuação alinhada + vol. baixa/média", stats(con_amb))

    print(f"\n### O gate completo (só o que passa) vs o que ele descarta\n{cab}\n" + "-" * 82)
    passa = [l["r"] for l in sinais
             if (l["_fam"] == "reversao" and l.get("regime") == "lateral")
             or (l["_fam"] == "continuacao" and l["_alinhado"])]
    barra = [l["r"] for l in sinais
             if not ((l["_fam"] == "reversao" and l.get("regime") == "lateral")
                     or (l["_fam"] == "continuacao" and l["_alinhado"]))]
    linha("PASSA no gate", stats(passa))
    linha("BARRADO pelo gate", stats(barra))
    if passa and barra:
        sp, sb = stats(passa), stats(barra)
        print(f"\nO gate corta {100.0*len(barra)/len(sinais):.1f}% dos sinais. "
              f"Diferença de expectância: {sp['expR']-sb['expR']:+.3f}R")

    print(f"\n### Volatilidade isolada (dimensão nunca medida)\n{cab}\n" + "-" * 82)
    for v in ("baixa", "media", "alta"):
        linha(f"Volatilidade {v}", stats([l["r"] for l in sinais if l["_vol"] == v]))

    print(f"\n### Melhor célula família × regime × volatilidade\n{cab}\n" + "-" * 82)
    cel = defaultdict(list)
    for l in sinais:
        if l["_vol"] and l.get("regime"):
            cel[(l["_fam"], l["regime"], l["_vol"])].append(l["r"])
    ranked = sorted(((k, stats(v)) for k, v in cel.items() if len(v) >= 200),
                    key=lambda x: -x[1]["expR"])
    for k, s in ranked[:6]:
        linha(" · ".join(k), s)
    print(f"\n{len(ranked)} células com n ≥ 200. Com {len(ranked)} tentativas, o limiar")
    print(f"prudente de |t| sobe para ≈ {math.sqrt(2*math.log(max(len(ranked),2))):.1f}.")


if __name__ == "__main__":
    main()
