---
phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis
plan: 02
subsystem: web/opcoes (camada explicativa do payoff)
tags: [payoff, explicacao, copy, tdd, opcoes]
dependency-graph:
  requires: [Fase 36 — dominio_da_curva()/segmentos_da_curva() (server/app/opcoes_payoff.py)]
  provides:
    - "web/src/opcoes/ExplicacaoPayoff.jsx (componente puro + montarTexto exportado)"
    - "formatarRazao() exportada de web/src/opcoes/uiOpcoes.jsx (fonte única da razão G/P)"
    - "19 chaves novas de copy em web/src/copy.js (CHART-01/02/03/05 + EXPL-01..03), pareadas Estudo/Operador"
  affects:
    - "Plano 37-04 (geometria do gráfico — consome as chaves CHART-*)"
    - "Plano 37-05 (wiring — conecta ExplicacaoPayoff.jsx a SecaoAnalisar.jsx/SecaoComparar.jsx)"
tech-stack:
  added: []
  patterns:
    - "Fonte única de formatação (formatarRazao) importada por dois consumidores, nunca reformatada inline — mitigação estrutural de T-37-04/EXPL-03"
    - "Componente puro + função pura exportada à parte (montarTexto) para ser testável sem DOM/render, mesmo padrão de estruturaParaPayoff.js"
    - "Hook de módulo ESM (node:module register()) para permitir node puro executar .jsx real em teste — infra nova, documentada como deviation"
key-files:
  created:
    - web/src/opcoes/ExplicacaoPayoff.jsx
    - web/tests/test_explicacao_payoff.mjs
    - web/tests/_jsx_loader.mjs
  modified:
    - web/src/copy.js
    - web/src/opcoes/uiOpcoes.jsx
decisions:
  - "formatarRazao() sem optional chaining (razao.valor/razao.motivo, guard `if (!razao) return \"—\"` explícito) para preservar os literais que o guardião pré-existente test_opcoes_analisar_ui.mjs já trancava no fonte de uiOpcoes.jsx"
  - "opcoesHojeCarregando não criado (UI-SPEC propunha), por decisão explícita do 37-02-PLAN.md: arquitetura síncrona do Plano 37-03 nunca teria consumidor para essa chave"
  - "montarTexto interpola {de}/{ate}/{spot} via replace literal nos templates de copy — nunca calcula/arredonda o número, só formata (fmt já existente em uiOpcoes.jsx)"
metrics:
  duration: "sessão única, sem timestamp de início capturado no arranque"
  completed: 2026-09-22
---

# Phase 37 Plan 02: Copy CHART/EXPL + ExplicacaoPayoff.jsx (componente puro) Summary

Camada explicativa determinística do payoff (EXPL-01/02/03): 19 chaves novas
de copy (`web/src/copy.js`), `formatarRazao()` extraída como fonte única da
razão ganho/perda (`web/src/opcoes/uiOpcoes.jsx`), e `ExplicacaoPayoff.jsx`
— componente React puro, zero I/O — que descreve todos os segmentos da
curva de payoff em português leigo, o segmento do spot sempre primeiro.

## O que foi entregue

**Task 1 — copy.js.** 8 chaves não-templated (eixo zero, ajuda de lote,
kickers "No vencimento"/"Hoje · valor de mercado", perda ilimitada curta,
prefixo do eixo, título "Como ler esta estrutura") + 11 templates de frase
EXPL-01/02/03 (segmento-posição × inclinação, redação literal do
`37-UI-SPEC.md` §3) — idênticas nos dois modos (Estudo/Operador), 19 chaves
× 2 = 38 linhas novas. D-04: `curadoriaRazaoRotulo` deixou de ler como
resultado financeiro ("prêmio sobre perda máxima"/"prêmio / perda máxima")
e passou a se identificar como pontuação de ranking — fecha a confusão
confirmada em produção com `RazaoGanhoPerda` (o mesmo bug que EXPL-03
nomeia, na tela de curadoria).

**Task 2 — formatarRazao() + ExplicacaoPayoff.jsx (TDD).** `formatarRazao
(razao)` extraída de dentro de `RazaoGanhoPerda` (era a expressão inline
`"1 : " + fmt(razao.valor)`), exportada de `uiOpcoes.jsx`; `RazaoGanhoPerda`
passou a chamá-la nos dois ramos (numérico e motivo) em vez de repetir a
lógica. `ExplicacaoPayoff.jsx` (novo): componente puro que importa `Kicker`/
`Aviso`/`formatarRazao` de `uiOpcoes.jsx`, com `montarTexto(segmentos, spot,
razao, cp)` exportado à parte para ser testável sem render. Regra de
prioridade em `montarTexto`: platô > direção; dentro de cada família, cauda
(`ate: null`) > finito — um segmento em cauda com inclinação positiva/
negativa NUNCA usa o template finito, mesmo sendo o segmento do spot.

Ainda **sem consumidor real** — nenhuma tela chama `ExplicacaoPayoff` nem lê
as chaves `opcoesExplic*`/`opcoesHoje*`/`opcoesNoVencimento*` (wiring é o
Plano 37-05, D-09 do `37-CONTEXT.md`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — blocking issue] `node` puro não consegue importar `.jsx`, mesmo sem sintaxe JSX**
- **Encontrado em:** Task 2, ao escrever `test_explicacao_payoff.mjs`
  (RED). O plano pedia `importa montarTexto de ExplicacaoPayoff.jsx e
  formatarRazao de uiOpcoes.jsx` via `node` puro (sem build, mesmo padrão
  de `test_estrutura_para_payoff.mjs`).
- **Achado:** confirmado empiricamente — `node -e "import('./uiOpcoes.jsx')"`
  falha com `Unknown file extension ".jsx"` mesmo em arquivo cuja função
  alvo (`formatarRazao`) não tem sintaxe JSX nenhuma. A falha é de
  EXTENSÃO no resolvedor ESM do Node, não de conteúdo — nenhum dos 139
  testes `.mjs` existentes importa um `.jsx` de verdade (o padrão
  dominante da casa é inspeção estática de fonte via `readFileSync`+regex;
  o único precedente de import real, `estruturaParaPayoff.js`, é
  deliberadamente um `.js` puro).
- **Opções avaliadas:** (a) mover a lógica pura para um `.js` espelho —
  rejeitada: um acceptance criterion do próprio plano exige que a
  expressão `"1 : " + fmt(razao.valor)` apareça exatamente 1 vez em
  `uiOpcoes.jsx`; duplicá-la num `.js` de teste reintroduziria a classe de
  bug EXPL-03 que este plano existe para fechar (duas fontes formatando o
  mesmo número). (b) hook de módulo ESM (`node:module` `register()`) que
  transforma `.jsx`→JS via `esbuild` (dependência já transitiva do Vite,
  nenhuma dependência nova) só para quem importa um `.jsx` — escolhida.
- **Fix:** `web/tests/_jsx_loader.mjs` (novo, não listado no
  `files_modified` do plano) — hook `load()` que intercepta só URLs
  `.jsx`, delega ao `esbuild.transformSync` (`jsx: "automatic"`, mesmo
  runtime que `@vitejs/plugin-react` usa por default) e devolve o módulo
  transformado. Registrado só dentro de `test_explicacao_payoff.mjs`
  (`register("./_jsx_loader.mjs", import.meta.url)`), sem tocar
  `scripts/executar.sh` nem nenhum outro teste.
- **Verificado:** `node web/tests/test_explicacao_payoff.mjs` roda como
  `node` puro, exit 0, dentro de `bash scripts/executar.sh --testes`
  (mesmo loop `node "${t#web/}"` de todos os outros 139 testes).
- **Commit:** `73a6297` (RED, hook criado junto do teste).

**2. [Rule 1 — bug que eu mesmo introduzi] `formatarRazao()` com optional chaining quebrou guardião pré-existente**
- **Encontrado em:** Task 2, GREEN, ao rodar a suíte canônica completa
  (não o teste novo isolado — `test_explicacao_payoff.mjs` sozinho
  passava com a versão quebrada).
- **Issue:** a primeira implementação usava `ehNum(razao?.valor)` e
  `razao?.motivo` (optional chaining, para tolerar `formatarRazao(undefined)`
  sem lançar). `web/tests/test_opcoes_analisar_ui.mjs` (guardião da Fase
  24/33, fora do escopo direto deste plano) trava por regex que exige os
  literais `razao.motivo` e `ehNum(razao.valor)` — SEM `?.` — em algum
  lugar do fonte de `uiOpcoes.jsx`. `razao?.valor` não contém a
  substring contígua `razao.valor` (o `?` quebra a sequência de
  caracteres), então o guardião passou a reprovar.
- **Fix:** reescrito sem optional chaining — `if (!razao) return "—"; return
  ehNum(razao.valor) ? ... : (razao.motivo || "—");` — preserva os dois
  literais e mantém o mesmo comportamento (inclusive `formatarRazao(undefined)
  === "—"`, testado).
- **Arquivo:** `web/src/opcoes/uiOpcoes.jsx`.
- **Commit:** `f91a69d`.

## Guardrail CLAUDE.md aplicado

Nenhuma alteração toca cálculo de carteira/preço/saldo — `ExplicacaoPayoff`
é apresentação pura sobre `segmentos`/`spot`/`razao` já calculados a
montante (Fase 36/backend); `montarTexto` só interpola strings (`replace`),
nunca faz aritmética (confirmado por `grep`/leitura direta, nenhuma
operação `*`/`/`/`+`/`-` sobre `seg.de`/`seg.ate`/`spot`/`razao.valor`
exceto o `ehNum(razao.valor)` que é uma checagem de tipo, não conta). Zero
palavra do vocabulário técnico banido (strike/prêmio/delta/theta/
volatilidade implícita/exercício/rolagem/ITM/OTM/ATM/perna) em nenhum
template de copy nem no texto composto — guardião estático + runtime em
`test_explicacao_payoff.mjs`.

## Verificação

- `node web/tests/test_explicacao_payoff.mjs` — exit 0 (25 asserções)
- `bash scripts/executar.sh --testes` (fora do sandbox, TLS bloqueado
  dentro dele) — **2968 pytest passed + 5 skipped + 3 xfailed**, TODOS os
  `.mjs` (incluindo `test_estrutura_para_payoff.mjs`,
  `test_payoff_responsivo.mjs`, `test_opcoes_analisar_ui.mjs`) OK, exit 0
- `npx vite build` (dentro de `web/`) — exit 0, 111 módulos, sem erro de
  sintaxe

## Known Stubs

Nenhum. `ExplicacaoPayoff.jsx` é um componente completo e funcional — só
não tem consumidor ainda (por desenho do plano, wiring é o Plano 37-05).

## Threat Flags

Nenhum achado de superfície nova fora do que o `<threat_model>` do plano já
cobria (T-37-03/T-37-04) — nenhum endpoint, rota de auth ou acesso a
arquivo novo; só texto derivado de props já validadas a montante.

## Self-Check: PASSED

- `web/src/opcoes/ExplicacaoPayoff.jsx` — FOUND
- `web/tests/test_explicacao_payoff.mjs` — FOUND
- `web/tests/_jsx_loader.mjs` — FOUND
- Commit `7c9fbb7` (feat, copy.js) — FOUND em `git log --oneline --all`
- Commit `73a6297` (test, RED) — FOUND
- Commit `f91a69d` (feat, GREEN) — FOUND
