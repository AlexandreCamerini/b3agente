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

## 2026-07-06 — Revisão Total · FASE 1 (STU + Setups BR)
- Causa raiz da divergência N1×N2 confirmada no código: três caminhos de
  insumo independentes (scanner / build_context do N2 / contexto parcial do
  N3, deep com cache por DIA) + nenhuma chamada LLM com temperature.
- Implementado o Snapshot Técnico Único (`technical_snapshot.py`): fonte única
  cacheada por fingerprint com `snapshotId`; N1, N1-deep, N2, N2 legado, N3 e
  /api/technicals religados; cache do deep re-chaveado por snapshotId;
  temperature=0.2 nos 3 provedores (com guarda p/ modelos OpenAI de raciocínio);
  snapshotId no prompt e visível na UI (Radar, N2, N3).
- 7 setups BR adicionados a `setups.py` (9.1/9.2/9.3, IFR2, PFR, 123, Ponto
  Contínuo, Inside Bar, 9.4 LW) com gatilho/invalidação/alvo didáticos;
  SMA200/EMA72/RSI2 no `indicators.py`. Regras auditáveis em qa/SETUPS.md.
- Testes: 66/66 suítes puras existentes · test_setups_br 17/17 ·
  test_snapshot_consistency (ACEITE F1) 8/8. -> qa/12-fase1-stu-setups-br.md
- HARD STOP: validar 5 tickers no device comparando N1 vs N2 (mesmo #id).
- Scripts atualizados (instalar/atualizar/executar + delegados): manifesto do
  verificar-arquivos.sh ganhou technical_snapshot.py (F1) e as lacunas
  agent.py/push.py + gates nominais da F1; atualizar.sh valida o manifesto na
  entrega e o health pós-deploy reprova build sem snapshotId no
  /api/technicals; atualizar-servidor.sh imprime o snapshot no health;
  instalar.sh roda o manifesto como 1ª prova; test.sh ganhou fallback offline
  (mini-runners) — provado no sandbox: manifesto ✓ e 14/14 suítes offline
  (incluindo auth/persistence/multiuser/metering, antes não-rodáveis aqui).
- Blindagem do deploy (erro recorrente "'origin' does not appear..."): o clone
  do Alex TEM origin correto (visto no .git do zip) — o erro vem de rodar o
  deploy em pasta extraída do zip (sem .git). atualizar-servidor.sh agora
  valida repo/pasta e reanexa o origin canônico sozinho; atualizar.sh reprova
  cedo (antes do overlay) quando a pasta não é o clone, com instrução do
  caminho certo. Cenários simulados e aprovados.
- Blindagem 2 do deploy ("! [rejected] main -> main"): atualizar-servidor.sh
  agora faz fetch + diagnóstico de divergência antes do push — remoto à frente
  com ancestral comum: rebase automático e segue; conflito real: aborta o
  rebase (local preservado) e instrui; históricos sem ancestral comum (repo
  local recriado): para e instrui o force-with-lease (local = fonte da
  verdade no fluxo do projeto). Três cenários simulados e aprovados.
  Contexto: pytest completo do Alex passou 154/154 com a F1 aplicada.

## 06/07/2026 — FASE 2 (Revisão Total): funil + Watchlist + Portfólio + Acompanhar
- Navegação: Acompanhar·Radar·Watchlist·Portfólio·Operador IA (ids internos
  preservados; deep-links/openAvaliar seguem valendo). "Avaliar" deixou de ser
  aba; N2 abre como detalhe do card.
- Acompanhar (home): resumo do dia determinístico (finance.js), operações de
  hoje, setups da watchlist, destaque de oportunidade fora da watchlist com
  leitura N1 (1×/sessão; cache por snapshotId limita a 1 cota/ativo/dia) e
  estado vazio para novato.
- Watchlist: ordenação permanente por confluência do STU + filtro por direção;
  badges de tier/veredito/setup/"em carteira"; histórico por ativo (a) resumo
  no card → (b) sparkline ▲/▼ + (c) tabela no detalhe.
- Portfólio: distância % de stop/alvo, dias em operação, R:R, % do capital,
  setup de entrada com status do gatilho, alerta sem stop; venda TOTAL/PARCIAL
  com confirmação (parcial preserva o preço médio).
- Stores: buy(meta sanitizada)+sell(qty) espelhados em store.py e nos DOIS
  stores do persistence.js (interface idêntica, invariante mantida);
  /api/buy|/api/sell estendidos; api.scan(period, tickers).
- Testes: server/tests/test_fase2_portfolio.py (7/7) e
  web/tests/test_fase2_portfolio.mjs (13/13, deviceStore real com Capacitor
  simulado); test_radar.mjs atualizado; 9/9 web, 20/24 backend no sandbox
  (4 puladas por httpx ausente — verdes no pytest completo).
- QA: qa/13-fase2-funil.md com o roteiro do hard stop no iPhone.

## 06/07/2026 — FASE 3: cards (mock v2) + Operador IA instrumentado
- Cards Radar/Watchlist/Portfólio no design aprovado: `PlanRuler` (régua
  invalidação→gatilho→alvo e stop→PM→alvo com "agora"), `PosPill` global,
  "+ Watchlist" no Radar (saiu "Análise completa"), linha de links na
  Watchlist, "Compras desta posição" + memória do PM no Portfólio, edição de
  stop/alvo sob demanda.
- Timeout do Operador resolvido em 3 frentes: run-now em background;
  `serverEnabled` por chamada LIVE (fim do estado fantasma otimista) com
  confirmação via status; instrumentação completa (Diário `/api/agent/log`,
  anel de passadas, próxima passada, guard de sobreposição, `[slow]` no
  middleware p/ logs do Railway).
- QA: qa/14-fase3-cards-operador.md · testes: test_fase3_operador.py (6/6),
  regressão 21 suítes backend + 9 web OK.
[2026-07-07T03:45:00Z] FASE 4: identidade travada (com.alexandrecamerini.bolsia / BolsIA) aplicada via scripts/atualizar-identidade.sh (idempotente). Bug da venda silenciosa = sellModal fora das deps do useMemo(A); corrigido + guardiao test_wiring_deps.mjs. Radar 1x/dia (radar_daily.py, 08:45 BRT, dentro do scheduler existente) e DeepModal fechavel/rolavel + colapsaveis + concisao no prompt N1. Retry de turno gravou a implementacao antes da adocao formal; tratada como nao-confiavel, revisada linha a linha e adotada apos confirmacao do Alex. Corte: 23 backend + 11 web verdes.
[2026-07-07T04:20:00Z] BLOCO 2 (login social): ponte nativa social.js (apple-sign-in + google-auth, import tardio), name-hint do 1o consentimento Apple persistido, siwa.py com exchange no login e REVOKE na exclusao (5.1.1(v)), URL scheme do Google automatizado no setup-ios.sh. Roteiro completo p/ Alex em LOGIN-SOCIAL.md (portais A/B, maquina C, matriz de teste D1-D8). Corte: 24 backend + 12 web verdes. Risco assumido: majors dos plugins sob Capacitor 8 nao verificaveis offline (latest + fallback C2).
[2026-07-07T04:50:00Z] BLOCOS 3+4: auditoria final (robustez OK: timeouts, ErrorBoundary, offline outbox, vazios, KPIs em finance.js), checklist App Store completo em qa/17 (App Privacy exato, ficha da loja pronta, categoria Educacao+Financas, 4+, notas p/ revisor), POLITICA-PRIVACIDADE.md pronta p/ publicar, MERCADO-RENTABILIZACAO.md (freemium R$14,90/99ano, BYOK gratis, Pro = recursos de servidor; canais: shorts do Radar diario, creators medios, ASO; linha vermelha CVM; roadmap 5 features). Corte final: 24 backend + 12 web verdes.
[2026-07-07T10:45:00Z] HARD STOP feedback: ERESOLVE no npm (codetrix peer Cap6 vs Cap8). Corrigido: migracao p/ @capgo/capacitor-social-login (um plugin, Apple+Google), social.js reescrito com extracao defensiva de retorno, teste atualizado e vigiando regressao dos plugins abandonados. Roteiro C2 atualizado (limpar package-lock antes do install; nunca --legacy-peer-deps).
