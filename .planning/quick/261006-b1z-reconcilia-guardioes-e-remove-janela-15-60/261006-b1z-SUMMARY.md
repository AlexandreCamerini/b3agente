---
phase: quick-261006-b1z
plan: 01
subsystem: opcoes
tags: [opcoes, vencimento, guardioes, janela-15-60]
requires: [261006-axi]
provides:
  - opcoes_lastreadas.prazo_elegivel (dias >= 1), sem piso de 15 nem teto de 60
  - 4 guardioes web reconciliados com `universo`
key-files:
  modified:
    - server/app/opcoes_lastreadas.py
    - server/app/opcoes_curadoria.py
    - server/app/opcoes_escada.py
    - server/app/main.py
    - server/app/skill_ref.py
    - web/src/copy.js
    - docs/adr/023-opcoes-lastreadas.md
metrics:
  completed: 2026-10-06
  tasks: 2
---

# Quick 261006-b1z: reconcilia guardioes e remove janela de 15 a 60 dias

## Commits

- cf4783cc (Task 1) test: 4 guardioes (`test_carteira_opcoes_tira`, `test_opcoes_abrir_ticker`, `test_opcoes_continuidade_ui`, `test_opcoes_nav_tres_abas_ui`) com regex aceitando `universo` e nota datada 2026-10-06 (quick 261006-axi). Nenhuma asserção removida; a intenção (mesma fonte, sem watchlist, restauração sem `escolherTicker`) é a mesma.
- 08c15d3d (Task 2) fix: remocao da janela.

## Regra de selecao dos 2 vencimentos

Inalterada, e ja nao dependia da janela: a cadeia pedida sem `expiration` devolve o vencimento futuro mais proximo; `opcoes_curadoria.proximos_vencimentos` (estritamente futuros, ordem crescente) fornece o seguinte; `VENCIMENTOS_POR_POSICAO = 2`. Nao existe prazo-alvo no codigo, entao valem os 2 vencimentos futuros mais proximos. Nenhum vencimento a mais, nenhuma chamada MyData a mais. O que mudou foi o filtro DEPOIS da busca (`propor`, `candidatos_da_posicao`, `motivo_sem_candidato`), que descartava tudo fora de 15..60.

## O que mudou

- `_PRAZO_MAX_DIAS` removido; `_PRAZO_MIN_DIAS = 1`; `prazo_elegivel(dias)` unico criterio (vencimento hoje, vencido ou data invalida segue fora; `None` nunca vira 0).
- `sem_vencimento_elegivel` = nenhum vencimento futuro lido. Textos reescritos em `skill_ref` (OPCOES_ESCADA, OPCOES_LASTREADAS) e `copy.js` (inclui a tira `tiraOpcoesMotivo`, 2 modos) na mesma edicao; placeholders `{min}`/`{max}` eliminados.
- Testes reconciliados com nota datada: lastreadas_proposta, curadoria, collar, escada, escada_rotas, fuso_dias_ate_vencimento, escada_espelho.mjs. Novos: 3 e 100+ dias elegiveis; hoje/vencido fora; cenario B3SA3 (09/10 e 16/10 vistos em 06/10) vira `sem_estrutura`/objetivos disponiveis, nao mais `sem_vencimento_elegivel`. Os testes antigos de recusa por 5/10/90 dias foram convertidos em seu inverso (a regra de negocio mudou por decisao do Alex); a recusa de vencimento hoje continua coberta.
- ADR-023: nota datada ao fim.

## Risco do prazo curto

Opcao a poucos dias do vencimento tem decaimento temporal (theta) alto e pouco tempo para a tese se realizar; o usuario leigo pode montar estrutura que perde valor rapido. A tela ja mostra o prazo em dias (Fase 49); nenhum aviso novo foi adicionado, conforme o plano. Sem teto, vencimentos muito longos tambem entram, mas so se estiverem entre os 2 mais proximos.

## Verificacao

- pytest (lastreadas, curadoria, escada, collar, skill_ref, mcp_guardioes, fuso, estrutura_posicao, anatomia_perna, fronteira): 657 passed.
- node test_opcoes*.mjs + test_estrutura_espelho: verdes; `npx vite build` e `npx cap copy ios` ok. Suite canonica completa NAO rodada (orquestrador).

## Deviations from Plan

Nenhuma de escopo. `_PRAZO_MIN_DIAS` foi mantido como nome (valor 1) para nao quebrar `test_fuso_dias_ate_vencimento`.

## Known Stubs

Nenhum.

## Self-Check: PASSED

Commits cf4783cc e 08c15d3d existem.
