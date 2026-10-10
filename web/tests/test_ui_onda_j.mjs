// Onda J (2026-10-10) — quick 261010-f50: voltar do sistema fecha modais/sheets e recolhe card.
// P1: modelo puro (navStack). P2: fiação estática (App.jsx / OpcoesScreen.jsx).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import * as N from "../src/navStack.js";
import { voltar } from "../src/opcoes/navOpcoes.js";

const here = dirname(fileURLToPath(import.meta.url));
const src = (...p) => readFileSync(join(here, "..", "src", ...p), "utf8");
let falhas = 0;
const ok = (nome, cond) => { if (!cond) { falhas++; console.error("FALHA:", nome); } };
const semComentario = (t) => t.split("\n").filter((l) => !l.trim().startsWith("//")).join("\n");
// Chamada tolerante: export ausente vira asserção falha, não exceção.
const f = (nome, ...a) => (typeof N[nome] === "function" ? N[nome](...a) : undefined);
const E = (o) => Object.freeze({ tab: "radar", carteiraView: "main", perfilView: "hub", opcoes: null, conceito: null, ...o });

// ---------- P1
ok("P1 ORDEM_CAMADAS", JSON.stringify(N.ORDEM_CAMADAS) === JSON.stringify(["catalog", "buy", "sell", "stopAlvo", "radarDeep", "about", "tour", "auth", "pet", "conceito", "borisIntro", "tech"]));
ok("P1 prof modal", f("profundidade", E({ modais: ["buy"] })) === 1);
ok("P1 prof carteira+2 modais", f("profundidade", E({ tab: "carteira", carteiraView: "historico", modais: ["sell", "tech"] })) === 3);
ok("P1 prof id desconhecido", f("profundidade", E({ modais: ["xyz"] })) === 0);
ok("P1 prof modais nao-array", f("profundidade", E({ modais: "buy" })) === 0);
ok("P1 prof card mercado", f("profundidade", E({ tab: "mercado", cardExpandido: true })) === 1);
ok("P1 prof opcoes hub sheet 1", f("profundidade", E({ tab: "opcoes", opcoes: { nivel: "hub", temTicker: false, sheet: 1 } })) === 1);
ok("P1 prof opcoes montar sheet 3", f("profundidade", E({ tab: "opcoes", opcoes: { nivel: "montar", temTicker: true, sheet: 3 } })) === 5);
ok("P1 prof radar card+deep", f("profundidade", E({ tab: "radar", cardExpandido: true, modais: ["radarDeep"] })) === 2);

ok("P1 profTela ignora camadas", f("profundidadeDeTela", E({ tab: "carteira", carteiraView: "historico", modais: ["buy"], cardExpandido: true, conceito: { trilha: 1 } })) === 3);
ok("P1 profTela ignora sheet", f("profundidadeDeTela", E({ tab: "opcoes", opcoes: { nivel: "escada", temTicker: true, sheet: 2 } })) === 2);

for (const [i, e] of [
  E({ tab: "carteira", carteiraView: "historico" }), E({ tab: "carteira" }),
  E({ tab: "perfil", perfilView: "glossario" }), E({ tab: "perfil" }),
  E({ conceito: { trilha: 2 } }),
  E({ tab: "opcoes", opcoes: { nivel: "confirmar", temTicker: true } }), E({ tab: "opcoes" }),
].entries()) ok(`P1 retrocompat Onda B #${i}`, f("profundidade", e) === f("profundidadeDeTela", e) && f("profundidade", e) !== undefined);

ok("P1 modalDoTopo tech>buy", f("modalDoTopo", E({ modais: ["tech", "buy"] })) === "tech" && f("modalDoTopo", E({ modais: ["buy", "tech"] })) === "tech");
ok("P1 modalDoTopo sell>buy", f("modalDoTopo", E({ modais: ["buy", "sell"] })) === "sell");
ok("P1 conceito acima de pet", f("camadaDoTopo", E({ modais: ["pet"], conceito: { trilha: 0 } })) === "conceito" && f("modalDoTopo", E({ modais: ["pet"], conceito: { trilha: 0 } })) === "pet");
ok("P1 nada aberto", f("camadaDoTopo", E({})) === null && f("modalDoTopo", E({})) === null);

ok("P1 sub modal", f("subirNivel", E({ modais: ["buy"] })) === "fecharModal");
ok("P1 sub buy+conceito0", f("subirNivel", E({ modais: ["buy"], conceito: { trilha: 0 } })) === "conceitoFechar");
ok("P1 sub buy+conceito1", f("subirNivel", E({ modais: ["buy"], conceito: { trilha: 1 } })) === "conceitoVoltar");
ok("P1 sub tech+conceito", f("subirNivel", E({ modais: ["tech"], conceito: { trilha: 0 } })) === "fecharModal");
ok("P1 sub borisIntro+conceito", f("subirNivel", E({ modais: ["borisIntro"], conceito: { trilha: 0 } })) === "fecharModal");
ok("P1 sub carteira+sell", f("subirNivel", E({ tab: "carteira", carteiraView: "historico", modais: ["sell"] })) === "fecharModal");
ok("P1 sub carteira+card", f("subirNivel", E({ tab: "carteira", carteiraView: "historico", cardExpandido: true })) === "carteiraMain");
ok("P1 sub opcoes hub sheet", f("subirNivel", E({ tab: "opcoes", opcoes: { nivel: "hub", temTicker: false, sheet: 1 } })) === "opcoesVoltar");
ok("P1 sub mercado card", f("subirNivel", E({ tab: "mercado", cardExpandido: true })) === "recolherCard");
ok("P1 sub radar card+deep", f("subirNivel", E({ tab: "radar", cardExpandido: true, modais: ["radarDeep"] })) === "fecharModal");
ok("P1 sub mercado sem card", f("subirNivel", E({ tab: "mercado", cardExpandido: false })) === null);
ok("P1 raiz null", ["radar", "carteira", "perfil", "opcoes", "evolucao", "mercado"].every((tab) => f("subirNivel", E({ tab })) === null));

// Contrato subir = -1 (simulador local das ações)
function aplicar(e, acao) {
  const o = { ...e };
  switch (acao) {
    case "fecharModal": { const t = f("modalDoTopo", e); o.modais = (e.modais || []).filter((m) => m !== t); break; }
    case "conceitoVoltar": o.conceito = { trilha: e.conceito.trilha - 1 }; break;
    case "conceitoFechar": o.conceito = null; break;
    case "carteiraMain": o.carteiraView = "main"; break;
    case "perfilHub": o.perfilView = "hub"; break;
    case "opcoesVoltar":
      if (e.opcoes.sheet > 0) o.opcoes = { ...e.opcoes, sheet: e.opcoes.sheet - 1 };
      else { const v = voltar({ nivel: e.opcoes.nivel, ticker: e.opcoes.temTicker ? "X" : "" }); o.opcoes = { nivel: v.nivel, temTicker: !!v.ticker, sheet: 0 }; }
      break;
    case "recolherCard": o.cardExpandido = false; break;
    default: return e;
  }
  return o;
}
const estados = [
  E({ modais: ["buy"] }),
  E({ modais: ["buy", "sell"] }),
  E({ modais: ["catalog", "tech", "pet"] }),
  E({ modais: ["buy"], conceito: { trilha: 1 } }),
  E({ modais: ["buy"], conceito: { trilha: 0 } }),
  E({ tab: "carteira", carteiraView: "historico", modais: ["sell"] }),
  E({ tab: "carteira", carteiraView: "historico", cardExpandido: true }),
  E({ tab: "perfil", perfilView: "glossario", modais: ["about"] }),
  E({ tab: "mercado", cardExpandido: true }),
  E({ tab: "mercado", cardExpandido: true, modais: ["tour"] }),
  E({ tab: "radar", cardExpandido: true, modais: ["radarDeep"] }),
  E({ tab: "radar", cardExpandido: true }),
  E({ tab: "opcoes", opcoes: { nivel: "hub", temTicker: false, sheet: 1 } }),
  E({ tab: "opcoes", opcoes: { nivel: "montar", temTicker: true, sheet: 3 } }),
  E({ tab: "opcoes", opcoes: { nivel: "confirmar", temTicker: true, sheet: 0 } }),
  E({ tab: "opcoes", opcoes: { nivel: "escada", temTicker: true, sheet: 2 }, conceito: { trilha: 1 }, modais: ["auth"] }),
  E({ modais: ["borisIntro", "auth", "about"], conceito: { trilha: 2 } }),
];
estados.forEach((e, i) => {
  const p = f("profundidade", e);
  const a = f("subirNivel", e);
  ok(`P1 subir=-1 #${i}`, p > 0 && typeof a === "string" && f("profundidade", aplicar(e, a)) === p - 1);
});
for (const e of [E({}), E({ tab: "mercado" }), E({ tab: "carteira" }), E({ tab: "opcoes", opcoes: { nivel: "hub", temTicker: false, sheet: 0 } })])
  ok("P1 prof 0 => null", f("profundidade", e) === 0 && f("subirNivel", e) === null);

const ps = (...a) => f("profundidadeSheetsOpcoes", ...a);
ok("P1 sheets opcoes", ps(false, null) === 0 && ps(true, null) === 1 && ps(false, { trilha: [] }) === 1 && ps(false, { trilha: ["a", "b"] }) === 3 && ps(true, { trilha: ["a"] }) === 2);
ok("P1 sheets opcoes invalidas", ps() === 0 && ps(undefined, undefined) === 0 && ps("x", 3) === 0 && ps(null, null) === 0);

const cf = (a) => f("campoDeTextoFocado", a);
ok("P1 campo texto", cf({ tag: "INPUT", type: "text" }) === true && cf({ tag: "input", type: "number" }) === true && cf({ tag: "INPUT" }) === true);
ok("P1 campo nao-texto", ["range", "checkbox", "radio", "button", "submit"].every((type) => cf({ tag: "INPUT", type }) === false));
ok("P1 campo textarea/select/editavel", cf({ tag: "TEXTAREA" }) === true && cf({ tag: "SELECT" }) === true && cf({ tag: "DIV", editavel: true }) === true);
ok("P1 campo div/nulo", cf({ tag: "DIV" }) === false && cf(undefined) === false && cf(null) === false);

ok("P1 navStack puro", !/\bwindow\b|\bdocument\b|\bhistory\b|from "react"|^import /m.test(semComentario(src("navStack.js"))));

// ---------- P2
const app = semComentario(src("App.jsx"));
const opc = semComentario(src("opcoes", "OpcoesScreen.jsx"));
const imp = (app.match(/import \{[^}]*\} from "\.\/navStack\.js";/) || [""])[0];
ok("P2 import navStack", ["profundidadeDeTela", "modalDoTopo", "campoDeTextoFocado"].every((s) => imp.includes(s)));
ok("P2 estadoNav modais/cardExpandido", app.includes("modais:") && app.includes("cardExpandido:"));
ok("P2 profTela", app.includes("const profTela = profundidadeDeTela(estadoNav);"));
ok("P2 transTelaRef profTela", app.includes("transTelaRef = useRef({ tab, prof: profTela })") && app.includes("transicaoDe(ant, { tab, prof: profTela })"));
ok("P2 regex Onda B layoutEffect", /useLayoutEffect\(\(\) => \{\s*const ant = transTelaRef\.current;/.test(app));

{
  const i = app.indexOf("aplicarSubidaRef.current = (acao) =>");
  const rest = i >= 0 ? app.slice(i) : "";
  const j = rest.indexOf("useEffect(");
  const rec = j >= 0 ? rest.slice(0, j) : "";
  ok("P2 recorte aplicarSubida existe", rec.length > 0);
  for (const s of ['"fecharModal"', '"recolherCard"', "modalDoTopo(estadoNavRef.current)", "catalog: A.closeCatalog", "buy: A.closeBuy", "sell: A.closeSell", "stopAlvo: A.closeStopAlvo", "about: A.closeAbout", "tour: A.closeTour", "tech: A.closeTech", "setAuthOpen(false)", "setPetOpen(false)", "marcarBorisIntroVisto()", 'radarFecharRef.current("deep")', 'radarFecharRef.current("card")', "A.toggleExpand("])
    ok(`P2 aplicarSubida contém ${s}`, rec.includes(s));
  ok("P2 aplicarSubida sem motor financeiro", !/\bstore\.(buy|sell)\(|A\.(buy|sell|confirmBuy|confirmSell|executeBuy|executeSell)\(/.test(rec));
}
ok("P2 onPop retorna boolean", /if \(!\(acao && aplicarSubidaRef\.current && aplicarSubidaRef\.current\(acao\)\)\) empurradasRef\.current = 0;/.test(app));
ok("P2 onStart Onda G intacto", app.includes('e.target.closest("canvas, input[type=\\"range\\"], [data-sem-gesto-voltar]")'));
ok("P2 onStart campoDeTextoFocado x2 + activeElement", (app.match(/campoDeTextoFocado\(/g) || []).length >= 2 && app.includes("document.activeElement"));
ok("P2 ctx reportarNavOpcoes sheet", app.includes("reportarNavOpcoes: (nivel, temTicker, sheet) =>"));
ok("P2 ctx radar", app.includes("reportarNavRadar:") && app.includes("registrarFecharRadar:"));
ok("P2 radarNav state/ref", app.includes("const [radarNav, setRadarNav] = useState({ card: false, deep: false });") && app.includes("const radarFecharRef = useRef(null);"));
{
  const i = app.indexOf("function RadarScreen(");
  const rest = i >= 0 ? app.slice(i + 1) : "";
  const j = rest.indexOf("\nfunction ");
  const rec = j >= 0 ? rest.slice(0, j) : rest;
  for (const s of ["ctx.reportarNavRadar(!!openTicker, !!deepFor)", "ctx.registrarFecharRadar(", "setDeepFor(null)", "setOpenTicker(null)"])
    ok(`P2 RadarScreen contém ${s}`, rec.includes(s));
}
ok("P2 OpcoesScreen sheet", opc.includes("profundidadeSheetsOpcoes(vigiasAberto, verbeteAberto)") && opc.includes("ctx.reportarNavOpcoes(nav.nivel, !!nav.ticker, sheetOpcoes)"));
{
  const i = opc.indexOf("ctx.registrarVoltarOpcoes(() =>");
  const rest = i >= 0 ? opc.slice(i) : "";
  const j = rest.indexOf("return () =>");
  const rec = j >= 0 ? rest.slice(0, j) : "";
  ok("P2 OpcoesScreen voltar fecha sheets antes", ["setVerbeteAberto(", "setVigiasAberto(false)", "setNav((n) => voltar(n))"].every((s) => rec.includes(s)));
}
ok("P2 reduced-motion 2 blocos", (app.match(/@media \(prefers-reduced-motion: reduce\)\{/g) || []).length === 2);
ok("P2 petTela intacto", app.includes("const petTela = telaDoAssistente(tab, carteiraView);"));
ok("P2 onDepois intacto", app.includes("onDepois={() => ctx.marcarBorisIntroVisto()}"));

if (falhas) { console.error(`${falhas} falha(s)`); process.exit(1); }
console.log("test_ui_onda_j: ok");
