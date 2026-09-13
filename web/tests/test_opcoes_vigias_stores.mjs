// Fase 27 — paridade do bloco `mcp*` nos DOIS stores, e o par novo em api.js.
//
// QUAL DEFEITO ESTE GUARDIÃO REPROVA: método `mcp*` que existe só num store.
// O sintoma não é um erro de build nem um teste vermelho — é o app NATIVO
// caindo em `undefined is not a function` na hora do clique, com o web
// funcionando perfeitamente ao lado. Foi exatamente a forma de dois incidentes
// reais deste repositório (carteira nativa que não sincronizava,
// F10-20260807-05; `initialBudget` sem sync device→servidor, F10-20260809-05).
// O CLAUDE.md trata isso como invariante: "método novo entra nos DOIS".
//
// Complementa `test_fase3_paridade_stores_generica.mjs` (que cobre TODOS os
// métodos) estreitando sobre a superfície da aba Opções e acrescentando o que
// aquele não vê: o método pode existir nos dois stores e delegar para uma
// função que NÃO existe em `api.js` — paridade perfeita entre dois caminhos
// igualmente quebrados.
//
// Derivado da FONTE, nunca de uma lista redigitada: uma lista aqui seria uma
// terceira cópia dos nomes, e a que ninguém atualiza.
//
// Roda sem build: `node web/tests/test_opcoes_vigias_stores.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const apiSrc = readFileSync(join(here, "..", "src", "api.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// O par que esta fase acrescenta. São os ÚNICOS nomes literais do arquivo, e
// de propósito: a assertiva (a) prova que eles chegaram, as demais provam a
// paridade do conjunto INTEIRO, derivado da fonte.
const NOVOS = ["mcpVigias", "mcpSetupsListar"];

// ------------------------------------------------------- localizar blocos
const iServer = src.indexOf("function serverStore()");
const iDevice = src.indexOf("function deviceStore()");
const iExport = src.indexOf("export const store");
if (iServer < 0 || iDevice < 0 || iExport < 0) {
  console.error("FALHOU: persistence.js foi reestruturado — serverStore()/deviceStore()/`export const store` não encontrados");
  process.exit(1);
}
const returnServer = src.indexOf("return {", iServer);
const returnDevice = src.indexOf("return {", iDevice);
if (returnServer < 0 || returnServer >= iDevice || returnDevice < 0 || returnDevice >= iExport) {
  console.error("FALHOU: o `return {` de um dos stores não foi encontrado onde se esperava");
  process.exit(1);
}
const blocoServer = src.slice(returnServer, iDevice);
const blocoDevice = src.slice(returnDevice, iExport);

const RESERVADAS = new Set(["if", "for", "while", "switch", "return", "else", "try", "catch", "function", "const", "let", "var"]);

// Mesma extração do guardião genérico (indentação de 4 espaços = nível do
// objeto retornado; comentário nunca conta), estreitada ao prefixo `mcp`.
function extrairMcp(bloco, shorthand) {
  const nomes = new Set();
  for (const linha of bloco.split("\n")) {
    const trim = linha.trim();
    if (trim.startsWith("//") || trim.startsWith("*")) continue;
    let m = linha.match(/^\s{4}([A-Za-z_$][\w$]*)\s*:\s*/);
    if (!m && shorthand) m = linha.match(/^\s{4}(?:async\s+)?([A-Za-z_$][\w$]*)\s*\(/);
    if (m && !RESERVADAS.has(m[1]) && m[1].startsWith("mcp")) nomes.add(m[1]);
  }
  return nomes;
}

const noServer = extrairMcp(blocoServer, false);
const noDevice = extrairMcp(blocoDevice, true);

// ------------------------------------------------------------ (a) chegaram
for (const nome of NOVOS) {
  ok(`(a) ${nome} existe no serverStore`, noServer.has(nome));
  ok(`(a) ${nome} existe no deviceStore`, noDevice.has(nome));
}

// ------------------------------------------------------------ (b) sanidade
// Se a regex quebrar por mudança de formatação, o guardião precisa FALHAR em
// vez de virar um no-op que aprova tudo calado.
ok(`(b) a extração rendeu >= 10 métodos mcp* no serverStore (achou ${noServer.size})`, noServer.size >= 10);
ok(`(b) a extração rendeu >= 10 métodos mcp* no deviceStore (achou ${noDevice.size})`, noDevice.size >= 10);

// ------------------------------------------- (c) igualdade de CONJUNTO
const soNoDevice = [...noDevice].filter((m) => !noServer.has(m));
const soNoServer = [...noServer].filter((m) => !noDevice.has(m));
ok(
  soNoDevice.length === 0
    ? "(c) nenhum método mcp* existe só no deviceStore"
    : `(c) FALHOU: [${soNoDevice.join(", ")}] só no deviceStore — método novo entra nos DOIS stores, no MESMO commit (CLAUDE.md).`,
  soNoDevice.length === 0
);
ok(
  soNoServer.length === 0
    ? "(d) nenhum método mcp* existe só no serverStore"
    : `(d) FALHOU: [${soNoServer.join(", ")}] só no serverStore — no app nativo isso vira "undefined is not a function" no clique, em silêncio no web.`,
  soNoServer.length === 0
);

// -------------------------- (e) todo método dos stores existe em api.js
// A paridade entre os dois stores não basta: os dois podem delegar para a
// mesma função inexistente.
const semApi = [...noServer].filter((m) => !new RegExp(`\\b${m}\\s*:`).test(apiSrc));
ok(
  semApi.length === 0
    ? "(e) todo método mcp* dos stores tem a função correspondente em api.js"
    : `(e) FALHOU: [${semApi.join(", ")}] não existe em web/src/api.js — os dois stores delegam para o vazio.`,
  semApi.length === 0
);

// ------------------------ (f) as duas rotas novas, e os DOIS custos
// O par existe porque são dois custos diferentes, e trocar um pelo outro é o
// defeito que o ADR-027 §3.3 proíbe (custo de MCP só em clique explícito).
ok(
  "(f) mcpVigias aponta para /api/options/vigias — FORA do prefixo /mcp/, porque é custo ZERO",
  /mcpVigias\s*:\s*\(\)\s*=>\s*req\("GET",\s*"\/api\/options\/vigias"/.test(apiSrc)
);
ok(
  "(f) mcpSetupsListar aponta para /api/options/mcp/setups — custo 2, declarado",
  /mcpSetupsListar\s*:\s*\(\)\s*=>\s*req\("GET",\s*"\/api\/options\/mcp\/setups"/.test(apiSrc)
);

console.log(fails === 0 ? "\nTODOS OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
