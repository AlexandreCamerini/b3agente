// Fase 41, plano 41-01, 2026-09-25 — GERADOR do baseline PRÉ-refactor das 4
// listas de tela do App.jsx (BottomNav.defs, tourPassos, ajudaSecoes,
// petTela/petSnapshot). Roda UMA VEZ, agora, antes da religação da 41-02
// (que substitui essas 4 listas por leitura do registro `web/src/telas.js`).
//
// Rodar de novo DEPOIS da 41-02 falha por desenho: o bloco `const defs` e a
// ternária `const petTela = …` deixam de existir no formato que este gerador
// procura (a religação os reescreve para ler do registro). O JSON gerado é a
// VERDADE CONGELADA do comportamento atual — não se regenera; é o fixture
// contra o qual `web/tests/test_telas_registro.mjs` compara o registro novo
// (D-04: refactor puro, zero mudança visível).
//
// Uso: node tests/fixtures/gerar_telas_baseline_41.mjs [caminho/para/App.jsx]
// Sem argumento, lê `web/src/App.jsx`. Aceita caminho alternativo para
// permitir auditoria contra uma revisão antiga:
//   git show <sha>:web/src/App.jsx > /tmp/App.jsx.antigo
//   node tests/fixtures/gerar_telas_baseline_41.mjs /tmp/App.jsx.antigo
import { readFileSync, writeFileSync } from "fs";
import { execFileSync } from "child_process";
import { createHash } from "crypto";
import { fileURLToPath, pathToFileURL } from "url";
import { dirname, join, resolve } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const appPath = process.argv[2] ? resolve(process.argv[2]) : join(here, "..", "..", "src", "App.jsx");
const outPath = join(here, "telas_baseline_41.json");

const app = readFileSync(appPath, "utf8");
const { COPY } = await import(pathToFileURL(join(here, "..", "..", "src", "copy.js")).href);

// -------------------------------------------------------- técnica extrair()
// (mesma de web/tests/test_tour_opcoes.mjs:44-65 — contagem de chaves, não
// regex de contagem, porque regex daria falso verde na primeira
// reorganização do array/função.)
function extrair(nome, fonte) {
  const i = fonte.indexOf("function " + nome + "(");
  if (i < 0) return null;
  let nivel = 0, dentro = false;
  for (let k = i; k < fonte.length; k++) {
    if (fonte[k] === "{") { nivel++; dentro = true; }
    else if (fonte[k] === "}") { nivel--; if (dentro && nivel === 0) return fonte.slice(i, k + 1); }
  }
  return null;
}

// ------------------------------------------------------------------ barra
const defsMatch = app.match(/const defs = (\[\[[\s\S]*?\]\]);/);
if (!defsMatch) throw new Error("const defs (BottomNav) não encontrado em " + appPath);
const defsFn = new Function("cp", "return " + defsMatch[1]); // eslint-disable-line no-new-func
const barra = {
  estudo: defsFn(COPY.estudo),
  operador: defsFn(COPY.operador),
  nulo: defsFn(null),
  vazio: defsFn({}),
};

// ------------------------------------------------------------------- tour
const fonteTour = extrair("tourPassos", app);
if (!fonteTour) throw new Error("tourPassos não encontrada em " + appPath);
const tourPassos = eval("(" + fonteTour + ")"); // eslint-disable-line no-eval
const tour = {
  estudo: tourPassos(COPY.estudo),
  operador: tourPassos(COPY.operador),
};

// ------------------------------------------------------------------ ajuda
const fonteAjuda = extrair("ajudaSecoes", app);
if (!fonteAjuda) throw new Error("ajudaSecoes não encontrada em " + appPath);
const ajudaSecoes = eval("(" + fonteAjuda + ")"); // eslint-disable-line no-eval
const ajuda = {
  "estudo,false": ajudaSecoes(COPY.estudo, false),
  "estudo,true": ajudaSecoes(COPY.estudo, true),
  "operador,false": ajudaSecoes(COPY.operador, false),
  "operador,true": ajudaSecoes(COPY.operador, true),
};

// ---------------------------------------------------------------- petTela
const petTelaMatch = app.match(/const petTela = ([\s\S]*?);\n/);
if (!petTelaMatch) throw new Error("const petTela não encontrado em " + appPath);
const petTelaFn = new Function("tab", "carteiraView", "return " + petTelaMatch[1]); // eslint-disable-line no-new-func
const tabs = ["evolucao", "radar", "mercado", "carteira", "opcoes", "perfil", "desconhecida"];
const views = ["main", "historico", "agente", undefined, "outra"];
const chaveView = (v) => (v === undefined ? "__undefined__" : v);
const petTela = {};
for (const tab of tabs) {
  petTela[tab] = {};
  for (const view of views) {
    petTela[tab][chaveView(view)] = petTelaFn(tab, view);
  }
}

// --------------------------------------------------------- switchPetSnapshot
const inicioMarcador = "switch (petTela) {";
const fimMarcador = "}, [petTela, data, quotes, wlScan]);";
const iInicio = app.indexOf(inicioMarcador);
const iFim = app.indexOf(fimMarcador, iInicio);
if (iInicio < 0 || iFim < 0) throw new Error("bloco do switch petSnapshot não encontrado em " + appPath);
const blocoSwitch = app.slice(iInicio, iFim + fimMarcador.length);
const casos = [...blocoSwitch.matchAll(/case "([a-z]+)":/g)].map((m) => m[1]);
const sha256 = createHash("sha256").update(blocoSwitch, "utf8").digest("hex");
const switchPetSnapshot = { casos, sha256 };

// ------------------------------------------------------------------ origem
let sha = "desconhecido";
try {
  sha = execFileSync("git", ["rev-parse", "HEAD"], { cwd: join(here, "..", "..", "..") }).toString().trim();
} catch { /* fora de um repo git — mantém "desconhecido" */ }
const _origem = {
  sha,
  data: new Date().toISOString().slice(0, 10),
  nota: "NÃO regenerar após a 41-02 (D-04) — este JSON é a verdade congelada do comportamento PRÉ-refactor.",
  appPath,
};

const baseline = { _origem, barra, tour, ajuda, petTela, switchPetSnapshot };
writeFileSync(outPath, JSON.stringify(baseline, null, 2) + "\n", "utf8");
console.log("baseline gerado em " + outPath);
console.log(
  "barra.estudo=" + barra.estudo.length +
  " tour.estudo=" + tour.estudo.length +
  " ajuda(estudo,false)=" + ajuda["estudo,false"].length +
  " switch.casos=" + casos.length + " (" + casos.join(",") + ")"
);
