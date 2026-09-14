# Fase 31 — Varredura de oportunidades de opções · CONTEXT (rascunho inicial)

> Aberto na noite de 2026-09-14, ao final de uma sessão longa (Fases 27-30 +
> fix de produção do mydata). Registra só as três decisões colhidas via
> `AskUserQuestion` — **não é um CONTEXT.md fechado**, tem lacunas reais de
> desenho ainda por resolver antes de qualquer plano de execução. Continuar
> isso é trabalho de fase nova, recomendado para uma sessão com orçamento
> fresco (`/handoff`), não uma extensão do que já rodou hoje.

## Por que esta fase existe

Depois do fix de produção da noite (seleção de vencimento em
`options_provider_mydata.py`, ver `quick/260914-b6p`), o Alex reconsiderou a
decisão que tinha acabado de tomar ("primeiro futuro, seja qual for") e
pediu algo maior: **"sempre trazer as opções disponíveis no futuro"**, com
**"uma análise AI ou determinística destas opções disponíveis usando os
principais setups de opções e os gráficos de payoff para trazer para o
usuário as oportunidades"**.

## Guardrail não-negociável (repetido, é o mesmo de toda a sessão)

A frase "análise AI **ou** determinística" é exatamente a ambiguidade que o
princípio 5 do CLAUDE.md e o pedido original desta sessão inteira vieram
para fechar. **Não é uma escolha entre as duas** — a seleção de quais
oportunidades aparecem tem de ser 100% determinística (mesma régua da Fase
30: razão prêmio/perda máxima, ou o que for decidido para as estruturas
novas, sempre calculada por `opcoes_motor.avaliar()`/`opcoes_payoff.py`,
nunca por um LLM). A IA, se entrar, **narra** o que o número já escolheu.
Isto não foi reaberto pelo Alex — só a frase dele reabriu a ambiguidade que
precisa ficar fechada de novo no plano de execução.

## Decisões coletadas (via `AskUserQuestion`, 2026-09-14)

### D1 — Escopo do "futuro": varredura completa, não só o próximo vencimento

Ao contrário da decisão de horas atrás ("primeiro futuro, seja qual for"),
o Alex escolheu explicitamente a opção maior: **varrer VÁRIOS vencimentos
futuros** atrás de oportunidades, não só pegar o mais próximo disponível e
aceitar vazio quando ele estiver curto demais (achado de hoje: quase todo o
mercado cai no mesmo vencimento mensal — 18/09 na medição, 4 dias, abaixo
do piso de 15 — então "só o próximo" deixa a tela vazia por boa parte de
cada ciclo).

**Não decidido ainda**: até onde varrer (todos os vencimentos que a cadeia
trouxer? Um teto, tipo 90 ou 120 dias? A mesma janela 15-60 da Fase 30,
aplicada vencimento a vencimento em vez de só ao mais próximo?). Isso muda
diretamente o custo de rede: hoje `options_provider.get_options(ticker)`
busca UM vencimento por chamada (Decisão D3 da Fase 30 — nunca mais de uma
chamada por posição, de propósito, pra não estourar o orçamento do
mydata/60 por minuto). Varrer N vencimentos por ticker multiplica isso por
N — precisa de desenho novo de orçamento, não é extensão trivial do que já
existe.

### D2 — Estruturas: as 3 do motor interno + opção a descoberto

Além de venda coberta/put/collar (o motor interno já cobre as 3), o Alex
quer **opção a descoberto** incluída na varredura de oportunidades.

**Tensão a resolver, não trivial**: a Fase 29 fechou, com checkpoint
aprovado, que operar a descoberto exige lastro OU flag opt-in ligado (com
termo de responsabilidade) — é o oposto do resto do produto, que nunca
esconde possibilidade, só bloqueia a AÇÃO. Uma varredura de "oportunidades"
que já mostra estruturas a descoberto pra conta SEM o flag ligado violaria
o espírito da Fase 29 (mostrar risco antes de operar) — mas simplesmente
OMITIR essas oportunidades pra quem não tem o flag também é uma escolha de
produto que ninguém validou ainda. **Não decidido**: a oportunidade a
descoberto aparece pra todo mundo (com aviso "ligue o flag pra operar") ou
só pra quem já tem o flag ligado?

### D3 — Payoff visual: reusar `PayoffChart.jsx`, mas melhorado

Decisão: sim à curva visual (não só os números que a Fase 30 já mostra),
reaproveitando `web/src/opcoes/PayoffChart.jsx` como base — mas o Alex
pediu explicitamente para **melhorar o gráfico**, não só reusar como está.

**Não decidido**: o que "melhorar" significa concretamente. Nenhum detalhe
foi pedido ainda (mobile 375px? múltiplos candidatos sobrepostos na mesma
curva pra comparar? interatividade — tocar num ponto e ver o preço?
zoom/pan?). Isto é a pergunta mais aberta das três — precisa de uma rodada
de design antes de virar plano de execução, não é algo para presumir.

## O que já existe e pode ser reaproveitado (não é fase do zero)

- `opcoes_motor.rastrear()`/`avaliar()` — já suportam N candidatos por
  chamada de `rastrear` (parâmetro `n`), sobre uma cadeia já em memória.
- `opcoes_curadoria.py` (Fase 30) — o padrão de ranking determinístico
  (`rankear`/`exigir_ranking`, que recusa estruturalmente pool não
  ordenado) é o molde a estender, não a jogar fora.
- `PayoffChart.jsx` — componente de curva + números já em produção no
  caminho MCP; ponto de partida citado pelo próprio Alex.
- `buy_option`/`sell_option` + o flag `permitirOpcaoADescoberto` (Fase 29)
  — a mecânica de execução a descoberto já existe e já está gateada; esta
  fase não precisa reconstruir isso, só decidir como a DESCOBERTA de
  oportunidade interage com o gate de EXECUÇÃO.

## Fora de escopo até decisão em contrário

- Mudar a Fase 29 (lastro obrigatório/flag opt-in) — invariante, não
  re-litigada por este pedido.
- Qualquer coisa que aproxime a IA de ESCOLHER/RANKEAR oportunidades —
  guardrail não-negociável, repetido acima.

## Recomendação de processo

Dado o tamanho real (orçamento de rede novo pra multi-vencimento, tensão
de produto com o flag de opção a descoberto, e um pedido de design aberto
pro gráfico), esta fase precisa de `/gsd-discuss-phase` de verdade — não dá
pra fechar as três lacunas acima só com suposição razoável, cada uma muda
o plano de execução de forma material. **Recomendado**: continuar em sessão
nova (`/handoff`), com orçamento fresco, começando por essas três lacunas
antes de qualquer `/gsd-plan-phase`.
