# Quick Task 261013-vai: Execução simulada fora do pregão — Context

**Gathered:** 2026-10-13
**Status:** Ready for planning
**Origem:** achado W4 da quick 261013-u7w (snapshot diário). Inventário (Explore, 2026-10-13) confirmou: o motor executa stop/alvo/trailing/alvo dinâmico, opções do agente e ENTRADA automática a qualquer hora quando disparado fora do scheduler; o iPhone (deviceStore.cycle) idem; rotas manuais de opções executam com prêmio possivelmente velho.

<domain>
## Task Boundary
Nenhuma EXECUÇÃO simulada acontece fora do pregão (calendário B3 + horário, `pregao.in_market_hours()`), no servidor e no iPhone. REGISTRAR stop/alvo continua sempre permitido (guardrail "stop/alvo nunca são vetados" — o portão afeta só a execução).

FORA de escopo: ordem pendente de opção; mudar o mecanismo de ordens pendentes de ações (já correto: com mercado fechado vira pendente e executa no 1º ciclo do pregão); preço oficial de abertura (continua o spot do primeiro ciclo).
</domain>

<decisions>
## Implementation Decisions (LOCKED — Alex, 2026-10-13)

### D1. Portão único no motor (servidor)
- `_run_cycle_inner` (server/app/agent.py:875-1029) não executa NADA (stop, alvo, trailing, alvo dinâmico, `_avaliar_opcoes`, `_avaliar_entradas`) fora de `in_market_hours()`. O portão usa o wrapper `in_market_hours` do próprio agent.py (que delega a `pregao.in_market_hours`, lido em tempo de chamada) — assim herda feriados, after-market opt-in (`B3_AFTER_MARKET`) e `B3_DEV_MERCADO_ABERTO` (staging), e os dois estilos de monkeypatch dos testes funcionam.
- Cobre todos os chamadores: scheduler (já gated), `_disparar_ciclo_imediato` (main.py:5258; chamado após PUT /api/position, buy/sell e fluxos de opções), `POST /api/agent/run-now` (main.py:5406) e `POST /api/cycle` (main.py:5300).
- `PUT /api/position` (registrar stop/alvo) continua funcionando sempre; só a avaliação/execução é adiada.
- Ordens pendentes de ações: inalteradas.

### D2. Aviso no Diário, execução na abertura
- Fora do pregão, se a cotação disponível indicar que um stop OU alvo seria atingido, o ciclo NÃO executa e registra no Diário UMA vez por posição por dia (dedupe) um evento determinístico: "Mercado fechado: stop/alvo de <ticker> será avaliado na abertura do próximo pregão" (copy por modo; nada de promessa de preço). Sem push de execução.
- Na abertura, o primeiro ciclo do scheduler reavalia com o preço corrente: executa se ainda atingido — com o gap real (pode ser pior que o stop). A copy do evento/diário explica isso de forma educativa (Estudo = professor; Operador = mesa).
- `POST /api/agent/run-now` e `/api/cycle` com mercado fechado: resposta clara "mercado fechado — nada foi executado; avaliação na abertura" (estado completo, princípio 9); o front mostra essa mensagem (botão Rodar agora App.jsx ~7866/7969; `A.cycle` ~10450/6727).

### D3. iPhone (paridade)
- `deviceStore.cycle()` (web/src/persistence.js ~1987-2008) e o `setInterval` do modo autônomo (App.jsx ~10563) aplicam o MESMO portão, usando o status de mercado que o front já consome (`/api/market/status`, api.js:453; mesma guarda das notificações locais App.jsx ~10617). Status indeterminado (offline/erro) → NÃO executa. Mesmo aviso de Diário local (D2). Paridade deviceStore ↔ serverStore e test_api_parity.

### D4. Opções manuais bloqueadas com aviso
- Rotas de EXECUÇÃO de opções recusam com mercado fechado: `/api/options/buy` (main.py:3029), `/api/options/sell` (:3090), `/api/options/lastreada/abrir` (:4230), `/abrir-collar` (:4315), `/fechar` (:4500), `/api/options/curadoria/abrir-collar` (:3693) — HTTP 409 com mensagem PT-BR acionável ("Mercado fechado — a B3 abre às 10:00; nenhuma ordem de opção é executada fora do pregão") e `detail.action/hint` no padrão do repo. Rotas só de LEITURA/simulação (cadeia, escada, payoff, proposta) continuam livres.
- UI de Opções: botões de executar/abrir/fechar desabilitados (ou com `aria-disabled` + explicação, conforme o padrão de acessibilidade do repo — guardiões proíbem `disabled=` em alguns componentes; seguir o padrão existente) mostrando "Mercado fechado — abre às HH:MM". Fonte do estado: o mesmo status de mercado do front.
- Agente (`_avaliar_opcoes`) coberto por D1.

### Claude's Discretion
- Forma exata do evento de Diário e da dedupe; nomes; onde mora o helper de "seria atingido" (reusar a lógica existente de stop/alvo, sem conta nova no front).
- Testes: o portão deixa testes de `run_cycle_for` dependentes do relógio real — fixture/monkeypatch explícito de pregão aberto (via `agent.in_market_hours` e `pregao.in_market_hours`), NUNCA `B3_DEV_MERCADO_ABERTO` como muleta. Casos novos com relógio injetado: fora do horário (noite, fim de semana, feriado, antes das 10:00, entre 16:55 e 17:30, after-market opt-in), dev forçado, PUT /api/position fora do pregão grava e não executa, run-now fechado, rotas de opções 409, iPhone fechado/indeterminado.
- Guardiões: test_fase3_operador.py:255-270 (split textual da linha do scheduler) e demais — toda alteração com substituta e nota `2026-10-13 (quick 261013-vai)`; nada apagado.
</decisions>

<specifics>
## Inventário (Explore, 2026-10-13) — pontos-chave
- Motor: agent.py:875-1029 (fluxo), preço `quotes_data[t]["price"]` :909 (spot cacheado/último do provedor), `store.sell(... motivo stop|alvo, origem automatico)` :962, eventos/push :999-1025, `_avaliar_entradas` :681 (entradaAuto + appMode operador). Scheduler gate :1308; wrapper `agent.in_market_hours` :369-379.
- Chamadores: run_cycle_for em agent.py:1465, main.py:5270 (_disparar_ciclo_imediato), :5300 (/api/cycle), :5420 (run-now). `_disparar_ciclo_imediato` chamado em main.py:2858, 2964 (buy/sell imediatos), 3010 (PUT /api/position), 3850/4309/4489/4586 (opções).
- Front: rodarAgora App.jsx:7866/botão :7969; A.cycle :10450, botão :6727, setInterval :10563; guarda de notificações :10617; MarketStatusBadge :988. Opções: HubOpcoes.jsx:66-74 (selo), OpcoesScreen.jsx:793-799 (`mercadoAberto`).
- iOS: deviceStore.cycle persistence.js:1987-2008 (breachStop/hitAlvo → this.sell).
- Pendentes: pending_orders.py (COMPRA/VENDA de ação; executar_pendentes :201 com o lote de cotações do scheduler).
- /api/market/status main.py:1783-1796.
- Testes ligados: test_agent.py, test_agent_options.py, test_agent_modo_estudo.py, test_fase3_operador.py, test_ciclo_imediato_apos_carteira.py, test_ordens_pendentes_*, test_fase5_rejeicao_rotas.py, test_rotas_fase4.py, test_opcoes_lastreadas_rotas.py, test_opcoes_lastreadas_vencimento.py, test_push_*.
- App.jsx ~164k tokens: NUNCA ler inteiro. Sem dependências novas, sem worktree, sem publicar/push. Executor roda guardiões tocados + testes novos + pytest dos módulos tocados + `npx vite build`; suíte canônica e `cap copy ios` com o orquestrador.
</specifics>

<canonical_refs>
- ./CLAUDE.md (princípios 2, 9; "preço de execução respeitando os dados disponíveis"; stop/alvo nunca vetados; paridade dos stores; guardiões não se apagam)
- .claude/skills/didatica-boris/SKILL.md (copy por modo)
- .planning/quick/261013-u7w-snapshot-diario-do-patrimonio-no-servido/261013-u7w-SUMMARY.md (achado W4)
</canonical_refs>

## D2-emenda (LOCKED — Alex, 2026-10-14)
Aviso de stop/alvo de OPÇÃO com o mercado fechado = **aviso genérico, sem preço**: para cada posição de opção (não vencida) com stop e/ou alvo definidos, o Diário registra "Mercado fechado: stop/alvo da opção <contrato> será avaliado na abertura" — UMA vez por posição por dia (dedupe `opcao:<contractId>`), SEM afirmar que seria atingido e SEM nenhuma leitura de prêmio/cota fora do pregão. Vale no servidor E no iPhone (D3). Ações mantêm o aviso "seria atingido" do D2 (cotação da ação já é lida no ciclo). Substitui a "decisão B1 do orquestrador" (cache/peek), que fica descartada.
