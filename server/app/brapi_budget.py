"""Orçamento de requisições da brapi (ADR-008, Fase 2 do qa/43).

A cota do plano gratuito é finita (15.000/mês, medida em 11/08/2026) e uma
recusa por plano DEBITA cota — então o controle é local e ANTES da chamada.
Política decidida no ADR-008:

  • teto diário = B3_BRAPI_COTA_MES ÷ 21 pregões (~700 com a cota padrão);
  • fatias: spot ~57%, delta diário ~21%, fundamentos ~4%, reserva o resto;
  • fatia estourada consome da reserva; reserva esgotada = fatia bloqueada;
  • SOFT STOP a 80% da fatia (`degradado()` → quem chama alonga TTL);
  • HARD STOP a 100% do teto do dia (brapi silencia até o próximo pregão);
  • consumo só na janela de negociação da B3 — desde 2026-08-17 vem de
    `pregao.py` (10:00–16:55, sem fim de semana e sem feriado), não mais de uma
    janela própria de 10:00–17:15 que ignorava o calendário. Fora dela,
    `pode_gastar()` é False.

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


# A janela do ORÇAMENTO é mais larga que a de EXECUÇÃO, de propósito: vai até
# 17:15 para caber a passada de DELTA PÓS-FECHAMENTO, que busca o preço de
# fechamento — gasto legítimo, na única hora em que aquele dado existe. Quem
# executa ordem para às 16:55 (`pregao.in_market_hours`).
_ORCAMENTO_FIM = 17 * 60 + 15     # 17:15 BRT


def em_pregao(now: Optional[datetime] = None) -> bool:
    """Janela de CONSUMO da brapi: dia com pregão (calendário de `pregao.py`,
    2026-08-17) entre a abertura e 17:15 BRT.

    O que mudou: o dia útil agora vem de `pregao.is_trading_day`, então FERIADO
    da B3 deixa de autorizar gasto. O comentário antigo aqui afirmava que
    "feriado sem pregão não gera demanda, o custo de tratá-lo como útil é
    ~zero" — a premissa era falsa, porque o `in_market_hours` de então também
    ignorava feriado e o laço rodava o dia inteiro.

    O FIM da janela continua em 17:15 e NÃO é o mesmo de `in_market_hours`:
    achatar os dois quebra o delta pós-fechamento (guardião
    `test_janela_de_pregao`, que pegou exatamente isso).
    """
    from . import pregao  # import local: sem ciclo (pregao não importa ninguém do app)
    n = now or datetime.now(BRT)
    if not pregao.is_trading_day(n.date()):
        return False
    minutos = n.hour * 60 + n.minute
    return (pregao.ABERTURA[0] * 60 + pregao.ABERTURA[1]) <= minutos <= _ORCAMENTO_FIM


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
        # controle de utilização: intervalo vigente + o que ele custa no mês
        "spotIntervaloS": spot_intervalo_s(),
        "projecaoMes": projecao(spot_intervalo_s(), _universo_n()),
    }


def reset() -> None:
    """Para testes."""
    global _estado, _spot_intervalo_mem
    _estado = {}
    _spot_intervalo_mem = None


# ---------------------------------------------------------------------------
# Controle de utilização (ADR-008, Fase 6+): intervalo → projeção mensal
# ---------------------------------------------------------------------------
# O parâmetro de operação é o INTERVALO entre atualizações de spot; a projeção
# responde na hora quantas chamadas/mês aquele intervalo custa no PIOR CASO
# (universo inteiro refrescado a cada intervalo, pregão cheio). O consumo real
# tende a ser menor (cache compartilhado + demanda), e as fatias continuam
# sendo o teto duro — a projeção é instrumento de decisão, não de bloqueio.
# Janela de negociação contínua, derivada do calendário (10:00–16:55 = 6h55).
# Era 7,25 h fixas (10:00–17:15) — 1.200 s a mais do que a bolsa negocia, o que
# deixava a projeção ~5% pessimista. Derivar evita as duas verdades divergirem.
def _janela_pregao_s() -> int:
    from . import pregao
    ini = pregao.ABERTURA[0] * 3600 + pregao.ABERTURA[1] * 60
    fim = pregao.FECHAMENTO[0] * 3600 + pregao.FECHAMENTO[1] * 60
    if pregao.after_market_ligado():
        fim = pregao.AFTER_FIM[0] * 3600 + pregao.AFTER_FIM[1] * 60
    return fim - ini


JANELA_PREGAO_S = _janela_pregao_s()
_SPOT_INTERVALO_KV = "brapiSpotIntervaloS"
SPOT_INTERVALO_DEFAULT_S = 300
_spot_intervalo_mem: Optional[int] = None


def spot_intervalo_s() -> int:
    """Intervalo vigente entre atualizações de spot (alimenta o TTL da
    fronteira). Ordem: memória → kv (sobrevive a deploy) → default 300s."""
    global _spot_intervalo_mem
    if _spot_intervalo_mem is not None:
        return _spot_intervalo_mem
    if _DB_ENABLED:
        try:
            row = _DB_CONN.execute("SELECT value FROM kv WHERE key = ?",
                                   (_SPOT_INTERVALO_KV,)).fetchone()
            if row:
                _spot_intervalo_mem = max(30, int(json.loads(row[0])))
                return _spot_intervalo_mem
        except Exception:  # noqa: BLE001
            pass
    _spot_intervalo_mem = SPOT_INTERVALO_DEFAULT_S
    return _spot_intervalo_mem


def set_spot_intervalo(segundos: int) -> int:
    """Aplica um intervalo novo (mínimo 30s). Persiste no kv — sem deploy."""
    global _spot_intervalo_mem
    s = max(30, int(segundos))
    _spot_intervalo_mem = s
    if _DB_ENABLED:
        try:
            _DB_CONN.execute(
                "INSERT INTO kv(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (_SPOT_INTERVALO_KV, json.dumps(s)))
            _DB_CONN.commit()
        except Exception:  # noqa: BLE001
            pass
    return s


def projecao(intervalo_s: int, universo_n: int, cota: Optional[int] = None) -> dict:
    """PURA e determinística: quanto custa/mês um intervalo de spot.

    chamadasMes = spot (universo × janela/intervalo × 21 pregões)
                + delta diário (universo × 21)
                + fundamentos (universo × 21/7 — TTL de 7 dias).
    `intervaloMinimoSeguro` é o menor intervalo cujo total cabe na cota.
    """
    cota = cota if cota is not None else cota_mes()
    intervalo_s = max(1, int(intervalo_s))
    universo_n = max(0, int(universo_n))
    spot_mes = universo_n * (JANELA_PREGAO_S // intervalo_s) * PREGOES_MES
    delta_mes = universo_n * PREGOES_MES
    fund_mes = (universo_n * PREGOES_MES) // 7
    total = spot_mes + delta_mes + fund_mes
    sobra_para_spot = cota - delta_mes - fund_mes
    if universo_n and sobra_para_spot > 0:
        refresh_max_por_ticker = sobra_para_spot / (universo_n * PREGOES_MES)
        minimo = (int(JANELA_PREGAO_S // refresh_max_por_ticker) + 1
                  if refresh_max_por_ticker >= 1 else None)
    else:
        minimo = None
    return {
        "intervaloS": intervalo_s,
        "universoN": universo_n,
        "cotaMes": cota,
        "chamadasMes": total,
        "detalhe": {"spot": spot_mes, "delta": delta_mes, "fundamentos": fund_mes},
        "percentualDaCota": round(total / cota * 100, 1) if cota else None,
        "cabeNaCota": bool(cota and total <= cota),
        "intervaloMinimoSeguro": minimo,
    }


def _universo_n() -> int:
    from . import scanner   # import tardio (sem ciclo no boot)
    try:
        return len(scanner.get_universe())
    except Exception:  # noqa: BLE001
        return 0
