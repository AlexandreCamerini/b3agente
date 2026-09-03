# ADR-026: Execução de estrutura multiperna — aceite do collar (Fase 17)

**Status:** Aceito
**Data:** 2026-09-03
**Decisor:** Alex (autonomia concedida em `17-CONTEXT.md`, seção "FLOW-03 —
execução real do collar (decisão de escopo desta sessão)").
**Base:** ROADMAP Fase 17; `17-CONTEXT.md`; `17-01-SUMMARY.md`
(`store.abrir_collar`); `17-02-SUMMARY.md` (frescor `source`/`at`);
ADR-025 (as cinco decisões da Fase 16 e a "Limitação conhecida" que este ADR
fecha).

---

## Contexto

O ADR-025 (Decisão 5, seção "Limitação conhecida — guarda por
autoidentificação") documentou explicitamente uma dívida: a trava de 400 do
Plano 16-04 (`POST /api/options/lastreada/abrir`) recusa qualquer corpo que
se declare `tipo == "collar"` ou traga mais de uma perna em
`pernasContratos`, mas essa trava confia no que o PRÓPRIO CLIENTE afirma
sobre o corpo — ela não re-deriva a partir da cadeia/posição/caixa reais.
Isso era aceitável na Fase 16 porque nenhum cliente publicado montava corpo
multiperna; o próprio ADR-025 já registrava que isso "torna-se um item de
hardening real a partir do momento em que a Fase 17 construir um cliente que
negocia `multiperna=1` de verdade". A Fase 17 é exatamente esse momento: o
Plano 17-01 entregou `store.abrir_collar` (execução atômica das 2 pernas) e
o Plano 17-03 liga isso a uma rota HTTP nova, `POST
/api/options/lastreada/abrir-collar`, que precisa fechar a lacuna do
ADR-025 no mesmo movimento em que abre o caminho de execução. Cinco
decisões concretas nasceram desse trabalho.

## Decisão 1 — Rota nova em vez de flag na rota antiga

A execução do collar entra por uma rota HTTP própria
(`options_lastreada_abrir_collar`), definida imediatamente após
`options_lastreada_abrir` e antes de `options_lastreada_fechar`. A rota
antiga (`/abrir`) e a trava de 400 do Plano 16-04 ficam intocadas — `git
diff` do plano confirma que nenhuma linha daquela função foi alterada.

**Alternativa descartada:** um parâmetro `permitirMultiperna` (ou
equivalente) no corpo de `/abrir`, que faria a mesma rota decidir entre
executar uma perna ou uma estrutura de duas. Descartada porque a trava do
Plano 16-04 existe precisamente para impedir que um corpo declare
"múltiplas pernas" e a rota execute mesmo assim — transformar essa defesa
num campo booleano que o cliente controla é entregar ao cliente exatamente
o poder que a trava foi desenhada para negar a ele. Uma rota nova preserva a
trava antiga como estava e cria uma superfície de escrita separada, mais
fácil de auditar (uma função, uma responsabilidade) do que uma bifurcação
condicional dentro da rota já existente.

## Decisão 2 — Re-derivação server-side da proposta antes de executar

`options_lastreada_abrir_collar` nunca confia no corpo da requisição para
decidir O QUE executar. Ela repete o pipeline de `options_proposta` (busca
de cadeia, posição, caixa, plano técnico) e chama
`opcoes_lastreadas.propor(..., multiperna=True)` de novo, a cada chamada,
sobre o estado ATUAL — e cruza os `contractSymbol`/`lado` submetidos contra
essa proposta fresca (comparação de dict `símbolo→lado`, que cobre de uma
vez contrato trocado, contrato faltando, contrato duplicado e lado
invertido). Os prêmios e a quantidade executados vêm sempre da proposta
re-derivada, nunca do corpo. Isso fecha, byte a byte, a "Limitação
conhecida" do ADR-025.

**Alternativa descartada:** assinar a proposta original (HMAC/nonce) no
momento em que `GET /api/options/proposta/{ticker}` a devolve, e validar a
assinatura no aceite. Resolveria adulteração do corpo, mas não resolveria o
problema maior: o dado ficar VELHO entre o instante da proposta e o
instante do aceite (posição vendida em outra aba, caixa consumido por outra
operação, cadeia que expirou o contrato). Um produto de simulação de
mercado real tem esse segundo risco como o dominante — re-derivar resolve
os dois problemas (integridade E frescor) reaproveitando o pipeline que já
existe, sem introduzir um mecanismo de assinatura novo só para o primeiro.

## Decisão 3 — Atomicidade a nível de ESTRUTURA

A execução das duas pernas usa `store.abrir_collar` (Plano 17-01), que
valida e escreve as DUAS pernas dentro de UMA única aquisição de
`ORDER_LOCK` — nenhuma escrita acontece se qualquer validação (tipo de
contrato, underlying, lastro, caixa) falhar em qualquer uma das pernas.

**Alternativa descartada:** compor `store.abrir_call_coberta` +
`store.comprar_put_protecao` (as duas funções single-leg já existentes) em
sequência dentro da rota. Descartada porque não funciona nem no caminho
feliz: `ORDER_LOCK` é `RLock`, então a composição não deadlocaria, mas a
PRIMEIRA chamada já teria persistido caixa/posição/`qtyTravada` antes de a
validação da SEGUNDA rodar — se a segunda perna fosse então recusada
(lastro que a primeira acabou de consumir, caixa que a primeira acabou de
debitar), o usuário ficaria com METADE da trava protetora, exposto a um
risco diferente do apresentado na tela. Exatamente a execução de meia
estrutura que toda esta fase existe para impedir (mesmo racional do
docstring de `abrir_collar`, 17-01-SUMMARY.md).

## Decisão 4 — 409 para proposta vencida, 400 para corpo malformado

Quando o corpo é sintaticamente inválido (menos/mais de duas pernas,
`underlying` ou `contratos` malformados), a rota devolve 400. Quando o
corpo está bem formado mas a proposta RE-DERIVADA não bate (motor não
propõe mais collar, contrato/lado/quantidade divergem da proposta fresca),
a rota devolve 409.

**Alternativa descartada:** 400 para os dois casos, sem distinção.
Descartada porque apagaria a diferença entre "o cliente errou ao montar o
corpo" (ação corretiva: consertar o corpo) e "o mercado ou a carteira
mudaram entre a proposta exibida e o aceite" (ação corretiva: buscar a
proposta de novo) — justamente a informação que a UI (Plano 17-05) precisa
para decidir entre reexibir um erro de formulário e recarregar a proposta
inteira. Usar o código de status HTTP para carregar essa distinção evita
que o cliente precise fazer parsing de string na mensagem de erro para
saber o que fazer a seguir.

## Decisão 5 — Porta de caixa sobre o custo LÍQUIDO da estrutura

`store.abrir_collar` (Plano 17-01) rejeita por caixa insuficiente apenas
quando o CUSTO LÍQUIDO da estrutura (`qty * (premio_put - premio_call)`)
excede o caixa disponível — um collar de crédito líquido (prêmio da call
vendida ≥ prêmio da put comprada) nunca aciona essa porta, porque o próprio
lastro financia a estrutura.

**Alternativa descartada:** exigir caixa disponível para o prêmio BRUTO da
put comprada, ignorando o crédito da call vendida na mesma operação.
Descartada porque recusaria travas que de fato cabem no caixa do usuário —
as duas pernas do collar liquidam no mesmo instante atômico (mesma
aquisição de `ORDER_LOCK`, Decisão 3), então validar o débito bruto de uma
perna isolada, sem considerar o crédito simultâneo da outra, é uma conta
que não corresponde ao dinheiro que de fato muda de mãos na operação.

## Limitações conhecidas

Registradas sem maquiar, para não repetir o padrão do ADR-025 (que também
nomeou sua limitação em vez de escondê-la):

- **O ENCERRAMENTO da trava protetora continua perna a perna**, pela rota
  `/api/options/lastreada/fechar` já em produção — fechar uma perna de um
  collar aberto é possível e não é impedido por esta fase. Justificativa:
  sair de uma proteção é decisão deliberada do usuário sobre uma posição já
  existente, categoria diferente de ABRIR meia estrutura sem querer (o risco
  que as Decisões 1-3 mitigam); unificar o encerramento das duas pernas
  numa única chamada é escopo de fase futura, não desta.
- **Depois de um collar aberto, `GET /api/options/proposta/{ticker}` cai no
  ramo `pos_op_aberta`** e oferece o fechamento da PRIMEIRA posição
  lastreada encontrada naquele underlying — comportamento herdado da Fase
  14, não introduzido por este ADR nem pela rota nova.
- **`at` da rota de proposta é o instante da montagem da resposta**, não o
  carimbo do pregão do dado que sustentou a proposta (T-17-07 do Plano
  17-02) — a rota de aceite herda essa mesma semântica de frescor porque
  re-deriva com o mesmo pipeline.

## Consequências

**Fica mais fácil:**
- A limitação nomeada no ADR-025 deixa de existir: qualquer cliente que
  negocie `multiperna=1` na proposta e monte o corpo de aceite tem a
  garantia de que o servidor nunca executa uma estrutura diferente da que a
  cadeia/posição/caixa ATUAIS realmente sustentam.
- A rota de aceite reusa o mesmo pipeline técnico já exposto por leitura
  (`options_proposta`), sem introduzir um segundo caminho de cálculo de
  proposta a manter sincronizado com o primeiro.

**Fica mais difícil / o que se paga:**
- Uma rota de ESCRITA agora paga o custo do pipeline técnico completo
  (candles, indicadores, setups) a cada aceite — aceito conscientemente
  (T-17-14 do threat model do Plano 17-03: mesmo cache de 300s do provider
  já usado pela rota de leitura, risco equivalente ao já aceito para
  aquela).
- Duas rotas de abertura lastreada agora existem (`/abrir` para uma perna,
  `/abrir-collar` para duas) — mais superfície de API para manter em
  paridade de comportamento (403/502/histórico) do que uma única rota
  genérica teria, trade-off aceito pela Decisão 1.

**A revisitar:**
- Se uma quarta estrutura de N pernas for adicionada no futuro (ADR-025 já
  cogitava isso para `propor()`), vale reavaliar se cada estrutura nova
  ganha sua própria rota de aceite ou se o padrão migra para uma rota
  genérica orientada por `tipo` — decisão adiada até haver uma terceira
  estrutura multiperna real para comparar.

## Referências

- ADR-025 — as cinco decisões da Fase 16 e a limitação que este ADR fecha.
- `.planning/phases/17-fluxo-de-aceite/17-CONTEXT.md` — decisão de escopo
  FLOW-03 (autonomia concedida).
- `server/app/store.py::abrir_collar` — execução atômica das 2 pernas
  (Plano 17-01).
- `server/app/main.py::options_lastreada_abrir_collar` — a rota que este
  ADR documenta (Plano 17-03).
- `server/tests/test_opcoes_collar_execucao.py` — guardiões de estrutura do
  motor (`store.abrir_collar`).
- `server/tests/test_opcoes_collar_rota.py` — guardiões de re-derivação,
  cross-check de contratos e não-regressão da trava de 16-04 (Plano 17-03).

---
*Fase: 17-fluxo-de-aceite*
*ADR: 026*
