"""Prova de persistencia (item 2): salvar -> recriar a conexao de banco
(simulando reinicio do servidor) -> reler -> confirmar que os valores voltaram.

Roda com pytest (`pytest`) e tambem standalone (`python -m tests.test_persistence`).
Nao depende de fixtures: cada teste cria seu proprio arquivo .db temporario.
"""
import os
import tempfile

from app import db, store


def _fresh_db():
    d = tempfile.mkdtemp(prefix="b3_test_")
    path = os.path.join(d, "b3_agente.db")
    conn = db.connect(path)
    store.ensure_defaults(conn)
    return conn, path


def test_config_persiste_apos_reinicio():
    conn, path = _fresh_db()
    store.set_config(conn, {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "baseUrl": "http://localhost:1234/v1",
        "keySource": "manual",
        "apiKey": "CHAVE-SECRETA-123",
    })
    conn.close()  # fecha a conexao = simula desligar o servidor

    conn2 = db.connect(path)  # reabre o MESMO arquivo = reinicio
    cfg = store.get(conn2, "config")
    assert cfg["provider"] == "openai"
    assert cfg["model"] == "gpt-4o-mini"
    assert cfg["baseUrl"] == "http://localhost:1234/v1"
    assert cfg["keySource"] == "manual"
    assert cfg["apiKey"] == "CHAVE-SECRETA-123"
    conn2.close()


def test_chave_nao_e_reexibida_mas_indicador_aparece():
    conn, path = _fresh_db()
    store.set_config(conn, {"keySource": "manual", "apiKey": "SEGREDO"})
    conn.close()

    conn2 = db.connect(path)
    pub = store.public_state(conn2)
    assert "apiKey" not in pub["config"]          # nunca reexpoe a chave
    assert pub["config"]["keyStored"] is True       # mas indica que esta salva
    conn2.close()


def test_watchlist_persiste_apos_reinicio():
    conn, path = _fresh_db()
    escolhidos = ["VALE3", "PETR4", "ITUB4", "WEGE3", "BPAC11"]
    store.set_watchlist(conn, escolhidos)
    conn.close()

    conn2 = db.connect(path)
    wl = store.get(conn2, "watchlist")
    # mesmos tickers (ordem segue o catalogo) e nada inventado
    assert set(wl) == set(escolhidos)
    assert all(t in store.get(conn2, "watchlist") for t in escolhidos)
    conn2.close()


def test_carteira_e_historico_persistem():
    conn, path = _fresh_db()
    store.buy(conn, "PETR4", 200, 40.0)
    conn.close()

    conn2 = db.connect(path)
    pos = [p for p in store.get(conn2, "positions") if p["t"] == "PETR4"][0]
    assert pos["qty"] >= 200
    assert store.get(conn2, "history")[0]["type"] == "COMPRA"
    conn2.close()


def test_caminho_absoluto_estavel_independe_do_cwd():
    # o caminho padrao do banco e absoluto e nao depende do diretorio atual
    p1 = db.default_db_path()
    cwd = os.getcwd()
    try:
        os.chdir(tempfile.gettempdir())
        p2 = db.default_db_path()
    finally:
        os.chdir(cwd)
    assert os.path.isabs(p1)
    assert p1 == p2


def test_analises_geradas_persistem():
    conn, path = _fresh_db()
    store.set_analysis(conn, "PETR4", {"kpis": {"direcao": "Alta", "conviccao": "Alto", "qualidade": "Boa", "recomendacao": "Comprar"}, "text": "Leitura tecnica...", "at": "23/06/2026 09:00"})
    conn.close()

    conn2 = db.connect(path)
    an = store.get(conn2, "analyses")["PETR4"]
    assert an["kpis"]["recomendacao"] == "Comprar"
    assert an["text"].startswith("Leitura")
    assert store.public_state(conn2)["analyses"]["PETR4"]["kpis"]["direcao"] == "Alta"
    conn2.close()




def test_perfil_persiste_e_valida():
    conn, path = _fresh_db()
    assert store.get(conn, "profile")["risco"] == "moderado"
    store.set_profile(conn, {"risco": "agressivo", "horizonte": "intraday", "toleranciaPerdaPct": 5, "objetivo": "renda", "experiencia": "avancado"})
    store.set_profile(conn, {"risco": "invalido"})  # ignorado
    conn.close()
    conn2 = db.connect(path)
    pf = store.get(conn2, "profile")
    assert pf["risco"] == "agressivo"
    assert pf["horizonte"] == "intraday"
    assert pf["toleranciaPerdaPct"] == 5
    assert pf["objetivo"] == "renda"
    assert pf["experiencia"] == "avancado"
    conn2.close()


def test_custom_ticker_e_watchlist():
    conn, path = _fresh_db()
    assert store.is_known(conn, "PETR4") is True
    assert store.is_known(conn, "TASA4") is False
    store.add_custom(conn, "TASA4", "Taurus")
    store.add_custom(conn, "TASA4", "Taurus")  # idempotente
    assert store.is_known(conn, "TASA4") is True
    assert store.custom_tickers(conn) == ["TASA4"]
    wl = store.set_watchlist(conn, ["PETR4", "TASA4", "XXXX9"])
    assert "TASA4" in wl and "PETR4" in wl and "XXXX9" not in wl
    conn.close()
    conn2 = db.connect(path)  # persiste apos "reinicio"
    assert store.is_known(conn2, "TASA4") is True
    pub = store.public_state(conn2)
    assert any(c["t"] == "TASA4" for c in pub["catalog"])
    assert any(c["t"] == "TASA4" for c in pub["custom"])
    conn2.close()



def test_agente_intervalo_persiste():
    conn, path = _fresh_db()
    assert store.get(conn, "agent")["intervalMin"] == 15
    store.set_agent(conn, {"autonomous": True, "intervalMin": 30})
    store.set_agent(conn, {"intervalMin": 9999})   # clamp para <=240
    conn.close()
    conn2 = db.connect(path)
    ag = store.get(conn2, "agent")
    assert ag["autonomous"] is True
    assert ag["intervalMin"] == 240
    conn2.close()



def test_orcamento_inicial_e_reset():
    conn, path = _fresh_db()
    assert store.get(conn, "config")["initialBudget"] == 10000.0
    assert store.get(conn, "cash") == 10000.0
    store.set_config(conn, {"initialBudget": 25000})
    store.set_config(conn, {"initialBudget": 5})   # clamp para >= 100
    assert store.get(conn, "config")["initialBudget"] == 100.0
    store.set_config(conn, {"initialBudget": 30000})
    store.buy(conn, "PETR4", 100, 30.0)            # mexe na carteira
    assert len(store.get(conn, "positions")) >= 1
    conn.close()
    conn2 = db.connect(path)                        # persiste apos "reinicio"
    assert store.get(conn2, "config")["initialBudget"] == 30000.0
    st = store.reset_portfolio(conn2)              # recomeca do zero
    assert st["cash"] == 30000.0 and st["positions"] == [] and st["history"] == []
    conn2.close()


def test_backfill_orcamento_em_estado_antigo():
    import app.db as db
    conn, path = _fresh_db()
    # simula config antiga sem initialBudget e caixa de 12840.5
    db.kv_set(conn, "config", {"provider": "anthropic", "model": "", "keySource": "env", "apiKey": "", "baseUrl": ""})
    db.kv_set(conn, "cash", 12840.5)
    store.ensure_defaults(conn)                     # deve preencher initialBudget com o caixa atual
    assert store.get(conn, "config")["initialBudget"] == 12840.5
    conn.close()



def test_watchlist_add_persiste_apos_reabrir():
    conn, path = _fresh_db()
    # simula o caminho do add: grava custom + watchlist (como store.add_custom/set_watchlist)
    store.add_custom(conn, "RDOR3", "Rede DOr")
    wl = store.get(conn, "watchlist")
    store.set_watchlist(conn, wl + ["RDOR3"])
    assert "RDOR3" in store.get(conn, "watchlist")
    conn.close()
    conn2 = db.connect(path)                       # "reabre o app"
    assert "RDOR3" in store.get(conn2, "watchlist")  # persistiu de verdade
    # e o ticker custom continua conhecido (aparece no catalogo publico)
    pub = store.public_state(conn2)
    assert any(c.get("t") == "RDOR3" for c in pub.get("catalog", []))
    conn2.close()


def test_onboarded_persiste():
    conn, path = _fresh_db()
    assert store.get(conn, "config")["onboarded"] is False     # 1a abertura
    store.set_config(conn, {"onboarded": True})
    conn.close()
    conn2 = db.connect(path)
    assert store.get(conn2, "config")["onboarded"] is True       # nao mostra de novo
    conn2.close()



def test_watchlist_save_preserva_custom():
    # trava o modo de falha "some ao salvar": add custom -> set_watchlist (como o
    # botao Salvar) -> reabrir -> custom continua na watchlist (etapas f/g).
    conn, path = _fresh_db()
    store.add_custom(conn, "RDOR3", "Rede DOr")
    base = store.get(conn, "watchlist")
    store.set_watchlist(conn, base + ["RDOR3"])     # salvar incluindo o custom
    assert "RDOR3" in store.get(conn, "watchlist")
    conn.close()
    conn2 = db.connect(path)                          # reabrir o app
    assert "RDOR3" in store.get(conn2, "watchlist")    # NAO sumiu
    conn2.close()



def test_snapshot_um_por_dia_sobrescreve():
    conn, path = _fresh_db()
    store.upsert_snapshot(conn, {"data": "2026-06-24", "patrimonio": 10000, "caixa": 4000, "posicoesValor": 6000})
    store.upsert_snapshot(conn, {"data": "2026-06-25", "patrimonio": 10200, "caixa": 4000, "posicoesValor": 6200})
    # reabrir no MESMO dia sobrescreve, nao duplica
    store.upsert_snapshot(conn, {"data": "2026-06-25", "patrimonio": 10350, "caixa": 4100, "posicoesValor": 6250})
    snaps = store.get(conn, "equitySnapshots")
    assert len(snaps) == 2
    assert snaps[-1]["data"] == "2026-06-25" and snaps[-1]["patrimonio"] == 10350.0
    conn.close()
    conn2 = db.connect(path)                       # persiste e relê
    snaps2 = store.public_state(conn2)["equitySnapshots"]
    assert len(snaps2) == 2 and snaps2[0]["data"] == "2026-06-24"
    conn2.close()


def test_snapshot_curva_retorno_drawdown():
    # calculo determinístico sobre uma série de exemplo
    serie = [10000, 11000, 9000, 12000]   # pico 11000 -> vale 9000 => dd ~18.18%
    retorno = (serie[-1] - serie[0]) / serie[0] * 100
    peak = serie[0]; dd = 0.0
    for v in serie:
        peak = max(peak, v)
        dd = max(dd, (peak - v) / peak * 100)
    assert round(retorno, 1) == 20.0
    assert round(dd, 1) == 18.2


def test_llm_prompts_persiste_e_extensivel():
    """FASE 2: a coleção de prompts é seedada, salva edições, aceita chaves
    novas sem mudar a interface, e sobrevive ao reinício do servidor sem
    sobrescrever o que o usuário editou."""
    conn, path = _fresh_db()
    # 1) default seedado
    ps = store.public_state(conn)
    assert "llmPrompts" in ps
    assert isinstance(ps["llmPrompts"].get("carteiraStopAlvo"), str)
    assert "educacional" in ps["llmPrompts"]["carteiraStopAlvo"].lower()
    # 2) edita + chave nova (extensibilidade)
    store.set_llm_prompts(conn, {"carteiraStopAlvo": "PROMPT EDITADO", "outroPrompt": "extra"})
    # 3) reinicia o servidor: nova conexao ao mesmo arquivo
    conn.close()
    conn2 = db.connect(path)
    store.ensure_defaults(conn2)  # backfill idempotente NAO sobrescreve editados
    ps2 = store.public_state(conn2)
    assert ps2["llmPrompts"]["carteiraStopAlvo"] == "PROMPT EDITADO"
    assert ps2["llmPrompts"]["outroPrompt"] == "extra"
    conn2.close()


def test_notif_prefs_persistem():
    """Bloqueador 1 (paridade): as preferências de notificação (config.notif)
    persistem e voltam após reinício — mesma interface que o deviceStore usa."""
    conn, path = _fresh_db()
    store.set_config(conn, {"notif": {"enabled": True, "stop": False, "variacao": False}})
    conn.close()
    conn2 = db.connect(path)
    cfg = store.public_state(conn2)["config"]
    assert cfg["notif"]["enabled"] is True
    assert cfg["notif"]["stop"] is False
    assert cfg["notif"]["variacao"] is False
    # tipos não enviados mantêm o default (True)
    assert cfg["notif"]["alvo"] is True
    conn2.close()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE PERSISTENCIA PASSARAM")
