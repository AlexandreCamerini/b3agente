# OPERAÇÃO — Ledger de Sinais Resolvidos (ADR-017, Bloco 1)

Runbook do comando manual que popula o ledger de sinais resolvidos —
`server/app/signal_ledger_bootstrap.py`. Este documento existe para que
alguém (inclusive o Alex, meses depois) rode o comando local ou em produção
sem precisar reabrir o ADR-017.

## 1. O que é

O ledger de sinais resolvidos guarda, por sinal (`ticker, setup, lado,
data_sinal`), o desfecho que o motor teria tido se tivesse operado aquele
sinal: `alvo`, `stop`, `expirou` ou `sem_gatilho`. A pergunta que ele responde
é **"este setup, medido sobre o histórico real, tem expectância positiva ou
negativa?"** — a mesma pergunta que `docs/adr/016-qualidade-do-sinal-do-motor-de-setups.md`
mediu manualmente com `scripts/backtest_sinal.py` (15 anos, 125.938 sinais).

Este ledger é **BACKTEST** (retrospectivo): replay determinístico do motor
sobre candles já fechados, sem execução real, sem viés de tempo real. Ele
NUNCA se soma nem se compara diretamente com `analysis_outcomes`, que é
**FORWARD** (prospectivo): o que a IA disse sobre um sinal ao vivo e o que
aconteceu depois. `docs/adr/015-assertividade-do-motor-de-recomendacao.md`
formaliza essa distinção — retrospectivo mede o MOTOR, prospectivo mede a
INTERPRETAÇÃO da IA sobre o motor. Misturar os dois números produziria uma
conclusão sem sentido (amostras com metodologias diferentes).

Duas leituras sobre o mesmo ledger, nunca duas implementações:

- **Cumulativa** (`signalLedger:cumulativo`): todo o histórico, atualizada a
  cada sinal resolvido. É o número exibido junto do setup (Bloco 3, fase
  futura).
- **Por janela anual fechada** (`signalLedger:janela`): só o ano-calendário
  anterior, congelada até a próxima virada de ano. É a elegibilidade que
  `regime.ranquear()` consome como peso no `radarScore` — walk-forward, sem
  vazamento de futuro (mesmo desenho validado em `scripts/backtest_pesos.py`,
  Spearman +0,523, t=+7,52 em 15 janelas).

## 2. Quando rodar o bootstrap

Só nestes três casos — não é recorrente e NÃO deve virar cron:

1. **Primeira instalação da fase** — o ledger nasce vazio; sem bootstrap, a
   elegibilidade por janela anual (`n≥40`) levaria anos para acumular amostra
   suficiente só com a manutenção diária incremental.
2. **Disaster recovery** — banco perdido ou recriado (ex.: troca de volume no
   Railway). Repopula do zero.
3. **Mudança de família de setups** — `setups.SETUPS_APOSENTADOS` muda, ou um
   detector é criado/alterado de forma que o comportamento passado deixa de
   representar o comportamento atual. Nesse caso o ledger antigo mede outra
   coisa; rode com `--reset`.

A manutenção diária (hook incremental, `signal_ledger_job` — Plano 04 desta
fase) é automática e roda dentro do `scheduler_loop`; ela NÃO refaz o replay
histórico, só avança o cursor por ticker com candles novos desde a última
execução. Não confunda os dois: o bootstrap é a carga pesada e manual: a
manutenção diária é o incremento leve e automático.

## 3. Comando local (venv do repositório)

```bash
cd server
B3_DB_PATH=/caminho/para/o/banco.db \
  ./.venv/bin/python -m app.signal_ledger_bootstrap --anos 15 --rng 15y
```

`B3_DB_PATH` aponta para o banco que se quer popular — sem a variável, o
comando usa `db.default_db_path()` (`server/data/b3_agente.db`, o banco de
desenvolvimento local).

Opções úteis para depuração rápida sem esperar a carga completa:

```bash
# Um ticker só, período curto, sem gravar (só reporta o que gravaria)
./.venv/bin/python -m app.signal_ledger_bootstrap \
  --tickers PETR4,VALE3 --anos 1 --dry-run

# Ver todos os argumentos
./.venv/bin/python -m app.signal_ledger_bootstrap --help
```

## 4. Comando em produção (Railway)

O `rootDirectory=/server` do Railway (`server/railway.json`) faz `server/`
virar a raiz do container — não existe `scripts/` lá dentro, por isso o
bootstrap vive em `server/app/`, não num diretório de scripts avulsos.

```bash
railway ssh
```

Dentro do container:

```bash
cd /app
/opt/venv/bin/python3 -m app.signal_ledger_bootstrap --anos 15 --rng 15y
```

**O `python3` do `PATH` do container NÃO tem as dependências do projeto** —
é preciso usar explicitamente `/opt/venv/bin/python3`. Rodar `python3` puro
(sem o caminho completo) falha com `ModuleNotFoundError` para `httpx`/
`fastapi`/etc.

`B3_DB_PATH` já está configurado no ambiente do Railway (aponta para o
volume persistente do serviço); não é preciso passá-lo de novo — o comando
usa o mesmo banco que a aplicação em produção usa.

## 5. Custo e duração esperados

- **74 requisições ao Yahoo** (uma por ticker do universo padrão,
  `scanner.DEFAULT_UNIVERSE`) — **ZERO consumo do orçamento de 15.000
  requisições/mês da brapi** (ADR-008: brapi é a master gratuita de
  diário/spot com orçamento; Yahoo é a fonte de backup/intraday, sem
  orçamento equivalente). O bootstrap usa exclusivamente Yahoo.
- **~126 mil sinais avaliados** (15 anos × 74 tickers, replay barra a barra).
- **Minutos de CPU** — o replay determinístico (`signal_replay.replay`) roda
  `detect_setups` para cada barra de cada ticker; não é instantâneo, mas não
  precisa de infraestrutura especial.
- Roda **fora do `scheduler_loop`** de propósito: 126 mil replays não podem
  competir com heartbeat e kill-switch no mesmo laço asyncio único do agente
  (`server/app/agent.py`). O precedente é o incidente do kill-switch — ligado
  sem querer, parou a execução da base inteira por 2,5 dias sem ninguém
  notar, porque o heartbeat mascarava o problema. O bootstrap é um processo
  separado justamente para nunca competir com esse laço.

## 6. Como conferir que deu certo

Ao final da execução (fora de `--dry-run`), o comando imprime em stdout:

```
=== Resumo final ===
total no ledger: <N>
setups elegíveis (janela <ano>, n>=40): <N>
setups com amostra insuficiente (janela <ano>): <N>
medidoAte: <data do sinal mais recente no ledger>
```

E duas chaves passam a existir no `kv` global (`user_id=None`):

- `signalLedger:cumulativo` — agregação por setup sobre todo o ledger.
- `signalLedger:janela` — elegibilidade por setup na janela anual anterior
  fechada (`minN: 40`, `elegivel`/`insuficiente` por setup).

Durante a execução, o progresso (`{feitos}/{total} tickers · {n} sinais`) sai
em stderr — ticker com fetch quebrado (sem histórico, granularidade
degradada) aparece na lista de erros ao final, sem derrubar os demais.

## 7. O que NÃO fazer

- **Não pendurar em cron.** O bootstrap é manual, disparado quando um dos
  três casos da seção 2 acontece — não uma rotina agendada.
- **Não usar `--reset` sem entender a consequência.** Apaga TODO o histórico
  medido; a elegibilidade por janela anual volta a `insuficiente` até
  acumular `n≥40` de novo (que pode levar meses só com a manutenção diária —
  rode o bootstrap completo de novo depois de um `--reset`, não confie só no
  incremental).
- **Não confundir com o hook diário.** `signal_ledger_job` (Plano 04) é
  automático e incremental, pendurado no `scheduler_loop` no mesmo bloco de
  `radar_daily.maybe_run`/`analysis_outcomes.maybe_run` — ele não substitui o
  bootstrap nem precisa dele rodar de novo em operação normal.
- **Não rodar com o `scheduler_loop` sob carga alta se puder evitar.** O
  bootstrap é I/O e CPU intensivo por alguns minutos; preferir rodar em
  horário de menor tráfego (fora de pregão) quando possível, embora o
  processo seja separado do agente e não compita pelo mesmo laço asyncio.
- **Não esperar que o número melhore.** Este comando mede o que o motor fez
  no passado; ele não promete e não garante que o setup vai repetir o
  desempenho medido.
