/* Dados das telas do Boris+ (guia de treinamento). Capturas de 09/10/2026, app local, dinheiro virtual.
   Cada ponto: [texto, x%, y%, largura%, altura%] — centro e tamanho do elemento na captura (o spotlight acompanha). */
window.TELAS = [
 {
  "id": "boas",
  "kind": "m",
  "img": "img/01-boas-vindas.jpg",
  "alt": "Boas-vindas: orçamento simulado de R$ 10.000, perfil de risco e aviso educacional.",
  "titulo": "Boas-vindas",
  "sub": "Primeira abertura",
  "can": [
   [
    "Dizer como prefere ser chamado (opcional).",
    50,
    51,
    78,
    5.2
   ],
   [
    "Definir o orçamento simulado inicial, em dinheiro virtual.",
    50,
    60,
    78,
    4.8
   ],
   [
    "Escolher o perfil de risco: conservador, moderado ou agressivo.",
    50,
    69,
    78,
    4.6
   ],
   [
    "Entrar na mesa e começar a treinar.",
    50,
    76,
    78,
    5.4
   ]
  ],
  "guard": "Já na entrada: ferramenta educacional, nada é recomendação de investimento.",
  "grupo": "Primeiros passos",
  "onde": "Primeira abertura, depois de criar a conta",
  "objetivo": "Definir o ponto de partida do seu treino.",
  "missao": [
   "Escolha como quer ser chamado (opcional).",
   "Defina o orçamento simulado.",
   "Escolha o perfil de risco.",
   "Toque em “Entrar na mesa”."
  ],
  "quiz": {
   "q": "O orçamento definido aqui é:",
   "o": [
    "Dinheiro depositado em uma corretora.",
    "Saldo fictício para treinar.",
    "Um limite de crédito real."
   ],
   "a": 1,
   "why": "Todo o saldo do Boris+ é virtual e identificado como tal."
  }
 },
 {
  "id": "acomp",
  "kind": "m",
  "img": "img/02-acompanhar.jpg",
  "alt": "Tela Acompanhar: resumo do dia, patrimônio simulado e estado vazio da curva.",
  "titulo": "Acompanhar",
  "sub": "O resumo do seu dia",
  "can": [
   [
    "Ver o saldo virtual e a variação do dia, sempre no topo.",
    62,
    8.5,
    36,
    7
   ],
   [
    "Abrir perfil e configurações.",
    90,
    10.5,
    11.5,
    5
   ],
   [
    "Saber se o mercado está aberto ou fechado e quando abre.",
    22,
    13,
    42,
    3
   ],
   [
    "Ler o resumo do dia: carteira, acumulado e operações.",
    50,
    45.5,
    91,
    21
   ],
   [
    "Acompanhar a curva do patrimônio simulado.",
    50,
    73,
    82,
    11
   ],
   [
    "Ver estados honestos: sem histórico, o app diz “Não há dados suficientes para concluir”.",
    50,
    84,
    86,
    8.5
   ],
   [
    "Navegar pelas abas: Acompanhar, Radar, Watchlist, Portfólio e Opções.",
    50,
    96,
    100,
    7.5
   ]
  ],
  "guard": "Nada de número inventado: o que não existe aparece como vazio explicado.",
  "grupo": "Primeiros passos",
  "onde": "Aba Acompanhar",
  "objetivo": "Ler o estado do seu dia de relance.",
  "missao": [
   "Confira se o mercado está aberto ou fechado.",
   "Leia o resumo do dia.",
   "Localize a curva do patrimônio e leia a mensagem quando ainda não há histórico."
  ],
  "quiz": {
   "q": "Sem histórico, a curva do patrimônio mostra:",
   "o": [
    "Uma linha estimada pelo app.",
    "A explicação de que não há dados suficientes.",
    "O resultado de outros usuários."
   ],
   "a": 1,
   "why": "O app não inventa dado: o vazio vem explicado."
  }
 },
 {
  "id": "radar",
  "kind": "m",
  "img": "img/09-radar.jpg",
  "alt": "Radar de mercado: 65 de 74 ativos varridos, 9 sem dados.",
  "titulo": "Radar de mercado",
  "sub": "Varredura do universo",
  "can": [
   [
    "Pedir análise de IA para os melhores ativos (“IA no top-N”).",
    70.5,
    21.8,
    22.5,
    5.4
   ],
   [
    "Buscar um ticker específico.",
    36,
    41.4,
    66,
    5
   ],
   [
    "Ver o período em uso (ex.: 1 ano, 252 pregões).",
    33,
    47,
    59,
    3.3
   ],
   [
    "Saber quantos ativos foram varridos e quantos ficaram sem dados.",
    45,
    55,
    84,
    2.3
   ],
   [
    "Abrir “Como o Radar analisa” para entender o método.",
    50,
    60,
    91,
    5
   ],
   [
    "Ler o card: plano educacional, confiança e o padrão detectado.",
    49,
    78.5,
    83,
    11.4
   ]
  ],
  "guard": "O Radar mostra condições técnicas para estudo, sem recomendação.",
  "grupo": "Descobrir e planejar",
  "onde": "Aba Radar (Mesa, no Modo Operador)",
  "objetivo": "Descobrir quais ativos têm condição técnica para estudar.",
  "missao": [
   "Repare no período em uso e no horário da leitura.",
   "Veja quantos ativos foram varridos e quantos ficaram sem dados.",
   "Abra um card e leia o plano educacional."
  ],
  "quiz": {
   "q": "“Estudar alta” no Radar significa:",
   "o": [
    "Que o preço vai subir.",
    "Que há condição técnica de alta para estudar, sem garantia.",
    "Que o app comprou o ativo."
   ],
   "a": 1,
   "why": "O Radar mostra condições técnicas para estudo, nunca previsão nem recomendação."
  }
 },
 {
  "id": "watch",
  "kind": "m",
  "img": "img/04-watchlist.jpg",
  "alt": "Watchlist com PETR4: preço, fonte do dado e plano educacional.",
  "titulo": "Watchlist",
  "sub": "Seus ativos em estudo",
  "can": [
   [
    "Editar a lista de ativos e atualizar as cotações.",
    82,
    21,
    24,
    5.2
   ],
   [
    "Filtrar por Estudar alta, Estudar baixa ou Neutros.",
    47,
    40,
    89,
    5.1
   ],
   [
    "Trocar o modelo de análise: Completo, Tendência, Price Action, Momentum, Volume…",
    50,
    58.2,
    90,
    7.5
   ],
   [
    "Ver preço, variação e a fonte do dado de cada ativo.",
    63,
    71.5,
    22,
    5.2
   ],
   [
    "Ler o plano educacional e a confiança do padrão.",
    49,
    81,
    83,
    11.4
   ],
   [
    "Conferir o estado do pregão e o horário da última barra.",
    49,
    89.8,
    86,
    3.6
   ]
  ],
  "guard": "O backend calcula; a IA interpreta dados históricos.",
  "grupo": "Descobrir e planejar",
  "onde": "Aba Watchlist (Monitoramento, no Modo Operador)",
  "objetivo": "Acompanhar de perto os ativos que você escolheu estudar.",
  "missao": [
   "Filtre por “Estudar alta”.",
   "Troque o modelo de análise.",
   "Confira a fonte e o horário do dado de um ativo."
  ],
  "quiz": {
   "q": "O selo “Fora do pregão” informa:",
   "o": [
    "Que o ativo foi suspenso.",
    "Que o mercado está fechado e mostra a última barra.",
    "Que o app está com erro."
   ],
   "a": 1,
   "why": "É o estado real do mercado, com o horário da última barra."
  }
 },
 {
  "id": "plano",
  "kind": "m",
  "img": "img/05-plano-setup.jpg",
  "alt": "Plano do setup com régua de invalidação, gatilho e alvo.",
  "titulo": "Plano do setup",
  "sub": "Antes de agir",
  "can": [
   [
    "Ver invalidação, gatilho e alvo, com o preço atual na régua.",
    49,
    41,
    83,
    6.3
   ],
   [
    "Ler o regime (ex.: alta) e se o setup é a favor da tendência.",
    36,
    47.6,
    57,
    2.8
   ],
   [
    "Ver o aviso de amostra insuficiente quando o histórico medido é pequeno.",
    31,
    51.4,
    48,
    2.5
   ],
   [
    "Abrir o ticket com “Simular compra…”.",
    49,
    66.5,
    83,
    5.2
   ],
   [
    "Estudar o ativo com o Bóris ou abrir os indicadores.",
    35,
    74.3,
    56,
    2.6
   ]
  ],
  "guard": "Níveis calculados por regra, nunca pela IA. Stop e alvo nunca são vetados.",
  "grupo": "Descobrir e planejar",
  "onde": "Card de um ativo, na Watchlist",
  "objetivo": "Saber onde a ideia se invalida, se confirma e termina, antes de agir.",
  "missao": [
   "Localize invalidação, gatilho e alvo na régua.",
   "Leia o regime e a marca “a favor da tendência”.",
   "Procure o aviso de amostra insuficiente."
  ],
  "quiz": {
   "q": "Quem calcula invalidação, gatilho e alvo?",
   "o": [
    "A IA.",
    "Regras determinísticas do app.",
    "O usuário, à mão."
   ],
   "a": 1,
   "why": "Níveis vêm do motor de cálculo. A IA só explica."
  }
 },
 {
  "id": "ordem",
  "kind": "m",
  "img": "img/06-ordem-virtual.jpg",
  "alt": "Ticket de compra simulada com custo estimado e aviso de operação simulada.",
  "titulo": "Ordem simulada",
  "sub": "O ticket",
  "can": [
   [
    "Ajustar a quantidade (lotes de 100).",
    50,
    37.4,
    80,
    5.2
   ],
   [
    "Ver o custo estimado antes de confirmar.",
    50,
    44.4,
    80,
    5
   ],
   [
    "Ler o estado: com o mercado fechado, a ordem fica pendente até a abertura e o caixa já é reservado.",
    50,
    53.6,
    80,
    11.3
   ],
   [
    "Saber que a execução é inteira ou nenhuma, sem preenchimento parcial.",
    49,
    62,
    78,
    3.3
   ],
   [
    "Confirmar que é operação simulada: nenhuma ordem real é enviada.",
    49,
    66.8,
    78,
    3.3
   ],
   [
    "Confirmar ou cancelar a compra.",
    50,
    73.4,
    80,
    5.2
   ]
  ],
  "guard": "Dinheiro virtual, sempre. Nenhuma ordem chega a corretora, bolsa ou banco.",
  "grupo": "Operar no simulador",
  "onde": "Card do ativo → Simular compra…",
  "objetivo": "Enviar uma ordem virtual sabendo o que vai acontecer.",
  "missao": [
   "Ajuste a quantidade.",
   "Leia o custo estimado.",
   "Leia o estado de execução.",
   "Confirme ou cancele."
  ],
  "quiz": {
   "q": "Uma ordem simulada pode ser executada pela metade?",
   "o": [
    "Sim, conforme a liquidez.",
    "Não: executa inteira ou é rejeitada.",
    "Só no Modo Operador."
   ],
   "a": 1,
   "why": "Execução tudo-ou-nada, por desenho."
  }
 },
 {
  "id": "pend",
  "kind": "m",
  "img": "img/07-ordem-pendente.jpg",
  "alt": "Aviso de ordem pendente registrada, com execução na abertura do próximo pregão.",
  "titulo": "Ordem pendente",
  "sub": "Execução simulada",
  "can": [
   [
    "Receber a confirmação: ordem pendente registrada, executa na abertura do próximo pregão.",
    50,
    83.5,
    50,
    11
   ],
   [
    "Ver o caixa disponível já reduzido no topo (valor reservado).",
    66,
    12.3,
    31,
    2.6
   ]
  ],
  "guard": "Cada ordem tem preço, quantidade, horário, tipo e status; rejeitadas mostram o motivo.",
  "grupo": "Operar no simulador",
  "onde": "Logo após confirmar, com o mercado fechado",
  "objetivo": "Entender o que acontece com uma ordem fora do pregão.",
  "missao": [
   "Confirme uma compra com o mercado fechado.",
   "Leia a mensagem de ordem pendente.",
   "Confira o caixa disponível no topo."
  ],
  "quiz": {
   "q": "Por que o caixa diminui com a ordem ainda pendente?",
   "o": [
    "Porque o valor foi gasto numa corretora.",
    "Porque o caixa é reservado na confirmação.",
    "Por erro do app."
   ],
   "a": 1,
   "why": "A reserva evita gastar duas vezes o mesmo saldo virtual."
  }
 },
 {
  "id": "port",
  "kind": "m",
  "img": "img/08-portfolio.jpg",
  "alt": "Portfólio com patrimônio total, caixa disponível e indicação de carteira simulada.",
  "titulo": "Portfólio",
  "sub": "O resultado",
  "can": [
   [
    "Abrir o Operador IA (modo avançado, também com execução simulada).",
    50,
    21,
    94,
    5.6
   ],
   [
    "Ver patrimônio total e resultado aberto.",
    50,
    41,
    92,
    5.6
   ],
   [
    "Ver caixa disponível e valor em posições.",
    50,
    48.7,
    92,
    4.1
   ],
   [
    "Entender o estado vazio e ir à Watchlist para a primeira compra simulada.",
    50,
    65.5,
    94,
    23
   ],
   [
    "Abrir o histórico de operações.",
    50,
    81.6,
    94,
    5.6
   ]
  ],
  "guard": "Carteira SIMULADA: ganhos e perdas aparecem sem maquiagem.",
  "grupo": "Operar no simulador",
  "onde": "Aba Portfólio (Posições, no Modo Operador)",
  "objetivo": "Ver resultado, caixa e o que está em posições.",
  "missao": [
   "Compare patrimônio total e caixa disponível.",
   "Abra o histórico de operações.",
   "Localize o acesso ao Operador IA."
  ],
  "quiz": {
   "q": "Patrimônio, caixa e resultado são calculados por:",
   "o": [
    "Regras determinísticas.",
    "Estimativa da IA.",
    "Média dos usuários."
   ],
   "a": 0,
   "why": "Número financeiro nunca vem da IA."
  }
 },
 {
  "id": "opc",
  "kind": "m",
  "img": "img/10-opcoes.png",
  "alt": "Aba Opções com PETR4 em carteira: 100 ações livres para lastro, evolução da semana, volatilidade, suporte e resistência.",
  "titulo": "Opções",
  "sub": "Estudo sobre a carteira",
  "can": [
   [
    "Escolher um ativo da carteira: o card mostra quantas ações você tem e quantas estão livres como lastro.",
    50,
    60,
    83,
    6.6
   ],
   [
    "Ver como a semana evoluiu: cada segmento é um pregão, colorido pelo regime medido naquele dia.",
    50,
    69.5,
    83,
    4.8
   ],
   [
    "Ler as referências do ativo: volatilidade (HV21), suporte e resistência.",
    45,
    77,
    72,
    7.3
   ],
   [
    "Saber se há estrutura aberta e quantas vigias você tem.",
    50,
    82.3,
    83,
    2.4
   ],
   [
    "Abrir o card para escolher o que fazer com as ações.",
    86,
    58,
    10,
    4
   ],
   [
    "Lembrete fixo: dinheiro virtual, nenhuma ordem sai para corretora, bolsa ou banco.",
    50,
    31.6,
    80,
    6.5
   ]
  ],
  "guard": "Cada segmento mostra o regime medido naquele dia, não uma previsão do próximo.",
  "grupo": "Opções",
  "onde": "Aba Opções",
  "objetivo": "Estudar opções sobre as ações que você já tem.",
  "missao": [
   "Localize o ativo em carteira e quantas ações estão livres como lastro.",
   "Leia a evolução da semana.",
   "Toque no card do ativo."
  ],
  "quiz": {
   "q": "Sem ações em carteira, a aba Opções:",
   "o": [
    "Libera qualquer opção.",
    "Explica que opções são estudadas sobre as ações da carteira virtual.",
    "Bloqueia a conta."
   ],
   "a": 1,
   "why": "As opções aqui são estudadas sobre as ações que você já tem."
  }
 },
 {
  "id": "opcobj",
  "kind": "m",
  "img": "img/11-opcoes-objetivos.png",
  "alt": "Objetivos para as 100 ações de PETR4: proteger de queda, gerar renda e proteger com custo baixo.",
  "titulo": "Opções · objetivos",
  "sub": "O que fazer com as ações",
  "can": [
   [
    "Escolher o objetivo: proteger de queda, gerar renda ou proteger com custo baixo.",
    50,
    34.7,
    84,
    4.6
   ],
   [
    "Ler cada objetivo em linguagem simples, com o termo técnico entre parênteses.",
    50,
    53,
    84,
    17
   ],
   [
    "Ver, antes de decidir, o que se perde em cada objetivo (o prêmio, ou o ganho acima do teto).",
    35,
    58.7,
    56,
    2.2
   ],
   [
    "Tocar nos termos sublinhados para abrir uma explicação.",
    50,
    41,
    84,
    2.8
   ],
   [
    "Voltar ao resumo da carteira.",
    10,
    23,
    14,
    2.4
   ]
  ],
  "guard": "Você vê o pior caso antes de decidir.",
  "grupo": "Opções",
  "onde": "Opções → card do ativo",
  "objetivo": "Escolher o que fazer com as ações.",
  "missao": [
   "Leia os três objetivos.",
   "Toque em um termo sublinhado.",
   "Compare o que se perde em cada objetivo."
  ],
  "quiz": {
   "q": "“Gerar renda” com venda coberta limita:",
   "o": [
    "A perda máxima.",
    "O ganho acima de um teto.",
    "O prazo da ação."
   ],
   "a": 1,
   "why": "Você recebe um prêmio e abre mão do ganho acima do teto."
  }
 },
 {
  "id": "opcpiso",
  "kind": "m",
  "img": "img/12-opcoes-piso.png",
  "alt": "Escolha do piso da proteção: vencimentos, três níveis de put, perda máxima e custo da proteção.",
  "titulo": "Opções · escolher o piso",
  "sub": "Proteger de queda",
  "can": [
   [
    "Escolher o vencimento (por exemplo, 42 ou 70 dias).",
    34,
    40.2,
    55,
    6.6
   ],
   [
    "Comparar três níveis de piso: mais protegido, equilibrado e mais barato.",
    50,
    66.5,
    84,
    43.5
   ],
   [
    "Ver a perda máxima de cada nível, em reais e em barras.",
    50,
    52,
    76,
    3.6
   ],
   [
    "Ver o custo da proteção.",
    50,
    56,
    76,
    3
   ]
  ],
  "guard": "Valores de opções nesta captura vêm de um ambiente de demonstração: são ilustrativos.",
  "grupo": "Opções",
  "onde": "Opções → Proteger de queda",
  "objetivo": "Escolher o piso da proteção.",
  "missao": [
   "Escolha o vencimento.",
   "Compare os três níveis.",
   "Observe a perda máxima e o custo da proteção."
  ],
  "quiz": {
   "q": "Um piso mais alto (“mais protegido”) tende a:",
   "o": [
    "Reduzir a perda máxima.",
    "Eliminar o custo.",
    "Garantir lucro."
   ],
   "a": 0,
   "why": "Mais proteção limita a perda, e nada garante lucro."
  }
 },
 {
  "id": "pior",
  "kind": "m",
  "img": "img/13-opcoes-pior-caso.jpg",
  "alt": "Pior caso, melhor caso e equilíbrio da proteção, com o botão Escolher este.",
  "titulo": "Opções · pior caso",
  "sub": "Antes de escolher",
  "can": [
   [
    "Mover o controle e comparar “só as ações” com “com a estrutura” para um preço no vencimento.",
    49,
    20.4,
    74,
    3.5
   ],
   [
    "Ver os dois resultados lado a lado, em reais.",
    50,
    27,
    76,
    4.8
   ],
   [
    "Ler o pior caso, o melhor caso e o equilíbrio em linguagem direta.",
    50,
    52.8,
    88,
    14.2
   ],
   [
    "Escolher a estrutura.",
    50,
    65,
    83,
    5.7
   ],
   [
    "Ver o custo da escolha na sua cota (aqui: sem custo).",
    14,
    69.4,
    16,
    2.2
   ],
   [
    "Ler o aviso: conteúdo educacional, dados de fim de pregão.",
    50,
    78,
    92,
    6
   ]
  ],
  "guard": "O pior caso vem antes de qualquer decisão.",
  "grupo": "Opções",
  "onde": "Opções → depois de escolher um nível",
  "objetivo": "Ler o pior caso antes de decidir.",
  "missao": [
   "Mova o controle de preço.",
   "Leia pior caso, melhor caso e equilíbrio.",
   "Veja o custo na sua cota."
  ],
  "quiz": {
   "q": "Por que olhar o pior caso antes de escolher?",
   "o": [
    "Porque é o resultado mais provável.",
    "Para saber quanto se pode perder.",
    "Porque o app o recomenda."
   ],
   "a": 1,
   "why": "Conhecer a perda máxima é a base da decisão com risco definido."
  }
 },
 {
  "id": "payoff",
  "kind": "m",
  "img": "img/14-opcoes-payoff.jpg",
  "alt": "Gráfico de resultado no vencimento com legenda numerada: piso, equilíbrio, perda máxima e preço médio.",
  "titulo": "Opções · resultado no vencimento",
  "sub": "O gráfico",
  "can": [
   [
    "Ler o gráfico: linha cheia com a estrutura, tracejada só com as ações.",
    50,
    25.5,
    84,
    19.7
   ],
   [
    "Conferir os pontos numerados: piso, equilíbrio, perda máxima e preço médio.",
    50,
    46.6,
    88,
    20.3
   ],
   [
    "Saber se há teto: “sem teto, o ganho acompanha a alta, menos o prêmio”.",
    50,
    63,
    84,
    10.4
   ],
   [
    "Simular: “e se a ação fechar a tal preço no vencimento?”.",
    50,
    80,
    84,
    20
   ]
  ],
  "guard": "Linguagem de cenário, nunca de promessa.",
  "grupo": "Opções",
  "onde": "Opções → Ver os números",
  "objetivo": "Ler o gráfico de resultado no vencimento.",
  "missao": [
   "Identifique a linha cheia e a tracejada.",
   "Localize piso, equilíbrio e perda máxima.",
   "Teste um preço no vencimento."
  ],
  "quiz": {
   "q": "No gráfico, a linha tracejada mostra:",
   "o": [
    "O resultado só com as ações.",
    "O resultado com a estrutura.",
    "A previsão do app."
   ],
   "a": 0,
   "why": "Linha cheia = com a estrutura; tracejada = só as ações."
  }
 },
 {
  "id": "confest",
  "kind": "m",
  "img": "img/15-opcoes-confirmar-estudo.jpg",
  "alt": "Confirmar a estrutura no Modo Estudo, com a nota de que no Estudo nada é executado e o botão Criar vigia.",
  "titulo": "Opções · confirmar (Estudo)",
  "sub": "Só leitura",
  "can": [
   [
    "Rever o pior e o melhor caso antes de qualquer decisão.",
    50,
    44,
    88,
    14
   ],
   [
    "Conferir a estrutura: vencimento, perna comprada e prêmio.",
    50,
    60,
    84,
    13.3
   ],
   [
    "Ver quantos contratos e ações entram e se as ações ficam livres como lastro.",
    45,
    70.5,
    76,
    6.5
   ],
   [
    "Entender que, no Modo Estudo, nada é executado: é a leitura de como funcionaria.",
    50,
    79.5,
    90,
    5
   ],
   [
    "Criar uma vigia para acompanhar a estrutura.",
    50,
    86.5,
    83,
    5.2
   ]
  ],
  "guard": "No Estudo você aprende a estrutura; executar fica para o Modo Operador.",
  "grupo": "Opções",
  "onde": "Opções → Escolher este (Modo Estudo)",
  "objetivo": "Rever a estrutura antes de decidir, sem executar.",
  "missao": [
   "Releia o pior caso.",
   "Confira a estrutura e o lastro.",
   "Leia por que nada é executado no Estudo."
  ],
  "quiz": {
   "q": "No Modo Estudo, “Escolher este” executa a estrutura?",
   "o": [
    "Sim.",
    "Não: é a leitura de como funcionaria.",
    "Só com mercado aberto."
   ],
   "a": 1,
   "why": "No Estudo a IA orienta e você decide; nada é executado."
  }
 },
 {
  "id": "termo",
  "kind": "m",
  "img": "img/16-operador-termo.jpg",
  "alt": "Termo de Responsabilidade do Modo Operador, com aceite liberado só ao final da leitura.",
  "titulo": "Termo do Operador",
  "sub": "Antes de ativar",
  "can": [
   [
    "Ler o termo até o fim: o Operador é ferramenta de decisão e disciplina, não recomendação.",
    50,
    45.5,
    80,
    33.9
   ],
   [
    "Saber que o texto precisa ser rolado até o fim para liberar o aceite.",
    50,
    64.2,
    60,
    2.4
   ],
   [
    "Marcar que leu e entende que pode perder dinheiro operando por conta e risco.",
    50,
    68.5,
    84,
    4.7
   ],
   [
    "Continuar no Estudo ou ativar o Modo Operador.",
    50,
    76,
    80,
    6.6
   ]
  ],
  "guard": "As decisões diretas só são liberadas depois da leitura e do aceite.",
  "grupo": "Modo Operador",
  "onde": "Perfil → Modo de trabalho → Operador",
  "objetivo": "Entender o compromisso antes de ativar o Operador.",
  "missao": [
   "Role o texto até o fim.",
   "Marque a confirmação de leitura.",
   "Decida entre continuar no Estudo ou ativar."
  ],
  "quiz": {
   "q": "O aceite do termo fica disponível:",
   "o": [
    "Imediatamente.",
    "Só depois de rolar o texto até o fim.",
    "Só com plano pago."
   ],
   "a": 1,
   "why": "“Leia até o fim para habilitar o aceite.”"
  }
 },
 {
  "id": "opcaberta",
  "kind": "m",
  "img": "img/17-opcoes-estrutura-aberta.jpg",
  "alt": "Aba Opções no Modo Operador com PETR4: 100 ações travadas como lastro e uma estrutura aberta.",
  "titulo": "Opções · estrutura aberta",
  "sub": "Modo Operador",
  "can": [
   [
    "Ver que a carteira tem uma estrutura aberta sobre o ativo.",
    50,
    75.7,
    77,
    4.4
   ],
   [
    "Notar que as 100 ações passam a ficar travadas como lastro (0 livres).",
    35,
    54,
    56,
    2.1
   ],
   [
    "Acompanhar a semana, a volatilidade, o suporte e a resistência do ativo.",
    50,
    66.4,
    77,
    12.7
   ],
   [
    "Ver quantas vigias há.",
    81,
    75.2,
    14,
    2.4
   ],
   [
    "Abrir o card do ativo.",
    50,
    51.3,
    84,
    4
   ]
  ],
  "guard": "Execução simulada. Códigos “MOCK” indicam o ambiente de demonstração.",
  "grupo": "Modo Operador",
  "onde": "Modo Operador → Opções",
  "objetivo": "Acompanhar a estrutura aberta sobre o ativo.",
  "missao": [
   "Observe as ações travadas como lastro.",
   "Leia a estrutura aberta no card.",
   "Confira o número de vigias."
  ],
  "quiz": {
   "q": "Com a estrutura aberta, as ações usadas como lastro ficam:",
   "o": [
    "Livres para vender.",
    "Travadas.",
    "Dobradas."
   ],
   "a": 1,
   "why": "O card mostra “0 livres para lastro”: as ações estão comprometidas."
  }
 },
 {
  "id": "boris",
  "kind": "m",
  "img": "img/03-boris-assistente.jpg",
  "alt": "Apresentação do Bóris: não recomenda compra ou venda e não envia ordem.",
  "titulo": "Bóris, o assistente",
  "sub": "Em qualquer tela do Estudo",
  "can": [
   [
    "Saber o que ele não faz: não recomenda compra ou venda e não envia ordem.",
    50,
    47.5,
    80,
    11.8
   ],
   [
    "Contar com a base de estudo: indicadores, estrutura de preço, setups e vocabulário da B3.",
    50,
    60,
    80,
    9.2
   ],
   [
    "Chamá-lo pela coruja flutuante, em qualquer tela do Estudo.",
    50,
    70,
    80,
    6.8
   ],
   [
    "Conversar agora ou deixar para depois.",
    50,
    82.1,
    80,
    11.3
   ]
  ],
  "guard": "O Bóris é o professor, nunca o operador.",
  "grupo": "Bóris",
  "onde": "Coruja flutuante, em qualquer tela do Estudo",
  "objetivo": "Tirar dúvidas com quem conhece a tela em que você está.",
  "missao": [
   "Toque na coruja.",
   "Leia o que ele não faz.",
   "Pergunte algo concreto, como o que invalidaria a entrada."
  ],
  "quiz": {
   "q": "O Bóris pode dizer “compre agora”?",
   "o": [
    "Sim, se a confluência for alta.",
    "Não: ele explica, não recomenda.",
    "Só no Modo Operador."
   ],
   "a": 1,
   "why": "O Bóris é o professor, nunca o operador."
  }
 },
 {
  "id": "web1",
  "kind": "w",
  "img": "img/web-acompanhar.jpg",
  "alt": "Versão web, aba Acompanhar.",
  "titulo": "Web · Acompanhar",
  "sub": "No navegador",
  "can": [
   [
    "Percorrer os setups da watchlist em carrossel, cada um com anel de confiança.",
    49,
    71,
    84,
    22
   ],
   [
    "Ver o estado do mercado e do horário de pregão.",
    34,
    23,
    64,
    3.2
   ],
   [
    "Ver o saldo virtual e o caixa no topo.",
    83,
    17,
    16,
    10
   ]
  ],
  "guard": "Mesmo conteúdo do celular, em layout largo.",
  "grupo": "Versão web",
  "onde": "Navegador · aba Acompanhar",
  "objetivo": "Usar o app em tela larga.",
  "missao": [
   "Abra o app no navegador.",
   "Percorra o carrossel de setups."
  ],
  "quiz": {
   "q": "Dados e avisos na versão web são:",
   "o": [
    "Menos completos.",
    "Os mesmos do celular.",
    "Fictícios."
   ],
   "a": 1,
   "why": "É o mesmo app: mesmo carimbo de dado e mesmos avisos."
  }
 },
 {
  "id": "web2",
  "kind": "w",
  "img": "img/web-plano-setup.jpg",
  "alt": "Versão web, Watchlist com dois cards lado a lado.",
  "titulo": "Web · Watchlist",
  "sub": "Cards em colunas",
  "can": [
   [
    "Comparar o plano de dois ativos lado a lado.",
    50,
    36,
    88,
    12.4
   ],
   [
    "Ler regime e amostra de cada setup.",
    50,
    52,
    88,
    10.6
   ],
   [
    "Abrir a compra simulada direto do card.",
    50,
    81,
    88,
    8.6
   ]
  ],
  "guard": "Em telas largas, os cards se organizam em colunas.",
  "grupo": "Versão web",
  "onde": "Navegador · Watchlist",
  "objetivo": "Comparar ativos lado a lado.",
  "missao": [
   "Compare o plano de dois ativos.",
   "Abra a compra simulada a partir do card."
  ],
  "quiz": {
   "q": "Em telas largas, a Watchlist:",
   "o": [
    "Organiza os cards em colunas.",
    "Muda os cálculos.",
    "Esconde o plano."
   ],
   "a": 0,
   "why": "Só o layout muda."
  }
 },
 {
  "id": "web3",
  "kind": "w",
  "img": "img/web-portfolio.jpg",
  "alt": "Versão web, Portfólio.",
  "titulo": "Web · Portfólio",
  "sub": "Carteira simulada",
  "can": [
   [
    "Abrir o Operador IA.",
    49,
    36.4,
    86,
    9.6
   ],
   [
    "Ver patrimônio total e caixa disponível.",
    28,
    70,
    44,
    20
   ],
   [
    "Ver resultado aberto e valor em posições.",
    71,
    70,
    42,
    20
   ]
  ],
  "guard": "O aviso de carteira simulada acompanha todas as telas.",
  "grupo": "Versão web",
  "onde": "Navegador · Portfólio",
  "objetivo": "Ver a carteira simulada no navegador.",
  "missao": [
   "Confira patrimônio e caixa.",
   "Localize o acesso ao Operador IA."
  ],
  "quiz": {
   "q": "O aviso de carteira simulada aparece:",
   "o": [
    "Só no celular.",
    "Em todas as telas.",
    "Nunca."
   ],
   "a": 1,
   "why": "O aviso acompanha todas as telas."
  }
 }
];
