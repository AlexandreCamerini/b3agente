// FASE 4 (1.1) — Guardião do wiring de deps do objeto A (App.jsx).
//
// BUG que motivou este teste: `sellModal` era LIDO em A.confirmSell mas não
// estava no array de deps do useMemo — o A não era recriado ao abrir o modal
// de venda e confirmSell ficava com closure de `sellModal = null`: o botão
// "Confirmar venda" virava um no-op SILENCIOSO no aparelho (venda "não
// funciona"), enquanto a compra funcionava porque `buyModal` estava nas deps.
//
// Regra imposta aqui: todo estado (useState do componente raiz) cuja leitura
// aparece no corpo do useMemo(A) DEVE constar do array de dependências.
// Roda sem build: `node web/tests/test_wiring_deps.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// ---- 1) localizar o useMemo do A e o componente raiz que o contém ---------
const aStart = src.indexOf("const A = useMemo(() => ({");
ok("useMemo do A localizado", aStart > 0);

const before = src.slice(0, aStart);
const rootStart = Math.max(
  before.lastIndexOf("\nexport default function "),
  before.lastIndexOf("\nfunction "),
);
ok("componente raiz localizado", rootStart > 0);

// ---- 2) corpo do A + array de deps (por profundidade de parênteses) -------
let depth = 0, i = aStart, bodyEnd = -1;
for (; i < src.length; i++) {
  const c = src[i];
  if (c === "(") depth++;
  else if (c === ")") { depth--; if (depth === 0) { bodyEnd = i; break; } }
}
ok("fechamento do useMemo encontrado", bodyEnd > aStart);
const aBlock = src.slice(aStart, bodyEnd + 1);
const depsMatch = aBlock.match(/\}\)\s*,\s*\[([^\]]*)\]\s*\)$/s);
ok("array de deps extraído", !!depsMatch);
const deps = depsMatch ? depsMatch[1].split(",").map((s) => s.trim()).filter(Boolean) : [];

// corpo sem o array de deps, sem comentários e sem conteúdo de strings —
// evita falso positivo com nomes em textos de UI e em comentários.
let body = aBlock.slice(0, aBlock.lastIndexOf("}),"));
body = body
  .replace(/\/\/[^\n]*/g, "")
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .replace(/"(?:[^"\\\n]|\\.)*"/g, '""')
  .replace(/'(?:[^'\\\n]|\\.)*'/g, "''")
  .replace(/`(?:[^`\\]|\\.)*`/g, "``");

// ---- 3) estados do componente raiz ----------------------------------------
const rootScope = src.slice(rootStart, aStart);
const states = [...rootScope.matchAll(/const \[(\w+),\s*set\w+\]\s*=\s*useState/g)].map((m) => m[1]);
ok("estados do raiz extraídos (>= 20 esperados)", states.length >= 20, String(states.length));

// ---- 4) regra: estado LIDO no corpo ⇒ presente nas deps --------------------
// Leitura = identificador solto (não propriedade `.x`, não chave `x:`).
// Exceções conscientes ficam registradas aqui com o motivo.
const WHITELIST = new Set([
  // (vazio hoje — adicionar só com justificativa em comentário)
]);
const readButMissing = [];
for (const s of new Set(states)) {
  if (deps.includes(s) || WHITELIST.has(s)) continue;
  const reads = [...body.matchAll(new RegExp(String.raw`(?<![.\w$])${s}\b(?!\s*:)`, "g"))];
  if (reads.length) readButMissing.push(s);
}
ok(
  "todo estado lido no A está nas deps",
  readButMissing.length === 0,
  "faltando: " + readButMissing.join(", "),
);

// ---- 5) casos históricos nomeados (nunca regredir) -------------------------
ok("sellModal está nas deps (bug da venda silenciosa)", deps.includes("sellModal"));
ok("buyModal segue nas deps", deps.includes("buyModal"));

console.log(fails ? `\n${fails} FALHA(S) NO WIRING` : "\nWIRING DE DEPS DO A OK");
process.exit(fails ? 1 : 0);
