# CHECKOUT — Racionalização de design + Operador (versão FINAL desta sessão)

> Handoff para um chat novo. Comece lendo este arquivo + `CLAUDE.md` + `qa/AUDITORIA-Design-System-v1.md`.
> Todas as mudanças abaixo **já estão aplicadas no clone** e validadas.

## Estado final
- **BUILD_ID atual:** `F9-20260709-13` (`web/src/version.js`). Se o app não mostrar isso no rodapé do Perfil, está rodando build antigo.
- **Raiz do Capacitor = `web/`** (`web/capacitor.config.ts`, `webDir: dist`). A plataforma iOS fica em **`web/ios`** (não na raiz do repo).
- **Publicar iOS (forma certa):** da raiz do repo, `bash scripts/instalar-iphone.sh` (faz `npm run build` → `npx cap sync ios` a partir de `web/` → abre o Xcode → Run no iPhone). Rodar `cap sync` de dentro de `web/ios` dá "ios platform has not been added yet".
- **Backend:** mudanças em `server/` vão ao Railway com `git push` + `./scripts/atualizar-servidor.sh`.

## O que foi implementado (mock aprovado `qa/mocks/racionalizacao-design-v2.html`)
Tudo em `web/src/App.jsx` salvo indicado:
1. **Tokens por modo:** Estudo agora **âmbar** (`#f0b429` dark / `#b45309` light); Operador segue verde. `copy.js`: `estudo.chipModo = "MODO ESTUDO"` (badge simétrico).
2. **Badge → linha de modo** sob o wordmark (ponto + rótulo), no lugar do pill apertado; **friso** de 3px no topo.
3. **Logo + "IA" do wordmark seguem o acento do modo** (`LogoMark` via `usePalette()`, `IA_GRAD` via `var(--accent)`) — não há mais azul fixo, exceto `TEAL`/`ORANGE` (cores semânticas de KPI, propositais).
4. **`ConfluenceRing`** (anel) no lugar da barra plana de confluência (Radar).
5. **`CapitalCurve`** com **área/gradiente** na cor do modo.
6. **Home = hero-carrossel** das melhores oportunidades da watchlist (confluência > 0, ordenado; aparece sempre que há setup). `destaque`/DeepModal/curva/streak/coach intactos.
7. **`Sparkline`** por card na Watchlist — data-layer: `server/app/scanner.py` emite `spark` (série compacta de ~32 fechamentos do snapshot).
8. **Perfil em tiles agrupados** (`ProfileTile`), preservando os 6 destinos (openAuth/config/ia/notificacoes/eficiencia/logs) + ModoTrabalhoCard.
9. **Operador IA — intervalo do ciclo configurável (5/15/30/60 min):** UI em `AgenteScreen`; `persistence.js` (`intervalMin` em `SERVER_KEYS`); `server/app/agent.py` (gate por usuário via `LAST_USER_RUN`, sem mudar a cadência base; `agent_params` expõe `intervalMin`, default 15). `server/app/store.py` já persistia o campo.

## Invariantes respeitados
- Nenhuma funcionalidade removida (histórico, análises de IA, controles do Operador — todos preservados).
- **Prompts de IA intactos:** `store.analyze` resolve prompt no servidor (default/custom via `llmPrompts`); `runStopAlvoFor` usa `carteiraStopAlvoOperador || carteiraStopAlvo`. Nenhuma dessas rotas foi tocada.
- Patches cirúrgicos; `persistence.js` estendido, nunca reescrito.

## Testes atualizados (design mudou → guardião mudou)
- `web/tests/test_mode_badge_outlined.mjs` — reescrito p/ a linha de modo.
- `web/tests/test_copy_theme.mjs` — asserções do chip/R3 atualizadas.

## Validação (nesta sessão)
- Parse JSX/JS (TypeScript) OK; **30/30** `web/tests/*.mjs`; `py_compile` de `server/app/*` OK; lógica do gate do intervalo conferida.
- **Pendente no Mac:** `cd server && pytest` (a `.venv` do sandbox é macOS; não roda no ambiente da sessão).

## Adiado / próximos
- `TEAL`/`ORANGE` (KPIs) poderiam virar mode-aware se quiser 100% de coerência.
- Fora de escopo desta frente: gamificação e paywall (trilhas separadas).
