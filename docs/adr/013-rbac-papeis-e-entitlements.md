# ADR-013: RBAC, papéis e entitlements — central de administração de verdade

**Status:** Implementado (aprovado pelo Alex em 2026-08-16). As 4 decisões
pendentes da v1 deste documento foram resolvidas e incorporadas (ver
"Decisões do Alex incorporadas" abaixo) e o backend + `web-admin/` foram
implementados na sequência — 915 testes de backend + 70 suítes web
passando, build do `web-admin/` limpo, verificação ao vivo das 5 telas
novas no navegador. Único item que segue como verificação manual pendente:
confirmar num build real de iOS que nenhum caminho do app nativo depende do
`llmPrompts` server-side sem mandar o próprio prompt no corpo (Decisão 5a).
**Data:** 2026-08-16 · **Origem:** pedido do Alex por um modelo de
papel/plano (admin/pagante/visitante) que feche a lacuna de governança que o
ADR-011 já apontou e não decidiu (`plan.py` sem superfície) e estenda
`web-admin/` de SÓ VER para uma central de administração com escrita
auditada.

---

## Contexto

Hoje o Boris+ tem DOIS mecanismos de controle de acesso, nenhum dos dois é
RBAC:

1. **Autenticação sem papel** (`server/app/auth.py`): email/senha, OAuth
   (Google/Apple), SIWA. O `user` resolvido não carrega nenhum conceito de
   papel ou plano — é só identidade.
2. **Gate de admin binário** (`_is_obs_admin`, `server/app/main.py:385-393`):
   `B3_ADMIN_EMAILS` (env, lista de e-mails) OU, na ausência da env, "a
   primeira conta criada no banco". Sem granularidade — quem passa nesse
   `if` vê TUDO que é admin; quem não passa, nada.

O `web-admin/` (ADR-011 v1 + ADR-012 Fases 1-5, em produção) é **só leitura**
por decisão deliberada do ADR-011 ("v1 SÓ VER — sem ação nenhuma"). A única
exceção real hoje é `POST /api/obs/brapi/projecao`, que já É admin-gated e já
ESCREVE estado em runtime (`brapi_budget.set_spot_intervalo`) — sem nenhum
registro de quem mudou o quê. É a prova viva de que o padrão "admin escreve
config em runtime" já existe no código; falta generalizá-lo com auditoria.

`server/app/plan.py` tem a estrutura de planos (`PLAN_FREE`/`PLAN_PRO`,
hooks `can_add_ticker`/`can_analyze`/`requires_subscription`) mas **todos os
limites são `None`** (sempre permite) e `current_plan(user)` recebe um
parâmetro `user` que nunca é usado — o design já previa resolução por
usuário, só não foi ligado. O ADR-010 já decidiu a parte comercial desse
modelo (cap por conta, validação de recibo de loja, `brapi_budget` como cota
física separada do cap comercial) — este ADR **não redecide nada disso**,
fecha a lacuna de superfície de administração em cima do que já foi
decidido.

---

## Etapa 1 — Pesquisa de mercado (padrões, não stack)

### Django Admin + django-guardian
- **Padrão:** RBAC clássico (grupo → permissões nomeadas fixas) via
  `auth.Group`/`Permission`, estendido por permissão **por objeto**
  (django-guardian) — a mesma permissão nomeada pode valer por instância, não
  só por modelo inteiro.
- **Onde checa:** no *authorization backend* plugável do Django, chamado via
  `user.has_perm(perm, obj)` — ponto central, não `if` espalhado por view.
- **Aplica ao Boris+:** `_is_obs_admin` devia virar checagem de permissão
  nomeada (`obs.read`, `prompts.write`) resolvida num ponto central — não uma
  decisão binária espalhada em 8 rotas repetindo o mesmo `if`.

### Auth0 / Clerk / WorkOS
- **Padrão:** RBAC com escopo de **organização** — papel/permissão são
  atributos da *membership* (usuário × org), não do usuário global.
- **Onde checa:** permissões embutidas no **access token** na emissão; o
  resource server valida o claim localmente, sem round-trip por request.
- **Aplica ao Boris+:** decisão explícita a registrar — o papel fica
  embutido na sessão (checagem local, rápida, revogação só no próximo
  login) ou é sempre consultado no backend (mais lento, revogação
  imediata)? Este ADR escolhe a segunda opção (ver Decisão 3) porque o
  volume de chamadas admin é baixo e revogação imediata pesa mais que
  latência aqui.

### Stripe Entitlements / Billing
- **Padrão:** gating por **feature associada a produto/plano** — não é RBAC
  de usuário, é "esta conta tem a feature X ativa" resolvido pela
  assinatura; a feature é a unidade.
- **Onde checa:** Stripe mantém a entitlement no lado deles, notifica por
  webhook; a aplicação replica num cache/tabela local — nunca chama a API
  deles no caminho crítico do request.
- **Aplica ao Boris+:** `plan.py` deve seguir o mesmo padrão — plano vira
  campo persistido por usuário (fonte de verdade local), nunca recalculado
  a partir de config externa a cada request.

### LaunchDarkly / Statsig
- **Padrão:** feature flag **por segmento/atributo**, não papel fixo —
  regras de targeting contra atributos de contexto (plano, cohort, rollout).
- **Onde checa:** SDK mantém cache local atualizado por streaming/polling;
  avaliação é local e determinística.
- **Aplica ao Boris+:** separar duas perguntas que hoje se misturam num
  único allowlist de e-mail — "este usuário tem o papel admin" (RBAC) é
  diferente de "esta feature está ligada para este plano" (entitlement).
  Tratar como dois sistemas (ver Decisão 1).

### Supabase RLS + custom claims
- **Padrão:** ABAC **no nível do dado** — a policy SQL compara coluna do
  registro contra um claim do JWT; `app_metadata` é imutável pelo cliente,
  única fonte confiável.
- **Onde checa:** no banco, em toda query — impossível contornar mesmo com
  acesso direto à API/SQL.
- **Aplica ao Boris+:** o Boris+ não expõe banco direto a cliente (tudo
  passa pelo FastAPI) — o equivalente aqui é nunca confiar em claim editável
  pelo cliente (o `scope` já vem só do Bearer token resolvido server-side,
  isso já está certo) e centralizar a checagem numa `Depends()`, não em cada
  handler.

### GitHub — papéis de organização/team/repo
- **Padrão:** RBAC hierárquico com **override por granularidade** — papel
  de org é o piso, team refina, repo é o mais específico e vence; papéis
  custom compõem permissões nomeadas por recurso.
- **Onde checa:** resolução central por recurso no momento do acesso,
  combinando os três níveis numa decisão só.
- **Aplica ao Boris+:** vale copiar "papel base + override por recurso
  específico" (ex.: alguém que só edita prompt, sem ser admin geral) — não a
  quantidade de níveis do GitHub, que é desproporcional a um backend deste
  tamanho.

---

## Etapa 2 — Auditoria: quem acessa o quê hoje

### Legenda das colunas
- **Gate hoje**: dependência FastAPI aplicada (`—` = nenhuma).
- **Quem passa hoje**: anônimo / logado / admin binário.
- **Papel/plano mínimo proposto**: ver modelo da Decisão 1.

### Middleware (roda ANTES de qualquer rota — cross-cutting, fora da tabela de rotas)

| Middleware | O que faz | Quem afeta |
|---|---|---|
| `gate_cadastro_obrigatorio` | Se `B3_GATED_HOSTS` tem o host da request E o path é `/api/*` fora de `/api/auth/*`/`/api/health`, exige sessão válida (401). Hoje **dormente** (`B3_GATED_HOSTS` vazio) — só afeta `acamerini.app` quando configurado. | Todas as rotas `/api/*`, condicionalmente por host |
| `security_headers` | Só cabeçalhos de resposta (X-Frame-Options etc.) — sem controle de acesso. | Todas |
| `log_requests` | Só observabilidade — sem controle de acesso. | Todas |

Qualquer RBAC novo **compõe com** este gate, não o substitui: o middleware
decide "esta request pode ir a este host sem sessão", o RBAC decide "com
sessão, o que este usuário pode fazer". Dois mecanismos independentes, ordem
de execução importa (middleware roda primeiro).

### Static mounts (sem gate de rota — bundle é público, o gate real é nas chamadas de API que o bundle faz)

| Mount | Conteúdo | Gate real |
|---|---|---|
| `/admin/*` | Bundle do `web-admin/` (JS/CSS/HTML) | Nenhum no arquivo estático — todo dado sensível vem de `/api/obs/*`, `/api/analytics/*`, `/api/admin/*`, gated por `_is_obs_admin` em cada rota |
| `/*` | Bundle do app consumidor (`web_dist`) | Nenhum — app público, dado vem das rotas `/api/*` |
| `/ios/*` (condicional) | `.ipa` Ad Hoc para instalação OTA | Nenhum — mitigado por UDID pré-registrado no portal Apple, fora do backend |

### Rotas de `server/app/main.py` (72) + `server/app/options_api.py` (4) — 76 rotas, 100% cobertas

Contagem confirmada por script (`grep`/regex sobre os dois arquivos, não
contagem manual) — 72 + 4 = 76.

**PÚBLICO (zero dependência de identidade — nem `current_scope`)**

| Método/rota | Papel/plano mínimo hoje | Proposto |
|---|---|---|
| POST `/api/auth/register` | público (rate-limited) | público |
| POST `/api/auth/login` | público (rate-limited) | público |
| POST `/api/auth/oauth` | público (rate-limited) | público |
| POST `/api/auth/logout` | público (no-op se sem token — não tem `Depends()` de identidade) | público |
| GET `/api/ai/models` | público | público (catálogo estático) |
| GET `/.well-known/apple-app-site-association` | público | público (exigência da Apple) |
| GET `/api/fundamentals/{ticker}` | público | público (dado de mercado, sem PII) |
| GET `/api/scan/progress` | público | público (telemetria de processo) |
| GET `/privacidade` | público | público (exigência App Store Connect) |
| GET `/privacy` | público | público (alias da mesma rota) |
| GET `/ios/manifest.plist` (condicional) | público | público (mitigado por UDID) |
| GET `/api/options/expirations/{ticker}` | público | público (dado de mercado) |
| GET `/api/options/chain/{ticker}` | público | público |
| GET `/api/options/gate/{ticker}` | público | público |
| POST `/api/options/analyze` | público | público (educacional, sem estado) |

15 rotas públicas.

**ANÔNIMO OK (`current_scope` — funciona sem login; com token, personaliza por `user_id`)**

| Método/rota | Papel/plano mínimo hoje | Proposto |
|---|---|---|
| GET `/api/health` | anônimo ok | anônimo ok |
| GET `/api/state` | anônimo ok | anônimo ok |
| PUT `/api/config` | anônimo ok | anônimo ok |
| POST `/api/config/test` | anônimo ok | anônimo ok |
| POST `/api/reset` | anônimo ok | anônimo ok |
| PUT `/api/skill` | anônimo ok | anônimo ok |
| POST `/api/skill/restore` | anônimo ok | anônimo ok |
| PUT `/api/llm-prompts` | anônimo ok | anônimo ok (override PESSOAL do usuário — sempre tem prioridade sobre o default, mesmo o editado pelo admin; ver Decisão 5a) |
| POST `/api/snapshot` | anônimo ok | anônimo ok |
| PUT `/api/watchlist` | anônimo ok | anônimo ok |
| POST `/api/watchlist/add` | anônimo ok (`plan.can_add_ticker` sempre libera) | anônimo ok até o cap do `PLAN_FREE`; `pagante` sem cap (gancho já existe, só liga o número — fora deste ADR, é ADR-010) |
| PUT `/api/profile` | anônimo ok | anônimo ok |
| GET `/api/validate/{ticker}` | anônimo ok | anônimo ok |
| GET `/api/quotes` | anônimo ok | anônimo ok |
| GET `/api/history/{ticker}` | anônimo ok | anônimo ok |
| GET `/api/technical/models` | anônimo ok | anônimo ok |
| GET `/api/technicals/{ticker}` | anônimo ok | anônimo ok |
| GET `/api/scan` | anônimo ok | anônimo ok |
| GET `/api/scan/deep/estimate` | anônimo ok | anônimo ok |
| POST `/api/scan/deep` | anônimo ok (cota de IA gerenciada se logado sem BYOK) | anônimo ok — cota já é por plano via `metering` |
| POST `/api/technical/analyze/{ticker}` | anônimo ok (`plan.can_analyze` sempre libera) | anônimo ok até o cap do `PLAN_FREE` (ADR-010, não decidido aqui) |
| POST `/api/analyze/{ticker}` (legado) | anônimo ok | idem acima |
| POST `/api/carteira-stopalvo/{ticker}` | anônimo ok | anônimo ok |
| POST `/api/buy` | anônimo ok | anônimo ok — carteira é sempre virtual, sem gate de plano |
| POST `/api/sell` | anônimo ok | anônimo ok |
| **PUT `/api/position/{ticker}`** | anônimo ok, **sem nenhum gate de plano** | **anônimo ok, sem gate — invariante. Stop/alvo NUNCA é vetado por papel/plano (restrição do CLAUDE.md); nenhuma proposta deste ADR adiciona `Depends()` de plano aqui** |
| POST `/api/options/buy` | anônimo ok | anônimo ok |
| POST `/api/options/sell` | anônimo ok | anônimo ok |
| **PUT `/api/options/position/{contract_id}`** | anônimo ok, **sem gate** | **idem: invariante preservada, mesmo motivo** |
| PUT `/api/agent` | anônimo ok | anônimo ok |
| GET `/api/intraday` | anônimo ok | anônimo ok |
| GET `/api/timing/{ticker}` | anônimo ok | anônimo ok |
| GET `/api/conceitos` | anônimo ok | anônimo ok |
| POST `/api/conceito/{cid}` | anônimo ok | anônimo ok |
| GET `/api/pet/resumo` | anônimo ok | anônimo ok |
| GET `/api/kb/buscar` | anônimo ok | anônimo ok (busca determinística, grátis) |
| POST `/api/assistente` | anônimo ok até a KB não cobrir; **401 explícito se cair pra LLM sem login** (`require_user` implícito no corpo da função, não na assinatura) | mesmo comportamento — LLM continua exigindo `usuário` (mínimo, sem exigir `pagante`; BYOK dispensa cota) |
| POST `/api/cycle` | anônimo ok | anônimo ok |
| POST `/api/analysis-log/{ticker}` | anônimo ok | anônimo ok |
| GET `/api/analysis-outcomes` | anônimo ok | anônimo ok |
| GET `/api/analysis-outcomes/stats` | anônimo ok | anônimo ok |
| GET `/api/ai-activity` | anônimo ok | anônimo ok |
| GET `/api/analysis-outcomes/export.csv` | anônimo ok | anônimo ok |
| GET `/api/agent/status` | anônimo ok | anônimo ok |
| GET `/api/ai/quota` | anônimo ok | anônimo ok |

45 rotas funcionam anônimas (`current_scope`) e personalizam por `user_id`
quando há token.

**USUÁRIO (`require_user` — exige sessão válida, qualquer plano)**

| Método/rota | Papel/plano mínimo hoje | Proposto |
|---|---|---|
| GET `/api/auth/me` | usuário | usuário |
| DELETE `/api/account` | usuário | usuário |
| POST `/api/push/register-token` | usuário | usuário |
| POST `/api/agent/run-now` | usuário | usuário |
| GET `/api/agent/log` | usuário | usuário |
| POST `/api/push/test` | usuário | usuário |
| POST `/api/analytics/events` | usuário | usuário |

7 rotas exigem sessão válida sem exigir permissão nomeada nem plano pago.

**ADMIN (`require_user` + `_is_obs_admin` binário)**

| Método/rota | Gate hoje | Proposto |
|---|---|---|
| GET `/api/obs/logs` | admin binário | `observabilidade.ver` |
| GET `/api/obs/usage` | admin binário | `observabilidade.ver` |
| GET `/api/obs/brapi/projecao` | admin binário | `fontes_dados.configurar` (leitura da própria permissão de escrita — só quem configura vê o valor vigente) |
| **POST `/api/obs/brapi/projecao`** | admin binário, **escreve sem audit log** | `fontes_dados.configurar` — **primeira rota migrada para o audit log** (ver Decisão 4) |
| GET `/api/analytics/summary` | admin binário | `observabilidade.ver` |
| GET `/api/analytics/ia-eficiencia` | admin binário | `operador_ia.ver` |
| GET `/api/analytics/automacao` | admin binário | `execucao_automatica.ver` |
| GET `/api/analytics/tendencias` | admin binário | `observabilidade.ver` |
| GET `/api/admin/summary` | admin binário | `observabilidade.ver` |

Contagem: 15 públicas + 45 anônimo-ok + 7 usuário + 9 admin =
**76/76 rotas cobertas** (72 de `main.py` + 4 de `options_api.py`).

### Rotas NOVAS propostas (não existem hoje — fora da contagem de 76 acima)

Superfície nova que este ADR introduz para fechar os 7 grupos de permissão
com ação real, não permissão vazia:

| Método/rota (proposta) | Permissão | O que muda |
|---|---|---|
| `PUT /api/admin/config/ia` | `llm.configurar` | provider/model/cota/rate/teto global gerenciados passam a ter override em DB, lido ANTES do env var |
| `PUT /api/admin/agent/kill-switch` | `execucao_automatica.ver` + variante de escrita (nomear na implementação, ex. `execucao_automatica.controlar`) | `B3_AGENT_KILL` sai do env-only e ganha toggle em runtime, auditado — hoje exige redeploy para desligar o Operador globalmente |
| `PUT /api/admin/prompts/{key}` | `prompts.editar` | ver Decisão 5 — edita o DEFAULT global; edição do usuário sempre tem prioridade |
| `POST /api/admin/users/{id}/roles` | `usuarios.gerenciar` | atribui/revoga um dos 7 grupos a um usuário |
| `GET /api/admin/audit` | qualquer permissão `*.configurar`/`.editar`/`.gerenciar` (filtrado ao que a pessoa administra) | lista `admin_audit_log` |

`execucao_automatica.ver` nasce cobrindo só LEITURA (`/api/analytics/automacao`,
já existente). O kill-switch é a única ação de ESCRITA proposta para este
grupo nesta rodada — não foi pedida nenhuma outra ação de controle sobre
execução automática (ex.: pausar por usuário), então nenhuma foi inventada;
se precisar, entra depois como nova permissão aditiva, sem reescrever o
grupo.

### Onde vive cada peça de config que o pedido quer centralizar

| Config | Onde vive hoje | Como muda hoje |
|---|---|---|
| IA gerenciada (provider/model/cota/rate/teto global) | env vars (`B3_MANAGED_LLM_*`) lidas em `managed.py` a cada chamada | edição de env no Railway + redeploy |
| Fontes de dados (intervalo de spot da brapi) | SQLite via `brapi_budget.set_spot_intervalo` | **já tem rota admin** (`POST /api/obs/brapi/projecao`) — único caso já dinâmico, sem audit log |
| Fontes de dados (universo do scan, fatias de orçamento) | env vars (`B3_SCAN_UNIVERSE`, `_FRACOES`) | edição de env/código + redeploy |
| Prompts (skill/skillOperador/llmPrompts, default global) | código-fonte (`server/app/defaults.py`), espelhado em `web/src/catalog.js` | hoje: PR + redeploy. **Decidido neste ADR**: passa a ter uma camada editável em runtime por admin, sem tocar `defaults.py`/`catalog.js` (ver Decisão 5) |
| Prompts (llmPrompts por usuário) | SQLite, `PUT /api/llm-prompts` já existe | já é dinâmico, por conta, sem admin — cada usuário edita o próprio |
| Caps de plano (`PLAN_FREE`/`PLAN_PRO`) | código-fonte (`plan.py`), todos `None` | PR + redeploy (ADR-010, decisão comercial pendente) |
| Admin allowlist (`B3_ADMIN_EMAILS`) | env var | edição de env + redeploy |

---

## Decisões do Alex incorporadas (2026-08-16)

As 4 pendências da primeira versão deste ADR foram decididas: (1) prompts
default SÃO editáveis em runtime, com edição do usuário sempre tendo
prioridade sobre o default (mecanismo na Decisão 5); (2) os grupos de
permissão nascem organizados por **macro função de produto** (ex.: Operador
IA, Execução de ordens automáticas, Mudança de LLM), não um `role_admin`
monolítico; (3) **sem** tela de override manual de plano nesta rodada — só
a coluna/migração; (4) `config.ia` e `config.fontes` são permissões
separadas (confirma o design original). O texto abaixo já reflete essas
decisões — nada nesta seção fica pendente de aprovação além dos detalhes de
implementação nomeados no fim.

## Decisão (técnica — proposta deste ADR)

### 1. Modelo de papel/plano

Duas dimensões **ortogonais**, não uma única enumeração — é o padrão que
apareceu em 4 dos 6 exemplos pesquisados (Django, Auth0/WorkOS, Stripe,
LaunchDarkly separam "quem administra" de "o que a assinatura libera"):

- **Papel de governança** (quem administra o sistema): `visitante` (sem
  conta) → `usuário` (conta, sem privilégio) → **grupos de permissão
  nomeada, organizados por macro função de produto** (não um enum
  `admin`/`não-admin`, nem permissões técnicas soltas tipo `config.write`).
  7 grupos iniciais, cada um mapeado a UMA função reconhecível do produto:

  | Grupo (macro função) | Permissão | Cobre hoje |
  |---|---|---|
  | Observabilidade | `observabilidade.ver` | `/api/obs/logs`, `/api/obs/usage`, `/api/admin/summary`, `/api/analytics/summary`, `/api/analytics/tendencias` |
  | Operador IA | `operador_ia.ver` | `/api/analytics/ia-eficiencia` (eficiência das análises N1/N2) |
  | Execução de ordens automáticas | `execucao_automatica.ver` | `/api/analytics/automacao` (leitura). Controle (kill-switch) é extensão NOVA — ver Decisão 4 |
  | Mudança de LLM | `llm.configurar` | NOVA — hoje só `B3_MANAGED_LLM_*` (env) |
  | Fontes de dados | `fontes_dados.configurar` | `/api/obs/brapi/projecao` GET+POST (rota já existe, migra a permissão) |
  | Prompts | `prompts.editar` | NOVA — ver Decisão 5 |
  | Usuários e papéis | `usuarios.gerenciar` | NOVA — atribuir/revogar papel (sem override de plano) |

  Um `role_admin` de bootstrap agrupa as 7 — migração idêntica ao
  `_is_obs_admin` de hoje (`B3_ADMIN_EMAILS` ou 1º usuário) recebe as 7
  permissões de uma vez, ninguém perde acesso que já tinha. Crescer =
  criar um 8º grupo com um subconjunto (ex.: `suporte` = só
  `usuarios.gerenciar` de leitura) — zero mudança no modelo, uma linha nova
  na tabela de grupos.
- **Plano comercial** (monetização): `visitante` → `free` (logado, cap do
  `PLAN_FREE`) → `pro` (`PLAN_PRO`, recibo validado). Este eixo já existe em
  `plan.py` — a mudança é ligar `current_plan(user)` a um campo persistido
  (`users.plan`), em vez do `ACTIVE_PLAN` global fixo hoje. A resolução do
  recibo (App Store/Google Play) **continua pendente do ADR-010**. **Sem
  tela de override manual nesta rodada** (decisão do Alex) — só a
  coluna/migração; se um caso de suporte precisar de ajuste manual, é uma
  operação direta no banco até essa tela nascer numa fase futura.

O pedido menciona "admin / pagante / visitante" como os 3 papéis mínimos —
a arquitetura acima cobre os 3, mas separa explicitamente "pagante" (eixo de
plano) de "admin" (eixo de governança, agora em 7 grupos), porque são
independentes: um admin pode nunca ter plano `pro` (não precisa, já vê tudo
por permissão), e um `pro` não ganha nenhuma permissão administrativa por
pagar.

**Persistência:** duas tabelas novas, aditivas —
`user_roles(user_id, role, granted_at, granted_by)` (many-to-many, `role`
é um dos 7 grupos ou `role_admin`) e `users.plan` (coluna nova, default
`free`, migração preenche `pro` para quem já tiver algum sinal de
pagamento hoje — hoje não há nenhum, então começa vazio). Nenhuma tabela
existente perde coluna nem muda semântica.

### 2. Mapeamento função→permissão

A tabela completa está na Etapa 2 acima (76/76 rotas). Resumo por
categoria proposta:

| Papel/plano mínimo | Nº de rotas |
|---|---|
| público | 15 (dado de mercado/estático + entrada de auth) |
| anônimo ok (`current_scope`) | 45 |
| usuário (`require_user`) | 7 |
| permissão nomeada (`observabilidade.ver`/`operador_ia.ver`/`execucao_automatica.ver`) | 9 |

Nenhuma rota de dado de carteira (compra, venda, stop/alvo, watchlist)
ganha gate de plano novo neste ADR — os hooks de cap (`can_add_ticker`,
`can_analyze`) já existem em `plan.py` e continuam sob decisão comercial do
ADR-010, não deste.

### 3. Onde a checagem é aplicada

Sempre no backend, via `Depends()` do FastAPI — nunca escondendo botão no
front. Duas dependencies novas, compondo com as duas que já existem
(`current_scope`, `require_user`):

```python
# server/app/rbac.py (novo módulo)
def require_permission(perm: str):
    def _dep(user: dict = Depends(require_user)) -> dict:
        if not rbac.user_has_permission(_conn, user["id"], perm):
            raise HTTPException(403, f"Requer a permissão '{perm}'.")
        return user
    return _dep

def require_plan(min_plan: str):
    def _dep(user: dict = Depends(require_user)) -> dict:
        if not plan.plan_at_least(plan.current_plan(user), min_plan):
            raise HTTPException(402, "Recurso do plano pago.")
        return user
    return _dep
```

`_is_obs_admin` é substituída por `require_permission("observabilidade.ver")`
(e equivalentes por grupo — `operador_ia.ver`, `execucao_automatica.ver`,
`fontes_dados.configurar`) nas 9 rotas admin — a função em si vira uma
consulta a
`user_roles` join permissões do grupo, cacheada em memória por request
(sem round-trip extra por chamada dentro do mesmo request; revogação é
imediata no próximo request, decisão explícita — ver pesquisa Auth0/WorkOS
acima, escolhemos "sempre backend" em vez de "embutido no token").

A UI (`web-admin/`) passa a receber `permissions: [...]` em
`GET /api/auth/me` e esconde botões que o usuário não tem — **só
cosmético**; toda rota de escrita valida a permissão de novo,
independente do que a UI mostrou.

O middleware `gate_cadastro_obrigatorio` não muda — continua sendo a
camada de "esta request pode chegar sem sessão neste host", checada ANTES
de qualquer `Depends()` de rota.

### 4. `web-admin/` como central de administração

Novas telas, cada uma atrás da permissão nomeada correspondente:

- **Usuários e papéis** (`usuarios.gerenciar`): lista (`db.list_users` já
  existe), atribuir/revogar um dos 7 grupos. **Sem override manual de
  plano nesta rodada** (decisão do Alex) — a tela mostra o `users.plan`
  vigente, só leitura; escrita fica para uma fase futura, se necessário.
  Toda mudança de papel grava uma linha de auditoria.
- **Mudança de LLM** (`llm.configurar`): hoje só leitura via
  `/api/obs/usage`; nova rota `PUT /api/admin/config/ia` grava override em
  tabela `admin_config(key, value, updated_by, updated_at)` — a leitura em
  `managed.py` passa a checar essa tabela ANTES do env var (env continua
  como piso de bootstrap/infra, nunca removido).
- **Fontes de dados** (`fontes_dados.configurar`): generaliza o padrão que
  `POST /api/obs/brapi/projecao` já usa — essa rota é a PRIMEIRA migrada
  para o audit log (prova de que o mecanismo funciona antes de estender a
  prompts). Permissão **separada** de `llm.configurar` (decisão do Alex,
  item 4) — quem edita a fonte de cotação não ganha automaticamente
  permissão para trocar o modelo de IA, e vice-versa.
- **Prompts** (`prompts.editar`): ver Decisão 5 — decidido, editável, com
  precedência da edição do usuário.
- **Operador IA** (`operador_ia.ver`) e **Execução de ordens automáticas**
  (`execucao_automatica.ver` + kill-switch): telas de leitura reaproveitando
  `/api/analytics/ia-eficiencia` e `/api/analytics/automacao`; a segunda
  ganha o toggle do kill-switch (ver "Rotas NOVAS propostas" acima).
- **Auditoria** (nova tela, visível a quem tem qualquer permissão de
  escrita, filtrada ao que a pessoa administra): lista
  `admin_audit_log(id, actor_user_id, at, entity, entity_id, field,
  old_value, new_value)` — toda escrita de admin, sem exceção "por
  enquanto".

`server/app/audit.py` (novo módulo, mesmo padrão stdlib-only de
`metering.py`): uma função `record(conn, actor_id, entity, entity_id,
field, old, new)` chamada por TODA rota de escrita admin — sem opt-out por
rota.

### 5. Trade-offs e decisões de implementação

**a) Prompts código → config editável, com prioridade da edição do usuário
(decidido pelo Alex).** CLAUDE.md descreve a paridade `defaults.py` ↔
`catalog.js` como "byte a byte — teste trava". Verificado na auditoria:
isso é **preciso só para** `llmPrompts.carteiraStopAlvo` e
`carteiraStopAlvoOperador` (`test_a8ii_paridade_defaults_carteira_com_catalog_js`,
comparação de string exata). `skill`/`skillOperador` são espelhados mas
checados só por presença de substring (`test_copy_theme.mjs`), não por
igualdade de texto completo — uma divergência ali hoje passaria
despercebida pelos testes atuais, independente deste ADR.

**O código continua sendo o piso de recuperação de desastre — não é
tocado.** `defaults.py` e `catalog.js` seguem existindo, seguem espelhados,
`test_a8ii` continua rodando exatamente como hoje. A edição do admin entra
como uma camada NOVA, por cima, nunca escrita em `defaults.py`:

- Tabela nova `prompt_defaults_override(chave, texto, updated_by,
  updated_at)` — o "default" que `ensure_defaults` usa para semear conta
  nova e fazer backfill passa a ser: override em DB, se existir; senão
  `defaults.default_llm_prompts()` (código), como hoje.
- **A prioridade da edição do usuário já é resolvida por um mecanismo que
  EXISTE no código, não é uma peça nova**: `store._eh_default_antigo` +
  `defaults.LEGACY_PROMPT_SHA256` — hoje comparam o texto salvo do usuário
  contra hashes de gerações anteriores do default (de commits antigos) para
  decidir se ele "nunca editou" (migra pro default novo) ou "editou de
  verdade" (fica intocado). Isso já roda em TODO login (`ensure_defaults`
  é chamado por `seed_user_from`/`_apply_seed` a cada `register`/`login`/
  `oauth`). A mudança é só a FONTE do histórico de hashes: hoje é uma lista
  hardcoded no código (uma linha por commit); passa a ser uma tabela
  `prompt_default_history(chave, sha256, texto, criado_em)` que ganha uma
  linha toda vez que o admin publica uma edição — o texto anterior (seja
  ele o código-fonte ou uma edição anterior do admin) entra como "hash
  conhecido de default", e `_eh_default_antigo` passa a consultar essa
  tabela em vez de (além de) `LEGACY_PROMPT_SHA256`. Resultado: usuário que
  nunca tocou no prompt sobe para o novo default no próximo login; usuário
  que editou o próprio texto nunca é sobrescrito — **exatamente o
  comportamento pedido, reusando um mecanismo já testado
  (`test_migracao_llmprompts_default_antigo_sobe_edicao_fica`) em vez de
  inventar um novo.**
- **iOS não é afetado por este mecanismo.** O app nativo é local-first:
  monta o próprio default de `web/src/catalog.js` embarcado no bundle, sem
  consultar o servidor para isso (só usa o servidor pra cotação/análise). A
  edição de default do admin vale para o servidor (contas web e o
  `llmPrompts` que o servidor usa quando o cliente não manda `skill`/
  `config` no corpo) — **verificar isso ao vivo antes de implementar**
  (rodar o app e confirmar que nenhuma chamada de iOS lê `llmPrompts`
  server-side sem mandar o próprio prompt no corpo), não assumir só pela
  leitura do código.

Nada disso remove ou modifica `test_a8ii`/`catalog.js` — o "teste-guardião"
citado na restrição continua de pé, sem mudança. Não há decisão pendente
aqui para o Alex além da implementação em si.

**b) Risco de permissão vazando por rota esquecida.** Mitigação: teste de
CI que enumera todas as rotas registradas no `app.routes` do FastAPI e
falha se alguma não tiver uma dependency reconhecida (`current_scope`,
`require_user`, `require_permission`, `require_plan`, ou estar na
allowlist explícita de "pública, dado de mercado"). A tabela da Etapa 2
deste ADR vira o baseline checado — rota nova sem entrada na allowlist
quebra o build, força decisão consciente em vez de omissão.

**c) O que fica de fora desta rodada:**
- Validação de recibo de loja (App Store/Google Play) — ADR-010, pendente,
  decisão comercial do Alex.
- Hospedagem/infra do `web-admin/` — ADR-011, não decidido lá, não decidido
  aqui.
- Ativar os caps numéricos de `PLAN_FREE`/`PLAN_PRO` (quantos ativos,
  quantas análises/mês) — ADR-010, decisão comercial pendente.
- Papel/plano interferindo em stop/alvo de proteção — **nunca**, invariante
  preservada explicitamente na Etapa 2.

---

## Pendente (decisão do Alex)

As 4 pendências originais foram resolvidas (ver "Decisões do Alex
incorporadas" no topo da seção de Decisão). O que resta é detalhe de
implementação, não arquitetura:

- Nome exato da permissão de escrita do kill-switch
  (`execucao_automatica.controlar` sugerido — Decisão "Rotas NOVAS
  propostas").
- Retenção de `admin_audit_log` (para sempre? N dias? Isso é escolha de
  produto/custo de armazenamento, não afeta o modelo).
- Confirmar ao vivo (não só por leitura de código) que nenhum caminho de
  iOS depende do `llmPrompts` server-side sem mandar o próprio prompt no
  corpo, antes de ligar a migração de default via admin (Decisão 5a).

## Guardrails do CLAUDE.md — como cada um é respeitado

- **Manchete só do motor determinístico**: não tocado — RBAC/plano nunca
  entra em `setups.py`/`technical_snapshot`, só decide quem LÊ observabilidade
  ou ESCREVE config/prompt.
- **Stop/alvo nunca vetado**: invariante nomeada explicitamente na Etapa 2
  para `PUT /api/position/{ticker}` e `PUT /api/options/position/{contract_id}`
  — nenhuma dependency de plano/papel é adicionada a essas duas rotas.
- **Guardiões de teste não se apagam**: `test_a8ii` não é tocado por este
  ADR — a edição de prompt do admin vive numa camada nova (tabela de
  override + histórico de hashes), o código (`defaults.py`/`catalog.js`)
  segue exatamente como está, guardado exatamente como está (Decisão 5a).
- **Histórico não se reescreve**: nenhum arquivo em `qa/`, `ESTADO-*`,
  `CHECKOUT-*`, RELEASES é tocado por este ADR.
- **Publicação é passo manual separado**: `web-admin/` continua publicado
  por `scripts/publicar-admin.sh`; merge deste ADR (quando implementado) não
  publica o front sozinho, mesma disciplina do ADR-012.
- **Login obrigatório, conta nova nasce limpa**: não tocado — RBAC/plano é
  uma camada SOBRE a conta já autenticada, não muda o fluxo de cadastro nem
  semeia dado novo em conta nova.
- **Bundle id / codinomes internos**: não tocado — nenhuma mudança de bundle
  id, nomenclatura de arquivo ou env.

## Referência cruzada

- `docs/adr/010-planos-e-cap-gratuito.md` — decisão comercial de plano;
  este ADR fecha a lacuna de SUPERFÍCIE que o 010 deixou pendente, sem
  redecidir preço/cap/recibo.
- `docs/adr/011-modulo-observabilidade-governanca.md` — identificou o gap
  (`plan.py` sem superfície) e explicitamente deixou RBAC "fora de escopo,
  projeto à parte" — este é esse projeto.
- `docs/adr/012-observabilidade-v2-tendencia-eficiencia.md` — Fases 1-5 do
  `web-admin/`, hoje só leitura; este ADR é a Fase 6 (escrita), pendente de
  aprovação.
- `server/app/main.py:385-393` — `_is_obs_admin`, o gate binário substituído.
- `server/app/plan.py` — `current_plan(user)`, o parâmetro não usado que
  este ADR liga.
