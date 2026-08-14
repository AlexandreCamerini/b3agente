# ADR-012: Portal de Observabilidade v2 — tendência no tempo, eficiência da IA e da automação

**Status:** Proposto — Fases 1 (Eficiência da IA agregada) e 2 (tendência
para Comportamento do Usuário) implementadas. Fases 3-5 (automação +
correlação análise↔operação, série temporal para Visão Geral/Custos,
redesenho visual) seguem o mesmo faseamento, cada uma com aprovação própria
antes de começar.
**Data:** 2026-08-14 · **Companion:** ADR-011 (v1 do portal, já em produção)

---

## Contexto

O ADR-011 (v1) entregou o portal de observabilidade — Visão Geral, Custos,
Comportamento do Usuário — todas em valor pontual (`Kv`), sem série temporal.
O pedido seguinte foi evoluir isso para um portal executivo real: toda
métrica com tendência no tempo, mais duas perguntas de negócio que nenhuma
tela do produto respondia: a IA acerta o que recomenda por ativo? As
operações automáticas do Operador são eficientes — e batem com o que a
própria IA registrou como análise?

Uma auditoria completa (leitura direta do código, não suposição) mudou o
escopo real do trabalho antes de qualquer linha ser escrita:

- **A pergunta "a IA acerta?" já estava resolvida no backend**, só não
  estava no portal. `server/app/analysis_outcomes.py` (qa/30, qa/35, qa/37,
  qa/44) já registra cada análise com stop/alvo, já avalia contra candle
  real em job diário (10 pregões fixos), e já calcula taxa de acerto, R
  médio, expectância, profit factor, calibração de confiança declarada,
  segmentação por setup/regime, curva de R acumulado e drawdown máximo —
  tudo isso exposto SÓ por-usuário (`GET /api/analysis-outcomes/stats`) na
  tela "Eficiência da IA" do app consumidor. O portal admin nunca via o
  agregado de todos os usuários.
- **A pergunta "a automação é eficiente?" não tinha nenhum dado ainda.**
  Ordens ficam em `kv["history"]` (JSON por usuário, sem tabela SQL), sem
  campo `origem` (manual × automático) — o próprio ADR-011 já citava isso
  como decisão pendente, nunca implementada.
- **Tendência no tempo é parcial.** `analytics.py` (qa/47) já tem uma tabela
  de rollup diário real (`analytics_daily`), mas o endpoint
  `GET /api/analytics/summary` não lê dela — lê o evento bruto, que expira
  em 90 dias. Para Visão Geral/Custos não existe NENHUMA série — tudo é
  dict em memória, zera a cada deploy.

## Decisão — faseamento

Cada fase entra em produção antes da próxima começar (branch própria,
testes, verificação ao vivo no browser, merge só com aprovação explícita).

### Fase 1 — Eficiência da IA agregada (implementada)

Reaproveitamento de 100% do backend existente, sem nenhum dado novo a
coletar:

- `analysis_outcomes.compute_stats_all_users()` — usa a função
  `_scopes_com_outcomes()` já existente pra concatenar outcomes de todos os
  escopos e reaproveita `compute_stats()` (puro, já testado) por cima do
  agregado. **Nunca devolve `user_id` nem lista bruta de outcomes** — só o
  dict agregado, que já respeita `MIN_N=10` por célula (evita reidentificar
  usuário por amostra pequena).
- Cache diário, não cálculo síncrono por request: o agregado é recomputado
  1x/dia dentro do MESMO hook que já roda `avaliar_pendentes`
  (`scheduler_loop` → `analysis_outcomes.maybe_run`, agora com um parâmetro
  opcional `cache_conn`), gravado numa tabela nova de cache genérica em
  `analytics.db` (sqlite puro, mesmo arquivo do resto da observabilidade):
  `admin_cache(key, value, computed_at)`. O `GET /api/analytics/ia-eficiencia`
  só lê o cache — com fallback de cálculo síncrono único no cold-start
  (cache ainda não rodou 1x, ex. logo após o deploy desta feature), pra não
  deixar o admin com tela vazia até a próxima passada diária.
- Nova tela "Eficiência da IA" no portal: KPIs (taxa de acerto, R médio,
  avaliadas, pendentes), expectância/profit factor, calibração da confiança
  declarada, curva de R acumulado (componente `RCurve` portado do app
  consumidor, sem lib nova). Rótulo fixo: "Autoavaliação interna do sistema
  — não é garantia de resultado futuro."

### Fase 2 — Tendência para Comportamento do Usuário (implementada)

`adocao_por_feature` e `shown_vs_dismissed` passam a ler de `analytics_daily`
(rollup persistido, sobrevive além de `RETENCAO_DIAS`) para tudo ANTES de
hoje, somado ao dado bruto de HOJE (o rollup só cobre até ontem — sem essa
soma haveria uma lacuna de 1 dia sempre visível). Nova função
`serie_diaria_por_evento()` devolve um ponto `{day, count}` por dia por
evento — é o que alimenta o novo gráfico de linha (`Sparkline`, sem lib
nova) ao lado de cada linha em "Adoção por feature" e "Shown vs. dismissed"
no portal.

**`funil` foi DELIBERADAMENTE excluído desta migração** — ele depende da
ORDEM de eventos por usuário (MIN(timestamp) por passo, comparado entre
passos), e `analytics_daily` só guarda contagem agregada do dia, sem
`user_id` nem timestamp. Migrar teria trocado o que o funil mede (sequência
real por usuário) por uma aproximação errada. Ele continua no dado bruto,
com o limite de `RETENCAO_DIAS` (90 dias) já existente — a UI mostra essa
limitação explicitamente, não a esconde.

### Fase 3 — Automação + correlação análise↔operação (planejada)

`store.buy`/`sell`/`buy_option`/`sell_option` ganham `origem: str = "manual"`
(default preserva as chamadas manuais existentes); os 3 call-sites do
Operador automático em `agent.py` passam `origem="automatico"`. Histórico
anterior à mudança fica sem `origem` — não é reescrito retroativamente.
Correlação por `snapshotId` (já existe nos dois lados: `history` e
`analysisOutcomes`) responde "das análises registradas, quantas viraram
ordem, com que origem, e o resultado bateu com o que a análise previu?" —
sem fabricar "tempo de reação" nem "slippage vs. previsto" (dado que não
existe hoje).

### Fase 4 — Série temporal para Visão Geral e Custos (planejada)

Nova tabela genérica em `analytics.db`, `obs_daily_metrics(day, metric,
value)` (mesmo padrão EAV que `analytics_daily` já usa), populada 1x/dia
pelo mesmo hook com os campos hoje só-memória (tokens/dia por modelo,
orçamento brapi, cache de candles, falhas de push automático, duração do
radar diário).

### Fase 5 — Redesenho visual executivo (planejada)

Reorganiza as 5 telas com hierarquia executiva (KPIs no topo, drill-down
abaixo), reaproveitando tokens do Brand Book v2 já usados no app consumidor.
Zero métrica nova, só layout.

### Fora de escopo desta rodada

- Alertas/thresholds (ex. "taxa de acerto caiu abaixo de X") — candidato a
  fase futura.
- Navegador de tabelas genérico e RBAC granular — já eram exclusões do
  ADR-011.
- "Tempo de reação" e "slippage vs. previsto" da automação — dado não
  existe, não será fabricado.

## Guardrails válidos para todas as fases

- Nenhum endpoint admin novo devolve `user_id` individual ou lista bruta —
  só agregados respeitando `MIN_N`.
- Nenhuma métrica de tendência aparece sem indicar desde quando o histórico
  existe.
- Taxa de acerto da IA é rotulada como autoavaliação interna, nunca como
  garantia.

## Consequências

- O portal ganha uma pergunta de negócio real (eficiência da IA agregada)
  sem duplicar cálculo — qualquer correção em `analysis_outcomes.py` se
  propaga automaticamente pro admin, mesma lógica de reaproveitamento já
  adotada no ADR-011.
- A trilha de automação (Fase 3) começa vazia no dia em que `origem` for
  ativado — não há como reconstruir retroativamente a origem de `history`
  já gravado (mesma consequência já registrada no ADR-011 para essa mesma
  peça de dado).

## Referência cruzada

- `docs/adr/011-modulo-observabilidade-governanca.md` — v1 do portal, já
  cita o campo `origem` como decisão pendente (Fase 3 aqui a resolve).
- `server/app/analysis_outcomes.py` — motor de autoavaliação da IA,
  reaproveitado sem alteração de comportamento, só uma função de agregação
  nova por cima.
- `server/app/analytics.py` — banco separado (`analytics.db`) e o padrão de
  rollup diário (`analytics_daily`) que a Fase 2/4 estendem.
