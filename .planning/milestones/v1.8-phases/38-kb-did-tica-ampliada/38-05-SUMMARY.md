---
phase: 38-kb-did-tica-ampliada
plan: 05
subsystem: ui
tags: [react, kb, didatica, glossario, opcoes, isolamento-adr027]

# Dependency graph
requires:
  - phase: 38-03
    provides: "glossario.js (catalogoKbValido/verbeteDoCatalogo), ctx.kbCatalogo, A.abrirVerbeteKb, ConceitoSheet resolvendo fonte kb síncrona"
  - phase: 38-04
    provides: "precedente de rótulo idêntico nos dois modos (glossarioSub/glossarioErro), padrão de comentário Fase 38 em copy.js"
provides:
  - "ANCORAS_KB (glossario.js) — fonte única dos 4 vid aprovados pelo Alex (D-07/D-08)"
  - "Link 'saiba mais' fixo nas 4 abas sem cobertura anterior (Acompanhar/Radar/Watchlist/Opções)"
  - "Guardião cross-linguagem server/tests/test_kb_ancoras.py (vid existe em kb.catalogo(), texto não vazio nos dois modos)"
  - "Guardião estático web/tests/test_kb_ancoras.mjs (portão didatica+catálogo, isolamento de Opções, estilo idêntico ao precedente)"
affects: [38-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Link 'saiba mais' fixo por aba: mesmo estilo/portão do precedente de Portfólio (diversificacao), vid vindo de ANCORAS_KB (fonte única congelada)"
    - "OpcoesScreen.jsx monta instância PRÓPRIA de ConceitoSheet (estado local, fonte='kb') em vez de reusar o overlay global — mantém o isolamento ADR-027 (nenhum import de App.jsx)"

key-files:
  created:
    - server/tests/test_kb_ancoras.py
    - web/tests/test_kb_ancoras.mjs
  modified:
    - web/src/glossario.js
    - web/src/copy.js
    - web/src/App.jsx
    - web/src/opcoes/OpcoesScreen.jsx

key-decisions:
  - "D-08: proposta original do 38-UI-SPEC.md aprovada sem alteração pelo Alex (Acompanhar→mkt-carteira-simulada, Radar→confluencia, Watchlist→ind-rsi, Opções→mkt-opcao)"
  - "Opções usa ConceitoSheet LOCAL (estado próprio), não o overlay global — cumpre D-08 (isolamento ADR-027) ao custo de duas vias de folha na mesma tela, risco declarado para o 38-06"

patterns-established:
  - "ANCORAS_KB congelado (Object.freeze) como fonte única de vid por aba, com guardião cross-linguagem obrigatório contra kb.py"

requirements-completed: [KB-02]

# Metrics
duration: ~45min
completed: 2026-09-23
---

# Phase 38 Plan 05: Ancoragem de verbete "saiba mais" nas 4 abas sem cobertura Summary

**Link "saiba mais" fixo (D-07/D-08) em Acompanhar/Radar/Watchlist/Opções, com `ANCORAS_KB` como fonte única e dois guardiões cross-linguagem/estáticos travando vid morto — Opções abre a folha por instância local para preservar o isolamento ADR-027.**

## Resolução de D-08 (checkpoint bloqueante, Task 1)

**Data:** 2026-09-23. O orquestrador apresentou as 4 opções do checkpoint ao Alex via `AskUserQuestion` (fora do contexto deste agente executor) e o Alex escolheu **"proposta"** — a proposta original do `38-UI-SPEC.md`, sem alteração:

| Aba | `vid` | Família |
|-----|-------|---------|
| Acompanhar (`EvolucaoScreen`) | `mkt-carteira-simulada` | `mercado_b3` |
| Radar (`RadarScreen`) | `confluencia` | (derivado de `conceitos.py`) |
| Watchlist (`MercadoScreen`) | `ind-rsi` | indicadores |
| Opções (`OpcoesScreen.jsx`) | `mkt-opcao` | `mercado_b3` |

Verificação automática (comando do `<verify>` da Task 1) confirmou os 4 ids
(mais os 2 alternativos citados no checkpoint) presentes em `kb.catalogo()`:

```
cd server && ./.venv/bin/python -c "from app import kb; ids={'mkt-carteira-simulada','confluencia','ind-rsi','mkt-opcao','estado-armado','familia-tendencia'}; print(all(kb.verbete(i) for i in ids))"
```
→ `True`

## Performance

- **Duration:** ~45min (estimado — timestamp inicial não capturado nesta sessão)
- **Completed:** 2026-09-23
- **Tasks:** 3/3 (Task 1 checkpoint, resolvida acima; Tasks 2 e 3 `type="auto"`)
- **Files modified:** 6 (4 modificados, 2 criados)

## Accomplishments

- KB-02 entregue: as 4 abas sem cobertura ganham link "saiba mais" fixo,
  cada uma abrindo sempre o mesmo verbete aprovado (D-07: sem lógica por
  contexto).
- `ANCORAS_KB` em `glossario.js` (módulo puro) é a fonte única dos 4 `vid`,
  travada contra o catálogo real do backend por um guardião cross-linguagem
  dedicado (`server/tests/test_kb_ancoras.py`), no mesmo padrão do guardião
  de paridade `defaults.py`↔`catalog.js` já usado no repo.
- `OpcoesScreen.jsx` continua com ZERO import de `App.jsx` — a ConceitoSheet
  do "saiba mais" desta aba é uma instância própria (estado local, trilha
  própria), importada só de `../entendimento.jsx`/`../glossario.js`.

## Task Commits

1. **Task 1: Alex aprova o verbete de cada aba (D-08)** — checkpoint resolvido fora deste agente (ver seção acima), sem código associado; nenhum commit próprio.
2. **Task 2: ANCORAS_KB + 3 links em App.jsx + guardião de backend** - `4f5a4d6` (feat)
3. **Task 3: link em Opções com ConceitoSheet local + guardião** - `2b8d1a7` (feat)

_Não houve tasks TDD nesta plan._

## Files Created/Modified

- `web/src/glossario.js` - `ANCORAS_KB` (Object.freeze, 4 chaves, comentário D-07/D-08)
- `web/src/copy.js` - `saibaMais: "saiba mais"` nos dois modos (idêntico, mesmo padrão de `glossarioSub`)
- `web/src/App.jsx` - import de `ANCORAS_KB`/`verbeteDoCatalogo`; link em `EvolucaoScreen`/`MercadoScreen`/`RadarScreen`, portão `ctx.didatica.ligada && verbeteDoCatalogo(...)`, ação `A.abrirVerbeteKb(ANCORAS_KB.<aba>)`
- `web/src/opcoes/OpcoesScreen.jsx` - import de `ConceitoSheet` (`../entendimento.jsx`) e `ANCORAS_KB`/`verbeteDoCatalogo` (`../glossario.js`); estado local `verbeteAberto`; link "saiba mais" após o subtítulo; instância `<ConceitoSheet fonte="kb" .../>` no fim da `<section>`; `A.abrirVerbete("liquidez-opcao", ...)` existente intocado
- `server/tests/test_kb_ancoras.py` - guardião cross-linguagem novo (4 testes): chaves exatas, vid existe em `kb.catalogo()`, texto não vazio nos dois modos, prova negativa de extração
- `web/tests/test_kb_ancoras.mjs` - guardião estático novo: link na tela certa, portão didatica+catálogo, ausência de `abrirSetor`/`openConceito`/`A.abrirVerbete(` antigo, estilo idêntico ao precedente, isolamento de `OpcoesScreen.jsx`, `ConceitoSheet` com `fonte="kb"`/`kbCatalogo`, chip de liquidez intocado

## Decisions Made

- **D-08 fechada** conforme registrado na seção "Resolução de D-08" acima —
  proposta original do UI-SPEC, sem alteração.
- **Opções usa folha LOCAL, não o overlay global** — decisão já travada no
  `38-05-PLAN.md` (Pattern 3, Opção B do RESEARCH): "ambos importam do
  módulo novo, nenhum importa do outro". Consequência aceita e não resolvida
  aqui (ver "Known Stubs / Tensões" abaixo).

## Deviations from Plan

None - plan executado como escrito, incluindo a resolução do checkpoint D-08
já decidida pelo orquestrador antes do início deste agente.

## Issues Encountered

Um guardião novo (`web/tests/test_kb_ancoras.mjs`) precisou de um ajuste de
implementação antes de fechar verde: a extração do "bloco do link" por
`indexOf(")}", ...)` cortava cedo demais, porque o próprio `onClick`
(`A.abrirVerbeteKb(ANCORAS_KB.evolucao)}`) contém um `)}` que fecha só a
expressão JS do atributo, não o bloco condicional inteiro — o corte
acontecia ANTES do `style={{...T.accent...}}` que o teste precisava
inspecionar. Corrigido trocando a busca por fechamento para uma janela de
tamanho fixo ao redor do marcador (mesma técnica já usada no bloco de
Opções). Sem impacto em código de produto — só no próprio guardião, antes de
qualquer commit.

## Known Stubs / Tensões declaradas (não resolvidas nesta plan)

- **`OpcoesScreen.jsx` ganha uma SEGUNDA via de folha de conceito.** O
  arquivo já abria o chip de liquidez pelo overlay GLOBAL
  (`A.abrirVerbete("liquidez-opcao", ...)`, intocado, guardado por
  `test_faixa_liquidez_ui.mjs`); agora o "saiba mais" desta plan abre uma
  instância LOCAL da mesma `ConceitoSheet`. Efeito colateral esperado, não
  corrigido aqui por desenho: a folha local não entra em `ctx.overlayLivre`
  do `App.jsx`, então o FAB do Boris provavelmente não se esconde sob ela —
  **a conferir no checkpoint humano do 38-06**, conforme já declarado no
  `<objective>` do `38-05-PLAN.md`.

## Threat Flags

Nenhum achado fora do `<threat_model>` do plano — os 4 threats declarados
(T-38-18 isolamento, T-38-19 link morto, T-38-20 decisão não registrada,
T-38-21 telemetria) foram todos mitigados exatamente como especificado, sem
superfície nova.

## User Setup Required

None - nenhuma configuração externa necessária.

## Next Phase Readiness

- KB-02 completo: as 4 abas do app (Acompanhar/Radar/Watchlist/Opções) têm
  entrada didática para a KB, além do Portfólio (pré-existente) e do
  Glossário completo (38-04, KB-01).
- Pendência explícita para o 38-06: confirmar ao vivo se o FAB do Boris
  se esconde (ou não) sob a folha local de Opções — comportamento
  conhecido, declarado, não bloqueante para esta plan.
- Suíte canônica fora do sandbox: 2991 pytest passed/5 skipped/3 xfailed/0
  failed (idêntico à baseline, as 27 falhas vistas DENTRO do sandbox são o
  artefato de rede/mocking pré-existente documentado no projeto, nenhuma
  toca `kb.py`/`App.jsx`/`OpcoesScreen.jsx`) + 156/157 `.mjs` (única falha,
  `test_ios_assets.mjs`, é ambiental e conhecida — `web/ios/` gitignored).
  `npx vite build` limpo nas duas rodadas (Task 2 e Task 3).

---
*Phase: 38-kb-did-tica-ampliada*
*Completed: 2026-09-23*

## Self-Check: PASSED

Todos os 6 arquivos de código/teste (glossario.js, copy.js, App.jsx,
OpcoesScreen.jsx, test_kb_ancoras.py, test_kb_ancoras.mjs) confirmados
presentes no filesystem; commits `4f5a4d6` e `2b8d1a7` confirmados em
`git log --oneline --all`.
