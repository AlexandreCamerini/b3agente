# 42-06 — Checkpoint humano (execução autônoma parou aqui)

Data: 2026-09-27 (execução agendada 01:30, autorizada pelo Alex em 2026-09-26 23:59).
Status: **aguardando o Alex**. Os planos 42-01..42-05 estão completos e commitados
localmente em `v2/interacao-estrutural` (sem push). O 42-06 não foi executado além
da preparação automática da Task 1, por dois motivos:

1. Task 1 é `checkpoint:human-verify` bloqueante: leitura do card em < 3 s e
   DP-1..DP-4 respondidas **por nome** pelo Alex. Isso não se automatiza.
2. Task 2 (bump + publicar + push + fast-forward de `origin/main`) e o push da
   Task 3 foram vetados na instrução da execução ("NÃO publicar, NÃO push, NÃO
   deploy"). A Task 3 (fechar REQUIREMENTS/ROADMAP/STATE) depende das respostas
   às DPs e do BUILD_ID publicado — fica junto.

Não existe `42-06-SUMMARY.md` de propósito: o índice do GSD trata SUMMARY como
"plano completo".

## Preparação automática da Task 1 (feita)

| Verificação | Resultado |
|---|---|
| `bash scripts/executar.sh --testes` (fora do sandbox) | exit 0 — pytest **3050 passed, 5 skipped, 3 xfailed**; web **168/168 `.mjs` OK** |
| Baseline Fase 41 | 3050 pytest / 165 `.mjs` → +3 guardiões novos (`test_sinal_helpers`, `test_cor_confiabilidade`, `test_sinal_chip_ui`) |
| `cd web && npx vite build` | exit 0 |
| `git diff --stat cf7c36d -- server/` | vazio — motor intocado |
| `npx cap copy ios` | feito (local, `web/ios` é gitignored) — resolve o drift que derrubava `test_ios_assets.mjs` depois de cada `vite build` |

Não subi backend + Vite locais para o roteiro: ninguém estaria olhando às 2h.
Para rodar o roteiro: `bash scripts/executar.sh`, viewport 375px.

## Verificação independente (gsd-verifier, 42-01..05)

`42-VERIFICATION.md`: **passed** no escopo 42-01..05, sem gap. COR-01, HIER-01, HIER-02, CHIP-01 e CHIP-02 verificados no código. Guardrail CVM, canal de cor, motor e paridade sem violação. 13 guardiões com nota de reversão, nenhum apagado, +410 asserções líquidas.

## Roteiro para o Alex (do 42-06-PLAN, sem alteração)

1. Radar, Modo Estudo, card de UGPA3 (ou outro ativo com manchete direcional contra o regime; se nenhum estiver assim hoje, usar o que tiver `gatilhoAlinhado` falso em tendência e dizer isso). Em < 3 s: qual é o veredito? O que é contexto? Há ou não vantagem estatística medida?
2. Mesmo card no Modo Operador: caixa entrada/stop/alvo SEM a régua duplicada; anel dentro da manchete; nada verde/vermelho fora de manchete/preço/P&L/níveis de stop-alvo.
3. Watchlist com o mesmo ativo: mesma ordem de leitura; regime e plano agora aparecem; nenhum chip de direção/convicção/qualidade da IA.
4. Ativo sem setup (confluência 0): anel ausente, manchete/motivo dizem a ausência.
5. Tema claro e escuro nos dois modos (4 combinações): o estado "sem vantagem medida" legível em âmbar.
6. Tocar o anel (camada de entendimento ligada): abre a explicação de confluência; tocar o chip de fundamento: abre fundamento.

## Decisões de planejamento — responder POR NOME

- **DP-1 — "No tema claro, o fundo âmbar do 'sem vantagem medida' está com 4% de opacidade: contraste 4,68:1 (passa AA 4,5:1, fica 0,02 abaixo da meta interna de 4,7:1). A alternativa é 3,6% (4,70:1, tint quase imperceptível). Mantém 4%, ou prefere 3,6%?"**
- **DP-2 — "A marca 'a favor / contra a tendência' só aparece quando o regime é de tendência (alta ou baixa). Em regime lateral ou indefinido ela é omitida, porque não há tendência para estar a favor ou contra. Aprova?"**
- **DP-3 — "A contagem 'x/y critérios' saiu do cabeçalho do Radar (o rótulo do anel absorveu setup e lado); os critérios continuam em '+ Ver critérios do setup'. Aprova?"**
- **DP-4 — "A Watchlist passou a mostrar regime e o bloco de plano (o dado já vinha do scan, sem API nova), e o selo de elegibilidade mudou de pílula redonda para o chip de cantos de 7px em todas as telas, inclusive na lista de setups do Operador IA. Aprova?"**

Informativo (não é pergunta): o carrossel de alertas da home mantém pill própria e anel de 52px (fora do AtivoCard); o app iOS só recebe a mudança num build novo de TestFlight.

## Divergências para decidir junto (achadas na execução)

1. **"FUNDAMENTO" aparece duas vezes na `FundamentoTabela`** (`web/src/App.jsx` ~1572 e ~1576): o `<span>` de cabeçalho que já existia e o rótulo do `SinalChip` novo. Correção de 1 linha, mas é escolha de produto (qual dos dois sai). Não corrigi.
2. **3 guardiões fora da lista do 42-05 foram reconciliados** (`test_modo_operador.mjs`, `test_radar.mjs`, `test_setup_operavel_adr017.mjs`), com nota datada, sem apagar nada. Vale olhar o diff: `git diff cf7c36d -- web/tests/`.
3. O executor do 42-05 usou `git stash`/`pop` uma vez no checkout principal (não é worktree). Revertido na hora, sem perda — a suíte completa deu o mesmo resultado antes e depois. Registrado por transparência.

## Decisões autônomas (consolidadas da fase)

Orquestração:
- Execução sequencial na árvore principal (`workflow.use_worktrees=false`), executor `sonnet`.
- Nenhum mutador do `gsd-sdk` chamado (nem `state.begin-phase`); STATE/ROADMAP editados à mão após cada onda (commits `docs(phase-42): update tracking after wave N`).
- Gate pós-onda: suíte canônica completa só na onda 1 e no fim; nas ondas 2-4, suíte web completa rodada pelo executor + `git diff -- server/` vazio (planos só de front).
- Suíte do backend rodada fora do sandbox: dentro dele, 27 testes falham com `PermissionError` no trust store SSL (artefato do sandbox, não do código).
- `npx cap copy ios` (local) para eliminar o drift `web/dist` × `web/ios`.
- 42-06 parado no checkpoint (ver topo).

Por plano (detalhe em cada SUMMARY, seção "Decisões autônomas"):
- 42-01: `ladoDoMotor(null)` via `motor || {}` (o default param literal do plano lançava TypeError com `null`).
- 42-02: borda `borderSubtle` no elegível (pedida pelo plano); fallback de `warnTint10` no guardião de contraste.
- 42-03: variáveis órfãs removidas do `HistoricoPill`; 4 flags nomeadas em `PlanoOperacionalBloco` para o guardião recortar o ramo Operador.
- 42-04: `decBg` mantido no destructuring do `vm`; Radar não tocado (transição prevista até o 42-05).
- 42-05: 3 guardiões extras reconciliados; `FUNDAMENTO` duplicado não corrigido; `git stash` usado uma vez.

## Para retomar

Depois de responder às DPs e aprovar (ou listar divergências → plano de gap):
`/gsd-execute-phase 42` retoma no 42-06 (Task 1 já preparada; seguem Task 2 publicar e Task 3 fechar docs).
