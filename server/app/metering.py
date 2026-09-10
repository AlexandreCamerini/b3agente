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

2026-09-09 (aba-opcoes F1, ADR-027) — overrides `_dia`/`_mes`. Achado do
inventário: `_now` NÃO decide o dia. `check(..., _now=...)` só alimenta o
rate limit (`now - t < 60.0`, epoch float); o dia sempre saiu de `_today()`,
que lê `datetime.now(timezone.utc)` e não tinha ponto de injeção. A aba
Opções precisa do MESMO reset que o serviço MCP usa (00:00
America/Sao_Paulo), senão o cap do usuário viraria três horas antes do teto
do serviço e o app recusaria chamada que o serviço ainda aceitaria (e
vice-versa, pior: liberaria depois que o serviço já recusou).

Solução: quem chama passa o dia/mês PRONTOS. `_dia=None`/`_mes=None`
(default) preservam o comportamento anterior byte a byte — nenhum call site
de IA gerenciada muda. `_dia` e `_mes` sempre viajam JUNTOS, pela mesma
regra que `_month` já documentava: nunca duas noções de tempo diferentes
para dia e mês no mesmo registro.
"""
from datetime import datetime, timezone
import time

from . import db

SECTION = "aiUsage"
GLOBAL_SECTION = "aiUsageGlobal"   # qa/42: contador GLOBAL (kv sem escopo de usuário)
# C-33 (fase 5): acumulado MENSAL, registro PRÓPRIO — escopado por user_id
# como SECTION, mas NUNCA misturado ao dict diário. `_load` devolve um dict
# novo (zerado) toda vez que o dia vira; se o mês vivesse dentro desse mesmo
# dict, a virada de DIA apagaria o acumulado do MÊS junto (é a classe exata
# de bug que `test_fase5_gate_mensal.py` trava no teste de rollover).
MONTH_SECTION = "aiUsageMonth"


def _today(_dia=None) -> str:
    """`_dia` (ADR-027): dia PRONTO, no formato `%Y-%m-%d`, calculado pelo
    chamador no fuso dele. `None` = comportamento histórico (UTC)."""
    if _dia:
        return str(_dia)
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _month(_mes=None) -> str:
    # Mesma âncora de fuso/relógio que `_today()` (datetime.now(timezone.utc))
    # — nunca duas noções de tempo diferentes para dia e mês. Com override, a
    # regra continua: quem passa `_mes` tem de passar `_dia` do mesmo fuso.
    if _mes:
        return str(_mes)
    return datetime.now(timezone.utc).strftime("%Y-%m")


# Os dois helpers abaixo existem por causa de um contrato de TESTE que não
# pode quebrar: `test_fase5_gate_mensal` monkeypatcha `_today`/`_month` por
# lambdas de ZERO argumentos (`lambda: "2099-01"`). Chamar `_today(_dia)`
# direto no corpo do módulo faria esse guardião estourar `TypeError` em vez
# de guardar a virada de mês. Então o corpo resolve o override ANTES e só
# chama a função sem argumento quando não há override — o parâmetro segue
# na assinatura para quem quiser usar `_today("2026-09-09")` diretamente.
def _resolve_dia(_dia=None) -> str:
    return str(_dia) if _dia else _today()


def _resolve_mes(_mes=None) -> str:
    return str(_mes) if _mes else _month()


def _load_global(conn, section: str = GLOBAL_SECTION, _dia=None) -> dict:
    hoje = _resolve_dia(_dia)
    g = db.kv_get(conn, section, None, user_id=None)
    if not isinstance(g, dict) or g.get("day") != hoje:
        return {"day": hoje, "count": 0}
    if not isinstance(g.get("count"), int):
        g["count"] = 0
    return g


def global_snapshot(conn, cap=None, section: str = GLOBAL_SECTION, _dia=None) -> dict:
    """qa/42 (FinOps): quanto a IA gerenciada gastou HOJE somando todos os
    usuários. Antes não existia contador agregado — a cota era só por usuário,
    então o gasto do servidor era (nº de usuários) × cota, SEM teto superior."""
    g = _load_global(conn, section=section, _dia=_dia)
    used = int(g.get("count", 0))
    return {"day": g["day"], "used": used, "cap": cap,
            "remaining": None if cap is None else max(0, cap - used)}


def _load(conn, user_id, section: str = SECTION, _dia=None) -> dict:
    hoje = _resolve_dia(_dia)
    u = db.kv_get(conn, section, None, user_id=user_id)
    if not isinstance(u, dict) or u.get("day") != hoje:
        return {"day": hoje, "count": 0, "rl": []}
    if not isinstance(u.get("rl"), list):
        u["rl"] = []
    if not isinstance(u.get("count"), int):
        u["count"] = 0
    return u


def _save(conn, user_id, u, section: str = SECTION) -> None:
    db.kv_set(conn, section, u, user_id=user_id)


def _load_month(conn, user_id, section: str = MONTH_SECTION, _mes=None) -> dict:
    """Mesmo padrão defensivo de `_load_global`: registro de outro mês (ou
    corrompido/tipo errado) devolve um dict zerado do mês corrente — nunca
    lança, nunca herda contagem de um mês que já virou."""
    mes = _resolve_mes(_mes)
    m = db.kv_get(conn, section, None, user_id=user_id)
    if not isinstance(m, dict) or m.get("month") != mes:
        return {"month": mes, "count": 0}
    if not isinstance(m.get("count"), int):
        m["count"] = 0
    return m


def month_used(conn, user_id, section: str = MONTH_SECTION, _mes=None) -> int:
    """C-33 (fase 5): contagem REAL de análises do mês corrente da conta —
    fonte única para `plan.can_analyze(used_this_month=...)`. Nunca um
    segundo contador paralelo: o acumulado só é incrementado por `consume()`
    logo abaixo."""
    return int(_load_month(conn, user_id, section=section, _mes=_mes).get("count", 0))


def used(conn, user_id, *, section: str = SECTION, _dia=None) -> int:
    """ADR-027: espelho DIÁRIO de `month_used` — quantas chamadas a conta já
    gastou HOJE na seção pedida. Existe para a rota mostrar `usado`/`limite`
    ao usuário sem reimplementar a lógica de virada de dia (que é justamente
    onde o `_dia` de São Paulo entra)."""
    return int(_load(conn, user_id, section=section, _dia=_dia).get("count", 0))


# qa/47: `section`/`global_section` permitem reusar este módulo para OUTRO
# domínio de cota (ex. ingest de analytics) sem misturar o balde de contagem
# com o da IA gerenciada — cada chamador usa sua própria chave de kv. Default
# preserva o comportamento anterior (todos os call sites de IA continuam
# implícitos em SECTION/GLOBAL_SECTION).
def check(conn, user_id, *, quota, rate_per_min, custo=1, cap_global=None, _now=None,
          section: str = SECTION, global_section: str = GLOBAL_SECTION, _dia=None):
    """(permitido, motivo). Registra o uso para o rate limit; NÃO consome a cota
    diária (isso é no consume, após sucesso).

    qa/42 (FinOps): `custo` = quantas análises ESTE request pode disparar.
    O /api/scan/deep chamava check 1x e consume até 10x (1 por ticker do
    top-N) — quem tinha 19/20 passava no check e terminava em 29. Reservar o
    custo na COTA fecha o furo. O rate limit segue contando 1 por REQUEST
    (ele existe para impedir martelar): reservar 10 slots num teto de 6/min
    bloquearia todo deep."""
    u = _load(conn, user_id, section=section, _dia=_dia)
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
    if cap_global is not None and _load_global(conn, section=global_section, _dia=_dia)["count"] + custo > cap_global:
        _save(conn, user_id, u, section=section)
        return (False, (
            "A IA do app atingiu o limite de uso de hoje (teto global do servidor). "
            "Use sua própria chave (BYOK) em Perfil → Conta & preferências para "
            "análises ilimitadas, ou volte amanhã."
        ))
    u["rl"].append(now)
    _save(conn, user_id, u, section=section)
    return (True, None)


def consume(conn, user_id, *, custo: int = 1, section: str = SECTION, global_section: str = GLOBAL_SECTION,
            month_section: str = MONTH_SECTION, _dia=None, _mes=None) -> int:
    """Conta análise(s) gerenciada(s) (chamar após o LLM responder com sucesso,
    ou — qa/47 — após um lote de eventos de analytics ser aceito).
    qa/42: conta no contador do usuário E no global (teto de gasto do servidor).
    qa/47: `custo` permite contar um LOTE inteiro numa chamada (em vez de
    laçar `consume()` N vezes) — default 1 preserva o comportamento anterior.
    C-33 (fase 5): também incrementa o acumulado MENSAL (registro próprio,
    ver `MONTH_SECTION`) — é o único ponto de escrita do ledger mensal."""
    custo = max(1, int(custo or 1))
    u = _load(conn, user_id, section=section, _dia=_dia)
    u["count"] = int(u.get("count", 0)) + custo
    _save(conn, user_id, u, section=section)
    g = _load_global(conn, section=global_section, _dia=_dia)
    g["count"] = int(g.get("count", 0)) + custo
    db.kv_set(conn, global_section, g, user_id=None)
    m = _load_month(conn, user_id, section=month_section, _mes=_mes)
    m["count"] = int(m.get("count", 0)) + custo
    db.kv_set(conn, month_section, m, user_id=user_id)
    return u["count"]


def snapshot(conn, user_id, quota, section: str = SECTION) -> dict:
    u = _load(conn, user_id, section=section)
    used = int(u.get("count", 0))
    remaining = None if quota is None else max(0, quota - used)
    m = _load_month(conn, user_id)
    return {"day": u["day"], "used": used, "quota": quota, "remaining": remaining,
            "month": m["month"], "monthUsed": int(m.get("count", 0))}


# ---------------------------------------------------------------------------
# FIX-C38 (fase 5) — alerta PREVENTIVO de gasto de IA, complementar ao hard
# stop de `check()`/`cap_global` acima (esse já bloqueia; isto avisa ANTES).
# ---------------------------------------------------------------------------
ALERTA_JANELA_PADRAO = 7  # dias — usada quando o admin não configurou janela própria


def alerta_gasto(usado_hoje, serie, limiar_pct, janela_dias, hoje=None) -> dict:
    """Função PURA (sem I/O, sem `conn`) — testável offline, como o
    docstring do módulo promete. Compara o gasto de HOJE contra a média dos
    dias PASSADOS da janela e devolve o desvio percentual.

    Escolha de grandeza: compara a MESMA que o hard stop limita — análises
    gerenciadas do dia (`ia_analises_gerenciadas_dia`, gravada 1x/dia a
    partir de `global_snapshot()["used"]`), não tokens. Tokens/dia seguem
    como sparkline separado na aba Custos do portal admin.

    Regra de produto inegociável (CLAUDE.md item 4 — nunca inventar/estimar
    na ausência de dado): `configurado` distingue "sem limiar admin" de
    "avaliável"; `avaliavel` distingue "consegui calcular" de "não consegui
    (histórico insuficiente ou média zero)". `acima` só tem significado
    quando `avaliavel is True` — quem renderiza NUNCA pode ler `acima is
    False` como "dentro do normal" sem checar `avaliavel` primeiro, porque
    aqui `acima` pode ser `False` só porque não há base pra avaliar, não
    porque o gasto está de fato normal.
    """
    hoje = hoje or _today()
    base = {
        "configurado": False, "avaliavel": False, "motivo": None,
        "hoje": usado_hoje, "media": None, "desvioPct": None,
        "limiarPct": None, "janelaDias": None, "acima": False,
    }
    try:
        limiar = float(limiar_pct) if limiar_pct not in (None, "") else None
    except (TypeError, ValueError):
        limiar = None
    if limiar is None or limiar <= 0:
        return base  # sem limiar configurado (ou inválido) => nada a avaliar

    try:
        janela = int(janela_dias) if janela_dias else ALERTA_JANELA_PADRAO
    except (TypeError, ValueError):
        janela = ALERTA_JANELA_PADRAO
    if janela <= 0:
        janela = ALERTA_JANELA_PADRAO

    base["configurado"] = True
    base["limiarPct"] = limiar
    base["janelaDias"] = janela

    # o dia de HOJE, se estiver na série, é EXCLUÍDO — senão o gasto de hoje
    # se compararia consigo mesmo (média enviesada pro próprio valor testado)
    passados = sorted(
        (p for p in (serie or []) if p.get("day") != hoje),
        key=lambda p: p["day"],
    )[-janela:]
    if len(passados) < 3:
        base["motivo"] = "Histórico insuficiente (menos de 3 dias anteriores) para calcular a média."
        return base

    media_bruta = sum(float(p.get("value") or 0) for p in passados) / len(passados)
    if media_bruta == 0:
        base["motivo"] = "Média dos dias anteriores é zero — não dá para calcular desvio percentual."
        return base

    media = round(media_bruta, 2)
    desvio = round((usado_hoje / media - 1) * 100, 1)
    base["avaliavel"] = True
    base["media"] = media
    base["desvioPct"] = desvio
    base["acima"] = desvio >= limiar
    return base
