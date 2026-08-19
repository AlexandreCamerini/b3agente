// Fase 3, Task 1 (C-20/REPORT-01): guardião GENÉRICO exaustivo de paridade
// `deviceStore()` × `serverStore()` (`web/src/persistence.js`).
//
// Por que existe: hoje os dois stores são simétricos (58 métodos de cada
// lado, 0 assimetrias de nome), mas 28 dos 58 não têm NENHUMA referência em
// teste — a paridade depende do autor lembrar de escrever um teste pontual
// (`test_deep_parity.mjs`, `test_didatica_parity.mjs`, ...). Os dois
// incidentes reais que essa lacuna já causou:
//   1. Carteira nativa não sincronizava — `deviceStore.buy/sell/putPosition`
//      eram 100% locais (F10-20260807-05).
//   2. `initialBudget` sem sync device→servidor — campo lido no servidor,
//      escrito só localmente no aparelho (F10-20260809-05).
// Este guardião COMPLEMENTA os pontuais acima — nenhum deles é removido.
// Roda sem build: `node web/tests/test_fase3_paridade_stores_generica.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Assimetrias INTENCIONAIS, declaradas com justificativa — nunca uma lista
// nua. Item novo só entra aqui com motivo por escrito (a assertiva (d)
// abaixo garante que a allowlist não vira lixo acumulado).
const ASSIMETRIAS_INTENCIONAIS = {
  "_setDeviceScope": "assinatura difere de propósito (escopo é conceito do aparelho, não do servidor) — REPORT-01 C-20",
};

// --------------------------------------------------------- localizar blocos
const iServer = src.indexOf("function serverStore()");
const iDevice = src.indexOf("function deviceStore()");
const iExport = src.indexOf("export const store");
if (iServer < 0 || iDevice < 0 || iExport < 0) {
  console.error("FALHOU: persistence.js foi reestruturado — function serverStore()/deviceStore()/export const store não encontrados como esperado");
  process.exit(1);
}

// Fatiar a partir do `return {` de cada store, NÃO do início da função: o
// corpo de deviceStore() tem helpers/setup (com if/for no MESMO nível de
// indentação dos métodos reais) ANTES do seu `return {` — fatiar do início
// da função capturaria essas palavras reservadas como "métodos" falsos.
const returnServer = src.indexOf("return {", iServer);
const returnDevice = src.indexOf("return {", iDevice);
if (returnServer < 0 || returnServer >= iDevice) {
  console.error("FALHOU: `return {` de serverStore() não encontrado antes de deviceStore()");
  process.exit(1);
}
if (returnDevice < 0 || returnDevice >= iExport) {
  console.error("FALHOU: `return {` de deviceStore() não encontrado antes de `export const store`");
  process.exit(1);
}
const blocoServer = src.slice(returnServer, iDevice);
const blocoDevice = src.slice(returnDevice, iExport);

// ------------------------------------------------------- extração de nomes
// Segunda camada de defesa contra falso-positivo de regex, mesmo já fatiando
// a partir do `return {`: nunca aceitar palavra reservada do JS como nome de
// método.
const RESERVADAS = new Set(["if", "for", "while", "switch", "return", "else", "try", "catch", "function", "const", "let", "var"]);

function extrairNomes(bloco, estiloShorthand) {
  const nomes = new Set();
  for (const linha of bloco.split("\n")) {
    const trim = linha.trim();
    if (trim.startsWith("//") || trim.startsWith("*")) continue; // linha de comentário
    // Indentação de 4 espaços = nível do objeto retornado (não captura
    // helpers/funções aninhadas dentro de um método, que ficam mais fundo).
    let m = linha.match(/^\s{4}([A-Za-z_$][\w$]*)\s*:\s*/);
    if (!m && estiloShorthand) {
      m = linha.match(/^\s{4}(?:async\s+)?([A-Za-z_$][\w$]*)\s*\(/);
    }
    if (m && !RESERVADAS.has(m[1])) nomes.add(m[1]);
  }
  return nomes;
}

// serverStore: estilo único, propriedade-seta (`nome: (args) => ...`).
const nomesServer = extrairNomes(blocoServer, false);
// deviceStore: mistura propriedade-seta e método-atalho (`nome(args) {`),
// com ou sem `async`.
const nomesDevice = extrairNomes(blocoDevice, true);

// ----------------------------------------------------------- (a) sanidade
// Se a regex quebrar por uma mudança de formatação, o guardião precisa
// falhar em vez de virar no-op silencioso.
ok(`(a) serverStore rendeu >= 40 nomes na extração (achou ${nomesServer.size})`, nomesServer.size >= 40);
ok(`(a) deviceStore rendeu >= 40 nomes na extração (achou ${nomesDevice.size})`, nomesDevice.size >= 40);

// ------------------------------------------------- (b)/(c) zero assimetria
const soNoDevice = [...nomesDevice].filter((m) => !nomesServer.has(m) && !(m in ASSIMETRIAS_INTENCIONAIS));
const soNoServer = [...nomesServer].filter((m) => !nomesDevice.has(m) && !(m in ASSIMETRIAS_INTENCIONAIS));

ok(
  soNoDevice.length === 0
    ? "(b) nenhum método existe só em deviceStore (fora da allowlist)"
    : `(b) FALHOU: [${soNoDevice.join(", ")}] existe(m) só em deviceStore. Método novo entra nos DOIS stores no MESMO commit (CLAUDE.md, guardrail de paridade). Se a assimetria for intencional, declare-a em ASSIMETRIAS_INTENCIONAIS com a justificativa.`,
  soNoDevice.length === 0
);
ok(
  soNoServer.length === 0
    ? "(c) nenhum método existe só em serverStore (fora da allowlist)"
    : `(c) FALHOU: [${soNoServer.join(", ")}] existe(m) só em serverStore. Método novo entra nos DOIS stores no MESMO commit (CLAUDE.md, guardrail de paridade). Se a assimetria for intencional, declare-a em ASSIMETRIAS_INTENCIONAIS com a justificativa.`,
  soNoServer.length === 0
);

// --------------------------------------------- (d) allowlist não é lixo
const allowlistOrfa = Object.keys(ASSIMETRIAS_INTENCIONAIS).filter((m) => !nomesServer.has(m) && !nomesDevice.has(m));
ok(
  allowlistOrfa.length === 0
    ? "(d) todo nome da ASSIMETRIAS_INTENCIONAIS existe em pelo menos um dos dois stores"
    : `(d) FALHOU: [${allowlistOrfa.join(", ")}] está na allowlist mas não existe em NENHUM dos dois stores — allowlist virou lixo acumulado, remover.`,
  allowlistOrfa.length === 0
);

// ----------------------------------------------- (e) contagem total igual
// (descontadas as assimetrias declaradas, os dois lados têm que bater)
const totalServer = nomesServer.size;
const totalDevice = nomesDevice.size;
ok(
  `(e) contagem total igual descontadas as assimetrias declaradas (server=${totalServer}, device=${totalDevice})`,
  totalServer === totalDevice
);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
