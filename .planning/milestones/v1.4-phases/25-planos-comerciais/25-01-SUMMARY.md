---
phase: 25-planos-comerciais
plan: 01
subsystem: api
tags: [metering, plan, freemium, analytics, guardioes, ast, fastapi]

requires:
  - phase: 24-aba-opcoes-mcp
    provides: "24-16 (precedencia BYOK -> plano -> metering em `_gate_analise`) e 24-17 (plano da conta mutavel pelo portal) — este plano conserta o CONTADOR que aquele gate le"
provides:
  - "telemetria com ledger mensal proprio (`analyticsEventsMonth`) — o contador do gate comercial volta a medir analise"
  - "medicao do impacto de ligar o gate mensal nas tres rotas orfas, com a ativacao devolvida como decisao do dono do produto"
  - "guardiao de `month_section` varrendo `server/app/*.py` inteiro, com sanidade que reprova o `consume` pelado"
  - "`metering.snapshot` com `month_section` — dia e mes do mesmo dominio"
  - "`test_contador_mensal.py`: o guardiao do que o contador SIGNIFICA"
affects: [25-02-catalogo-de-planos, 25-03-gates-leem-o-plano, 25-05-plano-visivel-no-app]

tech-stack:
  added: []
  patterns:
    - "`month_section` explicita em TODO `metering.consume`, inclusive quando o balde escolhido e o default"
    - "`xfail(strict=True)` para travar comportamento-alvo pendente de decisao: no dia da ativacao o teste FALHA por XPASS, obrigando a tirar a marca"

key-files:
  created:
    - server/tests/test_contador_mensal.py
  modified:
    - server/app/main.py
    - server/app/metering.py
    - server/tests/test_mcp_guardioes.py

key-decisions:
  - "A ativacao do gate mensal nas tres rotas orfas NAO foi feita — medida e devolvida ao Alex (guardrail explicito do plano)"
  - "`metering.snapshot` ganhou `month_section` em vez de derivar o mes de `section`: as chaves de kv sao independentes, derivar seria adivinhar convencao"
  - "`_ai_apply_managed` declara `month_section=metering.MONTH_SECTION`: o balde nao muda, o que muda e ter sido escolhido"
  - "Os nomes `analyticsEvents`/`analyticsEventsGlobal` NAO mudaram de valor — ha contador gravado no kv sob eles"

patterns-established:
  - "Guardiao geral (todo consume declara) + guardiao especifico (o do MCP e `mcpUsageMonth`) convivem — guardiao nao se afrouxa ao ser generalizado"
  - "Semear ledger mensal em teste usa `_dia` no passado: `consume` grava dia+mes juntos e o cap diario mascara o comercial (os dois 402 sao indistinguiveis pelo status)"

requirements-completed: []

duration: 95min
completed: 2026-09-12
---

# Phase 25 Plan 01: Conserto do contador mensal — Summary

**A telemetria parou de comer a cota de analises do plano free (media: 100% do
contador do mes era telemetria, 0% era analise), e a ativacao do gate nas tres
rotas orfas foi medida e devolvida como decisao do Alex em vez de ligada sobre
um contador contaminado.**

## Performance

- **Duration:** ~95 min
- **Started:** 2026-09-12T16:20Z
- **Completed:** 2026-09-12T17:55Z
- **Tasks:** 3 de 3 (Task 2 concluida como MEDICAO + PARADA, por desenho do plano)
- **Files modified:** 4 (3 modificados, 1 criado)

## Accomplishments

- **O defeito 1 esta fechado.** `POST /api/analytics/events` tem ledger mensal
  proprio. O contador que `plan.can_analyze` le volta a significar "analises de
  IA gerenciada", e so isso.
- **O defeito 2 esta medido e documentado, nao ligado.** A medicao mostrou que
  ligar hoje barraria conta pelo residuo do defeito 1, nao por uso.
- **A porta por onde o defeito entrou esta fechada.** O guardiao de
  `month_section` deixou de varrer um arquivo so e passou a varrer
  `server/app/*.py` inteiro, com prova por injecao.

## Task Commits

1. **Task 1: telemetria para de consumir cota de analise** — `7ffa86a` (fix)
2. **Task 2: as tres rotas orfas medidas; ativacao devolvida ao Alex** — `5dbba1a` (test)
3. **Task 3: guardiao generalizado + `snapshot` sem baldes misturados** — `df27bec` (test)

**Plan metadata:** (commit final deste SUMMARY)

## Files Created/Modified

- `server/app/main.py` — tres constantes de secao de analytics;
  `month_section=ANALYTICS_MONTH_SECTION` no `consume` da rota de telemetria;
  `month_section=metering.MONTH_SECTION` explicita no `_ai_apply_managed`.
- `server/app/metering.py` — `snapshot()` ganhou `month_section`, propagado a
  `_load_month`.
- `server/tests/test_mcp_guardioes.py` — guardiao geral sobre todo `app/*.py`,
  helpers `_chamadas_a_metering_consume` / `_resolve_month_section`, e um teste
  de sanidade do proprio guardiao.
- `server/tests/test_contador_mensal.py` (novo) — 9 casos verdes + 3
  `xfail(strict=True)` que descrevem o estado-alvo pendente de decisao.

## A medicao da Task 2 (o que o plano exigia antes de ativar)

Diagnostico **somente leitura** sobre `server/data/b3_agente.db` e
`analytics.db` (nenhuma escrita; nenhum e-mail, token ou chave impresso):

| metrica | valor |
|---|---|
| contas no banco | 7.273 (todas `free`) |
| contas com ledger mensal em 2026-09 | **3** |
| contas acima do limite de 30 | **2** |
| dessas, com BYOK (atravessariam o gate) | 0 |

E o dado que decide:

| conta | `aiUsageMonth.count` | eventos de telemetria ingeridos no mes |
|---|---|---|
| `3857e04a…` | 4.167 | **4.167** |
| `aef503cd…` | 2.348 | **2.348** |
| `152419ba…` | 25 | **25** |

Os tres contadores batem **exatamente** com a telemetria. Ou seja: **100% do
ledger mensal da base era telemetria e 0% era analise.** O defeito nao e uma
contaminacao parcial — ele e o contador inteiro.

**Ressalva que nao pode ser omitida:** este banco e de **teste** (7.146 contas
`@teste.com`, todas `provider=email`, criadas entre 2026-09-05 e hoje), nao
producao. Producao nao e acessivel daqui, e o numero acima **nao e** o numero
de producao. O que transfere e a **estrutura**, e ela transfere com forca: o
cliente envia telemetria em lotes de ate 50 (`web/src/analytics.js`), cada lote
somava o lote inteiro, e uma analise soma 1. Qualquer conta que use o app
acumula muito mais telemetria do que analise. O backup de 2026-09-07 mostra as
MESMAS tres contas com 4.158/2.338/25 — o contador so cresce.

### Por que a ativacao NAO foi feita

O plano manda parar se a amostra for relevante. Ela e — e pela pior razao
possivel: **as duas contas que seriam barradas sao barradas pelo defeito, nao
pelo uso.** Consertar o defeito (Task 1) para o crescimento, mas **nao apaga o
residuo ja gravado**: o registro do mes corrente so zera na virada de mes
(UTC). Ligar o gate hoje estenderia uma barreira espuria a mais tres
superficies — inclusive o assistente, que hoje responde.

Ha um indicio forte de que producao esta no mesmo estado: o 24-16 nasceu de um
bloqueio real da conta do Alex em "30/30 analises do mes". Com o que foi medido
aqui, e plausivel que aquelas 30 fossem telemetria.

**A decisao e do Alex.** As opcoes, com o custo de cada uma:

| opcao | ganho | preco |
|---|---|---|
| **A — ativar agora** | as tres rotas param de furar o cap por omissao | barra hoje as contas contaminadas (provavelmente a do proprio Alex) no assistente, no stop/alvo e no Radar profundo, ate a virada do mes |
| **B — ativar junto com a Fase 2** (o 25-CONTEXT ja preve) | ativa sobre contador limpo e com limites ja configuraveis | as tres rotas seguem gastando IA acima do cap por mais um ciclo |
| **C — ativar agora + zerar o residuo do mes** | resolve os dois lados de uma vez | e **migracao de dado** — escreve num contador de dinheiro; fora do escopo deste plano e decisao propria |

**Recomendacao:** B. O vazamento que a nao-ativacao deixa aberto ja existe hoje
e e limitado pelo teto FISICO (20/dia da chave do servidor, `metering.check`,
que essas rotas **ja** respeitam). O preco da opcao A e uma regressao visivel
para o usuario, causada por dado que sabemos estar errado.

O estado pendente ficou **codificado na suite**, nao so em prosa: os tres casos
estao como `xfail(strict=True)`. No dia da ativacao eles viram XPASS e
**falham**, obrigando quem ativar a tirar a marca. Esquecer nao e possivel.

## Decisoes Made

1. **Nao ativar o gate nas tres rotas** (acima). Devolvida ao Alex.
2. **`snapshot` ganhou parametro em vez de derivar o mes de `section`.** As
   duas chaves de kv sao independentes em todos os dominios
   (`SECTION`/`MONTH_SECTION`); derivar `"analyticsEvents" + "Month"` seria
   adivinhar uma convencao que nenhum chamador promete.
3. **`_ai_apply_managed` declara o balde default explicitamente.** O valor nao
   muda — ali o ledger comercial e o correto, porque essa E a analise que o
   plano cobra. O que muda e ter sido escolhido, e e o que o guardiao exige.
4. **Os dois nomes de secao antigos nao mudaram de valor.** Ha contador gravado
   no kv sob eles; renomear perderia o historico de quem ja usa o app.

## Diagnostico corrigido no caminho

O enunciado do plano (e o do 25-CONTEXT) diz que as tres rotas "gastam IA sem
contar onde o plano le". **Isso esta errado e a correcao importa para a Fase
2.** O `consume` devolvido por `_ai_apply_managed` usa o `MONTH_SECTION`
default, entao as tres rotas **ja escrevem** no ledger que o plano le. O
defeito e a ausencia do **GATE**, nao da contagem: elas gastam acima do cap,
registram o excesso e nao sao barradas. Ha teste dedicado a isso
(`test_as_tres_rotas_ja_CONTAM_no_ledger_mensal_hoje`), verde hoje.

Consequencia pratica: a Fase 3 nao precisa acrescentar contagem a essas rotas,
so o gate.

## RED medido antes de cada correcao

| correcao | RED |
|---|---|
| Task 1 — telemetria | `assert 50 == 0` em `test_lote_de_analytics_nao_move_o_contador_mensal` (4 failed) |
| Task 2 — as tres rotas | `/api/scan/deep` respondeu **200** com o mes em 100/30; `/api/carteira-stopalvo` e `/api/assistente` **chamaram a IA** com o mes estourado (o stub que grita "a IA foi chamada com o mes estourado" foi alcancado nos dois) |
| Task 3 — guardiao geral | injecao real de `metering.consume(_conn, uid, custo=50)` no fim de `main.py`: guardiao reprovou apontando `('main.py', 4027)`; arquivo restaurado de copia e diff conferido |
| Task 3 — `snapshot` | `TypeError: snapshot() got an unexpected keyword argument 'month_section'` |

## Deviations from Plan

### 1. [Processo] `test_contador_mensal.py` nasceu na Task 1, nao na Task 3

- **Found during:** Task 1
- **Issue:** O plano lista o arquivo em `<files>` da Task 3, mas a acao da Task
  3 exige "cada um provado RED **antes** da correcao" — o que e impossivel se o
  arquivo so existir depois das correcoes.
- **Fix:** O arquivo foi criado na Task 1 com o caso da telemetria (RED real
  contra o codigo anterior) e cresceu nas Tasks 2 e 3. Cumpre a regra mais
  forte; o arquivo final e o que o plano pediu.
- **Verification:** Cada commit carrega o RED que mediu.

### 2. [Rule 1 - Bug] O teste das tres rotas media o teto ERRADO

- **Found during:** Task 2
- **Issue:** Semear o ledger com `consume(custo=100)` leva o contador **diario**
  junto (a funcao grava dia + global + mes na mesma chamada). Com a IA
  gerenciada ligada, a rota respondia 402 pelo teto **fisico** de 20/dia da
  chave do servidor. Os dois 402 sao indistinguiveis pelo status — o teste
  estaria verde medindo outra coisa.
- **Fix:** O helper semeia com `_dia` no passado (o registro diario nasce
  obsoleto e `_load` devolve zerado para hoje) e **afirma** que o ledger diario
  ficou limpo. Os cenarios das tres rotas rodam sem IA gerenciada, para que o
  unico 402 possivel seja o comercial.
- **Files modified:** `server/tests/test_contador_mensal.py`
- **Committed in:** `5dbba1a`

### 3. [Rule 3 - Bloqueio] Disco cheio interrompeu a suite

- **Found during:** Task 2
- **Issue:** `sqlite3.OperationalError: disk I/O error` em todos os casos. A
  causa nao era o codigo: 120 MiB livres num disco de 460 GiB.
- **Fix:** Removida a copia temporaria de 27 MB do backup que este trabalho
  criou em `$TMPDIR`. Espaco de volta (12 GiB), suite verde.
- **Nota para o Alex:** o disco esta em 98%. Nao foi este trabalho que o
  encheu — vale uma limpeza fora daqui.

---

**Total deviations:** 3 (1 de processo, 1 Rule 1, 1 Rule 3). Nenhuma alterou
escopo nem limite.

## Verificacao

```
bash scripts/executar.sh --testes   (FORA do sandbox)
2576 passed, 5 skipped, 3 xfailed, 785 warnings in 66.42s
131 arquivos web/tests/*.mjs [OK]
EXIT=0
```

Baseline `2565 passed, 5 skipped` + 131 `.mjs` **preservada**: +11 passed e +3
xfailed sao exatamente os 14 casos novos deste plano (12 em
`test_contador_mensal.py`, 2 em `test_mcp_guardioes.py`).

Nenhum arquivo de `web/` tocado — `vite build` nao se aplica.

## Zero mudanca de politica

- `server/app/plan.py` — **intacto** (nao aparece no diff de nenhum commit).
- Limites: 30 analises/mes no free, 20/dia da gerenciada, 15k/mes da brapi —
  **todos iguais**.
- Nenhuma secao de kv renomeada; uma criada (`analyticsEventsMonth`).
- `metering.consume` e `metering.check` sem mudanca de assinatura ou semantica.

## Issues Encountered

Nenhum alem dos tres desvios acima.

## User Setup Required

Nenhum. Sem env nova, sem servico externo.

**Mas nao esta no ar.** E mudanca de backend: exige deploy com bump manual de
`SERVER_BUILD_ID`. Ate la, producao continua descontando telemetria da cota de
analise de quem usa o app.

## Next Phase Readiness

Pronto para a Fase 1 (papel `owner`) e para a Fase 2 (catalogo de planos), com
duas ressalvas que a Fase 2 herda:

1. **A ativacao do gate nas tres rotas segue aberta** e o 25-CONTEXT ja preve
   ativa-la junto com os limites configuraveis da Fase 2 (opcao B). Os tres
   `xfail(strict=True)` sao o marcador.
2. **O residuo do mes corrente** (contadores ja gravados com telemetria) so
   desaparece na virada de mes, ou por decisao explicita de limpeza. Qualquer
   coisa que a Fase 2 configure sobre o mes de setembro configura sobre esse
   residuo.

Um terceiro ponto, herdado e agora com evidencia: o ledger mensal usa **UTC**
(`metering.py`), enquanto a aba Opcoes usa Sao Paulo e a brapi usa BRT. Um
limite "por mes" configuravel na Fase 2 precisa dizer **qual mes**.

---
*Phase: 25-planos-comerciais*
*Completed: 2026-09-12*

## Self-Check: PASSED

- `server/tests/test_contador_mensal.py` — FOUND
- `.planning/phases/25-planos-comerciais/25-01-SUMMARY.md` — FOUND
- commits `7ffa86a`, `5dbba1a`, `df27bec` — FOUND
- `server/app/plan.py` fora do diff dos tres commits (0 linhas) — nenhuma
  politica alterada
- `SERVER_BUILD_ID`, `web/src/version.js`, `server/web_dist` e
  `server/admin_dist` fora do diff — nenhum carimbo tocado
- diff total: 4 arquivos, +512/-23
