/* Dados das telas do Boris+ (guia de treinamento). Capturas de 09/10/2026 (08-portfolio, web-portfolio e web-acompanhar refeitas em 10/10/2026 com o cartão do Operador IA), app local, dinheiro virtual.
   Cada ponto: [frase curta, x%, y%, largura%, altura%, título, explicação] — a frase curta vai no cartão de vidro; título + explicação, na aba Pontos (sem repetir a frase). */
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
    5.2,
    "Seu nome",
    "Só para o Bóris falar com você pelo nome. É opcional."
   ],
   [
    "Definir o orçamento simulado inicial, em dinheiro virtual.",
    50,
    60,
    78,
    4.8,
    "Orçamento simulado",
    "O saldo fictício com que você treina. Ele define o tamanho das posições e do risco; nenhum valor sai de conta bancária."
   ],
   [
    "Escolher o perfil de risco: conservador, moderado ou agressivo.",
    50,
    69,
    78,
    4.6,
    "Perfil de risco",
    "Conservador, moderado ou agressivo. A IA leva o seu perfil em conta ao comentar o risco da sua carteira; nada muda no mercado."
   ],
   [
    "Entrar na mesa e começar a treinar.",
    50,
    76,
    78,
    5.4,
    "Entrar na mesa",
    "Conclui a configuração. A conta nasce limpa, sem posições de demonstração, e você cai direto no Acompanhar."
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
    7,
    "Saldo virtual",
    "Patrimônio simulado e variação do dia, sempre à vista. O “caixa” é o dinheiro livre; o resto está em posições."
   ],
   [
    "Abrir perfil e configurações.",
    90,
    10.5,
    11.5,
    5,
    "Perfil e ajustes",
    "Troca de modo (Estudo ou Operador), conta, plano e preferências. A Ajuda, onde fica este guia, também mora aqui."
   ],
   [
    "Saber se o mercado está aberto ou fechado e quando abre.",
    22,
    13,
    42,
    3,
    "Estado do mercado",
    "Aberto ou fechado, com o horário de abertura. Fora do pregão, os preços são os do último fechamento, e o app avisa."
   ],
   [
    "Ler o resumo do dia: carteira, acumulado e operações.",
    50,
    45.5,
    91,
    21,
    "Resumo do dia",
    "Resultado da carteira no dia, acumulado e número de operações. Numa conta nova tudo começa zerado."
   ],
   [
    "Acompanhar a curva do patrimônio simulado.",
    50,
    73,
    82,
    11,
    "Curva do patrimônio",
    "Cada dia que você abre o app vira um ponto. Com poucos dias a curva é curta: o app prefere dizer isso a desenhar uma linha estimada."
   ],
   [
    "Ver estados honestos: sem histórico, o app diz “Não há dados suficientes para concluir”.",
    50,
    84,
    86,
    8.5,
    "Vazio explicado",
    "Sem dados, a tela diz “Não há dados suficientes para concluir”. É regra do produto: nunca preencher o vazio com número inventado."
   ],
   [
    "Navegar pelas abas: Acompanhar, Radar, Watchlist, Portfólio e Opções.",
    50,
    96,
    100,
    7.5,
    "As cinco abas",
    "Acompanhar, Radar, Watchlist, Portfólio e Opções. No Modo Operador, três delas ganham vocabulário de mesa: Mesa, Monitoramento e Posições."
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
    5.4,
    "IA no top-N",
    "Pede à IA que explique os melhores resultados da varredura. Gasta cota; a lista em si, que vem do motor, não gasta."
   ],
   [
    "Buscar um ticker específico.",
    36,
    41.4,
    66,
    5,
    "Busca por ticker",
    "Procure um ativo específico entre os varridos, em vez de rolar a lista inteira."
   ],
   [
    "Ver o período em uso (ex.: 1 ano, 252 pregões).",
    33,
    47,
    59,
    3.3,
    "Período em uso",
    "A janela de histórico da varredura (aqui, 1 ano ou 252 pregões). Todo sinal é calculado sobre esse período."
   ],
   [
    "Saber quantos ativos foram varridos e quantos ficaram sem dados.",
    45,
    55,
    84,
    2.3,
    "Cobertura da varredura",
    "Quantos ativos foram lidos e quantos ficaram sem dados. Ativo sem dado não recebe sinal: o Radar não adivinha."
   ],
   [
    "Abrir “Como o Radar analisa” para entender o método.",
    50,
    60,
    91,
    5,
    "Como o Radar analisa",
    "O motor reconhece setups no gráfico e ordena por confluência, que é quantos sinais independentes apontam na mesma direção."
   ],
   [
    "Ler o card: plano educacional, confiança e o padrão detectado.",
    49,
    78.5,
    83,
    11.4,
    "Card do ativo",
    "Traz o plano educacional (“estudar alta” ou “estudar baixa”), a confiança e o padrão. O anel mede aderência ao padrão em dados passados, não a probabilidade de resultado."
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
    5.2,
    "Editar e atualizar",
    "Escolha quais ativos acompanhar e atualize as cotações. O Radar sugere; quem decide o que entra na lista é você."
   ],
   [
    "Filtrar por Estudar alta, Estudar baixa ou Neutros.",
    47,
    40,
    89,
    5.1,
    "Filtros",
    "Estudar alta, Estudar baixa ou Neutros. “Reordenar” volta à ordem por oportunidade (confluência)."
   ],
   [
    "Trocar o modelo de análise: Completo, Tendência, Price Action, Momentum, Volume…",
    50,
    58.2,
    90,
    7.5,
    "Modelo de análise",
    "Completo, Tendência, Price Action, Momentum, Volume… Cada modelo muda o ângulo da leitura. O backend calcula; a IA interpreta dados históricos."
   ],
   [
    "Ver preço, variação e a fonte do dado de cada ativo.",
    63,
    71.5,
    22,
    5.2,
    "Preço e fonte",
    "Preço, variação do dia e de onde veio o dado (aqui, Yahoo). Fonte e horário ficam sempre visíveis."
   ],
   [
    "Ler o plano educacional e a confiança do padrão.",
    49,
    81,
    83,
    11.4,
    "Plano educacional",
    "A leitura do motor para o ativo, com a confiança do padrão. É material de estudo, não ordem."
   ],
   [
    "Conferir o estado do pregão e o horário da última barra.",
    49,
    89.8,
    86,
    3.6,
    "Estado do pregão",
    "Fora do pregão, a tela mostra a última barra de 15 minutos e avisa que a condição volta a ser verificada na abertura."
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
    6.3,
    "Régua do plano",
    "Invalidação é o preço que derruba a ideia; gatilho, onde ela se confirma; alvo, até onde vale esperar. O ponto branco é o preço de agora."
   ],
   [
    "Ler o regime (ex.: alta) e se o setup é a favor da tendência.",
    36,
    47.6,
    57,
    2.8,
    "Regime",
    "Alta, baixa ou lateral, e se o setup está a favor ou contra a tendência. Operar contra o regime pede mais cuidado."
   ],
   [
    "Ver o aviso de amostra insuficiente quando o histórico medido é pequeno.",
    31,
    51.4,
    48,
    2.5,
    "Amostra insuficiente",
    "Quando o padrão ocorreu poucas vezes (menos de 40), o histórico medido diz pouco. “Sinal técnico” e “histórico medido” são coisas diferentes."
   ],
   [
    "Abrir o ticket com “Simular compra…”.",
    49,
    66.5,
    83,
    5.2,
    "Simular compra",
    "Abre o ticket com o plano pronto. Mesmo quando o parecer é “não operar”, o app nunca impede você de definir stop e alvo."
   ],
   [
    "Estudar o ativo com o Bóris ou abrir os indicadores.",
    35,
    74.3,
    56,
    2.6,
    "Estudar este ativo",
    "Pede à IA a leitura em quatro passos: o que cada indicador marca, quais confirmam ou divergem, como se combinam e o que mudaria a leitura. Gasta uma análise da cota."
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
    5.2,
    "Quantidade",
    "Em lotes de 100. O custo estimado acompanha a quantidade que você escolhe."
   ],
   [
    "Ver o custo estimado antes de confirmar.",
    50,
    44.4,
    80,
    5,
    "Custo estimado",
    "Preço × quantidade, antes de confirmar. Nenhum valor real é cobrado."
   ],
   [
    "Ler o estado: com o mercado fechado, a ordem fica pendente até a abertura e o caixa já é reservado.",
    50,
    53.6,
    80,
    11.3,
    "Mercado fechado",
    "A ordem fica pendente e executa ao preço de abertura do próximo pregão. O caixa é reservado já na confirmação."
   ],
   [
    "Saber que a execução é inteira ou nenhuma, sem preenchimento parcial.",
    49,
    62,
    78,
    3.3,
    "Tudo ou nada",
    "Por desenho, a ordem executa inteira ou é rejeitada, com o motivo. Preenchimento parcial não existe no Boris+."
   ],
   [
    "Confirmar que é operação simulada: nenhuma ordem real é enviada.",
    49,
    66.8,
    78,
    3.3,
    "Operação simulada",
    "Paper trading: nenhuma ordem vai para corretora, bolsa ou banco."
   ],
   [
    "Confirmar ou cancelar a compra.",
    50,
    73.4,
    80,
    5.2,
    "Confirmar ou cancelar",
    "Confirmar registra a ordem. Cancelar volta ao card sem enviar nada."
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
    11,
    "Ordem pendente",
    "Registrada com o mercado fechado; executa ao preço de abertura do próximo pregão."
   ],
   [
    "Ver o caixa disponível já reduzido no topo (valor reservado).",
    66,
    12.3,
    31,
    2.6,
    "Caixa reservado",
    "O caixa do topo já desconta a ordem pendente. É assim que o app evita gastar duas vezes o mesmo saldo."
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
  "nh": 1775,
  "alt": "Portfólio com patrimônio total, caixa disponível e indicação de carteira simulada.",
  "titulo": "Portfólio",
  "sub": "O resultado",
  "can": [
   [
    "Ver o estado do Operador IA e abri-lo.",
    47.3,
    25.5,
    88.5,
    16.9,
    "Operador IA",
    "O cartão no topo diz se o Operador IA está ligado ou desligado no servidor e se ele só avisa ou também executa. Descreve a configuração, não que ele esteja rodando agora. No Modo Estudo ele só sinaliza; no Modo Operador a execução segue simulada. Toque para abrir."
   ],
   [
    "Ver patrimônio total e resultado aberto.",
    47.3,
    50.1,
    88.5,
    6.2,
    "Patrimônio e resultado aberto",
    "Patrimônio total é caixa mais posições. Resultado aberto é o ganho ou a perda das posições que ainda não foram vendidas."
   ],
   [
    "Ver caixa disponível e valor em posições.",
    47.3,
    56.3,
    88.5,
    4.5,
    "Caixa e posições",
    "Dinheiro livre de um lado, valor em posições do outro. Se tudo está em posições, não sobra saldo para novas ordens."
   ],
   [
    "Entender o estado vazio e ir à Watchlist para a primeira compra simulada.",
    47.3,
    73.5,
    88.5,
    23.3,
    "Portfólio vazio",
    "Sem posições, o app indica o próximo passo: ir à Watchlist e simular a primeira compra."
   ],
   [
    "Abrir o histórico de operações.",
    47.3,
    89.4,
    88.5,
    5.2,
    "Histórico de operações",
    "Registra cada decisão, inclusive as ordens recusadas e o motivo. Rever as recusas ensina tanto quanto as aceitas."
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
    6.6,
    "Ativo em carteira",
    "Opções aqui são estudadas sobre ações que você já tem. O card mostra quantas ações há e quantas estão livres como lastro."
   ],
   [
    "Ver como a semana evoluiu: cada segmento é um pregão, colorido pelo regime medido naquele dia.",
    50,
    69.5,
    83,
    4.8,
    "Evolução da semana",
    "Um segmento por pregão fechado, colorido pelo regime medido naquele dia. Descreve o passado; não é previsão do próximo."
   ],
   [
    "Ler as referências do ativo: volatilidade (HV21), suporte e resistência.",
    45,
    77,
    72,
    7.3,
    "Referências do ativo",
    "HV21 é a volatilidade histórica de 21 dias; suporte e resistência dão o contexto para escolher proteção ou renda."
   ],
   [
    "Saber se há estrutura aberta e quantas vigias você tem.",
    50,
    82.3,
    83,
    2.4,
    "Estruturas e vigias",
    "Mostra se há estrutura aberta sobre o ativo e quantas vigias você criou para acompanhar."
   ],
   [
    "Abrir o card para escolher o que fazer com as ações.",
    86,
    58,
    10,
    4,
    "Abrir o card",
    "Leva ao que fazer com as ações. Abrir um ativo não gasta consultas da sua cota."
   ],
   [
    "Lembrete fixo: dinheiro virtual, nenhuma ordem sai para corretora, bolsa ou banco.",
    50,
    31.6,
    80,
    6.5,
    "Aviso fixo",
    "Dinheiro virtual: nenhuma ordem sai para corretora, bolsa ou banco."
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
    4.6,
    "O que você quer fazer?",
    "Três objetivos: proteger de queda, gerar renda ou proteger com custo baixo. Cada um leva a uma estrutura de opções diferente."
   ],
   [
    "Ler cada objetivo em linguagem simples, com o termo técnico entre parênteses.",
    50,
    53,
    84,
    17,
    "Objetivo em linguagem simples",
    "O app diz primeiro o que a estrutura faz por você e só depois o nome técnico (put protetora, venda coberta, collar)."
   ],
   [
    "Ver, antes de decidir, o que se perde em cada objetivo (o prêmio, ou o ganho acima do teto).",
    35,
    58.7,
    56,
    2.2,
    "O que se perde",
    "Cada objetivo mostra aquilo de que você abre mão: o prêmio pago ou o ganho acima de um teto."
   ],
   [
    "Tocar nos termos sublinhados para abrir uma explicação.",
    50,
    41,
    84,
    2.8,
    "Termos sublinhados",
    "Toque no sublinhado pontilhado para abrir o verbete. É texto escrito à mão e não gasta cota."
   ],
   [
    "Voltar ao resumo da carteira.",
    10,
    23,
    14,
    2.4,
    "Voltar",
    "Retorna ao resumo da carteira de opções."
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
    6.6,
    "Vencimento",
    "A data até a qual a proteção vale. O app mostra os dias até o vencimento; prazos maiores tendem a custar mais."
   ],
   [
    "Comparar três níveis de piso: mais protegido, equilibrado e mais barato.",
    50,
    66.5,
    84,
    43.5,
    "Três níveis",
    "Mais protegido, equilibrado e mais barato: o piso (strike da put) sobe ou desce, trocando proteção por custo."
   ],
   [
    "Ver a perda máxima de cada nível, em reais e em barras.",
    50,
    52,
    76,
    3.6,
    "Perda máxima",
    "O quanto você pode perder nas 100 ações, por mais que o preço caia abaixo do piso."
   ],
   [
    "Ver o custo da proteção.",
    50,
    56,
    76,
    3,
    "Custo da proteção",
    "O prêmio pago pela put. Se a ação não cair, ele é o que se perde por ter se protegido."
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
    3.5,
    "Preço no vencimento",
    "Mova o controle para ver o resultado, com e sem a estrutura, em cada preço possível."
   ],
   [
    "Ver os dois resultados lado a lado, em reais.",
    50,
    27,
    76,
    4.8,
    "Só as ações × com a estrutura",
    "A comparação direta: onde a estrutura ajuda (nas quedas) e onde pesa (nas altas, por causa do prêmio)."
   ],
   [
    "Ler o pior caso, o melhor caso e o equilíbrio em linguagem direta.",
    50,
    52.8,
    88,
    14.2,
    "Pior, melhor e equilíbrio",
    "Pior caso é a perda máxima; melhor caso, o que se ganha se a ação subir; equilíbrio, o preço em que o resultado é zero."
   ],
   [
    "Escolher a estrutura.",
    50,
    65,
    83,
    5.7,
    "Escolher este",
    "Avança para a confirmação. No Modo Estudo, nada é executado."
   ],
   [
    "Ver o custo da escolha na sua cota (aqui: sem custo).",
    14,
    69.4,
    16,
    2.2,
    "Custo na sua cota",
    "Quantas consultas ao serviço de dados a escolha consome. Aqui, nenhuma."
   ],
   [
    "Ler o aviso: conteúdo educacional, dados de fim de pregão.",
    50,
    78,
    92,
    6,
    "Aviso de dados",
    "Dados de fim de pregão, possivelmente atrasados. Conteúdo educacional, nunca ordem."
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
    19.7,
    "O gráfico",
    "No eixo horizontal, o preço da ação no vencimento; no vertical, o seu resultado. Linha cheia é com a estrutura; tracejada, só com as ações."
   ],
   [
    "Conferir os pontos numerados: piso, equilíbrio, perda máxima e preço médio.",
    50,
    46.6,
    88,
    20.3,
    "Pontos numerados",
    "Piso, equilíbrio, perda máxima e preço médio, marcados no gráfico e explicados abaixo, cada um com o seu verbete."
   ],
   [
    "Saber se há teto: “sem teto, o ganho acompanha a alta, menos o prêmio”.",
    50,
    63,
    84,
    10.4,
    "Teto ou não",
    "“Sem teto” quer dizer que o ganho acompanha a alta da ação, descontado o prêmio pago."
   ],
   [
    "Simular: “e se a ação fechar a tal preço no vencimento?”.",
    50,
    80,
    84,
    20,
    "E se…?",
    "Um simulador de cenário: arraste o preço e veja o resultado de cada alternativa. É estudo, não previsão."
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
    14,
    "Pior e melhor caso",
    "Antes de qualquer decisão, o app repete os extremos em palavras simples."
   ],
   [
    "Conferir a estrutura: vencimento, perna comprada e prêmio.",
    50,
    60,
    84,
    13.3,
    "A estrutura",
    "Vencimento, perna comprada (a put) e prêmio por ação: o que seria negociado se você executasse."
   ],
   [
    "Ver quantos contratos e ações entram e se as ações ficam livres como lastro.",
    45,
    70.5,
    76,
    6.5,
    "Contratos e lastro",
    "Quantos contratos e ações entram. “Sem lastro: ações livres” indica que as ações ainda não estão comprometidas."
   ],
   [
    "Entender que, no Modo Estudo, nada é executado: é a leitura de como funcionaria.",
    50,
    79.5,
    90,
    5,
    "Estudo não executa",
    "No Modo Estudo você lê como a estrutura funcionaria. Executar, ainda que simulado, é função do Modo Operador."
   ],
   [
    "Criar uma vigia para acompanhar a estrutura.",
    50,
    86.5,
    83,
    5.2,
    "Criar vigia",
    "Acompanha a estrutura sem abri-la: você volta depois e confere."
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
    33.9,
    "O termo",
    "O Modo Operador é ferramenta de decisão e disciplina. O Boris+ não envia ordens, não garante resultado e não faz recomendação personalizada."
   ],
   [
    "Saber que o texto precisa ser rolado até o fim para liberar o aceite.",
    50,
    64.2,
    60,
    2.4,
    "Leitura até o fim",
    "O aceite só é liberado depois de rolar o texto inteiro. É de propósito: a responsabilidade é sua."
   ],
   [
    "Marcar que leu e entende que pode perder dinheiro operando por conta e risco.",
    50,
    68.5,
    84,
    4.7,
    "Confirmação",
    "Você declara que leu e entende que pode perder dinheiro operando por conta e risco (aqui, dinheiro virtual)."
   ],
   [
    "Continuar no Estudo ou ativar o Modo Operador.",
    50,
    76,
    80,
    6.6,
    "Continuar ou ativar",
    "Dá para continuar no Estudo. Ativar o Operador exige o aceite e recarrega o app."
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
    4.4,
    "Estrutura aberta",
    "O card lista as pernas abertas sobre o ativo. Códigos com “MOCK” indicam o ambiente de demonstração."
   ],
   [
    "Notar que as 100 ações passam a ficar travadas como lastro (0 livres).",
    35,
    54,
    56,
    2.1,
    "Ações travadas",
    "As 100 ações passam a ser lastro: ficam comprometidas com a estrutura e deixam de estar livres para outras operações."
   ],
   [
    "Acompanhar a semana, a volatilidade, o suporte e a resistência do ativo.",
    50,
    66.4,
    77,
    12.7,
    "Contexto do ativo",
    "Semana, volatilidade, suporte e resistência continuam à vista para você acompanhar."
   ],
   [
    "Ver quantas vigias há.",
    81,
    75.2,
    14,
    2.4,
    "Vigias",
    "A contagem de vigias ativas sobre o ativo."
   ],
   [
    "Abrir o card do ativo.",
    50,
    51.3,
    84,
    4,
    "Card do ativo",
    "A entrada para rever a estrutura e as alternativas."
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
    11.8,
    "O que o Bóris não faz",
    "Não recomenda compra nem venda e não envia ordem. Nada do que ele diz é recomendação ou promessa de resultado."
   ],
   [
    "Contar com a base de estudo: indicadores, estrutura de preço, setups e vocabulário da B3.",
    50,
    60,
    80,
    9.2,
    "O que ele conhece",
    "Indicadores, estrutura de preço, modelos, setups e o vocabulário da B3: a mesma base que o app usa para explicar cada tela."
   ],
   [
    "Chamá-lo pela coruja flutuante, em qualquer tela do Estudo.",
    50,
    70,
    80,
    6.8,
    "A coruja flutuante",
    "Aparece em qualquer tela do Estudo. Ele já sabe em que tela você está e o que ela mostra."
   ],
   [
    "Conversar agora ou deixar para depois.",
    50,
    82.1,
    80,
    11.3,
    "Conversar agora ou depois",
    "Pergunte algo concreto, como “o que invalidaria esta entrada?”. Perguntas que pedem previsão não são respondidas."
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
    "Ver o estado do Operador IA e abri-lo.",
    48.7,
    40.0,
    85.5,
    20.2,
    "Operador IA",
    "Cartão no Acompanhar com o estado do Operador IA (ligado ou desligado no servidor). Toque para abrir."
   ],
   [
    "Percorrer os setups da watchlist em carrossel, cada um com anel de confiança.",
    49,
    71,
    84,
    22,
    "Setups em carrossel",
    "Os ativos da watchlist com setup para estudar, cada um com o seu anel de confiança."
   ],
   [
    "Ver o estado do mercado e do horário de pregão.",
    34,
    23,
    64,
    3.2,
    "Mercado",
    "O estado do pregão e o horário de abertura ficam sempre no topo."
   ],
   [
    "Ver o saldo virtual e o caixa no topo.",
    83,
    17,
    16,
    10,
    "Saldo e caixa",
    "O mesmo resumo do celular, no canto da tela larga."
   ]
  ],
  "guard": "Mesmo conteúdo do celular, em layout largo.",
  "grupo": "Versão web",
  "onde": "Navegador · aba Acompanhar",
  "objetivo": "Usar o app em tela larga.",
  "missao": [
   "Abra o app no navegador.",
   "Localize o cartão do Operador IA.",
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
    12.4,
    "Dois planos lado a lado",
    "Compare invalidação, gatilho e alvo de dois ativos sem trocar de tela."
   ],
   [
    "Ler regime e amostra de cada setup.",
    50,
    52,
    88,
    10.6,
    "Regime e amostra",
    "Cada card traz o regime e o aviso de amostra insuficiente, para você não comparar planos de qualidade diferente."
   ],
   [
    "Abrir a compra simulada direto do card.",
    50,
    81,
    88,
    8.6,
    "Compra direto do card",
    "“Simular compra…” abre o mesmo ticket do celular."
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
    "Ver o estado do Operador IA e abri-lo.",
    48.7,
    41.5,
    85.5,
    20.6,
    "Operador IA",
    "O cartão do Operador IA também aparece no topo do Portfólio na tela larga, com o mesmo estado (ligado ou desligado no servidor)."
   ],
   [
    "Ver o patrimônio total.",
    28,
    77.5,
    42,
    11,
    "Patrimônio total",
    "Valor total da carteira simulada: caixa mais posições. O caixa disponível fica sempre no topo da tela."
   ],
   [
    "Ver o resultado aberto.",
    71,
    77.5,
    42,
    11,
    "Resultado aberto",
    "Ganho ou perda das posições que ainda não foram vendidas. O valor em posições aparece logo abaixo, rolando a tela."
   ]
  ],
  "guard": "O aviso de carteira simulada acompanha todas as telas.",
  "grupo": "Versão web",
  "onde": "Navegador · Portfólio",
  "objetivo": "Ver a carteira simulada no navegador.",
  "missao": [
   "Confira o patrimônio total e o caixa disponível no topo.",
   "Localize o cartão do Operador IA."
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
