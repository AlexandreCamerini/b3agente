"""FASE 3 (Revisão Total) — Operador IA instrumentado: observabilidade e
controle que resolvem o timeout relatado na ativação/execução.

Cobre: status com próxima passada + histórico de passadas; ciclo com origem e
duração no Diário (agentLog); ERRO de ciclo vira log (nunca silêncio); guard
de sobreposição; scheduler alimenta o anel de passadas.
"""
import asyncio
import os
import tempfile

from app import agent, db, store


def _conn():
    d = tempfile.mkdtemp(prefix="b3_f3_")
    c = db.connect(os.path.join(d, "b3.db"))
    store.ensure_defaults(c)
    return c


def _user(c, uid="u1", positions=None, ag=None):
    store.ensure_defaults(c, user_id=uid)
    db.kv_set(c, "positions", positions or [], user_id=uid)
    db.kv_set(c, "agent", {"serverEnabled": True, **(ag or {})}, user_id=uid)
    db.kv_set(c, "agentLog", [], user_id=uid)
    return uid


async def _quotes_ok(tickers):
    return {t: {"price": 10.0, "change": 0} for t in tickers}


async def _quotes_boom(_tickers):
    raise RuntimeError("simulando rate-limit do provedor")


def test_status_tem_proxima_passada_e_historico():
    c = _conn()
    _user(c)
    st = agent.status_snapshot(c, interval_s=60)
    assert "proximaPassadaEmS" in st and "passadas" in st
    assert isinstance(st["passadas"], list)
    c.close()


def test_ciclo_grava_duracao_e_origem_no_diario():
    c = _conn()
    uid = _user(c, positions=[{"t": "PETR4", "qty": 100, "avg": 9.0, "stop": None, "alvo": None}])
    asyncio.run(agent.run_cycle_for(c, uid, _quotes_ok, origem="manual"))
    log = db.kv_get(c, "agentLog", [], user_id=uid)
    assert log, "ciclo deve registrar no Diário"
    resumo = log[-1]["text"]
    assert "manual" in resumo and "s ·" in resumo  # origem + duração
    c.close()


def test_erro_do_ciclo_vira_log_nunca_silencio():
    c = _conn()
    uid = _user(c, positions=[{"t": "PETR4", "qty": 100, "avg": 9.0, "stop": None, "alvo": None}])
    try:
        asyncio.run(agent.run_cycle_for(c, uid, _quotes_boom, origem="manual"))
        assert False, "deveria propagar o erro"
    except RuntimeError:
        pass
    log = db.kv_get(c, "agentLog", [], user_id=uid)
    assert log and log[-1]["kind"] == "error" and "rate-limit" in log[-1]["text"]
    c.close()


def test_guard_de_sobreposicao_nao_roda_dois_ciclos_do_mesmo_usuario():
    c = _conn()
    uid = _user(c, positions=[{"t": "PETR4", "qty": 100, "avg": 9.0, "stop": None, "alvo": None}])

    async def _lento(tickers):
        await asyncio.sleep(0.15)
        return {}

    async def _dois():
        a = asyncio.create_task(agent.run_cycle_for(c, uid, _lento, origem="manual"))
        await asyncio.sleep(0.02)
        b = await agent.run_cycle_for(c, uid, _lento, origem="manual")
        ra = await a
        return ra, b

    ra, rb = asyncio.run(_dois())
    assert rb.get("skipped"), "segundo ciclo simultâneo deve ser pulado"
    assert not ra.get("skipped")
    c.close()


def test_scheduler_alimenta_historico_de_passadas():
    c = _conn()
    _user(c)
    agent.RUN_HISTORY.clear()
    # qa/42: LAST_USER_RUN é estado global do módulo (gate de intervalMin por
    # usuário) e test_agent.py também roda o scheduler_loop — rodando a suíte
    # INTEIRA, o uid chegava aqui já "rodado há <15min" e era pulado
    # (usuarios=0). Passava isolado e falhava em conjunto. Não é bug de
    # produção: lá cada boot começa com o dict vazio.
    agent.LAST_USER_RUN.clear()
    # força "pregão aberto" e sem kill-switch monkeypatchando a janela
    orig = agent.in_market_hours
    agent.in_market_hours = lambda now=None: True
    try:
        asyncio.run(agent.scheduler_loop(c, _quotes_ok, interval_s=1, once=True))
    finally:
        agent.in_market_hours = orig
    assert agent.RUN_HISTORY, "passada do scheduler deve entrar no anel"
    p = agent.RUN_HISTORY[-1]
    assert "duracaoS" in p and p["usuarios"] >= 1 and isinstance(p["erros"], list)
    c.close()


def test_cotacao_ausente_gera_aviso_diagnostico():
    c = _conn()
    uid = _user(c, positions=[{"t": "XPTO9", "qty": 100, "avg": 9.0, "stop": 8.0, "alvo": 12.0}])

    async def _sem_preco(tickers):
        return {t: {"price": None, "error": "429"} for t in tickers}

    asyncio.run(agent.run_cycle_for(c, uid, _sem_preco, origem="agendado"))
    log = db.kv_get(c, "agentLog", [], user_id=uid)
    joined = " ".join(e["text"] for e in log)
    assert "SEM cotação" in joined and "XPTO9" in joined and "rate-limit" in joined
    c.close()


def test_push_send_to_user_sem_configuracao_e_diagnostico():
    """FASE 3 (observabilidade do push): send_to_user devolve um diagnóstico
    rico (não mais um int) — a causa raiz do relato do Alex era mensagens de
    erro que escondiam se o problema era 'não configurado' vs 'sem token'."""
    from app import push
    c = _conn()
    uid = _user(c)
    os.environ.pop("APNS_TEAM_ID", None)  # garante "não configurado" neste teste
    r = asyncio.run(push.send_to_user(c, uid, "t", "b"))
    assert r["sent"] == 0 and r["total"] == 0 and "não configurado" in r["detalhes"][0]
    c.close()


def test_push_sem_token_registrado():
    from app import push
    c = _conn()
    uid = _user(c)
    os.environ["APNS_TEAM_ID"] = "X"
    os.environ["APNS_KEY_ID"] = "Y"
    os.environ["APNS_AUTH_KEY"] = "-----BEGIN PRIVATE KEY-----\nZmFrZQ==\n-----END PRIVATE KEY-----"
    os.environ["APNS_TOPIC"] = "com.alexandrecamerini.bolsia"
    try:
        r = asyncio.run(push.send_to_user(c, uid, "t", "b"))
        assert r["sent"] == 0 and r["total"] == 0
    finally:
        for k in ("APNS_TEAM_ID", "APNS_KEY_ID", "APNS_AUTH_KEY", "APNS_TOPIC"):
            os.environ.pop(k, None)
    c.close()


if __name__ == "__main__":
    import sys
    fails = 0
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("ok " + name)
            except AssertionError as e:
                fails += 1
                print("FALHOU " + name + " :: " + str(e))
            except Exception as e:  # noqa: BLE001
                fails += 1
                print("ERRO " + name + " :: " + repr(e))
    print()
    print("TODOS OS TESTES DO OPERADOR F3 PASSARAM" if fails == 0 else str(fails) + " TESTE(S) FALHARAM")
    sys.exit(0 if fails == 0 else 1)
