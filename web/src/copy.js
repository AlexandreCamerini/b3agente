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

export const COPY = {
  estudo: {
    // identidade
    marcaSufixo: "Estudo",
    chipModo: null, // sem chip — é o app padrão

    // saudação/tratamento (Acompanhar)
    saudacao: (nome) => (nome ? `Vamos estudar o mercado hoje, ${nome}?` : "Vamos estudar o mercado hoje?"),
    resumoDia: (nSetups, nGatilhos) =>
      nSetups > 0
        ? `Há ${nSetups} setup(s) para estudar na sua watchlist — bora entender o porquê de cada um?`
        : "Mercado sem setups claros na sua watchlist — bom dia para revisar os conceitos.",

    // abas
    tituloRadar: "Radar de mercado",
    subtituloRadar: "Varredura do universo com o motor de sinais: quais condições técnicas estão ativas em cada papel, para você estudar — sem qualquer recomendação.",
    tituloWatchlist: "Watchlist",
    tituloPortfolio: "Portfólio",
    subtituloPortfolio: "Sua carteira SIMULADA — dinheiro de estudo, decisões de verdade.",

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
  },

  operador: {
    // identidade
    marcaSufixo: "Operador",
    chipModo: "MODO OPERADOR",

    // saudação/tratamento (Acompanhar) — tom de mesa
    saudacao: (nome) => (nome ? `Mesa aberta, ${nome}.` : "Mesa aberta."),
    resumoDia: (nSetups, nGatilhos) =>
      nSetups > 0
        ? `${nSetups} plano(s) válido(s) hoje · ${nGatilhos} gatilho(s) próximos do preço. Disciplina: só entra quem confirmar.`
        : "Nenhum plano com vantagem estatística hoje. Não operar também é posição.",

    // abas
    tituloRadar: "Mesa de oportunidades",
    subtituloRadar: "Varredura do universo com decisão objetiva por ativo: plano de entrada, stop na invalidação, alvos e R:R — abaixo de 1,5:1 a mesa não opera.",
    tituloWatchlist: "Monitoramento",
    tituloPortfolio: "Posições",
    subtituloPortfolio: "Suas posições e o plano de cada uma — risco controlado em R, parciais no alvo 1.",

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

    // toasts/notificações
    toastCompra: (qty, t) => `Entrada registrada: ${qty} ${t}. Stop e alvo já definidos? Sem plano, sem posição.`,
    toastVenda: (desc, t) => `Saída registrada: ${desc} de ${t}. Anote o resultado em R.`,
    notifStopTitulo: (t) => `STOP executável · ${t}`,
    notifStopCorpo: (t, preco, stop) => `${t} a R$ ${preco} rompeu o stop de R$ ${stop}. Execute a saída na corretora — o plano manda.`,
    notifAlvoTitulo: (t) => `ALVO no preço · ${t}`,
    notifAlvoCorpo: (t, preco, alvo) => `${t} a R$ ${preco} tocou o alvo de R$ ${alvo}. Realize a parcial e suba o stop — disciplina.`,
    notifVarTitulo: (t) => `Movimento forte · ${t}`,
    notifVarCorpo: (t, ch, preco) => `${t} ${ch} no dia (R$ ${preco}). Confira se algum plano armado foi atingido.`,

    // rodapé/disclaimer
    disclaimer: DISCLAIMERS.operador,
    rodape: "Mesa de decisão — a execução e o risco são seus. Nenhuma ordem é enviada à corretora.",
  },
};

// Acesso seguro: modo desconhecido cai no Estudo (padrão do app).
export function copyFor(mode) {
  return COPY[mode === "operador" ? "operador" : "estudo"];
}
