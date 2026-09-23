// Quick 260923-ndy (Task 2) — guardião de `ExecutarProposta.jsx` (bloco de
// execução da estrutura montada manualmente em Opções → Analisar) e da
// fiação que o liga em `SecaoAnalisar.jsx`/`OpcoesScreen.jsx`.
//
// Duas metades, mesmo padrão de `test_explicacao_payoff.mjs` (37-02):
//  (A) RENDER — via `react-dom/server` `renderToStaticMarkup` +
//      `_jsx_loader.mjs` (node puro não conhece `.jsx`), `React.createElement`
//      cru, sem JSX no próprio `.mjs`;
//  (B) ESTÁTICO — inspeção de fonte, mesmo padrão de `test_opcoes_analisar_ui.mjs`
//      (regex + asserção de sanidade em cada uma, para não passar por
//      vacuidade quando o padrão muda).
//
// O que este arquivo trava, em uma frase cada:
//  - sem `dados.execucao`, o bloco não renderiza nada (a UI já mostra
//    `motivo`/estados anteriores fora deste componente);
//  - Modo Estudo NUNCA mostra o botão de execução — só a leitura de que o
//    Estudo não executa (mesmo gate de CuradoriaEstruturas.jsx, T-14-23);
//  - `executavel: false` mostra o motivo do backend VERBATIM, sem botão;
//  - `ehRecusaLiquidezDificil` reconhece o prefixo exato que o servidor usa
//    (`server/app/main.py`), e só ele;
//  - erro é sempre expressão nua, nunca concatenado (princípio 4 do
//    CLAUDE.md); consentimento de liquidez só nasce por `=== true`
//    (T-NDY-04); zero conta de tamanho de ordem no front (T-NDY-06); zero
//    import de `api`/`persistence`/`store` (o despacho é injetado por prop).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { register } from "node:module";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const ler = (p) => readFileSync(p, "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

register("./_jsx_loader.mjs", import.meta.url);

const React = (await import("react")).default;
const { renderToStaticMarkup } = await import("react-dom/server");
const ExecutarPropostaMod = await import("../src/opcoes/ExecutarProposta.jsx");
const ExecutarProposta = ExecutarPropostaMod.default;
const { ehRecusaLiquidezDificil } = ExecutarPropostaMod;

const cpOperador = COPY.operador;
const cpEstudo = COPY.estudo;
const noop = async () => ({});

const render = (props) => renderToStaticMarkup(React.createElement(ExecutarProposta, props));

// ═══════════════════════════════════════════════════════════ (A) RENDER ═══

// ---- (1) sem dados.execucao -> markup vazio ------------------------------
const markupSemExecucao = render({ dados: { ticker: "PETR4" }, operador: true, onExecutar: noop, cp: cpOperador });
ok("dados sem execucao -> markup vazio", markupSemExecucao === "");

const dadosExecutavel = {
  ticker: "PETR4",
  execucao: {
    executavel: true, tipo: "call_coberta", contractSymbol: "PETRI400",
    expiration: "2026-09-19", contratos: 2, qtyAcoes: 200,
  },
};

// ---- (2) Modo Estudo — nunca mostra botão --------------------------------
const markupEstudo = render({ dados: dadosExecutavel, operador: false, onExecutar: noop, cp: cpEstudo });
ok("Modo Estudo: contém cp.curadoriaEstudoNaoExecuta",
  markupEstudo.includes(cpEstudo.curadoriaEstudoNaoExecuta));
ok("Modo Estudo: NÃO contém cp.curadoriaExecutarCta",
  !markupEstudo.includes(cpEstudo.curadoriaExecutarCta));
ok("Modo Estudo: nenhum <button", !/<button/.test(markupEstudo));

// ---- (3) Modo Operador, executável — botão + linha de execução simulada --
const markupOperador = render({ dados: dadosExecutavel, operador: true, onExecutar: noop, cp: cpOperador });
ok("Modo Operador executável: contém cp.curadoriaExecutarCta",
  markupOperador.includes(cpOperador.curadoriaExecutarCta));
ok("Modo Operador executável: contém cp.opcoesExecucaoSimulada",
  markupOperador.includes(cpOperador.opcoesExecucaoSimulada));

// ---- (4) não executável — motivo verbatim, sem botão ---------------------
const dadosNaoExecutavel = { ticker: "PETR4", execucao: { executavel: false, motivo: "MOTIVO-X" } };
const markupMotivo = render({ dados: dadosNaoExecutavel, operador: true, onExecutar: noop, cp: cpOperador });
ok("não executável: motivo do backend aparece verbatim", markupMotivo.includes("MOTIVO-X"));
ok("não executável: nenhum <button", !/<button/.test(markupMotivo));

// ---- (5) ehRecusaLiquidezDificil ------------------------------------------
ok('ehRecusaLiquidezDificil("Liquidez DIFÍCIL (score 30/100) — ...") === true',
  ehRecusaLiquidezDificil("Liquidez DIFÍCIL (score 30/100) — esta operação exige atenção.") === true);
ok('ehRecusaLiquidezDificil("Liquidez SEM MERCADO ...") === false',
  ehRecusaLiquidezDificil("Liquidez SEM MERCADO (score 0/100) — sem negócio.") === false);
ok("ehRecusaLiquidezDificil(null) === false", ehRecusaLiquidezDificil(null) === false);
ok('ehRecusaLiquidezDificil("") === false', ehRecusaLiquidezDificil("") === false);

// ═══════════════════════════════════════════════════════════ (B) ESTÁTICO ═

const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const mainBruto = ler(join(here, "..", "..", "server", "app", "main.py"));
ok("server/app/main.py contém o prefixo de recusa 'Liquidez DIFÍCIL (score' (acoplamento declarado)",
  /Liquidez DIFÍCIL \(score/.test(mainBruto));
ok("sanidade: prefixo inventado NÃO bate contra main.py", !/Liquidez FÁCIL \(score/.test(mainBruto));

const execPropostaBruto = ler(join(here, "..", "src", "opcoes", "ExecutarProposta.jsx"));
const execProposta = semComentario(execPropostaBruto);

ok("erro renderizado como expressão nua {atual.erro} (pelo menos 2x: checkbox e caixa de erro)",
  (execProposta.match(/\{atual\.erro\}/g) || []).length >= 2);
ok("sanidade: {atual.erro} bate quando presente", /\{atual\.erro\}/.test("<span>{atual.erro}</span>"));
ok("nenhum '+' concatenando atual.erro (nem antes nem depois)",
  !/atual\.erro\s*\+/.test(execProposta) && !/\+\s*atual\.erro/.test(execProposta));

ok('"(e && e.message) || String(e)" presente', execProposta.includes("(e && e.message) || String(e)"));
ok("sanidade: string exata bate quando presente",
  "x = (e && e.message) || String(e);".includes("(e && e.message) || String(e)"));

ok("aceitaLiquidezDificil construído com === true",
  /aceitaLiquidezDificil:\s*atual\.aceite === true/.test(execProposta));
ok("sanidade: regex bate contra a forma esperada",
  /aceitaLiquidezDificil:\s*atual\.aceite === true/.test("{ aceitaLiquidezDificil: atual.aceite === true }"));

ok("sem BOTAO_PRIMARIO (Fase 35 D-04: só 3 arquivos, este não é um deles)",
  !/BOTAO_PRIMARIO/.test(execProposta));
ok("sanidade: BOTAO_PRIMARIO bate quando presente", /BOTAO_PRIMARIO/.test("const BOTAO_PRIMARIO = {};"));

ok("sem #fff literal", !/#fff/i.test(execProposta));
ok("sanidade: #fff bate quando presente", /#fff/i.test("color: #fff"));

ok("sem '* 100' / '/ 100' / '* lote' (zero conta de tamanho de ordem, T-NDY-06)",
  !/\*\s*100/.test(execProposta) && !/\/\s*100/.test(execProposta) && !/\*\s*lote/i.test(execProposta));
ok("sanidade: os três padrões batem quando presentes",
  /\*\s*100/.test("x * 100") && /\/\s*100/.test("x / 100") && /\*\s*lote/i.test("x * lote"));

ok("sem import de ../api, ../persistence ou ../store",
  !/from\s+["']\.\.\/(api|persistence|store)(\.js)?["']/.test(execProposta));
ok("sanidade: import proibido bate quando presente",
  /from\s+["']\.\.\/(api|persistence|store)(\.js)?["']/.test('import { x } from "../api.js";'));

ok("sem useEffect (estado amarra à identidade de dados, premissa 8, sem efeito nenhum)",
  !/useEffect/.test(execProposta));
ok("sanidade: useEffect bate quando presente", /useEffect/.test("useEffect(() => {}, [])"));

// ---- SecaoAnalisar.jsx: <ExecutarProposta dentro do ramo proposta.dados ?,
// depois de <Pernas ---------------------------------------------------------
const secaoAnalisarBruto = ler(join(here, "..", "src", "opcoes", "SecaoAnalisar.jsx"));
const secaoAnalisar = semComentario(secaoAnalisarBruto);
const iPernas = secaoAnalisar.indexOf("<Pernas");
const iExecutarProposta = secaoAnalisar.indexOf("<ExecutarProposta");
ok("SecaoAnalisar.jsx importa ExecutarProposta", /import ExecutarProposta from "\.\/ExecutarProposta\.jsx"/.test(secaoAnalisar));
ok("SecaoAnalisar.jsx: <ExecutarProposta existe e vem DEPOIS de <Pernas",
  iPernas > -1 && iExecutarProposta > -1 && iExecutarProposta > iPernas);
// A fatia entre "proposta.dados ? (" e "<Pernas" continua dentro do MESMO
// ramo — se <ExecutarProposta estivesse fora do ternário, haveria um
// "proposta.dados ?" mais próximo dela que não é este.
const iRamoDados = secaoAnalisar.lastIndexOf("proposta.dados ? (", iExecutarProposta);
ok("SecaoAnalisar.jsx: <ExecutarProposta está dentro do ramo `proposta.dados ?`",
  iRamoDados > -1 && iRamoDados < iPernas);

// ---- OpcoesScreen.jsx: passa operador= e onExecutarProposta= a <SecaoAnalisar
const opcoesScreenBruto = ler(join(here, "..", "src", "opcoes", "OpcoesScreen.jsx"));
const opcoesScreen = semComentario(opcoesScreenBruto);
const iSecaoAnalisar = opcoesScreen.indexOf("<SecaoAnalisar");
const fechoSecaoAnalisar = opcoesScreen.indexOf("/>", iSecaoAnalisar);
const blocoSecaoAnalisar = iSecaoAnalisar > -1 && fechoSecaoAnalisar > -1
  ? opcoesScreen.slice(iSecaoAnalisar, fechoSecaoAnalisar)
  : "";
ok("OpcoesScreen.jsx: <SecaoAnalisar existe", iSecaoAnalisar > -1);
ok("OpcoesScreen.jsx: <SecaoAnalisar recebe prop operador=",
  /operador=\{/.test(blocoSecaoAnalisar));
ok("OpcoesScreen.jsx: <SecaoAnalisar recebe prop onExecutarProposta=",
  /onExecutarProposta=\{/.test(blocoSecaoAnalisar));
// Guardrail de fronteira: este onExecutarProposta NÃO pode ser a literal
// travada em test_opcoes_consolidacao_ui.mjs:197 (onExecutar={(cand, o) =>
// ctx.A.executarCandidatoCurado(cand, o)}) — a contagem de 1 daquele
// guardião não pode subir por acidente.
ok("onExecutarProposta NÃO usa a forma literal travada por test_opcoes_consolidacao_ui.mjs",
  !/onExecutarProposta=\{\(cand, o\) => ctx\.A\.executarCandidatoCurado\(cand, o\)\}/.test(blocoSecaoAnalisar));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
