---
gsd_state_version: 1.0
milestone: v1.8
milestone_name: Didática ampliada + continuidade da aba Opções
status: executing
last_updated: "2026-09-23T06:20:00.000Z"
last_activity: 2026-09-23
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 6
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-20)

**Core value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.
**Current focus:** Milestone v1.8 (Didática ampliada + continuidade da aba Opções) — ROADMAP.md criado (Phases 38-40, 4/4 requirements mapeados). Fase 38 EXECUTANDO (`/gsd-execute-phase 38`, sem worktree, sequencial por onda).

## Current Position

Phase: 38 (KB Didática ampliada) — PLANEJADA, pronta para executar (não iniciada)
Plan: 38-01 a 38-06 (6 planos em 5 ondas), nenhum executado ainda
Status: `/gsd-plan-phase 38` completo (2026-09-23). Sequência: gate de UI-SPEC bloqueou a primeira tentativa (fase tem `UI hint: yes`, sem `38-UI-SPEC.md`) → `/gsd-ui-phase 38` rodado a pedido do Alex → `gsd-ui-researcher` gerou `38-UI-SPEC.md` (commit `537fd23`) → `gsd-ui-checker` aprovou 6/6 (1 FLAG não-bloqueante: `aria-label` do botão "×" de limpar busca, foco visual primário da tela) → Alex escolheu pesquisar antes de planejar → `gsd-phase-researcher` (`38-RESEARCH.md`, commit `61c6e19`, confiança HIGH) → `gsd-pattern-mapper` (`38-PATTERNS.md`, 9/9 analogs) → `gsd-planner` opus (6 planos, commit `e7cf22a`, também atualizou ROADMAP.md) → `gsd-plan-checker` VERIFICATION PASSED (0 blockers, 1 warning cosmético: Open Questions do RESEARCH sem sufixo `(RESOLVED)`, ambas de fato resolvidas nos planos). Gates de cobertura: 2/2 requisitos (KB-01, KB-02) e 8/8 decisões do CONTEXT.md.

**Achado central da pesquisa:** 3 dos 4 `vid` propostos no UI-SPEC (`mkt-carteira-simulada`, `ind-rsi`, `mkt-opcao`) NÃO existem em `conceitos.CONCEITOS` — a rota atual `POST /api/conceito/{cid}` daria 404 neles hoje; só `confluencia` existe nos dois catálogos. Fix: discriminador explícito `fonte: "conceito"|"kb"` na `ConceitoSheet`, default `"conceito"`, sem fallback silencioso por 404. `kb.formatar()` não tem campo `titulo` — vira tarefa própria (~74 verbetes × 2 modos ≈ 148 strings novas sob as regras do `didatica-boris`), não um detalhe escondido dentro de "ligar a ponte".

**Onde os planos se afastaram da pesquisa/UI-SPEC (razão declarada em cada plano):** ação nova `A.abrirVerbeteKb(vid)` em vez de 3º parâmetro em `abrirVerbete` (guardião `test_concentracao_carteira.mjs` trava a assinatura literal); busca por substring em vez de palavra inteira (D-02 trava só o `kb.buscar()` do backend, esta tela não o chama); tile "Glossário" no grupo "Ajuda", não em "IA e desempenho" (glossário não é IA); módulo compartilhado chamado `entendimento.jsx`, não `didatica.jsx` (colidiria com o estado/prop `didatica` já existente em `App.jsx`).

**D-08 (qual verbete cada aba abre) segue como decisão bloqueante**, checkpoint no início do 38-05 — nenhum link "saiba mais" é escrito antes da resposta do Alex. Proposta: Acompanhar→`mkt-carteira-simulada`, Radar→`confluencia`, Watchlist→`ind-rsi`, Opções→`mkt-opcao` (alternativas no próprio checkpoint: Acompanhar→`estado-armado`, Watchlist→`familia-tendencia`).

**Risco declarado, não resolvido:** para cumprir D-08 ao pé da letra (isolamento `OpcoesScreen.jsx`↔`App.jsx`, "ambos importam do módulo novo"), o "saiba mais" de Opções monta uma cópia local da folha de conceito em vez de reusar a folha global já em produção — o botão flutuante do Boris provavelmente não se esconde sob essa folha local. Declarado no 38-05, conferido no checkpoint humano do 38-06.

**Onda 1 completa (38-01, 38-02) — 2026-09-23, `/gsd-execute-phase 38` sem worktree, sequencial:**
- `38-01` (backend, commits `66f7d1e`/`6f24e00`/`46a19ad`): 65 títulos autorados + 18 derivados, `FAMILIAS`, `catalogo_formatado()`, rota `GET /api/kb/catalogo`. 65 testes-alvo + suíte completa fora do sandbox: 2987 pytest, 0 falhas relevantes (27 falhas dentro do sandbox são artefato de rede/mocking pré-existente, nenhuma toca `kb.py`/`main.py`).
- `38-02` (frontend, commits `bbab82e`/`5f47f18`/`4471a49`): `SetorAlvo`/`ConceitoSheet`/`AssistenteBox`/`AiNote` extraídos verbatim para `web/src/entendimento.jsx`; 6 guardiões reapontados + 1 novo (`test_entendimento_modulo.mjs`). **Defeito real achado e corrigido pela própria extração:** a asserção de `zIndex:86` em `test_conceito_ui.mjs` vinha passando silenciosamente contra o componente ERRADO (`PetSheet`, coincidência de zIndex) desde antes desta fase — reapontada pra testar `ConceitoSheet` de verdade. `npx vite build` limpo. Suíte fora do sandbox: 2987 pytest + 156/157 `.mjs` (só a falha ambiental conhecida, `test_ios_assets.mjs`).

Ambos os executores instruídos a não tocar STATE.md/ROADMAP.md; spot-check do orquestrador confirmou os 2 SUMMARY.md e os 6 commits antes de prosseguir pra Onda 2 (38-03).

**Guardrail aplicado:** mutadores de estado do gsd-sdk não foram chamados (`state.planned-phase`/`state.begin-phase` etc.) — este STATE.md foi editado à mão; `roadmap.annotate-dependencies` (não é `state.*`) rodou e confirmou `updated: false` (planner já tinha anotado o ROADMAP.md).

**Próximo passo:** Onda 2 — `38-03` (ponte kb×conceito).

## Posição anterior nesta fase (Fase 36, fechada)

Phase: 36 (Motor de Payoff Genérico) — **FECHADA (2/2 ondas)** — histórico, superado pela entrada acima
Plan: 36-01 ✓ | 36-02 ✓ (sem checkpoint humano, sem publicação — backend puro, `opcoes_payoff.py` ainda sem consumidor novo; a Fase 37 é quem publica)
Status: `/gsd-execute-phase 36` completo (2026-09-21), sem worktree (`workflow.use_worktrees=false`), executor sequencial por onda.
Last activity: 2026-09-21 — `36-02` fechou a fase: `dominio_da_curva()` (D-05, margem 12%/4%/15%/10%, exclui o strike=0.0 da perna ACAO, spot sempre dentro) e `segmentos_da_curva()` (D-06, corta só nos strikes, cauda com `ate` nulo) declaradas ao lado de `perfil_da_estrutura`; caso golden travado como regressão nomeada única (`test_golden_trava_de_alta_49_17_49_67_debito_025`, as 5 propriedades de PAYOFF-03 num só teste); auditoria de PAYOFF-01 (`grep` confirma zero ramificação por nome de estratégia no módulo). 65 testes no arquivo (48+17 novos). Suíte canônica: 2960 pytest + 154/154 `.mjs`. Nada publicado. Commits `31e7db7`/`6317698`/`0c0c27f`/`5fd9f86`.

**Contexto do planejamento:** `/gsd-discuss-phase 36` → `gsd-pattern-mapper` → `gsd-planner` opus (2 planos) → `gsd-plan-checker` (VERIFICATION PASSED, 0 blockers). Achado central: `server/app/opcoes_payoff.py` já era um motor genérico em produção desde a Fase 15 — esta fase ESTENDEU (D-01), nunca recriou.

## Posição anterior nesta fase (Fase 35, fechada)

Phase: 35 (Jornada Guiada do Workspace) — **FECHADA (3/3 ondas + checkpoint humano + publicação)** — histórico, superado pela entrada acima
Plan: 35-01 ✓ | 35-02 ✓ | 35-03 ✓ (checkpoint aprovado ao vivo — 8 leituras de contraste nas 4 combinações tema×modo — publicação confirmada em produção)
Status: `/gsd-execute-phase 35` completo nesta sessão (2026-09-21), sem worktree (`workflow.use_worktrees=false`), executor sequencial por onda. Cada executor foi instruído a NÃO tocar STATE.md/ROADMAP.md — o orquestrador edita à mão após cada onda, guardrail do repositório.
Last activity: 2026-09-21 — `35-03` fechou a fase: (1) checkpoint humano do roteiro de 8 itens aprovado AO VIVO pelo Alex, incluindo as 8 leituras de contraste (rótulo + subtexto de custo, 4 combinações tema×modo — claro/escuro × Estudo/Operador), fechando o risco aberto de D-07; achado de ambiente registrado (não do produto): `bash scripts/executar.sh` sozinho trava neste host por `lsof`/`ps` travados — contornado subindo backend/Vite diretamente; (2) publicação: `bump.sh` → `F10-20260921-01` → `publicar-web.sh` → comentário do `SERVER_BUILD_ID` reescrito à mão (histórico da entrega anterior preservado como "HISTORICO") → suíte canônica pós-bump confirmada (2923 pytest + guardião novo verde) → push em `v2/interacao-estrutural` E `origin/main` (fast-forward confirmado, `HEAD == origin/main`) → `/api/health` confirmado servindo o carimbo novo após ~3-4min de redeploy do Railway (dois carimbos observados: `F10-20260920-01` até 17:47, `F10-20260921-01` a partir de 17:47:36). Nenhuma PR envolvida — publicação é push direto (confirmado via `gh pr list`, zero PRs abertas neste repo).

**Onda 2 completa (35-02), resumo preservado:** os 3 CTAs da jornada (Ler no serviço de opções, Montar estrutura, Ver possibilidades) passaram do estilo neutro genérico a `BOTAO_PRIMARIO` (preenchimento sólido `T.accent` + texto `T.onAccent`, nunca `#fff` literal — reprovava AA em até 4 combinações tema×modo); marca `✓` neutra aparece nos dois re-clicáveis quando há resultado com conteúdo, sem nunca desabilitar o botão. Fold-in real achado pela própria varredura de tokens desta fase: `SecaoVigias.jsx` referenciava `T.bgPanel` fora do array `TOKENS` desde a Fase 33 — chip de vigia não selecionado renderizava sem fundo, em silêncio; corrigido. Guardião estendido para 70 asserções (24+46) com 4 provas negativas reais. **Achado de qualidade, não bug:** os helpers neutros `BOTAO` (em `SecaoComparar.jsx`) e `desabilitado` (em `SecaoAnalisar.jsx`/`SecaoComparar.jsx`) ficaram sem consumidor — cada arquivo tinha só 1 botão, promovido a `BOTAO_PRIMARIO`/`desabilitadoPrimario` por D-04; plano proíbe renomear/reescrever, então ficam declarados e mortos, candidatos a limpeza futura, não bloqueiam nada. Commits `b76f5d4`/`e3934fa`/`7825845`/`4c9a6c2`.

**Pendências que sobrevivem ao fechamento da Fase 35, sem bloquear nada:**

1. App iOS/TestFlight ainda não recebe esta entrega — bundle local, sem `server.url`; decisão do Alex quando quiser rodar `scripts/distribuir-iphone.sh --testflight` ou `--xcode`.
2. Achado de ambiente (não do produto): `bash scripts/executar.sh` sozinho trava neste host (lsof/ps travados) — usar backend+Vite diretos como contorno até investigar a causa.
3. Helpers `BOTAO`/`desabilitado` mortos em 2 arquivos (achado do 35-02) — candidatos a limpeza futura.
4. Todas as pendências herdadas do v1.6 (App iOS antigo, backlog B2, todos de bookkeeping, `.env.local` ausente, todo de prioridade alta MCP) continuam abertas, listadas na entrada anterior do STATE.md.

**Contexto do planejamento (sessão anterior, mesmo dia):** `/gsd-discuss-phase 35` (com 2 agentes especializados a pedido do Alex — UX Researcher + UI Designer) → `/gsd-ui-phase 35` (UI-SPEC aprovado 6/6 após 1 revisão de tipografia/espaçamento assinada pelo Alex) → `gsd-pattern-mapper` (5/5 analogs) → `gsd-planner` opus (3 planos em 3 ondas) → `gsd-plan-checker` (VERIFICATION PASSED, 0 blockers, 2 achados adversariais do planner conferidos contra o código real: bug real em `SecaoVigias.jsx` (`T.bgPanel` undefined desde a Fase 33) e armadilha real de fatiamento no guardião da Fase 34).

**Próximo passo:** `/gsd-execute-phase 35` continua — Onda 2 (35-02, `BOTAO_PRIMARIO`/`T.onAccent` nos 3 CTAs).

**Pendências herdadas do v1.6, ainda abertas (não bloqueiam o v1.7):**

1. App iOS não recebeu a navegação nova — só chega num build de TestFlight, decisão do Alex.
2. Backlog B2 (estado do workspace não sobrevive à troca de seção) — aberto por desenho (D-03 da Fase 34).
3. 2 todos já executados como fold-in na Fase 33 ainda fisicamente em `.planning/todos/pending/` (bookkeeping).
4. Avisos de lint pré-existentes em `web/src/opcoes/` — nunca bloquearam a suíte canônica.
5. `web/.env.local` ausente neste worktree — login Google falha no build local instalado no iPhone; Apple/SIWA e e-mail/senha não são afetados.
6. Todo de prioridade alta `revisao-arquitetura-mcp-ecossistema-b3.md` — o Alex optou explicitamente por tratar depois, não faz parte do v1.7.

## Posição anterior nesta fase (discussão + UI-SPEC)

Phase: 35 — DISCUTIDA, UI-SPEC aprovado (histórico, superado pela entrada acima)
Status: `/gsd-plan-phase 35` tinha detectado ausência de `35-CONTEXT.md` e, seguindo o gate #1009 (AskUserQuestion não funciona aninhado), pausou e pediu pra rodar `/gsd-discuss-phase 35` como comando de topo.
Last activity: 2026-09-21 — Discuss-phase da Fase 35 completo. O Alex pediu explicitamente para trazer agentes especializados (UX Researcher + UI Designer) antes de travar decisões pontuais, em vez de responder as 4 perguntas mecânicas direto. UX Researcher (pesquisa de padrões reais de progressive disclosure/apps de trading, achou que o portão de leitura fora do carril de pills é decisão de arquitetura já fechada na Fase 27/ADR-027 Emenda 2, não descuido — e achou de graça que `SecaoSetups` fica bloqueada pelo portão sem precisar dele); UI Designer (leu o design system real do workspace + `34-UI-SPEC.md`, propôs `BOTAO_PRIMARIO` estendendo o reserved-for de `T.accent`, com precedente em produção em `CuradoriaEstruturas.jsx`). Decisões travadas: Opção A do fluxo (passo numerado só no nível porta→carril, nunca numerando Analisar/Comparar entre si), extensão aprovada do accent, risco de contraste no tema claro declarado como verificação obrigatória pendente. Opção B (carril numerado com cadeado, desloca Setups salvos) registrada como candidata futura, não descartada. Em seguida, `/gsd-ui-phase 35`: `gsd-ui-researcher` gerou o UI-SPEC (corrigiu os literais `#fff`/`color-mix` de `35-CONTEXT.md` para `T.onAccent`, com evidência WCAG computada por tema — os literais originais falhavam AA em 2-4 combinações); `gsd-ui-checker` bloqueou 2/6 dimensões na primeira rodada (Tipografia: 4 pesos sem assinatura; Espaçamento: 3px/6px sem assinatura) — o Alex aprovou explicitamente os dois reusos, anotações `developer-approved — matches existing pattern — 2026-09-21` adicionadas, re-verificado 6/6.

## Posição anterior (v1.6, arquivado — Fase 34, fechada)

Phase: 34 (Navegação hub + workspace) — EXECUTANDO, 3/4 ondas (histórico, superado pela entrada acima)
Plan: 34-01 ✓ | 34-02 ✓ | 34-03 ✓ | 34-04 pendente (checkpoint humano bloqueante — publica 33+34 juntas)
Status: `/gsd-execute-phase 34` rodando nesta sessão (2026-09-20), sem worktree (`workflow.use_worktrees=false`), executor sequencial por onda. Cada executor foi instruído a NÃO tocar STATE.md/ROADMAP.md — o orquestrador edita à mão após cada onda, guardrail do repositório (2026-09-11).
Last activity: 2026-09-20 — `34-03` completo: pill row de 3 abas (Analisar/Comparar/Setups salvos) acrescentada ao workspace; ramo 4 (Dados) da cascata passou a gatear pela aba ativa, não mais por um bloco único. Guardião estendido com 7 asserções novas + prova negativa DUPLA (NAV-05: trocar de aba não dispara fetch novo). Dois achados documentados no SUMMARY em vez de corrigidos silenciosamente ou ignorados: (1) o guardião trava a garantia só em `OpcoesScreen.jsx`, não com um check de runtime em `SecaoAnalisar.jsx` — fronteira de cobertura honesta, não lacuna; (2) `cp.opcoesAbaSetupsSalvos` diverge de propósito entre estudo ("Setups salvos") e operador ("Setups") — herdado do 34-01, mesmo padrão de tom de `opcoesSubabaOperar`. Suíte canônica idêntica à baseline. `npx vite build` verde. `App.jsx` intocado. 4 diagnósticos de lint (`PayoffChart`/`ErroDoMcp`/2×`store`) confirmados PRÉ-EXISTENTES (mesmas 2 declarações de sempre, só deslocadas de linha). Commits `7180ae4`/`c09fee7`/`8924a49`/`1172104`/`f65785f`/`9d5f570`.

Anterior — `34-02` completo: `OpcoesScreen.jsx` particiona `hubTopo` × `workspaceTopo` acima da cascata (ramos 1-2 continuam únicos, ramos 3/4 particionados por modo) — o split hub/workspace de verdade. Guardião `test_opcoes_hub_workspace_ui.mjs` estendido. **Defeito real pego pela própria disciplina de prova negativa do plano**: a primeira versão do guardião buscava marcadores da cascata (`carregando ? (`, `erro ? (`, `!ticker ? (`) no arquivo INTEIRO, batendo por engano em homônimos dentro de `SubAbaOperar` — duas asserções ficaram inertes (defeito injetado de propósito não falhou). Corrigido escopando a busca à fatia da sub-aba "Setups" antes de qualquer inércia ir pro commit; prova negativa re-rodada e confirmada, revertida. Suíte canônica idêntica à baseline: 2923 pytest + 152/153 `.mjs`. `npx vite build` verde. `App.jsx` confirmado intocado (`git diff --stat 67c7472..HEAD -- web/src/App.jsx` vazio). 3 diagnósticos de lint novos investigados e confirmados PRÉ-EXISTENTES (mesma contagem de uso antes/depois do commit — `PayoffChart`/`ErroDoMcp` importados sem uso, `store` declarado sem uso em `SubAbaOperar`, todos herdados de fases anteriores). Commits `0bf14de`/`5d686ef`/`96174ae`/`9c3ab29`.

**Contexto do planejamento (sessão anterior, mesmo dia):** `/gsd-discuss-phase 34` → `/gsd-ui-phase 34` → `/gsd-plan-phase 34`. Decisões travadas em `34-CONTEXT.md`: (D-01, EMENDADO) hub = SecaoDescobrir → SecaoVigias (listagem cross-ticker real) → seletor; SecaoSetups migra INTEIRA (lista + criação) pro workspace como 3ª aba "Setups salvos" — a leitura original de D-01 (listagem de setups no hub) era impossível: `setups` deriva só de `leitura.dados` (leitura paga, ticker-scoped), sempre vazio com `ticker=""`. Achado do planner, verificado pelo orquestrador por leitura direta, confirmado pelo Alex. (D-02) pill row do workspace com 3 abas. (D-03) estado do workspace reseta sempre ao voltar — B2 não fechado de passagem. (D-04) ordem fixa do hub. (D-05) botão de voltar vira header fixo com o ticker. UI-SPEC aprovado (6/6). `gsd-planner` (opus): 4 planos em 4 ondas sequenciais. `gsd-plan-checker`: VERIFICATION PASSED, 0 blockers. Gates de cobertura: 6/6 requisitos, 5/5 decisões. Commits `d49b2bf` → `d8556ea`/`565a08b`/`6b71e41` → `a2b0f9d` → `55594fd`/`5dc45b6` → `3f807ef` → `1272930`.

## Posição anterior (Fase 33, fechada)

Phase: 33 (Extração dos 5 jobs em componentes próprios) — **EXECUTADA e VERIFICADA — VERIFICATION PASSED (7/7)**
Plan: 33-01 ✓ | 33-02 ✓ | 33-03 ✓ | 33-04 ✓ | 33-05 ✓ (todas as 5 ondas completas)
Status: Autorizado pelo Alex a retomar ("seguir", 2026-09-20). `gsd-verifier` rodou verificação goal-backward completa por leitura do código atual (não só dos SUMMARYs) — relatório em `.planning/phases/33-extra-o-dos-5-jobs-em-componentes-pr-prios/33-VERIFICATION.md`. Não prossigo pra `/gsd-plan-phase 34` sem decisão do Alex.
Last activity: 2026-09-20 — verificação da Fase 33: **PASSED, 7/7**. (1) 5 `Secao*.jsx` existem em `web/src/opcoes/`, zero import de `App.jsx` (grep + guardião por diretório). (2) `OpcoesScreen.jsx` continua único chamador de `useOpcoesMcp`/`useOpcoesPropostas` (grep repo-wide, nenhum `Secao*` importa os hooks). (3) `curadoriaAtiva` (`App.jsx:7739-7743`) segue gateado só por `tab` — `git diff --stat` vazio pra `App.jsx` no range INTEIRO da fase, nenhum `Secao*` referencia a flag. (4) Fold-in D-04a real: zero `optionsGate`/`optionsProposta` em qualquer `.jsx` de `web/src/opcoes/`, `SubAbaOperar` lê `opcoesPorTicker[ticker]` do fan-out compartilhado por prop, sem fetch local. (5) Guardrail CVM de manchete (D-02) generalizado: os 4 arquivos que renderizam `.manchete` batem byte a byte com a allowlist `RENDERIZADORES_DE_MANCHETE` do guardião, mais varredura negativa por diretório. (6) Suíte canônica fora do sandbox: **2923 pytest passed/5 skipped/3 xfailed/0 failed + 151/152 `.mjs`** (1 falha ambiental pré-existente, `test_ios_assets.mjs`, `web/ios/` gitignored — `CLAUDE.md:236`), idêntica à baseline de todas as ondas. (7) `npx vite build` verde, 111 módulos, sem erro de sintaxe. Único achado: doc drift em `REQUIREMENTS.md` (REORG-01..07 ainda marcados "Pending" apesar de satisfeitos) — corrigido nesta sessão (`Done`), não é gap funcional.

**Fase 33 completa — resumo das 5 ondas:** `SecaoVigias`+`uiOpcoes` (33-01) → `SecaoDescobrir`+carimbo de frescor front-only (33-02) → `SecaoSetups` (33-03) → `SecaoComparar`+guardião proativo de estado compartilhado (33-04) → `SecaoAnalisar`+fold-in D-04a (33-05). Todas com suíte canônica idêntica à baseline, todas com prova negativa real, `App.jsx` nunca tocado. Uma interrupção por rate limit na 33-01 (retomada sem perda). Avisos de lint não-bloqueantes acumulados (props/imports não usados em alguns arquivos) — candidatos a limpeza numa fase futura, não impedem nada hoje.

**Próximo passo, quando o Alex decidir:** `/gsd-plan-phase 34` (Navegação hub + workspace) — única fase restante do milestone v1.6.

Anterior — `33-04` completo: `SecaoComparar.jsx` extraído; `Linha`/`RazaoGanhoPerda` subiram pra `uiOpcoes.jsx` (reuso, não duplicação); 3 achados além do censo do plano: um guardião (`test_opcoes_analisar_ui.mjs` seção 9, "alvo e stop viajam nomeados") ficaria inerte, repontado pra `SecaoComparar.jsx`; a asserção nova de "sem recálculo de custo" só pegava a forma literal `2*N+1`, prova negativa 2 escapou por `Math.min(...)`, regra alargada; **guardião novo, proativo**: varredura de diretório trava `useState` redeclarando `tese`/`ticker`/`vencimento`/`lote` em QUALQUER dos 5 `Secao*.jsx` desta fase (Pitfall 6), não só neste arquivo — protege a 33-05 antes dela rodar. Suíte idêntica à baseline. Commits `3002958`/`7fe429b`/`2e06d75`. `App.jsx` intocado. 3 avisos de lint (props não usadas em `SecaoComparar.jsx`: `ticker`/`custos`/`setTese`) — não bloqueiam, suíte canônica é a fonte de verdade, revisar depois se sobrar tempo.

Anterior — `33-03` completo: `SecaoSetups.jsx` extraído (listagem de setups gravados + porta de criação, reusa `CriarSetup.jsx` sem duplicar); 5 guardiões reapontados (achou mais um, `test_opcoes_mcp_aba_ui.mjs`, só na suíte completa); prova negativa 3 gerou guardião novo pra `nomeNoServico` fora da tela, com um falso-positivo contra uso legítimo de `key=` pego e corrigido antes de commitar. Suíte idêntica à baseline (2923 pytest + 151/152 mjs). Commits `3729144`/`84203f1`/`8a59ede`. `App.jsx` intocado.

Anterior — `33-02` completo: `SecaoDescobrir.jsx` compõe Blocos A/B + frase-ponte sem reescrever nenhum dos dois motores; D-04b (carimbo de frescor) resolvido FRONT-ONLY (backend já devolvia `at`/`meta.source`); REORG-06 (guardrail CVM) generalizado por varredura de diretório; 5 guardiões reapontados + 2 asserções novas (REORG-07, relógio do cliente no carimbo). Suíte idêntica à baseline (2923 pytest + 151/152 mjs). Commits `20d1818`/`032efcb`/`5b21a61`. `App.jsx` intocado.

Anterior — `33-01` completo: `SecaoVigias.jsx` + `uiOpcoes.jsx` (módulo de primitivos compartilhados) extraídos de `OpcoesScreen.jsx`; 7 guardiões reapontados (achou 1 a mais que o censo do planejamento, só na suíte completa: `test_opcoes_custo_declarado.mjs`); 4 provas negativas reais por injeção. Suíte: 2923 pytest (baseline) + 151/152 `.mjs` (1 falha pré-existente, `test_ios_assets.mjs`, documentada em `CLAUDE.md:236` — `web/ios/` gitignored, não é regressão). Uma interrupção por rate limit no meio da execução (sessão retomada do ponto exato, nenhum trabalho perdido). Commits `b72ab44`/`dd954e2`/`0f6be6f`.

**Sessão de 2026-09-19 — planejamento (`/gsd-plan-phase 33`):** pesquisa de fase pulada (pesquisa do milestone já cobria), UI-SPEC pulado (fase é extração pura, zero mudança visual por desenho), `gsd-pattern-mapper` achou analog pros 11 arquivos (11/11), `gsd-planner` gerou 5 planos sequenciais (33-01 SecaoVigias → 33-02 SecaoDescobrir+D-04b → 33-03 SecaoSetups → 33-04 SecaoComparar → 33-05 SecaoAnalisar+D-04a). Achados do planejamento que corrigiram o CONTEXT.md original: lista de guardiões era 5, achou 9 reais (censo por plano vira piso, não a lista fixa); D-04b confirmado front-only por medição direta do backend (`/api/options/curadoria` já devolve `at`/`meta.source`); achado um guardião (`test_opcoes_mcp_aba_ui.mjs:133`) que ficaria falso-positivo silencioso pós-extração (chave `opcoesLeituraTitulo` duplicada em `OpcoesScreen.jsx:667,913`) — corrigido no plano 33-05. `gsd-plan-checker` achou 1 blocker real (33-05 removeu o fallback que D-04a original exigia) — verificado pelo orquestrador (`carteira.map` em `OpcoesScreen.jsx:402` e `:692` são o mesmo array, fallback é código morto provado) e fechado por emenda de uma linha ao CONTEXT.md, sem replanejar. 2 warnings não-bloqueantes: publicação combinada 33+34 ainda sem plano formal (decidir ao fim da Fase 34); 33-02/33-05 têm 4 tasks (limiar de aviso, não erro). Guardrail aplicado: nenhum mutador `gsd-sdk query state.*`/`roadmap.*` foi chamado — STATE.md editado à mão; anotação de dependências no ROADMAP.md pulada por precaução (já visível no frontmatter de cada plano).

**Milestone v1.4 (Opções v2) ARQUIVADO em 2026-09-19.** 14 fases (15-19, 24-32) em
`.planning/milestones/v1.4-phases/`; detalhe completo em
[`v1.4-ROADMAP.md`](milestones/v1.4-ROADMAP.md).

**Decisão de produto (2026-09-19, avaliação agentic UX escopada à aba Opções):**
mapeamento factual da aba (14 arquivos, ~4.960 linhas) achou a sub-aba "Setups"
misturando 5 trabalhos diferentes numa rolagem só (descobrir oportunidades cross-
carteira, vigias, analisar ticker manual, comparar vencimentos, gerenciar setups) —
~16 controles fixos mais os que escalam com a carteira. Achado adicional: a
"frase-ponte" (`OpcoesScreen.jsx:711-714`) nunca colapsa, repete a mesma explicação
toda visita. Alex decidiu: **reorganizar por job-to-be-done primeiro**, personalização
(progresso do aprendiz, desafio por padrão observado, explicação adaptativa) depois —
personalizar uma tela que já mistura 5 tarefas só entregaria "memória inteligente"
dentro da bagunça. Fase 2 (explicação adaptativa) é candidata a atacar a frase-ponte
como primeiro alvo mensurável.

## Posição anterior (v1.4, antes do arquivamento)

Phase: 32 (Consolidação das operações de opções na aba Opções) — **COMPLETA, em produção**. Única ressalva pendente corrigida e publicada pela quick `260916-g6p` (`F10-20260916-03`).

**Sessão de 2026-09-16 (quick 260916-g6p — fecha a ressalva `deferred-items.md`):**

Guard null-safe explícito substitui `|| 0` nas três cópias do helper `porLote`/CTA
de collar (`CuradoriaEstruturas.jsx:99`, `CandidatoOpcao.jsx:57,143-144`,
`PropostaLastreada.jsx:200,268-269`). Duas armadilhas medidas antes de editar:
`Math.abs(null) === 0` (o guard precisa ENVOLVER `Math.abs`, nunca ficar dentro
dele) e o ramo `ctaCollarDebito` do CTA de collar é alcançado também com
`p.caixa` falsy (o `p.caixa &&` na frente não é redundante). `ARQUIVOS_EXCECAO_OU_ZERO`
removida do guardião `test_opcoes_analisar_ui.mjs`; `PropostaLastreada.jsx`
(cópia original, Fase 28, nunca esteve na allowlist) entrou na regra `OU_ZERO`
pela primeira vez. Prova negativa real, não descrita: `|| 0` reintroduzido à
mão, guardião falhou nomeando o arquivo (exit 1), revertido, guardião voltou a
passar (exit 0). Suíte canônica completa fora do sandbox: 2923 pytest + 152
`.mjs`, exit 0, idêntico à baseline da Fase 32.

**Bloqueio de segurança do executor, resolvido pelo orquestrador:** o gate de
commit do executor exige, em modo worktree, que a branch HEAD bata com
`worktree-agent-*` (proteção contra a feature de paralelização de agentes).
`v2/interacao-estrutural` não bate — mas é a branch de trabalho de longa
duração deste projeto, não uma branch efêmera; o dispatch nunca usou
`isolation="worktree"` (`workflow.use_worktrees=false` neste projeto), então a
premissa do gate não se aplicava. Confirmado pelo orquestrador antes do
executor prosseguir.

**Task 3 (bump, `publicar-web.sh`, push nas duas branches, confirmação HTTP)
inicialmente NÃO executada de propósito**, pendente de confirmação explícita
do Alex antes de tocar produção, conforme guardrail do repositório ("não
publicar nada sem confirmação explícita, fase por fase"). Alex confirmou
("Pública") em turno separado; a Task 3 rodou então: `bump.sh`
(`F10-20260916-02`→`-03`), `publicar-web.sh` fora do sandbox (mesmo achado de
TLS das Tasks 1-2), comentário do `SERVER_BUILD_ID` reescrito à mão
preservando histórico, suíte canônica repetida pós-bump (2923 pytest + 152
`.mjs`, exit 0, sem queda), commit `bc2e03a`, push em `v2/interacao-estrutural`
E `origin/main` (fast-forward, `HEAD == origin/main`). Confirmado por HTTP:
`boris.semente.dev/api/health` respondeu `F10-20260916-02` por ~6 min
(Railway ainda redesplegando) e então `F10-20260916-03` — carimbo novo em
produção. Commits desta quick: `c584c96`/`47b8907` (Tasks 1-2) + `bc2e03a`
(Task 3, publicação).

**Sessão de 2026-09-16 (execução da Fase 32):**

As 5 waves rodaram sequenciais (uma por plano — `App.jsx`/`OpcoesScreen.jsx`
são tocados por quase todos, não havia paralelismo honesto). Executor `sonnet`,
sem worktree. Cada plano fechou com a suíte canônica inteira, não com meia
baseline: **2923 passed + 152 `.mjs`, exit 0** em todas as waves, mais
`vite build`.

O que mudou de verdade para o usuário: Posições perdeu os quatro blocos de
opções e ganhou UMA linha de chamada cuja contagem lê `ctx.curadoria` (fonte
única, D-03); a aba Opções abre com a frase-ponte que nega hierarquia entre os
dois motores (D-05, mitigação regulatória, incondicional por desenho) e os dois
blocos lado a lado, cada um com o rótulo que diz qual motor representa; a
sub-aba Operar ganhou o ramo multi-candidato e `PropostaDaPosicao` morreu.

**Um defeito de princípio 4 foi corrigido de passagem (32-03):** a curadoria
exibia "nenhuma estrutura elegível" também quando a BUSCA FALHAVA — afirmava um
resultado que ninguém mediu. Erro passou a ter precedência sobre vazio, com
texto e CTA próprios, e a linha em Posições nunca mostra número no estado de
erro (verificado ao vivo, com o fetch da curadoria forçado a 502).

**A verificação ao vivo pegou o que teste estático não pega.** A cadeia de
execução foi provada nos dois ramos: venda coberta por **clique real** (posição
`ITUB4MOCK06C` aberta, caixa +R$ 195,00 exatamente o prêmio) e collar pelo
MESMO `executarCandidato` + `store` reais servidos pelo Vite — porque no mock a
razão prêmio÷perda das vendas cobertas sempre ganha e **nenhum collar chega ao
top-4**, então o ramo era inalcançável por clique. O collar abriu as duas pernas
de verdade (call 31 vendida + put 29 comprada, 400 cada), caixa inalterado por
serem prêmios iguais. Nota metodológica: o ramo foi exercitado com o código de
produção, nunca com uma reimplementação do caminho.

**Duas ressalvas ficaram abertas, com o Alex ciente ao aprovar:**

1. *Item 8 do roteiro (multi-candidato) nunca foi visto rodando* — só renderiza
   com put isolada E collar endossados na mesma posição (MULTI-01, Fase 19), e
   o mock não produz isso. Dívida de verificação, não de código.

2. *`deferred-items.md`* — três cópias de `v * (X || 0)` que renderizariam
   "R$ 0,00" no lugar de "—" se o campo viesse nulo. A terceira
   (`PropostaLastreada.jsx`, Fase 28) está fora do escopo do plano que achou o
   padrão, então o guardião ganhou exceção **datada e nomeada** em vez de a
   regra ser afrouxada.

**Achado de processo:** o plano 32-05 mandava auditar `main...HEAD`, mas `main`
LOCAL estava parada em `54ff538` e o range acusava arquivos proibidos que a
fase nem tocou. A referência certa é `origin/main` — que já era ancestral do
HEAD, tornando a publicação um fast-forward sem merge.

*Guardrail aplicado:* mutadores de estado do gsd-sdk não foram chamados —
STATE.md e ROADMAP.md editados à mão.

**Sessão de 2026-09-15 (planejamento), depois do UI-SPEC:**

`gsd-pattern-mapper` rodou primeiro: 7 arquivos mapeados, 7 com analog exato —
esta é fase de extração/movimentação, não de UI nova. O achado que mais
importa para o executor: `test_opcoes_analisar_ui.mjs` tem uma allowlist
`ARQUIVOS` hardcoded que NÃO cobre arquivo novo em `web/src/opcoes/`, então
guardião que parece passar pode estar inerte.

`gsd-planner` (opus) gerou **5 planos em 5 waves, todas sequenciais** — não há
paralelismo honesto a extrair porque `App.jsx` e `OpcoesScreen.jsx` são tocados
por quase todos. 32-01 vocabulário em `copy.js`; 32-02 extração dos 3
componentes para `web/src/opcoes/` + `useCuradoria` sobe para `App()`; 32-03 os
blocos cross-carteira migram para o topo da sub-aba Setups e Posições fica com
a linha única; 32-04 sub-aba Operar ganha multi-candidato e `PropostaDaPosicao`
morre; 32-05 auditoria da cadeia do collar + checkpoint ao vivo + bump/
publicação (`autonomous: false`, checkpoint bloqueante).

**As duas decisões que o CONTEXT exigia por escrito ficaram escritas.**
(A, no 32-02) o fetch de `useCuradoria()` sobe para `App()` com flag monotônica
`curadoriaAtiva`, ligada por visita a Posições ou Opções, **nunca por boot** —
zero chamada para quem não abre as telas, uma varredura por sessão para quem
abre, menos que hoje, que refaz a cada volta a Posições; o custo contra
`mydata_budget` está declarado no plano. (B, no 32-04) multi-candidato é
**portado**, não aceito como débito: `PropostaDaPosicao` não se move, ela morre,
porque das três coisas que faz só o ramo `multi` tem valor fora da lista de
posições.

**O plan-checker achou 1 blocker real, e ele não era de forma.** O 32-03
removia a chamada de `useOpcoesPropostas` em `CarteiraScreen` na wave 3, mas o
consumidor da linha ~5009 (`PropostaDaPosicao`) só sumia na wave 4 —
`ReferenceError` em render para qualquer usuário com posição aberta, ou seja, o
caminho principal da fase. Nada automatizado pegaria: `vite build` é esbuild,
sem TypeScript e sem ESLint em `web/`, e os guardiões `.mjs` são regex sobre o
fonte, nenhum renderiza. Corrigido invertendo a ordem (a definição sai na wave
3, a chamada sobrevive e só sai na wave 4, junto do último consumidor) e —
mais importante — com **regra nova de guardião contra a classe inteira do
defeito**: identificador usado sem declaração em `App.jsx` reprova. Re-verificado:
VERIFICATION PASSED, incluindo a checagem de que o estado intermediário da wave
3 não chega a produção (só o 32-05 publica) nem a `mydata_budget` (o provider de
produção desse caminho é Yahoo, não mydata).

**Gate de cobertura de decisões reprovou primeiro, e expôs uma lacuna real.**
1/4 na primeira rodada: D-01, D-02 e D-07 só existiam no `requirements:` do
frontmatter, que o gate não lê — ele só procura `D-NN` em
`must_haves`/`truths`/`objective`. Corrigir não foi colar ids: o D-07 **não
tinha nenhuma truth**, então um executor que DELETASSE `OportunidadesOpcoes` em
vez de movê-la passaria em todos os critérios de aceite. Truth nova escrita para
ele. 4/4 na segunda rodada, conferido pelo orquestrador.

*Guardrail aplicado:* mutadores de estado do gsd-sdk não foram chamados —
este STATE.md foi editado à mão.

## Posição anterior nesta fase (pesquisa + contrato de UI)

*Pesquisa (`32-RESEARCH.md`).* Mapeou por leitura direta os 4 blocos que se
movem (as linhas do CONTEXT.md tinham deslocado), o hook `useCuradoria()`, a
cadeia de execução do collar curado e os guardiões estáticos em risco. Três
achados que a discussão não tinha: (a) a regressão que o CONTEXT.md temia —
a cadeia de execução do collar — **não** depende de onde o card renderiza
(`ctx.A.executarCandidatoCurado` já chega idêntico às duas telas); o risco
real são os testes; (b) **seis** guardiões quebram, não três —
`test_curadoria_ui.mjs` (26 regras) precisa de reescrita total porque ancora
em `indexOf("function CuradoriaEstruturas")` dentro de `App.jsx`; (c)
`SubAbaOperar` **nunca lê `prop.candidatos`** — a casca de props está pronta,
a lógica de multi-candidato não existe, então mover `PropostaDaPosicao` para
lá sem portá-la regride MULTI-02 em silêncio.

*Decisões novas.* **D-07** (Alex, respondendo à Open Question #1 da pesquisa):
`OportunidadesOpcoes` — o motor COM gate — vai para o **topo da aba, ao lado
da lista curada**, não é deletada nem empurrada para Operar. É a leitura que
cumpre o D-05 ao pé da letra: os dois motores cross-posição visíveis lado a
lado. Consequência aceita: agrava a rolagem do D-06. As Open Questions #2
(onde mora o fetch compartilhado de `useCuradoria()`, com o custo de
`mydata_budget` declarado) e #3 (portar multi-candidato ou nomear o débito)
viraram **obrigação de declaração explícita no PLAN.md**, registradas no
`32-CONTEXT.md`.

*Contrato de UI (`32-UI-SPEC.md`, aprovado 6/6).* Entrega central: os dois
rótulos do D-05 nos dois modos, com uma **frase-ponte obrigatória, sempre
visível e nunca colapsável** ("nenhuma é mais certa que a outra") — sem ela,
quem escaneia a tela lê "AS 4 MELHORES" (bloco sem gate) como veredito geral
do app. Também: a linha de chamada de Posições em 4 estados, contrato
mensurável de densidade em 375×667px (cartões de 210/220px, composição
exata da primeira dobra) para honrar o D-06 sem busca nem acordeão, e o
porte de multi-candidato reusando `CandidatoOpcao` verbatim. O checker achou
um bug de princípio que a pesquisa não pegou: **`useCuradoria().erro` existe
mas nunca é exibido** — falha de fonte cai hoje no estado "vazio", violando
o princípio 4 do `CLAUDE.md`. A correção entra na fase, especificada de
forma verificável.

*Duas decisões de fechamento (Alex, 2026-09-15).* (1) "Topo da aba" =
**topo da sub-aba Setups**, onde os vigias já vivem — os blocos
cross-carteira não aparecem em Operar, e a estrutura de render de
`OpcoesScreen.jsx` não muda. (2) A lacuna de **carimbo de frescor** nos dois
blocos cross-carteira (princípio 3: dado de mercado exibe horário e se está
atrasado) é pré-existente e fica **fora do escopo** — virou
`.planning/todos/pending/carimbo-frescor-blocos-cross-carteira.md`.

*Exceção assinada.* O UI-SPEC reusa as escalas herdadas do `App.jsx` (três
pesos de fonte, spacing fora da grade de 4px) em vez de normalizar. O Alex
assinou a exceção (`developer-approved — matches existing pattern —
2026-09-15`) com citações `file:line`; normalizar a escala é débito nomeado
para fase própria. Normalizar dentro da 32 transformaria "mover blocos" em
"mover + reestilizar".

*Guardrail aplicado:* mutadores de estado do gsd-sdk não foram chamados —
este STATE.md foi editado à mão.

## Posição anterior nesta fase (discussão)

Phase: 32 — DISCUTIDA, pronta para planejar

**Como chegamos aqui (2026-09-15):** a Fase 31 foi publicada e o Alex testou em produção. Achou dois defeitos em sequência — (1) os cards da lista curada não executavam nada (quick `260915-j5l`, confirmação inline no card) e (2) o collar sempre dava 409 porque a rota de execução re-derivava pelo motor errado (quick `260915-ndt`, rota nova pelo motor da curadoria). Ambas em produção (`F10-20260915-01`, `F10-20260915-02`). No meio disso ele levantou três vezes o mesmo incômodo — *"gostaria de deixar todo conteúdo em relação a opções na aba opções"*, *"as telas estão ficando muito poluídas"* — que virou a Fase 32. Discussão rodada: **D-01** Posições perde os 4 blocos de opções e fica com UMA linha de chamada com contagem; **D-02** o clique leva à lista na aba Opções (não a uma oportunidade específica — a leitura de deep-link foi desambiguada e caiu); **D-03** a contagem sai do mesmo dado da lista, nunca calculada à parte; **D-04..D-06** delegadas a mim ("decide o resto por mim"): blocos cross-carteira vão pro topo da aba junto dos vigias (precedente D4 da Fase 27, já aprovado), os dois motores ficam lado a lado com rótulos honestos em vez de unificar agora, e a rolagem longa fica aceita e adiada. Ver `.planning/phases/32-consolida-o-das-opera-es-de-op-es-na-aba-op-es-standalone/`.

## Posição anterior (Phase 31)

Phase: 31 (Varredura de oportunidades de opções) — EM PRODUÇÃO

**Contexto de chegada nesta fase:** Fases 27-30 (aba Opções sobre a carteira, sub-aba Operar, flag opt-in de opção a descoberto, curadoria de IA das 4 melhores vendas cobertas) foram publicadas juntas em produção em 2026-09-14 (`F10-20260914-01`), e um bug de produção achado no checkpoint ao vivo da Fase 30 — `options_provider_mydata.get_options` escolhia vencimento vencido por confiar num campo (`vence_no_pregao`) que vem falso em 100% dos dados reais, zerando a proposta de venda coberta desde a Fase 14 — foi corrigido e publicado à parte (`F10-20260914-02`, quick task `260914-b6p`). Ao final dessa sessão o Alex reabriu uma decisão que tinha acabado de fechar ("primeiro vencimento futuro, seja qual for") e pediu uma varredura maior de oportunidades — a Fase 31 nasceu desse pedido, registrada só como rascunho (`31-CONTEXT.md`) com 3 lacunas abertas.

**Esta sessão (continuação via handoff, 2026-09-14):** a branch `v2/interacao-estrutural` estava 59 commits atrás de `origin/main` (todo o parágrafo acima aconteceu numa sessão/worktree diferente) — fast-forward aplicado antes de qualquer trabalho. Rodado `/gsd-discuss-phase 31` de verdade sobre o rascunho: **D1** teto fixo de 2 vencimentos por posição elegível (custo declarado 2× o de hoje contra o orçamento medido do mydata, 60/min·2.000/dia — `get_vencimentos` é barato/lista inteira, `get_options_chain` é 1 chamada cara POR vencimento); **D2** as 4 estruturas do motor interno entram na varredura (venda coberta/put/collar/a descoberto, ampliando o universo estreito da Fase 30), mas a descoberto só aparece pra quem já tem `permitirOpcaoADescoberto` ligado (Fase 29 intacta, gate de execução não muda) e o ranking usa a MESMA fórmula prêmio÷perda-máxima da Fase 30 pras 4 estruturas, mesmo sabendo que isso desfavorece put/collar estruturalmente; **D3** `PayoffChart.jsx` ganha só responsividade mobile 375px nesta fase, sem overlay de múltiplos candidatos nem interatividade (component hoje recebe 1 estrutura por vez, confirmado por leitura); **D4** universo de tickers continua só posições já na carteira, sem estender a watchlist/catálogo. Nenhum código de produto tocado — só planejamento. Ver `.planning/phases/31-varredura-oportunidades-opcoes/31-CONTEXT.md` e `31-DISCUSSION-LOG.md`.

**Planejamento desta sessão (`/gsd:plan-phase 31`, 2026-09-14):** a Fase 31
tinha `31-CONTEXT.md` fechado mas nunca tinha sido registrada no
ROADMAP.md (`roadmap.get-phase` devolvia `found: false`) — registrada como
tabela + seção `#### Phase 31`, Goal/Success Criteria derivados 1:1 das
decisões D1-D9 já travadas, sem decisão de produto nova (commit
`714101b`). Pesquisa pulada por padrão do projeto
(`workflow.research=false`) e por já haver CONTEXT.md detalhado;
`gsd-pattern-mapper` rodou e produziu `31-PATTERNS.md` (7 arquivos
mapeados, todos extensão de arquivo já existente, sem módulo/rota/
componente genuinamente novo). UI-SPEC.md pulado deliberadamente — mesmo
precedente das Fases 29/30 (ambas "UI hint: yes" sem gate formal de
UI-SPEC). `gsd-planner` (modelo opus) gerou 4 planos em 3 ondas: 31-01
(motor puro — 4 estruturas, prêmio líquido com sinal, gate de descoberta
D-05) e 31-03 (PayoffChart 375px) na onda 1; 31-02 (rota + cache de
vencimentos no mydata) na onda 2; 31-04 (bloco de Posições + checkpoint
humano ao vivo) na onda 3. `gsd-plan-checker` (modelo sonnet): VERIFICATION
PASSED, 0 blockers, 2 warnings — cross-checou contra o código real (não só
a descrição dos planos): confirmou que o gate D-05 é genuinamente novo
(tempo de DESCOBERTA, separado do gate de EXECUÇÃO em `store.py`) e que o
número de requisições declarado (3/posição) bate com
`options_provider_mydata.get_options()` real. Os 2 warnings foram
corrigidos nos planos antes de fechar a fase: (1) 31-01 não mandava
atualizar os docstrings de `opcoes_curadoria.py` que hoje dizem "pare: é
mudança de escopo (D1)" — exatamente o que esta fase reverte de propósito;
(2) 31-02 declarava custo "exatamente 60/min" mas o teto REALMENTE
enforçado em `mydata_budget._teto_util_min()` é `int(60*MARGEM)` = **54**,
contador global compartilhado com `candle_provider`/agente, não 60 nem
por-usuário (commit `4f6f88b`). Gate de cobertura de decisão
(`check.decision-coverage-plan`) achou 0/8 D-NN cobertas na primeira
rodada — os planos citam decisões em prosa como "(D-05)", sem o formato
literal "D-NN:" que o gate escaneia em `must_haves.truths`; corrigido
adicionando o prefixo `D-NN:` às truths já existentes, sem mudar
substância — 8/8 na segunda rodada (commit `455b897`). Nenhum código de
produto tocado nesta sessão — só planejamento.

**Próximo passo:** `/gsd:execute-phase 31` (`/clear` antes, para começar a
onda 1 com contexto limpo).

## Posição anterior (Phase 29)

Phase: 29 (Opção a descoberto com flag opt-in) — CODE COMPLETE

Plans: **29-01 a 29-03 executados** (2026-09-13). `buy_option`/`sell_option` — o caminho "a seco", que não tinha nenhum gate de lastro — passa a exigir um flag opt-in para abrir posição nova; lastro obrigatório continua sendo o padrão de toda conta.

**O buraco que a fase fechou não era só o óbvio.** `abrir_call_coberta`/`comprar_put_protecao`/`abrir_collar` já checavam lastro; só `buy_option` (a compra a seco, que por definição nunca tem lastro) não checava nada — confirmado por leitura direta antes de planejar. O gate entrou dentro da própria função (`store.buy_option`), não só na rota HTTP, para que nenhum atalho de cliente o pule.

**O achado mais sério veio da execução, não do planejamento**: o `deviceStore` (ramo do iPhone sem sessão, offline) reimplementa `buy_option` em JavaScript inteiro, e não herdava nenhuma checagem do backend — sem o Plano 29-02, o app nativo continuaria comprando a seco livremente mesmo depois desta fase "fechar" o buraco no servidor. Achado e corrigido na execução, não previsto no plano original.

**A assimetria de risco é o invariante central**: ligar o flag exige o mesmo termo de responsabilidade do Modo Operador (`TermoDescobertoModal`, rolagem obrigatória, checkbox, versão "v1.0" — D1, decisão fechada com o Alex); desligar é um toque, sem modal. `sell_option`/fechar **nunca** é bloqueado, em nenhum estado — provado por teste real na sequência mais exigente (ligar → abrir → desligar → fechar), porque o pedido original do Alex foi explícito: o flag é para ABRIR sem lastro, nunca para impedir sair de uma posição já aberta.

**Escopo mantido estreito de propósito (D2, fechada com o Alex)**: `OpcoesCamada` (a UI de compra a seco em Watchlist/Radar) não migrou para a sub-aba "Operar" da Fase 28 nesta fase — só ganhou a recusa do backend. Migrar a UI fica para uma fase seguinte, sobre o gate já testado.

**Esta fase NÃO passou por `gsd-plan-checker`** (decisão de custo do Alex, mesma economia de outras fases) — e por isso cada plano exigiu prova negativa **real**, não descrita: apagar o gate (não só comentar) e confirmar que os testes nomeados caem de verdade, revertido com `git diff` limpo depois. Executado em todos os três planos, com comandos e saídas reais registrados nos SUMMARYs.

**Checkpoint fechado com aprovação DIRETA do Alex — diferente da Fase 28.** Primeiro round: ele reportou que o card "OPÇÕES A DESCOBERTO" não aparecia em Preferências — achado real, não descartado. O orquestrador investigou antes de aceitar qualquer coisa: navegou para o mesmo servidor ativo, na mesma conta do Alex, e o card apareceu normalmente — isso isolou o problema para o lado do cliente dele, não o código. Pergunta direta revelou a causa: ele tinha testado pelo **app nativo do iPhone**, que não foi recompilado nesta sessão (pendência nomeada, não defeito — o gate é do servidor, não confia em UI nenhuma). Na web, confirmado certo. Pedido o roteiro completo na web, com ênfase no passo mais importante (desligar o flag não pode bloquear fechar uma posição já aberta) — resposta do Alex, literal e direta nesta conversa: **"aprovado"**. O executor recusou corretamente, duas vezes, aceitar um relato do orquestrador antes disso — mesma regra do 28-03, funcionando como desenhada.

**Custo de execução ficou dentro da faixa aprendida na Fase 28** (163K/213K/160K tokens por onda) — a disciplina de orçamento corrigida ali (não ler `STATE.md` inteiro, suíte canônica uma vez só, `Grep` antes de `Read` em arquivo grande) generalizou para uma fase nova sem repetir o estouro de 536K tokens.

Suíte: **2793 passed, 5 skipped, 3 xfailed, 0 failed + 146/146 `.mjs`** (baseline da fase era 2780 + 144 — +13 pytest / +2 `.mjs`, todos guardiões novos). `npx vite build` verde nas três ondas.

**NÃO ESTÁ NO AR.** Nenhum push a `origin`, nenhum `scripts/bump.sh`, nenhum `publicar-web.sh`. **Pendência operacional nomeada**: o app nativo do iPhone só reflete esta fase depois de um build novo (`cap sync` + Xcode) — não bloqueia o fechamento da fase.

**Fora de escopo, intacto:** migrar `OpcoesCamada` para a sub-aba "Operar" (fase seguinte, sobre o gate já testado); abrir posição de opção automaticamente pelo Operador IA (sem precedente de código — pesquisa da Fase 26); curadoria de IA das 4 melhores estruturas (Fase 30, guardrail: ranking determinístico, IA só narra); polish de UX pós-uso real (Fase 31).

## Posição anterior (Phase 28)

Phase: 28 (Sub-aba "Operar" e extração de `PropostaLastreada`) — CODE COMPLETE

Plans: **28-01 a 28-03 executados** (2026-09-13). Toda operação lastreada (venda coberta, put de proteção, collar) que só existia dentro do card do ativo em Watchlist/Radar passa a existir na aba Opções, numa sub-aba nova ("Operar") ao lado de "Setups" (a Fase 27, intocada).

**A duplicação de UI que a fase existia para resolver:** `PropostaLastreada` (manchete do motor, payoff numérico, CTA de abrir/fechar) e o caminho de aceite que a acompanha (três `window.confirm` em ordem, o guard de liquidez difícil) viviam só dentro de `App.jsx`, usados por `AtivoCard` (Watchlist/Radar) e por `PropostaDaPosicao` (Portfólio). Trazer a operação para a aba Opções sem duplicar essa lógica pela terceira vez exigia extrair — mas `OpcoesScreen.jsx` não importa nada de `App.jsx`, de propósito (ADR-027, Decisão 3). A extração para `web/src/opcoes/PropostaLastreada.jsx`, importado pelos dois lados sem nenhum importar o outro, é a **Emenda 3** ao ADR-027 — mesma técnica das Emendas 1 e 2 da Fase 27, aplicada a componente de UI em vez de dado.

**O que existe agora:** o card de proposta lastreada não existe mais dentro de `AtivoCard` — removido sem deixar órfão (`opPropostaBusy`/`posAberta`/`onAbrirLastreada`/`onFecharLastreada`, as cópias locais, saíram; a cadeia legada `OpcoesCamada` continua). A tira `OportunidadesOpcoes` em Posições (Fase 18) ficou **intocada de propósito** — já não usava `PropostaLastreada`. A aba Opções ganhou a sub-aba "Operar": lista de posições → escolher uma → lastro livre + leitura técnica interna (mesma da Fase 27, custo zero) + a proposta lastreada do motor, com payoff numérico completo e o CTA de abrir/fechar em Modo Operador; em Modo Estudo, a MESMA proposta aparece como texto didático, sem botão nenhum.

**Verificado ao vivo pelo orquestrador** (conta de teste local, `api-qa-opcoes` com provider mock e mercado forçado aberto — não é o app de produção): custo zero confirmado por `read_network_requests` (só `/api/options/tecnico`, `/api/options/gate`, `/api/options/proposta`, `/vigias` — nenhuma `/api/options/mcp/*`); abrir uma PUT de proteção funcionou de ponta a ponta (`POST /api/options/lastreada/abrir` → 200, payoff numérico exibido — ganho ilimitado, perda máx. R$65, empate 30,65 —, caixa debitado R$65,00 certo, CTA virou "Vender a put — recebe R$65,00"); o card sumiu do `AtivoCard` mesmo com posição real E opção real abertas simultaneamente (o teste mais forte possível para SC-3); a tira em Posições seguiu mostrando a proposta corretamente; o ticker escolhido persistiu ao trocar entre "Setups" e "Operar".

**NÃO exercitado ao vivo:** fechar a posição de fato (o clique dispara `window.confirm(...)` nativo, que o ambiente de automação do Browser tool não consegue confirmar — sem chamada de rede resultante) e collar (a posição de teste só gerou proposta de PUT). Isto é limitação da ferramenta de verificação, registrada como tal, não um defeito encontrado.

**O executor da 28-03 recusou fechar o checkpoint** quando o orquestrador relatou "aprovado" de segunda mão — corretamente: mensagem de agente não é consentimento do usuário, regra deste ambiente. As três objeções (aprovação não veio do Alex diretamente; verificação foi sob mock/mercado forçado, não o `how-to-verify` pedido; 2 dos 9 passos, os mais frágeis, não exercitados) foram levadas ao Alex na conversa direta. Resposta literal: **"Fechar agora"** — decisão de produto aceitando o risco residual, fundamentada em `onFecharLastreada`/`abrirCollar` serem o MESMO caminho de `store.py`/`useAceiteLastreado` já em produção desde as Fases 14/17/19 (a extração do 28-01 só mudou de onde a UI chama, não a lógica).

**Custo de execução, medido e corrigido no caminho:** o executor da 28-01 gastou 536.743 tokens — 2 a 4× a faixa normal desta sessão — por dois erros do próprio orquestrador no prompt: mandar ler `STATE.md` inteiro (910 linhas / ~109KB, sem relação com o plano) e não proibir reruns redundantes da suíte canônica. Corrigido explicitamente nos prompts da 28-02 (195.669 tokens) e 28-03 (213.560 tokens) — ambos dentro da faixa esperada, apesar de cobrirem trabalho comparável ou maior.

Suíte: **2780 passed, 5 skipped, 3 xfailed, 0 failed + 144/144 `.mjs`** (idêntica à baseline herdada da Fase 27, +1 `.mjs` do guardião novo do 28-02). `npx vite build` verde nas três ondas.

**NÃO ESTÁ NO AR.** Nenhum push a `origin`, nenhum `scripts/bump.sh`, nenhum `publicar-web.sh` — publicação é passo humano separado, fora do escopo desta fase (28-CONTEXT, Guardrails).

**Fora de escopo, intacto:** opção a descoberto (Fase 29, exige o flag opt-in em Configurações que ainda não existe em lugar nenhum do código); curadoria de IA das 4 melhores estruturas (Fase 30, guardrail: ranking determinístico, IA só narra); polish de UX pós-uso real (Fase 31).

## Posição anterior (Phase 27)

Phase: 27 (Aba Opções sobre a carteira) — EXECUTING
Plans: **27-01 a 27-05 executados** (2026-09-13). A aba deixou de ser um consultor de tickers avulsos e passou a operar sobre o que a pessoa tem.

**O defeito que originou a fase não era o que parecia.** A queixa foi "os setups criados não estão sendo gravados". Não havia falha de escrita: `create_setup` gravava e a paridade `deviceStore`/`serverStore` estava correta nos três métodos. O que havia eram **três fatos que somados são indistinguíveis de "não gravou"** — (a) nenhuma rota de listar setups, porque `list_setups` só era chamado dentro de `/leitura/{ticker}` e imediatamente filtrado por ticker; (b) o ticker nascendo `""` a cada abertura da aba; e (c) o armazém do serviço sendo **compartilhado e sem dono** (ADR-027 Decisão 7), de modo que **o conceito "meus setups" não existia em lugar nenhum do sistema**. Diagnosticar isso antes de planejar mudou a fase inteira: o trabalho virou construir o dono que faltava, não caçar um bug de escrita que não existia.

**Medido antes de construir.** O isolamento depende de o serviço aceitar um nome prefixado, e isso era suposição de contrato externo. Virou checkpoint bloqueante na Task 0 — o Alex exercitou contra o `mcp.semente.dev` real, com controle sem prefixo para desambiguar recusa. Resultado: aceita, e devolve o `name` **byte a byte** como enviado, o que é a premissa silenciosa embaixo de todo prefixar/desprefixar.

**O que existe agora:** índice de vigias por usuário no kv (`opcoes_vigias.py`), namespacing por `sha256(uid)[:8]` no nome que vai ao serviço — o nome que a pessoa escreveu vive só no índice e na tela —, duas rotas de listagem (custo 0 e custo 2), universo da aba = `ctx.data.positions`, bloco "Seus vigias" fora de qualquer ticker, lastro livre no cartão **antes** da tentativa (hoje ele só aparecia na recusa), estado vazio com caminho para a Carteira, e a leitura técnica (tendência, ADX, HV21/HV63, suporte/resistência, régua de 7 pregões) saindo do **motor interno determinístico** — a mesma fonte do Radar e da Watchlist, custo ZERO — enquanto o serviço externo ficou só com cadeia/vencimento/payoff, sob clique explícito com o preço escrito no controle. Isso cruzou a fronteira que o ADR-027 fechou: **Emendas 1 e 2** registradas, não silenciosas.

**Verificado no app rodando, não só em teste:** abrir a aba dispara apenas o frescor e `/api/options/vigias` (custo 0); escolher um ativo dispara apenas `/api/options/tecnico/{ticker}?period=1y`; **nenhuma ida à rota de custo 3**. Universo provado com carteira de 1 posição (BBAS3) contra watchlist de 6 tickers. HV em 31,5%/29,9% — unidade correta, não 0,3% nem 3150%. Régua e linha de tendência concordando sobre o mesmo dia.

**Três exposições do nome do armazém fechadas**, uma delas achada só porque varremos irmãs do defeito relatado: o `/grafico` imprimia o hash **como título do gráfico**. Gate de dono fechado em `/grafico` e `/desativar` por helper único (`_exige_dono`), não por condição copiada.

**O que a execução desmentiu dos planos** (fonte ganha, sempre): `{setups}` que era `{vigias}`; `summary.sma9`/`sma21` inexistentes; a regex do guardião de custo que só via prefixo `mcp` e deixaria a entrada nova inerte; e **duas injeções de defeito que os planos vendiam como prova e eram vácuas** — medidas, reprovadas e substituídas.

Suíte: **2780 passed, 5 skipped, 3 xfailed, 0 failed + 143/143 `.mjs`** (a fase começou em 2691 + 137). `npx vite build` verde.

**NÃO ESTÁ NO AR, e a sequência importa:** `27-01` e `27-02` têm de sair **juntos** — publicar só o backend quebraria "Disparos do setup" e "Desativar" no app publicado, porque o front de hoje manda `s.name` sem prefixo e levaria 422. A validação ao vivo do 27-01 (Parte 1 do checkpoint) depende dessa publicação conjunta.

**Fora de escopo, intacto:** ligar a aba à execução de ordens — é o B3 da Fase 26, com a decisão de lastro obrigatório × flag de operação a descoberto ainda pendente. Esta fase é a fundação dele, não ele.

## Posição anterior (Phase 26)

Phase: 26 (Otimização de UX e da camada de IA) — EXECUTING
Plan: 26-01 concluído (Fase A do `26-CONTEXT.md` — sete correções independentes entre si, uma por commit, todas com referência reconfirmada por `grep` no momento da edição). **A aba Opções deixou de ser invisível para o assistente de IA:** nasceu na Fase 24 já no `BottomNav` e nunca entrou nos outros registros de tela — `pet:opcoes` respondia 400 "Tela desconhecida." e `/api/pet/resumo?tela=opcoes` caía no fallback de `"mercado"`, devolvendo a Watchlist **com cara de resposta certa**; nada quebrava e nada logava. Agora `PET_TELAS` tem 8 telas, existe `_pet_resumo_opcoes` com **custo ZERO de MCP por contrato** (ADR-027: a leitura da aba sai de clique explícito — há teste com bomba em `mcp_client.call_tool` provando) que manda o determinístico do servidor e **diz o que não sabe** em vez de inventar (a seleção ativo/tese/vencimento é estado local de `OpcoesScreen`, princípio 4), e `petSnapshot` tem `case "opcoes"` com o motivo no lugar do valor ausente — nem `null` nem omissão, que seriam lidos como "não escolheu ativo nenhum". **A KB passou a ser consultada ANTES da validação de tela/setor:** pergunta que os 83 verbetes respondem de graça era recusada com 400 por causa da TELA de onde partiu, com a dependência invertida (`kb.resolver` recebe só `(pergunta, voc)`, não lê a tela). A allowlist **não afrouxou** — `tela` continua nunca entrando em `kb.resolver`, e quando a KB devolve `None` as duas checagens rodam abaixo, antes de exigir conta e antes de qualquer gasto; quatro guardiões travam os dois lados, inclusive o contra-guardião "tela inválida sem cobertura da KB continua recusada". **O tour começa onde o app abre:** passo zero novo nomeando "Acompanhar" (`useState("evolucao")`) — antes o primeiro passo mandava "Descubra no Radar", apontando outra tela antes de dizer onde a pessoa caiu — mais o passo da aba Opções, seção nova em `ajudaSecoes` e o espelho em `docs/AJUDA.md`. **Três textos que descreviam um produto inexistente passaram a bater com o código:** a frase de evidência insuficiente (agora a do `CLAUDE.md` byte a byte, com o guardião **lendo** o arquivo de norma em vez de redigitá-la — redigitar foi como as duas divergiram; `skill_ref.sem_setup` intocada, é conceito diferente), o caminho das três mensagens de 402 do `metering.py` ("Conta & preferências" morreu no qa/45 Decisão 1; cota esgotada virava beco sem saída) e o trecho do mascote no `SKILL.md` da didática ("Coruja" não existe como componente; a restrição por modo caiu em 2026-08-08). **A3 estava JÁ IMPLEMENTADO pela Fase 24** (`404f8e6` criou `tituloOpcoes`/`subtituloOpcoes` nos dois blocos e já os lia em `OpcoesScreen.jsx`): o item virou o guardião que faltava, não reimplementação — registrado como desvio em vez de trabalho fabricado. **O padrão que atravessa a fase:** três dos sete achados (A1, A5, A6) nasceram de texto redigitado que apodreceu em silêncio, então todo guardião criado aqui **deriva da fonte** (`BottomNav.defs`, `CLAUDE.md`, `PerfilHub`). O do A6 cruza todo `"Perfil → X"` citado em prosa pelo backend contra os `title="X"` reais do `PerfilHub` — o rename anterior passou silencioso justamente porque o teste travava os tiles, o backend citava um caminho em prosa, e os dois nunca se olhavam. **Achado aberto, registrado e NÃO corrigido:** `web/src/api.js:11` (`ADDR_HINT`) tem o MESMO defeito do A6 com outro destino (o bloco SERVIDOR DO APP migrou para "Fonte de dados") — fora do escopo literal da task, registrado no SUMMARY, no comentário do guardião e na mensagem do commit; candidato a quick-task. Suíte canônica **2691 passed, 5 skipped, 3 xfailed, 0 failed + 137 `.mjs`, exit 0** (baseline 2682 + 134 — o delta de +9 pytest e +3 `.mjs` é exatamente o que os itens criaram); `npx vite build` verde. **NÃO está no ar, e são DUAS publicações:** A1/A2/A6 são backend (deploy com bump manual de `SERVER_BUILD_ID`) e A1/A3/A4/A5 tocam `web/src/` (`bump.sh` + `publicar-web.sh`) — e a **publicação conjunta da Fase 25 continua pendente na frente desta**, então as duas entram na mesma janela. `server/web_dist`, `web/src/version.js` e `SERVER_BUILD_ID` ficaram intocados de propósito.

Nota de contagem: a Fase 26 **não** está registrada no `ROADMAP.md` (o diretório e o `26-CONTEXT.md` nasceram sem entrada lá), pela mesma razão que o bloco `progress:` do frontmatter segue em **37/38**: ele conta o ROADMAP, e mexer nele aqui faria o número mentir. A linha da Fase 25 na tabela do ROADMAP também está desatualizada (diz `1/6 In Progress` com os 6 planos executados) — as duas correções pertencem a quem for registrar as fases 25 e 26 lá, não a este plano.

## Posição anterior (Phase 25)

Phase: 25 (Planos comerciais) — EXECUTING
Plan: 25-06 concluído (Fase 5 do `25-CONTEXT.md` — o plano visível no app). Até aqui **nada** no app lia `authUser.plan`; o único traço de plano na tela era um sufixo discreto num modal. Agora: **tile "Plano" no grupo CONTA** do hub de Perfil (não em "IA e desempenho", que é eixo modelo/BYOK/custo; não em "Atividade da IA", que é custo/histórico; e **nunca badge global** — plano muda raríssimo, hoje só por atribuição manual da administração, e um badge permanente cobraria carga cognitiva em TODA tela pela estética de freemium agressivo que o ADR-010, decisão 4, proíbe), **`PlanoScreen`** compondo `authUser.plan` (já vem de `/api/auth/me`, sem chamada nova) + `aiQuota` + `watchlistQuota` — as duas rotas publicam o limite EFETIVO desde o 25-04, então a tela não pode divergir do que o gate aplica —, e **`LimiteAtingido`**, banner compartilhado extraído da caixa `T.warn` já repetida em quatro pontos: cor `T.warn` e **nunca `T.negative`** (vermelho é de P&L; usá-lo faria "bati o teto" parecer prejuízo), **inline no ponto da tentativa** (nunca toast de 2,6 s, nunca modal) e só com **código reconhecido** — erro técnico continua na linha de erro de sempre, porque são categorias diferentes (princípio 4). **As duas rotas de watchlist** — as ÚNICAS que devolviam 402 **cru** ao cliente, já que a de análise degrada para 200 pelo FIX-C01 — passaram a devolver `detail` **dict** (`code`/`message`/`limite`/`usado`), com `message` sendo a frase de `plan.py` **verbatim**, comparada contra a FONTE no teste e não contra um literal copiado. **`usado` tem o MESMO sentido nas duas rotas** (quantos a conta tem HOJE), contra a letra do plano, que pedia `len(final)` no PUT: o campo é lido por um componente compartilhado e um sentido por rota daria número certo numa tela e errado na outra. **A fronteira ficou travada por teste:** o 402 de `_gate_analise` **continua string** — uniformizar mostraria `[object Object]` (decisão registrada no 25-04). `persistence.js` entrou no diff **fora dos `files_modified`** porque no iPhone o gate de watchlist é client-side e **autoritativo** (CR-01 da Fase 13): sem a recusa estruturada lá, o banner seria código morto justamente onde ele é a única defesa — a saída foi dar ao gate local a MESMA forma do 402 e ter **um leitor só**. Guardião novo com 90 asserções e **não-vacuidade MEDIDA por 7 defeitos injetados** (T.negative no banner, texto divergindo entre os modos, CTA de upgrade, badge global, código do 402 divergindo entre `main.py` e `plan.js`, limite caindo no toast, tabela comparativa) — todos reprovados, todos revertidos. `test_fase13_contadores_ui.mjs` atualizado com nota datada (`<QuotaSeg` de 3 para 4 usos) e **endurecido**: o uso novo tem de morar dentro de `PlanoLinha`. **Não está no ar, e a fase 25 está COMPLETA EM CÓDIGO** — falta a publicação CONJUNTA das cinco fases, nesta ordem: deploy do backend (bump manual de `SERVER_BUILD_ID`), depois `bump.sh` + `publicar-web.sh`, depois `publicar-admin.sh`.

Anterior: 25-05 concluído (Fase 4 do `25-CONTEXT.md` — o módulo de planos no portal). Os cinco limites e as funções de cada plano deixaram de ser editáveis só por `sqlite3` no container: `GET`/`POST /api/admin/planos` sob `usuarios.gerenciar`, com prévia (sem `aplicar`), validação tudo-ou-nada e auditoria de **um evento por campo** (entidade `plano_config`, `entity_id` = o plano, `field` = a chave). **As duas armadilhas que o 25-04 nomeou foram resolvidas, não só mencionadas.** (1) **Voltar ao padrão passou a existir:** não havia como LIMPAR um limite gravado no kv (`db` só tem `kv_delete_user`), então uma configuração vencia a env para sempre — e gravar `None` NÃO servia, porque `None` ali é valor legítimo (`ilimitado`). A saída foi **sentinela no kv** (`plan.TXT_PADRAO`), uma linha PRESENTE cujo conteúdo significa "não configurado", e não um `DELETE` novo em `db.py`, que daria de brinde o poder de apagar qualquer chave global (kill-switch, cota da brapi, prompts) por uma necessidade de um campo só. `null` explícito = voltar ao padrão; `ilimitado` = sem limite (configuração do plano, que VENCE o global) — são opostos e viajariam parecidos. (2) **A origem `default` parou de ser ambígua na tela:** o backend publica `decide` (plano|global) e `efetivo` por plano × limite, e o card tem frases DIFERENTES para "existe outro lugar que manda, e ele é este" e "o default do catálogo é a última palavra mesmo" — mais uma terceira, não pedida pelo plano, para o `origem: env` das três envs GLOBAIS, que também não é configuração do plano. **A auditoria compara o par `(valor, origem)`**, não só o número: restaurar 10 sobre um padrão 10 não muda o valor e muda quem decide. Card dentro da aba "Usuários e papéis" (mesma decisão comercial), sem aba nova, sem `window.confirm`, sem nenhuma lista literal de plano/limite/função no portal. Funções do plano em somente leitura — **D2 segue pendente**. 27 casos de backend (RED 27/0) + guardião estático de front (RED 25), este com verificação ESTRUTURAL de que a frase de origem mora dentro do ramo condicional. **Não está no ar:** deploy do backend com bump manual de `SERVER_BUILD_ID` e, SÓ DEPOIS, `publicar-admin.sh` — portal novo contra backend velho chamaria rota inexistente.

Anterior: 25-04 concluído (Fase 3 do `25-CONTEXT.md` — os gates leem o plano). O catálogo do 25-03 deixou de ser estrutura inerte: os cinco pontos de controle resolvem pelo plano da conta, com o override GLOBAL que o portal já escreve como camada de BAIXO (`managed.daily_quota`, `options_mcp_api.cota_usuario_dia`, `assistente.teto_dia_brl` não mudaram uma linha de lógica — é por isso que "sem configuração, nada muda"). A conciliação mora no CHAMADOR (`main._limite_do_plano`) e chega a `options_mcp_api` por injeção; `plan.py` não foi tocado. **A precedência é decidida pela ORIGEM, não pelo valor** — `origem: default` NÃO vence o painel admin, porque o default do catálogo É o número global de sempre. **D3:** o `owner` pula o cap COMERCIAL e continua sujeito ao FÍSICO, com a consulta de papel só no ramo de negação, sem cache (ADR-013) e fail-closed. **O 402 parou de ser classificado por frase:** o gate carimba a exceção no ponto da decisão e a aba Opções lê o carimbo; o `detail` continua string de propósito. **Escopo reduzido deliberado:** `opcoes.criar_setup` (D2) NÃO migrou do RBAC para o plano — liberar por plano ampliaria o acesso ao armazém compartilhado do serviço MCP; `funcoes_do_plano` segue pronta e não lida, e a pendência está nomeada no `25-04-SUMMARY.md`. 28 casos novos (RED 17/11 medido). **Não está no ar:** deploy do backend com bump manual de `SERVER_BUILD_ID`, sem efeito visível no primeiro request.

Anterior: 25-03 concluído (Fase 2 do `25-CONTEXT.md` — o catálogo de planos). `plan.py` deixou de ser dois dicts literais: cinco pontos de controle declarados numa tupla única, resolvendo por memória → kv → env → default, cada valor dizendo a origem, e funções de produto por plano (D2). **Não muda comportamento:** os três gates seguem lendo o dict estático; quem passa a ler o catálogo é o 25-04. 31 casos novos cravam os números de hoje por extenso. **Decisão registrada:** `plan_at_least` REMOVIDA (órfã, apontando para um `require_plan()` inexistente; a D2 escolheu conjunto de funções, não ordem de tier) — `_ORDEM_PLANO` fica, tem consumidor real. **Não está no ar:** exige deploy do backend com bump manual de `SERVER_BUILD_ID`, mas sem consequência visível — nada consome o catálogo até o 25-04, então o deploy pode ir junto com o do próximo plano.

Anterior: 25-02 concluído (Fase 1 — o papel `owner`, decisão D1). Irrevogável nas duas camadas, permissões pela união dinâmica de `GRUPOS`, ancorado em `B3_OWNER_EMAIL` sem fallback de primeira conta. **Não está no ar:** deploy do backend com bump manual de `SERVER_BUILD_ID` e, só depois, `publicar-admin.sh`. **O que o `owner` ainda NÃO faz:** pular o cap comercial — a D3 é a Fase 3.

Anterior: 25-01 concluído (Fase 0 — o conserto do contador). **Com uma decisão aberta para o Alex:** a ativação do gate mensal em `/api/scan/deep`, `/api/carteira-stopalvo` e `/api/assistente` foi MEDIDA e NÃO foi feita — ligá-la hoje barraria conta pelo resíduo do defeito que este plano acabou de corrigir, não por uso. Três opções e o preço de cada uma em `25-01-SUMMARY.md`; a recomendação é ativar junto com os limites configuráveis da Fase 2. Enquanto não houver decisão, os três casos estão na suíte como `xfail(strict=True)` e FALHAM no dia da ativação.
Status da fase 25: 6 de 6 planos — o `25-CONTEXT.md` descreve as Fases 0 a 5 e todas estão executadas. A fase está COMPLETA EM CÓDIGO; o que resta é a publicação conjunta (etapa operacional, não plano). A fase ainda NÃO está registrada no `ROADMAP.md` — o diretório e o contexto nasceram no commit `c92c3e1` sem entrada lá, e criá-la não era escopo deste plano. Por isso o bloco `progress:` do frontmatter segue em 37/38: ele conta o ROADMAP, e mexer nele aqui faria o número mentir nos dois sentidos.

## Posição anterior (Phase 24)

Phase: 24 (Aba Opções sobre MCP — análise e criação de setups) — 24-05 (publicação) ainda aberto
Plan: 24-17 concluído (12 planos concluídos: 24-01 a 24-04, 24-06, 24-07, 24-11, 24-12, 24-14, 24-15, 24-16 e 24-17), mais 24-08 e 24-09 fora de plano (ver abaixo)
Status: os QUATRO achados do `24-VERIFICATION.md` estão fechados (F-01/F-02/F-03 no 24-06; F-04 no 24-07), a VERIFICAÇÃO AO VIVO passou (2026-09-11, tarde) e os DOIS achados ao vivo da noite fecharam: campos vazios sem motivo na LEITURA DO ATIVO (24-11) e "dado em dia" com dois pregões faltando (24-12). Plano aberto: só o 24-05 (publicação), PENDENTE DE OK HUMANO por desenho (`autonomous: false`)

**PARIDADE VIVA VERDE (2026-09-11)** — o Alex rodou `scripts/fechar-fase-24.sh`
com as credenciais lidas do Railway em memória, e `test_mcp_vivo.py` +
`test_opcoes_paridade_mcp.py::test_paridade_viva` passaram. É a PRIMEIRA vez
que `opcoes_payoff.perfil_da_estrutura` e `evaluate_option_structure` são
confrontados sobre DADO REAL — até então a paridade só existia contra fixture
derivada do próprio `opcoes_payoff`, ou seja, consistência consigo mesmo.

Duas ressalvas sobre o que isso significa, para ninguém ler a mais:

- o gatilho de consolidação do **ADR-027, Decisão 3** pede "10 pregões seguidos
  de paridade viva verde **em staging**". Esta execução foi local, contra
  produção, num pregão. **Não conta como 1 de 10** — a contagem começa quando
  o smoke de staging (`publicar-staging.sh`) passar a rodar a paridade viva;

- a primeira tentativa FALHOU e não era do serviço: era o defeito de ciclo de
  vida de event loop corrigido no 24-09 (abaixo).
Progress: [█████████░] 97%

Last activity: 2026-09-12 (noite) — **25-06**: a fase 25 fecha em código. O
app passou a ler `authUser.plan` — tile no grupo Conta do Perfil, `PlanoScreen`
compondo plano + as duas cotas, e `LimiteAtingido`, banner compartilhado em
`T.warn` (nunca `T.negative`: bater o teto não é prejuízo), inline no ponto da
tentativa e só com código reconhecido, porque erro técnico e recusa de plano são
categorias diferentes. As duas rotas de watchlist devolvem 402 estruturado com a
frase de sempre verbatim; o 402 do gate de análise **continua string**, travado
por caso de teste. `persistence.js` entrou no diff fora dos `files_modified`: no
iPhone o gate é client-side e autoritativo, e sem a recusa estruturada lá o
banner seria código morto onde ele é a única defesa. Guardião novo com 90
asserções e 7 defeitos injetados, todos reprovados. Suíte 2682/5/3xfail + 134
`.mjs`, `vite build` verde, nada publicado.

Anterior (2026-09-12, tarde) — **25-01**: o contador mensal que o plano
comercial lê volta a medir análise. A rota de telemetria descontava o LOTE
inteiro (até 50 por envio) da cota de 30 análises/mês do free, porque chamava
`metering.consume` sem `month_section` e caía no default `aiUsageMonth` — o
ledger do gate. Agora tem balde próprio; os dois nomes antigos ficaram byte a
byte, porque já há contador gravado no kv sob eles.

MEDIDO antes de qualquer decisão: das 7.273 contas do banco local, TRÊS tinham
ledger mensal, e nas três o `count` batia EXATAMENTE com o número de eventos
de telemetria ingeridos no mês (4.167/4.167, 2.348/2.348, 25/25) — 100% do
contador era telemetria, 0% era análise; duas já acima do limite de 30. O banco
é de TESTE, não produção, e isso está declarado no SUMMARY: o que transfere é a
estrutura, não o número.

**Decisão devolvida ao Alex:** a ativação do gate mensal nas três rotas órfãs
NÃO foi feita. Com o resíduo do defeito ainda gravado no mês corrente (só zera
na virada), ligar hoje barraria — provavelmente a conta do próprio Alex — no
assistente, no stop/alvo e no Radar profundo, por telemetria que ele não pediu.

Diagnóstico corrigido no caminho, e importa para a Fase 3: as três rotas **já
contam** no ledger que o plano lê; o que falta é o GATE, não a contagem.

Guardião de `month_section` passou a varrer `server/app/` inteiro (prova por
injeção); `metering.snapshot` parou de misturar o dia de um domínio com o mês
de outro. `plan.py` fora do diff, nenhum limite alterado. 2576 passed, 5
skipped, 3 xfailed + 131 .mjs, exit 0. NÃO está no ar: exige deploy de backend
com bump manual de `SERVER_BUILD_ID`.

Anterior (2026-09-12, meio-dia) — **24-17**: o plano de uma conta passa
a mudar pelo portal admin, sem tocar no banco. Pedido do Alex do próprio dia,
depois de a promoção dele ter saído por `scripts/plano-da-conta.sh`, direto no
SQLite do container — porta que serve à conta do dono e a mais ninguém.

`POST /api/admin/users/{user_id}/plan` espelha a rota de papéis que já existia
ao lado: gate `usuarios.gerenciar`, 404 para conta inexistente, 400 nomeando os
aceitos para plano fora de `plan.PLANOS_POR_ID` e `audit.record` com entidade
`user_plan`, o valor anterior e o novo. A recusa é do **backend**, não só da
UI: a tela não é o único cliente possível da rota, e `users.plan` decide cota
de análises e de watchlist.

`user_plan` entrou em `rbac.ENTIDADES_POR_PERMISSAO["usuarios.gerenciar"]` —
sem essa linha o evento é gravado e `entidades_visiveis` o filtra para fora de
todo filtro, inclusive o de quem acabou de produzi-lo (mesma lição de 24-15 e
da Fase 5 do MCP).

Fonte única dos ids: `planosDisponiveis` viaja em `GET /api/admin/users`, o par
comercial de `gruposDisponiveis`. **Nenhum id de plano escrito no portal** —
inclusive o fallback `"free"` da exibição, que virou travessão. Uma lista na UI
seria a segunda cópia, e ela não acompanharia o dia em que existir um terceiro
plano.

**Isto reverte uma decisão registrada, e a reversão ficou registrada.** Quatro
notas diziam "sem override de plano nesta rodada": a docstring de
`POST .../roles`, o comentário de topo do card no portal e — fora do escopo
declarado do plano — `db.set_user_plan` e `plan.current_plan`. As quatro foram
ATUALIZADAS com a data (2026-09-12), nenhuma apagada: registro de decisão que
mente é pior que registro ausente.

**Decisão que não é para "melhorar":** mudar o PRÓPRIO plano continua permitido
e auditado, com teste próprio carregando a razão escrita. Quem tem
`usuarios.gerenciar` já concede a si mesmo qualquer papel de governança pela
rota irmã, e o registro com o nome de quem clicou é a mitigação que o ADR-013
escolheu para essa classe inteira; um freio só aqui seria regra inventada e
assimétrica com o que existe ao lado.

RED medido antes de cada correção: backend `21 failed, 2 passed` de 23, front
`12 falha(s)` de 27. Um caso passava por **vacuidade** — o 404 de conta
inexistente, porque o catch-all `_api_inexistente` também responde 404 — e foi
endurecido para exigir o texto da rota. Suíte canônica **2565 passed, 5 skipped

+ 131 .mjs, exit 0** (baseline 2542/5 + 130; +23 e +1 são exatamente os novos);

`cd web-admin && npx vite build` verde; a allowlist pública do ADR-013 **não
cresceu** (a rota é gated).

**NÃO ESTÁ NO AR**, e são DUAS publicações, nesta ordem: deploy do backend (com
bump manual de `SERVER_BUILD_ID`) e só depois `publicar-admin.sh` — portal
publicado antes do backend chamaria uma rota que o servidor não tem. Nada
empurrado a origin, nenhum PR, nenhuma publicação.

Anterior (2026-09-12, madrugada) — **24-16**: BYOK passa na frente do
gate **mensal** do plano. Achado a partir de um bloqueio real: o Alex bateu as
30 análises/mês do `PLAN_FREE` e, ao configurar a própria chave de LLM,
continuou barrado.

O bloqueio dele era legítimo; o **caminho de saída** é que estava quebrado.
`_gate_analise` consultava `plan.can_analyze(metering.month_used(...))`
**antes** de qualquer verificação de chave própria — e `month_used` lê um
ledger cujo único ponto de escrita, `metering.consume`, só roda no ramo
**gerenciado** de `_ai_apply_managed` (com BYOK esse ramo devolve
`lambda: None` na primeira linha). Quem traz a própria chave era barrado por
consumo de um recurso que não vai usar. O código já prometia o contrário em
dois lugares: o comentário `# BYOK utilizável → sem cota` e o texto do 402,
que fala de "análises do seu plano" para quem não está usando a chave do plano.

Precedência nova: **BYOK → PLANO (mensal) → METERING (diário)**. Não é mudança
de política comercial — muda **quando** o gate mensal é consultado, nunca **o
que** ele mede: `plan.py` intacto byte a byte, `metering.py` intacto, nenhum
contador novo. `llm.resolve_key(config)` é a mesma expressão que
`_ai_apply_managed` já usava (duas definições de "tem chave" divergem na
primeira manutenção, e uma delas decidiria dinheiro).

10 casos novos em `server/tests/test_plan_gate_byok.py`, com o RED **medido**
contra o código anterior (`4 failed, 6 passed`): falharam os casos 1/1b/1c —
a correção — e o 5, que só consegue medir o ledger depois de atravessar o gate
com chave própria (sub-asserto do caminho novo, não prova independente de
não-regressão; o desvio da previsão do plano está registrado no SUMMARY e na
docstring do teste). Passam nos **dois** estados: o caso 2 (sem BYOK continua
barrando com a mensagem exata — o guardião do cap comercial, tão importante
quanto o 1), 2b, 3, 4 (pro, com e sem chave) e 5b (anônimo segue fail-closed).

Vale para as três rotas que chamam `_gate_analise` (`/api/analyze`,
`/api/technical/analyze` e a compilação de setups da aba Opções); nenhuma
dependia da ordem antiga. Suíte canônica **2542 passed, 5 skipped + 130 .mjs**
(baseline 2532/5 + 130 — os +10 são exatamente os novos).

**NÃO ESTÁ NO AR**: é mudança de backend e exige deploy, com bump manual de
`SERVER_BUILD_ID`. Até lá a conta do Alex continua barrada em produção. Nada
empurrado a origin, nenhum PR, nenhuma publicação.

Anterior (2026-09-12, madrugada) — **24-14**: o terceiro achado ao vivo
da mesma leva, agora sobre o **ensaio** do setup. Reproduzido contra o motor
real do serviço: um setup com `sma 200` sobre 48 pregões volta
`disparos: 0` com `pregoes_avaliaveis: 31`.

Os dois números estão **certos** — o motor curto-circuita (`AND` com um
`False` conhecido é `False`), e nos 31 dias de RSI acima de 30 o dia é
comprovadamente falso. O serviço não tem defeito. O que engana é a **leitura**:
"testei e não disparou", quando a verdade é "**nunca pôde disparar**" — a
condição da média não teve valor em pregão nenhum. É pior que o campo vazio do
24-11: vazio se vê, número plausível não, e o fim da linha é alguém **gravar**
um setup acreditando que ele foi validado contra o histórico.

A correção é uma **demonstração de impossibilidade**, não uma opinião:
`_ensaio_inconclusivo` compara a janela que cada condição DECLARA com o
tamanho do período que o backtest informou (`pontos = n - w + 1`; a janela da
`reference` conta igual e a maior manda). Nada é recalculado e nenhuma chamada
nova é feita — `setup` e `backtest` são o que o dry-run já devolveu. O veredito
`indisparavel` fica reservado ao caso demonstrável (condição sem ponto nenhum
dentro de um `AND`); com `OR` ou com a janela curta para a sequência, a
condição é listada como **ressalva** e o veredito é calado. A faixa entra
**acima** dos números (quem lê o número primeiro já formou a conclusão) e o
botão de gravar **continua existindo**: a tela impede a conclusão errada, não
a ação.

Dois desvios do PLAN, os dois registrados no SUMMARY: `JANELA_POR_INDICADOR`
não foi criado (seria a segunda cópia do vocabulário do serviço — a detecção
sai da FORMA do dado, ENG-06), e o texto do motivo de sequência foi reescrito
("pregões demais no fim do histórico" se lê como "pregões em excesso", o
oposto do que a condição descreve).

Suíte canônica `2511 passed, 5 skipped` + 129 `.mjs`, exit 0 (baseline
2478/5 — +33, exatamente os novos); `npx vite build` verde. Nada empurrado a
origin, nenhum PR, nenhuma publicação — produção segue em `F10-20260911-07` e
este texto só chega ao usuário no próximo bump + `publicar-web.sh`.

Anterior (2026-09-11, noite) — **24-12**: o segundo achado ao vivo do
mesmo dia, agora sobre o CARIMBO do dado. Medido com
`scripts/diagnostico-leitura-opcoes.sh`: numa **sexta (11/09)** a aba mostrava
"Pregão: 2026-09-08" com o chip dizendo **"dado em dia"**. O serviço estava
coerente com o próprio contrato — `negociacao_b3` com 49,58 h de idade contra
um SLA de 96 h — e ainda assim quarta (09) e quinta (10) não estavam na base.
Um SLA de quatro dias para cotação diária permite afirmar "em dia" sobre dado
de dois pregões atrás; o princípio 3 do `CLAUDE.md` pede o oposto.

A decisão: **medir em vez de herdar**. `_atraso_em_pregoes(data, _hoje=None)`
conta os pregões **estritamente** entre o dado e hoje, com
`pregao.is_trading_day` como fonte ÚNICA do calendário (fixos, móveis
derivados da Páscoa, exceções por ofício, `B3_FERIADOS_EXTRA`) — um guardião
proíbe `weekday()` dentro do helper, porque uma segunda contagem divergiria em
silêncio no primeiro Carnaval. O **dia corrente nunca conta**: o COTAHIST de um
pregão só sai depois do fechamento, e contá-lo faria o app acusar atraso todas
as manhãs sobre um dado que ainda não poderia existir. Data ausente, torta ou
no futuro é `pregoes: None`, **nunca 0** — 0 afirmaria "está no último pregão
fechado" sem ter como saber. (O 404 do `COTAHIST_D07092026.ZIP` no
`last_failure` do MyData é do feriado de 7/9 e não entra na conta: a B3 não
publica arquivo de dia sem pregão. Há teste para isso.)

`atraso` entra no envelope de `/status` e `/leitura` derivado do MESMO valor
que já vai em `pregao` (a expressão virou variável nas duas rotas, em vez de
recalculada) e **sem chamada de tool nova** — custos declarados 1 e 3 intactos.
No front, o chip ganha a QUARTA variante, com **precedência** sobre "dado em
dia": guarda explícita no ramo mais a ordem no fonte, as duas travadas por
guardião, e uma sanidade que reprova a ordem invertida. Quando o frescor do
serviço TAMBÉM bloqueia, as duas informações **somam** ("dado atrasado (50 h) ·
2 pregões atrás") porque medem coisas diferentes: idade da carga × pregões
faltando. `opcoesAtrasoPregoes`/`opcoesAtrasoAjuda` nas duas vozes, com a ajuda
só onde há contagem na tela.

**Nada passou a ser bloqueado** por causa disto: quem barra veredito e criação
de setup continua sendo o frescor do serviço (ADR-027, Decisão 8), e há
asserção explícita disso no guardião de rota.

Regra de ouro cumprida: os 16 testes de backend foram vistos VERMELHOS antes
(`AttributeError: ... has no attribute '_atraso_em_pregoes'` ×14, `KeyError:
'atraso'` ×2) e as asserções do bloco 12 do guardião de front também
(`14 FALHA(S)` de 17 rodadas contra o fonte de antes; o bloco consolidado tem
19). Todo teste novo fixa o relógio por `_hoje`: nenhum muda de
resultado conforme o dia em que a suíte roda. Suíte canônica: 2473 passed, 5
skipped + 129 .mjs, exit 0 (baseline 2457/5 — +16, exatamente os novos).
`npx vite build` verde.

NOTA OPERACIONAL: durante esta execução **outra sessão publicou o front na
mesma árvore** (`F10-20260911-06` em `version.js` e `SERVER_BUILD_ID`,
`server/web_dist` regravado, mtime 22:14–22:15). Nenhum arquivo dela entrou em
commit meu — cada `git add` foi por caminho explícito e conferido com
`git diff --cached --stat` — e `web/dist` foi restaurado a partir de
`server/web_dist` depois do build, para que a republicação da outra sessão não
levasse ao ar um front que ninguém aprovou. Nada empurrado a origin, nenhum PR.

Anterior (2026-09-11, noite) — **24-11**: fechamento do achado ao vivo do
mesmo dia. Na tela do Alex (PETR4, pregão de 2026-09-08), cinco campos da
LEITURA DO ATIVO mostravam travessão e mais nada — e travessão mudo não é
estado vazio: a pessoa não sabe se o app quebrou, se o ativo é estranho ou se
falta dado (princípio 9). Entre quatro saídas, o Alex escolheu **dizer o motivo
na tela, sem duplicar cálculo**: preencher o número seria fabricar (princípio
4) e recalcular criaria uma segunda implementação do mesmo indicador,
divergindo da do serviço em silêncio.

`_lacunas_da_leitura(behavior)` é helper PURO e deriva o motivo do que o
próprio `behavior` mostra — não consulta nada, não conta pregão, não afirma
tamanho de série. Três motivos: janela de 63 que não fecha (a de 21 fecha, por
isso os campos de 21 vieram), série curta demais para as médias, e
volatilidade realizada que o provedor não publica (`hv21`/`hv63` são colunas
DIRETAS do candle — o serviço MCP não as calcula). A lista nomeia só o que de
fato veio vazio; `behavior` ausente, torto, `sem_candles` ou sem `close`
produz lista vazia, porque a tela já tem estado próprio e repetir viraria duas
mensagens para a mesma ausência.

`lacunas` viaja ao lado de `behavior` (que segue verbatim) e **não custa
chamada de tool nenhuma** — `_cap_check(uid, 3)` intacto. Na tela, os motivos
vão AGRUPADOS no rodapé do bloco, ao lado do carimbo do pregão: repetir a
explicação em cinco linhas da tabela empurraria para fora da tela os números
que VIERAM, que é o oposto do que o achado pede. Os três textos entram em
`AVISOS` ([R-12]) e `opcoesLacuna` entra nas DUAS vozes — o motivo é do
backend e vai verbatim, o front só junta os rótulos.

A trava central mudou de forma em relação ao plano, que se contradizia: a
regex pedida ("dígito seguido de pregões") reprovaria o próprio texto aprovado
no mesmo plano ("exigem 63 pregões"). Prevaleceu a intenção — não afirmar o
tamanho da série —, em duas camadas com sanidade: vocabulário (só as janelas
que o serviço declara, 21 e 63, podem ser número) e forma (nenhuma frase diz
que a série TEM n pregões). Achado extra corrigido no caminho:
`range_63_sessions` chega SEMPRE como dict com os dois extremos nulos, e a
tela mostrava `— – —`, travessão travestido de faixa.

Regra de ouro cumprida: 10 testes de backend vistos VERMELHOS antes
(`AttributeError: ... '_lacunas_da_leitura'`, `KeyError: 'lacunas'`) e as 28
asserções do bloco 15 do guardião de front também (`18 FALHA(S)`). Suíte
canônica: **2457 passed, 5 skipped + 129 .mjs, exit 0** (baseline 2447/5 —
+10, exatamente os novos). `npx vite build` verde. Nada empurrado a origin,
nenhum PR.

NOTA OPERACIONAL: a árvore principal tinha trabalho em curso de OUTRA sessão
(`web/src/version.js` em `F10-20260911-05`, `server/web_dist` republicado e o
bundle iOS sincronizado com esse build). O `vite build` exigido pelo plano
regerou `web/dist` com o MESMO carimbo e hashes diferentes, e
`test_ios_assets.mjs` reprovou exatamente a condição que ele existe para pegar.
`web/dist` foi restaurado a partir de `server/web_dist` (byte a byte o build
anterior); nenhum arquivo versionado de terceiros foi tocado.

Anterior (2026-09-11, tarde) — três coisas fora de plano, todas commitadas:
**(24-08)** a seção `Criar setup` passou a renderizar a linha de recusa cobrada
— o "Deferred" que o 24-07 registrou por ter aquela tela fora dos
`files_modified` dele. A condição ali é SÓ `detail.cobrado === true`, sem o
filtro por `code === "mcp_erro_de_tool"` que o `RecusaCobrada` de
`OpcoesScreen.jsx` usa: nesta seção o débito chega por `setup_invalido` e
`setup_desconhecido`, e filtrar por código deixaria de fora o caso comum. É
seguro porque a marca vem do PONTO DO DÉBITO, nunca de dedução. Guardião com 6
asserções, provado RED.
**(script)** `scripts/fechar-fase-24.sh` — wizard de 7 etapas para o que só o
Alex pode fechar. Nenhum segredo toca o disco (`ENV_FILE=/dev/null`, zero
`write_env`): as credenciais vêm do Railway para variáveis do processo e saem
da memória quando ele fecha — por isso o wizard NÃO é retomável, e isso é
aceito.
**(24-09, achado ao vivo)** o cliente MCP atravessava event loops. `_HTTP` é um
`AsyncClient` do httpx2 e guarda o pool; uma conexão keep-alive aberta dentro
de um loop não sobrevive à morte dele, e cada `asyncio.run` fecha o seu. O
sintoma foi o pior possível: a PRIMEIRA chamada de rede do processo passava, a
segunda levantava `RuntimeError`, e o `except` traduzia isso para
`McpIndisponivel: emissor de credencial inacessível` — o cliente acusando o
SERVIÇO por um defeito daqui. `reset_cache()` limpava cache e token e nunca o
cliente, que é justamente o objeto com estado de loop. Correção:
`_do_loop_corrente()` descarta cliente e primitivas quando o loop muda, chamado
no início do caminho de rede. **Produção nunca viu e não veria**: uvicorn tem um
loop de vida longa e a função é no-op a partir da segunda chamada. Medido antes
de afirmar: `asyncio.Lock` sem contenção NÃO quebra ao trocar de loop neste
Python — a recriação do lock ficou como defesa do caso com contenção, e o teste
diz isso em vez de fingir que reproduziu um crash. Junto, o achado A-03 no
`except` do emissor: `type(e).__name__` sozinho não separava "loop trocou" de
"socket morreu" de "DNS não resolveu", e foi o que custou a reprodução inteira.
Suíte: 2436 passed, 5 skipped + 129 .mjs, exit 0.

Anterior (2026-09-11) — 24-07 executado na árvore principal (sem worktree): fechamento do achado F-04 com a decisão do Alex (cobrar a viagem que a tool recusou). `_chamada_com_cap` debita 1 no `except McpErroDeTool` e re-levanta — ponto ÚNICO da regra; o `/status` repete só porque chama `call_tool` direto, e segue respondendo 200. As quatro falhas sem viagem provada continuam sem debitar, com os quatro motivos escritos no código. Transparência: `AVISO_RECUSA_COBRADA` em `AVISOS`, `cobrado`/`nota` nos 422 de erro de tool (condicional, vindo de uma marca posta no ponto do débito — literal fixo mentiria no 422 fabricado por `_material_do_compilador`) e a linha discreta na tela, nos dois modos. 9 testes novos de backend vistos VERMELHOS antes (o do cenário medido falhava com `assert 0 == 6`), os quatro de "não debita" provados por injeção do defeito oposto, e 10 asserções novas no guardião de front. Suíte canônica: 2433 passed, 5 skipped + 129 .mjs, exit 0 (baseline 2424/5 — +9). `npx vite build` verde. Cache negativo NÃO implementado: 0 linhas em `mcp_client.py`. Nada empurrado a origin, nenhum PR.

Anterior (2026-09-11) — 24-06 executado na árvore principal (sem worktree): plano de CORREÇÃO dos três achados de escopo do `24-VERIFICATION.md`. (F-01) `_razao_ganho_perda(dados)` puro ao lado de `_em_reais` — adimensional, SEM `lote` na assinatura; razão que não existe é `None` COM motivo nos quatro casos (ganho sem teto, perda sem piso, dado ausente, perda zero), nunca 0 nem ∞; `razaoGanhoPerda` FORA do bloco `emReais` em `/proposta` e por item de `/possibilidades`; `RazaoGanhoPerda` nas duas seções da tela; os quatro motivos em `AVISOS` ([R-12]). (F-02) `/setups/compilar` deixava `httpx.ReadTimeout` subir ao handler global — agora 503 `ia_indisponivel` com "nada foi gravado" e `action`, mais `except Exception` justificado por escrito. (F-03) `audit.record` fatorado em `_audita()` com try/except + obslog `warn`: contabilidade não derruba rota cuja escrita externa JÁ aconteceu (armazém sem dono; retentativa duplica setup para toda a base). Regra de ouro cumprida: os 17 testes novos foram escritos ANTES e vistos VERMELHOS contra o código antigo. Suíte canônica: 2424 passed, 5 skipped + 129 .mjs, exit 0 (baseline 2407/5 — +17, exatamente os novos). `npx vite build` verde. Nada empurrado a origin, nenhum PR. F-04 INTOCADO e provado por diff: 0 linhas em `mcp_client.py`, nenhuma mudança em `cap.consome` nem em custo declarado de rota.

Anterior (2026-09-11) — 24-04 executado na árvore principal (sem worktree): o FRONT da Fase 5. Seção `Criar setup` (`web/src/opcoes/CriarSetup.jsx`) — descrição em português → interpretação do serviço + ensaio no histórico → gravar —, montada só sob `opcoes.criar_setup` (gate provado por RENDER com 5 formas de `authUser`, não por grep; o backend recusa de qualquer forma, ADR-013). `problems` item a item e verbatim; `cru` da LLM em nó de texto com pre-wrap (um `<script>` renderizado sai escapado — T-24-17 verificado); backtest com a ressalva FIXA junto dos números, sem verde/vermelho, e as frases de expectativa banidas da pasta; `null` sempre travessão. Três rotas de escrita nos DOIS stores (compilar no TIMEOUT_LLM), `recarregarLeitura()` com contador próprio depois de gravar/desativar, 18 chaves de copy nas duas vozes. Guardião novo com 97 asserções, provado contra 5 defeitos injetados. Suíte canônica verde: 2407 passed, 5 skipped + 129 arquivos .mjs, exit 0. Nada empurrado a origin, nenhum PR. Pendente de verificação: nada exercitado AO VIVO (`MCP_CLIENT_SECRET` fora do ambiente, nenhuma chamada de LLM real) e nada testado no aparelho.

Anterior (2026-09-11) — 24-03: três rotas de ESCRITA de setup (`/setups/compilar`, `/setups/confirmar`, `/setups/{name}/desativar`) atrás de `opcoes.criar_setup`, com o `system` do compilador montado em RUNTIME do `inputSchema` de `create_setup` + o resource `mydata://tools/create_setup` (zero vocabulário de DSL dentro do Boris, ENG-06), `description` restaurada com as palavras da pessoa, frescor que bloqueia criar e não bloqueia desativar, os dois 402 do gate de análise com texto próprio da aba e auditoria `opcoes_setup`. 27 testes novos em `test_opcoes_dsl.py`, com duas provas de não-vacuidade (403 e cap) feitas e revertidas. Pendente de verificação: nada foi exercitado AO VIVO (`MCP_CLIENT_SECRET` fora do ambiente) e NENHUMA chamada de LLM real foi feita — que um modelo devolva JSON compilável a partir do `system` montado é a primeira coisa a exercitar quando houver credencial.

Anterior (2026-09-11) — 24-02: front da Fase 3 (`PayoffChart`, seções Analisar e Possibilidades sob demanda com o custo em chamadas ANTES do clique, quatro rotas nos DOIS stores, 28 chaves de copy nas duas vozes). Nada exercitado ao vivo nem no aparelho.

Anterior (2026-09-11) — 24-01: `/cadeia`, `/operaveis`, `POST /proposta` e `POST /possibilidades` escritos, com reserva de cap em duas etapas e conversão por lote fechada no backend.

Anterior (2026-09-08, tarde) — quick 260908-ldg, gate de liquidez em três faixas com consentimento, mesclada e testada (2110 passed). Junto com 260908-dnl (recalibração do score) fecha o achado do dia: opções estavam apagadas em produção por um gate impossível de cruzar com mydata. Front republicado junto no `F10-20260908-02` (o servidor passou a exigir `aceitaLiquidezDificil`; front velho quebraria). PR #32 mesclado e PROMOVIDO em 2026-09-08 — `/api/health` = `F10-20260908-02`, gate ao vivo confirmado (PETR4/ABEV3/VALE3/ITUB4 NEGOCIÁVEL, RADL3 DIFÍCIL 50,9). Produção tinha ficado em `F10-20260907-01` até então: o #31 foi mesclado mas nunca deployado, e o -02 o contém.

Anterior no mesmo dia — as QUATRO quick tasks de 07/09 consolidadas numa publicação só (`F10-20260908-01`, commit 7be6b55, branch empurrada). Todas nasceram da mesma sessão de teste ao vivo em staging/iPhone: 260907-w33 (largura do card de candidato), 260907-x69 (textos do card de fechamento), 260907-vwl (aviso de ordem pendente) e 260907-vzp (setup aposentado, ADR-017). Suíte canônica verde nas duas suites: 2049 passed, 1 skipped.

`origin/main` foi mesclado ANTES do bump — era o que travava a publicação. Ao mesclar, a branch `claude/gallant-volhard-b8dcdb` trouxe um bump para `F10-20260907-01`, o MESMO carimbo que produção já servia, para código diferente: a colisão prevista, resolvida para `F10-20260908-01` (que nunca foi ao ar). Lição operacional: sessão paralela que roda `bump.sh` sem estar em dia com `origin/main` sempre reemite o carimbo de produção — o script deriva do valor LOCAL.

PROMOÇÃO FEITA em 2026-09-08 (PR #32 → main → Deploy manual pelo Alex). O único comando contra o GitHub foi `gh pr merge 32`, autorizado explicitamente; nenhum comando tocou o Railway. Próxima verificação humana: o confirm de consentimento de liquidez no aparelho, e os checkpoints das Fases 17/18/19 que seguem abertos.

RESSALVA HONESTA: a verificação foi estática (suíte + build). As quatro correções nasceram de achados ao vivo, mas nenhuma foi reconfirmada no aparelho depois do fix — o cenário depende de mercado aberto e posição elegível, a mesma dependência que trava os checkpoints das Fases 17/18/19.

## Performance Metrics

**Velocity:**

- Total plans completed: 22 (v1.0) + 44 (v1.1) + 6 (Phase 9, standalone) + 8 (v1.2) + 8 (v1.3) + 8 (Phase 14, standalone)
- Average duration: -
- Total execution time: -

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 (v1.0) | 6 | - | - |
| 2-8 (v1.1) | 44 | - | - |
| 9 (standalone) | 6 | - | - |
| 0, 10, 11 (v1.2) | 8 | - | - |
| 12-13 (v1.3) | 8 | - | - |
| 14 (standalone) | 8 | - | - |
| 15-19 (v1.4) | TBD | - | - |
| 20-23 (v1.5) | TBD | - | - |
| 20 | 4 | - | - |
| 21 | 4 | - | - |
| 22 | 4 | - | - |
| 23 | 4 | - | - |
| 24 P01 | 32min | 3 tasks | 4 files |
| 24 P02 | 28min | 4 tasks | 7 files |
| 24 P03 | 25min | 3 tasks | 7 files |
| 24 P04 | 47min | 3 tasks | 7 files |
| 24 P06 | 41min | 3 tasks | 6 files |
| 24 P07 | 25min | 3 tasks | 7 files |
| 24 P11 | 35min | 3 tasks | 5 files |
| 24 P14 | 40min | 3 tasks | 5 files |
| 24 P17 | 45min | 3 tasks | 8 files |
| 25 P03 | 40min | 2 tasks | 3 files |
| 25 P06 | 16min | 3 tasks | 7 files |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- 25-06 (2026-09-12): **o `detail` do 402 de watchlist virou dict; o de
  `_gate_analise` continua string — e a fronteira está travada por teste.** Não
  é inconsistência por descuido: o app lê o texto do gate de análise DIRETO
  (`enrichErrorMessage` e o fallback determinístico do FIX-C01), então um dict
  ali mostraria `[object Object]`. Nas duas rotas de watchlist o texto continua
  chegando igual (a `message` do dict é a base que o `enrichErrorMessage` usa),
  e o número passa a viajar junto.

- 25-06 (2026-09-12): **`usado` significa a MESMA coisa nas duas rotas de
  watchlist** — quantos ativos a conta tem HOJE, contra a letra do plano (que
  pedia o tamanho PEDIDO no PUT). O campo é lido por um componente
  compartilhado: um sentido por rota daria número certo numa tela e errado na
  outra. Conta grandfathered publica `usado: 15, limite: 10` — truncar no teto
  fabricaria número e esconderia o único caso em que os dois divergem.

- 25-06 (2026-09-12): **plano é tile no grupo Conta do Perfil, nunca badge
  global.** A razão não é estética: plano muda raríssimo (hoje só por
  atribuição manual da administração), e um badge permanente para um dado quase
  nunca consultado cobra carga cognitiva em TODA tela pela estética de freemium
  agressivo que o ADR-010 (decisão 4) proíbe. Pelo mesmo motivo não há CTA de
  upgrade em lugar nenhum: não existe loja/IAP, e o botão prometeria o que não
  se cumpre.

- 25-06 (2026-09-12): **sem mapa id → nome de exibição de plano no front.** O
  app já mostra o id cru ao usuário ("do plano free") e duas vozes para a mesma
  coisa divergiriam; um mapa também seria uma segunda lista de planos, velha no
  dia em que existir um terceiro — mesmo raciocínio do guardião do portal
  (25-05).

- 25-04 (2026-09-12): **a precedência de um limite é decidida pela ORIGEM do
  valor, não pelo valor existir.** `plan.limites_do_plano()` devolve algo para
  os cinco pontos SEMPRE — com `origem: "default"` quando nada foi
  configurado. Usar esse valor por ele existir faria o default do catálogo
  passar na frente do `llmDailyQuota` que o admin digitou no painel; os números
  coincidem hoje, então o defeito ficaria invisível até alguém mexer no painel,
  e aí o painel confirmaria uma configuração que não vale. Só `origem == kv`
  (a chave carrega o id do plano) ou `env` com `{PLANO}` no molde vencem o
  resolvedor global.

- 25-04 (2026-09-12): **o `detail` do 402 continua sendo string.** O plano
  oferecia duas vias para o código estruturado (`detail.code` ou marca na
  exceção); a primeira foi descartada com medição — o app lê `e.detail` como
  TEXTO (`enrichErrorMessage`, e o fallback determinístico do FIX-C01), e um
  dict viraria `[object Object]` na tela. O carimbo viaja como atributo da
  exceção (`marcar_o_limite`, o padrão do `ATR_DEBITADO` que o próprio módulo
  já tinha) e some na serialização: o texto que chega ao usuário não muda.

- 25-04 (2026-09-12): **D3 — o `owner` é consultado DEPOIS de o gate negar.**
  Resultado observável idêntico ao de perguntar antes, e o caminho feliz não
  paga uma consulta de papel por requisição de IA. Sem cache, porque o ADR-013
  escolheu revogação imediata acima de latência — papel cacheado é papel que
  vale depois de revogado. Fail-closed: falha de leitura mantém a conta
  barrada; errar para o lado de barrar o dono é aborrecimento, errar para o
  outro libera o cap comercial da base inteira num banco intermitente.

- 25-04 (2026-09-12): **`opcoes.criar_setup` NÃO migrou do RBAC para o plano
  (D2)** — escopo reduzido a pedido do Alex ("da forma mais segura e rápida"),
  registrado como pendência nomeada e não como esquecimento. Liberar por plano
  AMPLIARIA o acesso: qualquer conta `pro` gravaria no armazém compartilhado do
  serviço MCP (2.000 `tools/call`/dia para a base inteira). `funcoes_do_plano`
  segue pronta e não lida; a migração exige mexer em `GRUPOS["opcoes"]`,
  `ENTIDADES_POR_PERMISSAO` e `test_opcoes_dsl.py:341-348`.

- 25-03 (2026-09-12): ponteiro para código inexistente é pior que ausência, e
  dois mecanismos para a mesma decisão garantem o dia da divergência.
  `plan_at_least` foi **removida** — órfã desde que nasceu, citando um
  `require_plan()` que nunca existiu em `main.py` (é esboço do ADR-013, não
  código), e a D2 já escolheu outro mecanismo para gate de função: conjunto de
  funções por plano, não ordem de tier. O ADR não foi tocado (é história); a
  remoção e a razão ficaram datadas na docstring de `plan.py`, com teste que
  proíbe a volta. `_ORDEM_PLANO` sobreviveu porque tem consumidor real.
  No mesmo plano, duas divergências DELIBERADAS do padrão copiado
  (`options_mcp_api._valor_e_origem`), ambas escritas no código: `0` aqui é
  valor legítimo (é como um plano bloqueia um ponto de controle) e não lixo; e
  `None` aqui é valor ("sem limite"), então o "não achei" virou um sentinela
  próprio — sem isso, "plano sem limite" viraria "plano não configurado" no
  primeiro ida e volta pelo kv.

- 24-17 (2026-09-12): reversão de decisão se REGISTRA, não se apaga — e o
  freio que não existe ao lado não se inventa aqui. O override de plano,
  recusado no ADR-013, entrou como rota irmã da de papéis; as quatro notas
  que diziam "sem override nesta rodada" ganharam a data da virada em vez de
  sumir. Mudar o próprio plano continua permitido e auditado: quem tem
  `usuarios.gerenciar` já concede a si mesmo qualquer papel de governança pela
  rota ao lado, e o registro do autor é a mitigação que o ADR-013 escolheu
  para essa classe — um freio só aqui seria assimétrico. A lista de planos
  ficou no backend (`planosDisponiveis`), pelo mesmo motivo de sempre: a
  segunda cópia é a que não acompanha.

- 24-15 (2026-09-12): a env não sai quando o painel entra — ela vira camada.
  Os três tetos da aba Opções passaram a ser configuráveis sem deploy
  (memória → kv → env → default), e o kv entra NA FRENTE da env, nunca no
  lugar dela: é como o Railway troca um teto sem publicar código. O que
  fecha a decisão é a ORIGEM publicada junto do número — sem ela o admin
  muda pelo painel, a env continua dizendo outra coisa, e as duas verdades
  convivem sem ninguém saber qual manda. Valor acima do teto do SERVIÇO
  (2.000/dia, compartilhado por toda a base) é aceito com aviso, não
  recusado: recusar fingiria um controle que o Boris não tem.

- 24-14 (2026-09-12): "zero por construção" não é "zero por raridade", e a
  diferença é dita ANTES do número. O ensaio de um setup cuja condição nunca
  fechou a janela devolvia `disparos: 0` com `pregoes_avaliaveis: 31` — os
  dois certos, e por isso mesmo enganosos. O aviso afirma só o que a
  aritmética de janela demonstra e cala onde a prova não alcança (`OR`,
  sequência curta); nenhuma lista de indicadores entrou no Boris (a detecção
  sai do `window` que a condição declara, ENG-06); e a tela NÃO bloqueia a
  gravação — impedir a conclusão errada é dever dela, decidir pela pessoa
  não é.

- 24-12 (2026-09-11): a DISTÂNCIA medida vence o SLA herdado. O frescor do
  fornecedor responde "a carga está dentro do contrato dele"; a pessoa
  pergunta "de quando é este número?". São perguntas diferentes, e repassar a
  primeira como se fosse a segunda foi o que produziu "dado em dia" sobre
  cotação de dois pregões atrás. O chip passa a dizer a distância; quando o
  serviço TAMBÉM bloqueia, as duas informações somam em vez de competir.

- 24-12 (2026-09-11): o carimbo INFORMA, não bloqueia. Quem barra veredito e
  criação de setup continua sendo o frescor do serviço (ADR-027, Decisão 8) —
  mudar o critério de bloqueio seria outra decisão, e o guardião de rota
  afirma `frescor.bloqueia is False` no cenário com atraso medido. E o dia
  corrente nunca entra na conta: alerta que toca toda manhã deixa de ser lido.

- 24-06 (2026-09-11): a razão ganho/perda é ADIMENSIONAL e o helper não
  recebe `lote` — a assinatura é a trava, não um teste. Razão que não existe
  é `None` COM motivo (ganho sem teto, perda sem piso, dado ausente, perda
  zero); número inventado ali seria o defeito que o critério 2 do ROADMAP
  proíbe. Em `/proposta` ela segue a régua de ambiguidade do `emReais` (uma
  estrutura só), não a de lote.

- 24-06 (2026-09-11): `except Exception` em torno de `llm._call_llm` é
  deliberado e justificado NO CÓDIGO — o provedor é código de terceiro cuja
  taxonomia de exceção não é do Boris, e o critério 7 do ROADMAP é literal
  ("nada cai no handler 500"). As classes de transporte conhecidas
  (`httpx.TimeoutException`/`HTTPError`) ficam NOMEADAS acima do genérico.

- 24-06 (2026-09-11): contabilidade nunca derruba rota cuja escrita externa
  JÁ foi efetivada. `audit.record` virou `_audita()` com try/except + obslog
  `warn`: o armazém de setups é sem dono (ADR-027, Decisão 7), então o 500
  convidava à retentativa e a retentativa duplicava o setup para toda a base.

- 24-07 (2026-09-11): **F-04 DECIDIDO pelo Alex — cobrar a viagem que a tool
  recusou.** Das três saídas possíveis (cobrar; cachear a recusa com TTL
  curto; teto de falhas por requisição em `/possibilidades`), vale a
  primeira; as outras duas foram descartadas nesta rodada e `mcp_client.py`
  ficou com 0 linhas alteradas. O critério passou a ser literal: *tocou a
  rede, debitou*. A regra vive em UM ponto (`_chamada_com_cap`), e as quatro
  falhas sem viagem provada seguem sem debitar — cobrar o que não se sabe se
  foi cobrado é o mesmo erro, invertido.

- 24-07 (2026-09-11): afirmação de cobrança nunca é literal fixo. O campo
  `cobrado` do 422 vem de uma marca posta no ponto do débito, porque nem todo
  `McpErroDeTool` nasce de uma `tools/call` — `_material_do_compilador`
  fabrica um quando o serviço não publica o schema, e ali nenhuma viagem
  contável aconteceu. Guardião em `test_opcoes_dsl.py`.

- v1.4 roadmap (2026-09-02): numeração de fase continua a partir da última
  fase standalone (14, Opções lastreadas) — Phases 15-18, sem
  `--reset-phase-numbers`. v1.3 (12-13) e Phase 14 arquivadas em
  `.planning/milestones/`.

- v1.4 roadmap: 4 fases derivadas na ordem engine → estruturas → aceite →
  navegação — ENG-01..06 (Phase 15, motor sem UI) primeiro porque
  NAV-02/03 e FLOW-01 precisam do formato de saída do motor existir antes;
  LIB-01..03 (Phase 16) generaliza os motores single-leg já em produção
  (Fase 14) para N-pernas + collar; FLOW-01..04 (Phase 17) exibe a
  proposta via o mecanismo de card já existente (AtivoCard, Fase 14) antes
  da aba dedicada existir; NAV-01..03 (Phase 18) só entra por último, como
  casa definitiva de um fluxo que já funciona.

- v1.4 roadmap: Phase 16 success criteria deliberadamente distintos de
  Phase 15 — não repetem "o motor calcula payoff" (isso é Phase 15), e sim
  o que a biblioteca especificamente contribui (generalização N-pernas +
  collar como nova composição), correção feita após revisão do advisor
  antes de escrever os arquivos.

- [Phase 24]: 24-01: /possibilidades reserva cap em duas etapas (1 + 2xN) — N so se conhece depois da primeira chamada
- [Phase 24]: 24-01: conversao por lote fica no backend; breakeven nunca entra em emReais (e preco do objeto, nao dinheiro)
- [Phase 24]: 24-02: o eixo X do payoff e mapeado por PRECO, nao por indice
- [Phase 24]: 24-02: a curva so se estende alem do ultimo strike quando o servico declarou os DOIS lados limitados
- [Phase 24]: 24-03: o system do compilador se monta em RUNTIME do inputSchema vivo — nenhum vocabulario de DSL dentro do Boris (ENG-06 aplicado a prompt)
- [Phase 24]: 24-03: description do setup e sempre a palavra da pessoa; a parafrase da IA e descartada antes de gravar
- [Phase 24]: 24-03: frescor bloqueia CRIAR setup e nao bloqueia DESATIVAR — assimetria deliberada, travada por teste
- [Phase 24]: 24-03: rota de escrita sem a fiacao de permissao responde 503, nunca 200 permissivo
- [Phase 24]: 24-04: a permissao ESCONDE a secao de criar setup; quem RECUSA e o backend — gate provado por RENDER, nao por grep
- [Phase 24]: 24-04: recarregar a leitura depois de gravar usa contador PROPRIO (leituraRef) — bumpar tickerRef invalidaria a propria chamada que pediu a recarga
- [Phase 24]: 24-04: as condicoes do setup sao renderizadas varrendo as chaves que CHEGARAM; traduzir indicator/operator criaria a segunda copia do contrato (ENG-06 no front)
- [Phase 24]: 24-04: backtest e contagem passada — ressalva FIXA no mesmo bloco dos numeros, sem verde/vermelho, e as tres frases de expectativa banidas da pasta

### Roadmap Evolution

- Milestone v1.5 roteirizado (2026-09-05): Redesenho de UI em 4 fases
  (20-23), numeração continuando a partir da Fase 19 do v1.4 (sem
  `--reset-phase-numbers`, diretórios 15-19 intocados). Fatoração: 20 =
  camada global/estrutural (FIX-01/02, SYS-04, TYPO-01/02/03, MOTION-03),
  porque mexe no shell/`GlobalStyle`/tokens que as outras três consomem;
  21 = duplicação removida e Portfólio consolidado (DEDUP-01/02/03,
  FIX-03 — mesmo componente `CapitalCurve` do DEDUP-01); 22 = componentes
  compartilhados (SYS-01/02/03), independente da 21; 23 = motion com
  propósito + ilustração (MOTION-01/02, ILUS-01), por último porque depende
  do gate de `prefers-reduced-motion` da 20 e dos componentes unificados da

  22. Nenhuma fase toca `server/app/*.py` nem contrato de API.

- Risco nomeado no roadmap do v1.5: as Fases 17/18/19 do v1.4 editam o mesmo
  `web/src/App.jsx` e não foram enviadas a `origin` nem verificadas ao vivo;
  publicar o front de qualquer fase do v1.5 empurra esse trabalho junto no
  mesmo bundle. A decisão a/b/c registrada em Blockers vale para o v1.5
  também.

- Milestone v1.4 aberto (2026-09-02): Opções v2 — nova experiência que
  propõe setups (venda coberta, put de proteção, collar) a partir da
  análise técnica sobre posições reais da carteira, independente do MCP
  externo (b-mcp) até ele ficar pronto. 4 fases: 15 (motor de proposta,
  sem UI), 16 (biblioteca de 3 estruturas), 17 (fluxo de aceite via card
  existente), 18 (aba própria "Opções" na navegação).

- Roadmap revisado em 2026-09-03, depois de verificar a Fase 15/16/17 e
  produzir mockup + revisão com `navigation-specialist` pra Fase 18: a
  barra inferior real tem 5 abas (não 4, presumido em 01/09) — Candidato A
  ("aba própria Opções") descartado. Fase 18 passa a ser "seção dentro de
  Posições" (tira "Oportunidades de opções" + detalhe por posição),
  validado em 2 iterações de mockup com o Alex (artifact
  `https://claude.ai/code/artifact/16ae7543-c58e-4b7f-b164-f8923efa431b`).
  NAV-01..03 reescritos em REQUIREMENTS.md pra essa forma.

- Fase 19 registrada em 2026-09-03 (decisão explícita do Alex: "Registrar
  como nova fase", em resposta a "no detalhamento da proposta deveríamos
  poder mostrar uma série de setups de opções para a análise do ativo") —
  o motor hoje devolve UMA estrutura por posição (regra fixa de
  `plano.decisao`, ENG-01, Fase 15 verificada, não reaberta); Fase 19
  generaliza pra N candidatos, aditivo sobre `opcoes_motor.rastrear()`/
  `avaliar()`. Novos requirements MULTI-01/02 em REQUIREMENTS.md, success
  criteria detalhados ficam pra `/gsd-plan-phase 19`. Ordem confirmada:
  Fase 18 (navegação, formato hoje single-candidato) primeiro, Fase 19
  (multi-candidato) depois — leitura literal da instrução do Alex, sem
  reordenar sem pedido explícito.

- v1.3 e Phase 14 (standalone) arquivadas em
  `.planning/milestones/v1.3-phases/` e
  `.planning/milestones/phase-14-opcoes-lastreadas/` nesta mesma sessão,
  já que o `/gsd-complete-milestone` anterior não tinha arquivado.

### Pending Todos

- `medir-rate-limit-mydata.md` (priority medium) — acompanhar volume real
  de tráfego de opções se crescer; sem relação direta com v1.4, mas o
  motor de proposta da Phase 15 consulta o hub mydata via o mesmo lock.

### Blockers/Concerns

- **Opções apagadas em produção pelo gate de liquidez — RESOLVIDO e EM PRODUÇÃO
  (F10-20260908-02, deploy 2026-09-08; gate ao vivo confirmado).** Com `B3_OPTIONS_PROVIDER=mydata`
  o `liquidity_score` perdia o `oi_score` inteiro (COTAHIST não publica open
  interest) e levava a penalidade de 25 por "spread desconhecido"; teto 35
  contra corte 40, impossível em qualquer volume — os 60 contratos de PETR4
  empatavam em 35,0. Quick `260908-bzf` mediu; `260908-dnl` recalibrou o score
  (volume carrega sozinho, OI substitui quando existe, livro byte-idêntico);
  `260908-ldg` trocou o corte binário por TRÊS FAIXAS com consentimento
  explícito em DIFÍCIL e bloqueio servidor-side em SEM MERCADO — o usuário
  vê o grau e decide, o simulador nunca inventa um fill. Contra as 20 cadeias
  reais: 282 NEGOCIÁVEL / 227 DIFÍCIL / 83 SEM MERCADO. PR #32 mesclado e promovido em 2026-09-08; `/api/options/gate/PETR4` devolve
  `liquida: true, faixa: NEGOCIÁVEL, melhorScore: 75`. Pendência humana:
  exercitar o confirm de consentimento no aparelho (nunca tocado ao vivo). Pendência de raiz (open interest de verdade) é ingestão do MyData.
  Números: `docs/MEDICAO-gate-liquidez-mydata-2026-09-08.md`.

- 3 itens de backlog pré-existentes bloqueados por dependência humana
  (verificação ao vivo de `entradaAuto`; 2 human-checks da Fase 3) — não
  relacionados a v1.4, seguem em PROJECT.md Active.

- **Fase 17, checkpoint humano (Task 2, `17-06-PLAN.md`) — ADIADO, não
  aprovado.** App local subiu sem erro (bump `F10-20260903-01`, suíte
  canônica 2010+web verde), mas o mercado estava fechado no momento da
  tentativa — cadeia de opções ao vivo indisponível pra exercitar o roteiro
  de 10 passos (payoff real, collar por caixa insuficiente, aceite/
  cancelamento, Radar vs. Watchlist, iPhone). Alex instruiu seguir pra Fase
  18 mesmo assim, risco aceito conscientemente — não é aprovação. Retomar
  o roteiro com o mercado aberto antes de considerar a Fase 17 fechada de
  verdade; push da Fase 17 pra origin segue não feito.

- **Fase 18, checkpoint humano (Task 2, `18-05-PLAN.md`) — PENDENTE, parcialmente
  exercitado ao vivo no iPhone (2026-09-03).** App local publicado com sucesso
  (bump `F10-20260903-02`, suíte canônica 2010+web verde depois da
  publicação). Build instalado no iPhone via `scripts/instalar-iphone.sh`
  (dev local, não TestFlight — localhost não tem dado de mercado real pra
  checar, motivo dado pelo Alex). Confirmado ao vivo, conta real com
  posições: a tira "Oportunidades de opções" aparece em Posições, mostra o
  estado vazio explícito correto (NAV-03) — texto de "cobertura líquida
  existe, mas nenhum setup técnico ativo hoje" (não o de falta de
  cobertura) — nenhuma caixa em branco/silêncio. Isso verifica o fan-out
  gate→proposta (hook `useOpcoesPropostas`, Plano 18-01) e a lógica de
  estado vazio (Plano 18-03) funcionando de ponta a ponta com dado real.
  **Ainda NÃO verificado** (nenhuma das posições reais do Alex tem proposta
  ativa hoje, então esses passos do roteiro de 10 seguem pendentes): tira
  COM item real, manchete idêntica à Watchlist, toque abre no card certo
  (NAV-02), aceite em Modo Operador, Modo Estudo sem CTA, collar por caixa
  insuficiente, Watchlist/Radar intocados. Decisão a/b/c sobre o risco
  herdado da Fase 17 também segue em aberto. Nenhum push pra `origin` foi
  feito. A fase não está fechada até o roteiro completo (o que exige um dia
  em que o Radar dispare um setup ativo sobre alguma posição real do Alex,
  ou teste num ativo/conta com proposta ativa).

- **Fase 19, checkpoint humano (Task 2, `19-04-PLAN.md`) — PENDENTE, não
  exercitado (2026-09-04).** Motor multi-candidato executado e publicado:
  `propor()` devolve `candidatos` (put_protecao + collar em paralelo quando
  ambos cabem, MULTI-01), rotas de leitura/escrita falam a língua de N
  candidatos e fecham o gap put→collar (MULTI-02), front renderiza os N
  lado a lado em `PropostaDaPosicao`/`CandidatoOpcao` reusando o padrão
  visual da Fase 18. Suíte canônica verde (2021 passed, 1 skipped + web
  ok), build `F10-20260904-01` publicado (`server/web_dist`, três elos de
  carimbo coerentes). **Roteiro de 10 passos do Plano 19-04 ainda não
  rodado** — exige mercado aberto E uma posição real com leitura
  VENDER/baixa cujo caixa comporte tanto a put isolada quanto a trava
  protetora (só assim os dois candidatos aparecem juntos); sem isso os
  passos 1-7 não são exercitáveis. Decisão a/b/c do passo 10 (publicar
  Fases 17+18+19 juntas / segurar até 17+18 fecharem / reprovar) segue em
  aberto — **esta fase amplia exatamente o mesmo fluxo de aceite que as
  Fases 17/18 ainda não confirmaram ao vivo**, então a decisão pendente
  cobre agora as três fases empilhadas, não só 19. Nenhum push pra
  `origin` foi feito.

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260901-r5t | Registrar decisão: Alex escolheu Candidato A (aba própria Opções) na navegação de Opções v2 | 2026-09-01 | da9a118 | Verified | [260901-r5t](./quick/260901-r5t-registrar-decis-o-alex-escolheu-candidat/) |
| 260901-u2c | Registrar decisão: escopo v1 biblioteca de setups (venda coberta+put+collar), espaço pra MCP futuro | 2026-09-02 | f29490b | Verified | [260901-u2c](./quick/260901-u2c-registrar-decis-o-escopo-v1-biblioteca-d/) |
| 260902-km8 | Registrar estratégia de arquitetura: Boris independe do b-mcp até o serviço MCP autenticado ficar pronto | 2026-09-02 | 36cc1d1 | Verified | [260902-km8](./quick/260902-km8-registrar-estrat-gia-de-arquitetura-bori/) |
| 260905-1gb | Corrigir crash `cp is not defined` em HistoricoScreen (achado em auditoria de design ao vivo) | 2026-09-05 | 2715f9a | Verified | [260905-1gb](./quick/260905-1gb-corrigir-crash-cp-is-not-defined-em-hist/) |
| 260906-rla | Corrigir contraste WCAG AA de `textDim` no tema claro (Modo Estudo) — achado colateral da Fase 4/FIX-C16, 4,20:1→4,67:1; guardião de contraste estendido de `textFaint` para `textFaint`+`textDim` | 2026-09-06 | 503363f | Verified | [260906-rla](./quick/260906-rla-corrigir-contraste-wcag-aa-de-textdim-no/) |
| 260906-ugb | Corrigir 3 achados Baixo do REPORT-01: C-18 (`aria-describedby` no gate "Executar"), C-08 (reversão à média nomeada no verbete `setup-ifr2`); C-28 reverificado e encontrado já resolvido (nenhum código mudou) | 2026-09-06 | 9a874c5 | Verified | [260906-ugb](./quick/260906-ugb-corrigir-3-achados-baixo-do-report-01-c-/) |
| 260906-vf9 | Corrigir 3 achados de PRODUTO do REPORT-01 (C-07: "Operador IA" nomeado em `ModoTrabalhoCard`; C-09: aviso de drawdown >15% em `CapitalCurve`, limiar decidido pelo orquestrador; C-06: `resumoOperacao(h)` — escopo reduzido a uma frase no Histórico existente) | 2026-09-06 | 72187df | Verified | [260906-vf9](./quick/260906-vf9-corrigir-3-achados-de-produto-do-report-/) |
| 260907-w33 | Corrigir estouro de largura do card de candidato de opção (achado ao vivo em staging/iPhone com put_protecao + collar): `flex: "0 0 210px"` nos dois trilhos de opções, CUMPRINDO a Decisão 1 do 22-UI-SPEC em vez de revertê-la — `minWidth` sempre foi piso, nunca teto. Guardião da asserção 7 intocado. Publicado em F10-20260908-01 | 2026-09-07 | (merge) | Published | [260907-w33](./quick/260907-w33-corrigir-estouro-de-largura-do-card-de-c/) |
| 260907-x69 | Corrigir os textos do card de FECHAMENTO de operação lastreada (achado ao vivo em staging/iPhone): a manchete de fechar uma put dizia "Comprar 1 put(s)…" acima de um botão que VENDE, e o CTA/confirmação falavam em "recomprar a call" e "destrava ações" para uma put que nunca travou ação. Frases `fechar_call_coberta`/`fechar_put_protecao` nos DOIS modos de `skill_ref`; `tipo`/`motivo` intocados (contrato de ~9 guardiões de igualdade exata). O dinheiro já estava certo (`side=="comprada"` → `store.sell_option`, credita) — defeito só de texto. **Dois guardiões afirmavam o texto errado** e foram atualizados com nota datada, não apagados. Publicado em F10-20260908-01 | 2026-09-07 | a90e0bf | Published | [260907-x69](./quick/260907-x69-corrigir-textos-do-card-de-fechamento-de/) |
| 260908-bzf | Documentar que o gate de liquidez de opções ficou IMPOSSÍVEL de cruzar com `B3_OPTIONS_PROVIDER=mydata` (medido em produção ao vivo): os 60 contratos de PETR4 empatam em `liquidity_score=35,0` contra corte 40 — `oi_score` some (COTAHIST não publica open interest) e a penalidade de spread cai no padrão 25 porque o livro vem com um lado zerado. Teto 35 < corte 40, nenhum volume cruza. Fecha o follow-up aberto do ADR-020. **Documentação apenas** — recalibrar o gate é decisão de produto, adiada pelo Alex | 2026-09-08 | — | Documented | [260908-bzf](./quick/260908-bzf-documentar-gate-de-liquidez-impossivel-c/) |
| 260908-dnl | Recalibrar `liquidity_score` para fonte sem open interest (opção 1, escolhida pelo Alex logo após a bzf): atividade = `max(curva(volume), curva(OI))` numa curva única até 75, livro byte-idêntico, corte 40 inalterado; piso sem livro = 1.000 unidades (onde a curva original saturava). Primeira candidata (penalidade de desconhecido 10) descartada por virar pass-through nas 20 cadeias reais. Contra produção: gate 18/18 (antes 2/18), 461/592 contratos (antes 3/592). Dois guardiões atualizados com nota datada, guardião novo com critérios fixados antes dos dados; mock fiel ao mydata (OI None, volume 5000) em commit separado. Suíte 2064 passed. **Em produção desde 2026-09-08 (F10-20260908-02)** | 2026-09-08 | (2 commits) | Deployed | [260908-dnl](./quick/260908-dnl-recalibrar-liquidity-score-para-mydata-s/) |
| 260908-ldg | Gate de liquidez em TRÊS FAIXAS com consentimento (quadro confirmado pelo Alex): NEGOCIÁVEL ≥55 normal · DIFÍCIL 30–54 aparece com a nota, só é selecionado se não houver negociável, e exige `window.confirm` próprio + `aceitaLiquidezDificil: true` no corpo (servidor recusa 400 sem o flag) · SEM MERCADO <30 bloqueado sem override (princípio 4). Limiares centralizados em `options_quant` (55/30, `faixa_de_liquidez`); `rastrear` em duas passadas; `proposta.liquidez` ganha faixa/volume/spreadPct/aviso com frase de `skill_ref` nos dois modos; ramo OFFLINE do `deviceStore` aplica a mesma régua (era o buraco real de paridade); verbete determinístico `liquidez-opcao`; guardião AST prova que o agente não abre estrutura. Fechamento NÃO bloqueia por faixa (deliberado). 12 guardiões atualizados com nota, 46 novos; plan-checker pegou 2 fatos errados do planner (fixture do collar é mista 67/53; 1.000 un. sem livro é DIFÍCIL). Contra as 20 cadeias reais: 282/227/83; RADL3 cai na 2ª passada. Suíte 2110 passed. **Em produção desde 2026-09-08 (F10-20260908-02); gate ao vivo confirmado — PETR4/ABEV3/VALE3/ITUB4 NEGOCIÁVEL, RADL3 DIFÍCIL 50,9** | 2026-09-08 | (3 commits + merge) | Deployed | [260908-ldg](./quick/260908-ldg-gate-de-liquidez-em-tres-faixas-com-cons/) |
| 260909-bwm | Script master de distribuição iOS (`scripts/distribuir-iphone.sh`): localiza o worktree onde `main` está checked out (`git worktree list --porcelain` — este worktree não pode `git checkout main`), fast-forward de `origin/main` (diverge → morre, nunca merge/rebase automático), suíte canônica antes de empacotar, builda contra PRODUÇÃO (nunca staging), sincroniza, e SÓ ENTÃO pergunta o canal — Xcode direto no aparelho × TestFlight. Flag `--no-open` nova em `instalar-iphone.sh` (compat total sem ela). Nunca flipa APNs pra produção sozinho — lê `aps-environment` e avisa se TestFlight for escolhido com push ainda em development. `bash -n` OK nos dois scripts; localização do worktree testada isoladamente (resolve certo). **Rodado ao vivo pelo Alex logo depois**: achou um bug real (caminho do entitlements no resumo final, `ios/App/App.entitlements` faltando um nível `App/` — sempre imprimia "ausente" mesmo com o valor certo no arquivo), corrigido no mesmo dia (commit `60cd0e0`, PR #34, mesclado). Rodou de novo com `--testflight`: canal escolhido corretamente, build 10 gerado, resumo agora lê `aps-environment: development` de verdade | 2026-09-09 | (2 commits) | Deployed to main, run live | [260909-bwm](./quick/260909-bwm-script-master-atualizar-main-e-instalar-/) |
| 260909-dao | Documenta no `TESTFLIGHT.md` (item 7) que o **App Name** do App Store Connect é único NA LOJA INTEIRA, diferente do `CFBundleDisplayName` (nome sob o ícone, continua "Boris+"). Achado ao vivo: "Boris+" sozinho colidiu ("App Record Creation failed... already being used") — vários apps "Boris" já publicados. Alex escolheu **"Boris+ Simulador B3"** entre 4 variantes apresentadas. Documentação apenas, nenhum código tocado | 2026-09-09 | — | Documented | [260909-dao](./quick/260909-dao-documentar-nome-boris-simulador-b3-no-ap/) |
| 260907-vwl | Reforçar aviso visual de ordem pendente (achado ao vivo em staging/iPhone 2026-09-07 — compra de ABEV3 com mercado fechado, aviso "discreto" passou batido): bloco `color-mix(T.warn 14%)` reusando o pill PENDENTE, des-concatenado da frase de execução tudo-ou-nada, simétrico em BuyModal/SellModal; guardião estendido | 2026-09-07 | d78a0a5 | Tested (suíte canônica verde, sem --validate) | [260907-vwl](./quick/260907-vwl-reforcar-aviso-visual-de-ordem-pendente-/) |
| 260907-vzp | Corrigir `setups[0]` cru sem filtrar aposentado em `App.jsx` (ADR-017 Decisão 1) — achado ao vivo em staging (compra ABEV3 gravou `setupEntrada` contraditório, invertendo a leitura de invalidação); `setupOperavel()`/`metaDeEntrada()` em `finance.js`, espelho de `setups.py:725` | 2026-09-07 | ebd23b2, e8dd43e | Verified | [260907-vzp](./quick/260907-vzp-corrigir-setups-0-cru-sem-filtrar-aposen/) |
| 260909-oyu | Carimbo de horário das ordens em BRT (era UTC no Railway): `store.now_str()` (histórico de compra/venda, `abertaEm` das posições, 17 usos) e `main.now_str()` (cotações `at`, agent log, análises — 15 usos) usavam `datetime.now()` naive; container Railway em UTC → 3h à frente e, das 21:00 às 23:59, no dia seguinte. `obslog.ts` idem. Formato das strings preservado; registros antigos não reconvertidos. Guardião cruza a meia-noite UTC. Pendência mapeada: `candle_provider.py:61` e `scan_deep.py:29` (dia local como chave de "hoje") | 2026-09-09 | 88ba707, b129c4f | Tested (suíte canônica verde: 2114 pytest + 124 mjs) | [260909-oyu](./quick/260909-oyu-carimbo-ordens-brt/) |
| 260909-th4 | Bump manual de `SERVER_BUILD_ID` → `F10-20260909-01` para o deploy só-backend da correção de fuso (260909-oyu). `version.js` fica em `-20260908-02` por desenho. Deploy é clique do Alex no Railway; próximo bump de front hoje tem que ser explícito (`bump.sh F10-20260909-02`) | 2026-09-09 | 403d1a7 | Verified (import + pytest -k health) | [260909-th4](./quick/260909-th4-bump-server-build-id-fuso/) |
| 260909-tmi | Pedido do Alex: "mude todos os domínios para boris.semente.dev". Código/scripts já eram boris; trocados os remanescentes `bolsia.semente.dev`, `acamerini.app` e `b3-production-8fc0` em doc viva, comentários e fixtures (11 arquivos). Histórico protegido intocado. `mydata.acamerini.app` → `mydata.semente.dev` (outro serviço). Pendente FORA do repo: valor de `B3_GATED_HOSTS` no Railway e return URLs SIWA/Google | 2026-09-09 | abfa21c | Tested (suíte canônica: 2114 pytest + 124 mjs) | [260909-tmi](./quick/260909-tmi-dominios-para-boris-semente-dev/) |
| 260909-waw | **Aba Opções — Fase 1** (PLANO-aba-opcoes aprovado 2026-09-09): ADR-027 substitui a fronteira do ADR-024 (só serviço autenticado `mcp.semente.dev`, dado real, nunca fixture); `mcp_client.py` único importador de `mcp`/`httpx2` (token client_credentials à mão, cache, semáforo 4, mapeamento de erros); `options_mcp_api.py` com `GET /api/options/mcp/status`, cap por usuário/dia em seções próprias do `metering` (`mcpUsage*`, dia em SP); permissão `opcoes.criar_setup`; pins exatos de fastapi/starlette/pydantic/uvicorn (provado em 3.12 via pip download); guardiões A/B reescritos com nota. Decisão a avalizar: `/status` responde 200 com `bloqueia:true` em erro de tool. Achado alto deferido: `test_adr013_cobertura_rotas` cego a rotas de `include_router` no fastapi 0.141 | 2026-09-09 | 0568271, 0a38cda, 63d038b | Tested (2225 pytest + 124 mjs) | [260909-waw](./quick/260909-waw-aba-opcoes-f1-adr027-cliente-mcp/) |
| 260910-biz | **Aba Opções — Fase 2**: rotas `GET /api/options/mcp/leitura/{ticker}` (behavior+catalog+expirations+setups do ticker, estado `nao_avaliado` com motivo verbatim) e `/setups/{name}/grafico`; front novo em `web/src/opcoes/` (OpcoesScreen, SetupChart, useOpcoesMcp) + `chartutil.js` extraído; **Opções entra na barra no lugar de "Operador IA", que virou sub-tela do Portfólio** (`goAgente`, `carteiraView === "agente"`). 3 guardiões atualizados com nota (pet_ui, benchmark_curva, c07). Desvio: `paletteFor()` extraída porque `usePalette()` fora do Provider leria a paleta default | 2026-09-10 | 3aff231, 404f8e6, 3be7a30, 5de774c | Tested (2239 pytest + 126 mjs + vite build) | [260910-biz](./quick/260910-biz-aba-opcoes-f2-leitura-setups-troca-de-aba/) |
| 260910-d57 | Dois defeitos do cabeçalho da aba Opções, achados no teste ao vivo no iPhone: (1) o chip de frescor nascia com "não medido" como default e afirmava medição que nunca houve quando nenhuma resposta chegou — agora distingue as TRÊS origens (nada consultado omite o chip; `medido:false` mantém o texto, que aí é verdade; `medido:true` em dia/atrasado), e a fonte deixou de afirmar `mcp.semente.dev` sem resposta; (2) `leitura.erro \|\| status.erro` fazia o 404 da leitura mascarar o `mcp_nao_configurado` do status — agora `escolherErroOpcoes()` escolhe por acionabilidade (`code` conhecido do ADR-027 vence erro sem código). Guardião estendido com prova red/green | 2026-09-10 | b79ef75 | Tested (2239 pytest + 126 mjs + vite build) | [260910-d57](./quick/260910-d57-cabecalho-opcoes-chip-e-erro/) |
| 260910-mqs | **Achado CRÍTICO A-00 da auditoria de 2026-09-10**: `POST /api/buy` aceitava `qty` negativo ou zero e EXECUTAVA a ordem (`-500` era coagido ao lote mínimo por `max(100, ...)`, e o mesmo `max` em `pending_orders.criar_compra` engolia o negativo no ramo fora de pregão); `qty` não numérico vazava `ValueError` como 500. Guarda espelhando `/api/sell` (F10-20260819) e `/api/options/buy`, posta depois do ticker normalizado e ANTES de `get_quote` (pedido inválido não queima requisição do orçamento brapi). Contrato de `qty` ausente (lote 100) preservado e travado por teste. 5 testes novos, provados RED antes e GREEN depois. **Sem relação com a aba de Opções** | 2026-09-10 | 45fdbe3 | Verified (RED/GREEN + suíte 2244 pytest + 126 mjs) | [260910-mqs](./quick/260910-mqs-buy-qty-negativo-a00/) |
| 260910-red | **Achado ao vivo na primeira leitura real em produção**: a aba mostrava "frescor não medido" com o dado EM DIA. `(l && l.frescor) \|\| (status.dados && status.dados.frescor)` deixava a leitura vencer sempre, e sem setups gravados `_frescor_da_avaliacao` devolve `{medido:false, bloqueia:true}` — objeto verdadeiro que nunca cai para o `/status`, que MEDIU de verdade. Terceira ocorrência da mesma classe (escolha por origem em vez de qualidade); helper `escolherFrescor` espelhando `escolherErroOpcoes`. `pregao`/`fonte` intocados (verificado no backend: `propose_option_setups` roda sempre; só `evaluate_setups` é pulada). Prova RED/GREEN refeita pelo orquestrador, não aceita do executor | 2026-09-10 | b6c986f | Verified (RED/GREEN independente + 2244 pytest + 126 mjs + vite build) | [260910-red](./quick/260910-red-precedencia-do-frescor/) |
| 260910-svy | **Lote MCP da auditoria (A-01 a A-05)**: (A-01) `CODIGO_TETO` colidia com `CONNECTION_CLOSED` do SDK, ambos `-32000` — conexão caída virava 402 "atingiu o teto do dia", número afirmado sem medição; agora só é teto COM prova numérica (`chamadas_hoje`+`teto` em `data`), e falso-negativo é o lado seguro; (A-02) o ramo 401/403 era código morto no transporte streamable-HTTP — o SDK colapsa todo erro HTTP numa frase genérica, então a correção proposta (classificar pelo texto) NÃO era implementável: resolvido MEDINDO o status com event hook do httpx2 numa ContextVar por chamada; (A-03) as três rotas passaram a logar `detalhe=str(e)`; (A-04) `mcp==2.2.0`/`httpx2==2.12.0` nos dois manifestos, resolução provada em 3.12 — guardião APERTADO (exigia faixa, agora exige `==`, com nota); (A-05) token recusado é invalidado e renovado UMA vez, nunca em laço. Extra não pedido: `_trecho()` redige segredo da mensagem do serviço antes de logar, porque ela é entrada externa (um serviço hostil ecoando `Authorization` arrastaria o token para o log) | 2026-09-10 | ebc963f, 460aa50, 3fed1d5 | Verified (RED/GREEN do A-01 + 2256 pytest + 126 mjs + pins em 3.12) | [260910-svy](./quick/260910-svy-lote-mcp-auditoria/) |
| 260910-wfp | **Quatro achados de peso da auditoria**: (A-07) cota de IA estourava sob concorrência — `check` comparava mas não reservava, e `consume` só cobrava depois da resposta do modelo (até 60 s); agora há `METERING_LOCK` + reserva com TTL, no mesmo padrão do WR-01. **Achado novo do executor**: o `read-modify-write` de `consume` TAMBÉM perdia atualização, deixando o contador do usuário MENOR que a verdade e mascarando parcialmente o estouro. (A-08) o ciclo do Operador anunciava venda que não houve quando a posição sumia antes da venda (`pnl is None`): registrava no Diário, disparava push "vendido" e consumia o teto diário; agora só com `pnl` real, e emite `kind:"warn"` (que o push não filtra) distinguindo os dois motivos de `None` relendo o motor. (A-17) guardião de permissões enxerga rotas de router — cegueira original reproduzida e invertida; allowlist NÃO cresceu (as 4 rotas já estavam lá, nunca exercitadas). (A-18) filtro de comentário pega comentário de cauda, helper extraído das três cópias | 2026-09-10 | f377e62, 68b5bc5, a9994b9, 2d13333 | Verified (4 provas invertidas + 2273 pytest + 126 mjs) | [260910-wfp](./quick/260910-wfp-cota-agente-guardioes/) |
| 260911-lib | Fecha a decisão pendente do A-07 (**opção A, escolhida pelo orquestrador**): a reserva não consumida voltava só por expiração (120 s), e nas rotas da aba isso produzia falso "Cota do dia esgotada" — mesma classe do A-08. `_cap_check` virou gerenciador de contexto que devolve o saldo num `finally`. **Medição confirmou o relatório anterior com uma nuance**: a recusa na 21ª chamada do minuto era do rate limit, não da reserva; o que isola a causa é a janela 60–120 s (rate vencido, reserva viva). Invariante travado em teste: devolvido nunca excede reservado (liberar a mais daria cota de graça). Desenho de context manager escolhido também para preservar intacto o guardião AST que exige `_cap_check` em cada rota | 2026-09-11 | 5b9c980 | Verified (RED/GREEN do falso esgotado + 2281 pytest + 126 mjs) | [260911-lib](./quick/260911-lib-liberar-reserva-nao-consumida/) |
| 260911-15a | **Achados baixos da auditoria**: A-09 (venda de opção que falhou devolvia 200 com `priceUsed`) + resto do A-00b (`/api/options/buy` vazava `ValueError` como 500); A-10 (fuso em `candle_provider`/`scan_deep` — guardião crava 01:30 UTC = 22:30 BRT do dia anterior; o código naive nem respondia ao monkeypatch do relógio, e foi por isso que escapou de 260909-oyu); A-11 (trava preventiva no orçamento da brapi — inerte hoje, portada do padrão WR-01; `_gate()` da fatia `delta` NÃO foi convertido, mesmo precedente do mydata: recusa por orçamento não pode virar "sem dado"); A-14/A-15/A-16 (docs e comentários que mentiam sobre o código) | 2026-09-11 | 7055cbc, d2a008a, 0e8e63b, d6dbb08 | Verified (provas por reintrodução + 2297 pytest + 126 mjs) | [260911-15a](./quick/260911-15a-achados-baixos-auditoria/) |
| 260911-axj | **Achado ao vivo no painel admin**: quatro jobs (Radar diário, Avaliação de análises, Aquecimento de fundamentos, Intraday) apareciam como "nunca rodou" — eram dicts em MEMÓRIA do processo, zerados a cada reinício, e reiniciamos produção 4× hoje. `db.marcar_job`/`ler_job` (chave `jobMarcador:<nome>`, escopo global) + `status_snapshot` lendo do kv. **Precedência INVERTIDA em relação ao meu plano, e o executor estava certo**: memória vence kv, porque a gravação é best-effort — se o kv vencesse, uma escrita falha mostraria data MAIS ANTIGA que a realidade. Marcador só grava no sucesso (gravar no erro sobrescreveria execução real com `date: None`). Front NÃO tocado: a tela ganha o dado certo sem mudar uma linha | 2026-09-11 | 13fc28e | Verified (reinício real com `importlib.reload` + falha de escrita não derruba job + 2304 pytest + 126 mjs) | [260911-axj](./quick/260911-axj-marcadores-de-job-persistidos/) |
| 260911-cf1 | **D-1**: `/api/options/sell` tinha ABERTA a regressão F10-20260819 — `qty=int(_qty) if _qty else None`, e `0` é falsy: vendia a posição INTEIRA. Prova: antes HTTP 200 com `optionPositions=[]`; depois 400 com posição intacta. Contrato preservado (`qty` ausente = venda total, único caminho da tela) e travado por teste que passa nos dois lados | 2026-09-11 | c7bd2b8 | Verified (RED/GREEN + 2310 pytest + 126 mjs) | [260911-cf1](./quick/260911-cf1-venda-opcao-qty-zero/) |
| 260911-ctd | **Quinta e última da família do `qty` falsy**, achada pelo executor da 260911-cf1: `/api/options/lastreada/fechar` aceitava `contratos` 0/-3/"abc" e fechava a operação INTEIRA. Pior que as anteriores: o `isinstance` engolia o não numérico sem 500 (silêncio total), e **a tela MANDA esse campo** (`App.jsx:3529`) — as outras quatro só eram alcançáveis por chamada direta. Prova nos DOIS ramos (vendida/comprada): 6 casos fechavam tudo com 200 limpo; depois, 400 com posição intacta. O segundo falsy do ramo `comprada` (`if contratos_n`) virou `is not None`, senão a guarda ficaria pela metade. **Família de 5 rotas fechada** com a mesma guarda e a mesma string; varredura pós-correção não achou sexta | 2026-09-11 | 6e7dc35 | Verified (RED/GREEN dos 2 ramos + 2321 pytest + 126 mjs) | [260911-ctd](./quick/260911-ctd-fechar-lastreada-contratos/) |
| 260911-dcq | **D-2, parte 1**: os três carimbos de apuração que a UI EXIBE (`scanner.py:350`, `scan_deep.py:155`, `technical_snapshot.py:174`) usavam `time.strftime` sem fuso — 3 h à frente em produção, contra o princípio 3. Prova cruzando a meia-noite: `2026-09-10T01:30` virou `2026-09-09T22:30`. Formato mantido (a tela imprime cru). **Um dos três estava no MESMO arquivo que ganhou BRT nesta semana, poucas linhas acima** — a correção anterior foi por sintoma, não por classe; a varredura desta confirmou que não há quarto | 2026-09-11 | 5d2117a | Verified (RED/GREEN + 2326 pytest + 126 mjs) | [260911-dcq](./quick/260911-dcq-fuso-carimbos-visiveis/) |
| 260911-dtx | **D-2, parte 2 — a que mudava decisão**: `date.today()` naive em 5 pontos (+1 sexto achado pelo executor) fazia o prazo até o vencimento sair um dia a menos das 21h às 24h BRT. Prova de impacto no GATE, pelo caminho real: contrato de 15 dias era RECUSADO e passa a ser aceito; o de 61 era ACEITO indevidamente e passa a ser recusado; o de 22 perdia o `riskFlag` de vencimento curto. Os 4 módulos puros de opções NÃO foram tocados (guardião de fronteira) — a correção é nos chamadores, e as assinaturas ficaram congeladas por teste. **Defeito de ferramental achado junto**: `test_admin_summary.py` reimporta `app.main` e deixa o atributo do pacote apontando para outro objeto, fazendo relógio cravado não alcançar a rota — envenena qualquer teste de tempo futuro; fixture agora ancora em `endpoint.__globals__` | 2026-09-11 | 43dc815 | Verified (prova de impacto no gate + 2342 pytest + 126 mjs) | [260911-dtx](./quick/260911-dtx-fuso-dias-ate-vencimento/) |
| 260911-k9g | **Achado de uso, 3ª vez na mesma sessão**: o rodapé do Perfil mostrava só o `BUILD_ID` do FRONT, e como houve **5 deploys só-backend em 10-11/09** o app parecia desatualizado sem ter como provar o contrário. Agora mostra os DOIS carimbos (app e servidor, via `/api/health`, buscado ao montar a tela). Falha na consulta vira travessão — **nunca** o carimbo do front, que faria a tela afirmar uma versão de servidor não medida (a mesma classe corrigida 3× hoje). Comentário FASE 8B reescrito: ele afirmava que carimbo divergente = aparelho com código antigo, falso no deploy só-backend, e foi o que confundiu | 2026-09-11 | a003612 | Verified (regressão perigosa provada pega + 2342 pytest + 127 mjs + vite build) | [260911-k9g](./quick/260911-k9g-carimbo-do-servidor-no-rodape/) |
| 260911-pub | **Publicação do front** que entrega o k9g (merge dos 4 commits parados em `v2/interacao-estrutural` + `server/web_dist`, a única árvore que o Railway serve). Carimbo passado À MÃO (`F10-20260911-03`): sem argumento o `bump.sh` derivaria `-01` do `F10-20260910-02` do front e o `publicar-web.sh` **rebaixaria** o `SERVER_BUILD_ID` de `-02` para `-01`, porque iguala os carimbos sem comparar ordem — o aviso estava no comentário do próprio `main.py`, deixado pelo deploy anterior, e foi obedecido. `-01`/`-02` pulados de propósito. **Achado de ambiente**: suíte dentro do sandbox acusa 26 falhas FALSAS (`PermissionError` em `ssl.load_verify_locations`) — mesma causa do `x509: OSStatus -26276` do `gh`; fora do sandbox, verde | 2026-09-11 | 54d97b1 | Verified (executar.sh exit 0 antes e depois, carimbo nos 4 elos) | [260911-pub](./quick/260911-pub-mesclar-k9g-e-publicar-front/) |
| 260912-vle | Manual de utilização do Boris+, produzido na análise de UX de 12/09/2026, entra no repo como `docs/MANUAL-BORIS-PLUS.md` (261 linhas), cópia verbatim do artefato de scratchpad — `diff` vazio, exit 0. Documentação apenas, nenhum código tocado. Checagem de contradição das três afirmações "nesta versão": todas se sustentam contra o código atual — `opcoes` está fora de `PET_TELAS` (`server/app/conceitos.py:555`, confirma a Coruja não funcionar na aba Opções); nenhuma chamada a `/api/options/buy`\|`sell` em `web/src/opcoes/*.jsx` (confirma a leitura sem execução de ordem); `tourPassos` (`web/src/App.jsx:2433`) cobre só Bem-vindo/Radar/Watchlist/Portfólio, sem Acompanhar nem Opções. Nenhuma linha do manual editada. Suíte canônica no baseline exato (2682 passed, 5 skipped, 3 xfailed + 134 `.mjs`, exit 0) — 27 falhas dentro do sandbox eram o `PermissionError` de SSL já conhecido (260911-pub), confirmado e resolvido rodando fora do sandbox. Nada publicado, nada empurrado a origin | 2026-09-12 | — | Documented | [260912-vle](./quick/260912-vle-salvar-manual-de-utiliza-o-do-boris-em-d/) |
| 260914-b6p | **Bug de produção achado durante o checkpoint ao vivo da Fase 30**: o Alex testou a curadoria no iPhone (pós-deploy conjunto das Fases 27-30) e viu vazio mesmo com posições elegíveis. Investigação ao vivo via `railway run` contra o mydata real (não mock): `options_provider_mydata.get_options` escolhia `nao_vence_hoje[0]` confiando no campo `vence_no_pregao`, que vem `0`/falsy em TODOS os itens nos dados reais (medido: BBAS3 27 vencimentos, PETR4 31, `vence_no_pregao=0` em 100%) — então o código sempre pegava o primeiro item da lista por ordem de data, sem checar se já tinha passado. Numa segunda-feira, com o snapshot D+1 do mydata ainda mostrando a série de sexta, isso escolhia um vencimento 3 dias no PASSADO, fazendo `_dias_ate()` computar dias negativos e todo o filtro de janela (`15..60`) reprovar — vazio tanto na proposta única (Fase 14, produção há semanas) quanto na curadoria nova (Fase 30). Corrigido para filtrar por `dt.date` estritamente futuro, com `hoje` injetável (`hoje_brt()` default) e degradação explícita se não houver nenhum futuro — nunca mais escolhe vencimento vencido em silêncio. Regressão com a forma REAL de produção (não uma fixture conveniente com `vence_no_pregao=1`); um guardião que travava o comportamento ERRADO foi reescrito com nota de reversão, não apagado. Achado registrado, não implementado: mesmo corrigido, o primeiro vencimento futuro pode cair abaixo do piso de 15 dias (BBAS3 mediu 4 dias) — a cadeia default segue vazia por metade do ciclo mensal, agora por motivo legítimo. Suíte 2864 passed (+8), 147 `.mjs`, exit 0 | 2026-09-14 | 05e6ffa, f079bfd | Verified (regressão com forma real de produção + suíte canônica) | [260914-b6p](./quick/260914-b6p-corrigir-bug-de-selecao-de-vencimento-em/) |
| 260915-j5l | **Bug de produção achado pelo Alex logo após publicar a Fase 31**: os 4 cards da lista curada ("AS 4 MELHORES OPORTUNIDADES DE OPÇÕES") mostravam a estrutura mas o clique não executava nenhuma — `App.jsx:4237` fazia `onClick={() => onAbrir(item.ticker)}`, jogando fora `idCandidato`/`contractSymbol`/`tipo`/etc. e só rolando até o acordeão antigo de proposta única (pré-Fase-31), que só sabe executar o que aquele motor calcula (sempre venda coberta) — put de proteção, collar e a descoberto não tinham NENHUM caminho de execução. Decisão do Alex (AskUserQuestion): confirmação INLINE no próprio card. Módulo puro `executarCandidato.js` despacha por `item.tipo` para as 3 rotas já existentes e corretas (`lastreada/abrir`, `lastreada/abrir-collar`, `options/buy`), com corpo verificado direto no código do servidor, sem cálculo financeiro novo no front (prêmio/perda/breakeven vêm do candidato). Erro do servidor exibido verbatim (nunca reescrito); liquidez DIFÍCIL exige checkbox de consentimento antes de mandar `aceitaLiquidezDificil: true`; Modo Estudo sem botão de executar (espelha o 403 do servidor). 9 guardiões novos + 6 casos de despacho com store espião. Suíte canônica 2910 passed, 150 `.mjs`, exit 0; `vite build` verde. **Verificado ao vivo pelo orquestrador** (não confiado do SUMMARY do executor): clique → confirmação inline → Executar → posição real aberta via `/api/options/lastreada/abrir`, cash creditado (+R$130,00). **Em produção desde 2026-09-15 (F10-20260915-01)** — publicado direto em `main` desta vez (achado do dia anterior: `git push` na branch `v2/interacao-estrutural` sozinha NÃO chega à produção, Railway só observa `main`; a Fase 31 tinha ficado presa por isso e só foi ao ar quando percebido) | 2026-09-15 | 781ecf3, 423ee89, 9acb475 | Published | [260915-j5l](./quick/260915-j5l-corrigir-clique-nos-cards-da-lista-curad/) |
| 260915-ndt | **Continuação do j5l: o botão aparecia e executava, mas o collar SEMPRE dava 409** — achado pelo Alex testando em produção. Causa: DOIS motores de proposta com regras diferentes. `opcoes_curadoria.py:211-212` diz literalmente que ali "Deliberadamente NÃO há porta de setup/plano técnico... ao contrário de `propor()`"; já a rota `lastreada/abrir-collar` re-derivava via `opcoes_lastreadas.propor()`, que EXIGE endosso da leitura técnica. Resultado: todo collar da lista curada era rejeitado sempre que a leitura técnica não endossava collar — o caso comum. Reproduzido no print: a tira de cima dizia "a leitura técnica não indica venda coberta, put de proteção nem collar agora" enquanto a lista curada logo abaixo oferecia 4 collars em UGPA3. Só o collar sofria: venda coberta/put (`lastreada/abrir`) e a descoberto (`options/buy`) não re-derivam via `propor()` e já funcionavam. Decisão do Alex (AskUserQuestion): "re-derivar pelo motor certo". Rota NOVA `POST /api/options/curadoria/abrir-collar` (não flag no corpo — ADR-026 Decisão 1 já rejeitou esse anti-padrão, uma flag escolhendo QUAL motor valida seria pior), re-derivando por `opcoes_curadoria` via helper `_curadoria_scan_posicao` extraído de `_curadoria_top` (uma varredura só; duas divergiriam de novo). **Defesa anti-adulteração intacta e conferida pelo orquestrador linha a linha**: `strike`/`expiration`/`ivEntrada`/prêmios vêm do candidato re-derivado e da cadeia recém-buscada, NUNCA do corpo; `idCandidato` é só chave de busca; corpo só serve para cross-check. `permitir_a_descoberto=False` hardcoded. Rota antiga intocada. Junto: corrigido rótulo financeiro errado que o j5l introduziu — o painel usava `curadoriaRazaoRotulo` ("prêmio / perda máxima", uma RAZÃO) exibindo `premioTotal` em reais; mesmo rótulo mostrando duas grandezas na mesma tela. Agora chave própria `curadoriaPremioRotulo` ("prêmio líquido"). 13 testes novos, incluindo a prova central medindo os DOIS lados no mesmo cenário (rota velha 409 / rota nova 200, com 2 pernas reais abertas e caixa movido) + prova negativa do cross-check revertida. Suíte 2923 passed, 0 failed, 150 `.mjs`, exit 0 (baseline 2910). **Verificado ao vivo pelo orquestrador**: rótulo corrigido visível em 375px e venda coberta executada sem regressão (caixa 75.210→75.340). **Limite honesto**: o collar não foi clicado ao vivo localmente — com o provedor mock os 4 primeiros são sempre `call_coberta` e o collar nunca entra no top-4; a prova do collar é o teste de rota ponta a ponta + o teste do Alex em produção, onde o collar ranqueia no topo | 2026-09-15 | e8ccd72, 0743a37, 3768ebd | Published (F10-20260915-02) | [260915-ndt](./quick/260915-ndt-re-derivar-execucao-de-candidato-curado-/) |
| 260916-cod | **Fecha os achados do code review da Fase 32 e a dívida do item 8.** WR-01: a linha de chamada em Posições E o Bloco B da aba Opções afirmavam "nenhuma oportunidade"/"nenhuma estrutura elegível" no render ANTERIOR ao ligamento da flag monotônica `curadoriaAtiva` — resultado afirmado antes de a varredura começar, a mesma classe de erro que a própria Fase 32 corrigiu no estado de ERRO (princípio 4). `useCuradoria` passou a expor `concluido` e os DOIS call sites tratam `!concluido` como "ainda não medi"; `carregando` NÃO foi reusado de propósito (significa "requisição em voo"; sobrecarregá-lo traria de volta o "Verificando…" eterno). Provado ao vivo no caminho frio: "Verificando…" → "4 oportunidades…", nunca vazio precoce. Junto: imports órfãos e sombreamento de `item` removidos (+6 asserções reconciliadas em `test_curadoria_ui.mjs`, colateral do rename). **Item 8 FECHADO**: o ramo multi-candidato foi visto renderizando — a fixture era escolher a posição certa, não mexer em código, porque a coexistência put+collar exige plano de VENDER/baixa (`opcoes_lastreadas.py:247`) e as sessões anteriores só tinham testado alta/lateral; com ABEV3 os dois cartões apareceram lado a lado, mesma largura, medido no DOM. `32-VERIFICATION.md` passou de `human_needed` para `passed`. | 2026-09-16 | 5a35850 | Verified (produção, F10-20260916-02) | [260916-cod](./quick/260916-cod-fecha-achados-pos-fase-32/) |
| 260916-g6p | **Fecha a única ressalva aberta da Fase 32** (`deferred-items.md`): guard null-safe explícito substitui `|| 0` nas três cópias do helper `porLote`/CTA de collar (`CuradoriaEstruturas.jsx`, `CandidatoOpcao.jsx`, `PropostaLastreada.jsx`) — campo ausente agora renderiza "—" nunca "R$ 0,00" (princípio 4). Duas armadilhas medidas antes de editar: `Math.abs(null) === 0` exige o guard ENVOLVENDO `Math.abs`, não dentro dele; o CTA de collar alcança o ramo débito também com `p.caixa` falsy, então o `p.caixa &&` na frente tem de ficar. Exceção `ARQUIVOS_EXCECAO_OU_ZERO` removida do guardião `OU_ZERO`; `PropostaLastreada.jsx` (cópia original, Fase 28, nunca esteve na allowlist) entra na regra pela primeira vez, com prova negativa real (defeito reintroduzido à mão, guardião falhou nomeando o arquivo, revertido, guardião voltou a passar). Suíte canônica sem queda: 2923 pytest + 152 `.mjs`, idêntico à baseline da Fase 32 (rodada duas vezes: pós-fix e pós-bump). Alex confirmou a publicação explicitamente ("Pública"), separada do pedido do fix. **Em produção desde `F10-20260916-03`** (push nas duas branches, carimbo confirmado por HTTP) | 2026-09-16 | c584c96, 47b8907, bc2e03a | Published (F10-20260916-03) | [260916-g6p](./quick/260916-g6p-corrigir-os-tres-0-diferidos-da-fase-32-/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close (v1.3 → v1.4):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Backlog | 3 achados Baixo do REPORT-01 sem correção (C-10, C-17, C-29) — C-08 e C-18 corrigidos na quick task 260906-ugb (2026-09-06); C-28 reverificado e encontrado já resolvido (efeito colateral do refactor FIX-C21, sem mudança de código); C-06/C-07/C-09 (achados de PRODUTO, não Baixo) corrigidos na quick task 260906-vf9 (2026-09-06) — C-06 com escopo reduzido (frase no Histórico existente, não tela nova) e C-09 com limiar de drawdown de 15% | Not mapped to any phase — explicit backlog | v1.0 close |
| verification_gap | Item 8 do checkpoint 08-05 — verificação ao vivo de `entradaAuto` por um pregão inteiro | human_needed | v1.1 close |
| verification_gap | 2 human-checks da Fase 3 (card de status 3 badges reativo; mensagem de "sem permissão" do kill-switch) | human_needed | v1.1 close |
| v2 requirements | CAP-08..11 (loja/IAP, preço/moeda, IA gerenciada sem BYOK como paga, alvo dinâmico exclusivo do pago) | Deferred to future release — depende da decisão comercial de venda em si | v1.3 roadmap (2026-08-29) |
| Pending todo | `medir-rate-limit-mydata.md` (priority medium) | Ainda aberto pra acompanhar volume real de tráfego de opções se crescer | Fase 9 close (2026-08-27), rebaixado 2026-08-31 |
| v2 requirements (nomeado no kickoff) | Integração MCP real (Estratégia C, `plano-mcp-servico.md`) — troca o corpo de `rastrear()`/`avaliar()` (ENG-04 da Phase 15) sem reabrir requirements quando aprovado | Deferred — condicionado à aprovação do Alex | v1.4 roadmap (2026-09-02) |
| v2 requirements (nomeado no kickoff) | Setup customizado pelo usuário; estruturas adicionais além das 3 do v1 | Deferred — biblioteca fixa por enquanto | v1.4 roadmap (2026-09-02) |
| uat_gap | 20-HUMAN-UAT.md — 3 cenários pendentes (reduced-motion real MOTION-01/02/03; pulso de sucesso real de MOTION-02 em venda total) | partial — limitação de ferramenta (sem CDP Emulation.setEmulatedMedia) + mercado fechado durante toda a janela de execução | v1.5 close (2026-09-06) |
| uat_gap | 22-HUMAN-UAT.md — 1 cenário pendente (snap em DOM real dos 2 trilhos de opções sem dado de mercado ativo) | partial — prova estática completa via guardião, sem dado real disponível | v1.5 close (2026-09-06) |
| verification_gap | 20-VERIFICATION.md, 22-VERIFICATION.md, 23-VERIFICATION.md — status human_needed | Todos com evidência completa em código/bundle; pendência é só de confirmação humana ao vivo, ver .planning/milestones/v1.5-MILESTONE-AUDIT.md | v1.5 close (2026-09-06) |
| Tech debt (achado na auditoria de integração) | `numHero` (token de 34px da escala TYPO-02) sem consumidor real — `CapitalCurve` segue com fontSize hardcoded 27px | Decisão deliberada, documentada em 3 fases sucessivas (20/21/22) — não bloqueia, item de backlog para fase futura de polish | v1.5 close (2026-09-06) |
| Quick tasks pré-existentes (12, não relacionados ao v1.5) | 260820-0hl, 260823-vu4, 260823-x55, 260824-i45, 260824-kc2, 260830-eqm, 260901-1ak, 260901-2da, 260901-r5t, 260901-u2c, 260902-km8, 260905-1gb — todos status "missing" (sem SUMMARY.md) | Pré-datam o milestone v1.5; não fazem parte do seu escopo — não resolvidos nem descartados, seguem no backlog geral | v1.5 close (2026-09-06) |
| Pending todo | `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` (priority medium) | Acompanhar aprovação do serviço MCP autenticado — não relacionado ao v1.5 | v1.5 close (2026-09-06) |

## Session Continuity

Last session: 2026-09-13T15:30:00Z
Stopped at: **Fase 27 — cinco planos executados**, aba Opções sobre a carteira. O defeito relatado ("setups não são gravados") era, na verdade, a ausência do conceito de dono: o armazém do serviço é compartilhado e sem dono, não havia rota de listar, e o ticker nascia vazio. Agora há índice por usuário, namespacing no nome que vai ao serviço, leitura técnica pelo motor interno (custo zero) e o serviço externo só sob clique com o preço escrito. Emendas 1 e 2 ao ADR-027. Suíte 2780 + 143 `.mjs`. **Pendente: publicação conjunta de 27-01 e 27-02** (separados quebram as ações de setup no app publicado), a validação ao vivo que depende dela, e a remoção do `abcdef12-teste-fase-27` no encerramento.

Anterior: Fase 26, plano 01 concluído — Fase A do `26-CONTEXT.md`, os sete itens baratos e independentes, um commit cada (`65ab89e` A1, `5155229` A2, `9265f0f` A3, `2ffb4bf` A4, `6144507` A5, `704955d` A6, `fa19bcf` A7; mais `16c07a2`, nota de flakiness fora de escopo). A aba Opções deixou de ser invisível para o assistente, a KB responde antes da checagem de tela, o tour começa onde o app abre, e três textos mortos (frase de evidência, caminho da mensagem de cota, mascote no SKILL.md) passaram a bater com o código — cada ponto com guardião novo derivando da fonte. Suíte 2691/5/3xfail + 137 `.mjs`, `vite build` verde. **Duas publicações pendentes e nesta ordem:** a conjunta da Fase 25 (que já estava pendente) e a desta fase — backend (A1/A2/A6) com bump manual de `SERVER_BUILD_ID`, depois `bump.sh` + `publicar-web.sh` para A1/A3/A4/A5. Nada empurrado a origin.

Anterior: Fase 25, plano 06 concluído — o plano visível no app (Fase 5 do `25-CONTEXT.md`), fechando a Fase 25 em código. Tile Plano no grupo Conta, `PlanoScreen` e o banner `LimiteAtingido`; as duas rotas de watchlist devolvem 402 estruturado. Publicação conjunta das cinco fases é a etapa seguinte.

Anterior: Fase 25, plano 04 concluído — os gates leem o plano (Fase 3 do `25-CONTEXT.md`). Os cinco limites de IA passam a resolver pelo plano da conta, com o override global como camada de baixo; o `owner` pula o cap comercial e nunca o físico (D3); a recusa é classificada por código, não por frase. `opcoes.criar_setup` (D2) ficou deliberadamente de fora, como pendência nomeada. Deploy do backend (bump manual de `SERVER_BUILD_ID`) é etapa posterior — sem efeito visível, porque sem kv de plano configurado nada muda.

Anterior: Fase 25, plano 03 concluído — o catálogo de planos (Fase 2 do `25-CONTEXT.md`). Estrutura criada e provada inerte: sem configuração, `free` e `pro` decidem exatamente como antes. Quem passa a LER o catálogo é o 25-04. Deploy do backend é etapa posterior, sem urgência — nada consome o catálogo ainda.

Anterior: Fase 24, plano 15 concluído — os três tetos da aba Opções configuráveis pelo portal admin (precedência memória → kv → env → default, origem publicada, prévia, auditoria por campo e o aviso do teto compartilhado do serviço). Deploy do backend e `publicar-admin.sh` são etapa posterior, já combinada com o Alex.

Anterior: Fase 24, plano 14 concluído — o ensaio de setup passou a dizer quando não testou nada (helper `_ensaio_inconclusivo`, campo `ensaio` no `/setups/compilar` e a faixa acima dos números do backtest). Nada publicado: produção segue em `F10-20260911-07`.
Resume file: None

## Operator Next Steps

**PUBLICAÇÃO PENDENTE — Fase 27 (2026-09-13, tarde).** A fase está completa
em código (24 commits, suíte 2780 + 143) e **não está no ar**. Restrição de
sequência própria: `27-01` (backend) e `27-02` (front) **têm de sair
juntos** — publicar só o backend quebraria "Disparos do setup" e "Desativar"
no app publicado, porque o front atual manda o nome sem o prefixo do armazém
e leva 422. Como a fase inteira já está commitada, a publicação natural é a
fase toda de uma vez.

Duas coisas dependem dessa publicação e não podem ser feitas antes:

1. a **validação ao vivo** do 27-01 (Parte 1 do checkpoint) — ela exige as
   rotas novas respondendo em produção;

2. **instalar no aparelho** com a aba nova funcionando — o app instalado fala
   com produção, então o front da Fase 27 sobre o backend de hoje acharia 404
   em `/api/options/vigias` e `/api/options/tecnico/{ticker}`.

No encerramento da fase, remover o setup `abcdef12-teste-fase-27` do armazém
do serviço (ele existe só para provar o caminho do pré-existente).

**PUBLICADO (2026-09-13, carimbo `F10-20260913-01`, PR [#54](https://github.com/AlexandreCamerini/b3agente/pull/54), merge `29962bb`).**
Fase 25 (planos comerciais) foi ao ar pela primeira vez, junto com a Fase
26/Fase A completa (A1-A8). `bump.sh` → `server/app/main.py` (SERVER_BUILD_ID
sincronizado à mão + comentário) → `npx vite build` → `publicar-web.sh
--so-publicar` → commit único → push → PR → merge. Verificado ao vivo:
`https://boris.semente.dev/api/health` responde `F10-20260913-01`, e o bundle
servido carrega o mesmo carimbo. `web-admin` (portal) **não** foi tocado
nesta rodada — a Fase 26 não mexeu nele, e o `admin_dist` publicado em
`62d1e88` (Fase 25) já estava atualizado. Sem pendência de publicação no
momento.

**v1.5 (Redesenho de UI) — SHIPPED, sem próximo passo mecânico.** 4 itens de
verificação humana pendentes, consolidados em
`.planning/milestones/v1.5-phases/20-funda-o-estrutural-e-tipogr-fica/20-HUMAN-UAT.md` — sem
urgência (nenhum bloqueia produto, ver `.planning/milestones/v1.5-MILESTONE-AUDIT.md`).

**v1.4 (Opções v2) — único milestone aberto, retomar quando o Alex puder:**

- Retomar o checkpoint humano da Fase 17 (`17-06-PLAN.md` Task 2) com o
  mercado aberto — payoff real, collar por caixa insuficiente, aceite/
  cancelamento, Radar vs. Watchlist, iPhone. Só depois considerar a Fase 17
  de fato fechada (e dar push pra origin).

- `/gsd-plan-phase 18` — seção "Oportunidades de opções" em Posições.
- `/gsd-plan-phase 19` — motor multi-candidato, depois da Fase 18 fechada.

**Depois do v1.4 fechar:** `/gsd-new-milestone` para decidir o próximo
milestone (nenhum roteirizado ainda além do v1.4).

## Deferred Items

Itens reconhecidos e adiados no fechamento da milestone v1.7 (2026-09-22),
via `gsd-sdk query audit-open` — nenhum é um gap desta milestone; a decisão
foi "reconhecer e fechar", não "resolver antes".

| Categoria | Item | Status |
|---|---|---|
| quick_task | 49 tarefas datadas 2026-08-20 a 2026-09-16 (antes da v1.7 existir) | missing (referência órfã do scanner — provável dívida já resolvida de milestones anteriores v1.4/v1.5/v1.6, não investigada a fundo) |
| todo | `carimbo-frescor-blocos-cross-carteira.md` | pending (revisado e não dobrado nas Fases 34/35/36/37 — match fraco por palavra-chave) |
| todo | `medir-rate-limit-mydata.md` | pending (revisado, sem relação com o escopo de payoff/gráfico) |
| todo | `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` | pending (tracking de aprovação de serviço externo, fora do controle do time) |
| todo | `revisao-arquitetura-mcp-ecossistema-b3.md` | pending (prioridade alta, mas decisão explícita do Alex de tratar à parte, fora do roadmap da v1.7) |
| todo | `subaba-operar-fetch-redundante-gate-proposta.md` | pending (baixa prioridade, revisado 4x, nunca dobrado) |

## Pendência não-bloqueante da Fase 37 (verificação visual)

O checkpoint humano da Task 2 do 37-05 foi aprovado com base em evidência
automática (suíte, build, plan-checker, revisão de código), não em
confirmação visual com dado real de mercado — bloqueada pela ausência de
`BRAPI_TOKEN`/`BOLSAI_API_KEY` no backend local usado na tentativa de
instalar no iPhone do Alex. Recomendado: dar uma olhada no gráfico/
explicação em produção (`https://boris.semente.dev`) quando conveniente.
Não bloqueia nada — só registrado para não se perder.
