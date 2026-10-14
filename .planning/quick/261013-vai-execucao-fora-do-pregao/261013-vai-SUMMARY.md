---
phase: quick-261013-vai
plan: 01
status: complete
note: Leva A (backend, Tarefas 1a/1b/2) e Leva B (front/iOS, Tarefas 3 e 4) concluídas.
completed: 2026-10-14
---

# Quick 261013-vai — Execução simulada fora do pregão (Leva A backend + Leva B front/iOS)

## Leva A

### Commits (só código)
- 397bb2fa — Tarefa 1a: portão em `_run_cycle_inner`, `_gatilho_saida`, `_avisar_fora_pregao` (ação), vocabulário `EXECUCAO_FORA_PREGAO`, helper de relógio, tabela F/A/T/D/S.
- e808a331 — Tarefa 1b: `_avaliar_opcoes(somente_vencimento)`, aviso genérico de opção, fixture `_pregao_aberto`, guardiões de `test_fase3_operador.py`, T5/V1–V9/B2.
- f91158bb — Tarefa 2: `_recusar_execucao_fora_do_pregao` (409) nas 6 rotas, run-now e `/api/cycle` com `mercadoFechado`, testes de rota R1–R8, fixture nos testes de rota de opções.

### Verifies
- 1a: test_execucao_fora_pregao, test_skill_ref, test_timing, test_entrada_automatica: verde.
- 1b: lista do PLAN verde com relógio real; `test_fase3_kill_switch_duracao.py` falha dentro do sandbox do executor (`[Errno 1] Operation not permitted` no alerta do kill-switch), mas PASSA no orquestrador (suíte canônica rc=0, 3599 pytest) — é limitação do sandbox, não regressão. Plugins fechado e aberto sobre os 8 arquivos do motor: verde.
- 2: lista do PLAN verde (fora do sandbox).
- Suíte backend INTEIRA (`tests/`), fora do sandbox: com plugin de relógio forçado FECHADO = 3599 passed, 5 skipped, 3 xfailed; com plugin forçado ABERTO = 3599 passed, 5 skipped, 3 xfailed. Plugins em $TMPDIR (apagados): `pytest_configure` troca `app.pregao.in_market_hours` (fechado: False com `now is None` salvo dev flag; aberto: instante quarta 14:00 BRT).
- Dentro do sandbox, ~50 testes falham por `PermissionError`/rede (yahoo, benchmark, texto_vazio, owner, etc.) — ruído de sandbox, não regressão.
- NÃO rodei suíte canônica, `cap copy ios`, vite build, nem testes `.mjs` (fora da leva).
- Observação: no momento da execução o relógio real era quarta 10:09 BRT (pregão aberto), então os testes antigos passavam "sem plugin" por acaso; a prova de independência do relógio são as duas rodadas com plugin.

### Testes legados ajustados (nada apagado; nenhuma asserção afrouxada)
Todos receberam fixture `autouse` `_pregao_aberto` (quarta 2026-10-14 14:00 BRT via `abrir_pregao`, nota `2026-10-13 (quick 261013-vai)`); a asserção antiga continua a mesma, só o relógio ficou determinístico.
- Motor: `test_agent.py`, `test_agent_options.py`, `test_agent_modo_estudo.py`, `test_push_payload.py`, `test_push_prefs_classes.py` (fixture nomeada `_pregao_aberto_fixture_vai` porque o arquivo já define `_pregao_aberto` como helper), `test_fase3_operador.py`.
- Rotas de opções: `test_fase5_rejeicao_rotas.py`, `test_gate_liquidez_rotas.py`, `test_opcoes_collar_rota.py`, `test_opcoes_lastreadas_rotas.py`, `test_curadoria_collar_rota.py`, `test_opcoes_cota_reserva_rotas.py`, `test_opcao_descoberto_gate.py`, `test_opcoes_anatomia_rota.py`, `test_fuso_dias_ate_vencimento.py`.
- Não precisaram de fixture (passaram sob relógio fechado e aberto): `test_opcoes_lastreadas_vencimento.py`, `test_mydata_budget_prioridade.py`, `test_ciclo_imediato_apos_carteira.py`, `test_rotas_fase4.py`, `test_fase3_kill_switch_duracao.py`.
- Guardião textual `test_fase3_operador.py::test_laco_avisa_dentro_do_pregao`: asserção antiga (split em `if not kill_switch_on() and in_market_hours():` sobre o arquivo todo) → substituta (mesma asserção, mas recortando antes o corpo de `async def scheduler_loop`), nota `2026-10-13 (quick 261013-vai)`. Guardião novo `test_portao_de_pregao_antes_de_qualquer_execucao_no_ciclo` (ordem do portão, `somente_vencimento=True` único no ramo fechado, `continue` antes de `nivel_trailing(`/`store.sell_option(`, `_avisar_fora_pregao` sem `option_quotes_getter`).
- Nota de datas: o PLAN pede "2026-10-14" para as substitutas; usei a data do PLAN/CONTEXT ("2026-10-13") nas notas dos fixtures e "quick 261013-vai" no resto. Troque se quiser exatamente `2026-10-14 (quick 261013-vai)` (mudança só de comentário).

### Desvios e decisões de discretion
- [Rule 3] `agent._agora_brt()` novo (ponto único do relógio do Diário/vencimento; `_today`/`_now_str` passam por ele) para testes fixarem data/hora sem tocar `datetime` global. `relogio_pregao.injetar_relogio` mexe só em `pregao.in_market_hours`; `injetar_data`/`fixar_instante` fixam também `agent._agora_brt` (separado para o fixture de pregão aberto não mover a data dos testes antigos).
- Na 1a já passei `optionPositions` a `_avisar_fora_pregao` (o PLAN previa só na 1b); o ramo de opção foi testado na 1b.
- `/api/options/sell` registra a rejeição com `qty` do corpo (ou a qty da posição quando ausente; `None` se não numérico).
- Estruturas (curadoria/abrir-collar, lastreada/abrir, abrir-collar, fechar): 409 SEM linha de rejeição no history (discretion do PLAN). `/lastreada/fechar` idem (sem `tipo`).
- Posição do helper nas rotas: depois do 403 de Modo Estudo e das validações 400 de corpo, antes da checagem de estado 409 (já existe lastreada) e de qualquer chamada ao provedor/re-derivação.
- Guardião R7 remove docstrings antes de comparar índices (a docstring de `abrir-collar` cita `opcoes_lastreadas.propor`).

### Limitações conhecidas (para o SUMMARY final)
1. Vencimento liquida com o spot do ativo-objeto lido no 1º ciclo que o alcança (no scheduler, o 1º ciclo do pregão do dia do vencimento, ~10:00; fora do pregão, o spot do payload no momento do ciclo). Liquidar pelo fechamento (ADR-005) é follow-up.
2. Aviso de opção fora do pregão é genérico por desenho (D2-emenda).
3. Estruturas multi-perna recusadas com 409 não ganham linha de rejeição no history.

Follow-up: liquidar o vencimento pelo fechamento do dia (ADR-005) — hoje liquida com o spot lido no 1º ciclo que o alcança.

## Leva B

### Commits (só código)
- 4303c5e4 — Tarefa 3: espelho `execucaoForaPregao` em `copy.js` (+ `execucaoForaPregaoTxt`, falha alta), `horaMinutoBRT`, portão em `deviceStore.cycle`, `mercadoRef`/setInterval/`A.cycle`/`A.*` de opções no `App.jsx`, `test_vocabulario_espelho.mjs` (EXECUCAO_FORA_PREGAO), `test_execucao_fora_pregao.mjs` (H1, C1–C9, estáticos).
- 68f023ec — Tarefa 4: `bloqueioMercado` nos componentes de opções + `test_opcoes_mercado_fechado_ui.mjs` + 2 guardiões ajustados.
- dab82c66 — fix: `mercadoRef` movido para junto de `cycleRef` (o guardião `test_status_mercado_ui.mjs` fatia 1800 caracteres após o `useState(mercado)` e meu bloco empurrou o cleanup para fora da janela).

### Verifies
- Tarefa 3 (lista do PLAN + vite build): verde. Tarefa 4 (lista do PLAN + vite build): verde.
- Loop COMPLETO de `web/tests/*.mjs` (226 arquivos, um por vez): único vermelho final = `test_ios_assets.mjs` (bundle iOS desatualizado, esperado — `cap copy ios` é do orquestrador). Num primeiro loop também falhou `test_status_mercado_ui.mjs` (corrigido em dab82c66, regressão real do meu posicionamento).
- `npx vite build` ok. Não rodei suíte canônica nem `cap copy ios`.

### Guardiões alterados (asserção antiga -> substituta)
- `test_vocabulario_espelho.mjs`: nada alterado; só acrescentados `EXECUCAO_FORA_PREGAO` (DICTS/CHAVE_JS/CHAVES_ESPERADAS) com nota `2026-10-13 (quick 261013-vai)`.
- `test_carteira_opcoes_tira.mjs` e `test_opcoes_proposta_ui.mjs`: regex `function PropostaLastreada\(\{ r, ..., onVerbeteLiquidez \}\)` -> mesma regex aceitando `(?:, bloqueioMercado)?` ao final (assinatura exata continua exigida, só admite o campo novo), nota `ATUALIZADO 2026-10-14 (quick 261013-vai)`. Motivo: `test_opcoes_multi_candidato_ui` exige `disabled={busy || degradado}` literal e a prop precisa entrar pela assinatura.
- Nada apagado.

### Desvios e decisões
- [Rule 1] `T.warn` não é token permitido em `web/src/opcoes/` (`test_opcoes_jornada_ui`/`test_opcoes_caminho_b_ui`): motivo do bloqueio usa `T.textPrimary` (`T.textSecondary` em `ExecutarProposta`, cuja paleta local não tem `textPrimary`). Sem hex, sem token novo.
- CandidatoOpcao/PropostaLastreada: `disabled={busy || degradado}` intacto; motivo de mercado via `aria-disabled` + `aria-describedby` + `onClick` inerte. ConfirmarEstrutura/ExecutarProposta/CuradoriaEstruturas: `|| !!bloqueioMercado` na definição da trava, `disabled={...}` byte-idêntico. PernasAbertas: ramo novo `aria-disabled` antes da confirmação (bloqueia inclusive o 2º passo).
- `AbaRecomendadas` não está montada em lugar nenhum (Fase 48); recebe e repassa a prop mesmo assim.
- deviceStore.cycle: falha de cotação fora do pregão não derruba o ciclo (remarcação é leitura); status indeterminado grava um evento warn `status_indeterminado` a cada ciclo (sem dedupe, por desenho do PLAN). Fechado não grava resumo "Ciclo executado".
- `OpcaoContrato` legado do App.jsx fica protegido só pelo throw em `A.buyOption`/`sellOption` (flash com a frase), sem mudança visual.
- `A.executarCandidatoCurado` lança o erro de mercado fechado ao painel do card (como o 409 do servidor).
- Status do mercado nulo/erro NÃO bloqueia os botões nem o caminho manual de opções: o servidor é a autoridade (409).

### Não verificado em runtime
- Nenhuma checagem visual/VoiceOver da aba de Opções com o pregão fechado (só guardião estático por leitura de fonte + build).
- Ciclo local no iPhone real (WKWebView, relógio do aparelho) e `cap copy ios`: só em Node com fetch/Date stubados.
- `bloqueioMercado` com `ctx.mercado.abertura` real do servidor: coberto só por regex de fonte, sem renderização React.

## Interfaces que a Leva B consome

### Vocabulário (`skill_ref.EXECUCAO_FORA_PREGAO`, 10 chaves idênticas nos 2 modos; educacional = `estudo` no front)
Função: `execucao_fora_pregao_txt(modo, chave, **dados)`; modo desconhecido -> educacional; placeholder sem valor -> ValueError; chave desconhecida -> KeyError. Placeholders: `{ticker}`, `{motivo}` ("stop"|"alvo"), `{abertura}` ("HH:MM"), `{contrato}`. Textos (copiar byte a byte de `server/app/skill_ref.py`, bloco `EXECUCAO_FORA_PREGAO`, logo antes de `RETORNO_ACUMULADO`):
- `aviso_diario` (operador/educacional diferentes), `aviso_opcao` (diferentes), `ciclo_fechado` (diferentes, usa `{abertura}`), `ciclo_fechado_sem_hora` (diferentes), `status_indeterminado` (diferentes).
- `opcao_bloqueada` ("Mercado fechado — a B3 abre às {abertura}; nenhuma ordem de opção é executada fora do pregão."), `opcao_bloqueada_sem_hora` ("Mercado fechado — nenhuma ordem de opção é executada fora do pregão.") — iguais nos 2 modos.
- `opcao_bloqueada_acao` (diferentes).
- `botao_bloqueado` ("Mercado fechado — abre às {abertura}"), `botao_bloqueado_sem_hora` ("Mercado fechado — execução só no pregão") — iguais nos 2 modos.
Cada valor é UMA string literal numa linha só, sem aspas internas (parser do guardião cruzado). O guardião py é `test_s1_vocabulario` em `server/tests/test_execucao_fora_pregao.py`.

### kv `avisoForaPregao` (por escopo)
`{"data": "YYYY-MM-DD" (BRT), "chaves": ["acao:PETR4", "opcao:PETRK30", ...]}`. Data diferente de hoje zera a lista. Chave de ação `acao:<ticker>`; de opção `opcao:<contractId>` (= `pos["id"]`). Evento de Diário: `{"time": "dd/mm HH:MM", "kind": "warn", "t": <ticker|underlying>, "text": ...}` SEM `tag` (sem push). Ação só avisa se `_gatilho_saida` (stop vence alvo) com a cotação já buscada; opção só se NÃO vencida (`expiration > hoje`), sem `lastro` e com `stop` e/ou `alvo` definidos, sem preço no texto.

### Respostas com mercado fechado
- `POST /api/agent/run-now`: 200 `{"ok": true, "iniciado": false, "mercadoFechado": true, "mensagem": <ciclo_fechado com abertura "10:00">}`; não cria task; grava a mesma frase no Diário (kind info). Aberto: `{ok, iniciado: true, mensagem}` como antes. Kill-switch continua 409 (prioridade antes do portão).
- `POST /api/cycle`: 200 com `public_state` + `quotes` (+ `mercadoFechado: true` e `mensagem: <ciclo_fechado>` quando o portão fechou). Campos ausentes quando aberto. `run_cycle_for` devolve `mercadoFechado: True` no dict interno.
- Modo da frase: `operador` se `config.appMode == "operador"`, senão `educacional`. `abertura` fixa `pregao.ABERTURA` ("10:00").

### 409 das rotas de execução de opções
`HTTPException(409, {"code": "mercado_fechado", "message": <opcao_bloqueada com abertura>, "action": <opcao_bloqueada_acao>, "abertura": "10:00"})`. Rotas: `/api/options/buy`, `/sell`, `/curadoria/abrir-collar`, `/lastreada/abrir`, `/lastreada/abrir-collar`, `/lastreada/fechar`. 403 de Modo Estudo (abrir/fechar) vem antes. `PUT /api/options/position/{id}` e `PUT /api/position/{ticker}` nunca bloqueados; leituras livres.

### `somente_vencimento` (contrato)
`agent._avaliar_opcoes(..., somente_vencimento=False)`. Com `True` (ramo fechado): considera só posições com `expiration <= hoje BRT`; pula `expiration == hoje` antes de 10:00 BRT (`pregao.ABERTURA`); nenhuma chamada ao provedor se não sobrar vencida; liquida lastreada (`store.liquidar_lastreada_vencida`, tag `protecao-opcao`) e legado (`store.close_option_vencida`) com o spot do payload do ciclo, mesmos eventos/`_bump_ops`; nunca trailing/stop/alvo. O retorno do ciclo fechado carrega `executed` das liquidações. O iPhone deve espelhar: vencimento roda em "fechado" e "indeterminado", `hoje` via `hojeBRT()` (não UTC), pula o dia do vencimento antes das 10:00 BRT.

## Self-Check
- Arquivos e commits conferidos: 397bb2fa, e808a331, f91158bb existem; temporários ($TMPDIR) apagados; nenhum commit de SUMMARY/PLAN/CONTEXT/STATE.

## Verificação do orquestrador (2026-10-14)
- Gate entre levas: suíte canônica no fim da Leva A (fora do sandbox) rc=0, 3599 pytest + .mjs, antes de liberar a Leva B.
- Suíte canônica após a Leva B (com vite build + cap copy ios): rc=0, 3599 pytest + todos os .mjs (test_ios_assets verde após o cap copy).
- Decisão do Alex registrada no CONTEXT (D2-emenda, 2026-10-14): aviso de opção genérico e sem preço, servidor e iPhone.
- Não verificado em runtime: UI de Opções com o pregão fechado (a verificação aconteceu com o pregão aberto, quarta 10:24); ciclo local num iPhone real; resposta 'mercado fechado' do Rodar agora em produção.
