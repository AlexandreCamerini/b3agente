"""Limite interno da Fase 15: `rastrear()` (screening de cadeia) e `avaliar()`
(avaliação de estrutura), mais os adaptadores contrato ADR-004 -> perna de
payoff.

Módulo PURO — sem rede, sem banco, sem LLM, sem leitura de relógio, mesma
disciplina de `opcoes_lastreadas.py`/`opcoes_payoff.py`/`setups.py`/
`indicators.py`.

ENG-04: `rastrear`/`avaliar` são o limite interno equivalente a
`find_tradable_options`/`evaluate_option_structure` do b-mcp
(`~/dev/MCP/docs/plano-mcp-servico.md`, repo separado, ainda não aprovado).
Quando esse plano for aprovado pelo Alex, a troca é do CORPO das duas
funções — nunca do chamador. É por isso que este módulo não pode conhecer
carteira, sessão, texto de UI nem relógio: qualquer dependência dessas
camadas amarraria o corpo de hoje a quem chama, e a troca deixaria de ser
possível sem redesenho.
"""
from __future__ import annotations

from typing import Any

from .options_quant import liquidity_score

# Corte de liquidez em produção desde a Fase 14 (`opcoes_lastreadas.py`).
# Fonte ÚNICA no repo: `opcoes_lastreadas` importa esta constante em vez de
# declarar o próprio literal 40.
LIQUIDEZ_MINIMA = 40


# ─────────────────────────────────────────────────────────────────────────
# rastrear() — screening de cadeia (ENG-01, equivalente a find_tradable_options)
# ─────────────────────────────────────────────────────────────────────────

def _candidato_valido(contrato: dict[str, Any], liquidez_minima: float) -> bool:
    """Replica `opcoes_lastreadas._candidato_valido`: `lastPrice` numérico
    e > 0, e `liquidity_score(...)["score"] >= liquidez_minima`."""
    preco = contrato.get("lastPrice")
    if not isinstance(preco, (int, float)) or isinstance(preco, bool) or preco <= 0:
        return False
    liq = liquidity_score(contrato.get("volume"), contrato.get("openInterest"),
                           contrato.get("bid"), contrato.get("ask"))
    return liq["score"] >= liquidez_minima


def rastrear(cadeia: Any, filtros: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Contratos negociáveis de uma cadeia ADR-004, pela régua já em produção
    (liquidez + strike extremo).

    `filtros` aceita: `tipo` ("call"|"put"), `referencia` (spot, float|None),
    `relacao` ("acima" -> strike > referencia; "abaixo_ou_igual" -> strike <=
    referencia; ausente -> não filtra por spot), `criterio` ("min"|"max",
    default "min"), `liquidez_minima` (default `LIQUIDEZ_MINIMA`), `n`
    (default 1).

    Devolve sempre uma lista — `[]` em toda porta fechada (cadeia inválida,
    degradada, tipo desconhecido, nenhum candidato líquido), nunca `None` e
    nunca uma exceção. Os dicts devolvidos são os contratos ADR-004
    ORIGINAIS, intactos: `rastrear` seleciona, não remapeia.

    O que esta função NÃO faz, de propósito:

    - Não filtra por prazo (`_PRAZO_MIN_DIAS`/`_PRAZO_MAX_DIAS` de
      `opcoes_lastreadas.py`). A cadeia ADR-004 carrega UM vencimento só
      (`cadeia["expiration"]`); prazo é decisão sobre a cadeia inteira, não
      screening contrato a contrato — continua no chamador.
    - Não distingue "cadeia degradada" de "nenhum contrato líquido": os dois
      casos devolvem `[]`. Quem precisa de motivos diferentes checa
      `providerStatus` ANTES de chamar `rastrear`, exatamente como
      `server/app/main.py:2390` já faz.
    """
    # PROIBIDO somar filtro ou ordenação pelo grego de sensibilidade ao preço
    # (o "d" das gregas, exposto em cada contrato como `greeks`) neste ponto
    # da seleção. ENG-01 é explícito: a régua do Boris é liquidez + strike
    # extremo, já em produção — não o critério do `estruturas.py` do b-mcp.
    # Se você está pensando em aproximar por sensibilidade aqui, pare: isso é
    # mudança de régua, não melhoria, e precisa passar por decisão de
    # produto antes de virar código.
    if not isinstance(cadeia, dict):
        return []
    if cadeia.get("providerStatus") != "ok":
        return []

    filtros = filtros or {}
    tipo = str(filtros.get("tipo") or "").lower()
    if tipo == "call":
        candidatos = cadeia.get("calls") or []
    elif tipo == "put":
        candidatos = cadeia.get("puts") or []
    else:
        return []

    referencia = filtros.get("referencia")
    relacao = filtros.get("relacao")
    if relacao == "acima" and isinstance(referencia, (int, float)):
        candidatos = [c for c in candidatos if (c.get("strike") or 0) > referencia]
    elif relacao == "abaixo_ou_igual" and isinstance(referencia, (int, float)):
        candidatos = [c for c in candidatos if (c.get("strike") or 0) <= referencia]

    liquidez_minima = filtros.get("liquidez_minima", LIQUIDEZ_MINIMA)
    validos = [c for c in candidatos if _candidato_valido(c, liquidez_minima)]
    if not validos:
        return []

    ordenados = sorted(validos, key=lambda c: c.get("strike") or 0)
    criterio = filtros.get("criterio") or "min"
    n = filtros.get("n") or 1
    selecionados = ordenados[:n] if criterio == "min" else list(reversed(ordenados))[:n]
    return selecionados
