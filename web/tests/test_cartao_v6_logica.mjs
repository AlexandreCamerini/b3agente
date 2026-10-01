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
ok("travadas todas", r.principal.chave === "estado_travadas_todas" && r.principal.tom === "info" && r.principal.glifo === "ⓘ");
r = ep({ p: P({ qtyTravada: 400 }), estrutura: est(), leituraPlano: lp() });
ok("travadas parcial", r.principal.chave === "estado_travadas_parcial" && eq(r.principal.vals, { n: 400, m: 1000, k: 600 }) && r.principal.tom === "info");
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
r = ep({ p: P(), estrutura: est({ resultado: { incompleto: true } }), leituraPlano: lp() });
ok("resultado parcial vira extra", r.extras.some((x) => x.chave === "extra_resultado_parcial" && x.glifo === "ⓘ"));
r = ep({ p: P(), estrutura: null, leituraPlano: lp({ preco: null }) });
ok("cotação indisponível vira extra (sem estrutura)", r.extras.some((x) => x.chave === "extra_cotacao_indisponivel" && x.glifo === "ⓘ"));
r = ep({ p: P(), estrutura: est({ estado: "premio_indisponivel", estadoTexto: "Prêmio indisponível" }), leituraPlano: lp() });
ok("prêmio indisponível vira extra do motor", r.extras.some((x) => x.chave === "motor" && x.tom === "info" && x.vals.texto === "Prêmio indisponível"));
r = ep({ p: P(), estrutura: est({ estado: "ate_5_dias" }), leituraPlano: lp() });
ok("ate_5_dias não gera linha", r.principal === null && r.extras.length === 0);
r = ep({ p: P(), estrutura: null, leituraPlano: null });
ok("leituraPlano ausente não quebra", r.principal === null && Array.isArray(r.extras));
r = ep({ p: P({ stop: null, alvo: null }), estrutura: null, leituraPlano: null });
ok("leituraPlano ausente + sem plano ainda avisa", r.principal && r.principal.chave === "estado_sem_plano");
r = ep({ p: P(), estrutura: est({ estado: "exercicio_provavel", estadoTexto: "x" }), leituraPlano: lp({ posicaoNoPlano: "abaixo_stop" }) });
ok("risco do motor tem precedência sobre fora do plano", r.principal.chave === "motor");
ok("entrada vazia não quebra", ep({}).principal === null);

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
const NOVAS = ["ancoraRotulo", "rotulosSemColisao", "flipDuracaoMs", "prefereMovimentoReduzido", "faceInicial", "estadoPrincipalV6", "pontoDoIndice", "indiceNomeado", "zonaVisual", "colunasDaGrade"];
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
