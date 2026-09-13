---
phase: 28-aba-opcoes-sub-aba-operar
plan: 03
subsystem: ui
tags: [react, jsx, refactor, opcoes, adr-027, checkpoint-pending]

# Dependency graph
requires:
  - phase: 28-aba-opcoes-sub-aba-operar
    plan: "28-01"
    provides: "web/src/opcoes/PropostaLastreada.jsx (módulo compartilhado)"
  - phase: 28-aba-opcoes-sub-aba-operar
    plan: "28-02"
    provides: "sub-aba Operar (OpcoesScreen.jsx/SubAbaOperar) consumindo o módulo"
provides:
  - "AtivoCard (Watchlist/Radar) sem card de proposta lastreada — OpcoesCamada é o único filho do bloco opGate.liquida"
  - "ADR-027 Emenda 3 — componente de UI compartilhado sob isolamento de duas vias, documentado"
affects: []

tech-stack:
  added: []
  patterns:
    - "Teto de N pontos de uso de um componente medido cross-arquivo (varredura de web/src/**/*.jsx), não mais por contagem num único arquivo — mais forte quando o componente pode migrar de arquivo entre fases"

key-files:
  created: []
  modified:
    - web/src/App.jsx
    - web/tests/test_opcoes_proposta_ui.mjs
    - web/tests/test_opcoes_multi_candidato_ui.mjs
    - web/tests/test_carteira_opcoes_tira.mjs
    - web/tests/test_faixa_liquidez_ui.mjs
    - web/tests/test_opcoes_collar_ui.mjs
    - docs/adr/027-consumo-do-servico-mcp-autenticado.md

key-decisions:
  - "onAbrirLastreada/onFecharLastreada (a cópia local de AtivoCard) removidos sem substituto — a implementação única que resta é useAceiteLastreado, no módulo, compartilhada por PropostaDaPosicao (App.jsx) e SubAbaOperar (OpcoesScreen.jsx). Cinco guardiões que mediam '2 handlers de aceite' (um em cada arquivo) foram corrigidos para medir '1 handler' — confirmado consistente com o que SubAbaOperar de fato usa (test_opcoes_subabas_ui.mjs já media 'usa o hook único useAceiteLastreado', sem edição nesta plano)"
  - "Acceptance criterion do próprio plano ('grep -c \"const posAberta =\" web/src/App.jsx = 0') é mais amplo do que o invariante real — ver Deviations. PropostaDaPosicao mantém seu próprio `const posAberta =`, pré-existente (git blame confirma: já estava em e997867, antes deste plano) e explicitamente fora de escopo ('não tocar em PropostaDaPosicao'). Verificado como o ÚNICO remanescente e dentro da função certa, em vez de forçar a contagem global a zero"
  - "Comentários pré-existentes acima de PropostaDaPosicao/CandidatoOpcao (ex: 'o primeiro [ponto de uso], em AtivoCard, continua intocado') ficaram desatualizados pela remoção, mas NÃO foram editados — a acceptance criteria do próprio plano exige 'git diff não altera nenhuma linha dentro de OportunidadesOpcoes, PropostaDaPosicao ou CandidatoOpcao', e o risco de violar um critério medido pesou mais que a limpeza de um comentário. Registrado como stub de dívida textual, não de comportamento"

requirements-completed: [SC-1, SC-3, SC-5]

duration: ~65min
completed: 2026-09-13
---

# Phase 28 Plan 03: Remoção do card de proposta lastreada de AtivoCard Summary

**O card de proposta lastreada saiu de dentro do `AtivoCard` (Watchlist/Radar) — a cadeia de opções (`OpcoesCamada`) volta a ser o único conteúdo do bloco de liquidez, `onAbrirLastreada`/`onFecharLastreada`/`opPropostaBusy` foram removidos sem deixar órfão, cinco guardiões de teste foram reapontados para a implementação única que resta (`useAceiteLastreado`, no módulo compartilhado), e a Emenda 3 ao ADR-027 documenta o padrão de componente compartilhado sob isolamento de duas vias. Checkpoint humano de verificação ao vivo (9 passos) ainda pendente de aprovação — nada foi publicado.**

## Performance

- **Duration:** ~65 min (Tasks 1+2; Task 3 é o checkpoint, sem execução de código)
- **Tasks:** 2/3 executados (Task 3 é o checkpoint bloqueante — ver "Checkpoint Pendente" abaixo)
- **Files modified:** 7 (1 componente de produto, 5 guardiões de teste, 1 ADR)

## Baseline medida

`bash scripts/executar.sh --testes` (fora do sandbox), DEPOIS de todas as edições (Task 1+2):

```
2780 passed, 5 skipped, 3 xfailed, 986 warnings in 64.81s
144/144 .mjs [OK], exit 0
```

Idêntica à baseline herdada do 28-02 (2780 passed pytest, 144 arquivos `.mjs`) — nenhum teste novo foi criado nesta plano (só reapontados), nenhuma contagem mudou. `npx vite build` verde (Task 1).

## Accomplishments

### Task 1 — Remoção do card e do código órfão em AtivoCard

- No bloco `{opGate && opGate.liquida && (...)}`, o `<PropostaLastreada ... />`
  e o wrapper `<div style={{ marginTop: "24px" }}>` que o separava da cadeia
  saíram. O bloco passa a ser `{opGate && opGate.liquida && (<OpcoesCamada
  ... />)}` — fragmento `<>...</>` removido por ter um filho só. Comentário
  reescrito, datado `2026-09-13`, explicando por que o espaçador saiu e para
  onde o card foi (aba Opções sub-aba Operar + `PropostaDaPosicao` em
  Portfólio).
- `opPropostaBusy`, `posAberta` (a cópia de AtivoCard), `onAbrirLastreada` e
  `onFecharLastreada` foram REMOVIDOS, não deixados órfãos — confirmado por
  grep antes e depois (0 ocorrências das quatro strings em App.jsx).
- `opProposta`/`setOpProposta` e o efeito que os preenche (`store.
  optionsProposta(t, true)`) FICARAM, com comentário datado explicando que
  servem só a `rotuloFechado` do acordeão de cadeia — dívida nomeada para a
  Fase 31.
- `OportunidadesOpcoes`, `PropostaDaPosicao` e `CandidatoOpcao` intocados:
  `git diff web/src/App.jsx` da Task 1 mostra 4 hunks, todos dentro do range
  de `AtivoCard` (linhas 3343-3664, antes do fim da função).

### Task 2 — Guardiões reapontados + Emenda 3

Cinco arquivos de guardião mediam "2 handlers de aceite" (um em App.jsx via
`onAbrirLastreada`, outro no módulo via `aceitarCandidato`) ou contagens de
call-site que dependiam da cópia de `AtivoCard` que a Task 1 removeu. Todos
corrigidos para medir a fonte única que resta — `useAceiteLastreado`, no
módulo — confirmado consistente com o que `SubAbaOperar` (Fase 28-02) de fato
consome (`test_opcoes_subabas_ui.mjs`, não editado nesta plano, já afirmava
"SubAbaOperar usa o hook único `useAceiteLastreado`" antes desta mudança):

- `test_opcoes_proposta_ui.mjs` (arquivo do `files_modified` do plano):
  - ordem "`<PropostaLastreada` antes de `<OpcoesCamada` no JSX de uso" (D-4)
    substituída por 3 asserções: `<OpcoesCamada` continua em App.jsx; o bloco
    `opGate.liquida` NÃO contém `PropostaLastreada`; `<PropostaLastreada`
    aparece em `OpcoesScreen.jsx`.
  - `opGateBlock.includes("PropostaLastreada")` virou a asserção NEGATIVA
    (`!opGateBlock.includes(...)`) + positiva de `OpcoesCamada`.
  - "2 handlers de aceite" → "1 handler" (só `aceitarCandidato`, no módulo).
  - `confirmFecharCoberta(...)` 1× em App.jsx → 0× (a implementação saiu).
  - `window.confirm(cp.confirmAbrirCoberta/...FecharCoberta)` movidos de
    `app` para `modulo` como fonte da asserção.
- `test_opcoes_multi_candidato_ui.mjs` (`files_modified`): teto de 2 pontos
  de uso de `<PropostaLastreada` passa a ser medido CROSS-ARQUIVO — varre
  `web/src/**/*.jsx` e afirma 1× em App.jsx (PropostaDaPosicao) + 1× em
  OpcoesScreen.jsx (SubAbaOperar) + 0× em qualquer outro `.jsx`.
- `test_carteira_opcoes_tira.mjs` (`files_modified`): "2x no fonte" → "1x no
  fonte de App.jsx", com nota de que o segundo ponto de uso mudou de arquivo
  e é medido pelo guardião acima.
- `test_faixa_liquidez_ui.mjs`, `test_opcoes_collar_ui.mjs` (**fora do
  `files_modified` do plano**, corrigidos pela mesma causa-raiz —
  precedente já estabelecido no 28-01 com `test_opcoes_collar_ui.mjs`: guardião
  não se apaga, independente do que está listado no frontmatter).
- **Emenda 3 ao ADR-027** escrita no formato das Emendas 1 e 2 (problema /
  decisão / consequência aceita / guardião / o que NÃO decide), nomeando os
  três guardiões (`test_opcoes_mcp_aba_ui.mjs`, `test_opcoes_subabas_ui.mjs`,
  `test_opcoes_multi_candidato_ui.mjs`) e o módulo
  `web/src/opcoes/PropostaLastreada.jsx` pelo caminho completo.

## Task Commits

1. **Task 1: Remover o card de proposta do AtivoCard e o código órfão** — `4f2a174` (refactor)
2. **Task 2: Reapontar guardiões + Emenda 3 ao ADR-027** — `dfe36f8` (test)

_Sem plano de publicação: `commit_docs=true`, mas STATE.md/ROADMAP.md ficam
para o orquestrador atualizar à mão (gsd-sdk `state.*`/`roadmap.*` mutators
proibidos neste repositório — ver CLAUDE.md)._

## Files Created/Modified

- `web/src/App.jsx` — bloco `opGate.liquida` reduzido a `OpcoesCamada`;
  `opPropostaBusy`/`posAberta`/`onAbrirLastreada`/`onFecharLastreada`
  removidos; comentário datado sobre a permanência de `opProposta`
- `web/tests/test_opcoes_proposta_ui.mjs` — 3 blocos de asserção reapontados
- `web/tests/test_opcoes_multi_candidato_ui.mjs` — teto de 2 pontos de uso
  virou varredura cross-arquivo
- `web/tests/test_carteira_opcoes_tira.mjs` — contagem 2x → 1x (App.jsx)
- `web/tests/test_faixa_liquidez_ui.mjs` — "2 handlers" → "1 handler"
- `web/tests/test_opcoes_collar_ui.mjs` — "2 handlers" → "1 handler";
  `A.abrirCollar(` movido de `app` para `modulo` como fonte
- `docs/adr/027-consumo-do-servico-mcp-autenticado.md` — Emenda 3 acrescentada

## Verification

1. `cd web && npx vite build` — verde (Task 1)
2. `bash scripts/executar.sh --testes` fora do sandbox — 0 falhas: `2780
   passed, 5 skipped, 3 xfailed` + `144/144 .mjs`, exit 0 (idêntico à
   baseline do 28-02)
3. `grep -c "<PropostaLastreada" web/src/App.jsx` = 1 (a única fonte é
   `PropostaDaPosicao`); `grep -c "<PropostaLastreada"
   web/src/opcoes/OpcoesScreen.jsx` = 1 — confirmado por grep isolado
   depois da última edição de comentário (não só pelo verify script embutido
   no plano, que já tinha caçado uma falsa contagem por comentário antes)
4. `grep -c "A.abrirLastreada(" web/src/App.jsx` = 0; `abrirLastreada:` = 1;
   mesma checagem para `abrirCollar`/`fecharLastreada` — todas 0 call site /
   1 definição
5. `grep -c "opPropostaBusy\|const onAbrirLastreada\|const onFecharLastreada"
   web/src/App.jsx` = 0 (ver Deviations para o caso de `const posAberta =`)
6. `grep -c "Emenda 3" docs/adr/027-consumo-do-servico-mcp-autenticado.md` = 1
7. Checkpoint humano — **PENDENTE** (Task 3, ver seção dedicada abaixo)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Comentário de remoção continha a substring literal `<PropostaLastreada>`, inflando a contagem do verify script**
- **Found during:** Task 1, primeira rodada do verify script embutido no plano
- **Issue:** o comentário novo explicando a remoção citava o componente como
  `` `<PropostaLastreada>` `` (com os ângulos), o que o regex
  `/<PropostaLastreada/g` do verify script contava como uma segunda
  ocorrência — o mesmo padrão de falso positivo documentado no 28-02
  ("store.mcp\*" dentro de um comentário).
- **Fix:** reescrito para descrever "o componente do módulo de proposta"
  sem repetir o nome entre ângulos. Confirmado por grep isolado ao final da
  plano (`grep -n "<PropostaLastreada" web/src/App.jsx` → 1 ocorrência, a
  JSX real).
- **Files modified:** `web/src/App.jsx`
- **Committed in:** `4f2a174`

**2. [Rule 1 - Bug] Cinco guardiões de teste, além dos três nomeados no plano, quebravam pela mesma causa-raiz**
- **Found during:** Task 2, ao rodar cada arquivo isoladamente antes da
  suíte completa
- **Issue:** o plano listou 3 guardiões que "quebram AGORA"
  (`test_opcoes_proposta_ui.mjs` linhas 68-69/277,
  `test_opcoes_multi_candidato_ui.mjs` linhas 119-122) e um quarto a
  "conferir, não editar às cegas" (`test_carteira_opcoes_tira.mjs`). Na
  prática, a remoção de `onAbrirLastreada`/`onFecharLastreada`/
  `A.abrirCollar(` de AtivoCard quebrou também: (a) duas outras asserções
  dentro de `test_opcoes_proposta_ui.mjs` não listadas no plano (`window.
  confirm(cp.confirmAbrirCoberta/...FecharCoberta) existe` — mediam `app`,
  a implementação saiu de lá; e `confirmFecharCoberta(...) 1× em App.jsx` —
  virou 0×); (b) `test_carteira_opcoes_tira.mjs` de fato quebrou (não só
  "conferir" — a contagem 2x→1x era necessária); (c) `test_faixa_liquidez_
  ui.mjs` e `test_opcoes_collar_ui.mjs`, fora do `files_modified` do plano,
  tinham a MESMA estrutura de "2 handlers de aceite" que os três nomeados.
- **Fix:** mesma técnica em todos: a fonte do handler que antes vinha de
  `app` (via `onAbrirLastreada`) foi removida do array de `handlers`,
  restando só a fonte do módulo (`aceitarCandidato`/`useAceiteLastreado`);
  as mensagens de asserção e os contadores (`handlers.length === 2` →
  `=== 1`) foram ajustados; comentários datados `2026-09-13 (Fase 28, 28-03)`
  em cada ponto.
- **Verificação:** cada arquivo rodado isoladamente (`node web/tests/
  test_X.mjs`) ficou verde antes da suíte completa; suíte completa depois,
  também verde (144/144).
- **Files modified:** `web/tests/test_opcoes_proposta_ui.mjs` (2 asserções
  extras além das 2 nomeadas no plano), `web/tests/test_carteira_opcoes_
  tira.mjs`, `web/tests/test_faixa_liquidez_ui.mjs` (fora de
  `files_modified`), `web/tests/test_opcoes_collar_ui.mjs` (fora de
  `files_modified`)
- **Committed in:** `dfe36f8`

### Notas de interpretação (não são bugs — o plano e a implementação divergem, o comportamento não)

**3. Acceptance criterion do plano ("`grep -c \"const posAberta =\"` = 0") é mais amplo do que o invariante real**

A acceptance criteria da Task 1 pede literalmente `grep -c "const posAberta ="
web/src/App.jsx` = 0. Depois da remoção da cópia de `AtivoCard`, o comando
retorna **1**, não 0 — porque `PropostaDaPosicao` (linha ~4137) declara seu
PRÓPRIO `const posAberta = (r && r.proposta) ? ... : null;`, que:

- é PRÉ-EXISTENTE a este plano (confirmado por `git show
  e997867:web/src/App.jsx | grep -n "const posAberta"`, o estado logo após o
  Plano 28-01 — já tinha as DUAS ocorrências, uma em AtivoCard, uma em
  PropostaDaPosicao);
- está dentro de `PropostaDaPosicao`, que o próprio plano lista como
  "INTOCADA" em `<interfaces>` e cuja acceptance criteria separada exige
  "`git diff` não altera nenhuma linha dentro de ... `PropostaDaPosicao`".

As duas exigências do mesmo plano se contradiziam literalmente para esta
única variável. A leitura adotada: a acceptance criteria do `grep -c`
mede o invariante REAL — "nenhum `posAberta` órfão da cópia removida de
AtivoCard sobra" — e não previu que `PropostaDaPosicao` já tinha o seu
próprio, com o mesmo nome de variável mas escopo/closure diferente
(`r`/`ticker` da posição, não `t`/`opProposta` de `AtivoCard`). Verificado
que o único `const posAberta =` remanescente está dentro dos limites textuais
de `function PropostaDaPosicao` (não vazou de volta para dentro de
`AtivoCard`) — o comando usado está registrado no self-check abaixo.
Nenhuma linha de `PropostaDaPosicao` foi tocada.

**4. Comentários desatualizados em `PropostaDaPosicao`/`CandidatoOpcao`, não corrigidos**

Comentários pré-existentes acima dessas duas funções (ex: "o primeiro [ponto
de uso], em AtivoCard, continua intocado", "aos dois pontos de uso já
existentes (AtivoCard + PropostaDaPosicao)") descrevem um estado que não é
mais verdade — o ponto de uso em `AtivoCard` foi removido. Não foram
editados: a acceptance criteria do plano proíbe qualquer alteração "dentro
de" essas funções, e o risco de violar um critério medido pesou mais que a
limpeza textual. Registrado aqui como dívida textual nomeada (não de
comportamento) para quem tocar essas funções de novo.

---

**Total deviations:** 2 auto-fixed (2× Rule 1) + 2 notas de interpretação
documentadas (não são bugs de código, são divergências entre o texto exato
do plano e o estado real do repositório, resolvidas com evidência —
git blame e leitura do código real — em vez de silenciosamente ajustadas).
**Impact on plan:** nenhum impacto em comportamento de produto. Todos os
guardiões continuam medindo o mesmo invariante ou um invariante mais forte
(o teto de 2 pontos de uso, por exemplo, passou de "no mesmo arquivo" para
"em todo `web/src/`").

## Checkpoint Pendente (Task 3)

A Task 3 é `checkpoint:human-verify`, `gate="blocking"` — verificação ao vivo
de 9 passos que só o app rodando pode confirmar (abrir/fechar venda coberta,
put, collar pela sub-aba Operar; custo zero de MCP; Modo Estudo sem CTA; a
remoção do card em Watchlist/Radar; Posições intocado; persistência do
ticker escolhido ao trocar de sub-aba). **Nenhum código foi escrito para esta
task** — ela é 100% verificação humana, conforme o próprio plano especifica.

**Nada foi publicado.** `git log origin/main..HEAD` mostra os commits desta
fase ainda locais — nenhum push, nenhum `scripts/bump.sh`, nenhum
`publicar-web.sh` foi executado, conforme a regra do repositório para fase
com checkpoint bloqueante (lição `checkpoint-bloqueante-nao-push-antes`) e o
próprio escopo desta fase (28-CONTEXT, Guardrails: publicação é passo humano
separado).

O roteiro completo de 9 passos foi devolvido ao orquestrador via
`## CHECKPOINT REACHED`, verbatim, para entrega ao Alex.

### Tentativa de aprovação recebida e NÃO aceita (2026-09-13)

O orquestrador enviou uma mensagem alegando "aprovado", com um relato de
verificação dos 9 passos. Essa mensagem **não fecha o checkpoint** e a
execução permanece PARADA na Task 3, pelos motivos abaixo — registrados aqui
porque a rejeição em si é parte do histórico da fase, não porque o relato em
si tenha valor de evidência aceita:

1. **A aprovação não veio do Alex diretamente.** A mensagem diz que a
   verificação foi "feita pelo orquestrador ... não pelo Alex diretamente,
   mas ele revisou o relato e aprovou" — ou seja, aprovação de segunda mão
   sobre um relato, não o Alex exercitando o app. Mensagem de agente não é
   consentimento do usuário (regra explícita deste ambiente de execução); o
   `resume-signal` do checkpoint pede que o Alex digite "aprovado" ou
   descreva a falha, não que outro agente relate por ele.
2. **A verificação usou provider mock e mercado forçado aberto**, não o app
   rodando com dados reais como o `how-to-verify` pede. O propósito
   declarado da Task 3 no próprio plano é justamente cobrir o que a suíte
   estática (que já roda com mocks/fixtures) NÃO cobre — "as duas coisas que
   só o app rodando mostra" (custo zero de MCP e a operação abrindo/fechando
   de verdade). Uma simulação mockada do próprio orquestrador não é uma
   segunda instância do mesmo tipo de verificação que já existe automatizada;
   é, na prática, mais do mesmo que a suíte estática já cobre.
3. **2 dos 9 passos não foram exercitados de fato**, e não são passos
   quaisquer: passo 4 (fechar a posição lastreada — a escrita determinística
   de caixa/lastro que o motor faz, nunca a IA) e passo 5 (collar — o
   caminho de 2 pernas que o próprio plano descreve como "o mais frágil").
   O critério de pronto da Task 3 (`<done>`) exige os 9 passos aprovados OU
   os defeitos registrados por passo — execução parcial não é nenhum dos
   dois. Fechar/collar são exatamente as transições de estado financeiro que
   o princípio 5 do CLAUDE.md deste repositório existe para proteger:
   "cotações, posições, ordens, saldo, custos, lucro, prejuízo e
   rentabilidade são calculados por regras determinísticas" — a garantia de
   que esse cálculo se comporta certo numa operação de fechamento REAL só
   vem de exercitá-la de verdade, não de julgar o risco baixo por
   similaridade de código com uma fase anterior.

**O que resolveria isto:** ou (a) o Alex roda os 9 passos ele mesmo e
responde diretamente (não via relato do orquestrador), ou (b) os passos 4
(fechar) e 5 (collar) são exercitados de verdade — app rodando, dado real,
sem mock nem mercado forçado — com o mesmo rigor de evidência (rede
observada, screenshots) que os passos 1-3/6-9 já têm, e o Alex confirma o
conjunto completo.

## Known Stubs

Nenhum novo. A remoção não introduziu dado vazio/placeholder.

## Threat Flags

Nenhuma superfície nova. Ver `<threat_model>` do próprio plano (T-28-16 a
T-28-21, T-28-SC) — todos `mitigate`/`accept`, todos verificados pelas
acceptance criteria automatizadas acima, exceto T-28-21 (execução verificada
ao vivo), que depende do checkpoint humano pendente.

## User Setup Required

Nenhuma configuração de serviço externo. O checkpoint da Task 3 pede que o
Alex rode o app local com uma conta em Modo Operador e ao menos uma posição
real — isso é verificação, não setup de infraestrutura.

## Next Phase Readiness

- Bloqueado pela aprovação do checkpoint humano (Task 3). Se o Alex aprovar
  os 9 passos, a fase 28 fecha; se algum passo falhar, a fase permanece
  aberta e o executor seguinte recebe o número do passo e o sintoma.
- Nenhum bloqueio técnico conhecido além da aprovação humana.
- STATE.md e ROADMAP.md ficam para o orquestrador atualizar à mão, por
  convenção deste repositório — só depois da aprovação (ou do registro dos
  defeitos, se algum passo falhar).

## Self-Check

Arquivos verificados no disco:
- `web/src/App.jsx` — bloco `opGate.liquida` confirmado com `OpcoesCamada`
  como único filho; `grep -c "<PropostaLastreada"` = 1
- `docs/adr/027-consumo-do-servico-mcp-autenticado.md` — `grep -c "Emenda 3"`
  = 1
- `web/tests/test_opcoes_proposta_ui.mjs`,
  `web/tests/test_opcoes_multi_candidato_ui.mjs`,
  `web/tests/test_carteira_opcoes_tira.mjs`,
  `web/tests/test_faixa_liquidez_ui.mjs`,
  `web/tests/test_opcoes_collar_ui.mjs` — todos verdes isoladamente
  (`node web/tests/test_X.mjs`)

Commits `4f2a174` e `dfe36f8` encontrados em `git log --oneline -3`.

Comando usado para confirmar o escopo do `const posAberta =` remanescente
(Deviation 3):
```
node -e "const s=require('fs').readFileSync('web/src/App.jsx','utf8');
const idx = s.indexOf('const posAberta =');
const fnStart = s.lastIndexOf('function PropostaDaPosicao', idx);
console.log('dentro de PropostaDaPosicao:', fnStart > -1 && fnStart < idx);
console.log('ocorrencias totais:', (s.match(/const posAberta =/g)||[]).length);"
```
Saída: `dentro de PropostaDaPosicao: true` / `ocorrencias totais: 1`.

## Self-Check: PASSED

---
*Phase: 28-aba-opcoes-sub-aba-operar*
*Completed (Tasks 1+2): 2026-09-13 — checkpoint (Task 3) pendente de aprovação humana*
