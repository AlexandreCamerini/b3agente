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
    tabOpcoes: "Opções",
    tituloOpcoes: "Opções",
    subtituloOpcoes: "Como o ativo vem se comportando e quais estruturas de opções fazem sentido estudar — leitura de fim de pregão, sem ordem nenhuma.",
    tituloOperadorIA: "Operador IA",
    linkOperadorIA: "Abrir o Operador IA →",
    opcoesLeituraTitulo: "LEITURA DO ATIVO",
    opcoesSetupsTitulo: "SETUPS GRAVADOS",
    opcoesPregaoRotulo: "Pregão",
    opcoesFonteRotulo: "Fonte",
    opcoesFrescorEmDia: "dado em dia",
    opcoesFrescorAtrasado: "dado atrasado",
    opcoesFrescorNaoMedido: "frescor não medido",
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
    opcoesEscolherAtivo: "Escolha um ativo da sua watchlist para ver a leitura dele.",
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
    opcoesCustoChamadas: (n) =>
      "Esta consulta gasta " + (typeof n === "number" ? n : "—") +
      " chamada(s) da sua cota do dia: uma para listar os vencimentos e duas para cada vencimento consultado.",
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
    opcoesDadoAtrasado: (idade, motivo) =>
      motivo === "nao_medido"
        ? "Não foi possível medir a idade do dado de negociação nesta consulta, e sem essa medição o setup não é gravado — ele vigiaria um pregão que ninguém conferiu."
        : "O dado de negociação da B3 está atrasado" +
          (idade === null || idade === undefined || idade === "" ? "" : " (" + idade + ")") +
          ": um setup criado agora vigiaria um pregão que já passou. Nada foi gravado.",

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
    // test_copy_theme.mjs compara os conjuntos ordenados).
    tabOpcoes: "Opções",
    tituloOpcoes: "Opções",
    subtituloOpcoes: "Comportamento do ativo, estruturas do catálogo e os setups armados — leitura de fim de pregão. Nenhuma ordem sai daqui.",
    tituloOperadorIA: "Operador IA",
    linkOperadorIA: "Abrir o Operador IA →",
    opcoesLeituraTitulo: "LEITURA DO ATIVO",
    opcoesSetupsTitulo: "SETUPS GRAVADOS",
    opcoesPregaoRotulo: "Pregão",
    opcoesFonteRotulo: "Fonte",
    opcoesFrescorEmDia: "dado em dia",
    opcoesFrescorAtrasado: "dado atrasado",
    opcoesFrescorNaoMedido: "frescor não medido",
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
    opcoesEscolherAtivo: "Escolha um ativo do seu monitoramento para ver a leitura.",
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
    opcoesCustoChamadas: (n) =>
      "Custo desta consulta: " + (typeof n === "number" ? n : "—") +
      " chamada(s) da cota do dia (1 para listar os vencimentos + 2 por vencimento).",
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
    opcoesDadoAtrasado: (idade, motivo) =>
      motivo === "nao_medido"
        ? "A idade do dado de negociação não foi medida nesta consulta. Sem medição, o setup não é gravado — ele vigiaria um pregão que ninguém conferiu."
        : "Dado de negociação da B3 atrasado" +
          (idade === null || idade === undefined || idade === "" ? "" : " (" + idade + ")") +
          ": um setup criado agora vigiaria um pregão que já passou. Nada foi gravado.",

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
