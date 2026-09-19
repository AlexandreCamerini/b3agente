---
phase: 24-opcoes-mcp-analise-e-setups
plan: 04
subsystem: front
tags: [react, opcoes, setups, rbac, copy, stores, guardiao, backtest]

# Dependency graph
requires:
  - phase: 24 (plano 24-03)
    provides: "`POST /setups/compilar` (dry-run obrigatório), `/setups/confirmar`, `/setups/{name}/desativar` com `require_criar_setup`, envelope estável e 422 `setup_invalido` com `problems[]`"
  - phase: 24 (plano 24-02)
    provides: "`useChamadaSobDemanda`, `ErroDoMcp`, `BOTAO`/`CAMPO` com 44 px, o bloco `opcoes*` de copy nas duas vozes"
  - phase: ADR-013
    provides: "`permissions` no `_public_user` e o precedente de leitura no front (`ctx.authUser.permissions`, grupo Administração do Perfil)"
provides:
  - "`CriarSetup.jsx` — descrição em PT-BR → interpretação + ensaio no histórico → gravar, com desativação em dois toques"
  - "`BotaoDesativar` — confirmação em dois toques, reusável por qualquer card de setup"
  - "seção Criar setup em `OpcoesScreen`, montada só sob `opcoes.criar_setup` (prova de gate por RENDER, 5 formas de permissão)"
  - "`setupNovo` + `compilarSetup`/`confirmarSetup`/`desativarSetup` no hook, com `recarregarLeitura()` depois de gravar"
  - "as três rotas de escrita alcançáveis pelos DOIS stores"
  - "18 chaves de copy novas nas duas vozes, com a ressalva do backtest idêntica byte a byte"
  - "`test_opcoes_criar_setup_ui.mjs` — 97 asserções, provadas contra 5 defeitos injetados"
affects: [24-05, fase-4-veredito, fase-6-fluxo-do-iniciante]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Contador PRÓPRIO por recurso (`leituraRef`) quando uma recarga não é troca de ativo — bumpar o contador compartilhado invalidaria a chamada que pediu a recarga"
    - "Render de campo por VARREDURA das chaves que chegaram, nunca por lista local de nomes (ENG-06 aplicado ao front)"
    - "Ação de estado destrutiva em dois toques, com o rótulo do botão virando a própria confirmação"
    - "Peças que o guardião lê por ORDEM declaradas DEPOIS do componente (içamento de função), mesmo padrão do `ErroDoMcp` do 24-02"

key-files:
  created:
    - web/src/opcoes/CriarSetup.jsx
    - web/tests/test_opcoes_criar_setup_ui.mjs
  modified:
    - web/src/api.js
    - web/src/persistence.js
    - web/src/copy.js
    - web/src/opcoes/useOpcoesMcp.js
    - web/src/opcoes/OpcoesScreen.jsx

key-decisions:
  - "`recarregarLeitura()` NÃO incrementa `tickerRef`: se incrementasse, invalidaria a própria chamada de confirmar/desativar que a pediu, e a tela mostraria 'gravando…' para sempre"
  - "Um trio de estado só para as TRÊS ações de escrita: são a mesma conversa, e `status` (`dry_run`/`ativo`/`inativo`) diz qual delas respondeu"
  - "As condições do setup são renderizadas varrendo as chaves que CHEGARAM — traduzir `indicator`/`operator` criaria a segunda cópia do contrato que o ENG-06 proíbe"
  - "`ErroDaCriacao`, `Ensaio` e `BotaoDesativar` declarados DEPOIS do componente, para que o literal do botão de gravar não apareça no fonte antes do ramo `dry_run`"
  - "`onDesativar` saiu da assinatura de `CriarSetup` e virou o componente exportado `BotaoDesativar`: o botão vive no card do setup GRAVADO, e uma prop nunca usada seria contrato falso"
  - "Qualquer status de sucesso que não seja `dry_run`/`inativo` é tratado como gravação — cravar a string `\"ativo\"` faria a confirmação sumir em silêncio se o serviço mudar a palavra"

patterns-established:
  - "Prova de gate de permissão por RENDER (react-dom/server + stub do hook), com asserção de sanidade de que a tela renderizou — grep no fonte não distingue 'condição presente' de 'condição correta'"
  - "Guardião que varre a PASTA inteira (`readdirSync`) em vez de uma lista fixa de arquivos: componente novo entra na regra sozinho"

requirements-completed: ["PLANO Fase 5 — front"]

# Metrics
duration: 47min
completed: 2026-09-11
---

# Phase 24 Plano 04: Criar setup — o front da Fase 5 Summary

**A pessoa com a permissão escreve a condição em português, vê o que o serviço entendeu e quantas vezes aquilo já aconteceu no histórico — com a ressalva de que contagem passada não é expectativa fixada junto dos números — e só então grava; quem não tem a permissão não vê a seção, e a rota recusaria de qualquer forma.**

## Performance

- **Duration:** 47 min
- **Started:** 2026-09-11T21:05:00Z
- **Completed:** 2026-09-11T21:52:00Z
- **Tasks:** 3
- **Files modified:** 7 (5 modificados, 2 criados)

## Accomplishments

- `CriarSetup.jsx` (novo, 391 linhas): textarea rotulada → botão → cascata de sete estados de erro escolhida por `code` → ensaio → gravar. Nenhum fetch próprio; estado e ações chegam por prop.
- Gate de permissão **provado no RENDER**, não por grep: `react-dom/server` sobre `OpcoesScreen` com cinco formas de `authUser` (com a permissão, com outra permissão, com lista vazia, anônimo, sem o campo `permissions`). A seção e o botão de desativar aparecem no primeiro caso e em nenhum dos outros quatro, com asserção de sanidade de que a tela de fato renderizou.
- Treze estados de `CriarSetup` renderizados de verdade: o botão de **gravar existe só nos dois casos `dry_run`** e em nenhum dos outros onze.
- `<script>alert(1)</script>` dentro do `cru` da LLM sai `&lt;script&gt;` no HTML renderizado — T-24-17 verificado, não só afirmado.
- Três rotas de escrita nos DOIS stores, com `compilar` no `TIMEOUT_LLM` (é a única da aba que chama modelo) e as outras duas em 30 s.
- 18 chaves de copy nas duas vozes, com `opcoesBacktestRessalva` **idêntica byte a byte** entre elas.
- Guardião novo com 97 asserções, **provado contra 5 defeitos injetados** e revertido byte a byte.

## Task Commits

1. **Task 1: as três rotas nos dois stores, hook e copy** — `1d5cb38` (feat)
2. **Task 2: `CriarSetup.jsx` e a montagem gateada por permissão** — `1ae7605` (feat)
3. **Task 3: guardião estático da seção de criação** — `df22a6b` (test)

## Files Created/Modified

- `web/src/api.js` — `mcpSetupCompilar` (`TIMEOUT_LLM`), `mcpSetupConfirmar` e `mcpSetupDesativar` (30 s, `encodeURIComponent` no nome).
- `web/src/persistence.js` — os três nos DOIS stores, delegação pura, fora de `sync.mutate`/outbox.
- `web/src/opcoes/useOpcoesMcp.js` — `leituraRef`, `recarregarLeitura()`, trio `setupNovo` e as três ações.
- `web/src/opcoes/CriarSetup.jsx` — componente novo + `BotaoDesativar` exportado.
- `web/src/opcoes/OpcoesScreen.jsx` — `podeCriarSetup`, a seção abaixo de "SETUPS GRAVADOS" e o botão de desativar em cada card.
- `web/src/copy.js` — 18 chaves nos dois blocos.
- `web/tests/test_opcoes_criar_setup_ui.mjs` — guardião novo.

## Verificação

Suíte canônica inteira, FORA do sandbox (`bash scripts/executar.sh --testes`):

```
2407 passed, 5 skipped, 597 warnings in 74.21s (0:01:14)
129 arquivos web/tests/*.mjs [OK], 0 falhas
exit=0
```

Baseline antes deste plano: **2407 passed, 5 skipped** + 128 `.mjs`. Delta: **0 no pytest** (o plano não toca `server/`) e **+1 arquivo `.mjs`** (o guardião novo). Zero regressão, zero skip novo.

`cd web && npx vite build` → verde, rodado depois de CADA task (grep não pega erro de sintaxe JSX).

`git diff --stat web/package.json package-lock.json` → **vazio**. Nenhuma dependência nova (T-24-SC).

**Render de verdade, além do estático.** Harness temporário (esbuild + `react-dom/server`, tudo em `$TMPDIR`, nada gravado no repo):

| O que foi renderizado | Resultado |
|---|---|
| `CriarSetup` em 13 estados (vazio, carregando, os 7 erros, dry-run com e sem backtest, gravado, desativado) | botão de GRAVAR presente **só** nos 2 `dry_run` |
| `cru` com `<script>alert(1)</script>` | sai `&lt;script&gt;` — escapado pelo React (T-24-17) |
| `dado_atrasado` com `motivo: "atrasado"` e idade 31,4 h | "…está atrasado (31 h): um setup criado agora vigiaria um pregão que já passou." |
| `dado_atrasado` com `motivo: "nao_medido"` | "Não foi possível medir a idade do dado…" — jamais silêncio |
| `retorno_apos_disparo` com `d+10` de valores `null` | travessão nos dois números, `com_dado` preservado |
| `OpcoesScreen` com 5 formas de `authUser` | seção + botão de desativar presentes **só** com `opcoes.criar_setup` |

**Prova de que o guardião não passa por vacuidade** (critério de aceite da Task 3), cinco defeitos injetados e revertidos:

| Defeito injetado | Resultado |
|---|---|
| `{podeCriarSetup ? (` → `{true ? (` na montagem | `FALHOU a montagem de <CriarSetup é condicionada a podeCriarSetup` |
| `problems.map` → `[problems.join(", ")].map` | 2 FALHAS (item a item **e** o anti-`join`) |
| `<pre>{cru}</pre>` → `dangerouslySetInnerHTML` | `FALHOU CriarSetup.jsx não injeta HTML cru` |
| `const ROTULOS = { crosses_above: …, bullish_engulfing: … }` | `FALHOU CriarSetup.jsx sem vocabulário da DSL hardcodado` |
| remoção do `if (!confirmando) { … return; }` | `FALHOU o primeiro toque NÃO age — só arma a confirmação` |

Revertido com `git checkout --` nos arquivos específicos; `diff` contra a cópia pré-injeção confirma byte a byte, e `git status` ficou limpo (fora os 4 diretórios não rastreados de `.claude/skills/`, que não entraram em commit nenhum).

## Decisions Made

- **`recarregarLeitura()` com contador próprio (`leituraRef`), sem tocar `tickerRef`.** A recarga depois de gravar/desativar não é troca de ativo. Se ela incrementasse `tickerRef`, a checagem `tickerRef.current === meuTicker` na volta de `confirmarSetup` falharia — a própria ação que pediu a recarga teria o resultado descartado, e a seção ficaria em "carregando" para sempre. Com dois contadores, `tickerRef` responde "de qual ativo é esta resposta?" e `leituraRef` responde "qual das leituras daquele ativo é a mais recente?".
- **O corpo da leitura é duplicado entre o efeito e `recarregarLeitura`, de propósito.** Extrair o `store.mcpLeitura` do efeito quebraria a asserção de sanidade do guardião do 24-02 (`efeitos.some(corpo => corpo.includes("store.mcpLeitura"))`), que existe para provar que a leitura inicial nasce no efeito; e chamar `recarregarLeitura()` de dentro do efeito criaria uma dependência que o faria reexecutar. Sete linhas duplicadas, com a razão escrita em cima.
- **Um trio de estado para as TRÊS ações.** Compilar, confirmar e desativar são a mesma conversa com o serviço: a resposta de uma substitui a da anterior na tela, e `status` diz qual respondeu. Três trios separados exigiriam três cascatas de erro idênticas e três lugares onde esquecer de tratar o 409.
- **Condições renderizadas por varredura das chaves que chegaram.** `Object.entries(cond)` com o nome do campo como veio. Traduzir `indicator`/`operator`/`pattern` para português exigiria um dicionário local dos nomes do serviço — exatamente a segunda cópia do contrato que o ENG-06 proíbe, e a que ninguém lembraria de atualizar quando o serviço publicasse um indicador novo. O guardião tranca isso com quatro nomes de DSL banidos da pasta inteira.
- **`ErroDaCriacao`, `Ensaio` e `BotaoDesativar` declarados DEPOIS do componente.** Mesmo motivo (e mesmo precedente) do `ErroDoMcp` do 24-02: o critério de aceite mede a ORDEM das primeiras ocorrências no fonte para provar que o botão de gravar só existe no ramo do ensaio. Com `Ensaio` acima, o literal do botão apareceria antes do `"dry_run"` sem nada ter mudado na tela. Declaração de função é içada — a ordem física não muda a execução.
- **Status desconhecido é tratado como gravação, não como erro.** A cascata testa `dry_run` e `inativo` explicitamente; qualquer outro sucesso cai no ramo "gravado", lendo o nome da RESPOSTA. Cravar `=== "ativo"` faria a confirmação sumir em silêncio se o serviço passasse a dizer outra palavra — e sumir em silêncio depois de gravar é o defeito que leva a pessoa a gravar de novo.
- **A seção vive no ramo de DADOS da tela, não acima dele.** Sem ticker escolhido não há o que criar (a rota exige o ativo), e sem leitura a pessoa não tem como saber o que está pedindo. O estado vazio de cima já diz o porquê, e criar um caminho alternativo ali duplicaria a cascata de estados.
- **Mínimo de 15 caracteres para habilitar o botão.** Cada compilação gasta uma chamada de LLM paga (chave do servidor, no caminho gerenciado) mais duas do cap. "oi" não é uma condição, e deixá-la virar uma chamada é cobrar da pessoa por nada (T-24-19).

## Deviations from Plan

### Ajustes de execução

**1. [Rule 3 — a assinatura do plano criaria prop morta] `onDesativar` saiu de `CriarSetup` e virou `BotaoDesativar`**
- **Found during:** Task 2
- **Issue:** o plano fixa `CriarSetup({ ctx, ticker, estado, onCompilar, onConfirmar, onDesativar, cp })`, mas o MESMO plano coloca o botão de desativar nos cards de setup GRAVADO, dentro de `OpcoesScreen`. `onDesativar` (e `ctx`) nunca seriam lidos dentro de `CriarSetup` — uma prop na assinatura que ninguém usa é contrato falso, e o próximo leitor passaria a ação por ali esperando que funcionasse.
- **Fix:** `CriarSetup({ ticker, estado, onCompilar, onConfirmar, cp })` + `export function BotaoDesativar({ nome, onDesativar, cp, ocupado })` no mesmo arquivo, consumido por `OpcoesScreen`. As duas ações de escrita nascem e mudam juntas, então moram juntas.
- **Committed in:** `1ae7605`

**2. [Rule 3 — o ticker não pode vir de dois lugares] `compilarSetup({ descricao })`, sem `ticker` no argumento**
- **Found during:** Task 1
- **Issue:** o plano escreve `compilarSetup({descricao, ticker})`. O hook já conhece o ticker (`alvoAtual`, o do cabeçalho) e o precedente da F3 (`montarProposta`) o fixa na chamada exatamente para que a tela nunca peça sobre um ativo diferente do exibido. Aceitar um `ticker` do chamador criaria a segunda fonte — e o setup é gravado num armazém compartilhado, onde o ativo errado fica.
- **Fix:** a ação recebe só a descrição; o corpo sai como `{descricao, ticker: alvoAtual}`. Travado por asserção no guardião.
- **Committed in:** `1d5cb38`

**3. [Rule 2 — textos que o plano descreve mas não nomeia] 3 chaves de copy além das 15 listadas**
- **Found during:** Task 1
- **Issue:** a lista de chaves do plano não tem texto para (a) a mensagem de sucesso depois de gravar — que o passo 5 da Task 2 descreve —, (b) a confirmação da desativação em dois toques — que a Task 2 descreve — nem (c) a mensagem de desativado. Guardrail do repo: todo texto sai de `cp.*`, nas duas vozes.
- **Fix:** `opcoesCriarGravado(nome)`, `opcoesCriarDesativado(nome)` e `opcoesCriarConfirmarDesativacao`. Total: 18 chaves novas, conjunto idêntico nos dois modos.
- **Committed in:** `1d5cb38`

**4. [ajuste] `forma_invalida` mostra o `faltando` E o `cru`, quando o serviço manda os dois**
- O plano pedia só `cp.opcoesCriarFaltando(faltando)`. Mas o backend inclui `cru` nesse 422 (`options_mcp_api.py`, ramo `faltando` do `/compilar`), e a lista de campos sozinha não deixa a pessoa ver o que a IA de fato respondeu. O `cru` vai no mesmo `<pre>` escapado do outro ramo.

**5. [ajuste] `d+5`/`d+10` iterados, não cravados**
- O plano nomeia os dois passos. O componente itera `Object.entries(retorno_apos_disparo)` e usa a chave como rótulo: mesma razão do ENG-06 — se o serviço publicar `d+20`, a tela o mostra em vez de engoli-lo, e se publicar só `d+5`, não aparece uma linha `d+10` vazia que ninguém mediu.

**6. [ajuste] o guardião varre a PASTA, não uma lista de arquivos**
- Os guardiões da F2/F3 listam os arquivos à mão. Para as regras de vocabulário (DSL, HTML cru, expectativa de retorno), a lista fixa é um buraco: o componente novo da próxima fase nasce fora da varredura em silêncio. O guardião novo usa `readdirSync` sobre `web/src/opcoes/`.

### Divergências de contagem nos critérios de aceite (não são defeito)

**7. `grep -c "mcpSetupCompilar" web/src/persistence.js` dá 3, não 2.** Mesma causa documentada no 24-02 (divergência 6): `grep -c` conta LINHAS, e no `deviceStore` o método ocupa duas (`async mcpSetupCompilar(body) {` + `return api.mcpSetupCompilar(body);`). Fatiando o arquivo nos dois stores: **2 ocorrências em cada um**, para os três métodos. O guardião novo trava isso por store, não por contagem global.

**8. `grep -rn "dangerouslySetInnerHTML" web/src/opcoes/` retorna 1 linha — um COMENTÁRIO.** O critério pede "nenhum `dangerouslySetInnerHTML` em `web/src/opcoes/`", e o que ele protege (nenhum USO) está cumprido: o comentário está no bloco que explica por que o `cru` sai em nó de texto. Apagar a explicação para satisfazer um grep literal tiraria justamente a nota que impede o próximo leitor de "otimizar" o `<pre>`. O guardião novo aplica a regra sobre o fonte SEM comentários, que é o padrão que o 24-02 já estabeleceu ("eles citam os mesmos termos ao EXPLICAR as decisões, e contá-los faria o guardião se auto-invalidar") — e ele varre a pasta inteira, não só o arquivo novo.

**9. "O botão de confirmar só existe depois de `dry_run` (índice no fonte)" exigiu reordenar o arquivo, e a busca ingênua mede o botão errado.** `opcoesCriarConfirmarDesativacao` CONTÉM `opcoesCriarConfirmar` como substring: um `indexOf` cru acha o botão de DESATIVAR e responde sobre ele. O guardião usa `/opcoesCriarConfirmar(?!Desativacao)/`, com asserção de sanidade provando que a busca ignora o sufixo. Além disso, as três funções auxiliares foram movidas para depois do componente (ver Decisions) — sem isso o critério reprovaria um arquivo correto.

**10. Guardião com 97 `ok`, o plano pedia ≥ 9.** Os 9 itens listados estão todos cobertos; o resto são as asserções de sanidade obrigatórias, a checagem por arquivo (5 arquivos × 3 regras de vocabulário) e as 18 chaves × 2 modos.

**11. `grep -c 'minHeight: "44px"'` em `CriarSetup.jsx` dá 1, não um por botão.** Mesma divergência 8 do 24-02: os três botões do arquivo herdam de `BOTAO`, que carrega o alvo de toque. O guardião checa a constante — assim o alvo de toque não depende de ninguém lembrar de digitá-lo.

---

**Total deviations:** 6 ajustes + 5 divergências de contagem. Nenhuma mudança arquitetural; nenhuma dependência nova.
**Impact on plan:** nenhum item do plano deixou de ser entregue.

## Issues Encountered

- **O render estático não clica.** `renderToStaticMarkup` não roda efeito nenhum, então a tela parava em "Escolha um ativo" e o gate de permissão nunca chegava a ser exercido. Resolvido no harness (fora do repo) com um plugin de esbuild que troca o estado inicial do seletor e substitui `useOpcoesMcp` por um stub já carregado — com uma asserção de sanidade ("a tela renderizou LEITURA DO ATIVO e SETUPS GRAVADOS") que teria pegado exatamente esse falso verde. Foi ela que pegou.
- **Substring de chave de copy engana `indexOf`.** `opcoesCriarConfirmarDesativacao` contém `opcoesCriarConfirmar`. O primeiro assert de ordem passou a falhar por medir o botão errado, não por defeito no código. Vale como lembrete: chave nova que é prefixo de outra precisa de busca com fronteira.
- **`grep -c` conta linhas, não ocorrências** — terceira vez nesta fase que um critério de aceite tropeça nisso.

## Known Stubs

Nenhum. Toda a seção lê dado real das três rotas do 24-03; nenhum componente recebe mock ou valor fixo. Os únicos literais de texto fora de `cp.*` são rótulos curtos de linha ("Nome", "Ativo", "logic", "consecutive_days", "Período", "Pregões avaliáveis", "Pregões sem indicador") e dois estados de ausência do serviço ("O serviço devolveu este setup sem condição listada…", "O serviço não devolveu ensaio no histórico…"), no mesmo padrão que a F2/F3 já usavam. `logic` e `consecutive_days` aparecem com o nome do serviço de propósito — são o vocabulário dele, e é o mesmo motivo pelo qual as condições não são traduzidas.

## Pendências de verificação (declaradas)

- **Nada foi exercitado AO VIVO** (D-24.7): `MCP_CLIENT_SECRET` fora do ambiente e nenhuma chamada de LLM real feita. Em particular, segue sem prova: (a) que um modelo real devolva, a partir do `system` montado em runtime, um JSON que `create_setup` aceite; (b) a forma real do `backtest` (o componente foi verificado contra a forma do contrato, não contra uma resposta do serviço); (c) o `idadeHoras` do 409.
- **Nenhum teste em aparelho.** A `<textarea>` no WKWebView, o alvo de toque dos botões novos em 375 px e a leitura do bloco de backtest no tema claro só se verificam no iPhone — e este plano não publica nada (o 24-05 é quem faz bump + `publicar-web.sh`, só com o OK do Alex).
- **O fluxo completo (compilar → confirmar → o setup aparecer na lista) nunca rodou ponta a ponta.** As peças estão provadas isoladamente (render dos 13 estados, `recarregarLeitura` chamada nos dois sucessos), mas a sequência inteira depende do serviço responder.

## Threat Flags

Nenhuma superfície nova fora do `<threat_model>` do plano.

- **T-24-16 (elevação de privilégio):** render condicionado, **provado por render** em 5 formas de permissão + o 403 do backend (24-03). O guardião falha se a condição sair da montagem ou do botão de desativar.
- **T-24-17 (`cru` da LLM na tela):** nó de texto com `pre-wrap`; `<script>` renderizado sai escapado no HTML. `dangerouslySetInnerHTML` banido da pasta inteira, com o defeito injetado e pego.
- **T-24-18 (backtest lido como promessa):** ressalva fixa no mesmo bloco dos números (travado por fatia do fonte), sem verde/vermelho nesses números (travado), e as três frases de expectativa banidas da pasta e das chaves novas — a única ocorrência permitida é a da própria ressalva, que as nega.
- **T-24-19 (textarea disparando LLM):** mínimo de 15 caracteres + botão desabilitado + o gate de análise do backend.
- **T-24-SC:** nenhum pacote instalado; `web/package.json` e `package-lock.json` intocados.

## Next Phase Readiness

A Fase 5 do `docs/PLANO-aba-opcoes.md` está completa nos dois lados (backend no 24-03, front aqui). O que falta é só publicação: **o 24-05 é o último plano da fase e NÃO roda sozinho** — ele faz bump de `version.js` + `publicar-web.sh` + o deploy do backend, e depende do OK explícito do Alex (ele toca `server/web_dist`, que é o que o Railway serve, e arrasta junto tudo o que estiver parado em `v2/interacao-estrutural`).

Nada deste plano foi empurrado para `origin`; nenhum PR foi aberto.

---
*Phase: 24-opcoes-mcp-analise-e-setups*
*Completed: 2026-09-11*

## Self-Check: PASSED

Os arquivos afirmados existem (`web/src/opcoes/CriarSetup.jsx`, `web/tests/test_opcoes_criar_setup_ui.mjs`, este SUMMARY) e os três commits estão no histórico (`1d5cb38`, `1ae7605`, `df22a6b`). Suíte canônica em 2407 passed / 5 skipped + 129 `.mjs` [OK], exit 0.

## Nota de processo — STATE.md e REQUIREMENTS.md

- `gsd-sdk query state.record-metric --phase 24 --plan 04 …` gravou a linha de métrica **fora** da tabela (depois do `*Updated after each plan completion*`) e com rótulo divergente (`Phase 24 P04` em vez de `24 P04`). Recolocada à mão na tabela, no formato das irmãs. `state.add-decision` e `roadmap.update-plan-progress` funcionaram (o `ERROR: failed to copy trust settings of system certificate` na saída é ruído do sandbox, não falha do comando — as quatro decisões e o `4/5` do ROADMAP entraram).
- `state.advance-plan` e `state.record-session` **não foram chamados** (corrompem `stopped_at`/contador, conforme registrado nas fases anteriores). Posição, `stopped_at`, `last_activity`, `percent` e a Session Continuity foram escritos à mão e conferidos: **Plan 5 of 5**, com o 24-05 marcado como pendente de OK humano.
- `requirements.mark-complete` **não foi chamado**: o `requirements:` do plano é `PLANO Fase 5 — front`, um ponteiro para `docs/PLANO-aba-opcoes.md`, não um ID de `REQUIREMENTS.md` (que não tem entrada para a Fase 24). Rodá-lo com esse texto só sujaria o arquivo. Mesmo tratamento do 24-03.
