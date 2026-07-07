# 03 — Revisão de QA de código

## Race conditions / React
- **`A` (`useMemo`)**: deps `[data, catalogSel, buyModal, keyDraft,
  refreshQuotes, flash]`. As ações novas (`runStopAlvoFor`, `applyStopAlvoFor`,
  `savePrompt`, `restorePrompt`) leem `data` (nas deps → sempre atual) e usam
  setters estáveis (`setData`, `setStopAlvo`, `setAnalysis`). Sem closure stale.
- **`ctx.openStopAlvo(t)`** chama `A.runStopAlvoFor(t)`: `A` é recriado a cada
  render (deps em `data`), então a referência usada é a atual.
- **`StopAlvoModal`** é single-asset e lê `stopAlvo[t]`: estado por ticker evita
  corrida entre cards; abrir um card não interfere noutro.
- **`runStopAlvoFor`**: set `loading:true` → `await` → set resultado/erro.
  Reabrir o mesmo card reinicia o ciclo; idempotente.

## Tela em branco (loading/erro/fallback)
- `loadErr` renderiza tela de erro com "Tentar de novo" (não branco).
- Bugs de tela branca conhecidos (markOnboarded, sectionTitle) corrigidos.
- `StopAlvoModal` com `stopAlvoFor` nulo retorna `null` (não monta).
- Modal sempre tem fallback: enquanto a IA carrega/erra, mostra a estimativa
  determinística (`localProposal`) — nunca fica vazio.

## Cadastro de ativo (validação Yahoo → 2 stores → relê → re-render)
- `serverStore.addWatchlistTicker` → `/api/watchlist/add` (valida no Yahoo,
  grava custom+watchlist, devolve `public_state`).
- `deviceStore.addWatchlistTicker` → valida via `/api/validate` (fallback
  `/api/quotes`), grava no `doc` (localStorage), `write()`, `pub()`.
- Ambos devolvem o estado público → `setData` re-renderiza. Paridade mantida.

## Segurança / BYOK
- `apiKey` nunca sai do servidor: `public_state`/`pub()` removem e expõem só
  `keyStored`. No nativo a chave fica no device e vai no corpo do POST (HTTPS/LAN
  conforme config), nunca em query string.
- Logs `[b3:notify]`/`[b3:add]` não imprimem chave nem dados sensíveis.
- `set_llm_prompts` limita tamanho (8000) e aceita só strings.

## Parsing robusto (paridade WebView iOS)
- `api.readBody`: remove BOM/cercas, tenta `JSON.parse`, extrai 1º `{…}`, e por
  fim devolve `{_raw}` — nunca lança. `req` converte `{_raw}` sozinho em erro
  acionável de endereço.
- `parse_carteira`: tolerante a cercas e a texto ao redor; array ou objeto;
  `operar:false` → níveis nulos; fallback p/ formato antigo.

## Riscos residuais (aceitos)
- `CapacitorHttp` pode não honrar `AbortController` no nativo → timeout depende
  do fetch nativo. Baixo impacto (erros ainda são tratados).
- Permissão de notificação revogada nas Ajustes do iOS após habilitar: o pref
  fica `enabled:true`; `send()` é guardado e não quebra. `NotifSection`
  reexibe o status real ao voltar o foco (`visibilitychange`).
