"""Aritmética pura de payoff de estrutura de opções de N pernas.

Módulo PURO — sem rede, sem banco, sem LLM, sem leitura de relógio, mesma
disciplina de `opcoes_lastreadas.py`/`setups.py`/`indicators.py`. Portado de
`~/dev/MCP/servers/mydata/calculos.py` (linhas 255-464), repo externo,
adaptado ao vocabulário e às mensagens em PT-BR já usados no Boris — Fase 15,
Plano 01, ENG-02.

Duas convenções herdadas da fonte, válidas para o arquivo inteiro:

  1. **Tudo por unidade do objeto.** Prêmio, strike e resultado são por ação.
     Lote de 100 multiplica do lado de fora — nunca embutir esse fator aqui.
  2. **Nulo sempre tem motivo.** `ganho_maximo`/`perda_maxima` só viram `None`
     quando a estrutura é de fato ilimitada naquele lado; `delta_total` só
     soma o que tem dado e declara `motivo` quando a soma é parcial. Nunca
     `0.0` no lugar de "desconhecido" (mesmo guardrail de
     `test_m3_format_pede_null_nunca_zero`).

NÃO portado deste arquivo (decisão de escopo do Plano 01): `FERIADOS_B3`,
`spread`, `moneyness`, `breakeven_compra_seco` (já têm equivalente em
`server/app/options_quant.py` — `liquidity_score`, `breakeven`,
`intrinsic_value`; duplicar criaria duas escalas para a mesma pergunta),
`prazo_em_pregoes` (calendário, fora do escopo de payoff) e o filtro de
seleção de contrato por delta que ENG-01 proíbe — a régua do Boris é
liquidez + strike extremo, já em produção em `opcoes_lastreadas.py`.
"""
from __future__ import annotations

from typing import Any, Sequence

TIPOS = ("CALL", "PUT")
# Perna de estrutura aceita um terceiro tipo que não é contrato de opção: a
# própria ação. Venda coberta e collar não existem sem ela, e sintetizar o
# papel como "CALL de strike zero" funcionaria no payoff mas confundiria o
# relatório — o leitor precisa ver ACAO onde há ação.
TIPOS_PERNA = TIPOS + ("ACAO",)
LADOS = ("compra", "venda")


# ─────────────────────────────────────────────────────────────────────────
# utilitários internos
# ─────────────────────────────────────────────────────────────────────────

def _numero(valor: Any) -> float | None:
    """Aceita int/float, recusa bool e qualquer outra coisa.

    `bool` é subclasse de `int` em Python, e um `True` que chega como strike
    viraria 1.0 silenciosamente. Recusar aqui é mais barato que caçar depois.
    """
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return None
    return float(valor)


def _tipo(contrato: dict[str, Any], permitidos: Sequence[str] = TIPOS) -> str | None:
    t = str(contrato.get("tipo", "")).upper()
    return t if t in permitidos else None


# ─────────────────────────────────────────────────────────────────────────
# estrutura de múltiplas pernas
# ─────────────────────────────────────────────────────────────────────────

def _validar_perna(perna: dict[str, Any], i: int) -> dict[str, Any]:
    """Recusa perna malformada com mensagem que nomeia a perna e o campo.

    Validar aqui, e não no chamador, é o que garante a mesma checagem para
    quem monta a perna a partir de um teste, de um script ou da rota HTTP.
    """
    tipo = _tipo(perna, TIPOS_PERNA)
    if tipo is None:
        raise ValueError(
            f"perna {i}: tipo precisa ser CALL, PUT ou ACAO, veio {perna.get('tipo')!r}")

    lado = str(perna.get("lado", "")).lower()
    if lado not in LADOS:
        raise ValueError(
            f"perna {i}: lado precisa ser 'compra' ou 'venda', veio {perna.get('lado')!r}")

    # Ação não tem strike. Zero aqui não é "valor faltando": é a constante
    # que faz o payoff linear cair no lugar certo, já que o intrínseco do
    # papel é o próprio preço e não depende de nenhum ponto de exercício.
    if tipo == "ACAO":
        strike = 0.0 if perna.get("strike") is None else _numero(perna.get("strike"))
        if strike is None or strike != 0:
            raise ValueError(
                f"perna {i}: ACAO não tem strike; use 0 ou omita, veio {perna.get('strike')!r}")
    else:
        strike = _numero(perna.get("strike"))
        if strike is None or strike <= 0:
            raise ValueError(f"perna {i}: strike inválido: {perna.get('strike')!r}")

    # Para ACAO, `premio` é o preço pago pelo papel (o preço do objeto no
    # pregão). Mesmo campo, mesma unidade, significado diferente — é isso
    # que permite uma única fórmula de custo líquido cobrir os dois casos.
    premio = _numero(perna.get("premio"))
    if premio is None or premio < 0:
        raise ValueError(f"perna {i}: prêmio inválido: {perna.get('premio')!r}")
    if tipo == "ACAO" and premio <= 0:
        raise ValueError(
            f"perna {i}: ACAO precisa do preço do papel em 'premio', veio {perna.get('premio')!r}")

    quantidade = _numero(perna.get("quantidade", 1))
    if quantidade is None or quantidade <= 0:
        raise ValueError(
            f"perna {i}: quantidade precisa ser positiva, veio {perna.get('quantidade')!r}")

    return {
        "contrato": perna.get("contrato"),
        "tipo": tipo,
        "lado": lado,
        "sinal": 1.0 if lado == "compra" else -1.0,
        "strike": strike,
        "premio": premio,
        "quantidade": quantidade,
        "delta": _numero(perna.get("delta")),
    }


def custo_liquido(normalizadas: Sequence[dict[str, Any]]) -> float:
    """Débito (>0) ou crédito (<0) líquido da estrutura, por unidade do objeto."""
    return round(sum(p["sinal"] * p["quantidade"] * p["premio"] for p in normalizadas), 4)


def _resultado_no_vencimento(pernas: Sequence[dict[str, Any]], preco: float,
                              custo_liquido_: float) -> float:
    total = 0.0
    for p in pernas:
        if p["tipo"] == "ACAO":
            # A ação não expira nem vira pó: no vencimento das opções ela
            # vale o que estiver valendo. Por isso o intrínseco é o próprio
            # preço.
            intrinseco = preco
        elif p["tipo"] == "CALL":
            intrinseco = max(preco - p["strike"], 0.0)
        else:
            intrinseco = max(p["strike"] - preco, 0.0)
        total += p["sinal"] * p["quantidade"] * intrinseco
    return total - custo_liquido_


def resultado_no_vencimento(pernas: Sequence[dict[str, Any]], preco: float) -> float:
    """Resultado da estrutura num preço qualquer do objeto, no vencimento.

    `perfil_da_estrutura` avalia a curva só onde ela dobra (zero e os
    strikes), porque basta para achar extremos e breakevens. Cenário é outra
    pergunta: "e se o papel estiver a 41,03?" cai no meio de um trecho reto,
    onde não há ponto avaliado. Esta função responde essa — mesma validação,
    mesmo custo líquido, ponto arbitrário.
    """
    if not pernas:
        raise ValueError("estrutura sem pernas: informe ao menos um contrato")
    s = _numero(preco)
    if s is None or s < 0:
        raise ValueError(f"preço do objeto inválido: {preco!r}")

    normalizadas = [_validar_perna(p, i) for i, p in enumerate(pernas, start=1)]
    return round(_resultado_no_vencimento(normalizadas, s, custo_liquido(normalizadas)), 4)


def perfil_da_estrutura(pernas: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Perfil de uma posição de N pernas no vencimento.

    Venda coberta, put de proteção e collar não são três funcionalidades:
    são três entradas desta função.

    O payoff é linear por partes, com quebra exatamente nos strikes. Então
    avaliar em `S=0` e em cada strike encontra todos os extremos do miolo —
    e a inclinação da cauda direita decide se ganho ou perda é ilimitado.
    Sem esse passo, a função devolveria o maior número que viu e chamaria de
    ganho máximo, e uma call vendida a descoberto passaria por operação
    limitada.
    """
    if not pernas:
        raise ValueError("estrutura sem pernas: informe ao menos um contrato")

    normalizadas = [_validar_perna(p, i) for i, p in enumerate(pernas, start=1)]

    custo = custo_liquido(normalizadas)

    # A perna ACAO entra com strike 0, que já é o ponto de partida da
    # avaliação: o conjunto evita avaliar o mesmo preço duas vezes e
    # duplicar a curva.
    avaliar = sorted({0.0, *(p["strike"] for p in normalizadas)})
    curva = [
        {"preco_objeto": round(s, 4),
         "resultado": round(_resultado_no_vencimento(normalizadas, s, custo), 4)}
        for s in avaliar
    ]

    # Inclinação além do maior strike: cada CALL comprada soma +1 por
    # unidade, cada CALL vendida soma -1, e PUT já não vale nada ali. ACAO
    # entra na mesma soma que a CALL — acima de todos os strikes o papel
    # sobe real por real, exatamente como uma call exercida. É essa linha
    # que faz a venda coberta (ACAO +1, CALL vendida -1 -> inclinação 0)
    # aparecer como ganho limitado em vez de ilimitado, e o collar ficar
    # travado dos dois lados.
    inclinacao_direita = sum(
        p["sinal"] * p["quantidade"] for p in normalizadas
        if p["tipo"] in ("CALL", "ACAO"))

    resultados = [ponto["resultado"] for ponto in curva]
    ganho_ilimitado = inclinacao_direita > 0
    perda_ilimitada = inclinacao_direita < 0

    ganho_maximo = None if ganho_ilimitado else round(max(resultados), 4)
    if perda_ilimitada:
        perda_maxima = None
    else:
        pior = min(resultados)
        perda_maxima = round(-pior, 4) if pior < 0 else 0.0

    return {
        "pernas": [
            {"contrato": p["contrato"], "tipo": p["tipo"], "lado": p["lado"],
             "quantidade": p["quantidade"], "strike": p["strike"], "premio": p["premio"]}
            for p in normalizadas
        ],
        "custo_liquido": custo,
        "fluxo": "debito" if custo > 0 else ("credito" if custo < 0 else "neutro"),
        "ganho_maximo": ganho_maximo,
        "perda_maxima": perda_maxima,
        "ganho_ilimitado": ganho_ilimitado,
        "perda_ilimitada": perda_ilimitada,
        "breakevens": _breakevens(curva, inclinacao_direita),
        "delta_total": _delta_total(normalizadas),
        "curva": curva,
        "unidade": "por unidade do objeto (uma ação); multiplique pelo lote se precisar",
    }


def _breakevens(curva: list[dict[str, Any]], inclinacao_direita: float) -> list[float]:
    """Onde a curva de resultado cruza o zero.

    Dois casos: cruzamento entre dois pontos avaliados (interpolação linear,
    exata porque o trecho é reto) e cruzamento na cauda à direita do último
    strike, onde não há próximo ponto e quem responde é a inclinação.
    """
    pontos: list[float] = []

    for anterior, atual in zip(curva, curva[1:]):
        y0, y1 = anterior["resultado"], atual["resultado"]
        x0, x1 = anterior["preco_objeto"], atual["preco_objeto"]
        if y0 == 0:
            pontos.append(x0)
        if (y0 < 0 < y1) or (y1 < 0 < y0):
            pontos.append(round(x0 + (x1 - x0) * (-y0) / (y1 - y0), 4))

    ultimo = curva[-1]
    if ultimo["resultado"] == 0:
        pontos.append(ultimo["preco_objeto"])
    elif inclinacao_direita:
        adiante = ultimo["preco_objeto"] - ultimo["resultado"] / inclinacao_direita
        if adiante > ultimo["preco_objeto"]:
            pontos.append(round(adiante, 4))

    return sorted(dict.fromkeys(pontos))


def _delta_total(pernas: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Delta somado da posição, dizendo quantas pernas ficaram de fora.

    Uma perna sem delta calculado torna a soma incompleta, e uma soma
    incompleta apresentada como completa é pior que soma nenhuma.
    """
    total = 0.0
    faltando = 0
    for p in pernas:
        if p["delta"] is None:
            faltando += 1
            continue
        total += p["sinal"] * p["quantidade"] * p["delta"]
    if faltando:
        return {"valor": round(total, 4), "pernas_sem_delta": faltando,
                "motivo": "soma parcial: alguma perna não tem delta calculado"}
    return {"valor": round(total, 4), "pernas_sem_delta": 0, "motivo": None}
