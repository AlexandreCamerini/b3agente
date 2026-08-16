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


def _formato_array_carteira(frases: str) -> str:
    """Contrato de saída do N3 (array por ativo, parseado pelo popup) — comum
    aos dois modos; só o tamanho da explicação muda."""
    return (
        "Formato de saída: retorne SOMENTE um JSON (nada fora dele), um objeto por\n"
        "ativo:\n"
        "[\n"
        "  {\n"
        '    "ativo": "PETR4",\n'
        '    "precoAtual": 38.50,\n'
        '    "stop": 36.20,\n'
        '    "alvo": 43.00,\n'
        '    "explicacao": "…' + frases + '…",\n'
        '    "operar": true\n'
        "  }\n"
        "]"
    )


# Fecho dos prompts de carteira: DISCLAIMER canônico como enquadramento.
_ENQUADRAMENTO_CARTEIRA = (
    "Enquadramento (não copie este parágrafo para o JSON): " + skill_ref.DISCLAIMER
)

# Migração dos llmPrompts (pendência 2 da auditoria, executada em 2026-08-01):
# sha256 de TODAS as gerações ANTERIORES dos textos default (extraídas do git —
# b9bf737/34e6f0f para o educacional; 34e6f0f para o operador). Usuário cujo
# prompt salvo bate com uma delas NUNCA editou o texto → recebe o default novo
# no próximo ensure_defaults. Texto que não bate com nenhuma é edição do
# usuário e fica intocado. Gen nova no default => acrescente o hash da antiga.
LEGACY_PROMPT_SHA256 = {
    "carteiraStopAlvo": {
        "1227244362d0740687e8b893f44a27cd5f3119faf9ae903c009ecd30bde1c65b",
        "ecdfea67063ebc0736829cbb8e3b284e6b4c8ec5783bc92777b386c53b920d81",
        # 10/08/2026 — geração que mandava zerar stop/alvo com operar=false
        "72f5394e112fd23f14d1618c5efc7e764a3cb5778aabb486bf3e8446de966056",
    },
    "carteiraStopAlvoOperador": {
        "021b5ac9827417685ac52f7aed77745828b2da783ff9816f44eda8dc7258a375",
        # 10/08/2026 — idem (o stop nunca é proibido)
        "c0b27d0bc97f4a96e46bb1d23a89ac93decbf34732c9adb04875c9545ba01bc8",
    },
}


# ADR-013 (Decisão 5a) — camada NOVA por cima do código, sem tocar este
# arquivo em runtime: o admin pode editar o default GLOBAL de llmPrompts via
# `prompt_defaults_override` (server/app/db.py); a edição do USUÁRIO sempre
# tem prioridade — reusa `LEGACY_PROMPT_SHA256`/`_eh_default_antigo` (a lista
# acima), só troca a FONTE do histórico de hashes de "hardcoded no código"
# para "tabela `prompt_default_history`, que ganha uma linha a cada
# publicação do admin". `defaults.py`/este dicionário nunca são escritos em
# runtime — continuam sendo o piso de recuperação de desastre.
def default_llm_prompts_ativo(conn) -> dict:
    """Default GLOBAL vigente: override do admin se existir, senão o texto de
    código (`default_llm_prompts()`) — nunca o override PESSOAL do usuário
    (esse é outro dado, em `store.get(conn, "llmPrompts", user_id=...)`)."""
    from . import db
    base = default_llm_prompts()
    overrides = db.prompt_override_get_all(conn)
    if not overrides:
        return base
    return {**base, **{k: v for k, v in overrides.items() if k in base}}


def publicar_override_admin(conn, chave: str, novo_texto: str, admin_user_id: str) -> None:
    """Admin publica um novo texto para o default GLOBAL de `chave`. O texto
    ATIVO anterior (override existente, ou o de código se nunca houve
    override) entra em `prompt_default_history` — é esse histórico que
    `store._eh_default_antigo` consulta para decidir se uma conta "nunca
    editou" (migra pro novo) ou "editou de verdade" (fica intocada)."""
    import hashlib
    from datetime import datetime, timezone
    from . import db

    if chave not in default_llm_prompts():
        raise ValueError(f"Chave de prompt desconhecida: {chave!r}")
    anterior = db.prompt_override_get(conn, chave)
    if anterior is None:
        anterior = default_llm_prompts()[chave]
    agora = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    db.prompt_history_add(conn, chave, hashlib.sha256(anterior.encode()).hexdigest(), anterior, agora)
    db.prompt_override_set(conn, chave, novo_texto, updated_by=admin_user_id, updated_at=agora)


def default_llm_prompts() -> dict:
    """FASE 2/3: coleção de prompts indexada por chave (extensível). O prompt da
    carteira analisa CADA ATIVO INDIVIDUALMENTE (saída em array por ativo) e
    mantém o enquadramento educacional (sugestão por perfil, não recomendação).

    Auditoria 2026-07-31 (A8ii): os blocos invioláveis COMPÕEM do canônico
    (skill_ref.PRINCIPIOS_N3 + DISCLAIMER) em vez de reescrever — o formato de
    saída permanece intacto. Prompts são persistidos por usuário (llmPrompts):
    a recomposição vale para DEFAULTS novos; estado existente não é migrado.
    IMPORTANTE: web/src/catalog.js espelha o TEXTO final destes defaults (o
    aparelho monta o estado sem servidor) — paridade travada byte a byte em
    test_auditoria_prompts.py; mudou aqui, mude lá."""
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
            + skill_ref.PRINCIPIOS_N3 + "\n"
            "Regras específicas do modo ESTUDO:\n"
            "- Conteúdo EDUCACIONAL e dinheiro SIMULADO — deixe isso explícito.\n"
            "- A proposta é uma SUGESTÃO por perfil, NÃO recomendação de compra ou venda,\n"
            "  nem sinal de entrada.\n"
            "- Dimensione o STOP para limitar a perda por operação conforme a tolerância\n"
            "  do perfil.\n"
            "- Abaixo do R:R mínimo, trate como cenário de estudo desfavorável ou use\n"
            '  "operar": false.\n'
            "Para cada ativo, explique em 2 a 4 frases, em linguagem simples, o raciocínio\n"
            "por trás dos números.\n"
            + _formato_array_carteira("2 a 4 frases") + "\n"
            'Quando recomendar aguardar, use "operar": false — e MESMO ASSIM devolva\n'
            'stop e alvo técnicos: quem já está posicionado precisa do nível de\n'
            'proteção, e definir stop nunca é proibido. Explique em "explicacao".\n'
            + _ENQUADRAMENTO_CARTEIRA
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
            + skill_ref.PRINCIPIOS_N3 + "\n"
            "Regras específicas do modo MESA:\n"
            "- O STOP fica na INVALIDAÇÃO TÉCNICA da posição (suporte/resistência, extremo\n"
            "  do setup, ATR) — nunca num percentual arbitrário.\n"
            '- Abaixo do R:R mínimo, a posição não compensa: "operar": false —\n'
            "  não operar também é posição.\n"
            "- A execução é do cliente, na corretora dele; isto não é recomendação\n"
            "  personalizada de investimento.\n"
            "Para cada ativo, dê a explicação em 1 a 3 frases de mesa: nível técnico do\n"
            "stop, R:R do alvo e a condição que cancela o plano.\n"
            + _formato_array_carteira("1 a 3 frases") + "\n"
            'Quando a posição não compensar, use "operar": false — e MESMO ASSIM devolva\n'
            'stop e alvo técnicos: o stop é a proteção de quem já está posicionado e\n'
            'nunca é omitido. Diga objetivamente o porquê em "explicacao".\n'
            + _ENQUADRAMENTO_CARTEIRA
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
            "borisIntroVisto": False,  # F6: apresentacao do Boris ja vista? (1x, na aba Mercado)
            "candlePeriod": "1y",      # Objetivo 4: janela de candles (1mo|3mo|6mo|1y|2y)
            "streak": {"days": 0, "last": ""},  # consistencia (dias seguidos abrindo)
            "notif": {                 # notificacoes LOCAIS de movimentos da carteira
                "enabled": False,      # mestre (pede permissao quando ligado)
                "stop": True, "alvo": True, "agente": True, "variacao": True,
                # Classe NOVA (2026-08-05): aviso de condição/gatilho atingido.
                # Nasce DESLIGADA de propósito — é a única que interrompe fora
                # do app por evento de mercado, e alerta de mercado é opt-in.
                "gatilho": False,
            },
            # Camada de entendimento: ids de conceito que o usuário já viu
            # (a explicação aparece sozinha UMA vez; depois fica a um toque).
            "conceitosVistos": [],
            # Camada de entendimento: medição de descoberta do sublinhado.
            # `gesto` = toques no termo sublinhado; `botao` = via sr-only;
            # `aberturas` é legado do toque longo (não é mais incrementado,
            # fica pelo merge monotônico entre aparelhos).
            "gestoUso": {"aberturas": 0, "gesto": 0, "botao": 0},
            # FASE 7 (F7.1) — Modo Operador
            "appMode": "estudo",       # estudo | operador (operador exige termo aceito)
            "operadorTermo": None,     # {aceitoEm, versao} registrado no aceite
            "risco": {"pctPorTrade": 1.0, "capital": None},  # sizing (capital None => usa initialBudget)
            # Tela de configuração do Boris (F10-20260809): voz, presença do
            # FAB e o único canal de aviso espontâneo (o mesmo `notif.gatilho`
            # acima — não é um segundo canal, só um segundo ponto de acesso).
            "vozAtiva": True,          # lê as respostas em voz alta? default ligado (comportamento de sempre)
            "vozId": "",               # voiceURI escolhida; "" = a plataforma decide
            "fabVisivel": True,        # assistente flutuante visível? default ligado nos dois modos
        },
        "skill": {"name": "Mesa B3 - Educacional v1", "text": default_skill_text()},
        # FASE 8B (R2): instrução do agente POR MODO, selecionável pelo nome
        "skillOperador": {"name": "Mesa B3 - Operador v1", "text": default_skill_text_operador()},
        "llmPrompts": default_llm_prompts(),
        "watchlist": ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "B3SA3"],
        # A CARTEIRA COMEÇA ZERADA — caixa = orçamento, sem posições, sem
        # histórico. Antes o estado inicial trazia R$ 23.600 em PETR4/ITUB4/
        # VALE3 com o caixa INTACTO nos R$ 10.000: ações que nunca foram pagas.
        # Consequências, todas visíveis ao usuário:
        #   • patrimônio de abertura ~R$ 33.600 contra "orçamento" de R$ 10.000,
        #     ou seja +236% de retorno acumulado antes da primeira operação;
        #   • o histórico exibia três COMPRAS com datas de junho que a pessoa
        #     nunca fez;
        #   • como o caixa nunca foi debitado, cada compra ADICIONAVA
        #     patrimônio — comprar bastava para o "retorno" subir.
        # `reset_portfolio` já produzia o estado correto (caixa = orçamento,
        # posições vazias); só a abertura divergia dele.
        "cash": 10000.0,
        "positions": [],
        "history": [],
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
        "optionPositions": [],          # ADR-003: coleção própria — nunca mistura com `positions`
    }
