# ATUALIZAR — Git · Railway · iOS
**Entrega:** Fix SQLite entre threads (500 intermitente) + handler de erro JSON
**Data:** 2026-07-02

---

## O que mudou nesta entrega (resumo)

| Arquivo | Mudança |
|---|---|
| `server/app/db.py` | `busy_timeout=5000` no connect(); novo `db.shared()` (conexão por thread) |
| `server/app/main.py` | `_conn = db.shared()`; handler global de exceção → JSON `{"detail": ...}` |
| `server/tests/test_thread_safety.py` | **novo** — regressão do 500 (3 testes) |
| `qa/08-fix-sqlite-threads.md` | **novo** — diagnóstico e validação |

**Frontend: ZERO mudanças.** Welcome boot gate, sessão, escopo por usuário e
agendamento nativo de notificações já estavam corretos — eram vítimas do bug
do servidor. O `App.jsx` standalone acompanha o pacote apenas por convenção.

Este fix corrige de uma vez: Radar (500), sessão que não restaurava (login
toda vez), e os "dados iguais para qualquer usuário" (o app caía no escopo
anônimo local quando o `/auth/me` falhava).

---

## PASSO 1 — Subir o código (Git → Railway)

```bash
# na raiz do projeto (onde está o subir-git.sh)
# substitua os arquivos pelo conteúdo do b3-agente.zip desta entrega
./subir-git.sh   # ou: git add -A && git commit -m "fix: SQLite thread-safe (conexao por thread) + erro JSON" && git push
```

O push dispara o redeploy automático no Railway. Aguarde o card ficar verde.

**Pré-requisito já feito:** volume em `/data` + `B3_DB_PATH=/data/b3.db`.

### ✋ HARD STOP 1 — validar o servidor (web, antes do iOS)
1. Abra o app web (ou o iOS atual mesmo desatualizado — o servidor é o mesmo).
2. **Radar:** toque em varrer. Deve completar SEM "Internal Server Error".
   Se algum ativo individual falhar, ele aparece em `errors` sem derrubar o
   resto. Se houver erro geral agora, a mensagem mostra a CAUSA (novo handler).
3. **Conta:** crie uma conta → feche e reabra o app → o welcome deve mostrar
   **"CONECTADO COMO [você]" + botão Entrar** (não mais o formulário).
4. **Multiusuário:** crie uma 2ª conta, opere algo nela, deslogue, logue na
   1ª → cada conta deve ver SÓ os próprios dados.
5. **Persistência real:** com dados criados, faça um redeploy (Deployments →
   ⋮ → Redeploy) → logue de novo → dados devem estar lá (prova do volume).

Só siga ao Passo 2 com os 5 itens verdes.

---

## PASSO 2 — Atualizar o iPhone (leva o código ao aparelho)

O `diag()` mudo indica que o binário instalado é antigo. Procedimento completo:

```bash
cd web
npm ci                 # garante deps (inclui @capacitor/local-notifications)
npm run build
npx cap sync ios       # copia dist/ e instala o pod do plugin
npx cap open ios
```

No Xcode:
1. **Product → Clean Build Folder** (⇧⌘K)
2. **Apague o app do iPhone antes de instalar** (reseta o estado de permissão)
3. Rode no aparelho físico (▶)
4. No primeiro uso das notificações, **aceite a permissão**

Se `diag()` ainda vier `pluginLoaded:false` após isso:
```bash
cd web/ios/App && pod install && cd - && npx cap open ios   # e rebuild
```

### ✋ HARD STOP 2 — validar no device
1. `diag()` → `pluginLoaded:true`, `permission:"granted"`, `pendingCount` ≥ 0.
2. **Teste agendado (30s)** na Config → **coloque o app em background e
   TRAVE a tela** → a notificação chega no horário. Repita com o app FECHADO
   (swipe up): agendamentos nativos sobrevivem — deve chegar também.
3. Welcome no device: matar o app, reabrir → "Conectado como X" + Entrar.
4. Radar no device: varredura completa, disclaimers visíveis, período da
   Config refletido no resultado.

---

## Limitação conhecida (transparência)

Alertas de **stop/alvo/variação** dependem do monitoramento de preços, que
roda no app (loop JS). Com o app em segundo plano/fechado, o iOS suspende o
WebView — esses alertas específicos NÃO disparam fora do app. Notificações
**agendadas** (teste de 30s, lembretes com horário) funcionam em background
porque o agendamento é nativo (o iOS entrega sozinho). Alertas de preço com
app fechado exigem push server-side (APNs) — já no backlog de publicação.

---

## Validação executada antes do empacote
`py_compile` ✅ · suítes backend **85/85** ✅ (inclui thread_safety novo) ·
`node --check` ✅ · balance App.jsx ✅ · suítes web ✅ (`test_notify.mjs`
requer `npm ci` local — dependência nativa fora do pacote, pré-existente).
