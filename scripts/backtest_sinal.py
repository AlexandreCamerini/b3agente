#!/usr/bin/env python3
"""backtest_sinal.py — replay determinístico do motor de setups sobre histórico real.

Por que existe: o produto nunca mediu se o próprio sinal tem expectativa
positiva. `analysis_outcomes` só acumula dado forward (dezenas de observações em
meses) e nem grava `confluencia`, então a pergunta comercial central
("confluência alta acerta mais?") não tinha como ser respondida. Este harness
recomputa `detect_setups` + `plano_do_resultado` dia a dia sobre candles reais e
mede o desfecho das 10 barras seguintes.

O que ele NÃO é: não toca `server/app/`, não altera o motor, não usa LLM, não
consome orçamento da brapi (usa Yahoo, mesma fonte de backup/intraday do ADR-008)
e cacheia candles em disco para não refazer download.

Metodologia (ADR-015): a entrada é ancorada no GATILHO (`plano["entrada"]`),
nunca no close do dia da análise. Plano do tipo "a mercado" abre a barreira no
candle seguinte sem exigir toque — exigir toque jogaria o gap adverso para fora
do denominador, que é o viés otimista que o ADR-015 documenta.

Uso:
    python3 scripts/backtest_sinal.py                     # universo completo, 3 anos
    python3 scripts/backtest_sinal.py --anos 5 --tickers PETR4,VALE3
    python3 scripts/backtest_sinal.py --so-cache          # não baixa nada
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server"))

from app import indicators, signal_replay, yahoo  # noqa: E402
from app.scanner import DEFAULT_UNIVERSE  # noqa: E402

# ADR-017 (Decisão 2, "Reprodutibilidade"): a barreira tripla e o replay
# determinístico vivem em UM lugar só — server/app/signal_replay.py. Este
# script é um wrapper fino: reexporta os nomes que os scripts irmãos
# importam (backtest_placebo.py: CACHE_DIR/HORIZONTE/avaliar) e cuida só do
# que é dele — cache em disco e apresentação/CLI. Nenhuma segunda
# implementação da barreira tripla deve existir no repositório.
JANELA = signal_replay.JANELA
HORIZONTE = signal_replay.HORIZONTE
sinais_do_ticker = signal_replay.sinais_do_ticker
avaliar = signal_replay.avaliar
agregar = signal_replay.agregar
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".cache-backtest")


# --------------------------------------------------------------------------- #
# 1) Dados
# --------------------------------------------------------------------------- #

async def carregar(ticker: str, rng: str, so_cache: bool, intervalo: str = "1d") -> list:
    """Candles com cache em disco (o Yahoo aperta quem insiste). `intervalo`
    entra na chave do cache — diário e semanal não podem disputar a mesma
    entrada (mesma razão do ADR-001 para o cache de snapshot).

    A validação de granularidade (`yahoo.confere_granularidade`) roda aqui
    mesmo o CACHE EM DISCO já validado uma vez: `get_history` só valida o que
    vem da rede; um cache gravado antes do guard existir pode conter dado
    degradado."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{ticker}-{rng}-{intervalo}.json")
    legado = os.path.join(CACHE_DIR, f"{ticker}-{rng}.json")  # cache diário anterior
    if intervalo == "1d" and not os.path.exists(path) and os.path.exists(legado):
        path = legado
    if os.path.exists(path):
        with open(path) as f:
            cs = json.load(f)
        yahoo.confere_granularidade(cs, intervalo, ticker, rng)
        return cs
    if so_cache:
        return []
    hist = await yahoo.get_history(ticker, rng=rng, interval=intervalo)
    cs = hist.get("candles") or []
    yahoo.confere_granularidade(cs, intervalo, ticker, rng)  # antes de gravar cache
    with open(path, "w") as f:
        json.dump(cs, f)
    return cs


def _tab(titulo: str, grupos: dict, min_n: int = 30):
    print(f"\n### {titulo}")
    print(f"{'chave':<44s} {'n':>5s} {'acerto%':>8s} {'expR':>7s} {'PF':>6s} "
          f"{'stop':>5s} {'alvo':>5s} {'n/acion':>8s}")
    print("-" * 96)
    for k in sorted(grupos, key=lambda x: -(grupos[x].get("n") or 0)):
        s = grupos[k]
        if not s.get("n"):
            continue
        flag = "" if s["n"] >= min_n else "  (n baixo)"
        pf = s["profitFactor"]
        print(f"{str(k)[:44]:<44s} {s['n']:>5d} {s['acerto']:>8.1f} "
              f"{s['expectanciaR']:>7.3f} {(f'{pf:.2f}' if pf else '—'):>6s} "
              f"{s['stops']:>5d} {s['alvos']:>5d} {s['naoAcionados']:>8d}{flag}")


# --------------------------------------------------------------------------- #

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anos", type=float, default=3.0, help="anos de sinais avaliados")
    ap.add_argument("--tickers", default="", help="lista separada por vírgula")
    ap.add_argument("--rng", default="5y", help="range do Yahoo (warmup incluso)")
    ap.add_argument("--so-cache", action="store_true", help="não baixa nada")
    ap.add_argument("--saida", default="", help="grava as linhas cruas em JSON")
    ap.add_argument("--horizonte", type=int, default=HORIZONTE,
                    help="barras de avaliação (default 10 = o do produto)")
    ap.add_argument("--intervalo", default="1d", choices=("1d", "1wk"),
                    help="1wk roda o motor em barra SEMANAL (muda a detecção, não só a avaliação)")
    ap.add_argument("--janela", type=int, default=JANELA, help="barras da janela do motor")
    args = ap.parse_args()

    uni = [t.strip().upper() for t in args.tickers.split(",") if t.strip()] or DEFAULT_UNIVERSE
    por_ano = 252 if args.intervalo == "1d" else 52
    dias = int(args.anos * por_ano)
    unidade = "pregões" if args.intervalo == "1d" else "semanas"

    print(f"universo: {len(uni)} tickers · intervalo: {args.intervalo} · "
          f"janela do motor: {args.janela} barras · horizonte: {args.horizonte} {unidade} · "
          f"sinais das últimas ~{dias} barras")

    sem = asyncio.Semaphore(4)

    async def um(tk):
        async with sem:
            try:
                cs = await carregar(tk, args.rng, args.so_cache, args.intervalo)
            except Exception as e:  # noqa: BLE001 — ticker sem histórico não derruba a varredura
                print(f"  ! {tk}: {e}", file=sys.stderr)
                return tk, [], []
            sinais = sinais_do_ticker(tk, cs, dias, args.horizonte, args.janela)
            cs_ok = indicators.sanitize_candles(cs or [])
            return tk, sinais, cs_ok

    linhas1, linhas2 = [], []
    feitos = 0
    for fut in asyncio.as_completed([um(t) for t in uni]):
        tk, sinais, cs_ok = await fut
        feitos += 1
        for s in sinais:
            for campo, destino in (("alvo1", linhas1), ("alvo2", linhas2)):
                r = avaliar(s, cs_ok, campo, args.horizonte)
                if r["resultado"] is None:
                    continue
                destino.append({**s, **r})
        print(f"\r  {feitos}/{len(uni)} tickers · {len(linhas1)} sinais", end="", file=sys.stderr)
    print(file=sys.stderr)

    if not linhas1:
        print("\nNenhum sinal avaliável. Sem cache local, rode sem --so-cache.")
        return

    for nome, linhas in (("BARREIRA = alvo1 (1R — o que o produto MEDE hoje)", linhas1),
                         ("BARREIRA = alvo2 (projeção do setup — o que o produto PROMETE)", linhas2)):
        print(f"\n{'=' * 96}\n{nome}\n{'=' * 96}")
        print("\n### Geral")
        print(json.dumps(agregar(linhas), ensure_ascii=False, indent=2))

        por_conf = defaultdict(list)
        for l in linhas:
            por_conf[l["confluencia"]].append(l)
        _tab("Por confluência", {k: agregar(v) for k, v in por_conf.items()})

        por_setup = defaultdict(list)
        for l in linhas:
            por_setup[l["setup"]].append(l)
        _tab("Por setup", {k: agregar(v) for k, v in por_setup.items()})

        por_lado = defaultdict(list)
        for l in linhas:
            por_lado[l["lado"]].append(l)
        _tab("Por lado", {k: agregar(v) for k, v in por_lado.items()})

        por_reg = defaultdict(list)
        for l in linhas:
            por_reg[l["regime"] or "—"].append(l)
        _tab("Por regime", {k: agregar(v) for k, v in por_reg.items()})

        conf100 = defaultdict(list)
        for l in linhas:
            if l["confluencia"] == 100:
                conf100[f"{l['setup']} · {l['lado']}"].append(l)
        _tab("Confluência 100% por setup+lado (a observação do dono do produto)",
             {k: agregar(v) for k, v in conf100.items()})

    if args.saida:
        with open(args.saida, "w") as f:
            json.dump({"alvo1": linhas1, "alvo2": linhas2}, f, ensure_ascii=False)
        print(f"\nlinhas cruas em {args.saida}")


if __name__ == "__main__":
    asyncio.run(main())
