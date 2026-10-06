---
phase: 49-anatomia-da-perna
plan: 06
subsystem: front-opcoes
tags: [anatomia, posicao-total, encerrar, fallback, ssr-guardiao]
requires: [49-01, 49-02, 49-04, 49-05]
provides: [PosicaoTotal, PernasAbertas como contêiner da anatomia, excluirParaRota]
affects: [49-07]
key-files:
  created:
    - web/src/opcoes/PosicaoTotal.jsx
  modified:
    - web/src/opcoes/PernasAbertas.jsx
    - web/src/opcoes/GraficoAnatomia.jsx
    - web/tests/test_opcoes_anatomia_render.mjs
    - web/tests/test_opcoes_fluxo_render.mjs
    - web/tests/test_opcoes_caminho_b_ui.mjs
decisions:
  - "Sem rolagem programática em 'Ver sem esta perna': o guardião de consolidação proíbe scrollIntoView em web/src/opcoes/ (Pitfall 4); o painel total já fica logo acima dos cards"
  - "TRACOS exportado de GraficoAnatomia para a amostra de traço dos chips"
metrics:
  tasks: 2
  files: 6
  completed: 2026-10-06
---

# Phase 49 Plan 06: PosicaoTotal + PernasAbertas contêiner Summary

Gráfico total do ativo com chips por perna (e ações só com preço médio do motor), slider por índice da grade rotulado como hipótese e leitura com/sem a perna no preço escolhido, tudo lido do motor. `PernasAbertas` virou o contêiner posição → pernas (`useAnatomia` → `PosicaoTotal` → `AnatomiaPerna`), com a lista do 48-16 preservada como fallback e Encerrar sempre disponível.

## Commits
- ca3ea483 feat(49-06): PosicaoTotal + guardião SSR (inclui export de TRACOS)
- fdff5be5 feat(49-06): PernasAbertas contêiner + reconciliação de guardiões

## Comportamento
- Total null (vencimentos diferentes ou nada marcado): só a frase do motor, sem R$, sem slider, sem botão "Ver sem esta perna".
- `excluirParaRota(excluidas, ids)` filtra ids que já não são pernas abertas; `encerrar` limpa `excluidas`/seleção antes de `recarregar()`.
- Erro/carregando/sem store: lista do 48-16 + `anat_erro`/motivo + "Tentar de novo"; Encerrar habilitado, vetado só por `encerrar.permitido === false`.
- `motivoSemCotacao` (enum) agora vira frase `anat_hoje_*` (corrige o enum cru exibido no 48-16).

## Verificação
- test_opcoes_anatomia_render (T1-T9, C1-C9), test_opcoes_fluxo_render, test_opcoes_caminho_b_ui, test_opcoes_anatomia_stores, test_opcoes_consolidacao_ui, test_opcoes_subabas_ui e as demais varreduras do plano: verdes. `npx vite build` verde.
- Greps de aceite: `A.sellOption(` = 1; palavras proibidas = 0.
- Não rodei suíte canônica nem `cap copy ios` (conforme restrição).

## Deviations from Plan

**1. [Rule 1 - Conflito com guardião] Rolagem em `verSemEsta` removida**
- Found during: Task 2 (test_opcoes_consolidacao_ui falhou: "nenhum arquivo de web/src/opcoes/ contém scrollIntoView").
- Fix: removido o `scrollIntoView`; guardiões não se apagam. O painel total está imediatamente acima dos cards.
- Files: web/src/opcoes/PernasAbertas.jsx. Commit: fdff5be5.

**2. Guardião T7**: asserção "sem 0,00" usa `R$ 0,00` (o chip "CALL 50,00" contém "0,00"), mesma intenção, como no 49-04.

## Known Stubs / Pendências
- `OpcoesScreen.jsx` ainda NÃO passa `store`/`didatica`/`kbCatalogo`/`onAbrirVerbete` às duas montagens de `PernasAbertas` (fora de files_modified deste plano). Sem `store`, em produção o contêiner cai no fallback 48-16. A fiação é o próximo passo (49-07 ou equivalente).

## Self-Check: PASSED
