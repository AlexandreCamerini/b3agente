"""Job de fechamento "Seu dia na bolsa" (Fase 51, plano 51-05).

POR QUE EXISTE (CONTEXT D-03/D-05/D-12): o app devolve ao usuário, no fim do
pregão, o que o mercado fez com o que ele viu (família 1, o "e se"), o que o
motor fez na carteira dele (família 2) e um fato raro do mercado (família 3).
Todo número do card sai do motor determinístico (`dia_na_bolsa_regras`,
`analysis_outcomes`, `store`); este módulo só ORQUESTRA: registra os setups
vistos (preços vindos do servidor, nunca do cliente — T-50-13), coleta candles
sem brapi, monta o card por conta, envia o push com consentimento e expõe as
leituras das rotas. Nenhuma chamada de LLM, nenhuma de brapi.

Molde: `snapshot_diario.py` (janela, idempotência por K_FEITAS, `maybe_run`
que nunca propaga). NÃO importa `agent` (regra de ciclo de import).

Chaves kv (contrato do plano):
  por escopo `diaNaBolsaVistos` — lista de vistos (ver `registrar_vistos`);
  por escopo `diaNaBolsa`       — card do dia ({data, vazio, familias, ...});
  globais `diaNaBolsaLastRun`, `diaNaBolsaFeitas`, `diaNaBolsaTentativa`,
          `diaNaBolsaYahooDia`.
"""
import asyncio
import os
import re
import time
from datetime import date as _date, datetime, timedelta, timezone
from typing import Optional

from . import (candle_cache, candles as candles_mod, db, obslog, pregao, radar_daily,
               setups, store, technical_snapshot)

BRT = timezone(timedelta(hours=-3))
JOB_NOME = "diaNaBolsa"
K_LAST_RUN = "diaNaBolsaLastRun"          # kv global: data do dia FECHADO
K_FEITAS = "diaNaBolsaFeitas"             # kv global: {"data", "escopos": [...]}
K_TENTATIVA = "diaNaBolsaTentativa"       # kv global: ISO da última passada
K_YAHOO_DIA = "diaNaBolsaYahooDia"        # kv global: {"data", "chamadas", "semDado"}
K_VISTOS = "diaNaBolsaVistos"             # kv por escopo
K_CARD = "diaNaBolsa"                     # kv por escopo
VISTOS_TETO = 300
TICKERS_MAX = 60
PODA_RESOLVIDO_DIAS = 28
PODA_ABERTO_DIAS = 40
ORIGENS = ("radar", "watchlist", "carteira")
_RE_TICKER = re.compile(r"^[A-Z]{4}[0-9]{1,2}$")


# ==========================================================================
# Registro de vistos (D-03)
# ==========================================================================
def _agora() -> datetime:
    """Ponto único de relógio (patchável em teste)."""
    return datetime.now(BRT)


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v


def _plano_do_snapshot(ticker: str):
    """Fallback do visto fora do Radar: motor sobre o cache local, SEM rede.
    Devolve (plano, dataBase, close) ou None."""
    cs = candle_cache.peek(ticker, "1d")
    if not cs:
        return None
    try:
        snap = technical_snapshot.build(ticker, cs, candles_mod.normalize_period(None))
        close = snap.get("close")
        if not _num(close):
            close = cs[-1].get("close")
        plano = setups.plano_do_resultado(snap.get("setups"), close=close)
    except Exception:  # noqa: BLE001 — sem histórico válido = sem plano
        return None
    return plano, str(cs[-1].get("date") or "")[:10], close


def _podar_vistos(vistos: list, hoje: _date) -> list:
    corte_res = (hoje - timedelta(days=PODA_RESOLVIDO_DIAS)).isoformat()
    corte_ab = (hoje - timedelta(days=PODA_ABERTO_DIAS)).isoformat()
    out = []
    for v in vistos:
        est = v.get("estado")
        if isinstance(est, dict) and est.get("aberto") is False:
            if str(est.get("resolvidoEm") or v.get("vistoEm") or "") < corte_res:
                continue
        elif str(v.get("dataBase") or "") < corte_ab:
            continue
        out.append(v)
    out.sort(key=lambda v: str(v.get("vistoEm") or ""))
    return out[-VISTOS_TETO:]


def ler_vistos(conn, uid: str) -> list:
    v = db.kv_get(conn, K_VISTOS, [], user_id=uid)
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def registrar_vistos(conn, uid: str, tickers: list, origem: str,
                     agora: Optional[datetime] = None) -> dict:
    """Registra, para a conta `uid`, os setups que ela viu (D-03).

    Os preços (entrada/stop/alvo) vêm SEMPRE do servidor: da linha do arquivo
    do Radar do dia (`radar_daily.arquivo_ate`) ou, fora do Radar, do motor
    sobre o cache local (`technical_snapshot` + `setups.plano_do_resultado`).
    A função não recebe preço: o corpo do cliente nunca decide o número
    (T-50-13/T-51-11). Devolve {"registrados", "semPlano", "ignorados"}.
    """
    if origem not in ORIGENS:
        raise ValueError("origem inválida")
    if not isinstance(tickers, (list, tuple)):
        raise ValueError("tickers deve ser uma lista")
    if len(tickers) > TICKERS_MAX:
        raise ValueError(f"no máximo {TICKERS_MAX} tickers por chamada")
    if not uid:
        raise ValueError("conta obrigatória")  # nunca o balde anônimo (T-51-12)
    agora = agora or _agora()
    hoje = agora.date()
    hoje_iso = hoje.isoformat()

    res = {"registrados": 0, "semPlano": 0, "ignorados": 0}
    arq = radar_daily.arquivo_ate(conn, hoje_iso)
    por_ticker = {}
    base_arq = None
    if arq:
        data_arq, dados = arq
        base_arq = dados.get("dataBase") or data_arq
        por_ticker = {l.get("ticker"): l for l in (dados.get("linhas") or []) if isinstance(l, dict)}

    vistos = ler_vistos(conn, uid)
    chaves = {(v.get("ticker"), v.get("setup"), v.get("dataBase")) for v in vistos}
    vistos_acao = False
    vistos_no_lote = set()
    for bruto in tickers:
        t = str(bruto or "").strip().upper()
        if not _RE_TICKER.match(t) or t in vistos_no_lote:
            res["ignorados"] += 1
            continue
        vistos_no_lote.add(t)
        linha = por_ticker.get(t)
        if linha:
            novo = {"setup": linha.get("setup"), "dataBase": str(base_arq)[:10],
                    "entrada": linha.get("entrada"), "stop": linha.get("stop"),
                    "alvo": linha.get("alvo"), "entradaAMercado": bool(linha.get("entradaAMercado")),
                    "precoBase": linha.get("close"), "fonte": "radar"}
        else:
            snap = _plano_do_snapshot(t)
            plano = snap[0] if snap else None
            if (not plano or str(plano.get("decisao") or "").upper() not in ("COMPRAR", "VENDER")
                    or not all(_num(plano.get(k)) for k in ("entrada", "stop", "alvo")) or not snap[1]):
                res["semPlano"] += 1
                continue
            novo = {"setup": plano.get("setup"), "dataBase": snap[1],
                    "entrada": plano["entrada"], "stop": plano["stop"], "alvo": plano["alvo"],
                    "entradaAMercado": str(plano.get("tipo") or "").startswith("a mercado"),
                    "precoBase": snap[2] if _num(snap[2]) else None, "fonte": "snapshot"}
        if not novo.get("setup") or not _num(novo.get("entrada")) or not _num(novo.get("stop")) \
                or not _num(novo.get("alvo")):
            res["semPlano"] += 1
            continue
        if (t, novo["setup"], novo["dataBase"]) in chaves:
            continue  # já visto (dedupe): não conta como novo registro
        novo.update({"ticker": t, "origem": origem, "vistoEm": hoje_iso, "estado": None})
        vistos.append(novo)
        chaves.add((t, novo["setup"], novo["dataBase"]))
        res["registrados"] += 1
        vistos_acao = True

    vistos = _podar_vistos(vistos, hoje)
    if vistos_acao or vistos != ler_vistos(conn, uid):
        db.kv_set(conn, K_VISTOS, vistos, user_id=uid)
    return res
