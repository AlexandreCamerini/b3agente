---
quick_id: 260910-red
status: done
commit: b6c986f
files_modified: [web/src/opcoes/OpcoesScreen.jsx, web/tests/test_opcoes_mcp_aba_ui.mjs]
---

# Quick 260910-red: precedência do frescor na aba Opções — SUMMARY

## O que era o defeito

Achado ao vivo em produção (2026-09-10, primeira leitura real de PETR4/VALE3):
a aba Opções mostrava "frescor não medido" mesmo com o dado em dia.

Causa: `web/src/opcoes/OpcoesScreen.jsx:82` escolhia o frescor por ORIGEM da
chamada (`(l && l.frescor) || (status.dados && status.dados.frescor) || null`),
não por qualidade da medição. Sem setups gravados (criar setup é a Fase 5,
ainda não existe), `evaluate_setups` nem é chamada e `_frescor_da_avaliacao`
devolve corretamente `{ medido: false, bloqueia: true }` — um objeto
verdadeiro que o `||` nunca deixa cair para o `/status`, que MEDIU de
verdade via `check_data_freshness`. A informação que não sabe mascarava a
que sabe: **todo** usuário via o aviso de frescor não medido, sempre, com
dado fresco.

Backend confirmado correto (não tocado): `_frescor`/`_frescor_da_avaliacao`
em `server/app/options_mcp_api.py` fazem exatamente o que devem — "não
medido" nunca pode passar por "em dia" (ADR-027, Decisão 8) quando não há
de onde medir.

Mesma classe do defeito 2 corrigido hoje em 260910-d57 (`escolherErroOpcoes`):
precedência decidida por qualidade da informação, não por ordem/origem de
chamada.

## O que mudou

`web/src/opcoes/OpcoesScreen.jsx`:
- Extraído `escolherFrescor(frescorLeitura, frescorStatus)` (mesmo padrão de
  `escolherErroOpcoes`, no fim do arquivo): `medido === true` vence
  `medido !== true`, venha da leitura ou do status; empate (os dois medidos,
  ou nenhum medido) mantém a leitura — é a chamada que a pessoa disparou ao
  escolher o ticker; `null` de um lado nunca vence objeto do outro.
- `pregao` e `fonte` **não mudaram** — continuam com a precedência atual
  (leitura primeiro). Verificado no backend (`server/app/options_mcp_api.py`,
  rota `/leitura`): `propose_option_setups` (fonte de `proposta.trading_date`
  → `pregao`) é chamada SEMPRE, incondicional ao número de setups; só
  `evaluate_setups` (fonte do `frescor`) é pulada quando o ticker não tem
  setup gravado (`if registros:`). Ou seja, o mesmo cenário do incidente
  (`setups=0 avaliou=False`) que deixa `frescor` sem medição NÃO deixa
  `pregao` vazio — os dois campos não compartilham a mesma causa raiz, e a
  precedência "leitura primeiro" continua correta para `pregao`/`fonte`.

`web/tests/test_opcoes_mcp_aba_ui.mjs`:
- Nova seção "4b" com três asserções que travam a CLASSE do defeito (não
  um caso específico): o front não pode voltar a ser um `||` simples entre
  `l.frescor` e `status.dados.frescor`; tem de existir um helper que testa
  `.medido === true`; e o `frescor` do render tem de vir desse helper.
- Asserção de sanidade (`BUG_FRESCOR`) que confirma a regex do "defeito 3
  não voltou" casa contra o padrão antigo literal — sem isso, uma regex
  com typo faria o assert passar sempre, mesmo com o bug de volta.

## Prova RED/GREEN

**RED** — guardião novo rodado contra o código de ANTES (via
`git show HEAD:web/src/opcoes/OpcoesScreen.jsx` para arquivo temporário
FORA do repo, `$TMPDIR/red-proof-260910/`, com as dependências transitivas
copiadas: `useOpcoesMcp.js`, `SetupChart.jsx`, `copy.js`, `disclaimers.js`,
`finance.js`; nunca `git stash`):

```
FALHOU defeito 3 não voltou: `frescor` não é mais um `||` simples entre leitura e status
FALHOU existe helper puro que decide o frescor por `medido`
FALHOU o `frescor` do cabeçalho vem do helper, não de precedência de chamada
ok sanidade: a regex do defeito 3 pega o padrão antigo quando ele existe
...
3 FALHA(S)
EXIT=1
```

Só as 3 asserções novas falharam; todas as outras (incluindo a sanidade)
passaram — confirma que o guardião pega exatamente a classe do defeito, sem
falso positivo em asserção pré-existente.

**GREEN** — mesmo guardião rodado contra o código corrigido
(`node web/tests/test_opcoes_mcp_aba_ui.mjs`, arquivo real do worktree):

```
ok defeito 3 não voltou: `frescor` não é mais um `||` simples entre leitura e status
ok existe helper puro que decide o frescor por `medido`
ok o `frescor` do cabeçalho vem do helper, não de precedência de chamada
ok sanidade: a regex do defeito 3 pega o padrão antigo quando ele existe
...
todos os testes passaram
EXIT=0
```

## Suíte canônica

`bash scripts/executar.sh --testes` (rodado com `dangerouslyDisableSandbox`
após falha de sandbox ao escrever `.log` na raiz do sistema — `Operation not
permitted`, não relacionado ao código): **2244 passed, 4 skipped** (pytest)
+ todas as suítes `web/tests/*.mjs` com `[OK]`, incluindo
`test_opcoes_mcp_aba_ui.mjs`. Saída final: `EXIT=0`.

## Build

`cd web && npx vite build`: `✓ 94 modules transformed`, `✓ built in 987ms`,
PWA precache gerado (23 entries). O aviso de chunk > 500 kB é pré-existente
(bundle único `index-*.js` de 827 kB), não relacionado a esta correção.

## Deviations from Plan

Nenhuma — plano executado exatamente como escrito. `pregao`/`fonte`
verificados e confirmados corretos com a precedência atual (não alterados,
conforme instrução do plano).

## Known Stubs

Nenhum.

## Threat Flags

Nenhum — mudança é puramente de precedência de leitura de dado já exposto
pelo backend, sem nova superfície.

## Nota final — esta correção ainda NÃO chegou ao usuário

Este quick só mudou `web/src/opcoes/OpcoesScreen.jsx` e o teste. O front
compilado que serve produção vive em `server/web_dist` (artefato
versionado) — o `npx vite build` rodado aqui gerou `web/dist/`, mas isso
**não é** `server/web_dist`. Para o usuário ver o dado em dia sem o aviso
de "frescor não medido":

1. `scripts/bump.sh`
2. `scripts/publicar-web.sh`
3. clique de deploy no Railway

Sem esses três passos, o defeito continua visível em produção mesmo com
este commit mesclado.

## Self-Check: PASSED

- FOUND: web/src/opcoes/OpcoesScreen.jsx (helper `escolherFrescor` presente)
- FOUND: web/tests/test_opcoes_mcp_aba_ui.mjs (seção 4b presente)
- FOUND commit b6c986f (git log --oneline confirma)
