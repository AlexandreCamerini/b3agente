---
phase: 14-opcoes-lastreadas
plan: 03
subsystem: api
tags: [options, portfolio-engine, deterministic-engine, fastapi, pytest, covered-call, protective-put, cvm-guardrail]

# Dependency graph
requires:
  - phase: 14-02
    provides: "store.abrir_call_coberta/fechar_call_coberta/comprar_put_protecao (motor de carteira) + formato side/lastro de optionPositions"
provides:
  - "opcoes_lastreadas.propor — motor puro que escolhe UM contrato (venda coberta ou put de proteção) a partir da leitura técnica do ativo-lastro e do lastro livre, ou devolve a ausência com motivo nomeado"
  - "opcoes_lastreadas.put_sem_lastro — estado derivado (put cuja posição de ações foi vendida), nunca persistido"
  - "skill_ref.OPCOES_LASTREADAS / opcoes_lastreadas_txt — fonte única da manchete da proposta por modo (guardrail CVM)"
  - "skill_ref.num_br — formatação pt-BR sem locale do sistema"
  - "GET /api/options/proposta/{ticker}, POST /api/options/lastreada/abrir, POST /api/options/lastreada/fechar"
affects: [14-04, 14-05, 14-06, 14-07, 14-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Motor puro (sem I/O, sem LLM, sem relógio interno — hoje entra por argumento) devolvendo sempre {proposta, motivo}; sucesso e ausência compartilham o MESMO formato de retorno, motivo sempre uma chave de vocabulário válida"
    - "Rota best-effort (ADR-004): qualquer exceção do provedor de cadeia OU do pipeline técnico vira providerStatus=degraded/motivo=degradado, nunca 500 — mas as portas 'degradado'/'sem_lastro' são checadas na ROTA antes do fetch técnico caro, para não pagar candles+indicators+setups quando a ausência já é conhecida só pela cadeia/posição"
    - "Trava de Modo Estudo na ESCRITA vive no SERVIDOR (403 explícito), não só na UI — mesmo princípio D-5 já usado em set_agent, mas agora com HTTPException direta em vez de fallback silencioso"

key-files:
  created:
    - server/app/opcoes_lastreadas.py
    - server/tests/test_opcoes_lastreadas_proposta.py
    - server/tests/test_opcoes_lastreadas_rotas.py
  modified:
    - server/app/skill_ref.py
    - server/app/main.py

key-decisions:
  - "Vocabulário: 3 motivos de ausência do motor (sem_contrato_liquido, sem_vencimento_elegivel, tendencia_de_alta) compartilham a MESMA frase de sem_setup via alias na função opcoes_lastreadas_txt, em vez de 3 entradas de texto idênticas no dict — uma fonte de texto, várias chaves de motivo apontando pra ela"
  - "motivo de SUCESSO em propor() é o próprio tipo (call_coberta/put_protecao) — também uma chave de vocabulário válida, então o chamador nunca precisa de um branch separado para saber que motivo interpretar quando proposta != None"
  - "Rota GET /api/options/proposta re-checa providerStatus/qty_livre ANTES do fetch técnico (candle_provider→indicators→setups), duplicando as duas primeiras portas de propor() — otimização deliberada para não pagar o pipeline técnico caro quando a ausência já é decidível só pela cadeia/posição (T-14-13)"
  - "Testes de rota usam e-mail único por chamada (uuid) em vez de e-mail fixo — o _conn do processo persiste no B3_DB_PATH do worktree entre execuções locais da suíte; e-mail fixo colidia com 'já existe conta' na segunda rodada"
  - "Teste da proposta completa pina o calendário do provider mock (_proximas_terceiras_sextas) e substitui technical_snapshot.get por um snapshot sintético — sem isso o teste dependeria do dia real em que a suíte roda (a terceira-sexta mais próxima da mock fica <15 dias de distância por ~2 semanas a cada ciclo mensal) e bateria rede de verdade"

requirements-completed: []

# Metrics
duration: ~50min
completed: 2026-08-31
---

# Phase 14 Plan 03: Motor de proposta, vocabulário canônico e rotas HTTP das operações lastreadas Summary

**Motor puro `opcoes_lastreadas.propor` escolhe venda coberta OU put de proteção a partir da leitura técnica do ativo-lastro (nunca inventa proposta), manchete nasce só em `skill_ref.opcoes_lastreadas_txt` por modo, e três rotas HTTP (`proposta`/`abrir`/`fechar`) expõem isso com a trava de Modo Estudo no servidor.**

## Performance

- **Duration:** ~50 min
- **Completed:** 2026-08-31T10:01:00Z
- **Tasks:** 3/3
- **Files modified:** 5 (3 criados: `opcoes_lastreadas.py` + 2 arquivos de teste; 2 modificados: `skill_ref.py`, `main.py`)

## Accomplishments
- `skill_ref.OPCOES_LASTREADAS`/`opcoes_lastreadas_txt`: fonte única da frase de venda coberta/put de proteção, Operador fala como mesa (verbo de ordem) × Estudo descreve condição ("Se você tivesse..."), mesmo padrão de `TIMING`/`HISTORICO`. `num_br()` formata pt-BR sem depender de locale do sistema (Railway não tem pt_BR instalado).
- `opcoes_lastreadas.propor(underlying, chain, spot, plano, posicao, cash, modo, hoje)`: motor determinístico puro que lê a decisão do plano técnico do ativo-lastro (VENDER/baixa → put de proteção; AGUARDAR/NÃO OPERAR/neutro → call coberta; COMPRAR/alta → sem_setup) e escolhe UM contrato líquido (score ≥40) dentro do vencimento elegível (15–60 dias), ou devolve a ausência com motivo nomeado (degradado/sem_lastro/sem_setup/sem_vencimento_elegivel/sem_contrato_liquido/caixa_insuficiente) — nunca fabrica proposta.
- `opcoes_lastreadas.put_sem_lastro()`: estado DERIVADO (put cuja posição de ações caiu abaixo do lastro registrado na abertura) calculado na leitura, nunca persistido, nunca fecha a put sozinho.
- `GET /api/options/proposta/{ticker}`: postura best-effort ADR-004 — cadeia degradada ou falha do pipeline técnico nunca derruba a rota (sempre 200, nunca 500); as portas de ausência mais baratas (providerStatus, lastro) são checadas antes do fetch técnico caro.
- `POST /api/options/lastreada/abrir` e `/fechar`: trava de Modo Estudo explícita no SERVIDOR (403 "Modo Estudo não executa ordens..."), bloqueio 502 por cadeia degradada, `ValueError` do motor vira 400 — rotas próprias, sem tocar `/api/options/buy|sell` (modelo antigo).
- Suíte canônica completa verde: `1797 passed, 1 skipped` (pytest) + `107/107` `web/tests/*.mjs` `[OK]` (backend-only nesta plano, rodado por disciplina do CLAUDE.md mesmo assim).

## Task Commits

Each task was committed atomically:

1. **Task 1: Vocabulário canônico das operações lastreadas por modo** - `30ffb96` (feat)
2. **Task 2: Motor puro de proposta (opcoes_lastreadas.propor)** - `6f56906` (feat)
3. **Task 3: Rotas HTTP — proposta, abrir e fechar operação lastreada** - `f526504` (feat)

_Note: nenhuma task era TDD — plano `autonomous: true`, sem checkpoints._

## Files Created/Modified
- `server/app/skill_ref.py` - bloco `OPCOES_LASTREADAS` + `opcoes_lastreadas_txt` + `num_br` (fonte única da manchete/didática da proposta lastreada)
- `server/app/opcoes_lastreadas.py` - motor puro `propor`/`put_sem_lastro` (174 linhas, sem I/O/LLM/relógio interno)
- `server/app/main.py` - 3 rotas novas (`GET /api/options/proposta/{ticker}`, `POST /api/options/lastreada/abrir`, `POST /api/options/lastreada/fechar`), imports de `opcoes_lastreadas`/`skill_ref`/`_spot_from_chain_or_quote`
- `server/tests/test_opcoes_lastreadas_proposta.py` - guardião do vocabulário (7 testes) + do motor puro (11 testes, cadeia sintética própria, sem rede/relógio)
- `server/tests/test_opcoes_lastreadas_rotas.py` - guardião das 3 rotas via `TestClient` (8 testes, `B3_OPTIONS_PROVIDER=mock`, calendário/técnico fixados para determinismo)

## Decisions Made
- Aliases de vocabulário: `sem_contrato_liquido`/`sem_vencimento_elegivel`/`tendencia_de_alta` (3 motivos distintos do motor) mapeiam para a MESMA frase de `sem_setup` dentro de `opcoes_lastreadas_txt` — uma fonte de texto, não três entradas idênticas no dicionário.
- `motivo` de sucesso em `propor()` é o próprio `tipo` (`call_coberta`/`put_protecao`) — evita um branch separado no chamador só para descobrir que texto interpretar quando há proposta.
- Rota de proposta re-checa `providerStatus`/`qty_livre` ANTES do fetch técnico (candle→indicators→setups) — otimização que evita pagar o pipeline caro quando a ausência já é decidível pela cadeia/posição sozinhas (reforça T-14-13, nenhuma chamada nova além da que o gate já faz).
- Testes de rota usam e-mail único por chamada (`uuid`) — o `_conn` do processo persiste no `B3_DB_PATH` do worktree entre rodadas locais da suíte; um e-mail fixo colidiria com "já existe conta" numa segunda execução manual.
- Teste da proposta completa pina o calendário do provider mock (`_proximas_terceiras_sextas`) e substitui `technical_snapshot.get` por um snapshot sintético (`setups=[]`, `close=38.0`) — sem isso o teste dependeria do dia real em que a suíte roda (a expiração mais próxima do mock fica <15 dias de distância por ~2 semanas a cada ciclo mensal, o que faria o teste falhar de forma intermitente) e bateria rede de verdade dentro de um teste unitário.

## Deviations from Plan

None nas regras de negócio — as três tasks foram implementadas exatamente como especificado (chaves de vocabulário, ordem de avaliação do motor, contrato das três rotas, mensagens de erro). Dois ajustes técnicos dentro do escopo da Task 3, sem mudar comportamento de produção:

**1. [Rule 1 - Bug] Rota de proposta reordenada para checar ausência ANTES do fetch técnico**
- **Found during:** Task 3, ao desenhar os testes da rota `GET /api/options/proposta`
- **Issue:** A ordem literal do texto do plano ("busca a cadeia, o spot, o plano técnico, a posição, o caixa") faria a rota sempre buscar candles+indicators+setups mesmo quando a posição já não existe (motivo `sem_lastro` de qualquer forma) — desperdício de I/O e, em ambiente de teste sem rede, mascarava o motivo real atrás de `degradado`.
- **Fix:** As duas primeiras portas de `opcoes_lastreadas.propor` (`providerStatus`/`qty_livre`) são checadas na ROTA antes do fetch técnico; o resultado final é idêntico ao que `propor()` já devolveria, só evita trabalho.
- **Files modified:** server/app/main.py
- **Verification:** `test_proposta_sem_posicao_devolve_sem_lastro_com_motivo_texto` passa sem monkeypatch de rede/calendário.
- **Committed in:** f526504 (Task 3 commit)

**2. [Rule 3 - Blocking] `.venv` do worktree ausente (mesmo padrão já documentado em 14-01/14-02)**
- **Found during:** início da execução, ao rodar os testes de cada task
- **Issue:** `server/.venv` não existe neste worktree (só no clone principal) — `pytest` direto falhava com `ModuleNotFoundError`.
- **Fix:** symlink temporário `server/.venv → <clone principal>/server/.venv` durante a execução de cada task, removido antes de cada commit (não aparece em nenhum `git status`/commit). `scripts/test.sh` (usado na validação final via `executar.sh --testes`) já resolve isso sozinho nativamente (lê o `git-common-dir` do worktree) — o symlink foi só para os `pytest` incrementais entre tasks.
- **Files modified:** nenhum arquivo versionado (symlink não commitado)
- **Committed in:** n/a (não versionado)

---

**Total deviations:** 2 (1 otimização de rota sem mudança de contrato, 1 ambiente de execução)
**Impact on plan:** Nenhum impacto no comportamento especificado — a reordenação da rota produz o MESMO resultado final que o texto do plano descreve, só evita I/O supérfluo; o symlink é puramente operacional.

## Issues Encountered
- Provider mock (`options_provider_mock.py`, Plano 01) escolhe a terceira-sexta-feira MAIS PRÓXIMA de "hoje" real como vencimento — isso torna qualquer teste que dependa de uma proposta completa (contrato elegível, 15–60 dias) potencialmente flaky dependendo do dia em que a suíte roda (a janela "muito perto do vencimento" ocorre ~2 semanas a cada ciclo mensal). Resolvido fixando o calendário do mock no teste (`_expiracao_fixa`), não no código de produção — o motor `propor()` continua respeitando o vencimento real da cadeia que vier.
- Ambiente de execução sem acesso à rede (sandbox) tornaria qualquer teste de rota que dependesse de `candle_provider.get_history`/`technical_snapshot.get` reais não-determinístico ou lento — resolvido com `_snapshot_sem_setup` (monkeypatch determinístico), sem tocar produção.

## User Setup Required

None - nenhuma configuração de serviço externo necessária. As rotas dependem só do provider de opções já configurado via `B3_OPTIONS_PROVIDER` (dormente em produção, per 14-CONTEXT.md — segue Yahoo até a virada do mydata acontecer).

## Next Phase Readiness
- `GET /api/options/proposta/{ticker}` está pronta para o front (plano 14-04/14-05) renderizar a proposta + `motivoTexto` + `putSemLastro` no card do ativo.
- `POST /api/options/lastreada/abrir|fechar` estão prontas para o front acionar a partir do botão de proposta — o contrato de erro (403/502/404/400) já cobre os quatro estados que a UI precisa distinguir.
- Nenhum bloqueio conhecido para os próximos planos da fase.

---
*Phase: 14-opcoes-lastreadas*
*Completed: 2026-08-31*

## Self-Check: PASSED

- FOUND: server/app/opcoes_lastreadas.py
- FOUND: server/tests/test_opcoes_lastreadas_proposta.py
- FOUND: server/tests/test_opcoes_lastreadas_rotas.py
- FOUND: .planning/phases/14-op-es-lastreadas-venda-coberta-e-put-de-prote-o-sobre-posi-e/14-03-SUMMARY.md
- FOUND commit 30ffb96 (Task 1)
- FOUND commit 6f56906 (Task 2)
- FOUND commit f526504 (Task 3)
