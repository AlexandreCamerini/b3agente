// Guardião do Brand Book v2 (2026-08-08) — trava os tokens de marca, os dois
// eixos (tema × modo) e o contraste do que é lido como TEXTO.
//
// Por que existe: a Fase 3 aplicou o Brand Book v1, que só especificava o tema
// ESCURO e não separava cor por modo. Resultado: o Estudo usava o âmbar da
// marca como acento de UI, e o tema claro seguia com hex antigos sem fonte de
// verdade. v2 fecha os dois furos e adiciona uma regra explícita — "nunca
// recolorir os óculos fora do âmbar da marca" —, então este guardião impede
// que qualquer uma das três coisas volte atrás:
//   1. âmbar/verde/rosa da marca com hex diferente do Brand Book;
//   2. o símbolo (LogoMark) voltando a seguir o acento do modo;
//   3. um token usado como TEXTO caindo abaixo de AA no seu tema.
//
// O item 3 é o que documenta a ÚNICA divergência deliberada em relação ao
// Brand Book: v2 diz que o verde de compra (#34d399) e o rosa de venda
// (#f26d6d) "não mudam com tema ou modo", mas neste app essas duas cores são
// COR DE TEXTO em ~72 lugares (valores de P&L), e sobre fundo claro elas medem
// 1,92:1 e 2,92:1 — reprovam AA com folga. No tema claro usamos o tom mais
// próximo da marca que passa (mesma matiz, luminosidade menor). No tema
// escuro, onde os hex da marca passam com folga (8,5:1 e 5,6:1), eles valem
// literalmente. Se alguém "corrigir" o claro de volta pro hex cru da marca,
// este teste falha e explica o porquê.
// Roda sem build: `node web/tests/test_brand_book_v2_tokens.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// --- leitura dos blocos de token direto do fonte (sem build/JSDOM) ---------
function objectBody(decl) {
  const i = src.indexOf(decl);
  if (i < 0) return null;
  let depth = 0, start = src.indexOf("{", i), j = start;
  for (; j < src.length; j++) {
    if (src[j] === "{") depth++;
    else if (src[j] === "}") { depth--; if (depth === 0) break; }
  }
  return src.slice(start, j + 1);
}
function scheme(block, name) {
  const i = block.indexOf(name + ": {");
  if (i < 0) return {};
  let depth = 0, start = block.indexOf("{", i), j = start;
  for (; j < block.length; j++) {
    if (block[j] === "{") depth++;
    else if (block[j] === "}") { depth--; if (depth === 0) break; }
  }
  const body = block.slice(start, j + 1);
  const out = {};
  for (const m of body.matchAll(/(\w+):\s*"(#[0-9a-fA-F]{6})"/g)) out[m[1]] = m[2].toLowerCase();
  // valores escritos como BRAND.x resolvem pelo bloco BRAND
  for (const m of body.matchAll(/(\w+):\s*BRAND\.(\w+)/g)) out[m[1]] = BRAND[m[2]];
  return out;
}
const brandBlock = objectBody("const BRAND = ");
const BRAND = {};
for (const m of brandBlock.matchAll(/(\w+):\s*"(#[0-9a-fA-F]{6})"/g)) BRAND[m[1]] = m[2].toLowerCase();

const paletteBlock = objectBody("const PALETTE = ");
const modeBlock = objectBody("const MODE_OPERADOR = ");
const estudo = { dark: scheme(paletteBlock, "dark"), light: scheme(paletteBlock, "light") };
const operadorOverride = { dark: scheme(modeBlock, "dark"), light: scheme(modeBlock, "light") };
const operador = {
  dark: { ...estudo.dark, ...operadorOverride.dark },
  light: { ...estudo.light, ...operadorOverride.light },
};

// --- contraste WCAG --------------------------------------------------------
const lin = (x) => (x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4));
function luminance(hex) {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => lin(parseInt(h.slice(i, i + 2), 16) / 255));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrast(a, b) {
  const [x, y] = [luminance(a), luminance(b)];
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

// === 1. cores de MARCA: hex literais do Brand Book v2 ======================
ok("BRAND.amber é #f2a93b", BRAND.amber === "#f2a93b");
ok("BRAND.amberDark é #c9791b", BRAND.amberDark === "#c9791b");
ok("BRAND.green (compra) é #34d399", BRAND.green === "#34d399");
ok("BRAND.red (venda) é #f26d6d", BRAND.red === "#f26d6d");

// === 2. neutros: hex literais do bloco "Design tokens" de v2 ===============
// dark: --bg #10121a, --bg-2 #161927, --panel #1b1f2e, --line #2c3245,
//       --ink #eef1f8, --muted #9aa3bd, --muted-2 #6f7797
//
// FIX-C16 (REPORT-01, fechado na Fase 4): o Brand Book v2 especificava
// --muted-2 #6f7797 (dark) / #7a8099 (light) — esses valores reprovavam AA
// (3,43-4,24:1 conforme a superfície; pior contra bgCard/bgPanel do que
// contra o bgBase que a auditoria original mediu). C-16 os substitui pelo
// mesmo tom com luminosidade ajustada, mesma metodologia que a seção 3 deste
// arquivo já usa para justificar o dourado claro #8a6c1c.
const NEUTROS = {
  dark: { bgBase: "#10121a", bgPanel: "#161927", bgCard: "#1b1f2e", borderSubtle: "#2c3245",
          textPrimary: "#eef1f8", textMuted: "#9aa3bd", textFaint: "#7f86a2" },
  light: { bgBase: "#f7f8fc", bgPanel: "#eef0f7", bgCard: "#ffffff", borderSubtle: "#e2e5f0",
           textPrimary: "#10121a", textMuted: "#5b6178", textFaint: "#666c85" },
};
for (const tema of ["dark", "light"]) {
  for (const [k, v] of Object.entries(NEUTROS[tema])) {
    ok(`neutro ${tema}.${k} = ${v} (Brand Book v2)`, estudo[tema][k] === v);
  }
}

// === 3. dois eixos: o acento é do MODO, não da marca =======================
// Paleta de acentos entregue pelo Alex em 08/08/2026, hex a hex, no lugar do
// azul/verde que o Brand Book v2 sugeria: Estudo = azul-esverdeado, Operador =
// dourado. Só o dourado do tema CLARO saiu do hex literal (#9c7a1f media
// 4,03:1 e reprovava AA; #8a6c1c é o mesmo tom um degrau mais escuro) — a
// checagem de contraste da seção 5 é quem justifica e defende esse desvio.
ok("acento do Estudo no escuro é o azul-esverdeado #2fa8a0", estudo.dark.accent === "#2fa8a0");
ok("acento do Estudo no claro é o azul-esverdeado #1f7d76", estudo.light.accent === "#1f7d76");
ok("acento do Operador no escuro é o dourado #d4af37", operador.dark.accent === "#d4af37");
ok("acento do Operador no claro é o dourado #8a6c1c", operador.light.accent === "#8a6c1c");
ok("Estudo e Operador têm acentos DIFERENTES no escuro", estudo.dark.accent !== operador.dark.accent);
ok("Estudo e Operador têm acentos DIFERENTES no claro", estudo.light.accent !== operador.light.accent);
ok("o âmbar da marca NÃO é acento de nenhum modo (v2 reserva pra marca)",
   ![estudo.dark.accent, estudo.light.accent, operador.dark.accent, operador.light.accent]
     .includes(BRAND.amber));
// O verde/rosa da marca são SINAL (compra/venda). Desde a paleta nova nenhum
// deles é também acento — antes o verde acumulava os dois papéis no Operador,
// e um botão primário verde dizia a mesma coisa que um "+R$" verde.
ok("nenhum acento reusa o verde ou o rosa de sinal",
   ![estudo.dark.accent, estudo.light.accent, operador.dark.accent, operador.light.accent]
     .some((a) => a === BRAND.green || a === BRAND.red));

// === 4. sinal de compra/venda ==============================================
ok("escuro: positive é o verde cru da marca", estudo.dark.positive === BRAND.green);
ok("escuro: negative é o rosa cru da marca", estudo.dark.negative === BRAND.red);
ok("escuro: Operador mantém o mesmo verde/rosa da marca",
   operador.dark.positive === BRAND.green && operador.dark.negative === BRAND.red);
// No claro os hex crus reprovam AA como texto — ver cabeçalho. O que se exige
// aqui é que continuem sendo VERDE e VERMELHO/ROSA (matiz da marca), não que
// sejam o hex cru.
const hue = (hex) => {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
  if (!d) return 0;
  let x = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return ((x * 60) + 360) % 360;
};
const perto = (a, b, tol) => Math.abs(a - b) <= tol || Math.abs(a - b) >= 360 - tol;
ok("claro: positive mantém a matiz verde da marca (±20°)",
   perto(hue(estudo.light.positive), hue(BRAND.green), 20));
ok("claro: negative mantém a matiz da marca (±20°)",
   perto(hue(estudo.light.negative), hue(BRAND.red), 20));

// === 5. contraste AA de tudo que é lido como TEXTO =========================
// Fundos de leitura: o card é a superfície onde o texto de fato assenta.
for (const [nome, esquema] of [["Estudo", estudo], ["Operador", operador]]) {
  for (const tema of ["dark", "light"]) {
    const p = esquema[tema];
    const fundo = p.bgCard;
    for (const token of ["textPrimary", "textMuted", "accent", "positive", "negative"]) {
      const razao = contrast(p[token], fundo);
      ok(`${nome}/${tema}: ${token} ${p[token]} sobre o card ${fundo} = ${razao.toFixed(2)}:1 (AA 4.5)`,
         razao >= 4.5);
    }
    // texto que fica EM CIMA do acento (CTA primária)
    const emCima = contrast(p.onAccent, p.accent);
    ok(`${nome}/${tema}: onAccent ${p.onAccent} sobre o acento ${p.accent} = ${emCima.toFixed(2)}:1 (AA 4.5)`,
       emCima >= 4.5);
  }
}

// FIX-C16 (REPORT-01): textFaint precisa passar AA nas TRÊS superfícies onde
// ele de fato renderiza (fonte/timestamp/disclaimer aparecem sobre bgBase,
// bgPanel E bgCard) — testar só o card (como os demais tokens acima) é a
// omissão que originou o bug: o pior caso é bgCard no escuro e bgPanel no
// claro, e um checador que olhasse só pra um dos dois deixaria o outro
// passar por engano.
for (const [nome, esquema] of [["Estudo", estudo], ["Operador", operador]]) {
  for (const tema of ["dark", "light"]) {
    const p = esquema[tema];
    for (const superficie of ["bgBase", "bgPanel", "bgCard"]) {
      const razao = contrast(p.textFaint, p[superficie]);
      ok(`${nome}/${tema}: textFaint ${p.textFaint} sobre ${superficie} ${p[superficie]} = ${razao.toFixed(2)}:1 (AA 4.5, C-16)`,
         razao >= 4.5);
    }
  }
}

// === 6. o símbolo estático não segue o modo ================================
// "Nunca recolorir os óculos fora do âmbar da marca" (Brand Book v2).
const logo = (() => {
  const i = src.indexOf("function LogoMark");
  return i < 0 ? "" : src.slice(i, src.indexOf("\n}", i));
})();
ok("LogoMark existe", logo.length > 0);
ok("LogoMark não lê a paleta do modo (usePalette)", !logo.includes("usePalette"));
ok("LogoMark não usa T.accent nem P.accent", !/[TP]\.accent/.test(logo));
ok("LogoMark pinta óculos/bico/selo com BRAND.amber", (logo.match(/BRAND\.amber/g) || []).length >= 4);
ok('o "+" do wordmark é o âmbar fixo da marca',
   /const PLUS_STYLE = \{ color: BRAND\.amber \}/.test(src));

console.log(fails ? `\n${fails} verificação(ões) falharam` : "\ntodas as verificações passaram");
process.exit(fails ? 1 : 0);
