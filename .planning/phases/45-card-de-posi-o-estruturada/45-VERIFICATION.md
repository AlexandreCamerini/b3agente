---
phase: 45-card-de-posi-o-estruturada
verified: 2026-09-30T00:00:00Z
status: human_needed
score: 4/4 critérios do ROADMAP e 6/6 requisitos verificados em código; 11/11 decisões atendidas; 5 itens só com olho humano ou backend em produção
overrides_applied: 0
re_verification: false
human_verification:
  - test: "Abrir Posições no iPhone/PWA com UGPA3 (ações + put 33,25 + call 42,00) contra backend que tenha a Fase 44 e preço real de opções"
    expected: "Chip ESTRUTURA · COLLAR, resultado total, régua de faixa, 2 pernas, sem 'sem stop' nem R:R —"
    why_human: "O backend da Fase 44 não está em produção; sem ele o card cai em 'falha' por desenho. Só se vê o card completo com provedor real."
  - test: "Estados carregando e falha (timeout 30s / 502) no aparelho"
    expected: "Card atual + aviso discreto ('Lendo a estrutura…' / 'Estrutura indisponível agora') + botão Atualizar; sem aviso falso de stop"
    why_human: "Depende de latência e falha reais da rota. Em código o comportamento está verificado (estadoLeitura, mostraAvisoSemStop)."
  - test: "Mercado fechado e dado atrasado: linha de fonte/horário do card"
    expected: "Fonte e horário vindos da rota, ou 'sem horário da fonte'; nada inventado"
    why_human: "Depende de a rota carregar source/at em cada regime de mercado."
  - test: "Olho humano nas 4 combinações tema×modo (claro/escuro × Estudo/Operador) e 5 estados"
    expected: "Legibilidade, régua com rótulo 'hoje' sem colisão, alvos de toque de 44px"
    why_human: "O guardião de contraste mede razões, mas não julga layout. Após as correções pós-teste local (45-04) não houve novo teste no navegador."
  - test: "Botão 'Ver encerramento em Opções…' no aparelho"
    expected: "Abre Opções > Oportunidades com o painel do ticker aberto; bloqueado com o motivo do motor quando o prêmio está indisponível"
    why_human: "Navegação de fluxo ponta a ponta"
---

# Fase 45: Card de posição estruturada — Relatório de verificação

**Objetivo:** o card de Posições mostra a estrutura inteira, com estados claros, sem aviso falso.
**Verificado sobre:** código atual do branch `v2/interacao-estrutural`, HEAD d68e5ff0.
**Status:** human_needed. Nenhum gap bloqueante. Os itens humanos dependem de olho no aparelho ou do backend da Fase 44 em produção.
**Re-verificação:** não (verificação inicial).

## Critérios do ROADMAP

| # | Critério | Status | Evidência |
|---|----------|--------|-----------|
| 1 | UGPA3 mostra collar, resultado total, régua de faixa e as 2 pernas | VERIFICADO (código) | `CardPosicaoEstruturada` (App.jsx:4515) renderiza `chip_estrutura` com `e.nomeTexto`, `r.total` com `numDe`, `<ReguaFaixa/>` e `<ul>` de `e.pernas`, sempre visível. Guardião `test_estrutura_card_ui` cobre. Confirmação com preço real está em `human_needed`. |
| 2 | Sem "sem stop" nem `R:R —` em estrutura protegida; piso/teto em texto do motor | VERIFICADO | `mostraAvisoSemStop(p,"estruturada",e)` só dispara sem stop e sem `stopTexto`. `mostraRR(p)` exige stop E alvo, e no card o R:R só renderiza quando `rr != null`. Piso/teto vêm de `e.faixa.piso/teto` e `e.faixa.textos`. Em carregando/falha o aviso fica suprimido (D-03). |
| 3 | 5 estados renderizam; Encerrar bloqueado com motivo se prêmio indisponível | VERIFICADO | `tomDoEstado` mapeia vigente (linha), ate_5_dias/exercicio_provavel (âmbar), premio_indisponivel (info), vencida (encerrada, com link ao histórico). O botão fica `disabled` com `aria-describedby` para `e.encerrar.texto` do motor. |
| 4 | AA nas 4 combinações; `vite build` e guardiões verdes | VERIFICADO | `test_estrutura_card_contraste` exit 0. `npx vite build` ok. Todos os guardiões abaixo com exit 0. |

## Requisitos

| Req | Status | Artefato | Guardião |
|-----|--------|----------|----------|
| CARD-01 resultado total ações+prêmio | SATISFEITO | `r.total`, `r.acoes`, `r.pernasCotadas` do motor. Sem soma no cliente. | `test_estrutura_card_ui` |
| CARD-02 régua piso/teto/hoje/PM | SATISFEITO | `ReguaFaixa` (App.jsx:4443), `dominioRegua`/`posRegua` puros, `role="img"` com aria, pontas abertas "sem piso/teto" | `test_estrutura_card_ui/logica` |
| CARD-03 todas as pernas | SATISFEITO | lista `e.pernas` fora de qualquer acordeão | `test_estrutura_card_ui` |
| CARD-04 5 estados + Encerrar bloqueado | SATISFEITO | `tomDoEstado`, botão `disabled` com motivo | `test_estrutura_card_logica` |
| CARD-05 sem aviso falso | SATISFEITO | ver critério 2 | `test_estrutura_card_logica` |
| CARD-06 badge, textos, COR-01, SP, AA, aria, âncora | SATISFEITO com reversão deliberada (D-11) | `tipoPillTravada`, `TravaPill contorno`, `ESTRUTURA_CARD` em `skill_ref.py` com espelho em `copy.js`, `test_ritmo_sp` estendido | `test_estrutura_card_espelho/contraste`, `test_ritmo_sp`, `test_estrutura_card_vocab.py` |

REQUIREMENTS.md traz a nota de reversão de CARD-06/D-11. Os checkboxes CARD-01..06 e a tabela ainda estão em "Pending". A atualização fica com o orquestrador.

## Decisões D-01..D-11

| D | Status | Evidência |
|---|--------|-----------|
| D-01 `store.optionsProposta(t,true)` por ativo, em paralelo | OK | `useEstruturasPosicao` (App.jsx:4372); `executarComTeto(thunks,3)` limita a concorrência a 3 para proteger a cota. Sem rota nova (`git diff -- server/app` não mostra rota). |
| D-02 sem `optionPositions`, sem chamada | OK | `tickersComPernas`; `estadoLeitura` devolve "atual". |
| D-03 carregando/falha com card atual + aviso, sem "sem stop" | OK | App.jsx:4930-4945; `mostraAvisoSemStop` só habilita em "atual" e "estruturada". |
| D-04 recarga ao abrir e após buy/sell/fechar; sem polling | OK | `assinaturaEstrutura` (qty, avg, ids, modo) dispara o efeito. Botão "Atualizar" opcional presente. |
| D-05 Encerrar só navega | OK | `ctx.goOpcoes("oportunidades",{abrirTicker})`; `abrirTickerOpcoes` valida contra a carteira (T-45-04). Nenhum caminho de execução novo. |
| D-06 um botão, bloqueado com `encerrar.texto` | OK | Renomeado para "Ver encerramento em Opções…" na decisão do Alex (ab840193). |
| D-07 `PlanRuler` sai da estruturada | OK | O card novo usa `ReguaFaixa`. O `PlanRuler` continua só no ramo legado. |
| D-08 mantidos: Stop/alvo (IA), Reanalisar, Histórico, contexto sem R:R falso, `AvisoLiquidacao` | OK | Reanalisar e Histórico ficam na linha compartilhada fora do ternário (App.jsx:~5018-5022). Stop/alvo (IA) e `AvisoLiquidacao` estão no card. |
| D-09 sem "Compras desta posição" na estruturada | OK | O acordeão fica só no ramo legado. |
| D-10 stop/alvo como marcadores e linhas; nunca vetados | OK | `traco(stop)`/`traco(alvo)`; "definir ▸" e "✎ definir stop e alvo" nunca `disabled`. |
| D-11 chips neutros; pill vermelha só com call vendida | OK | `tipoPillTravada` exige `qtyTravada>0`; variante `badge_travada_collar`. |

## Invariantes do repositório

| Invariante | Status | Evidência |
|------------|--------|-----------|
| Sem cálculo financeiro novo no front além de %capital e R:R | OK | `estruturaCard.js` é puro e só decide exibição. O card faz `pctCap` e `rr`, ambos permitidos. Tudo o mais lê `estrutura`. |
| Paridade `skill_ref.py`↔`copy.js` | OK | `test_estrutura_card_espelho` exit 0; `test_skill_ref.py` e `test_estrutura_card_vocab.py` verdes. |
| Stop/alvo nunca vetado | OK | ver D-10. |
| Manchete só do motor | OK | O card não gera manchete. `nomeTexto`, `estadoTexto`, `faixa.textos`, `encerrar.texto` e `stopTexto` são texto do motor, renderizados como filho de texto JSX. |
| `persistence.js` / `api.js` sem diff | OK | `git diff 8242c016..HEAD --stat` não os lista. |
| Guardiões de teste preservados | OK, com 3 reversões deliberadas e anotadas | Só 3 linhas `-` no diff de testes, todas substituídas por asserção equivalente ou mais estrita com nota "Reversão deliberada Fase 45": `optionsProposta(` 1x→2x (`test_carteira_opcoes_tira`), regex de `goOpcoes` com `opts.abrirTicker` (`test_opcoes_consolidacao_ui`), import com `abrirTickerOpcoes` (`test_opcoes_continuidade_ui`). Nenhuma asserção apagada sem substituta. |
| `server/app` só `skill_ref.py` | DESVIO MENOR | `main.py` mudou 1 linha: bump de `SERVER_BUILD_ID`, o carimbo de entrega previsto no CLAUDE.md. `web/src/version.js` também mudou (`BUILD_ID`). Nenhuma lógica de servidor. |

## Comandos executados

| Comando | Resultado |
|---------|-----------|
| `cd web && npx vite build` | exit 0 |
| node `test_estrutura_card_ui`, `_logica`, `_contraste`, `_espelho`, `test_opcoes_abrir_ticker`, `test_ritmo_sp`, `test_carteira_lastro_ui`, `test_carteira_opcoes_tira`, `test_opcoes_consolidacao_ui`, `test_opcoes_continuidade_ui`, `test_opcoes_collar_ui` | todos exit 0 |
| `server/.venv pytest test_estrutura_card_vocab.py test_opcoes_collar_vocab.py test_skill_ref.py` | 56 passed |

A suíte canônica completa (`scripts/executar.sh --testes`) não foi rodada aqui. Ela é do orquestrador, pela regra 4 do CLAUDE.md.

## Anti-padrões

Nenhum `TBD`, `FIXME` ou `XXX` nas linhas adicionadas em App.jsx, copy.js e estruturaCard.js. Nenhum stub: o estado `null` e a falha renderizam texto real, não valor inventado.

## Limitações conhecidas

- **(a)** O backend da Fase 44 (`estrutura` em `/api/options/proposta`) não está em produção. O front tolera isso: sem `estrutura`, o card cai em "falha" (card atual + aviso), nunca em número inventado.
- **(b)** O destino de "Ver encerramento em Opções…" só propõe recomprar a call, pelo fluxo `/api/options/lastreada/fechar` existente. A put do collar e a put de proteção não têm caminho de fechamento nesse fluxo. O botão promete só navegar, e o card mostra o texto do motor.
- **(c)** Ask × último negócio, investigado no 45-04 e não alterado. O card marca a perna vendida pelo ask, conservador por D-04. A proposta e a execução de fechamento usam `lastPrice`. Em UGPA3 isso deu R$ 0,70 no card contra R$ 0,65 na proposta. Não há rótulo explicando os dois preços de referência. Proposta segura, não implementada: chave nova em `ESTRUTURA_CARD` ↔ `estruturaCard`.
- **(d)** Dívida AA da `TravaPill` legada (AtivoCard e card atual). Razão de contraste, medida sem asserção: light·estudo e light·operador 4,18, abaixo de 4,5. O contorno da pill do card novo mede >= 4,79. P4 foi decidida pelo Alex como "não" (sem follow-up no AtivoCard).
- **(e)** Divergência de escopo em CARD-06: a âncora "trava protetora" segue na manchete `collar` de `OPCOES_LASTREADAS` (skill_ref.py:623/670). É texto regulado (guardrail CVM), fora do card, e foi deixada de propósito com nota em `skill_ref.py`. O card e as chaves visíveis de `copy.js` estão limpos, e o guardião `test_opcoes_collar_ui` assevera isso. Se o Alex quiser a âncora banida também na aba Opções, isso vira decisão de milestone.
- **(f)** O plano 45-05 (checkpoint humano) não tem SUMMARY. As decisões do Alex estão registradas em 45-04-SUMMARY ("Decisões do Alex"). M1 e M7 foram aprovados. O STOP foi deduplicado (159ed8a9). Depois das correções pós-teste local, o card não foi reaberto no navegador.

## Resumo

Nenhuma falha de must-have. Os 4 critérios do ROADMAP, CARD-01..06 e D-01..D-11 têm artefato de código e guardião verde. O `vite build` passa. Os guardiões alterados têm só reversões deliberadas e anotadas. Fica `human_needed` pelos cinco itens listados no frontmatter, que exigem o aparelho ou o backend da Fase 44 em produção.

---

_Verificado: 2026-09-30_
_Verificador: Claude (gsd-verifier)_
