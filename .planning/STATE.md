---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Estruturas de opções na carteira
status: ready_to_plan
stopped_at: 'Fase 46 fechada com ressalvas (2026-10-02): 12/12 planos, verifier passed 7/7, code review 0 críticos / 2 altos (AL-01, AL-02) abertos. Próximo: /gsd-plan-phase 46.1 (G-07, G-08, AL-01, AL-02) antes de publicar; depois /gsd-discuss-phase 47. Nada pushado nem publicado.'
last_updated: 2026-10-02T20:48:26.696Z
last_activity: 2026-10-02 -- Fase 46 fechada com ressalvas (phase.complete; checkpoint do iPhone aprovado com ressalvas); Fase 46.1 aberta no ROADMAP. | antes, em 2026-10-01 — Fase 46 em execução — onda 7/7: 46-08 tarefa 1 feita (guardiões transversais), cores da quick 261001-0or revertidas (deddf454, d8ab3b92) e paleta do design v6 reaplicada só no card (fe6dba75, 2c78e563, `cartaoV6Cores.js`); suíte verde; plano de correção 46-09..46-12 (gap closure do UAT no iPhone: G-01..G-06, card fechado) criado e aprovado pelo plan-checker; gap closure em execução: ondas 1-3/3 em código (46-09..46-12 tarefa 1; régua ancorada), suíte canônica verde (3211 pytest); AGUARDANDO checkpoint humano do Alex no iPhone (46-12 tarefa 2: G-01..G-06 + passos do 46-08); depois code review, verificação e phase.complete; checkpoint humano do 46-08 será repetido no 46-12; depois verificação, code review e fechamento da fase
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 20
  completed_plans: 20
  percent: 60
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-27)

**Core value:** O usuário leigo sai do Modo Estudo entendendo de verdade como o mercado funciona — não decorou uma resposta, aprendeu o raciocínio — e só então tem acesso a automações do Modo Operador.
**Current focus:** Phase 46.1 (ressalvas da 46: G-07, G-08, AL-01, AL-02), depois Phase 48 (Opções, caminho B; aberta 2026-10-05; PLANEJADA 2026-10-05: 14 planos em 7 ondas, plan-checker passed, pronta p/ `/gsd-execute-phase 48`) e Phase 47 — didática

## Current Position

Milestone: v2.0 Estruturas de opções na carteira (Fases 44-47, mais 46.1).
Phase: 46.1 (a planejar) — Fase 46 COMPLETA com ressalvas (12/12; verifier passed; review 0 crít./2 altos).
Fase 48 EM EXECUÇÃO (2026-10-05): ondas 1-4/7 completas (11/14 planos: 48-01..11). Suíte canônica verde ao fim da onda 3 (3323 pytest + .mjs); onda 4 (48-10) deixou 7 guardiões .mjs vermelhos POR DESENHO (âncoras de texto do OpcoesScreen antigo), todos atribuídos ao 48-12 — suíte só volta a ser exigida verde ao fim da onda 5. Próximo: 48-12, 48-13, 48-14 (checkpoint humano no iPhone). A conferir na verificação: `liquido` do collar sem sinal em conceitos (48-05) × com sinal no motor (48-04); `execucao.motivo` não enviado pelo backend; ao sair e voltar à aba só o ticker de montar é lembrado (objetivo/escada/confirmar voltam ao hub). Execução serial na árvore principal, STATE editado à mão.
Status: Ready to plan 46.1. Ressalvas do Alex (2026-10-02): G-07 nome da empresa sem fallback; G-08 "total suspenso" sem causa; aba Opções não executa a estrutura (NÃO reproduzida, fora da 46.1 até ter modo/ativo/estrutura). Review: AL-01 (collar mostra conta errada no Estudo, cartao_posicao.py:466-487) e AL-02 (leitura antiga mantida como atual quando /api/carteira/leitura falha, App.jsx:4484-4530) devem ser corrigidos antes de publicar; MD-01..06 e BX-01..07 em 46-REVIEW.md.
Decisões do Alex (2026-09-29): régua de faixa mantida; pernas sempre visíveis;
  texto do Estudo completo; escopo motor + front aprovado. Instrução
  principal: economizar modelo (CLAUDE.md §Estratégia de execução).
Pendências fora de milestone: build iOS/TestFlight (ação do Alex); quick task
  avulsa (textos de vazio sem consumidor + "amostra insuficiente" com janela
  e n); quick 260928-u0h e entrega ainda sem push (confirmar com o Alex).
Next (2026-09-30): Fase 46 (Carteira v6 — card com modos Estudo/Operador, todo cálculo no backend; protótipo: ver ROADMAP, Fase 46) entra antes da Didática, que foi renumerada para Fase 47 (DIDA-01..02). 45 promovida e validada pelo Alex. Dívida da 45: IN-02..07 do 45-REVIEW.md, TravaPill legado (AA 4,18 no claro), ask × último negócio, Encerrar só recompra a call.

## Quick Tasks Completed

Tabela anterior (até 2026-09-16) em `.planning/STATE-HISTORY.md` §"Quick Tasks Completed".

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260928-u0h | Aba Opções → Oportunidades: estrutura já aberta (proposta de encerramento, que não consulta a leitura técnica) sai do bloco "confirmadas pela leitura técnica" para a seção própria "Suas estruturas abertas"; cada posição que não vira proposta passa a mostrar o motivo (sem liquidez / sem mercado / leitura em COMPRAR / sem lastro / sem vencimento / sem contrato líquido / caixa / degradado / desconhecido → "Não há dados suficientes para concluir."). Módulo puro `classificarOportunidades.js`, frases por modo em `copy.js`, guardião novo `test_opcoes_abertas_e_motivos.mjs`, `test_carteira_opcoes_tira.mjs` reconciliado com nota. Gate da suíte pegou "trava protetora" (âncora CVM proibida no front) numa frase nova — corrigido (`fcf3cc98`). Suíte canônica 3063 pytest + 172/172 `.mjs`. Motor e `useOpcoesPropostas.js` intocados. Limitação: estrutura aberta em ativo com gate reprovado aparece como `aberta_sem_proposta`; frases de motivo em `copy.js` e não em `skill_ref` (o `motivoTexto` do backend colapsa 3 motivos na frase de sem_setup). Não publicado | 2026-09-28 | 51d32566, 77fdd628, fcf3cc98 | Verified | [260928-u0h](./quick/260928-u0h-separar-encerramento-e-motivo-por-posica/) |
| 261001-0or | Identidade de modo, opção C (aprovada por protótipo): faixa de modo de 44px no shell (`FaixaModo`, textos em `copy.js`), neutros com matiz própria por modo nos 4 temas, acento/verde/vermelho do claro corrigidos para AA (accent 4.89/5.00 sobre tint), borda superior de 3px e CTA "Comprar…" preenchido só no card da watchlist (`contexto="watchlist"`). Guardião novo `test_contraste_tokens.mjs` (AA 4.5 nas 4 combinações) + `test_identidade_modo_faixa.mjs`; 3 guardiões antigos atualizados com nota. Ajustes por medição: textFaint Estudo-escuro `#8189a5`, warn claro `#9a5b06`. Suíte canônica 3210 pytest + `.mjs` todos OK (fora do sandbox). Só UI; card de posição, `server/` e `web_dist` intocados. Limitações: bgPanel claro entre bgBase e bgCard (olho do Alex); derivados não aprovados (bgToast, borderDashed, knob…); Radar sem destaque; safe-area/BottomSheet no aparelho não verificados. Não publicado | 2026-10-01 | 0d95d9c1, d5d66510, f73a16a6, 383e67d8 | Verified | [261001-0or](./quick/261001-0or-identidade-modo-opcao-c/) |

## Histórico

Posições anteriores (Fases 24–43), métricas, contexto acumulado de decisões e
notas de sessão antigas: `.planning/STATE-HISTORY.md` (movido verbatim em
2026-09-28). Não é leitura obrigatória para executar planos.

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

## Deferred Items (fechamento da v1.8, 2026-09-26)

Itens reconhecidos e adiados no fechamento da milestone v1.8, via
`gsd-sdk query audit-open` (53 itens) — nenhum é gap da v1.8; decisão
"reconhecer e fechar" (config `mode: yolo`).

| Categoria | Item | Status |
|---|---|---|
| quick_task | 50 tarefas datadas 2026-08-20 em diante (todas anteriores à v1.8) | missing — falso positivo do scanner: as pastas têm `*-SUMMARY.md` (ex.: `260823-vu4`), o parser não lê status delas |
| todo | `medir-rate-limit-mydata.md` | pending (medium), já adiado desde a Fase 9 |
| todo | `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` | pending (medium), depende de aprovação de serviço externo |
| todo | `revisao-arquitetura-mcp-ecossistema-b3.md` | pending (high), decisão do Alex de tratar à parte do roadmap |
| achados D-04 (Fase 41) | 6 inconsistências de navegação/copy, `41-02-SUMMARY.md` | aprovados pelo Alex como "não corrigir agora" — fold-in oportunista |

## Deferred Items (fechamento da v1.9, 2026-09-27)

Itens reconhecidos e adiados no fechamento da milestone v1.9 — mesmo
mecanismo de scanner das v1.7/v1.8 (referências órfãs de quick tasks, não
gap desta milestone), contados diretamente em `.planning/quick/` e
`.planning/todos/pending/` nesta sessão: 51 diretórios de quick task (todos
com `*-SUMMARY.md`, o mais recente datado 2026-09-26, ainda anterior à
abertura da v1.9) + 3 todos pendentes. Total: 54.

| Categoria | Item | Status |
|---|---|---|
| quick_task | 51 tarefas datadas 2026-08-20 a 2026-09-26 (todas anteriores ou concorrentes à abertura da v1.9, nenhuma das Fases 42/43) | missing — mesmo falso positivo do scanner das v1.7/v1.8: as pastas têm `*-SUMMARY.md`, o parser não lê status delas |
| todo | `medir-rate-limit-mydata.md` | pending (medium), já adiado desde a Fase 9 |
| todo | `opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md` | pending (medium), depende de aprovação de serviço externo |
| todo | `revisao-arquitetura-mcp-ecossistema-b3.md` | pending (high), decisão do Alex de tratar à parte do roadmap |

**Known deferred items at close: 54**

Itens específicos da v1.9 (não fold-in do scanner, ver também `PROJECT.md`
§Active): build iOS/TestFlight das Fases 42-43 pendente do Alex; KB sem
verbete de vantagem estatística/expectativa matemática/taxa de acerto ×
rentabilidade (tema obrigatório do CLAUDE.md); "amostra insuficiente
(n=0 …)" no Operador sem janela/n total (observação do checkpoint da Fase
43, sem decisão); motion do `ConfluenceRing` e tokens `--sp-*` globais
(Fase 3 da auditoria — Polish, deferido por decisão de escopo 2026-09-26,
nunca reaberto); decisão contra o regime (motor) — observação sem
investigação própria ainda.
