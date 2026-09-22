---
phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis
plan: 04
subsystem: web/opcoes (PayoffChart.jsx)
tags: [payoff, svg, geometria, opcoes, chart]

# Dependency graph
requires:
  - phase: 37-01
    provides: "dominio/segmentos anexados a proposta()/possibilidades() em options_mcp_api.py (dominio_da_curva/segmentos_da_curva do backend, Fase 36)"
  - phase: 37-02
    provides: "chaves de copy CHART-01/02/03/05 em copy.js (opcoesEixoZeroRotulo, opcoesEixoVerticalLoteAjuda, opcoesNoVencimentoTitulo, opcoesHojeTitulo, opcoesHojeAjuda, opcoesPerdaIlimitadaCurta, opcoesHojePrefixoEixo)"
  - phase: 37-03
    provides: "valorHoje no envelope de proposta()/possibilidades() ({erro:...} | {dados:{porAcao,emReais}})"
provides:
  - "PayoffChart.jsx aceita 3 props novas opcionais (dominio, segmentos [ignorada por este componente], valorHoje) mantendo os 3 consumidores atuais intocados quando não passadas"
  - "eixo Y com até 3 marcas numéricas de 2 casas (CHART-01), strikes+spot marcados no eixo reusando o algoritmo de colisão de 44px dos breakevens (CHART-02), setas de lado ilimitado com rótulo curto colado (CHART-03)"
  - "bloco 'No vencimento'/'Hoje · valor de mercado' (CHART-05 frontend, sem consumidor real ainda — é o Plano 37-05)"
affects: [37-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fallback duplo no mesmo useMemo: usa dominio.{xMin,xMax,yMin,yMax} do backend quando as 4 chegam não-null, cai no cálculo local de janela existente quando qualquer uma falta — nunca dois componentes distintos"
    - "Merge de duas fontes de marca (breakeven+strike) num único array ordenado antes de rodar o MESMO algoritmo de colisão de 44px, discriminadas só por estilo de linha/cor — nunca um segundo algoritmo de supressão"
    - "entre() (interpolação linear já existente) reusado sem clamp para EXTRAPOLAR a posição Y de um marcador quando o ponto cai fora dos nós conhecidos da curva — continuação matemática do payoff declarado, não invenção de dado"

key-files:
  created: []
  modified:
    - web/src/opcoes/PayoffChart.jsx
    - web/tests/test_payoff_responsivo.mjs

key-decisions:
  - "CHART-01/02/03 (eixo Y, strike/spot no eixo, setas rotuladas) aplicam-se a TODOS os consumidores incondicionalmente, mesmo sem dominio — usam o ymin/ymax do fallback local já existente. Só a JANELA (x0/x1/ymin/ymax) e o marcador de spot dependem de dominio estar presente. Isso é o que faz D-09 (correção chega aos 3 consumidores automaticamente) funcionar sem tocar SecaoAnalisar/SecaoComparar/CuradoriaEstruturas"
  - "Prioridade breakeven-sobre-strike em colisão de 44px implementada por ordenação estável (breakeven listado primeiro no array de entrada, antes do sort por sx()) — resolve empate exato de posição; não implementa uma regra geral de 'breakeven sempre vence qualquer strike próximo independente de ordem em x', que o texto do plano não formalizava além do critério de ordenação"
  - "segmentos é aceito na assinatura (contrato de 3 props do 37-04-PLAN.md) mas nunca lido — quem consome é ExplicacaoPayoff.jsx (37-02); void segmentos silencia o aviso de variável não usada sem fingir uso"

requirements-completed: [CHART-01, CHART-02, CHART-03]

# Metrics
duration: ~45min
completed: 2026-09-22
---

# Phase 37 Plan 04: Geometria do PayoffChart (eixo Y, strike/spot, setas rotuladas) + bloco Hoje/No vencimento Summary

**`PayoffChart.jsx` ganha eixo Y com escala visível de 2 casas decimais, strikes e spot marcados no eixo (reusando o algoritmo de colisão de 44px dos breakevens), setas de lado ilimitado com rótulo curto colado, e o par de blocos "No vencimento"/"Hoje · valor de mercado" — tudo opcional via 3 props novas que preservam os 3 consumidores reais existentes quando não passadas.**

## Performance

- **Duration:** ~45 min
- **Tasks:** 2 (+ 1 correção de aresta descoberta no self-review pré-SUMMARY)
- **Files modified:** 2

## Accomplishments

- `PAD_E` de 10 para 48 (orçamento do pior caso de rótulo "-99,99" a `FONTE_MIN=11,5px`)
- `useMemo` da janela/domínio: usa `dominio.{xMin,xMax,yMin,yMax}` do backend quando as 4 chegam não-null; cai no cálculo local de sempre quando qualquer uma falta (fallback exato, D-09)
- eixo Y com até 3 marcas (topo/zero/base), 2 casas decimais via `fmt()` existente, dedup a 3px do zero, omissão do extremo topo/base quando `dominio.ganhoIlimitado`/`perdaIlimitada`
- strikes de `e.legs` (filtro `kind === "CALL" || kind === "PUT"`, `strike` numérico — confirmado contra `server/tests/fixtures/mcp_evaluate_petr4.json`, shape real do MCP) mesclados no MESMO array de colisão de 44px dos breakevens; linha pontilhada mais fraca (`strokeDasharray="1 3"`, `T.borderFaint`), breakeven vence em empate de slot por ordenação estável
- spot no eixo: linha cheia + círculo, entra PRIMEIRO na lista de colisão top-anchored (mesma que `cenarios` já usa), garantindo que nunca perde o texto para um cenário colidente
- setas ↑/↓ de lado ilimitado ganham rótulo curto colado (`"sem teto"`/`"sem piso"`, chave nova `opcoesPerdaIlimitadaCurta`) + legenda "multiplique pelo lote" abaixo do SVG
- bloco "No vencimento" (Kicker envolvendo o cabeçalho existente) + bloco "Hoje · valor de mercado" (ausente quando `valorHoje` não foi tentado; cascata erro via `ErroDoMcp`/dados via linhas por-ação+em-reais+ajuda) — ainda sem consumidor real (Plano 37-05)
- `descricao`/`aria-label`/`<title>` ganham sentença nova listando TODOS os strikes (não só os visíveis), mesma disciplina do breakeven

## Task Commits

1. **Task 1: eixo Y, strike+spot no eixo, setas rotuladas, domínio do backend** - `d3fafb3` (feat)
2. **Task 2: bloco No vencimento/Hoje + testes de geometria** - `027cf1a` (feat)
3. **Correção pós-self-review: extrapolação da posição Y do spot** - `69e38e5` (fix)

## Files Created/Modified

- `web/src/opcoes/PayoffChart.jsx` — `PAD_E=48`; assinatura ganha `dominio`/`segmentos`/`valorHoje`; `useMemo` com fallback duplo de janela; eixo Y de 3 marcas; strikes mesclados na colisão de breakeven; spot com prioridade na colisão de cenários; setas rotuladas; legenda de lote; Kicker "No vencimento"/"Hoje" + cascata erro/dados
- `web/tests/test_payoff_responsivo.mjs` — 2 marcadores do guardião pré-existente atualizados (assinatura de 7 props; âncora do bloco de breakeven, agora mesclado com strike) + 5 asserções novas de geometria estática (`PAD_E===48`, chave `opcoesEixoZeroRotulo`, `strokeDasharray "1 3"`, `opcoesPerdaIlimitadaCurta` junto de seta `aria-hidden`, import de `Kicker`)

## Decisions Made

- Ver `key-decisions` no frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — issue bloqueante] Guardião pré-existente de `test_payoff_responsivo.mjs` quebrou por âncora de string, não por regressão real**
- **Found during:** Task 2, ao rodar `node web/tests/test_payoff_responsivo.mjs` pela primeira vez após as edições da Task 1
- **Issue:** duas asserções do guardião da Fase 31 (D-08) buscavam substrings literais que a Task 1 removeu ao mesclar breakeven+strike (`"[...marcas].sort"`) e ao estender a assinatura para 7 props (regex fechada em 4 props exatas) — nenhuma das duas é regressão de comportamento, são âncoras de string que meu próprio refactor obsoletou
- **Fix:** a asserção de assinatura foi reescrita para confirmar as 4 props ORIGINAIS + as 3 novas opcionais (não mais um total fechado de 4); o marcador `iniBe` foi trocado para `'tipoMarca: "breakeven"'`, um literal estável do novo bloco mesclado — a INTENÇÃO de cada checagem (D-08: zero interatividade; linha do breakeven nunca condicional) foi preservada, só a âncora de busca mudou
- **Files modified:** `web/tests/test_payoff_responsivo.mjs`
- **Verification:** as 19 asserções pré-existentes + as 5 novas passam, exit 0; suíte canônica completa sem regressão (2973 pytest + 156/156 `.mjs`)
- **Committed in:** `027cf1a` (Task 2 commit)

**2. [Rule 1 — bug] Posição Y do spot caía silenciosamente em `yZero` quando fora dos nós conhecidos da curva**
- **Found during:** self-review pré-SUMMARY (não pelos guardiões estáticos — eles só provam a PRESENÇA da marca, nunca sua posição correta)
- **Issue:** a cauda plana só é sintetizada quando os DOIS lados são limitados (`!ganhoIlimitado && !perdaIlimitada`); com só um lado ilimitado, `curva` pode não cobrir o domínio inteiro que o backend calculou, e um `dominio.spot` além do último nó conhecido caía no fallback `yZero` — posição visualmente errada para uma estrutura descoberta/com lado ilimitado
- **Fix:** o fallback passou a extrapolar pela mesma `entre()` já existente (que não recorta, extrapola linearmente por definição), usando o segmento mais próximo (primeiro ou último par de `curva`) em vez de cravar no zero — continuação matemática do payoff linear por partes já declarado pelo backend, não invenção de dado (mesmo princípio que o arquivo já aplica em `entre()`)
- **Files modified:** `web/src/opcoes/PayoffChart.jsx`
- **Verification:** `node web/tests/test_payoff_responsivo.mjs` + `npx vite build` + suíte canônica completa, todos exit 0/sem regressão, após a correção
- **Committed in:** `69e38e5`

---

**Total deviations:** 2 auto-fixed (1 Rule 3 — guardião com âncora obsoleta, 1 Rule 1 — bug de posicionamento silencioso descoberto no self-review, não pelos testes estáticos)
**Impact on plan:** Nenhuma mudança de escopo; ambas as correções são estritamente dentro do que o plano já pedia (geometria correta do eixo/marcadores).

## Issues Encountered

- Nenhum bloqueio de execução. O `advisor`, consultado antes deste SUMMARY, apontou o edge case da posição Y do spot (corrigido, ver deviation 2 acima) e confirmou a leitura de `test_estrutura_para_payoff.mjs` individualmente na suíte (OK, sem regressão — arquivo irmão que define o shape que a extração de strikes lê).

## User Setup Required

None - no external service configuration required.

## Known Stubs

Nenhum. O bloco "No vencimento"/"Hoje" e os 3 props novos (`dominio`/`segmentos`/`valorHoje`) são funcionais e completos — só não têm consumidor real ainda (nenhuma tela passa essas props para `PayoffChart`), por desenho: o wiring é o Plano 37-05 (D-09 do `37-CONTEXT.md`). Confirmado por leitura direta: `SecaoAnalisar.jsx`/`SecaoComparar.jsx`/`CuradoriaEstruturas.jsx` continuam nas 4 props antigas (`estrutura`, `emReais`, `cp`, `palette`) após este plano.

## Threat Flags

Nenhum achado de superfície nova fora do que o `<threat_model>` do plano já cobria (T-37-08 aceito, T-37-09 mitigado por leitura/posicionamento sem recálculo — a extrapolação da correção 2 acima usa a MESMA função `entre()` já auditada, não introduz cálculo novo). Nenhum endpoint, rota de auth ou acesso a arquivo novo.

## Verificação

- `node web/tests/test_payoff_responsivo.mjs` — exit 0 (24 asserções: 19 pré-existentes reancoradas + 5 novas)
- `bash scripts/executar.sh --testes` (fora do sandbox, TLS bloqueado dentro dele) — **2973 pytest passed / 5 skipped / 3 xfailed + 156/156 `.mjs`**, exit 0, idêntico à baseline do Plano 37-03 (rodado 2x: após Task 2 e novamente após a correção pós-self-review)
- `npx vite build` (dentro de `web/`) — exit 0, 112 módulos, sem erro de sintaxe (rodado 3x, uma vez por commit)
- 5 acceptance criteria da Task 1 confirmados por grep direto: `PAD_E = 48`, as 4 chaves de copy em uso, `dominio` desestruturado+usado no `useMemo`, `npx vite build` exit 0, os 3 consumidores confirmados nas 4 props antigas (`grep PayoffChart` em `SecaoAnalisar.jsx`/`SecaoComparar.jsx`/`CuradoriaEstruturas.jsx`)
- 4 acceptance criteria da Task 2 confirmados por grep direto: import de `Kicker` de `uiOpcoes.jsx`, as 3 chaves `opcoesNoVencimentoTitulo`/`opcoesHojeTitulo`/`opcoesHojeAjuda` em uso

## Next Phase Readiness

- Backend (37-01/37-03) e camada explicativa (37-02) já prontos; `PayoffChart.jsx` agora aceita `dominio`/`segmentos`/`valorHoje` sem quebrar os 3 consumidores atuais — o Plano 37-05 só precisa PASSAR essas props desde `SecaoAnalisar.jsx`/`SecaoComparar.jsx` (e renderizar `ExplicacaoPayoff.jsx` do 37-02) para fechar CHART-04/CHART-05/EXPL-01..03 de ponta a ponta
- `CuradoriaEstruturas.jsx` continua recebendo a correção de CHART-01/02/03 automaticamente (D-09), sem qualquer edição neste plano — confirmado por leitura direta, nenhuma das 3 chamadas de `PayoffChart` foi tocada
- Nenhum bump/publicação nesta plan — é código de front ainda sem rota de consumo real (mesmo padrão de 37-02/37-03); a publicação acontece no 37-05, que já é `autonomous: false` com checkpoint humano bloqueante

---
*Phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis*
*Completed: 2026-09-22*

## Self-Check: PASSED

- FOUND: `.planning/phases/37-gr-fico-de-payoff-e-explica-o-confi-veis/37-04-SUMMARY.md`
- FOUND: `d3fafb3` (Task 1)
- FOUND: `027cf1a` (Task 2)
- FOUND: `69e38e5` (correção pós-self-review)
