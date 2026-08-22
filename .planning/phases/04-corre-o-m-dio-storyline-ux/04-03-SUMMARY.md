---
phase: 04-corre-o-m-dio-storyline-ux
plan: 03
subsystem: ui
tags: [react, wcag-aa, accessibility, contrast, accordion, keyboard, onboarding-nudge]

# Dependency graph
requires: []
provides:
  - "textFaint em PALETTE/MODE_OPERADOR passa WCAG AA (4.5:1) nas 3 superfícies (bgBase/bgPanel/bgCard), nos 2 temas x 2 modos"
  - "OpcaoContrato e OpcoesCamada (acordeão de opções) respondem a Enter/Espaço e anunciam aria-expanded"
  - "Painel de prontidão pedagógica em ModoTrabalhoCard (nudge soft, nunca bloqueio) antes da transição Estudo→Operador"
affects: [04-04, 04-05, 04-06, 04-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useRef para flag de dispensa lida/escrita no mesmo tick de um handler síncrono, evitando closure obsoleta de useState em chamadas recursivas ao mesmo handler"

key-files:
  created:
    - web/tests/test_acessibilidade_acordeao.mjs
    - web/tests/test_prontidao_operador.mjs
  modified:
    - web/src/App.jsx
    - web/tests/test_brand_book_v2_tokens.mjs
    - web/tests/test_copy_theme.mjs

key-decisions:
  - "chartAxis (App.jsx:81/142) NÃO foi alterado apesar de compartilhar hex antigo com textFaint por coincidência — é stroke não-textual (mesma categoria de exclusão que P.textFaint em CapitalCurve:1627), fora do escopo literal de FIX-C16"
  - "nudgeDispensado implementado como useRef, não useState (Rule 1 — bug fix): a instrução literal do plano quebraria 'Ativar mesmo assim' por causa de closure obsoleta de React"

patterns-established:
  - "Guardião estático de teclado por contagem agregada: conta toda ocorrência de role=\"button\" no arquivo e exige o mesmo número de onKeyDown/aria-expanded adjacentes — falha automaticamente se um toggle novo nascer sem teclado, sem precisar hardcodar os pontos de uso conhecidos"

requirements-completed: [FIX-C16, FIX-C15, FIX-C04]

duration: ~90min
completed: 2026-08-22
---

# Phase 4 Plan 3: Contraste, Teclado e Prontidão Pedagógica Summary

**Os 4 hex de `textFaint` corrigidos para WCAG AA real (medido nas 3 superfícies, não só bgBase), o acordeão de opções com Enter/Espaço/aria-expanded, e um aviso soft (nunca bloqueio) antes de ativar o Modo Operador sem nenhuma análise feita no Estudo.**

## Performance

- **Duration:** ~90min
- **Started:** 2026-08-22T00:38:00Z (aprox., a partir do UI-SPEC aprovado)
- **Completed:** 2026-08-22T01:52:02Z
- **Tasks:** 3/3 completas
- **Files modified:** 5 (1 fonte, 4 testes — 2 novos, 2 atualizados)

## Accomplishments
- FIX-C16: `PALETTE.dark/light.textFaint` e `MODE_OPERADOR.dark/light.textFaint` corrigidos — pior caso passou de 3,11-4,24:1 (reprovando AA) para 4,55-5,32:1 (passando), medido contra as 3 superfícies onde o token de fato renderiza (bgBase/bgPanel/bgCard), não só a única superfície que a auditoria original mediu.
- FIX-C15: os 2 únicos `role="button"` do arquivo (`OpcaoContrato`, `OpcoesCamada`) ganharam `onKeyDown` (Enter/Espaço com `preventDefault`) e `aria-expanded` — usuário de teclado/leitor de tela agora consegue abrir/fechar o acordeão de opções.
- FIX-C04: `ModoTrabalhoCard` ganhou um painel inline (não modal) que avisa quem nunca abriu uma análise no Estudo antes de deixar ativar o Operador — soft, dois botões ("Fazer uma análise no Estudo primeiro" recomendado, "Ativar mesmo assim" sempre disponível), sinal fail-open (ausência de dado nunca é lida como "nunca analisou"), gate legal (`operadorTermo`) intacto por trás.

## Task Commits

Each task was committed atomically:

1. **Task 1: textFaint acima de 4.5:1 nos 4 pares tema x modo (FIX-C16)** - `a4214dc` (fix)
2. **Task 2: Acordeão de opções responde a teclado e anuncia estado (FIX-C15)** - `7206074` (feat)
3. **Task 3: Aviso pedagógico de prontidão Estudo→Operador (FIX-C04)** - `f4570ca` (feat)

_Nenhuma task era TDD — sem commits test→feat separados._

## Files Created/Modified
- `web/src/App.jsx` — 4 hex de `textFaint` (PALETTE.dark/light, MODE_OPERADOR.dark/light) com comentário de decisão cada; `onKeyDown`/`aria-expanded` em `OpcaoContrato`/`OpcoesCamada`; painel de prontidão + sinal `nuncaAnalisou`/`prontidaoConhecida` + `nudgeDispensadoRef` em `ModoTrabalhoCard`
- `web/tests/test_brand_book_v2_tokens.mjs` — `NEUTROS.dark/light.textFaint` atualizado com nota; seção 5 estendida com loop de `textFaint` contra as 3 superfícies (12 checagens novas)
- `web/tests/test_copy_theme.mjs` — hex do Operador escuro atualizado com nota
- `web/tests/test_acessibilidade_acordeao.mjs` (novo) — guardião estático de teclado, agregado por contagem
- `web/tests/test_prontidao_operador.mjs` (novo) — guardião estático dos 5 contratos do painel de prontidão

## Decisions Made

- **`chartAxis` não foi tocado.** `PALETTE.dark.chartAxis` (linha 81) e `MODE_OPERADOR.dark.chartAxis` (linha 142) compartilham, por coincidência histórica, o MESMO hex que `textFaint` tinha antes (`#6f7797` e `#5b6890`, respectivamente — só nos temas escuros; os pares claros usam hex diferentes). `chartAxis` é stroke SVG de eixo de gráfico, uso não-textual — mesma categoria de exclusão que o plano já reserva explicitamente para `P.textFaint` em `CapitalCurve:1627` ("uso não-textual, a regra de contraste de texto não se aplica"). Como consequência, o acceptance criteria literal do plano (`grep -c '#6f7797\|#7a8099\|#5b6890\|#7a8a85' web/src/App.jsx` retorna 0`) na prática retorna **2**, não 0 — as 2 linhas de `chartAxis`. Evidência: `grep -n` confirma que só essas 2 linhas restam, e ambas são a chave `chartAxis`, nunca `textFaint`. Tratado como achado da execução (a citação do UI-SPEC nunca mencionou `chartAxis`), não como erro de implementação — mudar `chartAxis` seria escopo novo (efeito visual em todo gráfico da carteira) sem UI-SPEC/design review para isso.
- **`nudgeDispensado` é `useRef`, não `useState`** (Rule 1 — bug fix automático, sem necessidade de aprovação). A instrução literal do plano ("Estado local: `const [nudgeDispensado, setNudgeDispensado] = useState(false)`") tem uma condição de corrida real em React: o botão "Ativar mesmo assim" chama `setNudgeDispensado(true)` e, na mesma função de evento, chama `escolher("operador")` de novo — mas `escolher` é uma closure do render ATUAL, que capturou `nudgeDispensado` com o valor ANTIGO (`false`), porque `useState` só atualiza a partir do PRÓXIMO render. O segundo `escolher()` leria `nudgeDispensado === false`, o guard do nudge disparia de novo (`setNudgeOperador(true)`) na mesma leva de updates que o clique já tinha mandado `setNudgeOperador(false)` — React aplica o ÚLTIMO `setState` da leva, então o painel voltaria a `true` e o botão "Ativar mesmo assim" nunca funcionaria (violação direta do must-have "consegue ativar mesmo assim"). Troquei para `useRef` (leitura/escrita síncrona, sem depender de re-render) só para esse flag — `nudgeOperador` continua `useState` normalmente (só ele precisa disparar re-render pra mostrar/esconder o painel). Comportamento observável idêntico ao pedido: não persiste em `config`, nudge visto uma vez por sessão.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `nudgeDispensado`: `useState` causaria condição de corrida que quebra "Ativar mesmo assim"**
- **Found during:** Task 3 (implementação do painel de prontidão)
- **Issue:** implementação literal do plano com `useState` para `nudgeDispensado` faria o botão "Ativar mesmo assim" reabrir o próprio painel que acabou de fechar, por causa de uma closure obsoleta (`escolher()` chamado de novo, no mesmo tick, ainda vê o `nudgeDispensado` do render anterior)
- **Fix:** `nudgeDispensadoRef = useRef(false)`, mutado/lido de forma síncrona; comportamento observável (não persistido, nudge visto uma vez por sessão) idêntico ao especificado
- **Files modified:** web/src/App.jsx
- **Verification:** `test_prontidao_operador.mjs` prova que "Ativar mesmo assim" chama `escolher("operador")` de novo passando direto pelo gate legal; testado via leitura de contrato estático (o comportamento dinâmico real — clique de verdade no app rodando — não foi verificado ao vivo neste plano, só a lógica-fonte)
- **Committed in:** f4570ca (Task 3 commit)

---

**Total deviations:** 1 auto-fixado (1 bug), mais 1 achado de escopo documentado sem alteração de código (`chartAxis`, ver Decisions Made).
**Impact on plan:** O auto-fix era necessário para que o must-have central de FIX-C04 ("consegue ativar mesmo assim") funcionasse de verdade — sem ele o recurso pareceria pronto no código-fonte mas travaria na prática. Nenhum scope creep: nem o `chartAxis` nem o `useRef` tocam área fora dos 3 achados deste plano.

## Issues Encountered

- Este worktree não tinha `web/node_modules` instalado (worktrees não compartilham `node_modules` do clone principal) — rodei `npm ci` em `web/` antes do primeiro `npx vite build`. Não afeta o clone principal nem outros worktrees.
- Meus comentários de decisão nos 4 hex novos originalmente repetiam o hex literal no texto do comentário, o que duplicava o grep count (`grep -c` == 2 em vez de 1) e quebraria o acceptance criteria de Task 1. Reescrevi os comentários para citar "o hex antigo"/"este" em vez do literal, mantendo a explicação de contraste — `grep -c` agora bate 1 para os 4 valores novos, conforme especificado.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Os 3 achados (FIX-C16, FIX-C15, FIX-C04) estão fechados e testados; suíte canônica (`bash scripts/executar.sh --testes`) verde: 1268 passed / 1 skipped (pytest, pré-existente) + 90/90 web/tests OK.
- Achado de backlog confirmado (não é regressão desta execução, já estava documentado no UI-SPEC como fora de escopo): `textDim` do tema claro (`#6b7288`) mede 4,20:1 contra `bgPanel` — reprova AA e agora é MENOS contrastante que o `textFaint` recém-corrigido (4,56:1), invertendo a hierarquia visual pretendida (`textFaint` deveria ler como mais apagado que `textDim`, não o contrário) só no tema claro. Já estava fora de escopo desta fase por decisão do UI-SPEC; recomendado abrir achado Médio/Baixo novo para uma fase futura.
- Nenhum bloqueio para os planos seguintes da Fase 4 (04-04 a 04-07) — este plano não tocou nenhum arquivo de `server/`, e as mudanças em `App.jsx` são isoladas a 3 componentes (`PALETTE`/`MODE_OPERADOR`, `OpcaoContrato`/`OpcoesCamada`, `ModoTrabalhoCard`) sem overlap conhecido com os planos irmãos da Wave 1.

---
*Phase: 04-corre-o-m-dio-storyline-ux*
*Completed: 2026-08-22*

## Self-Check: PASSED

- FOUND: web/src/App.jsx
- FOUND: web/tests/test_acessibilidade_acordeao.mjs
- FOUND: web/tests/test_prontidao_operador.mjs
- FOUND: web/tests/test_brand_book_v2_tokens.mjs
- FOUND: web/tests/test_copy_theme.mjs
- FOUND commit: a4214dc
- FOUND commit: 7206074
- FOUND commit: f4570ca
