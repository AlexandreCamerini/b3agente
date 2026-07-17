"""FASE 4 (1.3) — Radar diário: uma varredura automática por dia + sob demanda.

Comportamento aprovado:
  • O servidor roda UMA varredura automática por dia útil às B3_RADAR_DAILY_HHMM
    (default 08:45 BRT — candle diário da véspera fechado, antes do pregão).
  • O resultado fica armazenado GLOBALMENTE (kv sem user_id — o universo é o
    mesmo para todos); abrir a aba Radar passa a servir o armazenado na hora.
  • Varredura manual (?force=1) recomputa e SUBSTITUI o resultado do dia.
  • Push opcional "Radar do dia pronto" para quem tem token registrado
    (mesma permissão do push do Operador IA — best-effort, nunca derruba).

Reusa a infraestrutura existente: roda DENTRO do scheduler_loop do agent.py
(sem segundo scheduler) e todo o custo de rede passa pelo candle_cache do
scanner (delta-only + fallback stale — resiliente ao rate-limit do Yahoo).
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import db, scanner
from . import candles as candles_mod

BRT = timezone(timedelta(hours=-3))
HHMM_DEFAULT = "08:45"

# Telemetria em memória (aparece no status_snapshot da Observabilidade)
LAST_DAILY = {"date": None, "atLabel": None, "duracaoS": None, "erro": None}


def _hhmm() -> str:
    raw = (os.environ.get("B3_RADAR_DAILY_HHMM") or HHMM_DEFAULT).strip()
    try:
        h, m = raw.split(":")
        assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
        return f"{int(h):02d}:{int(m):02d}"
    except Exception:  # noqa: BLE001 — valor inválido cai no default
        return HHMM_DEFAULT


def enabled() -> bool:
    return not os.environ.get("B3_RADAR_DAILY_OFF")


def should_run(now: Optional[datetime] = None, last_date: Optional[str] = None) -> bool:
    """Gating PURO (testável): dia útil, horário atingido, ainda não rodou hoje."""
    now = now or datetime.now(BRT)
    if now.weekday() >= 5:  # sáb/dom — feriado B3 apenas re-serve o de sexta
        return False
    hh, mm = _hhmm().split(":")
    alvo = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    if now < alvo:
        return False
    return last_date != now.date().isoformat()


def _key(period: str) -> str:
    return "radarDaily:" + period


def store_result(conn, period: str, payload: dict, origem: str) -> dict:
    """Grava o resultado do dia (cópia anotada — nunca muta o cache do scanner)."""
    now = datetime.now(BRT)
    annotated = dict(payload)
    annotated["scanAt"] = now.isoformat()
    annotated["scanAtLabel"] = now.strftime("%d/%m %H:%M")
    annotated["scanOrigem"] = origem  # "automática" | "manual"
    annotated["scanAuto"] = origem == "automática"
    db.kv_set(conn, _key(period), annotated, user_id=None)
    if origem == "automática":
        db.kv_set(conn, "radarDailyLastRun", now.date().isoformat(), user_id=None)
    return annotated


def get_stored(conn, period: str) -> Optional[dict]:
    hit = db.kv_get(conn, _key(period), user_id=None)
    return hit if isinstance(hit, dict) and hit.get("results") is not None else None


def last_run_date(conn) -> Optional[str]:
    return db.kv_get(conn, "radarDailyLastRun", user_id=None)


def _push_audience(conn) -> list:
    """Usuários com token de push registrado (mesma permissão do Operador IA)."""
    try:
        rows = conn.execute("SELECT id FROM users").fetchall()
    except Exception:  # noqa: BLE001 — sem tabela (modo legado) = sem audiência
        return []
    out = []
    for (uid,) in rows:
        if db.kv_get(conn, "pushTokens", [], user_id=uid):
            out.append(uid)
    return out


PUSH_TOP_N = 3          # qa/43: quantos destaques cabem no corpo do push


def push_body(payload: dict, top: int = PUSH_TOP_N) -> str:
    """qa/43: corpo do push do Radar diário.

    Antes dizia só "Varredura automática concluída: 74 ativo(s) analisados" —
    o ranking JÁ estava calculado (run_scan ordena por confluência) e o push
    jogava fora, mandando o usuário garimpar 74 linhas. Agora nomeia o top-N.

    O VEREDITO é obrigatório, não enfeite: o ranking é por confluência PURA e
    não separa alta de baixa (scanner: sort por -confluencia). O topo pode ser
    "Estudar baixa" — foi o caso de VALE3 100% em 16/07. Dizer só "VALE3 100%"
    faria o usuário ler como alta e comprar na queda. Vocabulário do produto
    ("confluência" = aderência ao padrão de estudo, como o DISCLAIMER define),
    sem verbo de ordem de operação — o guardrail regulatório vale aqui também.
    """
    results = payload.get("results") or []
    n = len(results)
    destaques = [r for r in results[:top]
                 if (r.get("confluencia") or 0) > 0 and r.get("ticker") and r.get("veredito")]
    if not destaques:
        return f"Varredura concluída: {n} ativo(s) analisados, nenhum setup em destaque hoje. Abra o Radar para estudar."
    itens = " · ".join(f"{r['ticker']} {int(r['confluencia'])}% {str(r['veredito']).lower()}"
                       for r in destaques)
    return f"Maior confluência: {itens}. Abra para ver o plano e o risco ({n} ativos analisados)."


async def run_daily(conn, fetch, notify_push=None, origem: str = "automática") -> dict:
    """Roda a varredura do dia, armazena e (opcional) avisa por push."""
    t0 = time.monotonic()
    period = candles_mod.normalize_period(None)
    payload = await scanner.run_scan(period=period, fetch=fetch)
    annotated = store_result(conn, period, payload, origem)
    LAST_DAILY.update(
        date=datetime.now(BRT).date().isoformat(),
        atLabel=annotated["scanAtLabel"],
        duracaoS=round(time.monotonic() - t0, 1),
        erro=None,
    )
    if notify_push and origem == "automática":
        corpo = push_body(payload)   # qa/43: nomeia o top-N em vez de só contar
        for uid in _push_audience(conn):
            try:
                await notify_push(uid, "Radar do dia 📡", corpo)
            except Exception:  # noqa: BLE001 — push é best-effort
                pass
    return annotated


async def maybe_run(conn, fetch, notify_push=None) -> Optional[dict]:
    """Hook do scheduler: roda no máximo 1x/dia útil no horário configurado."""
    if not enabled():
        return None
    if not should_run(last_date=last_run_date(conn)):
        return None
    try:
        return await run_daily(conn, fetch, notify_push=notify_push)
    except Exception as e:  # noqa: BLE001 — nunca derruba o laço do agente
        LAST_DAILY["erro"] = str(e)[:200]
        print(f"[radar-daily] varredura automática falhou: {e}")
        return None
