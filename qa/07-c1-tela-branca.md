# Etapa C1 — Blindagem contra tela branca (render crash)

## Problema (bug de LÓGICA, prioridade Crítica)
Doc de aparelho de versão antiga ou gravado pela metade podia não ter
`watchlist` / `positions` / `history` / `agent.events`. O render acessava esses
campos sem guarda (`data.watchlist.join`, `data.positions.reduce`,
`agent.events.map`), a exceção desmontava a árvore React e o usuário ficava com
**tela branca, sem recuperação**. Não havia Error Boundary no app.

## Correções (cirúrgicas, sem reescrever persistence.js)

### 1. `web/src/migrate.js` (NOVO) — módulo puro, sem imports nativos
`backfillStructural(doc, defaults)` garante a forma estrutural mínima:
config/agent/skill como objetos; watchlist/positions/history como arrays;
agent.events como array; cash como número (herda `initialBudget`).
Regra: **nunca fabrica** dados do usuário — positions/history ausentes viram
listas vazias (jamais as posições-demo). Não sobrescreve valores existentes.

### 2. `web/src/persistence.js` — estendido (não reescrito)
- `import { backfillStructural } from "./migrate.js";`
- No `ensure()`, logo após `doc = read() || defaultState();`, chama
  `backfillStructural(doc, defaultState())` ANTES dos backfills que já existiam
  (que assumem `doc.config`/`doc.agent`). Bloco antigo intacto.

### 3. `web/src/App.jsx` — 3 derefs guardados
- dep do efeito de cotações: `data && Array.isArray(data.watchlist) ? ... : ""`
- useMemo patr/dia: `(data.positions || []).reduce(...)` e `(data.cash || 0)`
- useMemo tickerItems: `(data.watchlist || []).map(...)`

### 4. `web/src/main.jsx` — Error Boundary (rede de segurança)
Classe `ErrorBoundary` envolvendo `<App/>`. Qualquer crash de render — inclusive
vetores desconhecidos — vira tela legível com botão **Recarregar** + detalhe
técnico (útil no iPhone via Web Inspector). Estilos inline, sem dependência do
tema (paleta da marca: #0b0e14 / #f0b429), alvo de toque ≥44px, safe-area no topo.

## QA da própria mudança
- **O que pode quebrar:** nada no caminho feliz — guardas e backfill só agem
  quando o campo está ausente/!array. Usuário com doc íntegro não percebe
  diferença (valores existentes são preservados — coberto por teste).
- **O que foi preservado:** os dois back-ends e a interface do store; os
  backfills existentes do `ensure()` (intactos); BYOK; guardrail; análise por
  ativo; persistence.js NÃO foi reescrito (apenas 1 import + 1 chamada).
- **Risco residual:** o Error Boundary não captura erros em handlers async
  (fora do render) — esses já têm try/catch + flash() no App.

## Validação automatizada (neste ambiente, sem device)
- `node --check`: migrate.js, persistence.js, api.js, notify.js → ok
- Balanceamento App.jsx/main.jsx (removendo comentários+strings) → diff 0
- `node web/tests/test_migrate.mjs` → **12/12 PASSARAM** (trava o vetor da tela branca)
- Regressão `node web/tests/test_api_parity.mjs` → **6/6 PASSARAM**

## Exige teste no iPhone
- Reinstalar pelo Xcode após `npm install && npm run build && npx cap sync ios`.
- Com um estado já existente no aparelho, abrir o app e navegar pelas 4 abas
  (Evolução/Mercado/Carteira/Perfil) — não deve haver tela branca.
- Forçar o Error Boundary (debug): no Web Inspector, rodar
  `localStorage.setItem("b3-agente-state-v1", JSON.stringify({config:{}}))` e
  recarregar — deve abrir normal (backfill), não em branco.
