# Achados — Dimensão CODE (dívida técnica)

**Data:** 2026-08-18

## Método de verificação

**Ambiente:** execução isolada em worktree Git (`agent-aef1707892a90a6db`), código completo
presente (`server/`, `web/`, `web-admin/`), mas `web/node_modules` **não instalado** neste
worktree (ver achado F-CODE-08 — impacto direto na suíte canônica).

**Lido (código):**
- `web/src/App.jsx` — só as faixas retornadas pelos greps abaixo (arquivo tem 7599+ linhas,
  nunca lido inteiro), incluindo `ModoTrabalhoCard` (~1820-1868), `TermoOperadorModal`
  (~1870-1905), `EvolucaoScreen` (~1619-1640), `AjudaScreen` (~2016-2020),
  `MercadoScreen`/watchlist (~3182-3195, ~5590-5615), `SkillSection` (~4218-4227),
  `AgenteScreen`/gate Executar/Entrada automática (~3688-3945), `App()` raiz e `ctx`
  (~6300-6350, ~6490-6520, ~6840-6870, ~7205-7270, ~7390-7470).
- `web/src/persistence.js` inteiro (1251 linhas) — `serverStore()` (linhas 97-208) e
  `deviceStore()` (linhas 214-1170, interface exposta a partir da linha 441).
- `server/app/defaults.py`, `web/src/catalog.js` inteiro (210 linhas).
- `server/app/agent.py` (`agent_params`, `_avaliar_entradas`, gate de `appMode`).
- `server/app/main.py` (rotas `/api/buy`, `/api/sell`, linhas 1502-1522+).
- `server/app/store.py` (`buy`, `sell`, `buy_option`, `sell_option`).
- `server/app/candle_provider.py` (modo de falha silencioso, já bem coberto).
- `docs/auditoria-controle-ordens-parametros.md` (fonte primária do defeito do gate
  "Executar" e da lista original de 11+ linhas do `appMode`) e seção "Status
  (atualizado 2026-08-07)".
- `.planning/codebase/CONCERNS.md`, `TESTING.md`.

**Executado:**
- `bash scripts/executar.sh --testes` (suíte canônica completa) — resultado detalhado em
  F-CODE-08.
- Greps direcionados (`grep -n "appMode" web/src/App.jsx`, comparação programática de
  `Object.keys`-equivalente entre `serverStore()`/`deviceStore()`, busca por referências de
  cada um dos 58 métodos em `web/tests/*.mjs`, busca por testes de rota `/api/buy`/`/api/sell`
  e por cenário de recompra após venda parcial).
- `git status --porcelain server web web-admin` — confirmado vazio ao final (ver rodapé).

**Não feito (fora do escopo D-01 desta dimensão):** nenhuma navegação ao vivo no browser/PWA;
nenhuma correção de código; não foi rodado `npm install` em `web/` para restaurar
`node_modules` (ver F-CODE-08 — decisão explícita, não é uma correção autorizada nesta fase
read-only e instalar pacote é ação excluída de auto-fix).

---

## Mapa de recomputação de appMode

Levantamento via `grep -n "appMode" web/src/App.jsx` (26 ocorrências — a lista do
CONCERNS.md, "linhas 1581, 1779, 1954, 3044, 3529, 4029, 5155, 5855, 6271, 6412...", está
**desatualizada**: essas linhas hoje contêm código não relacionado a `appMode` — o arquivo
mudou de tamanho desde a análise que gerou aquele texto. A lista abaixo é a atual, conferida
linha a linha.

| Linha | Expressão | Fonte | Uso | Risco de divergência | Evidência |
|---|---|---|---|---|---|
| 1624 | `(data.config && data.config.appMode) === "operador"` | `ctx.data.config.appMode` (prop) | Pill de decisão de modo na Home (`EvolucaoScreen`) | potencial | Lê o mesmo `ctx.data` do render atual — só divergiria de `ctx.operador` se `ctx.data` mudasse entre a montagem de `ctx` e o uso, o que não ocorre dentro do mesmo render (ambos vêm do mesmo objeto `ctx`) |
| 1828 | `c.appMode === "operador" ? "operador" : "estudo"` | `data.config.appMode` (via `c = data.config \|\| {}`) | Fonte exibida na PRÓPRIA tela onde o usuário troca de modo (`ModoTrabalhoCard`) | nenhum | É a tela que grava o valor; não há como divergir do que acabou de escrever |
| 1834 | `A.saveConfig({ appMode: m })` | escrita, não leitura | Persiste a troca de modo | nenhum | Falha de rede é tratada em catch com toast (linha 1841); UI não reflete otimisticamente antes da confirmação |
| 1837-1845 | comentário | N/A | Documenta a decisão de dar `window.location.reload()` após trocar de modo (linha 1850) | nenhum | — |
| 1897 | `A.saveConfig({ operadorTermo: {...}, appMode: "operador" })` | escrita | Ativa Operador pela 1ª vez (aceite de termo) | nenhum | Mesmo padrão de 1834 — reinício completo após confirmar (linha 1903) |
| 2018 | `(ctx.data.config && ctx.data.config.appMode) === "operador"` | `ctx.data.config.appMode` | Filtra seções exibidas em `AjudaScreen` | potencial | Mesma classificação de 1624 |
| 3188 | `(data.config && data.config.appMode) === "operador"` | `data.config.appMode` (via ctx) | Gate de exibição do "plano" determinístico do servidor na watchlist (`MercadoScreen`) | potencial | O CÁLCULO do plano vem sempre do servidor (`setups.py`); aqui só decide se a UI mostra a coluna — não há cálculo financeiro nesta linha |
| 4224 | `(data.config && data.config.appMode) === "operador" ? "operador" : "estudo"` | `data.config.appMode` | Escolhe qual skill (prompt) o editor mostra por padrão (`SkillSection`) | potencial | Mesma classificação — normalização idêntica ao padrão canônico |
| 5606 | `(data.config && data.config.appMode) === "operador"` | `data.config.appMode` | Recalculada **por item** dentro do `.map()` da watchlist (uma vez por ativo exibido) | nenhum (valor) / ineficiência | Mesmo valor em toda iteração do mesmo render — não é risco de divergência de dado, é recomputação redundante (N vezes por render em vez de 1) |
| 5756 | `(data.config && data.config.appMode) === "operador" ? DISCLAIMERS.operador : DISCLAIMERS.radar` | `data.config.appMode` (inline) | Escolhe qual disclaimer legal exibir no rodapé da watchlist | potencial | Mesma classificação |
| 6319 | `(data && data.config && data.config.appMode) === "operador" ? "operador" : "estudo"` | `data.config.appMode` (raiz do componente `App()`) | **Fonte real** de `cp = copyFor(appMode)`, classe CSS `b3-mode-operador`, `theme-color` da barra do navegador | nenhum | É a origem, não uma cópia — todo o restante da tela deriva (direta ou indiretamente) daqui |
| 6322, 6329, 6333, 6341, 6346 | reusam a variável local `appMode` definida em 6319 | mesma variável (mesmo escopo de função) | Vocabulário (`cp`), classe CSS, esquema de cor da barra do navegador | nenhum | Não são novas leituras — mesma referência já resolvida em 6319 |
| 6501 | `(data && data.config && data.config.appMode) \|\| "estudo"` | `data.config.appMode` | Parâmetro `modoApp` enviado a `store.conceitos(modoApp)` (camada didática, API) | potencial — **padrão de normalização diferente** | Não é ternário: se `config.appMode` algum dia contiver um valor que não seja `"operador"`/`"estudo"`/`undefined`, este ponto propagaria o valor bruto para o backend em vez de normalizar para `"estudo"` como os demais pontos fazem. Hoje as únicas escritas de `appMode` no código são exatamente `"estudo"`/`"operador"` (linhas 1834, 1897) — não há sequência de eventos observável que produza um terceiro valor; risco é estrutural, não observado |
| 6577 | comentário | N/A | Documenta perda de `appMode`/termo/risco em boot antigo (bug já corrigido) | nenhum | — |
| 6862 | `((data.config \|\| {}).appMode === "operador") ? ... : ...` | `data` (closure de `A = useMemo(() => ({...}), [data])`, linha 7160) | Escolhe prompt `carteiraStopAlvoOperador` vs `carteiraStopAlvo` ao pedir stop/alvo por IA | nenhum | `A` é recriado inteiro sempre que `data` muda (única dependência do `useMemo`) — a closure nunca fica com um `data` desatualizado |
| 7217 | comentário | N/A | Declara a regra: "Novo código deve ler `ctx.operador`, não redevirar de `data.config.appMode`" | nenhum | Regra de convenção, não de código — não é imposta por lint nem teste |
| 7220 | `!!(data && data.config && data.config.appMode === "operador")` | `data.config.appMode` | **Definição de `ctx.operador`** — a fonte canônica criada em 2026-08-07 (F10-20260807-08) | nenhum | É a definição em si |
| 7269 | comentário | N/A | Documenta perda de `appMode`/termo/risco em boot antigo (mesmo bug de 6577) | nenhum | — |
| 7411 | `cfg.appMode \|\| "estudo"` | `data.config.appMode` (via `cfg = data.config \|\| {}`) | Campo `modo` no snapshot `"perfil"` enviado ao **assistente de IA** (contexto da pergunta livre) | potencial — mesmo padrão de 6501 | Mesma ressalva de 6501; destino mais sensível (contexto que a LLM usa para calibrar a resposta), mas mesma ausência de sequência de eventos observável hoje |
| 7433 | reusa `appMode` (6319) | mesma variável | `className` do shell do app | nenhum | — |
| 7465 | reusa `appMode` (6319) | mesma variável | `ThemeCtx.Provider value={{ mode: appMode }}` | nenhum | — |

**Total de ocorrências mapeadas: 26** (12 leituras/recomputações independentes de valor +
2 escritas + 4 comentários + 5 reusos da variável local de `App()` + 1 definição canônica +
2 reusos dessa definição no fechamento do componente).

**Correção à narrativa do CONCERNS.md:** nenhum ponto encontrado hoje apresenta risco **real**
de divergência (nenhuma sequência de eventos observável produz dois valores diferentes de
`appMode` dentro do mesmo render). O risco é **potencial**: dois padrões de normalização
coexistem no arquivo — o ternário seguro (`=== "operador" ? "operador" : "estudo"`, usado em
~10 pontos e no `ctx.operador` canônico) e o passthrough cru (`\|\| "estudo"`, usado em 6501 e
7411) — e só divergiriam se `config.appMode` algum dia contivesse um terceiro valor, o que as
duas únicas rotas de escrita do código (1834, 1897) não produzem hoje.

### Os 3 bugs históricos — guardião cobre sintoma ou causa raiz?

`docs/auditoria-controle-ordens-parametros.md` atribui os 3 bugs a seguir ao "mesmo padrão de
erro raiz" da recomputação de `appMode`. Verificação linha a linha mostra que a causa raiz
real de cada um é mais específica que "appMode recalculado" — a atribuição do documento é
correta no nível temático ("estado que muda num lugar que outro não vê"), mas **nenhum dos 3
foi causado por dois pontos de `App.jsx` lendo `data.config.appMode` de forma inconsistente
no mesmo render**:

1. **Stop/alvo apagava sozinho** — causa raiz real: `blur` de campo vazio salvava `null` sem
   confirmação (lógica do handler de blur, não leitura de `appMode`). Guardião:
   `web/tests/test_posicao_stop_alvo.mjs` — cobre o **sintoma exato** (blur com campo vazio
   não chama `A.setStop`/`A.setAlvo`), não uma regra estrutural que impediria uma variante
   nova do mesmo tipo de bug em outro campo.
2. **Carteira nativa dessincronizada do servidor** — causa raiz real: `deviceStore.buy`/
   `sell`/`putPosition` eram 100% locais (gap de paridade `deviceStore`×`serverStore` —
   território de CODE-02, não de `appMode`). Guardião:
   `web/tests/test_carteira_nativa_sincroniza.mjs` — cobre o sintoma (sincronização
   acontece); não pôde ser executado nesta verificação por falta de `web/node_modules` (ver
   F-CODE-08).
3. **Ciclo do agente não reagia a gatilho recém-armado** — causa raiz real: o ciclo só
   rodava no `intervalMin` agendado, sem gatilho imediato após mudança de carteira (ausência
   de um mecanismo de disparo, não leitura de `appMode`). Guardião:
   `server/tests/test_ciclo_imediato_apos_carteira.py` — este SIM cobre a causa raiz
   específica (prova o gatilho em si, com um fake que só registra a chamada), é o guardião
   mais robusto dos 3.

Nenhum dos 3 guardiões travaria uma variante nova de "estado que muda num lugar que outro
não vê" fora do sintoma exato já corrigido — não existe um teste estrutural genérico para a
CLASSE do erro (isso é o próprio achado F-CODE-04 para o par de stores, e não tem equivalente
para `appMode` porque, como mostrado acima, `appMode` não foi de fato a causa dos 3 bugs).

---

## Achados

### F-CODE-01 — `ctx.operador` existe desde 2026-08-07 mas 10 de 12 pontos de leitura de `appMode` continuam recalculando de forma independente
- **Requisito:** CODE-01
- **Severidade:** Médio — D-04: risco real (dois padrões de normalização coexistem — ver
  mapa acima), mas sem incidente documentado causado especificamente por esta inconsistência
  (a atribuição do CONCERNS.md aos 3 bugs históricos não se sustenta na leitura linha a
  linha — ver seção acima). **Conflito explícito com a régua:** o próprio `01-CONTEXT.md`
  cita textualmente "os 3 bugs do padrão `appMode` em `App.jsx`" como exemplo de Alto (D-03).
  Esta classificação Médio DISCORDA deliberadamente desse exemplo textual, com base na
  evidência de código acima (nenhum dos 3 bugs foi causado por divergência de leitura de
  `appMode` no mesmo render) — a decisão de qual leitura prevalece (o exemplo da régua ou a
  evidência de código) fica para o plano 01-06 (consolidação). Calibração explícita do
  usuário em 01-CONTEXT.md também se aplica: "monólito grande por si só é Baixo/Médio".
- **Evidência:** `web/src/App.jsx:7214-7220` (definição de `ctx.operador`, com comentário
  "Novo código deve ler `ctx.operador`, não redevirar de `data.config.appMode`") vs. as 10
  leituras independentes em `web/src/App.jsx:1624, 1828, 2018, 3188, 4224, 5606, 5756, 6319,
  6501, 6862, 7411` (a de 1828 é a própria tela de troca, sem risco; a de 6319 é a origem, não
  uma cópia — das 10, 8 são cópias redundantes de uma fonte que já existe).
- **Verificação:** código (grep + leitura linha a linha das 26 ocorrências).
- **Impacto:** hoje nenhum (ver correção de narrativa acima). Se um dia uma tela nova passar
  a ler `data.config.appMode` com uma terceira variante de normalização (nem ternário nem
  passthrough), o próximo desenvolvedor não tem nenhum lint/teste que force o uso de
  `ctx.operador` — a convenção depende só do comentário na linha 7217.
- **Recomendação:** migrar os 8 pontos de recomputação redundante (exclui 1828 e 6319) para
  ler `ctx.operador` — mecânico, sem mudança de comportamento — e considerar um teste estático
  (regex em `App.jsx`, no padrão já usado pelos guardiões de paridade de stores) que falhe se
  `data.config.appMode` for lido fora de `App()`/`ctx.operador`.

### F-CODE-02 — Os 2 pontos com normalização "passthrough" (`|| "estudo"`) divergem estruturalmente do padrão ternário e alimentam a IA/API sem normalização
- **Requisito:** CODE-01
- **Severidade:** Baixo — D-05: nenhuma sequência de eventos observável produz hoje um valor
  fora de `{"estudo", "operador", undefined}`; é polimento/consistência, não risco
  materializável com o código atual.
- **Evidência:** `web/src/App.jsx:6501` (`modoApp` enviado a `store.conceitos(modoApp)`) e
  `web/src/App.jsx:7411` (`modo` no snapshot enviado ao assistente de IA).
- **Verificação:** código.
- **Impacto:** nenhum hoje; se as regras de escrita de `appMode` mudarem no futuro (ex.: novo
  modo intermediário), estes 2 pontos propagariam o valor bruto para APIs/IA em vez de
  normalizar, diferente dos demais 10 pontos.
- **Recomendação:** trocar `|| "estudo"` pelo mesmo ternário `=== "operador" ? "operador" :
  "estudo"` usado no resto do arquivo — uma linha em cada ponto.

### F-CODE-03 — Guardiões dos 3 bugs históricos travam o sintoma corrigido, não a classe do erro
- **Requisito:** CODE-01
- **Severidade:** Alto — D-03: os 3 bugs já causaram incidente real documentado
  (`docs/auditoria-controle-ordens-parametros.md`), e o padrão-classe ("estado que muda num
  lugar que outro não vê") permanece sem barreira estrutural — apenas o sintoma exato já
  visto está bloqueado.
- **Evidência:** `web/tests/test_posicao_stop_alvo.mjs` (bug 1, cobre só o blur vazio),
  `web/tests/test_carteira_nativa_sincroniza.mjs` (bug 2, não executável nesta verificação —
  ver F-CODE-08), `server/tests/test_ciclo_imediato_apos_carteira.py` (bug 3, este cobre a
  causa raiz específica).
- **Verificação:** código + suíte executada (bug 3); bug 2 não pôde ser exercitado (ambiente).
- **Impacto:** uma variante nova do mesmo padrão-classe (ex.: um campo novo em
  `deviceStore`/`serverStore`, ou um novo handler de blur em outro campo numérico) passaria
  pelos 3 guardiões existentes sem disparar nenhum deles.
- **Recomendação:** não é escopo desta fase implementar, mas a prioridade 5 do próprio
  `docs/auditoria-controle-ordens-parametros.md` ("um card de status único" + `operador` como
  valor derivado único) e o teste genérico de paridade de F-CODE-04 são os dois mecanismos
  estruturais que fechariam essa lacuna — ambos ainda pendentes.

### F-CODE-04 — Paridade `deviceStore`×`serverStore`: nomes 100% iguais hoje, mas 28 de 58 métodos (48%) não têm NENHUMA referência em teste, e não existe guardião genérico exaustivo
- **Requisito:** CODE-02
- **Severidade:** Alto — D-03: a lacuna de paridade **já foi causa raiz de 2 incidentes
  documentados** (carteira nativa não sincronizava — F10-20260807-05; `initialBudget` sem
  sync device→servidor — F10-20260809-05). Aplicando a régua com o histórico, não com o
  estado atual (que hoje está simétrico).
- **Evidência:** comparação programática de `web/src/persistence.js:110-208`
  (`serverStore()`) vs. `:441-1170` (interface exposta de `deviceStore()`) — **0 assimetrias
  de nome** (58 métodos em cada lado, conjuntos idênticos) e 1 única diferença de assinatura
  (`_setDeviceScope`, intencional — comentário "no-op no web"). Busca por referência
  (`grep -w`) de cada um dos 58 nomes em `web/tests/*.mjs`: 28 métodos com **zero**
  ocorrências em qualquer arquivo de teste — `_localSeed`, `_setDeviceScope`,
  `adminMobileHandoff`, `agentLog`, `agentRunNow`, `agentStatus`, `aiActivity`, `aiQuota`,
  `analyzeOption`, `cachedTechnicals`, `cycle`, `kbBuscar`, `obsLogs`, `optionsBuy`,
  `optionsChain`, `optionsExpirations`, `optionsGate`, `optionsSell`, `pushAnalysisLog`,
  `putLlmPrompts`, `putOptionPosition`, `putProfile`, `putSkill`, `putSnapshot`,
  `restoreSkill`, `scanProgress`, `technicals`, `testConfig`.
- **Verificação:** código (comparação estática + busca por referência; nenhum teste novo
  escrito).
- **Impacto:** um método novo adicionado a só um dos 2 stores (violação da regra do
  `CLAUDE.md`, "método novo entra nos DOIS") só é pego hoje se o autor lembrar de escrever um
  teste pontual — não existe teste que rode `Object.keys` (ou equivalente estático) nos dois
  objetos e falhe em qualquer assimetria não documentada. Ver seção "Paridade
  deviceStore x serverStore" abaixo para o detalhamento completo.
- **Recomendação:** um teste genérico único (padrão já usado pelos guardiões pontuais
  existentes: `readFileSync` + regex em `persistence.js`) que extraia a lista de chaves de
  `serverStore()`/`deviceStore()` e falhe em qualquer assimetria — complementa, não substitui,
  os testes pontuais de contrato de assinatura já existentes (ex.: `test_didatica_parity.mjs`
  para `syncPushPrefs`).

### F-CODE-05 — `default_skill_text()`/`defaultSkillText()` (prompt padrão do Modo Estudo) sem NENHUM guardião, diferente do par `carteiraStopAlvo*` que é byte-exato
- **Requisito:** CODE-02
- **Severidade:** Médio — D-04: risco real (drift silencioso de texto educacional entre
  Python e JS), sem ocorrência registrada para este par específico.
- **Evidência:** `server/app/defaults.py:22` (`default_skill_text`) e
  `web/src/catalog.js:54` (`defaultSkillText`). O guardião existente
  (`server/tests/test_auditoria_prompts.py::test_a8ii_paridade_defaults_carteira_com_catalog_js`)
  só compara `carteiraStopAlvo`/`carteiraStopAlvoOperador`. A checagem mais próxima,
  `web/tests/test_copy_theme.mjs:160-161`, verifica apenas se os dois arquivos CONTÊM a
  substring `defaultSkillTextOperador`/`default_skill_text_operador` (marcador de presença,
  não paridade de conteúdo) — e nem essa checagem de marcador cobre a versão SEM `Operador`
  (`default_skill_text`/`defaultSkillText`, a skill do Modo Estudo).
- **Verificação:** código.
- **Impacto:** o texto que define a persona/skill do Modo Estudo pode divergir entre o app
  nativo (que monta o próprio default sem chamar o servidor) e o servidor sem que nenhum
  teste detecte — diferente do stop/alvo, que é travado byte a byte.
- **Recomendação:** estender `test_a8ii_paridade_defaults_carteira_com_catalog_js` (ou criar
  um par equivalente) para `default_skill_text`/`defaultSkillText`.

### F-CODE-06 — Gate "Executar"/"Entrada automática": defeito original (2026-08-07) já corrigido — CONCERNS.md está desatualizado neste ponto
- **Requisito:** CODE-03
- **Severidade:** N/A (verificado como corrigido — ver "Verificado e conforme")
- **Evidência:** `web/src/App.jsx:3780-3803` (Executar) e `:3915-3945` (Entrada automática).
  Comparado contra `docs/auditoria-controle-ordens-parametros.md:124-136` ("Status
  (atualizado 2026-08-07)": itens 1 e 2 marcados "feito, F10-20260807-07").
- **Verificação:** código.
- **Impacto:** nenhum — ver seção "Verificado e conforme".

### F-CODE-07 — Toggle mestre de "Entrada automática" não tem atributo HTML `disabled` nem feedback próprio — reintroduz uma instância residual do defeito original
- **Requisito:** CODE-03
- **Severidade:** Médio — D-04: comportamento funcional correto (não liga sozinho fora do
  Operador), o que falha é o feedback — mas o parágrafo explicativo da seção (linha
  3937-3944) já existe e menciona o link "Trocar para Modo Operador →" logo abaixo, então a
  informação está presente na tela (só não anexada ao controle específico). **Não** classifico
  como Crítico/D-02: o princípio 9 do CLAUDE.md ("estados completos") pede que o estado exista
  e seja visível em algum lugar da tela — e existe, um parágrafo abaixo do toggle, ainda que
  não vinculado diretamente a ele. Isso distingue este caso do defeito original (2026-08-07),
  que não tinha NENHUMA explicação visível ao toque.
- **Evidência:** `web/src/App.jsx:3924` — `<Toggle on={!!ag.entradaAuto && operador}
  onClick={() => operador && putAg({ entradaAuto: !ag.entradaAuto })} .../>`. O componente
  `Toggle` (`web/src/App.jsx:310-318`) não recebe nem aplica prop `disabled` — é sempre um
  `<button>` clicável, sem `aria-disabled`, sem `title`, sem toast ao toque. **Blast radius
  medido:** dos 31 `disabled=` encontrados em `App.jsx` (`grep -c "disabled="`), 23 usos de
  `title=` no arquivo hoje são rótulos de componente (`ProfileTile`, `Fold`, `BackHeader`) —
  **nenhum** é mais usado como única explicação de controle desabilitado (correção do defeito
  original confirmada). Dos 2 controles efetivamente gateados por `appMode`/`operador`
  (`web/src/App.jsx:3788` botão Executar, `:3931` slider `allocPct`), ambos têm `disabled`
  HTML + parágrafo com link. O Toggle da linha 3924 é o **único** controle gateado por
  `appMode` sem `disabled` — 1 controle de blast radius.
- **Verificação:** código (`grep -n "disabled="` e `grep -n "title="` em `App.jsx`,
  contagem e cruzamento manual).
- **Possível duplicata:** UX-03 (plano 01-02 registra a faceta de acessibilidade do mesmo
  fato).
- **Recomendação:** aplicar `disabled={!operador}` (mesmo padrão do slider `allocPct` logo
  abaixo, linha 3931) no `Toggle` da linha 3924 — uma linha, sem mudança de lógica de negócio.

### F-CODE-08 — Suíte canônica: 970/970 testes de backend passaram; 7 de 74 testes web falharam por dependência de ambiente ausente (`web/node_modules`), não por regressão de produto — e os 7 incluem os guardiões dos 2 incidentes de paridade documentados
- **Requisito:** CODE-04
- **Severidade:** Médio — D-04: risco real de processo (uma verificação rodada num worktree
  novo, como este, pode reportar "suíte com falhas" sem que ninguém perceba que as falhas são
  de ambiente, não de produto — e nesse cenário específico, são exatamente os testes de maior
  valor que ficam sem cobertura). Sem incidente documentado deste cenário específico até
  agora.
- **Evidência:** `bash scripts/executar.sh --testes` — backend: `970 passed, 129 warnings in
  16.22s`. Web: 67 `[OK]`, 7 `[X]` — `test_appmode_sincroniza_servidor.mjs`,
  `test_carteira_nativa_sincroniza.mjs`, `test_fase2_portfolio.mjs`,
  `test_notif_central.mjs`, `test_notify.mjs`, `test_oauth_repassa_name_e_code.mjs`,
  `test_pet_resumo_modo_web.mjs`. Rodando cada um isoladamente
  (`node web/tests/<arquivo>.mjs`), os 7 falham com o MESMO erro:
  `Error [ERR_MODULE_NOT_FOUND]: Cannot find package '@capacitor/core' imported from
  .../web/src/persistence.js`. Confirmado: `web/node_modules/` não existe neste worktree
  (`ls web/node_modules` → "No such file or directory"). Os 2 arquivos mais relevantes desta
  auditoria — `test_carteira_nativa_sincroniza.mjs` (guardião do bug histórico #2, ver
  F-CODE-03) e `test_appmode_sincroniza_servidor.mjs` — estão entre os 7 bloqueados.
- **Verificação:** suíte executada (`bash scripts/executar.sh --testes`) + reprodução
  isolada de cada falha (`node web/tests/<arquivo>.mjs`) + confirmação da causa
  (`ls web/node_modules`).
- **Impacto:** nesta execução específica, não foi possível confirmar empiricamente que os
  guardiões dos bugs #2 (carteira nativa) e de sincronização de `appMode` ainda protegem o
  código — o resultado "passou" da suíte completa NÃO inclui esses 2 arquivos. Não há
  evidência de regressão real (o erro é 100% de resolução de módulo, não de asserção), mas
  também não há confirmação positiva.
- **Recomendação:** não corrigido nesta fase (rodar `npm install` está fora do escopo
  read-only e é excluído de auto-fix por política — pode mascarar dependência
  slopsquated/alterada). Documentar como pré-requisito operacional: qualquer execução da
  suíte canônica num checkout/worktree novo precisa rodar `npm install` em `web/` ANTES de
  `scripts/executar.sh --testes`, ou os 7 arquivos falham por ambiente e podem ser
  confundidos com regressão real.

### F-CODE-09 — Rejeição de ordem em `/api/buy`/`/api/sell` (caixa insuficiente, ticker sem cotação, ticker inválido) sem NENHUM teste de rota HTTP
- **Requisito:** CODE-04
- **Severidade:** Médio — D-04: risco real (mensagens/códigos de rejeição podem regredir
  sem que nenhum teste detecte), sem incidente documentado.
- **Evidência:** `server/app/main.py:1502-1518` — 3 caminhos de rejeição: `HTTPException(400,
  "Ticker invalido.")` (linha 1507), `HTTPException(502, "Sem cotacao para " + t)` (linha
  1510), `HTTPException(400, "Caixa insuficiente.")` (linha 1513). Busca
  (`grep -rln "Caixa insuficiente\|Sem cotacao para\|Ticker invalido" server/tests/*.py`):
  **zero arquivos**. `store.buy`/`store.sell` (o motor, sem a camada HTTP) TÊM boa cobertura
  em `server/tests/test_fase2_portfolio.py`, mas essa camada não valida caixa/cotação — quem
  valida é `main.py`. Único teste que chama `POST /api/buy`/`/api/sell`
  (`server/tests/test_ciclo_imediato_apos_carteira.py`) só exercita o caminho de sucesso
  (200), com cotação mockada sempre válida.
- **Verificação:** código (grep + leitura de `main.py`).
- **Impacto:** uma regressão que trocasse o código de status (ex.: 400→500) ou quebrasse a
  ordem das validações (ex.: checar caixa antes de validar ticker) passaria por toda a suíte
  sem ser detectada.
- **Recomendação:** 2-3 testes `TestClient` no padrão já usado em
  `test_ciclo_imediato_apos_carteira.py`/`test_gate_cadastro.py` (banco temporário, reimport
  de `app.main`): comprar com caixa insuficiente, comprar ticker sem cotação (mock retornando
  `None`), comprar ticker com `len(t) < 4`.

### F-CODE-10 — Recompra após venda parcial: preço médio reponderado não tem teste
- **Requisito:** CODE-04
- **Severidade:** Médio — D-04: risco real em cálculo financeiro (preço médio afeta PnL
  exibido), sem incidente documentado.
- **Evidência:** `server/app/store.py:539` — `existing["avg"] = round((existing["avg"] *
  existing["qty"] + price * qty) / total, 2)` roda em TODA compra que encontra posição
  existente, incluindo uma posição que sofreu venda parcial antes. `server/tests/
  test_fase2_portfolio.py` tem `test_sell_parcial_reduz_qty_e_preserva_preco_medio` (venda
  parcial preserva o PM — coberto) mas nenhuma sequência `buy → sell(qty parcial) → buy`
  (recompra) que confirme que o PM da posição RESIDUAL (pós-venda-parcial) é corretamente
  reponderado com o preço da nova compra. Buscado em `test_fase2_portfolio.py`,
  `test_persistence.py`, `test_multiuser.py`, `test_automacao.py` — nenhuma sequência dessa
  forma encontrada.
- **Verificação:** código (leitura de `store.py:530-544` + busca em 4 arquivos de teste).
- **Impacto:** um bug futuro na fórmula de reponderação (ex.: usar a quantidade ORIGINAL em
  vez da residual pós-venda-parcial) passaria pela suíte inteira sem ser detectado — PnL
  reportado ao usuário ficaria incorreto sem nenhum alarme.
- **Recomendação:** um teste `buy(100@30) → sell(qty=40) → buy(60@40)` e assert do `avg`
  resultante (deve ponderar 60 cotas remanescentes a 30 com as 60 novas a 40 = médias 35, não
  a média das 160 cotas originais).

---

## Paridade deviceStore x serverStore

**Comparação de existência (nomes):** extração estática de `web/src/persistence.js:110-208`
(`serverStore()`, 58 chaves) vs. `:441-1170` (interface exposta de `deviceStore()`, 58
chaves). **Conjunto idêntico dos dois lados — 0 assimetrias de nome hoje.** Única diferença
de assinatura: `_setDeviceScope` (`() => {}` no server, no-op documentado; `(id) { ... }` no
device) — intencional, comentário explícito no código.

**Guardiões dedicados confirmados** (checam explicitamente os DOIS nomes/assinaturas):

| Método/campo | serverStore | deviceStore | Guardião que cobre | Lacuna |
|---|---|---|---|---|
| `scanDeep`, `scanDeepEstimate` | sim | sim | `web/tests/test_deep_parity.mjs` (regex, `hits >= 2`) | não |
| `conceitos`, `conceito`, `assistente` | sim | sim | `web/tests/test_didatica_parity.mjs` | não |
| `syncPushPrefs` | sim | sim | `web/tests/test_didatica_parity.mjs` (checa ASSINATURA exata: `async syncPushPrefs() { ensure();` vs `syncPushPrefs: async () => {`) | não |
| `analysisOutcomesStats`, `analysisOutcomesCsv` | sim | sim | `web/tests/test_analysis_outcomes_ui.mjs` | não |
| `petResumo` | sim | sim | `web/tests/test_pet_ui.mjs` | não |
| `scan` | sim | sim | `web/tests/test_radar.mjs` (`scanDefs.length >= 2`) | não |
| `putConfig` | sim | sim | `web/tests/test_putconfig_so_o_que_mudou.mjs` (checa nº de chamadas, não paridade de nome diretamente) | parcial — não é guardião de PARIDADE, é de comportamento (debounce) |

**Os 51 métodos restantes** (58 − 7 explicitamente guardados acima): **sem guardião de
paridade dedicado**. 23 deles têm ao menos 1 referência indireta em algum teste de feature
(import/uso do store, não uma asserção de paridade); **28 têm zero referência em qualquer
arquivo de `web/tests/*.mjs`** — lista completa em F-CODE-04.

**Par `defaults.py` ↔ `catalog.js`:** apenas 2 chaves existem no dicionário
`default_llm_prompts()` (`server/app/defaults.py:161-217`) — `carteiraStopAlvo` e
`carteiraStopAlvoOperador` — ambas cobertas byte a byte por
`test_a8ii_paridade_defaults_carteira_com_catalog_js`. **Fora dessa comparação:**
`default_skill_text()`/`defaultSkillText()` (skill do Modo Estudo, sem marcador nem paridade
— F-CODE-05) e `default_skill_text_operador()`/`defaultSkillTextOperador()` (skill do Modo
Operador, só marcador de presença via `test_copy_theme.mjs`, não paridade de conteúdo).

---

## Verificado e conforme

- **CODE-02 (parte 1):** comparação de nomes entre `serverStore()` e `deviceStore()` não
  encontrou NENHUMA assimetria hoje — os 58 métodos existem nos dois lados com o mesmo nome.
  Comando usado: extração estática das chaves de nível superior dos dois objetos de retorno
  (linhas 110-208 e 441-1170 de `persistence.js`) e comparação de conjuntos. (A lacuna real
  reportada em F-CODE-04 é a AUSÊNCIA de um guardião que detectaria uma assimetria FUTURA, não
  uma assimetria existente hoje.)
- **CODE-02 (parte 2):** par `carteiraStopAlvo`/`carteiraStopAlvoOperador`
  (`defaults.py`↔`catalog.js`) é o único par de prompt com paridade byte-a-byte travada por
  teste (`test_a8ii_paridade_defaults_carteira_com_catalog_js`) — funciona como projetado, sem
  achado.
- **CODE-03:** o defeito original documentado em
  `docs/auditoria-controle-ordens-parametros.md` (2026-08-07) — botão "Executar" e "Entrada
  automática" desabilitados com `title` HTML como única explicação, invisível em toque
  (WKWebView/iOS não tem hover) — **está corrigido**. Confirmado em código:
  `web/src/App.jsx:3780-3803` (Executar) e `:3915-3945` (Entrada automática) hoje têm
  parágrafo sempre visível + botão "Trocar para Modo Operador →" (linhas 3798-3800,
  3940-3942), consistente com o próprio "Status (atualizado 2026-08-07)" do documento fonte
  (itens 1 e 2 marcados "feito, F10-20260807-07"). Nenhum dos 23 usos atuais de `title=` em
  `App.jsx` é mais a única explicação de um controle desabilitado — todos são rótulos de
  componente (`ProfileTile`, `Fold`, `BackHeader`). O achado residual (Toggle sem `disabled`,
  F-CODE-07) é uma instância NOVA e menor do mesmo padrão, não o mesmo defeito reaberto.
- **CODE-04 (falha silenciosa da fonte de dados):** o cenário mais perigoso já observado em
  produção (Yahoo devolvendo HTTP 200 com zero velas de B3) tem cobertura direta e específica
  — `server/tests/test_candle_provider.py::test_resposta_vazia_conta_como_falha`,
  `::test_serie_vazia_do_primario_cai_no_backup`,
  `::test_mistura_de_erro_e_vazio_soma_na_mesma_taxa`. Sem achado nesta sub-área.
- **CODE-04 (dado atrasado):** a tríade temporal (plano diário × barra 15min × timing
  determinístico) tem cobertura extensa em `server/tests/test_timing.py` (20+ testes,
  incluindo `test_montar_passada_velha_vira_sem_dado`, `test_avaliar_barra_de_ontem_nao_vira_
  estado_de_hoje`, `test_montar_aguardando_primeira_barra_do_dia`). Sem achado nesta
  sub-área.
- **CODE-04 (gate de modo no ciclo automático):** `agent.agent_params` força `mode=
  "sinalizar"` quando `app_mode != "operador"` — enforcement é server-side, não só de UI —
  coberto por `server/tests/test_agent_modo_estudo.py::test_agent_params_forca_sinalizar_
  fora_do_operador`. Sem achado nesta sub-área.
- **Suíte de backend:** `970/970` testes pytest passaram sem nenhuma falha real (129
  warnings, todos de depreciação de biblioteca — `on_event`/`asyncio.get_event_loop_policy`
  — não de lógica de produto).

---

## Cobertura dos fluxos financeiros críticos

| Fluxo | Testes que cobrem (arquivo::teste) | Camada | O que NÃO é coberto | Severidade da lacuna |
|---|---|---|---|---|
| 1. Execução de ordem (compra/venda, manual e automática) | `server/tests/test_fase2_portfolio.py` (motor: `test_buy_*`, `test_sell_*`); `server/tests/test_ciclo_imediato_apos_carteira.py` (rota HTTP, caminho de sucesso); `server/tests/test_automacao.py`, `test_agent.py` (execução automática pelo agente) | unit (motor) + integração (rota, só sucesso) | Caminhos de REJEIÇÃO em `/api/buy`/`/api/sell` (caixa insuficiente, sem cotação, ticker inválido) — zero testes de rota. Ver F-CODE-09 | Média |
| 2. Cálculo de PnL / preço médio / drawdown | `server/tests/test_fase2_portfolio.py` (`test_sell_total_comportamento_original`, `test_sell_parcial_reduz_qty_e_preserva_preco_medio`); `server/tests/test_persistence.py::test_snapshot_curva_retorno_drawdown`; `web/tests/test_finance.mjs` (motor espelho do front) | unit | Recompra após venda parcial (reponderação do PM da posição residual) — nenhum teste com sequência `buy→sell parcial→buy`. Ver F-CODE-10 | Média |
| 3. Falha da fonte de dados (inclusive HTTP 200 com zero velas) | `server/tests/test_candle_provider.py` (20+ testes, incluindo o cenário específico de falha silenciosa — ver "Verificado e conforme") | unit, com fetcher injetável (sem rede real) | Nada de relevante identificado — cobertura considerada adequada | Baixa |
| 4. Dado atrasado (carimbo, ressalva, tríade temporal) | `server/tests/test_timing.py` (20+ testes) | unit | Nada de relevante identificado — cobertura considerada adequada | Baixa |
| 5. Ordem rejeitada (caixa insuficiente, ticker sem cotação, gate de modo) | `server/tests/test_agent_modo_estudo.py::test_agent_params_forca_sinalizar_fora_do_operador` (gate de modo, coberto) | unit (gate) | Rejeição de `/api/buy`/`/api/sell` por caixa/cotação/ticker — ZERO testes de rota (mesma lacuna do fluxo 1, sub-caso "rejeição"). Ver F-CODE-09 | Média |

**Lacunas estruturais conhecidas (régua aplicada):**
- **Ausência de E2E/browser automation** (`TESTING.md`: "E2E tests: not present") — nenhum
  teste exercita a sequência completa escolher ativo → ordem → execução → resultado como o
  usuário realmente vive; a própria memória do projeto registra bugs "que só a verificação ao
  vivo pegou" (ex.: toque longo em setores, F10-20260807 e outros). **Severidade: Médio
  (D-04)** — risco real e recorrente pelo próprio histórico do projeto, sem se materializar
  necessariamente em CADA release.
- **Ausência de medição numérica de cobertura** (sem `pytest-cov`; `web/tests` não tem
  equivalente) — a suíte pode ter buracos que ninguém enxerga porque não há número/percentual
  para comparar entre releases. **Severidade: Baixo (D-05)** — a disciplina de "todo
  regressão vira guardião" mitiga bem na prática (confirmado pela profundidade real da
  suíte, 970 testes de backend), é uma lacuna de FERRAMENTA, não de disciplina observada.
- **Suíte web sensível a `node_modules` ausente, sem aviso diferenciado** (ver F-CODE-08 em
  detalhe) — um `ERR_MODULE_NOT_FOUND` de ambiente aparece com a mesma cara de uma falha de
  asserção real na saída de `scripts/executar.sh --testes`, sem distinção visual. **Severidade:
  Médio (D-04)**, incorporado como F-CODE-08 acima.

---

## Cobertura de requisitos

| Requisito | Achados | Status |
|---|---|---|
| CODE-01 | F-CODE-01, F-CODE-02, F-CODE-03 | com achados |
| CODE-02 | F-CODE-04, F-CODE-05 | com achados |
| CODE-03 | F-CODE-06 (verificado/conforme), F-CODE-07 | com achados |
| CODE-04 | F-CODE-08, F-CODE-09, F-CODE-10 | com achados |

---

*Verificação: `git status --porcelain server web web-admin` vazio ao final desta análise —
nenhum arquivo de produto ou teste foi criado/alterado.*
