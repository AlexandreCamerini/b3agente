---
phase: quick-261023-msp
plan: 01
status: complete
completed: 2026-10-23
---

# Quick 261023-msp — Summary

## Por tarefa

0. `setups.marcos_da_posicao` não recusa mais por R:R baixo (vira `parecer`, D-12). Commit 4c0b70fd.
1. `StopAlvoModal` mostra `m.parecer` em aviso tracejado quando `valido`. b0a47c97.
2. IN-01: chaves novas em `MARCOS_PLANO` (skill_ref ↔ copy.js ↔ lista do guardião de espelho): `modal_calculando`, `modal_calculo_motor`, `modal_parecer_aguardar`, `modal_ia_gauge`, `modal_marcos_calculando`, `modal_marcos_indisponiveis`, `modal_decisao_sua`. 9a4b4f44.
3. IN-05: bloco do plano esconde `bloco_breakeven` e usa `bloco_stop_legado` (chave nova, nos dois lados do espelho) quando `decisao !== "COMPRAR"`; `agent._avaliar_entradas` deriva `modo_txt` de `app_mode`. 5db59fcf.
4. IN-06(c): `gestaoVisivel` exige `!isNative || hasSession()`. 42019efd.
5. WR-03(c): helper `_reancorar_stop_inicial` (store.py) / `reancorarStopInicial` (persistence.js), usado em `set_position(manual)`, `store.buy` e `deviceStore.buy`/`putPosition` quando o lote é somado sem marcos do motor. 2 guardiões pytest + 2 casos .mjs. c880eec1.
6. `set_option_position` valida com `_marco_num` antes de mutar; rota PUT converte ValueError em 400 PT-BR; espelho em `deviceStore.putOptionPosition`. Guardiões pytest (`"abc"`, `True`) e .mjs. fc1d3eaf.
7. `notaStopAlvo` removida de copy.js (2 ocorrências); nota no comentário de `test_copy_theme.mjs` atualizada. 6768c84c.

## Desvios / pendente

- **Tarefa 2, parcial (pendente):** `acao_redefinir` ("Redefinir"), `regua_stop` ("STOP") e `regua_entrada` ("ENTRADA") NÃO viraram chaves. O guardião de `test_vocabulario_espelho.mjs` faz `!app.includes(valor)` em App.jsx inteiro; rótulos tão curtos colidem com `onRedefinir`, outro "STOP" (~3877 e modal) e texto "ENTRADA". Resolver exige mudar o texto visível ou o guardião (decisão de produto/guardião, não inventada). Também não migrei os `steps` do SweepGauge (marcado "se couber").
- Tentativa intermediária dessas 3 chaves foi corrigida antes de o commit da Tarefa 2 ser finalizado (amend, hash final 9a4b4f44).
- Arquivos não-meus aparecem no working tree ao final (`server/app/marcos_servico.py` modificado, `server/tests/test_marcos_fonte_unica.py` novo): não foram tocados nem commitados por esta execução.

## Testes rodados

- pytest: test_marcos_plano, test_skill_ref, test_marcos_vocabulario, test_marcos_agente, test_entrada_automatica, test_marcos_gravacao_store, test_marcos_rotas, test_agent_options — todos passam.
- node: test_vocabulario_espelho, test_marcos_ui, test_marcos_stores, test_marcos_espelho, test_modo_operador, test_copy_theme, test_api_parity — todos passam.
- `cd web && npx vite build` — exit 0.
- Suíte canônica e `cap copy` não rodados (conforme instrução).

## Adendo do orquestrador (2026-10-23): fonte única de marcos

O Alex enviou capturas do iPhone em que o mesmo ativo aparecia com números diferentes. Em produção, para PETR3 no mesmo momento:
- o card (Mesa/Monitoramento, `/api/timing`) mostrava o plano do Setup 9.3: entrada 66,46, stop 63,26, alvo 72,86;
- `/api/marcos` da posição recalculava por suporte: 65,70 / 64,74 / 67,62;
- no B3SA3, o modal mostrava "—" enquanto a explicação da IA citava 22,70 e 23,44.

Correção (a9f44964): `marcos_servico.marcos_para_posicao(snap, preco, avg, pos)` segue esta precedência:
1. marcos gravados na posição (vindos do servidor), se a geometria ainda vale;
2. o plano do setup que o card mostra (`plano_do_resultado`);
3. a proteção por suporte, só quando não há plano.

As 4 rotas (`/api/marcos` e as 3 de IA) recebem `pos=_posicao_aberta(scope, t)`. Chaves `origem_stop_gravado` e `origem_alvo_gravado` foram espelhadas. Guardião: `server/tests/test_marcos_fonte_unica.py` (4 testes). O stub de `test_marcos_ia.py` foi atualizado com nota (c0685ad6).

Suíte canônica: `bash scripts/executar.sh --testes` com rc=0 (3782 pytest; `.mjs` OK), depois de `vite build` e `cap copy ios`.

Pendente:
- iPhone **sem conta**: o servidor não conhece a posição local, então lá vale só a regra 2 ou 3 (o login é obrigatório pelo CLAUDE.md);
- prompt do N3 que cita níveis de suporte e resistência como se fossem stop e alvo (exige mudança byte a byte em `defaults.py` ↔ `catalog.js`);
- IN-06b (sizing sobre o patrimônio);
- publicação.

## Revisão independente (gsd-code-reviewer, Sonnet) e correções (af5d31d9)

**Corrigidos:**
- **WR-01:** reaplicar o mesmo stop não reancora o `stopInicial`, no `store.py` e no `deviceStore`.
- **WR-02:** o texto de origem "gravado" não promete mais "o mesmo do card".
- **WR-04 e WR-05:** o plano do card superado pelo preço e o marco gravado inválido viram aviso no `parecer`, em vez de trocar de fonte em silêncio.
- **WR-07:** `_marco_num` e o espelho JS exigem valor > 0; o JS aceita só string numérica estrita.
- **IN-02:** o parecer não formata "0" quando não há rr.
- **Testes:** `test_marcos_fonte_unica.py` tem agora 7 guardiões.

Suíte canônica: rc=0, 3785 pytest, todos os `.mjs` OK.

**Ficam para decisão do Alex:**
- **WR-03:** no iPhone sem conta, o servidor não vê a posição local.
- **WR-06:** em posição aberta, o alvo pode ser uma resistência com R:R ínfimo. Hoje isso gera só o parecer; a alternativa é buscar a próxima resistência que feche 1,5:1.
- **IN-01:** a semântica de `rr` difere entre os ramos.
- **IN-03:** `modo_txt` da entrada automática é código morto.
- **IN-04:** dupla leitura de `positions`.
