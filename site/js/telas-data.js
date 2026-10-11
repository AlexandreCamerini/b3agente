/* Dados das telas do Boris+ (guia de treinamento). Capturas de 09/10/2026 (02-acompanhar, 08-portfolio, web-portfolio e web-acompanhar refeitas em 10/10/2026 com o cartão do Operador IA), app local, dinheiro virtual.
   FONTE ÚNICA do guia: o site (js/guia.js) lê window.TELAS e o app (web/src/guiaTelas.js) importa este MESMO arquivo com ?raw. Contrato estrito: este comentário + `window.TELAS = <array JSON puro>;` (web/tests/test_guia_dados.mjs trava a paridade e o conteúdo).
   Tela: {id, kind (m = celular, w = web), img, nh?, alt, titulo, sub, grupo, onde, objetivo, pontos, missao (UMA string: resultado verificável), quiz {q,o,a,why}}.
   Ponto: {titulo, texto, x, y, w, h} (x/y/w/h = % da captura). Sem frase curta e sem aviso por ponto: o aviso legal vive num rodapé único. Reescrita 2026-10-11 (quick 261011-l5x): 95 -> 57 pontos. */
window.TELAS = [
 {
  "id": "boas",
  "kind": "m",
  "img": "img/01-boas-vindas.jpg",
  "alt": "Boas-vindas: orçamento simulado de R$ 10.000, perfil de risco e aviso educacional.",
  "titulo": "Boas-vindas",
  "sub": "Primeira abertura",
  "grupo": "Primeiros passos",
  "onde": "Primeira abertura, depois de criar a conta",
  "objetivo": "Definir o ponto de partida do seu treino.",
  "pontos": [
   {
    "titulo": "Orçamento simulado",
    "texto": "Saldo fictício com que você treina. Define o tamanho das posições e o risco por operação (padrão: 1% do orçamento). Nenhum valor sai de conta bancária.",
    "x": 50,
    "y": 60,
    "w": 78,
    "h": 4.8
   },
   {
    "titulo": "Perfil de risco",
    "texto": "Conservador, moderado ou agressivo. A IA leva o seu perfil em conta ao comentar o risco da sua carteira; nada muda no mercado.",
    "x": 50,
    "y": 69,
    "w": 78,
    "h": 4.6
   }
  ],
  "missao": "Entre na mesa com o orçamento e o perfil de risco escolhidos e confira o saldo no Acompanhar.",
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
  "grupo": "Primeiros passos",
  "onde": "Aba Acompanhar",
  "objetivo": "Ler o estado do seu dia de relance.",
  "pontos": [
   {
    "titulo": "Estado do mercado",
    "texto": "Aberto ou fechado, com o horário de abertura. Fora do pregão os preços são os do último fechamento; na Watchlist, a tela mostra a última barra de 15 minutos e avisa que a condição volta a ser verificada na abertura.",
    "x": 22,
    "y": 13,
    "w": 42,
    "h": 3
   },
   {
    "titulo": "Operador IA",
    "texto": "Mostra se o Operador IA está ligado ou desligado no servidor e se só avisa ou também executa. Descreve a configuração, não que ele esteja rodando agora. No Modo Estudo só sinaliza; a execução, simulada, é do Modo Operador.",
    "x": 48.7,
    "y": 25.5,
    "w": 91.3,
    "h": 18.2
   },
   {
    "titulo": "Resumo do dia",
    "texto": "Resultado da carteira no dia, acumulado e número de operações. Numa conta nova tudo começa zerado.",
    "x": 48.7,
    "y": 47.3,
    "w": 91.3,
    "h": 21.3
   },
   {
    "titulo": "Curva do patrimônio",
    "texto": "Curva, retorno acumulado e drawdown saem da mesma janela de dias. Com poucos dias a curva é curta; sem dados, a tela diz “Não há dados suficientes para concluir” em vez de desenhar uma linha estimada.",
    "x": 48.7,
    "y": 75.2,
    "w": 82.6,
    "h": 10.8
   }
  ],
  "missao": "Ache o cartão do Operador IA e diga se ele está ligado ou desligado no servidor.",
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
  "grupo": "Descobrir e planejar",
  "onde": "Aba Radar (Mesa, no Modo Operador)",
  "objetivo": "Descobrir quais ativos têm condição técnica para estudar.",
  "pontos": [
   {
    "titulo": "IA no top-N",
    "texto": "Pede à IA que explique os melhores resultados da varredura. Gasta cota de análises; a lista em si, calculada pelo motor, não gasta.",
    "x": 70.5,
    "y": 21.8,
    "w": 22.5,
    "h": 5.4
   },
   {
    "titulo": "Período em uso",
    "texto": "Janela de histórico da varredura (1 ano = 252 pregões, mostrados no selo). Todo sinal é calculado sobre ela: janela longa reage mais devagar que a curta.",
    "x": 33,
    "y": 47,
    "w": 59,
    "h": 3.3
   },
   {
    "titulo": "Cobertura da varredura",
    "texto": "O primeiro número são os ativos lidos; o segundo, o universo da varredura. Quem fica “sem dados” fica fora do ranking, sem nota estimada. Cobertura baixa é ranking incompleto, não mercado sem oportunidade.",
    "x": 45,
    "y": 55,
    "w": 84,
    "h": 2.3
   },
   {
    "titulo": "Como o Radar analisa",
    "texto": "O ranking ordena primeiro pelo regime (tendência antes de lateral e indefinido), depois pelo momentum relativo ao universo; a confluência só desempata. É ordem de estudo, não de compra.",
    "x": 50,
    "y": 60,
    "w": 91,
    "h": 5
   },
   {
    "titulo": "Card do ativo",
    "texto": "Traz o plano educacional (estudar alta ou baixa), a confiança e o padrão. O anel é a confluência: peso dos critérios do padrão atendidos hoje ÷ peso total; abaixo de 50% o setup não conta. Não mede a chance de dar certo.",
    "x": 49,
    "y": 78.5,
    "w": 83,
    "h": 11.4
   }
  ],
  "missao": "Ache o selo do período em uso e a contagem de ativos lidos e sem dados.",
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
  "grupo": "Descobrir e planejar",
  "onde": "Aba Watchlist (Monitoramento, no Modo Operador)",
  "objetivo": "Acompanhar de perto os ativos que você escolheu estudar.",
  "pontos": [
   {
    "titulo": "Modelo de análise",
    "texto": "Completo, Tendência, Price Action, Momentum, Volume… Cada modelo muda o ângulo da leitura. O backend calcula; a IA interpreta dados históricos.",
    "x": 50,
    "y": 58.2,
    "w": 90,
    "h": 7.5
   },
   {
    "titulo": "Preço e fonte",
    "texto": "Preço, variação do dia e de onde veio o dado (aqui, Yahoo). Fonte e horário ficam sempre visíveis.",
    "x": 63,
    "y": 71.5,
    "w": 22,
    "h": 5.2
   },
   {
    "titulo": "Plano educacional",
    "texto": "A leitura do motor para o ativo, em linguagem de estudo. Os níveis do plano ficam no card, na tela seguinte.",
    "x": 49,
    "y": 81,
    "w": 83,
    "h": 11.4
   }
  ],
  "missao": "Troque o modelo de análise e confira a fonte e o horário do dado de um ativo.",
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
  "grupo": "Descobrir e planejar",
  "onde": "Card de um ativo, na Watchlist",
  "objetivo": "Saber onde a ideia se invalida, se confirma e termina, antes de agir.",
  "pontos": [
   {
    "titulo": "Régua do plano",
    "texto": "Invalidação é o preço em que a ideia deixa de valer (stop didático); gatilho a confirma; alvo é a saída planejada. Em vários setups, alvo = gatilho + 2× a distância até a invalidação. Retorno abaixo de 1,5× o risco não vira plano.",
    "x": 49,
    "y": 41,
    "w": 83,
    "h": 6.3
   },
   {
    "titulo": "Regime",
    "texto": "Direção: fechamento acima ou abaixo da média de 200 pregões (com menos de 200, usa a de 50 e marca não confiável). Força: ADX14 ≥ 25 é tendência; abaixo disso, lateral.",
    "x": 36,
    "y": 47.6,
    "w": 57,
    "h": 2.8
   },
   {
    "titulo": "Amostra insuficiente",
    "texto": "Se o padrão ocorreu menos de 40 vezes, o histórico medido diz pouco. “Sinal técnico” (o padrão existe hoje) e “histórico medido” (como se saiu antes) são coisas diferentes.",
    "x": 31,
    "y": 51.4,
    "w": 48,
    "h": 2.5
   },
   {
    "titulo": "Simular compra",
    "texto": "Abre o ticket com o plano pronto. O parecer “não operar” é parecer, não veto: o app sempre deixa você definir stop e alvo.",
    "x": 49,
    "y": 66.5,
    "w": 83,
    "h": 5.2
   },
   {
    "titulo": "Estudar este ativo",
    "texto": "Pede à IA a leitura de um ativo em quatro passos: o que cada indicador marca, quais confirmam ou divergem, como se combinam e o que mudaria a leitura. Consome uma análise da cota.",
    "x": 35,
    "y": 74.3,
    "w": 56,
    "h": 2.6
   }
  ],
  "missao": "Na régua, localize invalidação, gatilho e alvo e leia o regime do ativo.",
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
  "grupo": "Operar no simulador",
  "onde": "Card do ativo → Simular compra…",
  "objetivo": "Enviar uma ordem virtual sabendo o que vai acontecer.",
  "pontos": [
   {
    "titulo": "Quantidade",
    "texto": "Lotes de 100. O plano sugere a quantidade pelo risco: capital × % de risco (padrão 1%, teto 5%) ÷ risco por ação, arredondada para baixo em lote de 100.",
    "x": 50,
    "y": 37.4,
    "w": 80,
    "h": 5.2
   },
   {
    "titulo": "Custo estimado",
    "texto": "Preço × quantidade, antes de confirmar. Se o caixa não cobre, o ticket avisa “Caixa insuficiente”.",
    "x": 50,
    "y": 44.4,
    "w": 80,
    "h": 5
   },
   {
    "titulo": "Tudo ou nada",
    "texto": "A ordem executa inteira ou é rejeitada, com o motivo. Preenchimento parcial não existe no Boris+, por desenho.",
    "x": 49,
    "y": 62,
    "w": 78,
    "h": 3.3
   }
  ],
  "missao": "Escolha uma quantidade e confira que o custo estimado é o preço vezes a quantidade.",
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
  "grupo": "Operar no simulador",
  "onde": "Logo após confirmar, com o mercado fechado",
  "objetivo": "Entender o que acontece com uma ordem fora do pregão.",
  "pontos": [
   {
    "titulo": "Ordem pendente",
    "texto": "Com o mercado fechado, a ordem fica pendente e executa ao preço de abertura do próximo pregão.",
    "x": 50,
    "y": 83.5,
    "w": 50,
    "h": 11
   },
   {
    "titulo": "Caixa reservado",
    "texto": "Na confirmação o app reserva o caixa (compra) ou a posição (venda), para não gastar duas vezes o mesmo saldo. O caixa do topo já desconta a ordem pendente.",
    "x": 66,
    "y": 12.3,
    "w": 31,
    "h": 2.6
   }
  ],
  "missao": "Confirme uma compra com o mercado fechado e confira que o caixa do topo já a desconta.",
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
  "grupo": "Operar no simulador",
  "onde": "Aba Portfólio (Posições, no Modo Operador)",
  "objetivo": "Ver resultado, caixa e o que está em posições.",
  "pontos": [
   {
    "titulo": "Patrimônio e resultado aberto",
    "texto": "Patrimônio total é caixa mais posições. Resultado aberto é o ganho ou a perda das posições ainda não vendidas, mostrado sem maquiagem. A variação do dia fica à vista no Acompanhar.",
    "x": 47.3,
    "y": 50.1,
    "w": 88.5,
    "h": 6.2
   },
   {
    "titulo": "Caixa e posições",
    "texto": "Dinheiro livre de um lado, valor em posições do outro. Se tudo está em posições, não sobra saldo para novas ordens.",
    "x": 47.3,
    "y": 56.3,
    "w": 88.5,
    "h": 4.5
   },
   {
    "titulo": "Histórico de operações",
    "texto": "Registra cada decisão, inclusive as ordens recusadas e o motivo. Rever as recusas ensina tanto quanto as aceitas.",
    "x": 47.3,
    "y": 89.4,
    "w": 88.5,
    "h": 5.2
   }
  ],
  "missao": "Compare o patrimônio total com o caixa disponível e abra o histórico de operações.",
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
  "grupo": "Opções",
  "onde": "Aba Opções",
  "objetivo": "Estudar opções sobre as ações que você já tem.",
  "pontos": [
   {
    "titulo": "Ativo em carteira",
    "texto": "Opções aqui são estudadas sobre ações que você já tem: o card mostra quantas há e quantas estão livres como lastro. Suporte e resistência dão contexto para escolher proteção ou renda.",
    "x": 50,
    "y": 60,
    "w": 83,
    "h": 6.6
   },
   {
    "titulo": "Evolução da semana",
    "texto": "Um segmento por pregão fechado, colorido pelo regime medido naquele dia. Descreve o passado; não é previsão do próximo.",
    "x": 50,
    "y": 69.5,
    "w": 83,
    "h": 4.8
   },
   {
    "titulo": "Estruturas e vigias",
    "texto": "Mostra se há estrutura aberta sobre o ativo e quantas vigias você criou. Abrir o card do ativo não gasta consultas da sua cota.",
    "x": 50,
    "y": 82.3,
    "w": 83,
    "h": 2.4
   }
  ],
  "missao": "Ache o ativo em carteira e quantas ações estão livres como lastro.",
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
  "grupo": "Opções",
  "onde": "Opções → card do ativo",
  "objetivo": "Escolher o que fazer com as ações.",
  "pontos": [
   {
    "titulo": "O que você quer fazer?",
    "texto": "Três objetivos: proteger de queda, gerar renda ou proteger com custo baixo. O app diz primeiro o que a estrutura faz por você e só depois o nome técnico (put protetora, venda coberta, collar).",
    "x": 50,
    "y": 34.7,
    "w": 84,
    "h": 4.6
   },
   {
    "titulo": "O que se perde",
    "texto": "Cada objetivo mostra aquilo de que você abre mão: o prêmio pago ou o ganho acima de um teto.",
    "x": 35,
    "y": 58.7,
    "w": 56,
    "h": 2.2
   },
   {
    "titulo": "Termos sublinhados",
    "texto": "Toque no sublinhado pontilhado para abrir o verbete. É texto escrito à mão e não gasta cota.",
    "x": 50,
    "y": 41,
    "w": 84,
    "h": 2.8
   }
  ],
  "missao": "Toque num termo sublinhado e leia o verbete.",
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
  "grupo": "Opções",
  "onde": "Opções → Proteger de queda",
  "objetivo": "Escolher o piso da proteção.",
  "pontos": [
   {
    "titulo": "Vencimento",
    "texto": "A data até a qual a proteção vale. O app mostra os dias até o vencimento; prazos maiores tendem a custar mais.",
    "x": 34,
    "y": 40.2,
    "w": 55,
    "h": 6.6
   },
   {
    "titulo": "Três níveis",
    "texto": "Mais protegido, equilibrado e mais barato: o piso (strike da put) sobe ou desce, trocando proteção por custo.",
    "x": 50,
    "y": 66.5,
    "w": 84,
    "h": 43.5
   },
   {
    "titulo": "Custo da proteção",
    "texto": "É o prêmio pago pela put. Se a ação não cair, é o que se perde por ter se protegido.",
    "x": 50,
    "y": 56,
    "w": 76,
    "h": 3
   }
  ],
  "missao": "Compare os três níveis e aponte qual tem o maior custo da proteção.",
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
  "grupo": "Opções",
  "onde": "Opções → depois de escolher um nível",
  "objetivo": "Ler o pior caso antes de decidir.",
  "pontos": [
   {
    "titulo": "Preço no vencimento",
    "texto": "Mova o controle para ver o resultado, com e sem a estrutura, em cada preço possível no vencimento.",
    "x": 49,
    "y": 20.4,
    "w": 74,
    "h": 3.5
   },
   {
    "titulo": "Só as ações × com a estrutura",
    "texto": "A comparação direta: onde a estrutura ajuda (nas quedas) e onde pesa (nas altas, por causa do prêmio).",
    "x": 50,
    "y": 27,
    "w": 76,
    "h": 4.8
   },
   {
    "titulo": "Pior, melhor e equilíbrio",
    "texto": "Pior caso é a perda máxima; equilíbrio, o preço de resultado zero. Put protetora: pior = (preço médio − piso + prêmio) × qtd; equilíbrio = preço médio + prêmio. Piso acima de preço médio + prêmio: perda máxima zero, sem equilíbrio.",
    "x": 50,
    "y": 52.8,
    "w": 88,
    "h": 14.2
   }
  ],
  "missao": "Leia o pior caso da estrutura e compare com o resultado só das ações.",
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
  "grupo": "Opções",
  "onde": "Opções → Ver os números",
  "objetivo": "Ler o gráfico de resultado no vencimento.",
  "pontos": [
   {
    "titulo": "O gráfico",
    "texto": "Eixo horizontal: preço da ação no vencimento; vertical: seu resultado. Linha cheia é com a estrutura; tracejada, só com as ações. Pontos numerados marcam piso, equilíbrio, perda máxima e preço médio.",
    "x": 50,
    "y": 25.5,
    "w": 84,
    "h": 19.7
   },
   {
    "titulo": "Teto ou não",
    "texto": "“Sem teto” quer dizer que o ganho acompanha a alta da ação, descontado o prêmio. Com venda coberta ou collar há teto: o ganho para no strike da call vendida.",
    "x": 50,
    "y": 63,
    "w": 84,
    "h": 10.4
   },
   {
    "titulo": "E se…?",
    "texto": "Um simulador de cenário: arraste o preço e veja o resultado de cada alternativa. É estudo, não previsão.",
    "x": 50,
    "y": 80,
    "w": 84,
    "h": 20
   }
  ],
  "missao": "Teste um preço no vencimento e localize o piso no gráfico.",
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
  "grupo": "Opções",
  "onde": "Opções → Escolher este (Modo Estudo)",
  "objetivo": "Rever a estrutura antes de decidir, sem executar.",
  "pontos": [
   {
    "titulo": "A estrutura",
    "texto": "Vencimento, perna comprada (a put) e prêmio por ação: o que seria negociado se você executasse. Antes, o app repete pior e melhor caso em palavras simples.",
    "x": 50,
    "y": 60,
    "w": 84,
    "h": 13.3
   },
   {
    "titulo": "Contratos e lastro",
    "texto": "Quantos contratos e ações entram. “Sem lastro: ações livres” indica que as ações ainda não estão comprometidas.",
    "x": 45,
    "y": 70.5,
    "w": 76,
    "h": 6.5
   },
   {
    "titulo": "Estudo não executa",
    "texto": "No Modo Estudo você lê como a estrutura funcionaria, sem executar. Executar, ainda que de forma simulada, é função do Modo Operador.",
    "x": 50,
    "y": 79.5,
    "w": 90,
    "h": 5
   },
   {
    "titulo": "Criar vigia",
    "texto": "Acompanha a estrutura sem abri-la: é um alerta, que não executa. Você volta depois e confere.",
    "x": 50,
    "y": 86.5,
    "w": 83,
    "h": 5.2
   }
  ],
  "missao": "Releia o pior caso e confira a estrutura e o lastro antes de decidir.",
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
  "grupo": "Modo Operador",
  "onde": "Perfil → Modo de trabalho → Operador",
  "objetivo": "Entender o compromisso antes de ativar o Operador.",
  "pontos": [
   {
    "titulo": "O termo",
    "texto": "O Modo Operador é ferramenta de decisão e disciplina. O aceite só é liberado depois de rolar o texto inteiro, de propósito: a responsabilidade é sua. O Boris+ não envia ordens.",
    "x": 50,
    "y": 45.5,
    "w": 80,
    "h": 33.9
   },
   {
    "titulo": "Confirmação",
    "texto": "Você declara que leu e entende que pode perder ao operar por conta e risco (aqui, com saldo virtual). Dá para continuar no Estudo; ativar o Operador exige o aceite e recarrega o app.",
    "x": 50,
    "y": 68.5,
    "w": 84,
    "h": 4.7
   }
  ],
  "missao": "Role o termo até o fim, marque a confirmação e decida entre continuar no Estudo ou ativar.",
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
  "grupo": "Modo Operador",
  "onde": "Modo Operador → Opções",
  "objetivo": "Acompanhar a estrutura aberta sobre o ativo.",
  "pontos": [
   {
    "titulo": "Estrutura aberta",
    "texto": "O card lista as pernas abertas sobre o ativo e a contagem de vigias ativas. Códigos com “MOCK” indicam o ambiente de demonstração.",
    "x": 50,
    "y": 75.7,
    "w": 77,
    "h": 4.4
   },
   {
    "titulo": "Ações travadas",
    "texto": "As 100 ações passam a ser lastro: ficam comprometidas com a estrutura e deixam de estar livres para outras operações.",
    "x": 35,
    "y": 54,
    "w": 56,
    "h": 2.1
   }
  ],
  "missao": "Confira no card que as ações usadas como lastro aparecem travadas.",
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
  "grupo": "Bóris",
  "onde": "Coruja flutuante, em qualquer tela do Estudo",
  "objetivo": "Tirar dúvidas com quem conhece a tela em que você está.",
  "pontos": [
   {
    "titulo": "O que o Bóris não faz",
    "texto": "O Bóris explica, não manda: não diz “compre agora”, não envia ordem e não responde a pedido de previsão.",
    "x": 50,
    "y": 47.5,
    "w": 80,
    "h": 11.8
   },
   {
    "titulo": "O que ele conhece",
    "texto": "Indicadores, estrutura de preço, modelos, setups e o vocabulário da B3: a mesma base que o app usa para explicar cada tela.",
    "x": 50,
    "y": 60,
    "w": 80,
    "h": 9.2
   },
   {
    "titulo": "A coruja flutuante",
    "texto": "Aparece em qualquer tela do Estudo e já sabe onde você está. Pergunte algo concreto, como “o que invalidaria esta entrada?”.",
    "x": 50,
    "y": 70,
    "w": 80,
    "h": 6.8
   }
  ],
  "missao": "Toque na coruja e pergunte o que invalidaria a entrada de um ativo.",
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
  "grupo": "Versão web",
  "onde": "Navegador · aba Acompanhar",
  "objetivo": "Usar o app em tela larga.",
  "pontos": [
   {
    "titulo": "Setups em carrossel",
    "texto": "Os ativos da watchlist com setup para estudar, cada um com o seu anel de confiança.",
    "x": 49,
    "y": 71,
    "w": 84,
    "h": 22
   }
  ],
  "missao": "Percorra o carrossel de setups no navegador.",
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
  "grupo": "Versão web",
  "onde": "Navegador · Watchlist",
  "objetivo": "Comparar ativos lado a lado.",
  "pontos": [
   {
    "titulo": "Dois planos lado a lado",
    "texto": "Compare invalidação, gatilho e alvo de dois ativos sem trocar de tela. Cada card traz o próprio regime.",
    "x": 50,
    "y": 36,
    "w": 88,
    "h": 12.4
   },
   {
    "titulo": "Compra direto do card",
    "texto": "“Simular compra…” abre o mesmo ticket do celular.",
    "x": 50,
    "y": 81,
    "w": 88,
    "h": 8.6
   }
  ],
  "missao": "Compare o plano de dois ativos e abra a compra simulada a partir do card.",
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
  "grupo": "Versão web",
  "onde": "Navegador · Portfólio",
  "objetivo": "Ver a carteira simulada no navegador.",
  "pontos": [
   {
    "titulo": "Patrimônio total",
    "texto": "Na tela larga, patrimônio total e resultado aberto aparecem lado a lado, em cartões. O caixa disponível fica no topo; o valor em posições, logo abaixo, rolando a tela.",
    "x": 28,
    "y": 77.5,
    "w": 42,
    "h": 11
   }
  ],
  "missao": "Confira o patrimônio total e o caixa disponível no topo.",
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
