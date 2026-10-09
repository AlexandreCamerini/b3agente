// Onda H2 (2026-10-08) — quick 261008-w9i: PayoffChart na linguagem da Onda H.
// Tranca a CLASSE de erro (texto de marcador sobre o plot, viewBox fixo, cor em
// atributo, resultado null desenhado como zero), não a instância. Três partes:
//  A) MarcadoresVerticais aceita `traco` por marcador (default "3 3" preservado);
//  B) varredura estática de PayoffChart.jsx e das 4 chaves novas de copy.js;
//  C) SSR de PayoffChart (3 fixtures: limitada, ganho ilimitado, sem curva).
// Cada regex nova carrega uma asserção-irmã de SANIDADE (prova que pega o caso ruim).
// Roda: node web/tests/test_ui_onda_h2.mjs
import { register } from "node:module";
import { createElement as h } from "react";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { renderToStaticMarkup } from "react-dom/server";

register("./_jsx_loader.mjs", import.meta.url);

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const lerSrc = (p) => (existsSync(join(here, "..", "src", p)) ? readFileSync(join(here, "..", "src", p), "utf8") : null);

// ---------------------------------------------------------------- Parte A
{
  let E = null, P = null;
  try { E = await import("../src/opcoes/payoffEixos.js"); } catch (err) { ok("A. import payoffEixos: " + err.message, false); }
  try { P = await import("../src/opcoes/PayoffPrimitivas.jsx"); } catch (err) { ok("A. import PayoffPrimitivas: " + err.message, false); }
  if (E && P) {
    const geo = E.montarGeometria({
      largura: 340, x0: 10, x1: 20, yMin: -1, yMax: 1,
      marcadores: [{ preco: 12, rotulo: "a", traco: "1 3" }, { preco: 18, rotulo: "b" }],
    });
    const out = renderToStaticMarkup(h("svg", null, h(P.MarcadoresVerticais, { geo })));
    ok('A. MarcadoresVerticais: traco por marcador ("1 3") repassado à <line>', out.includes('stroke-dasharray="1 3"'));
    ok('A. MarcadoresVerticais: default "3 3" preservado quando não há traco', out.includes('stroke-dasharray="3 3"'));
  }
}
ok("A. sanidade: renderToStaticMarkup emite stroke-dasharray com hífen",
  renderToStaticMarkup(h("svg", null, h("line", { strokeDasharray: "1 3" }))).includes('stroke-dasharray="1 3"'));

// ---------------------------------------------------------------- Parte B
const bruto = lerSrc("opcoes/PayoffChart.jsx");
ok("B. PayoffChart.jsx legível", bruto !== null);
if (bruto !== null) {
  const f = semComentario(bruto);
  ok("B. importa de ./payoffEixos.js e ./PayoffPrimitivas.jsx",
    /from "\.\/payoffEixos\.js"/.test(f) && /from "\.\/PayoffPrimitivas\.jsx"/.test(f));
  ok("B. usa montarGeometria(, useLarguraMedida(, <EixoY, <EixoX, <MarcadoresVerticais, <LegendaMarcadores",
    /montarGeometria\(/.test(f) && /useLarguraMedida\(/.test(f) && /<EixoY\b/.test(f)
    && /<EixoX\b/.test(f) && /<MarcadoresVerticais\b/.test(f) && /<LegendaMarcadores\b/.test(f));
  ok("B. sem viewBox fixo nem constantes antigas (W = 320, FONTE_MIN, FONTE_SETA, PAD_E)",
    !/const W = 320/.test(f) && !/FONTE_MIN/.test(f) && !/FONTE_SETA/.test(f) && !/\bPAD_E\b/.test(f));
  ok("B. sanidade: regex de viewBox fixo pega o código antigo", /const W = 320/.test("const W = 320, H = 192;"));
  const corAttr = /(?:fill|stroke)=\{(?:T\.|cor)/;
  ok("B. cor só via style (sem fill={T. / stroke={T. / fill={cor / stroke={cor)", !corAttr.test(f));
  ok("B. sanidade: regex de cor em atributo pega stroke={corLucro}", corAttr.test("<path stroke={corLucro} />"));
  const iHook = f.indexOf("useLarguraMedida(");
  const iRet = f.indexOf("if (!desenho)");
  ok("B. useLarguraMedida( chamado ANTES do early return (regra dos hooks)", iHook >= 0 && iRet > iHook);
  ok('B. traços distintos por tipo: traco: "2 4" (breakeven) e traco: "1 3" (strike)',
    /traco: "2 4"/.test(f) && /traco: "1 3"/.test(f));
  const textoMarcador = /<text[\s\S]{0,200}(?:s\.name|opcoesHojePrefixoEixo|fmt\(item\.valor\)|opcoesPerdaIlimitadaCurta)/;
  ok("B. nenhum <text de marcador/cenário/seta com texto dentro do plot", !textoMarcador.test(f));
  ok("B. sanidade: regex de texto de marcador pega <text x={1}>{s.name}</text>",
    textoMarcador.test("<text x={1}>{s.name}</text>") && textoMarcador.test("<text x={1}>{fmt(item.valor)}</text>"));
  ok("B. mantém aria-label={descricao} e <title>{descricao}</title>",
    /aria-label=\{descricao\}/.test(bruto) && /<title>\{descricao\}<\/title>/.test(bruto));
  const paths = f.match(/<path\b[^>]*>/g) || [];
  ok('B. exatamente 2 <path, ambos fill="none" e strokeWidth="3"',
    paths.length === 2 && paths.every((p) => /fill="none"/.test(p) && /strokeWidth="3"/.test(p)));
  ok("B. sanidade: checagem de <path pega path preenchido",
    !['<path d={d} fill="red" />'].every((p) => /fill="none"/.test(p)));
}

const copy = readFileSync(join(here, "..", "src", "copy.js"), "utf8");
let COPY = null;
try { COPY = (await import("../src/copy.js")).COPY; } catch (err) { ok("B. import copy.js: " + err.message, false); }
const CHAVES = ["opcoesLegStrike", "opcoesLegHoje", "opcoesSerieTotal", "opcoesSerieLeitura"];
if (COPY) {
  for (const modo of ["estudo", "operador"]) {
    ok(`B. COPY.${modo} tem as 4 chaves novas como string não vazia`,
      CHAVES.every((k) => typeof COPY[modo][k] === "string" && COPY[modo][k].trim().length > 0));
  }
}
ok("B. sanidade: copy.js é texto lido (chaves nomeadas existem como literal quando presentes)", copy.length > 1000);

// ---------------------------------------------------------------- Parte C
{
  let PayoffChart = null, COPY2 = null;
  try { PayoffChart = (await import("../src/opcoes/PayoffChart.jsx")).default; } catch (err) { ok("C. import PayoffChart: " + err.message, false); }
  try { COPY2 = (await import("../src/copy.js")).COPY; } catch (err) { ok("C. import copy: " + err.message, false); }
  if (PayoffChart && COPY2) {
    const cp = COPY2.estudo;
    const F1 = {
      name: "Trava de alta",
      legs: [{ kind: "CALL", strike: 28, expiration: "2026-11-21" }, { kind: "CALL", strike: 30, expiration: "2026-11-21" }],
      payoff: [{ underlying: 0, result: -0.8 }, { underlying: 28, result: -0.8 }, { underlying: 30, result: 1.2 }],
      breakevens: [28.8], net_cost: 0.8, max_gain: 1.2, max_loss: -0.8,
      unlimited_gain: false, unlimited_loss: false,
      scenarios: { scenarios: [{ name: "+1σ", underlying: 29.5, result: 0.7 }, { name: "alvo", underlying: 29.9, result: null }] },
    };
    const DOM = { xMin: 26, xMax: 32, yMin: -0.8, yMax: 1.2, spot: 29.1, ganhoIlimitado: false, perdaIlimitada: false };
    const recortar = (out) => {
      const i0 = out.indexOf("<svg");
      const i1 = out.indexOf("</svg>");
      if (i0 < 0 || i1 < i0) return { tag: "", svg: "", depois: out };
      const bruto = out.slice(i0, i1);
      const tag = (bruto.match(/^<svg[^>]*>/) || [""])[0];
      const svg = bruto.slice(tag.length).replace(/<title>[\s\S]*?<\/title>/, "");
      return { tag, svg, depois: out.slice(i1) };
    };

    const out1 = renderToStaticMarkup(h(PayoffChart, { estrutura: F1, cp, dominio: DOM }));
    const { tag, svg, depois } = recortar(out1);
    ok("C. F1: svg encontrado", svg.length > 200);
    const vb = (tag.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/) || []);
    ok('C. F1: viewBox começa com "0 0 340 " (largura medida, não 320)', vb[1] === "340");
    ok("C. F1: altura do viewBox >= 244", parseFloat(vb[2]) >= 244);
    for (const s of ["28,00", "30,00", "28,80", "29,10", "+1σ", "alvo", "hoje"]) {
      ok(`C. F1: "${s}" NÃO aparece dentro do svg`, !svg.includes(s));
    }
    for (const s of ["R$ 0", "R$ 1,20", "−R$ 0,80", "26,00", "32,00"]) {
      ok(`C. F1: tick "${s}" aparece no svg`, svg.includes(s));
    }
    const nums = [...svg.matchAll(/<text[^>]*>(\d+)<\/text>/g)].map((m) => m[1]);
    ok("C. F1: círculos numerados 1..5 no svg", ["1", "2", "3", "4", "5"].every((n) => nums.includes(n)));
    ok("C. F1: cenário com result null (6) NÃO vira ponto", !nums.includes("6"));
    const fontes = [...svg.matchAll(/font-size[:=]"?(\d+(?:\.\d+)?)/g)].map((m) => parseFloat(m[1]));
    ok("C. F1: todo font-size no svg >= 11 e inteiro (e existe algum)",
      fontes.length > 0 && fontes.every((v) => v >= 11 && Number.isInteger(v)));
    for (const s of ["28,00", "30,00", "28,80", "29,10", "+1σ", "alvo"]) {
      ok(`C. F1: legenda (após </svg>) traz "${s}"`, depois.includes(s));
    }
    ok("C. F1: legenda traz opcoesLegStrike e opcoesSerieTotal",
      depois.includes(cp.opcoesLegStrike) && depois.includes(cp.opcoesSerieTotal));

    const F2 = { ...F1, unlimited_gain: true, max_gain: null };
    const out2 = renderToStaticMarkup(h(PayoffChart, { estrutura: F2, cp, dominio: { ...DOM, ganhoIlimitado: true } }));
    const r2 = recortar(out2);
    ok("C. F2 (ganho ilimitado): svg sem tick de teto 'R$ 1,20'", r2.svg.length > 200 && !r2.svg.includes("R$ 1,20"));
    ok("C. F2: legenda tem seta ↑ e opcoesGanhoIlimitado", r2.depois.includes("↑") && r2.depois.includes(cp.opcoesGanhoIlimitado));
    ok("C. F2: 'ganho máx. ' seguido de opcoesGanhoIlimitado (não de 0,00)",
      out2.includes("ganho máx. " + cp.opcoesGanhoIlimitado) && !/ganho máx\. 0,00/.test(out2));

    const out3 = renderToStaticMarkup(h(PayoffChart, { estrutura: { ...F1, payoff: [] }, cp, dominio: DOM }));
    ok("C. F3 (sem curva): sem <svg e com opcoesSemEstrutura", !out3.includes("<svg") && out3.includes(cp.opcoesSemEstrutura));
  }
}
ok("C. sanidade: regex de números em <text> lê '<text x=\"1\">3</text>'",
  [..."<text x=\"1\">3</text>".matchAll(/<text[^>]*>(\d+)<\/text>/g)].length === 1);

console.log(fails ? `\n${fails} falha(s)` : "\nOK");
process.exit(fails ? 1 : 0);
