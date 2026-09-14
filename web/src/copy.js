// FASE 8 (B1 — AMOSTRA PARA APROVAÇÃO, ainda não importada pelas telas).
//
// "Dois apps em um": TODA a fraseologia que muda entre os modos vive NESTE
// dicionário — as telas leem COPY[modo].chave e nunca hardcodam texto sensível.
// O modo Estudo é um PROFESSOR (ensina o porquê, convida a estudar); o modo
// Operador é uma MESA DE OPERAÇÕES que orienta o cliente (o quê, quando,
// quanto — plano, risco em R, disciplina). Limite regulatório inalterado:
// nenhuma ordem à corretora, nenhuma recomendação personalizada; disclaimers
// por modo vêm do disclaimers.js (fonte única).
//
// Convenções:
//  • chaves idênticas nos dois modos (guardião compara os conjuntos);
//  • funções para textos com variáveis: saudacao(nome), resumoDia(n, g);
//  • vocabulário de ordem (comprar/vender) PROIBIDO no ramo estudo (guardião).
import { DISCLAIMERS } from "./disclaimers.js";
import { RR_MIN_TXT } from "./finance.js"; // ADR-015 (06-05): fonte única do R:R mínimo

export const COPY = {
  estudo: {
    // identidade
    // (qa/34: `marcaSufixo` removida — era chave órfã; a identidade do modo no
    //  topo vem da LINHA DE MODO (chipModo + dot), não de sufixo no wordmark.)
    chipModo: "MODO ESTUDO", // qa/mock v2: badge simétrico — os DOIS modos têm chip (antes só Operador)

    // saudação/tratamento (Acompanhar)
    saudacao: (nome) => (nome ? `Vamos estudar o mercado hoje, ${nome}?` : "Vamos estudar o mercado hoje?"),
    resumoDia: (nSetups, nGatilhos) =>
      nSetups > 0
        ? `Há ${nSetups} setup(s) para estudar na sua watchlist — bora entender o porquê de cada um?`
        : "Mercado sem setups claros na sua watchlist — bom dia para revisar os conceitos.",

    // Fase 21 (FIX-03): placeholder de CapitalCurve com 1-2 dias de patrimônio
    // registrados — mesmo texto nos dois modos (afirmação factual sobre
    // disponibilidade de dado, não enquadramento de decisão).
    curvaPoucosDias: (dias) =>
      dias === 1
        ? "Só 1 dia registrado ainda — a curva aparece a partir do 3º dia."
        : "Só 2 dias registrados ainda — a curva aparece a partir do 3º dia.",

    // 25-06 (Fase 5 do 25-CONTEXT) — PLANO DA CONTA. Texto IDÊNTICO nos dois
    // modos, mesmo precedente de `curvaPoucosDias` logo acima: é estado de
    // CONTA, não voz de professor vs mesa. O plano não muda como se decide
    // uma operação; ele diz quanto cabe no mês.
    //
    // Nenhuma chave de CTA de upgrade — de propósito, não esquecimento. Não
    // existe loja/IAP no produto (ADR-010, decisão 4) e um botão "assine"
    // prometeria o que não se cumpre. `test_plano_ui.mjs` trava a ausência.
    planoRotulo: "Plano",
    // Sem mapa id -> nome de exibição: o app JÁ mostra o id cru ao usuário no
    // modal de watchlist ("do plano free") e duas vozes para a mesma coisa
    // divergiriam. Um mapa no front também seria uma segunda lista de planos,
    // que fica velha no dia em que existir um terceiro (mesmo raciocínio do
    // guardião do portal, 25-05).
    planoNome: (planId) => (planId ? String(planId) : "—"),
    planoResumoTile: (planId) =>
      (planId ? String(planId) + " — análises" : "Análises") +
      " de IA por mês e ativos na watchlist",
    planoTituloTela: "Plano",
    planoDescricao:
      "O plano da sua conta define quantas análises de IA cabem no mês e quantos ativos cabem na watchlist. Os números abaixo vêm do servidor, no momento em que esta tela abriu. Hoje o plano é definido pela administração do Boris+.",
    // `null` quando o limite não existe: o app NUNCA escreve a palavra que
    // significa "sem teto" nem "X/∞" (D-03 da Fase 13) — a linha some.
    planoEntitlementAnalises: (limite) =>
      (limite == null ? null : "Análises da IA — " + limite + " por mês. Usadas até agora:"),
    planoEntitlementWatchlist: (limite) =>
      (limite == null ? null : "Ativos na watchlist — até " + limite + ". Em uso agora:"),
    // Princípio 4 do CLAUDE.md: limite que não pôde ser confirmado vira
    // travessão + motivo, nunca número estimado.
    planoLimiteIndisponivel:
      "Não foi possível confirmar este limite agora. Ele continua valendo no servidor — só não deu para exibir o número.",
    // Substitui a exibição da frase CRUA do backend no banner de recusa: a
    // `reason` de plan.py é ASCII sem acento (convenção de log Python), não
    // copy de produto. Sem contagem regressiva, sem "só resta 1", sem CTA.
    planoAvisoLimiteWatchlist: (limite, usado) =>
      (limite == null
        ? "Sua watchlist chegou ao limite do seu plano."
        : "Seu plano acompanha até " + limite + " ativos na watchlist.") +
      (usado == null ? "" : " Você tem " + usado + " agora.") +
      " Para acompanhar outro, tire um da lista.",

    // abas
    tabRadar: "Radar", // qa/34: rótulo CURTO da aba inferior (a tela usa tituloRadar)
    tituloRadar: "Radar de mercado",
    subtituloRadar: "Varredura do universo com o motor de sinais: quais condições técnicas estão ativas em cada papel, para você estudar — sem qualquer recomendação.",
    tituloWatchlist: "Watchlist",
    subtituloWatchlist: "Seus ativos em estudo, ordenados por oportunidade (confluência do snapshot). A análise completa abre no card.",
    tituloPortfolio: "Portfólio",
    subtituloPortfolio: "Sua carteira SIMULADA — dinheiro de estudo, decisões de verdade.",

    // aba Opções (aba-opcoes F2, 2026-09-10) — voz de professor: explica o
    // que o número é antes de dizer o que ele mostra. O Operador IA saiu da
    // barra e virou sub-tela do Portfólio (D-0.1 do PLANO-aba-opcoes).
    // 2026-09-12 (Fase 26, achado A3): o par estudo×operador destas chaves
    // agora tem guardião — `web/tests/test_vocabulario_opcoes.mjs` trava que o
    // SUBTÍTULO difere entre os modos, que o TÍTULO é igual por decisão, que
    // `tabOpcoes` não muda, e que os dois subtítulos dizem que nenhuma ordem
    // sai da aba. Voltar a escrever qualquer um deles direto no JSX falha.
    tabOpcoes: "Opções",
    tituloOpcoes: "Opções",
    subtituloOpcoes: "Como o ativo vem se comportando e quais estruturas de opções fazem sentido estudar — leitura de fim de pregão, sem ordem nenhuma.",
    tituloOperadorIA: "Operador IA",
    linkOperadorIA: "Abrir o Operador IA →",
    opcoesLeituraTitulo: "LEITURA DO ATIVO",
    // Fase 27 (27-05) — a leitura do SERVIÇO virou clique. As duas chaves
    // abaixo são o convite: o botão e o que ele traz de diferente do bloco
    // técnico interno (grátis, 27-04) que já está na tela logo acima. Sem
    // dizer a diferença, pagar 3 consultas por "mais uma leitura" pareceria
    // pagar duas vezes pela mesma coisa.
    opcoesLerNoServico: "Ler no serviço de opções",
    opcoesLeituraConvite: "A leitura acima é do motor do próprio Boris+ e não custa nada. O serviço de opções acrescenta o que só ele tem: o catálogo de estruturas montáveis, os vencimentos abertos e a avaliação de hoje dos vigias deste ativo.",
    opcoesSetupsTitulo: "SETUPS GRAVADOS",
    opcoesPregaoRotulo: "Pregão",
    opcoesFonteRotulo: "Fonte",
    opcoesFrescorEmDia: "dado em dia",
    opcoesFrescorAtrasado: "dado atrasado",
    opcoesFrescorNaoMedido: "frescor não medido",
    // Fase 27 (27-05) — a ÚNICA chamada da aba que ainda sai sem clique, dita
    // na tela. O frescor (`/status`) reserva 1 chamada e só a consome quando
    // precisa mesmo ir ao serviço; com o frescor em cache, o custo é zero. Ele
    // não vira botão porque um gate de frescor que só aparece depois de um
    // clique não protege ninguém (ADR-027, Decisão 8): o cabeçalho tem de
    // poder dizer a idade do dado desde o primeiro frame. Declarar é a
    // correção honesta; esconder seria a outra.
    opcoesCustoFrescor: "Abrir esta aba consulta o frescor do dado no serviço: consome até 1 chamada da sua cota do dia, e nenhuma quando o frescor já está em cache. É a única consulta desta tela que sai sem você pedir — todas as outras saem de um botão que diz o preço.",
    // 24-12 (achado ao vivo 2026-09-11): o serviço dizia "em dia" — e pelo
    // SLA dele, com razão — sobre uma cotação de dois pregões atrás. A
    // distância é MEDIDA aqui, pelo calendário da B3, e vence o veredito
    // herdado. Não é acusação à fonte: é a resposta à pergunta que quem olha
    // a tela está fazendo, que é "de quando é este número?".
    opcoesAtrasoPregoes: (n) => (n === 1 ? "1 pregão atrás" : n + " pregões atrás"),
    opcoesAtrasoAjuda: "A conta é de pregões FECHADOS, pelo calendário da B3: fim de semana e feriado não entram. O pregão de hoje também não — o fechamento dele só sai à noite, então ele só passa a contar amanhã.",
    opcoesSemSetups: "Nenhum setup gravado para este ativo ainda. Setup é uma condição objetiva escrita antes do pregão — enquanto não houver uma, não há o que avaliar.",
    opcoesNaoAvaliado: (motivo) =>
      motivo
        ? "O serviço não avaliou os setups hoje. Motivo, na palavra dele: " + motivo
        : "O serviço não avaliou os setups hoje e não informou o motivo. Sem avaliação, nenhum setup pode ser dado como armado — ausência de leitura não é leitura negativa.",
    // 24-11 (achado ao vivo 2026-09-11): campo vazio da leitura passou a dizer
    // POR QUE está vazio. O MOTIVO vem pronto do backend e é exibido verbatim —
    // aqui só se junta a lista de rótulos e a gramática que a une. Voz de
    // professor: nomeia a ausência e fecha lembrando que ninguém estimou nada
    // no lugar, que é a metade da informação que o travessão mudo escondia.
    opcoesLacuna: (campos, motivo) => {
      const lista = (Array.isArray(campos) ? campos : []).filter(Boolean);
      const nomes = lista.length > 1
        ? lista.slice(0, -1).join(", ") + " e " + lista[lista.length - 1]
        : (lista[0] || "Este campo");
      return nomes + (lista.length > 1 ? " não vieram: " : " não veio: ") +
        (motivo || "o serviço não informou o motivo") +
        ". Nada foi estimado no lugar.";
    },
    opcoesNaoConfigurado: "O serviço de opções não está configurado neste servidor. Nada foi consultado — a tela não inventa leitura quando a fonte não responde.",
    opcoesCota: (reinicia) =>
      "Sua cota de consultas da aba Opções acabou por hoje." +
      (reinicia ? " Ela reinicia às " + reinicia + "." : " Ela reinicia na virada do dia."),
    opcoesIndisponivel: "O serviço de opções não respondeu agora. Tente de novo em alguns minutos — nenhum número foi estimado no lugar.",
    // 24-07 (achado F-04). A recusa da tool passou a debitar uma chamada da
    // cota do dia, porque a viagem até o serviço aconteceu. A frase é do
    // front, e não do backend, porque o que ela conta é sobre a COTA DA
    // PESSOA — o que aconteceu com o pedido dela já vem na mensagem do
    // serviço, logo acima.
    opcoesRecusaCobrada: "O serviço recusou esta consulta e ainda assim ela consumiu uma chamada da sua cota do dia: ele conta a chamada quando a recebe, antes de decidir se consegue respondê-la.",
    opcoesCarregando: "Consultando o serviço de opções…",
    // Fase 27 (D3, 2026-09-13): o universo da aba virou a CARTEIRA. A frase
    // dizia "da sua watchlist" e passou a dizer da carteira — a chave NÃO foi
    // renomeada de propósito: `test_opcoes_mcp_aba_ui.mjs` usa o nome dela
    // como marcador da ordem dos estados no fonte da tela.
    opcoesEscolherAtivo: "Escolha um ativo da sua carteira para ver a leitura dele.",
    // Fase 27 (D2): carteira vazia tem motivo E caminho. Dizer só "não há nada
    // aqui" transferiria para a pessoa a tarefa de descobrir por quê — e o
    // porquê é de produto, não de bug.
    opcoesCarteiraVazia: "Esta aba trabalha sobre o que você já tem: toda estrutura de opção montada aqui é lastreada em ações da sua carteira. Como a carteira está vazia, não há ativo sobre o qual montar nem o que vigiar. A watchlist não entra no lugar: lista de interesse é intenção, e o que falta aqui é lastro. Comece escolhendo um ativo na Carteira.",
    opcoesIrParaCarteira: "Ir para a Carteira",
    // Fase 27 (27-02) — bloco "Seus vigias", no topo da aba e FORA de qualquer
    // ticker. É ele que corrige o defeito da fase: antes, um vigia gravado só
    // aparecia com o ativo dele selecionado, e sair da aba e voltar dava a
    // impressão de que nada tinha sido gravado.
    //
    // O título é o mesmo nos dois modos de propósito, como `tituloOpcoes`:
    // "vigia" é o nome da coisa nos dois registros, e não há sinônimo de mesa
    // para ele. A voz mora nos textos longos abaixo.
    opcoesVigiasTitulo: "SEUS VIGIAS",
    opcoesVigiasVazio: "Você ainda não gravou nenhum vigia. Vigia é uma condição objetiva que você escreve antes do pregão — por exemplo, \"o IFR de 2 períodos abaixo de 25\" — e que o serviço confere uma vez por dia, sobre o fechamento. Enquanto não houver uma condição escrita, não há o que conferir.",
    // Travessão COM motivo, nunca leitura negativa: enquanto o estado do dia
    // não foi pedido, ninguém mediu nada — e dizer que o vigia não disparou
    // seria afirmar uma medição que não existe (princípio 4 do CLAUDE.md).
    opcoesVigiasSemEstado: "— estado do dia ainda não pedido. O que está acima é o cadastro do vigia: ele vem do próprio Boris+, é de graça e não diz nada sobre hoje. Saber se a condição foi atendida é medição do serviço de dados, e ela só sai quando você pede.",
    opcoesVigiasAtualizar: "Pedir o estado do dia",
    // Vigia de ativo fora da carteira NÃO some da lista: ele existe e continua
    // sendo conferido. Escondê-lo repetiria o defeito que a fase fecha.
    opcoesVigiaForaDaCarteira: "Este vigia é de um ativo que não está na sua carteira agora. Ele continua existindo e continua sendo conferido pelo serviço — o que muda é que você não tem o papel para lastrear uma estrutura sobre ele.",
    // Fase 27 (27-02, D4) — o lastro livre no cartão, ANTES da tentativa. Este
    // número só existia na mensagem de recusa do backend ("Lastro
    // insuficiente: N ação(ões) livres…"), depois de a pessoa tentar. Mesmo
    // vocabulário de `badgeTravada`/`avisoTravaNaVenda`, que é como o resto do
    // app já fala de lastro — um segundo vocabulário faria a Carteira e esta
    // aba parecerem falar de coisas diferentes.
    opcoesLastroLivre: (livres, contratos) =>
      "Lastro livre: " + (typeof livres === "number" ? livres : "—") +
      " ação(ões), o que dá para " + (typeof contratos === "number" ? contratos : "—") +
      " contrato(s).",
    opcoesLastroTravado: (travadas) =>
      (typeof travadas === "number" ? travadas : "—") +
      " ação(ões) já está(ão) travada(s) como lastro de uma call coberta aberta — volta(m) a ficar livre(s) quando a call for recomprada ou vencer.",
    opcoesLastroAjuda: "1 contrato = 100 ações. É o mesmo número que a Carteira mostra, saído da mesma conta — e nenhuma ordem sai desta tela.",
    // Travessão COM motivo: zero seria lido como "você não tem lastro", que é
    // afirmação diferente de "não sei quanto você tem" (princípio 4).
    opcoesLastroSemDado: "não deu para ler a quantidade desta posição, então o lastro não é afirmado aqui. Zero seria outra coisa: \"você não tem lastro\" é diferente de \"não sei quanto você tem\".",
    // Fase 27 (27-04, D1/D4) — A LEITURA TÉCNICA INTERNA.
    //
    // Bloco que nasce do lado do app, não do serviço de opções: tendência,
    // volatilidade, suporte/resistência e a régua de sete pregões saem do
    // motor determinístico que já alimenta Radar e Watchlist (27-03). Custo
    // ZERO de cota — é isso que permite escolher um ativo e ter resposta na
    // hora, em vez de só ter resposta paga.
    opcoesInternaTitulo: "LEITURA TÉCNICA DO ATIVO",
    // O carimbo é o princípio 3 do CLAUDE.md: de QUANDO é a leitura e DE ONDE
    // ela veio. Sem fonte declarada, travessão — nunca um nome de fonte por
    // default, que é o mesmo defeito que o cabeçalho da aba já corrigiu.
    opcoesInternaCarimbo: (asOf, fonte) =>
      "Leitura do pregão de " + (asOf || "—") + ", calculada pelo próprio Boris+ a partir de " +
      (fonte || "—") + ". É o mesmo motor que o Radar e a Watchlist usam, então o número aqui é o mesmo de lá.",
    // Selo DERIVADO de `custoMcp === 0` na resposta, nunca escrito à mão: se a
    // rota um dia passar a custar, o selo some sozinho.
    opcoesSemCusto: "grátis — motor do próprio app, sem consultar o serviço de opções",
    opcoesInternaCarregando: "Calculando a leitura técnica no próprio app…",
    opcoesInternaErro: "A leitura técnica interna deste ativo não saiu agora. Nada foi estimado no lugar — e o resto da tela não depende dela: os vigias e a leitura do serviço continuam valendo.",
    // Os quatro regimes de `server/app/regime.py::REGIMES`. Uma tabela só,
    // aqui, para que a linha de tendência e a régua digam a MESMA palavra
    // sobre o mesmo estado — dois vocabulários divergiriam na primeira
    // renomeação e a régua passaria a contradizer a linha logo acima dela.
    opcoesRegimeRotulo: {
      tendencia_alta: "tendência de alta",
      tendencia_baixa: "tendência de baixa",
      lateral: "sem tendência definida (lateral)",
      indefinido: "indefinido — faltou dado para classificar",
    },
    opcoesForcaRotulo: { forte: "forte", transicao: "em transição", fraca: "fraca" },
    // Ressalva, não erro: o valor continua na tela. O que muda é que a janela
    // de 200 pregões não fechou e o filtro de direção se apoiou na média de
    // 50 — dizer isso é diferente de esconder o número.
    opcoesRegimeNaoConfiavel: "Esta classificação se apoiou na média de 50 pregões, não na de 200: o histórico disponível ainda não fecha a janela longa. O número continua valendo para o que ele mede — o que não dá para afirmar é tendência de longo prazo.",
    // A régua de sete pregões (D4 do 27-CONTEXT). Cada segmento é um pregão
    // FECHADO e a cor é o estado MEDIDO naquele dia. Nada ali é previsão — a
    // frase diz isso com todas as letras porque uma faixa horizontal com
    // cores é lida como projeção se ninguém disser o contrário.
    opcoesReguaTitulo: "Como a semana evoluiu",
    opcoesReguaAjuda: "Cada segmento é um pregão fechado, do mais antigo à esquerda até o mais recente à direita, e a cor é o regime que foi MEDIDO naquele dia — não uma previsão do próximo. Segmento mais apagado é dia em que a janela longa não estava disponível e a classificação se apoiou na média curta.",
    opcoesReguaSemDados: "Não há pregões suficientes para montar a evolução da semana deste ativo. A faixa fica de fora em vez de aparecer vazia: sete segmentos \"indefinido\" seriam lidos como \"a semana inteira sem direção\", que é afirmação diferente de \"não há dado\".",
    opcoesDisclaimer: "Conteúdo educacional. Os dados são de fim de pregão e podem estar atrasados; nada aqui é ordem, recomendação ou promessa de resultado.",
    opcoesGraficoTitulo: "Disparos do setup",
    opcoesDisparosRotulo: "Disparos",

    // aba Opções F3 (plano 24-02, 2026-09-11) — analisar e comparar
    // vencimentos. Voz de professor: cada número vem com o que ele é e o que
    // ele NÃO é. Quatro textos aqui são afirmação regulatória e valem com a
    // mesma substância nos dois modos (delta, ±1σ, breakeven e os dois
    // "ilimitado"): mudar a substância deles muda o que o app afirma, não o
    // tom com que afirma.
    opcoesAnalisarTitulo: "O QUE DÁ PARA MONTAR",
    opcoesPossibilidadesTitulo: "COMPARAR OS VENCIMENTOS",
    opcoesTeseRotulo: "Qual é a sua tese para este ativo? Nem o serviço nem o app escolhem direção — essa parte é sua.",
    opcoesTeseAlta: "Alta",
    opcoesTeseBaixa: "Baixa",
    opcoesTeseNeutra: "Neutra",
    opcoesLoteRotulo: "Lote (número de ações)",
    opcoesLoteAjuda: "1 contrato = 100 ações. O lote só serve para converter em reais os números que vêm por ação; a conta é feita no servidor.",
    opcoesMontarEstrutura: "Montar a estrutura",
    opcoesVerPossibilidades: "Comparar os vencimentos",
    // Fase 27 (27-02): a frase do CUSTO ficou genérica e a COMPOSIÇÃO saiu
    // para uma chave própria. Ela é a forma única de declarar custo na aba, e
    // agora também o botão do bloco de vigias a usa — cuja conta é outra
    // (`list_setups` + `evaluate_setups`). Mantida como estava, ela afirmaria
    // "uma para listar os vencimentos e duas para cada vencimento" sobre uma
    // chamada que não consulta vencimento nenhum: número certo, explicação
    // falsa.
    opcoesCustoChamadas: (n) =>
      "Esta consulta gasta " + (typeof n === "number" ? n : "—") +
      " chamada(s) da sua cota do dia.",
    opcoesCustoVencimentos: "A conta: uma chamada para listar os vencimentos e duas para cada vencimento consultado.",
    // Fase 27 (27-05) — o SEGUNDO eixo de custo, e ele só existe num controle:
    // compilar um setup usa o modelo de linguagem, que tem cota própria, teto
    // próprio e tela própria. Sem número aqui de propósito — o teto vive no
    // gate do `metering`, e um número redigitado nesta frase envelheceria em
    // silêncio no dia em que o plano mudasse.
    opcoesCustoAnaliseIA: "E consome uma análise de IA da sua cota do dia, que é uma cota separada desta.",
    opcoesVerCadeia: "Ver a cadeia de opções",
    opcoesVerOperaveis: "Ver só as opções com liquidez",
    opcoesCriterioOperaveis: (c) => {
      const k = c || {};
      const n = (v) => (typeof v === "number" ? String(v).replace(".", ",") : "—");
      return "Peneira aplicada: pelo menos " + n(k.minNegocios) +
        " negócios no pregão e delta entre " + n(k.deltaMin) + " e " + n(k.deltaMax) +
        ". O critério é do Boris, não do serviço — um strike fora dessa faixa não sumiu por falta de dado, sumiu por escolha nossa.";
    },
    opcoesSemEstrutura: "O serviço não mandou os pontos da curva desta estrutura. Os números acima continuam valendo — o que falta é o desenho, e um gráfico vazio seria lido como resultado zero.",
    opcoesSemVencimento: "A leitura deste ativo não trouxe nenhum vencimento aberto, então não há o que comparar. Nada foi consultado.",
    opcoesBreakevenRotulo: "Preço de empate (breakeven)",
    opcoesBreakevenAjuda: "preço do ativo no vencimento em que a estrutura empata. É preço, não dinheiro: não se multiplica pelo lote.",
    // 24-06 (achado F-01). A ajuda nega a leitura errada mais provável —
    // razão não é chance de acerto — e ensina a ler o "1 : x", que sem isso
    // é ambíguo (qual dos dois lados é o 1?).
    opcoesRazaoRotulo: "Razão ganho/perda",
    opcoesRazaoAjuda: "quantas vezes o ganho máximo cabe na perda máxima; não é probabilidade de nada. Leia \"1 : 0,67\" como: para cada 1 de risco, 0,67 de ganho máximo.",
    opcoesCenariosTitulo: "Cenários no vencimento",
    opcoesSigmaAjuda: "cenários ±1σ a partir da volatilidade realizada de 21 pregões — é conta de dispersão, não previsão de preço.",
    opcoesDeltaAjuda: "delta ≈ chance de terminar dentro do dinheiro (aproximação)",
    opcoesPorAcaoRotulo: "por ação",
    opcoesEmReaisRotulo: "em reais, para o seu lote",
    opcoesGanhoIlimitado: "sem teto",
    opcoesPerdaIlimitada: "sem piso declarado pelo serviço",
    opcoesCadeiaTruncada: (t) =>
      "A lista veio cortada pelo serviço. Na palavra dele: " + (t || "sem detalhe informado."),
    opcoesAlvoRotulo: "Preço-alvo (opcional)",
    opcoesStopRotulo: "Preço de stop (opcional)",

    // aba Opções F5 (plano 24-04, 2026-09-11) — criar setup por descrição em
    // português. O texto de MAIOR risco regulatório da aba é o do backtest:
    // números de histórico lidos como promessa. Por isso a ressalva é a
    // MESMA frase nos dois modos, fica FIXA junto dos números (não é
    // tooltip) e nega as duas leituras erradas de uma vez — expectativa de
    // retorno e taxa de acerto.
    opcoesCriarTitulo: "CRIAR UM SETUP",
    opcoesCriarAjuda: "Escreva a condição com as suas palavras, e escreva algo objetivo: um indicador, uma comparação e um número. A condição é avaliada UMA vez por pregão, sobre o fechamento — não durante o dia. Quem diz se o vocabulário é válido é o serviço de dados, não o app: se ele recusar, você vê o motivo dele, palavra por palavra. Mínimo de 15 caracteres.",
    opcoesCriarPlaceholder: "Ex.: quando o IFR de 2 períodos ficar abaixo de 25 e o preço estiver acima da média de 200 pregões",
    opcoesCriarBotao: "Ver a interpretação e o ensaio",
    opcoesCriarConfirmar: "Gravar este setup",
    opcoesCriarDesativar: "Desativar este setup",
    opcoesCriarConfirmarDesativacao: "Confirmar a desativação",
    opcoesCriarProblemas: "O serviço não aceitou este setup. O que ele apontou, item por item:",
    opcoesCriarCru: "A IA não devolveu um setup que dê para ler, então nada foi gravado. O texto que ela respondeu, sem edição nenhuma:",
    opcoesCriarFaltando: (campos) =>
      "A resposta veio sem campo que o serviço exige: " +
      (Array.isArray(campos) && campos.length ? campos.join(", ") : "—") +
      ". Nada foi gravado — completar isso por conta seria inventar o que ninguém escreveu.",
    opcoesCriarGravado: (nome) =>
      "Setup " + (nome || "—") + " gravado e ativo. A partir de agora ele é avaliado uma vez por pregão, e aparece na lista acima.",
    opcoesCriarDesativado: (nome) =>
      "Setup " + (nome || "—") + " desativado. Ele deixa de ser avaliado; o histórico dele não é apagado.",
    opcoesCriarSemPermissao: "Criar setup depende de uma permissão que esta conta não tem. Esconder o botão é só conveniência: o servidor recusa a gravação de qualquer forma.",
    opcoesBacktestTitulo: "ENSAIO NO HISTÓRICO",
    opcoesBacktestDisparos: (n, por100) =>
      "No período coberto, esta condição ocorreu " + (n === null || n === undefined ? "—" : n) +
      " vez(es) — " + (por100 === null || por100 === undefined ? "—" : por100) +
      " a cada 100 pregões avaliáveis.",
    opcoesBacktestRetorno: (passo, medio, mediano, comDado) =>
      "Variação do ativo em " + (passo || "—") + " depois do disparo: média " +
      (medio === null || medio === undefined ? "—" : medio) + ", mediana " +
      (mediano === null || mediano === undefined ? "—" : mediano) + " (" +
      (comDado === null || comDado === undefined ? "—" : comDado) + " disparo(s) com dado suficiente).",
    opcoesBacktestRessalva: "Contagem do que já aconteceu no histórico. Não é expectativa de retorno, e taxa de disparo não é taxa de acerto.",
    // 24-14 (achado ao vivo 2026-09-11): o ensaio que devolve "0 disparos"
    // sem ter testado nada. É o texto mais delicado desta fase — ele diz à
    // pessoa que o número que ela está vendo não significa o que parece.
    // Vem ANTES dos números de propósito: quem lê o número primeiro já
    // formou a conclusão. O MOTIVO de cada condição vem pronto do backend e
    // é exibido verbatim; aqui só mora a moldura, e ela tem voz por modo.
    opcoesEnsaioIndisparavel: "Este ensaio não testou o setup. Uma das condições exige mais pregões do que o histórico usado aqui tem, então ela não teve valor em nenhum dia — e o setup só dispara quando todas as condições valem no mesmo pregão. Por isso o número de disparos abaixo é consequência da conta, não sinal de que a condição é rara. Nada foi estimado no lugar.",
    opcoesEnsaioRessalva: "Antes dos números, uma ressalva: nem toda condição deste setup teve valor em todo o período do ensaio. O que ficou sem verificação está listado aqui; os números abaixo valem para os pregões em que deu para verificar.",
    opcoesEnsaioCondicao: (indicador, janela, motivo) => {
      const nome = (typeof indicador === "string" && indicador)
        ? indicador : "condição sem indicador nomeado";
      const j = Number.isFinite(janela) ? " (janela de " + janela + " pregões)" : "";
      return nome + j + ": " + (motivo || "o serviço não informou o motivo") + ".";
    },
    opcoesDadoAtrasado: (idade, motivo) =>
      motivo === "nao_medido"
        ? "Não foi possível medir a idade do dado de negociação nesta consulta, e sem essa medição o setup não é gravado — ele vigiaria um pregão que ninguém conferiu."
        : "O dado de negociação da B3 está atrasado" +
          (idade === null || idade === undefined || idade === "" ? "" : " (" + idade + ")") +
          ": um setup criado agora vigiaria um pregão que já passou. Nada foi gravado.",

    // Fase 28-02 — sub-aba "Operar" dentro da aba Opções. "Setups" é IGUAL
    // nos dois modos de propósito (mesma razão de tituloOpcoes: é o nome do
    // artefato, não uma ação). "Operar"/"Operação" DIFERE de propósito
    // (vocabulário por modo do repositório: Estudo descreve com substantivo,
    // Operador manda com imperativo — skill_ref.py/copy.js).
    opcoesSubabaSetups: "Setups",
    opcoesSubabaOperar: "Operação",
    opcoesOperarIntro: "Aqui você vê a estrutura lastreada que o motor propõe para cada posição da sua carteira, com ganho máximo, perda máxima e pontos de empate em número. Nada é enviado a nenhuma corretora.",
    opcoesOperarEscolherPosicao: "Escolha uma posição da carteira para ver a estrutura lastreada que o motor propõe para ela.",
    opcoesOperarSemLiquidez: (t) =>
      "Não há contrato com liquidez confirmada para " + (t || "este ativo") + " agora. Sem cadeia líquida o motor não monta estrutura, e nada foi estimado no lugar.",

    // onboarding (home vazia) — qa/34: antes hardcodado na voz de Estudo
    welcomeTitulo: "Bem-vindo ao seu simulador",
    welcomeCorpo: "A jornada tem 3 passos: descubra oportunidades no Radar, acompanhe os melhores na Watchlist e simule operações no Portfólio — tudo com dinheiro simulado e leitura educacional.",
    welcomeCta: "Começar pelo Radar →",

    // Radar — bloco "como funciona" + CTAs de monitoramento (qa/34)
    comoAnalisaTitulo: "COMO O RADAR ANALISA",
    comoAnalisaCorpo: "Cada ativo é comparado a setups didáticos clássicos, descritos como um checklist de critérios objetivos. A confluência é o percentual ponderado de critérios atendidos — mede aderência ao padrão em dados passados, não probabilidade de resultado. O veredito é sempre de estudo, nunca uma ordem.",
    btnAddMonitor: "+ Watchlist",
    jaMonitorado: "✓ Na watchlist",

    // ações
    btnComprar: "Simular compra",
    btnVender: "Simular venda",
    btnAnalise: "Estudar este ativo",
    btnAprofundar: "Aprofundar com IA",

    // estados vazios
    vazioWatchlist: "Sua watchlist está vazia — descubra oportunidades no Radar e traga os melhores para cá.",
    vazioPortfolio: "Você ainda não tem posições. Vá à Watchlist e simule sua primeira compra — é dinheiro simulado, sem risco.",

    // superfícies secundárias (home, modais)
    kickerSetups: "SETUPS NA SUA WATCHLIST",
    btnLevarWatchlist: "Levar para a watchlist →",
    btnVerWatchlist: "Ver Watchlist",
    tituloLeituraIA: (t) => `${t} · leitura da IA`,
    confirmarCompra: "Confirmar compra",
    confirmarVenda: "Confirmar venda",
    filtroAlta: "Estudar alta",
    filtroBaixa: "Estudar baixa",
    notaStopAlvo: "Sugestão por perfil — conteúdo educacional, dinheiro simulado. Não é recomendação de compra ou venda.",
    vazioHistorico: "Suas compras e vendas simuladas aparecerão aqui.",

    // toasts/notificações
    toastCompra: (qty, t) => `Compra simulada: ${qty} ${t}. Sugerindo alvo e stop…`,
    toastVenda: (desc, t) => `Venda simulada: ${desc} de ${t}.`,
    notifStopTitulo: (t) => `Stop acionado · ${t}`,
    notifStopCorpo: (t, preco, stop) => `${t} a R$ ${preco} atingiu o stop de R$ ${stop} — bom momento para estudar o que mudou.`,
    notifAlvoTitulo: (t) => `Alvo atingido · ${t}`,
    notifAlvoCorpo: (t, preco, alvo) => `${t} a R$ ${preco} alcançou o alvo de R$ ${alvo}. Que tal revisar a tese?`,
    notifVarTitulo: (t) => `Movimento forte · ${t}`,
    notifVarCorpo: (t, ch, preco) => `${t} ${ch} no dia (R$ ${preco}) — vale estudar o que está acontecendo.`,

    // rodapé/disclaimer
    disclaimer: DISCLAIMERS.radar,
    rodape: "Ferramenta educacional — nada aqui é recomendação de investimento.",

    // Fase 2 (MERC-01, D-08): status real do pregão — badge pré-login (Welcome)
    // e pós-login (Topbar), mesma fonte (server/app/pregao.py). O fato é
    // idêntico nos dois modos; só o tom muda — aqui o Estudo ensina que existe
    // um horário fixo de pregão, no Operador (abaixo) o texto fica seco. Nunca
    // inventar horário: a chave "fechado" só menciona "abre {HH:MM}" quando o
    // chamador PASSA o horário — sem argumento, nunca compõe um horário
    // (CLAUDE.md princípio 4).
    mercadoAberto: "Mercado aberto",
    mercadoFechado: (abertura) =>
      abertura
        ? `Mercado fechado — abre ${abertura} (a B3 só negocia em horário de pregão, em dias úteis)`
        : "Mercado fechado",
    mercadoIndisponivel: "Status do mercado indisponível",

    // Fase 2 (MERC-02/03, D-01): BuyModal/SellModal com o mercado fechado —
    // a ordem não some, vira PENDENTE. Mesmo fato nos dois modos, tom muda
    // (aqui explica o "porquê" como o resto do vocabulário Estudo); nunca
    // inventa horário — abertura só aparece quando `ctx.mercado.abertura`
    // vier preenchido (mesma regra de mercadoFechado, acima).
    ordemPendentePill: "PENDENTE",
    ordemPendenteAvisoCompra: (abertura) =>
      abertura
        ? `Mercado fechado agora — a ordem fica pendente e executa ao preço de abertura do próximo pregão, às ${abertura}. O caixa já é reservado nesta confirmação.`
        : "Mercado fechado agora — a ordem fica pendente até a abertura do próximo pregão. O caixa já é reservado nesta confirmação.",
    ordemPendenteAvisoVenda: (abertura) =>
      abertura
        ? `Mercado fechado agora — a ordem fica pendente e executa ao preço de abertura do próximo pregão, às ${abertura}. As cotas já ficam reservadas nesta confirmação.`
        : "Mercado fechado agora — a ordem fica pendente até a abertura do próximo pregão. As cotas já ficam reservadas nesta confirmação.",
    mercadoStatusFalhouNaOrdem: "Não conseguimos confirmar se o mercado está aberto agora — tente de novo antes de enviar a ordem.",
    toastOrdemPendente: (qty, t) => `Ordem pendente registrada: ${qty} ${t}. Executa na abertura do próximo pregão.`,
    toastOrdemPendenteCancelada: "Ordem pendente cancelada — o valor reservado volta a ficar disponível.",

    // Fase 8 (ADR-017 Bloco 3): histórico medido por setup — espelho byte a
    // byte de `server/app/skill_ref.py` (HISTORICO/HISTORICO_ROTULO/ENTRADA_AUTO,
    // modo "educacional"). Placeholders "{janela}"/"{medidoAte}"/"{setup}"/
    // "{janelaRef}" ficam LITERAIS aqui — a interpolação é dos helpers abaixo,
    // não do dicionário (permite comparação byte a byte com o Python).
    historico: {
      elegivel: "Estudo: vantagem estatística medida na janela {janela}.",
      inelegivel: "Estudo: sem vantagem estatística medida na janela {janela}.",
      insuficiente: "Amostra insuficiente (n<40) — ausência de evidência não é prova de mau desempenho.",
      nunca_medido: "Sem histórico medido ainda.",
      aposentado: "Padrão gráfico identificado, sem vantagem estatística medida (ADR-016).",
      desatualizado: "Medido até {medidoAte} — dado pode estar desatualizado.",
    },
    historicoRotulo: {
      elegivel: "VANTAGEM MEDIDA",
      inelegivel: "SEM VANTAGEM MEDIDA",
      insuficiente: "AMOSTRA INSUFICIENTE (n<40)",
      nunca_medido: "SEM HISTÓRICO MEDIDO",
      aposentado: "APOSENTADO (ADR-016)",
    },
    entradaAuto: {
      regra: "No Modo Operador, a entrada automática só executa em setup com vantagem estatística medida na janela anterior — sem vantagem medida, ele sinaliza e não executa.",
      contraste: "Sem filtro: −0,099R por sinal (todos os setups, 15 anos) · Com filtro (setups elegíveis na janela anterior): +0,005R — estatisticamente um empate, não lucro.",
      por_setup_disponivel: "Entrada automática disponível para {setup} — elegibilidade medida em {janelaRef}.",
      por_setup_bloqueado: "Entrada automática bloqueada para {setup} — sem vantagem estatística medida nesta janela.",
    },

    // Plano 04-07 (FIX-C05): aviso de concentração alta na Carteira, quando
    // um único ativo passa de 50% do patrimônio simulado (LIMIAR_CONCENTRACAO
    // em App.jsx). Rótulo/link são iguais nos dois modos (kicker/CTA, não
    // voz); só o corpo forka — texto VERBATIM do UI-SPEC ("FIX-C05"), sem
    // vocabulário de ordem de operação no ramo estudo.
    concentracaoTitulo: "Concentração alta",
    concentracaoCorpo: (ticker, pct) =>
      `${ticker} sozinho responde por ${pct}% do seu patrimônio simulado. Diversificação reduz o quanto um único evento negativo pode derrubar a carteira inteira — vale estudar o conceito antes de aumentar ainda mais essa posição.`,
    concentracaoLink: "saiba mais",

    // Quick 260906-vf9 (C-09, REPORT-01): aviso de drawdown alto no card de
    // patrimônio (CapitalCurve), acima de LIMIAR_DRAWDOWN_ALERTA=15% em
    // App.jsx. Aviso educacional, não bloqueio — mesma disciplina do trio
    // concentracao* acima. Rótulo idêntico nos dois modos; só o corpo forka.
    // Corpo do modo Estudo sem vocabulário de ordem (test_copy_theme.mjs).
    drawdownAlertaTitulo: "Drawdown alto",
    drawdownAlertaCorpo: (pct) =>
      `Sua carteira já caiu ${pct}% desde o pico. Quedas grandes pedem mais cautela: considere reduzir o tamanho das próximas posições até recuperar confiança no plano.`,

    // Fase 14 (Plano 06, 14-UI-SPEC.md "Copywriting Contract"): rótulos de
    // controle e confirmação das operações lastreadas (venda coberta / put de
    // proteção). A MANCHETE e a frase didática nunca vêm daqui — vêm prontas
    // de proposta.manchete/proposta.didatica (motor determinístico, guardrail
    // CVM); este dicionário só cobre eyebrow, CTA e confirmação. Ramo Estudo
    // nunca renderiza CTA (a UI condiciona por `operador`), mas a chave
    // existe pela paridade — vocabulário de ordem proibido aqui mesmo assim.
    eyebrowPropostaCall: "ESTUDO · VENDA COBERTA",
    eyebrowPropostaPut: "ESTUDO · PUT DE PROTEÇÃO",
    ctaVendaCoberta: () => "Ver como esta operação funcionaria",
    ctaPutProtecao: () => "Ver como esta operação funcionaria",
    ctaFecharLastreada: () => "Como esta posição se encerra",
    confirmAbrirCoberta: () => "", // ramo estudo nunca chama window.confirm — chave existe só pela paridade
    confirmFecharCoberta: () => "",
    verCadeiaCompleta: "ver cadeia completa",
    propostaIndisponivelDegradada: "Proposta indisponível — cotação de opções degradada.",
    propostaVaziaTitulo: "Sem proposta agora",

    // Fase 17 (Plano 04, FLOW-01/FLOW-04): payoff e frescor do dado — texto
    // IDÊNTICO nos dois modos (rótulo de dado/aviso de sistema, não voz de
    // professor/mesa; mesmo precedente de propostaIndisponivelDegradada/
    // verCadeiaCompleta/avisoLiquidacaoForcada acima).
    payoffTitulo: "No vencimento, se levar até o fim",
    payoffGanhoMaximo: "ganho máximo",
    payoffPerdaMaxima: "perda máxima",
    payoffBreakeven: "empata em",
    payoffIlimitado: "ilimitado",
    payoffSemDado: "—",
    payoffCaixaCredito: "recebe hoje",
    payoffCaixaDebito: "custa hoje",
    payoffCaixaNeutro: "sem movimento de caixa hoje",
    payoffNota: (precoObjeto) => `Inclui sua posição em ações marcada a R$ ${precoObjeto} (preço de hoje). Resultado no vencimento, antes de custos.`,
    fontePropostaLinha: (fonte, quando) => `Fonte: ${fonte} · ${quando}`,
    fontePropostaSemDado: "Fonte do dado não declarada.",

    // Fase 17 (Plano 05, FLOW-02/FLOW-03): collar (2 pernas, call + put).
    // `collarPernasLinha` é descrição de dado (contrato/strike), não voz de
    // professor/mesa — IDÊNTICA nos dois modos, mesmo precedente de
    // payoffTitulo/fontePropostaLinha acima. Ramo Estudo nunca chama
    // window.confirm (confirmAbrirCollar retorna "" aqui, mesma convenção de
    // confirmAbrirCoberta) e o CTA nunca usa "comprar"/"vender" — "Montar"
    // descreve a estrutura sem infinitivo de ordem. Texto usa "collar" em
    // vez da frase-âncora da manchete do motor (guardrail CVM,
    // test_opcoes_collar_vocab.py::test_nenhum_arquivo_front_compoe_manchete_do_collar
    // — mesma colisão já documentada pelos Planos 17-01/17-03).
    eyebrowPropostaCollar: "ESTUDO · TRAVA PROTETORA",
    collarPernasLinha: (n, ticker, strikeCall, strikePut) => `${n}× TRAVA ${ticker} · call ${strikeCall} / put ${strikePut}`,
    ctaCollarDebito: () => "Ver como este collar funcionaria",
    ctaCollarCredito: () => "Ver como este collar funcionaria",
    confirmAbrirCollar: () => "", // ramo estudo nunca chama window.confirm — chave existe só pela paridade

    // Fase 14 (Plano 07): trava de lastro visível na Carteira. Ramo Estudo
    // evita "vender"/"comprar" — "recomprada" (adjetivo) não contém o
    // infinitivo "comprar" como substring, por isso é a forma usada aqui
    // (guardião test_copy_theme.mjs testa substring, não palavra inteira).
    badgeTravada: (qty) => `${qty} travada(s) · lastro da call coberta`,
    avisoTravaNaVenda: (qty) => `${qty} ação(ões) está(ão) travada(s) como lastro de uma call coberta — volta(m) a ficar disponível(is) quando a call for recomprada ou vencer.`,

    // Fase 14 (Plano 07, T-14-27/T-14-28): liquidação forçada por vencimento
    // (estado do sistema, texto verbatim do UI-SPEC) e ressalva de marcação
    // do patrimônio com pernas lastreadas — mesmo texto nos dois modos
    // (system notice, não voz de professor/mesa; mesmo padrão de
    // verCadeiaCompleta/propostaIndisponivelDegradada acima).
    avisoLiquidacaoForcada: (ticker, valor) => valor === 0
      ? `Esta call de ${ticker} venceu fora do dinheiro — expirou sem valor, o prêmio integral ficou com quem estava do outro lado da operação, e o lastro foi liberado.`
      : `Esta call de ${ticker} venceu dentro do dinheiro e não foi fechada a tempo — liquidada em dinheiro pelo valor intrínseco (R$ ${valor}). Sua posição em ações não foi alterada.`,
    linhaPatrimonioOpcoes: "opções lastreadas (marcadas pelo prêmio de abertura — sem cotação ao vivo)",

    // Fase 18 (Plano 01, NAV-01/NAV-03): tira "Oportunidades de opções" em
    // Posições (agregado, todas as posições) e afordância de detalhe dentro
    // do card de uma posição específica. Rótulo de seção e micro-rótulo de
    // ação são IDÊNTICOS nos dois modos (mesmo precedente de payoffTitulo/
    // verCadeiaCompleta acima); os estados de carregamento/vazio e a
    // afordância da posição têm voz de modo. Nenhuma destas seis chaves
    // pode conter a manchete do motor nem frase que a substitua — a
    // manchete continua vindo só de proposta.manchete (guardrail CVM).
    tiraOpcoesTitulo: "OPORTUNIDADES DE OPÇÕES",
    tiraOpcoesVerDetalhe: "ver detalhe",
    tiraOpcoesCarregando: "Procurando estruturas possíveis nas suas posições…",
    tiraOpcoesSemCobertura: "Nenhuma das suas posições tem opção com liquidez suficiente hoje — sem contrato líquido, não dá para estudar uma estrutura sobre ela.",
    tiraOpcoesSemSetup: "Suas posições têm opção líquida, mas a leitura técnica não indica nenhuma estrutura agora. A cadeia completa continua disponível em cada ativo.",
    // Quick 260908-ldg (D-07): terceiro caso do estado vazio — a diferença
    // para `tiraOpcoesSemCobertura` é NOMEAR a faixa, em vez de "sem
    // liquidez suficiente" genérico. Voz de professor: descreve a condição.
    tiraOpcoesSemMercado: "As opções das suas posições estão hoje na faixa SEM MERCADO — negociaram tão pouco que o preço da tela não seria o preço real de uma ordem. Por isso nenhuma estrutura é estudada sobre elas agora.",
    linhaPropostaNaPosicao: "Estrutura de opções possível nesta posição",

    // Fase 30 (Plano 04, D4): bloco "as 4 melhores estruturas", irmão da
    // tira acima. Nenhuma frase promete rentabilidade, garante lucro ou usa
    // linguagem de enriquecimento (princípios 6/8 do CLAUDE.md) — a
    // manchete de cada item vem SÓ do motor (item.manchete), nunca de uma
    // chave de copy. `curadoriaSubtitulo` nomeia de onde vem a ordem sem
    // citar IA; `curadoriaIaRotulo`/`curadoriaIaRessalva` deixam explícito
    // que o texto seguinte é explicação da IA sobre uma lista já decidida
    // pelo motor.
    //
    // Fase 31 (Plano 04, D-04): a Fase 30 varria só venda coberta —
    // `curadoriaTitulo`/`curadoriaSubtitulo`/`curadoriaCarregando`/
    // `curadoriaVazio` reescritas porque o universo agora cobre as 4
    // estruturas do motor (venda coberta, put de proteção, collar, opção a
    // descoberto). Reversão deliberada, não apagamento — guardião
    // atualizado com nota (D-04). Chaves novas: `curadoriaTipo*` (rótulo de
    // categoria por tipo, nunca a manchete), `curadoriaVarreduraRotulo`
    // (resumo do que a varredura cobriu) e `curadoriaPayoffRotulo` (rótulo
    // da curva de payoff do item nº 1). `curadoriaRazaoAjuda` explica o
    // SINAL do prêmio (negativo = a estrutura custa para montar), não
    // promove estrutura nenhuma — é didática sobre o número que o motor já
    // calculou (princípio 5).
    curadoriaTitulo: "AS 4 MELHORES OPORTUNIDADES DE OPÇÕES",
    curadoriaSubtitulo: "Ordenadas pelo motor por prêmio sobre perda máxima — a ordem não muda com a explicação da IA.",
    curadoriaCarregando: "Varrendo sua carteira em busca das melhores oportunidades…",
    // ESTADO (NAV-03), sem CTA — nomeia o motivo, mesmo precedente de
    // tiraOpcoesSemCobertura acima.
    curadoriaVazio: "Nenhuma estrutura elegível nos vencimentos varridos — por isso não há nada para ranquear agora.",
    curadoriaRazaoRotulo: "prêmio sobre perda máxima",
    curadoriaRazaoAjuda: "Prêmio negativo significa que montar a estrutura custa dinheiro (é uma proteção) — por isso ela pode aparecer embaixo na mesma régua, sem que isso seja um defeito do ranking.",
    curadoriaTipoCallCoberta: "venda coberta",
    curadoriaTipoPutProtecao: "put de proteção",
    // Achado 31-01 (Rule 1, mesma colisão): a expressão canônica de collar
    // de proteção é string-âncora protegida por guardrail CVM desde a Fase
    // 16 (LIB-03, test_opcoes_collar_vocab.py::test_nenhum_arquivo_front_
    // compoe_manchete_do_collar) — nenhum arquivo do front pode compor esse
    // texto (nem em comentário: o guardião varre o arquivo inteiro, sem
    // filtrar comentário), só skill_ref.py. Rótulo de TIPO aqui usa o
    // mesmo texto descritivo já adotado em opcoes_curadoria.py (31-01).
    curadoriaTipoCollar: "collar (call vendida + put comprada)",
    curadoriaTipoDescoberto: "a descoberto",
    curadoriaVarreduraRotulo: "o que esta varredura cobriu",
    curadoriaPayoffRotulo: "Curva de resultado da estrutura nº 1",
    curadoriaNarrarCta: "Pedir explicação da IA",
    curadoriaNarrando: "Escrevendo a explicação…",
    curadoriaIaRotulo: "Explicação da IA sobre esta lista",
    curadoriaIaRessalva: "A IA explica a ordem que o motor já decidiu — ela não escolhe nem reordena as estruturas.",
    curadoriaCotaEsgotada: "Sua cota mensal de análises de IA acabou. Os itens acima continuam valendo — só a explicação em texto não está disponível agora.",
    curadoriaErroNarrar: "Não foi possível gerar a explicação agora. Os itens acima continuam calculados pelo motor e não dependem deste texto.",
  },

  operador: {
    // identidade
    chipModo: "MODO OPERADOR",

    // saudação/tratamento (Acompanhar) — tom de mesa
    saudacao: (nome) => (nome ? `Mesa aberta, ${nome}.` : "Mesa aberta."),
    resumoDia: (nSetups, nGatilhos) =>
      nSetups > 0
        ? `${nSetups} plano(s) válido(s) hoje · ${nGatilhos} gatilho(s) próximos do preço. Disciplina: só entra quem confirmar.`
        : "Nenhum plano com vantagem estatística hoje. Não operar também é posição.",

    // Fase 21 (FIX-03): placeholder de CapitalCurve com 1-2 dias de patrimônio
    // registrados — texto idêntico ao modo Estudo (afirmação factual sobre
    // disponibilidade de dado, não enquadramento de decisão).
    curvaPoucosDias: (dias) =>
      dias === 1
        ? "Só 1 dia registrado ainda — a curva aparece a partir do 3º dia."
        : "Só 2 dias registrados ainda — a curva aparece a partir do 3º dia.",

    // 25-06 (Fase 5 do 25-CONTEXT) — PLANO DA CONTA. Texto IDÊNTICO nos dois
    // modos, mesmo precedente de `curvaPoucosDias` logo acima: é estado de
    // CONTA, não voz de professor vs mesa. O plano não muda como se decide
    // uma operação; ele diz quanto cabe no mês.
    //
    // Nenhuma chave de CTA de upgrade — de propósito, não esquecimento. Não
    // existe loja/IAP no produto (ADR-010, decisão 4) e um botão "assine"
    // prometeria o que não se cumpre. `test_plano_ui.mjs` trava a ausência.
    planoRotulo: "Plano",
    // Sem mapa id -> nome de exibição: o app JÁ mostra o id cru ao usuário no
    // modal de watchlist ("do plano free") e duas vozes para a mesma coisa
    // divergiriam. Um mapa no front também seria uma segunda lista de planos,
    // que fica velha no dia em que existir um terceiro (mesmo raciocínio do
    // guardião do portal, 25-05).
    planoNome: (planId) => (planId ? String(planId) : "—"),
    planoResumoTile: (planId) =>
      (planId ? String(planId) + " — análises" : "Análises") +
      " de IA por mês e ativos na watchlist",
    planoTituloTela: "Plano",
    planoDescricao:
      "O plano da sua conta define quantas análises de IA cabem no mês e quantos ativos cabem na watchlist. Os números abaixo vêm do servidor, no momento em que esta tela abriu. Hoje o plano é definido pela administração do Boris+.",
    // `null` quando o limite não existe: o app NUNCA escreve a palavra que
    // significa "sem teto" nem "X/∞" (D-03 da Fase 13) — a linha some.
    planoEntitlementAnalises: (limite) =>
      (limite == null ? null : "Análises da IA — " + limite + " por mês. Usadas até agora:"),
    planoEntitlementWatchlist: (limite) =>
      (limite == null ? null : "Ativos na watchlist — até " + limite + ". Em uso agora:"),
    // Princípio 4 do CLAUDE.md: limite que não pôde ser confirmado vira
    // travessão + motivo, nunca número estimado.
    planoLimiteIndisponivel:
      "Não foi possível confirmar este limite agora. Ele continua valendo no servidor — só não deu para exibir o número.",
    // Substitui a exibição da frase CRUA do backend no banner de recusa: a
    // `reason` de plan.py é ASCII sem acento (convenção de log Python), não
    // copy de produto. Sem contagem regressiva, sem "só resta 1", sem CTA.
    planoAvisoLimiteWatchlist: (limite, usado) =>
      (limite == null
        ? "Sua watchlist chegou ao limite do seu plano."
        : "Seu plano acompanha até " + limite + " ativos na watchlist.") +
      (usado == null ? "" : " Você tem " + usado + " agora.") +
      " Para acompanhar outro, tire um da lista.",

    // abas
    tabRadar: "Mesa", // qa/34: a aba dizia "Radar" enquanto a tela é "Mesa de oportunidades"
    tituloRadar: "Mesa de oportunidades",
    subtituloRadar: `Varredura do universo com decisão objetiva por ativo: plano de entrada, stop na invalidação, alvos e R:R — abaixo de ${RR_MIN_TXT}:1 a mesa não opera.`,
    tituloWatchlist: "Monitoramento",
    subtituloWatchlist: "Seus ativos monitorados, ordenados por oportunidade (confluência do snapshot). O plano de cada um abre no card.",
    tituloPortfolio: "Posições",
    subtituloPortfolio: "Suas posições e o plano de cada uma — risco controlado em R, parciais no alvo 1.",

    // aba Opções (aba-opcoes F2, 2026-09-10) — voz de mesa: direto ao estado
    // do dado e ao que está armado. Mesmas chaves do ramo estudo (o guardião
    // test_copy_theme.mjs compara os conjuntos ordenados; desde 2026-09-12,
    // `test_vocabulario_opcoes.mjs` também trava a DIFERENÇA de subtítulo
    // entre os modos — ver a nota no ramo estudo, achado A3 da Fase 26).
    tabOpcoes: "Opções",
    tituloOpcoes: "Opções",
    subtituloOpcoes: "Comportamento do ativo, estruturas do catálogo e os setups armados — leitura de fim de pregão. Nenhuma ordem sai daqui.",
    tituloOperadorIA: "Operador IA",
    linkOperadorIA: "Abrir o Operador IA →",
    opcoesLeituraTitulo: "LEITURA DO ATIVO",
    // Fase 27 (27-05) — MESMA substância do ramo estudo, em voz de mesa: o que
    // o serviço acrescenta ao que o motor interno já entregou de graça.
    opcoesLerNoServico: "Puxar a leitura do serviço",
    opcoesLeituraConvite: "O bloco acima sai do motor interno, custo zero. O serviço acrescenta o que só ele tem: catálogo de estruturas, vencimentos abertos e a avaliação de hoje dos vigias deste ativo.",
    opcoesSetupsTitulo: "SETUPS GRAVADOS",
    opcoesPregaoRotulo: "Pregão",
    opcoesFonteRotulo: "Fonte",
    opcoesFrescorEmDia: "dado em dia",
    opcoesFrescorAtrasado: "dado atrasado",
    opcoesFrescorNaoMedido: "frescor não medido",
    // Fase 27 (27-05) — a única chamada da aba sem clique, declarada. Mesma
    // razão do ramo estudo: o gate de frescor precisa existir na abertura
    // (ADR-027, Decisão 8), então o que resta é dizer o preço dele.
    opcoesCustoFrescor: "Abrir a aba consulta o frescor no serviço: até 1 chamada da cota do dia, zero quando o frescor está em cache. É a única consulta desta tela que sai sem pedido — o resto sai de botão com o preço escrito.",
    // 24-12 — MESMA medição, em voz de mesa. O rótulo do chip é o mesmo nos
    // dois modos de propósito: é contagem de pregão, não juízo — e "2 pregões
    // atrás" já é a frase mais curta que diz o fato.
    opcoesAtrasoPregoes: (n) => (n === 1 ? "1 pregão atrás" : n + " pregões atrás"),
    opcoesAtrasoAjuda: "Contagem de pregões FECHADOS pelo calendário da B3 — fim de semana e feriado fora. O pregão de hoje só entra depois de publicado o fechamento.",
    opcoesSemSetups: "Nenhum setup gravado para este ativo. Sem condição escrita antes do pregão, não há o que a mesa avalie.",
    opcoesNaoAvaliado: (motivo) =>
      motivo
        ? "Setups não avaliados hoje. Motivo do serviço: " + motivo
        : "Setups não avaliados hoje, sem motivo informado. Sem avaliação, nenhum setup entra como armado.",
    // 24-11 — MESMA substância do outro ramo, em voz de mesa: o campo não tem
    // número, este é o motivo, e nada foi estimado no lugar. O motivo segue
    // verbatim do backend; só a moldura muda.
    opcoesLacuna: (campos, motivo) => {
      const lista = (Array.isArray(campos) ? campos : []).filter(Boolean);
      const nomes = lista.length > 1
        ? lista.slice(0, -1).join(", ") + " e " + lista[lista.length - 1]
        : (lista[0] || "Este campo");
      return nomes + " sem número: " +
        (motivo || "o serviço não informou o motivo") +
        ". Nada estimado no lugar.";
    },
    opcoesNaoConfigurado: "Serviço de opções não configurado neste servidor. Nada foi consultado.",
    opcoesCota: (reinicia) =>
      "Cota de consultas da aba Opções esgotada no dia." +
      (reinicia ? " Reinicia às " + reinicia + "." : " Reinicia na virada do dia."),
    opcoesIndisponivel: "Serviço de opções sem resposta agora. Tente em alguns minutos — nenhum número foi estimado no lugar.",
    // 24-07 (achado F-04). MESMA substância do outro ramo, em voz de mesa: o
    // que a pessoa precisa é fechar a conta da própria cota.
    opcoesRecusaCobrada: "Consulta recusada pelo serviço e cobrada assim mesmo: consumiu uma chamada da sua cota do dia. O serviço conta a chamada na entrada, não na resposta.",
    opcoesCarregando: "Consultando o serviço de opções…",
    // Fase 27 (D3): mesma troca do outro ramo — o universo é a carteira, não o
    // monitoramento. Chave preservada (é marcador de ordem no guardião).
    opcoesEscolherAtivo: "Escolha um ativo da carteira para ver a leitura.",
    // Fase 27 (D2), voz de mesa: o motivo em uma linha e o caminho logo em
    // seguida. MESMA substância do ramo estudo.
    opcoesCarteiraVazia: "A aba opera sobre a carteira: estrutura de opção aqui é lastreada em ação que você já tem. Carteira vazia, nada a lastrear e nada a vigiar. A watchlist não substitui — interesse não é lastro. Abra a Carteira e monte a posição antes.",
    opcoesIrParaCarteira: "Abrir a Carteira",
    // Fase 27 (27-02) — MESMAS chaves do ramo estudo, voz de mesa. O título é
    // igual nos dois por decisão (ver a nota no outro ramo).
    opcoesVigiasTitulo: "SEUS VIGIAS",
    opcoesVigiasVazio: "Nenhum vigia gravado nesta conta. Vigia é condição objetiva escrita antes do pregão e conferida uma vez por dia, sobre o fechamento. Sem condição escrita, não há o que conferir.",
    opcoesVigiasSemEstado: "— estado do dia ainda não pedido. Acima está só o cadastro, que é local e não custa cota. Estado é medição do serviço e sai sob pedido.",
    opcoesVigiasAtualizar: "Medir o estado do dia",
    opcoesVigiaForaDaCarteira: "Ativo fora da carteira. O vigia segue existindo e segue sendo conferido; o que falta é o papel para lastrear estrutura sobre ele.",
    // Fase 27 (27-02, D4) — MESMAS chaves do ramo estudo, voz de mesa. Mesmo
    // vocabulário de `badgeTravada`/`avisoTravaNaVenda`.
    opcoesLastroLivre: (livres, contratos) =>
      "Livre para lastro: " + (typeof livres === "number" ? livres : "—") +
      " ação(ões) = " + (typeof contratos === "number" ? contratos : "—") + " contrato(s).",
    opcoesLastroTravado: (travadas) =>
      (typeof travadas === "number" ? travadas : "—") +
      " ação(ões) travada(s) como lastro da call coberta aberta — liberam na recompra ou no vencimento.",
    opcoesLastroAjuda: "1 contrato = 100 ações. Mesmo número da Carteira, mesma conta; nenhuma ordem sai desta tela.",
    opcoesLastroSemDado: "quantidade desta posição ilegível, então o lastro não é afirmado. Zero diria \"sem lastro\", que é outra afirmação.",
    // Fase 27 (27-04, D1/D4) — a leitura técnica interna, voz de mesa: o
    // estado, a fonte e o custo, sem a aula. MESMAS chaves do ramo estudo.
    opcoesInternaTitulo: "TÉCNICO DO ATIVO",
    opcoesInternaCarimbo: (asOf, fonte) =>
      "Pregão de " + (asOf || "—") + " · motor interno sobre " + (fonte || "—") +
      ". Mesma fonte do Radar e da Watchlist.",
    opcoesSemCusto: "grátis — motor interno, não consulta o serviço",
    opcoesInternaCarregando: "Calculando o técnico no app…",
    opcoesInternaErro: "Técnico interno indisponível agora. Nada estimado no lugar; vigias e leitura do serviço seguem valendo.",
    opcoesRegimeRotulo: {
      tendencia_alta: "tendência de alta",
      tendencia_baixa: "tendência de baixa",
      lateral: "lateral",
      indefinido: "indefinido — sem dado para classificar",
    },
    opcoesForcaRotulo: { forte: "forte", transicao: "em transição", fraca: "fraca" },
    opcoesRegimeNaoConfiavel: "Classificação apoiada na média de 50, não na de 200 — a janela longa ainda não fechou. Vale para o que mede; não afirma tendência longa.",
    opcoesReguaTitulo: "Evolução da semana",
    opcoesReguaAjuda: "Um segmento por pregão fechado, mais antigo à esquerda. A cor é o regime MEDIDO no dia; não é previsão do próximo. Segmento apagado = janela longa indisponível, classificação pela média curta.",
    opcoesReguaSemDados: "Pregões insuficientes para a evolução da semana. A faixa fica fora em vez de vir vazia: sete \"indefinido\" seriam lidos como semana sem direção, que é outra afirmação.",
    opcoesDisclaimer: "Conteúdo educacional. Dados de fim de pregão, possivelmente atrasados; nada aqui é ordem, recomendação ou promessa de resultado.",
    opcoesGraficoTitulo: "Disparos do setup",
    opcoesDisparosRotulo: "Disparos",

    // aba Opções F3 (plano 24-02, 2026-09-11) — voz de mesa: direto ao
    // estado e ao custo. MESMAS chaves do ramo estudo. Os quatro textos
    // regulatórios (delta, ±1σ, breakeven e os dois "ilimitado") repetem a
    // substância do outro ramo de propósito: é o que o app AFIRMA, e isso
    // não muda com o tom.
    opcoesAnalisarTitulo: "ESTRUTURA PARA A TESE",
    opcoesPossibilidadesTitulo: "POSSIBILIDADES POR VENCIMENTO",
    opcoesTeseRotulo: "Tese da mesa. O serviço não escolhe direção — e o app menos ainda.",
    opcoesTeseAlta: "Alta",
    opcoesTeseBaixa: "Baixa",
    opcoesTeseNeutra: "Neutra",
    opcoesLoteRotulo: "Lote (ações)",
    opcoesLoteAjuda: "1 contrato = 100 ações. Converte em reais os números que vêm por ação; a conta é do servidor.",
    opcoesMontarEstrutura: "Montar estrutura",
    opcoesVerPossibilidades: "Ver possibilidades",
    // Fase 27 (27-02): mesma separação do ramo estudo — custo genérico aqui,
    // composição na chave própria abaixo.
    opcoesCustoChamadas: (n) =>
      "Custo desta consulta: " + (typeof n === "number" ? n : "—") +
      " chamada(s) da cota do dia.",
    opcoesCustoVencimentos: "Composição: 1 chamada para listar os vencimentos + 2 por vencimento consultado.",
    // Fase 27 (27-05) — mesmo fato, voz de mesa: dois eixos de custo no mesmo
    // controle, e o número da cota de IA mora no gate, não nesta frase.
    opcoesCustoAnaliseIA: "Consome também 1 análise de IA da cota do dia — cota separada desta.",
    opcoesVerCadeia: "Ver a cadeia",
    opcoesVerOperaveis: "Ver as operáveis",
    opcoesCriterioOperaveis: (c) => {
      const k = c || {};
      const n = (v) => (typeof v === "number" ? String(v).replace(".", ",") : "—");
      return "Peneira: mín. " + n(k.minNegocios) + " negócios no pregão, delta entre " +
        n(k.deltaMin) + " e " + n(k.deltaMax) +
        ". Critério do Boris, não do serviço — strike fora da faixa saiu por escolha nossa, não por falta de dado.";
    },
    opcoesSemEstrutura: "Sem pontos de payoff nesta resposta. Os números do cabeçalho valem; a curva, não há — e desenhar um gráfico vazio seria afirmar resultado zero.",
    opcoesSemVencimento: "Nenhum vencimento aberto na leitura deste ativo. Nada a consultar.",
    opcoesBreakevenRotulo: "Breakeven",
    opcoesBreakevenAjuda: "preço do ativo no vencimento em que a estrutura empata. É preço, não dinheiro: não se multiplica pelo lote.",
    // 24-06 (achado F-01). MESMA negação do outro ramo: "não é probabilidade"
    // não é tom, é o que o app afirma sobre o número.
    opcoesRazaoRotulo: "Razão G/P",
    opcoesRazaoAjuda: "quantas vezes o ganho máximo cabe na perda máxima; não é probabilidade de nada. \"1 : 0,67\" = 0,67 de ganho máximo para cada 1 de risco.",
    opcoesCenariosTitulo: "Cenários",
    opcoesSigmaAjuda: "cenários ±1σ a partir da volatilidade realizada de 21 pregões — é conta de dispersão, não previsão de preço.",
    opcoesDeltaAjuda: "delta ≈ chance de terminar dentro do dinheiro (aproximação)",
    opcoesPorAcaoRotulo: "por ação",
    opcoesEmReaisRotulo: "em reais (lote)",
    opcoesGanhoIlimitado: "sem teto",
    opcoesPerdaIlimitada: "sem piso declarado pelo serviço",
    opcoesCadeiaTruncada: (t) =>
      "Lista cortada pelo serviço: " + (t || "sem detalhe informado."),
    opcoesAlvoRotulo: "Alvo (opcional)",
    opcoesStopRotulo: "Stop (opcional)",

    // aba Opções F5 (plano 24-04, 2026-09-11) — criar setup por descrição.
    // MESMAS chaves do ramo estudo. `opcoesBacktestRessalva` é IDÊNTICA
    // byte a byte à do outro ramo, de propósito: ela não é tom, é o que o
    // app AFIRMA sobre números de histórico — e isso não muda com a voz.
    opcoesCriarTitulo: "CRIAR SETUP",
    opcoesCriarAjuda: "Condição objetiva, nas suas palavras: indicador, comparação e número. Avaliada UMA vez por pregão, sobre o fechamento — não intradiária. Quem valida o vocabulário é o serviço de dados; a recusa dele volta verbatim. Mínimo de 15 caracteres.",
    opcoesCriarPlaceholder: "Ex.: IFR de 2 períodos abaixo de 25 com o preço acima da média de 200 pregões",
    opcoesCriarBotao: "Compilar e ensaiar",
    opcoesCriarConfirmar: "Gravar setup",
    opcoesCriarDesativar: "Desativar",
    opcoesCriarConfirmarDesativacao: "Confirmar a desativação",
    opcoesCriarProblemas: "Setup recusado pelo serviço. O que ele apontou, item por item:",
    opcoesCriarCru: "A IA não devolveu um setup legível — nada foi gravado. Resposta dela, sem edição:",
    opcoesCriarFaltando: (campos) =>
      "Resposta sem campo obrigatório do serviço: " +
      (Array.isArray(campos) && campos.length ? campos.join(", ") : "—") +
      ". Nada gravado — completar por conta seria inventar o que ninguém escreveu.",
    opcoesCriarGravado: (nome) =>
      "Setup " + (nome || "—") + " ativo. Passa a ser avaliado uma vez por pregão e já aparece na lista acima.",
    opcoesCriarDesativado: (nome) =>
      "Setup " + (nome || "—") + " inativo. Deixa de ser avaliado; o histórico dele fica.",
    opcoesCriarSemPermissao: "Criar setup exige permissão que esta conta não tem. Esconder o botão é conveniência: o servidor recusa a gravação de qualquer forma.",
    opcoesBacktestTitulo: "ENSAIO NO HISTÓRICO",
    opcoesBacktestDisparos: (n, por100) =>
      "Disparos no período: " + (n === null || n === undefined ? "—" : n) + " — " +
      (por100 === null || por100 === undefined ? "—" : por100) +
      " a cada 100 pregões avaliáveis.",
    opcoesBacktestRetorno: (passo, medio, mediano, comDado) =>
      "Variação do ativo em " + (passo || "—") + " após o disparo: média " +
      (medio === null || medio === undefined ? "—" : medio) + ", mediana " +
      (mediano === null || mediano === undefined ? "—" : mediano) + " (" +
      (comDado === null || comDado === undefined ? "—" : comDado) + " disparo(s) com dado suficiente).",
    opcoesBacktestRessalva: "Contagem do que já aconteceu no histórico. Não é expectativa de retorno, e taxa de disparo não é taxa de acerto.",
    // 24-14 (achado ao vivo 2026-09-11): o ensaio que devolve "0 disparos"
    // sem ter testado nada. É o texto mais delicado desta fase — ele diz à
    // pessoa que o número que ela está vendo não significa o que parece.
    // Vem ANTES dos números de propósito: quem lê o número primeiro já
    // formou a conclusão. O MOTIVO de cada condição vem pronto do backend e
    // é exibido verbatim; aqui só mora a moldura, e ela tem voz por modo.
    opcoesEnsaioIndisparavel: "Ensaio sem valor de teste. Uma das condições exige mais pregões do que o histórico usado tem e ficou sem valor em todos os dias — e o setup só dispara com todas as condições valendo no mesmo pregão. O zero de disparos abaixo sai da conta, não de raridade. Nada estimado no lugar.",
    opcoesEnsaioRessalva: "Ressalva antes dos números: condição sem valor em parte do período do ensaio. O que ficou sem verificação está listado; os números abaixo valem só nos pregões em que deu para verificar.",
    opcoesEnsaioCondicao: (indicador, janela, motivo) => {
      const nome = (typeof indicador === "string" && indicador)
        ? indicador : "condição sem indicador nomeado";
      const j = Number.isFinite(janela) ? " (janela de " + janela + " pregões)" : "";
      return nome + j + ": " + (motivo || "o serviço não informou o motivo") + ".";
    },
    opcoesDadoAtrasado: (idade, motivo) =>
      motivo === "nao_medido"
        ? "A idade do dado de negociação não foi medida nesta consulta. Sem medição, o setup não é gravado — ele vigiaria um pregão que ninguém conferiu."
        : "Dado de negociação da B3 atrasado" +
          (idade === null || idade === undefined || idade === "" ? "" : " (" + idade + ")") +
          ": um setup criado agora vigiaria um pregão que já passou. Nada foi gravado.",

    // Fase 28-02 — sub-aba "Operar". Mesma nota do ramo estudo: "Setups" é
    // IGUAL nos dois modos (nome do artefato); "Operar" é imperativo (a mesa
    // executa, não só descreve).
    opcoesSubabaSetups: "Setups",
    opcoesSubabaOperar: "Operar",
    opcoesOperarIntro: "Aqui está a estrutura lastreada que o motor propõe para cada posição da carteira, com ganho máximo, perda máxima e pontos de empate em número. Abrir e fechar acontece direto aqui — nenhuma ordem sai para corretora nenhuma.",
    opcoesOperarEscolherPosicao: "Escolha uma posição da carteira para ver a estrutura que a mesa propõe para ela.",
    opcoesOperarSemLiquidez: (t) =>
      "Sem contrato com liquidez confirmada para " + (t || "este ativo") + " agora. Sem cadeia líquida a mesa não monta estrutura, e nada foi estimado no lugar.",

    // onboarding (home vazia) — qa/34: voz de mesa
    welcomeTitulo: "Bem-vindo à sua mesa de operações",
    welcomeCorpo: "O fluxo da mesa: a Mesa de oportunidades varre o universo e monta o plano, o Monitoramento acompanha os ativos armados e as Posições controlam risco e resultado em R. A execução é sempre sua, na corretora.",
    welcomeCta: "Abrir a Mesa de oportunidades →",

    // Mesa — bloco "como funciona" + CTAs de monitoramento (qa/34)
    comoAnalisaTitulo: "COMO A MESA DECIDE",
    comoAnalisaCorpo: `Cada ativo é comparado a setups clássicos, como um checklist de critérios objetivos. A confluência é o percentual ponderado de critérios atendidos. Sobre ela a mesa monta o plano: entrada, stop na invalidação e alvos com R:R mínimo de ${RR_MIN_TXT}:1 — abaixo disso, não se opera. Nenhuma ordem é enviada à corretora; a execução é sua.`,
    btnAddMonitor: "+ Monitorar",
    jaMonitorado: "✓ Monitorado",

    // ações
    btnComprar: "Registrar entrada",
    btnVender: "Registrar saída",
    btnAnalise: "Plano completo",
    btnAprofundar: "Plano da mesa (IA)",

    // estados vazios
    vazioWatchlist: "Nada monitorado. Puxe da Mesa de oportunidades os ativos com plano válido.",
    vazioPortfolio: "Sem posições abertas. Capital parado também é gestão — espere o plano certo.",

    // superfícies secundárias (home, modais)
    kickerSetups: "PLANOS NO MONITORAMENTO",
    btnLevarWatchlist: "Monitorar este ativo →",
    btnVerWatchlist: "Ver Monitoramento",
    tituloLeituraIA: (t) => `${t} · plano da mesa`,
    confirmarCompra: "Confirmar entrada",
    confirmarVenda: "Confirmar saída",
    filtroAlta: "Compra",
    filtroBaixa: "Venda",
    notaStopAlvo: "Plano da mesa por perfil de risco — stop na invalidação técnica, alvo com R:R explícito. A execução é sua, na corretora.",
    vazioHistorico: "Suas entradas e saídas registradas aparecerão aqui.",

    // toasts/notificações
    toastCompra: (qty, t) => `Entrada registrada: ${qty} ${t}. Stop e alvo já definidos? Sem plano, sem posição.`,
    toastVenda: (desc, t) => `Saída registrada: ${desc} de ${t}. Anote o resultado em R.`,
    notifStopTitulo: (t) => `STOP executável · ${t}`,
    notifStopCorpo: (t, preco, stop) => `${t} a R$ ${preco} rompeu o stop de R$ ${stop}. Execute a saída na corretora — o plano manda.`,
    notifAlvoTitulo: (t) => `ALVO no preço · ${t}`,
    notifAlvoCorpo: (t, preco, alvo) => `${t} a R$ ${preco} tocou o alvo de R$ ${alvo}. Realize a parcial e suba o stop — disciplina.`,
    // qa/34: título antes IDÊNTICO ao do Estudo — agora segue o padrão de mesa
    // dos irmãos (STOP executável / ALVO no preço: palavra-chave em caixa-alta).
    notifVarTitulo: (t) => `MOVIMENTO forte · ${t}`,
    notifVarCorpo: (t, ch, preco) => `${t} ${ch} no dia (R$ ${preco}). Confira se algum plano armado foi atingido.`,

    // rodapé/disclaimer
    disclaimer: DISCLAIMERS.operador,
    rodape: "Mesa de decisão — a execução e o risco são seus. Nenhuma ordem é enviada à corretora.",

    // Fase 2 (MERC-01, D-08): mesmo status/fonte do ramo estudo (acima), tom
    // seco de mesa — o fato não muda entre modos, só a voz.
    mercadoAberto: "Mercado aberto",
    mercadoFechado: (abertura) => (abertura ? `Mercado fechado — abre ${abertura}` : "Mercado fechado"),
    mercadoIndisponivel: "Status do mercado indisponível",

    // Fase 2 (MERC-02/03, D-01): mesmo fato do ramo estudo (acima), tom seco
    // de mesa.
    ordemPendentePill: "PENDENTE",
    ordemPendenteAvisoCompra: (abertura) =>
      abertura
        ? `Mercado fechado — ordem pendente, executa na abertura às ${abertura}. Caixa reservado agora.`
        : "Mercado fechado — ordem pendente até a próxima abertura. Caixa reservado agora.",
    ordemPendenteAvisoVenda: (abertura) =>
      abertura
        ? `Mercado fechado — ordem pendente, executa na abertura às ${abertura}. Cotas reservadas agora.`
        : "Mercado fechado — ordem pendente até a próxima abertura. Cotas reservadas agora.",
    mercadoStatusFalhouNaOrdem: "Status do mercado indisponível agora — tente de novo antes de enviar a ordem.",
    toastOrdemPendente: (qty, t) => `Ordem pendente: ${qty} ${t}. Executa na abertura do próximo pregão.`,
    toastOrdemPendenteCancelada: "Ordem pendente cancelada — caixa liberado.",

    // Fase 8 (ADR-017 Bloco 3): espelho byte a byte de `server/app/skill_ref.py`
    // (HISTORICO/HISTORICO_ROTULO/ENTRADA_AUTO, modo "operador").
    historico: {
      elegivel: "✓ ELEGÍVEL — vantagem estatística medida na janela {janela}.",
      inelegivel: "✗ NÃO ELEGÍVEL — sem vantagem estatística medida na janela {janela}.",
      insuficiente: "Amostra insuficiente (n<40) — ausência de evidência não é prova de mau desempenho.",
      nunca_medido: "Sem histórico medido ainda.",
      aposentado: "Padrão gráfico identificado, sem vantagem estatística medida (ADR-016).",
      desatualizado: "Medido até {medidoAte} — dado pode estar desatualizado.",
    },
    historicoRotulo: {
      elegivel: "✓ ELEGÍVEL",
      inelegivel: "✗ NÃO ELEGÍVEL",
      insuficiente: "AMOSTRA INSUFICIENTE (n<40)",
      nunca_medido: "SEM HISTÓRICO MEDIDO",
      aposentado: "APOSENTADO (ADR-016)",
    },
    entradaAuto: {
      regra: "Entrada automática só executa em setup com vantagem estatística medida na janela anterior — sem vantagem medida, o Operador sinaliza e não executa.",
      contraste: "Sem filtro: −0,099R por sinal (todos os setups, 15 anos) · Com filtro (setups elegíveis na janela anterior): +0,005R — estatisticamente um empate, não lucro.",
      por_setup_disponivel: "Entrada automática disponível para {setup} — elegibilidade medida em {janelaRef}.",
      por_setup_bloqueado: "Entrada automática bloqueada para {setup} — sem vantagem estatística medida nesta janela.",
    },

    // Plano 04-07 (FIX-C05): mesmo aviso do ramo estudo, tom de mesa — stop
    // ruim carrega peso desproporcional, não "diversificação" como conceito
    // de estudo. Chaves espelhadas (rótulo/link idênticos, ver ramo estudo).
    concentracaoTitulo: "Concentração alta",
    concentracaoCorpo: (ticker, pct) =>
      `${ticker} concentra ${pct}% da carteira. Acima disso, um único stop ruim carrega peso desproporcional no resultado — considere o tamanho antes do próximo aporte no papel.`,
    concentracaoLink: "saiba mais",

    // Quick 260906-vf9 (C-09, REPORT-01): mesmo aviso do ramo estudo, tom de
    // mesa — limiar LIMIAR_DRAWDOWN_ALERTA=15% em App.jsx. Chave espelhada
    // (rótulo idêntico, ver ramo estudo).
    drawdownAlertaTitulo: "Drawdown alto",
    drawdownAlertaCorpo: (pct) =>
      `Drawdown de ${pct}% desde o pico. Perda dessa magnitude pede revisão de tamanho antes da próxima entrada — não force recuperação com posição maior.`,

    // Fase 14 (Plano 06): mesma chave do ramo estudo (ver comentário acima).
    // Registro de mesa (imperativo) — texto VERBATIM do UI-SPEC.
    eyebrowPropostaCall: "PROPOSTA · VENDA COBERTA",
    eyebrowPropostaPut: "PROPOSTA · PUT DE PROTEÇÃO",
    ctaVendaCoberta: (n, ticker, strike, premio) => `Vender ${n}× CALL ${ticker} · strike ${strike} — recebe R$ ${premio}`,
    ctaPutProtecao: (n, ticker, strike, premio) => `Comprar ${n}× PUT ${ticker} · strike ${strike} — custa R$ ${premio}`,
    // ATUALIZADO 2026-09-07 (quick 260907-x69): as duas funções abaixo foram
    // escritas na Fase 14 só para a call coberta e nunca generalizadas quando
    // o fechamento da put entrou — fechar uma put de proteção mostrava
    // "Recomprar a call — R$ X" e uma confirmação que fala em "destrava
    // ações", que a put nunca travou (achado ao vivo em staging, iPhone,
    // Modo Operador, put ABEV3 strike 30,00). O parâmetro de lado (`isCall`)
    // entra POR ÚLTIMO de propósito: chamada antiga (3 args) degrada pro
    // ramo da put em vez de quebrar. `confirmFecharCoberta` mantém o nome
    // herdado — renomear mexeria em CHAVES_LASTREADAS (guardião web) sem
    // ganho — apesar de cobrir os dois lados agora.
    ctaFecharLastreada: (custo, isCall) => isCall
      ? `Recomprar a call — R$ ${custo}`
      : `Vender a put — recebe R$ ${custo}`,
    confirmAbrirCoberta: (n, ticker, qty) => `Vender ${n} call(s) de ${ticker} trava ${qty} ação(ões) do seu lote-lastro até você recomprar a call ou ela vencer. Continuar?`,
    confirmFecharCoberta: (custo, qty, ticker, isCall) => isCall
      ? `Recomprar esta call por R$ ${custo} destrava ${qty} ação(ões) de ${ticker} imediatamente. Continuar?`
      : `Vender esta put por R$ ${custo} encerra a proteção de ${qty} ação(ões) de ${ticker} imediatamente. Continuar?`,
    verCadeiaCompleta: "ver cadeia completa",
    propostaIndisponivelDegradada: "Proposta indisponível — cotação de opções degradada.",
    propostaVaziaTitulo: "Sem proposta agora",

    // Fase 17 (Plano 04, FLOW-01/FLOW-04): mesma chave do ramo estudo (ver
    // comentário acima) — rótulo de dado/aviso de sistema, texto IDÊNTICO
    // nos dois modos, mesmo precedente de propostaIndisponivelDegradada.
    payoffTitulo: "No vencimento, se levar até o fim",
    payoffGanhoMaximo: "ganho máximo",
    payoffPerdaMaxima: "perda máxima",
    payoffBreakeven: "empata em",
    payoffIlimitado: "ilimitado",
    payoffSemDado: "—",
    payoffCaixaCredito: "recebe hoje",
    payoffCaixaDebito: "custa hoje",
    payoffCaixaNeutro: "sem movimento de caixa hoje",
    payoffNota: (precoObjeto) => `Inclui sua posição em ações marcada a R$ ${precoObjeto} (preço de hoje). Resultado no vencimento, antes de custos.`,
    fontePropostaLinha: (fonte, quando) => `Fonte: ${fonte} · ${quando}`,
    fontePropostaSemDado: "Fonte do dado não declarada.",

    // Fase 17 (Plano 05, FLOW-02/FLOW-03): mesma chave do ramo estudo (ver
    // comentário acima) — `collarPernasLinha` IDÊNTICA nos dois modos
    // (descrição de dado). CTA em duas chaves (débito/crédito) em vez de uma
    // com o texto montado no componente: o front escolhe chave, não compõe
    // frase. `confirmAbrirCollar` declara a trava, a quantidade e o "as duas
    // pernas juntas ou nenhuma" — mesma razão que já obriga confirmação na
    // venda coberta (T-14-24), aplicada à estrutura de 2 pernas.
    eyebrowPropostaCollar: "PROPOSTA · TRAVA PROTETORA",
    collarPernasLinha: (n, ticker, strikeCall, strikePut) => `${n}× TRAVA ${ticker} · call ${strikeCall} / put ${strikePut}`,
    ctaCollarDebito: (n, ticker, sc, sp, valor) => `Montar ${n}× trava ${ticker} · call ${sc} / put ${sp} — custa R$ ${valor}`,
    ctaCollarCredito: (n, ticker, sc, sp, valor) => `Montar ${n}× trava ${ticker} · call ${sc} / put ${sp} — recebe R$ ${valor}`,
    confirmAbrirCollar: (n, ticker, qty) => `Montar ${n} trava(s) protetora(s) de ${ticker} trava ${qty} ação(ões) do seu lote-lastro (perna da call) até você encerrar a estrutura ou ela vencer. As duas pernas são abertas juntas — ou nenhuma. Continuar?`,

    // Fase 14 (Plano 07): mesma chave do ramo estudo (ver comentário acima).
    // Registro de mesa — vocabulário de ordem liberado aqui.
    badgeTravada: (qty) => `${qty} travada(s) · lastro de CALL`,
    avisoTravaNaVenda: (qty) => `${qty} ação(ões) travada(s) como lastro da call coberta — liberam quando você recomprar a call ou ela vencer.`,

    // Fase 14 (Plano 07): mesma chave do ramo estudo (ver comentário acima) —
    // texto idêntico, system notice sem voz de modo.
    avisoLiquidacaoForcada: (ticker, valor) => valor === 0
      ? `Esta call de ${ticker} venceu fora do dinheiro — expirou sem valor, o prêmio integral ficou com quem estava do outro lado da operação, e o lastro foi liberado.`
      : `Esta call de ${ticker} venceu dentro do dinheiro e não foi fechada a tempo — liquidada em dinheiro pelo valor intrínseco (R$ ${valor}). Sua posição em ações não foi alterada.`,
    linhaPatrimonioOpcoes: "perna de opções (prêmio de abertura — sem cotação ao vivo)",

    // Fase 18 (Plano 01, NAV-01/NAV-03): mesma chave do ramo estudo (ver
    // comentário acima). Registro de mesa nos estados de carregamento/vazio
    // e na afordância da posição; rótulo de seção e micro-rótulo de ação
    // permanecem idênticos ao ramo estudo.
    tiraOpcoesTitulo: "OPORTUNIDADES DE OPÇÕES",
    tiraOpcoesVerDetalhe: "ver detalhe",
    tiraOpcoesCarregando: "Varrendo suas posições…",
    tiraOpcoesSemCobertura: "Nenhuma posição com opção líquida hoje — sem contrato líquido, não há estrutura para montar.",
    tiraOpcoesSemSetup: "Cobertura líquida existe, mas a leitura técnica não indica venda coberta, put de proteção nem collar agora. A cadeia completa continua disponível em cada ativo.",
    // Quick 260908-ldg (D-07): mesma distinção do ramo estudo (ver
    // comentário acima). Voz de mesa, sem verbo de ordem.
    tiraOpcoesSemMercado: "As opções das suas posições estão hoje na faixa SEM MERCADO — negociaram tão pouco que o preço da tela não é um preço real de execução. Nenhuma estrutura é montada sobre elas agora.",
    linhaPropostaNaPosicao: "Estrutura de opções disponível nesta posição",

    // Fase 30 (Plano 04, D4): mesma chave do ramo estudo (ver comentário
    // acima). Voz de mesa, sem verbo de ordem, sem promessa de lucro.
    //
    // Fase 31 (Plano 04, D-04): mesma reescrita/extensão do ramo estudo
    // (ver comentário acima) — voz de mesa, curta.
    curadoriaTitulo: "AS 4 MELHORES OPORTUNIDADES DE OPÇÕES",
    curadoriaSubtitulo: "Ordenadas pelo motor por prêmio sobre perda máxima — a ordem não muda com o texto da IA.",
    curadoriaCarregando: "Varrendo a carteira…",
    curadoriaVazio: "Nenhuma estrutura elegível nos vencimentos varridos — sem nada para ranquear agora.",
    curadoriaRazaoRotulo: "prêmio / perda máxima",
    curadoriaRazaoAjuda: "Prêmio negativo = a estrutura custa para montar (proteção) — por isso pode aparecer embaixo na régua.",
    curadoriaTipoCallCoberta: "venda coberta",
    curadoriaTipoPutProtecao: "put de proteção",
    curadoriaTipoCollar: "collar (call vendida + put comprada)",
    curadoriaTipoDescoberto: "a descoberto",
    curadoriaVarreduraRotulo: "o que a varredura cobriu",
    curadoriaPayoffRotulo: "Payoff da estrutura nº 1",
    curadoriaNarrarCta: "Explicação da IA",
    curadoriaNarrando: "Gerando…",
    curadoriaIaRotulo: "Leitura da IA sobre esta lista",
    curadoriaIaRessalva: "A IA lê a ordem que o motor decidiu — não escolhe nem reordena.",
    curadoriaCotaEsgotada: "Cota mensal de análises esgotada. Os itens seguem valendo; só o texto da IA fica indisponível.",
    curadoriaErroNarrar: "Falha ao gerar o texto agora. Os itens não dependem dele.",
  },
};

// Acesso seguro: modo desconhecido cai no Estudo (padrão do app).
export function copyFor(mode) {
  return COPY[mode === "operador" ? "operador" : "estudo"];
}

// Espelho de `skill_ref.historico_txt` (Fase 8, ADR-017 Bloco 3): resolve o
// modo pelo mesmo critério de `copyFor`, cai em `nunca_medido` se o estado
// não existir, e interpola "{janela}"/"{medidoAte}".
export function historicoTxt(mode, estado, vals) {
  const h = copyFor(mode).historico;
  const frase = h[estado] || h.nunca_medido;
  return frase
    .replace("{janela}", (vals && vals.janela) || "?")
    .replace("{medidoAte}", (vals && vals.medidoAte) || "?");
}

// Espelho de `skill_ref.entrada_auto_txt`: falha FECHADA — só `estado ===
// "disponivel"` libera a frase positiva; qualquer outro valor cai em
// `por_setup_bloqueado`.
export function entradaAutoTxt(mode, estado, vals) {
  const e = copyFor(mode).entradaAuto;
  const frase = estado === "disponivel" ? e.por_setup_disponivel : e.por_setup_bloqueado;
  return frase
    .replace("{setup}", (vals && vals.setup) || "?")
    .replace("{janelaRef}", (vals && vals.janelaRef) || "?");
}
