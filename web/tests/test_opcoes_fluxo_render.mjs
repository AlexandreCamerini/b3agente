// Fase 48 (48-10, 2026-10-05) — guardião de CONTRATO em runtime do caminho B.
// Os componentes de 48-08/48-09 só tinham sido parseados; aqui eles são
// renderizados de verdade (react-dom/server, sem DOM, via _jsx_loader) com o
// formato REAL que o backend/OpcoesScreen entrega, para provar que a fiação
// não depende de premissa errada (ex.: `pos.ticker` x `p.t`).
// Efeitos não rodam em SSR: o que se trava é a renderização por nível.
import { register } from "node:module";
import { createElement as h } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { COPY } from "../src/copy.js";

register("./_jsx_loader.mjs", import.meta.url);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const cp = COPY.estudo;
const HubOpcoes = (await import("../src/opcoes/HubOpcoes.jsx")).default;
const ObjetivoAtivo = (await import("../src/opcoes/ObjetivoAtivo.jsx")).default;
const EscadaObjetivo = (await import("../src/opcoes/EscadaObjetivo.jsx")).default;
const ConfirmarEstrutura = (await import("../src/opcoes/ConfirmarEstrutura.jsx")).default;
const MatrizVencimentos = (await import("../src/opcoes/MatrizVencimentos.jsx")).default;
const OpcoesScreen = (await import("../src/opcoes/OpcoesScreen.jsx")).default;

const html = (el) => renderToStaticMarkup(el);

// ---- Hub: carteira vem de ctx.data.positions ({t, qty}); OpcoesScreen mapeia p.t -> ticker
const carteira = [{ t: "PETR4", qty: 300, qtyTravada: 100 }, { t: "VALE3", qty: 100 }];
const hub = html(h(HubOpcoes, {
  cp, mode: "estudo",
  carteira: carteira.map((p) => ({ ...p, ticker: p.t })),
  opcoesPorTicker: { PETR4: { estrutura: { nome: "PETR4X1" } } },
  tecnicoPorTicker: {}, vigiasLista: [], vigiasComEstado: false,
  frescor: { fonte: "mcp", pregao: "2026-10-02", situacao: "fim_pregao", mercadoAberto: false, atrasado: false },
}));
ok("hub: um card por ativo da carteira (PETR4 e VALE3)", hub.includes("PETR4") && hub.includes("VALE3"));
ok("hub: nenhum card com 'undefined' (ticker mapeado de p.t)", !hub.includes("undefined"));
ok("hub: estrutura aberta aparece no rodapé do card", hub.includes("PETR4X1"));
ok("hub: aviso de dinheiro virtual presente", hub.toLowerCase().includes("virtual"));
ok("hub: sem vigias, a seção Atenção não aparece", !hub.includes(COPY.estudo.opcoesEscada.hub_atencao));

// ---- Objetivo: backend entrega `objetivos` (+ `termos` como MAPA, não array)
const escadaObj = { dados: { estado: "ok", posicao: { qty: 300 }, objetivos: [
  { id: "proteger", titulo: "Proteger de queda", descricao: "Compra uma put.", termos: { put: "put" }, disponivel: true },
  { id: "renda", titulo: "Gerar renda", descricao: "Vende uma call.", termos: {}, disponivel: false, motivo: "sem lote" },
  { id: "collar", titulo: "Proteger com custo baixo", descricao: "Collar.", termos: {}, disponivel: true },
] }, carregando: false, erro: null };
const obj = html(h(ObjetivoAtivo, { cp, mode: "estudo", ticker: "PETR4", escada: escadaObj, estruturaAberta: h("div", null, "PAINEL-ESTRUTURA") }));
ok("objetivo: 3 objetivos na ordem do backend", obj.indexOf("Proteger de queda") < obj.indexOf("Gerar renda") && obj.indexOf("Gerar renda") < obj.indexOf("Proteger com custo baixo"));
ok("objetivo: inviável fica aria-disabled com motivo escrito", obj.includes('aria-disabled="true"') && obj.includes("sem lote"));
ok("objetivo: painel da estrutura aberta é renderizado", obj.includes("PAINEL-ESTRUTURA"));
ok("objetivo: termos em formato mapa não quebram a renderização", obj.includes("Compra uma put."));

// ---- Escada: degrau com colunas, execucao.executavel controla o CTA
const degrau = (exec) => ({
  id: "d1", nome: "d1", rotulo: "Mais perto", strikes: { put: 30 }, fraseRisco: "Perde no máximo R$ 100,00.",
  execucao: exec,
  colunas: [{ chave: "perda", rotulo: "Pior caso", sinal: "negativo", fracao: 0.5, valor: { total: -100, porAcao: -1 } }],
});
const escadaDados = (d) => ({ dados: { estado: "ok", precoObjeto: 32.5, vencimento: "2026-11-21",
  vencimentos: [{ iso: "2026-11-21", texto: "21/11", dias: 40 }], degraus: [d], degrausAusentes: [],
  comparar: { vencimentos: ["2026-11-21"], chamadasPrevistas: 3, rotulo: "Comparar custa 3 consultas", restamHoje: 10 } },
  carregando: false, erro: null });
const base = { cp, mode: "estudo", ticker: "PETR4", objetivo: "proteger", unidade: "total", degrauId: "d1", vencimento: "2026-11-21" };
const escSem = html(h(EscadaObjetivo, { ...base, escada: escadaDados(degrau({ executavel: false })), comparar: { aberto: false, matriz: { dados: null, carregando: false, erro: null } } }));
ok("escada: CTA 'Escolher este' desabilitado sem execucao.executavel === true", /<button[^>]*disabled[^>]*>[^<]*Escolher/.test(escSem));
ok("escada: custo da comparação aparece ANTES do clique (rótulo do backend)", escSem.includes("Comparar custa 3 consultas"));
ok("escada: frase de risco do backend", escSem.includes("Perde no máximo R$ 100,00."));
const escOk = html(h(EscadaObjetivo, { ...base, escada: escadaDados(degrau({ executavel: true })), comparar: { aberto: false, matriz: { dados: null, carregando: false, erro: null } } }));
ok("escada: CTA habilitado com executavel === true", !/<button[^>]*disabled[^>]*>[^<]*Escolher/.test(escOk));

// ---- Matriz: célula sem dado vira travessão, nunca zero
const matriz = html(h(MatrizVencimentos, { cp, mode: "estudo", objetivo: "proteger", selecionado: null,
  matriz: { carregando: false, erro: null, dados: { fonte: "mcp", pregao: "2026-10-02", frescor: { medido: true },
    matriz: { proteger: [{ vencimento: "2026-11-21", celulas: [
      { id: "d1", total: { perdaMaxima: -100, premioPago: 50 } }, { motivo: "sem liquidez" }, null ] }] } } } }));
ok("matriz: célula com motivo mostra o motivo e é aria-disabled", matriz.includes("sem liquidez") && matriz.includes('aria-disabled="true"'));

// ---- Confirmar: Estudo não executa; Operador mostra CTA e usa origem 'escada'
const degConf = { ...degrau({ executavel: true, tipo: "put_protetora", contractSymbol: "PETRX30", expiration: "2026-11-21", contratos: 1, qtyAcoes: 100 }), nome: "Put protetora", vencimentoTexto: "21/11" };
const confEstudo = html(h(ConfirmarEstrutura, { cp, mode: "estudo", operador: false, ticker: "PETR4", degrau: degConf, onExecutar: async () => {} }));
ok("confirmar: Estudo não tem botão de executar", !confEstudo.includes(COPY.estudo.opcoesEscada.cta_executar));
const confOp = html(h(ConfirmarEstrutura, { cp: COPY.operador, mode: "operador", operador: true, ticker: "PETR4", degrau: degConf, onExecutar: async () => {} }));
ok("confirmar: Operador com executavel === true mostra o CTA", confOp.includes(COPY.operador.opcoesEscada.cta_executar));

// ---- Tela real montada no hub (SSR do 1º render, sem efeitos): grafo de módulos + nível inicial
const ctx = {
  cp, store: {}, palette: {}, operador: false,
  data: { positions: carteira, optionPositions: [] },
  authUser: { permissions: [] }, A: {}, mercado: { aberto: false },
};
let tela = "";
try { tela = html(h(OpcoesScreen, { ctx })); } catch (e) { tela = "ERRO:" + e.message; }
ok("OpcoesScreen: 1º render abre no HUB com os cards da carteira (sem exceção)", !tela.startsWith("ERRO:") && tela.includes("PETR4") && tela.includes("VALE3"));
ok("OpcoesScreen: a barra de 3 sub-abas não existe mais", !tela.includes(cp.opcoesAbaOportunidades) && !tela.includes(cp.opcoesAbaRecomendadas));
const telaMontar = html(h(OpcoesScreen, { ctx: { ...ctx, opcoesAbaInicial: "montar" } }));
ok("OpcoesScreen: goOpcoes('montar') abre Montar do zero (kicker de Montar)", telaMontar.includes(cp.opcoesMontarTitulo));
const telaEncerrar = html(h(OpcoesScreen, { ctx: { ...ctx, opcoesAbrirTicker: "PETR4", data: { ...ctx.data, optionPositions: [{ id: "PETRX30", underlying: "PETR4", qty: 1 }] } } }));
ok("OpcoesScreen: 'Encerrar estrutura…' abre o objetivo do ativo", telaEncerrar.includes("PETR4") && telaEncerrar.includes(COPY.estudo.opcoesEscada.voltar));
const telaForaCarteira = html(h(OpcoesScreen, { ctx: { ...ctx, opcoesAbrirTicker: "ZZZZ3" } }));
ok("OpcoesScreen: abrirTicker fora da carteira cai no hub (T-48-36)", telaForaCarteira.includes("VALE3") && !telaForaCarteira.includes("ZZZZ3"));

if (fails) { console.log("\n" + fails + " falha(s)"); process.exit(1); }
console.log("\nOK");
