---
phase: 31-varredura-oportunidades-opcoes
verified: 2026-09-14T20:00:00Z
status: passed
score: 7/7 must-haves verified
overrides_applied: 0
---

# Phase 31: Varredura de oportunidades de opções — Verification Report

**Phase Goal:** Estender a curadoria determinística de oportunidades de opções
(Fase 30) de "1 vencimento × 1 estrutura (venda coberta)" para "até 2
vencimentos × as 4 estruturas que o motor interno já executa" (venda
coberta, put de proteção, collar, opção a descoberto), sobre as posições
que o usuário já tem na carteira — mais responsividade mobile do
`PayoffChart.jsx`. A seleção de quais oportunidades aparecem continua 100%
determinística; a IA, se aparecer, só narra.

**Verified:** 2026-09-14T20:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC-1 | Varredura cobre até 2 vencimentos por posição elegível, custo declarado (≤2× `get_options_chain`) contra orçamento mydata | VERIFIED | `server/app/opcoes_curadoria.py:70` `VENCIMENTOS_POR_POSICAO = 2`; `server/app/main.py:3360-3372` laço de vencimentos extras limitado a `VENCIMENTOS_POR_POSICAO - 1`, budget declarado em docstring (3286-3298). 129 testes de rota/provedor/curadoria verdes, incluindo prova negativa (teto alterado para 3 → teste quebra, revertido). |
| SC-2 | Varredura cobre as 4 estruturas do motor interno | VERIFIED (código/teste); ressalva mock-vs-real herdada para a exibição AO VIVO em 375px | `opcoes_curadoria.py` gera `call_coberta`/`put_protecao`/`collar`/`opcao_a_descoberto` de UMA cadeia em memória (Plano 01, Tasks 1-3). `main.py` publica `meta.candidatosPorTipo` com as 4 chaves sempre presentes. Front (`App.jsx` `CuradoriaEstruturas`) renderiza chip de tipo por card (`ROTULO_TIPO_CURADORIA`) e a linha de resumo (`test_curadoria_ui.mjs`: "(Fase 31) o mapa de rótulo cobre os 4 tipos", "a linha de resumo lê meta.candidatosPorTipo" — ambos passam). A verificação AO VIVO em navegador (checkpoint 31-04 Task 4) rodou contra provedor MOCK, não o servidor real — ressalva explícita em 31-04-SUMMARY.md, herdada aqui, não é gap (checkpoint já resolvido com aprovação literal do Alex — ver nota abaixo). |
| SC-3 | Oportunidade a descoberto só aparece com `permitirOpcaoADescoberto=true` já ligado, sem exceção/aviso | VERIFIED | `candidatos_da_posicao(..., permitir_a_descoberto=False)` fail-closed por padrão (`opcoes_curadoria.py:172`); as duas rotas (`GET /api/options/curadoria`, `POST .../narrativa`) leem o flag exclusivamente de `store.get(_conn,"config",...)` no servidor, nunca do corpo (`main.py:3435`, `3477-3484` — comentário nomeia o motivo T-31-01). Front: `test_curadoria_ui.mjs` confirma nenhuma das 18 frases de copy convida a ligar o flag (D-05). Prova negativa: gate invertido para `if True` → teste de D-05 cai, revertido. |
| SC-4 | Ranking usa uma fórmula só (prêmio ÷ perda máxima) para as 4 estruturas, sem seções separadas | VERIFIED | `rankear()` ordena por `(-razao, -premioUnitario, contractSymbol, idCandidato)` — mesma fórmula para os 4 tipos, sem filtro por tipo (Plano 01 Task 3). Front: `test_curadoria_ui.mjs` confirma `CuradoriaEstruturas` não usa `.sort(`/`.reverse(`/comparação de `item.razao` — a ordem exibida é a do motor. |
| SC-5 | `PayoffChart.jsx` funciona em 375px sem mudar lógica de exibição (uma estrutura por vez, sem overlay) | VERIFIED (estático); ressalva mock-vs-real herdada para o visual AO VIVO | Piso de tipografia (`FONTE_MIN=11.5`), geometria ajustada, supressão determinística de rótulo sobreposto (Plano 03). Guardião `test_payoff_responsivo.mjs`: 20/20 ok, incluindo fence D-08 (zero `useState`/`onClick`/`onPointer`/`onTouch`/`onMouse`, 4 props). Prova negativa (piso rebaixado para 9.5) derruba exatamente a regra do piso, revertido. |
| SC-6 | Varredura cobre só tickers com posição aberta na carteira do usuário | VERIFIED | `_curadoria_top` lê `store.get(_conn, "positions", user_id=scope)` e particiona por elegibilidade (`qty_livre >= 100`) antes de qualquer chamada de rede (`main.py:3313-3317`) — nenhuma referência a watchlist/catálogo. |
| SC-7 | Suíte canônica sem regressão da baseline; `npx vite build` verde | VERIFIED (reverificado diretamente por este agente) | `bash scripts/executar.sh --testes` (sandbox desabilitado, mesma causa "sandbox mente" documentada no projeto): **2910 passed, 5 skipped, 3 xfailed, 0 failed** + **149/149 .mjs OK**, exit 0 — idêntico ao relatado em 31-01/31-02/31-04-SUMMARY. `cd web && npx vite build`: verde, `✓ built in 1.07s`. |

**Score:** 7/7 truths verified (2 com ressalva mock-vs-real herdada, documentada, não-bloqueante — ver nota "Checkpoint mock-vs-real" abaixo)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `server/app/opcoes_curadoria.py` | 4 estruturas + prêmio líquido com sinal + gate de descoberto + `proximos_vencimentos` | VERIFIED | `TIPOS`, `VENCIMENTOS_POR_POSICAO=2`, `CONTRATOS_A_DESCOBERTO=1`, `premio_liquido_unitario`, `id_candidato`, `proximos_vencimentos`, `permitir_a_descoberto` todos presentes e testados (178 testes do módulo+irmãos verdes). |
| `server/app/skill_ref.py` | frase canônica `opcao_a_descoberto` nos dois registros | VERIFIED | 2 ocorrências confirmadas (`operador`/`educacional`), sem cair no fallback `sem_setup` (testado). |
| `server/app/main.py` (`_curadoria_top` + rotas) | varredura de 2 vencimentos + meta por tipo + leitura server-side do flag | VERIFIED | Código lido diretamente; 129 testes de rota/curadoria/provedor verdes. |
| `server/app/options_provider_mydata.py` | cache de vencimentos (1 `get_vencimentos`/ticker/dia) | VERIFIED | `_venc_cache`, `_vencimentos()` confirmados; teste de contagem exata (3 requisições, não 4) verde. |
| `web/src/opcoes/PayoffChart.jsx` | legível em 375px, sem overlay/interatividade | VERIFIED | Piso de tipografia + geometria confirmados; 20/20 asserções do guardião estático passam. |
| `web/src/opcoes/estruturaParaPayoff.js` | adaptador puro PT→envelope do payoff | VERIFIED | Lido integralmente — zero aritmética, `null`-safe, 26/26 asserções do guardião passam. |
| `web/src/copy.js` | 18 chaves `curadoria*`, nos dois modos, sem convite a ligar o flag | VERIFIED | Confirmado por grep + guardião (`test_curadoria_ui.mjs`). |
| `web/src/App.jsx` (`CuradoriaEstruturas`) | tipo por card, chave estável `idCandidato`, resumo, payoff do nº 1 | VERIFIED | Lido diretamente (linhas 4197-4270); `key={item.idCandidato || item.contractSymbol}` confirmado; 46/46 asserções do guardião `test_curadoria_ui.mjs` passam. |
| `server/tests/*` / `web/tests/*` (guardiões) | cobertura das regras acima | VERIFIED | Todos executados diretamente nesta verificação (não apenas lidos) — ver seção Behavioral Spot-Checks. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `opcoes_curadoria.py` | `opcoes_motor.py` | `rastrear/avaliar/perna_de_contrato/perna_de_acao` | WIRED | Padrão herdado da Fase 30, confirmado nos 4 ramos (Plano 01). |
| `opcoes_curadoria.py` | `skill_ref.py` | `opcoes_lastreadas_txt` | WIRED | Manchete/didática de todo tipo, verbatim, sem composição (guardrail CVM confirmado pelo guardião `test_opcoes_collar_vocab.py`, que passou). |
| `main.py` | `opcoes_curadoria.py` | `proximos_vencimentos` + `candidatos_da_posicao(permitir_a_descoberto=...)` | WIRED | Confirmado por leitura direta (linhas 3360-3372). |
| `main.py` | `store.py` | leitura server-side de `permitirOpcaoADescoberto` | WIRED | Confirmado nas duas rotas (3435, 3477-3484), nunca do corpo do cliente. |
| `options_provider_mydata.py` | `mydata_budget.py` | `_debita`/`reservar` | WIRED | Confirmado (`return mydata_budget.reservar(n)` linha 229) — WR-01 do PRÉ-existente lock (Fase 9) intacto. |
| `App.jsx` (`CuradoriaEstruturas`) | `PayoffChart.jsx` | `estruturaParaPayoff` + render do item nº 1 | WIRED | Confirmado (linha 4266), exatamente 1 ocorrência (guardião). |
| `App.jsx` | `main.py` (`GET /api/options/curadoria`) | `meta.candidatosPorTipo`/`tetoVencimentos` | WIRED | Confirmado (linhas 4205-4230). |

### Behavioral Spot-Checks (reexecutados diretamente por este verificador, não apenas lidos)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Suíte canônica completa sem regressão | `bash scripts/executar.sh --testes` (sandbox desabilitado) | 2910 passed, 5 skipped, 3 xfailed, 0 failed; 149/149 .mjs OK; exit 0 | PASS |
| Build de produção do front | `cd web && npx vite build` | `✓ built in 1.07s`, sem erro | PASS |
| Módulo de curadoria (backend, subset) | `pytest tests/test_opcoes_curadoria.py tests/test_opcoes_curadoria_narrativa.py tests/test_opcoes_curadoria_rota.py tests/test_options_provider_mydata.py tests/test_opcoes_collar_vocab.py tests/test_skill_ref.py -q` | 178 passed | PASS |
| Adaptador de payoff (front) | `node web/tests/test_estrutura_para_payoff.mjs` | 26/26 ok, exit 0 | PASS |
| PayoffChart responsivo (front) | `node web/tests/test_payoff_responsivo.mjs` | 20/20 ok, exit 0 | PASS |
| Bloco de curadoria UI (front) | `node web/tests/test_curadoria_ui.mjs` | 46/46 ok, exit 0 | PASS |
| Ausência de debt markers (TBD/FIXME/XXX) nos 8 arquivos-chave da fase | `grep -n "TBD\|FIXME\|XXX"` em cada arquivo | 0 ocorrências em todos | PASS |

### Requirements Coverage

Fase 31 é **standalone** (mesmo padrão da Fase 9 no ROADMAP) — seus IDs de
requisito (SC-1 a SC-7) são definidos diretamente na seção "#### Phase 31"
do `ROADMAP.md` e detalhados em `31-CONTEXT.md` (decisões D1-D9), não em
`.planning/REQUIREMENTS.md`. Confirmado por busca: `grep -n "31\|SC-"
.planning/REQUIREMENTS.md` não retorna nenhuma ocorrência — o arquivo cobre
exclusivamente o milestone v1.4 (Opções v2, NAV/LIB/ENG), que é outro eixo
de trabalho, não esta fase. **Zero requisitos órfãos por construção**, não
por omissão: não há requisito de REQUIREMENTS.md mapeado para a Fase 31 que
não apareça em algum plano.

Cada plano declara seu subconjunto de SCs em `requirements:` no frontmatter,
e a união cobre exatamente SC-1 a SC-7 sem lacuna:
- 31-01: SC-2, SC-3, SC-4 (motor puro)
- 31-02: SC-1, SC-2, SC-3, SC-6 (rota + cache)
- 31-03: SC-5, SC-7 (payoff responsivo)
- 31-04: SC-2, SC-3, SC-4, SC-5, SC-7 (bloco de Posições + checkpoint)

### Anti-Patterns Found

Nenhum bloqueador. Os 3 achados do `31-REVIEW.md` (já classificados lá como
warning, não-bloqueante) foram reconfirmados independentemente por este
verificador via leitura direta do código-fonte, não apenas aceitos do
relatório:

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `web/src/App.jsx` | 4197 (prop), corpo 4197-4310 | Prop `erro` recebida por `CuradoriaEstruturas` mas nunca lida no corpo — falha real de rede renderiza idêntico a "sem estrutura elegível" | Warning (WR-01) | Confirmado por grep: `erro` só aparece na assinatura da função e em `erroNarrativa` (variável homônima diferente); nenhum uso do prop `erro` no corpo. Viola em espírito o princípio 4 do CLAUDE.md ("mostre o estado correto"), mas não fabrica número nem quebra o app — degradação silenciosa, não incorreta em dado financeiro. |
| `web/src/copy.js:624,1137` / `web/src/App.jsx:4253` | — | `curadoriaRazaoAjuda` existe, testado para paridade, nunca renderizado — explicação de D-06 (prêmio negativo) não chega ao usuário | Warning (WR-02) | Confirmado: `grep -n curadoriaRazaoAjuda web/src/App.jsx` não retorna nenhum call site de render, só o comentário. Não é violação de guardrail, é lacuna de UX. |
| `web/src/App.jsx:4571-4585` | — | `useCuradoria()` tem `useEffect` com dependência `[]` — nunca revalida após o mount, ao contrário do hook irmão `useOpcoesPropostas` | Warning (WR-03) | Confirmado por leitura direta (`}, []);` na linha 4585). Lista/payoff podem ficar desatualizados se a carteira mudar com a aba aberta — sem indicação visual de staleness. |

Nenhum dos três toca cálculo financeiro, o guardrail CVM da manchete, ou o
gate D-05 — todos confirmados como classificados corretamente pelo
`31-REVIEW.md` (0 blockers, 3 warnings, 1 info).

### Checkpoint mock-vs-real — nota de proveniência (não é gap)

O checkpoint humano bloqueante da Task 4 (31-04) já foi resolvido dentro da
sessão que produziu esta fase: o orquestrador rodou verificação técnica ao
vivo via Browser pane contra um provedor MOCK de opções (não o servidor
real com dados de mercado reais), apresentou os 8 passos ao Alex via
`AskUserQuestion`, e recebeu duas aprovações literais — a segunda delas
**depois** de a lacuna mock-vs-real ter sido nomeada explicitamente ("Aprovado
mesmo com verificação mock"). Essa proveniência está documentada com
transcrição literal em `31-04-SUMMARY.md`, seção "Checkpoint". Por
instrução explícita desta verificação, este é tratado como checkpoint
legitimamente resolvido, não como um item de verificação humana pendente —
por isso SC-2/SC-3/SC-4/SC-5 aparecem como VERIFIED (com a ressalva anotada
na coluna Evidence), e a seção "Human Verification Required" abaixo está
vazia por desenho, não por omissão.

### Human Verification Required

Nenhum item. O checkpoint que exigiria isso (Task 4 do plano 31-04) já foi
resolvido com aprovação literal do usuário dentro da sessão de execução —
ver nota acima. Nenhuma nova necessidade de verificação humana foi
identificada por esta verificação independente.

### Gaps Summary

Nenhum gap bloqueante. Três achados de qualidade/UX não-bloqueantes
(WR-01/02/03 do `31-REVIEW.md`), todos reconfirmados diretamente nesta
verificação, permanecem como dívida técnica conhecida e documentada — não
tocam cálculo financeiro, o guardrail CVM, nem o gate `permitirOpcaoADescoberto`.

Pendências operacionais conhecidas e deliberadamente deferidas pelo próprio
Alex nesta rodada (não são gaps desta verificação):
- **Publicação:** `scripts/bump.sh` + `scripts/publicar-web.sh` não
  executados — Alex pediu só fechamento local ("Aprovado, fechar a fase").
- **App iOS nativo:** não reflete esta fase sem `cap sync` + build novo no
  Xcode — pendência operacional já conhecida de fases anteriores, não
  defeito desta fase.

---

_Verified: 2026-09-14T20:00:00Z_
_Verifier: Claude (gsd-verifier)_
