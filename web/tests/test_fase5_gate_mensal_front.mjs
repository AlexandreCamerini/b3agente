// Fase 5 (v1.1) — guardião de FIX-C33 (metade FRONT) do REPORT-01.
//
// C-33 (Médio): o espelho front do gate de análises chamava `canAnalyze(0)`
// com o comentário "FUTURO: passar contagem do mês" — dado hardcoded, não a
// contagem real. Hoje irrelevante porque `PLAN_FREE.maxAnalysesPerMonth` é
// `null`, mas se o número comercial do ADR-010 for populado sem tocar esse
// call site, o gate quebraria silenciosamente (compara `0 >= limite` sempre).
//
// Este guardião fecha a CLASSE do erro, não a instância: qualquer
// `canAnalyze(0` (literal numérico) volta a quebrar este teste, mesmo que o
// autor não conheça o histórico de C-33. Também trava a paridade
// `analisesNoMes` nos dois stores (guardrail CLAUDE.md) e que nenhum limite
// comercial foi ligado por acidente enquanto o call site era corrigido.
//
// Padrão "static source inspection" da casa (mesmo de
// test_fase3_fonte_technicals.mjs / test_fase5_appmode_fonte_unica.mjs):
// readFileSync + regex sobre o fonte (App.jsx não é importável fora do
// build). Roda sem build: `node web/tests/test_fase5_gate_mensal_front.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(join(here, "..", p), "utf8");
const srcApp = read("src/App.jsx");
const srcPersistence = read("src/persistence.js");
const srcPlan = read("src/plan.js");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Filtra linhas de comentário ANTES de contar — mesmo cuidado de
// test_fase5_appmode_fonte_unica.mjs: só remove linhas cujo conteúdo, após
// trim, COMEÇA com `//` (comentário de fim de linha continua contado, porque
// código real nessa linha não deveria conter o hardcode de qualquer forma).
const linhasAppSemComentario = srcApp.split("\n").filter((l) => !/^\s*\/\//.test(l));
const appSemComentario = linhasAppSemComentario.join("\n");

// (a) o hardcode `canAnalyze(0` não existe mais no fonte, sem comentário —
// fecha a CLASSE do erro, não só a instância (`canAnalyze(0)` literal).
ok(
  "App.jsx (sem comentários) não contém `canAnalyze(0` (nenhum literal numérico hardcoded)",
  !/canAnalyze\(0/.test(appSemComentario)
);

// (b) em A.analyze, canAnalyze é chamado com um IDENTIFICADOR (variável),
// não com literal numérico — prova positiva de que a leitura real substituiu
// o hardcode, não só que o hardcode sumiu (uma remoção sem substituição
// também passaria no assert (a) e deixaria o gate quebrado).
ok(
  "canAnalyze é chamado com um identificador (não um literal numérico)",
  /const gate = canAnalyze\([A-Za-z_$][\w$]*\)/.test(srcApp)
);

// (c) o comentário "FUTURO: passar contagem do mês" deixou de ser verdade —
// não pode sobreviver como comentário morto contradizendo o código real.
ok(
  "comentário 'FUTURO: passar contagem do mês' não existe mais no fonte",
  !srcApp.includes("FUTURO: passar contagem do mês")
);

// (d) `analisesNoMes` está DEFINIDO nos dois stores de persistence.js —
// conta pela ASSINATURA de definição (arrow property do serverStore, método
// shorthand do deviceStore), não por qualquer ocorrência da palavra (que
// incluiria comentários e o call site em App.jsx nesse mesmo grep).
const defsAnalisesNoMes = (srcPersistence.match(/analisesNoMes\s*:\s*async\s*\(|async\s+analisesNoMes\s*\(/g) || []).length;
ok(
  `analisesNoMes tem exatamente 2 definições em persistence.js (uma por store, achado ${defsAnalisesNoMes})`,
  defsAnalisesNoMes === 2
);

// (e) plan.js continua sem limite comercial ligado nos dois planos — o
// teste falha se alguém ligar `maxAnalysesPerMonth` sem passar pelo ADR-010.
const maxAnalysesNullMatches = (srcPlan.match(/maxAnalysesPerMonth: null/g) || []).length;
ok(
  `plan.js continua com 'maxAnalysesPerMonth: null' nos dois planos (achado ${maxAnalysesNullMatches})`,
  maxAnalysesNullMatches === 2
);

// (f) canAddTicker continua recebendo o TAMANHO REAL da watchlist — essa
// metade de C-33 já estava correta antes da fase; guardião prova que
// continua assim (não regrediu para um hardcode também).
ok(
  "canAddTicker continua recebendo `(data.watchlist || []).length`",
  /canAddTicker\(\(data\.watchlist \|\| \[\]\)\.length\)/.test(srcApp)
);

console.log(fails ? `\n${fails} FALHA(S)` : "\nTODOS OS TESTES PASSARAM");
process.exit(fails === 0 ? 0 : 1);
