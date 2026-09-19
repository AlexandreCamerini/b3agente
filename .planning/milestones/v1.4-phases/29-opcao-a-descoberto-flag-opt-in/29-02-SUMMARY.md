---
phase: 29-opcao-a-descoberto-flag-opt-in
plan: 02
subsystem: frontend — persistência local (deviceStore, ADR-003)
tags: [gate, flag-opt-in, opcoes, deviceStore, paridade-de-stores, ios]

requires:
  - phase: 29-opcao-a-descoberto-flag-opt-in (plano 01)
    provides: "config.permitirOpcaoADescoberto/descobertoTermo, MOTIVO_DESCOBERTO_DESLIGADO, gate em store.buy_option (backend)"
provides:
  - "permitirOpcaoADescoberto/descobertoTermo espelhados no deviceStore (saneamento fail-closed, regra de aceite, sync device->servidor)"
  - "gate no ramo LOCAL de deviceStore.optionsBuy, byte a byte igual ao do backend"
  - "prova de que deviceStore.optionsSell nunca é gateado (source assertion + comportamento)"
  - "web/tests/test_opcao_descoberto_store.mjs (30 asserções, guardião próprio)"
affects: ["fase-30 (curadoria IA das 4 estruturas)", "fase-31 (polish UX)"]

tech-stack:
  added: []
  patterns:
    - "espelho estrutural exato de store.py.set_config no putConfig do deviceStore (mesmo padrão de appMode/operadorTermo)"
    - "sanitizer de doc carregado usa igualdade ESTRITA com `true`, não `!!` — fail-closed real para lixo truthy (string/número)"
    - "gate no ramo local ANTES de qualquer chamada de rede (evita queimar orçamento de requisição em pedido já proibido)"

key-files:
  created:
    - web/tests/test_opcao_descoberto_store.mjs
  modified:
    - web/src/persistence.js

key-decisions:
  - "serverStore não recebeu nenhuma linha nova — optConfig (linha ~115) já copia qualquer chave do patch (genérico), e optionsBuy/optionsSell são relays puros. Confirmado lendo persistence.js:115-121 antes de decidir não tocar."
  - "Sanitizer do doc usa `=== true` (igualdade estrita), não `!!` — bug encontrado na própria execução: `!!\"true\"` e `!!1` avaliam `true` em JS, o oposto do fail-closed que o plano exige. Corrigido antes do guardião existir (commit b074819)."

requirements-completed: [SC-1, SC-2, SC-4]

duration: ~50min
completed: 2026-09-13
---

# Fase 29 Plano 02: Flag de opção a descoberto — gate espelhado no deviceStore Summary

Fechado o buraco do tamanho do app iOS offline: o ramo LOCAL de
`deviceStore.optionsBuy` — a única superfície de todo o produto capaz de
abrir uma posição de opção a seco sem tocar o servidor — agora recusa a
compra com a mesma mensagem do backend quando o flag está desligado, sem
queimar requisição do provedor de opções. `optionsSell` continua
comprovadamente livre do gate, em qualquer estado.

## O que foi feito

**Task 1 — Campos no deviceStore (`web/src/persistence.js`, commit `83dec92`)**
- Saneamento do doc carregado (`ensure()`): `descobertoTermo` não-objeto
  volta a `null`; `permitirOpcaoADescoberto` é saneado fail-closed (ver
  Deviação abaixo — corrigido em commit separado).
- `putConfig`: espelho estrutural exato de `store.py.set_config` — ligar
  exige `descobertoTermo` já aceito ou vindo no mesmo patch; desligar é
  livre e preserva o termo.
- Sync device→servidor dentro de `if (sync.hasSession())`: os dois campos
  sobem chave a chave no MESMO `putConfig` que os mudou, incluindo a carona
  do termo quando o flag liga sem reenviá-lo (mesma classe de incidente que
  os comentários de `appMode`/`operadorTermo` já documentam no arquivo).
- **`serverStore` não mudou** — confirmado por leitura direta:
  `persistence.js:115-121` (`optConfig`) copia genericamente qualquer chave
  do patch (`for (const k of Object.keys(patch || {})) { ... c[k] = patch[k]; }`,
  exceto `apiKey`/`clearKey`), e `serverStore.optionsBuy`/`optionsSell` são
  relays puros para `api.optionsBuy`/`api.optionsSell`. Nenhuma linha nova
  necessária; o guardião (Grupo B, asserção 5) trava isso.

**Task 2 — Gate no ramo local (`web/src/persistence.js`, commit `aa634e8`)**
- Constante `MOTIVO_DESCOBERTO_DESLIGADO` espelhada byte a byte de
  `server/app/store.py` (verificado por comparação programática, ver
  "Verificação de paridade" abaixo).
- Gate inserido em `deviceStore.optionsBuy` ANTES do `api.optionsChain`
  (evita queimar requisição do provedor com pedido já proibido — orçamento
  brapi de 15k/mês, ADR-008), reusando `_registrarRejeicaoLocal` + `throw`,
  mesmo padrão do gate de "Lastro insuficiente" já existente no arquivo.
  `price` gravado como `null` de propósito (convenção da casa: nunca `0.0`
  para valor desconhecido).
- `deviceStore.optionsSell` ganhou só um comentário de decisão — **nenhuma
  linha de código muda nela** (T-29-07: fechar posição nunca é vetado pelo
  flag, guardrail "Stop/alvo nunca são vetados" do CLAUDE.md).
- **`A.buyOption` (`web/src/App.jsx:8439-8446`) NÃO precisou de mudança** —
  confirmado por leitura direta do span: o `catch` já faz
  `flash("Compra de opção: " + (e.message || e))`, ou seja a mensagem do
  gate local chega à tela sem código novo (D2 do 29-CONTEXT.md: único
  comportamento novo na UI existente é a recusa, vinda do backend/gate).

**Task 3 — Guardião (`web/tests/test_opcao_descoberto_store.mjs`, novo, commit `fdd9187`)**
- 30 asserções (bem acima do mínimo de 17 do plano), em 4 grupos:
  - **Grupo A** (1 asserção): paridade byte a byte da mensagem, lida dos
    dois arquivos do disco via regex, com falha explícita se o regex não
    casar em qualquer um dos dois (nunca passa por vacuidade).
  - **Grupo B** (5 asserções): forma do gate por marcador de string (não
    número de linha) — presença em `optionsBuy`, ordem antes de
    `api.optionsChain`, ausência em `optionsSell`, ausência em
    `serverStore()`, forma negativa da regra de aceite no `putConfig`.
  - **Grupo C** (19 asserções): comportamento real do `deviceStore` com
    `api`/`fetch` mockados, sem sessão — default do doc novo, gate
    recusando sem queimar requisição do provedor, aceite/recusa/preservação
    do termo no `putConfig`, execução normal com flag ligado, a sequência
    ligar→comprar→desligar→vender (SC-4, prova comportamental de que
    `optionsSell` nunca é vetado), e o saneamento de doc com lixo
    (`permitirOpcaoADescoberto: "true"` string → `false`).
  - **Grupo D** (5 asserções): sync com sessão — ambos os campos no mesmo
    corpo, carona do termo quando falta no servidor, disciplina "sem
    carona" para campos não relacionados.

## Deviação do plano (Rule 1 — bug encontrado na própria execução)

**[Rule 1 - Bug] Sanitizer de `permitirOpcaoADescoberto` usava `!!`, que NÃO
cumpre o fail-closed exigido**

- **Encontrado durante:** preparação do Grupo C.6 do guardião (Task 3),
  antes de qualquer teste rodar.
- **Problema:** o plano (Task 1a) prescreve coação com `!!` para que "doc
  antigo... com lixo (`\"true\"`, `1`) resolva para `false`". Isso é
  matematicamente falso em JavaScript: `!!"true"` e `!!1` avaliam para
  `true` (qualquer string não-vazia é truthy), o OPOSTO do fail-closed
  pretendido. Verificado com `node -e 'console.log(!!"true", !!1)'` →
  `true true`.
- **Fix:** trocado `!!doc.config.permitirOpcaoADescoberto` por
  `doc.config.permitirOpcaoADescoberto === true` (igualdade estrita) no
  saneamento do doc. Só o booleano `true` de verdade liga o flag; qualquer
  outro valor (string, número, `null`, ausência) resolve para `false`.
  **Não** mudei o bloco de aceite do `putConfig` (Task 1b), que segue com
  `!!patch.permitirOpcaoADescoberto` de propósito — ali é um patch EXPLÍCITO
  do chamador, mesmo padrão de `bool(patch[...])` em `store.set_config`
  (aceitar coação de um valor que o próprio código do app está enviando é
  diferente de sanear lixo passivo vindo do disco).
- **Arquivos modificados:** `web/src/persistence.js`.
- **Verificação:** assertion 26/27 do guardião (Grupo C.6) prova o
  comportamento correto com um doc de lixo real gravado direto na chave
  escopada do `localStorage`, forçando reload via `_setDeviceScope`.
- **Commit:** `b074819` (commit próprio, separado do Task 1 original —
  Task 1 já estava commitado quando o bug foi encontrado).

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug de coação booleana)
**Impact on plan:** Correção necessária para a garantia de segurança
central do plano (fail-closed). Sem ela, a asserção 11 do próprio plano
("doc com lixo é saneado para false") teria FALHADO ao escrever o guardião
— o bug foi pego ANTES de qualquer teste rodar, não depois.

## Provas negativas (Task 3, executadas de verdade)

**(a) Remover o gate — 8 asserções nomeadas quebram**

1. Removidas as 6 linhas do gate em `deviceStore.optionsBuy` (bloco
   `if (!doc.config.permitirOpcaoADescoberto) { ... }`), deixando o fluxo
   ir direto ao `api.optionsChain` — DELETADO, não comentado (comentar
   deixaria a substring `permitirOpcaoADescoberto` ainda presente no
   arquivo, o que mascararia as asserções de forma do Grupo B).
2. Rodado `node tests/test_opcao_descoberto_store.mjs` de dentro de `web/`
   → **resultado real observado**: `8 TESTE(S) FALHARAM`, exit 1. Falharam
   exatamente: presença do gate em `optionsBuy`, ordem antes do
   `optionsChain`, "compra a seco com flag desligado É RECUSADA", "mensagem
   da recusa", "optionPositions inalterado", "cash inalterado", "history[0]
   registrou a rejeição" e "api.optionsChain NÃO foi chamado" — as 22
   asserções restantes continuaram passando (comportamento correto: só o
   que depende do gate quebrou).
3. Restaurado o bloco removido, texto idêntico ao original.
4. Confirmado com `git diff --stat web/src/persistence.js` → **saída
   vazia** (arquivo idêntico ao commit `aa634e8`).
5. Re-executado o guardião → 30/30 `ok`, exit 0.

**(b) Alterar 1 caractere da constante — só a asserção de paridade quebra**

1. Alterado `"está"` → `"esta"` (removido o acento de um caractere) em
   `const MOTIVO_DESCOBERTO_DESLIGADO` de `persistence.js`.
2. Rodado o guardião → **resultado real observado**: `1 TESTE(S)
   FALHARAM` — exatamente "mensagem do gate é byte a byte igual em
   persistence.js e store.py" (Grupo A). As 29 asserções restantes
   continuaram passando, incluindo as comportamentais que comparam a
   mensagem lançada em runtime contra o valor JÁ ALTERADO da constante
   (comportamento correto: o guardião pega DIVERGÊNCIA ENTRE ARQUIVOS, não
   uma inconsistência interna do próprio JS).
3. Restaurado o caractere.
4. Confirmado com `git diff --stat web/src/persistence.js` → **saída
   vazia**.
5. Re-executado o guardião → 30/30 `ok`, exit 0.

Um guardião que passa com e sem o que ele guarda não guarda nada — as duas
provas confirmam que este guarda de verdade.

## Verificação de paridade da mensagem (manual, além do guardião)

```
$ node -e '... extrai as duas constantes e compara ...'
JS : "Operar opções a descoberto está desligado — ligue o flag em Preferências → Operar opções a descoberto. Lastro obrigatório é o padrão desta conta."
PY : "Operar opções a descoberto está desligado — ligue o flag em Preferências → Operar opções a descoberto. Lastro obrigatório é o padrão desta conta."
EQUAL: true
```

## Números da suíte canônica (antes/depois)

- Baseline herdada do `29-01-SUMMARY.md`: **2793 passed, 5 skipped, 3
  xfailed**, exit 0; **144** arquivos `web/tests/*.mjs`, todos `[OK]`.
- Após Task 1: `2793 passed, 5 skipped, 3 xfailed`, exit 0 — sem regressão
  (a primeira rodada com `npx vite build` real gerou um `web/dist` novo que
  fez `test_ios_assets.mjs` falhar por divergência de chunks contra o
  bundle iOS já embarcado — efeito colateral do MEU build local, não do
  código; resolvido removendo `web/dist` gerado, gitignored e descartável,
  e reconfirmado com exit 0).
- Após Task 2: `2793 passed, 5 skipped, 3 xfailed`, exit 0 — sem regressão.
- Após a correção do sanitizer (commit `b074819`) + Task 3 (guardião novo):
  `2793 passed, 5 skipped, 3 xfailed`, exit 0; **145** arquivos `.mjs`,
  todos `[OK]` (144 + 1 novo).

Suíte canônica rodada 3 vezes ao todo neste plano (uma por task; a task 1
precisou de uma segunda rodada por causa do efeito colateral do próprio
`vite build`, não por regressão de código — dentro do orçamento "uma vez
por task, duas se houver correção").

## Verificação — comandos e resultados

```
$ cd web && node tests/test_opcao_descoberto_store.mjs
(30 linhas "ok", 0 "FALHOU")
TODOS OS TESTES DO GATE DE OPÇÃO A DESCOBERTO PASSARAM
EXIT=0

$ cd web && npx vite build
✓ built in ~900ms — EXIT=0

$ bash scripts/executar.sh --testes
2793 passed, 5 skipped, 3 xfailed, 990 warnings — EXIT=0
145 arquivos web/tests/*.mjs — todos [OK]

$ git diff --stat 93c89f2..HEAD
.../29-01-SUMMARY.md                          | 181 +++++++
web/src/persistence.js                        |  58 +++
web/tests/test_opcao_descoberto_store.mjs     | 262 +++++++
3 files changed, 501 insertions(+)
```

Zero linha em `web/src/App.jsx`, `web/src/opcoes/OpcoesScreen.jsx`,
`web/src/opcoes/PropostaLastreada.jsx` ou `server/app/agent.py` (fence D2
do `29-CONTEXT.md` preservada). Nenhum `bump.sh`/`publicar-web.sh`/push a
`origin` — o build local usado para verificação teve seu artefato
(`web/dist`, gitignorado) descartado logo em seguida, exatamente para não
deixar rastro de publicação fora do pipeline oficial.

## Limitações conhecidas

- Nenhuma. `deviceStore.optionsSell` segue intacto e comprovadamente livre
  do gate, tanto por source assertion quanto pela sequência
  ligar→comprar→desligar→vender.
- Rodar `npx vite build` localmente para verificação regenera `web/dist`
  (gitignorado) com hashes de chunk novos, o que faz
  `web/tests/test_ios_assets.mjs` acusar divergência contra o bundle iOS já
  embarcado (que só é atualizado pelo pipeline `entregar.sh`). Isto NÃO é
  regressão de código — é o comportamento correto do guardião de paridade
  de chunks detectando um build de desenvolvimento não publicado. Qualquer
  executor futuro que rode `vite build` fora do `entregar.sh` deve apagar
  `web/dist` antes de rodar a suíte canônica, ou aceitar essa falha isolada
  como esperada.

## Instruções para validar localmente

```bash
cd /Users/acamerini/dev/bolsia/b3-agente
node web/tests/test_opcao_descoberto_store.mjs   # roda de dentro de web/, ou ajuste o path
cd web && npx vite build && rm -rf dist
cd /Users/acamerini/dev/bolsia/b3-agente
bash scripts/executar.sh --testes
```

## Self-Check: PASSED

- `web/src/persistence.js` — FOUND (permitirOpcaoADescoberto, descobertoTermo, MOTIVO_DESCOBERTO_DESLIGADO, gate em optionsBuy, comentário em optionsSell)
- `web/tests/test_opcao_descoberto_store.mjs` — FOUND (30 asserções)
- commit `83dec92` — FOUND (`git log --oneline | grep 83dec92`)
- commit `aa634e8` — FOUND
- commit `b074819` — FOUND
- commit `fdd9187` — FOUND

## Next Phase Readiness

O gate está fechado nos dois lados (backend, 29-01; deviceStore local,
29-02) com guardiões próprios em ambos. Pronto para a Fase 30 (curadoria de
IA das 4 melhores estruturas) e Fase 31 (polish de UX) — nenhuma delas
depende de mudança adicional no gate em si.

---
*Phase: 29-opcao-a-descoberto-flag-opt-in*
*Completed: 2026-09-13*
