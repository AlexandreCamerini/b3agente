---
phase: quick-261001-0or-identidade-modo-opcao-c
plan: 01
subsystem: web/ui-tokens
tags: [identidade-modo, contraste-aa, tokens, faixa-modo]
key-files:
  created: [web/tests/test_contraste_tokens.mjs, web/tests/test_identidade_modo_faixa.mjs]
  modified: [web/src/App.jsx, web/src/copy.js, web/tests/test_brand_book_v2_tokens.mjs, web/tests/test_copy_theme.mjs, web/tests/test_chart_colors_theme_aware.mjs]
metrics:
  completed: 2026-10-01
---

# Quick 261001-0or: Identidade de modo, opção C

Neutros com matiz própria por modo (azul no Estudo, âmbar no Operador) nos 4 esquemas, faixa de modo de 44px no shell, e card da watchlist com borda e CTA no acento. Só UI/tokens; nenhum cálculo, server/, web_dist ou card de posição da Carteira editado.

## O que mudou

- PALETTE/MODE_OPERADOR: neutros aprovados (bgBase/bgCard/borderSubtle/borderFaint) e derivados (bgPanel, bgToast, borderDashed, borderToast, knob, navDotIdle, chartAxis do Operador). MODE_OPERADOR.dark/light definem todas as chaves de neutro.
- Claro: accent/positive/negative e tints nos hex aprovados.
- `FaixaModo` (App.jsx, antes de Ticker): item de fluxo do shell flex, fundo T.accent, texto T.onAccent, sem position/zIndex, `role="note"` + aria-label. Montada uma vez no return principal, substituiu o friso de 3px. Textos em copy.js (`faixaModoTitulo`/`faixaModoSub`) nos dois ramos.
- AtivoCard: `ehWatchlist = contexto === "watchlist"`; borderTop 3px no acento e CTA neutro "Comprar…" preenchido (opacity 0.6 se desabilitado). Radar inalterado; `const card` intacto.

## Tokens ajustados

Aprovados pelo Alex entraram como vieram, exceto os dois forçados pela medição.

| Token | Antes | Depois | Razão (pior caso) |
|---|---|---|---|
| Estudo/dark textFaint | #7f86a2 | #8189a5 | 4,49:1 sobre o novo bgCard #15203a reprovava; agora 4,66:1 (bgCard) |
| claro warn (os dois modos) | #a16207 | #9a5b06 | 4,33:1 (Estudo) / 4,29:1 (Operador) sobre bgBase reprovava; agora 4,77:1 / 4,73:1 (bgBase). Serve aos dois, sem override; warn sobre warnTint10 composto passa |
| Estudo/light accent | #1f7d76 | #1c746d | aprovado; tint10 media 4,33:1 com o antigo |
| Operador/light accent | #8a6c1c | #7f6318 | aprovado; idem 4,36:1 |
| claro positive / negative | #1c825d / #c6464c | #197a56 / #b83a41 | aprovado |

Mantidos conforme briefing: Operador/dark textFaint #7581a8 (4,51:1 sobre bgCard #1e1a12, passa no limite e o guardião confirma), accentSoft do Operador claro #7d621a.

Decisão registrada: no claro, bgPanel fica ENTRE bgBase e bgCard (#f3f7fd Estudo, #faf6eb Operador), em vez de um degrau mais escuro que a base; senão positive/accent reprovam sobre o painel.

Derivados escolhidos (não aprovados explicitamente, seguiram o ponto de partida do plano): Estudo/dark bgPanel #111a2f, borderDashed/Toast #34446c; Operador/dark bgPanel #18150e, borderDashed/Toast #4a412c, chartAxis #7d7562; Estudo/light bgPanel #f3f7fd, bgToast #1a2438, borderDashed #b9c9e6, borderToast #34425e, knob #d5e0f2; Operador/light bgPanel #faf6eb, bgToast #241f14, borderDashed #d4c59c, borderToast #4a412c, knob #e3d8b8, chartAxis #8a7f66.

## Guardiões

- Criado: `test_contraste_tokens.mjs` (10 tokens de texto x 3 superfícies x 4 esquemas, onAccent/accent, 4 textos coloridos sobre tint composto, neutros e acentos literais, painel claro entre base e card).
- Criado: `test_identidade_modo_faixa.mjs` (copy, FaixaModo, montagem única, friso removido, AtivoCard, `card` intacto).
- Atualizados com nota datada (nenhuma asserção apagada): `test_brand_book_v2_tokens.mjs` (NEUTROS, acentos claros), `test_copy_theme.mjs` (bgCard Operador #141926 -> #1e1a12), `test_chart_colors_theme_aware.mjs` (warn claro).

## Verificações

- RED confirmado antes de cada GREEN (38 falhas no contraste; 11 na faixa; 4 no card).
- Passam: test_contraste_tokens, test_identidade_modo_faixa, test_brand_book_v2_tokens, test_copy_theme, test_chart_colors_theme_aware, test_mode_operador_light_palette, test_cor_confiabilidade, test_estrutura_card_contraste, test_fase22_componentes_compartilhados.
- `npx vite build` (web/): OK.
- Sem `d,d:1` de uma casa em App.jsx/copy.js (armadilha do test_auditoria_prompts); pytest e suíte canônica não rodados (orquestrador).
- `git diff` sem server/ nem web/src/estruturaCard.js.

## Login/onboarding e a faixa

`WelcomeAuthScreen` (position fixed, inset 0, zIndex 85) e `OnboardingModal` (fixed, zIndex 80) são renderizados dentro do mesmo return principal, como overlays de tela cheia, então a faixa existe no DOM mas fica totalmente coberta por eles (não é montada nos early returns loadErr/!data, onde só aparece erro/carregando). Não há tela de login fora desse return.

## Desvios

Nenhum de regra 1-4. Nota de processo: a seção 4 (card) do guardião novo foi adicionada só na Task 3, para cada RED/GREEN ficar atômico.

## Precisa de olho do Alex

- bgPanel claro entre bgBase e bgCard (Estudo #f3f7fd, Operador #faf6eb): decisão minha para manter AA; muda o degrau visual do painel no tema claro em relação ao protótipo (onde o painel podia ser mais escuro que a base). Conferir nos 4 esquemas.
- Derivados não aprovados (bgToast, borderDashed etc., lista acima).
- Visual: BottomSheet abrindo sobre a faixa, iPhone com notch (margem negativa + env(safe-area-inset-top)).

## Limitações

Radar fora do destaque do card por escopo. `web/src/main.jsx` mantém #10121a no fallback de erro (fora do token system). `cap copy ios` não rodado.
