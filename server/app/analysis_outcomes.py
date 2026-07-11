"""qa/30 (Fase A) — autoavaliação da IA: cada análise (N1/scanDeep e
N2/analyze) que produz stop/alvo grava o que recomendou; um job diário
(encaixado no MESMO scheduler_loop do agent.py, sem scheduler novo — igual ao
padrão do radar_daily) confere, num prazo FIXO de 10 pregões, se o ativo
bateu o alvo, o stop, ou fechou o prazo sem decisão.

Escopo (decidido com o Alex): SÓ autoavaliação da IA aqui. Trades reais
(registro manual, mock modo-operador.html tela 4) é feature separada
(qa/30 Fase B), com seu próprio armazenamento — não usa nada deste módulo.

Puro/testável onde possível: `_avaliar_entry` não faz I/O (candles injetados);
`avaliar_pendentes`/`maybe_run` recebem `fetch` por injeção (mesmo padrão do
radar_daily.maybe_run), sem import direto de yahoo.py aqui.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import db

BRT = timezone(timedelta(hours=-3))
HORIZON_PREGOES = 10   # decidido com o Alex: prazo FIXO, não "até bater stop/alvo"
CAP = 500               # teto de registros por escopo (evita blob JSON gigante no kv)
MAX_DIAS = 180          # prune por idade — o que vier primeiro entre CAP e MAX_DIAS

RESULTADOS_SUCESSO = ("alvo", "expirou_pos")
RESULTADOS_FALHA = ("stop", "expirou_neg")

# qa/35 (P2, decidido com o Alex): células de segmentação com amostra menor
# que isto mostram "n insuficiente" em vez de porcentagem enganosa.
MIN_N = 10


def normalizar_confianca(valor) -> Optional[str]:
    """Escala única de confiança declarada pela IA: N1 usa `confianca`
    (baixa|moderada, teto sem 2º timeframe); N2 usa `conviccao`
    (Muito Alto|Alto|Médio|Baixo). Puro; devolve alta|moderada|baixa ou None."""
    v = str(valor or "").strip().lower()
    if not v:
        return None
    if v in ("muito alto", "alto", "alta"):
        return "alta"
    if v in ("médio", "medio", "moderada", "moderado"):
        return "moderada"
    if v in ("baixo", "baixa"):
        return "baixa"
    return None

# Telemetria em memória (mesmo padrão de radar_daily.LAST_DAILY — aparece no
# status_snapshot da Observabilidade).
LAST_EVAL = {"date": None, "avaliadas": 0, "erro": None}


def _key() -> str:
    return "analysisOutcomes"


def registrar(conn, *, ticker: str, modo: Optional[str], tipo: str, modelo: str,
              setup: Optional[str], recomendacao: Optional[str],
              stop: Optional[float], alvo: Optional[float], preco: Optional[float],
              snapshot_id: Optional[str], confianca=None, user_id=None) -> None:
    """Grava 1 análise (N1 ou N2) pra avaliação futura. Só faz sentido quando
    stop/alvo/preço estão definidos (sem risco não dá pra medir R-multiple nem
    decidir lado da operação) — o chamador filtra ANTES de chamar aqui.
    Nunca levanta: best-effort, o chamador decide se loga a falha."""
    if stop is None or alvo is None or preco is None or stop == alvo:
        return
    entry = {
        "id": uuid.uuid4().hex,
        "ticker": ticker, "modo": modo or "estudo", "tipo": tipo, "modelo": modelo,
        "setup": setup, "recomendacao": recomendacao,
        "stopProposto": float(stop), "alvoProposto": float(alvo), "precoNaAnalise": float(preco),
        "snapshotId": snapshot_id,
        # qa/35 (P2c): confiança DECLARADA pela IA na hora da análise — vira a
        # base da calibração (declarada × acerto real). None = IA não declarou.
        "confianca": normalizar_confianca(confianca),
        "criadoEm": datetime.now(timezone.utc).isoformat(),
        "prazoPregoes": HORIZON_PREGOES,
        "resultado": "pendente",
        "precoResolucao": None, "rMultiple": None, "resolvidoEm": None,
    }
    outcomes = db.kv_get(conn, _key(), [], user_id=user_id) or []
    outcomes.append(entry)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_DIAS)).isoformat()
    outcomes = [o for o in outcomes if (o.get("criadoEm") or "") >= cutoff]
    if len(outcomes) > CAP:
        outcomes = outcomes[-CAP:]
    db.kv_set(conn, _key(), outcomes, user_id=user_id)


def _celula(resolvidos: list) -> dict:
    """Métricas de UMA célula de segmentação (qa/35 P2). Puro. Abaixo de
    MIN_N devolve n + insuficiente=True e NENHUMA porcentagem — regra do
    Alex: amostra pequena não vira % enganosa."""
    n = len(resolvidos)
    if n < MIN_N:
        return {"n": n, "insuficiente": True, "taxaAcerto": None, "rMedio": None}
    sucesso = [o for o in resolvidos if o.get("resultado") in RESULTADOS_SUCESSO]
    r_vals = [o["rMultiple"] for o in resolvidos if o.get("rMultiple") is not None]
    return {
        "n": n, "insuficiente": False,
        "taxaAcerto": round(100 * len(sucesso) / n, 1),
        "rMedio": round(sum(r_vals) / len(r_vals), 2) if r_vals else None,
    }


def compute_stats(outcomes: list, modo: Optional[str] = None, tipo: Optional[str] = None) -> dict:
    """Agrega taxa de acerto / R médio / recorte por setup — usado pelo painel
    'Eficiência da IA'. Puro (sem I/O). qa/35 (P2, camadas a+c decididas com o
    Alex): + expectância (R médio por análise), profit factor e calibração da
    confiança declarada (alta×moderada×baixa) e por decisão. TODO cálculo aqui
    em Python — a LLM não calcula nada."""
    filtrado = [o for o in (outcomes or [])
                if (modo is None or o.get("modo") == modo) and (tipo is None or o.get("tipo") == tipo)]
    resolvidos = [o for o in filtrado if o.get("resultado") not in (None, "pendente")]
    pendentes = [o for o in filtrado if o.get("resultado") == "pendente"]
    sucesso = [o for o in resolvidos if o.get("resultado") in RESULTADOS_SUCESSO]
    r_valores = [o["rMultiple"] for o in resolvidos if o.get("rMultiple") is not None]
    por_setup: dict = {}
    for o in resolvidos:
        s = o.get("setup") or "—"
        d = por_setup.setdefault(s, {"acerto": 0, "total": 0})
        d["total"] += 1
        if o.get("resultado") in RESULTADOS_SUCESSO:
            d["acerto"] += 1

    # --- qa/35 P2a: expectância -------------------------------------------------
    # Expectância por análise = média dos R-múltiplos (o rMedio de sempre, agora
    # nomeado como o que é). Profit factor = soma dos R positivos / |soma dos
    # negativos|. Com menos de MIN_N avaliadas, tudo vira "n insuficiente".
    suficiente = len(resolvidos) >= MIN_N
    r_pos = sum(r for r in r_valores if r > 0)
    r_neg = sum(r for r in r_valores if r < 0)
    profit_factor = None
    if suficiente and r_valores:
        if r_neg == 0:
            profit_factor = None if r_pos == 0 else float("inf")
        else:
            profit_factor = round(r_pos / abs(r_neg), 2)
    expectancia = round(sum(r_valores) / len(r_valores), 2) if (suficiente and r_valores) else None

    # --- qa/35 P2c: calibração --------------------------------------------------
    # A confiança que a IA DECLAROU bate com o acerto real? Célula por nível
    # declarado (alta/moderada/baixa; "—" = análises antigas sem o campo) e por
    # decisão (recomendacao). Cada célula respeita MIN_N.
    por_confianca: dict = {}
    por_decisao: dict = {}
    for o in resolvidos:
        por_confianca.setdefault(o.get("confianca") or "—", []).append(o)
        por_decisao.setdefault((o.get("recomendacao") or "—").strip() or "—", []).append(o)

    return {
        "totalAnalises": len(filtrado),
        "avaliadas": len(resolvidos),
        "pendentes": len(pendentes),
        "taxaAcerto": round(100 * len(sucesso) / len(resolvidos), 1) if resolvidos else None,
        "rMedio": round(sum(r_valores) / len(r_valores), 2) if r_valores else None,
        "porSetup": por_setup,
        # qa/35 P2 (a+c) — minN vai junto pro painel explicar a régua.
        "minN": MIN_N,
        "expectancia": expectancia,
        "profitFactor": ("inf" if profit_factor == float("inf") else profit_factor),
        "expectanciaInsuficiente": not suficiente,
        "porConfianca": {k: _celula(v) for k, v in por_confianca.items()},
        "porDecisao": {k: _celula(v) for k, v in por_decisao.items()},
    }


def to_csv(outcomes: list) -> str:
    """Export CSV das análises registradas (qa/35 P2) — colunas fixas, uma
    linha por análise; célula vazia = dado indisponível (nunca inferido)."""
    cols = ("id", "ticker", "modo", "tipo", "modelo", "setup", "recomendacao",
            "confianca", "stopProposto", "alvoProposto", "precoNaAnalise",
            "snapshotId", "criadoEm", "prazoPregoes", "resultado",
            "precoResolucao", "rMultiple", "resolvidoEm")

    def esc(v) -> str:
        if v is None:
            return ""
        s = str(v)
        return '"' + s.replace('"', '""') + '"' if any(ch in s for ch in ",\"\n") else s

    linhas = [",".join(cols)]
    for o in (outcomes or []):
        linhas.append(",".join(esc(o.get(c)) for c in cols))
    return "\n".join(linhas) + "\n"


def _scopes_com_outcomes(conn) -> list:
    """user_id de cada escopo com analysisOutcomes gravado + o escopo legado
    (global, user_id=None) quando existir — mesmo padrão de
    agent.list_server_users (varre o kv por sufixo de chave)."""
    rows = conn.execute(
        "SELECT key FROM kv WHERE key LIKE 'u:%:analysisOutcomes' OR key = 'analysisOutcomes'"
    ).fetchall()
    out = []
    for (key,) in rows:
        if key == "analysisOutcomes":
            out.append(None)
        else:
            out.append(key[len("u:"):-len(":analysisOutcomes")])
    return out


def _pregoes_apos(candles: list, criado_em: str) -> list:
    """Candles com data ESTRITAMENTE depois do dia da análise, em ordem
    cronológica (o dia da própria análise nunca conta como pregão decorrido)."""
    dia = (criado_em or "")[:10]
    janela = [c for c in (candles or []) if c.get("date") and c["date"] > dia]
    return sorted(janela, key=lambda c: c["date"])


def _avaliar_entry(entry: dict, candles: list) -> Optional[dict]:
    """Decide o resultado de UMA análise pendente dado o histórico de candles
    do ativo. Retorna None se o prazo (10 pregões) ainda não completou —
    mantém pendente. Sem I/O (candles injetados) — testável isoladamente."""
    janela = _pregoes_apos(candles, entry["criadoEm"])
    prazo = entry.get("prazoPregoes") or HORIZON_PREGOES
    if len(janela) < prazo:
        return None
    stop, alvo, preco0 = entry["stopProposto"], entry["alvoProposto"], entry["precoNaAnalise"]
    lado_compra = alvo > stop  # geometria do plano garante isso (setups.py: stop sempre do lado oposto ao alvo)
    resultado = preco_resolucao = resolvido_em = None
    for i, c in enumerate(janela[:prazo]):
        hi, lo = c.get("high"), c.get("low")
        if hi is None or lo is None:
            continue
        bateu_stop = (lo <= stop) if lado_compra else (hi >= stop)
        bateu_alvo = (hi >= alvo) if lado_compra else (lo <= alvo)
        if bateu_stop:  # cenário conservador quando os dois batem no mesmo candle
            resultado, preco_resolucao, resolvido_em = "stop", stop, c["date"]
            break
        if bateu_alvo:
            resultado, preco_resolucao, resolvido_em = "alvo", alvo, c["date"]
            break
    if resultado is None:
        c = janela[prazo - 1]
        fechou_a_favor = (c["close"] >= preco0) == lado_compra
        resultado = "expirou_pos" if fechou_a_favor else "expirou_neg"
        preco_resolucao, resolvido_em = c["close"], c["date"]
    risco = abs(preco0 - stop)
    ganho = (preco_resolucao - preco0) if lado_compra else (preco0 - preco_resolucao)
    r_multiple = round(ganho / risco, 2) if risco else None
    return {"resultado": resultado, "precoResolucao": preco_resolucao,
            "resolvidoEm": resolvido_em, "rMultiple": r_multiple}


async def avaliar_pendentes(conn, fetch) -> int:
    """Varre TODOS os escopos com outcomes pendentes, busca candles (via
    `fetch(ticker, rng=...)`, injetado — mesmo padrão do radar_daily.maybe_run)
    e resolve o que já completou o prazo. Retorna nº de entradas avaliadas."""
    total = 0
    for uid in _scopes_com_outcomes(conn):
        outcomes = db.kv_get(conn, _key(), [], user_id=uid) or []
        pendentes = [o for o in outcomes if o.get("resultado") == "pendente"]
        if not pendentes:
            continue
        por_ticker: dict = {}
        for o in pendentes:
            por_ticker.setdefault(o["ticker"], []).append(o)
        mudou = False
        for ticker, entries in por_ticker.items():
            try:
                hist = await fetch(ticker, rng="6mo")
            except Exception:  # noqa: BLE001 — 1 ativo sem cotação não trava os demais
                continue
            candles = (hist or {}).get("candles") or []
            for entry in entries:
                r = _avaliar_entry(entry, candles)
                if r:
                    entry.update(r)
                    mudou = True
                    total += 1
        if mudou:
            db.kv_set(conn, _key(), outcomes, user_id=uid)
    return total


def _hoje() -> str:
    return datetime.now(BRT).date().isoformat()


async def maybe_run(conn, fetch) -> Optional[int]:
    """Hook do scheduler: roda no máximo 1x/dia (mesmo padrão de
    radar_daily.maybe_run) — não precisa de horário fixo, só de rodar depois
    do fechamento do pregão pelo menos uma vez por dia."""
    if LAST_EVAL["date"] == _hoje():
        return None
    try:
        n = await avaliar_pendentes(conn, fetch)
        LAST_EVAL.update(date=_hoje(), avaliadas=n, erro=None)
        return n
    except Exception as e:  # noqa: BLE001 — nunca derruba o laço do agente
        LAST_EVAL["erro"] = str(e)[:200]
        print(f"[analysis-outcomes] avaliação falhou: {e}")
        return None
