# Phase 51: Seu dia na bolsa — card de curiosidade no fechamento - Context

**Gathered:** 2026-11-17
**Status:** Ready for planning (UI-SPEC antes do plano: `workflow.ui_phase: true`)
**Discussão:** Alex + orquestrador, em sessão de grilling registrada em `.planning/engajamento/DECISIONS.md` (Q1–Q8, todas confirmadas).

<domain>
## Phase Boundary

O app passa a fechar cada pregão com um card determinístico, "Seu dia na bolsa". O gancho é a **curiosidade honesta** (Q1), não obrigação nem alarme. O card junta três famílias de informação:

- (1) o "e se" dos setups que o usuário viu e não operou;
- (2) o que o motor fez sozinho na carteira dele;
- (3) um fato raro do mercado, com nome de conceito.

Ele chega por push às ~17:15 e fica no topo do Acompanhar até o próximo pregão. O streak deixa de contar aberturas e passa a contar dias de decisão. O portal ganha a medição do card e o contrapeso de overtrading.

Fora do escopo:
- notícias, feed externo e calendário de eventos (Q6; o calendário curado fica para depois, condicionado a ter um dono);
- texto de IA, mesmo uma linha diária em cache (Q5: experimento posterior);
- push de abertura novo (Q4);
- push na web/PWA;
- ranking entre usuários;
- qualquer recompensa por número de operações.
</domain>

<decisions>
## Implementation Decisions

### Mecanismo e limites (Q1, Q3)
- **D-01 Curiosidade:** o sucesso é o usuário abrir o card E explorar (tocar em conceito, ativo ou plano). Só abrir não conta.
- **D-02 Proibido:**
  - push ou texto de "oportunidade" ("entre agora");
  - ranking entre usuários;
  - recompensa ou medalha por número de operações;
  - urgência artificial ("só hoje", contagem regressiva);
  - esconder o placar negativo.
  - Um guardião de vocabulário trava as palavras proibidas ("perdeu", "oportunidade", urgência) nos templates do card e do push.

### Família 1 — o "e se" (Q2b, Q4b)
- **D-03 Escopo:** só os setups que o usuário **viu de fato**:
  - ativos da carteira;
  - ativos da watchlist;
  - card do Radar aberto (`radar_result_opened`).
  - Setups que ele não viu não entram.
- **D-04 Equilíbrio:** os dois desfechos têm o **mesmo destaque**.
  - Alvo atingido: "o plano chegaria ao alvo".
  - Stop atingido: "não entrar foi o acerto".
  - A palavra "perdeu" nunca aparece.
  - Placar semanal honesto: X setups vistos, Y chegariam ao alvo, Z ao stop, W ainda abertos ou expirados.
- **D-05 Desfecho pelo motor:** o resultado (alvo, stop, expirou, sem gatilho) e o R saem de regra determinística sobre candles. A IA nunca calcula nem escreve o número.
  - Reusar a régua de `signal_ledger.py:66-83` (`resultado`, `r`) ou a de `analysis_outcomes.avaliar_pendentes` (`HORIZON_PREGOES=10`). Não criar uma terceira régua.
  - Um setup visto hoje normalmente só se resolve dias depois. Por isso o card mostra os setups **resolvidos no dia**, que podem ter sido vistos em pregões anteriores, dentro do horizonte. Os ainda abertos entram só no placar semanal.

### Família 2 — o motor na carteira (Q2b)
- **D-06:** o que o motor fez no dia na carteira do usuário:
  - stop que subiu (breakeven, trailing);
  - alvo ou stop executado;
  - ordem pendente executada;
  - carteira × IBOV no dia (o benchmark já existe e hoje aparece pouco).
- Fonte: histórico de ordens e eventos do motor já gravados mais o snapshot das 17:05. Nada é recalculado pela IA.

### Família 3 — fato raro (Q4c)
- **D-07 Critério pessoal (opção c):**
  - **Mercado:** só entra quando é raro de verdade. O IBOV precisa estar no **percentil 95 de |retorno diário| dos últimos 12 meses** (alvo: cerca de 1 por semana).
  - **Ativos da carteira e da watchlist:** critério mais solto, movimento > **2×ATR(14)** do próprio ativo.
- **D-08 Regras candidatas, cada uma ligada a um conceito:**
  - IBOV fora do normal → volatilidade;
  - amplitude (quase todo o universo na mesma direção) → amplitude/capitulação;
  - gap de abertura grande → gap;
  - máxima ou mínima de 52 semanas → rompimento / suporte e resistência;
  - ativo da carteira > 2×ATR → volatilidade / stop.
  - Os limiares exatos ficam com o planner, calibrados por backtest sobre o cache: é preciso mostrar a frequência resultante em 12 meses. Alvo de mercado: cerca de 1 por semana. Pessoal: a maioria dos dias com algo.
  - Pela régua de 12 meses, o IBOV usa o desvio dos retornos de fechamento: `benchmark.serie_ibov` só traz `{date, close}`, sem OHLC, então o ATR do IBOV não está disponível.

### Modos e texto (Q2, Q5)
- **D-09 Mesmo card nos dois modos,** com uma regra única de seleção.
  - Muda o tom: no Estudo, conceito mais uma pergunta; no Operador, uma linha de mesa.
  - Muda também a ordem das famílias: **Estudo 1 → 3 → 2**, **Operador 2 → 1 → 3**.
- **D-10 Só templates determinísticos:** por regra e modo, com placeholders e 3 a 4 variantes por regra.
  - Ficam em `skill_ref` ↔ `copy.js`, com paridade byte a byte e guardião de espelho. O front não compõe vocabulário.
  - A variante é escolhida de forma determinística (ex.: hash de usuário + dia), não aleatória, para ser testável.
- **D-11 Fontes externas:** só o que o app já calcula (candles, setups, carteira, IBOV). Toda afirmação traz o carimbo do dado (princípio 3).

### Entrega (Q4, Q8)
- **D-12 Job de fechamento ~17:15 BRT:** roda depois do snapshot de patrimônio (`snapshot_diario`, janela 17:05–17:15) e é idempotente por dia (`*LastRun`).
  - **Não gasta brapi:** o orçamento fecha às 17:15 (`brapi_budget._ORCAMENTO_FIM`). Usa `candle_cache.peek` e o EOD já em cache.
  - IBOV via Yahoo (`benchmark.serie_ibov`).
  - Sem nada relevante nas regras, não gera card nem push.
- **D-13 Push "Seu dia na bolsa":**
  - Preferência nova `fechamento` em `push.PREFS_PADRAO`/`PREFS_BOOLS`.
    - **Conta nova:** ligada por padrão.
    - **Conta existente:** desligada até aceitar um **convite único** no próprio card do Acompanhar ("Quer receber isto às 17:15?").
    - O planner define como distinguir conta nova de existente (ex.: data de criação da conta × data do deploy, ou flag gravada no aceite/recusa).
    - Atenção: `prefs_for` faz merge do default sobre o valor gravado. Um default `True` ligaria o push para todo mundo, então esse ponto precisa de cuidado explícito.
  - **Silêncio:**
    - dia sem pregão (`pregao.is_holiday`, que cobre feriados fixos, móveis e `B3_FERIADOS_EXTRA`, e fim de semana);
    - dia sem nada relevante.
  - **Teto de 2 pushes de engajamento por dia:** Radar 08:45 + fechamento. Gatilho, execução e proteção ficam fora do teto.
  - **Web/PWA:** sem push na v1, só o card.
- **D-14 Linha no Radar das 08:45:** o push de prévia (`radar_daily.push_body`, template `skill_ref.PUSH_RADAR`) ganha uma linha com o "e se" de ontem. Não cria push novo.
- **D-15 Card no topo do Acompanhar** até o próximo pregão: o card do dia anterior some quando o próximo é gerado.

### Streak (Q3)
- **D-16 Dia de decisão:** o dia entra no streak quando há decisão registrada:
  - explorar o card do dia;
  - revisar um plano;
  - ajustar stop ou alvo;
  - decidir conscientemente "não entrar".
  - Compra e venda **não** são exigidas, para não estimular overtrading.
  - Fim de semana e feriado não quebram nada.
  - Nada zera: a exibição é "X dias de decisão nas últimas 4 semanas".
  - **Emenda D-16 (2026-11-17, decisão do Alex):** "decidir não entrar" fica FORA da v1 — não existe controle de usuário para isso no app; `decision_day` cobre só `card`, `plano` e `stop`. Não criar botão nesta fase.
- **D-17 Data de Brasília:** o streak atual usa data UTC (`App.jsx:10938-10951`, `toISOString().slice(0,10)`) e credita o dia seguinte depois das 21:00 BRT. Passa a usar `hojeBRT()`, como o efeito do snapshot logo acima. Isso entra como correção junto com a mudança de regra.

- **Emendas D-06/D-12 (2026-11-18, confirmada pelo Alex em 2026-11-18, reversível por env — ver `.planning/engajamento/DECISIONS.md` P-A/P-B):**
  - P-A (D-12): o job fica cache-first. O que faltar vem do Yahoo (backup ADR-008, zero brapi), na prioridade vistos > posições > IBOV > watchlist > universo do Radar, com teto de 120 chamadas por dia BRT, somando as passadas, (`B3_DIA_NA_BOLSA_MAX_YAHOO`). Ticker sem dado fica fora do card.
  - P-B (D-06): carteira × IBOV só entra junto de um evento do motor; sozinha não gera card.

### Medição (Q7)
- **D-18 Eventos novos:**
  - `daily_card_shown`, `daily_card_opened`, `daily_card_explored` (com `tipo`: conceito/ativo/plano e `familia`) e `decision_day`;
  - todos com `modo`;
  - entram na lista `EVENTOS` de `web/tests/test_analytics_instrumentacao.mjs`. O servidor não tem whitelist.
- **D-19 Portal:**
  - taxa de exploração (explorou ÷ viu) por família e por modo;
  - WAU exato (`COUNT(DISTINCT user_id)` de `session_start` em 7 dias, sobre os eventos brutos). Persistir um valor diário em `obs_daily_metrics` via `registrar_metricas_diarias`/`METRICAS_CONHECIDAS` para guardar a série além dos 90 dias;
  - dias de decisão por usuário em 4 semanas;
  - **contrapeso:** `trade_simulated` por usuário ativo, lado a lado.
- **D-20 Hipótese, não meta:** exploração ≥ 30% em 4 semanas, WAU estável ou em alta, sem alta de operações por usuário. Não vira alerta nem gate.

### Claude's Discretion
- Forma do registro de "vistos" e do arquivo do Radar. Hoje o Radar diário é global e sobrescrito (`radarDaily:<period>`, `user_id=None`, `radar_daily.py:80-92`), e `radar_result_opened` só leva `{ticker}` (`App.jsx:8589`). O planner decide:
  - um arquivo diário global do Radar (`radarDailyArquivo:<data>`), com retenção que cubra o horizonte do desfecho;
  - um registro por usuário (kv por escopo) dos vistos (ticker, setup, data), com o evento do Radar passando a enviar `setup`;
  - os preços de gatilho, stop e alvo saem do arquivo do motor, nunca do cliente (T-50-13);
  - retenção própria, maior que os 90 dias de analytics.
- Watchlist no iOS: o servidor não tem a watchlist do aparelho (`deviceStore.putWatchlist` só grava local). Opções:
  - usar `pushPrefs.universo` (watchlist ∪ posições, máximo 60, válido por 7 dias);
  - o front enviar a lista no registro de "vistos".
  - O planner escolhe; a paridade `deviceStore` ↔ `serverStore` é obrigatória.
- Onde o streak e os dias de decisão são persistidos (config hoje é local no iOS). Se o portal precisa de "dias de decisão por usuário", a fonte é o evento `decision_day`, não o config.
- Nome do módulo do job (ex.: `server/app/dia_na_bolsa.py`) e do endpoint do card (ex.: `GET /api/dia-na-bolsa`).
- Conceitos novos: "amplitude/capitulação" e "máxima de 52 semanas" como `CONCEITOS` (com números do dia) ou verbete KB. Gap e volatilidade reaproveitam `kb.py` (`estr-gap` :615, `ind-volatilidade-historica` :449, `ind-atr` :243) via `abrirVerbeteKb`. Redação pela skill `didatica-boris`.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Decisões e regras
- `.planning/engajamento/DECISIONS.md` — registro do grilling (Q1–Q8) e inventário
- `CLAUDE.md` — princípios 1–10, guardrails CVM, paridades, vocabulário por modo
- `.claude/skills/didatica-boris/SKILL.md` — voz por modo, princípios de dado, guardiões
- `docs/adr/001`, `docs/adr/008` — fontes de dados e orçamento brapi; `docs/adr/015` — ledger de sinais

### Código — dados e desfecho
- `server/app/signal_ledger.py` (:38, :66-83), `server/app/signal_ledger_job.py` (:45, :113) — desfecho global (alvo/stop/expirou/sem_gatilho, r), sem preços
- `server/app/analysis_outcomes.py` (:94-162, :614) — desfecho por usuário de análises N1/N2 (HORIZON_PREGOES=10)
- `server/app/radar_daily.py` (:80-94 armazenamento, :218-316 push) — Radar global sobrescrito; push da prévia
- `server/app/candle_cache.py` (:147 `peek`), `server/app/benchmark.py` (:40 `serie_ibov`), `server/app/indicators.py` (:155 `atr`)
- `server/app/brapi_budget.py` (:90 `_ORCAMENTO_FIM`)

### Código — job, push, carteira
- `server/app/agent.py` (:1533 `scheduler_loop`, :1655-1658 hook do snapshot, :1895+ `status_snapshot`, :123 métricas diárias)
- `server/app/snapshot_diario.py` (:21-40, :175-247 `run_tick` sobre `store.scopes_com_carteira`) — padrão de job a copiar
- `server/app/push.py` (:101-148 prefs, :156-166 classes, :237 `send_to_user`)
- `server/app/timing_watch.py` (:146-192) — padrão de estado kv diário, teto e dedupe
- `server/app/pregao.py` (:86 `feriados`, :102 `is_holiday`)
- `server/app/store.py` (:482-513 watchlist, :713 `scopes_com_carteira`, :1768-1827 snapshots)

### Código — vocabulário, conceitos, analytics
- `server/app/skill_ref.py` (:350-354 `PUSH_RADAR`) ↔ `web/src/copy.js`
- `server/app/conceitos.py` (:188+ estrutura, :800 `SETORES`), `server/app/kb.py` (:243, :449, :615, :732)
- `server/app/analytics.py` (:30 retenção, :35 chaves proibidas, :148-181 ingest, :233-264 métricas diárias, :305-348 resumo/funil), `server/app/main.py` (:1044, :1065, :1117)
- `web-admin/src/App.jsx` (:270-304), `web-admin/src/api.js` (:55)

### Código — front
- `web/src/App.jsx` (:8589 `radar_result_opened`, :9906-9935 `session_start`, :10612-10650 abrir conceito/verbete, :10921-10951 snapshot e streak, :11594 `ConceitoSheet`) — nunca ler inteiro
- `web/src/entendimento.jsx` (:89 `SetorAlvo`, :182 `ConceitoSheet`)
- `web/src/persistence.js` (:6-28 fonte de verdade por plataforma, :227 `putWatchlist`)
- `web/src/analytics.js` — `track`
</canonical_refs>

## Existing Code Insights

### Reusable Assets
- Padrão de job diário idempotente: `snapshot_diario` / `radar_daily` (`enabled`, `should_run`, `last_run_date`, `maybe_run`, `db.marcar_job`, nunca levanta exceção).
- Régua de desfecho: `signal_ledger` (global) e `analysis_outcomes` (por usuário).
- Envio de push: `push.send_to_user` + `prefs_for` (merge de default) + estado kv diário de `timing_watch`.
- Calendário: `pregao.is_holiday`.
- Didática: `CONCEITOS` + `SETORES` + `SetorAlvo`/`ConceitoSheet` + KB.

### Established Patterns
- Backend calcula, front exibe; o front nunca compõe vocabulário.
- `null` para desconhecido, nunca `0.0`.
- Toda mudança de prompt ou vocabulário passa por guardião de espelho.
- Guardiões não se apagam; uma reversão deliberada atualiza o guardião com nota.

### Integration Points
- `scheduler_loop`, depois do bloco do snapshot (antes do bloco de pregão aberto, porque roda após o fechamento).
- `push_body` do Radar, para a linha do "e se".
- Topo da tela Acompanhar (`App.jsx`, localizar por grep).
- Efeito do streak em `App.jsx:10937`.

## Specific Ideas
- Exemplos de linha (ilustrativos; o texto final sai dos templates):
  - "O IBOV caiu 3,8%: dia mais forte em 14 meses."
  - "B3SA3 andou 3 ATRs hoje. O que isso diz do seu stop?"
  - "PETR4 abriu 4% abaixo de ontem e não voltou."

## Deferred Ideas
- Linha diária de IA, igual para todos e em cache, comparada pela métrica de exploração (Q5).
- Calendário curado de eventos no portal (Copom, IPCA, datas de resultado), condicionado a ter dono (Q6).
- Push na web/PWA.
- Meta formal de engajamento depois de 4 semanas de baseline (Q7).
