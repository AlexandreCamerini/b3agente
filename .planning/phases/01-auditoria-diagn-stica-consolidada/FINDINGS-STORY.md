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

### F-STORY-01 — Passo 7 (explicação educacional) depende 100% de chamada de IA opcional, sem fallback determinístico
- **Requisito:** STORY-01
- **Severidade:** Médio — risco real ao Core Value, ainda não materializado em incidente documentado (D-04)
- **Evidência:** `server/app/main.py:1362` (`POST /api/analyze/{ticker}`) exige `apiKey`/chave gerenciada; testado ao vivo com a conta `auditoria-story@local.test` sem chave configurada, retornou `HTTP 502 {"code":"missing_key"}` | mesmo comportamento em `POST /api/technical/analyze/{ticker}` (`main.py:1218`)
- **Verificação:** ao vivo (API real, 502 medido) + código
- **Impacto:** um usuário grátis sem chave BYOK e sem cota gerenciada disponível nunca recebe NENHUMA explicação de IA após operar — o Passo 7 da Experiência Principal, um dos dois de maior peso pro Core Value segundo o próprio plano desta auditoria, fica totalmente ausente para esse perfil, que é o mais comum na entrada do funil (grátis).
- **Recomendação:** garantir que o Modo Estudo sempre produza alguma explicação mínima determinística (ex.: montar a explicação a partir do setup/indicador identificado via `conceitos.py`/`kb.py`, sem depender de LLM) quando a IA não estiver disponível, em vez de deixar o passo pedagógico central do produto 100% condicionado a uma chamada opcional.

### F-STORY-02 — Ordem rejeitada não deixa rastro: sem `status`, sem `motivo de rejeição`, sem registro algum
- **Requisito:** STORY-01
- **Severidade:** Médio — risco real, não incidente documentado (D-04)
- **Evidência:** `server/app/main.py:1501-1518` (`/api/buy`) e `:1521-1535` (`/api/sell`) — uma rejeição (`HTTPException(400, "Caixa insuficiente.")`) simplesmente retorna erro HTTP, sem qualquer chamada a `store.py` que persista a tentativa; testado ao vivo: `history[0]` após uma compra bem-sucedida tem `{"date","type":"COMPRA","t","qty","price","pnl":null,"origem":"manual"}` — nenhum campo `status`
- **Verificação:** ao vivo (compra bem-sucedida exercitada) + código (ausência confirmada por leitura de `store.py`, sem função de log de tentativa rejeitada)
- **Impacto:** CLAUDE.md exige explicitamente, na seção "Modelo de simulação", que o sistema mantenha "cada ordem simulada com preço, quantidade, horário, tipo, status e motivo de rejeição". Hoje só decisões bem-sucedidas viram registro persistente — o usuário não consegue revisar depois POR QUE uma ordem foi rejeitada, exatamente o caso mais educativo (ex.: estourou o limite de risco, caixa insuficiente).
- **Recomendação:** registrar toda tentativa de ordem (aceita ou rejeitada) em `history`/estrutura equivalente com campo `status` (`executada`/`rejeitada`) e `motivo`, mesmo sem persistir posição.

### F-STORY-03 — Passo 8 "comparar com o benchmark": não existe comparação com nenhum índice em lugar nenhum do código
- **Requisito:** STORY-01
- **Severidade:** Médio — risco real ao Core Value, sem incidente documentado (D-04)
- **Evidência:** `web/src/finance.js:56-93` (`equityCurve`) calcula `retAcum`/`drawdown` só sobre a curva de patrimônio da própria carteira — nenhum parâmetro de índice externo; `web/src/App.jsx:4786-4789` tem um comentário explícito confirmando a ausência intencional: "Sem comparação com IBOV (R de análise não compara com retorno de índice)"; `grep -rn "Ibovespa\|IBOV\|benchmark" server/ web/src` não retorna nenhum cálculo, só esse comentário
- **Verificação:** código
- **Impacto:** o Passo 8 da Experiência Principal do CLAUDE.md ("registrar o aprendizado e comparar com um benchmark") está PARCIALMENTE ausente — o app registra e mostra retorno/drawdown da própria carteira, mas nunca contextualiza esse número contra o mercado (ex.: "você rendeu 3%, o Ibovespa rendeu 5% no período") — sem essa referência, o usuário leigo não consegue avaliar se o resultado foi bom ou ruim de fato, o que é justamente o tipo de raciocínio que o Core Value promete ensinar.
- **Recomendação:** adicionar uma série de retorno do Ibovespa (já disponível via Yahoo, mesmo provedor usado para os ativos) à `equityCurve`, exibida lado a lado com o retorno da carteira simulada, mesmo que como adição incremental de baixo esforço.

### F-STORY-04 — "Diário" (Perfil → Logs) é log operacional do agente, não uma jornada de aprendizado do usuário
- **Requisito:** STORY-01
- **Severidade:** Baixo — polimento/consistência, sem risco de produto (D-05)
- **Evidência:** `web/src/App.jsx:4850-5039` — a tela "Diário" mostra `agent.events` (ex.: "Ciclo (imediato) em 0.0s · 1 posição(ões) · 0 execução(ões)"), evidenciado ao vivo em `GET /api/state` → `agent.events` após a compra de teste; não há em nenhum ponto do código um prompt de reflexão dirigido ao usuário (ex.: "o que você aprendeu com essa operação?")
- **Verificação:** ao vivo (API real) + código
- **Impacto:** o "registrar o aprendizado" do Passo 8 hoje só existe como telemetria técnica do agente automático (útil para depuração), não como um artefato pedagógico voltado ao usuário leigo — reforça, junto com F-STORY-03, que o Passo 8 é o elo mais fraco da jornada.
- **Recomendação:** considerar (fase futura, fora do escopo desta auditoria) um resumo pós-operação em linguagem simples, distinto do log técnico do agente.

### F-STORY-05 — Transição Estudo→Operador tem critério LEGAL (aceite de termo), mas nenhum critério PEDAGÓGICO de prontidão
- **Requisito:** STORY-02
- **Severidade:** Médio — risco real ao Core Value ("só então tem acesso"), sem incidente documentado (D-04)
- **Evidência:** `web/src/App.jsx:1832` — `if (m === "operador" && !c.operadorTermo) { setTermoOpen(true); return; }`, o único gate antes de liberar o toggle; `server/app/store.py:235-239` confirma a mesma trava no backend (`if patch["appMode"] == "operador" and not isinstance(cfg.get("operadorTermo"), dict): pass  # sem termo aceito, o modo NÃO muda`); testado ao vivo via `PUT /api/config`: enviar `{"appMode":"operador"}` sozinho foi SILENCIOSAMENTE ignorado (retornou `appMode:"estudo"`), só mudou ao enviar `operadorTermo` junto — nenhum campo de progresso pedagógico (`conceitosVistos`, número de análises, tempo de uso) é consultado antes de liberar o modo
- **Verificação:** ao vivo (API real, testado nos dois sentidos) + código
- **Impacto:** um usuário pode entrar no app pela primeira vez e, na mesma sessão, sem executar uma única análise ou ordem, rolar um termo de responsabilidade e ativar o Modo Operador — o produto promete "só então" (depois de aprender) mas tecnicamente só verifica consentimento jurídico, não aprendizado algum.
- **Recomendação:** considerar um critério mínimo de prontidão antes de liberar o toggle (ex.: N operações concluídas no Estudo, ou N conceitos vistos) — mesmo que soft (aviso, não bloqueio duro) — para que a transição tenha alguma relação real com o Core Value declarado, não só o aceite de responsabilidade legal.

### F-STORY-06 — "Dois nomes Operador" (Operador IA × Modo Operador): faceta narrativa da dívida técnica já documentada
- **Requisito:** STORY-02
- **Severidade:** Baixo — já mitigado por link cruzado adicionado (F10-20260807-07); resta a hierarquia implícita (D-05)
- **Possível duplicata:** CODE
- **Evidência:** `.planning/codebase/CONCERNS.md:59-69` já documenta o achado técnico; `web/src/App.jsx` (`ModoTrabalhoCard`, ~linha 1825, e a navegação da aba "Operador IA") — nada no texto de nenhuma das duas telas explica que o agente autônomo ("Operador IA") só funciona DENTRO do Modo Operador (a trava é só reforçada em `agent.py:566`, nunca comunicada nesse sentido causal ao usuário)
- **Verificação:** código/docs
- **Impacto:** pedagogicamente, o usuário pode configurar o "Operador IA" sem entender por que ele não age (está fora do Modo Operador) — a lacuna é a mesma raiz de CONCERNS.md, mas o ângulo aqui é a ausência de explicação causal, não a duplicidade de nome em si.
- **Recomendação:** uma frase de link causal nas duas telas ("Operador IA só executa dentro do Modo Operador") resolve a lacuna narrativa; a correção estrutural (card de status único) é do plano CODE.

## Verificado e conforme

- **STORY-01, Passo 4 (enviar ordem virtual):** compra manual testada ao vivo (`POST /api/buy {"t":"PETR4","qty":100}`) executa com preço real da cotação no momento (`priceUsed 42.47`), débito correto do caixa (`cash 5753.00 = 10000 - 100*42.47`) — cálculo determinístico confirmado, sem intervenção de IA (`server/app/main.py:1501-1518`).
- **STORY-01, Passo 2 (fonte + horário do dado):** `GET /api/quotes` retorna `source` e o envelope tem `at`; front exibe ambos via `FONTE_LABEL()` e `quotesAt` (`web/src/App.jsx:1057,2927-2936,3234`) — atende ao princípio de transparência de dado do CLAUDE.md.
- **STORY-01, falha de dado (Passo 7):** a chamada de IA sem chave retornou erro estruturado (`502`, `code:"missing_key"`, `action`/`hint` preenchidos) em vez de qualquer conteúdo fabricado — comportamento correto de "nunca invente valor" mesmo no caminho de falha, verificado ao vivo.
- **STORY-02, Q3 (a troca acontece onde o usuário procuraria):** `ModoTrabalhoCard` fica no hub de Perfil (`web/src/App.jsx:1820-1868`), com toggle segmentado visível "🎓 Estudo / 📈 Operador" e texto explicando o que cada modo habilita — não está enterrada em sub-menu.
- **STORY-02, Q1 (o produto diz o que muda):** o texto abaixo do toggle diz explicitamente a diferença ("Decisões diretas... com plano de entrada, stop, alvo e risco" no Operador vs. "Carteira simulada e leitura didática" no Estudo — `App.jsx:1860-1863`); vocabulário de timing também muda por modo, confirmado ao vivo (`GET /api/timing/PETR4?appMode=operador` retornou `modo:"operador"` com frase própria, distinta do vocabulário `educacional`).
- **STORY-02, Q4 ("Modo Estudo nunca executa" — Fase A do `docs/plano-operador-entrada-e-modos.md`):** implementado com trava dupla — escrita (`store.set_agent`, impede gravar `mode:"executar"` fora do Operador) e leitura (`server/app/agent.py:559-570`, `if app_mode is not None and app_mode != "operador": mode = "sinalizar"`) — confirmado no código; a "Status: aguardando aprovação" no topo do documento está desatualizada (o código já referencia "Fase A" como entregue em `agent.py:559,637,642`), mas isso é achado de higiene de doc (Baixo), registrado aqui e não como F-STORY separado por não ter risco de produto associado.
- **Guardrail CVM (manchete do card só do motor determinístico):** confirmado por código — `server/app/setups.py:484-521` (`produzir_leitura`, a função que calcula `veredito`) é 100% determinística (sem chamada de IA); `web/src/App.jsx:2958-2999` (comentário "MANCHETE ÚNICA — decisão da mesa (o veredito do plano)") renderiza esse mesmo campo determinístico como headline do card, nunca o campo `recomendacao` que a IA devolve em `/api/analyze` (que é um campo textual separado, dentro da análise livre, nunca promovido a manchete). **Este é o item mais crítico da régua e está CONFORME.**

## Cobertura de requisitos

(preenchido na task 3)
