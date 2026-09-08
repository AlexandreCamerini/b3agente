---
phase: quick-260907-vzp
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - web/src/finance.js
  - web/src/App.jsx
  - web/tests/test_setup_operavel_adr017.mjs
autonomous: true
requirements: [ADR-017-D1]
must_haves:
  truths:
    - "O `setupEntrada` gravado numa compra descreve UM ÚNICO setup: `setup`, `lado`, `gatilho` e `invalidacao` vêm do mesmo elemento de `setups`, nunca de elementos diferentes."
    - "Setup marcado `aposentado: true` nunca vira base de plano operacional (lado/gatilho/invalidação gravados ou exibidos como acionáveis), mas continua aparecendo na lista de estudo do Radar."
    - "Sem nenhum setup operável na lista, os campos `lado`/`gatilho`/`invalidacao` ficam AUSENTES no meta de entrada — nada de `0`, `null` fabricado ou o aposentado como stand-in."
    - "A régua INVALIDAÇÃO/GATILHO/ALVO 2:1 do Radar não renderiza níveis de setup aposentado."
    - "A suíte canônica (pytest + web/tests) segue verde e `vite build` compila."
  artifacts:
    - path: "web/src/finance.js"
      provides: "setupOperavel() + metaDeEntrada() — regra de seleção do setup operável, espelho de setups.py:725"
      contains: "export function setupOperavel"
    - path: "web/src/App.jsx"
      provides: "os dois pontos de consumo corrigidos (buyMeta da watchlist e s0 do Radar)"
      contains: "setupOperavel"
    - path: "web/tests/test_setup_operavel_adr017.mjs"
      provides: "guardião híbrido — unidade de finance.js + grep estático de App.jsx"
  key_links:
    - from: "web/src/App.jsx (grade da watchlist, ~L3911)"
      to: "metaDeEntrada() em finance.js"
      via: "import + chamada única, substituindo `(sc.setups || [])[0]`"
      pattern: "metaDeEntrada\\(sc\\)"
    - from: "web/src/App.jsx (card do Radar, ~L6955)"
      to: "setupOperavel() em finance.js"
      via: "substituição de `(r.setups || [])[0]`"
      pattern: "setupOperavel\\(r\\.setups"
    - from: "web/tests/test_setup_operavel_adr017.mjs"
      to: "web/src/finance.js"
      via: "import ESM direto (padrão de test_c06/test_c09)"
      pattern: "from \"\\.\\./src/finance\\.js\""
---

<objective>
Corrigir a violação da ADR-017 Decisão 1 no front: `web/src/App.jsx` consome
`setups[0]` cru em dois pontos, sem filtrar setup aposentado, enquanto o
backend já filtra (`server/app/setups.py:718-725`, `plano_do_resultado`:
`operaveis = [s for s in setups_list if not s.get("aposentado")]`).

Consequência real, verificada ao vivo em staging (2026-09-07): a compra de
ABEV3 gravou `setupEntrada` internamente contraditório — `setup`/`veredito`
de BAIXA (PFR, vindo de `sc.melhorSetup`/`sc.veredito`, fonte JÁ filtrada
pelo backend) misturados com `lado`/`gatilho`/`invalidacao` do Setup 9.2,
APOSENTADO e de ALTA (vindos de `setups[0]`, cru). Com `se.lado` errado, a
avaliação em `App.jsx:4571-4572`
(`const inval = se.lado === "baixa" ? cur > se.invalidacao : cur < se.invalidacao;`)
INVERTE: o app mostra a tese como válida quando está invalidada, e vice-versa.

Purpose: o contexto de decisão gravado na posição alimenta o histórico de
aprendizado — pilar do produto. Um `setupEntrada` contraditório envenena o
aprendizado do usuário e a régua de acompanhamento exibida.
Output: regra de seleção única e testável no front (espelho da do backend),
aplicada nos dois pontos de consumo, com guardião novo em `web/tests/`.

Severidade: não é cálculo financeiro — saldo, preço médio, PnL e drawdown
seguem corretos, calculados pelo motor determinístico. Contaminado está (a) o
`setupEntrada` gravado e (b) os níveis exibidos na régua.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/STATE.md

Arquivos de trabalho:
@web/src/finance.js
@web/src/App.jsx
@server/app/setups.py

<interfaces>
<!-- Contratos já verificados no código. NÃO explorar de novo. -->

Elemento de `setups[]` (montado em server/app/setups.py:127-218 e marcado em :556):
  { nome: string, lado: "alta"|"baixa"|"neutro", confluencia: number,
    criterios: [{ ok: boolean, obrigatorio?: boolean, ... }],
    gatilho?: number, invalidacao?: number, alvoSugerido?: number,
    aposentado: boolean, historico?: object|null }

Payload do scan (server/app/main.py:1615):
  { "melhorSetup": sres.get("melhor"), "setups": sres.get("setups"), ... }
  — `melhorSetup` é o NOME (`melhor["nome"]`) do melhor setup OPERÁVEL,
    preferindo direcional (setups.py:567-581). `setups` é a lista COMPLETA
    ordenada por confluência, aposentados incluídos (educacional).

Regra do backend a espelhar (server/app/setups.py:725):
  operaveis = [s for s in setups_list if not s.get("aposentado")]

Sanitização no servidor (server/app/store.py:621-637, `_sanitize_trade_meta`):
  strings aceitas em ("setup","lado","veredito","snapshotId"); números em
  ("gatilho","invalidacao","confluencia"). Chave ausente é simplesmente
  omitida — não quebra o payload salvo.

finance.js já hospeda lógica ADR-017 pura (`historicoEstado(historico,
aposentado)`, linha ~373) e é importado por App.jsx (linha 15) e por
guardiões (`test_c06`, `test_c09`) — é a casa correta dos novos helpers,
sem criar módulo novo.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Regra de setup operável em finance.js e os dois pontos de consumo em App.jsx</name>
  <files>web/src/finance.js, web/src/App.jsx</files>
  <behavior>
    setupOperavel(setups, melhorSetupNome):
    - lista `[aposentado(alta), aposentado(baixa), operável(baixa)]` + nome do
      operável → devolve o elemento OPERÁVEL (casamento por nome).
    - nome ausente/não encontrado → primeiro elemento com `!aposentado`
      (fallback por ordem, mesma regra de setups.py:725).
    - todos aposentados, ou lista vazia/ausente/não-array → `null`.
    - nunca devolve elemento com `aposentado: true`.

    metaDeEntrada(sc):
    - com setup operável: `{ setup, veredito, confluencia, snapshotId, lado,
      gatilho, invalidacao }` — `setup` e `lado` vindos do MESMO elemento.
    - sem setup operável: as chaves `lado`/`gatilho`/`invalidacao` NÃO existem
      no objeto (`"lado" in meta === false`), nem como `null` nem como `0`.
  </behavior>
  <action>
Em `web/src/finance.js`, ao final do arquivo (perto de `historicoEstado`, que já
é lógica ADR-017), adicionar DUAS funções puras exportadas — exportadas porque o
guardião da Task 2 precisa exercitá-las de verdade; não criar módulo novo:

1. `setupOperavel(setups, melhorSetupNome)`: filtra `!s.aposentado`; se
   `melhorSetupNome` for string não-vazia, procura entre os operáveis o de
   `nome` idêntico e o devolve; senão devolve o primeiro operável; sem nenhum
   operável (ou entrada não-array) devolve `null`. Guardas defensivas contra
   elemento nulo. Comentário curto citando ADR-017 Decisão 1 e o espelho em
   `server/app/setups.py:725`, e explicando POR QUE o casamento por nome vem
   primeiro: `melhorSetup` é a fonte já filtrada pelo backend, então casar por
   nome garante por construção (não por coincidência de índice) que `setup`,
   `veredito` e `lado`/`gatilho`/`invalidacao` descrevam o MESMO setup.

2. `metaDeEntrada(sc)`: monta o meta de compra a partir do scan. Campos fixos
   `setup`/`veredito`/`confluencia`/`snapshotId` como hoje, com
   `setup: (op && op.nome) || sc.melhorSetup || undefined`; os campos do setup
   entram por SPREAD CONDICIONAL — `...(op ? { lado: op.lado, gatilho:
   op.gatilho, invalidacao: op.invalidacao } : {})` — para que fiquem
   literalmente AUSENTES quando não há operável (princípio 4 do CLAUDE.md:
   nunca inventar dado; `_sanitize_trade_meta` já omite chave ausente sem
   quebrar). Não usar `0` nem valor do aposentado como stand-in.

Em `web/src/App.jsx`:

3. Adicionar `setupOperavel` e `metaDeEntrada` ao import já existente de
   `./finance.js` (linha 15).

4. Linha ~3911-3917 (grade da watchlist): remover a variável `melhorSet =
   sc && (sc.setups || [])[0]` (ela só é usada nessas 3 linhas — verificado) e
   trocar o corpo por `const buyMeta = sc ? metaDeEntrada(sc) : undefined;`.
   PRESERVAR a forma ternária `sc ? … : undefined` — `test_watchlist_anvencida_guard.mjs`
   documenta esse curto-circuito de `sc` como padrão da função.

5. Linha ~6955 (card do Radar): trocar `const s0 = (r.setups || [])[0];` por
   `const s0 = setupOperavel(r.setups, r.melhorSetup);`. Isso corrige de uma vez
   os três consumidores de `s0`: `critTot`/`critOk` (~L6972-6973, os "critérios"
   exibidos ao lado de `r.melhorSetup` — hoje podem ser de outro setup) e a régua
   `PlanRuler` (~L7053-7062). A régua já é guardada por
   `s0 && s0.gatilho != null && s0.invalidacao != null && s0.alvoSugerido != null`,
   então `s0 === null` faz ela simplesmente não renderizar — estado vazio já
   coerente, NÃO criar componente novo de estado vazio nem mexer no layout ao
   redor. `critTot > 0 ?` idem: já degrada sozinho.

NÃO FAZER (limites do achado):
- Não tocar `server/app/setups.py` — o backend está correto.
- Não filtrar/reordenar `r.setups` globalmente. As linhas 7083 e 7091 de
  App.jsx (lista de estudo do Radar, com `HistoricoPill` e o comentário que
  cita ADR-017 em ~L7096) DEVEM continuar recebendo o array cru, com
  aposentados: "aposentado ≠ apagado".
- Não mexer em `web/src/persistence.js` (nenhum store ganha campo novo —
  paridade `deviceStore`/`serverStore` não é afetada), nem em
  `server/web_dist`.
  </action>
  <verify>
    <automated>node --input-type=module -e "import('./web/src/finance.js').then(({setupOperavel,metaDeEntrada})=>{const sc={melhorSetup:'PFR',veredito:'Estudar baixa',confluencia:70,snapshotId:'x',setups:[{nome:'Setup 9.2',lado:'alta',aposentado:true,gatilho:1,invalidacao:2},{nome:'PFR',lado:'baixa',aposentado:false,gatilho:10,invalidacao:12}]};const m=metaDeEntrada(sc);if(m.lado!=='baixa'||m.setup!=='PFR')throw new Error('meta contraditoria: '+JSON.stringify(m));const vazio=metaDeEntrada({melhorSetup:null,setups:[{nome:'Setup 9.2',lado:'alta',aposentado:true,gatilho:1,invalidacao:2}]});if('lado' in vazio||'gatilho' in vazio||'invalidacao' in vazio)throw new Error('aposentado usado como stand-in: '+JSON.stringify(vazio));if(setupOperavel([{nome:'A',aposentado:true}],null)!==null)throw new Error('devolveu aposentado');console.log('ok');})"</automated>
  </verify>
  <done>`setupOperavel` e `metaDeEntrada` exportados de finance.js; App.jsx sem nenhuma ocorrência de `(sc.setups || [])[0]` ou `(r.setups || [])[0]`; lista de estudo (L7083/7091) intocada; comando de verificação imprime `ok`.</done>
</task>

<task type="auto">
  <name>Task 2: Guardião test_setup_operavel_adr017.mjs cobrindo o caso real do achado</name>
  <files>web/tests/test_setup_operavel_adr017.mjs</files>
  <action>
Criar `web/tests/test_setup_operavel_adr017.mjs` no formato híbrido já usado no
repo (`test_c09_drawdown_alerta.mjs`: unidade importando `../src/finance.js` +
grep estático de `App.jsx`), com o mesmo contador `fails` / helper `ok()` e
`process.exit(fails ? 1 : 0)` ao final. Cabeçalho com comentário explicando o
achado (ABEV3, 2026-09-07) e a regra da ADR-017 Decisão 1.

Parte (a) — unidade de `setupOperavel`/`metaDeEntrada`, reproduzindo o caso real:
- Fixture do achado: `[{nome:"Setup 9.2", lado:"alta", aposentado:true,
  gatilho:…, invalidacao:…}, {nome:"Rompimento (baixa)", lado:"baixa",
  aposentado:true, …}, {nome:"PFR", lado:"baixa", aposentado:false,
  gatilho:…, invalidacao:…}]` com `melhorSetup:"PFR"`, `veredito:"Estudar baixa"`.
  Asserções: `metaDeEntrada(sc).lado === "baixa"`; `meta.setup === "PFR"`;
  `meta.gatilho`/`meta.invalidacao` iguais aos do elemento PFR (mesmo elemento,
  não coincidência de índice); nenhum valor do Setup 9.2 vazando.
- Fallback sem nome: `setupOperavel(lista, null)` devolve o primeiro `!aposentado`.
- Nome que não casa: cai no primeiro operável, não em `setups[0]`.
- Todos aposentados: `setupOperavel(...) === null` E
  `!("lado" in meta) && !("gatilho" in meta) && !("invalidacao" in meta)` —
  aposentado NÃO usado como fallback silencioso, e nada de `0`.
- Entradas degeneradas: `undefined`, `[]`, elemento `null` na lista → `null`,
  sem lançar.
- Anti-regressão do bug de inversão: replicar a expressão de `App.jsx:4571`
  (`se.lado === "baixa" ? cur > se.invalidacao : cur < se.invalidacao`) sobre o
  meta produzido e afirmar que, com preço abaixo da invalidação do PFR (setup de
  baixa), a tese resulta VÁLIDA — era o resultado invertido antes da correção.

Parte (b) — grep estático de `web/src/App.jsx` (fonte lida com `readFileSync`,
mesmo boilerplate de path do `test_c09`):
- `App.jsx` NÃO contém mais `(sc.setups || [])[0]` nem `(r.setups || [])[0]`
  (regex literal escapada).
- `App.jsx` contém `metaDeEntrada(sc)` e `setupOperavel(r.setups, r.melhorSetup)`.
- Ambos importados de `./finance.js` (checar a linha de import).
- A lista de estudo segue crua: `App.jsx` ainda contém `(r.setups || []).map(`
  — guardião de que a correção NÃO virou filtro global (aposentado ≠ apagado).

Higiene de grep: ao contar ocorrências, filtrar linhas de comentário
(`.split("\n").filter((l) => !l.trim().startsWith("//"))`) antes de contar, para
que o próprio comentário explicativo não valide/invalide a asserção.
  </action>
  <verify>
    <automated>node web/tests/test_setup_operavel_adr017.mjs</automated>
  </verify>
  <done>Guardião roda sem build, sai com código 0, e cobre os dois casos exigidos (operável escolhido entre aposentados; nenhum operável → campos ausentes). Reverter a Task 1 faz o guardião falhar.</done>
</task>

<task type="auto">
  <name>Task 3: Suíte canônica + vite build</name>
  <files>(nenhum — validação)</files>
  <action>
Rodar a validação obrigatória do CLAUDE.md, nesta ordem:

1. `bash scripts/executar.sh --testes` — suíte canônica, as DUAS suítes (pytest
   do backend + `web/tests/*.mjs`). `scripts/test.sh` sozinho é meia baseline e
   NÃO conta. Confirmar que o novo guardião aparece na saída da suíte web e que
   nenhum guardião existente regrediu — em especial
   `test_watchlist_anvencida_guard.mjs`, `test_fase2_portfolio.mjs`,
   `test_snapshotid_debug_only.mjs` e `test_opcoes_proposta_ui.mjs`, que tocam a
   região editada.
2. `(cd web && npx vite build)` — obrigatório porque `web/src/App.jsx` foi
   editado; grep e teste estático não pegam erro de sintaxe JS.

Se algo falhar, corrigir e repetir os DOIS comandos, não só o que falhou.

NÃO executar `scripts/bump.sh` nem `scripts/publicar-web.sh` — publicação é
passo manual, decisão do Alex.
  </action>
  <verify>
    <automated>bash scripts/executar.sh --testes && (cd web && npx vite build)</automated>
  </verify>
  <done>Suíte canônica verde (pytest + web/tests, incluindo o guardião novo) e `vite build` concluído sem erro.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| front (App.jsx) → `store.buy(meta)` → `_sanitize_trade_meta` | meta de entrada montado no cliente atravessa para persistência; o servidor já valida tipo e whitelist de chaves (`store.py:621-637`) |
| motor determinístico (setups.py) → UI | níveis exibidos como acionáveis não podem divergir do plano operável do backend |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-vzp-01 | Tampering (integridade de dado, não adversarial) | `buyMeta` em App.jsx ~L3911 | mitigate | `metaDeEntrada()` monta setup/lado/gatilho/invalidação de um único elemento; guardião de unidade trava a coerência |
| T-vzp-02 | Information disclosure (dado enganoso ao usuário) | régua `PlanRuler` do Radar ~L7053 | mitigate | `setupOperavel()` devolve `null` sem operável; guarda existente impede render de níveis aposentados |
| T-vzp-03 | Spoofing de dado ausente (`0` como stand-in) | meta sem setup operável | mitigate | spread condicional → chaves ausentes; `_sanitize_trade_meta` omite sem quebrar (princípio 4 do CLAUDE.md) |
| T-vzp-SC | Tampering | supply chain | accept | nenhum pacote novo instalado (npm/pip/cargo) neste plano |
</threat_model>

<verification>
- `grep -n "setups || \[\])\[0\]" web/src/App.jsx` → zero linhas.
- `grep -n "(r.setups || \[\]).map(" web/src/App.jsx` → segue existindo (lista de estudo com aposentados, ADR-017).
- `git diff --stat` toca só `web/src/finance.js`, `web/src/App.jsx` e o teste novo. Nada em `server/`, `web/dist`, `server/web_dist`.
- `bash scripts/executar.sh --testes` verde; `npx vite build` em `web/` verde.
</verification>

<success_criteria>
- Compra a partir de um ativo cujo `setups[0]` é aposentado grava `setupEntrada`
  com `setup`, `lado`, `gatilho` e `invalidacao` do MESMO setup operável.
- Sem setup operável, o meta não carrega `lado`/`gatilho`/`invalidacao` (chaves
  ausentes), e a régua do Radar não renderiza níveis.
- Lista de setups do Radar continua exibindo aposentados com a pílula de
  histórico (ADR-017 Decisão 1 preservada nos dois sentidos).
- Guardião novo em `web/tests/` falha se a correção for revertida.
- Suíte canônica (pytest + web) verde e `vite build` ok.
</success_criteria>

<output>
Create `.planning/quick/260907-vzp-corrigir-setups-0-cru-sem-filtrar-aposen/260907-vzp-SUMMARY.md` when done.

No SUMMARY, registrar obrigatoriamente como limitação conhecida: o código está
pronto mas NÃO publicado — como o plano toca `web/src/`, ir ao ar exige
`scripts/bump.sh` seguido de `scripts/publicar-web.sh`, passo manual que o Alex
decide quando executar. `server/web_dist` é artefato versionado e não deve ser
editado diretamente.
</output>
