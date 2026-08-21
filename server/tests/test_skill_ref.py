"""Tema 2 — fidelidade à skill `analise-tecnica-b3` e fonte canônica única.

Trava o que o consolidação garante: (a) a metodologia vem de UM lugar
(`skill_ref`) e é a MESMA em todas as personas montadas; (b) princípios da
referência (R:R, invalidação, teto de dados) presentes; (c) contrato de dados
chega ao N1; (d) as conclusões canônicas têm fonte única.
"""
import asyncio

from app import skill_ref, llm, defaults


def test_canonico_expoe_metodologia_da_referencia():
    assert len(skill_ref.CONCLUSOES) == 4
    assert any("vantagem estatística" in c for c in skill_ref.CONCLUSOES)
    # princípios-chave da referência
    assert "1,5:1" in skill_ref.PRINCIPIOS and "INVALIDA" in skill_ref.PRINCIPIOS
    assert "confluência" in skill_ref.PRINCIPIOS
    # processo de 9 passos e contrato de dados presentes
    assert "Processo de análise" in skill_ref.PROCESSO
    assert "multiTimeframe" in skill_ref.CONTRATO_DADOS
    assert skill_ref.DISCLAIMER.strip().endswith("respeito ao plano de risco.")


def test_vocabulario_por_modo():
    assert skill_ref.decisoes_txt("operador") == \
        "'COMPRAR' | 'VENDER' | 'AGUARDAR CONFIRMAÇÃO' | 'NÃO OPERAR'"
    edu = skill_ref.decisoes_txt("educacional")
    assert "Estudar alta" in edu and "COMPRAR" not in edu
    assert skill_ref.vocab["educacional"]["proibe_verbo_ordem"] is True
    assert skill_ref.vocab["operador"]["proibe_verbo_ordem"] is False


def test_fonte_unica_todas_as_personas_derivam_do_canonico():
    """A metodologia (PRINCIPIOS) aparece nas QUATRO superfícies de persona —
    prova que não há mais tríplice divergência: todas compõem do mesmo bloco."""
    personas = [
        llm.OPERADOR_EDUCACIONAL,
        llm.OPERADOR_PRO,
        defaults.default_skill_text(),
        defaults.default_skill_text_operador(),
    ]
    for p in personas:
        assert skill_ref.PRINCIPIOS in p, "persona não deriva do canônico"


def test_rr_e_invalidacao_em_todos_os_modos():
    """R:R (lacuna fechada) e invalidação da referência valem em estudo e mesa."""
    for p in (llm.OPERADOR_EDUCACIONAL, llm.OPERADOR_PRO):
        assert "1,5:1" in p            # R:R mínimo — antes faltava no N1 operador
        assert "INVALIDA" in p


def test_conclusoes_canonicas_fonte_unica():
    assert llm.CONCLUSOES_PRO is skill_ref.CONCLUSOES
    for c in skill_ref.CONCLUSOES:
        assert c in llm.GUARDRAILS_PRO  # a mesa fecha com uma delas


def test_educacional_nao_ganha_verbo_de_ordem_da_referencia():
    """A referência decide comprar/vender; o modo ESTUDO mantém o guardrail:
    o vocabulário de decisão do educacional não vira COMPRAR/VENDER."""
    edu = llm.OPERADOR_EDUCACIONAL
    assert "Estudar alta" in edu and "Estudar baixa" in edu
    assert "COMPRAR" not in edu and "VENDER" not in edu


def test_opcao_b_estudo_assertivo():
    """Opção B: o modo Estudo fecha com veredito canônico (assertivo) e ganha a
    diretriz de assertividade — SEM verbo de ordem nem 'recomendação'."""
    assert len(skill_ref.CONCLUSOES_EDU) == 4
    for c in skill_ref.CONCLUSOES_EDU:
        assert "compr" not in c.lower() and "venda" not in c.lower()
    # conclusões de estudo obrigatórias no guardrail educacional
    for c in skill_ref.CONCLUSOES_EDU:
        assert c in llm.GUARDRAILS
    # assertividade presente nos dois modos
    assert skill_ref.ASSERTIVIDADE in llm.OPERADOR_EDUCACIONAL
    assert skill_ref.ASSERTIVIDADE in llm.OPERADOR_PRO


def test_doutrina_fundamental_e_fonte_unica():
    """A doutrina fundamental está no canônico e fundamentals.py deriva dela —
    mudar o threshold num lugar só muda o score (sem números mágicos soltos)."""
    from app import fundamentals
    assert fundamentals.MIN_PILARES is skill_ref.FUND_MIN_PILARES
    assert "Análise fundamental" in skill_ref.FUNDAMENTOS
    assert "FILTRO DE QUALIDADE" in skill_ref.FUNDAMENTOS
    # comportamento preservado: A exige >=2 pilares bons
    forte = {"pl": 10, "roe": 0.20, "margemLiquida": 0.15, "dividaEbitda": 1.0}
    assert fundamentals.score_fundamento(forte) == "A"
    fraco = {"pl": 50, "roe": 0.01, "margemLiquida": -0.1, "dividaEbitda": 8.0}
    assert fundamentals.score_fundamento(fraco) == "C"
    assert fundamentals.score_fundamento({"pl": 10}) is None  # 1 pilar → sem score


def test_contrato_de_dados_chega_ao_n1(monkeypatch):
    """N1 (analyze_deep) recebe o pacote completo → o contrato de dados
    (defasagem/volume/multi-timeframe) tem de estar no system, nos dois modos."""
    seen = {}

    async def spy(config, key, system, user, max_tokens):
        seen["system"] = system
        return '{"resumo":"x","planoEstudo":"Aguardar","confianca":"baixa"}'
    monkeypatch.setattr(llm, "_call_llm", spy)
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    for modo in ("operador", "estudo"):
        asyncio.run(llm.analyze_deep({"appMode": modo}, {}, "PETR4",
                                     {"snapshotId": "s1"}, {"setups": []}, modo=modo))
        assert "multiTimeframe" in seen["system"]  # CONTRATO_DADOS presente


def test_didatica_so_no_estudo_e_ensina_correlacao():
    """Feature didática (objetivo do produto): o modo Estudo ensina a cadeia
    indicador→correlação→decisão; a mesa (operador) NÃO recebe a diretriz."""
    assert "DIVERGEM" in skill_ref.DIDATICA and "confluenciaEntreFamilias" in skill_ref.DIDATICA
    assert skill_ref.DIDATICA in llm.OPERADOR_EDUCACIONAL          # N1 estudo
    assert skill_ref.DIDATICA not in llm.OPERADOR_PRO              # mesa não ensina, decide
    # sem verbo de ordem (o guardião varre via OPERADOR_EDUCACIONAL, mas trava aqui também)
    low = skill_ref.DIDATICA.lower()
    assert "compre" not in low and "venda agora" not in low


def test_didatica_no_system_do_estudo_nao_do_operador(monkeypatch):
    """O caminho legado /api/analyze leva DIDATICA no Estudo e não no Operador."""
    import asyncio
    seen = {}

    async def spy(config, key, system, user, max_tokens):
        seen[config.get("appMode")] = system
        return '{"direcao":"Alta","recomendacao":"Estudar alta","corpo":"x"}'
    monkeypatch.setattr(llm, "_call_llm", spy)
    monkeypatch.setattr(llm, "resolve_key", lambda cfg: "k")
    asyncio.run(llm.analyze({"appMode": "estudo"}, {"text": "s"}, {}, {}, "PETR4", {}, {"candles": []}))
    asyncio.run(llm.analyze({"appMode": "operador"}, {"text": "s"}, {}, {}, "PETR4", {}, {"candles": []}))
    assert skill_ref.DIDATICA in seen["estudo"]
    assert skill_ref.DIDATICA not in seen["operador"]


# --- ADR-017 Bloco 3 — vocabulário do histórico medido por setup ------------

def test_historico_chaves_espelhadas_nos_dois_modos():
    esperado = {"elegivel", "inelegivel", "insuficiente", "nunca_medido", "aposentado", "desatualizado"}
    assert set(skill_ref.HISTORICO["operador"]) == esperado
    assert set(skill_ref.HISTORICO["educacional"]) == esperado


def test_historico_rotulo_chaves_espelhadas_sem_desatualizado():
    esperado = {"elegivel", "inelegivel", "insuficiente", "nunca_medido", "aposentado"}
    assert set(skill_ref.HISTORICO_ROTULO["operador"]) == esperado
    assert set(skill_ref.HISTORICO_ROTULO["educacional"]) == esperado


def test_entrada_auto_chaves_espelhadas_nos_dois_modos():
    esperado = {"regra", "contraste", "por_setup_disponivel", "por_setup_bloqueado"}
    assert set(skill_ref.ENTRADA_AUTO["operador"]) == esperado
    assert set(skill_ref.ENTRADA_AUTO["educacional"]) == esperado


def test_entrada_auto_placeholders_literais():
    for modo in ("operador", "educacional"):
        disp = skill_ref.ENTRADA_AUTO[modo]["por_setup_disponivel"]
        bloq = skill_ref.ENTRADA_AUTO[modo]["por_setup_bloqueado"]
        assert "{setup}" in disp and "{janelaRef}" in disp
        assert "{setup}" in bloq and "{janelaRef}" not in bloq


def test_entrada_auto_txt_interpola_disponivel():
    t = skill_ref.entrada_auto_txt("operador", "disponivel", setup="IFR2 (alta)", janela_ref="2025")
    assert "IFR2 (alta)" in t and "2025" in t and "{" not in t


def test_entrada_auto_txt_falha_fechada_em_estado_desconhecido_vazio_ou_none():
    esperado = skill_ref.ENTRADA_AUTO["operador"]["por_setup_bloqueado"].replace("{setup}", "X")
    assert skill_ref.entrada_auto_txt("operador", "xpto", setup="X") == esperado
    assert skill_ref.entrada_auto_txt("operador", "", setup="X") == esperado
    assert skill_ref.entrada_auto_txt("operador", None, setup="X") == esperado


def test_entrada_auto_contraste_tem_os_dois_numeros_juntos():
    for modo in ("operador", "educacional"):
        t = skill_ref.ENTRADA_AUTO[modo]["contraste"]
        assert "−0,099R" in t and "+0,005R" in t


def test_historico_txt_interpola_janela_e_medido_ate():
    t1 = skill_ref.historico_txt("operador", "elegivel", janela="2025")
    assert "2025" in t1 and "{janela}" not in t1
    t2 = skill_ref.historico_txt("operador", "desatualizado", medido_ate="2026-08-19")
    assert "2026-08-19" in t2 and "{medidoAte}" not in t2


def test_historico_txt_fallback_modo_e_estado_desconhecidos():
    assert skill_ref.historico_txt("banana", "elegivel", janela="2025") == \
        skill_ref.historico_txt("educacional", "elegivel", janela="2025")
    assert skill_ref.historico_txt("operador", "xpto") == skill_ref.HISTORICO["operador"]["nunca_medido"]
    assert skill_ref.historico_txt("operador", None) == skill_ref.HISTORICO["operador"]["nunca_medido"]


def test_historico_educacional_sem_verbo_de_ordem():
    proibidos = ("COMPRAR", "VENDER", "COMPRE", "VENDA", "registrar entrada", "registrar saída")
    for d in (skill_ref.HISTORICO["educacional"], skill_ref.HISTORICO_ROTULO["educacional"], skill_ref.ENTRADA_AUTO["educacional"]):
        for v in d.values():
            for p in proibidos:
                assert p not in v, f"verbo de ordem '{p}' vazou para {v!r}"
