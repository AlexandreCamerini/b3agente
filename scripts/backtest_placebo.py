#!/usr/bin/env python3
"""backtest_placebo.py — controle nulo para o backtest do motor.

Pergunta que ele responde: a expectância negativa medida vem dos SETUPS ou da
GEOMETRIA da barreira (stop/alvo a X% do preço, horizonte de 10 pregões, empate
intrabar a favor do stop)? Sem esse controle não dá para distinguir "o setup
escolhe mal" de "qualquer entrada com essa geometria perde".

Método: para cada sinal real, gera um placebo no MESMO ticker, com a MESMA
distância relativa de stop e alvo e o MESMO lado, mas com a entrada num dia
sorteado do mesmo período. Se o placebo empatar com o real, o setup não está
adicionando informação — está só pagando o custo da geometria.

Uso: python3 scripts/backtest_placebo.py /tmp/backtest-linhas.json
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))
from app import indicators  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backtest_sinal import CACHE_DIR, HORIZONTE, avaliar  # noqa: E402

SEMENTE = 42  # reprodutível de propósito


def stats(linhas):
    res = [l for l in linhas if l["resultado"] in ("alvo", "stop", "expirou")]
    n = len(res)
    if n < 2:
        return {"n": n}
    rs = [l["r"] for l in res]
    m = sum(rs) / n
    var = sum((r - m) ** 2 for r in rs) / (n - 1)
    se = math.sqrt(var / n)
    return {"n": n, "expR": round(m, 3), "se": round(se, 4),
            "t": round(m / se, 2) if se else None,
            "acerto": round(100.0 * sum(1 for r in rs if r > 0) / n, 1),
            "naoAcionados": sum(1 for l in linhas if l["resultado"] == "sem_gatilho")}


def main():
    caminho = sys.argv[1] if len(sys.argv) > 1 else "/tmp/backtest-linhas.json"
    with open(caminho) as f:
        reais = json.load(f)["alvo1"]

    rnd = random.Random(SEMENTE)
    por_ticker = defaultdict(list)
    for l in reais:
        por_ticker[l["ticker"]].append(l)

    placebos = []
    for tk, sinais in por_ticker.items():
        path = os.path.join(CACHE_DIR, f"{tk}-5y.json")
        if not os.path.exists(path):
            continue
        with open(path) as f:
            cs = indicators.sanitize_candles(json.load(f))
        ts = [l["t"] for l in sinais]
        lo, hi = min(ts), max(ts)
        for l in sinais:
            # mesma geometria relativa, dia sorteado no mesmo intervalo
            t = rnd.randint(lo, hi)
            if t + HORIZONTE + 1 >= len(cs):
                continue
            preco = cs[t]["close"]
            if not preco:
                continue
            d_stop = (l["stop"] - l["entrada"]) / l["entrada"]
            d_alvo = (l["alvo1"] - l["entrada"]) / l["entrada"]
            placebos.append({
                "ticker": tk, "t": t, "data": cs[t]["date"], "lado": l["lado"],
                # entrada a mercado: o placebo não tem gatilho para esperar
                "tipo": "a mercado (placebo)",
                "entrada": preco, "stop": preco * (1 + d_stop),
                "alvo1": preco * (1 + d_alvo),
                "setup": "PLACEBO", "confluencia": None, "regime": None,
            })

    linhas = []
    por_tk = defaultdict(list)
    for p in placebos:
        por_tk[p["ticker"]].append(p)
    for tk, ps in por_tk.items():
        path = os.path.join(CACHE_DIR, f"{tk}-5y.json")
        with open(path) as f:
            cs = indicators.sanitize_candles(json.load(f))
        for p in ps:
            r = avaliar(p, cs, "alvo1")
            if r["resultado"] is not None:
                linhas.append({**p, **r})

    # O real precisa ser comparado no mesmo pé: placebo entra a mercado, então o
    # recorte justo do real é o subconjunto que também entrou (exclui sem_gatilho).
    s_real = stats(reais)
    s_plac = stats(linhas)

    print("=" * 76)
    print("CONTROLE NULO — o setup adiciona informação sobre a geometria?")
    print("=" * 76)
    print(f"\nMOTOR   : {json.dumps(s_real, ensure_ascii=False)}")
    print(f"PLACEBO : {json.dumps(s_plac, ensure_ascii=False)}")

    if s_real.get("n") and s_plac.get("n"):
        d = s_real["expR"] - s_plac["expR"]
        se = math.sqrt(s_real["se"] ** 2 + s_plac["se"] ** 2)
        t = d / se if se else 0.0
        print(f"\nDIFERENÇA (motor − placebo): {d:+.3f}R   t = {t:+.2f}")
        if abs(t) < 2:
            print("\nLeitura: a diferença não é estatisticamente distinguível de zero.")
            print("O setup não está adicionando informação sobre entrar num dia sorteado.")
            print("A expectância negativa é o CUSTO DA GEOMETRIA (barreira 1:1 com empate")
            print("intrabar resolvido a favor do stop), não um erro de escolha do setup.")
        elif t > 0:
            print("\nLeitura: o motor bate o placebo — o setup carrega informação real,")
            print("ainda que insuficiente para virar expectância positiva.")
        else:
            print("\nLeitura: o motor perde do placebo — o setup está ativamente")
            print("selecionando piores momentos que o acaso.")


if __name__ == "__main__":
    main()
