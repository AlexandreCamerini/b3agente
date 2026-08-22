// FIX-C01 (REPORT-01, lado front) — guardião do rótulo de fonte da
// explicação (IA × determinístico) e do fallback quando não há dados.
//
// Contrato:
//  (a) AiNote tem as duas variantes de texto (ia / deterministico);
//  (b) AnalysisView escolhe a variante por an.fonte;
//  (c) a frase "Não há dados suficientes para uma explicação agora."
//      (mandatória, CLAUDE.md) está presente verbatim;
//  (d) a linha "IA indisponível agora ..." está presente verbatim;
//  (e) o caminho determinístico usa <Markdown, não um contêiner de erro;
//  (f) persistence.js persiste `fonte` em doc.analyses.
// Roda sem build: `node web/tests/test_fonte_explicacao.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------- localizar blocos
const iAiNote = app.indexOf("const AiNote = ");
const iAiNoteEnd = app.indexOf(");", iAiNote);
const aiNote = iAiNote >= 0 && iAiNoteEnd > iAiNote ? app.slice(iAiNote, iAiNoteEnd) : "";
ok("AiNote localizado", aiNote.length > 0);

const iAnalysisView = app.indexOf("function AnalysisView(");
const iAnalysisViewEnd = app.indexOf("\nfunction hasAnalysis(", iAnalysisView);
const analysisView = iAnalysisView >= 0 && iAnalysisViewEnd > iAnalysisView ? app.slice(iAnalysisView, iAnalysisViewEnd) : "";
ok("AnalysisView localizado", analysisView.length > 0);

// --------------------------------------------------- (a) duas variantes --
ok("AiNote recebe prop source com default \"ia\"", /const AiNote = \(\{ at, source = "ia" \}\) =>/.test(aiNote));
ok("variante source=\"ia\" preserva o texto original byte a byte",
   aiNote.includes('"Conteúdo educacional de IA · não é recomendação" + (at ? " · " + at : "")'));
ok("variante source=\"deterministico\" com a copy exata do UI-SPEC",
   aiNote.includes('"Explicação automática do app (sem IA) · baseada no setup/indicador detectado" + (at ? " · " + at : "")'));

// grep global: string original não duplicou/alterou, nova aparece 1x
const totalIaText = (app.match(/Conteúdo educacional de IA · não é recomendação/g) || []).length;
ok("\"Conteúdo educacional de IA · não é recomendação\" aparece 1x no arquivo", totalIaText === 1);
const totalDetText = (app.match(/Explicação automática do app \(sem IA\)/g) || []).length;
ok("\"Explicação automática do app (sem IA)\" aparece 1x no arquivo", totalDetText === 1);

// ------------------------------------------ (b) AnalysisView escolhe por an.fonte
ok("AnalysisView deriva source de an.fonte === \"deterministico\"",
   /const source = an\.fonte === "deterministico" \? "deterministico" : "ia";/.test(analysisView));
ok("AnalysisView passa source à AiNote", /<AiNote at=\{an\.at\} source=\{source\} \/>/.test(analysisView));

// a 2ª chamada de AiNote (fora de AnalysisView) continua sem passar source —
// mantém o texto de IA por causa do default.
const segundaChamada = app.slice(iAnalysisViewEnd);
ok("a chamada de AiNote fora de AnalysisView não passa source (mantém default \"ia\")",
   /<AiNote \/>/.test(segundaChamada));

// ------------------------------------------------------- (c) sem dados ----
const FRASE_SEM_DADOS = "Não há dados suficientes para uma explicação agora.";
ok("frase mandatória \"Não há dados suficientes para uma explicação agora.\" presente verbatim",
   analysisView.includes(FRASE_SEM_DADOS));
ok("frase mandatória aparece 1x no arquivo inteiro",
   (app.match(/Não há dados suficientes para uma explicação agora\./g) || []).length === 1);
ok("semDados deriva de an.semDados OU corpo vazio no caminho determinístico (fail-safe, não hardcoded)",
   /const semDados = an\.semDados === true \|\| \(source === "deterministico" && !body\);/.test(analysisView));

// ------------------------------------------------- (d) IA indisponível ----
const FRASE_IA_INDISPONIVEL = "IA indisponível agora — mostrando a explicação automática do app, sem IA.";
ok("linha \"IA indisponível agora...\" presente verbatim, condicionada a an.iaIndisponivel",
   analysisView.includes(FRASE_IA_INDISPONIVEL) && /\{an\.iaIndisponivel && <div/.test(analysisView));
// não é T.negative/caixa de alerta — 11px T.textFaint
ok("a linha de IA indisponível usa T.textFaint (não T.negative, não caixa de alerta)",
   /\{an\.iaIndisponivel && <div style=\{\{ fontSize: "11px", color: T\.textFaint/.test(analysisView));

// -------------------------------------------- (e) mesmo caminho de render
ok("o caminho determinístico (body preenchido) usa <Markdown, não um contêiner de erro/degradado",
   /semDados\s*\n\s*\? <div[^>]*>Não há dados suficientes[\s\S]*?\n\s*: \(body \? <Markdown text=\{body\} \/>/.test(analysisView));
ok("o ramo if (an.error) continua existindo (erro real de rede/cliente)",
   /if \(an\.error\) return <div style=\{\{ color: T\.negative/.test(analysisView));

// --------------------------------------------- (f) persistence.js persiste fonte
ok("deviceStore.analyze grava fonte/iaIndisponivel/verbetes/semDados em doc.analyses[t]",
   /doc\.analyses\[t\] = \{[^}]*fonte: r\.fonte \|\| "ia", iaIndisponivel: r\.iaIndisponivel \|\| null, verbetes: r\.verbetes \|\| \[\], semDados: !!r\.semDados \}/.test(persistence));
// ramo reaproveitada preserva via spread do objeto guardado anteriormente
ok("o ramo reaproveitada preserva os campos via spread de `guardada`",
   /doc\.analyses\[t\] = \{ \.\.\.guardada, at: r\.at, snapshotId:/.test(persistence));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
