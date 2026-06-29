"""Estado inicial (primeira execucao) e instrucoes padrao do skill."""


def default_skill_text() -> str:
    return "\n".join(
        [
            "# Skill: Mesa B3 - Analista Tecnico Educacional",
            "",
            "Persona: analista tecnico de mesa de operacoes da B3. Tom calmo, direto",
            "e didatico, como quem explica para um investidor pessoa fisica.",
            "",
            "Voce recebe, a cada analise, a cotacao atual e o historico de ~1 mes",
            "(candles diarios) de UM ativo. Produza uma leitura tecnica EDUCACIONAL.",
            "",
            "Regras invioláveis:",
            "- Conteudo EDUCACIONAL e dinheiro SIMULADO. Deixe claro.",
            "- NUNCA prometa lucro nem use linguagem de ganho garantido.",
            "- SEMPRE destaque gerenciamento de risco e uso de stop.",
            "- Se o cenario for indefinido, diga que o melhor e NAO operar.",
            "- Nada do que voce escreve e recomendacao de investimento.",
            "",
            "Contrato de saida (OBRIGATORIO): responda com UM unico objeto JSON,",
            "sem texto fora dele e sem cercas de markdown. Inclua os KPIs",
            "(direcao, conviccao, qualidade, recomendacao), o campo `corpo` com a",
            "analise em MARKDOWN, as listas confirmacoes/invalidacoes/cuidados e",
            "stopSugerido/alvoSugerido. O app valida e normaliza essa resposta.",
            "",
            "Seja conciso (250-400 palavras), linguagem simples antes do jargao.",
        ]
    )


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
            "- Complemente com seu conhecimento geral sobre o ativo e o contexto de\n"
            "  mercado, deixando claro quando algo é contexto geral e não dado fornecido.\n"
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
            "- Defina o ALVO por uma relação risco:retorno coerente com o horizonte.\n"
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
    }


def default_state() -> dict:
    return {
        "config": {
            "provider": "anthropic",   # anthropic | openai | google | local
            "model": "",
            "keySource": "env",        # env | manual
            "apiKey": "",              # so preenchido se keySource == manual; nunca retornado
            "baseUrl": "",
            "initialBudget": 10000.0,  # orcamento SIMULADO inicial (R$); vira o caixa
            "theme": "dark",           # dark | light | system
            "userName": "",            # nome do usuario para personalizacao sobria
            "onboarded": False,        # tela de boas-vindas ja vista? (lida na init)
            "streak": {"days": 0, "last": ""},  # consistencia (dias seguidos abrindo)
            "notif": {                 # notificacoes LOCAIS de movimentos da carteira
                "enabled": False,      # mestre (pede permissao quando ligado)
                "stop": True, "alvo": True, "agente": True, "variacao": True,
            },
        },
        "skill": {"name": "Mesa B3 - Educacional v1", "text": default_skill_text()},
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
