---
quick_id: 261014-upj
slug: rebaixamento-operador-visivel
date: 2026-10-14
mode: quick
---

# Quick 261014-upj — rebaixamento do Operador visível

## Problema (diagnóstico de produção, 2026-10-14)

`store.set_config` com `appMode != "operador"` troca `agent.mode` de
`"executar"` para `"sinalizar"` e zera `entradaAuto`, sem rastro. Voltar ao
Operador NÃO restaura (guardião `test_entrar_no_operador_nao_mexe_no_mode_sinalizar`,
decisão travada). Resultado: stops batidos viram só "Sinal do agente… apenas
sinalizar" e o usuário acha que o Operador quebrou.

## Decisões

- D1 — Evento `warn` no `agentLog` gravado DENTRO da migração, só quando `mudou`
  (idempotente: segunda saída com nada a desligar não grava nada). Sem push:
  `push_agent_log` não notifica; os filtros de push do agente leem só os eventos
  do ciclo.
- D2 — Marcador `agent.rebaixadoOperador = {em, execucao, entradaAuto}` gravado
  junto. É o que distingue "rebaixado pela migração" de "escolheu sinalizar"
  (sem ele, o aviso apareceria para quem escolheu sinalizar de propósito).
  Limpo em `set_agent` quando a conta, já em Operador, grava `mode` ou
  `entradaAuto` explicitamente (decisão do usuário). Nova saída acumula os
  campos (OR) com o marcador anterior.
- D3 — O aviso lê do `GET /api/agent/status` (`meuModo`, `minhaEntradaAuto`,
  `meuRebaixamento`), já consultado a cada 20 s pela tela do Operador IA nos
  DOIS stores — verdade do servidor, sem tocar `persistence.js` (o `doc.agent`
  do iPhone não reflete a migração feita no servidor; ler dele mostraria
  "Executar" fantasma). Paridade deviceStore/serverStore intacta.
- D4 — Copy em `skill_ref.REBAIXAMENTO_OPERADOR` (dois modos, chaves idênticas,
  sem placeholder) + espelho byte a byte em `COPY[modo].rebaixamentoOperador`,
  travado por `test_vocabulario_espelho.mjs`. Texto do Diário no modo de
  destino (educacional — a conta acabou de ir para o Estudo).
- D5 — Aviso na `AgenteScreen` (card-herói, abaixo dos botões de modo), só com
  `operador` (implica termo aceito) e marcador presente. Atalho "Religar
  Executar" → `putAg({mode:"executar"})` (que já religa `serverEnabled`); botão
  secundário mantém sinalizar (`putAg({mode:"sinalizar"})`) e limpa o marcador.

## Arquivos

- `server/app/store.py` (migração + limpeza em set_agent)
- `server/app/skill_ref.py` (REBAIXAMENTO_OPERADOR)
- `server/app/main.py` (/api/agent/status)
- `web/src/copy.js` (espelho), `web/src/App.jsx` (aviso)
- `server/tests/test_rebaixamento_operador.py`, `web/tests/test_rebaixamento_operador_ui.mjs`
- `web/tests/test_vocabulario_espelho.mjs` (inclui o dict novo)

## Critérios de aceite

1. Sair do Operador com executar/entradaAuto ligados grava 1 evento warn com o
   texto da combinação certa e o marcador; sair de novo sem nada ligado não
   grava evento novo.
2. Sair sem nada ligado não grava evento nem marcador.
3. `set_agent` em Operador com `mode`/`entradaAuto` limpa o marcador; fora do
   Operador não limpa.
4. `/api/agent/status` expõe `meuModo`, `minhaEntradaAuto`, `meuRebaixamento`.
5. Aviso no App.jsx condicionado a `operador` + marcador, com atalho que grava
   `mode:"executar"`; copy vem de `COPY`, não hardcoded.
6. Guardiões existentes intactos; suíte canônica verde.

## Limitação conhecida

Contas migradas ANTES deste deploy (ex.: a do Alex, 14/10) não têm marcador —
não ganham aviso retroativo. Religar é um toque em Operador IA → Executar.
