#!/usr/bin/env python3
"""backtest_operador.py — o Modo Operador de verdade, não o plano do Estudo.

Lacuna que este script fecha: o ADR-016 mediu stop fixo + alvo1 fixo (1R). Isso é
a mecânica do Modo ESTUDO. O Modo Operador tem trailing stop em 3 modos
(`agent.py:366-428`, ATR 2× por padrão, stop só sobe) e alvo dinâmico com até 2
extensões de 1,5× ATR (`agent.py:444-478`). Nada disso entrou na medição
anterior, então "o motor perde dinheiro" estava medido sobre a máquina errada.

Também testa a proposta que saiu do diagnóstico: com `alvo1 = entrada ± risco`
(`setups.py:623`), o alvo é exatamente 1R, e numa barreira simétrica a
expectância é ≈ 2p − 1. Com 44,8% de acerto isso dá −0,104R por aritmética,
independente da qualidade do sinal. A saída é assimetria: cortar em 1R e deixar
o vencedor correr.

Quatro braços, mesmos sinais:
  A  fixo            stop fixo + alvo1 (1R)            — o que o ADR-016 mediu
  B  trailing        trailing ATR 2×, sem alvo fixo    — deixa correr
  C  operador        trailing + alvo dinâmico          — a config real do Operador
  D  parcial+trail   50% em 1R, resto no trailing      — a proposta

Ordem de checagem por barra, espelhando `agent.py:804-836`: trailing primeiro,
depois stop (contra `low`, empate a favor do stop), depois alvo (contra `high`).

Uso: python3 scripts/backtest_operador.py /tmp/linhas-h10.json
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

ATR_MULT_TRAILING = 2.0    # agent.ATR_MULT_DEFAULT
ALVO_ATR_MULT = 1.5        # agent.ALVO_ATR_MULT
MAX_EXTENSOES = 2          # agent.MAX_ALVO_EXTENSOES
RR_MINIMO = 1.5            # agent.RR_MINIMO
TETO_BARRAS = 60           # trailing precisa de espaço; o Operador não tem prazo fixo


def _serie(ticker: str, rng: str, intervalo: str):
    for nome in (f"{ticker}-{rng}-{intervalo}.json", f"{ticker}-{rng}.json"):
        p = os.path.join(CACHE_DIR, nome)
        if os.path.exists(p):
            with open(p) as f:
                cs = indicators.sanitize_candles(json.load(f))
            return cs, indicators.compute(cs)["indicators"].get("atr14") or []
    return [], []


def _rr(entrada, stop, alvo, compra):
    risco = (entrada - stop) if compra else (stop - entrada)
    if risco <= 0:
        return None
    ganho = (alvo - entrada) if compra else (entrada - alvo)
    return ganho / risco


def simular(sinal, cs, atr, braco: str):
    """Devolve o R-múltiplo da operação, ou None se o gatilho nunca foi tocado."""
    entrada, stop0 = sinal["entrada"], sinal["stop"]
    compra = sinal["lado"] == "alta"
    risco = abs(entrada - stop0)
    if risco <= 0:
        return None
    alvo1 = sinal.get("alvo1")
    t = sinal["t"]
    janela = cs[t + 1: t + 1 + TETO_BARRAS]
    if len(janela) < 5:
        return None

    # Abertura da barreira: plano "a mercado" entra já; rompimento espera o toque.
    if str(sinal.get("tipo") or "").startswith("a mercado"):
        i0 = 0
    else:
        i0 = None
        for i, c in enumerate(janela):
            hi, lo = c.get("high"), c.get("low")
            if hi is None or lo is None:
                continue
            if (compra and hi >= entrada) or (not compra and lo <= entrada):
                i0 = i
                break
        if i0 is None:
            return None

    stop = stop0
    alvo = alvo1
    extensoes = 0
    parcial_feita = False
    r_acum = 0.0
    peso_restante = 1.0

    for k in range(i0, len(janela)):
        c = janela[k]
        hi, lo, cl = c.get("high"), c.get("low"), c.get("close")
        if hi is None or lo is None:
            continue
        a = atr[t + 1 + k] if t + 1 + k < len(atr) else None

        # 1) Trailing (agent.py:814-820) — só aperta, nunca afrouxa.
        if braco in ("trailing", "operador", "parcial") and a:
            base = cl if cl is not None else (hi if compra else lo)
            novo = (base - ATR_MULT_TRAILING * a) if compra else (base + ATR_MULT_TRAILING * a)
            if compra and novo > stop:
                stop = novo
            elif not compra and novo < stop:
                stop = novo

        # 2) Stop (empate intrabar a favor do stop, como no módulo)
        bateu_stop = (lo <= stop) if compra else (hi >= stop)
        if bateu_stop:
            r = ((stop - entrada) if compra else (entrada - stop)) / risco
            return r_acum + peso_restante * r

        # 3) Alvo
        if alvo is not None:
            bateu_alvo = (hi >= alvo) if compra else (lo <= alvo)
            if bateu_alvo:
                if braco == "fixo":
                    return ((alvo - entrada) if compra else (entrada - alvo)) / risco
                if braco == "parcial" and not parcial_feita:
                    # Realiza metade em 1R e solta o resto no trailing.
                    r = ((alvo - entrada) if compra else (entrada - alvo)) / risco
                    r_acum += 0.5 * r
                    peso_restante = 0.5
                    parcial_feita = True
                    alvo = None
                elif braco == "operador" and extensoes < MAX_EXTENSOES and a:
                    novo_alvo = (alvo + ALVO_ATR_MULT * a) if compra else (alvo - ALVO_ATR_MULT * a)
                    rr = _rr(entrada, stop, novo_alvo, compra)
                    if rr is not None and rr >= RR_MINIMO:
                        alvo = novo_alvo
                        extensoes += 1
                    else:
                        return ((alvo - entrada) if compra else (entrada - alvo)) / risco
                elif braco == "operador":
                    return ((alvo - entrada) if compra else (entrada - alvo)) / risco
                else:  # trailing puro não tem alvo
                    alvo = None

    fim = janela[-1].get("close")
    if fim is None:
        return None
    r = ((fim - entrada) if compra else (entrada - fim)) / risco
    return r_acum + peso_restante * r


def stats(vals):
    n = len(vals)
    if n < 2:
        return {"n": n}
    m = sum(vals) / n
    var = sum((v - m) ** 2 for v in vals) / (n - 1)
    se = math.sqrt(var / n)
    ganhos = [v for v in vals if v > 0]
    perdas = [-v for v in vals if v < 0]
    return {"n": n, "expR": m, "t": m / se if se else 0.0,
            "acerto": 100.0 * len(ganhos) / n,
            "pf": (sum(ganhos) / sum(perdas)) if perdas else None,
            "melhor": max(vals), "medioGanho": (sum(ganhos) / len(ganhos)) if ganhos else 0.0,
            "medioPerda": (-sum(perdas) / len(perdas)) if perdas else 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("linhas")
    ap.add_argument("--rng", default="5y")
    ap.add_argument("--intervalo", default="1d")
    args = ap.parse_args()

    with open(args.linhas) as f:
        sinais = json.load(f)["alvo1"]

    bracos = ("fixo", "trailing", "operador", "parcial")
    res = {b: [] for b in bracos}
    por_setup = {b: defaultdict(list) for b in bracos}
    cache = {}

    for s in sinais:
        tk = s["ticker"]
        if tk not in cache:
            cache[tk] = _serie(tk, args.rng, args.intervalo)
        cs, atr = cache[tk]
        if not cs or s["t"] + TETO_BARRAS + 1 >= len(cs):
            continue
        for b in bracos:
            r = simular(s, cs, atr, b)
            if r is not None:
                res[b].append(r)
                por_setup[b][s["setup"]].append(r)

    print("=" * 96)
    print(f"MODO OPERADOR — mecânica de saída real  ({args.linhas}, teto {TETO_BARRAS} barras)")
    print("=" * 96)
    rot = {"fixo": "A · fixo (stop + alvo 1R) — o que o ADR-016 mediu",
           "trailing": "B · trailing ATR 2×, sem alvo",
           "operador": "C · trailing + alvo dinâmico (config do Operador)",
           "parcial": "D · 50% em 1R + trailing no resto (a proposta)"}
    print(f"\n{'braço':<52s} {'n':>7s} {'expR':>8s} {'t':>7s} {'acerto%':>8s} "
          f"{'PF':>6s} {'ganho méd':>10s} {'perda méd':>10s}")
    print("-" * 112)
    for b in bracos:
        s = stats(res[b])
        if not s.get("n"):
            continue
        pf = f"{s['pf']:.2f}" if s["pf"] else "—"
        print(f"{rot[b]:<52s} {s['n']:>7d} {s['expR']:>+8.3f} {s['t']:>+7.2f} "
              f"{s['acerto']:>8.1f} {pf:>6s} {s['medioGanho']:>+10.2f}R {s['medioPerda']:>+9.2f}R")

    print(f"\n### Por setup — expectância em R por braço")
    print(f"{'setup':<42s} " + "".join(f"{rot[b][:1]:>12s}" for b in bracos))
    print("-" * 92)
    nomes = sorted(por_setup["fixo"], key=lambda k: -len(por_setup["fixo"][k]))
    for nome in nomes:
        if len(por_setup["fixo"][nome]) < 100:
            continue
        linha = ""
        for b in bracos:
            v = por_setup[b].get(nome) or []
            linha += f"{(sum(v)/len(v) if v else 0):>+12.3f}"
        print(f"{str(nome)[:42]:<42s}{linha}")

    print("\nLeitura: se B/C/D viram a expectância para positivo, o problema era a")
    print("geometria de saída (alvo travado em 1R), não o sinal. Se seguem negativos,")
    print("nem a máquina profissional de saída salva um gatilho sem informação.")


if __name__ == "__main__":
    main()
