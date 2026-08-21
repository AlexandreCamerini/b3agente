"""server/app/signal_ledger_job.py — manutenção diária do ledger de sinais
(ADR-017, Bloco 1, Decisão 2: "Manutenção diária").

O bootstrap (Plano 03) é uma FOTO: roda uma vez, fora do scheduler_loop, e
para de evoluir no dia em que rodou. Sem este hook a evidência do ledger
congela naquele dia enquanto o mercado segue produzindo sinais novos, e o
peso por desempenho histórico que `regime.ranquear()` consome passaria a
pesar por um passado cada vez mais velho.

Por que INCREMENTAL: refazer os 15 anos todo dia seria o bootstrap
disfarçado de cron — caro (74 tickers × 15 anos de replay) e desnecessário
(o cursor já sabe onde parou). O cursor é DERIVADO do próprio ledger
(`signal_ledger.data_sinal_maxima`), não uma chave kv paralela: assim ele
nunca diverge do dado, sobrevive a um `--reset` do bootstrap e não precisa
de reconciliação.

Por que lê do `candle_cache` em vez de buscar (ADR-008): o orçamento de
brapi é de 15k requisições/mês para o app INTEIRO. O Radar diário já busca
os candles de todo o universo minutos antes deste hook rodar — reusar via
`candle_cache.peek()` custa ZERO requisição extra.

Decisão de desenho mais importante deste módulo: o ledger é WRITE-ON-
RESOLUTION. `signal_replay.sinais_do_ticker` só avalia barras que têm
horizonte cheio À FRENTE (`t1 = len(cs) - horizonte - 1`), então todo sinal
já nasce resolvido e o cursor anda `horizonte` barras atrás da última barra
fechada. Não existe linha "pendente" para varrer depois nem estado parcial
para reconciliar — é o que torna este job idempotente e barato. O campo
`status` do ledger distingue `resolvido` de `sem_gatilho`, nunca "pendente
vs. resolvido".
"""
from __future__ import annotations

from . import candle_cache, scanner, signal_ledger, signal_replay

# Cobre uma parada longa do job (fim de semana prolongado, incidente, deploy
# quebrado por alguns dias) sem virar uma recarga completa dos 15 anos.
DIAS_RECUPERACAO = 60

# A UNIQUE(ticker, setup, lado, data_sinal) absorve a sobreposição — regravar
# um sinal já no ledger não infla `n`. A margem existe porque o horizonte de
# HORIZONTE barras faz o cursor andar atrás da última barra fechada, e uma
# emenda de feriado pode deslocar a contagem de "dias após a última data".
MARGEM_REPROCESSO = 3


def run_incremental(conn, universo: list | None = None) -> dict:
    """Avança o ledger com os candles que `candle_cache` já buscou.

    SÍNCRONA de propósito (o `await` fica em `maybe_run`) — roda em
    `asyncio.to_thread` porque é CPU-bound sobre o universo inteiro.

    Devolve {"tickers": int, "novas": int, "pulados": int, "erros": list}.
    """
    tickers = list(universo) if universo is not None else scanner.get_universe()
    min_candles = signal_replay.JANELA + signal_replay.HORIZONTE + 10
    novas = 0
    pulados = 0
    erros: list = []

    for ticker in tickers:
        cs = candle_cache.peek(ticker, "1d")
        if not cs or len(cs) < min_candles:
            pulados += 1
            continue

        # Cursor DERIVADO do próprio ledger — não uma chave kv paralela.
        ultima = signal_ledger.data_sinal_maxima(conn, ticker)
        if ultima is None:
            dias = DIAS_RECUPERACAO
        else:
            dias = sum(1 for c in cs if (c.get("date") or "") > ultima) + MARGEM_REPROCESSO
        if dias <= 0:
            pulados += 1
            continue

        # Achado do plan-checker (07-04, warning): o try/except cobre os
        # passos 4 E 5 juntos. Escopar só o replay deixaria uma falha de
        # registrar_linhas (ex.: IntegrityError fora do UNIQUE esperado)
        # propagar pra fora do laço por-ticker e abortar o dia inteiro pros
        # tickers restantes — contradiz "isola erro por ticker".
        try:
            linhas = signal_replay.replay(ticker, cs, dias)
            novas += signal_ledger.registrar_linhas(conn, linhas)
        except Exception as e:  # noqa: BLE001 — isola erro por ticker, nunca aborta o lote
            erros.append(f"{ticker}: {str(e)[:120]}")
            continue

    if novas > 0:
        signal_ledger.agregar_cumulativo(conn)
        # Invalida o cache em processo do provedor de histórico — sem isso o
        # dado novo levaria até TTL_HISTORICO_S (300s) para aparecer, e o
        # processo que grava é o mesmo que serve requests.
        signal_ledger.reset_cache()

    return {"tickers": len(tickers), "novas": novas, "pulados": pulados, "erros": erros}
