---
phase: 260824-kc2-preferencias-de-push-por-classe-de-event
plan: 01
subsystem: preferências de push (backend + dois stores + UI)
tags: [push, apns, preferencias, consentimento, paridade-stores, guardioes]
requires:
  - push.prefs_for / push.set_prefs (kv `pushPrefs`, já existiam com 1 booleano)
  - POST /api/push/register-token (canal único de escrita — NÃO foi tocado)
  - skill_ref.push_titulo / PUSH_TITULOS (vocabulário do push — NÃO foi tocado)
  - agent.events como rastro durável (entregue pelo 260824-i45)
provides:
  - push.PREFS_PADRAO com radar/execucao/protecao nascendo LIGADAS
  - push.PREFS_BOOLS (allowlist booleana) + patch parcial como contrato escrito
  - push.CLASSE_POR_TAG + push.classe_do_evento() (tabela única tag→classe, fail-open)
  - gate por classe nos 3 call sites (Radar diário, ordem pendente, ciclo do Operador)
  - tag `protecao-opcao` no evento de venda de opção
  - serverStore.syncPushPrefs efetivo (item 6 do brief) e disparado pelo próprio store
  - quadro de autoridade cliente↔cliente escrito nos dois lados
  - controles por classe em Perfil → Notificações
affects:
  - server/app/push.py, agent.py, radar_daily.py, store.py, defaults.py
  - web/src/persistence.js, web/src/App.jsx
tech-stack:
  added: []
  patterns:
    - "asserção de presença por CONTAGEM (=== 2), não por booleano — mutar um store só fica vermelho"
    - "asserção de ausência sobre o código com comentários REMOVIDOS (o comentário cita o antipadrão de propósito)"
    - "quadro de autoridade cliente↔cliente escrito no código, não em doc externo"
    - "fail-open declarado no docstring, com o PREÇO do desenho escrito junto"
key-files:
  created:
    - server/tests/test_push_prefs_classes.py
    - web/tests/test_push_prefs_classes.mjs
    - web/tests/test_notif_classes_ui.mjs
  modified:
    - server/app/push.py
    - server/app/agent.py
    - server/app/radar_daily.py
    - server/app/store.py
    - server/app/defaults.py
    - server/tests/test_didatica_isolamento.py
    - web/src/persistence.js
    - web/src/App.jsx
    - web/tests/test_didatica_parity.mjs
    - web/tests/test_putconfig_so_o_que_mudou.mjs
decisions:
  - "Decisão travada respeitada: as 3 classes nascem LIGADAS (é controle novo de alerta velho); `gatilho` continua opt-in e desligado"
  - "O web escreve SÓ as 3 classes da conta — `gatilho`/`modo`/`universo` continuam autoridade do aparelho, e a ausência é estrutural (grep prova)"
  - "Consentimento NÃO é conjunção com `config.notif.enabled`: são dois mestres, e o do push do servidor é o token registrado"
  - "Fail-open para tag desconhecida; o preço (todo evento notificável precisa de tag) fica escrito no docstring"
metrics:
  tasks: 3
  commits: 3
  duration: ~1h20
  completed: 2026-08-24
---

# Quick task 260824-kc2: preferências de push por classe de evento

O push server-side tinha UM booleano (`gatilho`) e três classes que não
consultavam nada — quem registrou token recebia prévia do Radar, execução de
ordem e proteção sem controle nenhum. Agora cada classe tem interruptor, os dois
clientes gravam a preferência (fechando o item 6 do brief, em que ativar push no
web logado não gravava nada), e **ninguém perde notificação**: o que nasceu foi o
CONTROLE, não o alerta.

## O que mudou, por camada

**Servidor — `push.py` é o dono do consentimento.** `PREFS_PADRAO` ganhou
`radar`/`execucao`/`protecao` LIGADAS, com a nota que resolve a tensão contra o
comentário de opt-in logo acima (classe de alerta genuinamente nova continua
nascendo desligada; `gatilho` segue sendo o exemplo vivo). A migração de quem já
existe saiu **de graça**: `prefs_for` faz `{**PREFS_PADRAO, **p}`, então
preferência gravada antes herda o default certo — nenhuma migração de dado foi
escrita. `set_prefs` passou a iterar `PREFS_BOOLS` aplicando só as chaves
PRESENTES, e a parcialidade virou **contrato escrito**, não acidente: é ela que
permite ao web escrever as três classes sem encostar no que é do aparelho.

**Tabela tag→classe, com fail-open declarado.** `CLASSE_POR_TAG` +
`classe_do_evento()` moram em `push.py` (não em `agent.py`) porque os dois funis
de push precisam da MESMA tabela e consentimento é assunto daquele módulo. Tag
ausente/desconhecida devolve `None` e o push SAI — silenciar por omissão de
tabela seria tirar aviso sem consentimento, o mais caro dos dois erros. O PREÇO
desse desenho está escrito junto: **todo evento que vira push precisa de `tag`**.

**O evento de opção estava exatamente nesse buraco.** `_avaliar_opcoes` emitia
`{"kind": "buy", "text": "Proteção simulada: opção…"}` **sem tag**; o funil D3
filtra por `kind == "buy"`, então virava push e, com o fail-open, sairia mesmo com
"Proteção" desligado — o controle mentiria para o usuário. Ganhou
`tag: protecao-opcao`. O **título não mudou**: `push_titulo` já devolvia o
genérico do modo para tag sem frase, que é o título que esse push sempre teve
(guardião próprio contra "completar" `PUSH_TITULOS` sem necessidade).

**Os três call sites.** O gate fica sempre **antes do `notify_push` e depois da
contabilização** — preferência de aviso não mexe em métrica de execução. E fica
**sobre a interrupção, nunca sobre o rastro**: o evento continua entrando em
`agent.events` para quem tem token mesmo com a classe desligada, que é o rastro
durável criado pelo 260824-i45. No Radar, a leitura de prefs tem `try/except`
**próprio degradando para ENVIAR**: as duas operações daquele laço são guardadas
individualmente de propósito, e um `prefs_for` que levantasse escaparia do laço,
subiria até `maybe_run` e mataria a varredura do dia para todos os usuários
restantes.

**Kill-switch continua sem interruptor**, agora com a exceção escrita: a
audiência é por RBAC, é aviso operacional, e foi justamente o kill-switch ligado
sem querer que parou a execução de toda a base por 2,5 dias.

**Front — cada cliente escreve o que lhe cabe.** Os dois stores ganharam as três
classes na MESMA forma literal (`n.<chave> !== false`), sem conjunção com
`n.enabled`. O `syncPushPrefs` do web manda **só as três classes** — sem
`gatilho`, sem `modo`, sem `universo` — e isso não é omissão, é o fechamento da
janela de clobber (detalhe abaixo). O `notif` passou a subir device→servidor
**chave a chave**, e o `serverStore` dispara o sync sozinho com debounce próprio.

**UI.** `rowPushClasse` existe por UMA razão: não ser gated por `nf.enabled`. O
bloco "O QUE O SERVIDOR AVISA" renderiza sob `logged` (a preferência é da CONTA e
pode ser entregue no iPhone da mesma conta), enquanto os botões de registro do
aparelho seguem sob `isNative`.

## Os dois invariantes, e por que cada um tem guardião próprio

**1. Dois mestres, não um.** `config.notif.enabled` é o mestre das notificações
LOCAIS do front; o mestre do push do SERVIDOR é o **token registrado**, que é um
ato explícito e separado (`onAtivarPush`). Aplicar a conjunção
`n.enabled && n.execucao` às classes novas desligaria execução e proteção para
todo usuário que registrou push e nunca ligou o interruptor local — gente que
recebe esses avisos hoje. O guardião do front assere por **CONTAGEM** (`=== 2`):
na forma booleana, mutar só um store continuaria verde. Provado por mutação.

**2. Ninguém perde o `gatilho`.** `serverStore.syncPushPrefs` nunca era chamado,
então o clobber não existia; ele nasceria no momento em que o web passasse a
chamá-lo, derivando `gatilho` do `config.notif` **do servidor** — que para um
usuário device-first é o default, e o default **não é ausência de chave**:
`defaults.py` grava `enabled: False` e `gatilho: False` EXPLÍCITOS, e `set_prefs`
grava por chave. Sintoma: iPhone com gatilho ligado, uma visita ao app pelo
navegador, e o aviso some em silêncio. O fechamento é **estrutural**, não
temporal: o web literalmente não escreve a chave, e um grep de ausência prova.
Do lado do backend, o que sustenta isso é a parcialidade do patch, com teste
próprio (`test_patch_parcial_nao_toca_chave_ausente`). `modo` e `universo` saíram
pela mesma razão.

## Guardiões: três novos, três atualizados com nota

**Novos.** `server/tests/test_push_prefs_classes.py` (22 testes) exercita o
invariante pelos **caminhos REAIS** — `radar_daily.run_daily` e
`agent.scheduler_loop`, não chamada direta ao gate: um teste que chamasse
`classe_do_evento` sozinho ficaria verde mesmo se o call site nunca consultasse a
preferência. Cobre isolamento por classe (com o rastro preservado), fail-open
unitário **e comportamental**, a opção, patch parcial, migração de graça,
cobertura estrutural por SUPERCONJUNTO (com igualdade, `protecao-opcao` exigiria
inventar título) e a exceção do kill-switch ancorada na **chamada**
(`prefs_for(`), nunca na palavra — o docstring a contém de propósito, e o teste
assere as duas coisas: a chamada ausente e a palavra presente.

`web/tests/test_push_prefs_classes.mjs` e `web/tests/test_notif_classes_ui.mjs`
seguem o padrão source-grep da casa. Toda asserção de ausência roda sobre o
código com **comentários removidos**.

**Atualizados com nota, nunca apagados.** `test_didatica_isolamento.py`
(o opt-in do `gatilho` continua, e as três classes ganharam asserção própria no
MESMO teste, para a tensão entre as duas regras ficar visível no mesmo lugar);
`test_didatica_parity.mjs` (a linha "consentimento é CONJUNÇÃO" continua valendo
— **só para o gatilho, só no deviceStore** — com nota de 12 linhas explicando os
dois mestres, mais duas asserções novas; e o literal da allowlist atualizado sem
relaxar a forma); `test_putconfig_so_o_que_mudou.mjs` (`notif` entrou no payload,
com a regra do "sem carona" **estendida para dentro do campo**, não relaxada).

`test_notif_central.mjs` ficou **verde sem alteração** — o markup novo não moveu
nenhuma das âncoras existentes.

## Provas de mutação — quatro, todas executadas e desfeitas

| # | Mutação | Resultado |
|---|---------|-----------|
| 1 | `PREFS_PADRAO["radar"] = False` | VERMELHO (4 testes, incl. o invariante do Radar pelo caminho real) |
| 2 | `PREFS_PADRAO["execucao"] = False` | VERMELHO (4 testes, incl. o funil de ordem pendente) |
| 3 | `PREFS_PADRAO["protecao"] = False` | VERMELHO (4 testes, incl. stop e opção) |
| 4a | `execucao: !!(n.enabled && n.execucao)` em UM store só | VERMELHO (é o que prova que a contagem pega mutação de um lado só) |
| 4b | `gatilho:` de volta no corpo do `syncPushPrefs` do web | VERMELHO nos DOIS guardiões (novo + paridade) |
| 4c | `nf.enabled &&` no Toggle de `rowPushClasse` | VERMELHO (2 asserções) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Três guardiões acusariam a própria explicação**

- **Found during:** Tasks 2 e 3, ao rodar os guardiões pela primeira vez
- **Issue:** É a mesma classe de defeito que o 260824-i45 documentou em
  `test_notif_pregao.mjs`, e apareceu **três vezes**: (a) o comentário do quadro
  de autoridade continha o literal `gatilho: true`, que `test_didatica_parity
  .mjs:83` assere como AUSENTE; (b) o comentário do agendador do web continha o
  literal `_agendarSyncPrefs();`, inflando de 7 para 8 a contagem que o critério
  de aceite trava; (c) o comentário do `enviar.notif` continha o literal
  `enviar.notif = c.notif`, cuja ausência é justamente a asserção.
- **Fix:** Os três comentários foram **reescritos preservando o argumento**
  (nenhuma explicação foi removida), e cada um passou a dizer por que a forma
  literal não aparece ali. Nenhum guardião foi relaxado.
- **Files modified:** `web/src/persistence.js`
- **Commit:** bde6a76

**2. [Rule 1 - Bug] Critério de aceite `rowOptIn == 2` × instrução do próprio plano**

- **Found during:** Task 3, na conferência dos greps
- **Issue:** O plano manda (item 1) escrever um comentário nomeando os TRÊS
  helpers, e ao mesmo tempo trava `grep -c 'rowOptIn' web/src/App.jsx` em 2 —
  o comentário mandado levava a contagem a 3. O plano já tinha previsto essa
  armadilha para `rowPushClasse` ("NÃO use igualdade porque o comentário contém
  a palavra") e não a aplicou a `rowOptIn`.
- **Fix:** O comentário passou a referir o helper de opt-in **descritivamente**
  ("a variante OPT-IN logo acima, a do gatilho"), preservando a explicação dos
  três mestres e mantendo o critério em 2 exatos. O guardião novo, mais
  preciso, conta `rowOptIn` sobre o código SEM comentários — o invariante real
  ("a classe antiga não regrediu") fica travado nas duas formas.
- **Files modified:** `web/src/App.jsx`, `web/tests/test_notif_classes_ui.mjs`
- **Commit:** 94ff07c

### Drift entre o plano e o HEAD (reportado, não ajustado para passar)

Dois valores de `HEAD` no plano não batiam com o repositório. **Nenhum foi
alterado para fazer o critério passar** — em ambos, o invariante que o critério
mede continua verificado com o valor REAL:

1. `grep -c '_agendarSyncPrefs();' web/src/persistence.js` — o plano diz
   `6 → 6`; o HEAD real é **7** (linhas 560, 590, 677, 1083, 1124, 1135, 1167 —
   a definição na 489 não casa o padrão de chamada). O critério é de
   INVARIÂNCIA ("o agendador do web não infla a contagem do deviceStore") e está
   satisfeito: **7 antes, 7 depois**, e o guardião novo trava `=== 7`.
2. `grep -c 'protecao-opcao' server/app/push.py` — o plano diz `0 → 1`; o real é
   **2**, porque o próprio plano manda citar o caso da opção dentro do docstring
   de `classe_do_evento` (item 3). A ocorrência extra é a explicação exigida,
   não uma segunda tabela.

## Consequências conhecidas e bounded (registradas, sem mudança de semântica)

**1. O carimbo `at` é renovado por um patch só-de-classes.** `set_prefs` sempre
grava `at`, então um sync vindo do web renova a validade de 7 dias do `universo`
que o APARELHO gravou (`universo_valido`). Efeito real: conta ativa no web
mantém válido o universo do aparelho. Não é perda de segurança relevante — o
universo em si não é sobrescrito, e aparelho que sumiu tem o token descartado
pelo próprio APNs (`_DROP_TOKEN_REASONS`). **Nenhuma mudança de semântica do
`at` foi inventada para isto**, como o plano determinou.

**2. Status quo mantido: ligar/desligar `gatilho` pelo web não altera o push.**
Altera só `config.notif` no servidor. Já era assim antes desta entrega. Fechar
exigiria decidir quem é a fonte da verdade do `config` num app local-first —
decisão de arquitetura, não de quick task.

**3. Offline, o sync de prefs do web é best-effort e não entra na outbox.** Se a
rede cair, o `putConfig` é enfileirado e reaplicado ao reconectar, mas o
`syncPushPrefs` não — ele volta a valer no próximo toque em qualquer controle de
notificação com rede. É a mesma característica (e o mesmo comentário) do
`_agendarSyncPrefs` do deviceStore. Sem risco de clobber no caminho: online,
`sync.mutate` já grava no cache o estado RECONCILIADO pelo servidor (que faz
merge de `notif` por chave) e `readState()` refaz a leitura no servidor, então o
corpo do sync nunca é montado sobre o patch otimista raso.

## Verificação executada

- `bash scripts/executar.sh --testes` — **as duas suítes**: **1412 pytest passed,
  1 skipped** (baseline do irmão era 1390 + 1; +22 do arquivo novo) e **105/105**
  guardiões `web/tests/*.mjs`, zero falhas.
- `cd web && npx vite build` — exit 0 (rodado após Task 2 e após Task 3).
- **Diff VAZIO confirmado** (`git diff 8fbe737 HEAD --`) nos arquivos que não
  podiam mudar: `server/app/timing_watch.py`, `server/app/skill_ref.py`,
  `server/app/main.py`, `web/src/notify.js`, `web/src/copy.js`,
  `web/src/catalog.js`, `web/tests/test_api_parity.mjs`.
- Critérios de aceite por grep das três tasks conferidos contra HEAD e contra o
  esperado — todos batem, com as duas divergências de HEAD reportadas acima.
- Nenhum script de publicação foi executado (`bump.sh`, `publicar-web.sh`,
  `entregar.sh`, `cap sync ios`).

## Limitações conhecidas / pendências para o Alex

**Nenhum push foi recebido num aparelho.** Os testes cobrem PREFERÊNCIA e
PAYLOAD, não ENTREGA. A confirmação ao vivo pedida é específica: **desligar
"Proteção" no iPhone, deixar um stop ser acionado, e conferir as duas coisas** —
o banner NÃO chega, e o evento continua aparecendo em "EVENTOS E AVISOS
RECENTES". É esse par que prova que a preferência silencia a interrupção sem
apagar o rastro.

**Publicação é passo separado, não foi feita.** As mudanças de backend (Task 1 e
as partes de `store.py`/`defaults.py` da Task 2) valem assim que o Railway subir.
As de front (Tasks 2 e 3) exigem `bump.sh` → `publicar-web.sh` para o web, e
build novo (TestFlight) para o iPhone. **Enquanto o front não for publicado, os
interruptores não existem na tela** — mas o backend já respeita as preferências,
e o default LIGADO garante que ninguém perde aviso nesse intervalo.

## Self-Check: PASSED

Arquivos criados conferidos no disco: `server/tests/test_push_prefs_classes.py`,
`web/tests/test_push_prefs_classes.mjs`, `web/tests/test_notif_classes_ui.mjs`.
Commits conferidos em `git log`: `b31b240`, `bde6a76`, `94ff07c`.
