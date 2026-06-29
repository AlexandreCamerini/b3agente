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


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load(conn, user_id) -> dict:
    u = db.kv_get(conn, SECTION, None, user_id=user_id)
    if not isinstance(u, dict) or u.get("day") != _today():
        return {"day": _today(), "count": 0, "rl": []}
    if not isinstance(u.get("rl"), list):
        u["rl"] = []
    if not isinstance(u.get("count"), int):
        u["count"] = 0
    return u


def _save(conn, user_id, u) -> None:
    db.kv_set(conn, SECTION, u, user_id=user_id)


def check(conn, user_id, *, quota, rate_per_min, _now=None):
    """(permitido, motivo). Registra o uso para o rate limit; NÃO consome a cota
    diária (isso é no consume, após sucesso)."""
    u = _load(conn, user_id)
    now = time.time() if _now is None else _now
    u["rl"] = [t for t in u["rl"] if (now - t) < 60.0]
    if rate_per_min is not None and len(u["rl"]) >= rate_per_min:
        _save(conn, user_id, u)
        return (False, "Muitas análises em pouco tempo. Aguarde alguns segundos e tente de novo.")
    if quota is not None and u["count"] >= quota:
        _save(conn, user_id, u)
        return (False, (
            "Você atingiu o limite diário de %d análises com a IA do app. "
            "Use sua própria chave (BYOK) em Perfil → Conta & preferências para "
            "análises ilimitadas, ou volte amanhã." % quota
        ))
    u["rl"].append(now)
    _save(conn, user_id, u)
    return (True, None)


def consume(conn, user_id) -> int:
    """Conta UMA análise gerenciada (chamar após o LLM responder com sucesso)."""
    u = _load(conn, user_id)
    u["count"] = int(u.get("count", 0)) + 1
    _save(conn, user_id, u)
    return u["count"]


def snapshot(conn, user_id, quota) -> dict:
    u = _load(conn, user_id)
    used = int(u.get("count", 0))
    remaining = None if quota is None else max(0, quota - used)
    return {"day": u["day"], "used": used, "quota": quota, "remaining": remaining}
