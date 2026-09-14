"""Fase 30, Plano 01 — motor PURO da curadoria das 4 melhores estruturas.

Módulo PURO — sem rede, sem banco, sem LLM, sem leitura de relógio interna
(`hoje` entra por argumento), mesma disciplina de
`opcoes_motor.py`/`opcoes_lastreadas.py`/`opcoes_payoff.py`.

Dois cercos da Fase 30, declarados aqui porque é aqui que valem:

- **Universo (D1): SÓ venda coberta.** Put de proteção e collar não entram
  neste ranking — misturar "proteção" com "gerar receita" no mesmo ranking
  de risco mínimo não faz sentido matemático (put por definição não gera
  receita). Se você está pensando em acrescentar um filtro de PUT no lado do
  contrato aqui, pare: é mudança de escopo de produto (D1), não melhoria.
- **Janelas (D3): vários STRIKES dentro do vencimento ÚNICO que a cadeia já
  traz, nunca múltiplos vencimentos.** A cadeia devolvida pelo provider de
  mercado (mydata/Yahoo, ADR-004/008/009) hoje já vem presa a UM vencimento
  (`chain["expiration"]`). Testar vários vencimentos exigiria uma busca por
  vencimento testado, por posição — isso destruiria a propriedade de custo
  de rede ZERO desta fase (30-CONTEXT, achado 3 e decisão D3).
  `candidatos_da_posicao` só enumera `n` strikes dentro da MESMA cadeia já
  buscada, em memória.

Guardrail não-negociável (CLAUDE.md princípio 5 + 30-CONTEXT): a escolha das
4 melhores é 100% aritmética de `opcoes_motor.rastrear()`/`avaliar()`, nunca
de LLM. `rankear()` é a única função que decide ordem; `exigir_ranking()`
torna essa regra comportamento do código, não promessa de comentário — a
camada de narração (`narrativa_user`) é estruturalmente incapaz de receber
um pool não rankeado.
"""
from __future__ import annotations

from typing import Any

from . import opcoes_motor, skill_ref, store
from .opcoes_lastreadas import _PRAZO_MAX_DIAS, _PRAZO_MIN_DIAS, _bloco_liquidez, _dias_ate
from .options_quant import LIQUIDEZ_NEGOCIAVEL, liquidity_score

# TOPO: quantas estruturas a UI mostra ("as 4 melhores" — pedido original).
TOPO = 4
# STRIKES_POR_POSICAO: quantos strikes candidatos `rastrear()` devolve por
# posição elegível, dentro do vencimento único da cadeia (D3).
STRIKES_POR_POSICAO = 5
# PISO_LIQUIDEZ: D5 — reusa o piso já em produção, nunca um corte novo
# inventado só para este ranking. Importado de `.options_quant`, nunca o
# literal 55, para que uma recalibração futura (como a quick 260908-ldg já
# fez uma vez) propague sozinha.
PISO_LIQUIDEZ = LIQUIDEZ_NEGOCIAVEL


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
) -> list[dict[str, Any]]:
    """Candidatos de venda coberta (um por strike distinto) para UMA posição,
    a partir de UMA cadeia já buscada em memória. Devolve SEMPRE lista — `[]`
    em toda porta fechada, nunca `None`, nunca exceção (mesma postura de
    `opcoes_motor.rastrear`/`opcoes_lastreadas.propor`).

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
    motor técnico lê alta). D1 define elegibilidade como "comprado, com lote
    livre >= 100 ações", e só — é decisão de produto fechada, não descuido.
    Consequência nomeada: uma posição que o motor técnico lê como ALTA PODE
    aparecer neste ranking mesmo que não apareceria na proposta única da
    mesma tela (que recusaria com `sem_setup`). Não "corrija" isso
    adicionando um gate técnico aqui.
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
            pernas = [
                opcoes_motor.perna_de_acao(underlying, spot, quantidade=1),
                opcoes_motor.perna_de_contrato(contrato, "venda", quantidade=1),
            ]
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

        premio = float(contrato.get("lastPrice") or 0)
        premio_unitario = round(premio, 2)
        premio_total = round(premio * qty_acoes, 2)
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
        })

    return candidatos


# ─────────────────────────────────────────────────────────────────────────
# rankear() / exigir_ranking() — ordem total, determinística, auditável
# ─────────────────────────────────────────────────────────────────────────

def rankear(candidatos: list[dict[str, Any]], *, topo: int = TOPO) -> list[dict[str, Any]]:
    """As `topo` melhores estruturas, por razão prêmio/perda máxima
    decrescente, com desempate TOTAL e determinístico.

    Chave de ordenação: `(-razao, -premioUnitario, contractSymbol)`. Sem um
    último critério TOTAL (o `contractSymbol`), dois candidatos de razão e
    prêmio iguais ficariam na ordem de chegada — e a ordem de chegada depende
    da ordem das posições na carteira/da cadeia, então a MESMA carteira
    produziria rankings diferentes entre requisições. "As 4 melhores"
    deixaria de ser uma afirmação verificável.

    Esta chave de ordenação é a ÚNICA fonte da ordem: sem peso configurável,
    sem entrada de usuário, sem qualquer campo vindo de LLM (D2 + princípio 5
    do CLAUDE.md). `rankear` não altera nenhum campo dos candidatos além de
    acrescentar `posicaoNoRanking` (1-based, cópia rasa — os dicts de entrada
    não são mutados).
    """
    ordenados = sorted(candidatos, key=lambda c: (-c["razao"], -c["premioUnitario"], c.get("contractSymbol") or ""))
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
    ])
    return "\n\n".join([
        regras,
        skill_ref.PRINCIPIOS,
        skill_ref.PRINCIPIO_DADOS_SEM_PACOTE,
        "# Aviso obrigatório\n" + skill_ref.DISCLAIMER,
    ])


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
        linhas.append(
            f"{item.get('posicaoNoRanking')}. {item.get('ticker')} "
            f"{item.get('contractSymbol')} — strike R$ {skill_ref.num_br(item.get('strike'))}, "
            f"{item.get('diasParaVencimento')} dias, prêmio unitário "
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
