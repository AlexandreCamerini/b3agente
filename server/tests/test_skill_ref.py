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


# --- Fase 43 (HIER-03) — reconciliação sinal técnico × histórico medido -----

def test_reconciliacao_chaves_espelhadas_nos_dois_modos():
    esperado = {"elegivel", "inelegivel", "insuficiente", "nunca_medido", "aposentado"}
    assert set(skill_ref.RECONCILIACAO_ELEGIBILIDADE["operador"]) == esperado
    assert set(skill_ref.RECONCILIACAO_ELEGIBILIDADE["educacional"]) == esperado


def test_reconciliacao_txt_operador_interpola_n_janela_expr():
    t = skill_ref.reconciliacao_elegibilidade_txt("operador", "inelegivel", n=123, janela="2024", exp_r=0.005)
    assert t == "Critérios ok · sem vantagem medida (n=123, 2024, +0,005R)"


def test_reconciliacao_txt_expr_negativo_usa_sinal_de_menos():
    t = skill_ref.reconciliacao_elegibilidade_txt("operador", "elegivel", n=80, janela="2025", exp_r=-0.099)
    assert t.endswith("−0,099R)")
    assert "-0,099R" not in t


def test_reconciliacao_txt_educacional_sem_expr():
    t = skill_ref.reconciliacao_elegibilidade_txt("educacional", "inelegivel", n=123, janela="2024", exp_r=0.005)
    assert t == "O padrão bateu os critérios, mas em 123 ocorrências na janela 2024 não houve vantagem medida."
    assert "R)" not in t


# REVERSÃO DELIBERADA (2026-09-27, Fase 43, DP-3): ausência não vira mais "?"
# no microtexto — cai para nunca_medido (resposta do Alex no checkpoint 43-05).
def test_reconciliacao_txt_ausente_cai_para_nunca_medido_nunca_zero():
    t = skill_ref.reconciliacao_elegibilidade_txt("operador", "inelegivel", n=None, janela="2024", exp_r=0.005)
    assert t == skill_ref.RECONCILIACAO_ELEGIBILIDADE["operador"]["nunca_medido"]
    assert "?" not in t

    t2 = skill_ref.reconciliacao_elegibilidade_txt("operador", "elegivel", n=80, janela="2025", exp_r=None)
    assert t2 == skill_ref.RECONCILIACAO_ELEGIBILIDADE["operador"]["nunca_medido"]
    assert "?" not in t2

    t3 = skill_ref.reconciliacao_elegibilidade_txt("educacional", "inelegivel", n=1, janela="", exp_r=0.0)
    assert t3 == skill_ref.RECONCILIACAO_ELEGIBILIDADE["educacional"]["nunca_medido"]

    t4 = skill_ref.reconciliacao_elegibilidade_txt("operador", "insuficiente", n=None, janela="2024")
    assert t4 == skill_ref.RECONCILIACAO_ELEGIBILIDADE["operador"]["nunca_medido"]

    # exp_r = 0.0 é valor presente (não cai)
    t5 = skill_ref.reconciliacao_elegibilidade_txt("operador", "elegivel", n=80, janela="2025", exp_r=0.0)
    assert "+0,000R" in t5


def test_reconciliacao_txt_n_zero_e_valor_presente():
    t = skill_ref.reconciliacao_elegibilidade_txt("operador", "insuficiente", n=0, janela="2025")
    assert t == "Critérios ok · amostra insuficiente (n=0 — pouco para medir)"


def test_reconciliacao_txt_nenhum_retorno_contem_interrogacao():
    valores_ausentes = [
        {"n": None, "janela": "2024", "exp_r": 0.005},
        {"n": 80, "janela": "", "exp_r": 0.005},
        {"n": 80, "janela": "2024", "exp_r": None},
        {"n": None, "janela": "", "exp_r": None},
        {"n": 0, "janela": "2025", "exp_r": 0.0},
    ]
    for modo in ("operador", "educacional"):
        for estado in skill_ref.RECONCILIACAO_ELEGIBILIDADE[modo]:
            for vals in valores_ausentes:
                t = skill_ref.reconciliacao_elegibilidade_txt(modo, estado, **vals)
                assert "?" not in t, f"{modo}/{estado}/{vals} -> {t!r}"


def test_reconciliacao_txt_fallback_modo_e_estado():
    assert skill_ref.reconciliacao_elegibilidade_txt("banana", "inelegivel", n=1, janela="x", exp_r=0.0) == \
        skill_ref.reconciliacao_elegibilidade_txt("educacional", "inelegivel", n=1, janela="x", exp_r=0.0)
    esperado_nunca_medido_operador = skill_ref.reconciliacao_elegibilidade_txt("operador", "nunca_medido")
    assert skill_ref.reconciliacao_elegibilidade_txt("operador", "xpto") == esperado_nunca_medido_operador
    assert skill_ref.reconciliacao_elegibilidade_txt("operador", None) == esperado_nunca_medido_operador


def test_reconciliacao_sem_verbo_de_ordem_nem_promessa():
    proibidos = ("COMPRAR", "VENDER", "COMPRE", "VENDA", "registrar entrada", "registrar saída")
    for modo, d in skill_ref.RECONCILIACAO_ELEGIBILIDADE.items():
        for v in d.values():
            assert "lucro" not in v.lower()
            assert "garant" not in v.lower()
            if modo == "educacional":
                for p in proibidos:
                    assert p not in v, f"verbo de ordem '{p}' vazou para {v!r}"


def test_reconciliacao_por_que_importa_fixa():
    assert skill_ref.RECONCILIACAO_POR_QUE_IMPORTA == "sinal técnico e histórico medido são coisas diferentes"


def test_reconciliacao_por_que_importa_rotulo_fixo():
    # Fase 47 (2026-10-06, DIDA-02): rótulo do botão sr-only da cláusula tocável.
    v = skill_ref.RECONCILIACAO_POR_QUE_IMPORTA_ROTULO
    assert v == "a expectativa matemática"
    assert "garant" not in v.lower() and "lucro" not in v.lower()


# --- Fase 44 (ESTR-06): ESTRUTURA_POSICAO -----------------------------------
import re as _re

_CHAVES_ESTRUTURA = {
    "nome_call_coberta", "nome_put_protecao", "nome_collar", "nome_fora_da_biblioteca",
    "estado_vigente", "estado_vigente_sem_data", "estado_perto_vencimento",
    "estado_exercicio_provavel", "estado_premio_indisponivel", "estado_vencida",
    "aberta_sem_proposta", "faixa_piso", "faixa_teto", "faixa_sem_piso", "faixa_sem_teto",
    "faixa_teto_parcial", "faixa_piso_sem_perda",
    "faixa_vencimentos_diferentes", "faixa_perna_sem_lastro", "faixa_sem_acoes",
    "faixa_dados_insuficientes", "descoberta_put", "stop_protegida", "resultado_incompleto",
    "acao_sem_cotacao", "resultado_dados_invalidos", "encerrar_premio_indisponivel", "encerrar_vencida", "origem_last",
}


def test_estrutura_posicao_chaves_espelhadas_e_exatas():
    op = set(skill_ref.ESTRUTURA_POSICAO["operador"])
    ed = set(skill_ref.ESTRUTURA_POSICAO["educacional"])
    assert op == ed == _CHAVES_ESTRUTURA
    # Reversão deliberada (correção WR-01/WR-02, Fase 44): 26 -> 28 chaves;
    # WR-05 acrescenta resultado_dados_invalidos (29).
    assert len(_CHAVES_ESTRUTURA) == 29


def test_estrutura_posicao_txt_estudo_degrada_para_educacional_sem_marcador_solto():
    a = skill_ref.estrutura_posicao_txt("estudo", "estado_vencida", vencimento="17/10/2026")
    b = skill_ref.estrutura_posicao_txt("educacional", "estado_vencida", vencimento="17/10/2026")
    assert a == b and "{" not in a and "17/10/2026" in a


def test_estrutura_posicao_txt_chave_desconhecida_falha_fechada():
    assert skill_ref.estrutura_posicao_txt("operador", "chave_inexistente") is None


def test_estrutura_posicao_interpolacao_com_todos_os_marcadores():
    for modo, d in skill_ref.ESTRUTURA_POSICAO.items():
        for chave, frase in d.items():
            marcadores = _re.findall(r"\{([a-zA-Z]+)\}", frase)
            out = skill_ref.estrutura_posicao_txt(modo, chave, **{m: "9" for m in marcadores})
            assert "{" not in out and "}" not in out, (modo, chave)


def test_estrutura_posicao_sem_ancoras_proibidas_e_sem_verbo_de_ordem_no_estudo():
    todas = " ".join(v for m in skill_ref.ESTRUTURA_POSICAO.values() for v in m.values())
    novas = " ".join(skill_ref.OPCOES_LASTREADAS[m][k] for m in ("operador", "educacional")
                     for k in ("sem_contrato_liquido", "sem_vencimento_elegivel", "premio_indisponivel",
                               "contrato_fora_da_cadeia", "sem_mercado"))
    for texto in (todas, novas):
        assert not _re.search(r"trava protetora|abate o custo", texto, _re.I)
    edu = " ".join(skill_ref.ESTRUTURA_POSICAO["educacional"].values())
    assert not _re.search(r"\bcomprar\b|\bvender\b", edu, _re.I)


# --- Card de posição v6 (Fase 46, CART6-06/07) --------------------------------
# Neutras (UI-SPEC "Neutras"): texto idêntico nos dois modos.
_V6_NEUTRAS = (
    "face_acao", "face_opcoes", "plano_titulo", "compras_titulo", "estado_sem_plano",
    "estado_travadas_todas", "estado_travadas_parcial", "encerrar", "atualizar",
    "sem_cenario", "conta_sem_formula", "aguardando_calculo", "piso", "teto",
    "equilibrio_rotulo", "chip_alta_forte", "cel_be", "cel_lastro", "rodape_fechar",
    # 46-UAT 2026-10-01 (G-01..G-06): chaves do card fechado rótulo/valor
    "legenda_resultado", "legenda_resultado_variacao", "legenda_resultado_estrutura", "chip_total_suspenso",
    "linha_acoes", "linha_opcoes", "linha_estrutura", "motivo_premio_indisponivel",
    "motivo_dados_incompletos", "motivo_aguardando_premio", "motivo_aguardando_cotacao", "motivo_cotacao_indisponivel",
    "chip_acoes_pm", "chip_vence", "chip_plano", "chip_estrategia_generica",
    "faixa_rot_teto", "faixa_leg_hoje",
)
_V6_PROIBIDO = r"\bcomprar\b|\bvender\b|trava protetora|abate o custo|\bgarante|\bcerto\b|\bsempre\b"


def test_cartao_posicao_rotulos_por_modo():
    from app import skill_ref as sr
    assert sr.cartao_posicao_txt("operador", "rodape_abrir") == "Detalhes e ações ▾"
    assert sr.cartao_posicao_txt("educacional", "rodape_abrir") == "Ver detalhes e aprender ▾"
    assert sr.cartao_posicao_txt("estudo", "saida") == "Simular venda"
    assert sr.cartao_posicao_txt("operador", "saida") == "Registrar saída"
    assert sr.cartao_posicao_txt("operador", "encerrar") == "Encerrar opção em Opções"


def test_cartao_posicao_interpola_e_falha_fechado():
    from app import skill_ref as sr
    assert (
        sr.cartao_posicao_txt("educacional", "estado_travadas_parcial", n="600", m="1.000", k="400")
        == "600 de 1.000 ações travadas · 400 livres"
    )
    assert sr.cartao_posicao_txt("operador", "nao_existe") is None
    assert sr.cartao_didatica_txt("chave_inexistente") is None


def test_cartao_posicao_mesmas_chaves_e_neutras_iguais():
    from app import skill_ref as sr
    op, ed = sr.CARTAO_POSICAO["operador"], sr.CARTAO_POSICAO["educacional"]
    assert set(op) == set(ed)
    for k in _V6_NEUTRAS:
        assert op[k] == ed[k], k


def test_cartao_estudo_sem_vocabulario_proibido():
    import re
    from app import skill_ref as sr
    rx = re.compile(_V6_PROIBIDO, re.I)
    for d in (sr.CARTAO_POSICAO["educacional"], sr.CARTAO_DIDATICA["educacional"]):
        for k, v in d.items():
            assert not rx.search(v), (k, v)


def test_cartao_didatica_so_educacional_e_marcadores_resolvem():
    import re
    from app import skill_ref as sr
    assert set(sr.CARTAO_DIDATICA) == {"educacional"}
    d = sr.CARTAO_DIDATICA["educacional"]
    for k, v in d.items():
        if k.startswith("paragrafo_"):
            for m in re.findall(r"\[\[([a-z_]+)\]\]", v):
                assert f"termo_{m}" in d, (k, m)
    assert sr.cartao_didatica_txt("caso_sem_piso", perdaMaxima="38.010,00") == (
        "Sem piso: se a ação fosse a zero, a perda seria de R$ 38.010,00."
    )


def test_cartao_posicao_uat_card_fechado():
    """46-UAT 2026-10-01: textos do card fechado rótulo/valor (G-01..G-06)."""
    import re
    from app import skill_ref as sr
    for modo in ("educacional", "operador"):
        t = lambda k, **kw: sr.cartao_posicao_txt(modo, k, **kw)
        assert t("linha_estrutura") == "Estrutura"
        assert t("chip_total_suspenso") == "total suspenso"
        assert t("motivo_premio_indisponivel") == "prêmio indisponível"
        assert t("motivo_aguardando_premio") == "aguardando prêmio"
        assert t("estado_travadas_todas") == "Ações travadas pela call · saída após encerrar"
        assert t("linha_opcoes", contrato="UGPAK422") == "Opções · UGPAK422"
        assert t("chip_vence", ddmm="19/11", dias="49") == "vence 19/11 · 49d"
    assert sr.cartao_posicao_txt("operador", "faixa_rot_be", v="X").startswith("◆ BE")
    assert sr.cartao_posicao_txt("educacional", "faixa_rot_be", v="X").startswith("◆ equilíbrio")
    rx = re.compile(_V6_PROIBIDO, re.I)
    for modo in ("educacional", "operador"):
        for k in _V6_NEUTRAS[-18:]:
            assert not rx.search(sr.CARTAO_POSICAO[modo][k]), (modo, k)
        assert not rx.search(sr.CARTAO_POSICAO[modo]["faixa_rot_be"])


# --- Fase 48 (2026-10-05): OPCOES_ESCADA (vocabulário do caminho B da aba Opções)
_OPC_PROIBIDO = r"garant|lucro certo|ganhe|proteção total|sem risco|100%"


def test_opcoes_escada_mesmos_modos_e_chaves():
    a = skill_ref.OPCOES_ESCADA
    assert set(a) == {"educacional", "operador"}
    assert set(a["educacional"]) == set(a["operador"])
    assert len(a["educacional"]) >= 90


def test_opcoes_escada_sem_frase_vazia():
    for modo, d in skill_ref.OPCOES_ESCADA.items():
        for k, v in d.items():
            assert isinstance(v, str) and v.strip(), (modo, k)


def test_opcoes_escada_vocabulario_proibido():
    import re
    rx = re.compile(_OPC_PROIBIDO, re.I)
    for modo, d in skill_ref.OPCOES_ESCADA.items():
        for k, v in d.items():
            assert not rx.search(v), (modo, k, v)


def test_opcoes_escada_risco_usa_pior_e_melhor_caso():
    for modo, d in skill_ref.OPCOES_ESCADA.items():
        assert "Pior caso" in d["risco_pior"] and "Pior caso" in d["risco_pior_sem_piso"], modo
        assert "Melhor caso" in d["risco_melhor"] and "Melhor caso" in d["risco_melhor_sem_teto"], modo


def test_opcoes_escada_txt_degrada_interpola_e_falha_fechada():
    assert skill_ref.opcoes_escada_txt("estudo", "acao_a", preco="38,00") == "ação a R$ 38,00"
    assert skill_ref.opcoes_escada_txt("operador", "acao_a", preco="38,00") == "ação a R$ 38,00"
    assert skill_ref.opcoes_escada_txt("operador", "nao_existe") is None


def test_opcoes_escada_sem_chave_de_ordem_parcial():
    for d in skill_ref.OPCOES_ESCADA.values():
        assert not [k for k in d if "parcial" in k.lower()]
