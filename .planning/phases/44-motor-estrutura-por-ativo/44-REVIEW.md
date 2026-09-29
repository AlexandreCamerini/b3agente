---
phase: 44-motor-estrutura-por-ativo
reviewed: 2026-09-29T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - server/app/estrutura_posicao.py
  - server/app/opcoes_lastreadas.py
  - server/app/skill_ref.py
  - web/src/copy.js
  - server/app/main.py
  - server/tests/test_estrutura_posicao.py
  - server/tests/test_estrutura_posicao_rota.py
  - web/tests/test_estrutura_espelho.mjs
findings:
  critical: 0
  warning: 6
  info: 4
  total: 10
status: issues_found
---

# Phase 44: Code Review Report

**Depth:** standard. Testes lidos apenas como contexto; nenhum arquivo-fonte alterado; testes nao executados.

## Summary

Motor puro bem isolado (sem rede/relogio), rota com try/except proprio, chave aditiva, paridade skill_ref<->copy.js coerente no diff, `None` em vez de 0 na maior parte. Os defeitos reais estao em texto que afirma protecao/limite que os numeros nao sustentam (guardrail de honestidade), nao em crash. Nenhum BLOCKER provado.

## Warnings

### WR-01 [CORRIGIDO]: Texto de piso/stop afirma protecao da quantidade-base inteira mesmo com put menor

**File:** `server/app/estrutura_posicao.py:158-182, 367-368`
**Issue:** `base = min(s, max(q_call, q_put))`. Em collar com call cobrindo mais que a put (ex.: 300 ações, call 300, put 100), `base=300` e `faixa_piso` diz "a put protege as 300 ações" (`qtd=base`), enquanto a put cobre 100. `stopTexto` ("limita a perda desta posição") também é emitido sempre que `piso` existe, sem checar cobertura. É afirmação de proteção falsa (princípios 5/6 de CLAUDE.md).
**Fix:** calcular `q_put_efetiva = min(q_put, base)`; usar essa quantidade em `faixa_piso`; emitir `stopTexto` só se `q_put >= s` (ou texto próprio de proteção parcial, com "Não há dados suficientes" se preciso).

### WR-02 [CORRIGIDO]: `faixa_sem_teto` emitido quando existe call vendida mas `ganho_maximo` é None

**File:** `server/app/estrutura_posicao.py:185-189`
**Issue:** O `else` cobre dois casos: sem call (correto) e `teto is not None and ganho is None` (call cobre menos que a base; ganho ilimitado no trecho descoberto). No 2º caso, educacional diz "a put de proteção não limita o ganho" - texto errado para um collar/call parcial e omite a call que existe. Análogo em `perda is None` com piso: nenhum texto de piso é emitido, silenciosamente.
**Fix:** ramificar `teto is None` (sem_teto) vs `ganho is None` (nova chave "teto parcial/ganho não limitado no trecho sem call", nos dois modos + espelho); emitir texto quando `piso` existe e `perda is None`.

### WR-03: `descoberta` (put excedente) perdida nos retornos antecipados

**File:** `server/app/estrutura_posicao.py:148-157`
**Issue:** `descoberta = q_put > s` só é calculada depois dos returns de `vencimentos_diferentes` e `dados_insuficientes` (o 1º devolve `False, None`; o 2º também). Put excedente sem ações correspondentes some do payload nesses casos, contradição com D-09 ("put excedente → descoberta"). O caminho `ValueError` já devolve descoberta, então o contrato é inconsistente.
**Fix:** calcular `descoberta`/`desc_txt` logo após o teste `q_call > s` e devolvê-los em todos os retornos seguintes.

### WR-04 [CORRIGIDO]: `side` desconhecido vira "compra" silenciosamente

**File:** `server/app/estrutura_posicao.py:70`
**Issue:** `"venda" if op.get("side") == "vendida" else "compra"`. Qualquer valor inesperado ("short", "Vendida", "sell") vira perna comprada: call vendida lida como call comprada muda nome (`None`), resultado (sinal invertido em `_resultado_perna`) e marcação (bid em vez de ask). Sem sinal de erro.
**Fix:** normalizar (`str(...).strip().lower()`); para valor não vazio e fora de {"vendida","comprada"}, marcar `lado=None`, resultado None e `incompleto` True (nunca adivinhar sinal).

### WR-05 [CORRIGIDO]: Motivo de "incompleto" atribuído sempre a falta de cotação

**File:** `server/app/estrutura_posicao.py:105-110, 281-292`
**Issue:** `resultado` da perna é None também quando `premioEntrada` (`avg`) ou `quantidade` é inválido; `resultado_incompleto` diz "falta cotação de X" mesmo com cotação presente. Além disso `pernasSemCotacao` mistura os dois motivos, e `estado` só vira `premio_indisponivel` pela cotação: estados divergem.
**Fix:** separar `sem_cotacao` (premioAtual None) de `sem_entrada` (entrada/qtd inválida) com frase própria, ou renomear o campo e texto para "sem dados".

### WR-06 [CORRIGIDO]: Comparação de vencimento por string crua

**File:** `server/app/estrutura_posicao.py:148-153`
**Issue:** `divergem` compara `p["vencimento"]` cru; "2026-10-16" e "2026-10-16T00:00:00" contam como vencimentos diferentes e derrubam a faixa (falso "vencimentos diferentes"). O payoff já tem a mesma regra (dado opaco), mas aqui a normalização `_data` já existe. Também: `estado` usa o menor vencimento, então uma perna vencida marca a estrutura inteira como `vencida` e bloqueia `encerrar` de pernas ainda vigentes (`estrutura_posicao.py:332`).
**Fix:** comparar `_data(v) or v`; para perna vencida com outras vigentes, permitir encerrar as vigentes ou documentar/testar a decisão.

## Info

### IN-01: Duplicação da lógica de bloqueio de encerramento
**File:** `server/app/estrutura_posicao.py:196-205, 331-343`
`_encerrar_perna` e o bloco de `enc` repetem as mesmas regras (vencida / sem prêmio / sem `lastPrice`). Extrair um helper evita divergência futura.

### IN-02: "Vence em 0 dia(s)"
**File:** `server/app/estrutura_posicao.py:237-238`
`dias == 0` gera "0 dia(s)". Frase dedicada "vence hoje" em ambos os modos (e espelho).

### IN-03: `_liquidez` colapsa volume 0 em None
**File:** `server/app/estrutura_posicao.py:129-131`
`_num` devolve None para 0; `liquidity_score` recebe None em vez de 0 para volume/OI/bid/ask zerados. Confirmar que score é idêntico para 0 e None em `options_quant.liquidity_score`, senão `sem_mercado` pode ser sub ou super-disparado.

### IN-04: Chamadas de cadeia sequenciais e por vencimento na rota
**File:** `server/app/main.py:3253-3266`
Uma `get_options` por vencimento, em série, além da cadeia já buscada para a proposta, sem timeout próprio (o try/except só captura erro). Fora do escopo de performance, mas uma cadeia lenta atrasa a rota inteira; considerar `asyncio.wait_for` + reuso de `chain_pos` quando o vencimento coincide.

---

_Reviewed: 2026-09-29_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
