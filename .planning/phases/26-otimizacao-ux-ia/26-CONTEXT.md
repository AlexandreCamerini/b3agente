# 26-CONTEXT — Otimização de UX e da camada de IA do Boris+

Origem: prompt de execução consolidado a partir da análise das cinco abas e da
camada de IA (12/09/2026), com inventário verificado arquivo:linha. O
documento original do Alex está preservado em `26-BRIEFING-ORIGINAL.md` neste
mesmo diretório — este CONTEXT só registra o que mudou depois da conferência
e as decisões tomadas.

## Referências RECONFIRMADAS em 2026-09-12 (à noite, pós Fase 25)

Todos os números de linha do documento original estavam desatualizados — as
Fases 24 e 25 (aba Opções + planos comerciais) acrescentaram ~400 linhas a
`server/app/main.py` e centenas a `web/src/App.jsx`/`copy.js` no mesmo dia.
Os números abaixo são os corretos, medidos por grep antes de qualquer edição:

| Item | Referência do briefing | Referência real (26-09-12 noite) |
|---|---|---|
| A1 | `main.py:3606` (Tela desconhecida) | `main.py:4020` |
| A1 | `App.jsx:9202-9272` (petSnapshot) | `App.jsx:9338` (`const petSnapshot = useMemo(...)`), `switch (petTela)`, casos: carteira/evolucao/radar/agente/historico/perfil + `default: return {}` — **confirma ausência de `case "opcoes"`** |
| A1 | `test_pet_todas_telas.py:44-45` | testes em `:43` (`test_pet_telas_tem_as_7_abas_do_plano`), `:50`, `:56`, `:62`, `:74` |
| A2 | `main.py` linha ~3606/3614 | `kb.resolver` em `main.py:4027`; checagem de tela antes dele |
| A3 | `App.jsx:985`, `copy.js:52/456` | `App.jsx:1015` (`defs` do BottomNav), `copy.js:93` (estudo) e `:538` (operador) |
| A3 | `tituloWatchlist`/`subtituloWatchlist` | `copy.js:85-86` (estudo), `:530-531` (operador) — padrão confirmado a espelhar |
| A4 | `App.jsx:2403-2410` (tourPassos) | `App.jsx:2433` |
| A4 | `App.jsx:2350` (ajudaSecoes) | `App.jsx:2380` |
| A4 | `useState("evolucao")` em `:7867` | `App.jsx:7980` |
| A5 | `App.jsx:1424` (texto) / `:1415-1416` (comentário) | texto em `App.jsx:1454`, comentário "frase MANDATÓRIA do CLAUDE.md, verbatim" em `:1450` — **confirmado que o comentário AFIRMA verbatim e os dois textos DIVERGEM de fato** ("uma explicação agora." × "concluir.") |
| A5 | `skill_ref.py:221,227` | `vocab["operador"]["sem_setup"]`/`vocab["educacional"]["sem_setup"]` em `skill_ref.py:220-227` — confirmado: é uma TERCEIRA frase, para um propósito diferente (ausência de setup, não ausência de dados) — a citação do achado está correta |
| A5 | `CLAUDE.md:74-76` | `CLAUDE.md:75` |
| A6 | `metering.py:252-253,258-259,270-271` | `metering.py:253,258,277` — as três ocorrências de "Perfil → Conta & preferências" confirmadas |
| A6 | tile atual | `App.jsx:2594` — `title="IA & Boris"`, confirma que o caminho antigo não existe mais |
| A7 | SKILL.md:62-64 | conteúdo confirmado verbatim: cita "Coruja" (não existe — `App.jsx:20` importa `Boris` de `./pet/Boris.jsx`) e "só na Watchlist do Estudo" (falso, ver reversão registrada em `App.jsx:9384+`) |

Achados extras da reconferência, não estavam no briefing original:

- **B1 confirmado com precisão**: `defs` do `BottomNav` (`App.jsx:1015-1017`)
  tem exatamente 5 itens (`evolucao`, `radar`, `mercado`, `carteira`,
  `opcoes`) — `perfil` não é um deles, mas `tab === "perfil"` É um valor
  válido de `tab` (setado em `App.jsx:8425`, `:9459`). O Perfil existe como
  destino de navegação sem existir como item da barra — confirma o problema
  exatamente como descrito.
- **B4 confirmado com o código pós-25-04**: `GET /api/ai/quota`
  (`main.py:745-772`) já devolve `quota: {used, quota, remaining, ...}`
  (diário, via `metering.snapshot`) ao lado de `monthUsed`/`monthLimit`.
  `AtividadeIAScreen` (`App.jsx:6009+`) só lê `monthUsed`/`monthLimit`
  (`:6031-6032`) — o `quota` diário chega e não é renderizado. O trabalho da
  Fase 25 (25-04/25-06) tocou esta MESMA rota e NÃO fechou este achado — são
  preocupações diferentes (25-04 fez o número vir do plano; B4 é expor o
  número diário que já existe).

## Decisões do Alex (2026-09-12, à noite)

### B3 — MUDOU DE ESCOPO. Não é mais item de quick-task.

Decisão de direção: **opção 1 do briefing** (ligar a aba às rotas de
execução), mas com uma regra nova que o briefing não previa:

> "só é permitido operações com opções quando você tem lastro de ações que
> te permitam isto. para operar sem ter lastro tem que ligar um flag no
> setor configurações."

Leitura: operar opções (de qualquer estrutura, não só as que
`opcoes_lastreadas.py` já cobre) fica **restrito a posições com lastro por
padrão**; operar **a descoberto** (naked) exige um flag opt-in em
Configurações. Isto toca o sistema de lastro já em produção (Fase 14/17:
venda coberta, put de proteção) e pergunta se ele se estende, ou se nasce um
caminho novo para as estruturas que a aba Opções monta via MCP (que não são
necessariamente cobertas por ação em carteira).

Segunda pergunta do Alex, para INVESTIGAR antes de planejar: **o Operador IA
(agente autônomo, `server/app/agent.py`) hoje analisa opções? Consegue
transacioná-las automaticamente?** — respondida (ver seção
"Pesquisa CONCLUÍDA" abaixo): fechar/liquidar automaticamente já existe;
abrir posição nova automaticamente não existe, é a construir do zero.

**Isto vira uma fase de planejamento própria** (não `/gsd-quick`, não
`/gsd-execute-phase` direto) — precisa de `RESEARCH.md` sobre o sistema de
lastro existente e o alcance real do agente antes de qualquer plano de
execução.

### B2 — NÃO DECIDIDO.

A resposta do Alex à pergunta (montar tudo e esconder com CSS × içar estado
para o App) não chegou como texto elaborado. Nenhuma das duas abordagens foi
escolhida — **fica em backlog, sem implementação**, até uma decisão clara.
Não presumir a opção "recomendada" do briefing original só porque ela era a
sugestão.

## Pesquisa CONCLUÍDA — B3 (Operador IA × opções)

Investigado por agente de leitura em 2026-09-12 (à noite), com citação
arquivo:linha para cada resposta. Isto é FATO levantado do código atual —
não é decisão nem plano de execução, que continuam pendentes de uma fase
própria (ver abaixo).

1. **O agente já itera sobre posições de opção, não só ação.**
   `scheduler_loop` (`agent.py:1182`) → `run_cycle_for` → `_run_cycle_inner`
   (`agent.py:876`) chama `_avaliar_opcoes` (`agent.py:1006-1007`), que lê
   `optionPositions` direto (`agent.py:548`). O briefing original presumia
   que o agente só decidia sobre ações — **falso**, ele já maneja opções
   abertas.
2. **Não existe abertura automática de opção, só fechamento/liquidação.**
   O agente VENDE (fecha) opção por stop/alvo automaticamente
   (`store.sell_option(..., origem="automatico")`, `agent.py:646`) e liquida
   por vencimento (`agent.py:602`, `agent.py:568`) — sempre sobre posição
   JÁ existente. As quatro funções que ABREM posição nova
   (`buy_option`/`abrir_call_coberta`/`comprar_put_protecao`/`abrir_collar`,
   `store.py:774,894,1029,1117`) só são chamadas a partir de rotas HTTP em
   `main.py` (`:3058`, `:3247`, `:3317-3319`, `:3331`, `:3498`), todas atrás
   de `Depends(current_scope)`. Nenhum caminho de cron/webhook abre opção
   sozinho (grep zero em `agent.py` e zero por `webhook`/`callback` em
   `app/*.py`).
3. **`opcoes_motor.py` nunca é chamado por `agent.py`.** Zero referência.
   Só é consumido por `opcoes_lastreadas.py` (proposta sob demanda, disparada
   pela tela).
4. **Dois motores paralelos, por decisão já registrada, não acidente.**
   `docs/adr/027-consumo-do-servico-mcp-autenticado.md` (Decisão 3) já
   declara que a consolidação é um ADR futuro, com gatilho: "10 pregões
   seguidos de paridade viva verde em staging, ou a primeira divergência".
   `test_opcoes_paridade_mcp.py` já testa a paridade (`:69-106`), tem
   contra-guardião (`:131`) e um teste vivo gated por credencial
   (`:158`, não roda em CI comum). `options_mcp_api.py` (`/setups/compilar`
   `:2667`, `/setups/confirmar` `:2825`) grava "setups" via `create_setup` e
   NUNCA toca `optionPositions` nem chama as funções de abertura do
   `store.py` — é caminho de análise/monitoramento, não de execução.

**Implicação para o flag de lastro/naked** (do próprio relatório do
agente): "transacionar opções automaticamente" é **meio existente, meio
novo**. Fechar/liquidar automaticamente já está em produção, restrito à
saída de uma posição que o usuário abriu manualmente. Abrir posição nova
automaticamente — lastreada ou naked — **não tem nenhum precedente de
código hoje**; é funcionalidade de ponta a ponta a construir. A aba Opções
(MCP) hoje só analisa (cria setups de alerta), nunca transaciona.

## Itens NÃO tocados nesta rodada (backlog, registrado, não esquecido)

- **A8 — FECHADO (2026-09-13, commit `839a430`)**: `web/src/api.js:11`
  (`ADDR_HINT`) tinha o MESMO defeito do A6 — corrigido para "Perfil →
  Fonte de dados". O guardião `test_perfil_reorg.mjs` foi ampliado para
  cruzar `api.js` também (não só `metering.py`), e ao rodar ampliado achou
  de graça um SEGUNDO defeito da mesma classe: um comentário citava
  "Perfil → Observabilidade" (tela monolítica extinta desde o qa/45) —
  também corrigido, para "Eficiência da IA".
- **B2**: preservar estado ao trocar de aba — sem decisão de abordagem.
- **B3 execução**: aguarda a pesquisa acima + um plano de fase próprio.
- **C1**: porta de busca para os 83 verbetes da KB — precisa de decisão de
  UX (busca livre × por família × os dois) e é feature nova, não correção.
- **C2**: ancorar verbete nas quatro abas sem cobertura — precisa extrair
  `SetorAlvo`/`ConceitoSheet` de `App.jsx` para módulo compartilhado sem
  violar o isolamento deliberado de `OpcoesScreen.jsx` (`OpcoesScreen.jsx:20-24`
  não importa nada de `App.jsx`).
- **C3 (novo, achado do Alex em 2026-09-12, durante a execução da Fase A)**:
  consolidar o registro de telas do front num ponto único. Hoje existem
  **cinco** listas/switches paralelos que decompõem por tela, sem teste
  amarrando uns aos outros: `BottomNav.defs` (`App.jsx:1015`), `tourPassos`
  (`App.jsx:2433`), `ajudaSecoes` (`App.jsx:2380`), `petSnapshot`
  (`App.jsx:9338`) e a cópia backend `PET_TELAS` (`conceitos.py:555`). Foi
  por isso que "opcoes" apareceu no `BottomNav` mas ficou ausente do
  `petSnapshot`/`PET_TELAS` (achado A1) — o mesmo defeito pode se repetir em
  qualquer tela futura. Proposta do Alex: um registro único de telas no
  front (label, snapshot, passo de tour, seção de ajuda por tela), do qual
  os quatro consumidores JS leem — front↔backend continua sendo par com
  teste de paridade (não há "um" ponto cruzando JS/Python, só dois pontos
  testados, no mesmo padrão de `defaults.py`×`catalog.js`). **Decisão
  registrada (2026-09-12, à noite): não entra nesta rodada** — é refactor de
  App.jsx (~9500 linhas) que toca nav+tour+ajuda+assistente ao mesmo tempo,
  maior que os itens "baratos e independentes" da Fase A; fica como fase
  própria de arquitetura, com plano e verificação de regressão dedicados.
  A1 desta rodada segue como fix pontual (só acrescenta "opcoes" aos
  switches existentes).
- Os três itens explicitamente fora de escopo do briefing original (fundir
  Radar/Watchlist, ampliar o gate mensal de 30 análises, remover rotas
  órfãs, sexta aba) continuam fora — não foram reabertos.

## Guardrails (herdados do briefing, não re-litigar)

Manchete do card só do motor determinístico (guardrail CVM); stop/alvo nunca
vetado; paridade `defaults.py` × `catalog.js` e `deviceStore` ×
`serverStore`; toda elegibilidade/ranking é regra determinística (ADR-017) —
nenhum item aqui aproxima a IA de calcular ou ordenar o Radar; guardiões de
teste não se apagam, só se atualizam com nota; texto idêntico nos dois modos
onde for estado de conta/sistema (não voz de professor/mesa); zero
linguagem de upgrade (ADR-010 §4); não chamar os mutadores de estado do
`gsd-sdk` (decisão do Alex, 2026-09-11 — CLAUDE.md); commit por heredoc com
delimitador entre aspas.
