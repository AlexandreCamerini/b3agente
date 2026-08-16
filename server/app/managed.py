"""IA gerenciada (FASE 3, item 2) — caminho PARALELO ao BYOK.

A chave fica no SERVIDOR (env, nunca versionada nem exposta ao cliente) e usa um
modelo barato. Só entra em cena para usuário LOGADO que NÃO tem chave própria;
quem tem BYOK passa direto, sem cota. Se nada estiver configurado no servidor,
`managed_config()` retorna None e o comportamento atual (BYOK/erro acionável)
permanece — ou seja, é 100% aditivo.

Env:
  B3_MANAGED_LLM_KEY        (obrigatória p/ habilitar)
  B3_MANAGED_LLM_PROVIDER   (default: openai)
  B3_MANAGED_LLM_MODEL      (default: gpt-4o-mini — barato)
  B3_MANAGED_LLM_BASE_URL   (opcional, p/ provider compatível)
  B3_MANAGED_DAILY_QUOTA    (default: 20)
  B3_MANAGED_RATE_PER_MIN   (default: 6)
"""
import os

# ADR-013 (Decisão 4, grupo "Mudança de LLM"): provider/model/cota/rate/teto
# global ganham override em runtime (admin_config), lido ANTES do env — MESMO
# padrão que brapi_budget.py já usa (memória → DB → env), generalizado aqui.
# `apiKey`/`baseUrl` ficam DE FORA do override (permanecem só em env) — são
# segredo, e o guardrail do CLAUDE.md sobre segredo só em env do servidor
# vale mesmo dentro do próprio backend: uma tela web não deveria ser o
# caminho de trocar a chave.
_DB_CONN = None
_DB_ENABLED = False


def configure_db(conn) -> None:
    global _DB_CONN, _DB_ENABLED
    _DB_CONN = conn
    _DB_ENABLED = True


def _override(key: str, default=None):
    if not _DB_ENABLED:
        return default
    from . import db
    return db.admin_config_get(_DB_CONN, key, default)


def managed_config():
    """Config de IA gerenciada a partir do ambiente (+ override de provider/
    model via admin), ou None se não habilitada. keySource='managed' deixa
    explícito que a chave é do servidor (e a apiKey NUNCA volta ao cliente —
    public_state já remove qualquer apiKey)."""
    key = (os.environ.get("B3_MANAGED_LLM_KEY") or "").strip()
    if not key:
        return None
    cfg = {
        "provider": _override("llmProvider", os.environ.get("B3_MANAGED_LLM_PROVIDER", "openai")),
        "model": _override("llmModel", os.environ.get("B3_MANAGED_LLM_MODEL", "gpt-4o-mini")),
        "apiKey": key,
        "keySource": "managed",
    }
    base = (os.environ.get("B3_MANAGED_LLM_BASE_URL") or "").strip()
    if base:
        cfg["baseUrl"] = base
        if cfg["provider"] not in ("openai", "anthropic", "google", "local"):
            cfg["provider"] = "local"
    return cfg


def global_daily_cap():
    """qa/42 (FinOps): teto GLOBAL de análises gerenciadas por dia, somando
    TODOS os usuários (override admin, senão env B3_MANAGED_GLOBAL_DAILY_CAP).
    None = ilimitado. É a única defesa contra o gasto escalar com o nº de
    usuários — a cota diária é POR usuário e não agrega."""
    override = _override("llmGlobalDailyCap")
    if override is not None:
        return override if isinstance(override, int) and override > 0 else None
    raw = (os.environ.get("B3_MANAGED_GLOBAL_DAILY_CAP") or "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def daily_quota() -> int:
    override = _override("llmDailyQuota")
    if isinstance(override, int):
        return override
    return _int_env("B3_MANAGED_DAILY_QUOTA", 20)


def rate_per_min() -> int:
    override = _override("llmRatePerMin")
    if isinstance(override, int):
        return override
    return _int_env("B3_MANAGED_RATE_PER_MIN", 6)


def is_available() -> bool:
    return managed_config() is not None
