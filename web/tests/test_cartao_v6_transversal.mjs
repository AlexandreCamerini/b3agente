// Fase 46 (46-08, D-14/D-17, 2026-10-01) — guardião TRANSVERSAL do card v6.
// Varre como TEXTO a fatia ReguaPlano → LinhaChamadaOpcoes + CardPosicaoEstruturada
// (App.jsx): zero hex, zero `disabled=`, alvos >= 44 px, tipografia 12/14/20 e
// pesos 400/700, zero HTML injetado, zero cálculo de opções no front e nenhuma
// aritmética sobre valores financeiros (todo número vem do backend, D-01/D-02).
// Reversão deliberada atualiza este guardião com nota (CLAUDE.md).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function fimDaFuncao(inicio) {
  const prox = src.indexOf("\nfunction ", inicio + 10);
  return prox < 0 ? src.length : prox;
}
const a = src.indexOf("function ReguaPlano(");
const b = src.indexOf("function LinhaChamadaOpcoes(");
const c = src.indexOf("function CardPosicaoEstruturada(");
ok("âncoras da fatia v6 existem e em ordem", a > 0 && b > a && c > 0);
const fatia = src.slice(a, b);
const card = src.slice(c, fimDaFuncao(c));
ok("fatias não são vazias", fatia.length > 20000 && card.length > 2000);

// Sem comentários de linha inteira e sem comentário JSX (prosa pode citar hex/regras).
function limpo(t) {
  return t.replace(/\{\/\*[\s\S]*?\*\/\}/g, "").split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
}
const alvo = limpo(fatia) + "\n" + limpo(card);

// ---- autoteste dos detectores ---------------------------------------------
const reHex = /#[0-9a-fA-F]{3,8}\b/;
const reDisabled = /(^|[^-\w])disabled\s*=/;
ok("autoteste hex flagra", reHex.test('color: "#fff"') && !reHex.test("color: T.accent"));
ok("autoteste disabled flagra e ignora aria-disabled", reDisabled.test("<button disabled={x}>") && !reDisabled.test("aria-disabled={x}"));

// ---- higiene ---------------------------------------------------------------
ok("zero hex literal (só tokens T.*)", !reHex.test(alvo));
ok("zero `disabled=` (usar aria-disabled + motivo visível)", !reDisabled.test(alvo));
ok("zero dangerouslySetInnerHTML", !alvo.includes("dangerouslySetInnerHTML"));
ok("zero markPrice( e optionsCalc (números de opções vêm do backend, D-02)", !/markPrice\(|optionsCalc/.test(alvo));

// ---- tipografia -------------------------------------------------------------
{
  const pesos = [...alvo.matchAll(/fontWeight:\s*([^,}]+)/g)].map((m) => m[1].trim());
  // 46-UAT (2026-10-01, G-02): a linha Estrutura usa o ternário `l.total ? 700 : 400` (só 400/700, mesma escala).
  const ruins = pesos.filter((p) => p !== "400" && p !== "700" && p !== "l.total ? 700 : 400");
  ok(`fontWeight só 400/700 (${pesos.length} usos)`, pesos.length > 0 && ruins.length === 0);
  const tam = [...alvo.matchAll(/fontSize:\s*([^,}]+)/g)].map((m) => m[1].trim());
  // 46-UAT G-01/G-04/G-05: 21/11/11.5 px (TIPO_CARD.valor|legenda|chip), redução determinística do valor
  // (fonteValorCabecalho) e o ternário corpo/rótulo da linha Estrutura, aprovados pelo Alex.
  // NOTA 2026-10-08 (quick 261008-dgv, Onda E): GradeConta usa `fmt(cel).length > 11 ? TIPO_CARD.rotulo : TIPO_CARD.corpo` para o valor monetário
  // longo não quebrar linha; ambos os operandos são tokens da escala (nenhuma asserção removida, só a alternativa nova aceita).
  const okTam = (t) => /^TIPO_CARD\.(titulo|corpo|rotulo|valor|legenda|chip)$/.test(t) || t === "fonteValorCabecalho(txtValor)" || t === "l.total ? TIPO_CARD.corpo : TIPO_CARD.rotulo" || t === "fmt(cel).length > 11 ? TIPO_CARD.rotulo : TIPO_CARD.corpo" || ["12", "14", "20", '"12px"', '"14px"', '"20px"'].includes(t);
  const ruinsT = tam.filter((t) => !okTam(t));
  if (ruinsT.length) console.log("  fontSize fora da escala:", ruinsT.join(" | "));
  ok(`fontSize só 12/14/20 (${tam.length} usos)`, tam.length > 0 && ruinsT.length === 0);
}

// ---- alvos de toque ---------------------------------------------------------
{
  const buttons = [];
  const re = /<button\b/g;
  let m;
  while ((m = re.exec(alvo))) {
    const fim = alvo.indexOf("</button>", m.index);
    const prox = alvo.indexOf("<button", m.index + 7);
    const limite = Math.min(...[fim, prox, m.index + 1200].filter((x) => x > 0));
    buttons.push(alvo.slice(m.index, limite));
  }
  ok("há botões na fatia", buttons.length >= 10);
  const semMin = [];
  for (const bt of buttons) {
    const mh = /minHeight:\s*(`[^`]*`|"[^"]*"|[^,}\s]+)/.exec(bt);
    const n = mh ? parseInt(mh[1].replace(/[^0-9]/g, ""), 10) : 0;
    const inline = /textDecoration:\s*"underline dotted"/.test(bt); // termo inline (UI-SPEC exceção a: 28 px)
    if (inline) { if (n < 28) semMin.push(bt.slice(0, 60)); continue; }
    if (!(n >= 44)) semMin.push(bt.slice(0, 80).replace(/\s+/g, " "));
  }
  if (semMin.length) for (const s of semMin) console.log("  botão sem minHeight >= 44:", s);
  ok(`todo <button> tem minHeight >= 44 (termo inline 28) — ${buttons.length} botões`, semMin.length === 0);
}

// ---- aritmética sobre valores financeiros (D-01) ---------------------------
{
  const FIN = "(?:preco|resultado|be|k|stop|alvo|avg|valor|distStopPct|ateBePct)";
  // (operador com espaços — prosa tipo `stop/alvo` em texto JSX não conta) operando financeiro adjacente a + - * / (aceita `.campo` e `?.campo`); ignora
  // `//`, `/>`, `</`, `+=`... e operadores dentro de string/regex simples.
  const reA = new RegExp(`(?<![\\w$])(?:[\\w$]+\\??\\.)*${FIN}(?![\\w])\\s+[-+*/]\\s+[\\w(]`, "g");
  const reB = new RegExp(`[\\w)\\]]\\s+[-+*/]\\s+(?:[\\w$]+\\??\\.)*${FIN}(?![\\w])`, "g");
  const semStrings = alvo.replace(/"[^"\n]*"|'[^'\n]*'|`[^`\n]*`/g, '""').replace(/<\/?\w+[^>]*>/g, (t) => t.replace(/[-+*/]/g, " "));
  // layout liberado por nome: posRegua / xDoGrafico / yDoGrafico (retiram o operando).
  const achados = [];
  for (const re of [reA, reB]) {
    let mm;
    while ((mm = re.exec(semStrings))) {
      const ctx = semStrings.slice(Math.max(0, mm.index - 40), mm.index + mm[0].length + 20).replace(/\s+/g, " ");
      if (/posRegua|xDoGrafico|yDoGrafico|dominioRegua/.test(ctx)) continue;
      achados.push(ctx);
    }
  }
  if (achados.length) for (const x of achados) console.log("  aritmética suspeita:", x);
  ok("nenhuma aritmética (+ - * /) sobre preco|resultado|be|k|stop|alvo|avg|valor|distStopPct|ateBePct", achados.length === 0);
  // autoteste: os dois detectores flagram contas reais e ignoram nomes parecidos
  const t = (re, txt) => { re.lastIndex = 0; return re.test(txt); };
  ok("autoteste aritmética flagra `p.stop - p.avg`, `valor * 2` e `2 * e.cenarios.be`",
    t(reA, "p.stop - p.avg") && t(reA, "valor * 2") && t(reB, "2 * e.cenarios.be"));
  ok("autoteste aritmética ignora `kicker - 1` e `stopLabel + x`", !t(reA, "kicker - 1") && !t(reA, "stopLabel + x"));
}

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
