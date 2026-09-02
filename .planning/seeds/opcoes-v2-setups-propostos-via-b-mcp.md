---
title: Opções v2 — setups de opções propostos a partir da análise técnica via b-mcp
trigger_condition: A base de arquitetura já existe (decisão 2026-09-02, ver
  "Decisões de arquitetura fechadas" acima) — o v1 é planejável com código
  determinístico do próprio Boris, sem depender do b-mcp. O item de
  identidade do hub (mydata.semente.dev × mydata.acamerini.app) já foi
  resolvido. O que falta antes de virar fase é a pendência de produto do
  plano comercial (gratuito vs. pago); o rate-limit do hub segue como item
  de acompanhamento, não bloqueio.
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

Item de acompanhamento (histórico de bloqueio, não trava mais o
planejamento):
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

Decisões de arquitetura fechadas:
- **Independência do b-mcp em runtime no v1** (2026-09-02). O Boris não
  chama o processo nem o serviço b-mcp; o único acoplamento é código Python
  puro adotado uma vez, por cópia, no repo do Boris. Estratégia B (motor
  próprio do Boris, b-mcp como especificação de referência) entre as 5
  avaliadas.
- **Critério de seleção do contrato: `liquidity_score` >= 40 + strike
  extremo** — mantém o que já está em produção
  (`server/app/opcoes_lastreadas.py`, Fase 14). NÃO adota o critério por
  **delta** do `estruturas.py` do b-mcp. Motivo: réguas incompatíveis;
  convivendo sem reconciliar, o app proporia venda coberta por critérios
  diferentes dependendo da tela.
- **Reaproveita `calculos.py`** (custo líquido, ganho/perda máximos,
  breakevens, delta somado) — matemática de identidade pura, sem I/O.
- **Exclui a DSL de setups (`setups.py`)** do escopo do v1 — gatilho técnico
  já vem do Radar do Boris, e portar sinal preditivo sem
  `backtest_sinal.py` reintroduziria o defeito medido no `ADR-016` e
  corrigido no `ADR-017`.
- **Limite interno `rastrear()` / `avaliar()`**, no vocabulário do contrato
  `ADR-004` / `mydata_client.py` — a troca futura pela chamada MCP (quando
  `plano-mcp-servico.md` for aprovado) é troca de corpo de função, não
  redesenho.
- Racional completo: `.planning/notes/opcoes-v2-b-mcp-exploracao.md`, seção
  "Arquitetura decidida (2026-09-02)".

Pendências de produto (não técnicas, aguardando o Alex):
- Plano comercial (gratuito vs. pago), relação com o cap da v1.3.
