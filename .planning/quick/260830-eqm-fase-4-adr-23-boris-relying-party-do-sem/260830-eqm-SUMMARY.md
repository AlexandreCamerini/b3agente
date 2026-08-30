---
phase: quick-260830-eqm
plan: 01
subsystem: auth
tags: [oidc, pkce, jwt, fastapi, sqlite, observability, rename]

requires: []
provides:
  - "server/app/semente_id.py — cliente OIDC relying party (PKCE S256, validação id_token via JWKS/issuer/audience/nonce/exp, trava SEMENTE_ID_EMAIL_DONO)"
  - "GET /api/auth/semente-id/inicio e /callback — segundo caminho de login do painel admin, deságua no handoff do ADR-014"
  - "GET /observabilidade — contrato mínimo do ADR-23 (situacao/alertas/ultimas_execucoes/proximas), autenticado por chave de máquina ou observabilidade.ver"
  - "scripts/atualizar-identidade.sh generalizado — guardião duplo (BolsIA + B3 Agente), cauda do rename fechada"
affects: [portal-admin, observabilidade, identidade-do-produto]

tech-stack:
  added: []
  patterns:
    - "Relying party OIDC com httpx.AsyncClient como única fronteira de rede + PyJWT[crypto] para validação de id_token (sem PyJWKClient — JWKS buscado manualmente para manter httpx como ponto único mockável)"
    - "Tabela SQLite dedicada de vida curta (semente_id_flow) para estado de fluxo OIDC, nunca kv (kv é território de estado de usuário)"
    - "Autenticação dupla numa mesma rota (chave de máquina compare_digest OU sessão+permissão), resolvida no corpo da rota quando Depends(require_permission) não serve (não conhece a chave de máquina)"

key-files:
  created:
    - server/app/semente_id.py
    - server/tests/test_semente_id.py
    - server/tests/test_semente_id_http.py
    - server/tests/test_observabilidade.py
  modified:
    - server/app/db.py
    - server/app/main.py
    - web-admin/src/App.jsx
    - scripts/atualizar-identidade.sh
    - scripts/gerar-adhoc.sh
    - server/app/mydata_budget.py
    - README.md
    - OPTIONS-MODELS.md
    - OPTIONS-SMOKE-TEST.md
    - TECHNICAL-ANALYSIS-MODELS.md
    - scripts/setup.sh
    - scripts/setup-ios.sh
    - scripts/run.sh
    - scripts/backup-db.sh
    - server/tests/test_adr013_cobertura_rotas.py
    - server/admin_dist/**

key-decisions:
  - "concluir_login devolve (sub, email, destino), 3-tupla, não (email, destino) como a referência do MyData — Boris+ tem identities multi-provedor (auth.upsert_oauth_user) que EXIGE (provider, sub); MyData usa sessão-cookie única e não precisa de sub. Confirmado lendo a implementação de referência antes de decidir, não por suposição."
  - "acao em cada alerta de /observabilidade é string simples, não {rotulo, rota} como no MyData — a própria PLAN.md escreve os exemplos de acao como texto puro; nada no SPEC/PLAN deste repo exige o formato dict do MyData."
  - "Falha de login pelo portal redireciona para /admin/ sem hash — a PLAN.md descreve isso como 'a tela já sabe exibir o aviso', mas o useEffect existente só lê aviso do handoff (#handoff=), não de um redirect liso. Segui a restrição EXPLÍCITA do PLAN ('nenhuma outra alteração no arquivo') em vez de adicionar wiring de aviso novo — ver Known Gaps abaixo."
  - "SCHEME de gerar-adhoc.sh vira detecção (IOS_SCHEME env > 1º *.xcscheme > die) em vez do literal 'BolsIA' hardcoded — é identificador de scheme do Xcode, não texto de marca; trocar no escuro quebraria a build ad-hoc."

requirements-completed: [ADR23-F4-IDENT, ADR23-F4-OBS, ADR23-F4-RENAME]

duration: ~70min (sessão completa, incluindo leitura da implementação de referência em ~/dev/cvm-financas)
completed: 2026-08-30
status: complete
---

# Quick Task 260830-eqm: Fase 4 do ADR-23 — Boris+ relying party do semente.id, Summary

**Boris+ ganha um segundo caminho de login administrativo via OIDC/PKCE contra o portal semente.id (deságua no handoff do ADR-014 já existente), publica `GET /observabilidade` no contrato mínimo do ADR-23, e fecha a cauda medida do rename BolsIA/B3 Agente → Boris+ em 9 arquivos vivos.**

## Performance

- **Duration:** ~70min (orientação incluindo leitura de `~/dev/cvm-financas` + implementação + TDD + full suite)
- **Completed:** 2026-08-30
- **Tasks:** 3 de 4 (Task 4 é checkpoint bloqueante — ver "Pendência para o Alex" abaixo)
- **Files modified:** 22 (6 no Task 1, 2 no Task 2, 16 no Task 3, incluindo `server/admin_dist/**` republicado)

## Accomplishments

- `server/app/semente_id.py`: cliente OIDC completo — PKCE S256, troca de code, validação de id_token por assinatura (JWKS), issuer, audience, exp e nonce; segunda trava `SEMENTE_ID_EMAIL_DONO` case-insensitive; nunca eco de client_secret/code/id_token em erro.
- `GET /api/auth/semente-id/inicio` e `/callback` em `server/app/main.py`, reusando 100% do handoff do ADR-014 (`POST /api/admin/mobile-handoff/exchange`) — nenhum caminho de troca novo no front.
- Botão "Entrar com semente.dev" em `web-admin/src/App.jsx` (`Login`), abaixo do formulário e-mail+senha que não mudou.
- `GET /observabilidade` na raiz (fora de `/api/`), declarada antes do mount catch-all, com as quatro chaves nuas do contrato ADR-23, semáforo derivado da própria lista de alertas, fail-closed sem chave de máquina configurada.
- `scripts/atualizar-identidade.sh` generalizado: segundo guardião ("B3 Agente" fora do histórico), pathspec do POLITICA-PRIVACIDADE.md corrigido, 9 arquivos vivos migrados (1 código + 8 títulos de documentação/scripts), idempotência preservada.

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Boris+ vira relying party do portal semente.id** — `b7cef72` (feat, TDD: 40 testes novos)
2. **Task 2: GET /observabilidade no contrato do ADR-23** — `3ba8830` (feat, TDD: 16 testes novos)
3. **Task 3: Cauda do rename — generalizar atualizar-identidade.sh** — `d0b9a6c` (fix, inclui 2 correções de guardiões pré-existentes descobertas pela suíte canônica completa)

_Nota: Task 1 e 2 seguiram RED→GREEN explícito (teste escrito e visto falhar por `ImportError`/404 antes da implementação), conforme `tdd="true"` no PLAN._

## Files Created/Modified

- `server/app/semente_id.py` — módulo do relying party (194 linhas)
- `server/app/db.py` — tabela `semente_id_flow` + 4 helpers (insert/get/delete/purge)
- `server/app/main.py` — 2 rotas de auth + rota `/observabilidade` (import `hmac`, `RedirectResponse`, `semente_id`)
- `web-admin/src/App.jsx` — botão secundário em `Login`
- `server/tests/test_semente_id.py` — 14 testes (módulo, offline, chave RSA em memória)
- `server/tests/test_semente_id_http.py` — 7 testes (rota real via `TestClient`, regressão de login/oauth)
- `server/tests/test_observabilidade.py` — 10 testes (contrato, semáforo, 4 desfechos de auth, ordem de mount, PII)
- `scripts/atualizar-identidade.sh` — `aplicar()` +9 substituições, `verificar()` +1 guardião +2 exclusões +1 fix de pathspec
- `scripts/gerar-adhoc.sh` — `SCHEME` hardcoded → detecção acionável
- `server/app/mydata_budget.py`, `README.md`, `OPTIONS-MODELS.md`, `OPTIONS-SMOKE-TEST.md`, `TECHNICAL-ANALYSIS-MODELS.md`, `scripts/setup.sh`, `scripts/setup-ios.sh`, `scripts/run.sh`, `scripts/backup-db.sh` — 1 título/comentário cada, aplicado via `aplicar()`, nunca editado à mão
- `server/tests/test_adr013_cobertura_rotas.py` — allowlist pública +2 rotas, contador pinado 17→19 (guardião de crescimento deliberado)
- `server/admin_dist/**` — republicado via `scripts/publicar-admin.sh` (botão de login vai ao ar)

## Decisions Made

Ver `key-decisions` no frontmatter — as 4 decisões relevantes (contrato de retorno de `concluir_login`, formato de `acao`, comportamento do redirect sem handoff, detecção de SCHEME) foram todas confirmadas lendo a implementação de referência (`~/dev/cvm-financas/app/api/semente_id.py`, `admin.py:737-753`, ambas as suítes de teste de lá) antes de decidir, não por suposição.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Contrato `concluir_login` adaptado para 3-tupla (sub, email, destino)**
- **Found during:** Task 1, antes de escrever `main.py` — a `<action>` do PLAN pedia `tuple[str, str]` mas o próprio texto da rota chama `auth.upsert_oauth_user(_conn, "semente-id", sub, email, ...)`, exigindo um `sub` que a assinatura não devolvia.
- **Fix:** `concluir_login` devolve `(sub, email, destino)`. Confirmado contra a referência do MyData (que devolve só `(email, destino)` porque não tem `identities` multi-provedor) antes de implementar — não é cópia cega, é adaptação deliberada e necessária pro contrato de `auth.upsert_oauth_user` deste repo.
- **Files modified:** `server/app/semente_id.py`, `server/app/main.py`, `server/tests/test_semente_id.py`
- **Verification:** 14 testes do módulo passam, incluindo o caminho feliz asserindo `sub == "conta-1"`.
- **Committed in:** `b7cef72`

**2. [Rule 1 - Bug] Citação de linha errada em SPEC.md (713-728 → 737-753) não propagada**
- **Found during:** Task 2, leitura da implementação de referência — SPEC.md cita `admin.py:713-728` para `/observabilidade`, mas essa faixa é a rota `/alertas`; PLAN.md cita `737-753`, que é a correta. Usei a correta (confirmada por `grep -n "def get_observabilidade"`), não precisei corrigir nenhum arquivo (SPEC.md é histórico da fonte externa, fora de escopo editar).
- **Files modified:** nenhum (achado de leitura, sem ação de escrita necessária)
- **Committed in:** n/a

**3. [Rule 3 - Blocking] `web-admin/node_modules` ausente no worktree**
- **Found during:** Task 1, ao rodar `npx vite build` — worktree novo não herda `node_modules` (não é tracked).
- **Fix:** `npm install --no-audit --no-fund` em `web-admin/` — reproduz `package-lock.json` existente, nenhum pacote novo instalado (não é o caso do gate de legitimidade de pacote, que é para pacotes NOVOS).
- **Files modified:** nenhum arquivo versionado (`node_modules/` é gitignored)
- **Committed in:** n/a (não versionado)

**4. [Rule 1 - Bug] Guardião de ordem de mount pego pela própria explicação (falso red)**
- **Found during:** Task 2, primeira rodada do teste de ordem — o comentário que eu escrevi acima da rota citava literalmente `app.mount("/")` como exemplo, e o `.find()` do teste pegava essa string no COMENTÁRIO em vez do mount real (~2000 linhas depois).
- **Fix:** reescrevi o comentário para não conter o literal exato `app.mount("/"`.
- **Files modified:** `server/app/main.py`
- **Verification:** `test_observabilidade_registrada_antes_do_mount_raiz` passa.
- **Committed in:** `3ba8830`

**5. [Rule 1 - Bug] Dois guardiões pré-existentes quebrados só pela suíte COMPLETA (não pelo subset do `<verify>` da task)**
- **Found during:** Task 3, ao rodar `bash scripts/executar.sh --testes` pela primeira vez (a suíte canônica completa é o critério de aceite explícito, não os `<verify>` por task).
  - `test_adr013_cobertura_rotas.py::test_toda_rota_de_api_tem_gate_reconhecido_ou_esta_na_allowlist`: as 2 rotas novas do Task 1 (`/inicio`, `/callback`) são pré-sessão por natureza (mesma classe de `/api/auth/login`) mas não tinham dependency reconhecida nem estavam na allowlist — o guardião existe exatamente pra pegar isso.
  - `test_adr013_cobertura_rotas.py::test_allowlist_publica_nao_cresce_sem_atualizar_este_teste`: contador pinado (`== 17`) — cresceu pra 19 de propósito, é o "sinal humano" que o próprio docstring do teste descreve.
  - `test_observabilidade.py::test_situacao_ok_sem_alerta_nenhum` (meu PRÓPRIO teste, Task 2): passava isolado mas falhava na suíte completa — `obslog.stats()` acumula desde o boot do PROCESSO pytest inteiro; outro módulo rodando antes gerava um `:error` que inflava o alerta "atencao" e quebrava o cenário "zero alertas". Bug de isolamento no meu teste, não no código de produção.
- **Fix:** allowlist +2 rotas com comentário explicando por quê são pré-sessão; contador pinado atualizado com comentário do porquê; `obslog.reset()` adicionado à fixture `_isolado` de `test_observabilidade.py` (mesmo padrão de `brapi_budget.reset()`/`agent.reset_kill_switch_cache()` que já existia ali).
- **Files modified:** `server/tests/test_adr013_cobertura_rotas.py`, `server/tests/test_observabilidade.py`
- **Verification:** `bash scripts/executar.sh --testes` → 1737 passed, 1 skipped, exit 0.
- **Committed in:** `d0b9a6c`

**6. [Correção operacional] `git stash` acidental durante teste de idempotência**
- **Found during:** Task 3, ao tentar validar idempotência do script — usei `git stash -u` pra "comparar antes/depois" e isso reverteu TODO o trabalho não commitado do Task 3 (script + renomes aplicados). Corrigido imediatamente com `git stash pop` (nada foi perdido — stash preserva o estado). Idempotência foi então validada do jeito certo: checksums MD5 antes/depois de rodar `aplicar()` de novo, sem stash.
- **Files modified:** nenhum (recuperação completa)
- **Committed in:** n/a

---

**Total deviations:** 6 (4 auto-fixed Rule 1, 1 auto-fixed Rule 3, 1 correção operacional sem perda)
**Impact on plan:** Todas as correções foram necessárias para completar as tasks corretamente ou corrigir guardiões pré-existentes que a suíte canônica completa (critério de aceite explícito do PLAN) exigia ficarem verdes. Nenhum scope creep — nenhuma funcionalidade fora do que as 3 tasks pediam.

## Known Gaps

**Redirect sem handoff (conta sem papel administrativo) não mostra aviso visível.** O PLAN.md descreve "redirecione para /admin/ SEM handoff (a tela de login já sabe exibir o aviso)", mas o `useEffect` existente em `web-admin/src/App.jsx` só lê `avisoInicial` a partir do hash `#handoff=` (ver linha ~1253) — um redirect liso para `/admin/` sem hash não populate nenhum aviso hoje. O PLAN também restringe explicitamente "Nenhuma outra alteração no arquivo" para o Task 1 além do botão de login. Priorizei a restrição explícita sobre a afirmação descritiva (que parece imprecisa para este caso específico): o usuário sem permissão é corretamente barrado (nenhuma sessão nasce), só sem mensagem explicando o motivo — mesmo comportamento de segurança, UX levemente inferior a outros fluxos de erro do painel. Não é bloqueante; documentado aqui para o Alex decidir se quer uma fase de acompanhamento.

## Issues Encountered

Nenhum problema não coberto pelas seções acima. A suíte canônica completa (`bash scripts/executar.sh --testes`) passa integralmente: 1737 passed, 1 skipped (backend) + todos os `web/tests/*.mjs` (frontend), exit 0.

## Task 4 — checkpoint RESOLVIDO (2026-08-30)

Alex rodou o registro do client no portal `semente-id`, definiu `SEMENTE_ID_CLIENT_ID`/`SEMENTE_ID_CLIENT_SECRET`/`SEMENTE_ID_EMAIL_DONO` no Railway, aprovou o merge (PR #27, `f534fda`, merged 2026-08-30T21:50:35Z) e confirmou "tudo funcionando" após a verificação ao vivo. Deploy em produção verificado (`build: F10-20260830-01`); `/api/auth/semente-id/inicio` → 302 para o portal com PKCE correto; `/observabilidade` → 401 sem header (fail-closed); `/admin/` → 200. Único item novo levantado pós-deploy: `B3_OBSERVABILIDADE_CHAVE` não estava nas 3 variáveis originais do checkpoint — instruções de como definir foram passadas ao Alex separadamente (coordenação cross-repo com o console `admin.semente.dev`, fora do escopo deste quick task).

Registro original do checkpoint (histórico, mantido abaixo):

A Task 4 do PLAN foi uma pausa bloqueante por desenho — nenhuma edição de código, porque o próximo passo rodava contra produção de OUTRO repositório (portal `semente-id`) e o `client_secret` devolvido aparece uma única vez. Reproduzido aqui verbatim do PLAN.md:

> **O que foi construído:** Boris+ como relying party do semente.id (rotas `/api/auth/semente-id/*`, botão no painel admin reusando o handoff do ADR-014), `GET /observabilidade` no contrato do ADR-23, e a cauda do rename fechada pelo verificador de identidade.
>
> **Como verificar:**
> 1. Decisão pendente de você, Alex — registrar o client no portal:
>    `railway ssh --service semente-id "python -m app.cli client boris-web-admin --redirect https://boris.semente.dev/api/auth/semente-id/callback"`
>    (projeto `mydata`). O agente NÃO rodou esse comando de propósito: é produção de outro repositório e o `client_secret` aparece uma única vez. Rode você, ou autorize explicitamente.
> 2. Com o `client_id`/`client_secret` em mãos, defina no Railway do serviço deste repo: `SEMENTE_ID_CLIENT_ID`, `SEMENTE_ID_CLIENT_SECRET`, `SEMENTE_ID_EMAIL_DONO` (e `SEMENTE_ID_URL` só se o portal não estiver em `https://id.semente.dev`).
> 3. Abra `https://boris.semente.dev/admin/` → confirme que "Entrar" com e-mail+senha continua funcionando exatamente como antes (é a garantia de que o portal soma um caminho, não substitui).
> 4. Clique "Entrar com semente.dev" → o portal deve autenticar e devolver você ao painel já logado, com as mesmas abas de sempre.
> 5. `curl -H "X-Observabilidade-Chave: <valor de B3_OBSERVABILIDADE_CHAVE>" https://boris.semente.dev/observabilidade` deve devolver as quatro chaves; sem o header, 401.
> 6. Confirme no app do iPhone que o login dos clientes finais (Apple/Google/e-mail) não mudou nada.
>
> **Resume signal:** Responda "aprovado" ou descreva o que quebrou.

**Não fiz nem tentarei fazer:** rodar o comando `railway ssh --service semente-id ...` de registro do client, nem adquirir/fabricar `SEMENTE_ID_CLIENT_ID`/`SEMENTE_ID_CLIENT_SECRET` por qualquer outro meio. Sem essas 3 variáveis definidas em produção, `semente_id.configurado()` é `False` e `/api/auth/semente-id/inicio` responde 503 (mensagem acionável) — o app continua funcionando normalmente com o login e-mail+senha de sempre até você decidir.

## Next Phase Readiness

- Backend e front prontos, testados, com o bundle do admin já republicado localmente neste worktree (`server/admin_dist/**`) — falta o deploy real (push) e as 3 variáveis de ambiente no Railway, que dependem da Task 4.
- Nenhum arquivo sob `web/src/` tocado — login dos clientes finais (Apple/Google/e-mail no app) intacto, confirmado por diff vazio.
- `web/capacitor.config.ts` mantém `appId: "com.alexandrecamerini.bolsia"` — confirmado.
- Bloqueio: push da fase inteira aguarda a aprovação humana da Task 4 (checkpoint bloqueante) — não fazer push antes disso.

---
*Quick task: 260830-eqm*
*Completed: 2026-08-30*

## Self-Check: PASSED

- Todos os 12 arquivos-chave verificados existem no worktree (created + principais modified).
- Os 3 hashes de commit (`b7cef72`, `3ba8830`, `d0b9a6c`) confirmados em `git log --oneline --all`.
- `bash scripts/executar.sh --testes` → 1737 passed, 1 skipped (backend) + todos os `web/tests/*.mjs`, exit 0.
- `bash scripts/atualizar-identidade.sh --verificar` → IDENTIDADE OK; idempotência confirmada por checksum MD5 antes/depois de `aplicar()`.
- `git grep -n "SEMENTE_ID_CLIENT_SECRET"` → só leitura de env / fixtures de teste com placeholder, nenhum literal do segredo real.
- `git diff --stat` sob `web/src/` → vazio (login dos clientes finais intocado).
