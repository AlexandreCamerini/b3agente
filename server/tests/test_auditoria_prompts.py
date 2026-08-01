"""Auditoria dos prompts da LLM (2026-07-31) — guardiões dos aceites.

Cada teste trava uma correção da auditoria (A1-A8, M1-M5) para ela não
regredir em silêncio. Padrão: espiona `_call_llm` (como test_skill_ref) ou
afirma sobre os blocos montados — nunca chama provedor real.
"""
import asyncio

from app import defaults, llm, skill_ref


def _spy(seen):
    async def call(config, key, system, user, max_tokens):
        seen["system"] = system
        seen["user"] = user
        return ('{"direcao":"Alta","conviccao":"Baixo","qualidade":"Boa",'
                '"recomendacao":"Aguardar","resumo":"x","corpo":"x",'
                '"planoEstudo":"Aguardar","confianca":"baixa",'
                '"stopSugerido":10.0,"alvoSugerido":12.0}')
    return call


# ===== A1 — perfil dimensiona risco; NÃO personaliza a recomendação =========

def test_a1_perfil_nao_ajusta_recomendacao():
    linha = llm._profile_line({"risco": "moderado"})
    assert "NAO mudam" in linha
    assert "ajuste recomendacao" not in linha
    # os cinco campos continuam presentes
    for campo in ("risco", "horizonte", "tolerancia", "objetivo", "experiencia"):
        assert campo in linha


# ===== A2b — rota legada (só candles) sobrescreve o Princípio 1 =============

def test_a2_legado_declara_ausencia_do_pacote(monkeypatch):
    seen = {}
    monkeypatch.setattr(llm, "_call_llm", _spy(seen))
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    for modo in ("estudo", "operador"):
        asyncio.run(llm.analyze({"appMode": modo}, {"text": skill_ref.PRINCIPIOS},
                                {}, {}, "PETR4", {}, {"candles": []}))
        assert "NÃO há pacote técnico pré-calculado" in seen["system"], modo
        assert "derivável aritmeticamente" in seen["system"], modo
    # M4: a mesa não pede leitura "educacional" no fecho do user prompt
    assert "educacional" not in seen["user"].splitlines()[-1]


# ===== A3 — CONTRATO_DADOS chega ao N2 e ao N3 ==============================

def test_a3_contrato_de_dados_no_n2(monkeypatch):
    seen = {}
    monkeypatch.setattr(llm, "_call_llm", _spy(seen))
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    for modo in ("estudo", "operador"):
        asyncio.run(llm.analyze_structured({}, {"text": "s"}, {}, {}, "PETR4",
                                           {"dataQuality": {"multiTimeframe": False}},
                                           modo=modo))
        assert "Qualidade dos dados" in seen["system"], modo


def test_a3_a4_contrato_e_fecho_no_n3_mesmo_com_prompt_editado(monkeypatch):
    seen = {}

    async def call(config, key, system, user, max_tokens):
        seen["system"] = system
        seen["user"] = user
        return '[{"ativo":"PETR4","precoAtual":10.0,"stop":9.0,"alvo":12.0,"explicacao":"x","operar":true}]'
    monkeypatch.setattr(llm, "_call_llm", call)
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    for modo in ("estudo", "operador"):
        asyncio.run(llm.analyze_carteira({"appMode": modo}, {}, {}, "PETR4", {},
                                         {"candles": []}, "PROMPT EDITADO PELO USUARIO"))
        # A3: camada do servidor vale sobre prompt editado
        assert "Qualidade dos dados" in seen["system"], modo
        # A4: o "Termine SEMPRE..." ganha endereço no array
        assert "FECHA a `explicacao`" in seen["system"], modo
        # M4: o fecho do user prompt pede o ARRAY (não "o JSON" de estudo)
        assert "ARRAY JSON" in seen["user"], modo


# ===== A4 — simetria: fecho canônico exigido tem endereço no contrato =======

def test_a4_fecho_canonico_tem_endereco_por_modo():
    # GUARDRAILS (edu) exige o fecho → FORMAT e DEEP_FORMAT dizem ONDE ele vai
    assert "Termine SEMPRE" in llm.GUARDRAILS
    assert "conclusoes de estudo canonicas" in llm.FORMAT          # corpo
    assert "conclusões de estudo canônicas" in llm.DEEP_FORMAT     # resumo
    # operador já tinha endereço; segue lá
    assert "Termine SEMPRE" in llm.GUARDRAILS_PRO
    assert "conclusao canonica" in llm.FORMAT_PRO
    assert "conclusão canônica" in llm.PRO_DEEP_FORMAT
    # M5: coerência decisão ↔ conclusão pedida nos dois modos do N2
    assert "COERENTE com a `recomendacao`" in llm.FORMAT
    assert "COERENTE com a `recomendacao`" in llm.FORMAT_PRO


# ===== A5 — N2 pede até 4 modelos (mesmo remédio do N1) =====================

def test_a5_n2_pede_top4_modelos_nao_cada():
    p = llm._build_structured_prompt("PETR4", {"model": "m", "modelLabel": "M"})
    assert "ATE 4 modelos MAIS RELEVANTES" in p
    assert "CADA metodologia" not in p


# ===== A6a — teto de confiança do N1 documentado (decisão provisória) =======

def test_a6_teto_de_confianca_declarado_e_imposto(monkeypatch):
    for fmt in (llm.DEEP_FORMAT, llm.PRO_DEEP_FORMAT):
        assert "PÁRA em 'moderada'" in fmt
    # enforcement: "alta" não sobrevive (vira o default seguro "baixa")
    seen = {}

    async def call(config, key, system, user, max_tokens):
        seen["system"] = system
        return '{"resumo":"x","planoEstudo":"Aguardar","confianca":"alta"}'
    monkeypatch.setattr(llm, "_call_llm", call)
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    d = asyncio.run(llm.analyze_deep({}, {}, "PETR4", {}, {"setups": []}, modo="estudo"))
    assert d["confianca"] == "baixa"


# ===== A7 — perfil SÓ no user prompt (dedup + cache não fragmenta) ==========

def test_a7_perfil_fora_do_system_em_todas_as_superficies(monkeypatch):
    perfil = {"risco": "conservador", "horizonte": "swing"}
    seen = {}
    monkeypatch.setattr(llm, "_call_llm", _spy(seen))
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    chamadas = [
        lambda: llm.analyze_structured({}, {"text": "s"}, perfil, {}, "PETR4",
                                       {"dataQuality": {}}, modo="estudo"),
        lambda: llm.analyze({}, {"text": "s"}, perfil, {}, "PETR4", {}, {"candles": []}),
        lambda: llm.analyze_deep({}, perfil, "PETR4", {}, {"setups": []}, modo="estudo"),
    ]
    for c in chamadas:
        asyncio.run(c())
        assert "Perfil do operador" not in seen["system"]
        assert "Perfil do operador" in seen["user"]

    async def call_n3(config, key, system, user, max_tokens):
        seen["system"] = system
        seen["user"] = user
        return '[{"ativo":"PETR4","stop":9.0,"alvo":12.0,"explicacao":"x","operar":true}]'
    monkeypatch.setattr(llm, "_call_llm", call_n3)
    asyncio.run(llm.analyze_carteira({}, perfil, {}, "PETR4", {}, {"candles": []}, "p"))
    assert "Perfil do operador" not in seen["system"]
    assert "Perfil do operador" in seen["user"]


# ===== A8 — R:R mínimo/ideal com fonte única ================================

def test_a8_rr_min_fonte_unica():
    assert skill_ref.RR_MIN == 1.5 and skill_ref.RR_IDEAL == 2.0
    assert skill_ref.RR_MIN_TXT == "1,5" and skill_ref.RR_IDEAL_TXT == "2"
    assert skill_ref.RR_MIN_TXT + ":1" in skill_ref.PRINCIPIOS
    prompts = defaults.default_llm_prompts()
    for chave in ("carteiraStopAlvo", "carteiraStopAlvoOperador"):
        assert skill_ref.RR_MIN_TXT + ":1" in prompts[chave], chave


# ===== A8ii — prompts de carteira compõem do canônico + paridade cliente ====

def test_a8ii_prompts_de_carteira_compoem_do_canonico():
    prompts = defaults.default_llm_prompts()
    for chave in ("carteiraStopAlvo", "carteiraStopAlvoOperador"):
        assert skill_ref.PRINCIPIOS_N3 in prompts[chave], chave
        assert skill_ref.DISCLAIMER in prompts[chave], chave
        # contrato de saída intacto (o popup parseia este array)
        for campo in ('"ativo"', '"precoAtual"', '"stop"', '"alvo"',
                      '"explicacao"', '"operar"', "null"):
            assert campo in prompts[chave], f"{chave}: {campo}"


def test_a8ii_paridade_defaults_carteira_com_catalog_js():
    """web/src/catalog.js espelha o TEXTO dos defaults do servidor (o aparelho
    monta o estado sem servidor). Byte a byte: divergiu, este teste acusa."""
    import os
    import re
    caminho = os.path.join(os.path.dirname(__file__), "..", "..",
                           "web", "src", "catalog.js")
    with open(caminho, encoding="utf-8") as f:
        src = f.read()
    prompts = defaults.default_llm_prompts()
    for chave in ("carteiraStopAlvo", "carteiraStopAlvoOperador"):
        m = re.search(chave + r":\s*`([^`]*)`", src)
        assert m, f"literal de {chave} não encontrado no catalog.js"
        assert m.group(1) == prompts[chave], f"{chave} divergiu do servidor"


# ===== M3 — regra explícita de null para stop/alvo sem referência ===========

def test_m3_format_pede_null_nunca_zero():
    assert "use null (nunca 0.0" in llm.FORMAT
    assert "use null (nunca 0.0" in llm.FORMAT_PRO  # herdado na derivação
