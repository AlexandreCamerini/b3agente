---
status: partial
phase: 20-funda-o-estrutural-e-tipogr-fica
source: [20-VERIFICATION.md]
started: 2026-09-05T00:00:00Z
updated: 2026-09-05T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Comportamento real de `prefers-reduced-motion: reduce` (MOTION-03)
expected: Ligar "Reduzir movimento" no sistema (macOS: Ajustes do Sistema →
Acessibilidade → Movimento → Reduzir Movimento), abrir o app (build
`F10-20260905-02`) e confirmar: (1) troca de tema/modo em Preferências é
instantânea, sem fade; (2) o marquee do ticker e o spinner ficam PARADOS —
dois screenshots com ~1s de intervalo na mesma posição, sem strobe; (3)
desligar a preferência e confirmar que o ticker volta a andar normalmente.
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

Nenhum gap de código — a regra CSS foi confirmada byte-idêntica no
código-fonte e no bundle de produção servido (`F10-20260905-02`), em 3
sessões de execução e 2 reverificações do orquestrador. Nenhuma ferramenta
disponível neste ambiente expõe emulação real de `prefers-reduced-motion`
via CDP (`Emulation.setEmulatedMedia`) para alternar o media feature e
observar o efeito comportamental — limitação de ferramenta documentada, não
omissão. Decisão do orquestrador (autorização explícita do Alex para evoluir
sem pausar por aprovação): tratar como item de baixo risco (CSS puramente
aditivo de acessibilidade, não financeiro/regulatório) e prosseguir com a
fase marcada completa, deixando este item pendente de confirmação humana
real — mesmo padrão de transparência já usado para os checkpoints de mercado
aberto do v1.4 (nomear a pendência, nunca escondê-la).
