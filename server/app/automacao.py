"""ADR-012 (Fase 3) — eficiência das operações automáticas do Operador.

Duas perguntas, cada uma com sua função:
1. `resumo_por_origem`: quantas ordens e qual PnL agregado por origem
   (manual|automatico|sistema) — `sistema` é liquidação por expiração
   (ADR-005), não decisão do Operador, por isso separada de `automatico`.
2. `correlacao_analise_operacao`: das análises que a IA registrou
   (analysis_outcomes), quantas viraram ordem — cruzamento por `snapshotId`,
   a chave que já existe nos dois lados (`history` e `analysisOutcomes`).

NÃO mede "tempo de reação" nem "slippage vs. previsto" — esse dado não
existe no sistema hoje (não há timestamp de quando um gatilho disparou nem
preço-alvo de execução registrado à parte); não é fabricado aqui.

Cobertura é PARCIAL por natureza: `snapshotId` é campo opcional que o
cliente manda na hora da ordem (`_sanitize_trade_meta`, store.py), nem toda
ordem carrega. A função devolve o percentual de cobertura explicitamente —
nunca esconde a lacuna atrás de um número que pareça completo.

Histórico anterior a esta feature não tem a chave `origem` — cai no balde
"desconhecida", não é reescrito nem adivinhado.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from . import analysis_outcomes, store

BRT = timezone(timedelta(hours=-3))

# Telemetria em memória do último refresh (mesmo padrão de LAST_EVAL/LAST_ROLLUP).
LAST_CACHE_REFRESH = {"date": None, "erro": None}


def _todas_as_ordens(conn) -> list:
    """Concatena `history` de todos os escopos — agregado, nunca
    identificável por usuário no retorno público (mesma regra de
    analysis_outcomes.outcomes_de_todos_os_usuarios)."""
    todas: list = []
    for uid in store.scopes_com_history(conn):
        todas.extend(store.get(conn, "history", user_id=uid) or [])
    return todas


def resumo_por_origem(conn) -> dict:
    """Contagem e PnL agregado por origem. PnL só soma entradas que TÊM pnl
    (vendas — compra sempre grava `pnl: None`)."""
    ordens = _todas_as_ordens(conn)
    por_origem: dict = {}
    for o in ordens:
        origem = o.get("origem") or "desconhecida"
        d = por_origem.setdefault(origem, {"ordens": 0, "pnlTotal": 0.0, "pnlContagem": 0})
        d["ordens"] += 1
        if isinstance(o.get("pnl"), (int, float)):
            d["pnlTotal"] = round(d["pnlTotal"] + o["pnl"], 2)
            d["pnlContagem"] += 1
    for d in por_origem.values():
        d["pnlTotal"] = round(d["pnlTotal"], 2)
    return {"totalOrdens": len(ordens), "porOrigem": por_origem}


def correlacao_analise_operacao(conn) -> dict:
    """Cruza ordens de ENTRADA (COMPRA) com análises da IA por `snapshotId`.
    `seguiuAnaliseComSucesso` só conta análises já RESOLVIDAS (não
    'pendente') cujo resultado é sucesso (alvo|expirou_pos) — mesma régua de
    analysis_outcomes.RESULTADOS_SUCESSO. Desfechos neutros
    (analysis_outcomes.RESULTADOS_NEUTROS, ex.: `sem_gatilho` — ADR15-02)
    também NÃO contam como resolvidos: o gatilho nunca foi tocado, a
    correlação nunca aconteceu, e deixá-la em `resolvidas` diluiria
    `seguiuAnaliseComSucesso / resolvidas` com um desfecho que não é acerto
    nem erro."""
    ordens = _todas_as_ordens(conn)
    ordens_entrada = [o for o in ordens if o.get("type") == "COMPRA"]
    com_snapshot = [o for o in ordens_entrada if o.get("snapshotId")]

    analises = analysis_outcomes.outcomes_de_todos_os_usuarios(conn)
    por_snapshot = {a["snapshotId"]: a for a in analises if a.get("snapshotId")}

    vinculadas = [
        {"origem": o.get("origem") or "desconhecida", "resultadoAnalise": por_snapshot[o["snapshotId"]].get("resultado")}
        for o in com_snapshot if o["snapshotId"] in por_snapshot
    ]
    resolvidas = [v for v in vinculadas
                  if v["resultadoAnalise"] not in (None, "pendente", *analysis_outcomes.RESULTADOS_NEUTROS)]
    nao_acionadas = [v for v in vinculadas if v["resultadoAnalise"] in analysis_outcomes.RESULTADOS_NEUTROS]
    sucesso = [v for v in resolvidas if v["resultadoAnalise"] in analysis_outcomes.RESULTADOS_SUCESSO]

    return {
        "ordensDeEntrada": len(ordens_entrada),
        "comSnapshotVinculado": len(com_snapshot),
        "coberturaPct": round(100 * len(com_snapshot) / len(ordens_entrada), 1) if ordens_entrada else None,
        "vinculadasComAnaliseRegistrada": len(vinculadas),
        "resolvidas": len(resolvidas),
        # ADR15-02: aditivo — a fatia de `vinculadas` que ficou fora de
        # `resolvidas` por ser sem_gatilho, para o painel mostrar o que saiu
        # em vez de sumir com o número.
        "naoAcionadas": len(nao_acionadas),
        "seguiuAnaliseComSucesso": len(sucesso),
    }


def _hoje() -> str:
    return datetime.now(BRT).date().isoformat()


def maybe_refresh_cache(conn, cache_conn) -> Optional[bool]:
    """Hook do scheduler (agent.py): recomputa os agregados 1x/dia (mesmo
    padrão de analysis_outcomes.maybe_run/analytics.maybe_run) — o GET admin
    só lê o cache, nunca recalcula síncrono numa request (exceto cold-start,
    tratado no endpoint). Sem I/O de rede: não precisa de `fetch` injetado."""
    hoje = _hoje()
    if LAST_CACHE_REFRESH["date"] == hoje:
        return None
    try:
        from . import analytics as analytics_mod  # import local: sem ciclo de import
        analytics_mod.set_cache(cache_conn, "automacao_resumo", resumo_por_origem(conn))
        analytics_mod.set_cache(cache_conn, "automacao_correlacao", correlacao_analise_operacao(conn))
        LAST_CACHE_REFRESH.update(date=hoje, erro=None)
        return True
    except Exception as e:  # noqa: BLE001 — cache nunca derruba o laço do agente
        LAST_CACHE_REFRESH["erro"] = str(e)[:200]
        print(f"[automacao] refresh do cache admin falhou: {e}")
        return None
