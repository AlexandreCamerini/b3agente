// quick 261013-svo (2026-10-13) — guardião estático do painel de atenção/hoje da aba Posições,
// do filtro da lista e do gráfico do resultado em aberto na folha. Varre App.jsx como TEXTO.
// Cobre a forma (ordem, helpers puros, ausência de conta/data no componente, caminho de candles);
// layout no aparelho, gráfico nos dois modos e filtro tocável ficam para conferência manual.
// Reversão deliberada atualiza este guardião com nota (CLAUDE.md).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persist = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const evoSrc = readFileSync(join(here, "..", "src", "evolucaoPosicao.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(m.index, i);
}
const semComentarios = (b) => (b || "").split("\n").filter((l) => !/^\s*\/\//.test(l.trim())).join("\n").replace(/\{\/\*[\s\S]*?\*\/\}/g, "");
const conta = (t, s) => t.split(s).length - 1;

const tela = functionBody("CarteiraScreen") || "";
ok("CarteiraScreen localizada", tela.length > 2000);

// --- 1. CarteiraScreen: fiação e ordem --------------------------------------
for (const s of ["<PainelPosicoes", "resumoAtencao(", "filtroVigente(", "filtrarPorNivel(", "painelHoje(", 'A.go("evolucao")', "m.dayVal"]) {
  ok(`CarteiraScreen contém ${s}`, tela.includes(s));
}
{
  const iState = tela.indexOf("const [filtroNivel, setFiltroNivel] = useState(null);");
  const iRet = tela.indexOf("  return (\n");
  ok("useState(null) do filtroNivel antes do primeiro return", iState > 0 && iRet > iState);
  const ordem = ["PATRIMÔNIO TOTAL", "m.opcoesSemMarcacao > 0", "<PainelPosicoes", "concentracaoMaxima(", "<LinhaChamadaOpcoes", "<ChipsOrdenacaoPosicoes"].map((s) => tela.indexOf(s, iRet));
  ok("ordem da tela: hero < aviso de opções < painel < concentração < chamada de opções < chips", ordem.every((x, i) => x > 0 && (i === 0 || x > ordem[i - 1])));
}
ok("CarteiraScreen não renderiza <CapitalCurve", !tela.includes("<CapitalCurve"));
ok("CarteiraScreen sem nova chamada de portfolioMetrics (1 só)", conta(tela, "portfolioMetrics(") === 1);
ok("CarteiraScreen passa rotuloFonte: FONTE_LABEL", tela.includes("rotuloFonte: FONTE_LABEL"));
ok("lista e avulsas respeitam o filtro", tela.includes("ordenarLinhas(filtrarPorNivel(linhas, filtro), ordem)") && tela.includes("avulsas.map((t) =>") && tela.includes("avulsasVisiveis.has(t)"));

// --- 2. App.jsx inteiro ------------------------------------------------------
ok("<CapitalCurve exatamente 1x no App.jsx (DEDUP-01)", conta(src, "<CapitalCurve") === 1);
ok("portfolioMetrics( exatamente 7x no App.jsx", conta(src, "portfolioMetrics(") === 7);

const nomes = ["PainelPosicoes", "ContadoresAtencao", "BlocoHoje", "EvolucaoResultadoPosicao", "GraficoResultadoPosicao"];
const corpos = Object.fromEntries(nomes.map((n) => [n, semComentarios(functionBody(n))]));
for (const n of nomes) ok(`${n} localizado`, corpos[n].length > 200);

// --- 3. painel ---------------------------------------------------------------
const painel = corpos.PainelPosicoes + corpos.ContadoresAtencao + corpos.BlocoHoje;
for (const s of ["aria-pressed=", 'role="group"', "minHeight: 44", "quotesAt", "hoje_lote_hora", "tipoFonte"]) ok(`painel contém ${s}`, painel.includes(s));
ok("BlocoHoje não carrega fonte/horário por item (sem `source`)", !corpos.BlocoHoje.includes("source"));
ok("painel sem conta nem ordenação de mercado (ranking e % vêm do helper)", !/\.change\s*[-+*/]|sort\(|\.dayVal\s*[-+*/]|dayReturnPct\(/.test(painel));
ok("filtro 0 é nível válido: comparação com null, não truthiness", corpos.ContadoresAtencao.includes("filtro !== null"));

// --- 4. evolução --------------------------------------------------------------
const evo = corpos.EvolucaoResultadoPosicao;
for (const s of ["store.technicals(p.t, periodo)", "hojeBRT()", "reconstruirPosicao(", "periodoCandles(", "serieResultadoPosicao(", "evo_sem_dados", "evo_motivo_periodo", "!periodo", "evo_opcoes_fora", "tentar_de_novo", "[p.t, periodo, tentativa]", 'useState({ status: "carregando"']) {
  ok(`EvolucaoResultadoPosicao contém ${s}`, evo.includes(s));
}
for (const s of ['"idle"', "api.history", "/api/history", "<CapitalCurve"]) ok(`EvolucaoResultadoPosicao não contém ${s}`, !evo.includes(s));
ok("GraficoResultadoPosicao usa geometriaSerie( e role=\"img\"", corpos.GraficoResultadoPosicao.includes("geometriaSerie(") && corpos.GraficoResultadoPosicao.includes('role="img"'));
ok("GraficoResultadoPosicao sem Math. nem toFixed(", !/Math\.|toFixed\(/.test(corpos.GraficoResultadoPosicao));

// --- 5. CartaoPosicao ---------------------------------------------------------
{
  const cartao = functionBody("CartaoPosicao") || "";
  const a = cartao.indexOf("faceAcao}\n");
  const b = cartao.indexOf("naFolha && <EvolucaoResultadoPosicao");
  const c = cartao.indexOf("<BlocoBorisIA");
  ok("CartaoPosicao: gráfico só naFolha, depois da face e antes do BlocoBorisIA", a > 0 && b > a && c > b);
}

// --- 6. paridade de store por construção -------------------------------------
ok("technicals existe nos dois stores", conta(persist, "technicals") >= 2);
ok("persistence.js sem método history( / candles( novo", !/^\s+(async\s+)?(history|candles)\s*\(/m.test(persist));

// --- 7. âncora: dentro da fatia do transversal ------------------------------
{
  const ini = src.indexOf("function LinhaPernaAvulsa(");
  const fim = src.indexOf("function SeletorFace(");
  const reg = src.indexOf("function ReguaPlano(");
  const lco = src.indexOf("function LinhaChamadaOpcoes(");
  ok("âncoras da fatia existem", ini > 0 && fim > ini && reg > 0 && lco > fim);
  for (const n of nomes) {
    const i = src.indexOf(`function ${n}(`);
    ok(`${n} entre LinhaPernaAvulsa e SeletorFace (dentro da fatia do transversal)`, i > ini && i < fim && i > reg && i < lco);
  }
}

// --- 8. sem data/texto/conta nos componentes; fuso só no helper --------------
{
  const proibidos = ["new Date", "Date.", "Intl.", "toISOString", "getFullYear", ".slice(", ".split(", "padStart", "toFixed(", "Math.", ".join(", ".sort("];
  for (const n of nomes) {
    const achou = proibidos.filter((s) => corpos[n].includes(s));
    if (achou.length) console.log(`  ${n}:`, achou.join(" | "));
    ok(`${n} sem data/junção/conta (${proibidos.length} padrões)`, achou.length === 0);
  }
  ok('evolucaoPosicao.js resolve o fuso: timeZone: "America/Sao_Paulo"', evoSrc.includes('timeZone: "America/Sao_Paulo"'));
  const cab = src.slice(src.indexOf("// quick 261013-svo (2026-10-13) — painel de atenção"), src.indexOf("function SeletorFace("));
  ok("comentários das peças novas não falam em economia de brapi", !/econom[^\n]{0,60}brapi|brapi[^\n]{0,60}econom/i.test(cab));
}

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
