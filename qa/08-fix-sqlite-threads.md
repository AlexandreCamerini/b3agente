# QA 08 — Fix: SQLite entre threads (500 intermitente em toda rota autenticada)

## Sintomas em produção (relatados + traceback do Railway)
- Radar: "A varredura falhou — Internal Server Error" em `/api/scan?period=2y`.
- Welcome sempre pedindo login/criar conta (sessão salva nunca restaurava).
- "Dados sempre os mesmos independente do usuário" (app caía no escopo
  anônimo do deviceStore porque o `/api/auth/me` falhava).

## Causa raiz (confirmada pelo traceback)
```
File "app/main.py", line 54, in current_scope
    user = auth.resolve_session(_conn, ...)
sqlite3.ProgrammingError: SQLite objects created in a thread can only be
used in that same thread.
```
`_conn = db.connect()` era criada na thread principal no import; o FastAPI
executa dependências síncronas (`current_scope`, `require_user`) num POOL de
threads (anyio). Requisição caindo em outra thread ⇒ exceção ⇒ 500. Como o
pool alterna threads, o erro era INTERMITENTE — às vezes funcionava, o que
mascarou o diagnóstico. `current_scope` roda em TODA rota de dados, então o
bug afetava scan, auth/me, state, buy/sell etc.

## Correção (cirúrgica — call sites intactos)
1. `db.py` — `PRAGMA busy_timeout=5000` no `connect()` (escritas concorrentes
   esperam o lock do WAL em vez de falhar).
2. `db.py` — novo `db.shared()`: proxy `_ThreadLocalConnection` que abre UMA
   conexão real por thread e delega tudo via `__getattr__`. Mesma interface;
   nenhum dos ~76 usos de `_conn` em `main.py` mudou.
3. `main.py` linha 30 — `_conn = db.connect()` → `_conn = db.shared()`.
4. `main.py` — handler global de exceção: erro não tratado vira JSON
   `{"detail": "Tipo: mensagem"}` (o api.js já exibe `detail`); o traceback
   segue integral nos logs do Railway.

Por que não `Depends(get_conn)`: exigiria tocar todos os handlers (diff
enorme, alto risco de regressão) contra o princípio "estender, nunca
reescrever". Por que não `check_same_thread=False` na conexão global: sem
lock próprio, duas threads na MESMA conexão corrompem estado interno.

## Itens que NÃO precisaram de código (já implementados; eram mascarados)
- Welcome boot gate (BLOCO 2): sempre aparece; com sessão restaurada mostra
  "Conectado como X" + Entrar — dependia do `/auth/me` que 500ava.
- Escopo por usuário no device (`_setDeviceScope`): ativado no `auth.me()`/
  login — idem.
- Scanner robusto por ativo (erro de 1 símbolo vai para `errors`): o crash
  acontecia ANTES do scanner, no `current_scope`.
- notify.js: agendamento nativo (`schedule:{at}`) já migrado; `diag()` mudo
  no device = binário desatualizado (falta `cap sync` + rebuild — ambiente).

## Validação
- `py_compile` OK (db.py, main.py, teste novo).
- Suítes backend: **85 passed, 0 failed** (inclui `test_thread_safety.py`
  novo: resolve_session em 8 threads × 32 chamadas; escrita concorrente;
  visibilidade entre threads — o 1º teste FALHA com o código antigo).
- `node --check` OK (notify, persistence, sync, api, migrate, finance).
- Balance checker App.jsx: OK (inalterado).
- Suítes web: OK, exceto `test_notify.mjs` por ausência de `@capacitor/core`
  no ambiente de build do pacote (sem node_modules/rede) — pré-existente e
  ambiental; roda normal após `npm ci`.

## Dependências de ambiente (fora do código)
- Volume Railway em `/data` + `B3_DB_PATH=/data/b3.db` (feito pelo Alex).
- iPhone: `npm run build && npx cap sync ios` + rebuild no Xcode (leva o
  código atual ao aparelho; destrava `diag()` e o teste de notificação).
