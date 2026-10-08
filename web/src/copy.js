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
    // Fase 35 (35-01, D-01/D-06) — rótulo de progresso do estágio 1 (a
    // "porta" de leitura paga) e o metadado que ocupa o lugar do convite
    // quando a leitura já existe. Valor IDÊNTICO nos dois modos: são
    // metadado de estado, categoria já neutra neste arquivo (mesmo padrão
    // de opcoesPregaoRotulo/opcoesFonteRotulo/opcoesConsultadoEmRotulo) —
    // divergir de tom aqui inventaria voz onde não há ação nem dinheiro.
    opcoesPasso1de2: "Passo 1 de 2",
    opcoesLeituraJaFeita: "leitura já feita",
    opcoesSetupsTitulo: "SETUPS GRAVADOS",
    opcoesPregaoRotulo: "Pregão",
    opcoesFonteRotulo: "Fonte",
    opcoesFrescorEmDia: "dado em dia",
    opcoesFrescorAtrasado: "dado atrasado",
    opcoesFrescorNaoMedido: "frescor não medido",
    // Fase 33 (33-02, D-04b): rótulo do carimbo de frescor dos dois blocos
    // cross-carteira ("descobrir oportunidades") — TODO fechado
    // (carimbo-frescor-blocos-cross-carteira.md). Mesmo tom neutro dos
    // vizinhos acima (Pregão/Fonte), que também são idênticos nos dois
    // modos.
    opcoesConsultadoEmRotulo: "Consultado",
    // Fase 27 (27-05) — a ÚNICA chamada da aba que ainda sai sem clique, dita
    // na tela. O frescor (`/status`) reserva 1 chamada e só a consome quando
    // precisa mesmo ir ao serviço; com o frescor em cache, o custo é zero. Ele
    // não vira botão porque um gate de frescor que só aparece depois de um
    // clique não protege ninguém (ADR-027, Decisão 8): o cabeçalho tem de
    // poder dizer a idade do dado desde o primeiro frame. Declarar é a
    // correção honesta; esconder seria a outra.
    opcoesCustoFrescor: "Abrir esta aba consulta o frescor do dado no serviço: consome até 1 chamada da sua cota do dia, e nenhuma quando o frescor já está em cache. É a única consulta desta tela que sai sem você pedir — todas as outras saem de um botão que diz o preço.",
    // Fase 39 (NAV-01, D-14): rótulo do ⓘ de bastidor da aba Montar — o
    // parágrafo de opcoesCustoFrescor sai do fluxo fixo e vira conteúdo desse
    // ⓘ (39-UI-SPEC.md); este rótulo é só o texto do botão que abre o
    // conteúdo, não substitui o parágrafo em si.
    opcoesCustoFrescorRotulo: "quanto esta aba consome da sua cota",
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
    // Fase 39 (NAV-01, D-07): título/fechar do sheet de Vigias (ícone+contador
    // no cabeçalho da aba, badge abre um bottom sheet reusando o mesmo bloco
    // "SEUS VIGIAS" de sempre) e o aria-label do próprio badge — navegação/
    // rótulo de controle, idêntico nos dois modos (mesmo padrão de
    // opcoesVoltarAoHub). Nunca afirma um número antes de medir (princípio 4
    // do CLAUDE.md): sem `medido`, o badge mostra só o ícone.
    opcoesVigiasSheetTitulo: "Seus vigias",
    opcoesVigiasFechar: "Fechar",
    opcoesVigiasAbrirSheet: (n) =>
      n === 1 ? "1 vigia — abrir" : n > 1 ? n + " vigias — abrir" : "Vigias — abrir",
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
    // Fase 39 (NAV-01, D-14): rótulo do ⓘ de bastidor da aba Montar para a
    // mecânica de lastro — mesmo padrão de opcoesCustoFrescorRotulo acima.
    opcoesLastroAjudaRotulo: "como o lastro é contado",
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
    // Fase 39 (NAV-01, D-06): link que expande SecaoComparar INLINE dentro de
    // Montar (nunca aba/sheet própria) — navegação, texto idêntico nos dois
    // modos (mesmo padrão de opcoesVoltarAoHub/opcoesAbaMontar). Alterna
    // conforme o estado de expansão (aria-expanded).
    opcoesVerOutrosVencimentos: "Ver outros vencimentos",
    opcoesOcultarOutrosVencimentos: "Ocultar outros vencimentos",
    // Fase 35 (35-01, D-06): marca neutra de resultado re-clicável — nunca
    // celebração, T.textMuted (par T.positive/T.negative é reservado para
    // direção financeira). Mesmo motivo de neutralidade de tom das duas
    // chaves de progresso acima: metadado, não ação nem dinheiro.
    opcoesEstruturaMontada: "Estrutura montada",
    opcoesPossibilidadesVistas: "Possibilidades carregadas",
    // Quick 260923-ndy (Task 2): linha fixa acima do botão de execução do
    // bloco `ExecutarProposta.jsx` — reforça, na hora do clique, que a
    // ordem é virtual (princípio 1/8 do CLAUDE.md). Sem linguagem de ganho.
    opcoesExecucaoSimulada: "Execução simulada com dinheiro virtual — nenhuma ordem vai para corretora ou bolsa.",
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

    // Fase 37 (37-02) — gráfico de payoff corrigido (CHART-01/02/03/05) e
    // camada explicativa determinística (EXPL-01/02/03). Chaves preparadas
    // para os Planos 37-04 (geometria do gráfico) e 37-05 (wiring) — nenhum
    // consumidor ainda nesta plano, por desenho (37-02-PLAN.md).
    opcoesEixoZeroRotulo: "R$ 0",
    opcoesEixoVerticalLoteAjuda: "Multiplique pelo lote para o valor total.",
    opcoesNoVencimentoTitulo: "No vencimento",
    opcoesHojeTitulo: "Hoje · valor de mercado",
    opcoesHojeAjuda: "Preço de mercado agora — pode mudar a qualquer momento, diferente do resultado no vencimento acima.",
    opcoesPerdaIlimitadaCurta: "sem piso",
    opcoesHojePrefixoEixo: "hoje",
    opcoesComoLerTitulo: "Como ler esta estrutura",
    // EXPL-01/02/03 — 11 templates de frase (segmento-posição × inclinação),
    // consumidos por `ExplicacaoPayoff.jsx`. Redação idêntica nos dois modos
    // (Estudo/Operador): o UI-SPEC (37-UI-SPEC.md §3) não pede variação de
    // voz para estas 11 chaves — só a citação da razão, que reusa
    // `formatarRazao`, tratada pelo componente, não pela chave de copy.
    opcoesExplicSpotPositiva: "Hoje, com o ativo em R$ {spot}, você está numa faixa de alta: se o preço subir, seu resultado melhora; se cair, piora.",
    opcoesExplicSpotNegativa: "Hoje, com o ativo em R$ {spot}, você está numa faixa de baixa: se o preço cair, seu resultado melhora; se subir, piora.",
    opcoesExplicSpotPlato: "Hoje, com o ativo em R$ {spot}, seu resultado está travado: dentro desta faixa, o preço subir ou cair não muda nada.",
    opcoesExplicSpotCaudaGanho: "Hoje, com o ativo em R$ {spot}, você está na faixa sem teto de ganho: quanto mais o preço subir, maior o resultado, sem limite declarado pelo serviço.",
    opcoesExplicSpotCaudaPerda: "Hoje, com o ativo em R$ {spot}, você está na faixa sem piso de perda: quanto mais o preço subir, maior a perda, sem limite declarado pelo serviço.",
    opcoesExplicOutroPositiva: "Entre R$ {de} e R$ {ate}, o resultado sobe conforme o preço do ativo sobe.",
    opcoesExplicOutroNegativa: "Entre R$ {de} e R$ {ate}, o resultado cai conforme o preço do ativo sobe.",
    opcoesExplicOutroPlato: "Entre R$ {de} e R$ {ate}, o resultado fica travado — não muda com o preço.",
    opcoesExplicOutroCaudaPlato: "Acima de R$ {de}, o resultado fica travado, mesmo que o preço continue subindo.",
    opcoesExplicOutroCaudaGanho: "Acima de R$ {de}, o ganho aumenta sem limite conforme o preço sobe.",
    opcoesExplicOutroCaudaPerda: "Acima de R$ {de}, a perda aumenta sem limite conforme o preço sobe.",

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

    // Fase 34 (34-01) — header fixo do workspace (D-05) + pill row de 3 abas
    // do workspace (D-02). "Voltar" fica curto de propósito: o botão mora
    // DENTRO do header, colado ao nome do ticker, mesmo verbo único que todo
    // botão de volta/cancelar deste diretório usa. As 3 abas são pills numa
    // linha a 375px — rótulo longo estoura a linha (UI-SPEC, Typography).
    opcoesVoltarAoHub: "Voltar",
    opcoesAbaAnalisar: "Analisar",
    opcoesAbaComparar: "Comparar",
    opcoesAbaSetupsSalvos: "Setups salvos",
    // Fase 39 (NAV-01, D-01): as 3 abas fixas de nível 1 que substituem
    // `subaba`/`abaWorkspace` — navegação, idêntica nos dois modos (mesmo
    // padrão de opcoesVoltarAoHub acima). `opcoesAbaAnalisar`/
    // `opcoesAbaComparar`/`opcoesAbaSetupsSalvos` acima NÃO são deletadas
    // (UI-SPEC, Copywriting Contract) — ficam retiradas de uso.
    opcoesAbaOportunidades: "Oportunidades",
    // Fase 39-06 (checkpoint humano, override deliberado de D-03): renomeada
    // de "Recomendadas" para "Destacadas" — decisão do Alex ao vivo, por
    // ambiguidade regulatória CVM do termo "recomendada/recomendação" ao
    // lado do disclaimer "nada aqui é recomendação de compra/venda". A
    // chave (`opcoesAbaRecomendadas`) e o id interno da aba (`"recomendadas"`
    // em OpcoesScreen.jsx) NÃO mudam — só o texto visível.
    opcoesAbaRecomendadas: "Destacadas",
    opcoesAbaMontar: "Montar",
    // Fase 39 (NAV-01, D-04): eyebrow interno da aba Montar e o link de
    // "montar outra estrutura" quando já há um ativo escolhido — voz de
    // professor, mais longa que a voz de mesa (ver ramo Operador).
    opcoesMontarTitulo: "MONTAR UMA ESTRUTURA",
    opcoesMontarNoAtivo: (t) => "Montar outra estrutura com " + t,
    // Fase 35 (35-01, D-01/D-08): rótulo do estágio 2 (o carril de pills) e
    // a linha de transição que aparece quando a leitura já foi feita. Nunca
    // numera Analisar/Comparar entre si (princípio 5 do CLAUDE.md) — o
    // Kicker nomeia o JOB do estágio, não uma posição de sequência.
    opcoesEscolhaTitulo: "O QUE FAZER",
    opcoesPasso2de2: "Passo 2 de 2",
    // Fase 39 (NAV-01, D-01/D-06): reescrita — a pill row Analisar/Comparar
    // deixa de existir (D-01), "comparar" agora é o link "ver outros
    // vencimentos" dentro de Montar (D-06).
    opcoesLeituraConcluidaAjuda: "Leitura concluída — monte a estrutura abaixo. Para comparar vencimentos, use o link logo depois dela.",

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
    // Quick 261006-dvf (2026-10-06): espelho byte a byte de skill_ref.RETORNO_ACUMULADO.
    retornoAcumulado: {
      carimbada: "Desde o capital inicial desta simulação, o retorno acumulado é de {pct}.",
      carimbada_reinicio: "Desde {desde}, quando o capital da simulação foi alterado, o retorno acumulado é de {pct}. Aporte ou retirada não conta como retorno.",
      primeiro_registro: "Desde {desde}, o primeiro dia registrado, o retorno acumulado é de {pct}. O capital inicial desta série não foi registrado, por isso a conta parte desse dia.",
      sem_serie: "Não há dados suficientes para concluir. Ainda não há nenhum dia de patrimônio registrado nesta simulação.",
      inconsistente: "Não há dados suficientes para concluir. A série de patrimônio registra bases diferentes sem um ajuste de capital que as explique.",
    },
    // Quick 261006-qre (2026-10-06): espelho byte a byte de skill_ref.CURVA_EVOLUCAO.
    curvaEvolucao: {
      antes_da_base: "Antes de {desde} a linha fica pontilhada: mostra só o patrimônio registrado, porque o retorno acumulado só é medido a partir desse dia.",
    },
    // Fase 43 (HIER-03): espelho byte a byte de
    // skill_ref.RECONCILIACAO_ELEGIBILIDADE (modo "educacional") — placeholders
    // literais, interpolação é do helper reconciliacaoTxt.
    reconciliacaoElegibilidade: {
      elegivel: "O padrão bateu os critérios, e em {n} ocorrências na janela {janela} houve vantagem medida.",
      inelegivel: "O padrão bateu os critérios, mas em {n} ocorrências na janela {janela} não houve vantagem medida.",
      insuficiente: "O padrão bateu os critérios; só {n} ocorrências — pouco para medir.",
      nunca_medido: "O padrão bateu os critérios; ainda sem histórico medido.",
      aposentado: "Padrão identificado; sem vantagem medida em 15 anos (ADR-016).",
    },
    // Fase 42 (D-01/D-07/D-09/D-15): fatos do motor, idênticos nos dois
    // modos — microtexto por modo é HIER-03 (Fase 43).
    sinal: {
      alinhamento: { a_favor: "a favor da tendência", contra: "contra a tendência" },
      anelLado: { alta: "padrão de compra", baixa: "padrão de venda" },
      fundamentoNaoDirecao: "fundamento indica qualidade da empresa, não direção",
      degradadoSufixo: "·SMA50",
      degradadoAria: "base degradada SMA50",
      ariaRegime: (valor, alinhamentoTxt, degradado) =>
        "Regime: " + String(valor).toLowerCase() +
        (degradado ? " (base degradada SMA50)" : "") +
        (alinhamentoTxt ? ", " + alinhamentoTxt : ""),
      ariaFundamento: (score) => "Fundamento: qualidade " + score + " (não indica direção)",
      ariaAnel: (texto) => "Confluência " + texto,
      ariaManchete: (kicker, decisao) => kicker + ": " + decisao,
      // Fase 43 (CHIP-03, D-02): rótulos da Leitura da IA — fatos de seção,
      // idênticos nos dois modos; recomendação da IA NÃO tem rótulo aqui (D-03).
      leituraIa: {
        rotulo: "LEITURA DA IA",
        campos: { direcao: "DIREÇÃO", conviccao: "CONVICÇÃO", qualidade: "QUALIDADE" },
        aria: (chave, valor) =>
          ({ direcao: "Direção", conviccao: "Convicção", qualidade: "Qualidade" })[chave] +
          " da leitura da IA: " + valor,
      },
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

    // Fase 38 (38-04, KB-01): rótulos de interface da tela de Glossário
    // (Perfil → Glossário) — são rótulo de tile/campo/estado, não voz de
    // modo, por isso texto idêntico nos dois blocos (mesmo padrão de
    // concentracaoLink acima).
    glossarioSub: (n) => (n ? n + " termos" : "Termos") + " de indicadores, estruturas e mecânica da B3 — busque ou navegue por categoria",
    glossarioBuscaPlaceholder: "Buscar um termo (ex.: RSI, stop, IPO...)",
    glossarioBuscaRotulo: "Buscar no glossário",
    glossarioLimpar: "Limpar busca",
    glossarioVazio: (termo) => `Nenhum verbete encontrado para "${termo}".`,
    glossarioErro: "Não consegui carregar o glossário agora. Toque para tentar de novo.",

    // Fase 38 (38-05, KB-02): link "saiba mais" fixo por aba (Acompanhar/
    // Radar/Watchlist/Opções, ver ANCORAS_KB em glossario.js). Rótulo
    // genérico idêntico nos dois modos (mesmo padrão de concentracaoLink
    // acima) — NÃO reusar concentracaoLink, que pertence ao alerta de
    // concentração e fica intocado.
    saibaMais: "saiba mais",
    // Fase 39 (NAV-01, D-13): o ⓘ contextual por aba reusa `saibaMais` como
    // texto visível, mas precisa de um aria-label composto — 3 botões iguais
    // dizendo só "saiba mais" seriam indistinguíveis num leitor de tela.
    opcoesSaibaMaisAria: (aba) => "O que é uma opção — " + aba,

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
    // Reversão deliberada (Fase 45, D-11/discretion "usar collar"): a âncora legada do vocabulário de collar (Fase 8) saiu da voz visível.
    eyebrowPropostaCollar: "ESTUDO · COLLAR",
    collarPernasLinha: (n, ticker, strikeCall, strikePut) => `${n}× COLLAR ${ticker} · call ${strikeCall} / put ${strikePut}`,
    ctaCollarDebito: () => "Ver como este collar funcionaria",
    ctaCollarCredito: () => "Ver como este collar funcionaria",
    confirmAbrirCollar: () => "", // ramo estudo nunca chama window.confirm — chave existe só pela paridade

    // Fase 14 (Plano 07): trava de lastro visível na Carteira. Ramo Estudo
    // evita "vender"/"comprar" — "recomprada" (adjetivo) não contém o
    // infinitivo "comprar" como substring, por isso é a forma usada aqui
    // (guardião test_copy_theme.mjs testa substring, não palavra inteira).
    badgeTravada: (qty) => `${qty} travada(s) · lastro da call coberta`,
    avisoTravaNaVenda: (qty) => `${qty} ação(ões) está(ão) travada(s) como lastro de uma call coberta — volta(m) a ficar disponível(is) quando a call for recomprada ou vencer.`,

    // Fase 45 — rótulos neutros do card estruturado; guardião de igualdade Estudo=Operador
    // (test_estrutura_card_espelho.mjs). Idênticos nos dois modos de propósito.
    estruturaResultadoRotulo: "RESULTADO DA ESTRUTURA",
    estruturaResultadoSoAcoesRotulo: "SÓ AS AÇÕES — PRÊMIOS INDISPONÍVEIS",
    estruturaAcoesRotulo: "Ações",
    estruturaOpcoesRotulo: "Opções",
    estruturaFaixaTitulo: "FAIXA NO VENCIMENTO",
    estruturaPernasTitulo: "PERNAS",
    estruturaLegenda: { piso: "PISO", pm: "PM", hoje: "HOJE", teto: "TETO", stop: "STOP", alvo: "ALVO" },
    semPiso: "sem piso",
    semTeto: "sem teto",
    ladoVendida: "vendida",
    ladoComprada: "comprada",
    semCotacaoPerna: "sem cotação",
    chipVence: (ddmm, dias) => `vence ${ddmm} · ${dias} dia(s)`,
    chipVenceHoje: "vence hoje",
    chipVencida: (ddmm) => `vencida em ${ddmm}`,
    // Reversão deliberada Fase 45 (decisão do Alex): o destino só recompra a call; o rótulo promete apenas navegar.
    btnEncerrarEstrutura: "Encerrar opção em Opções",
    btnAtualizarEstrutura: "Atualizar",
    fonteEstruturaLinha: (fonte, quando) => `Opções lidas de ${fonte} em ${quando}`,
    fonteEstruturaSemDado: "Fonte das opções não declarada.",
    estruturaFaixaAria: (nome, textos, hoje, pm) => `${nome}. ${textos} Hoje R$ ${hoje}. Preço médio R$ ${pm}.`,
    encerrarAria: (t) => `Ver encerramento de ${t}: abre a aba Opções em ${t}`,
    // Fase 45 (code review WR-04): motivo neutro quando o motor não trouxe o texto do bloqueio.
    encerrarSemMotivo: "Encerramento indisponível: não há dados suficientes para concluir.",
    estruturaGrupoAria: "Estrutura de opções",
    estruturaPernaLinha: (tipo, lado, strike, ddmm) => `${tipo} ${lado} · strike ${strike} · vence ${ddmm}`,
    estruturaPremioLinha: (entrada, atual) => `prêmio R$ ${entrada} → R$ ${atual}`,
    estruturaQtdPerna: (q) => `×${q}`,
    // Fase 45 (code review WR-03): fallbacks neutros para campo parcial do motor.
    semPremioPerna: "prêmio —",
    estruturaPremioSoAtual: (atual) => `prêmio atual R$ ${atual}`,
    estruturaLivresLinha: (livres, qty) => `${livres}/${qty} livres (lastro da call)`,
    estruturaSaidaSemLastro: "sem lastro",
    estruturaVerHistorico: "Ver no histórico de operações →",

    // Fase 14 (Plano 07, T-14-27/T-14-28): liquidação forçada por vencimento
    // (estado do sistema, texto verbatim do UI-SPEC) e ressalva de marcação
    // do patrimônio com pernas lastreadas — mesmo texto nos dois modos
    // (system notice, não voz de professor/mesa; mesmo padrão de
    // verCadeiaCompleta/propostaIndisponivelDegradada acima).
    avisoLiquidacaoForcada: (ticker, valor) => valor === 0
      ? `Esta call de ${ticker} venceu fora do dinheiro — expirou sem valor, o prêmio integral ficou com quem estava do outro lado da operação, e o lastro foi liberado.`
      : `Esta call de ${ticker} venceu dentro do dinheiro e não foi fechada a tempo — liquidada em dinheiro pelo valor intrínseco (R$ ${valor}). Sua posição em ações não foi alterada.`,
    // 2026-10-06 (quick 261006-bwv): "lastreadas" -> "em aberto" — a linha agora
    // cobre também a perna avulsa (buy_option). Chave só do front.
    linhaPatrimonioOpcoes: "opções em aberto (marcadas pelo prêmio de abertura — sem cotação ao vivo)",

    // Fase 18 (Plano 01, NAV-01/NAV-03): tira "Oportunidades de opções" em
    // Posições (agregado, todas as posições) e afordância de detalhe dentro
    // do card de uma posição específica. Rótulo de seção e micro-rótulo de
    // ação são IDÊNTICOS nos dois modos (mesmo precedente de payoffTitulo/
    // verCadeiaCompleta acima); os estados de carregamento/vazio e a
    // afordância da posição têm voz de modo. Nenhuma destas seis chaves
    // pode conter a manchete do motor nem frase que a substitua — a
    // manchete continua vindo só de proposta.manchete (guardrail CVM).
    //
    // Fase 32 (32-01, D-01/D-03/D-05): título REESCRITO — antes era
    // "OPORTUNIDADES DE OPÇÕES" nos dois modos, igual ao título do bloco de
    // curadoria (Bloco B, abaixo). Os dois blocos cross-carteira passam a
    // conviver na mesma tela (topo da sub-aba Setups), então o título
    // sozinho não basta mais para dizer qual motor é qual — agora NOMEIA o
    // motor (LEITURA TÉCNICA = o motor COM gate). `tiraOpcoesSubtitulo`
    // (chave nova) reforça a mesma distinção em prosa.
    tiraOpcoesTitulo: "OPORTUNIDADES CONFIRMADAS PELA LEITURA TÉCNICA",
    tiraOpcoesSubtitulo: "Só aparecem aqui as posições em que a leitura técnica do próprio ativo confirma a estrutura agora — o mesmo motor que decide o gatilho do Radar.",
    tiraOpcoesVerDetalhe: "ver detalhe",
    tiraOpcoesCarregando: "Procurando estruturas possíveis nas suas posições…",
    // Quick 260928-u0h (2026-09-28): tiraOpcoesSemCobertura/SemSetup/SemMercado sem consumidor em
    // componente desde esta quick — mantidas (guardiões de paridade as travam); remoção é decisão separada.
    tiraOpcoesSemCobertura: "Nenhuma das suas posições tem opção com liquidez suficiente hoje — sem contrato líquido, não dá para estudar uma estrutura sobre ela.",
    tiraOpcoesSemSetup: "Suas posições têm opção líquida, mas a leitura técnica não indica nenhuma estrutura agora. A cadeia completa continua disponível em cada ativo.",
    // Quick 260908-ldg (D-07): terceiro caso do estado vazio — a diferença
    // para `tiraOpcoesSemCobertura` é NOMEAR a faixa, em vez de "sem
    // liquidez suficiente" genérico. Voz de professor: descreve a condição.
    tiraOpcoesSemMercado: "As opções das suas posições estão hoje na faixa SEM MERCADO — negociaram tão pouco que o preço da tela não seria o preço real de uma ordem. Por isso nenhuma estrutura é estudada sobre elas agora.",
    // Quick 260928-u0h (2026-09-28): encerramento não passa pela leitura técnica (main.py, ramo
    // `pos_op_aberta` -> proposta_fechar), por isso ganha seção própria. As frases de motivo moram
    // AQUI e não em skill_ref porque `motivoTexto` do backend colapsa sem_contrato_liquido e
    // sem_vencimento_elegivel na frase de sem_setup (falsa para eles).
    tiraOpcoesAbertasTitulo: "SUAS ESTRUTURAS ABERTAS",
    tiraOpcoesAbertasSubtitulo: "Estruturas que você já montou sobre suas ações. A proposta aqui é de encerramento do mesmo contrato — ela não passa pela leitura técnica, só pela cotação atual da opção.",
    tiraOpcoesNenhumaNova: "Nenhuma estrutura nova confirmada pela leitura técnica agora.",
    tiraOpcoesMotivosTitulo: "POR QUE AS OUTRAS POSIÇÕES NÃO APARECEM",
    tiraOpcoesMotivo: {
      sem_setup: "A leitura técnica deste ativo não pede venda coberta nem put de proteção agora — em alta, a venda da call travaria o movimento lido e a put pagaria uma proteção que a leitura não pede; sem leitura conclusiva, nada é proposto.",
      sem_lastro: "Não há um lote livre de 100 ações deste ativo na carteira — venda coberta e put de proteção precisam de pelo menos 100 ações que ainda não estejam comprometidas com outra estrutura.",
      sem_vencimento_elegivel: "Nenhum vencimento futuro de opção deste ativo foi lido. Sem vencimento futuro, nenhuma estrutura é montada.",
      sem_contrato_liquido: "Existe cadeia de opções, mas nenhum contrato no strike e no vencimento que a estrutura pede negocia o bastante para ter um preço confiável.",
      caixa_insuficiente: "O dinheiro virtual disponível não cobre o prêmio da put de proteção, e o collar também não coube no caixa. Nenhuma estrutura é estudada sem caixa para pagá-la.",
      degradado: "A cotação de opções deste ativo veio degradada ou incompleta. Sem dado confiável, nenhuma estrutura é estudada — nada é estimado no lugar.",
      sem_mercado: "As opções deste ativo estão na faixa SEM MERCADO — negociaram tão pouco que o preço da tela não seria o preço real de uma ordem.",
      sem_liquidez: "As opções deste ativo não têm liquidez suficiente hoje para sustentar o estudo de uma estrutura.",
      indisponivel: "Não foi possível consultar as opções deste ativo agora. Nada é mostrado no lugar do dado que faltou.",
      aberta_sem_proposta: "Há uma estrutura aberta neste ativo, mas a proposta de encerramento não pôde ser montada agora (opção sem liquidez ou cotação indisponível). A posição continua aberta na sua carteira.",
      desconhecido: "Nenhuma estrutura para este ativo agora, e o motivo não veio identificado. Não há dados suficientes para concluir.",
    },
    // Fase 44 (ESTR-06): espelho byte a byte de skill_ref.ESTRUTURA_POSICAO / OPCOES_LASTREADAS —
    // guardião web/tests/test_estrutura_espelho.mjs; texto novo nasce no .py primeiro.
    estruturaPosicao: {
      nome_call_coberta: "call coberta",
      nome_put_protecao: "put de proteção",
      nome_collar: "collar",
      nome_fora_da_biblioteca: "Estrutura fora das três que o simulador lê (call coberta, put de proteção e collar). As pernas aparecem abaixo, sem faixa calculada.",
      estado_vigente: "Estrutura vigente: faltam {dias} dia(s) para o vencimento de {vencimento}.",
      estado_vigente_sem_data: "Vencimento não informado para esta estrutura. Não há dados suficientes para concluir o prazo.",
      estado_perto_vencimento: "Faltam {dias} dia(s) para o vencimento de {vencimento}. Perto do vencimento o prêmio muda rápido, e a estrutura pede uma decisão: encerrar ou deixar vencer.",
      estado_exercicio_provavel: "A opção de strike R$ {strike} está dentro do dinheiro com a ação a R$ {spot}. Se o vencimento fosse hoje, ela seria exercida.",
      estado_premio_indisponivel: "Sem cotação para {pernas} agora. O resultado total não é calculado e nada é estimado no lugar.",
      estado_vencida: "O vencimento de {vencimento} já passou. Esta estrutura não está mais vigente.",
      aberta_sem_proposta: "A estrutura continua aberta na sua carteira, mas o encerramento não pode ser proposto agora. {motivo}",
      faixa_piso: "Piso no vencimento: abaixo de R$ {piso}, a put protege as {qtd} ações — a perda máxima fica em R$ {perdaMaxima}.",
      faixa_teto: "Teto no vencimento: acima de R$ {teto}, a call vendida limita o ganho das {qtd} ações a R$ {ganhoMaximo}.",
      faixa_sem_piso: "Sem piso: a call coberta não protege contra queda. Se a ação fosse a zero, a perda seria de R$ {perdaMaxima}.",
      faixa_sem_teto: "Sem teto: a put de proteção não limita o ganho das ações se o preço subir.",
      faixa_teto_parcial: "Teto parcial: a call vendida (strike R$ {teto}) limita o ganho de {qtd} das {qtdBase} ações. O ganho das demais não tem limite se o preço subir.",
      faixa_piso_sem_perda: "Piso no vencimento: abaixo de R$ {piso}, a put protege {qtd} ações. Não há dados suficientes para concluir a perda máxima.",
      faixa_vencimentos_diferentes: "As pernas vencem em datas diferentes ({vencimentos}). Sem uma data comum, a faixa no vencimento não pode ser calculada — nada é aproximado.",
      faixa_perna_sem_lastro: "Há {quantidade} call(s) vendida(s) sem ações para cobrir. Nesse trecho a perda não tem limite, por isso a faixa não é calculada.",
      faixa_sem_acoes: "Não há ações de {ticker} na carteira: as pernas aparecem abaixo, mas não há faixa de estrutura a calcular.",
      faixa_dados_insuficientes: "Não há dados suficientes para concluir a faixa no vencimento.",
      descoberta_put: "{quantidade} put(s) protegem mais ações do que você tem. A faixa considera só a parte coberta ({qtdBase} ações).",
      stop_protegida: "A put de strike R$ {piso} limita a perda desta posição no vencimento — o limite vem dela, não de um stop de preço.",
      resultado_incompleto: "Resultado total indisponível: falta cotação de {pernas}. Aparecem separados só o resultado das ações e o das pernas cotadas.",
      acao_sem_cotacao: "Sem cotação da ação agora: o resultado das ações e o total não são calculados.",
      resultado_dados_invalidos: "Resultado total indisponível: os dados de {pernas} estão incompletos ou inválidos (lado, quantidade ou prêmio de entrada). Nada é estimado no lugar.",
      encerrar_premio_indisponivel: "Encerrar fica bloqueado: sem prêmio cotado para {pernas}, não há preço para o simulador usar.",
      encerrar_vencida: "Encerrar não se aplica: o vencimento de {vencimento} já passou.",
      origem_last: "Prêmio de {perna} pelo último negócio: não há oferta no lado que fecha a posição.",
    },
    opcoesLastreadasMotivo: {
      sem_lastro: "Sem posição em {ticker} na carteira — venda coberta e put de proteção exigem uma posição real do ativo-lastro.",
      sem_setup: "A leitura técnica de {ticker} não indica venda coberta nem put de proteção agora. A cadeia completa continua disponível abaixo.",
      degradado: "Proposta indisponível — cotação de opções degradada.",
      caixa_insuficiente: "Caixa insuficiente para o prêmio desta put de proteção.",
      sem_contrato_liquido: "Existe cadeia de opções de {ticker}, mas nenhum contrato no strike e no vencimento que a estrutura pede negocia o bastante para ter um preço confiável.",
      sem_vencimento_elegivel: "Nenhum vencimento futuro de opção de {ticker} foi lido — sem vencimento futuro, nenhuma estrutura nova é montada.",
      premio_indisponivel: "Sem prêmio cotado para a opção aberta de {ticker} agora — o encerramento não é proposto sem preço, e nada é estimado no lugar.",
      contrato_fora_da_cadeia: "O contrato aberto de {ticker} não veio na cadeia de opções consultada agora — sem ele, o encerramento não é proposto.",
      sem_mercado: "As opções abertas de {ticker} estão na faixa SEM MERCADO — o preço da tela não seria o preço real de uma ordem.",
    },
    // Fase 45 (CARD-01/04/05/06): espelho byte a byte de skill_ref.ESTRUTURA_CARD.
    // Texto novo nasce no .py primeiro; guardião test_estrutura_card_espelho.mjs.
    estruturaCard: {
      chip_estrutura: "ESTUDO · {nome}",
      chip_estrutura_generica: "ESTUDO · OPÇÕES",
      lendo: "Lendo a estrutura de opções desta posição…",
      indisponivel: "Não foi possível ler a estrutura de opções agora. As pernas abertas continuam na sua carteira, e nenhum valor é estimado no lugar.",
      badge_travada_collar: "{qty} travada(s) · lastro da call do collar",
      aviso_sem_stop: "Esta posição não tem stop definido. Defina em Editar stop/alvo ou peça a sugestão da IA.",
    },
    // Fase 48 (2026-10-05): espelho byte a byte de skill_ref.OPCOES_ESCADA.
    // Texto novo nasce no .py primeiro; guardião test_opcoes_escada_espelho.mjs.
    opcoesEscada: {
      objetivo_proteger_titulo: "Proteger de queda",
      objetivo_proteger_desc: "Você paga um prêmio. Se a ação cair abaixo do piso, a perda para ali. Em termos técnicos, uma put protetora.",
      objetivo_proteger_perde: "Perde: o prêmio, se a ação não cair",
      objetivo_renda_titulo: "Gerar renda",
      objetivo_renda_desc: "Você recebe um prêmio. Em troca, limita o ganho acima de um teto. Em termos técnicos, uma venda coberta, que trava as ações como lastro.",
      objetivo_renda_perde: "Perde: ganho acima do teto",
      objetivo_collar_titulo: "Proteger com custo baixo",
      objetivo_collar_desc: "O prêmio recebido paga (quase) o da proteção. Perda e ganho ficam entre o piso e o teto. Em termos técnicos, um collar.",
      objetivo_collar_perde: "Perde: ganho acima do teto",
      objetivo_indisponivel: "{objetivo} indisponível: {motivo}.",
      lastro_insuficiente: "só {livres} ações livres; esta estrutura precisa de {necessarias}",
      lastro_travado: "ações travadas em outra call",
      pergunta_objetivo: "O que você quer fazer com as {qtd} ações?",
      pergunta_objetivo_sub: "Você vê o pior caso e o gráfico antes de decidir. Termos sublinhados abrem uma explicação.",
      montar_do_zero: "Montar do zero",
      secao_proteger: "Escolha o piso",
      secao_renda: "Escolha o teto",
      secao_collar: "Escolha o piso e o teto",
      acao_a: "ação a R$ {preco}",
      degrau_proteger_0: "Mais protegido",
      degrau_proteger_1: "Equilibrado",
      degrau_proteger_2: "Mais barato",
      degrau_renda_0: "Mais renda",
      degrau_renda_1: "Equilibrado",
      degrau_renda_2: "Mais espaço para subir",
      degrau_collar_0: "Mais protegido",
      degrau_collar_1: "Equilibrado",
      degrau_collar_2: "Mais barato",
      degrau_ausente: "Sem estrutura neste degrau: {motivo}",
      vencimento_dias: "{dias} dias",
      vencimento_dia: "{dias} dia",
      col_perda_maxima: "Perda máxima",
      col_custo_protecao: "Custo da proteção",
      col_ganho_maximo: "Ganho máximo",
      col_premio_recebido: "Prêmio recebido",
      col_liquido_custa: "Custa no líquido",
      col_liquido_recebe: "Recebe no líquido",
      nota_sem_piso: "sem piso: a queda não é limitada",
      nota_ganho_negativo: "se exercida: perda",
      risco_pior: "Pior caso: perde até R$ {perdaTotal} nas {qtd} ações (R$ {perdaAcao} por ação), por mais que a ação caia abaixo do piso de R$ {piso}.",
      risco_pior_sem_piso: "Pior caso: sem piso, se a ação for a zero você perde R$ {perdaTotal}; a queda segue a da ação, amortecida só pelo prêmio de R$ {premio}.",
      risco_melhor: "Melhor caso: ganha até R$ {ganhoTotal} nas {qtd} ações (R$ {ganhoAcao} por ação), se a ação fechar acima do teto de R$ {teto}.",
      risco_melhor_sem_teto: "Melhor caso: sem teto, você ganha o que a ação subir, menos o prêmio pago.",
      risco_equilibrio: "Equilíbrio: a ação precisa fechar a R$ {be} no vencimento {venc}.",
      risco_sem_equilibrio: "Equilíbrio: não há dados suficientes para concluir.",
      grafico_titulo: "Resultado no vencimento",
      grafico_subtitulo: "linha cheia = com a estrutura · tracejada = só as ações",
      unidade_total: "Total ({qtd} ações)",
      unidade_acao: "Por ação",
      linha_so_acoes: "Só as ações",
      linha_com_estrutura: "Com a estrutura",
      linha_preco_medio: "preço médio",
      marcador_piso: "piso",
      marcador_equilibrio: "equilíbrio",
      marcador_teto: "teto",
      marcador_perda_maxima: "perda máxima",
      marcador_ganho_maximo: "ganho máximo",
      legenda_piso: "Piso: R$ {preco}. Abaixo dele, a perda por ação para de crescer.",
      legenda_equilibrio: "Equilíbrio: R$ {preco}. Nesse preço no vencimento, o resultado é zero.",
      legenda_teto: "Teto: R$ {preco}. Acima dele, o ganho por ação para de crescer.",
      legenda_perda_maxima: "Perda máxima: R$ {valor}. É o pior resultado possível no vencimento.",
      legenda_ganho_maximo: "Ganho máximo: R$ {valor}. É o melhor resultado possível no vencimento.",
      ausente_piso: "Sem piso nesta estrutura: a queda não é limitada.",
      ausente_teto: "Sem teto nesta estrutura: o ganho acompanha a alta, menos o prêmio.",
      ausente_ganho_maximo: "Sem ganho máximo nesta estrutura: o ganho acompanha a alta da ação.",
      grafico_aria: "Gráfico do resultado de {ticker} no vencimento {venc}, em {unidade}. Pior caso: {pior}. Melhor caso: {melhor}. Equilíbrio: {be}.",
      sem_grafico: "Sem gráfico para esta estrutura: {motivo}",
      ese_pergunta: "E se a {ticker} fechar a R$ {preco} no vencimento?",
      ese_melhora: "Neste preço, a estrutura melhora o resultado em R$ {d}.",
      ese_reduz: "Neste preço, a estrutura reduz o resultado em R$ {d}.",
      ese_igual: "Neste preço, a estrutura não muda o resultado.",
      tabela_ver: "Ver os números",
      tabela_preco: "Preço no vencimento",
      tabela_so_acoes: "Só as ações",
      tabela_com_estrutura: "Com a estrutura",
      comparar_rotulo: "Comparar vencimentos",
      comparar_custo: "até {n} consultas (2×{k}+1) · restam {x} hoje",
      cota_esgotada: "Cota de consultas do dia esgotada. Renova {quando}. A explicação acima continua valendo.",
      consultando: "consultando…",
      matriz_sem_dado: "—",
      matriz_so_comparacao: "Este vencimento está aqui para comparar: a execução simulada usa os vencimentos {lista}.",
      matriz_pior: "pior caso",
      matriz_ganho: "ganho máx.",
      sem_estrutura: "Sem estrutura disponível para {ticker} neste vencimento",
      sem_estrutura_dica: "Tente outro vencimento ou monte do zero.",
      // Fase 48 gap G-01/G-02 (2026-10-05): namespace OPCOES_ESCADA; não colide com sem_vencimento_elegivel da Fase 44 em OPCOES_LASTREADAS.
      sem_vencimento_elegivel: "Nenhum vencimento futuro lido para {ticker} ({vencimentos}): o que vence hoje ou já venceu não é negociável. Sem vencimento futuro, nenhuma estrutura guiada é montada.",
      sem_vencimento_elegivel_dica: "Quando houver um vencimento futuro, os objetivos voltam. Para estudar outro vencimento agora, use Montar do zero.",
      objetivo_indisponivel_ver_motivo: "{objetivo} indisponível pelo motivo acima.",
      pernas_titulo: "Suas pernas abertas",
      pernas_linha: "{tipo} {lado} · strike R$ {strike} · vence {vencimento} · {qtd} opções",
      pernas_premio: "Prêmio de entrada R$ {entrada} · agora R$ {atual}",
      pernas_resultado: "Resultado: {valor}",
      perna_lado_compra: "comprada",
      perna_lado_venda: "vendida",
      pernas_carregando: "Lendo o resultado das pernas…",
      pernas_encerrar: "Encerrar",
      pernas_encerrar_aria: "Encerrar a perna {id}",
      pernas_confirmar: "Encerrar {id}? A venda é simulada pelo último prêmio da fonte. Nenhuma ordem real é enviada.",
      pernas_confirmar_sim: "Confirmar encerramento",
      pernas_cancelar: "Cancelar",
      pernas_encerrando: "Encerrando…",
      pernas_na_estrutura: "Esta perna faz parte de uma estrutura com lastro: encerre pelo painel da estrutura.",
      pernas_vendida_sem_acao: "Perna vendida: a recompra não é feita nesta lista.",
      // Fase 49 (2026-10-06): espelho de skill_ref.OPCOES_ESCADA anat_*.
      anat_titulo_posicao: "Sua posição em {ticker}",
      anat_sub_posicao: "Veja o que cada perna faz antes de decidir. Mexa no preço para testar hipóteses: não é previsão.",
      anat_total_titulo: "Resultado no vencimento ({vencimento})",
      anat_total_titulo_sem_data: "Resultado no vencimento",
      anat_chips_aria: "Pernas incluídas no gráfico",
      anat_chip_perna: "{tipo} {strike}",
      anat_chip_acoes: "{qtd} ações",
      anat_slider_rotulo: "Se {ticker} estiver a R$ {preco} no vencimento (hipótese sua, não previsão)",
      anat_leitura_total: "Em R$ {preco} no vencimento, o que está marcado soma {valor}.",
      anat_leitura_com_sem: "Em R$ {preco} no vencimento: com a perna {id} o resultado é {com}; sem ela, {sem}. Ela contribui com {contrib}.",
      anat_sem_esta_vazio: "Sem a perna {id}, nada fica marcado no gráfico.",
      anat_acoes_dentro: "Inclui as {qtd} ações de {ticker} pelo preço médio de R$ {pm}, registrado no simulador.",
      anat_acoes_fora_sem_pm: "As {qtd} ações de {ticker} ficam fora do gráfico: o simulador não tem o preço médio delas. Nada foi estimado.",
      anat_total_vencimentos_diferentes: "Não há dados suficientes para concluir. As pernas marcadas vencem em datas diferentes ({vencimentos}), então não existe um único resultado no vencimento. Cada perna segue com o seu quadro.",
      anat_total_sem_data: "Não há dados suficientes para concluir. Uma das pernas marcadas não tem data de vencimento no simulador, então não dá para afirmar que vencem juntas nem montar um único resultado no vencimento. Cada perna segue com o seu quadro.",
      anat_total_vazio: "Nada marcado. Ligue ao menos uma perna para ver o resultado.",
      anat_total_aria: "Curva do resultado total no vencimento por preço de {ticker}, somando {n} perna(s){acoes}. A tabela abaixo traz os valores.",
      anat_total_aria_acoes: " e as {qtd} ações",
      anat_pernas_titulo: "Suas pernas",
      anat_objetivos_titulo: "O que você quer fazer com a posição?",
      anat_frase_call_compra: "Você pagou R$ {valor} (R$ {premio} × {qtd}) pelo direito de comprar {qtd} {ticker} a R$ {strike} cada, até {vencimento}. Se não valer a pena exercer, o máximo que você perde é o que pagou.",
      anat_frase_put_compra: "Você pagou R$ {valor} (R$ {premio} × {qtd}) pelo direito de vender {qtd} {ticker} a R$ {strike} cada, até {vencimento}. Se não valer a pena exercer, o máximo que você perde é o que pagou.",
      anat_frase_call_venda: "Você recebeu R$ {valor} (R$ {premio} × {qtd}) e assumiu a obrigação de vender {qtd} {ticker} a R$ {strike} cada, se a opção for exercida até {vencimento}.",
      anat_frase_put_venda: "Você recebeu R$ {valor} (R$ {premio} × {qtd}) e assumiu a obrigação de comprar {qtd} {ticker} a R$ {strike} cada, se a opção for exercida até {vencimento}.",
      anat_cond_call_compra: "Fica no positivo se {ticker} passar de R$ {equilibrio} no vencimento.",
      anat_cond_put_compra: "Fica no positivo se {ticker} cair abaixo de R$ {equilibrio} no vencimento.",
      anat_cond_call_venda: "Fica no positivo enquanto {ticker} não passar de R$ {equilibrio} no vencimento.",
      anat_cond_put_venda: "Fica no positivo enquanto {ticker} não cair abaixo de R$ {equilibrio} no vencimento.",
      anat_prazo_dias: "vence em {dias} dias ({vencimento})",
      anat_prazo_amanha: "vence amanhã ({vencimento})",
      anat_prazo_hoje: "vence hoje ({vencimento})",
      anat_prazo_vencida: "venceu em {vencimento}",
      anat_prazo_sem_data: "Prazo: — (o simulador não tem a data de vencimento desta perna)",
      anat_rotulo_pior: "Pior caso",
      anat_rotulo_equilibrio: "Equilíbrio",
      anat_rotulo_hoje: "Hoje",
      anat_pior_ilimitado: "sem limite",
      anat_pior_ilimitado_nota: "Se {ticker} subir sem parar, a perda desta perna cresce junto: não existe um pior caso fixo.",
      anat_sem_cotacao_chip: "Sem cotação",
      anat_hoje_fonte_indisponivel: "Valor de hoje indisponível: a fonte de opções não respondeu. Nada foi estimado.",
      anat_hoje_fora_da_cadeia: "Valor de hoje indisponível: este contrato não veio na cadeia lida da fonte. Nada foi estimado.",
      anat_hoje_sem_negocio: "Valor de hoje indisponível: o contrato está na cadeia, mas sem preço de compra, de venda ou último negócio. Nada foi estimado.",
      anat_hoje_sem_cotacao: "Valor de hoje indisponível: sem cotação deste contrato agora. Nada foi estimado.",
      anat_hoje_sem_estrutura: "Valor de hoje indisponível: a leitura de cotação desta posição não respondeu. Nada foi estimado.",
      anat_hoje_nota: "O quadro de vencimento não depende de cotação; só o valor de hoje depende.",
      anat_ver_sem_esta: "Ver o que muda sem esta perna",
      anat_ver_total: "Voltar ao total",
      anat_ver_tabela: "Ver em tabela",
      anat_tabela_preco: "{ticker} no vencimento",
      anat_tabela_perna: "Resultado da perna",
      anat_tabela_total: "Resultado do que está marcado",
      anat_perna_aria: "Resultado da perna {id} no vencimento: pior caso {pior}, equilíbrio em R$ {equilibrio}.",
      anat_dados_insuficientes: "Não há dados suficientes para concluir. Faltam strike, prêmio ou quantidade desta perna no simulador; nada foi estimado.",
      anat_confirmar_com_cotacao: "Encerrar {id}? Você vende o direito de volta. Pelo último prêmio lido (R$ {premio}), o resultado desta perna agora é {resultado}; o valor exato sai do prêmio no momento da ordem simulada. Nenhuma ordem real é enviada.",
      anat_confirmar_sem_cotacao: "Encerrar {id}? Você vende o direito de volta. Sem cotação agora, não dá para calcular quanto entra no caixa. Nenhuma ordem real é enviada.",
      anat_carregando: "Calculando o que cada perna faz…",
      anat_recalculando: "Recalculando…",
      anat_desatualizado: "Esta leitura pode estar desatualizada: a última tentativa de recalcular falhou. O gráfico e o total foram ocultados para não mostrar um número de outra hipótese. Nada foi estimado.",
      anat_erro: "Não foi possível calcular agora o que cada perna faz. Nada foi estimado. As pernas e o Encerrar continuam abaixo.",
      anat_legenda_perda: "Área hachurada: perda",
      anat_legenda_ganho: "Área lisa: ganho",
      anat_marcador_strike: "K {strike}",
      anat_marcador_equilibrio: "equilíbrio",
      anat_marcador_pm: "preço médio",
      anat_marcador_hoje: "hoje",
      anat_sem_pernas: "Nenhuma perna aberta em {ticker}.",
      erro_fonte: "Não foi possível ler as opções agora. Nenhum valor foi estimado. Tente de novo; se persistir, os dados de opções estão fora do ar.",
      tentar_de_novo: "Tentar de novo",
      carregando: "Carregando",
      mercado_fechado: "Pregão fechado: estes valores são de {data}, não de agora.",
      frescor: "{fonte} · pregão {data} · {situacao}",
      situacao_em_dia: "em dia",
      situacao_atrasado: "atrasado",
      situacao_fim_pregao: "fim de pregão",
      atrasado_frase: "não é o preço de agora",
      dado_insuficiente: "Não há dados suficientes para concluir.",
      aviso_virtual: "Dinheiro virtual: nenhuma ordem sai para corretora, bolsa ou banco.",
      hub_atencao: "Atenção",
      hub_carteira: "Sua carteira",
      hub_aviso_custo: "Abrir um ativo não gasta consultas.",
      hub_atualizar: "atualizar ›",
      hub_atualizar_custo: "o estado do dia custa {n} consultas",
      hub_nenhum_armado: "Nenhum vigia armado hoje.",
      card_subtitulo: "{qtd} ações · {livres} livres para lastro",
      card_subtitulo_sem_acoes: "sem ações deste ativo · opção sem lastro",
      card_estrutura_aberta: "estrutura aberta: {nome}",
      card_sem_estrutura: "nenhuma estrutura aberta",
      card_vigias: "{n} vigia(s)",
      hub_vazio_titulo: "Você ainda não tem ações em carteira",
      hub_vazio_corpo: "As opções aqui são estudadas sobre as ações que você já tem na carteira virtual. Compre uma posição simulada e volte.",
      hub_vazio_cta: "Ver Carteira",
      voltar: "‹ voltar",
      cta_escolher: "Escolher este",
      sem_custo: "sem custo",
      confirmar_titulo: "Confirmar a estrutura",
      confirmar_estrutura: "Estrutura",
      confirmar_vencimento: "Vencimento",
      perna_put_comprada: "Put comprada: strike R$ {strike}, paga R$ {premio} por ação",
      perna_call_vendida: "Call vendida: strike R$ {strike}, recebe R$ {premio} por ação",
      confirmar_lote: "{contratos} contrato(s) · {qtd} ações",
      lastro_trava: "{qtd} ações ficam travadas como lastro",
      lastro_livre: "sem lastro: ações livres",
      cta_executar: "Executar (simulado)",
      cta_criar_vigia: "Criar vigia",
      estudo_nao_executa: "No Modo Estudo você não executa operações: esta é a leitura de como a estrutura funcionaria.",
      ordem_rejeitada: "Ordem rejeitada: {motivo}",
      toast_executada: "Ordem simulada registrada. Nenhuma ordem real foi enviada.",
    },
    // Fase 48: texto de front da Ajuda/tour (consumido em App.jsx pelo plano 48-11).
    opcoesTourPasso: "A aba Opções estuda as ações da sua Carteira: escolha um ativo, diga o que quer fazer (proteger de queda, gerar renda), compare a escada de estruturas e veja o gráfico do resultado no vencimento — leitura de fim de pregão, sem ordem nenhuma.",
    opcoesAjudaEstuda: "Estuda **opções** sobre as ações que você tem na Carteira: você escolhe um ativo, diz o objetivo (proteger de queda, gerar renda ou proteger com custo baixo), compara a escada de estruturas por vencimento e vê, no gráfico, o resultado no vencimento com o pior caso e o melhor caso antes de decidir.",
    // Fase 46 (CART6-06/07): espelho byte a byte de skill_ref.CARTAO_POSICAO e CARTAO_DIDATICA.
    // Texto novo nasce no .py primeiro; guardião test_cartao_posicao_espelho.mjs.
    cartaoPosicao: {
      face_acao: "Ação",
      face_opcoes: "Opções ({n})",
      face_grupo_aria: "Face do card {ticker}",
      plano_titulo: "Plano da ação",
      compras_titulo: "Compras ({n})",
      ver: "Ver ▾",
      ocultar: "Ocultar ▴",
      compras_indisponivel: "Compras: indisponível nesta fonte",
      compras_sem_detalhe: "Detalhes das compras não vieram nesta fonte — nada foi inferido.",
      falta_definir: "Falta definir",
      estado_sem_plano: "Sem stop e alvo — defina o plano",
      avulsa_sem_acoes: "Sem ações deste ativo: só a opção está aberta.",
      estado_falta_alvo: "Falta o alvo — plano incompleto",
      estado_falta_stop: "Falta o stop — plano incompleto",
      estado_abaixo_stop: "Abaixo do stop do plano",
      estado_acima_alvo: "Acima do alvo do plano",
      estado_dentro: "Dentro do plano",
      estado_travadas_todas: "Ações travadas pela call · saída após encerrar",
      estado_travadas_parcial: "{n} de {m} ações travadas · {k} livres",
      extra_resultado_parcial: "Resultado parcial: um prêmio atual indisponível",
      extra_cotacao_indisponivel: "Cotação atual indisponível nesta fonte",
      plano_ia_definir: "Definir plano · IA",
      plano_ia_completar: "Completar plano · IA",
      plano_ia_ajustar: "Ajustar plano · IA",
      reanalisar: "Reanalisar",
      historico: "Histórico de análises ({n})",
      kicker_ia: "✦ BÓRIS IA",
      encerrar: "Encerrar opção em Opções",
      atualizar: "↻ Atualizar",
      origem_nao_informada: "Origem da cotação não informada",
      sem_cenario: "Cenários não calculados para esta combinação. Os limites dependem do cálculo do app.",
      conta_sem_formula: "Calculado pela camada de opções do app",
      aguardando_calculo: "aguardando o cálculo do app",
      piso: "Piso",
      equilibrio_rotulo: "◆ Equilíbrio",
      teto: "Teto",
      sem_piso: "sem piso",
      sem_teto: "sem teto",
      agora: "agora",
      hoje: "hoje",
      faixa_titulo: "No vencimento ({ddmm})",
      chip_hoje: "Hoje",
      chip_equilibrio: "Equilíbrio",
      chip_teto: "Teto",
      chip_alta_forte: "Alta forte",
      rr_atual: "R:R atual",
      em_operacao: "Em operação",
      do_capital: "Do capital",
      cotacao_atual: "Cotação atual",
      setup_entrada: "Setup de entrada",
      gatilho_valido: "válido",
      gatilho_invalidado: "invalidado",
      nota_pm: "PM R$ {pm} = R$ {total} ÷ {qtd} ações (média ponderada).",
      nota_pm_vendas: " Vendas parciais reduzem a quantidade, não o PM.",
      editar_plano: "✎ Editar stop/alvo",
      regua_aria: "{ticker}: stop R$ {stop}, alvo R$ {alvo}, preço médio R$ {pm}, agora {agora}.",
      faixa_aria: "{ticker} no vencimento: piso {piso}, equilíbrio R$ {be}, teto {teto}, hoje {hoje}.",
      leg_hoje: "┆ hoje {v}",
      leg_be: "◆ BE {v}",
      leg_k: "┆ K {v}",
      leg_eixo: "eixo x: {lo} → {hi}",
      cel_be: "BE",
      cel_ate_be: "Até BE",
      cel_ate_k: "Até K",
      cel_ganho_max: "Ganho máx.",
      cel_perda_max: "Perda máx.",
      cel_lastro: "Lastro",
      conta_be_call: "BE = PM − prêmio",
      conta_ate_be: "Até BE = BE ÷ hoje − 1",
      conta_ate_k: "Até K = K ÷ hoje − 1",
      conta_ganho_call: "Ganho máx. = (K − BE) × qtd",
      conta_perda_call: "Perda máx. = BE × qtd (ação a zero)",
      conta_lastro: "Lastro = ações que cobrem a CALL vendida",
      sim_aria: "Preço de {ticker} no vencimento",
      sim_valuetext: "R$ {preco}; {resultado}; {zona}",
      payoff_sem_custos: "sem custos",
      zona_rotulo_perda_travada: "perda limitada",
      zona_rotulo_prejuizo: "prejuízo",
      zona_rotulo_ganho: "ganho",
      zona_rotulo_ganho_travado: "ganho limitado",
      saida_motivo_lastro: "Todas as ações estão travadas como lastro. Para sair do ativo, encerre a CALL vendida em Opções.",
      rodape_fechar: "Fechar ▴",
      rodape_abrir: "Ver detalhes e aprender ▾",
      saida: "Simular venda",
      saida_sem_livres: "Simular venda · 0 ações livres",
      apoio_saida: "Treino com dinheiro virtual: nenhuma ordem é enviada.",
      sim_lead: "Se em {ddmm} {ticker} fechar a",
      sim_resultado: "resultado da estrutura",
      sim_metodo: "Sem custos. É o resultado no vencimento, não o de hoje.",
      payoff_titulo: "Payoff no vencimento · {ddmm}",
      payoff_aria: "Payoff de {ticker} no vencimento: prejuízo abaixo do equilíbrio R$ {be}; acima do teto R$ {teto} o resultado fica limitado ({ganhoMaximo}); perda máxima {perdaMaxima}.",
      payoff_aria_sem_teto: "Payoff de {ticker} no vencimento: prejuízo abaixo do equilíbrio R$ {be}; sem teto, o resultado acompanha a ação; perda máxima {perdaMaxima}.",
      zona_perda_travada: "Abaixo do piso R$ {piso}: a perda fica limitada a R$ {perdaMaxima}.",
      zona_prejuizo_sem_piso: "Abaixo do equilíbrio R$ {be}: prejuízo. Sem piso, se a ação fosse a zero a perda seria de R$ {perdaMaxima}.",
      zona_prejuizo_com_piso: "Entre o piso R$ {piso} e o equilíbrio R$ {be}: prejuízo, limitado pelo piso.",
      zona_ganho: "Entre o equilíbrio R$ {be} e o teto R$ {teto}: o resultado cresce junto com a ação.",
      zona_ganho_sem_teto: "Acima do equilíbrio R$ {be}, sem teto: o resultado acompanha a ação.",
      zona_ganho_travado: "Acima do teto R$ {teto}: o resultado fica limitado em R$ {ganhoMaximo} e as ações são entregues a R$ {teto}.",
      // 46-UAT (2026-10-01, G-01..G-06): card fechado rótulo/valor, chips e faixa ancorada
      legenda_resultado: "resultado",
      legenda_resultado_variacao: "resultado · {pct}",
      legenda_resultado_estrutura: "resultado da estrutura",
      chip_total_suspenso: "total suspenso",
      linha_acoes: "Ações",
      linha_opcoes: "Opções · {contrato}",
      linha_estrutura: "Estrutura",
      motivo_premio_indisponivel: "prêmio indisponível",
      motivo_dados_incompletos: "dados incompletos",
      motivo_aguardando_premio: "aguardando prêmio",
      motivo_aguardando_cotacao: "aguardando cotação",
      motivo_cotacao_indisponivel: "cotação indisponível",
      chip_acoes_pm: "{qty} ações · PM {pm}",
      chip_vence: "vence {ddmm} · {dias}d",
      chip_plano: "stop {stop} · alvo {alvo}",
      chip_estrategia_generica: "estratégia não classificada",
      faixa_rot_be: "◆ equilíbrio {v}",
      faixa_rot_teto: "teto {v}",
      faixa_leg_hoje: "● hoje {v}",
      // # 46.1 (2026-10-02, G-08/AL-02/MD-02/MD-05): causas da suspensão, estados da leitura, legenda só ações, aria teto parcial.
      motivo_lendo: "atualizando",
      motivo_leitura_indisponivel: "leitura indisponível",
      chip_desatualizado: "desatualizado",
      tentar_de_novo: "↻ Tentar de novo",
      legenda_resultado_so_acoes: "resultado · só ações",
      leitura_falhou: "Não foi possível atualizar a leitura desta posição agora. Os números ficam suspensos e nada é estimado no lugar.",
      leitura_desatualizada: "Esta leitura é das {hora} e não foi atualizada: os números podem não refletir a cotação de agora.",
      causa_sem_cotacao: "Sem cotação da opção {contratos} nesta fonte: o total fica suspenso e nada é estimado no lugar.",
      causa_fora_da_cadeia: "A fonte de dados não trouxe a opção {contratos} na lista de opções: sem cotação dela, o total fica suspenso e nada é estimado no lugar.",
      causa_sem_negocio: "A opção {contratos} está na fonte, mas sem oferta nem negócio recente: sem preço, o total fica suspenso e nada é estimado no lugar.",
      causa_fonte_indisponivel: "A fonte de dados de opções não respondeu para {contratos}: sem cotação, o total fica suspenso e nada é estimado no lugar.",
      payoff_aria_teto_parcial: "Payoff de {ticker} no vencimento: prejuízo abaixo do equilíbrio R$ {be}; o teto R$ {teto} cobre só parte das ações, então o ganho máximo não é calculado; perda máxima {perdaMaxima}.",
    },
    cartaoDidatica: {
      kicker_termos: "TOQUE NOS TERMOS",
      no_seu_caso: "No seu caso:",
      entendi: "Entendi",
      boris_explica: "Bóris explica ·",
      termo_lastro: "lastro",
      termo_call_coberta: "call coberta",
      termo_teto: "teto",
      termo_equilibrio: "equilíbrio",
      termo_piso: "piso",
      termo_preco_medio: "preço médio",
      termo_stop: "stop",
      termo_alvo: "alvo",
      termo_rr: "R:R",
      paragrafo_call_coberta: "Suas {qtd} ações estão como [[lastro]] de uma [[call_coberta]]. O [[teto]] é R$ {teto} e o [[equilibrio]] R$ {be}. Não há [[piso]].",
      paragrafo_collar: "Suas {qtd} ações têm [[piso]] de R$ {piso} e [[teto]] de R$ {teto}, com [[lastro]] para a call. O [[equilibrio]] é R$ {be}.",
      paragrafo_put_protecao: "Suas {qtd} ações têm [[piso]] de R$ {piso}. Não há [[teto]], e o [[equilibrio]] é R$ {be}.",
      paragrafo_composta: "Esta combinação envolve [[lastro]], [[piso]] e [[teto]]: aguardando o cálculo do app.",
      paragrafo_plano_completo: "Você pagou em média o [[preco_medio]] de R$ {pm}. O [[stop]] é R$ {stop}, o [[alvo]] é R$ {alvo} e o [[rr]] é {rr}.",
      paragrafo_plano_completo_sem_rr: "Você pagou em média o [[preco_medio]] de R$ {pm}. O [[stop]] é R$ {stop} e o [[alvo]] é R$ {alvo}.",
      paragrafo_plano_incompleto: "Seu [[preco_medio]] é R$ {pm}. O plano ainda não tem [[stop]] e [[alvo]] completos.",
      caso_lastro: "{qtd} ações ficam reservadas para cobrir a call; {livres} estão livres.",
      caso_call_coberta: "Você recebeu R$ {premio} por ação, R$ {premioTotal} no total, e aceitou entregar as ações a R$ {teto} até {ddmm}.",
      caso_teto: "Acima de R$ {teto} no vencimento, o resultado fica limitado em R$ {ganhoMaximo}.",
      caso_equilibrio: "R$ {be} = preço médio R$ {pm} menos o prêmio R$ {premio}; hoje a ação está a R$ {hoje}.",
      caso_equilibrio_sem_hoje: "R$ {be} = preço médio R$ {pm} menos o prêmio R$ {premio}.",
      caso_equilibrio_collar: "R$ {be} = preço médio R$ {pm} menos o prêmio recebido na call R$ {premioCall} mais o prêmio pago na put R$ {premioPut}; hoje a ação está a R$ {hoje}.",
      caso_equilibrio_collar_sem_hoje: "R$ {be} = preço médio R$ {pm} menos o prêmio recebido na call R$ {premioCall} mais o prêmio pago na put R$ {premioPut}.",
      caso_piso: "Abaixo de R$ {piso} no vencimento, a perda fica limitada a R$ {perdaMaxima}.",
      caso_sem_piso: "Sem piso: se a ação fosse a zero, a perda seria de R$ {perdaMaxima}.",
      caso_preco_medio: "Você pagou em média R$ {pm} por {qtd} ações; hoje a ação está a R$ {hoje}.",
      caso_preco_medio_sem_hoje: "Você pagou em média R$ {pm} por {qtd} ações.",
      caso_stop: "Sair em R$ {stop} daria {resultadoNoStop} em relação ao preço médio.",
      caso_stop_indefinido: "O stop ainda não foi definido.",
      caso_alvo: "Chegar a R$ {alvo} daria {resultadoNoAlvo} em relação ao preço médio.",
      caso_alvo_indefinido: "O alvo ainda não foi definido.",
      caso_rr: "Do preço de hoje, o alvo paga {rr} para cada R$ 1,00 arriscado até o stop.",
      caso_aguardando: "aguardando o cálculo do app",
      explica_call_coberta: "O resultado fica limitado em R$ {ganhoMaximo}, o equilíbrio é R$ {be} e a queda abaixo dele continua com você.",
      explica_collar: "O piso de R$ {piso} e o teto de R$ {teto} mantêm o resultado entre uma perda de R$ {perdaMaxima} e um ganho de R$ {ganhoMaximo}.",
      explica_put_protecao: "O piso de R$ {piso} limita a perda a R$ {perdaMaxima}; acima do equilíbrio R$ {be} o resultado acompanha a ação.",
      explica_composta: "Esta combinação não tem leitura pronta: aguardando o cálculo do app.",
      explica_plano_completo: "O plano tem stop em R$ {stop} e alvo em R$ {alvo}: é um roteiro de treino, não uma previsão.",
      explica_plano_incompleto: "Falta definir parte do plano; sem os dois limites, não há dados suficientes para concluir o risco.",
      explica_sem_plano: "Esta posição não tem stop e alvo; defina um plano para treinar a decisão de saída.",
    },
    linhaPropostaNaPosicao: "Estrutura de opções possível nesta posição",

    // Fase 32 (32-01, D-05): frase-ponte entre os dois motores cross-
    // carteira (Bloco A = OportunidadesOpcoes, com gate; Bloco B =
    // CuradoriaEstruturas, sem gate), sempre visível e NUNCA colapsável —
    // é a mitigação do risco regulatório do D-05: sem ela, quem escaneia a
    // tela lê "AS 4 MELHORES" (Bloco B) como veredito geral do app, em vez
    // de "melhores dentro dos 4 candidatos do próprio bloco". Texto
    // IDÊNTICO nos dois modos DE PROPÓSITO — é constatação de fato sobre
    // dois motores determinísticos, não voz de personagem (mesmo
    // precedente de linhaPatrimonioOpcoes/avisoLiquidacaoForcada acima).
    duasLeiturasIntro: "Duas leituras diferentes da sua carteira — nenhuma é mais certa que a outra: uma parte do que a leitura técnica confirma agora, a outra varre a cadeia inteira sem exigir essa confirmação.",

    // Fase 32 (32-01, D-01/D-02/D-03): linha de chamada em Posições,
    // substituindo os quatro blocos que hoje vivem lá — texto IDÊNTICO nos
    // dois modos (constatação de fato sobre contagem, não voz de
    // personagem). `linhaChamadaOpcoesTexto`/`linhaChamadaOpcoesAria` são
    // FUNÇÕES (as outras chaves deste grupo são string). A contagem `n`
    // vem de `useCuradoria().top.length` — nunca uma segunda busca (D-03).
    // Fase 39 (NAV-01, D-02/D-03): reescrito — a contagem é da aba
    // Recomendadas (curadoria), e "oportunidades" passaria a nomear o OUTRO
    // motor (a aba Oportunidades, D-02, com gate de liquidez).
    // Fase 39-06 (override de D-03, decisão do Alex): "recomendada(s)" vira
    // "destacada(s)" — mesmo motivo regulatório do rótulo da aba acima.
    linhaChamadaOpcoesTexto: (n) => n === 1
      ? "1 estrutura destacada nas suas posições"
      : `${n} estruturas destacadas nas suas posições`,
    linhaChamadaOpcoesVazia: "Nenhuma estrutura destacada agora",
    linhaChamadaOpcoesCarregando: "Verificando estruturas destacadas…",
    // Estado de ERRO de busca — distinto de "vazio" (que é um resultado
    // real, zero candidatos elegíveis). Mostrar "0" aqui seria inventar
    // valor (princípio 4 do CLAUDE.md); por isso a frase não cita número.
    linhaChamadaOpcoesErro: "Não foi possível verificar agora — toque para ver na aba Opções",
    // Existe porque o leitor de tela não deve anunciar só a seta "→".
    linhaChamadaOpcoesAria: (texto) => `${texto} — abrir aba Opções`,

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
    // Fase 39 (NAV-01, D-01/D-08/D-09): reescrito — "AS 4 MELHORES
    // OPORTUNIDADES DE OPÇÕES" colidia com o rótulo da aba vizinha
    // "Oportunidades" (outro motor, SC#4) e "melhores" virava veredito. A
    // posição no ranking passa a ser a leitura primária (D-14, ver
    // curadoriaPosicaoRotulo abaixo).
    curadoriaTitulo: "AS 4 PRIMEIRAS DO RANKING",
    // Fase 39 (NAV-01, D-08/D-09): reescrito de novo — sucessora da
    // frase-ponte da Fase 32 (32-01, D-05), agora DENTRO da aba (as duas
    // viraram abas separadas, a frase-ponte física deixou de fazer sentido
    // entre elas). Nomeia o piso de 60% de chance OTM e o critério de
    // ordenação (prêmio anualizado, D-09), preservando as 3 funções da
    // frase-ponte: nega hierarquia entre os dois motores, nomeia o
    // critério, diz que a IA não reordena.
    curadoriaSubtitulo: "Só entram aqui candidatos com pelo menos 60% de chance estimada (modelo Black-Scholes) de a opção terminar fora do dinheiro no vencimento, ordenados por prêmio anualizado. É um critério de ordenação entre outros possíveis — não uma promessa de resultado nem uma leitura mais certa que a aba Oportunidades. Varre todas as posições e vencimentos, inclusive o que a leitura técnica ainda não confirma. A ordem é do motor; não muda com a explicação da IA.",
    curadoriaCarregando: "Varrendo sua carteira em busca das melhores oportunidades…",
    // ESTADO (NAV-03), sem CTA — nomeia o motivo, mesmo precedente de
    // tiraOpcoesSemCobertura acima.
    curadoriaVazio: "Nenhuma estrutura elegível nos vencimentos varridos — por isso não há nada para ranquear agora.",
    // Fase 39 (NAV-01, D-08/D-11): 4º estado (não 3) — distingue "varreu e
    // nenhum passou no piso de 60% OTM" (este) de "zero candidatos varridos"
    // (curadoriaVazio acima) e de "não deu para medir a probabilidade"
    // (curadoriaVazioSemProb abaixo). Nunca dizer "não há oportunidade"
    // quando na verdade "há candidatos, mas nenhum passou no piso de
    // segurança" (princípio 4 do CLAUDE.md).
    curadoriaVazioPiso: (pct) =>
      `Nenhum candidato com pelo menos ${pct}% de chance estimada de terminar fora do dinheiro (OTM) no vencimento hoje. Isto não significa que não há oportunidade — significa que nenhum passou no piso mínimo desta lista.`,
    // Fase 39 (NAV-01, D-08): quando a volatilidade dos contratos varridos
    // não está disponível, a chance OTM não pode ser estimada — excluir o
    // candidato é a resposta correta (nunca admitir por falta de dado,
    // princípio 4 do CLAUDE.md), mas o motivo tem de ser NOMEADO, não
    // confundido com "nenhum passou no piso" (que afirmaria uma medição que
    // não ocorreu).
    curadoriaVazioSemProb: "Não há dados suficientes para concluir: a volatilidade dos contratos varridos hoje não está disponível, então a chance de terminar fora do dinheiro não pôde ser estimada e nenhum candidato entrou na lista.",
    // Fase 39 (NAV-01, D-14): posição no ranking substitui o score bruto
    // (curadoriaRazaoRotulo, "pontuação de curadoria: 0.02") como a forma
    // única de comunicar ordem — idêntica nos dois modos (é navegação, não
    // voz de personagem).
    curadoriaPosicaoRotulo: (pos, total) => pos + "ª de " + total,
    curadoriaProbOtmRotulo: "Chance estimada de terminar fora do dinheiro (OTM)",
    curadoriaPremioAnualizadoRotulo: "Prêmio anualizado (critério da ordem)",
    curadoriaVolImplicita: "vol. implícita",
    curadoriaVolHistorica: "vol. histórica de 21 pregões",
    // Fase 32 (32-01): correção de estado obrigatória (achado do UI-SPEC).
    // `useCuradoria().erro` já existia mas nunca era exibido — falha de
    // busca caía no ramo `top.length === 0 && !carregando`, que mostra
    // `curadoriaVazio` ("nenhuma estrutura elegível"), afirmando um
    // resultado que ninguém mediu (princípio 4 do CLAUDE.md: não invente
    // valores, mostre o estado correto). Texto IDÊNTICO nos dois modos —
    // constatação de fato sobre falha técnica, não voz de personagem.
    curadoriaErroBusca: "Não foi possível varrer sua carteira agora. Isto não significa que não há oportunidade — significa que a busca falhou. Toque para tentar de novo.",
    curadoriaErroBuscaCta: "Tentar de novo",
    // Fase 37 (37-02, D-04): renomeado — o valor antigo ("prêmio sobre
    // perda máxima") lia como resultado financeiro e foi a causa raiz da
    // confusão confirmada em produção com `RazaoGanhoPerda` (ver comentário
    // do quick 260915-ndt logo abaixo). `cand.razao` (campo JS) não muda —
    // é só o rótulo lido por humano.
    curadoriaRazaoRotulo: "Pontuação de curadoria (ordena a lista — não é o resultado da estrutura)",
    curadoriaRazaoAjuda: "Prêmio negativo significa que montar a estrutura custa dinheiro (é uma proteção) — por isso ela pode aparecer embaixo na mesma régua, sem que isso seja um defeito do ranking.",
    // Quick 260915-ndt: defeito corrigido — o painel inline de confirmação
    // (App.jsx, quick 260915-j5l) usava `curadoriaRazaoRotulo` ("prêmio
    // sobre perda máxima") ao lado de `money(item.premioTotal)`, que é o
    // PRÊMIO EM REAIS, não a razão. Em produção o painel mostrou "prêmio /
    // perda máxima  R$ 847,00" enquanto o card acima mostrava a razão real
    // (77.00) sob o MESMO rótulo — dois números diferentes, um rótulo só,
    // num app financeiro (princípio 4 do CLAUDE.md). Chave separada, nunca
    // reaproveita `curadoriaRazaoRotulo`. O modo Estudo explica o SINAL, que
    // é justamente o que confunde em put de proteção e collar de débito
    // (mesma assimetria de `opcoes_curadoria.py:341-343`).
    curadoriaPremioRotulo: "prêmio líquido (positivo você recebe, negativo você paga)",
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

    // Quick 260915-j5l: o clique no card passa a abrir uma confirmação
    // INLINE (prêmio/perda máxima/breakeven + botão) em vez de rolar para o
    // acordeão de UMA posição. Voz de professor: descreve a condição, nunca
    // convida a trocar de modo com linguagem de venda.
    curadoriaExecutarCta: "Executar esta estrutura",
    curadoriaExecutando: "Executando…",
    curadoriaFechar: "Fechar",
    curadoriaExecutada: "Estrutura executada — veja a posição na carteira.",
    curadoriaLiquidezConsentir: "Entendo que esta opção negociou pouco hoje e o preço pode se mover contra mim ao executar.",
    curadoriaEstudoNaoExecuta: "No Modo Estudo você não executa operações — esta é a leitura de como a estrutura funcionaria.",
    curadoriaVerPosicao: "Ver detalhe da posição",
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
    // Fase 35 (35-01) — MESMA nota do ramo estudo: metadado de progresso,
    // valor idêntico nos dois modos por desenho (D-01/D-06).
    opcoesPasso1de2: "Passo 1 de 2",
    opcoesLeituraJaFeita: "leitura já feita",
    opcoesSetupsTitulo: "SETUPS GRAVADOS",
    opcoesPregaoRotulo: "Pregão",
    opcoesFonteRotulo: "Fonte",
    opcoesFrescorEmDia: "dado em dia",
    opcoesFrescorAtrasado: "dado atrasado",
    opcoesFrescorNaoMedido: "frescor não medido",
    // Fase 33 (33-02, D-04b): mesmo rótulo do ramo estudo — é o nome do
    // dado, não juízo, igual aos vizinhos Pregão/Fonte.
    opcoesConsultadoEmRotulo: "Consultado",
    // Fase 27 (27-05) — a única chamada da aba sem clique, declarada. Mesma
    // razão do ramo estudo: o gate de frescor precisa existir na abertura
    // (ADR-027, Decisão 8), então o que resta é dizer o preço dele.
    opcoesCustoFrescor: "Abrir a aba consulta o frescor no serviço: até 1 chamada da cota do dia, zero quando o frescor está em cache. É a única consulta desta tela que sai sem pedido — o resto sai de botão com o preço escrito.",
    // Fase 39 (NAV-01, D-14): MESMA nota do ramo estudo — rótulo do ⓘ de
    // bastidor da aba Montar, voz de mesa (curta).
    opcoesCustoFrescorRotulo: "custo da aba",
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
    // Fase 39 (NAV-01, D-07): MESMAS chaves do ramo estudo — navegação/
    // rótulo de controle, idêntico nos dois modos (ver comentário lá).
    opcoesVigiasSheetTitulo: "Seus vigias",
    opcoesVigiasFechar: "Fechar",
    opcoesVigiasAbrirSheet: (n) =>
      n === 1 ? "1 vigia — abrir" : n > 1 ? n + " vigias — abrir" : "Vigias — abrir",
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
    // Fase 39 (NAV-01, D-14): MESMA nota do ramo estudo — rótulo do ⓘ de
    // bastidor, voz de mesa (curta).
    opcoesLastroAjudaRotulo: "regra do lastro",
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
    // Fase 39 (NAV-01, D-06): MESMAS chaves do ramo estudo — navegação,
    // idêntico nos dois modos (ver comentário lá).
    opcoesVerOutrosVencimentos: "Ver outros vencimentos",
    opcoesOcultarOutrosVencimentos: "Ocultar outros vencimentos",
    // Fase 35 (35-01) — MESMA nota do ramo estudo: marca neutra, T.textMuted,
    // valor idêntico nos dois modos (D-06).
    opcoesEstruturaMontada: "Estrutura montada",
    opcoesPossibilidadesVistas: "Possibilidades carregadas",
    // Quick 260923-ndy (Task 2): mesma linha do ramo estudo, voz de mesa.
    opcoesExecucaoSimulada: "Execução simulada, saldo virtual — nenhuma ordem sai do app.",
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

    // Fase 37 (37-02) — mesmas chaves do ramo estudo (ver comentário lá),
    // redação idêntica: o UI-SPEC (37-UI-SPEC.md §3) não pede variação de
    // voz para estas 19 chaves.
    opcoesEixoZeroRotulo: "R$ 0",
    opcoesEixoVerticalLoteAjuda: "Multiplique pelo lote para o valor total.",
    opcoesNoVencimentoTitulo: "No vencimento",
    opcoesHojeTitulo: "Hoje · valor de mercado",
    opcoesHojeAjuda: "Preço de mercado agora — pode mudar a qualquer momento, diferente do resultado no vencimento acima.",
    opcoesPerdaIlimitadaCurta: "sem piso",
    opcoesHojePrefixoEixo: "hoje",
    opcoesComoLerTitulo: "Como ler esta estrutura",
    opcoesExplicSpotPositiva: "Hoje, com o ativo em R$ {spot}, você está numa faixa de alta: se o preço subir, seu resultado melhora; se cair, piora.",
    opcoesExplicSpotNegativa: "Hoje, com o ativo em R$ {spot}, você está numa faixa de baixa: se o preço cair, seu resultado melhora; se subir, piora.",
    opcoesExplicSpotPlato: "Hoje, com o ativo em R$ {spot}, seu resultado está travado: dentro desta faixa, o preço subir ou cair não muda nada.",
    opcoesExplicSpotCaudaGanho: "Hoje, com o ativo em R$ {spot}, você está na faixa sem teto de ganho: quanto mais o preço subir, maior o resultado, sem limite declarado pelo serviço.",
    opcoesExplicSpotCaudaPerda: "Hoje, com o ativo em R$ {spot}, você está na faixa sem piso de perda: quanto mais o preço subir, maior a perda, sem limite declarado pelo serviço.",
    opcoesExplicOutroPositiva: "Entre R$ {de} e R$ {ate}, o resultado sobe conforme o preço do ativo sobe.",
    opcoesExplicOutroNegativa: "Entre R$ {de} e R$ {ate}, o resultado cai conforme o preço do ativo sobe.",
    opcoesExplicOutroPlato: "Entre R$ {de} e R$ {ate}, o resultado fica travado — não muda com o preço.",
    opcoesExplicOutroCaudaPlato: "Acima de R$ {de}, o resultado fica travado, mesmo que o preço continue subindo.",
    opcoesExplicOutroCaudaGanho: "Acima de R$ {de}, o ganho aumenta sem limite conforme o preço sobe.",
    opcoesExplicOutroCaudaPerda: "Acima de R$ {de}, a perda aumenta sem limite conforme o preço sobe.",

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

    // Fase 34 (34-01) — mesma nota do ramo estudo: header fixo do workspace
    // (D-05) + pill row de 3 abas (D-02). Tom mais terso que o Estudo, igual
    // ao restante do vocabulário de mesa (rótulo da 3ª aba fica "Setups" em
    // vez de "Setups salvos" — mesma divergência de tom de opcoesSubabaOperar).
    opcoesVoltarAoHub: "Voltar",
    opcoesAbaAnalisar: "Analisar",
    opcoesAbaComparar: "Comparar",
    opcoesAbaSetupsSalvos: "Setups",
    // Fase 39 (NAV-01, D-01): MESMAS chaves do ramo estudo — as 3 abas fixas
    // de nível 1, navegação idêntica nos dois modos (ver comentário lá).
    opcoesAbaOportunidades: "Oportunidades",
    // Fase 39-06: mesma renomeação do ramo estudo (ver comentário lá) —
    // "Destacadas" nos dois modos.
    opcoesAbaRecomendadas: "Destacadas",
    opcoesAbaMontar: "Montar",
    // Fase 39 (NAV-01, D-04): voz de mesa, mais curta que o ramo estudo.
    opcoesMontarTitulo: "MONTAR ESTRUTURA",
    opcoesMontarNoAtivo: (t) => "Montar com " + t,
    // Fase 35 (35-01) — MESMA nota do ramo estudo: rótulo do estágio 2 e
    // linha de transição, nunca numerando Analisar/Comparar entre si (D-01/
    // D-08, princípio 5 do CLAUDE.md).
    opcoesEscolhaTitulo: "O QUE FAZER",
    opcoesPasso2de2: "Passo 2 de 2",
    // Fase 39 (NAV-01, D-01/D-06): reescrita, mesma razão do ramo estudo —
    // voz de mesa, curta.
    opcoesLeituraConcluidaAjuda: "Leitura feita — monte abaixo; outros vencimentos no link depois.",

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
    // Quick 261006-dvf (2026-10-06): espelho byte a byte de skill_ref.RETORNO_ACUMULADO.
    retornoAcumulado: {
      carimbada: "Retorno acumulado desde o capital inicial: {pct}.",
      carimbada_reinicio: "Retorno acumulado desde {desde} (capital alterado): {pct}. Aporte ou retirada não conta como retorno.",
      primeiro_registro: "Retorno acumulado desde {desde} (1º dia registrado): {pct}. Capital inicial da série não registrado.",
      sem_serie: "Não há dados suficientes para concluir. Sem dia de patrimônio registrado.",
      inconsistente: "Não há dados suficientes para concluir. Bases da série inconsistentes, sem ajuste de capital registrado.",
    },
    // Quick 261006-qre (2026-10-06): espelho byte a byte de skill_ref.CURVA_EVOLUCAO.
    curvaEvolucao: {
      antes_da_base: "Antes de {desde} (pontilhado): só patrimônio registrado, fora da base do retorno.",
    },
    // Fase 43 (HIER-03): espelho byte a byte de
    // skill_ref.RECONCILIACAO_ELEGIBILIDADE (modo "operador") — placeholders
    // literais, interpolação é do helper reconciliacaoTxt.
    reconciliacaoElegibilidade: {
      elegivel: "Critérios ok · vantagem medida (n={n}, {janela}, {expR})",
      inelegivel: "Critérios ok · sem vantagem medida (n={n}, {janela}, {expR})",
      insuficiente: "Critérios ok · amostra insuficiente (n={n} — pouco para medir)",
      nunca_medido: "Critérios ok · sem histórico medido",
      aposentado: "Padrão identificado · sem vantagem medida em 15 anos (ADR-016)",
    },
    // Fase 42 (D-01/D-07/D-09/D-15): fatos do motor, idênticos nos dois
    // modos — microtexto por modo é HIER-03 (Fase 43).
    sinal: {
      alinhamento: { a_favor: "a favor da tendência", contra: "contra a tendência" },
      anelLado: { alta: "padrão de compra", baixa: "padrão de venda" },
      fundamentoNaoDirecao: "fundamento indica qualidade da empresa, não direção",
      degradadoSufixo: "·SMA50",
      degradadoAria: "base degradada SMA50",
      ariaRegime: (valor, alinhamentoTxt, degradado) =>
        "Regime: " + String(valor).toLowerCase() +
        (degradado ? " (base degradada SMA50)" : "") +
        (alinhamentoTxt ? ", " + alinhamentoTxt : ""),
      ariaFundamento: (score) => "Fundamento: qualidade " + score + " (não indica direção)",
      ariaAnel: (texto) => "Confluência " + texto,
      ariaManchete: (kicker, decisao) => kicker + ": " + decisao,
      // Fase 43 (CHIP-03, D-02): rótulos da Leitura da IA — fatos de seção,
      // idênticos nos dois modos; recomendação da IA NÃO tem rótulo aqui (D-03).
      leituraIa: {
        rotulo: "LEITURA DA IA",
        campos: { direcao: "DIREÇÃO", conviccao: "CONVICÇÃO", qualidade: "QUALIDADE" },
        aria: (chave, valor) =>
          ({ direcao: "Direção", conviccao: "Convicção", qualidade: "Qualidade" })[chave] +
          " da leitura da IA: " + valor,
      },
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

    // Fase 38 (38-04, KB-01): chaves espelhadas do ramo estudo — rótulo de
    // interface, não voz de modo (ver comentário no ramo estudo).
    glossarioSub: (n) => (n ? n + " termos" : "Termos") + " de indicadores, estruturas e mecânica da B3 — busque ou navegue por categoria",
    glossarioBuscaPlaceholder: "Buscar um termo (ex.: RSI, stop, IPO...)",
    glossarioBuscaRotulo: "Buscar no glossário",
    glossarioLimpar: "Limpar busca",
    glossarioVazio: (termo) => `Nenhum verbete encontrado para "${termo}".`,
    glossarioErro: "Não consegui carregar o glossário agora. Toque para tentar de novo.",

    // Fase 38 (38-05, KB-02): chave espelhada do ramo estudo — rótulo de
    // interface, não voz de modo (ver comentário no ramo estudo).
    saibaMais: "saiba mais",
    // Fase 39 (NAV-01, D-13): MESMA chave do ramo estudo — aria-label
    // composto do ⓘ contextual por aba, idêntico nos dois modos.
    opcoesSaibaMaisAria: (aba) => "O que é uma opção — " + aba,

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
    // Reversão deliberada (Fase 45, D-11/discretion "usar collar"): a âncora legada do vocabulário de collar (Fase 8) saiu das 5 chaves de collar do Operador.
    eyebrowPropostaCollar: "PROPOSTA · COLLAR",
    collarPernasLinha: (n, ticker, strikeCall, strikePut) => `${n}× COLLAR ${ticker} · call ${strikeCall} / put ${strikePut}`,
    ctaCollarDebito: (n, ticker, sc, sp, valor) => `Montar ${n}× collar ${ticker} · call ${sc} / put ${sp} — custa R$ ${valor}`,
    ctaCollarCredito: (n, ticker, sc, sp, valor) => `Montar ${n}× collar ${ticker} · call ${sc} / put ${sp} — recebe R$ ${valor}`,
    confirmAbrirCollar: (n, ticker, qty) => `Montar ${n} collar(s) de ${ticker} — trava ${qty} ação(ões) do seu lote-lastro (perna da call) até você encerrar a estrutura ou ela vencer. As duas pernas são abertas juntas — ou nenhuma. Continuar?`,

    // Fase 14 (Plano 07): mesma chave do ramo estudo (ver comentário acima).
    // Registro de mesa — vocabulário de ordem liberado aqui.
    badgeTravada: (qty) => `${qty} travada(s) · lastro de CALL`,
    avisoTravaNaVenda: (qty) => `${qty} ação(ões) travada(s) como lastro da call coberta — liberam quando você recomprar a call ou ela vencer.`,

    // Fase 45 — rótulos neutros do card estruturado; guardião de igualdade Estudo=Operador
    // (test_estrutura_card_espelho.mjs). Idênticos nos dois modos de propósito.
    estruturaResultadoRotulo: "RESULTADO DA ESTRUTURA",
    estruturaResultadoSoAcoesRotulo: "SÓ AS AÇÕES — PRÊMIOS INDISPONÍVEIS",
    estruturaAcoesRotulo: "Ações",
    estruturaOpcoesRotulo: "Opções",
    estruturaFaixaTitulo: "FAIXA NO VENCIMENTO",
    estruturaPernasTitulo: "PERNAS",
    estruturaLegenda: { piso: "PISO", pm: "PM", hoje: "HOJE", teto: "TETO", stop: "STOP", alvo: "ALVO" },
    semPiso: "sem piso",
    semTeto: "sem teto",
    ladoVendida: "vendida",
    ladoComprada: "comprada",
    semCotacaoPerna: "sem cotação",
    chipVence: (ddmm, dias) => `vence ${ddmm} · ${dias} dia(s)`,
    chipVenceHoje: "vence hoje",
    chipVencida: (ddmm) => `vencida em ${ddmm}`,
    // Reversão deliberada Fase 45 (decisão do Alex): o destino só recompra a call; o rótulo promete apenas navegar.
    btnEncerrarEstrutura: "Encerrar opção em Opções",
    btnAtualizarEstrutura: "Atualizar",
    fonteEstruturaLinha: (fonte, quando) => `Opções lidas de ${fonte} em ${quando}`,
    fonteEstruturaSemDado: "Fonte das opções não declarada.",
    estruturaFaixaAria: (nome, textos, hoje, pm) => `${nome}. ${textos} Hoje R$ ${hoje}. Preço médio R$ ${pm}.`,
    encerrarAria: (t) => `Ver encerramento de ${t}: abre a aba Opções em ${t}`,
    // Fase 45 (code review WR-04): motivo neutro quando o motor não trouxe o texto do bloqueio.
    encerrarSemMotivo: "Encerramento indisponível: não há dados suficientes para concluir.",
    estruturaGrupoAria: "Estrutura de opções",
    estruturaPernaLinha: (tipo, lado, strike, ddmm) => `${tipo} ${lado} · strike ${strike} · vence ${ddmm}`,
    estruturaPremioLinha: (entrada, atual) => `prêmio R$ ${entrada} → R$ ${atual}`,
    estruturaQtdPerna: (q) => `×${q}`,
    // Fase 45 (code review WR-03): fallbacks neutros para campo parcial do motor.
    semPremioPerna: "prêmio —",
    estruturaPremioSoAtual: (atual) => `prêmio atual R$ ${atual}`,
    estruturaLivresLinha: (livres, qty) => `${livres}/${qty} livres (lastro da call)`,
    estruturaSaidaSemLastro: "sem lastro",
    estruturaVerHistorico: "Ver no histórico de operações →",

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
    //
    // Fase 32 (32-01, D-01/D-03/D-05): título REESCRITO, mesmo motivo do
    // ramo estudo (ver comentário acima) — voz de mesa, curta.
    tiraOpcoesTitulo: "CONFIRMADAS PELA LEITURA TÉCNICA",
    tiraOpcoesSubtitulo: "Só entram aqui posições cuja leitura técnica confirma a estrutura agora — mesmo motor do gatilho do Radar.",
    tiraOpcoesVerDetalhe: "ver detalhe",
    tiraOpcoesCarregando: "Varrendo suas posições…",
    // Quick 260928-u0h (2026-09-28): tiraOpcoesSemCobertura/SemSetup/SemMercado sem consumidor em
    // componente desde esta quick — mantidas (guardiões de paridade as travam); remoção é decisão separada.
    tiraOpcoesSemCobertura: "Nenhuma posição com opção líquida hoje — sem contrato líquido, não há estrutura para montar.",
    tiraOpcoesSemSetup: "Cobertura líquida existe, mas a leitura técnica não indica venda coberta, put de proteção nem collar agora. A cadeia completa continua disponível em cada ativo.",
    // Quick 260908-ldg (D-07): mesma distinção do ramo estudo (ver
    // comentário acima). Voz de mesa, sem verbo de ordem.
    tiraOpcoesSemMercado: "As opções das suas posições estão hoje na faixa SEM MERCADO — negociaram tão pouco que o preço da tela não é um preço real de execução. Nenhuma estrutura é montada sobre elas agora.",
    // Quick 260928-u0h (2026-09-28): encerramento não passa pela leitura técnica (main.py, ramo
    // `pos_op_aberta` -> proposta_fechar), por isso ganha seção própria. As frases de motivo moram
    // AQUI e não em skill_ref porque `motivoTexto` do backend colapsa sem_contrato_liquido e
    // sem_vencimento_elegivel na frase de sem_setup (falsa para eles).
    tiraOpcoesAbertasTitulo: "ESTRUTURAS ABERTAS · ENCERRAMENTO",
    tiraOpcoesAbertasSubtitulo: "Encerramento do contrato já aberto — não depende da leitura técnica, só da cotação atual da opção.",
    tiraOpcoesNenhumaNova: "Nenhuma estrutura nova confirmada agora.",
    tiraOpcoesMotivosTitulo: "SEM ESTRUTURA AGORA",
    tiraOpcoesMotivo: {
      sem_setup: "Leitura técnica sem sinal para venda coberta ou put de proteção — em alta a call trava o movimento; sem leitura, sem proposta.",
      sem_lastro: "Sem lote livre de 100 ações para lastrear a estrutura.",
      sem_vencimento_elegivel: "Nenhum vencimento futuro lido.",
      sem_contrato_liquido: "Sem contrato líquido no strike/vencimento da estrutura.",
      caixa_insuficiente: "Caixa insuficiente para o prêmio da put; collar também não fecha.",
      degradado: "Cotação de opções degradada — estrutura suspensa até o dado normalizar.",
      sem_mercado: "Opções na faixa SEM MERCADO — preço de tela não é preço de execução.",
      sem_liquidez: "Opções sem liquidez suficiente hoje.",
      indisponivel: "Consulta de opções indisponível agora — sem dado, sem estrutura.",
      aberta_sem_proposta: "Estrutura aberta, encerramento sem proposta agora (opção ilíquida ou cotação indisponível). Posição segue aberta.",
      desconhecido: "Sem estrutura agora; motivo não identificado. Não há dados suficientes para concluir.",
    },
    // Fase 44 (ESTR-06): espelho byte a byte de skill_ref.ESTRUTURA_POSICAO / OPCOES_LASTREADAS —
    // guardião web/tests/test_estrutura_espelho.mjs; texto novo nasce no .py primeiro.
    estruturaPosicao: {
      nome_call_coberta: "call coberta",
      nome_put_protecao: "put de proteção",
      nome_collar: "collar",
      nome_fora_da_biblioteca: "Fora da biblioteca (call coberta, put de proteção, collar) — pernas listadas, sem faixa.",
      estado_vigente: "Vigente · vence {vencimento} ({dias} dia(s)).",
      estado_vigente_sem_data: "Vencimento não informado — prazo indeterminado.",
      estado_perto_vencimento: "Vence em {dias} dia(s) ({vencimento}) — decidir: encerrar ou deixar vencer.",
      estado_exercicio_provavel: "Exercício provável: strike R$ {strike} dentro do dinheiro (ação a R$ {spot}).",
      estado_premio_indisponivel: "Prêmio indisponível: {pernas}. Resultado total suspenso.",
      estado_vencida: "Vencida em {vencimento}.",
      aberta_sem_proposta: "Aberta, sem proposta de encerramento. {motivo}",
      faixa_piso: "Piso R$ {piso} · perda máx. R$ {perdaMaxima}.",
      faixa_teto: "Teto R$ {teto} · ganho máx. R$ {ganhoMaximo}.",
      faixa_sem_piso: "Sem piso · perda máx. R$ {perdaMaxima} (ação a zero).",
      faixa_sem_teto: "Sem teto · ganho não limitado pela estrutura.",
      faixa_teto_parcial: "Teto R$ {teto} só em {qtd} de {qtdBase} ações · ganho do restante não limitado.",
      faixa_piso_sem_perda: "Piso R$ {piso} em {qtd} ações · perda máx. não calculável.",
      faixa_vencimentos_diferentes: "Vencimentos diferentes ({vencimentos}) — faixa não calculada.",
      faixa_perna_sem_lastro: "Call vendida sem lastro em {quantidade} — perda ilimitada, faixa não calculada.",
      faixa_sem_acoes: "Sem ações de {ticker} — faixa não calculada.",
      faixa_dados_insuficientes: "Faixa indisponível — dados insuficientes.",
      descoberta_put: "Put excedente em {quantidade} — faixa na parte coberta ({qtdBase}).",
      stop_protegida: "Proteção pela put R$ {piso} no vencimento.",
      resultado_incompleto: "Resultado total indisponível — sem cotação: {pernas}.",
      acao_sem_cotacao: "Ação sem cotação — resultado suspenso.",
      resultado_dados_invalidos: "Resultado total indisponível — dados inválidos: {pernas}.",
      encerrar_premio_indisponivel: "Encerrar bloqueado — sem prêmio: {pernas}.",
      encerrar_vencida: "Encerrar indisponível — vencida em {vencimento}.",
      origem_last: "{perna}: prêmio pelo último negócio (sem oferta).",
    },
    opcoesLastreadasMotivo: {
      sem_lastro: "Sem posição em {ticker} na carteira — venda coberta e put de proteção exigem uma posição real do ativo-lastro.",
      sem_setup: "A leitura técnica de {ticker} não indica venda coberta nem put de proteção agora. A cadeia completa continua disponível abaixo.",
      degradado: "Proposta indisponível — cotação de opções degradada.",
      caixa_insuficiente: "Caixa insuficiente para o prêmio desta put de proteção.",
      sem_contrato_liquido: "Existe cadeia de opções de {ticker}, mas nenhum contrato no strike e no vencimento que a estrutura pede negocia o bastante para ter um preço confiável.",
      sem_vencimento_elegivel: "Nenhum vencimento futuro de opção de {ticker} foi lido — sem vencimento futuro, nenhuma estrutura nova é montada.",
      premio_indisponivel: "Sem prêmio cotado para a opção aberta de {ticker} agora — o encerramento não é proposto sem preço, e nada é estimado no lugar.",
      contrato_fora_da_cadeia: "O contrato aberto de {ticker} não veio na cadeia de opções consultada agora — sem ele, o encerramento não é proposto.",
      sem_mercado: "As opções abertas de {ticker} estão na faixa SEM MERCADO — o preço da tela não seria o preço real de uma ordem.",
    },
    // Fase 45 (CARD-01/04/05/06): espelho byte a byte de skill_ref.ESTRUTURA_CARD.
    // Texto novo nasce no .py primeiro; guardião test_estrutura_card_espelho.mjs.
    estruturaCard: {
      chip_estrutura: "ESTRUTURA · {nome}",
      chip_estrutura_generica: "ESTRUTURA · OPÇÕES",
      lendo: "Lendo a estrutura de opções…",
      indisponivel: "Estrutura indisponível agora. Pernas abertas seguem na carteira — nada estimado.",
      badge_travada_collar: "{qty} travada(s) · lastro da CALL do collar",
      aviso_sem_stop: "Posição sem stop definido — defina em Editar stop/alvo ou peça a sugestão da IA.",
    },
    // Fase 48 (2026-10-05): espelho byte a byte de skill_ref.OPCOES_ESCADA.
    // Texto novo nasce no .py primeiro; guardião test_opcoes_escada_espelho.mjs.
    opcoesEscada: {
      objetivo_proteger_titulo: "Proteger de queda",
      objetivo_proteger_desc: "Paga prêmio, trava o piso. Put protetora.",
      objetivo_proteger_perde: "Perde: o prêmio, se a ação não cair",
      objetivo_renda_titulo: "Gerar renda",
      objetivo_renda_desc: "Recebe prêmio, limita o teto. Venda coberta: trava as ações como lastro.",
      objetivo_renda_perde: "Perde: ganho acima do teto",
      objetivo_collar_titulo: "Proteger com custo baixo",
      objetivo_collar_desc: "Prêmio da call paga (quase) a put. Perda e ganho entre piso e teto. Collar.",
      objetivo_collar_perde: "Perde: ganho acima do teto",
      objetivo_indisponivel: "{objetivo} indisponível: {motivo}.",
      lastro_insuficiente: "só {livres} ações livres; esta estrutura precisa de {necessarias}",
      lastro_travado: "ações travadas em outra call",
      pergunta_objetivo: "Objetivo para as {qtd} ações?",
      pergunta_objetivo_sub: "Pior caso e gráfico antes de decidir. Termos sublinhados abrem a explicação.",
      montar_do_zero: "Montar do zero",
      secao_proteger: "Escolha o piso",
      secao_renda: "Escolha o teto",
      secao_collar: "Escolha o piso e o teto",
      acao_a: "ação a R$ {preco}",
      degrau_proteger_0: "Mais protegido",
      degrau_proteger_1: "Equilibrado",
      degrau_proteger_2: "Mais barato",
      degrau_renda_0: "Mais renda",
      degrau_renda_1: "Equilibrado",
      degrau_renda_2: "Mais espaço para subir",
      degrau_collar_0: "Mais protegido",
      degrau_collar_1: "Equilibrado",
      degrau_collar_2: "Mais barato",
      degrau_ausente: "Degrau sem estrutura: {motivo}",
      vencimento_dias: "{dias} dias",
      vencimento_dia: "{dias} dia",
      col_perda_maxima: "Perda máxima",
      col_custo_protecao: "Custo da proteção",
      col_ganho_maximo: "Ganho máximo",
      col_premio_recebido: "Prêmio recebido",
      col_liquido_custa: "Custa no líquido",
      col_liquido_recebe: "Recebe no líquido",
      nota_sem_piso: "sem piso: a queda não é limitada",
      nota_ganho_negativo: "se exercida: perda",
      risco_pior: "Pior caso: perde até R$ {perdaTotal} nas {qtd} ações (R$ {perdaAcao}/ação) abaixo do piso de R$ {piso}.",
      risco_pior_sem_piso: "Pior caso: sem piso, ação a zero = perda de R$ {perdaTotal}; queda igual à da ação, amortecida só pelo prêmio de R$ {premio}.",
      risco_melhor: "Melhor caso: ganha até R$ {ganhoTotal} nas {qtd} ações (R$ {ganhoAcao}/ação) acima do teto de R$ {teto}.",
      risco_melhor_sem_teto: "Melhor caso: sem teto, ganho = alta da ação menos o prêmio pago.",
      risco_equilibrio: "Equilíbrio: ação a R$ {be} no vencimento {venc}.",
      risco_sem_equilibrio: "Equilíbrio: não há dados suficientes para concluir.",
      grafico_titulo: "Resultado no vencimento",
      grafico_subtitulo: "linha cheia = com a estrutura · tracejada = só as ações",
      unidade_total: "Total ({qtd} ações)",
      unidade_acao: "Por ação",
      linha_so_acoes: "Só as ações",
      linha_com_estrutura: "Com a estrutura",
      linha_preco_medio: "preço médio",
      marcador_piso: "piso",
      marcador_equilibrio: "equilíbrio",
      marcador_teto: "teto",
      marcador_perda_maxima: "perda máxima",
      marcador_ganho_maximo: "ganho máximo",
      legenda_piso: "Piso R$ {preco}: abaixo, a perda por ação para de crescer.",
      legenda_equilibrio: "Equilíbrio R$ {preco}: resultado zero no vencimento.",
      legenda_teto: "Teto R$ {preco}: acima, o ganho por ação para de crescer.",
      legenda_perda_maxima: "Perda máxima R$ {valor}: pior resultado no vencimento.",
      legenda_ganho_maximo: "Ganho máximo R$ {valor}: melhor resultado no vencimento.",
      ausente_piso: "Sem piso nesta estrutura: a queda não é limitada.",
      ausente_teto: "Sem teto nesta estrutura: o ganho acompanha a alta, menos o prêmio.",
      ausente_ganho_maximo: "Sem ganho máximo: o ganho acompanha a alta da ação.",
      grafico_aria: "Resultado de {ticker} no vencimento {venc}, em {unidade}. Pior caso: {pior}. Melhor caso: {melhor}. Equilíbrio: {be}.",
      sem_grafico: "Sem gráfico para esta estrutura: {motivo}",
      ese_pergunta: "E se a {ticker} fechar a R$ {preco} no vencimento?",
      ese_melhora: "Neste preço, a estrutura melhora o resultado em R$ {d}.",
      ese_reduz: "Neste preço, a estrutura reduz o resultado em R$ {d}.",
      ese_igual: "Neste preço, a estrutura não muda o resultado.",
      tabela_ver: "Ver os números",
      tabela_preco: "Preço no vencimento",
      tabela_so_acoes: "Só as ações",
      tabela_com_estrutura: "Com a estrutura",
      comparar_rotulo: "Comparar vencimentos",
      comparar_custo: "até {n} consultas (2×{k}+1) · restam {x} hoje",
      cota_esgotada: "Cota de consultas do dia esgotada. Renova {quando}. A leitura acima segue valendo.",
      consultando: "consultando…",
      matriz_sem_dado: "—",
      matriz_so_comparacao: "Vencimento só para comparar: a execução simulada usa {lista}.",
      matriz_pior: "pior caso",
      matriz_ganho: "ganho máx.",
      sem_estrutura: "Sem estrutura disponível para {ticker} neste vencimento",
      sem_estrutura_dica: "Tente outro vencimento ou monte do zero.",
      // Fase 48 gap G-01/G-02 (2026-10-05): namespace OPCOES_ESCADA; não colide com sem_vencimento_elegivel da Fase 44 em OPCOES_LASTREADAS.
      sem_vencimento_elegivel: "{ticker}: nenhum vencimento futuro lido ({vencimentos}). Sem estrutura guiada.",
      sem_vencimento_elegivel_dica: "Objetivos voltam quando houver vencimento futuro. Outro vencimento agora: Montar do zero.",
      objetivo_indisponivel_ver_motivo: "{objetivo} indisponível pelo motivo acima.",
      pernas_titulo: "Pernas abertas",
      pernas_linha: "{tipo} {lado} · K R$ {strike} · venc {vencimento} · {qtd}",
      pernas_premio: "Entrada R$ {entrada} · agora R$ {atual}",
      pernas_resultado: "Resultado: {valor}",
      perna_lado_compra: "comprada",
      perna_lado_venda: "vendida",
      pernas_carregando: "Lendo resultado das pernas…",
      pernas_encerrar: "Encerrar",
      pernas_encerrar_aria: "Encerrar a perna {id}",
      pernas_confirmar: "Encerrar {id}? Venda simulada pelo último prêmio da fonte; nenhuma ordem real sai.",
      pernas_confirmar_sim: "Confirmar encerramento",
      pernas_cancelar: "Cancelar",
      pernas_encerrando: "Encerrando…",
      pernas_na_estrutura: "Perna de estrutura com lastro: encerre pelo painel da estrutura.",
      pernas_vendida_sem_acao: "Perna vendida: recompra fora desta lista.",
      // Fase 49 (2026-10-06): espelho de skill_ref.OPCOES_ESCADA anat_*.
      anat_titulo_posicao: "Posição em {ticker}",
      anat_sub_posicao: "Resultado no vencimento por perna e no total. O preço escolhido é hipótese, não previsão.",
      anat_total_titulo: "Payoff no vencimento ({vencimento})",
      anat_total_titulo_sem_data: "Payoff no vencimento",
      anat_chips_aria: "Pernas no total",
      anat_chip_perna: "{tipo} {strike}",
      anat_chip_acoes: "Ações ({qtd})",
      anat_slider_rotulo: "{ticker} a R$ {preco} no vencimento (hipótese, não previsão)",
      anat_leitura_total: "Em R$ {preco}: total {valor}.",
      anat_leitura_com_sem: "Em R$ {preco}: com {id} {com}; sem {id} {sem}; contribuição {contrib}.",
      anat_sem_esta_vazio: "Sem {id}: nada marcado.",
      anat_acoes_dentro: "Inclui {qtd} ações a PM R$ {pm} (simulador).",
      anat_acoes_fora_sem_pm: "Ações fora do total: sem preço médio no simulador. Nada estimado.",
      anat_total_vencimentos_diferentes: "Não há dados suficientes para concluir. Vencimentos diferentes ({vencimentos}): sem payoff único. Veja cada perna.",
      anat_total_sem_data: "Não há dados suficientes para concluir. Perna sem data de vencimento: sem payoff único. Veja cada perna.",
      anat_total_vazio: "Nada marcado.",
      anat_total_aria: "Payoff total no vencimento de {ticker}: {n} perna(s){acoes}. Valores na tabela.",
      anat_total_aria_acoes: " + {qtd} ações",
      anat_pernas_titulo: "Pernas",
      anat_objetivos_titulo: "Objetivo para a posição",
      anat_frase_call_compra: "Pagou R$ {valor} ({premio} × {qtd}) pelo direito de comprar {qtd} {ticker} a R$ {strike} até {vencimento}. Perda máxima: o prêmio pago.",
      anat_frase_put_compra: "Pagou R$ {valor} ({premio} × {qtd}) pelo direito de vender {qtd} {ticker} a R$ {strike} até {vencimento}. Perda máxima: o prêmio pago.",
      anat_frase_call_venda: "Recebeu R$ {valor} ({premio} × {qtd}); obrigado a vender {qtd} {ticker} a R$ {strike} se exercido até {vencimento}.",
      anat_frase_put_venda: "Recebeu R$ {valor} ({premio} × {qtd}); obrigado a comprar {qtd} {ticker} a R$ {strike} se exercido até {vencimento}.",
      anat_cond_call_compra: "Positivo acima de R$ {equilibrio} no vencimento.",
      anat_cond_put_compra: "Positivo abaixo de R$ {equilibrio} no vencimento.",
      anat_cond_call_venda: "Positivo abaixo de R$ {equilibrio} no vencimento.",
      anat_cond_put_venda: "Positivo acima de R$ {equilibrio} no vencimento.",
      anat_prazo_dias: "{dias} dias ({vencimento})",
      anat_prazo_amanha: "vence amanhã ({vencimento})",
      anat_prazo_hoje: "vence hoje ({vencimento})",
      anat_prazo_vencida: "vencida ({vencimento})",
      anat_prazo_sem_data: "Prazo: — (sem data no simulador)",
      anat_rotulo_pior: "Perda máx.",
      anat_rotulo_equilibrio: "Equilíbrio",
      anat_rotulo_hoje: "Agora",
      anat_pior_ilimitado: "ilimitada",
      anat_pior_ilimitado_nota: "Perda sem teto na alta de {ticker}.",
      anat_sem_cotacao_chip: "Sem cotação",
      anat_hoje_fonte_indisponivel: "Sem valor agora: fonte de opções fora. Nada estimado.",
      anat_hoje_fora_da_cadeia: "Sem valor agora: contrato fora da cadeia lida. Nada estimado.",
      anat_hoje_sem_negocio: "Sem valor agora: contrato sem bid, ask ou último negócio. Nada estimado.",
      anat_hoje_sem_cotacao: "Sem cotação agora. Nada estimado.",
      anat_hoje_sem_estrutura: "Sem leitura de cotação da posição. Nada estimado.",
      anat_hoje_nota: "Payoff no vencimento independe de cotação; só Agora depende.",
      anat_ver_sem_esta: "Comparar sem esta perna",
      anat_ver_total: "Ver total",
      anat_ver_tabela: "Ver em tabela",
      anat_tabela_preco: "{ticker} no venc.",
      anat_tabela_perna: "Resultado",
      anat_tabela_total: "Total marcado",
      anat_perna_aria: "Payoff de {id}: perda máx. {pior}, equilíbrio R$ {equilibrio}.",
      anat_dados_insuficientes: "Não há dados suficientes para concluir. Perna sem strike, prêmio ou quantidade.",
      anat_confirmar_com_cotacao: "Encerrar {id}? Venda simulada; último prêmio lido R$ {premio}, resultado agora {resultado}. O valor exato sai do prêmio na hora da ordem simulada. Nenhuma ordem real sai.",
      anat_confirmar_sem_cotacao: "Encerrar {id}? Venda simulada. Sem cotação agora: não dá para calcular o caixa. Nenhuma ordem real sai.",
      anat_carregando: "Calculando payoff…",
      anat_recalculando: "Recalculando…",
      anat_desatualizado: "Leitura possivelmente desatualizada (releitura falhou). Total oculto. Nada estimado.",
      anat_erro: "Payoff indisponível agora. Nada estimado. Pernas e Encerrar abaixo.",
      anat_legenda_perda: "Hachura: perda",
      anat_legenda_ganho: "Liso: ganho",
      anat_marcador_strike: "K {strike}",
      anat_marcador_equilibrio: "eq.",
      anat_marcador_pm: "PM",
      anat_marcador_hoje: "agora",
      anat_sem_pernas: "Sem pernas em {ticker}.",
      erro_fonte: "Opções fora do ar. Nenhum valor foi estimado. Tente de novo; se persistir, a fonte está indisponível.",
      tentar_de_novo: "Tentar de novo",
      carregando: "Carregando",
      mercado_fechado: "Pregão fechado: estes valores são de {data}, não de agora.",
      frescor: "{fonte} · pregão {data} · {situacao}",
      situacao_em_dia: "em dia",
      situacao_atrasado: "atrasado",
      situacao_fim_pregao: "fim de pregão",
      atrasado_frase: "não é o preço de agora",
      dado_insuficiente: "Não há dados suficientes para concluir.",
      aviso_virtual: "Dinheiro virtual: nenhuma ordem sai para corretora, bolsa ou banco.",
      hub_atencao: "Atenção",
      hub_carteira: "Sua carteira",
      hub_aviso_custo: "Abrir um ativo não gasta consultas.",
      hub_atualizar: "atualizar ›",
      hub_atualizar_custo: "o estado do dia custa {n} consultas",
      hub_nenhum_armado: "Nenhum vigia armado hoje.",
      card_subtitulo: "{qtd} ações · {livres} livres para lastro",
      card_subtitulo_sem_acoes: "sem ações deste ativo · opção sem lastro",
      card_estrutura_aberta: "estrutura aberta: {nome}",
      card_sem_estrutura: "nenhuma estrutura aberta",
      card_vigias: "{n} vigia(s)",
      hub_vazio_titulo: "Você ainda não tem ações em carteira",
      hub_vazio_corpo: "Opções são estudadas sobre as ações da carteira virtual. Abra uma posição simulada e volte.",
      hub_vazio_cta: "Ver Carteira",
      voltar: "‹ voltar",
      cta_escolher: "Escolher este",
      sem_custo: "sem custo",
      confirmar_titulo: "Confirmar estrutura",
      confirmar_estrutura: "Estrutura",
      confirmar_vencimento: "Vencimento",
      perna_put_comprada: "Put comprada: strike R$ {strike}, paga R$ {premio} por ação",
      perna_call_vendida: "Call vendida: strike R$ {strike}, recebe R$ {premio} por ação",
      confirmar_lote: "{contratos} contrato(s) · {qtd} ações",
      lastro_trava: "{qtd} ações ficam travadas como lastro",
      lastro_livre: "sem lastro: ações livres",
      cta_executar: "Executar (simulado)",
      cta_criar_vigia: "Criar vigia",
      estudo_nao_executa: "Modo Estudo não executa: esta é a leitura da estrutura.",
      ordem_rejeitada: "Ordem rejeitada: {motivo}",
      toast_executada: "Ordem simulada registrada. Nenhuma ordem real foi enviada.",
    },
    // Fase 48: texto de front da Ajuda/tour (consumido em App.jsx pelo plano 48-11).
    opcoesTourPasso: "A aba Opções trabalha as ações da sua Carteira: escolha o ativo, defina o objetivo, compare a escada e o gráfico do resultado no vencimento — leitura de fim de pregão, sem ordem nenhuma.",
    opcoesAjudaEstuda: "Estuda **opções** sobre as ações que você tem na Carteira: ativo, objetivo, escada de estruturas por vencimento e gráfico do resultado no vencimento, com pior caso e melhor caso à vista.",
    // Fase 46 (CART6-06/07): espelho byte a byte de skill_ref.CARTAO_POSICAO.
    // Texto novo nasce no .py primeiro; guardião test_cartao_posicao_espelho.mjs.
    cartaoPosicao: {
      face_acao: "Ação",
      face_opcoes: "Opções ({n})",
      face_grupo_aria: "Face do card {ticker}",
      plano_titulo: "Plano da ação",
      compras_titulo: "Compras ({n})",
      ver: "Ver ▾",
      ocultar: "Ocultar ▴",
      compras_indisponivel: "Compras: indisponível nesta fonte",
      compras_sem_detalhe: "Detalhes das compras não vieram nesta fonte — nada foi inferido.",
      falta_definir: "Falta definir",
      estado_sem_plano: "Sem stop e alvo — defina o plano",
      avulsa_sem_acoes: "Sem ações deste ativo: só a opção está aberta.",
      estado_falta_alvo: "Falta o alvo — plano incompleto",
      estado_falta_stop: "Falta o stop — plano incompleto",
      estado_abaixo_stop: "Abaixo do stop do plano",
      estado_acima_alvo: "Acima do alvo do plano",
      estado_dentro: "Dentro do plano",
      estado_travadas_todas: "Ações travadas pela call · saída após encerrar",
      estado_travadas_parcial: "{n} de {m} ações travadas · {k} livres",
      extra_resultado_parcial: "Resultado parcial: um prêmio atual indisponível",
      extra_cotacao_indisponivel: "Cotação atual indisponível nesta fonte",
      plano_ia_definir: "Definir plano · IA",
      plano_ia_completar: "Completar plano · IA",
      plano_ia_ajustar: "Ajustar plano · IA",
      reanalisar: "Reanalisar",
      historico: "Histórico de análises ({n})",
      kicker_ia: "✦ BÓRIS IA",
      encerrar: "Encerrar opção em Opções",
      atualizar: "↻ Atualizar",
      origem_nao_informada: "Origem da cotação não informada",
      sem_cenario: "Cenários não calculados para esta combinação. Os limites dependem do cálculo do app.",
      conta_sem_formula: "Calculado pela camada de opções do app",
      aguardando_calculo: "aguardando o cálculo do app",
      piso: "Piso",
      equilibrio_rotulo: "◆ Equilíbrio",
      teto: "Teto",
      sem_piso: "sem piso",
      sem_teto: "sem teto",
      agora: "agora",
      hoje: "hoje",
      faixa_titulo: "No vencimento ({ddmm})",
      chip_hoje: "Hoje",
      chip_equilibrio: "Equilíbrio",
      chip_teto: "Teto",
      chip_alta_forte: "Alta forte",
      rr_atual: "R:R atual",
      em_operacao: "Em operação",
      do_capital: "Do capital",
      cotacao_atual: "Cotação atual",
      setup_entrada: "Setup de entrada",
      gatilho_valido: "válido",
      gatilho_invalidado: "invalidado",
      nota_pm: "PM R$ {pm} = R$ {total} ÷ {qtd} ações (média ponderada).",
      nota_pm_vendas: " Vendas parciais reduzem a quantidade, não o PM.",
      editar_plano: "✎ Editar stop/alvo",
      regua_aria: "{ticker}: stop R$ {stop}, alvo R$ {alvo}, preço médio R$ {pm}, agora {agora}.",
      faixa_aria: "{ticker} no vencimento: piso {piso}, equilíbrio R$ {be}, teto {teto}, hoje {hoje}.",
      leg_hoje: "┆ hoje {v}",
      leg_be: "◆ BE {v}",
      leg_k: "┆ K {v}",
      leg_eixo: "eixo x: {lo} → {hi}",
      cel_be: "BE",
      cel_ate_be: "Até BE",
      cel_ate_k: "Até K",
      cel_ganho_max: "Ganho máx.",
      cel_perda_max: "Perda máx.",
      cel_lastro: "Lastro",
      conta_be_call: "BE = PM − prêmio",
      conta_ate_be: "Até BE = BE ÷ hoje − 1",
      conta_ate_k: "Até K = K ÷ hoje − 1",
      conta_ganho_call: "Ganho máx. = (K − BE) × qtd",
      conta_perda_call: "Perda máx. = BE × qtd (ação a zero)",
      conta_lastro: "Lastro = ações que cobrem a CALL vendida",
      sim_aria: "Preço de {ticker} no vencimento",
      sim_valuetext: "R$ {preco}; {resultado}; {zona}",
      payoff_sem_custos: "sem custos",
      zona_rotulo_perda_travada: "perda limitada",
      zona_rotulo_prejuizo: "prejuízo",
      zona_rotulo_ganho: "ganho",
      zona_rotulo_ganho_travado: "ganho limitado",
      saida_motivo_lastro: "Todas as ações estão travadas como lastro. Para sair do ativo, encerre a CALL vendida em Opções.",
      rodape_fechar: "Fechar ▴",
      rodape_abrir: "Detalhes e ações ▾",
      saida: "Registrar saída",
      saida_sem_livres: "Registrar saída · 0 ações livres",
      apoio_saida: "Saída simulada com dinheiro virtual. Nenhuma ordem é enviada à corretora.",
      sim_lead: "{ticker} em {ddmm}:",
      sim_resultado: "resultado",
      sim_metodo: "Sem custos. Resultado no vencimento.",
      payoff_titulo: "Payoff no vencimento · {ddmm}",
      payoff_aria: "Payoff de {ticker} no vencimento: prejuízo abaixo do BE R$ {be}; acima do teto R$ {teto} o resultado fica limitado ({ganhoMaximo}); perda máxima {perdaMaxima}.",
      payoff_aria_sem_teto: "Payoff de {ticker} no vencimento: prejuízo abaixo do BE R$ {be}; sem teto; perda máxima {perdaMaxima}.",
      zona_perda_travada: "Abaixo do piso R$ {piso}: perda limitada a R$ {perdaMaxima}.",
      zona_prejuizo_sem_piso: "Abaixo do BE R$ {be}: prejuízo. Sem piso (ação a zero: perda de R$ {perdaMaxima}).",
      zona_prejuizo_com_piso: "Entre o piso R$ {piso} e o BE R$ {be}: prejuízo, limitado pelo piso.",
      zona_ganho: "Entre o BE R$ {be} e o teto R$ {teto}: o resultado acompanha a ação.",
      zona_ganho_sem_teto: "Acima do BE R$ {be}, sem teto.",
      zona_ganho_travado: "Acima do teto R$ {teto}: resultado limitado em R$ {ganhoMaximo}; ações entregues a R$ {teto}.",
      // 46-UAT (2026-10-01, G-01..G-06): card fechado rótulo/valor, chips e faixa ancorada
      legenda_resultado: "resultado",
      legenda_resultado_variacao: "resultado · {pct}",
      legenda_resultado_estrutura: "resultado da estrutura",
      chip_total_suspenso: "total suspenso",
      linha_acoes: "Ações",
      linha_opcoes: "Opções · {contrato}",
      linha_estrutura: "Estrutura",
      motivo_premio_indisponivel: "prêmio indisponível",
      motivo_dados_incompletos: "dados incompletos",
      motivo_aguardando_premio: "aguardando prêmio",
      motivo_aguardando_cotacao: "aguardando cotação",
      motivo_cotacao_indisponivel: "cotação indisponível",
      chip_acoes_pm: "{qty} ações · PM {pm}",
      chip_vence: "vence {ddmm} · {dias}d",
      chip_plano: "stop {stop} · alvo {alvo}",
      chip_estrategia_generica: "estratégia não classificada",
      faixa_rot_be: "◆ BE {v}",
      faixa_rot_teto: "teto {v}",
      faixa_leg_hoje: "● hoje {v}",
      // # 46.1 (2026-10-02, G-08/AL-02/MD-02/MD-05): causas da suspensão, estados da leitura, legenda só ações, aria teto parcial.
      motivo_lendo: "atualizando",
      motivo_leitura_indisponivel: "leitura indisponível",
      chip_desatualizado: "desatualizado",
      tentar_de_novo: "↻ Tentar de novo",
      legenda_resultado_so_acoes: "resultado · só ações",
      leitura_falhou: "Leitura da posição indisponível agora · números suspensos",
      leitura_desatualizada: "Leitura das {hora} · não atualizou, números podem estar defasados",
      causa_sem_cotacao: "Sem cotação de {contratos} nesta fonte · total suspenso",
      causa_fora_da_cadeia: "{contratos} não veio na cadeia desta fonte · total suspenso",
      causa_sem_negocio: "Sem oferta nem último negócio para {contratos} nesta fonte · total suspenso",
      causa_fonte_indisponivel: "Fonte de opções indisponível para {contratos} · total suspenso",
      payoff_aria_teto_parcial: "Payoff de {ticker} no vencimento: prejuízo abaixo do BE R$ {be}; teto R$ {teto} cobre só parte das ações, ganho máximo não calculado; perda máxima {perdaMaxima}.",
    },
    linhaPropostaNaPosicao: "Estrutura de opções disponível nesta posição",

    // Fase 32 (32-01, D-05): mesma chave do ramo estudo (ver comentário
    // acima) — texto IDÊNTICO nos dois modos DE PROPÓSITO (constatação de
    // fato sobre dois motores determinísticos, não voz de personagem).
    duasLeiturasIntro: "Duas leituras diferentes da sua carteira — nenhuma é mais certa que a outra: uma parte do que a leitura técnica confirma agora, a outra varre a cadeia inteira sem exigir essa confirmação.",

    // Fase 32 (32-01, D-01/D-02/D-03): mesma chave do ramo estudo (ver
    // comentário acima) — texto IDÊNTICO nos dois modos.
    // Fase 39 (NAV-01, D-02/D-03): reescrito, mesmo motivo do ramo estudo
    // (ver comentário lá) — a contagem é da aba Recomendadas.
    // Fase 39-06: mesma renomeação do ramo estudo (ver comentário lá).
    linhaChamadaOpcoesTexto: (n) => n === 1
      ? "1 estrutura destacada nas suas posições"
      : `${n} estruturas destacadas nas suas posições`,
    linhaChamadaOpcoesVazia: "Nenhuma estrutura destacada agora",
    linhaChamadaOpcoesCarregando: "Verificando estruturas destacadas…",
    linhaChamadaOpcoesErro: "Não foi possível verificar agora — toque para ver na aba Opções",
    linhaChamadaOpcoesAria: (texto) => `${texto} — abrir aba Opções`,

    // Fase 30 (Plano 04, D4): mesma chave do ramo estudo (ver comentário
    // acima). Voz de mesa, sem verbo de ordem, sem promessa de lucro.
    //
    // Fase 31 (Plano 04, D-04): mesma reescrita/extensão do ramo estudo
    // (ver comentário acima) — voz de mesa, curta.
    // Fase 39 (NAV-01, D-01/D-08/D-09): reescrito, mesmo motivo do ramo
    // estudo (ver comentário lá) — voz de mesa, curta.
    curadoriaTitulo: "AS 4 PRIMEIRAS DO RANKING",
    // Fase 39 (NAV-01, D-08/D-09): reescrito de novo, mesmo motivo do ramo
    // estudo (ver comentário lá) — voz de mesa.
    curadoriaSubtitulo: "Candidatos com ≥ 60% de chance estimada (Black-Scholes) de terminar OTM, ordenados por prêmio anualizado — um critério entre outros, não promessa de resultado nem leitura mais certa que Oportunidades. Inclui o que a leitura técnica ainda não confirma. Ordem do motor; a IA não reordena.",
    curadoriaCarregando: "Varrendo a carteira…",
    curadoriaVazio: "Nenhuma estrutura elegível nos vencimentos varridos — sem nada para ranquear agora.",
    // Fase 39 (NAV-01, D-08/D-11): mesmo motivo do ramo estudo (ver
    // comentário lá) — voz de mesa.
    curadoriaVazioPiso: (pct) =>
      `Nenhum candidato com ≥ ${pct}% de chance estimada de terminar OTM hoje — nenhum passou no piso desta lista, o que não é o mesmo que não haver oportunidade.`,
    curadoriaVazioSemProb: "Não há dados suficientes para concluir: sem volatilidade para estimar a chance OTM dos candidatos de hoje — lista vazia por falta de dado, não por reprovação.",
    curadoriaPosicaoRotulo: (pos, total) => pos + "ª de " + total,
    curadoriaProbOtmRotulo: "Prob. estimada OTM",
    curadoriaPremioAnualizadoRotulo: "Prêmio anualizado",
    curadoriaVolImplicita: "vol. implícita",
    curadoriaVolHistorica: "vol. histórica de 21 pregões",
    // Fase 32 (32-01): mesma correção de estado do ramo estudo (ver
    // comentário acima) — texto IDÊNTICO nos dois modos.
    curadoriaErroBusca: "Não foi possível varrer sua carteira agora. Isto não significa que não há oportunidade — significa que a busca falhou. Toque para tentar de novo.",
    curadoriaErroBuscaCta: "Tentar de novo",
    // Fase 37 (37-02, D-04): renomeado, mesmo motivo do ramo estudo (ver
    // comentário lá) — mesa fala curto.
    curadoriaRazaoRotulo: "Pontuação de curadoria",
    curadoriaRazaoAjuda: "Prêmio negativo = a estrutura custa para montar (proteção) — por isso pode aparecer embaixo na régua.",
    // Quick 260915-ndt: mesmo defeito/motivo do ramo estudo (ver comentário
    // acima) — chave separada para o prêmio em reais do painel inline.
    // Mesa fala curto: o sinal já está no número.
    curadoriaPremioRotulo: "prêmio líquido",
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

    // Quick 260915-j5l: mesma chave do ramo estudo (ver comentário acima).
    // Voz de mesa, curta, sem verbo de ordem.
    curadoriaExecutarCta: "Executar estrutura",
    curadoriaExecutando: "Executando…",
    curadoriaFechar: "Fechar",
    curadoriaExecutada: "Executada — veja a posição na carteira.",
    curadoriaLiquidezConsentir: "Ciente: esta opção negociou pouco hoje, o preço pode se mover contra a execução.",
    curadoriaEstudoNaoExecuta: "Modo Estudo não executa operações — esta é a leitura de como a estrutura funcionaria.",
    curadoriaVerPosicao: "Ver posição",
  },
};

// Acesso seguro: modo desconhecido cai no Estudo (padrão do app).
export function copyFor(mode) {
  return COPY[mode === "operador" ? "operador" : "estudo"];
}

// Espelho de `skill_ref.estrutura_card_txt` (Fase 45): resolve o modo como
// `copyFor`; chave ausente devolve null (falha fechada); interpola `{k}` de
// `vals` por String(v). Sem `vals`, devolve a frase crua.
export function estruturaCardTxt(mode, chave, vals) {
  const frase = copyFor(mode).estruturaCard[chave];
  if (frase == null) return null;
  if (!vals) return frase;
  let out = frase;
  for (const [k, v] of Object.entries(vals)) out = out.split("{" + k + "}").join(String(v));
  return out;
}

// Espelho de `skill_ref.opcoes_escada_txt` (Fase 48): mesma semântica de
// `cartaoPosicaoTxt` (modo via `copyFor`; chave ausente -> null; interpolação
// de `{k}` por String(v)).
export function opcoesEscadaTxt(mode, chave, vals) {
  const frase = copyFor(mode).opcoesEscada[chave];
  if (frase == null) return null;
  if (!vals) return frase;
  let out = frase;
  for (const [k, v] of Object.entries(vals)) out = out.split("{" + k + "}").join(String(v));
  return out;
}

// Espelho de `skill_ref.cartao_posicao_txt` (Fase 46): mesma semântica de
// `estruturaCardTxt` (modo via `copyFor`; chave ausente -> null; interpolação
// de `{k}` por String(v)).
export function cartaoPosicaoTxt(mode, chave, vals) {
  const frase = copyFor(mode).cartaoPosicao[chave];
  if (frase == null) return null;
  if (!vals) return frase;
  let out = frase;
  for (const [k, v] of Object.entries(vals)) out = out.split("{" + k + "}").join(String(v));
  return out;
}

// Espelho de `skill_ref.cartao_didatica_txt` (Fase 46, D-11): só Estudo; o
// Operador não tem camada didática. Chave ausente -> null.
export function cartaoDidaticaTxt(chave, vals) {
  const frase = COPY.estudo.cartaoDidatica[chave];
  if (frase == null) return null;
  if (!vals) return frase;
  let out = frase;
  for (const [k, v] of Object.entries(vals)) out = out.split("{" + k + "}").join(String(v));
  return out;
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

// Espelho de `skill_ref.retorno_acumulado_txt` (quick 261006-dvf): frase do
// retorno acumulado por origem da base; estado desconhecido cai em sem_serie.
// vals: { pct, desde } — `desde` já formatado DD/MM/AAAA pelo chamador.
export function retornoAcumuladoTxt(mode, estado, vals) {
  const r = copyFor(mode).retornoAcumulado;
  const frase = r[estado] || r.sem_serie;
  return frase
    .replace("{pct}", (vals && vals.pct) || "—")
    .replace("{desde}", (vals && vals.desde) || "?");
}

// Espelho de `skill_ref.curva_evolucao_txt` (quick 261006-qre): legenda do trecho
// pré-janela da curva. vals: { desde } já formatado DD/MM/AAAA pelo chamador.
export function curvaEvolucaoTxt(mode, chave, vals) {
  const r = copyFor(mode).curvaEvolucao;
  const frase = r[chave] || r.antes_da_base;
  return frase.replace("{desde}", (vals && vals.desde) || "?");
}

// Espelho de skill_ref.reconciliacao_elegibilidade_txt (Fase 43, HIER-03) —
// só o FATO. A cláusula "por que importa" é exportada separada (constante
// fixa, sem interpolação), espelho de RECONCILIACAO_POR_QUE_IMPORTA.
//
// REVERSÃO DELIBERADA (2026-09-27, Fase 43, DP-3, checkpoint 43-05): a
// ausência de um dado que a frase do `estado` exige não vira mais "?" —
// espelho exato da queda em skill_ref.reconciliacao_elegibilidade_txt.
// `n == null` (nunca "0"), `!janela` e `typeof expR !== "number"` são
// ausência; se a frase contém o placeholder correspondente e ele falta,
// devolve nunca_medido do modo, sem interpolação. `n = 0` é valor
// presente (não cai).
export function reconciliacaoTxt(mode, estado, vals) {
  const d = copyFor(mode).reconciliacaoElegibilidade;
  const frase = d[estado] || d.nunca_medido;
  const n = vals && vals.n;
  const janela = vals && vals.janela;
  const expR = vals && typeof vals.expR === "number" ? vals.expR : null;
  const faltaN = frase.includes("{n}") && n == null;
  const faltaJanela = frase.includes("{janela}") && !janela;
  const faltaExpR = frase.includes("{expR}") && expR == null;
  if (faltaN || faltaJanela || faltaExpR) return d.nunca_medido;
  const expTxt = expR == null ? "" : (expR >= 0 ? "+" : "−") + Math.abs(expR).toFixed(3).replace(".", ",") + "R";
  return frase
    .replace("{n}", n != null ? String(n) : "")
    .replace("{janela}", janela || "")
    .replace("{expR}", expTxt);
}

// Fixa, sem interpolação, só Estudo (D-11/D-12) — HistoricoPill anexa isto
// como cláusula TOCÁVEL, nunca a compõe/parafraseia.
export const reconciliacaoPorQueImporta = "sinal técnico e histórico medido são coisas diferentes";
// Espelho byte a byte de skill_ref.RECONCILIACAO_POR_QUE_IMPORTA_ROTULO (Fase 47, DIDA-02).
export const reconciliacaoPorQueImportaRotulo = "a expectativa matemática";

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
