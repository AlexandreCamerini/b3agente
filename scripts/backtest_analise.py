#!/usr/bin/env python3
"""backtest_analise.py — lê as linhas cruas de backtest_sinal.py e responde às
perguntas do ADR com controle de sobreajuste.

Três proteções que separam evidência de ruído:
  1. Erro-padrão e t-stat por célula — expectância sem incerteza não é resultado.
  2. Walk-forward: a mesma célula medida em janelas de tempo consecutivas. Edge
     que só aparece numa janela é ruído.
  3. Contagem explícita de configurações testadas. Testar 40 combinações e
     reportar a melhor produz um número bonito e falso (Bailey & López de Prado,
     "The Deflated Sharpe Ratio", 2014). O limiar de |t| sobe com o número de
     tentativas.

Uso: python3 scripts/backtest_analise.py /tmp/backtest-linhas.json
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict

MIN_N = 30  # piso para reportar como resultado; abaixo disso é "amostra insuficiente"


def stats(linhas: list) -> dict:
    """Expectância em R com incerteza. `sem_gatilho` fora do denominador."""
    res = [l for l in linhas if l["resultado"] in ("alvo", "stop", "expirou")]
    n = len(res)
    if n < 2:
        return {"n": n}
    rs = [l["r"] for l in res]
    media = sum(rs) / n
    var = sum((r - media) ** 2 for r in rs) / (n - 1)
    se = math.sqrt(var / n)
    ganhos = [r for r in rs if r > 0]
    perdas = [-r for r in rs if r < 0]
    return {
        "n": n,
        "expR": round(media, 3),
        "se": round(se, 3),
        "t": round(media / se, 2) if se > 0 else None,
        "ic95": (round(media - 1.96 * se, 3), round(media + 1.96 * se, 3)),
        "acerto": round(100.0 * len(ganhos) / n, 1),
        "pf": round(sum(ganhos) / sum(perdas), 2) if perdas else None,
        "naoAcionados": sum(1 for l in linhas if l["resultado"] == "sem_gatilho"),
    }


def tabela(titulo: str, grupos: dict, ordena_por_n=True):
    print(f"\n### {titulo}")
    print(f"{'chave':<46s} {'n':>6s} {'expR':>7s} {'IC95':>17s} {'t':>6s} {'acerto%':>8s} {'PF':>6s}")
    print("-" * 100)
    chaves = sorted(grupos, key=(lambda k: -(grupos[k].get("n") or 0)) if ordena_por_n else str)
    for k in chaves:
        s = grupos[k]
        if not s.get("n"):
            continue
        if s["n"] < 2:
            print(f"{str(k)[:46]:<46s} {s['n']:>6d}   (amostra insuficiente)")
            continue
        ic = f"[{s['ic95'][0]:+.2f},{s['ic95'][1]:+.2f}]"
        flag = "" if s["n"] >= MIN_N else "  ·n<30"
        t = f"{s['t']:+.2f}" if s["t"] is not None else "—"
        pf = f"{s['pf']:.2f}" if s["pf"] else "—"
        print(f"{str(k)[:46]:<46s} {s['n']:>6d} {s['expR']:>+7.3f} {ic:>17s} "
              f"{t:>6s} {s['acerto']:>8.1f} {pf:>6s}{flag}")


def walk_forward(linhas: list, chave_fn, janelas: int = 6):
    """A mesma célula medida em janelas de tempo consecutivas. Edge real
    sobrevive à troca de janela; sobreajuste não."""
    ordenadas = sorted(linhas, key=lambda l: l["data"])
    if not ordenadas:
        return
    tam = len(ordenadas) // janelas
    cortes = [ordenadas[i * tam:(i + 1) * tam] for i in range(janelas)]
    periodos = [(c[0]["data"][:7], c[-1]["data"][:7]) for c in cortes if c]

    grupos = defaultdict(lambda: [None] * janelas)
    for i, corte in enumerate(cortes):
        por = defaultdict(list)
        for l in corte:
            por[chave_fn(l)].append(l)
        for k, v in por.items():
            s = stats(v)
            grupos[k][i] = (s.get("expR"), s.get("n"))

    print(f"\n### Walk-forward — {janelas} janelas consecutivas")
    print("janelas: " + " | ".join(f"{a}→{b}" for a, b in periodos))
    print(f"\n{'chave':<40s} " + " ".join(f"{'j'+str(i+1):>13s}" for i in range(janelas)) + "   sinais+")
    print("-" * 116)
    for k in sorted(grupos, key=lambda x: -sum((g[1] or 0) for g in grupos[x] if g)):
        cels = grupos[k]
        total = sum((g[1] or 0) for g in cels if g)
        if total < MIN_N:
            continue
        linha = ""
        positivas = 0
        for g in cels:
            if not g or g[0] is None:
                linha += f"{'—':>14s}"
            else:
                linha += f"{g[0]:>+8.2f}(n{g[1]:<3d})"
                if g[0] > 0:
                    positivas += 1
        print(f"{str(k)[:40]:<40s} {linha}   {positivas}/{sum(1 for g in cels if g and g[0] is not None)}")
    print("\n'sinais+' = em quantas janelas a expectância foi positiva. "
          "Consistência importa mais que a média — 6/6 é sinal, 3/6 é moeda.")


def main():
    caminho = sys.argv[1] if len(sys.argv) > 1 else "/tmp/backtest-linhas.json"
    with open(caminho) as f:
        dados = json.load(f)

    for barreira in ("alvo1", "alvo2"):
        linhas = dados[barreira]
        rotulo = ("alvo1 (1R — o que o produto MEDE)" if barreira == "alvo1"
                  else "alvo2 (projeção do setup — o que o produto PROMETE)")
        print(f"\n{'=' * 100}\nBARREIRA = {rotulo}\n{'=' * 100}")

        print("\n### Geral")
        g = stats(linhas)
        print(json.dumps(g, ensure_ascii=False))

        # --- a pergunta central: a confluência discrimina? ---
        dist = defaultdict(int)
        for l in linhas:
            dist[l["confluencia"]] += 1
        total = sum(dist.values())
        print(f"\n### Distribuição da confluência ({total} sinais)")
        for k in sorted(dist, reverse=True):
            print(f"  {k:>3}% : {dist[k]:>6d}  ({100.0*dist[k]/total:5.1f}%)")

        por_conf = defaultdict(list)
        for l in linhas:
            por_conf[l["confluencia"]].append(l)
        tabela("Expectância por confluência", {k: stats(v) for k, v in por_conf.items()},
               ordena_por_n=False)

        por_setup = defaultdict(list)
        for l in linhas:
            por_setup[l["setup"]].append(l)
        tabela("Por setup", {k: stats(v) for k, v in por_setup.items()})
        print(f"\nConfigurações testadas nesta tabela: {len(por_setup)}. "
              f"Com {len(por_setup)} tentativas, |t| ≈ 2 deixa de ser evidência — "
              f"o limiar prudente sobe para |t| ≳ {round(math.sqrt(2*math.log(max(len(por_setup),2))),1)}.")

        por_lado = defaultdict(list)
        for l in linhas:
            por_lado[l["lado"]].append(l)
        tabela("Por lado", {k: stats(v) for k, v in por_lado.items()})

        por_reg = defaultdict(list)
        for l in linhas:
            por_reg[l["regime"] or "—"].append(l)
        tabela("Por regime", {k: stats(v) for k, v in por_reg.items()})

        por_sr = defaultdict(list)
        for l in linhas:
            por_sr[f"{l['setup']} · {l['regime']}"].append(l)
        tabela("Por setup × regime (tese do ADR-009)", {k: stats(v) for k, v in por_sr.items()})

        if barreira == "alvo1":
            walk_forward(linhas, lambda l: l["setup"])
            walk_forward(linhas, lambda l: f"conf {l['confluencia']}%", janelas=6)


if __name__ == "__main__":
    main()
