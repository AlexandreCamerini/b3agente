"""Orçamento de requisições da brapi (ADR-008, Fase 2 do qa/43).

A cota do plano gratuito é finita (15.000/mês, medida em 11/08/2026) e uma
recusa por plano DEBITA cota — então o controle é local e ANTES da chamada.
Política decidida no ADR-008:

  • teto diário = B3_BRAPI_COTA_MES ÷ 21 pregões (~700 com a cota padrão);
  • fatias: spot ~57%, delta diário ~21%, fundamentos ~4%, reserva o resto;
  • fatia estourada consome da reserva; reserva esgotada = fatia bloqueada;
  • SOFT STOP a 80% da fatia (`degradado()` → quem chama alonga TTL);
  • HARD STOP a 100% do teto do dia (brapi silencia até o próximo pregão);
  • consumo só na janela de pregão da B3 (seg–sex, 10:00–17:15 BRT — inclui a
    passada de delta pós-fechamento). Fora dela, `pode_gastar()` é False.

Persistência: contador do dia no `kv` do SQLite (sobrevive a deploy), mesma
postura do L2 de `candle_cache` — a conexão é injetada no boot e a ausência
dela degrada para memória, nunca derruba. O header `x-ratelimit-remaining`
(capturado por `brapi.py` a cada resposta) é a VERDADE da brapi; o contador
local é a previsão — `snapshot()` expõe os dois para reconciliação a olho.
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

BRT = timezone(timedelta(hours=-3))
PREGOES_MES = 21
_FRACOES = {"spot": 400 / 700, "delta": 150 / 700, "fund": 30 / 700}
_SOFT = 0.8

_JANELA_INI = 10 * 60          # 10:00 BRT
_JANELA_FIM = 17 * 60 + 15     # 17:15 BRT (leilão de fechamento + delta)

_DB_CONN = None
_DB_ENABLED = False
_estado: dict = {}   # {"dia": "AAAA-MM-DD", "fatias": {nome: gasto}, "total": n}


def configure_db(conn=None, enabled: bool = True) -> None:
    global _DB_CONN, _DB_ENABLED
    _DB_CONN = conn
    _DB_ENABLED = bool(enabled and conn is not None)


def cota_mes() -> int:
    try:
        return max(0, int(os.environ.get("B3_BRAPI_COTA_MES", "15000")))
    except ValueError:
        return 15000


def teto_dia() -> int:
    return cota_mes() // PREGOES_MES


def fatia_limite(fatia: str) -> int:
    f = _FRACOES.get(fatia)
    if f is None:                      # fatia desconhecida = reserva
        return _reserva_limite()
    return int(teto_dia() * f)


def _reserva_limite() -> int:
    return teto_dia() - sum(int(teto_dia() * f) for f in _FRACOES.values())


def _hoje(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(BRT)).strftime("%Y-%m-%d")


def em_pregao(now: Optional[datetime] = None) -> bool:
    """Janela de consumo: dia útil (seg–sex), 10:00–17:15 BRT. Feriado B3 sem
    pregão não gera demanda de spot — o custo de tratá-lo como útil é ~zero."""
    n = now or datetime.now(BRT)
    if n.weekday() >= 5:
        return False
    minutos = n.hour * 60 + n.minute
    return _JANELA_INI <= minutos <= _JANELA_FIM


# -- persistência -----------------------------------------------------------
def _kv_key(dia: str) -> str:
    return "brapiBudget:" + dia


def _carrega(dia: str) -> None:
    global _estado
    if _estado.get("dia") == dia:
        return
    _estado = {"dia": dia, "fatias": {}, "total": 0}
    if not _DB_ENABLED:
        return
    try:
        row = _DB_CONN.execute("SELECT value FROM kv WHERE key = ?",
                               (_kv_key(dia),)).fetchone()
        if row:
            d = json.loads(row[0])
            _estado["fatias"] = dict(d.get("fatias") or {})
            _estado["total"] = int(d.get("total") or 0)
    except Exception:  # noqa: BLE001 — contador é proteção, nunca derruba
        pass


def _persiste() -> None:
    if not _DB_ENABLED:
        return
    try:
        _DB_CONN.execute(
            "INSERT INTO kv(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (_kv_key(_estado["dia"]),
             json.dumps({"fatias": _estado["fatias"], "total": _estado["total"]})))
        _DB_CONN.commit()
    except Exception:  # noqa: BLE001
        pass


# -- API --------------------------------------------------------------------
def pode_gastar(fatia: str, now: Optional[datetime] = None) -> bool:
    """True se a chamada à brapi está autorizada agora, para esta fatia."""
    if not em_pregao(now):
        return False
    _carrega(_hoje(now))
    if _estado["total"] >= teto_dia():          # hard stop do dia
        return False
    gasto = _estado["fatias"].get(fatia, 0)
    if gasto < fatia_limite(fatia):
        return True
    # fatia cheia: consome da reserva enquanto houver
    reserva_gasta = _estado["fatias"].get("reserva", 0)
    return reserva_gasta < _reserva_limite()


def debita(fatia: str, n: int = 1, now: Optional[datetime] = None) -> None:
    _carrega(_hoje(now))
    gasto = _estado["fatias"].get(fatia, 0)
    alvo = fatia if gasto < fatia_limite(fatia) else "reserva"
    _estado["fatias"][alvo] = _estado["fatias"].get(alvo, 0) + n
    _estado["total"] += n
    _persiste()


def degradado(fatia: str, now: Optional[datetime] = None) -> bool:
    """SOFT STOP: a fatia passou de 80% — quem chama alonga o TTL do cache."""
    _carrega(_hoje(now))
    lim = fatia_limite(fatia)
    return lim > 0 and _estado["fatias"].get(fatia, 0) >= lim * _SOFT


def snapshot(now: Optional[datetime] = None) -> dict:
    """Para /api/status: previsão local + verdade do header, lado a lado."""
    from . import brapi   # import tardio: evita ciclo em boot parcial
    _carrega(_hoje(now))
    return {
        "dia": _estado["dia"],
        "tetoDia": teto_dia(),
        "cotaMes": cota_mes(),
        "total": _estado["total"],
        "fatias": {f: {"gasto": _estado["fatias"].get(f, 0),
                       "limite": fatia_limite(f),
                       "degradado": degradado(f, now)}
                   for f in (*_FRACOES, "reserva")},
        "emPregao": em_pregao(now),
        # o que a PRÓPRIA brapi disse na última resposta (verdade > previsão)
        "headerRateLimit": dict(brapi.LAST_RATELIMIT),
    }


def reset() -> None:
    """Para testes."""
    global _estado
    _estado = {}
