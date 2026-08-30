---
phase: quick-260830-eqm
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server/app/semente_id.py
  - server/app/db.py
  - server/app/main.py
  - server/app/mydata_budget.py
  - server/requirements.txt
  - web-admin/src/App.jsx
  - server/tests/test_semente_id.py
  - server/tests/test_semente_id_http.py
  - server/tests/test_observabilidade.py
  - scripts/atualizar-identidade.sh
  - scripts/gerar-adhoc.sh
  - README.md
  - OPTIONS-MODELS.md
  - OPTIONS-SMOKE-TEST.md
  - TECHNICAL-ANALYSIS-MODELS.md
  - scripts/setup.sh
  - scripts/setup-ios.sh
  - scripts/run.sh
  - scripts/backup-db.sh
autonomous: false
requirements: [ADR23-F4-IDENT, ADR23-F4-OBS, ADR23-F4-RENAME]

user_setup:
  - service: semente-id
    why: "Registrar o client OIDC `boris-web-admin` no portal id.semente.dev (produção, repositório semente-id)"
    env_vars:
      - name: SEMENTE_ID_CLIENT_ID
        source: "saída de `railway ssh --service semente-id \"python -m app.cli client boris-web-admin --redirect https://boris.semente.dev/api/auth/semente-id/callback\"` (projeto `mydata`) — SÓ o Alex roda"
      - name: SEMENTE_ID_CLIENT_SECRET
        source: "mesma saída — aparece UMA única vez; entra só no env do Railway do serviço deste repo, nunca em commit ou log"
      - name: SEMENTE_ID_EMAIL_DONO
        source: "e-mail do Alex no portal (segunda trava sobre o RBAC)"
    dashboard_config:
      - task: "Definir as 3 variáveis no serviço deste repo"
        location: "Railway → serviço do Boris+ → Variables"

must_haves:
  truths:
    - "O login por e-mail+senha do painel admin continua idêntico ao de hoje (nenhuma regressão em /api/auth/login)"
    - "O login pelo portal semente.id abre o painel administrativo de ponta a ponta, provado por teste com id_token assinado por chave RSA gerada em memória — nenhum teste toca o portal de produção"
    - "GET /observabilidade responde as quatro chaves do contrato do ADR-23 (situacao, alertas, ultimas_execucoes, proximas)"
    - "GET /observabilidade nunca é público: sem chave de máquina válida nem sessão com observabilidade.ver, responde 401/403"
    - "`bash scripts/atualizar-identidade.sh --verificar` termina em IDENTIDADE OK, com appId ainda com.alexandrecamerini.bolsia"
    - "`bash scripts/executar.sh --testes` passa inteiro (pytest do backend + web/tests/*.mjs)"
    - "Nenhum client_secret aparece em commit, em log de servidor ou em mensagem de erro"
    - "O login dos clientes finais (e-mail/senha, Apple, Google no app) não é tocado"
  artifacts:
    - path: "server/app/semente_id.py"
      provides: "Cliente OIDC do portal: PKCE S256, troca do code, validação de id_token (iss/aud/nonce/exp) contra o JWKS, trava SEMENTE_ID_EMAIL_DONO"
      exports: ["ErroSementeId", "configurado", "iniciar_login", "concluir_login"]
      min_lines: 90
    - path: "server/tests/test_semente_id.py"
      provides: "Suíte do módulo com chave RSA em memória e fronteira httpx mockada"
      contains: "def test_"
    - path: "server/tests/test_semente_id_http.py"
      provides: "Ida e volta HTTP: /inicio redireciona ao portal, /callback devolve handoff, exchange abre sessão admin"
      contains: "TestClient"
    - path: "server/tests/test_observabilidade.py"
      provides: "As quatro chaves do contrato + fechamento de acesso"
      contains: "ultimas_execucoes"
  key_links:
    - from: "server/app/main.py"
      to: "server/app/semente_id.py"
      via: "rotas GET /api/auth/semente-id/inicio e /api/auth/semente-id/callback"
      pattern: "semente_id\\.(iniciar_login|concluir_login)"
    - from: "server/app/main.py (callback)"
      to: "POST /api/admin/mobile-handoff/exchange (já existente, ADR-014)"
      via: "redirect 302 para /admin/#handoff=<codigo de 90s, uso único>"
      pattern: "/admin/#handoff="
    - from: "web-admin/src/App.jsx (Login)"
      to: "/api/auth/semente-id/inicio"
      via: "botão 'Entrar com semente.dev' (navegação de página inteira, não fetch)"
      pattern: "semente-id/inicio"
    - from: "server/app/main.py"
      to: "agent_mod.status_snapshot / brapi_budget.snapshot / obslog.stats"
      via: "GET /observabilidade derivando o contrato de dado que já existe"
      pattern: "def observabilidade"
---

<objective>
Fase 4 do ADR-23 neste repositório: o painel administrativo do Boris+ ganha um
segundo caminho de entrada pelo portal `id.semente.dev`, o backend publica o
contrato de observabilidade que o console `admin.semente.dev` vai agregar, e a
cauda do rename BolsIA→Boris+ nas superfícies vivas é fechada pelo script
idempotente que já existe.

Purpose: entrar no SSO do portfólio somando um caminho, nunca substituindo o
que já funciona — e publicar o contrato que torna este sistema observável de
fora sem ninguém ler banco nem código alheio.

Output: `server/app/semente_id.py` + duas rotas de auth + `GET /observabilidade`
+ 3 suítes novas + `scripts/atualizar-identidade.sh` generalizado.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/quick/260830-eqm-fase-4-adr-23-boris-relying-party-do-sem/260830-eqm-SPEC.md
@CLAUDE.md

Fonte de verdade do protocolo (outro repositório — LEITURA APENAS, nunca editar):
- `~/dev/cvm-financas/docs/arquitetura.md` linhas 1138-1260 (ADR-23; a tabela de
  fases define esta fase como "Fase 4 · repo do BolsIA · web-admin como relying
  party + endpoint de observabilidade")
- `~/dev/cvm-financas/app/api/semente_id.py` (implementação de referência)
- `~/dev/cvm-financas/tests/test_semente_id.py` (padrão de teste a espelhar)
- `~/dev/cvm-financas/app/api/admin.py` linhas 737-753 (`GET /observabilidade`)

Deste repositório:
@server/app/auth.py
@server/app/rbac.py
@web-admin/src/App.jsx
@scripts/atualizar-identidade.sh

**Skills do projeto — checadas e dispensadas:** `didatica-boris` governa
vocabulário didático/assistente de IA; `swiftui-pro` governa código SwiftUI.
Este trabalho é auth de backend, contrato de observabilidade e rename de
strings operacionais — nenhuma das duas se aplica. Nenhum texto didático,
nenhuma manchete de card e nenhuma resposta de IA é tocada aqui.

<interfaces>
<!-- Contratos que o executor usa direto. Não explorar a base atrás deles. -->

De `server/app/auth.py` (já existente):
```python
class AuthError(Exception): ...
def create_session(conn, user_id: str, ttl_days: int = None) -> str
def resolve_session(conn, token: str) -> dict | None
def revoke_session(conn, token: str) -> None
def upsert_oauth_user(conn, provider: str, sub: str, email: str = None,
                      name: str = None, email_verified: bool = False) -> dict
def throttle_key(ip: str, email: str = "") -> str
def throttle_check(key: str, now: float = None) -> None   # levanta AuthError
def throttle_fail(key: str) -> None
def throttle_clear(key: str) -> None
```

De `server/app/rbac.py` (já existente):
```python
def ensure_bootstrap_role(conn, user: dict) -> None     # idempetente, aditivo
def permissions_for_user(conn, user_id: str) -> set     # vazio = sem papel admin
```

De `server/app/main.py` (já existente — o handoff do ADR-014 que este plano reusa):
```python
@app.post("/api/admin/mobile-handoff")            # mint de código de ~90s
@app.post("/api/admin/mobile-handoff/exchange")   # valida, exige papel admin,
                                                  # revoga (uso único), abre sessão
def require_permission(perm: str)                 # Depends() — sessão + permissão
def _client_ip(request: Request) -> str
_GATE_ALLOWLIST_PREFIXES = ("/api/auth/", "/api/health", "/api/market")
```

De `web-admin/src/App.jsx` (já existente, linhas 1248-1285): o `useEffect` do
App já lê `#handoff=<código>` da URL, limpa o hash, chama
`api.mobileHandoffExchange(codigo)`, recusa conta sem `permissions` e trata
código expirado. **O callback do portal desemboca exatamente nesse fluxo — não
existe caminho de troca novo para escrever no front.**

Dado já existente que alimenta `/observabilidade`:
```python
agent_mod.status_snapshot(_conn)  # -> killSwitch, pregaoAberto,
                                  #    heartbeat{haS, lacoVivo}, radarDiario,
                                  #    ordensPendentes{total}, passadas[],
                                  #    proximaPassadaEmS, intervaloS
brapi_budget.snapshot()           # orçamento de requisições do dia/mês
obslog.stats()                    # contadores "cat:level" desde o boot
obslog.recent(n, level="error")   # últimos erros do ring buffer
_usage_snapshot()                 # uso/custo de IA (já usado por /api/admin/summary)
timing_watch.kill_switch_on()     # 2º kill-switch (push do gatilho)
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Boris+ vira relying party do portal semente.id</name>
  <files>server/app/semente_id.py, server/app/db.py, server/app/main.py, web-admin/src/App.jsx, server/tests/test_semente_id.py, server/tests/test_semente_id_http.py</files>
  <behavior>
    Módulo `semente_id` (chave RSA gerada em memória, fronteira `httpx` mockada — nunca rede real):
    - `configurado()` é False sem SEMENTE_ID_CLIENT_ID+SECRET, True com os dois.
    - `iniciar_login` devolve URL de authorize com client_id, response_type=code, scope "openid email profile", code_challenge_method=S256, state e nonce; grava a linha do fluxo com o `code_verifier`, o `nonce` e o `destino`.
    - `concluir_login` no caminho feliz devolve (email minúsculo, destino) e o state deixa de existir (uso único).
    - State desconhecido/vencido falha com ErroSementeId.
    - `error=access_denied` do portal CONSOME o fluxo e falha (nenhuma segunda tentativa com o mesmo state).
    - nonce divergente falha; issuer diferente de SEMENTE_ID_URL falha; audience diferente do client_id falha; id_token expirado falha.
    - `email_verified` ausente/false falha.
    - SEMENTE_ID_EMAIL_DONO definida com OUTRO e-mail bloqueia; definida com o mesmo e-mail (comparação case-insensitive) deixa passar.
    - `/token` respondendo != 200 falha, e a mensagem do erro NÃO contém o client_secret.
    HTTP (TestClient):
    - GET /api/auth/semente-id/inicio com o portal configurado responde 302 para {SEMENTE_ID_URL}/authorize com os parâmetros de PKCE; sem configuração responde 503 com mensagem acionável (não 500, não redirect).
    - GET /api/auth/semente-id/callback com code/state válidos responde 302 para /admin/#handoff=<codigo>, e POST /api/admin/mobile-handoff/exchange com esse código devolve token + user com `permissions` não vazio.
    - Conta do portal SEM papel administrativo não recebe handoff: redirect para /admin/ com aviso, e nenhuma sessão plena nasce.
    - Regressão explícita: POST /api/auth/login e POST /api/auth/oauth respondem exatamente como antes.
  </behavior>
  <action>
Implementa D-IDENT (objetivo 1 do SPEC). Escreva os testes primeiro, veja falhar, então implemente.

**1. `server/app/semente_id.py` (novo).** Porte a lógica de
`~/dev/cvm-financas/app/api/semente_id.py` — mesmo protocolo, mesma ordem de
travas — mas com as dependências DESTE repositório: `httpx` no lugar de
`requests` e `PyJWT[crypto]` no lugar de `authlib` (as duas já estão em
`server/requirements.txt` e em `requirements-prod.txt`; não instale pacote
nenhum). Não copie o arquivo: adapte.

Superfície pública: `ErroSementeId`, `configurado()`, `iniciar_login(conn,
destino) -> str`, `async concluir_login(conn, state, code, erro_do_portal) ->
tuple[str, str]`.

Configuração, toda por env, com placeholder documentado no topo do módulo:
`SEMENTE_ID_CLIENT_ID`, `SEMENTE_ID_CLIENT_SECRET`, `SEMENTE_ID_URL`
(default `https://id.semente.dev`), `SEMENTE_ID_REDIRECT_BASE` (default
`https://boris.semente.dev`) e `SEMENTE_ID_EMAIL_DONO`. O `redirect_uri` é
`{SEMENTE_ID_REDIRECT_BASE}/api/auth/semente-id/callback` montado num único
lugar e usado idêntico no authorize e na troca do code — o portal compara por
igualdade exata, sem prefixo nem wildcard (restrição do SPEC).

`concluir_login` é `async` e usa `httpx.AsyncClient` para POST `/token` e GET
`/jwks`: I/O síncrono no event loop é proibido neste repositório. Valide o
id_token com PyJWT — monte a chave a partir do JWKS com `jwt.PyJWK` e chame
`jwt.decode` com `algorithms=["RS256","ES256"]`, `audience=<client_id>`,
`issuer=<SEMENTE_ID_URL>` e `options={"require": ["exp","iss","sub","aud"]}`;
depois compare o `nonce` com o gravado no fluxo e exija
`email_verified` verdadeiro. Nunca inclua o client_secret, o code nem o
id_token em mensagem de erro ou log — a mensagem diz o que falhou, não com quê.

Trava do dono: aplique `SEMENTE_ID_EMAIL_DONO` como no MyData E documente no
docstring que ela é a SEGUNDA trava — a primeira é o RBAC do ADR-013 deste
repo, que já recusa conta sem `permissions` no exchange do handoff. As duas
juntas, não uma no lugar da outra (o SPEC aceita qualquer das duas; entregue
ambas porque o portal é multiusuário e o painel é de dono único).

**2. `server/app/db.py`.** Acrescente em `init_db` a tabela
`semente_id_flow (state TEXT PRIMARY KEY, code_verifier TEXT NOT NULL, nonce
TEXT NOT NULL, destino TEXT, criado_em TEXT NOT NULL)` com o mesmo
`CREATE TABLE IF NOT EXISTS` das demais, e os helpers
`semente_id_flow_insert/get/delete/purge(conn, ...)`. NÃO use a tabela `kv`
para isso: `kv` é território de estado de usuário (é o que `store` exporta e
semeia em conta nova) e uma linha de fluxo de login vazando para um export de
conta seria um defeito real. Purga de fluxos com mais de 10 minutos roda no
`iniciar_login`, como no MyData.

**3. `server/app/main.py`.** Duas rotas, ao lado das demais `/api/auth/*` (o
prefixo `/api/auth/` já está em `_GATE_ALLOWLIST_PREFIXES`, então elas
funcionam antes de haver sessão — que é o ponto):

- `GET /api/auth/semente-id/inicio` → sem `configurado()`, `HTTPException(503,
  ...)` com mensagem acionável nomeando as variáveis que faltam; com
  configuração, `RedirectResponse(semente_id.iniciar_login(_conn, "/admin/"),
  status_code=302)`.
- `GET /api/auth/semente-id/callback` recebendo `code`, `state` e `error` →
  `throttle_check` com `auth.throttle_key(_client_ip(request), "semente-id")`
  antes de qualquer trabalho; `await semente_id.concluir_login(...)`;
  `auth.upsert_oauth_user(_conn, "semente-id", sub, email, email_verified=True)`
  — é o caminho de unificação por e-mail verificado que já existe e que anexa
  a identidade nova à conta que o Alex já tem, preservando o `role_admin`
  dela; `rbac.ensure_bootstrap_role`; se `rbac.permissions_for_user` vier
  vazio, redirecione para `/admin/` SEM handoff (a tela de login já sabe
  exibir o aviso); caso contrário minte o código com
  `auth.create_session(_conn, user["id"], ttl_days=90/86400)` — exatamente o
  mesmo mint do ADR-014, linha 933 — e redirecione 302 para
  `/admin/#handoff=<codigo>`. Falha do portal vira redirect para `/admin/`
  com o aviso, nunca stack trace na cara do navegador. Registre no `obslog`
  categoria "auth" só o desfecho (ok/motivo), nunca token, code ou segredo.

O código no fragmento da URL (`#`) e não na query é deliberado: fragmento não
vai para o log do servidor nem para o `Referer` — mesmo raciocínio do ADR-014.

**4. `web-admin/src/App.jsx`, `function Login` (~linha 962).** Acrescente
ABAIXO do formulário de e-mail+senha (que não muda em nada — restrição do
SPEC) um botão secundário "Entrar com semente.dev" que faz navegação de página
inteira para `/api/auth/semente-id/inicio` (`window.location.href`, não
`fetch` — é um fluxo de redirecionamento OIDC). Estilo: variante discreta dos
tokens `T` já usados no arquivo, nunca acima nem no lugar do botão "Entrar".
Nenhuma outra alteração no arquivo; o `useEffect` do handoff já existe e já
faz a troca.

**PARE E ESCALE, não contorne:** se em qualquer momento a implementação exigir
tocar o login dos clientes finais (`/api/auth/oauth` do app, `deviceStore`,
telas do consumidor em `web/src/`) ou o bundle id
`com.alexandrecamerini.bolsia` / `APNS_TOPIC` / o `aud` do Sign in with Apple,
interrompa a task e traga a decisão para o Alex.

**NÃO RODE** `railway ssh --service semente-id "python -m app.cli client
boris-web-admin --redirect ..."` — é produção de outro repositório e o
client_secret devolvido aparece uma única vez. Sem confirmação explícita do
Alex, a integração fica pronta lendo credenciais de env com os placeholders
documentados, e a task termina pedindo a ele que rode o comando e defina as
variáveis no Railway (registrado em `user_setup` no frontmatter deste plano).
  </action>
  <verify>
    <automated>PYBIN="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)/server/.venv/bin/python"; (cd server && "$PYBIN" -m pytest tests/test_semente_id.py tests/test_semente_id_http.py tests/test_auth.py -q)</automated>
    <automated>(cd web-admin && npx vite build)</automated>
    <automated>! git grep -nE "SEMENTE_ID_CLIENT_SECRET\s*=\s*[\"'][^\"']" -- server web-admin scripts</automated>
  </verify>
  <done>As duas suítes novas passam com id_token assinado por chave RSA gerada em memória e zero rede real; `test_auth.py` continua verde (login e-mail+senha e OAuth dos clientes intactos); o build do web-admin compila; nenhum literal de client_secret no código.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: GET /observabilidade no contrato do ADR-23</name>
  <files>server/app/main.py, server/tests/test_observabilidade.py</files>
  <behavior>
    - A resposta tem exatamente as quatro chaves de topo `situacao`, `alertas`, `ultimas_execucoes`, `proximas`.
    - `situacao` está em {"ok","atencao","critico"} e é coerente: com o kill-switch do agente ligado é "critico"; com o kill-switch desligado e nenhum alerta é "ok".
    - Cada item de `alertas` tem as quatro chaves `severidade`, `titulo`, `detalhe`, `acao`.
    - `ultimas_execucoes` e `proximas` são listas (podem vir vazias, nunca ausentes nem `null`).
    - Sem chave de máquina e sem sessão: 401. Com sessão de conta sem `observabilidade.ver`: 403. Com a chave de máquina correta: 200. Com `B3_OBSERVABILIDADE_CHAVE` não definida, o caminho de máquina fica DESLIGADO (chave errada ou vazia continua 401) — nunca cai para público.
    - A rota é declarada antes do `app.mount("/")` catch-all (mesma classe de defeito que `test_admin_portal.py` já guarda para `/admin`).
    - Nenhum e-mail, `user_id` ou identidade de usuário aparece no payload — só contagens.
  </behavior>
  <action>
Implementa D-OBS (objetivo 2 do SPEC). Testes primeiro.

Acrescente `GET /observabilidade` em `server/app/main.py`. Caminho na RAIZ, não
sob `/api/`: o contrato do ADR-23 é literalmente `GET <sistema>/observabilidade`
e o console vai chamar `https://boris.semente.dev/observabilidade`. Declare a
rota junto das demais rotas `@app.get` — todas ficam ACIMA dos `app.mount()` no
fim do arquivo, e o catch-all `app.mount("/")` engoliria o caminho se a ordem
invertesse. Escreva um teste que trave essa ordem lendo o texto de `main.py`,
no mesmo molde de `test_admin_mount_vem_antes_do_mount_raiz`.

Formato da resposta: as quatro chaves no TOPO, sem envelope. O MyData embrulha
em `{"dados": ...}` porque a API admin inteira dele embrulha; o contrato do
ADR-23 e a restrição do SPEC mostram as quatro chaves nuas — siga o contrato.

Autenticação (o ADR diz "autenticado por chave de máquina") — dois caminhos,
nunca público:
- header `X-Observabilidade-Chave` comparado com `hmac.compare_digest` contra
  `B3_OBSERVABILIDADE_CHAVE`. Variável ausente ou vazia = caminho de máquina
  desligado (fail-closed), nunca "qualquer um passa".
- ou sessão válida com a permissão `observabilidade.ver`, para o painel deste
  repo poder consumir a mesma rota.
Falta dos dois: 401. Sessão válida sem a permissão: 403. Não use
`Depends(require_permission(...))` direto (ele exige sessão e não conhece a
chave de máquina) — resolva os dois caminhos no corpo da rota e reuse
`auth.resolve_session` + `rbac.ensure_bootstrap_role` + `rbac.permissions_for_user`.

Conteúdo, derivado SÓ de dado que já existe (nenhuma coleta nova, nenhuma
chamada a fonte externa dentro da rota — é uma rota de status e não pode gastar
orçamento da brapi nem cota de LLM):
- `alertas`: monte a lista a partir de `agent_mod.status_snapshot(_conn)`
  (kill-switch ligado → severidade "critico", ação "desligar em Execução
  automática"; `heartbeat.lacoVivo` falso → "critico"; ordens pendentes com
  kill-switch ligado → "critico", que é exatamente o mascaramento do incidente
  de v1.0), `timing_watch.kill_switch_on()` (→ "atencao"),
  `brapi_budget.snapshot()` (orçamento do dia esgotado/degradado → "atencao")
  e `obslog.stats()` (contador de `:error` > 0 desde o boot → "atencao", com
  `acao` apontando Perfil → Observabilidade). Cada alerta com as quatro chaves
  do contrato.
- `situacao`: "critico" se houver qualquer alerta crítico; "atencao" se houver
  alerta não-crítico; "ok" se a lista estiver vazia. Derive do próprio array,
  não de uma segunda regra paralela — semáforo que discorda da lista é o
  defeito clássico deste tipo de endpoint.
- `ultimas_execucoes`: `status_snapshot(...)["passadas"]` (já vem da mais
  recente para a mais antiga) limitado a 10, cada item com o que rodou, o
  status e quando.
- `proximas`: a próxima passada do agente (`proximaPassadaEmS` +
  `intervaloS`) e a janela do radar diário (`radarDiario`). Lista vazia é
  resposta legítima quando o agendador não está rodando — nunca invente
  horário (princípio 4 do CLAUDE.md: não fabricar valor quando o dado falta).

Sem PII: contagens, nunca identidade — a mesma regra que
`status_snapshot` já segue para `ordensPendentes` e `protecaoSemOperador`.
  </action>
  <verify>
    <automated>PYBIN="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)/server/.venv/bin/python"; (cd server && "$PYBIN" -m pytest tests/test_observabilidade.py tests/test_admin_portal.py -q)</automated>
    <automated>grep -vn '^\s*#' server/app/main.py | grep -c 'app.get("/observabilidade")'</automated>
  </verify>
  <done>As quatro chaves do contrato respondem com dado real do sistema; o semáforo é coerente com a lista de alertas; sem chave de máquina nem permissão a rota fecha; a rota está registrada antes do mount catch-all e o teste de ordem prova isso.</done>
</task>

<task type="auto">
  <name>Task 3: Cauda do rename — generalizar atualizar-identidade.sh até o verificador rodar limpo</name>
  <files>scripts/atualizar-identidade.sh, scripts/gerar-adhoc.sh, server/app/mydata_budget.py, README.md, OPTIONS-MODELS.md, OPTIONS-SMOKE-TEST.md, TECHNICAL-ANALYSIS-MODELS.md, scripts/setup.sh, scripts/setup-ios.sh, scripts/run.sh, scripts/backup-db.sh</files>
  <action>
Implementa D-RENAME (objetivo 3 do SPEC). O alvo já está MEDIDO — rode
`bash scripts/atualizar-identidade.sh --verificar` antes de tocar em qualquer
coisa para confirmar a medição abaixo (hoje ele termina em
"identidade INCOMPLETA", com 7 arquivos listados):

Classificação dos 7, decidida e não a re-decidir:

1. `.planning/milestones/.../09-01-PLAN.md`, `.planning/notes/boris-pp-...md`,
   `.planning/todos/pending/medir-rate-limit-mydata.md` — **registro
   histórico**, mesma classe que `qa/` e `ESTADO-*`. Some `':!.planning'` à
   lista de exclusão do `git grep` em `verificar()`, com comentário dizendo por
   quê (reescrever o nome da época falsificaria a decisão da época). Isto
   também cobre o SPEC e este PLAN, que citam "BolsIA" verbatim ao transcrever
   o contexto e passariam a quebrar o verificador assim que fossem commitados.
2. `docs/MEDICAO-Mydata-2026-08-27.md` — relatório de medição DATADO, snapshot
   de uma data específica, e a única ocorrência (linha 228) está dentro de uma
   citação. Mesma classe: exclua com `':!docs/MEDICAO-*'`, não reescreva.
3. `server/POLITICA-PRIVACIDADE.md` — **defeito no verificador, não sobra de
   rename.** O comentário do próprio script diz que o "(anteriormente BolsIA)"
   é mantido de propósito, e a exclusão `':!POLITICA-PRIVACIDADE.md'` existe —
   mas um pathspec sem magic é relativo à raiz e não casa
   `server/POLITICA-PRIVACIDADE.md`. Corrija para `':!*POLITICA-PRIVACIDADE.md'`.
   O texto do arquivo não muda.
4. `server/app/mydata_budget.py` linha 3 — código VIVO: "A chave de produção do
   BolsIA" → "do Boris+". Faça pelo `aplicar()` (um `perl -0777 -pi` idempotente,
   como as demais linhas de lá), nunca à mão: o script é a fonte única desta
   migração, e uma edição manual cria a segunda fonte de verdade que ele existe
   para evitar.
5. `scripts/gerar-adhoc.sh` linha 27, `SCHEME="BolsIA"` — **não é texto, é
   identificador de scheme do Xcode**, mesma classe do bundle id. Trocar a
   string por "Boris+" no escuro quebraria a build ad-hoc se o scheme real
   ainda se chamar outra coisa, e `web/ios/` nem existe nesta worktree (é
   gerado por `cap sync`). Substitua o literal por detecção com escape
   explícito: `SCHEME="${IOS_SCHEME:-}"`; se vazio, derive do primeiro
   `$PROJ/xcshareddata/xcschemes/*.xcscheme` existente; se ainda vazio, `die`
   com mensagem acionável mandando rodar `npx cap sync ios` ou passar
   `IOS_SCHEME=<nome>`. A detecção vai DEPOIS do `[ -f "$PBXPROJ" ] || die` que
   já existe. Nenhum nome fica chutado e nenhuma falha fica silenciosa.

Superfícies vivas que ainda carregam o nome ANTERIOR ao BolsIA ("B3 Agente") e
que o objetivo 3 do SPEC nomeia explicitamente (README, documentação
operacional viva) — 8 ocorrências, todas em título/cabeçalho, todas via
`aplicar()`: `README.md:1`, `OPTIONS-MODELS.md:1`, `OPTIONS-SMOKE-TEST.md:1`,
`TECHNICAL-ANALYSIS-MODELS.md:1`, e o comentário de cabeçalho de
`scripts/setup.sh:2`, `scripts/setup-ios.sh:3`, `scripts/run.sh:2`,
`scripts/backup-db.sh:2`. NÃO toque nas ocorrências de "B3 Agente" dentro do
próprio `atualizar-identidade.sh` (linhas 18, 61, 64, 73, 76): são os literais
de busca das substituições — apagá-los quebra a idempotência do script.

Acrescente ao verificador um segundo grep guardião, na mesma forma do de
"BolsIA": "B3 Agente" não pode sobrar em arquivo vivo, com as mesmas exclusões
de histórico mais o próprio script. Atualize o cabeçalho de documentação do
`atualizar-identidade.sh` (o bloco "O que este script cobre" e "O que NÃO
muda") para listar os arquivos novos e a regra do `.planning`/`docs/MEDICAO-*`
— o cabeçalho é a explicação da migração e ficar desatualizado é o mesmo
problema de duas fontes de verdade.

O bundle id `com.alexandrecamerini.bolsia`, o codinome `b3-agente`, as env
`B3_*` e as chaves `b3-*` não mudam — releia as linhas 7-11 e 25-29 do próprio
script antes de tocar em qualquer coisa.

Publicação: este plano toca `web-admin/src/` (Task 1). Rode
`bash scripts/publicar-admin.sh` ao final para o botão de login pelo portal
sair do build local e virar bundle servido — sem isso a mudança fica testada e
nunca vai ao ar. `web/src/` NÃO é tocado por este plano, então não há bump de
versão do app consumidor nem `publicar-web.sh` aqui.
  </action>
  <verify>
    <automated>bash scripts/atualizar-identidade.sh --verificar</automated>
    <automated>grep -c 'appId: "com.alexandrecamerini.bolsia"' web/capacitor.config.ts</automated>
    <automated>bash scripts/executar.sh --testes</automated>
  </verify>
  <done>`--verificar` termina em "IDENTIDADE OK"; rodar o script duas vezes seguidas não produz diff (idempotência preservada); `appId` segue `com.alexandrecamerini.bolsia`; a suíte canônica inteira (pytest + web/tests/*.mjs) passa; o bundle do admin foi republicado.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 4: Checkpoint — registrar o client no portal e verificar os dois caminhos de login ao vivo</name>
  <action>Pausa bloqueante. Nenhuma edição de código nesta task: o agente para aqui porque o passo seguinte roda contra produção de OUTRO repositório (portal semente-id) e o client_secret devolvido aparece uma única vez. Apresente ao Alex o comando de registro do client, as variáveis de ambiente pendentes e o roteiro de verificação abaixo; aguarde a resposta antes de qualquer push da fase.</action>
  <what-built>
    Boris+ como relying party do semente.id (rotas /api/auth/semente-id/*, botão
    no painel admin reusando o handoff do ADR-014), GET /observabilidade no
    contrato do ADR-23, e a cauda do rename fechada pelo verificador de identidade.
  </what-built>
  <how-to-verify>
    1. Decisão pendente de você, Alex — registrar o client no portal:
       `railway ssh --service semente-id "python -m app.cli client boris-web-admin --redirect https://boris.semente.dev/api/auth/semente-id/callback"`
       (projeto `mydata`). O agente NÃO rodou esse comando de propósito: é
       produção de outro repositório e o client_secret aparece uma única vez.
       Rode você, ou autorize explicitamente.
    2. Com o `client_id`/`client_secret` em mãos, defina no Railway do serviço
       deste repo: SEMENTE_ID_CLIENT_ID, SEMENTE_ID_CLIENT_SECRET,
       SEMENTE_ID_EMAIL_DONO (e SEMENTE_ID_URL só se o portal não estiver em
       https://id.semente.dev).
    3. Abra https://boris.semente.dev/admin/ → confirme que "Entrar" com
       e-mail+senha continua funcionando exatamente como antes (é a garantia de
       que o portal soma um caminho, não substitui).
    4. Clique "Entrar com semente.dev" → o portal deve autenticar e devolver
       você ao painel já logado, com as mesmas abas de sempre.
    5. `curl -H "X-Observabilidade-Chave: <valor de B3_OBSERVABILIDADE_CHAVE>" https://boris.semente.dev/observabilidade`
       deve devolver as quatro chaves; sem o header, 401.
    6. Confirme no app do iPhone que o login dos clientes finais (Apple/Google/
       e-mail) não mudou nada.
  </how-to-verify>
  <resume-signal>Responda "aprovado" ou descreva o que quebrou</resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| navegador → `/api/auth/semente-id/*` | `code`, `state` e `error` chegam da URL, sob controle de quem clica |
| portal `id.semente.dev` → backend | `id_token` e resposta de `/token` vêm de terceiro pela rede |
| console `admin.semente.dev` → `GET /observabilidade` | chamador externo, autenticado só por chave de máquina |
| env do Railway → processo | `SEMENTE_ID_CLIENT_SECRET` e `B3_OBSERVABILIDADE_CHAVE` são segredo e não podem vazar em log/erro/commit |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-eqm-01 | Spoofing | `/api/auth/semente-id/callback` | mitigate | `id_token` validado por assinatura JWKS + `iss` + `aud` + `exp` + `nonce`; `email_verified` obrigatório |
| T-eqm-02 | Tampering | fluxo OIDC (code injection / CSRF de login) | mitigate | PKCE S256 com `code_verifier` só no servidor; `state` de uso único, consumido mesmo quando o portal recusa; fluxo expira em 10 min |
| T-eqm-03 | Elevation of Privilege | conta qualquer do portal (multiusuário) abrindo o painel | mitigate | duas travas: `SEMENTE_ID_EMAIL_DONO` no módulo e RBAC do ADR-013 no exchange do handoff (conta sem `permissions` não abre sessão) |
| T-eqm-04 | Information Disclosure | código de handoff na URL | mitigate | código de ~90s, uso único, revogado no exchange, e entregue no FRAGMENTO (`#`) — não vai a log de servidor nem a `Referer` |
| T-eqm-05 | Information Disclosure | `client_secret` em log/erro/commit | mitigate | segredo só via env; mensagens de erro nomeiam o que falhou sem eco do valor; gate `git grep` no verify da Task 1 |
| T-eqm-06 | Information Disclosure | `GET /observabilidade` exposto | mitigate | fail-closed: sem `B3_OBSERVABILIDADE_CHAVE` definida o caminho de máquina fica desligado; alternativa é sessão com `observabilidade.ver`; payload só com contagens, sem PII |
| T-eqm-07 | Denial of Service | força bruta no callback / martelar `/observabilidade` | mitigate | `auth.throttle_*` no callback por (ip, "semente-id"); `/observabilidade` não faz chamada externa nenhuma, não gasta orçamento brapi nem cota de LLM |
| T-eqm-08 | Repudiation | login administrativo sem rastro | accept | `obslog` categoria "auth" registra o desfecho do callback; auditoria completa de sessão administrativa é escopo do ADR-013, não desta fase |
| T-eqm-SC | Tampering | npm/pip/cargo installs | n/a | este plano NÃO instala pacote nenhum: `httpx` e `PyJWT[crypto]` já estão em `server/requirements.txt` e `requirements-prod.txt`. Se a implementação passar a exigir dependência nova, PARE — o gate de legitimidade de pacote não foi rodado para esta fase |
</threat_model>

<verification>
- `bash scripts/executar.sh --testes` verde (pytest do backend + `web/tests/*.mjs`) — `scripts/test.sh` sozinho não conta como validação.
- `(cd web-admin && npx vite build)` compila — grep e teste estático não pegam erro de sintaxe JS.
- `bash scripts/atualizar-identidade.sh --verificar` termina em "IDENTIDADE OK", e rodar `bash scripts/atualizar-identidade.sh` duas vezes não gera diff.
- `git grep -n "SEMENTE_ID_CLIENT_SECRET" -- server web-admin scripts` mostra só leitura de env, nunca um valor.
- Nenhum arquivo sob `web/src/` no diff (o login dos clientes finais não é tocado).
- `web/capacitor.config.ts` segue com `appId: "com.alexandrecamerini.bolsia"`.
</verification>

<success_criteria>
1. `/api/auth/semente-id/inicio` e `/callback` existem, validam o id_token por
   issuer/audience/nonce/assinatura contra o JWKS do portal, e desembocam no
   handoff do ADR-014 que já abre o painel.
2. Login por e-mail+senha do painel e login dos clientes finais idênticos ao de
   hoje, provado por `test_auth.py` verde e por nenhum diff em `web/src/`.
3. `GET /observabilidade` responde `situacao`/`alertas`/`ultimas_execucoes`/
   `proximas`, fechado por chave de máquina ou por `observabilidade.ver`.
4. `bash scripts/atualizar-identidade.sh --verificar` roda limpo com o bundle id
   preservado.
5. Suíte canônica inteira verde; nenhum client_secret em commit ou log.
6. Pendências para o Alex declaradas no SUMMARY: registro do client no portal e
   as variáveis de ambiente do Railway.
</success_criteria>

<output>
Crie `.planning/quick/260830-eqm-fase-4-adr-23-boris-relying-party-do-sem/260830-eqm-SUMMARY.md` ao terminar.
</output>
