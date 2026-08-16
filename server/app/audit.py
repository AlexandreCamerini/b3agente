"""ADR-013 — auditoria de escrita administrativa. Stdlib-only, mesmo padrão
de `metering.py`: uma função central chamada por TODA rota de escrita admin,
sem exceção "por enquanto" (restrição do ADR-013). Quem, quando, o quê, valor
antigo, valor novo — nunca um write silencioso.
"""
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def record(conn, actor_id: str, entity: str, entity_id, field, old_value, new_value) -> None:
    from . import db
    db.audit_insert(conn, actor_id, _now_iso(), entity,
                    str(entity_id) if entity_id is not None else None,
                    field, old_value, new_value)


def recent(conn, limit: int = 200) -> list:
    from . import db
    return db.audit_recent(conn, limit=limit)
