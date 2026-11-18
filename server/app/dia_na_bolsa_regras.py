"""Núcleo PURO do card "Seu dia na bolsa" (Fase 51, plano 51-01).

Sem I/O, sem rede, sem kv: recebe séries e registros já montados pelo job
(51-05) e devolve dicts ou `None`. Princípio 5 do produto: todo número do card
sai daqui (motor determinístico), nunca da IA. Regra da casa: `None` para
desconhecido, nunca `0`.

Decisões herdadas (CONTEXT D-05/D-07/D-08/D-10):
- Desfecho do "e se" REUSA `analysis_outcomes._avaliar_entry` (D-05). Não há
  terceira régua de stop/alvo aqui. A referência `signal_ledger` do CONTEXT só
  ARMAZENA linhas; `signal_replay.avaliar` usa outros rótulos. A régua com
  ancoragem de gatilho é a de `analysis_outcomes` (divergência 4 do PATTERNS);
  `expirou_pos|expirou_neg` viram o rótulo único "expirou" no card.
- Limiares de raridade TRAVADOS por D-07: IBOV_PERCENTIL e ATR_MULT_ATIVO. A
  calibração (51-04) NÃO os altera; só AMPLITUDE_MIN, AMPLITUDE_MIN_ATIVOS e
  GAP_MIN_ATR são calibráveis (D-08).
- Variante de template por sha256(uid|data|chave), nunca a função embutida
  de hash do Python (salgada por processo) nem aleatório (D-10).
"""
from __future__ import annotations

import hashlib
import statistics
from datetime import date as _date
from typing import Optional

from . import indicators
from .analysis_outcomes import HORIZON_PREGOES, METODOLOGIA_ATUAL, _avaliar_entry

# --- Limiares -------------------------------------------------------------
# TRAVADOS (D-07): a calibração do plano 51-04 não os altera.
IBOV_PERCENTIL = 0.95      # IBOV raro = |retorno do dia| >= p95 de |retorno diário| dos 252 anteriores
ATR_MULT_ATIVO = 2.0       # ativo raro = |movimento| > 2 x ATR(14)
JANELA_12M = 252           # pregões de referência (~12 meses)
MIN_HISTORICO_IBOV = 200   # abaixo disso não há base para percentil: None
# CALIBRÁVEIS (D-08): valor inicial, ajustável só pelo script do plano 51-04.
AMPLITUDE_MIN = 0.85
AMPLITUDE_MIN_ATIVOS = 30
GAP_MIN_ATR = 1.0

ATR_PERIODO = 14

# Conceitos por regra (D-08). Ids dos conceitos novos são criados em 51-04.
CONCEITO_POR_REGRA = {
    "ibov_raro": {"fonte": "kb", "id": "ind-volatilidade-historica"},
    "atr_ativo": {"fonte": "kb", "id": "ind-atr"},
    "gap": {"fonte": "kb", "id": "estr-gap"},
    "amplitude": {"fonte": "conceito", "id": "amplitude"},
    "max52": {"fonte": "conceito", "id": "extremo-52-semanas"},
    "min52": {"fonte": "conceito", "id": "extremo-52-semanas"},
}

# Ordem das famílias por modo (D-09): 1 = visto/"e se", 2 = motor, 3 = fato raro.
_ORDEM = {"estudo": [1, 3, 2], "educacional": [1, 3, 2], "operador": [2, 1, 3]}

# Família 2: evento do motor -> chave do template.
_TAG_PARA_CHAVE = {
    "stop": "f2_stop_executado",
    "alvo": "f2_alvo_executado",
    "entrada-auto": "f2_entrada_auto",
    "pendente-executada": "f2_pendente_executada",
}
_MARCO_PARA_CHAVE = {"stop_subiu": "f2_stop_subiu", "breakeven": "f2_breakeven"}


def _num(v) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None


# ==========================================================================
# Família 1: desfecho do "e se" e placar semanal
# ==========================================================================
def entry_do_visto(visto: dict) -> dict:
    """Converte o registro de visto na forma que `_avaliar_entry` lê."""
    return {
        "criadoEm": visto.get("dataBase"),
        "stopProposto": _num(visto.get("stop")),
        "alvoProposto": _num(visto.get("alvo")),
        "entrada": _num(visto.get("entrada")),
        "entradaAMercado": visto.get("entradaAMercado"),
        "precoNaAnalise": _num(visto.get("precoBase")),
        "metodologiaVersao": METODOLOGIA_ATUAL,
    }


def estado_do_visto(visto: dict, candles: list, hoje: str) -> Optional[dict]:
    """Estado do "e se" de UM visto em `hoje` (AAAA-MM-DD).

    Reusa `_avaliar_entry` (D-05) com `prazoPregoes = min(decorridos, 10)`
    sobre os candles até hoje: assim stop/alvo tocado no 2º pregão aparece como
    resolvido NAQUELE dia. Já `expirou_*`/`sem_gatilho` só valem com o prazo
    cheio (10 pregões); antes disso o visto segue aberto.

    None quando faltam dados (sem candles, sem stop/alvo ou sem âncora).
    """
    if not isinstance(visto, dict) or not candles or not hoje:
        return None
    entry = entry_do_visto(visto)
    if not entry["criadoEm"] or entry["stopProposto"] is None or entry["alvoProposto"] is None:
        return None
    if entry["entrada"] is None and entry["precoNaAnalise"] is None:
        return None
    base = str(entry["criadoEm"])[:10]
    ate_hoje = [c for c in candles if c.get("date") and c["date"] <= hoje]
    if not ate_hoje:
        return None
    decorridos = sum(1 for c in ate_hoje if c["date"] > base)
    if decorridos == 0:
        return {"resultado": None, "resultadoBruto": None, "r": None, "resolvidoEm": None,
                "resolvidoHoje": False, "aberto": True, "decorridos": 0}

    entry["prazoPregoes"] = min(decorridos, HORIZON_PREGOES)
    res = _avaliar_entry(dict(entry), ate_hoje)

    aberto = {"resultado": None, "resultadoBruto": None, "r": None, "resolvidoEm": None,
              "resolvidoHoje": False, "aberto": True, "decorridos": decorridos}
    if res is None:
        return aberto
    bruto = res["resultado"]
    if bruto not in ("stop", "alvo") and decorridos < HORIZON_PREGOES:
        return aberto
    resultado = "expirou" if bruto in ("expirou_pos", "expirou_neg") else bruto
    return {
        "resultado": resultado,
        "resultadoBruto": bruto,
        "r": res.get("rMultiple"),
        "resolvidoEm": res.get("resolvidoEm"),
        "resolvidoHoje": res.get("resolvidoEm") == hoje,
        "aberto": False,
        "decorridos": decorridos,
    }


def placar_semanal(estados: list) -> dict:
    """Quatro contadores sempre presentes (inclusive 0). `abertos` = ainda
    aberto + expirou + sem_gatilho (nem alvo nem stop)."""
    out = {"vistos": 0, "alvo": 0, "stop": 0, "abertos": 0}
    for e in estados or []:
        if not isinstance(e, dict):
            continue
        out["vistos"] += 1
        r = e.get("resultado")
        if r == "alvo":
            out["alvo"] += 1
        elif r == "stop":
            out["stop"] += 1
        else:
            out["abertos"] += 1
    return out


# ==========================================================================
# Família 2: eventos do motor no dia
# ==========================================================================
def eventos_motor_do_dia(eventos: list, hoje_ddmmaaaa: str) -> list:
    """Filtra os eventos gravados pelo motor com `time` de hoje e os mapeia
    para a chave do template. Nunca lê `text`. Ignora evento sem ticker."""
    out = []
    for ev in eventos or []:
        if not isinstance(ev, dict):
            continue
        tm = str(ev.get("time") or "")
        if not hoje_ddmmaaaa or not tm.startswith(hoje_ddmmaaaa):
            continue
        marco = ev.get("marcoMotor")
        chave = ticker = None
        stop = None
        motivo = None
        if isinstance(marco, dict):
            chave = _MARCO_PARA_CHAVE.get(marco.get("tipo"))
            ticker = marco.get("ticker")
            stop = _num(marco.get("stop"))
            motivo = marco.get("motivo")
        else:
            chave = _TAG_PARA_CHAVE.get(ev.get("tag"))
            ticker = ev.get("t")
        if not chave or not ticker:
            continue
        out.append({"chave": chave, "ticker": str(ticker), "hora": tm[11:16],
                    "stop": stop, "motivo": motivo})
    out.sort(key=lambda x: x["hora"])
    return out


# ==========================================================================
# Utilidades de série
# ==========================================================================
def _data(p: dict) -> Optional[str]:
    return p.get("date") or p.get("data")


def _ordenada(serie: list, campo: str) -> list:
    """Pontos com data e valor numérico, em ordem cronológica."""
    pts = [p for p in (serie or []) if isinstance(p, dict) and _data(p) and _num(p.get(campo)) is not None]
    return sorted(pts, key=_data)


def retorno_dia(serie: list, hoje: str, campo: str) -> Optional[float]:
    """Retorno % do dia: close de hoje / close do pregão anterior - 1. None se
    o último ponto não é de hoje ou falta o anterior."""
    pts = _ordenada(serie, campo)
    if len(pts) < 2 or _data(pts[-1]) != hoje:
        return None
    ant, cur = _num(pts[-2][campo]), _num(pts[-1][campo])
    if not ant or ant <= 0 or cur is None:
        return None
    return (cur / ant - 1.0) * 100.0


def _percentil(valor: float, historico: list) -> Optional[float]:
    """Fração do histórico estritamente menor que `valor`."""
    if not historico:
        return None
    return sum(1 for h in historico if h < valor) / len(historico)


def _meses_entre(d1: str, d2: str) -> Optional[int]:
    try:
        a = _date.fromisoformat(d1[:10])
        b = _date.fromisoformat(d2[:10])
    except ValueError:
        return None
    return int(abs((b - a).days) / 30.44)


def _fato(regra: str, ticker: Optional[str], percentil: Optional[float], **campos) -> dict:
    d = {"regra": regra, "ticker": ticker, "percentil": percentil,
         "conceito": dict(CONCEITO_POR_REGRA[regra])}
    d.update(campos)
    return d


# ==========================================================================
# Família 3: regras de raridade
# ==========================================================================
def regra_ibov_raro(serie_close: list, hoje: str) -> Optional[dict]:
    """IBOV raro: |retorno do dia| >= p95 de |retorno diário| dos 252 pregões
    anteriores (D-07). Só fechamento (sem ATR do IBOV, D-08)."""
    pts = _ordenada(serie_close, "close")
    if len(pts) < 3 or _data(pts[-1]) != hoje:
        return None
    rets = []
    for i in range(1, len(pts)):
        ant, cur = pts[i - 1]["close"], pts[i]["close"]
        if ant and ant > 0:
            rets.append((_data(pts[i]), cur / ant - 1.0))
    if not rets or rets[-1][0] != hoje:
        return None
    r_hoje = rets[-1][1]
    previos = rets[:-1][-JANELA_12M:]
    if len(previos) < MIN_HISTORICO_IBOV:
        return None
    abs_prev = [abs(r) for _, r in previos]
    limiar = statistics.quantiles(abs_prev, n=100, method="inclusive")[round(IBOV_PERCENTIL * 100) - 1]
    if abs(r_hoje) < limiar:
        return None
    meses = None
    for d, r in reversed(previos):
        if abs(r) >= abs(r_hoje):
            meses = _meses_entre(d, hoje)
            break
    return _fato("ibov_raro", None, _percentil(abs(r_hoje), abs_prev),
                 pct=round(r_hoje * 100.0, 2), mesesDesde=meses)


def _ohlc(candles: list) -> list:
    return sorted((c for c in (candles or []) if isinstance(c, dict) and c.get("date")
                   and _num(c.get("high")) is not None and _num(c.get("low")) is not None
                   and _num(c.get("close")) is not None), key=lambda c: c["date"])


def regra_atr_ativo(candles: list, hoje: str, ticker: str) -> Optional[dict]:
    """Ativo raro: |movimento do dia| > 2 x ATR(14) calculado só com candles
    até o pregão ANTERIOR (D-07)."""
    cs = _ohlc(candles)
    if len(cs) < ATR_PERIODO + 2 or cs[-1]["date"] != hoje:
        return None
    hs = [c["high"] for c in cs]
    ls = [c["low"] for c in cs]
    cl = [c["close"] for c in cs]
    atrs = indicators.atr(hs, ls, cl, ATR_PERIODO)
    a_prev = atrs[-2]
    if not a_prev or a_prev <= 0:
        return None
    mov = cl[-1] - cl[-2]
    multiplo = abs(mov) / a_prev
    if multiplo <= ATR_MULT_ATIVO:
        return None
    hist = []
    for i in range(1, len(cs) - 1):
        if atrs[i - 1]:
            hist.append(abs(cl[i] - cl[i - 1]) / atrs[i - 1])
    hist = hist[-JANELA_12M:]
    return _fato("atr_ativo", ticker, _percentil(multiplo, hist),
                 pct=round((cl[-1] / cl[-2] - 1.0) * 100.0, 2) if cl[-2] else None,
                 multiplo=round(multiplo, 2))


def regra_gap(candles: list, hoje: str, ticker: str) -> Optional[dict]:
    """Gap: |abertura/fechamento anterior - 1| >= GAP_MIN_ATR x ATR% e o
    fechamento ficou do lado do gap (não fechou o gap)."""
    cs = _ohlc(candles)
    if len(cs) < ATR_PERIODO + 2 or cs[-1]["date"] != hoje:
        return None
    ab = _num(cs[-1].get("open"))
    if ab is None:
        return None
    hs = [c["high"] for c in cs]
    ls = [c["low"] for c in cs]
    cl = [c["close"] for c in cs]
    atrs = indicators.atr(hs, ls, cl, ATR_PERIODO)
    a_prev, c_prev = atrs[-2], cl[-2]
    if not a_prev or not c_prev or c_prev <= 0:
        return None
    atr_pct = a_prev / c_prev
    gap = ab / c_prev - 1.0
    if abs(gap) < GAP_MIN_ATR * atr_pct:
        return None
    # Gap fechado = o fechamento voltou ao fechamento anterior (ou além).
    lado_ok = cl[-1] > c_prev if gap > 0 else cl[-1] < c_prev
    if not lado_ok:
        return None
    hist = []
    for i in range(1, len(cs) - 1):
        o = _num(cs[i].get("open"))
        if o is None or not atrs[i - 1] or cl[i - 1] <= 0:
            continue
        hist.append(abs(o / cl[i - 1] - 1.0) / (atrs[i - 1] / cl[i - 1]))
    hist = hist[-JANELA_12M:]
    return _fato("gap", ticker, _percentil(abs(gap) / atr_pct, hist),
                 pct=round(gap * 100.0, 2), direcao="alta" if gap > 0 else "baixa")


def regra_extremo_52s(serie: list, hoje: str, ticker: Optional[str], campo: str = "close") -> Optional[dict]:
    """Close de hoje acima do máximo (ou abaixo do mínimo) dos 252 pregões
    anteriores. Percentil: fração dos 252 anteriores com nível abaixo (acima,
    no mínimo) do de hoje — 1.0 por definição de novo extremo."""
    pts = _ordenada(serie, campo)
    if not pts or _data(pts[-1]) != hoje:
        return None
    previos = [p[campo] for p in pts[:-1]][-JANELA_12M:]
    if len(previos) < JANELA_12M:
        return None
    hoje_v = pts[-1][campo]
    if hoje_v > max(previos):
        regra = "max52"
        perc = sum(1 for v in previos if v < hoje_v) / len(previos)
    elif hoje_v < min(previos):
        regra = "min52"
        perc = sum(1 for v in previos if v > hoje_v) / len(previos)
    else:
        return None
    return _fato(regra, ticker, perc, valor=hoje_v)


def regra_amplitude(universo: dict, hoje: str) -> Optional[dict]:
    """Amplitude: fração do universo se movendo na mesma direção hoje.
    `universo` = ticker -> candles. Percentil sobre a amplitude dos 252
    pregões anteriores calculada do mesmo universo (None sem histórico)."""
    por_data: dict = {}
    for _t, candles in (universo or {}).items():
        cs = _ohlc(candles)
        for i in range(1, len(cs)):
            if cs[i - 1]["close"] > 0:
                por_data.setdefault(cs[i]["date"], []).append(cs[i]["close"] - cs[i - 1]["close"])
    rets_hoje = por_data.get(hoje) or []
    n = len(rets_hoje)
    if n < AMPLITUDE_MIN_ATIVOS:
        return None
    alta = sum(1 for r in rets_hoje if r > 0)
    baixa = sum(1 for r in rets_hoje if r < 0)
    fracao = max(alta, baixa) / n
    if fracao < AMPLITUDE_MIN or alta == baixa:
        return None
    hist = []
    for d in sorted(k for k in por_data if k < hoje)[-JANELA_12M:]:
        rs = por_data[d]
        if len(rs) >= AMPLITUDE_MIN_ATIVOS:
            hist.append(max(sum(1 for r in rs if r > 0), sum(1 for r in rs if r < 0)) / len(rs))
    return _fato("amplitude", None, _percentil(fracao, hist),
                 fracao=round(fracao, 4), n=n, direcao="alta" if alta > baixa else "baixa")


# ==========================================================================
# Seleção, ordem e variante
# ==========================================================================
def escolher_fato(candidatos: list) -> Optional[dict]:
    """Um fato por dia: maior percentil; empate -> ativo do usuário antes de
    mercado; depois ticker alfabético. Lista vazia -> None."""
    validos = [c for c in (candidatos or []) if isinstance(c, dict)]
    if not validos:
        return None

    def chave(c):
        p = c.get("percentil")
        return (-(p if isinstance(p, (int, float)) else -1.0),
                0 if c.get("doUsuario") else 1,
                c.get("ticker") or "")

    return sorted(validos, key=chave)[0]


def ordem_familias(modo: str, presentes: Optional[list] = None) -> list:
    """Ordem das famílias por modo (D-09). Família ausente sai da ordem."""
    base = list(_ORDEM.get(modo, _ORDEM["estudo"]))
    if presentes is None:
        return base
    return [f for f in base if f in presentes]


def variante(uid: str, data: str, chave: str, n: int) -> Optional[int]:
    """Índice determinístico em [0, n) por sha256(uid|data|chave) (D-10)."""
    if not isinstance(n, int) or n < 1:
        return None
    h = hashlib.sha256(f"{uid}|{data}|{chave}".encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big") % n
