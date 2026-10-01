---
phase: 46-carteira-v6-card-de-posi-o-com-modos-estudo-e-operador
plan: 01
subsystem: vocabulário / KB
tags: [skill_ref, copy.js, kb, guardiao, carteira-v6]
requires: []
provides:
  - "CARTAO_POSICAO (por modo) e CARTAO_DIDATICA (só Estudo) em skill_ref.py + helpers"
  - "COPY[modo].cartaoPosicao, COPY.estudo.cartaoDidatica, cartaoPosicaoTxt, cartaoDidaticaTxt"
  - "6 verbetes KB: opc-lastro, opc-call-coberta, opc-teto, opc-piso, opc-equilibrio, mkt-preco-medio"
affects: [46-03, 46-04, 46-05, 46-06, 46-07]
key-files:
  created:
    - web/tests/test_cartao_posicao_espelho.mjs
    - server/tests/test_kb_verbetes_v6.py
  modified:
    - server/app/skill_ref.py
    - web/src/copy.js
    - server/app/kb.py
    - server/tests/test_skill_ref.py
    - server/tests/test_kb_catalogo.py
    - web/tests/test_estrutura_card_espelho.mjs
decisions:
  - "Marcador de termo nos parágrafos didáticos = [[id]], id = sufixo de termo_<id> (ex.: [[preco_medio]], [[call_coberta]])"
  - "Chaves sim_*/payoff_* existem nos dois modos (mesmo conjunto); Operador tem sim_* mais terso"
metrics:
  tasks: 2
  completed: 2026-10-01
---

# Phase 46 Plan 01: Contrato de texto da Carteira v6 Summary

Contrato de TEXTO do card v6 (97 chaves por modo em `CARTAO_POSICAO`, 42 em `CARTAO_DIDATICA`) em `skill_ref.py` com espelho byte a byte em `copy.js`, mais 6 verbetes de KB para os termos tocáveis.

## Tarefas

| # | Tarefa | Commit |
|---|--------|--------|
| 1 | Vocabulário v6 skill_ref ↔ copy.js + guardião de paridade | 9c546e10 |
| 2 | 6 verbetes de KB (catálogo 83→89 / 74→80) | 46a4e688 |

## Detalhes

- `skill_ref.py`: dicts no formato rígido (um par por linha, sem aspas internas), `cartao_posicao_txt(modo, chave, **dados)` (modo desconhecido/"estudo" → educacional, chave ausente → None) e `cartao_didatica_txt`. O bloco foi gerado por script a partir de uma única fonte para os dois lados, garantindo paridade byte a byte.
- `copy.js`: `cartaoPosicao` em ambos os modos, `cartaoDidatica` só no Estudo, helpers exportados ao lado de `estruturaCardTxt`. `btnEncerrarEstrutura` agora "Encerrar opção em Opções" nos dois modos (S13); `encerrarAria` inalterado.
- Guardiões: novo `test_cartao_posicao_espelho.mjs` (paridade, mesmas chaves, neutras iguais, regex proibida no Estudo, marcadores `[[id]]` resolvem, helpers). `test_estrutura_card_espelho.mjs`: asserção do botão de encerrar reescrita com nota "Fase 46 (D-15, UI-SPEC S13, 2026-09-30)" (não apagada). `test_skill_ref.py`: 5 testes novos. `test_kb_catalogo.py`: contagens atualizadas com nota.
- `test_estrutura_card_vocab.py` não referenciava o rótulo; sem alteração.
- Estudo livre de `vender/comprar/trava protetora/abate o custo/garante/certo/sempre` (call coberta descrita como "aceitou entregar as ações a R$ {teto}").

## Verificação

- pytest: test_skill_ref, test_estrutura_card_vocab, test_opcoes_collar_vocab (61 ok); test_kb_verbetes_v6, test_kb_catalogo, test_kb, test_kb_espelho, test_kb_ancoras, test_assistente_kb (65 ok); test_pet_todas_telas (29 ok).
- node: test_cartao_posicao_espelho, test_estrutura_card_espelho, test_estrutura_espelho ok. `npx vite build` ok.

## Deviations from Plan

- [Rule 1 - Bug] Primeira versão do verbete `opc-teto` usava "garantia", violando o próprio critério (sem promessa); reescrito antes do commit.
- Testes de KB adaptados à API real (`kb.verbete(id)` devolve o dict cru; texto por modo via `kb.formatar`), diferente do `kb.verbete(id, modo)` suposto no plano.

## Known Stubs

Nenhum.

## Self-Check: PASSED

Arquivos e commits 9c546e10 e 46a4e688 verificados.
