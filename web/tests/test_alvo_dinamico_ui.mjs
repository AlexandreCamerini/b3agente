// F3 — Guardião do toggle de ALVO DINÂMICO na aba Operador IA.
//
// O backend passou a aceitar `alvoDinamico` (opt-in). Sem este controle, a
// feature existia só via PUT /api/agent — invisível para quem usa o app,
// mesma armadilha que a F2 já teve.
//
// O que este teste protege:
//  • o toggle chama putAg({ alvoDinamico });
//  • o bloco só aparece com a regra de alvo LIGADA (rules.alvo !== false);
//  • o texto ENSINA o mecanismo (ATR, limite de 2, R:R do Princípio 5);
//  • a chave chega ao servidor (SERVER_KEYS do persistence.js);
//  • vocabulário descritivo — nenhum verbo de ordem de operação.
// Roda sem build: `node web/tests/test_alvo_dinamico_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const pers = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- toggle ------------------------------------------------------------
ok("toggle emite putAg({ alvoDinamico })", src.includes("putAg({ alvoDinamico: !ag.alvoDinamico })"));

// ---- só com a regra de alvo ligada --------------------------------------
const abre = src.indexOf("Alvo dinâmico <span");
ok("bloco existe no arquivo", abre > 0);
const antes = abre > 0 ? src.slice(Math.max(0, abre - 400), abre) : "";
ok("bloco condicionado a rules.alvo !== false", antes.includes('rules.alvo !== false && ('));

// ---- o app ensina o mecanismo --------------------------------------------
ok("explica o critério por ATR", /1,5× o ATR\(14\)/.test(src));
ok("declara o limite de extensões", /no máximo 2 vezes por posição/.test(src));
// ADR-015 (06-05): o "1,5:1" literal virou a expressão JSX {RR_MIN_TXT}:1 —
// fonte única em web/src/finance.js, amarrada a server/app/skill_ref.py por
// test_rr_min_fonte_unica.mjs. Atualização, não afrouxamento: o texto
// renderizado continua "R:R recalculado continuar ≥ 1,5:1" (Princípio 5).
ok("cita o piso de R:R do Princípio 5 (fonte única RR_MIN_TXT)", /R:R recalculado continuar ≥ \{RR_MIN_TXT\}:1/.test(src));

// ---- a chave chega ao servidor -------------------------------------------
ok('"alvoDinamico" está em SERVER_KEYS (senão o patch não sai do app)', pers.includes('"alvoDinamico"'));

// ---- guardrail de vocabulário ---------------------------------------------
const bloco = abre > 0 ? src.slice(abre, src.indexOf(")}", abre + 800)) : "";
const imperativos = /\b(compre|venda|entre agora|opere|invista|aproveite|garanta)\b/i;
ok("vocabulário descritivo (sem verbo de ordem)", !imperativos.test(bloco));

console.log(fails ? `\n${fails} falha(s)` : "\nALVO DINÂMICO (UI) OK");
process.exit(fails ? 1 : 0);
