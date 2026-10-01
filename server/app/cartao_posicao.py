"""Motor puro do card de posição v6 (Fase 46, Plano 03; D-01..D-12).

Módulo PURO — sem rede, banco, LLM ou relógio; toda frase vem de `skill_ref`
(`cartao_posicao_txt` / `cartao_didatica_txt`); nenhuma regra de cálculo nova:
só reexpõe/compõe o que `opcoes_payoff` e o plano da posição já definem.
Mesma disciplina de `estrutura_posicao.py`.

- `leitura_plano`: régua, enum de posição no plano, R:R, nota de PM e didática
  do Estudo para uma posição de ação.
- `cenarios_da_estrutura`: simulador (Estudo), payoff + grade com conta
  (Operador) de uma estrutura de opções; todo resultado sai de
  `opcoes_payoff.resultado_no_vencimento` com a mesma entrada que
  `estrutura_posicao._faixa` monta (D-01).
- `didatica_estrutura`: parágrafo com termos tocáveis + "Bóris explica", só
  no Estudo, frases determinísticas (D-11/D-12).

Dado ausente ou inválido → None, nunca 0 nem PM no lugar do preço (princípio 4).
"""
from __future__ import annotations

import math
import re
from typing import Any, Optional

from . import opcoes_payoff, skill_ref

# D-03: decisão de produto — "alta forte" = K × 1,09.
ALTA_FORTE_FATOR = 1.09
# D-05: tick da B3 e teto de pontos da grade do simulador.
TICK = 0.05
MAX_PONTOS_GRADE = 1200

# id do marcador [[id]] -> id do verbete de KB (46-01).
TERMO_KB = {
    "lastro": "opc-lastro",
    "call_coberta": "opc-call-coberta",
    "teto": "opc-teto",
    "equilibrio": "opc-equilibrio",
    "piso": "opc-piso",
    "preco_medio": "mkt-preco-medio",
    "stop": "stop",
    "alvo": "alvo",
    "rr": "risco-rr",
}

_EDU = "educacional"
_MARCADOR = re.compile(r"\[\[([a-z_]+)\]\]")


def _num(v: Any) -> Optional[float]:
    """Número > 0 e finito; bool, texto, None, zero, negativo, NaN → None."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    return v if math.isfinite(v) and v > 0 else None


def _r1(v: Optional[float]) -> Optional[float]:
    return None if v is None else round(v, 1)


def _r2(v: Optional[float]) -> Optional[float]:
    return None if v is None else round(v, 2)


def _moeda_sinal(v: Optional[float]) -> str:
    """"+R$ 1.234,00" / "−R$ 1.234,00" (U+2212); zero sem sinal."""
    if v is None:
        return ""
    a = skill_ref.num_br(abs(v))
    if round(v, 2) == 0:
        return f"R$ {a}"
    return f"{'+' if v > 0 else chr(0x2212)}R$ {a}"


def _pct_txt(v: Optional[float]) -> str:
    """1 casa pt-BR com sinal (U+2212 para negativo)."""
    if v is None:
        return ""
    s = f"{abs(v):.1f}".replace(".", ",")
    if round(v, 1) == 0:
        return f"{s}%"
    return f"{'+' if v > 0 else chr(0x2212)}{s}%"


def _txt(modo: str, chave: str, **d) -> Optional[str]:
    return skill_ref.cartao_posicao_txt(modo, chave, **d)


def _dt(chave: str, **d) -> Optional[str]:
    return skill_ref.cartao_didatica_txt(chave, **d)


def _segmentos(modelo_txt: Optional[str], casos: dict) -> list:
    """Parte o texto já interpolado nos marcadores `[[id]]`. Marcador sem
    verbete (fora de TERMO_KB) ou sem caso vira texto simples (D-09)."""
    if not modelo_txt:
        return []
    out: list = []
    pos = 0
    for m in _MARCADOR.finditer(modelo_txt):
        if m.start() > pos:
            out.append({"texto": modelo_txt[pos:m.start()]})
        tid = m.group(1)
        rotulo = _dt("termo_" + tid) or tid
        caso = casos.get(tid)
        if tid in TERMO_KB and caso:
            out.append({"termo": tid, "rotulo": rotulo, "kb": TERMO_KB[tid],
                        "noSeuCaso": caso})
        else:
            out.append({"texto": rotulo})
        pos = m.end()
    if pos < len(modelo_txt):
        out.append({"texto": modelo_txt[pos:]})
    return out


# ---------------------------------------------------------------- plano

def _nota_pm(avg, qty, compras, modo) -> Optional[str]:
    if avg is None or not isinstance(compras, (list, tuple)):
        return None
    total = q = 0.0
    n = 0
    for c in compras:
        if not isinstance(c, dict):
            continue
        cq, cpv = _num(c.get("qty")), _num(c.get("price"))
        if cq is None or cpv is None:
            continue
        total += cq * cpv
        q += cq
        n += 1
    if n == 0 or q <= 0:
        return None
    nota = _txt(modo, "nota_pm", pm=skill_ref.num_br(avg), total=skill_ref.num_br(total),
                qtd=skill_ref.num_br_inteiro(q))
    if qty is not None and abs(q - qty) > 1e-9:
        nota += _txt(modo, "nota_pm_vendas") or ""
    return nota


def _didatica_plano(r: dict, avg, qty, stop, alvo) -> Optional[dict]:
    if avg is None:
        return None
    pm = skill_ref.num_br(avg)
    if r["plano"] == "completo":
        if r["rr"] is not None:
            modelo = _dt("paragrafo_plano_completo", pm=pm, stop=skill_ref.num_br(stop),
                         alvo=skill_ref.num_br(alvo), rr=skill_ref.num_br(r["rr"]))
        else:
            modelo = _dt("paragrafo_plano_completo_sem_rr", pm=pm,
                         stop=skill_ref.num_br(stop), alvo=skill_ref.num_br(alvo))
        explica = _dt("explica_plano_completo", stop=skill_ref.num_br(stop),
                      alvo=skill_ref.num_br(alvo))
    else:
        modelo = _dt("paragrafo_plano_incompleto", pm=pm)
        explica = _dt("explica_sem_plano" if r["plano"] == "sem_plano"
                      else "explica_plano_incompleto")
    qtd = skill_ref.num_br_inteiro(qty) if qty is not None else ""
    if r["preco"] is not None and qtd:
        c_pm = _dt("caso_preco_medio", pm=pm, qtd=qtd, hoje=skill_ref.num_br(r["preco"]))
    elif qtd:
        c_pm = _dt("caso_preco_medio_sem_hoje", pm=pm, qtd=qtd)
    else:
        c_pm = _dt("caso_aguardando")
    if stop is not None and r["resultadoNoStop"] is not None:
        c_stop = _dt("caso_stop", stop=skill_ref.num_br(stop),
                     resultadoNoStop=_moeda_sinal(r["resultadoNoStop"]))
    else:
        c_stop = _dt("caso_stop_indefinido") if stop is None else _dt("caso_aguardando")
    if alvo is not None and r["resultadoNoAlvo"] is not None:
        c_alvo = _dt("caso_alvo", alvo=skill_ref.num_br(alvo),
                     resultadoNoAlvo=_moeda_sinal(r["resultadoNoAlvo"]))
    else:
        c_alvo = _dt("caso_alvo_indefinido") if alvo is None else _dt("caso_aguardando")
    casos = {"preco_medio": c_pm, "stop": c_stop, "alvo": c_alvo}
    if r["rr"] is not None:
        casos["rr"] = _dt("caso_rr", rr=skill_ref.num_br(r["rr"]))
    return {"paragrafo": _segmentos(modelo, casos), "borisExplica": explica}


def leitura_plano(posicao: dict, preco, compras, modo: str) -> dict:
    """Leitura do plano de uma posição de ação (contrato 46-03)."""
    posicao = posicao if isinstance(posicao, dict) else {}
    avg, qty = _num(posicao.get("avg")), _num(posicao.get("qty"))
    stop, alvo = _num(posicao.get("stop")), _num(posicao.get("alvo"))
    preco = _num(preco)
    ticker = posicao.get("t")
    plano = ("completo" if stop is not None and alvo is not None else
             "so_stop" if stop is not None else
             "so_alvo" if alvo is not None else "sem_plano")

    r: dict = {"ticker": ticker, "preco": _r2(preco), "plano": plano}
    r["resultado"] = (_r2((preco - avg) * qty)
                      if preco is not None and avg is not None and qty is not None else None)
    r["variacaoPct"] = (_r1((preco / avg - 1) * 100)
                        if preco is not None and avg is not None else None)
    pos_plano = None
    if plano == "completo" and preco is not None:
        pos_plano = ("abaixo_stop" if preco < stop else
                     "acima_alvo" if preco > alvo else "dentro")
    r["posicaoNoPlano"] = pos_plano
    r["distStopPct"] = _r1((stop / preco - 1) * 100) if stop is not None and preco else None
    r["distAlvoPct"] = _r1((alvo / preco - 1) * 100) if alvo is not None and preco else None
    rr = None
    if plano == "completo" and preco is not None and preco > stop:
        v = (alvo - preco) / (preco - stop)
        rr = round(v, 2) if math.isfinite(v) and v > 0 else None
    r["rr"] = rr
    r["resultadoNoStop"] = (_r2((stop - avg) * qty)
                            if stop is not None and avg is not None and qty is not None else None)
    r["resultadoNoAlvo"] = (_r2((alvo - avg) * qty)
                            if alvo is not None and avg is not None and qty is not None else None)

    gat = None
    se = posicao.get("setupEntrada")
    inval = _num(se.get("invalidacao")) if isinstance(se, dict) else None
    if inval is not None and preco is not None:
        invalidado = preco > inval if se.get("lado") == "baixa" else preco < inval
        gat = "invalidado" if invalidado else "valido"
    r["gatilhoStatus"] = gat
    r["notaPm"] = _nota_pm(avg, qty, compras, modo)
    r["reguaAria"] = (_txt(modo, "regua_aria", ticker=ticker, stop=skill_ref.num_br(stop),
                           alvo=skill_ref.num_br(alvo), pm=skill_ref.num_br(avg),
                           agora=(f"R$ {skill_ref.num_br(preco)}" if preco is not None
                                  else "indisponível"))
                      if plano == "completo" and avg is not None else None)
    r["didatica"] = _didatica_plano(r, avg, qty, stop, alvo) if modo == _EDU else None
    return r
