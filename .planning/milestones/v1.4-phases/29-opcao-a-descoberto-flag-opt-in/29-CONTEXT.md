# Fase 29 — Opção a descoberto com flag opt-in · CONTEXT

> Consolidado por Claude, sem `/gsd-discuss-phase` assistido por subagente
> (mesma economia de orçamento da Fase 28). Ao contrário da 28, esta fase
> tinha decisões de produto genuínas — D1 e D2 foram levadas ao Alex com
> recomendação (não presumidas) e ele as confirmou em 2026-09-13; D3 segue
> aberta por ser trivial, decidida no plano de execução.

## Por que esta fase existe

Decisão do Alex, registrada em `26-CONTEXT.md` (2026-09-12): operar opções
fica restrito a posições com lastro **por padrão**; operar **a descoberto**
exige um flag opt-in em Configurações. Citação literal do pedido original:

> "só é permitido operações com opções quando você tem lastro de ações que
> te permitam isto. para operar sem ter lastro tem que ligar um flag no
> setor configurações."

A Fase 28 trouxe as operações **lastreadas** (venda coberta, put de
proteção, collar) para dentro da aba Opções e deixou a descoberto **fora de
escopo, explicitamente**, porque o flag não existe em lugar nenhum do
código. Esta fase constrói o flag e o gate que faltam.

## O que já existe hoje (verificado por leitura direta, 2026-09-13)

1. **O caminho "a seco" já existe em produção, sem NENHUM gate.**
   `buy_option`/`sell_option` (`server/app/store.py:774,829`) compram e
   vendem um contrato de opção sem checar lastro nenhum — ao contrário de
   `abrir_call_coberta`/`comprar_put_protecao`/`abrir_collar`
   (`store.py:894,1029,1117`), que checam `qty_livre(pos_acao) < qty` e
   rejeitam com "Lastro insuficiente...". `buy_option` não tem essa checagem
   porque, por definição, uma compra a seco NÃO tem lastro — é a operação
   que o flag existe para autorizar ou barrar.
2. **A UI do caminho a seco é `OpcoesCamada`** (`web/src/App.jsx:3430`),
   dentro do `AtivoCard` em Watchlist/Radar — `doBuyOption`/`doSellOption`
   chamam `A.buyOption`/`A.sellOption`, que mapeiam direto para
   `store.buy_option`/`sell_option`. `myOptionPositionsLegado` (filtro
   `!p.lastro`) já separa essas posições das lastreadas na mesma tela — o
   conceito "posição sem lastro" já existe no dado, só não tem gate nem flag.
3. **Nenhum flag existe hoje.** Grep vazio por
   `naked`/`a_descoberto`/`permitirNaked`/variantes em todo `server/app/` e
   `web/src/`. O padrão de persistência para um flag assim já existe —
   `store.putConfig({ chave: valor })`, usado por `theme`, `notif`,
   `gestoUso`, `apiKey` (`App.jsx:8540-8724`) — nos dois stores
   (`deviceStore`/`serverStore`), com o mesmo contrato.
4. **O Operador IA (`agent.py`) já fecha posição de opção sozinho, nunca
   abre.** Pesquisa da Fase 26 (`26-CONTEXT.md`, "Pesquisa CONCLUÍDA"):
   `scheduler_loop` fecha lastreada por stop/alvo/vencimento
   automaticamente; abrir posição nova — lastreada OU a descoberto — não
   tem nenhum precedente de código, é construção do zero. Fechar uma
   posição a seco que o agente já gerencia (se o usuário abriu manualmente)
   é extensão natural do padrão existente; abrir automaticamente
   continua fora de escopo desta fase (ninguém pediu).
5. **Existe precedente de consentimento explícito para uma decisão de
   risco**: o toggle Modo Estudo → Operador (`App.jsx`, Perfil) já pede
   leitura de um "Termo de Responsabilidade" até o fim, com checkbox e
   texto versionado ("Modo Operador · versão 1.0"), antes de liberar
   decisão direta. Verificado ao vivo na Fase 28 (o modal existe e
   funciona, embora tenha se mostrado frágil a automação de teste — não é
   bug de produto, é limitação do ambiente de QA).

## Decisões herdadas (não re-litigar)

- **Lastro obrigatório por padrão é o invariante desta fase inteira.** O
  flag é a EXCEÇÃO nomeada, nunca o padrão — conta nova nasce com o flag
  desligado, sem exceção, sem migração silenciosa de contas existentes para
  "ligado".
- **Fechar uma posição já aberta nunca é bloqueado pelo flag.** Isto não
  foi dito explicitamente pelo Alex, mas é a mesma lógica já aplicada a
  stop/alvo em todo o resto do produto (CLAUDE.md, guardrail do
  repositório: "Stop/alvo nunca são vetados... a UI sempre permite Aplicar
  proteção") — impedir alguém de SAIR de uma posição a seco que ele já tem
  (por exemplo, se o flag foi desligado depois de aberta) seria pior que
  não ter gate nenhum. `sell_option` fica **fora** do gate; só `buy_option`
  (abrir posição nova) entra.
- **A recusa é do backend, sempre** — mesmo padrão de todo o resto do
  produto (CLAUDE.md, anti-padrão "esconder admin só no front"). A UI pode
  e deve esconder/desabilitar o controle quando o flag está desligado, mas
  isso é conveniência, não a defesa.

## Decisões (fechadas em 2026-09-13, confirmadas pelo Alex)

### D1 — Fechado: mesmo termo de responsabilidade do Modo Operador

**Decisão: ligar o flag exige o mesmo padrão de fricção do Modo Operador**
— modal com termo de responsabilidade, leitura até o fim, checkbox,
versão do texto registrada. Simetria de risco: operar a descoberto não é
menos arriscado que ligar o Modo Operador, então não recebe menos fricção.
O plano de execução reusa o padrão visual/estrutural já existente (mesmo
componente ou variação dele), não inventa um terceiro modal do zero.

### D2 — Fechado: escopo estreito, só flag + gate no backend

**Decisão: esta fase constrói o flag em Configurações e o gate em
`buy_option` — nada além disso.** A UI de compra a seco (`OpcoesCamada` em
`AtivoCard`, Watchlist/Radar) **continua onde está**, sem migrar para a
sub-aba "Operar" (Fase 28). O único comportamento novo na UI existente é a
recusa: tentar comprar a seco com o flag desligado mostra a mensagem do
backend, não inventa um caminho novo de compra. Migrar `OpcoesCamada` para
"Operar" — completando o pedido original de trazer as quatro operações
para a aba Opções — fica para uma fase seguinte, sobre o gate já fechado e
testado, não junto com ele.

### D3 — Nome e semântica exata do flag

Não decidido: nome do campo (`permitirOpcaoADescoberto`? outro?), e se é
booleano simples ou se guarda também a data de aceite (mirando o padrão do
Modo Operador, que registra versão do termo + timestamp). Trivial de
decidir no plano de execução, não bloqueia o desenho da fase — o Alex não
teve preferência quando perguntado.

## Fora de escopo (explícito)

- **Abrir posição de opção automaticamente pelo Operador IA** — lastreada
  ou a descoberto. A pesquisa da Fase 26 já provou que não existe
  precedente nenhum; seria construção do zero, não pedida aqui.
- **Migração da UI de `OpcoesCamada` para "Operar"** — decisão D2, fechada:
  fica para uma fase seguinte, sobre o gate já testado.
- **Curadoria de IA das 4 melhores estruturas** (Fase 30) e **polish de UX**
  (Fase 31) — dependem desta fase existir primeiro, não o contrário.

## Guardrails (herdados, não re-litigar)

- **Princípio 5 do CLAUDE.md**: nenhuma linha desta fase aproxima a IA de
  decidir ou calcular risco/lastro — o gate é uma regra determinística no
  backend, ponto.
- **Paridade obrigatória** `deviceStore` ↔ `serverStore` em
  `web/src/persistence.js` — o flag, sendo config, precisa existir nos
  DOIS lados do `putConfig`/leitura, como todo campo de config existente.
- **Guardiões de teste não se apagam** — reversão deliberada atualiza com
  nota datada.
- **Suíte canônica**: `bash scripts/executar.sh --testes`, fora do
  sandbox. Front editado → `npx vite build` antes de declarar ok.
- **Verificação adversarial (`gsd-plan-checker`) recomendada para esta
  fase**, ao contrário da 28 — é a parte que toca lastro/execução de ordem
  real que o pedido original do Alex nomeou como merecendo esse cuidado
  extra. Decisão de rodar ou não fica para quando o plano estiver pronto,
  não agora.
