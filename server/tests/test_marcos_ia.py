"""Fase 50 (50-07) — D-10/D-18: a IA explica os marcos do motor; nenhum número
dela vira proposta aplicável e ela não recebe número concorrente."""
from app import kpi, llm


def test_format_sem_stop_alvo_da_ia():
    for fmt in (llm.FORMAT, llm.FORMAT_PRO):
        assert "stopSugerido" not in fmt and "alvoSugerido" not in fmt
        assert "MARCOS DO MOTOR" in fmt


def test_parse_carteira_legado_descarta_numeros():
    raw = ('[{"ativo":"PETR4","precoAtual":100.0,"stop":95.0,"alvo":105.0,'
           '"explicacao":"x","operar":false,'
           '"cenarios":[{"perfil":"moderado","stop":95.0,"alvo":105.0}]}]')
    r = llm.parse_carteira(raw, "PETR4")
    assert r["proposal"] is None
    assert r["numerosIaDescartados"] is True
    assert r["operar"] is False          # parecer preservado, nunca veto
    assert "cenarios" not in r


def test_parse_carteira_novo_formato_nao_marca_descarte():
    raw = '[{"ativo":"PETR4","operar":true,"explicacao":"e","riscos":["r"],"quandoRevisar":"q"}]'
    r = llm.parse_carteira(raw, "PETR4")
    assert r["numerosIaDescartados"] is False
    assert r["riscos"] == ["r"] and r["quandoRevisar"] == "q"


def test_parse_rich_ignora_stop_alvo_da_ia():
    r = kpi.parse_rich('{"recomendacao":"Estudar alta","corpo":"x",'
                       '"stopSugerido":36.0,"alvoSugerido":43.0}')
    assert r["proposal"] == {"stop": None, "alvo": None}


# ---- Task 2 (D-18): a IA nao le numero concorrente ao dos marcos -------------

def test_compact_setups_sem_alvo_sugerido():
    from app import technical_snapshot
    sres = {"setups": [{"nome": "S", "lado": "compra", "alvoSugerido": 12.3, "invalidacao": "x"}]}
    out = technical_snapshot._compact_setups(sres)
    assert out and "alvoSugerido" not in out[0] and out[0]["invalidacao"] == "x"


def test_technical_models_sem_risk_plan_reference():
    import inspect
    from app import technical_models
    assert "riskPlanReference" not in inspect.getsource(technical_models)


# ---- Task 3 (D-10): prompts default e hashes legados -------------------------

def test_prompts_default_explicam_marcos_do_motor():
    import hashlib
    from app import defaults
    prompts = defaults.default_llm_prompts()
    for chave, texto in prompts.items():
        assert "MARCOS DO MOTOR" in texto, chave
        assert "stopSugerido" not in texto
        h = hashlib.sha256(texto.encode()).hexdigest()
        assert h not in defaults.LEGACY_PROMPT_SHA256[chave], "default atual nao pode ser legado"
    # geracao anterior (Fase 50 D-10 trocou o texto) entrou como legada
    assert "3ccfd9c582895c9230478cb2ec535526a0728dd7a746b454ce7450ce8be750b7" in defaults.LEGACY_PROMPT_SHA256["carteiraStopAlvo"]
    assert "a470ed3bf1b1953aa9786cffd515e404a7d2bc6de81c29af87de7ada25eb369a" in defaults.LEGACY_PROMPT_SHA256["carteiraStopAlvoOperador"]


# ---- Task 4 (D-10): rotas N2/N3 devolvem os marcos do motor -------------------

import importlib
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

_CFG = {"provider": "anthropic", "model": "claude-haiku-4-5", "keySource": "env",
        "appMode": "operador", "candlePeriod": "6mo"}


def _candles(n=120):
    out = []
    for i in range(n):
        base = 10 + i * 0.08
        out.append({"date": f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}", "open": base,
                    "high": base + 0.4, "low": base - 0.3, "close": base + 0.1, "volume": 1000 + i})
    return out


@pytest.fixture
def rota(monkeypatch):
    from app import agent, brapi_budget, managed, technical_snapshot
    brapi_budget.reset(); agent.reset_kill_switch_cache(); managed.reset_cache()
    original = sys.modules.get("app.main")
    d = tempfile.mkdtemp(prefix="b3_marcos_ia_")
    monkeypatch.setenv("B3_DB_PATH", os.path.join(d, "b3.db"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-teste")
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    technical_snapshot.reset()

    async def _quote(t):
        return {"t": t, "price": 19.62, "change": 0.1, "source": "brapi"}

    async def _hist(t, rng=None):
        return {"candles": _candles(), "currency": "BRL"}
    monkeypatch.setattr(main.candle_provider, "get_quote", _quote)
    monkeypatch.setattr(main.candle_provider, "get_history", _hist)
    yield TestClient(main.app), main
    technical_snapshot.reset(); brapi_budget.reset(); agent.reset_kill_switch_cache(); managed.reset_cache()
    if original is not None:
        sys.modules["app.main"] = original
    else:
        sys.modules.pop("app.main", None)


def test_n3_proposal_e_do_motor_nunca_da_ia(rota, monkeypatch):
    c, main = rota
    visto = {}
    # (review WR-01: o stub aceita o `avg` novo da rota)
    # marcos validos fixos: a serie sintetica faz o motor real recusar (R:R baixo)
    monkeypatch.setattr(main.marcos_servico, "marcos_para_posicao",
                        lambda snap, preco, avg=None: {"valido": True, "motivo": "", "stop": 18.4, "alvo": 21.4, "rr": 2.0})

    async def _ia(config, profile, account, t, quote, history, prompt, tech_context=None):
        visto["ctx"] = tech_context
        # LLM "maliciosa" (prompt salvo antigo): numero absurdo + parecer operar:false
        return {"proposal": {"stop": 1.0, "alvo": 999.0}, "explicacao": "x", "operar": False,
                "numerosIaDescartados": False}
    monkeypatch.setattr(main.llm, "analyze_carteira", _ia)
    r = c.post("/api/carteira-stopalvo/BRAP4", json={"config": dict(_CFG)})
    assert r.status_code == 200, r.text
    j = r.json()
    ctx = visto["ctx"]
    assert "referencias" not in ctx and "riskPlanReference" not in ctx
    assert ctx["marcosMotor"] is not None
    assert j["proposalOrigem"] == "motor" and j["operar"] is False   # parecer preservado
    marcos = j["marcos"]
    if marcos["valido"]:
        assert j["proposal"] == {"stop": marcos["stop"], "alvo": marcos["alvo"]}
    else:
        assert j["proposal"] is None
    assert j["proposal"] != {"stop": 1.0, "alvo": 999.0}
    assert marcos["valido"] is True and j["proposal"] == {"stop": 18.4, "alvo": 21.4}
    assert j["iaExplica"]


def test_n3_sem_snapshot_proposal_none(rota, monkeypatch):
    c, main = rota

    async def _falha(*_a, **_k):
        raise ValueError("sem historico")
    monkeypatch.setattr(main.technical_snapshot, "get", _falha)

    async def _ia(config, profile, account, t, quote, history, prompt, tech_context=None):
        return {"proposal": {"stop": 1.0, "alvo": 999.0}, "explicacao": "x", "operar": True}
    monkeypatch.setattr(main.llm, "analyze_carteira", _ia)
    j = c.post("/api/carteira-stopalvo/BRAP4", json={"config": dict(_CFG)}).json()
    assert j["proposal"] is None and j["marcos"] is None


def test_n2_proposal_e_do_motor_e_ia_recebe_marcos(rota, monkeypatch):
    c, main = rota
    visto = {}

    async def _ia(config, skill, profile, account, t, context, modo=None):
        visto["ctx"] = context
        return {"kpis": {"conviccao": "Médio", "recomendacao": "COMPRAR"}, "detail": {},
                "proposal": {"stop": 1.0, "alvo": 999.0}, "markdown": "m", "text": "t"}
    monkeypatch.setattr(main.llm, "analyze_structured", _ia)
    r = c.post("/api/technical/analyze/BRAP4", json={"config": dict(_CFG), "skill": {"text": "s"}})
    assert r.status_code == 200, r.text
    j = r.json()
    assert "riskPlanReference" not in visto["ctx"] and "marcosMotor" in visto["ctx"]
    assert j["proposalOrigem"] == "motor"
    assert j["proposal"] != {"stop": 1.0, "alvo": 999.0}
    if j["marcos"]["valido"]:
        assert j["proposal"] == {"stop": j["marcos"]["stop"], "alvo": j["marcos"]["alvo"]}
