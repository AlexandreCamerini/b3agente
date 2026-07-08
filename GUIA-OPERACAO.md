# GUIA DE OPERAÇÃO — BolsIA
*Para quem NÃO é desenvolvedor. Tudo em comandos únicos, na pasta do projeto.*

O BolsIA tem três "casas": o **código** (esta pasta, versionada no GitHub), o
**servidor** (Railway — roda o backend e o site) e o **app do iPhone**
(instalado pelo Xcode/TestFlight). Este guia cobre o dia a dia das três.

---

## 1. Instalar (uma vez por computador)

```bash
bash instalar.sh            # backend + web
bash instalar.sh --iphone   # cadeia do iPhone (build + abre o Xcode)
```

## 2. Rodar no seu Mac (desenvolvimento)

```bash
bash executar.sh            # liga tudo: backend :8787 + site :5173
bash executar.sh --stop     # desliga
```

## 3. Verificar se está tudo bem

```bash
bash operar.sh status       # servidor no ar? ambiente ok? commits pendentes?
bash operar.sh testes       # roda TODOS os testes (deve terminar sem falhas)
```

Regra de ouro: **nunca publique com teste falhando.**

## 4. Publicar uma atualização (deploy)

```bash
bash operar.sh testes                       # 1º: tudo verde
bash operar.sh deploy "o que mudou aqui"    # 2º: sobe pro GitHub + Railway
```

O Railway publica sozinho após o push (2–3 min). O próprio script confere a
saúde no final. Se o app do iPhone também mudou (o roteiro da entrega avisa),
rode `cd web && npm run ios` e instale pelo Xcode.

## 5. Backup dos dados

```bash
bash operar.sh backup       # cópia segura do banco local (mantém as 14 últimas)
```

No Railway, os dados vivem no volume `/data` (variável
`B3_DB_PATH=/data/b3_agente.db`). **Nunca remova esse volume** — é onde moram
as contas, carteiras e o cache que deixa o Radar rápido.

## 6. Ver os logs (o que o servidor está fazendo)

- **No app** (mais fácil): Perfil → Observabilidade → **"Logs do servidor"**.
  Cada linha mostra hora, categoria e o que houve; filtros "lentos+erros" e
  "só erros" vão direto ao problema. Só o admin vê (defina
  `B3_ADMIN_EMAILS=seu-email` no Railway; sem isso, só a primeira conta
  criada).
- **No Railway**: painel → serviço → Deployments → View Logs (mesmas linhas,
  formato `[b3][categoria] mensagem`).

Categorias: `req` (cada chamada, com duração) · `slow` (demorou >2s) · `err`
(erro não tratado) · `auth` (logins falhos, purga de sessões).

## 7. Problemas comuns

| Sintoma | O que fazer |
|---|---|
| Site/app não responde | `bash operar.sh status`; se o Railway caiu, veja View Logs e clique em Redeploy |
| App diz "Sem conexão com o servidor" | iPhone: Perfil → Conta & preferências → endereço do servidor → Testar conexão |
| Radar lento logo após publicar | Normal só na 1ª varredura de um ativo NOVO; se estiver lento sempre, confira o volume `/data` no Railway |
| Push não chega | Aba Operador IA → "Ativar push das ações" (deve dar "push ativo ✓"); depois Observabilidade → "Testar push agora" — a mensagem de erro diz exatamente o quê corrigir |
| "Muitas tentativas de login" | É a proteção contra ataques: aguarde 15 min (ou confira se alguém está tentando entrar na sua conta) |
| Esqueci o que mudou na última entrega | Leia `ATUALIZAR-Git-Railway-iOS.md` (sempre descreve a entrega atual) |

## 8. Mapa dos arquivos importantes

| Arquivo/pasta | O que é |
|---|---|
| `instalar.sh` / `executar.sh` / `operar.sh` / `atualizar.sh` | os 4 comandos do dia a dia |
| `server/` | backend (FastAPI + SQLite) |
| `web/` | app React (site + base do app iOS) |
| `web/ios/` | projeto Xcode do iPhone |
| `scripts/` | ferramentas específicas (backup, APNs, identidade…) |
| `qa/` | histórico de qualidade de cada fase |
| `GUIA-OPERACAO.md` | este guia |
| `LOGIN-SOCIAL.md` | passo a passo para ativar login Apple/Google |
| `DEPLOY_RAILWAY.md` | detalhes do servidor no Railway |
