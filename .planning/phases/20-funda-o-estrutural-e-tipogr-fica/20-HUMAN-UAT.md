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
result: PASS — reproduzido ao vivo pelo orquestrador em 2026-09-06 (dev
server, conta de teste, tema claro): modal abriu com `<svg viewBox="0 0 64
92">` (assinatura exclusiva do `BorisFlat`, o PNG antigo não tem esse
viewBox), 11 elementos path/circle, visualmente reconhecível como o Boris.
Tema escuro não reconferido nesta passada (já aprovado antes por
renderização isolada do mesmo SVG contra os dois `bgCard` reais, ver
`23-02-SUMMARY.md`) — risco residual baixíssimo, mesmo asset, mesmo CSS.

### 3. Pulso de sucesso na confirmação de ordem, com mercado aberto (MOTION-02, Fase 23)
expected: Com o mercado ABERTO (pregão em andamento), confirmar uma compra
ou venda que execute IMEDIATAMENTE (não fique pendente) e observar o pulso
`~120ms` (`scale(1→1.08→1)`) no valor confirmado, antes da UI virar o
estado de sucesso já existente. Repetir para uma VENDA TOTAL de uma posição
(o caso que o planner sinalizou como de risco — `SellModal` desmonta via
`if (!pos) return null`) e confirmar que o pulso pinta ANTES do modal
fechar, não depois.
result: [pending — mercado fechado durante toda a verificação ao vivo desta
sessão; testado e confirmado com sucesso apenas os caminhos que NÃO devem
pulsar (pendente e rejeitada, ver Gaps) — o caminho de sucesso real
permanece por reproduzir]

## Summary

total: 3
passed: 1
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

Item 2: RESOLVIDO nesta sessão (ver Test 2 acima) — o modal abriu numa
passada de verificação subsequente (navegação a partir da Watchlist, em vez
do reload direto da aba Acompanhar usado na primeira tentativa; a causa
exata da diferença não foi isolada, mas deixou de ser relevante assim que a
reprodução aconteceu) e confirmou `BorisFlat` ao vivo.

Item 3: nenhum gap de código — os dois caminhos que NÃO devem pulsar
(pendente, por mercado fechado; rejeitada, por caixa insuficiente) foram
confirmados ao vivo com ZERO eventos de pulso capturados por
`MutationObserver` num teste real de compra (incluindo um teste adversarial
de 3 cliques quase-simultâneos, que corretamente resultou em 1 ordem
pendente real + 2 tentativas rejeitadas em `history`, sem nenhuma ordem
duplicada nem reserva de caixa dobrada — o invariante financeiro do
CLAUDE.md do repo permaneceu intacto mesmo sob esse teste agressivo). O
caminho de SUCESSO (execução imediata, mercado aberto) e o caso da
`SellModal` em venda total não puderam ser exercitados porque o mercado
esteve fechado durante toda a sessão de verificação — mesma classe de
limitação (dependente de horário de pregão) já documentada para outros itens
deste milestone. Decisão do orquestrador (mesma autorização): tratar como
item de baixo risco (a prova estática do guardião + a prova ao vivo dos dois
caminhos negativos já cobre a parte que mais importa — nunca pulsar quando
não devia) e prosseguir, deixando a confirmação do pulso de sucesso real
pendente de teste humano em horário de pregão.
