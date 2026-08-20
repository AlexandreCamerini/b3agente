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

from app import indicators, regime, setups, yahoo  # noqa: E402
from app.scanner import DEFAULT_UNIVERSE  # noqa: E402

JANELA = 252          # candles_mod.resolve_keep("1y") — a janela que o Radar usa
HORIZONTE = 10        # analysis_outcomes.HORIZON_PREGOES
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".cache-backtest")


# --------------------------------------------------------------------------- #
# 1) Dados
# --------------------------------------------------------------------------- #

async def carregar(ticker: str, rng: str, so_cache: bool) -> list:
    """Candles diários, com cache em disco (o Yahoo aperta quem insiste)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{ticker}-{rng}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    if so_cache:
        return []
    hist = await yahoo.get_history(ticker, rng=rng, interval="1d")
    cs = hist.get("candles") or []
    with open(path, "w") as f:
        json.dump(cs, f)
    return cs


# --------------------------------------------------------------------------- #
# 2) Replay do motor
# --------------------------------------------------------------------------- #

def _summary_em(ind: dict, closes: list, t: int) -> dict:
    """Mini-summary no dia t. Os indicadores são causais e alinhados ao array de
    candles, então o valor no índice t é exatamente o que a produção teria
    calculado naquele dia — não há vazamento de futuro."""
    def v(nome):
        arr = ind.get(nome) or []
        return arr[t] if t < len(arr) else None
    return {"close": closes[t], "sma200": v("sma200"), "sma50": v("sma50"),
            "adx14": v("adx14"), "diPlus": v("diPlus"), "diMinus": v("diMinus")}


def sinais_do_ticker(ticker: str, cs: list, dias: int) -> list:
    """Roda o motor dia a dia e devolve os planos acionáveis (COMPRAR/VENDER)."""
    cs = indicators.sanitize_candles(cs or [])
    if len(cs) < JANELA + HORIZONTE + 10:
        return []
    full = indicators.compute(cs)
    ind, closes = full["indicators"], [c["close"] for c in cs]

    # Só avalia dias que têm janela cheia atrás E horizonte cheio à frente.
    t0 = max(JANELA, len(cs) - HORIZONTE - dias)
    t1 = len(cs) - HORIZONTE - 1

    out = []
    for t in range(t0, t1 + 1):
        ini = max(0, t + 1 - JANELA)
        janela = cs[ini:t + 1]
        ind_slice = {k: arr[ini:t + 1] for k, arr in ind.items()}
        sres = setups.detect_setups(janela, ind_slice)
        plano = setups.plano_do_resultado(sres, close=cs[t]["close"])
        if plano.get("decisao") not in (setups.DECISAO_COMPRAR, setups.DECISAO_VENDER):
            continue
        entrada, stop = plano.get("entrada"), plano.get("stop")
        if entrada is None or stop is None or entrada == stop:
            continue
        reg = regime.classificar({"close": cs[t]["close"],
                                  "summary": _summary_em(ind, closes, t),
                                  "candlesAvailable": t + 1})
        # A confluência que importa é a do setup QUE VIROU PLANO — não a global
        # de `sres["confluencia"]` (que é a do melhor setup, podendo ser um
        # neutro ou do lado oposto ao plano, ver plano_do_resultado).
        nome = plano.get("setup")
        conf = next((s.get("confluencia") for s in (sres.get("setups") or [])
                     if s.get("nome") == nome), sres.get("confluencia"))
        out.append({
            "ticker": ticker, "data": cs[t]["date"], "t": t,
            "setup": nome, "lado": plano.get("lado"),
            "confluencia": conf,
            "tipo": plano.get("tipo"), "entrada": entrada, "stop": stop,
            "alvo1": plano.get("alvo1"), "alvo2": plano.get("alvo2"),
            "rr2": plano.get("rr2"), "regime": reg.get("regime"),
        })
    return out


# --------------------------------------------------------------------------- #
# 3) Avaliação forward (barreira tripla ancorada no gatilho — ADR-015)
# --------------------------------------------------------------------------- #

def avaliar(sinal: dict, cs: list, alvo_campo: str) -> dict:
    """Desfecho das próximas HORIZONTE barras. `resultado` ∈
    {alvo, stop, sem_gatilho, expirou}. `r` é o múltiplo do risco do PLANO."""
    alvo = sinal.get(alvo_campo)
    if alvo is None:
        return {"resultado": None, "r": None}
    entrada, stop = sinal["entrada"], sinal["stop"]
    compra = sinal["lado"] == "alta"
    risco = abs(entrada - stop)
    if risco <= 0:
        return {"resultado": None, "r": None}

    janela = cs[sinal["t"] + 1: sinal["t"] + 1 + HORIZONTE]
    if len(janela) < HORIZONTE:
        return {"resultado": None, "r": None}

    # Entrada a mercado: o gatilho já rompeu, a entrada é imediata — a barreira
    # abre na primeira barra, sem exigir toque (ADR-015 / ADR15-02).
    a_mercado = str(sinal.get("tipo") or "").startswith("a mercado")
    if a_mercado:
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
            return {"resultado": "sem_gatilho", "r": None}

    for c in janela[i0:]:
        hi, lo = c.get("high"), c.get("low")
        if hi is None or lo is None:
            continue
        # Empate intrabar resolve a favor do stop (cenário conservador — mesma
        # convenção de analysis_outcomes._avaliar_entry e agent.py).
        bateu_stop = lo <= stop if compra else hi >= stop
        bateu_alvo = hi >= alvo if compra else lo <= alvo
        if bateu_stop:
            return {"resultado": "stop", "r": -1.0}
        if bateu_alvo:
            return {"resultado": "alvo", "r": round(abs(alvo - entrada) / risco, 3)}

    fim = janela[-1].get("close")
    if fim is None:
        return {"resultado": None, "r": None}
    ganho = (fim - entrada) if compra else (entrada - fim)
    return {"resultado": "expirou", "r": round(ganho / risco, 3)}


# --------------------------------------------------------------------------- #
# 4) Estatística
# --------------------------------------------------------------------------- #

def agregar(linhas: list) -> dict:
    """Expectância em R e taxa de acerto. `sem_gatilho` fica FORA do
    denominador: o trade não existiu, contá-lo como perda inflaria a taxa de
    stop pelo mesmo viés que o ADR-015 corrige."""
    resolvidos = [l for l in linhas if l["resultado"] in ("alvo", "stop", "expirou")]
    n = len(resolvidos)
    if not n:
        return {"n": 0, "naoAcionados": sum(1 for l in linhas if l["resultado"] == "sem_gatilho")}
    rs = [l["r"] for l in resolvidos]
    ganhos = [r for r in rs if r > 0]
    perdas = [-r for r in rs if r < 0]
    return {
        "n": n,
        "naoAcionados": sum(1 for l in linhas if l["resultado"] == "sem_gatilho"),
        "acerto": round(100.0 * len(ganhos) / n, 1),
        "expectanciaR": round(sum(rs) / n, 3),
        "somaR": round(sum(rs), 1),
        "profitFactor": (round(sum(ganhos) / sum(perdas), 2) if perdas else None),
        "stops": sum(1 for l in resolvidos if l["resultado"] == "stop"),
        "alvos": sum(1 for l in resolvidos if l["resultado"] == "alvo"),
        "expirou": sum(1 for l in resolvidos if l["resultado"] == "expirou"),
    }


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
    args = ap.parse_args()

    uni = [t.strip().upper() for t in args.tickers.split(",") if t.strip()] or DEFAULT_UNIVERSE
    dias = int(args.anos * 252)

    print(f"universo: {len(uni)} tickers · janela do motor: {JANELA} barras · "
          f"horizonte: {HORIZONTE} pregões · sinais dos últimos ~{dias} pregões")

    sem = asyncio.Semaphore(4)

    async def um(tk):
        async with sem:
            try:
                cs = await carregar(tk, args.rng, args.so_cache)
            except Exception as e:  # noqa: BLE001 — ticker sem histórico não derruba a varredura
                print(f"  ! {tk}: {e}", file=sys.stderr)
                return tk, [], []
            sinais = sinais_do_ticker(tk, cs, dias)
            cs_ok = indicators.sanitize_candles(cs or [])
            return tk, sinais, cs_ok

    linhas1, linhas2 = [], []
    feitos = 0
    for fut in asyncio.as_completed([um(t) for t in uni]):
        tk, sinais, cs_ok = await fut
        feitos += 1
        for s in sinais:
            for campo, destino in (("alvo1", linhas1), ("alvo2", linhas2)):
                r = avaliar(s, cs_ok, campo)
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
