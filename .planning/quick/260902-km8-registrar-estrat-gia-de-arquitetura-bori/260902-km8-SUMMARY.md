---
phase: quick-260902-km8
plan: 01
subsystem: planning-docs
tags: [opcoes-v2, arquitetura, b-mcp, mydata, planejamento]
dependency-graph:
  requires: []
  provides:
    - "Decisão de arquitetura fechada: v1 de Opções não depende do b-mcp em runtime"
  affects:
    - ".planning/notes/opcoes-v2-b-mcp-exploracao.md"
    - ".planning/seeds/opcoes-v2-setups-propostos-via-b-mcp.md"
    - ".planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md"
tech-stack:
  added: []
  patterns:
    - "Histórico não se reescreve — atualização entra por cima do texto antigo, rotulado como contexto histórico"
key-files:
  created: []
  modified:
    - ".planning/notes/opcoes-v2-b-mcp-exploracao.md"
    - ".planning/seeds/opcoes-v2-setups-propostos-via-b-mcp.md"
    - ".planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md"
decisions:
  - "Estratégia B escolhida (motor próprio do Boris, b-mcp só como especificação de referência), com refinamento de reaproveitar calculos.py"
  - "Critério de seleção de contrato mantém liquidity_score >= 40 + strike extremo (produção); NÃO adota critério por delta do estruturas.py"
  - "DSL de setups técnicos (setups.py) fica fora de escopo do v1 — risco de sinal já corrigido em ADR-016/017"
  - "Limite interno rastrear()/avaliar() no vocabulário do contrato ADR-004/mydata_client.py, não vocabulário novo"
metrics:
  duration: "~25min"
  completed: 2026-09-02
---

# Quick Task 260902-km8: Registrar estratégia de arquitetura Boris×b-mcp Summary

Registra nos três documentos de planejamento (nota de exploração, seed e
todo) a decisão de arquitetura fechada com o Alex nesta sessão: o v1 de
Opções do Boris não depende do b-mcp em runtime — o único acoplamento
aceito é adoção pontual de código puro (`calculos.py`), a seleção de
contrato continua usando `liquidity_score` (régua já em produção), e a DSL
de setups técnicos (`setups.py`) fica fora de escopo.

## O que foi feito

**Arquivo 1 — `.planning/notes/opcoes-v2-b-mcp-exploracao.md`:**
- Item 2 ("Transporte em produção") virou veredito `DECIDIDO (2026-09-02)`,
  com o texto anterior (`PARCIALMENTE RESOLVIDO`) preservado como contexto
  histórico rotulado.
- Nova seção `## Arquitetura decidida (2026-09-02) — independência do b-mcp
  no v1`, inserida imediatamente antes de `## Bloqueios`, com: os achados
  novos (`estruturas.py`, `plano-mcp-servico.md` em avaliação, portal
  sintético em produção); as 5 estratégias avaliadas (A-E, com B marcada
  ESCOLHIDA e o racional de descarte de cada uma das outras quatro); o
  achado operacional crítico das duas réguas de seleção incompatíveis
  (`liquidity_score` vs. `delta`); o que se reaproveita (`calculos.py`) e o
  que fica fora de escopo (`setups.py`, com racional ADR-016/017); e o
  limite interno `rastrear()`/`avaliar()` no vocabulário do ADR-004.
- Bloqueio 2 marcado `DESBLOQUEADO PARA O V1 (2026-09-02)`, com a pergunta
  original (`PORTAL_SENHA`) preservada como contexto histórico.
- "Próximo passo formal" atualizado: não afirma mais que os 3 bloqueios
  travam o planejamento; registra o que resta (rate-limit + plano
  comercial).
- "Fontes consultadas" ganhou as 3 fontes novas desta rodada.

**Arquivo 2 — `.planning/seeds/opcoes-v2-setups-propostos-via-b-mcp.md`:**
- Nova seção `Decisões de arquitetura fechadas:`, entre as decisões de
  produto e as pendências de produto, com o resumo da estratégia e link
  para a nota.
- `trigger_condition` reescrita: não condiciona mais ao todo do b-mcp;
  registra que a base de arquitetura já existe e o que falta é a pendência
  comercial.
- Rótulo "Bloqueios que precisam resolver antes de planejar" trocado por
  "Item de acompanhamento", preservando o link para o todo.

**Arquivo 3 — `.planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`:**
- `priority: high` → `priority: medium`; título mudou de "Definir acesso
  server-to-server ao b-mcp antes de planejar Opções v2" para "Acompanhar
  aprovação do serviço MCP autenticado para eventual migração de Opções
  v2" (H1 do corpo casado com o novo título).
- Item 2 marcado `DESBLOQUEADO PARA O V1 (2026-09-02)`, com gatilho de
  revisita (aprovação de `plano-mcp-servico.md` → Estratégia C) e a
  pergunta original preservada como contexto histórico.
- Parágrafo "Por que isso bloqueia planejamento" atualizado para "Transporte
  decidido", preservando o texto anterior como histórico.
- Links de volta para a nota e o seed adicionados.
- Arquivo permanece em `todos/pending/` (não movido para `resolved/`,
  porque o item 2 não foi respondido — apenas deixou de bloquear).

## Deviations from Plan

None - plan executado exatamente como escrito. Um ajuste de formatação foi
necessário durante a verificação: o gate `nota/arq: setups.py fora de
escopo` falhou na primeira rodada porque a frase "fora de escopo" ficou
quebrada por um wrap de linha (`**fora de\nescopo**`); corrigido para manter
a frase na mesma linha antes de recommitar. Isso não é uma mudança de
conteúdo, só de quebra de linha.

## Verificação

Bloco `<automated>` da Task 1 (suíte completa desta quick task) executado
via script equivalente (mesmo conteúdo do bloco do plano, com
`LANG=en_US.UTF-8`/`LC_ALL=en_US.UTF-8` explicitados — o ambiente padrão do
worktree roda em locale `C`, que quebra os padrões regex com acentuação
como `hist.rico`; sem o locale UTF-8 o `.` de regex não casa bytes
multi-byte de caracteres acentuados). Resultado: `VERIFY OK` (81/81 checks
passaram).

`git diff --name-only HEAD~1 HEAD` = exatamente os 3 arquivos alvo, todos
sob `.planning/`. Nenhum arquivo de código tocado.

Suíte canônica (`bash scripts/executar.sh --testes`) e `npx vite build` não
se aplicam — nada em `server/`, `web/` ou `web-admin/` foi tocado (conforme
`<verification>` do plano).

## Self-Check: PASSED

- FOUND: `.planning/notes/opcoes-v2-b-mcp-exploracao.md`
- FOUND: `.planning/seeds/opcoes-v2-setups-propostos-via-b-mcp.md`
- FOUND: `.planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`
- FOUND: commit `36cc1d1`
