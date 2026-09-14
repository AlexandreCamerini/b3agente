"""Fase 30, Plano 03 — a etapa de IA da curadoria: narração fina sobre o
top-4 já ordenado pelo motor determinístico.

Este módulo é o ÚNICO ponto onde a IA toca a curadoria de estruturas de
opções, e ele recebe a lista final já pronta por parâmetro (`top`). É
PROIBIDO este módulo importar o motor de enumeração/avaliação de
estruturas, chamar a função de enumeração de candidatos por posição ou a
função de ordenação do módulo puro da Fase 30, ou aceitar um pool não
ordenado — se uma manutenção futura precisar de mais candidatos, quem os
ordena é a camada determinística no chamador (`server/app/main.py`),
nunca aqui. O motivo é o guardrail não-negociável da Fase 30
(30-CONTEXT.md) e o princípio 5 do CLAUDE.md: cálculo financeiro é sempre
determinístico, nunca da IA — este módulo só ESCREVE texto sobre uma
decisão já tomada, nunca a toma.

Também é proibido buscar cadeia de opções aqui: nenhuma chamada ao
provedor de mercado (rede) pertence a esta camada — só o texto que o
modelo de linguagem escreve sobre dados já resolvidos por quem chamou
`narrar`.

Espelha `assistente.responder` (server/app/assistente.py:280-342): mesma
camada fina de LLM (coleta de uso, chamada ao modelo, registro de
atividade em try/except, normalização de markdown).
"""
from __future__ import annotations

from typing import Any

from . import ai_activity, kpi, llm, opcoes_curadoria

# TIPO: rótulo do ledger de `ai_activity` — separa este gasto dos demais
# (ex.: "Análise") no portal admin.
TIPO = "Curadoria"

# MAX_TOKENS: 4 parágrafos curtos, um por estrutura do topo do módulo puro
# da Fase 30. Menor que o teto do assistente contextual (que sustenta
# conversa aberta) porque o formato aqui é FECHADO: um parágrafo por item
# de uma lista pequena, nunca uma resposta livre.
MAX_TOKENS = 900


async def narrar(conn, config: dict, scope, modo: str, top: list[dict[str, Any]]) -> dict:
    """Escreve um parágrafo por estrutura sobre `top`, na ordem recebida."""
    # PRIMEIRA ação do corpo: recusa ANTES de qualquer chamada ao modelo.
    opcoes_curadoria.exigir_ranking(top)
    if not top:
        raise ValueError(
            "narrar precisa de pelo menos 1 estrutura no top; lista vazia "
            "pertence à decisão da rota, que não deve chamar esta função "
            "sem ter algo para narrar")

    # `top` precisa ser exatamente a saída do módulo puro da Fase 30
    # (validado acima pela função de exigência de ranking) e não pode ser
    # vazio — decidir que não há o que narrar pertence à rota (Task 2), que
    # não deve sequer chamar esta função com lista vazia.
    #
    # Contabilidade (`ai_activity`) nunca derruba a resposta: mesmo
    # precedente de `assistente.responder` — falha de registro vira log,
    # não exceção. A cota em si (quanto custa, se ainda há direito de
    # gastar) é decidida inteiramente pela ROTA, via o mesmo gate de
    # `/api/analyze` (D6, 30-CONTEXT) — este módulo não implementa nenhum
    # freio de custo próprio, nem em tokens além de `MAX_TOKENS`, nem em
    # R$. Um freio paralelo aqui seria exatamente o orçamento paralelo que
    # D6 proíbe; se uma manutenção futura achar que falta um limite, o
    # lugar certo para revisar é o gate da rota, não duplicá-lo aqui.
    system = opcoes_curadoria.narrativa_system(modo)
    user = opcoes_curadoria.narrativa_user(top, modo)

    key = llm.resolve_key(config)
    # `_call_llm` devolve TEXTO (não o JSON do provedor) e já aplica a
    # normalização de cache do prefixo por dentro. Precedente de uso fora
    # de `llm.py`: server/app/assistente.py:320-321.
    with llm.collect_usage() as usos:
        texto = await llm._call_llm(config, key, system, user, MAX_TOKENS)

    try:
        # ticker="-": a narração é cross-posição — não pertence a um ativo
        # único, mesmo sentinela que outras rotas usam sem ticker.
        ai_activity.registrar_uso(conn, scope=scope, ticker="-", tipo=TIPO, usos=usos)
    except Exception as e:  # noqa: BLE001 — contabilidade nunca derruba a resposta
        print(f"[curadoria_narrativa] registro de custo falhou: {e}")

    return {
        "texto": kpi.normalize_markdown((texto or "").strip()),
        # A lista de símbolos NA ORDEM narrada viaja de propósito: é o que
        # permite ao cliente (e ao teste) provar que o texto fala das
        # MESMAS estruturas que a tela mostra, na mesma ordem.
        "estruturas": [it["contractSymbol"] for it in top],
    }
