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


# Retorno acumulado (quick 261006-dvf, 2026-10-06): texto por ORIGEM da base
# (`store.resolver_base_serie`). Espelho byte a byte em `web/src/copy.js`
# (`COPY[modo].retornoAcumulado`), travado por test_vocabulario_espelho.mjs.
# `carimbada_reinicio` = a janela recomeçou num aporte/retirada (inicio > 0):
# a frase NÃO pode dizer "desde o capital inicial". Estados sem base dizem
# "Não há dados suficientes para concluir." — nunca um número inventado.
RETORNO_ACUMULADO = {
    "operador": {
        "carimbada": "Retorno acumulado desde o capital inicial: {pct}.",
        "carimbada_reinicio": "Retorno acumulado desde {desde} (capital alterado): {pct}. Aporte ou retirada não conta como retorno.",
        "primeiro_registro": "Retorno acumulado desde {desde} (1º dia registrado): {pct}. Capital inicial da série não registrado.",
        "sem_serie": "Não há dados suficientes para concluir. Sem dia de patrimônio registrado.",
        "inconsistente": "Não há dados suficientes para concluir. Bases da série inconsistentes, sem ajuste de capital registrado.",
    },
    "educacional": {
        "carimbada": "Desde o capital inicial desta simulação, o retorno acumulado é de {pct}.",
        "carimbada_reinicio": "Desde {desde}, quando o capital da simulação foi alterado, o retorno acumulado é de {pct}. Aporte ou retirada não conta como retorno.",
        "primeiro_registro": "Desde {desde}, o primeiro dia registrado, o retorno acumulado é de {pct}. O capital inicial desta série não foi registrado, por isso a conta parte desse dia.",
        "sem_serie": "Não há dados suficientes para concluir. Ainda não há nenhum dia de patrimônio registrado nesta simulação.",
        "inconsistente": "Não há dados suficientes para concluir. A série de patrimônio registra bases diferentes sem um ajuste de capital que as explique.",
    },
}


def retorno_acumulado_txt(modo: str, estado: str, pct: str = "", desde: str = "") -> str:
    """Frase canônica do retorno acumulado por origem da base; estado
    desconhecido cai em `sem_serie` (nunca afirma número)."""
    r = RETORNO_ACUMULADO.get(modo if modo in RETORNO_ACUMULADO else "educacional", RETORNO_ACUMULADO["educacional"])
    frase = r.get(estado) or r["sem_serie"]
    return frase.replace("{pct}", pct or "—").replace("{desde}", desde or "?")


# Legenda da curva da Evolução (quick 261006-qre, 2026-10-06): o trecho ANTERIOR
# ao início da janela do retorno é desenhado pontilhado — patrimônio registrado,
# sem base de retorno. Espelho byte a byte em `web/src/copy.js`
# (`COPY[modo].curvaEvolucao`), travado por test_vocabulario_espelho.mjs.
CURVA_EVOLUCAO = {
    "operador": {
        "antes_da_base": "Antes de {desde} (pontilhado): só patrimônio registrado, fora da base do retorno.",
    },
    "educacional": {
        "antes_da_base": "Antes de {desde} a linha fica pontilhada: mostra só o patrimônio registrado, porque o retorno acumulado só é medido a partir desse dia.",
    },
}


def curva_evolucao_txt(modo: str, chave: str = "antes_da_base", desde: str = "") -> str:
    """Legenda do trecho pré-janela da curva; chave desconhecida cai em
    `antes_da_base`, modo desconhecido em educacional."""
    r = CURVA_EVOLUCAO.get(modo if modo in CURVA_EVOLUCAO else "educacional", CURVA_EVOLUCAO["educacional"])
    frase = r.get(chave) or r["antes_da_base"]
    return frase.replace("{desde}", desde or "?")


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


# --- Reconciliação sinal técnico × histórico medido (HIER-03) --------------
# O padrão bateu os critérios (sinal técnico, setups.py) e o histórico medido
# (signal_ledger, ADR-017 Bloco 1) são DUAS perguntas diferentes — este
# vocabulário é a frase que conecta as duas sem fundi-las num veredito só
# (guardrail ADR-017: decisão × elegibilidade nunca em síntese). `n`/`janela`
# nunca são omitidos nem inventados (D-08); Estudo explica o "por que
# importa" (duas orações), Operador é fato curto com os três números.
RECONCILIACAO_ELEGIBILIDADE = {
    "operador": {
        "elegivel": "Critérios ok · vantagem medida (n={n}, {janela}, {expR})",
        "inelegivel": "Critérios ok · sem vantagem medida (n={n}, {janela}, {expR})",
        "insuficiente": "Critérios ok · amostra insuficiente (n={n} — pouco para medir)",
        "nunca_medido": "Critérios ok · sem histórico medido",
        "aposentado": "Padrão identificado · sem vantagem medida em 15 anos (ADR-016)",
    },
    "educacional": {
        "elegivel": "O padrão bateu os critérios, e em {n} ocorrências na janela {janela} houve vantagem medida.",
        "inelegivel": "O padrão bateu os critérios, mas em {n} ocorrências na janela {janela} não houve vantagem medida.",
        "insuficiente": "O padrão bateu os critérios; só {n} ocorrências — pouco para medir.",
        "nunca_medido": "O padrão bateu os critérios; ainda sem histórico medido.",
        "aposentado": "Padrão identificado; sem vantagem medida em 15 anos (ADR-016).",
    },
}

# Cláusula "por que importa" (D-11): só o Modo Estudo a exibe, e é TOCÁVEL
# no front (abre setorId="analise" → conceito "confluencia", existente —
# nenhum conceito novo). String FIXA, sem interpolação — por isso não é uma
# função, é o mesmo padrão de `PRINCIPIOS`/frase única do módulo. O front
# nunca compõe esta frase a partir de outra coisa; ela vem pronta de aqui,
# como QUALQUER texto desta camada (regra da casa, didatica-boris/SKILL.md).
RECONCILIACAO_POR_QUE_IMPORTA = "sinal técnico e histórico medido são coisas diferentes"


def reconciliacao_elegibilidade_txt(modo: str, estado: str, n=None, janela: str = "", exp_r=None) -> str:
    """Frase de reconciliação por modo/estado — só o FATO (sem a cláusula
    "por que importa", que o front busca separado, ver
    RECONCILIACAO_POR_QUE_IMPORTA, e só anexa no Estudo).

    REVERSÃO DELIBERADA (2026-09-27, Fase 43, DP-3, checkpoint 43-05): a
    ausência de um dado que a frase do `estado` exige não vira mais o
    placeholder "?" — a frase inspeciona os placeholders que contém
    (`{n}`, `{janela}`, `{expR}`) e, se QUALQUER um deles não tem valor
    (n é None; janela vazia/None; exp_r é None), a função devolve a frase
    `nunca_medido` do mesmo modo, sem interpolação. `n = 0` é valor
    presente (não cai)."""
    d = RECONCILIACAO_ELEGIBILIDADE.get(modo if modo in RECONCILIACAO_ELEGIBILIDADE else "educacional",
                                         RECONCILIACAO_ELEGIBILIDADE["educacional"])
    frase = d.get(estado) or d["nunca_medido"]
    falta_n = "{n}" in frase and n is None
    falta_janela = "{janela}" in frase and not janela
    falta_expr = "{expR}" in frase and exp_r is None
    if falta_n or falta_janela or falta_expr:
        return d["nunca_medido"]
    exp_txt = "" if exp_r is None else (("+" if exp_r >= 0 else "−") + f"{abs(exp_r):.3f}".replace(".", ",") + "R")
    return (frase
            .replace("{n}", str(n) if n is not None else "")
            .replace("{janela}", janela or "")
            .replace("{expR}", exp_txt))


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


def num_br_inteiro(valor) -> str:
    """`num_br` sem a parte decimal — volume de contrato é sempre um inteiro
    (unidades negociadas), e "300,00 unidades" seria falso precisão nenhuma
    justifica. Reusa `num_br` para o ponto de milhar em vez de duplicar a
    lógica de agrupamento (quick 260908-ldg, frase de consentimento de
    liquidez)."""
    return num_br(valor).split(",")[0]


def num_br_percentual(valor) -> str:
    """Percentual pt-BR sem decimais para o spread do livro de opções
    (`{spread}` de `LIQUIDEZ_FRAGMENTOS["livro"]`) — "66%", nunca "66,47%":
    a frase de consentimento cita a ordem de grandeza, não a casa decimal
    (quick 260908-ldg)."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "0%"
    return f"{round(v):d}%"


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
        # ATUALIZADO 2026-09-07 (quick 260907-x69): fechar_call_coberta e
        # fechar_put_protecao são frases DISTINTAS da abertura acima, porque a
        # MESMA posição descreve ações OPOSTAS nos dois momentos — abrir uma
        # call coberta VENDE a call; fechá-la RECOMPRA. Abrir uma put de
        # proteção COMPRA a put; fechá-la VENDE (e credita). Antes desta
        # correção, `proposta_fechar` reusava a frase de abertura e o card de
        # fechamento de uma put dizia "Comprar 1 put(s)…" acima de um botão
        # que na verdade VENDE — achado ao vivo em staging (iPhone, Modo
        # Operador, put ABEV3 strike 30,00).
        "fechar_call_coberta": "Recomprar {n} call(s) de {ticker} strike {strike} por R$ {premioTotal} — destrava {qtyAcoes} ação(ões).",
        "fechar_put_protecao": "Vender {n} put(s) de {ticker} strike {strike} por R$ {premioTotal} — encerra a proteção de {qtyAcoes} ação(ões).",
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
        # Fase 31, Plano 01 (D-05): quarta estrutura da varredura de
        # oportunidades — compra de call a seco (mesma mecânica da Fase 29,
        # `store.buy_option`), sem nenhuma ação como lastro. Esta frase só é
        # emitida pela varredura quando `permitirOpcaoADescoberto` está
        # ligado na conta; o gate mora em `opcoes_curadoria.
        # candidatos_da_posicao` (parâmetro `permitir_a_descoberto`), não
        # aqui — este dict só guarda o TEXTO, nunca a decisão de exibir.
        # Fala como mesa (verbo de ordem), risco máximo nomeado explícito:
        # sem promessa de lucro/enriquecimento (princípios 6 e 8 do
        # CLAUDE.md).
        "opcao_a_descoberto": "Comprar {n} call(s) de {ticker} strike {strike} a seco por R$ {premioTotal} — sem lastro em ações: o risco máximo é todo o prêmio pago.",
        "sem_lastro": "Sem posição em {ticker} na carteira — venda coberta e put de proteção exigem uma posição real do ativo-lastro.",
        "sem_setup": "A leitura técnica de {ticker} não indica venda coberta nem put de proteção agora. A cadeia completa continua disponível abaixo.",
        "degradado": "Proposta indisponível — cotação de opções degradada.",
        "caixa_insuficiente": "Caixa insuficiente para o prêmio desta put de proteção.",
        # Fase 44, D-06/D-07: sem_contrato_liquido e sem_vencimento_elegivel
        # deixaram de ser alias de sem_setup (a frase de sem_setup fala de
        # leitura técnica e era falsa para eles); premio_indisponivel,
        # contrato_fora_da_cadeia e sem_mercado são os motivos distinguíveis
        # do encerramento. Fato, não oferta: texto idêntico nos dois modos.
        "sem_contrato_liquido": "Existe cadeia de opções de {ticker}, mas nenhum contrato no strike e no vencimento que a estrutura pede negocia o bastante para ter um preço confiável.",
        "sem_vencimento_elegivel": "Nenhum vencimento futuro de opção de {ticker} foi lido — sem vencimento futuro, nenhuma estrutura nova é montada.",
        "premio_indisponivel": "Sem prêmio cotado para a opção aberta de {ticker} agora — o encerramento não é proposto sem preço, e nada é estimado no lugar.",
        "contrato_fora_da_cadeia": "O contrato aberto de {ticker} não veio na cadeia de opções consultada agora — sem ele, o encerramento não é proposto.",
        "sem_mercado": "As opções abertas de {ticker} estão na faixa SEM MERCADO — o preço da tela não seria o preço real de uma ordem.",
        "liquidacao_forcada": "Esta call de {ticker} venceu dentro do dinheiro e não foi fechada a tempo — liquidada em dinheiro pelo valor intrínseco (R$ {valor}). Sua posição em ações não foi alterada.",
        # Quick 260908-ldg (2026-09-08): consentimento de liquidez DIFÍCIL
        # (30-54). O SERVIDOR exige `aceitaLiquidezDificil: true` no corpo
        # quando a pior perna cai aqui (main.py, Task 2) — a UI exibe este
        # texto VERBATIM num `window.confirm` (App.jsx, Task 3), nunca
        # compõe a frase. "Continuar?" é o único ponto do módulo com
        # pergunta de confirmação — o registro operador fala como mesa e
        # pede a decisão explícita.
        "liquidez_dificil": "Liquidez DIFÍCIL ({score}/100): {atividade}, {livro}. O preço simulado é o do último negócio; no mercado real sua ordem poderia não ser atendida a esse preço. Continuar?",
    },
    "educacional": {
        "call_coberta": "Se você tivesse vendido esta call coberta agora, receberia um prêmio de R$ {premioTotal} e travaria {qtyAcoes} ação(ões) até a recompra ou o vencimento.",
        "put_protecao": "Se você tivesse comprado esta put de proteção agora, pagaria R$ {premioTotal} para proteger {qtyAcoes} ação(ões) contra queda abaixo de R$ {strike}.",
        # ATUALIZADO 2026-09-07 (quick 260907-x69): registro condicional do
        # FECHAMENTO — mesma correção do registro operador acima, sem verbo
        # de ordem.
        "fechar_call_coberta": "Se você encerrasse esta call coberta agora, pagaria R$ {premioTotal} para recomprá-la e {qtyAcoes} ação(ões) voltariam a ficar livres.",
        "fechar_put_protecao": "Se você encerrasse esta put de proteção agora, receberia R$ {premioTotal} pela venda e {qtyAcoes} ação(ões) deixariam de estar protegidas contra queda abaixo de R$ {strike}.",
        # Fase 16, Plano 02 (LIB-03): mesma decisão de não sinalizar valor em
        # reais do registro operador acima (ver comentário lá) — condição
        # descrita, nunca ordem, e sem promessa de financiamento completo.
        "collar": "Se você tivesse montado esta trava protetora agora, {qtyAcoes} ação(ões) ficariam protegidas contra queda abaixo de R$ {strikePut} e o ganho ficaria limitado a partir de R$ {strikeCall} — o prêmio da call vendida abate o custo da put comprada.",
        # Fase 31, Plano 01 (D-05): mesmo registro condicional de
        # `put_protecao` acima — condição, nunca ordem. Ver comentário do
        # registro `operador` sobre o gate (`permitirOpcaoADescoberto`).
        "opcao_a_descoberto": "Se você tivesse comprado esta call a seco agora, pagaria R$ {premioTotal} e perderia todo esse valor se a opção virasse pó no vencimento — nenhuma ação sua entra como lastro.",
        "sem_lastro": "Sem posição em {ticker} na carteira — venda coberta e put de proteção exigem uma posição real do ativo-lastro.",
        "sem_setup": "A leitura técnica de {ticker} não indica venda coberta nem put de proteção agora. A cadeia completa continua disponível abaixo.",
        "degradado": "Proposta indisponível — cotação de opções degradada.",
        "caixa_insuficiente": "Caixa insuficiente para o prêmio desta put de proteção.",
        # Fase 44, D-06/D-07: sem_contrato_liquido e sem_vencimento_elegivel
        # deixaram de ser alias de sem_setup (a frase de sem_setup fala de
        # leitura técnica e era falsa para eles); premio_indisponivel,
        # contrato_fora_da_cadeia e sem_mercado são os motivos distinguíveis
        # do encerramento. Fato, não oferta: texto idêntico nos dois modos.
        "sem_contrato_liquido": "Existe cadeia de opções de {ticker}, mas nenhum contrato no strike e no vencimento que a estrutura pede negocia o bastante para ter um preço confiável.",
        "sem_vencimento_elegivel": "Nenhum vencimento futuro de opção de {ticker} foi lido — sem vencimento futuro, nenhuma estrutura nova é montada.",
        "premio_indisponivel": "Sem prêmio cotado para a opção aberta de {ticker} agora — o encerramento não é proposto sem preço, e nada é estimado no lugar.",
        "contrato_fora_da_cadeia": "O contrato aberto de {ticker} não veio na cadeia de opções consultada agora — sem ele, o encerramento não é proposto.",
        "sem_mercado": "As opções abertas de {ticker} estão na faixa SEM MERCADO — o preço da tela não seria o preço real de uma ordem.",
        "liquidacao_forcada": "Esta call de {ticker} venceu dentro do dinheiro e não foi fechada a tempo — liquidada em dinheiro pelo valor intrínseco (R$ {valor}). Sua posição em ações não foi alterada.",
        # Quick 260908-ldg (2026-09-08): mesma condição do registro operador,
        # sem verbo de ordem nem "Continuar?" — descreve a condição, como o
        # resto do vocabulário educacional deste dict.
        "liquidez_dificil": "Esta opção tem liquidez DIFÍCIL ({score}/100): {atividade}, {livro}. O preço simulado é o do último negócio — no mercado real, uma ordem a esse preço poderia não ser atendida.",
    },
}

# Fragmentos factuais do consentimento de liquidez (quick 260908-ldg) — iguais
# nos dois modos, mesmo precedente de `HISTORICO["insuficiente"]`:
# atividade/livro do dia são FATO de mercado, não decisão/oferta que muda de
# registro por modo. `_bloco_liquidez` (opcoes_lastreadas.py) escolhe o
# fragmento certo e interpola em `liquidez_dificil` acima; o texto visível
# nasce inteiro aqui.
LIQUIDEZ_FRAGMENTOS = {
    "atividade": "{volume} unidades negociadas hoje",
    "atividade_sem_negocio": "sem negócio registrado hoje",
    "livro": "spread {spread}",
    "livro_ausente": "sem livro publicado",
}

# `opcoes_lastreadas.propor` (Task 2) tem 3 motivos de ausência distintos que
# compartilham a MESMA leitura factual ("a leitura técnica não pede a
# operação agora") — `tendencia_de_alta` é sinônimo aceito mas não emitido
# hoje pelo motor (mantido pela paridade nomeada no 14-UI-SPEC.md). Alias
# aqui, não 3 entradas idênticas no dict acima — uma fonte de texto, várias
# chaves de motivo apontando pra ela.
#
# Fase 44 (D-06) — REVERSÃO DELIBERADA: `sem_contrato_liquido` e
# `sem_vencimento_elegivel` saíram desta tupla e ganharam frase própria acima;
# colapsá-los em `sem_setup` afirmava "a leitura técnica não indica" quando o
# motivo real era liquidez/prazo. Só `tendencia_de_alta` segue alias.
_OPCOES_LASTREADAS_ALIASES_SEM_SETUP = ("tendencia_de_alta",)


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

# --- Estrutura por ativo (Fase 44, ESTR-06) ----------------------------------
# Fonte única das frases da leitura de estrutura por ativo (nome, estado,
# faixa piso/teto, stop, incompleto, descoberta, encerrar bloqueado, origem
# last). Espelhada byte a byte em `web/src/copy.js` (`estruturaPosicao`),
# guardião `web/tests/test_estrutura_espelho.mjs`. O Estudo descreve CONDIÇÃO
# (sem verbo de ordem); o Operador fala como mesa. Âncoras proibidas:
# "trava protetora" e "abate o custo". A Fase 45 decidiu NÃO tocar a manchete
# `collar` de OPCOES_LASTREADAS (texto regulado, guardrail CVM, premissa P1) e
# trocou a âncora só nas chaves visíveis do copy.js.
# Formato rígido p/ o guardião JS: um par por linha, sem aspas internas.
ESTRUTURA_POSICAO = {
    "operador": {
        "nome_call_coberta": "call coberta",
        "nome_put_protecao": "put de proteção",
        "nome_collar": "collar",
        "nome_fora_da_biblioteca": "Fora da biblioteca (call coberta, put de proteção, collar) — pernas listadas, sem faixa.",
        "estado_vigente": "Vigente · vence {vencimento} ({dias} dia(s)).",
        "estado_vigente_sem_data": "Vencimento não informado — prazo indeterminado.",
        "estado_perto_vencimento": "Vence em {dias} dia(s) ({vencimento}) — decidir: encerrar ou deixar vencer.",
        "estado_exercicio_provavel": "Exercício provável: strike R$ {strike} dentro do dinheiro (ação a R$ {spot}).",
        "estado_premio_indisponivel": "Prêmio indisponível: {pernas}. Resultado total suspenso.",
        "estado_vencida": "Vencida em {vencimento}.",
        "aberta_sem_proposta": "Aberta, sem proposta de encerramento. {motivo}",
        "faixa_piso": "Piso R$ {piso} · perda máx. R$ {perdaMaxima}.",
        "faixa_teto": "Teto R$ {teto} · ganho máx. R$ {ganhoMaximo}.",
        "faixa_sem_piso": "Sem piso · perda máx. R$ {perdaMaxima} (ação a zero).",
        "faixa_sem_teto": "Sem teto · ganho não limitado pela estrutura.",
        "faixa_teto_parcial": "Teto R$ {teto} só em {qtd} de {qtdBase} ações · ganho do restante não limitado.",
        "faixa_piso_sem_perda": "Piso R$ {piso} em {qtd} ações · perda máx. não calculável.",
        "faixa_vencimentos_diferentes": "Vencimentos diferentes ({vencimentos}) — faixa não calculada.",
        "faixa_perna_sem_lastro": "Call vendida sem lastro em {quantidade} — perda ilimitada, faixa não calculada.",
        "faixa_sem_acoes": "Sem ações de {ticker} — faixa não calculada.",
        "faixa_dados_insuficientes": "Faixa indisponível — dados insuficientes.",
        "descoberta_put": "Put excedente em {quantidade} — faixa na parte coberta ({qtdBase}).",
        "stop_protegida": "Proteção pela put R$ {piso} no vencimento.",
        "resultado_incompleto": "Resultado total indisponível — sem cotação: {pernas}.",
        "acao_sem_cotacao": "Ação sem cotação — resultado suspenso.",
        "resultado_dados_invalidos": "Resultado total indisponível — dados inválidos: {pernas}.",
        "encerrar_premio_indisponivel": "Encerrar bloqueado — sem prêmio: {pernas}.",
        "encerrar_vencida": "Encerrar indisponível — vencida em {vencimento}.",
        "origem_last": "{perna}: prêmio pelo último negócio (sem oferta).",
    },
    "educacional": {
        "nome_call_coberta": "call coberta",
        "nome_put_protecao": "put de proteção",
        "nome_collar": "collar",
        "nome_fora_da_biblioteca": "Estrutura fora das três que o simulador lê (call coberta, put de proteção e collar). As pernas aparecem abaixo, sem faixa calculada.",
        "estado_vigente": "Estrutura vigente: faltam {dias} dia(s) para o vencimento de {vencimento}.",
        "estado_vigente_sem_data": "Vencimento não informado para esta estrutura. Não há dados suficientes para concluir o prazo.",
        "estado_perto_vencimento": "Faltam {dias} dia(s) para o vencimento de {vencimento}. Perto do vencimento o prêmio muda rápido, e a estrutura pede uma decisão: encerrar ou deixar vencer.",
        "estado_exercicio_provavel": "A opção de strike R$ {strike} está dentro do dinheiro com a ação a R$ {spot}. Se o vencimento fosse hoje, ela seria exercida.",
        "estado_premio_indisponivel": "Sem cotação para {pernas} agora. O resultado total não é calculado e nada é estimado no lugar.",
        "estado_vencida": "O vencimento de {vencimento} já passou. Esta estrutura não está mais vigente.",
        "aberta_sem_proposta": "A estrutura continua aberta na sua carteira, mas o encerramento não pode ser proposto agora. {motivo}",
        "faixa_piso": "Piso no vencimento: abaixo de R$ {piso}, a put protege as {qtd} ações — a perda máxima fica em R$ {perdaMaxima}.",
        "faixa_teto": "Teto no vencimento: acima de R$ {teto}, a call vendida limita o ganho das {qtd} ações a R$ {ganhoMaximo}.",
        "faixa_sem_piso": "Sem piso: a call coberta não protege contra queda. Se a ação fosse a zero, a perda seria de R$ {perdaMaxima}.",
        "faixa_sem_teto": "Sem teto: a put de proteção não limita o ganho das ações se o preço subir.",
        "faixa_teto_parcial": "Teto parcial: a call vendida (strike R$ {teto}) limita o ganho de {qtd} das {qtdBase} ações. O ganho das demais não tem limite se o preço subir.",
        "faixa_piso_sem_perda": "Piso no vencimento: abaixo de R$ {piso}, a put protege {qtd} ações. Não há dados suficientes para concluir a perda máxima.",
        "faixa_vencimentos_diferentes": "As pernas vencem em datas diferentes ({vencimentos}). Sem uma data comum, a faixa no vencimento não pode ser calculada — nada é aproximado.",
        "faixa_perna_sem_lastro": "Há {quantidade} call(s) vendida(s) sem ações para cobrir. Nesse trecho a perda não tem limite, por isso a faixa não é calculada.",
        "faixa_sem_acoes": "Não há ações de {ticker} na carteira: as pernas aparecem abaixo, mas não há faixa de estrutura a calcular.",
        "faixa_dados_insuficientes": "Não há dados suficientes para concluir a faixa no vencimento.",
        "descoberta_put": "{quantidade} put(s) protegem mais ações do que você tem. A faixa considera só a parte coberta ({qtdBase} ações).",
        "stop_protegida": "A put de strike R$ {piso} limita a perda desta posição no vencimento — o limite vem dela, não de um stop de preço.",
        "resultado_incompleto": "Resultado total indisponível: falta cotação de {pernas}. Aparecem separados só o resultado das ações e o das pernas cotadas.",
        "acao_sem_cotacao": "Sem cotação da ação agora: o resultado das ações e o total não são calculados.",
        "resultado_dados_invalidos": "Resultado total indisponível: os dados de {pernas} estão incompletos ou inválidos (lado, quantidade ou prêmio de entrada). Nada é estimado no lugar.",
        "encerrar_premio_indisponivel": "Encerrar fica bloqueado: sem prêmio cotado para {pernas}, não há preço para o simulador usar.",
        "encerrar_vencida": "Encerrar não se aplica: o vencimento de {vencimento} já passou.",
        "origem_last": "Prêmio de {perna} pelo último negócio: não há oferta no lado que fecha a posição.",
    },
}


def estrutura_posicao_txt(modo: str, chave: str, **dados):
    """Frase canônica da leitura de estrutura por ativo. Modo fora de
    `ESTRUTURA_POSICAO` (inclui "estudo") degrada para `educacional`; chave
    desconhecida devolve `None` (falha fechada — nunca uma frase errada no
    lugar). Interpolação por `str.replace`, igual a `opcoes_lastreadas_txt`."""
    d = ESTRUTURA_POSICAO.get(modo if modo in ESTRUTURA_POSICAO else "educacional")
    frase = d.get(chave)
    if frase is None:
        return None
    for k, v in dados.items():
        frase = frase.replace("{" + str(k) + "}", str(v))
    return frase


# --- Card de posição estruturada (Fase 45, CARD-01/04/05/06, D-03/D-11) ------
# Frases de voz do card estruturado. Dict SEPARADO de ESTRUTURA_POSICAO para não
# quebrar o guardião de conjunto exato de chaves da Fase 44 (P8). Espelhado byte
# a byte em `COPY[modo].estruturaCard` (web/src/copy.js); guardião
# `web/tests/test_estrutura_card_espelho.mjs`. Âncoras proibidas: "trava
# protetora" e "abate o custo" (o collar se chama "collar").
# Formato rígido p/ o guardião JS: um par por linha, sem aspas internas.
ESTRUTURA_CARD = {
    "operador": {
        "chip_estrutura": "ESTRUTURA · {nome}",
        "chip_estrutura_generica": "ESTRUTURA · OPÇÕES",
        "lendo": "Lendo a estrutura de opções…",
        "indisponivel": "Estrutura indisponível agora. Pernas abertas seguem na carteira — nada estimado.",
        "badge_travada_collar": "{qty} travada(s) · lastro da CALL do collar",
        "aviso_sem_stop": "Posição sem stop definido — defina em Editar stop/alvo ou peça a sugestão da IA.",
    },
    "educacional": {
        "chip_estrutura": "ESTUDO · {nome}",
        "chip_estrutura_generica": "ESTUDO · OPÇÕES",
        "lendo": "Lendo a estrutura de opções desta posição…",
        "indisponivel": "Não foi possível ler a estrutura de opções agora. As pernas abertas continuam na sua carteira, e nenhum valor é estimado no lugar.",
        "badge_travada_collar": "{qty} travada(s) · lastro da call do collar",
        "aviso_sem_stop": "Esta posição não tem stop definido. Defina em Editar stop/alvo ou peça a sugestão da IA.",
    },
}


def estrutura_card_txt(modo: str, chave: str, **dados):
    """Frase canônica do card estruturado. Modo fora de `ESTRUTURA_CARD`
    (inclui "estudo") degrada para `educacional`; chave desconhecida devolve
    `None`. Interpolação por `str.replace`."""
    d = ESTRUTURA_CARD.get(modo if modo in ESTRUTURA_CARD else "educacional")
    frase = d.get(chave)
    if frase is None:
        return None
    for k, v in dados.items():
        frase = frase.replace("{" + str(k) + "}", str(v))
    return frase

# --- Card de posição v6 (Fase 46, CART6-06/07, D-06/D-11/D-15) ----------------
# Frases do card de posição v6, por modo (CARTAO_POSICAO) e a camada didática
# só do Estudo (CARTAO_DIDATICA; D-11/D-12: texto determinístico, nunca LLM).
# Texto novo nasce AQUI e é espelhado byte a byte em `COPY[modo].cartaoPosicao`
# e `COPY.estudo.cartaoDidatica` (web/src/copy.js); guardião
# `web/tests/test_cartao_posicao_espelho.mjs`. Marcador `[[id]]` nos parágrafos
# didáticos = termo tocável (id = sufixo de `termo_<id>`). Estudo descreve
# condição (sem "vender"/"comprar" como verbo de ordem); âncoras proibidas:
# "trava protetora" e "abate o custo". Chaves neutras idênticas nos dois modos.
# Formato rígido p/ o guardião JS: um par por linha, sem aspas internas.
CARTAO_POSICAO = {
    "operador": {
        "face_acao": "Ação",
        "face_opcoes": "Opções ({n})",
        "face_grupo_aria": "Face do card {ticker}",
        "plano_titulo": "Plano da ação",
        "compras_titulo": "Compras ({n})",
        "ver": "Ver ▾",
        "ocultar": "Ocultar ▴",
        "compras_indisponivel": "Compras: indisponível nesta fonte",
        "compras_sem_detalhe": "Detalhes das compras não vieram nesta fonte — nada foi inferido.",
        "falta_definir": "Falta definir",
        "estado_sem_plano": "Sem stop e alvo — defina o plano",
        "avulsa_sem_acoes": "Sem ações deste ativo: só a opção está aberta.",
        "estado_falta_alvo": "Falta o alvo — plano incompleto",
        "estado_falta_stop": "Falta o stop — plano incompleto",
        "estado_abaixo_stop": "Abaixo do stop do plano",
        "estado_acima_alvo": "Acima do alvo do plano",
        "estado_dentro": "Dentro do plano",
        "estado_travadas_todas": "Ações travadas pela call · saída após encerrar",
        "estado_travadas_parcial": "{n} de {m} ações travadas · {k} livres",
        "extra_resultado_parcial": "Resultado parcial: um prêmio atual indisponível",
        "extra_cotacao_indisponivel": "Cotação atual indisponível nesta fonte",
        "plano_ia_definir": "Definir plano · IA",
        "plano_ia_completar": "Completar plano · IA",
        "plano_ia_ajustar": "Ajustar plano · IA",
        "reanalisar": "Reanalisar",
        "historico": "Histórico de análises ({n})",
        "kicker_ia": "✦ BÓRIS IA",
        "encerrar": "Encerrar opção em Opções",
        "atualizar": "↻ Atualizar",
        "origem_nao_informada": "Origem da cotação não informada",
        "sem_cenario": "Cenários não calculados para esta combinação. Os limites dependem do cálculo do app.",
        "conta_sem_formula": "Calculado pela camada de opções do app",
        "aguardando_calculo": "aguardando o cálculo do app",
        "piso": "Piso",
        "equilibrio_rotulo": "◆ Equilíbrio",
        "teto": "Teto",
        "sem_piso": "sem piso",
        "sem_teto": "sem teto",
        "agora": "agora",
        "hoje": "hoje",
        "faixa_titulo": "No vencimento ({ddmm})",
        "chip_hoje": "Hoje",
        "chip_equilibrio": "Equilíbrio",
        "chip_teto": "Teto",
        "chip_alta_forte": "Alta forte",
        "rr_atual": "R:R atual",
        "em_operacao": "Em operação",
        "do_capital": "Do capital",
        "cotacao_atual": "Cotação atual",
        "setup_entrada": "Setup de entrada",
        "gatilho_valido": "válido",
        "gatilho_invalidado": "invalidado",
        "nota_pm": "PM R$ {pm} = R$ {total} ÷ {qtd} ações (média ponderada).",
        "nota_pm_vendas": " Vendas parciais reduzem a quantidade, não o PM.",
        "editar_plano": "✎ Editar stop/alvo",
        "regua_aria": "{ticker}: stop R$ {stop}, alvo R$ {alvo}, preço médio R$ {pm}, agora {agora}.",
        "faixa_aria": "{ticker} no vencimento: piso {piso}, equilíbrio R$ {be}, teto {teto}, hoje {hoje}.",
        "leg_hoje": "┆ hoje {v}",
        "leg_be": "◆ BE {v}",
        "leg_k": "┆ K {v}",
        "leg_eixo": "eixo x: {lo} → {hi}",
        "cel_be": "BE",
        "cel_ate_be": "Até BE",
        "cel_ate_k": "Até K",
        "cel_ganho_max": "Ganho máx.",
        "cel_perda_max": "Perda máx.",
        "cel_lastro": "Lastro",
        "conta_be_call": "BE = PM − prêmio",
        "conta_ate_be": "Até BE = BE ÷ hoje − 1",
        "conta_ate_k": "Até K = K ÷ hoje − 1",
        "conta_ganho_call": "Ganho máx. = (K − BE) × qtd",
        "conta_perda_call": "Perda máx. = BE × qtd (ação a zero)",
        "conta_lastro": "Lastro = ações que cobrem a CALL vendida",
        "sim_aria": "Preço de {ticker} no vencimento",
        "sim_valuetext": "R$ {preco}; {resultado}; {zona}",
        "payoff_sem_custos": "sem custos",
        "zona_rotulo_perda_travada": "perda limitada",
        "zona_rotulo_prejuizo": "prejuízo",
        "zona_rotulo_ganho": "ganho",
        "zona_rotulo_ganho_travado": "ganho limitado",
        "saida_motivo_lastro": "Todas as ações estão travadas como lastro. Para sair do ativo, encerre a CALL vendida em Opções.",
        "rodape_fechar": "Fechar ▴",
        "rodape_abrir": "Detalhes e ações ▾",
        "saida": "Registrar saída",
        "saida_sem_livres": "Registrar saída · 0 ações livres",
        "apoio_saida": "Saída simulada com dinheiro virtual. Nenhuma ordem é enviada à corretora.",
        "sim_lead": "{ticker} em {ddmm}:",
        "sim_resultado": "resultado",
        "sim_metodo": "Sem custos. Resultado no vencimento.",
        "payoff_titulo": "Payoff no vencimento · {ddmm}",
        "payoff_aria": "Payoff de {ticker} no vencimento: prejuízo abaixo do BE R$ {be}; acima do teto R$ {teto} o resultado fica limitado ({ganhoMaximo}); perda máxima {perdaMaxima}.",
        "payoff_aria_sem_teto": "Payoff de {ticker} no vencimento: prejuízo abaixo do BE R$ {be}; sem teto; perda máxima {perdaMaxima}.",
        "zona_perda_travada": "Abaixo do piso R$ {piso}: perda limitada a R$ {perdaMaxima}.",
        "zona_prejuizo_sem_piso": "Abaixo do BE R$ {be}: prejuízo. Sem piso (ação a zero: perda de R$ {perdaMaxima}).",
        "zona_prejuizo_com_piso": "Entre o piso R$ {piso} e o BE R$ {be}: prejuízo, limitado pelo piso.",
        "zona_ganho": "Entre o BE R$ {be} e o teto R$ {teto}: o resultado acompanha a ação.",
        "zona_ganho_sem_teto": "Acima do BE R$ {be}, sem teto.",
        "zona_ganho_travado": "Acima do teto R$ {teto}: resultado limitado em R$ {ganhoMaximo}; ações entregues a R$ {teto}.",
        # 46-UAT (2026-10-01, G-01..G-06): card fechado rótulo/valor, chips e faixa ancorada
        "legenda_resultado": "resultado",
        "legenda_resultado_variacao": "resultado · {pct}",
        "legenda_resultado_estrutura": "resultado da estrutura",
        "chip_total_suspenso": "total suspenso",
        "linha_acoes": "Ações",
        "linha_opcoes": "Opções · {contrato}",
        "linha_estrutura": "Estrutura",
        "motivo_premio_indisponivel": "prêmio indisponível",
        "motivo_dados_incompletos": "dados incompletos",
        "motivo_aguardando_premio": "aguardando prêmio",
        "motivo_aguardando_cotacao": "aguardando cotação",
        "motivo_cotacao_indisponivel": "cotação indisponível",
        "chip_acoes_pm": "{qty} ações · PM {pm}",
        "chip_vence": "vence {ddmm} · {dias}d",
        "chip_plano": "stop {stop} · alvo {alvo}",
        "chip_estrategia_generica": "estratégia não classificada",
        "faixa_rot_be": "◆ BE {v}",
        "faixa_rot_teto": "teto {v}",
        "faixa_leg_hoje": "● hoje {v}",
        # 46.1 (2026-10-02, G-08/AL-02/MD-02/MD-05): causas da suspensão, estados da leitura, legenda só ações, aria teto parcial.
        "motivo_lendo": "atualizando",
        "motivo_leitura_indisponivel": "leitura indisponível",
        "chip_desatualizado": "desatualizado",
        "tentar_de_novo": "↻ Tentar de novo",
        "legenda_resultado_so_acoes": "resultado · só ações",
        "leitura_falhou": "Leitura da posição indisponível agora · números suspensos",
        "leitura_desatualizada": "Leitura das {hora} · não atualizou, números podem estar defasados",
        "causa_sem_cotacao": "Sem cotação de {contratos} nesta fonte · total suspenso",
        "causa_fora_da_cadeia": "{contratos} não veio na cadeia desta fonte · total suspenso",
        "causa_sem_negocio": "Sem oferta nem último negócio para {contratos} nesta fonte · total suspenso",
        "causa_fonte_indisponivel": "Fonte de opções indisponível para {contratos} · total suspenso",
        "payoff_aria_teto_parcial": "Payoff de {ticker} no vencimento: prejuízo abaixo do BE R$ {be}; teto R$ {teto} cobre só parte das ações, ganho máximo não calculado; perda máxima {perdaMaxima}.",
    },
    "educacional": {
        "face_acao": "Ação",
        "face_opcoes": "Opções ({n})",
        "face_grupo_aria": "Face do card {ticker}",
        "plano_titulo": "Plano da ação",
        "compras_titulo": "Compras ({n})",
        "ver": "Ver ▾",
        "ocultar": "Ocultar ▴",
        "compras_indisponivel": "Compras: indisponível nesta fonte",
        "compras_sem_detalhe": "Detalhes das compras não vieram nesta fonte — nada foi inferido.",
        "falta_definir": "Falta definir",
        "estado_sem_plano": "Sem stop e alvo — defina o plano",
        "avulsa_sem_acoes": "Sem ações deste ativo: só a opção está aberta.",
        "estado_falta_alvo": "Falta o alvo — plano incompleto",
        "estado_falta_stop": "Falta o stop — plano incompleto",
        "estado_abaixo_stop": "Abaixo do stop do plano",
        "estado_acima_alvo": "Acima do alvo do plano",
        "estado_dentro": "Dentro do plano",
        "estado_travadas_todas": "Ações travadas pela call · saída após encerrar",
        "estado_travadas_parcial": "{n} de {m} ações travadas · {k} livres",
        "extra_resultado_parcial": "Resultado parcial: um prêmio atual indisponível",
        "extra_cotacao_indisponivel": "Cotação atual indisponível nesta fonte",
        "plano_ia_definir": "Definir plano · IA",
        "plano_ia_completar": "Completar plano · IA",
        "plano_ia_ajustar": "Ajustar plano · IA",
        "reanalisar": "Reanalisar",
        "historico": "Histórico de análises ({n})",
        "kicker_ia": "✦ BÓRIS IA",
        "encerrar": "Encerrar opção em Opções",
        "atualizar": "↻ Atualizar",
        "origem_nao_informada": "Origem da cotação não informada",
        "sem_cenario": "Cenários não calculados para esta combinação. Os limites dependem do cálculo do app.",
        "conta_sem_formula": "Calculado pela camada de opções do app",
        "aguardando_calculo": "aguardando o cálculo do app",
        "piso": "Piso",
        "equilibrio_rotulo": "◆ Equilíbrio",
        "teto": "Teto",
        "sem_piso": "sem piso",
        "sem_teto": "sem teto",
        "agora": "agora",
        "hoje": "hoje",
        "faixa_titulo": "No vencimento ({ddmm})",
        "chip_hoje": "Hoje",
        "chip_equilibrio": "Equilíbrio",
        "chip_teto": "Teto",
        "chip_alta_forte": "Alta forte",
        "rr_atual": "R:R atual",
        "em_operacao": "Em operação",
        "do_capital": "Do capital",
        "cotacao_atual": "Cotação atual",
        "setup_entrada": "Setup de entrada",
        "gatilho_valido": "válido",
        "gatilho_invalidado": "invalidado",
        "nota_pm": "PM R$ {pm} = R$ {total} ÷ {qtd} ações (média ponderada).",
        "nota_pm_vendas": " Vendas parciais reduzem a quantidade, não o PM.",
        "editar_plano": "✎ Editar stop/alvo",
        "regua_aria": "{ticker}: stop R$ {stop}, alvo R$ {alvo}, preço médio R$ {pm}, agora {agora}.",
        "faixa_aria": "{ticker} no vencimento: piso {piso}, equilíbrio R$ {be}, teto {teto}, hoje {hoje}.",
        "leg_hoje": "┆ hoje {v}",
        "leg_be": "◆ BE {v}",
        "leg_k": "┆ K {v}",
        "leg_eixo": "eixo x: {lo} → {hi}",
        "cel_be": "BE",
        "cel_ate_be": "Até BE",
        "cel_ate_k": "Até K",
        "cel_ganho_max": "Ganho máx.",
        "cel_perda_max": "Perda máx.",
        "cel_lastro": "Lastro",
        "conta_be_call": "BE = PM − prêmio",
        "conta_ate_be": "Até BE = BE ÷ hoje − 1",
        "conta_ate_k": "Até K = K ÷ hoje − 1",
        "conta_ganho_call": "Ganho máx. = (K − BE) × qtd",
        "conta_perda_call": "Perda máx. = BE × qtd (ação a zero)",
        "conta_lastro": "Lastro = ações que cobrem a CALL vendida",
        "sim_aria": "Preço de {ticker} no vencimento",
        "sim_valuetext": "R$ {preco}; {resultado}; {zona}",
        "payoff_sem_custos": "sem custos",
        "zona_rotulo_perda_travada": "perda limitada",
        "zona_rotulo_prejuizo": "prejuízo",
        "zona_rotulo_ganho": "ganho",
        "zona_rotulo_ganho_travado": "ganho limitado",
        "saida_motivo_lastro": "Todas as ações estão travadas como lastro. Para sair do ativo, encerre a CALL vendida em Opções.",
        "rodape_fechar": "Fechar ▴",
        "rodape_abrir": "Ver detalhes e aprender ▾",
        "saida": "Simular venda",
        "saida_sem_livres": "Simular venda · 0 ações livres",
        "apoio_saida": "Treino com dinheiro virtual: nenhuma ordem é enviada.",
        "sim_lead": "Se em {ddmm} {ticker} fechar a",
        "sim_resultado": "resultado da estrutura",
        "sim_metodo": "Sem custos. É o resultado no vencimento, não o de hoje.",
        "payoff_titulo": "Payoff no vencimento · {ddmm}",
        "payoff_aria": "Payoff de {ticker} no vencimento: prejuízo abaixo do equilíbrio R$ {be}; acima do teto R$ {teto} o resultado fica limitado ({ganhoMaximo}); perda máxima {perdaMaxima}.",
        "payoff_aria_sem_teto": "Payoff de {ticker} no vencimento: prejuízo abaixo do equilíbrio R$ {be}; sem teto, o resultado acompanha a ação; perda máxima {perdaMaxima}.",
        "zona_perda_travada": "Abaixo do piso R$ {piso}: a perda fica limitada a R$ {perdaMaxima}.",
        "zona_prejuizo_sem_piso": "Abaixo do equilíbrio R$ {be}: prejuízo. Sem piso, se a ação fosse a zero a perda seria de R$ {perdaMaxima}.",
        "zona_prejuizo_com_piso": "Entre o piso R$ {piso} e o equilíbrio R$ {be}: prejuízo, limitado pelo piso.",
        "zona_ganho": "Entre o equilíbrio R$ {be} e o teto R$ {teto}: o resultado cresce junto com a ação.",
        "zona_ganho_sem_teto": "Acima do equilíbrio R$ {be}, sem teto: o resultado acompanha a ação.",
        "zona_ganho_travado": "Acima do teto R$ {teto}: o resultado fica limitado em R$ {ganhoMaximo} e as ações são entregues a R$ {teto}.",
        # 46-UAT (2026-10-01, G-01..G-06): card fechado rótulo/valor, chips e faixa ancorada
        "legenda_resultado": "resultado",
        "legenda_resultado_variacao": "resultado · {pct}",
        "legenda_resultado_estrutura": "resultado da estrutura",
        "chip_total_suspenso": "total suspenso",
        "linha_acoes": "Ações",
        "linha_opcoes": "Opções · {contrato}",
        "linha_estrutura": "Estrutura",
        "motivo_premio_indisponivel": "prêmio indisponível",
        "motivo_dados_incompletos": "dados incompletos",
        "motivo_aguardando_premio": "aguardando prêmio",
        "motivo_aguardando_cotacao": "aguardando cotação",
        "motivo_cotacao_indisponivel": "cotação indisponível",
        "chip_acoes_pm": "{qty} ações · PM {pm}",
        "chip_vence": "vence {ddmm} · {dias}d",
        "chip_plano": "stop {stop} · alvo {alvo}",
        "chip_estrategia_generica": "estratégia não classificada",
        "faixa_rot_be": "◆ equilíbrio {v}",
        "faixa_rot_teto": "teto {v}",
        "faixa_leg_hoje": "● hoje {v}",
        # 46.1 (2026-10-02, G-08/AL-02/MD-02/MD-05): causas da suspensão, estados da leitura, legenda só ações, aria teto parcial.
        "motivo_lendo": "atualizando",
        "motivo_leitura_indisponivel": "leitura indisponível",
        "chip_desatualizado": "desatualizado",
        "tentar_de_novo": "↻ Tentar de novo",
        "legenda_resultado_so_acoes": "resultado · só ações",
        "leitura_falhou": "Não foi possível atualizar a leitura desta posição agora. Os números ficam suspensos e nada é estimado no lugar.",
        "leitura_desatualizada": "Esta leitura é das {hora} e não foi atualizada: os números podem não refletir a cotação de agora.",
        "causa_sem_cotacao": "Sem cotação da opção {contratos} nesta fonte: o total fica suspenso e nada é estimado no lugar.",
        "causa_fora_da_cadeia": "A fonte de dados não trouxe a opção {contratos} na lista de opções: sem cotação dela, o total fica suspenso e nada é estimado no lugar.",
        "causa_sem_negocio": "A opção {contratos} está na fonte, mas sem oferta nem negócio recente: sem preço, o total fica suspenso e nada é estimado no lugar.",
        "causa_fonte_indisponivel": "A fonte de dados de opções não respondeu para {contratos}: sem cotação, o total fica suspenso e nada é estimado no lugar.",
        "payoff_aria_teto_parcial": "Payoff de {ticker} no vencimento: prejuízo abaixo do equilíbrio R$ {be}; o teto R$ {teto} cobre só parte das ações, então o ganho máximo não é calculado; perda máxima {perdaMaxima}.",
    },
}

CARTAO_DIDATICA = {
    "educacional": {
        "kicker_termos": "TOQUE NOS TERMOS",
        "no_seu_caso": "No seu caso:",
        "entendi": "Entendi",
        "boris_explica": "Bóris explica ·",
        "termo_lastro": "lastro",
        "termo_call_coberta": "call coberta",
        "termo_teto": "teto",
        "termo_equilibrio": "equilíbrio",
        "termo_piso": "piso",
        "termo_preco_medio": "preço médio",
        "termo_stop": "stop",
        "termo_alvo": "alvo",
        "termo_rr": "R:R",
        "paragrafo_call_coberta": "Suas {qtd} ações estão como [[lastro]] de uma [[call_coberta]]. O [[teto]] é R$ {teto} e o [[equilibrio]] R$ {be}. Não há [[piso]].",
        "paragrafo_collar": "Suas {qtd} ações têm [[piso]] de R$ {piso} e [[teto]] de R$ {teto}, com [[lastro]] para a call. O [[equilibrio]] é R$ {be}.",
        "paragrafo_put_protecao": "Suas {qtd} ações têm [[piso]] de R$ {piso}. Não há [[teto]], e o [[equilibrio]] é R$ {be}.",
        "paragrafo_composta": "Esta combinação envolve [[lastro]], [[piso]] e [[teto]]: aguardando o cálculo do app.",
        "paragrafo_plano_completo": "Você pagou em média o [[preco_medio]] de R$ {pm}. O [[stop]] é R$ {stop}, o [[alvo]] é R$ {alvo} e o [[rr]] é {rr}.",
        "paragrafo_plano_completo_sem_rr": "Você pagou em média o [[preco_medio]] de R$ {pm}. O [[stop]] é R$ {stop} e o [[alvo]] é R$ {alvo}.",
        "paragrafo_plano_incompleto": "Seu [[preco_medio]] é R$ {pm}. O plano ainda não tem [[stop]] e [[alvo]] completos.",
        "caso_lastro": "{qtd} ações ficam reservadas para cobrir a call; {livres} estão livres.",
        "caso_call_coberta": "Você recebeu R$ {premio} por ação, R$ {premioTotal} no total, e aceitou entregar as ações a R$ {teto} até {ddmm}.",
        "caso_teto": "Acima de R$ {teto} no vencimento, o resultado fica limitado em R$ {ganhoMaximo}.",
        "caso_equilibrio": "R$ {be} = preço médio R$ {pm} menos o prêmio R$ {premio}; hoje a ação está a R$ {hoje}.",
        "caso_equilibrio_sem_hoje": "R$ {be} = preço médio R$ {pm} menos o prêmio R$ {premio}.",
        "caso_equilibrio_collar": "R$ {be} = preço médio R$ {pm} menos o prêmio recebido na call R$ {premioCall} mais o prêmio pago na put R$ {premioPut}; hoje a ação está a R$ {hoje}.",
        "caso_equilibrio_collar_sem_hoje": "R$ {be} = preço médio R$ {pm} menos o prêmio recebido na call R$ {premioCall} mais o prêmio pago na put R$ {premioPut}.",
        "caso_piso": "Abaixo de R$ {piso} no vencimento, a perda fica limitada a R$ {perdaMaxima}.",
        "caso_sem_piso": "Sem piso: se a ação fosse a zero, a perda seria de R$ {perdaMaxima}.",
        "caso_preco_medio": "Você pagou em média R$ {pm} por {qtd} ações; hoje a ação está a R$ {hoje}.",
        "caso_preco_medio_sem_hoje": "Você pagou em média R$ {pm} por {qtd} ações.",
        "caso_stop": "Sair em R$ {stop} daria {resultadoNoStop} em relação ao preço médio.",
        "caso_stop_indefinido": "O stop ainda não foi definido.",
        "caso_alvo": "Chegar a R$ {alvo} daria {resultadoNoAlvo} em relação ao preço médio.",
        "caso_alvo_indefinido": "O alvo ainda não foi definido.",
        "caso_rr": "Do preço de hoje, o alvo paga {rr} para cada R$ 1,00 arriscado até o stop.",
        "caso_aguardando": "aguardando o cálculo do app",
        "explica_call_coberta": "O resultado fica limitado em R$ {ganhoMaximo}, o equilíbrio é R$ {be} e a queda abaixo dele continua com você.",
        "explica_collar": "O piso de R$ {piso} e o teto de R$ {teto} mantêm o resultado entre uma perda de R$ {perdaMaxima} e um ganho de R$ {ganhoMaximo}.",
        "explica_put_protecao": "O piso de R$ {piso} limita a perda a R$ {perdaMaxima}; acima do equilíbrio R$ {be} o resultado acompanha a ação.",
        "explica_composta": "Esta combinação não tem leitura pronta: aguardando o cálculo do app.",
        "explica_plano_completo": "O plano tem stop em R$ {stop} e alvo em R$ {alvo}: é um roteiro de treino, não uma previsão.",
        "explica_plano_incompleto": "Falta definir parte do plano; sem os dois limites, não há dados suficientes para concluir o risco.",
        "explica_sem_plano": "Esta posição não tem stop e alvo; defina um plano para treinar a decisão de saída.",
    },
}


def cartao_posicao_txt(modo: str, chave: str, **dados):
    """Frase canônica do card v6. Modo fora de `CARTAO_POSICAO` (inclui
    "estudo") degrada para `educacional`; chave desconhecida devolve `None`
    (falha fechada). Interpolação por `str.replace`."""
    d = CARTAO_POSICAO.get(modo if modo in CARTAO_POSICAO else "educacional")
    frase = d.get(chave)
    if frase is None:
        return None
    for k, v in dados.items():
        frase = frase.replace("{" + str(k) + "}", str(v))
    return frase


def cartao_didatica_txt(chave: str, **dados):
    """Frase da camada didática do card v6 (só Estudo, D-11). Chave
    desconhecida devolve `None`. Interpolação por `str.replace`."""
    frase = CARTAO_DIDATICA["educacional"].get(chave)
    if frase is None:
        return None
    for k, v in dados.items():
        frase = frase.replace("{" + str(k) + "}", str(v))
    return frase


# Fase 48 (2026-10-05): fonte única do vocabulário do caminho B da aba Opções
# (objetivo -> escada -> gráfico -> confirmar). O front não compõe frase: o motor
# (48-04) e as telas (48-08/09) só leem chaves daqui. Espelho byte a byte em
# web/src/copy.js (COPY[modo].opcoesEscada); guardião test_opcoes_escada_espelho.mjs.
# Mesmo conjunto de chaves nos dois modos. Sem promessa de rentabilidade; "proteger"
# é sempre limite de perda. Sem chave de ordem parcial (execução é tudo-ou-nada, C-14).
OPCOES_ESCADA = {
    "educacional": {
        "objetivo_proteger_titulo": "Proteger de queda",
        "objetivo_proteger_desc": "Você paga um prêmio. Se a ação cair abaixo do piso, a perda para ali. Em termos técnicos, uma put protetora.",
        "objetivo_proteger_perde": "Perde: o prêmio, se a ação não cair",
        "objetivo_renda_titulo": "Gerar renda",
        "objetivo_renda_desc": "Você recebe um prêmio. Em troca, limita o ganho acima de um teto. Em termos técnicos, uma venda coberta, que trava as ações como lastro.",
        "objetivo_renda_perde": "Perde: ganho acima do teto",
        "objetivo_collar_titulo": "Proteger com custo baixo",
        "objetivo_collar_desc": "O prêmio recebido paga (quase) o da proteção. Perda e ganho ficam entre o piso e o teto. Em termos técnicos, um collar.",
        "objetivo_collar_perde": "Perde: ganho acima do teto",
        "objetivo_indisponivel": "{objetivo} indisponível: {motivo}.",
        "lastro_insuficiente": "só {livres} ações livres; esta estrutura precisa de {necessarias}",
        "lastro_travado": "ações travadas em outra call",
        "pergunta_objetivo": "O que você quer fazer com as {qtd} ações?",
        "pergunta_objetivo_sub": "Você vê o pior caso e o gráfico antes de decidir. Termos sublinhados abrem uma explicação.",
        "montar_do_zero": "Montar do zero",
        "secao_proteger": "Escolha o piso",
        "secao_renda": "Escolha o teto",
        "secao_collar": "Escolha o piso e o teto",
        "acao_a": "ação a R$ {preco}",
        "degrau_proteger_0": "Mais protegido",
        "degrau_proteger_1": "Equilibrado",
        "degrau_proteger_2": "Mais barato",
        "degrau_renda_0": "Mais renda",
        "degrau_renda_1": "Equilibrado",
        "degrau_renda_2": "Mais espaço para subir",
        "degrau_collar_0": "Mais protegido",
        "degrau_collar_1": "Equilibrado",
        "degrau_collar_2": "Mais barato",
        "degrau_ausente": "Sem estrutura neste degrau: {motivo}",
        "vencimento_dias": "{dias} dias",
        "col_perda_maxima": "Perda máxima",
        "col_custo_protecao": "Custo da proteção",
        "col_ganho_maximo": "Ganho máximo",
        "col_premio_recebido": "Prêmio recebido",
        "col_liquido_custa": "Custa no líquido",
        "col_liquido_recebe": "Recebe no líquido",
        "nota_sem_piso": "sem piso: a queda não é limitada",
        "risco_pior": "Pior caso: perde até R$ {perdaTotal} nas {qtd} ações (R$ {perdaAcao} por ação), por mais que a ação caia abaixo do piso de R$ {piso}.",
        "risco_pior_sem_piso": "Pior caso: sem piso, se a ação for a zero você perde R$ {perdaTotal}; a queda segue a da ação, amortecida só pelo prêmio de R$ {premio}.",
        "risco_melhor": "Melhor caso: ganha até R$ {ganhoTotal} nas {qtd} ações (R$ {ganhoAcao} por ação), se a ação fechar acima do teto de R$ {teto}.",
        "risco_melhor_sem_teto": "Melhor caso: sem teto, você ganha o que a ação subir, menos o prêmio pago.",
        "risco_equilibrio": "Equilíbrio: a ação precisa fechar a R$ {be} no vencimento {venc}.",
        "risco_sem_equilibrio": "Equilíbrio: não há dados suficientes para concluir.",
        "grafico_titulo": "Resultado no vencimento",
        "grafico_subtitulo": "linha cheia = com a estrutura · tracejada = só as ações",
        "unidade_total": "Total ({qtd} ações)",
        "unidade_acao": "Por ação",
        "linha_so_acoes": "Só as ações",
        "linha_com_estrutura": "Com a estrutura",
        "linha_preco_medio": "preço médio",
        "marcador_piso": "piso",
        "marcador_equilibrio": "equilíbrio",
        "marcador_teto": "teto",
        "marcador_perda_maxima": "perda máxima",
        "marcador_ganho_maximo": "ganho máximo",
        "legenda_piso": "Piso: R$ {preco}. Abaixo dele, a perda por ação para de crescer.",
        "legenda_equilibrio": "Equilíbrio: R$ {preco}. Nesse preço no vencimento, o resultado é zero.",
        "legenda_teto": "Teto: R$ {preco}. Acima dele, o ganho por ação para de crescer.",
        "legenda_perda_maxima": "Perda máxima: R$ {valor}. É o pior resultado possível no vencimento.",
        "legenda_ganho_maximo": "Ganho máximo: R$ {valor}. É o melhor resultado possível no vencimento.",
        "ausente_piso": "Sem piso nesta estrutura: a queda não é limitada.",
        "ausente_teto": "Sem teto nesta estrutura: o ganho acompanha a alta, menos o prêmio.",
        "ausente_ganho_maximo": "Sem ganho máximo nesta estrutura: o ganho acompanha a alta da ação.",
        "grafico_aria": "Gráfico do resultado de {ticker} no vencimento {venc}, em {unidade}. Pior caso: {pior}. Melhor caso: {melhor}. Equilíbrio: {be}.",
        "sem_grafico": "Sem gráfico para esta estrutura: {motivo}",
        "ese_pergunta": "E se a {ticker} fechar a R$ {preco} no vencimento?",
        "ese_melhora": "Neste preço, a estrutura melhora o resultado em R$ {d}.",
        "ese_reduz": "Neste preço, a estrutura reduz o resultado em R$ {d}.",
        "ese_igual": "Neste preço, a estrutura não muda o resultado.",
        "tabela_ver": "Ver os números",
        "tabela_preco": "Preço no vencimento",
        "tabela_so_acoes": "Só as ações",
        "tabela_com_estrutura": "Com a estrutura",
        "comparar_rotulo": "Comparar vencimentos",
        "comparar_custo": "até {n} consultas (2×{k}+1) · restam {x} hoje",
        "cota_esgotada": "Cota de consultas do dia esgotada. Renova {quando}. A explicação acima continua valendo.",
        "consultando": "consultando…",
        "matriz_sem_dado": "—",
        "matriz_so_comparacao": "Este vencimento está aqui para comparar: a execução simulada usa os vencimentos {lista}.",
        "matriz_pior": "pior caso",
        "matriz_ganho": "ganho máx.",
        "sem_estrutura": "Sem estrutura disponível para {ticker} neste vencimento",
        "sem_estrutura_dica": "Tente outro vencimento ou monte do zero.",
        # Fase 48 gap G-01/G-02 (2026-10-05): namespace OPCOES_ESCADA; não colide com sem_vencimento_elegivel da Fase 44 em OPCOES_LASTREADAS.
        "sem_vencimento_elegivel": "Nenhum vencimento futuro lido para {ticker} ({vencimentos}): o que vence hoje ou já venceu não é negociável. Sem vencimento futuro, nenhuma estrutura guiada é montada.",
        "sem_vencimento_elegivel_dica": "Quando houver um vencimento futuro, os objetivos voltam. Para estudar outro vencimento agora, use Montar do zero.",
        "objetivo_indisponivel_ver_motivo": "{objetivo} indisponível pelo motivo acima.",
        "pernas_titulo": "Suas pernas abertas",
        "pernas_linha": "{tipo} {lado} · strike R$ {strike} · vence {vencimento} · {qtd} opções",
        "pernas_premio": "Prêmio de entrada R$ {entrada} · agora R$ {atual}",
        "pernas_resultado": "Resultado: {valor}",
        "perna_lado_compra": "comprada",
        "perna_lado_venda": "vendida",
        "pernas_carregando": "Lendo o resultado das pernas…",
        "pernas_encerrar": "Encerrar",
        "pernas_encerrar_aria": "Encerrar a perna {id}",
        "pernas_confirmar": "Encerrar {id}? A venda é simulada pelo último prêmio da fonte. Nenhuma ordem real é enviada.",
        "pernas_confirmar_sim": "Confirmar encerramento",
        "pernas_cancelar": "Cancelar",
        "pernas_encerrando": "Encerrando…",
        "pernas_na_estrutura": "Esta perna faz parte de uma estrutura com lastro: encerre pelo painel da estrutura.",
        "pernas_vendida_sem_acao": "Perna vendida: a recompra não é feita nesta lista.",
        # Fase 49 (2026-10-06): anatomia da perna — ANAT-01..08; texto nasce aqui, espelho em copy.js.
        "anat_titulo_posicao": "Sua posição em {ticker}",
        "anat_sub_posicao": "Veja o que cada perna faz antes de decidir. Mexa no preço para testar hipóteses: não é previsão.",
        "anat_total_titulo": "Resultado no vencimento ({vencimento})",
        "anat_total_titulo_sem_data": "Resultado no vencimento",
        "anat_chips_aria": "Pernas incluídas no gráfico",
        "anat_chip_perna": "{tipo} {strike}",
        "anat_chip_acoes": "{qtd} ações",
        "anat_slider_rotulo": "Se {ticker} estiver a R$ {preco} no vencimento (hipótese sua, não previsão)",
        "anat_leitura_total": "Em R$ {preco} no vencimento, o que está marcado soma {valor}.",
        "anat_leitura_com_sem": "Em R$ {preco} no vencimento: com a perna {id} o resultado é {com}; sem ela, {sem}. Ela contribui com {contrib}.",
        "anat_sem_esta_vazio": "Sem a perna {id}, nada fica marcado no gráfico.",
        "anat_acoes_dentro": "Inclui as {qtd} ações de {ticker} pelo preço médio de R$ {pm}, registrado no simulador.",
        "anat_acoes_fora_sem_pm": "As {qtd} ações de {ticker} ficam fora do gráfico: o simulador não tem o preço médio delas. Nada foi estimado.",
        "anat_total_vencimentos_diferentes": "Não há dados suficientes para concluir. As pernas marcadas vencem em datas diferentes ({vencimentos}), então não existe um único resultado no vencimento. Cada perna segue com o seu quadro.",
        "anat_total_sem_data": "Não há dados suficientes para concluir. Uma das pernas marcadas não tem data de vencimento no simulador, então não dá para afirmar que vencem juntas nem montar um único resultado no vencimento. Cada perna segue com o seu quadro.",
        "anat_total_vazio": "Nada marcado. Ligue ao menos uma perna para ver o resultado.",
        "anat_total_aria": "Curva do resultado total no vencimento por preço de {ticker}, somando {n} perna(s){acoes}. A tabela abaixo traz os valores.",
        "anat_total_aria_acoes": " e as {qtd} ações",
        "anat_pernas_titulo": "Suas pernas",
        "anat_objetivos_titulo": "O que você quer fazer com a posição?",
        "anat_frase_call_compra": "Você pagou R$ {valor} (R$ {premio} × {qtd}) pelo direito de comprar {qtd} {ticker} a R$ {strike} cada, até {vencimento}. Se não valer a pena exercer, o máximo que você perde é o que pagou.",
        "anat_frase_put_compra": "Você pagou R$ {valor} (R$ {premio} × {qtd}) pelo direito de vender {qtd} {ticker} a R$ {strike} cada, até {vencimento}. Se não valer a pena exercer, o máximo que você perde é o que pagou.",
        "anat_frase_call_venda": "Você recebeu R$ {valor} (R$ {premio} × {qtd}) e assumiu a obrigação de vender {qtd} {ticker} a R$ {strike} cada, se a opção for exercida até {vencimento}.",
        "anat_frase_put_venda": "Você recebeu R$ {valor} (R$ {premio} × {qtd}) e assumiu a obrigação de comprar {qtd} {ticker} a R$ {strike} cada, se a opção for exercida até {vencimento}.",
        "anat_cond_call_compra": "Fica no positivo se {ticker} passar de R$ {equilibrio} no vencimento.",
        "anat_cond_put_compra": "Fica no positivo se {ticker} cair abaixo de R$ {equilibrio} no vencimento.",
        "anat_cond_call_venda": "Fica no positivo enquanto {ticker} não passar de R$ {equilibrio} no vencimento.",
        "anat_cond_put_venda": "Fica no positivo enquanto {ticker} não cair abaixo de R$ {equilibrio} no vencimento.",
        "anat_prazo_dias": "vence em {dias} dias ({vencimento})",
        "anat_prazo_amanha": "vence amanhã ({vencimento})",
        "anat_prazo_hoje": "vence hoje ({vencimento})",
        "anat_prazo_vencida": "venceu em {vencimento}",
        "anat_prazo_sem_data": "Prazo: — (o simulador não tem a data de vencimento desta perna)",
        "anat_rotulo_pior": "Pior caso",
        "anat_rotulo_equilibrio": "Equilíbrio",
        "anat_rotulo_hoje": "Hoje",
        "anat_pior_ilimitado": "sem limite",
        "anat_pior_ilimitado_nota": "Se {ticker} subir sem parar, a perda desta perna cresce junto: não existe um pior caso fixo.",
        "anat_sem_cotacao_chip": "Sem cotação",
        "anat_hoje_fonte_indisponivel": "Valor de hoje indisponível: a fonte de opções não respondeu. Nada foi estimado.",
        "anat_hoje_fora_da_cadeia": "Valor de hoje indisponível: este contrato não veio na cadeia lida da fonte. Nada foi estimado.",
        "anat_hoje_sem_negocio": "Valor de hoje indisponível: o contrato está na cadeia, mas sem preço de compra, de venda ou último negócio. Nada foi estimado.",
        "anat_hoje_sem_cotacao": "Valor de hoje indisponível: sem cotação deste contrato agora. Nada foi estimado.",
        "anat_hoje_sem_estrutura": "Valor de hoje indisponível: a leitura de cotação desta posição não respondeu. Nada foi estimado.",
        "anat_hoje_nota": "O quadro de vencimento não depende de cotação; só o valor de hoje depende.",
        "anat_ver_sem_esta": "Ver o que muda sem esta perna",
        "anat_ver_total": "Voltar ao total",
        "anat_ver_tabela": "Ver em tabela",
        "anat_tabela_preco": "{ticker} no vencimento",
        "anat_tabela_perna": "Resultado da perna",
        "anat_tabela_total": "Resultado do que está marcado",
        "anat_perna_aria": "Resultado da perna {id} no vencimento: pior caso {pior}, equilíbrio em R$ {equilibrio}.",
        "anat_dados_insuficientes": "Não há dados suficientes para concluir. Faltam strike, prêmio ou quantidade desta perna no simulador; nada foi estimado.",
        "anat_confirmar_com_cotacao": "Encerrar {id}? Você vende o direito de volta. Pelo último prêmio lido (R$ {premio}), o resultado desta perna agora é {resultado}; o valor exato sai do prêmio no momento da ordem simulada. Nenhuma ordem real é enviada.",
        "anat_confirmar_sem_cotacao": "Encerrar {id}? Você vende o direito de volta. Sem cotação agora, não dá para calcular quanto entra no caixa. Nenhuma ordem real é enviada.",
        "anat_carregando": "Calculando o que cada perna faz…",
        "anat_recalculando": "Recalculando…",
        "anat_desatualizado": "Esta leitura pode estar desatualizada: a última tentativa de recalcular falhou. O gráfico e o total foram ocultados para não mostrar um número de outra hipótese. Nada foi estimado.",
        "anat_erro": "Não foi possível calcular agora o que cada perna faz. Nada foi estimado. As pernas e o Encerrar continuam abaixo.",
        "anat_legenda_perda": "Área hachurada: perda",
        "anat_legenda_ganho": "Área lisa: ganho",
        "anat_marcador_strike": "K {strike}",
        "anat_marcador_equilibrio": "equilíbrio",
        "anat_marcador_pm": "preço médio",
        "anat_marcador_hoje": "hoje",
        "anat_sem_pernas": "Nenhuma perna aberta em {ticker}.",
        "erro_fonte": "Não foi possível ler as opções agora. Nenhum valor foi estimado. Tente de novo; se persistir, os dados de opções estão fora do ar.",
        "tentar_de_novo": "Tentar de novo",
        "carregando": "Carregando",
        "mercado_fechado": "Pregão fechado: estes valores são de {data}, não de agora.",
        "frescor": "{fonte} · pregão {data} · {situacao}",
        "situacao_em_dia": "em dia",
        "situacao_atrasado": "atrasado",
        "situacao_fim_pregao": "fim de pregão",
        "atrasado_frase": "não é o preço de agora",
        "dado_insuficiente": "Não há dados suficientes para concluir.",
        "aviso_virtual": "Dinheiro virtual: nenhuma ordem sai para corretora, bolsa ou banco.",
        "hub_atencao": "Atenção",
        "hub_carteira": "Sua carteira",
        "hub_aviso_custo": "Abrir um ativo não gasta consultas.",
        "hub_atualizar": "atualizar ›",
        "hub_atualizar_custo": "o estado do dia custa {n} consultas",
        "hub_nenhum_armado": "Nenhum vigia armado hoje.",
        "card_subtitulo": "{qtd} ações · {livres} livres para lastro",
        "card_subtitulo_sem_acoes": "sem ações deste ativo · opção sem lastro",
        "card_estrutura_aberta": "estrutura aberta: {nome}",
        "card_sem_estrutura": "nenhuma estrutura aberta",
        "card_vigias": "{n} vigia(s)",
        "hub_vazio_titulo": "Você ainda não tem ações em carteira",
        "hub_vazio_corpo": "As opções aqui são estudadas sobre as ações que você já tem na carteira virtual. Compre uma posição simulada e volte.",
        "hub_vazio_cta": "Ver Carteira",
        "voltar": "‹ voltar",
        "cta_escolher": "Escolher este",
        "sem_custo": "sem custo",
        "confirmar_titulo": "Confirmar a estrutura",
        "confirmar_estrutura": "Estrutura",
        "confirmar_vencimento": "Vencimento",
        "perna_put_comprada": "Put comprada: strike R$ {strike}, paga R$ {premio} por ação",
        "perna_call_vendida": "Call vendida: strike R$ {strike}, recebe R$ {premio} por ação",
        "confirmar_lote": "{contratos} contrato(s) · {qtd} ações",
        "lastro_trava": "{qtd} ações ficam travadas como lastro",
        "lastro_livre": "sem lastro: ações livres",
        "cta_executar": "Executar (simulado)",
        "cta_criar_vigia": "Criar vigia",
        "estudo_nao_executa": "No Modo Estudo você não executa operações: esta é a leitura de como a estrutura funcionaria.",
        "ordem_rejeitada": "Ordem rejeitada: {motivo}",
        "toast_executada": "Ordem simulada registrada. Nenhuma ordem real foi enviada.",
    },
    "operador": {
        "objetivo_proteger_titulo": "Proteger de queda",
        "objetivo_proteger_desc": "Paga prêmio, trava o piso. Put protetora.",
        "objetivo_proteger_perde": "Perde: o prêmio, se a ação não cair",
        "objetivo_renda_titulo": "Gerar renda",
        "objetivo_renda_desc": "Recebe prêmio, limita o teto. Venda coberta: trava as ações como lastro.",
        "objetivo_renda_perde": "Perde: ganho acima do teto",
        "objetivo_collar_titulo": "Proteger com custo baixo",
        "objetivo_collar_desc": "Prêmio da call paga (quase) a put. Perda e ganho entre piso e teto. Collar.",
        "objetivo_collar_perde": "Perde: ganho acima do teto",
        "objetivo_indisponivel": "{objetivo} indisponível: {motivo}.",
        "lastro_insuficiente": "só {livres} ações livres; esta estrutura precisa de {necessarias}",
        "lastro_travado": "ações travadas em outra call",
        "pergunta_objetivo": "Objetivo para as {qtd} ações?",
        "pergunta_objetivo_sub": "Pior caso e gráfico antes de decidir. Termos sublinhados abrem a explicação.",
        "montar_do_zero": "Montar do zero",
        "secao_proteger": "Escolha o piso",
        "secao_renda": "Escolha o teto",
        "secao_collar": "Escolha o piso e o teto",
        "acao_a": "ação a R$ {preco}",
        "degrau_proteger_0": "Mais protegido",
        "degrau_proteger_1": "Equilibrado",
        "degrau_proteger_2": "Mais barato",
        "degrau_renda_0": "Mais renda",
        "degrau_renda_1": "Equilibrado",
        "degrau_renda_2": "Mais espaço para subir",
        "degrau_collar_0": "Mais protegido",
        "degrau_collar_1": "Equilibrado",
        "degrau_collar_2": "Mais barato",
        "degrau_ausente": "Degrau sem estrutura: {motivo}",
        "vencimento_dias": "{dias} dias",
        "col_perda_maxima": "Perda máxima",
        "col_custo_protecao": "Custo da proteção",
        "col_ganho_maximo": "Ganho máximo",
        "col_premio_recebido": "Prêmio recebido",
        "col_liquido_custa": "Custa no líquido",
        "col_liquido_recebe": "Recebe no líquido",
        "nota_sem_piso": "sem piso: a queda não é limitada",
        "risco_pior": "Pior caso: perde até R$ {perdaTotal} nas {qtd} ações (R$ {perdaAcao}/ação) abaixo do piso de R$ {piso}.",
        "risco_pior_sem_piso": "Pior caso: sem piso, ação a zero = perda de R$ {perdaTotal}; queda igual à da ação, amortecida só pelo prêmio de R$ {premio}.",
        "risco_melhor": "Melhor caso: ganha até R$ {ganhoTotal} nas {qtd} ações (R$ {ganhoAcao}/ação) acima do teto de R$ {teto}.",
        "risco_melhor_sem_teto": "Melhor caso: sem teto, ganho = alta da ação menos o prêmio pago.",
        "risco_equilibrio": "Equilíbrio: ação a R$ {be} no vencimento {venc}.",
        "risco_sem_equilibrio": "Equilíbrio: não há dados suficientes para concluir.",
        "grafico_titulo": "Resultado no vencimento",
        "grafico_subtitulo": "linha cheia = com a estrutura · tracejada = só as ações",
        "unidade_total": "Total ({qtd} ações)",
        "unidade_acao": "Por ação",
        "linha_so_acoes": "Só as ações",
        "linha_com_estrutura": "Com a estrutura",
        "linha_preco_medio": "preço médio",
        "marcador_piso": "piso",
        "marcador_equilibrio": "equilíbrio",
        "marcador_teto": "teto",
        "marcador_perda_maxima": "perda máxima",
        "marcador_ganho_maximo": "ganho máximo",
        "legenda_piso": "Piso R$ {preco}: abaixo, a perda por ação para de crescer.",
        "legenda_equilibrio": "Equilíbrio R$ {preco}: resultado zero no vencimento.",
        "legenda_teto": "Teto R$ {preco}: acima, o ganho por ação para de crescer.",
        "legenda_perda_maxima": "Perda máxima R$ {valor}: pior resultado no vencimento.",
        "legenda_ganho_maximo": "Ganho máximo R$ {valor}: melhor resultado no vencimento.",
        "ausente_piso": "Sem piso nesta estrutura: a queda não é limitada.",
        "ausente_teto": "Sem teto nesta estrutura: o ganho acompanha a alta, menos o prêmio.",
        "ausente_ganho_maximo": "Sem ganho máximo: o ganho acompanha a alta da ação.",
        "grafico_aria": "Resultado de {ticker} no vencimento {venc}, em {unidade}. Pior caso: {pior}. Melhor caso: {melhor}. Equilíbrio: {be}.",
        "sem_grafico": "Sem gráfico para esta estrutura: {motivo}",
        "ese_pergunta": "E se a {ticker} fechar a R$ {preco} no vencimento?",
        "ese_melhora": "Neste preço, a estrutura melhora o resultado em R$ {d}.",
        "ese_reduz": "Neste preço, a estrutura reduz o resultado em R$ {d}.",
        "ese_igual": "Neste preço, a estrutura não muda o resultado.",
        "tabela_ver": "Ver os números",
        "tabela_preco": "Preço no vencimento",
        "tabela_so_acoes": "Só as ações",
        "tabela_com_estrutura": "Com a estrutura",
        "comparar_rotulo": "Comparar vencimentos",
        "comparar_custo": "até {n} consultas (2×{k}+1) · restam {x} hoje",
        "cota_esgotada": "Cota de consultas do dia esgotada. Renova {quando}. A leitura acima segue valendo.",
        "consultando": "consultando…",
        "matriz_sem_dado": "—",
        "matriz_so_comparacao": "Vencimento só para comparar: a execução simulada usa {lista}.",
        "matriz_pior": "pior caso",
        "matriz_ganho": "ganho máx.",
        "sem_estrutura": "Sem estrutura disponível para {ticker} neste vencimento",
        "sem_estrutura_dica": "Tente outro vencimento ou monte do zero.",
        # Fase 48 gap G-01/G-02 (2026-10-05): namespace OPCOES_ESCADA; não colide com sem_vencimento_elegivel da Fase 44 em OPCOES_LASTREADAS.
        "sem_vencimento_elegivel": "{ticker}: nenhum vencimento futuro lido ({vencimentos}). Sem estrutura guiada.",
        "sem_vencimento_elegivel_dica": "Objetivos voltam quando houver vencimento futuro. Outro vencimento agora: Montar do zero.",
        "objetivo_indisponivel_ver_motivo": "{objetivo} indisponível pelo motivo acima.",
        "pernas_titulo": "Pernas abertas",
        "pernas_linha": "{tipo} {lado} · K R$ {strike} · venc {vencimento} · {qtd}",
        "pernas_premio": "Entrada R$ {entrada} · agora R$ {atual}",
        "pernas_resultado": "Resultado: {valor}",
        "perna_lado_compra": "comprada",
        "perna_lado_venda": "vendida",
        "pernas_carregando": "Lendo resultado das pernas…",
        "pernas_encerrar": "Encerrar",
        "pernas_encerrar_aria": "Encerrar a perna {id}",
        "pernas_confirmar": "Encerrar {id}? Venda simulada pelo último prêmio da fonte; nenhuma ordem real sai.",
        "pernas_confirmar_sim": "Confirmar encerramento",
        "pernas_cancelar": "Cancelar",
        "pernas_encerrando": "Encerrando…",
        "pernas_na_estrutura": "Perna de estrutura com lastro: encerre pelo painel da estrutura.",
        "pernas_vendida_sem_acao": "Perna vendida: recompra fora desta lista.",
        # Fase 49 (2026-10-06): anatomia da perna — ANAT-01..08; texto nasce aqui, espelho em copy.js.
        "anat_titulo_posicao": "Posição em {ticker}",
        "anat_sub_posicao": "Resultado no vencimento por perna e no total. O preço escolhido é hipótese, não previsão.",
        "anat_total_titulo": "Payoff no vencimento ({vencimento})",
        "anat_total_titulo_sem_data": "Payoff no vencimento",
        "anat_chips_aria": "Pernas no total",
        "anat_chip_perna": "{tipo} {strike}",
        "anat_chip_acoes": "Ações ({qtd})",
        "anat_slider_rotulo": "{ticker} a R$ {preco} no vencimento (hipótese, não previsão)",
        "anat_leitura_total": "Em R$ {preco}: total {valor}.",
        "anat_leitura_com_sem": "Em R$ {preco}: com {id} {com}; sem {id} {sem}; contribuição {contrib}.",
        "anat_sem_esta_vazio": "Sem {id}: nada marcado.",
        "anat_acoes_dentro": "Inclui {qtd} ações a PM R$ {pm} (simulador).",
        "anat_acoes_fora_sem_pm": "Ações fora do total: sem preço médio no simulador. Nada estimado.",
        "anat_total_vencimentos_diferentes": "Não há dados suficientes para concluir. Vencimentos diferentes ({vencimentos}): sem payoff único. Veja cada perna.",
        "anat_total_sem_data": "Não há dados suficientes para concluir. Perna sem data de vencimento: sem payoff único. Veja cada perna.",
        "anat_total_vazio": "Nada marcado.",
        "anat_total_aria": "Payoff total no vencimento de {ticker}: {n} perna(s){acoes}. Valores na tabela.",
        "anat_total_aria_acoes": " + {qtd} ações",
        "anat_pernas_titulo": "Pernas",
        "anat_objetivos_titulo": "Objetivo para a posição",
        "anat_frase_call_compra": "Pagou R$ {valor} ({premio} × {qtd}) pelo direito de comprar {qtd} {ticker} a R$ {strike} até {vencimento}. Perda máxima: o prêmio pago.",
        "anat_frase_put_compra": "Pagou R$ {valor} ({premio} × {qtd}) pelo direito de vender {qtd} {ticker} a R$ {strike} até {vencimento}. Perda máxima: o prêmio pago.",
        "anat_frase_call_venda": "Recebeu R$ {valor} ({premio} × {qtd}); obrigado a vender {qtd} {ticker} a R$ {strike} se exercido até {vencimento}.",
        "anat_frase_put_venda": "Recebeu R$ {valor} ({premio} × {qtd}); obrigado a comprar {qtd} {ticker} a R$ {strike} se exercido até {vencimento}.",
        "anat_cond_call_compra": "Positivo acima de R$ {equilibrio} no vencimento.",
        "anat_cond_put_compra": "Positivo abaixo de R$ {equilibrio} no vencimento.",
        "anat_cond_call_venda": "Positivo abaixo de R$ {equilibrio} no vencimento.",
        "anat_cond_put_venda": "Positivo acima de R$ {equilibrio} no vencimento.",
        "anat_prazo_dias": "{dias} dias ({vencimento})",
        "anat_prazo_amanha": "vence amanhã ({vencimento})",
        "anat_prazo_hoje": "vence hoje ({vencimento})",
        "anat_prazo_vencida": "vencida ({vencimento})",
        "anat_prazo_sem_data": "Prazo: — (sem data no simulador)",
        "anat_rotulo_pior": "Perda máx.",
        "anat_rotulo_equilibrio": "Equilíbrio",
        "anat_rotulo_hoje": "Agora",
        "anat_pior_ilimitado": "ilimitada",
        "anat_pior_ilimitado_nota": "Perda sem teto na alta de {ticker}.",
        "anat_sem_cotacao_chip": "Sem cotação",
        "anat_hoje_fonte_indisponivel": "Sem valor agora: fonte de opções fora. Nada estimado.",
        "anat_hoje_fora_da_cadeia": "Sem valor agora: contrato fora da cadeia lida. Nada estimado.",
        "anat_hoje_sem_negocio": "Sem valor agora: contrato sem bid, ask ou último negócio. Nada estimado.",
        "anat_hoje_sem_cotacao": "Sem cotação agora. Nada estimado.",
        "anat_hoje_sem_estrutura": "Sem leitura de cotação da posição. Nada estimado.",
        "anat_hoje_nota": "Payoff no vencimento independe de cotação; só Agora depende.",
        "anat_ver_sem_esta": "Comparar sem esta perna",
        "anat_ver_total": "Ver total",
        "anat_ver_tabela": "Ver em tabela",
        "anat_tabela_preco": "{ticker} no venc.",
        "anat_tabela_perna": "Resultado",
        "anat_tabela_total": "Total marcado",
        "anat_perna_aria": "Payoff de {id}: perda máx. {pior}, equilíbrio R$ {equilibrio}.",
        "anat_dados_insuficientes": "Não há dados suficientes para concluir. Perna sem strike, prêmio ou quantidade.",
        "anat_confirmar_com_cotacao": "Encerrar {id}? Venda simulada; último prêmio lido R$ {premio}, resultado agora {resultado}. O valor exato sai do prêmio na hora da ordem simulada. Nenhuma ordem real sai.",
        "anat_confirmar_sem_cotacao": "Encerrar {id}? Venda simulada. Sem cotação agora: não dá para calcular o caixa. Nenhuma ordem real sai.",
        "anat_carregando": "Calculando payoff…",
        "anat_recalculando": "Recalculando…",
        "anat_desatualizado": "Leitura possivelmente desatualizada (releitura falhou). Total oculto. Nada estimado.",
        "anat_erro": "Payoff indisponível agora. Nada estimado. Pernas e Encerrar abaixo.",
        "anat_legenda_perda": "Hachura: perda",
        "anat_legenda_ganho": "Liso: ganho",
        "anat_marcador_strike": "K {strike}",
        "anat_marcador_equilibrio": "eq.",
        "anat_marcador_pm": "PM",
        "anat_marcador_hoje": "agora",
        "anat_sem_pernas": "Sem pernas em {ticker}.",
        "erro_fonte": "Opções fora do ar. Nenhum valor foi estimado. Tente de novo; se persistir, a fonte está indisponível.",
        "tentar_de_novo": "Tentar de novo",
        "carregando": "Carregando",
        "mercado_fechado": "Pregão fechado: estes valores são de {data}, não de agora.",
        "frescor": "{fonte} · pregão {data} · {situacao}",
        "situacao_em_dia": "em dia",
        "situacao_atrasado": "atrasado",
        "situacao_fim_pregao": "fim de pregão",
        "atrasado_frase": "não é o preço de agora",
        "dado_insuficiente": "Não há dados suficientes para concluir.",
        "aviso_virtual": "Dinheiro virtual: nenhuma ordem sai para corretora, bolsa ou banco.",
        "hub_atencao": "Atenção",
        "hub_carteira": "Sua carteira",
        "hub_aviso_custo": "Abrir um ativo não gasta consultas.",
        "hub_atualizar": "atualizar ›",
        "hub_atualizar_custo": "o estado do dia custa {n} consultas",
        "hub_nenhum_armado": "Nenhum vigia armado hoje.",
        "card_subtitulo": "{qtd} ações · {livres} livres para lastro",
        "card_subtitulo_sem_acoes": "sem ações deste ativo · opção sem lastro",
        "card_estrutura_aberta": "estrutura aberta: {nome}",
        "card_sem_estrutura": "nenhuma estrutura aberta",
        "card_vigias": "{n} vigia(s)",
        "hub_vazio_titulo": "Você ainda não tem ações em carteira",
        "hub_vazio_corpo": "Opções são estudadas sobre as ações da carteira virtual. Abra uma posição simulada e volte.",
        "hub_vazio_cta": "Ver Carteira",
        "voltar": "‹ voltar",
        "cta_escolher": "Escolher este",
        "sem_custo": "sem custo",
        "confirmar_titulo": "Confirmar estrutura",
        "confirmar_estrutura": "Estrutura",
        "confirmar_vencimento": "Vencimento",
        "perna_put_comprada": "Put comprada: strike R$ {strike}, paga R$ {premio} por ação",
        "perna_call_vendida": "Call vendida: strike R$ {strike}, recebe R$ {premio} por ação",
        "confirmar_lote": "{contratos} contrato(s) · {qtd} ações",
        "lastro_trava": "{qtd} ações ficam travadas como lastro",
        "lastro_livre": "sem lastro: ações livres",
        "cta_executar": "Executar (simulado)",
        "cta_criar_vigia": "Criar vigia",
        "estudo_nao_executa": "Modo Estudo não executa: esta é a leitura da estrutura.",
        "ordem_rejeitada": "Ordem rejeitada: {motivo}",
        "toast_executada": "Ordem simulada registrada. Nenhuma ordem real foi enviada.",
    },
}


def opcoes_escada_txt(modo: str, chave: str, **dados):
    """Frase canônica do caminho B (Opções). Modo fora de `OPCOES_ESCADA` (inclui
    "estudo") degrada para `educacional`; chave desconhecida devolve `None`
    (falha fechada). Interpolação por `str.replace`."""
    d = OPCOES_ESCADA.get(modo if modo in OPCOES_ESCADA else "educacional")
    frase = d.get(chave)
    if frase is None:
        return None
    for k, v in dados.items():
        frase = frase.replace("{" + str(k) + "}", str(v))
    return frase
