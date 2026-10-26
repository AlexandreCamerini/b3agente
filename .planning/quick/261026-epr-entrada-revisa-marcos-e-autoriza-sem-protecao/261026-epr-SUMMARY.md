---
phase: quick-261026-epr
plan: 01
status: complete
---

# Quick 261026-epr: entrada revisa marcos no preço atual e autoriza sem proteção

Commits: a583b316 (vocabulário), e1dea0f7 (servidor), mais o commit do front (ver git log).

- Servidor: `marcos_servico.marcos_para_compra` (fonte única prévia == gravação); `/api/buy` aceita `protecao` "sem"/"motor" (ausente = comportamento antigo); `/api/marcos` aceita `compra` e `recalcular`.
- Vocabulário: 7 chaves em MARCOS_PLANO nos dois modos, espelhadas em copy.js e no guardião.
- Front: BuyModal com prévia, recalcular, checkbox de gravar e autorização explícita; confirmBuy não abre StopAlvoModal com "sem"; StopAlvoModal com Recalcular.
- Testes: pytest marcos_*/skill_ref 207 ok (6 novos); node test_marcos_compra_ui, test_marcos_ui, test_api_parity, test_vocabulario_espelho, test_rr_min_fonte_unica ok; `npx vite build` ok.

## Pendências / observações
- Plano mandava trailer "Opus 5.5"; usado como no plano.
- Pendentes: `marcos` do novo caminho vão sem gatilho/invalidação efetivos quando a fonte é suporte (revalidação tolera None); não há teste dedicado de execução de pendente com marcos do caminho "motor".
- Prévia usa a cotação de `quotes[t]` do cliente como referência; o preço executado é o do servidor (pode divergir levemente; revalidação ocorre no /api/buy).
- Suíte canônica e `cap copy` não rodados (orquestrador).

## Plano 02 — correções da revisão independente

Commits: 0997a4f3 (vocabulário), f97770a7 (servidor R1/R3/R4/R5/R7), 07c72dc3 (api.js + persistence.js, R1/R3/R6), 2d64da09 (App.jsx R1/R2/R3/R7 + guardiões).

- R1: `/api/buy` com `protecao:"motor"` compara `previa` com `marcos_para_compra` no preço executado; divergência, motor inválido ou sem snapshot -> 409 `previa_mudou` (marcos novos + mensagem), sem histórico, imediato e pendente. BuyModal fica aberto com prévia nova, aviso e autorização zerada. `/api/marcos` devolve `precoRef`/`calculadoEm`; prévia exibe o carimbo. deviceStore sem sessão espelha o 409 (erro com status/detail).
- R2: efeito com preço arredondado nas deps, debounce 800 ms (primeira busca imediata), sem preço = loading, autorização zera ao mudar status/par.
- R3: `store.buy` devolve bool; rota usa `compra_marcos_mantidos`. Opção 2 escolhida: servidor pula cálculo e comparação quando a posição já tem stop/alvo válidos (média projetada); front mostra `compra_previa_mantem_marcos`.
- R4: `recalcular` chama `marcos_da_posicao` direto (`fonte: "recalculo"`), antes do ramo de setup. R5: fallback por suporte em `marcos_para_compra`. R6: protecao ausente = caminho antigo sem `compra:true`.
- R7: pendente "sem" usa `ordem_sem_marcos_autorizada`; `confirmBuy` não abre StopAlvoModal com `s.marcos` gravado; aria-live só no texto de status; motivo sob o Confirmar; duplo toque por `buyEnvioRef` antes do await (liberado no catch/finalizar). Desvio: não marquei `confirmado` antes do await porque ele dispara o pulso de sucesso (guardião MOTION-02).
- Guardiões atualizados (localizador `confirmBuy: async (protecao, previa) => {` e `disabled` com termos extras, com nota; asserções semânticas mantidas): test_fase23_motion, test_historico_rejeitada, test_ordens_pendentes_ui.
- Testes: pytest test_marcos_compra/test_marcos_rotas/test_skill_ref + -k "buy or marcos or pending or compra or store" (277 ok); .mjs vocabulario_espelho, rr_min_fonte_unica, api_parity, marcos_ui, marcos_compra_ui, marcos_stores, fase23_motion, historico_rejeitada, ordens_pendentes_ui; `npx vite build` ok.
- Pendente/limitação: a checagem `mantem` do servidor usa média projetada; se o front mostrar "mantém" e o servidor julgar os marcos inválidos, cai no 409 e o usuário revê. Suíte canônica e `cap copy` não rodados (orquestrador).

## Orquestrador (2026-10-26)

- O texto de estudo de `compra_sem_protecao_check` deixou de sugerir "prejuízo ilimitado" (c99ff457).
- A revisão independente (gsd-code-reviewer, Sonnet) do plano 01 gerou o plano 02 (R1–R7), aplicado pelo executor.
- Os 3 guardiões `.mjs` quebrados pela nova assinatura de `confirmBuy` foram atualizados com nota, sem afrouxar as asserções.
- A comparação da prévia era exata, o que dispararia 409 a cada centavo do alvo projetado. Agora tem tolerância de 1% (mín. R$ 0,01), com espelho no deviceStore e 2 guardiões.
- Suíte canônica rc=0: 3802 pytest e todos os `.mjs`.

Não verificado:
- tela no iPhone ou navegador (exige login);
- publicação.
