# REPORT-01 — Revisão geral do Boris+ (b3-agente)

**Data:** 2026-08-18
**Escopo:** 5 dimensões (storyline pedagógico, UX/UI, código, gating de monetização,
portal admin) — diagnóstico, sem nenhuma correção implementada.

## Sumário executivo

| Severidade | Qtd | Dimensões afetadas |
|---|---|---|
| Crítico | 2 | UX, GATE |
| Alto | 8 | UX, CODE, GATE, ADMIN |
| Médio | 20 | STORY, UX, CODE, GATE, ADMIN |
| Baixo | 9 | STORY, UX, CODE |

### Críticos

- **C-11** — Rótulo de fonte de dado fixo e incorreto no painel técnico
  (`TechnicalModal` sempre exibe "Fonte: Yahoo Finance", mesmo quando o dado
  veio da brapi, que é a fonte MASTER de candles diários desde a ADR-008).
  Viola o princípio 3 do CLAUDE.md — a informação de proveniência é ativamente
  falsa, não apenas ausente. → Propagar `source`/`provedor` até o payload de
  `/api/technicals` e trocar a string fixa por `FONTE_LABEL(data.source)`.
- **C-30** — Estado `degradado` da cota brapi (TTL do cache de spot triplicado
  quando o orçamento mensal passa de 80%) é invisível para usuário E admin,
  sem nenhum timestamp/badge que reflita o dado mais velho. Viola o mesmo
  princípio 3, de forma sistemática (todo mês, ao se aproximar do teto). →
  Expor o estado `degradado` no payload de `/api/obs/usage` e refletir no
  timestamp de "última atualização" mostrado ao usuário.

### Altos

- **C-12** — Erro de fonte de dado (ticker inválido em `/api/buy`) vaza
  detalhe técnico interno (URL da Yahoo, parâmetro `crumb`) como HTTP 500 cru,
  em vez do 502 limpo já implementado logo abaixo no código, que nunca é
  alcançado. → Envolver `candle_provider.get_quote` num tratamento que
  devolva preço nulo, replicando o padrão já usado em `get_quotes`.
- **C-19** — Os guardiões de teste dos 3 bugs históricos travam o sintoma
  exato já corrigido, não a classe do erro ("estado que muda num lugar que
  outro não vê") — uma variante nova do mesmo padrão passaria pelos 3 sem
  disparar nenhum. → Teste genérico de paridade (ver C-20) + "card de status
  único" fecham a lacuna estrutural.
- **C-20** — Paridade `deviceStore`×`serverStore`: 28 de 58 métodos (48%) sem
  nenhuma referência em teste, sem guardião genérico que detectaria uma
  assimetria futura — lacuna que já foi causa raiz de 2 incidentes
  documentados. → Teste único que extraia as chaves dos dois stores e falhe
  em qualquer assimetria.
- **C-31** — Os hooks de gate (`can_add_ticker`, `can_analyze`) nunca resolvem
  o plano por usuário — `current_plan(user)` existe e está correto mas nunca é
  chamado; ligar o cap comercial hoje bloquearia igualmente contas `'pro'`. →
  Passar `plan=plan.current_plan(user)` nos 3 call sites de `main.py`.
- **C-32** — `can_analyze` (hook de plano) e `metering.check` (cota de IA
  gerenciada) são dois gates concorrentes respondendo à mesma pergunta na
  mesma requisição — ativar o passo 2 do ADR-010 sem reconciliar os dois cria
  contagem duplicada. → Decidir se `can_analyze` vira wrapper de
  `metering.check` antes de alimentá-lo com contador real.
- **C-35** — O segundo kill-switch (`timing_watch`, controla o push do
  gatilho) é invisível nas 10 abas do portal e só pode ser desligado por
  redeploy — mesmo padrão de risco que já causou o incidente real de 2,5 dias,
  agora numa superfície irmã. → Estender o padrão memória→DB→env do
  `agent.kill_switch_on()` para `timing_watch` + 2º KPI na Visão Geral.
- **C-36** — O painel de custos mostra `erros` mas nunca `vazios`/`alerta`/
  `taxaFalha` — o backend já resolveu a cegueira do incidente real de
  31/07/2026 (Yahoo 200 com zero velas), mas a UI reproduz a mesma cegueira na
  apresentação. → Ligar os 3 campos já prontos no payload ao card "Orçamento
  brapi" da aba Custos.
- **C-37** — Não existe alerta de "kill-switch ligado há N horas em horário
  de pregão" — é o mecanismo que, se existisse, teria encurtado o incidente
  real de 2,5 dias para horas; o dado (timestamp da mudança) já existe no
  `admin_audit_log`. → Card "ligado há Xh" na aba Automação, leitura do dado
  já existente.

### Leitura de conjunto

- **O mesmo padrão — "o backend já calcula/corrige o dado certo, mas a
  camada de apresentação nunca lê o campo pronto" — se repete em 3 dimensões
  diferentes**: C-11/C-30 (UX/GATE, campo de proveniência/degradado nunca
  chega ao payload consumido pela tela) e C-36 (ADMIN, o campo já está no
  payload e a UI simplesmente não lê). Não é falta de dado, é falta de fiação
  entre backend e UI — o padrão de correção é estruturalmente o mesmo nos 3
  casos.
- **GATE concentra o maior risco de "arquitetura pronta, mas inerte"**: os 3
  achados Alto/Crítico de GATE (C-30, C-31, C-32) descrevem hooks e campos que
  já existem e estão corretos, mas nunca são chamados/lidos pelos call sites
  reais — ativar o gating comercial hoje exige tocar código, não só
  configuração.
- **ADMIN concentra o maior número de Altos (3 de 8)**: todos ligados à mesma
  causa-raiz do incidente real do kill-switch — sinalização passiva sem
  alerta ativo, repetida em 3 superfícies distintas (2º kill-switch, painel
  de falha de provedor, ausência de alerta por duração).
- **Divergência de calibração registrada explicitamente — C-21 (Médio)
  discorda do exemplo textual do `01-CONTEXT.md`**, que cita os 3 bugs
  históricos do padrão `appMode` como exemplo ilustrativo de Alto (D-03). A
  investigação de código (F-CODE-01) mostrou que nenhum dos 3 bugs foi
  causado por divergência real de leitura de `appMode` no mesmo render — a
  atribuição do exemplo não se sustenta na evidência. Este relatório manteve
  Médio com base na evidência, mas registra a divergência aqui porque depende
  do julgamento do dono do produto, não só da régua objetiva — ver nota de
  calibração completa na Metodologia e o achado `C-21` na seção Código.
- **O que este relatório NÃO conseguiu verificar** (limitações herdadas da
  wave 1): renderização visual real em nenhuma das 5 dimensões (sem
  ferramenta de browser disponível nesta execução); saída real de resposta de
  IA (Surface 3 de STORY-04, sem chave configurada no backend local);
  comportamento do app nativo iOS; verificação visual ao vivo das 10 telas do
  portal admin e do handoff mobile completo; payload real de `GET
  /api/ai/quota`; 2 dos guardiões de teste mais relevantes desta auditoria
  (`test_carteira_nativa_sincroniza.mjs`, `test_appmode_sincroniza_servidor.mjs`)
  não puderam ser confirmados como passando neste worktree (falha de
  ambiente, não de asserção — ver C-24).
- **A separação cota-física-brapi × cap-comercial-de-IA está bem resolvida
  na arquitetura** (ADR-010) — o risco real de GATE não é design, é ativação
  incompleta dos call sites (C-31, C-32, C-33).

### Sugestão de sequenciamento

Agrupamento dos achados Críticos/Altos por dependência TÉCNICA (o que precisa
vir antes do quê) — sem estimativa de tempo, sem prioridade de negócio (fica
com o Alex):

1. **Transparência de proveniência/frescor do dado de mercado** (C-11, C-30)
   — ambos exigem que o payload de API carregue um campo novo
   (`source`/`provedor` em `/api/technicals`; estado `degradado` por fatia em
   `/api/obs/usage`) antes que qualquer UI possa consumi-lo corretamente.
   Pré-requisito técnico do bloco 2.
2. **Robustez do caminho de erro/observabilidade de falha do provedor de
   dados** (C-12, C-36) — C-12 exige tratar a exceção crua de
   `candle_provider.get_quote`; C-36 exige ligar campos que o backend já
   calcula (`vazios`/`alerta`/`taxaFalha`) ao painel administrativo. Ambos
   dependem do mesmo tipo de trabalho (expor dado de falha já calculado pela
   camada certa).
3. **Guardiões estruturais de paridade e regressão** (C-20, C-19) — C-20 (teste
   genérico de paridade `deviceStore`×`serverStore`) é pré-requisito técnico
   de C-19 (fechar a lacuna dos 3 guardiões que só cobrem sintoma): o teste
   genérico de paridade é o mecanismo que fecharia a lacuna estrutural do
   bug histórico #2.
4. **Ativação dos hooks de gating comercial** (C-31 → C-32) — C-31 (call
   sites passarem a resolver `current_plan(user)`) é pré-requisito técnico de
   C-32 (reconciliar `can_analyze` com `metering.check`): sem plano resolvido
   por usuário, não há base para decidir a arquitetura de contagem.
5. **Visibilidade ativa de incidentes operacionais (kill-switches)** (C-35 →
   C-37) — C-35 (expor o estado do 2º kill-switch no padrão memória→DB→env)
   é pré-requisito técnico de C-37 (calcular "ligado há Xh" a partir do
   `admin_audit_log`): só depois que os dois kill-switches estiverem
   igualmente visíveis faz sentido calcular duração para os dois.

## Metodologia

### Régua de severidade (D-02..D-05, `01-CONTEXT.md`)

- **Crítico (D-02)** — viola um dos 10 princípios obrigatórios do `CLAUDE.md` do
  repo OU o guardrail CVM (manchete do card só do motor determinístico).
- **Alto (D-03)** — já causou incidente real documentado OU bloqueia uma decisão
  de negócio pendente.
- **Médio (D-04)** — risco real, ainda não materializado em incidente.
- **Baixo (D-05)** — polimento/consistência sem risco de produto.

A régua foi aplicada a TODO o inventário de achados na mesma ordem, para todas
as 5 dimensões: (1) viola um dos 10 princípios do `CLAUDE.md` (nomeados
individualmente, não a seção "Modelo de simulação" nem o Core Value do
`PROJECT.md`, que não são um dos 10) ou o guardrail CVM → Crítico; (2) se não,
já causou incidente real documentado ou bloqueia decisão de negócio pendente →
Alto; (3) se não, risco real ainda não materializado → Médio; (4) senão →
Baixo.

### Método de verificação por dimensão e limitações

| Dimensão | Nível alcançado | Como o stack subiu | Conta/ambiente | Limitação declarada |
|---|---|---|---|---|
| STORY | 3 — API real + código (Níveis 1/2 de browser indisponíveis nesta execução, `mcp__claude-in-chrome__*`/`mcp__computer-use__*` ausentes do toolset) | Backend compartilhado da wave já no ar (`GET /api/health` 200); Vite deste plano não subido (sem ferramenta de browser, não haveria como observar o resultado) | `auditoria-story@local.test`, ticker PETR4, 100 ações | Renderização visual real não verificada (CSS/layout/contraste/toque); saída real de IA não exercitada (sem chave BYOK/gerenciada — `502 missing_key` medido); comportamento do app nativo iOS fora do alcance |
| UX | 3 — API real + código/docs (mesma ausência de Níveis 1/2, confirmada por inspeção do toolset) | `uvicorn` real na porta 8787 contra fontes de dado reais (Yahoo/brapi, sem stub); Vite na porta 5176; `web/node_modules` reusado via symlink para a árvore principal (gitignored, nenhum pacote novo instalado) | `auditoria-ux@local.test`, chamadas HTTP reais (registro, login, quotes, buy/sell, timing, technicals) | Renderização visual real (screenshot/DOM) não verificada; contraste calculado por fórmula de luminância WCAG a partir dos hex do tema, não medido em tela renderizada |
| CODE | D-01 autoriza código+docs para esta dimensão | Suíte canônica executada (`bash scripts/executar.sh --testes`); greps direcionados; comparação programática de paridade de stores | Worktree próprio, `web/node_modules` NÃO instalado (decisão explícita — instalar pacote é exclusão de auto-fix nesta fase read-only) | Nenhuma navegação ao vivo no browser/PWA; 7 de 74 testes web falharam por `ERR_MODULE_NOT_FOUND` de ambiente (não regressão) — os 2 arquivos mais relevantes da auditoria (`test_carteira_nativa_sincroniza.mjs`, `test_appmode_sincroniza_servidor.mjs`) ficaram entre os 7 bloqueados, sem confirmação positiva de que ainda protegem o código |
| GATE | D-01 autoriza código+docs para esta dimensão; backend local não subido (fora do ar, decisão de não competir com os processos dos planos irmãos) | Leitura integral de `plan.py`, `metering.py`, `managed.py`, `brapi_budget.py` (trechos), `candle_provider.py` (trecho), `agent.py` (trecho), rotas de `main.py`, `web/src/plan.js` inteiro | — | Payload real de `GET /api/ai/quota` não exercitado; comportamento em produção do estado `degradado` sob carga real não observado |
| ADMIN | D-01 autoriza código+docs para esta dimensão; portal parcialmente subido (`web-admin/node_modules` instalado via `npm install`, sem editar `package.json`), backend NÃO subido (sem `server/.venv` provisionado neste worktree, e subir um novo arriscava colidir com os servidores dos planos irmãos na mesma porta 8787) | Leitura integral de `rbac.py`, ADRs 013/014, rotas `/api/obs/*`/`/api/analytics/*`/`/api/admin/*`, `web-admin/src/App.jsx` inteiro | — | Nenhuma verificação visual ao vivo das 10 telas nem do handoff mobile completo (app→browser in-app→portal); todo achado cita arquivo:linha real, não inferência sem evidência |

**Nota de plumbing (herdada de todos os 5 planos da wave 1):** os worktrees da
wave 1 foram ramificados de um commit anterior à criação de `.planning/` nesta
sessão de planejamento — `.planning/` teve que ser recriado localmente em cada
worktree, e os arquivos de referência (`PROJECT.md`, `STATE.md` etc.) foram
lidos por caminho absoluto no worktree de origem (`peaceful-swanson-e9e462`).
A ferramenta `Write` deste ambiente também bloqueia por padrão qualquer
caminho cujo nome de arquivo contenha `FINDINGS` (e, como descoberto neste
próprio plano de consolidação, também `REPORT`) — os 5 artefatos da wave 1 e
este `REPORT-01.md` foram escritos sob nome alternativo e renomeados via `mv`
(operação de filesystem, fora do guard de conteúdo do `Write`).

### Deduplicação

**Inventário de partida:** 39 achados nomeados com ID `F-{DIM}-NN` nos 5
arquivos (`grep -n '^### F-'` nos 5 `FINDINGS-*.md`: STORY 10, UX 9, CODE 10,
GATE 5, ADMIN 4), mais 3 achados substantivos com severidade atribuída mas
sem número `F-` formal (registrados em texto corrido nas seções de tabela dos
achados brutos): "Ausência de E2E/browser automation" (CODE-04, Médio),
"Ausência de medição numérica de cobertura" (CODE-04, Baixo) e "gasto anômalo
de IA sem alerta preventivo" (ADMIN-02, Médio) — total de 42 unidades de
julgamento avaliadas.

**Candidatos de deduplicação do plano (task 1b) — avaliados um a um, não
assumidos:**

1. **Gate "Executar" mudo — faceta de acessibilidade (F-UX-08) × faceta de
   dívida técnica/blast radius (F-CODE-06/07).** NÃO fundido. Evidência: F-UX-08
   é sobre o botão "Executar" (`App.jsx:3780-3799`) sem `aria-describedby`
   ligando-o ao parágrafo explicativo; F-CODE-07 é sobre o *Toggle* "Entrada
   automática" (`App.jsx:3924`) sem atributo HTML `disabled`. São controles
   diferentes, com gaps estruturalmente diferentes (vínculo semântico vs.
   ausência de atributo que também afeta usuário sem leitor de tela) — ambos
   descendem do mesmo incidente histórico documentado
   (`docs/auditoria-controle-ordens-parametros.md`), mas não compartilham a
   mesma causa raiz específica. Mantidos como `C-18` e `C-23`, com
   cross-referência explícita entre eles em vez de fusão.
2. **"Dois nomes Operador" — faceta pedagógica (F-STORY-06) × faceta de
   código (CODE-01).** NÃO fundido. F-STORY-06 documenta a lacuna narrativa
   (nenhuma tela explica por que "Operador IA" não age fora do "Modo
   Operador"). Nenhum achado formal em `FINDINGS-CODE.md` cobre essa
   duplicidade de nome especificamente — os achados de CODE-01 são sobre
   recomputação de `appMode`, não sobre nomenclatura de tela. O candidato de
   fusão sugerido pelo plano não se confirmou na evidência; mantido como
   `C-07`, standalone.
3. **Transparência de cota quando o orçamento da brapi degrada — faceta de UX
   (UX-01) × faceta de gating (GATE-02).** NÃO fundido. Nenhum achado em
   `FINDINGS-UX.md` cobre o estado `degradado` do orçamento brapi
   especificamente — os achados de UX-01 (F-UX-01..04) tratam de rótulo de
   fonte fixo, disclaimer ausente, erro 500 cru e ausência de fill parcial,
   temas relacionados mas com causa raiz distinta da opacidade do TTL
   estendido por orçamento. O achado real (`C-30`, F-GATE-04, Crítico) existe
   só do lado GATE.
4. **Kill-switch — faceta de observabilidade (ADMIN-02) × faceta de dívida
   técnica (CODE).** NÃO fundido. `FINDINGS-CODE.md` não contém nenhuma menção
   a kill-switch. Achados mantidos só no lado ADMIN (`C-35`, `C-37`).

**Fusão confirmada (não estava na lista do plano, encontrada por inspeção
direta):** `F-STORY-10` (STORY-04: a frase "Não há dados suficientes para
concluir" nunca aparece verbatim) e `F-UX-09` (UX-04: o mesmo fato, mesma
busca, mesma conclusão) são o MESMO achado, relatado de forma independente
por dois planos que rodaram a mesma busca textual sobre o mesmo conjunto de
arquivos. Fundidos em `C-10` (origem: `F-STORY-10, F-UX-09`).

**Achado movido para "Verificado e conforme" (não é um achado de risco):**
`F-CODE-06` (severidade `N/A` na origem) confirma que o defeito original do
gate "Executar"/"Entrada automática" (2026-08-07) já foi corrigido — não é um
problema, é uma confirmação de correção histórica, então não recebe um `C-NN`
na lista de achados por severidade; está citado na seção "Verificado e
conforme" da dimensão Código.

**Contagem final:** 42 unidades avaliadas − 1 (F-CODE-06 movido para
conforme) − 1 (fusão F-STORY-10+F-UX-09, 2→1) = **39 achados `C-NN`** no
relatório consolidado. Nenhum achado da wave 1 desaparece sem este registro.

**Nota de calibração — F-CODE-01 diverge do exemplo textual do
`01-CONTEXT.md`:** o próprio `01-CONTEXT.md` (régua D-03) cita "os 3 bugs do
padrão `appMode` em `App.jsx`" como exemplo ilustrativo de severidade Alto. A
investigação de código do plano CODE (F-CODE-01, ver `C-21` abaixo) verificou
linha a linha os 3 bugs históricos e concluiu que **nenhum dos 3 foi causado
por divergência real de leitura de `appMode` no mesmo render** — a atribuição
causal do `CONCERNS.md`/`01-CONTEXT.md` não se sustenta na evidência de
código. Este relatório mantém a classificação Médio (D-04) atribuída pelo
próprio plano CODE, com base na evidência, e não o exemplo ilustrativo do
contexto — mas registra a divergência aqui explicitamente e a destaca no
Sumário executivo (`### Leitura de conjunto`) e no texto que acompanha o
checkpoint de validação (Task 3), porque é exatamente o tipo de julgamento
que depende da memória do dono do produto, não só da régua objetiva.

### Validação humana (checkpoint Task 3, 2026-08-18)

O Alex (dono do produto) validou o sumário executivo e as listas de
Críticos/Altos. Resultado, resumido aqui para auditabilidade (detalhe
completo em cada achado citado e em `01-06-SUMMARY.md`):

- **C-21** (Médio) — confirmado sem reclassificação: sem memória de incidente
  adicional causado pela divergência de leitura de `appMode`, além dos 3 bugs
  já documentados e já avaliados como não causados por ela.
- **C-11** (Crítico) — confirmado sem reclassificação. Duas propostas
  alternativas de solução foram discutidas e explicitamente descartadas
  (fonte dupla por finalidade; listbox de configuração de fonte/frequência
  para o usuário) — motivo do descarte registrado no próprio achado C-11.
- **C-34** (Médio) — um "medidor de orçamento brapi visível ao usuário" foi
  levantado como achado candidato durante a discussão do checkpoint;
  avaliado com o mesmo critério de deduplicação da Task 1 e confirmado que
  já é o mesmo fato que `F-GATE-05`/`C-34` documenta — não virou achado novo,
  recebeu evidência adicional e recomendação estendida no próprio C-34.
- **Nenhuma severidade mudou** nesta validação (0 linhas `**Reclassificado:**`
  adicionadas) — a tabela de contagem do Sumário executivo permanece 2
  Crítico, 8 Alto, 20 Médio, 9 Baixo (39 total).
- Nenhuma correção de código foi implementada durante ou após esta
  validação, consistente com a fase ser diagnóstica por decisão do próprio
  Alex (`PROJECT.md`, Out of Scope).

## Achados por dimensão

### 1. Storyline pedagógico (STORY-01..04)

**Roteiro navegado ao vivo** (8 passos da Experiência Principal do
`CLAUDE.md`, conta `auditoria-story@local.test`, ticker PETR4): passos 1-6
verificados ao vivo via API real em ambos os modos (Estudo/Operador) sem
diferença de cálculo subjacente; passo 7 (explicação educacional) retornou
`HTTP 502 {"code":"missing_key"}` — falha estruturada, não invenção; passo 8
(comparar com benchmark) confirmado ausente por código (`grep -rn
"Ibovespa|IBOV|benchmark"` sem cálculo algum). Detalhe completo linha a linha
no arquivo `FINDINGS-STORY.md` (roteiro de 8 passos × 2 modos, 16 linhas de
evidência).

#### C-01 — Passo 7 (explicação educacional) depende 100% de chamada de IA opcional, sem fallback determinístico [Médio]
- **Dimensão:** STORY | **Requisito:** STORY-01 | **Origem:** F-STORY-01
- **Regra aplicada:** D-04 — risco real ao Core Value, ainda não materializado em incidente documentado
- **Evidência:** `server/app/main.py:1362` (`POST /api/analyze/{ticker}`) exige `apiKey`/chave gerenciada; testado ao vivo com `auditoria-story@local.test` sem chave configurada, retornou `HTTP 502 {"code":"missing_key"}`; mesmo comportamento em `POST /api/technical/analyze/{ticker}` (`main.py:1218`)
- **Verificação:** ao vivo (API real, 502 medido) + código
- **Impacto:** um usuário grátis sem chave BYOK e sem cota gerenciada disponível nunca recebe NENHUMA explicação de IA após operar — o Passo 7, um dos dois de maior peso pro Core Value, fica totalmente ausente para o perfil mais comum na entrada do funil (grátis)
- **Recomendação:** garantir que o Modo Estudo sempre produza alguma explicação mínima determinística (montada a partir do setup/indicador via `conceitos.py`/`kb.py`, sem depender de LLM) quando a IA não estiver disponível.

#### C-02 — Ordem rejeitada não deixa rastro: sem `status`, sem `motivo de rejeição`, sem registro algum [Médio]
- **Dimensão:** STORY | **Requisito:** STORY-01 | **Origem:** F-STORY-02
- **Regra aplicada:** D-04 — risco real. Não classificado Crítico: o requisito citado ("cada ordem simulada com preço, quantidade, horário, tipo, status e motivo de rejeição") vem da seção "Modelo de simulação" do `CLAUDE.md`, não de um dos 10 "Princípios obrigatórios" numerados que definem D-02
- **Evidência:** `server/app/main.py:1501-1518` (`/api/buy`) e `:1521-1535` (`/api/sell`) — uma rejeição (`HTTPException(400, "Caixa insuficiente.")`) retorna erro HTTP sem persistir a tentativa; testado ao vivo: `history[0]` após compra bem-sucedida tem `{"date","type":"COMPRA","t","qty","price","pnl":null,"origem":"manual"}`, sem campo `status`
- **Verificação:** ao vivo (compra bem-sucedida exercitada) + código
- **Impacto:** só decisões bem-sucedidas viram registro persistente — o usuário não consegue revisar depois POR QUE uma ordem foi rejeitada, o caso mais educativo (ex.: estourou risco, caixa insuficiente)
- **Recomendação:** registrar toda tentativa de ordem (aceita ou rejeitada) com campo `status` (`executada`/`rejeitada`) e `motivo`, mesmo sem persistir posição.

#### C-03 — Passo 8 "comparar com o benchmark": não existe comparação com nenhum índice em lugar nenhum do código [Médio]
- **Dimensão:** STORY | **Requisito:** STORY-01 | **Origem:** F-STORY-03
- **Regra aplicada:** D-04 — risco real ao Core Value, sem incidente documentado
- **Evidência:** `web/src/finance.js:56-93` (`equityCurve`) calcula `retAcum`/`drawdown` só sobre a curva da própria carteira; `web/src/App.jsx:4786-4789` tem comentário explícito confirmando a ausência intencional ("Sem comparação com IBOV"); `grep -rn "Ibovespa|IBOV|benchmark" server/ web/src` não retorna nenhum cálculo
- **Verificação:** código
- **Impacto:** o Passo 8 está PARCIALMENTE ausente — o app mostra retorno/drawdown da própria carteira mas nunca contextualiza contra o mercado; sem essa referência, o usuário leigo não consegue avaliar se o resultado foi bom ou ruim, exatamente o raciocínio que o Core Value promete ensinar
- **Recomendação:** adicionar série de retorno do Ibovespa (via Yahoo, mesmo provedor já usado) à `equityCurve`, exibida lado a lado com o retorno da carteira simulada.

#### C-04 — Transição Estudo→Operador tem critério LEGAL (aceite de termo), mas nenhum critério PEDAGÓGICO de prontidão [Médio]
- **Dimensão:** STORY | **Requisito:** STORY-02 | **Origem:** F-STORY-05
- **Regra aplicada:** D-04 — risco real ao Core Value ("só então tem acesso"), sem incidente documentado
- **Evidência:** `web/src/App.jsx:1832` — `if (m === "operador" && !c.operadorTermo) { setTermoOpen(true); return; }`, único gate antes de liberar o toggle; `server/app/store.py:235-239` confirma a mesma trava no backend; testado ao vivo via `PUT /api/config`: `{"appMode":"operador"}` sozinho foi SILENCIOSAMENTE ignorado, só mudou ao enviar `operadorTermo` junto; nenhum campo de progresso pedagógico é consultado antes de liberar o modo
- **Verificação:** ao vivo (API real, testado nos dois sentidos) + código
- **Impacto:** um usuário pode entrar no app pela primeira vez, sem executar uma única análise, rolar um termo de responsabilidade e ativar o Modo Operador na mesma sessão — o produto promete "só então" mas tecnicamente só verifica consentimento jurídico, não aprendizado algum
- **Recomendação:** considerar um critério mínimo de prontidão (ex.: N operações no Estudo, ou N conceitos vistos) antes de liberar o toggle, mesmo que soft (aviso, não bloqueio duro).

#### C-05 — "Diversificação" está totalmente ausente do produto [Médio]
- **Dimensão:** STORY | **Requisito:** STORY-03 | **Origem:** F-STORY-07
- **Regra aplicada:** D-04 — conceito da lista obrigatória do CLAUDE.md ("Camada educacional") completamente ausente, risco real ao Core Value
- **Evidência:** `grep -rn "diversific" server/app/*.py web/src/*.js web/src/*.jsx docs/*.md` — zero ocorrência: nem verbete em `kb.py`, nem aviso na tela de Carteira, nem menção em `conceitos.py`/`skill_ref.py`
- **Verificação:** código
- **Impacto:** um usuário pode concentrar 100% do caixa simulado num único ativo sem qualquer alerta — um dos 13 conceitos obrigatórios do CLAUDE.md nunca é ensinado
- **Recomendação:** adicionar verbete de diversificação a `kb.py` e um aviso na tela de Carteira quando a concentração num ativo passar de um limiar (ex.: >50% do patrimônio).

#### C-06 — "Diário" (Perfil → Logs) é log operacional do agente, não uma jornada de aprendizado do usuário [Baixo]
- **Dimensão:** STORY | **Requisito:** STORY-01 | **Origem:** F-STORY-04
- **Regra aplicada:** D-05 — polimento/consistência, sem risco de produto
- **Evidência:** `web/src/App.jsx:4850-5039` mostra `agent.events` (ex.: "Ciclo (imediato) em 0.0s..."), evidenciado ao vivo; nenhum prompt de reflexão dirigido ao usuário existe no código
- **Verificação:** ao vivo (API real) + código
- **Impacto:** o "registrar o aprendizado" do Passo 8 hoje só existe como telemetria técnica, não como artefato pedagógico — reforça, junto com C-03, que o Passo 8 é o elo mais fraco da jornada
- **Recomendação:** considerar (fase futura) um resumo pós-operação em linguagem simples, distinto do log técnico do agente.

#### C-07 — "Dois nomes Operador" (Operador IA × Modo Operador): faceta narrativa da dívida técnica já documentada [Baixo]
- **Dimensão:** STORY | **Requisito:** STORY-02 | **Origem:** F-STORY-06
- **Regra aplicada:** D-05 — já mitigado por link cruzado (F10-20260807-07); resta a hierarquia implícita
- **Evidência:** `.planning/codebase/CONCERNS.md:59-69` já documenta o achado técnico; nenhuma tela explica que "Operador IA" só funciona DENTRO do Modo Operador (trava só reforçada em `agent.py:566`, nunca comunicada nesse sentido causal)
- **Verificação:** código/docs
- **Impacto:** o usuário pode configurar "Operador IA" sem entender por que ele não age (está fora do Modo Operador). Candidato de fusão com CODE avaliado e NÃO confirmado — ver "Deduplicação" acima
- **Recomendação:** uma frase de link causal nas duas telas ("Operador IA só executa dentro do Modo Operador").

#### C-08 — "Reversão à média" é usada implicitamente (setup IFR2) mas nunca nomeada nem explicada como conceito [Baixo]
- **Dimensão:** STORY | **Requisito:** STORY-03 | **Origem:** F-STORY-08
- **Regra aplicada:** D-05 — mecanismo existe e funciona, falta só a camada didática explícita
- **Evidência:** `server/app/kb.py:802` (`setup-ifr2`) implementa a lógica sem citar o termo "reversão à média"; `grep -n "reversão à média|reversao a media" server/app/kb.py` não retorna nada
- **Verificação:** código
- **Impacto:** o usuário pode operar um setup de reversão à média sem o conceito geral explicado — perde a generalização
- **Recomendação:** adicionar 1-2 frases ao verbete `setup-ifr2` nomeando e explicando o princípio geral.

#### C-09 — Drawdown fica em nível "definição", nunca "decisão" [Baixo]
- **Dimensão:** STORY | **Requisito:** STORY-03 | **Origem:** F-STORY-09
- **Regra aplicada:** D-05 — lacuna real mas de menor risco, já parcialmente coberta
- **Evidência:** `web/src/App.jsx:4808` — única explicação é a legenda "Drawdown = maior queda do pico, em R..."; nenhum ponto do código sugere ação ao usuário
- **Verificação:** código
- **Impacto:** o padrão-alvo do Modo Estudo (indicador→correlação→decisão) não é atingido para este conceito
- **Recomendação:** ao ultrapassar um limiar de drawdown, exibir sugestão educacional (ex.: "considere reduzir o tamanho das próximas posições").

#### C-10 — A frase literal "Não há dados suficientes para concluir" nunca aparece verbatim, apesar do conceito estar implementado [Baixo]
- **Dimensão:** STORY + UX | **Requisito:** STORY-04, UX-04 | **Origem:** F-STORY-10, F-UX-09 (achado fundido — mesma busca textual, mesma conclusão, relatada de forma independente pelos dois planos)
- **Regra aplicada:** D-05 — comportamento subjacente é conforme, só o texto literal diverge
- **Evidência:** busca por "dados suficientes"/"Não há dados" em `server/app/*.py`, `web/src/*.js`, `web/src/*.jsx` não retorna a frase exata; o CONCEITO está implementado sob rótulos diferentes em 3+ camadas independentes: `"n insuficiente"` (`analysis_outcomes.py:109`, `App.jsx:4671-4746`), `"dados insuficientes"` (`fundamentals.py:253-256`, `skill_ref.py:201`), regra 11 do prompt de IA (`skill_ref.py:54`: "Dados insuficientes ⇒ não produza uma leitura definitiva; declare a lacuna"), system prompt do assistente (`assistente.py:103-105,126-132`)
- **Verificação:** código (duas buscas independentes, mesmo resultado)
- **Impacto:** nenhum no comportamento — o usuário sempre vê alguma declaração de insuficiência de dado quando aplicável; risco é só de inconsistência textual entre vozes do produto
- **Recomendação:** padronizar a frase-âncora do CLAUDE.md como rótulo comum entre as superfícies, por consistência de marca, sem urgência.

### 2. UX/UI (UX-01..04)

**Auditoria dos 10 princípios do CLAUDE.md contra telas reais** (conta
`auditoria-ux@local.test`, backend real na porta 8787):

| # | Princípio | Veredito | Achado relacionado |
|---|---|---|---|
| 1 | Saldo fictício visível | conforme | — |
| 2 | Nenhuma ação envia ordens reais | conforme | — |
| 3 | Fonte + horário + natureza do dado exibidos | **violado** | C-11 |
| 4 | Fonte falha → não inventa valor | parcial | C-12 |
| 5 | Cálculo determinístico | conforme | — |
| 6 | IA não promete rentabilidade/certeza | conforme | — |
| 7 | Toda análise de IA informa uso de dado histórico/atrasado/insuficiente | conforme | ver C-10 |
| 8 | Sem linguagem de enriquecimento rápido | conforme | — |
| 9 | Estados completos | parcial | C-14 (ver matriz abaixo) |
| 10 | Acessibilidade, linguagem clara, responsividade, transparência de risco | parcial | C-15, C-16 |

**Matriz de estados** (princípio 9, 4 telas principais — `vazio`,
`erro/fonte indisponível` e `ordem rejeitada` provocados via API real,
demais inferidos do código com a API real que os alimenta):

| Estado | Ativo | Carteira | Operador IA | Perfil |
|---|---|---|---|---|
| Carregamento | OK (skeleton `.sk`, `App.jsx:2908-2912`) | OK (mesmo componente) | OK (`SweepGauge`, `App.jsx:5567`) | OK (`App.jsx:5077,5131`) |
| Vazio | OK (`vazioWatchlist`, `App.jsx:3268`, testado ao vivo) | OK ("Portfólio vazio" + CTA, testado ao vivo) | OK (chips de sugestão, `App.jsx:2464`) | N/A |
| Erro / fonte indisponível | PARCIAL — cotação individual OK; compra com ticker inexistente NÃO é limpa — ver C-12 | OK (mesmo padrão `q.error`) | OK ("IA indisponível" degrada para determinístico, `App.jsx:3420`) | N/A (erros de observabilidade engolidos por design, não generalizar p/ dado financeiro) |
| Mercado fechado | OK — testado ao vivo (`foraDoPregao:true`, rótulo "◌ FORA DO PREGÃO") | N/A direto | Indireto (mesmo dado alimenta o card) | N/A |
| Dado atrasado | PARCIAL — `barraDeOutroDia` tem rótulo dedicado; cotação não expõe idade por ticker na UI do card | N/A | N/A | N/A |
| Ordem rejeitada | OK — testado ao vivo (400 "Caixa insuficiente.", `BuyModal` mostra inline) | N/A direto | N/A | N/A |
| Ordem parcialmente executada | **AUSENTE estruturalmente** — ver C-14 | mesmo | N/A | N/A |
| Operação concluída | OK — testado ao vivo (ciclo compra→venda com `pnl`) | OK (mesmo endpoint) | N/A direto | N/A |

#### C-11 — Rótulo de fonte de dado fixo e incorreto no painel técnico (candlestick/indicadores) [Crítico]
- **Dimensão:** UX | **Requisito:** UX-01 | **Origem:** F-UX-01
- **Regra aplicada:** D-02 — viola o princípio 3 do `CLAUDE.md` ("Dados de mercado exibem fonte, horário da última atualização..."): a fonte exibida não é "a fonte", é uma string fixa que pode estar objetivamente errada
- **Evidência:** `web/src/App.jsx:1511-1513` — `TechnicalModal` renderiza `"Fonte: Yahoo Finance"` como texto literal, sem ler campo de proveniência; `GET /api/technicals/PETR4?period=1y` (testado ao vivo) — o payload NÃO contém nenhum campo `source`/`provedor`; desde a ADR-008 (11/08/2026), brapi é a fonte MASTER de candles diários e Yahoo é backup — o rótulo fixo está provavelmente errado para boa parte das consultas diárias
- **Verificação:** API real (curl autenticado) + leitura do caminho de render
- **Impacto:** o usuário lê "Fonte: Yahoo Finance" mesmo quando o dado veio da brapi — informação de proveniência ativamente falsa, não apenas ausente
- **Recomendação:** propagar `source`/`provedor` do `candle_provider` até o payload de `/api/technicals` (o `candle_cache`/`technical_snapshot` já carregam essa informação para o Radar) e trocar a string fixa por `FONTE_LABEL(data.source)`, com fallback explícito se o campo faltar.
- **Validação humana (checkpoint Task 3, 2026-08-18) — 2 propostas alternativas discutidas e explicitamente descartadas, registradas para não serem re-propostas sem contexto:**
  - **Proposta 1 (descartada) — fonte dupla por finalidade** (brapi só para carteira/watchlist, Yahoo só para o Radar). **Motivo do descarte:** o Radar intraday (15m) JÁ usa Yahoo hoje, automaticamente — `brapi.PLAN_INTERVALS={"1d"}` rejeita 15m antes de tocar rede e cai pro fallback Yahoo sem debitar orçamento (`server/app/brapi.py:28,69-80`, `server/app/candle_provider.py:288-296`). O único uso real de brapi pelo Radar é o scan diário (~74 req/dia, fatia pequena do orçamento mensal) — o ganho de orçamento da proposta seria modesto, não o grande alívio que parecia à primeira vista.
  - **Proposta 2 (descartada) — listbox de configuração para o usuário escolher fonte (brapi/Yahoo) e frequência de atualização, com medidor de cota visível.** **Motivo do descarte:** já foi proposto e rejeitado explicitamente no `docs/adr/008-fonte-de-cotacoes-selecionavel.md`, seção "Alternativas descartadas" ("Escolha de fonte na UI... descartados... usuário sem base para escolher; consumo dobrado sem histórico de divergência; L2 duplicado e failover frio") e item 2 das decisões fechadas do mesmo ADR ("Nada de escolha na UI"). Frequência configurável por usuário também esbarra no ADR-010 (orçamento é por-app, não por-usuário — dar controle de frequência a cada usuário individualmente quebra o modelo de orçamento compartilhado).
  - Severidade mantida Crítico, sem reclassificação — nenhuma das duas propostas altera a evidência ou o impacto do achado original (rótulo ativamente errado).

#### C-12 — Erro de fonte de dado vaza detalhe técnico interno e sai como 500, não 502 limpo [Alto]
- **Dimensão:** UX | **Requisito:** UX-01 | **Origem:** F-UX-03
- **Regra aplicada:** D-03 — comportamento real, atual e reproduzível em produção (testado ao vivo, não hipotético): quebra a convenção do próprio projeto de nunca expor erro opaco ao usuário
- **Evidência:** `POST /api/buy {"t":"XXXXX9","qty":10}` (testado) devolveu HTTP 500 com `{"detail":"HTTPStatusError: ... 'https://query1.finance.yahoo.com/v8/finance/chart/XXXXX9.SA?...crumb=rZaCr5Q9WJs'..."}` — URL do provedor e parâmetro `crumb` vazam; `server/app/candle_provider.py:365-379` (`get_quote`, singular) chama `yahoo.get_quote` sem `try/except`, diferente de `get_quotes` (plural, linhas 382-404) que captura falha por ticker
- **Verificação:** API real (curl autenticado, reproduzido)
- **Impacto:** usuário com ticker mal digitado recebe mensagem técnica ilegível em vez do 502 "Sem cotacao para..." já implementado logo abaixo (`main.py:1508-1510`), que nunca é alcançado porque a exceção interrompe antes
- **Recomendação:** envolver `candle_provider.get_quote` num tratamento que devolva preço nulo em vez de propagar exceção crua, replicando o padrão já usado em `get_quotes`.

#### C-13 — Disclaimer de operação simulada definido mas nunca renderizado no momento da decisão [Médio]
- **Dimensão:** UX | **Requisito:** UX-01 | **Origem:** F-UX-02
- **Regra aplicada:** D-04 — princípio formalmente cumprido em outros pontos da tela (banner global, rótulo "COMPRA SIMULADA"), mas o texto específico de responsabilidade não aparece onde a decisão é tomada
- **Evidência:** `web/src/disclaimers.js:24-26` define `DISCLAIMERS.trade` ("Nenhuma ordem real é enviada a uma corretora") — nenhuma das 7 ocorrências de `DISCLAIMERS.` em `App.jsx` é `.trade` nem `.proposal`; `BuyModal` (`App.jsx:6144-6188`) mostra só o rótulo curto "COMPRA SIMULADA"
- **Verificação:** código (grep dirigido + leitura do componente)
- **Impacto:** no instante de maior atenção do usuário, a garantia explícita "não vai para uma corretora real" não está na tela
- **Recomendação:** renderizar `DISCLAIMERS.trade` no `BuyModal`/`SellModal`, próximo ao botão de confirmação.

#### C-14 — "Ordem parcialmente executada" não existe no modelo de dados [Médio]
- **Dimensão:** UX | **Requisito:** UX-01 | **Origem:** F-UX-04
- **Regra aplicada:** D-04 — princípio 9 lista o estado como obrigatório; a ausência é estrutural
- **Evidência:** `server/app/store.py:530-531` (`buy`) e `:578` (`sell`) — toda ordem executa 100% ou é rejeitada inteira (`main.py:1512-1513`); "Venda parcial" na UI é escolha do usuário de vender uma fração, semanticamente diferente do fill parcial de mercado que o princípio pede
- **Verificação:** código — não há caminho de API para provocar esse estado porque ele não existe
- **Impacto:** nenhum usuário verá esse estado porque o motor não o produz; suposição de cobertura completa do princípio 9 seria incorreta
- **Recomendação:** decisão de produto — declarar explicitamente (copy/doc) que a simulação é "tudo ou nada" por desenho, defensável pelo princípio 5 (determinismo).

#### C-15 — Toggle "acordeão" com `role="button"` não responde a teclado [Médio]
- **Dimensão:** UX | **Requisito:** UX-03 | **Origem:** F-UX-06
- **Regra aplicada:** D-04 — risco real de exclusão de usuário que navega por teclado/leitor de tela
- **Evidência:** `web/src/App.jsx:2706,2773` — `<div onClick={onToggle} role="button" tabIndex={0}>`; busca por `onKeyDown|onKeyPress` no arquivo inteiro encontra 1 única ocorrência em 7599 linhas (`App.jsx:6098`, não relacionada)
- **Verificação:** código (grep dirigido + leitura dos dois pontos de uso)
- **Impacto:** usuário por teclado/leitor de tela consegue focar o toggle mas não ativá-lo — a seção nunca abre por teclado
- **Recomendação:** trocar por `<button>` nativo ou adicionar `onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onToggle()}`.

#### C-16 — `textFaint` abaixo do mínimo de contraste WCAG AA para texto pequeno, nos dois temas [Médio]
- **Dimensão:** UX | **Requisito:** UX-03 | **Origem:** F-UX-07
- **Regra aplicada:** D-04 — risco real de legibilidade para usuário com baixa visão
- **Evidência:** `web/src/App.jsx:70,87` — `textFaint: "#6f7797"` (escuro) sobre `bgBase: "#10121a"` = 4.24:1; `textFaint: "#7a8099"` (claro) sobre `bgBase: "#f7f8fc"` = 3.68:1 (mínimo AA 4,5:1 para texto normal). Usado em rótulos de fonte (`2927,2936`), timestamps, disclaimers auxiliares, mensagens de erro secundárias (`2367,4595,4698,5077,5131`)
- **Verificação:** cálculo real a partir dos hex do tema (luminância relativa WCAG 2.x) — não medição em tela renderizada
- **Impacto:** usuário com baixa visão ou uso mobile ao ar livre pode não conseguir ler informação de proveniência do dado e mensagens de erro secundárias
- **Recomendação:** escurecer/clarear `textFaint` até ≥4.5:1 nos dois temas, ou reservar a cor a texto ≥14px em negrito.

#### C-17 — Troca de modo força reload completo do app [Baixo]
- **Dimensão:** UX | **Requisito:** UX-02 | **Origem:** F-UX-05
- **Regra aplicada:** D-05 — polimento de fluxo; a própria implementação documenta a intenção deliberada (evitar mistura de vocabulário)
- **Evidência:** `web/src/App.jsx:1849` — flash + reload completo a cada troca de `appMode`
- **Verificação:** código/docs (comentário do próprio arquivo confirma a intenção)
- **Impacto:** perda de contexto de navegação a cada troca — fricção real, trade-off consciente
- **Recomendação:** se a fricção incomodar em uso real, considerar re-render local preservando a tela atual; baixa prioridade.

#### C-18 — Gate "Executar" desabilitado: aviso visível existe, mas sem vínculo semântico (`aria-describedby`) [Baixo]
- **Dimensão:** UX | **Requisito:** UX-03 | **Origem:** F-UX-08
- **Regra aplicada:** D-05 — o defeito original (só `title`, invisível em toque) já foi corrigido; resta um refinamento de acessibilidade
- **Evidência:** `web/src/App.jsx:3780-3799` — botão "Executar" fica `disabled` fora do Operador e um parágrafo abaixo explica o motivo com link — falta só `aria-describedby` ligando o botão ao parágrafo
- **Verificação:** código (leitura direta do JSX, comparado com CONCERNS.md)
- **Impacto:** leitor de tela que navegue direto ao botão não ouve o motivo (informação está na tela, só não amarrada semanticamente)
- **Nota de dedup:** candidato de fusão com C-23 (F-CODE-07, mesma família "gate mudo", controle diferente) avaliado e NÃO confirmado como fusão — ver "Deduplicação" acima
- **Recomendação:** adicionar `aria-describedby` no botão apontando para o `id` do parágrafo explicativo.

### 3. Código / dívida técnica (CODE-01..04)

**Mapa de recomputação de `appMode`** (`grep -n "appMode" web/src/App.jsx`, 26
ocorrências — a lista do `CONCERNS.md` está desatualizada, o arquivo mudou de
tamanho desde então): 12 leituras/recomputações independentes de valor + 2
escritas + 4 comentários + 5 reusos da variável local de `App()` + 1 definição
canônica (`ctx.operador`, linha 7220) + 2 reusos dessa definição. Das 12
leituras, 10 usam o padrão ternário seguro (`=== "operador" ? "operador" :
"estudo"`, linhas 1624, 1828, 2018, 3188, 4224, 5606, 5756, 6319, 6862, 7220),
2 usam passthrough cru `|| "estudo"` (linhas 6501, 7411). **Nenhum ponto
apresenta risco REAL de divergência hoje** — as duas únicas rotas de escrita
do código (1834, 1897) só produzem `"estudo"`/`"operador"`, nunca um terceiro
valor.

**Os 3 bugs históricos, causa raiz verificada linha a linha** (não
"appMode recomputado", como o `CONCERNS.md` atribui tematicamente):
1. Stop/alvo apagava sozinho → `blur` de campo vazio salvava `null` sem
   confirmação (não leitura de `appMode`). Guardião: `test_posicao_stop_alvo.mjs`
   (cobre o sintoma exato).
2. Carteira nativa dessincronizada → `deviceStore.buy/sell/putPosition` eram
   100% locais (gap de paridade — território de C-20). Guardião:
   `test_carteira_nativa_sincroniza.mjs` (não executável nesta verificação —
   ver C-24).
3. Ciclo do agente não reagia a gatilho recém-armado → ausência de disparo
   imediato (não leitura de `appMode`). Guardião:
   `test_ciclo_imediato_apos_carteira.py` (cobre a causa raiz específica, o
   mais robusto dos 3).

**Paridade `deviceStore`×`serverStore`:** 58 métodos em cada lado, 0
assimetrias de NOME hoje (1 diferença de assinatura intencional,
`_setDeviceScope`). 7 métodos/campos têm guardião dedicado de paridade
(`scanDeep`/`scanDeepEstimate`, `conceitos`/`conceito`/`assistente`,
`syncPushPrefs`, `analysisOutcomesStats`/`Csv`, `petResumo`, `scan`,
`putConfig` — parcial, é guardião de comportamento não de nome). **28 dos 58
métodos têm ZERO referência em qualquer teste** (`_localSeed`,
`_setDeviceScope`, `adminMobileHandoff`, `agentLog`, `agentRunNow`,
`agentStatus`, `aiActivity`, `aiQuota`, `analyzeOption`, `cachedTechnicals`,
`cycle`, `kbBuscar`, `obsLogs`, `optionsBuy`, `optionsChain`,
`optionsExpirations`, `optionsGate`, `optionsSell`, `pushAnalysisLog`,
`putLlmPrompts`, `putOptionPosition`, `putProfile`, `putSkill`, `putSnapshot`,
`restoreSkill`, `scanProgress`, `technicals`, `testConfig`).

**Cobertura dos fluxos financeiros críticos:**

| Fluxo | Cobertura | Camada | Lacuna | Severidade |
|---|---|---|---|---|
| 1. Execução de ordem (compra/venda) | `test_fase2_portfolio.py`, `test_ciclo_imediato_apos_carteira.py`, `test_automacao.py`, `test_agent.py` | unit + integração (só sucesso) | Rejeição em `/api/buy`/`/sell` sem nenhum teste de rota — ver C-25 | Média |
| 2. PnL / preço médio / drawdown | `test_fase2_portfolio.py`, `test_persistence.py::test_snapshot_curva_retorno_drawdown`, `test_finance.mjs` | unit | Recompra após venda parcial sem teste de reponderação — ver C-26 | Média |
| 3. Falha da fonte de dados (200 com zero velas) | `test_candle_provider.py` (20+ testes) | unit, fetcher injetável | Nenhuma identificada — cobertura adequada | Baixa |
| 4. Dado atrasado (tríade temporal) | `test_timing.py` (20+ testes) | unit | Nenhuma identificada — cobertura adequada | Baixa |
| 5. Ordem rejeitada (gate de modo) | `test_agent_modo_estudo.py::test_agent_params_forca_sinalizar_fora_do_operador` | unit (gate) | Rejeição de `/api/buy`/`/sell` por caixa/cotação — mesma lacuna do fluxo 1 | Média |

#### C-19 — Guardiões dos 3 bugs históricos travam o sintoma corrigido, não a classe do erro [Alto]
- **Dimensão:** CODE | **Requisito:** CODE-01 | **Origem:** F-CODE-03
- **Regra aplicada:** D-03 — os 3 bugs já causaram incidente real documentado (`docs/auditoria-controle-ordens-parametros.md`); o padrão-classe ("estado que muda num lugar que outro não vê") permanece sem barreira estrutural
- **Evidência:** `web/tests/test_posicao_stop_alvo.mjs` (bug 1, só o blur vazio), `web/tests/test_carteira_nativa_sincroniza.mjs` (bug 2, não executável nesta verificação), `server/tests/test_ciclo_imediato_apos_carteira.py` (bug 3, cobre a causa raiz)
- **Verificação:** código + suíte executada (bug 3); bug 2 não pôde ser exercitado (ambiente)
- **Impacto:** uma variante nova do mesmo padrão-classe passaria pelos 3 guardiões existentes sem disparar nenhum
- **Recomendação:** não é escopo desta fase implementar, mas "card de status único" + teste genérico de paridade (C-20) são os dois mecanismos estruturais pendentes.

#### C-20 — Paridade `deviceStore`×`serverStore`: nomes 100% iguais hoje, mas 28 de 58 métodos (48%) sem NENHUMA referência em teste, sem guardião genérico exaustivo [Alto]
- **Dimensão:** CODE | **Requisito:** CODE-02 | **Origem:** F-CODE-04
- **Regra aplicada:** D-03 — a lacuna de paridade já foi causa raiz de 2 incidentes documentados (carteira nativa não sincronizava, F10-20260807-05; `initialBudget` sem sync device→servidor, F10-20260809-05). Aplicando a régua com o histórico, não com o estado atual (hoje simétrico)
- **Evidência:** ver tabelas acima (0 assimetrias de nome hoje, 28/58 sem referência em teste)
- **Verificação:** código (comparação estática + busca por referência; nenhum teste novo escrito)
- **Impacto:** método novo adicionado a só um dos 2 stores só é pego hoje se o autor lembrar de escrever teste pontual — não existe teste que rode `Object.keys` nos dois objetos e falhe em qualquer assimetria não documentada
- **Recomendação:** teste genérico único (padrão já usado pelos guardiões pontuais) que extraia as chaves de `serverStore()`/`deviceStore()` e falhe em qualquer assimetria — complementa, não substitui, os testes pontuais existentes.

#### C-21 — `ctx.operador` existe desde 2026-08-07 mas 10 de 12 pontos de leitura de `appMode` continuam recalculando de forma independente [Médio]
- **Dimensão:** CODE | **Requisito:** CODE-01 | **Origem:** F-CODE-01
- **Regra aplicada:** D-04 — risco real (dois padrões de normalização coexistem), sem incidente documentado causado especificamente por esta inconsistência. **Ver "Nota de calibração" na Metodologia**: este achado discorda deliberadamente do exemplo textual do `01-CONTEXT.md` (que cita os 3 bugs como Alto/D-03), com base em evidência de código — nenhum dos 3 bugs foi causado por divergência de leitura de `appMode` no mesmo render. Julgamento de calibração explícito, submetido à confirmação do Alex no checkpoint (Task 3)
- **Evidência:** `web/src/App.jsx:7214-7220` (definição de `ctx.operador`, comentário "Novo código deve ler `ctx.operador`") vs. 10 leituras independentes (linhas 1624, 1828, 2018, 3188, 4224, 5606, 5756, 6319, 6501, 6862, 7411 — a de 1828 é a própria tela de troca, sem risco; a de 6319 é a origem, não cópia)
- **Verificação:** código (grep + leitura linha a linha das 26 ocorrências)
- **Impacto:** hoje nenhum. Se uma tela nova ler `data.config.appMode` com uma terceira variante de normalização, não há lint/teste que force `ctx.operador` — a convenção depende só do comentário
- **Recomendação:** migrar os 8 pontos de recomputação redundante para `ctx.operador` (mecânico, sem mudança de comportamento) e considerar teste estático (regex, padrão já usado nos guardiões de paridade) que falhe se `data.config.appMode` for lido fora de `App()`/`ctx.operador`.
- **Validação humana (checkpoint Task 3, 2026-08-18):** Confirmado pelo Alex em validação humana — sem memória de incidente adicional causado por esta divergência, fora dos 3 bugs já documentados e já avaliados como não causados por leitura divergente de `appMode` no mesmo render. Severidade mantida Médio, sem reclassificação.

#### C-22 — `default_skill_text()`/`defaultSkillText()` (prompt padrão do Modo Estudo) sem NENHUM guardião, diferente do par `carteiraStopAlvo*` que é byte-exato [Médio]
- **Dimensão:** CODE | **Requisito:** CODE-02 | **Origem:** F-CODE-05
- **Regra aplicada:** D-04 — risco real de drift silencioso de texto educacional entre Python e JS
- **Evidência:** `server/app/defaults.py:22` e `web/src/catalog.js:54`; o guardião existente (`test_a8ii_paridade_defaults_carteira_com_catalog_js`) só compara `carteiraStopAlvo*`; `test_copy_theme.mjs:160-161` verifica só se os dois arquivos CONTÊM a substring `defaultSkillTextOperador`/`default_skill_text_operador` (marcador de presença), e nem essa checagem cobre a versão sem `Operador`
- **Verificação:** código
- **Impacto:** o texto que define a persona/skill do Modo Estudo pode divergir entre app nativo e servidor sem que nenhum teste detecte
- **Recomendação:** estender `test_a8ii_paridade_defaults_carteira_com_catalog_js` (ou criar par equivalente) para `default_skill_text`/`defaultSkillText`.

#### C-23 — Toggle mestre de "Entrada automática" não tem atributo HTML `disabled` nem feedback próprio — reintroduz uma instância residual do defeito original [Médio]
- **Dimensão:** CODE | **Requisito:** CODE-03 | **Origem:** F-CODE-07
- **Regra aplicada:** D-04 — comportamento funcional correto (não liga sozinho fora do Operador), o que falha é o feedback. Severidade Médio, não Baixo como C-18 (mesma família "gate mudo"): a diferença de impacto é que este gap afeta QUALQUER usuário (o Toggle fica visualmente clicável, sem `disabled` styling, sem toast ao toque), não só quem navega por leitor de tela como em C-18, onde o botão já é visualmente `disabled` e só falta o vínculo semântico
- **Evidência:** `web/src/App.jsx:3924` — `<Toggle on={!!ag.entradaAuto && operador} onClick={() => operador && putAg(...)} .../>`; o componente `Toggle` (`App.jsx:310-318`) não recebe nem aplica prop `disabled`. Blast radius medido: dos 2 controles gateados por `appMode`/`operador` na tela (botão Executar `3788`, slider `allocPct` `3931`), ambos têm `disabled` HTML + parágrafo com link — o Toggle da linha 3924 é o ÚNICO sem `disabled`
- **Verificação:** código (`grep -n "disabled="` e `"title="`, contagem e cruzamento manual)
- **Impacto:** usuário sighted que toque no Toggle fora do Operador não recebe NENHUM feedback visual de que está inerte
- **Recomendação:** aplicar `disabled={!operador}` (mesmo padrão do slider `allocPct` logo abaixo) — uma linha, sem mudança de lógica de negócio.

#### C-24 — Suíte canônica: 970/970 testes de backend passaram; 7 de 74 testes web falharam por dependência de ambiente ausente, não regressão — e os 7 incluem os guardiões dos 2 incidentes de paridade documentados [Médio]
- **Dimensão:** CODE | **Requisito:** CODE-04 | **Origem:** F-CODE-08
- **Regra aplicada:** D-04 — risco real de processo (verificação num worktree novo pode reportar "suíte com falhas" sem perceber que são de ambiente — e são exatamente os testes de maior valor que ficam sem cobertura)
- **Evidência:** `bash scripts/executar.sh --testes` — backend: `970 passed, 129 warnings`; web: 67 OK, 7 falharam (`test_appmode_sincroniza_servidor.mjs`, `test_carteira_nativa_sincroniza.mjs`, `test_fase2_portfolio.mjs`, `test_notif_central.mjs`, `test_notify.mjs`, `test_oauth_repassa_name_e_code.mjs`, `test_pet_resumo_modo_web.mjs`); todos com o MESMO erro `ERR_MODULE_NOT_FOUND: '@capacitor/core'`; confirmado `web/node_modules/` inexistente neste worktree
- **Verificação:** suíte executada + reprodução isolada de cada falha + confirmação da causa
- **Impacto:** não foi possível confirmar empiricamente que os guardiões dos bugs #2 (carteira nativa) e de sincronização de `appMode` ainda protegem o código nesta execução específica; não há evidência de regressão real (erro 100% de resolução de módulo)
- **Recomendação:** não corrigido nesta fase (instalar pacote excluído de auto-fix). Documentar como pré-requisito operacional: qualquer execução da suíte num checkout/worktree novo precisa `npm install` em `web/` ANTES de `scripts/executar.sh --testes`.

#### C-25 — Rejeição de ordem em `/api/buy`/`/api/sell` (caixa insuficiente, ticker sem cotação, ticker inválido) sem NENHUM teste de rota HTTP [Médio]
- **Dimensão:** CODE | **Requisito:** CODE-04 | **Origem:** F-CODE-09
- **Regra aplicada:** D-04 — risco real (mensagens/códigos de rejeição podem regredir sem detecção)
- **Evidência:** `server/app/main.py:1502-1518` — 3 caminhos de rejeição (`400 Ticker invalido`, `502 Sem cotacao`, `400 Caixa insuficiente`); `grep -rln "Caixa insuficiente|Sem cotacao para|Ticker invalido" server/tests/*.py` — zero arquivos; único teste que chama `/api/buy`/`/sell` só exercita o caminho de sucesso
- **Verificação:** código (grep + leitura de `main.py`)
- **Impacto:** regressão que trocasse status (400→500) ou ordem das validações passaria por toda a suíte sem detecção
- **Recomendação:** 2-3 testes `TestClient` no padrão já usado (banco temporário, reimport de `app.main`): caixa insuficiente, ticker sem cotação, ticker inválido.

#### C-26 — Recompra após venda parcial: preço médio reponderado não tem teste [Médio]
- **Dimensão:** CODE | **Requisito:** CODE-04 | **Origem:** F-CODE-10
- **Regra aplicada:** D-04 — risco real em cálculo financeiro (preço médio afeta PnL exibido)
- **Evidência:** `server/app/store.py:539` — reponderação roda em toda compra que encontra posição existente, incluindo pós-venda-parcial; `test_sell_parcial_reduz_qty_e_preserva_preco_medio` cobre a venda parcial isolada, mas nenhuma sequência `buy → sell parcial → buy` foi encontrada em 4 arquivos de teste
- **Verificação:** código (leitura de `store.py` + busca em 4 arquivos de teste)
- **Impacto:** bug futuro na fórmula de reponderação passaria pela suíte sem detecção
- **Recomendação:** teste `buy(100@30) → sell(qty=40) → buy(60@40)` e assert do `avg` resultante (médias 60 remanescentes a 30 com 60 novas a 40 = 35, não a média das 160 cotas originais).

#### C-27 — Ausência de E2E/browser automation na suíte canônica [Médio]
- **Dimensão:** CODE | **Requisito:** CODE-04 | **Origem:** achado sem número `F-` (seção "Lacunas estruturais conhecidas", `FINDINGS-CODE.md`)
- **Regra aplicada:** D-04 — risco real e recorrente pelo próprio histórico do projeto, sem se materializar necessariamente em CADA release
- **Evidência:** `TESTING.md`: "E2E tests: not present"; a própria memória do projeto registra bugs "que só a verificação ao vivo pegou" (ex.: toque longo em setores, F10-20260807)
- **Verificação:** código/docs
- **Impacto:** nenhum teste exercita a sequência completa escolher ativo → ordem → execução → resultado como o usuário realmente vive
- **Recomendação:** avaliar E2E leve (Playwright/similar) para o roteiro dos 8 passos da Experiência Principal, fora do escopo desta fase diagnóstica.

#### C-28 — Os 2 pontos com normalização "passthrough" (`|| "estudo"`) divergem estruturalmente do padrão ternário e alimentam a IA/API sem normalização [Baixo]
- **Dimensão:** CODE | **Requisito:** CODE-01 | **Origem:** F-CODE-02
- **Regra aplicada:** D-05 — nenhuma sequência de eventos observável produz hoje um valor fora de `{"estudo","operador",undefined}`; polimento, não risco materializável
- **Evidência:** `web/src/App.jsx:6501` (`modoApp` enviado a `store.conceitos`) e `:7411` (`modo` no snapshot ao assistente)
- **Verificação:** código
- **Impacto:** nenhum hoje; se as regras de escrita de `appMode` mudarem, estes 2 pontos propagariam valor bruto em vez de normalizar
- **Recomendação:** trocar `|| "estudo"` pelo mesmo ternário usado no resto do arquivo.

#### C-29 — Ausência de medição numérica de cobertura de testes [Baixo]
- **Dimensão:** CODE | **Requisito:** CODE-04 | **Origem:** achado sem número `F-` (seção "Lacunas estruturais conhecidas", `FINDINGS-CODE.md`)
- **Regra aplicada:** D-05 — disciplina de "toda regressão vira guardião" mitiga bem na prática (970 testes de backend); lacuna de FERRAMENTA, não de disciplina observada
- **Evidência:** sem `pytest-cov`; `web/tests` sem equivalente
- **Verificação:** código/docs
- **Impacto:** a suíte pode ter buracos que ninguém enxerga por falta de número comparável entre releases
- **Recomendação:** avaliar `pytest-cov` como item de baixa prioridade, fora do escopo desta fase.

**Nota — Verificado e conforme relevante desta dimensão está na seção
"Verificado e conforme" ao final (F-CODE-06, suíte de backend, falha silenciosa
da fonte de dados, tríade temporal, gate de modo no ciclo automático).**

### 4. Gating de monetização (GATE-01..03)

**Estado dos hooks de gate:**

| Hook | Retorna hoje | Quem chama | O que falta |
|---|---|---|---|
| `current_plan` (`plan.py:41`) | Resolve `users.plan` corretamente por usuário | **NINGUÉM** — zero call sites fora da própria definição | Nada tecnicamente pronto; falta ser plugado nos 3 call sites de gate |
| `plan_at_least` (`plan.py:52`) | `bool` de índice em `_ORDEM_PLANO` | **NINGUÉM** (docstring confirma: "nenhuma rota usa isto ainda") | Nenhum `require_plan()`/decorator existe para consumir |
| `can_add_ticker` (`plan.py:63`) | `(True, None)` sempre — `max_watchlist` é `None` | `main.py:870`, sem passar `plan=` — cai no fallback `ACTIVE_PLAN` global | `PLAN_FREE["max_watchlist"]` virar número **e** call site passar `plan=current_plan(user)` |
| `can_analyze` (`plan.py:73`) | `(True, None)` sempre — call sites passam `0` hardcoded | `main.py:1223,1370`, `plan.can_analyze(0)` (comentário admite "FUTURO: passar a contagem") | contador mensal real, call sites pararem de hardcodar `0`, decidir relação com `metering.check` |
| `requires_subscription` (`plan.py:83`) | `False` sempre | **NINGUÉM** | Mecanismo de validação de recibo de loja (App Store/Google Play) server-side inteiro — inexistente |

**Veredito `can_analyze` × `metering.check`:** duas implementações concorrentes
do mesmo conceito na mesma requisição — `plan.can_analyze(0)` (sempre libera)
roda antes de `metering.check(...)` (quota diária real) na mesma chamada de
`/api/analyze/{ticker}` e `/api/technical/analyze/{ticker}`. Ativar `can_analyze`
sem reconciliar com `metering.check` criaria dois contadores independentes
respondendo pela mesma pergunta.

**Veredito `ACTIVE_PLAN` global vs. `current_plan(user)` por usuário:** mesmo
que `users.plan = 'pro'` esteja persistido no banco, os gates atuais NUNCA
leriam esse valor — `current_plan(user)` nunca é chamado em lugar nenhum do
código. Ligar `PLAN_FREE["max_watchlist"]=10` hoje bloquearia igualmente
contas `'pro'`. É reescrita pequena (3 call sites + 1 import), mas é reescrita
de código, não configuração.

**Cota física × cap comercial:**

| Eixo | Onde é calculado | Escopo | O que o usuário vê quando estoura | Confunde com o outro? |
|---|---|---|---|---|
| Cota física brapi | `brapi_budget.py` (`cota_mes`, `teto_dia`, `fatia_limite`, `degradado`) | Compartilhada por TODA a base (15k/mês) | **NADA** — sem painel para usuário comum, nem alerta ativo para admin | Não no texto, mas por OPACIDADE total do primeiro eixo — ver C-30 |
| Cap comercial de IA (gerenciada) | `metering.py` (`check`, `consume`); `managed.py` (`daily_quota`, `global_daily_cap`) | Por conta (`user_id`) | Texto do 402 explícito, sugere BYOK como alternativa | Não — vocabulário próprio |

**Features candidatas a tier pago:** IA gerenciada com cota maior (esforço
baixo-médio, bloqueio: decisão comercial + F-GATE-01), ajuste de intervalo de
cotação (esforço alto, mecanismo inexistente — variável global de módulo, não
por usuário), alvo dinâmico (esforço baixo, per-conta já hoje, depende de
F-GATE-01 + decisão comercial), recorte de eficiência da IA (esforço baixo na
superfície, mas depende de `requires_subscription` sair do estado sempre
`False`).

#### C-30 — Estado `degradado` da cota brapi é invisível para usuário E admin, violando o princípio 3 do CLAUDE.md [Crítico]
- **Dimensão:** GATE | **Requisito:** GATE-02 | **Origem:** F-GATE-04
- **Regra aplicada:** D-02 — viola o princípio 3 obrigatório ("Dados de mercado exibem fonte, horário da última atualização e se são em tempo real, atrasados ou históricos")
- **Evidência:** `server/app/candle_provider.py:338` — `return base * 3 if brapi_budget.degradado("spot") else base` triplica o TTL do cache de spot sem nenhum sinal externo; `grep` confirma que `degradado(` só é chamado nesse ponto interno; o único campo exposto à UI, `candles.alerta` (`App.jsx:5316-5317`, admin-only), mede taxa de FALHA do provedor, métrica diferente do estado de ORÇAMENTO
- **Verificação:** código
- **Impacto:** quando uma fatia do orçamento mensal passa de 80%, os dados ficam até 3x mais desatualizados e nem usuário nem admin recebem qualquer indicação — nenhum timestamp, badge ou texto reflete o TTL estendido; acontece sistematicamente (todo mês, ao se aproximar do teto), não é hipotético
- **Recomendação:** expor o estado `degradado` por fatia no payload já consumido por `FonteDadosScreen`/`/api/obs/usage`, e refletir no timestamp/label de "última atualização" quando o TTL estendido estiver ativo.

#### C-31 — Hooks de gate nunca resolvem o plano por usuário; `current_plan` é código órfão [Alto]
- **Dimensão:** GATE | **Requisito:** GATE-01 | **Origem:** F-GATE-01
- **Regra aplicada:** D-03 — bloqueia decisão de negócio pendente: mesmo com o número comercial decidido, ligar o cap hoje não respeitaria diferenciação `free`/`pro` por conta
- **Evidência:** `server/app/plan.py:66,76` (`plan = plan or ACTIVE_PLAN`); `main.py:870,1223,1370` chamam os hooks sem `plan=`; zero chamadas de `current_plan(` fora da própria definição
- **Verificação:** código
- **Impacto:** quando `PLAN_FREE` ganhar limite numérico, TODAS as contas — inclusive `'pro'` — cairiam no mesmo limite do global
- **Recomendação:** nos 3 call sites, passar `plan=plan.current_plan(user)` em vez de deixar cair no fallback global.

#### C-32 — `can_analyze` e `metering.check` são gates concorrentes na mesma requisição [Alto]
- **Dimensão:** GATE | **Requisito:** GATE-01 | **Origem:** F-GATE-02
- **Regra aplicada:** D-03 — bloqueia decisão pendente: ativar o passo 2 do ADR-010 sem reconciliar os dois mecanismos duplica a lógica de contagem
- **Evidência:** `main.py:1223,1367-1370` (`plan.can_analyze(0)`) e `main.py:367` (`metering.check(...)`, dentro de `_ai_apply_managed`) — ambos na MESMA chamada de `/api/analyze/{ticker}` e `/api/technical/analyze/{ticker}`
- **Verificação:** código
- **Impacto:** alimentar `can_analyze` com contador real, seguindo literalmente o passo 2 do ADR-010, sem reconciliar com `metering.check`, cria dois contadores independentes — risco de UX confusa e contagem duplicada
- **Recomendação:** decidir explicitamente se `can_analyze` vira wrapper fino sobre `metering.check` antes de alimentá-lo com contador real.

#### C-33 — `can_add_ticker`/`can_analyze` são chamados com dado hardcoded, não com o estado real do usuário [Médio]
- **Dimensão:** GATE | **Requisito:** GATE-01 | **Origem:** F-GATE-03
- **Regra aplicada:** D-04 — risco real, ainda não materializado porque limite=`None` hoje torna irrelevante, mas quebraria silenciosamente se o número comercial fosse ligado sem tocar o call site
- **Evidência:** `main.py:1370` — `plan.can_analyze(0) # FUTURO: passar a contagem do mes do usuario`; `App.jsx:6627` — mesmo comentário no espelho front
- **Verificação:** código
- **Impacto:** popular `PLAN_FREE.max_analyses_per_month` sem tocar os call sites faria o gate comparar `0 >= limite` sempre — bloqueia todo mundo ou ninguém, dependendo da ordem de avaliação
- **Recomendação:** os call sites (backend e front) precisam calcular a contagem real do mês corrente antes do gate virar operacional.

#### C-34 — Painel de orçamento brapi é 100% admin-only; usuário comum não tem visibilidade do eixo físico de cota [Médio]
- **Dimensão:** GATE | **Requisito:** GATE-02 | **Origem:** F-GATE-05
- **Regra aplicada:** D-04 — risco real de opacidade, ainda não incidente documentado — distinto de C-30, que é a violação ativa do princípio quando o estado degradado ocorre
- **Evidência:** `App.jsx:5201` (comentário "cotações: só admin") e `:5372-5375`; `server/app/brapi_budget.py:170-189` (`snapshot()`, já real e persistido, cobre tanto o estado NORMAL quanto o degradado) exposto hoje só via `GET /api/obs/usage` (`server/app/main.py:449-472`), protegido por `require_permission("observabilidade.ver")` — nenhuma superfície de `web/src/App.jsx` voltada ao usuário final lê esse payload
- **Verificação:** código
- **Impacto:** combinado com C-30, significa que não existe NENHUM canal, nem admin nem usuário, que sinalize em tempo real quando o app está em modo degradado. Isto vale tanto para o estado degradado quanto para o consumo NORMAL (percentual do orçamento mensal já usado) — o usuário nunca vê nenhum dos dois, só a cota de IA (`/api/ai/quota`)
- **Recomendação:** não é necessário expor orçamento bruto ao usuário final, mas o efeito do degradado (dado mais velho) precisa aparecer no timestamp que o usuário já vê — mesma mudança de C-30 resolve as duas questões. **Se algum dia um medidor de consumo (consumo × limite) for exposto ao usuário final** (preventivo, antes de bater o degradado), o texto precisa deixar claro que é o consumo do APP INTEIRO (orçamento compartilhado, ADR-010), não uma cota pessoal dele — senão cria confusão nova com a cota de IA por conta que ele já vê em `/api/ai/quota`.
- **Validação humana (checkpoint Task 3, 2026-08-18):** durante o checkpoint, foi levantada a hipótese de um "medidor de orçamento da brapi visível ao usuário" como achado novo. Avaliado com o mesmo critério de deduplicação da Task 1 e confirmado que **este achado (C-34/F-GATE-05) já cobre exatamente esse fato** ("o usuário comum nunca vê o orçamento brapi, nem em estado normal, nem degradado" — texto original de `F-GATE-05` em `FINDINGS-GATE.md`) — não é um achado novo, é o mesmo achado com evidência adicional (`brapi_budget.py:170-189`, `main.py:449-472`) e uma recomendação estendida (nota sobre app-wide vs. cota pessoal, acima). Não recebeu `C-NN` próprio nem foi fundido em C-30 (que é especificamente sobre o estado degradado, Crítico) — C-34 (Médio) permanece o achado correto para a visibilidade geral do eixo físico de cota. Severidade mantida Médio, sem reclassificação.

### 5. Portal de administração/observabilidade (ADMIN-01..03)

**Aba × permissão × rota × gate de backend** (10 abas do `web-admin/`): as 9
abas com campo `perm` batem exatamente com o gate de backend
(`require_permission`) — nenhuma divergência de gate encontrada. A aba
"Auditoria" não tem `perm` no front (por desenho, qualquer papel
administrativo libera), mas o backend exige `require_any_admin_permission()`
— não é escalada de privilégio, é inconsistência de rótulo (ver C-39).

**Replay do incidente do kill-switch** (ligado sem querer, parou a execução
automática de TODA a base por 2,5 dias — o heartbeat continuava batendo,
mascarando "vivo, mas parado" como "vivo, normal"):

| Momento | Sinal disponível hoje | Alguém seria notificado? | Lacuna |
|---|---|---|---|
| T0 — kill-switch ligado | Sim, na hora (`admin_config`+`admin_audit_log`) | **Não** — passivo, só quem abrir a tela vê | Nenhum alerta ativo — ver C-37 |
| T0+1h — 1º pregão sem execução | Indireto ("Ordens por origem"), sem baseline "deveria ter N" | **Não** — passivo | Não há alerta de "zero execuções com Operador habilitado" |
| T0+1 dia | Heartbeat continua "vivo" (KPI verde) enquanto kill-switch fica "LIGADO" (KPI separado) | **Não** — 2 KPIs coexistem sem contradição visual | Nenhuma correlação automática entre "laço vivo" + "kill-switch ligado" |
| T0+2,5 dias — descoberta manual | Mesmos sinais, 100% passivos | **Não** — descoberta real foi manual; dados corretos já estavam lá | Confirma C-37: falta o mecanismo ATIVO |

#### C-35 — Segundo kill-switch (`timing_watch`) invisível no portal e sem toggle em runtime [Alto]
- **Dimensão:** ADMIN | **Requisito:** ADMIN-02 | **Origem:** F-ADMIN-01
- **Regra aplicada:** D-03 — o kill-switch é o exemplo literal citado na régua; o portal existir e mesmo assim não mostrar UM dos dois interruptores é o mesmo padrão de risco que já causou o incidente de 2,5 dias, agora numa superfície irmã
- **Evidência:** `server/app/timing_watch.py:39,58-59` — `kill_switch_on()` lê só env, sem o padrão memória→DB→env que `agent.kill_switch_on()` já tem (`agent.py:173-204`); `web-admin/src/App.jsx:96` — KPI "KILL-SWITCH" lê só `agent_mod.status_snapshot()`; `grep -rn "timing_watch" server/app/main.py` não retorna nenhuma rota que exponha `timing_watch.kill_switch_on()`
- **Verificação:** código/docs
- **Impacto:** se `B3_TIMING_PUSH_KILL=1` for ligado (redeploy/env do Railway), o push do gatilho para para TODA a base e nenhuma das 10 abas mostra isso — este só pode ser desligado por redeploy
- **Recomendação:** estender o padrão memória→DB→env para `timing_watch.kill_switch_on()` (rota admin própria sob `execucao_automatica.controlar`) e adicionar 2º KPI "PUSH DO GATILHO: ligado/desligado" na Visão Geral.

#### C-36 — Painel de custos mostra `erros` mas nunca `vazios`/`alerta`/`taxaFalha` — cego para o modo de falha que já aconteceu em produção [Alto]
- **Dimensão:** ADMIN | **Requisito:** ADMIN-02 | **Origem:** F-ADMIN-02
- **Regra aplicada:** D-03 — já causou incidente real documentado: 31/07/2026, Yahoo devolveu HTTP 200 com zero velas por 2 horas de pregão aberto; a taxa de "erro" ficaria em 0,00 e nenhum KPI do portal hoje mostraria isso
- **Evidência:** `server/app/candle_provider.py:98-141` (`snapshot()`) já calcula `vazios`, `falhas`, `taxaFalha`, `alerta` e devolve no payload de `/api/obs/usage`; `web-admin/src/App.jsx:166-184` renderiza só `requisicoes` e `erros`, nunca lê `vazios`/`falhas`/`taxaFalha`/`alerta`
- **Verificação:** código/docs
- **Impacto:** um admin olhando "Erros (janela 3 dias): 0" durante um evento idêntico ao de 31/07 veria zero, porque o contador exibido não inclui `vazios` — o backend já resolveu a "cegueira" documentada, mas a UI reproduz a mesma cegueira na apresentação
- **Recomendação:** adicionar ao card "Orçamento brapi (ADR-008)": `Kv` para "Respostas vazias (200 sem vela)", `Kpi` com tom negativo quando `alerta===true`, e a taxa de falha ao lado da contagem bruta de erros — dado já pronto no payload.

#### C-37 — Nenhum alerta de "kill-switch ligado há N horas em horário de pregão" [Alto]
- **Dimensão:** ADMIN | **Requisito:** ADMIN-02 | **Origem:** F-ADMIN-04
- **Regra aplicada:** D-03 — é o mecanismo que, se existisse, teria encurtado o incidente real de 2,5 dias para horas
- **Evidência:** `server/app/agent.py:154-204` — `set_kill_switch`/`kill_switch_on` não gravam timestamp consultável pelo portal separado do log genérico; `web-admin/src/App.jsx:432-482` (`KillSwitchBox`) mostra só o estado atual; nenhuma rota calcula duração; `admin_audit_log` TEM o timestamp da mudança (dado já existe, é leitura, não escrita nova)
- **Verificação:** código/docs
- **Impacto:** o sinal é 100% passivo — alguém precisa abrir a aba e notar o KPI vermelho; é exatamente o padrão do incidente real
- **Recomendação:** card na aba Automação: "ligado há Xh" calculado a partir do último evento `admin_audit_log` para `entity="agentKillSwitch"`, com tom negativo crescente após um limiar (ex. 4h em pregão); push/e-mail é segunda fase.

#### C-38 — Métricas de gasto de IA: hard stop no teto global existe, mas nenhum alerta preventivo antes de bater o teto [Médio]
- **Dimensão:** ADMIN | **Requisito:** ADMIN-02 | **Origem:** achado sem número `F-` (seção "Replay do incidente do kill-switch", `FINDINGS-ADMIN.md`)
- **Regra aplicada:** D-04 — risco real (gasto pode crescer até o teto global sem aviso intermediário), mitigado pelo hard stop existente (não é gasto ilimitado), ainda não materializado em incidente de fatura documentado
- **Evidência:** `server/app/metering.py:99-113` impõe teto global de gasto diário (HARD STOP, não alerta preventivo); aba Custos mostra "TOKENS/DIA" com sparkline (`App.jsx:146,158`) — detectar anomalia depende de um humano notar visualmente; não há limiar configurável nem alerta automático
- **Verificação:** código/docs
- **Impacto:** gasto pode crescer até o teto sem aviso intermediário — mitigado pelo hard stop, mas sem alarme antecipado
- **Recomendação:** limiar configurável de "gasto de hoje X% acima da média dos últimos N dias" com alerta, complementar ao hard stop já existente.

#### C-39 — Aba "Auditoria" sem campo `perm` diverge do padrão visual das outras 9 abas [Médio]
- **Dimensão:** ADMIN | **Requisito:** ADMIN-01 | **Origem:** F-ADMIN-03
- **Regra aplicada:** D-04 — risco real de confusão operacional, não incidente materializado; o backend já gateia corretamente
- **Evidência:** `web-admin/src/App.jsx:1110` — entrada sem `perm`, única das 10; `:1176` — `visiveis` filtra `!v.perm || perms.includes(v.perm)`, torna a aba sempre visível a qualquer usuário com QUALQUER permissão administrativa; `server/app/main.py:741-742` exige `require_any_admin_permission()` — dado real nunca vazou
- **Verificação:** código/docs
- **Impacto:** não é vazamento de dado — é que a UI não deixa claro que "Auditoria" tem regra de acesso DIFERENTE (qualquer permissão administrativa, não uma específica) das outras 9 abas
- **Recomendação:** documentar visualmente a diferença (ex.: rótulo "(visível a qualquer papel administrativo)") ou formalizar `perm: "*"` como convenção explícita no array `VIEWS`.

## Verificado e conforme

### Storyline pedagógico
- Compra manual (Passo 4): testada ao vivo, cálculo determinístico confirmado, sem intervenção de IA (`server/app/main.py:1501-1518`).
- Fonte + horário do dado (Passo 2): `GET /api/quotes` retorna `source`/`at`; front exibe ambos (`App.jsx:1057,2927-2936,3234`).
- Falha de dado (Passo 7): erro estruturado (502, `code:"missing_key"`), nunca conteúdo fabricado.
- STORY-02 Q3/Q1: troca de modo acessível no hub de Perfil, texto explica a diferença entre modos, vocabulário de timing muda por modo (confirmado ao vivo).
- STORY-02 Q4 ("Modo Estudo nunca executa", Fase A do `docs/plano-operador-entrada-e-modos.md`): trava dupla (escrita + leitura, `agent.py:559-570`) confirmada no código; documento fonte tem status desatualizado ("aguardando aprovação"), achado de higiene de doc (Baixo), sem risco de produto associado.
- **Guardrail CVM (manchete só do motor determinístico): CONFORME, item mais crítico da régua.** `server/app/setups.py:484-521` (`produzir_leitura`) 100% determinística; `App.jsx:2958-2999` renderiza esse campo como headline, nunca o `recomendacao` textual da IA.
- STORY-04 Superfície 1 (texto determinístico) e Superfície 2 (prompt à LLM): auditados `skill_ref.py`, `copy.js`, `disclaimers.js`, `conceitos.py`, `kb.py` — nenhuma frase de garantia/certeza; guardião de teste `test_auditoria_prompts.py` (15 testes travando essas propriedades).
- STORY-04 Superfície 3 (saída real da IA): não exercitada nesta verificação (sem chave configurada) — limitação declarada, não omitida.

### UX/UI
- Saldo/caixa/patrimônio sempre visíveis no `Topbar` global, testado ao vivo (princípio 1).
- Rejeição de compra por caixa insuficiente: 400 limpo, testado ao vivo, com espelho no cálculo local do `BuyModal`.
- Ciclo compra→venda completo testado ao vivo, histórico com `pnl` correto, sem invenção de número.
- Timing fora do pregão: estado/motivo/ressalva explícitos, mapeado para rótulo dedicado.
- Grep dirigido por linguagem de enriquecimento/garantia em 9 arquivos: zero violação real (só negações "não garante"/"nunca prometa" ou o guardrail explícito).
- Degradação graciosa quando IA indisponível: estimativa determinística automática em vez de bloquear.
- Chip de modo textual persistente em toda tela; paleta/vocabulário coerentes por modo; gate do agente autônomo comunica o modo atual com link de saída.
- 74 `aria-`/9 `role=`/2 `tabIndex` — cobertura semântica real (modais `role="dialog"`, switch `role="switch"`, ícones `aria-hidden`, progresso `role="status" aria-live`); zero `<img>` sem `alt` (não há `<img>` no arquivo).
- Botões de ação primária declaram `minHeight`/dimensão ≥40px, consistente com alvo de toque WKWebView.

### Código
- **Paridade de NOMES `deviceStore`×`serverStore` hoje: 0 assimetrias** — os 58 métodos existem nos dois lados com o mesmo nome (a lacuna real, ausência de guardião FUTURO, é C-20).
- Par `carteiraStopAlvo`/`carteiraStopAlvoOperador` (`defaults.py`↔`catalog.js`): único par de prompt com paridade byte-a-byte travada por teste — funciona como projetado.
- **F-CODE-06 — Gate "Executar"/"Entrada automática": defeito original (2026-08-07) já corrigido.** `App.jsx:3780-3803` e `:3915-3945` hoje têm parágrafo sempre visível + link "Trocar para Modo Operador →"; nenhum dos 23 usos atuais de `title=` é mais a única explicação de um controle desabilitado. O achado residual é C-23 (instância nova e menor do mesmo padrão, não o mesmo defeito reaberto).
- Falha silenciosa da fonte de dados (cenário mais perigoso já observado em produção — Yahoo 200 com zero velas): cobertura direta e específica em `test_candle_provider.py` (3 testes nomeados). Sem achado.
- Dado atrasado (tríade temporal): cobertura extensa em `test_timing.py` (20+ testes). Sem achado.
- Gate de modo no ciclo automático: `agent.agent_params` força `mode="sinalizar"` fora do Operador, enforcement server-side, coberto por `test_agent_modo_estudo.py`. Sem achado.
- Suíte de backend: 970/970 testes passaram sem falha real (129 warnings, todos de depreciação de biblioteca, não de lógica de produto).

### Gating de monetização
- Separação conceitual cota-física-brapi × cap-comercial-de-IA bem resolvida no ADR-010 e implementada como duas camadas de fato independentes — nenhum ponto de código onde as duas contagens compartilham contador. Não precisa virar item de roadmap.
- Texto de erro quando o cap de IA gerenciada estoura já sugere BYOK como alternativa gratuita, não empurra upgrade pago (alinhado ao princípio 8).
- `requires_subscription`/`plan_at_least` sendo funções órfãs não é, por si, achado de severidade alta — são pontos de extensão deliberadamente não conectados (ADR-010 é explícito). O achado real é que `can_add_ticker`/`can_analyze` JÁ têm call site mas incompleto (C-31/C-33).
- Mensagem de teto global de IA gerenciada já é transparente sobre ser limite do servidor, não confunde os dois eixos.
- GATE-03 (mapa de features candidatas a tier pago): tabela técnica evidencia esforço/bloqueio sem revelar problema estrutural adicional além dos já cobertos por GATE-01 — requisito conforme, sem achado `C-NN` dedicado.

### Portal de administração
- Os 4 grupos RBAC (`server/app/rbac.py:21-29`) servem os 4 cenários de operação sem exigir permissão a mais: só observar, desligar kill-switch em emergência, editar prompt, e o bootstrap do dono (`_is_admin_bootstrap`) confere `role_admin` idempotente em toda request administrativa.
- Guardião de cobertura de rotas (`test_adr013_cobertura_rotas.py`): enumera `app.routes` via introspecção do FastAPI e falha se qualquer rota não tiver dependency reconhecida ou allowlist explícita — nenhuma rota `/api/admin/*`, `/api/obs/*` ou `/api/analytics/*` fora da cobertura.
- Auditoria de escrita sem exceção: toda rota de escrita admin verificada passa por `require_permission`/gate nomeado.
- Handoff mobile (ADR-014): 2 toques, TTL 90s de uso único (revogação em falha é ponto de atenção menor, risco residual baixo — só quem já É admin gera o código); 10 abas fluidas por design (`maxWidth:760px`, sem `<table>`, sem media query); pendências já mapeadas pelo próprio ADR-014, não bloqueantes.
- ADMIN-03: conforme, sem achado `C-NN` dedicado.

## Rastreabilidade de requisitos

| Requisito | Dimensão | Achados (C-NN) | Status |
|---|---|---|---|
| STORY-01 | STORY | C-01, C-02, C-03, C-06 | com achados |
| STORY-02 | STORY | C-04, C-07 | com achados |
| STORY-03 | STORY | C-05, C-08, C-09 | com achados |
| STORY-04 | STORY | C-10 | com achados |
| UX-01 | UX | C-11, C-12, C-13, C-14 | com achados |
| UX-02 | UX | C-17 | com achados |
| UX-03 | UX | C-15, C-16, C-18 | com achados |
| UX-04 | UX | C-10 (fundido com STORY-04) | com achados |
| CODE-01 | CODE | C-19, C-21, C-28 | com achados |
| CODE-02 | CODE | C-20, C-22 | com achados |
| CODE-03 | CODE | C-23 (defeito original já corrigido — ver F-CODE-06 em "Verificado e conforme") | com achados |
| CODE-04 | CODE | C-24, C-25, C-26, C-27, C-29 | com achados |
| GATE-01 | GATE | C-31, C-32, C-33 | com achados |
| GATE-02 | GATE | C-30, C-34 | com achados |
| GATE-03 | GATE | nenhum — mapa técnico em "Features candidatas a tier pago" não revelou problema estrutural adicional além de GATE-01 | conforme |
| ADMIN-01 | ADMIN | C-39 | com achados |
| ADMIN-02 | ADMIN | C-35, C-36, C-37, C-38 | com achados |
| ADMIN-03 | ADMIN | nenhum — handoff 2 toques, TTL 90s uso único, 10 abas fluidas por design, pendências do ADR-014 já mapeadas e não bloqueantes | conforme |
| REPORT-01 | Consolidação | este documento (`REPORT-01.md`) | conforme — documento único, sumário executivo primeiro (D-07), 39 achados consolidados, 19 requisitos rastreados |

## Passe de consistência final (Task 2c)

- **Nenhum achado propõe correção implementada nem número comercial.** Todas
  as 39 recomendações são sugestões de ação em prosa (ex.: "propagar
  `source`...", "trocar `\|\| \"estudo\"\`..."); GATE-03 explicitamente evita
  decidir preço/limite (fora de escopo, ver PROJECT.md Out of Scope).
- **Nenhum achado sugere mudar o bundle id `com.alexandrecamerini.bolsia`.**
  Achados de branding (C-07, "dois nomes Operador") tratam só de nomenclatura
  de tela dentro do app, não do identificador de build.
- **Nenhuma recomendação viola um guardrail do CLAUDE.md.** O guardrail CVM
  (manchete só do motor determinístico) foi verificado CONFORME (seção
  "Verificado e conforme" — Storyline); nenhuma recomendação propõe apagar
  guardião de teste (C-19/C-20 propõem ADICIONAR guardiões, nunca remover os
  existentes); nenhuma recomendação reescreve `qa/`/`ESTADO-*`/`CHECKOUT-*`;
  as recomendações de paridade (C-20, C-22) reforçam, não enfraquecem, os
  pares de arquivo obrigatórios.
- **Nenhum segredo foi copiado para dentro do relatório.** Buscado por
  padrões de chave de API (`sk-...`, `AIza...`) e por valores reais de
  `BRAPI_TOKEN`/token de sessão — o relatório só cita NOMES de variável de
  ambiente (ex. `B3_TIMING_PUSH_KILL`, `BRAPI_TOKEN`), nunca valores; contas
  usadas na verificação são de teste isolado (`auditoria-story@local.test`,
  `auditoria-ux@local.test`, `auditoria-admin@local.test`), não e-mail real de
  usuário.
- **Toda severidade citada no Sumário executivo bate com o detalhe da
  dimensão** — os 2 Críticos (C-11, C-30) e os 8 Altos (C-12, C-19, C-20,
  C-31, C-32, C-35, C-36, C-37) citados no sumário são exatamente os mesmos
  rótulos `[Crítico]`/`[Alto]` usados nas seções de dimensão (confirmado por
  contagem automatizada: 2 Crítico, 8 Alto, 20 Médio, 9 Baixo = 39).
- **Os 6 Success Criteria da Phase 1 (`ROADMAP.md`) estão todos atendidos:**
  (1) jornada STORY vs. 8 passos, transição de modo, cobertura educacional,
  violações de promessa — C-01..C-10; (2) UX vs. 10 princípios, matriz de
  estados, consistência Estudo/Operador, responsividade/acessibilidade, copy
  — C-11..C-18; (3) dívida técnica com mapa de `appMode`, lacunas de
  paridade, gate "Executar", cobertura da suíte — C-19..C-29; (4) gating
  free→pago, transparência cota física × cap comercial, features candidatas
  — C-30..C-34; (5) portal admin vs. RBAC, visibilidade do incidente do
  kill-switch, usabilidade do handoff mobile — C-35..C-39; (6) todos os
  achados consolidados num único documento, classificados por severidade e
  dimensão, sem correção implementada — este documento. Nenhuma lacuna
  declarada.
