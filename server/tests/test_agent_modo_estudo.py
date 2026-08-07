"""Fase A do plano (docs/plano-operador-entrada-e-modos.md) — trava
estrutural: Modo Estudo NUNCA executa ordem automática, mesmo que
`agent.mode="executar"` esteja salvo (migração incompleta, escrita por outra
via, ou o usuário simplesmente trocou de modo com o agente já configurado).

Cobre os três pontos do plano: leitura (`agent.agent_params`), escrita
(`store.set_agent`) e migração ao trocar de modo (`store.set_config`).
"""
import asyncio
import os
import tempfile

from app import agent, db, store


def _conn(app_mode="estudo"):
    d = tempfile.mkdtemp(prefix="b3_modo_estudo_")
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c, user_id="u1")
    if app_mode == "operador":
        store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                              "appMode": "operador"}, user_id="u1")
    elif app_mode is not None:
        store.set_config(c, {"appMode": app_mode}, user_id="u1")
    return c


def _quotes(prices):
    async def getter(tickers):
        return {t: {"price": prices.get(t)} for t in tickers}
    return getter


# ---------------------------------------------------------------------------
# agent_params — unidade pura (leitura)
# ---------------------------------------------------------------------------
def test_agent_params_forca_sinalizar_fora_do_operador():
    par = agent.agent_params({"mode": "executar"}, app_mode="estudo")
    assert par["mode"] == "sinalizar"


def test_agent_params_mantem_executar_em_operador():
    """Guardião: a trava não pode ter quebrado o caminho normal."""
    par = agent.agent_params({"mode": "executar"}, app_mode="operador")
    assert par["mode"] == "executar"


def test_agent_params_sem_app_mode_preserva_comportamento_antigo():
    """Compatibilidade retroativa: `app_mode=None` (o default do parâmetro) é
    o contrato para quem chama sem saber o appMode do usuário — o dado salvo
    em `ag["mode"]` decide sozinho, exatamente como antes desta entrega."""
    par = agent.agent_params({"mode": "executar"})
    assert par["mode"] == "executar"
    par2 = agent.agent_params({"mode": "executar"}, app_mode=None)
    assert par2["mode"] == "executar"


# ---------------------------------------------------------------------------
# Integração: run_cycle_for NUNCA executa em Modo Estudo.
# ---------------------------------------------------------------------------
def test_ciclo_nao_executa_em_modo_estudo_mesmo_com_mode_executar_salvo():
    c = _conn(app_mode="estudo")
    db.kv_set(c, "positions", [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0}], user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    db.kv_set(c, "agent", {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3}, user_id="u1")
    r = asyncio.run(agent.run_cycle_for(c, "u1", _quotes({"PETR4": 37.5})))
    assert r["executed"] == 0
    assert len(db.kv_get(c, "positions", user_id="u1")) == 1  # posição intacta — store.sell não rodou
    assert any(e["kind"] == "warn" and "apenas sinalizar" in e["text"] for e in r["events"])


def test_ciclo_executa_normalmente_em_modo_operador():
    """Guardião: o mesmo cenário, em Modo Operador, executa como sempre."""
    c = _conn(app_mode="operador")
    db.kv_set(c, "positions", [{"t": "PETR4", "qty": 100, "avg": 40.0, "stop": 38.0}], user_id="u1")
    db.kv_set(c, "cash", 100000.0, user_id="u1")
    db.kv_set(c, "agent", {"serverEnabled": True, "mode": "executar", "maxOpsDia": 3}, user_id="u1")
    r = asyncio.run(agent.run_cycle_for(c, "u1", _quotes({"PETR4": 37.5})))
    assert r["executed"] == 1
    assert db.kv_get(c, "positions", user_id="u1") == []


# ---------------------------------------------------------------------------
# set_agent — trava na ESCRITA.
# ---------------------------------------------------------------------------
def test_set_agent_nao_grava_executar_fora_do_operador():
    c = _conn(app_mode="estudo")
    ag = store.set_agent(c, {"mode": "executar"}, user_id="u1")
    assert ag["mode"] == "sinalizar"
    assert db.kv_get(c, "agent", user_id="u1")["mode"] == "sinalizar"


def test_set_agent_grava_executar_em_operador_e_acopla_server_enabled():
    c = _conn(app_mode="operador")
    ag = store.set_agent(c, {"mode": "executar"}, user_id="u1")
    assert ag["mode"] == "executar"
    # Acoplamento (Fase A): mode="executar" sem serverEnabled no mesmo patch
    # e sem já estar True liga serverEnabled junto — fecha o estado ambíguo
    # descrito em agent.py:486-500 (proteção que só corre com o app aberto).
    assert ag["serverEnabled"] is True


def test_set_agent_respeita_server_enabled_explicito_no_mesmo_patch():
    c = _conn(app_mode="operador")
    ag = store.set_agent(c, {"mode": "executar", "serverEnabled": False}, user_id="u1")
    assert ag["mode"] == "executar"
    assert ag["serverEnabled"] is False  # escolha explícita do mesmo request não é sobrescrita


def test_set_agent_nao_grava_autonomous_true_fora_do_operador():
    c = _conn(app_mode="estudo")
    ag = store.set_agent(c, {"autonomous": True}, user_id="u1")
    assert ag["autonomous"] is False


def test_set_agent_grava_autonomous_true_em_operador():
    c = _conn(app_mode="operador")
    ag = store.set_agent(c, {"autonomous": True}, user_id="u1")
    assert ag["autonomous"] is True


# ---------------------------------------------------------------------------
# Migração (D1): sair do Modo Operador rebaixa mode="executar" já salvo.
# ---------------------------------------------------------------------------
def test_migracao_ao_sair_do_operador_rebaixa_mode_executar():
    c = _conn(app_mode="operador")
    store.set_agent(c, {"mode": "executar"}, user_id="u1")
    assert db.kv_get(c, "agent", user_id="u1")["mode"] == "executar"
    store.set_config(c, {"appMode": "estudo"}, user_id="u1")
    assert db.kv_get(c, "agent", user_id="u1")["mode"] == "sinalizar"


def test_entrar_no_operador_nao_mexe_no_mode_sinalizar():
    """Entrar em Operador não precisa migrar nada — `set_agent` já trava a
    escrita de "executar" fora dele; o mode salvo (aqui "sinalizar", escrito
    direto no kv para isolar do que `set_agent` faria) fica intacto ao trocar
    de appMode para "operador"."""
    c = _conn(app_mode="estudo")
    db.kv_set(c, "agent", {"mode": "sinalizar"}, user_id="u1")
    store.set_config(c, {"operadorTermo": {"aceitoEm": "2026-01-01", "versao": "1"},
                          "appMode": "operador"}, user_id="u1")
    assert db.kv_get(c, "agent", user_id="u1")["mode"] == "sinalizar"
