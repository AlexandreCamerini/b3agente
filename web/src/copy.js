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

    // abas
    tabRadar: "Radar", // qa/34: rótulo CURTO da aba inferior (a tela usa tituloRadar)
    tituloRadar: "Radar de mercado",
    subtituloRadar: "Varredura do universo com o motor de sinais: quais condições técnicas estão ativas em cada papel, para você estudar — sem qualquer recomendação.",
    tituloWatchlist: "Watchlist",
    subtituloWatchlist: "Seus ativos em estudo, ordenados por oportunidade (confluência do snapshot). A análise completa abre no card.",
    tituloPortfolio: "Portfólio",
    subtituloPortfolio: "Sua carteira SIMULADA — dinheiro de estudo, decisões de verdade.",

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

    // abas
    tabRadar: "Mesa", // qa/34: a aba dizia "Radar" enquanto a tela é "Mesa de oportunidades"
    tituloRadar: "Mesa de oportunidades",
    subtituloRadar: `Varredura do universo com decisão objetiva por ativo: plano de entrada, stop na invalidação, alvos e R:R — abaixo de ${RR_MIN_TXT}:1 a mesa não opera.`,
    tituloWatchlist: "Monitoramento",
    subtituloWatchlist: "Seus ativos monitorados, ordenados por oportunidade (confluência do snapshot). O plano de cada um abre no card.",
    tituloPortfolio: "Posições",
    subtituloPortfolio: "Suas posições e o plano de cada uma — risco controlado em R, parciais no alvo 1.",

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
