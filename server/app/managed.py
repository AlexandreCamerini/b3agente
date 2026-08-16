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
# Achado de revisão: `_override` fazia uma leitura SÍNCRONA de SQLite (sem
# cache) em CADA chamada — até 5 por request de IA gerenciada (provider,
# model, cota, rate, teto), no caminho mais quente do app. Cache em memória
# aqui, mesmo padrão de `agent.kill_switch_on`/`brapi_budget.spot_intervalo_s`
# — só é limpo por escrita admin (`reset_cache`, chamada pela rota) ou teste.
_CACHE: dict = {}


def configure_db(conn) -> None:
    global _DB_CONN, _DB_ENABLED
    _DB_CONN = conn
    _DB_ENABLED = True


def reset_cache() -> None:
    """Chamado pela rota admin após escrever (`PUT /api/admin/config/ia`) e
    por testes que trocam de banco entre casos — mesmo motivo do
    `agent.reset_kill_switch_cache()`/`brapi_budget.reset()`."""
    global _CACHE
    _CACHE = {}


def _override(key: str, default=None):
    if not _DB_ENABLED:
        return default
    if key in _CACHE:
        return _CACHE[key]
    try:
        from . import db
        val = db.admin_config_get(_DB_CONN, key, default)
    except Exception:  # noqa: BLE001 — degrada pro default, nunca derruba o caminho de IA
        val = default
    _CACHE[key] = val
    return val


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
    usuários — a cota diária é POR usuário e não agrega.

    A env `B3_MANAGED_GLOBAL_DAILY_CAP=0` continua significando "ilimitado"
    (test_qa42_finops.py:120, decisão deliberada — 0 num valor de deploy é
    fácil de ser acidente/typo, e bloquear tudo em silêncio é pior que não
    ter teto). O OVERRIDE do admin (ADR-013) é diferente: alguém digitando 0
    no painel, ao vivo, num incidente de custo, tem intenção inequívoca de
    bloquear — achado de revisão: antes isso também virava "ilimitado", o
    oposto do que a pessoa pediu. `metering.check` já trata `count+custo>0`
    corretamente (0 bloqueia qualquer uso), então só o override aceita 0."""
    override = _override("llmGlobalDailyCap")
    if override is not None:
        return override if isinstance(override, int) and override >= 0 else None
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
