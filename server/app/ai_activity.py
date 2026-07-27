"""qa/45 — Atividade da IA: custo estimado (R$) + histórico de comportamento.

Cada chamada de LLM (N1 Radar, N2 Análise, N3 Carteira) vira UMA linha de
ledger, persistida no KV ESCOPADO por user_id (seção `aiActivity`). Os TOKENS
já eram capturados por chamada (qa/42, llm.record_usage) — aqui adicionamos a
camada de PREÇO (tokens → R$) e a persistência por chamada + acumulado.

- `total` (nunca podado) = acumulado real desde o 1º uso.
- `recentes` (capado) = as últimas N chamadas para o histórico visível.

Preços são ESTIMATIVA (list price público × câmbio), centralizados e editáveis
aqui — a UI sempre rotula "custo estimado". Modelo desconhecido cai num preço
de referência, marcado. Stdlib, testável offline.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from . import db

SECTION = "aiActivity"
CAP = 200          # linhas de histórico visíveis (o acumulado usa `total`, não a lista)
MAX_DIAS = 180
BRT = timezone(timedelta(hours=-3))

# Câmbio usado na estimativa (editável). Mantido explícito para o usuário saber.
USD_BRL = 5.40

# Preço LIST público por 1 MILHÃO de tokens (USD), (entrada, saída). ESTIMATIVA
# — muda com o tempo; centralizado para atualizar num lugar só. Match por
# prefixo do id do modelo (o mais específico primeiro).
PRECOS_USD_POR_MI = [
    ("claude-opus", (15.0, 75.0)),
    ("claude-sonnet", (3.0, 15.0)),
    ("claude-haiku", (0.80, 4.0)),
    ("claude-fable", (1.0, 5.0)),      # tier rápido — estimativa
    ("gpt-4o-mini", (0.15, 0.60)),
    ("gpt-4o", (2.5, 10.0)),
    ("gpt-5", (2.5, 10.0)),
    ("gpt-4", (10.0, 30.0)),
    ("o1", (15.0, 60.0)),
    ("gemini-1.5-flash", (0.075, 0.30)),
    ("gemini-1.5-pro", (1.25, 5.0)),
    ("gemini-2", (1.25, 5.0)),
    ("gemini", (1.25, 5.0)),
]
_FALLBACK_USD_POR_MI = (3.0, 15.0)   # referência (sonnet-like) p/ modelo desconhecido


def _preco_usd_por_mi(model: str):
    m = str(model or "").lower()
    for prefixo, preco in PRECOS_USD_POR_MI:
        if prefixo in m:
            return preco
    return _FALLBACK_USD_POR_MI


def custo_estimado(model: str, in_tok: int, out_tok: int) -> float:
    """R$ estimado de UMA chamada. Puro. Nunca levanta."""
    pin, pout = _preco_usd_por_mi(model)
    usd = (int(in_tok or 0) / 1_000_000.0) * pin + (int(out_tok or 0) / 1_000_000.0) * pout
    return round(usd * USD_BRL, 4)


def _hoje() -> str:
    return datetime.now(BRT).date().isoformat()


def _load(conn, scope) -> dict:
    d = db.kv_get(conn, SECTION, None, user_id=scope)
    if not isinstance(d, dict):
        d = {}
    d.setdefault("total", {"custo": 0.0, "calls": 0, "inTok": 0, "outTok": 0, "desde": None})
    d.setdefault("recentes", [])
    return d


def registrar(conn, *, scope, ticker: str, tipo: str, model: str,
              in_tok: int, out_tok: int, at: Optional[str] = None) -> None:
    """Grava UMA chamada no ledger + soma no acumulado. Best-effort: nunca
    derruba a análise (o chamador envolve em try/except mesmo assim)."""
    in_tok, out_tok = int(in_tok or 0), int(out_tok or 0)
    if in_tok == 0 and out_tok == 0:
        return  # provedor sem `usage` no corpo — nada a contabilizar
    custo = custo_estimado(model, in_tok, out_tok)
    at = at or datetime.now(timezone.utc).isoformat()
    d = _load(conn, scope)
    t = d["total"]
    t["custo"] = round(float(t.get("custo") or 0.0) + custo, 4)
    t["calls"] = int(t.get("calls") or 0) + 1
    t["inTok"] = int(t.get("inTok") or 0) + in_tok
    t["outTok"] = int(t.get("outTok") or 0) + out_tok
    if not t.get("desde"):
        t["desde"] = at
    linha = {"ticker": ticker, "tipo": tipo, "model": model,
             "inTok": in_tok, "outTok": out_tok, "custo": custo, "at": at}
    recentes = [linha] + list(d.get("recentes") or [])
    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_DIAS)).isoformat()
    recentes = [r for r in recentes if (r.get("at") or "") >= cutoff][:CAP]
    d["recentes"] = recentes
    db.kv_set(conn, SECTION, d, user_id=scope)


def registrar_uso(conn, *, scope, ticker: str, tipo: str, usos) -> None:
    """Registra a partir da lista coletada por llm.collect_usage() —
    [(in, out, model), ...] de UMA operação (a maioria tem 1 chamada; o N1 deep
    pode ter mais). Soma os tokens e usa o modelo predominante."""
    itens = [u for u in (usos or []) if u]
    if not itens:
        return
    in_tot = sum(int(u[0] or 0) for u in itens)
    out_tot = sum(int(u[1] or 0) for u in itens)
    model = itens[-1][2] if len(itens[-1]) > 2 else "?"
    registrar(conn, scope=scope, ticker=ticker, tipo=tipo, model=model,
              in_tok=in_tot, out_tok=out_tot)


def snapshot(conn, scope) -> dict:
    """Acumulado + hoje + histórico recente. Puro (só leitura)."""
    d = _load(conn, scope)
    hoje = _hoje()
    # "hoje" = dia BRT do timestamp de cada linha recente.
    do_dia = []
    for r in d["recentes"]:
        try:
            dia = datetime.fromisoformat(r["at"]).astimezone(BRT).date().isoformat()
        except Exception:  # noqa: BLE001
            continue
        if dia == hoje:
            do_dia.append(r)
    custo_hoje = round(sum(float(r.get("custo") or 0.0) for r in do_dia), 4)
    return {
        "total": d["total"],
        "hoje": {"custo": custo_hoje, "calls": len(do_dia)},
        "recentes": d["recentes"][:60],
        "usdBrl": USD_BRL,
    }
