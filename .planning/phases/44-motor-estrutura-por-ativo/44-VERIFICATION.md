---
phase: 44-motor-estrutura-por-ativo
verified: 2026-09-29T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 44: Motor — estrutura por ativo — Verification Report

**Phase Goal:** o backend entrega, por ativo, todas as pernas e a leitura determinística da estrutura (resultado, faixa, estado, motivos), sem estimar nada.
**Status:** passed (initial verification)

## Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | put + call abertas retornam 2 pernas e classificam collar | VERIFIED | `estrutura_posicao.ler_estrutura` filtra TODAS as `optionPositions` do underlying; `_classificar` -> collar; `main.py:3273` chama com todas as pernas (não só `pos_op_aberta`). Testes `test_collar_ugpa3_pernas_marcacao_e_resultado`, `test_collar_aberto_volta_duas_pernas_e_nome` |
| 2 | Resultado = P&L ações + prêmio MtM; sem cotação -> `null` + incompleto, nunca 0 | VERIFIED | `_marcar` (bid/ask/last, sem mid), `_num` rejeita 0/negativo/bool; `resultado.total=None` + `incompleto` + texto quando falta perna ou ação. Testes `test_sem_ask_e_sem_last_premio_none_sem_mid`, `test_nenhum_desconhecido_vira_zero`, `test_perna_fora_da_cadeia...` |
| 3 | Faixa no vencimento bate com a conta pelos strikes; `null` se indeterminável | VERIFIED | `_faixa` via `opcoes_payoff.perfil_da_estrutura`; None para fora da biblioteca, sem ações, sem lastro, vencimentos divergentes, dados insuficientes. `test_faixa_collar_ugpa3_bate_com_a_conta_pelos_strikes` e demais |
| 4 | Gate reprovado -> `aberta_sem_proposta` (não some); motivos distintos; frases só de `skill_ref.py` com paridade em `copy.js` | VERIFIED | Eixo `abertaSemProposta`/`motivoSemProposta` (sem_mercado por perna ou motivo da rota); `skill_ref.ESTRUTURA_POSICAO` + `OPCOES_LASTREADAS` com `sem_contrato_liquido`/`sem_vencimento_elegivel` distintos (reversão deliberada D-06); espelho `copy.js estruturaPosicao` travado por `web/tests/test_estrutura_espelho.mjs` |

Estados ESTR-04 (vigente / ate_5_dias / exercicio_provavel / premio_indisponivel / vencida) com precedência testada; `encerrar` bloqueado com motivo quando prêmio indisponível/vencida (ESTR-05).

## Key Links

| From | To | Status |
|------|----|--------|
| `main.py` GET `/api/options/proposta/{ticker}` | `estrutura_posicao.ler_estrutura` | WIRED — chave aditiva `estrutura` (None sem opção aberta), try/except próprio (falha isolada não degrada proposta nem vira 500) |
| `estrutura_posicao.py` | `skill_ref.estrutura_posicao_txt` | WIRED — nenhuma frase de usuário escrita no módulo |
| `skill_ref.ESTRUTURA_POSICAO` | `copy.js estruturaPosicao` | WIRED — guardião de paridade verde |

## Requirements Coverage

ESTR-01..ESTR-06: SATISFIED (evidência acima). Nenhum requisito órfão.

## Spot-checks executados pelo verificador

- `pytest test_estrutura_posicao.py test_estrutura_posicao_rota.py test_skill_ref.py test_guardrail_imperativo.py` -> 85 passed
- `node web/tests/test_estrutura_espelho.mjs` -> todos passaram
- Suíte canônica (relato do orquestrador): pytest 3116 passed, web ok

## Anti-patterns

Sem TBD/FIXME/XXX em `estrutura_posicao.py`. Módulo puro (sem rede/banco/LLM/relógio). Nenhum bloqueador.

## Observações (não bloqueantes)

- REQUIREMENTS.md ainda marca ESTR-01..06 como `Pending`/`[ ]`; atualização é do orquestrador (fora do escopo deste verificador).
- Consumo no front (card) é Fase 45; nada disso é gap da 44.

## Human verification

Nenhuma (fase de motor puro, sem UI).

_Verifier: Claude (gsd-verifier)_
