"""FASE 3.5 — agente server-side com relógio e provedor FAKES."""
import asyncio
import os
import re
import tempfile
from datetime import datetime, timezone, timedelta

from app import (agent, analysis_outcomes, db, fundamentals, indicators,
                 intraday, radar_daily, store)


def _conn():
    d = tempfile.mkdtemp()
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    # Fase A (trava Modo Estudo): estes testes exercitam a EXECUÇÃO do
    # agente (mode="executar"), não a trava em si — precisam do Modo
    # Operador para o comportamento de antes desta entrega continuar valendo.
    # A trava tem suíte própria em test_agent_modo_estudo.py.
    store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"}, "appMode": "operador"}, user_id="u1")
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


def test_venda_por_stop_grava_motivo_stop_no_historico():
    """ADR15-04: o call site automático passa o motivo curto ('stop'), não o
    texto do Diário ('stop atingido')."""
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 1
    h = db.kv_get(c, "history", user_id="u1")[0]
    assert h["type"] == "VENDA" and h["motivo"] == "stop" and h["origem"] == "automatico"
    # texto do Diário continua o de sempre, não vira o valor do campo
    assert any("stop atingido" in e["text"] for e in r["events"])


def test_venda_por_alvo_grava_motivo_alvo_no_historico():
    c = _conn()
    _seed(c, [{"t": "VALE3", "qty": 100, "avg": 60.0, "stop": 55.0, "alvo": 65.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = _run(c, {"VALE3": 66.0})
    assert r["executed"] == 1
    h = db.kv_get(c, "history", user_id="u1")[0]
    assert h["type"] == "VENDA" and h["motivo"] == "alvo" and h["origem"] == "automatico"


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


# ---------------------------------------------------------------------------
# A-08 (auditoria 2026-09-10) — o ciclo não anuncia venda que não houve.
# ---------------------------------------------------------------------------
def _quotes_vendendo_no_meio(c, prices, ticker):
    """Reprodução REAL da corrida, sem stub do motor: `_run_cycle_inner` lê
    `positions` ANTES de `await quotes_getter(...)`. Vender dentro do getter
    coloca a venda concorrente exatamente no ponto de espera onde ela acontece
    em produção — a lista que o laço percorre fica velha e `store.sell`
    devolve None porque a posição já não está lá."""
    async def getter(tickers):
        store.sell(c, ticker, 39.0, user_id="u1", motivo="manual", origem="manual")
        return {t: {"price": prices.get(t)} for t in tickers}
    return getter


def test_a08_posicao_vendida_por_outro_caminho_nao_vira_venda_do_agente():
    """Antes: `executed += 1`, `_bump_ops` e evento `kind:"buy"` com "Proteção
    simulada: PETR4 vendido" rodavam mesmo com `pnl is None`. O Diário
    registrava venda inexistente e o funil de push (filtro `kind == "buy"`)
    avisava o usuário de uma operação que o motor nunca fez."""
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = asyncio.run(agent.run_cycle_for(
        c, "u1", _quotes_vendendo_no_meio(c, {"PETR4": 37.5}, "PETR4")))

    assert r["executed"] == 0, "o ciclo contou execução que não houve"
    assert [e for e in r["events"] if e.get("kind") == "buy"] == [], \
        "evento kind:'buy' emitido sem venda — é ele que o push usa como filtro"
    assert not any("vendido" in (e.get("text") or "") for e in r["events"]), \
        "o Diário afirmou ao usuário que o ativo foi vendido"
    # e o motor não foi tocado duas vezes: só a venda MANUAL está no histórico
    h = db.kv_get(c, "history", user_id="u1")
    vendas = [x for x in h if x.get("type") == "VENDA"]
    assert len(vendas) == 1 and vendas[0]["origem"] == "manual"


def test_a08_venda_fantasma_nao_consome_o_teto_diario_de_operacoes():
    """`_bump_ops` gravava `opsToday` por uma operação inexistente — o usuário
    perdia vaga do teto do dia sem nada ter sido executado."""
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    asyncio.run(agent.run_cycle_for(
        c, "u1", _quotes_vendendo_no_meio(c, {"PETR4": 37.5}, "PETR4")))
    ag = db.kv_get(c, "agent", {}, user_id="u1")
    assert int(ag.get("opsToday") or 0) == 0, "teto diário consumido por operação inexistente"


def test_a08_estado_correto_em_vez_de_silencio():
    """Princípio 9: o ciclo não pode mentir, e também não pode calar. O evento
    informativo diz o que REALMENTE aconteceu, com o motivo lido do motor
    (posição ausente), e avisa que o teto não foi debitado."""
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = asyncio.run(agent.run_cycle_for(
        c, "u1", _quotes_vendendo_no_meio(c, {"PETR4": 37.5}, "PETR4")))
    avisos = [e for e in r["events"] if e.get("kind") == "warn" and e.get("t") == "PETR4"]
    assert len(avisos) == 1, "nenhum registro do que aconteceu — silêncio também é estado errado"
    txt = avisos[0]["text"]
    assert "nenhuma venda" in txt and "já não estava na carteira" in txt
    assert "teto diário" in txt
    assert "tag" not in avisos[0], "aviso sem operação não pode carregar tag de execução"
    # o log persistente guarda o mesmo rastro
    log = db.kv_get(c, "agentLog", [], user_id="u1")
    assert any("nenhuma venda" in e["text"] for e in log)


def test_a08_recusa_por_lastro_de_call_coberta_tambem_nao_vira_venda():
    """O outro caminho em que `store.sell` devolve None (store.py:712): ações
    travadas como lastro de CALL coberta. O motor já registra a rejeição; o
    ciclo tem de reportar ESSE motivo, não inventar uma venda nem culpar uma
    posição ausente que está lá."""
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "qtyTravada": 100, "avg": 40.0,
               "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 0
    assert [e for e in r["events"] if e.get("kind") == "buy"] == []
    avisos = [e for e in r["events"] if e.get("kind") == "warn" and e.get("t") == "PETR4"]
    assert len(avisos) == 1 and "lastro de uma CALL coberta" in avisos[0]["text"]
    # a posição continua inteira — o motor não mexeu em nada
    assert db.kv_get(c, "positions", user_id="u1")[0]["qty"] == 100
    assert int(db.kv_get(c, "agent", {}, user_id="u1").get("opsToday") or 0) == 0


def test_a08_venda_real_continua_anunciada_com_resultado():
    """Contraprova: o caminho feliz não foi estreitado junto. Venda que o motor
    fez segue com `executed`, `_bump_ops`, evento `kind:"buy"`, `tag` e o
    resultado realizado no texto."""
    c = _conn()
    _seed(c, [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0, "alvo": 45.0}],
          {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3})
    r = _run(c, {"PETR4": 37.5})
    assert r["executed"] == 1
    compras = [e for e in r["events"] if e.get("kind") == "buy"]
    assert len(compras) == 1 and compras[0]["tag"] == "stop"
    assert "vendido" in compras[0]["text"] and "Resultado realizado" in compras[0]["text"]
    assert compras[0]["pnl"] is not None
    assert int(db.kv_get(c, "agent", {}, user_id="u1").get("opsToday") or 0) == 1


# ---------------------------------------------------------------------------
# 260911-axj — marcadores de job sobrevivem ao reinício do processo.
#
# Achado ao vivo no painel de administração (2026-09-11): quatro jobs apareciam
# como "NUNCA RODOU" no mesmo dia em que rodaram — o marcador de cada um era um
# dict de MÓDULO, em memória do processo, e produção reiniciou quatro vezes
# (deploys -01 a -04). "Nunca rodou" é afirmação sobre toda a história do
# sistema; o que o painel sabia era "sem registro NESTE processo".
# ---------------------------------------------------------------------------

# (nome no snapshot, dict de telemetria em memória, registro de uma execução)
_JOBS_MARCADOS = [
    (radar_daily.JOB_NOME, radar_daily.LAST_DAILY,
     {"date": "2026-09-10", "atLabel": "10/09 08:45", "duracaoS": 12.3, "erro": None}),
    (analysis_outcomes.JOB_NOME, analysis_outcomes.LAST_EVAL,
     {"date": "2026-09-10", "avaliadas": 7, "erro": None}),
    (fundamentals.JOB_NOME, fundamentals.LAST_WARM,
     {"date": "2026-09-10", "aquecidos": 42, "erro": None}),
    (intraday.JOB_NOME, intraday.LAST_PASS,
     {"at": "2026-09-10T12:00:00-03:00", "atLabel": "10/09 12:00", "duracaoS": 0.5,
      "ativos": 65, "comLacuna": 2, "erros": 0, "erro": None}),
]

# A FORMA que o portal admin lê (web-admin/src/App.jsx:118-130). Lista explícita
# de propósito: é contrato com a tela, não detalhe interno.
_FORMA_MARCADORES = {
    "radarDiario": {"date", "atLabel", "duracaoS", "erro"},
    "avaliacaoAnalises": {"date", "avaliadas", "erro"},
    "aquecimentoFundamentos": {"date", "aquecidos", "erro"},
    "intraday": {"at", "atLabel", "duracaoS", "ativos", "comLacuna", "erros", "erro"},
}


def _reinicia_processo(memoria):
    """Simula o REINÍCIO DO PROCESSO: o dict de telemetria volta ao estado de
    import (o deploy não faz mais do que isto — e era o bastante para o painel
    passar a dizer "nunca rodou")."""
    for k, v in list(memoria.items()):
        memoria[k] = 0 if isinstance(v, int) and not isinstance(v, bool) else None


def test_marcador_de_job_sobrevive_ao_reinicio_do_processo():
    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    guardados = [(mem, dict(mem)) for _n, mem, _r in _JOBS_MARCADOS]
    try:
        for nome, memoria, registro in _JOBS_MARCADOS:
            memoria.update(registro)                        # o job rodou
            assert db.marcar_job(c, nome, memoria) is True  # e anotou no kv
            _reinicia_processo(memoria)                     # deploy: memória zerada

        st = agent.status_snapshot(c, interval_s=60)
        for nome, _memoria, registro in _JOBS_MARCADOS:
            for campo, esperado in registro.items():
                assert st[nome][campo] == esperado, (nome, campo)
            # o que a tela lê para NÃO dizer "nunca rodou"
            assert st[nome].get("date") or st[nome].get("atLabel")
            assert st["jobs"]["origem"][nome] == "kv"
            assert set(st[nome]) == _FORMA_MARCADORES[nome]
    finally:
        for mem, antes in guardados:
            mem.clear()
            mem.update(antes)


def test_sem_registro_em_lugar_nenhum_nunca_rodou_continua_verdade():
    """O outro lado do mesmo achado: com banco vazio E memória vazia, "nunca
    rodou" é a única leitura honesta — e é o que a tela continua recebendo."""
    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    guardados = [(mem, dict(mem)) for _n, mem, _r in _JOBS_MARCADOS]
    try:
        for _nome, memoria, _registro in _JOBS_MARCADOS:
            _reinicia_processo(memoria)
        st = agent.status_snapshot(c, interval_s=60)
        for nome, _memoria, _registro in _JOBS_MARCADOS:
            assert not st[nome].get("date") and not st[nome].get("at")
            assert not st[nome].get("atLabel")       # a tela cai no "nunca rodou"
            assert st["jobs"]["origem"][nome] is None
    finally:
        for mem, antes in guardados:
            mem.clear()
            mem.update(antes)


def test_falha_ao_gravar_o_marcador_nao_derruba_o_job(monkeypatch):
    """O invariante que não pode quebrar: um job que falha por não conseguir
    ANOTAR que rodou é pior que o defeito que o marcador corrige. Mesmo padrão
    de `brapi_budget._persiste` ("contador é proteção, nunca derruba")."""
    import sqlite3 as _sqlite3

    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    antes = dict(radar_daily.LAST_DAILY)
    espiao = {"tentativas": 0}
    kv_set_real = db.kv_set

    def kv_set_que_levanta(conn, key, value, user_id=None):
        if key.startswith(db.JOB_MARCADOR_PREFIX):
            espiao["tentativas"] += 1
            raise _sqlite3.OperationalError("database is locked")
        return kv_set_real(conn, key, value, user_id=user_id)

    async def scan_fake(period=None, fetch=None):
        return {"period": period, "results": [], "universo": 0}

    try:
        monkeypatch.setattr(db, "kv_set", kv_set_que_levanta)
        monkeypatch.setattr(radar_daily.scanner, "run_scan", scan_fake)
        _reinicia_processo(radar_daily.LAST_DAILY)

        r = asyncio.run(radar_daily.run_daily(c, None))

        assert espiao["tentativas"] == 1           # tentou gravar o marcador
        assert r.get("results") is not None        # e o JOB CONCLUIU mesmo assim
        hoje = datetime.now(agent.BRT).date().isoformat()
        assert radar_daily.LAST_DAILY["date"] == hoje   # memória segue atualizada
        # e o snapshot segue de pé, servindo a memória deste processo
        monkeypatch.setattr(db, "kv_set", kv_set_real)
        st = agent.status_snapshot(c, interval_s=60)
        assert st["radarDiario"]["date"] == hoje
        assert st["jobs"]["origem"]["radarDiario"] == "memoria"
    finally:
        radar_daily.LAST_DAILY.clear()
        radar_daily.LAST_DAILY.update(antes)


def test_falha_ao_ler_o_marcador_nao_derruba_o_snapshot(monkeypatch):
    """Mesma regra na leitura: a observabilidade é a tela a que alguém recorre
    para diagnosticar — ela não pode ser a que cai."""
    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    antes = dict(radar_daily.LAST_DAILY)
    kv_get_real = db.kv_get

    def kv_get_que_levanta(conn, key, default=None, user_id=None):
        if key.startswith(db.JOB_MARCADOR_PREFIX):
            raise RuntimeError("kv indisponível")
        return kv_get_real(conn, key, default, user_id=user_id)

    try:
        radar_daily.LAST_DAILY.update(date="2026-09-10", atLabel="10/09 08:45")
        db.marcar_job(c, radar_daily.JOB_NOME, radar_daily.LAST_DAILY)
        _reinicia_processo(radar_daily.LAST_DAILY)
        monkeypatch.setattr(db, "kv_get", kv_get_que_levanta)

        st = agent.status_snapshot(c, interval_s=60)
        assert st["radarDiario"]["date"] is None           # degrada para "sem registro"
        assert st["jobs"]["origem"]["radarDiario"] is None
        assert set(st["radarDiario"]) == _FORMA_MARCADORES["radarDiario"]
    finally:
        radar_daily.LAST_DAILY.clear()
        radar_daily.LAST_DAILY.update(antes)


def test_marcador_persistido_por_outra_versao_nao_muda_a_forma_do_snapshot():
    """O registro do kv é PROJETADO nas chaves do dict de memória: um marcador
    gravado por outra versão do código (chave a mais, chave a menos) não vaza
    para o contrato que o portal admin lê."""
    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    antes = dict(radar_daily.LAST_DAILY)
    try:
        db.marcar_job(c, radar_daily.JOB_NOME,
                      {"date": "2026-09-10", "chaveDeOutraVersao": 1})
        _reinicia_processo(radar_daily.LAST_DAILY)
        st = agent.status_snapshot(c, interval_s=60)
        assert set(st["radarDiario"]) == _FORMA_MARCADORES["radarDiario"]
        assert st["radarDiario"]["date"] == "2026-09-10"
        assert st["radarDiario"]["atLabel"] is None   # ausente no marcador: None
    finally:
        radar_daily.LAST_DAILY.clear()
        radar_daily.LAST_DAILY.update(antes)


def test_erro_deste_processo_prevalece_sobre_o_marcador_persistido():
    """Job rodou ontem (está no kv) e falhou hoje, antes de registrar execução:
    a data vem do kv, o erro vem da memória — o erro é DESTE processo."""
    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    antes = dict(radar_daily.LAST_DAILY)
    try:
        db.marcar_job(c, radar_daily.JOB_NOME,
                      {"date": "2026-09-10", "atLabel": "10/09 08:45",
                       "duracaoS": 9.0, "erro": None})
        _reinicia_processo(radar_daily.LAST_DAILY)
        radar_daily.LAST_DAILY["erro"] = "Sem dados de mercado"
        st = agent.status_snapshot(c, interval_s=60)
        assert st["radarDiario"]["date"] == "2026-09-10"
        assert st["radarDiario"]["erro"] == "Sem dados de mercado"
    finally:
        radar_daily.LAST_DAILY.clear()
        radar_daily.LAST_DAILY.update(antes)


def test_status_snapshot_mantem_a_forma_que_o_portal_admin_le():
    """260911-axj trocou a FONTE dos quatro marcadores, não a forma. A lista
    abaixo é a do snapshot ANTES desta entrega + a chave aditiva `jobs`."""
    c = _conn()
    _seed(c, [], {"serverEnabled": True})
    st = agent.status_snapshot(c, interval_s=60)
    assert set(st) == {
        "killSwitch", "pregaoAberto", "heartbeat", "radarDiario", "avaliacaoAnalises",
        "aquecimentoFundamentos", "intraday", "pushAutomaticoFalhasHoje",
        "ordensPendentes", "intervaloS", "usuariosHabilitados", "protecaoSemOperador",
        "ultimoCiclo", "proximaPassadaEmS", "passadas", "agoraBRT",
        "jobs",   # ADITIVA (260911-axj): nenhuma chave existente mudou
    }
    for nome, chaves in _FORMA_MARCADORES.items():
        assert set(st[nome]) == chaves, nome
    # o bloco aditivo carrega o que falta para a tela distinguir "aguardando a
    # próxima janela" de "nunca rodou" — sem que o front mude agora.
    assert st["jobs"]["processoDesdeBRT"] and st["jobs"]["processoHaS"] >= 0
    assert set(st["jobs"]["origem"]) == set(_FORMA_MARCADORES)
    assert st["jobs"]["janelas"]["radarDiario"]["hhmm"] == radar_daily.janela_hhmm()
