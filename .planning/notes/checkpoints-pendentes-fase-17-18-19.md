# Checkpoints humanos pendentes — Fases 17, 18 e 19 (Opções v2)

**Registrado:** 2026-09-04, a pedido do Alex ("quero deixar isso registrado
num arquivo pra consultar depois"). Consolida os roteiros de verificação
ao vivo que ainda faltam rodar, cruzados com o que já foi confirmado nesta
sessão. Fonte de verdade contínua: `.planning/STATE.md` seção
"Blockers/Concerns" — este arquivo é um snapshot de consulta rápida, não
substitui aquela seção se ela divergir no futuro.

## Por que as três fases estão no mesmo barco

Fase 17 construiu o fluxo de aceite; Fase 18 deu a ele uma casa em
Posições; Fase 19 generalizou o mesmo fluxo pra N candidatos. As três
publicam no MESMO bundle e nenhuma teve seu checkpoint humano aprovado
ainda — aprovar/publicar uma das fases mais recentes implicitamente carrega
o risco das anteriores, ainda não confirmadas ao vivo.

Praticamente todo passo pendente depende da mesma precondição real: **uma
posição sua, de verdade, com proposta de opção ativa** (mercado aberto +
cadeia líquida + setup técnico do Radar disparando VENDER/baixa). Sem isso
os passos de aceite/payoff/manchete não são exercitáveis em nenhuma das
três fases.

---

## Fase 17 — Fluxo de aceite (`.planning/phases/17-fluxo-de-aceite/17-06-PLAN.md`)

**Status: ADIADO, não aprovado.** Única tentativa (03/09) caiu com o
mercado fechado; Alex instruiu seguir mesmo assim — risco aceito
conscientemente, não é aprovação. Push da Fase 17 pra `origin` nunca
aconteceu.

| # | Passo | Status |
|---|---|---|
| 1-2 | Modo Estudo: card mostra payoff, "Fonte: … · data/hora", frase didática, **sem** botão de executar | Pendente |
| 3 | Modo Operador: CTA aparece, payoff continua legível | Pendente |
| 4 | Nenhum número como "R$ 0,00" onde deveria ser "ilimitado"/"—" (put de proteção tem ganho ilimitado) | Pendente |
| 5-6 | Collar oferecido quando a put isolada não cabe no caixa; confirmação cita a trava do lastro + "as duas pernas juntas — ou nenhuma" | Pendente |
| 7 | Aceitar de verdade: 2 posições de opção novas na Carteira (call vendida + put comprada), caixa movido pelo líquido, trava de lastro visível | Pendente |
| 8 | Proposta ficou velha (tela parada) → servidor recalcula, erro legível se mudou, sem execução parcial | Pendente |
| 9 | Card de proposta íntegro no Radar (não só na Watchlist) — mesmo `AtivoCard`, guardião `test_opcoes_proposta_ui.mjs` | Pendente |
| 10 | iPhone (repetir passos 2 e 5 — `deviceStore` é store diferente do `serverStore` do navegador) | Pendente |

---

## Fase 18 — Seção de Opções em Posições (`.planning/phases/18-aba-opcoes/18-05-PLAN.md`)

**Status: PENDENTE, parcialmente exercitado ao vivo no iPhone (03/09).**
Build instalado via `scripts/instalar-iphone.sh` (dev local — localhost não
tem dado de mercado real pra checar, motivo dado pelo Alex).

| # | Passo | Status |
|---|---|---|
| 1 | Tira "Oportunidades de opções" aparece acima da lista de posições, um cartão por posição com proposta | **Parcial** — tira aparece; sem item porque nenhuma posição tinha proposta ativa no dia do teste |
| 2 | Manchete do item da tira idêntica à manchete do mesmo ativo na Watchlist (guardrail CVM — divergência é reprovação automática) | Pendente (precisa de item real pra comparar) |
| 3 | Toque no item rola a posição pro centro E abre o detalhe da estrutura ali | Pendente |
| 4 | Tocar outro item fecha o detalhe anterior e abre o novo — um por vez | Pendente |
| 5 | Aceite em Modo Operador direto de Posições; confirmação cita a trava; CTA vira "recomprar"; destrava ao encerrar | Pendente |
| 6 | Modo Estudo: detalhe mostra a frase didática, nenhum botão de executar, tira continua aparecendo | Pendente |
| 7 | Estado vazio com motivo (tira não some, mostra "sem contrato líquido" × "cobertura líquida mas sem setup hoje") | **✓ Confirmado** ao vivo, 03/09 — mostrou "cobertura líquida existe, mas nenhum setup técnico ativo hoje" |
| 8 | Carteira vazia → tira não aparece de forma alguma (só o estado vazio de portfólio de sempre) | Pendente |
| 9 | iPhone: repetir passos 1, 3, 7 | **Parcial** — 1 e 7 confirmados no iPhone; 3 não (sem item pra tocar) |
| 10 | Watchlist/Radar intocados — proposta aparece ali exatamente como antes desta fase | Pendente |
| — | **Decisão obrigatória**: (a) aprovar Fases 17+18 juntas e liberar o push; (b) aprovar a 18 mas segurar o push até rodar o roteiro da 17 com mercado aberto; (c) reprovar | **Em aberto** |

---

## Fase 19 — Motor multi-candidato (`.planning/phases/19-motor-multi-candidato/19-04-PLAN.md`)

**Status: PENDENTE, não exercitado (04/09).** Motor + rotas + front
executados e publicados (carimbo `F10-20260904-01`, suíte canônica verde,
três elos de carimbo coerentes). Precondição pro roteiro é mais estreita
que a da Fase 18: precisa de uma posição com leitura **VENDER/baixa** cujo
caixa caiba TANTO a put isolada QUANTO a trava protetora (só assim os dois
candidatos aparecem juntos).

| # | Passo | Status |
|---|---|---|
| 1 | Dois candidatos lado a lado (put primeiro, collar depois) | Pendente |
| 2 | Manchete de cada um = a do motor; a do primeiro = idêntica à Watchlist (zero-tolerância CVM) | Pendente |
| 3 | Payoff próprio por card (ganho/perda/breakeven/caixa diferentes, nunca "R$ 0,00" onde deveria ser vazio) | Pendente |
| 4 | Posição com só uma estrutura elegível continua idêntica a antes da Fase 19 | Pendente |
| 5 | Aceitar o 2º card (collar) em Modo Operador — trava o lastro, abre as 2 pernas | Pendente |
| 6 | Tentar o 1º card (put) depois — NÃO executa, erro de lastro insuficiente | Pendente |
| 7 | Ordem inversa (put primeiro, collar depois) — 2ª tentativa recusada por "operação lastreada já aberta" | Pendente |
| 8 | Modo Estudo: os dois cards aparecem, sem nenhum CTA | Pendente |
| 9 | iPhone: repetir 1, 2 e 5 | Pendente |
| 10 | **Decisão a/b/c** — agora empilha as três fases: (a) aprovar 17+18+19 juntas e liberar push; (b) aprovar a 19 mas segurar até 17+18 fecharem ao vivo; (c) reprovar | **Em aberto** |

---

## Próximo passo

Quando o Radar disparar um setup ativo sobre alguma posição real (idealmente
de queda, com caixa de sobra, pra também cobrir o roteiro da Fase 19), rodar
os três roteiros na sequência — muitos passos se sobrepõem (ex.: manchete
idêntica à Watchlist é checada nas três) e dá pra fechar tudo na mesma
sessão de teste ao vivo.
