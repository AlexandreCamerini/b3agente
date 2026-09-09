---
quick_id: 260909-oyu
phase: quick-260909-oyu
plan: 01
status: complete
subsystem: backend
tags: [datetime, timezone, store, obslog, guardiao]

requires: []
provides:
  - "store.now_str() em BRT — fonte única do carimbo de histórico/posições"
  - "main.now_str() delegando a store.now_str() (sem cópia da regra de fuso)"
  - "obslog.log() carimbando ts em BRT"
  - "teste guardião cruzando a meia-noite UTC (prova hora e dia)"
affects: [store, main, obslog, historico-de-ordens, admin-log]

tech-stack:
  added: []
  patterns:
    - "BRT = timezone(timedelta(hours=-3)) local ao módulo, replicando o padrão já usado em agent.py/ai_activity/brapi_budget/pregao — sem módulo compartilhado de fuso"

key-files:
  created:
    - server/tests/test_store_now_str_brt.py
  modified:
    - server/app/store.py
    - server/app/main.py
    - server/app/obslog.py

key-decisions:
  - "Offset fixo -3h (sem DST): Brasil não tem horário de verão desde 2019, mesma justificativa de brapi.py:31-33"
  - "obslog não importa store (log é a camada mais baixa, não pode depender de nada que possa derrubá-la) — BRT definido localmente também em obslog.py, duplicando a constante mas não a lógica de negócio"
  - "Registros já gravados no histórico NÃO são reconvertidos — ver seção dedicada abaixo"

requirements-completed: [D-01, D-02, D-03, D-04, D-05]

duration: ~35min
completed: 2026-09-09
---

# Quick 260909-oyu: Carimbo de horário das ordens em BRT

**`store.now_str()` agora carimba em horário de Brasília (offset fixo -3h) em vez do fuso do container Railway (UTC), com `main.now_str()` delegando à mesma fonte e `obslog` seguindo o mesmo padrão localmente; um teste guardião cruza a meia-noite UTC para provar que tanto a hora quanto o DIA do carimbo estão corretos.**

## Performance

- **Duration:** ~35 min
- **Completed:** 2026-09-09
- **Tasks:** 2/2 completos
- **Files modified:** 3 (+ 1 criado)

## Accomplishments

- Histórico de compra/venda (e `abertaEm` das posições) deixa de sair 3h adiantado e, na janela 21:00–23:59 BRT, deixa de "pular" para o dia seguinte.
- `at` das cotações e `time` dos eventos de log do agente (via `main.now_str()`) agora delegam para a mesma fonte única, eliminando a cópia duplicada da regra de fuso.
- `ts` do ring buffer de observabilidade (`GET /api/obs/logs`, aba Observabilidade do portal admin) também em BRT.
- Guardião automatizado prova o defeito real: falha mostrando `23:30` (UTC cru) se alguém reverter para `datetime.now()` naive, em vez de só verificar um número de hora isolado.

## Task Commits

Each task was committed atomically:

1. **Task 1: BRT nos três pontos de carimbo, com main.py delegando a store** - `88ba707` (fix)
2. **Task 2: Guardião — carimbo em BRT prova hora E dia (cruzando a meia-noite UTC)** - `b129c4f` (test)

**Plan metadata:** commit separado feito pelo orquestrador (não incluído por esta execução, conforme instrução).

## Files Created/Modified

- `server/app/store.py` — `BRT = timezone(timedelta(hours=-3))` definido junto de `SECTIONS`; `now_str()` usa `datetime.now(BRT)`; comentário de decisão explicando o defeito original e por que o offset é fixo.
- `server/app/main.py` — `now_str()` reduzido a `return store.now_str()`; import de `datetime` preservado (ainda usado nas linhas 866/869/1142, fora do escopo desta task).
- `server/app/obslog.py` — `BRT` local ao módulo (não importa `store`, por desenho: log é a camada mais baixa); `ts` usa `datetime.now(BRT)`.
- `server/tests/test_store_now_str_brt.py` (novo) — 4 casos: `store.now_str()`, delegação de `main.now_str()`, `obslog.log()`/`ts`, e um assert de que os dois formatos de string (`%d/%m/%Y %H:%M` e `%d/%m %H:%M:%S`) não mudaram.

## Deviations from Plan

None — plano executado exatamente como escrito. Único ajuste local: a categoria de log usada no caso 4 do teste (`"teste_brt_formato"`, 18 caracteres) foi truncada pelo próprio `obslog.log()` (`cat[:16]`) e não batia com o filtro do assert; renomeada para `"teste_fmt"` (13 caracteres) — ajuste de nome de string de teste, sem tocar em código de produção nem em comportamento coberto pelo plano.

## Verification Performed

- `cd server && python -c "from app import store, obslog; print(store.BRT, obslog.BRT); print(store.now_str())"` → `UTC-03:00 UTC-03:00` / horário correto.
- `grep -n "datetime.now()" app/store.py app/main.py app/obslog.py` → nenhum `datetime.now()` naive restante no código (só aparece dentro de um comentário de decisão).
- Suíte pytest completa (venv do clone principal, `/Users/acamerini/dev/borisv2/server/.venv/bin/python -m pytest -q`, executando o código do worktree — confirmado via `app.store.__file__`): **2114 passed, 1 skipped** (2110 antes do novo arquivo de teste + 4 casos novos).
  - Nota de ambiente: a primeira tentativa rodou dentro do sandbox padrão da ferramenta Bash e falhou 27 testes com `PermissionError: [Errno 1] Operation not permitted` ao carregar certificados SSL (`ssl.py:717`, chamado por `httpx`/testes de rede real) — não relacionado a esta mudança. Repetindo com `dangerouslyDisableSandbox: true` os mesmos 27 testes passaram, confirmando que era restrição do sandbox e não regressão introduzida.
- Guardião isolado: `pytest tests/test_store_now_str_brt.py -q` → **4 passed**.
- Prova de que o guardião pega a regressão: os três arquivos foram temporariamente substituídos pelo conteúdo pré-fix (via `git show <commit-base>:<arquivo>`, sem usar `git stash`), o guardião foi rodado de novo (**3 de 4 casos falharam** — exatamente os que testam hora/dia; o caso de formato passa porque o formato da string não muda mesmo sem o fix, como esperado) e os arquivos foram restaurados com `git checkout HEAD -- <arquivos>`. Suíte voltou a passar 100% depois da restauração.
- Suíte canônica completa: `bash scripts/executar.sh --testes` → pytest **2114 passed, 1 skipped**; `web/tests/*.mjs` **124 [OK], 0 [X]**; exit code 0.
- `web/src/persistence.js` **não foi tocado** (confirmado — fora dos arquivos modificados no diff).
- Nenhum deploy, bump de `SERVER_BUILD_ID` ou comando `railway` foi executado.

## Registros já gravados não são reconvertidos

`history[].date` é uma string sem fuso embutido — não há como distinguir, a
posteriori, quais entradas foram gravadas pelo container UTC do Railway
(3h adiantadas / possivelmente no dia errado) e quais vieram de execução
local já em BRT. Subtrair -3h de tudo corromperia os registros que já
estavam corretos. A correção desta quick vale a partir do deploy em diante;
o histórico anterior ao deploy permanece como foi gravado, sem reprocessamento.

## Pendência fora de escopo: candle_provider.py:61 e scan_deep.py:29

Dois pontos usam o dia LOCAL do container como chave de "hoje" e têm o MESMO
defeito de classe (no Railway, em UTC, o "dia" vira às 21:00 BRT):

- `server/app/candle_provider.py:61` — usa `time.localtime()`.
- `server/app/scan_deep.py:29` — usa `time.strftime` com hora local.

Não foram corrigidos nesta quick (fora do `files_modified` do plano). Ficam
registrados aqui como candidato a uma próxima quick/fase dedicada, seguindo
o mesmo padrão de BRT explícito local ao módulo.

## Known Stubs

Nenhum.

## Threat Flags

Nenhum — a mudança não introduz superfície nova (mesmos três pontos de
carimbo já existentes, só troca a fonte do relógio). Ver `<threat_model>`
do plano para o registro STRIDE completo (T-oyu-01/02/03).

## Self-Check: PASSED

- `server/app/store.py` — FOUND (contém `BRT = timezone(timedelta(hours=-3))` e `datetime.now(BRT)`)
- `server/app/main.py` — FOUND (contém `return store.now_str()`)
- `server/app/obslog.py` — FOUND (contém `datetime.now(BRT)`)
- `server/tests/test_store_now_str_brt.py` — FOUND (66 linhas, 4 testes)
- Commit `88ba707` — FOUND em `git log --oneline`
- Commit `b129c4f` — FOUND em `git log --oneline`
