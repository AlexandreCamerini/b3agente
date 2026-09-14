// Plano 31-03 (Fase 31, varredura de oportunidades de opções) — guardião da
// legibilidade mobile de `PayoffChart.jsx` (D-07) e do fence D-08.
//
// Este arquivo tranca a CLASSE de erro (regressão de legibilidade em 375px e
// reabertura do fence "sem overlay, sem interatividade"), não a instância —
// mesmo padrão dos outros guardiões estáticos de `web/tests/*.mjs`
// (`readFileSync` do fonte + `ok(nome, cond)` + `process.exit(fails ? 1 : 0)`).
//
// O que se prova, uma regra por item do <behavior> do plano:
//  1. nenhuma `fontSize` de `<text>` do SVG fica abaixo de 11 — literal
//     (`fontSize="N"`) OU via constante nomeada (`fontSize={FONTE_MIN}`),
//     resolvendo o valor da constante no próprio fonte;
//  2. o SVG continua responsivo: `preserveAspectRatio="xMidYMid meet"` e
//     `width: "100%"` presentes, nenhum atributo `width=`/`height=` fixo
//     (px) na tag `<svg>`;
//  3. o wrapper `caixa` ganhou `minWidth: 0` (contenção em grid/flex estreito
//     — sem isso o SVG estoura a coluna em 375px);
//  4. zero interatividade (D-08): nenhum `useState`/`onClick`/`onPointer`/
//     `onTouch`/`onMouse`, e a assinatura continua com as 4 props de sempre;
//  5. nenhuma aritmética sobre os campos financeiros (`net_cost`/`max_gain`/
//     `max_loss`) — o componente EXIBE o que o backend calculou, nunca soma/
//     multiplica/divide em cima;
//  6. a supressão de rótulo sobreposto (breakeven) atinge só o `<text>` — a
//     `<line>` que marca o preço nunca fica atrás de `&&`/`?` condicional;
//  7. `aria-label`/`<title>` continuam citando TODOS os breakevens — suprimir
//     texto ilegível na tela não pode podar a descrição acessível.
//
// Cada regex carrega uma asserção de SANIDADE: sem ela, um typo (ou um
// Unicode diferente) faria o assert passar por vacuidade, para sempre.
//
// Roda sem build: `node web/tests/test_payoff_responsivo.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const caminho = join(here, "..", "src", "opcoes", "PayoffChart.jsx");
const bruto = readFileSync(caminho, "utf8");

// Sem comentários: eles citam os mesmos termos ao EXPLICAR as decisões (o
// próprio arquivo comenta "fontSize=\"9.5\" era 9,5px reais na tela" ao
// justificar o piso) — contá-los faria o guardião se auto-invalidar.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const fonte = semComentario(bruto);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- helper: resolve o valor de uma constante `const NOME = N;` no fonte
function valorConst(nome, src) {
  const m = src.match(new RegExp("\\b" + nome + "\\s*=\\s*([0-9]+(?:\\.[0-9]+)?)"));
  return m ? parseFloat(m[1]) : null;
}

// ---- 1) piso de legibilidade: toda fontSize (literal ou via constante) >= 11
const FONTSIZE_RE = /fontSize=(?:"([0-9]+(?:\.[0-9]+)?)"|\{([A-Za-z_][A-Za-z0-9_]*)\})/g;
const valoresFonte = [];
let m;
while ((m = FONTSIZE_RE.exec(fonte))) {
  valoresFonte.push(m[1] != null ? parseFloat(m[1]) : valorConst(m[2], fonte));
}
ok("existem ocorrências de fontSize no SVG (o teste não está vazio)", valoresFonte.length >= 4);
ok("toda fontSize resolvida é um número (literal ou constante existente)",
   valoresFonte.every((v) => typeof v === "number" && isFinite(v)));
ok("toda fontSize de <text> no SVG tem piso >= 11 (D-07, legibilidade em 375px)",
   valoresFonte.length > 0 && valoresFonte.every((v) => v >= 11));
ok("sanidade: a regex pega fontSize=\"9.5\" literal E resolve fontSize={CONST}",
   (() => {
     const lit = /fontSize=(?:"([0-9]+(?:\.[0-9]+)?)"|\{([A-Za-z_][A-Za-z0-9_]*)\})/.exec('fontSize="9.5"');
     const viaConst = valorConst("FONTE_MIN", "const FONTE_MIN = 11.5;");
     return lit && parseFloat(lit[1]) === 9.5 && viaConst === 11.5;
   })());

// ---- 2) SVG continua responsivo, sem largura/altura fixa em px
const tagSvg = (fonte.match(/<svg[\s\S]*?>/) || [""])[0];
ok("<svg> mantém preserveAspectRatio=\"xMidYMid meet\"",
   /preserveAspectRatio="xMidYMid meet"/.test(tagSvg));
ok("<svg> mantém width: \"100%\" no style (responsivo)",
   /width:\s*"100%"/.test(tagSvg));
ok("<svg> não ganhou width=/height= fixo em px (perda de responsividade)",
   !/\swidth=\{?\d/.test(tagSvg) && !/\sheight=\{?\d/.test(tagSvg));
ok("sanidade: a regex de largura fixa pega width={320}",
   /\swidth=\{?\d/.test("<svg width={320}>"));

// ---- 3) contenção do wrapper em container estreito
ok("wrapper `caixa` ganhou minWidth: 0 (não estoura coluna grid em 375px)",
   /minWidth:\s*0/.test(fonte));

// ---- 4) fence D-08: zero interatividade, contrato de props inalterado
ok("D-08: zero useState/onClick/onPointer/onTouch/onMouse no componente",
   !/useState|onClick|onPointer|onTouch|onMouse/.test(fonte));
ok("assinatura continua com as 4 props de sempre (estrutura, emReais, cp, palette)",
   /export default function PayoffChart\(\{\s*estrutura,\s*emReais,\s*cp,\s*palette\s*\}\)/.test(bruto));
ok("sanidade: a regex de interatividade pega onClick real",
   /useState|onClick|onPointer|onTouch|onMouse/.test("const [x] = useState(0);"));

// ---- 5) nenhuma aritmética sobre os campos financeiros
const ARITMETICA_FINANCEIRA = /(net_cost|max_gain|max_loss)\s*[*/+-]\s*[\w.]/;
ok("nenhuma aritmética sobre net_cost/max_gain/max_loss (exibe, não calcula)",
   !ARITMETICA_FINANCEIRA.test(fonte));
ok("sanidade: a regex de aritmética pega uma conta inventada",
   ARITMETICA_FINANCEIRA.test("const dobro = e.max_gain * 2;"));

// ---- 6) a linha do breakeven nunca depende da mesma condição que suprime o texto
// Marcadores de CÓDIGO (não de comentário — o comentário "3. breakevens" /
// "4. cenários" é removido por `semComentario`): o bloco de breakevens vai
// da ordenação de `marcas` até o início do `.map` dos cenários.
const iniBe = fonte.indexOf("[...marcas].sort");
const iniCen = fonte.indexOf("cenarios.map((s, i)");
const blocoBreakeven = iniBe >= 0 && iniCen > iniBe ? fonte.slice(iniBe, iniCen) : "";
ok("o bloco de breakevens foi localizado no fonte", blocoBreakeven.length > 0);
ok("a <line> do breakeven não tem guarda condicional imediata (&&/`?` antes dela)",
   /<line/.test(blocoBreakeven)
   && !/&&\s*<line/.test(blocoBreakeven)
   && !/\?\s*<line/.test(blocoBreakeven));
ok("a supressão condicional existe e mira só o <text>",
   /mostrarTexto \? \(/.test(blocoBreakeven) && /<text/.test(blocoBreakeven));
ok("sanidade: a regex de guarda pega `mostrarTexto && <line`",
   /&&\s*<line/.test("{mostrarTexto && <line x1={x} />}"));

// ---- 7) aria-label/<title> continuam completos (nada de dado se perde)
ok("aria-label e <title> usam a mesma `descricao` (leitor de tela não perde nada)",
   /aria-label=\{descricao\}/.test(bruto) && /<title>\{descricao\}<\/title>/.test(bruto));
ok("a `descricao` lista TODOS os breakevens, não só os visíveis na tela",
   /breakevens\.map/.test(fonte) && /Empata com o ativo em/.test(fonte));

console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
