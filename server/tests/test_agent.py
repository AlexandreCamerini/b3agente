"""FASE 3.5 — agente server-side com relógio e provedor FAKES."""
import asyncio
import os
import re
import tempfile
from datetime import datetime, timezone, timedelta

from app import agent, db, indicators, store


def _conn():
    d = tempfile.mkdtemp()
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    return c


def _seed(c, positions, ag):
    db.kv_set(c, "positions", positions, user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    ag_full = {"autonomous": True, **ag}
    db.kv_set(c, "agent", ag_full, user_id="u1")


def _quotes(prices):
    async def getter(tickers):
        return {t: {"price": prices.get(t)} for t in tickers}
    return getter


def _run(c, prices, snapshot_getter=None):
    return asyncio.run(agent.run_cycle_for(c, "u1", _quotes(prices),
                                           snapshot_getter=snapshot_getter))


def _snap(candles, atr):
    """STU FAKE com o mínimo que o trailing dinâmico lê (F2)."""
    async def getter(_ticker):
        return {"candles": candles, "indicators": {"atr14": [atr]}}
    return getter


def test_executa_venda_no_stop_e_registra_log():
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 1
    assert db.kv_get(c, "positions", user_id="u1") == []           # vendeu
    log = db.kv_get(c, "agentLog", [], user_id="u1")
    # F3: o ciclo grava uma linha-resumo APÓS a execução ("Ciclo ... em Xs"),
    # então a venda não é mais necessariamente log[-1] — checar por conteúdo.
    assert log and any("stop atingido" in e["text"] for e in log)


def test_modo_sinalizar_nao_opera():
    c = _conn()
    _seed(c, [{"t": "VALE3", "qty": 100, "avg": 60.0, "stop": 58.0}],
          {"serverEnabled": True, "mode": "sinalizar"})
    r = _run(c, {"VALE3": 57.0})
    assert r["executed"] == 0
    assert len(db.kv_get(c, "positions", user_id="u1")) == 1       # posição intacta
    assert any("apenas sinalizar" in e["text"] for e in r["events"])


def test_teto_diario_de_operacoes():
    c = _conn()
    _seed(c, [{"t": "AAAA3", "qty": 100, "avg": 10, "stop": 9.5},
              {"t": "BBBB4", "qty": 100, "avg": 10, "stop": 9.5}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 1})
    r = _run(c, {"AAAA3": 9.0, "BBBB4": 9.0})
    assert r["executed"] == 1
    assert len(db.kv_get(c, "positions", user_id="u1")) == 1       # 2ª ficou
    assert any("Teto diário" in e["text"] for e in r["events"])


def test_teto_por_valor_de_operacao():
    c = _conn()
    _seed(c, [{"t": "CCCC3", "qty": 1000, "avg": 50.0, "stop": 49.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 5, "maxValorOp": 1000.0})
    r = _run(c, {"CCCC3": 48.0})                                    # op = 48.000
    assert r["executed"] == 0
    assert any("Teto por operação" in e["text"] for e in r["events"])


def test_trailing_sobe_o_stop_e_nunca_desce():
    c = _conn()
    _seed(c, [{"t": "DDDD3", "qty": 100, "avg": 10.0, "stop": 9.0}],
          {"serverEnabled": True, "mode": "executar", "rules": {"trailing": True}, "trailingPct": 5})
    _run(c, {"DDDD3": 12.0})                                        # stop deve ir p/ 11.40
    pos = db.kv_get(c, "positions", user_id="u1")[0]
    assert pos["stop"] == 11.4
    _run(c, {"DDDD3": 11.5})                                        # 10.93 < 11.40 → não desce
    assert db.kv_get(c, "positions", user_id="u1") == [] or db.kv_get(c, "positions", user_id="u1")[0]["stop"] == 11.4


# ---------------------------------------------------------------------------
# F2 — Trailing dinâmico. Série REAL de PETR4 (Yahoo, pregões de 02/07 a
# 29/07/2026): é nela que percentual e critério técnico divergem de verdade.
# Uma série sintética de números redondos esconderia justamente a divergência
# que esta feature existe para produzir.
# ---------------------------------------------------------------------------
PETR4_REAL = [
    {"date": "2026-07-02", "open": 37.89, "high": 38.46, "low": 37.65, "close": 37.96},
    {"date": "2026-07-03", "open": 38.07, "high": 38.25, "low": 37.86, "close": 38.25},
    {"date": "2026-07-06", "open": 37.95, "high": 38.02, "low": 37.61, "close": 37.77},
    {"date": "2026-07-07", "open": 38.0, "high": 38.77, "low": 37.92, "close": 38.44},
    {"date": "2026-07-08", "open": 39.65, "high": 39.75, "low": 39.0, "close": 39.65},
    {"date": "2026-07-09", "open": 39.74, "high": 39.98, "low": 38.89, "close": 39.21},
    {"date": "2026-07-10", "open": 39.64, "high": 39.97, "low": 39.34, "close": 39.65},
    {"date": "2026-07-13", "open": 40.51, "high": 40.92, "low": 40.24, "close": 40.66},
    {"date": "2026-07-14", "open": 41.2, "high": 41.31, "low": 40.11, "close": 40.66},
    {"date": "2026-07-15", "open": 40.41, "high": 40.8, "low": 40.23, "close": 40.59},
    {"date": "2026-07-16", "open": 40.38, "high": 40.86, "low": 39.89, "close": 39.89},
    {"date": "2026-07-17", "open": 40.41, "high": 41.11, "low": 40.41, "close": 40.9},
    {"date": "2026-07-20", "open": 41.2, "high": 41.44, "low": 40.47, "close": 41.15},
    {"date": "2026-07-21", "open": 41.21, "high": 41.7, "low": 41.13, "close": 41.66},
    {"date": "2026-07-22", "open": 42.1, "high": 42.74, "low": 41.97, "close": 42.58},
    {"date": "2026-07-23", "open": 43.4, "high": 43.49, "low": 42.86, "close": 42.95},
    {"date": "2026-07-24", "open": 42.37, "high": 42.91, "low": 42.15, "close": 42.21},
    {"date": "2026-07-27", "open": 41.2, "high": 41.48, "low": 40.82, "close": 41.01},
    {"date": "2026-07-28", "open": 41.02, "high": 41.77, "low": 40.89, "close": 41.21},
    {"date": "2026-07-29", "open": 42.16, "high": 42.4, "low": 41.75, "close": 42.0},
]
# ATR(14) DERIVADO da série acima pelo MESMO indicador que o STU usa — não um
# número escrito à mão. Se `indicators.atr` mudar, o teste denuncia em vez de
# seguir verde com um valor que já não corresponde ao que a produção calcula.
PETR4_ATR = round(indicators.atr([c["high"] for c in PETR4_REAL],
                                 [c["low"] for c in PETR4_REAL],
                                 [c["close"] for c in PETR4_REAL], 14)[-1], 2)


def test_fixture_do_atr_bate_com_o_indicador_da_producao():
    assert PETR4_ATR == 0.97


def test_nivel_trailing_e_puro_e_os_tres_criterios_divergem():
    """O ponto da F2: com o MESMO preço, os três critérios dão níveis
    diferentes — senão a feature não teria razão de existir."""
    par = {"trailingPct": 5.0, "trailingAtrMult": 2.0, "trailingLookback": 5}
    ctx = {"atr": PETR4_ATR, "candles": PETR4_REAL}
    preco = 42.0

    pct, d_pct = agent.nivel_trailing("percentual", preco, par, ctx)
    atr, d_atr = agent.nivel_trailing("atr", preco, par, ctx)
    est, d_est = agent.nivel_trailing("estrutura", preco, par, ctx)

    assert pct == 39.9                      # 42,00 − 5%
    assert atr == 40.06                     # 42,00 − 2 × 0,97
    assert est == 40.82                     # menor mínima das últimas 5 velas
    assert len({pct, atr, est}) == 3, "os critérios precisam divergir na série real"
    # A descrição vai para o Diário: precisa NOMEAR o critério e o número.
    assert "5% abaixo do preço" in d_pct
    assert "ATR(14)" in d_atr and "0.97" in d_atr
    assert "últimas 5 velas" in d_est and "40.82" in d_est


def test_trailing_atr_ajusta_o_stop_pela_volatilidade():
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 38.0, "stop": 37.0}],
          {"serverEnabled": True, "mode": "executar", "rules": {"trailing": True},
           "trailingMode": "atr", "trailingAtrMult": 2.0})
    r = _run(c, {"PETR4": 42.0}, snapshot_getter=_snap(PETR4_REAL, PETR4_ATR))
    pos = db.kv_get(c, "positions", user_id="u1")[0]
    assert pos["stop"] == 40.06
    assert any("ATR(14)" in e["text"] for e in r["events"])


def test_trailing_estrutura_usa_a_minima_das_ultimas_velas():
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 38.0, "stop": 37.0}],
          {"serverEnabled": True, "mode": "executar", "rules": {"trailing": True},
           "trailingMode": "estrutura", "trailingLookback": 5})
    _run(c, {"PETR4": 42.0}, snapshot_getter=_snap(PETR4_REAL, PETR4_ATR))
    pos = db.kv_get(c, "positions", user_id="u1")[0]
    assert pos["stop"] == 40.82


def test_trailing_dinamico_nunca_afrouxa():
    """GUARDIÃO da F2, irmão do `test_trailing_sobe_o_stop_e_nunca_desce`: a
    monotonicidade vale para os modos técnicos, inclusive quando a volatilidade
    AUMENTA (ATR maior ⇒ nível bruto mais baixo) ou quando o preço recua."""
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 38.0, "stop": 37.0}],
          {"serverEnabled": True, "mode": "sinalizar", "rules": {"trailing": True},
           "trailingMode": "atr", "trailingAtrMult": 2.0})
    _run(c, {"PETR4": 42.0}, snapshot_getter=_snap(PETR4_REAL, PETR4_ATR))
    assert db.kv_get(c, "positions", user_id="u1")[0]["stop"] == 40.06

    # ATR dobra (mercado ficou volátil): 42,00 − 2 × 1,94 = 38,12 < 40,06.
    _run(c, {"PETR4": 42.0}, snapshot_getter=_snap(PETR4_REAL, PETR4_ATR * 2))
    assert db.kv_get(c, "positions", user_id="u1")[0]["stop"] == 40.06, "ATR maior não pode afrouxar"

    # Preço recua: 41,00 − 2 × 0,97 = 39,06 < 40,06.
    _run(c, {"PETR4": 41.0}, snapshot_getter=_snap(PETR4_REAL, PETR4_ATR))
    assert db.kv_get(c, "positions", user_id="u1")[0]["stop"] == 40.06, "recuo não pode afrouxar"


def test_trailing_sem_insumo_tecnico_cai_para_percentual_e_declara():
    """Sem ATR, a posição não pode ficar sem trailing — mas o Diário precisa
    dizer que o critério escolhido não estava disponível."""
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 38.0, "stop": 37.0}],
          {"serverEnabled": True, "mode": "executar", "rules": {"trailing": True},
           "trailingMode": "atr", "trailingPct": 5})
    r = _run(c, {"PETR4": 42.0}, snapshot_getter=None)      # nenhum STU injetado
    pos = db.kv_get(c, "positions", user_id="u1")[0]
    assert pos["stop"] == 39.9                              # caiu para o percentual
    assert any("critério técnico indisponível" in e["text"] for e in r["events"])


def test_trailing_default_continua_percentual_para_quem_ja_usava():
    """Compatibilidade: quem tem `trailingPct` e nunca ouviu falar de
    `trailingMode` não pode mudar de comportamento por causa da F2."""
    par = agent.agent_params({"rules": {"trailing": True}, "trailingPct": 7})
    assert par["trailingMode"] == "percentual"
    assert par["trailingAtrMult"] == agent.ATR_MULT_DEFAULT
    # Valor inválido vindo do kv não explode: cai no default.
    assert agent.agent_params({"trailingMode": "chute"})["trailingMode"] == "percentual"
    assert agent.agent_params({"trailingAtrMult": 99})["trailingAtrMult"] == agent.ATR_MULT_MAX
    assert agent.agent_params({"trailingLookback": 1})["trailingLookback"] == agent.LOOKBACK_MIN


def test_set_agent_valida_os_campos_do_trailing_dinamico():
    c = _conn()
    store.set_agent(c, {"trailingMode": "estrutura", "trailingAtrMult": 9.9,
                        "trailingLookback": 999}, user_id="u1")
    ag = db.kv_get(c, "agent", user_id="u1")
    assert ag["trailingMode"] == "estrutura"
    assert ag["trailingAtrMult"] == 4.0        # teto
    assert ag["trailingLookback"] == 20        # teto
    store.set_agent(c, {"trailingMode": "invalido"}, user_id="u1")
    assert db.kv_get(c, "agent", user_id="u1")["trailingMode"] == "estrutura"  # não sobrescreve


# ---------------------------------------------------------------------------
# F3 — Alvo dinâmico. Reusa a mesma série/ATR real de PETR4 da F2 (linha 103):
# alvo e trailing compartilham o insumo técnico, e um número redondo esconderia
# a divergência que o critério por ATR existe para produzir.
# ---------------------------------------------------------------------------
def test_avaliar_alvo_dinamico_estende_dentro_do_limite():
    pos = {"alvo": 45.0, "stop": 36.0, "avg": 38.0, "alvoExtensoes": 0}
    novo, criterio = agent.avaliar_alvo_dinamico(45.5, pos, {"atr": PETR4_ATR})
    assert novo == 46.45                    # 45,00 + 1,5 × 0,97
    assert "extensão 1/2" in criterio and "R:R 4.2" in criterio


def test_avaliar_alvo_dinamico_nao_dispara_antes_de_bater_o_alvo():
    pos = {"alvo": 45.0, "stop": 36.0, "avg": 38.0}
    assert agent.avaliar_alvo_dinamico(44.9, pos, {"atr": PETR4_ATR}) == (None, None)


def test_avaliar_alvo_dinamico_respeita_o_limite_de_extensoes():
    pos = {"alvo": 45.0, "stop": 36.0, "avg": 38.0, "alvoExtensoes": agent.MAX_ALVO_EXTENSOES}
    assert agent.avaliar_alvo_dinamico(45.5, pos, {"atr": PETR4_ATR}) == (None, None)


def test_avaliar_alvo_dinamico_recusa_sem_rr_minimo():
    """Alvo original já fraco (R:R 0,5:1, abaixo do Princípio 5) — a extensão
    NÃO valida um plano que já nasceu fora da doutrina."""
    pos = {"alvo": 39.0, "stop": 36.0, "avg": 38.0, "alvoExtensoes": 0}
    assert agent.avaliar_alvo_dinamico(39.1, pos, {"atr": PETR4_ATR}) == (None, None)


def test_avaliar_alvo_dinamico_sem_atr_nao_estende():
    pos = {"alvo": 45.0, "stop": 36.0, "avg": 38.0, "alvoExtensoes": 0}
    assert agent.avaliar_alvo_dinamico(45.5, pos, {}) == (None, None)
    assert agent.avaliar_alvo_dinamico(45.5, pos, None) == (None, None)


def test_alvo_dinamico_estende_duas_vezes_e_fecha_na_terceira():
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 38.0, "stop": 36.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "rules": {"alvo": True}, "alvoDinamico": True})
    snap = _snap(PETR4_REAL, PETR4_ATR)

    r1 = _run(c, {"PETR4": 45.5}, snapshot_getter=snap)
    pos = db.kv_get(c, "positions", user_id="u1")[0]
    assert pos["alvo"] == 46.45 and pos["alvoExtensoes"] == 1
    assert r1["executed"] == 0
    assert any("Alvo dinâmico" in e["text"] for e in r1["events"])

    r2 = _run(c, {"PETR4": 46.5}, snapshot_getter=snap)
    pos = db.kv_get(c, "positions", user_id="u1")[0]
    assert pos["alvo"] == 47.91 and pos["alvoExtensoes"] == 2
    assert r2["executed"] == 0

    r3 = _run(c, {"PETR4": 48.0}, snapshot_getter=snap)     # 3ª batida: limite estourado
    assert r3["executed"] == 1
    assert db.kv_get(c, "positions", user_id="u1") == []
    assert any("alvo atingido" in e["text"] for e in r3["events"])


def test_alvo_dinamico_desligado_fecha_normal_compat():
    """Compatibilidade: quem nunca ligou `alvoDinamico` continua fechando no
    alvo — a F3 não muda comportamento de quem não pediu."""
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 38.0, "stop": 36.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "rules": {"alvo": True}})
    r = _run(c, {"PETR4": 45.5}, snapshot_getter=_snap(PETR4_REAL, PETR4_ATR))
    assert r["executed"] == 1
    assert db.kv_get(c, "positions", user_id="u1") == []


def test_agent_params_default_alvo_dinamico_desligado():
    assert agent.agent_params({})["alvoDinamico"] is False
    assert agent.agent_params({"alvoDinamico": True})["alvoDinamico"] is True


def test_set_agent_grava_alvo_dinamico():
    """Guardião do bug real: o toggle da UI faz PUT /api/agent → store.set_agent
    PRECISA aceitar `alvoDinamico`, senão o clique não persiste em silêncio
    (mesma armadilha que trailingMode/serverEnabled já tiveram)."""
    c = _conn()
    store.set_agent(c, {"alvoDinamico": True}, user_id="u1")
    assert db.kv_get(c, "agent", user_id="u1")["alvoDinamico"] is True
    store.set_agent(c, {"alvoDinamico": False}, user_id="u1")
    assert db.kv_get(c, "agent", user_id="u1")["alvoDinamico"] is False


def test_kill_switch_e_janela_de_pregao():
    os.environ["B3_AGENT_KILL"] = "1"
    try:
        assert agent.kill_switch_on()
    finally:
        os.environ.pop("B3_AGENT_KILL", None)
    assert not agent.kill_switch_on()
    brt = timezone(timedelta(hours=-3))
    assert agent.in_market_hours(datetime(2026, 7, 1, 14, 0, tzinfo=brt))      # qua 14h
    assert not agent.in_market_hours(datetime(2026, 7, 4, 14, 0, tzinfo=brt))  # sábado
    assert not agent.in_market_hours(datetime(2026, 7, 1, 20, 0, tzinfo=brt))  # após pregão


def test_scheduler_uma_passada_so_usuarios_habilitados():
    c = _conn()
    _seed(c, [{"t": "EEEE3", "qty": 100, "avg": 10, "stop": 9.5}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    store.ensure_defaults(c, user_id="u2")                          # u2 SEM serverEnabled
    db.kv_set(c, "positions", [{"t": "FFFF3", "qty": 100, "avg": 10, "stop": 9.5}], user_id="u2")
    db.kv_set(c, "agent", {"autonomous": True}, user_id="u2")
    assert agent.list_server_users(c) == ["u1"]
    # qa/42: LAST_USER_RUN é estado global do módulo (gate de intervalMin) e
    # test_fase3_operador.py roda o mesmo scheduler com o mesmo uid — sem este
    # clear, o teste passa ou falha CONFORME A ORDEM da suíte.
    agent.LAST_USER_RUN.clear()
    brt_ok = datetime(2026, 7, 1, 14, 0, tzinfo=timezone(timedelta(hours=-3)))
    assert agent.in_market_hours(brt_ok)
    asyncio.run(agent.scheduler_loop(c, _quotes({"EEEE3": 9.0, "FFFF3": 9.0}), interval_s=1, once=True))
    if agent.in_market_hours():                                     # roda de fato só em horário de pregão
        assert db.kv_get(c, "positions", user_id="u1") == []
    assert len(db.kv_get(c, "positions", user_id="u2")) == 1        # u2 NUNCA é tocado pelo servidor


def test_textos_do_agente_sem_verbo_de_ordem():
    c = _conn()
    _seed(c, [{"t": "GGGG3", "qty": 100, "avg": 10, "stop": 9.5, "alvo": 12.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = _run(c, {"GGGG3": 12.5})
    todos = " ".join(e["text"].lower() for e in r["events"])
    for pat in (r"\bcompre\b", r"\bvenda\s+agora\b", r"\bentre\s+agora\b", r"\bdeve\s+comprar\b"):
        assert not re.search(pat, todos), pat


def test_status_snapshot_shape():
    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    st = agent.status_snapshot(c, interval_s=60)
    assert set(["killSwitch", "pregaoAberto", "intervaloS", "usuariosHabilitados", "ultimoCiclo", "agoraBRT"]) <= set(st)
    assert st["usuariosHabilitados"] == 1 and st["intervaloS"] == 60


def test_heartbeat_persistido_prova_laco_vivo_fora_do_pregao():
    """P2: sem heartbeat, status_snapshot não distingue vivo de morto. Antes de
    qualquer tick, lacoVivo=False; após um tick do laço (mesmo FORA do pregão),
    o heartbeat persiste e lacoVivo=True — sobrevive a deploy (é kv/SQLite)."""
    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    # nada bateu ainda → não há prova de vida
    st0 = agent.status_snapshot(c, interval_s=60)
    assert st0["heartbeat"]["lacoVivo"] is False and st0["heartbeat"]["haS"] is None
    # um tick FORA do pregão (sábado): corpo do ciclo não roda, mas o heartbeat sim
    sabado = datetime(2026, 7, 4, 14, 0, tzinfo=timezone(timedelta(hours=-3)))
    assert not agent.in_market_hours(sabado)
    agent.LAST_USER_RUN.clear()
    asyncio.run(agent.scheduler_loop(c, _quotes({}), interval_s=1, once=True))
    st1 = agent.status_snapshot(c, interval_s=60)
    assert st1["heartbeat"]["lacoVivo"] is True
    assert st1["heartbeat"]["haS"] is not None and st1["heartbeat"]["haS"] < 60
    assert st1["heartbeat"]["atBRT"]  # rótulo do último tick presente
