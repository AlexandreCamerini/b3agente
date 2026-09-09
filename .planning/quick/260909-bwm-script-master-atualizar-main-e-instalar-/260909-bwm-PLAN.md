---
quick_id: 260909-bwm
description: script master — atualizar main e instalar no iPhone, escolhendo Xcode ou TestFlight na hora
date: 2026-09-09
status: executing
---

# Quick 260909-bwm — script master de distribuição iOS

## Pedido

"Script master que execute todos os comandos necessários para atualizar a
última versão e instalar. Na hora da instalação eu escolher se será
distribuído pelo Xcode ou TestFlight."

## Restrição concreta descoberta (não hipótese)

`main` está com checkout permanente em `/Users/acamerini/dev/bolsia/b3-agente`
(`git worktree list`). Este worktree (`borisv2`, branch
`v2/interacao-estrutural`) NÃO PODE dar `git checkout main` — o git recusa
("already used by worktree"), erro já visto ao vivo nesta sessão ao rodar
`promover-staging-para-producao.sh`. Confirmado agora: `main` local está
LIMPO (só um `??` inofensivo, `.claude/skills/swiftui-pro`) e ATRÁS de
`origin/main` (`a266c3a` → `a4a9446`) — a atualização vai ter efeito real na
primeira execução.

Decisão: o script master localiza o worktree com `main` via
`git worktree list --porcelain`, faz `cd` para lá, e opera de dentro dele
(fetch + `merge --ff-only`, nunca merge/rebase automático — diverge → morre
com instrução). Se algum dia rodar num repo de checkout único sem essa
restrição, cai no caminho simples (`git checkout main` in place).

## Desenho (reaproveita os scripts existentes — não duplica lógica)

Nome: `scripts/distribuir-iphone.sh` (verbo bate com o pedido: "distribuído
pelo Xcode ou TestFlight" é literal do usuário).

Fluxo:
1. Localizar o worktree com `main` (ou usar o atual, se já for `main`).
2. `git fetch origin` + `merge --ff-only origin/main` — morre com instrução
   clara em qualquer divergência; NUNCA merge/rebase/reset automático.
3. Suíte canônica no worktree de `main` (`bash scripts/executar.sh --testes`)
   — escapável via `--skip-testes`. Pega `main` quebrado ANTES de empacotar
   pro Xcode/TestFlight, não depois.
4. `bash scripts/instalar-iphone.sh --no-open` (flag NOVA, ver abaixo) —
   builda contra PRODUÇÃO (default do próprio script; distribuição nunca
   aponta pra staging por decisão de escopo), instala deps, gera ícone,
   `cap sync`, restaura entitlements/AppDelegate. Passa `--recriar-ios` se o
   usuário pedir (única flag repassada; `--staging`/`--api-base` propositalmente
   NÃO expostos aqui — script de DISTRIBUIÇÃO não deveria nem oferecer apontar
   pra staging por acidente).
5. Escolha do canal — flags `--xcode`/`--testflight` pulam o prompt; sem
   flag, `read` interativo (script é de terminal, não de agente).
   - **Xcode**: abre o projeto (`cap open ios`, mesmo fallback do
     `instalar-iphone.sh`) e imprime as mesmas instruções de Run direto no
     aparelho.
   - **TestFlight**: `bash scripts/ios-testflight.sh` (manifesto + export
     compliance; NÃO toca `--apns-prod` — isso é coordenado com o Railway,
     ação separada e explícita, nunca automática aqui) → `bash
     scripts/ios-bump-build.sh` (+1) → abre o Xcode com instruções de
     Archive → Distribute App → App Store Connect.
6. Resumo final SEMPRE impresso, com o que importa saber antes de instalar
   num aparelho real: backend embutido, versão/build, e o `aps-environment`
   ATUAL lido do entitlement (não assumido) — se for `development` e o canal
   escolhido for TestFlight, avisa explicitamente que push NÃO vai funcionar
   até coordenar com o Railway (gap real, encontrado ao vivo nesta sessão
   ontem).

## Mudança cirúrgica em `instalar-iphone.sh`

Adicionar `--no-open`: pula SÓ o passo 8 (abrir Xcode + bloco de instruções
de Run direto). Sem a flag, comportamento 100% preservado (uso direto do
script continua igual). Necessário para o master poder decidir DEPOIS do
build qual Xcode abrir e com qual instrução — sem isso o Xcode abriria duas
vezes, ou abriria com a instrução errada antes do TestFlight rodar.

## Fora de escopo

- Flip de APNs para produção (`--apns-prod`) — ação coordenada com o Railway,
  fica manual e explícita, nunca dentro de um script "instalar".
- Upload automatizado ao App Store Connect (Archive/Distribute é GUI do
  Xcode; não existe CLI oficial suportada por este projeto).
- `web/.env.local` (login Google) — script avisa se ausente (mesma frase que
  `instalar-iphone.sh` já imprime), não cria.

## Validação

- `bash -n` nos dois scripts (sintaxe).
- Dry-run real: rodar `distribuir-iphone.sh --skip-testes --xcode` de dentro
  do worktree `borisv2` (branch feature) e confirmar que ele efetivamente
  `cd`a para `/Users/acamerini/dev/bolsia/b3-agente`, faz o fast-forward,
  builda, sincroniza e abre o Xcode — sem tocar em `git checkout main` no
  worktree errado.
- Sem suíte automatizada para scripts shell neste repo (nenhum precedente em
  `server/tests`/`web/tests` cobre `scripts/*.sh`) — consistente com o
  restante do diretório.
