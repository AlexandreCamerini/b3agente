# v2 — Opções como classe de primeira ordem

Síntese do painel de 4 especialistas (`anthropic-skills:analise-tecnica-b3`,
`engineering:system-design`, `design:user-research`+`design:design-critique`,
`engineering:architecture`) convocado via `CHECKOUT-V2-Opcoes-otimizado.md`,
mais um mapeamento de código adicional que confirmou/corrigiu premissas dos
quatro. Nenhuma linha de produção foi tocada nesta rodada — é proposta, para
aprovar antes de implementar.

Decisões que o Alex já travou antes do painel (não reabertas aqui):
opção vira **camada dentro do card do ativo**, não aba irmã; escopo de operar
é **só compra de call/put a seco** (1 perna); opção aparece **nos dois modos**
(Estudo/Operador) com o mesmo tratamento vocabular que ação já tem.

---

## 1. Veredito sobre a separação de temas

**Confirma-se a tese do Alex — com o argumento de mercado, não só de UI.**

Opção difere de ação em cinco eixos que não têm equivalente em ação: prazo
finito (a tese pode estar certa na direção e errada no tempo), breakeven como
número que decide (não o alvo — o preço precisa passar de strike+prêmio
*antes* do vencimento), decaimento temporal (parado custa dinheiro via theta),
IV vs HV (dá para acertar a direção e perder no prêmio), e liquidez do
contrato específico (spread de 30% come o R:R antes da operação começar). Isso
justifica um tratamento de análise genuinamente diferente — não é a mesma
lente em escala menor.

Mas a *unidade de decisão* do usuário continua sendo o ativo: ninguém "navega
para opções" no abstrato, alguém está olhando PETR4 e quer saber se as opções
dela fazem sentido. A camada dentro do card (em vez de aba irmã) está alinhada
com esse comportamento — e o mapeamento de código confirma que o seam já
existe: `AtivoCard({ vm, contexto, children })` já é composto de fora pelo
Radar via `children` (App.jsx:2128). Opção entra por `children`, não por campo
novo em `vm` nem por `contexto === "opcoes"` — isto é invariante de
code-review, não decisão de arquitetura nova.

**Correção ao que o painel assumiu**: o comentário no código diz "fonte única
em todas as abas (watchlist, radar, posições, home)", mas isso não é verdade
hoje — `CarteiraScreen` (App.jsx:2547) ainda tem card próprio, sem usar
`AtivoCard`. A reconciliação está em 2 de 4 superfícies. Isso não bloqueia a
v2 (a camada de opções entra nas duas superfícies que já usam `AtivoCard` —
Watchlist e Radar), mas significa que Carteira/Posições fica **fora da v2**
até essa reconciliação avançar (ver seção 6).

---

## 2. Gatilho e layout — onde a camada aparece

Recomendação do painel de UX, adotada:

- **Gatilho**: linha colapsada no rodapé do card, na mesma gramática visual
  que a linha de links já existente (`✨ Reanalisar · 📈 Indicadores`) —
  `⚡ opções · call 38 · R$ 0,72 · 24 dias ▾`. Substitui o botão isolado
  "Opções ▸" hoje em `MercadoScreen` (App.jsx:2366), que é removido.
- **Expansão — "A acoplado" (revisado numa 2ª rodada do painel, ver abaixo)**:
  um único controle. Abrir a linha de opções encolhe automaticamente o bloco
  do ativo (manchete + chips + régua) para uma **espinha persistente** — não
  some, não precisa de um segundo toggle. A espinha carrega os números que
  sustentam a checagem de coerência (Princípio 5/9): stop, alvo, move/dia
  típico e o veredito "sustenta a direção?". Dos contratos, só **1 fica
  aberto por vez** (accordion) — corta mais altura do card do que esconder o
  ativo teria cortado.
- **Cadeia completa**: overlay ticker-scoped, mesmo padrão de `openTech`/
  `techFor` já usado pra indicadores — `BackHeader title="PETR4 › Opções"`.
- **Gate de descobribilidade**: a linha só aparece se o ticker tem opções
  líquidas (flag do backend) — sem badge chamativo. Primeira aparição leva
  um explicador de uma linha, dispensável.
- **Ambos os modos**: mesmo componente, vocabulário/ênfase trocam pelo padrão
  já usado na manchete (`decM`, App.jsx:2177) — Estudo enfatiza "prêmio pago
  é a perda máxima"; Operador enfatiza R:R e % do capital.

**Densidade — os 5 campos acima da dobra** (lente técnica, já filtrado pelo
que é ruído para quem aprende):

1. **Custo e risco**: prêmio × 100 = valor em risco + "perder tudo é o
   resultado comum" (não é cauda, é modal).
2. **Até onde e até quando**: breakeven em R$/% de distância do preço atual
   + dias até o vencimento — reusa a régua visual `PlanRuler` já existente
   (eixo no preço do ativo, marcas em strike e breakeven).
3. **A tendência do ativo-objeto sustenta a direção?** — herdado da análise
   de ação que já existe; se a ação diz "aguardar", a opção nunca vira
   "comprar" (Princípio 5/9 da skill).
4. **Dá para sair?** — selo de 3 estados por spread (negociável/difícil/sem
   mercado); "sem mercado" bloqueia a camada de comprar.
5. **Custo de esperar** — theta traduzido em % do prêmio por semana, nunca o
   grego cru.

Gregas completas (delta, gamma, vega, rho), preço teórico BSM e IV vs HV vão
para um "Aprofundar" — não somem, mas não competem com os 5 campos.

**Trade-off aceito**: uma linha discreta custa ~34px em todo card com opção
líquida, e toda a descobribilidade repousa em o usuário notá-la. Validar com
teste de 5 usuários ("ache as opções da PETR4", medir quem acha em <15s)
antes de fechar o layout final.

---

## 3. Modelo de dados — o que muda em cada módulo

**Decisão: coleção separada `optionPositions`, não campos opcionais em
`positions`.** Confirmada de forma independente pelas lentes de dados e de
arquitetura — e reforçada pelo mapeamento de código: `positions` não é
tabela, é blob JSON no kv-store (`store.py`) e, no iOS, documento local no
aparelho (`persistence.js`, deviceStore) — não existe caminho de migração
real para usuários que já têm posições salvas. `p["t"]` hoje é
simultaneamente chave primária, **chave de cotação** (`priceOf(t)` →
`yahoo.get_quote`) e rótulo de UI; um contrato de opção quebra os três papéis
ao mesmo tempo. Reusar `positions` faria todo consumidor atual (compra,
venda, KPI, snapshot, UI) tratar opção como ação em silêncio — coleção
separada torna quem ignora opções seguro por omissão, e quem as suporta
explícito.

Shape proposto:

```
{ id: "PETRH340",          # contractSymbol — chave, único por série
  underlying: "PETR4",     # ativo-objeto — onde a camada aparece no card
  optionType: "call"|"put", strike: 34.0, expiration: "2026-08-15",
  qty: 100,                # ações-equivalente, mesma unidade de positions.qty
  avg: 1.25,               # PRÊMIO pago por ação — mesmo nome/semântica de positions.avg
  stop: null, alvo: null,  # em PRÊMIO (mesma unidade de avg)
  abertaEm, setupEntrada,  # idênticos ao padrão de positions
  ivEntrada, deltaEntrada, hv21Entrada }  # snapshot didático da entrada
```

**O que quebra em `server/app/agent.py`** (laço `_run_cycle_inner`):

- **Cotação**: `quotes_getter` hoje é de ação; contrato de opção volta
  `price=None` e a posição fica invisível pra sempre no `continue` atual.
  Precisa de um getter próprio que resolve o contrato pela cadeia
  `(underlying, expiration)` — 1 fetch por vencimento, não por contrato.
- **Trailing (F2)**: percentual funciona sobre prêmio; `"atr"`/`"estrutura"`
  não — ATR é em R$ do ativo-objeto, unidade incompatível com prêmio. Cai no
  fallback `_percentual()` de `nivel_trailing`, com a descrição dizendo por
  quê no Diário. A monotonicidade sobrevive intacta (stop em prêmio também só
  sobe) — mas o efeito é real: theta faz o prêmio cair sem movimento
  adverso do ativo, então o stop monotônico pode disparar por decaimento
  puro. Correto, mas precisa aparecer nomeado.
- **Alvo dinâmico (F3)**: `avaliar_alvo_dinamico` soma `1.5×ATR(ativo)` a um
  alvo em prêmio — unidade quebrada. Retorna `(None, None)` para opção na v2
  (sem extensão).
- **Fechamento por vencimento — ramo novo, obrigatório**: hoje nada no laço
  fecha por data. Antes do loop de stop/alvo, fora do gate `price is None`:
  se `hoje >= expiration`, liquidar pelo intrínseco (`max(0, S−K)` para call),
  que pode ser zero — perda total, sem nenhum stop acionado. Aviso em D-3.

**Achado adicional (mapeamento de código, não estava no radar do painel):**
fechar posição hoje NÃO tem um caminho único — são **5**: venda manual, laço
do agente server-side (`agent.py`), ciclo foreground web
(`POST /api/cycle`, reusa o mesmo `agent.py`), ciclo foreground **iOS** (uma
**segunda implementação**, em `web/src/persistence.js:729-741`, que reproduz
a lógica de stop/alvo em JS) e `reset_portfolio`. **O caminho do iOS diverge
do server-side**: ignora `maxOpsDia`/`maxValorOp`, e não tem NENHUMA das
proteções de F2 (trailing técnico) nem F3 (alvo dinâmico) — só stop/alvo
percentual cru. Isso é um bug pré-existente, não introduzido por opções, e
fica **fora do escopo desta v2** — mas como qualquer novo ramo de
fechamento (vencimento) precisaria ser adicionado nos dois lugares pra não
piorar a divergência, ele vira dependência direta: **ADR-005 (seção 7)
precisa decidir se resolve essa duplicação antes, ou se aceita conscientemente
adicionar o vencimento só do lado server e documentar que o iOS-foreground
fica sem essa proteção na v2.** Sinalizando como possível tarefa em paralelo,
fora desta v2.

Também não existe hoje um campo estruturado de **motivo de fechamento** —
`"stop atingido"`/`"alvo atingido"` é string local, interpolada em texto de
evento e descartada (duplicada nos dois arquivos acima); o registro de VENDA
no `history` não guarda motivo nenhum. ADR-005 precisa decidir se cria esse
campo agora (ficaria estruturado desde o início: `stop`/`alvo`/`vencimento`)
ou se opção também herda o padrão atual de string descartável — a primeira
opção custa pouco a mais e evita repetir a dívida.

**`analysis_outcomes.py`**: R-multiple sobre stop do ativo não se aplica; o
risco já é conhecido e fechado no momento da compra. Redefinir como
`R = (prêmio_saída − prêmio_entrada)/prêmio_entrada`, com pó = exatamente
−1R. Mas medir isso exige série histórica de prêmio, que não existe (COTAHIST
tem restrição de redistribuição — ver `qa/35`). **Recomendação: não medir
opção em `analysis_outcomes.py` na v2** — mede-se a tese direcional do ativo
(que já é medida hoje); o resultado da operação de opção vive só no
`history` da carteira.

---

## 4. Estado da fonte de dados

Sem mudança desde a decisão de 2026-08-04 (memória `opcoes-b3-fonte-de-dados`):
`server/app/options_provider_yahoo.py` é a única fonte hoje, endpoint
não-oficial que falha com frequência para B3 (401/403/429) — degrada com
`providerStatus: "degraded"` e nunca inventa dado. O MyData decidiu aceitar
brapi como fonte de opções marcada como terceiro, mas **nada disso está
implementado em nenhum dos dois lados**.

**Pergunta que a rodada anterior não fez e esta traz**: o produto pode
**simular execução** (registrar uma compra na carteira) a um preço que o
próprio sistema rotula como não-confiável? Ler uma cadeia degradada pra
mostrar é honesto; preencher o `avg` de uma posição simulada com esse número
vira P&L falso no histórico de um usuário real. Isso é decisão de
arquitetura, não só de fonte — ver ADR-004 na seção 6.

---

## 5. Custo por decisão

| Decisão | Custo |
|---|---|
| Camada no card (Watchlist + Radar) | Zero fetch novo por padrão — só ativa quando o usuário expande; reusa o padrão best-effort do `TimingBadge` (fetch próprio, não bloqueia o card) |
| Cadeia completa (overlay) | 1 fetch por ticker/vencimento aberto, já cacheado 300s no provider Yahoo hoje |
| Fechamento por vencimento no laço do agente | Marginal — 1 comparação de data por posição de opção aberta, sem fetch extra |
| Fonte MyData/brapi | Zero aqui — custo já orçado do lado do MyData (chave + cota), não deste repo |
| Gate de liquidez (flag "tem opções líquidas") | 1 campo a mais no payload de scan/watchlist, calculado do lado do provider — sem chamada nova |

Nenhuma decisão desta rodada aumenta o custo O(1) por usuário que já rege o
produto — a exceção seria medir opção em `analysis_outcomes.py`, e por isso
ficou fora da v2.

---

## 6. Fora da v2 (declarado)

- **Multi-perna / travas e estruturas** — decisão já tomada antes do painel;
  fica pra v3.
- **Exercício antecipado / atribuição** — só saída por venda antes do
  vencimento ou expiração (liquidação pelo intrínseco). Opção americana pode
  ser exercida cedo; a v2 não modela isso.
- **Medir resultado de opção em `analysis_outcomes.py`** — falta série
  histórica de prêmio (restrição de redistribuição do COTAHIST); mede-se só
  a tese direcional do ativo.
- **Camada em `CarteiraScreen`/Posições** — essa tela ainda não usa
  `AtivoCard` (reconciliação incompleta, achado desta rodada); entra depois
  que isso for resolvido, não bloqueado por opções.
- **IV rank/percentile** — sem série histórica de IV, não dá para estimar
  sem inventar dado.
- **`greek_score` do score educacional** — achado incidental do painel:
  `options_quant.py:138` tem esse campo fixo em 50 (peso morto, não
  calculado). Não é escopo da v2, mas é bug real — abrindo chip separado.

---

## 7. ADRs a escrever antes de codar

Confirmado pela lente de arquitetura — três decisões irreversíveis o
suficiente pra virar ADR nomeado (formato de `docs/adr/001-fonte-de-dados-intraday.md`):

- **ADR-003 — Identidade da posição de opção**: `t` deixa de ser
  simultaneamente chave primária, chave de cotação e rótulo de UI; documentar
  o novo papel de `id`/`underlying` e o que isso propaga (catálogo, radar,
  STU, P&L hoje linear/long-only em `sell()`). Raio real, medido: **19
  arquivos tocam a forma de `positions` hoje** (13 de produção + 6 de teste;
  3 implementações independentes de cálculo de P&L; `deviceStore` em
  `persistence.js` é um espelho manual completo do `store.py`, não um
  adaptador fino). E **não existe hoje nenhum ponto único de migração de
  schema de posição** — `store.ensure_defaults` faz backfill de `config`/
  `agent`/`llmPrompts`, nunca de `positions`; campos novos sobrevivem só por
  leitura defensiva (`pos.get("alvoExtensoes") or 0`). `optionPositions`
  como coleção nova evita herdar essa dívida — mas o ADR precisa registrar
  que ela também nasce sem migração, por decisão consciente.
- **ADR-004 — Fonte de opções na v2**: o que o app pode simular com dado
  degradado do Yahoo enquanto o MyData não entrega — gatilho declarado de
  virada, no formato do ADR-001.
- **ADR-005 — Fechamento por expiração**: o terceiro motivo de saída de
  posição (hoje só COMPRA/VENDA em `history.type`, e `sell()` exige
  `priceOf(t)` — expiração sem valor é hoje inexprimível no modelo).

O resto (layout/copy da camada, quais vencimentos exibir, escopo de 1 perna,
presença nos dois modos) é decisão de produto reversível — já registrada
neste documento, sem precisar de ADR.

---

## 8. Mock

- [`qa/mocks/opcoes-camada-v1.html`](../qa/mocks/opcoes-camada-v1.html) —
  primeira rodada: linha colapsada, expansão in-place com 2 contratos, régua
  reusada. Feedback do Alex sobre este mock: gostou do card, mas não quer
  perder a visão do ativo quando opções abre.
- **[`qa/mocks/opcoes-camada-v2.html`](../qa/mocks/opcoes-camada-v2.html) —
  vigente.** Segunda rodada do painel (UX + técnica + engenharia,
  re-convocados só pra essa pergunta), decidindo entre dois caminhos que o
  Alex propôs — colapso duplo independente, ou card "frente e verso"/abas —
  e chegando a um terceiro: **"A acoplado"**. Um controle só; o ativo encolhe
  automaticamente para a espinha persistente (stop/alvo/move-dia/veredito,
  não um selo) quando opções abre; 1 contrato aberto por vez. A UX rejeitou
  "frente e verso" achando que comparar exigiria virar+memorizar+virar de
  volta; a técnica rejeitou por quebrar a verificabilidade do Princípio 5/9
  (esconder o ativo por completo não deixa o usuário *conferir* a checagem,
  só confiar num rótulo); a engenharia mediu ~5-8× mais custo pro flip 3D
  de verdade — primeiro precedente de animação complexa num componente sem
  memoização, renderizado dezenas de vezes no Radar.

---

## 9. Status — implementado, aguardando deploy (2026-08-04)

Backend e UI da v2 estão codados e verificados localmente, **não commitados
nem deployados** — aguardando revisão do Alex antes de subir.

- ADR-003/004/005 escritos em `docs/adr/`.
- `optionPositions`: coleção própria em `store.py` (`buy_option`/
  `sell_option`/`close_option_vencida`/`set_option_position`), refletida em
  `defaults.py`, `public_state`, `reset_portfolio`.
- `agent.py`: segunda passada do ciclo (`_avaliar_opcoes`) — 1 fetch por
  `(underlying, expiration)`, vencimento com prioridade sobre stop/alvo,
  trailing técnico cai no percentual (nomeado no Diário), F3 nunca se aplica
  a opção. 17 testes novos em `test_agent_options.py`; suíte completa em
  **484 testes**, 0 regressão.
- Endpoints: `POST /api/options/buy`, `POST /api/options/sell`,
  `PUT /api/options/position/{id}`, `GET /api/options/gate/{ticker}`
  (gate de descobribilidade, ADR-004 aplicado — bloqueia compra com
  `providerStatus != "ok"`).
- UI: camada "A acoplado" self-contained dentro de `AtivoCard` (nenhuma
  mudança em `MercadoScreen`/`RadarScreen` além de remover o botão "Opções ▸"
  isolado, substituído pela linha por card). Verificado ao vivo no browser:
  abertura/fechamento da espinha, accordion de 1 contrato por vez, régua de
  breakeven, compra chamando o endpoint real (rejeitado corretamente por
  contrato inexistente na cadeia real — confirma a validação de ponta a
  ponta).
- `persistence.js`: paridade iOS completa (`deviceStore` replica
  `optionPositions`, compra/venda locais, e o ramo de vencimento no `cycle()`
  — sem isso o ADR-005 pioraria a divergência dos 5 caminhos de fechamento
  já documentada).
- **Limite desta verificação**: a cadeia de opções do Yahoo está retornando
  vazia para TODOS os tickers testados neste momento (`providerStatus: "ok"`
  mas 0 calls/puts — o mesmo padrão de degradação que já afeta o
  `OptionsScreen` original). O fluxo completo (accordion, régua, compra) foi
  verificado com resposta de rede mockada no navegador; o gate em si
  (bloquear com dado ruim) foi verificado contra o backend real.
- Não implementado nesta rodada (fora do escopo declarado): overlay
  "cadeia completa" ticker-scoped (§2 mencionava; a v2 mostra até 4
  contratos inline com "ver mais", sem overlay dedicado) e IV/gregas
  completas ("Aprofundar").
