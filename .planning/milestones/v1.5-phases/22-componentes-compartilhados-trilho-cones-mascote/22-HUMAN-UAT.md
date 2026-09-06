---
status: partial
phase: 22-componentes-compartilhados-trilho-cones-mascote
source: [22-VERIFICATION.md]
started: 2026-09-06T00:00:00Z
updated: 2026-09-06T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Snap/peek dos trilhos de opções em DOM real (SYS-01, 2 de 4 trilhos)
expected: Com o mercado aberto e uma proposta de opções ativa na conta (ou
uma posição com candidatos comparáveis), abrir Posições (build
`F10-20260906-01` ou posterior) e confirmar em DOM real: (1) a tira
"Oportunidades de opções" tem `getComputedStyle(container).scrollSnapType`
equivalente a `x proximity` e o primeiro item `scrollSnapAlign: "start"`;
(2) a linha de candidatos dentro do detalhe de uma posição com proposta tem
o mesmo comportamento. Comparar visualmente que nenhum dos dois herdou o
peek de 84% do HERO-CARROSSEL (ambos devem mostrar mais de 1 item por vez,
sem "vazar" a largura dominante).
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

Nenhum gap de código — os 4 trilhos são roteados pelo mesmo helper
`carouselTrackStyle`/`carouselItemStyle` (`web/src/App.jsx:301`), confirmado
por leitura de fonte e por guardião estático
(`test_fase22_componentes_compartilhados.mjs`, Seção A) para os 4 call
sites, incluindo os 2 pendentes aqui. A medição em DOM real dos outros 2
trilhos (HERO-CARROSSEL e filtro "MODELO DE ANÁLISE" da Watchlist) foi
concluída pelo orquestrador contra o bundle de produção publicado
(`22-04-SUMMARY.md`, seção "Orchestrator Live Re-Verification") e confirmou
exatamente o padrão esperado, incluindo a equivalência computada
`scroll-snap-type: x` ≡ `x proximity` (canonicalização do Chromium quando a
força de encaixe é a default) — forte indício de que os 2 trilhos restantes
computam da mesma forma, já que usam o mesmo helper de módulo. Mas essa é
uma inferência a partir do código, não uma medição — os 2 itens não puderam
ser exercitados com dado real porque a conta de verificação não tinha
proposta de opções ativa e o mercado estava fechado no momento da checagem
(2026-09-06, madrugada). Decisão do orquestrador (autorização explícita do
Alex para evoluir sem pausar por aprovação): tratar como item de baixo risco
(mesmo mecanismo já provado 2 de 4 vezes em produção, sem lógica condicional
divergente por trilho) e prosseguir com a fase marcada completa, deixando
este item pendente de confirmação humana real com dado de mercado —
mesmo padrão de transparência já usado para o item MOTION-03 da Fase 20 e
para os checkpoints de mercado aberto do v1.4 (nomear a pendência, nunca
escondê-la).
