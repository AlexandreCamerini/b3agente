---
phase: 28-aba-opcoes-sub-aba-operar
plan: 02
subsystem: ui
tags: [react, jsx, opcoes, adr-027, sub-tabs]

# Dependency graph
requires:
  - phase: 28-aba-opcoes-sub-aba-operar
    plan: "28-01"
    provides: "web/src/opcoes/PropostaLastreada.jsx (default PropostaLastreada, FonteDoDadoProposta, ChipDaProposta, useAceiteLastreado)"
provides:
  - "web/src/opcoes/OpcoesScreen.jsx — alternador de sub-aba (\"Setups\"/\"Operar\") e componente SubAbaOperar, consumindo PropostaLastreada e useAceiteLastreado sem importar App.jsx"
  - "web/src/copy.js — chaves opcoesSubabaSetups/opcoesSubabaOperar/opcoesOperarIntro/opcoesOperarEscolherPosicao/opcoesOperarSemLiquidez, paridade intacta"
  - "web/tests/test_opcoes_subabas_ui.mjs — guardião novo, 24 asserções, 3 injeções de defeito provadas"
affects: ["28-03-remocao-card-watchlist-radar"]

tech-stack:
  added: []
  patterns:
    - "Sub-aba dentro de uma tela existente via useState + ternário no return, reusando os mesmos tokens/régua visual do seletor já presente (nenhum token novo)"
    - "Componente de sub-aba recebe o seletor de chips por PROP (não reimplementa), garantindo ticker compartilhado entre sub-abas"

key-files:
  created:
    - web/tests/test_opcoes_subabas_ui.mjs
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/copy.js

key-decisions:
  - "Ramo multi-candidato (CandidatoOpcao) NÃO replicado em SubAbaOperar — fica exclusivo de App.jsx/PropostaDaPosicao (App.jsx, dentro da função PropostaDaPosicao). Com multi-candidato, PropostaLastreada mostra r.proposta (candidato principal), mesmo comportamento de AtivoCard hoje. Registrado em comentário no código, acima de SubAbaOperar, para a Fase 30 não redescobrir."
  - "Import de FonteDoDadoProposta em OpcoesScreen.jsx: o plano pedia o import literal (Task 2, passo 1), mas PropostaLastreada já a renderiza internamente — SubAbaOperar nunca a usou direto. Corrigido no self-review pós-execução (removido, commit 5803c4d): manter import morto contradiria diffs limpos/deliberados. As acceptance criteria do plano nunca checam esse símbolo, então a remoção não quebra nenhum critério."

requirements-completed: [SC-1, SC-4]

duration: ~70min
completed: 2026-09-13
---

# Phase 28 Plan 02: Sub-aba Operar dentro da aba Opções Summary

**A aba Opções ganhou duas sub-abas alternáveis — "Setups" (a tela da Fase 27, intocada) e "Operar" (nova) — e a sub-aba Operar renderiza a proposta lastreada de uma posição da carteira via o módulo `PropostaLastreada` extraído no 28-01, com custo zero de MCP e sem nenhum import de `App.jsx`.**

## Performance

- **Duration:** ~70 min
- **Tasks:** 3/3
- **Files modified:** 2 (`OpcoesScreen.jsx`, `copy.js`) + 1 criado (`test_opcoes_subabas_ui.mjs`)
- **Tool-call count desta sessão:** ~55 chamadas de ferramenta (Read/Grep/Bash/Edit/Write), a maioria Bash de verificação pontual e grep cirúrgico — nenhuma leitura de arquivo grande sem offset/limit, `App.jsx`/`OpcoesScreen.jsx` lidos só nas faixas de linha citadas pelo `<read_first>` do plano ou localizadas por grep. `STATE.md` não foi lido (proibido pela orquestração). Suíte canônica rodada 2× (a segunda foi necessária por um artefato de build local, não por erro de código — ver Deviations).

## Contagem de arquivos `.mjs`

- Antes (baseline herdada do 28-01): 143
- Depois (Task 3): **144** (+1, `test_opcoes_subabas_ui.mjs`)

## Accomplishments

- **Task 1 — copy.js:** cinco chaves novas em `COPY.estudo` e `COPY.operador` (`opcoesSubabaSetups`, `opcoesSubabaOperar`, `opcoesOperarIntro`, `opcoesOperarEscolherPosicao`, `opcoesOperarSemLiquidez`). `opcoesSubabaSetups` é igual nos dois modos (nome do artefato, mesma razão de `tituloOpcoes`); `opcoesSubabaOperar` difere ("Operação" no Estudo, substantivo — "Operar" no Operador, imperativo). Paridade de chaves intacta (`test_copy_theme.mjs`, `test_opcoes_mcp_aba_ui.mjs` verdes sem edição).
- **Task 2 — OpcoesScreen.jsx:** import de `PropostaLastreada`/`FonteDoDadoProposta`/`useAceiteLastreado` (sem import de `App.jsx`); estado `subaba` (`useState("setups")`); alternador `subabas` com a MESMA régua visual do `seletor` existente (mesmos tokens de `TOKENS`, `aria-pressed`, `minHeight: "44px"`); o corpo inteiro da Fase 27 (`cabecalho`, `blocoVigias`, `seletor`, `LastroDoAtivo`, `LeituraInterna`, `blocoLeituraDoServico`, a cascata carregando/erro/vazio/dados e o disclaimer) só ganhou indentação dentro do ramo `subaba === "setups"` — `git diff` confirma que a ÚNICA linha removida foi o `import { useState }` (substituído por `import { useState, useEffect }`), zero remoção de conteúdo. `SubAbaOperar` declarado depois de `OpcoesScreen`, reusando `Aviso`, `BOTAO`, `LastroDoAtivo`, `LeituraInterna` verbatim; recebe `seletor` por prop (não reimplementa); dois `useEffect` em cascata (`store.optionsGate`→`store.optionsProposta`, guardados por `gate && gate.liquida` primitivo, `vivo` flag no cleanup) espelhando `AtivoCard`; zero `store.mcp*` no corpo do componente.
- **Task 3 — guardião novo:** `web/tests/test_opcoes_subabas_ui.mjs`, 24 asserções `ok`, cobrindo os 11 invariantes do `<behavior>` do plano (isolamento de duas vias, custo zero de MCP, gate/proposta sem duplicação nem chamada desguardada, manchete só via `PropostaLastreada`, aceite único via `useAceiteLastreado`, fonte única de `appMode`, universo=carteira, alternador com `aria-pressed`/44px, blocos da Fase 27 intactos). Asserção de "parse mudo" (fatia de `SubAbaOperar` localizada e com >300 caracteres) evita que um recorte vazio faça as negativas passarem de graça.

## Injeções de defeito (provadas vermelhas, revertidas)

Todas aplicadas com `python3`/edição pontual, confirmado vermelho, revertidas com `git checkout --` (working tree limpo depois de cada uma):

**(a) Remover a guarda de `gate.liquida` antes de `store.optionsProposta`:**
```
if (!store || !ticker || !(gate && gate.liquida)) return () => { vivo = false; };
```
virou
```
if (!store || !ticker) return () => { vivo = false; };
```
Saída: `FALHOU a chamada de store.optionsProposta está guardada por um if/return que testa gate/liquida ANTES da chamada` (exit 1).

**Achado durante a escrita do próprio guardião** (não é bug de produto): a primeira versão da asserção 4 aceitava a presença literal da substring `gate && gate.liquida` EM QUALQUER LUGAR do corpo de `SubAbaOperar` — incluindo o array de dependências do `useEffect` (`[store, ticker, gate && gate.liquida]`), que sempre existe mesmo com a guarda removida do `if`. A injeção (a) não disparou na primeira tentativa por esse motivo. Corrigido: a asserção agora recorta só o texto ENTRE `setProp(null);` e a chamada `store.optionsProposta(`, e exige um `if (...!(gate && gate.liquida)...) return` nesse recorte especificamente. Sem essa correção, o guardião seria decoração para exatamente o invariante mais citado no `<threat_model>` (T-28-09).

**(b) Inserir `store.mcpLeitura(ticker)` no corpo de `SubAbaOperar`:**
```js
const operador = !!(ctx && ctx.operador);
if (store && ticker) { /* injeção de defeito temporária */ store.mcpLeitura(ticker); }
```
Saída: `FALHOU SubAbaOperar não chama nenhum método store.mcp* (ADR-027 §3.3)` (exit 1).

**(c) Trocar `ctx.operador` por `ctx.data.config.appMode === "operador"`:**
```js
const operador = !!(ctx && ctx.data && ctx.data.config && ctx.data.config.appMode === "operador");
```
Saída: `FALHOU SubAbaOperar deriva o modo só de ctx.operador` (exit 1).

## Task Commits

1. **Task 1: Chaves de copy da sub-aba Operar nos dois modos** — `86f4f36` (feat)
2. **Task 2: Alternador de sub-aba e SubAbaOperar em OpcoesScreen.jsx** — `3d0f29a` (feat)
3. **Task 3: Guardião das sub-abas** — `f8409ad` (test)
4. **Self-review (advisor): remove import não usado de FonteDoDadoProposta** — `5803c4d` (refactor)

_Sem plano de publicação: `commit_docs=true`, mas STATE.md/ROADMAP.md ficam para o orquestrador atualizar à mão (gsd-sdk `state.*`/`roadmap.*` mutators proibidos neste repositório — ver CLAUDE.md)._

## Files Created/Modified

- `web/src/copy.js` — 5 chaves novas × 2 ramos (`estudo`/`operador`)
- `web/src/opcoes/OpcoesScreen.jsx` — import do módulo 28-01; estado `subaba`; alternador `subabas`; `return` recomposto (ternário `subaba === "setups"` vs `<SubAbaOperar>`); função `SubAbaOperar` nova
- `web/tests/test_opcoes_subabas_ui.mjs` (criado) — guardião novo

## Verification

1. `npx vite build` — verde (2×, Task 2 e final)
2. `node web/tests/test_opcoes_subabas_ui.mjs` — verde, 24 `ok` (≥12 exigido)
3. 3 injeções de defeito → vermelho cada uma → revertidas (ver acima)
4. `bash scripts/executar.sh --testes` fora do sandbox — 0 falhas: `2780 passed, 5 skipped, 3 xfailed` (idêntico à baseline do 28-01) + `144/144 .mjs` (baseline 143 + esta), exit 0
5. `grep -c "carteira.map(" web/src/opcoes/OpcoesScreen.jsx` = 2 (mesmo número de hoje: `tickersEmCarteira` + `seletor` — nenhuma terceira ocorrência, o seletor não foi duplicado)
6. `git diff --stat web/src/persistence.js web/src/opcoes/useOpcoesMcp.js web/src/App.jsx` — vazio

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário em SubAbaOperar continha a string literal `store.mcp*`, disparando o próprio verify script do plano por engano**
- **Found during:** Task 2, verificação automatizada
- **Issue:** o comentário acima dos dois `useEffect` (explicando por que as rotas são de custo zero) citava `store.mcp*` como texto explicativo — o script de verificação do plano faz `/store\.mcp/.test(body)` sobre o CORPO BRUTO da função (sem remover comentários), então o próprio comentário fez a checagem falhar.
- **Fix:** reescrito o comentário para descrever "os métodos de leitura paga do serviço externo (o prefixo `mcp` do store)" em vez de citar o padrão literalmente.
- **Files modified:** `web/src/opcoes/OpcoesScreen.jsx`
- **Verificação:** `grep -n "store\.mcp" web/src/opcoes/OpcoesScreen.jsx` só encontra ocorrências dentro dos dois `useEffect` de leitura (que são `store.optionsGate`/`store.optionsProposta`, não `store.mcp*`); o verify script do plano passa.
- **Committed in:** `3d0f29a`

**2. [Rule 1 - Bug] Assinatura falsa-positiva na primeira versão da asserção 4 do guardião novo**
- **Found during:** Task 3, ao provar a injeção de defeito (a)
- **Issue:** ver detalhamento na seção "Injeções de defeito" acima — a asserção original aceitava `gate && gate.liquida` presente em QUALQUER lugar do corpo de `SubAbaOperar`, incluindo o array de dependências do `useEffect`, que nunca muda mesmo com o `if` de guarda removido.
- **Fix:** a asserção agora recorta o texto entre `setProp(null);` e a chamada `store.optionsProposta(` e exige o padrão de guarda (`if (...!(gate && gate.liquida)...) return`) especificamente nesse recorte.
- **Files modified:** `web/tests/test_opcoes_subabas_ui.mjs`
- **Verificação:** reaplicada a injeção (a) depois da correção — falhou como esperado (ver acima).
- **Committed in:** `f8409ad` (a versão corrigida já foi a única commitada — o guardião nunca chegou a ser commitado na forma falho-positiva)

**3. [Rule 3 - Blocking] `web/dist` desatualizado fazendo `test_ios_assets.mjs` reprovar na primeira rodada da suíte canônica**
- **Found during:** primeira execução de `bash scripts/executar.sh --testes` (verificação final da Task 3)
- **Issue:** `npx vite build` (rodado na Task 2) regenerou `web/dist` com hashes de chunk novos, sob o mesmo `BUILD_ID` do último `server/web_dist` publicado — exatamente o mesmo artefato de build local já documentado no `28-01-SUMMARY.md` ("Issues Encountered"), não uma regressão desta plano. `test_ios_assets.mjs` reprovou a paridade dist↔ios-bundle.
- **Fix:** restaurado `web/dist` a partir de `server/web_dist` (`rm -rf web/dist && cp -R server/web_dist web/dist`) — mesmo padrão do 28-01. Ambos os diretórios são gitignorados; nenhum arquivo versionado foi tocado.
- **Files modified:** nenhum arquivo versionado (só diretórios de build locais, gitignorados)
- **Verificação:** `node web/tests/test_ios_assets.mjs` passa isoladamente; suíte canônica completa re-rodada depois, verde (exit 0, 144/144 `.mjs`, 2780 passed pytest).
- **Committed in:** N/A (gitignorado, nada a commitar)

---

**Total deviations:** 3 auto-fixed (2× Rule 1, 1× Rule 3). Nenhuma mudou comportamento de produto: a primeira é correção de texto de comentário, a segunda é correção do PRÓPRIO guardião novo antes de ser commitado, a terceira é um artefato de build local (não versionado) já precedente do plano anterior.

## Issues Encountered

Nenhum além dos já documentados em Deviations.

## Known Stubs

Nenhum. `SubAbaOperar` lê dados reais (`store.optionsGate`/`store.optionsProposta`, `ctx.data.positions`, `ctx.data.optionPositions`) — nenhum valor hardcoded vazio nem placeholder de "em breve".

## Threat Flags

Nenhuma superfície nova fora do `threat_model` do próprio plano. Os 8 itens `mitigate` (T-28-08 a T-28-14) e os 2 `accept` (T-28-15, T-28-SC) foram todos verificados nas 3 injeções de defeito + acceptance criteria — nenhum caminho de rede, auth ou schema novo foi introduzido: as duas rotas usadas (`/api/options/gate`, `/api/options/proposta`) já existiam e já eram consumidas por `AtivoCard`.

## User Setup Required

None — nenhuma configuração de serviço externo.

## Next Phase Readiness

- A sub-aba "Operar" está pronta e testada; a Fase 28-03 (remoção do card duplicado em `AtivoCard`/Watchlist/Radar) pode prosseguir com a certeza de que a Fase 28-02 não tocou `AtivoCard` nem `useOpcoesMcp.js`/`persistence.js`.
- Decisão registrada em código (comentário acima de `SubAbaOperar`, `web/src/opcoes/OpcoesScreen.jsx`) para a Fase 30: o ramo multi-candidato (`CandidatoOpcao`) continua exclusivo de `App.jsx`/`PropostaDaPosicao` — não foi replicado aqui.
- Nenhum bloqueio conhecido. Publicação (bump + `publicar-web.sh`) segue fora de escopo desta fase, como no 28-01.

## Self-Check: PASSED

Arquivos verificados no disco: `web/src/copy.js`, `web/src/opcoes/OpcoesScreen.jsx`, `web/tests/test_opcoes_subabas_ui.mjs` — todos encontrados com o conteúdo esperado. Commits `86f4f36`, `3d0f29a`, `f8409ad` encontrados em `git log --oneline --all`. Suíte canônica rodada 2× (a segunda após a correção do artefato de `web/dist`), verde na rodada final: `2780 passed, 5 skipped, 3 xfailed` + `144/144 .mjs`, exit 0.

---
*Phase: 28-aba-opcoes-sub-aba-operar*
*Completed: 2026-09-13*
