// Plano 04-06 (FIX-C03) — guardião estático da 2ª série (Ibovespa) e do modo
// de falha em CapitalCurve (Passo 8). Trava o contrato visual do UI-SPEC
// (04-UI-SPEC.md, seção FIX-C03): série tracejada neutra, z-order, célula
// VS. IBOVESPA condicional, frase única de indisponibilidade — sem nunca
// desenhar dado que não existe (guardrail CLAUDE.md, princípio 4).
// Roda sem build: `node web/tests/test_benchmark_curva.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Mesma convenção dos demais guardiões estáticos deste projeto
// (test_chart_colors_theme_aware.mjs): localiza o corpo de uma função
// top-level pelo balanceamento de chaves a partir do nome.
function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  const start = m.index;
  let depth = 0, i = start + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(start, i);
}

const cc = functionBody("CapitalCurve");
ok("CapitalCurve: função localizada em App.jsx", !!cc);

if (cc) {
  // ---- (a) traço do Ibovespa: tracejado + P.textDim, nunca cor semântica ----
  ok("(a) path do Ibovespa usa strokeDasharray=\"3 3\"", /strokeDasharray="3 3"/.test(cc));
  ok("(a) path do Ibovespa usa stroke={P.textDim}", /stroke=\{P\.textDim\}/.test(cc));
  // isola só a linha do path do benchmark para não capturar P.positive/negative
  // usados legitimamente em OUTROS elementos (legenda "sua carteira", gradiente).
  const linhaIbov = (cc.match(/<path d=\{ibovPath\}[^/]*\/>/) || [""])[0];
  ok("(a) path do Ibovespa foi encontrado por inteiro", linhaIbov.length > 0);
  ok("(a) path do Ibovespa NÃO usa P.positive/P.negative/P.accent",
    linhaIbov.length > 0 && !/P\.(positive|negative|accent)/.test(linhaIbov));

  // ---- (b) z-order: Ibovespa ANTES da carteira no fonte ----
  const iIbov = cc.indexOf("<path d={ibovPath}");
  const iCarteira = cc.indexOf("<path d={path}");
  ok("(b) path do Ibovespa aparece ANTES do path da carteira (z-order)",
    iIbov >= 0 && iCarteira >= 0 && iIbov < iCarteira);

  // ---- (c) célula VS. IBOVESPA existe e é condicional ----
  const nVsIbov = (cc.match(/VS\. IBOVESPA/g) || []).length;
  ok("(c) célula \"VS. IBOVESPA\" aparece exatamente 1x", nVsIbov === 1);
  ok("(c) célula é condicional a diffIbov != null (retAcum do benchmark)",
    /diffIbov != null && stat\("VS\. IBOVESPA"/.test(cc));

  // ---- (d) frase de indisponibilidade: verbatim, T.textFaint, não T.negative ----
  const nFrase = (cc.match(/Comparação com o Ibovespa indisponível agora\./g) || []).length;
  ok("(d) frase de indisponibilidade aparece exatamente 1x, verbatim", nFrase === 1);
  const blocoFrase = (cc.match(/<div[^>]*>\s*Comparação com o Ibovespa indisponível agora\./) || [""])[0];
  ok("(d) frase usa T.textFaint", /T\.textFaint/.test(blocoFrase));
  ok("(d) frase NÃO usa T.negative (não é erro/alarme)", !/T\.negative/.test(blocoFrase));

  // ---- (e) nenhuma linha plana fabricada no caminho do benchmark ----
  // procura "|| 0" / "?? 0" nas linhas que envolvem bm.pct/ibovPath — não
  // pode existir: ponto sem cobertura tem que ficar null, nunca virar 0.
  const linhasBenchmark = cc.split("\n").filter((l) => /\bbm\.pct\b|\bibovPath\b/.test(l));
  const violacao = linhasBenchmark.find((l) => /\|\|\s*0\b|\?\?\s*0\b/.test(l));
  ok("(e) nenhum '|| 0' / '?? 0' nas linhas que produzem bm.pct/ibovPath", !violacao);

  // ---- import de benchmarkSerie na mesma linha de equityCurve (linha 15) ----
  const linha15 = src.split("\n")[14] || "";
  ok("benchmarkSerie importado de ./finance.js na mesma linha de equityCurve",
    /\bbenchmarkSerie\b/.test(linha15) && /\bequityCurve\b/.test(linha15) && /from "\.\/finance\.js"/.test(linha15));

  // ---- placeholder de estado vazio (!hasSeries) permanece intocado ----
  ok("estado vazio (!hasSeries) segue com o mesmo placeholder tracejado",
    /M0,72 C60,66 110,58 150,52 C200,45 250,40 300,30/.test(cc));

  // ---- busca do benchmark não dispara sem série (T-04-20: sem retry, 1x por montagem) ----
  ok("efeito consulta store.benchmarkIbov (1x por montagem, guarda hasSeries)",
    /store\.benchmarkIbov\(period\)/.test(cc) && /if \(!hasSeries\) return/.test(cc));
}

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
