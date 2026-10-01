---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 05
subsystem: card fechado v6 (front)
tags: [carteira, cartao_posicao, App.jsx, guardiao]
requires: ["46-01", "46-02", "46-04"]
provides:
  - "useLeiturasPlano, ReguaPlano, FaixaVencimento, LinhaEstadoV6, CartaoPosicao (App.jsx)"
  - "web/tests/test_cartao_v6_fechado.mjs"
affects: [46-06]
requirements: [CART6-01]
key-files:
  modified:
    - web/src/App.jsx
    - web/tests/test_estrutura_card_ui.mjs
  created:
    - web/tests/test_cartao_v6_fechado.mjs
decisions:
  - "Task 1 e 2 num único commit: ambas editam o mesmo arquivo de forma entrelaçada (componentes + fiação)"
metrics:
  tasks: 2
  completed: 2026-10-01
---

# Phase 46 Plan 05: Card fechado v6 Summary

Toda posição da Carteira renderiza o card fechado v6 (cabeçalho, meta, régua stop/alvo OU faixa no vencimento, um estado, "Bóris explica" só no Estudo, rodapé abrir/fechar); aberto, o corpo é o detalhe anterior intacto.

## Commit

| Tarefas | Commit |
|---------|--------|
| 1+2 (componentes, hook, fiação, guardiões) | f704bade |

## O que mudou

- `useLeiturasPlano`: uma chamada `store.carteiraLeitura` por mudança de assinatura; preço só de `quotes[t].price > 0` (nunca preço de marcação); token monotônico + corte por `escopoSeq`; falha mantém leituras anteriores.
- `ReguaPlano`: disco "agora" só com `leitura.preco != null`; aria do backend (`reguaAria`) com fallback via `regua_aria`.
- `FaixaVencimento`: sem `cenarios` mostra só "aguardando o cálculo do app"; aria `faixaAria` do backend.
- `LinhaEstadoV6`: estado por `estadoPrincipalV6` (decisão no helper puro, não no JSX).
- `CartaoPosicao`: rodapé `aria-expanded`/`aria-controls`, `minHeight: 44`; status lendo/indisponível com `BotaoAtualizarEstrutura`.
- `CarteiraScreen`: o cabeçalho/P&L inline do ramo simples saiu (o card fechado o mostra); links Editar/Reanalisar/Histórico e painéis `histFor`/`editFor` seguem no corpo aberto.

## Verificação

`npx vite build` ok; guardiões verdes: test_cartao_posicao_espelho, test_cartao_v6_logica, test_cartao_v6_fechado (novo), test_estrutura_card_ui, test_carteira_lastro_ui, test_estrutura_card_logica, test_estrutura_card_espelho, test_ritmo_sp, test_concentracao_carteira, test_carteira_leitura_paridade.

## Deviations from Plan

**1. [Guardião atualizado, D-15]** `test_estrutura_card_ui.mjs`: as asserções da linha `role=status` ("lendo"/"indisponivel") passaram a ler `CartaoPosicao` em vez de `CarteiraScreen` (nota "Fase 46 (D-15, 2026-09-30)" no arquivo); acrescentada asserção de que `CarteiraScreen` renderiza `<CartaoPosicao`. `test_carteira_lastro_ui.mjs` e `test_ritmo_sp.mjs` não precisaram de edição. `skill_ref.py`/`copy.js` não mudaram (todas as chaves já existiam).

**2. Textos fixos na meta** (`ações · PM`, `estratégia não classificada`, `vence dd/mm (Nd)`, `Parcial`, `indisp.`) estão hardcoded em `CartaoPosicao`, como o plano descreve; não são frases do motor (sem número calculado). Candidatos a chaves de copy numa limpeza futura.

**3. Commit único** para as duas tarefas (ver decisions).

## Known Stubs

Nenhum.

## Self-Check: PASSED
