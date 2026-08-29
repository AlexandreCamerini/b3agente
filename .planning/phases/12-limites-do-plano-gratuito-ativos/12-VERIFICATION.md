---
phase: 12-limites-do-plano-gratuito-ativos
verified: 2026-08-29T00:00:00Z
status: human_needed
score: 10/10 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Decidir o que fazer com o cap de watchlist no app iOS nativo (deviceStore nunca chama PUT /api/watchlist nem POST /api/watchlist/add — grava direto em localStorage). CR-01 do 12-REVIEW.md, pré-registrado em .planning/todos/pending/cap-gratuito-lacunas-de-cobertura.md com 3 opções (a: dobrar na Fase 13, b: fase 12.1 dedicada, c: aceitar como limitação documentada)."
    expected: "Alex escolhe uma das 3 opções; a decisão determina se CAP-01 precisa de trabalho adicional antes da Fase 13 ou se a limitação é formalmente aceita no ADR-010."
    why_human: "É decisão de produto/escopo (qual plataforma o cap comercial precisa cobrir e quando), não um defeito de implementação do que foi planejado na Fase 12 — o próprio ROADMAP.md já anota isso como 'lacuna conhecida, fora do escopo desta fase'."
  - test: "Confirmar se o follow-up 'separado, fora de escopo' para WR-01 (race condition sem lock em PUT/POST watchlist), WR-02 (can_add_ticker com -1 por coincidência aritmética) e WR-03 (sem validação de tipo em body['tickers']) foi de fato criado em algum lugar rastreável."
    expected: "Um arquivo em .planning/todos/pending/ (ou equivalente) referenciando WR-01/02/03 do 12-REVIEW.md."
    why_human: "Buscas em .planning/todos/ não encontraram nenhum arquivo referenciando WR-01/02/03 ou 'race'/'lock' relacionado à Fase 12 — a alegação de que um follow-up foi 'spawnado' não tem artefato correspondente encontrado nesta verificação. Pode ser que exista em outro lugar (tracker externo, mensagem só na sessão) que este verificador não tem visibilidade — precisa de confirmação humana antes de considerar risco endereçado."
gaps: []
deferred: []
---

# Phase 12: Limites do plano gratuito ativos Verification Report

**Phase Goal:** Usuário no plano gratuito é bloqueado de verdade ao tentar
ultrapassar 10 ativos na watchlist ou 30 análises de IA no mês corrente,
usando a contagem real de `metering.py`; usuário no plano pago não sofre
nenhum dos dois limites; e nenhuma outra funcionalidade do app degrada
quando um limite é atingido.

**Verified:** 2026-08-29
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Free user com 10 ativos não consegue adicionar o 11º via `POST /api/watchlist/add` | VERIFIED | `server/app/main.py:1063-1094` chama `plan.can_add_ticker(len(watchlist), plan=_plano_do_escopo(scope))`; `server/tests/test_fase12_cap_watchlist.py::test_h_*` confirma 402 |
| 2 | Free user com 10 ativos não consegue chegar a 11 via `PUT /api/watchlist` (bypass fechado, D-02/D-03) | VERIFIED | `server/app/main.py:1041-1058` (`put_watchlist`) — gate condicional só quando `len(final) > len(atual)`; `test_fase12_cap_watchlist.py` casos (a)/(b)/(e); prova de regressão documentada no SUMMARY (gate revertido → 6 testes falham) |
| 3 | `PUT /api/watchlist` nunca bloqueia remoção/reordenação, mesmo acima do limite (D-03/D-04, grandfather) | VERIFIED | Código: gate só entra `if len(final) > len(atual)`; testes (c)/(d)/(f) provam grandfather clause por leitura de estado (`len(watchlist)==15` sem truncar) |
| 4 | Free user com 30 análises consumidas não consegue a 31ª, nas DUAS rotas de análise, com mensagem exata | VERIFIED | `_gate_analise` (`main.py:437-456`) chama `plan.can_analyze(metering.month_used(...))`; `test_fase12_cap_analises.py` casos (a)/(b) confirmam `iaIndisponivel.code=="quota"` e mensagem exata nas duas rotas |
| 5 | A contagem que decide o gate mensal é o ledger real de `metering.month_used` (CAP-03), não um contador paralelo | VERIFIED | Teste (d1) espiona `plan.can_analyze` e confirma o valor exato recebido; teste (d2) monkeypatcha `month_used` para 0 e confirma que a negação desaparece — muda o resultado do gate |
| 6 | Conta pro não sofre nenhum dos dois limites | VERIFIED | `PLAN_PRO` com `max_watchlist=None`/`max_analyses_per_month=None` intacto; testes (g)/(e)/(f) provam crescimento >10 e análise #31 liberados para pro |
| 7 | Depois de uma recusa, resto do app continua funcionando (estado, cotações, ordens, redução) | VERIFIED | Testes de não-regressão pós-402 nos dois arquivos (`test_i` watchlist, `test_g` análises) — `GET /api/state`, `GET /api/quotes`, `POST /api/buy`/redução respondem 200 na mesma sessão |
| 8 | Mensagem de recusa é fato+motivo, sem CTA/upgrade (CAP-07) | VERIFIED | `can_add_ticker` reescrita para `"Voce atingiu o limite de {limit} ativos do plano {id}."`; `grep -ci upgrade server/app/plan.py server/app/main.py` = 0 |
| 9 | Suíte canônica inteira (`pytest` + `web/tests/*.mjs`) verde após a ativação | VERIFIED | `bash scripts/executar.sh --testes` executado nesta verificação: `1701 passed, 1 skipped` (pytest) + todos os `.mjs` `[OK]`, 0 FAIL |
| 10 | ADR-010 registra a ativação técnica e o que segue pendente | VERIFIED | `docs/adr/010-planos-e-cap-gratuito.md` — Status alterado para "Parcialmente aceito"; seção `## Atualização — ativação técnica (v1.3, Fase 12, 2026-08-29)` apensada com números, bypass fechado, grandfather, copy, consequência BYOK, ponteiro para Fase 13 |

**Score:** 10/10 truths verified (dentro do escopo declarado pela Fase 12 — ver nota de escopo abaixo)

### Note on Scope — iOS/deviceStore Gap (Not Counted Against This Phase's Score)

O code review (`12-REVIEW.md`, CR-01) encontrou que o app iOS nativo
(`web/src/persistence.js::deviceStore`) grava a watchlist só em
`localStorage` e nunca chama `PUT /api/watchlist` nem
`POST /api/watchlist/add` — os dois pontos que esta fase gateou. Na prática,
o cap de 10 ativos **não vale no app iOS**, só no web/PWA.

Verificado que este achado:
- **NÃO** foi mascarado por nenhum artefato da Fase 12 como "fechado
  cross-platform" — grep em `12-CONTEXT.md`/`12-0X-PLAN.md`/`12-0X-SUMMARY.md`
  não encontrou nenhuma menção a iOS/nativo/`deviceStore`; a linguagem usada
  (D-02 do `12-CONTEXT.md`) fala genericamente em "o frontend usa esse mesmo
  endpoint", que é verdade para o caminho web (`serverStore`), mas nunca
  afirma cobertura do `deviceStore`.
- **Já está pré-registrado** em
  `.planning/todos/pending/cap-gratuito-lacunas-de-cobertura.md`, datado
  2026-08-29, com 3 opções para decisão do Alex.
- **Já está anotado no próprio `ROADMAP.md`**, seção da Fase 12: "Lacunas
  conhecidas, fora do escopo desta fase (precisam de decisão do Alex antes
  da Fase 13): o `deviceStore` do iOS grava a watchlist só no aparelho e não
  passa por gate nenhum (...)".
- **A Fase 13** (próxima), cujo Goal e Success Criteria foram lidos nesta
  verificação, cobre apenas **visibilidade** ("Usuário... vê o número real
  de uso/limite... tanto no web quanto no app iOS nativo") — não cobre
  enforcement no `deviceStore`. Portanto este item **não é elegível para
  filtro de "deferred" (Step 9b)**: nenhuma fase futura do roadmap tem goal
  ou success criteria que resolvam a falta de enforcement no iOS.

Conclusão: o achado é real, consequente (viola a guardrail "Paridade
obrigatória" do `CLAUDE.md` e o próprio texto do Goal desta fase, que não
qualifica "usuário" por plataforma), mas **não é uma regressão introduzida
pela Fase 12** nem uma alegação falsa de nenhum artefato da fase — é uma
lacuna de escopo descoberta durante o planejamento, corretamente escalada e
ainda pendente de decisão humana. Por isso não entra em `gaps:` (reservado
para must-haves que a Fase 12 se comprometeu a entregar e não entregou) —
entra em `human_verification:` no frontmatter, forçando o status
`human_needed`.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `server/app/plan.py` | `max_watchlist=10`, `max_analyses_per_month=30` no FREE; PRO intocado; copy sem CTA | VERIFIED | Lido diretamente — valores corretos, docstring reescrita, `can_add_ticker` sem "upgrade" |
| `server/app/main.py::put_watchlist` | Gate condicional (só crescimento) antes da escrita | VERIFIED | Lido diretamente — `normalize_watchlist` → compara `len(final) > len(atual)` → `plan.can_add_ticker` → 402 se negado |
| `server/app/main.py::watchlist_add` | Gate já existente, referência | VERIFIED | Intocado, continua chamando `plan.can_add_ticker` |
| `server/app/main.py::_gate_analise` | Único ponto de decisão de gate de análise, lê `metering.month_used` | VERIFIED | Lido diretamente — contrato C-32/C-33 preservado |
| `server/app/store.py::normalize_watchlist` | Fonte única do tamanho final efetivo, pura (sem escrita) | VERIFIED | Extraída corretamente; `set_watchlist` delega nela; `db.kv_set` aparece 1x só |
| `server/tests/test_fase3_gate_plano.py` | Guardião invertido (FREE ativo, PRO `None`) | VERIFIED | Testes passam; `PLAN_PRO[...] is None` preservado |
| `server/tests/test_fase5_gate_mensal.py` | `monthLimit == 30` para conta logada free | VERIFIED | Testes passam |
| `server/tests/test_fase12_cap_watchlist.py` | Suíte de comportamento (crescimento/redução/grandfather/pro/não-regressão) | VERIFIED | 14 testes coletados, 0 falhas, executados nesta verificação |
| `server/tests/test_fase12_cap_analises.py` | Suíte de comportamento do cap mensal | VERIFIED | 10 testes coletados, 0 falhas, executados nesta verificação |
| `docs/adr/010-planos-e-cap-gratuito.md` | Registro da ativação v1.3 | VERIFIED | Seção nova presente, Status atualizado, corpo original intacto |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `main.py::put_watchlist` | `plan.py::can_add_ticker` | gate antes da escrita | WIRED | `grep -A12 "def put_watchlist"` confirma a chamada |
| `main.py::put_watchlist` | `store.py::normalize_watchlist` | tamanho final efetivo | WIRED | Confirmado por leitura direta |
| `main.py::put_watchlist` | `main.py::_plano_do_escopo` | plano real da conta | WIRED | Confirmado; nunca `plan.ACTIVE_PLAN` direto |
| `main.py::_gate_analise` | `metering.py::month_used` | contagem real do mês | WIRED | Confirmado por leitura direta + teste com espião |
| `main.py::analyze/technical_analyze` | `iaIndisponivel` (FIX-C01) | 402 do gate vira 200 + fallback determinístico | WIRED | Confirmado pelos testes (a)/(b) de `test_fase12_cap_analises.py` |
| `web/src/persistence.js::deviceStore` (iOS) | `PUT /api/watchlist` / `POST /api/watchlist/add` | — | **NOT_WIRED** | Ver "Note on Scope" acima — gap real, pré-registrado, não é regressão desta fase |

### Behavioral Spot-Checks / Test Execution

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Testes-alvo da Fase 12 + guardiões atualizados | `pytest tests/test_fase12_cap_watchlist.py tests/test_fase12_cap_analises.py tests/test_fase3_gate_plano.py tests/test_fase5_gate_mensal.py -q` | `48 passed` | PASS |
| Suíte canônica completa | `bash scripts/executar.sh --testes` | `1701 passed, 1 skipped` (pytest) + todos os `web/tests/*.mjs` `[OK]`, 0 FAIL | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CAP-01 | 12-01, 12-02 | Free não consegue >10 ativos, ação recusada | SATISFIED (escopo declarado: web/PWA via HTTP) | Ver Observable Truths #1/#2; caveat de escopo iOS documentado separadamente, não rebaixa esta linha |
| CAP-02 | 12-01, 12-03 | Free não consegue >30 análises/mês, recusada | SATISFIED | Observable Truth #4 |
| CAP-03 | 12-03 | Contagem vem do ledger real de `metering.py` | SATISFIED | Observable Truth #5 |
| CAP-04 | 12-01, 12-02, 12-03 | Pro não sofre nenhum limite | SATISFIED | Observable Truth #6 |
| CAP-05 | 12-02, 12-03 | Resto do app não degrada após recusa | SATISFIED | Observable Truth #7 |
| CAP-07 | 12-01, 12-02 | Recusa sem CTA/upgrade | SATISFIED | Observable Truth #8 |
| CAP-06 | (Phase 13, não desta fase) | Exibir uso/limite real na UI | Fora de escopo — corretamente não reivindicado por nenhum plano da Fase 12 | `.planning/REQUIREMENTS.md` mapeia CAP-06 → Phase 13, Pending |

Nenhuma requirement órfã: todos os IDs `CAP-01..05, CAP-07` do frontmatter dos
3 planos aparecem em `.planning/REQUIREMENTS.md` mapeados para Phase 12 e
marcados `[x]`/`Complete`; `CAP-06` está corretamente mapeado para Phase 13.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `server/app/main.py` | 1043-1094 | Read-modify-write sem lock em `PUT /watchlist` e `POST /watchlist/add` (WR-01 do 12-REVIEW.md) | WARNING | Corrida concorrente pode perder um add em `POST` (não pode estourar o cap via `PUT`, que é full-replace); não fixado nesta fase, alegado como follow-up separado mas sem artefato de tracking encontrado |
| `server/app/main.py:1054` | — | `can_add_ticker(len(final)-1, ...)` correto por coincidência aritmética, não por contrato nomeado (WR-02) | WARNING | Frágil a mudança futura no operador de comparação de `can_add_ticker`; não fixado, sem tracking encontrado |
| `server/app/main.py:1050` | — | `body.get("tickers") or []` sem validação de tipo antes de `normalize_watchlist` (WR-03) | WARNING | Payload malformado (string, bool) pode zerar a watchlist em silêncio (200) ou estourar `TypeError` genérico (500); pré-existente à Fase 12, mas esta fase tornou o call site um ponto de gate comercial; não fixado, sem tracking encontrado |
| `server/app/store.py:417-443` | — | `normalize_watchlist` não normaliza case antes de comparar na primeira passada (IN-01) | INFO | Não afeta contagem/cap; só ordem interna em caso raro de ticker minúsculo |

Nenhum debt-marker (`TBD`/`FIXME`/`XXX`) encontrado nos arquivos desta fase.
Nenhum `TODO`/`HACK`/`PLACEHOLDER` novo introduzido.

### Human Verification Required

### 1. Decisão sobre o cap de watchlist no app iOS nativo

**Test:** Ler `.planning/todos/pending/cap-gratuito-lacunas-de-cobertura.md`
(item 1) e decidir entre as opções (a) dobrar no escopo da Fase 13, (b) fase
12.1 dedicada, ou (c) aceitar como limitação documentada no ADR-010.
**Expected:** Uma decisão registrada (ADR-010 atualizado ou novo item de
roadmap) antes de considerar o cap comercial "fechado" para o produto
inteiro — hoje só está fechado para web/PWA.
**Why human:** É trade-off de produto/prioridade, não um bug de
implementação do que a Fase 12 se propôs a fazer.

### 2. Confirmar o follow-up dos achados WR-01/02/03 do code review

**Test:** Localizar o item de trabalho (issue, todo, backlog) que endereça
os 3 Warnings do `12-REVIEW.md` (lock na leitura-decisão-escrita da
watchlist, contrato honesto para `can_add_ticker` em uso bulk, validação de
tipo no body).
**Expected:** Um artefato rastreável (arquivo em `.planning/todos/`, issue
de tracker externo, ou item no ROADMAP) referenciando WR-01/WR-02/WR-03.
**Why human:** Esta verificação não encontrou nenhum arquivo em
`.planning/todos/` referenciando esses 3 achados, apesar do contexto da
tarefa afirmar que "foram spawnados como uma follow-up task separada". Pode
existir em local não visível a este verificador — precisa confirmação antes
de considerar o risco (race condition sem lock em rota de escrita) como
endereçado.

### Gaps Summary

Nenhum must-have da Fase 12 falhou. Os 3 planos (12-01/02/03) entregaram
exatamente o que prometeram: números reais ligados em `plan.py`, bypass do
`PUT /api/watchlist` fechado com semântica de crescimento/grandfather
corretas, suítes de comportamento novas (24 testes) provando os dois caps
por comportamento observável (não só leitura de config), e ADR-010
atualizado. A suíte canônica inteira (pytest + `.mjs`) roda verde nesta
verificação independente.

O que resta em aberto não é um gap de execução da Fase 12, e sim (1) uma
lacuna de escopo pré-registrada — o cap de watchlist não vale no app iOS
nativo, porque `deviceStore` nunca chama os endpoints gateados — que precisa
de decisão do Alex antes de a Fase 13 (ou uma fase dedicada) fechar de
verdade o CAP-01 para a base de usuários inteira; e (2) confirmação de que
os 3 Warnings do code review têm de fato um item de acompanhamento
rastreável, o que esta verificação não conseguiu localizar.

---

_Verified: 2026-08-29_
_Verifier: Claude (gsd-verifier)_
