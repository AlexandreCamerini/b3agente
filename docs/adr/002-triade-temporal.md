# ADR-002: Tríade temporal — horizonte × intervalo × período

**Status:** Proposto — a implementar **depois** da validação do atraso ([ADR-001](001-fonte-de-dados-intraday.md) § Decisão 2)
**Data:** 2026-07-31
**Decisor:** Alex
**Relacionado:** ADR-001 (fonte de dados intraday)

---

## Contexto

A F1 introduz o intervalo como parâmetro real. Antes de espalhá-lo pelo app,
este ADR fecha **como os três parâmetros temporais se relacionam** — porque hoje
eles não se relacionam de jeito nenhum, e um deles não faz nada.

### Estado verificado (31/07/2026)

| Parâmetro | Onde vive | O que ele REALMENTE faz hoje |
|---|---|---|
| `horizonte` (`intraday`\|`swing`\|`posicao`) | `defaults.py:205`, validado em `store.py:229` | **NADA.** Único uso: uma linha de texto no prompt (`llm.py:220`) |
| `candlePeriod` (`1mo`…`2y`) | `candles.py` | Define `keep`/`tail_n` — a janela EXIBIDA e enviada à IA. Os indicadores são sempre calculados sobre o warmup de 2 anos |
| `interval` | `candles.py:VALID_INTERVALS = ("1d","1wk")` | Existia sem uso no STU. Passou a existir de fato na camada de dados (ADR-001, itens 5–7) |

O `horizonte` é o problema mais sério: um usuário marcado como `intraday` recebe
**exatamente** os mesmos candles, indicadores, famílias, setups e plano
operacional de um marcado como `posicao`. Só a IA "sabe" do horizonte — e fala
como se os números tivessem sido calculados para ele. **Isso é pior que o
parâmetro não existir**, porque promete uma personalização que não acontece.

### Três armadilhas de degradação silenciosa

O padrão já apareceu duas vezes nesta linha de trabalho (o colapso de velas por
data e o `range=max` devolvendo dado mensal). Combinar os três parâmetros sem
regra cria mais três:

1. **Impossível.** `5m` + `2y` → HTTP 422. O Yahoo não tem 5m além de 1 mês.
2. **Indicador mudo.** `60m` + `1mo` = 155 velas. **SMA200 nunca produz valor**:
   a família tendência emudece e os setups que filtram por SMA200 (o IFR2,
   conforme `indicators.py:257`) param de disparar. Sem erro nenhum.
3. **Janela truncada.** `resolve_keep("1mo")` devolve **22** — vinte e dois
   *pregões*. Com `interval=15m` isso vira 22 *velas de 15 minutos*, ou seja
   **5,5 horas** de contexto para detectar setup, quando o usuário pediu um mês.
   `technical_snapshot.py:80` usa esse número direto.

Nenhuma das três levanta exceção. Todas produzem análise plausível e errada.

---

## Decisão 1 — A tríade é um objeto único, e o horizonte é o driver

Os três parâmetros deixam de ser campos soltos e passam a formar uma
**tríade temporal** validada em conjunto.

> **O horizonte é a escolha do usuário. Intervalo e período são consequência —
> sobrescrevíveis, mas só dentro do envelope legal.**

A dependência é funcional, não estética:

- o **horizonte** define quanto tempo a operação dura;
- o **intervalo** precisa ser tal que a operação caiba em ~10–30 velas (abaixo
  disso não há estrutura para ler; acima, é ruído);
- o **período** precisa conter pelo menos **200 velas do intervalo escolhido**,
  senão a SMA200 é nula e a leitura degrada em silêncio.

Três botões livres dariam 4 × 5 × 3 = 60 combinações, boa parte inválida. Um
driver com envelope dá um punhado de combinações, todas verificáveis.

## Decisão 2 — A matriz legal

| Horizonte | Intervalo | Período | Velas/pregão | 200 velas em | Disponível no Yahoo |
|---|---|---|---|---|---|
| `intraday` curto | `5m` | 1mo | 85 | ~2,4 pregões | 1.821 ✓ |
| **`intraday` (default)** | **`15m`** | **1mo** | **29** | **~7 pregões** | **617 ✓** |
| `intraday` lento | `30m` | 1mo | 15 | ~13 pregões | 309 ✓ |
| `swing` | `60m` | 6mo | 8 | ~25 pregões | 855 ✓ |
| `swing` (default) | `1d` | 6mo | 1 | 200 pregões | ✓ |
| `posicao` | `1d` | 1y–2y | 1 | 200 pregões | ✓ |

Todas as linhas cabem no limite real do Yahoo (medido em 30/07) **e** entregam
SMA200 válida. Qualquer combinação fora desta tabela é recusada na borda com
mensagem que diz o porquê — nunca aceita e degradada.

**Teto que precisa ser declarado:** `candle_cache._MAX = 600`. Com `5m` + `1mo`
(1.821 velas) a série é cortada em 600, ou seja **~7 pregões efetivos**, não um
mês. Isso não é bug, é o teto de RAM — mas precisa aparecer na UI, senão o
usuário pede um mês e recebe uma semana sem saber.

## Decisão 3 — `resolve_keep` passa a conhecer o intervalo

`resolve_keep(period)` → `resolve_keep(period, interval)`, devolvendo o número
de velas **daquele intervalo** que cobrem o período pedido:

```
velas = pregões_do_período × velas_por_pregão[intervalo]
```

Com `interval="1d"` o resultado é idêntico ao de hoje (`velas_por_pregão = 1`),
então nada do diário muda. É a correção da armadilha nº 3.

## Decisão 4 — A calibragem viaja com a tríade

O ponto que costuma passar despercebido: **os limiares das famílias estão
calibrados para o diário**. Trocar o intervalo sem trocá-los não gera erro —
gera leitura sistematicamente errada.

| Família | Limiar de hoje | O que acontece em `15m` |
|---|---|---|
| **Volatilidade** | largura das Bandas `< 6%` = compressão, `> 12%` = expansão (`technical_models.py:170`) | A largura em 15m é fração da diária: **tudo vira "compressão"**, sempre, para todo ativo |
| **Volume** | volume vs. média da série | O pregão tem sazonalidade em U: abertura e fechamento têm volume estruturalmente alto. A vela das 10:00 seria "volume excepcional" **todo dia** |
| **Tendência** | ADX ≥ 25 definida, < 20 fraca | Convenção é timeframe-agnóstica, mas o ADX intraday oscila mais — o estado troca com mais frequência |
| **Momentum** | RSI 14, MACD 12/26/9 | Períodos são convenção; funcionam em qualquer timeframe |

Portanto a tríade carrega **parâmetros de calibragem por intervalo**, não só a
seleção de famílias. Duas consequências concretas:

- os limiares de regime de volatilidade passam a vir da tríade, não de constantes;
- o comparativo de volume no intraday é contra **o mesmo horário de pregões
  anteriores**, não contra a média da série.

A **fonte da metodologia continua sendo `skill_ref.py`** — a calibragem é
parâmetro numérico, não persona nova.

## Decisão 5 — Fronteira de custo: Radar global, tríade sob demanda

Colide com a Decisão 3 do ADR-001, que fixou o Radar como **global** (65 ativos,
uma varredura, custo O(1) no número de usuários). Se o intervalo virasse
preferência por usuário, a varredura deixaria de ser compartilhável e o custo
viraria O(usuários × intervalos).

**Decisão do Alex:**

- **O Radar roda num intervalo canônico e global**: `1d` (como hoje) e, quando a
  F1 entrar, `15m`. Dois caches globais, custo constante em usuários.
- **A tríade completa vale na análise SOB DEMANDA de um ativo** — que já é por
  usuário e por ativo, então a configurabilidade não escala o custo.

O `snapshotId` já segmenta por intervalo (ADR-001, Decisão 5), então as duas
varreduras convivem sem colidir.

---

## Invariantes (o que o guardião precisa provar)

Sem isto, 60 combinações viram 60 modos de falhar em silêncio. O teste percorre
**toda a matriz legal** e prova, para cada linha:

1. **Dado real chega** — a combinação (intervalo, período) não toma 422 nem
   devolve granularidade diferente da pedida.
2. **SMA200 não é nula** — se for, a família tendência mente por omissão.
3. **A janela pedida é a janela entregue** — `resolve_keep` devolve velas do
   intervalo certo, e o corte de `_MAX` é declarado, não silencioso.
4. **Nenhuma contradição veredito↔plano** — o invariante que o
   `scripts/masstest-agentes.py` já cobre, agora por combinação.
5. **Combinação ilegal é recusada na borda**, com mensagem que nomeia o motivo.

## Consequências

**Fica mais fácil**
- O `horizonte` passa a significar alguma coisa: hoje ele é texto no prompt.
- Adicionar um intervalo novo vira uma linha na matriz, com o guardião cobrindo.
- A IA deixa de receber "horizonte intraday" junto de números calculados no
  diário — a incoerência de hoje.

**Fica mais difícil**
- A superfície de teste multiplica: o masstest passa a varrer combinações, não
  um caminho só. É o preço de ter configurabilidade honesta.
- A UI precisa explicar a derivação, senão o usuário mexe no intervalo e não
  entende por que o período mudou junto.

**A revisitar**
- Se o atraso do feed derrubar `15m` (ADR-001 § Decisão 2), a linha `intraday`
  desta matriz desloca para `30m` e as demais acompanham.

## Action items

1. [ ] `resolve_keep(period, interval)` — corrige a armadilha nº 3, com teste de
       que o diário não muda.
2. [ ] Objeto `TriadeTemporal`: driver (horizonte), derivação, envelope e
       validação na borda.
3. [ ] Calibragem por intervalo dos limiares de volatilidade (sai de constante).
4. [ ] Comparativo de volume intraday contra o mesmo horário de pregões
       anteriores.
5. [ ] `horizonte` passa a dirigir a tríade (hoje só entra no prompt).
6. [ ] Radar global no intervalo canônico; tríade completa só sob demanda.
7. [ ] Guardião da matriz legal (invariantes 1–5), no `masstest-agentes.py`.
8. [ ] UI: mostrar a derivação e o teto de `_MAX` quando ele cortar a janela.
