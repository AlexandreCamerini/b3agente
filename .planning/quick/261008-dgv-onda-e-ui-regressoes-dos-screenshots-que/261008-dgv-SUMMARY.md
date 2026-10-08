---
quick: 261008-dgv
status: complete
commits: [d51b780d, 62de6fc7]
---

# Quick 261008-dgv — Onda E

## Task 1 — nowrap em valores (d51b780d)
- (a) preço do card de ativo: `web/src/App.jsx:3772` (container do preço, `flexShrink:0` + `whiteSpace:nowrap`).
- (b) "Perda máx." na grade de métricas (GradeConta): `web/src/App.jsx:5592` (valor nowrap; fonte cai de `TIPO_CARD.corpo` 14px para `TIPO_CARD.rotulo` 12px quando o texto passa de 11 caracteres; rótulo continua podendo quebrar).
- (c) "N vigia(s)": `web/src/opcoes/HubOpcoes.jsx:113`.
- (d) faixa "em carteira": `web/src/App.jsx:3819-3821` (gap 8, texto à esquerda com `minWidth:0`, resultado nowrap).

## Task 2 — texto (62de6fc7)
- "1 dias": nova chave `vencimento_dia` nos dois modos em `web/src/copy.js:939,2238` e `server/app/skill_ref.py:1317,1530` (paridade mantida); seletor em `web/src/opcoes/EscadaObjetivo.jsx:116`.
- "sem piso: a queda não é limitada": o texto do card vem da coluna `nota_sem_piso` do servidor (`opcoes_escada.py:314`), idêntico ao do rodapé. Rodapé removido de `EscadaObjetivo.jsx` (era a linha ~197).

## Guardiões
Novo `web/tests/test_ui_onda_e.mjs`. Nenhum guardião existente precisou de reconciliação: passaram test_ui_onda_a/b/c1, test_cartao_v6_camadas, test_estrutura_para_payoff, test_opcoes_{caminho_b_ui,fluxo_render,jornada_ui,nav_tres_abas_ui,universo_carteira,escada_espelho}, test_ritmo_sp, test_api_parity, test_cartao_posicao_espelho; pytest test_skill_ref + test_opcoes_escada (87 passed); `npx vite build` ok.

## Fora do escopo / não feito
- Pet/FAB sobrepondo conteúdo, colisão de rótulos do PayoffChart, altura do cabeçalho (decisão de design pendente).
- Outros "dias" sem plural tratado: `chipVence` ("dia(s)", copy.js:768/2081), `anat_prazo_dias` ("vence em {dias} dias", copy.js:1040/2338) e `App.jsx:3536` (`daysToExpiration + " dias"`). Não estavam no plano.
- `Stat` de `AnatomiaPerna.jsx` (valor monetário) não recebeu nowrap; não foi um dos defeitos citados.
