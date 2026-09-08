---
phase: quick/260907-vwl
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - web/src/App.jsx
  - web/tests/test_ordens_pendentes_ui.mjs
autonomous: true
requirements: [VWL-01]
must_haves:
  truths:
    - "Com o mercado fechado, o aviso de ordem pendente aparece em bloco próprio destacado (fundo T.warn a 14%, texto T.warn), não mais na letra miúda T.textFaint 11px"
    - "O aviso de pendente não vem mais concatenado com a frase de execução tudo-ou-nada — são dois elementos separados"
    - "A frase 'Esta simulação executa por completo ou não executa...' continua visível em ambos os estados (aberto e fechado), no slot T.textFaint de sempre"
    - "Com o mercado aberto, a confirmação de ordem é byte-idêntica ao comportamento atual"
    - "COMPRA e VENDA recebem tratamento visual simétrico, cada um com sua função de copy"
  artifacts:
    - path: "web/src/App.jsx"
      provides: "Bloco de aviso de pendente destacado em BuyModal e SellModal"
      contains: "ordemPendenteAvisoCompra"
    - path: "web/tests/test_ordens_pendentes_ui.mjs"
      provides: "Guardião estendido — trava o destaque visual nos dois ramos"
  key_links:
    - from: "web/src/App.jsx (BuyModal)"
      to: "web/src/copy.js ordemPendenteAvisoCompra"
      via: "ctx.cp.ordemPendenteAvisoCompra(ctx.mercado.abertura)"
      pattern: "ordemPendenteAvisoCompra\\(ctx\\.mercado\\.abertura\\)"
    - from: "web/src/App.jsx (SellModal)"
      to: "web/src/copy.js ordemPendenteAvisoVenda"
      via: "ctx.cp.ordemPendenteAvisoVenda(ctx.mercado.abertura)"
      pattern: "ordemPendenteAvisoVenda\\(ctx\\.mercado\\.abertura\\)"
---

<objective>
Tirar o aviso de ordem pendente do slot de letra miúda (`T.textFaint`, 11px) e
dar a ele peso visual próprio nos dois modais de confirmação de ordem
(`BuyModal` e `SellModal`), reusando a mesma linguagem visual do pill
"PENDENTE" que já existe logo acima no mesmo bloco.

Purpose: achado ao vivo em 2026-09-07 (staging, iPhone) — o usuário comprou 100
ABEV3 com o mercado fechado (feriado de 7/9), a ordem virou pendente com R$
1.574 de caixa reservado, ele VIU o aviso mas passou batido e seguiu achando
que tinha posição executada. Uma mudança de estado real (dinheiro reservado
agora, nada executa agora) está tipografada como boilerplate e ainda vem
concatenada com a frase de execução tudo-ou-nada, diluindo as duas.

Output: `web/src/App.jsx` com bloco de aviso destacado nos dois ramos; guardião
`web/tests/test_ordens_pendentes_ui.mjs` estendido para travar a simetria.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md

@web/src/App.jsx
@web/tests/test_ordens_pendentes_ui.mjs

**Estado atual do código (já lido — não precisa reexplorar):**

`BuyModal` (função em `web/src/App.jsx`, começa em ~7554):
- linha ~7566: `const fechado = ctx.mercado && ctx.mercado.aberto === false;`
- linha ~7575: pill "PENDENTE" já existente, com `padding: "3px 9px"`,
  `borderRadius: "999px"`, `background: "color-mix(in srgb, " + T.warn + " 14%, transparent)"`,
  `color: T.warn`, `fontSize: "10.5px"`, `fontWeight: 800` — **esta é a
  referência visual a ser reusada**
- linha ~7605: a linha a mudar (slot `T.textFaint` 11px com a concatenação)
- linha ~7607: bloco de `statusIndisponivel` — outro exemplo de caixa `T.warn`
  já no arquivo (`padding: "9px 11px"`, `borderRadius: "9px"`, `color-mix` a 12%)

`SellModal` (função em `web/src/App.jsx`, começa em ~7624):
- linha ~7653: mesmo `const fechado`
- linha ~7662: pill "PENDENTE" gêmeo
- linha ~7705: a linha a mudar (gêmea da 7605, com texto de aberto diferente:
  `"O preço final é o da cotação no momento da confirmação (servidor). Registro vai para o histórico do ativo."`)

**Copy existente (NÃO editar `web/src/copy.js`):**
- `ctx.cp.ordemPendenteAvisoCompra(abertura)` e
  `ctx.cp.ordemPendenteAvisoVenda(abertura)` — funções que recebem
  `ctx.mercado.abertura` e já tratam `abertura == null` sem inventar horário.
  Definidas 1x por modo (estudo linha ~116/120, operador ~344/348).

**Guardiões relevantes:**
- `web/tests/test_chart_colors_theme_aware.mjs` — proíbe hex solto fora do
  PALETTE; em particular `#fbbf24` só pode aparecer 1x no arquivo inteiro
  (a definição do token `warn`). Usar `T.warn`, nunca o hex.
- `web/tests/test_ordens_pendentes_ui.mjs` linhas 79-82 — já exige que
  `BuyModal` contenha `ordemPendenteAvisoCompra` **e** `T.warn`, e que
  `SellModal` contenha `ordemPendenteAvisoVenda`.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Destacar o aviso de pendente nos dois modais (COMPRA e VENDA)</name>
  <files>web/src/App.jsx</files>
  <action>
Editar APENAS as duas linhas de disclaimer dos modais de confirmação — a de
`BuyModal` (~7605) e a gêmea de `SellModal` (~7705). Nada mais do arquivo é
tocado: sem refatoração de componente, sem mexer no pill, no bloco de
`statusIndisponivel`, no `DISCLAIMERS.trade` nem nos botões.

Em cada um dos dois pontos, substituir a linha única por DOIS elementos irmãos,
nesta ordem:

1. Um bloco condicional renderizado só quando `fechado` for true, contendo
   SOMENTE a frase de pendente — `ctx.cp.ordemPendenteAvisoCompra(ctx.mercado.abertura)`
   no `BuyModal` e `ctx.cp.ordemPendenteAvisoVenda(ctx.mercado.abertura)` no
   `SellModal`. Estilo inline, reusando a linguagem visual do pill "PENDENTE"
   que já está algumas linhas acima no mesmo componente: `background` via
   `"color-mix(in srgb, " + T.warn + " 14%, transparent)"`, `color: T.warn`,
   `marginTop: "8px"`, `padding: "10px 12px"`, `borderRadius: "9px"` (caixa,
   não pill — o pill de 999px continua sendo só o rótulo curto lá em cima),
   `fontSize: "12.5px"`, `fontWeight: 700`, `lineHeight: 1.45`. Concatenação de
   string para o `color-mix` (`"... " + T.warn + " ..."`) é o padrão já usado
   nas linhas 7575/7607 — seguir o mesmo, não introduzir template literal novo.
   Proibido: qualquer cor literal/hex — só os tokens `T.warn` / `T.textFaint`
   (há guardião de tema em `test_chart_colors_theme_aware.mjs`).

2. O `div` de letra miúda de sempre (`fontSize: "11px"`, `color: T.textFaint`,
   `marginTop: "8px"` no BuyModal / `"6px"` no SellModal — preservar o valor
   que já está em cada um), agora contendo: quando `fechado` for false, o texto
   de aberto de hoje seguido da frase de execução total (mesmíssimo resultado
   de string que a versão atual produz — no BuyModal `"O preço final é o da
   cotação no momento da confirmação (servidor)."`, no SellModal a variante que
   termina em `"Registro vai para o histórico do ativo."`); quando `fechado`
   for true, SOMENTE a frase `"Esta simulação executa por completo ou não
   executa — não há preenchimento parcial de ordem."` (a frase de pendente já
   saiu para o bloco destacado; a frase de aberto não se aplica).

Invariantes a preservar:
- Ramo `fechado === false` sai visualmente idêntico ao de hoje (mesma string,
  mesmo slot, mesmo estilo) — a mudança é só no ramo `fechado === true`.
- Simetria entre os dois modais: mesma estrutura, mesmo estilo, mesmos valores;
  a única diferença é a função de copy (`...Compra` vs `...Venda`) e o texto de
  mercado aberto que cada um já tinha.
- `web/src/copy.js` NÃO é editado; nenhum texto novo é inventado.
- Deixar um comentário curto acima do bloco novo registrando o porquê (achado
  ao vivo 2026-09-07: aviso de pendente no slot `textFaint` passou batido e o
  usuário achou que a ordem tinha executado) — o repositório usa comentário
  para carregar histórico de decisão.
  </action>
  <verify>
    <automated>npx vite build --root web && node web/tests/test_ordens_pendentes_ui.mjs && node web/tests/test_chart_colors_theme_aware.mjs</automated>
  </verify>
  <done>
`BuyModal` e `SellModal` renderizam, quando `fechado`, um bloco com fundo
`color-mix` de `T.warn` a 14% e texto `T.warn` contendo só o aviso de pendente;
a frase de execução tudo-ou-nada permanece no `div` `T.textFaint` 11px em ambos
os estados; nenhuma cor literal introduzida; `web/src/copy.js` intocado;
`npx vite build` passa (sem erro de sintaxe JSX).
  </done>
</task>

<task type="auto">
  <name>Task 2: Estender o guardião de ordens pendentes e rodar a suíte canônica</name>
  <files>web/tests/test_ordens_pendentes_ui.mjs</files>
  <action>
Estender o guardião existente (`web/tests/test_ordens_pendentes_ui.mjs`, bloco
de asserts sobre `BuyModal`/`SellModal` nas linhas ~79-82, que hoje só checa
presença de `ordemPendenteAvisoCompra` + `T.warn` no BuyModal e
`ordemPendenteAvisoVenda` no SellModal) com asserts que travam o achado de
2026-09-07 e a simetria entre os dois ramos. Usar o mesmo estilo do arquivo:
`functionBody(nome)` / recorte por componente + `ok(nome, cond)`, sem framework
de teste, executável por `node web/tests/test_ordens_pendentes_ui.mjs`.

Asserts a acrescentar (um por ramo, simétricos):
1. `SellModal` também usa `T.warn` (paridade com o BuyModal, que já é exigido).
2. Em cada componente, o aviso de pendente aparece dentro de um trecho que
   carrega `color-mix` com `T.warn` — isto é, existe no corpo da função uma
   ocorrência de `ordemPendenteAviso(Compra|Venda)` cujo elemento envolvente
   também contém `color-mix(in srgb, " + T.warn` (recorte simples por regex/
   janela de string basta; o objetivo é impedir a volta silenciosa ao slot
   apagado).
3. Em cada componente, `ordemPendenteAviso(Compra|Venda)` NÃO aparece mais na
   mesma expressão que `"preenchimento parcial de ordem"` — trava a
   des-concatenação (o aviso de estado não volta a ser diluído no boilerplate).
4. Em cada componente, a frase `"Esta simulação executa por completo ou não
   executa"` continua presente (não foi perdida na edição).

Adicionar comentário no topo do bloco novo com a origem (achado ao vivo
2026-09-07, staging/iPhone, compra de 100 ABEV3 com mercado fechado) — pelo
guardrail do repositório, guardião carrega o porquê e não se apaga.

Depois, rodar a suíte canônica completa (pytest do backend + `web/tests/*.mjs`),
que é a única validação que conta neste repositório.
  </action>
  <verify>
    <automated>node web/tests/test_ordens_pendentes_ui.mjs && bash scripts/executar.sh --testes</automated>
  </verify>
  <done>
Guardião estendido falha se o aviso voltar ao slot `T.textFaint` ou voltar a ser
concatenado com a frase de execução total, nos DOIS ramos; suíte canônica
(`bash scripts/executar.sh --testes`) verde — pytest do backend e todos os
`web/tests/*.mjs`, incluindo `test_chart_colors_theme_aware.mjs`,
`test_ordens_pendentes_ui.mjs` e `test_status_mercado_ui.mjs`.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| (nenhuma nova) | Mudança é 100% de apresentação no cliente; não cria entrada de dado, rota, chamada externa nem cálculo |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-vwl-01 | Information Disclosure | `BuyModal`/`SellModal` | accept | Nenhum dado novo é exibido — a mesma string de `copy.js` só muda de slot visual |
| T-vwl-02 | Tampering | `web/src/copy.js` | mitigate | Arquivo fora de `files_modified`; guardião de paridade de copy já existente barra alteração de texto |
| T-vwl-SC | Tampering | npm/pip/cargo installs | mitigate | N/A — nenhuma dependência instalada nesta tarefa |
</threat_model>

<verification>
1. `npx vite build --root web` — pega erro de sintaxe JSX que grep/teste
   estático não pega (obrigatório sempre que o front é editado).
2. `bash scripts/executar.sh --testes` — suíte canônica DUPLA (pytest do
   backend + `web/tests/*.mjs`). `scripts/test.sh` sozinho é meia baseline e
   NÃO conta como validação.
3. Inspeção do diff: confirmar que só as duas linhas de disclaimer mudaram em
   `web/src/App.jsx`, que os dois ramos ficaram simétricos, e que
   `web/src/copy.js` está intocado (`git diff --stat` não deve listá-lo).
</verification>

<success_criteria>
- [ ] Com `fechado === true`, o aviso de pendente aparece em bloco próprio com
      fundo `color-mix` de `T.warn` a 14% e texto `T.warn`, em COMPRA e VENDA
- [ ] O aviso de pendente não está mais concatenado com a frase de execução
      tudo-ou-nada, nos dois ramos
- [ ] Com `fechado === false`, o texto e o estilo são idênticos aos de hoje
- [ ] Zero cor literal/hex introduzida — só `T.warn` e `T.textFaint`
- [ ] `web/src/copy.js` não aparece no diff
- [ ] `npx vite build --root web` passa
- [ ] `bash scripts/executar.sh --testes` verde (pytest + web/tests)
- [ ] Guardião estendido em `web/tests/test_ordens_pendentes_ui.mjs` trava a
      regressão nos dois ramos
</success_criteria>

<out_of_scope>
- **Publicação não faz parte desta quick task.** Levar isto a produção exige um
  follow-up separado: `scripts/bump.sh` seguido de `scripts/publicar-web.sh`
  (nunca editar `server/web_dist` direto). Escopo aqui é código + testes.
- Não editar `web/src/copy.js` nem criar texto novo.
- Não refatorar `BuyModal`/`SellModal` além das duas linhas de disclaimer.
- Não mexer no pill "PENDENTE", no bloco de `statusIndisponivel`, no toast de
  ordem pendente nem na tela de ordens pendentes.
</out_of_scope>

<output>
Create `.planning/quick/260907-vwl-reforcar-aviso-visual-de-ordem-pendente-/260907-vwl-SUMMARY.md` when done
</output>
