// Onda B (2026-10-08) — quick 261008-1ar. Parte 1: navStack puro. Parte 2: fiação estática.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import * as N from "../src/navStack.js";
import { NIVEIS, voltar } from "../src/opcoes/navOpcoes.js";

const here = dirname(fileURLToPath(import.meta.url));
const src = (...p) => readFileSync(join(here, "..", "src", ...p), "utf8");
let falhas = 0;
const ok = (nome, cond) => { if (!cond) { falhas++; console.error("FALHA:", nome); } };
const semComentario = (t) => t.split("\n").filter((l) => !l.trim().startsWith("//")).join("\n");

// ---- parte 1
const E = (o) => Object.freeze({ tab: "radar", carteiraView: "main", perfilView: "hub", opcoes: null, conceito: null, ...o });
ok("carteira historico", N.profundidade(E({ tab: "carteira", carteiraView: "historico" })) === 1);
ok("carteira main", N.profundidade(E({ tab: "carteira" })) === 0);
ok("perfil glossario", N.profundidade(E({ tab: "perfil", perfilView: "glossario" })) === 1);
ok("perfil hub", N.profundidade(E({ tab: "perfil" })) === 0);
ok("conceito trilha 2", N.profundidade(E({ conceito: { trilha: 2 } })) === 3);
const po = N.profundidadeOpcoes;
ok("opcoes niveis", po("hub") === 0 && po("objetivo") === 1 && po("escada") === 2 && po("confirmar") === 3 && po("montar", true) === 2 && po("montar", false) === 1 && po("xx") === 0);
ok("profundidade opcoes via estado", N.profundidade(E({ tab: "opcoes", opcoes: { nivel: "confirmar", temTicker: true } })) === 3);
ok("opcoes nulo", N.profundidade(E({ tab: "opcoes" })) === 0);
for (const nivel of NIVEIS) for (const ticker of ["", "PETR4"]) {
  const e = { nivel, ticker };
  const p = po(nivel, !!ticker);
  if (p > 0) {
    const v = voltar(e);
    ok(`invariante ${nivel}/${ticker}`, po(v.nivel, !!v.ticker) === p - 1);
  }
}
ok("subir conceito voltar", N.subirNivel(E({ conceito: { trilha: 1 } })) === "conceitoVoltar");
ok("subir conceito fechar", N.subirNivel(E({ conceito: { trilha: 0 } })) === "conceitoFechar");
ok("subir carteira", N.subirNivel(E({ tab: "carteira", carteiraView: "agente" })) === "carteiraMain");
ok("subir perfil", N.subirNivel(E({ tab: "perfil", perfilView: "ia" })) === "perfilHub");
ok("subir opcoes", N.subirNivel(E({ tab: "opcoes", opcoes: { nivel: "escada", temTicker: true } })) === "opcoesVoltar");
ok("prioridade conceito", N.subirNivel(E({ tab: "carteira", carteiraView: "historico", conceito: { trilha: 0 } })) === "conceitoFechar");
ok("raiz null", ["radar", "carteira", "perfil", "opcoes", "evolucao"].every((tab) => N.subirNivel(E({ tab })) === null));
const rp = N.reconciliarPilha;
ok("rp push", JSON.stringify(rp(0, 2)) === '{"tipo":"push","n":2}');
ok("rp voltar", JSON.stringify(rp(3, 1)) === '{"tipo":"voltar","n":2}');
ok("rp nada", rp(1, 1).tipo === "nada" && rp(-1, NaN).tipo === "nada");
ok("chaves", N.chaveDeTela(E({ tab: "opcoes", opcoes: { nivel: "escada" } })) === "opcoes"
  && N.chaveDeScroll(E({ tab: "opcoes", opcoes: { nivel: "escada" } })) === "opcoes:escada"
  && N.chaveDeScroll(E({ tab: "carteira" })) === "carteira"
  && N.chaveDeTela(E({ tab: "carteira", carteiraView: "historico" })) === "carteira:historico"
  && N.chaveDeTela(E({ tab: "perfil", perfilView: "glossario" })) === "perfil:glossario"
  && N.chaveDeTela(E({ tab: "radar" })) === "radar");
ok("transicao", N.transicaoDe(null, { tab: "a", prof: 0 }) === null
  && N.transicaoDe({ tab: "a", prof: 0 }, { tab: "b", prof: 0 }) === "tab"
  && N.transicaoDe({ tab: "a", prof: 0 }, { tab: "a", prof: 1 }) === "entrar"
  && N.transicaoDe({ tab: "a", prof: 1 }, { tab: "a", prof: 0 }) === "voltar"
  && N.transicaoDe({ tab: "a", prof: 1 }, { tab: "a", prof: 1 }) === null);
ok("classe", N.classeDaTransicao("entrar") === "tela-entrar" && N.classeDaTransicao("x") === undefined);
ok("gesto", N.ehGestoVoltarBorda({ x0: 0, y0: 100, x1: 80, y1: 110 }) === true
  && !N.ehGestoVoltarBorda({ x0: 30, y0: 100, x1: 120, y1: 100 })
  && !N.ehGestoVoltarBorda({ x0: 5, y0: 100, x1: 50, y1: 100 })
  && !N.ehGestoVoltarBorda({ x0: 5, y0: 100, x1: 90, y1: 160 })
  && !N.ehGestoVoltarBorda({ x0: "a" }));
ok("entradasOrfas (override B1)", N.entradasOrfas({ b3nav: 3 }) === 3 && N.entradasOrfas(null) === 0 && N.entradasOrfas({}) === 0 && N.entradasOrfas({ b3nav: -2 }) === 0 && N.entradasOrfas({ b3nav: "x" }) === 0);
const nsrc = semComentario(src("navStack.js"));
ok("navStack puro", !/\bwindow\b|\bdocument\b|\bhistory\b|from "react"|^import /m.test(nsrc));

// ---- parte 2 (estática)
const app = semComentario(src("App.jsx"));
const opc = semComentario(src("opcoes", "OpcoesScreen.jsx"));
for (const s of ['addEventListener("popstate"', 'removeEventListener("popstate"', "history.pushState(", "history.go(-", "subirNivel(", "reconciliarPilha(", "entradasOrfas(", 'addListener("backButton"', 'getPlatform() !== "ios"', "ehGestoVoltarBorda(", "reportarNavOpcoes:", "registrarVoltarOpcoes:", "const petTela = telaDoAssistente(tab, carteiraView);", 'onBack={() => setCarteiraView("main")}'])
  ok(`App.jsx contém ${s}`, app.includes(s));
for (const s of ["ctx.reportarNavOpcoes(", "ctx.registrarVoltarOpcoes("]) ok(`OpcoesScreen contém ${s}`, opc.includes(s));

// ---- parte 3 (estado por tela + scroll por chave)
const { lerMemo } = await import("../src/uiMemo.js");
ok("lerMemo sem memo", lerMemo(undefined, "k", 7) === 7);
ok("lerMemo memo vazio", lerMemo(new Map(), "k", 7) === 7);
ok("lerMemo restaura", JSON.stringify(lerMemo(new Map([["k", { busy: true, res: 1 }]]), "k", null, (v) => ({ ...v, busy: false }))) === JSON.stringify({ busy: false, res: 1 }));
ok("lerMemo restaurar que lança -> inicial", lerMemo(new Map([["k", 1]]), "k", "ini", () => { throw new Error("x"); }) === "ini");
const memSrc = semComentario(src("uiMemo.js"));
ok("uiMemo sem disco", !/localStorage|sessionStorage/.test(memSrc));
for (const s of ['useEstadoMemorizado(ctx.uiMemo, "radar.busca", "")', 'useEstadoMemorizado(ctx.uiMemo, "radar.scan"', 'useEstadoMemorizado(ctx.uiMemo, "radar.deep"', 'useEstadoMemorizado(ctx.uiMemo, "glossario.busca", "")', "uiMemoRef = useRef(new Map())", "uiMemo: uiMemoRef.current", "chaveDeScroll(", "useLayoutEffect(", "scrollPorChaveRef.current.set(chaveScrollRef.current"])
  ok(`App.jsx contém ${s}`, app.includes(s));
ok("radar.scan restaura busy:false", /"radar\.scan"[^\n]*busy: false/.test(app));
ok("radar.deep descarta loading", /"radar\.deep"[^\n]*!x\.loading/.test(app));
ok("App sem storage no scroll/memo", !/(localStorage|sessionStorage)[^\n]*(scrollPorChave|uiMemo)/.test(app));

// ---- parte 4 (transições)
const css = [
  "@keyframes b3telaTab{ from{ opacity:0; transform:translateY(8px); } to{ opacity:1; transform:translateY(0); } }",
  ".b3 .tela-tab{ animation:b3telaTab 180ms ease-out; }",
  "@keyframes b3telaEntrar{ from{ opacity:0; transform:translateX(16px); } to{ opacity:1; transform:translateX(0); } }",
  ".b3 .tela-entrar{ animation:b3telaEntrar 220ms ease-out; }",
  "@keyframes b3telaFade{ from{ opacity:0; } to{ opacity:1; } }",
  ".b3 .tela-voltar{ animation:b3telaFade 180ms ease-out; }",
  "@keyframes b3sheetEnter{ from{ opacity:0; transform:translateY(24px); } to{ opacity:1; transform:translateY(0); } }",
  ".b3 .sheet-enter{ animation:b3sheetEnter 220ms ease-out; }",
];
for (const l of css) ok(`CSS: ${l.slice(0, 40)}`, app.includes(l));
// W2: o regex exato dos guardiões de motion (fase20/fase23) — nenhum @media novo.
ok("reduced-motion: exatamente 2 blocos", (app.match(/@media \(prefers-reduced-motion: reduce\)\{/g) || []).length === 2);
ok("App.jsx key={chaveTela} e classeDaTransicao(", app.includes("key={chaveTela}") && app.includes("classeDaTransicao("));
ok("classe de tela via useLayoutEffect (sem mutar ref no render)", /useLayoutEffect\(\(\) => \{\s*const ant = transTelaRef\.current;/.test(app));
ok("sheet-enter >= 4 em App.jsx", (app.match(/"sheet-enter"/g) || []).length >= 4);
ok("sheet-enter em entendimento.jsx", semComentario(src("entendimento.jsx")).includes('"sheet-enter"'));
ok("OpcoesScreen: classeNivel no wrapper dos 4 níveis (key por nível) e no montar", /key=\{nav\.nivel\} className=\{classeNivel\}/.test(opc) && (opc.match(/className=\{classeNivel\}/g) || []).length >= 2);
for (const k of ["b3telaTab", "b3telaEntrar", "b3telaFade", "b3sheetEnter"]) {
  const m = app.match(new RegExp("@keyframes " + k + "\\{([^\\n]*)"));
  ok(`${k} só opacity/transform`, !!m && !/\b(left|top|width|height|margin)\s*:/.test(m[1]));
}

// ---- parte 5 (Voltar único)
const vp = semComentario(src("VoltarPadrao.jsx"));
ok("VoltarPadrao: 44px nas duas variantes", (vp.match(/minHeight: "44px"/g) || []).length >= 2);
ok("VoltarPadrao: polyline do chevron", vp.includes('points="15 5 8 12 15 19"'));
ok("BackHeader usa VoltarPadrao", app.includes("<VoltarPadrao onClick={onBack} />"));
for (const [nome, t] of [["ObjetivoAtivo", src("opcoes", "ObjetivoAtivo.jsx")], ["EscadaObjetivo", src("opcoes", "EscadaObjetivo.jsx")], ["ConfirmarEstrutura", src("opcoes", "ConfirmarEstrutura.jsx")], ["OpcoesScreen", src("opcoes", "OpcoesScreen.jsx")], ["entendimento", src("entendimento.jsx")]]) {
  const c = semComentario(t);
  ok(`${nome} importa VoltarPadrao`, /import VoltarPadrao from "\.\.?\/(\.\.\/)?VoltarPadrao\.jsx"|import VoltarPadrao from "\.\.?\/VoltarPadrao\.jsx"/.test(c));
  ok(`${nome} sem <button> de voltar artesanal`, !/<button[^>]*>\s*(\{tx\("voltar"\)\}|\{opcoesEscadaTxt\(mode, "voltar"\)\}|‹ voltar)\s*<\/button>/.test(c));
}
{
  const { register } = await import("node:module");
  register("./_jsx_loader.mjs", import.meta.url);
  const { renderToStaticMarkup } = await import("react-dom/server");
  const React = (await import("react")).default;
  const VP = (await import("../src/VoltarPadrao.jsx")).default;
  const html = renderToStaticMarkup(React.createElement(VP, { rotulo: "‹ voltar", onClick() {} }));
  ok("SSR variante texto", html.includes("‹ voltar") && html.includes("min-height:44px"));
  const htmlI = renderToStaticMarkup(React.createElement(VP, { onClick() {} }));
  ok("SSR variante ícone", htmlI.includes('aria-label="Voltar"') && htmlI.includes("min-height:44px"));
}

if (falhas) { console.error(`${falhas} falha(s)`); process.exit(1); }
console.log("test_ui_onda_b: ok");
