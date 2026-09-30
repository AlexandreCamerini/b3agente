---
phase: 45-card-de-posi-o-estruturada
plan: 04
subsystem: web-front
tags: [card-posicao, regua, contraste, guardioes]
requires: [45-02, 45-03]
provides:
  - "ReguaFaixa (faixa no vencimento: piso/teto/PM/hoje + stop/alvo)"
  - "Bloco de limites, Stop/Alvo, contexto e aviso sem stop no CardPosicaoEstruturada"
  - "TravaPill com prop opt-in contorno"
  - "test_estrutura_card_contraste.mjs; test_estrutura_card_ui e test_ritmo_sp estendidos"
key-files:
  created:
    - web/tests/test_estrutura_card_contraste.mjs
  modified:
    - web/src/App.jsx
    - web/tests/test_estrutura_card_ui.mjs
    - web/tests/test_ritmo_sp.mjs
requirements-completed: [CARD-02, CARD-05, CARD-06]
completed: 2026-09-29
---

# Phase 45 Plan 04: Régua de faixa, limites e contorno da pill

`ReguaFaixa` (top-level, antes de `CardPosicaoEstruturada`, fora das fatias dos guardiões) desenha a régua de 2px sem gradiente, com marcadores de forma distinta, pontas abertas ("sem piso"/"sem teto") e `role="img"` com `cp.estruturaFaixaAria`. O card ganhou caixa de limites neutra (`T.bgBase`, sem cor semântica), linha Stop/Alvo, contexto (dias, % do capital, R:R só com stop e alvo, setup de entrada) e aviso sem stop via `mostraAvisoSemStop(p, "estruturada", e)`. "definir stop e alvo" nunca é desabilitado. `TravaPill` recebeu `contorno` (default false, legado byte a byte).

## Commits

| Task | Commit | Resultado |
|------|--------|-----------|
| 1 (+ TravaPill opt-in) | 0072b619 | vite build ok |
| 2 guardiões | 2606cce0 | UI estendido, contraste novo, ritmo SP estendido |

## Deviations from Plan

**1. [Rule 3] TravaPill implementada no commit da Task 1.** As chamadas com `contorno` ficaram no mesmo commit do card (arquivo entrelaçado); a Task 2 só acrescentou os guardiões.

**2. Reversão deliberada em `test_estrutura_card_ui.mjs`.** A asserção "âncora do 45-04 presente" (do 45-03) virou "âncora consumida e `<ReguaFaixa …/>` renderizada", com nota no arquivo. Nenhuma outra asserção removida.

**3. Guardião de contraste:** o escuro declara `positive/negative` como `BRAND.green/red`; o teste resolve via objeto `BRAND` (sem afrouxar limiar). `test_ritmo_sp.mjs`: só adições (0 linhas removidas).

## Dívida conhecida

`TravaPill` legado (AtivoCard e card atual) segue com `negative` sobre `negativeTint10` fora de AA no claro. Razão medida nas 4 combinações (informativa, não assertada): dark·estudo 4.90, dark·operador 5.28, light·estudo 4.18, light·operador 4.18. O contorno do card novo mede >= 4.79 (light) e >= 5.60 (dark). Estender o contorno ao legado fica como pergunta do checkpoint 45-05.

## Guardiões realmente executados (exit 0 conferido)

node: test_estrutura_card_ui, test_estrutura_card_logica, test_estrutura_card_contraste, test_ritmo_sp, test_carteira_lastro_ui (sem diff), test_opcoes_consolidacao_ui, test_concentracao_carteira, test_carteira_opcoes_tira, test_hero_reconciliado, test_setor_toque, test_opcoes_continuidade_ui, test_opcoes_abrir_ticker, test_estrutura_card_espelho, test_cor_confiabilidade: todos 0.
pytest: `server/tests/test_opcoes_collar_vocab.py` 11 passed.
`cd web && npx vite build`: exit 0.
Não rodados (orquestrador): suíte completa, `npx cap copy ios`.

## Known Stubs

Nenhum.

## Self-Check: PASSED

Arquivos presentes; commits 0072b619 e 2606cce0 no git log; STATE.md e ROADMAP.md intocados.

## Correções pós-teste local

Teste local com UGPA3 (banco temporário) achou 5 defeitos no `CardPosicaoEstruturada`; um commit `fix(45): …` por correção.

1. Kicker "SÓ AS AÇÕES — PRÊMIOS INDISPONÍVEIS" só aparece quando o resultado das ações é numérico (`kickerResultadoSoAcoes` em `estruturaCard.js`); sem ele usa `RESULTADO DA ESTRUTURA` (chave já existente, sem mexer no par skill_ref.py↔copy.js).
2. Rótulo "hoje R$ x" da régua: encosta em `left: 0` se a posição < 30% e em `right: 0` se > 70%; centralizado no meio. `posRegua` não mudou.
3. Callout `vencida`: o link mantém o alvo de toque de 44px, mas com `margin: -SP[3] 0` para absorver a folga do texto centralizado; o vão visível segue o gap SP[2].
4. `% do capital` do card novo com vírgula (`15,0%`). O card LEGADO tem o mesmo ponto decimal (`toFixed(1)` sem replace) — fora de escopo, não alterado.
5. Zero exato neutro (`R$ 0,00`, `textMuted`, sem sinal) nas pernas, nas ações e no total via `sinalResultado`; `moneySigned` global intocado.

Guardiões: novas asserções em `test_estrutura_card_ui.mjs` (1–5) e `test_estrutura_card_logica.mjs` (1, 5), sem remover as existentes.

Verificado (exit 0): test_estrutura_card_ui/logica/contraste/espelho, test_ritmo_sp, test_carteira_lastro_ui, test_opcoes_consolidacao_ui, test_concentracao_carteira, test_carteira_opcoes_tira, test_hero_reconciliado, test_setor_toque, test_opcoes_continuidade_ui, test_opcoes_abrir_ticker, test_cor_confiabilidade, `npx vite build`, pytest `test_opcoes_collar_vocab.py` (11 passed). `skill_ref.py` não foi tocado. Não verificado visualmente após as correções (sem novo teste no navegador).

Pendentes de decisão do Alex (não mexidos): STOP duplicado no card, semântica do botão Encerrar, ask × último negócio.

## Investigação: ask × último negócio

Sintoma (teste local): o card marcou a call vendida por R$ 0,70 (perda −R$ 250 sobre entrada R$ 0,45 × 1000) e o destino (PropostaDoAtivo em Opções) propôs recomprar a R$ 0,65 (R$ 650).

Fontes:
- Card: `server/app/estrutura_posicao.py:92-105` (`_marcar`) — perna vendida marcada pelo `ask` (R$ 0,70), comprada pelo `bid`; só cai no `lastPrice` (com `origem_last` explícita) se o lado do book faltar. Resultado da perna em `_resultado_perna` (linha ~123) usa esse `premioAtual`.
- Destino: `server/app/main.py:3207` chama `opcoes_lastreadas.proposta_fechar`, que lê `contrato.get("lastPrice")` em `server/app/opcoes_lastreadas.py:451` e calcula `premio_total = round(premio * qty_acoes, 2)` (R$ 0,65 × 1000 = R$ 650). O front (`PropostaLastreada.jsx:151,268`) só exibe `p.premioTotal` — não recalcula.
- Execução: `POST /api/options/lastreada/fechar` (`server/app/main.py:4160`) também executa a `lastPrice`. Por isso `estrutura_posicao.py:318` (`lastOk`) e o cabeçalho do módulo (linhas 31-33) exigem `lastPrice` numérico para liberar `encerrar`.

Deliberado? Sim nos dois lados, mas por decisões diferentes: D-04 da Fase 45 escolheu ask/bid para a MARCAÇÃO (custo real de sair, conservador, nunca mid); a proposta/execução de fechamento é anterior (Fases 30-44) e sempre usou o último negócio, que é o preço que o simulador de fato executa. A divergência é a diferença ask − last (R$ 0,05/ação = R$ 50); o card mostra "quanto custaria sair pelo book", o destino/execução "o que o simulador cobra". Não é bug de cálculo, é dois preços de referência sem rótulo explicando.

Menor alteração que alinharia (NÃO implementada):
1. Alinhar a marcação ao executado: `_marcar` usar `lastPrice` como principal para a perna vendida (ask só como informação). Camada backend, Fase 45 (D-04 muda; guardiões `test_estrutura_posicao.py` de origem ask/bid e textos `origem_last` a reverter deliberadamente). Risco ao guardrail: baixo (continua motor determinístico, sem IA), mas perde o conservadorismo do ask e passa a valer last possivelmente velho/sem liquidez.
2. Alternativa: alinhar a execução ao ask (`opcoes_lastreadas.py:451` e `main.py:4160`). Mexe no motor de ordens e nas Fases 30-44, maior risco; não recomendado.
3. Só rótulo (segura e dentro do spec, proposta, não implementada): já existe `origemTexto`/kicker por perna; adicionar ao card uma nota curta tipo "marcada pelo preço de recompra no book (ask); o simulador fecha pelo último negócio", como chave nova no par `skill_ref.ESTRUTURA_CARD` ↔ `copy.js estruturaCard` (paridade byte a byte, vocabulário por modo), sem tocar em números.

## Decisões do Alex (checkpoint 45-05)

- M1: aprovado (24px).
- M7: aprovado.
- P4: não — sem follow-up no AtivoCard.
- Encerrar: renomeado para "Ver encerramento em Opções…" (aria "Ver encerramento de {ticker}: abre a aba Opções em {ticker}"); copy neutra em `copy.js` nos dois modos, sem promessa de fechar as duas pernas; guardião de espelho atualizado; estado bloqueado/`encerrar.texto` do motor intocado. Commit ab840193.
- STOP: deduplicado — a linha STOP/ALVO é o único rótulo; `stopTexto` virou nota abaixo dela; "definir ▸" do stop sempre disponível quando sem stop. Commit 159ed8a9.
- Números (ask × último negócio): investigado (seção acima), nada alterado.

Verificado (exit 0): 17 guardiões node (estrutura_card_ui/logica/contraste/espelho, ritmo_sp, carteira_lastro_ui, opcoes_consolidacao_ui, concentracao_carteira, carteira_opcoes_tira, hero_reconciliado, setor_toque, opcoes_continuidade_ui, opcoes_abrir_ticker, cor_confiabilidade, vocabulario_opcoes, opcoes_collar_ui, api_parity), `npx vite build`, pytest test_opcoes_collar_vocab + test_estrutura_card_vocab + test_skill_ref (56 passed).
