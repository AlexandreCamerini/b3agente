"""Motor puro de proposta de opção lastreada (Fase 14, Plano 03).

Módulo PURO — sem rede, sem banco, sem LLM, sem leitura de relógio interna
(`hoje` entra por argumento), mesma disciplina de `setups.py`/`indicators.py`.

A ÚNICA fonte da MANCHETE é `skill_ref.opcoes_lastreadas_txt` — este módulo
escolhe O QUE propor (contrato, quantidade, prêmio, motivo de ausência); o
TEXTO vem sempre de lá (guardrail CVM: a IA explica, nunca substitui a
manchete do motor determinístico).
"""
import datetime as dt

from . import skill_ref, store
from .options_quant import liquidity_score

# Prazo elegível: cadeia carregada traz um vencimento só — escolher outro é
# papel da cadeia expansível, não da proposta.
_PRAZO_MIN_DIAS = 15
_PRAZO_MAX_DIAS = 60
_LIQUIDEZ_MINIMA = 40


def _dias_ate(expiration, hoje):
    if not expiration:
        return None
    try:
        d = dt.date.fromisoformat(expiration)
    except (TypeError, ValueError):
        return None
    return (d - hoje).days


def _label_liquidez(score):
    """Reusa os cortes já usados na UI — não inventar uma segunda escala."""
    if score >= 55:
        return "NEGOCIÁVEL"
    if score >= 30:
        return "DIFÍCIL"
    return "SEM MERCADO"


def _candidato_valido(c):
    preco = c.get("lastPrice")
    if not isinstance(preco, (int, float)) or preco <= 0:
        return False
    liq = liquidity_score(c.get("volume"), c.get("openInterest"), c.get("bid"), c.get("ask"))
    return liq["score"] >= _LIQUIDEZ_MINIMA


def _escolher_contrato(candidatos, melhor):
    """`melhor` é `min` (menor strike — call OTM mais próxima) ou `max`
    (maior strike — put mais próxima do spot, proteção mais próxima)."""
    validos = [c for c in candidatos if _candidato_valido(c)]
    if not validos:
        return None
    return melhor(validos, key=lambda c: c.get("strike") or 0)


def propor(underlying, chain, spot, plano, posicao, cash, modo, hoje):
    """Proposta de UM contrato (venda coberta ou put de proteção) a partir da
    leitura técnica do ativo-lastro e do lastro livre — ou a ausência
    explicada por um motivo nomeado (CLAUDE.md princípio 4: nunca inventar
    proposta; toda porta fechada devolve `proposta=None` com `motivo`).

    Devolve sempre `{"proposta": <dict|None>, "motivo": <str>}`; em sucesso,
    `motivo` é o próprio `tipo` (`call_coberta`|`put_protecao`) — também uma
    chave de vocabulário válida, então o chamador nunca precisa checar
    `proposta is not None` para saber que motivo interpretar."""
    if not isinstance(chain, dict) or chain.get("providerStatus") != "ok":
        return {"proposta": None, "motivo": "degradado"}
    if not isinstance(posicao, dict) or store.qty_livre(posicao) < 100:
        return {"proposta": None, "motivo": "sem_lastro"}

    plano = plano or {}
    decisao = plano.get("decisao")
    lado = plano.get("lado")
    if decisao == "VENDER" or lado == "baixa":
        # Risco de queda sobre posição existente: proteger com PUT.
        tipo = "put_protecao"
    elif decisao in ("AGUARDAR CONFIRMAÇÃO", "NÃO OPERAR") or lado == "neutro":
        # Sem alta a preservar: vender o upside gera prêmio.
        tipo = "call_coberta"
    else:
        # decisao == "COMPRAR" ou lado == "alta": vender call contra a alta
        # que o motor está lendo trava justamente o movimento; comprar put
        # contra alta é pagar proteção que o motor não pede. `plano`
        # ausente/vazio (decisao/lado None) cai aqui também.
        return {"proposta": None, "motivo": "sem_setup"}

    dias = _dias_ate(chain.get("expiration"), hoje)
    if dias is None or not (_PRAZO_MIN_DIAS <= dias <= _PRAZO_MAX_DIAS):
        return {"proposta": None, "motivo": "sem_vencimento_elegivel"}

    if tipo == "call_coberta":
        candidatos = [c for c in (chain.get("calls") or []) if (c.get("strike") or 0) > spot]
        contrato = _escolher_contrato(candidatos, min)
    else:
        candidatos = [c for c in (chain.get("puts") or []) if (c.get("strike") or 0) <= spot]
        contrato = _escolher_contrato(candidatos, max)
    if not contrato:
        return {"proposta": None, "motivo": "sem_contrato_liquido"}

    qty_livre_val = store.qty_livre(posicao)
    contratos = qty_livre_val // 100
    premio = float(contrato.get("lastPrice") or 0)
    if tipo == "put_protecao":
        contratos = min(contratos, int(cash // (100 * premio)) if premio > 0 else 0)
        if contratos < 1:
            return {"proposta": None, "motivo": "caixa_insuficiente"}

    qty_acoes = contratos * 100
    premio_total = round(premio * qty_acoes, 2)
    liq = liquidity_score(contrato.get("volume"), contrato.get("openInterest"), contrato.get("bid"), contrato.get("ask"))
    strike = contrato.get("strike")

    dados = {
        "n": str(contratos), "ticker": underlying, "strike": skill_ref.num_br(strike),
        "premioTotal": skill_ref.num_br(premio_total), "qtyAcoes": str(qty_acoes),
    }
    manchete = skill_ref.opcoes_lastreadas_txt(modo, tipo, **dados)
    # `didatica` = a mesma frase no modo educacional, SEMPRE presente (o
    # Estudo a usa como corpo; o Operador pode exibi-la como explicação
    # secundária) — nunca recomputada por outro caminho.
    didatica = skill_ref.opcoes_lastreadas_txt("educacional", tipo, **dados)

    proposta = {
        "tipo": tipo,
        "contractSymbol": contrato.get("contractSymbol"),
        "optionType": contrato.get("optionType"),
        "strike": strike,
        "expiration": chain.get("expiration"),
        "diasParaVencimento": dias,
        "contratos": contratos,
        "qtyAcoes": qty_acoes,
        "premioUnitario": round(premio, 2),
        "premioTotal": premio_total,
        "lastro": {"t": underlying, "qtyLivre": qty_livre_val},
        "liquidez": {"score": liq["score"], "label": _label_liquidez(liq["score"])},
        "manchete": manchete,
        "didatica": didatica,
        "chips": [
            {"k": "prazo", "v": f"{dias} dias"},
            {"k": "strike", "v": f"R$ {skill_ref.num_br(strike)}"},
            {"k": "prêmio", "v": f"R$ {skill_ref.num_br(premio)}"},
            {"k": "liquidez", "v": _label_liquidez(liq["score"])},
        ],
    }
    return {"proposta": proposta, "motivo": tipo}


def proposta_fechar(pos_opcao, chain, modo, hoje):
    """Proposta de FECHAMENTO de uma posição lastreada JÁ ABERTA — irmã de
    `propor()` para quando a carteira já tem uma call vendida/put comprada
    neste `underlying` (bug do checkpoint humano do Plano 08: `propor()` é
    stateless e pode escolher um contrato DIFERENTE do já aberto a cada
    chamada — spot mudou, a leitura técnica mudou — e o front casa a
    proposta com a posição só por `contractSymbol` idêntico
    (`web/src/App.jsx:3216-3217`), então o CTA "Recomprar/fechar" some
    depois da primeira operação). Esta função NUNCA re-escolhe contrato: lê
    o MESMO contrato já aberto (por `id`==`contractSymbol`) na cadeia
    atual, só para atualizar o prêmio de recompra/venda — `propor()`
    continua intocado e puro.

    `pos_opcao`: item de `optionPositions` (schema de
    `store.abrir_call_coberta`/`comprar_put_protecao`) — usa `id`,
    `underlying`, `strike`, `expiration`, `qty`, `side`, `lastro`.
    `chain`: já buscada pelo CHAMADOR, keyed ao MESMO `underlying`+
    `expiration` da posição (mesmo padrão de `options_lastreada_fechar` em
    `main.py`).

    Devolve `{"proposta": <dict|None>, "motivo": <str>}` no MESMO shape de
    `propor()` — sucesso tem `motivo` == `tipo`; qualquer ausência
    (cadeia degradada, contrato sumiu da cadeia, sem prêmio válido) sempre
    `"degradado"` (CLAUDE.md princípio 4: nunca inventar prêmio, mesmo já
    sabendo qual é o contrato)."""
    if not isinstance(chain, dict) or chain.get("providerStatus") != "ok":
        return {"proposta": None, "motivo": "degradado"}
    if not isinstance(pos_opcao, dict):
        return {"proposta": None, "motivo": "degradado"}

    contract_symbol = pos_opcao.get("id")
    contrato = next(
        (c for c in [*(chain.get("calls") or []), *(chain.get("puts") or [])]
         if c.get("contractSymbol") == contract_symbol),
        None,
    )
    if not contrato:
        return {"proposta": None, "motivo": "degradado"}

    premio = contrato.get("lastPrice")
    if not isinstance(premio, (int, float)) or premio <= 0:
        return {"proposta": None, "motivo": "degradado"}

    qty_total = int(pos_opcao.get("qty") or 0)
    contratos = qty_total // 100
    if contratos < 1:
        return {"proposta": None, "motivo": "degradado"}

    # `side` só é gravado como "vendida" (abrir_call_coberta) ou "comprada"
    # (comprar_put_protecao) — binário seguro por construção do schema
    # (server/app/store.py), nunca um terceiro valor.
    underlying = pos_opcao.get("underlying")
    tipo = "call_coberta" if pos_opcao.get("side") == "vendida" else "put_protecao"

    expiration = pos_opcao.get("expiration") or chain.get("expiration")
    dias = _dias_ate(expiration, hoje)

    qty_acoes = contratos * 100
    premio_total = round(premio * qty_acoes, 2)
    strike = pos_opcao.get("strike")
    liq = liquidity_score(contrato.get("volume"), contrato.get("openInterest"), contrato.get("bid"), contrato.get("ask"))

    dados = {
        "n": str(contratos), "ticker": underlying, "strike": skill_ref.num_br(strike),
        "premioTotal": skill_ref.num_br(premio_total), "qtyAcoes": str(qty_acoes),
    }
    manchete = skill_ref.opcoes_lastreadas_txt(modo, tipo, **dados)
    didatica = skill_ref.opcoes_lastreadas_txt("educacional", tipo, **dados)

    lastro = pos_opcao.get("lastro") or {}
    qty_livre_val = lastro.get("qty", qty_acoes)

    proposta = {
        "tipo": tipo,
        "contractSymbol": contract_symbol,
        "optionType": contrato.get("optionType"),
        "strike": strike,
        "expiration": expiration,
        "diasParaVencimento": dias,
        "contratos": contratos,
        "qtyAcoes": qty_acoes,
        "premioUnitario": round(premio, 2),
        "premioTotal": premio_total,
        "lastro": {"t": underlying, "qtyLivre": qty_livre_val},
        "liquidez": {"score": liq["score"], "label": _label_liquidez(liq["score"])},
        "manchete": manchete,
        "didatica": didatica,
        "chips": [
            {"k": "prazo", "v": f"{dias} dias" if dias is not None else "—"},
            {"k": "strike", "v": f"R$ {skill_ref.num_br(strike)}"},
            {"k": "prêmio", "v": f"R$ {skill_ref.num_br(premio)}"},
            {"k": "liquidez", "v": _label_liquidez(liq["score"])},
        ],
    }
    return {"proposta": proposta, "motivo": tipo}


def put_sem_lastro(option_positions, positions):
    """IDs das posições de PUT de proteção cujo lastro (ações que protegiam,
    registradas na abertura) excede a posição ATUAL de ações do mesmo ticker
    — ou cuja posição sumiu inteiramente. Valor DERIVADO na leitura; proibido
    persistir um campo espelho (mesma razão de `caixa_reservado` ser
    calculado, não guardado — `store.py`).

    A put NUNCA é fechada automaticamente por isso (CLAUDE.md princípio 4:
    nunca inventar ação): o motor só sinaliza o estado; quem decide fechar é
    o usuário."""
    out = []
    for op in option_positions or []:
        if not isinstance(op, dict) or op.get("side") != "comprada":
            continue
        lastro = op.get("lastro")
        if not isinstance(lastro, dict):
            continue
        t = lastro.get("t")
        qty_lastro = int(lastro.get("qty") or 0)
        pos_acao = next((p for p in (positions or []) if p.get("t") == t), None)
        qty_atual = int(pos_acao.get("qty") or 0) if pos_acao else 0
        if qty_lastro > qty_atual:
            out.append(op.get("id"))
    return out
