"""FASE 3 — Agente autônomo SERVER-SIDE.

O ciclo que rodava só com o app aberto (setInterval no App.jsx chamando
/api/cycle) agora TAMBÉM roda no servidor, por usuário logado com o agente
habilitado — o app pode estar fechado. A lógica do /api/cycle foi PORTADA
para cá (run_cycle_for) e o endpoint passou a reusá-la: uma implementação só.

Parâmetros por usuário (seção `agent`, decisão 3.2):
  serverEnabled  bool   — liga o modo servidor (exige conta; anônimo segue foreground)
  mode           str    — "executar" (vende no stop/alvo) | "sinalizar" (só registra/avisa)
  rules          dict   — {stop: bool, alvo: bool, trailing: bool}
  trailingMode   str    — "percentual" (default) | "atr" | "estrutura"   [F2]
  trailingPct    float  — distância do trailing PERCENTUAL (default 5%)
  trailingAtrMult float — múltiplo do ATR(14) no modo "atr" (default 2,0) [F2]
  trailingLookback int  — nº de candles da mínima no modo "estrutura" (default 5) [F2]
  alvoDinamico   bool   — estende o alvo por ATR em vez de fechar, opt-in (default False) [F3]
  maxOpsDia      int    — teto de operações executadas por dia (default 3)
  maxValorOp     float  — teto de valor por operação (0 = sem teto)

Guardrails: opera SOMENTE a carteira simulada; textos descritivos, nunca
imperativos; kill-switch global (env B3_AGENT_KILL=1) e por usuário
(serverEnabled=false). Fora do pregão (~10h–18h BRT, seg–sex) não roda.
"""
import asyncio
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from . import db, skill_ref, store

INTERVAL_S_DEFAULT = 300
BRT = timezone(timedelta(hours=-3))

# ESPELHO DELIBERADO de `web/src/notify.js:382`: o app valida o ticker do
# payload contra este MESMO formato e DESCARTA EM SILÊNCIO o que não casar.
# Mandar `t` fora do formato (contrato de opção, por ex.) é peso morto no
# payload e ruído no diagnóstico — filtramos na origem.
_TICKER_PUSH_RE = re.compile(r"^[A-Z]{4}\d{1,2}$")

# BLOCO D3 — visibilidade: o scheduler grava aqui o resultado da última
# passada; GET /api/agent/status expõe (fim do "não sei por que não roda").
LAST_RUN = {"at": None, "usuarios": 0, "executadas": 0, "erro": None}

# Fase 2 (MERC-02, plano 02-03): mesmo padrão de LAST_RUN, mas para a
# execução de ordens pendentes — que varre `store.scopes_com_pendentes` (ver
# comentário completo no bloco novo dentro de `scheduler_loop`), então
# precisa do próprio contador (um usuário pode aparecer aqui sem nunca ter
# ligado o Operador).
LAST_PENDING = {"at": None, "escopos": 0, "executadas": 0, "canceladas": 0, "erro": None}

# FASE 3 (Operador): observabilidade de verdade — anel com as últimas passadas
# (duração, usuários, execuções, erros) + próxima passada + guard de
# sobreposição de ciclo por usuário (um run-now não colide com o scheduler).
RUN_HISTORY: list = []           # [{at, duracaoS, usuarios, executadas, erros:[..]}]
RUN_HISTORY_MAX = 12
NEXT_RUN_AT = {"ts": None}       # epoch da próxima passada do scheduler
_CYCLE_BUSY: set = set()          # escopos com ciclo em andamento
# Intervalo do ciclo POR USUÁRIO (agent.intervalMin, min): o laço acorda na
# cadência base (env B3_AGENT_INTERVAL_S) e só roda o ciclo de um usuário se já
# passou o intervalo DELE desde a última passada — assim cada conta escolhe a
# frequência (default 15 min). A granularidade mínima é a cadência base.
LAST_USER_RUN: dict = {}          # {uid: epoch da última passada efetiva}
# ADR-001 (item 7): quando a última passada INTRADAY global rodou (monotonic).
# Global e não por usuário — a passada é uma só para todo mundo.
_LAST_INTRADAY: dict = {"ts": None}

# qa/46 (Fase 2, item "push automático falho"): antes disto a falha de push
# de uma ação EXECUTADA pelo agente era `except: pass` silencioso — ninguém
# sabia que uma ordem rodou e o aviso não chegou. Contador reseta por dia
# (mesmo padrão de fundamentals.LAST_WARM), incrementado só na falha real.
PUSH_FAIL_TODAY: dict = {"date": None, "falhas": 0}


def _registrar_push_falho() -> None:
    hoje = _today()
    if PUSH_FAIL_TODAY["date"] != hoje:
        PUSH_FAIL_TODAY["date"] = hoje
        PUSH_FAIL_TODAY["falhas"] = 0
    PUSH_FAIL_TODAY["falhas"] += 1


# ADR-012 (Fase 4): campos hoje só em memória, capturados 1x/dia pro portal
# admin ganhar tendência (Visão Geral/Custos). Gate persistido — mesmo
# motivo de qa/42 pra analysis_outcomes: memória zera no deploy, sem gate
# persistido um dia com vários deploys gravaria o snapshot várias vezes
# (idempotente aqui, mas ainda assim redundante).
LAST_METRICAS_DIARIAS: dict = {"date": None}


def _coletar_metricas_diarias(conn) -> dict:
    """Cada valor é o que os módulos em memória diziam NO MOMENTO em que o
    job rodou — ver docstring de analytics.registrar_metricas_diarias sobre
    a diferença pra rollup de eventos. Import local: sem ciclo de import."""
    from . import candle_cache, candle_provider, managed, metering, llm, radar_daily

    usage = llm.usage_snapshot()
    tokens_dia = sum(
        (m.get("inputTokens", 0) or 0) + (m.get("outputTokens", 0) or 0)
        for m in (usage.get("porModelo") or {}).values()
    )
    ger = metering.global_snapshot(conn, managed.global_daily_cap())
    cp = candle_provider.snapshot()

    return {
        "custo_ia_tokens_dia": tokens_dia,
        "ia_analises_gerenciadas_dia": ger.get("used", 0),
        # candle_provider.snapshot() é janela de 3 dias (_JANELA_DIAS), não
        # só hoje — nome da métrica deixa isso explícito, não esconde.
        "brapi_requisicoes_janela3d": cp.get("requisicoes", 0),
        "brapi_erros_janela3d": cp.get("erros", 0),
        "cache_candles_series": len(candle_cache.stats() or {}),
        "push_automatico_falhas_dia": PUSH_FAIL_TODAY.get("falhas", 0),
        "radar_diario_duracao_s": radar_daily.LAST_DAILY.get("duracaoS"),
    }


def _maybe_registrar_metricas_diarias(conn, analytics_conn) -> None:
    hoje = _today()
    if LAST_METRICAS_DIARIAS["date"] == hoje:
        return
    from . import analytics as analytics_mod  # import local: sem ciclo de import
    analytics_mod.registrar_metricas_diarias(analytics_conn, hoje, _coletar_metricas_diarias(conn))
    LAST_METRICAS_DIARIAS["date"] = hoje


def _push_run_history(entry: dict):
    RUN_HISTORY.append(entry)
    del RUN_HISTORY[:-RUN_HISTORY_MAX]


def _today() -> str:
    return datetime.now(BRT).strftime("%Y-%m-%d")


def _now_str() -> str:
    return datetime.now(BRT).strftime("%d/%m %H:%M")


# ADR-013 (Decisão "Rotas NOVAS propostas", grupo "Execução de ordens
# automáticas"): o kill-switch ganha um toggle em runtime (admin_config),
# além do env — mesmo padrão memória→DB→env que brapi_budget.py já usa,
# generalizado aqui em vez de inventado de novo. Nenhum call site muda de
# assinatura (kill_switch_on() continua sem args) — só passa a checar mais
# uma fonte, na ordem memória → DB → env, antes de cair no default (off).
_DB_CONN = None
_DB_ENABLED = False
_KILL_MEM = None       # None = sem override explícito ainda; True/False = override achado (DB ou set_kill_switch)
_KILL_DB_CHECKED = False  # já confirmamos que o DB NÃO tem override neste processo? evita reconsultar a cada chamada


def configure_db(conn) -> None:
    global _DB_CONN, _DB_ENABLED
    _DB_CONN = conn
    _DB_ENABLED = True


def reset_kill_switch_cache() -> None:
    """Só para testes — mesmo padrão de `brapi_budget.reset()`: a memória
    NÃO é limpa por `configure_db` de propósito (produção nunca deveria
    perder o cache num reconnect); testes que trocam de banco entre casos
    chamam isto explicitamente para não vazar estado de um teste pro outro."""
    global _KILL_MEM, _KILL_DB_CHECKED
    _KILL_MEM = None
    _KILL_DB_CHECKED = False


def set_kill_switch(on: bool, actor: str = None) -> bool:
    """Chamado pela rota admin (`PUT /api/admin/agent/kill-switch`). Persiste
    e atualiza a memória imediatamente — sem esperar o próximo boot. `actor`
    é o user_id de quem mudou (achado de revisão: ficava sempre None, sem
    correspondência com quem `admin_audit_log` já registrava corretamente).
    A escrita no banco é best-effort (try/except): falhar aqui não pode
    impedir o kill-switch de valer NA MEMÓRIA — é o controle de emergência,
    tem que responder mesmo com o SQLite indisponível."""
    global _KILL_MEM
    _KILL_MEM = bool(on)
    if _DB_ENABLED:
        try:
            from . import db
            db.admin_config_set(_DB_CONN, "agentKillSwitch", bool(on), updated_by=actor)
        except Exception:  # noqa: BLE001 — mesmo padrão de brapi_budget.set_spot_intervalo
            pass
    return _KILL_MEM


def kill_switch_on() -> bool:
    """Memória → DB (best-effort, só até confirmar se existe override) →
    env (SEMPRE lido ao vivo) → default (desligado).

    Achados de revisão corrigidos aqui: (a) a leitura do DB não tinha
    try/except — uma falha do SQLite propagava pro `scheduler_loop` e podia
    pular o ciclo INTEIRO (todas as checagens de stop/alvo) por causa só
    desta checagem; (b) quando ninguém nunca mexeu no toggle (override
    ausente, o caso mais comum), a função batia no SQLite em TODO tick do
    scheduler — `_KILL_DB_CHECKED` faz essa consulta correr NO MÁXIMO uma
    vez por processo quando não há override.

    IMPORTANTE: ao contrário do intervalo da brapi, o resultado do ENV
    nunca é cacheado em `_KILL_MEM` — só um override explícito (do DB ou de
    `set_kill_switch`) é. `B3_AGENT_KILL` continua sendo lido AO VIVO em
    toda chamada sem override (guardião: test_agent.py::
    test_kill_switch_e_janela_de_pregao muda a env em runtime e espera
    efeito imediato)."""
    global _KILL_MEM, _KILL_DB_CHECKED
    if _KILL_MEM is not None:
        return _KILL_MEM
    if _DB_ENABLED and not _KILL_DB_CHECKED:
        try:
            from . import db
            override = db.admin_config_get(_DB_CONN, "agentKillSwitch")
            if isinstance(override, bool):
                _KILL_MEM = override
                return _KILL_MEM
        except Exception:  # noqa: BLE001
            pass
        _KILL_DB_CHECKED = True
    return (os.environ.get("B3_AGENT_KILL") or "").strip() in ("1", "true", "TRUE", "yes")


def kill_switch_ligado_desde(conn) -> Optional[str]:
    """`at` (ISO) da última transição do kill-switch para LIGADO, best-effort
    a partir do `admin_audit_log` — ou `None` quando não há como saber.

    C-37 / D-04 (03-CONTEXT.md): a ativação via rota admin
    (`PUT /api/admin/agent/kill-switch`) grava auditoria
    (`entity="agent_kill_switch", field="on"`); a ativação por
    `B3_AGENT_KILL` no ambiente é lida AO VIVO por `kill_switch_on()` e NÃO
    passa por `set_kill_switch`/`audit.record` — não deixa rastro nenhum.

    `None` significa "não rastreável" (kill-switch desligado, OU ligado mas
    sem registro de auditoria correspondente) — NUNCA "zero horas". Quem
    chama esta função nunca deve inventar uma duração quando ela devolve
    `None` (princípio 4 do CLAUDE.md).
    """
    try:
        if not kill_switch_on():
            return None
        reg = db.audit_last(conn, "agent_kill_switch", "on")
        if not reg or not reg.get("newValue"):
            return None
        return reg.get("at")
    except Exception:  # noqa: BLE001 — best-effort, nunca propaga
        return None


# C-37 (REPORT-01): o sinal do kill-switch era 100% passivo — o heartbeat
# continuava verde, mascarando "vivo, mas parado" como "vivo, normal" e foi
# isso que deixou a execução automática de TODA a base parada por 2,5 dias
# sem que ninguém notasse. `_ALERTA_KILL_LIMIAR_H` é só o limiar de TOM
# (negativo) usado pela UI/push, não um gate de disparo — o alerta dispara
# desde a 1ª passada dentro do pregão com o kill-switch ligado.
_ALERTA_KILL_LIMIAR_H = 4
_ALERTA_KILL_REPETE_S = 4 * 3600


async def _alertar_kill_switch(conn, client=None) -> int:
    """Hook do `scheduler_loop` (C-37): enquanto o kill-switch do agente
    estiver ligado DENTRO do pregão, avisa ATIVAMENTE quem tem papel
    administrativo — em vez de depender de alguém abrir o portal e notar o
    KPI vermelho (D-04: "o admin também é um usuário, pode usar o push").

    Dedupe persistido em kv (`agentKillSwitchAlerta`) — sobrevive a
    redeploy: no máximo 1 push por episódio a cada `_ALERTA_KILL_REPETE_S`.
    "Episódio" muda quando `desde` muda (reset do kill-switch limpa o
    estado). Nunca consulta `push.prefs_for`: isto NÃO é uma classe de
    aviso de mercado opt-in do usuário final, é aviso operacional para quem
    tem papel administrativo — se o admin não tiver aparelho registrado,
    `send_to_user` devolve `sent=0` sem levantar.

    260824-kc2: a exceção vale TAMBÉM para as três classes novas
    (`radar`/`execucao`/`protecao`). A audiência aqui é por RBAC
    (`db.user_ids_with_roles`), não a conta de mercado do usuário final —
    preferência de aviso de carteira não pode silenciar aviso operacional de
    admin. Foi o kill-switch ligado sem querer que parou a execução de toda a
    base por 2,5 dias; o alerta que denuncia isso não tem interruptor.
    """
    from . import push, rbac  # imports locais: sem ciclo de import

    if not kill_switch_on():
        try:
            db.kv_set(conn, "agentKillSwitchAlerta", {}, user_id=None)
        except Exception:  # noqa: BLE001 — reset é best-effort
            pass
        return 0
    if not in_market_hours():
        return 0

    estado = db.kv_get(conn, "agentKillSwitchAlerta", {}, user_id=None) or {}
    desde = kill_switch_ligado_desde(conn)
    ultimo_aviso_ts = estado.get("ultimoAvisoTs")
    if (estado.get("desde") == desde and isinstance(ultimo_aviso_ts, (int, float))
            and (time.time() - ultimo_aviso_ts) < _ALERTA_KILL_REPETE_S):
        return 0

    horas = None
    if desde is not None:
        try:
            agora = datetime.now(timezone.utc)
            momento = datetime.fromisoformat(desde)
            if momento.tzinfo is None:
                momento = momento.replace(tzinfo=timezone.utc)
            horas = int((agora - momento).total_seconds() // 3600)
        except Exception:  # noqa: BLE001 — parse ruim não pode derrubar o alerta
            horas = None

    if horas is not None:
        titulo = f"Kill-switch ligado há {horas}h em horário de pregão"
        desde_brt = "?"
        try:
            momento = datetime.fromisoformat(desde)
            if momento.tzinfo is None:
                momento = momento.replace(tzinfo=timezone.utc)
            desde_brt = momento.astimezone(BRT).strftime("%d/%m %H:%M")
        except Exception:  # noqa: BLE001
            pass
        corpo = (f"A execução automática do Operador está parada desde {desde_brt}. "
                 "Verifique no portal admin (aba Automação) se isso é intencional.")
    else:
        titulo = "Kill-switch do Operador ligado em horário de pregão"
        corpo = ("O kill-switch do Operador está ligado, mas o horário exato não pôde ser "
                 "determinado (ativado por variável de ambiente, sem registro de auditoria). "
                 "Verifique no portal admin.")

    enviados = 0
    try:
        import httpx

        destinatarios = db.user_ids_with_roles(
            conn, [rbac.ROLE_ADMIN] + [g for g in rbac.GRUPOS if "execucao_automatica.ver" in rbac.GRUPOS[g]]
        )

        async def _fan_out(cli):
            nonlocal enviados
            for uid in destinatarios:
                try:
                    r = await push.send_to_user(conn, uid, titulo, corpo, som=True, prioridade="10",
                                                client=cli, extra={"kind": "admin_kill_switch"})
                    if r.get("sent"):
                        enviados += 1
                except Exception as e:  # noqa: BLE001 — cada envio é best-effort, isolado
                    print(f"[kill-switch-alerta] envio para {uid[:8]}… falhou: {e}")

        if client is not None:
            await _fan_out(client)
        else:
            async with httpx.AsyncClient(http2=True, timeout=10) as cliente:
                await _fan_out(cliente)
    except Exception as e:  # noqa: BLE001 — o hook inteiro nunca derruba o laço
        print(f"[kill-switch-alerta] {e}")

    try:
        db.kv_set(conn, "agentKillSwitchAlerta", {"desde": desde, "ultimoAvisoTs": time.time()}, user_id=None)
    except Exception:  # noqa: BLE001 — dedupe é best-effort
        pass
    return enviados


def in_market_hours(now: datetime = None) -> bool:
    """A bolsa está negociando agora. Delega para `pregao.py`, que é a fonte
    única — por aqui passam também intraday, timing e timing_watch.

    Era `seg–sex, 10 <= hora < 18` ("janela aproximada", dizia o docstring):
    tratava como pregão o call de fechamento, a zona morta até 17:30 e TODOS os
    feriados da B3. Cada uma dessas janelas custava passada intraday (65 ativos)
    e consulta de cotação por usuário, sem dado novo para buscar.
    """
    from . import pregao  # import local: sem ciclo (pregao não importa agent)
    return pregao.in_market_hours(now)


# ---------------------------------------------------------------------------
# F2 — Trailing dinâmico (segue estrutura/volatilidade, não um % fixo)
#
# O trailing percentual continua sendo o DEFAULT: quem já tem `trailingPct`
# configurado não muda de comportamento por causa desta entrega. Os modos
# técnicos são opt-in explícito.
#
# A INVARIANTE é a mesma dos três modos e não é negociável: o stop só SOBE.
# `nivel_trailing` calcula o nível bruto; quem aplica compara com o stop atual
# e só grava se for maior. O guardião `test_trailing_sobe_o_stop_e_nunca_desce`
# cobre o modo percentual; `test_trailing_dinamico_nunca_afrouxa` cobre os outros.
# ---------------------------------------------------------------------------
TRAILING_MODES = ("percentual", "atr", "estrutura")
ATR_MULT_DEFAULT, ATR_MULT_MIN, ATR_MULT_MAX = 2.0, 1.0, 4.0
LOOKBACK_DEFAULT, LOOKBACK_MIN, LOOKBACK_MAX = 5, 2, 20


def contexto_trailing(snap: dict) -> dict:
    """Extrai do STU só o que o trailing precisa — ATR(14) e as velas.

    Isola a regra da FORMA do snapshot: `nivel_trailing` fica pura e testável
    com um dict de duas chaves, sem montar um STU inteiro no teste.
    """
    ind = (snap or {}).get("indicators") or {}
    atr = None
    for v in reversed(ind.get("atr14") or []):
        if isinstance(v, (int, float)):
            atr = float(v)
            break
    return {"atr": atr, "candles": (snap or {}).get("candles") or []}


def _minima_recente(candles: list, n: int):
    """Menor mínima das últimas `n` velas — o nível que invalida a tese de alta
    (Princípio 6 da skill: sempre declarar o ponto de invalidação)."""
    lows = [c.get("low") for c in (candles or [])[-n:] if isinstance(c.get("low"), (int, float))]
    return min(lows) if lows else None


def nivel_trailing(mode: str, price: float, par: dict, ctx: dict = None):
    """Nível BRUTO do trailing, ANTES da monotonicidade. PURO.

    Devolve (nivel|None, descricao). A descrição vai para o Diário — o app
    ensina o mecanismo, então ela nomeia o critério e o número que o gerou.

    Sem o insumo técnico (ATR ou velas ausentes), cai para o percentual e DIZ
    que caiu. Silêncio aqui deixaria a posição protegida por uma regra que o
    usuário não escolheu, sem nada no Diário denunciando a troca.
    """
    ctx = ctx or {}
    pct = par.get("trailingPct") or 5.0

    def _percentual(sufixo: str = ""):
        return round(price * (1 - pct / 100.0), 2), f"{pct:.0f}% abaixo do preço{sufixo}"

    if mode == "atr":
        atr = ctx.get("atr")
        if not atr or atr <= 0:
            return _percentual(" (sem ATR disponível — critério técnico indisponível)")
        k = par.get("trailingAtrMult") or ATR_MULT_DEFAULT
        return round(price - k * atr, 2), f"{k:.1f}× o ATR(14) de R$ {atr:.2f} abaixo do preço"

    if mode == "estrutura":
        n = int(par.get("trailingLookback") or LOOKBACK_DEFAULT)
        minima = _minima_recente(ctx.get("candles"), n)
        if minima is None:
            return _percentual(" (sem candles disponíveis — critério técnico indisponível)")
        return round(minima, 2), f"na mínima das últimas {n} velas (R$ {minima:.2f})"

    return _percentual()


# ---------------------------------------------------------------------------
# F3 — Alvo dinâmico. Quando o preço já bateu o alvo com força (extensão de
# ATR clara), estende em vez de fechar — decisão do Alex (2026-08-03): o
# critério é ATR (reusa o mesmo ATR(14) do trailing técnico), opt-in via
# `agent.alvoDinamico` (quem não ligou continua fechando no alvo, como sempre).
#
# O que trava a corrida atrás do preço: MAX_ALVO_EXTENSOES por posição é o
# freio de verdade (não configurável — v1 simples, decisão do Alex). O R:R
# recalculado (Princípio 5, mínimo 1,5:1) é a segunda trava — garante que uma
# extensão nunca é aplicada sobre uma geometria degenerada (ex.: stop já
# quase colado no preço). Nenhuma das duas muda o stop; quem sobe o stop é o
# trailing (F2), sempre monotônico.
# ---------------------------------------------------------------------------
MAX_ALVO_EXTENSOES = 2
ALVO_ATR_MULT = 1.5      # multiplicador de ATR do alvo dinâmico — NÃO é o R:R mínimo, não consolidar com RR_MINIMO
RR_MINIMO = skill_ref.RR_MIN  # ADR15-05: fonte única em skill_ref (era literal 1.5 solto)


def _rr(avg, stop, alvo):
    """R:R do plano (Princípio 5 da skill). None se a geometria não fecha."""
    if avg is None or stop is None or alvo is None:
        return None
    risco = avg - stop
    if risco <= 0:
        return None
    return (alvo - avg) / risco


def avaliar_alvo_dinamico(price: float, pos: dict, ctx: dict = None):
    """F3, PURA: se o preço já bateu o alvo e ainda sobra ATR/R:R, devolve
    (novo_alvo, descricao) para ESTENDER em vez de fechar a posição. Devolve
    (None, None) quando não há extensão a fazer — nesse caso o chamador segue
    o fechamento normal de stop/alvo."""
    alvo, stop, avg = pos.get("alvo"), pos.get("stop"), pos.get("avg")
    if alvo is None or price < alvo:
        return None, None
    usadas = int(pos.get("alvoExtensoes") or 0)
    if usadas >= MAX_ALVO_EXTENSOES:
        return None, None
    atr = (ctx or {}).get("atr")
    if not atr or atr <= 0:
        return None, None
    novo_alvo = round(alvo + ALVO_ATR_MULT * atr, 2)
    rr = _rr(avg, stop, novo_alvo)
    if rr is None or rr < RR_MINIMO:
        return None, None
    return novo_alvo, (f"extensão {usadas + 1}/{MAX_ALVO_EXTENSOES}: alvo levado a R$ {novo_alvo:.2f} "
                        f"({ALVO_ATR_MULT:.1f}× o ATR(14) de R$ {atr:.2f} além do alvo batido; R:R {rr:.1f}:1)")


# ---------------------------------------------------------------------------
# Opções (v2) — ADR-003 (coleção própria `optionPositions`), ADR-004 (só age
# sobre cotação com providerStatus "ok" — nunca simula execução sobre dado
# degradado) e ADR-005 (fechamento por vencimento, motivo estruturado).
#
# `option_quotes_getter(underlying, expiration) -> payload` é injetado (fake
# nos testes; `options_provider.get_options` em produção — seletor por env,
# Fase 9). 1 fetch por VENCIMENTO aberto, não por contrato — várias posições
# no mesmo ativo/vencimento dividem a mesma chamada.
# ---------------------------------------------------------------------------
def intrinseco_opcao(pos: dict, spot: float) -> float:
    """Valor intrínseco na liquidação por vencimento — pode ser ZERO (perda
    total do prêmio). PURA."""
    strike = pos.get("strike") or 0.0
    if pos.get("optionType") == "put":
        return max(0.0, float(strike) - float(spot))
    return max(0.0, float(spot) - float(strike))


async def _option_quotes(option_quotes_getter, opts: list) -> dict:
    pares = sorted({(p.get("underlying"), p.get("expiration")) for p in opts
                     if p.get("underlying") and p.get("expiration")})
    out = {}
    for underlying, expiration in pares:
        try:
            out[(underlying, expiration)] = await option_quotes_getter(underlying, expiration)
        except Exception:  # noqa: BLE001 — 1 vencimento indisponível não derruba o ciclo
            out[(underlying, expiration)] = None
    return out


async def _avaliar_opcoes(conn, scope, ag, par, option_quotes_getter, executed: int, events: list) -> int:
    """Segunda passada do ciclo: `optionPositions`, separada da de `positions`
    porque a unidade (prêmio, não preço do ativo) e o terceiro motivo de saída
    (vencimento) não têm equivalente em ação. Retorna o `executed` atualizado."""
    opts = store.get(conn, "optionPositions", user_id=scope) or []
    if not opts or option_quotes_getter is None:
        return executed
    quotes = await _option_quotes(option_quotes_getter, opts)
    hoje = _today()
    for pos in list(opts):
        payload = quotes.get((pos.get("underlying"), pos.get("expiration")))
        # ADR-004: sem cotação confiável, nem liquida por vencimento nem avalia
        # stop/alvo neste ciclo — o mesmo tratamento best-effort que ação já tem
        # para "sem cotação"; tenta de novo no próximo ciclo.
        if not payload or payload.get("providerStatus") != "ok":
            continue
        spot = payload.get("underlyingPrice")
        contrato = next((c for c in (payload.get("calls") or []) + (payload.get("puts") or [])
                          if c.get("contractSymbol") == pos.get("id")), None)
        price = contrato.get("lastPrice") if contrato else None
        if pos.get("expiration") and str(pos["expiration"]) <= hoje:
            if not isinstance(spot, (int, float)):
                continue
            intrinseco = intrinseco_opcao(pos, float(spot))
            store.close_option_vencida(conn, pos["id"], intrinseco, user_id=scope)
            executed += 1
            _bump_ops(conn, scope, store.get(conn, "agent", user_id=scope) or ag)
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Vencimento: {pos['id']} ({pos.get('underlying')}) liquidado pelo "
                                   f"intrínseco (R$ {intrinseco:.2f}/ação)."})
            continue
        if price is None:
            continue
        # F2 (trailing técnico): ATR é em R$ do ativo-objeto, unidade incompatível
        # com prêmio — cai sempre no percentual, nomeado no Diário quando o modo
        # configurado era técnico (proposta §3, "o que quebra em agent.py").
        if par["rules"]["trailing"] and pos.get("stop") is not None:
            novo, criterio = nivel_trailing("percentual", price, par, None)
            if par["trailingMode"] != "percentual":
                criterio += " — trailing técnico não se aplica a prêmio de opção, caiu no percentual"
            if novo is not None and novo > pos["stop"]:
                store.set_option_position(conn, pos["id"], stop=novo, has_stop=True, user_id=scope)
                events.append({"time": _now_str(), "kind": "info",
                               "text": f"Trailing: stop de {pos['id']} ajustado para R$ {novo:.2f} ({criterio})."})
                pos = {**pos, "stop": novo}
        breach_stop = par["rules"]["stop"] and pos.get("stop") is not None and price <= pos["stop"]
        hit_alvo = par["rules"]["alvo"] and pos.get("alvo") is not None and price >= pos["alvo"]
        # F3 (alvo dinâmico) não se aplica a opção — mesma unidade quebrada do
        # trailing técnico; opção sempre fecha no alvo, sem extensão.
        if not (breach_stop or hit_alvo):
            continue
        motivo = "stop" if breach_stop else "alvo"
        valor_op = price * (pos.get("qty") or 0)
        if par["mode"] != "executar":
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Sinal do agente: opção {pos['id']} com {motivo} atingido (R$ {price:.2f}). "
                                   f"Modo 'apenas sinalizar' — nenhuma operação feita."})
            continue
        if _ops_today(ag) + executed >= par["maxOpsDia"]:
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Teto diário de operações atingido ({par['maxOpsDia']}). "
                                   f"{pos['id']} com {motivo} atingido ficou registrado, sem execução."})
            continue
        if par["maxValorOp"] > 0 and valor_op > par["maxValorOp"]:
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Teto por operação (R$ {par['maxValorOp']:.2f}) excedido em {pos['id']} "
                                   f"(R$ {valor_op:.2f}). Registrado, sem execução."})
            continue
        store.sell_option(conn, pos["id"], price, user_id=scope, motivo=motivo, origem="automatico")  # ADR-012 (Fase 3)
        executed += 1
        _bump_ops(conn, scope, store.get(conn, "agent", user_id=scope) or ag)
        # `tag` de CONSENTIMENTO (260824-kc2): este evento vira push pelo funil
        # D3 (filtro `kind == "buy"`) e saía SEM tag nenhuma — com o fail-open
        # de `push.classe_do_evento`, ele escaparia do controle e o usuário
        # desligaria "Proteção" continuando a receber proteção de OPÇÃO. O
        # TÍTULO não muda: `skill_ref.push_titulo` devolve o genérico do modo
        # para tag sem frase (skill_ref.py:325-327), que é exatamente o título
        # que este push já tem hoje — não completar `PUSH_TITULOS` por causa
        # desta tag.
        events.append({"time": _now_str(), "kind": "buy", "tag": "protecao-opcao",
                       "text": f"Proteção simulada: opção {pos['id']} ({pos.get('underlying')}) vendida "
                               f"({motivo} atingido) a R$ {price:.2f}."})
    return executed


# ---------------------------------------------------------------------------
# Fase B (plano operador-entrada-e-modos) — entrada automática. Compra 1 lote
# quando o TIMING do dia (não o Radar diário sozinho) confirma que a condição
# de entrada foi atingida AGORA, dentro do % do caixa configurado. D5: só o
# lado COMPRA é executável — `store.py` não tem posição vendida/short, então
# um plano de baixa (`decisaoDiaria == "VENDER"`) nunca vira ordem automática,
# só o aviso/push de sempre.
# ---------------------------------------------------------------------------
# ADR-017 (Decisão 3, 2026-08-20 → Adendo 2, 2026-08-21): a antiga suspensão
# cega (uma flag booleana que bloqueava TODO setup incondicionalmente) sempre
# foi um gate reversível esperando o Bloco 1 (ledger de sinais + seleção
# dinâmica, Fase 7). Com o Bloco 1 em produção desde 2026-08-21, a suspensão
# vira um gate por elegibilidade MEDIDA do setup do gatilho: só executa quem a
# janela anterior fechada mediu como positivo (`elegivel is True`). Hoje isso
# restringe a entrada automática a 5 pares setup×lado (123 de fundo alta,
# IFR2 alta, PFR alta, Setup 9.1 alta, Setup 9.3 alta) — sem lista hardcodada,
# o dado decide e muda sozinho a cada virada de janela (ver Adendo 2 do
# ADR-017).
async def _avaliar_entradas(conn, scope, ag, par, app_mode, positions, executed: int, events: list,
                            agora=None) -> int:
    """Terceira passada do ciclo (depois de saída e de opções): watchlist menos
    quem já está em `positions` (a MESMA lista carregada no topo do ciclo, de
    propósito — reentrar no ticker que talvez tenha acabado de ser vendido
    NESTE ciclo não faz sentido). Só roda em Modo Operador com `entradaAuto`
    ligado (D1, aplicado aqui por defesa em profundidade — `set_agent` já
    impede `entradaAuto=True` de ser salvo fora do Operador). Retorna o
    `executed` atualizado."""
    if not (par["entradaAuto"] and app_mode == "operador"):
        return executed
    # imports locais: mesmo padrão do resto do arquivo — evita ciclo de import
    # (timing_watch → timing → intraday; radar_daily/intraday não dependem de
    # agent; signal_ledger idem, mesmo padrão de `signal_ledger_job` abaixo).
    # Carregados SÓ aqui dentro do guard acima: quem não ligou a feature não
    # paga a leitura extra de kv por ciclo.
    from . import candles as candles_mod, intraday, radar_daily, signal_ledger, timing, timing_watch
    p = candles_mod.normalize_period(None)   # período CANÔNICO do Radar diário
    radar_stored = radar_daily.get_stored(conn, p)
    intra_stored = intraday.get_stored(conn)

    watchlist = store.get(conn, "watchlist", user_id=scope) or []
    em_posicao = {pos["t"] for pos in (positions or [])}
    candidatos = [t for t in watchlist if t not in em_posicao]
    if not candidatos:
        return executed

    # ADR-017 Adendo 2: uma leitura só por chamada, fora do laço — o snapshot
    # não muda entre candidatos do mesmo ciclo, e `historico_snapshot` já tem
    # cache próprio (TTL 300s) e nunca levanta (devolve `{}` em falha de banco,
    # o que faz o gate abaixo fechar para todos os candidatos, nunca abrir).
    hist = signal_ledger.historico_snapshot(conn) or {}

    # `hoje` precisa vir de `agora` quando fornecido (mesmo idioma de
    # timing.py:179) — `_today()` sozinho usa o relógio REAL, e um teste com
    # `agora` fixo no passado gravaria `timingWatch.dia` com a data de hoje
    # de verdade; na leitura seguinte a data não bateria, `_zera_se_virou_o_dia`
    # descartaria o estado de dedup, e o vigia reavisaria um ticker que a
    # entrada automática já comprou neste mesmo ciclo.
    hoje = (agora or datetime.now(BRT)).date().isoformat()
    tw_estado = timing_watch._zera_se_virou_o_dia(
        db.kv_get(conn, "timingWatch", None, user_id=scope) or {"dia": "", "ultimo": {}, "avisados": []}, hoje)
    tw_mudou = False

    for ticker in candidatos:
        r = timing.montar(radar_stored, intra_stored, ticker, "operador", agora=agora)
        if r.get("estado") != "gatilho" or r.get("decisaoDiaria") != "COMPRAR":
            continue  # D5: só COMPRAR executa; VENDER/demais estados seguem só informativos
        nome_setup = r.get("setup")
        if not nome_setup:
            continue  # sem setup identificado, não há o que qualificar — bloqueia
        # ADR-017 Adendo 2: só `elegivel is True` passa. `is not True` cobre no
        # MESMO predicado os três casos negativos (False medido, None por
        # amostra insuficiente/nunca medido, e chave ausente do snapshot) —
        # bloqueio SILENCIOSO (sem events.append, sem log), porque isto não é
        # erro, é o gate funcionando (08-CONTEXT.md, "Religamento do Operador").
        if (hist.get(nome_setup) or {}).get("elegivel") is not True:
            continue
        price = r.get("fechamento15m")
        if not isinstance(price, (int, float)) or price <= 0:
            continue
        cash = store.get(conn, "cash", user_id=scope) or 0.0
        orcamento = cash * (par["allocPct"] / 100.0)
        # Arredonda SEMPRE para BAIXO — lotes de 100. `store.buy` sozinho
        # arredondaria para CIMA (max(100, round(qty/100)*100)) e estouraria o
        # % prometido; a decisão de não executar precisa ser tomada AQUI, antes
        # de chamar store.buy.
        qty = int(orcamento // price // 100) * 100
        if qty < 100:
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Entrada automática: orçamento de {par['allocPct']:.0f}% do caixa "
                                   f"(R$ {orcamento:.2f}) não cobre 1 lote de {ticker} a R$ {price:.2f} — "
                                   f"sem execução, aviso mantido."})
            continue
        if _ops_today(ag) + executed >= par["maxOpsDia"]:
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Teto diário de operações atingido ({par['maxOpsDia']}). Entrada "
                                   f"automática em {ticker} (gatilho de entrada atingido) ficou registrada, "
                                   f"sem execução."})
            continue
        valor_op = qty * price
        if par["maxValorOp"] > 0 and valor_op > par["maxValorOp"]:
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Teto por operação (R$ {par['maxValorOp']:.2f}) excedido na entrada "
                                   f"automática de {ticker} (R$ {valor_op:.2f}). Registrado, sem execução."})
            continue
        store.buy(conn, ticker, qty, price, user_id=scope, meta={"setup": r.get("setup")}, origem="automatico")  # ADR-012 (Fase 3)
        executed += 1
        _bump_ops(conn, scope, store.get(conn, "agent", user_id=scope) or ag)
        # `t`/`tag` (260824-i45, itens 1 e 2): destino do toque e marco do
        # título. O `text` fica byte a byte como estava.
        events.append({"time": _now_str(), "kind": "buy", "t": ticker, "tag": "entrada-auto",
                       "text": f"Entrada automática: {ticker} comprado ({qty} ações, "
                               f"{par['allocPct']:.0f}% do caixa) a R$ {price:.2f} — gatilho de entrada "
                               f"atingido."})
        # Dedupe com o push do vigia (timing_watch): marca o ticker como já
        # avisado hoje, senão o push "condição atingida" competiria com a
        # compra real já feita neste mesmo ciclo — mesma chave/formato que
        # `timing_watch._estado` usa, só gravada aqui em vez de por ele.
        tw_estado["ultimo"][ticker] = "gatilho"
        if ticker not in tw_estado["avisados"]:
            tw_estado["avisados"].append(ticker)
        tw_mudou = True

    if tw_mudou:
        db.kv_set(conn, "timingWatch", tw_estado, user_id=scope)
    return executed


def agent_params(ag: dict, app_mode: str = None) -> dict:
    """Normaliza a seção agent para os parâmetros do servidor (defaults sãos).

    `app_mode` é o `config.appMode` do usuário (não a seção `agent`) — quem
    chama e SABE o modo do usuário deve passar; `None` (default) preserva o
    comportamento de antes desta trava, para os poucos chamadores que varrem
    muitos usuários sem carregar a config de cada um (ver
    `list_protecao_sem_operador`)."""
    ag = ag or {}
    rules = ag.get("rules") if isinstance(ag.get("rules"), dict) else {}
    mode = ag.get("mode") if ag.get("mode") in ("executar", "sinalizar") else ("executar" if ag.get("autonomous") else "sinalizar")
    # Trava estrutural (Fase A do plano, D1): Modo Estudo é educacional — o
    # agente NUNCA executa ordem automática ali, e isso não é preferência
    # configurável, é filosofia do app. `store.set_agent` já evita gravar
    # "executar" fora do Modo Operador, mas a leitura precisa da MESMA trava:
    # dado antigo (de antes desta entrega) ou escrito por outra via não pode
    # reabrir a lacuna. `app_mode is None` é o único jeito de pular a trava —
    # reservado a quem não tem o appMode do usuário à mão (ver acima).
    if app_mode is not None and app_mode != "operador":
        mode = "sinalizar"
    return {
        "serverEnabled": bool(ag.get("serverEnabled")),
        "mode": mode,
        "rules": {"stop": rules.get("stop", True) is not False,
                  "alvo": rules.get("alvo", True) is not False,
                  "trailing": bool(rules.get("trailing"))},
        # F2: default "percentual" preserva o comportamento de quem já usa o agente.
        "trailingMode": ag.get("trailingMode") if ag.get("trailingMode") in TRAILING_MODES else "percentual",
        "trailingAtrMult": max(ATR_MULT_MIN, min(ATR_MULT_MAX, float(ag.get("trailingAtrMult") or ATR_MULT_DEFAULT))),
        "trailingLookback": max(LOOKBACK_MIN, min(LOOKBACK_MAX, int(ag.get("trailingLookback") or LOOKBACK_DEFAULT))),
        "trailingPct": float(ag.get("trailingPct") or 5.0),
        # F3: default False preserva quem já usa `rules.alvo` como fecha-no-alvo.
        "alvoDinamico": bool(ag.get("alvoDinamico")),
        "maxOpsDia": int(ag.get("maxOpsDia") or 3),
        "maxValorOp": float(ag.get("maxValorOp") or 0),
        "intervalMin": max(1, min(240, int(ag.get("intervalMin") or 15))),
        # Fase B (entrada automática): default False preserva quem nunca ligou;
        # a trava de MODO (Operador) fica em `_avaliar_entradas`, que recebe o
        # `app_mode` separadamente — mesma razão de `mode` acima, mas o teste
        # de defesa em profundidade cobre a função, não este dict.
        "entradaAuto": bool(ag.get("entradaAuto")),
        # D4: `allocPct` já existia (UI + modelo de dados) mas era decorativo —
        # agora alimenta o cálculo de quantidade da entrada automática. Mesmo
        # range/default de sempre (1–20%, default 5%), teto absoluto no backend.
        "allocPct": max(1, min(20, float(ag.get("allocPct") or 5))),
    }


def _ops_today(ag: dict) -> int:
    return int(ag.get("opsToday") or 0) if ag.get("opsDate") == _today() else 0


def _bump_ops(conn, scope, ag):
    n = _ops_today(ag) + 1
    db.kv_set(conn, "agent", {**ag, "opsToday": n, "opsDate": _today()}, user_id=scope)
    return n


async def run_cycle_for(conn, scope, quotes_getter, origem: str = "agendado", snapshot_getter=None,
                        option_quotes_getter=None) -> dict:
    """UM ciclo do agente para UM escopo (usuário ou anônimo). Portado do
    /api/cycle e estendido com modo/tetos/trailing. Retorna {events, executed}.
    `quotes_getter(tickers) -> {t: {price, ...}}` é injetado (fake nos testes).
    `option_quotes_getter(underlying, expiration) -> payload` (v2, ADR-003/004/005)
    avalia `optionPositions` — None desliga a segunda passada sem quebrar quem
    ainda não tem contratos abertos.

    FASE 3 (Operador): instrumentado — guard de sobreposição, duração medida,
    início/erros registrados no agentLog (o Diário da UI mostra o que houve)."""
    key = scope or "__anon__"
    if key in _CYCLE_BUSY:
        return {"events": [], "executed": 0, "skipped": "ciclo já em andamento"}
    _CYCLE_BUSY.add(key)
    t0 = time.monotonic()
    try:
        return await _run_cycle_inner(conn, scope, quotes_getter, origem, t0, snapshot_getter, option_quotes_getter)
    except Exception as e:  # noqa: BLE001 — erro do ciclo vira LOG, nunca silêncio
        if scope:
            store.push_agent_log(conn, [{"time": _now_str(), "kind": "error",
                                         "text": f"Ciclo ({origem}) FALHOU após {time.monotonic()-t0:.1f}s: {e}"}], user_id=scope)
        raise
    finally:
        _CYCLE_BUSY.discard(key)


async def _run_cycle_inner(conn, scope, quotes_getter, origem: str, t0: float, snapshot_getter=None,
                           option_quotes_getter=None) -> dict:
    positions = store.get(conn, "positions", user_id=scope) or []
    ag = store.get(conn, "agent", user_id=scope) or {}
    # Trava estrutural (Fase A): o ciclo PRECISA saber o appMode real do
    # usuário para decidir se "executar" vale — sem isto, `agent_params`
    # ficaria cego e um `mode="executar"` salvo (migração incompleta, escrita
    # por outra via) executaria ordem em Modo Estudo.
    cfg = store.get(conn, "config", user_id=scope) or {}
    app_mode = cfg.get("appMode") if isinstance(cfg, dict) else None
    par = agent_params(ag, app_mode=app_mode)
    quotes_data = await quotes_getter([p["t"] for p in positions]) if positions else {}
    sem_cotacao = [p["t"] for p in positions if (quotes_data.get(p["t"]) or {}).get("price") is None]
    events, executed = [], 0

    # F2/F3: insumo técnico (ATR) do trailing dinâmico E do alvo dinâmico — os
    # dois reusam o mesmo contexto. Só busca quando algum dos dois PRECISA; no
    # percentual sem alvo dinâmico o ciclo continua custando o que custava.
    # Falha de um ticker não derruba o ciclo: cada critério cai para o default
    # dele e a descrição no Diário denuncia a troca.
    ctxs = {}
    if ((par["rules"]["trailing"] and par["trailingMode"] != "percentual") or par["alvoDinamico"]) \
            and snapshot_getter is not None and positions:
        for p in positions:
            try:
                snap = await snapshot_getter(p["t"])
                if snap:
                    ctxs[p["t"]] = contexto_trailing(snap)
            except Exception as e:  # noqa: BLE001 — insumo técnico é best-effort
                events.append({"time": _now_str(), "kind": "warn",
                               "text": f"Contexto técnico de {p['t']}: indisponível ({e}). "
                                       f"Usando os defaults neste ciclo."})
    for pos in list(positions):
        q = quotes_data.get(pos["t"]) or {}
        price = q.get("price")
        if price is None:
            continue
        # Trailing stop (regra opcional): SOBE o stop conforme o preço avança;
        # nunca desce. Registro descritivo — o app ensina o mecanismo.
        # F2: o critério vem de `trailingMode` (percentual | atr | estrutura).
        # A monotonicidade é aplicada AQUI, uma vez, para os três modos — nenhum
        # critério novo pode afrouxar o stop sem passar por esta comparação.
        if par["rules"]["trailing"] and pos.get("stop") is not None:
            novo, criterio = nivel_trailing(par["trailingMode"], price, par, ctxs.get(pos["t"]))
            if novo is not None and novo > pos["stop"]:
                store.set_position(conn, pos["t"], stop=novo, alvo=None, has_stop=True, has_alvo=False, user_id=scope)
                events.append({"time": _now_str(), "kind": "info",
                               "text": f"Trailing: stop de {pos['t']} ajustado para R$ {novo:.2f} ({criterio})."})
                pos = {**pos, "stop": novo}
        breach_stop = par["rules"]["stop"] and pos.get("stop") is not None and price <= pos["stop"]
        hit_alvo = par["rules"]["alvo"] and pos.get("alvo") is not None and price >= pos["alvo"]
        # F3: alvo batido, sem stop rompido — antes de fechar, tenta ESTENDER.
        # Só quando o Alex ligou (`alvoDinamico`); senão o comportamento de
        # sempre (fecha no alvo) continua intacto.
        if hit_alvo and not breach_stop and par["alvoDinamico"]:
            novo_alvo, criterio = avaliar_alvo_dinamico(price, pos, ctxs.get(pos["t"]))
            if novo_alvo is not None:
                usadas = int(pos.get("alvoExtensoes") or 0) + 1
                store.set_position(conn, pos["t"], alvo=novo_alvo, has_alvo=True,
                                    alvo_extensoes=usadas, user_id=scope)
                events.append({"time": _now_str(), "kind": "info",
                               "text": f"Alvo dinâmico: {pos['t']} {criterio}."})
                pos = {**pos, "alvo": novo_alvo, "alvoExtensoes": usadas}
                hit_alvo = False
        if not (breach_stop or hit_alvo):
            continue
        motivo = "stop atingido" if breach_stop else "alvo atingido"
        valor_op = price * (pos.get("qty") or 0)
        if par["mode"] != "executar":
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Sinal do agente: {pos['t']} com {motivo} (R$ {price:.2f}). Modo 'apenas sinalizar' — nenhuma operação feita."})
            continue
        if _ops_today(ag) + executed >= par["maxOpsDia"]:
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Teto diário de operações atingido ({par['maxOpsDia']}). {pos['t']} com {motivo} ficou registrado, sem execução."})
            continue
        if par["maxValorOp"] > 0 and valor_op > par["maxValorOp"]:
            events.append({"time": _now_str(), "kind": "warn",
                           "text": f"Teto por operação (R$ {par['maxValorOp']:.2f}) excedido em {pos['t']} (R$ {valor_op:.2f}). Registrado, sem execução."})
            continue
        # 260824-i45 (item 3): o `pnl` vem do RETORNO de `store.sell`
        # (`store.py:650`), o motor determinístico — recompor
        # `(price - avg) * qty` aqui violaria o princípio 5 do CLAUDE.md
        # (número de carteira só sai do motor). Este call site vende sempre
        # TOTAL (sem `qty=`), então o valor é realizado, em R$ e com o sinal
        # certo. `pnl is None` (posição sumiu entre a leitura e a venda)
        # mantém o texto de antes — sem inventar resultado.
        pnl = store.sell(conn, pos["t"], price, user_id=scope, motivo="stop" if breach_stop else "alvo",
                         origem="automatico")  # ADR-012 (Fase 3) / ADR15-04
        executed += 1
        _bump_ops(conn, scope, store.get(conn, "agent", user_id=scope) or ag)
        _txt = f"Proteção simulada: {pos['t']} vendido ({motivo}) a R$ {price:.2f}."
        if pnl is not None:
            _txt += f" Resultado realizado: R$ {pnl:+.2f}."
        # `t`/`tag` (item 2): o marco já existia como `breach_stop`/`motivo` e
        # morria aqui — só `text` viajava até o push, que caía no genérico.
        events.append({"time": _now_str(), "kind": "buy", "t": pos["t"],
                       "tag": "stop" if breach_stop else "alvo", "pnl": pnl, "text": _txt})
    executed = await _avaliar_opcoes(conn, scope, ag, par, option_quotes_getter, executed, events)
    # Fase B: entrada automática — DEPOIS da saída (stop/alvo) e das opções,
    # de propósito (não faz sentido abrir posição nova no mesmo ciclo em que
    # talvez feche outra do mesmo ticker). Early return interno cobre
    # entradaAuto=False/Modo Estudo sem custo extra de kv.
    executed = await _avaliar_entradas(conn, scope, ag, par, app_mode, positions, executed, events)
    dur = time.monotonic() - t0
    resumo = f"Ciclo ({origem}) em {dur:.1f}s · {len(positions)} posição(ões) · {executed} execução(ões)"
    if sem_cotacao:
        resumo += f" · SEM cotação: {', '.join(sem_cotacao)} (provável rate-limit do provedor — tento no próximo ciclo)"
        events.append({"time": _now_str(), "kind": "warn", "text": resumo})
    elif not events:
        events.append({"time": _now_str(), "kind": "info",
                       "text": resumo + ". Nenhum stop/alvo atingido."})
    else:
        events.append({"time": _now_str(), "kind": "info", "text": resumo})
    store.push_events(conn, events, user_id=scope)
    if scope:  # log persistente do agente (3.3a) só faz sentido por usuário
        store.push_agent_log(conn, events, user_id=scope)
    # `appMode` (260824-i45, item 2): o modo já foi lido acima para o
    # `agent_params`; devolvê-lo poupa o funil D3 de uma leitura de kv por
    # usuário por tick só para escolher o vocabulário do título.
    return {"events": events, "executed": executed, "appMode": app_mode}


def _agent_rows(conn) -> list:
    """(uid, ag) de todo usuário com seção `agent` no kv. Extraído de
    list_server_users para ser reusado sem duplicar a query — o contrato de
    list_server_users NÃO muda (mesma varredura, mesmo retorno)."""
    rows = conn.execute("SELECT key, value FROM kv WHERE key LIKE 'u:%:agent'").fetchall()
    out = []
    import json as _json
    for key, value in rows:
        try:
            ag = _json.loads(value)
        except (ValueError, TypeError):
            continue
        if isinstance(ag, dict):
            out.append((key[len("u:"):-len(":agent")], ag))
    return out


def list_server_users(conn) -> list:
    """Usuários com o agente server-side LIGADO (varre o kv 'u:<id>:agent')."""
    return [uid for uid, ag in _agent_rows(conn) if ag.get("serverEnabled")]


def list_protecao_sem_operador(conn) -> list:
    """qa/41 (H6): usuários com stop/alvo ARMADO numa posição e o Operador no
    servidor DESLIGADO.

    Por que isto existe: "proteção armada" (stop/alvo na posição) e "Operador
    no servidor" (serverEnabled) são controles SEPARADOS, e armar o primeiro
    não liga o segundo. `/api/cycle` e `/api/agent/run-now` — os caminhos do
    app ABERTO — chamam run_cycle_for direto, sem consultar serverEnabled;
    este laço consulta. Resultado: quem arma o stop sem ligar o Operador vê a
    ordem executar com o app aberto e NADA acontecer com o app fechado.
    Parece bug do agente; é assimetria de contrato entre os dois caminhos.

    O laço não pode ligar o Operador por conta própria (é decisão do usuário —
    e ligar sozinho seria pior: executaria ordem que ninguém pediu). O que ele
    PODE é parar de ser silencioso: contar no status e avisar no Diário."""
    out = []
    for uid, ag in _agent_rows(conn):
        if ag.get("serverEnabled"):
            continue                                   # já é cuidado pelo laço
        # Sem app_mode de propósito: esta função varre TODO usuário com seção
        # `agent` no kv (via _agent_rows) sem carregar a config de cada um —
        # custaria uma leitura extra por usuário só para contar. Não é um
        # ponto de execução (só conta quem tem stop/alvo ARMADO), então a
        # trava da Fase A não se aplica aqui: `rules.stop`/`rules.alvo` não
        # mudam com o appMode.
        par = agent_params(ag)
        if not (par["rules"]["stop"] or par["rules"]["alvo"]):
            continue                                   # nem stop nem alvo valem para ele
        for p in (store.get(conn, "positions", user_id=uid) or []):
            if ((par["rules"]["stop"] and p.get("stop") is not None) or
                    (par["rules"]["alvo"] and p.get("alvo") is not None)):
                out.append(uid)
                break
    return out


def _avisar_protecao_sem_operador(conn) -> int:
    """qa/41 (H6): avisa NO DIÁRIO, 1x/dia, quem tem proteção armada sem o
    Operador ligado. Gate persistido no kv (não em memória) — senão o deploy
    zeraria e o aviso repetiria. Best-effort: nunca derruba o laço."""
    n = 0
    hoje = _today()
    for uid in list_protecao_sem_operador(conn):
        try:
            if db.kv_get(conn, "avisoProtecaoSemOperador", None, user_id=uid) == hoje:
                continue
            store.push_agent_log(conn, [{"time": _now_str(), "kind": "warn", "text": (
                "Você tem stop/alvo armado numa posição, mas o Operador no servidor está "
                "DESLIGADO. Sem ele, a proteção só é avaliada enquanto o app está aberto — "
                "com o app fechado, ninguém acompanha o preço por você. Ligue em "
                "Perfil → Operador para o servidor acompanhar suas posições no pregão."
            )}], user_id=uid)
            db.kv_set(conn, "avisoProtecaoSemOperador", hoje, user_id=uid)
            n += 1
        except Exception as e:  # noqa: BLE001 — aviso nunca derruba o laço
            print(f"[agent] aviso de proteção sem operador falhou para {uid[:8]}…: {e}")
    return n


async def _avisar_gatilhos(conn) -> int:
    """Vigia do gatilho: varre quem consentiu e envia o aviso de condição
    atingida. Isolado do `notify_push` do Operador de propósito — esta classe
    vai SILENCIOSA (priority 5, sem som) e com o payload carregando o ticker,
    para o toque na notificação ter destino.

    O fan-out é concorrente com UM cliente HTTP compartilhado: `send_to_user`
    abre uma conexão por chamada e espera até 10 s por token, em série. Com N
    usuários isso travaria a passada intraday e o ciclo de todo mundo atrás.
    """
    # imports locais: sem ciclo de import (timing_watch → timing → intraday)
    from . import candles as candles_mod, intraday, push, radar_daily, timing_watch
    if timing_watch.kill_switch_on():
        return 0
    import httpx
    p = candles_mod.normalize_period(None)   # período CANÔNICO do Radar diário
    radar_stored = radar_daily.get_stored(conn, p)
    intra_stored = intraday.get_stored(conn)
    async with httpx.AsyncClient(http2=True, timeout=10) as cliente:
        async def _enviar(uid, titulo, corpo, tickers):
            # `t` SÓ no aviso de um ativo. No agregado ("3 ativos · condição
            # atingida"), mandar `tickers[0]` faria o toque levar em silêncio a
            # UM deles e fixar a explicação nos números dele — o mesmo erro de
            # ticker trocado que a reserva da eleição existe para evitar, e
            # justamente no caminho da abertura, quando mais gente é avisada.
            extra = {"kind": "timing"}
            if len(tickers) == 1:
                extra["t"] = tickers[0]
            # 260824-i45 (item 4): registra o EVENTO DE MERCADO em
            # `agent.events` — a tela "EVENTOS E AVISOS RECENTES"
            # (App.jsx:4301). Até aqui o único rastro do gatilho era a linha de
            # ENTREGA logo abaixo ("Aviso de condição atingida enviado a
            # N/M aparelho(s)"), que vai para o `agentLog` (tela técnica) e
            # registra o ENVIO, não o evento — ela continua existindo, sem
            # alteração. Vem ANTES do `try` do envio de propósito: o evento de
            # mercado aconteceu independentemente de a entrega dar certo.
            # `t` só no caso de UM ativo, pela mesma razão do comentário acima.
            try:
                store.push_events(conn, [{"time": _now_str(), "kind": "info",
                                          "tag": "timing-gatilho",
                                          "t": tickers[0] if len(tickers) == 1 else None,
                                          "text": corpo}], user_id=uid)
            except Exception as e:  # noqa: BLE001 — registro nunca derruba o aviso
                print(f"[timing_watch] registro do evento para {uid[:8]}… falhou: {e}")
            try:
                # `send_to_user` NÃO levanta nos casos que importam: devolve
                # sent=0 para APNs não configurado, aparelho sem token, HTTP
                # não-200 e token rejeitado. Logar "enviado" sem ler o retorno
                # faria o Diário afirmar uma entrega que não houve — e a vaga
                # do dia já foi gasta (`avisados` é gravado antes do envio).
                # Todo o `_REASON_HELP` existe para não perder essa distinção.
                r = await push.send_to_user(conn, uid, titulo, corpo, som=False,
                                            prioridade="5", client=cliente, extra=extra)
                alvos = ", ".join(tickers)
                if r.get("sent"):
                    txt, kind = (f"Aviso de condição atingida enviado a {r['sent']}/{r['total']} "
                                 f"aparelho(s): {alvos}."), "info"
                else:
                    detalhes = "; ".join(r.get("detalhes") or []) or "nenhum aparelho registrado"
                    txt, kind = (f"Aviso de condição atingida NÃO entregue ({alvos}): {detalhes}. "
                                 "O aviso deste ativo não se repete hoje — abra o app para ver o "
                                 "estado atual."), "warn"
                store.push_agent_log(conn, [{"time": _now_str(), "kind": kind, "text": txt}],
                                     user_id=uid)
            except Exception as e:  # noqa: BLE001 — push é best-effort
                print(f"[timing_watch] envio para {uid[:8]}… falhou: {e}")
        return await timing_watch.maybe_run(conn, radar_stored, intra_stored, _enviar)


async def scheduler_loop(conn, quotes_getter, notify_push=None, interval_s: int = None, once: bool = False,
                         radar_fetch=None, snapshot_getter=None, intraday_fetch=None, option_quotes_getter=None,
                         analytics_conn=None):
    """Laço do servidor: a cada N min (env B3_AGENT_INTERVAL_S), dentro do
    pregão e sem kill-switch, roda o ciclo de cada usuário habilitado.
    `notify_push(user_id, title, body)` (opcional) envia APNs por ação executada.
    FASE 4 (1.3): `radar_fetch` (opcional) habilita a varredura diária do Radar
    — 1x/dia útil no horário configurado, FORA do gate de pregão (8h45 é
    pré-abertura), reusando este mesmo laço (sem segundo scheduler).
    qa/30 (Fase A): o mesmo `radar_fetch` também alimenta a avaliação diária
    das análises pendentes (analysis_outcomes) — outro hook no mesmo laço,
    sem scheduler novo.
    qa/47: `analytics_conn` (opcional, banco SEPARADO — ver analytics.py)
    habilita o rollup+purga diário de eventos de comportamento — hook próprio,
    independente do kill-switch do agente (não é execução de ordem) e do
    gate de pregão (não depende de cotação).
    ADR-017 (Bloco 1): o mesmo laço também avança o ledger de sinais
    resolvidos — hook próprio, gate próprio (`B3_LEDGER_DAILY_HHMM`, default
    09:15), lendo do `candle_cache` sem custo de rede.
    Fase 10: o mesmo laço arma a ponte gatilho→put — hook próprio, gate próprio (`B3_PUT_BRIDGE_HHMM`, default 09:30), lendo o Radar já armazenado, sem custo de rede extra e sem scheduler novo."""
    interval = interval_s or int(os.environ.get("B3_AGENT_INTERVAL_S") or INTERVAL_S_DEFAULT)
    # 260824-kc2: preferência por classe de push. Import local (padrão do
    # arquivo, ex.: `_alertar_kill_switch` e os hooks abaixo) e FORA do
    # `while`: a tabela tag→classe e o `prefs_for` são consultados a cada
    # passada dos dois funis de push deste laço.
    from . import push  # import local: sem ciclo de import
    while True:
        # P2 (liveness): heartbeat PERSISTIDO a CADA tick, FORA do gate de pregão.
        # O corpo do ciclo (e o registro de passada) só roda dentro do pregão, então
        # off-hours não havia sinal nenhum e o deploy zerava o estado em memória —
        # impossível distinguir "vivo, pregão fechado" de "morto". O heartbeat bate
        # sempre, sobrevive ao deploy (kv/SQLite) e é o que o status expõe como lacoVivo.
        try:
            db.kv_set(conn, "agentHeartbeat", {
                "ts": time.time(),
                "pregaoAberto": in_market_hours(),
                "atBRT": datetime.now(BRT).strftime("%d/%m %H:%M"),
            }, user_id=None)
        except Exception as e:  # noqa: BLE001 — heartbeat nunca derruba o laço
            print(f"[agent] heartbeat: {e}")
        # C-37: alerta ATIVO de kill-switch ligado — pendurado AQUI, logo
        # após o heartbeat e ANTES do primeiro portão do kill-switch mais
        # abaixo neste laço (dentro do gate de pregão). Atrás do portão, o
        # alerta seria silenciado exatamente pelo estado que precisa
        # denunciar — é o mesmo erro do heartbeat que mascarou o incidente
        # real (2,5 dias de execução automática parada sem ninguém notar).
        # `try` PRÓPRIO, no padrão dos demais hooks deste laço: nenhuma
        # falha do alerta pode derrubar o ciclo de stop/alvo de todos os
        # usuários.
        try:
            await _alertar_kill_switch(conn)
        except Exception as e:  # noqa: BLE001
            print(f"[kill-switch-alerta] {e}")
        if analytics_conn is not None:
            try:
                from . import analytics as analytics_mod  # import local: sem ciclo de import
                await analytics_mod.maybe_run(analytics_conn)
            except Exception as e:  # noqa: BLE001 — analytics nunca derruba o laço
                print(f"[analytics] hook do scheduler falhou: {e}")
            try:
                from . import automacao  # ADR-012 (Fase 3): import local, sem ciclo de import
                automacao.maybe_refresh_cache(conn, analytics_conn)
            except Exception as e:  # noqa: BLE001 — automação nunca derruba o laço
                print(f"[automacao] hook do scheduler falhou: {e}")
            try:
                _maybe_registrar_metricas_diarias(conn, analytics_conn)
            except Exception as e:  # noqa: BLE001 — métricas nunca derrubam o laço
                print(f"[obs-metricas] hook do scheduler falhou: {e}")
        try:
            # `is_trading_day` (e não `in_market_hours`): estes jobs rodam FORA
            # da janela de horário de propósito — o radar diário é 8h45, na
            # pré-abertura. Mas em sábado, domingo e feriado da B3 não há dado
            # novo para buscar, e antes eles rodavam assim mesmo.
            from . import pregao  # import local: sem ciclo de import
            if radar_fetch is not None and not kill_switch_on() and pregao.is_trading_day():
                from . import radar_daily  # import local: sem ciclo de import
                await radar_daily.maybe_run(conn, radar_fetch, notify_push=notify_push)
                from . import analysis_outcomes  # qa/30 (Fase A): import local, sem ciclo de import
                await analysis_outcomes.maybe_run(conn, radar_fetch, cache_conn=analytics_conn)  # ADR-012 (Fase 1)
                # qa/36 (F10.2): aquece o cache de fundamentos do universo 1x/dia
                # (o TTL de 7 dias garante que só rebusca o vencido). Cache-only
                # no scan → o job é a única via de rede; best-effort.
                from . import fundamentals, scanner  # import local: sem ciclo
                await fundamentals.maybe_warm(conn, scanner.get_universe())
                # ADR-017 (Bloco 1): manutenção diária do ledger de sinais
                # resolvidos — DEPOIS de radar_daily/fundamentals de propósito:
                # o candle_cache já foi preenchido pelo Radar minutos antes, e
                # este hook lê exatamente esse cache via `candle_cache.peek`,
                # sem gastar requisição nova de brapi (ADR-008). `try/except`
                # PRÓPRIO — segundo cinto além do try/except interno de
                # `signal_ledger_job.maybe_run` (que já nunca propaga): nenhuma
                # falha aqui pode chegar ao heartbeat, ao kill-switch ou ao
                # ciclo de stop/alvo dos usuários, mesmo padrão de
                # `_alertar_kill_switch`/`analytics_mod.maybe_run` acima.
                try:
                    from . import signal_ledger_job  # import local: sem ciclo de import
                    await signal_ledger_job.maybe_run(conn)
                except Exception as e:  # noqa: BLE001 — ledger nunca derruba o laço
                    print(f"[ledger-diario] hook do scheduler falhou: {e}")
                # Fase 10 (PUT-01/PUT-02): ponte gatilho→put. DEPOIS do ledger de
                # propósito — o Radar diário já armazenou o resultado EOD que este
                # hook lê (`radar_daily.get_stored`), sem gastar requisição nova.
                # `try/except` PRÓPRIO, segundo cinto além do try/except interno de
                # `put_bridge.maybe_run` (que já nunca propaga): nenhuma falha da
                # ponte pode chegar ao heartbeat, ao kill-switch ou ao ciclo de
                # stop/alvo dos usuários — mesma regra de `signal_ledger_job` acima.
                try:
                    from . import put_bridge  # import local: sem ciclo de import
                    await put_bridge.maybe_run(conn)
                except Exception as e:  # noqa: BLE001 — a ponte nunca derruba o laço
                    print(f"[put-bridge] hook do scheduler falhou: {e}")
            if not kill_switch_on() and in_market_hours():
                # ADR-001 (item 7): passada INTRADAY, GLOBAL, uma por acordar do
                # laço. Roda ANTES do ciclo por usuário de propósito — assim o
                # Radar intraday do pregão já está fresco quando cada usuário é
                # avaliado. Custo O(1) em usuários (65 requisições, 0,45 s
                # medidos), chave de cache e de armazenamento próprias: o
                # caminho do Radar DIÁRIO não é tocado.
                if intraday_fetch is not None:
                    from . import intraday  # import local: sem ciclo de import
                    if await intraday.maybe_run(conn, intraday_fetch, last_ts=_LAST_INTRADAY["ts"]):
                        _LAST_INTRADAY["ts"] = time.monotonic()
                        # Vigia do gatilho. Ele próprio ignora barra já varrida
                        # (`timing_watch._ULTIMA_BARRA`), então pendurar aqui é
                        # só para casar com dado fresco — não é o que evita
                        # repetir. `try` PRÓPRIO: sem ele, uma falha
                        # aqui (get_stored, httpx, qualquer coisa a montante do
                        # `maybe_run`, que se protege sozinho) cairia no except
                        # do laço e stop/alvo de TODOS os usuários deixariam de
                        # ser avaliados nesta passada. O componente mais novo
                        # não pode derrubar o mais crítico.
                        if notify_push is not None:
                            try:
                                await _avisar_gatilhos(conn)
                            except Exception as e:  # noqa: BLE001
                                print(f"[timing_watch] gancho falhou: {e}")
                # qa/41 (H6): durante o pregão, quem tem proteção armada e o
                # Operador desligado é avisado no Diário (1x/dia). O laço passa
                # por cima dessa gente por contrato — mas em silêncio ela achava
                # que estava protegida.
                _avisar_protecao_sem_operador(conn)
                # Fase 2 (MERC-02, plano 02-03): execução de ordens pendentes —
                # MESMO gate do resto do bloco (kill-switch + pregão aberto).
                # Roda ANTES do ciclo por usuário, logo abaixo, de propósito:
                # uma ordem que acabou de executar já entra como posição
                # avaliável pelo stop/alvo do Operador NESTA MESMA passada,
                # não só na próxima. `try` PRÓPRIO: o comentário da linha 950
                # explica a regra da casa — componente novo não pode derrubar
                # o ciclo mais crítico (T-02-16).
                try:
                    from . import pending_orders  # import local: sem ciclo de import
                    # Varre quem TEM ordem pendente gravada, não quem está no
                    # Operador (a função abaixo do bloco, chamada logo mais):
                    # ordem pendente é um pedido MANUAL do usuário,
                    # independente do Operador estar ligado — senão quem está
                    # em Modo Estudo ficaria com ordem presa pra sempre só por
                    # nunca ter ligado o Operador no servidor.
                    escopos = store.scopes_com_pendentes(conn)
                    if escopos:
                        # Reúne os tickers DISTINTOS de todas as ordens de
                        # todos os escopos e pede UM lote só — orçamento da
                        # brapi é de 15k requisições/mês pro app inteiro
                        # (ADR-008), então a passada tem que ser O(tickers
                        # distintos), nunca O(ordens).
                        tickers = sorted({o["t"] for uid in escopos
                                          for o in pending_orders.listar(conn, user_id=uid)})
                        cotacoes = await quotes_getter(tickers) if tickers else {}

                        def _price_getter(t, _c=cotacoes):
                            # Sem rede — só LÊ do lote já buscado acima.
                            return _c.get(t) or {"price": None}

                        _executadas = 0
                        _canceladas = 0
                        for uid in escopos:
                            try:
                                eventos = await pending_orders.executar_pendentes(conn, uid, _price_getter)
                            except Exception as e:  # noqa: BLE001 — 1 escopo não derruba os outros
                                print(f"[pending-orders] escopo {str(uid)[:8]}…: {e}")
                                continue
                            # 260824-i45 (item 2): leitura do modo CONDICIONAL
                            # — `executar_pendentes` devolve lista vazia na
                            # esmagadora maioria dos ticks, e uma leitura de
                            # `config` por uid por tick sem nenhum push a
                            # emitir seria trabalho jogado fora. Mapeamento de
                            # nomes: `config.appMode` é "operador"|"estudo";
                            # as chaves de `skill_ref` são "operador"|
                            # "educacional".
                            # 260824-kc2: as PREFS entram na MESMA condicional,
                            # pela mesma razão — uma leitura de kv por uid por
                            # tick sem push a emitir é trabalho jogado fora.
                            # Uma leitura só por uid serve todos os eventos.
                            _modo = "educacional"
                            _prefs = None
                            if eventos:
                                _modo = "operador" if (store.get(conn, "config", user_id=uid) or {}).get("appMode") == "operador" else "educacional"
                                _prefs = push.prefs_for(conn, uid)
                            for ev in eventos:
                                _executou = ev.get("kind") == "buy"
                                _cancelou = ev.get("tag") == "pendente-cancelada"
                                if _executou:
                                    _executadas += 1
                                elif _cancelou:
                                    _canceladas += 1
                                # Push best-effort para execução E para
                                # auto-cancelamento (mesmo padrão das linhas
                                # 990-996: falha de push nunca propaga). O
                                # filtro roda só sobre os eventos devolvidos
                                # por `executar_pendentes` — nunca sobre o
                                # `agentLog` inteiro, senão qualquer `warn` do
                                # Operador viraria notificação. O `warn` de
                                # cancelamento entra aqui de propósito: a
                                # ordem some da seção "Pendentes" e o caixa
                                # volta sozinho — sem push (e sem o toast do
                                # plano 02-06) o usuário veria a ordem
                                # evaporar sem motivo (T-02-36).
                                if notify_push is not None and (_executou or _cancelou):
                                    # 260824-kc2: gate por CLASSE, depois da
                                    # contabilização acima (preferência de
                                    # aviso não mexe em métrica de execução) e
                                    # antes do envio. O evento já foi
                                    # persistido por `executar_pendentes`:
                                    # desligar a classe silencia a
                                    # INTERRUPÇÃO, nunca o rastro.
                                    # Fail-open: tag sem classe conhecida
                                    # (`classe_do_evento` devolve None) envia.
                                    _classe = push.classe_do_evento(ev.get("tag"))
                                    if _classe and not (_prefs or {}).get(_classe, True):
                                        continue
                                    # Título derivado do `tag` que o evento já
                                    # carregava, e `t` no payload para o toque
                                    # ter destino (260824-i45, itens 1 e 2).
                                    _tk = str(ev.get("t") or "")
                                    _extra = {"kind": "ordem"}
                                    if _TICKER_PUSH_RE.match(_tk):
                                        _extra["t"] = _tk
                                    try:
                                        await notify_push(uid, skill_ref.push_titulo(_modo, ev.get("tag"), _tk),
                                                          ev["text"], extra=_extra)
                                    except Exception:  # noqa: BLE001 — push é best-effort
                                        _registrar_push_falho()
                        LAST_PENDING.update(at=datetime.now(BRT).strftime("%d/%m %H:%M"),
                                            escopos=len(escopos), executadas=_executadas,
                                            canceladas=_canceladas, erro=None)
                except Exception as e:  # noqa: BLE001 — bloco novo não derruba o ciclo do Operador
                    LAST_PENDING["erro"] = str(e)[:300]
                    print(f"[pending-orders] bloco: {e}")
                _t0 = time.monotonic()
                _erros = []
                LAST_RUN.update(at=datetime.now(BRT).strftime("%d/%m %H:%M"), usuarios=0, executadas=0, erro=None)
                _agora = time.time()
                for uid in list_server_users(conn):
                    # Gate por usuário: respeita o intervalMin DELE (default 15).
                    # Sem app_mode de propósito: só o campo `intervalMin` é lido
                    # aqui, e ele não muda com o appMode — buscar `config` a
                    # cada usuário a cada tick só para isto seria leitura extra
                    # sem efeito. A trava de verdade (mode="executar" só em
                    # Modo Operador) mora dentro de `run_cycle_for`/
                    # `_run_cycle_inner`, chamado logo abaixo — é lá que a
                    # execução de fato acontece.
                    _ag = store.get(conn, "agent", user_id=uid) or {}
                    _int_s = agent_params(_ag)["intervalMin"] * 60
                    _ult = LAST_USER_RUN.get(uid, 0)
                    if _agora - _ult < _int_s - 1:
                        continue  # ainda não deu o intervalo deste usuário
                    LAST_USER_RUN[uid] = _agora
                    LAST_RUN["usuarios"] += 1
                    try:
                        r = await run_cycle_for(conn, uid, quotes_getter, origem="agendado", snapshot_getter=snapshot_getter,
                                                option_quotes_getter=option_quotes_getter)
                        LAST_RUN["executadas"] += r["executed"]
                        if notify_push and r["executed"]:
                            # 260824-i45 (itens 1 e 2): itera sobre os EVENTOS
                            # (não sobre uma lista de textos), preservando o
                            # filtro `kind == "buy"`. O modo vem do próprio
                            # retorno do ciclo — sem leitura de kv extra.
                            _modo = "operador" if r.get("appMode") == "operador" else "educacional"
                            # 260824-kc2: uma leitura de prefs por uid, aqui
                            # dentro (só quando o ciclo executou algo), serve
                            # todos os eventos desta passada.
                            _prefs = push.prefs_for(conn, uid)
                            for e in r["events"]:
                                if e.get("kind") != "buy":
                                    continue
                                # Gate por CLASSE, antes do envio e sem tocar
                                # em `LAST_RUN["executadas"]` (já contabilizado
                                # acima). Os eventos seguem persistidos por
                                # `run_cycle_for`: o rastro em `agent.events`
                                # não depende da preferência de push.
                                _classe = push.classe_do_evento(e.get("tag"))
                                if _classe and not (_prefs or {}).get(_classe, True):
                                    continue
                                _tk = str(e.get("t") or "")
                                _extra = {"kind": "operador"}
                                if _TICKER_PUSH_RE.match(_tk):
                                    _extra["t"] = _tk
                                try:
                                    await notify_push(uid, skill_ref.push_titulo(_modo, e.get("tag"), _tk),
                                                      e["text"], extra=_extra)
                                except Exception:  # noqa: BLE001 — push é best-effort
                                    _registrar_push_falho()
                    except Exception as e:  # noqa: BLE001 — 1 usuário não derruba o laço
                        _erros.append(f"{uid[:8]}…: {e}")
                        print(f"[agent] ciclo de {uid} falhou: {e}")
                _push_run_history({"at": LAST_RUN["at"], "duracaoS": round(time.monotonic() - _t0, 1),
                                   "usuarios": LAST_RUN["usuarios"], "executadas": LAST_RUN["executadas"],
                                   "erros": _erros})
                if _erros:
                    LAST_RUN["erro"] = "; ".join(_erros)[:300]
        except Exception as e:  # noqa: BLE001
            print(f"[agent] laço: {e}")
        if once:
            return
        NEXT_RUN_AT["ts"] = time.time() + interval
        await asyncio.sleep(interval)


def status_snapshot(conn, interval_s: int = None) -> dict:
    """BLOCO D3 — estado observável do Operador IA no servidor."""
    prox = None
    if NEXT_RUN_AT["ts"]:
        prox = max(0, int(NEXT_RUN_AT["ts"] - time.time()))
    from . import radar_daily  # import local: sem ciclo de import
    from . import analysis_outcomes  # qa/30 (Fase A): import local, sem ciclo de import
    from . import fundamentals  # qa/46 (Fase 2): aquecimento de cache — hoje sem contador exposto
    from . import intraday  # qa/46 (Fase 2): passada intraday global — hoje sem contador exposto
    from . import pending_orders  # Fase 2 (MERC-02, plano 02-03): import local, sem ciclo de import
    # Fase 2 (MERC-02, plano 02-03): fila de ordens pendentes observável no
    # mesmo payload que já mostra `killSwitch`. Lição direta do incidente do
    # kill-switch de v1.0 (ligado sem querer, parou a execução de toda a base
    # por 2,5 dias) — foi mascarado justamente porque o heartbeat batia antes
    # do portão. Com ordens pendentes na jogada, um kill-switch esquecido
    # deixa dinheiro reservado e ordem parada indefinidamente; o contador ao
    # lado do `killSwitch`, no mesmo payload, é o que torna isso visível.
    # Contagem, nunca identidade (sem PII) — mesma regra de
    # `protecaoSemOperador`, logo abaixo.
    _escopos_pendentes = store.scopes_com_pendentes(conn)
    _total_pendentes = sum(len(pending_orders.listar(conn, user_id=uid)) for uid in _escopos_pendentes)
    # P2 (liveness): heartbeat persistido (sobrevive a deploy e bate fora do pregão).
    intervalo = interval_s or int(os.environ.get("B3_AGENT_INTERVAL_S") or INTERVAL_S_DEFAULT)
    hb = db.kv_get(conn, "agentHeartbeat", None, user_id=None) or {}
    hb_ha_s = int(time.time() - hb["ts"]) if hb.get("ts") else None
    # vivo se bateu dentro de ~2,5 intervalos (tolera 1 tick perdido + folga)
    laco_vivo = hb_ha_s is not None and hb_ha_s < intervalo * 2.5
    return {
        "killSwitch": kill_switch_on(),
        "pregaoAberto": in_market_hours(),
        "heartbeat": {
            "atBRT": hb.get("atBRT"),
            "haS": hb_ha_s,
            "pregaoAbertoNoTick": hb.get("pregaoAberto"),
            "lacoVivo": laco_vivo,
        },
        "radarDiario": dict(radar_daily.LAST_DAILY),  # FASE 4 (1.3)
        "avaliacaoAnalises": dict(analysis_outcomes.LAST_EVAL),  # qa/30 (Fase A)
        # qa/46 (Fase 2): 3 contadores que existiam só em memória, sem endpoint —
        # a função que os calcula já rodava; isto só liga o fio até o snapshot.
        "aquecimentoFundamentos": dict(fundamentals.LAST_WARM),
        "intraday": dict(intraday.LAST_PASS),
        "pushAutomaticoFalhasHoje": dict(PUSH_FAIL_TODAY),
        "ordensPendentes": {
            "total": _total_pendentes,
            "escopos": len(_escopos_pendentes),
            "ultimoCiclo": dict(LAST_PENDING),
        },
        "intervaloS": interval_s or int(os.environ.get("B3_AGENT_INTERVAL_S") or INTERVAL_S_DEFAULT),
        "usuariosHabilitados": len(list_server_users(conn)),
        # qa/41 (H6): quantos têm stop/alvo armado com o Operador DESLIGADO —
        # o laço os ignora por contrato e eles executam só com o app aberto.
        # > 0 aqui explica "o Operador só funciona quando abro o app" sem que
        # exista bug nenhum no laço. Contagem, nunca identidade (sem PII).
        "protecaoSemOperador": len(list_protecao_sem_operador(conn)),
        "ultimoCiclo": dict(LAST_RUN),
        "proximaPassadaEmS": prox,
        "passadas": list(reversed(RUN_HISTORY)),  # mais recente primeiro
        "agoraBRT": datetime.now(BRT).strftime("%d/%m %H:%M"),
    }
