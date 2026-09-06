---
phase: 21-duplica-o-removida-e-portf-lio-consolidado
verified: 2026-09-05T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 21: Duplicação removida e Portfólio consolidado Verification Report

**Phase Goal:** O usuário para de ver a mesma informação duas vezes: a curva
de patrimônio existe em uma única tela, o status do Operador aparece uma vez
só, e os números do Portfólio viram um card denso — e o gráfico deixa de
mostrar caixa vazia quando ainda há pouco dado.
**Verified:** 2026-09-05
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (mapeada a requisito) | Status | Evidence |
|---|---|---|---|
| 1 | DEDUP-01 — `CapitalCurve`/"PATRIMÔNIO SIMULADO" existe em exatamente UMA tela | ✓ VERIFIED | `grep -n "<CapitalCurve" web/src/App.jsx` → 1 ocorrência única (linha 2039), dentro de `EvolucaoScreen` (1889–4311); `CarteiraScreen` (4311+) não contém `<CapitalCurve`. Guardião `test_fase21_dedup_consolidacao.mjs` (17 asserções DEDUP-01/03) executado diretamente por este verificador — 39/39 `ok` no arquivo inteiro, exit 0. Bundle de produção (`server/web_dist/assets/index-DyIcihNZ.js`) contém `PATRIMÔNIO TOTAL` — confirma que a mudança chegou ao build publicado. Confirmação em DOM real (Acompanhar tem, Portfólio não) registrada na apêndice "Orchestrator Live Re-Verification" do `21-01-SUMMARY.md` e fechada em `21-04-SUMMARY.md` ("Fechamento do roteiro pelo orquestrador"). |
| 2 | DEDUP-03 — Portfólio mostra 1 card consolidado 2×2 (não 4 cards empilhados) | ✓ VERIFIED | Leitura direta de `CarteiraScreen` (`App.jsx:4361-4381`): um único `<div style={{...card}}>` com `gridTemplateColumns: "1fr 1fr"` contendo as 4 células (PATRIMÔNIO TOTAL/RESULTADO ABERTO/CAIXA DISPONÍVEL/EM POSIÇÕES), cada uma usando `{...numBody, fontFamily: MONO, ...}` / `{...numMicro, ...}` (Fase 20). Helper `kpi(` removido por completo (`grep -n "kpi("` → 0 ocorrências). Guardião confirma ausência do grid antigo `repeat(auto-fit,minmax(160px,1fr))`. Bundle de produção contém a assinatura. DOM real (`gridTemplateColumns: "141.5px 141.5px"`, `scrollWidth===clientWidth` em 375px) registrado no fechamento do roteiro (`21-04-SUMMARY.md`). |
| 3 | DEDUP-02 — Operador IA mostra modo/operador/execução uma única vez | ✓ VERIFIED | `grep -n "Modo do app"` em `App.jsx` → 0 ocorrências (texto removido); "Trocar modo →" presente 1× (`App.jsx:4796`), com `onClick={() => A.go("perfil")}`, ANTES do card-herói "OPERADOR NO SERVIDOR" (4803+); transparência `ctx.cp.entradaAuto.regra`/`.contraste` (`App.jsx:4975-4976`) realocada para dentro do card "ENTRADA AUTOMÁTICA" (`App.jsx:4958`). Os 3 guardiões que travavam o card antigo (`test_fase3_c19_card_status.mjs`, `test_auditoria_status_strip.mjs`, `test_historico_setup_card_ui.mjs`) foram lidos (cabeçalho com nota de reversão datada 2026-09-05, conforme regra do CLAUDE.md "guardiões não se apagam") e executados diretamente por este verificador — os 3 passam (8+6+25 asserções, 0 falhas). Bundle de produção NÃO contém "Modo do app:" (checado em todos os chunks JS, 0 ocorrências) e contém "Trocar modo". |
| 4 | FIX-03 — placeholder de "poucos dias" substitui a reta de escala degenerada | ✓ VERIFIED | `App.jsx:1741-1742`: `hasSeries = ec.days >= 3` (era `>= 1`), `poucosDias = ec.days >= 1 && ec.days < 3`; terceiro ramo JSX (`App.jsx:1856-1859`) chama `cp.curvaPoucosDias(ec.days)`, nunca texto hardcodado. `curvaPoucosDias(dias)` presente em `COPY.estudo` e `COPY.operador` (`web/src/copy.js:35`, `:263`), texto idêntico nos dois modos, com pluralização real. Guardião (seção FIX-03, 22 asserções) chama `equityCurve()` REAL (não mockado) com 0/1/2 snapshots e confirma `curve.length===2` para 1 snapshot de hoje (a escala degenerada motivadora) — executado por este verificador, passa. Texto do estado zero ("Sua curva começa amanhã...") confirmado byte a byte inalterado. Bundle de produção contém "a curva aparece a partir do 3º dia". **Nota aceita**: o estado real de 1-2 dias em DOM nunca foi observado ao vivo (não dá para forçar sem semear dado ou esperar dias reais) — fechado via prova unitária direta da função pura, decisão de engenharia razoável documentada no `21-03/21-04-SUMMARY.md`, não afeta o veredito. |

**Score:** 4/4 truths verificadas em código-fonte + guardião executado por este verificador + bundle de produção; as 3 primeiras têm também confirmação em DOM real registrada pelo orquestrador (apêndices "Orchestrator Live Re-Verification" nos SUMMARYs 21-01/21-02/21-04).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web/src/App.jsx` | Rota Portfólio sem `CapitalCurve` duplicada; card consolidado 2×2; `AgenteScreen` sem card de status; `CapitalCurve` com limiar de 3 dias | ✓ VERIFIED | Todas as 4 mudanças confirmadas por leitura direta do arquivo (linhas citadas acima); `npx vite build` executado por este verificador → sucesso, exit 0, sem erro. |
| `web/src/copy.js` | `curvaPoucosDias(dias)` em `COPY.estudo` e `COPY.operador` | ✓ VERIFIED | Presente nas 2 chaves, texto correto, pluralização testada pelo guardião. |
| `web/tests/test_fase21_dedup_consolidacao.mjs` | Guardião único DEDUP-01/03 + FIX-03 | ✓ VERIFIED | Executado por este verificador: 39/39 `ok`, exit 0. |
| `web/tests/test_fase3_c19_card_status.mjs` | Reversão datada de DEDUP-02, travando estado novo | ✓ VERIFIED | Executado: 8/8 `ok`, exit 0; cabeçalho com nota de reversão 2026-09-05. |
| `web/tests/test_auditoria_status_strip.mjs` | Reversão datada da tira de status | ✓ VERIFIED | Executado: 6/6 `ok`, exit 0. |
| `web/tests/test_historico_setup_card_ui.mjs` | Recorte repontado para card ENTRADA AUTOMÁTICA | ✓ VERIFIED | Executado: 25/25 `ok`, exit 0 (contagem de `ok(` não encolheu — 18 vs. 17 anteriores, conforme SUMMARY). |
| `web/src/version.js` | `BUILD_ID` novo | ✓ VERIFIED | `BUILD_ID = "F10-20260905-03"`. |
| `server/app/main.py` | `SERVER_BUILD_ID` sincronizado | ✓ VERIFIED | `SERVER_BUILD_ID = "F10-20260905-03"` — coerente com `version.js`. |
| `server/web_dist` | Bundle publicado com as 4 mudanças | ✓ VERIFIED | `grep` neste verificador confirma presença de `PATRIMÔNIO TOTAL`/`Trocar modo`/`3º dia` e AUSÊNCIA de `Modo do app:` em todos os chunks JS minificados. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `App.jsx` (card consolidado) | `numBody`/`numMicro`/`card`/`kicker`/`MONO` (Fase 20) | spread `{...numBody, ...}` | ✓ WIRED | Confirmado por leitura direta e pelo guardião (≥4 ocorrências de `...numBody`, ≥1 de `...numMicro`). |
| `test_fase21_dedup_consolidacao.mjs` | `App.jsx` | `readFileSync` + regex | ✓ WIRED | Guardião roda e falha/passa de fato (verificado por execução direta, não apenas leitura). |
| `AgenteScreen` (link relocado) | tela Perfil | `onClick={() => A.go("perfil")}` | ✓ WIRED | Confirmado literal em `App.jsx:4795-4796`. |
| `AgenteScreen` (card ENTRADA AUTOMÁTICA) | `copy.js COPY[modo].entradaAuto.*` | `ctx.cp.entradaAuto.regra`/`.contraste` | ✓ WIRED | Confirmado em `App.jsx:4975-4976`, dentro do card certo (linhas 4958-4979), sem hardcode (guardião de não-hardcode passa). |
| `CapitalCurve` | `copy.js COPY[modo].curvaPoucosDias` | `cp.curvaPoucosDias(ec.days)` | ✓ WIRED | Confirmado em `App.jsx:1858`; `cp` desestruturado de `ctx` na linha 1729. |
| `CapitalCurve` | `finance.js equityCurve` | `ec.days >= 3` | ✓ WIRED | Confirmado em `App.jsx:1741`; guardião prova com `equityCurve()` real que o gate produz o resultado esperado para 0/1/2 snapshots. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Guardião DEDUP-01/03/FIX-03 executa e passa | `node web/tests/test_fase21_dedup_consolidacao.mjs` | 39 `ok`, exit 0 | ✓ PASS |
| Guardião DEDUP-02 (3 arquivos) executa e passa | `node web/tests/test_fase3_c19_card_status.mjs` / `test_auditoria_status_strip.mjs` / `test_historico_setup_card_ui.mjs` | 8+6+25 `ok`, exit 0 cada | ✓ PASS |
| Build de produção do front compila | `npx vite build` (dentro de `web/`) | `✓ built in 2.80s`, exit 0 | ✓ PASS |
| Bundle publicado contém as adições e não contém o texto removido | `grep` nos chunks de `server/web_dist/assets/*.js` | `PATRIMÔNIO TOTAL`/`Trocar modo`/`3º dia` presentes; `Modo do app:` 0 ocorrências em todos os chunks | ✓ PASS |
| Suíte canônica completa (`bash scripts/executar.sh --testes`) | pytest + `web/tests/*.mjs` | `2021 passed, 1 skipped` (pytest); `116 [OK] / 0 [X]` (web) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| DEDUP-01 | 21-01 | Curva de patrimônio em exatamente uma tela | ✓ SATISFIED | Ver Truth #1 |
| DEDUP-02 | 21-02 | Status do Operador aparece uma única vez em Operador IA | ✓ SATISFIED | Ver Truth #3 |
| DEDUP-03 | 21-01 | Card consolidado 2×2 no Portfólio | ✓ SATISFIED | Ver Truth #2 |
| FIX-03 | 21-03 | Placeholder de poucos dias em `CapitalCurve` | ✓ SATISFIED | Ver Truth #4 |

Nenhum requisito órfão: os 4 IDs do ROADMAP da Fase 21 (`DEDUP-01, DEDUP-02,
DEDUP-03, FIX-03`) aparecem no campo `requirements` de algum plano (21-01,
21-02, 21-03, e novamente todos os 4 em 21-04 como plano de publicação) e
todos têm evidência de implementação.

**Nota de sincronismo de documento (não-bloqueante):** `.planning/REQUIREMENTS.md`
ainda lista os 4 IDs como `[ ]` (checkbox) e status `Pending` na tabela de
cobertura (linhas 129-132). Isso é esperado — a atualização para `Complete`
é uma etapa de fechamento posterior a esta verificação (mesmo padrão
observado para a Fase 20, cujos requisitos já aparecem `Complete` na tabela
mas ainda `[ ]` no checkbox de texto). Não é um gap de código; fica registrado
para o orquestrador atualizar ao fechar a fase.

### Anti-Patterns Found

Nenhum. Varredura de `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` nos 8 arquivos
tocados pela fase (`App.jsx`, `copy.js`, `version.js`, `main.py`, e os 4
arquivos de teste) não encontrou nenhuma ocorrência. Nenhum `console.log`
órfão, nenhum handler vazio, nenhum retorno estático substituindo dado real.

### Human Verification Required

Nenhum item pendente. As três metades de goal com componente puramente
visual/de fluxo (DEDUP-01, DEDUP-02, DEDUP-03) já têm confirmação em DOM
real registrada pelo orquestrador via MCP de navegador contra o bundle de
produção (`21-01-SUMMARY.md`, `21-02-SUMMARY.md` e o "Fechamento do roteiro"
em `21-04-SUMMARY.md`), incluindo o gotcha de service-worker/cache PWA
reconhecido e contornado (mesmo precedente da Fase 20). Este verificador não
tem ferramenta de navegador na própria sessão e por isso não reproduziu os
números de DOM de forma independente — mas corroborou de forma independente
tudo o que é estático/determinístico (código-fonte, guardiões executados ao
vivo por este verificador, bundle minificado publicado, suíte canônica
completa), o que é consistente com as medições de DOM relatadas (ex.: a
ausência de "Modo do app:" no bundle publicado bate exatamente com o "0
ocorrências" relatado em DOM).

O único ponto que ficou formalmente "aberto" nos SUMMARYs (estado real de
1-2 dias de `CapitalCurve` em tela) foi uma decisão de escopo do próprio
plano 21-03/21-04 — aceita aqui como fechada por prova unitária direta da
função pura `equityCurve()`, não por não-verificação.

### Gaps Summary

Nenhum gap. Os 4 critérios de sucesso do ROADMAP da Fase 21 estão
implementados no código-fonte, cobertos por guardiões de teste que este
verificador executou diretamente (não apenas leu), presentes no bundle de
produção publicado (`server/web_dist`, carimbo `F10-20260905-03` coerente
em `web/src/version.js` e `server/app/main.py`), e a suíte canônica
completa (`bash scripts/executar.sh --testes`) está verde: `2021 passed, 1
skipped` (pytest) + `116 [OK] / 0 [X]` (web). `npx vite build` verde.
Nenhum `git push` foi identificado nos commits desta fase (verificado por
`git log`, publicação ficou local).

---

*Verified: 2026-09-05*
*Verifier: Claude (gsd-verifier)*
