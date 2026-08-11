# qa/43 — Plano: brapi gratuita como master, Yahoo backup, orçamento de 15k req

**Data:** 2026-08-11 · **Decisão:** [ADR-008](../docs/adr/008-fonte-de-cotacoes-selecionavel.md) (brapi free master para diário+spot; Yahoo backup e dono do intraday; orçamento diário ≈ 700 req restrito ao pregão) · **Custo:** R$ 0

Porta de saída de TODA fase: `bash scripts/executar.sh --testes` verde (as duas
suítes — pytest e `web/tests/*.mjs`). Front editado → `npx vite build`.
Publicação → `scripts/bump.sh` antes de `publicar-web.sh`. Nada entra na branch
de submissão da App Store sem ok do Alex.

---

## Fase 0 — Spike com token gratuito (custo R$ 0) — GATE

Criar a conta gratuita, definir `BRAPI_TOKEN` **só no ambiente local**, rodar
script descartável (scratchpad) e escrever `docs/MEDICAO-Brapi-<data>.md` no
formato da medição do Yahoo. Confirma as premissas do ADR:

1. **Cota real do gratuito** — é 15.000/mês? Reset mensal ou diário? O que a
   API devolve ao estourar (código/mensagem — o orçamento local precisa
   reconhecer)?
2. **Tickers por requisição** com token free (hipótese: 1; se for mais, o
   orçamento do ADR é refeito para melhor).
3. **Intervalos permitidos** com token free em ticker fora do sandbox
   (WEGE3/BBAS3): `1d` ok? `15m` recusa com qual erro? (hipótese: só `1d`).
4. **Range máximo** no free: `2y` diário funciona? (decide onde mora o warmup
   de médias longas — brapi ou Yahoo).
5. **Atraso real do spot** durante pregão: `regularMarketTime` vs relógio,
   amostrado por 1h.
6. **`adjustedClose` vs `close`** num ticker com provento recente (valida a
   regra "fonte diferente = substituição, nunca merge").

**Aceite:** cada item com número/erro literal, ou "não confirmado + por quê".
Se a cota real for muito menor que 15k ou o `1d` não vier confiável, parar e
voltar ao ADR — custo do aprendizado: zero.

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
