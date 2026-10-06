"""Fase 49, Plano 03 — motor puro da anatomia da perna (ANAT-01..05, ANAT-08).

Decisões que moldam o módulo:

- PURO: sem rede, banco, LLM nem relógio. `hoje` entra por argumento; o
  chamador (rota do 49-05) decide o dia. Princípio 5 do produto: todo número
  da tela nasce aqui, a tela só lê e posiciona (nada de conta no cliente).
- Payoff NÃO tem fórmula própria: tudo passa por `opcoes_payoff`
  (`resultado_no_vencimento` / `perfil_da_estrutura`), a mesma da Fase 36.
  `cartao_posicao.cenarios_da_estrutura` só serve estrutura nomeada com um
  breakeven; três compradas avulsas não formam estrutura, daí este motor.
- O resultado no vencimento de cada perna NÃO depende de cotação. Só o campo
  `hoje` vem da estrutura cotada (`estrutura_posicao.ler_estrutura`).
- Dias CORRIDOS (`(venc - hoje).days`), igual a estrutura_posicao/ESTR-04.
- Valores em R$ arredondados a 2 casas. Dado ausente é None com frase que
  começa por "Não há dados suficientes para concluir." — nunca 0.
- A grade de preços NÃO depende de `excluir`: ligar/desligar um chip não pode
  mover o índice do slider. Por isso as âncoras incluem todas as pernas
  válidas e o preço médio das ações, marcados ou não.
- Ações só entram no total com o preço médio do simulador (`posicao.avg`);
  sem ele ficam fora com aviso, nunca estimadas.
"""
from __future__ import annotations

import datetime as _dt
import math
from typing import Any, Optional, Sequence

from . import opcoes_payoff, skill_ref

MAX_PONTOS_ANATOMIA = 121
ACOES_ID = "ACOES"
# Mesmo tick de cartao_posicao.TICK (R$ 0,05); redefinido para não acoplar o
# motor ao módulo do cartão por uma constante.
TICK = 0.05
_CAUSAS = ("fonte_indisponivel", "fora_da_cadeia", "sem_negocio", "sem_cotacao")


# --- helpers numéricos --------------------------------------------------

def _num(v: Any) -> Optional[float]:
    """Número > 0; bool/texto/None/zero/negativo → None (T-49-07)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    return v if math.isfinite(v) and v > 0 else None


def _num_nn(v: Any) -> Optional[float]:
    """Número >= 0 (prêmio de entrada pode ser 0)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    return v if math.isfinite(v) and v >= 0 else None


def _r2(v: Optional[float]) -> Optional[float]:
    return None if v is None else round(v, 2)


def _inteiro_se_cabe(v: Optional[float]):
    return int(v) if v is not None and float(v).is_integer() else v


def _data(v: Any) -> Optional[_dt.date]:
    if not isinstance(v, str):
        return None
    try:
        return _dt.date.fromisoformat(v.strip()[:10])
    except ValueError:
        return None


def _dd_mm(d: Optional[_dt.date]) -> Optional[str]:
    return None if d is None else f"{d.day:02d}/{d.month:02d}"


def _txt(modo: str, chave: str, **dados) -> Optional[str]:
    return skill_ref.opcoes_escada_txt(modo, chave, **dados)


# --- normalização -------------------------------------------------------

def _normalizar(op: dict) -> dict:
    """Mesma regra de estrutura_posicao._perna (WR-04): `side` ausente =
    comprada; valor fora de {vendida, comprada} vira lado=None (o sinal não é
    adivinhado). Reimplementada aqui para não importar função privada."""
    bruto = op.get("side")
    lado_txt = str(bruto).strip().lower() if bruto is not None else ""
    if lado_txt == "vendida":
        lado = "venda"
    elif lado_txt in ("", "comprada"):
        lado = "compra"
    else:
        lado = None
    return {
        "id": op.get("id"),
        "tipo": str(op.get("optionType") or "").upper(),
        "lado": lado,
        "strike": _num(op.get("strike")),
        "quantidade": _num(op.get("qty")),
        "premioEntrada": _num_nn(op.get("avg")),
        "vencimento": op.get("expiration"),
    }


def _entrada(p: dict) -> dict:
    return {"tipo": p["tipo"], "lado": p["lado"], "strike": p["strike"],
            "premio": p["premioEntrada"], "quantidade": p["quantidade"],
            "vencimento": p["vencimento"]}


def _valida(p: dict) -> bool:
    return (p["tipo"] in ("CALL", "PUT") and p["lado"] is not None
            and p["strike"] is not None and p["quantidade"] is not None
            and p["premioEntrada"] is not None)


def _prazo(modo: str, venc: Optional[_dt.date], hoje: _dt.date):
    if venc is None:
        return None, _txt(modo, "anat_prazo_sem_data")
    dias = (venc - hoje).days
    dd = _dd_mm(venc)
    if dias < 0:
        chave = "anat_prazo_vencida"
    elif dias == 0:
        chave = "anat_prazo_hoje"
    elif dias == 1:
        chave = "anat_prazo_amanha"
    else:
        chave = "anat_prazo_dias"
    return dias, _txt(modo, chave, dias=dias, vencimento=dd)


# --- grade --------------------------------------------------------------

def _grade(ancoras: list[float], spot: Optional[float]) -> dict:
    if not ancoras:
        return {"precos": [], "passo": TICK, "indiceInicial": 0, "hoje": spot}
    lo_t = math.floor(0.85 * min(ancoras) / TICK)
    hi_t = math.ceil(1.15 * max(ancoras) / TICK)
    passo_t = max(1, math.ceil((hi_t - lo_t) / (MAX_PONTOS_ANATOMIA - 1)))
    lo, hi = round(lo_t * TICK, 2), round(hi_t * TICK, 2)
    precos = {round(t * TICK, 2) for t in range(lo_t, hi_t + 1, passo_t)}
    precos.add(hi)
    precos.update(a for a in (round(x, 2) for x in ancoras) if lo <= a <= hi)
    precos = sorted(precos)
    if spot is not None and round(spot, 2) in precos:
        ini = precos.index(round(spot, 2))
    else:
        ini = len(precos) // 2
    return {"precos": precos, "passo": round(passo_t * TICK, 2),
            "indiceInicial": ini, "hoje": spot}


def _pontos(entrada: list[dict], precos: list[float]) -> list[float]:
    return [round(opcoes_payoff.resultado_no_vencimento(entrada, p), 2) for p in precos]


def _tabela(precos: list[float], pontos: list[float], chaves: list) -> list[dict]:
    alvo = {precos[0], precos[-1]}
    alvo.update(round(c, 2) for c in chaves if c is not None)
    return [{"preco": p, "resultado": pontos[i]}
            for i, p in enumerate(precos) if p in alvo]


# --- hoje / encerrar ----------------------------------------------------

def _hoje(modo: str, estrutura: Any, id_: Any) -> tuple[dict, Optional[dict]]:
    if not isinstance(estrutura, dict):
        return ({"valor": None, "premioAtual": None,
                 "motivoTexto": _txt(modo, "anat_hoje_sem_estrutura")}, None)
    alvo = next((x for x in (estrutura.get("pernas") or [])
                 if isinstance(x, dict) and x.get("id") == id_), None)
    if alvo is None:
        return ({"valor": None, "premioAtual": None,
                 "motivoTexto": _txt(modo, "anat_hoje_sem_cotacao")}, None)

    def _n(v):
        # IN-01 (49-REVIEW): inf/nan do payload é dado ausente, nunca número.
        return (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool)
                and math.isfinite(v) else None)

    valor, premio = _n(alvo.get("resultado")), _n(alvo.get("premioAtual"))
    motivo = None
    if valor is None:
        causa = alvo.get("motivoSemCotacao")
        causa = causa if causa in _CAUSAS else "sem_cotacao"
        motivo = _txt(modo, f"anat_hoje_{causa}")
    enc = alvo.get("encerrar")
    return ({"valor": valor, "premioAtual": premio, "motivoTexto": motivo},
            dict(enc) if isinstance(enc, dict) else None)


# --- API ----------------------------------------------------------------

def ler_anatomia(option_positions: Sequence[dict], underlying: str, posicao: Any,
                 spot: Any, estrutura: Any, hoje: _dt.date, modo: str,
                 excluir: Sequence[str] = ()) -> Optional[dict]:
    """Anatomia por perna + total por ativo. None se não há perna do ativo."""
    ops = [o for o in (option_positions or [])
           if isinstance(o, dict) and o.get("underlying") == underlying]
    if not ops:
        return None
    excluir = tuple(excluir or ())
    spot_n = _num(spot)
    pernas = [_normalizar(o) for o in ops]

    # Perfil por perna; ValueError do payoff isola a perna (T-49-07).
    for p in pernas:
        p["_ok"] = _valida(p)
        p["_venc"] = _data(p["vencimento"])
        p["_perfil"] = None
        if p["_ok"]:
            try:
                p["_perfil"] = opcoes_payoff.perfil_da_estrutura([_entrada(p)])
            except ValueError:
                p["_ok"] = False

    # Ações: só com preço médio do simulador.
    acoes = None
    pm = qtd_acoes = None
    if isinstance(posicao, dict):
        qtd_acoes = _num(posicao.get("qty"))
        if qtd_acoes is not None:
            pm = _num(posicao.get("avg"))
            pm = round(pm, 2) if pm else None
    acoes_incluidas = pm is not None and ACOES_ID not in excluir

    # Grade: independe de `excluir`.
    ancoras: list[float] = []
    for p in pernas:
        if p["_ok"]:
            ancoras.append(p["strike"])
            bes = p["_perfil"]["breakevens"]
            if len(bes) == 1:
                ancoras.append(round(bes[0], 2))
    if spot_n is not None:
        ancoras.append(spot_n)
    if pm is not None:
        ancoras.append(pm)
    grade = _grade(ancoras, spot_n)
    precos = grade["precos"]

    saida_pernas = []
    for p in pernas:
        id_ = p["id"]
        tipo_k = "call" if p["tipo"] == "CALL" else "put"
        lado_k = "compra" if p["lado"] == "compra" else "venda"
        dias, prazo_txt = _prazo(modo, p["_venc"], hoje)
        hoje_p, enc = _hoje(modo, estrutura, id_)
        item = {
            "id": id_, "tipo": p["tipo"], "lado": p["lado"], "strike": p["strike"],
            "quantidade": _inteiro_se_cabe(p["quantidade"]),
            "premioEntrada": p["premioEntrada"], "vencimento": p["vencimento"],
            "vencimentoTexto": _dd_mm(p["_venc"]), "dias": dias, "prazoTexto": prazo_txt,
            "valorPremio": None, "piorCaso": None, "piorIlimitado": False,
            "piorTexto": None, "equilibrio": None, "frase": None, "condicao": None,
            "pontos": None, "marcadores": [], "tabela": [], "aria": None,
            "incluida": False, "motivoTexto": None, "hoje": hoje_p, "encerrar": enc,
        }
        if not p["_ok"] or not precos:
            item["motivoTexto"] = _txt(modo, "anat_dados_insuficientes")
            saida_pernas.append(item)
            continue

        perfil = p["_perfil"]
        item["valorPremio"] = round(p["premioEntrada"] * p["quantidade"], 2)
        item["piorIlimitado"] = bool(perfil["perda_ilimitada"])
        if not item["piorIlimitado"]:
            item["piorCaso"] = round(-abs(perfil["perda_maxima"]), 2)
        bes = perfil["breakevens"]
        item["equilibrio"] = round(bes[0], 2) if len(bes) == 1 else None
        pts = _pontos([_entrada(p)], precos)
        item["pontos"] = pts
        item["marcadores"] = [{"chave": "strike", "preco": p["strike"]}]
        if item["equilibrio"] is not None:
            item["marcadores"].append({"chave": "equilibrio", "preco": item["equilibrio"]})
        item["tabela"] = _tabela(precos, pts, [p["strike"], item["equilibrio"], spot_n])
        item["incluida"] = id_ not in excluir

        venc_txt = _dd_mm(p["_venc"]) or "—"
        item["frase"] = _txt(
            modo, f"anat_frase_{tipo_k}_{lado_k}",
            valor=skill_ref.num_br(item["valorPremio"]),
            premio=skill_ref.num_br(p["premioEntrada"]),
            qtd=skill_ref.num_br_inteiro(p["quantidade"]), ticker=underlying,
            strike=skill_ref.num_br(p["strike"]), vencimento=venc_txt)
        if item["equilibrio"] is not None:
            item["condicao"] = _txt(modo, f"anat_cond_{tipo_k}_{lado_k}", ticker=underlying,
                                    equilibrio=skill_ref.num_br(item["equilibrio"]))
        if item["piorIlimitado"]:
            item["piorTexto"] = _txt(modo, "anat_pior_ilimitado_nota", ticker=underlying)
            pior_aria = _txt(modo, "anat_pior_ilimitado")
        else:
            pior_aria = "−R$ " + skill_ref.num_br(abs(item["piorCaso"]))
        if item["equilibrio"] is not None:
            item["aria"] = _txt(modo, "anat_perna_aria", id=id_, pior=pior_aria,
                                equilibrio=skill_ref.num_br(item["equilibrio"]))
        saida_pernas.append(item)

    # Ações (pontos só se incluídas).
    acao_entrada = None
    if qtd_acoes is not None:
        qtd_i = _inteiro_se_cabe(qtd_acoes)
        acoes = {"quantidade": qtd_i, "precoMedio": pm, "incluidas": acoes_incluidas,
                 "pontos": None, "texto": None}
        if pm is not None:
            acoes["texto"] = _txt(modo, "anat_acoes_dentro", qtd=skill_ref.num_br_inteiro(qtd_acoes),
                                  ticker=underlying, pm=skill_ref.num_br(pm))
        else:
            acoes["texto"] = _txt(modo, "anat_acoes_fora_sem_pm",
                                  qtd=skill_ref.num_br_inteiro(qtd_acoes), ticker=underlying)
        if acoes_incluidas and precos:
            acao_entrada = {"tipo": "ACAO", "lado": "compra", "strike": 0, "premio": pm,
                            "quantidade": qtd_acoes}
            acoes["pontos"] = _pontos([acao_entrada], precos)

    # Total.
    incl = [p for p, it in zip(pernas, saida_pernas) if it["incluida"]]
    total = {"pontos": None, "incluidas": [], "semEsta": {}, "motivoTexto": None,
             "aria": None, "tabela": [], "marcadores": []}
    if not incl and acao_entrada is None:
        total["motivoTexto"] = _txt(modo, "anat_total_vazio")
    else:
        vencs = sorted({p["_venc"] for p in incl if p["_venc"] is not None})
        if len(vencs) > 1:
            total["incluidas"] = [p["id"] for p in incl]
            total["motivoTexto"] = _txt(
                modo, "anat_total_vencimentos_diferentes",
                vencimentos=" e ".join(_dd_mm(v) for v in vencs))
        else:
            base = [_entrada(p) for p in incl] + ([acao_entrada] if acao_entrada else [])
            total["incluidas"] = [p["id"] for p in incl]
            total["pontos"] = _pontos(base, precos)
            for p in incl:
                resto = [_entrada(q) for q in incl if q is not p] + (
                    [acao_entrada] if acao_entrada else [])
                total["semEsta"][p["id"]] = _pontos(resto, precos) if resto else None
            acoes_aria = (_txt(modo, "anat_total_aria_acoes",
                               qtd=skill_ref.num_br_inteiro(qtd_acoes))
                          if acao_entrada else "")
            total["aria"] = _txt(modo, "anat_total_aria", ticker=underlying,
                                 n=len(incl), acoes=acoes_aria)
            total["tabela"] = _tabela(
                precos, total["pontos"],
                [p["strike"] for p in incl]
                + [it["equilibrio"] for it in saida_pernas if it["incluida"]]
                + [spot_n, pm if acao_entrada else None])
            total["marcadores"] = [{"chave": "strike", "preco": p["strike"], "id": p["id"]}
                                   for p in incl]
            if acao_entrada:
                total["marcadores"].append({"chave": "precoMedio", "preco": pm, "id": None})
            if spot_n is not None:
                total["marcadores"].append({"chave": "hoje", "preco": spot_n, "id": None})

    validas = [p for p in pernas if p["_ok"]]
    vencs_validas = {p["_venc"] for p in validas}
    venc_unico = (_dd_mm(next(iter(vencs_validas)))
                  if len(vencs_validas) == 1 else None)
    ids = {p["id"] for p in pernas}
    excluidas = [e for e in excluir if e in ids or e == ACOES_ID]

    return {"vencimentoTexto": venc_unico, "grade": grade, "excluidas": excluidas,
            "acoes": acoes, "pernas": saida_pernas, "total": total}
