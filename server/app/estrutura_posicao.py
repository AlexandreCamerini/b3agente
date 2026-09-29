"""Motor puro de leitura de estrutura de opções por ativo (Fase 44, Plano 02).

Módulo PURO — sem rede, sem banco, sem LLM, sem leitura de relógio (`hoje`
entra por argumento) — mesma disciplina de `opcoes_payoff.py` e
`opcoes_lastreadas.py`. Toda frase do payload vem de `skill_ref`
(`estrutura_posicao_txt` / `opcoes_lastreadas_txt`); nenhum texto de usuário
é escrito aqui.

Decisões (44-CONTEXT):
- D-01/D-03: recebe TODAS as `optionPositions` do escopo, filtra pelo
  underlying, lista todas as pernas e classifica o CONJUNTO (call coberta,
  put de proteção, collar). Qualquer outro conjunto: nome None, pernas ainda
  listadas.
- D-02: cálculo só no servidor; o front recebe o payload pronto (sem espelho).
- D-04: perna vendida é marcada pelo ASK (o que custa recomprar), comprada
  pelo BID (o que rende vender); lado ausente cai no `lastPrice` com origem
  "last" explícita; nenhum → None. Nunca mid, nunca estimado.
- D-05: com perna (ou ação) sem cotação o total é None e `incompleto` True;
  as partes conhecidas aparecem separadas. Nunca 0 no lugar de desconhecido.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Optional

from . import skill_ref

_CALL, _PUT = "CALL", "PUT"


def _num(v: Any) -> Optional[float]:
    """Número > 0; bool, texto, None, zero e negativo → None (T-44-03)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    return v if v == v and v > 0 else None


def _num_nn(v: Any) -> Optional[float]:
    """Número >= 0 (prêmio de entrada pode, em tese, ser 0)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    return v if v == v and v >= 0 else None


def _r2(v: Optional[float]) -> Optional[float]:
    return None if v is None else round(v, 2)


def _perna(op: dict) -> dict:
    """Normaliza uma `optionPosition`. `side` ausente = comprada (modelo antigo)."""
    return {
        "id": op.get("id"),
        "tipo": str(op.get("optionType") or "").upper(),
        "lado": "venda" if op.get("side") == "vendida" else "compra",
        "strike": _num(op.get("strike")),
        "vencimento": op.get("expiration"),
        "quantidade": _num(op.get("qty")),
        "premioEntrada": _num_nn(op.get("avg")),
    }


def _marcar(perna: dict, contrato: Optional[dict], modo: str) -> tuple:
    """(premioAtual, origem, origemTexto) — D-04."""
    if not isinstance(contrato, dict):
        return None, None, None
    principal, origem = ((contrato.get("ask"), "ask") if perna["lado"] == "venda"
                         else (contrato.get("bid"), "bid"))
    v = _num(principal)
    if v is not None:
        return v, origem, None
    v = _num(contrato.get("lastPrice"))
    if v is not None:
        return v, "last", skill_ref.estrutura_posicao_txt(
            modo, "origem_last", perna=perna["id"])
    return None, None, None


def _classificar(pernas: list) -> Optional[str]:
    conj = {(p["tipo"], p["lado"]) for p in pernas}
    if conj == {(_CALL, "venda")}:
        return "call_coberta"
    if conj == {(_PUT, "compra")}:
        return "put_protecao"
    if conj == {(_CALL, "venda"), (_PUT, "compra")}:
        return "collar"
    return None


def _resultado_perna(p: dict) -> Optional[float]:
    atual, entrada, qtd = p["premioAtual"], p["premioEntrada"], p["quantidade"]
    if atual is None or entrada is None or qtd is None:
        return None
    dif = entrada - atual if p["lado"] == "venda" else atual - entrada
    return round(dif * qtd, 2)


def ler_estrutura(option_positions, underlying, posicao, spot, contratos_por_id,
                  hoje, modo, motivo_sem_proposta=None) -> Optional[dict]:
    """Leitura determinística da estrutura aberta de `underlying`.

    `None` quando não há nenhuma perna do ativo. Números arredondados a 2
    casas; None = desconhecido, nunca 0.0.
    """
    ops = [o for o in (option_positions or [])
           if isinstance(o, dict) and o.get("underlying") == underlying]
    if not ops:
        return None
    spot = _num(spot)
    contratos = contratos_por_id if isinstance(contratos_por_id, dict) else {}

    pernas = []
    for op in ops:
        p = _perna(op)
        p["premioAtual"], p["origemPremio"], p["origemTexto"] = _marcar(
            p, contratos.get(p["id"]), modo)
        p["resultado"] = _resultado_perna(p)
        pernas.append(p)

    nome = _classificar(pernas)

    # --- ações ---
    qtd_acoes = _num(posicao.get("qty")) if isinstance(posicao, dict) else None
    acoes = None
    if qtd_acoes is not None:
        pm = _num(posicao.get("avg"))
        res_acoes = None if (spot is None or pm is None) else round((spot - pm) * qtd_acoes, 2)
        acoes = {"quantidade": qtd_acoes, "precoMedio": _r2(pm), "preco": _r2(spot),
                 "resultado": res_acoes}

    # --- resultado total (D-05) ---
    sem_cotacao = [p["id"] for p in pernas if p["resultado"] is None]
    cotadas = [p["resultado"] for p in pernas if p["resultado"] is not None]
    acao_falta = acoes is not None and acoes["resultado"] is None
    incompleto = bool(sem_cotacao) or acao_falta
    total, texto = None, None
    if not incompleto:
        total = round(sum(cotadas) + (acoes["resultado"] if acoes else 0.0), 2)
    else:
        partes = []
        if sem_cotacao:
            partes.append(skill_ref.estrutura_posicao_txt(
                modo, "resultado_incompleto", pernas=", ".join(str(i) for i in sem_cotacao)))
        if acao_falta:
            partes.append(skill_ref.estrutura_posicao_txt(modo, "acao_sem_cotacao"))
        texto = " ".join(t for t in partes if t)
    resultado = {
        "total": total,
        "acoes": acoes["resultado"] if acoes else None,
        "pernasCotadas": round(sum(cotadas), 2) if cotadas else None,
        "incompleto": incompleto,
        "pernasSemCotacao": sem_cotacao,
        "texto": texto,
    }

    saida_pernas = [{
        "id": p["id"], "tipo": p["tipo"], "lado": p["lado"], "strike": p["strike"],
        "vencimento": p["vencimento"], "quantidade": p["quantidade"],
        "premioEntrada": _r2(p["premioEntrada"]), "premioAtual": _r2(p["premioAtual"]),
        "origemPremio": p["origemPremio"], "origemTexto": p["origemTexto"],
        "resultado": p["resultado"],
    } for p in pernas]

    return {
        "underlying": underlying,
        "nome": nome,
        "nomeTexto": skill_ref.estrutura_posicao_txt(
            modo, f"nome_{nome}" if nome else "nome_fora_da_biblioteca"),
        "pernas": saida_pernas,
        "acoes": acoes,
        "resultado": resultado,
        "incompleto": incompleto,
    }
