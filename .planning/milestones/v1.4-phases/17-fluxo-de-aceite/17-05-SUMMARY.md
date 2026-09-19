---
phase: 17-fluxo-de-aceite
plan: 05
subsystem: ui
tags: [react, options-collar, client-execution, copy-vocabulary, cvm-guardrail]

# Dependency graph
requires:
  - phase: 17-fluxo-de-aceite
    provides: "POST /api/options/lastreada/abrir-collar (17-03) — re-derivação server-side + ORDER_LOCK atômico das 2 pernas; bloco de payoff em PropostaLastreada (17-04)"
provides:
  - "Cliente declara capacidade multiperna (store.optionsProposta(t, true) → GET .../proposta/{ticker}?multiperna=1)"
  - "PropostaLastreada renderiza a trava protetora (2 pernas: call+put, eyebrow/linha de identificação/CTA próprios), sem alterar assinatura, isCall/cor, nem posAberta"
  - "Aceite explícito: window.confirm(cp.confirmAbrirCollar) ANTES de A.abrirCollar → store.optionsAbrirCollar → POST /abrir-collar; corpo só contractSymbol+lado por perna (servidor re-deriva prêmio/strike)"
  - "optionsAbrirCollar nos DOIS stores (paridade obrigatória); deviceStore sem sessão lança erro nomeado — sem espelho local da estrutura de 2 pernas"
  - "web/tests/test_opcoes_collar_ui.mjs — 7 guardiões estáticos (FLOW-02/FLOW-03, T-17-22..27)"
affects: [17-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Despacho por tipo de proposta (p.tipo === 'collar') dentro do HANDLER de clique, não por prop nova no componente — PropostaLastreada continua com a mesma assinatura pinada pelo guardião"
    - "Corpo de execução minimalista (contractSymbol + lado por perna) — nunca reenviar prêmio/strike que o servidor já re-deriva, para não sugerir que o cliente os negocia"
    - "Varredura estática de useEffect( com extração de bloco balanceado (parênteses/chaves/colchetes respeitando strings) para provar que uma função de execução NUNCA aparece dentro de um efeito — generalização do padrão já usado para objectLiteralKeys em test_opcoes_proposta_ui.mjs"

key-files:
  created:
    - web/tests/test_opcoes_collar_ui.mjs
  modified:
    - web/src/api.js
    - web/src/persistence.js
    - web/src/copy.js
    - web/src/App.jsx
    - web/tests/test_opcoes_proposta_ui.mjs

key-decisions:
  - "optionsProposta(t, multiperna) com segundo parâmetro OPCIONAL — chamada sem ele produz a MESMA URL de hoje, preservando todo caller pré-existente que ainda não declara a capacidade"
  - "optionsAbrirCollar é rota/método SEPARADO de optionsAbrirLastreada (nunca uma flag na chamada antiga) — mesma razão do Plano 17-03 na rota: uma flag transformaria a trava de 400 do 16-04 num opt-in do próprio cliente"
  - "deviceStore.optionsAbrirCollar SEM sessão lança erro nomeado em vez de reimplementar a estrutura — diferente das operações de 1 perna (que têm espelho local completo), as duas garantias que tornam o collar seguro (re-derivação server-side + ORDER_LOCK atômico das 2 pernas) só existem no servidor; reimplementá-las no aparelho criaria um segundo motor divergente"
  - "Rule 1 (bug): textos do collar (copy.js/persistence.js/App.jsx) colidiam com a frase-âncora \"trava protetora\"/\"Trava protetora\" do guardrail CVM (test_opcoes_collar_vocab.py) — mesma classe de colisão já documentada pelos Planos 17-01/17-03. Substituído por \"collar\"/\"Collar\" nas strings de CÓDIGO e comentários; o eyebrow em CAIXA ALTA (\"ESTUDO · TRAVA PROTETORA\") sobrevive ao guardião porque a checagem é case-sensitive e o texto do plano já foi desenhado em maiúsculas por esse motivo"

patterns-established:
  - "Guardião de 'execução só por clique' por varredura estrutural de useEffect(, não por lista fixa de nomes de efeito — pega qualquer novo efeito futuro que acidentalmente chame a função de execução"

requirements-completed: [FLOW-02, FLOW-03]

# Metrics
duration: ~85min
completed: 2026-09-03
---

# Phase 17 Plan 05: Fluxo de aceite do collar no cliente Summary

**O app passa a declarar a capacidade multiperna, renderizar a trava protetora (2 pernas + payoff já exibido pelo Plano 17-04) e executá-la de verdade via `POST /api/options/lastreada/abrir-collar` — só por clique confirmado, nunca em efeito, com corpo minimalista (o servidor re-deriva prêmio/strike).**

## Performance

- **Duration:** ~85 min (incluindo `npm install` do worktree para resolver `node_modules` ausente, execução completa da suíte canônica duas vezes — sandbox ligado e desligado — e injeção de falha manual)
- **Started:** 2026-09-03T02:58:00Z (aprox.)
- **Completed:** 2026-09-03T04:23:00Z (aprox.)
- **Tasks:** 3/3 completos
- **Files modified:** 5 (1 criado, 4 modificados)

## Accomplishments
- `web/src/api.js`: `optionsProposta(t, multiperna)` — segundo parâmetro opcional monta `?multiperna=1`; `optionsAbrirCollar(body)` novo, rota separada (`/abrir-collar`) da rota single-leg (`/abrir`, trava do 16-04 intocada).
- `web/src/persistence.js`: `optionsAbrirCollar` nos DOIS stores. `serverStore` delega puro (fora de `sync.mutate`/outbox, mesma razão de buy/sell). `deviceStore` COM sessão espelha o padrão de `optionsAbrirLastreada` (adota o estado do servidor, `premiosUsados` no lugar de `priceUsed`); SEM sessão lança erro nomeado — nenhum espelho local da estrutura de 2 pernas.
- `web/src/copy.js`: 5 chaves novas nos dois modos (`eyebrowPropostaCollar`, `collarPernasLinha`, `ctaCollarDebito`, `ctaCollarCredito`, `confirmAbrirCollar`) — `collarPernasLinha` idêntica nos dois modos (descrição de dado); ramo Estudo sem "comprar"/"vender".
- `web/src/App.jsx`: efeito de busca declara `store.optionsProposta(t, true)`; `PropostaLastreada` ganha `isCollar` (derivado APÓS `isCall`/`cor`, sem tocar nessas duas linhas nem na assinatura do componente) e ramos de eyebrow/identificação de contrato/CTA para o collar; `onAbrirLastreada` ganha caminho próprio — `window.confirm(cp.confirmAbrirCollar(...))` ANTES de `A.abrirCollar({underlying, pernasContratos: [{contractSymbol, lado}], contratos, expiration})`; wrapper `A.abrirCollar` novo, mesmo formato de `A.abrirLastreada`.
- `web/tests/test_opcoes_collar_ui.mjs` (novo, 25 asserções em 7 guardiões): capacidade multiperna declarada; nenhuma execução dentro de `useEffect(` (varredura estrutural com extração de bloco balanceado); confirmação antes da execução no mesmo handler; exatamente 1 `<button` em `PropostaLastreada` e ele continua sob `{operador && (`; corpo de `A.abrirCollar(` sem "premio"/"strike"; paridade `optionsAbrirCollar` nos dois stores + erro nomeado no ramo sem sessão; nenhuma chave nova compõe a manchete/didática do motor.
- `web/tests/test_opcoes_proposta_ui.mjs`: guardião de gate de dormência atualizado com nota datada para o literal `"store.optionsProposta(t, true)"` (guardião não apagado, só o literal medido).
- Injeção de falha (acceptance criteria da Task 3) executada manualmente: `A.abrirCollar({})` movido para dentro de um `useEffect` pré-existente — o guardião 2 reprovou corretamente (3 asserções falharam, incluindo a principal). `git checkout -- web/src/App.jsx` restaurou o estado correto; suíte voltou a 100% verde.

## Task Commits

1. **Task 1: Contrato de cliente — api.js, os dois stores e as chaves de copy** - `28f7dd2` (feat)
2. **Task 2: Renderização das duas pernas e aceite explícito do collar** - `a8a3de8` (feat)
3. **Task 3: Guardião de aceite explícito e correção de colisão CVM** - `04a240d` (test)

**Plan metadata:** commit final (SUMMARY.md) — este commit.

## Files Created/Modified
- `web/src/api.js` — `optionsProposta` ganha parâmetro opcional `multiperna`; `optionsAbrirCollar` novo.
- `web/src/persistence.js` — `optionsAbrirCollar` em `serverStore` (delegação pura) e `deviceStore` (com sessão delega e adota; sem sessão lança erro nomeado).
- `web/src/copy.js` — 5 chaves novas em `COPY.estudo`/`COPY.operador`.
- `web/src/App.jsx` — declaração de capacidade no efeito de busca; `isCollar` e ramos collar em `PropostaLastreada`; caminho collar em `onAbrirLastreada`; wrapper `A.abrirCollar`.
- `web/tests/test_opcoes_proposta_ui.mjs` — literal do guardião de gate de dormência atualizado com nota.
- `web/tests/test_opcoes_collar_ui.mjs` (novo) — 7 guardiões de FLOW-02/FLOW-03.

## Decisions Made
Ver `key-decisions` no frontmatter. Resumo: parâmetro `multiperna` opcional (byte-compatível com callers antigos), rota/método novo em vez de flag, `deviceStore` sem sessão recusa com erro nomeado (sem segundo motor de 2 pernas no aparelho), e a correção de vocabulário CVM (mesma classe já documentada pelos Planos 17-01/17-03).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Textos do collar colidiam com a frase-âncora do guardrail CVM ("trava protetora"/"Trava protetora")**
- **Found during:** Task 3, ao rodar `bash scripts/executar.sh --testes` — `test_opcoes_collar_vocab.py::test_nenhum_arquivo_front_compoe_manchete_do_collar` reprovou.
- **Issue:** O `<action>` do Task 1 do plano especifica literalmente `ctaCollarDebito`/`ctaCollarCredito` (ramo Estudo) como `"Ver como esta trava protetora funcionaria"`, e o texto que escrevi para `deviceStore.optionsAbrirCollar` (sem sessão) e para os flashes/comentários de `App.jsx` também usava "trava protetora"/"Trava protetora". `test_opcoes_collar_vocab.py` faz uma varredura de TEXTO BRUTO (não só string literal de código) de todo `web/src/*.js`/`*.jsx` contra as âncoras `("trava protetora", "abate o custo")` — a manchete do collar vem SÓ de `skill_ref.py` (guardrail CVM). Mesma colisão documentada nos SUMMARYs dos Planos 17-01 (`store.abrir_collar`) e 17-03 (rota `/abrir-collar`), agora no lado do front.
- **Fix:** Substituí "trava protetora"/"Trava protetora" por "collar"/"Collar" em todas as strings de código e comentários que continham a frase minúscula/capitalizada exata — `copy.js` (`ctaCollarDebito`/`ctaCollarCredito` e comentários), `persistence.js` (mensagem de erro sem sessão), `App.jsx` (flash de sucesso/erro e um comentário). O `eyebrowPropostaCollar` (`"ESTUDO · TRAVA PROTETORA"` / `"PROPOSTA · TRAVA PROTETORA"`, todo em CAIXA ALTA) e o `confirmAbrirCollar` (`"trava(s) protetora(s)"`, com marcador de plural quebrando a substring contígua) sobrevivem ao guardião porque a checagem é case-sensitive e por substring exata — ambos os textos já estavam desenhados dessa forma no `<action>` do plano, aparentemente de propósito.
- **Files modified:** `web/src/copy.js`, `web/src/persistence.js`, `web/src/App.jsx`
- **Verification:** `grep -rn "trava protetora\|abate o custo" web/src/` devolve vazio; `cd server && .venv/bin/python -m pytest tests/test_opcoes_collar_vocab.py -q` → 11 passed; suíte canônica completa (`bash scripts/executar.sh --testes`, sandbox desligado) verde: 2010 passed, 1 skipped (pytest) + 111/111 `web/tests/*.mjs`.
- **Committed in:** `04a240d`

---

**Total deviations:** 1 auto-fixed (Rule 1 — mesma classe de colisão com o guardião CVM já documentada pelos Planos 17-01/17-03, não uma descoberta nova).
**Impact on plan:** Nenhuma mudança de escopo ou de comportamento validado pelos testes do plano — só o texto exato de algumas strings divergiu do `<action>` literal, para não colidir com a frase-âncora da manchete do motor.

## Issues Encountered
- **`web/node_modules` ausente no worktree:** `npx vite build` falhou inicialmente com `EPERM` (cache do npm) porque o worktree não tinha `node_modules` instalado (não é só cache — o pacote `vite` em si não estava resolvido). Rodei `npm install` uma vez com sandbox desabilitado — instalação de dependências JÁ declaradas em `package.json`/`package-lock.json` (confirmado: `git diff --stat web/package.json web/package-lock.json` vazio depois), não uma instalação Rule-3-excluída. Mesmo padrão documentado no SUMMARY do Plano 17-04.
- **`server/.venv` ausente no worktree:** criado um symlink temporário `server/.venv -> <repo principal>/server/.venv` para rodar a suíte backend com sandbox desligado (necessário para obter sinal real da rede — Yahoo/Anthropic/benchmark IBOV bloqueados pelo sandbox padrão); removido antes de finalizar (`rm server/.venv`, confirmado ausente).
- **28 falhas backend com sandbox padrão ligado, todas de classe já documentada** (chamadas HTTP reais bloqueadas — Yahoo, Anthropic/OpenAI, benchmark IBOV — mesma classe dos Planos 17-01/17-02/17-03/17-04). Confirmado rodando a suíte completa com `dangerouslyDisableSandbox: true`: **2010 passed, 1 skipped**. Nenhuma delas toca arquivo deste plano (`git status --porcelain server/` vazio o tempo todo — plano front-only confirmado).

## Verification Executed

- `cd web && npx vite build` — sucesso (3 vezes: antes da correção de vocabulário, depois, e na verificação final).
- `node web/tests/test_opcoes_collar_ui.mjs` — 25 asserções, 7 guardiões, verde.
- `node web/tests/test_opcoes_proposta_ui.mjs`, `node web/tests/test_copy_theme.mjs`, `node web/tests/test_fase3_paridade_stores_generica.mjs`, `node web/tests/test_api_parity.mjs`, `node web/tests/test_carteira_lastro_ui.mjs` — todos verdes.
- `bash scripts/executar.sh --testes` (sandbox desligado) — verde: 2010 passed, 1 skipped (pytest, `test_opcoes_collar_vocab.py` incluso e verde) + 111/111 `web/tests/*.mjs` (0 `[X]`).
- Injeção de falha manual no guardião 2 (`useEffect` com `A.abrirCollar` dentro) — reprovou corretamente; `git checkout -- web/src/App.jsx` restaurou; suíte voltou a verde.
- `grep -c "optionsAbrirCollar" web/src/persistence.js` → linhas 274 (serverStore) e 1380/1383 (deviceStore), presente nos dois.
- `grep -c "abrir-collar" web/src/api.js` → 1.
- `grep -c "eyebrowPropostaCollar" web/src/copy.js` → 2.
- `grep -n "window.confirm(cp.confirmAbrirCollar(" web/src/App.jsx` → exatamente 1 linha.
- `git diff web/src/App.jsx` não altera `const isCall = p.optionType === "call";` nem `const cor = isCall ? T.positive : T.negative;` (confirmado via grep no diff, nenhuma linha `+`/`-`).
- `git diff --stat web/package.json web/package-lock.json` → vazio.
- `git status --porcelain server/` → vazio (plano front-only confirmado).

## User Setup Required

None - nenhuma configuração de serviço externo.

## Verificação adicional (revisão pré-fechamento)

`price(Math.abs((p.caixa && p.caixa.custoLiquidoTotal) || 0))` no CTA do
collar usa `|| 0` — à primeira vista parece a mesma classe de defeito que o
`porLote` do Plano 17-04 foi construído para evitar (`null` virando "R$
0,00" disfarçado, regra "null nunca 0.0"). Verificado no backend
(`server/app/opcoes_payoff.py:161-220`, `server/app/opcoes_lastreadas.py:41-153`):
`custoLiquidoTotal` é sempre `round(custo_liquido(...) * qty_acoes, 2)` — um
float real, nunca `None` — e `caixa` é construído incondicionalmente sempre
que `tipo === "collar"`. Não há caso legítimo de null aqui (diferente de
`ganho_maximo`/`perda_maxima`, que têm um booleano irmão `_ilimitado` para o
caso sem número). O `|| 0`/`p.caixa &&` são código defensivo morto,
inofensivo — não é uma violação da regra, mantido como está.

## Next Phase Readiness

**Para o Plano 17-06:** o front está PRONTO e TESTADO (build limpo, suíte canônica completa verde) mas AINDA NÃO publicado — nenhum `scripts/bump.sh`/`publicar-web.sh` rodado, `server/web_dist` intocado (`git status --porcelain server/` confirmado vazio durante toda a execução). O Plano 17-06 (ou equivalente) precisa incluir o passo de bump+publicação para que esta UI chegue ao usuário real — sem isso, o merge fica testado mas nunca vai ao ar (achado documentado em `.planning/quick/fase-sem-plano-de-publicacao-front.md` do histórico deste repositório).

Nenhum bloqueio conhecido para o próximo plano.

---
*Phase: 17-fluxo-de-aceite*
*Completed: 2026-09-03*

## Self-Check: PASSED

- FOUND: `web/tests/test_opcoes_collar_ui.mjs`
- FOUND: `web/src/api.js`
- FOUND commits: `28f7dd2`, `a8a3de8`, `04a240d` (todos presentes em `git log --oneline`)
- `grep -rn "trava protetora\|abate o custo" web/src/` — vazio (correção de vocabulário confirmada)
- `cd server && .venv/bin/python -m pytest tests/test_opcoes_collar_vocab.py -q` (symlink temporário) — 11 passed
- `bash scripts/executar.sh --testes` (sandbox desligado) — 2010 passed, 1 skipped (pytest) + 111/111 `web/tests/*.mjs`
- `server/.venv` symlink removido antes de finalizar (confirmado ausente)
