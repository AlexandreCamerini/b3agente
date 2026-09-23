// Fase 38 (38-04) — guardião da tela de Glossário (KB-01).
//
// Parte 1 (Task 1): filtros puros de `glossario.js` — normalizarBusca,
// filtrarVerbetes, agruparPorFamilia. Comportamental, sem device nem build.
// Parte 2 (Task 2): estático sobre App.jsx/copy.js — tile em Perfil, rota de
// sub-tela, TelaGlossario, textos.
//
// Roda sem build: `node web/tests/test_glossario.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { normalizarBusca, filtrarVerbetes, agruparPorFamilia } from "../src/glossario.js";

const here = dirname(fileURLToPath(import.meta.url));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ============================================================ Parte 1 (comportamental)

// Fixture local (~14 verbetes) cobrindo: prefixo × contém × termo/id,
// acento/caixa, ordenação com empate, "sem limite" (7 casando "setup") e
// família desconhecida (para agruparPorFamilia).
const V = [
  { id: "ind-rsi", familia: "indicadores", titulo: "RSI (IFR) — Índice de Força Relativa", texto: "...", veja: [], termos: ["rsi", "ifr", "índice de força relativa", "sobrecomprado", "sobrevendido"] },
  { id: "ind-macd", familia: "indicadores", titulo: "MACD — Convergência e divergência de médias", texto: "...", veja: [], termos: ["macd"] },
  { id: "gatilho-armado", familia: "estados_app", titulo: "Gatilho armado", texto: "...", veja: [], termos: [] },
  { id: "gatilho-b", familia: "estados_app", titulo: "Gatilho de venda", texto: "...", veja: [], termos: [] },
  { id: "estado-gatilho", familia: "estados_app", titulo: "Estado: gatilho ativo", texto: "...", veja: [], termos: [] },
  { id: "estado-outro", familia: "estados_app", titulo: "Estado outro", texto: "...", veja: [], termos: ["gatilho"] },
  { id: "setup-1", familia: "setups", titulo: "Setup 1.2 IFR2", texto: "...", veja: [], termos: [] },
  { id: "setup-2", familia: "setups", titulo: "Setup 2 Bandas", texto: "...", veja: [], termos: [] },
  { id: "setup-3", familia: "setups", titulo: "Setup 3 Pullback", texto: "...", veja: [], termos: [] },
  { id: "setup-4", familia: "setups", titulo: "Setup 4 Rompimento", texto: "...", veja: [], termos: [] },
  { id: "setup-5", familia: "setups", titulo: "Setup 5 Reversão", texto: "...", veja: [], termos: [] },
  { id: "setup-6", familia: "setups", titulo: "Setup 6 Gap", texto: "...", veja: [], termos: [] },
  { id: "setup-7", familia: "setups", titulo: "Setup 7 Fechamento", texto: "...", veja: [], termos: [] },
  { id: "verbete-orfa", familia: "familia-desconhecida", titulo: "Órfã", texto: "...", veja: [], termos: [] },
];

ok("normalizarBusca remove acento/espaço nas pontas/caixa", normalizarBusca("  Índice ") === "indice");
ok("normalizarBusca(null) => string vazia", normalizarBusca(null) === "");

ok("filtrarVerbetes com termo vazio => []", filtrarVerbetes(V, "").length === 0);
ok("filtrarVerbetes com só espaços => []", filtrarVerbetes(V, "   ").length === 0);

const porRs = filtrarVerbetes(V, "rs");
ok("filtrarVerbetes('rs') acha o RSI pelo prefixo do título (casa durante a digitação)", porRs.some((v) => v.id === "ind-rsi"));

const porIfr = filtrarVerbetes(V, "ifr");
ok("filtrarVerbetes('ifr') acha o RSI pelo título", porIfr.some((v) => v.id === "ind-rsi"));

const porSobrevendido = filtrarVerbetes(V, "sobrevendido");
ok("filtrarVerbetes('sobrevendido') acha o RSI só pelos termos", porSobrevendido.length === 1 && porSobrevendido[0].id === "ind-rsi");

const porIndiceMin = filtrarVerbetes(V, "indice").map((v) => v.id);
const porIndiceMaiusc = filtrarVerbetes(V, "ÍNDICE").map((v) => v.id);
ok("filtrarVerbetes('indice') === filtrarVerbetes('ÍNDICE') (acento/caixa não mudam resultado)",
  JSON.stringify(porIndiceMin) === JSON.stringify(porIndiceMaiusc) && porIndiceMin.length > 0);

const porGat = filtrarVerbetes(V, "gat").map((v) => v.id);
ok("ordenação: título-prefixo > título-contém > termo/id; empate mantém a ordem do catálogo",
  JSON.stringify(porGat) === JSON.stringify(["gatilho-armado", "gatilho-b", "estado-gatilho", "estado-outro"]));

const porSetup = filtrarVerbetes(V, "setup");
ok("sem limite: fixture com 7 verbetes casando 'setup' devolve os 7", porSetup.length === 7);

ok("filtrarVerbetes não lança com '(['", (() => { try { filtrarVerbetes(V, "(["); return true; } catch { return false; } })());
ok("filtrarVerbetes não lança com '*'", (() => { try { filtrarVerbetes(V, "*"); return true; } catch { return false; } })());
ok("filtrarVerbetes não lança com '\\\\'", (() => { try { filtrarVerbetes(V, "\\"); return true; } catch { return false; } })());

const FAM = [
  { id: "setups", rotulo: "Setups" },
  { id: "indicadores", rotulo: "Indicadores" },
  { id: "estados_app", rotulo: "Estados e leituras do app" },
  { id: "mercado_b3", rotulo: "Mercado e B3" },
];
const grupos = agruparPorFamilia(V, FAM);
ok("agruparPorFamilia: só famílias com ≥1 verbete, na ORDEM de familias (mercado_b3 fica de fora)",
  grupos.map((g) => g.id).join(",") === "setups,indicadores,estados_app");
const totalAgrupado = grupos.reduce((n, g) => n + g.verbetes.length, 0);
ok("agruparPorFamilia: verbete de família desconhecida não entra em grupo nenhum",
  totalAgrupado === V.length - 1);

// ============================================================ Parte 2 (Task 2, estático)
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const copySrc = readFileSync(join(here, "..", "src", "copy.js"), "utf8");

const teloStart = app.indexOf("function TelaGlossario({ ctx })");
const hubStart = app.indexOf("function PerfilHub(");
ok("TelaGlossario existe", teloStart > -1);
ok("TelaGlossario vem ANTES de PerfilHub (fora da fatia do guardião de perfil)", teloStart > -1 && hubStart > -1 && teloStart < hubStart);

ok("PerfilHub abre o tile Glossário: onOpen(\"glossario\") + title=\"Glossário\"",
  app.includes('onOpen("glossario")') && app.includes('title="Glossário"'));
ok("onOpen(\"glossario\") aparece exatamente 1x", (app.match(/onOpen\("glossario"\)/g) || []).length === 1);

ok("roteamento: ramo perfilView === \"glossario\" monta TelaGlossario",
  /perfilView === "glossario"[\s\S]{0,120}<TelaGlossario ctx=\{ctx\} \/>/.test(app));

// A fatia começa no primeiro helper (LinhaVerbeteGlossario/GlossarioFamilia
// vêm ANTES de TelaGlossario, mas são parte da mesma feature) até PerfilHub.
const glossarioFeatStart = app.indexOf("function LinhaVerbeteGlossario(");
const telaGlossarioFatia = app.slice(glossarioFeatStart > -1 ? glossarioFeatStart : teloStart, hubStart);
ok("TelaGlossario usa filtrarVerbetes(", telaGlossarioFatia.includes("filtrarVerbetes("));
ok("TelaGlossario usa agruparPorFamilia(", telaGlossarioFatia.includes("agruparPorFamilia("));
ok("TelaGlossario abre o verbete via abrirVerbeteKb(", telaGlossarioFatia.includes("abrirVerbeteKb("));
ok("cabeçalho de família usa aria-expanded", telaGlossarioFatia.includes("aria-expanded"));
ok("estado de erro chama ctx.recarregarKb", telaGlossarioFatia.includes("ctx.recarregarKb"));

ok("App.jsx importa filtrarVerbetes/agruparPorFamilia de ./glossario.js",
  /import \{[^}]*filtrarVerbetes[^}]*agruparPorFamilia[^}]*\} from "\.\/glossario\.js"/.test(app));

// As 6 chaves glossario* precisam estar nos DOIS blocos de copy.js (2 ocorrências cada).
for (const chave of ["glossarioSub", "glossarioBuscaPlaceholder", "glossarioBuscaRotulo", "glossarioLimpar", "glossarioVazio", "glossarioErro"]) {
  const n = (copySrc.match(new RegExp(chave + ":", "g")) || []).length;
  ok(`copy.js: ${chave} presente nos dois blocos (2x)`, n === 2);
}
ok('copy.js: string exata "Nenhum verbete encontrado para" (D-05)', copySrc.includes("Nenhum verbete encontrado para"));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
