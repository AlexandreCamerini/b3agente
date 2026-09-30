// Guardião — one-shot ctx.goOpcoes("oportunidades", { abrirTicker }) (Fase 45, D-05).
// Roda isolado: `node web/tests/test_opcoes_abrir_ticker.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { abrirTickerOpcoes } from "../src/opcoes/memoriaOpcoes.js";

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};
const ler = (rel) => readFileSync(fileURLToPath(new URL(rel, import.meta.url)), "utf8");
const semComentarios = (s) => s.split("\n").map((l) => l.replace(/\/\/.*$/, "")).join("\n");

// (a) puro
ok("abrirTicker na carteira -> ticker", abrirTickerOpcoes("UGPA3", [{ t: "UGPA3" }]) === "UGPA3");
ok("abrirTicker fora da carteira -> null", abrirTickerOpcoes("VALE3", [{ t: "UGPA3" }]) === null);
ok("abrirTicker vazio -> null", abrirTickerOpcoes("", [{ t: "UGPA3" }]) === null);
ok("abrirTicker não-string -> null", abrirTickerOpcoes(null, [{ t: "UGPA3" }]) === null && abrirTickerOpcoes(42, [{ t: "UGPA3" }]) === null && abrirTickerOpcoes(undefined, [{ t: "UGPA3" }]) === null);
ok("abrirTicker carteira não-array -> null", abrirTickerOpcoes("UGPA3", null) === null && abrirTickerOpcoes("UGPA3", undefined) === null);

// (b) App.jsx
const app = semComentarios(ler("../src/App.jsx"));
ok("App: estado opcoesAbrirTicker useState(null)", /const \[opcoesAbrirTicker, setOpcoesAbrirTicker\] = useState\(null\)/.test(app));
ok("App: goOpcoes aceita (aba, opts)", /goOpcoes:\s*\(aba,\s*opts\)\s*=>/.test(app));
ok("App: ticker só gravado com typeof opts.abrirTicker === \"string\"", /typeof opts\.abrirTicker === "string" && opts\.abrirTicker/.test(app));
ok("App: grava memória {ticker, aba: oportunidades}", /setOpcoesMemoria\(\{ ticker: opts\.abrirTicker, aba: "oportunidades" \}\)/.test(app));
ok("App: ctx expõe opcoesAbrirTicker", /^\s*opcoesAbrirTicker,\s*$/m.test(app));
ok("App: ctx expõe limparOpcoesAbrirTicker", /limparOpcoesAbrirTicker:\s*\(\)\s*=>\s*setOpcoesAbrirTicker\(null\)/.test(app));
const reset = app.match(/const _resetScopeState = \(\) => \{[\s\S]*?\n  \};/);
ok("App: _resetScopeState limpa opcoesAbrirTicker (T-45-05)", !!reset && reset[0].includes("setOpcoesAbrirTicker(null)"));
ok("App: goOpcoes sem opts mantém setOpcoesAbaInicial + navigate", /if \(typeof aba === "string"\) setOpcoesAbaInicial\(aba\);/.test(app));

// (c) OpcoesScreen.jsx
const scr = semComentarios(ler("../src/opcoes/OpcoesScreen.jsx"));
ok("Tela: importa abrirTickerOpcoes", /import \{[^}]*abrirTickerOpcoes[^}]*\} from "\.\/memoriaOpcoes\.js"/.test(scr));
ok("Tela: oportunidadeAberta com inicializador lazy", /useState\(\(\) => abrirTickerOpcoes\(ctx && ctx\.opcoesAbrirTicker, carteira\)\)/.test(scr));
ok("Tela: useEffect [] limpa o one-shot", /useEffect\(\(\) => \{\s*if \(ctx && ctx\.opcoesAbrirTicker && ctx\.limparOpcoesAbrirTicker\) ctx\.limparOpcoesAbrirTicker\(\);\s*\}, \[\]\);/.test(scr));

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntudo ok");
