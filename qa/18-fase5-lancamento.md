# QA 18 — FASE 5 "Lançamento"
*07/07/2026 · revisão integral + correções + observabilidade + performance*

## Escopo da revisão

Revisão completa da aplicação (backend FastAPI, web React, projeto iOS,
fluxos funcionais, design system, segurança do login) com baseline verde
ANTES de qualquer mudança: 16 suítes backend (modo offline) + 12 suítes web.

## Bugs encontrados e corrigidos

### B1 — "+ Watchlist" do Radar não insere o ativo (silencioso)
- **Sintoma:** toque em "+ Watchlist" no card do Radar mostra "adicionado ✓",
  mas o ativo não aparece na Watchlist.
- **Causa-raiz:** `A.addToWatchlist` e `ctx.openAvaliar` usavam
  `store.putWatchlist([...watchlist, t])`. Nos DOIS stores, `putWatchlist`
  filtra a lista contra `knownTickers()` = catálogo (20 tickers) + `custom`.
  O universo do Radar tem ~74 tickers (`DEFAULT_UNIVERSE` do scanner) — um
  ticker fora do catálogo era descartado em silêncio (web:
  `store.set_watchlist`; iOS: `deviceStore.putWatchlist`).
- **Correção:** ambos os caminhos passam a usar `store.addWatchlistTicker(t)`
  (rota `/api/watchlist/add` no web; validação via servidor + registro em
  `doc.custom` no iOS) e conferem o retorno (`watchlist.includes(t)`), com
  erro claro se não entrar.
- **Guardião:** `web/tests/test_radar_watchlist.mjs` (10 asserções: proíbe
  putWatchlist nesses caminhos, exige a conferência, tranca o wiring do card
  e o registro em custom no deviceStore).

### B2 — Push (APNs) nunca registra ("tempo esgotado no registro do push")
- **Sintoma:** "Ativar push das ações" termina em timeout de 15s mesmo com
  capability + chaves APNs corretas.
- **Causa-raiz:** o plugin `@capacitor/push-notifications` exige que o
  AppDelegate reencaminhe `didRegisterForRemoteNotificationsWithDeviceToken`
  e `didFailToRegisterForRemoteNotificationsWithError` via
  `NotificationCenter` (`.capacitorDidRegister/DidFail...`). O
  `AppDelegate.swift` não tinha os dois callbacks — o `register()` do JS
  jamais resolvia.
- **Correção:** callbacks adicionados; `PushNotifications.presentationOptions
  = [alert, sound, badge]` no `capacitor.config.ts` (sem isso, push recebido
  com o app ABERTO é suprimido pelo iOS). Exige `cap sync` + rebuild.
- **Guardião:** `web/tests/test_push_wiring.mjs` (AppDelegate, config, SPM,
  entitlements).
- **Nota:** as notificações LOCAIS (stop/alvo/variação/teste) já estavam
  corretas no código (`notify.js` + ids persistidos + clamp de horário);
  regressão coberta por `test_notify.mjs` (segue verde).

## Login — hardening para o lançamento (auth.py / main.py)

- **Rate-limit de força bruta**: janela deslizante por (ip, e-mail) nas rotas
  `/api/auth/{register,login,oauth}` — 10 falhas/15 min (envs
  `B3_AUTH_RL_MAX`, `B3_AUTH_RL_WINDOW_S`); sucesso zera o contador; IP real
  atrás do proxy do Railway via `X-Forwarded-For`.
- **Teto de senha (128)**: PBKDF2 com 240k iterações sobre senha gigante era
  vetor de DoS; `verify_password` devolve False sem computar.
- **Purga de sessões expiradas**: `purge_expired_sessions` no boot + a cada
  24h (o resolve lazy já cobria o token consultado; isto cobre os
  abandonados).
- Revisado e mantido: PBKDF2 240k + salt, mensagens genéricas (não revelam se
  o e-mail existe), token opaco de 256 bits, `pass_hash`/`provider_sub` nunca
  saem ao cliente, SIWA exchange+revoke (5.1.1(v)), seed idempotente.
- **Testes novos:** `test_senha_gigante_e_rejeitada`, `test_throttle_de_login`,
  `test_purga_de_sessoes_expiradas` (em `test_auth.py`).

## Observabilidade (novo módulo `server/app/obslog.py`)

- Log estruturado (`[b3][cat] msg k=v`) no stdout do Railway + ring buffer em
  memória (cap 1000), thread-safe, stdlib-only, nunca levanta.
- Middleware: TODA request de API vira evento `req` (método, rota, status,
  duração, ip); >2s vira `slow` (warn); 5xx vira error; exceções não tratadas
  viram `err` com o traceback continuando no Railway. `/api/obs` não se
  auto-loga.
- `GET /api/obs/logs?n=&level=&cat=` → `{logs, stats}` (uptime + contadores
  por categoria). Acesso: `B3_ADMIN_EMAILS` (lista) ou, sem a env, apenas a
  PRIMEIRA conta criada.
- UI: Perfil → Observabilidade → seção "LOGS DO SERVIDOR" (filtros tudo /
  lentos+erros / só erros; auto-refresh 15s; 403 esconde a seção).
- **Teste:** mini-runner embutido (`python3 app/obslog.py`, 9 asserções).

## Performance — cache de candles persistente (a "demora para atualizar")

- **Causa da lentidão:** o cache de candles era só memória; cada redeploy do
  Railway zerava tudo e a 1ª varredura rebaixava 2 anos × ~74 ativos do
  Yahoo (minutos, com risco de 429).
- **Correção:** L2 em SQLite (`candle_cache(k, currency, candles, at)` no
  MESMO banco do app, volume `/data`), write-through no miss e no delta;
  reboot reidrata e busca só a janela de 1 mês. Opt-in explícito
  (`candle_cache.configure_db(conn)` no boot do main) — suítes puras seguem
  sem tocar disco; falha de SQLite degrada para o comportamento antigo.
- **Testes novos:** `test_l2_persiste_e_reidrata_apos_reboot`,
  `test_l2_desligado_mantem_comportamento_antigo`,
  `test_l2_corrompido_degrada_para_miss`.
- **Correção de portão:** o bloco `__main__` do `test_candle_cache.py` estava
  no MEIO do arquivo — os 3 testes do BLOCO A1 abaixo dele nunca rodavam no
  modo offline. Movido para o fim; agora 11 testes rodam no portão.

## Scripts e documentação

- `operar.sh` (novo, raiz): `status | testes | backup | deploy "msg" | ajuda`
  — fachada sobre `test.sh`, `backup-db.sh`, `atualizar-servidor.sh`.
- `GUIA-OPERACAO.md` (novo): instalação, execução, testes, deploy, backup,
  logs e solução de problemas em linguagem para não-desenvolvedor.
- `ATUALIZAR-Git-Railway-iOS.md` atualizado com o roteiro desta entrega.

## Evidência de testes (sandbox, modo offline)

- Backend: 16/16 suítes OK (incl. auth com 3 testes novos e candle_cache com
  6 novos/reativados) · `py_compile` OK em todos os módulos.
- Web: 14/14 suítes OK (12 existentes + `test_radar_watchlist.mjs` +
  `test_push_wiring.mjs`) · parse Babel/JSX OK em App.jsx e módulos tocados.
- Pendente (exige ambiente do Alex): `pytest` completo no venv (cobre as 2
  suítes com FastAPI/httpx), build do Xcode e HARD STOP no iPhone físico
  (roteiro no ATUALIZAR).

## Riscos e reversão

- Mudanças de UI são cirúrgicas (2 funções + 1 seção nova); wiring guardado
  por testes de texto. Backend aditivo (módulo novo + tabela nova + rotas
  novas); nenhum contrato existente mudou. Reversão: `git revert` do commit
  da entrega; a tabela `candle_cache` pode ficar (ignorada por versões
  antigas).
