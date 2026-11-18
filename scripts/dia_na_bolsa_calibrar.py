#!/usr/bin/env python3
"""Calibração de frequência das regras de raridade do card "Seu dia na bolsa"
(Fase 51, plano 51-04, D-08).

Reaplica cada regra de `app.dia_na_bolsa_regras` aos últimos N pregões (padrão
252) com a série CORTADA no dia avaliado, conta disparos e imprime a frequência.
NUNCA altera constante: quem decide é o Alex, com a tabela na mão.

Fontes (nunca gasta o orçamento de requisições do provedor pago):
  sem --rede : L2 local (`candle_cache.peek`), banco em server/data/b3_agente.db
               (ou B3_DB_PATH já definido).
  com --rede : Yahoo direto (`yahoo.get_history`, range 2y) e `benchmark.serie_ibov`.

Uso:
  server/.venv/bin/python scripts/dia_na_bolsa_calibrar.py [--rede] [--dias 252]
                                                           [--tickers A,B,C]
Sem série suficiente a saída diz "calibração pendente" e o exit é 2.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(RAIZ, "server")
sys.path.insert(0, SERVER)

JANELA = 252
MIN_BARRAS = JANELA + 1   # 252 pregões anteriores + o dia avaliado
CARTEIRA_EXEMPLO = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "B3SA3", "ABEV3", "WEGE3"]
ALVO_MERCADO_SEMANA = 1.0   # ~1 por semana na UNIÃO das regras de mercado
PREGOES_SEMANA = 5


def _regras():
    from app import dia_na_bolsa_regras as R
    return R


def _corta(serie: list, dia: str) -> list:
    return [c for c in serie if c.get("date") and c["date"] <= dia]


def medir(ibov: list, universo: dict, dias: int = JANELA, carteira: list | None = None) -> dict:
    """Núcleo puro: séries injetadas -> contagens. `ibov` = candles com
    date/close; `universo` = ticker -> candles OHLC. Sem I/O."""
    R = _regras()
    carteira = [t for t in (carteira or CARTEIRA_EXEMPLO) if t in universo]
    datas = sorted({c["date"] for c in ibov if c.get("date")})
    avaliaveis = [d for i, d in enumerate(datas) if i + 1 >= MIN_BARRAS][-dias:]
    excluidos = sorted(t for t, s in universo.items() if len(s) < MIN_BARRAS)
    elegiveis = {t: s for t, s in universo.items() if len(s) >= MIN_BARRAS}

    disparos = defaultdict(int)
    dias_mercado = set()
    dias_pessoal = defaultdict(set)     # regra -> dias com >= 1 disparo na carteira
    dias_pessoal_uniao = set()

    for dia in avaliaveis:
        ib = _corta(ibov, dia)
        mercado = [("ibov_raro", R.regra_ibov_raro(ib, dia)),
                   ("ibov_extremo52", R.regra_extremo_52s(ib, dia, None))]
        amp = R.regra_amplitude({t: _corta(s, dia) for t, s in elegiveis.items()}, dia)
        mercado.append(("amplitude", amp))
        for nome, fato in mercado:
            if fato:
                disparos[nome] += 1
                dias_mercado.add(dia)
        for t in carteira:
            cs = _corta(elegiveis.get(t) or [], dia)
            if not cs:
                continue
            for nome, fato in (("atr_ativo", R.regra_atr_ativo(cs, dia, t)),
                               ("gap", R.regra_gap(cs, dia, t)),
                               ("extremo52_ativo", R.regra_extremo_52s(cs, dia, t))):
                if fato:
                    disparos[nome] += 1
                    dias_pessoal[nome].add(dia)
                    dias_pessoal_uniao.add(dia)

    n = len(avaliaveis)
    return {
        "dias_avaliados": n,
        "excluidos_sem_barras": excluidos,
        "n_universo": len(elegiveis),
        "carteira": carteira,
        "disparos": dict(disparos),
        "dias_mercado": len(dias_mercado),
        "dias_pessoal": {k: len(v) for k, v in dias_pessoal.items()},
        "dias_pessoal_uniao": len(dias_pessoal_uniao),
    }


def formatar(r: dict) -> str:
    R = _regras()
    n = r["dias_avaliados"]
    semanas = n / PREGOES_SEMANA if n else 0
    L = []
    L.append(f"Dias avaliados: {n} (~{semanas:.0f} semanas) | universo elegível: {r['n_universo']} ativos "
             f"| sem {MIN_BARRAS} barras: {len(r['excluidos_sem_barras'])}"
             + (f" ({', '.join(r['excluidos_sem_barras'])})" if r["excluidos_sem_barras"] else ""))
    L.append(f"Constantes: IBOV_PERCENTIL={R.IBOV_PERCENTIL} (travado) ATR_MULT_ATIVO={R.ATR_MULT_ATIVO} (travado) "
             f"AMPLITUDE_MIN={R.AMPLITUDE_MIN} AMPLITUDE_MIN_ATIVOS={R.AMPLITUDE_MIN_ATIVOS} GAP_MIN_ATR={R.GAP_MIN_ATR}")
    if r["n_universo"] < R.AMPLITUDE_MIN_ATIVOS:
        L.append(f"AVISO: universo ({r['n_universo']}) < AMPLITUDE_MIN_ATIVOS ({R.AMPLITUDE_MIN_ATIVOS}): "
                 "a regra de amplitude NUNCA dispara com este universo.")
    L.append("")
    L.append(f"{'regra':<18}{'escopo':<10}{'disparos 12m':>14}{'média/semana':>14}")
    for nome, escopo in (("ibov_raro", "mercado"), ("ibov_extremo52", "mercado"), ("amplitude", "mercado"),
                         ("atr_ativo", "carteira"), ("gap", "carteira"), ("extremo52_ativo", "carteira")):
        d = r["disparos"].get(nome, 0)
        L.append(f"{nome:<18}{escopo:<10}{d:>14}{(d / semanas if semanas else 0):>14.2f}")
    L.append("")
    um = r["dias_mercado"] / semanas if semanas else 0
    L.append(f"UNIÃO regras de mercado: {r['dias_mercado']} dias com fato ({um:.2f}/semana; alvo ~{ALVO_MERCADO_SEMANA:.0f}/semana)")
    pu = r["dias_pessoal_uniao"] / n if n else 0
    L.append(f"UNIÃO regras pessoais (carteira-exemplo de {len(r['carteira'])}): {r['dias_pessoal_uniao']} dias "
             f"= {pu:.0%} dos pregões (alvo: maioria dos dias)")
    for k, v in sorted(r["dias_pessoal"].items()):
        L.append(f"  {k}: {v} dias ({v / n:.0%})" if n else f"  {k}: {v}")
    L.append("")
    L.append("Nota: p95 isolado do IBOV dá ~5% dos pregões (~1 por mês); o alvo de ~1/semana só é "
             "atingível pela UNIÃO das regras de mercado. Se a união medida ficar abaixo, é achado para o "
             "Alex, não ajuste do script. Este script não altera constante alguma.")
    return "\n".join(L)


def _carregar_local(tickers: list) -> tuple:
    from app import candle_cache
    ibov = candle_cache.peek("^BVSP", "1d")
    universo = {t: candle_cache.peek(t, "1d") for t in tickers}
    return ibov, {t: s for t, s in universo.items() if s}


def _carregar_rede(tickers: list) -> tuple:
    from app import benchmark, yahoo

    async def tudo():
        ib = (await benchmark.serie_ibov("2y"))["candles"]
        uni = {}
        for t in tickers:
            try:
                uni[t] = (await yahoo.get_history(t, "2y", "1d"))["candles"]
            except Exception as e:  # noqa: BLE001 — ticker fora da medição, reportado
                print(f"[aviso] {t}: {type(e).__name__}: {e}", file=sys.stderr)
        return ib, uni
    return asyncio.run(tudo())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rede", action="store_true", help="busca no Yahoo (range 2y) em vez do L2 local")
    ap.add_argument("--dias", type=int, default=JANELA, help="pregões avaliados (padrão 252)")
    ap.add_argument("--tickers", default="", help="lista separada por vírgula (padrão: universo do Radar, scanner.DEFAULT_UNIVERSE — o mesmo do job)")
    a = ap.parse_args(argv)

    padrao_db = os.path.join(SERVER, "data", "b3_agente.db")
    if not a.rede and not os.environ.get("B3_DB_PATH") and os.path.exists(padrao_db):
        os.environ["B3_DB_PATH"] = padrao_db
    # Orquestrador da Fase 51: o padrão é o mesmo universo do job (dia_na_bolsa
    # usa scanner.DEFAULT_UNIVERSE como base da amplitude). O catálogo de 20
    # ativos ficava abaixo de AMPLITUDE_MIN_ATIVOS e media outra coisa.
    from app.scanner import DEFAULT_UNIVERSE
    tickers = [t.strip().upper() for t in a.tickers.split(",") if t.strip()] or list(DEFAULT_UNIVERSE)

    ibov, universo = (_carregar_rede if a.rede else _carregar_local)(tickers)
    if len(ibov or []) < MIN_BARRAS or not universo:
        print("calibração pendente: sem séries locais nem rede suficientes "
              f"(IBOV={len(ibov or [])} barras, ativos com dado={len(universo)}; precisa >= {MIN_BARRAS}). "
              "Rode fora do sandbox com: server/.venv/bin/python scripts/dia_na_bolsa_calibrar.py --rede")
        return 2
    print(formatar(medir(ibov, universo, a.dias)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
