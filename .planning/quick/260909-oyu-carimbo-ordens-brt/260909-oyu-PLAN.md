---
quick_id: 260909-oyu
phase: quick-260909-oyu
plan: 01
type: execute
wave: 1
depends_on: []
date: 2026-09-09
status: planned
autonomous: true
requirements: [D-01, D-02, D-03, D-04, D-05]
files_modified:
  - server/app/store.py
  - server/app/main.py
  - server/app/obslog.py
  - server/tests/test_store_now_str_brt.py

must_haves:
  truths:
    - "Uma compra feita às 20:30 BRT aparece no histórico com data 09/09/2026 e hora 20:30, não 09/09/2026 23:30."
    - "Uma operação feita depois das 21:00 BRT fica registrada no DIA correto (o carimbo não pula para o dia seguinte)."
    - "O 'última atualização' das cotações (`at`) mostra a hora de Brasília."
    - "O log do portal admin (`ts`) mostra a hora de Brasília."
    - "O formato da string de carimbo não muda (`%d/%m/%Y %H:%M` no histórico, `%d/%m %H:%M:%S` no log) — o front exibe a string como está."
  artifacts:
    - path: "server/app/store.py"
      provides: "now_str() em BRT — fonte única do carimbo de histórico"
      contains: "BRT = timezone(timedelta(hours=-3))"
    - path: "server/app/main.py"
      provides: "now_str() delegando para store.now_str()"
      contains: "return store.now_str()"
    - path: "server/app/obslog.py"
      provides: "ts do ring buffer em BRT"
      contains: "datetime.now(BRT)"
    - path: "server/tests/test_store_now_str_brt.py"
      provides: "Guardião: prova hora E dia, cruzando a meia-noite UTC"
      min_lines: 40
  key_links:
    - from: "server/app/main.py:now_str"
      to: "server/app/store.py:now_str"
      via: "delegação direta (fonte única)"
      pattern: "return store\\.now_str\\(\\)"
    - from: "server/tests/test_store_now_str_brt.py"
      to: "store.now_str / main.now_str / obslog.log"
      via: "monkeypatch do módulo datetime com instante UTC fixo"
      pattern: "monkeypatch\\.setattr"
---

<objective>
Corrigir o carimbo de horário das ordens (e das cotações e do log admin) para
o fuso de Brasília. Produção roda no Railway com o container em UTC, e as três
funções de carimbo usam `datetime.now()` naive — o histórico de compra/venda
sai 3 horas adiantado e, entre 21:00 e 23:59 BRT, sai com o DIA errado também.

Purpose: o histórico de operações é a memória da simulação (princípio 5 do
CLAUDE.md — número de carteira é determinístico). Um carimbo 3h à frente
desalinha a operação do pregão a que ela pertence e quebra a leitura
educacional do próprio histórico.

Output: `store.now_str()` como fonte única em BRT, `main.now_str()` delegando
a ela, `obslog` carimbando em BRT, e um teste guardião que prova hora e dia.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/STATE.md

Arquivos tocados: `server/app/store.py`, `server/app/main.py`,
`server/app/obslog.py`, `server/tests/test_store_now_str_brt.py`.
</context>

<diagnostico_fechado>
Investigação já concluída pelo orquestrador. NÃO re-investigar; implementar.

| Local | Código hoje | O que carimba |
|---|---|---|
| `server/app/store.py:179-180` | `datetime.now().strftime("%d/%m/%Y %H:%M")` | `date` de TODA entrada de `history` (ação e opção — 17 chamadas) e `abertaEm` das posições |
| `server/app/main.py:549-550` | idem (cópia literal) | `at` das cotações e `time` dos eventos de agent log (≈15 chamadas) |
| `server/app/obslog.py:43` | `datetime.now().strftime("%d/%m %H:%M:%S")` | `ts` do ring buffer lido em `GET /api/obs/logs` |

Padrão do repo para fuso: **BRT definido localmente em cada módulo**, offset
fixo -3h. Já existe em `agent.py:34` (`BRT = timezone(timedelta(hours=-3))`,
usado por `_today()` e `_now_str()`), e o mesmo em `ai_activity`, `analytics`,
`automacao`, `brapi_budget`, `analysis_outcomes`, `pregao`. **Não criar módulo
compartilhado de fuso** — seguir o padrão existente.

Justificativa canônica do offset fixo está em `server/app/brapi.py:31-33`: o
Brasil não tem horário de verão desde 2019.

`web/src/persistence.js:475` (`deviceStore`) usa `new Date()` do aparelho —
já correto, **não tocar**. O front NÃO parseia `history[].date`: é string
opaca exibida como está, então o formato não pode mudar.
</diagnostico_fechado>

<tasks>

<task type="auto">
  <name>Task 1: BRT nos três pontos de carimbo, com main.py delegando a store</name>
  <files>server/app/store.py, server/app/main.py, server/app/obslog.py</files>
  <action>
(a) `server/app/store.py` (D-01, D-02):
- linha 5: trocar `from datetime import datetime` por
  `from datetime import datetime, timedelta, timezone`.
- logo abaixo de `SECTIONS` (linha 10), definir `BRT = timezone(timedelta(hours=-3))`
  no mesmo padrão de `agent.py:34`.
- `now_str()` (linha 179) passa a `return datetime.now(BRT).strftime("%d/%m/%Y %H:%M")`.
- Comentário curto de DECISÃO acima do `BRT` (o repo usa comentário para
  carregar histórico de decisão, não para reafirmar o código): produção roda no
  Railway com o container em UTC, então `datetime.now()` naive carimbava o
  histórico 3h à frente e, das 21:00 às 23:59 BRT, no dia seguinte; offset fixo
  -3h porque o Brasil não tem horário de verão desde 2019 (mesma justificativa
  de `brapi.py:31-33`); BRT local ao módulo é o padrão do repo (`agent.py`,
  `ai_activity`, `brapi_budget`, `pregao`), não há módulo compartilhado de fuso.
- O FORMATO não muda: `%d/%m/%Y %H:%M`. O front exibe `history[].date` como
  string opaca; mudar o formato quebraria a leitura sem nenhum ganho.

(b) `server/app/main.py` (D-03):
- `now_str()` (linhas 549-550) passa a `return store.now_str()` — fonte única,
  em vez de uma segunda cópia da regra de fuso que pode divergir. `store` já
  está importado (linha 18); NÃO adicionar import novo.
- Comentário de uma linha dizendo que a regra de fuso mora em `store.now_str()`.
- NÃO remover `from datetime import datetime` (linha 10): ainda é usado nas
  linhas 865-868 e 1141.

(c) `server/app/obslog.py` (D-04):
- linha 15: `from datetime import datetime, timedelta, timezone`.
- definir `BRT = timezone(timedelta(hours=-3))` junto das constantes de módulo
  (perto de `_MAX`, linha 20), com comentário curto remetendo à mesma decisão.
- linha 43: `"ts": datetime.now(BRT).strftime("%d/%m %H:%M:%S")`. Formato
  inalterado. `obslog` não pode importar `store` (store importa `db`, e o log é
  a camada mais baixa — nunca deve poder derrubar quem observa), por isso aqui
  o BRT é local mesmo, e não delegação.

FORA DE ESCOPO nesta task (só listar como pendência no SUMMARY, não corrigir):
`server/app/candle_provider.py:61` (`time.localtime()`) e
`server/app/scan_deep.py:29` (`time.strftime` local) usam o dia LOCAL do
container como chave de "hoje" — no Railway, esse dia vira às 21:00 BRT.
  </action>
  <verify>
    <automated>cd server &amp;&amp; .venv/bin/python -c "from app import store, obslog; print(store.BRT, obslog.BRT); print(store.now_str())"</automated>
    <automated>cd server &amp;&amp; grep -n "datetime.now()" app/store.py app/main.py app/obslog.py || echo "OK: nenhum datetime.now() naive sobrou nos tres modulos"</automated>
    <automated>cd server &amp;&amp; .venv/bin/python -m pytest -q</automated>
  </verify>
  <done>
`store.now_str()` e `obslog` carimbam em BRT; `main.now_str()` é uma linha que
delega a `store.now_str()`; os dois formatos de string estão idênticos aos de
antes; a suíte pytest inteira passa.
  </done>
</task>

<task type="auto">
  <name>Task 2: Guardião — carimbo em BRT prova hora E dia (cruzando a meia-noite UTC)</name>
  <files>server/tests/test_store_now_str_brt.py</files>
  <action>
Criar `server/tests/test_store_now_str_brt.py` (D-05). Docstring no padrão do
repo: explica QUE DEFEITO o teste guarda (carimbo naive em container UTC =
histórico 3h à frente e, na janela 21:00–23:59 BRT, no dia seguinte), não o
que o código faz.

Instante de referência: `datetime(2026, 9, 9, 23, 30, tzinfo=timezone.utc)`,
escolhido de propósito dentro da janela em que UTC e BRT estão em DIAS
diferentes — assim o assert prova a data, não só a hora. Esperado em BRT:
`09/09/2026 20:30`.

Fake do relógio (uma classe no arquivo de teste, reusada pelos casos):

    class _RelogioFixo(datetime):
        @classmethod
        def now(cls, tz=None):
            instante = datetime(2026, 9, 9, 23, 30, tzinfo=timezone.utc)
            return instante.astimezone(tz) if tz is not None else instante.replace(tzinfo=None)

Herdar de `datetime` (e não um objeto solto) para que `strftime` funcione sem
reimplementação. O ramo `tz is None` devolve o instante NAIVE em UTC — é
exatamente o que o container do Railway devolveria hoje, então se alguém
reverter para `datetime.now()` o teste falha com `09/09/2026 23:30`,
mostrando o defeito real.

Casos:
1. `monkeypatch.setattr(store, "datetime", _RelogioFixo)` →
   `assert store.now_str() == "09/09/2026 20:30"`.
2. Mesmo patch em `store` (o de main delega) + `from app import main` →
   `assert main.now_str() == "09/09/2026 20:30"`. Este caso é o guardião da
   DELEGAÇÃO: se alguém reintroduzir uma cópia do `strftime` em `main.py`, o
   patch em `store` deixa de alcançá-la e o teste quebra. Importar `app.main`
   direto funciona (vários testes já fazem: `test_admin_portal.py`,
   `test_gate_liquidez_rotas.py`); se o import exigir env/DB, seguir o padrão
   de fixture desses arquivos em vez de inventar setup novo.
3. `monkeypatch.setattr(obslog, "datetime", _RelogioFixo)`, chamar
   `obslog.log("teste_brt", "carimbo")` e ler `obslog.recent(5, cat="teste_brt")[0]["ts"]`
   → `assert ts.startswith("09/09 20:30")`. O único efeito colateral é uma
   entrada no ring buffer em memória (cap 1000, `deque`), que não persiste nada
   e não afeta outros testes — por isso dá para exercitar a função pública em
   vez de testar um helper privado.
4. Um assert curto de que os FORMATOS não mudaram: `store.now_str()` casa
   `^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$` e o `ts` casa `^\d{2}/\d{2} \d{2}:\d{2}:\d{2}$`
   — o front exibe essas strings como estão.

Usar `monkeypatch` (fixture do pytest), nunca patch global sem desfazer.
  </action>
  <verify>
    <automated>cd server &amp;&amp; .venv/bin/python -m pytest tests/test_store_now_str_brt.py -q</automated>
    <automated>cd server &amp;&amp; git stash &amp;&amp; .venv/bin/python -m pytest tests/test_store_now_str_brt.py -q; echo "esperado: FALHA acima (guardiao pega a regressao)"; git stash pop</automated>
    <automated>bash scripts/executar.sh --testes</automated>
  </verify>
  <done>
O teste passa com o código da Task 1 e FALHA se a Task 1 for revertida (o
segundo comando de verify prova isso). `bash scripts/executar.sh --testes`
(pytest + `web/tests/*.mjs`) passa inteiro.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| container Railway → carimbo exibido | O fuso do host (UTC) atravessava direto para o dado mostrado ao usuário; após a correção, o offset é explícito no código e independe do ambiente |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-oyu-01 | Repudiation | `store.now_str()` (carimbo do histórico) | mitigate | Offset explícito no código + guardião que prova hora e dia; carimbo deixa de depender do fuso do host |
| T-oyu-02 | Information Disclosure | `obslog.ts` | accept | Só muda o fuso do carimbo; nenhum campo novo, nenhuma identidade de usuário adicionada ao buffer |
| T-oyu-03 | Tampering | registros já gravados no SQLite | accept | Não são reconvertidos — ver `<dados_historicos>`; reescrever seria adivinhar |
| T-oyu-SC | Tampering | npm/pip/cargo installs | N/A | Nenhuma dependência instalada nesta quick (stdlib `datetime` apenas) |
</threat_model>

<dados_historicos>
**Registros já gravados NÃO são reconvertidos.** `history[].date` é string sem
fuso; não há como saber quais foram gravadas pelo container UTC do Railway e
quais vieram de execução local em BRT. Somar -3h em cima disso corromperia as
corretas. A correção vale da data do deploy em diante.

O executor DEVE escrever isso no SUMMARY, junto com a pendência fora de escopo
(`candle_provider.py:61` e `scan_deep.py:29` — dia local como chave de "hoje").
</dados_historicos>

<verification>
Validação obrigatória do CLAUDE.md: `bash scripts/executar.sh --testes` (roda
as DUAS suítes — pytest do backend + `web/tests/*.mjs`). `scripts/test.sh`
sozinho não conta.

Front NÃO é editado nesta quick → **sem** `npx vite build`.

**NÃO fazer deploy. NÃO bumpar `SERVER_BUILD_ID`. NÃO rodar nada contra o
Railway** — decisão do Alex; a publicação é passo separado, fora desta quick.
</verification>

<commits>
Commits atômicos, um por task, mensagem em PT-BR no padrão do repo:

- Task 1: `fix(store): carimbo de horario em BRT, nao no fuso do container (260909-oyu)`
- Task 2: `test(store): guardiao do carimbo BRT cruzando a meia-noite UTC (260909-oyu)`
</commits>

<success_criteria>
- [ ] `store.now_str()` retorna hora de Brasília; formato `%d/%m/%Y %H:%M` intacto
- [ ] `main.now_str()` é `return store.now_str()` (fonte única, sem cópia da regra)
- [ ] `obslog` carimba `ts` em BRT; formato `%d/%m %H:%M:%S` intacto
- [ ] Nenhum `datetime.now()` naive restou em `store.py`, `main.py`, `obslog.py`
- [ ] `web/src/persistence.js` NÃO foi tocado
- [ ] Guardião passa com o fix e falha sem ele
- [ ] `bash scripts/executar.sh --testes` passa inteiro
- [ ] SUMMARY registra: dados históricos não reconvertidos + pendência `candle_provider.py:61` / `scan_deep.py:29` + nenhum deploy feito
</success_criteria>

<output>
Criar `.planning/quick/260909-oyu-carimbo-ordens-brt/260909-oyu-SUMMARY.md` ao final.
</output>
