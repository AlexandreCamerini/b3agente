# Phase 12: Limites do plano gratuito ativos - Context

**Gathered:** 2026-08-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Ativar de verdade os dois limites do plano gratuito que `server/app/plan.py`
já desenha tecnicamente (`max_watchlist=10`, `max_analyses_per_month=30`),
fechar o caminho que hoje bypassa o gate de watchlist, e ajustar a copy de
recusa pra tirar o tom de CTA/upgrade urgente. Sem loja, sem IAP, sem UI
nova (isso é Fase 13).

</domain>

<decisions>
## Implementation Decisions

### Ativação dos limites
- **D-01:** `PLAN_FREE.max_watchlist = 10`, `PLAN_FREE.max_analyses_per_month = 30`. `PLAN_PRO` continua com ambos `None` (ilimitado).

### Gap real encontrado no scout — gate de watchlist tem bypass
- **D-02:** `POST /api/watchlist/add` (`server/app/main.py:1069`) já chama `plan.can_add_ticker` corretamente — isso já funciona. Mas `PUT /api/watchlist` (`server/app/main.py:1041-1044`, `store.set_watchlist` direto) **não passa por nenhum gate**, e o frontend usa esse mesmo endpoint pra dois fluxos de adicionar ticker: `App.jsx:7087` (`store.putWatchlist([...wl, t])`, quick-add) e `App.jsx:7254` (seleção em massa do catálogo, `catalogSel`). Sem fechar isso, CAP-01 fica furado — dá pra passar de 10 ativos pelo catálogo em massa, ignorando o limite inteiro.
- **D-03 (recomendado, decisão travada):** `PUT /api/watchlist` passa a checar o limite também, mas **só quando o novo tamanho da lista é MAIOR que o atual** (`len(tickers_novos) > len(watchlist_atual)`) — nunca bloqueia remoção nem reordenação. Se o resultado ultrapassa `max_watchlist`, recusa com `HTTPException(402, reason)` igual ao `POST /add`, usando o mesmo `plan.can_add_ticker`-style check (comparar o tamanho FINAL contra o limite, não incremento a incremento).
- **D-04 (grandfather clause, recomendado):** Usuário que hoje já tem mais de 10 ativos (porque o limite era `None` até agora) **não é forçado a remover nada** — continua vendo e operando a watchlist inteira. O gate só impede CRESCER além do limite a partir de agora; não deleta nem trava o que já existe. Isso é consistente com ADR-010 ("ativação é reversível e gradual") e com o princípio de não-destrutivo do CLAUDE.md.

### Copy de recusa (CAP-07)
- **D-05:** Só `can_add_ticker` precisa de ajuste de copy — o texto atual é `"O plano {id} permite ate {limit} ativos. Faca upgrade para adicionar mais."` (tom de CTA). Novo texto, sem CTA: `"Voce atingiu o limite de {limit} ativos do plano {id}."` — mesmo padrão de `can_analyze`, que já está conforme (`"Voce atingiu o limite de {limit} analises/mes do plano {id}."`, sem CTA, já correto hoje).

### Conta anônima
- **D-06:** Conta anônima (sem login, `scope=None`) cai no fallback `ACTIVE_PLAN` (= `PLAN_FREE`) — já é o comportamento atual de `current_plan(None)`, sem mudança necessária. Os dois limites passam a valer igual pra ela.

### Claude's Discretion
- Exato texto de log/teste para provar D-02/D-03 (redação dos testes de comportamento) fica a critério do planner/executor, desde que cubra: (a) `PUT` bloqueia crescimento além do limite, (b) `PUT` nunca bloqueia redução/reordenação, (c) usuário já acima do limite não perde ativos existentes.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Decisão de produto (o que já foi decidido, não reabrir)
- `docs/adr/010-planos-e-cap-gratuito.md` — decisão técnica completa (unidade do cap, separação cap-comercial vs. cota física, comportamento ao atingir o cap, o que falta nascer)

### Contrato de contagem
- `server/app/plan.py` — hooks `can_add_ticker`/`can_analyze`/`current_plan`, contrato C-32 documentado no docstring do módulo (gate de plano nunca mantém contador próprio)
- `server/app/metering.py` — contador real por usuário, fonte da contagem mensal (contrato C-33)

### Call sites a modificar/verificar
- `server/app/main.py:1041-1080` — `PUT /api/watchlist` (sem gate, precisa ganhar), `POST /api/watchlist/add` (já gateado, referência de como recusar)
- `server/app/main.py:437-453` — `_gate_analise`, único ponto de decisão de análise (já correto, não mexer na lógica, só confirmar)

### Milestone
- `.planning/PROJECT.md` — seção "Current Milestone: v1.3 Cap comercial (plano gratuito)"
- `.planning/REQUIREMENTS.md` — CAP-01..CAP-07 (v1), CAP-08..CAP-11 (v2, fora desta fase)
- `.planning/ROADMAP.md` §Phase 12 — success criteria formais

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `plan.can_add_ticker(current_count, plan)` — já retorna `(bool, motivo)`, só falta o segundo call site (PUT) chamá-lo
- `HTTPException(402, reason)` — padrão já estabelecido em `watchlist_add` pra recusa de limite comercial; reusar o mesmo status code em `PUT /api/watchlist`

### Established Patterns
- Contrato C-32/C-33: gate de plano (mensal, TIER) sempre lê contagem de uma fonte única (`metering.py` pra análises, `len(watchlist)` pra ativos) — nunca mantém contador paralelo
- Mensagens de recusa no padrão do módulo: fato + motivo, sem CTA (`can_analyze` já é o exemplo correto a seguir)

### Integration Points
- `PUT /api/watchlist` (`main.py:1041`) é o ponto de integração que falta — precisa do mesmo padrão de gate que `POST /api/watchlist/add` já tem, mas com a semântica "só bloqueia crescimento" (D-03)

</code_context>

<specifics>
## Specific Ideas

Nenhuma referência específica de UI/copy além do já capturado em D-05 — o texto exato virou decisão travada nesta discussão, não uma diretriz aberta.

</specifics>

<deferred>
## Deferred Ideas

- Expor o número de uso/limite na tela — é a Fase 13 inteira, não repetir aqui
- Loja/IAP, preço, features avançadas do plano pago — fora do milestone v1.3 (CAP-08..11, v2)

### Reviewed Todos (not folded)
- `medir-rate-limit-mydata.md` (score 0.6 no match automático) — revisado e **não** dobrado: é sobre rate-limit do mydata (fonte de dados), domínio completamente diferente de cap comercial. Match automático foi falso positivo por palavras genéricas ("real", "tem"); descartado deliberadamente nesta fase.

</deferred>

---

*Phase: 12-limites-do-plano-gratuito-ativos*
*Context gathered: 2026-08-29*
