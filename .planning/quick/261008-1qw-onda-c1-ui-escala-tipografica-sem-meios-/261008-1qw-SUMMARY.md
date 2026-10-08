---
quick: 261008-1qw
status: complete
branch: ui/diagnostico-ondas-a-d
---

# Quick 261008-1qw — Onda C1: escala tipográfica inteira

Script determinístico (Python) normalizou 343 literais de fontSize fracionário em 20 arquivos de web/src.

## Contagens (antes -> depois)
- 11.5 -> 12: 145 · 12.5 -> 13: 107 · 10.5 -> 11: 69 · 9.5 -> 10: 10 · 13.5 -> 14: 10 (8 + 2 em ternário `compact ? "12px" : "13.5px"`) · 14.5 -> 14: 1
- Extra fora da lista do plano: 8.5 -> 9 (App.jsx, `compact ? "8.5px" : "12px"`, rótulo do sweep).
- Depois: 0 fontSize fracionário literal.

## Exceções (não literais, não alteradas)
- `fontSize: "0.92em"` (markdown.jsx:35, relativo).
- `fontSize={Math.round(size * 0.26)}` (App.jsx:7873, calculado).
- `FONTE_MIN = 11.5` em opcoes/PayoffChart.jsx: constante de SVG em user-space, com orçamento de layout (PAD_E, 37-UI-SPEC) e travada por test_payoff_responsivo (piso >= 11). Fica para decisão própria; guardião não a captura (`fontSize={FONTE_MIN}`).
- Comentário em PayoffChart.jsx:51 (`fontSize="9.5"`) preservado.

## Guardiões reconciliados (nota datada 2026-10-08, asserção mantida, aceita histórico OU novo)
test_historico_rejeitada.mjs, test_disclaimer_trade_modal.mjs, test_estrutura_card_ui.mjs (allowlist de valores ampliada), test_fase21_dedup_consolidacao.mjs.

## Guardião novo
web/tests/test_ui_onda_c1.mjs (varre web/src, allowlist vazia, ignora em/rem/% e fatores multiplicativos).

## Verificação
vite build ok; ok: test_ui_onda_c1, a, b, os 4 reconciliados, payoff_responsivo, cartao_v6_transversal, fase20_fundacao_visual. Suíte completa/cap copy/push não rodados (conforme instrução).

## Riscos de quebra de linha
Texto cresce ~0,5px (~4%). Nenhum container nowrap com largura fixa de rótulo encontrado por grep (só SR_ONLY). Riscos remanescentes sem screenshot: chips/pills e tab bar com nowrap + largura intrínseca (badges 10.5->11, tabs 11.5->12), linhas flex densas em 375px, sweep compact 8.5->9. Validar visualmente.

## Commits
Ver git log (`fix(261008-1qw)` x2).
