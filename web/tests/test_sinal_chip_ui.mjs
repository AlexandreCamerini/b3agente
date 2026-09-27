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

// ---------------------------------------------------------------------------
// Parte B — LinhaContexto e PlanoOperacionalBloco (Task 2, definição; a
// fiação no AtivoCard/Radar é do 42-04 — estes componentes ainda não têm
// call site real, só o contrato).
// ---------------------------------------------------------------------------

ok("function LinhaContexto( existe em App.jsx", /^function LinhaContexto\(/m.test(src));
ok("function PlanoOperacionalBloco( existe em App.jsx", /^function PlanoOperacionalBloco\(/m.test(src));

const linhaContexto = functionBody("LinhaContexto") || "";
const linhaContextoSemComentario = semComentarios(linhaContexto);
ok("corpo de LinhaContexto encontrado (não vazio)", linhaContexto.length > 200);
ok("corpo de LinhaContexto (sem comentários) não usa T.positive/T.negative/T.warn/T.accent (D-05/D-06/D-07)",
  !/T\.positive|T\.negative|T\.warn|T\.accent/.test(linhaContextoSemComentario));
{
  const idxRegime = linhaContexto.indexOf('label="REGIME"');
  const idxAlinhamento = linhaContexto.indexOf("cp.alinhamento[");
  const idxFundamentoSetor = linhaContexto.indexOf('setorId="fundamento"');
  const idxFundamentoNaoDirecao = linhaContexto.indexOf("cp.fundamentoNaoDirecao");
  ok("LinhaContexto: ordem de leitura REGIME < marca de alinhamento < setor fundamento < disclaimer de não-direção",
    idxRegime >= 0 && idxAlinhamento > idxRegime && idxFundamentoSetor > idxAlinhamento && idxFundamentoNaoDirecao > idxFundamentoSetor);
}
ok("LinhaContexto usa regimeRotulo(regime) (fonte única do rótulo, sinal.js)", linhaContexto.includes("regimeRotulo(regime)"));
ok("LinhaContexto declara a base degradada do regime (·SMA50, D-16)", linhaContexto.includes("regime.confiavel === false"));
ok("LinhaContexto renderiza os glifos ↗/↘ dentro de elemento aria-hidden (marca de alinhamento neutra)",
  /aria-hidden="true"[^>]*>[\s\S]{0,80}↗/.test(linhaContexto) && linhaContexto.includes("↘"));

const planoBloco = functionBody("PlanoOperacionalBloco") || "";
ok("corpo de PlanoOperacionalBloco encontrado (não vazio)", planoBloco.length > 200);
ok("PlanoOperacionalBloco usa sizingPlano( (mesmo motor de sizing do Radar)", planoBloco.includes("sizingPlano("));
ok("PlanoOperacionalBloco: gate literal `!operador && motivo &&` (motivo determinístico do Estudo)",
  planoBloco.includes("!operador && motivo &&"));
ok("PlanoOperacionalBloco declara \"PLANO DO SETUP (didático)\" (régua do Estudo)",
  planoBloco.includes("PLANO DO SETUP (didático)"));
{
  // O ramo Operador é o trecho entre o primeiro teste de `operador` (a caixa)
  // e o início do ramo Estudo (`!operador && motivo &&`) — não pode conter
  // <PlanRuler (D-12: a régua sai do Operador).
  const idxOperador = planoBloco.indexOf("temCaixa &&");
  const idxEstudo = planoBloco.indexOf("!operador && motivo &&");
  const ramoOperador = (idxOperador >= 0 && idxEstudo > idxOperador) ? planoBloco.slice(idxOperador, idxEstudo) : null;
  ok("ramo Operador de PlanoOperacionalBloco isolado para a asserção de ausência de régua", !!ramoOperador);
  ok("ramo Operador de PlanoOperacionalBloco NÃO contém <PlanRuler (D-12: régua sai do Operador)",
    ramoOperador != null && !ramoOperador.includes("<PlanRuler"));
}

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
