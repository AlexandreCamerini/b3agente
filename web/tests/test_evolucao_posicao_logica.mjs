// 2026-10-13 (quick 261013-svo) — reconstrução determinística da série de resultado por posição (puro).
// Princípio 4 (não inventar) e 5 (cálculo determinístico): se não fecha com a posição atual, não desenha.
import fs from "node:fs";
import * as E from "../src/evolucaoPosicao.js";

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

ok("exporta os 8 símbolos", ["parseDataOperacao", "hojeBRT", "ymdParaBr", "reconstruirPosicao", "serieResultadoPosicao", "periodoCandles", "geometriaSerie"].every((k) => typeof E[k] === "function") && Array.isArray(E.PERIODOS_CANDLES));

// --- parseDataOperacao
const pd = E.parseDataOperacao;
ok("parse com hora", pd("01/10/2026 10:15") === "2026-10-01");
ok("parse sem hora", pd("01/10/2026") === "2026-10-01");
ok("parse ISO -> null", pd("2026-10-01") === null);
ok("parse dia 32 -> null", pd("32/10/2026 10:00") === null);
ok("parse mês 13 -> null", pd("01/13/2026 10:00") === null);
ok("parse null/undefined/número -> null", pd(null) === null && pd(undefined) === null && pd(123) === null);

// --- hojeBRT / ymdParaBr
ok("hojeBRT 22h30 BRT (dia 14 em UTC)", E.hojeBRT(new Date("2026-10-14T01:30:00Z")) === "2026-10-13");
ok("hojeBRT meio-dia UTC", E.hojeBRT(new Date("2026-10-13T12:00:00Z")) === "2026-10-13");
ok("hojeBRT meia-noite BRT", E.hojeBRT(new Date("2026-10-14T03:00:00Z")) === "2026-10-14");
ok("hojeBRT inválido -> null", E.hojeBRT(new Date(NaN)) === null);
ok("ymdParaBr", E.ymdParaBr("2026-10-05") === "05/10/2026" && E.ymdParaBr("x") === null && E.ymdParaBr(null) === null);

// --- periodoCandles
const HOJE = "2026-10-13";
const menos = (n) => {
  const d = new Date(Date.UTC(2026, 9, 13) - n * 86400000);
  return d.toISOString().slice(0, 10);
};
const pc = (n) => E.periodoCandles(menos(n), HOJE);
ok("período hoje -> 1mo", pc(0) === "1mo");
ok("período -20d -> 1mo", pc(20) === "1mo");
ok("período -30d -> 3mo", pc(30) === "3mo");
ok("período -80d -> 3mo", pc(80) === "3mo");
ok("período -100d -> 6mo", pc(100) === "6mo");
ok("período -300d -> 1y", pc(300) === "1y");
ok("período -400d -> 2y", pc(400) === "2y");
ok("período -1000d -> 2y", pc(1000) === "2y");
ok("período inválido -> null", E.periodoCandles("x", HOJE) === null && E.periodoCandles(null, HOJE) === null);
ok("período futuro -> null", E.periodoCandles("2026-10-20", HOJE) === null);
const py = fs.readFileSync(new URL("../../server/app/candles.py", import.meta.url), "utf8");
const bloco = py.match(/PERIOD_BARS\s*=\s*\{([^}]*)\}/);
const pares = bloco ? [...bloco[1].matchAll(/"([^"]+)"\s*:\s*(\d+)/g)].map((m) => [m[1], Number(m[2])]) : [];
ok("PERIODOS_CANDLES espelha PERIOD_BARS de candles.py", pares.length === 5 && eq(pares, E.PERIODOS_CANDLES.map((x) => [...x])) && Object.isFrozen(E.PERIODOS_CANDLES));

// --- reconstrução / série
// Fixtures: lista CRONOLÓGICA; o helper do teste inverte para newest-first (formato real).
const op = (type, qty, price, date, extra) => ({ type, t: "PETR4", qty, price, date, status: "executada", ...extra });
const hist = (...cron) => [...cron].reverse();
const C = (...pares) => pares.map(([date, close]) => ({ date, close }));
const serie = (history, candles, posicao, hojeYmd = HOJE) =>
  E.serieResultadoPosicao({ ticker: "PETR4", history, candles, posicao, hojeYmd });
const res = (s) => (s.pontos || []).map((p) => p.resultado);
const dts = (s) => (s.pontos || []).map((p) => p.data);

const c1 = C(["2026-10-01", 31], ["2026-10-02", 29.5], ["2026-10-05", 32]);
const h1 = hist(op("COMPRA", 100, 30, "01/10/2026 10:15"));
const pos1 = { t: "PETR4", qty: 100, avg: 30 };

let s = serie(h1, c1, pos1);
ok("1 compra única: pontos", s.ok && eq(res(s), [100, -50, 200]), JSON.stringify(s));
ok("1 marcas/inicio/ate/parcial/min/max/ultimo", eq(s.marcas, [{ data: "2026-10-01", tipo: "compra" }]) && s.inicio === "2026-10-01" && s.ate === "2026-10-05" && s.parcial === false && s.min === -50 && s.max === 200 && s.ultimo === 200);
ok("1 datas BR", s.inicioBr === "01/10/2026" && s.ateBr === "05/10/2026");

s = serie(hist(op("COMPRA", 100, 30, "01/10/2026 10:15"), op("COMPRA", 100, 32, "05/10/2026 10:15")),
  C(["2026-10-01", 31], ["2026-10-02", 29.5], ["2026-10-05", 32], ["2026-10-06", 30]), { qty: 200, avg: 31 });
ok("2 compras múltiplas: pontos", s.ok && eq(res(s), [100, -50, 200, -200]), JSON.stringify(res(s)));
ok("2 marcas compra 10-01 e 10-05", eq(s.marcas, [{ data: "2026-10-01", tipo: "compra" }, { data: "2026-10-05", tipo: "compra" }]));

s = serie(hist(op("COMPRA", 200, 30, "01/10/2026 10:15"), op("VENDA", 100, 33, "02/10/2026 10:15")),
  C(["2026-10-01", 31], ["2026-10-02", 33], ["2026-10-05", 32]), { qty: 100, avg: 30 });
ok("3 venda parcial preserva PM", s.ok && eq(res(s), [200, 300, 200]), JSON.stringify(res(s)));
ok("3 marcas compra e venda", eq(s.marcas, [{ data: "2026-10-01", tipo: "compra" }, { data: "2026-10-02", tipo: "venda" }]));

const c4 = C(["2026-09-01", 20], ["2026-09-10", 22], ["2026-10-01", 31], ["2026-10-02", 29.5], ["2026-10-05", 32]);
s = serie(hist(op("COMPRA", 100, 20, "01/09/2026 10:15"), op("VENDA", 100, 22, "10/09/2026 10:15"), op("COMPRA", 100, 30, "01/10/2026 10:15")), c4, pos1);
ok("4 venda total + recompra: só o episódio atual", s.ok && eq(res(s), [100, -50, 200]) && s.inicio === "2026-10-01" && eq(s.marcas, [{ data: "2026-10-01", tipo: "compra" }]), JSON.stringify(s));

s = serie(h1, c1, { qty: 200, avg: 30 });
ok("5a histórico incompleto (qty)", !s.ok && s.motivo === "nao_fecha");
s = serie(h1, c1, { qty: 100, avg: 30.5 });
ok("5b PM não fecha", !s.ok && s.motivo === "nao_fecha");
s = serie(h1, c1, { qty: 100, avg: 30.01 });
ok("5c PM dentro da tolerância (usa PM reconstruído)", s.ok && eq(res(s), [100, -50, 200]));
s = serie(hist(op("VENDA", 100, 30, "01/10/2026 10:15")), c1, pos1);
ok("5d venda sem compra antes", !s.ok && s.motivo === "nao_fecha");

s = serie([], c1, pos1);
ok("6 sem compra (vazio)", !s.ok && s.motivo === "sem_compra");
s = serie(hist(op("COMPRA", 100, 30, "01/10/2026 10:15", { t: "VALE3" })), c1, pos1);
ok("6 sem compra (outro ticker)", !s.ok && s.motivo === "sem_compra");

s = serie(h1, C(["2026-10-01", 31]), pos1);
ok("7a candles insuficientes (1)", !s.ok && s.motivo === "candles_insuficientes");
s = serie(hist(op("COMPRA", 100, 30, "12/10/2026 10:15")), C(["2026-10-12", 31], ["2026-10-13", 32]), pos1);
ok("7b só o candle de hoje depois da compra", !s.ok && s.motivo === "candles_insuficientes");
ok("7c candles vazios/nulos", serie(h1, [], pos1).motivo === "candles_insuficientes" && serie(h1, null, pos1).motivo === "candles_insuficientes");

s = serie(hist(op("COMPRA", 100, 30, "01/10/2026 10:15"), op("COMPRA", 100, 31, "02/10/2026 10:15", { status: "rejeitada" })), c1, pos1);
ok("8 rejeitada ignorada", s.ok && eq(res(s), [100, -50, 200]) && s.marcas.length === 1);

s = serie(hist(op("COMPRA", 100, 30, "01/10/2026 10:15"),
  op("COMPRA", 1, 2, "02/10/2026 10:15", { t: "PETRJ300", underlying: "PETR4", kind: "opcao" }),
  op("VENDA", 100, 3, "03/10/2026 10:15", { kind: "opcao" })), c1, pos1);
ok("9 opção ignorada", s.ok && eq(res(s), [100, -50, 200]) && s.marcas.length === 1);

s = serie(h1, [...c1, { date: "2026-10-13", close: 40 }], pos1);
ok("10 candle de hoje excluído", s.ok && s.ate === "2026-10-05" && !dts(s).includes("2026-10-13"));

s = serie(h1, C(["2026-10-02", 29.5], ["2026-10-05", 32]), pos1);
ok("11 janela parcial", s.ok && eq(res(s), [-50, 200]) && s.parcial === true && s.desde === "2026-10-02" && s.desdeBr === "02/10/2026" && eq(s.marcas, []), JSON.stringify(s));

s = serie(hist(op("COMPRA", 100, 30, "02/10/2026 10:15")), C(["2026-10-01", 31], ["2026-10-05", 32], ["2026-10-06", 33]), pos1);
ok("12 compra em dia sem candle", s.ok && eq(res(s), [200, 300]) && eq(s.marcas, [{ data: "2026-10-05", tipo: "compra" }]) && s.parcial === false, JSON.stringify(s));

s = serie(h1, [...c1, { date: "2026-10-03", close: null }, { date: "2026-10-04", close: 0 }], pos1);
ok("13 close inválido ignorado", s.ok && eq(res(s), [100, -50, 200]));

s = serie(hist({ type: "COMPRA", t: "PETR4", qty: 100, price: 30, date: "01/10/2026 10:15" }), c1, pos1);
ok("14 legado sem status conta como executada", s.ok && eq(res(s), [100, -50, 200]));

s = serie(hist(op("COMPRA", 200, 30, "01/10/2026 10:00"), op("VENDA", 100, 31, "01/10/2026 11:00")), c1, pos1);
ok("15 mesmo dia compra+venda: estado depois das duas", s.ok && res(s)[0] === 100, JSON.stringify(res(s)));

ok("16 sem posição (null)", serie(h1, c1, null).motivo === "sem_posicao");
ok("16 sem posição (qty 0)", serie(h1, c1, { qty: 0 }).motivo === "sem_posicao");

// --- não muta
{
  const h = JSON.parse(JSON.stringify(h1)), c = JSON.parse(JSON.stringify(c1)), p = { ...pos1 };
  const h0 = JSON.stringify(h), c0 = JSON.stringify(c), p0 = JSON.stringify(p);
  E.reconstruirPosicao({ ticker: "PETR4", history: h, posicao: p });
  E.serieResultadoPosicao({ ticker: "PETR4", history: h, candles: c, posicao: p, hojeYmd: HOJE });
  ok("não muta history/candles/posicao", JSON.stringify(h) === h0 && JSON.stringify(c) === c0 && JSON.stringify(p) === p0);
}
{
  const r = E.reconstruirPosicao({ ticker: "PETR4", history: h1, posicao: pos1 });
  ok("reconstruirPosicao ok: inicioYmd, ops, nCompras", r.ok && r.inicioYmd === "2026-10-01" && r.nCompras === 1 && eq(r.ops, [{ ymd: "2026-10-01", tipo: "compra", qtyDepois: 100, pmDepois: 30 }]), JSON.stringify(r));
}

// --- geometriaSerie
let g = E.geometriaSerie({ pontos: [{ data: "a", resultado: 0 }, { data: "b", resultado: 100 }], marcas: [{ data: "b", tipo: "venda" }], largura: 100, altura: 50, margem: 0 });
ok("geometria d e yZero", g.d === "M0.0 50.0 L100.0 0.0" && g.yZero === 50, JSON.stringify(g));
ok("geometria marca no índice da data", g.marcas.length === 1 && g.marcas[0].x === 100 && g.marcas[0].y === 0 && g.marcas[0].tipo === "venda");
g = E.geometriaSerie({ pontos: [{ data: "a", resultado: -100 }, { data: "b", resultado: -50 }], marcas: [], largura: 100, altura: 50, margem: 0 });
ok("geometria todos negativos: zero no topo", g.yZero === 0, JSON.stringify(g));
g = E.geometriaSerie({ pontos: [{ data: "a", resultado: 0 }, { data: "b", resultado: 0 }], marcas: [] });
ok("geometria todos zero sem NaN", !/NaN/.test(JSON.stringify(g)) && typeof g.d === "string" && g.W === 280 && g.H === 72, JSON.stringify(g));

process.exit(fails ? 1 : 0);
