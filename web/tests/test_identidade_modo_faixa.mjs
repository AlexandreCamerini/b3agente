// Guardião da identidade de modo, opção C (2026-10-01): faixa de modo
// persistente no shell + destaque do card da watchlist.
//
// Contratos:
//  1) copy.js: faixaModoTitulo/faixaModoSub nos dois ramos, textos aprovados;
//  2) FaixaModo: fundo T.accent, texto T.onAccent, sem position/zIndex (item de
//     fluxo do shell flex: não cobre conteúdo e fica sob BottomSheet/modais);
//  3) montada UMA vez no return principal de App, entre <GlobalStyle /> e
//     <Ticker, nunca nos early returns loadErr/!data; o friso de 3px saiu;
//  4) AtivoCard: borda superior 3px no acento e CTA neutro preenchido só em
//     contexto "watchlist" (Radar compartilha o componente e fica fora);
//     `const card` global intacto.
// Roda sem build: `node web/tests/test_identidade_modo_faixa.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) copy ---------------------------------------------------------------
ok("copy estudo: faixaModoTitulo ESTUDO", COPY.estudo.faixaModoTitulo === "ESTUDO");
ok("copy estudo: faixaModoSub", COPY.estudo.faixaModoSub === "a IA orienta, você decide");
ok("copy operador: faixaModoTitulo OPERADOR", COPY.operador.faixaModoTitulo === "OPERADOR");
ok("copy operador: faixaModoSub", COPY.operador.faixaModoSub === "execução simulada");

// ---- 2) componente ---------------------------------------------------------
const fi = app.indexOf("function FaixaModo");
const faixa = fi < 0 ? "" : app.slice(fi, app.indexOf("\n}", fi));
ok("App.jsx define function FaixaModo", faixa.length > 0);
ok("FaixaModo: background T.accent e color T.onAccent", /background:\s*T\.accent/.test(faixa) && /color:\s*T\.onAccent/.test(faixa));
ok("FaixaModo: sem position nem zIndex", !/position\s*:/.test(faixa) && !/zIndex/.test(faixa));
ok("FaixaModo: não reduz opacity", !/opacity/.test(faixa));
ok("FaixaModo: sem hex literal", !/#[0-9a-fA-F]{3,6}\b/.test(faixa));

// ---- 3) montagem -----------------------------------------------------------
const ini = app.indexOf("<ThemeCtx.Provider value={{ key: themeKey, mode: appMode }}>");
const fim = app.indexOf("<BottomNav", ini);
const principal = ini < 0 || fim < 0 ? "" : app.slice(ini, fim);
ok("return principal localizado", principal.length > 0);
ok("<FaixaModo aparece exatamente uma vez no return principal", (principal.match(/<FaixaModo/g) || []).length === 1);
ok("<FaixaModo vem entre <GlobalStyle /> e <Ticker",
  principal.indexOf("<GlobalStyle />") < principal.indexOf("<FaixaModo") && principal.indexOf("<FaixaModo") < principal.indexOf("<Ticker"));
ok("FaixaModo alimentada por cp.faixaModoTitulo / cp.faixaModoSub",
  principal.includes("cp.faixaModoTitulo") && principal.includes("cp.faixaModoSub"));
ok("<FaixaModo só aparece uma vez em todo o App.jsx (fora dos early returns)", (app.match(/<FaixaModo/g) || []).length === 1);
ok("friso de 3px (linear-gradient accent/accentSoft) removido do return principal",
  !principal.includes("linear-gradient(90deg, ${T.accent}, ${T.accentSoft})"));

console.log(fails ? `\n${fails} verificação(ões) falharam` : "\ntodas as verificações passaram");
process.exit(fails ? 1 : 0);
