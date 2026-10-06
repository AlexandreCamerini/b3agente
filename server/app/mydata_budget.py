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
4. Classes de prioridade (quick 261006-oav, 2026-10-06). Incidente: dezenas de
   GET /api/options/gate/<t> (AtivoCards da Mesa) consumiram o minuto e o
   POST /api/options/buy do usuário levou 502 em 2 ms. Agora há três classes:
   "usuario" enxerga o teto útil TOTAL (54/min · 1.800/dia); "fundo" (default:
   candles, agente, propostas) e "descoberta" (gate de liquidez) param em
   teto − reserva (44/min · 1.650/dia) — a reserva é FATIA do teto, não
   acréscimo. A descoberta ainda tem sub-teto próprio por minuto (40% do teto
   útil, 21/54). A classe trafega por ContextVar (precedente
   `llm._USAGE_COLLECT`) para que NENHUM chamador existente ganhe kwarg novo e
   os guardiões que monkeypatcham pode_gastar/debita/reservar continuem
   válidos. `registrar_recusa()` deixa rastro (obslog cat "cota") com limite
   de taxa.
"""
import asyncio
import contextvars
import json
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import obslog

# WR-01 (09-REVIEW.md): trava dedicada para o read-modify-write de `_estado`/
# `_minuto` — sem ela, `pode_gastar()` e `debita()` chamados por threads
# concorrentes (candle_provider, options_provider_mydata, scheduler do
# agente) podem intercalar leitura/escrita e corromper o contador (mesma
# classe de bug que `store.ORDER_LOCK`/`WATCHLIST_LOCK` fecham para
# cash/positions/watchlist). `reservar()` (abaixo) usa a MESMA trava para
# tornar check+debit atômico onde o chamador consegue — RLock porque
# `reservar()` chama `pode_gastar()`/`debita()` por dentro da própria trava.
MYDATA_BUDGET_LOCK = threading.RLock()

BRT = timezone(timedelta(hours=-3))
QUOTA_MIN_DEFAULT = 60
QUOTA_DIA_DEFAULT = 2000
# Teto ÚTIL local: o hub é a verdade e o contador local é previsão — gastar
# 100% da previsão garante bater no 429 do outro lado antes de o contador
# local perceber. Expor os dois números (previsão vs. cota real) em
# snapshot().
MARGEM = 0.9
_SOFT = 0.8

PRIORIDADES = ("usuario", "fundo", "descoberta")
RESERVA_USUARIO_MIN_DEFAULT = 10
RESERVA_USUARIO_DIA_DEFAULT = 150
FRACAO_DESCOBERTA_MIN = 0.4
LOG_RECUSA_INTERVALO_S = 60

_PRIORIDADE = contextvars.ContextVar("mydata_prioridade", default="fundo")
_ORIGEM = contextvars.ContextVar("mydata_origem", default=None)
_ultimo_log: dict = {}   # {(janela, classe, origem): [instante, suprimidas]}

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


def _env_int(nome: str, default: int) -> int:
    try:
        return int(os.environ.get(nome, str(default)))
    except ValueError:
        return default


def reserva_min() -> int:
    return max(0, min(_env_int("MYDATA_RESERVA_MIN", RESERVA_USUARIO_MIN_DEFAULT),
                      _teto_util_min()))


def reserva_dia() -> int:
    return max(0, min(_env_int("MYDATA_RESERVA_DIA", RESERVA_USUARIO_DIA_DEFAULT),
                      _teto_util_dia()))


def _teto_min(classe: str) -> int:
    if classe == "usuario":
        return _teto_util_min()
    return max(0, _teto_util_min() - reserva_min())


def _teto_dia(classe: str) -> int:
    if classe == "usuario":
        return _teto_util_dia()
    return max(0, _teto_util_dia() - reserva_dia())


def _teto_descoberta_min() -> int:
    return int(_teto_util_min() * FRACAO_DESCOBERTA_MIN)


def prioridade_atual() -> str:
    return _PRIORIDADE.get()


def origem_atual() -> Optional[str]:
    return _ORIGEM.get()


@contextmanager
def contexto(prioridade: str, origem: Optional[str] = None):
    """Fixa a classe de prioridade (e a origem, para o log) das chamadas feitas
    DENTRO do bloco. ARMADILHA: `asyncio.create_task` copia o contexto no
    instante da criação — envolva SÓ o await da cadeia, nunca a rota inteira,
    senão uma task criada dentro herda a prioridade."""
    if prioridade not in PRIORIDADES:
        raise ValueError(f"prioridade inválida: {prioridade!r}")
    t1 = _PRIORIDADE.set(prioridade)
    t2 = _ORIGEM.set(origem)
    try:
        yield
    finally:
        _ORIGEM.reset(t2)
        _PRIORIDADE.reset(t1)


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
        _minuto = {"chave": chave, "gasto": 0, "descoberta": 0}


# -- API ----------------------------------------------------------------------
def pode_gastar(n: int = 1, now: Optional[datetime] = None,
                prioridade: Optional[str] = None) -> bool:
    """True se há vaga nas duas janelas (dia e minuto) para gastar `n` agora,
    contra o teto da classe de prioridade (contexto ou `prioridade`)."""
    classe = prioridade or _PRIORIDADE.get()
    with MYDATA_BUDGET_LOCK:
        _carrega(_hoje(now))
        if _estado["gasto"] + n > _teto_dia(classe):
            return False
        _carrega_minuto(_chave_minuto(now))
        if _minuto["gasto"] + n > _teto_min(classe):
            return False
        if classe == "descoberta":
            return _minuto["descoberta"] + n <= _teto_descoberta_min()
        return True


def debita(n: int = 1, now: Optional[datetime] = None,
           prioridade: Optional[str] = None) -> None:
    classe = prioridade or _PRIORIDADE.get()
    with MYDATA_BUDGET_LOCK:
        _carrega(_hoje(now))
        _estado["gasto"] += n
        _persiste()
        _carrega_minuto(_chave_minuto(now))
        _minuto["gasto"] += n
        if classe == "descoberta":
            _minuto["descoberta"] += n


def reservar(n: int = 1, now: Optional[datetime] = None,
             prioridade: Optional[str] = None) -> bool:
    """WR-01: check+debit ATÔMICO — fecha a corrida que `pode_gastar()` +
    `debita()` chamados separadamente deixava aberta (duas threads podem ver
    `pode_gastar()` = True antes de qualquer uma debitar). Sob a MESMA
    trava (RLock, reentrante), reavalia `pode_gastar(n)` e só debita se
    ainda houver vaga — nunca debita quando devolve False. Chamador deve
    tratar `False` exatamente como já trata `pode_gastar()` = False (mesma
    mensagem/estado degradado), pois o resultado pode divergir do check
    otimista feito antes (ex.: `_gate()` de pré-filtro que não debita).

    2026-10-06 (quick 261006-oav, incidente do 502 no buy): a classe de
    prioridade vem do contexto (ou do `prioridade` explícito, que não vaza
    após o retorno). As chamadas internas seguem `(n, now=now)` — sem kwarg
    novo — para manter válidos os lambdas monkeypatchados nos guardiões."""
    token = None
    if prioridade is not None:
        if prioridade not in PRIORIDADES:
            raise ValueError(f"prioridade inválida: {prioridade!r}")
        token = _PRIORIDADE.set(prioridade)
    try:
        with MYDATA_BUDGET_LOCK:
            if not pode_gastar(n, now=now):
                return False
            debita(n, now=now)
            return True
    finally:
        if token is not None:
            _PRIORIDADE.reset(token)


def _janela_recusada(n: int, now: Optional[datetime], classe: str):
    with MYDATA_BUDGET_LOCK:
        _carrega(_hoje(now))
        _carrega_minuto(_chave_minuto(now))
        if _estado["gasto"] + n > _teto_dia(classe):
            return "dia", _estado["gasto"], _teto_dia(classe)
        if _minuto["gasto"] + n > _teto_min(classe):
            return "minuto", _minuto["gasto"], _teto_min(classe)
        if classe == "descoberta" and \
                _minuto["descoberta"] + n > _teto_descoberta_min():
            return ("descoberta-minuto", _minuto["descoberta"],
                    _teto_descoberta_min())
        return "indeterminada", _minuto["gasto"], _teto_min(classe)


def registrar_recusa(n: int = 1, now: Optional[datetime] = None,
                     agora: Optional[float] = None,
                     prioridade: Optional[str] = None,
                     origem: Optional[str] = None) -> None:
    """Deixa rastro (WARNING, obslog cat "cota") da recusa por cota, no máximo
    1 linha por (janela, classe, origem) a cada LOG_RECUSA_INTERVALO_S, com
    contador `suprimidas`. Só rótulos e números — sem header/env/URL. Nunca
    levanta (log não derruba a rota)."""
    try:
        classe = prioridade or _PRIORIDADE.get()
        origem = origem or _ORIGEM.get() or "nao-identificada"
        janela, gasto, teto = _janela_recusada(n, now, classe)
        agora = agora if agora is not None else time.monotonic()
        chave = (janela, classe, origem)
        with MYDATA_BUDGET_LOCK:
            ult = _ultimo_log.get(chave)
            if ult is not None and agora - ult[0] < LOG_RECUSA_INTERVALO_S:
                ult[1] += 1
                return
            suprimidas = ult[1] if ult else 0
            _ultimo_log[chave] = [agora, 0]
        obslog.log("cota", "mydata: recusa por cota", level="warn",
                   janela=janela, gasto=gasto, teto=teto, classe=classe,
                   origem=origem, n=n, suprimidas=suprimidas)
    except Exception:  # noqa: BLE001
        pass


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
        if _estado["gasto"] + n > _teto_dia(_PRIORIDADE.get()):
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
        "reservaUsuarioMin": reserva_min(),
        "reservaUsuarioDia": reserva_dia(),
        "tetoFundoMin": _teto_min("fundo"),
        "tetoFundoDia": _teto_dia("fundo"),
        "tetoDescobertaMin": _teto_descoberta_min(),
        "gastoDescobertaMinuto": _minuto.get("descoberta", 0),
    }


def reset() -> None:
    """Para testes."""
    global _estado, _minuto
    _estado = {}
    _minuto = {}
    _ultimo_log.clear()
