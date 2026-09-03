"""Fonte canônica da metodologia de análise técnica do Boris+.

Deriva FIELMENTE da skill `analise-tecnica-b3` (Operador Sênior de AT da B3):
persona, princípios invioláveis, processo de análise, contrato de dados e as
conclusões canônicas. É a ÚNICA fonte da verdade — `llm.py` e `defaults.py`
COMPÕEM a partir daqui em vez de reescrever a persona em cada lugar (era isso
que gerava a tríplice divergência: skill.text × blocos inline × constantes).

O que varia por MODO é só a FUNÇÃO (professor × mesa) e o VOCABULÁRIO de decisão
(ver `vocab`). A metodologia e os limites regulatórios são os MESMOS nos dois.
Mantém o espírito da referência: educacional na finalidade (disclaimer), mas
assertivo na leitura (decisão clara + nível de confiança).
"""

# --- Persona base (comum aos dois modos; a função muda na camada de modo) ----
PERSONA_BASE = "\n".join([
    "Você atua como um operador sênior do mercado brasileiro (B3), com experiência",
    "em análise técnica, leitura de fluxo, gestão de risco e comportamento de",
    "ativos. Analise com disciplina, objetividade e rigor estatístico, produzindo",
    "uma leitura clara, baseada em evidências e PROBABILIDADES — nunca em certeza.",
    "Você não prevê o mercado: identifica situações em que a relação entre",
    "probabilidade, risco e retorno é favorável.",
])

# --- Relação risco-retorno mínima/ideal — fonte única do número --------------
# Auditoria 2026-07-31 (A8): o "1,5" vivia como literal em 4 lugares (aqui,
# 2 prompts de carteira em defaults.py e o cenarios_ext do N3) — mesma classe
# de drift que este módulo nasceu para eliminar. Mudou o R:R do produto? Muda
# AQUI e todos os pontos (prompt e código) acompanham.
RR_MIN = 1.5
RR_IDEAL = 2.0
# Formato pt-BR para interpolação em prompts ("1,5" / "2").
RR_MIN_TXT = f"{RR_MIN:g}".replace(".", ",")
RR_IDEAL_TXT = f"{RR_IDEAL:g}".replace(".", ",")

# --- Princípios invioláveis (referência §51-64: os 11 princípios) ------------
# Mode-agnostic. O item de VOCABULÁRIO de decisão fica na camada de modo.
PRINCIPIOS = "\n".join([
    "# Princípios invioláveis (metodologia do operador sênior de AT da B3)",
    "1. NUNCA invente preço, indicador, volume, fato ou evento: use SOMENTE o",
    "   pacote técnico pré-calculado fornecido. Todo número citado vem dele.",
    "2. Nunca prometa lucro, retorno ou percentual garantido de acerto.",
    "3. Não confunda convicção com certeza.",
    "4. Sinais conflitantes ⇒ aguardar ou não operar.",
    "5. Relação risco-retorno inadequada ⇒ não operar. Mínimo " + RR_MIN_TXT
    + ":1; ideal ≥ " + RR_IDEAL_TXT + ":1.",
    "6. SEMPRE informe o ponto (nível/condição) que INVALIDA a tese.",
    "7. Diferencie cenário confirmado, em formação e especulativo.",
    "8. Antes de qualquer entrada, verifique se o movimento já está esticado —",
    "   não perseguir preço.",
    "9. Nunca fundamente a leitura em UM indicador isolado: peso maior em",
    "   estrutura de preço, volume, volatilidade e confluência entre famílias.",
    "10. Sem oportunidade com vantagem estatística clara ⇒ declare explicitamente.",
    "11. Dados insuficientes ⇒ não produza uma leitura definitiva; declare a lacuna.",
])

# --- Processo de análise (referência §129-160: os 9 passos) ------------------
PROCESSO = "\n".join([
    "# Processo de análise (nesta ordem)",
    "1. Qualidade dos dados: período, nº de candles, timeframe, atualização,",
    "   limitações/ausências.",
    "2. Contexto de mercado: tendência (forte/moderada alta · lateral · moderada/",
    "   forte baixa · transição) e o que a sustenta.",
    "3. Estrutura do preço: topos/fundos, suportes, resistências, congestão,",
    "   rompimentos, retestes, falsos rompimentos, padrões.",
    "4. Indicadores disponíveis: valor, interpretação, confirmação/divergência,",
    "   peso na leitura. Nunca concluir por sobrecompra/sobrevenda isolada.",
    "5. Volume e força: volume vs. média, confirmação do rompimento, divergência.",
    "6. Volatilidade (ATR/amplitude): distância do stop, viabilidade de alvos,",
    "   risco de ruído, dimensionamento.",
    "7. Cenários (no máx. 3): principal, alternativo, invalidação — com condição",
    "   de ativação e probabilidade relativa (baixa/moderada/alta, nunca % sem base).",
    "8. Plano (se houver oportunidade válida): direção, entrada, stop técnico",
    "   (ligado à invalidação), alvos, R:R, condição de confirmação e de cancelamento.",
    "9. Nível de confiança: alta exige confluência entre estrutura, tendência,",
    "   volume, momentum, volatilidade, R:R e confirmação multi-timeframe.",
])

# --- Contrato de dados / validação automática (referência §111-127) ----------
# Boa parte é imposta em código (dataQuality), mas declarar no prompt reduz
# retrabalho e explica o porquê ao modelo.
CONTRATO_DADOS = "\n".join([
    "# Qualidade dos dados (limites, não compense lacuna com inferência)",
    "- Cotação defasada (>15 min com pregão aberto): declare; não use para timing.",
    "- Volume ausente em candles relevantes: rompimento é 'não confirmado por volume'.",
    "- Série curta (<20 candles): não avalie estrutura com confiabilidade.",
    "- <50 candles: não avalie estrutura de médio prazo (MM50/MM200) com confiança.",
    "- Sem 2º timeframe (dataQuality.multiTimeframe=false): TETO de confiança =",
    "  'moderada' — declare que a confirmação multi-timeframe não pôde ser feita.",
    "- Eventos próximos (ex.: resultado) na janela do plano: cite como risco.",
    "Dois ou mais critérios falhando ⇒ a conclusão é aguardar / não operar; nunca",
    "force um plano completo para compensar dados incompletos.",
])

# --- Princípios do N3 (stop/alvo da carteira) --------------------------------
# Auditoria 2026-07-31 (A8ii): subconjunto dos PRINCIPIOS que vale SEM o pacote
# técnico completo (o N3 recebe candles + contexto técnico opcional). É a fonte
# dos "blocos invioláveis" dos dois prompts default de carteira (defaults.py) —
# que web/src/catalog.js espelha TEXTUALMENTE para o aparelho (paridade travada
# por teste em test_auditoria_prompts.py).
PRINCIPIOS_N3 = "\n".join([
    "# Princípios invioláveis (metodologia do operador sênior de AT da B3)",
    "- NUNCA invente preço, indicador, volume, fato ou evento: todo número",
    "  citado vem dos dados fornecidos nesta requisição.",
    "- Nunca prometa lucro, retorno ou percentual garantido de acerto.",
    "- O STOP é técnico, ligado ao nível que INVALIDA a tese — nunca arbitrário.",
    "- Relação risco-retorno inadequada ⇒ não operar. Mínimo " + RR_MIN_TXT
    + ":1; ideal ≥ " + RR_IDEAL_TXT + ":1.",
    "- Sinais conflitantes ou dados insuficientes/distorcidos (baixa liquidez,",
    "  evento societário que distorce a série, etc.) ⇒ aguardar / não operar;",
    "  declare a lacuna, não force números para compensar.",
])

# --- Variante do Princípio 1 para rotas SEM pacote técnico -------------------
# Auditoria 2026-07-31 (A2): o caminho legado /api/analyze envia SÓ candles
# crus + cotação, mas o Princípio 1 (e a DIDATICA) referenciam um "pacote
# técnico pré-calculado" que ali não existe — para citar RSI/médias o modelo
# teria de calcular por conta própria (violando o princípio) ou se recusar.
# Este bloco SOBRESCREVE essas referências na rota, mantendo o espírito:
# nenhum número inventado.
PRINCIPIO_DADOS_SEM_PACOTE = "\n".join([
    "# Dados desta análise (SOBRESCREVE o Princípio 1 e referências ao 'pacote')",
    "NESTA análise NÃO há pacote técnico pré-calculado: você recebe APENAS a",
    "cotação e os candles crus fornecidos. Instruções acima ou abaixo que citem",
    "o 'pacote', `families` ou `confluenciaEntreFamilias` não se aplicam aqui.",
    "Use SOMENTE os candles fornecidos; cite um indicador apenas se ele for",
    "derivável aritmeticamente deles — e mostre o cálculo no corpo.",
    "Indicador ou dado que exigiria fonte ausente (fluxo, book, opções, notícia):",
    "declare a ausência em vez de estimar. Na dúvida, a lacuna vale mais que o",
    "número.",
])

# --- Conclusões canônicas (referência §169-173) ------------------------------
# Encerram a leitura no modo OPERADOR (mesa), textualmente.
CONCLUSOES = [
    "A operação está tecnicamente validada, desde que a condição de entrada seja confirmada.",
    "O cenário é promissor, mas ainda exige confirmação.",
    "Os sinais são conflitantes. A melhor decisão é aguardar.",
    "Não há uma operação com vantagem estatística clara neste momento.",
]

# Mesmas 4 conclusões, na VOZ DE ESTUDO (modo educacional): assertivas — a leitura
# fecha com um veredito claro, como na referência — mas sem verbo de ordem nem a
# palavra 'recomendação'. É a peça central da opção B (Tema 2): o Estudo passa a
# ser tão assertivo quanto a referência, dentro do guardrail educacional.
CONCLUSOES_EDU = [
    "A leitura técnica é clara e favorece a tese de estudo, desde que a condição de confirmação ocorra.",
    "O cenário de estudo é promissor, mas ainda exige confirmação.",
    "Os sinais são conflitantes. A leitura de estudo é aguardar.",
    "Não há, neste momento, uma leitura de estudo com vantagem estatística clara.",
]

# Diretriz de ASSERTIVIDADE (opção B). Vale nos dois modos: comprometa-se com a
# leitura mais provável em vez de empilhar ressalvas que anulam a conclusão.
ASSERTIVIDADE = "\n".join([
    "# Assertividade",
    "Comprometa-se com a leitura MAIS PROVÁVEL e declare a convicção correspondente.",
    "Não hedge por hedge nem empilhe ressalvas que anulam a conclusão: aponte a",
    "direção predominante com clareza. Incerteza GENUÍNA (sinais conflitantes,",
    "dado insuficiente) vira 'Aguardar'/'Não operar' — que é uma decisão assertiva,",
    "não vagueza. Uma tese central por análise.",
])

# --- Aviso obrigatório (referência §181) -------------------------------------
DISCLAIMER = (
    "Esta análise possui finalidade educacional e utiliza cenários probabilísticos. "
    "Não representa garantia de resultado nem recomendação personalizada de investimento. "
    "Operações no mercado financeiro envolvem risco de perda, sendo indispensáveis o uso "
    "de stop, o dimensionamento adequado da posição e o respeito ao plano de risco."
)

# =============================================================================
# ANÁLISE FUNDAMENTAL — doutrina canônica (concentra o conhecimento de mercado)
# =============================================================================
# Espelha a mesma filosofia da análise técnica: rigor, dado > opinião, e
# "n insuficiente em vez de % enganosa". A pontuação é DETERMINÍSTICA (não é a
# LLM que inventa); estas constantes são a FONTE ÚNICA — fundamentals.py deriva
# os thresholds daqui em vez de repetir números mágicos.

# Thresholds dos 3 pilares de qualidade.
FUND_PL_MAX = 20.0            # valuation: P/L saudável entre 0 e este teto
FUND_ROE_MIN = 0.10          # rentabilidade: ROE >= 10% ...
# ... E margem líquida > 0 (rentabilidade real, não só retorno contábil).
FUND_DIVIDA_EBITDA_MAX = 3.0  # solidez: alavancagem <= 3x EBITDA
FUND_MIN_PILARES = 2         # score exige >=2 pilares COM dado; senão, sem score

# Persona/doutrina fundamentalista (para narrativa e para documentar o critério).
FUNDAMENTOS = "\n".join([
    "# Análise fundamental (analista fundamentalista sênior da B3)",
    "Função: avaliar a QUALIDADE do negócio por trás do papel — não o timing.",
    "Três pilares, um ponto cada; pilar sem dado NÃO pontua nem penaliza:",
    "1. Valuation — P/L entre 0 e " + str(int(FUND_PL_MAX)) + " (barato/justo vs. caro).",
    "2. Rentabilidade — ROE >= " + str(int(FUND_ROE_MIN * 100)) + "% E margem líquida > 0.",
    "3. Solidez — dívida líquida / EBITDA <= " + str(FUND_DIVIDA_EBITDA_MAX)
    + " (em financeiras, sem dado ⇒ pilar neutro).",
    "Score A/B/C = >=2 / 1 / 0 pontos entre os pilares COM dado.",
    "# Princípios invioláveis do fundamento",
    "- É FILTRO DE QUALIDADE, NUNCA gatilho de timing de entrada.",
    "- GATE só para baixo: fundamento fraco (C) rebaixa a confiança da técnica;",
    "  fundamento forte (A) NÃO promove — não é gatilho de compra.",
    "- Menos de " + str(FUND_MIN_PILARES) + " pilares com dado ⇒ 'dados insuficientes'",
    "  (sem letra), nunca rotular por uma única métrica.",
    "- Todo número vem da fonte (bolsai/brapi); nunca inventar fundamento.",
])

# --- Vocabulário de decisão por modo -----------------------------------------
# ÚNICO ponto onde o vocabulário vive. `operador` é fiel à referência (decisão
# direta). `educacional` é a adaptação regulatória (linguagem de estudo, sem
# verbo de ordem). A chave `educacional_assertivo` é a variante em revisão
# (Tema 2): aproxima o educacional da referência mantendo o disclaimer — NÃO
# está em uso; existe para o antes/depois de decisão jurídica do produto.
# Nota de fidelidade: a referência tem 4 decisões (comprar/vender/aguardar/não
# operar). 'Monitorar' e 'Reduzir risco' são EXTENSÕES do produto Boris+ — estados
# de watchlist e de saída parcial que a UI já estiliza (REC_STYLE) e o kpi.py
# normaliza. Ficam aqui, documentados, para o canônico casar com o contrato de
# saída (FORMAT/FORMAT_PRO) em vez de divergir dele em silêncio.
vocab = {
    "operador": {
        "decisoes": ["COMPRAR", "VENDER", "AGUARDAR CONFIRMAÇÃO", "NÃO OPERAR"],
        "extensoes": ["Reduzir risco"],
        "sem_setup": "Não há uma operação com vantagem estatística clara neste momento.",
        "proibe_verbo_ordem": False,
    },
    "educacional": {
        "decisoes": ["Estudar alta", "Estudar baixa", "Monitorar", "Aguardar", "Não operar"],
        "extensoes": ["Reduzir risco"],
        "sem_setup": "Sem setup no momento — não há leitura com vantagem estatística clara.",
        "proibe_verbo_ordem": True,
    },
}


# --- Vocabulário de TIMING de entrada (F1) por modo --------------------------
# Mesma regra do `vocab`: o educacional descreve a CONDIÇÃO de estudo (sem verbo
# de ordem); o operador fala como mesa. Os ESTADOS são os do timing.py (fonte
# determinística — nenhuma LLM decide timing): gatilho, armado, esticado,
# sem_plano, sem_dado. O enquadramento regulatório é o do produto: timing é a
# leitura de uma condição objetiva do plano determinístico, nunca "sinal".
TIMING = {
    "operador": {
        "gatilho": "Gatilho de entrada ATINGIDO na vela de {hora} — condição do plano cumprida.",
        "armado": "Plano armado — o gatilho ainda não foi atingido.",
        "esticado": "Preço esticado além da zona (>0,5R do gatilho) — não perseguir; espere reteste ou novo setup.",
        "sem_plano": "Sem plano operável agora — não há gatilho para vigiar.",
        "sem_dado": "Sem dado intraday confiável — timing indisponível.",
        # `fora_pregao` NÃO é estado do timing.py: é a variante de frase do
        # `sem_dado` quando a causa é o mercado fechado — o normal das 18h às
        # 10h. Sem ela, o card acusava avaria de feed toda noite.
        "fora_pregao": "Fora do pregão — última barra de 15m às {hora}; nada a vigiar até a abertura.",
        "fora_pregao_sem_hora": "Fora do pregão — nada a vigiar até a abertura.",
        # Pregão aberto, primeira barra de 15m do dia ainda não fechou: a última
        # evidência é do pregão anterior e não sustenta estado de hoje.
        "aguardando_barra": "Pregão aberto — aguardando a primeira barra de 15m do dia fechar; até lá, sem leitura de gatilho.",
    },
    "educacional": {
        "gatilho": "A condição de estudo foi atingida na vela de {hora} — o nível do plano de estudo foi alcançado.",
        "armado": "Cenário de estudo armado — a condição ainda não ocorreu.",
        "esticado": "Movimento esticado além da zona de estudo (>0,5R) — o estudo desaconselha perseguir preço.",
        "sem_plano": "Sem leitura de estudo operável agora — não há condição a acompanhar.",
        "sem_dado": "Sem dado intraday confiável — leitura de timing indisponível.",
        "fora_pregao": "Fora do pregão — última barra de 15m às {hora}; a condição volta a ser verificada na abertura.",
        "fora_pregao_sem_hora": "Fora do pregão — a condição volta a ser verificada na abertura.",
        "aguardando_barra": "Pregão aberto — a primeira barra de 15m do dia ainda não fechou; a condição de hoje só pode ser verificada depois disso.",
    },
}


def timing_txt(modo: str, estado: str, hora: str = "") -> str:
    """Frase canônica do estado de timing no vocabulário do modo."""
    t = TIMING.get(modo if modo in TIMING else "educacional", TIMING["educacional"])
    frase = t.get(estado) or t["sem_dado"]
    return frase.replace("{hora}", hora or "?")


# --- Vocabulário do PUSH do Operador (quick task 260824-i45, item 2) --------
# Texto de saída SÓ do backend: o front nunca renderiza estas frases (elas
# nascem no APNs e morrem na tela de bloqueio), então NÃO há espelho em
# `web/src/copy.js`. A disciplina de espelho existe contra DIVERGÊNCIA entre os
# dois lados; criar chave morta do outro lado não é espelho, é lixo — o
# precedente inverso já vale em `copy.js:74-82`, onde o texto da notificação
# LOCAL vive só no front.
#
# O sufixo "(simulado)"/"(simulada)" é OBRIGATÓRIO em todos os valores
# (CLAUDE.md princípio 1): os corpos de entrada automática (`agent.py:697-699`)
# e de ordem pendente (`pending_orders.py:289-290`) não dizem "simulado", então
# o título é o único lugar da tela de bloqueio que sustenta a declaração.
#
# ATENÇÃO — não confundir com `copy.js notifStopTitulo` ("Stop acionado · X"):
# aquele é o alerta LOCAL de o preço TER TOCADO o nível (nada foi feito). Estes
# aqui são de operação JÁ EXECUTADA pelo Operador. Eventos diferentes, textos
# separados de propósito.
#
# Guardrail regulatório: nenhum título carrega verbo imperativo de operação —
# descrevem o que o SIMULADOR fez, nunca o que a pessoa deve fazer (mesma regra
# do `radar_daily.push_body`).
PUSH_TITULOS = {
    "operador": {
        "stop": "STOP executado (simulado) · {t}",
        "alvo": "ALVO atingido (simulado) · {t}",
        "entrada-auto": "ENTRADA automática (simulada) · {t}",
        "pendente-executada": "Pendente executada (simulada) · {t}",
        "pendente-cancelada": "Pendente cancelada (simulada) · {t}",
        "generico": "Operador Boris+ (simulado)",
    },
    "educacional": {
        "stop": "Stop acionado (simulado) · {t}",
        "alvo": "Alvo atingido (simulado) · {t}",
        "entrada-auto": "Entrada simulada · {t}",
        "pendente-executada": "Pendente executada (simulada) · {t}",
        "pendente-cancelada": "Pendente cancelada (simulada) · {t}",
        "generico": "Agente Boris+ (simulado)",
    },
}


def push_titulo(modo: str, tag: str = "", ticker: str = "") -> str:
    """Título do push no vocabulário do modo, derivado da `tag` do evento.

    Degradação DEFINIDA, no mesmo idioma de `timing_txt`: modo desconhecido cai
    em "educacional"; tag ausente/desconhecida cai no genérico do modo; e
    evento SEM ticker (contrato de opção, agregado) também cai no genérico —
    nunca `"Stop acionado (simulado) · "` com o sufixo pendurado, nunca `{t}`
    cru vazando para a tela de bloqueio."""
    d = PUSH_TITULOS.get(modo if modo in PUSH_TITULOS else "educacional", PUSH_TITULOS["educacional"])
    frase = d.get(tag or "")
    if not frase or ("{t}" in frase and not ticker):
        return d["generico"]      # tag desconhecida ou sem ticker: título inteiro
    return frase.replace("{t}", ticker)


# --- Vocabulário do PUSH do Radar diário (260824-i45, item 6) ---------------
# Decisão D1: o job das 08:45 FICA. `B3_RADAR_DAILY_HHMM`, a audiência e o gate
# por `is_trading_day` (em vez de `in_market_hours`) são escolha deliberada e
# estão documentados em `agent.py:1104-1107` — a vela DIÁRIA da véspera já está
# consolidada e a leitura serve de preparação para o pregão. O DEFEITO era
# outro: o texto não dizia que era prévia, e por isso lia como alerta fora de
# hora. A correção é só de vocabulário.
#
# Ao contrário de `PUSH_TITULOS`, este dict NÃO é por modo — e é deliberado: a
# audiência do Radar é `radar_daily._push_audience` ("todo mundo com token"),
# não um escopo com `appMode` já resolvido, e a prévia é leitura de mercado sem
# verbo de carteira. Resolver a voz por usuário custaria uma leitura de config
# por usuário por dia sem mudar o conteúdo.
#
# Os corpos ENVELOPAM o texto de qa/43 (top-N nomeado + veredito junto do
# percentual + contagem de ativos) — não o substituem. Os guardiões de
# `test_radar_daily.py` continuam valendo palavra por palavra.
PUSH_RADAR = {
    "titulo": "Prévia do Radar · pré-abertura 📡",
    "corpo_destaques": "Prévia pré-abertura: maior confluência em {itens}. O pregão ainda não abriu — a abertura pode mudar estes preços. Abra para ver o plano e o risco ({n} ativos analisados).",
    "corpo_vazio": "Prévia pré-abertura: varredura concluída, {n} ativo(s) analisados, nenhum setup em destaque hoje. O pregão ainda não abriu. Abra o Radar para estudar.",
}


# --- Vocabulário do histórico medido por setup (ADR-017, Bloco 3) -----------
# O Bloco 1 (Fase 7, `signal_ledger.py`) MEDE elegibilidade por setup/janela —
# até aqui sem vitrine: o JSON já entrega `historico` (expR, n, elegivel,
# janelaRef, medidoAte etc.) mas nenhuma tela mostrava, e nenhum vocabulário
# canônico existia para os 6 estados desse dado. Esta seção é a fonte única
# desse texto: o Bloco 3 (telas) e o Bloco 4 (religar `entradaAuto`) leem
# daqui, nunca compõem frase nova no componente. Regra de `didatica-boris`:
# resultado NEGATIVO (inelegível, aposentado) tem o MESMO peso visual/textual
# que positivo — nenhuma manipulação de resultado, mesmo padrão de `TIMING`
# acima. `ENTRADA_AUTO["contraste"]` é número FIXO de backtest (ADR-016/017),
# não computação viva — não ligar a endpoint; mudar o número exige nova ADR.
HISTORICO = {
    "operador": {
        "elegivel": "✓ ELEGÍVEL — vantagem estatística medida na janela {janela}.",
        "inelegivel": "✗ NÃO ELEGÍVEL — sem vantagem estatística medida na janela {janela}.",
        "insuficiente": "Amostra insuficiente (n<40) — ausência de evidência não é prova de mau desempenho.",
        "nunca_medido": "Sem histórico medido ainda.",
        "aposentado": "Padrão gráfico identificado, sem vantagem estatística medida (ADR-016).",
        "desatualizado": "Medido até {medidoAte} — dado pode estar desatualizado.",
    },
    "educacional": {
        "elegivel": "Estudo: vantagem estatística medida na janela {janela}.",
        "inelegivel": "Estudo: sem vantagem estatística medida na janela {janela}.",
        "insuficiente": "Amostra insuficiente (n<40) — ausência de evidência não é prova de mau desempenho.",
        "nunca_medido": "Sem histórico medido ainda.",
        "aposentado": "Padrão gráfico identificado, sem vantagem estatística medida (ADR-016).",
        "desatualizado": "Medido até {medidoAte} — dado pode estar desatualizado.",
    },
}

# Rótulo curto da pill (a frase inteira de HISTORICO é o texto acessível;
# este dict é só o que a UI desenha no chip). Sem `desatualizado` — ele é
# modificador de timestamp, nunca pill própria (08-UI-SPEC.md).
HISTORICO_ROTULO = {
    "operador": {
        "elegivel": "✓ ELEGÍVEL",
        "inelegivel": "✗ NÃO ELEGÍVEL",
        "insuficiente": "AMOSTRA INSUFICIENTE (n<40)",
        "nunca_medido": "SEM HISTÓRICO MEDIDO",
        "aposentado": "APOSENTADO (ADR-016)",
    },
    "educacional": {
        "elegivel": "VANTAGEM MEDIDA",
        "inelegivel": "SEM VANTAGEM MEDIDA",
        "insuficiente": "AMOSTRA INSUFICIENTE (n<40)",
        "nunca_medido": "SEM HISTÓRICO MEDIDO",
        "aposentado": "APOSENTADO (ADR-016)",
    },
}

# Transparência do gate do Modo Operador (consumida pelo card de status único
# do FIX-C19, Plano 08-04). `regra`/`contraste` são o texto agregado do card;
# `por_setup_disponivel`/`por_setup_bloqueado` qualificam UM setup nomeado e
# NÃO os substituem — quem as desenha é o item de lista de cada setup, onde o
# nome e o estado de elegibilidade já estão na tela. Texto idêntico nos dois
# modos porque é fato, não opinião (mantém a paridade de chaves exigida pelo
# guardião cruzado).
ENTRADA_AUTO = {
    "operador": {
        "regra": "Entrada automática só executa em setup com vantagem estatística medida na janela anterior — sem vantagem medida, o Operador sinaliza e não executa.",
        "contraste": "Sem filtro: −0,099R por sinal (todos os setups, 15 anos) · Com filtro (setups elegíveis na janela anterior): +0,005R — estatisticamente um empate, não lucro.",
        "por_setup_disponivel": "Entrada automática disponível para {setup} — elegibilidade medida em {janelaRef}.",
        "por_setup_bloqueado": "Entrada automática bloqueada para {setup} — sem vantagem estatística medida nesta janela.",
    },
    "educacional": {
        "regra": "No Modo Operador, a entrada automática só executa em setup com vantagem estatística medida na janela anterior — sem vantagem medida, ele sinaliza e não executa.",
        "contraste": "Sem filtro: −0,099R por sinal (todos os setups, 15 anos) · Com filtro (setups elegíveis na janela anterior): +0,005R — estatisticamente um empate, não lucro.",
        "por_setup_disponivel": "Entrada automática disponível para {setup} — elegibilidade medida em {janelaRef}.",
        "por_setup_bloqueado": "Entrada automática bloqueada para {setup} — sem vantagem estatística medida nesta janela.",
    },
}


def historico_txt(modo: str, estado: str, janela: str = "", medido_ate: str = "") -> str:
    """Frase canônica de um estado do histórico medido, no vocabulário do modo."""
    h = HISTORICO.get(modo if modo in HISTORICO else "educacional", HISTORICO["educacional"])
    frase = h.get(estado) or h["nunca_medido"]
    return frase.replace("{janela}", janela or "?").replace("{medidoAte}", medido_ate or "?")


def entrada_auto_txt(modo: str, estado: str, setup: str = "", janela_ref: str = "") -> str:
    """Frase de transparência do gate por setup — falha FECHADA: qualquer
    estado que não seja literalmente 'disponivel' cai em `por_setup_bloqueado`,
    nunca anuncia entrada automática disponível por engano."""
    e = ENTRADA_AUTO.get(modo if modo in ENTRADA_AUTO else "educacional", ENTRADA_AUTO["educacional"])
    chave = "por_setup_disponivel" if estado == "disponivel" else "por_setup_bloqueado"
    frase = e[chave]
    return frase.replace("{setup}", setup or "?").replace("{janelaRef}", janela_ref or "?")


def decisoes_txt(modo: str) -> str:
    """Enum de decisão do modo, como string 'A | B | C' para o contrato."""
    v = vocab.get(modo, vocab["educacional"])
    return " | ".join("'" + d + "'" for d in v["decisoes"])


def conclusoes_txt() -> str:
    return " | ".join("'" + c + "'" for c in CONCLUSOES)


def conclusoes_edu_txt() -> str:
    return " | ".join("'" + c + "'" for c in CONCLUSOES_EDU)


# Diretriz de ENSINO (objetivo do produto no modo Estudo): a análise não é um
# veredito com glossário ao lado — é a cadeia indicador → correlação → decisão.
# A confluência entre famílias JÁ vem calculada no pacote (families /
# confluenciaEntreFamilias em technical_models); aqui o modelo NARRA essa
# correlação em vez de só listar os modelos usados.
DIDATICA = "\n".join([
    "# Função de ensino (o objetivo do modo Estudo)",
    "O usuário está aqui para APRENDER a ler o ativo, não só para receber a decisão.",
    "A leitura vale quando ele consegue refazer o raciocínio sozinho no próximo papel.",
    "Ensine na ordem em que um operador pensa:",
    "1. O que cada indicador disponível marca AGORA — com o número do pacote e o que",
    "   esse valor significa NESTE ativo (não a definição de manual).",
    "2. Como eles se relacionam: quais CONFIRMAM a mesma leitura e quais DIVERGEM, e o",
    "   que a divergência indica.",
    "3. Como essa combinação PRODUZ a leitura — a decisão é consequência da confluência;",
    "   mostre o dado que puxou para cada lado.",
    "4. O que MUDARIA a leitura: o nível ou a condição que quebra a tese.",
    "Use `families` e `confluenciaEntreFamilias` do pacote como esqueleto do passo 2",
    "(o viés por família e a síntese já vêm calculados). O fundamento entra como filtro",
    "de qualidade do negócio: explique o que o score diz e por que não muda o timing.",
    "Termo técnico vem depois da ideia em linguagem simples, uma vez cada.",
])


def num_br(valor) -> str:
    """Formata número no padrão pt-BR (vírgula decimal, ponto de milhar) SEM
    depender de `locale` do sistema — o container do Railway não tem pt_BR
    instalado, e `locale.setlocale` não é portável entre ambientes de deploy.
    Todo número interpolado nas frases de `OPCOES_LASTREADAS` passa por aqui —
    fonte única de formatação monetária desta fase, mesmo padrão de "backend
    calcula, front recebe pronto" já vigente no resto do módulo."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "0,00"
    neg = v < 0
    v = abs(v)
    inteiro, frac = f"{v:,.2f}".split(".")
    inteiro = inteiro.replace(",", ".")
    out = f"{inteiro},{frac}"
    return ("-" + out) if neg else out


# --- Vocabulário das operações lastreadas por modo (Fase 14, Plano 03) ------
# ÚNICO lugar onde a frase da proposta de venda coberta/put de proteção nasce
# — o front nunca compõe manchete de proposta (mesma regra já vigente para
# TIMING/HISTORICO acima; guardrail CVM: a IA explica, nunca substitui a
# manchete do motor determinístico).
#
# Registro por modo: `operador` fala como mesa (verbo de ordem, primeira
# pessoa da mesa); `educacional` descreve CONDIÇÃO no condicional ("se você
# tivesse..."), nunca ordem — mesma distinção de `vocab`/`TIMING` acima.
# `sem_lastro`/`sem_setup`/`degradado`/`caixa_insuficiente`/`liquidacao_
# forcada` são texto FACTUAL, idêntico nos dois modos (mesmo padrão de
# `HISTORICO["insuficiente"]`/`ENTRADA_AUTO["contraste"]`: fato não muda de
# registro, só decisão/oferta muda).
OPCOES_LASTREADAS = {
    "operador": {
        "call_coberta": "Vender {n} call(s) de {ticker} strike {strike} por R$ {premioTotal}.",
        "put_protecao": "Comprar {n} put(s) de {ticker} strike {strike} por R$ {premioTotal}.",
        # Fase 16, Plano 02 (LIB-03): collar não carrega valor em reais na
        # frase — diferente de call_coberta/put_protecao, o resultado
        # líquido do collar tem SINAL (débito quando a put custa mais que a
        # call, crédito no caso contrário) e `opcoes_lastreadas_txt` interpola
        # por `str.replace` sem condicional; uma frase única com valor
        # sinalizado imprimiria "por R$ -12,00" em metade dos casos. Custo
        # líquido/breakeven/ganho-perda máximos viajam em
        # caixa/estrutura/chips (Plano 16-03 preenche, Fase 17 exibe).
        # "Abate o custo" é verdade nos dois sentidos (abatimento total ou
        # parcial); "financiada pelo prêmio da call" seria falsa quando o
        # abatimento é parcial — afirmar financiamento completo é a promessa
        # que o CLAUDE.md proíbe.
        "collar": "Vender {n} call(s) de {ticker} strike {strikeCall} e comprar {n} put(s) strike {strikePut} sobre {qtyAcoes} ação(ões) — trava protetora: o prêmio da call abate o custo da put.",
        "sem_lastro": "Sem posição em {ticker} na carteira — venda coberta e put de proteção exigem uma posição real do ativo-lastro.",
        "sem_setup": "A leitura técnica de {ticker} não indica venda coberta nem put de proteção agora. A cadeia completa continua disponível abaixo.",
        "degradado": "Proposta indisponível — cotação de opções degradada.",
        "caixa_insuficiente": "Caixa insuficiente para o prêmio desta put de proteção.",
        "liquidacao_forcada": "Esta call de {ticker} venceu dentro do dinheiro e não foi fechada a tempo — liquidada em dinheiro pelo valor intrínseco (R$ {valor}). Sua posição em ações não foi alterada.",
    },
    "educacional": {
        "call_coberta": "Se você tivesse vendido esta call coberta agora, receberia um prêmio de R$ {premioTotal} e travaria {qtyAcoes} ação(ões) até a recompra ou o vencimento.",
        "put_protecao": "Se você tivesse comprado esta put de proteção agora, pagaria R$ {premioTotal} para proteger {qtyAcoes} ação(ões) contra queda abaixo de R$ {strike}.",
        # Fase 16, Plano 02 (LIB-03): mesma decisão de não sinalizar valor em
        # reais do registro operador acima (ver comentário lá) — condição
        # descrita, nunca ordem, e sem promessa de financiamento completo.
        "collar": "Se você tivesse montado esta trava protetora agora, {qtyAcoes} ação(ões) ficariam protegidas contra queda abaixo de R$ {strikePut} e o ganho ficaria limitado a partir de R$ {strikeCall} — o prêmio da call vendida abate o custo da put comprada.",
        "sem_lastro": "Sem posição em {ticker} na carteira — venda coberta e put de proteção exigem uma posição real do ativo-lastro.",
        "sem_setup": "A leitura técnica de {ticker} não indica venda coberta nem put de proteção agora. A cadeia completa continua disponível abaixo.",
        "degradado": "Proposta indisponível — cotação de opções degradada.",
        "caixa_insuficiente": "Caixa insuficiente para o prêmio desta put de proteção.",
        "liquidacao_forcada": "Esta call de {ticker} venceu dentro do dinheiro e não foi fechada a tempo — liquidada em dinheiro pelo valor intrínseco (R$ {valor}). Sua posição em ações não foi alterada.",
    },
}

# `opcoes_lastreadas.propor` (Task 2) tem 3 motivos de ausência distintos que
# compartilham a MESMA leitura factual ("a leitura técnica não pede a
# operação agora") — `tendencia_de_alta` é sinônimo aceito mas não emitido
# hoje pelo motor (mantido pela paridade nomeada no 14-UI-SPEC.md). Alias
# aqui, não 3 entradas idênticas no dict acima — uma fonte de texto, várias
# chaves de motivo apontando pra ela.
_OPCOES_LASTREADAS_ALIASES_SEM_SETUP = ("tendencia_de_alta", "sem_contrato_liquido", "sem_vencimento_elegivel")


def opcoes_lastreadas_txt(modo: str, chave: str, **dados) -> str:
    """Frase canônica de uma operação lastreada (ou do motivo de ausência),
    no vocabulário do modo. Modo desconhecido cai em `educacional` (mesma
    degradação definida de `timing_txt`/`historico_txt`). Interpolação por
    `str.replace` de marcadores `{...}` — todo valor numérico chega já
    formatado por `num_br()` (chamador, não aqui)."""
    d = OPCOES_LASTREADAS.get(modo if modo in OPCOES_LASTREADAS else "educacional", OPCOES_LASTREADAS["educacional"])
    chave_canonica = "sem_setup" if chave in _OPCOES_LASTREADAS_ALIASES_SEM_SETUP else chave
    frase = d.get(chave_canonica) or d["sem_setup"]
    for k, v in dados.items():
        frase = frase.replace("{" + str(k) + "}", str(v))
    return frase
