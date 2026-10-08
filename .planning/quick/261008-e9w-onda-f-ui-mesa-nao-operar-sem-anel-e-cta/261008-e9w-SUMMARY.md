---
phase: quick-261008-e9w
plan: 01
status: complete
commits: [74080718, 82955755, e94df1df]
---

# Quick 261008-e9w: Onda F de UI

## Entregue
1. Mesa: `DECISOES_NAO_OPERAR`/`ehNaoOperar` em App.jsx; AtivoCard anula `anel` sob não operar (some anel e a linha "N% · Forte — …"); CTA "Registrar entrada…" cai para o estilo secundário; carrossel do Resumo também sem anel.
2. Opções: ganho máximo <= 0 sem fill; < 0 com nota "se exercida: perda" (`nota_ganho_negativo`, copy.js <-> skill_ref.py, nos dois modos).
3. Régua: `semAjuda` em ReguaRegime; legenda única no topo da lista do hub; detalhe mantém a sua.

## Decisões
- v === 0: trilho vazio, cor normal, sem nota.
- Linha "100% · Forte" some junto com o anel.

## Deviations
- [Rule 1/2 - acessibilidade] O plano pedia valor e nota em T.negative. O guardião existente test_opcoes_caminho_b_ui §10 proíbe `color: T.negative` em componentes (não atinge 4,5:1 como texto). Mantive o guardião intacto; o valor segue em textPrimary (o sinal "−" já o marca) e a nota "se exercida: perda" em textPrimary. Não-cor sinaliza a perda.

## "sem piso"
grep em web/src/opcoes/: sem duplicata da nota na escada (coluna por cartão via backend; `risco_pior_sem_piso` é conteúdo distinto; PayoffChart é outra tela).

## Verificação
vite build ok; test_ui_onda_a/b/c1/e/f, vocabulario_espelho, opcoes_escada_espelho, opcoes_leitura_interna_ui, opcoes_jornada_ui, opcoes_caminho_b_ui, opcoes_fluxo_render, hero_reconciliado, sinal_chip_ui, sinal_helpers, ritmo_sp: verdes. pytest test_skill_ref + test_opcoes_escada: 87 passed.

## Dívida (fora de escopo)
Ramo pós-análise (~App.jsx 4008-4037): a CTA verde "Registrar entrada · sugestão N ações" é decidida pela `recomendacao` da IA; se a IA disser "alta" com o motor em NÃO OPERAR, a contradição volta por esse caminho. Exige decidir se o motor também cala a sugestão de quantidade.
