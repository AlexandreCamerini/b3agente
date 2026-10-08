---
quick: 261008-dgv
branch: ui/diagnostico-ondas-a-d
autonomous: true
origem: screenshots do iPhone (Modo Operador) enviados pelo Alex em 2026-10-08, após instalar a branch
---

# Quick 261008-dgv — Onda E: regressões e defeitos vistos no aparelho

Escopo SÓ de apresentação (nenhum cálculo, nenhum texto de produto novo, nenhum backend).
App.jsx nunca inteiro (Grep + offset/limit). Guardiões: reconciliar com NOTA DATADA
2026-10-08, nunca apagar asserção. Sem suíte completa, sem cap copy, sem push.

## Task 1 — valores monetários nunca quebram linha
Defeitos vistos: (a) card PETR4 da Mesa/Monitoramento mostra "R$" numa linha e "54,33" na
seguinte (preço ao lado do sparkline, ~App.jsx fonte do card de ativo, procurar o bloco que
renderiza `R$` + preço com o rótulo "Yahoo" abaixo); (b) Posições > Opções, grade de métricas:
"Perda máx." renderiza "-R$" e "21.663,00" em duas linhas; (c) "0 vigia(s)" quebra em 2 linhas
no card de carteira das Opções; (d) "+R$ 42,00 · +0,1…" cortado na faixa "em carteira".
Correção: `whiteSpace: "nowrap"` nos spans/containers de valor monetário e percentuais dessas
linhas (e `flexShrink: 0` no valor, deixando o RÓTULO ceder/quebrar), sem alterar fontSize.
Se o valor não couber numa célula de grade de 3 colunas, permitir o ROTULO da célula quebrar e o
valor encolher via `fontSize` de uma escala já existente (nunca fracionário; guardião
test_ui_onda_c1). Localize por Grep (`Perda máx`, `vigia(s)`, `em carteira`, `Yahoo`).
Guardião novo `web/tests/test_ui_onda_e.mjs` (parte 1): os 4 trechos acima têm nowrap.

## Task 2 — texto: plural e linha duplicada
(a) "1 dias" → "1 dia" (Opções, seletor de vencimento "09/10 1 dias"): localizar o formatador
(Grep `dias` em web/src/opcoes/*.jsx e copy.js; pode estar em copy.js nos dois modos — manter
paridade com server/app/skill_ref.py SE o texto vier de lá, e rodar test_skill_ref/espelho);
(b) a frase "sem piso: a queda não é limitada" aparece dentro de CADA card da escada E de novo
logo abaixo da lista (3 cards + 1 rodapé). Deixe a do card e remova a repetição do rodapé SOMENTE
se o rodapé for exatamente o mesmo texto sem informação adicional; senão registre no SUMMARY.
Cuidado: textos de Opções são travados por guardiões (test_opcoes_*); reconciliar com nota.
Guardião (parte 2): plural correto para n=1 e n>1.

## Verificação
`cd web && npx vite build`; test_ui_onda_e, test_ui_onda_a/b/c1 e todos os guardiões que a
tarefa tocar (descobrir por Grep em web/tests). Se tocar copy.js/skill_ref.py, rodar
`pytest server/tests/test_skill_ref.py -q` e o guardião de espelho. Commits
`fix(261008-dgv): ...` com a linha `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
Não commitar PLAN/SUMMARY/STATE. SUMMARY em 261008-dgv-SUMMARY.md (status: complete) listando
cada defeito, arquivo:linha e o que ficou fora.

## Fora de escopo (decisão de design pendente, listar no SUMMARY como não feito)
Pet/FAB sobrepondo conteúdo; colisão de rótulos do PayoffChart; altura do cabeçalho.
