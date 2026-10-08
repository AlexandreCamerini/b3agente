// Onda H (2026-10-08) — quick 261008-oos: gráficos de payoff legíveis no iPhone.
// Tranca a CLASSE de erro (rótulo sobre o plot, eixo cortado, chip sem estado,
// legenda redundante), não a instância. Três partes:
//  A) geometria/formatação pura de web/src/opcoes/payoffEixos.js (valores reais);
//  B) varredura estática dos fontes (GraficoResultado, GraficoAnatomia, PosicaoTotal,
//     PayoffOperador em App.jsx, PayoffPrimitivas, copy.js ↔ skill_ref.py);
//  C) SSR de GraficoAnatomia (nenhum texto de marcador dentro do <svg>).
// Cada regex nova carrega uma asserção-irmã de SANIDADE (prova que pega o caso ruim).
// Roda: node web/tests/test_ui_onda_h.mjs
import { register } from "node:module";
import { createElement as h } from "react";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";

register("./_jsx_loader.mjs", import.meta.url);

const here = dirname(fileURLToPath(import.meta.url));
const raiz = join(here, "..", "..");
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const lerSrc = (p) => (existsSync(join(here, "..", "src", p)) ? readFileSync(join(here, "..", "src", p), "utf8") : null);
const perto = (a, b) => Math.abs(a - b) < 1e-9;

// ---------------------------------------------------------------- Parte A
let E = null;
try {
  E = await import("../src/opcoes/payoffEixos.js");
} catch (err) {
  ok("A. payoffEixos.js ausente (parte A pulada)", false);
}

if (E) {
  const { rotuloEixoBRL, margemEsquerda, ticksY, ticksX, empilharMarcadores, alturaTopo, afastarPontos, montarGeometria,
    FONTE_EIXO, PLOT_H, PLOT_H_COMPACTO, MARC_R, MARC_DIST, MB_EIXO, MR_EIXO } = E;

  ok("A. constantes: FONTE_EIXO inteiro >= 11, PLOT_H >= 220, MARC_DIST 22, MARC_R 9",
    Number.isInteger(FONTE_EIXO) && FONTE_EIXO >= 11 && PLOT_H >= 220 && MARC_DIST === 22 && MARC_R === 9);

  ok("A. rotuloEixoBRL zero e inteiros", rotuloEixoBRL(0) === "R$ 0" && rotuloEixoBRL(841) === "R$ 841");
  ok("A. rotuloEixoBRL negativo usa U+2212 antes de R$", rotuloEixoBRL(-4998) === "−R$ 4.998");
  ok("A. rotuloEixoBRL < 100 tem 2 casas", rotuloEixoBRL(0.83) === "R$ 0,83" && rotuloEixoBRL(-22.5) === "−R$ 22,50");
  ok("A. rotuloEixoBRL mil/mi", rotuloEixoBRL(150000) === "R$ 150 mil" && rotuloEixoBRL(1234567) === "R$ 1,23 mi");
  ok("A. rotuloEixoBRL null/undefined/NaN => travessão", rotuloEixoBRL(null) === "—" && rotuloEixoBRL(undefined) === "—" && rotuloEixoBRL(NaN) === "—");

  ok("A. margemEsquerda(['R$ 841','R$ 0','−R$ 4.998'], 12) === 75", margemEsquerda(["R$ 841", "R$ 0", "−R$ 4.998"], 12) === 75);
  ok("A. margemEsquerda monotônica e vazia = 8",
    margemEsquerda(["R$ 1.000"], 12) > margemEsquerda(["R$ 10"], 12) && margemEsquerda([], 12) === 8);

  const sy = (v) => 100 - v / 50;
  const chaves = (t) => t.map((x) => x.chave).join(",");
  const t1 = ticksY({ yMin: -4998, yMax: 841, sy });
  ok("A. ticksY: max,zero,min e rótulo do zero 'R$ 0'", chaves(t1) === "max,zero,min" && t1.find((x) => x.chave === "zero").rotulo === "R$ 0");
  ok("A. ticksY semTeto remove max", chaves(ticksY({ yMin: -4998, yMax: 841, sy, semTeto: true })) === "zero,min");
  ok("A. ticksY semPiso remove min", chaves(ticksY({ yMin: -4998, yMax: 841, sy, semPiso: true })) === "max,zero");
  ok("A. ticksY yMax 0 sem max; yMin 5 sem min", chaves(ticksY({ yMin: -4998, yMax: 0, sy })) === "zero,min" && chaves(ticksY({ yMin: 5, yMax: 841, sy })) === "max,zero");
  ok("A. ticksY suprime extremo colado no zero (o zero fica)", chaves(ticksY({ yMin: -100, yMax: 100, sy })) === "zero");

  const tx = ticksX(45.35, 63.8);
  ok("A. ticksX: 3 itens, meio, âncoras", tx.length === 3 && perto(tx[0].valor, 45.35) && perto(tx[1].valor, 54.575) && perto(tx[2].valor, 63.8)
    && tx.map((x) => x.ancora).join(",") === "start,middle,end");
  ok("A. ticksX com extremo não numérico => []", ticksX(null, 5).length === 0);

  const idt = (p) => p;
  const mk = (...ps) => ps.map((p) => ({ preco: p, rotulo: "m" + p }));
  const r1 = empilharMarcadores(mk(200, 100, 110), idt, { xMin: 0, xMax: 400 });
  const porPreco = (r, p) => r.itens.find((i) => i.preco === p);
  ok("A. empilhar: n por ordem de preço", porPreco(r1, 100).n === 1 && porPreco(r1, 110).n === 2 && porPreco(r1, 200).n === 3);
  ok("A. empilhar: linhas 0/1/0 e total 2", porPreco(r1, 100).linha === 0 && porPreco(r1, 110).linha === 1 && porPreco(r1, 200).linha === 0 && r1.linhas === 2);
  const r2 = empilharMarcadores(mk(100, 105, 110, 115), idt, { xMin: 0, xMax: 400 });
  ok("A. empilhar: 4 marcadores colados => 4 linhas distintas", new Set(r2.itens.map((i) => i.linha)).size === 4);
  let sem = 12345;
  const rnd = () => { sem = (sem * 1103515245 + 12345) % 2147483648; return sem / 2147483648; };
  let semColisao = true;
  let dentro = true;
  for (let k = 0; k < 30; k++) {
    const ps = Array.from({ length: 2 + Math.floor(rnd() * 6) }, () => Math.round(rnd() * 400));
    const r = empilharMarcadores(mk(...ps), idt, { xMin: 0, xMax: 400 });
    for (const a of r.itens) {
      if (a.cx < 0 + MARC_R - 1e-9 || a.cx > 400 - MARC_R + 1e-9) dentro = false;
      for (const b of r.itens) if (a !== b && a.linha === b.linha && Math.abs(a.cx - b.cx) < 22 - 1e-9) semColisao = false;
    }
  }
  ok("A. empilhar: 30 conjuntos, nenhum par na mesma linha a < 22px", semColisao);
  ok("A. empilhar: cx dentro de [xMin+R, xMax-R]", dentro);
  ok("A. empilhar: preco null descartado", empilharMarcadores([{ preco: null, rotulo: "x" }, { preco: 5, rotulo: "y" }], idt, { xMin: 0, xMax: 400 }).itens.length === 1);
  ok("A. empilhar: n inteiro recebido é preservado", empilharMarcadores([{ preco: 50, rotulo: "pm", n: 6 }], idt, { xMin: 0, xMax: 400 }).itens[0].n === 6);
  ok("A. empilhar: vazio => linhas 0", empilharMarcadores([], idt, { xMin: 0, xMax: 400 }).linhas === 0);

  ok("A. alturaTopo", alturaTopo(0) === 28 && alturaTopo(1) === 28 && alturaTopo(3) === 72);

  const af = afastarPontos([{ x: 100, y: 100 }, { x: 105, y: 102 }]);
  ok("A. afastarPontos: segundo com dy -20", af[0].dy === 0 && af[1].dy === -20);
  ok("A. afastarPontos: distantes => dy 0", afastarPontos([{ x: 0, y: 0 }, { x: 200, y: 200 }]).every((p) => p.dy === 0));

  const geo = montarGeometria({ largura: 317, x0: 45, x1: 64, yMin: -4998, yMax: 841, marcadores: mk(50, 51, 52) });
  const rotsGeo = [rotuloEixoBRL(841), rotuloEixoBRL(0), rotuloEixoBRL(-4998)];
  ok("A. montarGeometria: plotH >= 220, W 317, ML da margem dos rótulos, H = topo+plotH+MB",
    geo.plotH >= 220 && geo.W === 317 && geo.ML === margemEsquerda(rotsGeo) && geo.H === geo.topo + geo.plotH + MB_EIXO);
  ok("A. montarGeometria: sx(45)=ML e sx(64)=W-MR", perto(geo.sx(45), geo.ML) && perto(geo.sx(64), geo.W - geo.MR) && geo.MR === MR_EIXO);
  ok("A. montarGeometria compacto => PLOT_H_COMPACTO", montarGeometria({ largura: 317, x0: 45, x1: 64, yMin: -1, yMax: 1, marcadores: [], compacto: true }).plotH === PLOT_H_COMPACTO);
  ok("A. montarGeometria largura inválida => 340", montarGeometria({ largura: 0, x0: 1, x1: 2, yMin: -1, yMax: 1, marcadores: [] }).W === 340);
}

// ---------------------------------------------------------------- Parte B
const prim = lerSrc("opcoes/PayoffPrimitivas.jsx");
ok("B. PayoffPrimitivas.jsx existe", prim !== null);
if (prim !== null) {
  const p = semComentario(prim);
  ok("B. primitivas exportam os 6 componentes",
    ["useLarguraMedida", "EixoY", "EixoX", "MarcadoresVerticais", "BadgeNumero", "LegendaMarcadores"]
      .every((n) => new RegExp("export (?:default )?(?:function|const) " + n + "\\b").test(p)));
  ok("B. primitivas: cor só via style (sem fill={T. / stroke={T.), sem transition/animation", !/(?:fill|stroke)=\{T\./.test(p) && !/transition|animation/i.test(p));
  ok("B. primitivas importam de ./payoffEixos.js", /from "\.\/payoffEixos\.js"/.test(p));
}
ok("B. sanidade: regex de cor em atributo pega fill={T.accent}", /(?:fill|stroke)=\{T\./.test('<line stroke={T.accent} />'));

const gres = lerSrc("opcoes/GraficoResultado.jsx");
if (gres !== null) {
  const g = semComentario(gres);
  ok("B. GraficoResultado importa primitivas e eixos", /from "\.\/PayoffPrimitivas\.jsx"/.test(g) && /from "\.\/payoffEixos\.js"/.test(g));
  ok("B. GraficoResultado usa montarGeometria(, <EixoY, <EixoX, <MarcadoresVerticais", /montarGeometria\(/.test(g) && /<EixoY\b/.test(g) && /<EixoX\b/.test(g) && /<MarcadoresVerticais\b/.test(g));
  ok("B. GraficoResultado: sem <text do PM sobre o plot", !/<text[^>]*>[^<]*linha_preco_medio/.test(g) && !/<text[\s\S]{0,200}linha_preco_medio/.test(g));
  ok("B. GraficoResultado: sem redundância valor+frase na legenda", !/R\$ \{fmt\(v\)\}[\s\S]{0,300}it\.frase/.test(g));
  ok("B. GraficoResultado mantém OPACIDADE 0.2 (2 usos), aria-label, details, range",
    /OPACIDADE = 0\.2/.test(g) && (g.match(/fillOpacity=\{OPACIDADE\}/g) || []).length === 2
    && /aria-label=\{ariaTxt\}/.test(g) && /<details/.test(g) && /type="range"/.test(g));
} else ok("B. GraficoResultado.jsx legível", false);
ok("B. sanidade: regex de redundância casa o caso ruim",
  /R\$ \{fmt\(v\)\}[\s\S]{0,300}it\.frase/.test("<span>R$ {fmt(v)}</span>\n {perde ? x : null}\n {it.frase ? <span> {it.frase}</span> : null}"));
ok("B. sanidade: regex do PM casa <text ...>{tx(\"linha_preco_medio\")}", /<text[\s\S]{0,200}linha_preco_medio/.test('<text x={1}>{tx("linha_preco_medio")} 1</text>'));

const gan = lerSrc("opcoes/GraficoAnatomia.jsx");
if (gan !== null) {
  const g = semComentario(gan);
  ok("B. GraficoAnatomia usa montarGeometria( e <LegendaMarcadores", /montarGeometria\(/.test(g) && /<LegendaMarcadores\b/.test(g));
  ok("B. GraficoAnatomia: nenhum {m.rotulo} dentro de <text", !/<text[^>]*>\s*\{m\.rotulo\}/.test(g));
  ok("B. GraficoAnatomia: TRACOS sem traço cheio", (() => {
    const m = g.match(/export const TRACOS = \[([^\]]*)\]/);
    return !!m && !/(^|,)\s*""\s*(,|$)/.test(m[1]) && m[1].split(",").length >= 4;
  })());
  ok("B. GraficoAnatomia: sem viewBox fixo de 720", !/W = compacto \? 340 : 720/.test(g));
} else ok("B. GraficoAnatomia.jsx legível", false);
ok("B. sanidade: regex de {m.rotulo} em <text pega o caso ruim", /<text[^>]*>\s*\{m\.rotulo\}/.test("<text x={1} style={eixo}>{m.rotulo}</text>"));
ok("B. sanidade: regex de TRACOS pega traço cheio", /(^|,)\s*""\s*(,|$)/.test('"", "6 4"'));

const pt = lerSrc("opcoes/PosicaoTotal.jsx");
if (pt !== null) {
  const p = semComentario(pt);
  ok("B. PosicaoTotal: chip ligado usa accentTint10, desligado textMuted", /background: ligado \? T\.accentTint10/.test(p) && /T\.textMuted/.test(p));
  ok("B. PosicaoTotal: sem 2px solid accent", !/2px solid \$\{T\.accent\}/.test(p));
  ok("B. PosicaoTotal: chips em grade de 3 colunas, alvo mínimo mantido", /repeat\(3, minmax\(0, 1fr\)\)/.test(p) && /minHeight: ALVO_MIN/.test(p));
} else ok("B. PosicaoTotal.jsx legível", false);
ok("B. sanidade: regex 2px solid accent pega o caso ruim", /2px solid \$\{T\.accent\}/.test("border: `2px solid ${T.accent}`"));

const app = lerSrc("App.jsx") || "";
{
  const ini = app.indexOf("function PayoffOperador(");
  const fim = app.indexOf("\nfunction GradeConta(", ini + 1);
  const rec = ini >= 0 && fim > ini ? semComentario(app.slice(ini, fim)) : "";
  ok("B. App.jsx: recorte de PayoffOperador encontrado", rec.length > 300);
  ok("B. App.jsx importa payoffEixos.js e PayoffPrimitivas.jsx", /from "\.\/opcoes\/payoffEixos\.js"/.test(app) && /from "\.\/opcoes\/PayoffPrimitivas\.jsx"/.test(app));
  ok("B. PayoffOperador usa montarGeometria(, useLarguraMedida(, <LegendaMarcadores", /montarGeometria\(/.test(rec) && /useLarguraMedida\(/.test(rec) && /<LegendaMarcadores\b/.test(rec));
  ok("B. PayoffOperador: sem '140px', sem fill/stroke={T.", !rec.includes("140px") && !/(?:fill|stroke)=\{T\./.test(rec));
  ok("B. PayoffOperador: svg role=img aria-label={pf.aria} e zero <text", /<svg role="img" aria-label=\{pf\.aria\}/.test(rec) && !/<text\b/.test(rec));
}

// copy.js ↔ skill_ref.py
const copy = readFileSync(join(here, "..", "src", "copy.js"), "utf8");
const py = readFileSync(join(raiz, "server", "app", "skill_ref.py"), "utf8");
for (const [nome, src] of [["copy.js", copy], ["skill_ref.py", py]]) {
  for (const k of ["leg_hoje", "leg_be", "leg_k"]) {
    const linhas = src.split("\n").filter((l) => new RegExp("^\\s*\"?" + k + "\"?:").test(l));
    ok(`B. ${nome}: ${k} tem 2 ocorrências, sem ┆ nem ◆`, linhas.length === 2 && linhas.every((l) => !/[┆◆]/.test(l)));
  }
  for (const k of ["legenda_equilibrio", "legenda_piso", "legenda_teto"]) {
    const linhas = src.split("\n").filter((l) => new RegExp("^\\s*\"?" + k + "\"?:").test(l));
    ok(`B. ${nome}: ${k} começa com 'R$ {preco}' nos 2 modos`, linhas.length === 2 && linhas.every((l) => /:\s*"R\$ \{preco\}/.test(l)));
  }
  for (const k of ["legenda_perda_maxima", "legenda_ganho_maximo"]) {
    const linhas = src.split("\n").filter((l) => new RegExp("^\\s*\"?" + k + "\"?:").test(l));
    ok(`B. ${nome}: ${k} sem {valor} nos 2 modos`, linhas.length === 2 && linhas.every((l) => !l.includes("{valor}")));
  }
}
ok("B. sanidade: detector de {valor} pega a frase antiga", "Perda máxima: R$ {valor}. É o pior".includes("{valor}"));

// ---------------------------------------------------------------- Parte C
{
  let GraficoAnatomia = null;
  try { GraficoAnatomia = (await import("../src/opcoes/GraficoAnatomia.jsx")).default; } catch (err) { ok("C. import GraficoAnatomia: " + err.message, false); }
  if (GraficoAnatomia) {
    const precos = [44, 46, 48, 50, 52];
    const vals = [1, 2, -3, 2, 4];
    const out = renderToStaticMarkup(h(GraficoAnatomia, {
      precos, series: [{ id: "p", valores: vals, traco: 0 }], area: vals, cursorIdx: 2, titulo: "T", descricao: "D",
      marcadores: [{ preco: 48.0, rotulo: "K 48" }, { preco: 48.2, rotulo: "PM", comPreco: true }, { preco: 49, rotulo: "hoje", comPreco: true }],
    }));
    const i0 = out.indexOf("<svg");
    const i1 = out.indexOf("</svg>");
    const svg = i0 >= 0 && i1 > i0 ? out.slice(i0, i1) : "";
    ok("C. svg encontrado", svg.length > 200);
    ok("C. 'K 48' NÃO aparece dentro do svg", !svg.includes("K 48"));
    ok("C. legenda <ol> traz 'K 48' e 'PM'", /<ol/.test(out) && out.slice(i1).includes("K 48") && out.slice(i1).includes("PM"));
    const nums = [...svg.matchAll(/<text[^>]*>(\d+)<\/text>/g)].map((m) => m[1]);
    ok("C. 3 círculos numerados 1,2,3 no svg", ["1", "2", "3"].every((n) => nums.includes(n)));
    const fontes = [...svg.matchAll(/font-size[:=]"?(\d+(?:\.\d+)?)/g)].map((m) => parseFloat(m[1]));
    ok("C. todo font-size no svg >= 11 (e existe algum)", fontes.length > 0 && fontes.every((v) => v >= 11));
  }
}
ok("C. sanidade: regex de font-size lê style e atributo", [..."font-size:12px;x font-size=\"11\"".matchAll(/font-size[:=]"?(\d+(?:\.\d+)?)/g)].length === 2);

console.log(fails ? `\n${fails} falha(s)` : "\nOK");
process.exit(fails ? 1 : 0);
