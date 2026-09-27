// Fase 42 (CHIP-01/CHIP-02; D-08, D-14, D-15) — guardião do contrato do
// componente SinalChip (dois pesos fixos, sem prop de cor livre, aria
// obrigatório) e, no plano 02, dos blocos compostos LinhaContexto/
// PlanoOperacionalBloco. Lê App.jsx como TEXTO (sem build, sem DOM), mesmo
// padrão de test_radar_leitura_rapida.mjs. Caminhos resolvidos por
// `new URL(..., import.meta.url)`, nunca relativos ao cwd.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Corpo de função top-level (mesma convenção dos demais guardiões).
function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(m.index, i);
}

// Corpo sem linhas de comentário (// ...) — evita falso-positivo de token
// citado em prosa explicativa, mesma regra do repositório (ver 42-PATTERNS.md
// "Guardião de teste").
function semComentarios(body) {
  return (body || "").split("\n").filter((l) => !/^\s*\/\//.test(l.trim())).join("\n");
}

// ---------------------------------------------------------------------------
// Parte A — contrato do SinalChip (Task 1)
// ---------------------------------------------------------------------------

ok("function SinalChip( existe em App.jsx", /^function SinalChip\(/m.test(src));

const sinalChipDecl = /function SinalChip\(\{([^}]*)\}/.exec(src);
const paramList = sinalChipDecl ? sinalChipDecl[1] : "";
ok("corpo de SinalChip encontrado (lista de parâmetros não vazia)", paramList.length > 0);
ok("a lista de parâmetros de SinalChip não contém color/cor/col/background/bg (sem prop de cor livre, D-14)",
  !/\bcolor\b|\bcor\b|\bcol\b|\bbackground\b|\bbg\b/.test(paramList));

const sinalChip = functionBody("SinalChip") || "";
const sinalChipSemComentario = semComentarios(sinalChip);
ok("corpo de SinalChip encontrado (não vazio)", sinalChip.length > 200);
ok("corpo de SinalChip resolve a cor da manchete via REC_STYLE[decision] (guardrail: manchete só do motor)",
  sinalChip.includes("REC_STYLE[decision]"));
ok("corpo de SinalChip lê o estado de elegibilidade via HISTORICO_PILL_STYLE[estado]",
  sinalChip.includes("HISTORICO_PILL_STYLE[estado]"));
ok("corpo de SinalChip (sem comentários) não usa T.positive/T.negative/T.accent — cor só via REC_STYLE/HISTORICO_PILL_STYLE",
  !/T\.positive|T\.negative|T\.accent/.test(sinalChipSemComentario));
ok("corpo de SinalChip embute o ConfluenceRing em size={36} (D-08)", sinalChip.includes("size={36}"));
ok("peso=\"primario\" usa role=\"group\" na manchete (uma leitura só)", sinalChip.includes('role="group"'));
ok("peso=\"contexto\" expõe role=\"img\" aria-label={ariaLabel} (D-15/CHIP-02)",
  /role="img" aria-label=\{ariaLabel\}/.test(sinalChip));
ok("corpo de SinalChip marca glifos decorativos com aria-hidden=\"true\"", sinalChip.includes('aria-hidden="true"'));
ok("peso=\"contexto\" usa padding \"4px 8px\" (contrato do UI-SPEC)", sinalChip.includes('padding: "4px 8px"'));
ok("peso=\"contexto\" usa borderRadius \"7px\" (contrato do UI-SPEC)", sinalChip.includes('borderRadius: "7px"'));

ok("ConfluenceRing aceita prop ariaLabel", /function ConfluenceRing\(\{[^}]*ariaLabel[^}]*\}/.test(src));

// HistoricoPill migrado: nenhuma receita paralela de pill, sempre via SinalChip.
ok("HistoricoPill renderiza <SinalChip peso=\"contexto\" estado={estado}> (CHIP-01, zero pill paralelo)",
  src.includes('<SinalChip peso="contexto" estado={estado}'));

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
