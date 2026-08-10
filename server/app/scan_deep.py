"""FASE 1 (N1) — Aprofundamento IA do Radar (modelo HÍBRIDO por custo).

O scanner determinístico varre TODO o universo de graça; a IA aprofunda SÓ o
top-N por confluência (config `radarAiTopN`, default 5, teto 10). Uma chamada
de LLM por ativo, com cache por (ticker, período, DIA) — repetir a varredura
no mesmo dia não repaga. `estimate()` informa custo/chamadas ANTES de rodar.

Guardrail: os textos fixos daqui e o prompt (llm.DEEP_FORMAT) são educacionais;
nenhum verbo de ordem. Puro/testável: a chamada de IA entra por injeção.
"""
import asyncio
import hashlib
import json
import time
from typing import Optional

DEFAULT_TOP_N = 5
MAX_TOP_N = 10

_DEEP_CACHE: dict = {}   # (ticker, period, yyyy-mm-dd) -> payload do ativo


def reset():
    """Para testes."""
    _DEEP_CACHE.clear()


def _day() -> str:
    return time.strftime("%Y-%m-%d")


def leitor_fp(profile: dict = None, config: dict = None) -> str:
    """Identidade de QUEM pergunta, nas dimensões que mudam a resposta.

    O perfil de risco entra no prompt (`llm._profile_line`: risco, horizonte,
    tolerância de perda, objetivo, experiência) e o modelo escolhe a voz. Sem
    isso na chave, este cache — que é GLOBAL — servia a leitura escrita para um
    conservador a um arrojado, e entregava a um usuário o texto gerado com a
    chave de IA de outro (inclusive BYOK pagando pela resposta alheia, e
    recebendo um modelo diferente do que configurou).
    """
    p = profile or {}
    c = config or {}
    cru = json.dumps([
        p.get("risco"), p.get("horizonte"), p.get("toleranciaPerdaPct"),
        p.get("objetivo"), p.get("experiencia"),
        c.get("provider"), c.get("model"), c.get("keySource"),
    ], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(cru.encode("utf-8")).hexdigest()[:10]


def _key(item: dict, period: str, modo: str = None, leitor: str = "") -> tuple:
    """FASE 1 (STU): o cache do deep é indexado pelo snapshotId — se o STU
    mudou (novo candle), a leitura é refeita; se não mudou, não repaga.
    Fallback no dia para itens antigos sem snapshotId.
    FASE 8B (B3): o MODO entra na chave — a leitura da mesa (operador) e a do
    professor (estudo) são textos diferentes do MESMO snapshot; sem isso, o
    cache de um modo vazava no outro.
    `leitor`: perfil + modelo de quem pergunta (ver `leitor_fp`) — o que faltava
    para o cache global parar de misturar leituras personalizadas."""
    return (item["ticker"], period, item.get("snapshotId") or _day(),
            "operador" if modo == "operador" else "estudo", leitor or "")


def resolve_top_n(requested, config: Optional[dict] = None) -> int:
    """Prioridade: pedido explícito > config radarAiTopN > default. Teto fixo."""
    for cand in (requested, (config or {}).get("radarAiTopN"), DEFAULT_TOP_N):
        try:
            n = int(cand)
            if n > 0:
                return min(n, MAX_TOP_N)
        except (TypeError, ValueError):
            continue
    return DEFAULT_TOP_N


def select_top(scan_payload: dict, top_n: int) -> list:
    """Top-N do resultado do scan (já rankeado por confluência). Ignora ativos
    sem nenhum setup/condição (nada para a IA aprofundar)."""
    results = (scan_payload or {}).get("results") or []
    picked = [r for r in results if (r.get("confluencia") or 0) > 0 or r.get("condicoes_detectadas")]
    return picked[:max(0, top_n)]


def estimate(scan_payload: dict, top_n: int, period: str, modo: str = None, leitor: str = "") -> dict:
    """Quantas chamadas NOVAS de IA a varredura profunda vai custar agora
    (exibido na UI antes de rodar; cache do dia não repaga)."""
    sel = select_top(scan_payload, top_n)
    cached = [r["ticker"] for r in sel if _key(r, period, modo, leitor) in _DEEP_CACHE]
    novas = [r["ticker"] for r in sel if _key(r, period, modo, leitor) not in _DEEP_CACHE]
    return {
        "topN": top_n, "selecionados": [r["ticker"] for r in sel],
        "emCache": cached, "novasChamadasIA": novas, "chamadas": len(novas),
    }


async def run_deep(scan_payload: dict, top_n: int, period: str, deep_call, concurrency: int = 2, modo: str = None, leitor: str = "") -> dict:
    """Roda o aprofundamento no top-N. `deep_call(item)` é a função (injetada)
    que faz UMA chamada de IA para um item do scan e devolve o dict da leitura.
    Erro em um ativo não derruba os demais (cai em `errors`)."""
    sel = select_top(scan_payload, top_n)
    sem = asyncio.Semaphore(max(1, concurrency))
    results, errors = [], []

    async def one(item):
        t = item["ticker"]
        key = _key(item, period, modo, leitor)
        hit = _DEEP_CACHE.get(key)
        if hit is not None:
            results.append({**hit, "cache": True})
            return
        async with sem:
            try:
                deep = await deep_call(item)
                payload = {
                    "ticker": t,
                    "snapshotId": item.get("snapshotId"),
                    "snapshotAt": item.get("snapshotAt"),
                    "confluencia": item.get("confluencia"),
                    "melhorSetup": item.get("melhorSetup"),
                    "deep": deep,
                    "cache": False,
                }
                _DEEP_CACHE[key] = {k: v for k, v in payload.items() if k != "cache"}
                results.append(payload)
            except Exception as e:  # noqa: BLE001 — 1 ativo não derruba o deep
                errors.append({"ticker": t, "erro": str(e) or type(e).__name__})

    await asyncio.gather(*(one(it) for it in sel))
    order = {it["ticker"]: i for i, it in enumerate(sel)}
    results.sort(key=lambda r: order.get(r["ticker"], 99))
    return {
        "period": period,
        "topN": top_n,
        "analisados": len(results),
        "results": results,
        "errors": errors,
        "disclaimer": (
            "Aprofundamento educacional: a IA interpreta dados técnicos pré-"
            "calculados de dados passados, sem garantia de resultado e sem "
            "qualquer recomendação de investimento. Use para estudar a leitura."
        ),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
