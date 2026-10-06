// Fase 48 (48-10, 2026-10-05) — guardião de CONTRATO em runtime do caminho B.
// Os componentes de 48-08/48-09 só tinham sido parseados; aqui eles são
// renderizados de verdade (react-dom/server, sem DOM, via _jsx_loader) com o
// formato REAL que o backend/OpcoesScreen entrega, para provar que a fiação
// não depende de premissa errada (ex.: `pos.ticker` x `p.t`).
// Efeitos não rodam em SSR: o que se trava é a renderização por nível.
import { register } from "node:module";
import { createElement as h } from "react";
import { readFileSync } from "node:fs";
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
      // formato REAL de opcoes_escada.celulas_da_cadeia: id, pernas (tipo/lado/strike/premio/contrato), total, motivo
      { indice: 0, nome: "d1", id: "c1", pernas: [{ tipo: "PUT", lado: "compra", strike: 30, premio: 0.5, contrato: "PETRX30" }],
        total: { perdaMaxima: -100, premioPago: 50 }, motivo: null },
      { indice: 1, nome: "d2", id: null, pernas: null, total: null, motivo: "sem liquidez" }, null ] }] } } } }));
ok("matriz: célula real mostra os totais do backend formatados (R$ −100,00) e o travessão para ausente", matriz.includes("−100,00") && matriz.includes("—"));
ok("matriz: célula com motivo mostra o motivo e é aria-disabled", matriz.includes("sem liquidez") && matriz.includes('aria-disabled="true"'));

// ---- Confirmar: Estudo não executa; Operador mostra CTA e usa origem 'escada'
const degConf = { ...degrau({ executavel: true, tipo: "put_protecao", contractSymbol: "PETRX30", expiration: "2026-11-21", contratos: 1, qtyAcoes: 100 }), nome: "Put protetora", vencimentoTexto: "21/11" };
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
ok("OpcoesScreen: 'Encerrar estrutura…' abre o objetivo do ativo COM o painel da estrutura aberta (PropostaDoAtivo: 'Montar com PETR4')",
   telaEncerrar.includes(cp.opcoesMontarNoAtivo("PETR4")) && telaEncerrar.includes(COPY.estudo.opcoesEscada.voltar));
ok("OpcoesScreen: o hub NÃO mostra o painel de PropostaDoAtivo", !tela.includes(cp.opcoesMontarNoAtivo("PETR4")));
const telaForaCarteira = html(h(OpcoesScreen, { ctx: { ...ctx, opcoesAbrirTicker: "ZZZZ3" } }));
ok("OpcoesScreen: abrirTicker fora da carteira cai no hub (T-48-36)", telaForaCarteira.includes("VALE3") && !telaForaCarteira.includes("ZZZZ3"));

// ---- Fase 48 gap G-01 (2026-10-05): frase única de indisponibilidade + slot de pernas acima da escada
const objInd = (id, t) => ({ id, titulo: t, descricao: "d", termos: {}, disponivel: false, motivoChave: "sem_vencimento_elegivel", motivo: "M-REAL 09/10", dica: "D-REAL" });
const escadaG01 = { dados: { estado: "ok", posicao: { qty: 100 }, objetivos: [objInd("proteger", "Proteger de queda"), objInd("renda", "Gerar renda"), objInd("collar", "Collar")],
  objetivosMotivo: { chave: "sem_vencimento_elegivel", texto: "M-REAL 09/10", dica: "D-REAL" } }, carregando: false, erro: null };
const g01 = html(h(ObjetivoAtivo, { cp, mode: "estudo", ticker: "ITUB4", escada: escadaG01 }));
ok("G-01: motivo real aparece exatamente 1 vez", g01.split("M-REAL 09/10").length - 1 === 1);
ok("G-01: dica aparece", g01.includes("D-REAL"));
ok("G-01: 3 cards seguem aria-disabled", (g01.match(/aria-disabled="true"/g) || []).length === 3);
ok("G-01: cards apontam para a frase via aria-describedby", g01.includes('aria-describedby="objetivos-motivo-ITUB4"'));
ok("G-01: texto genérico sem_estrutura não aparece", !g01.includes(COPY.estudo.opcoesEscada.sem_estrutura.replace("{ticker}", "ITUB4")));
const g01Erro = html(h(ObjetivoAtivo, { cp, mode: "estudo", ticker: "ITUB4", escada: { dados: null, carregando: false, erro: "x" }, pernasAbertas: h("div", null, "SLOT-PERNAS") }));
ok("G-01: slot de pernas visível mesmo com a escada em erro", g01Erro.includes("SLOT-PERNAS") && g01Erro.includes(COPY.estudo.opcoesEscada.erro_fonte));

// ---- Fase 48 gap G-02 (2026-10-05): PernasAbertas (lista + encerrar por perna)
const PernasAbertas = (await import("../src/opcoes/PernasAbertas.jsx")).default;
const ox = COPY.estudo.opcoesEscada;
const posCall = { id: "ITUBJ492", underlying: "ITUB4", optionType: "call", strike: 49.2, expiration: "2026-10-09", qty: 100, avg: 0.85 };
const posPut = { id: "ITUBV465", underlying: "ITUB4", optionType: "put", strike: 46.5, expiration: "2026-10-09", qty: 100, avg: 0.85 };
const posLastro = { id: "ITUBJ500", underlying: "ITUB4", optionType: "call", strike: 50, expiration: "2026-10-09", qty: 100, avg: 0.5, lastro: { t: "ITUB4", qty: 100 } };
const posVendida = { id: "ITUBJ510", underlying: "ITUB4", optionType: "call", strike: 51, expiration: "2026-10-09", qty: 100, avg: 0.4, side: "vendida" };
const posOutra = { id: "PETRJ300", underlying: "PETR4", optionType: "call", strike: 30, expiration: "2026-10-09", qty: 100, avg: 0.3 };
const pernas = (props) => html(h(PernasAbertas, { mode: "estudo", ticker: "ITUB4", A: {}, ...props }));
ok("G-02: sem pernas do ticker renderiza vazio", pernas({ optionPositions: [posOutra] }) === "");
const p1 = pernas({ optionPositions: [posCall, posPut], estrutura: null });
ok("G-02: título e os dois ids", p1.includes(ox.pernas_titulo) && p1.includes("ITUBJ492") && p1.includes("ITUBV465"));
ok("G-02: resultado sem motor vira travessão, nunca 0,00", p1.includes("—") && !p1.includes("0,00"));
ok("G-02: botão Encerrar habilitado sem estrutura (2 botões)", (p1.match(new RegExp(">" + ox.pernas_encerrar + "<", "g")) || []).length === 2 && !/<button[^>]*disabled/.test(p1) && !p1.includes('aria-disabled="true"'));
ok("G-02: prêmio de entrada vem da posição (0,85) e data DD/MM", p1.includes("0,85") && p1.includes("09/10"));
const p2 = pernas({ optionPositions: [posCall], estrutura: { pernas: [{ id: "ITUBJ492", resultado: -12.5, premioAtual: 0.4, encerrar: { permitido: true } }] } });
ok("G-02: resultado e prêmio atual do motor (−12,50 e 0,40)", p2.includes("−12,50") && p2.includes("0,40"));
const p3 = pernas({ optionPositions: [posCall], estrutura: { pernas: [{ id: "ITUBJ492", resultado: null, motivoSemCotacao: "SEM-COTACAO-MOTOR", encerrar: { permitido: true } }] } });
ok("G-02: resultado null mostra motivo do motor, sem 0,00", p3.includes("SEM-COTACAO-MOTOR") && !p3.includes("0,00"));
const p4 = pernas({ optionPositions: [posCall], estrutura: { pernas: [{ id: "ITUBJ492", resultado: null, encerrar: { permitido: false, texto: "VETO-DO-MOTOR" } }] } });
ok("G-02: encerrar.permitido false -> aria-disabled com texto do motor e describedby", p4.includes('aria-disabled="true"') && p4.includes("VETO-DO-MOTOR") && p4.includes("aria-describedby"));
const p5 = pernas({ optionPositions: [posLastro, posVendida] });
ok("G-02: lastro e vendida sem botão Encerrar", !p5.includes(">" + ox.pernas_encerrar + "<") && p5.includes(ox.pernas_na_estrutura) && p5.includes(ox.pernas_vendida_sem_acao));
ok("G-02: perna de PETR4 ausente na lista de ITUB4", !pernas({ optionPositions: [posCall, posOutra] }).includes("PETRJ300"));
ok("G-02: componente não decide botão por frescor/executavel/liquida", !/executavel|frescor|liquida/.test(readFileSync(new URL("../src/opcoes/PernasAbertas.jsx", import.meta.url), "utf8")));

if (fails) { console.log("\n" + fails + " falha(s)"); process.exit(1); }
console.log("\nOK");
