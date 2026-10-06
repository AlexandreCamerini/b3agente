// Fase 49 (2026-10-06) — paridade de opcoesAnatomia nos dois stores + api.js; funções puras do hook. Guardião não se apaga. Roda: node web/tests/test_opcoes_anatomia_stores.mjs
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const lerSemComentario = (rel) => readFileSync(join(here, "..", "src", rel), "utf8")
  .split("\n").filter((l) => !l.trim().startsWith("//") && !l.trim().startsWith("*")).join("\n");

const src = lerSemComentario("persistence.js");
const apiSrc = lerSemComentario("api.js");
const hookSrc = lerSemComentario("opcoes/useAnatomia.js");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const iServer = src.indexOf("function serverStore()");
const iDevice = src.indexOf("function deviceStore()");
const iExport = src.indexOf("export const store");
const blocoServer = src.slice(src.indexOf("return {", iServer), iDevice);
const blocoDevice = src.slice(src.indexOf("return {", iDevice), iExport);

ok("opcoesAnatomia no serverStore (delegando)", /opcoesAnatomia\s*:\s*\(t,\s*q\)\s*=>\s*api\.opcoesAnatomia\(t,\s*q\)/.test(blocoServer));
ok("opcoesAnatomia no deviceStore (delegando)", /async opcoesAnatomia\(t,\s*q\)\s*\{[^}]*api\.opcoesAnatomia\(t,\s*q\)/.test(blocoDevice));
ok("api.js: rota /api/options/anatomia/ com ticker escapado",
  /opcoesAnatomia\s*:[^\n]*"\/api\/options\/anatomia\/"[^\n]*encodeURIComponent\(t\)/.test(apiSrc));
ok("rota não está sob /api/options/mcp/ (custo zero)",
  !(apiSrc.split("\n").find((l) => l.includes("opcoesAnatomia:")) || "").includes("/mcp/"));
ok("nenhum nome mcp*Anatomia", !/mcp\w*Anatomia/i.test(src + apiSrc + hookSrc));
ok("hook não importa persistence.js nem App.jsx", !/persistence|App\.jsx/.test(hookSrc));
ok("hook sem _cap_check/mcp", !/_cap_check|mcp/i.test(hookSrc));

const { chaveAnatomia, buscarAnatomia } = await import("../src/opcoes/useAnatomia.js");

ok("chaveAnatomia estável e ordenada",
  chaveAnatomia("ITUB4", ["B", "A"], ["X", "Y"], "estudo") === chaveAnatomia("ITUB4", ["A", "B"], ["Y", "X"], "estudo"));
ok("chaveAnatomia muda com o modo",
  chaveAnatomia("ITUB4", ["A"], ["X"], "estudo") !== chaveAnatomia("ITUB4", ["A"], ["X"], "operador"));
ok("chaveAnatomia tolera arrays ausentes", typeof chaveAnatomia("ITUB4", undefined, undefined, "estudo") === "string");

ok("store null -> null", (await buscarAnatomia(null, "ITUB4", [])) === null);
ok("store sem método -> null", (await buscarAnatomia({}, "ITUB4", [])) === null);

const chamadas = [];
const falso = { opcoesAnatomia: async (t, q) => { chamadas.push([t, q]); return { ok: 1 }; } };
await buscarAnatomia(falso, "ITUB4", ["ACOES", "ITUBJ493W2"]);
ok("excluir vira CSV, uma chamada",
  chamadas.length === 1 && chamadas[0][0] === "ITUB4" && JSON.stringify(chamadas[0][1]) === '{"excluir":"ACOES,ITUBJ493W2"}');
await buscarAnatomia(falso, "ITUB4", []);
ok("sem excluir -> {} sem chave", chamadas.length === 2 && JSON.stringify(chamadas[1][1]) === "{}");
const antes = chamadas.length;
ok("ticker vazio -> null sem chamar", (await buscarAnatomia(falso, "", [])) === null && (await buscarAnatomia(falso, undefined, [])) === null && chamadas.length === antes);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
