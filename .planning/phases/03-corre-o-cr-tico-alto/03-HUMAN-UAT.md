---
status: complete
phase: 03-corre-o-cr-tico-alto
source: [03-VERIFICATION.md]
started: 2026-08-19T04:28:51Z
updated: 2026-08-19T09:41:26Z
---

## Current Test

[done]

## Tests

### 1. Operador IA — card de status reativo (FIX-C19)
expected: Abrir a tela "Operador IA" (Modo Operador). O card de 3 badges aparece no topo, antes do título "Operador IA". Trocar o Modo do app em Perfil e voltar move o badge 1 ("Modo do app") e o badge 3 ("Executar/sinalizar") JUNTOS. Ligar/desligar o toggle "Operador no servidor" no card-herói move o badge 2 ("Operador no servidor") e o rótulo ATIVO/INATIVO do card-herói NA MESMA direção — nunca em direções opostas.
result: passed — Alex testou ao vivo e aprovou (2026-08-19).

### 2. Kill-switch do timing_watch — fallback de permissão (FIX-C35)
expected: No portal admin, com uma conta que tem `execucao_automatica.ver` mas NÃO tem `execucao_automatica.controlar`, abrir a aba Automação. O box "Kill-switch do push de gatilho (timing_watch)" mostra o estado, mas o botão de alternância é substituído pela mensagem "Sem permissão para alternar (requer execucao_automatica.controlar)." — nenhum controle interativo aparece para essa conta.
result: skipped — não testável ao vivo pelo fluxo real do produto: o papel `execucao_automatica` no RBAC (`server/app/rbac.py:24`) agrupa `.ver` e `.controlar` juntos; não existe hoje, na tela "Usuários e papéis" do admin, forma de conceder só `.ver`. Construir essa conta exigiria manipulação direta de banco ou edição temporária de `rbac.py` — Alex decidiu (2026-08-19) aceitar a garantia já verificada no nível de código em vez de forçar o estado: backend rejeita com 403 quem não tem `.controlar` (coberto por teste automatizado), e o front só renderiza o toggle quando a permissão existe (leitura direta do componente). Vale registrar como possível gap de granularidade do modelo RBAC para revisão futura, não como defeito desta fase.

## Summary

total: 2
passed: 1
issues: 0
pending: 0
skipped: 1
blocked: 0

## Gaps
