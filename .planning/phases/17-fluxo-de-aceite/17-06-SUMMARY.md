---
status: incomplete
plan: 17-06
---

# Summary — Task 1: bump do carimbo e publicação do front

**Carimbo gerado:** `F10-20260903-01` (anterior: `F10-20260831-02`).

## O que foi feito

1. `bash scripts/bump.sh` — sem argumento, próximo carimbo do dia.
2. `bash scripts/publicar-web.sh` — build (`npm ci` + `vite build`) e publicação
   em `server/web_dist`. `npm ci` falhou dentro do sandbox padrão (`EPERM`
   tentando apagar `node_modules/xmlbuilder/.vscode/launch.json` — falha de
   permissão do sandbox, não do projeto); rerodado com sandbox desabilitado,
   sucesso.
3. `bash scripts/executar.sh --testes` — rodado DEPOIS da publicação, com
   sandbox desabilitado (mesma razão): **2010 passed, 1 skipped** (backend) +
   todas as suítes `web/tests/*.mjs` OK, incluindo os guardiões de
   carimbo/bundle e os testes novos desta fase
   (`test_opcoes_collar_ui.mjs`, `test_opcoes_proposta_ui.mjs`,
   `test_opcoes_lastreadas_stores.mjs`). Exit 0.
4. Confirmado manualmente: `web/src/version.js` tem `BUILD_ID =
   "F10-20260903-01"`; o mesmo carimbo aparece literal dentro de
   `server/web_dist/assets/index-DeOKn4JS.js`; `git status --porcelain`
   mostra `server/web_dist` genuinamente trocado (assets antigos removidos,
   novos adicionados) e `server/app/main.py` com o `SERVER_BUILD_ID`
   sincronizado.

## Acceptance criteria

- [x] `git diff web/src/version.js` mostra um `BUILD_ID` novo
- [x] `git status --porcelain server/web_dist` não vazio
- [x] `bash scripts/executar.sh --testes` verde depois da publicação
- [x] Carimbo em `server/web_dist` bate com `web/src/version.js`

## Task 2 — checkpoint humano bloqueante

**ADIADO, não aprovado — decisão explícita do Alex.** O app local foi subido
(`api`/`web` via `.claude/launch.json`, sem erro nos dois), mas o mercado
estava fechado no momento da tentativa — cadeia de opções ao vivo
indisponível pra exercitar o roteiro de verificação (payoff real, collar
ofertado por caixa insuficiente, aceite/cancelamento, Radar vs. Watchlist,
iPhone). Alex instruiu explicitamente: "não consigo testar isso pq o
mercado está fechado. siga para a próxima fase".

**Isso NÃO é aprovação — é adiamento com risco aceito conscientemente.**
Registrado como `verification_gap: human_needed`, mesmo padrão já usado no
histórico do projeto (ex.: item 8 do checkpoint 08-05 sobre `entradaAuto`,
2 human-checks da Fase 3) — ver `.planning/STATE.md` seção "Blockers/Concerns"
e `PROJECT.md` Active. `status: incomplete` neste frontmatter permanece —
não deve virar `complete`/`passed` sem a verificação ao vivo de fato
acontecer, mesmo que o trabalho de código siga para a Fase 18. Push da Fase
17 pra origin segue não feito nesta sessão (só commits locais).

## Nota operacional

Os dois comandos que falharam dentro do sandbox padrão (`npm ci`,
`executar.sh --testes`) falharam por restrição de escrita/rede do sandbox
(`EPERM` em ambos os casos, mesma causa-raiz), não por problema no código ou
nos scripts — confirmado rodando fora do sandbox com sucesso limpo.
