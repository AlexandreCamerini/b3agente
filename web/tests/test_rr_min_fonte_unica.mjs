// ADR-015 (06-05) — Guardião cruzado do R:R mínimo (piso 1,5:1).
//
// O número vivia como 3 constantes Python independentes (skill_ref.RR_MIN,
// setups.RR_MINIMO, agent.RR_MINIMO) e 7 literais no front, com um único
// guardião cobrindo skill_ref (test_a8_rr_min_fonte_unica). Este runner fecha
// o lado front×backend: falha se o VALOR divergir (não a grafia da linha de
// código) e se qualquer interpolação ficar INERTE — `${RR_MIN_TXT}` dentro de
// aspas duplas ou em texto JSX cru não interpola, passa em grep e em build, e
// manda o nome da variável literal para a tela do usuário.
//
// IMPORTANTE — RR_MIN_TXT NÃO é literal de fonte no Python: skill_ref.py
// declara `RR_MIN = 1.5` (literal) e logo abaixo
// `RR_MIN_TXT = f"{RR_MIN:g}".replace(".", ",")` (COMPUTADO em runtime). Por
// isso o cruzamento aqui parseia só o NÚMERO com a regex `RR_MIN\s*=\s*([0-9.]+)`
// e DERIVA o texto esperado em JS — nunca procura `RR_MIN_TXT = "1,5"` como
// string literal do fonte Python (esse match falharia sempre).
//
// Caminhos resolvidos por `new URL(..., import.meta.url)`, nunca relativo ao
// cwd: `scripts/executar.sh` roda os runners com cwd=web e saída para
// /dev/null — um caminho relativo errado viraria um `[X]` mudo, sem
// diagnóstico (mesmo raciocínio que test_auditoria_prompts.py já aplica do
// lado Python para ler catalog.js).
//
// O caminho do skill_ref.py aceita override por B3_SKILL_REF_PATH — usado
// SÓ pela sabotagem controlada em sandbox exigida no aceite da Task 2 (roda
// contra uma CÓPIA alterada, nunca contra o arquivo real do servidor).
//
// Roda sem build: `node web/tests/test_rr_min_fonte_unica.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

import { RR_MIN, RR_MIN_TXT } from "../src/finance.js";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) finance.js é a fonte única do front --------------------------------
ok("RR_MIN === 1.5", RR_MIN === 1.5);
ok('RR_MIN_TXT === "1,5"', RR_MIN_TXT === "1,5");

// ---- 2) cruzamento front × backend, por VALOR (não por grafia) ------------
const caminhoSkillRef = process.env.B3_SKILL_REF_PATH
  ? process.env.B3_SKILL_REF_PATH
  : fileURLToPath(new URL("../../server/app/skill_ref.py", import.meta.url));

let numeroBackend = null;
let textoDerivado = null;
try {
  const srcSkillRef = readFileSync(caminhoSkillRef, "utf8");
  const m = srcSkillRef.match(/RR_MIN\s*=\s*([0-9.]+)/);
  if (!m) {
    console.log(`FALHOU RR_MIN não encontrado em ${caminhoSkillRef}`);
    fails++;
  } else {
    numeroBackend = parseFloat(m[1]);
    // mesma derivação de skill_ref.py: f"{RR_MIN:g}".replace(".", ",")
    textoDerivado = String(numeroBackend).replace(".", ",");
  }
} catch (e) {
  console.log(`FALHOU skill_ref.py ilegível em ${caminhoSkillRef} — o guardião cruzado front×backend não rodou (${e.message})`);
  fails++;
}

if (numeroBackend !== null) {
  ok(`número do front (${RR_MIN}) === número do backend (${numeroBackend})`, RR_MIN === numeroBackend);
  ok(`texto derivado do backend ("${textoDerivado}") === RR_MIN_TXT do front ("${RR_MIN_TXT}")`, textoDerivado === RR_MIN_TXT);
}

// ---- 3) copy.js — interpolação REAL em runtime (pega string aspeada morta) -
ok("COPY.operador.subtituloRadar contém RR_MIN_TXT + ':1' (runtime)",
  COPY.operador.subtituloRadar.includes(RR_MIN_TXT + ":1"));
ok("COPY.operador.comoAnalisaCorpo contém RR_MIN_TXT + ':1' (runtime)",
  COPY.operador.comoAnalisaCorpo.includes(RR_MIN_TXT + ":1"));

// ---- 4) fonte de copy.js e App.jsx não tem mais o literal "1,5:1" ----------
const srcCopy = readFileSync(join(here, "..", "src", "copy.js"), "utf8");
const srcApp = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
ok("copy.js: fonte não contém mais '1,5:1' literal", !srcCopy.includes("1,5:1"));
ok("App.jsx: fonte não contém mais '1,5:1' literal", !srcApp.includes("1,5:1"));
ok("copy.js: importa RR_MIN_TXT de finance.js", /import\s*\{[^}]*RR_MIN_TXT[^}]*\}\s*from\s*["']\.\/finance\.js["']/.test(srcCopy));
ok("App.jsx: importa RR_MIN_TXT de finance.js", /import\s*\{[^}]*RR_MIN_TXT[^}]*\}\s*from\s*["']\.\/finance\.js["']/.test(srcApp));

// ---- 5) ANTI-INTERPOLAÇÃO-MORTA EM JSX -------------------------------------
// App.jsx não é importável em Node (JSX cru); recorta o parágrafo do alvo
// dinâmico do FONTE e simula a "renderização" — a checagem POSITIVA de que o
// usuário vê o número do backend, não o nome da variável.
const abreP = srcApp.indexOf("Quando o preço bate o alvo");
const paragrafo = abreP > 0 ? srcApp.slice(Math.max(0, abreP - 20), srcApp.indexOf("</p>", abreP)) : "";
ok("trecho do alvo dinâmico encontrado em App.jsx", abreP > 0);
ok("trecho usa a expressão JSX {RR_MIN_TXT}:1", paragrafo.includes("{RR_MIN_TXT}:1"));
ok("trecho NÃO contém '${' (interpolação de string é inerte em JSX cru)", !paragrafo.includes("${"));
if (numeroBackend !== null) {
  const renderizado = paragrafo.replace("{RR_MIN_TXT}", textoDerivado);
  ok("renderização simulada produz 'R:R recalculado continuar ≥ 1,5:1'",
    renderizado.includes(`R:R recalculado continuar ≥ ${textoDerivado}:1`));
}

// ---- 6) hint: de carteiraStopAlvoOperador usa crase + ${RR_MIN_TXT}:1 ------
const abreHint = srcApp.indexOf("carteiraStopAlvoOperador");
const trechoHint = abreHint > 0 ? srcApp.slice(abreHint, srcApp.indexOf("},", abreHint)) : "";
ok("hint: de carteiraStopAlvoOperador usa crase com ${RR_MIN_TXT}:1", trechoHint.includes("${RR_MIN_TXT}:1"));

// ---- 7) catalog.js — segue literal (paridade byte-a-byte de prompt) -------
const srcCatalog = readFileSync(join(here, "..", "src", "catalog.js"), "utf8");
const ocorrencias = srcCatalog.match(/\d,\d:1/g) || [];
ok("catalog.js tem ocorrências de R:R (espelhos de prompt)", ocorrencias.length > 0);
if (numeroBackend !== null) {
  for (const oc of ocorrencias) {
    ok(`catalog.js: '${oc}' === RR_MIN_TXT + ':1' (fonte única)`, oc === RR_MIN_TXT + ":1");
  }
}

console.log(fails ? `\n${fails} falha(s)` : "\nRR_MIN — FONTE ÚNICA (front×backend) OK");
process.exit(fails ? 1 : 0);
