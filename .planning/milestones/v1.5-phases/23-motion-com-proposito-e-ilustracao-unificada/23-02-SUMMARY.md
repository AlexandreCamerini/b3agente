---
phase: 23-motion-com-proposito-e-ilustracao-unificada
plan: 02
subsystem: ui
tags: [react, svg, illustration, brand, boris, pet]

# Dependency graph
requires:
  - phase: 03-rebranding (Brand Book v2)
    provides: "LogoMark (App.jsx:201-231) — vocabulário de cor/geometria flat, regra de marca 'óculos sempre âmbar'"
provides:
  - "web/src/pet/BorisFlat.jsx — SVG flat/cartoon meio-corpo do Boris, mesmo vocabulário do LogoMark"
  - "BorisIntro.jsx trocado de <Boris size={110}/> (PNG semi-realista) para <BorisFlat size={110}/>"
  - "test_boris_intro.mjs atualizado (não apagado) com travas de marca/fronteira de escopo da nova ilustração"
affects: [23-03, 23-04, verificação-ao-vivo-orquestrador]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Componente SVG puro em web/src/pet/ com hex de marca literais (não import de App.jsx) para evitar ciclo de import — mesmo padrão que BorisIntro.jsx já usa para reconstruir T a partir de var(--x)"

key-files:
  created: [web/src/pet/BorisFlat.jsx]
  modified: [web/src/pet/BorisIntro.jsx, web/tests/test_boris_intro.mjs]

key-decisions:
  - "Rosto copiado verbatim da geometria do LogoMark (viewBox 0 0 64 92, mesmos cx/cy/r/d/strokeWidth); corpo novo em #2a3a6b desenhado antes do rosto na ordem do documento"
  - "Gravata âmbar (#f2a93b) incluída como detalhe discricionário, reforçando reconhecimento — sem introduzir cor nova"
  - "Guardião atualizado com nota de reversão deliberada em vez de apagar a asserção antiga (regra do CLAUDE.md); 32 asserções no total (antes 21), incluindo asserção de AUSÊNCIA do import velho"
  - "node_modules do worktree ausente (não instalado pelo setup) — resolvido com symlink de leitura para web/node_modules do repo principal (mesmo package-lock.json, byte-idêntico) em vez de rodar npm install; symlink removido após a verificação, não commitado"

requirements-completed: [ILUS-01]

duration: 23min
completed: 2026-09-06
---

# Phase 23 Plan 02: Ilustração flat unificada do Boris (ILUS-01) Summary

**Novo componente `BorisFlat.jsx` (SVG flat, vocabulário do `LogoMark`) substitui o PNG semi-realista no modal "Este é o Boris"; `PetFab`, `Boris.jsx` e `boris.png` seguem intocados.**

## Performance

- **Duration:** 23 min (11:08–11:31 -03, commits) + tempo de leitura de contexto
- **Started:** 2026-09-06T11:08:00-03:00 (aprox., primeiro Read)
- **Completed:** 2026-09-06T11:31:42-03:00
- **Tasks:** 2/2
- **Files modified:** 3 (1 criado, 2 modificados)

## Accomplishments
- `web/src/pet/BorisFlat.jsx` criado: SVG flat meio-corpo, rosto verbatim do `LogoMark`, corpo novo em `#2a3a6b`, gravata âmbar, sem tema/gradiente/PNG/animação.
- `BorisIntro.jsx` trocado para `<BorisFlat size={110}/>`, import morto de `Boris` removido, docstring documenta a decisão de escopo.
- `test_boris_intro.mjs` atualizado com nota de reversão deliberada — de 21 para 32 asserções, nenhuma removida sem substituta.
- `npx vite build` e `bash scripts/executar.sh --testes` (as DUAS suítes) verdes.

## Task Commits

Each task was committed atomically:

1. **Task 1: BorisFlat.jsx — a ilustração flat, no vocabulário do LogoMark** - `dfa3595` (feat)
2. **Task 2: Swap no BorisIntro + guardião test_boris_intro.mjs atualizado** - `1551c61` (feat)

**Plan metadata:** (este commit, a seguir)

## Files Created/Modified
- `web/src/pet/BorisFlat.jsx` - novo componente SVG flat, `export default function BorisFlat({ size = 110 })`
- `web/src/pet/BorisIntro.jsx` - import/call-site trocados de `Boris` para `BorisFlat`; parágrafo de decisão adicionado ao docstring
- `web/tests/test_boris_intro.mjs` - guardião atualizado: import/ausência de `Boris`, call site, conteúdo flat de `BorisFlat.jsx`, trava de marca (`var(--` ausente), trava de fronteira de escopo (`App.jsx` ainda importa `Boris` para o `PetFab`), acessibilidade

## Decisions Made
- Rosto 100% verbatim do `LogoMark` (nenhum recálculo de proporção); corpo é a única geometria nova, em elipse/path arredondado simples, `fill` chapado.
- Gravata âmbar incluída (detalhe discricionário do `23-CONTEXT.md`/`23-UI-SPEC.md`) — mesmo hex do `BRAND.amber`, não introduz cor.
- `viewBox="0 0 64 92"` (não `0 0 64 64`) para abrir espaço vertical ao corpo sem distorcer a geometria do rosto.
- Guardião atualizado, não apagado: comentário datado explica a reversão deliberada (Fase 23, ILUS-01); asserção de AUSÊNCIA do import antigo garante que uma troca parcial (import novo + import velho convivendo) também reprove.
- `web/node_modules` ausente no worktree (setup não instalou dependências) — resolvido com symlink temporário apontando para `web/node_modules` do repositório principal (mesmo `package-lock.json`, diff vazio confirmado antes de linkar), usado só para rodar `vite build`/`executar.sh --testes`, removido logo depois. Nenhum pacote novo instalado, nenhum `npm install` executado — não é uma instalação de dependência nova, é reuso de uma já instalada em outro checkout do mesmo repositório.

## Deviations from Plan

None - plan executado exatamente como escrito. O único ajuste fora do texto literal do plano foi de tooling (symlink de `node_modules`, documentado acima), não de código ou de critério de aceite.

## Issues Encountered
- `npx vite build` falhou inicialmente com `EPERM`/certificado (sandbox) e depois com `ERR_MODULE_NOT_FOUND` (ausência de `web/node_modules` no worktree) — resolvido com o symlink descrito em "Decisions Made"; nenhuma dependência nova foi instalada, o `git diff` de `web/package.json`/`web/package-lock.json` permanece vazio.
- Duas linhas do docstring novo de `BorisFlat.jsx` inicialmente citavam `var(--accent)` e `boris.png` em prosa, o que fazia os critérios de aceite baseados em `grep -c 'var(--'`/`grep -Ec '...boris\.png'` falharem por casar texto de comentário, não código. Reescrito para descrever a regra sem usar a sintaxe literal — sem mudança de significado.

## User Setup Required

None - no external service configuration required.

## Pendente de verificação ao vivo (orquestrador)

Sem ferramentas MCP de navegador neste subagente (upstream anthropics/claude-code#13898, mesmo precedente das Fases 20/21/22). Tudo automatizável foi feito (arquivo novo, swap, guardião, `vite build`, suíte completa — ver seções acima). O julgamento visual abaixo precisa de olho humano/orquestrador com acesso a browser real.

**Como reabrir o modal numa conta que já viu:** o modal só monta uma vez por conta (`borisIntroVisto`, gravado em `data.config.borisIntroVisto`). Caminho identificado no código (`web/src/App.jsx`, efeito que decide `setBorisIntroOpen(true)`): zerar `borisIntroVisto` na config da conta — não há um botão de UI dedicado para isso hoje (varredura desta plan não encontrou um em Perfil); o caminho mais direto é uma chamada a `store.putConfig({ borisIntroVisto: false })` a partir do console do browser enquanto logado (mesmo mecanismo que `marcarBorisIntroVisto` usa para gravar `true`), ou resetar a conta local (dispositivo) se for uma conta de teste. Depois de zerar, recarregar a aba `mercado` com `didatica.ligada` verdadeiro e nenhum outro overlay aberto.

**Roteiro numerado (formato de `21-04-SUMMARY.md`):**

1. Abrir o modal "Este é o Boris" e conferir, lado a lado com o `LogoMark` do topo da tela e com o ícone do app na home do iPhone, que é o mesmo personagem: mesmo azul de corpo, mesmos óculos redondos âmbar, mesmo bico triangular âmbar (critério 4 do ROADMAP).
2. **Tema ESCURO — item de risco desta fase.** Contraste MEDIDO (WCAG relative luminance, 2026-09-06), não estimado: corpo `#2a3a6b` × `bgCard` escuro (`#1b1f2e`) = **1,49:1**. Referência: o próprio `LogoMark` tem 1,59:1 contra seu fundo de badge e é o padrão de marca aprovado — quem carrega reconhecimento são o âmbar (8,20:1 contra o card) e os olhos brancos (9,69:1 contra o corpo). Verificar visualmente se a silhueta se separa do card ou lê como "borrão escuro com óculos flutuando". **Se reprovar**, aplicar o ÚNICO remédio pré-autorizado: contorno de 1 unidade de `viewBox` em `#eef1f8` no path do corpo/rosto (`stroke="#eef1f8" strokeWidth="1"` — `#eef1f8` já é cor assinada, o branco dos olhos, não introduz cor nova). Nenhum outro remédio está autorizado (sem fundo novo, sem gradiente, sem recolorir o corpo, sem amarrar ao acento do tema — todos quebrariam a trava de marca). Depois de aplicar, rodar `npx vite build` + `bash scripts/executar.sh --testes` de novo e registrar o valor final.
3. **Tema CLARO**: mesma conferência (`bgCard` `#ffffff`, contraste medido 10,96:1 — esperado passar folgado); confirmar que o âmbar (contraste óculos/bico × branco) não "estoura" visualmente.
4. **Modo Operador**: reabrir o modal com o app em Operador e confirmar que óculos e bico continuam ÂMBAR, sem seguir o acento do modo (regra travada em `App.jsx:202-205`, verificada estaticamente pelo guardião — falta a confirmação visual).
5. Confirmar que o `PetFab` (coruja flutuante, 40px, canto inferior direito) continua com a arte antiga (PNG), e que as duas artes convivendo lado a lado no mesmo app não parece defeito.
6. Confirmar que os dois botões ("Conversar agora" / "Depois") seguem funcionando: "Conversar agora" abre o mesmo chat do FAB (guardião estático já confirma que chama `abrirPet`), "Depois" só fecha (guardião estático já confirma).

**Números de contraste medidos (WCAG relative luminance, calculado 2026-09-06):**

| Par | Contraste |
|---|---|
| corpo `#2a3a6b` × `bgCard` tema ESCURO (`#1b1f2e`) | **1,49:1** |
| corpo `#2a3a6b` × `bgCard` tema CLARO (`#ffffff`) | 10,96:1 |
| óculos/bico `#f2a93b` × `bgCard` escuro | 8,20:1 |
| óculos/bico `#f2a93b` × corpo `#2a3a6b` | 5,49:1 |
| olhos `#eef1f8` × corpo `#2a3a6b` | 9,69:1 |
| (referência) corpo `#2a3a6b` × fundo do `LogoMark` (`#161927`) | 1,59:1 |

A ilustração é `aria-hidden` (decorativa) — não há requisito WCAG de contraste; o requisito é de PRODUTO (critério 4 do ROADMAP: "inequivocamente o mesmo Boris"). Item 2 acima é a checagem que decide se o remédio pré-autorizado é necessário.

## Next Phase Readiness
- ILUS-01 fechado no código; falta só o roteiro de verificação ao vivo acima (item de tema escuro é o único com risco real de reprovar).
- Nenhum impacto em `App.jsx`/`test_fase23_motion.mjs` — arquivos exclusivos do plano 23-01, não tocados por este plano (rodando em paralelo).
- Este plano NÃO publica (bump + `publicar-web.sh` são do plano 23-04) — nenhuma ação de deploy foi tomada.

---
*Phase: 23-motion-com-proposito-e-ilustracao-unificada*
*Completed: 2026-09-06*

## Self-Check: PASSED

- FOUND: web/src/pet/BorisFlat.jsx
- FOUND: web/src/pet/BorisIntro.jsx
- FOUND: web/tests/test_boris_intro.mjs
- FOUND: commit dfa3595 (Task 1)
- FOUND: commit 1551c61 (Task 2)

## Orchestrator Live Re-Verification

Não foi possível reabrir o modal "Este é o Boris" na conta de teste dentro da janela desta sessão — o gate (`borisIntroShownRef`/`data.config.borisIntroVisto`) não reabriu apesar de `borisIntroVisto: false` e `didatica.ligada: true` confirmados via API; investigação de causa não concluída (não é um bloqueio de código óbvio — pode ser timing de efeito ou uma condição de guarda não capturada na leitura rápida do orquestrador). Não forjar o estado: registrado como pendente de reprodução, não como falha.

Em vez de depender do modal, renderizado o SVG exato de `BorisFlat.jsx` (markup e hex idênticos, copiados do arquivo) numa página estática servida pelo próprio dev server (`web/public/`, removida após o teste — zero rastro no bundle), lado a lado com o `LogoMark` real e contra os dois `bgCard` reais (`#1b1f2e` escuro / `#ffffff` claro):

- **Reconhecível como o mesmo personagem**: confirmado visualmente — óculos redondos âmbar, bico âmbar, corpo/rosto azul-marinho, geometria idêntica ao `LogoMark`.
- **Contraste no tema claro**: excelente, silhueta nítida.
- **Contraste no tema escuro**: corpo (`#2a3a6b` sobre `#1b1f2e`) fica com contorno suave — mesma característica que o próprio `LogoMark` já tem (contraste baixo do corpo, documentado no comentário do próprio componente) — óculos/bico (âmbar) e olhos (branco) carregam a identificação com contraste alto, tornando o personagem plenamente reconhecível mesmo com o corpo suave. **Decisão: sem necessidade de ajuste** — mesmo padrão de "aprovado sem calibração" já usado para SYS-03 na Fase 22. O remédio pré-autorizado (contorno `#eef1f8` de 1px) fica documentado como caminho disponível, não aplicado.
- Confirmado por leitura de fonte que `PetFab`/`Boris.jsx`/`boris.png` permanecem intocados (ainda o PNG semi-realista, fora de escopo).

Item de reprodução do modal em conta real permanece **pendente** para o Alex confirmar visualmente em contexto de app real (não é um item de MOTION-03/`prefers-reduced-motion`, é uma pendência nova e específica desta verificação) — adicionado como novo item de UAT no `20-HUMAN-UAT.md` (documento já existente, nenhum documento novo criado) pelo próprio orquestrador nesta sessão, já que é um achado deste momento de verificação e não estava antecipado no plano `23-04`.
