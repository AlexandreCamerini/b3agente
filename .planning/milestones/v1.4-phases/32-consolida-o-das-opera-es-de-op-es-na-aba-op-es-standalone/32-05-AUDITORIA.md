# Fase 32 Plano 05 — Task 1: Auditoria de não-regressão

**Escopo:** só a Task 1 do `32-05-PLAN.md` (auditoria de evidência, sem editar
código de produção). A Task 2 (`checkpoint:human-verify`, gate bloqueante) e a
Task 3 (bump/publicação/push) NÃO foram executadas — ficam retidas atrás da
aprovação do Alex.

**Executado em:** 2026-09-16, branch `v2/interacao-estrutural`, working tree
`/Users/acamerini/dev/borisv2` (sem alterações de código de produção; único
artefato desta task é este próprio arquivo).

---

## 1. `git diff --name-only` do range que cobre a fase

**Aviso ao orquestrador/Alex, antes do veredito:** este item tem uma decisão
de julgamento que o PLAN.md manda ESCALAR ("Se listar, é ACHADO: parar e
reportar"), não resolver por conta própria. Reporto os dois resultados por
completo abaixo, com o raciocínio de por que considero `bd459f1..HEAD` o
range certo para julgar ESTA fase — mas essa é minha leitura, não um fato
que eu possa fechar sozinho. Se o Alex (ou quem revisar isto) discordar do
range, o veredito de "LIMPO" do item 1 muda.

### 1a. Resultado bruto: `main...HEAD` (o range literal do texto do plano) LISTA os arquivos proibidos

```
$ git diff --name-only main...HEAD
```

Devolve, entre ~90 arquivos, exatamente os que o plano proíbe:
`web/src/opcoes/executarCandidato.js`, `web/src/persistence.js`,
`web/src/api.js`, `server/app/main.py`, `server/app/opcoes_curadoria.py`,
`server/app/options_provider_mydata.py`, `server/app/skill_ref.py`, além de
`server/web_dist/**` inteiro e toda a Fase 31.

**Investigação:** `main...HEAD` (three-dot, contra o merge-base) inclui TODO o
histórico não mesclado desta branch de trabalho desde que ela divergiu de
`main` — não só a Fase 32. `git log --oneline --reverse main..HEAD` mostra que
a branch carrega, nesta ordem: a Fase 31 inteira (varredura de oportunidades
de opções, com release `F10-20260914-02/-03`), os dois quicks
`260915-j5l` (correção do clique na lista curada) e `260915-ndt` (rota nova de
re-derivação do collar — que É a cadeia que este plano deve preservar
intocada), e só DEPOIS os commits da Fase 32
(`df34cb6` até `3ea2af2`). `main`/`origin/main` estão atrasados em relação a
todo esse trabalho — nada disso foi publicado ainda (`git rev-parse main` ≠
`origin/main`, e nenhum dos dois bate com `HEAD`).

Ou seja: os arquivos proibidos foram tocados pelos QUICKS, que são
PRÉ-REQUISITO desta fase (o 32-05-PLAN.md lista
`260915-ndt-PLAN.md` como contexto obrigatório de leitura — é o commit que
criou `optionsCuradoriaAbrirCollar`), não pela Fase 32 em si. `main...HEAD`
mistura os dois.

**Isto NÃO é um não-achado automático.** É um fato relevante por si só, com
peso independente do range escolhido: `main`/`origin/main` estão atrasados
de TODA a Fase 31 (publicada em produção via
`F10-20260914-02/-03`... releases, mas aparentemente não mesclada de volta a
`main` nesta branch) e dos dois quicks (`260915-j5l`/`260915-ndt`, também
com releases próprios). A Interface section do 32-05-PLAN.md já avisa que
"`bump.sh` deriva do valor LOCAL: mesclar `origin/main` ANTES de bumpar" —
exatamente porque esse tipo de divergência existe. A Task 3 (retida, não
executada por este agente) tem um passo explícito de merge antes do bump por
esse motivo. Registro aqui para quem for decidir a Task 2/3: o estado de
`main`/`origin/main` precisa ser investigado por quem aprovar a publicação —
não é escopo desta Task 1 resolver, mas é fato que a Task 1 descobriu e não
deve ficar enterrado.

### 1b. Leitura alternativa: `bd459f1..HEAD` (só os commits da Fase 32)

`bd459f1` é `docs(quick-260915-ndt): marca publicado em F10-20260915-02` — o
ÚLTIMO commit antes de `df34cb6 docs(32): registra a Fase 32 e captura o
contexto da discussão`, isto é, o estado do repositório imediatamente antes
da Fase 32 começar. Histórico linear confirmado (`git log --merges
bd459f1..HEAD` = 0 commits de merge).

```
$ git diff --name-only bd459f1..HEAD
```

NÃO lista `web/src/opcoes/executarCandidato.js`, `web/src/persistence.js`,
`web/src/api.js` nem nada sob `server/app/`. Lista só: `web/src/App.jsx`,
`web/src/copy.js`, os 5 módulos de `web/src/opcoes/` que os Planos 32-02/03/04
criaram ou modificaram (`CandidatoOpcao.jsx`, `CuradoriaEstruturas.jsx`,
`OpcoesScreen.jsx`, `OportunidadesOpcoes.jsx`, `useOpcoesPropostas.js`), os 12
guardiões `.mjs` tocados pelos planos anteriores, e artefatos de planejamento
(`.planning/**`). **Critério de aceite do item 1 satisfeito, SE este for o range aceito como
"o range que cobre a fase".**

**Veredito do item 1: LIMPO condicional ao range `bd459f1..HEAD` ser
aceito como o correto para julgar a Fase 32 — decisão que fica sinalizada
para o orquestrador/Alex ratificar, não resolvida unilateralmente por este
agente.** Pelo range literal do texto do plano (`main...HEAD`), o resultado
é ACHADO: lista os 4 arquivos/diretórios proibidos, mais `server/web_dist`
inteiro. A causa raiz não é código da Fase 32 vazando para fora do escopo —
é `main`/`origin/main` estarem muito atrasados nesta branch (Fase 31 + 2
quicks não mesclados de volta). Isso é, em si, um fato que quem for aprovar
a Task 3 (merge + bump + publicação) precisa considerar antes de mesclar
`origin/main`, exatamente pelo motivo que a seção `<interfaces>` do
32-05-PLAN.md já registra.

---

## 2. `executarCandidato.js` (despacho por tipo) e paridade em `persistence.js`

```
$ grep -n 'tipo === "collar"' -A3 web/src/opcoes/executarCandidato.js
77:  if (tipo === "collar") {
```
… resolve para `metodo: "optionsCuradoriaAbrirCollar"` (linha 108). Lido o
arquivo inteiro (136 linhas) — nenhuma linha mudou nesta fase (confirmado
pelo range do item 1b: `executarCandidato.js` não aparece no diff).

```
$ grep -c "optionsCuradoriaAbrirCollar" web/src/opcoes/executarCandidato.js
2
$ grep -c "optionsCuradoriaAbrirCollar" web/src/persistence.js
3
$ grep -n "function deviceStore\|function serverStore\|optionsCuradoriaAbrirCollar" web/src/persistence.js
118:function serverStore() {
330:    optionsCuradoriaAbrirCollar: (body) => api.optionsCuradoriaAbrirCollar(body),
388:function deviceStore() {
1641:    async optionsCuradoriaAbrirCollar(body) {
1644:        const r = await api.optionsCuradoriaAbrirCollar(body);
```

Linha 330 cai dentro de `serverStore()` (abre em 118, fecha antes de 388);
linha 1641 cai dentro de `deviceStore()` (abre em 388). **Paridade
confirmada: o método existe nos DOIS stores** — critério de aceite
(`>= 2` ocorrências) satisfeito com folga (3, porque `deviceStore` tem
definição + 1 chamada interna a `api.optionsCuradoriaAbrirCollar`).

**Veredito do item 2: LIMPO.**

---

## 3. `ctx.A.executarCandidatoCurado` — chamadores de UI

```
$ grep -n "executarCandidatoCurado" web/src/opcoes/OpcoesScreen.jsx
748:      onExecutar={(cand, o) => ctx.A.executarCandidatoCurado(cand, o)}
```
→ 1 chamador, exatamente onde o `32-RESEARCH.md` (seção "Cadeia de execução
do collar curado") previu que a Fase 32 pousaria: `ctx.A` idêntico ao que
`CarteiraScreen` já recebia, só o call site migrou de `App.jsx` para
`OpcoesScreen.jsx`.

```
$ grep -v "^\s*//" web/src/App.jsx | grep -c "A.executarCandidatoCurado"
0
```
Zero chamadores de UI em `App.jsx` (fora de comentário). A DEFINIÇÃO da ação
continua lá (`web/src/App.jsx:8437`, dentro do objeto `ctx.A` — não é um
"chamador", é onde a função é declarada), intocada desde a quick 260915-ndt.

**Veredito do item 3: LIMPO** — bate exatamente com a rota que o
`32-RESEARCH.md` traçou como "a ÚNICA mudança necessária nesta cadeia".

---

## 4. `bash scripts/executar.sh --testes`

Executado com `dangerouslyDisableSandbox: true` (o sandbox padrão do Bash
tool produz falsos-positivos de rede em `ssl.py` — padrão já registrado nos
SUMMARYs 32-01 a 32-04 e em `worktree-test-setup.md`).

```
EXIT_CODE=0
--- backend (pytest) ---
2923 passed, 5 skipped, 3 xfailed, 991 warnings in 71.80s (0:01:11)
--- frontend (.mjs) ---
152/152 [OK], 0 [FAIL]
```

152 arquivos `.mjs` bate com o total no fim do Plano 32-04 (152, "nenhum
arquivo deletado"). 2923/5/3 backend também bate com o número reportado em
todos os SUMMARYs anteriores da fase (32-02/03/04) — nenhuma regressão de
suíte introduzida por nada que tenha acontecido entre o fechamento do 32-04 e
agora (porque nada aconteceu — esta é uma auditoria, sem edição de código).

**Veredito do item 4: LIMPO — exit 0, as duas suítes.**

---

## 5. `npm --prefix web run build`

```
✓ 105 modules transformed.
✓ built in 976ms
PWA v0.21.2 — mode generateSW — precache 23 entries (984.91 KiB)
EXIT=0
```

`git status --short` depois do build: vazio (o build escreve em `web/dist/`,
que é gitignored — nenhum efeito colateral em árvore versionada).

**Veredito do item 5: LIMPO — exit 0.**

---

## 6. Bateria nominal dos 11 guardiões da Task 1

Cada um rodado individualmente com `node web/tests/<arquivo>.mjs`:

| # | Arquivo | Exit | Resultado |
|---|---|---|---|
| 1 | `test_consolidacao_opcoes_copy.mjs` | 0 | todos os testes passaram |
| 2 | `test_opcoes_consolidacao_ui.mjs` | 0 | todos os testes passaram |
| 3 | `test_curadoria_ui.mjs` | 0 | todos os testes passaram |
| 4 | `test_carteira_opcoes_tira.mjs` | 0 | todos os testes passaram |
| 5 | `test_opcoes_multi_candidato_ui.mjs` | 0 | todos os testes passaram |
| 6 | `test_opcoes_subabas_ui.mjs` | 0 | todos os testes passaram |
| 7 | `test_opcoes_proposta_ui.mjs` | 0 | todos os testes passaram |
| 8 | `test_opcoes_collar_ui.mjs` | 0 | todos os testes passaram |
| 9 | `test_opcoes_analisar_ui.mjs` | 0 | todos os testes passaram |
| 10 | `test_vocabulario_opcoes.mjs` | 0 | todos os testes passaram |
| 11 | `test_wiring_deps.mjs` | 0 | "WIRING DE DEPS DO A OK" |

Destaque relevante da bateria nominal (item 5, `test_opcoes_multi_candidato_ui.mjs`):
```
ok (Fase 32/32-04) total de pontos de uso de <PropostaLastreada em
web/src/**/*.jsx é 1 (só OpcoesScreen.jsx — era 2 antes desta fase)
```
Destaque relevante (item 8, `test_opcoes_collar_ui.mjs`):
```
ok deviceStore.optionsCuradoriaAbrirCollar NÃO reimplementa a estrutura sem
sessão (sem chamada a api.optionsChain dentro deste método)
```

**Veredito do item 6: LIMPO — 11/11 guardiões, exit 0, nenhuma reprovação.**

---

## 7. Contagem antes/depois de `ok(` por guardião reescrito em 32-02/03/04

### Metodologia e por que ela mudou a meio caminho

Os SUMMARYs de 32-02/03/04 registram números como "81/81 ok" ou "23/23 ok"
em prosa. Ao tentar reconciliar esses números com a contagem medida agora,
apareceram duas fontes de ruído que precisam ficar explícitas antes da
tabela final, para o veredito não virar falso-positivo de regressão:

1. **Contagem estática (`grep -c "ok("` no arquivo-fonte) ≠ contagem em
   tempo de execução**, para guardiões que têm `ok(...)` dentro de um laço
   (`for (const x of [...])`). Ex.: `test_opcoes_subabas_ui.mjs` tem 1 linha
   `ok(...)` estática dentro de um `for` de 6 itens — 23 ocorrências
   estáticas de `"ok("` no arquivo, mas 28 execuções reais de `ok()` ao
   rodar o script. Os números "23/23" registrados no 32-04-SUMMARY batem
   com a contagem ESTÁTICA, não com a de execução — confirmado comparando
   contra o histórico do arquivo (o laço de 6 itens existe desde a Fase
   28-02, `git log -L`, não foi introduzido por esta fase).
2. Para pelo menos um arquivo (`test_faixa_liquidez_ui.mjs`), o número "13"
   registrado no 32-02-SUMMARY não bate nem com a contagem estática (51,
   confirmada por `git show` em TODOS os commits relevantes da fase, de
   antes da 32-02 até HEAD — sempre 51, nunca mudou) nem com nenhuma leitura
   óbvia do arquivo. Verifiquei explicitamente se existe algum mecanismo de
   subconjunto (flag de CLI, `process.argv`, `describe`/`only`, bloco
   nomeado por seção) que rodasse só 13 das 51 asserções deste arquivo — não
   existe: `grep -n "process.argv\|SECTION\|describe(\|only\b"` no arquivo
   não devolve nada, e `node test_faixa_liquidez_ui.mjs` sempre executa e
   imprime as 51. Não há como reconciliar essa transcrição retroativamente
   com nenhum mecanismo real do arquivo; registro aqui como discrepância de
   PROSA no SUMMARY 32-02 (possível erro de transcrição do executor daquela
   sessão, não algo que eu consiga explicar por diferença de metodologia),
   não como evidência de perda de regra — a evidência direta
   (`git show <commit>:<arquivo> | grep -c "ok("`) mostra 51 em todo ponto
   verificável da fase, sem nenhuma queda.

Por isso a tabela abaixo usa como "antes" o valor **verificado diretamente
via `git show bd459f1:<arquivo>`** — `bd459f1` é o último commit antes da
Fase 32 começar (ver item 1b) — em vez da prosa do SUMMARY. É o único método
auditável e reproduzível por qualquer pessoa que rodar os mesmos comandos.
A prosa dos SUMMARYs é citada ao lado, como referência cruzada.

### Tabela

| Guardião | `ok(` em `bd459f1` (antes da Fase 32) | `ok(` em HEAD (agora) | Δ | Prosa do SUMMARY (referência) |
|---|---:|---:|---:|---|
| `test_curadoria_ui.mjs` | 69 | 82 | **+13** | "75" (32-02) → "81, era 76" (32-03) |
| `test_carteira_opcoes_tira.mjs` | 43 | 47 | **+4** | "50, era 43" (32-03) — ver nota abaixo |
| `test_opcoes_multi_candidato_ui.mjs` | 35 | 44 | **+9** | "34" (32-03) → "44, era 42" (32-04) |
| `test_opcoes_subabas_ui.mjs` | 20 | 23 | **+3** | "23, era 22" (32-04) |
| `test_opcoes_proposta_ui.mjs` | 69 | 70 | **+1** | "70, era 69" (32-04) |
| `test_opcoes_collar_ui.mjs` | 34 | 34 | **0** | "34, igual" (32-04) |
| `test_opcoes_consolidacao_ui.mjs` | 0 (não existia) | 32 | **+32 (novo)** | "32/32, guardião novo" (32-03) |
| `test_faixa_liquidez_ui.mjs` | 51 | 51 | **0** | "13/13" (32-02) — discrepância de prosa, ver metodologia acima; contagem direta nunca variou |
| `test_fase22_componentes_compartilhados.mjs` | 113 | 113 | **0** | "118/118" (32-02) — mesma classe de discrepância (execução com laço vs. estática); contagem estática nunca variou |

**Nenhum guardião teve a contagem `ok(` diminuída em relação ao estado
anterior à Fase 32.** A maior variação isolada dentro de um único plano
(`test_carteira_opcoes_tira.mjs`, de 50 para 47 entre o fechamento do 32-03 e
o do 32-04) é integralmente explicada e documentada: o commit `9489359`
(deviation Rule 1 do Plano 32-04) removeu as asserções dos itens 8/9 ("silêncio
deliberado do card" e "estado `opcoesFor`") porque os dois conceitos deixaram
de existir no código — `PropostaDaPosicao` foi removida nesta mesma fase
(decisão arquitetural B, registrada no PLAN.md do 32-04) — e as substituiu por
asserções negativas equivalentes, com nota datada explicando a substituição
(ver `git show 9489359 -- web/tests/test_carteira_opcoes_tira.mjs`). Não é
uma regra perdida em silêncio: é uma regra aposentada por escrito, no mesmo
commit que removeu o código que ela guardava, e a contagem contra o baseline
pré-Fase-32 (43→47) segue positiva.

**Veredito do item 7: LIMPO.**

---

## Veredito final da Task 1

**LIMPA nos itens 2 a 7, sem ressalva** — a cadeia de execução do collar
curado, a paridade dos stores, o chamador único de UI, a suíte canônica
inteira, o build e os 11 guardiões nominais não têm nenhum achado.

**Item 1 fica ACHADO-CONDICIONAL, sinalizado e não resolvido
unilateralmente:** pelo range literal do plano (`main...HEAD`), o diff
LISTA os 4 arquivos/diretórios proibidos — não porque a Fase 32 os tocou,
mas porque `main`/`origin/main` estão atrasados de toda a Fase 31 e dos
quicks 260915-j5l/260915-ndt nesta branch. Uso `bd459f1..HEAD` (só os
commits da Fase 32) como a leitura que julgo correta, e por esse range o
item 1 também é LIMPO — mas essa escolha de range é uma decisão que o
próprio plano manda escalar, não fechar por conta própria. Fica para o
orquestrador/Alex ratificar antes da Task 3 (que já tem, por desenho, um
passo de merge com `origin/main` antes do bump — o lugar certo para lidar
com essa divergência).

A cadeia de execução do collar curado (`card → handleExecutar → onExecutar →
ctx.A.executarCandidatoCurado → executarCandidato() → store.optionsCuradoriaAbrirCollar
→ POST /api/options/curadoria/abrir-collar`) está intocada pela Fase 32,
exatamente como o `32-RESEARCH.md` previu: só o local de onde o call site é
disparado mudou (`App.jsx` → `OpcoesScreen.jsx`), o resto da cadeia (o módulo
puro `executarCandidato.js`, os dois stores em `persistence.js`, `api.js`, a
rota do backend) não foi tocado por nenhum commit da Fase 32.

A suíte canônica (as DUAS suítes) passa inteira: 2923 passed / 5 skipped / 3
xfailed no backend, 152/152 no frontend, exit 0. `npm --prefix web run build`
sai limpo. Nenhum guardião perdeu regra.

Isto prova a AUSÊNCIA de regressão estática. Não prova, e não tem como
provar, que o clique real no card do collar curado abre a posição de verdade
— essa prova só existe por execução ao vivo (item 5 da Task 2), que é
exatamente o motivo desta fase ter um checkpoint humano bloqueante antes da
publicação.

---

*Task 1 do Plano 05 concluída. Parando aqui — a Task 2
(`checkpoint:human-verify`, gate bloqueante) exige verificação ao vivo do
Alex e não pode ser executada por este agente. A Task 3
(bump/publicação/push) permanece retida até a aprovação do Alex na Task 2.*
