# Phase 7: Seleção Dinâmica por Desempenho Histórico — Context

**Gathered:** 2026-08-21
**Status:** Ready for planning
**Source:** ADR Ingest Express Path (manual — o parser automático de ADR não reconhece a
estrutura de múltiplas seções "Decisão N" deste ADR; conteúdo abaixo é fiel ao ADR-017,
que já foi revisado e aprovado pelo Alex em Plan Mode)

<domain>
## Phase Boundary

Constrói a camada de evidência medida e seleção dinâmica desenhada no ADR-017 (Bloco 1).
Bloco 0 do mesmo ADR (aposentar a faixa catastrófica de setups) já foi entregue fora desta
fase (commit 4a6e7e3, 2026-08-20) — esta fase NÃO revisita essa decisão, só constrói em
cima dela.

O que esta fase entrega:
1. Um ledger de sinais resolvidos (replay determinístico do motor, barreira tripla) —
   tabela nova no banco principal, não no `admin_cache`/`analytics.db`.
2. Bootstrap único (15 anos × 74 tickers) — roda uma vez, fora do `scheduler_loop`,
   comando manual documentado.
3. Manutenção diária incremental — hook novo no padrão de `radar_daily`, pendurado no
   `scheduler_loop`.
4. Guard de granularidade do Yahoo (`range=max` devolve velas mensais mesmo pedindo
   diário/semanal) portado para `server/app/yahoo.py`, cobrindo todos os intervalos.
5. `detect_setups()` ganha campo `historico` (informativo, lido de cache em processo).
6. `regime.ranquear()` consome elegibilidade (janela anual, `min_n=40`) como peso novo no
   `radarScore`.

Fora do escopo desta fase (Blocos 3/4 do ADR-017, deferidos para depois):
- Vocabulário novo em `skill_ref.py`/`copy.js` para expectância negativa/empate estatístico.
- Telas do Radar/Watchlist/Operador exibindo o histórico.
- Prompt novo de IA explicando expectância/R-múltiplo (paridade byte-exata).
- Religar `entradaAuto` do Modo Operador (segue suspenso, `agent.ENTRADA_AUTO_SUSPENSA_ADR017`).

</domain>

<decisions>
## Implementation Decisions

### Arquitetura do ledger (ADR-017, Decisão 2)
- Um ledger, duas leituras — não dois mecanismos independentes. Tabela nova no banco
  PRINCIPAL (mesmo banco de `radar_daily`/`kv`, NÃO `admin_cache`/`analytics.db` — esse é
  só pro portal admin; o motor de decisão precisa ler do banco principal).
- Schema mínimo do ledger: `ticker, setup, lado, data_sinal, data_resolucao, resultado, status`.
- Duas agregações SQL sobre o mesmo ledger: **cumulativa** (histórico exibido junto do setup,
  atualizada a cada sinal resolvido) e **por janela fechada** (elegibilidade que
  `regime.ranquear()` consome, congelada até a próxima virada de janela).

### Bootstrap (ADR-017, Decisão 2)
- Roda UMA VEZ, fora do `scheduler_loop` — 15 anos × 74 tickers não pode competir com
  heartbeat/kill-switch no mesmo laço asyncio único (`server/app/agent.py`, linhas
  ~1013-1100).
- Comando manual documentado, reexecutável para disaster recovery/mudança de família de
  setup — não automático, não recorrente.

### Manutenção diária (ADR-017, Decisão 2)
- Hook novo no padrão EXATO de `radar_daily.should_run()`/`maybe_run()` (gate: dia útil +
  horário + `last_date != hoje`, persistido em `kv`), pendurado no `scheduler_loop`
  (mesmo bloco que já chama `radar_daily.maybe_run`/`analysis_outcomes.maybe_run`,
  `agent.py` ~1074-1087).
- Avança o cursor por ticker usando candles que `candle_cache` JÁ buscou — sem custo extra
  de brapi/ADR-008 (o orçamento é de 15k requisições/mês pro app inteiro).
- Resolve sinais pendentes (barreira tripla), regrava as duas agregações.

### Janela de reavaliação: ANUAL (ADR-017, Decisão 2)
- Não é meio-termo arbitrário — é a granularidade sob a qual `scripts/backtest_pesos.py`
  mediu a persistência (Spearman +0,523, t=+7,52, 15 janelas em 15 anos). Trimestral/
  semestral extrapolaria pra regime não testado e furaria ainda mais o piso de amostra por
  célula.
- Fechamento de janela: gate barato do mesmo formato de `radar_daily.should_run()`,
  checado todo dia, dispara só quando o marcador "última janela fechada" (em `kv`) for
  anterior à virada de ano-calendário (alinhado a `pregao.is_trading_day()`, não timer
  fixo).

### Dois pisos de amostra (ADR-017, Decisão 2)
- Bloco 0 (estrutural, all-time, já entregue): n≥100 — não é usado nesta fase.
- Bloco 1 (elegibilidade por janela, NESTA fase): **n≥40 literalmente**, herdado de
  `scripts/backtest_pesos.py:69` — mudar o número invalidaria o resultado empírico que
  justifica a técnica.
- Célula abaixo do piso NUNCA vira "elegibilidade negativa" — ausência de evidência ≠
  prova de mau desempenho. Cai no comportamento atual (sem peso histórico) até acumular
  amostra.

### Carimbo obrigatório (ADR-017, Decisão 2)
- Todo número exibido/persistido carrega `medidoAte` (projeção cumulativa) ou
  `calculadoEm`/`janelaRef` (projeção por janela) no mesmo registro.
- Degrada visualmente (nunca bloqueia) se o job atrasar mais de 2 dias úteis — fora de
  escopo desta fase o "visualmente" (isso é Bloco 3), mas o CAMPO precisa existir agora
  pra Bloco 3 consumir depois.

### Reprodutibilidade (ADR-017, Decisão 2)
- Promove as funções PURAS de `scripts/backtest_sinal.py` (`sinais_do_ticker` linha 115,
  `avaliar` linha 164 — replay determinístico + barreira tripla) para um módulo NOVO em
  `server/app/` (nome sugerido: `signal_replay.py`).
- `scripts/backtest_sinal.py` vira wrapper fino sobre a mesma lógica — NÃO duplicar a
  implementação da barreira tripla. Sentido de dependência preservado: scripts→app, nunca
  o contrário (confirmado: hoje `backtest_sinal.py` já importa `from app import
  indicators, regime, setups, yahoo` — nada em `server/app/` importa de `scripts/`).
- O bootstrap continua sendo um comando documentado que reproduz o número exato que a
  produção mostra, porque usa a MESMA função.

### Guard do Yahoo (ADR-017, Decisão 2)
- Portar `_confere_granularidade` (`scripts/backtest_sinal.py:51-73`) para dentro de
  `server/app/yahoo.py`, na fronteira de fetch (`get_history` ou equivalente), cobrindo
  TODOS os intervalos — hoje o guard existente em `yahoo.py` (linha ~226) só cobre
  `INTRADAY_INTERVALS`, deixando diário/semanal passar sem verificação. Isso é o MESMO
  bug que já causou dado degradado silencioso (medição de 2026-08-20 no ADR-016: PETR4/max
  devolveu 320 barras mensais rotuladas como diárias).

### `detect_setups`/`regime.ranquear` (ADR-017, Decisão 2, achado adicional do Plan agent)
- `detect_setups()` ganha campo informativo por setup: `historico: {expR, n, medidoAte,
  elegivel, insuficiente}`, lido de CACHE EM PROCESSO com TTL curto (padrão `_SNAP_CACHE`
  já existente em `technical_snapshot.py`) — nunca uma query a banco por request (essa
  função roda no caminho síncrono quente, por request).
- **NÃO altera `_vale()`** para excluir setups com expectância negativa da janela — isso
  apagaria o setup da tela, contra o mandato didático do produto (mostrar o padrão E seu
  histórico, não esconder).
- `regime.ranquear()` (linhas ~246-258) é quem consome `elegivel`/`expR` da janela anterior
  como termo NOVO no `radarScore`, no mesmo lugar onde `gatilhoAlinhado` e o desempate por
  confluência já vivem hoje — regra determinística, testável isolada.

### Guardrail explícito (CVM/princípio 5, ADR-016 já vetou isso)
- Isto é regra determinística. Se em algum momento a proposta for deixar a IA escolher
  setup, ordenar o Radar ou decidir entrada, isso é mudança de natureza e exige aprovação
  separada e explícita — NÃO é decisão desta fase.

### Claude's Discretion
- Nome exato do módulo novo (`signal_replay.py` é sugestão, não obrigação).
- Nome exato da tabela do ledger e dos campos de índice (SQLite, mesmo banco principal —
  ver `server/app/db.py` pro padrão de `CREATE TABLE IF NOT EXISTS` já usado no projeto).
- Nome exato da chave `kv` das duas agregações (seguir o padrão `radarDaily:<period>` já
  existente).
- Detalhe de implementação do TTL do cache em processo em `detect_setups`.
- Onde exatamente no `scheduler_loop` pendurar o novo hook (perto de `radar_daily`/
  `analysis_outcomes`, mas a ordem exata dentro do bloco é discrição do planner).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Decisão e diagnóstico (fonte da verdade desta fase)
- `docs/adr/017-revisao-de-setups-e-selecao-dinamica.md` — as 3 decisões formais (critério
  de revisão, arquitetura da seleção dinâmica, destino do Modo Operador). Este CONTEXT.md
  é um resumo estruturado dela; em caso de qualquer divergência, o ADR-017 é a fonte.
- `docs/adr/016-qualidade-do-sinal-do-motor-de-setups.md` — o diagnóstico completo (7
  adendos) que motivou o ADR-017. Adendo 7 é o mais relevante aqui (a técnica de peso por
  desempenho histórico, validada out-of-sample).
- `docs/adr/015-assertividade-do-motor-de-recomendacao.md` — por que retrospectivo
  (backtest, esta fase) e prospectivo (`analysis_outcomes`, já corrigido na Fase 6) NUNCA
  se misturam no mesmo número.

### Código já existente a reaproveitar (não reescrever)
- `scripts/backtest_sinal.py` — `sinais_do_ticker()` (linha 115), `avaliar()` (linha 164),
  `agregar()` (linha 221), `_confere_granularidade()` (linha 51-73). Funções PURAS a
  promover para `server/app/`.
- `scripts/backtest_pesos.py` — a lógica de seleção walk-forward já validada (janela
  anterior → elegibilidade da janela atual, `min_n=40`, sem vazamento de futuro). Replicar
  esse PADRÃO em produção, não o script em si.
- `server/app/radar_daily.py` — `should_run()`/`maybe_run()`/`store_result()`: o padrão
  exato de job diário a reusar para o hook de manutenção incremental.
- `server/app/agent.py` (linhas ~1013-1100, `scheduler_loop`) — onde pendurar o hook novo,
  mesmo bloco de `radar_daily.maybe_run`/`analysis_outcomes.maybe_run`.
- `server/app/technical_snapshot.py` — `_SNAP_CACHE` (linha 32) e `build()` (linha 99): o
  padrão de cache em processo a reusar para o campo `historico` de `detect_setups`.
- `server/app/setups.py` — `detect_setups()` (linha 483+, já editado no Bloco 0 com
  `SETUPS_APOSENTADOS`/campo `aposentado`); `_setups_br()`, `_vale()`.
- `server/app/regime.py` — `ranquear()` (linha ~214-261), `_gatilho_alinhado()` (linha
  ~188-210, já editado no Bloco 0 pra filtrar `aposentado`).
- `server/app/yahoo.py` — `get_history()` (linha ~214-247), guard existente de
  `INTRADAY_INTERVALS` (linha ~226) a estender.
- `server/app/db.py` — padrão de schema/`kv` do banco principal.
- `server/app/analytics.py` — o QUE NÃO usar (`admin_cache`, banco separado) — só citado
  como contraste negativo, não como padrão a seguir aqui.

### Guardrails do repositório (não re-litigar)
- `CLAUDE.md` (raiz do repo) — princípios 1-10, especialmente 4 (nunca inventar valor) e 5
  (motor determinístico, IA nunca decide).
- Paridade `deviceStore`/`serverStore` (`web/src/persistence.js`) — esta fase é backend-only
  (sem UI, Bloco 3), então não deveria tocar nisso; se algum campo novo vazar pro front por
  engano, os dois stores precisam ficar em paridade.

</canonical_refs>

<specifics>
## Specific Ideas

- Reaproveitar EXATAMENTE a barreira tripla já implementada e testada em
  `backtest_sinal.avaliar()` — não reinventar a lógica de resolução de sinal (empate
  intrabar a favor do stop, `r=-1.0` no stop, `r=abs(alvo-entrada)/risco` no alvo, `r` do
  close final se expirar sem bater nada).
- O bootstrap deve ser reexecutável (idempotente ou com opção de reset) — não precisa ser
  incremental na primeira versão, mas precisa deixar claro no comando/doc que é uma
  operação PESADA e MANUAL.
- O hook diário NÃO deve refazer o replay dos 15 anos — só avança o cursor com candles
  novos desde a última execução por ticker.

</specifics>

<deferred>
## Deferred Ideas

- Bloco 3 (interface): vocabulário novo em `skill_ref.py`/`copy.js`, telas do
  Radar/Watchlist/card de setup mostrando `historico`, estados completos (sem amostra,
  amostra insuficiente, dado desatualizado, setup aposentado).
- Bloco 4 (IA): prompt novo explicando expectância/R-múltiplo/amostra insuficiente,
  paridade byte-exata `defaults.py`↔`catalog.js`.
- Religar `entradaAuto` do Modo Operador (gated pela elegibilidade construída nesta fase) —
  decisão de produto separada, não desta fase.
- Janela móvel/recálculo mais frequente que anual — registrado no ADR-017 como "possível
  v2, não recomendado agora, não foi o que foi validado".

</deferred>

<scope_fence>
## Scope Fence

- NÃO reabrir a decisão do Bloco 0 (critério de aposentadoria por magnitude econômica, já
  aprovado e em produção).
- NÃO tocar em `web/src/App.jsx`, `copy.js`, `skill_ref.py` nesta fase — é backend puro
  (Bloco 1). Qualquer necessidade de UI é Bloco 3, fase futura.
- NÃO religar `agent.ENTRADA_AUTO_SUSPENSA_ADR017` — permanece suspenso até decisão
  explícita separada, mesmo que a elegibilidade por setup passe a existir nesta fase.
- NÃO mover nenhuma decisão de seleção/ordenação/entrada para julgamento de IA — guardrail
  do ADR-016, sem exceção.
- NÃO consumir orçamento extra de brapi (ADR-008) — o hook diário só usa candles que
  `candle_cache` já buscou para outros fins.

</scope_fence>

---

*Phase: 07-sele-o-din-mica-por-desempenho-hist-rico-ledger-de-sinais-re*
*Context gathered: 2026-08-21 via ADR Ingest Express Path (manual, ADR-017)*
