---
quick_id: 260926-uhl
slug: fixa-social-login-8-3-34-cherry-pick-ac2
date: 2026-09-26
phase: quick-260926-uhl
plan: 01
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [QUICK-260926-uhl]
files_modified:
  - web/package.json
  - web/package-lock.json
  - .planning/STATE.md
  - .planning/PROJECT.md

must_haves:
  truths:
    - "@capgo/capacitor-social-login resolve para ^8.3.34 em web/package.json e web/package-lock.json (nunca mais 'latest')"
    - "Suíte canônica (pytest + .mjs) roda fora do sandbox e bate a baseline (3050 pytest passed / 5 skipped / 3 xfailed; 165/165 .mjs) ou qualquer divergência é explicada, não escondida"
    - "web/vite build passa limpo (sem erro de sintaxe JS)"
    - "STATE.md e PROJECT.md refletem que borisv2 é repositório independente desde 2026-09-26, sem o aviso antigo de que arquivar a pasta 'antigo' quebra o worktree"
  artifacts:
    - path: "web/package.json"
      provides: "dependency pin ^8.3.34"
    - path: "web/package-lock.json"
      provides: "lockfile alinhado ao pin e à version 2.0.0"
    - path: ".planning/STATE.md"
      provides: "Current Position atualizado + linha nova em Quick Tasks Completed"
    - path: ".planning/PROJECT.md"
      provides: "linha da tabela Key Decisions sobre o worktree borisv2 marcada resolvida"
  key_links:
    - from: "web/package.json"
      to: "web/package-lock.json"
      via: "npm dependency resolution"
      pattern: "8\\.3\\.34"
---

<objective>
Cherry-pick o commit `ac20a9c` (fixa `@capgo/capacitor-social-login` em `^8.3.34`, evitando que `npm install` puxe major nova do plugin de login Apple/Google) para o branch atual `v2/interacao-estrutural`, validar com a suíte canônica, e documentar à mão que o repositório `borisv2` virou independente em 2026-09-26 (não depende mais da pasta antiga `bolsia=boris antigo/b3-agente`).

Purpose: fechar o gap de manifest entre o commit isolado que só existia na pasta antiga/branch órfão e o histórico atual do borisv2, e eliminar o aviso desatualizado em STATE.md/PROJECT.md de que arquivar a pasta antiga quebraria este repo — isso não é mais verdade, borisv2 tem `.git` próprio e `origin` próprio.
Output: `web/package.json`/`web/package-lock.json` com o pin aplicado, commitado; STATE.md e PROJECT.md atualizados à mão com Edit (nunca via mutadores `gsd-sdk state.*`/`milestone.*`/`roadmap.*`) — commit dos docs fica a cargo do orquestrador, não deste plano.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/PROJECT.md
@CLAUDE.md

Commit a cherry-pick: `ac20a9cff8924f9bf3395496b8b588d36de5bf34` (existe localmente e em `origin/arquivo/main-bolsia-antigo`, a7358e4).
Mensagem original: "chore(web): fixa @capgo/capacitor-social-login em ^8.3.34 (era latest)" com `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
Diff do commit: `web/package.json` dependency `"@capgo/capacitor-social-login": "latest"` → `"^8.3.34"`; `web/package-lock.json` root `"version"` `1.0.0`→`2.0.0` (top-level e `packages[""]`) e a mesma dependência em `packages[""].dependencies`.

web/package.json atual já tem `"version": "2.0.0"` (não muda desde o commit original) — o cherry-pick da lockfile version deve ser um no-op ou aplicar limpo.

Fatos confirmados por inspeção (`git remote -v`, `git worktree list`, `origin/arquivo/*`) para a Task 3:
- `origin` já aponta para `https://github.com/AlexandreCamerini/b3agente.git`.
- `git worktree list` mostra só este próprio repo — não há mais vínculo de worktree com a pasta antiga.
- borisv2 foi criado via `git clone --mirror --no-hardlinks` do repo antigo, sem `alternates`, `core.bare=false`.
- A pasta antiga (`/Users/acamerini/dev/bolsia=boris antigo/b3-agente`) teve a entrada de worktree removida (metadata dir deletado + `git worktree prune`, que também limpou uma entrada órfã stale `zen-nightingale-492c64`).
- Dados local-only do repo antigo preservados no GitHub: `origin/arquivo/main-bolsia-antigo` (`a7358e4` — inclui `ac20a9c` e um commit docs da quick task `260923-fst`, este ÚLTIMO **não** trazido porque conflita com o STATE.md atual) e `origin/arquivo/stash-pre-gateway` (`0f7f79b`).
- Conclusão: a pasta antiga pode ser arquivada/apagada sem afetar borisv2. Únicos itens dela que valem checagem pelo Alex antes de apagar (não ler `.env`): `web/.env-local` (untracked) e `.claude/skills/swiftui-pro` (untracked).

STATE.md `## Current Position`, bloco "Ambiente:" ATUAL a substituir:
```
Ambiente: o repo principal foi renomeado para `/Users/acamerini/dev/bolsia=boris antigo/b3-agente`;
  o worktree `borisv2` foi reparado com `git worktree repair` em 2026-09-26.
  Arquivar/apagar essa pasta quebra o borisv2 — converter em clone
  independente antes disso.
```

PROJECT.md linha 671 (Key Decisions table), coluna "Outcome" ATUAL a substituir:
```
⚠️ Revisit — reparado com `git worktree repair` em 2026-09-26; se a pasta "antigo" for arquivada/apagada, o borisv2 perde o repositório — converter em clone independente antes disso
```
</context>

<tasks>

<task type="auto">
  <name>Task 1: Cherry-pick ac20a9c e validar o manifest</name>
  <files>web/package.json, web/package-lock.json</files>
  <action>
  A partir de `/Users/acamerini/dev/borisv2` (branch `v2/interacao-estrutural`, working tree limpo), rode `git cherry-pick -x ac20a9cff8924f9bf3395496b8b588d36de5bf34`. O `-x` preserva a referência ao commit original na mensagem; a mensagem original já traz o `Co-Authored-By` correto — não adicionar outro.

  Se o cherry-pick aplicar limpo: confirme que `web/package.json` tem `"@capgo/capacitor-social-login": "^8.3.34"` e que `web/package-lock.json` tem a mesma string em `packages[""].dependencies` e `"version": "2.0.0"` tanto no topo quanto em `packages[""]`.

  Se houver conflito (esperado se HEAD já divergiu da lockfile do commit original em outros campos): resolva SEMPRE alinhando ao `web/package.json` ATUAL — nunca mude o campo `"version"` público do `package.json` em si (isso é rótulo de release, não gerenciado por este cherry-pick). No lockfile, aplique apenas a troca de spec de dependência (`latest`→`^8.3.34`) e o alinhamento de `version` do lock com o `package.json` vigente; preserve qualquer outra entrada do lockfile que tenha mudado desde `ac20a9c`. Depois de resolver, `git add` os dois arquivos e `git cherry-pick --continue` (sem editar a mensagem além do que o `-x` já gerou).

  NÃO rode `npm install` de rede ampla neste passo — o objetivo é só o pin do manifest, `node_modules` já tem 8.3.34 instalado.
  </action>
  <verify>
    <automated>cd web && npm ls @capgo/capacitor-social-login 2>&1 | grep -q '8\.3\.34' && echo OK_RESOLVED</automated>
  </verify>
  <done>Commit criado no branch atual com o pin `^8.3.34` em package.json e package-lock.json; `npm ls @capgo/capacitor-social-login` mostra 8.3.34 resolvido sem UNMET; se `npm install --package-lock-only --ignore-scripts` puder rodar (rede disponível), roda sem gerar diff — caso falhe por rede, confirmar por inspeção do lockfile e anotar no SUMMARY que a checagem foi só por inspeção.</done>
</task>

<task type="auto">
  <name>Task 2: Validar suíte canônica e build</name>
  <files>(nenhum arquivo modificado — validação apenas)</files>
  <action>
  Rode `bash scripts/executar.sh --testes` FORA do sandbox (`dangerouslyDisableSandbox: true`) — a suíte pytest tem ~27 falhas dentro do sandbox por um artefato de TLS, não relacionadas a este cherry-pick. Compare contra a baseline do fechamento do milestone v1.8: 3050 pytest passed / 5 skipped / 3 xfailed / 0 failed + 165/165 `.mjs`.

  Em seguida rode `cd web && npx vite build` (grep/teste estático não pega erro de sintaxe JS — build real é obrigatório quando o front é tocado, mesmo que a mudança aqui seja só de manifest/lockfile).

  Se os números baterem com a baseline: nenhuma ação adicional. Se divergirem, investigue e relate a causa no SUMMARY — não ignore silenciosamente.

  Não publicar: sem `scripts/bump.sh`, sem `publicar-web.sh` — mudança de manifest sem efeito de runtime, dispensa deploy.
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && bash scripts/executar.sh --testes 2>&1 | tail -30</automated>
  </verify>
  <done>Suíte canônica bate a baseline (3050/5/3/0 pytest + 165/165 .mjs) rodada fora do sandbox; `npx vite build` conclui sem erro.</done>
</task>

<task type="auto">
  <name>Task 3: Registrar à mão a independência do borisv2 em STATE.md e PROJECT.md</name>
  <files>.planning/STATE.md, .planning/PROJECT.md</files>
  <action>
  Use a ferramenta Edit (NUNCA `gsd-sdk state.*`/`milestone.*`/`roadmap.*` — guardrail deste repo, ver CLAUDE.md) para dois edits pontuais:

  Em `.planning/STATE.md`, seção `## Current Position`, substitua o bloco "Ambiente:" atual (que fala em worktree reparado e risco de arquivar a pasta antiga) por um texto que registre: em 2026-09-26 borisv2 virou repositório independente — `.git` próprio criado via `git clone --mirror --no-hardlinks` do repo antigo (sem alternates, `core.bare=false`), `origin` = `https://github.com/AlexandreCamerini/b3agente.git`; removido da lista de worktrees da pasta antiga (`/Users/acamerini/dev/bolsia=boris antigo/b3-agente`, metadata deletada + `git worktree prune`, que também limpou a entrada órfã stale `zen-nightingale-492c64`); dados local-only do repo antigo preservados em `origin/arquivo/main-bolsia-antigo` (`a7358e4`, inclui `ac20a9c`; o commit docs da quick task `260923-fst` nesse branch NÃO foi trazido — conflita com o STATE.md atual) e `origin/arquivo/stash-pre-gateway` (`0f7f79b`); a pasta antiga agora pode ser arquivada/apagada sem afetar borisv2 — só vale o Alex checar antes `web/.env-local` e `.claude/skills/swiftui-pro` (untracked na pasta antiga, não ler `.env`).

  Adicione uma linha nova em "### Quick Tasks Completed" (mesma tabela, mesmas 6 colunas #/Description/Date/Commit/Status/Directory das linhas existentes) para a quick task `260926-uhl`: descrição cobrindo cherry-pick do pin `^8.3.34` (`ac20a9c`) + registro da independência do borisv2; data 2026-09-26; commit do cherry-pick (hash da Task 1); status conforme resultado das Tasks 1-2 (`Verified` se suíte bateu a baseline); coluna Directory com o link relativo padrão `[260926-uhl](./quick/260926-uhl-fixa-social-login-8-3-34-cherry-pick-ac2/)`, igual ao formato de todas as linhas anteriores.

  Em `.planning/PROJECT.md`, tabela "Key Decisions", localize a linha que começa com "Worktree `borisv2` ficou órfão..." e troque a coluna Outcome de `⚠️ Revisit — ...` para `✓ Good — risco eliminado em 2026-09-26: borisv2 convertido em repositório independente (clone --mirror, origin próprio, dados antigos preservados em origin/arquivo/*); pasta antiga pode ser arquivada/apagada sem quebrar este repo`. Mantenha as colunas Decision/Reasoning intocadas — só o Outcome muda.

  Verifique com `git diff .planning/STATE.md .planning/PROJECT.md` que só os blocos pretendidos mudaram, antes de finalizar (não commitar — o commit destes dois arquivos fica a cargo do orquestrador, por constraint deste plano).
  </action>
  <verify>
    <automated>cd /Users/acamerini/dev/borisv2 && git diff --stat .planning/STATE.md .planning/PROJECT.md | grep -E "STATE\.md|PROJECT\.md"</automated>
  </verify>
  <done>STATE.md sem mais o aviso "Arquivar/apagar essa pasta quebra o borisv2"; nova linha em Quick Tasks Completed para 260926-uhl; PROJECT.md com o Outcome da linha do worktree órfão trocado para `✓ Good` explicando a independência; nenhum commit criado para estes dois arquivos (fica para o orquestrador).</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| npm registry → node_modules/lockfile | dependency de terceiro (`@capgo/capacitor-social-login`) usada para login Apple/Google no app nativo |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-quick-01 | Tampering | web/package.json dependency spec | mitigate | pin `^8.3.34` em vez de `latest` — impede que um `npm install` futuro puxe uma major nova não auditada do plugin de login nativo sem revisão explícita |
| T-quick-02 | Tampering | cherry-pick de commit externo (branch órfão) | accept | commit já existe no histórico do próprio repo (object local) e em `origin/arquivo/main-bolsia-antigo`; mesmo autor (Alexandre Camerini), sem código novo de terceiro introduzido — só edição de manifest |
</threat_model>

<verification>
1. `cd web && npm ls @capgo/capacitor-social-login` mostra `8.3.34` (não `UNMET DEPENDENCY`, não outra versão).
2. `git log -1 --format=%H` no branch atual mostra o novo commit do cherry-pick, com `ac20a9c` referenciado via `(cherry picked from commit ...)` na mensagem (efeito do `-x`).
3. `bash scripts/executar.sh --testes` fora do sandbox bate a baseline 3050/5/3/0 + 165/165.
4. `cd web && npx vite build` conclui sem erro.
5. `git diff .planning/STATE.md .planning/PROJECT.md` mostra a substituição do aviso "arquivar quebra o borisv2" pelo novo estado de repo independente, e a nova linha em Quick Tasks Completed — sem esses dois arquivos commitados ainda (fica para o orquestrador).
</verification>

<success_criteria>
- Cherry-pick aplicado e commitado no branch `v2/interacao-estrutural`, sem alterar o `version` público de `web/package.json`.
- Dependência resolvida em `^8.3.34` em package.json e lockfile.
- Suíte canônica (pytest + .mjs) e `vite build` verdes, rodados fora do sandbox.
- Nenhuma publicação/deploy disparado (mudança de manifest, sem efeito de runtime).
- STATE.md `## Current Position` (bloco "Ambiente:") e "### Quick Tasks Completed" atualizados à mão via Edit — NUNCA via `gsd-sdk state.*`/`milestone.*`/`roadmap.*`.
- PROJECT.md Key Decisions table: linha do worktree órfão com outcome `✓ Good` explicando a conversão em repo independente em 2026-09-26.
- Docs (STATE.md, PROJECT.md) editados mas não commitados por este plano — commit é do orquestrador.
</success_criteria>

<output>
Create `.planning/quick/260926-uhl-fixa-social-login-8-3-34-cherry-pick-ac2/260926-uhl-SUMMARY.md` when done.
</output>
