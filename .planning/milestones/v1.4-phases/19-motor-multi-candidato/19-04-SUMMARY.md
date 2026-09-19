---
status: incomplete
phase: 19-motor-multi-candidato
plan: 04
subsystem: publishing
tags: [publish, checkpoint-pending, human-verify, options, multi-candidato]

# Dependency graph
requires:
  - phase: 19-motor-multi-candidato
    plan: "19-03"
    provides: "CandidatoOpcao e ramo multi de PropostaDaPosicao, guardiões estáticos, suíte web verde pré-publicação"
provides: []
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - web/src/version.js
    - server/web_dist
    - server/app/main.py

key-decisions:
  - "server/app/main.py mudou 1 linha (SERVER_BUILD_ID) — sync automático do próprio scripts/publicar-web.sh, não mudança de comportamento de backend. Mesmo padrão documentado em 17-06-SUMMARY.md e 18-05-SUMMARY.md."
  - "bash scripts/executar.sh --testes falhou no sandbox padrão (27 falhas, PermissionError em ssl.create_default_context — mesma assinatura ambiental de 17-06/18-05/19-01/19-02/19-03); rerodado fora do sandbox (dangerouslyDisableSandbox, fatos apresentados via Fact-Forcing Gate) → exit 0, 2021 passed/1 skipped + web/tests/*.mjs 100% OK. Mesma resolução usada em 18-05."

requirements-completed: []

duration: ~35min (Task 1 apenas)
completed: null
---

# Phase 19 Plan 04: Publicação do motor multi-candidato e verificação humana Summary

**Task 1 completa e commitada (bump + publicação + suíte canônica verde); Task 2 é checkpoint humano bloqueante que requer o Alex ao vivo, com mercado aberto — NÃO executável por este agente. Fase permanece INCOMPLETA até resposta humana.**

## Performance

- **Duration:** ~35min (Task 1)
- **Task 2:** não iniciada — requer humano

## Task 1: Bump do carimbo e publicação de front + backend — COMPLETO

**Carimbo gerado:** `F10-20260904-01` (anterior: `F10-20260903-02`).

1. `bash scripts/bump.sh` — sem argumento, gerou o primeiro carimbo do dia (04/09).
2. `bash scripts/publicar-web.sh` — build (`vite build`, 89 módulos, exit 0) e
   publicação em `server/web_dist`. Warnings `ERROR: failed to copy trust
   settings of system certificate-25291` apareceram antes do build (mesmo
   artefato de sandbox documentado em 17-06/18-05/19-01/19-02/19-03) mas
   NÃO impediram a conclusão do build/publicação.
3. `bash scripts/executar.sh --testes` — rodado DEPOIS da publicação, com
   `server/.venv` temporariamente symlinkado do repositório principal
   (gitignored, mesmo precedente de 19-01/19-02/19-03) só para o comando de
   teste, removido antes do commit final.
   - Primeira tentativa (sandbox padrão): **27 failed, 1994 passed, 1
     skipped** — mesma lista de nomes de teste já documentada como
     pré-existente/ambiental (sandbox sem egress de rede,
     `PermissionError: [Errno 1] Operation not permitted` em
     `ssl.create_default_context`, confirmado por inspeção direta do
     traceback de `test_yahoo_granularidade.py`).
   - Rerodado fora do sandbox (`dangerouslyDisableSandbox: true`, fatos
     apresentados via Fact-Forcing Gate: nenhum arquivo modificado/deletado
     pelo rerun de testes, nenhum rollback necessário, instrução vem do
     mandato de validação do CLAUDE.md + precedente de 18-05-SUMMARY.md):
     **exit 0**, **2021 passed, 1 skipped, 370 warnings** (pytest) + TODAS
     as suítes `web/tests/*.mjs` OK, incluindo `test_opcoes_multi_candidato_ui.mjs`
     e os guardiões nomeados como intocáveis
     (`test_opcoes_proposta_ui.mjs`, `test_carteira_lastro_ui.mjs`,
     `test_opcoes_collar_ui.mjs`, `test_carteira_opcoes_tira.mjs`).
4. Confirmado os TRÊS elos do carimbo:
   - `web/src/version.js` → `BUILD_ID = "F10-20260904-01"`.
   - `server/app/main.py` → `SERVER_BUILD_ID = "F10-20260904-01"` (sync
     automático de `publicar-web.sh`).
   - `grep -rl "F10-20260904-01" server/web_dist` retornou
     `server/web_dist/assets/index-DZdG64aO.js`.

### Acceptance criteria (Task 1)

- [x] `git diff web/src/version.js` mostra `BUILD_ID` novo, formato
      `F10-AAAAMMDD-NN`, diferente de `F10-20260903-02`.
- [x] `git status --porcelain server/web_dist` mostrou 24 arquivos
      modificados/renomeados/criados/removidos (publicação de fato
      aconteceu).
- [x] Os três elos batem (ver acima).
- [x] `bash scripts/executar.sh --testes` saiu com código 0 DEPOIS da
      publicação (ambas as suítes) — fora do sandbox padrão, ver Issues.
- [x] `git diff --stat web/package.json web/package-lock.json
      server/requirements.txt server/requirements-prod.txt` vazio.
- [x] Nenhum `git push` foi executado; `git status -sb` mostra a branch
      local `worktree-agent-aeb1184d09ae27e1d` à frente do que estava em
      `origin` antes desta sessão (sem push).

## Task Commits

1. **Task 1: Bump do carimbo e publicação de front + backend** — `820b010` (chore)

## Task 2 — checkpoint humano bloqueante (NÃO EXECUTADO)

**Status: pendente. Este agente não pode completar esta task — requer o
Alex, ao vivo, com o app rodando e o mercado ABERTO.**

Texto do checkpoint, verbatim do plano `19-04-PLAN.md`:

### O que foi construído (what-built)

O motor de proposta deixou de escolher UMA estrutura por posição. Quando a
leitura técnica é de queda (VENDER/baixa) e TANTO a put de proteção QUANTO a
trava protetora cabem no caixa e no lastro, os dois candidatos passam a ser
oferecidos ao mesmo tempo, lado a lado, dentro do detalhe da posição em
Posições — cada um com a manchete do motor, o payoff próprio e o próprio botão
de aceite. Quando só uma estrutura cabe (o caso de hoje), a tela é exatamente a
mesma de antes.

O padrão visual é o MESMO da tira "Oportunidades de opções" da Fase 18 —
nenhuma cor, tamanho ou frase nova foi criada nesta fase. Nos dois branches em
que o motor já era de candidato único (venda coberta no viés de prêmio; nenhuma
estrutura no viés de alta), nada mudou.

No backend, aceitar um candidato passa a impedir a execução do irmão sobre a
mesma posição — por dois caminhos que já existiam: o lastro travado pela call
vendida e a regra "posição com lastreada aberta recebe proposta de fechamento,
não proposta nova".

### Como verificar (how-to-verify)

Rodar o app local (`bash scripts/executar.sh` ou o fluxo de dev habitual), com
mercado ABERTO — a cadeia de opções ao vivo é o que faz existir um segundo
candidato. Se nenhuma posição real tiver leitura de VENDER/baixa no dia, usar
uma conta/ativo em que o Radar esteja indicando queda; sem isso, os passos 1-5
não são exercitáveis e o checkpoint fica parcialmente pendente (registrar,
não fingir aprovação).

1. **Dois candidatos aparecem.** Em Posições, abrir o detalhe de opções de uma
   posição cuja leitura técnica seja de queda e cujo caixa comporte a put
   isolada. Esperado: DOIS cards lado a lado, roláveis com o dedo — put de
   proteção primeiro (à esquerda), trava protetora depois.
2. **Cada manchete é a do motor.** Ler as duas manchetes. Esperado: são
   DIFERENTES entre si e nenhuma delas parece montada com pedaços (nada de
   frase truncada com "..."). Comparar a manchete do primeiro card com a que
   aparece para o mesmo ativo na Watchlist: TEXTO IDÊNTICO. Divergência é bug de
   guardrail CVM — reprovar.
3. **Cada card tem payoff próprio.** Esperado: ganho máximo, perda máxima,
   breakeven e caixa DIFERENTES entre os dois cards (são estratégias
   diferentes); nenhum campo mostrando "R$ 0,00" onde deveria estar vazio/"—".
4. **Um candidato só continua igual.** Abrir o detalhe de uma posição em que só
   uma estrutura é elegível. Esperado: o card único de sempre, sem linha de
   rolagem, visualmente idêntico ao de antes desta fase.
5. **Aceite em Modo Operador.** Com o app em Modo Operador, tocar o CTA do
   SEGUNDO card (a trava protetora). Esperado: a confirmação cita a trava do
   lastro; a operação abre as DUAS pernas juntas; enquanto está em voo, o botão
   do outro card também fica desabilitado.
6. **O irmão não executa depois.** Logo em seguida, tocar o CTA do primeiro card
   (a put). Esperado: NÃO abre nada — aparece a mensagem de erro no rodapé
   ("Lastro insuficiente..."). A carteira continua com as duas pernas do collar,
   sem uma terceira posição de opção.
7. **Ordem inversa.** Em outra posição (ou depois de encerrar as pernas),
   aceitar primeiro a put e depois tentar a trava protetora. Esperado: a
   segunda tentativa é recusada com a mensagem de que já existe operação
   lastreada aberta naquela posição.
8. **Modo Estudo.** Trocar para Modo Estudo e reabrir o detalhe com dois
   candidatos. Esperado: os dois cards continuam aparecendo, cada um com a
   frase didática, e NENHUM botão de executar em nenhum dos dois.
9. **iPhone.** Repetir 1, 2 e 5 no aparelho. Esperado: os dois cards rolam
   horizontalmente com o dedo, os botões são tocáveis sem precisar mirar, e a
   manchete não sai cortada em nenhum dos dois.
10. **Risco herdado — decisão sua.** Publicar/empurrar a Fase 19 leva junto os
    fluxos das Fases 17 e 18, que seguem sem checkpoint aprovado (detalhe em
    `<risco_herdado>` do plano e em `.planning/STATE.md`). Escolher:
    (a) aprovar e empurrar as três fases juntas; (b) aprovar a Fase 19 e segurar
    o push até fechar 17/18 ao vivo; (c) reprovar e listar o que corrigir antes.

### Sinal de retomada (resume-signal)

Responder "aprovado" (com a escolha a/b/c do passo 10) ou descrever os
problemas encontrados, indicando quais passos falharam.

### Critérios de aceite da Task 2 (ainda não cumpridos)

- Os 10 passos foram exercitados com o mercado aberto e o resultado de cada um
  registrado no SUMMARY (passou / falhou / não aplicável, com o motivo).
- O passo 2 (manchete de cada candidato idêntica à do motor, e a do primeiro
  card idêntica à da Watchlist) passou — divergência aqui é reprovação
  automática, sem exceção.
- Os passos 6 e 7 (as duas ordens de aceite do irmão) foram exercitados; se a
  segunda aceitação tiver SUCEDIDO em qualquer das ordens, é reprovação —
  MULTI-02 critério 3 não foi cumprido.
- A decisão sobre o risco herdado das Fases 17/18 (a/b/c) está registrada
  literalmente no SUMMARY e em `.planning/STATE.md`.
- Nenhum push para `origin` aconteceu antes da resposta do humano.

Nenhum push para `origin` foi feito por este agente. A fase NÃO está marcada
como completa.

## Files Created/Modified

- `web/src/version.js` — `BUILD_ID` bumpado (`F10-20260903-02` → `F10-20260904-01`).
- `server/web_dist` — republicado (24 arquivos trocados/renomeados/criados/
  removidos, bundle com o ramo de N candidatos da Fase 19).
- `server/app/main.py` — `SERVER_BUILD_ID` sincronizado (sync automático de
  `publicar-web.sh`, 1 linha).

## Decisions Made

- Ver `key-decisions` no frontmatter: o diff de 1 linha em
  `server/app/main.py` é o sync de carimbo intrínseco ao
  `scripts/publicar-web.sh`, não uma mudança de backend desta fase. Mesmo
  padrão de 17-06/18-05.
- Suíte canônica rerodada fora do sandbox padrão após falha ambiental
  confirmada por inspeção direta do traceback (`PermissionError` em
  `ssl.create_default_context`) — mesma resolução aplicada em 18-05, com
  fatos apresentados via Fact-Forcing Gate antes da execução.

## Deviations from Plan

Nenhuma no sentido das Regras 1-4 (nenhum bug corrigido no código de produto,
nenhuma funcionalidade crítica adicionada, nenhuma decisão arquitetural). Duas
notas operacionais (ambiente, não código), ambas com precedente documentado
nos planos anteriores desta fase e nas fases 17/18:

1. `bash scripts/executar.sh --testes` falhou dentro do sandbox padrão
   (27 testes com `PermissionError` — rede/socket bloqueado ao carregar
   trust settings do sistema para SSL), rerodado fora do sandbox com sucesso
   limpo (2021 passed/1 skipped + web 100% OK).
2. `server/.venv` (gitignored, ausente no worktree) foi temporariamente
   symlinkado do repositório principal só para rodar o pytest, removido
   antes do commit — nenhum artefato de ambiente commitado (confirmado por
   `git status --short` limpo pós-remoção e pós-commit).

## Issues Encountered

- `bash scripts/executar.sh --testes` dentro do sandbox padrão: 27 falhas por
  `PermissionError: [Errno 1] Operation not permitted` em
  `ssl.create_default_context` (ex. `test_benchmark_ibov.py`,
  `test_yahoo_intraday.py`, `test_yahoo_granularidade.py`,
  `test_options_provider_yahoo.py`, `test_texto_vazio.py`,
  `test_fase3_kill_switch_duracao.py`, `test_push_registro_evento.py`,
  `test_opcoes_lastreadas_rotas.py`, `test_rotas_fase4.py`) — restrição de
  rede/certificado do sandbox, confirmada por inspeção direta do traceback,
  não relacionada a nenhuma mudança deste plano ou da Fase 19. Resolvido
  reexecutando fora do sandbox.
- `bash scripts/publicar-web.sh` emitiu ~10 linhas de
  `ERROR: failed to copy trust settings of system certificate-25291` antes
  do build — mesmo artefato de sandbox (certificados/cache root-owned) já
  documentado nos planos anteriores, sem impedir a conclusão do
  build/publicação.
- Worktree foi criado a partir de uma base desatualizada (commit `0b9ead1`,
  anterior a `docs(19): marca 19-03 completo no ROADMAP`) — mesmo padrão
  sistemático reportado em 19-01/19-02/19-03-SUMMARY.md (terceira/quarta
  ocorrência em sequência). Corrigido com fast-forward verificado
  (`git merge-base --is-ancestor HEAD 54d3cf8` confirmou ancestralidade,
  `git status` confirmou working tree limpo antes do reset) para
  `54d3cf84305f169ccd7b3d22facba7cdba0aca22`, conforme instruído no
  `worktree_branch_check` deste prompt de execução. Nenhum trabalho local foi
  perdido — a recomendação de `worktree.baseRef: "head"`, já registrada nos
  3 planos anteriores, segue válida e aparentemente ainda não aplicada.

## User Setup Required

**Ação necessária do Alex antes de qualquer push:** rodar o roteiro de 10
passos do Task 2 (app local publicado com o carimbo `F10-20260904-01`, mercado
ABERTO, incluindo passo no iPhone) e responder explicitamente à decisão a/b/c
sobre publicar junto os fluxos das Fases 17 e 18 (ambos os checkpoints seguem
ADIADO/PENDENTE, não aprovados). Ver a mensagem de CHECKPOINT REACHED (seção
final desta resposta) para o texto completo apresentado ao orquestrador.

## Next Phase Readiness

- Task 1 completa e commitada — front publicado localmente neste worktree,
  carimbo `F10-20260904-01` coerente entre `version.js`, `SERVER_BUILD_ID` e o
  bundle em `server/web_dist`.
- Task 2 bloqueia o fechamento da Fase 19 inteira. Nenhum push feito.
  `STATE.md`/`ROADMAP.md` NÃO foram tocados por este agente — ficam a cargo
  do orquestrador após a resposta do humano, incluindo o registro da decisão
  a/b/c em `.planning/STATE.md` conforme exigido pelo critério de aceite da
  Task 2.
- Risco herdado das Fases 17/18 permanece intacto e não resolvido por este
  plano — apenas nomeado e apresentado ao humano, conforme `<risco_herdado>`
  do plano.

---
*Phase: 19-motor-multi-candidato*
*Completed: pending (Task 2 not executed)*

## Self-Check: PASSED

- FOUND: web/src/version.js
- FOUND: server/app/main.py
- FOUND: server/web_dist
- FOUND: .planning/phases/19-motor-multi-candidato/19-04-SUMMARY.md
- FOUND commit: 820b010 (Task 1)
