---
phase: 27-aba-opcoes-sobre-a-carteira
plan: 02
subsystem: web
tags: [react, jsx, copy-por-modo, adr-027, guardioes, acessibilidade]

requires:
  - phase: 27-01
    provides: "`mcpVigias` (custo 0) e `mcpSetupsListar` (custo 2) nos dois stores; contrato `name` (nome da pessoa) × `nomeNoServico` (chave do armazém)"
  - phase: 26-b3-opcoes
    provides: "aba Opções no front (`OpcoesScreen.jsx`), `useOpcoesMcp.js`"
provides:
  - "universo da aba = `ctx.data.positions` (a carteira), não mais a watchlist"
  - "bloco 'Seus vigias' no topo da aba, fora de qualquer ticker e de custo ZERO"
  - "botão de atualizar o estado dos vigias com o custo (2) declarado DENTRO do controle"
  - "lastro livre no cartão do ativo, antes da tentativa, via `qtyLivre` (fonte única)"
  - "estado vazio da carteira com caminho — `ctx.goCarteira`"
  - "`EFEITO_PERMITIDO`: allowlist nomeada de chamadas que podem sair por `useEffect`"
  - "fiação correta de `nomeNoServico` nas duas ações que viajam ao serviço"
affects: [27-04, 27-05, aba-opcoes, front-opcoes]

tech-stack:
  added: []
  patterns:
    - "ref transversal ao ticker (`vigiasRef`) para trio sob demanda que NÃO é afirmação sobre um ativo"
    - "custo declarado DENTRO do controle (segunda linha do próprio botão), não ao lado dele"
    - "guardião por ALLOWLIST NOMEADA em vez de contagem: a contagem falha sobre mudança correta e passa calada sobre a errada"
    - "item de allowlist marcado TRANSITÓRIO por escrito, com o plano que o remove"

key-files:
  created:
    - web/tests/test_opcoes_universo_carteira.mjs
    - web/tests/test_opcoes_vigias_ui.mjs
  modified:
    - web/src/opcoes/OpcoesScreen.jsx
    - web/src/opcoes/useOpcoesMcp.js
    - web/src/opcoes/CriarSetup.jsx
    - web/src/copy.js
    - web/src/App.jsx
    - web/tests/test_opcoes_analisar_ui.mjs
    - web/tests/test_opcoes_mcp_aba_ui.mjs
    - web/tests/test_opcoes_criar_setup_ui.mjs

key-decisions:
  - "O ticker CONTINUA nascendo `\"\"`. A aba não abre vazia por causa da LISTA das posições e do bloco de vigias (custo zero), e não por causa de um ativo auto-selecionado — que custaria 3 chamadas de quem só abriu a tela"
  - "A ORDENAÇÃO dos vigias é delegada às duas fontes já ordenadas (o backend do 27-01 e o índice), em vez de reimplementada em JS: uma segunda régua divergiria da primeira em silêncio"
  - "`opcoesCustoChamadas` ficou genérica e a composição dos vencimentos ganhou chave própria — reusada como estava, ela daria o número certo com a explicação errada no botão dos vigias"
  - "A contagem `efeitos.length === 2` virou a allowlist `EFEITO_PERMITIDO`, disjunta de `METODOS`, com `mcpLeitura` marcado TRANSITÓRIO (sai no 27-05)"
  - "`BotaoDesativar` passou a receber DOIS nomes: o que viaja (`nome` = chave do armazém) e o que é lido em voz alta (`nomeVisivel` = nome da pessoa)"

patterns-established:
  - "Guardião de ordem ancorado no ponto de render (`{cabecalho}`), não no byte 0: uma segunda cascata na mesma tela quebra o `indexOf` global"
  - "Guardião novo só entra depois da injeção de defeito ser de fato exercitada e revertida"

requirements-completed: [SC-1, SC-2, SC-5, D2, D3, D4, G1, G2, A1, A2]

duration: ~1h
completed: 2026-09-13
---

# Phase 27 Plan 02: A aba Opções sobre a carteira Summary

**O universo da aba deixou de ser a watchlist e passou a ser `ctx.data.positions`; os vigias gravados passaram a existir no topo da tela, fora de qualquer ticker e de graça; e o lastro livre saiu da mensagem de recusa e foi para o cartão — sem que nada de custo passasse a disparar por efeito.**

## Performance

- **Duração:** ~1h (09:00 → 10:01 BRT)
- **Tasks:** 3 de 4 (a quarta é o `checkpoint:human-verify`, que está ABERTO)
- **Arquivos:** 10 (2 criados, 8 modificados)
- **Commits de produção:** 5
- **Suíte canônica:** `2773 passed, 5 skipped, 3 xfailed, 0 failed` + `141/141 .mjs`, exit 0, fora do sandbox
- **Baseline de entrada (após 27-01):** `2729 passed` + `138/138` — o delta inclui o 27-03, que rodou em paralelo e commitou antes (`8a25d5f`…`29c2d2d`). Minha parte: **+3 `.mjs`** (`test_opcoes_universo_carteira`, `test_opcoes_vigias_ui`, e o `test_opcoes_tecnico_stores` é do 27-03). **Zero regressão.**
- **`npx vite build`:** verde a cada task

## Accomplishments

### O universo virou a carteira (D3), e o ticker continua nascendo vazio

`OpcoesScreen` deriva de `ctx.data.positions`; `ctx.data.watchlist` não aparece mais no arquivo. Sem chamada nova — é a mesma fonte que o `App.jsx` já usa para marcar "em carteira".

A parte que exigiu disciplina foi **não** fazer o óbvio. A versão anterior do plano mandava auto-selecionar o primeiro ativo, e o 27-CONTEXT descreve o sintoma ("sair da aba e voltar = nenhum setup à vista") de um jeito que convida a isso. Selecionar um ativo dispara `mcpLeitura` pelo efeito de troca de ticker, e essa chamada custa **3** — auto-selecionar cobraria 3 consultas de quem só abriu a aba. O `useState("")` ficou, agora com o comentário que explica por que mexer nele é o defeito, não a correção; e há um guardião que reprova tanto o inicializador quanto um `setTicker` dentro de efeito.

### O bloco "Seus vigias" (a correção de verdade)

Duas fontes, dois custos, e a diferença é deliberada: o índice local (`mcpVigias`, custo **zero**, sai no mount) traz o cadastro; o estado do dia (`mcpSetupsListar`, custo **2**) só sai de clique. O botão declara o custo **dentro do próprio controle**, numa segunda linha — não ao lado, não abaixo.

Três coisas que só se decidem lendo o código:

1. **`vigiasRef`.** `useChamadaSobDemanda(tickerRef)` descarta a resposta quando o ticker mudou entre o pedido e a volta — disciplina certa para cadeia e proposta, que são afirmações *sobre um ativo*. A lista de vigias não é. Com `tickerRef`, clicar num cartão (que troca o ticker) apagaria a lista que a pessoa acabou de pagar 2 chamadas para ver. Um ref que nunca muda mantém o contador próprio (contra disparo repetido) e desliga só a conferência de ticker.
2. **Recarga do índice depois de gravar/desativar.** Sem ela, o vigia recém-criado só apareceria no topo depois de um reload — que é literalmente o defeito da fase.
3. **`irParaVigia` não é `escolherTicker`.** O chip precisa ser toggle (desselecionar); o cartão precisa navegar. Reusar o toggle cru faria clicar no vigia do ativo já aberto **fechar** o ativo.

### Lastro livre no cartão

`qtyLivre` importado de `finance.js` (módulo puro — o isolamento do ADR-027 continua intacto), `ACOES_POR_CONTRATO = 100` como constante nomeada espelhando `store.py`, e ausência com motivo: posição sem `qty` legível mostra travessão e o porquê, nunca `0` — "você não tem lastro" é afirmação diferente de "não sei quanto você tem".

### Os três guardiões atualizados, com nota datada

Nenhum foi apagado.

- **`test_opcoes_analisar_ui.mjs`** — a contagem `efeitos.length === 2` virou a regra que sempre importou: `EFEITO_PERMITIDO`, allowlist nomeada, disjunta de `METODOS` (que ganhou `mcpSetupsListar`). Cada entrada carrega o porquê, e `mcpLeitura` está marcada **TRANSITÓRIA** com todas as letras — ela custa 3, continua no efeito de troca de ticker e sai da allowlist no 27-05. Contagem falha sobre mudança correta e passa calada sobre a errada que não mexa no número; allowlist falha exatamente onde dói.
- **`test_opcoes_mcp_aba_ui.mjs`** — as buscas de ordem passaram a ancorar em `{cabecalho}`. A aba ganhou uma segunda cascata de estados (o bloco de vigias, montado antes do `return`) que reusa `cp.opcoesCarregando`, e `indexOf` a partir do byte 0 passou a achar o carregando do bloco errado. A asserção da seção 5 foi reancorada em `{carregando ? (` para não virar tautologia.
- **`test_opcoes_criar_setup_ui.mjs`** — a asserção de `aria-label` passou a exigir o nome **legível**.

## Task Commits

| # | Task | Commit |
|---|------|--------|
| 1 | Universo = carteira + estado vazio com caminho | `4115ec9` (feat) |
| 2 | Bloco "Seus vigias" | `140f9e8` (feat) |
| 3 | Lastro livre no cartão | `f3668d3` (feat) |
| — | Desvio 1: `nomeNoServico` nas ações | `cd8fe7c` (fix) |
| — | Desvio 2: `<span>` dentro do `<button>` | `466f2a9` (fix) |

## Injeções de defeito — de fato exercitadas

Toda não-vacuidade exigida foi injetada, o guardião reprovou, e o defeito foi revertido antes do commit. Nenhuma foi presumida.

| # | Injeção | Guardião que reprovou | Resultado medido |
|---|---------|----------------------|------------------|
| A | `useState("")` do ticker → `useState(carteira[0] && carteira[0].t)` | `test_opcoes_universo_carteira.mjs` | "o ticker nasce vazio" vermelho |
| B | universo de volta para `ctx.data.watchlist` | `test_opcoes_universo_carteira.mjs` | 3 asserções vermelhas |
| C | `store.mcpCadeia()` dentro do `useEffect` do índice | `test_opcoes_analisar_ui.mjs` | 2 vermelhas: fora da allowlist **e** método de `METODOS` em efeito |
| D | `store.mcpSetupsListar()` movida para o `useEffect` do mount | `test_opcoes_vigias_ui.mjs` | 2 vermelhas: "custo 2 só em clique" e "porta única" |
| E | `qtyLivre(pos)` → `pos.qty - (pos.qtyTravada \|\| 0)` | `test_opcoes_universo_carteira.mjs` | 2 vermelhas: subtração reimplementada + import virou fachada |
| F | `abrirGrafico(chave)` → `abrirGrafico(s.name)` | `test_opcoes_vigias_ui.mjs` | "o gráfico é aberto pela chave do ARMAZÉM" vermelho |

## Deviations from Plan

### Auto-fixed

**1. [Rule 2 - Missing critical] As ações do setup mandavam ao serviço o nome SEM prefixo**
- **Encontrado em:** Task 3 (sinalizado pelo Alex na abertura da sessão).
- **Problema:** o 27-01 mudou `/leitura` para devolver `name` (nome da pessoa) **e** `nomeNoServico` (chave do armazém, com o prefixo de 8 hexadecimais da conta). A lista de setups do ticker continuava passando `s.name` para `abrirGrafico` e para `BotaoDesativar`. Com o backend novo, isso manda um nome sem prefixo ao serviço: **422 `setup_desconhecido` nos dois botões, em produção**. Nenhum teste de render pegaria — a tela fica idêntica até alguém clicar.
- **Correção:** `const chave = s.nomeNoServico || s.name`, uma só, usada em `abrirGrafico`, em `grafico.setup ===`, na `key` e no `nome` do `BotaoDesativar`. O que a pessoa lê continua `s.name`.
- **Verificação:** seção 4b nova em `test_opcoes_vigias_ui.mjs`; injeção F.
- **Commit:** `cd8fe7c`.

**2. [Rule 1 - Bug] A correção acima teria vazado o hash para o leitor de tela**
- **Encontrado em:** durante o desvio 1.
- **Problema:** `BotaoDesativar` usa o mesmo `nome` no `onDesativar` **e** no `aria-label`. Passar a chave do armazém faria o leitor de tela anunciar "Desativar este setup a1b2c3d4-IFR baixo" — o mesmo dano que a injeção nº 4 do 27-01 mediu, agora no canal de acessibilidade. Regressão introduzida por mim, não pré-existente.
- **Correção:** `BotaoDesativar` recebe `nomeVisivel` (cai em `nome` quando ausente). O que VIAJA é a chave; o que é LIDO EM VOZ ALTA é o nome da pessoa.
- **Arquivo fora do `files_modified`:** `web/src/opcoes/CriarSetup.jsx` e `web/tests/test_opcoes_criar_setup_ui.mjs`. Nenhum dos dois pertence ao 27-03 (backend + `api.js`/`persistence.js`), então não houve risco de escrita concorrente. A alternativa era entregar a regressão de acessibilidade.
- **Commit:** `cd8fe7c`.

**3. [Rule 1 - Bug] `opcoesCustoChamadas` daria o número certo com a explicação errada**
- **Encontrado em:** Task 2.
- **Problema:** o plano manda reusar `cp.opcoesCustoChamadas(2)` no botão dos vigias — correto, uma forma só de dizer custo. Mas o texto terminava em "*uma para listar os vencimentos e duas para cada vencimento consultado*", que é a composição da chamada de **possibilidades**. No botão dos vigias (`list_setups` + `evaluate_setups`) isso é falso.
- **Correção:** a frase de custo ficou genérica e a composição ganhou chave própria (`opcoesCustoVencimentos`), renderizada na seção que já explicava o `2×N+1`.
- **Verificação:** asserções novas em `test_opcoes_vigias_ui.mjs` travam que a frase de custo **não** menciona vencimento e que a composição existe em chave própria.
- **Commit:** `140f9e8`.

**4. [Rule 1 - Bug] `<div>` dentro de `<button>` no cartão do vigia**
- **Encontrado em:** revisão final.
- **Problema:** `<button>` aceita conteúdo de frase; `<div>` é conteúdo de fluxo. Navegadores toleram, mas o cartão é botão de verdade e HTML inválido dentro dele é o tipo de coisa que quebra num WKWebView atualizado, calado.
- **Correção:** `<span>` com `display: block`/`flex`. Mesma aparência.
- **Commit:** `466f2a9`.

**5. [Rule 3 - Blocking] `web/dist` restaurado ao build publicado, a cada build**
- Mesmo achado do 27-01 (desvio nº 3): `npx vite build` regenera `web/dist` com hashes novos **sem** bump, e `test_ios_assets.mjs` compara `dist/assets` com `web/ios/.../public/assets` quando os dois têm o mesmo carimbo. Cada build foi rodado (é o que o plano exige) e `web/dist` foi restaurado de `server/web_dist` em seguida. `web/dist` é gitignorada. Nada commitado.

### Divergências entre o plano e a fonte, corrigidas por leitura

**6. O `<interfaces>` do plano descreve `mcpSetupsListar` devolvendo `{ setups: [...] }`. O backend devolve `{ vigias: [...] }`.**
`options_mcp_api.py:1934` retorna a chave `vigias` nas DUAS rotas — o que é melhor, porque a tela lê a mesma chave nas duas fontes. Implementado contra a fonte, não contra o plano. Se eu tivesse confiado no `<interfaces>`, o bloco renderizaria vazio para sempre, em silêncio, sem quebrar teste nenhum.

**7. Ordenação: delegada, não reimplementada.**
O plano descreve a régua ("armado → streak → criadoEm → nome") e manda comentá-la como decisão do executor. Implementei a decisão de **não reimplementá-la em JavaScript**: o backend do 27-01 já ordena a listagem por `_ordem_dos_vigias` e o índice já chega mais-recente-primeiro. A tela só ESCOLHE a fonte. O próprio plano diz "a tela não reordena o que o servidor já ordenou"; uma segunda régua divergiria da primeira na correção seguinte, em silêncio, com as duas listas parecendo iguais na tela. Registrado em comentário no fonte.

**8. Chave a mais: `opcoesLastroSemDado`.**
O plano lista três chaves de lastro e exige, no mesmo parágrafo, que ausência de `qty` mostre "travessão e o porquê". O porquê precisa de um texto. Quarta chave, nos dois blocos.

---

**Total:** 4 auto-fixes (3 bugs, 1 faltante crítico), 1 higiene de ambiente, 3 divergências plano↔fonte resolvidas pela fonte.
**Impacto:** os desvios 1 e 2 seriam defeitos em produção — o primeiro derrubaria os dois botões do cartão de setup, e ele não estava previsto em plano nenhum.

## Consequência transitória, declarada (item d da Task 2)

Enquanto `mcpLeitura` continuar saindo do efeito de troca de ticker, **clicar num cartão de vigia troca o ativo e, com isso, gasta 3 chamadas sem que o controle diga**. É defeito, é conhecido, está escrito na allowlist do guardião com a palavra "TRANSITÓRIO", e quem fecha é o **27-05** (a leitura do serviço vira botão com custo declarado). O roteiro do checkpoint abaixo avisa o desenvolvedor no passo 5, para ninguém descobrir sozinho o contador subindo 3.

## Achados que exigem decisão (não implementados — fora do `files_modified`)

**1. `/setups/{name}/desativar` devolve o nome do ARMAZÉM em `name`.**
`options_mcp_api.py:3270` retorna `"name": alvo`, onde `alvo` é o nome prefixado. `CriarSetup.jsx:173` mostra isso ao usuário via `opcoesCriarDesativado(dados.name)` — a pessoa lê "Setup `a1b2c3d4-IFR baixo` desativado". A rota irmã `/setups/confirmar` já faz o certo (`name` = nome da pessoa, `nomeNoServico` = chave). A correção pertence ao **backend**: desprefixar no front recriaria a regra do prefixo em JavaScript, que o 27-01 proíbe explicitamente. `options_mcp_api.py` não está no `files_modified` de nenhum plano desta onda — decisão do Alex sobre onde encaixar (27-04 ou um quick).

**2. `/setups/{name}/grafico` segue sem gate de dono** (achado nº 2 do 27-01, ainda aberto). Nada neste plano mudou isso; o 27-02 é só front.

## Issues Encountered

- **Nenhuma.** O 27-03 rodou em paralelo no mesmo repositório e commitou antes; os `files_modified` eram disjuntos e não houve colisão. A suíte final cobre os dois planos juntos, exit 0.

## User Setup Required

Nenhum. Nenhuma variável de ambiente nova, nenhum pacote novo (`T-27-SC`: zero `npm install`/`pip install` nesta fase).

## Checkpoint final — ABERTO (bloqueante)

O plano termina num `checkpoint:human-verify` com `gate="blocking"`, e ele **não pode ser automatizado**: os guardiões travam estrutura e copy, mas nenhum deles vê a tela. Layout em 375 px, ordem visual real, alvo de toque, contraste e — principalmente — **o contador de cota ao abrir a aba** só aparecem no aparelho. `ui_safety_gate` está ligado nesta fase.

Roteiro entregue ao desenvolvedor na resposta ao orquestrador. Resposta do Alex: **aguardando** — será registrada aqui verbatim quando chegar.

**Nada foi publicado e nada foi empurrado a `origin`.** Sem `bump.sh`, sem `publicar-web.sh`, sem `entregar.sh`. `server/web_dist`, `server/admin_dist`, `web/src/version.js` e `SERVER_BUILD_ID` intocados.

## Next Phase Readiness

- **27-04 está destravado** no que depende deste plano: a tela já consome `positions`, já tem o bloco de vigias e já tem o lastro no cartão.
- **O que o 27-05 herda, nomeado:** tirar `mcpLeitura` do efeito de troca de ticker, movê-la para `METODOS` e removê-la de `EFEITO_PERMITIDO` — o comentário no guardião diz isso com todas as letras, então a asserção nasce verde no dia em que o 27-05 fizer a mudança e vermelha se alguém esquecer metade dela. O 27-05 também passa a declarar na tela o custo de `mcpStatus` (até 1).
- **Bloqueio para publicação:** este checkpoint e o do 27-01 precisam ser fechados antes de qualquer push da fase (histórico: "fase com checkpoint humano segura o push da FASE INTEIRA").

## Self-Check: PASSED

- `web/tests/test_opcoes_universo_carteira.mjs` — FOUND
- `web/tests/test_opcoes_vigias_ui.mjs` — FOUND
- commits `4115ec9`, `140f9e8`, `f3668d3`, `cd8fe7c`, `466f2a9` — FOUND em `git log`
- `bash scripts/executar.sh --testes` — exit 0, `2773 passed, 5 skipped, 3 xfailed, 0 failed` + `141/141 .mjs`
- `cd web && npx vite build` — verde; `web/dist` restaurado ao build publicado
- `git status --short` — limpo

---
*Phase: 27-aba-opcoes-sobre-a-carteira*
*Completed: 2026-09-13 (checkpoint final em aberto)*
