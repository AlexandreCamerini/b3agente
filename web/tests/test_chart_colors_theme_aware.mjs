// qa/29 (B2) — Guardião: componentes de gráfico/SVG não podem usar T.x (a
// referência de string "var(--x)") em atributos de apresentação fill=/stroke=.
//
// BUG: o próprio código já documentava esse padrão (comentário de FASE 8B/N1
// perto da definição de PALETTE/MODE_OPERADOR): atributos de apresentação
// SVG (fill=, stroke=, como STRING crua, fora de style=) não resolvem
// var(--x) de forma confiável neste WebKit — o elemento renderiza com a cor
// da PALETA BASE (ex.: accent azul do tema dark "Estudo"), ignorando o
// override do Modo Operador. O fix documentado usa usePalette() (hex já
// resolvido, mesclado com MODE_OPERADOR) em vez de T.x nesses atributos.
// O fix original só cobriu PriceChart (o gráfico principal via
// lightweight-charts) — OpsSparkline (marcações de compra/venda) e
// CapitalCurve (Patrimônio Simulado) ficaram de fora e reproduziam o mesmo
// bug: "gráficos ficam com cor errada no Modo Operador" (qa/26 B2).
// Este guardião tranca que NENHUM desses três componentes volte a usar T.x
// dentro de fill=/stroke=.
// Roda sem build: `node web/tests/test_chart_colors_theme_aware.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Extrai o corpo de uma função top-level pelo nome (até o próximo
// "\n}\n" no início de linha — mesma convenção usada nos demais guardiões
// deste projeto para varrer trechos específicos do App.jsx).
function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  const start = m.index;
  // m[0] já inclui a chave de abertura do CORPO da função (fim do match) —
  // começa a contar profundidade A PARTIR DELA, não do início de "function",
  // senão a desestruturação dos parâmetros (ex.: "({ candles, ops })") já
  // teria sua própria chave balanceada e encerraria a busca cedo demais.
  let depth = 0, i = start + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(start, i);
}

for (const name of ["OpsSparkline", "CapitalCurve", "PriceChart"]) {
  const body = functionBody(name);
  ok(`${name}: função localizada em App.jsx`, !!body);
  if (!body) continue;
  ok(`${name}: usa usePalette() (hex resolvido, não var())`, /usePalette\(\)/.test(body));
  ok(`${name}: nenhum fill={T\\. ou stroke={T\\. (var() cru em atributo SVG)`,
    !/(?:fill|stroke)=\{T\./.test(body));
}

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
