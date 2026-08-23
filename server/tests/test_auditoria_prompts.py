"""Auditoria dos prompts da LLM (2026-07-31) — guardiões dos aceites.

Cada teste trava uma correção da auditoria (A1-A8, M1-M5) para ela não
regredir em silêncio. Padrão: espiona `_call_llm` (como test_skill_ref) ou
afirma sobre os blocos montados — nunca chama provedor real.
"""
import asyncio

from app import agent, defaults, llm, setups, skill_ref


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


# ===== A6b (F1) — "alta" existe, gated pelo 2º timeframe REAL ===============

def test_a6_alta_gated_por_multitimeframe(monkeypatch):
    for fmt in (llm.DEEP_FORMAT, llm.PRO_DEEP_FORMAT):
        assert "baixa|moderada|alta" in fmt
        assert "multiTimeframe=true" in fmt
    seen = {}

    async def call(config, key, system, user, max_tokens):
        seen["system"] = system
        return '{"resumo":"x","planoEstudo":"Aguardar","confianca":"alta"}'
    monkeypatch.setattr(llm, "_call_llm", call)
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    # sem multi-timeframe: "alta" declarada vira o TETO "moderada" (não o
    # default "baixa" — a leitura foi forte; a lacuna é só a confirmação)
    d = asyncio.run(llm.analyze_deep({}, {}, "PETR4", {}, {"setups": []}, modo="estudo"))
    assert d["confianca"] == "moderada"
    # com multi-timeframe REAL (bloco intraday15m alimentado): "alta" sobrevive
    ctx = {"dataQuality": {"multiTimeframe": True}, "intraday15m": {"asOf": "x"}}
    d = asyncio.run(llm.analyze_deep({}, {}, "PETR4", ctx, {"setups": []}, modo="estudo"))
    assert d["confianca"] == "alta"
    # valor inválido segue caindo no default seguro

    async def call_invalida(config, key, system, user, max_tokens):
        return '{"resumo":"x","planoEstudo":"Aguardar","confianca":"altíssima"}'
    monkeypatch.setattr(llm, "_call_llm", call_invalida)
    d = asyncio.run(llm.analyze_deep({}, {}, "PETR4", ctx, {"setups": []}, modo="estudo"))
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


def test_a8iii_rr_min_fonte_unica_nos_dois_motores_e_no_front():
    """ADR-015 (06-05): o "1,5" do R:R mínimo vivia como 3 constantes Python
    independentes (skill_ref.RR_MIN, setups.RR_MINIMO, agent.RR_MINIMO) e 7
    literais no front, com um único guardião (test_a8_rr_min_fonte_unica)
    cobrindo só skill_ref. Este teste amarra os dois motores E o front à
    mesma fonte — divergiu, acusa e diz qual arquivo.
    """
    import os
    import re

    # -- os dois motores leem em runtime de skill_ref -----------------------
    assert setups.RR_MINIMO == skill_ref.RR_MIN == 1.5
    assert agent.RR_MINIMO == skill_ref.RR_MIN == 1.5

    # -- prova que é IMPORT, não um literal novo por acaso igual a 1.5 ------
    # (leitura do código-fonte, como test_a8ii_paridade_defaults_carteira_com_catalog_js
    # já faz com catalog.js — senão trocar skill_ref.RR_MIN por outro 1.5
    # hardcoded em setups.py/agent.py passaria batido)
    caminho_setups = os.path.join(os.path.dirname(__file__), "..", "app", "setups.py")
    caminho_agent = os.path.join(os.path.dirname(__file__), "..", "app", "agent.py")
    with open(caminho_setups, encoding="utf-8") as f:
        src_setups = f.read()
    with open(caminho_agent, encoding="utf-8") as f:
        src_agent = f.read()
    assert "RR_MINIMO = skill_ref.RR_MIN" in src_setups, \
        "setups.py: RR_MINIMO não importa de skill_ref (literal solto?)"
    assert "RR_MINIMO = skill_ref.RR_MIN" in src_agent, \
        "agent.py: RR_MINIMO não importa de skill_ref (literal solto?)"

    # -- ALVO_ATR_MULT é outro 1.5 (multiplicador de ATR), NÃO consolidar ---
    assert agent.ALVO_ATR_MULT == 1.5
    assert "ALVO_ATR_MULT = 1.5" in src_agent, \
        "agent.py: ALVO_ATR_MULT deixou de ser literal próprio — não amarrar a RR_MIN"

    # -- fonte única do front (finance.js) -----------------------------------
    caminho_finance = os.path.join(os.path.dirname(__file__), "..", "..",
                                   "web", "src", "finance.js")
    with open(caminho_finance, encoding="utf-8") as f:
        src_finance = f.read()
    m_num = re.search(r"RR_MIN\s*=\s*([0-9.]+)", src_finance)
    assert m_num, "web/src/finance.js: RR_MIN não encontrado no fonte"
    assert float(m_num.group(1)) == skill_ref.RR_MIN
    m_txt = re.search(r'RR_MIN_TXT\s*=\s*"([^"]+)"', src_finance)
    assert m_txt, "web/src/finance.js: RR_MIN_TXT não encontrado no fonte"
    assert m_txt.group(1) == skill_ref.RR_MIN_TXT

    # -- literais (\d,\d):1 em copy.js/App.jsx/catalog.js batem com a fonte -
    padrao = re.compile(r"\d,\d:1")
    for nome in ("copy.js", "App.jsx", "catalog.js"):
        caminho = os.path.join(os.path.dirname(__file__), "..", "..",
                               "web", "src", nome)
        with open(caminho, encoding="utf-8") as f:
            src = f.read()
        for ocorrencia in padrao.findall(src):
            assert ocorrencia == skill_ref.RR_MIN_TXT + ":1", \
                f"{nome}: '{ocorrencia}' diverge do R:R mínimo canônico ({skill_ref.RR_MIN_TXT}:1)"


# ===== A8ii — prompts de carteira compõem do canônico + paridade cliente ====

def test_a8ii_prompts_de_carteira_compoem_do_canonico():
    prompts = defaults.default_llm_prompts()
    for chave in ("carteiraStopAlvo", "carteiraStopAlvoOperador"):
        assert skill_ref.PRINCIPIOS_N3 in prompts[chave], chave
        assert skill_ref.DISCLAIMER in prompts[chave], chave
        # contrato de saída intacto (o popup parseia este array).
        # REVERSÃO DELIBERADA (10/08/2026): "null" saiu do contrato — a
        # instrução "stop/alvo como null quando operar=false" morreu. O N3
        # roda sobre posição que a pessoa JÁ carrega: a IA pode desaconselhar
        # ("operar": false é parecer), mas SEMPRE devolve os níveis de
        # proteção. Stop nunca é proibido.
        for campo in ('"ativo"', '"precoAtual"', '"stop"', '"alvo"',
                      '"explicacao"', '"operar"'):
            assert campo in prompts[chave], f"{chave}: {campo}"
        assert "como null" not in prompts[chave], \
            f"{chave}: voltou a mandar zerar stop/alvo no operar=false"
        assert "MESMO ASSIM devolva" in prompts[chave], \
            f"{chave}: perdeu a garantia de que os níveis sempre vêm"


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


def test_a8ii_paridade_defaults_skill_com_catalog_js():
    """FIX-C22 (2026-08-23): o par default_skill_text()/defaultSkillText()
    (e a versão Operador) não tinha guardião de paridade byte-exata, ao
    contrário do par carteiraStopAlvo* acima — a verificação de 2026-08-23
    achou os dois textos JÁ divergentes por completo (catalog.js carregava
    uma geração anterior, sem acentos, sem os 11 princípios e sem o Contrato
    de saída). O aparelho manda `doc.skill`/`doc.skillOperador` no CORPO da
    requisição de análise (deviceStore, ver persistence.js) — divergir aqui
    significa persona DIFERENTE no iPhone. Byte a byte: divergiu, acusa.

    O texto contém um backtick literal (`corpo`, no Contrato de saída),
    escapado como \\` no template literal de catalog.js — o regex abaixo
    trata `\\`` como par escapado (não fecha o literal) e o unescape desfaz
    isso antes de comparar com a string Python (que já traz o backtick cru).
    """
    import os
    import re
    caminho = os.path.join(os.path.dirname(__file__), "..", "..",
                           "web", "src", "catalog.js")
    with open(caminho, encoding="utf-8") as f:
        src = f.read()
    pares = {
        "SKILL_TEXT_ESTUDO": defaults.default_skill_text(),
        "SKILL_TEXT_OPERADOR": defaults.default_skill_text_operador(),
    }
    for nome, canonico in pares.items():
        m = re.search(nome + r"\s*=\s*`((?:\\.|[^`\\])*)`", src)
        assert m, f"literal de {nome} não encontrado no catalog.js"
        extraido = m.group(1).replace("\\`", "`").replace("\\\\", "\\")
        assert extraido == canonico, (
            f"{nome} (catalog.js) divergiu de defaults.py — "
            f"fonte de verdade é o servidor: mudou lá, muda no catalog.js"
        )


# ===== M3 — regra explícita de null para stop/alvo sem referência ===========

def test_m3_format_pede_null_nunca_zero():
    assert "use null (nunca 0.0" in llm.FORMAT
    assert "use null (nunca 0.0" in llm.FORMAT_PRO  # herdado na derivação


# ===== Pendência 2 (2026-08-01) — migração dos llmPrompts nunca editados ====

def test_migracao_llmprompts_default_antigo_sobe_edicao_fica(monkeypatch, tmp_path):
    import hashlib

    from app import db, store
    c = db.connect(str(tmp_path / "b3.db"))
    antigo = "DEFAULT DE GERAÇÃO ANTERIOR (nunca editado pelo usuário)"
    editado = "MEU PROMPT PERSONALIZADO — não é default de geração nenhuma"
    monkeypatch.setitem(defaults.LEGACY_PROMPT_SHA256, "carteiraStopAlvo",
                        {hashlib.sha256(antigo.encode()).hexdigest()})
    db.kv_set(c, "llmPrompts", {"carteiraStopAlvo": antigo,
                                "carteiraStopAlvoOperador": editado}, user_id="u1")
    store.ensure_defaults(c, user_id="u1")
    lp = db.kv_get(c, "llmPrompts", user_id="u1")
    novo = defaults.default_llm_prompts()
    assert lp["carteiraStopAlvo"] == novo["carteiraStopAlvo"], "default antigo tinha que subir"
    assert lp["carteiraStopAlvoOperador"] == editado, "edição do usuário é INTOCÁVEL"


def test_hashes_legados_existem_e_nao_incluem_o_default_atual():
    """Sanidade da lista de migração: não vazia e NUNCA contém a geração
    atual (senão a migração reescreveria o default vigente em loop)."""
    import hashlib
    novo = defaults.default_llm_prompts()
    for chave, hs in defaults.LEGACY_PROMPT_SHA256.items():
        assert hs, chave
        assert hashlib.sha256(novo[chave].encode()).hexdigest() not in hs, chave
