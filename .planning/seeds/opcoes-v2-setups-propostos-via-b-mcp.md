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

Decisões de produto fechadas:
- Colocação na navegação — **Candidato A: aba própria "Opções"** na barra de
  navegação inferior, decidido por Alex em 2026-09-01. Barra resultante:
  Mesa/Radar, Monitoramento/Watchlist, Posições, Opções (nova), Perfil. Supera
  o Candidato B (contextual dentro de Posições), que era o palpite inicial
  desta sessão de exploração. Mockup comparando os 3 candidatos levantados
  (referência do comparativo, decisão já fechada):
  https://claude.ai/code/artifact/f9a3690f-94f9-46ed-9209-ef934ccaae21. Racional
  completo, trade-offs conscientemente aceitos e o contexto histórico de por
  que o outro candidato havia sido cogitado primeiro:
  `.planning/notes/opcoes-v2-b-mcp-exploracao.md` (seção "Navegação").
- Escopo do v1 da biblioteca — decidido por Alex em 2026-09-01: **venda
  coberta + put de proteção + collar (trava protetora)**. O collar entra por
  ser a combinação das duas mesmas pernas já calculadas (venda coberta e put
  de proteção já existem, Fase 14) — extensão natural, zero peça nova no
  motor. Excluídos, com motivos DISTINTOS: **straddle/strangle coberto** sai
  por liquidez (opções B3 fora dos blue-chips já são curtas pra 1 perna,
  pior pra 2 pernas simultâneas de lados opostos — o `find_tradable_options`
  do b-mcp tem `min_trades` justamente por isso); **cash-secured put** sai
  por definição, não por liquidez (inicia posição em vez de proteger uma que
  já existe, contradiz a régua "só sobre cobertura real" que é o enunciado da
  feature). **Ressalva arquitetural (Alex), parte da mesma decisão:** o v1
  tem que ser implementável com código determinístico do próprio Boris, sem
  depender do b-mcp para existir (o acesso server-to-server segue bloqueado —
  ver `.planning/todos/pending/opcoes-v2-confirmar-hub-mydata-e-acesso-b-mcp.md`,
  item 2), MAS desenhado com a lógica de screening de cadeia e cálculo de
  estrutura atrás de um limite/interface interno, de modo que trocar/estender
  por `find_tradable_options` / `evaluate_option_structure` do b-mcp, quando o
  bloqueio cair, seja extensão limpa e não reescrita. Isso é diretriz de
  design para a fase de implementação, não decisão de código a fechar agora.
  Racional completo: `.planning/notes/opcoes-v2-b-mcp-exploracao.md`, item 5
  da seção "Decisões tomadas nesta sessão".

Pendências de produto (não técnicas, aguardando o Alex):
- Plano comercial (gratuito vs. pago), relação com o cap da v1.3.
