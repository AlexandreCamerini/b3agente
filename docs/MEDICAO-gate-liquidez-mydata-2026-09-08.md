# Medição — o gate de liquidez de opções é impossível de cruzar com mydata

**Data:** 2026-09-08
**Fonte da medição:** produção ao vivo (`https://bolsia.semente.dev`), rotas
públicas `GET /api/options/gate/{ticker}` e `GET /api/options/chain/{ticker}`.
Nenhuma credencial envolvida — as duas rotas são sem autenticação.
**Origem:** o Alex reportou que a tira "Oportunidades de opções" não aparece
no Portfólio. Não era defeito da tira.

## O que foi medido

Produção roda `B3_OPTIONS_PROVIDER=mydata` (registrado em `STAGING.md`, tabela
de configuração do environment). O provedor **responde normalmente**:
`providerStatus: "ok"` em todos os casos abaixo. Quem reprova é o gate.

| ticker | `liquida` | `providerStatus` |
|---|---|---|
| ABEV3 | **false** | ok |
| PETR4 | **false** | ok |
| VALE3 | true | ok |
| ITUB4 | **false** | ok |

Cadeia do PETR4 (`source=mydata`, vencimento 2026-09-11, 60 contratos), os
melhores por `liquidity_score`:

```
 score contrato            vol     OI     bid     ask  spread%
  35.0 PETRI478W2        88100   None     0.0     0.0     None
  35.0 PETRU436W2        79300   None    0.02     0.0     None
  35.0 PETRU493W2        49300   None    1.34     0.0     None
  35.0 PETRU498W2        25700   None    0.45     0.0     None
```

**Todos os 60 contratos empatam em 35,0.** O corte é 40. Um contrato com
88.100 unidades negociadas é classificado como ilíquido.

VALE3 (67 contratos) passa por dois pontos: 31 contratos têm os dois lados do
livro preenchidos, e o melhor deles mede **42,0** — com spread real de 17,28%.

## Por que 35, e por que é um teto e não um acaso

`options_quant.liquidity_score` soma três parcelas:

```
score = vol_score(máx 35) + oi_score(máx 40) + 25 − spread_penalty
```

Duas parcelas se perdem com o mydata:

1. **`openInterest` é sempre `None`.** O COTAHIST não publica posições em
   aberto, e o adaptador grava `None` fixo
   (`server/app/options_provider_mydata.py:107`, comentário "SEM FONTE").
   Perde-se `oi_score` inteiro — até 40 pontos.

2. **O livro chega com um lado zerado.** O spread só é calculado quando
   `bid > 0 E ask > 0`; fora disso aplica-se a penalidade padrão de **25**,
   que é a de "spread desconhecido". Nos dados reais do PETR4, nenhum dos 60
   contratos tem os dois lados.

Sobra o teto de volume, 35 pontos, contra um corte de 40. A tabela de
viabilidade, calculada antes de consultar produção e confirmada por ela:

| spread | volume mínimo para cruzar o corte |
|---|---|
| ≤ 3% | 20 |
| ≤ 8% | 100 |
| ≤ 18% | 600 |
| > 18% | **impossível em qualquer volume** |
| sem bid/ask | **impossível em qualquer volume** |

Não é "contrato fraco pode não passar". É uma **faixa de impossibilidade**:
sem os dois lados do livro, nenhum volume cruza o corte.

## Relação com o que o ADR-020 previu

ADR-020 registrou o risco e o deixou explicitamente em aberto:

> `openInterest` **não tem fonte no COTAHIST** — o campo é sempre `None` no
> adaptador. Efeito MEDIDO (não estimado) no Plano 09-03: um contrato PETR4
> realista (volume 5.000, spread ≈5,41%) mede `liquidity_score=52,0` (corte
> de aprovação é 40) — passa, mas o teto do score cai de 100 para 60 sem open
> interest; contratos de volume mais baixo que hoje dependiam do open interest
> real podem deixar de cruzar o corte. **Achado registrado para o checkpoint
> de virada, não corrigido nesta fase.**

A virada aconteceu; o acompanhamento não. Duas correções ao que aquele
registro concluiu:

- O caso medido lá era **hipotético favorável** (spread 5,41%, os dois lados
  do livro presentes). O PETR4 real — o ticker do próprio exemplo — não tem
  os dois lados em nenhum contrato, e reprova.
- O risco descrito era gradual ("volume mais baixo pode não cruzar"). A
  medição de hoje mostra que ele é **categórico** para a maior parte da
  cadeia: nenhum volume salva um contrato sem spread calculável.

## Consequência de produto, hoje

A funcionalidade de opções (Fases 14, 16, 17, 18, 19) está **apagada em
produção para quase todo o catálogo**. Não por defeito de UI, não por falha de
fonte — por um corte calibrado para uma fonte que publicava open interest,
ainda aplicado a uma que não publica.

E a mensagem exibida atribui a causa errada:

> "Nenhuma posição com opção líquida hoje — sem contrato líquido, não há
> estrutura para montar."

O PETR4 negociou 88.100 unidades. A frase fala do **mercado**; o fato é sobre
a **medição**. Um usuário conclui que a B3 não tem liquidez em opções, o que é
falso. Isto tangencia o princípio 3 do CLAUDE.md (o estado da fonte deve
aparecer) — não é dado inventado, mas é causa mal atribuída.

## Decisão

**Documentar agora, recalibrar depois** — decisão do Alex, 2026-09-08, entre
quatro opções apresentadas (recalibrar o score, baixar o corte para 30, buscar
open interest na B3, só documentar).

Nada foi alterado em `options_quant.py` nem no corte. Mexer no gate muda o que
o app **afirma** sobre liquidez, e afrouxá-lo faria um simulador educacional
propor estrutura sobre opção genuinamente fina — decisão de produto, não de
implementação.

Quando for recalibrar, as opções levantadas e seus custos:

1. **Recalibrar o score** — redistribuir os 40 pontos do open interest para
   volume e separar "spread desconhecido" de "spread ruim". Faz o score voltar
   a medir liquidez com o dado que existe, mantendo o corte em 40. Nada
   afrouxa de fato; só para de reprovar contrato líquido.
2. **Baixar o corte para 30** — uma linha, efeito imediato, não conserta a
   causa: continua tratando "não sei o spread" como "spread ruim".
3. **Buscar open interest na B3** — publicado em arquivo separado do COTAHIST.
   Corrige a raiz e devolve o teto de 100, mas é ingestão nova e pertence ao
   MyData, não ao Boris.

## Como reproduzir

```bash
for t in ABEV3 PETR4 VALE3 ITUB4; do
  curl -s "https://bolsia.semente.dev/api/options/gate/$t"; echo
done
```

Para os scores contrato a contrato, buscar `/api/options/chain/{ticker}` e
aplicar `options_quant.liquidity_score(volume, openInterest, bid, ask)` sobre
`calls + puts`.

## Nota de doc desatualizada

`docs/adr/021`, `docs/adr/022`, `docs/OPERACAO-ciclo-de-vida-put.md` e
`docs/OPERACAO-ponte-gatilho-put.md` afirmam que `B3_OPTIONS_PROVIDER=yahoo` é
"o default de produção". Era verdade quando foram escritos; deixou de ser com
a virada para `mydata`. O texto da época fica como está (histórico não se
reescreve); esta nota existe para que a próxima pessoa que ler aqueles
arquivos não repita o erro de tomá-los como estado atual — foi exatamente o
que aconteceu nesta investigação antes da medição.

Fonte de verdade sobre o que cada environment roda: a tabela de configuração
em `STAGING.md`.
