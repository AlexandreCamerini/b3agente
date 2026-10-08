---
phase: quick-261008-iuz
plan: 01
status: complete
commits: [33b0dac4, db8ba6f7, b04ce733]
completed: 2026-10-08
---

# Quick 261008-iuz (Onda G de UI): swipe tolerante, mais largura, saída desabilitada

Swipe-back 32/50/60 com trilhos e sliders excluídos; gutter 12px (rampa até 18px) e padding lateral de cartão 16px; "Registrar saída" com 0 livres realmente `disabled`.

## Commits
- 33b0dac4 test: guardião test_ui_onda_g (RED, 45 falhas)
- db8ba6f7 fix: navStack 32/50/60, closest com `input[type="range"]`, 11 trilhos marcados, NOTA em test_ui_onda_b
- b04ce733 fix: GUTTER_X/CARD_PAD_X, wrapper com safe-area, hero-carrossel, 30 cartões, botão de saída, NOTAs em test_cartao_v6_aberto e test_cartao_v6_transversal

## Largura (375pt / 430pt)
- Container: 351px = 93,6% / 406px = 94,4% (antes 90,4% / 91,6%)
- Texto do cartão (borda 1 + CARD_PAD_X 16): 317px = 84,5% / 372px = 86,5% (antes 80,3% / 82,8%)

## Desvios
- [Rule 1] Plano dizia >= 12 trilhos; a soma por arquivo é 11 (2+1+1+2+2+1+1+1). Guardião ajustado para >= 11, com comentário.
- [Rule 3] test_cartao_v6_transversal (na lista de verificação, não na de reconciliação) proibia `disabled=` na fatia v6. Reconciliado com NOTA 2026-10-08: tolera exatamente `disabled={semLivres}`; nenhuma asserção apagada.
- Incidente: um `git stash` / `git stash pop` acidental (stash list estava vazia antes; pop imediato restaurou tudo, nada perdido).

## Verificação
- `npx vite build` ok; 13 guardiões do plano PASS; `${CARD_PAD_X}px` = 30; `@media (prefers-reduced-motion: reduce){` = 2.
- Não rodados: suíte completa, `cap copy ios`, push, publicação.

## Decisões / pendências
G-D1..G-D5 conforme o plano. CARD_PAD_X = SP[4]; mudar para SP[3] é uma linha (texto do cartão iria a ~86,7% em 375pt). `disabled` nativo tira a saída da ordem de foco do VoiceOver (motivo segue visível). Rampa do gutter entre 721–731px é intermediária.

Validação manual no aparelho: swipe a partir de ~25pt na Carteira->posição; carrossel "SETUPS NA SUA WATCHLIST" e sliders junto à borda não voltam a tela; posição 100% em lastro mostra a saída esmaecida e inerte.
