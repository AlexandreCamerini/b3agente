# BolsIA — Como funciona

> Documento de referência (suporte / App Store / onboarding). Espelha a tela
> **Perfil → Como funciona** do app. Mantido junto do código
> (`web/src/App.jsx` → `ajudaSecoes`) — ao mudar um, atualize o outro.

**BolsIA é um app educacional de análise técnica da B3.** Ele varre o mercado,
mostra oportunidades de estudo e deixa você simular uma carteira — tudo com
dinheiro fictício. Nada aqui é ordem real nem recomendação personalizada:
nenhuma ordem é enviada à corretora.

---

## Os dois modos

O app tem dois modos, com a mesma base técnica e vozes diferentes:

- **Modo Estudo** — um *professor*: explica o porquê de cada setup, no vocabulário de aprendizado.
- **Modo Operador** — uma *mesa de operações*: dá o plano objetivo (entrada, stop, alvo, risco em R).

Troque em **Perfil → Modo de trabalho**. O modo muda a cor, os rótulos e o tom
— mas a execução e o risco são sempre seus.

## Acompanhar (início)

A tela inicial resume seu dia: melhores oportunidades da sua watchlist, a curva
do patrimônio simulado, sua sequência de estudo e um lembrete do que fazer a
seguir. É o ponto de partida — dali você vai para o Radar.

## Radar (Modo Estudo) / Mesa de oportunidades (Modo Operador)

Varre o universo de ações e lista, por ativo:

- **Veredito** — a leitura do ativo (ex.: "Estudar alta", ou "Comprar — no rompimento" na mesa).
- **Confluência** — um anel de 0–100%: quanto o ativo bate com um setup clássico. Mede aderência ao padrão em dados passados, **não** probabilidade de resultado.
- **Leitura rápida** + mini-gráfico de preço.

Em cada card você pode abrir a **leitura da IA** ("Aprofundar com IA" / "Plano
da mesa (IA)") ou levar o ativo para a Watchlist / Monitoramento.

## Watchlist (Estudo) / Monitoramento (Operador)

Seus ativos acompanhados, ordenados por oportunidade. Cada linha tem um
mini-gráfico e abre a análise completa. Use para acompanhar de perto os ativos
que te interessam antes de simular uma operação.

## Portfólio (Estudo) / Posições (Operador)

Sua carteira **simulada**: patrimônio, resultado do dia e cada posição com a
régua do plano (invalidação → gatilho → alvo). Você simula compras e vendas,
define stop e alvo, e acompanha o resultado em R — sem risco de dinheiro real.

## Operador IA

Um agente que acompanha as posições da carteira simulada e age pelas regras que
você define (proteger stop, realizar no alvo). Com conta, roda no servidor
24×5, mesmo com o app fechado.

Você escolhe **Executar** (ele simula a saída no stop/alvo) ou **Apenas
sinalizar** (só avisa), define regras e tetos, e o intervalo de reavaliação.
Sempre sobre a carteira simulada.

## Fundamento (A / B / C)

Ao lado do sinal técnico, alguns ativos mostram um selo de **fundamento**:

- **A** — sólido · **B** — regular · **C** — fraco

Avaliado por três pilares: valuation (preço/lucro), rentabilidade (ROE e
margem) e solidez (dívida/EBITDA). É um **filtro de qualidade, nunca um gatilho
de compra**: a técnica manda no plano. Quando a decisão técnica é operável mas
o fundamento é fraco (C), a confiança desce um degrau. Sem dado de fundamento,
o app mostra **"sem dado"** — nunca inventa.

## Eficiência da IA

O app guarda cada análise com stop/alvo e, **10 pregões depois**, confere se
bateu o alvo, o stop ou expirou. Isso vira estatística:

- **Taxa de acerto**
- **Expectância** — a vantagem média por análise, em R
- **Calibração da confiança** — a confiança declarada bate com o acerto real?
- **Curva de R acumulado** + drawdown

Enquanto não há amostra suficiente, aparece **"n insuficiente"** ou
**"aguardando o prazo"** — em vez de um número enganoso. É autoavaliação sobre
o passado, não garantia de futuro. Dá para exportar tudo em CSV.

---

## Avisos importantes

Tudo no BolsIA é **educacional e simulado**. Não é recomendação de investimento
nem promessa de resultado. Operar no mercado real envolve risco de perda. Use
sempre stop, dimensione a posição e respeite seu plano de risco. As decisões e
a execução são suas.
