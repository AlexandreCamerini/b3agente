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
// Onda H2 (2026-10-08): itens 1, 6 e 8 reconciliados, ver NOTAs datadas.
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
// NOTA 2026-10-08 (quick 261008-w9i, Onda H2): a fonte do eixo agora vem de
// FONTE_EIXO=12 em px reais (viewBox = largura medida) e a cor/tamanho de texto do SVG
// passam por `style={{ fontSize: "12px" }}`; a exceção FONTE_MIN=11,5 deixou de existir.
// A regex abaixo captura também a forma de style, mantendo piso >= 11 e >= 4 ocorrências.
const FONTSIZE_STYLE_RE = /fontSize:\s*"([0-9]+(?:\.[0-9]+)?)px"/g;
let ms;
while ((ms = FONTSIZE_STYLE_RE.exec(fonte))) valoresFonte.push(parseFloat(ms[1]));
ok("existem ocorrências de fontSize no SVG (o teste não está vazio)", valoresFonte.length >= 4);
ok("toda fontSize resolvida é um número (literal ou constante existente)",
   valoresFonte.every((v) => typeof v === "number" && isFinite(v)));
ok("toda fontSize de <text> no SVG tem piso >= 11 (D-07, legibilidade em 375px)",
   valoresFonte.length > 0 && valoresFonte.every((v) => v >= 11));
ok("sanidade (H2): a regex de style pega fontSize: \"9px\" e o piso >= 11 o reprova",
   (() => {
     const r = /fontSize:\s*"([0-9]+(?:\.[0-9]+)?)px"/.exec('style={{ fontSize: "9px" }}');
     return !!r && parseFloat(r[1]) === 9 && !(parseFloat(r[1]) >= 11);
   })());
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
// Plano 37-04: a assinatura ganhou 3 props NOVAS e opcionais
// (dominio/segmentos/valorHoje, CHART-04/05) — D-08 continua provado pelo
// bloco acima (zero useState/onClick/...); esta asserção agora trava que as
// 4 props ORIGINAIS não mudaram de nome/ordem, não mais um total fechado.
ok("assinatura mantém as 4 props originais + as 3 novas opcionais do plano 37-04 (dominio, segmentos, valorHoje)",
   /export default function PayoffChart\(\{\s*estrutura,\s*emReais,\s*cp,\s*palette,\s*dominio,\s*segmentos,\s*valorHoje\s*\}\)/.test(bruto));
ok("sanidade: a regex de interatividade pega onClick real",
   /useState|onClick|onPointer|onTouch|onMouse/.test("const [x] = useState(0);"));

// ---- 5) nenhuma aritmética sobre os campos financeiros
const ARITMETICA_FINANCEIRA = /(net_cost|max_gain|max_loss)\s*[*/+-]\s*[\w.]/;
ok("nenhuma aritmética sobre net_cost/max_gain/max_loss (exibe, não calcula)",
   !ARITMETICA_FINANCEIRA.test(fonte));
ok("sanidade: a regex de aritmética pega uma conta inventada",
   ARITMETICA_FINANCEIRA.test("const dobro = e.max_gain * 2;"));

// ---- 6) a linha do breakeven nunca depende da mesma condição que suprime o texto
// NOTA 2026-10-08 (quick 261008-w9i, Onda H2): o bloco âncora `tipoMarca: "breakeven"` ...
// `cenarios.map((s, i)` deixou de existir. Agora o breakeven é um item de marcador
// (`traco: "2 4"`) entregue a `montarGeometria(` e desenhado por `<MarcadoresVerticais`
// (a <line> vertical vive em PayoffPrimitivas.jsx); a intenção — a linha do preço
// nunca fica atrás de guarda condicional — é provada nos dois arquivos. A asserção
// "supressão mira só o <text>" vira "nenhum texto de marcador no plot": não há mais
// supressão de texto porque o texto saiu do SVG (legenda numerada abaixo).
const iBe = fonte.indexOf('traco: "2 4"');
const itemBe = iBe >= 0 ? fonte.slice(Math.max(0, iBe - 200), iBe + 20) : "";
ok("o item de marcador do breakeven (traco: \"2 4\") foi localizado e alimenta montarGeometria(",
   iBe >= 0 && /preco:/.test(itemBe) && /montarGeometria\(/.test(fonte));
ok("<MarcadoresVerticais está presente sem guarda && / ? imediata antes dele",
   /<MarcadoresVerticais/.test(fonte)
   && !/&&\s*<MarcadoresVerticais/.test(fonte)
   && !/\?\s*<MarcadoresVerticais/.test(fonte));
const primFonte = semComentario(readFileSync(join(here, "..", "src", "opcoes", "PayoffPrimitivas.jsx"), "utf8"));
const iMv = primFonte.indexOf("export function MarcadoresVerticais");
const blocoMv = iMv >= 0 ? primFonte.slice(iMv, primFonte.indexOf("export function BadgeNumero")) : "";
ok("em MarcadoresVerticais a <line> vertical não tem guarda condicional imediata",
   /<line/.test(blocoMv) && !/&&\s*<line\s+x1=\{m\.x\}/.test(blocoMv) && !/\?\s*<line\s+x1=\{m\.x\}/.test(blocoMv));
const TEXTO_MARCADOR = /<text[\s\S]{0,200}(?:s\.name|opcoesHojePrefixoEixo|fmt\(item\.valor\))/;
ok("nenhum texto de marcador (valor/nome de cenário/hoje) dentro do plot", !TEXTO_MARCADOR.test(fonte));
ok("sanidade: a regex de guarda pega `mostrarTexto && <line`",
   /&&\s*<line/.test("{mostrarTexto && <line x1={x} />}"));
ok("sanidade: a regex de texto de marcador pega <text x={1}>{s.name}</text>",
   TEXTO_MARCADOR.test("<text x={1}>{s.name}</text>"));

// ---- 7) aria-label/<title> continuam completos (nada de dado se perde)
ok("aria-label e <title> usam a mesma `descricao` (leitor de tela não perde nada)",
   /aria-label=\{descricao\}/.test(bruto) && /<title>\{descricao\}<\/title>/.test(bruto));
ok("a `descricao` lista TODOS os breakevens, não só os visíveis na tela",
   /breakevens\.map/.test(fonte) && /Empata com o ativo em/.test(fonte));

// ---- 8) plano 37-04: eixo Y de 2 casas, strike no eixo, seta rotulada, Kicker
// importado. Cada asserção nova ganha sua companheira de SANIDADE, mesmo
// padrão do resto do arquivo (ver comentário no topo) — sem ela, um typo na
// regex faria o assert passar por vacuidade, pra sempre.
// NOTA 2026-10-08 (quick 261008-w9i, Onda H2): "PAD_E cresceu para 48" deixou de valer —
// a margem esquerda agora é calculada por `montarGeometria` a partir do maior rótulo do
// eixo Y (sem constante PAD_E fixa). A asserção mantém a intenção (o rótulo mais largo
// cabe) trocando "48 fixo" por "margem derivada, sem constante".
ok("margem esquerda vem de montarGeometria (sem constante PAD_E fixa)",
   !/\bPAD_E\b/.test(fonte) && /montarGeometria\(/.test(fonte));
ok("sanidade: valorConst(PAD_E) resolve o valor ANTIGO corretamente contra uma fonte engenheirada (prova que a regex funciona, não vacuidade)",
   valorConst("PAD_E", "const PAD_E = 10, PAD_D = 10;") === 10);

ok("chave opcoesEixoZeroRotulo em uso (rótulo do zero no eixo Y)",
   /opcoesEixoZeroRotulo/.test(fonte));
ok("sanidade: a regex de opcoesEixoZeroRotulo não casa com fonte sem a chave",
   !/opcoesEixoZeroRotulo/.test("const x = c.opcoesOutraCoisa;"));

// NOTA 2026-10-08 (quick 261008-w9i, Onda H2): o traço do strike deixou de ser
// `strokeDasharray` no PayoffChart; vira o campo `traco: "1 3"` do marcador (repassado
// à <line> por MarcadoresVerticais), ainda distinto do `traco: "2 4"` do breakeven.
ok('strike tem traço próprio traco: "1 3", distinto do breakeven traco: "2 4"',
   /traco: "1 3"/.test(fonte) && /traco: "2 4"/.test(fonte));
ok('sanidade: a regex de traco "1 3" não casa quando só "2 4" existe',
   !/traco: "1 3"/.test('{ preco: b, traco: "2 4" }'));

ok("opcoesPerdaIlimitadaCurta aparece junto de uma seta aria-hidden (CHART-03)",
   (() => {
     const idxCurta = fonte.indexOf("opcoesPerdaIlimitadaCurta");
     const blocoSeta = idxCurta >= 0 ? fonte.slice(Math.max(0, idxCurta - 200), idxCurta + 300) : "";
     return /aria-hidden/.test(blocoSeta) && /↓/.test(blocoSeta);
   })());
ok("sanidade: a checagem de proximidade falha quando opcoesPerdaIlimitadaCurta não está perto de seta nenhuma",
   (() => {
     const src = "const x = c.opcoesPerdaIlimitadaCurta; ".padEnd(250, ".") + "sem seta nenhuma aqui";
     const idx = src.indexOf("opcoesPerdaIlimitadaCurta");
     const bloco = idx >= 0 ? src.slice(Math.max(0, idx - 200), idx + 300) : "";
     return !(/aria-hidden/.test(bloco) && /↓/.test(bloco));
   })());

ok("Kicker é importado de ./uiOpcoes.jsx",
   /import\s*\{[^}]*\bKicker\b[^}]*\}\s*from\s*"\.\/uiOpcoes\.jsx"/.test(fonte));
ok("sanidade: a regex de import do Kicker não casa com import de outro módulo",
   !/import\s*\{[^}]*\bKicker\b[^}]*\}\s*from\s*"\.\/uiOpcoes\.jsx"/.test('import { Kicker } from "./outro.jsx";'));

console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
