// Navegação/progresso/layout puros da folha do guia (quick 261011-l5x). Roda sem build.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import {
  proximo, anterior, irParaTela, rotuloSeletor, carregarProgresso, serializarProgresso, telaConcluida,
  layoutGuia, enquadrar, ehSwipeHorizontal, TOPO_PX, RODAPE_PX, CHAVE_PROGRESSO,
} from "../src/guiaNav.js";
import { parseTelasData } from "../src/guiaDados.js";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond, extra) => { console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra)); if (!cond) fails++; };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

const T = [{ id: "a", pontos: [{}, {}] }, { id: "b", pontos: [{}] }, { id: "c", pontos: [{}, {}, {}] }];

// proximo
ok("proximo: ponto 0 -> 1", eq(proximo({ tela: 0, ponto: 0 }, T), { tela: 0, ponto: 1 }));
ok("proximo: último ponto -> Na prática", eq(proximo({ tela: 0, ponto: 1 }, T), { tela: 0, ponto: 2 }));
ok("proximo: Na prática -> ponto 0 da tela seguinte", eq(proximo({ tela: 0, ponto: 2 }, T), { tela: 1, ponto: 0 }));
ok("proximo: Na prática da última tela devolve o mesmo", eq(proximo({ tela: 2, ponto: 3 }, T), { tela: 2, ponto: 3 }));
// anterior
ok("anterior: ponto 1 -> 0", eq(anterior({ tela: 0, ponto: 1 }, T), { tela: 0, ponto: 0 }));
ok("anterior: ponto 0 da tela 1 -> Na prática da tela 0", eq(anterior({ tela: 1, ponto: 0 }, T), { tela: 0, ponto: 2 }));
ok("anterior: ponto 0 da tela 0 devolve o mesmo", eq(anterior({ tela: 0, ponto: 0 }, T), { tela: 0, ponto: 0 }));
ok("anterior: Na prática -> último ponto", eq(anterior({ tela: 2, ponto: 3 }, T), { tela: 2, ponto: 2 }));
// irParaTela / rótulo
ok("irParaTela faz clamp e zera o ponto", eq(irParaTela({ tela: 0, ponto: 1 }, 99, T), { tela: 2, ponto: 0 }) && eq(irParaTela({ tela: 1, ponto: 0 }, -3, T), { tela: 0, ponto: 0 }));
const reais = parseTelasData(readFileSync(join(here, "..", "..", "site", "js", "telas-data.js"), "utf8"));
ok("rotuloSeletor({tela:2}) === '3/20' nas telas reais", rotuloSeletor({ tela: 2, ponto: 0 }, reais) === "3/20");

// progresso
ok("chave de progresso é a do guia web", CHAVE_PROGRESSO === "boris-guia-v1");
ok("carregarProgresso: null/JSON inválido -> vazio", eq(carregarProgresso(null), { v: 2, mis: {}, q: {} }) && eq(carregarProgresso("{x"), { v: 2, mis: {}, q: {} }));
ok("carregarProgresso: sem v:2 zera mis e mantém q", eq(carregarProgresso(JSON.stringify({ mis: { a: [true] }, q: { a: true } })), { v: 2, mis: {}, q: { a: true } }));
ok("carregarProgresso: v:2 mantém tudo", eq(carregarProgresso(JSON.stringify({ v: 2, mis: { a: true }, q: { b: true } })), { v: 2, mis: { a: true }, q: { b: true } }));
ok("telaConcluida exige missão E teste", telaConcluida({ mis: { a: true }, q: { a: true } }, "a") && !telaConcluida({ mis: { a: true }, q: {} }, "a") && !telaConcluida({ mis: {}, q: { a: true } }, "a"));
ok("serializarProgresso grava v:2", JSON.parse(serializarProgresso({ mis: { a: true }, q: {} })).v === 2);

// layout
for (const [vw, vh] of [[375, 667], [375, 812]]) {
  const L = layoutGuia(vw, vh);
  ok(`layoutGuia(${vw},${vh}): topo 44, captura começa em 44, termina acima do rodapé, empilhado`,
    L.topo === TOPO_PX && L.captura.top === 44 && L.captura.top + L.captura.height <= vh - RODAPE_PX && L.lado === false
    && L.folha.top === L.captura.top + L.captura.height && L.folha.top + L.folha.height <= vh - RODAPE_PX);
}
const W = layoutGuia(1024, 768);
ok("layoutGuia(1024,768): lado a lado, sem rolagem", W.lado === true && W.captura.height <= 768 - 44 - RODAPE_PX && W.folha.height <= 768 - 44 - RODAPE_PX
  && W.captura.width + W.folha.width === 1024 && W.folha.left === W.captura.width);

// enquadrar
const e1 = enquadrar({ x: 50, y: 50, w: 20, h: 5 }, 780, 1688, 375, 325);
ok("enquadrar: escala = vw/natW", Math.abs(e1.s - 375 / 780) < 1e-9);
ok("enquadrar: captura cobre a moldura (sem borda vazia) e ponto a ~40% da altura",
  e1.tx <= 0 && e1.ty <= 0 && e1.tx + e1.w >= 375 - 1e-6 && e1.ty + e1.h >= 325 - 1e-6
  && Math.abs((e1.ty + 0.5 * e1.h) - 0.4 * 325) < 1e-6);
ok("enquadrar: spot dentro da moldura", e1.spot.left >= 0 && e1.spot.top >= 0 && e1.spot.left + e1.spot.width <= 375 + 1e-6 && e1.spot.top + e1.spot.height <= 325 + 1e-6);
const eTopo = enquadrar({ x: 10, y: 2, w: 10, h: 2 }, 780, 1688, 375, 325);
ok("enquadrar: ponto no topo faz clamp (ty = 0)", eTopo.ty === 0);
const eW = enquadrar({ x: 50, y: 50, w: 10, h: 10 }, 800, 500, 1000, 800);
ok("enquadrar: captura menor que a moldura fica centrada", eW.ty >= 0 && Math.abs(eW.ty - (800 - eW.h) / 2) < 1e-6 && eW.spot.top >= 0);
const eInt = enquadrar(null, 780, 1688, 375, 325);
ok("enquadrar(null): tela inteira cabe na moldura, sem spot", eInt.spot === null && eInt.w <= 375 + 1e-6 && eInt.h <= 325 + 1e-6);

// swipe
ok("swipe: da borda esquerda é null (reservado a fechar)", ehSwipeHorizontal({ x0: 10, y0: 100, x1: 200, y1: 100 }) === null);
ok("swipe: esquerda -> proximo", ehSwipeHorizontal({ x0: 300, y0: 100, x1: 200, y1: 110 }) === "proximo");
ok("swipe: direita -> anterior", ehSwipeHorizontal({ x0: 100, y0: 100, x1: 220, y1: 90 }) === "anterior");
ok("swipe: curto ou vertical demais -> null", ehSwipeHorizontal({ x0: 100, y0: 100, x1: 130, y1: 100 }) === null && ehSwipeHorizontal({ x0: 100, y0: 100, x1: 220, y1: 200 }) === null);
ok("swipe: entrada inválida -> null", ehSwipeHorizontal({}) === null && ehSwipeHorizontal() === null);

if (fails) { console.log(`\n${fails} falha(s).`); process.exit(1); }
console.log("\ntodos os testes passaram.");
