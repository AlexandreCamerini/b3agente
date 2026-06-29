[2026-06-26T05:46:49Z] INICIO modo autonomo: auditoria full-stack
[2026-06-26T05:51:56Z] Etapa 1 (Auditoria): varredura de paridade web×iOS. Nenhum fetch relativo solto; JSON.parse protegido; base configurável existente. Bloqueadores B1/B2 já tratados em código; falhas de campo eram ambiente. -> qa/01-auditoria.md
[2026-06-26T05:51:56Z] Etapa 2 (Refator): consolidadas Fases 1-4; Fase 3 reescrita para análise INDIVIDUAL por card (endpoint carteira-stopalvo + parse_carteira). notify.js ganhou schedule/cancel/diag. Decisao: nao reescrever persistence.js (estendido nos 2 stores). -> qa/02-mudancas.md
[2026-06-26T05:51:56Z] Etapa 3 (QA codigo): revisao de deps de useMemo, closures, tela branca, BYOK, parsing. Riscos residuais aceitos e registrados. -> qa/03-revisao-qa.md
[2026-06-26T05:51:56Z] Etapa 4 (Testes): persistencia 19/19; paridade HTTP 5/5; parser carteira verde. Adicionados test_api_parity.mjs e test_notif_prefs_persistem. -> qa/04-testes.md
[2026-06-26T05:51:56Z] Etapa 5 (Pacote): INSTALACAO/TESTFLIGHT/SMOKE-TEST/RAILWAY + zip de codigo (exclui node_modules,dist,ios,.venv,__pycache__,*.db). -> dist/
[2026-06-26T05:51:56Z] Decisao autonoma: appId permanece com.exemplo.b3agente no repo; troca fica documentada (TESTFLIGHT/INSTALACAO) pois exige id proprio do dev. Sem bloqueio fisico exceto assinatura Apple (humana).
[2026-06-26T05:51:56Z] FIM do ciclo. Criterios de conclusao atendidos no escopo automatizavel.

## 2026-06-27 — Reaplicação das correções na versão enviada pelo usuário
- Base utilizada: `b3-agente-mobile-technical-models-fix-pytest.zip` enviado pelo usuário.
- Correção reaplicada: normalização robusta de `VITE_API_BASE` e `serverUrl` para iOS/WebView.
- Decisão: domínio público sem protocolo passa a usar `https://`; IP/localhost continua usando `http://` para backend local.
- Motivo: evitar que `b3-production-8fc0.up.railway.app` seja tratado como caminho relativo ou HTTP inválido no iPhone.
- Testes executados: `node web/tests/test_api_parity.mjs` e `python -m pytest -q` no backend.

## 2026-06-27 — Novo ciclo de auditoria + Etapa C1
- Auditoria refeita contra o código ATUAL (não contra docs antigos). Veredito:
  os 2 bloqueadores (B1 endereçamento / B2 notificações) já estão corretos em
  código — falhas de campo são de AMBIENTE (URL não configurada; plugin não
  sincronizado no projeto iOS git-ignored). Confirmado por paridade 6/6.
- Achados NOVOS: C1 (tela branca, Crítico, bug de lógica) priorizado por risco e
  atacado primeiro; M1 (CapacitorHttp obsoleto/patch de fetch — timeout nativo a
  validar); M2 (appId placeholder = bloqueador real de TestFlight); M3 (notif
  local é foreground-only — escopo, deixar claro ao tester); L1/L2/L3 menores.
- Etapa C1 implementada: migrate.js (novo, puro) + persistence.js estendido
  (não reescrito) + 3 guardas em App.jsx + Error Boundary em main.jsx + teste
  test_migrate.mjs (12/12). Sem regressão (paridade 6/6). -> qa/07-c1-tela-branca.md
- HARD STOP para teste no iPhone antes da próxima etapa.
