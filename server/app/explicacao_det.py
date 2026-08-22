"""Compositor determinístico da explicação do Passo 7 (FIX-C01).

Por que existe: `POST /api/analyze/{ticker}` e `POST /api/technical/analyze/
{ticker}` dependiam de uma chamada de IA — sem chave BYOK nem cota gerenciada,
o usuário grátis nunca recebia NENHUMA explicação depois de operar. Este
módulo monta uma explicação mínima a partir do setup/indicador que o motor JÁ
calculou (`setups.py`/`technical_snapshot.py`), usando a mesma fonte
determinística 0-custo de `conceitos.py`/`kb.py` — nunca um card vazio, nunca
só o erro técnico.

O que este módulo NÃO é: não sabe que existe uma camada de IA, não recebe nem
formata mensagem de indisponibilidade de provedor (isso é da rota, Plano
04-04, para nenhum detalhe cru vazar no texto do usuário — ver
`<threat_model>` T-04-01 do plano 04-01). PURO: zero rede, zero acesso a
persistência, zero import de camada de IA.

Estrutura do markdown, na ordem pedagógica canônica do produto
(`skill_ref.DIDATICA`: o que o motor detectou → o que cada indicador marca →
o que isso significa → o que mudaria a leitura → idade do dado):

  1. O que o motor detectou agora — veredito de `context["setupsRadar"]`
     (frase canônica de `setups.avaliar`, copiada verbatim — guardrail CVM:
     a manchete vem SÓ do motor determinístico).
  2. O que cada indicador marca — viés de tendência, ATR(14)/ATR%, suporte e
     resistência mais próximos, bandas de Bollinger. Campo ausente some da
     saída — nunca vira "0,0" nem "—" com número inventado.
  3. O que isso significa — verbete correspondente ao setup detectado
     (`kb.buscar`/`kb.formatar`), com fallback para o verbete genérico de
     risco quando o setup não tem verbete próprio.
  4. O que mudaria a leitura — gatilho/invalidação do melhor setup.
  5. Idade do dado — última barra fechada e ressalva da barra em formação
     descartada, no mesmo tom de `_pet_resumo_evolucao` ("nunca é agora").
"""
from __future__ import annotations

from typing import Optional

from .conceitos import _num, _pct
from . import kb

_FALLBACK_VERBETE_IDS = ("risco-rr", "stop")


def _linha_motor(setups_radar: dict) -> tuple[list, Optional[str], Optional[int]]:
    veredito = setups_radar.get("veredito")
    melhor_nome = setups_radar.get("melhorSetup")
    confluencia = setups_radar.get("confluencia")
    linhas = []
    if veredito:
        linhas.append(f"O motor aponta: **{veredito}**.")
    if melhor_nome:
        conf_txt = _pct(confluencia) if isinstance(confluencia, (int, float)) else None
        if conf_txt:
            linhas.append(f"Setup identificado: {melhor_nome}, confluência {conf_txt}.")
        else:
            linhas.append(f"Setup identificado: {melhor_nome}.")
    return linhas, melhor_nome, confluencia


def _linhas_indicadores(context: dict) -> list:
    trend = context.get("trend") or {}
    vol = context.get("volatility") or {}
    levels = context.get("levels") or {}
    bias = trend.get("bias")
    atr14 = vol.get("atr14")
    atr14_pct = vol.get("atr14Pct")
    sup = levels.get("nearestSupport")
    res = levels.get("nearestResistance")
    bu, bl = vol.get("bollingerUpper"), vol.get("bollingerLower")

    linhas = []
    if bias in ("alta", "baixa"):
        linhas.append(f"Tendência: viés de {bias}, medido pelo alinhamento das médias móveis.")
    elif bias:
        linhas.append("Tendência: sem viés definido no momento — médias sem alinhamento claro.")

    if atr14 is not None:
        atr_txt = _num(atr14)
        if atr_txt:
            pct_txt = _pct(atr14_pct) if isinstance(atr14_pct, (int, float)) else None
            complemento = f" ({pct_txt} do preço)" if pct_txt else ""
            linhas.append(f"Volatilidade (ATR 14): {atr_txt}{complemento} de oscilação média por candle.")

    if sup is not None:
        sup_txt = _num(sup)
        if sup_txt:
            linhas.append(f"Suporte mais próximo: {sup_txt}.")

    if res is not None:
        res_txt = _num(res)
        if res_txt:
            linhas.append(f"Resistência mais próxima: {res_txt}.")

    if bu is not None and bl is not None:
        bu_txt, bl_txt = _num(bu), _num(bl)
        if bu_txt and bl_txt:
            linhas.append(f"Bandas de Bollinger: banda superior {bu_txt}, banda inferior {bl_txt}.")

    return linhas


def _verbete_do_setup(melhor_nome: Optional[str], modo: str) -> tuple[list, list]:
    """Texto do verbete do setup detectado, com fallback genérico de risco
    quando o setup não resolve nenhum verbete próprio. Nunca link morto:
    os ids de fallback existem sempre no catálogo (`kb.py`, família
    `plano_risco`)."""
    v = None
    if melhor_nome:
        achados = kb.buscar(melhor_nome, limite=1)
        v = achados[0] if achados else None
    if v is None:
        for vid in _FALLBACK_VERBETE_IDS:
            v = kb.verbete(vid)
            if v:
                break
    if not v:
        return [], []
    f = kb.formatar(v, modo)
    texto = f.get("texto")
    if not texto:
        return [], []
    return [texto], [f["id"]]


def _linhas_mudanca(setups_radar: dict, melhor_nome: Optional[str]) -> list:
    if not melhor_nome:
        return []
    setup = next((s for s in (setups_radar.get("setups") or [])
                  if isinstance(s, dict) and s.get("nome") == melhor_nome), None)
    if not setup:
        return []
    linhas = []
    gat_txt = _num(setup.get("gatilho")) if setup.get("gatilho") is not None else None
    if gat_txt:
        linhas.append(f"Gatilho de entrada do plano: {gat_txt}.")
    inv_txt = _num(setup.get("invalidacao")) if setup.get("invalidacao") is not None else None
    if inv_txt:
        linhas.append(f"Nível de invalidação: {inv_txt} — passado ele, a leitura deixa de valer.")
    return linhas


def _linhas_idade(snap: dict) -> list:
    linhas = []
    as_of = (snap or {}).get("asOf")
    if as_of:
        linhas.append(f"Leitura até a barra fechada em {as_of}. O que você vê já aconteceu; nunca é agora.")
    barra_formacao = (snap or {}).get("barraEmFormacao")
    if barra_formacao:
        linhas.append(
            f"A barra em formação ({barra_formacao}) foi descartada desta leitura — "
            "ainda pode mudar até fechar."
        )
    return linhas


def montar(ticker: str, snap: dict, modo: str = "educacional", quote: Optional[dict] = None) -> dict:
    """Explicação determinística do Passo 7, a partir de um snapshot técnico
    já calculado (`technical_snapshot.build/get`). `quote` é reservado para
    quem chamar querer citar a cotação ao vivo no futuro — não é usado aqui:
    o motor de sinais fica separado dos preços ao vivo, mesmo princípio do
    próprio `technical_snapshot.py`.

    Retorno: `{"markdown": str, "fonte": "deterministico", "verbetes": [ids],
    "semDados": bool, "asOf": str | None}`. `semDados=True` quando não há
    setup detectado NEM indicador utilizável — quem decide o que mostrar
    nesse caso é a rota/UI (não este módulo)."""
    snap = snap or {}
    context = snap.get("context") or {}
    setups_radar = context.get("setupsRadar") or {}
    as_of = snap.get("asOf")

    linhas_motor, melhor_nome, _confluencia = _linha_motor(setups_radar)
    linhas_indicadores = _linhas_indicadores(context)

    if not melhor_nome and not linhas_indicadores:
        return {"markdown": "", "fonte": "deterministico", "verbetes": [], "semDados": True, "asOf": as_of}

    linhas_significado, verbetes_usados = _verbete_do_setup(melhor_nome, modo)
    linhas_mudanca = _linhas_mudanca(setups_radar, melhor_nome)
    linhas_idade = _linhas_idade(snap)

    blocos = []
    if linhas_motor:
        blocos.append("## O que o motor detectou agora\n\n" + " ".join(linhas_motor))
    if linhas_indicadores:
        blocos.append("## O que cada indicador marca\n\n" + "\n".join("- " + l for l in linhas_indicadores))
    if linhas_significado:
        blocos.append("## O que isso significa\n\n" + " ".join(linhas_significado))
    if linhas_mudanca:
        blocos.append("## O que mudaria a leitura\n\n" + " ".join(linhas_mudanca))
    if linhas_idade:
        blocos.append("## Idade do dado\n\n" + " ".join(linhas_idade))

    return {
        "markdown": "\n\n".join(blocos),
        "fonte": "deterministico",
        "verbetes": verbetes_usados,
        "semDados": False,
        "asOf": as_of,
    }
