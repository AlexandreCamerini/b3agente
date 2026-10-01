---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 06
subsystem: card aberto v6 (front)
tags: [carteira, cartao_posicao, App.jsx, guardiao, flip]
requires: ["46-05"]
provides:
  - "SeletorFace, AreaFlip, FaceAcao, BlocoBorisIA, HistoricoAnalises, EditorStopAlvo (App.jsx)"
  - "pctDoCapital, totalDaCompra (helpers nomeados)"
  - "web/tests/test_cartao_v6_aberto.mjs"
affects: [46-07, 46-08]
requirements: [CART6-02]
key-files:
  modified:
    - web/src/App.jsx
    - web/tests/test_estrutura_card_ui.mjs
    - web/tests/test_carteira_lastro_ui.mjs
  created:
    - web/tests/test_cartao_v6_aberto.mjs
decisions:
  - "Tasks 1 e 2 num único commit (718e86f6): mesmo arquivo, edição entrelaçada (CartaoPosicao passa a montar o corpo)"
metrics:
  tasks: 2
  completed: 2026-10-01
---

# Phase 46 Plan 06: Card aberto v6 Summary

Card aberto de toda posição: seletor `Ação | Opções (n)` (só com pernas), flip 3D só da área abaixo do seletor com movimento reduzido lido na hora da troca, face Ação (plano, fatos do backend, compras com nota de PM), face Opções (evolução de `CardPosicaoEstruturada`) e bloco BÓRIS IA com saída aria-disabled quando 0 ações livres.

## Commit

| Tarefas | Commit |
|---------|--------|
| 1+2 (componentes, fiação, guardiões) | 718e86f6 |

## O que mudou

- `AreaFlip`: `flipDuracaoMs(prefereMovimentoReduzido(window))` lido na troca; `total === 0` troca sem timer; `busy` trava, último alvo vence, timers limpos no unmount; só a face exibida é montada. Animação por keyframes (`borisFlipOut/In`) em `<style>` local.
- `FaceAcao`: R:R, distâncias e status do gatilho vêm de `leituraPlano` (o front não compara mais preço × invalidação); nota de PM = `leitura.notaPm`; compras com `totalDaCompra(h)`; `pctDoCapital` e `totalDaCompra` extraídos.
- `CardPosicaoEstruturada` (mesmo nome): ficou com avisos de liquidação, textos da faixa/descoberta, pernas, área de cenário (`sem_cenario` ou `data-area-cenario` para 46-07), fonte + Atualizar e Encerrar com todos os bloqueios da 45. Tipografia v6 (TIPO_CARD) e só `SP`.
- `BlocoBorisIA`: plano IA sempre habilitado (`ctx.openStopAlvo`), Reanalisar, Histórico, saída com `aria-disabled` + `aria-describedby` + motivo quando `qtyLivre(p) === 0` (onClick não abre o modal; `store.sell` segue recusando lastro).
- `CartaoPosicao` monta o corpo aberto (deixou de usar `children`); `HistoricoAnalises` e `EditorStopAlvo` copiam o comportamento antigo (sair do campo vazio não apaga; ✕ limpa).
- `CarteiraScreen`: bloco simples antigo, PlanRuler, links e `comprasOpen` removidos; `SellModal` ganhou a linha `apoio_saida`.

## Verificação

`npx vite build` ok. Guardiões verdes: test_cartao_v6_aberto (novo), test_cartao_v6_fechado, test_cartao_posicao_espelho, test_cartao_v6_logica, test_estrutura_card_ui, test_carteira_lastro_ui, test_estrutura_card_espelho, test_ritmo_sp, test_estrutura_card_contraste, test_concentracao_carteira, test_carteira_leitura_paridade. Não rodei o loop completo de web/tests nem `cap copy ios` (orquestrador).

## Deviations from Plan

**1. [Guardiões, D-15]** `test_estrutura_card_ui.mjs` e `test_carteira_lastro_ui.mjs` atualizados com nota "Fase 46 (D-15, 2026-09-30)": cada asserção que apontava para algo que subiu ao card fechado / FaceAcao / BlocoBorisIA foi trocada por uma equivalente no novo endereço (chip genérico na meta, R:R `L.rr`, estado sem plano do backend, SeletorFace role=group, TIPO_CARD, pctCap com vírgula, total via numDe em CartaoPosicao). `test_ritmo_sp.mjs` não precisou de edição.

**2. [Rule 2 - funcionalidade perdida] Link "Ver histórico"** (estado `encerrada`) vivia no callout que subiu ao card fechado e não foi reaproveitado em 46-05; recolocado na face Opções como botão de 44 px (`ctx.goHistoricoOperacoes`).

**3. [Rule 2] Botão `editar_plano` fora da caixa "Plano da ação"** quando a posição não tem opções mas tem stop e alvo, para não perder a edição manual (o plano só previa o botão dentro da caixa, exibida com opções).

**4. ReguaFaixa mantida sem uso** na face Opções: `test_ritmo_sp`/`test_estrutura_card_ui` a medem; removê-la exigiria reescrever esses guardiões. Candidata a remoção em 46-08. `PlanRuler` segue por ter outros chamadores. `mostraAvisoSemStop`/`mostraRR`/`valorRR` ficam importados sem uso em App.jsx.

**5. TravaPill** perdeu a superfície do card estruturado (resta 1 uso); a asserção "≥ 2 superfícies" virou "≥ 1 + estado_travadas_* + saida_motivo_lastro".

**6. `BotaoAtualizarEstrutura`** ganhou prop opcional `rotulo` (chave `atualizar` na face Opções) e tipografia 14/700.

**7. Commit único** para as duas tarefas.

## Known Stubs

`data-area-cenario` (div vazio quando há `cenarios`) é o ponto de montagem do simulador/payoff, entregue em 46-07.

## Self-Check: PASSED
