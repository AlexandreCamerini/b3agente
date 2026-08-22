// FIX-C04 (REPORT-01) — guardião do aviso pedagógico de prontidão
// Estudo→Operador.
//
// Contrato: o único gate hoje é o LEGAL (`!c.operadorTermo` →
// TermoOperadorModal). Este achado adiciona uma camada pedagógica SOFT por
// cima, nunca no lugar dela — "aviso, não bloqueio duro" (CONTEXT.md). Este
// guardião trava:
//  1. o painel é T.warn (nunca T.accent/T.negative no fundo/borda da caixa);
//  2. a copy é a do UI-SPEC, palavra por palavra;
//  3. existe o caminho "Ativar mesmo assim" — sem ele o achado seria
//     REINTRODUZIDO ao contrário (nudge virando bloqueio disfarçado);
//  4. o gate legal (`operadorTermo`/`TermoOperadorModal`) segue presente;
//  5. o sinal falha aberto: `typeof analyses === "object"` é checado ANTES
//     de concluir "zero análises" — ausência de dado nunca é lida como
//     "nunca analisou".
// Roda sem build: `node web/tests/test_prontidao_operador.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const startIdx = app.indexOf("function ModoTrabalhoCard(");
const endIdx = app.indexOf("function TermoOperadorModal(");
ok("ModoTrabalhoCard localizado e vem antes de TermoOperadorModal", startIdx >= 0 && endIdx > startIdx);
const card = startIdx >= 0 && endIdx > startIdx ? app.slice(startIdx, endIdx) : "";

// ---------------------------------------------------------------- 1. cor --
ok("o painel do nudge usa T.warn no background/border",
   /background: "color-mix\(in srgb, " \+ T\.warn \+ " 12%, transparent\)", border: `1px solid \$\{T\.warn\}`/.test(card));
// A caixa do nudge (background/border) não pode usar T.accent nem
// T.negative — só o BOTÃO recomendado usa accent (é o CTA, não a caixa).
const caixaNudge = (() => {
  const i = card.indexOf('{nudgeOperador && (');
  const j = card.indexOf(")}\n", i);
  return i >= 0 ? card.slice(i, j > i ? j : i + 900) : "";
})();
ok("caixaNudge isolada (guardião não fica vácuo)", caixaNudge.length > 0);
const primeiraDiv = caixaNudge.slice(0, caixaNudge.indexOf("</div>"));
ok("a caixa do nudge (1ª div) não usa T.accent nem T.negative no fundo/borda",
   !/style=\{\{[^}]*T\.accent[^}]*\}\}/.test(primeiraDiv) && !/style=\{\{[^}]*T\.negative[^}]*\}\}/.test(primeiraDiv));

// ------------------------------------------------------------- 2. copy ----
ok("título verbatim: \"Você ainda não abriu nenhuma análise no Estudo.\"",
   card.includes("Você ainda não abriu nenhuma análise no Estudo."));
ok("corpo verbatim (voz de professor do Estudo)",
   card.includes("O Modo Operador libera decisões diretas — mas ele parte do que você já entende. Vale a pena estudar pelo menos um ativo antes de ativar."));

// --------------------------------------------------------- 3. dois botões -
ok("botão recomendado: \"Fazer uma análise no Estudo primeiro\"",
   card.includes("Fazer uma análise no Estudo primeiro"));
ok("botão de dispensa: \"Ativar mesmo assim\" (o caminho que impede virar bloqueio)",
   card.includes("Ativar mesmo assim"));
ok("o botão recomendado navega para o Estudo (ctx.goMercado, mesma ação do portfólio vazio)",
   /onClick=\{\(\) => \{ setNudgeOperador\(false\); goMercado\(\); \}\}/.test(card));
ok("\"Ativar mesmo assim\" dispensa o nudge e chama escolher(\"operador\") de novo — passa direto pro gate legal",
   /onClick=\{\(\) => \{ nudgeDispensadoRef\.current = true; setNudgeOperador\(false\); escolher\("operador"\); \}\}/.test(card));

// ------------------------------------------------ 4. gate legal intacto ---
ok("o gate legal (!c.operadorTermo) continua em escolher()", /!c\.operadorTermo/.test(card));
ok("TermoOperadorModal continua sendo renderizado por ModoTrabalhoCard",
   /\{termoOpen && <TermoOperadorModal /.test(card));
const totalOperadorTermo = (app.match(/operadorTermo/g) || []).length;
ok(`grep -c "operadorTermo" no arquivo inteiro não diminuiu (>= 5, era 5 antes deste plano)`, totalOperadorTermo >= 5);

// ------------------------------------------------------- 5. fail-open -----
ok("prontidaoConhecida exige typeof === \"object\" (não conclui zero de undefined/null)",
   /const prontidaoConhecida = analises && typeof analises === "object";/.test(card));
ok("nuncaAnalisou só é calculado A PARTIR de prontidaoConhecida — fail-open",
   /const nuncaAnalisou = prontidaoConhecida && Object\.keys\(analises\)\.length === 0;/.test(card));

// -------------------------------------------------- não persistido --------
ok("nudgeDispensado(Ref) não aparece em nenhuma chamada de saveConfig/putConfig (não é persistido)",
   !/saveConfig\(\{[^}]*nudgeDispensado/.test(app) && !/putConfig\(\{[^}]*nudgeDispensado/.test(app));

// -------------------------------------------------- não é modal -----------
ok("o painel renderiza inline entre o segmented control e a descrição, não como modal (sem position:fixed)",
   card.slice(card.indexOf("{nudgeOperador && ("), card.indexOf("{nudgeOperador && (") + 400).indexOf("position: \"fixed\"") === -1);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
