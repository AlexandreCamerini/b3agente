"""Fase 30, Plano 01 — motor PURO da curadoria das 4 melhores estruturas.
Estendido na Fase 31, Plano 01 (D-04/D-01/D-05/D-06) — ver abaixo.

Módulo PURO — sem rede, sem banco, sem LLM, sem leitura de relógio interna
(`hoje` entra por argumento), mesma disciplina de
`opcoes_motor.py`/`opcoes_lastreadas.py`/`opcoes_payoff.py`.

Dois cercos da Fase 30 foram DELIBERADAMENTE revertidos pela Fase 31 —
reversão deliberada atualiza o guardião com nota, não apaga a história
(mesma disciplina já usada nos testes desta base):

- **Universo (Fase 30/D1 → Fase 31/D-04): SÓ venda coberta virou as 4
  estruturas do motor interno.** Put de proteção, collar e opção a
  descoberto agora entram neste módulo — a Fase 30 excluiu essas estruturas
  de propósito (misturar "proteção" com "gerar receita" no mesmo ranking de
  risco mínimo não fazia sentido matemático); a Fase 31 amplia o universo de
  propósito, com a MESMA fórmula de ranking para as 4 mesmo sabendo que
  put/collar rankeiam estruturalmente mal nela (Fase 31/D-06 — não é bug,
  não filtre). A opção a descoberto só existe quando `permitir_a_descoberto`
  é `True` (Fase 31/D-05, ver `candidatos_da_posicao` abaixo) — a Fase 29 e
  seu gate de EXECUÇÃO (`store.buy_option`) não mudam.
- **Janelas (Fase 30/D3 → Fase 31/D-01): vencimento único por CHAMADA,
  teto de 2 vencimentos por posição no CHAMADOR.** `candidatos_da_posicao`
  continua recebendo UMA `chain` por chamada — nada muda aqui, este módulo
  continua puro e alheio a rede. O que muda é fora deste arquivo: o chamador
  (`server/app/main.py`, Plano 31-02) passa a invocar esta função até
  `VENCIMENTOS_POR_POSICAO` (2) vezes por posição elegível, uma por
  vencimento buscado, em vez de uma vez só — e é o CHAMADOR que paga o custo
  de rede declarado (30-CONTEXT achado 3; 31-CONTEXT D-01/D-03), nunca este
  módulo.

Guardrail não-negociável (CLAUDE.md princípio 5 + 30-CONTEXT): a escolha das
4 melhores é 100% aritmética de `opcoes_motor.rastrear()`/`avaliar()`, nunca
de LLM. `rankear()` é a única função que decide ordem; `exigir_ranking()`
torna essa regra comportamento do código, não promessa de comentário — a
camada de narração (`narrativa_user`) é estruturalmente incapaz de receber
um pool não rankeado.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from . import opcoes_motor, skill_ref, store
from .opcoes_lastreadas import _PRAZO_MAX_DIAS, _PRAZO_MIN_DIAS, _bloco_liquidez, _dias_ate
from .options_quant import LIQUIDEZ_NEGOCIAVEL, liquidity_score

# TOPO: quantas estruturas a UI mostra ("as 4 melhores" — pedido original).
TOPO = 4
# STRIKES_POR_POSICAO: quantos strikes candidatos `rastrear()` devolve por
# posição elegível, dentro do vencimento único da cadeia (D3 da Fase 30,
# ainda válido: continua sendo "strikes dentro de UMA cadeia", só que agora
# o chamador pode repetir a chamada para até 2 cadeias/vencimentos, Fase 31/
# D-01).
STRIKES_POR_POSICAO = 5
# PISO_LIQUIDEZ: D5 — reusa o piso já em produção, nunca um corte novo
# inventado só para este ranking. Importado de `.options_quant`, nunca o
# literal 55, para que uma recalibração futura (como a quick 260908-ldg já
# fez uma vez) propague sozinha.
PISO_LIQUIDEZ = LIQUIDEZ_NEGOCIAVEL
# VENCIMENTOS_POR_POSICAO: Fase 31/D-01 — teto FIXO de vencimentos varridos
# por posição elegível. Cada vencimento a mais é 1 chamada de
# `get_options_chain` por posição, contra o orçamento medido do mydata
# (60/min · 2.000/dia, `docs/MEDICAO-Mydata-2026-08-27.md`). Quem subir esta
# constante paga rede por posição × vencimento — não é parâmetro de ajuste
# fino, é decisão de custo de produto (mesma disciplina de
# `STRIKES_POR_POSICAO`/`PISO_LIQUIDEZ` acima). Usada como default de
# `proximos_vencimentos` abaixo; o LOOP que multiplica chamadas por
# vencimento vive no chamador (main.py, Plano 31-02), não aqui.
VENCIMENTOS_POR_POSICAO = 2
# CONTRATOS_A_DESCOBERTO: a opção a descoberto não tem lastro contra o qual
# dimensionar (Fase 31/D-05) — a varredura é DESCOBERTA, não execução: 1
# contrato = 100 unidades do objeto, fixo. A checagem de caixa acontece na
# execução (`store.buy_option`), nunca aqui.
CONTRATOS_A_DESCOBERTO = 1
# TIPOS: universo fechado de estruturas desta fase (Fase 31/D-04).
TIPOS = ("call_coberta", "put_protecao", "collar", "opcao_a_descoberto")


# ─────────────────────────────────────────────────────────────────────────
# premio_liquido_unitario() / id_candidato() / proximos_vencimentos() —
# funções puras novas da Fase 31, Plano 01
# ─────────────────────────────────────────────────────────────────────────

def premio_liquido_unitario(pernas_opcao: list[dict[str, Any]]) -> float:
    """Fluxo de caixa líquido das pernas de OPÇÃO de uma estrutura, por
    unidade do objeto — positivo quando o usuário RECEBE (crédito), negativo
    quando PAGA (débito).

    Recebe SÓ as pernas de opção (nunca a perna de ação — incluí-la somaria
    o preço do papel ao "prêmio", que é um número de opção, não de carteira).
    É reuso do número que `opcoes_motor.avaliar` já calcula
    (`custo_liquido`: >0 débito, <0 crédito — ver `opcoes_payoff.
    custo_liquido`), o mesmo padrão que `_propor_collar` já usa
    (`caixa_pernas = avaliar(pernas_opcao)`), não uma segunda aritmética.

    Prêmio NEGATIVO é resultado ESPERADO em put de proteção, em collar de
    débito e em opção a descoberto (compra a seco) — Fase 31/D-06 exige que
    esses candidatos continuem no ranking, rankeados naturalmente mal pela
    MESMA fórmula (prêmio ÷ perda máxima), nunca filtrados por prêmio
    negativo.
    """
    return round(-opcoes_motor.avaliar(pernas_opcao)["custo_liquido"], 2)


def id_candidato(
    tipo: str,
    ticker: str,
    expiration: Any,
    contract_symbol: str | None = None,
    *,
    strike_call: Any = None,
    strike_put: Any = None,
) -> str:
    """Identidade estável e TOTAL de um candidato de curadoria.

    Existe por dois motivos nomeados: (1) o collar não tem `contractSymbol`
    único (duas pernas — `opcoes_lastreadas.py:145-156` já explica por que
    preencher com uma das pernas seria mentira), e sem um último critério
    TOTAL dois collars empatados em `razao`/`premioUnitario` voltariam em
    ordem de chegada, não determinística (ver `rankear`); (2) o front
    precisa de uma chave de React estável (`web/src/App.jsx:4191`, hoje
    `key={item.contractSymbol}`, que colide em `null`).
    """
    sufixo = contract_symbol or f"{strike_call}/{strike_put}"
    return f"{tipo}:{ticker}:{expiration}:{sufixo}"


def proximos_vencimentos(
    expirations: Any, hoje: Any, *, teto: int = VENCIMENTOS_POR_POSICAO
) -> list[str]:
    """Até `teto` vencimentos ESTRITAMENTE futuros de `expirations` (lista
    ISO da cadeia ADR-004), ordenados crescente, sem repetição.

    Mesma tolerância a item malformado da escolha de vencimento do provedor
    mydata (`_primeiro_vencimento_futuro`, módulo do provider de mercado —
    citado aqui só pelo NOME da função, este arquivo não importa camada de
    rede) — `dt.date.fromisoformat` dentro de `try/except (TypeError,
    ValueError): continue` — e `sorted()` defensivo pelo mesmo motivo (D-05
    da quick 260914-b6p: a ordem da lista é contrato de terceiro não
    documentado). Entrada que não é lista devolve `[]`. Função PURA: `hoje`
    entra por argumento, nunca lê relógio.
    """
    if not isinstance(expirations, list):
        return []

    candidatos: list[tuple[dt.date, str]] = []
    for exp in expirations:
        try:
            d = dt.date.fromisoformat(exp)
        except (TypeError, ValueError):
            continue
        if d > hoje:
            candidatos.append((d, exp))
    candidatos.sort(key=lambda item: item[0])
    return [exp for _, exp in candidatos[:teto]]


# ─────────────────────────────────────────────────────────────────────────
# candidatos_da_posicao() — enumeração de strikes sobre uma cadeia em memória
# ─────────────────────────────────────────────────────────────────────────

def candidatos_da_posicao(
    underlying: str,
    chain: Any,
    spot: Any,
    posicao: Any,
    modo: str,
    hoje: Any,
    *,
    n: int = STRIKES_POR_POSICAO,
    permitir_a_descoberto: bool = False,
) -> list[dict[str, Any]]:
    """Candidatos de curadoria para UMA posição, a partir de UMA cadeia (um
    único vencimento) já buscada em memória. Devolve SEMPRE lista — `[]` em
    toda porta fechada, nunca `None`, nunca exceção (mesma postura de
    `opcoes_motor.rastrear`/`opcoes_lastreadas.propor`).

    Fase 31/D-04 amplia o universo desta função de "só venda coberta"
    (Fase 30/D1) para as 4 estruturas do motor interno — venda coberta, put
    de proteção, collar e opção a descoberto (esta última só quando
    `permitir_a_descoberto=True`, Fase 31/D-05; ver Plano 31-01 Tasks 2/3).
    Todas nascem da MESMA cadeia já buscada, nenhuma chamada de rede nova
    dentro deste módulo — quem varre múltiplos vencimentos é o CHAMADOR
    (Fase 31/D-01, ver docstring do módulo).

    `permitir_a_descoberto` (Fase 31/D-05): default `False` é FAIL-CLOSED
    e proposital — um chamador que esqueça de passar o flag nunca vaza
    oportunidade a descoberto. Este é o primeiro ponto do sistema onde
    `permitirOpcaoADescoberto` é lido no momento da DESCOBERTA (o segundo
    ponto, depois do gate de EXECUÇÃO em `store.buy_option`,
    store.py:815-828). A semântica aqui é PULO SILENCIOSO — sem `raise`,
    sem `registrar_rejeicao`, sem aviso ao usuário — deliberadamente
    diferente do gate de execução, que recusa alto e registra rejeição. Os
    dois comportamentos NÃO devem ser unificados: um é filtro de exibição
    (esta função), o outro é recusa de ordem (`store.buy_option`).

    Portas fechadas, na ordem, espelhando `opcoes_lastreadas.propor`
    (opcoes_lastreadas.py:220-237, 260-262) — mesmos motivos, mesma ordem de
    checagem, para que o comportamento desta fase não divirja em silêncio do
    fluxo de proposta única de hoje:

    - `chain` não é dict, ou `chain.get("providerStatus") != "ok"`.
    - `posicao` não é dict, ou `store.qty_livre(posicao) < 100` (lote livre
      insuficiente para 1 contrato).
    - `spot` não numérico, `bool` (subclasse de `int`, precisa ser excluída
      explicitamente) ou <= 0.
    - `dias = _dias_ate(chain.get("expiration"), hoje)` é `None` ou fora de
      `_PRAZO_MIN_DIAS..._PRAZO_MAX_DIAS`.

    Deliberadamente NÃO há porta de setup/plano técnico aqui, ao contrário de
    `propor()` (que exige `decisao`/`lado` e devolve `sem_setup` quando o
    motor técnico lê alta). Fase 30/D1 define elegibilidade como "comprado,
    com lote livre >= 100 ações", e só — é decisão de produto fechada, não
    descuido, e a Fase 31 não reabre isso. Consequência nomeada: uma posição
    que o motor técnico lê como ALTA PODE aparecer neste ranking mesmo que
    não apareceria na proposta única da mesma tela (que recusaria com
    `sem_setup`). Não "corrija" isso adicionando um gate técnico aqui.
    """
    if not isinstance(chain, dict) or chain.get("providerStatus") != "ok":
        return []
    if not isinstance(posicao, dict) or store.qty_livre(posicao) < 100:
        return []
    if not isinstance(spot, (int, float)) or isinstance(spot, bool) or spot <= 0:
        return []

    dias = _dias_ate(chain.get("expiration"), hoje)
    if dias is None or not (_PRAZO_MIN_DIAS <= dias <= _PRAZO_MAX_DIAS):
        return []

    # `liquidez_minima` EXPLÍCITO é o ponto de D5: sem ele, `rastrear` faz
    # uma SEGUNDA passada em `LIQUIDEZ_DIFICIL` (opcoes_motor.py:104-109)
    # quando a primeira passada NEGOCIÁVEL não acha nada — um contrato
    # DIFÍCIL entraria num ranking que o usuário vai ler como "as 4 melhores
    # para gerar receita". O piso desta fase é NEGOCIÁVEL e só; nunca herdar
    # o fallback de duas passadas de `rastrear()`.
    selecionados = opcoes_motor.rastrear(chain, {
        "tipo": "call", "referencia": spot, "relacao": "acima",
        "criterio": "min", "n": n, "liquidez_minima": PISO_LIQUIDEZ,
    })
    if not selecionados:
        return []

    qty_livre_val = store.qty_livre(posicao)
    contratos = qty_livre_val // 100
    qty_acoes = contratos * 100

    candidatos: list[dict[str, Any]] = []
    for contrato in selecionados:
        try:
            perna_opcao = opcoes_motor.perna_de_contrato(contrato, "venda", quantidade=1)
            pernas = [opcoes_motor.perna_de_acao(underlying, spot, quantidade=1), perna_opcao]
            estrutura = opcoes_motor.avaliar(pernas)
        except ValueError:
            # Um contrato defeituoso individual (prêmio ausente, optionType
            # inválido) não pode derrubar a curadoria da carteira inteira —
            # os outros candidatos ainda são úteis.
            continue

        perda_maxima = estrutura.get("perda_maxima")
        # Razão sobre zero não é "razão infinita", é razão INDEFINIDA:
        # publicar `inf`/`None` como se fosse mérito (quanto menor a perda,
        # "melhor" a razão) violaria o princípio 4 do CLAUDE.md — nunca
        # inventar valor quando o dado de risco não sustenta o cálculo.
        if not isinstance(perda_maxima, (int, float)) or isinstance(perda_maxima, bool) or perda_maxima <= 0:
            continue

        # `premio_liquido_unitario` sobre SÓ a perna de opção dá exatamente
        # `+lastPrice` (crédito da venda) — idêntico ao `round(premio, 2)`
        # de antes desta fase, agora via a função reusável pelas 4
        # estruturas (Fase 31, Plano 01, Task 1c).
        premio_unitario = premio_liquido_unitario([perna_opcao])
        premio_total = round(premio_unitario * qty_acoes, 2)
        razao = round(premio_unitario / perda_maxima, 6)

        liq = liquidity_score(contrato.get("volume"), contrato.get("openInterest"),
                               contrato.get("bid"), contrato.get("ask"))
        strike = contrato.get("strike")

        dados = {
            "n": str(contratos), "ticker": underlying, "strike": skill_ref.num_br(strike),
            "premioTotal": skill_ref.num_br(premio_total), "qtyAcoes": str(qty_acoes),
        }
        # `manchete`/`didatica` vêm SÓ de `skill_ref.opcoes_lastreadas_txt` —
        # este módulo não compõe frase nova (guardrail CVM: a IA explica,
        # nunca substitui a manchete do motor determinístico).
        manchete = skill_ref.opcoes_lastreadas_txt(modo, "call_coberta", **dados)
        didatica = skill_ref.opcoes_lastreadas_txt("educacional", "call_coberta", **dados)

        candidatos.append({
            "tipo": "call_coberta",
            "ticker": underlying,
            "contractSymbol": contrato.get("contractSymbol"),
            "optionType": contrato.get("optionType"),
            "strike": strike,
            "expiration": chain.get("expiration"),
            "diasParaVencimento": dias,
            "contratos": contratos,
            "qtyAcoes": qty_acoes,
            "premioUnitario": premio_unitario,
            "premioTotal": premio_total,
            "liquidez": _bloco_liquidez(contrato, liq, modo),
            "estrutura": estrutura,
            "razao": razao,
            "manchete": manchete,
            "didatica": didatica,
            "precoObjeto": round(float(spot), 2),
            "idCandidato": id_candidato("call_coberta", underlying, chain.get("expiration"),
                                         contrato.get("contractSymbol")),
        })

    # ─────────────────────────────────────────────────────────────────
    # put_protecao / collar — Fase 31, Plano 01, Task 2 (D-04). Segunda
    # seleção em memória, ZERO chamada de rede nova: mesma cadeia já em
    # mãos. `liquidez_minima` EXPLÍCITO pelo MESMO motivo (D5) do ramo das
    # calls acima — sem ele, `rastrear` cairia para a segunda passada
    # DIFÍCIL, e um contrato DIFÍCIL entraria num ranking lido como "as
    # melhores oportunidades". Nenhuma porta nova: `selecionados_put` vazio
    # simplesmente não gera estes dois ramos, os `call_coberta` de cima já
    # saíram normalmente.
    selecionados_put = opcoes_motor.rastrear(chain, {
        "tipo": "put", "referencia": spot, "relacao": "abaixo_ou_igual",
        "criterio": "max", "n": n, "liquidez_minima": PISO_LIQUIDEZ,
    })

    for contrato_put in selecionados_put:
        try:
            perna_opcao = opcoes_motor.perna_de_contrato(contrato_put, "compra", quantidade=1)
            pernas = [opcoes_motor.perna_de_acao(underlying, spot, quantidade=1), perna_opcao]
            estrutura = opcoes_motor.avaliar(pernas)
        except ValueError:
            # Mesma tolerância a contrato defeituoso individual do ramo
            # call_coberta acima — um `optionType` corrompido não derruba a
            # curadoria da carteira inteira.
            continue

        perda_maxima = estrutura.get("perda_maxima")
        if not isinstance(perda_maxima, (int, float)) or isinstance(perda_maxima, bool) or perda_maxima <= 0:
            continue

        # Débito da compra: NEGATIVO por desenho (D-06) — nunca filtrado.
        premio_unitario = premio_liquido_unitario([perna_opcao])
        premio_total = round(premio_unitario * qty_acoes, 2)
        razao = round(premio_unitario / perda_maxima, 6)

        liq = liquidity_score(contrato_put.get("volume"), contrato_put.get("openInterest"),
                               contrato_put.get("bid"), contrato_put.get("ask"))
        strike = contrato_put.get("strike")

        # A frase canônica de put_protecao diz "pagaria R$ {premioTotal}" —
        # o marcador recebe o MÓDULO (nunca "pagaria R$ -65,00"); o sinal
        # vive só no campo JSON premioUnitario/premioTotal, não na frase.
        # Assimetria deliberada, não bug.
        dados = {
            "n": str(contratos), "ticker": underlying, "strike": skill_ref.num_br(strike),
            "premioTotal": skill_ref.num_br(abs(premio_total)), "qtyAcoes": str(qty_acoes),
        }
        manchete = skill_ref.opcoes_lastreadas_txt(modo, "put_protecao", **dados)
        didatica = skill_ref.opcoes_lastreadas_txt("educacional", "put_protecao", **dados)

        candidatos.append({
            "tipo": "put_protecao",
            "ticker": underlying,
            "contractSymbol": contrato_put.get("contractSymbol"),
            "optionType": contrato_put.get("optionType"),
            "strike": strike,
            "expiration": chain.get("expiration"),
            "diasParaVencimento": dias,
            "contratos": contratos,
            "qtyAcoes": qty_acoes,
            "premioUnitario": premio_unitario,
            "premioTotal": premio_total,
            "liquidez": _bloco_liquidez(contrato_put, liq, modo),
            "estrutura": estrutura,
            "razao": razao,
            "manchete": manchete,
            "didatica": didatica,
            "precoObjeto": round(float(spot), 2),
            "idCandidato": id_candidato("put_protecao", underlying, chain.get("expiration"),
                                         contrato_put.get("contractSymbol")),
        })

    # collar — usa SEMPRE `selecionados[0]` (a call OTM de menor strike,
    # mesma régua de `_propor_collar`, opcoes_lastreadas.py:74-78),
    # combinada com CADA put selecionada.
    contrato_call_collar = selecionados[0]
    for contrato_put in selecionados_put:
        try:
            perna_call = opcoes_motor.perna_de_contrato(contrato_call_collar, "venda", quantidade=1)
            perna_put = opcoes_motor.perna_de_contrato(contrato_put, "compra", quantidade=1)
            pernas_opcao = [perna_call, perna_put]
            pernas = [opcoes_motor.perna_de_acao(underlying, spot, quantidade=1), *pernas_opcao]
            estrutura = opcoes_motor.avaliar(pernas)
        except ValueError:
            continue

        perda_maxima = estrutura.get("perda_maxima")
        if not isinstance(perda_maxima, (int, float)) or isinstance(perda_maxima, bool) or perda_maxima <= 0:
            continue

        # Crédito quando a call vale mais que a put, débito no caso
        # contrário — sinal natural, nunca filtrado (D-06).
        premio_unitario = premio_liquido_unitario(pernas_opcao)
        premio_total = round(premio_unitario * qty_acoes, 2)
        razao = round(premio_unitario / perda_maxima, 6)

        strike_call = contrato_call_collar.get("strike")
        strike_put = contrato_put.get("strike")

        liq_call = liquidity_score(contrato_call_collar.get("volume"), contrato_call_collar.get("openInterest"),
                                    contrato_call_collar.get("bid"), contrato_call_collar.get("ask"))
        liq_put = liquidity_score(contrato_put.get("volume"), contrato_put.get("openInterest"),
                                   contrato_put.get("bid"), contrato_put.get("ask"))
        # A estrutura só é tão negociável quanto a sua perna PIOR — exibir a
        # melhor seria otimismo embutido no dado (mesma régua de
        # `_propor_collar`, opcoes_lastreadas.py:113-124).
        if liq_call["score"] <= liq_put["score"]:
            contrato_pior, pior = contrato_call_collar, liq_call
        else:
            contrato_pior, pior = contrato_put, liq_put

        dados = {
            "n": str(contratos), "ticker": underlying,
            "strikeCall": skill_ref.num_br(strike_call), "strikePut": skill_ref.num_br(strike_put),
            "qtyAcoes": str(qty_acoes),
        }
        manchete = skill_ref.opcoes_lastreadas_txt(modo, "collar", **dados)
        didatica = skill_ref.opcoes_lastreadas_txt("educacional", "collar", **dados)

        candidatos.append({
            "tipo": "collar",
            "ticker": underlying,
            # O collar não tem CONTRATO único nem STRIKE único — preencher
            # com o valor de UMA das pernas faria uma estrutura de 2 pernas
            # se passar por operação de 1 perna só (mesma regra de
            # `_propor_collar`, "null nunca 0.0").
            "contractSymbol": None,
            "optionType": None,
            "strike": None,
            "strikeCall": strike_call,
            "strikePut": strike_put,
            "pernasContratos": [
                {"contractSymbol": contrato_call_collar.get("contractSymbol"),
                 "optionType": contrato_call_collar.get("optionType"), "lado": "venda",
                 "strike": strike_call,
                 "premioUnitario": round(float(contrato_call_collar.get("lastPrice") or 0), 2)},
                {"contractSymbol": contrato_put.get("contractSymbol"),
                 "optionType": contrato_put.get("optionType"), "lado": "compra",
                 "strike": strike_put,
                 "premioUnitario": round(float(contrato_put.get("lastPrice") or 0), 2)},
            ],
            "expiration": chain.get("expiration"),
            "diasParaVencimento": dias,
            # Sem gate de caixa aqui, ao contrário de `_propor_collar`:
            # `candidatos_da_posicao` é PURA e não recebe `cash` — a
            # varredura é DESCOBERTA, o caixa é cobrado na execução
            # (`store.abrir_collar`). Não "conserte" adicionando um
            # parâmetro de caixa.
            "contratos": contratos,
            "qtyAcoes": qty_acoes,
            "premioUnitario": premio_unitario,
            "premioTotal": premio_total,
            "liquidez": _bloco_liquidez(contrato_pior, pior, modo),
            "estrutura": estrutura,
            "razao": razao,
            "manchete": manchete,
            "didatica": didatica,
            "precoObjeto": round(float(spot), 2),
            "idCandidato": id_candidato("collar", underlying, chain.get("expiration"), None,
                                         strike_call=strike_call, strike_put=strike_put),
        })

    # ─────────────────────────────────────────────────────────────────
    # opcao_a_descoberto — Fase 31, Plano 01, Task 3 (D-05). Só roda com o
    # flag ligado; reusa `selecionados` (as MESMAS calls OTM do ramo
    # call_coberta) — zero `rastrear()` novo, zero rede nova. Escopo de
    # BUSCA continua sendo a carteira do usuário mesmo sem exigir lastro
    # (D-09): a oportunidade a descoberto nasce sobre os tickers que o
    # usuário já tem, nunca sobre o catálogo B3 inteiro.
    #
    # Escolha registrada (discrição do plano, não decisão nova de produto):
    # a estrutura "a descoberto" desta fase é a COMPRA de call a seco — o
    # caminho que a Fase 29 gateou (`store.buy_option`). Venda de call NUA
    # não entra: `avaliar` devolve `perda_maxima=None` para perda
    # ilimitada, e a porta de `perda_maxima` já existente descartaria o
    # candidato de qualquer jeito — publicar razão sobre perda indefinida
    # violaria o princípio 4 do CLAUDE.md.
    if permitir_a_descoberto:
        for contrato in selecionados:
            try:
                # Sem perna de ação — é exatamente o que "a descoberto"
                # significa: nenhum lastro.
                perna_opcao = opcoes_motor.perna_de_contrato(contrato, "compra", quantidade=1)
                estrutura = opcoes_motor.avaliar([perna_opcao])
            except ValueError:
                continue

            perda_maxima = estrutura.get("perda_maxima")
            if not isinstance(perda_maxima, (int, float)) or isinstance(perda_maxima, bool) or perda_maxima <= 0:
                continue

            contratos_naked = CONTRATOS_A_DESCOBERTO
            qty_acoes_naked = contratos_naked * 100
            # Débito da compra a seco: NEGATIVO por desenho, nunca filtrado
            # (D-06) — é o risco máximo inteiro da estrutura.
            premio_unitario = premio_liquido_unitario([perna_opcao])
            premio_total = round(premio_unitario * qty_acoes_naked, 2)
            razao = round(premio_unitario / perda_maxima, 6)

            liq = liquidity_score(contrato.get("volume"), contrato.get("openInterest"),
                                   contrato.get("bid"), contrato.get("ask"))
            strike = contrato.get("strike")

            # Mesma assimetria sinal-no-campo/módulo-na-frase da put de
            # proteção: a frase canônica diz "pagaria R$ {premioTotal}".
            dados = {
                "n": str(contratos_naked), "ticker": underlying, "strike": skill_ref.num_br(strike),
                "premioTotal": skill_ref.num_br(abs(premio_total)), "qtyAcoes": str(qty_acoes_naked),
            }
            manchete = skill_ref.opcoes_lastreadas_txt(modo, "opcao_a_descoberto", **dados)
            didatica = skill_ref.opcoes_lastreadas_txt("educacional", "opcao_a_descoberto", **dados)

            candidatos.append({
                "tipo": "opcao_a_descoberto",
                "ticker": underlying,
                "contractSymbol": contrato.get("contractSymbol"),
                "optionType": contrato.get("optionType"),
                "strike": strike,
                "expiration": chain.get("expiration"),
                "diasParaVencimento": dias,
                "contratos": contratos_naked,
                "qtyAcoes": qty_acoes_naked,
                "premioUnitario": premio_unitario,
                "premioTotal": premio_total,
                "liquidez": _bloco_liquidez(contrato, liq, modo),
                "estrutura": estrutura,
                "razao": razao,
                "manchete": manchete,
                "didatica": didatica,
                "precoObjeto": round(float(spot), 2),
                "idCandidato": id_candidato("opcao_a_descoberto", underlying, chain.get("expiration"),
                                             contrato.get("contractSymbol")),
            })

    return candidatos


# ─────────────────────────────────────────────────────────────────────────
# rankear() / exigir_ranking() — ordem total, determinística, auditável
# ─────────────────────────────────────────────────────────────────────────

def rankear(candidatos: list[dict[str, Any]], *, topo: int = TOPO) -> list[dict[str, Any]]:
    """As `topo` melhores estruturas, por razão prêmio/perda máxima
    decrescente, com desempate TOTAL e determinístico.

    Chave de ordenação (Fase 31, Plano 01, Task 3 — cresceu de 3 para 4
    critérios): `(-razao, -premioUnitario, contractSymbol, idCandidato)`.
    `contractSymbol` permanece como TERCEIRO critério de propósito — preserva
    byte a byte a ordem que os guardiões da Fase 30 já travaram.
    `idCandidato` entra como QUARTO critério só para desempatar o que antes
    não tinha como desempatar: o collar não tem `contractSymbol` único (Fase
    31/D-04), então dois collars empatados em razão e prêmio ficariam ambos
    com `contractSymbol=None` — sem um quarto critério TOTAL, a ordem entre
    eles voltaria a depender da ordem de chegada. `premioUnitario`/
    `idCandidato` lidos via `.get(...) or <default>` porque os guardiões
    mínimos da Fase 30 (dicts sintéticos de teste) não carregam `idCandidato`
    — nenhum campo novo virou obrigatório.

    Esta chave de ordenação é a ÚNICA fonte da ordem: sem peso configurável,
    sem entrada de usuário, sem qualquer campo vindo de LLM (D2 + princípio 5
    do CLAUDE.md). `rankear` não altera nenhum campo dos candidatos além de
    acrescentar `posicaoNoRanking` (1-based, cópia rasa — os dicts de entrada
    não são mutados).
    """
    ordenados = sorted(candidatos, key=lambda c: (
        -c["razao"], -(c.get("premioUnitario") or 0.0),
        c.get("contractSymbol") or "", c.get("idCandidato") or "",
    ))
    cortados = ordenados[:topo]
    return [{**c, "posicaoNoRanking": i} for i, c in enumerate(cortados, start=1)]


def exigir_ranking(top: Any) -> None:
    """Recusa qualquer coisa que não seja a saída de `rankear`.

    Esta função existe para que a etapa de IA seja INCAPAZ de receber um pool
    não rankeado — o guardrail vira comportamento do código, não promessa de
    comentário (30-CONTEXT, "guardrail não-negociável"). Levanta `ValueError`
    nomeando o defeito quando: `top` não é lista; tem mais de `TOPO` itens;
    algum item não é dict ou não tem `razao` numérica; `posicaoNoRanking` não
    é exatamente `1..len(top)` na ordem; a sequência de `razao` não é
    monotonicamente não-crescente.
    """
    if not isinstance(top, list):
        raise ValueError(f"ranking precisa ser uma lista, veio {type(top).__name__}")
    if len(top) > TOPO:
        raise ValueError(f"ranking tem {len(top)} itens, máximo permitido é {TOPO}")

    razao_anterior = None
    for i, item in enumerate(top, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"item {i} do ranking não é dict")
        razao = item.get("razao")
        if not isinstance(razao, (int, float)) or isinstance(razao, bool):
            raise ValueError(f"item {i} do ranking não tem razao numérica (veio {razao!r})")
        if item.get("posicaoNoRanking") != i:
            raise ValueError(
                f"item {i} do ranking tem posicaoNoRanking={item.get('posicaoNoRanking')!r}, "
                f"esperado {i} (ranking precisa vir na própria ordem, 1..N)")
        if razao_anterior is not None and razao > razao_anterior:
            raise ValueError(
                f"ranking fora de ordem: item {i} tem razao {razao} maior que o anterior {razao_anterior}")
        razao_anterior = razao


# ─────────────────────────────────────────────────────────────────────────
# narrativa_system() / narrativa_user() — prompts da etapa de narração
# ─────────────────────────────────────────────────────────────────────────

def narrativa_system(modo: str) -> str:
    """Prefixo ESTÁVEL por modo (mesmo padrão de
    `assistente.system_prefixo`, server/app/assistente.py:189-196) — nada
    variável (timestamp, id, ticker) aqui dentro: variável invalida o cache
    de prompt em silêncio."""
    regras = "\n".join([
        "# Regras desta narração",
        "A ordem das estruturas já foi decidida por um motor determinístico "
        "(razão prêmio recebido / perda máxima), fora do seu alcance.",
        "Descreva as estruturas NA ORDEM recebida.",
        "É PROIBIDO: reordenar as estruturas, sugerir outra ordem, "
        "acrescentar estrutura que não está na lista, inventar número que "
        "não está na lista, prometer lucro ou tratar o texto como "
        "recomendação de investimento.",
        # Fase 31, Plano 01, Task 3 (D-06): put de proteção, collar de
        # débito e opção a descoberto podem trazer prêmio líquido negativo
        # (débito) — isso é o usuário PAGANDO para montar a estrutura, não
        # ganho nenhum.
        "É PROIBIDO descrever um prêmio líquido NEGATIVO como receita, "
        "ganho ou entrada de caixa — número negativo significa que o "
        "usuário paga para montar aquela estrutura.",
    ])
    return "\n\n".join([
        regras,
        skill_ref.PRINCIPIOS,
        skill_ref.PRINCIPIO_DADOS_SEM_PACOTE,
        "# Aviso obrigatório\n" + skill_ref.DISCLAIMER,
    ])


# Fase 31, Plano 01, Task 3: rótulo em PT-BR de cada tipo do universo
# fechado `TIPOS`, para a narração nomear a estrutura explicitamente em vez
# de tratar tudo como venda coberta.
_ROTULO_TIPO = {
    "call_coberta": "venda coberta",
    "put_protecao": "put de proteção",
    # "collar (call vendida + put comprada)", não "trava protetora (collar)":
    # a string-âncora "trava protetora" é guardada por CVM em
    # test_opcoes_collar_vocab.py (a manchete do collar nasce SÓ em
    # skill_ref.py) — este rótulo é só a etiqueta de TIPO da narração, não
    # pode reusar o texto da manchete nem por acidente.
    "collar": "collar (call vendida + put comprada)",
    "opcao_a_descoberto": "opção a descoberto",
}


def narrativa_user(top: list[dict[str, Any]], modo: str) -> str:
    """Prompt de usuário da narração. PRIMEIRA ação é `exigir_ranking(top)` —
    uma lista fora de ordem levanta `ValueError` e NUNCA chega a montar
    texto, muito menos a sair como prompt para o LLM.

    Serializa só os campos que a narração precisa (T-30-03: lista FECHADA,
    sem `curva`, sem dado de conta, sem saldo, sem id de sessão) — nunca "tudo
    que houver no dict".
    """
    exigir_ranking(top)

    linhas = ["Estas são as estruturas já escolhidas pelo motor determinístico, "
              "na ordem final (não reordene):"]
    for item in top:
        estrutura = item.get("estrutura") or {}
        liquidez = item.get("liquidez") or {}
        rotulo = _ROTULO_TIPO.get(item.get("tipo"), item.get("tipo"))
        # O collar não tem `contractSymbol` único (2 pernas, Fase 31/D-04) —
        # imprimir `None` aqui seria pior que impreciso, seria ilegível.
        # `strikeCall`/`strikePut` já existem no candidato para exatamente
        # este caso.
        identificador = item.get("contractSymbol") or \
            f"call {item.get('strikeCall')} / put {item.get('strikePut')}"
        linhas.append(
            f"{item.get('posicaoNoRanking')}. [{rotulo}] {item.get('ticker')} "
            f"{identificador} — strike R$ {skill_ref.num_br(item.get('strike'))}, "
            f"{item.get('diasParaVencimento')} dias, prêmio líquido unitário "
            f"(positivo = recebido, negativo = pago) "
            f"R$ {skill_ref.num_br(item.get('premioUnitario'))}, prêmio total "
            f"R$ {skill_ref.num_br(item.get('premioTotal'))}, razão "
            f"{skill_ref.num_br(item.get('razao'))}, ganho máximo "
            f"R$ {skill_ref.num_br(estrutura.get('ganho_maximo'))}, perda máxima "
            f"R$ {skill_ref.num_br(estrutura.get('perda_maxima'))}, breakevens "
            f"{estrutura.get('breakevens')}, liquidez {liquidez.get('faixa')}."
        )
    linhas.append("")
    linhas.append("Escreva um parágrafo curto por estrutura, na ordem dada acima.")
    return "\n".join(linhas)
