// Fase 13 (13-03, CAP-06) — guardião estático dos 5 estados de `QuotaSeg` e
// do tratamento tipográfico/de cor travado pelo 13-UI-SPEC.md.
//
// O que este guardião PREVINE: alguém "simplificar" o helper mostrando
// "ilimitado"/"X/∞" para conta pro (reabre D-03, critério de sucesso 5 — sem
// número fabricado), ou trocar `T.warn` por `T.negative`/`T.positive`
// (reabre o guardrail de cor: verde/vermelho são reservados a P&L neste app,
// uma contagem de uso não pode parecer resultado financeiro). Também trava
// que `CatalogModal` (seleção local em edição) e o subtítulo da Watchlist
// (estado salvo) continuem lendo de DUAS fontes de numerador diferentes por
// desenho — unificá-las faria a contagem do modal divergir visualmente da
// seleção em progresso do usuário antes de salvar.
//
// Padrão "static source inspection" da casa (mesmo de
// test_fase5_gate_mensal_front.mjs / test_device_budget_sync.mjs):
// readFileSync + regex/bracket-matching sobre o fonte — App.jsx não é
// importável fora do build Vite. Roda sem build:
// `node web/tests/test_fase13_contadores_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(join(here, "..", p), "utf8");
const src = read("src/App.jsx");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Mesmo helper de bracket-matching de test_device_budget_sync.mjs — extrai o
// corpo de uma função a partir de uma âncora textual, até a chave de
// fechamento correspondente (profundidade balanceada).
function bodyOf(source, anchor) {
  const at = source.indexOf(anchor);
  if (at < 0) return null;
  const open = source.indexOf("{", at + anchor.length);
  let depth = 0;
  for (let i = open; i < source.length; i++) {
    if (source[i] === "{") depth++;
    else if (source[i] === "}") { depth--; if (depth === 0) return source.slice(open, i + 1); }
  }
  return null;
}

// --- (1) exatamente 1 definição, exatamente 3 usos --------------------------
const defsQuotaSeg = (src.match(/function QuotaSeg\(/g) || []).length;
ok(`function QuotaSeg tem exatamente 1 definição (achado ${defsQuotaSeg})`, defsQuotaSeg === 1);

const usosQuotaSeg = (src.match(/<QuotaSeg/g) || []).length;
ok(`<QuotaSeg é usado exatamente 3 vezes (achado ${usosQuotaSeg})`, usosQuotaSeg === 3);

// Âncora até o parêntese de fechamento dos parâmetros (sem incluir a chave
// de abertura do corpo) — QuotaSeg desestrutura `{ quota, count, ... }` no
// próprio parâmetro, e essa chave NÃO pode ser confundida com a chave de
// abertura do corpo da função (bodyOf busca a PRÓXIMA "{" após a âncora).
const body = bodyOf(src, "function QuotaSeg({ quota, count, prefix, suffix }) ");
ok("corpo de QuotaSeg localizado (bracket-matching)", !!body);

// --- (2) tipografia: MONO + peso 700 nos dígitos -----------------------------
ok("corpo de QuotaSeg contém `fontFamily: MONO`", !!body && body.includes("fontFamily: MONO"));
ok("corpo de QuotaSeg contém `fontWeight: 700`", !!body && body.includes("fontWeight: 700"));

// --- (3) cor: T.warn presente, T.negative/T.positive AUSENTES ---------------
ok("corpo de QuotaSeg contém `T.warn`", !!body && body.includes("T.warn"));
ok("corpo de QuotaSeg NÃO contém `T.negative` (reservado a P&L)", !!body && !body.includes("T.negative"));
ok("corpo de QuotaSeg NÃO contém `T.positive` (reservado a P&L)", !!body && !body.includes("T.positive"));

// --- (4) estado indisponível ("—") presente; "ilimitado" AUSENTE (D-03) -----
ok('corpo de QuotaSeg contém o travessão "—" (estado indisponível)', !!body && body.includes("—"));
ok('corpo de QuotaSeg NÃO contém a palavra "ilimitado" (D-03: plano sem teto omite o segmento)', !!body && !/ilimitado/i.test(body));

// --- (5) limiar "quase no limite" travado em 0.9 (piso do 13-UI-SPEC) -------
ok("corpo de QuotaSeg contém o limiar `0.9`", !!body && body.includes("0.9"));

// --- (6) as duas fontes de numerador NÃO foram unificadas -------------------
// CatalogModal (seleção local, em edição) usa `catalogSel.length`.
ok(
  "chamada em CatalogModal usa `count={catalogSel.length}` (seleção local, não salva)",
  /<QuotaSeg quota=\{wlQuota\} count=\{catalogSel\.length\}/.test(src)
);
// Subtítulo da Watchlist (estado salvo) usa `data.watchlist`.
ok(
  "chamada do subtítulo usa `count={(data.watchlist || []).length}` (estado salvo)",
  /<QuotaSeg quota=\{wlQuota\} count=\{\(data\.watchlist \|\| \[\]\)\.length\}/.test(src)
);

// --- (7) nenhum literal de limite (10/30) hardcoded nesta fase --------------
// Mesmo cuidado de test_fase5_gate_mensal_front.mjs: filtra linhas de
// comentário antes de checar (comentário de fim de linha continua contado —
// código real não deveria ter o hardcode de qualquer forma).
const linhasSemComentario = src.split("\n").filter((l) => !/^\s*\/\//.test(l));
const semComentario = linhasSemComentario.join("\n");
ok(
  'nenhum literal `/10` fixo como texto na tela (limite continua vindo de wlQuota.limit/aiq.monthLimit)',
  !/["'`][^"'`]*\/10[^"'`]*["'`]/.test(semComentario)
);
ok(
  'nenhum literal `/30` fixo como texto na tela (limite continua vindo de wlQuota.limit/aiq.monthLimit)',
  !/["'`][^"'`]*\/30[^"'`]*["'`]/.test(semComentario)
);

// --- (8) AtividadeIAScreen: dois try/catch independentes dentro de `carregar`
// A falha de `aiActivity` não pode apagar `aiq`, e vice-versa (Task 2).
// Mesmo cuidado: âncora até a seta, sem incluir a chave de abertura do
// corpo (senão bodyOf pularia a chave real e capturaria só um bloco interno).
const carregarBody = bodyOf(src, "const carregar = useCallback(async () => ");
ok("corpo de `carregar` (AtividadeIAScreen) localizado", !!carregarBody);
const tryCount = carregarBody ? (carregarBody.match(/\btry\s*\{/g) || []).length : 0;
ok(`\`carregar\` tem 2 blocos try/catch independentes (aiActivity + aiQuota, achado ${tryCount})`, tryCount === 2);
ok(
  "`carregar` busca `store.aiActivity()` e `store.aiQuota()` em try/catch separados",
  !!carregarBody && carregarBody.includes("store.aiActivity()") && carregarBody.includes("store.aiQuota()")
);

console.log(fails ? `\n${fails} FALHA(S)` : "\nTODOS OS TESTES PASSARAM");
process.exit(fails === 0 ? 0 : 1);
