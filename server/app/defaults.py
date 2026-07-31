"""Estado inicial (primeira execucao) e instrucoes padrao do skill.

As personas padrão COMPÕEM a metodologia da fonte canônica (`skill_ref`, fiel à
skill analise-tecnica-b3) em vez de reescrevê-la — o que muda por modo é só a
função (professor × mesa) e o vocabulário de decisão. São editáveis pelo usuário.
"""
from . import skill_ref

# Contrato de saída (mesmas CHAVES que a UI parseia) — comum aos dois modos.
# Auditoria 2026-07-31 (A7): redundância DELIBERADA com o FORMAT do llm.py —
# a skill é editável pelo usuário; se ele trocar o texto e perder este bloco,
# o FORMAT (camada do servidor) continua garantindo o contrato. Manter os dois.
_CONTRATO_SAIDA = "\n".join([
    "# Contrato de saída (OBRIGATÓRIO)",
    "Responda com UM único objeto JSON, sem texto fora dele e sem cercas de",
    "markdown. Inclua os KPIs (direcao, conviccao, qualidade, recomendacao), o",
    "campo `corpo` com a análise em MARKDOWN, as listas confirmacoes/invalidacoes/",
    "cuidados e stopSugerido/alvoSugerido. O app valida e normaliza a resposta.",
])


def default_skill_text() -> str:
    return "\n".join([
        "# Skill: Mesa B3 - Analista Técnico Educacional",
        "",
        skill_ref.PERSONA_BASE,
        "Função: papel de PROFESSOR — explique primeiro em linguagem simples, depois",
        "o termo técnico, para um investidor pessoa física. Leitura EDUCACIONAL.",
        "",
        skill_ref.PRINCIPIOS,
        "",
        "# Limite do modo ESTUDO",
        "Conteúdo EDUCACIONAL e dinheiro SIMULADO — deixe claro. Não use verbo de",
        "ordem nem a palavra 'recomendação' de investimento. Vocabulário de estudo:",
        skill_ref.decisoes_txt("educacional") + ".",
        "",
        _CONTRATO_SAIDA,
        "",
        "Seja conciso, linguagem simples antes do jargão.",
    ])


def default_skill_text_operador() -> str:
    """Skill da MESA (Modo Operador): MESMA metodologia canônica, função de mesa
    que orienta o cliente e vocabulário de decisão. Editável como a educacional."""
    return "\n".join([
        "# Skill: Mesa B3 - Operador v1",
        "",
        skill_ref.PERSONA_BASE,
        "Função: mesa de operações orientando o PRÓPRIO cliente — direto, curto e",
        "acionável: decisão, plano (entrada, stop na invalidação, alvos com R:R) e",
        "onde a tese morre.",
        "",
        skill_ref.PRINCIPIOS,
        "",
        "# Vocabulário de DECISÃO do modo MESA",
        "Decisão: " + skill_ref.decisoes_txt("operador") + ", sempre coerente com o",
        "plano determinístico do pacote. A execução é do cliente, na corretora dele;",
        "nada aqui é recomendação personalizada de investimento.",
        "",
        _CONTRATO_SAIDA,
    ])


def default_llm_prompts() -> dict:
    """FASE 2/3: coleção de prompts indexada por chave (extensível). O prompt da
    carteira analisa CADA ATIVO INDIVIDUALMENTE (saída em array por ativo) e
    mantém o enquadramento educacional (sugestão por perfil, não recomendação)."""
    return {
        "carteiraStopAlvo": (
            "Você é um analista técnico educacional da B3. Sua tarefa é analisar CADA\n"
            "ATIVO INDIVIDUALMENTE e propor, para cada um, um STOP e um ALVO.\n"
            "Base da análise:\n"
            "- Use PRIMEIRO as informações do ativo fornecidas nesta requisição (preço\n"
            "  atual, histórico e indicadores passados). NÃO invente dados que não foram\n"
            "  fornecidos.\n"
            "- Não cite notícias, resultados ou eventos que NÃO estejam nos dados\n"
            "  fornecidos; conceito geral de análise técnica é permitido se prefixado\n"
            "  com [contexto geral]. Fonte indisponível = declare a ausência.\n"
            "- Considere o PERFIL do investidor (apetite a risco, horizonte e tolerância\n"
            "  de perda por operação) como o fator que dimensiona os números.\n"
            "Cada análise é INDIVIDUAL: avalie cada ativo isoladamente. Não produza um\n"
            "número único para a carteira inteira; o stop/alvo de um ativo não influencia\n"
            "o do outro.\n"
            "Regras invioláveis:\n"
            "- Conteúdo EDUCACIONAL e dinheiro SIMULADO — deixe isso explícito.\n"
            "- A proposta é uma SUGESTÃO por perfil, NÃO recomendação de compra ou venda,\n"
            "  nem sinal de entrada.\n"
            "- NUNCA prometa lucro nem use linguagem de ganho garantido.\n"
            "- Dimensione o STOP para limitar a perda por operação conforme a tolerância\n"
            "  do perfil.\n"
            "- Defina o ALVO por uma relação risco:retorno de NO MÍNIMO "
            + skill_ref.RR_MIN_TXT + ":1; abaixo\n"
            "  disso, trate como cenário de estudo desfavorável ou use \"operar\": false.\n"
            "- Se os dados forem insuficientes ou estiverem distorcidos (baixa liquidez,\n"
            "  evento de redução de capital, etc.) ou o cenário estiver indefinido, diga\n"
            "  que o melhor é AGUARDAR / não operar — não force números.\n"
            "Para cada ativo, explique em 2 a 4 frases, em linguagem simples, o raciocínio\n"
            "por trás dos números.\n"
            "Formato de saída: retorne SOMENTE um JSON (nada fora dele), um objeto por\n"
            "ativo:\n"
            "[\n"
            "  {\n"
            '    "ativo": "PETR4",\n'
            '    "precoAtual": 38.50,\n'
            '    "stop": 36.20,\n'
            '    "alvo": 43.00,\n'
            '    "explicacao": "…2 a 4 frases…",\n'
            '    "operar": true\n'
            "  }\n"
            "]\n"
            'Quando recomendar aguardar, use "operar": false e stop/alvo como null,\n'
            'explicando o porquê em "explicacao".'
        ),
        # FASE 8B (N4) — versão MESA DE OPERAÇÕES do mesmo contrato (usada
        # quando config.appMode == "operador"). MESMO formato de saída (o popup
        # parseia o mesmo array); muda a voz, o rigor de R:R e a disciplina.
        "carteiraStopAlvoOperador": (
            "Você é a mesa de operações do cliente na B3. Sua tarefa é definir, para CADA\n"
            "ATIVO INDIVIDUALMENTE, o STOP e o ALVO da posição — números executáveis, direto\n"
            "ao ponto.\n"
            "Base da análise:\n"
            "- Use SOMENTE as informações fornecidas nesta requisição (preço atual,\n"
            "  histórico, indicadores e contexto técnico pré-calculado). NÃO invente dados.\n"
            "- O PERFIL do cliente dimensiona o risco (tolerância de perda por operação);\n"
            "  ele NÃO muda a leitura técnica.\n"
            "Regras invioláveis:\n"
            "- O STOP fica na INVALIDAÇÃO TÉCNICA da posição (suporte/resistência, extremo\n"
            "  do setup, ATR) — nunca num percentual arbitrário.\n"
            "- O ALVO precisa render relação risco:retorno de NO MÍNIMO "
            + skill_ref.RR_MIN_TXT + ":1 (ideal " + skill_ref.RR_IDEAL_TXT + ":1 ou\n"
            '  melhor). Abaixo disso, a posição não compensa: "operar": false.\n'
            "- Nunca prometa lucro nem percentual de acerto. Dados passados não garantem\n"
            "  repetição.\n"
            '- Dados insuficientes/distorcidos ou cenário indefinido => "operar": false —\n'
            "  não operar também é posição.\n"
            "- A execução é do cliente, na corretora dele; isto não é recomendação\n"
            "  personalizada de investimento.\n"
            "Para cada ativo, dê a explicação em 1 a 3 frases de mesa: nível técnico do\n"
            "stop, R:R do alvo e a condição que cancela o plano.\n"
            "Formato de saída: retorne SOMENTE um JSON (nada fora dele), um objeto por\n"
            "ativo:\n"
            "[\n"
            "  {\n"
            '    "ativo": "PETR4",\n'
            '    "precoAtual": 38.50,\n'
            '    "stop": 36.20,\n'
            '    "alvo": 43.00,\n'
            '    "explicacao": "…1 a 3 frases…",\n'
            '    "operar": true\n'
            "  }\n"
            "]\n"
            'Quando a posição não compensar, use "operar": false e stop/alvo como null,\n'
            'dizendo objetivamente o porquê em "explicacao".'
        ),
    }


def default_state() -> dict:
    return {
        "config": {
            "provider": "anthropic",   # anthropic | openai | google | local
            "model": "claude-haiku-4-5",  # padrão econômico/rápido (qa/48); sonnet-5 raciocina e é mais caro
            "keySource": "env",        # env | manual
            "apiKey": "",              # so preenchido se keySource == manual; nunca retornado
            "baseUrl": "",
            "initialBudget": 10000.0,  # orcamento SIMULADO inicial (R$); vira o caixa
            "theme": "dark",           # dark | light | system
            "userName": "",            # nome do usuario para personalizacao sobria
            "onboarded": False,        # tela de boas-vindas ja vista? (lida na init)
            "candlePeriod": "1y",      # Objetivo 4: janela de candles (1mo|3mo|6mo|1y|2y)
            "streak": {"days": 0, "last": ""},  # consistencia (dias seguidos abrindo)
            "notif": {                 # notificacoes LOCAIS de movimentos da carteira
                "enabled": False,      # mestre (pede permissao quando ligado)
                "stop": True, "alvo": True, "agente": True, "variacao": True,
            },
            # FASE 7 (F7.1) — Modo Operador
            "appMode": "estudo",       # estudo | operador (operador exige termo aceito)
            "operadorTermo": None,     # {aceitoEm, versao} registrado no aceite
            "risco": {"pctPorTrade": 1.0, "capital": None},  # sizing (capital None => usa initialBudget)
        },
        "skill": {"name": "Mesa B3 - Educacional v1", "text": default_skill_text()},
        # FASE 8B (R2): instrução do agente POR MODO, selecionável pelo nome
        "skillOperador": {"name": "Mesa B3 - Operador v1", "text": default_skill_text_operador()},
        "llmPrompts": default_llm_prompts(),
        "watchlist": ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "B3SA3"],
        "cash": 10000.0,
        "positions": [
            {"t": "PETR4", "qty": 300, "avg": 36.8, "stop": None, "alvo": None},
            {"t": "ITUB4", "qty": 200, "avg": 31.1, "stop": None, "alvo": None},
            {"t": "VALE3", "qty": 100, "avg": 63.4, "stop": None, "alvo": None},
        ],
        "history": [
            {"date": "18/06/2026 11:02", "type": "COMPRA", "t": "PETR4", "qty": 300, "price": 36.8, "pnl": None},
            {"date": "17/06/2026 10:12", "type": "COMPRA", "t": "ITUB4", "qty": 200, "price": 31.1, "pnl": None},
            {"date": "12/06/2026 09:58", "type": "COMPRA", "t": "VALE3", "qty": 100, "price": 63.4, "pnl": None},
        ],
        "agent": {
            "autonomous": False,
            "allocPct": 5,
            "intervalMin": 15,
            "events": [
                {"time": "Inicio", "kind": "info", "text": "Bem-vindo. Configure o modelo de IA na aba Config e peca uma analise na aba Mercado."}
            ],
        },
        "analyses": {},
        "equitySnapshots": [],  # Fase B1: serie diaria de patrimonio
        "profile": {
            "risco": "moderado",        # conservador | moderado | agressivo
            "horizonte": "swing",       # intraday | swing | posicao
            "toleranciaPerdaPct": 2.0,  # perda maxima aceita por operacao (%)
            "objetivo": "crescimento",  # preservacao | renda | crescimento
            "experiencia": "intermediario",  # iniciante | intermediario | avancado
        },
        "custom": [],                   # tickers adicionados pelo usuario (validados no Yahoo): [{t,n}]
    }
