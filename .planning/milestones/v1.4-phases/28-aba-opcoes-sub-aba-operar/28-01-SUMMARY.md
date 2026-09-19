---
phase: 28-aba-opcoes-sub-aba-operar
plan: 01
subsystem: ui
tags: [react, jsx, refactor, opcoes, adr-027]

# Dependency graph
requires:
  - phase: 27-aba-opcoes-sobre-carteira
    provides: universo de "Operar" = carteira (ctx.data.positions), leitura técnica interna
provides:
  - "web/src/opcoes/PropostaLastreada.jsx — módulo compartilhado (FonteDoDadoProposta, ChipDaProposta, useAceiteLastreado, PropostaLastreada default) que App.jsx e a futura sub-aba Operar podem importar sem ciclo"
  - "ADR-027 Emenda 3 exercitada em código: isolamento de duas vias entre App.jsx e OpcoesScreen.jsx via módulo terceiro"
affects: [28-02-sub-aba-operar-ui, 28-03-remocao-card-watchlist-radar]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Módulo de UI compartilhado em web/src/opcoes/ com bloco VARKEY/TOKENS/T local (espelha var(--x) do :root), em vez de importar App.jsx — mesmo padrão de OpcoesScreen.jsx/SetupChart.jsx, generalizado para um componente de apresentação"
    - "Hook de caminho de aceite/fechamento (useAceiteLastreado) como unidade de extração para lógica de handler + estado local (busy), em vez de expor funções soltas"

key-files:
  created:
    - web/src/opcoes/PropostaLastreada.jsx
  modified:
    - web/src/App.jsx
    - web/tests/test_opcoes_proposta_ui.mjs
    - web/tests/test_opcoes_multi_candidato_ui.mjs
    - web/tests/test_faixa_liquidez_ui.mjs
    - web/tests/test_carteira_opcoes_tira.mjs
    - web/tests/test_opcoes_mcp_aba_ui.mjs
    - web/tests/test_opcoes_collar_ui.mjs

key-decisions:
  - "AtivoCard (Watchlist/Radar) NÃO foi tocado — continua com a cópia antiga não-parametrizada de onAbrirLastreada/onFecharLastreada; a remoção é do plano 28-03, de propósito, para manter a suíte verde entre os dois movimentos"
  - "A asserção literal do plano ('App.jsx não importa OpcoesScreen.jsx') foi corrigida para o invariante real: App.jsx importa OpcoesScreen.jsx de propósito, para montar a aba como tela — isso não é o ciclo que a Emenda 3 proíbe. O ciclo proibido é o módulo compartilhado importar OpcoesScreen.jsx, que é o que o guardião novo mede"
  - "test_opcoes_collar_ui.mjs foi corrigido mesmo estando fora de files_modified do plano — quebrava pela mesma causa-raiz (aceitarCandidato/PropostaLastreada saíram de App.jsx) e o guardrail 'nenhum guardião apagado' se aplica independente de estar listado no frontmatter"

requirements-completed: [SC-2]

# Metrics
duration: ~75min
completed: 2026-09-13
---

# Phase 28 Plan 01: Extração de PropostaLastreada Summary

**`PropostaLastreada`/`FonteDoDadoProposta`/`ChipDaProposta` e o caminho de aceite/fechamento lastreado saíram de `App.jsx` para `web/src/opcoes/PropostaLastreada.jsx`, um módulo terceiro que os dois lados do isolamento ADR-027 podem importar sem ciclo — zero mudança de comportamento, cor, texto ou rota.**

## Performance

- **Duration:** ~75 min
- **Started:** 2026-09-13 (medição de baseline antes da primeira edição)
- **Completed:** 2026-09-13T17:45:04Z
- **Tasks:** 3/3
- **Files modified:** 8 (1 criado, 7 modificados — 6 do `files_modified` do plano + 1 guardião adicional descoberto quebrado pela mesma causa)

## Baseline medida (obrigatória pelo plano)

Medida com `bash scripts/executar.sh --testes` (fora do sandbox), ANTES de
qualquer edição:

```
2780 passed, 5 skipped, 3 xfailed, 986 warnings in 64.48s
143/143 .mjs [OK], exit 0
```

Contagem DEPOIS de todas as edições (Task 1+2+3), mesma suíte, mesmo comando:

```
2780 passed, 5 skipped, 3 xfailed, 986 warnings in 65.27s–65.57s (3 execuções)
143/143 .mjs [OK], exit 0
```

**Idêntica à baseline** — a extração não mudou a contagem de pytest, e o
número de ARQUIVOS `.mjs` (143) também não mudou (asserções novas foram
adicionadas DENTRO de arquivos existentes, não em arquivos novos). `npx vite
build` verde nas duas verificações (Task 2 e final).

## Accomplishments

- `web/src/opcoes/PropostaLastreada.jsx` criado: exporta `default`
  (`PropostaLastreada`), `FonteDoDadoProposta`, `ChipDaProposta` e
  `useAceiteLastreado` (hook novo, fusão do `useState(busy)` +
  `aceitarCandidato`/`onFecharLastreada` que viviam em `PropostaDaPosicao`).
  Corpos verbatim; a única mudança de identificador permitida (`t`→`ticker`,
  `r` do closure→parâmetro) foi aplicada e verificada.
- `App.jsx` reapontado: import do módulo, três definições locais removidas,
  `PropostaDaPosicao` consome `useAceiteLastreado({ A, cp, ticker: t })` em
  vez de declarar os handlers localmente. `AtivoCard` (Watchlist/Radar)
  intocado de propósito — fica para o 28-03.
- Seis guardiões de teste reapontados para ler o módulo onde a definição
  migrou, com nota datada em cada mudança — nenhuma asserção apagada.
- Guardião novo (T-28-05): as quatro linhas de formatador (`MONO`, `nf2`,
  `price`, `FONTE_LABEL`) são comparadas caractere a caractere entre
  `App.jsx` e o módulo — **provado por injeção de defeito** (espaço extra em
  `price` → suíte sai com exit 1; revertido via `git checkout --`).
- Guardião novo (T-28-06): `PropostaLastreada.jsx` não importa
  `OpcoesScreen.jsx` (a metade do invariante de duas vias da Emenda 3 que
  ainda não estava coberta pelo loop de isolamento existente).

## Task Commits

1. **Task 1: Criar web/src/opcoes/PropostaLastreada.jsx** - `e997867` (feat)
2. **Task 2: Reapontar App.jsx para o módulo** - `b0b1b5b` (refactor)
3. **Task 3: Reapontar guardiões de teste** - `68f721a` (test)

_Sem plano de publicação: `commit_docs=true`, mas STATE.md/ROADMAP.md ficam
para o orquestrador atualizar à mão, por convenção deste repositório
(gsd-sdk `state.*`/`roadmap.*` mutators proibidos — ver CLAUDE.md)._

## Files Created/Modified

- `web/src/opcoes/PropostaLastreada.jsx` - módulo novo: os três componentes
  extraídos + `useAceiteLastreado`
- `web/src/App.jsx` - import do módulo; remoção das três definições locais;
  `PropostaDaPosicao` usa o hook
- `web/tests/test_opcoes_proposta_ui.mjs` - guardião principal reapontado +
  guardião novo de igualdade de formatadores (T-28-05)
- `web/tests/test_opcoes_multi_candidato_ui.mjs` - item (10) medido pela
  implementação única no módulo
- `web/tests/test_faixa_liquidez_ui.mjs` - fronteira de fatia trocada
  (`FonteDoDadoProposta`→`OpcoesCamada`); handlers de aceite lidos de duas
  fontes
- `web/tests/test_carteira_opcoes_tira.mjs` - assinatura de
  `PropostaLastreada` lida do módulo
- `web/tests/test_opcoes_mcp_aba_ui.mjs` - módulo entra no loop de
  isolamento ADR-027; guardião novo T-28-06
- `web/tests/test_opcoes_collar_ui.mjs` - **fora de `files_modified` do
  plano**, corrigido por quebrar pela mesma causa (ver Deviations)

## Decisions Made

- **AtivoCard fica intocado neste plano** (decisão do próprio plano,
  confirmada em execução): a cópia antiga e não-parametrizada de
  `onAbrirLastreada`/`onFecharLastreada` continua em `App.jsx`, com
  `A.abrirLastreada(`/`A.abrirCollar(`/`A.fecharLastreada(` aparecendo
  exatamente 1× cada em `App.jsx` (as definições no objeto `A`, linhas
  ~8512-8540, continuam intactas). Remoção é do plano 28-03.
- **Correção do texto literal do plano para o guardião T-28-06** (ver
  Deviations abaixo — não é decisão de produto, é correção de um enunciado
  de teste que seria falso contra o código real).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Enunciado do guardião T-28-06 corrigido (asserção que seria falsa)**
- **Found during:** Task 3 (`test_opcoes_mcp_aba_ui.mjs`)
- **Issue:** O plano pedia literalmente a asserção "App.jsx não importa
  OpcoesScreen.jsx". Isso é falso no código real: `App.jsx:12` importa
  `OpcoesScreen` DE PROPÓSITO, para montar a aba como tela
  (`<OpcoesScreen ... />`) — é composição pai→filho normal, não o ciclo que
  a Emenda 3 proíbe. Escrever a asserção como pedida teria criado um
  guardião permanentemente vermelho contra uma importação legítima e
  necessária.
- **Fix:** Implementado o invariante REAL de duas vias para o módulo
  COMPARTILHADO: `PropostaLastreada.jsx` não importa `App.jsx` (já coberto
  pelo loop de isolamento existente, agora incluindo o módulo) nem
  `OpcoesScreen.jsx` (asserção nova). A ausência de ciclo entre `App.jsx` e
  `OpcoesScreen.jsx` já era garantida pela asserção pré-existente
  "`OpcoesScreen.jsx` não importa `App.jsx`" — a direção `App.jsx`→
  `OpcoesScreen.jsx` é composição, não ciclo.
- **Files modified:** `web/tests/test_opcoes_mcp_aba_ui.mjs`
- **Verificação:** `node web/tests/test_opcoes_mcp_aba_ui.mjs` passa; a
  asserção nova falharia se `PropostaLastreada.jsx` importasse
  `OpcoesScreen.jsx` (inspeção manual do regex).
- **Committed in:** `68f721a`

**2. [Rule 1 - Bug] test_opcoes_collar_ui.mjs corrigido fora de files_modified**
- **Found during:** Task 3, ao rodar a suíte canônica completa após editar
  só os cinco arquivos listados no `files_modified` do plano
- **Issue:** `test_opcoes_collar_ui.mjs` (Fase 17) tinha os MESMOS dois
  padrões quebrados dos arquivos já corrigidos — um bloco de "2 handlers de
  aceite" contando `aceitarCandidato` em `app` (que não existe mais lá) e
  uma fatia `PropostaLastreada`↔`OpcoesCamada` dentro de `App.jsx` (também
  não existe mais lá). Não estava no `files_modified` do plano porque o
  plano não previu este arquivo, mas a regra "guardião não se apaga" e o
  guardrail de suíte verde se aplicam independente do que está listado no
  frontmatter.
- **Fix:** Mesma técnica dos outros cinco arquivos — handlers de aceite
  passam a ser coletados de duas fontes (`App.jsx` para
  `onAbrirLastreada`, o módulo para `aceitarCandidato`); a fatia de
  `PropostaLastreada` passa a vir do módulo (é o último componente do
  arquivo, a fatia vai até o fim).
- **Files modified:** `web/tests/test_opcoes_collar_ui.mjs`
- **Verificação:** `node web/tests/test_opcoes_collar_ui.mjs` passa (36
  asserções, nenhuma removida — contagem de linhas com `ok(` foi de 30 para
  30, substituição 1-para-1).
- **Committed in:** `68f721a`

---

**Total deviations:** 2 auto-fixed (2× Rule 1 — ambos correções de guardião
de teste causadas diretamente pela extração, não bugs de produto)
**Impact on plan:** Nenhum impacto em comportamento de produto. Os dois
desvios são exclusivamente sobre a EXATIDÃO dos guardiões de teste —
essenciais para que "suíte verde" continue significando "nada quebrou", não
"os testes pararam de medir a coisa certa". Sem scope creep: nenhum código
de produto foi tocado além do que o plano já previa (Tasks 1 e 2).

## Issues Encountered

- Ao provar o guardião de igualdade de formatadores (T-28-05) por injeção de
  defeito, o primeiro `cp`/revert falhou por um path de backup em `$TMPDIR`
  que não existia (o `TMPDIR` resolvido difere entre chamadas de shell
  sandboxed vs. não-sandboxed neste ambiente). Resolvido com
  `git checkout -- web/src/opcoes/PropostaLastreada.jsx` (o arquivo já
  estava commitado no estado correto pela Task 1) — sem risco, porque a
  Task 2 não tocou esse arquivo.
- `npx vite build` regenerou `web/dist` (gitignorado) com hashes de chunk
  novos, sob o MESMO `BUILD_ID` do último `server/web_dist` publicado
  (ninguém bumpou o carimbo nesta sessão — publicação é fora de escopo
  desta fase). Isso fez `test_ios_assets.mjs` reprovar a paridade
  dist↔ios-bundle (mesmo carimbo, chunks diferentes — exatamente a
  "amputação" que aquele guardião existe para pegar, mas aqui é
  meio-de-build local, não publicação real). Resolvido restaurando
  `web/dist` a partir de `server/web_dist` depois do build — mesmo padrão
  documentado em várias entradas do `STATE.md` (Fases 24/25). Nenhum
  arquivo versionado foi tocado (`web/dist` é gitignorado); a verificação
  "`npx vite build` passa sem erro" já tinha sido satisfeita antes da
  restauração.

## Known Stubs

Nenhum. A extração não introduziu dado vazio/placeholder — os três
componentes e o hook continuam lendo props reais (`r`, `cp`, `A`) fornecidas
pelos consumidores, exatamente como antes.

## Threat Flags

Nenhuma superfície nova. A extração moveu componentes de apresentação e um
hook de handler de clique entre arquivos do mesmo bundle front-end — nenhum
endpoint, caminho de auth, acesso a arquivo ou schema novo. O `threat_model`
do próprio plano (T-28-01 a T-28-07) já cobre os riscos reais da mudança
(cópia fiel do caminho de aceite, ordem dos `window.confirm`, split de modo,
manchete verbatim, divergência de formatador, ciclo de import, guardião
apagado) — todos com mitigação verificada acima.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Next Phase Readiness

- `web/src/opcoes/PropostaLastreada.jsx` está pronto para ser importado
  pela sub-aba "Operar" (plano 28-02) sem criar ciclo com `App.jsx`.
- O plano 28-03 (remoção do card duplicado em `AtivoCard`/Watchlist/Radar)
  pode prosseguir: os pontos de uso remanescentes em `App.jsx`
  (`<PropostaLastreada` 2×, `A.abrirLastreada(`/`A.abrirCollar(`/
  `A.fecharLastreada(` 1× cada, todos em `AtivoCard`) estão identificados e
  isolados — nenhum deles foi tocado por este plano.
- Nenhum bloqueio conhecido. Publicação continua fora de escopo desta fase
  (nada foi commitado em `server/web_dist`/`version.js`/`SERVER_BUILD_ID`).

## Self-Check: PASSED

Todos os arquivos criados/modificados encontrados no disco; os três hashes
de commit (`e997867`, `b0b1b5b`, `68f721a`) encontrados em `git log --oneline
--all`. Suíte canônica rodada 3× ao longo da execução, sempre idêntica à
baseline (2780 passed, 5 skipped, 3 xfailed + 143/143 `.mjs`, exit 0).

---
*Phase: 28-aba-opcoes-sub-aba-operar*
*Completed: 2026-09-13*
