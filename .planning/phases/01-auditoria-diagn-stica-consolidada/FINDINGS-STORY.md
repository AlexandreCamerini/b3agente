# Achados — Dimensão STORY (storyline pedagógico)

Data: 2026-08-18

## Método de verificação

**Nível da escada alcançado: Nível 3 — API real + código.** Nem `mcp__claude-in-chrome__*`
nem `mcp__computer-use__*` estavam disponíveis no conjunto de ferramentas deste agente
(confirmado por inspeção da lista de tools antes de iniciar a Task 1) — Níveis 1 e 2 (browser
dirigível/observável) não puderam ser tentados, não por escolha, mas por ausência da
ferramenta. Todo o roteiro abaixo foi dirigido pelo backend real (`http://localhost:8787`),
nunca inferido de leitura de código sem confirmação, exceto onde marcado explicitamente
"código" na coluna Método.

**Como o stack foi subido:** o backend compartilhado da wave já estava no ar quando este plano
iniciou (`GET /api/health` respondeu `200 {"ok":true,"build":"F10-20260817-08"}` de imediato) —
não foi necessário nem permitido subir um segundo uvicorn. O Vite deste plano (porta 5174) NÃO
foi subido: sem ferramenta de browser disponível, não haveria como observar o resultado
renderizado, e subir o processo só para não o usar violaria o princípio de não gerar processo
solto sem propósito. Nenhum arquivo de produção foi tocado (confirmado ao final: `git status
--porcelain server web web-admin` vazio).

**Conta e ticker usados:** conta isolada `auditoria-story@local.test` criada via
`POST /api/auth/register` (escopo `user_id` próprio, isolado do plano de UX que roda em
paralelo no mesmo backend). Ticker `PETR4` (líquido, real), ordem de compra de 100 ações
(1 lote).

**O que NÃO pôde ser verificado ao vivo (limitação explícita):**
- Renderização visual real (CSS, layout, contraste, responsividade, toque) — não há Nível 1/2
  disponível nesta execução. Qualquer afirmação sobre UI vem de leitura de `web/src/App.jsx`
  (com `grep -n` para localizar a faixa, nunca o arquivo inteiro), não de tela observada.
- Saída real de IA (Surface 3 de STORY-04, e o próprio Passo 7 "explicação educacional"):
  `POST /api/analyze/PETR4` retornou `HTTP 502 {"code":"missing_key", "message":"Nenhuma chave
  de API disponível para a IA."}` — nenhuma chave BYOK nem gerenciada está configurada no
  backend local desta wave. O comportamento de falha em si (erro estruturado, sem inventar
  resposta) foi verificado ao vivo; o CONTEÚDO que a IA produziria não foi.
- Comportamento específico do app nativo iOS (WKWebView, TTS, push) — fora do alcance de um
  backend local sem o app compilado.

## Roteiro navegado

| # | Passo (CLAUDE.md) | Modo | Tela/rota observada | O que apareceu | Método |
|---|---|---|---|---|---|
| 1 | Escolher ativo | Estudo | `GET /api/state` (watchlist) + tela Mercado (`web/src/App.jsx`, grid de watchlist) | Watchlist inicial da conta nova: PETR4, VALE3, ITUB4, BBDC4, BBAS3, B3SA3; catálogo completo de 20 tickers B3 disponível em `config.catalog` | API real |
| 1 | Escolher ativo | Operador | idem — a escolha de ativo não depende de `appMode` (confirmado: nenhuma ocorrência de `appMode` nas rotas de watchlist/catálogo em `server/app/main.py`) | Mesma lista, mesmo fluxo — sem tela ou filtro exclusivo do Operador | API real + código |
| 2 | Visualizar dado + horário da atualização | Estudo | `GET /api/quotes?symbols=PETR4` | `{"price":42.47,"source":"yahoo","previousClose":42.09,"currency":"BRL"}` + `"at":"18/08/2026 09:18"` no envelope da resposta | API real |
| 2 | Visualizar dado + horário da atualização | Operador | idem — fonte/horário da cotação não mudam por modo | Mesmo dado; front exibe fonte via `FONTE_LABEL()` (`App.jsx:1057,2927-2936,3234`) e horário via `quotesAt` (`App.jsx:3234,6258`) | API real + código |
| 3 | Analisar contexto e risco | Estudo | `GET /api/technicals/PETR4` | Pacote 100% determinístico: RSI14 55.9, MACD hist −0.059, SMA20/50/200, ADX14 16.4 ("tendência fraca/lateral"), `snapshotId`/`snapshotAt` carimbados | API real |
| 3 | Analisar contexto e risco | Operador | `GET /api/timing/PETR4?appMode=operador` | `{"modo":"operador","estado":"sem_dado","vereditoDiario":"Estudar alta"}` — vocabulário de timing muda para o modo Operador (comparado ao mesmo endpoint sem `appMode`, que usa vocabulário `educacional`) | API real |
| 4 | Enviar ordem virtual | Estudo | `POST /api/buy {"t":"PETR4","qty":100}` | `HTTP 200`, `priceUsed 42.47`, `cash 5753.00`, posição aberta `{"t":"PETR4","qty":100,"avg":42.47,"stop":null,"alvo":null}` — SEM checagem de `appMode` na rota | API real |
| 4 | Enviar ordem virtual | Operador | mesmo endpoint `/api/buy` — único ponto real de diferença por modo é a AUTOMAÇÃO do agente (`agent.py:551-570`), não a ordem manual | API real + código |
| 5 | Acompanhar execução simulada | Estudo | `GET /api/state` → `history[0]` | `{"date":"18/08/2026 09:19","type":"COMPRA","t":"PETR4","qty":100,"price":42.47,"pnl":null,"origem":"manual"}` — SEM campo `status`, SEM registro de tentativas rejeitadas | API real |
| 5 | Acompanhar execução simulada | Operador | idem — `history` é por conta, não segmentado por modo | Mesmo formato | API real |
| 6 | Visualizar resultado | Estudo | `GET /api/state` → `positions[0]` | `avg 42.47`, `qty 100`, `stop/alvo null` (não setados no fluxo mínimo de compra) | API real |
| 6 | Visualizar resultado | Operador | idem + `portfolioMetrics()` (`web/src/finance.js:25`) calcula patrimônio/PnL para exibição | Mesmo cálculo determinístico subjacente, independente do modo | API real + código |
| 7 | Receber explicação educacional | Estudo | `POST /api/analyze/PETR4` | `HTTP 502 {"code":"missing_key","message":"Nenhuma chave de API disponível para a IA."}` — sem chave configurada neste backend local, a explicação de IA não pôde ser obtida | API real (falha, não fabricação) |
| 7 | Receber explicação educacional | Operador | `POST /api/technical/analyze/PETR4` (mesma dependência de chave, não testado ao vivo pela mesma limitação) | AUSENTE nesta verificação — mesma limitação de ambiente (Surface 3 não exercitável) | código (inferência de rota, não exercitado) |
| 8 | Registrar aprendizado e comparar com benchmark | Estudo | `GET /api/state` → `equitySnapshots` | `[]` — grava só 1×/sessão a partir do FRONT (`App.jsx:7162-7176`), após cotações; sem front rodando neste teste, nunca disparou | API real + código |
| 8 | Registrar aprendizado e comparar com benchmark | Operador | idem; tela "Diário" (Perfil → Logs) é log operacional do agente (`agent.events`), não uma jornada de aprendizado do usuário | AUSENTE — nenhuma comparação com IBOV/benchmark existe em `web/src/finance.js:56-93` (`equityCurve`) nem em nenhum outro ponto do código (`grep -rn "Ibovespa\|IBOV\|benchmark"` não retorna cálculo algum, só um comentário explicando a ausência em `App.jsx:4786-4789`) | código |

## Achados

(preenchido nas tasks 2 e 3)

## Verificado e conforme

(preenchido nas tasks 2 e 3)

## Cobertura de requisitos

(preenchido na task 3)
