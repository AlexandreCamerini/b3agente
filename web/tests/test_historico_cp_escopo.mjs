// Guardião de escopo léxico — HistoricoScreen (App.jsx).
//
// Por que este guardião existe: `cp` NÃO é um binding de módulo em App.jsx.
// `const cp = copyFor(...)` só existe DENTRO de outras funções (não no topo
// do arquivo). HistoricoScreen recebe o vocabulário via `ctx.cp` (desestrutura
// só `{ data, A }` de `ctx` — nunca `cp` solto). Uma referência livre a `cp.`
// dentro deste componente é `ReferenceError: cp is not defined` em runtime,
// e só dispara no branch de estado vazio do histórico (achado de 2026-09-05:
// conta com >=1 ordem pendente e zero operações executadas → Portfólio →
// "Ver histórico de operações" → ErrorBoundary global "Algo saiu do lugar").
//
// Roda sem build: `node web/tests/test_historico_cp_escopo.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ------------------------------------------------------- localizar bloco ---
// Recorte: de `function HistoricoScreen(` até a próxima declaração de função
// de topo (`function AgenteScreen(`, a que vem logo em seguida no arquivo —
// confirmado por grep, não presumido).
const iHistorico = app.indexOf("function HistoricoScreen(");
const iAgenteScreen = app.indexOf("function AgenteScreen(");
ok("HistoricoScreen localizado antes de AgenteScreen", iHistorico >= 0 && iAgenteScreen > iHistorico);
const historicoRaw = iHistorico >= 0 && iAgenteScreen > iHistorico ? app.slice(iHistorico, iAgenteScreen) : "";
ok("slice de HistoricoScreen não está vazio", historicoRaw.length > 0);

// ------------------------------------------- higiene: remover comentários --
// Um comentário futuro citando `cp.algo` não pode derrubar este guardião nem
// mascarar uma referência livre real. Remove blocos /* */ e linhas // antes
// de rodar a regex de escopo.
const semBlocos = historicoRaw.replace(/\/\*[\s\S]*?\*\//g, "");
const historico = semBlocos.replace(/\/\/.*$/gm, "");

// -------------------------------------------- Teste 3: sanidade do recorte -
// Evita guardião vazio que sempre passa — prova que o recorte pegou o bloco
// certo (referência correta pré-existente, linha 4577 no momento da escrita).
ok("slice contém ctx.cp.ordemPendentePill (prova que o recorte é o bloco certo)",
   historico.includes("ctx.cp.ordemPendentePill"));

// -------------------------------------------- Teste 1: nenhuma cp. livre ---
// Toda ocorrência de `cp.` no slice deve ser precedida por `.` (forma
// `ctx.cp.`) ou fazer parte de um identificador maior (ex.: `wcp.`). Uma
// referência livre (`cp.` no início da expressão, ou precedida por espaço,
// parêntese, chave, vírgula etc.) é o bug.
const referenciaLivre = /(^|[^.\w])cp\s*\./.test(historico);
ok("nenhuma referência livre a `cp` no slice de HistoricoScreen (toda ocorrência é ctx.cp.)",
   !referenciaLivre);

// -------------------------------------------- Teste 2: fix correto no lugar
ok("slice contém literalmente ctx.cp.vazioHistorico",
   historico.includes("ctx.cp.vazioHistorico"));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
