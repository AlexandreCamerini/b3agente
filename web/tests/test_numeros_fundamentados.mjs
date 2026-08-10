// Reporte do Alex (09/08/2026): "um acumulado de 9990%. Como pode." — número
// exibido sem base de cálculo real. Causa: a base do retorno era
// `config.initialBudget`, um CAMPO EDITÁVEL. Digitar outro valor reescrevia o
// retorno acumulado de meses sem nenhuma operação ter acontecido.
// Segunda causa: "Recomeçar do zero" não zerava `equitySnapshots`, então a
// curva misturava duas simulações com bases diferentes.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
const here = dirname(fileURLToPath(import.meta.url));
const fin = readFileSync(join(here, "..", "src", "finance.js"), "utf8");
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
let fails = 0;
const ok = (n, c) => { console.log((c ? "ok " : "FALHOU ") + n); if (!c) fails++; };

ok("a base do retorno vem do carimbo da série, não do campo de orçamento",
  /snaps\.find\(\(s\) => typeof s\.base === "number" && s\.base > 0\)/.test(fin));
ok("o orçamento corrente só entra quando ainda não há série carimbada",
  /const b = carimbada \? carimbada\.base : \(Number\(budget\) \|\| 0\)/.test(fin));

// --- comportamento, não só forma: roda o cálculo de verdade -----------------
const { equityCurve } = await import(join(here, "..", "src", "finance.js"));
const serie = [
  { data: "2026-08-01", patrimonio: 10500, base: 10000 },
  { data: "2026-08-02", patrimonio: 10800, base: 10000 },
];
const comOrcamentoAdulterado = equityCurve(serie, 380, 10800, "2026-08-02");
ok("editar o orçamento não infla o retorno acumulado",
  Math.round(comOrcamentoAdulterado.retAcum) === 8);
ok("a base usada é a carimbada", comOrcamentoAdulterado.base === 10000);

const semSerie = equityCurve([], 10000, 12000, "2026-08-02");
ok("sem série, o orçamento ainda serve de base (1ª abertura)",
  Math.round(semSerie.retAcum) === 20);

// --- login obrigatório -------------------------------------------------------
// o texto sobrevive no COMENTÁRIO que registra a remoção — o que não pode
// existir é o botão que chamava onSkip.
ok("não há mais botão de entrada sem conta",
  !/onSkip && onSkip\(\)/.test(app) && !/onSkip=\{/.test(app));
ok("quem entra logando passa pelo onboarding (orçamento/perfil)",
  /if \(!\(data\.config && data\.config\.onboarded\)\) setWelcomeOpen\(true\);/.test(app));

// --- markdown na segunda superfície de IA ------------------------------------
ok("AssistenteBox renderiza markdown (mesma resposta do chat)",
  /<Markdown text=\{r\.texto\} \/>/.test(app));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
