---
phase: 24-opcoes-mcp-analise-e-setups
plan: 02
subsystem: front
tags: [react, svg, opcoes, payoff, copy, stores, guardiao]

# Dependency graph
requires:
  - phase: 24 (plano 24-01)
    provides: "`/cadeia`, `/operaveis`, `/proposta`, `/possibilidades` com envelope estável, `emReais` fechado no backend e `chamadasPrevistas` na resposta"
  - phase: 23 (aba-opcoes F1/F2 — ADR-027)
    provides: "`OpcoesScreen`/`useOpcoesMcp`/`SetupChart`, `chartutil.js`, os três métodos MCP nos dois stores, o bloco de copy da aba"
provides:
  - "`PayoffChart.jsx` — curva de resultado no vencimento com eixo X em preço do objeto, breakevens, cenários e ilimitado declarado"
  - "seções Analisar e Possibilidades em `OpcoesScreen.jsx`, sob demanda, com o custo em chamadas ANTES do clique"
  - "`useChamadaSobDemanda` — quatro trios `{dados, carregando, erro}` com contador próprio e conferência de ticker"
  - "quatro rotas alcançáveis pelos DOIS stores + 28 chaves de copy nas duas vozes"
  - "`test_opcoes_analisar_ui.mjs` — 120 asserções, com sanidade provada por injeção de defeito"
affects: [24-03, 24-04, 24-05, fase-4-veredito, fase-6-fluxo-do-iniciante]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gráfico de payoff em SVG com X mapeado por PREÇO (não por índice) e recorte interpolado da poligonal — zoom, não edição"
    - "Cauda da curva só se estende quando o serviço declarou os DOIS lados limitados (aí a inclinação é zero por definição)"
    - "Hook interno (`useChamadaSobDemanda`) para chamadas que custam cap: contador por chamada + conferência de ticker na volta"
    - "Cascata de erro por `code` duplicada de propósito (`ErroDoMcp`), declarada depois do componente para não inverter a ordem que o guardião lê"

key-files:
  created:
    - web/src/opcoes/PayoffChart.jsx
    - web/tests/test_opcoes_analisar_ui.mjs
  modified:
    - web/src/api.js
    - web/src/persistence.js
    - web/src/copy.js
    - web/src/opcoes/useOpcoesMcp.js
    - web/src/opcoes/OpcoesScreen.jsx

key-decisions:
  - "O eixo X do payoff é mapeado por PREÇO, não pelo índice do ponto: os nós que o serviço manda são os strikes (mais S=0) e são irregulares — `linePath` (índice) poria o breakeven no lugar errado"
  - "A janela do gráfico é recortada em torno de strikes/breakevens/cenários, com interpolação no corte: desenhar de 0 ao último strike esmaga contra a borda a região onde a decisão acontece"
  - "Cauda direita estendida SÓ com `unlimited_gain === false && unlimited_loss === false`; com qualquer ilimitado a curva simplesmente termina"
  - "Nenhum `fill` em `<path>`: lado sem limite não pode aparecer fechado por um retângulo"
  - "Seletor de vencimento com default \"o serviço escolhe\" (valor vazio) — fingir que fomos nós que escolhemos o primeiro da lista seria a tela assumindo uma decisão que não tomou"
  - "Trocar de ticker apaga tese, vencimento, alvo e stop; o lote fica (é da pessoa, não do ativo)"
  - "`ErroDoMcp` mora DEPOIS do componente: um literal `mcp_nao_configurado` acima inverteria a ordem carregando → erro → vazio → dados que `test_opcoes_mcp_aba_ui.mjs` lê no fonte"

patterns-established:
  - "Estilo compartilhado (`BOTAO`, `CAMPO`) carrega o `minHeight: 44px` — alvo de toque que não se esquece porque não se digita duas vezes"
  - "Tabela de dado largo rola no CONTAINER (`overflowX: auto`), nunca no `body`"

requirements-completed: ["PLANO Fase 3 — front"]

# Metrics
duration: 28min
completed: 2026-09-11
---

# Phase 24 Plano 02: Aba Opções — Analisar e Possibilidades Summary

**A tese vira estrutura na tela: por vencimento, a pessoa vê as pernas, a curva de payoff em preço do objeto, o custo/ganho/perda em reais para o lote dela — e o preço em chamadas da consulta aparece ANTES do clique, não depois.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-09-11T19:50:36Z
- **Completed:** 2026-09-11T20:19:34Z
- **Tasks:** 4
- **Files modified:** 7 (5 modificados, 2 criados)

## Accomplishments

- Quatro rotas da F3 alcançáveis pelos DOIS stores, com `qs()` (chave sem valor vira ausência do parâmetro) e 60 s só em `/possibilidades` — as outras três em 30 s.
- 28 chaves de copy novas, conjunto IGUAL nos dois modos, com as quatro afirmações regulatórias (delta, ±1σ, breakeven, ilimitado) repetindo a substância nas duas vozes.
- `PayoffChart`: curva em SVG puro com eixo X em preço, linha do zero, breakevens marcados em preço, cenários do serviço sobre a curva, ilimitado declarado e nunca fechado.
- Seções Analisar e Possibilidades entre a leitura e os setups, ambas sob demanda, com `2 × N + 1` (N ≤ 6) visível antes do disparo e falha por vencimento isolada.
- Guardião novo com 120 asserções e as três regex de defeito **provadas** (injetei `* lote`, `emReais.breakeven` e `|| 0`, vi vermelho, revertí).
- Verificação de RENDER além do estático: renderizei a tela inteira com `react-dom/server` em três variantes (painel fechado, cadeia, operáveis) e o `PayoffChart` em sete cenários — é o que provou a geometria da curva e o corte em 6 vencimentos.

## Task Commits

1. **Task 1: api.js, persistence.js (dois stores) e copy.js (dois modos)** — `44d024b` (feat)
2. **Task 2: PayoffChart.jsx — a curva em preço do objeto** — `4bb65e0` (feat)
3. **Task 3: useOpcoesMcp sob demanda + seções Analisar e Possibilidades** — `04c6fb1` (feat)
4. **Task 4: guardião estático das seções novas** — `3b48c7b` (test)

## Files Created/Modified

- `web/src/api.js` — helper `qs()` + `mcpCadeia`/`mcpOperaveis`/`mcpProposta` (30 s) e `mcpPossibilidades` (60 s).
- `web/src/persistence.js` — os quatro métodos nos DOIS stores, delegação pura (nada persistido: cachear carimbaria pregão velho como do dia).
- `web/src/copy.js` — 28 chaves nos dois blocos.
- `web/src/opcoes/PayoffChart.jsx` — componente novo (305 linhas), SVG puro, zero dependência nova.
- `web/src/opcoes/useOpcoesMcp.js` — `useChamadaSobDemanda` + quatro trios + quatro ações; o efeito de troca de ticker agora também APAGA os quatro.
- `web/src/opcoes/OpcoesScreen.jsx` — duas seções novas + `ErroDoMcp`, `Pernas`, `TabelaDeOpcoes`, `Cenarios`.
- `web/tests/test_opcoes_analisar_ui.mjs` — guardião novo.

## Verificação

Suíte canônica inteira, FORA do sandbox (`bash scripts/executar.sh --testes`):

```
2379 passed, 5 skipped, 549 warnings in 46.88s
128 arquivos web/tests/*.mjs [OK], 0 falhas
exit=0
```

Baseline antes deste plano: **2379 passed, 5 skipped** + 127 `.mjs`. Delta: **0 no pytest** (o plano não toca `server/`) e **+1 arquivo `.mjs`** (o guardião novo). Nenhuma regressão.

`cd web && npx vite build` → `✓ built in 952ms`, sem erro. Rodado depois de CADA task (o plano exige, e grep não pega erro de sintaxe JSX).

`git diff 14625a1 HEAD --stat -- web/package.json package-lock.json` → vazio. Nenhuma dependência nova (T-24-SC).

**Render de verdade, além do estático.** O guardião é sintático; a geometria da curva não é. Montei um harness temporário (esbuild + `react-dom/server`, arquivos apagados depois, nada commitado):

- `PayoffChart` em 7 cenários sobre a fixture `mcp_evaluate_petr4.json`. Com os dois lados limitados, o caminho sai `M10.0 147.6 L140.7 147.6 L232.5 20.4 L310.0 20.4` — plano até o strike 38, subindo até 40, plano de novo até a borda. Com `unlimited_gain`, o MESMO caso termina em `L232.5 20.4`: a curva PARA no último strike em vez de inventar inclinação.
- `OpcoesScreen` completa, em três variantes. Com 7 vencimentos na leitura, a tela mostra **13** chamadas e lista **6** vencimentos — o corte do `N ≤ 6` está do lado certo. Os três itens de possibilidade (estrutura, `motivo`, `erro`) renderizam juntos: um vencimento que falhou não apaga os outros.

**Prova de que o guardião não passa por vacuidade** (critério de aceite da Task 4), três defeitos injetados e revertidos:

| Defeito injetado | Onde | Resultado |
|---|---|---|
| `const errado = 1.5 * lote;` | `OpcoesScreen.jsx` | `FALHOU OpcoesScreen.jsx não multiplica por lote` → 1 FALHA(S) |
| `moeda(emReais && emReais.breakeven)` | `PayoffChart.jsx` | `FALHOU PayoffChart.jsx não mistura emReais e breakeven na mesma expressão` |
| `const zeroErrado = v \|\| 0;` | `OpcoesScreen.jsx` | `FALHOU OpcoesScreen.jsx sem \`\|\| 0\`` |

Revertido com `git checkout --` nos dois arquivos; `diff` contra a cópia pré-injeção confirma byte a byte, e `git status` ficou limpo.

## Decisions Made

- **X por preço, não por índice.** O plano pedia `linePath` de `chartutil.js` sobre os `result`. `linePath` espaça os pontos por ÍNDICE, e os pontos do payoff são os nós da função linear por partes — `{0, strike₁, strike₂, …}`, irregulares por construção (na fixture: 0 → 38 → 40). Com espaçamento por índice, o trecho de 38 unidades e o de 2 ganhariam a mesma largura na tela, e a marca vertical do breakeven (que eu desenho em proporção de PREÇO) cairia sobre a curva no lugar errado. `extentOf` continua sendo usado de `chartutil.js`; o caminho é montado com a escala de preço.
- **Janela recortada com interpolação no corte.** Desenhar de S=0 até o último strike joga a região da decisão contra a borda direita. A janela cobre strikes, breakevens e cenários com 8% de folga, e o recorte interpola nos limites — o que é exato, porque entre dois nós a função É a reta.
- **Cauda só quando os dois lados são limitados.** `unlimited_gain === false && unlimited_loss === false` significa inclinação zero à direita (é o que `opcoes_payoff` calcula e o que a paridade do 24-01 provou valer também no serviço), então estender na horizontal é ler o que ele afirmou. Com qualquer ilimitado, a magnitude é desconhecida e a curva termina no último nó.
- **Seletor de vencimento (não estava no plano).** `montarProposta({..., expiration})` carrega `expiration` na assinatura que o plano fixou, mas o plano não disse de onde ele viria; sem seletor o campo seria código morto e as duas consultas secundárias (cadeia/operáveis) voltariam com 50 contratos de vencimentos misturados. O default é `""` = "o serviço escolhe", que é a chamada sem filtro — a escolha fica VISÍVEL e a tela não assume uma decisão que não tomou.
- **`cp.opcoesSemEstrutura` é sobre a CURVA, não sobre a estrutura.** `/proposta` devolve a estrutura montada SEM `payoff` (quem produz a curva é `evaluate_option_structure`, que só `/possibilidades` chama). Então o `PayoffChart` mostra o cabeçalho com as cifras e, no lugar do SVG, diz que o serviço não mandou os pontos. O texto da chave foi escrito para esse caso; `estruturas: []` continua sendo o `motivo` verbatim do serviço, como o plano pediu.
- **`side` da perna aparece como "compra"/"venda" nos dois modos.** É a descrição da PERNA ("esta trava compra o 38 e vende o 40"), não instrução a quem lê — sem ela a estrutura fica ininteligível. O que o Estudo não tem é veredito em voz de ordem, e isso segue valendo.
- **`criterio` do serviço vai verbatim, em inglês.** `find_tradable_options` devolve `criteria` em inglês ("a computed IV and at least 100 trades…"). Traduzir seria a tela falando pelo serviço; então ele aparece atribuído ("Como o serviço descreveu a peneira: …") logo abaixo do `cp.opcoesCriterioOperaveis(criterioAplicado)`, que é o MESMO critério em PT-BR com os números do Boris (D-24.4).
- **`situacao_sigma` é coluna de primeira classe** na tabela de cadeia/operáveis: é ela que explica por que delta e volatilidade vêm vazios em ~10% dos contratos. Sem ela, o travessão vira "o app não sabe" onde o serviço declarou o motivo.

## Deviations from Plan

### Ajustes de execução

**1. [Rule 1 — defeito de desenho] `linePath` trocado por escala de preço**
- **Found during:** Task 2, ao ler a fixture `mcp_evaluate_petr4.json` (`payoff` = 3 pontos: 0, 38, 40).
- **Issue:** o plano mandava desenhar com `linePath` (X por índice). Com nós irregulares, isso distorce as larguras e desalinha as marcas de breakeven, que são medidas em preço. Seria um gráfico que afirma coisa diferente do número ao lado.
- **Fix:** escala própria `sx(u)` por preço; `extentOf` de `chartutil.js` segue em uso para o eixo Y.
- **Verification:** render dos 7 cenários; caminho confere com a geometria esperada.
- **Committed in:** `4bb65e0`

**2. [Rule 2 — chave faltando] `opcoesMontarEstrutura` acrescentada à "lista fechada" de copy**
- **Found during:** Task 1.
- **Issue:** a lista de chaves do plano não tinha texto para o botão PRINCIPAL da seção Analisar ("montar estrutura"), que o próprio plano descreve na Task 3. Guardrail do repo: todo texto sai de `cp.*`, nas duas vozes.
- **Fix:** 28ª chave, nos dois modos ("Montar a estrutura" / "Montar estrutura").
- **Committed in:** `44d024b`

**3. [ajuste] `opcoesCadeiaTruncada` não é `(t) => t` puro**
- O plano escreveu `(t) => t`. O texto do serviço segue VERBATIM, mas com atribuição ("A lista veio cortada pelo serviço. Na palavra dele: …"), que é o padrão já estabelecido por `opcoesNaoAvaliado`. Sem atribuição, um texto em inglês do serviço apareceria como se fosse do app. `null` vira "sem detalhe informado.", nunca string vazia.

**4. [ajuste] seletor de vencimento** — ver Decisions Made. Um `<select>` novo na seção Analisar, com label literal "Vencimento" (mesmo precedente dos rótulos curtos já literais no arquivo, como "Tendência").

**5. [ajuste] `ErroDoMcp` duplica a cascata de códigos, de propósito**
- A cascata da cadeia de estados principal NÃO pode sair do lugar: `test_opcoes_mcp_aba_ui.mjs` lê a posição da primeira ocorrência de `mcp_nao_configurado` para provar a ordem carregando → erro → vazio → dados. Extrair a cascata para um componente acima do `OpcoesScreen` inverteria essa ordem sem nada ter mudado na tela; movê-la para baixo E fazer a principal chamá-la faria o mesmo. Então a principal fica literal e as quatro seções novas usam `ErroDoMcp`, declarada depois do componente. O guardião novo trava os quatro códigos nas DUAS.

### Divergências de contagem nos critérios de aceite (não são defeito)

**6. `grep -c "mcpPossibilidades" web/src/persistence.js` dá 3, não 2.** `grep -c` conta LINHAS. No `serverStore` o método é uma linha (`mcpCadeia: (t, q) => api.mcpCadeia(t, q),`); no `deviceStore`, o formato que o próprio plano prescreveu ocupa duas (`async mcpCadeia(t, q) {` + `return api.mcpCadeia(t, q);`). O `mcpLeitura` pré-existente conta 3 pela mesma razão. Verificado o que o critério queria dizer, fatiando o arquivo nos dois stores: **2 ocorrências em cada um**, idêntico ao `mcpLeitura` — e o guardião novo passou a travar isso por store, não por contagem global.

**7. `grep -c "useEffect" web/src/opcoes/useOpcoesMcp.js` dá 3, não 2 — e já dava antes deste plano.** A linha do `import { useCallback, useEffect, ... }` conta. O que o critério protege (nenhuma chamada nova por efeito) está intacto: continuam sendo DOIS `useEffect(`, e o guardião novo verifica o que importa — fatia o corpo de cada efeito e prova que nenhum menciona `mcpCadeia`/`mcpOperaveis`/`mcpProposta`/`mcpPossibilidades`.

**8. "Todo botão interativo novo tem `minHeight: "44px"`" é cumprido por constante, não por repetição.** `grep -c 'minHeight: "44px"'` na tela dá 4, e não um por botão: os botões novos herdam de `BOTAO` e os campos de `CAMPO`. O guardião checa as DUAS constantes — assim o alvo de toque não depende de ninguém lembrar de digitá-lo.

**9. Guardião com 120 `ok`, o plano pedia ≥ 9.** Os 9 itens listados estão todos cobertos; o resto são as asserções de sanidade obrigatórias e a checagem por arquivo (4 arquivos × 4 regras).

---

**Total deviations:** 5 ajustes + 4 divergências de contagem. Nenhuma mudança arquitetural; nenhuma dependência nova.
**Impact on plan:** nenhum item deixou de ser entregue.

## Issues Encountered

- **`/proposta` não traz `payoff`.** Só `evaluate_option_structure` produz a curva, e `/proposta` não a chama (custo 1). Descoberto lendo o `CHAVES_DA_ESTRUTURA` do 24-01 contra o contrato do serviço — antes de escrever a tela, não depois. Por isso o `PayoffChart` nasceu com o caminho "cabeçalho sem curva" como estado de primeira classe, e não como erro.
- **Chaves em dois idiomas no mesmo payload.** As pernas de `propose_option_setups` vêm em inglês (`contract`, `side`, `premium`); as linhas de cadeia/operáveis vêm em PT-BR (`contrato`, `premio`, `total_negocios`). São duas tabelas diferentes no componente de propósito — unificar exigiria um mapeamento que mentiria sobre a origem de cada campo.
- **`useId()` traz `:` no valor** e viraria referência inválida em `url(#…)`. Como a seção de possibilidades renderiza até 6 gráficos na mesma página, dois `clipPath` com id colidindo pintariam a curva errada. Id saneado com `replace(/[^a-zA-Z0-9_-]/g, "")`.

## Known Stubs

Nenhum. Toda seção nova lê dado real das rotas do 24-01; nenhum componente recebe mock ou valor fixo. Os únicos literais de texto fora de `cp.*` são rótulos curtos de coluna e dois estados vazios ("A cadeia deste ativo voltou sem contrato…", "O serviço não montou estrutura para esta tese e não informou o motivo."), no mesmo padrão que a F2 já usava para o estado `sem_candles`.

## Pendências de verificação (declaradas)

- **Nada foi exercitado ao vivo** (D-24.7): `MCP_CLIENT_SECRET` não está no ambiente. A tela foi verificada por render com dados da fixture; que o serviço real preencha esses campos exatamente assim é o que o smoke de staging deve confirmar.
- **Nenhum teste em aparelho.** Rolagem horizontal da tabela em 375 px, `<select>` e `<input type="number">` no WKWebView e o contraste das duas cores de P&L nos dois temas só se verificam no iPhone — e este plano não publica nada (o 24-05 é quem faz bump + `publicar-web.sh`, só com o OK do Alex).
- **`cp.opcoesCenariosTitulo` só aparece quando `emReais` traz cenários**, ou seja, na seção Possibilidades. Em `/proposta` o serviço não devolve `scenarios`, então a lista textual não existe lá — é ausência do dado, não omissão da tela.

## Threat Flags

Nenhuma superfície nova fora do `<threat_model>` do plano. T-24-06 (dobrar o número em reais) fica travado por guardião com sanidade provada; T-24-07 (custo do `/possibilidades`) é mitigado por botão desabilitado sem tese/lote, N ≤ 6 e custo declarado antes do clique; T-24-08 (curva que mente) por curva sem `fill` e cauda que só se estende sob limite declarado; T-24-09 (erro por vencimento) pela mensagem já sanitizada do backend em `pre-wrap`, sem stack. Nenhum pacote instalado.

## Next Phase Readiness

Pronto para o **24-03/24-04** (Fase 5 do PLANO: criação de setups). As peças reutilizáveis já estão no lugar: `useChamadaSobDemanda` serve qualquer chamada nova que custe cap, `ErroDoMcp` já cobre os quatro códigos do ADR-027 e `PayoffChart` aceita qualquer estrutura no formato de `evaluate_option_structure`.

Bloqueio conhecido para a publicação: nada disto vai ao ar sem o bump + `publicar-web.sh` do 24-05.

---
*Phase: 24-opcoes-mcp-analise-e-setups*
*Completed: 2026-09-11*

## Self-Check: PASSED

Os arquivos afirmados existem (`PayoffChart.jsx`, `test_opcoes_analisar_ui.mjs`, este SUMMARY) e os quatro commits estão no histórico (`44d024b`, `4bb65e0`, `04c6fb1`, `3b48c7b`).
