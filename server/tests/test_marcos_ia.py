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
