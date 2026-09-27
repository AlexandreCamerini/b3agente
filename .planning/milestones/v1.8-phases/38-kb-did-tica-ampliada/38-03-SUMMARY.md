---
phase: 38-kb-did-tica-ampliada
plan: 03
subsystem: ui
tags: [react, glossario, kb, conceitos, didatica]

# Dependency graph
requires:
  - phase: 38-01
    provides: "GET /api/kb/catalogo (kb.py: catalogo_formatado(), 65 titulos autorados + 18 derivados, FAMILIAS)"
  - phase: 38-02
    provides: "web/src/entendimento.jsx (ConceitoSheet/SetorAlvo/AssistenteBox/AiNote extraidos de App.jsx, importavel sem ciclo)"
provides:
  - "Catalogo da KB no cliente: api.kbCatalogo, serverStore.kbCatalogo, deviceStore.kbCatalogo (paridade)"
  - "web/src/glossario.js: helpers puros catalogoKbValido/verbeteDoCatalogo (zero import, base para busca do 38-04)"
  - "App.jsx: estado kbCatalogo (3 estados: undefined/null/objeto), carregarKb memoizada em modoApp, ctx.kbCatalogo, ctx.recarregarKb"
  - "A.abrirVerbeteKb(vid) — acao separada que abre a ConceitoSheet com fonte:\"kb\", sem tocar A.abrirVerbete"
  - "ConceitoSheet com discriminador fonte=\"conceito\"|\"kb\": ramo kb resolve sincrono do catalogo em memoria (sem fetch), sem AssistenteBox"
affects: [38-05, 38-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Discriminador explicito fonte:\"conceito\"|\"kb\" com default \"conceito\" — nunca fallback silencioso por 404 entre os dois catalogos didaticos"
    - "Modulo puro (zero import) para logica de lookup compartilhada entre App.jsx/entendimento.jsx/opcoes — mesmo padrao de uiOpcoes.jsx (Fase 33)"

key-files:
  created:
    - web/src/glossario.js
    - web/tests/test_kb_ponte.mjs
  modified:
    - web/src/api.js
    - web/src/persistence.js
    - web/src/App.jsx
    - web/src/entendimento.jsx

key-decisions:
  - "Acao NOVA A.abrirVerbeteKb(vid) em vez de 3o parametro em A.abrirVerbete(cid, dados) — test_concentracao_carteira.mjs trava a assinatura literal `abrirVerbete: (cid, dados) =>` por indexOf, e o nome da acao carrega a fonte sem flag posicional"
  - "Lookup de 'veja tambem' NAO migrou de didatica.conceitos para o catalogo kb no ramo conceito — o ramo kb ganhou lookup proprio (verbeteDoCatalogo) no catalogo kb; o ramo conceito ficou byte a byte, guardiao test_conceito_ui.mjs:115 intocado"
  - "Ramo kb da ConceitoSheet resolve SINCRONO (sem chamada de rede) — o catalogo ja esta em memoria via ctx.kbCatalogo, buscado 1x no boot/troca de modo"

patterns-established:
  - "Pattern 1 do RESEARCH (discriminador explicito, nunca fallback por 404) confirmado em codigo: os 9 ids que existem nos dois catalogos nao trocam de fonte em silencio"

requirements-completed: [KB-01, KB-02]

duration: ~15min
completed: 2026-09-23
---

# Phase 38 Plan 03: Ponte kb×conceito na ConceitoSheet Summary

**Discriminador explícito `fonte: "conceito"|"kb"` na `ConceitoSheet` — a folha agora abre tanto a explicação ancorada nos números do card (`conceitos.py`) quanto qualquer um dos 83 verbetes do glossário genérico (`kb.py`), sem fallback silencioso por 404 e sem tocar nenhum dos 9 call-sites existentes.**

## Performance

- **Duration:** ~15 min (estimativa — hora de início da sessão não foi capturada formalmente; timestamps dos 2 commits: 09:18:53 e 09:20:29 -03:00, o trabalho de leitura/edição/teste antecedeu o primeiro commit)
- **Completed:** 2026-09-23
- **Tasks:** 2/2
- **Files modified/created:** 6 (2 criados, 4 modificados)

## Accomplishments
- Catálogo completo da KB (`GET /api/kb/catalogo`) chega ao cliente com paridade nos dois stores (`serverStore`/`deviceStore`) e três estados honestos no `App.jsx` (`undefined`=carregando, `null`=falhou com retry via `ctx.recarregarKb`, objeto=pronto) — nunca lista parcial/inventada.
- `web/src/glossario.js` — módulo puro (zero import) com `catalogoKbValido`/`verbeteDoCatalogo`, base que o 38-04 estende com os filtros de busca.
- `A.abrirVerbeteKb(vid)` abre a `ConceitoSheet` com `fonte: "kb"` sem alterar `A.abrirVerbete` (guardião de assinatura literal preservado).
- `ConceitoSheet` ganhou o ramo `kb`: resolve o verbete **síncrono** do catálogo em memória (sem chamada de rede), renderiza título/subtítulo honesto ("Verbete do glossário — explicação geral, sem números de nenhum ativo.")/corpo/"veja também" resolvido no catálogo kb, sem `AssistenteBox` (não há snapshot de ativo para a caixa paga "Pergunte à IA sobre estes números").
- Fluxo ancorado (ramo `conceito`, 9 call-sites existentes) permanece byte a byte — `git diff --stat` vazio em `test_conceito_ui.mjs`/`test_boris_chat.mjs` confirma.

## Task Commits

Each task was committed atomically:

1. **Task 1: caminho de dados do catálogo (api, dois stores, helpers puros, estado no App, A.abrirVerbeteKb)** - `8b5e0e6` (feat)
2. **Task 2: ConceitoSheet com discriminador de fonte + render de verbete kb + mount global** - `c6fe822` (feat)

**Plan metadata:** este commit (docs: complete plan, ver final_commit)

## Files Created/Modified
- `web/src/glossario.js` - módulo puro: `catalogoKbValido(r)`, `verbeteDoCatalogo(cat, vid)`
- `web/src/api.js` - `kbCatalogo: (modo) => req("GET", "/api/kb/catalogo"...)`, timeout 15000
- `web/src/persistence.js` - `kbCatalogo` nos dois stores (paridade: `serverStore`/`deviceStore`)
- `web/src/App.jsx` - estado `kbCatalogo`, `carregarKb` (useCallback dep `[modoApp]`), `ctx.kbCatalogo`/`ctx.recarregarKb`, `A.abrirVerbeteKb`, mount global de `ConceitoSheet` com `fonte`/`kbCatalogo`
- `web/src/entendimento.jsx` - `ConceitoSheet` ganha props `fonte = "conceito"`, `kbCatalogo = null`; ramo `kb` síncrono; erro por fonte
- `web/tests/test_kb_ponte.mjs` - guardião novo (comportamental + estático, 2 partes)

## Decisions Made
- `A.abrirVerbeteKb` como ação separada em vez de 3º parâmetro de `abrirVerbete` — motivo documentado no PLAN.md e travado por teste (`test_concentracao_carteira.mjs` continua passando sem edição).
- Lookup de "veja também" do ramo `conceito` NÃO migrou para o catálogo kb (ficou em `didatica.conceitos`, como sempre foi) — só o ramo `kb` ganhou lookup próprio. Resultado: zero risco de os chips do fluxo ancorado sumirem se o catálogo kb falhar.
- Ramo `kb` resolve síncrono (não chama `store.conceito` nem qualquer rota) — o catálogo já está em `ctx.kbCatalogo`, buscado uma vez no boot/troca de modo.

## Deviations from Plan

None - plan executado exatamente como escrito. Todas as decisões de mecanismo (discriminador explícito, ação separada, lookup próprio no ramo kb) já estavam especificadas no PLAN.md e foram implementadas literalmente.

## Issues Encountered
None.

## Known Stubs
None - o catálogo é buscado de verdade e o ramo kb renderiza dados reais do backend (38-01); nenhum valor hardcoded/vazio no caminho novo.

## Threat Flags
None - as 5 mitigações do `<threat_model>` (T-38-09..T-38-13) foram implementadas e travadas por asserção no `test_kb_ponte.mjs` (sem `Markdown`/`dangerouslySetInnerHTML` no ramo kb, discriminador com default seguro, `catalogoKbValido`/`verbeteDoCatalogo` retornando `null` em forma inesperada, `AssistenteBox` ausente do ramo kb, paridade dos dois stores). Nenhuma superfície nova fora do que o `<threat_model>` já previa.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `web/src/glossario.js` está pronto para o 38-04 estender com os filtros de busca (tile "Glossário").
- `A.abrirVerbeteKb(vid)` está pronto para qualquer um dos 4 pontos de ancoragem do 38-05 (Acompanhar/Radar/Watchlist/Opções) chamar — D-08 (qual verbete cada aba abre) segue como decisão bloqueante do Alex no checkpoint do 38-05, nada foi decidido aqui.
- `ConceitoSheet` aceita `fonte`/`kbCatalogo` como props opcionais — `opcoes/OpcoesScreen.jsx` (38-05) pode montar sua própria folha local reusando o mesmo componente de `entendimento.jsx` (risco de isolamento do FAB do Boris já declarado no STATE.md, a ser conferido no checkpoint do 38-06).
- Nenhum bloqueador. Suíte canônica local (`.mjs`) sem falha nova; `npx vite build` verde.

---
*Phase: 38-kb-did-tica-ampliada*
*Completed: 2026-09-23*

## Self-Check: PASSED

- FOUND: web/src/glossario.js
- FOUND: web/tests/test_kb_ponte.mjs
- FOUND: .planning/phases/38-kb-did-tica-ampliada/38-03-SUMMARY.md
- FOUND commit: 8b5e0e6
- FOUND commit: c6fe822
