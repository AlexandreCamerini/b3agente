---
phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis
plan: 05
subsystem: web/opcoes (SecaoAnalisar.jsx, SecaoComparar.jsx)
tags: [payoff, wiring, opcoes, checkpoint-humano, publicacao]

# Dependency graph
requires:
  - phase: 37-01
    provides: "dominio/segmentos anexados a proposta()/possibilidades() em options_mcp_api.py"
  - phase: 37-02
    provides: "ExplicacaoPayoff.jsx (componente puro, EXPL-01/02/03) e chaves de copy"
  - phase: 37-03
    provides: "valorHoje no envelope de proposta()/possibilidades(), gate do 1o candidato"
  - phase: 37-04
    provides: "PayoffChart.jsx aceita dominio/segmentos/valorHoje, geometria corrigida (CHART-01/02/03)"
provides:
  - "SecaoAnalisar.jsx e SecaoComparar.jsx passam dominio/segmentos/valorHoje ao PayoffChart e renderizam ExplicacaoPayoff — CHART-01..05/EXPL-01..03 observáveis de ponta a ponta num app rodando (Task 1)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Passthrough puro de props já validadas pelos planos 37-01/37-02/37-03/37-04 — zero lógica de índice/gate reimplementada no front (T-37-10: item.valorHoje repassado como está, o backend já decide quem recebe a chave)"

key-files:
  created: []
  modified:
    - web/src/opcoes/SecaoAnalisar.jsx
    - web/src/opcoes/SecaoComparar.jsx

key-decisions:
  - "SecaoComparar.jsx não reintroduz gate por índice (i === 0) para o bloco Hoje — a fonte única do gate é o backend (chave item.valorHoje ausente vs. presente), conforme D-09/T-37-10 do 37-05-PLAN.md"
  - "CuradoriaEstruturas.jsx não foi tocado nesta task (D-09) — confirmado por git diff --stat, recebe a correção de geometria do 37-04 de graça via fallback local em PayoffChart.jsx, sem os blocos novos"

requirements-completed: [CHART-01, CHART-02, CHART-03, CHART-04, CHART-05, EXPL-01, EXPL-02, EXPL-03]

# Metrics
duration: "~35min (Task 1) + checkpoint humano (Task 2, aprovado com ressalva) + ~15min (Task 3, bump/publicação)"
completed: "2026-09-22"
---

# Phase 37 Plan 05: Wiring do gráfico/explicação em Analisar e Comparar + checkpoint humano + publicação Summary

**`SecaoAnalisar.jsx`/`SecaoComparar.jsx` passam a passar `dominio`/`segmentos`/`valorHoje` ao `PayoffChart` corrigido (Plano 37-04) e a renderizar `<ExplicacaoPayoff/>` (Plano 37-02) — a onda de fechamento que torna CHART-01..05/EXPL-01..03 observáveis de ponta a ponta nos dois consumidores reais que um usuário vê, publicada em produção com carimbo `F10-20260922-01`.**

## Status desta entrega

**COMPLETA — as 3 tasks rodaram: Task 1 (wiring, commit `e62e231`), Task 2 (checkpoint humano, aprovado pelo Alex COM RESSALVA — ver seção própria abaixo, não foi uma verificação visual ao vivo completa) e Task 3 (bump + publicação, commit `d25a2a8`, confirmado em produção por HTTP). Este SUMMARY foi escrito em duas etapas por dois agentes executores diferentes (Task 1 por um, Task 2/3 por uma continuação fresca depois do checkpoint) — mantido honesto sobre essa descontinuidade.

## Performance

- **Duration:** ~35min (Task 1) + checkpoint humano (Task 2) + ~15min (Task 3)
- **Tasks:** 3/3 completas
- **Files modified:** 2 (Task 1) + 3 (Task 3: `web/src/version.js`, `server/app/main.py`, `server/web_dist`)

## Task 2 — checkpoint humano: resolução COM RESSALVA (registro honesto)

**Resposta do Alex:** "Aprovado com base no automático + revisão de código já feita."

Isto é uma aprovação real e explícita do dono da fase — mas NÃO é o que o roteiro de 7 passos da Task 2 pedia (verificação visual ao vivo do gráfico/explicação com dados reais de mercado, item a item). Registro do que de fato aconteceu, sem maquiar:

- O orquestrador subiu um backend de desenvolvimento local + instalou um build iOS fresco no iPhone físico do Alex, apontado para esse backend local (`http://192.168.0.36:8787`).
- Esse backend local **não tinha nenhuma credencial de dado de mercado/MCP configurada** (sem `BRAPI_TOKEN`, sem `BOLSAI_API_KEY` — confirmado por inspeção do ambiente do processo em execução).
- Resultado: a aba Opções não conseguia alcançar o serviço MCP de opções de jeito nenhum ("nada funciona em opções") — o gráfico/explicação corrigidos NÃO puderam ser confirmados visualmente com números reais no aparelho.
- Diante disso, o orquestrador perguntou explicitamente ao Alex como fechar o checkpoint. Ele escolheu aprovar com base na evidência automatizada já colhida (suíte canônica verde 3x ao longo das ondas, `npx vite build` verde, `gsd-plan-checker` com VERIFICATION PASSED duas vezes no planejamento, e a própria revisão de código linha a linha repetida pelo orquestrador durante a execução) em vez de esperar para fornecer credenciais e rodar a verificação visual completa.

**Isto NÃO bloqueia a Task 3** — é uma aprovação real e explícita do dono da fase, registrada nesta conversa, exatamente como o guardrail do repositório exige ("checkpoint bloqueante segura a publicação da FASE INTEIRA... só roda depois do 'aprovado' explícito"). Mas fica registrado com honestidade: **o "aprovado" se apoiou em evidência automatizada + revisão de código, não numa confirmação visual ao vivo do gráfico corrigido rodando com dado real.** Uma verificação visual em produção (com dado real de mercado) depois desta publicação continua sendo uma boa ideia para o Alex fazer quando quiser — não bloqueia nada, é uma lacuna honesta a registrar, não uma pendência que impede o fechamento da fase.

Esta mesma ressalva foi transcrita, verbatim em espírito, no comentário do `SERVER_BUILD_ID` em `server/app/main.py` (linha ~1662) — não fica só neste SUMMARY.

## Accomplishments (Task 1)

- `SecaoAnalisar.jsx`: `import ExplicacaoPayoff from "./ExplicacaoPayoff.jsx"`; `<PayoffChart>` ganha `dominio={proposta.dados.dominio}`, `segmentos={proposta.dados.segmentos}`, `valorHoje={proposta.dados.valorHoje}`; `<ExplicacaoPayoff segmentos=... spot=... razao=... cp={cp} />` renderizado logo após `<RazaoGanhoPerda>`, antes de `<Pernas>`
- `SecaoComparar.jsx`: mesmo import; dentro do `.map((item) => ...)`, `<PayoffChart>` ganha as mesmas 3 props lendo de `item.*`; `<ExplicacaoPayoff>` renderizado após `<RazaoGanhoPerda>`, antes de `<Cenarios>` — sem nenhuma lógica de índice própria (o backend já decide, via presença/ausência de `item.valorHoje`, quem recebe o bloco Hoje)
- `CuradoriaEstruturas.jsx` confirmado intocado por `git diff --stat` (D-09)

## Accomplishments (Task 3)

- `origin/main` já era ancestral do HEAD local (`33f326f`) — nenhum merge real necessário, só confirmado (`git merge-base --is-ancestor`)
- `bash scripts/bump.sh` — `BUILD_ID` `F10-20260921-01` → `F10-20260922-01` em `web/src/version.js`
- `bash scripts/publicar-web.sh` — `npm ci && npx vite build` (113 módulos), `server/web_dist` regenerado, `SERVER_BUILD_ID` sincronizado automaticamente
- Comentário do `SERVER_BUILD_ID` reescrito à mão: novo parágrafo resume esta fase (gráfico corrigido, explicação por segmento, bloco Hoje só no 1o candidato, rótulo "Pontuação de curadoria", a ressalva do checkpoint da Task 2) seguido de `HISTORICO (entrega anterior, F10-20260921-01): ` + o texto integral e verbatim do comentário anterior (Fase 35 + toda a cadeia de HISTORICO que ele já carregava) — nada foi reescrito ou resumido do texto antigo, só prefixado
- `bash scripts/executar.sh --testes` repetida DEPOIS do bump — **2973 pytest passed / 5 skipped / 3 xfailed / 0 failed** + **156/156 `.mjs`**, exit 0
- Commit `d25a2a8`, push em `v2/interacao-estrutural` E `origin/main` — fast-forward confirmado (`33f326f..d25a2a8` nos dois, `HEAD == origin/main == origin/v2/interacao-estrutural`)
- `curl https://boris.semente.dev/api/health` — dois carimbos observados durante o redeploy do Railway: `F10-20260921-01` por ~119s, depois `F10-20260922-01` confirmado em ~134s (2min14s) de polling

## Task Commits

1. **Task 1: wiring de dominio/segmentos/valorHoje + ExplicacaoPayoff** - `e62e231` (feat)
2. **Task 3: bump, publicação e confirmação em produção** - `d25a2a8` (feat)

## Files Created/Modified

- `web/src/opcoes/SecaoAnalisar.jsx` — import de `ExplicacaoPayoff`; props novas no `PayoffChart`; `<ExplicacaoPayoff>` renderizado
- `web/src/opcoes/SecaoComparar.jsx` — idem, por item da lista de possibilidades
- `web/src/version.js` — `BUILD_ID` → `F10-20260922-01`
- `server/app/main.py` — `SERVER_BUILD_ID` → `F10-20260922-01`, comentário reescrito com resumo da fase + histórico preservado
- `server/web_dist` — regenerado por `publicar-web.sh` (dist buildado com o carimbo novo)

## Decisions Made

Ver `key-decisions` no frontmatter. Adicional (Task 3): checkpoint humano fechado com aprovação qualificada do Alex — ver seção própria acima; decisão dele, não inferência do executor.

## Deviations from Plan

Nenhuma no conteúdo das Tasks 1 e 3 — ambas executadas exatamente como especificadas (Task 1: passthrough puro de props, sem transformação, sem gate por índice reintroduzido; Task 3: sequência merge→bump→publicar→suíte→commit→push→confirmação HTTP idêntica ao precedente de `35-03-PLAN.md`). A única divergência real está documentada na seção "Task 2 — checkpoint humano" acima: a verificação visual ao vivo prevista na Task 2 não pôde ser concluída por falta de credenciais de dados no backend local usado na tentativa — o Alex aprovou explicitamente com base em evidência alternativa, decisão dele, registrada, não uma correção silenciosa do executor.

## Issues Encountered

- **Falsos-positivos de sandbox na primeira rodada da suíte canônica**: `bash scripts/executar.sh --testes` dentro do sandbox padrão reportou 27 falhas de backend (`test_benchmark_ibov.py`, `test_yahoo_*`, `test_fase3_kill_switch_duracao.py`, etc.), todas com `PermissionError` — padrão já documentado no projeto ("sandbox mente", memória `worktree-test-setup.md`). Rerodada fora do sandbox (`dangerouslyDisableSandbox: true`) confirmou **2973 pytest passed, 0 failed** + **156/156 `.mjs`**, idêntico à baseline do Plano 37-04. Nenhuma das 27 falhas tem relação com os 2 arquivos desta task (ambos puramente frontend/JSX).
- **Backend/Vite não sobem com bind em `0.0.0.0` dentro do sandbox padrão** (`EPERM`/`operation not permitted` ao dar `listen`) — mesma classe de restrição de rede do sandbox, não falha de configuração do projeto. Resolvido subindo os dois com `dangerouslyDisableSandbox: true`, confirmado por HTTP antes de apresentar o roteiro da Task 2 (ver seção Verificação abaixo).

## User Setup Required

Nenhum novo — o checkpoint da Task 2 pede só a leitura visual do Alex, sem nenhuma configuração.

## Known Stubs

Nenhum. As props novas (`dominio`/`segmentos`/`valorHoje`) são passthrough puro de dados já produzidos pelo backend (37-01/37-03); `ExplicacaoPayoff` é componente puro já testado isoladamente (37-02).

## Threat Flags

Nenhum achado de superfície nova. T-37-10 (gate de índice divergente em `SecaoComparar.jsx`) mitigado por desenho: nenhuma lógica de índice foi adicionada, `item.valorHoje` é repassado como está.

## Verificação (Task 1)

- `git diff --stat` (contra o HEAD anterior a este plano): `CuradoriaEstruturas.jsx` NÃO aparece — confirmado
- `grep -n "import ExplicacaoPayoff"` / `grep -n "dominio={"` / `grep -n "<ExplicacaoPayoff"` — presentes nos dois arquivos
- `cd web && npx vite build` — exit 0, 113 módulos, sem erro de sintaxe
- `bash scripts/executar.sh --testes` fora do sandbox — **2973 pytest passed / 5 skipped / 3 xfailed / 0 failed** + **156/156 `.mjs`**, exit 0
- Backend (`uvicorn app.main:app --host 0.0.0.0 --port 8787`) e Vite (`npm run dev -- --host --port 5174`) subidos DIRETAMENTE (não pelo launcher `scripts/executar.sh` sem argumentos, que trava neste host — achado de ambiente já registrado em STATE.md), confirmados por HTTP:
  - `curl http://localhost:8787/api/health` → `{"ok":true,"build":"F10-20260921-01"}` (carimbo ANTERIOR ao bump — esperado, bump só na Task 3)
  - `curl http://localhost:5174/` → HTTP 200
  - `curl http://localhost:5174/api/health` → `{"ok":true,"build":"F10-20260921-01"}` (proxy dev do Vite para o backend confirmado funcionando)

## Verificação (Task 3)

- `grep -c 'BUILD_ID = "F10-' web/src/version.js` → 1, `F10-20260922-01` (data de hoje, sufixo -01)
- `grep -o 'SERVER_BUILD_ID = "[^"]*"' server/app/main.py` → `F10-20260922-01`, bate exatamente com `BUILD_ID`
- Comentário do `SERVER_BUILD_ID` contém o resumo desta fase E `HISTORICO (entrega anterior, F10-20260921-01):` seguido do texto anterior preservado verbatim
- `bash scripts/executar.sh --testes` fora do sandbox, DEPOIS do bump — **2973 pytest passed / 5 skipped / 3 xfailed / 0 failed** + **156/156 `.mjs`**, exit 0
- `git log --oneline -1` → `d25a2a8`; `git status --short` limpo (só a modificação pré-existente e fora de escopo de `web/package-lock.json`, já presente antes desta sessão começar); `HEAD == origin/main == origin/v2/interacao-estrutural` (fast-forward `33f326f..d25a2a8` nos dois pushes)
- `curl -s https://boris.semente.dev/api/health` — carimbos observados: `F10-20260921-01` de `+0s` a `+94s`, resposta vazia em `+119s` (Railway reiniciando o processo), `F10-20260922-01` confirmado em `+134s`
- `git diff .planning/STATE.md .planning/ROADMAP.md` — vazio (0 linhas), documentos de planejamento intocados pelo executor

## Next Phase Readiness

- Fase 37 completa: 3/3 tasks do plano 05, publicada em produção com carimbo `F10-20260922-01`, confirmado por HTTP.
- **Pendência honesta, não bloqueante:** a verificação visual ao vivo do gráfico/explicação corrigidos com dado real de mercado (roteiro de 7 passos da Task 2) não foi concluída — só a evidência automatizada + revisão de código. Uma passada visual em produção (`boris.semente.dev`, dado real, sem a limitação de credenciais do backend local) fica registrada como recomendação para o Alex fazer quando quiser, não como algo que impede o fechamento da fase.
- STATE.md/ROADMAP.md ainda não atualizados por este executor — por desenho, o orquestrador fecha esses documentos à mão após esta onda (guardrail do repositório).

---
*Phase: 37-gr-fico-de-payoff-e-explica-o-confi-veis*
*Status: COMPLETA — publicada em produção (F10-20260922-01), checkpoint humano aprovado com ressalva registrada*

## Self-Check: PASSED

- FOUND: `.planning/phases/37-gr-fico-de-payoff-e-explica-o-confi-veis/37-05-SUMMARY.md`
- FOUND: `e62e231` (Task 1)
- FOUND: `d25a2a8` (Task 3)
- CONFIRMED: `curl https://boris.semente.dev/api/health` retorna `F10-20260922-01`
