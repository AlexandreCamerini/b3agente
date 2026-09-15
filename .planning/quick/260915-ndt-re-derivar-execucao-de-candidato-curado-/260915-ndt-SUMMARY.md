---
phase: quick-260915-ndt
plan: 01
subsystem: options-trading
tags: [fastapi, options-trading, curadoria, collar, adr-026, react]

requires:
  - phase: 31-varredura-oportunidades-opcoes
    provides: "opcoes_curadoria.py (motor puro das 4 estruturas + candidatos_da_posicao), _curadoria_top (varredura cross-posição), GET /api/options/curadoria"
  - phase: quick-260915-j5l
    provides: "executarCandidato.js (despacho por tipo), confirmação inline por card em CuradoriaEstruturas"
provides:
  - "POST /api/options/curadoria/abrir-collar — execução do collar curado re-derivando pelo motor de opcoes_curadoria (nunca opcoes_lastreadas.propor())"
  - "_curadoria_scan_posicao — varredura de UMA posição extraída de _curadoria_top, reusada pela rota nova (não-regressão provada por test_opcoes_curadoria_rota.py intacto)"
  - "web/src/api.js/persistence.js — optionsCuradoriaAbrirCollar nos dois stores"
  - "executarCandidato.js despachando collar para a rota nova, com idCandidato no corpo em vez de expiration"
  - "COPY.curadoriaPremioRotulo — rótulo próprio do prêmio em reais no painel inline, distinto de curadoriaRazaoRotulo"
affects: [opcoes, curadoria, carteira]

tech-stack:
  added: []
  patterns:
    - "Rota de execução NOVA por motor de re-derivação, não flag no corpo escolhendo o motor (ADR-026 Decisão 1, extensão): o namespace da rota (curadoria/lastreada) nomeia o motor que valida"
    - "idCandidato como CHAVE de re-derivação server-side, nunca fonte de dado — servidor recalcula e procura o candidato pelo id, corpo só serve para cross-check de adulteração"

key-files:
  created:
    - server/tests/test_curadoria_collar_rota.py
  modified:
    - server/app/main.py
    - web/src/api.js
    - web/src/persistence.js
    - web/src/opcoes/executarCandidato.js
    - web/src/copy.js
    - web/src/App.jsx
    - web/tests/test_executar_candidato.mjs
    - web/tests/test_opcoes_collar_ui.mjs
    - web/tests/test_curadoria_ui.mjs

key-decisions:
  - "Rota NOVA (POST /api/options/curadoria/abrir-collar), não flag/parâmetro no corpo da rota existente — mesmo precedente ADR-026 Decisão 1 (a Fase 17 já rejeitou 'permitirMultiperna' no corpo pelo mesmo motivo: o cliente escolheria qual gate atravessar)"
  - "Re-derivação pelo motor de opcoes_curadoria (o mesmo que gerou o card), não por opcoes_lastreadas.propor() — decisão de produto do Alex, 2026-09-15, fechando a incoerência de exigir endosso técnico numa execução cujo card nasceu sem esse gate (Fase 30/D1)"
  - "expiration SAI do corpo do front (idCandidato já a carrega) — evita segunda fonte de verdade para o mesmo campo"
  - "POST /api/options/lastreada/abrir-collar fica byte a byte intocada — serve o card da proposta única, que nasceu do propor() e deve continuar exigindo o gate técnico"

requirements-completed: [QUICK-260915-NDT]

duration: ~90min
completed: 2026-09-15
---

# Quick 260915-ndt: Re-derivar execução de candidato curado pelo motor certo

**Todo collar da lista curada ("AS 4 MELHORES OPORTUNIDADES DE OPÇÕES") devolvia 409 ao ser executado porque a rota de execução re-derivava por um motor diferente do que gerou o card — rota nova re-deriva pelo motor certo (opcoes_curadoria), preservando toda a defesa anti-adulteração do ADR-026.**

## Performance

- **Duration:** ~90 min
- **Started:** 2026-09-15 (sessão contínua)
- **Completed:** 2026-09-15
- **Tasks:** 3/3
- **Files modified:** 10 (1 criado, 9 modificados)

## Accomplishments

- Diagnóstico confirmado por RED medido (não só por leitura): o mesmo cenário (Modo Operador, posição com lote livre, `setups.plano_do_resultado` devolvendo `"NÃO OPERAR"`) prova `POST /api/options/lastreada/abrir-collar` devolvendo 409 e `POST /api/options/curadoria/abrir-collar` devolvendo 200, no MESMO teste.
- `_curadoria_scan_posicao` extraída de dentro de `_curadoria_top` (mesma varredura, zero duplicação) — `_curadoria_top` passou a chamá-la; não-regressão provada por `test_opcoes_curadoria_rota.py` (15 casos) passando sem nenhuma linha editada.
- Rota nova valida, na ordem: Modo Estudo (403) → forma do corpo (400) → lastreada já aberta no underlying (409, antes de qualquer rede) → posição elegível (409) → re-derivação server-side (502 se degradada) → candidato existe e é tipo collar (409) → cross-check de contratos e `{contractSymbol: lado}` (409) → liquidez em 3 faixas (400) → execução via `store.abrir_collar` (400 em `ValueError`, atomicidade das 2 pernas preservada).
- `idCandidato` é a CHAVE de re-derivação: o corpo nunca vira número executado — `premioUnitario`/`strike`/`expiration` sempre saem do candidato recalculado. Provado por 6 guardiões de adulteração + 1 guardião estrutural via `inspect.getsource` que a fonte da rota não menciona `opcoes_lastreadas`/`.propor(` nem lê `premioUnitario`/`strike`/`expiration` do corpo (fora do docstring, que precisa citar o nome por prosa).
- Front despacha collar para `optionsCuradoriaAbrirCollar` (método novo, espelhado nos dois stores — `serverStore` delega, `deviceStore` lança erro nomeado sem sessão, mesma disciplina de `optionsAbrirCollar`); os outros três tipos (call_coberta, put_protecao, opcao_a_descoberto) continuam byte a byte.
- Painel de confirmação inline corrigido: o prêmio em reais (`money(item.premioTotal)`) tinha o rótulo da RAZÃO (`curadoriaRazaoRotulo`) do lado — em produção mostrou "prêmio / perda máxima R$ 847,00" com o card acima mostrando a razão real (77.00) sob o mesmo rótulo. `curadoriaPremioRotulo` nova, nos dois modos, resolve.

## Task Commits

1. **Task 1: rota `/api/options/curadoria/abrir-collar` + extração de `_curadoria_scan_posicao`** - `e8ccd72` (feat, TDD) — RED medido (404 nas 13 asserções novas, incluindo a prova central mostrando 409 na rota velha), GREEN 13/13 no primeiro run após a implementação
2. **Task 2: front despacha collar curado para a rota nova** - `0743a37` (feat)
3. **Task 3: rótulo próprio do prêmio no painel inline** - `3768ebd` (fix)

_Nota: Task 1 é TDD (frontmatter `tdd="true"`) — o arquivo de teste (13 casos) foi escrito e rodado em RED (13 falhas, todas 404 — a rota não existia) antes de qualquer linha de `main.py` além da extração do helper. A extração de `_curadoria_scan_posicao` foi verificada como não-regressão ANTES de escrever a rota nova (15/15 em `test_opcoes_curadoria_rota.py`), separando as duas mudanças mesmo dentro do mesmo commit._

## Files Created/Modified

- `server/tests/test_curadoria_collar_rota.py` - 13 casos: prova central (409/200 no mesmo cenário), 6 guardiões de adulteração, 6 defesas preservadas (Modo Estudo, lastreada aberta, liquidez DIFÍCIL, caixa insuficiente/atomicidade, cadeia degradada), 1 guardião estrutural por `inspect.getsource`
- `server/app/main.py` - `_curadoria_scan_posicao` (extração pura de `_curadoria_top`); `POST /api/options/curadoria/abrir-collar` nova
- `web/src/api.js` - `optionsCuradoriaAbrirCollar`
- `web/src/persistence.js` - `optionsCuradoriaAbrirCollar` nos dois stores (serverStore delega; deviceStore espelha `optionsAbrirCollar`, lança erro nomeado sem sessão)
- `web/src/opcoes/executarCandidato.js` - ramo `collar` despacha para `optionsCuradoriaAbrirCollar`, `idCandidato` no corpo, `expiration` removida da lista de campos exigidos; reversão datada da nota "ZERO método novo de store" no cabeçalho
- `web/src/copy.js` - `curadoriaPremioRotulo` em `COPY.estudo`/`COPY.operador`
- `web/src/App.jsx` - linha 4313 do painel inline: `cp.curadoriaRazaoRotulo` → `cp.curadoriaPremioRotulo`
- `web/tests/test_executar_candidato.mjs` - `storeEspiao()` com a chave nova; casos (3)/(5) atualizados com nota datada; caso novo "collar sem idCandidato lança e não chama store"; bloco de despacho sem rótulo (espiao2) corrigido para o método novo
- `web/tests/test_opcoes_collar_ui.mjs` - bloco 6b espelhando a paridade de `optionsCuradoriaAbrirCollar` nos dois stores
- `web/tests/test_curadoria_ui.mjs` - `CHAVES` 25→26 com nota datada; regras (23)/(24)/(25) novas (rótulo posicional do painel, `curadoriaRazaoRotulo` exatamente 1x, rótulos diferentes nos dois modos); header do arquivo atualizado com o novo item

## Decisions Made

- Rota nova, não flag — mesmo precedente ADR-026 Decisão 1, citado no docstring da rota nova.
- Re-derivação por `opcoes_curadoria` (a MESMA varredura que gera o card), não por `opcoes_lastreadas.propor()` — decisão do Alex fechada no `PLAN.md`, alinhada ao guardrail já existente do `CLAUDE.md` ("Stop/alvo nunca são vetados: `operar: false` é parecer, não veto").
- `idCandidato` troca `expiration` no corpo do front — o id já carrega a expiração; duas fontes para o mesmo campo divergiriam.
- Guardião estrutural isola o CORPO da função (depois do docstring, via split em `"""`) antes de comparar contra `opcoes_lastreadas`/`.propor(` — o docstring da rota PRECISA citar esses nomes em prosa (o plano exige a explicação), então checar a fonte inteira acusaria o próprio comentário explicativo.

## Deviations from Plan

**Nenhuma [Rule 1-4]** — plano executado como especificado, sem bug pré-existente corrigido, sem funcionalidade crítica faltante adicionada, sem mudança arquitetural fora do previsto.

Um ajuste de forma, registrado por transparência: o guardião estrutural do plano (`inspect.getsource` provando que a fonte "não menciona `opcoes_lastreadas.propor`") precisou de uma técnica adicional (isolar o corpo do docstring por `split('"""')`) porque a AÇÃO do plano também exige que o docstring da rota EXPLIQUE por que ela não usa `opcoes_lastreadas.propor()` — checar a string na fonte INTEIRA (docstring incluso) faria o guardião acusar a própria explicação em prosa. Medido: sem o isolamento, o guardião falhava contra a implementação correta (falso positivo); com o isolamento, passa e ainda pega uma chamada real na Task de negative proof (ver abaixo). Não é desvio de comportamento da rota, só do MECANISMO de verificação do guardião — a defesa (nenhum número do corpo, nenhuma chamada a `propor()`) é idêntica à especificada.

## Issues Encountered

Nenhum bloqueio. A extração de `_curadoria_scan_posicao` foi verificada como não-regressão em separado (`test_opcoes_curadoria_rota.py`, 15/15) antes de escrever a rota nova, isolando as duas mudanças da Task 1 — se a extração tivesse quebrado algo, o erro teria ficado óbvio antes de a rota nova entrar em cena.

## User Setup Required

None - nenhuma configuração de serviço externo.

## Verificação

**Baseline** (registrada no `260915-j5l-SUMMARY.md`, sessão anterior, antes desta quick): `2910 passed, 0 failed` (backend) + `150/150` `.mjs`.

**Final** (`bash scripts/executar.sh --testes`, `dangerouslyDisableSandbox: true` — confirmado antes que as 27 falhas do primeiro run sandboxed eram `PermissionError` em `ssl.py`, artefato de ambiente documentado, não relacionado a este plano): `2923 passed, 5 skipped, 3 xfailed, 0 failed` (backend) + `150/150` `.mjs`.

**Delta explicado:**
- Backend: +13 pytest (exatamente os 13 casos novos de `test_curadoria_collar_rota.py`; nenhum arquivo pytest pré-existente ganhou caso novo).
- Frontend: +0 arquivos `.mjs` (nenhum arquivo `.mjs` novo criado — os três arquivos tocados já existiam e continuam contados como 1 cada; as asserções novas vivem DENTRO deles).

`cd web && npx vite build` — verde (rodado após Task 2 e após Task 3).

**Prova negativa** (obrigatória pelo plano, fase sem `gsd-plan-checker`): apagado (não comentado) o bloco de cross-check `{contractSymbol: lado}` de `options_curadoria_abrir_collar` em `server/app/main.py`. Rodado `pytest tests/test_curadoria_collar_rota.py -q`:

```
FAILED tests/test_curadoria_collar_rota.py::test_perna_contractSymbol_trocado_409
FAILED tests/test_curadoria_collar_rota.py::test_lado_invertido_409
2 failed, 11 passed, 3 warnings in 3.66s
```

Confirma que os dois guardiões de adulteração que dependem especificamente desse cross-check CAEM de verdade quando a defesa some (os outros 11 casos continuam verdes porque testam outras defesas). Revertido com `git checkout -- server/app/main.py`; `git diff --stat server/app/main.py` limpo (sem saída) depois do revert; `pytest tests/test_curadoria_collar_rota.py -q` voltou a `13 passed` confirmando o revert intacto.

**Nota sobre ADR-026:** a decisão "rota nova, não flag" desta quick é uma EXTENSÃO direta do precedente já registrado em `docs/adr/026-*` (Decisão 1, citada no docstring da rota nova) — o mesmo raciocínio (um parâmetro no corpo escolhendo qual motor valida é opt-out do cliente sobre a defesa do servidor) se aplica aqui trocando "collar vs. single-leg" por "curadoria vs. lastreada" como o eixo de escolha. Não foi criado um ADR novo (fora do escopo autorizado — "considere se merece uma nota de extensão, não crie ADR novo sem pedir"); fica registrado aqui como candidato a nota de extensão do ADR-026, para o Alex decidir.

## Next Phase Readiness

**DUAS publicações pendentes, NESTA ORDEM — backend primeiro:**

1. Deploy do backend (`server/app/main.py`), com bump manual de `SERVER_BUILD_ID` (mudança só-backend, sem `scripts/bump.sh`/`publicar-web.sh`).
2. `scripts/bump.sh` + `scripts/publicar-web.sh` para o front (`web/src/api.js`, `persistence.js`, `executarCandidato.js`, `copy.js`, `App.jsx`).

A ordem importa: front novo (que já manda `idCandidato` para `/api/options/curadoria/abrir-collar`) contra um backend velho (sem a rota) trocaria o 409 de hoje por um 404 — pior, não melhor. O backend PRECISA ir ao ar antes do front.

Pendência de app nativo (não bloqueia o fechamento deste plano): o app iOS só reflete esta mudança depois de `cap sync` + build novo no Xcode.

Nenhum bloqueio para trabalho futuro. `POST /api/options/lastreada/abrir-collar`, `store.abrir_collar`, e os caminhos de venda coberta/put/opção a descoberto permaneceram intocados, como exigido pelo plano.

## Self-Check: PASSED

- `server/app/main.py` (contém `_curadoria_scan_posicao` e `options_curadoria_abrir_collar`) — FOUND
- `server/tests/test_curadoria_collar_rota.py` — FOUND
- `web/src/opcoes/executarCandidato.js` (contém `optionsCuradoriaAbrirCollar`) — FOUND
- Commit `e8ccd72` — FOUND (`git log --oneline --all`)
- Commit `0743a37` — FOUND
- Commit `3768ebd` — FOUND
- `git diff --stat 7b7737a HEAD` — exatamente os 10 arquivos de `files_modified` do plano, nenhum arquivo fora da lista
- `bash scripts/executar.sh --testes` (`dangerouslyDisableSandbox: true`) — 2923 passed, 0 failed (backend) + 150/150 `.mjs`, exit 0
- `cd web && npx vite build` — verde
- Prova negativa executada e revertida — `git diff --stat server/app/main.py` limpo após o revert

---
*Phase: quick-260915-ndt*
*Completed: 2026-09-15*
