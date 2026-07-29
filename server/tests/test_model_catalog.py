"""qa/49 (pedido do Alex) — CATÁLOGO de modelos + parâmetros aceitos. Fonte única
no servidor; a UI consome via /api/ai/models e o llm.py aplica. Guardião: specs
coerentes, defaults por-modelo respeitados, modelo desconhecido cai em default
permissivo, e o endpoint devolve o catálogo.
"""
from app import model_catalog as mc
from app import llm


def test_todo_modelo_tem_campos_obrigatorios():
    for provider, modelos in mc.CATALOG.items():
        for m in modelos:
            assert set(m) >= {"id", "label", "tier", "temperature", "tempMax", "maxTokens", "maxTokensCap", "thinking"}, (provider, m)
            assert isinstance(m["temperature"], bool)
            assert isinstance(m["thinking"], bool)
            assert m["maxTokens"] >= 1
            assert m["maxTokensCap"] >= m["maxTokens"]  # o teto máximo nunca corta o default
            assert 0 < m["tempMax"] <= 2.0


def test_anthropic_tem_teto_de_temperatura_1():
    for m in mc.CATALOG["anthropic"]:
        assert m["tempMax"] == 1.0, m["id"]  # #2: Anthropic recusa temperature > 1


def test_modelos_que_raciocinam_recusam_temperature_e_tem_folga():
    # regra de coerência: se raciocina, temperature=False e teto = folga
    for provider, modelos in mc.CATALOG.items():
        for m in modelos:
            if m["thinking"]:
                assert m["temperature"] is False, m["id"]
                assert m["maxTokens"] >= mc.FOLGA_RACIOCINIO, m["id"]


def test_spec_modelo_conhecido_e_desconhecido():
    sp = mc.spec("anthropic", "claude-sonnet-5")
    assert sp["temperature"] is False and sp["thinking"] is True
    # desconhecido → default permissivo (aceita temperature; não trava)
    d = mc.spec("anthropic", "modelo-inexistente-xyz")
    assert d["temperature"] is True and d["tier"] == "Personalizado"
    # provedor sem catálogo (local) → também default
    assert mc.spec("local", "qualquer")["temperature"] is True


def test_params_efetivos_respeita_catalogo_e_usuario():
    # modelo que raciocina: temperatura omitida (None), teto sobe p/ a folga
    t, mt = llm._params_efetivos({"provider": "anthropic", "model": "claude-sonnet-5"}, 1800)
    assert t is None and mt >= mc.FOLGA_RACIOCINIO
    # modelo rápido: usa temperatura default do sistema
    t2, _ = llm._params_efetivos({"provider": "anthropic", "model": "claude-haiku-4-5"}, 1800)
    assert t2 == llm.LLM_TEMPERATURE
    # usuário sobrepõe temperatura (aceita) e sobe o teto
    t3, mt3 = llm._params_efetivos(
        {"provider": "openai", "model": "gpt-4o-mini", "temperature": 0.7, "maxTokens": 12000}, 1300)
    assert t3 == 0.7 and mt3 == 12000
    # usuário NÃO consegue starvar a saída abaixo do necessário da chamada
    _, mt4 = llm._params_efetivos(
        {"provider": "openai", "model": "gpt-4o-mini", "maxTokens": 100}, 1300)
    assert mt4 >= 1300
    # #2: temperatura clampada ao teto do provedor (Anthropic → 1.0)
    t5, _ = llm._params_efetivos(
        {"provider": "anthropic", "model": "claude-haiku-4-5", "temperature": 1.8}, 1800)
    assert t5 == 1.0
    # #3: teto de saída clampado ao maxTokensCap do modelo (haiku → 8192)
    _, mt6 = llm._params_efetivos(
        {"provider": "anthropic", "model": "claude-haiku-4-5", "maxTokens": 999999}, 1800)
    assert mt6 == 8192


def test_store_persiste_e_limpa_parametros(tmp_path):
    from app import db, store
    conn = db.connect(str(tmp_path / "b3.db"))
    # grava temperatura e teto (clampados)
    store.set_config(conn, {"model": "claude-haiku-4-5", "temperature": 0.7, "maxTokens": 12000})
    cfg = store.get(conn, "config")
    assert cfg["temperature"] == 0.7 and cfg["maxTokens"] == 12000
    # clamp: valores fora do range são limitados, não rejeitados
    store.set_config(conn, {"temperature": 9, "maxTokens": 10})
    cfg = store.get(conn, "config")
    assert cfg["temperature"] == 2.0 and cfg["maxTokens"] == 256
    # null limpa (volta ao default do catálogo)
    store.set_config(conn, {"temperature": None, "maxTokens": None})
    cfg = store.get(conn, "config")
    assert "temperature" not in cfg and "maxTokens" not in cfg


def test_endpoint_ai_models():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.get("/api/ai/models")
    assert r.status_code == 200
    j = r.json()
    assert "catalog" in j and "anthropic" in j["catalog"]
    assert any(m["id"] == "claude-haiku-4-5" for m in j["catalog"]["anthropic"])
    assert isinstance(j["temperatureDefault"], (int, float))
