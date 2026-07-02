# ATUALIZAR — Git · Railway · iOS (Fase 2: multiusuário)

Este guia aplica a **Fase 2** (auth + base multiusuário) ao seu ambiente. O
código já foi validado aqui (todas as suítes verdes, `py_compile`, `node --check`,
balance checker do `App.jsx`, grep de wiring). O que falta roda **na sua máquina**,
com as **suas** credenciais — eu não tenho rede/Xcode/Railway aqui.

> **Pare no hard-stop de device** ao final. Só depois seguimos para a Fase 3.

---

## 0) O que mudou nesta fase (resumo)

**Backend (FastAPI/SQLite)**
- Schema novo e limpo com `user_id`: tabelas `users` e `sessions` (`db.py`).
- KV agora é **escopado por usuário** (`u:<id>:<seção>`); sem token => escopo
  **anônimo/legado** (web sem login e as suítes antigas seguem idênticos).
- Novo `auth.py`: e-mail/senha (PBKDF2, stdlib), sessões com token, e verificação
  OIDC de Apple/Google (opcional, degrada limpo sem a dependência/config).
- `main.py`: endpoints `/api/auth/{register,login,oauth,me,logout}` e
  `DELETE /api/account`; toda rota de dados resolve o escopo pelo `Bearer` token.
- `store.py`: `seed_user_from` (1º login adota o dado local — **BYOK preservado**),
  `export_sections`, `delete_user_data` (exclusão de conta).

**Cliente (React/Capacitor)**
- `api.js`: token de sessão vira `Authorization: Bearer` em toda chamada.
- `sync.js` (novo): cache otimista + **fila offline** (reaplica ao reconectar) —
  servidor é a fonte da verdade quando logado.
- `persistence.js` (estendido, **não reescrito**): `serverStore` fala via sync;
  superfície `auth` (login/registro/logout/excluir conta); `deviceStore` segue
  **local-first** no iOS (a conta habilita identidade + futura cota de IA).
- `App.jsx`: tela de conta (`AuthModal`) + item "Conta" no Perfil. **App continua
  abrindo sem login** (conta é opcional).

**Infra**
- WAL já estava ligado; agora documentado **volume persistente + backup**.
- `scripts/backup-db.sh` (novo): backup online consistente do SQLite.
- `requirements*.txt`: `PyJWT[crypto]` (só para login Apple/Google).

---

## 1) Git — subir as mudanças

Do diretório `b3-agente/`:

```bash
git checkout -b fase2-multiusuario
git add -A
git commit -m "Fase 2: auth + base multiusuário (schema user_id, sync, exclusão de conta)"
```

Enviar (o GitHub não aceita senha — use um **Personal Access Token** como senha):

```bash
git push -u origin fase2-multiusuario
# usuário: seu-usuário-github   |   senha: <COLE O PAT>
```

> Se o push reclamar de históricos divergentes (repos recriados):
> `git pull --no-rebase --allow-unrelated-histories origin main` e resolva os
> conflitos antes de repetir o push.

Faça o merge para `main` (PR ou local) quando quiser disparar o deploy.

---

## 2) Railway — deploy + **volume persistente** (crítico)

O critério de aceite da Fase 2 inclui **"os dados sobrevivem a um redeploy"**.
Isso só vale se o SQLite morar num **volume**, não no disco efêmero do container.

1. **Deploy** normal (cada `git push` na branch publicada refaz o deploy).
   - `Settings → Root Directory = server` (onde estão `requirements.txt` e `app/`).
2. **Adicionar o volume**: serviço → **Variables/Volumes → New Volume**
   - **Mount path**: `/data`
3. **Variáveis de ambiente** (serviço → **Variables**):
   - `B3_DB_PATH = /data/b3_agente.db`  ← coloca o banco **no volume**.
   - *(opcional)* `B3_SESSION_TTL_DAYS = 90`  (validade da sessão).
   - *(opcional, login social)* `GOOGLE_CLIENT_ID = <client_id>` e/ou
     `APPLE_CLIENT_ID = <client_id/service_id>`. Sem isso, **e-mail/senha funciona
     normalmente** e o login social devolve erro acionável (não derruba o app).
4. **Redeploy** e teste:
   `https://SEU-APP.up.railway.app/api/health` → `{"ok":true}`.

### Prova do volume (faça no hard-stop)
Crie uma conta, faça uma operação, **Redeploy** pelo painel, recarregue: os dados
devem continuar lá.

### Backup
Rode quando quiser (ou agende um cron job no Railway):
```bash
B3_DB_PATH=/data/b3_agente.db BACKUP_DIR=/data/backups bash scripts/backup-db.sh
```
Mantém os 14 backups mais recentes em `/data/backups` (no volume).

---

## 3) iOS — rebuild e TestFlight

Na sua máquina (com o backend já no Railway, HTTPS):

```bash
cd web
npm install
npm run build
npx cap sync ios
npx cap open ios     # abre o Xcode
```

No Xcode: selecione o destino (device/simulador) → **Run** para testar, ou
**Product → Archive → Distribute → TestFlight** para subir.

> Diálogo de senha do **keychain** ao assinar é comportamento normal do macOS —
> use **"Sempre permitir"** com a senha de login do Mac.

> O app iОS é **local-first**: configure o endereço do servidor em
> *Perfil → Conta & preferências* apontando para a URL do Railway e toque em
> **Testar conexão**. A conta (login) é **opcional** e usa esse mesmo endereço.

---

## 4) ✋ Hard-stop de device (critério de aceite da Fase 2)

Valide no aparelho/navegador antes de seguir para a Fase 3:

- [ ] **Criar conta** (e-mail/senha) — entra e mostra a carteira.
- [ ] **Login** com a conta criada.
- [ ] **Logout** — volta ao modo anônimo, app continua funcionando.
- [ ] **Excluir conta** — pede confirmação, apaga e volta ao anônimo.
- [ ] **Dois usuários isolados** — A e B veem carteiras diferentes (sem vazamento).
- [ ] **Usuário pré-existente** (dado antigo no aparelho) abre **sem tela branca**.
- [ ] **Dados sobrevivem a um redeploy** no Railway (prova do volume).

Se algo travar (especialmente tela branca), abra o **Safari Web Inspector**
(simulador ou device via USB) e me mande o erro do console — o ponto provável é
acesso a campo `undefined` em estado não migrado, e tratamos pontualmente.

---

## Notas

- **BYOK intacto**: a chave nunca trafega ao cliente nem é versionada. No 1º login,
  a semente da conta vem do escopo local (web: escopo anônimo do servidor; iOS: o
  doc do aparelho) — a chave é preservada no servidor, por usuário.
- **Login social (Apple/Google)** está pronto no backend, mas exige os *client IDs*
  (passo 2.3) e o SDK nativo de Sign in with Apple/Google para obter o `idToken` no
  app — integração nativa que encaixo quando você quiser. E-mail/senha já cobre o
  hard-stop inteiro.
- **iOS como cache sincronizado** (deviceStore espelhando o servidor) é deliberadamente
  mínimo nesta fase para não desestabilizar o caminho local-first; a migração ampla
  de seções por usuário nos dois stores é da **Fase 3**.

---

## Fase 3 — IA gerenciada + escopo por usuário no aparelho

### IA gerenciada (item 2) — variáveis no Railway
Caminho PARALELO ao BYOK. Só vale para usuário LOGADO sem chave própria; quem tem
BYOK usa a própria chave, sem cota. Se você NÃO definir a chave abaixo, nada muda
(segue BYOK/erro acionável). No serviço → **Variables**:

- `B3_MANAGED_LLM_KEY` = chave do provedor (server-side; nunca vai ao cliente).
- `B3_MANAGED_LLM_PROVIDER` = `openai` (ou `anthropic`/`google`/`local`).
- `B3_MANAGED_LLM_MODEL` = `gpt-4o-mini` (modelo barato; ajuste ao provider).
- `B3_MANAGED_LLM_BASE_URL` = (opcional) para provider compatível/local.
- `B3_MANAGED_DAILY_QUOTA` = `20` (análises/dia por usuário; padrão 20).
- `B3_MANAGED_RATE_PER_MIN` = `6` (rate limit por usuário/minuto; padrão 6).

A cota/metering é por usuário (KV escopado), reseta por dia (UTC). Estado da IA
para a UI: `GET /api/ai/quota`. Ao estourar a cota, a análise responde **402** com
mensagem orientando a usar BYOK ou voltar amanhã.

### Escopo por usuário no aparelho (item 1)
No iOS, ao logar, os dados locais passam a um **namespace por usuário**
(`localStorage`, NÃO vira SQLite). O modo **anônimo é inalterado** (chave base) —
usuário existente/sem login não migra nada. 1º login no aparelho adota o doc
anônimo como semente; logout volta ao anônimo.

### Hard-stop (device) da Fase 3
- [ ] IA gerenciada: logado sem BYOK consome cota; ao estourar, bloqueia com a
      mensagem; com BYOK, ilimitado.
- [ ] Escopo por usuário: dois logins diferentes no MESMO aparelho têm dados
      locais isolados; logout volta ao anônimo sem tela branca.

> **Item 3 (disclaimers nos sinais)** — FEITO: rodapé fixo discreto sob cada
> sinal no `KpiBlock` ("Sinal gerado para fins educacionais — não é recomendação
> de compra ou venda"). Sem hard-stop próprio; valide visualmente junto com o
> resto. Texto trocável numa linha do `App.jsx`.

---

## Blocos 1·2·3 — Notificações · Welcome boot gate · Radar

### O que mudou (resumo)
- **web/src/notify.js**: ids persistidos entre aberturas (`b3-notify-nid`),
  entrega imediata sem `at` no passado, clamp de horário no `schedule`,
  `getPending()` e `diag()` com `pendingCount`.
- **web/src/App.jsx**: welcome vira portão de boot (sempre aparece; com sessão
  mostra "Conectado como X"); teste de notificação agendada passou a 30s;
  nova aba/tela **Radar**.
- **web/src/persistence.js**: `scan(period)` espelhado nos dois stores (aditivo).
- **web/src/api.js**: `api.scan` → `GET /api/scan` (timeout 120s).
- **web/src/disclaimers.js**: `DISCLAIMERS.radar` (aditivo).
- **server/app/scanner.py** (novo) + rota `GET /api/scan` no `main.py`.
- Testes: `test_scanner.py` e `test_radar.mjs` novos; `test_welcome.mjs`
  reescrito para o contrato de boot gate; `test_notify.mjs` estendido.

### Git
```bash
git add -A
git commit -m "Blocos 1-3: notificacoes nativas confiaveis, welcome boot gate, radar de mercado"
git push origin main
```

### Railway
- Deploy automático no push. **Nada obrigatório** de novo.
- Opcional: `B3_SCAN_UNIVERSE="PETR4,VALE3,..."` para sobrepor o universo do
  Radar sem redeploy de código.
- Continua pendente das Fases 2/3: volume `/data` + `B3_DB_PATH=/data/b3_agente.db`.
- Smoke test pós-deploy: `curl "https://SEU-APP.railway.app/api/scan?period=1mo&tickers=PETR4,VALE3"`
  → JSON com `results`, `disclaimer` e sem 5xx.

### iOS
```bash
cd web && npm install && npm run build && npx cap sync ios
# Xcode: rebuild no device / TestFlight
```
Sem plugin novo (o @capacitor/local-notifications já estava no projeto) — o
`cap sync` basta. Validar `notify.diag()` → `pluginLoaded:true`,
`permission:"granted"`, `pendingCount` após agendar.

### ✋ Hard-stops
Checklists completos por bloco em **ESTADO-Blocos-1-2-3-BolsIA.md** — validar
um bloco por vez antes de seguir.

---

## Blocos A·B·C·D·E — Diagnóstico de notificações · Radar v2 (setups) · Período unificado · Login persistido · Identidade iOS

### Ordem de execução (automatizada)
```bash
# 1) Servidor: commit + push + espera o deploy + smoke do /api/scan v2
bash scripts/atualizar-servidor.sh "Blocos A-E: radar v2 setups, periodo unificado, login persistido, identidade iOS"

# 2) iPhone: cadeia completa com verificação do plugin de notificações
bash scripts/instalar-iphone.sh
#    (se o SPM travar de novo, último recurso: --recriar-ios)
```

### Railway — variáveis (opcionais, mas recomendadas)
- `B3_APPLE_APP_ID=TEAMID.bundleid` → habilita o AutoFill do Chaveiro
  (Team ID em Xcode → Signing & Capabilities; bundle id do app).
- `B3_SCAN_UNIVERSE=...` → sobrepõe o universo do Radar (já existia).

### Xcode — uma vez (AutoFill do Chaveiro)
Signing & Capabilities → + Capability → **Associated Domains** →
`webcredentials:b3agente-production.up.railway.app`.

### O que mudou (resumo por arquivo)
- `server/app/setups.py` (novo) + `scanner.py`: setups, confluência, veredito,
  `modelo[]` no payload, ranking por confluência.
- `server/app/main.py`: análise completa e stop/alvo com candle_cache +
  janela do candlePeriod; endpoint `/.well-known/apple-app-site-association`.
- `server/app/candles.py`: helper `slice_for_config`. `llm.py`: prompt declara
  a janela real.
- `web/src/App.jsx`: painel Diagnóstico (notificações), Radar v2 (veredito/
  confluência/checklist/“Como o Radar analisa”), e-mail lembrado + AutoFill.
- `resources/` (fonte única da marca) + `scripts/instalar-iphone.sh`,
  `scripts/atualizar-servidor.sh`, `scripts/gen-assets.sh`.
- Testes: `test_setups.py` novo; `test_scanner.py` e `test_radar.mjs` no
  contrato v2 (+ guardrails de senha e linguagem).

### ✋ Hard-stops
Checklists por bloco em **ESTADO-Blocos-A-E-BolsIA.md** — ordem A → E.
