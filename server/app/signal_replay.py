"""signal_replay.py — fonte única do replay determinístico do motor de setups.

O que é: replay barra a barra de `detect_setups` + `plano_do_resultado` sobre
candles reais, avaliado por uma barreira tripla (alvo/stop/expira em N barras)
ancorada no GATILHO do plano, nunca no close do dia da análise. Módulo PURO —
sem I/O, sem rede, sem relógio, sem argparse: mesmos candles ⇒ mesmas linhas,
sempre.

De onde veio: promovido de `scripts/backtest_sinal.py` (`sinais_do_ticker`,
`avaliar`, `agregar`) por decisão do ADR-017 (Decisão 2, "Reprodutibilidade")
— duas implementações da mesma barreira produziriam dois números para a mesma
pergunta, o que o ADR proíbe explicitamente. `scripts/backtest_sinal.py`
agora é um wrapper fino sobre este módulo (ver Task 3 do plano 07-01).

Invariante de direção de dependência: `scripts/` importa de `server/app/`,
nunca o contrário — é o que garante que o deploy (que só publica `server/`)
nunca fica sem o código que o harness do ADR-016/017 usa para reproduzir o
número que a produção mostra.

Metodologia (ADR-015): a entrada é ancorada no GATILHO (`plano["entrada"]`),
nunca no close do dia da análise. Plano do tipo "a mercado" abre a barreira no
candle seguinte sem exigir toque — exigir toque jogaria o gap adverso para
fora do denominador, que é o viés otimista que o ADR-015 documenta.
"""
from __future__ import annotations

from . import indicators, regime, setups

JANELA = 252          # candles_mod.resolve_keep("1y") — a janela que o Radar usa
HORIZONTE = 10         # analysis_outcomes.HORIZON_PREGOES (default do produto)


# --------------------------------------------------------------------------- #
# 1) Replay do motor
# --------------------------------------------------------------------------- #

def _summary_em(ind: dict, closes: list, t: int) -> dict:
    """Mini-summary no dia t. Os indicadores são causais e alinhados ao array de
    candles, então o valor no índice t é exatamente o que a produção teria
    calculado naquele dia — não há vazamento de futuro."""
    def v(nome):
        arr = ind.get(nome) or []
        return arr[t] if t < len(arr) else None
    return {"close": closes[t], "sma200": v("sma200"), "sma50": v("sma50"),
            "adx14": v("adx14"), "diPlus": v("diPlus"), "diMinus": v("diMinus")}


def sinais_do_ticker(ticker: str, cs: list, dias: int,
                     horizonte: int = HORIZONTE, janela: int = JANELA) -> list:
    """Roda o motor barra a barra e devolve os planos acionáveis (COMPRAR/VENDER)."""
    cs = indicators.sanitize_candles(cs or [])
    if len(cs) < janela + horizonte + 10:
        return []
    full = indicators.compute(cs)
    ind, closes = full["indicators"], [c["close"] for c in cs]

    # Só avalia barras que têm janela cheia atrás E horizonte cheio à frente.
    t0 = max(janela, len(cs) - horizonte - dias)
    t1 = len(cs) - horizonte - 1

    out = []
    for t in range(t0, t1 + 1):
        ini = max(0, t + 1 - janela)
        bloco = cs[ini:t + 1]
        ind_slice = {k: arr[ini:t + 1] for k, arr in ind.items()}
        sres = setups.detect_setups(bloco, ind_slice)
        plano = setups.plano_do_resultado(sres, close=cs[t]["close"])
        if plano.get("decisao") not in (setups.DECISAO_COMPRAR, setups.DECISAO_VENDER):
            continue
        entrada, stop = plano.get("entrada"), plano.get("stop")
        if entrada is None or stop is None or entrada == stop:
            continue
        reg = regime.classificar({"close": cs[t]["close"],
                                  "summary": _summary_em(ind, closes, t),
                                  "candlesAvailable": t + 1})
        # A confluência que importa é a do setup QUE VIROU PLANO — não a global
        # de `sres["confluencia"]` (que é a do melhor setup, podendo ser um
        # neutro ou do lado oposto ao plano, ver plano_do_resultado).
        nome = plano.get("setup")
        conf = next((s.get("confluencia") for s in (sres.get("setups") or [])
                     if s.get("nome") == nome), sres.get("confluencia"))
        out.append({
            "ticker": ticker, "data": cs[t]["date"], "t": t,
            "setup": nome, "lado": plano.get("lado"),
            "confluencia": conf,
            "tipo": plano.get("tipo"), "entrada": entrada, "stop": stop,
            "alvo1": plano.get("alvo1"), "alvo2": plano.get("alvo2"),
            "rr2": plano.get("rr2"), "regime": reg.get("regime"),
        })
    return out


# --------------------------------------------------------------------------- #
# 2) Avaliação forward (barreira tripla ancorada no gatilho — ADR-015)
# --------------------------------------------------------------------------- #

def avaliar(sinal: dict, cs: list, alvo_campo: str = "alvo1", horizonte: int = HORIZONTE) -> dict:
    """Desfecho das próximas `horizonte` barras. `resultado` ∈
    {alvo, stop, sem_gatilho, expirou}. `r` é o múltiplo do risco do PLANO.
    `dataResolucao` é o campo `date` do candle em que a barreira fechou
    (alvo/stop), o último candle do horizonte se expirou, ou None quando não
    houve gatilho ou o desfecho não pôde ser avaliado — o ledger (Plano 02)
    grava esse valor; sem ele o registro afirmaria um desfecho sem saber
    quando ele ocorreu (T-07-02)."""
    alvo = sinal.get(alvo_campo)
    if alvo is None:
        return {"resultado": None, "r": None, "dataResolucao": None}
    entrada, stop = sinal["entrada"], sinal["stop"]
    compra = sinal["lado"] == "alta"
    risco = abs(entrada - stop)
    if risco <= 0:
        return {"resultado": None, "r": None, "dataResolucao": None}

    janela = cs[sinal["t"] + 1: sinal["t"] + 1 + horizonte]
    if len(janela) < horizonte:
        return {"resultado": None, "r": None, "dataResolucao": None}

    # Entrada a mercado: o gatilho já rompeu, a entrada é imediata — a barreira
    # abre na primeira barra, sem exigir toque (ADR-015 / ADR15-02).
    a_mercado = str(sinal.get("tipo") or "").startswith("a mercado")
    if a_mercado:
        i0 = 0
    else:
        i0 = None
        for i, c in enumerate(janela):
            hi, lo = c.get("high"), c.get("low")
            if hi is None or lo is None:
                continue
            if (compra and hi >= entrada) or (not compra and lo <= entrada):
                i0 = i
                break
        if i0 is None:
            return {"resultado": "sem_gatilho", "r": None, "dataResolucao": None}

    for c in janela[i0:]:
        hi, lo = c.get("high"), c.get("low")
        if hi is None or lo is None:
            continue
        # Empate intrabar resolve a favor do stop (cenário conservador — mesma
        # convenção de analysis_outcomes._avaliar_entry e agent.py).
        bateu_stop = lo <= stop if compra else hi >= stop
        bateu_alvo = hi >= alvo if compra else lo <= alvo
        if bateu_stop:
            return {"resultado": "stop", "r": -1.0, "dataResolucao": c.get("date")}
        if bateu_alvo:
            return {"resultado": "alvo", "r": round(abs(alvo - entrada) / risco, 3),
                    "dataResolucao": c.get("date")}

    fim = janela[-1].get("close")
    if fim is None:
        return {"resultado": None, "r": None, "dataResolucao": None}
    ganho = (fim - entrada) if compra else (entrada - fim)
    return {"resultado": "expirou", "r": round(ganho / risco, 3),
            "dataResolucao": janela[-1]["date"]}


# --------------------------------------------------------------------------- #
# 3) Estatística
# --------------------------------------------------------------------------- #

def agregar(linhas: list) -> dict:
    """Expectância em R e taxa de acerto. `sem_gatilho` fica FORA do
    denominador: o trade não existiu, contá-lo como perda inflaria a taxa de
    stop pelo mesmo viés que o ADR-015 corrige."""
    resolvidos = [l for l in linhas if l["resultado"] in ("alvo", "stop", "expirou")]
    n = len(resolvidos)
    if not n:
        return {"n": 0, "naoAcionados": sum(1 for l in linhas if l["resultado"] == "sem_gatilho")}
    rs = [l["r"] for l in resolvidos]
    ganhos = [r for r in rs if r > 0]
    perdas = [-r for r in rs if r < 0]
    return {
        "n": n,
        "naoAcionados": sum(1 for l in linhas if l["resultado"] == "sem_gatilho"),
        "acerto": round(100.0 * len(ganhos) / n, 1),
        "expectanciaR": round(sum(rs) / n, 3),
        "somaR": round(sum(rs), 1),
        "profitFactor": (round(sum(ganhos) / sum(perdas), 2) if perdas else None),
        "stops": sum(1 for l in resolvidos if l["resultado"] == "stop"),
        "alvos": sum(1 for l in resolvidos if l["resultado"] == "alvo"),
        "expirou": sum(1 for l in resolvidos if l["resultado"] == "expirou"),
    }


# --------------------------------------------------------------------------- #
# 4) Conveniência — ponto de entrada único para bootstrap e hook diário
# --------------------------------------------------------------------------- #

def replay(ticker: str, cs: list, dias: int, horizonte: int = HORIZONTE,
           janela: int = JANELA, alvo_campo: str = "alvo1") -> list:
    """`sinais_do_ticker` + `avaliar`, uma linha por sinal AVALIÁVEL
    (`{**sinal, **resultado_da_avaliacao}`). Descarta os sinais que `avaliar`
    devolve com `resultado is None` (sem horizonte cheio ainda) — é o ponto
    de entrada único que o bootstrap (Plano 03) e o hook diário (Plano 04)
    consomem: "sinais deste ticker, já resolvidos"."""
    sinais = sinais_do_ticker(ticker, cs, dias, horizonte, janela)
    cs_ok = indicators.sanitize_candles(cs or [])
    out = []
    for s in sinais:
        r = avaliar(s, cs_ok, alvo_campo, horizonte)
        if r["resultado"] is None:
            continue
        out.append({**s, **r})
    return out
