# Quick 261006-dvf: acumulado de retorno com base errada — Summary

Base do retorno acumulado resolvida na LEITURA pela própria série de snapshots (`resolver_base_serie` / `resolverBaseSerie`, gêmeos com fixture compartilhado); `initialBudget` nunca é divisor; carimbo na escrita só quando provado (sem operação = caixa). Caso real: +10.193 % passa a ≈ +2,9 %.

## Commits
- a91ad88b — fix(dvg): reconcilia guardião de pendingOrders após remover `_localSeed` (passo zero)
- dec207fb — backend: resolvedor, regra de carimbo, fixture (11 casos)
- f5f94bd4 — front: `resolverBaseSerie`, `equityCurve`, carimbo/reset no deviceStore
- 110d25c2 — texto por origem (skill_ref ↔ copy.js) e `pet:evolucao`
- 8df99354 — CapitalCurve, Home e contexto do assistente

## Arquivos alterados
server: `app/store.py`, `app/skill_ref.py`, `app/main.py`, `tests/test_retorno_acumulado_base.py` (novo), `tests/fixtures/retorno_acumulado_casos.json` (novo), `tests/test_persistence.py`.
web: `src/finance.js`, `src/persistence.js`, `src/copy.js`, `src/App.jsx`, `tests/test_retorno_acumulado_base.mjs` (novo), `test_finance.mjs`, `test_numeros_fundamentados.mjs`, `test_vocabulario_espelho.mjs`, `test_ordens_pendentes_client.mjs`.

## Guardiões reconciliados (nota datada 2026-10-06)
- `test_ordens_pendentes_client.mjs` (passo zero, dvg): `pendingOrders` exigia >= 2 ocorrências; `_localSeed` saiu. Agora >= 1 (`deviceStore.getState`) + asserção de que `pendingOrders` está na lista de campos de `_semearDoServidor`. Os outros 3 nomes mantêm >= 2.
- `test_persistence.py` (2 testes): fixtures ganham UMA operação em `history` antes da edição do orçamento (sem operação a edição move o caixa = aporte). Asserções `[10000, 10000]` e `== 5000` inalteradas.
- `test_numeros_fundamentados.mjs`: regex do código antigo (`snaps.find`, `Number(budget)`) → prova `resolverBaseSerie(` em `equityCurve` e ausência de `Number(budget)`. REVERSÃO DELIBERADA: "sem série, o orçamento serve de base (+20 %)" → `retAcum === null && baseOrigem === "sem_serie"`.
- `test_finance.mjs`: combinações 1 e 3 — `datas` sem o `null` inicial (`primeiro_registro` não antepõe ponto-base). Reconciliação adicional não prevista no plano: caso "vazio+orçamento" (curva `[orçamento, ao vivo]` e `retAcum === 0` → curva só com o ponto ao vivo, `retAcum === null`, drawdown finito), mesma causa (orçamento como base; "null nunca zero").
- `test_vocabulario_espelho.mjs`: `RETORNO_ACUMULADO` entra em DICTS/mapa/chaves.
- `test_c09_drawdown_alerta.mjs` e `test_fase21_dedup_consolidacao.mjs`: passam SEM edição.

## Ajustes do plan-checker
1. Fixture com 11 casos (A–H + D2 + I1 base==patrimônio no 1º registro + I2 âncora sobre série legada), lidos por pytest E Node.
2. `upsertSnapshot` segue privada; `deviceStore.putSnapshot` monta `ctx {semOperacao, caixa}`. O `.mjs` extrai o fonte da função e a executa isolada (persistence.js importa Capacitor).
3. Guardiões estáticos `ec.retAcum == null ?` presente e `(ec.retAcum || 0)` ausente em App.jsx.
4. Janela reiniciada (`inicio > 0`): novo estado `carimbada_reinicio` em skill_ref ↔ copy (paridade byte a byte nos 2 modos), cita a data do capital alterado; não diz "desde o capital inicial". Exigiu `baseInicio` no retorno de `equityCurve`.

## Deviations from Plan
- [Rule 3] Reconciliação extra em `test_finance.mjs` ("vazio+orçamento"), descrita acima.
- [Rule 2] Estado extra `carimbada_reinicio` (ajuste 4 do checker) e campo `baseInicio` em `equityCurve`.

## Testes
- pytest: test_retorno_acumulado_base, test_persistence, test_patrimonio_opcao_avulsa, test_skill_ref, test_ordens_pendentes_rotas, test_pet_todas_telas, test_pet, + todos os que tocam `upsert_snapshot`/`equitySnapshots`: verdes.
- .mjs: test_retorno_acumulado_base, test_finance, test_numeros_fundamentados, test_vocabulario_espelho, test_benchmark_curva, test_api_parity, test_c09_drawdown_alerta, test_fase21_dedup_consolidacao, test_ordens_pendentes_client: verdes.
- `npx vite build` ok; `npx cap copy ios` ok. Suíte canônica NÃO rodada (orquestrador).

## Limitações conhecidas (aceitas)
1. Carimbo legado no 1º registro vindo de `initialBudget` divergente do caixa real é aceito (foi escrito quando a série começou).
2. Coincidência exata `base == patrimônio` com operação aberta vira início de janela (retorno medido desde essa data, ainda real).
3. iOS logado não envia snapshots ao servidor; `pet:evolucao` pode divergir da tela no iPhone — dívida pré-existente, fora de escopo.
4. Ligação com a quick dvg (conta nova limpa, `_localSeed` removido): já concluída; conta nova nasce sem série, logo `sem_serie` até o 1º snapshot. Séries já adotadas em contas existentes não são limpas retroativamente.
5. Snapshots históricos gravados com `base` de `initialBudget` sobre série sem base continuam no banco (nunca reescritos); o resolvedor os ignora pela regra de âncora.

## Self-Check: PASSED
