# Phase 38: KB Didática ampliada - Context

**Gathered:** 2026-09-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Usuário consegue buscar qualquer um dos 83 verbetes da KB de mecânica B3
(`server/app/kb.py`) e encontrar um link "saiba mais" contextualizado nas 4
abas que hoje não oferecem essa ponta de entrada (Acompanhar, Radar,
Watchlist, Opções — só Portfólio tem hoje, via o alerta de concentração
ligado a `abrirVerbete("diversificacao", ...)`). `SetorAlvo`/`ConceitoSheet`
saem de `App.jsx` para um módulo compartilhado, sem que `OpcoesScreen.jsx`
passe a importar nada de `App.jsx` (isolamento deliberado preservado,
`OpcoesScreen.jsx:20-24`).

</domain>

<decisions>
## Implementation Decisions

### Mecanismo de busca (KB-01)
- **D-01:** Busca livre por texto **e** navegação por família, na mesma
  tela — não é um toggle entre dois modos. Campo de texto no topo filtra a
  lista completa; sem texto digitado, a lista mostra as 9 famílias
  (`indicadores`, `estrutura`, `familias`, `modelos`, `setups`,
  `plano_risco`, `fundamentos`, `mercado_b3`, `estados_app` — 4 a 16
  verbetes cada) como seções/acordeão.
- **D-02:** `kb.buscar()` mantém a lógica de match atual (termo/frase
  completa com fronteira de palavra) — não estender para prefixo/substring.
  Zero risco de regredir o uso existente por `resolver()` (assistente).
- **D-03:** Sem limite de resultados na tela de navegação — mostra todos os
  que baterem. O `limite=5` de `kb.buscar()` foi desenhado pra responder 1
  pergunta do assistente, não pra filtrar uma lista; fica pro planner
  decidir se cria parâmetro/função nova sem tocar o comportamento que o
  assistente já usa.
- **D-04:** Busca é **live** (filtra a cada tecla), client-side sobre o
  catálogo completo já carregado — sem round-trip por letra. Implica que o
  front precisa buscar `catalogo()` completo uma vez (hoje só existe
  `GET /api/kb/buscar`, que devolve resultados já pontuados/limitados —
  **não existe endpoint que devolva o catálogo completo**; fica pro
  planner/pesquisa decidir a rota nova).
- **D-05:** Estado vazio (0 resultados): mensagem clara ("Nenhum verbete
  encontrado para '{termo}'") sem esconder a navegação por família abaixo —
  a pessoa continua podendo explorar por categoria mesmo sem match de
  texto.

### Onde a busca vive
- **D-06:** Dentro da aba Perfil — não abre ícone global novo nem entra na
  folha de ajuda existente. Perfil é hoje um hub de tiles (Preferências,
  Conta, IA & chaves, Observabilidade...) que abrem tela focada
  (`ProfileTile`, padrão de `App.jsx` em torno da linha 2471/2726); a busca
  de verbetes segue o MESMO padrão: um tile novo (ex.: "Aprender"/
  "Glossário") abrindo uma tela dedicada de busca. Não introduz mecanismo
  de navegação novo.
- Justificativa: 5 abas fixas na BottomNav é decisão travada do v1.5 (não
  reabrir); ícone global competiria por espaço no header com o `PetFab`
  (mascote) já fixo.

### Âncora do "saiba mais" por aba (KB-02)
- **D-07:** Cada uma das 4 abas (Acompanhar, Radar, Watchlist, Opções) abre
  sempre o MESMO verbete fixo — sem lógica condicional por contexto
  (ticker/setup ativo). Mesmo padrão simples que o link existente de
  Portfólio já usa (fixo em `"diversificacao"`).
- **D-08:** O `vid` exato por aba (qual dos 83 verbetes ancora cada uma) NÃO
  foi travado nesta discussão — é proposta do planner a partir do catálogo
  existente, revisada e aprovada pelo Alex no CONTEXT.md/plano antes de
  qualquer código (ver Claude's Discretion abaixo).

### Claude's Discretion
- Escolher o `vid` (dentre os 83 de `kb.py`) que ancora cada uma das 4 abas
  sem cobertura — critério: coerência temática com o que a aba mostra hoje
  (ex.: Acompanhar → família `estados_app`; Radar → família `setups`;
  Watchlist → família `indicadores`; Opções → família `estrutura` ou
  `mercado_b3`, o que fizer mais sentido olhando o conteúdo real da tela).
  Apresentar a escolha explicitamente no plano para aprovação do Alex antes
  de codar — não é uma decisão silenciosa.
- Mecanismo técnico de como `ConceitoSheet`/`store.conceito(cid)` (hoje
  resolve só via `conceitos.py`/`conceitos.montar()`) passa a abrir também
  verbetes de `kb.py` (que tem formato de dado diferente — ver
  `kb.formatar()`). Isso é implementação, não vai a `discuss-phase` — mas o
  researcher/planner DEVE endereçar essa ponte explicitamente, porque hoje
  as duas fontes (`conceitos.py` ancorado-em-números × `kb.py` estático) não
  se falam.
- Nome/label exato do tile novo em Perfil e da tela de busca.
- Rota/endpoint novo para expor o catálogo completo de `kb.py` ao front
  (D-04) — nome, formato, se cacheável.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### KB e camada didática
- `server/app/kb.py` — módulo da KB de mecânica B3: docstring no topo
  documenta o formato do verbete, as 9 famílias, e as funções públicas
  (`catalogo()`, `verbete()`, `buscar()`, `formatar()`, `resolver()`).
  `buscar()` (linha ~1602) e `formatar()` (linha ~1618) são o contrato atual
  — qualquer extensão deve ser aditiva, sem quebrar `resolver()` (usado por
  `/api/assistente`).
- `server/app/conceitos.py` — catálogo que `ConceitoSheet` renderiza hoje
  via `/api/conceito/{cid}` (`conceitos.montar()`); formato de saída
  diferente do `kb.formatar()` — ponte entre os dois é decisão de
  implementação (ver Claude's Discretion).
- `.planning/milestones/v1.4-phases/26-otimizacao-ux-ia/26-CONTEXT.md` —
  origem do backlog C1 (busca) e C2 (ancoragem); linha ~146-151 documenta a
  mesma decisão de UX pendente que esta discussão resolveu (D-01) e o
  constraint de isolamento do `OpcoesScreen.jsx` (idêntico ao success
  criterion #4 do ROADMAP).
- `.claude/skills/didatica-boris/SKILL.md` — regras de vocabulário por modo
  (Estudo/Operador) e princípios de dado da camada de entendimento; qualquer
  texto novo de verbete/explicação segue essa skill.

### Isolamento estrutural
- `web/src/OpcoesScreen.jsx:20-24` — comentário/import que declara o
  isolamento deliberado (zero import de `App.jsx`). O módulo compartilhado
  novo para `SetorAlvo`/`ConceitoSheet` deve ser importável por
  `OpcoesScreen.jsx` sem violar essa regra (ambos importam do módulo novo,
  nenhum importa do outro).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `kb.buscar(pergunta, limite=5)` (`server/app/kb.py:1602`) — pontuação
  determinística por termo/palavra inteira, já filtra por `familia` (campo
  presente em cada item do catálogo). Zero custo de LLM.
- `kb.formatar(v, modo)` (`server/app/kb.py:1618`) — formata um verbete pro
  vocabulário do modo atual (educacional/operador), com `veja` para
  navegação "veja também".
- `ProfileTile` (`web/src/App.jsx` ~linha 2471/2726) — padrão de tile do hub
  Perfil que abre tela focada; usar o mesmo pra "Aprender"/busca de
  verbetes.
- `A.abrirVerbete(cid, dados)` (`web/src/App.jsx:8624`) — único ponto de
  entrada existente pro "saiba mais" (hoje só chamado 1x, linha 4358, com
  `cid="diversificacao"`); é o padrão a replicar nas 4 abas novas.

### Established Patterns
- `SetorAlvo`/`ConceitoSheet` (`web/src/App.jsx:2848`/`2941`) vivem hoje
  dentro de `App.jsx`; `conceitoAberto` é estado do componente `App` raiz
  (linha 7783), repassado via objeto `A` (`abrirVerbete`/`trocarConceito`/
  `voltarConceito`/`closeConceito`, linhas 8619-8636).
- `kb.py` já deriva texto de `conceitos.montar()` quando o conceito
  coincide (gatilho, stop, alvo, r, confluência, fundamento, barra15m) —
  "REFERÊNCIA, NÃO CÓPIA" (docstring do módulo) — evita duas fontes de
  verdade pro mesmo texto.
- Paridade `defaults.py`×`catalog.js`/`deviceStore`×`serverStore` (guardrail
  do CLAUDE.md) não se aplica aqui — `kb.py` não tem espelho client-side,
  serve só via API.

### Integration Points
- `web/src/api.js:285` (`kbBuscar`) e `web/src/persistence.js:1188`
  (`store.kbBuscar`) já existem e não são consumidos por NENHUMA tela hoje
  — é a ponte de busca já pronta no client, só falta UI e (D-04) o endpoint
  de catálogo completo.
- `server/app/main.py:4595` (`GET /api/kb/buscar`) é a única rota de KB
  hoje — não existe rota de catálogo completo (D-04).

</code_context>

<specifics>
## Specific Ideas

- Nenhuma referência específica de UI trazida pelo Alex nesta discussão —
  as decisões ficaram no nível de mecanismo (D-01 a D-08), não de layout
  pixel a pixel. O gate de UI-SPEC (fase tem `UI hint: yes`) cobre o
  detalhe visual depois.

</specifics>

<deferred>
## Deferred Ideas

None — discussão ficou dentro do escopo da fase (busca KB-01 + ancoragem
KB-02). B2 (continuidade de estado da aba Opções) e C3 (consolidação de
registros de tela) são as Fases 39 e 40, não tocadas aqui.

</deferred>

---

*Phase: 38-KB Didática ampliada*
*Context gathered: 2026-09-23*
