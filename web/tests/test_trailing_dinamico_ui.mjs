// F2 — Guardião do controle de TRAILING DINÂMICO na aba Operador IA.
//
// O backend passou a aceitar `trailingMode` (percentual | atr | estrutura) com
// os parâmetros de cada critério. Sem este controle, a feature existia só via
// PUT /api/agent — invisível para quem usa o app.
//
// O que este teste protege:
//  • os três critérios aparecem e chamam putAg({ trailingMode });
//  • cada critério tem SEU campo de parâmetro, e só o do critério ativo é
//    renderizado (três campos simultâneos ensinariam errado sobre o que
//    governa o stop);
//  • o bloco só aparece com o trailing LIGADO;
//  • o texto ENSINA o mecanismo e declara a monotonicidade e o fallback;
//  • o vocabulário continua descritivo — nenhum verbo de ordem de operação
//    (mesmo guardrail regulatório do backend).
// Roda sem build: `node web/tests/test_trailing_dinamico_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const pers = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- catálogo dos critérios -----------------------------------------------
ok("TRAILING_CRITERIOS declarado", src.includes("const TRAILING_CRITERIOS = ["));
for (const m of ["percentual", "atr", "estrutura"]) {
  ok(`critério "${m}" no catálogo`, new RegExp(`\\["${m}",`).test(src));
}
ok("cada critério traz rótulo E explicação (tripla)",
  (src.match(/\["(percentual|atr|estrutura)", "[^"]+", "[^"]+"\]/g) || []).length === 3);

// ---- seletor ---------------------------------------------------------------
ok("seletor emite putAg({ trailingMode })", src.includes("putAg({ trailingMode: m })"));
ok("default do seletor é percentual", src.includes('ag.trailingMode || "percentual"'));

// ---- campo por critério (um por vez) ---------------------------------------
ok("campo do percentual escreve trailingPct", src.includes("putAg({ trailingPct: +e.target.value })"));
ok("campo do ATR escreve trailingAtrMult", src.includes("putAg({ trailingAtrMult: +e.target.value })"));
ok("campo da estrutura escreve trailingLookback", src.includes("putAg({ trailingLookback: +e.target.value })"));
// Pareamento REAL: o campo tem que estar DENTRO do bloco condicional do seu
// critério. Só checar que ambos existem no arquivo deixaria passar um campo de
// ATR renderizado no modo estrutura.
for (const [modo, campo] of [["percentual", "trailingPct"], ["atr", "trailingAtrMult"], ["estrutura", "trailingLookback"]]) {
  const abre = src.indexOf(`=== "${modo}" && (`);
  const bloco = abre < 0 ? "" : src.slice(abre, src.indexOf(")}", abre));
  ok(`campo de ${campo} vive DENTRO do bloco do critério "${modo}"`,
    abre > 0 && bloco.includes(campo));
}

// Limites da UI espelham os do servidor (agent.agent_params / store.set_agent):
// um campo que aceita 99 e o servidor corta para 4 ensina errado.
ok("ATR limitado a 1–4 na UI", /min="1" max="4" step="0\.5"/.test(src));
ok("lookback limitado a 2–20 na UI", /min="2" max="20" step="1"/.test(src));
ok("percentual limitado a 1–20 na UI", /min="1" max="20" step="0\.5"/.test(src));

// ---- só com o trailing ligado ----------------------------------------------
ok("bloco condicionado a rules.trailing", src.includes("{!!rules.trailing && ("));

// ---- o app ensina o mecanismo ----------------------------------------------
ok("explica que o stop nunca desce", /o stop só sobe — nunca desce/.test(src));
ok("declara o fallback para o percentual", /usa o percentual e registra isso no Diário/.test(src));
ok("explica o ATR pelo que ele mede", /ATR\(14\), que mede a oscilação típica/.test(src));
ok("explica a estrutura pelo nível de invalidação", /invalidaria a tese de alta/.test(src));

// ---- as chaves chegam ao servidor ------------------------------------------
for (const k of ["trailingMode", "trailingAtrMult", "trailingLookback"]) {
  ok(`${k} está em SERVER_KEYS (senão o patch não sai do app)`, pers.includes(`"${k}"`));
}

// ---- guardrail de vocabulário ----------------------------------------------
// O bloco novo não pode introduzir ordem de operação. Verbos proibidos no
// recorte do texto que este teste adicionou.
const trecho = (src.match(/const TRAILING_CRITERIOS = \[[\s\S]*?\];/) || [""])[0];
const imperativos = /\b(compre|venda|entre agora|opere|invista|aproveite|garanta)\b/i;
ok("vocabulário descritivo (sem verbo de ordem)", !imperativos.test(trecho));

console.log(fails ? `\n${fails} falha(s)` : "\nTRAILING DINÂMICO (UI) OK");
process.exit(fails ? 1 : 0);
