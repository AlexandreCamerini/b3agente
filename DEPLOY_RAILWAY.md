# Publicar o backend no Railway (e apontar o iPhone para lá)

Com o backend no Railway você ganha uma URL pública **HTTPS** e o app no iPhone
funciona de qualquer rede — não precisa mais estar na mesma Wi‑Fi do Mac.

> Importante: o backend é **stateless** para o app do iPhone. O telefone guarda
> tudo (config, chave, watchlist, carteira, histórico, análises) **no próprio
> aparelho** e usa o servidor só para **cotações** e **análise da IA** (enviando
> sua config + chave no corpo da requisição). Por isso o disco efêmero do Railway
> não atrapalha o uso no celular.

---

## Opção A — Deploy pelo GitHub (recomendado)

1. Suba o projeto para um repositório no GitHub (a pasta `b3-agente` inteira).
2. Em https://railway.app → **New Project** → **Deploy from GitHub repo** →
   escolha o repositório.
3. Abra o serviço criado → **Settings**:
   - **Root Directory**: `server`
     (essencial — é onde estão o `requirements.txt`, `app/` e o `railway.json`).
   - O **Start Command** já vem do `railway.json`
     (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`). Não precisa mexer.
4. **Settings → Networking → Generate Domain** para criar a URL pública
   (algo como `https://boris.semente.dev`).
5. Aguarde o deploy. Teste no navegador:
   `https://SEU-APP.up.railway.app/api/health` → deve responder `{"ok":true}`.

Cada `git push` refaz o deploy automaticamente.

---

## Opção B — Deploy pela CLI (sem GitHub)

```bash
# instala a CLI (precisa de Node) e faz login
npm i -g @railway/cli
railway login

# a partir da PASTA server (para o build context ser o backend)
cd b3-agente/server
railway init            # cria o projeto
railway up              # builda e publica esta pasta
railway domain          # gera a URL publica
```

Teste: `https://SEU-APP.up.railway.app/api/health`.

---

## Apontar o app do iPhone para o Railway

Como o endereço do servidor é configurável no app (a partir da versão com o
campo "Servidor do app"), **não precisa recompilar**:

1. Abra o app no iPhone → aba **Config** → seção **"Servidor do app (Mac)"**.
2. Coloque a URL do Railway, com `https://`:
   `https://SEU-APP.up.railway.app`
3. Toque **Testar conexão** → deve dar "Servidor respondeu OK."
4. Pronto: cotações e análises passam a vir do Railway, de qualquer rede.

Se ainda não tiver esse campo no app, refaça o build apontando o valor inicial:
```bash
bash scripts/setup-ios.sh --api-base https://SEU-APP.up.railway.app
```

> HTTPS resolve o bloqueio de rede do iOS (ATS): com a URL do Railway não é mais
> necessária a liberação de HTTP local que o `ios-allow-http.sh` faz para uso na
> LAN.

---

## Variáveis de ambiente (opcional)

Em **Settings → Variables** do serviço:

- `B3_AGENTE_API_KEY` (ou `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY`)
  — só é necessária se você quiser que o **servidor** tenha a chave (caso da
  versão **web** servida pelo próprio backend). Para o **app do iPhone** não
  precisa: o telefone envia a config + chave a cada análise.
- `B3_DB_PATH` — caminho do banco SQLite. Só importa para a persistência da
  versão **web**. Se quiser que ela sobreviva a novos deploys, crie um
  **Volume** (Settings → Volumes) montado, por ex., em `/data`, e defina
  `B3_DB_PATH=/data/b3_agente.db`. Para o uso no iPhone, pode ignorar.
- **Passada intraday** (ADR-001 item 7; defaults já são os valores medidos —
  só defina para AJUSTAR):
  - `B3_INTRADAY_OFF=1` — kill switch próprio (não desliga o Operador);
  - `B3_INTRADAY_GAP_S` — gap mínimo entre passadas, em s (default 240;
    envelope 60–3600);
  - `B3_INTRADAY_CONC` — requisições simultâneas ao provedor (default 8;
    envelope 1–16);
  - `B3_INTRADAY_PERIOD` — janela buscada (`1mo` default | `5d`; fora da
    matriz legal do ADR-002 cai no default com log).
  - O intervalo (15m) é CANÔNICO (ADR-002 Decisão 5) e não tem variável.
- **`B3_GATED_HOSTS`** (F4 completo, 2026-08-02) — domínios (separados por
  vírgula) onde o cadastro é OBRIGATÓRIO (sem modo convidado). Vazio por
  default: ninguém é afetado. Ex.: `B3_GATED_HOSTS=acamerini.app`. A URL do
  Railway e o app iOS NUNCA entram nessa lista — continuam com o modo
  convidado, é por isso que a variável precisa ser explícita e não um
  comportamento automático do domínio custom.
- **`B3_ADMIN_EMAILS`** — quem vê `/api/obs/logs`, `/api/obs/usage` e o painel
  de admin (F5, `/api/admin/summary`). Lista separada por vírgula; sem a env,
  só a PRIMEIRA conta criada no banco é admin.

> **Cuidado com o NOME da variável**: em 2026-08-01 uma `B3_MANAGED_LLM_KEY `
> (com espaço no fim) ficou meses no Railway sem nunca ser lida — a IA
> gerenciada parecia configurada e estava desligada. O servidor agora loga no
> boot qualquer variável `B3_*`/`APNS_*` com espaço no nome.

> **Plano**: a conta do Railway é o plano pago de **US$ 20/mês** (não é free
> tier/trial) — o container 24/7, o volume e o egress são cobertos por essa
> franquia de uso; os números de custo incremental do intraday (ver
> `docs/MEDICAO-Yahoo-Intraday-2026-07-30.md`) valem como uso adicional.

---

## Build mais enxuto (opcional)

O `requirements.txt` inclui o `pytest` (para testes locais). Em produção isso só
deixa o build um pouco mais lento. Se quiser, no Railway defina a variável
`NIXPACKS_INSTALL_CMD` para usar o arquivo só‑de‑produção:

```
NIXPACKS_INSTALL_CMD=pip install -r requirements-prod.txt
```

---

## Atenção: cotações no Railway (Yahoo)

As cotações vêm do Yahoo Finance. A partir de servidores de nuvem, o Yahoo às
vezes bloqueia/limita o IP (HTTP 401/403/429) com mais rigor do que numa conexão
residencial. O backend já tem mitigação (cookie + crumb + retry), mas pode ser
que, do Railway, as cotações falhem de vez em quando.

Se isso acontecer com frequência, o caminho é trocar a fonte de cotações por um
provedor com chave (ex.: brapi.dev). Se precisar, peça que eu adapto o
`server/app/yahoo.py` para usar esse provedor — a análise da IA não muda.
