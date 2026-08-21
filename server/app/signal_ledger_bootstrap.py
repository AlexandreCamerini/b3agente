"""server/app/signal_ledger_bootstrap.py — carga histórica única do ledger de
sinais resolvidos (ADR-017, Bloco 1, Decisão 2: "um ledger, duas leituras").

(a) Este comando é MANUAL e PESADO: ~126 mil sinais (15 anos × 74 tickers),
74 requisições ao Yahoo, minutos de CPU rodando o replay determinístico
barra a barra. Por isso NÃO está pendurado no `scheduler_loop`
(`server/app/agent.py`) — decisão explícita do ADR-017 (Decisão 2): essa
carga não pode competir com heartbeat e kill-switch no mesmo laço asyncio
único. O incidente do kill-switch (execução parada por 2,5 dias sem
ninguém notar porque o heartbeat mascarava o problema) é o precedente
concreto do que acontece quando esse laço trava — este módulo roda como
processo dedicado (`python -m app.signal_ledger_bootstrap`), nunca dentro
do ciclo do agente.

(b) Vive dentro de `server/app/`, não num diretório de scripts avulsos: o
Railway publica com `rootDirectory=/server`, então qualquer coisa fora
desse diretório simplesmente não existe dentro do container de produção.
Um bootstrap fora daqui rodaria só na máquina do desenvolvedor e seria
inexecutável em produção. Por isso este módulo é um `__main__` dentro do
pacote da aplicação, invocável via `railway ssh` com
`/opt/venv/bin/python3 -m app.signal_ledger_bootstrap` (ver
`docs/OPERACAO-ledger-de-sinais.md` para o runbook completo).

(c) É REEXECUTÁVEL: a restrição `UNIQUE(ticker, setup, lado, data_sinal)` do
ledger (schema em `server/app/db.py`) torna a recarga idempotente — rodar
este comando duas vezes com os mesmos candles grava N linhas na primeira
execução e 0 na segunda. A flag `--reset` existe para os dois únicos casos
em que apagar o histórico medido faz sentido: disaster recovery (banco
perdido/recriado) ou mudança de família de setups (o motor passa a medir
outra coisa e o histórico anterior deixa de responder à mesma pergunta).
`--reset` nunca é o comportamento default — sem a flag, a carga é aditiva.

(d) Usa a MESMA `signal_replay.replay()` que a manutenção diária (hook
incremental) também vai usar — é isso que garante que este comando
reproduz o número EXATO que a produção exibe (ADR-017, "Reprodutibilidade").
Este módulo não reimplementa nenhuma parte do replay determinístico nem da
avaliação de desfecho (alvo/stop/expira): só orquestra busca de candles,
grava no ledger e recalcula as agregações.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime

from . import db, scanner, signal_ledger, signal_replay, yahoo

# --------------------------------------------------------------------------- #
# 1) Dados — sem cache em disco (container efêmero do Railway)
# --------------------------------------------------------------------------- #


async def carregar_candles(ticker: str, rng: str) -> list:
    """Busca candles diários direto do Yahoo. Sem cache em disco: o container
    do Railway não tem um diretório de cache persistente e o disco é efêmero
    (qualquer cache local morreria no próximo deploy de qualquer forma). O
    guard de granularidade degradada já roda DENTRO de `yahoo.get_history`
    (`yahoo.confere_granularidade`, promovido no Plano 01 desta fase) — esta
    função não precisa, e não deve, revalidar nada por conta própria."""
    hist = await yahoo.get_history(ticker, rng=rng, interval="1d")
    return hist.get("candles") or []


# --------------------------------------------------------------------------- #
# 2) Carga por ticker — replay + gravação no ledger
# --------------------------------------------------------------------------- #


def bootstrap_ticker(conn, ticker: str, candles: list, dias: int) -> tuple:
    """Roda o replay determinístico do motor (`signal_replay.replay` — a
    MESMA função que a manutenção diária vai usar) para UM ticker e grava o
    resultado no ledger. Devolve `(linhas produzidas, linhas NOVAS
    gravadas)`. Grava por ticker, sem acumular os ~126 mil sinais totais em
    memória de uma vez — o container do Railway é pequeno e este comando
    varre o universo inteiro numa única execução."""
    linhas = signal_replay.replay(ticker, candles, dias)
    novas = signal_ledger.registrar_linhas(conn, linhas)
    return len(linhas), novas


# --------------------------------------------------------------------------- #
# 3) Orquestração — semáforo de concorrência + progresso em stderr
# --------------------------------------------------------------------------- #


async def executar(conn, tickers: list, anos: float, rng: str,
                    concorrencia: int = 4, dry_run: bool = False) -> dict:
    """Varre `tickers`: busca candles (respeitando `concorrencia`
    requisições simultâneas ao Yahoo — mesmo valor validado nas medições do
    ADR-016 para `scripts/backtest_sinal.py`) e grava no ledger via
    `bootstrap_ticker`. Ticker cujo fetch falha (sem histórico, granularidade
    degradada) entra em `erros` e NÃO derruba a varredura dos demais.

    Em `dry_run=True`, calcula o replay mas não grava nada — o resumo
    reporta quantas linhas SERIAM gravadas, sem tocar o ledger.

    Devolve `{"tickers": n, "linhas": n, "novas": n, "erros": [...]}`."""
    dias = int(anos * 252)
    sem = asyncio.Semaphore(concorrencia)
    total = len(tickers)
    resumo = {"tickers": total, "linhas": 0, "novas": 0, "erros": []}

    async def um(tk: str):
        async with sem:
            try:
                candles = await carregar_candles(tk, rng)
            except Exception as e:  # noqa: BLE001 — ticker sem histórico não derruba a varredura
                return tk, None, None, str(e)
            if dry_run:
                linhas = signal_replay.replay(tk, candles, dias)
                return tk, len(linhas), 0, None
            n, novas = bootstrap_ticker(conn, tk, candles, dias)
            return tk, n, novas, None

    feitos = 0
    for fut in asyncio.as_completed([um(tk) for tk in tickers]):
        tk, n, novas, erro = await fut
        feitos += 1
        if erro is not None:
            resumo["erros"].append({"ticker": tk, "erro": erro})
        else:
            resumo["linhas"] += n
            resumo["novas"] += novas
        print(f"\r  {feitos}/{total} tickers · {resumo['linhas']} sinais",
              end="", file=sys.stderr)
    print(file=sys.stderr)
    return resumo


# --------------------------------------------------------------------------- #
# 4) CLI
# --------------------------------------------------------------------------- #


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Bootstrap do ledger de sinais resolvidos (ADR-017, Bloco 1). "
                     "Comando MANUAL e PESADO — ver docs/OPERACAO-ledger-de-sinais.md.")
    ap.add_argument("--anos", type=float, default=15.0, help="anos de sinais avaliados")
    ap.add_argument("--rng", default="15y", help="range do Yahoo (warmup incluso)")
    ap.add_argument("--tickers", default="",
                    help="lista separada por vírgula; vazio = scanner.get_universe()")
    ap.add_argument("--concorrencia", type=int, default=4,
                    help="requisições simultâneas ao Yahoo")
    ap.add_argument("--reset", action="store_true",
                    help="apaga o ledger inteiro antes de carregar (disaster recovery / "
                         "mudança de família de setup)")
    ap.add_argument("--dry-run", action="store_true",
                    help="calcula e reporta o resumo sem gravar nenhuma linha")
    ap.add_argument("--db", default="",
                    help="caminho do banco; vazio = db.default_db_path() (respeita B3_DB_PATH)")
    args = ap.parse_args()

    tickers = ([t.strip().upper() for t in args.tickers.split(",") if t.strip()]
               or scanner.get_universe())
    conn = db.connect(args.db or None)

    if args.reset:
        apagadas = signal_ledger.apagar_tudo(conn)
        print(f"--reset: {apagadas} linha(s) apagada(s) do ledger antes da carga.")

    modo = " · DRY-RUN (nada será gravado)" if args.dry_run else ""
    print(f"universo: {len(tickers)} tickers · anos: {args.anos} · rng: {args.rng} · "
          f"concorrência: {args.concorrencia}{modo}")

    resumo = asyncio.run(
        executar(conn, tickers, args.anos, args.rng, args.concorrencia, args.dry_run)
    )

    print(f"\ntickers processados: {resumo['tickers']} · sinais avaliados: {resumo['linhas']} · "
          f"novas linhas gravadas: {resumo['novas']} · erros: {len(resumo['erros'])}")
    for e in resumo["erros"]:
        print(f"  ! {e['ticker']}: {e['erro']}")

    if args.dry_run:
        print("\nDRY-RUN: nenhuma linha foi gravada; total do ledger permanece inalterado.")
        return

    ano_anterior = datetime.now().year - 1
    cumulativo = signal_ledger.agregar_cumulativo(conn)
    janela = signal_ledger.agregar_janela(conn, ano_anterior)

    por_setup_janela = janela.get("porSetup") or {}
    elegiveis = sum(1 for s in por_setup_janela.values() if s.get("elegivel"))
    insuficientes = sum(1 for s in por_setup_janela.values() if s.get("insuficiente"))

    print("\n=== Resumo final ===")
    print(f"total no ledger: {signal_ledger.contar(conn)}")
    print(f"setups elegíveis (janela {ano_anterior}, n>={signal_ledger.MIN_N_JANELA}): {elegiveis}")
    print(f"setups com amostra insuficiente (janela {ano_anterior}): {insuficientes}")
    print(f"medidoAte: {cumulativo.get('medidoAte')}")


if __name__ == "__main__":
    main()
