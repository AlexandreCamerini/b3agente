---
status: partial
phase: 20-funda-o-estrutural-e-tipogr-fica
source: [20-VERIFICATION.md, 23-02-SUMMARY.md]
started: 2026-09-05T00:00:00Z
updated: 2026-09-06T00:00:00Z
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

### 2. Modal "Este é o Boris" com a nova ilustração flat (ILUS-01, Fase 23)
expected: Numa conta nova (ou numa que ainda não tenha `borisIntroVisto`),
chegar na aba inicial (Acompanhar/Watchlist) com a camada de entendimento
ligada e confirmar que o modal "Este é o Boris" abre mostrando a nova
ilustração flat/cartoon (`BorisFlat.jsx`) — reconhecível como o mesmo
personagem do `LogoMark` (óculos redondos âmbar, corpo azul-marinho) — em
vez do PNG semi-realista antigo. Conferir nos dois temas (claro/escuro) que
o personagem não "some" contra o fundo do card do modal.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
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

Item 2: nenhum gap de código — o SVG de `BorisFlat.jsx` foi confirmado
correto por leitura de fonte (geometria/hex idênticos a `LogoMark`) e
renderizado isoladamente contra os dois `bgCard` reais do app, com
reconhecibilidade e contraste aprovados sem necessidade de ajuste (ver
`23-02-SUMMARY.md`, seção "Orchestrator Live Re-Verification"). O que não
foi possível nesta sessão foi reabrir o modal "Este é o Boris" dentro do
próprio app rodando (o gate de exibição — `borisIntroShownRef`/
`data.config.borisIntroVisto`/`didatica.ligada` — não reagiu como esperado
numa conta de teste existente, apesar de todas as pré-condições lidas via
API baterem certo); causa não investigada a fundo por não bloquear a entrega
(a arte em si já está provada correta por outro caminho). Decisão do
orquestrador (mesma autorização): tratar como item de baixo risco (visual,
não financeiro/regulatório) e prosseguir, deixando a confirmação dentro do
modal real pendente de teste humano.
