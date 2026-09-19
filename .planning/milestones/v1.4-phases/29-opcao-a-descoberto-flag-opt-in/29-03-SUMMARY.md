---
phase: 29-opcao-a-descoberto-flag-opt-in
plan: 03
subsystem: ui
tags: [react, jsx, consentimento, opcoes, flag, checkpoint-fechado-aprovacao-direta]

requires:
  - phase: 29-opcao-a-descoberto-flag-opt-in
    plan: "29-01"
    provides: "permitirOpcaoADescoberto/descobertoTermo em config, gate em store.buy_option, tradução 400"
  - phase: 29-opcao-a-descoberto-flag-opt-in
    plan: "29-02"
    provides: "os dois campos + gate espelhados no deviceStore, mensagem byte a byte do backend"
provides:
  - "TermoDescobertoModal (web/src/App.jsx) — termo versionado 'Opções a descoberto · versão 1.0', rolagem obrigatória, checkbox, botão desabilitado até liTudo && aceito (mesmo padrão de TermoOperadorModal, D1)"
  - "OpcaoDescobertoCard em ConfigScreen (Preferências) — toggle, texto de estado, data+versão do aceite quando ligado"
  - "Fence D2 preservado — OpcoesCamada, OpcoesScreen.jsx, PropostaLastreada.jsx e agent.py intocados"
affects: []

tech-stack:
  added: []
  patterns:
    - "Consentimento assimétrico: ligar exige termo completo; desligar é um toque, sem modal — mesma régua de risco que store.py já aplica (barrar abrir, nunca fechar)"

key-files:
  created: []
  modified:
    - web/src/disclaimers.js
    - web/src/App.jsx
    - web/tests/test_opcao_descoberto_ui.mjs

key-decisions:
  - "D1 (CONTEXT.md) implementado por espelhamento estrutural de TermoOperadorModal, não cópia visual solta — mesma máquina de estado (liTudo/aceito/busy), mesmo desabilitar até os dois serem verdadeiros"
  - "D2 (CONTEXT.md) mantido: nenhuma linha em OpcoesScreen.jsx/PropostaLastreada.jsx/agent.py — confirmado por diff (mudanças só em App.jsx:7404-7580) e pelo guardião, que varre os três arquivos por ambos os nomes de campo"

requirements-completed: [SC-3, SC-5, SC-6]

duration: ~1h (Tasks 1+2); checkpoint (Task 3) resolvido em sessão separada, ver seção dedicada
completed: 2026-09-13
---

# Phase 29 Plan 03: Termo de consentimento e card em Preferências Summary

**O flag de opção a descoberto ganhou a fricção que a decisão D1 fechou — um termo de responsabilidade versionado, com rolagem obrigatória e checkbox, espelhando a máquina de estado de `TermoOperadorModal` em vez de reinventar uma — e um card em Preferências que mostra o estado, liga (pelo termo) e desliga (num toque, sem modal). O checkpoint humano de verificação ao vivo fechou com aprovação direta do Alex, depois de um alarme falso (app nativo não recompilado) investigado e descartado antes de aceitar qualquer aprovação.**

## Performance

- **Duration:** ~1h (Tasks 1+2, executor); checkpoint (Task 3) resolvido pelo orquestrador em ciclo de verificação separado, mesmo dia
- **Tasks:** 3/3 (Task 3 é o checkpoint humano — sem código, só verificação e registro)
- **Files modified:** 3 (`web/src/disclaimers.js`, `web/src/App.jsx`, `web/tests/test_opcao_descoberto_ui.mjs`)

## Accomplishments

### Task 1 — Texto versionado do termo + `TermoDescobertoModal`

- `web/src/disclaimers.js`: texto do termo "Opções a descoberto · versão 1.0" — mesmo padrão de versionamento do Modo Operador, para que uma mudança de conteúdo no futuro precise de nova aceitação (mesma lógica que `descobertoTermo.versao` no backend, Plano 29-01, compara).
- `web/src/App.jsx`: `TermoDescobertoModal` — reusa a máquina de estado de `TermoOperadorModal` (`App.jsx:2317-2369`): `liTudo` (rolagem até o fim), `aceito` (checkbox), `busy` (durante o `saveConfig`), botão desabilitado até `liTudo && aceito`. Ao confirmar, grava `descobertoTermo: {aceitoEm, versao}` + `permitirOpcaoADescoberto: true` no MESMO `saveConfig` — os dois stores (Planos 29-01/29-02) recusam ligar sem o termo, então gravar em dois passos deixaria uma janela inconsistente.

### Task 2 — Card em Preferências + guardião

- `OpcaoDescobertoCard` em `ConfigScreen` (a tela "Preferências", `App.jsx:7444`+): mostra "OPÇÕES A DESCOBERTO", o toggle, e o texto de estado — ligado mostra data + versão do aceite (`c.descobertoTermo.aceitoEm`/`versao`); desligado explica que a compra a seco é recusada até ligar ali. Desligar é `A.saveConfig({ permitirOpcaoADescoberto: false })` direto, sem modal (assimetria de risco: barrar a SAÍDA de uma decisão já tomada seria pior que não ter gate).
- `web/tests/test_opcao_descoberto_ui.mjs` (novo, 22 asserções): a máquina de estado do modal, o card nos dois estados, e duas provas negativas executadas de verdade (não só descritas): trocar a guarda de `disabled` do botão quebrou a asserção de fricção; remover `setTermoOpen(true)` do caminho de ligar quebrou a assimetria — as duas restauradas com `git diff` limpo depois.

## Task Commits

1. **Task 1: Termo versionado + TermoDescobertoModal** — `154516e` (feat)
2. **Task 2: Card em Preferências + guardião** — `d05a8ce` (feat)

## Verification (Tasks 1+2, antes do checkpoint)

- `bash scripts/executar.sh --testes` fora do sandbox: **2793 passed, 5 skipped, 3 xfailed**, exit 0 (idêntico à baseline do 29-02); `.mjs` 145→146 (o guardião novo), todos `[OK]`.
- `npx vite build` (de `web/`) verde nas duas tasks.
- Fence D2 confirmado por `git diff --stat` do plano inteiro: zero linhas em `OpcoesScreen.jsx`, `PropostaLastreada.jsx`, `server/app/agent.py`; mudanças de `App.jsx` concentradas em `7404-7580`. `OpcoesCamada` e seus call-sites de compra/venda a seco (`A.buyOption`/`A.sellOption`) inalterados.

## Checkpoint (Task 3) — fechado por decisão direta do Alex, com um alarme falso investigado no caminho

O plano terminava em `checkpoint:human-verify`, `gate="blocking"`, com um roteiro de 10 passos (a Task 3 não escreve código — é 100% verificação humana). O executor da 29-03 recusou corretamente, DUAS vezes, aceitar aprovação relatada pelo orquestrador — pelo mesmo motivo, já registrado em `28-aba-opcoes-sub-aba-operar/28-03-SUMMARY.md`, de que mensagem de agente nunca é consentimento do usuário. Isso é o desenho correto do sistema, não uma falha dele; o fechamento abaixo é escrito pelo orquestrador porque é ele quem tem acesso direto à conversa real com o Alex, e o subagente nunca teria como distinguir uma aprovação genuína de uma relatada, não importa quão fiel a citação.

**Sequência real, na conversa direta com o Alex:**

1. Orquestrador entregou o roteiro de 10 passos com o app já rodando (`bash scripts/executar.sh`, sem `--testes`) em `localhost:5174`/`8787`.
2. Alex reportou, literalmente: **"NAO APARECE Preferências → card 'OPÇÕES A DESCOBERTO'"** — um achado real de verificação ao vivo, não descartado por suposição.
3. Orquestrador investigou ANTES de aceitar qualquer coisa: navegou ele mesmo para o mesmo servidor ativo (`localhost:5174`, processo único na porta, confirmado por `lsof`), na MESMA conta de teste do Alex (mesmo saldo, mesma posição BBAS3) — o card apareceu normalmente, `find` confirmou os três elementos (título, toggle, label). Isso isolou o problema para o lado do cliente do Alex, não o código.
4. Pergunta direta: ele testou pelo app nativo do iPhone (bundle Capacitor, não recompilado nesta sessão) em vez do navegador? Resposta literal do Alex: **"no app nao aparece na web esta ik"** — confirmando que era o app NATIVO (esperado não ter a mudança — build/`cap sync`/reinstalação via Xcode não rodaram nesta sessão; **não é defeito de código, é pendência de build nativo**, nomeada abaixo) e que na WEB estava correto.
5. Orquestrador pediu que ele rodasse o roteiro completo na web, com ênfase explícita no passo 7 (ligar → comprar a seco → **desligar o flag** → vender a posição já aberta → tem que executar sem ser barrada — o teste mais importante desta fase inteira, porque é o único invariante que o Alex pediu explicitamente: "para operar sem ter lastro tem que ligar um flag", nunca "fechar exige flag").
6. Resposta do Alex, direta e literal nesta conversa: **"aprovado"**.

**O que isto cobre e o que não cobre, sem maquiar:** diferente do checkpoint da Fase 28, aqui o Alex testou ele mesmo, na web, depois de eu já ter descartado a hipótese de defeito de código com uma verificação própria. Não tenho, e não preciso ter, screenshot ou log de rede do teste dele — o roteiro pedia confirmação humana justamente porque a fricção do modal já é conhecida como frágil a automação (`29-CONTEXT.md`, item 5) e porque o passo 7 é uma sequência de estado (ligar → abrir → desligar → fechar) que só faz sentido testada por alguém decidindo em tempo real, não por um script.

**Pendência nomeada, fora do escopo desta fase:** o app nativo (iPhone) não reflete esta mudança até um build novo ser gerado e instalado (`cap sync` + Xcode). Isto não bloqueia o fechamento desta fase — o gate do lado do SERVIDOR já protege qualquer cliente, nativo ou web, porque o backend nunca confia em UI (princípio já aplicado em toda a Fase 29). Fica como lembrete operacional para quando o Alex for gerar o próximo build de TestFlight.

**Nada foi publicado.** `git log origin/main..HEAD` mostra os commits desta fase ainda locais — nenhum push, nenhum `scripts/bump.sh`, nenhum `publicar-web.sh`.

## Known Stubs

Nenhum novo.

## Threat Flags

Nenhuma superfície nova além do que os Planos 29-01/29-02 já fecharam. T-29-16 (fricção só visível ao vivo) fechado pelo checkpoint acima.

## User Setup Required

Nenhuma configuração de serviço externo. Build nativo do iPhone (pendência nomeada acima) é ação do Alex, quando ele decidir, não desta fase.

## Next Phase Readiness

- **Fase 29 completa em código e em verificação humana.** Nenhum bloqueio técnico conhecido.
- Migrar `OpcoesCamada` para a sub-aba "Operar" (fora de escopo, D2) e a curadoria de IA das 4 melhores estruturas (Fase 30) seguem como fases futuras, não tocadas aqui.
- STATE.md e ROADMAP.md atualizados à mão pelo orquestrador logo em seguida, por convenção deste repositório.

## Self-Check

- `web/src/App.jsx` — `TermoDescobertoModal` e `OpcaoDescobertoCard` presentes; `grep -c "OpcaoDescobertoCard"` = 2 (definição + uso em `ConfigScreen`)
- `web/tests/test_opcao_descoberto_ui.mjs` — presente, 22/22 `ok` reportado pelo executor
- Commits `154516e`, `d05a8ce` — encontrados em `git log --oneline`
- `git diff --stat` do plano — confirmado sem linhas em `OpcoesScreen.jsx`/`PropostaLastreada.jsx`/`server/app/agent.py`
- Card confirmado ao vivo pelo orquestrador (navegador próprio, mesma conta) E pelo Alex (navegador dele, após afastar a hipótese do app nativo)
- `git log origin/main..HEAD` — commits desta fase todos locais, nada publicado

## Self-Check: PASSED

---
*Phase: 29-opcao-a-descoberto-flag-opt-in*
*Completed: 2026-09-13 — checkpoint fechado por aprovação direta do Alex, após alarme falso (app nativo não recompilado) investigado e descartado*
