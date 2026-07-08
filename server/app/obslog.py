"""FASE 5 — Observabilidade: log estruturado + ring buffer consultável.

Objetivo: todos os eventos relevantes do servidor (requests, lentidão, auth,
scan, LLM, push, cache, erros) num formato ÚNICO, com dois destinos:

  1. stdout (logging) — aparece nos logs do Railway como sempre, agora com
     timestamp, nível e categoria padronizados:  [b3][cat] mensagem
  2. ring buffer em memória (cap 1000) — consultável em GET /api/obs/logs,
     alimenta a tela Perfil → Observabilidade sem depender do painel do Railway.

Stdlib-only, thread-safe, nunca levanta: log é observabilidade, não pode
derrubar o fluxo que está observando. Testável offline (mini-runner no fim).
"""
from collections import Counter, deque
from datetime import datetime
import logging
import threading
import time

_MAX = 1000
_buffer: deque = deque(maxlen=_MAX)
_lock = threading.Lock()
_counters: Counter = Counter()          # "cat:level" -> quantos (desde o boot)
_boot_at = time.time()

_logger = logging.getLogger("b3")
if not _logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    _logger.addHandler(_h)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False

_LEVELS = {"debug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARNING, "error": logging.ERROR}


def log(cat: str, msg: str, level: str = "info", **extra) -> None:
    """Registra um evento. cat curto e estável (req, slow, auth, scan, llm,
    push, cache, agent, err); extra vira sufixo k=v na linha e campos no buffer."""
    try:
        lv = level if level in _LEVELS else "info"
        entry = {
            "ts": datetime.now().strftime("%d/%m %H:%M:%S"),
            "at": time.time(),
            "level": lv,
            "cat": str(cat or "app")[:16],
            "msg": str(msg)[:500],
        }
        if extra:
            entry["extra"] = {k: (str(v)[:200]) for k, v in extra.items()}
        with _lock:
            _buffer.append(entry)
            _counters[entry["cat"] + ":" + lv] += 1
        suffix = (" " + " ".join(f"{k}={v}" for k, v in (entry.get("extra") or {}).items())) if extra else ""
        _logger.log(_LEVELS[lv], "[b3][%s] %s%s", entry["cat"], entry["msg"], suffix)
    except Exception:  # noqa: BLE001 — log nunca quebra o chamador
        pass


def recent(n: int = 200, level: str = None, cat: str = None) -> list:
    """Últimos eventos (mais novos primeiro), com filtro opcional por nível
    mínimo ('warn' => warn+error) e categoria."""
    order = ["debug", "info", "warn", "error"]
    min_i = order.index(level) if level in order else 0
    with _lock:
        items = list(_buffer)
    out = []
    for e in reversed(items):
        if order.index(e["level"]) < min_i:
            continue
        if cat and e["cat"] != cat:
            continue
        out.append(e)
        if len(out) >= max(1, min(int(n or 200), _MAX)):
            break
    return out


def stats() -> dict:
    """Resumo desde o boot: uptime, total por categoria/nível, tamanho do buffer."""
    with _lock:
        counts = dict(_counters)
        size = len(_buffer)
    cats: dict = {}
    for key, v in counts.items():
        c, lv = key.rsplit(":", 1)
        cats.setdefault(c, {})[lv] = v
    return {
        "uptimeS": int(time.time() - _boot_at),
        "bufferSize": size,
        "bufferMax": _MAX,
        "porCategoria": cats,
    }


def reset() -> None:
    """Para testes."""
    with _lock:
        _buffer.clear()
        _counters.clear()


if __name__ == "__main__":
    # mini-runner (padrão do projeto): valida o contrato sem pytest/rede.
    fails = 0

    def ok(name, cond):
        global fails
        print(("ok " if cond else "FALHOU ") + name)
        if not cond:
            fails += 1

    reset()
    log("req", "GET /api/state", ip="1.2.3.4")
    log("slow", "GET /api/scan levou 3.2s", level="warn", dur="3.2")
    log("err", "explodiu", level="error")
    r = recent(10)
    ok("3 eventos no buffer", len(r) == 3)
    ok("mais novo primeiro", r[0]["cat"] == "err")
    ok("extra preservado", r[2].get("extra", {}).get("ip") == "1.2.3.4")
    ok("filtro por nível warn+", len(recent(10, level="warn")) == 2)
    ok("filtro por categoria", len(recent(10, cat="slow")) == 1)
    s = stats()
    ok("stats por categoria", s["porCategoria"].get("err", {}).get("error") == 1)
    ok("nível inválido não quebra", (log("x", "y", level="banana"), True)[1])
    ok("msg não-string não quebra", (log("x", {"a": 1}), True)[1])
    # cap do buffer
    reset()
    for i in range(1100):
        log("cap", str(i))
    ok("buffer respeita o cap", len(recent(2000)) == _MAX)
    print("\n%d falha(s)" % fails if fails else "\ntodos os testes passaram")
    raise SystemExit(1 if fails else 0)
