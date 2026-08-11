# qa/43 — Plano: brapi gratuita como master, Yahoo backup, orçamento de 15k req

**Data:** 2026-08-11 · **Decisão:** [ADR-008](../docs/adr/008-fonte-de-cotacoes-selecionavel.md) (brapi free master para diário+spot; Yahoo backup e dono do intraday; orçamento diário ≈ 700 req restrito ao pregão) · **Custo:** R$ 0

> **EXECUÇÃO (madrugada de 11→12/08, autorizada pelo Alex "siga sem minha
> intervenção"):** Fases 0–5 implementadas e commitadas; suíte canônica verde
> (786 pytest + 60 suítes web); prova ao vivo com token real via `railway run`
> (cliente brapi servindo; roteamento honrando janela de pregão; paridade de
> close brapi×Yahoo ao vivo). Decisão adicional do Alex (11/08) incorporada na
> Fase 4: **o L2 é o acervo próprio de histórico** — o delta diário da brapi
> (≤3mo) estende a série local dia a dia, contornando a limitação de 3 meses
> do plano. Pendências no fim do arquivo.

Porta de saída de TODA fase: `bash scripts/executar.sh --testes` verde (as duas
suítes — pytest e `web/tests/*.mjs`). Front editado → `npx vite build`.
Publicação → `scripts/bump.sh` antes de `publicar-web.sh`. Nada entra na branch
de submissão da App Store sem ok do Alex.

---

## Fase 0 — Spike com token gratuito — EXECUTADA em 11/08 ✅ (ressalva: delay)

Resultado completo em [`docs/MEDICAO-Brapi-2026-08-11.md`](../docs/MEDICAO-Brapi-2026-08-11.md)
(via `railway run`, 8 requisições). Resumo do que muda nas fases seguintes:

1. Cota **15.000 confirmada** por header (`x-ratelimit-limit`); reset não
   exposto — presumido mensal, confirmar no painel da conta.
2. **1 ticker/req** (`QUOTES_PER_REQUEST_EXCEEDED`) — orçamento do ADR mantido.
3. **Só `1d`** (`INVALID_INTERVAL` fora do sandbox) — roteamento por intervalo
   confirmado.
4. **Range máximo `3mo`** (`INVALID_RANGE` para 2y; permitidos 1d/5d/1mo/3mo)
   — **novo**: warmup e histórico ≥6mo ficam definitivamente no Yahoo; a brapi
   serve spot + delta de até 3mo. A Fase 3 ganha guarda de range além da de
   intervalo.
5. **Recusa por plano DEBITA cota** — **novo**: validação client-side de
   intervalo/range/lote ANTES de chamar; erro de plano vira guarda de teste.
6. `close`≠`adjustedClose` em 25/62 velas (ITSA4 3mo) — regra de substituição
   confirmada com dado real.
7. `x-ratelimit-remaining` vem em toda resposta — o contador local do
   orçamento (Fase 2) **reconcilia** com o header e expõe ambos no
   `/api/status`.

**Pendência aberta (não bloqueia Fases 1–4):** delay real do spot em pregão
(amostragem de 1h, 10h–17h BRT) — decide o TTL da fatia de spot na Fase 5.

## Fase 1 — Cliente brapi + `BrapiProvider.history()` real

**Arquivos:** `server/app/brapi.py` (novo — httpx, timeout, retry curto, token
via header `Authorization: Bearer`; sem sessão/crumb), `server/app/candle_provider.py`
(stub delega ao cliente; mensagem de falha-alto fica para o caso sem token).

Mapeamento (evidência do spike no ADR-008): ticker **sem** `.SA` (não usar
`yahoo_symbol`); `historicalDataPrice[].date` epoch s → chave no fuso da bolsa
via `America/Sao_Paulo` (diário corta a hora; intraday `"AAAA-MM-DD HH:MM"` —
implementado mesmo que o free não sirva intraday, para o dia de um upgrade);
`close` de `close` (não `adjustedClose`); exceção em HTTP ≠ 200 / `error:true`
/ série vazia; guardião de granularidade (`usedInterval` ≠ pedido → recusa,
mesma regra do Yahoo em `yahoo.py:224-231`).

**Testes** (`server/tests/test_brapi.py` novo + ajuste em
`test_candle_provider.py:75`, cuja asserção trava a mensagem do stub —
guardião atualizado com nota): parse de fixture real do spike; epoch→BRT
diário e 15m; recusa de granularidade; sem token → falha-alto preservada.
**Comando:** `server/.venv/bin/python -m pytest tests/test_brapi.py tests/test_candle_provider.py -q`

## Fase 2 — Orçamento de requisições (o subsistema novo)

**Arquivos:** `server/app/brapi_budget.py` (novo), `server/app/candle_provider.py`
(consulta o orçamento antes de chamar a brapi), `server/app/main.py:410`
(consumo por fatia no `/api/status`).

- Contador **persistido em SQLite** por dia-calendário (sobrevive a deploy;
  reusar `db.py`, sem tabela ad-hoc fora do padrão do projeto).
- Teto diário = `B3_BRAPI_COTA_MES` (default 15000) ÷ 21, calculado — não
  hardcoded. Fatias do ADR: spot 400 / delta 150 / fundamentos 30 / reserva.
- **Janela de pregão**: dia útil B3, 10:00–17:15 BRT + a passada única de
  delta pós-fechamento. Reusar a noção de pregão existente (`intraday.py`,
  `candles.py:64` — `ABERTURA_MIN`); feriados: mesma fonte que o app já usa
  (se não houver, dia útil seg–sex é a v1 e feriado vira consumo zero de fato,
  porque a B3 sem pregão não gera demanda de spot).
- Soft stop 80% da fatia (TTL do spot degrada 5→15 min), hard stop 100% do
  teto (brapi silencia até o próximo pregão).
- `fundamentals.py` passa a consumir da fatia própria quando usar
  `BRAPI_TOKEN` (hoje chama sem token; com token a cota conta).

**Testes:** consumo debita a fatia certa; soft stop degrada TTL; hard stop
silencia brapi e o failover serve Yahoo; contador sobrevive a "restart"
(reabrir conn); fora da janela de pregão a brapi não é chamada; teto
recalculado quando `B3_BRAPI_COTA_MES` muda.
**Comando:** `server/.venv/bin/python -m pytest tests/test_brapi_budget.py tests/test_candle_provider.py -q`

## Fase 3 — Inversão do primário + failover por requisição e por orçamento

**Arquivos:** `server/app/candle_provider.py`.

- `B3_CANDLE_PROVIDER=brapi` (novo default de produção via env no Railway; o
  default **de código** continua `yahoo`, para ambiente sem token funcionar
  como hoje), `B3_CANDLE_FALLBACK=yahoo`.
- **Roteamento por intervalo**: pedido intraday vai direto ao Yahoo sem
  debitar orçamento (restrição de plano, não falha). Diário/semanal → brapi
  com orçamento → Yahoo em exceção/vazio/estouro.
- Payload ganha `"source"`; `_registra` ganha dimensão do provedor;
  `snapshot()` reporta por provedor; o `alerta` de 2%/3 dias passa a vigiar a
  brapi (primário novo) — nota no teste-guardião.

**Testes:** intraday nunca toca brapi nem debita; diário com brapi ok → `source:"brapi"`;
brapi falha → Yahoo serve com `source:"yahoo"` e falha registrada na brapi;
orçamento estourado → Yahoo sem tentar brapi; sem token → 100% Yahoo
(comportamento de hoje, teste de regressão).
**Comando:** `server/.venv/bin/python -m pytest tests/test_candle_provider.py tests/test_brapi_budget.py -q`

## Fase 4 — Cache e snapshot conhecem a fonte

**Arquivos:** `server/app/candle_cache.py`, `server/app/technical_snapshot.py`.

Entrada do cache ganha `src`; merge só entre mesma fonte; fonte diferente =
substituição completa + re-warmup `FULL_RANGE` (que pode ir ao Yahoo se o free
limitar range — decisão da Fase 0); entrada legada sem `src` = tratada como do
primário corrente; `snapshotId` inclui `src` no fingerprint (mesma classe de
bug da descoberta 2 do ADR-001).

**Testes:** merge entre fontes substitui; legado não invalida à toa;
`snapshotId` muda com a fonte; L2 persiste o `src`.
**Comando:** `server/.venv/bin/python -m pytest tests/test_candle_cache.py tests/test_technical_snapshot.py -q`

## Fase 5 — Spot atrás da fronteira

**Arquivos:** `server/app/candle_provider.py` (contrato `quote`/`quotes`;
implementação brapi 1 ticker/req dentro da fatia de orçamento, com cache
compartilhado; Yahoo delega a `yahoo.get_quote(s)`), `server/app/main.py`
(rotas `529, 568, 583-592, 908` trocam `yahoo.` pelo ponto único),
`server/app/options_api.py` (spot de ação; cadeia de opções não muda — ADR-004).

`QuoteUnavailable` re-exposto pela fronteira (os `except` existentes não
mudam). Paridade do payload de `/api/quotes` com o formato atual
(`t, name, price, change, previousClose, currency`).

**Testes:** paridade de payload; failover do spot; débito na fatia; TTL
degradado sob soft stop; mapeamento do spot brapi por fixture real.
**Comando:** suíte completa — `bash scripts/executar.sh --testes`

## Fase 6 — Fonte declarada + verificação ao vivo

Didática declara origem e atraso do dado onde cita frescor (backend-only,
mesmo caminho do Estudo; intraday declarado como Yahoo). Se texto do front
mudar: paridade `defaults.py` ↔ `catalog.js` byte a byte e
`deviceStore` ↔ `serverStore` — pela decisão 2 do ADR, **não** entra campo de
usuário.

**Verificação ao vivo (o que unit test não pega):** subir `api` local (porta
8787), com `BRAPI_TOKEN` de teste: card diário servindo `source:"brapi"`;
matar o token (env inválida) e ver o Yahoo assumir; forçar hard stop
(`B3_BRAPI_COTA_MES` baixa) e ver o dia terminar no Yahoo; `/api/status` com
consumo por fatia; rodapé do Perfil com carimbo novo após `bump.sh`.

**Aceite final:** suíte canônica verde; roteamento intraday→Yahoo comprovado;
orçamento visível e com stop testado ao vivo; rollback comprovado
(`B3_CANDLE_PROVIDER=yahoo` + fallback vazio = comportamento de hoje);
`docs/MEDICAO-Brapi` citada no ADR com status atualizado.

---

## Fora de escopo

Plano Pro/intraday pago (upgrade futuro; o consumo por fatia no `/api/status`
é o dado que justificaria); UI de escolha de fonte; cross-check de preço;
circuito persistente; opções pela brapi; troca de bundle id / renames
`b3-agente`/`B3_*`/`b3-*`; token commitado; editar `web_dist` sem `bump.sh`;
baseline declarada só com `scripts/test.sh`.

## Pendências pós-execução (12/08)

1. **Virar a chave em produção** (decisão do Alex): definir no Railway
   `B3_CANDLE_PROVIDER=brapi` (o default de código segue `yahoo`;
   `B3_CANDLE_FALLBACK` default já é `yahoo` quando o primário não é yahoo).
   Sem essa env, o deploy do PR não muda comportamento nenhum.
2. **Delay do spot em pregão** (ressalva da Fase 0): amostragem de 1h entre
   10h–17h BRT; decide se o TTL base do spot (5 min) fica ou alonga.
3. **Fase 6 restante**: didática declarando fonte/atraso nos textos (o dado
   `source` já sai em candles, cache e spot; falta o texto citá-lo) e a
   verificação ao vivo com servidor local completo.
4. **Reset da cota**: o header sugeriu reset DIÁRIO (remaining voltou a ~15k
   na madrugada seguinte ao spike) — confirmar no painel da conta; se for
   diário, o teto local pode subir de ~700 para o limite diário real
   (`B3_BRAPI_COTA_MES` ajusta sem deploy).
5. ~~Persistência do orçamento em produção~~ — FECHADA na própria execução:
   `main.py` liga `brapi_budget.configure_db(_conn)` junto do L2 no boot.

## Riscos abertos

1. **Premissa dos 15k** — se o free real for menor, o orçamento recalcula por
   env (`B3_BRAPI_COTA_MES`) sem mudar código; se for por dia e não por mês, a
   Fase 2 simplifica.
2. **Free sem `2y`** — warmup fica no Yahoo; a dependência do Yahoo não some
   nunca (intraday + warmup + backup); é redução de exposição, não remoção.
3. **Delay do free desconhecido** — se for pior que os ~15 min do Yahoo, o
   spot master fica mais atrasado que hoje; a didática declara o número real
   medido na Fase 0, e a decisão de manter a inversão é do Alex com esse dado.
4. **Fundamentos passam a debitar cota** quando o token entrar — a fatia de 30
   req/dia cobre o TTL de 7 dias do universo, mas o warm anual
   (`fundamentals.py` `warm`) precisa respeitar o orçamento.
