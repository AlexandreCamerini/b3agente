// REANCORAGEM — Fase 48 (2026-10-05), caminho B: o par de estados `ticker` +
// `abaOpcoes` virou UM estado `nav` (navOpcoes.js), inicializado por
// `estadoInicialOpcoes` (que delega a abaInicialOpcoes/tickerInicialOpcoes/
// abrirTickerOpcoes — a PARTE A, comportamental, segue valendo sem mudança).
// A PARTE B troca as âncoras de fiação (B6-B12) pelas equivalentes do estado
// único; a invariante é a mesma (precedência no inicializador lazy, sem salto
// pós-paint, write-back sem cleanup, memória fora de store). Continuidade da
// ESCOLHA ao voltar (objetivo/vencimento/degrau preservados; trocar de ativo
// zera) é travada também em test_opcoes_nav_profundidade.mjs e nos ok()
// (reancorado 2026-10-05) de B15 abaixo. Texto original abaixo preservado.
//
// Fase 40, plano 40-01 (2026-09-25) — guardião do ESTADO-01: continuidade do
// ticker selecionado e da aba ativa da tela Opções entre trocas de aba
// principal, na MESMA sessão (D-01), com precedência deep-link > memória >
// default (D-03), validação contra allowlist/carteira (T-39-14, P-2),
// restauração silenciosa sem flash (D-05) e isolamento por escopo de conta
// (D-04/SC#4, cenário C2).
//
// Duas partes. Cada item nomeia o defeito que reprova:
//
// PARTE A (comportamental) — as três funções puras de
// `web/src/opcoes/memoriaOpcoes.js`:
//  - precedência errada (memória vencendo o deep-link, ou vice-versa fora de
//    ordem) reabriria o bug do cenário B (D-03);
//  - aceitar aba fora de `ABAS_OPCOES` ou ticker fora da carteira reabriria
//    T-39-14/P-2 (cenários E/E2, aba "lixo");
//  - `memoriaOpcoes` não normalizando o estado default para `null` quebraria
//    o cenário C2 ("a memória termina null").
//
// PARTE B (estrutural) — fiação em App.jsx/OpcoesScreen.jsx (Task 2 deste
// plano). Neste commit (Task 1) esta parte é VERMELHA DE PROPÓSITO: a fiação
// ainda não existe. É o RED do ciclo TDD do plano — a Parte A já nasce
// verde porque o módulo puro é criado neste mesmo commit.
//
// Roda sem build: `node web/tests/test_opcoes_continuidade_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { abaInicialOpcoes, tickerInicialOpcoes, memoriaOpcoes } from "../src/opcoes/memoriaOpcoes.js";

const here = dirname(fileURLToPath(import.meta.url));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Mesmo helper de test_opcoes_nav_tres_abas_ui.mjs — remove comentários antes
// de qualquer contagem, para o guardião não se auto-invalidar citando os
// próprios termos que reprova ao explicar a decisão.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

// Mesmo helper de test_logout_reset.mjs — isola o corpo de uma função pelo
// balanceamento de chaves a partir de uma âncora textual.
function bodyOf(src, anchor) {
  const at = src.indexOf(anchor);
  if (at < 0) return null;
  const open = src.indexOf("{", at + anchor.length);
  let depth = 0;
  for (let i = open; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) return src.slice(open, i + 1); }
  }
  return null;
}

// =========================================================================
// PARTE A — comportamental (memoriaOpcoes.js)
// =========================================================================

const ABAS = ["oportunidades", "recomendadas", "montar"];

// Sanidade: a lista usada neste teste tem de ser IDÊNTICA à ABAS_OPCOES real
// de OpcoesScreen.jsx — senão o teste comportamental valida contra uma
// allowlist divergente da que roda em produção.
const opcoesScreenBrutoParaSanidade = readFileSync(join(here, "..", "src", "opcoes", "OpcoesScreen.jsx"), "utf8");
const mABAS = opcoesScreenBrutoParaSanidade.match(/const ABAS_OPCOES = (\[[^\]]*\]);/);
ok("ABAS_OPCOES foi localizada em OpcoesScreen.jsx", !!mABAS);
ok("a lista ABAS deste teste é idêntica a ABAS_OPCOES de OpcoesScreen.jsx",
   !!mABAS && JSON.stringify(JSON.parse(mABAS[1])) === JSON.stringify(ABAS));

// --- abaInicialOpcoes ------------------------------------------------------
ok("abaInicialOpcoes: sem deep-link, sem memória → default \"oportunidades\"",
   abaInicialOpcoes(ABAS, null, null) === "oportunidades");
ok("abaInicialOpcoes: sem deep-link, memória válida → usa a memória (cenário A/F)",
   abaInicialOpcoes(ABAS, null, { ticker: "PETR4", aba: "montar" }) === "montar");
ok("abaInicialOpcoes: memória sem ticker mas aba válida → usa a aba (A2)",
   abaInicialOpcoes(ABAS, null, { ticker: "", aba: "recomendadas" }) === "recomendadas");
ok("abaInicialOpcoes: deep-link válido vence memória válida (D-03, cenário B)",
   abaInicialOpcoes(ABAS, "recomendadas", { ticker: "PETR4", aba: "montar" }) === "recomendadas");
ok("abaInicialOpcoes: deep-link inválido com memória válida → usa a memória (T-39-14)",
   abaInicialOpcoes(ABAS, "lixo", { aba: "montar" }) === "montar");
ok("abaInicialOpcoes: deep-link inválido sem memória → default (T-39-14)",
   abaInicialOpcoes(ABAS, "lixo", null) === "oportunidades");
ok("abaInicialOpcoes: sem deep-link, memória com aba inválida → default",
   abaInicialOpcoes(ABAS, null, { aba: "lixo" }) === "oportunidades");
ok("abaInicialOpcoes: sem deep-link, memória vazia ({}) → default",
   abaInicialOpcoes(ABAS, null, {}) === "oportunidades");

// --- tickerInicialOpcoes ----------------------------------------------------
ok("tickerInicialOpcoes: ticker lembrado presente na carteira → restaura (A)",
   tickerInicialOpcoes({ ticker: "PETR4", aba: "montar" }, [{ t: "PETR4" }, { t: "VALE3" }]) === "PETR4");
ok("tickerInicialOpcoes: ticker lembrado vendido, fora da carteira → vazio (E)",
   tickerInicialOpcoes({ ticker: "PETR4", aba: "montar" }, [{ t: "VALE3" }]) === "");
ok("tickerInicialOpcoes: carteira vazia → vazio (E2)",
   tickerInicialOpcoes({ ticker: "PETR4" }, []) === "");
ok("tickerInicialOpcoes: sem memória → vazio, NUNCA auto-seleciona o primeiro ativo",
   tickerInicialOpcoes(null, [{ t: "PETR4" }]) === "");
ok("tickerInicialOpcoes: memória com ticker vazio (desseleção lembrada) → vazio (G)",
   tickerInicialOpcoes({ ticker: "" }, [{ t: "PETR4" }]) === "");
ok("tickerInicialOpcoes: ticker não-string é rejeitado",
   tickerInicialOpcoes({ ticker: 42 }, [{ t: 42 }]) === "");

// --- memoriaOpcoes -----------------------------------------------------------
ok("memoriaOpcoes: estado default (\"\", \"oportunidades\") normaliza para null (C2)",
   memoriaOpcoes("", "oportunidades") === null);
ok("memoriaOpcoes: ticker + aba não-default → objeto { ticker, aba }",
   JSON.stringify(memoriaOpcoes("PETR4", "montar")) === JSON.stringify({ ticker: "PETR4", aba: "montar" }));
ok("memoriaOpcoes: sem ticker mas aba não-default → memória regravada sem ticker (E)",
   JSON.stringify(memoriaOpcoes("", "montar")) === JSON.stringify({ ticker: "", aba: "montar" }));
ok("memoriaOpcoes: ticker mantido ao trocar para aba \"recomendadas\" (B/P-1)",
   JSON.stringify(memoriaOpcoes("PETR4", "recomendadas")) === JSON.stringify({ ticker: "PETR4", aba: "recomendadas" }));

// =========================================================================
// PARTE B — estrutural (App.jsx + OpcoesScreen.jsx, fiação da Task 2)
// =========================================================================

const appBruto = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persBruto = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const opcoesScreenBruto = opcoesScreenBrutoParaSanidade;
const memoriaOpcoesBruto = readFileSync(join(here, "..", "src", "opcoes", "memoriaOpcoes.js"), "utf8");

const app = semComentario(appBruto);
const opcoesScreen = semComentario(opcoesScreenBruto);

// ---- B1) declaração dos dois estados novos em App.jsx ----------------------
ok("App.jsx declara opcoesMemoria com useState(null)",
   /const \[opcoesMemoria, setOpcoesMemoria\] = useState\(null\);/.test(app));
ok("App.jsx declara escopoOpcoes com useState(0)",
   /const \[escopoOpcoes, setEscopoOpcoes\] = useState\(0\);/.test(app));

// ---- B2) ctx expõe opcoesMemoria + lembrarOpcoes ---------------------------
ok("ctx expõe opcoesMemoria,", /\bopcoesMemoria,/.test(app));
ok("ctx expõe lembrarOpcoes: (m) => setOpcoesMemoria(m),",
   /lembrarOpcoes: \(m\) => setOpcoesMemoria\(m\),/.test(app));

// ---- B3) _resetScopeState limpa a memória e incrementa o escopo (D-04/SC#4, C2) --
const reset = bodyOf(app, "const _resetScopeState = () =>");
ok("_resetScopeState existe", !!reset);
ok("_resetScopeState chama setOpcoesMemoria(null)", !!reset && reset.includes("setOpcoesMemoria(null)"));
ok("_resetScopeState chama setEscopoOpcoes((n) => n + 1)", !!reset && reset.includes("setEscopoOpcoes((n) => n + 1)"));

// ---- B4) render usa key de escopo (mecanismo de C2) ------------------------
ok('render: {tab === "opcoes" && <OpcoesScreen key={escopoOpcoes} ctx={ctx} />}',
   /\{tab === "opcoes" && <OpcoesScreen key=\{escopoOpcoes\} ctx=\{ctx\} \/>\}/.test(app));

// ---- B5) D-01: memória nunca passa por store/persistence/localStorage -----
const linhasComOpcoesMemoria = app.split("\n").filter((l) => l.includes("opcoesMemoria"));
ok("nenhuma linha de App.jsx contém opcoesMemoria E store. ao mesmo tempo (D-01)",
   linhasComOpcoesMemoria.every((l) => !l.includes("store.")));
ok("persistence.js não contém opcoesMemoria", !/opcoesMemoria/.test(persBruto));
ok("persistence.js não contém lembrarOpcoes", !/lembrarOpcoes/.test(persBruto));
ok("OpcoesScreen.jsx não contém localStorage/sessionStorage",
   !/localStorage|sessionStorage/.test(opcoesScreenBruto));
ok("memoriaOpcoes.js não contém localStorage/sessionStorage (fora de comentário)",
   !/localStorage|sessionStorage/.test(semComentario(memoriaOpcoesBruto)));

// ---- B6) OpcoesScreen importa as três funções puras ------------------------
// Reversão deliberada Fase 45 (D-05): o import ganha abrirTickerOpcoes (one-shot do "Encerrar estrutura…"); as três funções originais continuam exigidas.
// REANCORAGEM (2026-10-05, Fase 48): as três funções puras de entrada são
// consumidas por navOpcoes.js (estadoInicialOpcoes); OpcoesScreen mantém só
// `memoriaOpcoes` (write-back).
const navOpcoesBruto = readFileSync(join(here, "..", "src", "opcoes", "navOpcoes.js"), "utf8");
ok('OpcoesScreen importa { memoriaOpcoes } de "./memoriaOpcoes.js" (write-back) (reancorado 2026-10-05)',
   /import\s*\{\s*memoriaOpcoes\s*\}\s*from\s*["']\.\/memoriaOpcoes\.js["']/.test(opcoesScreenBruto));
ok('navOpcoes.js importa { tickerInicialOpcoes, abrirTickerOpcoes, abaInicialOpcoes } de "./memoriaOpcoes.js" (reancorado 2026-10-05)',
   /import\s*\{\s*tickerInicialOpcoes,\s*abrirTickerOpcoes,\s*abaInicialOpcoes\s*\}\s*from\s*["']\.\/memoriaOpcoes\.js["']/.test(navOpcoesBruto));

// ---- B7) inicializador lazy do ticker --------------------------------------
// REANCORAGEM (2026-10-05): ticker E aba nascem do MESMO inicializador lazy do nav.
const reNav = /const \[nav, setNav\] = useState\(\(\) => estadoInicialOpcoes\(\{[\s\S]*?memoria: ctx && ctx\.opcoesMemoria,[\s\S]*?carteira,[\s\S]*?\}\)\);/;
ok("nav: inicializador lazy lê estadoInicialOpcoes({ ..., memoria: ctx && ctx.opcoesMemoria, carteira }) — ticker restaurado só se estiver na carteira (reancorado 2026-10-05)",
   reNav.test(opcoesScreenBruto));
ok("estadoInicialOpcoes restaura o ticker via tickerInicialOpcoes(memoria, carteira) (reancorado 2026-10-05)",
   /tickerInicialOpcoes\(memoria, carteira\)/.test(navOpcoesBruto));

// ---- B8) inicializador lazy da aba ------------------------------------------
const reAba = reNav;
ok("aba: o deep-link (abaInicial: ctx && ctx.opcoesAbaInicial) entra no mesmo inicializador e a validação de allowlist é de abaInicialOpcoes (reancorado 2026-10-05)",
   /abaInicial: ctx && ctx\.opcoesAbaInicial,/.test(opcoesScreenBruto) && /abaInicialOpcoes\(abas, null, memoria\)/.test(navOpcoesBruto));

// ---- B9) `carteira` declarada ANTES do useState do ticker -------------------
const iCarteira = opcoesScreenBruto.indexOf("const carteira =");
const iTickerState = opcoesScreenBruto.indexOf("const [nav, setNav]");
ok("const carteira = ... vem antes de const [nav, setNav] (ordem de declaração) (reancorado 2026-10-05)",
   iCarteira >= 0 && iTickerState > iCarteira);

// ---- B10) D-05: nenhum useEffect com opcoesMemoria chama setTicker/setAbaOpcoes --
const blocosUseEffect = opcoesScreen.match(/useEffect\(\(\) => \{[\s\S]*?\}, \[[^\]]*\]\);/g) || [];
ok("localizou ao menos um useEffect em OpcoesScreen.jsx (parse mudo)", blocosUseEffect.length > 0);
ok("nenhum useEffect com opcoesMemoria chama setNav( — sem salto pós-paint (D-05) (reancorado 2026-10-05)",
   blocosUseEffect.every((b) => !(/opcoesMemoria/.test(b) && /setNav\(/.test(b))));

// ---- B11) write-back sem cleanup --------------------------------------------
const blocoWriteBack = blocosUseEffect.find((b) => /ctx\.lembrarOpcoes\(memoriaOpcoes\(nav\.ticker, nav\.nivel === "montar" \? "montar" : "oportunidades"\)\)/.test(b));
ok("existe useEffect com ctx.lembrarOpcoes(memoriaOpcoes(nav.ticker, <aba derivada do nível>)) — allowlist antiga de memória preservada (reancorado 2026-10-05)", !!blocoWriteBack);
ok("esse useEffect tem deps exatamente [nav.ticker, nav.nivel] (reancorado 2026-10-05)",
   !!blocoWriteBack && /\}, \[nav\.ticker, nav\.nivel\]\);$/.test(blocoWriteBack));
ok("esse useEffect NÃO contém return (sem cleanup — cenário C)",
   !!blocoWriteBack && !/return/.test(blocoWriteBack));
ok("lembrarOpcoes nunca aparece dentro de um `return () =>` (sem escrita em unmount) no arquivo",
   !/return \(\) => \{[^}]*lembrarOpcoes/.test(opcoesScreen) && !/return \(\) => ctx\.lembrarOpcoes/.test(opcoesScreen));

// ---- B12) restauração não passa por escolherTicker ---------------------------
const matchTicker = opcoesScreenBruto.match(reNav);
const matchAba = opcoesScreenBruto.match(reAba);
ok("o inicializador do ticker (nav) não contém escolherTicker",
   !!matchTicker && !/escolherTicker/.test(matchTicker[0]));
ok("o inicializador da aba (nav) não contém escolherTicker",
   !!matchAba && !/escolherTicker/.test(matchAba[0]));

// ---- B13) one-shot de opcoesAbaInicial continua intacto ----------------------
ok("continua existindo o useEffect one-shot com limparOpcoesAbaInicial() e deps []",
   /useEffect\(\(\) => \{[\s\S]{0,200}limparOpcoesAbaInicial\(\)[\s\S]{0,80}\}, \[\]\);/.test(opcoesScreenBruto));

// ---- B14) D-05/UI-SPEC: nenhum literal novo proibido de "restauração" -------
ok('OpcoesScreen.jsx não contém a string "Voltamos" fora de comentário',
   !/Voltamos/i.test(opcoesScreen));
ok('OpcoesScreen.jsx não contém a string "restaurad" fora de comentário',
   !/restaurad/i.test(opcoesScreen));

// ---- B15) (reancorado 2026-10-05) continuidade da escolha no estado único --
// Substitui, para o invariante "o que o usuário escolheu não se perde ao
// navegar", a continuidade ENTRE ABAS pela continuidade entre NÍVEIS.
const nav = await import("../src/opcoes/navOpcoes.js");
{
  let e = nav.estadoInicialOpcoes({ abas: ABAS, carteira: [{ t: "PETR4" }] });
  e = nav.abrirAtivo(e, "PETR4");
  e = nav.escolherObjetivo(e, "proteger");
  e = nav.escolherVencimento(e, "2026-11-21");
  e = nav.escolherDegrau(e, "d1");
  e = nav.irConfirmar(e);
  const volta = nav.voltar(nav.voltar(e)); // confirmar -> escada -> objetivo
  ok("voltar preserva ativo/objetivo/vencimento/degrau ao subir níveis (reancorado 2026-10-05)",
     volta.nivel === "objetivo" && volta.ticker === "PETR4" && volta.objetivo === "proteger"
     && volta.vencimento === "2026-11-21" && volta.degrauId === "d1");
  const outro = nav.abrirAtivo(volta, "VALE3");
  ok("trocar de ativo zera objetivo/vencimento/degrau (reancorado 2026-10-05)",
     outro.ticker === "VALE3" && outro.objetivo === null && outro.vencimento === null && outro.degrauId === null);
  const reabre = nav.abrirAtivo(volta, "PETR4");
  ok("reabrir o MESMO ativo mantém a escolha (reancorado 2026-10-05)",
     reabre.objetivo === "proteger" && reabre.degrauId === "d1");
}

console.log(fails === 0 ? "TODOS OS " + "TESTES PASSARAM" : fails + " FALHA(S)");
if (fails > 0) {
  process.exit(1);
}
