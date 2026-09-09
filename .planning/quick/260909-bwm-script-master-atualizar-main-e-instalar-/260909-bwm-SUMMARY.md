---
quick_id: 260909-bwm
status: complete
date: 2026-09-09
files_modified:
  - scripts/distribuir-iphone.sh (novo)
  - scripts/instalar-iphone.sh
---

# Summary — 260909-bwm

## O que foi entregue

`scripts/distribuir-iphone.sh` — script master de distribuição iOS. Um
comando: atualiza `main`, roda a suíte canônica, builda contra produção,
sincroniza o projeto nativo e, na hora de instalar, pergunta o canal (Xcode
direto no aparelho, ou TestFlight/App Store Connect).

Mudança cirúrgica em `scripts/instalar-iphone.sh`: flag nova `--no-open` que
pula só o passo de abrir o Xcode + imprimir as instruções de Run — sem a
flag, comportamento 100% preservado. Necessária para o master decidir DEPOIS
do build qual Xcode abrir e com qual instrução (evita abrir o projeto duas
vezes, ou com a instrução errada, antes de rodar os passos de TestFlight).

## Restrição real que moldou o desenho

`main` tem checkout permanente noutro worktree deste repo
(`/Users/acamerini/dev/bolsia/b3-agente`) — este worktree (`borisv2`,
`v2/interacao-estrutural`) não pode dar `git checkout main` (o git recusa:
"already used by worktree", erro já visto ao vivo nesta sessão). O script
localiza esse worktree via `git worktree list --porcelain` e opera de dentro
dele; se rodar num repo de checkout único, cai no caminho simples (`git
checkout main` in place). Testado isoladamente: resolve para o caminho certo
a partir daqui.

## Decisões de escopo, e por quê

- **Nunca aponta pra staging.** `--staging`/`--api-base` do
  `instalar-iphone.sh` não são repassados — script de distribuição não
  deveria nem oferecer isso por acidente.
- **Nunca flipa APNs pra produção automaticamente.** É ação coordenada com o
  Railway (zerar `APNS_SANDBOX` do outro lado); o script só LÊ o
  `aps-environment` atual e avisa no resumo final se estiver em
  `development` com o canal TestFlight escolhido — é exatamente o gap real
  que apareceu ao vivo na conversa de ontem sobre TestFlight.
- **Suíte canônica antes de empacotar** (`--skip-testes` escapa). Pega
  `main` quebrado antes de gerar um build de distribuição, não depois.
- **`git merge --ff-only` só.** Diverge → morre com instrução; nunca
  merge/rebase/reset automático.
- **Upload ao App Store Connect continua manual** (Archive/Distribute é GUI
  do Xcode; não existe CLI oficial suportada por este projeto) — fora de
  escopo, documentado no cabeçalho.

## Validação

- `bash -n` nos dois scripts: sintaxe OK.
- Lógica de localização do worktree de `main` testada isoladamente (sem
  disparar build): resolve para `/Users/acamerini/dev/bolsia/b3-agente`, que
  é onde `main` de fato está.
- **Não executei o pipeline completo** (npm install + vite build + cap sync +
  abrir Xcode) — tem efeito real fora deste worktree e termina com um `read`
  interativo + abertura de GUI, que fazem sentido ao Alex rodar ele mesmo,
  não a este agente disparar sozinho. Confirmado que `main` está limpo e
  atrás de `origin/main` (`a266c3a` → `a4a9446`) — a primeira execução real
  vai ter efeito.
- Sem suíte automatizada para `scripts/*.sh` neste repo — consistente com o
  restante do diretório (nenhum teste em `server/tests`/`web/tests` cobre
  scripts shell).

## Como usar

```bash
bash scripts/distribuir-iphone.sh                # pergunta o canal
bash scripts/distribuir-iphone.sh --xcode        # sem perguntar
bash scripts/distribuir-iphone.sh --testflight   # sem perguntar
```
