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
// REVERSÃO DELIBERADA (2026-09-27, Fase 43, RITMO-01): o contrato (anel
// 36px; chip 4px 8px) é o mesmo, só passou a ser expresso pela escala
// nomeada SP/SP_OPTICO_ANEL — px solto no card é falha do test_ritmo_sp.mjs.
ok("corpo de SinalChip embute o ConfluenceRing em size={SP_OPTICO_ANEL} (D-08) (via SP)", sinalChip.includes("size={SP_OPTICO_ANEL}"));
ok("peso=\"primario\" usa role=\"group\" na manchete (uma leitura só)", sinalChip.includes('role="group"'));
ok("peso=\"contexto\" expõe role=\"img\" aria-label={ariaLabel} (D-15/CHIP-02)",
  /role="img" aria-label=\{ariaLabel\}/.test(sinalChip));
ok("corpo de SinalChip marca glifos decorativos com aria-hidden=\"true\"", sinalChip.includes('aria-hidden="true"'));
// REVERSÃO DELIBERADA (2026-09-27, Fase 43, RITMO-01): o contrato (anel
// 36px; chip 4px 8px) é o mesmo, só passou a ser expresso pela escala
// nomeada SP/SP_OPTICO_ANEL — px solto no card é falha do test_ritmo_sp.mjs.
ok("peso=\"contexto\" usa padding `${SP[1]}px ${SP[2]}px` (contrato do UI-SPEC) (via SP)", sinalChip.includes("padding: `${SP[1]}px ${SP[2]}px`"));
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

// ---------------------------------------------------------------------------
// Parte C — ordem e fiação no AtivoCard (42-04). HIER-02: a mesma sequência
// vale para watchlist e radar porque é UM render.
// ---------------------------------------------------------------------------

const ativoCard = functionBody("AtivoCard") || "";
{
  const idxPos = ativoCard.indexOf("{pos && (");
  const idxSinal = ativoCard.indexOf('<SinalChip peso="primario"');
  const idxTiming = ativoCard.indexOf("<TimingBadge");
  const idxPlano = ativoCard.indexOf("<PlanoOperacionalBloco");
  const idxContexto = ativoCard.indexOf("<LinhaContexto");
  const idxHistorico = ativoCard.indexOf("<HistoricoPill");
  const idxAnVencida = ativoCard.indexOf("{anVencida &&");
  ok("AtivoCard: ordem de leitura estritamente crescente (pos < manchete < timing < plano < contexto < elegibilidade < anVencida)",
    idxPos >= 0 && idxSinal > idxPos && idxTiming > idxSinal && idxPlano > idxTiming
    && idxContexto > idxPlano && idxHistorico > idxContexto && idxAnVencida > idxHistorico);
}
ok("AtivoCard usa alinhamentoDoMotor({ decisao: decM (D-01)", ativoCard.includes("alinhamentoDoMotor({ decisao: decM"));
ok("AtivoCard usa ladoDoMotor({ setup: s0Card, plano: sc.plano }) (D-09, lado nunca inferido do nome)",
  ativoCard.includes("ladoDoMotor({ setup: s0Card, plano: sc.plano })"));
ok("AtivoCard usa tierOf(sc.confluencia)[1] (rótulo do tier travado por teste)",
  ativoCard.includes("tierOf(sc.confluencia)[1]"));
ok("AtivoCard não contém kp. (D-02: chips da IA saíram do card)", !ativoCard.includes("kp."));
ok("AtivoCard não contém DIR_STYLE (herdado do chip de direção da IA, removido)", !ativoCard.includes("DIR_STYLE"));
ok("AtivoCard garante alvo de toque 44x44 no anel (acessibilidade)",
  ativoCard.includes("minWidth: 44") && ativoCard.includes("minHeight: 44"));

// ---------------------------------------------------------------------------
// Parte D — receita única e tier único por card (42-05, CHIP-01/HIER-01).
// Fecha a migração: nenhuma receita de chip paralela sobrevive em App.jsx, e
// o tier de confluência aparece uma única vez por card.
// ---------------------------------------------------------------------------

const srcSemComentarios = semComentarios(src);

ok("nenhum `function FundamentoChip|RegimeChip|TierDot` sobrevive em App.jsx (CHIP-01)",
  !/function (FundamentoChip|RegimeChip|TierDot)\(/.test(src));
ok("nenhum `const chip =` sobrevive em App.jsx (receita interna do AtivoCard/Watchlist apagada)",
  !/const chip =/.test(src));
ok("nenhum `confiança {` sobrevive em App.jsx (pill solta do Radar apagada, HIER-01)",
  !srcSemComentarios.includes("confiança {"));

// <ConfluenceRing fora de comentários aparece exatamente 2 vezes: dentro do
// corpo de SinalChip (a manchete, D-08) e no carrossel de alertas da home
// (App.jsx ≈2286, composição própria fora do AtivoCard — Out of Scope desta
// fase, registrado em 42-CONTEXT.md).
ok('`<ConfluenceRing` fora de comentários aparece exatamente 2 vezes em App.jsx (SinalChip + carrossel da home, fora de escopo)',
  (srcSemComentarios.match(/<ConfluenceRing/g) || []).length === 2);

// Nenhum `borderRadius: "999px"` (pill redonda legada) dentro do bloco do
// Radar — a cauda (per-setup, condições detectadas) usa a mesma forma legada
// em OUTRO contexto (badges de condição, não chip de sinal); a asserção aqui
// é específica ao contrato de SinalChip/receita antiga de pill de confiança,
// não uma varredura ampla do bloco inteiro.
ok('nenhum `borderRadius: "999px"` remanescente da pill de confiança apagada (âncora específica, HIER-01)',
  !src.includes('borderRadius: "999px", border: `1px solid ${T.borderSubtle}`, color: T.textMuted, fontSize: "10px", fontWeight: 800, letterSpacing: "0.04em" }}>confiança'));

// SinalChip peso="contexto" tem exatamente os 4 call sites reais esperados:
// LinhaContexto (regime + fundamento, 2×), HistoricoPill (1×), FundamentoTabela (1×).
// REVERSÃO DELIBERADA (2026-09-27, Fase 43, CHIP-03/D-01): +3 call sites em
// AnalysisView (direção/convicção/qualidade da IA, neutros, fora do card).
const callSitesContexto = (srcSemComentarios.match(/<SinalChip peso="contexto"/g) || []).length;
ok('`<SinalChip peso="contexto"` tem exatamente 7 call sites (LinhaContexto 2× + HistoricoPill 1× + FundamentoTabela 1× + AnalysisView 3×)',
  callSitesContexto === 7);
const iAnalysisViewParaD = src.indexOf("function AnalysisView(");
const iAnalysisViewEndParaD = src.indexOf("\nfunction hasAnalysis(", iAnalysisViewParaD);
const avParaD = iAnalysisViewParaD >= 0 && iAnalysisViewEndParaD > iAnalysisViewParaD ? src.slice(iAnalysisViewParaD, iAnalysisViewEndParaD) : "";
ok('AnalysisView usa `<SinalChip peso="contexto"` 3 vezes',
  (semComentarios(avParaD).match(/<SinalChip peso="contexto"/g) || []).length === 3);
const lcParaD = functionBody("LinhaContexto") || "";
ok('LinhaContexto usa `<SinalChip peso="contexto"` 2 vezes (regime + fundamento)',
  (lcParaD.match(/<SinalChip peso="contexto"/g) || []).length === 2);
const ftParaD = functionBody("FundamentoTabela") || "";
ok('FundamentoTabela usa `<SinalChip peso="contexto"` 1 vez (migrado de FundamentoChip, CHIP-01)',
  (ftParaD.match(/<SinalChip peso="contexto"/g) || []).length === 1);
const hpParaD = functionBody("HistoricoPill") || "";
ok('HistoricoPill usa `<SinalChip peso="contexto"` 1 vez (zero receita de pill paralela)',
  (hpParaD.match(/<SinalChip peso="contexto"/g) || []).length === 1);

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
