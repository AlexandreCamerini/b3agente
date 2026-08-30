"""Orçamento de requisições do mydata (Fase 9, Plano 01).

A chave de produção do Boris+ tem cota combinada por DUAS janelas — 60/min e
2.000/dia (`~/dev/cvm-financas/docs/contrato-consumidor.md`). Este módulo
copia a estrutura de `server/app/brapi_budget.py` (memória→DB→env, contador
do dia persistido no `kv`) com três diferenças deliberadas:

1. Duas janelas, não uma. O minuto é uma janela FIXA em memória (chave
   "AAAA-MM-DD HH:MM") — um minuto não precisa sobreviver a deploy, e
   persistir custaria escrita por chamada. O dia persiste no `kv`, mesmo
   UPSERT de `brapi_budget._persiste()`.
2. Sem fatias. `brapi_budget` divide spot/delta/fundamentos; aqui há um
   cliente só (`mydata_client.py`) servindo dois tipos de dado (candles e
   opções) sob uma cota combinada. `pode_gastar()`/`debita()` recebem só
   `n: int`, sem nome de fatia.
3. Sem gate de pregão. `brapi_budget` tem um gate de janela de negociação
   (função homônima do nome do dia útil B3) que bloqueia fora do horário
   porque o spot só faz sentido com mercado aberto. O dado do
   mydata é EOD (fechamento do COTAHIST) e o usuário navega fora do pregão —
   este módulo DELIBERADAMENTE não tem gate de horário. Não copiar esse gate
   de volta para cá.
"""
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

BRT = timezone(timedelta(hours=-3))
QUOTA_MIN_DEFAULT = 60
QUOTA_DIA_DEFAULT = 2000
# Teto ÚTIL local: o hub é a verdade e o contador local é previsão — gastar
# 100% da previsão garante bater no 429 do outro lado antes de o contador
# local perceber. Expor os dois números (previsão vs. cota real) em
# snapshot().
MARGEM = 0.9
_SOFT = 0.8

_DB_CONN = None
_DB_ENABLED = False
_estado: dict = {}   # {"dia": "AAAA-MM-DD", "gasto": n}  -- persistido no kv
_minuto: dict = {}   # {"chave": "AAAA-MM-DD HH:MM", "gasto": n}  -- só memória


def configure_db(conn=None, enabled: bool = True) -> None:
    global _DB_CONN, _DB_ENABLED
    _DB_CONN = conn
    _DB_ENABLED = bool(enabled and conn is not None)


def quota_min() -> int:
    try:
        return max(0, int(os.environ.get("MYDATA_QUOTA_MIN", str(QUOTA_MIN_DEFAULT))))
    except ValueError:
        return QUOTA_MIN_DEFAULT


def quota_dia() -> int:
    try:
        return max(0, int(os.environ.get("MYDATA_QUOTA_DIA", str(QUOTA_DIA_DEFAULT))))
    except ValueError:
        return QUOTA_DIA_DEFAULT


def _teto_util_min() -> int:
    return int(quota_min() * MARGEM)


def _teto_util_dia() -> int:
    return int(quota_dia() * MARGEM)


def _hoje(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(BRT)).strftime("%Y-%m-%d")


def _chave_minuto(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(BRT)).strftime("%Y-%m-%d %H:%M")


# -- persistência do contador do DIA -----------------------------------------
def _kv_key(dia: str) -> str:
    return "mydataBudget:" + dia


def _carrega(dia: str) -> None:
    global _estado
    if _estado.get("dia") == dia:
        return
    _estado = {"dia": dia, "gasto": 0}
    if not _DB_ENABLED:
        return
    try:
        row = _DB_CONN.execute("SELECT value FROM kv WHERE key = ?",
                               (_kv_key(dia),)).fetchone()
        if row:
            d = json.loads(row[0])
            _estado["gasto"] = int(d.get("gasto") or 0)
    except Exception:  # noqa: BLE001 — contador é proteção, nunca derruba
        pass


def _persiste() -> None:
    if not _DB_ENABLED:
        return
    try:
        _DB_CONN.execute(
            "INSERT INTO kv(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (_kv_key(_estado["dia"]), json.dumps({"gasto": _estado["gasto"]})))
        _DB_CONN.commit()
    except Exception:  # noqa: BLE001
        pass


def _carrega_minuto(chave: str) -> None:
    global _minuto
    if _minuto.get("chave") != chave:
        _minuto = {"chave": chave, "gasto": 0}


# -- API ----------------------------------------------------------------------
def pode_gastar(n: int = 1, now: Optional[datetime] = None) -> bool:
    """True se há vaga nas duas janelas (dia e minuto) para gastar `n` agora."""
    _carrega(_hoje(now))
    if _estado["gasto"] + n > _teto_util_dia():
        return False
    _carrega_minuto(_chave_minuto(now))
    return _minuto["gasto"] + n <= _teto_util_min()


def debita(n: int = 1, now: Optional[datetime] = None) -> None:
    _carrega(_hoje(now))
    _estado["gasto"] += n
    _persiste()
    _carrega_minuto(_chave_minuto(now))
    _minuto["gasto"] += n


def degradado(now: Optional[datetime] = None) -> bool:
    """SOFT STOP: o gasto do dia passou de 80% do teto útil."""
    _carrega(_hoje(now))
    lim = _teto_util_dia()
    return lim > 0 and _estado["gasto"] >= lim * _SOFT


async def aguarda_vaga(n: int = 1, timeout_s: float = 30.0,
                        now: Optional[datetime] = None) -> bool:
    """Pacer assíncrono para o consumidor em lote (Plano 09-02). Enquanto não
    houver vaga no minuto E ainda houver vaga no dia, dorme e reavalia.
    Devolve False se o teto do DIA estourou (esperar não resolve) ou se
    `timeout_s` acabou. Com `timeout_s=0` avalia uma vez, sem dormir."""
    restante = timeout_s
    while True:
        if pode_gastar(n, now=now):
            return True
        _carrega(_hoje(now))
        if _estado["gasto"] + n > _teto_util_dia():
            return False
        if restante <= 0:
            return False
        espera = min(2.0, restante)
        await asyncio.sleep(espera)
        restante -= espera


def snapshot(now: Optional[datetime] = None) -> dict:
    """Previsão local + verdade do header, lado a lado (mesma postura de
    `brapi_budget.snapshot()`)."""
    from . import mydata_client  # import tardio: evita ciclo em boot parcial
    _carrega(_hoje(now))
    _carrega_minuto(_chave_minuto(now))
    return {
        "dia": _estado["dia"],
        "quotaMin": quota_min(),
        "quotaDia": quota_dia(),
        "gastoMinuto": _minuto["gasto"],
        "gastoDia": _estado["gasto"],
        "headerQuota": dict(mydata_client.LAST_QUOTA),
        "degradado": degradado(now),
    }


def reset() -> None:
    """Para testes."""
    global _estado, _minuto
    _estado = {}
    _minuto = {}
