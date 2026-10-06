# Quick 261006-dvg: conta nova no iOS nasce limpa — Summary

Servidor ignora `body.seed` (`_apply_seed` só chama `ensure_defaults`) e o deviceStore deixou de enviar semente e de copiar o doc anônimo; namespace novo nasce do `state` do login via `_semearDoServidor`.

## O que mudou
- `server/app/main.py`: `_apply_seed` nunca lê `body["seed"]`; docstring registra a revogação da "decisão B" (2026-10-06). `store.py` intocado (`seed_user_from` segue como unidade).
- `web/src/persistence.js`: removidos `_localSeed` (2 stores), `_seedBody`, as linhas `body.seed` e a cópia `readKey(BASE_KEY)` em `ensure()`. Novo `_semearDoServidor(state)` nos dois stores (no-op no web; no device só grava se o namespace ainda não existe, nunca escreve em BASE_KEY) + helper `_deviceSeedFromServer` chamado após `_deviceScope` em register/login/oauth.
- Testes: novo `server/tests/test_conta_nova_nasce_limpa.py` (register/login/oauth com seed hostil + guardião estático), novo `web/tests/test_conta_nova_ios_nasce_limpa.mjs` (comportamental + estático + doc anônimo intocado). Notas datadas 2026-10-06 em `test_multiuser.py` e `test_oauth_repassa_name_e_code.mjs`; nenhuma asserção alterada/removida.

## Commits
- 7ef77e7e — fix: servidor ignora seed
- c1db8b1b — fix: cliente iOS

## Testes
- pytest test_conta_nova_nasce_limpa + test_multiuser + test_gate_cadastro: 19 passed (RED confirmado antes: 3 falhas).
- .mjs: test_conta_nova_ios_nasce_limpa, test_oauth_repassa_name_e_code, test_fase5_skill_migracao_legado, test_opcao_descoberto_store, test_carteira_nativa_sincroniza, test_fase2_portfolio: todos verdes.
- `npx vite build` ok; `npx cap copy ios` (em web/) ok. Suíte canônica NÃO rodada (orquestrador).

## Deviations from Plan
None - plan executed exactly as written.

## Limitações conhecidas
1. Namespaces já criados por adoção (ex.: conta de teste `teate@gmail.com`) não são limpos retroativamente.
2. A chave BYOK local não migra para conta nova (usuário recadastra).
3. Não há UI para importar o doc anônimo (funcionalidade nova, não pedida).
4. A regra que deixou a 2ª conta limpa na 46.1 não foi confirmada (irrelevante após a remoção).

## Self-Check: PASSED
