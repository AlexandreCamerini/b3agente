# Staging — ambiente paralelo do Boris+

Ambiente para validar uma versão parcial **sem expor o usuário real**, mantido
em paralelo até você decidir promovê-la a produção.

Escrito em 2026-09-07, depois de dois deploys indevidos em produção no mesmo
dia. Quase tudo aqui é contraintuitivo e foi aprendido quebrando coisa — leia
antes de mexer em qualquer configuração do Railway.

---

## O mapa

| | produção | staging |
|---|---|---|
| Environment (Railway) | `production` | `staging` |
| URL | `boris.semente.dev` | `b3agente-staging.up.railway.app` |
| Branch rastreada | `main` | — (não rastreia; ver abaixo) |
| Como publicar | `scripts/promover-staging-para-producao.sh` | `scripts/publicar-staging.sh` |
| Banco | volume próprio, `b3.db` ~1,1 GB | volume próprio, `b3.db` ~192 KB |
| Dados | reais dos usuários | isolados, descartáveis |

Projeto: `bolsIA` · serviço: `b3agente` · `rootDirectory=/server` nos dois.

---

## Regra número um

**Nenhum comando de CLI que mexe em branch é seguro.** O campo de branch é
COMPARTILHADO entre os environments no modelo de dados do Railway. Mudar a
branch de staging muda a de produção junto.

Em 2026-09-07 isso ainda encontrava produção com auto-deploy LIGADO, então a
mudança de config virava deploy na hora. O auto-deploy foi desligado
justamente por causa disso (ver "Deploy de produção é manual" abaixo) — mas
não trate isso como imunidade: a config continua vazando, só não sobe
sozinha.

Em 2026-09-07 isso aconteceu duas vezes:

1. `railway service source connect --repo ... --branch staging --service b3agente`,
   rodado com o contexto em `staging`, mudou **os dois** environments. A
   ajuda do comando avisa (*"GitHub sources are connected at the service
   level"*) — o aviso é literal.
2. Depois de `railway upgrade` (v5.49.2 → v5.49.3), o
   `railway environment edit --service-config <svc> source.branch` — que
   antes era inócuo — voltou a funcionar e aplicou **nos dois**. Produção
   chegou a servir o build não verificado por alguns minutos.

Detalhe que engana: na v5.49.2 o `environment edit --service-config` não
aplicava **nada**, campo nenhum. O teste que revela isso é pedir uma variável
inexistente — ele responde `{"committed":false,"message":"No changes to
apply"}` igual. Não confie na ausência de erro como prova de que nada mudou.

**Se precisar mudar branch, use o painel** (`Settings → Source → "Branch
connected to staging"`), que é a única superfície com semântica
por-environment declarada. E confira produção logo depois.

---

## Como publicar em staging

```bash
bash scripts/publicar-staging.sh
```

O script: exige árvore limpa → roda a suíte canônica → builda e publica o
front → commita → **pede confirmação** → sobe com `railway up --environment
staging --service b3agente` → confere o carimbo em `/api/health`.

Ele recusa rodar a partir de `main` e recusa `STAGING_ENV=production`.
`railway up` envia o diretório local direto para um serviço+environment
nomeados: não lê branch, não escreve configuração, **não alcança produção**.

## Deploy de produção é manual

**O auto-deploy de produção está DESLIGADO** (2026-09-07, painel: environment
`production` → serviço `b3agente` → Settings → Source → "Auto deploys when
pushed to GitHub" → Disable).

Motivo: os dois incidentes do dia não vieram de push de código — vieram de
mudança de **configuração** no Railway, que disparava deploy imediato. O gate
que existia estava só dentro do script de promoção, e config não passa por
script nenhum. Com o auto-deploy desligado, nada sobe em produção sem um
clique consciente.

Não há como desligar isso por CLI: não está no config do serviço nem no
schema do `railway.json`. É um "deployment trigger", só pelo painel.

Para promover depois de validar em staging:

```bash
bash scripts/promover-staging-para-producao.sh
```

Faz merge da branch local em `main`, roda a suíte **de novo já com o merge**,
publica o front, e só empurra depois que você digitar `PRODUCAO`. **O push
não deploya** — ao final o script imprime o passo manual: painel → environment
`production` → serviço `b3agente` → **Deploy**.

Consequência de escolha, registrada: manter o deploy por git (e não por
`railway up`) preserva o **Nixpacks** em produção. Promover com `railway up`
seria automatizável, mas trocaria o builder para Railpack — a mesma
divergência que staging tem. Não vale o preço em produção.

---

## O que staging NÃO prova

Decisão consciente de 2026-09-07 (opção "c" — aceitar e documentar):

`railway up` **ignora o `server/railway.json`**. Consequências medidas nos
logs de build:

| | `railway.json` declara | staging na prática |
|---|---|---|
| Builder | `NIXPACKS` | **Railpack 0.39.0** |
| `preDeployCommand` | backup do banco | **não roda** |
| Python | — | ~~3.13.15~~ → **3.12.x** (resolvido, ver abaixo) |

Provável causa: `railway up` procura o arquivo de config na raiz do upload, e
o nosso está em `server/`. O `rootDirectory=/server` é aplicado ao build (ele
acha o `requirements.txt` certo), mas não à descoberta da config.

**Então staging serve para:** validar UI, fluxo, texto, regressão funcional,
comportamento de API.

**Staging NÃO serve para:** validar nada que dependa do builder ou do
processo de deploy em si (incluindo o `preDeployCommand`). Se o bug só
aparece em produção, essa diferença é a primeira suspeita.

Prova de que o backup não roda: o volume de staging tem `b3.db` mas **não tem
`/data/backups/`**. Verifique com
`railway volume files --volume b3agente-volume list /`.

Pendência registrada, não resolvida: mover `railway.json` para a raiz do repo
(resolveria builder e backup de uma vez, mas mexe na config que produção usa
— exige janela dedicada e produção sob observação).

### Ordem pendente NUNCA executa em staging (achado de 2026-09-07)

O scheduler executa a fila de ordens pendentes com
`candle_provider.get_quotes_exclusive` — brapi **exclusiva, sem fallback para
o Yahoo** de propósito: preço de execução não pode vir de fonte secundária em
silêncio. Staging não tem `BRAPI_TOKEN` (degradação deliberada, ver a seção
"Por que as credenciais de staging são propositalmente ruins"), então toda
ordem pendente fica parada com este erro gravado nela:

```
fonte exclusiva (brapi) sem cotação: brapi sem BRAPI_TOKEN
    — fonte exclusiva do agente para ABEV3
```

Isso **não é defeito** — é o princípio 4 do CLAUDE.md operando: sem preço
utilizável a ordem permanece pendente e o motivo é registrado, em vez de o
motor inventar um preço. O comportamento foi observado ao vivo e está correto.

Dar um `BRAPI_TOKEN` a staging **não** é a saída: a cota de 15k requisições/mês
é por TOKEN, não por ambiente — staging passaria a comer o orçamento de
produção.

**Como testar fluxo que precisa de posição executada, então:** compre com o
mercado ABERTO. O caminho direto de compra (`main.py`, `if
pregao.in_market_hours():`) usa `candle_provider.get_quote` — o provider
normal, que em staging é o Yahoo — e executa na hora, sem tocar na fila nem
na brapi. Fora do horário real, force com `B3_DEV_MERCADO_ABERTO=1`.

Atenção: forçar o pregão sozinho não basta. O bloco do scheduler exige os DOIS
portões (`agent.py`: `if not kill_switch_on() and in_market_hours():`), e
staging nasceu com `B3_AGENT_KILL=1`. Em 2026-09-07 os dois foram ligados
juntos:

```bash
railway variables --environment staging --service b3agente \
  --set "B3_DEV_MERCADO_ABERTO=1" --set "B3_AGENT_KILL=0"
```

Verificado no mesmo minuto: produção ficou intacta (mesmo build, mesmas
variáveis). Diferente de `service source connect`, o `railway variables` é
mesmo escopado por environment.

Lembre que o kill-switch segue memória → **DB** → env: se alguém já gravou o
override pelo portal admin, mudar a env não tem efeito nenhum. Confira com
`SELECT * FROM admin_config WHERE key='agentKillSwitch'` antes de culpar a env.

### Python: divergência resolvida em 2026-09-07

Antes não havia pin nenhum e cada ambiente pegava o default do seu builder:

```
produção  3.12.7   (Nixpacks)      ← a real, medida por railway ssh
staging   3.13.15  (Railpack)      ← uma minor À FRENTE de produção
local     3.14.6   (server/.venv)  ← e a suíte rodava aqui
```

O `CLAUDE.md` afirmava "Python 3.14" — descrevia a venv local, nunca
produção. Corrigido no mesmo commit.

`server/.python-version` agora fixa **`3.12`**. Minor, não patch: patch exato
pode não existir no nixpkgs e quebrar o build de produção. Isso **não mudou a
versão de produção** — tornou explícito o que já rodava, e trouxe staging
para a mesma minor (hoje 3.12.13 lá, 3.12.7 em produção; a diferença de patch
é ruído, o risco era a 3.13).

Confirme que o pin está valendo pelo log de build — a linha precisa dizer
`idiomatic-version-file`, não `railpack default`:

```bash
railway logs -b --environment staging --service b3agente --lines 300 | grep -i "python.*3\.1"
```

**Armadilha:** `RAILPACK_PYTHON_VERSION` está na documentação do Railpack
como variável de configuração, mas **não funciona como entrada** — o próprio
Railpack a sobrescreve com o valor que resolveu (setamos `3.12.7`, virou
`3.13`). Parece config, é output. Use o arquivo `.python-version`.

Segundo motivo pelo qual ela não funcionaria: `railway up` aparentemente não
passa variáveis do serviço para o ambiente de *build* — só para o runtime.
Mesma família do `railway.json` ignorado.

---

## Por que as credenciais de staging são propositalmente ruins

Cotas externas são por **credencial**, não por ambiente. Copiar as variáveis
de produção faria staging comer a mesma cota — e cada ambiente teria seu
contador local começando do zero, então os dois se achariam dentro do teto
enquanto somados estouram. O próprio `brapi_budget.py` admite que o contador
local é "a previsão" e o header `x-ratelimit-remaining` é "a VERDADE".

Agrava: `scheduler_loop` sobe sozinho no boot (`main.py`). Staging não é uma
cópia parada — sem freio, começaria a rodar radar diário e passada intraday
por conta própria, 24/7.

Configuração aplicada **no ato da criação** (`environment new --duplicate`
com `--service-config`), para não existir janela em que staging suba com
credencial de produção:

| Variável | produção | staging | por quê |
|---|---|---|---|
| `B3_AGENT_KILL` | (ausente) | `1` | mata o ciclo autônomo |
| `B3_CANDLE_PROVIDER` | `brapi` | `yahoo` | brapi é 15k/mês por token |
| `B3_OPTIONS_PROVIDER` | `mydata` | `mock` | zero rede |
| `BRAPI_TOKEN` | real | `""` | cota compartilhada |
| `MYDATA_TOKEN` | real | `""` | 60/min · 2.000/dia |
| `BOLSAI_API_KEY` | real | `""` | — |
| `B3_MANAGED_LLM_KEY` | real | `""` | dinheiro real por chamada |
| `APNS_AUTH_KEY` | real | `""` | push para aparelho real |

`(os.environ.get("X") or "").strip()` é o padrão do código, então **string
vazia conta como ausente** — não precisa remover a variável.

`B3_CANDLE_PROVIDER=yahoo` não é detalhe: com `brapi` e token vazio, a
cotação estoura `RuntimeError` em vez de degradar.

Login social (Apple/Google) e o portal admin (`SEMENTE_ID_*`) não funcionam
em staging — os client IDs têm allowlist de redirect URI do domínio de
produção. Login por e-mail/senha funciona.

---

## Volume: isolado, apesar de parecer o contrário

`RAILWAY_VOLUME_ID` é **idêntico** nos dois environments — é o ID da
*definição*, não da instância de storage. O armazenamento é separado.

Volume compartilhado seria o único desfecho catastrófico possível aqui
(staging escrevendo no banco de produção), então vale saber verificar direito.

**Não use o "Storage used" do `railway volume list`** — ele mede alocação de
filesystem, não conteúdo, e engana. Em 2026-09-07 ele reportou 797MB para um
staging que tinha 344KB de dados reais.

A verificação confiável é olhar os arquivos:

```bash
railway ssh --service b3agente "ls -la /data"
```

Referência de 2026-09-07, logo após a criação:

```
staging:   b3.db  192 KB   ·  analytics.db  45 KB     (banco novo, vazio)
produção:  b3.db  ~1,1 GB                             (dados reais)
```

Se `b3.db` de staging tiver ordem de grandeza próxima da de produção, pare e
investigue antes de qualquer escrita — pode significar que ele está montando
o volume errado.

---

## Rollback

**Código volta fácil.** Todo deploy é um commit; `server/web_dist` é
versionado (o Railway só enxerga `server/`), então front e backend voltam
juntos, no mesmo commit. Dá para reverter por git ou pelo redeploy de um
deployment anterior no painel.

**Dado não volta junto.** O SQLite vive no volume, que sobrevive a qualquer
deploy. E `db.connect()` roda migrações no boot (`ALTER TABLE ADD COLUMN`,
`_migrate_identities_from_users`).

A boa notícia: **todas as migrações são aditivas e idempotentes** — não
existe `DROP TABLE`/`DROP COLUMN` no backend. Rollback de código sobre banco
migrado é seguro: coluna nova fica órfã, código antigo não a lê.

Onde ainda dói: blobs JSON da tabela `kv` (`config`, `positions`, `history`).
Campo novo ignorado é inofensivo; campo que **muda de formato** não é. Caso
conhecido: a migração de `llmPrompts` decide por sha256 — voltar o código não
desmigra o dado.

### Backup

`server/app/backup.py` faz backup online consistente (checkpoint do WAL + API
`.backup()` do SQLite), retendo 14.

Ponto crítico: usa `sqlite3.connect` **cru**, nunca `db.connect()` — este
chama `init_db()`, que migra. Backup tirado depois da migração guarda o
estado NOVO, inútil para voltar atrás. Guardião mutation-tested em
`server/tests/test_backup_pre_deploy.py`.

Mora em `server/app/` e não em `scripts/` porque `rootDirectory=/server`:
`scripts/` **não existe dentro do container**.

Está ligado como `preDeployCommand` no `server/railway.json` — funciona em
deploy por git (produção), **não** em `railway up` (staging, ver acima).
Localmente: `bash scripts/backup-db.sh`.

---

## Checklist de segurança

Antes de qualquer comando que toque configuração do Railway:

1. `railway status` — confirme o environment. Comando certo no environment
   errado é o modo de falha mais comum.
2. Guarde o baseline de produção:
   `railway environment production >/dev/null && railway environment config --json`
3. Rode o comando.
4. **Verifique produção imediatamente** — branch, `/api/health`, carimbo.
5. Se mudou, reverta na hora com o baseline.

O passo 4 não é paranoia: foi o que permitiu afirmar com evidência que
produção não chegou a rodar o código não verificado no primeiro incidente (o
deploy dela não tinha a linha `[backup]`, que só existe na outra branch).
