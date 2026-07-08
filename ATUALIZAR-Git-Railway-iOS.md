# ATUALIZAR — Git · Railway · iOS
## Entrega FASE 5 "Lançamento": correções (watchlist do Radar + push), login blindado, observabilidade e cache persistente
*07/07/2026 · detalhes técnicos em `qa/18-fase5-lancamento.md`*

## O que mudou nesta entrega

1. **"+ Watchlist" do Radar CORRIGIDO:** o botão dizia "adicionado ✓" mas o
   ativo nunca entrava quando estava fora do catálogo de 20 tickers (o Radar
   varre ~74). `addToWatchlist` e a ponte `openAvaliar` agora usam
   `addWatchlistTicker` (valida e registra em `custom` nos dois stores) e
   CONFEREM se o ticker entrou. Guardião: `web/tests/test_radar_watchlist.mjs`.
2. **Push (APNs) CORRIGIDO na raiz:** o `AppDelegate.swift` não repassava o
   registro do APNs ao Capacitor — o "Ativar push das ações" SEMPRE caía no
   timeout de 15s, com tudo certo no portal. Adicionados os dois callbacks
   (`didRegister/didFail...RemoteNotifications`) + `PushNotifications.
   presentationOptions` no capacitor.config (banner com o app aberto).
   Guardião: `web/tests/test_push_wiring.mjs`. **Exige recompilar no Xcode.**
3. **Login pronto para o lançamento:** rate-limit de força bruta nas 3 rotas
   de auth (10 falhas/15 min por ip+e-mail; sucesso zera; ajustes
   `B3_AUTH_RL_MAX`/`B3_AUTH_RL_WINDOW_S`), teto de 128 caracteres na senha
   (anti-DoS do PBKDF2) e purga automática de sessões expiradas (boot + 24h).
   E-mail/senha, Apple e Google seguem como estavam (código do social pronto;
   ativação é a Parte A–D do `LOGIN-SOCIAL.md`).
4. **Observabilidade com logs detalhados:** novo `server/app/obslog.py` — toda
   request de API (rota, status, duração, ip), lentidões (>2s), erros 5xx e
   eventos de auth entram num log estruturado no stdout (Railway) E num ring
   buffer consultável em `GET /api/obs/logs`. A tela Perfil → Observabilidade
   ganhou a seção "Logs do servidor" com filtros (tudo / lentos+erros / só
   erros). Acesso restrito: `B3_ADMIN_EMAILS` no Railway, ou (sem a env) só a
   PRIMEIRA conta criada.
5. **Fim da lentidão pós-deploy (cache persistente):** o cache de candles
   ganhou um segundo nível em SQLite (tabela `candle_cache`, no volume
   `/data`). Redeploy do Railway reidrata a série e busca só o DELTA recente —
   antes, cada deploy rebaixava 2 anos × 74 ativos do Yahoo (a "demora para
   atualizar"). Testes novos em `test_candle_cache.py` (incl. reboot e
   corrupção); de quebra, 3 testes antigos que não rodavam no modo offline
   voltaram ao portão.
6. **Operação em um comando:** novo `operar.sh` na raiz —
   `status | testes | backup | deploy "msg" | ajuda`. Guia completo para
   não-desenvolvedor em `GUIA-OPERACAO.md`.

## 1) Validação local (antes de subir)

```bash
bash operar.sh testes    # 16 suítes backend + 14 suítes web devem passar
```

## 2) Git + Railway

```bash
bash operar.sh deploy "FASE 5: watchlist do radar + push APNs + login blindado + observabilidade + cache persistente"
```

Variables (conferir no Railway):
- `B3_DB_PATH=/data/b3_agente.db` (volume persistente — OBRIGATÓRIO; o cache
  novo também vive aí)
- **novo (recomendado)** `B3_ADMIN_EMAILS=seu-email@...` — quem vê os "Logs do
  servidor" no app (sem a env, só a 1ª conta criada vê)
- (opcionais) `B3_AUTH_RL_MAX=10` · `B3_AUTH_RL_WINDOW_S=900`
- APNs (como antes): `APNS_TOPIC=com.alexandrecamerini.bolsia`,
  `APNS_TEAM_ID`, `APNS_KEY_ID`, `APNS_AUTH_KEY`, `APNS_SANDBOX=1` (builds do
  Xcode; remover no TestFlight)

## 3) iOS — recompilar (necessário pelo item 2)

```bash
cd web && npm run ios     # vite build + cap sync + abre o Xcode
```

No Xcode: conferir **Push Notifications** em Signing & Capabilities →
Product → Clean Build Folder → instalar no iPhone.

## 4) HARD STOP — roteiro de teste no aparelho

1. **Watchlist via Radar:** Radar → um ativo FORA do catálogo (ex.: MGLU3,
   GGBR4, CSNA3) → "+ Watchlist" → toast "✓" → abrir a aba Watchlist e
   CONFERIR que o ativo está lá, com cotação. Repetir com "Levar para a
   watchlist →" no destaque do Acompanhar.
2. **Push:** aba Operador IA → "Ativar push das ações" → deve concluir SEM o
   erro de tempo esgotado (aparece "push ativo ✓" ou o motivo exato). Depois
   Perfil → Observabilidade → "Testar push agora" com o app em segundo plano
   → banner deve chegar.
3. **Notificações locais (regressão):** Config → ligar notificações → "Testar
   notificação" (app em segundo plano) → banner em ~5s.
4. **Login:** sair e entrar de novo (e-mail/senha). Errar a senha 10+ vezes →
   mensagem "Muitas tentativas... aguarde"; acertar depois do intervalo →
   entra normalmente.
5. **Logs do servidor:** Perfil → Observabilidade → seção "LOGS DO SERVIDOR"
   deve listar as requests que você acabou de fazer (com duração). Filtro
   "só erros" deve esvaziar (ou mostrar apenas erros reais).
6. **Velocidade pós-deploy:** logo após o redeploy, abrir o Radar — o
   resultado deve vir em segundos (reidratado do cache persistente), não em
   minutos.

Qualquer item falhando: copie a linha correspondente dos "Logs do servidor"
(ou do Diário) que eu sigo o diagnóstico.

## Próximo bloco (após o hard stop)
Submissão App Store (`qa/17-auditoria-appstore.md`) + ativação do login social
(`LOGIN-SOCIAL.md`, Partes A–D).
