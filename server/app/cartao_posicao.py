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
    # 46.1 (MD-03a): a equação "PM = total ÷ qtd" só aparece sobre histórico completo
    # (qualquer item descartado -> None) e que reconcilia com o PM da posição
    # (posição importada, ajuste por exercício ou histórico truncado -> None).
    total = q = 0.0
    n = 0
    for c in compras:
        if not isinstance(c, dict):
            return None
        cq, cpv = _num(c.get("qty")), _num(c.get("price"))
        if cq is None or cpv is None:
            return None
        total += cq * cpv
        q += cq
        n += 1
    if n == 0 or q <= 0:
        return None
    if abs(total / q - avg) > 0.005 + 1e-9:
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


# ------------------------------------------------------------- cenários

_MENOS = "−"
_INDISP = "indisponível"
_ZONAS = ("perda_travada", "prejuizo", "ganho", "ganho_travado")


def _n(v: Optional[float]) -> Optional[str]:
    """pt-BR 2 casas, ou None (nunca "0,00" para ausente)."""
    return None if v is None else skill_ref.num_br(v)


def _rs(v: Optional[float]) -> str:
    return f"R$ {skill_ref.num_br(v)}" if v is not None else _INDISP


def _ddmm(iso) -> Optional[str]:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return f"{m.group(3)}/{m.group(2)}" if m else None


def _resultado(entrada, preco: float) -> float:
    return round(opcoes_payoff.resultado_no_vencimento(entrada, preco), 2)


def _grade_precos(lo_t: int, hi_t: int, extras: list) -> tuple:
    """Preços da grade em ticks inteiros (sem deriva de float) + preços
    exatos inseridos; devolve (precos_ordenados_sem_duplicata, passo)."""
    n_bruto = max(hi_t - lo_t, 1)
    step = max(1, -(-n_bruto // MAX_PONTOS_GRADE))
    while True:
        base = {round(t * TICK, 2) for t in range(lo_t, hi_t + 1, step)}
        base.add(round(hi_t * TICK, 2))
        base.update(e for e in extras if e is not None and lo_t * TICK - 1e-9 <= e <= hi_t * TICK + 1e-9)
        precos = sorted(base)
        if len(precos) <= MAX_PONTOS_GRADE:
            return precos, round(step * TICK, 2)
        step += 1


def _zona(preco: float, piso, be, k) -> str:
    if piso is not None and preco < piso:
        return "perda_travada"
    if preco < be:
        return "prejuizo"
    if k is None or preco < k:
        return "ganho"
    return "ganho_travado"


def _textos_zonas(presentes: set, modo, piso, be, k, ganho, perda) -> dict:
    ag = _txt(modo, "aguardando_calculo")
    out = {}
    for z in _ZONAS:
        if z not in presentes:
            continue
        dados = {"piso": _n(piso), "be": _n(be), "teto": _n(k),
                 "ganhoMaximo": _n(ganho), "perdaMaxima": _n(perda)}
        if z == "perda_travada":
            chave, precisa = "zona_perda_travada", ("piso", "perdaMaxima")
        elif z == "prejuizo":
            chave, precisa = (("zona_prejuizo_sem_piso", ("be", "perdaMaxima")) if piso is None
                              else ("zona_prejuizo_com_piso", ("piso", "be")))
        elif z == "ganho":
            chave, precisa = (("zona_ganho_sem_teto", ("be",)) if k is None
                              else ("zona_ganho", ("be", "teto")))
        else:
            chave, precisa = "zona_ganho_travado", ("teto", "ganhoMaximo")
        texto = (_txt(modo, chave, **dados) if all(dados[p] is not None for p in precisa)
                 else ag)
        out[z] = {"texto": texto, "rotulo": _txt(modo, "zona_rotulo_" + z)}
    return out


def _conta_call_coberta(entrada, faixa, be, k, nome) -> Optional[dict]:
    """Fórmula fechada só para call coberta simples (D-07)."""
    if nome != "call_coberta" or len(entrada) != 2:
        return None
    acao = next((p for p in entrada if p.get("tipo") == "ACAO"), None)
    call = next((p for p in entrada if p.get("tipo") == "CALL" and p.get("lado") == "venda"), None)
    if not acao or not call or acao.get("quantidade") != call.get("quantidade"):
        return None
    pm, prem, qtd = _num(acao.get("premio")), _num(call.get("premio")), _num(call.get("quantidade"))
    if pm is None or prem is None or qtd is None or k is None:
        return None
    return {"pm": pm, "prem": prem, "qtd": qtd}


def cenarios_da_estrutura(entrada, faixa, nome, spot, vencimento_iso, ticker, modo):
    """Cenários de uma estrutura (contrato 46-03); None se não calculável."""
    if (not isinstance(faixa, dict) or not isinstance(entrada, (list, tuple)) or not entrada
            or not all(isinstance(p, dict) for p in entrada)):
        return None
    bes = faixa.get("breakevens")
    if not isinstance(bes, (list, tuple)) or len(bes) != 1 or _num(bes[0]) is None:
        return None
    be = round(float(bes[0]), 2)
    k, piso = _r2(_num(faixa.get("teto"))), _r2(_num(faixa.get("piso")))
    hoje = _r2(_num(spot))
    try:
        opcoes_payoff.resultado_no_vencimento(entrada, be)
    except ValueError:
        return None
    ganho, perda = faixa.get("ganhoMaximo"), faixa.get("perdaMaxima")
    ate_be = _r1((be / hoje - 1) * 100) if hoje else None
    ate_k = _r1((k / hoje - 1) * 100) if hoje and k is not None else None
    alta_forte = _r2(k * ALTA_FORTE_FATOR) if k is not None else None

    ancoras = [x for x in (hoje, be, piso) if x is not None]
    lo_t = int(math.floor(0.8 * min(ancoras) / TICK + 1e-9))
    hi_t = int(math.ceil(1.14 * max(x for x in (hoje, be, k) if x is not None) / TICK - 1e-9))
    lo, hi = round(lo_t * TICK, 2), round(hi_t * TICK, 2)

    out = {"be": be, "k": k, "piso": piso, "hoje": hoje, "ateBePct": ate_be,
           "ateKPct": ate_k, "altaForte": alta_forte,
           "vencimentoTexto": _ddmm(vencimento_iso),
           "faixaAria": _txt(modo, "faixa_aria", ticker=ticker,
                             piso=(_rs(piso) if piso is not None else _txt(modo, "sem_piso")),
                             be=_n(be), teto=(_rs(k) if k is not None else _txt(modo, "sem_teto")),
                             hoje=_rs(hoje)),
           "simulador": None, "payoff": None, "grade": None}

    if modo == _EDU:
        precos, passo = _grade_precos(lo_t, hi_t, [hoje, be, k, alta_forte])
        pontos = [{"preco": p, "resultado": _resultado(entrada, p),
                   "zona": _zona(p, piso, be, k)} for p in precos]
        idx = {p["preco"]: i for i, p in enumerate(pontos)}
        nomeados = {"hoje": idx.get(hoje), "equilibrio": idx.get(be),
                    "teto": idx.get(k), "alta_forte": idx.get(alta_forte)}
        out["simulador"] = {
            "min": precos[0], "max": precos[-1], "passo": passo, "pontos": pontos,
            "nomeados": nomeados,
            "zonas": _textos_zonas({p["zona"] for p in pontos}, modo, piso, be, k, ganho, perda)}
        return out

    # modo operador: payoff + grade com conta
    perfil = opcoes_payoff.perfil_da_estrutura(entrada)
    xs = {lo, hi, be}
    xs.update(round(c["preco_objeto"], 2) for c in perfil["curva"] if lo <= c["preco_objeto"] <= hi)
    pts = [{"preco": x, "resultado": _resultado(entrada, x)} for x in sorted(xs)]
    ys = [p["resultado"] for p in pts]
    aria_dados = {"ticker": ticker, "be": _n(be), "teto": _n(k), "ganhoMaximo": _rs(ganho),
                  "perdaMaxima": _rs(perda) if perda is not None else "não calculada"}
    # 46.1 (MD-02): teto que cobre só parte das ações (k definido, ganho não calculado)
    # não é "sem teto" para o leitor de tela.
    if k is None:
        chave_aria = "payoff_aria_sem_teto"
    elif ganho is None:
        chave_aria = "payoff_aria_teto_parcial"
    else:
        chave_aria = "payoff_aria"
    out["payoff"] = {"pontos": pts, "xMin": lo, "xMax": hi, "yMin": min(ys), "yMax": max(ys),
                     "aria": _txt(modo, chave_aria, **aria_dados)}

    cc = _conta_call_coberta(entrada, faixa, be, k, nome)
    calls_v = sum(_num(p.get("quantidade")) or 0 for p in entrada
                  if p.get("tipo") == "CALL" and p.get("lado") == "venda")
    acoes_q = sum(_num(p.get("quantidade")) or 0 for p in entrada if p.get("tipo") == "ACAO")
    lastro = min(calls_v, acoes_q) if calls_v > 0 and acoes_q > 0 else None

    def cel(chave, valor, formato, formula=None, numeros=None):
        conta = ({"formula": _txt(modo, formula), "numeros": numeros}
                 if formula and numeros else None)
        return {"chave": chave, "rotulo": _txt(modo, "cel_" + chave), "valor": valor,
                "formato": formato, "conta": conta}

    conta_be = conta_gm = conta_pm = None
    if cc:
        conta_be = f"{_n(cc['pm'])} {_MENOS} {_n(cc['prem'])} = {_n(be)}"
        if ganho is not None:
            conta_gm = (f"({_n(k)} {_MENOS} {_n(be)}) × {skill_ref.num_br_inteiro(cc['qtd'])}"
                        f" = {_n(ganho)}")
        if perda is not None:
            conta_pm = f"{_n(be)} × {skill_ref.num_br_inteiro(cc['qtd'])} = {_n(perda)}"
    out["grade"] = [
        cel("be", be, "preco", "conta_be_call", conta_be),
        cel("ate_be", ate_be, "pct", "conta_ate_be",
            f"{_n(be)} ÷ {_n(hoje)} {_MENOS} 1 = {_pct_txt(ate_be)}" if ate_be is not None else None),
        cel("ate_k", ate_k, "pct", "conta_ate_k",
            f"{_n(k)} ÷ {_n(hoje)} {_MENOS} 1 = {_pct_txt(ate_k)}" if ate_k is not None else None),
        cel("ganho_max", _r2(ganho), "moeda_sinal", "conta_ganho_call", conta_gm),
        cel("perda_max", None if perda is None else _r2(-perda), "moeda_sinal",
            "conta_perda_call", conta_pm),
        cel("lastro", None if lastro is None else int(lastro), "qtd", "conta_lastro",
            f"{skill_ref.num_br_inteiro(lastro)} ações" if lastro is not None else None),
    ]
    return out


# ------------------------------------------------------ didática estrutura

def didatica_estrutura(nome, faixa, entrada, cenarios, acoes, pernas, ticker, modo):
    """Parágrafo com termos tocáveis + "Bóris explica"; só no Estudo."""
    if modo != _EDU:
        return None
    ag = _dt("caso_aguardando")
    faixa = faixa if isinstance(faixa, dict) else {}
    cen = cenarios if isinstance(cenarios, dict) else None
    pernas = [p for p in (pernas or []) if isinstance(p, dict)]
    be = cen["be"] if cen else None
    piso, teto = faixa.get("piso"), faixa.get("teto")
    ganho, perda = faixa.get("ganhoMaximo"), faixa.get("perdaMaxima")
    base = faixa.get("qtdBase")
    qtd = skill_ref.num_br_inteiro(base) if _num(base) is not None else None
    n = {"be": _n(be), "piso": _n(piso), "teto": _n(teto), "ganhoMaximo": _n(ganho),
         "perdaMaxima": _n(perda)}

    def todos(*ks):
        return all(n[k] is not None for k in ks)

    modelo = explica = None
    casos: dict = {}
    if nome == "call_coberta" and cen and qtd and todos("teto", "be", "ganhoMaximo"):
        modelo = _dt("paragrafo_call_coberta", qtd=qtd, teto=n["teto"], be=n["be"])
        explica = _dt("explica_call_coberta", ganhoMaximo=n["ganhoMaximo"], be=n["be"])
    elif nome == "collar" and cen and qtd and todos("piso", "teto", "be", "perdaMaxima", "ganhoMaximo"):
        modelo = _dt("paragrafo_collar", qtd=qtd, piso=n["piso"], teto=n["teto"], be=n["be"])
        explica = _dt("explica_collar", piso=n["piso"], teto=n["teto"],
                      perdaMaxima=n["perdaMaxima"], ganhoMaximo=n["ganhoMaximo"])
    elif nome == "put_protecao" and cen and qtd and todos("piso", "be", "perdaMaxima"):
        modelo = _dt("paragrafo_put_protecao", qtd=qtd, piso=n["piso"], be=n["be"])
        explica = _dt("explica_put_protecao", piso=n["piso"], perdaMaxima=n["perdaMaxima"],
                      be=n["be"])
    if modelo is None:
        casos = {"lastro": ag, "piso": ag, "teto": ag}
        return {"paragrafo": _segmentos(_dt("paragrafo_composta"), casos),
                "borisExplica": _dt("explica_composta")}

    calls = [p for p in pernas if p.get("tipo") == "CALL" and p.get("lado") == "venda"]
    q_calls = sum(_num(p.get("quantidade")) or 0 for p in calls)
    q_acoes = _num((acoes or {}).get("quantidade")) if isinstance(acoes, dict) else None
    pm = _num((acoes or {}).get("precoMedio")) if isinstance(acoes, dict) else None
    if pm is None and isinstance(entrada, (list, tuple)) and entrada:
        pm = _num(entrada[0].get("premio")) if isinstance(entrada[0], dict) else None
    if q_calls and q_acoes is not None:
        casos["lastro"] = _dt("caso_lastro", qtd=skill_ref.num_br_inteiro(min(q_calls, q_acoes)),
                              livres=skill_ref.num_br_inteiro(max(q_acoes - q_calls, 0)))
    else:
        casos["lastro"] = ag
    call = calls[0] if len(calls) == 1 else None
    premio = None
    if call is not None:
        premio = _num(call.get("premioEntrada", call.get("premio")))
    ddmm = cen.get("vencimentoTexto") if cen else None
    if call is not None and premio is not None and ddmm and n["teto"]:
        casos["call_coberta"] = _dt(
            "caso_call_coberta", premio=skill_ref.num_br(premio),
            premioTotal=skill_ref.num_br(premio * (_num(call.get("quantidade")) or 0)),
            teto=n["teto"], ddmm=ddmm)
    else:
        casos["call_coberta"] = ag
    if n["teto"] and n["ganhoMaximo"]:
        casos["teto"] = _dt("caso_teto", teto=n["teto"], ganhoMaximo=n["ganhoMaximo"])
    # sem teto (put de proteção): sem caso → vira texto simples (D-09)
    # 46.1 (2026-10-02, AL-01): a frase só cita a conta que o motor sustenta. A conta
    # do equilíbrio é por estrutura (call coberta: PM - prêmio da call; collar: PM -
    # prêmio da call + prêmio da put) e só é exibida se reconcilia com `cenarios.be`
    # (tolerância de 1 centavo = arredondamento do be a 2 casas). Cobertura parcial,
    # dado divergente ou estrutura sem conta própria caem em "aguardando o cálculo do app".
    puts_c = [p for p in pernas if p.get("tipo") == "PUT" and p.get("lado") == "compra"]
    premio_put = None
    if len(puts_c) == 1:
        premio_put = _num(puts_c[0].get("premioEntrada", puts_c[0].get("premio")))
    be_num = _num(be)
    tol = 0.01 + 1e-9
    hoje = cen.get("hoje") if cen else None
    casos["equilibrio"] = ag
    if pm is not None and premio is not None and be_num is not None and n["be"]:
        if nome == "call_coberta" and abs(pm - premio - be_num) <= tol:
            d = {"be": n["be"], "pm": skill_ref.num_br(pm), "premio": skill_ref.num_br(premio)}
            if hoje is not None:
                casos["equilibrio"] = _dt("caso_equilibrio", hoje=skill_ref.num_br(hoje), **d)
            else:
                casos["equilibrio"] = _dt("caso_equilibrio_sem_hoje", **d)
        elif (nome == "collar" and premio_put is not None
              and abs(pm - premio + premio_put - be_num) <= tol):
            d = {"be": n["be"], "pm": skill_ref.num_br(pm),
                 "premioCall": skill_ref.num_br(premio), "premioPut": skill_ref.num_br(premio_put)}
            if hoje is not None:
                casos["equilibrio"] = _dt("caso_equilibrio_collar", hoje=skill_ref.num_br(hoje), **d)
            else:
                casos["equilibrio"] = _dt("caso_equilibrio_collar_sem_hoje", **d)
    if n["piso"] and n["perdaMaxima"]:
        casos["piso"] = _dt("caso_piso", piso=n["piso"], perdaMaxima=n["perdaMaxima"])
    elif piso is None and n["perdaMaxima"]:
        casos["piso"] = _dt("caso_sem_piso", perdaMaxima=n["perdaMaxima"])
    else:
        casos["piso"] = ag
    return {"paragrafo": _segmentos(modelo, casos), "borisExplica": explica}
