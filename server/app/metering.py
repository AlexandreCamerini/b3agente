"""Metering da IA gerenciada (FASE 3, item 2): cota DIÁRIA + rate limit por
usuário, persistidos no KV ESCOPADO por user_id (seção `aiUsage`). Stdlib,
testável offline. BYOK não passa por aqui.

Fluxo nas rotas:
  ok, reason = metering.check(conn, uid, quota=..., rate_per_min=...)
  if not ok: -> 402 reason
  ... chama o LLM ...
  metering.consume(conn, uid)   # só conta no SUCESSO (falha não gasta cota)

`check` registra o timestamp para o rate limit (impede martelar), mas NÃO conta
a cota diária — quem conta é `consume`, após a resposta vir.
"""
from datetime import datetime, timezone
import time

from . import db

SECTION = "aiUsage"
GLOBAL_SECTION = "aiUsageGlobal"   # qa/42: contador GLOBAL (kv sem escopo de usuário)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_global(conn, section: str = GLOBAL_SECTION) -> dict:
    g = db.kv_get(conn, section, None, user_id=None)
    if not isinstance(g, dict) or g.get("day") != _today():
        return {"day": _today(), "count": 0}
    if not isinstance(g.get("count"), int):
        g["count"] = 0
    return g


def global_snapshot(conn, cap=None, section: str = GLOBAL_SECTION) -> dict:
    """qa/42 (FinOps): quanto a IA gerenciada gastou HOJE somando todos os
    usuários. Antes não existia contador agregado — a cota era só por usuário,
    então o gasto do servidor era (nº de usuários) × cota, SEM teto superior."""
    g = _load_global(conn, section=section)
    used = int(g.get("count", 0))
    return {"day": g["day"], "used": used, "cap": cap,
            "remaining": None if cap is None else max(0, cap - used)}


def _load(conn, user_id, section: str = SECTION) -> dict:
    u = db.kv_get(conn, section, None, user_id=user_id)
    if not isinstance(u, dict) or u.get("day") != _today():
        return {"day": _today(), "count": 0, "rl": []}
    if not isinstance(u.get("rl"), list):
        u["rl"] = []
    if not isinstance(u.get("count"), int):
        u["count"] = 0
    return u


def _save(conn, user_id, u, section: str = SECTION) -> None:
    db.kv_set(conn, section, u, user_id=user_id)


# qa/47: `section`/`global_section` permitem reusar este módulo para OUTRO
# domínio de cota (ex. ingest de analytics) sem misturar o balde de contagem
# com o da IA gerenciada — cada chamador usa sua própria chave de kv. Default
# preserva o comportamento anterior (todos os call sites de IA continuam
# implícitos em SECTION/GLOBAL_SECTION).
def check(conn, user_id, *, quota, rate_per_min, custo=1, cap_global=None, _now=None,
          section: str = SECTION, global_section: str = GLOBAL_SECTION):
    """(permitido, motivo). Registra o uso para o rate limit; NÃO consome a cota
    diária (isso é no consume, após sucesso).

    qa/42 (FinOps): `custo` = quantas análises ESTE request pode disparar.
    O /api/scan/deep chamava check 1x e consume até 10x (1 por ticker do
    top-N) — quem tinha 19/20 passava no check e terminava em 29. Reservar o
    custo na COTA fecha o furo. O rate limit segue contando 1 por REQUEST
    (ele existe para impedir martelar): reservar 10 slots num teto de 6/min
    bloquearia todo deep."""
    u = _load(conn, user_id, section=section)
    now = time.time() if _now is None else _now
    custo = max(1, int(custo or 1))
    u["rl"] = [t for t in u["rl"] if (now - t) < 60.0]
    if rate_per_min is not None and len(u["rl"]) >= rate_per_min:
        _save(conn, user_id, u, section=section)
        return (False, "Muitas análises em pouco tempo. Aguarde alguns segundos e tente de novo.")
    if quota is not None and u["count"] + custo > quota:
        _save(conn, user_id, u, section=section)
        restam = max(0, quota - int(u.get("count", 0)))
        if custo > 1 and restam > 0:
            return (False, (
                "Esta varredura profunda faria %d análises e você tem %d restante(s) "
                "hoje (limite diário: %d). Reduza o número de ativos, use sua própria "
                "chave (BYOK) em Perfil → Conta & preferências para análises "
                "ilimitadas, ou volte amanhã." % (custo, restam, quota)
            ))
        return (False, (
            "Você atingiu o limite diário de %d análises com a IA do app. "
            "Use sua própria chave (BYOK) em Perfil → Conta & preferências para "
            "análises ilimitadas, ou volte amanhã." % quota
        ))
    # qa/42 (FinOps): teto GLOBAL — a última linha de defesa do bolso. Sem ele,
    # o gasto do servidor era (nº de usuários) × cota/dia, ilimitado por cima.
    # cap_global=None (default) => ilimitado => comportamento anterior intacto.
    if cap_global is not None and _load_global(conn, section=global_section)["count"] + custo > cap_global:
        _save(conn, user_id, u, section=section)
        return (False, (
            "A IA do app atingiu o limite de uso de hoje (teto global do servidor). "
            "Use sua própria chave (BYOK) em Perfil → Conta & preferências para "
            "análises ilimitadas, ou volte amanhã."
        ))
    u["rl"].append(now)
    _save(conn, user_id, u, section=section)
    return (True, None)


def consume(conn, user_id, *, custo: int = 1, section: str = SECTION, global_section: str = GLOBAL_SECTION) -> int:
    """Conta análise(s) gerenciada(s) (chamar após o LLM responder com sucesso,
    ou — qa/47 — após um lote de eventos de analytics ser aceito).
    qa/42: conta no contador do usuário E no global (teto de gasto do servidor).
    qa/47: `custo` permite contar um LOTE inteiro numa chamada (em vez de
    laçar `consume()` N vezes) — default 1 preserva o comportamento anterior."""
    custo = max(1, int(custo or 1))
    u = _load(conn, user_id, section=section)
    u["count"] = int(u.get("count", 0)) + custo
    _save(conn, user_id, u, section=section)
    g = _load_global(conn, section=global_section)
    g["count"] = int(g.get("count", 0)) + custo
    db.kv_set(conn, global_section, g, user_id=None)
    return u["count"]


def snapshot(conn, user_id, quota, section: str = SECTION) -> dict:
    u = _load(conn, user_id, section=section)
    used = int(u.get("count", 0))
    remaining = None if quota is None else max(0, quota - used)
    return {"day": u["day"], "used": used, "quota": quota, "remaining": remaining}
