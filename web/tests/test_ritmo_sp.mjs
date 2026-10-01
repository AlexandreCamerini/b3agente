// Fase 43 (RITMO-01, D-14/D-15/D-16/D-18) — ban-list de px solto de
// espaçamento no card; escala do qa/AUDITORIA-Design-System-v1.md §3.2;
// exceção só na lista fechada SP_OPTICO_*. Lê App.jsx como TEXTO (sem build,
// sem DOM), mesmo padrão de test_sinal_chip_ui.mjs (Infraestrutura
// functionBody/semComentarios copiada literalmente daquele arquivo).
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
// citado em prosa explicativa, mesma regra do repositório.
function semComentarios(body) {
  return (body || "").split("\n").filter((l) => !/^\s*\/\//.test(l.trim())).join("\n");
}

// Remove também comentário JSX ({/* ... */}), que pode conter px solto em
// prosa explicativa (ex.: "espaçador de 24px" no texto, não no código).
function semComentariosJsx(body) {
  return (body || "").replace(/\{\/\*[\s\S]*?\*\/\}/g, "");
}

function limpo(body) {
  return semComentarios(semComentariosJsx(body));
}

// ---------------------------------------------------------------------------
// Detector: varre margin/padding/gap (+ variantes Top/Bottom/Left/Right e
// rowGap/columnGap) e reprova qualquer valor que não seja SP[N], SP_OPTICO_*,
// 0 (literal ou string) ou template literal composto só por pedaços
// `-?${SP...}px`, `0` e espaço.
// ---------------------------------------------------------------------------

function valorAceito(v) {
  const val = v.trim();
  if (/^SP\[\d\]$/.test(val)) return true;
  if (/^SP_OPTICO_[A-Z_]+(\.[vh])?$/.test(val)) return true;
  if (val === "0") return true;
  if (/^["']0["']$/.test(val)) return true;
  if (/^`[^`]*`$/.test(val)) {
    const inner = val.slice(1, -1);
    const pieceRe = /-?\$\{SP(?:_OPTICO_[A-Z_]+)?(?:\[\d\]|\.[vh])?\}px|0|\s+/g;
    const resto = inner.replace(pieceRe, "");
    return resto === "";
  }
  return false;
}

function violacoes(trecho) {
  const achadas = [];
  const re = /\b(margin|padding|gap|rowGap|columnGap)(Top|Bottom|Left|Right)?\s*:\s*(`[^`]*`|"[^"]*"|'[^']*'|[^,}\n]+)/g;
  let m;
  while ((m = re.exec(trecho))) {
    const prop = m[1] + (m[2] || "");
    const valor = m[3].trim();
    if (!valorAceito(valor)) achadas.push({ prop, valor });
  }
  return achadas;
}

// ---------------------------------------------------------------------------
// Parte A — autoteste do detector (roda ANTES da migração — prova que o
// detector funciona já no RED).
// ---------------------------------------------------------------------------

{
  const rejeitados = [
    'marginTop: "11px"',
    'padding: "9px 11px"',
    'padding: `12px 0`',
    "gap: 6",
    'marginTop: x ? "4px" : "8px"',
  ];
  for (const snippet of rejeitados) {
    ok(`autoteste do detector FLAGRA \`${snippet}\``, violacoes(snippet).length > 0);
  }

  const aceitos = [
    "marginTop: SP[3]",
    "padding: 0",
    'padding: "0"',
    'padding: `${SP[1]}px 0`',
    'margin: `-${SP[3]}px -${SP[2]}px`',
    'padding: `${SP_OPTICO_CHIP_PRIMARIO.v}px ${SP_OPTICO_CHIP_PRIMARIO.h}px`',
  ];
  for (const snippet of aceitos) {
    ok(`autoteste do detector ACEITA \`${snippet}\``, violacoes(snippet).length === 0);
  }
}

// ---------------------------------------------------------------------------
// Parte B — const SP e exceções ópticas (lista fechada, D-16).
// ---------------------------------------------------------------------------

ok("App.jsx contém exatamente `const SP = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32 };`",
  src.includes("const SP = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32 };"));

{
  const declaradas = [...src.matchAll(/^const (SP_OPTICO_[A-Z_]+)\s*=/gm)].map((m) => m[1]);
  const esperadas = ["SP_OPTICO_CHIP_PRIMARIO", "SP_OPTICO_ANEL"];
  ok("as declarações `const SP_OPTICO_*` em App.jsx são exatamente {SP_OPTICO_CHIP_PRIMARIO, SP_OPTICO_ANEL} (lista fechada, D-16)",
    declaradas.length === esperadas.length && esperadas.every((n) => declaradas.includes(n)));
}

// ---------------------------------------------------------------------------
// Parte C — zero violação nos 5 escopos do card (D-14).
// ---------------------------------------------------------------------------

const sinalChip = functionBody("SinalChip") || "";
const linhaContexto = functionBody("LinhaContexto") || "";
const planoBloco = functionBody("PlanoOperacionalBloco") || "";
const historicoPill = functionBody("HistoricoPill") || "";
// Fase 45 (UI-SPEC §Copywriting — guardiões): extensão, não reversão.
const cardEstr = functionBody("CardPosicaoEstruturada") || "";
const reguaFaixa = functionBody("ReguaFaixa") || "";
ok("recortes CardPosicaoEstruturada/ReguaFaixa não são vazios", cardEstr.length > 500 && reguaFaixa.length > 500);

const idxManchete = src.indexOf("{/* qa/49 (v11): MANCHETE ÚNICA");
const idxAnVencida = src.indexOf("{anVencida && (");
ok("âncora de início do recorte do AtivoCard (MANCHETE ÚNICA) existe", idxManchete >= 0);
ok("âncora de fim do recorte do AtivoCard (anVencida) existe", idxAnVencida > idxManchete);
const recorteAtivoCard = (idxManchete >= 0 && idxAnVencida > idxManchete)
  ? src.slice(idxManchete, idxAnVencida) : "";
ok("recorte do AtivoCard não é vazio (recorte vazio é falha, nunca pass silencioso)", recorteAtivoCard.length > 500);

// Fase 46 (46-08, 2026-10-01, D-14/D-17): componentes do card v6 entram na
// varredura (extensão, nada removido). Exceções nomeadas da UI-SPEC já cabem
// no detector (padding "0" / `0 ${SP[1]}px`); px solto continua reprovado.
const componentesV6 = ["ReguaPlano", "FaixaVencimento", "LinhaEstadoV6", "CartaoPosicao", "SeletorFace",
  "AreaFlip", "FaceAcao", "BlocoBorisIA", "SimuladorEstudo", "TermosTocaveis", "PayoffOperador", "GradeConta"]
  .map((n) => [n, functionBody(n) || ""]);
for (const [n, corpo] of componentesV6) ok(`recorte ${n} (card v6) não é vazio`, corpo.length > 200);

for (const [nome, corpo] of [
  ...componentesV6,
  ["SinalChip", sinalChip],
  ["LinhaContexto", linhaContexto],
  ["PlanoOperacionalBloco", planoBloco],
  ["HistoricoPill", historicoPill],
  ["CardPosicaoEstruturada", cardEstr],
  ["ReguaFaixa", reguaFaixa],
  ["AtivoCard (recorte manchete→elegibilidade)", recorteAtivoCard],
]) {
  // Fase 46 (46-08, 2026-10-01): exceções NOMEADAS da UI-SPEC, por componente
  // (lista fechada; qualquer outro px solto segue reprovado).
  const excecoesV6 = {
    TermosTocaveis: [{ prop: "padding", valor: '"0 2px"' }], // termo inline (UI-SPEC exceção c)
    GradeConta: [{ prop: "gap", valor: '"1px"' }],           // separador 1px T.borderSubtle (S5)
  }[nome] || [];
  const achadas = violacoes(limpo(corpo)).filter((a) => !excecoesV6.some((x) => x.prop === a.prop && x.valor === a.valor));
  if (achadas.length > 0) {
    for (const a of achadas) console.log(`  violação em ${nome}: ${a.prop}: ${a.valor}`);
  }
  ok(`zero violação de margin/padding/gap em ${nome}`, achadas.length === 0);
}

// ---------------------------------------------------------------------------
// Parte D — pontos específicos citados no <behavior> do plano.
// ---------------------------------------------------------------------------

ok('corpo de SinalChip usa `size={SP_OPTICO_ANEL}`', sinalChip.includes("size={SP_OPTICO_ANEL}"));

const timingBadge = functionBody("TimingBadge") || "";
ok('corpo de TimingBadge usa `marginTop: SP[2]` (o marginTop que separa o TimingBadge do bloco anterior — "espaço ENTRE blocos")',
  timingBadge.includes("marginTop: SP[2]"));

{
  const idxFundamento = linhaContexto.indexOf('setorId="fundamento"');
  ok('LinhaContexto declara setorId="fundamento"', idxFundamento >= 0);
  const trechoFundamento = idxFundamento >= 0 ? linhaContexto.slice(idxFundamento, idxFundamento + 400) : "";
  ok("D-18: o SetorAlvo setorId=\"fundamento\" tem padding `${SP[3]}px ${SP[2]}px`",
    trechoFundamento.includes("padding: `${SP[3]}px ${SP[2]}px`"));
  ok("D-18: o SetorAlvo setorId=\"fundamento\" tem margin `-${SP[3]}px -${SP[2]}px` (simétrico, sinal oposto)",
    trechoFundamento.includes("margin: `-${SP[3]}px -${SP[2]}px`"));
}

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
