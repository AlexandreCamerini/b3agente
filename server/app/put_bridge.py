"""server/app/put_bridge.py — ponte gatilho→put (Fase 10, Plano 01, Task 2).

Este módulo é a PONTE entre um sinal de setup (gatilho de baixa detectado
pelo motor determinístico) e a put de proteção candidata — mas, NESTE
plano, só a metade "escolher o contrato certo dentro de uma cadeia já
carregada": função pura, sem rede, sem hook, sem gravação. O Plano 02
pendura o hook que chama `options_provider` e alimenta `triar_put` de
verdade; este plano garante que, quando ele pendurar, escolher um contrato
inventado é estruturalmente impossível.

D-10-A (por que a sugestão de put não mora no `signal_ledger`, ver
`db.init_db`/`10-01-PLAN.md`): a agregação `GROUP BY setup` do ADR-017 não
tem coluna discriminadora de tipo de linha — gravar ali mudaria o ranking
VISÍVEL do Radar por um caminho que nenhum grep de front-end pegaria. Este
módulo nem importa `signal_ledger`.

D-10-E (por que o piso de liquidez usa `volume`, não `total_negocios`): o
`find_tradable_options` do MCP do mydata (referência de desenho de outro
repositório, não código importável) filtra por `total_negocios` — campo que
NÃO existe no contrato ADR-004 (`options_provider_mydata._clean_contract`
mapeia `quantidade_negociada → volume`). Usar o campo que existe é o
correto; inventar o que não existe seria fabricação de dado.

Escopo: Fase 10 é EOD de ponta a ponta, só put COMPRADA, uma perna, sem
margem e sem atribuição — este módulo nunca lê a perna de opção de compra
do payload e nunca produz um resultado que represente venda a descoberto.
"""
from __future__ import annotations

from typing import Optional

PISO_LIQUIDEZ = 100     # quantidade_negociada mínima na sessão (D-10-E)
COLCHAO_PCT = 0.05       # alvo de strike = spot * (1 - 0,05)
OPTION_TYPE = "put"


def _numero_positivo(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def triar_put(payload: dict) -> tuple[Optional[dict], str]:
    """Escolhe UM contrato de put comprada, determinístico, a partir de uma
    cadeia real (formato de `options_provider_mydata.get_options`). Nunca
    levanta: falha de dado sempre volta como `(None, motivo)`.

    Ordem exata das guardas — a primeira que fecha determina o motivo
    (parada dura #1 e #2 do contrato de autonomia vivem aqui: sem estilo de
    exercício real ou sem IV real, o contrato é PULADO, nunca completado por
    default)."""
    if not payload or payload.get("providerStatus") != "ok":
        return None, "fonte degradada"

    spot = payload.get("underlyingPrice")
    if not _numero_positivo(spot):
        return None, "sem preço do ativo-objeto"

    puts = payload.get("puts") or []
    if not puts:
        return None, "sem cadeia de puts"

    alvo = spot * (1 - COLCHAO_PCT)

    elegiveis = []
    pulados_sem_estilo = 0
    pulados_sem_iv = 0
    pulados_sem_liquidez = 0

    for contrato in puts:
        if contrato.get("optionType") != "put":
            continue  # defesa em profundidade: nunca deveria vir aqui vindo de "puts"

        strike = contrato.get("strike")
        if not isinstance(strike, (int, float)) or isinstance(strike, bool) or strike > spot:
            continue  # proteção é abaixo do preço atual — sem contador dedicado

        iv = contrato.get("impliedVolatility")
        if not _numero_positivo(iv):
            pulados_sem_iv += 1
            continue

        estilo = contrato.get("exerciseStyle")
        if not estilo:
            pulados_sem_estilo += 1
            continue

        volume = contrato.get("volume") or 0
        if volume < PISO_LIQUIDEZ:
            pulados_sem_liquidez += 1
            continue

        if not contrato.get("contractSymbol") or not contrato.get("expiration"):
            continue  # sem contador dedicado — dado estrutural ausente da fonte

        elegiveis.append(contrato)

    if not elegiveis:
        return None, "nenhuma put elegível"

    # Ordem TOTAL: distância ao alvo, depois maior volume, depois menor
    # strike, depois o próprio símbolo — sem a quádrupla completa, o teste
    # de determinismo seria uma loteria sobre listas que chegam em ordem
    # diferente (sorted é estável, mas só ajuda se a chave já for total).
    elegiveis.sort(
        key=lambda c: (
            abs(c["strike"] - alvo),
            -(c.get("volume") or 0),
            c["strike"],
            c.get("contractSymbol") or "",
        )
    )
    escolhido = elegiveis[0]

    prov = payload.get("provenance") or {}

    candidato = {
        "contrato": escolhido.get("contractSymbol"),
        "optionType": OPTION_TYPE,
        "strike": escolhido.get("strike"),
        "vencimento": escolhido.get("expiration"),
        "estiloExercicio": escolhido.get("exerciseStyle"),
        "iv": escolhido.get("impliedVolatility"),
        "delta": (escolhido.get("greeks") or {}).get("delta"),
        "premio": escolhido.get("lastPrice"),
        "volume": escolhido.get("volume"),
        "spot": spot,
        "fonte": payload.get("source"),
        "asOf": payload.get("pregao"),
        "provSha256": prov.get("sha256"),
        "provDtCaptura": prov.get("dt_captura"),
        "provCaptura": prov.get("captura"),
        "puladosSemEstilo": pulados_sem_estilo,
        "puladosSemIv": pulados_sem_iv,
        "puladosSemLiquidez": pulados_sem_liquidez,
    }
    return candidato, ""
