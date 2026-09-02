# Phase 13: Uso real visível na interface + enforcement no iOS - Context

**Gathered:** 2026-08-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Duas entregas relacionadas, ambas sobre o cap comercial do plano gratuito
que a Fase 12 já ativou no backend:

1. **Visibilidade (CAP-06):** expor os dois números reais de uso/limite
   (ativos na watchlist, análises de IA no mês) na UI, nos dois stores
   (web/PWA e app iOS nativo), nunca estimado ou escondido.
2. **Enforcement no iOS (CAP-12):** fechar o bypass achado no code review da
   Fase 12 (CR-01, `12-REVIEW.md`) — `deviceStore.putWatchlist`/
   `addWatchlistTicker` gravam direto no `localStorage` sem checar limite
   nenhum; passam a checar o `max_watchlist` real antes de gravar.

Mais dois itens de escopo fechado (não são gray areas, só execução):
limpeza de resíduos textuais do rename BolsIA→Boris+ em dois arquivos
nomeados, e um checkpoint humano (nome do app no App Store Connect/
TestFlight — fora do repositório).

</domain>

<decisions>
## Implementation Decisions

### Placement dos contadores (CAP-06) — única área discutida a fundo
- **D-01:** Contador de **ativos** (watchlist) em dois pontos:
  - Ponto de ação: `CatalogModal` (`web/src/App.jsx:6618`) — a linha hoje
    mostra `{catalogSel.length} de {data.catalog.length} selecionados`;
    estende para incluir o par uso/limite do plano free (ex.: "7 de 40
    selecionados · 7/10 do plano free").
  - Visão passiva: subtítulo da tela Watchlist (`cp.subtituloWatchlist`,
    `App.jsx:3427-3428`) ganha um segmento adicional (ex.: "· ativos:
    7/10"), visível sem precisar abrir o modal de edição.
- **D-02:** Contador de **análises do mês** na seção de IA da tela Config/
  Perfil (`App.jsx:4991-5018`, onde já existe a estimativa de custo
  BYOK/gerenciado) — nova linha "análises deste mês: X/30", mesma vizinhança
  de informação (uso de IA), sem criar tela nova.
- Opções descartadas explicitamente: "minimalista" (só no ponto de ação, sem
  visão passiva na Watchlist) e "centralizado" (um card de plano único na
  tela Perfil, nada espalhado) — o usuário escolheu a opção dual porque
  combina visibilidade proativa (subtítulo, sempre à vista) com o número
  exato no momento em que a ação pode ser bloqueada (CatalogModal).

### Exibição no plano Pro — assumido, não discutido a fundo
- **D-03 (premissa declarada):** Quando o plano ativo não tem limite
  (`max_watchlist`/`max_analyses_per_month` são `None`, hoje só `PLAN_PRO`),
  os três pontos acima **não mostram nenhum contador** — nem "X/∞", nem
  "ilimitado". Justificativa: critério de sucesso 5 exige "sem número
  fabricado"; omitir é mais simples e mais alinhado ao princípio de nunca
  simular um teto que não existe. Se o Alex preferir mostrar "ilimitado"
  explicitamente em vez de omitir, é um ajuste pequeno no planejamento —
  sinalizar se divergir desta premissa.

### iOS: comportamento em falha ao buscar o limite real — assumido, não discutido a fundo
- **D-04 (premissa declarada):** Se `deviceStore` não conseguir confirmar o
  `max_watchlist` real (endpoint novo indisponível/offline) no momento de
  adicionar um ativo, a adição é **bloqueada** (fail-closed) com uma
  mensagem de "não foi possível confirmar o limite do plano agora, tente de
  novo" — não um erro genérico, não uma adição silenciosa. Justificativa:
  princípio 4 do CLAUDE.md ("impede operações dependentes de dados
  inválidos"), e porque para watchlist **não existe** gate autoritativo no
  servidor (diferente de análises, que sempre passam por `_gate_analise` no
  `POST /api/analyze`) — esta checagem local é a ÚNICA linha de defesa
  contra o CR-01 reabrir. Divergente do padrão de falha-aberta já usado em
  `analisesNoMes()` (aceitável lá porque o servidor é a autoridade real);
  aqui a autoridade é o próprio cliente, então falha-aberta reabriria o
  bypass.

### iOS: cadência de busca do limite — assumido, não discutido a fundo
- **D-05 (premissa declarada):** Busca ao vivo a cada tentativa de adicionar
  um ticker (mesmo padrão hoje usado por `analisesNoMes()`/`aiQuota()` —
  chamada de rede direta, sem cache local), não uma camada de cache nova.
  Justificativa: é o padrão já estabelecido no arquivo para esse tipo de
  leitura server-authoritative; introduzir cache criaria uma janela extra
  de dado desatualizado justamente no gate mais crítico da fase.

### Claude's Discretion
- Nome exato/rota do endpoint novo de watchlist quota (ex.:
  `/api/watchlist/quota` vs. estender a resposta de `GET /api/watchlist`
  existente) — decisão de implementação, sem impacto de produto/UX.
- Redação exata da mensagem de bloqueio no iOS (D-04) e do texto de erro/
  indisponível nos três pontos de exibição (critério de sucesso 3) — deve
  seguir o vocabulário canônico existente (`copy.js`/`skill_ref.py`), sem
  inventar tom novo.
- Limiar de "quase no limite" (se o planner decidir destacar visualmente
  quando o usuário está perto do teto, ex. 9/10 ou 28/30) — não foi pedido
  como requisito, fica a critério de quem planeja/implementa.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap e requisitos da fase
- `.planning/ROADMAP.md` (seção "Phase 13: Uso real visível na interface +
  enforcement no iOS", linhas ~185-230) — goal, 9 success criteria, deps
- `.planning/REQUIREMENTS.md` — CAP-06, CAP-12 (a fase também fecha CAP-07 do
  front, ver `web/src/plan.js`)
- `.planning/PROJECT.md` — milestone v1.3, decisões travadas (cap por conta
  vs. cota física da brapi; fonte de cotação não é diferencial de plano)

### Achado que originou CAP-12
- `.planning/phases/12-limites-do-plano-gratuito-ativos/12-REVIEW.md` —
  CR-01 (bypass do cap no iOS, com os dois caminhos de fix sugeridos pelo
  reviewer; o critério de sucesso 6 desta fase já escolheu a variante
  "porta o check local pro deviceStore", não "deviceStore vira thin wrapper
  do servidor")
- `docs/adr/010-planos-e-cap-gratuito.md` — decisão comercial e técnica do
  cap (limites, camadas independentes cap-por-conta vs. cota-física-brapi)

### Guardrails de repositório relevantes
- `CLAUDE.md` (raiz do repo) — princípio 3 (fonte/horário/atraso do dado),
  princípio 4 (nunca inventar valor, bloquear operação com dado inválido),
  princípio 5 (cálculo determinístico, nunca pela IA), seção "Paridade
  obrigatória" (deviceStore ↔ serverStore, método/campo novo entra nos
  DOIS), contrato C-32/C-33 (fonte única, nunca contador paralelo)

**No external specs beyond the above** — requisitos numéricos (10 ativos,
30 análises/mês) já estão travados desde a Fase 12; esta fase não reabre
esses números.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `server/app/plan.py` — `PLAN_FREE`/`PLAN_PRO` (`max_watchlist`,
  `max_analyses_per_month`), `can_add_ticker`, `can_grow_watchlist_to`
  (adicionado no WR-02 da Fase 12) — fonte única dos números; o endpoint
  novo desta fase deve ler daqui, nunca hardcodar 10/30.
- `server/app/main.py:461-479` (`ai_quota`) — padrão exato a espelhar para o
  endpoint novo de watchlist quota: `monthUsed`/`monthLimit` em nível raiz
  da resposta.
- `web/src/persistence.js:1140-1152` (`analisesNoMes`) — padrão de "leitura
  ao vivo do servidor, sem contador próprio no aparelho" a repetir para o
  contador de watchlist no `deviceStore`.
- `web/src/App.jsx:7257-7272` (`A.analyze`) — padrão de pré-check client-side
  com fail-open documentado (aceitável ali porque o servidor é autoritativo);
  NÃO repetir esse fail-open para o check de watchlist no iOS (ver D-04).

### Established Patterns
- Padrão "X/Y" de uso/limite já existe em dois lugares: orçamento brapi
  (`App.jsx:5714`, "orçamento brapi: X/Y hoje · cota X/mês") e cota por
  usuário/dia no admin (`App.jsx:5569`). Reaproveitar o mesmo formato
  textual para os contadores novos, não inventar um componente visual novo.
- `CatalogModal` (`App.jsx:6603-6665`) já é o ponto único de adicionar/
  remover tickers da watchlist — extensão natural para o contador de
  ativos, sem criar tela nova.

### Integration Points
- `web/src/persistence.js` — `deviceStore.putWatchlist`
  (linhas 791-798) e `deviceStore.addWatchlistTicker` (linhas 799-838) são
  onde o check de `max_watchlist` entra no iOS, ANTES do `write()`.
- `web/src/plan.js` — mirror do `server/app/plan.py`; hoje com limites
  `null` e frase de CTA ("Faça upgrade para adicionar mais.") que precisa
  sair (mesma correção de tom do CAP-07 backend, Fase 12).
- Endpoint novo de watchlist quota entra em `server/app/main.py`, próximo ao
  bloco existente de `/api/watchlist*` (linhas ~1043-1110).

</code_context>

<specifics>
## Specific Ideas

Mockup aprovado pelo Alex (opção "Dual — ação + visão passiva"):

```
WATCHLIST (subtítulo)
┌────────────────────────────────┐
│ Ativos monitorados              │
│ em estudo · cotações 14:32      │
│ · ativos: 7/10                  │
└────────────────────────────────┘

CATALOGMODAL (ao editar)
┌────────────────────────────────┐
│ Editar watchlist                │
│ 7 de 40 selecionados · 7/10     │
│ do plano free                   │
└────────────────────────────────┘

CONFIG/PERFIL (seção IA)
┌────────────────────────────────┐
│ Custo estimado (BYOK/gerenciado)│
│ R$ 3,20 hoje                    │
│ análises deste mês: 12/30       │
└────────────────────────────────┘
```

</specifics>

<deferred>
## Deferred Ideas

Nenhuma — a discussão ficou dentro do escopo da fase. Os itens não
aprofundados (exibição no Pro, fail-open/closed no iOS, cadência de busca)
foram fechados como premissa declarada (ver `<decisions>`), não como ideia
adiada.

### Reviewed Todos (not folded)
- `.planning/todos/pending/cap-watchlist-robustez-code-review.md` (WR-01/
  WR-02/WR-03 do code review da Fase 12) — **não dobrado porque já está
  resolvido**: o próprio arquivo diz "nenhum foi corrigido inline", mas o
  `12-REVIEW.md` (seção "Status de correção") e o `ROADMAP.md` confirmam que
  os 3 foram corrigidos em 3 commits atômicos e mergeados via PR #26. Este
  todo ficou desatualizado (escrito antes dos commits de correção) — vale
  deletar/arquivar, não é trabalho pendente para esta fase.
- `.planning/todos/pending/medir-rate-limit-mydata.md` — fora de escopo,
  pertence ao ciclo de virada de produção do mydata (Fase 9, já rastreado em
  `PROJECT.md` Active), não à Fase 13.

</deferred>

---

*Phase: 13-uso-real-vis-vel-na-interface-enforcement-no-ios*
*Context gathered: 2026-08-29*
