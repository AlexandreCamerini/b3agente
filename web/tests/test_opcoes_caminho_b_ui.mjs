// Fase 48 (2026-10-05, plano 48-13) — guardião transversal do caminho B de Opções
// (UI-SPEC: Estados, Acessibilidade, Color). Guardião não se apaga: reversão
// deliberada atualiza este arquivo com nota.
//
// REPROVA se, nos 7 .jsx do caminho B (HubOpcoes, ObjetivoAtivo, EscadaObjetivo,
// GraficoResultado, MatrizVencimentos, ConfirmarEstrutura, TermoOpcoes) ou em
// fluxoEstilo.js:
//  - aparecer `transition`/`animation` literal fora dos helpers de fluxoEstilo, ou
//    os helpers não devolverem {} com movimento reduzido;
//  - houver `minHeight` numérico < 44, ou CTA/célula/degrau abaixo do contrato;
//  - faltar radiogroup/aria-checked/setas, role="img"+aria, <details>/<table>/range;
//  - o termo clicável perder "O que é" sr-only ou o SUBLINHADO importado;
//  - surgir "Watchlist" ou `ctx.data.watchlist`;
//  - ausente virar 0 (`|| 0` / `?? 0`) em campo financeiro (T-48-46);
//  - faltar estado obrigatório (princípio 9) ou o aviso de dinheiro virtual;
//  - par de token de texto < 4,5:1 ou gráfico/borda < 3:1 em claro/escuro x estudo/operador.
// Prova negativa: inserir `transition: "all 1s"` em qualquer .jsx faz o item 1
// falhar; trocar `minHeight: "44px"` por "40px" faz o item 2 falhar; `?? 0` em
// `perdaMaxima` faz o item 7 falhar (as regexes abaixo são exercitadas em memória
// no bloco "prova negativa" ao final).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { transicaoTela, transicaoDegrau } from "../src/opcoes/fluxoEstilo.js";

const here = dirname(fileURLToPath(import.meta.url));
const src = (...p) => readFileSync(join(here, "..", "src", ...p), "utf8");
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const semComentarios = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:"'`\\])\/\/[^\n]*/g, "$1");

const NOMES = ["HubOpcoes", "ObjetivoAtivo", "EscadaObjetivo", "GraficoResultado", "MatrizVencimentos", "ConfirmarEstrutura", "TermoOpcoes"];
const raw = {}; const F = {};
for (const n of NOMES) { raw[n] = src("opcoes", n + ".jsx"); F[n] = semComentarios(raw[n]); }
const fluxo = src("opcoes", "fluxoEstilo.js");
const opcoesScreen = semComentarios(src("opcoes", "OpcoesScreen.jsx"));
const app = src("App.jsx");
const copy = src("copy.js");
const todos = NOMES.map((n) => F[n]).join("\n");

// ---- 1. reduced-motion ------------------------------------------------------
const reTrans = (s) => /\btransition\s*:/.test(s) || /\banimation\s*:/.test(s) || /\banimation[A-Z]\w*\s*:/.test(s);
for (const n of NOMES) ok(`1. ${n}: sem transition/animation literal`, !reTrans(F[n]));
ok("1. helpers com movimento reduzido devolvem {} (sem transition)",
  Object.keys(transicaoTela(true)).length === 0 && Object.keys(transicaoDegrau(true)).length === 0);
ok("1. helpers sem redução devolvem transition só de opacity/transform",
  /opacity/.test(transicaoTela(false).transition) && /transform/.test(transicaoTela(false).transition) && !/\ball\b/.test(transicaoTela(false).transition)
  && /opacity/.test(transicaoDegrau(false).transition) && !/\ball\b/.test(transicaoDegrau(false).transition));
ok("1. componentes usam os helpers (transicaoTela/transicaoDegrau)", /transicaoTela\(/.test(todos) && /transicaoDegrau\(/.test(todos));

// ---- 2. alvos de toque ------------------------------------------------------
const CONST = { ALVO_MIN: 44, CTA_MIN: 48, CELULA_MIN: 52 };
const minHeights = [];
for (const n of NOMES) {
  for (const m of F[n].matchAll(/minHeight:\s*(?:"(\d+)px"|(\d+)(?![\w.])|(ALVO_MIN|CTA_MIN|CELULA_MIN)\s*\+\s*"px")/g)) {
    minHeights.push([n, m[3] ? CONST[m[3]] : Number(m[1] || m[2]), m[0]]);
  }
}
ok(`2. há minHeight medido nos componentes (${minHeights.length})`, minHeights.length >= 15);
// exceção declarada: checkbox nativo de aceite (ConfirmarEstrutura) fica dentro de
// <label> com o texto clicável; o alvo é o label inteiro, não o input de 20px.
const abaixo = minHeights.filter(([n, v, t]) => v < 44 && !(n === "ConfirmarEstrutura" && /minHeight:\s*"20px"/.test(t)));
ok("2. nenhum minHeight < 44 (exceto o input do checkbox, dentro de <label>)" + (abaixo.length ? " -> " + JSON.stringify(abaixo) : ""), abaixo.length === 0);
ok("2. CTAs principais = 48 (CTA_MIN em fluxoEstilo e uso em Escada e Confirmar)", /CTA_MIN\s*=\s*48/.test(fluxo) && /minHeight:\s*CTA_MIN/.test(F.EscadaObjetivo) && /minHeight:\s*CTA_MIN/.test(F.ConfirmarEstrutura));
ok("2. ALVO_MIN = 44", /ALVO_MIN\s*=\s*44/.test(fluxo));
ok("2. células da matriz = 52", /CELULA_MIN\s*=\s*52/.test(F.MatrizVencimentos) && /minHeight:\s*CELULA_MIN/.test(F.MatrizVencimentos));
ok("2. degrau (Escada), objetivo (ObjetivoAtivo) e card (Hub) = 64", /minHeight:\s*"64px"|minHeight:\s*64/.test(F.EscadaObjetivo) && /minHeight:\s*64/.test(F.ObjetivoAtivo) && /minHeight:\s*64/.test(F.HubOpcoes));
ok("2. checkbox de aceite está dentro de <label> (alvo = linha toda)", /<label[^>]*>\s*<input type="checkbox"/.test(F.ConfirmarEstrutura));

// ---- 3. EscadaObjetivo: radiogroup -------------------------------------------
ok('3. role="radiogroup"', /role="radiogroup"/.test(F.EscadaObjetivo));
ok('3. role="radio" + aria-checked', /role="radio"/.test(F.EscadaObjetivo) && /aria-checked=/.test(F.EscadaObjetivo));
ok("3. roving tabindex (0 no focável, -1 nos demais)", /tabIndex=\{[^}]*\?\s*0\s*:\s*-1\}/.test(F.EscadaObjetivo));
ok("3. ArrowUp/ArrowDown tratados", /ArrowUp/.test(F.EscadaObjetivo) && /ArrowDown/.test(F.EscadaObjetivo));
ok("3. degrau ausente é aria-disabled (motivo escrito, nunca oculto)", /aria-disabled="true"/.test(F.EscadaObjetivo) && /degrau_ausente/.test(F.EscadaObjetivo));
ok('3. chips de vencimento com aria-pressed', /aria-pressed=\{ativo\}/.test(F.EscadaObjetivo));

// ---- 4. GraficoResultado ------------------------------------------------------
const G = F.GraficoResultado;
ok('4. svg role="img"', /<svg[^>]*role="img"/.test(G));
ok("4. aria-label vem de grafico.aria (nunca montado no componente)", /g\.aria/.test(G) && /aria-label=\{ariaTxt\}/.test(G));
ok("4. <details> + <table> alternativa", /<details/.test(G) && /<table/.test(G));
ok('4. input type="range" (e se...)', /<input[^>]*type="range"/.test(G));
ok('4. marcadores aria-hidden (rótulo vai pela legenda/tabela)', /<g[^>]*aria-hidden="true"/.test(G));
ok("4. título/subtítulo e legenda por chaves (rótulo além da cor)", /grafico_subtitulo/.test(G) && /legenda\.map\(/.test(G));

// ---- 5. TermoOpcoes ------------------------------------------------------------
ok('5. sr-only "O que é "', /"O que é "\s*\+/.test(F.TermoOpcoes) && /SR_ONLY/.test(F.TermoOpcoes));
ok("5. importa SUBLINHADO de entendimento.jsx", /import\s*\{[^}]*SUBLINHADO[^}]*\}\s*from\s*"\.\.\/entendimento\.jsx"/.test(F.TermoOpcoes));
ok("5. termos inline têm role=button + tabIndex + teclado", /role="button" tabIndex=\{0\}/.test(F.TermoOpcoes) && /onKeyDown/.test(F.TermoOpcoes));

// ---- 6. sem "Watchlist" ---------------------------------------------------------
for (const n of NOMES) ok(`6. ${n}: sem "Watchlist" nem data.watchlist`, !/watchlist/i.test(F[n]));

// ---- 7. ausente nunca vira zero -------------------------------------------------
const CAMPOS = "perdaMaxima|ganhoMaximo|premio\\w*|liquido\\w*|equilibrio|comEstrutura|soAcoes|perdaTotal|ganhoTotal|custo\\w*";
const reZero = new RegExp(`\\b(${CAMPOS})\\b[^;\\n]{0,40}(\\|\\||\\?\\?)\\s*0\\b`);
for (const n of NOMES) ok(`7. ${n}: sem "|| 0"/"?? 0" em campo financeiro`, !reZero.test(F[n]));
ok("7. nenhum arquivo usa `|| 0`/`?? 0` em preço/valor (varredura geral)", !/\b(preco|valor|premio|strike|spot|qty)\w*\s*(\|\||\?\?)\s*0\b/i.test(todos));
ok('7. existe fallback "—" nos componentes', NOMES.filter((n) => /"—"/.test(F[n])).length >= 4);
ok('7. "matriz_sem_dado" é "—" no copy', /matriz_sem_dado:\s*"—"/.test(copy));

// ---- 8. estados obrigatórios (princípio 9) ---------------------------------------
const chavesCopy = ["carregando", "erro_fonte", "tentar_de_novo", "hub_vazio_titulo", "hub_vazio_corpo", "hub_vazio_cta", "sem_estrutura", "cota_esgotada", "mercado_fechado", "objetivo_indisponivel", "ordem_rejeitada", "estudo_nao_executa", "toast_executada", "dado_insuficiente", "aviso_virtual"];
for (const k of chavesCopy) ok(`8. copy.js opcoesEscada tem "${k}"`, new RegExp(`\\b${k}:\\s*"`).test(copy));
const usada = (k) => new RegExp(`["']${k}["']`).test(todos) || new RegExp(`["']${k}["']`).test(opcoesScreen);
for (const k of ["carregando", "erro_fonte", "tentar_de_novo", "hub_vazio_titulo", "sem_estrutura", "cota_esgotada", "mercado_fechado", "objetivo_indisponivel", "ordem_rejeitada", "estudo_nao_executa"]) ok(`8. estado "${k}" é renderizado`, usada(k));
ok('8. toast "escada" no App.jsx (origem === "escada")', /opts\.origem === "escada"[\s\S]{0,80}toast_executada/.test(app));
ok('8. C-14: nenhuma chave de fill parcial nos componentes do caminho B', !/parcial/i.test(todos) && !/ordem_parcial|fill_parcial|parcialmente/i.test(copy.slice(copy.indexOf("opcoesEscada: {"), copy.indexOf("opcoesEscada: {") + 12000)));

// ---- 9. aviso virtual, live regions, alert ----------------------------------------
ok('9. aviso_virtual no HubOpcoes e no OpcoesScreen', /"aviso_virtual"/.test(F.HubOpcoes) && /"aviso_virtual"/.test(opcoesScreen));
ok('9. aviso_virtual também no objetivo, escada e confirmar', ["ObjetivoAtivo", "EscadaObjetivo", "ConfirmarEstrutura"].every((n) => /"aviso_virtual"/.test(F[n])));
ok('9. frase de risco com aria-live="polite"', /<p aria-live="polite"/.test(F.EscadaObjetivo));
for (const n of ["HubOpcoes", "ObjetivoAtivo", "EscadaObjetivo", "ConfirmarEstrutura"]) ok(`9. ${n}: erro com role="alert"`, /role="alert"/.test(F[n]));
ok('9. carregando com role="status"', ["HubOpcoes", "ObjetivoAtivo", "EscadaObjetivo"].every((n) => /role="status"/.test(F[n])));

// ---- 10. contraste AA ---------------------------------------------------------------
function objectBody(decl, s) {
  const i = s.indexOf(decl); if (i < 0) return null;
  let d = 0, st = s.indexOf("{", i), j = st;
  for (; j < s.length; j++) { if (s[j] === "{") d++; else if (s[j] === "}") { d--; if (d === 0) break; } }
  return s.slice(st, j + 1);
}
function scheme(block, name) {
  if (!block) return {};
  const i = block.indexOf(name + ": {"); if (i < 0) return {};
  const body = objectBody(name + ": {", block.slice(i - 0)) || "";
  const out = {};
  for (const m of body.matchAll(/(\w+):\s*"(#[0-9a-fA-F]{6})"/g)) out[m[1]] = m[2].toLowerCase();
  return out;
}
const pal = objectBody("const PALETTE = ", app), mod = objectBody("const MODE_OPERADOR = ", app), brandB = objectBody("const BRAND = ", app) || "";
const brand = {}; for (const m of brandB.matchAll(/(\w+):\s*"(#[0-9a-fA-F]{6})"/g)) brand[m[1]] = m[2].toLowerCase();
const base = { dark: scheme(pal, "dark"), light: scheme(pal, "light") };
for (const t of ["dark", "light"]) for (const k of ["positive", "negative"]) {
  if (!base[t][k]) { const ref = new RegExp(`${k}:\\s*BRAND\\.(\\w+)`).exec(pal); if (ref && brand[ref[1]]) base[t][k] = brand[ref[1]]; }
}
const over = { dark: scheme(mod, "dark"), light: scheme(mod, "light") };
const combos = {
  "dark · estudo": base.dark, "dark · operador": { ...base.dark, ...over.dark },
  "light · estudo": base.light, "light · operador": { ...base.light, ...over.light },
};
const lin = (x) => (x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4));
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const lum = ([r, g, b]) => 0.2126 * lin(r / 255) + 0.7152 * lin(g / 255) + 0.0722 * lin(b / 255);
const ratio = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
const mix = (fg, a, bg) => { const f = hex(fg), b = hex(bg); return f.map((v, i) => v * a + b[i] * (1 - a)); };
// Texto: tokens neutros + accent medidos em TODAS as combinações (>= 4,5).
// positive/negative/warn como cor de TEXTO sobre bgPanel (e positive/negative sobre
// bgBase) ficam abaixo de AA no tema claro do PALETTE global (dívida legada, ver
// test_estrutura_card_contraste.mjs; UI-SPEC "Zero cor nova" proíbe tocar o token).
// Por isso o guardião trava o USO: esses tokens não são cor de texto de forma
// nenhuma (exceto warn do selo "atrasado" sobre bgBase, medido); o texto que carrega
// o aviso usa textPrimary. As medidas viram linhas "info" (não assertadas).
const TEXTO = ["textPrimary", "textSecondary", "textMuted"];
const FUNDOS = ["bgPanel", "bgBase"];
const sobre = (c, tint, fundo) => { const m = /rgba\(([^)]+)\)/.exec(c[tint]); const [r, g, b, a] = m[1].split(",").map(Number); const bg = hex(c[fundo]); return [r, g, b].map((v, i) => v * a + bg[i] * (1 - a)); };
for (const [nome, c] of Object.entries(combos)) {
  ok(`10. ${nome}: tokens resolvidos`, [...TEXTO, ...FUNDOS, "onAccent", "accent", "warn", "positive", "negative"].every((k) => /^#[0-9a-f]{6}$/.test(c[k] || "")));
  for (const f of FUNDOS) for (const t of TEXTO) {
    const r = ratio(lum(hex(c[t])), lum(hex(c[f])));
    ok(`10. ${nome}: ${t}/${f} = ${r.toFixed(2)} >= 4.5`, r >= 4.5);
  }
  const rA = ratio(lum(hex(c.accent)), lum(hex(c.bgBase)));
  ok(`10. ${nome}: accent(texto de link/botão)/bgBase = ${rA.toFixed(2)} >= 4.5`, rA >= 4.5);
  if (c.accentTint10) {
    const rT = ratio(lum(hex(c.accent)), lum(sobre(c, "accentTint10", "bgBase")));
    ok(`10. ${nome}: accent/accentTint10 sobre bgBase (chip ativo) = ${rT.toFixed(2)} >= 4.5`, rT >= 4.5);
  }
  const rW = ratio(lum(hex(c.warn)), lum(hex(c.bgBase)));
  ok(`10. ${nome}: warn(selo "atrasado")/bgBase = ${rW.toFixed(2)} >= 4.5`, rW >= 4.5);
  const rC = ratio(lum(hex(c.onAccent)), lum(hex(c.accent)));
  ok(`10. ${nome}: onAccent/accent (CTA) = ${rC.toFixed(2)} >= 4.5`, rC >= 4.5);
  // gráficos / bordas / marcadores (>= 3,0): token cheio sobre o fundo. O
  // preenchimento usa OPACIDADE 0.2 (tinta decorativa; a informação vai pela
  // linha accent, pelos marcadores com rótulo, pela legenda e pela tabela).
  for (const f of FUNDOS) for (const k of ["accent", "positive", "negative", "warn"]) {
    const r = ratio(lum(hex(c[k])), lum(hex(c[f])));
    ok(`10. ${nome}: gráfico/borda ${k}/${f} = ${r.toFixed(2)} >= 3.0`, r >= 3.0);
  }
  for (const f of FUNDOS) for (const k of ["positive", "negative", "warn"]) {
    const r = ratio(lum(hex(c[k])), lum(hex(c[f])));
    if (r < 4.5) console.log(`info ${nome}: ${k}/${f} = ${r.toFixed(2)} < 4.5 (não usado como texto)`);
  }
}
ok("10. positive/negative nunca são cor de texto nos componentes", !/color:\s*T\.(positive|negative)\b/.test(todos));
ok("10. warn só é cor de texto no selo/aviso 'atrasado' do HubOpcoes (sobre bgBase)",
  NOMES.filter((n) => n !== "HubOpcoes").every((n) => !/color:\s*T\.warn\b/.test(F[n])));
ok("10. OPACIDADE do preenchimento é a mesma para ganho e perda", /OPACIDADE = 0\.2/.test(G) && (G.match(/fillOpacity=\{OPACIDADE\}/g) || []).length === 2);

// ---- prova negativa em memória -------------------------------------------------------
ok("PN. regex de transition acusa injeção", reTrans('style={{ transition: "all 1s" }}'));
ok("PN. regex de zero acusa `perdaMaxima ?? 0`", reZero.test("const x = c.perdaMaxima ?? 0;"));
ok("PN. regex de zero NÃO acusa `qtd ?? 0` (campo não financeiro)", !reZero.test("const x = c.qtd ?? 0;"));

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\nOK");
