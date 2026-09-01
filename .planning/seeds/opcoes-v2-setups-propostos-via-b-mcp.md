---
title: Opções v2 — setups de opções propostos a partir da análise técnica via b-mcp
trigger_condition: Quando o todo "opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp"
  for resolvido pelo Alex (identidade do hub mydata.semente.dev × mydata.acamerini.app
  confirmada, e via de acesso server-to-server ao b-mcp definida) — aí sim
  /gsd-plan-phase ou /gsd-new-milestone tem base pra desenhar o transporte.
planted_date: 2026-09-01
---

# Opções v2 — setups de opções propostos via b-mcp

Nova experiência de Opções no Boris+, restrita a opções com cobertura real na
carteira (mesma régua da Fase 14 — venda coberta, put de proteção). A partir do
snapshot de análise técnica de um ativo, propor um setup de opções (ou uma
perna) que o usuário aceita ou recusa, usando as tools do servidor MCP
`b-mcp`/`mydata` (`~/dev/MCP/servers/mydata/`) como fonte de dado/cálculo de
opções — não como motor de decisão (esse motor é do Boris, por ser o único
lado que conhece a carteira real do usuário).

V1: biblioteca fixa dos setups mais conhecidos do mercado. Customização pelo
usuário fica para versão futura, fora deste seed.

Contexto completo, achados de arquitetura e decisões já tomadas:
`.planning/notes/opcoes-v2-b-mcp-exploracao.md`.

Bloqueios que precisam resolver antes de planejar:
`.planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`.

Pendências de produto (não técnicas, aguardando o Alex):
- Escopo do v1 da biblioteca além de venda coberta/put de proteção.
- Colocação na navegação — 3 candidatos levantados (aba própria fora do
  Operador / contextual em Posições / fundida com Mesa). Mockup comparando
  os 3 lado a lado (dados mockados, tokens reais do Brand Book v2):
  https://claude.ai/code/artifact/f9a3690f-94f9-46ed-9209-ef934ccaae21 —
  recomendação provisória por "dentro de Posições", mas pede validação do
  Alex (e opcionalmente um pass de `design-with-claude:navigation-specialist`)
  antes de comprometer.
- Plano comercial (gratuito vs. pago), relação com o cap da v1.3.
