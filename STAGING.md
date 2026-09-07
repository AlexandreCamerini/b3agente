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
| URL | `bolsia.semente.dev` · `boris.semente.dev` | `b3agente-staging.up.railway.app` |
| Branch rastreada | `main` | — (não rastreia; ver abaixo) |
| Como publicar | `scripts/promover-staging-para-producao.sh` | `scripts/publicar-staging.sh` |
| Banco | volume próprio, `b3.db` ~1,1 GB | volume próprio, `b3.db` ~192 KB |
| Dados | reais dos usuários | isolados, descartáveis |

Projeto: `bolsIA` · serviço: `b3agente` · `rootDirectory=/server` nos dois.

---

## Regra número um

**Nenhum comando de CLI que mexe em branch é seguro.** O campo de branch é
COMPARTILHADO entre os environments no modelo de dados do Railway. Mudar a
branch de staging muda a de produção junto — e produção tem auto-deploy.

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

Para promover depois de validar:

```bash
bash scripts/promover-staging-para-producao.sh
```

Faz merge da branch local em `main`, roda a suíte **de novo já com o merge**,
e só empurra depois que você digitar `PRODUCAO`. É o único caminho que toca
produção.

---

## O que staging NÃO prova

Decisão consciente de 2026-09-07 (opção "c" — aceitar e documentar):

`railway up` **ignora o `server/railway.json`**. Consequências medidas nos
logs de build:

| | `railway.json` declara | staging na prática |
|---|---|---|
| Builder | `NIXPACKS` | **Railpack 0.39.0** |
| Python | 3.14 (repo) | **3.13.15** (default do Railpack) |
| `preDeployCommand` | backup do banco | **não roda** |

Provável causa: `railway up` procura o arquivo de config na raiz do upload, e
o nosso está em `server/`. O `rootDirectory=/server` é aplicado ao build (ele
acha o `requirements.txt` certo), mas não à descoberta da config.

**Então staging serve para:** validar UI, fluxo, texto, regressão funcional,
comportamento de API.

**Staging NÃO serve para:** validar nada que dependa da versão do Python, do
builder, ou do processo de deploy em si. Se o bug só aparece em produção,
essa diferença é a primeira suspeita.

Prova de que o backup não roda: o volume de staging tem `b3.db` mas **não tem
`/data/backups/`**. Verifique com
`railway volume files --volume b3agente-volume list /`.

Pendências registradas, não resolvidas:
- mover `railway.json` para a raiz do repo (resolveria os dois casos, mas
  mexe na config que produção usa — exige janela dedicada);
- fixar a versão do Python com `.python-version`/`runtime.txt` em `server/`
  (ataca a divergência mais perigosa sem tocar config compartilhada).

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
