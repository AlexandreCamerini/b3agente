// Guardião — lógica pura do card v6 (Fase 46, plano 02).
// Roda isolado: `node web/tests/test_cartao_v6_logica.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import * as E from "../src/estruturaCard.js";

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// ancoraRotulo
ok("ancora 10 -> inicio", E.ancoraRotulo(10) === "inicio");
ok("ancora 21.9 -> inicio", E.ancoraRotulo(21.9) === "inicio");
ok("ancora 22 -> centro", E.ancoraRotulo(22) === "centro");
ok("ancora 50 -> centro", E.ancoraRotulo(50) === "centro");
ok("ancora 78 -> centro", E.ancoraRotulo(78) === "centro");
ok("ancora 78.1 -> fim", E.ancoraRotulo(78.1) === "fim");
ok("ancora não-número -> centro", E.ancoraRotulo("x") === "centro" && E.ancoraRotulo(null) === "centro" && E.ancoraRotulo(NaN) === "centro");

// rotulosSemColisao
const linhas = (itens) => E.rotulosSemColisao(itens).map((r) => r.linha);
ok("colisao longe", eq(linhas([{ id: "a", x: 10 }, { id: "b", x: 50 }]), [0, 0]));
ok("colisao perto", eq(linhas([{ id: "a", x: 40 }, { id: "b", x: 60 }]), [0, 1]));
ok("colisao 3 itens (0,1,0)", eq(linhas([{ id: "a", x: 40 }, { id: "b", x: 60 }, { id: "c", x: 90 }]), [0, 1, 0]));
ok("colisao 3 itens (0,1,2)", eq(linhas([{ id: "a", x: 40 }, { id: "b", x: 50 }, { id: "c", x: 60 }]), [0, 1, 2]));
ok("colisao preserva ordem e id", eq(E.rotulosSemColisao([{ id: "z", x: 10 }, { id: "y", x: 12 }]).map((r) => r.id), ["z", "y"]));
ok("colisao omite x inválido", eq(E.rotulosSemColisao([{ id: "a", x: null }, { id: "b", x: 10 }]).map((r) => r.id), ["b"]));
ok("colisao entrada inválida", eq(E.rotulosSemColisao(null), []));

// flipDuracaoMs / prefereMovimentoReduzido / faceInicial
ok("flip reduzido", eq(E.flipDuracaoMs(true), { saida: 0, entrada: 0, total: 0 }));
ok("flip normal", eq(E.flipDuracaoMs(false), { saida: 170, entrada: 170, total: 340 }));
let consultas = 0;
const winRed = { matchMedia: (q) => { consultas++; return { matches: q.includes("prefers-reduced-motion") }; } };
ok("movimento reduzido lê matchMedia", E.prefereMovimentoReduzido(winRed) === true && consultas === 1);
E.prefereMovimentoReduzido(winRed);
ok("movimento reduzido lê NA HORA (sem cache)", consultas === 2);
ok("movimento reduzido sem win", E.prefereMovimentoReduzido(undefined) === false && E.prefereMovimentoReduzido({}) === false);
ok("movimento reduzido matchMedia falso", E.prefereMovimentoReduzido({ matchMedia: () => ({ matches: false }) }) === false);
ok("faceInicial opções", E.faceInicial(2) === "opcoes");
ok("faceInicial ação", E.faceInicial(0) === "acao" && E.faceInicial(undefined) === "acao");

// estadoPrincipalV6
const P = (o) => ({ t: "UGPA3", qty: 1000, qtyTravada: 0, stop: 10, alvo: 20, ...o });
const est = (o) => ({ estado: "vigente", estadoTexto: "txt", resultado: { incompleto: false }, ...o });
const lp = (o) => ({ preco: 15, posicaoNoPlano: "dentro", ...o });
const ep = (a) => E.estadoPrincipalV6(a);

let r = ep({ p: P(), estrutura: est({ estado: "vencida", estadoTexto: "Vencida em 15/09" }), leituraPlano: lp() });
ok("vencida -> motor/encerrada", r.principal.chave === "motor" && r.principal.tom === "encerrada" && r.principal.glifo === "ⓘ" && r.principal.vals.texto === "Vencida em 15/09");
r = ep({ p: P(), estrutura: est({ estado: "exercicio_provavel", estadoTexto: "Exercício provável" }), leituraPlano: lp() });
ok("exercício provável -> motor/atenção", r.principal.chave === "motor" && r.principal.tom === "atencao" && r.principal.glifo === "⚠");
r = ep({ p: P({ qtyTravada: 1000 }), estrutura: est(), leituraPlano: lp() });
// 46-UAT (2026-10-01, G-03): glifo das travadas passou de "ⓘ" para "cadeado".
ok("travadas todas", r.principal.chave === "estado_travadas_todas" && r.principal.tom === "info" && r.principal.glifo === "cadeado" && r.extras.length === 0);
r = ep({ p: P({ qtyTravada: 400 }), estrutura: est(), leituraPlano: lp() });
ok("travadas parcial", r.principal.chave === "estado_travadas_parcial" && eq(r.principal.vals, { n: 400, m: 1000, k: 600 }) && r.principal.tom === "info" && r.principal.glifo === "cadeado");
r = ep({ p: P({ qtyTravada: 1000, stop: null, alvo: null }), estrutura: est(), leituraPlano: lp() });
ok("trava + sem plano: sem plano NÃO entra em extras (D-13)", r.principal.chave === "estado_travadas_todas" && !r.extras.some((x) => x.chave === "estado_sem_plano"));
r = ep({ p: P({ stop: null, alvo: null }), estrutura: null, leituraPlano: lp() });
ok("sem plano", r.principal.chave === "estado_sem_plano" && r.principal.tom === "atencao" && r.principal.glifo === "⚠");
r = ep({ p: P({ alvo: null }), estrutura: null, leituraPlano: lp() });
ok("só stop -> falta alvo", r.principal.chave === "estado_falta_alvo");
r = ep({ p: P({ stop: null }), estrutura: null, leituraPlano: lp() });
ok("só alvo -> falta stop", r.principal.chave === "estado_falta_stop");
r = ep({ p: P(), estrutura: null, leituraPlano: lp({ posicaoNoPlano: "abaixo_stop" }) });
ok("abaixo do stop", r.principal.chave === "estado_abaixo_stop" && r.principal.tom === "atencao");
r = ep({ p: P(), estrutura: null, leituraPlano: lp({ posicaoNoPlano: "acima_alvo" }) });
ok("acima do alvo", r.principal.chave === "estado_acima_alvo" && r.principal.tom === "atencao");
r = ep({ p: P(), estrutura: null, leituraPlano: lp() });
ok("dentro sem estrutura", r.principal.chave === "estado_dentro" && r.principal.tom === "neutro" && r.principal.glifo === "✓");
r = ep({ p: P(), estrutura: est(), leituraPlano: lp() });
ok("dentro com estrutura -> sem principal", r.principal === null);
// 46-UAT (2026-10-01, G-03): resultado parcial e prêmio indisponível saíram da linha de estado — a info vive na linha 'Opções · contrato' (linhasResultadoV6); asserção equivalente: extras vazio + motivo na linha
r = ep({ p: P(), estrutura: est({ resultado: { incompleto: true } }), leituraPlano: lp() });
ok("resultado parcial não é mais extra (G-03)", r.extras.length === 0 && r.principal === null);
r = ep({ p: P(), estrutura: null, leituraPlano: lp({ preco: null, posicaoNoPlano: null }) });
ok("cotação indisponível vira o ÚNICO estado (sem estrutura)", r.principal && r.principal.chave === "extra_cotacao_indisponivel" && r.principal.glifo === "ⓘ" && r.extras.length === 0);
r = ep({ p: P(), estrutura: est({ estado: "premio_indisponivel", estadoTexto: "Prêmio indisponível" }), leituraPlano: lp() });
ok("prêmio indisponível não é mais extra (G-03)", r.principal === null && r.extras.length === 0);
r = ep({ p: P({ qtyTravada: 1000 }), estrutura: est({ estado: "premio_indisponivel", resultado: { incompleto: true } }), leituraPlano: lp() });
ok("UGPA3: travadas + prêmio faltando -> um estado, extras vazio", r.principal.chave === "estado_travadas_todas" && r.principal.glifo === "cadeado" && r.extras.length === 0);
r = ep({ p: P(), estrutura: est({ estado: "ate_5_dias" }), leituraPlano: lp() });
ok("ate_5_dias não gera linha", r.principal === null && r.extras.length === 0);
r = ep({ p: P(), estrutura: null, leituraPlano: null });
ok("leituraPlano ausente não quebra", r.principal === null && Array.isArray(r.extras));
r = ep({ p: P({ stop: null, alvo: null }), estrutura: null, leituraPlano: null });
ok("leituraPlano ausente + sem plano ainda avisa", r.principal && r.principal.chave === "estado_sem_plano");
r = ep({ p: P(), estrutura: est({ estado: "exercicio_provavel", estadoTexto: "x" }), leituraPlano: lp({ posicaoNoPlano: "abaixo_stop" }) });
ok("risco do motor tem precedência sobre fora do plano", r.principal.chave === "motor");
ok("entrada vazia não quebra", ep({}).principal === null);

// 46-UAT (2026-10-01, G-01..G-05): helpers do card fechado
const L = (a) => E.linhasResultadoV6(a);
const perna = (o) => ({ id: "UGPAK422", resultado: 2390, ...o });
const resEst = (o) => ({ total: 1240, acoes: -1150, incompleto: false, pernasSemCotacao: [], pernasSemDados: [], ...o });
let q = L({ estrutura: { resultado: resEst(), pernas: [perna()] } });
ok("linhas call coberta completa", q.linhas.length === 3 && q.linhas[0].chave === "linha_acoes" && q.linhas[0].valor === -1150 && q.linhas[1].chave === "linha_opcoes" && q.linhas[1].vals.contrato === "UGPAK422" && q.linhas[1].valor === 2390 && q.linhas[2].chave === "linha_estrutura" && q.linhas[2].total === true && q.linhas[2].valor === 1240);
ok("cabeçalho = MESMA referência da linha Estrutura", q.cabecalho.valor === q.linhas[2].valor && q.cabecalho.legenda === "legenda_resultado_estrutura" && q.cabecalho.suspenso === false);
q = L({ estrutura: { resultado: resEst({ total: null, pernasSemCotacao: ["UGPAK422"] }), pernas: [perna({ resultado: null })] } });
ok("UGPA3 prêmio faltando: motivos e cabeçalho suspenso", q.linhas[1].valor === null && q.linhas[1].motivo === "motivo_premio_indisponivel" && q.linhas[2].valor === null && q.linhas[2].motivo === "motivo_aguardando_premio" && eq(q.cabecalho, { valor: null, legenda: null, vals: {}, suspenso: true }));
q = L({ estrutura: { resultado: resEst({ total: null, pernasSemDados: ["UGPAK422"] }), pernas: [perna({ resultado: null })] } });
ok("perna sem dados -> motivo_dados_incompletos", q.linhas[1].motivo === "motivo_dados_incompletos" && q.linhas[2].motivo === "motivo_dados_incompletos");
q = L({ estrutura: { resultado: resEst({ total: null, acoes: null }), pernas: [perna()] } });
ok("ação sem cotação -> aguardando cotação", q.linhas[0].motivo === "motivo_cotacao_indisponivel" && q.linhas[2].motivo === "motivo_aguardando_cotacao");
q = L({ estrutura: null, leituraPlano: { resultado: 120, variacaoPct: 2.1 }, pctCapital: 4.2 });
ok("ação simples: Ações + Do capital, sem Estrutura", q.linhas.length === 2 && q.linhas[0].valor === 120 && q.linhas[1].chave === "do_capital" && q.linhas[1].tipo === "pct" && q.linhas[1].valor === 4.2 && !q.linhas.some((x) => x.chave === "linha_estrutura") && q.cabecalho.legenda === "legenda_resultado_variacao" && q.cabecalho.vals.pct === 2.1);
q = L({ estrutura: null, leituraPlano: { resultado: 120, variacaoPct: 2.1 }, pctCapital: null });
ok("pctCapital null -> sem linha do_capital", q.linhas.length === 1);
ok("linhasResultadoV6 entrada vazia não quebra", L({}).cabecalho.suspenso === true);
ok("rsSinalNbsp", E.rsSinalNbsp(-123456.78) === "\u2212R$\u00a0123.456,78" && E.rsSinalNbsp(120) === "+R$\u00a0120,00" && E.rsSinalNbsp(0) === "R$\u00a00,00" && E.rsSinalNbsp(null) === "—");
ok("rsNbsp", E.rsNbsp(38.01) === "R$\u00a038,01" && E.rsNbsp(undefined) === "—");
ok("nenhum R$ com espaço comum", ![E.rsNbsp(1), E.rsSinalNbsp(-5), E.rsSinalNbsp(5)].some((t) => t.includes("R$ ")));
ok("fonteValorCabecalho degraus", E.fonteValorCabecalho("1".repeat(10)) === "21px" && E.fonteValorCabecalho("1".repeat(12)) === "18px" && E.fonteValorCabecalho("1".repeat(14)) === "16px" && E.fonteValorCabecalho("−R$\u00a01.234.567,89") === "14px");
let cabe = true;
for (let n = 1; n <= 16; n++) { const px = parseInt(E.fonteValorCabecalho("x".repeat(n)), 10); if (n * 0.6 * px * 1.3 > E.LARGURA_VALOR_PIOR_CASO_PX) cabe = false; }
ok("fonte do valor cabe no pior caso 320px x 130% (n=1..16)", cabe);
const vc0 = { tipo: "vence", ddmm: "19/11", dias: 49, ambar: false };
ok("chips call coberta", eq(E.chipsMetaV6({ p: { qty: 1000, avg: 39.5 }, estrutura: { nomeTexto: "call coberta" }, vc: vc0 }), [{ chave: "chip_acoes_pm", vals: { qty: "1000", pm: "39,50" } }, { texto: "Call coberta" }, { chave: "chip_vence", vals: { ddmm: "19/11", dias: "49" } }]));
ok("chips estratégia genérica / vencimento âmbar fora", eq(E.chipsMetaV6({ p: { qty: 1, avg: 1 }, estrutura: {}, vc: { ...vc0, ambar: true } }).map((c) => c.chave), ["chip_acoes_pm", "chip_estrategia_generica"]));
ok("chips ação simples", eq(E.chipsMetaV6({ p: { qty: 300, avg: 66.4, stop: 62, alvo: 74 }, estrutura: null }), [{ chave: "chip_acoes_pm", vals: { qty: "300", pm: "66,40" } }, { chave: "chip_plano", vals: { stop: "62,00", alvo: "74,00" } }]));
ok("chips sem stop/alvo -> sem plano; um só -> '—'", E.chipsMetaV6({ p: { qty: 3, avg: 1 }, estrutura: null }).length === 1 && E.chipsMetaV6({ p: { qty: 3, avg: 1, stop: 5 }, estrutura: null })[1].vals.alvo === "—");
ok("pctCapitalTexto", E.pctCapitalTexto(4.234) === "4,2%" && E.pctCapitalTexto(null) === null);

// pontoDoIndice / indiceNomeado
const sim = { pontos: [{ preco: 1, resultado: -5, zona: "prejuizo" }, { preco: 2, resultado: 0, zona: "prejuizo" }, { preco: 3, resultado: 7, zona: "ganho" }], nomeados: { hoje: 1, equilibrio: 2, teto: null, alta_forte: 9 } };
ok("pontoDoIndice meio", E.pontoDoIndice(sim, 1).preco === 2);
ok("pontoDoIndice clamp baixo", E.pontoDoIndice(sim, -4).preco === 1);
ok("pontoDoIndice clamp alto", E.pontoDoIndice(sim, 99).preco === 3);
ok("pontoDoIndice arredonda índice", E.pontoDoIndice(sim, 1.6).preco === 3);
ok("pontoDoIndice inválido", E.pontoDoIndice(null, 0) === null && E.pontoDoIndice({ pontos: [] }, 0) === null && E.pontoDoIndice({}, 0) === null);
ok("pontoDoIndice NaN", E.pontoDoIndice(sim, NaN) === null);
ok("indiceNomeado ok", E.indiceNomeado(sim, "hoje") === 1 && E.indiceNomeado(sim, "equilibrio") === 2);
ok("indiceNomeado null/ausente/fora", E.indiceNomeado(sim, "teto") === null && E.indiceNomeado(sim, "nada") === null && E.indiceNomeado(sim, "alta_forte") === null);
ok("indiceNomeado simulador inválido", E.indiceNomeado(null, "hoje") === null);

// zonaVisual
ok("zona perda_travada", eq(E.zonaVisual("perda_travada"), { borda: "negative", glifo: "▾" }));
ok("zona prejuizo", eq(E.zonaVisual("prejuizo"), { borda: "negative", glifo: "▾" }));
ok("zona ganho", eq(E.zonaVisual("ganho"), { borda: "borderDashed", glifo: "▬" }));
ok("zona ganho_travado", eq(E.zonaVisual("ganho_travado"), { borda: "positive", glifo: "▴" }));
ok("zona desconhecida", eq(E.zonaVisual("xyz"), { borda: "borderSubtle", glifo: "ⓘ" }));

// colunasDaGrade
ok("colunas estreito", E.colunasDaGrade(320, 1) === 2 && E.colunasDaGrade(339, 1) === 2);
ok("colunas largo", E.colunasDaGrade(340, 1) === 3 && E.colunasDaGrade(390, 1.2) === 3);
ok("colunas texto grande", E.colunasDaGrade(390, 1.3) === 2);
ok("colunas inválido", E.colunasDaGrade(NaN, 1) === 2 && E.colunasDaGrade(400, undefined) === 2 && E.colunasDaGrade(undefined, undefined) === 2);

// Guardião estático (T-46-04): sem aritmética em campo financeiro nas 10 funções novas
const NOVAS = ["ancoraRotulo", "rotulosSemColisao", "flipDuracaoMs", "prefereMovimentoReduzido", "faceInicial", "estadoPrincipalV6", "pontoDoIndice", "indiceNomeado", "zonaVisual", "colunasDaGrade", "linhasResultadoV6", "chipsMetaV6", "rsNbsp", "rsSinalNbsp", "fonteValorCabecalho", "pctCapitalTexto"];
const fonte = readFileSync(fileURLToPath(new URL("../src/estruturaCard.js", import.meta.url)), "utf8");
const semComentario = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
const CAMPO = "(?:preco|resultado|be|stop|alvo)";
const reAritm = new RegExp(`\\b${CAMPO}\\b\\s*[-+*/](?![=])|[-+*/]\\s*\\b${CAMPO}\\b`);
for (const nome of NOVAS) {
  const ini = fonte.indexOf(`export function ${nome}(`);
  ok(`fonte tem ${nome}`, ini >= 0);
  if (ini < 0) continue;
  const prox = fonte.indexOf("\nexport function ", ini + 10);
  const corpo = semComentario(fonte.slice(ini, prox < 0 ? undefined : prox));
  ok(`${nome} sem aritmética em campo financeiro`, !reAritm.test(corpo), (corpo.match(reAritm) || [])[0]);
  ok(`${nome} sem toFixed`, !/toFixed/.test(corpo));
}
ok("sem REDUCE_MOTION no módulo", !/REDUCE_MOTION/.test(fonte));
ok("qtyLivre importado de finance.js", /import \{[^}]*qtyLivre[^}]*\} from "\.\/finance\.js"/.test(fonte));

process.exit(fails ? 1 : 0);
