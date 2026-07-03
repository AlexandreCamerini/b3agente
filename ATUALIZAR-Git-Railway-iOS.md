<<<<<<< HEAD
# ATUALIZAR — Git · Railway · iOS
**Entrega:** Fase 0 (proposta UX, gate) + Fase 1 (pipeline IA em 3 níveis, backend)
**Data:** 2026-07-02 · **Pré-requisito:** entrega anterior (fix SQLite threads) aplicada e validada.

## O que esta entrega contém
| Item | Arquivo(s) |
|---|---|
| Espec das análises (skill analise-tecnica-b3, determinístico × LLM) | `ESPEC-Analises-Tecnicas.md` |
| Proposta de UX ✋ GATE (aguarda sua aprovação) | `PROPOSTA-UX.md` |
| N1: deep scan do Radar | `server/app/scan_deep.py` (novo) + endpoints em `main.py` |
| N2: ADX/DI±, padrões de candle, famílias, dataQuality | `indicators.py`, `technical_models.py`, prompt em `llm.py` |
| N3: contexto técnico + cenários com memória de cálculo | `main.py` (stopalvo), `llm.py` |
| Testes novos (26) | `test_scan_deep.py`, `test_pipeline_n2_n3.py`, `test_guardrail_imperativo.py` |
| Estado e decisões (Apple paga → APNs liberado p/ F3) | `ESTADO-Fase0-Fase1-Pipeline-IA.md` |

**Frontend: INALTERADO** (a UI dos níveis entra na Fase 2, após o gate).
**iOS: nenhum passo nesta entrega** — sem plugin novo, sem `cap sync` necessário.

## PASSO ÚNICO — subir e validar o backend
```bash
./subir-git.sh   # ou git add -A && git commit -m "feat: pipeline IA 3 niveis (backend) + espec + proposta UX" && git push
```
Após o deploy (card verde), valide por API (Safari/terminal):
1. `GET /api/scan?period=6mo` → agora cada contexto de análise traz `families` e `dataQuality` (indireto).
2. `GET /api/scan/deep/estimate?period=6mo&topN=3` → `{topN, selecionados, novasChamadasIA, chamadas}`.
3. `POST /api/scan/deep` body `{"period":"6mo","topN":2}` (logado, gerenciada/BYOK) → leituras com `leituraSetups`, `cenarios`, `modelosUtilizados`; repetir a chamada → `cache: true` sem gastar cota.
4. `POST /api/carteira-stopalvo/PETR4` → resposta agora com `cenarios[3]` + `memoriaCalculo` (formato antigo continua aceito).

### ✋ HARD STOP — sua aprovação do PROPOSTA-UX.md
A Fase 2 (telas do flow oportunidade→carteira) e as migrações M1–M6 só
começam depois do seu OK (ou dos ajustes que pedir). A Fase 3 (agente
server-side + push/APNs) vem depois do hard stop de device da Fase 2.

## Validação executada antes do empacote
py_compile ✅ · suítes backend **111/111** ✅ · node --check ✅ · frontend
inalterado · grep de wiring ✅ · guardrail anti-imperativo ✅ (o teste
inclusive pegou e forçou o refinamento do próprio prompt durante o build).
<<<<<<< HEAD
=======

---

## NOVO — Scripts de um comando (raiz do projeto)

A partir desta entrega o fluxo inteiro tem três pontos de entrada:

| Comando | O que faz |
|---|---|
| `bash instalar.sh` | Ambiente local completo (venv+deps backend, npm web) e roda as suítes como prova. `--iphone` executa a cadeia completa do aparelho (build→sync→pod→Xcode); `--tudo` faz ambos. |
| `bash executar.sh` | Sobe DEV (backend :8787 + Vite :5173) com dica do endereço para o iPhone. Aceita `--prod`, `--stop`, `--status` e o novo `--testes` (só suítes). |
| `bash atualizar.sh files.zip "msg"` | **Aplica a entrega do Claude**: exige working tree limpa, extrai o b3-agente.zip, faz overlay aditivo protegendo `.git/ node_modules/ web/ios/ dist/ .venv/ data/ *.db`, valida (py_compile, node --check, suítes se houver venv) e só então deploya via `scripts/atualizar-servidor.sh`, verificando também `/api/scan/deep/estimate`. Flags: `--somente-aplicar` (sem git/deploy) e `--somente-deploy "msg"` (sem zip). |

Eles ORQUESTRAM os scripts existentes em `scripts/` (setup, run, test,
atualizar-servidor, instalar-iphone) — nada foi reescrito. **O fluxo de toda
entrega futura vira:** baixar o files.zip → `bash atualizar.sh ~/Downloads/files.zip "msg"`.
>>>>>>> 3ded4d0 (feat: pipeline IA 3 niveis (backend) + espec + proposta UX)
=======
# BolsIA — Guia definitivo: Git do zero · Railway passo a passo · iPhone
**Entrega:** suíte completa de scripts em `scripts/` (rebuild do repositório do
zero, instalação, execução e atualização — tudo por script).

---

## Os scripts (todos em `scripts/`)

| Script | Para quê |
|---|---|
| `verificar-arquivos.sh` | Confere o MANIFESTO completo (todos os arquivos que o app precisa) + sanidade do .gitignore e do deploy. Roda sozinho ou dentro dos outros. |
| `git-do-zero.sh` | **Reconstrói o repositório do zero e publica no GitHub.** Valida manifesto+código, `git init`, commit com tudo (protegendo node_modules/ios/dist/venv/data/db/env), remote e push. Flags: `--sem-push` (ensaio), `--recriar` (apaga o .git atual). |
| `instalar.sh` | Ambiente local (venv+deps backend, npm web) + suítes como prova. `--iphone` = cadeia do aparelho; `--tudo` = ambos. |
| `executar.sh` | DEV local (:8787 + :5173). Aceita `--prod`, `--stop`, `--status`, `--testes`. |
| `atualizar.sh` | Aplica um `files.zip` de entrega (overlay protegido + validação) e deploya. Flags: `--somente-aplicar`, `--somente-deploy "msg"`. |
| `atualizar-servidor.sh` · `instalar-iphone.sh` · `setup.sh` · `run.sh` · `test.sh` | Já existiam — os novos os orquestram. |

---

# PASSO A PASSO COMPLETO

## Etapa 0 — Pré-requisitos no Mac (uma vez)
```bash
xcode-select --install        # git + ferramentas
# Python 3.10+ (python.org ou brew install python)
# Node 18+ (nodejs.org ou brew install node)
```

## Etapa 1 — Instalar o ambiente
```bash
cd b3-agente
bash scripts/instalar.sh
```
Termina com as suítes verdes = ambiente são.

## Etapa 2 — Subir o Git DO ZERO
Antes: crie (ou confirme) o repositório **vazio** no GitHub
(github.com → New repository → `b3agente` → sem README).
Tenha um **Personal Access Token**: GitHub → Settings → Developer settings →
Personal access tokens → **Generate new token (classic)** → escopo `repo` →
copie o token (é a "senha" do push).
```bash
bash scripts/git-do-zero.sh
# ensaio sem publicar:        bash scripts/git-do-zero.sh --sem-push
# refazer apagando o .git:    bash scripts/git-do-zero.sh --recriar
# outro repositório:          bash scripts/git-do-zero.sh https://github.com/USUARIO/REPO.git
```
No prompt do push: **Username** = seu usuário · **Password** = o TOKEN (PAT).

## Etapa 3 — Railway do zero (uma vez, ~5 minutos)
1. https://railway.app → login → **New Project** → **Deploy from GitHub repo**
   → autorize e escolha `b3agente`.
2. Clique no card do serviço → **Settings**:
   - **Root Directory:** `server`  ← essencial (é onde estão `requirements.txt`,
     `app/` e o `railway.json`; o start command e o healthcheck vêm dele).
3. **Volume persistente** (sem isto o banco zera a cada deploy):
   botão direito no card do serviço → **Attach Volume** → **Mount Path:** `/data`.
4. **Variables** do serviço → **+ New Variable**:
   - `B3_DB_PATH` = `/data/b3.db`   (obrigatória — banco no volume)
   - `B3_AGENTE_API_KEY` = sua chave de IA (opcional — habilita a IA gerenciada)
   - `B3_SCAN_UNIVERSE` = `PETR4,VALE3,...` (opcional — universo do Radar sem redeploy)
5. **Settings → Networking → Generate Domain** → anote a URL
   (ex.: `https://b3agente-production.up.railway.app`).
6. Aguarde o deploy (card verde) e teste no navegador:
   - `SUA-URL/api/health` → `{"ok":true}`
   - `SUA-URL/api/scan?period=1mo&tickers=PETR4` → JSON do Radar
7. No iPhone: Perfil → Config → **endereço do servidor** = a URL do passo 5
   → **Testar conexão**.

## Etapa 4 — Atualizações do Railway (recorrente)
O Railway redeploya **sozinho a cada push**. Três formas de atualizar:
```bash
# A) entrega minha (files.zip): aplica + valida + commit + push + health
bash scripts/atualizar.sh ~/Downloads/files.zip "mensagem do commit"

# B) mudanças suas já no repo: só commit + push + health
bash scripts/atualizar.sh --somente-deploy "mensagem"

# C) manual, se preferir:
git add -A && git commit -m "mensagem" && git push
```
O script A/B espera o deploy e verifica `/api/scan` e `/api/scan/deep/estimate`
automaticamente. Para acompanhar/depurar no painel: card do serviço →
**Deployments** → deploy ativo → **View Logs** (filtre por `Traceback`).

## Etapa 5 — iPhone (quando o app/plugin mudar)
```bash
bash scripts/instalar.sh --iphone
```
No Xcode: Clean Build Folder (⇧⌘K) → rodar no aparelho → aceitar permissões.
(Backend mudou mas o app não? O iPhone não precisa de nada — ele fala com a
URL do Railway.)

---

## O que o repositório versiona (e o que nunca entra)
**Entra:** `server/` (código+testes+Procfile+railway.json+requirements),
`web/` (src, public, package.json, package-lock.json, vite, capacitor.config),
`scripts/`, documentos `.md`, `.gitignore`, `qa/`, `resources/`.
**Nunca entra (protegido pelo .gitignore e checado pelos scripts):**
`node_modules/`, `web/ios/` (gerado pelo Capacitor), `web/dist/`,
`server/.venv/`, `server/data/`, `*.db*`, `.env*`, logs.
`bash scripts/verificar-arquivos.sh` audita tudo isso a qualquer momento.
>>>>>>> 27ae2f3 (BolsIA — bootstrap do repositório (app completo: backend FastAPI + web React/Capacitor + scripts + testes))
