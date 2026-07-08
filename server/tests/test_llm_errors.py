import asyncio

from app import llm


def test_llm_test_connection_returns_actionable_missing_key():
    cfg = {"provider": "openai", "model": "gpt-4o-mini", "keySource": "manual", "apiKey": ""}
    r = asyncio.run(llm.test_connection(cfg))
    assert r["ok"] is False
    assert "chave" in r["message"].lower()
    assert r["provider"] == "openai"
    assert r["model"] == "gpt-4o-mini"
    assert r["keySource"] == "manual"
    assert "action" in r


# ===== FASE 6 (fix 2) — fallback do N1 nunca devolve blob cru ===============
def test_deep_fallback_salva_o_resumo_de_json_truncado():
    # JSON truncado no meio (causa típica: limite de tokens) — o resumo deve
    # ser recuperado LIMPO, sem chaves/aspas, e parseFalhou marcado.
    raw = '{"resumo": "IFR2 armado com pullback na média de 21.", "leituraSetups": [{"setup": "IFR'
    d = llm._deep_fallback(raw)
    assert d["resumo"] == "IFR2 armado com pullback na média de 21."
    assert d["parseFalhou"] is True
    assert d["planoEstudo"] == "Monitorar" and d["confianca"] == "baixa"


def test_deep_fallback_limpa_sintaxe_json_sem_resumo():
    raw = '```json\n{"leituraSetups": [{"setup": "PFR", "leitura": "candle de reversão no suporte"}]'
    d = llm._deep_fallback(raw)
    for proibido in ("{", "}", "[", '"', "```"):
        assert proibido not in d["resumo"], f"sintaxe JSON vazou no resumo: {proibido!r}"
    assert "PFR" in d["resumo"] and "reversão" in d["resumo"]
    assert d["parseFalhou"] is True


def test_deep_fallback_vazio_orienta_rodar_de_novo():
    d = llm._deep_fallback("")
    assert "novamente" in d["resumo"] or "incompleta" in d["resumo"]
    assert d["parseFalhou"] is True


def test_analyze_deep_json_valido_nao_marca_parse_falhou():
    # o caminho feliz continua intacto: JSON válido não passa pelo fallback
    data = llm._parse_json_loose('{"resumo": "ok", "confianca": "moderada"}')
    assert isinstance(data, dict) and "parseFalhou" not in data


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE ERROS DA LLM PASSARAM")
