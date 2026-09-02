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
from .opcoes_payoff import perfil_da_estrutura

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


# ─────────────────────────────────────────────────────────────────────────
# adaptadores: contrato ADR-004 / ação -> perna de payoff (ENG-04)
# ─────────────────────────────────────────────────────────────────────────

_OPTION_TYPE_PARA_TIPO = {"call": "CALL", "put": "PUT"}


def perna_de_contrato(contrato: dict[str, Any], lado: str, quantidade: float = 1) -> dict[str, Any]:
    """Adapta um contrato da cadeia ADR-004 para o vocabulário de perna de
    `opcoes_payoff` (`contrato`, `tipo`, `lado`, `strike`, `premio`,
    `quantidade`, `delta`) — sem que o chamador precise conhecer o
    vocabulário interno do payoff.

    Falha alto, no adaptador, e não fundo na aritmética de `opcoes_payoff` —
    é o que mantém a mensagem de erro legível e nomeando o `contractSymbol`.
    Um contrato sem prêmio publicado (`lastPrice` None/0/negativo) é
    recusado aqui: NUNCA vira perna de prêmio 0 (CLAUDE.md princípio 4,
    regra "null nunca 0.0").
    """
    symbol = contrato.get("contractSymbol")
    tipo = _OPTION_TYPE_PARA_TIPO.get(str(contrato.get("optionType") or "").lower())
    if tipo is None:
        raise ValueError(
            f"contrato {symbol!r}: optionType precisa ser 'call' ou 'put', "
            f"veio {contrato.get('optionType')!r}")

    premio = contrato.get("lastPrice")
    if not isinstance(premio, (int, float)) or isinstance(premio, bool) or premio <= 0:
        raise ValueError(
            f"contrato {symbol!r}: sem prêmio publicado (lastPrice="
            f"{contrato.get('lastPrice')!r}) — não pode virar perna")

    if not isinstance(quantidade, (int, float)) or isinstance(quantidade, bool) or quantidade <= 0:
        raise ValueError(f"contrato {symbol!r}: quantidade precisa ser positiva, veio {quantidade!r}")

    delta = (contrato.get("greeks") or {}).get("delta")

    return {
        "contrato": symbol,
        "tipo": tipo,
        "lado": lado,
        "strike": contrato.get("strike"),
        "premio": float(premio),
        "quantidade": quantidade,
        "delta": delta,
    }


def perna_de_acao(ticker: str, preco: float, quantidade: float) -> dict[str, Any]:
    """Perna de lastro (a própria ação) — sem ela, venda coberta e collar não
    existem. `strike` 0.0 é a constante que faz o payoff linear cair no
    lugar certo (ver `opcoes_payoff._validar_perna`), não um valor faltando.
    `delta` 1.0 é identidade matemática da ação, não estimativa."""
    if not isinstance(preco, (int, float)) or isinstance(preco, bool) or preco <= 0:
        raise ValueError(f"ação {ticker!r}: preço precisa ser positivo, veio {preco!r}")
    if not isinstance(quantidade, (int, float)) or isinstance(quantidade, bool) or quantidade <= 0:
        raise ValueError(f"ação {ticker!r}: quantidade precisa ser positiva, veio {quantidade!r}")

    return {
        "contrato": ticker,
        "tipo": "ACAO",
        "lado": "compra",
        "strike": 0.0,
        "premio": float(preco),
        "quantidade": quantidade,
        "delta": 1.0,
    }


# ─────────────────────────────────────────────────────────────────────────
# avaliar() — avaliação de estrutura (ENG-04, equivalente a evaluate_option_structure)
# ─────────────────────────────────────────────────────────────────────────

def avaliar(pernas: list[dict[str, Any]]) -> dict[str, Any]:
    """Custo líquido, ganho/perda máximos, breakevens e delta somado de uma
    estrutura de N pernas.

    O corpo é uma delegação DIRETA a `opcoes_payoff.perfil_da_estrutura`, sem
    renomear nenhuma chave do dicionário devolvido — a Fase 16 e a Fase 17
    consomem esse dicionário direto. A magreza é o desenho, não descuido: é
    exatamente por `avaliar` não acrescentar semântica própria que trocar seu
    corpo por uma chamada a `evaluate_option_structure` do b-mcp não muda
    nenhum chamador. Não "simplifique" removendo esta indireção.
    """
    return perfil_da_estrutura(pernas)
