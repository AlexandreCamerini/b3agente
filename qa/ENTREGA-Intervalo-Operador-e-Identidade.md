# Entrega — Intervalo do ciclo do Operador (configurável) + início da identidade

> As alterações **já estão aplicadas no seu clone** (esta sessão editou os arquivos reais). Este documento é o checkout: o que mudou, como validar e como publicar.

## O que foi feito

### 1) Intervalo do ciclo do Operador IA — configurável por usuário (ponta a ponta)
O backend já tinha o campo `agent.intervalMin` (persistido, clamp 1–240, default **15**), mas **ninguém o consumia**: o `scheduler_loop` rodava o ciclo de TODOS os usuários a cada passada da cadência base. Agora cada conta escolhe a frequência.

- **`server/app/agent.py`**
  - `agent_params()` passou a expor `intervalMin` (default 15, clamp 1–240).
  - Novo dict de módulo `LAST_USER_RUN` (epoch da última passada efetiva por usuário).
  - `scheduler_loop`: **gate por usuário** — em cada passada da cadência base, só roda o ciclo de um usuário se já passou o `intervalMin` DELE. A cadência base (`B3_AGENT_INTERVAL_S`, default 300s) não mudou; ela vira a granularidade mínima.
- **`web/src/persistence.js`** — `intervalMin` adicionado ao `SERVER_KEYS` do `deviceStore.putAgent` (antes era descartado no iOS).
- **`web/src/App.jsx`** (`AgenteScreen`) — controle segmentado **5 / 15 / 30 / 60 min** que salva via `putAgent({ intervalMin })`.

> **Atenção (comportamento):** hoje o laço reavalia cada usuário a ~5 min (cadência base). Passando a honrar o `intervalMin`, o **default vira 15 min** (valor já definido em `defaults.py`). Quem quiser 5 min escolhe no controle; para mudar o *default* global, ajuste `intervalMin` em `server/app/defaults.py`. Se quiser que eu troque o default, é uma linha.

### 2) Identidade — início da implementação do modelo aprovado (mock v2)
- **Estudo deixou de rodar o azul genérico.** `PALETTE` (App.jsx): acento do Estudo → **âmbar** (`#f0b429` dark / `#b45309` light) + `accentTint`/`onAccent` coerentes. Operador segue verde. A **marca** (LogoMark + wordmark "IA") continua azul→ciano fixa.
- **Badge simétrico + reposicionado.** `copy.js`: `estudo.chipModo = "MODO ESTUDO"` (antes `null`). `Topbar` (App.jsx): o badge saiu de ao lado do wordmark (apertado contra o patrimônio) e virou uma **linha de modo** sob a marca — ponto na cor do modo (halo `accentTint`) + rótulo + nome.

> As demais telas do modelo (hero-carrossel na home, anel de confluência, curva com área, sparkline na watchlist, tiles no Perfil, histórico/leitura-IA como pontos de acesso) são o **próximo conjunto de patches** — restruturam a camada de view e vão em passos validados, como de praxe.

### Testes atualizados (design mudou → guardião muda)
- `web/tests/test_mode_badge_outlined.mjs` — reescrito para o novo badge (linha de modo, não pill).
- `web/tests/test_copy_theme.mjs` — asserção R3 e "chip no Topbar" atualizadas para o novo markup.

## Validação executada nesta sessão
- `py_compile` de todo `server/app/*.py` — OK.
- Lógica nova do gate + `agent_params` (default 15, clamp, elegibilidade por tempo) — asserts OK.
- **30/30** suítes `web/tests/*.mjs` — PASS.
- `node --check` + parse JSX (TypeScript) de `App.jsx`, `persistence.js`, `copy.js` — OK.
- **Pendente no seu Mac:** `cd server && pytest` (a `.venv` é macOS; o sandbox não roda pytest).

## Publicar
1. **`server/` mudou** → `./scripts/atualizar-servidor.sh` (Railway redeploy).
2. **`web/src/` mudou** → `./scripts/instalar-iphone.sh` (build Capacitor + instalar no device).
3. Rodar `pytest` no `server/` antes do push.
4. **Hard stop físico no iPhone**: abrir Operador IA, trocar o intervalo (5/15/30/60), confirmar persistência; conferir o novo badge/linha de modo e o acento âmbar do Estudo nos dois temas.
