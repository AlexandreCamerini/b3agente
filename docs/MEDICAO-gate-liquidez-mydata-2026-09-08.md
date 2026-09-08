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

---

## Recalibração aplicada — 2026-09-08, mesmo dia (quick 260908-dnl)

A decisão "só documentar" durou o tempo de o Alex ler as opções e escolher a
**opção 1 — recalibrar o score**. Registro do que foi feito e do que os dados
mandaram.

### O que as 20 cadeias do catálogo ensinaram (produção, 2026-09-08)

- Volume é quase o único sinal: livro com dois lados existe em ~15% dos
  contratos (0/28 no BPAC11, 1/69 no PRIO3). Só PETR4 (28/60) e VALE3 (31/67)
  têm cobertura decente.
- Volume vem em lotes: **592/592** valores são múltiplos de 100, mínimo 100.
  `volume=100` significa "negociou uma vez".
- Escala real: mediana de 400 (RADL3) a 28.800 (VALE3); máximos até 1,8 mi.

### A primeira candidata foi descartada — e é por isso que este registro existe

Curva de volume até 75 + penalidade de livro desconhecido reduzida de 25 para
10. Passava nos critérios olhando PETR4 e VALE3. Nas 20 cadeias: pass-through
— 15/15, 66/66, 69/69. `ABEVU147W2` com volume 100 e livro vazio passava a
51,1; `PETRI556` com spread **medido** de 147% reprovava a 39,6. Ter dado
piorava a nota. Falhou o critério fixado antes de olhar os dados ("volume 500
com um lado zerado reprova").

### A fórmula que ficou

```
atividade = max(curva(volume), curva(open_interest))
curva(x)  = clamp((log10(x + 1) − 1) × 20, 0, 75)
score     = clamp(atividade + 25 − spread_penalty, 0, 100)
```

`spread_penalty` **byte-idêntica** à anterior (0/8/18/30 medido; 25
desconhecido). Única mudança conceitual: a atividade pode ser carregada por
volume sozinho, e o open interest — quando a fonte o publica — **substitui**
o volume em vez de somar (mantém o caminho Yahoo de rollback sem inflar nada
no mydata).

Piso sem livro: **1.000 unidades (10 lotes)** — onde a curva de volume
original saturava. Derivado, não tunado.

### Resultado contra as mesmas 20 cadeias, com o código real

| | antes | depois |
|---|---|---|
| cadeias com gate aprovado | 2/18 (VALE3, WEGE3) | **18/18** |
| contratos aprovados | 3/592 | **461/592 (78%)** |
| contratos reprovados | 589 | 131 — continua sendo gate |
| PETR4 | 0/60 | 50/60, mín. volume 1.000 |
| RADL3 (o mais fino) | 0/10 | 3/10, mín. volume 1.500 |

### O que mudou fora da fórmula

- Dois guardiões travavam o valor antigo e foram **atualizados com nota
  datada**, não apagados: `test_options_provider_mydata.py` (literal 52,0 →
  71,0; a docstring antiga documentava o teto de 60 e deixava o resto "para o
  checkpoint de virada") e a fixture do collar em `test_opcoes_collar.py` (put
  com volume 100 reprova agora e o motor nem a seleciona).
- Guardião novo `server/tests/test_liquidity_score_mydata.py`: os critérios
  sintéticos fixados antes de olhar os dados, linhas reais congeladas de
  produção, a fronteira explícita (1.000 passa, 900 reprova), OI substitui
  volume, monotonicidade.
- **Mock fiel ao mydata** (commit separado): `MOCK_OPEN_INTEREST = None`,
  `MOCK_VOLUME = 5000`. O mock tinha OI 2000, que salvava o volume 500 — a
  mesma cegueira do ADR-020. Staging aprovava por um campo que produção nunca
  tem.

### O que continua pendente

- **Deploy.** Está na branch `v2/interacao-estrutural`; só vale em produção
  depois de promovido.
- **Open interest de verdade** (opção 3): a B3 publica em arquivo separado do
  COTAHIST; ingestão pertence ao MyData. Quando existir, a fórmula já o
  consome — `curva(open_interest)` substitui o volume automaticamente.
- A mensagem "nenhuma posição com opção líquida hoje" continua atribuindo ao
  mercado o que é da medição, nos casos residuais em que o gate reprova.
  Menor agora, mas não zero.
