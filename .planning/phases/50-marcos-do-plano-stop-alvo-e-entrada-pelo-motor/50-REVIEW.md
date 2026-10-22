---
phase: 50-marcos-do-plano-stop-alvo-e-entrada-pelo-motor
reviewed: 2026-10-22T00:00:00Z
depth: standard
files_reviewed: 23
files_reviewed_list:
  - server/app/agent.py
  - server/app/cartao_posicao.py
  - server/app/defaults.py
  - server/app/kpi.py
  - server/app/llm.py
  - server/app/main.py
  - server/app/marcos_servico.py
  - server/app/opcoes_lastreadas.py
  - server/app/opcoes_motor.py
  - server/app/pending_orders.py
  - server/app/setups.py
  - server/app/skill_ref.py
  - server/app/store.py
  - server/app/technical_models.py
  - server/app/technical_snapshot.py
  - server/app/timing.py
  - web/src/App.jsx
  - web/src/api.js
  - web/src/catalog.js
  - web/src/copy.js
  - web/src/estruturaCard.js
  - web/src/finance.js
  - web/src/persistence.js
findings:
  critical: 1
  warning: 6
  info: 6
  total: 13
status: issues_found
---

# Phase 50: Code Review Report

**Reviewed:** 2026-10-22
**Depth:** standard
**Files Reviewed:** 23
**Status:** issues_found

## Summary

O motor puro (`setups.marcos_do_plano`, `validar_marcos`, `revalidar_na_execucao`, `sizing_por_risco`) está coerente com D-01..D-07, e a paridade `setups.py` ↔ `finance.js` é travada por `test_marcos_espelho.mjs` (passa). Princípio 5 preservado: `parse_carteira` descarta número da IA, `kpi.parse_rich` não lê mais `stopSugerido/alvoSugerido`, e as rotas N2/N3/legada sobrescrevem `proposal` com os marcos do motor. Gatilho/invalidação/marcos do cliente são ignorados em `/api/buy` e `pending_orders` (só `meta["setup"]` é lido como nome).

Verificação executada: `test_agent.py`, `test_plano_operacional.py`, `test_entrada_automatica.py` (63 passed); suíte servidor completa: 3722 passed, 22 failed. Os 22 que inspecionei são `PermissionError: Operation not permitted` (rede/sockets bloqueados no sandbox: yahoo, push, texto_vazio, benchmark_ibov), sem relação com a Fase 50; a suíte canônica precisa ser rodada fora do sandbox para confirmar. Node: `test_marcos_espelho`, `test_finance`, `test_api_parity` passam.

Defeito principal: com gestão padrão ligada, o alvo dinâmico (D-15) fica inoperante (CR-01), reproduzido empiricamente.

## Critical Issues

### CR-01: Alvo dinâmico nunca estende com gestão padrão ligada (contradiz D-15)

**File:** `server/app/agent.py:531-550` (`avaliar_alvo_dinamico` / `_rr` l.522-528); ordem no laço em `agent.py:1169-1203`
**Issue:** `avaliar_alvo_dinamico` mede o R:R com `_rr(avg, stop, novo_alvo)` usando o stop ATUAL. A gestão (D-14) roda antes no mesmo tick e, a partir de 1R, leva o stop a `avg` (breakeven) ou acima (trailing). Então `risco = avg - stop <= 0` e `_rr` devolve `None` => `(None, None)` => nunca estende. Como o alvo é no mínimo 1,5R e a gestão arma em 1R, quando o preço chega ao alvo o stop já está em >= avg em todo caso. Reproduzido:
- pos avg 23,50, stop 22,50, alvo 25,50, ATR 0,5, preço 25,60
- stop = 23,50 (breakeven): `avaliar_alvo_dinamico` -> `(None, None)`
- stop = 22,50 (inicial): `-> (26.25, 'extensão 1/2 ... R:R 2.8:1')`

Resultado: o opt-in "Alvo dinâmico" vira letra morta para toda posição aberta pelo motor ou legada com stop (gestão é default ON, `_gestao_ligada`), e a posição fecha no alvo sem aviso de que a extensão foi bloqueada. D-15 diz "medida com o stop já em breakeven/trailing", mas a literal é indefinida (risco zero), então a intenção só pode ser medir contra o risco ORIGINAL. Os testes existentes passam porque usam stop < avg sem gestão.
**Fix:** medir o R:R com o risco inicial (`stopInicial`, fallback ao stop quando ele ainda está abaixo do PM) e manter o piso 1,5 sobre o ganho:
```python
def avaliar_alvo_dinamico(price, pos, ctx=None):
    ...
    base = pos.get("stopInicial")
    if not (isinstance(base, (int, float)) and not isinstance(base, bool)):
        base = stop
    rr = _rr(avg, base, novo_alvo)   # risco original, não o stop já em BE/trailing
```
Para posição legada sem `stopInicial` e com stop >= avg, devolver `(None, None)` continua correto (sem base de risco). Adicionar teste: posição com `gestaoAuto` ligada, stop em BE, preço >= alvo, `alvoDinamico` ON => estende; extensão 3 => fecha. Se o Alex preferir que o R:R seja avaliado "do preço" (`(novo_alvo-price)/(price-stop)`), registrar a escolha no CONTEXT, mas a atual não é uma opção válida.

## Warnings

### WR-01: `marcos_da_posicao` ignora o PM e propõe marcos que o próprio `validar_marcos` recusa (posição no prejuízo)

**File:** `server/app/setups.py:756-785` (`marcos_da_posicao`), `server/app/marcos_servico.py:46-47`, `server/app/main.py:3132-3154` (`/api/marcos`), `web/src/App.jsx:4180-4186`
**Issue:** os marcos da posição são calculados a partir do preço atual sem considerar `avg`. `validar_marcos(..., avg=)` recusa `alvo <= avg`. Posição comprada a 25,00 e hoje a 23,00 com resistência em 24,80 e suporte 22,00: o motor devolve `valido=True, stop=21.95, alvo=24.80, rr=1.71`; `validar_marcos(21.95, 24.80, preco=23, avg=25)` => "Alvo (R$ 24,80) abaixo do preço médio". O modal mostra os números como "CÁLCULO DO MOTOR" e o Aplicar (sempre habilitado, D-17) devolve 400 com a mensagem; o usuário não consegue aplicar a sugestão do motor justamente na posição que mais precisa de stop. O front já envia `avg` em `store.marcos(t, {preco, avg})` (App.jsx:4136), mas `/api/marcos` descarta o campo (só lê `preco`/`setup`), o que indica fiação incompleta.
**Fix:** aceitar `avg` (do servidor: ler a posição do escopo; não confiar no corpo) em `marcos_da_posicao(preco, niveis, avg=None)` e, quando `alvo <= avg`, escolher a próxima resistência acima do PM ou devolver `valido=False` com motivo explícito ("a primeira resistência fica abaixo do seu preço médio"). Assim o motor nunca sugere o que ele mesmo recusa. Cobrir com teste de valores conhecidos (caso acima).

### WR-02: Posição com alvo inválido perde também o stop (venda por stop suprimida)

**File:** `server/app/agent.py:1152-1158` (laço principal), `agent.py:1015-1017` (`_avisar_fora_pregao`); espelho `web/src/persistence.js:2099-2112`
**Issue:** D-13 quer que "marco inválido não dispare venda", mas o gate faz `continue` quando `validar_marcos(stop, alvo, avg)` falha por QUALQUER motivo, pulando também a avaliação do stop (e do trailing/gestão). Cenário: posição legada PM 25,00 / cotação 23,00 / stop 22,00 / alvo 24,00 (usuário definiu saída de recuperação abaixo do PM; hoje recusado por `alvo <= avg`). A posição fica "plano inválido" e, se a cotação cair a 21,90, NADA vende: a proteção de perda foi desligada por causa do alvo. No caso-gatilho (PM 23,01, stop 23,36, alvo 21,58) o stop é válido isoladamente (breakeven+) e também deixa de proteger.
**Fix:** suprimir só o gatilho do marco inválido: se `validar_marcos(stop, None, avg=avg)` for válido, manter a avaliação do stop e neutralizar apenas `hit_alvo`; se o inválido for o stop, suprimir o stop. Mantém o aviso diário. Aplicar a mesma regra em `_avisar_fora_pregao` e no ciclo local do `deviceStore`. Se a decisão do Alex for mesmo suprimir tudo, registrar no CONTEXT/CLAUDE.md que a posição fica sem stop até redefinição e dizer isso no texto de `plano_invalido_diario` (hoje diz só "Nenhuma venda foi feita por esses marcos").

### WR-03: `stopInicial` não é atualizado em edição manual e não existe em posição legada: o "1R" da gestão deriva

**File:** `server/app/store.py:602-640` (`set_position` não toca `stopInicial`), `server/app/agent.py:480-495` (`nivel_gestao`)
**Issue:** `R = avg - (stopInicial or stop)`. (a) Usuário edita o stop pelo `PUT /api/position` de uma posição aberta pelo motor: `stopInicial` fica com o stop antigo, então o breakeven arma em 1R do risco antigo, não do que o usuário assumiu (stop apertado => breakeven só muito acima; stop frouxo => cedo demais). (b) Posição legada sem `stopInicial`: a base passa a ser `pos["stop"]`, que sobe com o trailing global/gestão; R encolhe a cada ajuste e o limiar de 1R se aproxima do preço. (c) `buy` somando lote recalcula `avg` mas mantém o `stopInicial` antigo.
**Fix:** em `set_position`, quando a chamada vier do usuário (rota PUT; não do agente) e `has_stop`, gravar `stopInicial = novo_stop` se `novo_stop < avg`; para legadas, gravar `stopInicial` na primeira vez que a gestão avalia (stop ainda abaixo do PM). Teste: editar stop manualmente muda o limiar de breakeven.

### WR-04: Paridade `deviceStore` ↔ `serverStore` incompleta na compra a partir de setup

**File:** `web/src/persistence.js:1857-1897` (`deviceStore.buy`), `server/app/main.py:2944-2947`
**Issue:** o servidor devolve `marcos`, `marcosMotivo` e `marcosTexto` (frase por modo) e roda `revalidar_na_execucao` (perseguição, R:R mínimo, geometria) antes de gravar. O `deviceStore.buy` sem sessão: (a) só devolve `marcosMotivo` — nunca `marcosTexto`, então o toast de App.jsx:10232 (`s.marcosTexto`) fica mudo no iOS local, sem dizer que a compra nasceu sem marcos (princípio 9/D-06); (b) só roda `validarMarcos`, não `revalidar` (confia no `/api/marcos`, que embute perseguição mas mede R:R da entrada e não do preço executado quando `close < gatilho`); (c) falha de rede em `api.marcos` vira `marcosMotivo = null` sem texto. A regra do CLAUDE.md exige método/campo novo nos DOIS stores.
**Fix:** montar `marcosTexto` no device via `marcosPlanoTxt(modo, "compra_com_marcos"/"compra_sem_marcos", ...)` (já importado) e devolver `marcos`; trocar o `catch` por motivo explícito ("Sem dados técnicos para calcular os marcos agora."); expor `revalidarNaExecucao` espelhado em `finance.js` ou fazer o servidor devolver o `rr` revalidado em `/api/marcos` para o preço informado. Estender `test_api_parity.mjs`/espelho com esses campos.

### WR-05: `PUT /api/position/{ticker}` faz I/O externo antes de validar ticker/posição

**File:** `server/app/main.py:3097-3124`
**Issue:** `ticker.upper()` (sem `_normalize_ticker`, sem checar se existe posição no escopo) segue direto para `candle_provider.get_quote(t)` e, se falhar, `marcos_servico.snapshot_canonico(t)`. `current_scope` aceita escopo anônimo, então qualquer cliente pode disparar buscas de cotação/histórico de tickers arbitrários queimando o orçamento da brapi (15k/mês para o app inteiro) e o Yahoo; `set_position` depois ignora silenciosamente ticker sem posição. Uma regressão em relação ao PUT anterior, que não tinha I/O.
**Fix:** normalizar com `_normalize_ticker`, rejeitar `len(t) < 4` e checar `any(p["t"] == t for p in store.get(_conn, "positions", user_id=scope))` ANTES de buscar preço (404/400 curto). Aplicar também limite de uso no `/api/marcos` se o orçamento brapi for sensível a anônimos (hoje igual a `/api/technicals`, mas sem cota).

### WR-06: Preço de referência do PUT cai para o último fechamento do snapshot e é tratado como "cotação atual"

**File:** `server/app/main.py:3108-3117`
**Issue:** se `get_quote` falha, a validação usa `snap["close"]` (fechamento diário, possivelmente do dia anterior ou de dados atrasados) e as mensagens dizem "cotação atual". Princípio 4: dado atrasado deve ser dito, não validar silenciosamente como preço corrente. Stop gravado válido contra o fechamento pode já estar acima da cotação real (disparando venda no próximo ciclo) e um alvo legítimo pode ser recusado. Além disso o stop de uma posição só edita o alvo e é recusado se o stop existente já ≥ preço (a validação reavalia o stop não editado contra o preço).
**Fix:** validar contra o fechamento apenas a estrutura (preco_ref=None) e avisar na resposta `precoRefOrigem: "fechamento"`; ou recusar com `MOTIVO_SEM_PRECO_VALIDAR` quando `get_quote` falhar (consistente com o `deviceStore`, que recusa sem cotação). Em edição de um só campo, validar contra o preço apenas o campo enviado.

## Info

### IN-01: Textos fixos fora do vocabulário por modo (App.jsx)

**File:** `web/src/App.jsx:5574` ("Redefinir"), `4228` ("CALCULANDO…", "PARECER: AGUARDAR", "CÁLCULO DO MOTOR"), `4219` ("Explicação com IA", steps), `4206` e `4209` (mensagens de recusa), `4266` ("A decisão é sua — isto não é recomendação de investimento."), `1591-1592` (rótulos "STOP"/"ENTRADA" da régua)
**Issue:** o resto da fase usa `marcosPlanoTxt`/`cartaoPosicaoTxt` com paridade `skill_ref` ↔ `copy.js` e guardião `test_vocabulario_espelho.mjs`; estes literais escapam do espelho e da regra "front nunca compõe vocabulário" (skill didatica-boris).
**Fix:** criar chaves em `MARCOS_PLANO` (`modal_calculando`, `modal_calculo_motor`, `modal_parecer_aguardar`, `acao_redefinir`, `modal_marcos_calculando`, `modal_ia_gauge`) nos dois modos, espelhar em `copy.js` e travar no teste de espelho.

### IN-02: `/api/marcos` ignora `avg` enviado pelo front; comentário obsoleto em main.py

**File:** `web/src/App.jsx:4136` (envia `avg`), `server/app/main.py:3132-3154` (não lê), `server/app/main.py:2548-2562` (comentário diz que stop/alvo do N2 "vêm da proposal da LLM")
**Issue:** parâmetro morto no cliente (relacionado a WR-01) e comentário que descreve comportamento removido, o que induz leitura errada da série `analysis_outcomes` (N2 agora grava `stop=None, alvo=None`).
**Fix:** remover `avg` do cliente ou usá-lo no servidor lendo a posição (WR-01); atualizar o comentário para refletir que o N2 não grava mais stop/alvo.

### IN-03: Mensagem bruta do Python em stop/alvo não numérico

**File:** `server/app/store.py:608-612`
**Issue:** `float(stop)` com string não numérica levanta `ValueError("could not convert string to float: 'abc'")`, que a rota converte em 400 em inglês (e `stop=True` vira 1.0). Domínio de erro deve ser PT-BR (CLAUDE.md, Error Handling).
**Fix:** validar `isinstance(v, (int, float)) and not isinstance(v, bool)` (ou `float()` num try) e levantar `ValueError("Stop e alvo precisam ser valores positivos.")`.

### IN-04: Aviso de stop não ajustado repete a cada ciclo

**File:** `server/app/agent.py:1186-1189`
**Issue:** quando `set_position` recusa o stop novo (ex.: trailing >= alvo com preço acima do alvo e alvo dinâmico ligado), cada ciclo de 5 min acrescenta um `warn` no Diário sem dedupe.
**Fix:** usar `_aviso_diario(conn, scope, "avisoStopNaoAjustado", "stop:" + t, t, texto)`.

### IN-05: Rótulos de gestão aparecem em plano de VENDA legado; `modoTxt` de entrada automática fixo

**File:** `web/src/App.jsx:1557-1563` (`PlanoOperacionalBloco`), `server/app/agent.py:806` (`modo_txt = "operador"`)
**Issue:** `bloco_breakeven` ("o stop vai para a entrada") e `bloco_stop` ("com folga de ATR") são exibidos também quando `plano.decisao === "VENDER"` (caminho legado, sem folga e sem gestão, short fora do escopo). No agente, o texto da entrada automática ignora `app_mode` (parâmetro disponível).
**Fix:** esconder a linha de breakeven e usar o rótulo antigo quando `decisao !== "COMPRAR"`; derivar `modo_txt` de `app_mode`.

### IN-06: Decisões de produto a registrar

**File:** `server/app/agent.py:1137-1152`, `server/app/agent.py:817-823`, `server/app/setups.py:703-705`
**Issue:** (a) gestão default ON altera o stop de posições legadas com stop sem consentimento (consequência literal de D-14, mas muda o stop do usuário sem aviso prévio; o Diário informa a posteriori); (b) `capital` do sizing é `risco.capital`/`initialBudget`, não o patrimônio atual (D-07 fala em "% do patrimônio"); espelhado no front, mas vale registrar; (c) o ciclo local do iPhone sem conta não implementa gestão/entrada (D-14 só no servidor), coerente com "login obrigatório", mas o toggle de gestão aparece no modal do `deviceStore` sem efeito local.
**Fix:** nota no CONTEXT/ADR e, para (c), esconder o toggle quando não há sessão.

## Resolução

Aplicada em 2026-10-22 (`gsd-code-fixer`), um commit por achado em `main`.

| ID | Status | Commit |
|----|--------|--------|
| CR-01 | corrigido: R:R do alvo dinâmico medido contra `stopInicial` (fallback: stop atual só se < PM) | 37966647 |
| WR-02 | corrigido: stop e alvo avaliados separadamente (`agent.marcos_efetivos`, espelho `finance.marcosEfetivos`); alvo inválido nunca dispara, stop válido segue vendendo; gestão/trailing só ajustam com o par íntegro; texto de `plano_invalido_diario` atualizado nos dois modos; guardião de `test_marcos_stores.mjs` revertido com nota | 5a0c387b |
| WR-01 | corrigido: `marcos_da_posicao(..., avg=)`; `/api/marcos` e as 3 rotas de IA leem o PM da posição no servidor (corpo ignorado); sem nível acima do PM, inválido com motivo | 1cd95b19 |
| IN-03 | corrigido: `store._marco_num` -> 400 PT-BR | b682a85b |
| WR-03 | corrigido: `set_position(manual=True)` reancora `stopInicial` (removido se stop >= PM/limpo); legado ganha âncora na 1a avaliação da gestão; espelho no `deviceStore.putPosition`. Item (c) do achado (lote somado no `buy` mantém `stopInicial`) NÃO tratado: fora da regra pedida | ba437116 |
| WR-05, WR-06 | corrigidos no mesmo commit (mesmo trecho da rota): ticker normalizado + 404 sem posição antes de I/O; só o marco editado é conferido contra o preço; fechamento do snapshot rotulado "último fechamento (em DD/MM/AAAA, ...)"; espelho no `deviceStore.putPosition`. Testes de `test_ciclo_imediato_apos_carteira.py` e `test_adr013_rbac.py` passaram a semear a posição (nota WR-05) | 2646b8a0 |
| IN-04 | corrigido: `_aviso_diario("avisoStopNaoAjustado")` | 6d686f98 |
| WR-04 | corrigido: `finance.revalidarNaExecucao` (espelho, fixture `revalidacao`), `deviceStore.buy` devolve `marcos`/`marcosMotivo`/`marcosTexto`, motivo explícito na falha de rede | 584fce3d |
| IN-02 | corrigido: comentário obsoleto do N2 (o `avg` morto do cliente passou a ser ignorado de propósito: o servidor lê o PM) | e50e61bb |
| IN-01, IN-05, IN-06 | não tratados (fora do escopo pedido) | - |

---

_Reviewed: 2026-10-22_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
