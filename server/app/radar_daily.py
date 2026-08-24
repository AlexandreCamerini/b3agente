"""FASE 4 (1.3) — Radar diário: uma varredura automática por dia + sob demanda.

Comportamento aprovado:
  • O servidor roda UMA varredura automática por dia útil às B3_RADAR_DAILY_HHMM
    (default 08:45 BRT — candle diário da véspera fechado, antes do pregão).
  • O resultado fica armazenado GLOBALMENTE (kv sem user_id — o universo é o
    mesmo para todos); abrir a aba Radar passa a servir o armazenado na hora.
  • Varredura manual (?force=1) recomputa e SUBSTITUI o resultado do dia.
  • Push opcional de PRÉVIA PRÉ-ABERTURA para quem tem token registrado
    (mesma permissão do push do Operador IA — best-effort, nunca derruba).
    Título e corpo saem de `skill_ref.PUSH_RADAR`: às 08:45 o pregão ainda não
    abriu, e o texto tem que dizer isso (260824-i45, item 6) sob pena de ler
    como alerta fora de hora.
  • O mesmo corpo vira EVENTO em `agent.events` para a mesma audiência — o
    rastro durável da tela "EVENTOS E AVISOS RECENTES", independente de a
    entrega do push dar certo.

Reusa a infraestrutura existente: roda DENTRO do scheduler_loop do agent.py
(sem segundo scheduler) e todo o custo de rede passa pelo candle_cache do
scanner (delta-only + fallback stale — resiliente ao rate-limit do Yahoo).
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import db, scanner, skill_ref, store
from . import candles as candles_mod

BRT = timezone(timedelta(hours=-3))
HHMM_DEFAULT = "08:45"
# Hora em que a vela DIÁRIA de um pregão está consolidada (após o leilão de
# fechamento e o after-market). Não é o horário do pregão: é o instante a
# partir do qual uma leitura que não enxergou aquele dia está atrasada.
FECHAMENTO_H = 18

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


def get_bruto(conn, period: str) -> Optional[dict]:
    """O armazenado como está, sem julgar validade — é nele que a herança
    escreve (`merge_leituras`) e dele que a telemetria lê."""
    hit = db.kv_get(conn, _key(period), user_id=None)
    return hit if isinstance(hit, dict) and hit.get("results") is not None else None


def ultimo_fechamento(now: Optional[datetime] = None) -> Optional[datetime]:
    """Último fechamento de pregão já consolidado antes de `now`."""
    now = now or datetime.now(BRT)
    for i in range(0, 10):          # 10 dias cobrem qualquer emenda de feriado
        d = now - timedelta(days=i)
        if d.weekday() >= 5:
            continue
        fech = d.replace(hour=FECHAMENTO_H, minute=0, second=0, microsecond=0)
        if fech <= now:
            return fech
    return None


def esta_vencida(scan_at: Optional[str], now: Optional[datetime] = None) -> bool:
    """A leitura armazenada venceu quando um pregão FECHOU depois dela.

    Este é o portão que faltava. `get_stored` só perguntava se o dict tinha
    `results`, então sábado e domingo (quando `should_run` não roda) o payload
    de sexta 08:45 — que enxergou até quinta — era servido indefinidamente,
    enquanto a Watchlist recalculava e já lia o fechamento de sexta. Resultado:
    o mesmo papel com dois vereditos ao mesmo tempo.

    Não é uma janela de tempo arbitrária ("expira em 24h"): o que invalida uma
    leitura técnica é o mercado ter produzido um candle que ela não viu.

    Carimbo ausente ou ilegível conta como vencido — servir sem saber a idade é
    afirmar o que não se sabe.
    """
    if not scan_at:
        return True
    try:
        t = datetime.fromisoformat(str(scan_at))
    except (TypeError, ValueError):
        return True
    if t.tzinfo is None:
        t = t.replace(tzinfo=BRT)
    fech = ultimo_fechamento(now)
    return bool(fech and t < fech)


def get_stored(conn, period: str, now: Optional[datetime] = None) -> Optional[dict]:
    """A leitura que o Radar pode servir — ou None, se um pregão já a venceu.

    Devolver None é o contrato: quem chamou recomputa. É mais barato recomputar
    uma vez por pregão fechado do que exibir duas verdades sobre o mesmo ativo.
    """
    hit = get_bruto(conn, period)
    if hit is None:
        return None
    return None if esta_vencida(hit.get("scanAt"), now=now) else hit


def _ordena(results: list) -> list:
    """Mesma chave do `scanner.run_scan` — confluência, intensidade, ticker."""
    return sorted(results, key=lambda r: (-(r.get("confluencia") or 0),
                                          -(r.get("score_tecnico") or 0),
                                          r.get("ticker") or ""))


def merge_leituras(conn, period: str, rows: Optional[list]) -> Optional[dict]:
    """"Atualizou o ativo numa tela, todas as outras herdam."

    A Watchlist recalcula a cada request (subconjunto pequeno, barato); o Radar
    serve o armazenado. Sem esta herança, durante o próprio pregão as duas
    divergem de novo — o diário mantém de propósito a vela do dia em formação
    (`technical_snapshot._descarta_barra_em_formacao`), então a leitura viva
    anda durante o dia enquanto o retrato das 08:45 fica parado.

    Escreve no armazenado só o que de fato mudou (`snapshotId` diferente) e
    reordena, porque o Radar é rankeado por confluência. Custo: zero varredura
    nova — aproveita o que a outra tela já calculou.
    """
    bruto = get_bruto(conn, period)
    if bruto is None:
        return None
    novos = {r.get("ticker"): r for r in (rows or []) if isinstance(r, dict) and r.get("ticker")}
    if not novos:
        return bruto
    results = list(bruto.get("results") or [])
    mudou = False
    for i, r in enumerate(results):
        n = novos.get(r.get("ticker"))
        if n and n.get("snapshotId") and n.get("snapshotId") != r.get("snapshotId"):
            results[i] = n
            mudou = True
    if not mudou:
        return bruto
    atualizado = dict(bruto)
    atualizado["results"] = _ordena(results)
    db.kv_set(conn, _key(period), atualizado, user_id=None)
    return atualizado


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

    260824-i45 (item 6): o texto passa a declarar que é PRÉVIA PRÉ-ABERTURA.
    Este job roda às 08:45 por desenho (decisão D1) e o corpo não dizia isso,
    o que fazia o push ler como alerta fora de hora — e pior, sugeria preços
    que a abertura ainda pode mudar. O vocabulário vive em
    `skill_ref.PUSH_RADAR`; o texto novo ENVELOPA o de qa/43 (top-N, veredito,
    contagem), não o substitui.
    """
    results = payload.get("results") or []
    n = len(results)
    destaques = [r for r in results[:top]
                 if (r.get("confluencia") or 0) > 0 and r.get("ticker") and r.get("veredito")]
    if not destaques:
        return skill_ref.PUSH_RADAR["corpo_vazio"].replace("{n}", str(n))
    itens = " · ".join(f"{r['ticker']} {int(r['confluencia'])}% {str(r['veredito']).lower()}"
                       for r in destaques)
    return skill_ref.PUSH_RADAR["corpo_destaques"].replace("{itens}", itens).replace("{n}", str(n))


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
        # SEM `extra` aqui, e é deliberado (260824-i45): a prévia nomeia N
        # tickers e não tem destino único — eleger `destaques[0]` cometeria o
        # erro de ticker trocado que `agent.py:1008-1015` existe para evitar. E
        # `extra` só com `kind`, sem `t`, seria peso morto: `notify.js:382`
        # filtra por `^[A-Z]{4}\d{1,2}$` ANTES de chamar o handler, então um
        # payload sem `t` válido nunca chega a lugar nenhum. Rotear o toque por
        # `kind` exigiria mudar o contrato de navegação do cliente — fora de
        # escopo.
        #
        # Limite deliberado: o evento entra só para `_push_audience` (quem tem
        # token), a MESMA audiência do push — escrever para toda a base seria um
        # `kv_set` por usuário por dia sem push correspondente.
        for uid in _push_audience(conn):
            # `try` PRÓPRIO: o registro do evento é o rastro DURÁVEL (a tela
            # "EVENTOS E AVISOS RECENTES", App.jsx:4301); a entrega do push é
            # efêmera. Um `except` só, como antes, fazia a falha de um matar o
            # outro — e o Radar era o único call site sem rastro nenhum.
            try:
                store.push_events(conn, [{"time": store.now_str(), "kind": "info",
                                          "tag": "radar-diario", "text": corpo}], user_id=uid)
            except Exception:  # noqa: BLE001 — registro é best-effort
                pass
            try:
                await notify_push(uid, skill_ref.PUSH_RADAR["titulo"], corpo)
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
