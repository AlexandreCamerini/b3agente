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


# ===== FASE 8B (B3) — cérebro por modo (mesa × professor) ===================
def test_is_operador_le_o_modo_da_config():
    assert llm.is_operador({"appMode": "operador"}) is True
    assert llm.is_operador({"appMode": "estudo"}) is False
    assert llm.is_operador({}) is False and llm.is_operador(None) is False


def test_format_pro_troca_vocabulario_sem_trocar_contrato():
    # mesmas CHAVES do FORMAT (o app já parseia); muda só o vocabulário
    assert '"recomendacao": "COMPRAR|VENDER|AGUARDAR CONFIRMAÇÃO|NÃO OPERAR|Reduzir risco",' in llm.FORMAT_PRO
    assert "Estudar alta|Estudar baixa" not in llm.FORMAT_PRO
    assert "PLANO EDUCACIONAL" not in llm.FORMAT_PRO
    for chave in ('"direcao"', '"conviccao"', '"qualidade"', '"resumo"', '"corpo"', '"stopSugerido"', '"alvoSugerido"'):
        assert chave in llm.FORMAT_PRO, "chave do contrato sumiu no PRO: " + chave
    # M1 (auditoria 2026-07-31): o FORMAT_PRO pedia 12 E 10 linhas — o limite
    # herdado do FORMAT tem de sair; só o da mesa (10) fica.
    assert "12 linhas" not in llm.FORMAT_PRO
    assert "10 linhas" in llm.FORMAT_PRO
    # e o educacional permanece intacto
    assert '"recomendacao": "Estudar alta|Estudar baixa|Monitorar|Aguardar|Não operar|Reduzir risco",' in llm.FORMAT


def test_pro_deep_format_mantem_as_chaves_do_deep():
    import re as _re
    chaves = lambda s: set(_re.findall(r'^\s*"(\w+)":', s, _re.M))  # noqa: E731
    assert chaves(llm.PRO_DEEP_FORMAT) == chaves(llm.DEEP_FORMAT), "DeepModal renderiza as MESMAS chaves nos dois modos"
    assert "COMPRAR|VENDER|AGUARDAR CONFIRMAÇÃO|NÃO OPERAR" in llm.PRO_DEEP_FORMAT


def test_conclusoes_canonicas_da_persona():
    assert len(llm.CONCLUSOES_PRO) == 4
    assert any("vantagem estatística" in c for c in llm.CONCLUSOES_PRO)
    for c in llm.CONCLUSOES_PRO:
        assert c in llm.GUARDRAILS_PRO  # a mesa é obrigada a fechar com uma delas


def test_operador_pro_preserva_limites_regulatorios():
    txt = llm.OPERADOR_PRO + llm.GUARDRAILS_PRO
    assert "Nunca prometa lucro" in txt or "prometa lucro" in txt
    assert "NUNCA invente" in llm.OPERADOR_PRO
    assert "coerente" in llm.OPERADOR_PRO.lower()  # amarrado ao plano determinístico


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("TODOS OS TESTES DE ERROS DA LLM PASSARAM")


def test_anthropic_repete_sem_temperature_quando_deprecado(monkeypatch):
    """Regressão (achado do masstest-agentes-llm): claude-opus-4-8 responde 400
    '`temperature` is deprecated' — o backend deve repetir UMA vez sem o
    parâmetro em vez de estourar 502 e bloquear toda análise."""
    chamadas = []

    class FakeResp:
        def __init__(self, status, data):
            self.status_code = status
            self._d = data
            self.text = ""
        def json(self):
            return self._d

    class FakeClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            return False
        async def post(self, url, headers=None, json=None):
            chamadas.append(dict(json))   # snapshot: o body é mutado in-place no retry
            if "temperature" in json:
                return FakeResp(400, {"error": {"message": "`temperature` is deprecated for this model."}})
            return FakeResp(200, {"content": [{"type": "text", "text": "ok"}],
                                  "usage": {"input_tokens": 1, "output_tokens": 1}})

    monkeypatch.setattr(llm.httpx, "AsyncClient", FakeClient)
    out = asyncio.run(llm._call_anthropic(
        {"model": "claude-opus-4-8", "provider": "anthropic"}, "k", "sys", "usr", 100))
    assert out == "ok"
    assert len(chamadas) == 2                      # 1ª com temperature (400), 2ª sem
    assert "temperature" in chamadas[0] and "temperature" not in chamadas[1]


def test_cache_min_cobre_todo_modelo_anthropic_do_catalogo():
    """Gap achado ao otimizar o Modo Estudo: o listbox oferecia claude-opus-5 mas
    ele não estava em _CACHE_MIN — gateway cai no ramo 'modelo desconhecido' e NÃO
    cacheia em silêncio (paga input cheio por análise). Invariante: todo modelo
    Anthropic ofertado ao usuário tem mínimo cacheável definido."""
    from app import model_catalog
    ofertados = {m["id"] for m in model_catalog.CATALOG.get("anthropic", [])}
    faltando = ofertados - set(llm._CACHE_MIN)
    assert not faltando, f"modelos no catálogo sem _CACHE_MIN (não cacheiam): {faltando}"
