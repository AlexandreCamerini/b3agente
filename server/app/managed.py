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


def managed_config():
    """Config de IA gerenciada a partir do ambiente, ou None se não habilitada.
    keySource='managed' deixa explícito que a chave é do servidor (e a apiKey
    NUNCA volta ao cliente — public_state já remove qualquer apiKey)."""
    key = (os.environ.get("B3_MANAGED_LLM_KEY") or "").strip()
    if not key:
        return None
    cfg = {
        "provider": os.environ.get("B3_MANAGED_LLM_PROVIDER", "openai"),
        "model": os.environ.get("B3_MANAGED_LLM_MODEL", "gpt-4o-mini"),
        "apiKey": key,
        "keySource": "managed",
    }
    base = (os.environ.get("B3_MANAGED_LLM_BASE_URL") or "").strip()
    if base:
        cfg["baseUrl"] = base
        if cfg["provider"] not in ("openai", "anthropic", "google", "local"):
            cfg["provider"] = "local"
    return cfg


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def daily_quota() -> int:
    return _int_env("B3_MANAGED_DAILY_QUOTA", 20)


def rate_per_min() -> int:
    return _int_env("B3_MANAGED_RATE_PER_MIN", 6)


def is_available() -> bool:
    return managed_config() is not None
