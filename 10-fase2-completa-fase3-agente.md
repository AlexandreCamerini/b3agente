# QA 10 — Fase 2 completa (2.2–2.5) + Fase 3 (agente server-side + APNs)

## Fase 2 — flow oportunidade → carteira (fechado)
- **2.2** "Simular compra" no card da análise (Avaliar): abre o BuyModal com
  quantidade SUGERIDA por caixa × perfil (conservador 15% / moderado 25% /
  agressivo 40%, lotes de 100 — `suggestedQty`). Usuário sempre ajusta/confirma.
- **2.3** Pós-compra: oferta IMEDIATA do N3 — abre o StopAlvoModal já
  analisando o ativo; Fechar cancela sem efeito.
- **2.4** Posição: "Reanalisar (IA vê sua posição)" → Avaliar com contexto da
  posição (qty, PM, stop/alvo, resultadoAtual → `userPosition` no pacote da
  IA, backend). StopAlvoModal agora renderiza os **cenários** do N3
  (conservador/moderado/agressivo) com R:R, badge ⚠ quando desfavorável
  (<1,5) e memória de cálculo; 1 toque escolhe, Aplicar confirma.
- **2.5** Telemetria didática: `analysisLog` por ticker (cap 20) nos DOIS
  stores + endpoint /api/analysis-log; registrado no sucesso da análise e no
  aplicar stop/alvo; "Histórico de análises (N)" no card da posição.

## Fase 3 — agente autônomo server-side
- **3.1** `agent.py`: motor PORTADO do /api/cycle (endpoint agora o reusa —
  uma implementação); scheduler asyncio no startup (intervalo env
  B3_AGENT_INTERVAL_S, default 5min), só em pregão (seg–sex 10–18 BRT),
  kill-switch global `B3_AGENT_KILL=1`, por usuário `serverEnabled`.
- **3.2** Parâmetros na tela Automatizar: agente no servidor (exige conta;
  anônimo mantém foreground com aviso — 3.4), modo executar|sinalizar,
  regras stop/alvo/trailing (trailing SOBE o stop, nunca desce), teto de
  ops/dia e valor máx./operação. `A.putAgent` otimista; `set_agent` estendido.
- **3.3a** `agentLog` persistente (cap 200) + card "Registro do agente" +
  resumo ao abrir o app ("X ações desde sua última visita", notificação
  local) com `lastSeenAt`.
- **3.3b** APNs: `push.py` (JWT ES256/PyJWT + httpx http2/h2), tokens por
  usuário (cap 5, remove inválidos), envio por ação executada no scheduler;
  app: `notify.registerPush` + `@capacitor/push-notifications@^8` no
  package.json + botão em Automatizar. Passo a passo: APNS-PUSH.md.
- **3.5** `test_agent.py` (8): executa no stop, sinalizar não opera, teto
  diário, teto por valor, trailing sobe/não desce, kill-switch + janela de
  pregão, scheduler só usuários habilitados (anônimo intocado), textos sem
  verbo de ordem.

## Validação
py_compile ✅ · backend **123/123** ✅ · balance App.jsx 0/0/0 ✅ ·
node --check ✅ · suítes web ✅ (test_notify.mjs: ambiental pré-existente) ·
requirements + `h2` (APNs/HTTP2) · manifesto (verificar-arquivos) cobre os
módulos novos via server/app/*.py.

## Hard stop (device) — checklist
1. Avaliar: analisar um ativo → "Simular compra · sugestão N ações" → modal
   com N pré-preenchido → confirmar → StopAlvoModal abre sozinho com os 3
   cenários; escolher um → Aplicar → stop/alvo na posição.
2. Operar: "Reanalisar" leva a Avaliar (a leitura cita a posição);
   "Histórico de análises (N)" lista os registros.
3. Automatizar: ligar "Agente no servidor" (logado), modo executar, teto 1
   op/dia; deixar um stop tocável; FECHAR o app; após um ciclo (~5min em
   pregão) reabrir → resumo "1 ação desde sua última visita" + Registro.
4. Push (após APNS-PUSH.md): repetir o item 3 com push ativo → notificação
   chega com o app fechado.
5. Anônimo: aviso "requer conta" no card do servidor; ciclo foreground segue.
