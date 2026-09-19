---
phase: 25-planos-comerciais
plan: 06
subsystem: ui
tags: [plano-comercial, adr-010, ux-researcher, copy-por-modo, guardioes, watchlist, 402-estruturado]

requires:
  - phase: 25-planos-comerciais
    provides: "25-04 — `/api/ai/quota` e `/api/watchlist/quota` publicando o limite EFETIVO do plano (sem isso a tela mostraria um teto e o gate aplicaria outro)"
  - phase: 25-planos-comerciais
    provides: "25-02/25-03 — `users.plan` no `_public_user` de `/api/auth/me` e o catálogo que resolve os limites"
  - phase: aba-opcoes-F2
    provides: "`api.js` anexando `err.code`/`err.detail` a partir do corpo de erro — infraestrutura pronta e, até aqui, sem nenhum consumidor"
provides:
  - "`main.COD_WATCHLIST` + `main._recusa_de_watchlist`: o 402 estruturado das duas rotas de watchlist"
  - "`plan.COD_LIMITE_WATCHLIST`, `plan.erroDeLimiteWatchlist`, `plan.limiteDeWatchlist`: a MESMA forma de recusa para o 402 do servidor e para o gate local do iOS"
  - "`App.LimiteAtingido`: banner compartilhado de limite (T.warn, inline, só com código reconhecido)"
  - "`App.PlanoScreen` + `App.PlanoLinha`: a sub-tela de Perfil que compõe plano + as duas cotas"
  - "9 chaves `plano*` em `copy.js`, texto idêntico nos dois modos"
  - "web/tests/test_plano_ui.mjs — 90 asserções, 7 defeitos injetados"
affects: [publicacao-conjunta-25-01-a-25-06]

tech-stack:
  added: []
  patterns:
    - "Recusa de plano com a MESMA forma vindo de dois caminhos (402 do servidor no web, gate local no iOS) — um leitor único (`limiteDeWatchlist`) em vez de dois tratamentos"
    - "Guardião que compara uma constante ENTRE ARQUIVOS de linguagens diferentes (`main.py` × `plan.js`): o código do erro é contrato publicado e nada mais amarra as duas pontas"
    - "Paridade de CONTEÚDO (não só de chave) entre os dois ramos de `copy.js`, para o caso em que o texto deve ser idêntico por decisão"

key-files:
  created:
    - web/tests/test_plano_ui.mjs
  modified:
    - server/app/main.py
    - server/tests/test_fase12_cap_watchlist.py
    - web/src/App.jsx
    - web/src/copy.js
    - web/src/plan.js
    - web/src/persistence.js
    - web/tests/test_fase13_contadores_ui.mjs

key-decisions:
  - "`usado` tem o MESMO significado nas duas rotas (o tamanho de HOJE), e não `len(final)` no PUT como o plano sugeria: o campo é lido por um componente compartilhado e um sentido por rota daria número certo numa tela e errado na outra"
  - "O `detail` do 402 de watchlist virou dict, mas o de `_gate_analise` continua STRING — a fronteira ficou travada por caso de teste, porque 'uniformizar' faria a tela mostrar `[object Object]` (decisão registrada no 25-04)"
  - "Sem mapa id → nome de exibição do plano: o app já mostra o id cru ao usuário ('do plano free') e duas vozes divergiriam; um mapa no front também seria uma segunda lista de planos, velha no dia em que existir um terceiro"
  - "`canGrowWatchlistTo` NÃO devolve `usado`: ela só recebe o tamanho PEDIDO, e publicar isso num campo que significa 'quantos você tem' seria número com outro sentido no mesmo lugar"
  - "`persistence.js` entrou no diff (fora dos `files_modified`): no iPhone o gate de watchlist é client-side e autoritativo, então sem a recusa estruturada lá o banner seria código morto exatamente onde ele é a única defesa"
  - "Tile no grupo Conta, nunca badge global — a razão é custo cognitivo pago em TODA tela por um dado quase nunca consultado, não estética"

patterns-established:
  - "Contador de usos de um componente compartilhado (`<QuotaSeg` = 4) atualizado com nota datada E endurecido: o uso novo tem de morar dentro de um componente nomeado, senão um uso solto passaria pelo contador"

requirements-completed: ["Fase 5 do 25-CONTEXT — plano visível no app"]

duration: 16min
completed: 2026-09-12
---

# Phase 25 Plan 06: Plano visível no app — Summary

**O app passou a ler `authUser.plan`: um tile no grupo Conta do Perfil abre uma
tela que diz o que o plano libera (com os números vindos das mesmas rotas que o
gate aplica), e a recusa por limite de watchlist chega estruturada — código e
número — para virar um aviso em `T.warn` no ponto da tentativa, em vez da frase
crua que o backend nunca escreveu para ser lida por um usuário.**

## Performance

- **Duração:** ~16 min
- **Tasks:** 3 de 3
- **Arquivos:** 6 modificados, 1 criado

## Task Commits

1. **Task 1: os dois gates de watchlist com 402 estruturado** — `0722100` (feat)
2. **Task 2: banner compartilhado, tile e PlanoScreen** — `ff63344` (feat)
3. **Task 3: o guardião** — `ad4f227` (test)

## O que mudou, e por quê

### 1. O 402 de watchlist parou de ser só uma frase

`PUT /api/watchlist` e `POST /api/watchlist/add` são as **duas únicas** rotas
que devolvem 402 **cru** ao cliente — o gate de análise tem o 402 capturado e
convertido em 200 com fallback determinístico antes de chegar ao front
(FIX-C01). O `detail` delas virou dict:

```json
{"code": "watchlist_limite", "message": "<a frase de plan.py, verbatim>", "limite": 10, "usado": 10}
```

Três coisas fazem isso ser uma mudança de forma e não de conteúdo:

- `message` é a frase de `plan.can_grow_watchlist_to`/`can_add_ticker` **byte a
  byte** — há caso comparando contra a **fonte** (`main.plan.can_grow_watchlist_to`),
  não contra um literal copiado para o teste, que divergiria em silêncio;
- `enrichErrorMessage` (`web/src/api.js`) já usa `d.message` como base quando o
  detail é objeto, então `e.message` no cliente continua idêntico;
- os dois guardiões da Fase 12 que liam `detail` como string foram
  **atualizados com nota datada**, não apagados.

**`usado` significa a mesma coisa nas duas rotas** — quantos ativos a conta tem
HOJE, antes da tentativa. O plano sugeria `len(final)` (o tamanho **pedido**) no
PUT; isso foi recusado deliberadamente: o campo é lido por um componente
compartilhado, e um sentido por rota daria número certo numa tela e errado na
outra. Conta grandfathered devolve `usado: 15, limite: 10` — truncar `usado` no
teto fabricaria número (princípio 4) e esconderia justamente o caso em que os
dois divergem.

**A fronteira ficou travada por teste:** o 402 de `_gate_analise` **continua
string**. O 25-04 registrou por escrito por quê (o app lê aquele texto direto;
um dict viraria `[object Object]`), e sem a asserção a próxima pessoa
"uniformiza" os dois.

### 2. Onde o plano aparece (e onde não aparece)

A decisão de lugar veio do subagente **UX Researcher**, por instrução do CONTEXT
aprovado, e está implementada como ele recomendou:

| Decisão | Onde | Por quê |
|---|---|---|
| Tile "Plano" | grupo **Conta** do `PerfilHub`, logo abaixo do login | é estado de conta; ao lado de quem você é |
| **Não** em "IA e desempenho" | — | lá o eixo é modelo/BYOK/custo, ortogonal ao entitlement |
| **Não** em "Atividade da IA" | — | aquela tela é sobre custo/histórico, não sobre o que se pode |
| **Não** badge global | — | plano muda raríssimo (hoje só por atribuição manual da administração): um badge permanente cobra carga cognitiva em TODA tela pela estética de freemium agressivo que o ADR-010 (decisão 4) proíbe |

`PlanoScreen` compõe `authUser.plan` (já vem de `/api/auth/me`, sem chamada
nova) + `store.aiQuota()` + `store.watchlistQuota()`. As duas rotas de cota
publicam o limite **efetivo** desde o 25-04 — é por isso que a tela não pode
divergir do que barra.

`PlanoLinha` herda a semântica de 3 estados do `QuotaSeg` **um nível acima**:
`undefined` (carregando) omite a linha inteira, sem flash de travessão; `null`
(falhou) diz o **motivo** em vez de mostrar número estimado; `limit == null`
(plano sem teto) **omite**, porque o app nunca escreve a palavra que significa
"sem teto" nem "X/∞" (D-03 da Fase 13). E ela **não reimplementa a lógica de
cor** — o número continua saindo do próprio `QuotaSeg`.

**Consequência assumida do D-03:** numa conta cujos dois limites sejam `null`,
a tela mostra o nome do plano e a descrição, e nenhuma linha de número. É o
preço de não escrever "ilimitado"/"∞", que é regra da casa desde a Fase 13.

### 3. O aviso de limite

`LimiteAtingido` extrai a caixa `T.warn` que já estava repetida inline em quatro
pontos do `App.jsx`. Ele carrega três decisões:

- **cor:** `T.warn`, nunca `T.negative` — vermelho é reservado a P&L (mesma
  razão do `QuotaSeg`); usá-lo aqui faria "bati o teto" parecer prejuízo. Bater
  o limite é estado **esperado**, não catástrofe;
- **lugar:** inline, no ponto da tentativa. Nunca `flash()` (2,6 s, curto demais
  para algo que a pessoa precisa entender) e nunca modal bloqueante. São **dois
  pontos de montagem no mesmo modal** — o campo de adicionar ticker e o botão de
  salvar em massa — com um estado cada, porque são tentativas diferentes e o
  aviso tem de aparecer onde a pessoa tocou;
- **gatilho:** só com `code` reconhecido. Erro técnico (provedor fora do ar,
  rede) e recusa de plano são categorias diferentes (princípio 4) e não podem
  cair no mesmo aviso — o erro técnico **continua** indo para a linha vermelha /
  o toast de sempre, e há asserção posicional disso.

O texto vem de `copy.js`. A `reason` do backend é ASCII sem acento, convenção de
log Python, e nunca aparece verbatim no banner.

### 4. As duas pontas da mesma recusa

No **web** a recusa vem do 402; no **iPhone** ela vem do gate local, que é
client-side e **autoritativo** (CR-01 da Fase 13 — o aparelho é a fonte da
verdade e não existe gate de watchlist no servidor para ele). Sem tratar os
dois, o banner seria código morto exatamente na plataforma onde ele é a única
defesa.

A saída foi dar ao gate local a **mesma forma** do 402 (`erroDeLimiteWatchlist`)
e ter **um leitor só** (`limiteDeWatchlist`), em vez de dois tratamentos na
tela. O guardião prova isso por comportamento, não por regex: o erro do gate
local é lido pelo mesmo leitor do 402, com o mesmo resultado.

## Verificação

`bash scripts/executar.sh --testes`, **fora do sandbox**, `exit 0`:

```
2682 passed, 5 skipped, 3 xfailed, 921 warnings in 64.84s
134 arquivos web/tests/*.mjs [OK]
```

Baseline: `2676 passed, 5 skipped, 3 xfailed` + 133 `.mjs`. **+6 são exatamente
os casos novos de backend** e **+1 `.mjs` é exatamente o guardião novo**;
skipped e xfailed inalterados.

`cd web && npx vite build` — verde.

Recortes:

- Task 1 — `tests/test_fase12_cap_watchlist.py tests/test_fase3_gate_plano.py`:
  37 passed. Recorte largo `-k "watchlist or plan or plano or quota or multiuser"`:
  236 passed.
- Task 2 — guardiões de front rodados um a um antes da suíte cheia
  (`test_copy_theme`, `test_wiring_deps`, `test_fase5_gate_mensal_front`,
  `test_fase13_watchlist_quota_ios`, `test_api_parity`,
  `test_fase3_paridade_stores_generica`): todos OK.

### Não-vacuidade do guardião novo, medida

`test_plano_ui.mjs` nasceu **depois** do código (é a ordem das tasks do plano),
então RED natural não existia. A prova foi por **injeção de defeito**, um a um,
com reversão por `git checkout --` de arquivo específico:

| defeito injetado | reprovou? |
|---|---|
| `T.warn` → `T.negative` dentro de `LimiteAtingido` | 1 falha |
| texto do ramo `operador` divergindo do `estudo` | 1 falha |
| CTA de upgrade numa chave de copy | 2 falhas |
| terceira leitura de `authUser.plan` (badge global) | 1 falha |
| código do 402 divergindo entre `main.py` e `plan.js` | 1 falha |
| recusa de limite caindo no `flash` | 1 falha |
| tabela comparativa dentro da `PlanoScreen` | 1 falha |

Depois de cada reversão, verde de novo. Cada regex de defeito tem asserção de
sanidade ao lado (o padrão casa quando o defeito existe), pelo mesmo motivo:
regex com typo faz o assert "o defeito não existe" passar sempre.

## Deviations from Plan

### 1. [Rule 2 — funcionalidade crítica ausente] `web/src/persistence.js` entrou no diff

- **Encontrado em:** Task 2
- **Situação:** os `files_modified` do plano não incluem `persistence.js`. Mas
  no iOS a recusa de watchlist **nunca** passa por um 402: o gate é local e
  autoritativo. Os dois pontos do `deviceStore` levantavam `new Error(r.reason)`
  — sem `code`, o banner compartilhado nunca renderizaria no iPhone.
- **Correção:** as duas linhas passam a levantar `erroDeLimiteWatchlist(...)`.
  Paridade preservada (o `serverStore` já recebe o `code` pelo `api.js`), e os
  guardiões de fail-closed da Fase 13 seguem verdes — nenhum `catch` de falha de
  rede foi tocado.
- **Commit:** `ff63344`

### 2. [Rule 3 — bloqueio] `copy.js` foi para o commit da Task 2, não da Task 3

- **Encontrado em:** Task 2
- **Situação:** o plano põe `App.jsx` na Task 2 e `copy.js` na Task 3. Commitar
  nessa ordem produziria um commit intermediário em que a tela renderiza
  `undefined` (as chaves ainda não existem) — commit atômico deveria significar
  estado funcionante.
- **Correção:** `copy.js` entrou no commit da Task 2; a Task 3 ficou só com o
  guardião, que é o entregável dela.

### 3. [Rule 3 — bloqueio] `web/tests/test_fase13_contadores_ui.mjs` atualizado

- **Encontrado em:** Task 2
- **Situação:** o guardião cravava `<QuotaSeg` em **exatamente 3 usos**. A
  `PlanoScreen` é o 4º ponto de exibição, e o teste reprovou.
- **Correção:** nota datada explicando que o número subiu porque **nasceu um
  consumidor**, não porque alguém duplicou lógica — e o guardião ficou **mais
  forte**, não mais fraco: três asserções novas exigem que o 4º uso more
  **dentro** de `PlanoLinha` e que `PlanoLinha` não tenha cor própria. Sem isso,
  um 4º uso solto em qualquer tela passaria pelo contador.
- **Commit:** `ff63344`

### 4. [Registro] `usado` com semântica uniforme, contra a letra do plano

O plano dizia "`usado` é `len(final)` na rota PUT". Foi implementado como
`len(atual)` nas duas (o tamanho de hoje). Razão no corpo deste SUMMARY e no
comentário de `_recusa_de_watchlist`. A latitude estava no próprio plano ("use o
que a rota já calcula"), mas a escolha é deliberada e merece registro.

### 5. [Registro] Uma chave de copy a mais que a lista do plano

`planoLimiteIndisponivel` não estava na lista de chaves do plano. Ela cobre o
estado `quota === null` (a busca do limite falhou): sem ela, a linha ficaria com
um travessão órfão ou um número estimado — os dois proibidos pelo princípio 4.
As outras 8 são exatamente as pedidas, e **nenhuma** de CTA.

---

**Total:** 3 desvios (1× Rule 2, 2× Rule 3) + 2 registros. Nenhum desvio de
escopo — os três acréscimos são consequência direta do que o plano cobra.

## O que este plano deliberadamente NÃO fez

- **Nada foi publicado.** Nenhum push, nenhum PR, nenhum `bump.sh`,
  `publicar-web.sh` ou `publicar-admin.sh`. `server/web_dist`,
  `server/admin_dist`, `web/src/version.js` e `SERVER_BUILD_ID` **não foram
  tocados** — a publicação é a próxima etapa e leva as CINCO fases juntas
  (25-01 a 25-06), com deploy de backend **antes** do front (o front novo lê um
  `detail` que só o backend novo produz; contra o backend velho o banner
  simplesmente não aparece, e a frase de sempre continua na linha de erro —
  degradação, não quebra).
- **Nada foi exercitado ao vivo nem no aparelho.** A verificação foi estática
  (suíte + build). O banner no iPhone depende do caminho `deviceStore`, que
  nenhum teste automatizado executa contra um aparelho real.
- **Os mutadores de estado do `gsd-sdk` não foram chamados** (decisão do Alex):
  `STATE.md` foi atualizado à mão.
- **`plan.py` não foi tocado.** Nenhum limite mudou de valor; a frase de recusa
  é a mesma.
- **A decisão aberta do 25-01 continua aberta** (ativação do gate mensal em
  `/api/scan/deep`, `/api/carteira-stopalvo` e `/api/assistente`). Nada aqui a
  aproximou nem a afastou.
- **D2 (`opcoes.criar_setup` do RBAC para o plano) segue pendente**, como o
  25-04 e o 25-05 registraram.

## Known Stubs

Nenhum. Os dois números da `PlanoScreen` vêm de rotas reais; o estado de falha
mostra travessão + motivo, e não placeholder.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: contrato | server/app/main.py | `detail` das duas rotas de watchlist deixou de ser `str` e virou `dict`. É mudança de contrato de API pública. Mitigação: `message` carrega a frase de antes e `enrichErrorMessage` já a usa como base, então cliente antigo continua exibindo o mesmo texto; os dois guardiões que liam a string foram atualizados. Nenhuma rota nova, nenhuma mudança de autenticação, nenhum limite alterado. |

## Next Phase Readiness

A fase 25 fica **completa em código** (Fases 0 a 5 do `25-CONTEXT.md`). O que
falta é a **publicação conjunta**, nesta ordem:

1. deploy do backend com **bump manual de `SERVER_BUILD_ID`** (25-01, 25-02,
   25-03, 25-04, 25-05 e a Task 1 desta fase são todas backend);
2. `bump.sh` + `publicar-web.sh` (o front desta fase);
3. `publicar-admin.sh` (o portal do 25-05).

Publicar o front **antes** do backend não quebra: o banner só não aparece, e a
frase de recusa continua na linha de erro. Publicar o **portal** antes do
backend, sim — ele chama `/api/admin/planos`, que não existe no servidor velho.

## Self-Check: PASSED

- `server/app/main.py` — FOUND
- `server/tests/test_fase12_cap_watchlist.py` — FOUND
- `web/src/App.jsx` — FOUND
- `web/src/copy.js` — FOUND
- `web/src/plan.js` — FOUND
- `web/src/persistence.js` — FOUND
- `web/tests/test_fase13_contadores_ui.mjs` — FOUND
- `web/tests/test_plano_ui.mjs` — FOUND
- commit `0722100` — FOUND
- commit `ff63344` — FOUND
- commit `ad4f227` — FOUND
- `git diff --diff-filter=D HEAD~3 HEAD` — **nenhuma** deleção de arquivo
- índice conferido com `git diff --cached --stat` antes de cada commit; os 4
  diretórios não rastreados em `.claude/skills/` seguem intocados

---
*Phase: 25-planos-comerciais*
*Completed: 2026-09-12*
