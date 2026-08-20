# Phase 6: Instrumentação de Assertividade (ADR-015) - Context

**Gathered:** 2026-08-20
**Status:** Ready for planning
**Source:** ADR Ingest (manual — `docs/adr/015-assertividade-do-motor-de-recomendacao.md` usa
formato narrativo próprio do repo, não Nygard/MADR; o parser automático (`adr-parser.cjs`)
não reconheceu as seções e extraiu zero decisões — este CONTEXT.md foi escrito a partir da
leitura direta do ADR e da pesquisa (`.planning/quick/260820-0hl-*/260820-0hl-RESEARCH.md`).)

<domain>
## Phase Boundary

Consertar a **medição** de eficiência da IA (`analysis_outcomes`), não o
**motor de decisão** (confluência, setup, plano operacional). O painel
"Eficiência da IA" hoje fabrica stops (ancora no `close` em vez do gatilho) e
infla `n` por duplicação — na direção otimista (+2,56R medido vs 0,00R real
nos mesmos dados). É a Alternativa 1 do ADR-015 — pré-requisito para
qualquer decisão futura sobre o motor, mas não muda o motor em si.

</domain>

<decisions>
## Implementation Decisions

### ADR15-01 — Gravar campos que faltam no outcome

- `main.py:1313-1327` (N1) e `main.py:1416-1432` (N2): adicionar ao payload
  de `analysis_outcomes.registrar(...)`: `entrada=plano.get("entrada")`,
  `alvo2=plano.get("alvo2")`, `rr2=plano.get("rr2")`,
  `confluencia=sres.get("confluencia")` (ou o campo equivalente já
  disponível no resultado de `detect_setups`/`sres` no ponto de chamada —
  verificar o nome exato do campo lendo `setups.py` antes de codar).
- Puramente aditivo. Não migrar/inferir esses campos em registros antigos.

### ADR15-02 — Corrigir a âncora de `_avaliar_entry`

- `analysis_outcomes.py:289-325`: `_avaliar_entry` passa a exigir que o
  preço tenha tocado o `entrada` (gatilho) antes de abrir a barreira tripla;
  usa `entrada` como `preco0`, não `close`.
- **Retrocompatibilidade obrigatória**: registros gravados antes desta
  mudança não têm `entrada` (são da metodologia antiga, ADR15-01 ainda não
  existia para eles). Adicionar um campo de versão de metodologia ao
  registro (ex. `metodologiaVersao: 1` para o formato antigo, `2` para o
  novo) OU tratar `entrada is None` como "não avaliável pela metodologia
  nova, mantém resultado antigo mas marca `metodologiaAntiga: true`" — a
  escolha exata de schema fica a critério do planner/executor, mas o
  requisito duro é: **`compute_stats`/`compute_stats_all_users` NUNCA
  misturam outcomes calculados pelas duas metodologias no mesmo agregado**
  sem sinalizar isso explicitamente no resultado.
- Não alterar `main.py:1313-1327`/`1416-1432` além do que ADR15-01 já pede
  (não introduzir uma segunda mudança de comportamento no mesmo call site
  fora do escopo mapeado).

### ADR15-03 — Deduplicar por `snapshotId`

- `analysis_outcomes.py:230-242` (`compute_stats_all_users`, e a função
  auxiliar `_scopes_com_outcomes`/agregação): antes de agregar, deduplicar
  outcomes pelo `snapshotId` (campo já gravado hoje, `main.py:1318`) — um
  mesmo `snapshotId` conta como 1 observação, não N.
- Verificado no ADR-015: um plano chegou a ser gravado 24x (dev) e 12x
  (produção) pelo mesmo `snapshotId`/plano determinístico. Sem dedup,
  `MIN_N=10` (`analysis_outcomes.py:34`) não protege de nada.
- `compute_stats` (função pura, não-agregada) não precisa mudar — o dedup é
  responsabilidade da camada de agregação cross-scope.

### ADR15-04 — `motivo` em `store.sell()`

- `store.py:621`: `sell()` ganha parâmetro `motivo: str = "manual"`, mesmo
  contrato de `sell_option()` (`store.py:704-715`): valores
  `'manual'|'stop'|'alvo'|'vencimento'`.
- `agent.py:838` já calcula `motivo = "stop atingido" if breach_stop else
  "alvo atingido"` — hoje usado só no texto do Diário. Os 3 call sites
  automáticos do Operador em `agent.py` (ex. `agent.py:852`) passam esse
  motivo real para `store.sell(...)` (mapear para os valores curtos
  `'stop'`/`'alvo'`, não a frase longa do Diário).
- Chamadas manuais (`main.py`, rota `/api/sell`) continuam com
  `motivo="manual"` (default) — não pedir ao usuário para classificar o
  motivo na venda manual.

### ADR15-05 — Consolidar `RR_MIN`

- Fonte única: `skill_ref.RR_MIN` (`skill_ref.py:30`, já vale 1.5).
- `setups.RR_MINIMO` (`setups.py:559`) e `agent.RR_MINIMO` (`agent.py:446`)
  passam a importar de `skill_ref` em vez de declarar a própria constante.
- Os 7 literais hardcoded no front (`web/src/copy.js:134,147`,
  `web/src/catalog.js:45,100,147`, `web/src/App.jsx:4009,4347`) — decisão de
  implementação do executor: idealmente uma constante única exportada
  (ex. `web/src/finance.js` ou `catalog.js`) que os 3 arquivos importam, no
  padrão que o resto do front já usa para constantes compartilhadas.
- Guardião de teste cruzado: estender/criar teste que falha se
  `setups.RR_MINIMO`, `agent.RR_MINIMO` ou a constante do front divergirem
  de `skill_ref.RR_MIN` — hoje só `test_auditoria_prompts.py:167-172` trava
  `skill_ref`, os outros 2 motores e o front não têm rede de segurança.
- **Não mudar o valor numérico** (continua 1.5) — esta fase é sobre
  consolidar a fonte, não sobre decidir um novo limiar de R:R.

### Claude's Discretion

- Nome exato do campo de "versão de metodologia" em ADR15-02 (schema).
- Onde exatamente colocar a constante única de RR_MIN no front (ADR15-05) —
  desde que seja uma única fonte importada nos 3 lugares, não 3 valores
  independentes.
- Ordem de execução das 5 tasks dentro da fase (não há dependência dura
  entre elas exceto: ADR15-02 pressupõe que `entrada` já esteja disponível
  no plano — que já é o caso hoje, `setups.py:602-612` — então ADR15-01 e
  ADR15-02 podem ser a mesma wave ou waves adjacentes).

</decisions>

<specifics>
## Specific Ideas

Números que provam o problema (citar em teste/PR, não re-medir do zero):
em dev, 11 planos avaliados pela metodologia atual deram placar 5 stop / 3
alvo e expectância +2,56R (n=44, com duplicatas) / +0,60R (n=8, sem
duplicatas); a metodologia corrigida nos MESMOS planos deu 3 stop / 3 alvo
e 0,00R (n=6). Isso é o "antes/depois" que qualquer teste de regressão para
`_avaliar_entry` deveria conseguir reproduzir com um fixture pequeno.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Diagnóstico e decisão
- `docs/adr/015-assertividade-do-motor-de-recomendacao.md` — ADR completo:
  diagnóstico, alternativas, recomendação. Fonte de verdade desta fase.
- `.planning/quick/260820-0hl-pesquisa-e-design-assertividade-do-motor/260820-0hl-RESEARCH.md`
  — pesquisa original com todas as citações arquivo:linha e a prova
  numérica do defeito (§2.4, §2.5).

### Código a modificar
- `server/app/analysis_outcomes.py` — `registrar()` (linha ~60), `_avaliar_entry()`
  (linhas 289-325), `compute_stats_all_users()` (linhas 230-242).
- `server/app/main.py` — linhas 1311-1327 (N1) e 1416-1432 (N2), os dois
  call sites de `analysis_outcomes.registrar`.
- `server/app/store.py` — `sell()` (linha 621), `sell_option()` (linha
  704-715, referência de contrato a replicar).
- `server/app/agent.py` — linha 838 (cálculo de `motivo`), linha ~852 (call
  site de `store.sell` a atualizar), linha 446 (`RR_MINIMO`).
- `server/app/setups.py` — linha 559 (`RR_MINIMO`), linhas 602-632
  (geometria do plano — NÃO MODIFICAR, só ler para confirmar que `entrada`
  já existe no dict `plano`).
- `server/app/skill_ref.py` — linha 30 (`RR_MIN`, fonte única já existente).
- `web/src/copy.js` (linhas 134, 147), `web/src/catalog.js` (linhas 45, 100,
  147), `web/src/App.jsx` (linhas 4009, 4347) — literais de RR a
  consolidar.
- `server/tests/test_auditoria_prompts.py` — linha 167-172, teste guardião
  existente de `skill_ref.RR_MIN` a estender para os outros 2 motores + front.

### Guardrails do projeto (não re-litigar)
- CLAUDE.md do repo — Princípio 5 (cálculo por regra, nunca pela IA) e
  guardrail CVM: NENHUMA task desta fase pode mover cálculo de determinístico
  para julgamento de IA. Todas as 5 correções são código medindo/registrando
  código, não decidindo.
- CLAUDE.md do repo — paridade obrigatória `server/app/defaults.py` ↔
  `web/src/catalog.js` e `deviceStore` ↔ `serverStore`: se alguma mudança
  desta fase tocar `catalog.js`, checar se `defaults.py` tem par
  equivalente (não deveria, RR_MIN não é um prompt, mas confirmar antes).
- Suíte canônica obrigatória antes de fechar: `bash scripts/executar.sh --testes`
  (pytest backend + `web/tests/*.mjs`) — `scripts/test.sh` sozinho não conta.

</canonical_refs>

<deferred>
## Deferred Ideas

- Alternativa 2 do ADR-015 (backtest determinístico com walk-forward) —
  fase futura, depende desta fase estar em produção primeiro.
- Alternativa 3 (TradingView) — rejeitada, não deferida (não faz parte do
  backlog).
- Mudar o valor numérico de RR_MIN (ex. subir para 2:1) — decisão de
  produto separada, esta fase só consolida a fonte.
- Instrumentar `resultado="ambiguo_stop"` para empate intrabar (I2 da
  pesquisa) — mencionado na pesquisa como melhoria futura, não é um dos 5
  requirements desta fase.

</deferred>

<scope_fence>
## Scope Fence

**Dentro do escopo:** as 5 correções ADR15-01..05, testes unitários/de
regressão para cada uma, e o guardião cruzado de RR_MIN.

**Fora do escopo — não fazer nesta fase:**
- Qualquer mudança em `setups.py` além de trocar a fonte de `RR_MINIMO`
  (não tocar `_confluencia`, `plano_operacional`, `detect_setups`).
- Qualquer mudança em `regime.py` (achado I4/addendum do ADR-015 é sobre
  falta de dado, não sobre bug de código — nada a corrigir lá).
- Backtest, walk-forward, ou qualquer coisa de fonte de dado nova
  (TradingView).
- Mudança visual/UX no painel "Eficiência da IA" — o número que ele mostra
  vai mudar como consequência de ADR15-02/03, mas o componente React em si
  não precisa de trabalho nesta fase.

</scope_fence>

---

*Phase: 06-instrumentacao-assertividade-adr015*
*Context gathered: 2026-08-20 via leitura direta do ADR-015 (parser automático não reconheceu o formato)*
