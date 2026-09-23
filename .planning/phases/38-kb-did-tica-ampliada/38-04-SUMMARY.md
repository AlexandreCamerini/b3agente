---
phase: 38-kb-did-tica-ampliada
plan: 04
subsystem: ui
tags: [react, glossario, kb, busca, acordeao, didatica]

# Dependency graph
requires:
  - phase: 38-01
    provides: "GET /api/kb/catalogo (kb.py: catalogo_formatado(), 65 titulos autorados + 18 derivados, FAMILIAS)"
  - phase: 38-03
    provides: "web/src/glossario.js (catalogoKbValido/verbeteDoCatalogo), ctx.kbCatalogo/ctx.recarregarKb, A.abrirVerbeteKb(vid), ConceitoSheet com fonte kb"
provides:
  - "KB-01 completo: tela Perfil → Glossário com busca livre + acordeão de 9 famílias na mesma tela (D-01)"
  - "web/src/glossario.js estendido: normalizarBusca, filtrarVerbetes, agruparPorFamilia (puros)"
  - "TelaGlossario/LinhaVerbeteGlossario/GlossarioFamilia em App.jsx, tile 'Glossário' no grupo Ajuda do PerfilHub"
  - "6 chaves glossario* em copy.js (rótulo de interface, mesmas nos dois modos)"
affects: [38-05, 38-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Filtro live client-side por substring normalizada (NFD, sem acento, minúscula) com posto de ordenação 0/1/2 (prefixo-título > contém-título > termo/id), estável por índice de descoberta — sem RegExp construída do input (T-38-14)"
    - "Componente de linha de resultado compartilhado entre o acordeão de famílias e a lista plana de busca (mesmo componente local, dois contextos de uso)"

key-files:
  created:
    - web/tests/test_glossario.mjs
  modified:
    - web/src/glossario.js
    - web/src/App.jsx
    - web/src/copy.js

key-decisions:
  - "Casamento por SUBSTRING normalizada, não fronteira de palavra — D-02 trava só o kb.buscar() do backend (consumido pelo assistente via resolver()); esta tela nunca chama kb.buscar(), e busca live exige casar prefixo (\"rs\" → RSI) enquanto se digita"
  - "Tile 'Glossário' no grupo 'Ajuda' do PerfilHub (wide, logo abaixo de 'Como funciona'), não em 'IA e desempenho' como o 38-UI-SPEC.md (draft) sugeria — glossário não é IA; Ajuda já é o par temático certo (D-06)"
  - "Subtítulo do tile usa a CONTAGEM REAL do catálogo carregado (ctx.kbCatalogo.verbetes.length), não o literal '83 termos' do UI-SPEC — com a didática desligada o backend serve 74 (38-01), número fixo seria afirmação não medida"
  - "Fórmula de pontuação do assistente (kb._pontuar, privada) NÃO replicada em JS — posto 0/1/2 é deliberadamente mais simples, evita duas implementações da mesma pontuação divergirem (Don't Hand-Roll)"

patterns-established:
  - "Ordenação estável por índice de descoberta como critério de desempate explícito, sem depender da estabilidade de Array.prototype.sort do motor JS"

requirements-completed: [KB-01]

# Metrics
duration: ~25min
completed: 2026-09-23
---

# Phase 38 Plan 04: Tela de Glossário (busca + navegação por família) Summary

**Tela Perfil → Glossário com busca live client-side (sem round-trip por tecla, sem limite de resultados) e acordeão de 9 famílias, resolvendo KB-01 — os 83 verbetes da KB de mecânica B3 (antes sem NENHUM consumidor de UI) agora têm porta de entrada.**

## Performance

- **Duration:** ~25 min (commits às 09:24:30 e 09:27:22 -03:00; leitura/edição antecedeu o primeiro commit)
- **Completed:** 2026-09-23
- **Tasks:** 2/2
- **Files modified/created:** 4 (1 criado, 3 modificados)

## Accomplishments
- `web/src/glossario.js` ganhou `normalizarBusca`/`filtrarVerbetes`/`agruparPorFamilia` — filtro puro, testado por comportamento, sem `RegExp` construída do input (T-38-14), sem limite de resultados (D-03).
- `TelaGlossario` (App.jsx): três estados honestos (skeleton ao montar / erro com retry via `ctx.recarregarKb`, nunca lista parcial / pronto), e dentro do estado pronto três modos de resultado mutuamente exclusivos — query vazia → acordeão de famílias recolhido por padrão; query com match → lista plana sem cap; query sem match → mensagem "Nenhum verbete encontrado para "{termo}"." ACIMA do acordeão, que continua visível e interativo (D-05).
- Tile "Glossário" no grupo Ajuda do PerfilHub, subtítulo com a contagem real do catálogo carregado.
- Tocar qualquer verbete (acordeão ou lista) abre a mesma `ConceitoSheet` global via `A.abrirVerbeteKb(vid)` (ponte já pronta do 38-03).
- `web/tests/test_glossario.mjs`: 31 asserções (15 comportamentais de Task 1 + 16 estáticas de Task 2).

## Task Commits

Each task was committed atomically:

1. **Task 1: filtros puros da busca (glossario.js) com guardião comportamental** - `caeb49d` (feat)
2. **Task 2: TelaGlossario + tile em Perfil + rota de sub-tela + textos** - `3cde3cc` (feat)

**Plan metadata:** this commit (docs: complete plan, ver final_commit)

## Files Created/Modified
- `web/src/glossario.js` - `normalizarBusca(s)`, `filtrarVerbetes(verbetes, termo)`, `agruparPorFamilia(verbetes, familias)` (módulo continua puro, zero import)
- `web/src/App.jsx` - `TelaGlossario`/`LinhaVerbeteGlossario`/`GlossarioFamilia` (declarados imediatamente antes de `PerfilHub`, fora da fatia que `test_perfil_reorg.mjs` lê); tile "Glossário" no hub; roteamento `perfilView === "glossario"`; import de `filtrarVerbetes`/`agruparPorFamilia`
- `web/src/copy.js` - `glossarioSub`, `glossarioBuscaPlaceholder`, `glossarioBuscaRotulo`, `glossarioLimpar`, `glossarioVazio`, `glossarioErro` nos dois blocos (`estudo`/`operador`)
- `web/tests/test_glossario.mjs` - guardião novo, 2 partes (comportamental + estático)

## Decisions Made
- Substring normalizada em vez de fronteira de palavra (ver key-decisions) — decisão já declarada no `<objective>` do PLAN.md, implementada literalmente.
- Tile no grupo "Ajuda", não "IA e desempenho" — idem, decisão pré-declarada no plano, confirmada correta ao ler o `hubGroup` "IA e desempenho" real (só tiles de modelo/BYOK/custo) contra "Ajuda" (só "Como funciona").
- Subtítulo com contagem real — idem, evita repetir o literal "83" do UI-SPEC draft.
- `useMemo` para `resultados`/`grupos` em `TelaGlossario`: conveniência, não correção — a derivação é barata (≤83 itens) e roda de qualquer forma a cada tecla, sem debounce (D-04 exige exatamente isso).

## Deviations from Plan

None - plan executado exatamente como escrito. As três escolhas de implementação declaradas no `<objective>` do PLAN.md (substring, placement do tile, contagem real) já eram decisões pré-tomadas pelo plano, não decisões novas tomadas durante a execução.

## Issues Encountered
- Primeira versão do guardião estático (Task 2) fatiava `App.jsx` a partir de `function TelaGlossario(`, mas `LinhaVerbeteGlossario`/`GlossarioFamilia` (onde `aria-expanded` vive) são declarados ANTES desse ponto — a asserção de `aria-expanded` falhou por fatiamento estreito demais, não por ausência do atributo no código. Corrigido alargando a fatia para começar em `function LinhaVerbeteGlossario(`. Nenhum código de produto mudou, só o teste.

## Known Stubs
None - o catálogo é buscado de verdade (ponte do 38-03) e a tela renderiza dados reais do backend (38-01); nenhum valor hardcoded/vazio no caminho novo.

## Threat Flags
None - as 4 mitigações do `<threat_model>` (T-38-14..T-38-17) foram implementadas e travadas: `filtrarVerbetes` só usa `includes`/`startsWith` (grep confirma zero `RegExp` em `glossario.js`, 3 casos de caractere especial testados sem exceção); termo buscado nunca sai do aparelho (filtro local, sem chamada de rede por tecla); três estados explícitos de catálogo, erro com retry, sem lista parcial; render é só nó de texto React (nenhum HTML cru/Markdown na tela nova).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- KB-01 entregue: busca livre + famílias, live, sem limite, vazio honesto, erro com retry, verbete abre a `ConceitoSheet` real.
- **Precondição do checkpoint visual do 38-06 NÃO verificada nesta sessão**: backend/Vite locais não estavam de pé (`curl localhost:8787/api/kb/catalogo` → `http_code:000`, conexão recusada). O próprio `<acceptance_criteria>` do plano previa esse caminho ("se não der para subir o ambiente, registrar no SUMMARY — a verificação visual fica no 38-06") — nenhuma verificação ao vivo (skeleton real, digitação real, abertura real da `ConceitoSheet`) foi feita aqui, só estática/build.
- `npx vite build` verde (961 KB do bundle principal, aviso de chunk grande pré-existente, não relacionado a esta fase).
- Suíte `.mjs` completa: 157/158 (única falha é a ambiental conhecida, `test_ios_assets.mjs`, `web/ios/` gitignored).
- Nenhum bloqueador para o 38-05 (ancoragem "saiba mais" nas 4 abas) ou 38-06 (checkpoint visual consolidado).

---
*Phase: 38-kb-did-tica-ampliada*
*Completed: 2026-09-23*

## Self-Check: PASSED

- FOUND: web/src/glossario.js
- FOUND: web/tests/test_glossario.mjs
- FOUND: web/src/App.jsx
- FOUND: web/src/copy.js
- FOUND: .planning/phases/38-kb-did-tica-ampliada/38-04-SUMMARY.md
- FOUND commit: caeb49d
- FOUND commit: 3cde3cc
