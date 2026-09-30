# Phase 44: Motor — estrutura por ativo - Pattern Map

**Mapped:** 2026-09-29
**Files analyzed:** 6 files (1 new, 5 modified)
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `server/app/estrutura_posicao.py` | service | transform | `server/app/opcoes_payoff.py` | exact |
| `server/app/main.py` (rota integr.) | controller | request-response | `server/app/main.py:3156` (`options_proposta`) | exact |
| `server/app/skill_ref.py` (frases) | utility/config | data-lookup | `server/app/skill_ref.py:1-150` (OPCOES_LASTREADAS) | exact |
| `web/src/copy.js` (espelho) | utility | data-lookup, paridade | `web/src/copy.js:18-150` (COPY dict) | exact |
| `server/app/opcoes_lastreadas.py` (fechar) | service | request-response | `server/app/opcoes_lastreadas.py:405` (`proposta_fechar`) | exact |
| `server/tests/test_estrutura_posicao.py` | test | test | `server/tests/test_opcoes_payoff.py` | exact |
| `web/tests/test_estrutura_*.mjs` | test | test | `web/tests/test_opcoes_*.mjs` | exact |

---

## Pattern Assignments

### `server/app/estrutura_posicao.py` (service, transform)

**Analog:** `server/app/opcoes_payoff.py`

**Module docstring pattern** (lines 1-26):
```python
"""Motor puro de leitura de estrutura por ativo (Fase 44, Plano XX).

Módulo PURO — sem rede, sem banco, sem LLM, sem leitura de relógio, mesma
disciplina de `opcoes_payoff.py`/`opcoes_lastreadas.py`/`setups.py`.

A função ÚNICA calcula estrutura (nome, resultado, faixa, estado, motivos)
reutilizando `opcoes_payoff.perfil_da_estrutura` — sem reimplementação de
payoff. Entrada: opções abertas + preço do objeto. Saída: estrutura
classificada com pernas visíveis e motivos de descarte (sem contrato líquido,
vencimentos divergentes, quantidade descoberta, etc.).
"""
```

**Imports pattern** (reuse `opcoes_payoff`, `skill_ref`):
```python
from __future__ import annotations

from typing import Any, Sequence

from . import opcoes_motor, opcoes_payoff, skill_ref
```

**Core pattern — pure transform function** (single responsibility):
```python
def estrutura_da_posicao(option_positions: list[dict[str, Any]], 
                         underlying: str, 
                         posicao: dict[str, Any],
                         spot: float) -> dict[str, Any]:
    """Classifica estrutura de múltiplas pernas abertas por underlying.
    
    - Entrada: lista completa de `optionPositions` do escopo, não só a 1ª.
    - Saída: dict com `nome`, `resultado_total`, `faixa`, `piso`/`teto`,
      `estado`, `motivo` (se houver), `pernas` (sempre visíveis), `incompleto`.
    - Vencimentos divergentes → `faixa=None`, `motivo="vencimentos diferentes"`.
    - Quantidade descoberta → flag `descoberta=True`, `faixa` calculada só na
      parte coberta.
    - Perna sem cotação → `resultado_total=None`, `incompleto=True`, expõe
      P&L de ações + prêmio das pernas cotadas separadas (nunca soma parcial
      apresentada como total).
    """
```

**Validation & error pattern** (guardrail: null explícito, motivo sempre):
```python
# Segue `opcoes_payoff` linhas 44-52: rejeitar bool, recusar valores
# inválidos com mensagem clara. Nunca 0.0 no lugar de "desconhecido".
def _numero(valor: Any) -> float | None:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return None
    return float(valor)
```

**Return shape pattern** (never hide incomplete calculations):
```python
{
    "nome": str | None,  # ex: "call coberta", "collar", "put proteção"
    "resultado_total": float | None,  # PnL da estrutura completa, ou None se incompleto
    "incompleto": bool,  # True se alguma perna não tem cotação
    "pernasAusentes": [{"tipo": str, "strike": float}],  # só se incompleto
    "faixa": {"piso": float, "teto": float} | None,  # None se descoberta/divergente
    "piso": float | None,  # Estudo: texto completo; Operador: número direto
    "teto": float | None,
    "estado": str,  # "vigente", "exercicio_provavel", "vencida", etc.
    "motivo": str | None,  # "vencimentos_diferentes", "descoberta", None se OK
    "pernas": [{"tipo": str, "lado": str, "strike": float, ...}],  # sempre visível
    "descoberta": bool,
}
```

---

### `server/app/main.py` (rota integração, request-response)

**Analog:** `server/app/main.py` líneas 3156-3254 (`options_proposta`)

**Integration pattern** (chave ADITIVA, `.get()` com default):
```python
# D-01, D-02, D-03: rota existente `GET /api/options/proposta/{ticker}`
# ganha chave ADITIVA `estrutura` — não nova rota.
# NÃO quebra clientes antigos (`.get()` com default).

async def options_proposta(ticker: str, multiperna: bool = False, ...):
    # ... existing logic para `proposta` e `motivo` ...
    
    # NOVA lógica: após montar `resultado` com proposta/motivo,
    # chamar estrutura_posicao.estrutura_da_posicao(**args) se houver
    # opções abertas no underlying.
    
    estrutura_aberta = None
    option_positions = store.get(_conn, "optionPositions", user_id=scope)
    if option_positions:
        pernas_ativo = [p for p in option_positions if p.get("underlying") == t]
        if pernas_ativo:
            posicao = next((p for p in positions if p["t"] == t), None)
            try:
                estrutura_aberta = estrutura_posicao.estrutura_da_posicao(
                    option_positions, t, posicao, spot)
            except Exception:
                estrutura_aberta = None  # falha vira None, não 500
    
    return {
        "ticker": t, "providerStatus": provider_status, "modo": modo,
        "proposta": resultado["proposta"], "motivo": motivo, ...
        "estrutura": estrutura_aberta,  # ADITIVA: `.get()` no cliente
        "candidatos": resultado.get("candidatos", []),
    }
```

**Error handling pattern** (never 500 on market data failure):
```python
# Toda exceção do motor (estrutura_posicao) vira `estrutura=None`,
# nunca dispara HTTPException — degradado já é conhecido via `motivo`.
try:
    estrutura_aberta = estrutura_posicao.estrutura_da_posicao(...)
except Exception:
    estrutura_aberta = None
```

---

### `server/app/skill_ref.py` (utility, frases de motor)

**Analog:** `server/app/skill_ref.py:1-150` (padrão de OPCOES_LASTREADAS) + uso em `opcoes_lastreadas.py`

**Dictionary pattern for OPCOES_LASTREADAS** (exists, add keys D-06):

```python
# LINHAS ~592-707 de skill_ref.py — padrão EXISTENTE:
OPCOES_LASTREADAS = {
    "educacional": {
        "call_coberta": "Você vende uma call ... {n} contrato(s) ...",
        "put_protecao": "Você protege a posição comprando uma put ...",
        "collar": "Você monta uma trava protetora ...",
        # D-06: ADICIONAR chaves novas para gates e estados
        "sem_contrato_liquido": "Frase de ESTUDO (educacional=true) ...",
        "sem_vencimento_elegivel": "Frase de ESTUDO ...",
        # ADR-010 (D-06): nomes distintos de `sem_setup`, chave/frase próprias
        "estado_aberta_sem_proposta": "Frase explicando por que a estrutura aberta ...",
        "estado_vencida": "Frase explicando estrutura vencida ...",
        "estado_exercicio_provavel": "Frase explicando exercício provável ...",
        # Frases de piso/teto (para Card, Fase 45) — formato:
        "faixa_piso": "Proteção limitada a R$ {piso}",
        "faixa_teto": "Ganho limitado a R$ {teto}",
        "faixa_descoberta": "Perna vendida sem cobertura completa de {quantidade}",
    },
    "operador": {
        "call_coberta": "Venda 1 call {strike}, prêmio R$ {premioTotal} ...",
        # ... mirror de educacional, linguagem operacional ...
        # D-06: ADD operador.sem_contrato_liquido, etc.
        "faixa_piso": "{piso}",  # direto, sem texto
        "faixa_teto": "{teto}",
    },
}

# Função canônica: interpolação + fallback para educacional
def opcoes_lastreadas_txt(modo: str, chave: str, **dados: dict) -> str | None:
    """Retorna frase de OPCOES_LASTREADAS interpolada ou None se chave ausente."""
    trees = OPCOES_LASTREADAS.get(modo, {}) or {}
    frase = trees.get(chave)
    if frase is None and modo != "educacional":
        frase = OPCOES_LASTREADAS.get("educacional", {}).get(chave)
    if frase is None:
        return None
    if callable(frase):
        return frase(**dados)
    return frase.format(**dados) if dados else frase
```

**Usage in `estrutura_posicao`**:
```python
# Para cada motivo de porta fechada (vencimentos divergentes, descoberta, etc.)
motivo_texto = skill_ref.opcoes_lastreadas_txt(
    modo, motivo_enum, piso=piso, teto=teto, quantidade=qtd)
```

**Paridade test** (guardião não se apaga, reverter com nota):
```python
# server/tests/test_skill_ref.py — já existe test de paridade
# OPCOES_LASTREADAS entre skill_ref.py e web/src/copy.js
# Reverter deliberadamente: adicionar nota ao commit, nunca apagar a linha
```

---

### `web/src/copy.js` (utility, espelho de frases)

**Analog:** `web/src/copy.js:18-150` (padrão COPY.estudo/operador)

**Paridade pattern** (mirror `skill_ref.OPCOES_LASTREADAS`):

```javascript
export const COPY = {
  estudo: {
    // ... existing keys ...
    
    // D-06: ADICIONAR chaves paralelas a skill_ref.OPCOES_LASTREADAS
    // Educacional = voz de professor, explica o número antes de dizer uso
    opcoesSemContratoLiquido: "Não há contrato com liquidez suficiente...",
    opcoesSemVencimentoElegivel: "O vencimento disponível está fora...",
    
    // Estados (Fase 44, estrutura aberta)
    estruturaAbrertaSemProposta: "A estrutura está aberta, mas não aceitamos nova proposta porque...",
    estruturaVencida: "A estrutura chegou ao vencimento...",
    estruturaExercicioProvavel: "A estrutura pode ser exercida...",
    
    // Faixa/piso/teto (Card Fase 45)
    estruturaFaixaPiso: "Proteção limitada a R$ {piso}",
    estruturaFaixaTeto: "Ganho limitado a R$ {teto}",
    estruturaDescoberta: "Uma perna da estrutura foi vendida sem lastro completo de {quantidade}",
  },
  operador: {
    // ... existing keys ...
    
    // D-06: Operador = linguagem de mesa, direto
    opcoesSemContratoLiquido: "Contrato sem liquidez.",
    opcoesSemVencimentoElegivel: "Vencimento inelegível.",
    
    // Estados
    estruturaAbretraSemProposta: "Estrutura aberta, gate ativo. Motivo: {motivo}",
    estruturaVencida: "Vencida em {data}.",
    estruturaExercicioProvavel: "Exercício provável.",
    
    // Faixa
    estruturaFaixaPiso: "{piso}",
    estruturaFaixaTeto: "{teto}",
    estruturaDescoberta: "Descoberta em {quantidade}",
  },
};

// Importar RR_MIN_TXT de finance.js (paridade com skill_ref.RR_MIN_TXT)
import { RR_MIN_TXT } from "./finance.js";
```

**Guardian test** (não deletar, reverter com nota):
```javascript
// web/tests/test_vocabulario_opcoes.mjs — trava:
// 1. COPY.estudo.estrutura* keys existem
// 2. COPY.operador.estrutura* keys existem
// 3. Chaves são idênticas nos dois modos
// 4. Nenhum vocabulário de ordem ("compra"/"venda") no estudo
```

---

### `server/app/opcoes_lastreadas.py` (service, fechar com error handling)

**Analog:** `server/app/opcoes_lastreadas.py` líneas 405-514 (`proposta_fechar`)

**Extension pattern D-07** (encerrar com `{permitido: false, motivo}`):

```python
def encerrar(pos_opcao: dict, chain: dict, modo: str) -> dict:
    """Proposta de ENCERRAMENTO (eliminação de estrutura aberta).
    
    Diferente de `proposta_fechar`: essa devolve a proposta de RECOMPRA
    (prêmio a pagar para FECHAR). `encerrar` devolve permissão + motivo.
    
    D-07: Se a perna a recomprar não tem cotação → `{permitido: false, motivo: "prêmio_indisponível"}`.
    Estrutura já aberta reprovada por gate de liquidez (novo contrato não cabe)
    → `{permitido: false, motivo: "sem_contrato_liquido"}`.
    
    Retorno:
    - `{permitido: true}` → estrutura pode ser encerrada
    - `{permitido: false, motivo: str}` → motivo específico (prêmio, liquidez, etc.)
    """
    if not isinstance(chain, dict) or chain.get("providerStatus") != "ok":
        return {"permitido": False, "motivo": "degradado"}
    
    # ... buscar contrato na chain ...
    
    premio = contrato.get("lastPrice")
    if not isinstance(premio, (int, float)) or premio <= 0:
        # D-07: prêmio não-numérico vira motivo distinguível
        return {"permitido": False, "motivo": "prêmio_indisponível"}
    
    # ... resto da lógica ...
    return {"permitido": True}
```

---

### `server/tests/test_estrutura_posicao.py` (test, new)

**Analog:** `server/tests/test_opcoes_payoff.py` líneas 1-80

**Module docstring pattern** (reference phase):
```python
"""Fase 44, Plano XX — motor puro de leitura de estrutura por ativo.

Módulo sob teste: `server/app/estrutura_posicao.py`.

Validação de entrada (pernas malformadas), cálculo de estrutura (nome,
resultado, faixa, estado, motivo), casos de borda (vencimentos divergentes,
descoberta, cotação ausente).
"""
import pytest

from app import estrutura_posicao as m
```

**Test pattern** (pure function, no DB/network):
```python
# Teste de normalização + validação
def test_estrutura_da_posicao_call_coberta_simples():
    # Setup: 1 ação + 1 call vendida
    positions = [{"t": "UGPA3", "qty": 100, ...}]
    option_positions = [{"underlying": "UGPA3", "tipo": "CALL", ...}]
    
    # Execute
    result = m.estrutura_da_posicao(option_positions, "UGPA3", 
                                     positions[0], spot=40.0)
    
    # Assert
    assert result["nome"] == "call_coberta"
    assert result["incompleto"] is False
    assert result["resultado_total"] is not None
    assert "estado" in result


def test_estrutura_da_posicao_vencimentos_divergentes_motivo():
    # Setup: call vence 2026-10-01, put vence 2026-10-15
    option_positions = [
        {"underlying": "UGPA3", "tipo": "CALL", "expiration": "2026-10-01", ...},
        {"underlying": "UGPA3", "tipo": "PUT", "expiration": "2026-10-15", ...},
    ]
    
    # Execute
    result = m.estrutura_da_posicao(option_positions, "UGPA3", ...)
    
    # Assert
    assert result["faixa"] is None
    assert result["motivo"] == "vencimentos_diferentes"
    assert len(result["pernas"]) == 2  # SEMPRE visível


def test_estrutura_da_posicao_perna_sem_cotacao_incompleto():
    # Setup: call com lastPrice = None
    option_positions = [{"lastPrice": None, ...}]
    
    # Execute
    result = m.estrutura_da_posicao(option_positions, ...)
    
    # Assert
    assert result["incompleto"] is True
    assert result["resultado_total"] is None
    assert "pernasAusentes" in result
    assert len(result["pernasAusentes"]) > 0
```

---

### `web/tests/test_estrutura_posicao.mjs` (test, new)

**Analog:** `web/tests/test_opcoes_*.mjs` (plain Node scripts, no framework)

**Test pattern** (exported function, assertions):
```javascript
// web/tests/test_estrutura_posicao.mjs
// Rodar como: node web/tests/test_estrutura_posicao.mjs

import assert from "assert";

// Importar os helpers que já existem em outro test
import { api } from "./test_api_parity.mjs";

export async function testEstruturaIntegracao() {
  // Setup
  const ticker = "UGPA3";
  const optionPositions = [
    { underlying: ticker, tipo: "CALL", ... },
  ];
  
  // Execute
  const result = await api.estrutura(ticker, optionPositions);
  
  // Assert
  assert(result.nome === "call_coberta", "Nome incorreto");
  assert(result.incompleto === false, "Deve estar completo");
  assert(typeof result.resultado_total === "number", "Resultado deve ser número");
  console.log("✓ test estrutura integração passou");
}

// Rodar se chamado direto
if (import.meta.url === `file://${process.argv[1]}`) {
  await testEstruturaIntegracao();
}
```

---

## Shared Patterns

### Pure Transform Modules

**Source:** `server/app/opcoes_payoff.py`, `server/app/setups.py`, `server/app/indicators.py`

**Apply to:** `server/app/estrutura_posicao.py`

```python
# Disciplina:
# 1. Sem rede (httpx)
# 2. Sem banco (db.py, store)
# 3. Sem LLM (llm.py)
# 4. Sem leitura de relógio interno (hoje entra por argumento)
# 5. Validação no módulo, não no chamador — mesma checagem em teste/script/rota
# 6. Guardrail: `None` explícito, nunca 0.0 para "desconhecido"
# 7. Toda falha devolve motivo nomeado (enum ou string)
```

### HTTP Response Pattern (Chave Aditiva)

**Source:** `server/app/main.py:3246-3253` (`candidatos` ADITIVA com `.get()`)

**Apply to:** `options_proposta` (adicionar `estrutura`)

```python
# Chave ADITIVA: clientes antigos que não leem `estrutura` funcionam intactos.
# Nunca quebrar paridade — sempre `.get()` com default no leitor.
return {
    "ticker": t,
    # ... campos já existentes ...
    "estrutura": estrutura_aberta,  # NOVO: `.get("estrutura", None)` no cliente
}
```

### Vocabulary Lookup & Interpolation

**Source:** `server/app/skill_ref.opcoes_lastreadas_txt(modo, chave, **dados)`

**Apply to:** Qualquer motivo ou estado que precise de frase

```python
# Frase SEMPRE vem de skill_ref.py, nunca do motor nem do cliente.
# Interpolação com dados necessários — motivo, quantidade, strike, etc.
motivo_texto = skill_ref.opcoes_lastreadas_txt(
    modo, "vencimentos_diferentes",
    dias1="2026-10-01", dias2="2026-10-15")
```

### Error Handling — Never 500 on Market Data

**Source:** `server/app/main.py:3232-3234` (rota options_proposta)

**Apply to:** Toda rota que toca provedor de mercado

```python
try:
    resultado = estrutura_posicao.estrutura_da_posicao(...)
except Exception:
    resultado = None  # Nunca exceção; caller trata None como "degradado"
    # já reportado via motivo anterior ou providerStatus
```

### Paridade Backend ↔ Frontend

**Source:** `web/tests/test_api_parity.mjs`, `server/tests/test_auditoria_prompts.py`

**Apply to:** `skill_ref.OPCOES_LASTREADAS` ↔ `web/src/copy.js`

```python
# Guardiões travando:
# 1. Chaves idênticas nos dois modos de skill_ref.py
# 2. Chaves COPY.estudo.estrutura* ⊇ chaves no skill_ref (superconjunto)
# 3. Reversão deliberada atualiza nota no commit, nunca apaga
# 4. Teste falha se houver divergência

# Exemplo: skill_ref.py adiciona "sem_contrato_liquido"
# → web/src/copy.js DEVE ter COPY.estudo.opcoesSemContratoLiquido + operador
# → test_auditoria trava a paridade
```

---

## No Analog Found

None — todos os padrões têm análogo direto no codebase.

---

## Metadata

**Analog search scope:** 
- `server/app/*.py` (módulos de motor: payoff, lastreadas, skill_ref, indicators, setups)
- `web/src/*.js` (copy.js, finance.js, catalog.js)
- `server/tests/test_*.py` (patterns de unit test)
- `web/tests/test_*.mjs` (patterns de integration test)

**Files scanned:** 8 source + 4 test files

**Pattern extraction date:** 2026-09-29

---

## PATTERN MAPPING COMPLETE

**Phase:** 44 - motor-estrutura-por-ativo
**Files classified:** 6 (1 new, 5 modified)
**Analogs found:** 5 / 5 (100%)

### Coverage
- Files with exact analog: 5
- Files with role-match analog: 1 (tests — pattern reuse)
- Files with no analog: 0

### Key Patterns Identified
- **Pure module discipline:** No I/O, no clock, no DB inside motor (analógo: `opcoes_payoff.py`)
- **Chave ADITIVA em rota:** `.get()` com default nunca quebra clientes antigos (analógo: `options_proposta`)
- **Frases do skill_ref → copy.js:** Paridade travada, reversão deliberada com nota (analógo: OPCOES_LASTREADAS)
- **Transform puro com motivo nomeado:** Toda falha retorna enum/string de estado, nunca None silencioso (analógo: `opcoes_lastreadas.propor`)
- **Validação no módulo:** Mesma checagem em teste/script/rota, guardrail null explícito (analógo: `opcoes_payoff._validar_perna`)

### Ready for Planning
Pattern mapping complete. Planner can now reference analog patterns in PLAN.md files.
