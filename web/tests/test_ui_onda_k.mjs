// Onda K (2026-10-10, quick 261010-f51): destaque do Operador IA.
// A linha-botão neutra "Abrir o Operador IA →" virou o cartão OperadorIACard (Portfólio + Acompanhar),
// com estado lido só de data.agent/authUser/operador (operadorIA.js, puro). Sem estado inventado.
import { readFileSync } from "node:fs";
import { COPY } from "../src/copy.js";

let falhas = 0;
const ok = (nome, cond) => { console.log((cond ? "ok " : "FALHOU ") + nome); if (!cond) falhas++; };

const src = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");

function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(m.index, i);
}
const semComentarios = (s) => s
  .replace(/\{\/\*[\s\S]*?\*\/\}/g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const conta = (s, sub) => s.split(sub).length - 1;

// A) função pura
let estadoOperadorIA = null;
try { ({ estadoOperadorIA } = await import("../src/operadorIA.js")); } catch { /* RED */ }
ok("operadorIA.js importável", typeof estadoOperadorIA === "function");
if (typeof estadoOperadorIA === "function") {
  const e = estadoOperadorIA;
  ok("agent undefined → indisponivel", e({ agent: undefined, logado: true, operador: true }).codigo === "indisponivel");
  ok("agent null → indisponivel", e({ agent: null, logado: true, operador: true }).codigo === "indisponivel");
  ok("sem login → semConta", e({ agent: { serverEnabled: true }, logado: false, operador: true }).codigo === "semConta");
  const a = e({ agent: { serverEnabled: true, mode: "executar" }, logado: true, operador: true });
  ok("ligado/executar no Operador", a.codigo === "ligado" && a.modo === "executar");
  const b = e({ agent: { serverEnabled: true, mode: "executar" }, logado: true, operador: false });
  ok("Estudo nunca executa", b.codigo === "ligado" && b.modo === "sinalizar");
  const c = e({ agent: { serverEnabled: false, autonomous: true }, logado: true, operador: true });
  ok("desligado com autonomous → executar", c.codigo === "desligado" && c.modo === "executar");
  const d = e({ agent: {}, logado: true, operador: true });
  ok("agent vazio → desligado/sinalizar", d.codigo === "desligado" && d.modo === "sinalizar");
  ok("nenhum valor é number", [a, b, c, d].every((r) => Object.values(r).every((v) => typeof v !== "number")));
}

// B) COPY
for (const m of ["estudo", "operador"]) {
  const cp = COPY[m];
  ok(`${m}: operadorIACardDescricao string`, typeof cp.operadorIACardDescricao === "string" && cp.operadorIACardDescricao.length > 0);
  ok(`${m}: operadorIACardCta === "Abrir"`, cp.operadorIACardCta === "Abrir");
  const E = cp.operadorIAEstado;
  ok(`${m}: operadorIAEstado com 6 chaves`, !!E && typeof E === "object" &&
    ["indisponivel", "semConta", "ligado", "desligado", "executar", "sinalizar"].every((k) => typeof E[k] === "string" && E[k].length > 0));
  ok(`${m}: tituloOperadorIA`, cp.tituloOperadorIA === "Operador IA");
  ok(`${m}: linkOperadorIA sem seta`, !!cp.linkOperadorIA && !cp.linkOperadorIA.includes("→"));
  const desc = cp.operadorIACardDescricao || "";
  ok(`${m}: descrição cita simulad e corretora`, /simulad/i.test(desc) && /corretora/i.test(desc));
  ok(`${m}: descrição sem promessa`, !/lucro|ganh|garant|rentab|enriquec/i.test(desc));
}
ok("descrição difere entre modos", COPY.estudo.operadorIACardDescricao !== COPY.operador.operadorIACardDescricao);
ok("descrição de Estudo diz sinaliza", /sinaliza/i.test(COPY.estudo.operadorIACardDescricao || ""));

// C) componente
const comp = functionBody("OperadorIACard") || "";
ok("function OperadorIACard existe", comp.length > 0);
for (const tok of ["onClick={() => ctx.goAgente()}", "aria-label=", "estadoOperadorIA(", "cp.operadorIACardDescricao",
  "cp.operadorIACardCta", 'NavIcon id="agente"', "T.accent", 'minHeight: "56px"']) {
  ok(`OperadorIACard contém ${tok}`, comp.includes(tok));
}
ok("OperadorIACard sem CARD_PAD_X", !comp.includes("CARD_PAD_X"));
ok("import estadoOperadorIA", src.includes('import { estadoOperadorIA } from "./operadorIA.js";'));

// D) renderizações
const semC = semComentarios(src);
ok("<OperadorIACard  aparece 2x", conta(semC, "<OperadorIACard ") === 2);
const evo = functionBody("EvolucaoScreen") || "";
ok("1x em EvolucaoScreen", conta(semComentarios(evo), "<OperadorIACard ") === 1);
const iAg = src.indexOf('carteiraView === "agente"');
const iCart = src.indexOf("<CarteiraScreen ctx={ctx} />", iAg);
ok("Portfólio main renderiza o cartão antes de CarteiraScreen",
  iAg >= 0 && iCart > iAg && src.slice(iAg, iCart).includes("<OperadorIACard ctx={ctx} />"));

// E) linha-link removida
ok("sem 'cp.linkOperadorIA || \"Abrir o Operador IA →\"'", !src.includes('cp.linkOperadorIA || "Abrir o Operador IA →"'));
ok('sem literal "Abrir o Operador IA →"', !src.includes('"Abrir o Operador IA →"'));
ok("OperadorIACard definida antes de CarteiraScreen",
  src.indexOf("function OperadorIACard(") >= 0 && src.indexOf("function OperadorIACard(") < src.indexOf("function CarteiraScreen("));

// F) ajuda
const ajuda = functionBody("ajudaSecoes") || "";
ok("ajuda aponta para o cartão", ajuda.includes("cartão **Operador IA**"));
ok("ajuda sem a frase antiga", !ajuda.includes("toque em **Abrir o Operador IA**"));

// G) invariantes
ok("CARD_PAD_X px === 30", conta(src, "${CARD_PAD_X}px") === 30);
ok("reduced-motion === 2", conta(src, "@media (prefers-reduced-motion: reduce){") === 2);
ok("goAgente: () => === 1", conta(src, "goAgente: () =>") === 1);

if (falhas) { console.log(`\n${falhas} falha(s)`); process.exit(1); }
console.log("\nTUDO OK");
