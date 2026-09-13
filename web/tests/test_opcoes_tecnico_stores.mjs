// Fase 27 (decisão D1) — paridade de `opcoesTecnico` nos DOIS stores, e a
// função correspondente em `api.js`.
//
// QUAL DEFEITO ESTE GUARDIÃO REPROVA: método que existe só no `serverStore`.
// O sintoma não é erro de build nem teste vermelho — é o app NATIVO caindo em
// `undefined is not a function` na hora do clique, com o web funcionando
// perfeitamente ao lado. Foi a forma de dois incidentes reais deste
// repositório (carteira nativa que não sincronizava, F10-20260807-05;
// `initialBudget` sem sync device→servidor, F10-20260809-05). O CLAUDE.md
// trata isso como invariante: "método novo entra nos DOIS".
//
// POR QUE ELE É NECESSÁRIO ALÉM DOS QUE JÁ EXISTEM: o irmão desta fase
// (`test_opcoes_vigias_stores.mjs`) filtra pelo prefixo `mcp` e NÃO vê este
// método — `opcoesTecnico` não tem esse prefixo, de propósito, porque `mcp*`
// neste código significa "custa cota do serviço" e esta rota não custa nada.
// O guardião genérico (`test_fase3_paridade_stores_generica.mjs`) vê o nome,
// mas não vê a segunda metade do problema: os dois stores podem delegar para
// uma função que NÃO existe em `api.js` — paridade perfeita entre dois
// caminhos igualmente quebrados.
//
// Derivado da FONTE, nunca de lista redigitada: uma lista aqui seria uma
// terceira cópia dos nomes, e a que ninguém atualiza.
//
// Roda sem build: `node web/tests/test_opcoes_tecnico_stores.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const apiSrc = readFileSync(join(here, "..", "src", "api.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// O ÚNICO nome literal do arquivo, e é o que esta fase acrescenta. Tudo o
// mais é derivado da fonte.
const NOVO = "opcoesTecnico";

// ------------------------------------------------------- localizar blocos
const iServer = src.indexOf("function serverStore()");
const iDevice = src.indexOf("function deviceStore()");
const iExport = src.indexOf("export const store");
if (iServer < 0 || iDevice < 0 || iExport < 0) {
  console.error("FALHOU: persistence.js foi reestruturado — serverStore()/deviceStore()/`export const store` não encontrados");
  process.exit(1);
}
// Fatiar a partir do `return {` de cada store (e não do início da função):
// o corpo de deviceStore() tem helpers com if/for na MESMA indentação dos
// métodos reais antes do seu `return {`.
const returnServer = src.indexOf("return {", iServer);
const returnDevice = src.indexOf("return {", iDevice);
if (returnServer < 0 || returnServer >= iDevice || returnDevice < 0 || returnDevice >= iExport) {
  console.error("FALHOU: o `return {` de um dos stores não foi encontrado onde se esperava");
  process.exit(1);
}
const blocoServer = src.slice(returnServer, iDevice);
const blocoDevice = src.slice(returnDevice, iExport);

const RESERVADAS = new Set(["if", "for", "while", "switch", "return", "else", "try", "catch", "function", "const", "let", "var"]);

// Mesma extração dos guardiões irmãos (indentação de 4 espaços = nível do
// objeto retornado; linha de comentário nunca conta), estreitada à superfície
// da aba Opções: `mcp*` (custa cota) + `opcoes*` (custo zero). São as duas
// famílias que a aba consome, e o ponto do par é justamente que elas se
// distinguem pelo CUSTO, não pela tela.
function extrairSuperficieDaAba(bloco, shorthand) {
  const nomes = new Set();
  for (const linha of bloco.split("\n")) {
    const trim = linha.trim();
    if (trim.startsWith("//") || trim.startsWith("*")) continue;
    let m = linha.match(/^\s{4}([A-Za-z_$][\w$]*)\s*:\s*/);
    if (!m && shorthand) m = linha.match(/^\s{4}(?:async\s+)?([A-Za-z_$][\w$]*)\s*\(/);
    if (m && !RESERVADAS.has(m[1]) && (m[1].startsWith("mcp") || m[1].startsWith("opcoes"))) {
      nomes.add(m[1]);
    }
  }
  return nomes;
}

const noServer = extrairSuperficieDaAba(blocoServer, false);
const noDevice = extrairSuperficieDaAba(blocoDevice, true);

// ------------------------------------------------------------ (a) chegou
ok(`(a) ${NOVO} existe no serverStore`, noServer.has(NOVO));
ok(`(a) ${NOVO} existe no deviceStore`, noDevice.has(NOVO));

// ------------------------------------------------------------ (b) sanidade
// Se a regex quebrar por mudança de formatação, o guardião precisa FALHAR em
// vez de virar um no-op que aprova tudo calado.
ok(`(b) a extração rendeu >= 11 métodos da aba no serverStore (achou ${noServer.size})`, noServer.size >= 11);
ok(`(b) a extração rendeu >= 11 métodos da aba no deviceStore (achou ${noDevice.size})`, noDevice.size >= 11);

// ------------------------------------------- (c)/(d) igualdade de CONJUNTO
const soNoDevice = [...noDevice].filter((m) => !noServer.has(m));
const soNoServer = [...noServer].filter((m) => !noDevice.has(m));
ok(
  soNoDevice.length === 0
    ? "(c) nenhum método da aba Opções existe só no deviceStore"
    : `(c) FALHOU: [${soNoDevice.join(", ")}] só no deviceStore — método novo entra nos DOIS stores, no MESMO commit (CLAUDE.md).`,
  soNoDevice.length === 0
);
ok(
  soNoServer.length === 0
    ? "(d) nenhum método da aba Opções existe só no serverStore"
    : `(d) FALHOU: [${soNoServer.join(", ")}] só no serverStore — no app nativo isso vira "undefined is not a function" no clique, em silêncio no web.`,
  soNoServer.length === 0
);

// -------------------------- (e) todo método dos stores existe em api.js
const semApi = [...noServer].filter((m) => !new RegExp(`\\b${m}\\s*:`).test(apiSrc));
ok(
  semApi.length === 0
    ? "(e) todo método da aba nos stores tem a função correspondente em api.js"
    : `(e) FALHOU: [${semApi.join(", ")}] não existe em web/src/api.js — os dois stores delegam para o vazio.`,
  semApi.length === 0
);

// ------------------------------- (f) a rota certa, e FORA do prefixo /mcp/
// A propriedade que interessa não é "a URL está escrita": é que ela NÃO está
// sob `/api/options/mcp/`. Rota sob esse prefixo é obrigada pelo guardião
// (iv) do backend a passar pelo cap — cobrar cota por uma leitura que não sai
// do processo seria cobrar pelo que não aconteceu (ADR-027, Emenda 2).
const linhaNova = (apiSrc.split("\n").find((l) => l.includes(`${NOVO}:`)) || "");
ok(
  `(f) ${NOVO} aponta para /api/options/tecnico/`,
  /opcoesTecnico\s*:\s*\(t,\s*q\)\s*=>\s*req\("GET",\s*"\/api\/options\/tecnico\//.test(apiSrc)
);
ok(
  `(f) ${NOVO} NÃO está sob /api/options/mcp/ — é leitura de custo ZERO`,
  linhaNova.length > 0 && !linhaNova.includes("/api/options/mcp/")
);

// --------------------------------- (g) o ticker é ESCAPADO antes de viajar
// Ticker é entrada do usuário (vem da carteira, mas o caminho é o mesmo das
// irmãs `mcpLeitura`/`mcpCadeia`): segmento de URL vindo de fora sempre passa
// por `encodeURIComponent`.
ok(
  `(g) ${NOVO} escapa o ticker com encodeURIComponent`,
  /opcoesTecnico\s*:[^\n]*encodeURIComponent\(t\)/.test(apiSrc)
);

console.log(fails === 0 ? "\nTODOS OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
