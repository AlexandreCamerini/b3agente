"""Motor puro de proposta de opção lastreada (Fase 14, Plano 03).

Módulo PURO — sem rede, sem banco, sem LLM, sem leitura de relógio interna
(`hoje` entra por argumento), mesma disciplina de `setups.py`/`indicators.py`.

A ÚNICA fonte da MANCHETE é `skill_ref.opcoes_lastreadas_txt` — este módulo
escolhe O QUE propor (contrato, quantidade, prêmio, motivo de ausência); o
TEXTO vem sempre de lá (guardrail CVM: a IA explica, nunca substitui a
manchete do motor determinístico).
"""
import datetime as dt

from . import opcoes_motor, skill_ref, store
from .options_quant import liquidity_score

# Prazo elegível: cadeia carregada traz um vencimento só — escolher outro é
# papel da cadeia expansível, não da proposta.
_PRAZO_MIN_DIAS = 15
_PRAZO_MAX_DIAS = 60


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


def _propor_collar(underlying, chain, spot, contrato_put, posicao, cash, modo, hoje, dias, qty_livre_val):
    """Trava protetora (collar): vende 1 call OTM (mesma régua do ramo
    `call_coberta` — `opcoes_motor.rastrear`, liquidez >= 40, strike acima do
    spot) + a put de proteção que `propor()` já escolheu (recebida por
    parâmetro, NUNCA re-selecionada aqui — reselecionar duplicaria a régua e
    poderia devolver uma put diferente da que gerou o gatilho).

    Devolve `None` em qualquer porta fechada (sem call líquida, custo líquido
    não cabe no caixa disponível) — `propor()` cai no `caixa_insuficiente` de
    sempre quando isto acontece; nunca uma exceção, nunca uma proposta
    incompleta."""
    selecionados = opcoes_motor.rastrear(chain, {
        "tipo": "call", "referencia": spot, "relacao": "acima",
        "criterio": "min", "n": 1,
    })
    contrato_call = selecionados[0] if selecionados else None
    if not contrato_call:
        return None

    # Pernas de opção, por unidade do objeto (mesma convenção "quantidade=1"
    # do resto do módulo).
    pernas_opcao = [
        opcoes_motor.perna_de_contrato(contrato_call, "venda", quantidade=1),
        opcoes_motor.perna_de_contrato(contrato_put, "compra", quantidade=1),
    ]
    # Teto de contratos sai do custo líquido calculado por `avaliar()`, nunca
    # de `premio_put - premio_call` escrito à mão: uma segunda aritmética do
    # mesmo número é exatamente a duplicação que esta fase existe para
    # eliminar. `custo_unit <= 0` (crédito ou neutro) financia o próprio
    # collar — o teto vem só do lastro; `custo_unit > 0` (débito) soma o
    # teto do caixa disponível.
    caixa_pernas = opcoes_motor.avaliar(pernas_opcao)
    custo_unit = caixa_pernas["custo_liquido"]
    if custo_unit <= 0:
        contratos = qty_livre_val // 100
    else:
        contratos = min(qty_livre_val // 100, int(cash // (100 * custo_unit)))
    if contratos < 1:
        return None

    qty_acoes = contratos * 100
    # UMA avaliação para as 3 pernas — é esta chamada que prova LIB-03: o
    # mesmo `perfil_da_estrutura` que serve 2 pernas (venda coberta, put
    # isolada) serve 3 sem uma linha de aritmética nova.
    pernas = [opcoes_motor.perna_de_acao(underlying, spot, quantidade=1), *pernas_opcao]
    estrutura = opcoes_motor.avaliar(pernas)

    strike_call = contrato_call.get("strike")
    strike_put = contrato_put.get("strike")

    # A estrutura só é tão negociável quanto a sua perna PIOR — exibir a
    # melhor seria otimismo embutido no dado.
    liq_call = liquidity_score(contrato_call.get("volume"), contrato_call.get("openInterest"),
                                contrato_call.get("bid"), contrato_call.get("ask"))
    liq_put = liquidity_score(contrato_put.get("volume"), contrato_put.get("openInterest"),
                               contrato_put.get("bid"), contrato_put.get("ask"))
    pior = liq_call if liq_call["score"] <= liq_put["score"] else liq_put

    dados = {
        "n": str(contratos), "ticker": underlying,
        "strikeCall": skill_ref.num_br(strike_call), "strikePut": skill_ref.num_br(strike_put),
        "qtyAcoes": str(qty_acoes),
    }
    manchete = skill_ref.opcoes_lastreadas_txt(modo, "collar", **dados)
    # `didatica` = a mesma frase no modo educacional, SEMPRE presente — nunca
    # recomputada por outro caminho (mesmo padrão do resto do módulo).
    didatica = skill_ref.opcoes_lastreadas_txt("educacional", "collar", **dados)

    caixa = {
        "custoLiquidoUnitario": custo_unit,
        "custoLiquidoTotal": round(custo_unit * qty_acoes, 2),
        "fluxo": caixa_pernas["fluxo"],
    }
    chip_caixa_chave = "crédito líquido" if caixa["fluxo"] == "credito" else "custo líquido"

    return {
        "tipo": "collar",
        # O collar não tem CONTRATO único nem PRÊMIO único — preencher
        # qualquer um destes com o valor de UMA das pernas faria uma
        # estrutura de duas pernas se passar por operação de uma perna só
        # para qualquer consumidor que case por `contractSymbol` (é assim
        # que o front casa proposta com posição, web/src/App.jsx:3216-3217).
        # `None` com o valor real em `pernasContratos`/`caixa` é a aplicação
        # direta da regra "null nunca 0.0" do repositório.
        "contractSymbol": None,
        "optionType": None,
        "strike": None,
        "premioUnitario": None,
        "premioTotal": None,
        "strikeCall": strike_call,
        "strikePut": strike_put,
        "pernasContratos": [
            {"contractSymbol": contrato_call.get("contractSymbol"), "optionType": contrato_call.get("optionType"),
             "lado": "venda", "strike": strike_call, "premioUnitario": round(float(contrato_call.get("lastPrice") or 0), 2)},
            {"contractSymbol": contrato_put.get("contractSymbol"), "optionType": contrato_put.get("optionType"),
             "lado": "compra", "strike": strike_put, "premioUnitario": round(float(contrato_put.get("lastPrice") or 0), 2)},
        ],
        "expiration": chain.get("expiration"),
        "diasParaVencimento": dias,
        "contratos": contratos,
        "qtyAcoes": qty_acoes,
        "lastro": {"t": underlying, "qtyLivre": qty_livre_val},
        "liquidez": {"score": pior["score"], "label": _label_liquidez(pior["score"])},
        "manchete": manchete,
        "didatica": didatica,
        "chips": [
            {"k": "prazo", "v": f"{dias} dias"},
            {"k": "strikes", "v": f"call R$ {skill_ref.num_br(strike_call)} / put R$ {skill_ref.num_br(strike_put)}"},
            {"k": chip_caixa_chave, "v": f"R$ {skill_ref.num_br(abs(caixa['custoLiquidoTotal']))}"},
            {"k": "liquidez", "v": _label_liquidez(pior["score"])},
        ],
        "estrutura": estrutura,
        "caixa": caixa,
        "precoObjeto": round(float(spot), 2),
    }


def propor(underlying, chain, spot, plano, posicao, cash, modo, hoje, *, multiperna=False):
    """Proposta de estrutura(s) (venda coberta, put de proteção e/ou collar) a
    partir da leitura técnica do ativo-lastro e do lastro livre — ou a
    ausência explicada por um motivo nomeado (CLAUDE.md princípio 4: nunca
    inventar proposta; toda porta fechada devolve `proposta=None` com
    `motivo`, SEM a chave `candidatos`).

    `multiperna` (Fase 16, Plano 03, LIB-03) é negociação de capacidade do
    CLIENTE, não uma meia-entrega: default `False` preserva byte a byte o
    comportamento de antes desta fase. O cliente que sabe exibir e aceitar
    uma estrutura de MAIS de uma perna pede `multiperna=True` e pode receber
    um collar (call vendida + put comprada) no lugar de `caixa_insuficiente`,
    ou COEXISTINDO com a put isolada (Fase 19, MULTI-01, ver `candidatos`
    abaixo). Sem o pedido explícito, receber um collar produziria um CTA que
    abriria METADE da estrutura — o front publicado hoje (`PropostaLastreada`
    em web/src/App.jsx:3012-3068) casa proposta com posição por
    `contractSymbol` e executa por uma perna só. O Plano 16-04 liga este
    parâmetro na rota; a Fase 17/18 ligam no cliente.

    RETORNO POSITIVO (Fase 19, MULTI-01):
    `{"proposta": <dict>, "motivo": <str>, "candidatos": [<dict>, ...]}` — a
    lista `candidatos` tem 1 ou 2 entradas na MESMA forma de `proposta` de
    sempre; quando há duas, a ordem é SEMPRE `["put_protecao", "collar"]`.
    `proposta` é SEMPRE `candidatos[0]` (nunca recalculado à parte) e
    `motivo` é SEMPRE `candidatos[0]["tipo"]` — a regra que faz "o card
    exibido é o que o usuário aceita" verificável, não só uma convenção
    verbal.

    RETORNO NEGATIVO (toda porta fechada — degradado/sem_lastro/sem_setup/
    sem_contrato_liquido/sem_vencimento_elegivel/caixa_insuficiente):
    `{"proposta": None, "motivo": <str>}`, SEM a chave `candidatos`. Isto não
    é esquecimento: ~15 guardiões em `server/tests/test_opcoes_*.py` fazem
    igualdade EXATA de dict nesses retornos — acrescentar `"candidatos": []`
    quebraria todos por nada. Consumidor lê sempre com
    `resultado.get("candidatos", [])`, nunca `resultado["candidatos"]`."""
    if not isinstance(chain, dict) or chain.get("providerStatus") != "ok":
        return {"proposta": None, "motivo": "degradado"}
    if not isinstance(posicao, dict) or store.qty_livre(posicao) < 100:
        return {"proposta": None, "motivo": "sem_lastro"}

    # Guarda de preço do objeto: `_spot_from_chain_or_quote`
    # (server/app/options_api.py:30-36) devolve `Optional[float]` — hoje um
    # `spot=None` estoura `TypeError` na comparação
    # `(c.get("strike") or 0) > spot` e o `except Exception` da rota
    # (server/app/main.py:2404) converte em `degradado`. Depois da migração
    # para `opcoes_motor.rastrear()`, `referencia` não-numérica é IGNORADA
    # (opcoes_motor.py:95-98) — o motor devolveria o contrato de menor
    # strike da cadeia inteira em silêncio, e trocar uma exceção por uma
    # seleção errada viola o princípio 4 do CLAUDE.md (nunca inventar valor
    # quando o dado falhou). Guarda explícita aqui preserva o mesmo motivo
    # de saída de hoje (`degradado`) sem depender do acidente do TypeError.
    if not isinstance(spot, (int, float)) or isinstance(spot, bool) or spot <= 0:
        return {"proposta": None, "motivo": "degradado"}

    # Fase 19, MULTI-01: `colar` precisa existir nos DOIS branches positivos
    # (put_protecao e call_coberta) — só o primeiro pode preenchê-lo, mas a
    # montagem final de `candidatos` (no fim da função) lê a variável sem
    # saber qual branch foi tomado.
    colar = None
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
        selecionados = opcoes_motor.rastrear(chain, {
            "tipo": "call", "referencia": spot, "relacao": "acima",
            "criterio": "min", "n": 1,
        })
    else:
        # Desempate de strike mudou com a migração: `max(validos,
        # key=strike)` (implementação anterior) devolvia o PRIMEIRO strike
        # máximo na ordem da cadeia; `rastrear(criterio="max")` ordena
        # ascendente e devolve `list(reversed(...))[:n]`
        # (opcoes_motor.py:105-108) — o ÚLTIMO empatado. Cadeia real da B3
        # não repete strike no mesmo tipo e vencimento; a régua única (fonte
        # compartilhada com venda coberta e o futuro collar) vale mais que
        # preservar o desempate arbitrário anterior.
        selecionados = opcoes_motor.rastrear(chain, {
            "tipo": "put", "referencia": spot, "relacao": "abaixo_ou_igual",
            "criterio": "max", "n": 1,
        })
    # NÃO passar `liquidez_minima`: o default de `rastrear()` já é
    # `opcoes_motor.LIQUIDEZ_MINIMA` — repassar aqui recriaria o
    # acoplamento local que esta migração remove.
    contrato = selecionados[0] if selecionados else None
    if not contrato:
        return {"proposta": None, "motivo": "sem_contrato_liquido"}

    qty_livre_val = store.qty_livre(posicao)
    contratos = qty_livre_val // 100
    premio = float(contrato.get("lastPrice") or 0)
    if tipo == "put_protecao":
        contratos = min(contratos, int(cash // (100 * premio)) if premio > 0 else 0)
        # Fase 19, MULTI-01: a regra mudou de "collar só como FALLBACK do
        # caixa insuficiente" para "collar tentado sempre que a leitura é de
        # proteção, incondicional ao caixa da put isolada" — só assim os dois
        # candidatos podem coexistir quando os dois cabem (put E collar), em
        # vez do motor escolher um e esconder o outro do usuário. A chamada
        # fica FORA do `if contratos < 1` de propósito: quando a put cabe
        # (`contratos >= 1`), o fluxo segue para montar `proposta` normal e
        # `colar` (se não `None`) entra como segundo candidato lá embaixo.
        # `_propor_collar` continua pura: recebe a put JÁ selecionada por
        # parâmetro, nunca reseleciona.
        if multiperna:
            colar = _propor_collar(
                underlying, chain, spot, contrato, posicao, cash, modo, hoje, dias, qty_livre_val)
        if contratos < 1:
            # Julgamento de produto herdado da Fase 16 (16-CONTEXT.md,
            # decisão tomada com autonomia concedida): sem caixa para a put
            # isolada, o collar (que se autofinancia com o prêmio da call
            # vendida) é a única saída além de "caixa insuficiente" — em vez
            # de só devolver isso sem alternativa. `colar` já foi tentado
            # acima (incondicional); aqui só decide o que RETORNAR quando a
            # put não coube. `_propor_collar` devolvendo `None` (sem call
            # líquida acima do spot, ou débito que também não cabe no caixa)
            # cai no `caixa_insuficiente` de sempre, logo abaixo.
            if colar is not None:
                return {"proposta": colar, "motivo": "collar", "candidatos": [colar]}
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

    # Perna de opção, por unidade do objeto (a mesma convenção "quantidade=1"
    # de `opcoes_payoff` — o lote de `qty_acoes` multiplica só na hora de
    # apresentar o caixa, nunca dentro da perna).
    pernas_opcao = [opcoes_motor.perna_de_contrato(
        contrato, "venda" if tipo == "call_coberta" else "compra", quantidade=1)]

    # A perna ACAO entra SEMPRE no cálculo de risco: sem ela,
    # `perfil_da_estrutura` vê só a call vendida (inclinação -1) e classifica
    # uma venda COBERTA como perda ilimitada (opcoes_payoff.py:198-204) —
    # apresentar isso ao usuário de um produto educacional seria descrever
    # risco errado. `quantidade=1` nas duas pernas mantém a convenção "por
    # unidade do objeto" que `opcoes_payoff` declara em `unidade`.
    pernas = [opcoes_motor.perna_de_acao(underlying, spot, quantidade=1), *pernas_opcao]
    # Nenhum try/except aqui: `rastrear()` só devolve contrato com `lastPrice`
    # numérico > 0 (opcoes_motor.py:38-43) e a guarda de spot acima já
    # garante o argumento de `perna_de_acao` — um `ValueError` nesta linha
    # seria defeito de programação, não estado de mercado; engolir viraria
    # proposta silenciosamente incompleta.
    estrutura = opcoes_motor.avaliar(pernas)

    # Movimento de CAIXA de hoje é outra pergunta: `estrutura["custo_liquido"]`
    # inclui o preço da ação (numa venda coberta, spot - prêmio ≈ 28,5) — mas
    # a ação JÁ é do usuário, comprada em outra operação. Exibir isso como
    # custo da proposta seria número certo respondendo a pergunta errada.
    # `caixa` avalia só as pernas de opção, isoladas.
    caixa_pernas = opcoes_motor.avaliar(pernas_opcao)

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
        "estrutura": estrutura,
        "caixa": {
            "custoLiquidoUnitario": caixa_pernas["custo_liquido"],
            "custoLiquidoTotal": round(caixa_pernas["custo_liquido"] * qty_acoes, 2),
            "fluxo": caixa_pernas["fluxo"],
        },
        "precoObjeto": round(float(spot), 2),
    }
    # Fase 19, MULTI-01: `candidatos` começa pelo candidato PRIMÁRIO
    # (`proposta`, put_protecao ou call_coberta) e acrescenta `colar` quando
    # ele não é `None` — ordem sempre put_protecao/call_coberta primeiro,
    # collar depois. `proposta`/`motivo` são derivados do candidato primário
    # (`candidatos[0]`), NUNCA recalculados à parte — recalcular à parte
    # poderia divergir do candidato que a UI de fato exibe em destaque.
    candidatos = [proposta]
    if colar is not None:
        candidatos.append(colar)
    return {"proposta": candidatos[0], "motivo": candidatos[0]["tipo"], "candidatos": candidatos}


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
