---
phase: 32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone
verified: 2026-09-16T00:00:00Z
status: passed
score: 8/8 — 7/7 truths verificadas por código+suíte; o comportamento pendente (multi-candidato) foi observado ao vivo na quick 260916-cod
resolved_by: 260916-cod (2026-09-16) — ver .planning/quick/260916-cod-fecha-achados-pos-fase-32/260916-cod-SUMMARY.md
overrides_applied: 0
human_verification:
  - test: "Multi-candidato lado a lado na sub-aba Operar (item 8 do roteiro do 32-05-PLAN.md)"
    expected: "Uma posição com 2+ candidatos elegíveis (ex.: put isolada + collar na mesma posição, MULTI-01) mostra os cartões lado a lado, mesma largura, na sub-aba Operar da aba Opções."
    resolvido_em: "2026-09-16, quick 260916-cod — OBSERVADO AO VIVO. A fixture era escolher a posição certa, não alterar código: a coexistência put isolada + collar exige plano com decisao==VENDER ou lado==baixa (opcoes_lastreadas.py:247); as sessões anteriores só tinham testado posições de alta/lateral. Com ABEV3 (plano de baixa) 500 cotas, /api/options/proposta/ABEV3?multiperna=1 devolveu candidatos [put_protecao, collar] e a sub-aba Operar renderizou os dois cartões — PUT DE PROTEÇÃO e TRAVA PROTETORA — na mesma linha (y=399), mesma largura (210px), x=165 e x=385, medido no DOM."
    why_human_original: "O código existe e está coberto por guardião estático (test_opcoes_multi_candidato_ui.mjs, sanidade comprovada por injeção real de defeito no 32-04) e pela cadeia real de dados (API /api/options/proposta/{ticker} sempre devolve candidatos). Mas o provedor mock usado na verificação ao vivo do 32-05 nunca produziu a coexistência put isolada + collar na mesma posição — o ramo `multi` nunca foi observado renderizando em navegador. Grep e teste estático não substituem ver rodando; é dívida de verificação, não de implementação (ver 32-05-SUMMARY.md, item 8 da tabela de checkpoint, e estado_conhecido desta verificação)."
---

# Phase 32: Consolidação das operações de opções na aba Opções — Verification Report

**Phase Goal:** Concentrar na aba Opções todo o conteúdo de OPERAÇÃO com opções
que hoje vive espalhado entre Posições e Opções, reduzindo a poluição da tela
de Posições sem perder a descoberta da oportunidade.

**Verified:** 2026-09-16
**Status:** passed *(era `human_needed`; o único item pendente foi observado ao vivo na quick `260916-cod`, 2026-09-16)*
**Re-verification:** Não — verificação inicial (nenhum `32-VERIFICATION.md` prévio encontrado).

## Método

Verificação goal-backward independente do SUMMARY: leitura de todos os 5
PLAN.md/SUMMARY.md, do `32-CONTEXT.md` (decisões D-01 a D-07), do
`32-UI-SPEC.md`, do `32-05-AUDITORIA.md` e do `deferred-items.md`; em seguida,
confirmação por grep direto no código-fonte atual (não no que o SUMMARY
alegou), execução da suíte canônica completa (`bash scripts/executar.sh
--testes`, as duas suítes), `npm --prefix web run build`, e consulta HTTP ao
carimbo de build em produção. Nenhuma alegação abaixo depende só de prosa de
SUMMARY.

## Goal Achievement

### Observable Truths (D-01 a D-07, cruzadas com o código real)

| # | Decisão / Truth | Status | Evidência |
|---|---|---|---|
| 1 | D-01 — Posições perde os 4 blocos de opções; fica uma única linha de chamada com contagem | ✓ VERIFIED | `web/src/App.jsx:4216 function LinhaChamadaOpcoes(...)`; `grep -c "<LinhaChamadaOpcoes" App.jsx` = 1; `grep -c "<OportunidadesOpcoes\|<CuradoriaEstruturas"` = 0 (só comentários em prosa, confirmado por `grep -n`); `PropostaDaPosicao` ausente de `App.jsx` (só menções em comentário histórico) |
| 2 | D-02 — clique na linha leva à lista de oportunidades, sem deep-link | ✓ VERIFIED | `App.jsx`: `onIr={ctx.goOpcoes}`; `ctx.goOpcoes: () => navigate("opcoes")` sem parâmetro de ticker/candidato; guardião `test_opcoes_consolidacao_ui.mjs` trava ausência de deep-link |
| 3 | D-03 — contagem da linha vem do mesmo dado da lista curada (fonte única) | ✓ VERIFIED | `LinhaChamadaOpcoes` recebe `curadoria={ctx.curadoria}`; `useCuradoria(` aparece 1x como definição + 1x como chamada em `App()`; `OpcoesScreen.jsx` lê o MESMO `ctx.curadoria` no `blocoCuradoria`. Confirmado ao vivo no 32-05-SUMMARY (item 2): "4 oportunidades" na linha == 4 cartões na lista |
| 4 | D-04 — curadoria no topo da aba Opções (fora do ticker); blocos por posição na sub-aba Operar | ✓ VERIFIED | `OpcoesScreen.jsx`: ordem confirmada por código `{fraseDuasLeituras} → {blocoOportunidades} → {blocoCuradoria} → {blocoVigias}` (índices 42077 < 42103 < 42130 < 42350); `SubAbaOperar` (linha ~1297) contém `candidatos.length > 1` (multi) e `<PropostaLastreada` (único) |
| 5 | D-05 — os dois motores lado a lado com rótulos que negam hierarquia | ✓ VERIFIED | `OpcoesScreen.jsx:711-713` renderiza `cp.duasLeiturasIntro` incondicionalmente (sem `&&`/ternário, sem `aria-expanded`); `copy.js` contém a chave nos dois modos com "nenhuma é mais certa que a outra"; guardião novo comprovou por injeção (aria-expanded reprovou, revertido) |
| 6 | D-06 — nada impede busca/filtro futuro; sem sticky/fixed novo nos blocos | ✓ VERIFIED | Verificado por esta verificação (não só pelo AUDITORIA): nenhum `position: sticky/fixed` em `OpcoesScreen.jsx`/`CandidatoOpcao.jsx`/`CuradoriaEstruturas.jsx`/`OportunidadesOpcoes.jsx`; os `position: fixed` que existem em `App.jsx` são modais pré-existentes não relacionados (buy/sell/catálogo/toast), não os blocos migrados; os `<input>` existentes em `OpcoesScreen.jsx`/`CuradoriaEstruturas.jsx` são campo "Lote"/checkbox de liquidez pré-existentes, não busca/filtro novo |
| 7 | D-07 — `OportunidadesOpcoes` (motor COM gate) permanece visível, topo da aba, ao lado da curadoria | ✓ VERIFIED | `OpcoesScreen.jsx` `blocoOportunidades` renderiza `<OportunidadesOpcoes .../>` antes de `blocoCuradoria`, fora do seletor de ticker; componente não foi deletado nem movido para dentro de Operar |
| 8 | MULTI-02 (REQUIREMENTS.md) — N candidatos lado a lado, usuário aceita exatamente um | ✓ VERIFIED *(ao vivo, quick 260916-cod)* | Observado renderizando com ABEV3 (plano de baixa, o que faz `propor()` entrar no ramo `put_protecao` e tentar o collar): dois cartões lado a lado, mesma linha e mesma largura, medidos no DOM. Guardião estático `test_opcoes_multi_candidato_ui.mjs` segue cobrindo a regressão |

**Score:** 8/8 — 7/7 truths de código verificadas nesta verificação, mais o comportamento multi-candidato observado ao vivo na quick `260916-cod` (2026-09-16).

### Requirements Coverage

| Requirement | Fonte | Descrição | Status | Evidência |
|---|---|---|---|---|
| D-01 a D-07 | `32-CONTEXT.md` | Decisões de produto da fase 32 | ✓ SATISFIED (todas) | Ver tabela de truths acima |
| MULTI-02 | `.planning/REQUIREMENTS.md` linha 93/145 (Fase 19, listada como "Pending") | "O detalhe da posição em Posições mostra os N candidatos lado a lado" | ✓ SATISFIED pelo código, com nota de dívida de documentação | O código entrega candidatos lado a lado (`SubAbaOperar`, `OpcoesScreen.jsx`), mas NÃO mais "em Posições" — foram movidos para a sub-aba Operar da aba Opções por decisão explícita e documentada do Alex (D-04, `32-CONTEXT.md`). A redação literal de MULTI-02 ficou desatualizada por essa decisão arquitetural posterior e legítima, não por omissão da fase 32. `REQUIREMENTS.md` segue com MULTI-02 marcado "Pending" — é dívida de manutenção do documento de rastreabilidade (atualizar redação/local e status), não um gap de implementação desta fase. Verificação AO VIVO do comportamento em si (item 8 da tabela acima) segue pendente. |

Nenhum requirement órfão encontrado: `32-CONTEXT.md` declara D-01..D-07 como o escopo rastreável desta fase; todos os 5 PLAN.md declaram `requirements:` cobrindo o subconjunto que implementam, e a soma cobre D-01 a D-07 por completo (32-01: D-01/D-03/D-05; 32-02: D-03/D-04/D-07; 32-03: D-01/D-02/D-03/D-04/D-05/D-06/D-07; 32-04: D-01/D-04; 32-05: D-01 a D-07 como auditoria/publicação final).

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `web/src/copy.js` | 9 chaves novas + 3 conteúdos reescritos, nos dois modos | ✓ VERIFIED | Confirmado por `test_consolidacao_opcoes_copy.mjs` (guardião dedicado, 24 asserções, passou na suíte canônica) |
| `web/src/opcoes/OportunidadesOpcoes.jsx` | Bloco A (motor COM gate) como módulo terceiro | ✓ VERIFIED | Existe, `export default`, não importa `App.jsx` |
| `web/src/opcoes/CuradoriaEstruturas.jsx` | Bloco B (motor SEM gate), lê `erro` com precedência sobre vazio | ✓ VERIFIED | Confirmado por grep direto: `erro` na assinatura, ramo `top.length === 0 && !carregando && erro` antes do ramo `!erro` |
| `web/src/opcoes/CandidatoOpcao.jsx` | Cartão reusável, consumido por Operar | ✓ VERIFIED | Importado em `OpcoesScreen.jsx`, usado no ramo `multi` |
| `web/src/opcoes/useOpcoesPropostas.js` | Hook extraído, `store` por parâmetro | ✓ VERIFIED | Existe como módulo; `App.jsx` só importa, não define mais |
| `web/src/opcoes/OpcoesScreen.jsx` | Frase-ponte + Bloco A + Bloco B no topo da sub-aba Setups; `SubAbaOperar` com ramo multi | ✓ VERIFIED | Ordem confirmada por índice de string; `candidatos.length > 1` presente |
| `web/src/App.jsx` | `LinhaChamadaOpcoes`, `ctx.curadoria`, `ctx.goOpcoes`; sem `PropostaDaPosicao`/blocos cross-carteira | ✓ VERIFIED | Todos confirmados por grep direto nesta verificação |
| `web/tests/test_opcoes_consolidacao_ui.mjs` | Guardião dedicado da consolidação | ✓ VERIFIED | Existe, passou na suíte, 32 asserções conforme SUMMARY |
| `server/web_dist` | Bundle publicado com a consolidação | ✓ VERIFIED | `curl https://boris.semente.dev/api/health` → `{"ok":true,"build":"F10-20260916-01"}`, mesmo carimbo do 32-05-SUMMARY |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `LinhaChamadaOpcoes` | `ctx.goOpcoes` | `onIr` | ✓ WIRED | `onIr={ctx.goOpcoes}` confirmado por grep |
| `LinhaChamadaOpcoes` | `ctx.curadoria.top.length` | contagem | ✓ WIRED | `curadoria={ctx.curadoria}` — fonte única, sem segunda instância do hook |
| `OpcoesScreen.jsx blocoCuradoria` | `ctx.A.executarCandidatoCurado` | `onExecutar` | ✓ WIRED | `onExecutar={(cand, o) => ctx.A.executarCandidatoCurado(cand, o)}` (linha 748); definição intocada em `App.jsx:8437` |
| `ctx.A.executarCandidatoCurado` | `executarCandidato.js` → `optionsCuradoriaAbrirCollar` → `POST /api/options/curadoria/abrir-collar` | cadeia de execução do collar | ✓ WIRED (verificado por CLIQUE REAL, não só estático) | 32-05-SUMMARY registra execução real: card ITUB4 (venda coberta) abriu posição de verdade com variação de caixa exata (+R$195); ramo collar (inalcançável por clique no mock) foi exercitado com o MÓDULO real (`executarCandidato.js` + `persistence.js` real) e abriu duas pernas reais em BBDC4 |
| `SubAbaOperar` | `CandidatoOpcao` | `<CandidatoOpcao` no ramo multi | ✓ WIRED (estaticamente) / ⚠️ nunca visto renderizando | Código presente e testado estaticamente; não exercitado ao vivo (ver Human Verification) |

### Anti-Patterns Found

Nenhum `TBD`/`FIXME`/`XXX` nos arquivos modificados pela fase
(`web/src/App.jsx`, `web/src/copy.js`, `web/src/opcoes/*.jsx`,
`web/src/opcoes/useOpcoesPropostas.js`) — checado por grep direto nesta
verificação.

O único item de débito conhecido (`|| 0` em três cópias de `porLote`/CTA de
collar) está registrado em `deferred-items.md`, com risco classificado como
BAIXO pelo executor e justificativa técnica sólida (campos que nunca vêm
nulos para um candidato válido). Não bloqueia o goal desta fase — é um achado
pré-existente (idêntico em `PropostaLastreada.jsx` desde a Fase 28), ampliado
em visibilidade pela extração, não criado por ela. Não escalo como BLOCKER;
registro como ℹ️ Info herdado.

### Item 1 da AUDITORIA (range de diff) — resolvido nesta verificação

O `32-05-AUDITORIA.md` sinalizou como "achado-condicional" a escolha de range
(`main...HEAD` lista arquivos proibidos; `bd459f1..HEAD` não lista) e pediu
ratificação externa. Verificado independentemente nesta sessão:

```
$ git merge-base --is-ancestor origin/main HEAD && echo ancestral
ancestral
```

`origin/main` (`df34cb6`) é ancestral direto de `HEAD` — confirma que
`main...HEAD` mistura histórico não relacionado (Fase 31 + quicks
`260915-j5l`/`260915-ndt`, publicados via releases próprios mas não
mesclados de volta a `main` local) com os commits da própria Fase 32.
`bd459f1..HEAD` (o estado do repo imediatamente antes de `df34cb6 docs(32):
registra a Fase 32`) é o range correto para julgar esta fase, e por ele
NENHUM dos arquivos proibidos (`executarCandidato.js`, `persistence.js`,
`api.js`, `server/app/`) aparece no diff — confirmado por leitura direta do
output em `git diff --name-only bd459f1..HEAD`. **Item 1: LIMPO, ratificado.**

## Verificação técnica independente executada nesta sessão

- `bash scripts/executar.sh --testes` (sem sandbox, `dangerouslyDisableSandbox: true`) — **exit 0**, as duas suítes completas (backend pytest + `web/tests/*.mjs`). A primeira tentativa dentro do sandbox padrão reportou 27 falhas de backend, todas `PermissionError` em `ssl.py` — o mesmo padrão de falso-negativo já documentado em todos os SUMMARYs da fase e em `worktree-test-setup.md` (MEMORY do usuário). Confirmado como falso-negativo pela reexecução fora do sandbox.
- `npm --prefix web run build` — exit 0, sem erro de sintaxe.
- `curl https://boris.semente.dev/api/health` — `{"ok":true,"build":"F10-20260916-01"}`, confirmando que a consolidação está publicada em produção com o mesmo carimbo declarado no 32-05-SUMMARY.
- Grep direto (não confiando no SUMMARY) de: `LinhaChamadaOpcoes`, ausência de call sites de `OportunidadesOpcoes`/`CuradoriaEstruturas`/`PropostaDaPosicao` em `App.jsx`, ordem dos blocos em `OpcoesScreen.jsx`, precedência de `erro` em `CuradoriaEstruturas.jsx`, wiring de `executarCandidatoCurado`, ausência de `TBD/FIXME/XXX`, ausência de `sticky`/`fixed`/`input` de busca novos.
- `git merge-base --is-ancestor origin/main HEAD` — ratifica o range usado no `32-05-AUDITORIA.md`.

## Human Verification Required

### 1. Multi-candidato lado a lado na sub-aba Operar

**Test:** Encontrar (ou construir com uma conta de teste) uma posição cuja
leitura técnica endosse simultaneamente put isolada E collar (MULTI-01),
abrir a aba Opções → sub-aba Operar com essa posição selecionada.
**Expected:** Dois (ou mais) cartões `CandidatoOpcao` lado a lado, mesma
largura, com o mesmo botão de aceite (`aceitarCandidato`) para ambos —
aceitar um desabilita a rodada para os demais.
**Why human:** O código está implementado e coberto por guardião estático
com sanidade comprovada (injeção real de defeito em `32-04`, reprovou
corretamente), e a API já devolve `candidatos` para o front consumir. Mas na
verificação ao vivo do `32-05` (ambiente com `B3_OPTIONS_PROVIDER=mock`),
nenhuma das 5 posições testadas produziu a coexistência que o ramo `multi`
exige — o mock não gera essa combinação. O ramo nunca foi visto renderizando
em navegador real. Isto é uma dívida de verificação herdada e documentada
pelo próprio orquestrador (`estado_conhecido` desta tarefa), não uma falha de
implementação: grep e teste estático não substituem ver o layout, o
espaçamento entre 2 cartões e o comportamento de exclusividade rodando de
verdade.

## Gaps Summary

Nenhum gap de implementação encontrado. Todas as 7 decisões D-01 a D-07 estão
provadas em código (não apenas alegadas em SUMMARY), a cadeia de execução do
collar curado foi provada por clique real (dois ramos), a suíte canônica
passa inteira, o build é limpo, e a consolidação está publicada em produção
com o carimbo correto. O único item pendente é uma verificação COMPORTAMENTAL
ao vivo (multi-candidato, item 8), que o próprio produto e a auditoria da
fase já isolaram como dívida de verificação — não de código — e que este
relatório mantém explícita em vez de arquivá-la silenciosamente atrás de um
score 7/7.

Nota de manutenção fora do escopo de bloqueio: `.planning/REQUIREMENTS.md`
(linhas 93 e 145) segue com MULTI-02 grafado "em Posições" e status
"Pending", desatualizado pela decisão D-04 desta fase (que moveu
multi-candidato de Posições para a sub-aba Operar em Opções). Recomendo ao
Alex atualizar a redação/status de MULTI-02 na próxima revisão de
`REQUIREMENTS.md`, mas isso não é um gap desta fase — é dívida de
rastreabilidade documental.

---

*Verified: 2026-09-16*
*Verifier: Claude (gsd-verifier)*
