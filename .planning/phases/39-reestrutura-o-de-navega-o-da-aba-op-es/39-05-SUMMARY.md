---
phase: 39-reestrutura-o-de-navega-o-da-aba-op-es
plan: 05
subsystem: testing
tags: [react, opcoes, navegacao, guardian-test, vigias, adr-027]

# Dependency graph
requires:
  - phase: 39-04
    provides: OpcoesScreen.jsx reescrito (abaOpcoes de 3 valores fixos, VigiasBadge/VigiasSheet, PropostaDoAtivo, AbaOportunidades.jsx/AbaRecomendadas.jsx, SecaoDescobrir.jsx/WorkspaceHeader.jsx deletados) e a lista dos 10 guardiões vermelhos esperados
provides:
  - 10 guardiões vermelhos reconciliados (2 arquivos reescritos por completo, 8 com edições cirúrgicas) — cada reversão de invariante documentada com nota datada, cada rename re-ancorado sem perda de cobertura
  - Suíte canônica de volta à baseline: web/tests/*.mjs 163/163 verde, pytest 3021 passed/27 falhas TLS-sandbox pré-existentes (confirmadas artefato via 102/0 fora do sandbox), npx vite build limpo
affects: [39-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reconciliação de guardião pós-refactor de navegação: por arquivo, classificar cada ok( vermelho em (a) âncora mudou/invariante vale — renomear mantendo a mesma condição, (b) invariante revertido de propósito — reescrever com nota datada D-XX, ou (c) defeito real — corrigir o código. Nunca remover um ok( sem substituto."
    - "Falso positivo de guardião por comentário de proveniência: quando um componente novo documenta em prosa que NÃO tem uma característica (ex.: \"sem .manchete próprio\"), a checagem precisa rodar sobre a fonte SEM comentário (semComentario()) antes do regex, senão o próprio texto explicativo dispara a asserção"

key-files:
  modified:
    - web/tests/test_opcoes_subabas_ui.mjs
    - web/tests/test_opcoes_hub_workspace_ui.mjs
    - web/tests/test_opcoes_jornada_ui.mjs
    - web/tests/test_opcoes_consolidacao_ui.mjs
    - web/tests/test_curadoria_ui.mjs
    - web/tests/test_carteira_opcoes_tira.mjs
    - web/tests/test_opcoes_multi_candidato_ui.mjs
    - web/tests/test_fase22_componentes_compartilhados.mjs
    - web/tests/test_opcoes_vigias_ui.mjs
    - web/tests/test_kb_ancoras.mjs

key-decisions:
  - "test_opcoes_hub_workspace_ui.mjs e test_opcoes_consolidacao_ui.mjs foram REESCRITOS por completo (não editados incrementalmente) — o split hub/workspace e SecaoDescobrir.jsx que eles guardavam desapareceram inteiramente; edição incremental teria deixado fatiamento morto (marcadores de código que não existe mais). O histórico das versões antigas está preservado no git log, citado no cabeçalho novo de cada arquivo."
  - "7 dos 12 arquivos do Task 2 (proposta/collar/faixa_liquidez/analisar/custo_declarado/mcp_aba/analisar_executar) já estavam verdes antes de qualquer edição — suas asserções testam comportamento, não a forma dissolvida (SubAbaOperar/SecaoDescobrir/WorkspaceHeader), então sobreviveram ao Plano 39-04 sem precisar de mudança. Confirmado empiricamente (node em cada um, exit 0) antes de declarar 'sem ação necessária', não assumido pela lista do 39-04-SUMMARY."
  - "Contagem de ok( por arquivo antes/depois (exigida pelo repo_guardrail): todos os 10 arquivos fecham >= ao valor anterior (subabas 30/30, hub_workspace 39→41, jornada 53→54, consolidacao 43/43, curadoria 118→121, carteira_opcoes_tira 49/49, multi_candidato 44/44, fase22 113/113, vigias 49→51, kb_ancoras 22→29) — nenhum invariante perdeu cobertura líquida."

patterns-established:
  - "Quando um componente é DISSOLVIDO (não apenas renomeado) e seu invariante de fundo passa a ser garantido por um mecanismo diferente (bloco fixo -> badge+sheet; pill row -> ⓘ contextual; frase-ponte -> chave de copy), a reconciliação escreve uma nota datada explícita citando o D-XX da decisão e troca o MARCADOR de busca, nunca tenta forçar o marcador antigo a continuar existindo em forma degradada"

requirements-completed: [NAV-01]

# Metrics
duration: ~55min
completed: 2026-09-24
---

# Phase 39 Plan 05: Reconciliação dos guardiões vermelhos pós-reestruturação da navegação Summary

**Os 10 guardiões que o Plano 39-04 deixou vermelhos (SubAbaOperar→PropostaDoAtivo, split hub/workspace dissolvido, SecaoDescobrir.jsx deletado, "Seus vigias" virou badge+sheet, "saiba mais" fixo virou ⓘ por aba) foram reconciliados com nota datada em cada reversão — suíte web 163/163 verde, pytest na baseline conhecida (27 falhas de TLS-sandbox confirmadas artefato, não regressão), vite build limpo.**

## Performance

- **Duration:** ~55 min
- **Completed:** 2026-09-24T18:14:00Z
- **Tasks:** 2/2
- **Files modified:** 10 (todos em `web/tests/`, nenhum arquivo de produção tocado)

## Accomplishments

- **Task 1 (5 guardiões estruturais):** `test_opcoes_subabas_ui.mjs` re-ancorado para `function PropostaDoAtivo`/`const abaBar = (` (rename puro, mesma condição em todos os 30 `ok(`), mais um Rule 1 real (falso positivo de `.manchete` num comentário de proveniência de `AbaOportunidades.jsx`, mesma classe do defeito já documentado no 39-04-SUMMARY para o guardião novo). `test_opcoes_hub_workspace_ui.mjs` REESCRITO: WorkspaceHeader.jsx (deletado) vira checagem de `seletor`/`escolherTicker` como caminho único de reset; a adjacência `duasLeiturasIntro`→`SecaoVigias` no hub vira duas checagens (curadoriaSubtitulo nega hierarquia, fork 3 do 39-02; VigiasBadge sempre antes de qualquer aba, D-07); a pill row do ramo 4 vira checagem de que Analisar/Setups sempre aparecem e Comparar fica atrás de `compararAberto` (D-06). `test_opcoes_jornada_ui.mjs`: gate `abaWorkspace !== "setups"` dissolvido em `podePedirLeitura` sozinho; marcador de ordem `{workspacePillRow}` vira `<SecaoAnalisar`/`<SecaoComparar`/`<SecaoSetups`; bloco de anti-inércia do guardião da Fase 34 removido sem substituto (a fatia que ele protegia não existe mais no arquivo irmão). `test_opcoes_consolidacao_ui.mjs` REESCRITO: a ordem sequencial "Bloco A antes de Bloco B" vira checagem de exclusividade mútua entre `abaOpcoes === "oportunidades"`/`"recomendadas"`; `curadoria`/`concluido` passam a atravessar `AbaRecomendadas.jsx` em vez de `SecaoDescobrir.jsx`. `test_curadoria_ui.mjs`: call site de `<CuradoriaEstruturas`/`<OportunidadesOpcoes` migrado para `AbaRecomendadas.jsx`/`AbaOportunidades.jsx`, cada um com o próprio `CarimboFrescor`.
- **Task 2 (5 guardiões restantes + suíte canônica):** `test_carteira_opcoes_tira.mjs` e `test_fase22_componentes_compartilhados.mjs` re-ancorados (rename puro: `SubAbaOperar`→`PropostaDoAtivo`, ordem `<SecaoDescobrir`/`<SecaoVigias`→`<VigiasBadge` antes de qualquer aba). `test_opcoes_multi_candidato_ui.mjs`: 18 ocorrências de `SubAbaOperar` renomeadas em bloco (mesma condição, nenhuma reversão). `test_opcoes_vigias_ui.mjs`: "vigias antes da carteira" (D4) re-ancorado de `<SecaoVigias` para `<VigiasBadge`, e `irParaVigia`/`irParaMontar` (o guarda de toggle que evita desselecionar o ativo já aberto migrou de função). `test_kb_ancoras.mjs`: o "saiba mais" fixo do topo (link único, `fontSize: "12px"`) vira `infoDaAba(` 3x + `BotaoSaibaMais` compartilhado (`uiOpcoes.jsx`, `fontSize: "13px"`, D-13) — os 3 links de Evolução/Mercado/Radar (fora do escopo desta fase) permanecem intocados. Os 7 arquivos restantes do Task 2 (proposta/collar/faixa_liquidez/analisar/custo_declarado/mcp_aba/analisar_executar) já estavam verdes, confirmado por execução, sem edição.
- **Validação final:** `web/tests/*.mjs` completo (163 arquivos, incluindo `test_ios_assets.mjs` — verde neste worktree, `web/ios/` presente) 163/163; `bash scripts/executar.sh --testes` roda o pytest completo (3021 passed/5 skipped/3 xfailed/27 failed) — os 27 são a mesma classe de artefato de sandbox já documentada (`PermissionError: [Errno 1] Operation not permitted` em `ssl.load_verify_locations`, disparado por chamadas de rede real em `test_yahoo_intraday.py`/`test_yahoo_granularidade.py`/`test_benchmark_ibov.py`/`test_options_provider_yahoo.py`/`test_owner.py`/`test_push_registro_evento.py`/`test_rotas_fase4.py`/`test_texto_vazio.py`/`test_fase3_kill_switch_duracao.py`), confirmados fora do sandbox: os mesmos 9 arquivos rodam 102 passed/1 skipped/0 failed. `npx vite build` limpo (117 módulos). `git log --diff-filter=D --name-only 535a3d6..HEAD -- web/tests server/tests` vazio — nenhum arquivo de teste deletado nesta fase.

## Task Commits

1. **Task 1: guardiões estruturais (subabas, hub/workspace, jornada, consolidação, curadoria)** - `449482e` (test)
2. **Task 2: guardiões restantes + suíte canônica** - `914550d` (test)

**Plan metadata:** (a seguir, commit de docs)

## Files Created/Modified

- `web/tests/test_opcoes_subabas_ui.mjs` - `SubAbaOperar`→`PropostaDoAtivo`, `subabas`→`abaBar`, 1 Rule 1 (falso positivo de `.manchete` em comentário)
- `web/tests/test_opcoes_hub_workspace_ui.mjs` - reescrito: WorkspaceHeader.jsx dissolvido em seletor/escolherTicker; adjacência hub em curadoriaSubtitulo+VigiasBadge; pill row do ramo 4 em Analisar/Setups sempre visíveis + compararAberto
- `web/tests/test_opcoes_jornada_ui.mjs` - gate por pill dissolvido em `podePedirLeitura`; marcador de ordem migrado para `<SecaoAnalisar`/`<SecaoComparar`; bloco de anti-inércia removido sem objeto
- `web/tests/test_opcoes_consolidacao_ui.mjs` - reescrito: ordem sequencial vira exclusividade mútua entre abas; call site migrado para AbaOportunidades.jsx/AbaRecomendadas.jsx
- `web/tests/test_curadoria_ui.mjs` - call site migrado para AbaRecomendadas.jsx; ordem/adjacência antigas viram checagem de "cada aba mora no próprio arquivo, com o próprio CarimboFrescor"
- `web/tests/test_carteira_opcoes_tira.mjs` - ordem `<SecaoDescobrir`/`<SecaoVigias` re-ancorada em `<VigiasBadge`
- `web/tests/test_opcoes_multi_candidato_ui.mjs` - `SubAbaOperar`→`PropostaDoAtivo` (18 ocorrências, rename puro)
- `web/tests/test_fase22_componentes_compartilhados.mjs` - `isolarFuncaoDeOpcoesScreen("SubAbaOperar")`→`("PropostaDoAtivo")`
- `web/tests/test_opcoes_vigias_ui.mjs` - "vigias antes da carteira" re-ancorado em VigiasBadge; guarda de toggle migrado para irParaMontar
- `web/tests/test_kb_ancoras.mjs` - "saiba mais" fixo em OpcoesScreen.jsx re-ancorado em `infoDaAba(` 3x + `BotaoSaibaMais` (uiOpcoes.jsx)

## Decisions Made

Nenhuma decisão de arquitetura nova — este plano só reconcilia guardiões de teste contra decisões já travadas nos Planos 39-02/39-03/39-04 (D-01 a D-14). Ver `key-decisions` no frontmatter para as decisões de EXECUÇÃO (reescrever vs. editar incrementalmente, quando considerar um arquivo "já verde", como contar ok( antes/depois).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Falso positivo de `.manchete` em comentário de proveniência, em `test_opcoes_subabas_ui.mjs`**
- **Found during:** Task 1, reconciliação da seção REORG-06 (guardrail CVM de manchete)
- **Issue:** A varredura de diretório que proíbe `.manchete` fora da allowlist (`RENDERIZADORES_DE_MANCHETE`) lia o arquivo BRUTO (com comentários) — o header de `AbaOportunidades.jsx` explica em prosa que o componente é "sem `.manchete` próprio", e essa frase disparava a própria proibição que ela está descrevendo. Mesma classe de defeito já documentada no 39-04-SUMMARY (deviation 4, sobre `test_opcoes_nav_tres_abas_ui.mjs`).
- **Fix:** A checagem passou a rodar `semComentario()` na fonte antes do regex — mesmo helper que o próprio arquivo já usa nas outras seções.
- **Files modified:** `web/tests/test_opcoes_subabas_ui.mjs`
- **Verification:** `node web/tests/test_opcoes_subabas_ui.mjs` sai 0, 30/30 ok.
- **Committed in:** `449482e` (Task 1 commit)

**2. [Rule 1 - Bug] Checagem NAV-05 nova (não pedida pelo plano) causava falso positivo por prop wiring legítima**
- **Found during:** Task 1, ao tentar estender a cobertura de NAV-05 em `test_opcoes_jornada_ui.mjs` para compensar 2 asserções sem objeto do bloco 7 removido
- **Issue:** Uma tentativa de checar "nenhum disparador pago entre o Kicker do estágio 2 e o disclaimer" reprovava porque `<SecaoSetups>` recebe `compilarSetup`/`confirmarSetup` como PROPS (wiring legítimo, não um disparo automático) — a regex de disparadores proibidos não distingue "passado como prop para uso sob clique" de "chamado direto".
- **Fix:** A checagem foi substituída por uma mais estreita e correta (ordem de `<SecaoComparar` em relação ao rótulo do estágio 2), que não depende de heurística de regex sobre prop wiring.
- **Files modified:** `web/tests/test_opcoes_jornada_ui.mjs`
- **Verification:** `node web/tests/test_opcoes_jornada_ui.mjs` sai 0, 54/54 ok.
- **Committed in:** `449482e` (Task 1 commit — corrigido antes do commit, nunca chegou a ser commitado com a checagem falha)

---

**Total deviations:** 2 auto-fixed (Rule 1 — um bug real de guardião pré-existente descoberto ao reconciliar, um erro de escrita do próprio executor corrigido antes de commitar). Nenhum é mudança de escopo ou de comportamento de produto.
**Impact on plan:** Nenhum sobre o comportamento da tela — os dois são correções de precisão de guardião (regex/escopo de checagem).

## Issues Encountered

- **Achado de checklist, não bloqueio:** a instrução do orquestrador para verificar `OpcoesScreen.jsx` linha ~312 quanto a `subaba`/`setSubaba` como "estado morto não usado" não se confirmou — `grep -n "\bsubaba\b"` (sem comentário) no arquivo dá zero ocorrências de CÓDIGO; a linha ~312 é um COMENTÁRIO explicando a decisão de substituir os dois estados antigos por `abaOpcoes` (`// Fase 39 (39-04, D-01): estado único de navegação — substitui \`subaba\`...`). O diagnóstico ao vivo citado na instrução provavelmente se referia a um estado intermediário do arquivo antes do commit `4b24d6c` (Task 2 do 39-04) ter sido finalizado. Nada para remover.
- `grep -c` conta LINHAS que casam, não ocorrências — mesmo gotcha já documentado nos SUMMARYs anteriores da fase. Toda contagem "antes/depois" de `ok(` deste SUMMARY foi feita com `grep -c "ok("` (uma chamada `ok(` por linha neste código, então o gotcha não se aplica aqui — confirmado inspecionando os arquivos, nenhuma chamada `ok(` multi-linha na abertura).

## User Setup Required

None - no external service configuration required.

## Known Stubs

Nenhum stub novo. Este plano só editou arquivos de teste — nenhum componente de produção foi tocado.

## Threat Flags

Nenhuma superfície nova. Os dois threat IDs do `<threat_model>` do plano (T-39-19 repúdio de histórico de decisão, T-39-20 guardião afrouxado) foram os que motivaram o processo de reconciliação inteiro — ambos mitigados por desenho: nenhum `ok(` foi removido sem nota datada, e a contagem antes/depois (frontmatter `key-decisions`) confirma que nenhum arquivo perdeu cobertura líquida.

## Next Phase Readiness

- Suíte canônica na baseline conhecida: `web/tests/*.mjs` 163/163 verde; pytest 3021 passed/27 falhas de TLS-sandbox pré-existente (mesma classe documentada em `[[worktree-test-setup]]`, confirmada artefato fora do sandbox: 102 passed/0 failed nos 9 arquivos envolvidos); `npx vite build` limpo (117 módulos).
- `NAV-01` (3 abas fixas de nível 1) está implementado (39-04) E com a suíte de guardiões reconciliada (39-05) — pronto para o checkpoint humano do `39-06`, que trata das decisões nomeadas DR-1 (destino do card de Oportunidades, divergência da Leitura A do UI-SPEC) e DR-2 (custo do rodapé global vs. só em Montar), ambas já implementadas e aguardando aprovação/rejeição do Alex, não desta fase.
- Nada foi publicado — `scripts/bump.sh`/`publicar-web.sh` seguem fora do escopo deste plano, aguardando o checkpoint bloqueante do 39-06 (guardrail do repositório: "checkpoint bloqueante segura o push da FASE INTEIRA, não só da task, até aprovação").

---
*Phase: 39-reestrutura-o-de-navega-o-da-aba-op-es*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: `web/tests/test_opcoes_subabas_ui.mjs`
- FOUND: `web/tests/test_opcoes_hub_workspace_ui.mjs`
- FOUND: `web/tests/test_opcoes_jornada_ui.mjs`
- FOUND: `web/tests/test_opcoes_consolidacao_ui.mjs`
- FOUND: `web/tests/test_curadoria_ui.mjs`
- FOUND: `web/tests/test_carteira_opcoes_tira.mjs`
- FOUND: `web/tests/test_opcoes_multi_candidato_ui.mjs`
- FOUND: `web/tests/test_fase22_componentes_compartilhados.mjs`
- FOUND: `web/tests/test_opcoes_vigias_ui.mjs`
- FOUND: `web/tests/test_kb_ancoras.mjs`
- FOUND commit `449482e` (Task 1)
- FOUND commit `914550d` (Task 2)
- `node` em cada um dos 10 arquivos reconciliados: 0 (todos verdes)
- `for t in web/tests/*.mjs; do node "$t" ...; done`: 163/163 verdes, zero `VERMELHO`
- `npx vite build`: verde (117 módulos)
- `git log --diff-filter=D --name-only 535a3d6..HEAD -- web/tests server/tests`: vazio (nenhum teste deletado)
