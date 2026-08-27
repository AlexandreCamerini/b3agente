# ADR-020: Centralização de dados de mercado no hub mydata

**Status:** Aceito
**Data:** 2026-08-27
**Decisores:** Produto/engenharia Boris+ (Alex)
**Base empírica:** `.planning/notes/boris-pp-centralizacao-dados-mydata.md`,
[`docs/MEDICAO-Mydata-2026-08-27.md`](../MEDICAO-Mydata-2026-08-27.md),
`server/app/mydata_client.py` (Fase 9, Planos 09-01 a 09-05).

---

## Contexto

Em 25/08/2026 o Boris implementou (ADR-019) a leitura diária do COTAHIST da
B3: baixa o ZIP oficial, valida o TXT de posições fixas de 245 colunas,
grava em `b3_daily_quotes`, SHA-256 para idempotência, job no scheduler às
20:30 BRT. Um dia depois, a auditoria do lado `cvm-financas` (26/08) apontou
que o hub `mydata.acamerini.app` já roda exatamente essa ingestão em
produção — mesma fonte oficial da B3, mesmo arquivo, proveniências
separadas: "duas capturas do mesmo arquivo oficial, com proveniências
separadas: exatamente o que a fronteira existe para impedir" (achado que
originou esta Fase 9, registrado em
`.planning/notes/boris-pp-centralizacao-dados-mydata.md`). O mesmo achado se
repete na cadeia de opções: `options_provider_yahoo.py` é um endpoint
não-oficial que falha com frequência (401/403/429), enquanto o hub já serve
IV e gregas pré-calculadas sobre o mesmo COTAHIST oficial, com solver `bs_iv`
testado (36 testes verdes).

`~/dev/cvm-financas/docs/contrato-consumidor.md` já listava o Boris
(`b3-agente`) como consumidor em produção do hub (chave `f00b4554`, emitida
26/08/2026, escopo `negociacao_b3`+`provento_b3`), com uma pendência
explícita do lado de lá: implementar `mydata_client.py` e desligar o
Yahoo/brapi/COTAHIST paralelo nas fatias que o hub já cobre. Manter as duas
ingestões paga o mesmo dado duas vezes e cria dois números possíveis para o
mesmo pregão — o problema estrutural que motivou a fase inteira.

## Decisão

Implementar `mydata_client.py` como cliente HTTP do hub e migrar duas fatias
de dado de mercado (COTAHIST diário e Opções/IV) para trás dele, mantendo os
mesmos contratos internos já existentes — nenhum call site consumidor mudou.

**D-01 — Candles diários atrás da interface `CandleProvider`.**
`MydataProvider` (Plano 09-02) implementa a mesma interface que
`BrapiProvider`/`YahooProvider` já implementam em `candle_provider.py`,
reusando o cache L2 (`candle_cache.py`) e todos os call sites atuais (setups,
indicadores, agente) sem mudar nada neles.

**D-02 — Opções atrás do mesmo contrato `providerStatus`.**
`options_provider_mydata.py` (Plano 09-03) implementa o mesmo contrato que
`options_provider_yahoo.py` já expunha (`providerStatus`/`calls`/`puts`/
`expirations`). `options_api.py` continua chamando o mesmo contrato; a
ADR-004 não é reaberta, só a implementação por trás muda. Um seletor por env
(`options_provider.py`, `B3_OPTIONS_PROVIDER`) decide qual provedor está
ativo.

**D-03 — Candles degradam em cadeia (mydata→brapi→Yahoo), priorizando
disponibilidade sobre pureza de proveniência única.** Se
`GET /v1/cotacoes/{ticker}` falhar no refresh diário, `candle_provider`
(Plano 09-02) cai para o próximo elo da cadeia — mesmo padrão de fallback já
usado entre brapi→Yahoo antes desta fase. `candle_cache.py` já grava o `src`
de proveniência por registro; o candle daquele dia vem etiquetado com quem
serviu.

**D-04 — Opções NÃO caem no Yahoo em nenhuma hipótese.** Se o endpoint de
opções do mydata falhar, o resultado vai direto para
`providerStatus="degraded"` (ADR-004 já bloqueia compra e mostra aviso nesse
estado), sem tentar Yahoo como fallback. Motivo: o Yahoo (401/403/429
frequentes) é exatamente a fonte instável que esta migração elimina;
reintroduzi-la como fallback ativo anularia o ganho. `options_provider_yahoo.py`
fica como código histórico, alcançável via `B3_OPTIONS_PROVIDER=yahoo`, não
caminho ativo por padrão.

**Decisões complementares fechadas no planejamento (sem ID próprio no
09-CONTEXT.md, mas parte da mesma decisão):**

- O refresh diário do mydata é **pass-through pelo `candle_cache` existente**,
  não um job em lote novo — nenhum hook novo entrou no `scheduler_loop` (o
  hook antigo do `b3_historical` foi removido, não substituído por outro).
- IV e gregas vêm **pré-calculadas do hub**; nenhum recálculo local
  redundante — `options_provider_mydata.py` só adapta o payload cru
  (`gold_opcoes`) ao contrato do ADR-004, campos aditivos (`greeks`,
  `theoreticalPrice`, `ivStatus`) nunca substituindo os campos antigos.
- `openInterest` **não tem fonte no COTAHIST** — o campo é sempre `None` no
  adaptador. Efeito MEDIDO (não estimado) no Plano 09-03: um contrato PETR4
  realista (volume 5.000, spread ≈5,41%) mede `liquidity_score=52,0` (corte
  de aprovação é 40) — passa, mas o teto do score cai de 100 para 60 sem
  open interest; contratos de volume mais baixo que hoje dependiam do open
  interest real podem deixar de cruzar o corte. Achado registrado para o
  checkpoint de virada, não corrigido nesta fase.
- O provedor de opções é **selecionável por env
  (`B3_OPTIONS_PROVIDER`) como alavanca de rollback manual**, nunca fallback
  automático em runtime — mesmo espírito de `B3_CANDLE_PROVIDER`.
- O fallback de candles deixou de ser um salto único e virou **cadeia**
  (`B3_CANDLE_FALLBACK` aceita lista separada por vírgula, roteada por
  `fallback_names()`/`get_fallbacks()` em `candle_provider.py`).
- A ingestão paralela do COTAHIST (`b3_historical.py`/ADR-019) foi
  **removida** do caminho de código (Plano 09-05, Task 1 — decisão do Alex
  no checkpoint humano bloqueante: `remover`). O commit que a implementou,
  `b3fdf02` (`feat(b3-historical): acervo diário oficial COTAHIST da B3
  (ADR-019)`), permanece no histórico como o "antes" da migração —
  `git show b3fdf02` recupera as 754 linhas originais. Nada desse código foi
  pushado antes da remoção, então nenhuma tabela chegou a existir no SQLite
  de produção (Railway).

## Status das ADRs anteriores

| ADR | O que era | Status após esta |
|---|---|---|
| ADR-001 — intraday Yahoo 15min | Yahoo dono do intraday | **INTOCADA.** O COTAHIST só publica após o fechamento do pregão; a fatia intraday não tem substituto no mydata — limitação estrutural da fonte, não lacuna de implementação |
| ADR-004 — fonte de opções na v2 | contrato `providerStatus` | **NÃO REABERTA.** Só a implementação por trás mudou (D-02); o bloqueio de compra em `degraded` continua valendo, agora também para falha do mydata |
| ADR-008 — brapi master de diário/spot | brapi master das duas fatias | **ESCOPO REDUZIDO** a spot ao vivo. O diário passa ao mydata; a brapi vira o primeiro elo de fallback da cadeia (D-03). O COTAHIST só é publicado após o fechamento — a brapi continua exclusiva do spot durante o pregão aberto, limitação estrutural, não de implementação |
| ADR-019 — COTAHIST diário próprio | ingestão própria do ZIP da B3 | **SUPERADA na fatia diária.** Decisão do Alex no checkpoint do Plano 09-05: `remover` o código do caminho ativo. Implementado no commit `b3fdf02` (não pushado); removido no commit desta task de execução do Plano 09-05, que cita `b3fdf02` na própria mensagem. O registro da ADR-019 permanece legível, carimbado com o status desta supersessão, corpo original intacto |

## Consequências

**Ganha-se:**
- Uma proveniência só para candle diário e cadeia de opções — fim da
  duplicação que originou a fase.
- `sha256`/nome de `arquivo` até o arquivo oficial da B3 em cada linha
  (`candle_cache.py` já registra `src`; o payload de opções carrega
  `provenance` quando presente), rastro que o Yahoo nunca teve.
- IV e gregas prontas do hub, sem recálculo local redundante.
- Uma superfície de ingestão a menos: nenhum download direto de
  `bvmf.bmfbovespa.com.br` no código do Boris; um par de endpoints admin a
  menos (`/api/admin/b3/cotahist*` removidos junto com `b3_historical.py`).

**Paga-se:**
- Dependência de um serviço externo com cota de **60 requisições/min ·
  2.000/dia** (chave de produção `f00b4554`) — ver §Medição.
- Perda dos campos crus do COTAHIST que o `gold_cotacoes` do mydata não
  expõe (`bdi_code`, `market_type`, `specification`, `reference_term`,
  `average`, `exercise_price`). Nada no Boris consumia esses campos antes
  desta migração; a capacidade sai junto do módulo removido, recuperável via
  `git show b3fdf02` se algum consumidor futuro precisar deles.
- `openInterest` ausente nas opções — efeito medido em §Decisão, acompanhar
  no checkpoint de virada.
- A cadeia de opções (D-02/D-04) **não tem, hoje, gate de orçamento** no
  código — confirmado por leitura em `options_provider.py`/
  `options_provider_mydata.py`: nenhum dos dois chama
  `mydata_budget.pode_gastar()`/`debita()` (só `candle_provider.get_history()`
  tem esse gate, Plano 09-02). Achado de arquitetura registrado na medição,
  não corrigido nesta ADR — ver §Medição, item do plano de ação.

## Medição

Números de [`docs/MEDICAO-Mydata-2026-08-27.md`](../MEDICAO-Mydata-2026-08-27.md)
(Plano 09-04), obtidos executando o código real (`mydata_client.get_history`/
`get_vencimentos`/`get_options_chain`) com `fetch_json` fake contando
chamadas — não estimativa por leitura de código. Uma ADR deste repo não
afirma suficiência de cota sem número, mesma postura de ADR-008 e de
`docs/MEDICAO-Brapi-2026-08-11.md`.

- **Custo unitário medido:** candle diário = 1 chamada por `get_history`
  (tanto `2y` quanto `1mo`, sem paginação); cadeia de opções = 2 chamadas
  por cadeia completa (1 `/vencimentos` + 1 página de `/opcoes/{ticker}`).
- **Volume/dia projetado (74 ativos do universo real):** 74 (carga
  frio/redeploy) + 74 (delta diário real, via `radar_daily.maybe_run`, 1x/dia
  útil) + 400 (opções, cenário de 200 cadeias/dia) = **548 de 2.000/dia** →
  **CABE**, com 72,6% de folga.
- **Pico chamadas/min projetado:** 74 (frio) + 74 (morno) = **148 de
  60/min** → **NÃO CABE** — 147% acima do teto do minuto. O gate global de
  espaçamento do scanner (`scanner.MIN_FETCH_GAP_S=0,15s`) foi dimensionado
  para Yahoo/brapi e permite rajadas de até ~400 chamadas/min, 6,7× mais
  folgado do que o mydata tolera.
- **`intervaloMinimoSeguro`:** 1,0s de espaçamento mínimo entre chamadas
  reais ao mydata, calculado para manter o pico de qualquer janela de 60s
  dentro da cota do minuto.
- **Perna ao vivo (autenticação real da chave `f00b4554`):** BLOQUEADA no
  Plano 09-04 por ausência de `MYDATA_TOKEN` no ambiente de execução —
  pendente de rodar `scripts/medir-mydata.py --fases vivo --vivo` localmente
  com a chave exportada, antes de qualquer virada de produção.
- **Veredito da projeção (offline):** **NÃO CABE** por causa do pico/min —
  não do volume diário. Duas ações pendentes antes da virada
  (`B3_CANDLE_PROVIDER=mydata`/`B3_OPTIONS_PROVIDER=mydata` em produção):
  tornar o espaçamento entre chamadas sensível ao provedor ativo (preservar
  0,15s para Yahoo/brapi, aplicar 1,0s só quando o elo ativo for mydata); e
  confirmar a perna ao vivo com a chave real. Nenhuma das duas depende de
  negociar aumento de cota com o lado `cvm-financas`.

## Reversibilidade

`B3_CANDLE_PROVIDER=brapi` e `B3_OPTIONS_PROVIDER=yahoo` restauram o
comportamento anterior a esta fase sem deploy de código — apenas
configuração de ambiente no Railway, mesmo padrão de rollback já
estabelecido em ADR-008/ADR-004.

Se algum dia for preciso recuperar a ingestão própria do COTAHIST removida
no Plano 09-05 (saída `remover` da Task 1), `git show b3fdf02` restaura as
754 linhas originais de `b3_historical.py` + `test_b3_historical.py` — o
commit permanece no histórico local por decisão deliberada do Alex, feita
antes desta ADR ser escrita, precisamente para preservar esse caminho de
volta. Isso é o que torna esta migração barata de desfazer: nenhum
trade-off entre "limpar o código" e "perder o trabalho" — as duas coisas
convivem, uma no caminho ativo (removida), outra no `git log` (recuperável).
