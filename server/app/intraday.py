"""ADR-001 (item 7) — a passada INTRADAY do servidor.

Sem este módulo, toda a infraestrutura intraday construída em 30–31/07 fica
DORMENTE: a chave da vela com horário, a identidade por intervalo, o cache sem
L2, o descarte da barra em formação e a detecção de lacuna existem e nada os
exercita em produção.

Contrato, fixado nos ADRs e não negociável aqui:

  • GLOBAL, não por usuário (ADR-001 Decisão 3). 65 ativos, uma passada, custo
    O(1) no número de usuários. Uma varredura por posição/watchlist custaria
    O(usuários x ativos) e cresceria com o sucesso do produto.
  • Intervalo CANÔNICO `15m` (ADR-002 Decisão 5). A tríade completa vale na
    análise sob demanda; o Radar intraday roda num intervalo só, compartilhado.
  • Só DENTRO do pregão (`agent.in_market_hours`) — fora dele não há barra nova
    e a passada só queimaria requisição.
  • NÃO toca o caminho do Radar diário: chave de cache própria
    (`símbolo@15m`), chave de armazenamento própria, período próprio. O custo
    do diário fica exatamente como está.
  • Nunca derruba o laço do agente: qualquer falha vira log e telemetria.

Custo medido (31/07, do IP de produção): 65 requisições em 0,45 s a conc=16,
3,7 KB por ativo em `15m x 1d`. ~US$ 1/mês de infraestrutura.
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import db, technical_snapshot
from .agent import in_market_hours
from .scanner import get_universe

BRT = timezone(timedelta(hours=-3))

INTERVALO = "15m"          # ADR-002 Decisão 5: o canônico do Radar intraday
PERIODO = "1mo"            # janela do STU; com 15m dá ~638 velas (SMA200 com folga)
CONCORRENCIA = 8           # medido: 65 ativos em 0,45 s a conc=16; 8 é folgado
GAP_MIN_S = 240            # não repete a passada antes disso (laço acorda a 300 s)
CHAVE = "intradayPass"

# Telemetria em memória (aparece no status_snapshot da Observabilidade).
LAST_PASS = {"at": None, "atLabel": None, "duracaoS": None,
             "ativos": 0, "comLacuna": 0, "erros": 0, "erro": None}


def enabled() -> bool:
    """Kill switch próprio: desligar o intraday NÃO desliga o Operador."""
    return not os.environ.get("B3_INTRADAY_OFF")


def should_run(now: Optional[datetime] = None, last_ts: Optional[float] = None,
               agora_mono: Optional[float] = None) -> bool:
    """Gating PURO (testável): pregão aberto e passou o intervalo mínimo."""
    if not in_market_hours(now or datetime.now(BRT)):
        return False
    if last_ts is None:
        return True
    return (agora_mono if agora_mono is not None else time.monotonic()) - last_ts >= GAP_MIN_S


def get_stored(conn) -> Optional[dict]:
    hit = db.kv_get(conn, CHAVE, user_id=None)
    return hit if isinstance(hit, dict) and hit.get("ativos") is not None else None


def _resumo(snap: dict) -> dict:
    """O que a passada guarda por ativo. Enxuto de propósito: o STU completo
    fica no cache de snapshot; aqui vai só o que o Radar intraday exibe e o que
    a F1 vai consultar para decidir timing."""
    sres = snap.get("setups") or {}
    lac = snap.get("lacunas") or {}
    return {
        "ticker": snap.get("ticker"),
        "snapshotId": snap.get("snapshotId"),
        # ADR-001 Decisão 2: `asOf` é a última barra FECHADA. É este carimbo que
        # a interface tem que mostrar — sem ele a frase insinua tempo real.
        "asOf": snap.get("asOf"),
        "barraEmFormacao": snap.get("barraEmFormacao"),
        "close": snap.get("close"),
        "veredito": sres.get("veredito"),
        "confluencia": sres.get("confluencia"),
        "melhorSetup": sres.get("melhor"),
        "scoreTecnico": snap.get("scoreTecnico"),
        # ADR-001 item 1d: série furada mente com cara de certa.
        "lacuna": bool(lac.get("temLacuna")),
        "cobertura": lac.get("cobertura"),
    }


async def run_pass(conn, fetch, universo: Optional[list] = None) -> dict:
    """Uma passada intraday sobre o universo. `fetch(ticker, rng, interval)` é
    injetado (produção: candle_provider.get_history; fake nos testes)."""
    t0 = time.monotonic()
    uni = universo if universo is not None else get_universe()
    sem = asyncio.Semaphore(CONCORRENCIA)
    resultados, erros = [], []

    async def um(tk):
        async with sem:
            try:
                snap = await technical_snapshot.get(
                    tk, PERIODO,
                    lambda rng, s=tk: fetch(s, rng, INTERVALO),
                    interval=INTERVALO,
                )
                resultados.append(_resumo(snap))
            except Exception as e:  # noqa: BLE001 — 1 ativo ruim não derruba a passada
                erros.append({"ticker": tk, "erro": str(e)[:120] or type(e).__name__})

    await asyncio.gather(*(um(t) for t in uni))
    resultados.sort(key=lambda r: (-(r.get("confluencia") or 0), r.get("ticker") or ""))
    agora = datetime.now(BRT)
    com_lacuna = sum(1 for r in resultados if r.get("lacuna"))
    payload = {
        "interval": INTERVALO,
        "period": PERIODO,
        "at": agora.isoformat(),
        "atLabel": agora.strftime("%d/%m %H:%M"),
        "universo": len(uni),
        "ativos": len(resultados),
        "comLacuna": com_lacuna,
        "resultados": resultados,
        "erros": erros,
    }
    db.kv_set(conn, CHAVE, payload, user_id=None)   # GLOBAL: sem user_id
    LAST_PASS.update(at=agora.isoformat(), atLabel=payload["atLabel"],
                     duracaoS=round(time.monotonic() - t0, 2), ativos=len(resultados),
                     comLacuna=com_lacuna, erros=len(erros), erro=None)
    return payload


async def maybe_run(conn, fetch, last_ts: Optional[float] = None) -> Optional[dict]:
    """Hook do `scheduler_loop`. Devolve o payload se rodou, None se pulou."""
    if not enabled() or not should_run(last_ts=last_ts):
        return None
    try:
        return await run_pass(conn, fetch)
    except Exception as e:  # noqa: BLE001 — nunca derruba o laço do agente
        LAST_PASS["erro"] = str(e)[:200]
        print(f"[intraday] passada falhou: {e}")
        return None
