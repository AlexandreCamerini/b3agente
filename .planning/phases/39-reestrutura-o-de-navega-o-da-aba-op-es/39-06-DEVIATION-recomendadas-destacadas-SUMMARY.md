---
phase: 39-reestrutura-o-de-navega-o-da-aba-op-es
plan: 06
subsystem: ui
tags: [copy.js, opcoes, navegacao, regulatorio, cvm, override]

# Dependency graph
requires:
  - phase: 39-02
    provides: "copy.js com opcoesAbaRecomendadas e o grupo linhaChamadaOpcoes* (D-01/D-02/D-03), consumidos por este deviation"
provides:
  - "Rótulo user-facing da 3ª aba fixa de Opções trocado de 'Recomendadas' para 'Destacadas' (só o texto — id interno, nome do componente e chave de copy preservados)"
  - "Copy descritiva ligada a essa aba (linha de chamada de Posições) trocada de 'recomendada(s)' para 'destacada(s)' nos dois modos"
affects: [39-06]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - web/src/copy.js
    - web/src/opcoes/OpcoesScreen.jsx
    - web/tests/test_consolidacao_opcoes_copy.mjs

key-decisions:
  - "Override deliberado de D-03 (CONTEXT.md), decidido pelo Alex AO VIVO durante o checkpoint humano da Task 1 do 39-06: o rótulo 'Recomendadas' colide com o disclaimer 'nada aqui é recomendação de compra/venda' e com a leitura regulatória CVM de recomendação — trocado para 'Destacadas'. Motivo idêntico ao risco (a) já registrado no roteiro de verificação do 39-06-PLAN.md."
  - "Renomeação escopada a TEXTO VISÍVEL apenas: a chave de copy `opcoesAbaRecomendadas` NÃO foi renomeada (só o valor mudou), o id interno da aba `'recomendadas'` em ABAS_OPCOES/OpcoesScreen.jsx NÃO mudou, e o componente `AbaRecomendadas.jsx` mantém nome de arquivo/export — são identificadores JS internos, não texto de usuário."
  - "Grupo `linhaChamadaOpcoes*` (linha de chamada de Posições) também renomeado porque é copy descritiva da MESMA feature usando 'recomendada(s)' como sinônimo do nome da aba (confirmado pelo próprio comentário do arquivo: 'a contagem é da aba Recomendadas') — inclui `linhaChamadaOpcoesTexto` (singular/plural), `linhaChamadaOpcoesVazia` e `linhaChamadaOpcoesCarregando`, nos dois modos."
  - "Fallbacks `cp.opcoesAbaRecomendadas || \"Recomendadas\"` em OpcoesScreen.jsx (abaBar e infoBotao) também atualizados para \"Destacadas\" — são o mesmo texto visível, só como valor-padrão caso a chave de copy falte."
  - "Comentários internos de código/testes que mencionam 'Recomendadas' como nome HISTÓRICO/INTERNO da aba (ex.: 'AbaOportunidades/Recomendadas agora são abas irmãs', nomes de variável `abaRecomendadasSC`, o id `'recomendadas'` em asserções) foram DELIBERADAMENTE deixados como estão — não são texto de usuário, e mudar o vocabulário de identificador interno está fora do escopo desta rename e fora do pedido do Alex."

patterns-established: []

requirements-completed: []

# Metrics
duration: ~25min
completed: 2026-09-24
---

# Phase 39 Plan 06 (deviation): rename "Recomendadas" → "Destacadas" na aba Opções Summary

**Rótulo da 3ª aba fixa de Opções e a copy descritiva ligada a ela ("N estruturas recomendadas...") trocados de "recomendada(s)" para "destacada(s)" nos dois modos — override deliberado da decisão travada D-03, aprovado pelo Alex ao vivo no checkpoint do 39-06 por ambiguidade regulatória CVM.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-09-24T20:47:14Z
- **Tasks:** 1 (deviation atômico, fora da numeração de tasks do 39-06-PLAN.md)
- **Files modified:** 3 (web/src/copy.js, web/src/opcoes/OpcoesScreen.jsx, web/tests/test_consolidacao_opcoes_copy.mjs)

## Contexto e motivo

Durante a verificação humana ao vivo da Task 1 do plano 39-06, o Alex revisou a navegação
nova de 3 abas (Oportunidades / Recomendadas / Montar) e decidiu, na hora, renomear a aba
"Recomendadas" para "Destacadas". Essa decisão SOBRESCREVE deliberadamente D-03 (CONTEXT.md),
que havia travado o nome "Recomendadas". O próprio roteiro do 39-06-PLAN.md já registrava
esse risco regulatório como item (a) das "Riscos para o Alex decidir": *"o rótulo
'Recomendadas' convive com o disclaimer 'nada aqui é recomendação' e com a leitura
regulatória (CVM) de recomendação — D-03 travou o nome; manter?"* — o Alex respondeu que não,
e pediu a troca para "Destacadas".

Esta é a decisão do Alex, não uma reinterpretação do planner; documentada aqui como deviation
atômico, ANTES da Task 2 (publicação) do 39-06, para não misturar a mudança de rótulo com o
bump/publish daquele plano.

## Escopo aplicado

**Renomeado (texto visível ao usuário):**
1. `copy.js` — `opcoesAbaRecomendadas` (valor da chave, Estudo e Operador): `"Recomendadas"` → `"Destacadas"`.
2. `copy.js` — grupo `linhaChamadaOpcoes*` (linha de chamada em Posições, Estudo e Operador):
   - `linhaChamadaOpcoesTexto(1)`: `"1 estrutura recomendada nas suas posições"` → `"1 estrutura destacada nas suas posições"`
   - `linhaChamadaOpcoesTexto(n>1)`: `"${n} estruturas recomendadas nas suas posições"` → `"${n} estruturas destacadas nas suas posições"`
   - `linhaChamadaOpcoesVazia`: `"Nenhuma estrutura recomendada agora"` → `"Nenhuma estrutura destacada agora"`
   - `linhaChamadaOpcoesCarregando`: `"Verificando estruturas recomendadas…"` → `"Verificando estruturas destacadas…"`
3. `web/src/opcoes/OpcoesScreen.jsx` — dois fallbacks de string (mesmo texto visível, valor-padrão caso a copy falte):
   - `{ id: "recomendadas", rotulo: cp.opcoesAbaRecomendadas || "Recomendadas" }` → `|| "Destacadas"`
   - `infoBotao={infoDaAba(cp.opcoesAbaRecomendadas || "Recomendadas")}` → `|| "Destacadas"`
4. `web/tests/test_consolidacao_opcoes_copy.mjs` — assertions de singular/plural do item 4 atualizadas para `"1 estrutura destacada"` / `"3 estruturas destacadas"`.

**Deliberadamente NÃO renomeado (identificador interno, não texto de usuário)** — lista completa
verificada por grep em `web/src` e `web/tests` após a mudança:

| O que ficou como estava | Onde | Por quê |
|---|---|---|
| Chave de copy `opcoesAbaRecomendadas` | `copy.js` (nome da chave) | É identificador JS, nunca visível ao usuário; só o valor muda (regra explícita do escopo) |
| Id interno da aba `"recomendadas"` | `OpcoesScreen.jsx` (`ABAS_OPCOES`, `{ id: "recomendadas", ... }`, `abaOpcoes === "recomendadas"`) | Discriminador de estado interno, não string exibida |
| Componente `AbaRecomendadas` / arquivo `AbaRecomendadas.jsx` | `web/src/opcoes/AbaRecomendadas.jsx` e imports | Nome de módulo/export JS |
| Variáveis de teste `abaRecomendadasSC`, `abaRecomendadasBruto`, `corpoRamoRecomendadas`, `ramoRecomendadas`, `iRamoRecomendadas`, etc. | `web/tests/test_curadoria_ui.mjs`, `test_opcoes_consolidacao_ui.mjs`, `test_opcoes_nav_tres_abas_ui.mjs` | Nomes de variável local do teste, não asserção sobre texto de usuário |
| Comentários de código/teste citando "aba Recomendadas" como referência histórica/interna (ex.: "Oportunidades/Recomendadas agora são abas irmãs", "de SecaoDescobrir.jsx para AbaRecomendadas.jsx") | `OpcoesScreen.jsx`, `AbaOportunidades.jsx`, `uiOpcoes.jsx`, e ~10 arquivos de teste listados no escopo original | Documentação de decisão de arquitetura interna (D-01/D-02/D-05), não string renderizada; alterar exigiria reescrever histórico de comentários sem ganho — mantidos como estavam, com a ressalva de que 2 comentários NOVOS em `copy.js` (adicionados por esta mudança) já explicam a divergência entre o nome interno e o rótulo visível atual |
| `server/app/*.py` | backend inteiro | Confirmado por grep `recomendad` (case-insensitive): 3 ocorrências de "recomendado" em `model_catalog.py` (tier de modelo de LLM, ex.: "Econômico · rápido (recomendado)") e 1 ocorrência em comentário de histórico do `SERVER_BUILD_ID` em `main.py` ("fica registrada como pendência recomendada") — nenhuma relacionada à aba de Opções; zero mudança de backend necessária ou feita |

## Task Commits

1. **Deviation: renomeia aba Recomendadas para Destacadas (override D-03, decisão do Alex)** - `6a4e819` (feat)

## Files Created/Modified

- `web/src/copy.js` - `opcoesAbaRecomendadas` e o grupo `linhaChamadaOpcoes*` (Estudo+Operador) trocados para "Destacadas"/"destacada(s)", com comentário datado explicando o override de D-03
- `web/src/opcoes/OpcoesScreen.jsx` - 2 fallbacks de string (abaBar, infoBotao do ⓘ) atualizados para "Destacadas"
- `web/tests/test_consolidacao_opcoes_copy.mjs` - assertions de singular/plural atualizadas para "estrutura(s) destacada(s)"

## Decisions Made

Ver `key-decisions` no frontmatter — resumo: override explícito de D-03 pelo Alex, escopo
restrito a texto visível, identificadores internos preservados intencionalmente.

## Deviations from Plan

Este documento inteiro É o deviation (Rule 4 — mudança de produto pedida explicitamente pelo
dono do produto, não uma correção automática de bug/gap). Não houve deviations adicionais
DENTRO da execução desta rename — nenhum bug encontrado, nenhuma dependência quebrada.

## Issues Encountered

- `bash scripts/executar.sh --testes` dentro do sandbox padrão retornou 27 falhas no backend,
  todas `PermissionError: [Errno 1] Operation not permitted` em `ssl.py` (chamadas TLS de
  rede bloqueadas pelo sandbox) — o mesmo artefato de ambiente já documentado na memória do
  projeto ("sandbox mente"). Como `scripts/test.sh` aborta o `executar.sh --testes` inteiro
  (inclusive a suíte web) na primeira falha do backend, a suíte web nunca chegou a rodar
  dentro do sandbox padrão. Reexecutado com sandbox desabilitado para validar de verdade:
  backend zerou as 27 falhas (rede disponível), suíte web 100% verde. Nenhum código de
  produto foi alterado por causa disso — é puramente o ambiente de execução da validação.

## User Setup Required

None - no external service configuration required.

## Validação executada

- `bash scripts/executar.sh --testes` (sandbox desabilitado, para permitir rede real): backend
  `3048 passed, 5 skipped, 3 xfailed` (0 failed); suíte web `web/tests/*.mjs` — todos os
  arquivos `[OK]`, exit 0.
- Conferidos explicitamente, um a um, os 9 arquivos de teste apontados como "conhecidos" no
  escopo original desta rename (`test_opcoes_consolidacao_ui.mjs`,
  `test_opcoes_hub_workspace_ui.mjs`, `test_curadoria_ui.mjs`, `test_opcoes_subabas_ui.mjs`,
  `test_consolidacao_opcoes_copy.mjs`, `test_carteira_opcoes_tira.mjs`,
  `test_opcoes_nav_primitivos_ui.mjs`, `test_opcoes_nav_tres_abas_ui.mjs`,
  `test_kb_ancoras.mjs`) — só `test_consolidacao_opcoes_copy.mjs` tinha assertion sobre o
  VALOR da copy (singular/plural de `linhaChamadaOpcoesTexto`) e foi atualizado; os outros 8
  só referenciam nome de componente (`AbaRecomendadas`), id interno (`"recomendadas"`) ou
  comentário de arquitetura, nada que precisasse mudar.
- Grep final e específico por assertion de VALOR (não apenas menção) confirmando que nenhum
  guardião trava o texto antigo como esperado: `grep -rn '=== "Recomendadas"\|\.includes("Recomendadas")\|"Recomendadas"' web/tests/*.mjs` devolveu zero ocorrências — nenhum teste
  espera literalmente "Recomendadas" como valor, nem via `===` nem via `.includes`.
- `cd web && npx vite build`: `✓ 117 modules transformed`, build limpo, sem erro de sintaxe.
- Grep de confirmação pós-mudança em `web/src` e `web/tests`: toda ocorrência remanescente de
  "Recomendadas"/"recomendada(s)" é identificador interno ou comentário de arquitetura (ver
  tabela acima) — nenhum texto renderizado ao usuário ficou com o nome antigo.
- Grep de confirmação em `server/app`: nenhuma ocorrência de "recomendad" relacionada à aba de
  Opções (as 4 ocorrências existentes são de outro domínio — tier de modelo de LLM e um
  comentário de histórico de build não relacionado).

## Next Phase Readiness

- Esta rename fica pronta ANTES da Task 2 (publicar) do 39-06-PLAN.md, como pedido — o próximo
  passo é a Task 2 daquele plano (bump + publicar-web.sh), que agora vai empacotar o bundle já
  com "Destacadas".
- A Task 3 do 39-06-PLAN.md (fechamento de STATE.md/ROADMAP.md/REQUIREMENTS.md) deve referenciar
  esta decisão ao registrar o fechamento da Fase 39: o nome final da 3ª aba é "Destacadas", não
  "Recomendadas" como D-03 originalmente travava — este SUMMARY é a fonte da decisão e do
  motivo (CVM) para quem for escrever aquele registro.
- Nenhum arquivo de `.planning/STATE.md`, `.planning/ROADMAP.md` ou `.planning/REQUIREMENTS.md`
  foi tocado por este deviation, por desenho — isso pertence à Task 3 do 39-06, executada
  separadamente.

---
*Phase: 39-reestrutura-o-de-navega-o-da-aba-op-es*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: `web/src/copy.js` com `opcoesAbaRecomendadas: "Destacadas"` (2x, Estudo+Operador)
- FOUND: `web/src/opcoes/OpcoesScreen.jsx` com os 2 fallbacks `|| "Destacadas"`
- FOUND: `web/tests/test_consolidacao_opcoes_copy.mjs` com asserções "estrutura(s) destacada(s)"
- Suíte canônica verde (backend 3048 passed/5 skipped/3 xfailed; web 100% .mjs OK), `npx vite build` limpo
