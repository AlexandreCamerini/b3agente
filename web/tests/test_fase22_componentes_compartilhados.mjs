// Guardião ÚNICO da Fase 22 (v1.5, Redesenho de UI) — componentes
// compartilhados (trilho, ícones, mascote).
//
// Seção A (SYS-01, plano 22-01): padrão único de rolagem horizontal. Os 4
// trilhos de App.jsx (HERO-CARROSSEL, filtro MODELO DE ANÁLISE, tira de
// OportunidadesOpcoes, linha de candidatos de PropostaDaPosicao) passam a
// chamar os helpers de módulo `carouselTrackStyle`/`carouselItemStyle` em
// vez de definir `overflowX`/scroll-snap inline cada um por conta própria.
//
// Este arquivo vai ser ESTENDIDO pelos planos 22-02 e 22-03 com:
//   Seção B (SYS-02, ícones SVG) — plano 22-02
//   Seção C (SYS-02, Radar + tier dot + varredura de emoji zero) — plano 22-02 ou 22-03
//   Seção D (SYS-03, sombra do PetFab) — plano 22-03
// O próximo agente que tratar SYS-02/SYS-03 deve ACRESCENTAR seções a este
// MESMO arquivo, não criar um arquivo paralelo.
//
// Roda sem build: `node web/tests/test_fase22_componentes_compartilhados.mjs`.
// Padrão da casa: regex sobre App.jsx lido com readFileSync — o módulo
// importa @capacitor/core e não é importável fora do build (ver
// test_fase21_dedup_consolidacao.mjs, test_fase3_c19_card_status.mjs).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// --- Seção A — SYS-01 (plano 22-01): padrão único de carrossel horizontal --

// Isolamento por marcador textual estável, padrão da casa (test_fase3_c19_
// card_status.mjs / test_fase21_dedup_consolidacao.mjs): do início do
// marcador até o próximo marcador do mesmo tipo. Aborta com mensagem
// explícita (nunca passa em silêncio) se o marcador sumir.

function isolarFuncao(nome) {
  const marcador = `function ${nome}(`;
  const inicio = app.indexOf(marcador);
  if (inicio < 0) {
    console.error(`FALHOU: ${marcador} não encontrado em App.jsx — guardião não pode isolar o componente`);
    process.exit(1);
  }
  const fim = app.indexOf("\nfunction ", inicio + 10);
  return app.slice(inicio, fim > inicio ? fim : undefined);
}

const evolucaoScreen = isolarFuncao("EvolucaoScreen");
const oportunidadesOpcoes = isolarFuncao("OportunidadesOpcoes");
const propostaDaPosicao = isolarFuncao("PropostaDaPosicao");
const candidatoOpcao = isolarFuncao("CandidatoOpcao");

// TECH_MODELS não vive dentro de uma função nomeada própria — isolar pelo
// próprio marcador do container + o `.map()` que segue, com um recorte
// generoso (algumas linhas antes e depois) para cobrir container e item.
const idxTechModels = app.indexOf("TECH_MODELS.map(");
if (idxTechModels < 0) {
  console.error("FALHOU: TECH_MODELS.map( não encontrado em App.jsx — guardião não pode isolar o filtro MODELO DE ANÁLISE");
  process.exit(1);
}
// A abertura do container fica na linha imediatamente anterior ao .map() —
// recuar até o início dessa linha (o `<div style={carouselTrackStyle...`).
const inicioContainerTechModels = app.lastIndexOf("\n", app.lastIndexOf("\n", idxTechModels) - 1) + 1;
const fimTechModels = app.indexOf("</div>", idxTechModels + "TECH_MODELS.map(".length);
const techModelsBloco = app.slice(inicioContainerTechModels, fimTechModels > 0 ? fimTechModels : idxTechModels + 800);

// --- 1. carouselTrackStyle existe -------------------------------------------

const idxTrackDef = app.indexOf("const carouselTrackStyle");
ok("existe `const carouselTrackStyle`", idxTrackDef >= 0);
if (idxTrackDef >= 0) {
  const fimTrackDef = app.indexOf("\nconst ", idxTrackDef + 10);
  const trackDefBloco = app.slice(idxTrackDef, fimTrackDef > idxTrackDef ? fimTrackDef : idxTrackDef + 400);
  ok("`carouselTrackStyle` contém `overflowX: \"auto\"`", trackDefBloco.includes('overflowX: "auto"'));
  ok("`carouselTrackStyle` contém `display: \"flex\"`", trackDefBloco.includes('display: "flex"'));
  ok("`carouselTrackStyle` contém `scrollSnapType: \"x proximity\"`", trackDefBloco.includes('scrollSnapType: "x proximity"'));
  ok("`carouselTrackStyle` contém `WebkitOverflowScrolling: \"touch\"`", trackDefBloco.includes('WebkitOverflowScrolling: "touch"'));
} else {
  ok("`carouselTrackStyle` contém `overflowX: \"auto\"`", false);
  ok("`carouselTrackStyle` contém `display: \"flex\"`", false);
  ok("`carouselTrackStyle` contém `scrollSnapType: \"x proximity\"`", false);
  ok("`carouselTrackStyle` contém `WebkitOverflowScrolling: \"touch\"`", false);
}

// --- 2. carouselItemStyle existe ---------------------------------------------

const idxItemDef = app.indexOf("const carouselItemStyle");
ok("existe `const carouselItemStyle`", idxItemDef >= 0);
if (idxItemDef >= 0) {
  const fimItemDef = app.indexOf("\nconst ", idxItemDef + 10);
  const itemDefBloco = app.slice(idxItemDef, fimItemDef > idxItemDef ? fimItemDef : idxItemDef + 200);
  ok("`carouselItemStyle` contém `scrollSnapAlign`", itemDefBloco.includes("scrollSnapAlign"));
} else {
  ok("`carouselItemStyle` contém `scrollSnapAlign`", false);
}

// --- 3. Asserção central: overflowX: "auto" só pode existir 1x (no helper) --

const totalOverflowXAuto = (app.match(/overflowX: "auto"/g) || []).length;
ok(
  "`overflowX: \"auto\"` aparece exatamente 1× em App.jsx (trilho horizontal novo deve usar carouselTrackStyle(), não redefinir overflowX inline)",
  totalOverflowXAuto === 1
);

// --- 4. Os 4 call sites de carouselTrackStyle( -------------------------------
// A definição é `const carouselTrackStyle = (extra) => ({...})` — o nome
// seguido de parêntese sem espaço não ocorre nessa forma, então a definição
// não entra na contagem de chamadas.

const totalTrackCalls = (app.match(/carouselTrackStyle\(/g) || []).length;
ok("os 4 containers de trilho chamam `carouselTrackStyle(` (limiar >= 4, definição não conta)", totalTrackCalls >= 4);

// --- 5. Os 4 itens de carouselItemStyle( -------------------------------------
// Mesma razão do item 4: `const carouselItemStyle = (align = "start") => ...`
// não casa com o padrão `nome(`.

const totalItemCalls = (app.match(/carouselItemStyle\(/g) || []).length;
ok("os 4 itens chamam `carouselItemStyle(` (limiar >= 4, definição não conta)", totalItemCalls >= 4);

// --- 6. Presença nomeada de cada um dos 4 call sites -------------------------

ok("recorte de TECH_MODELS.map( chama `carouselTrackStyle(`", techModelsBloco.includes("carouselTrackStyle("));
ok("função OportunidadesOpcoes chama `carouselTrackStyle(`", oportunidadesOpcoes.includes("carouselTrackStyle("));
ok("função PropostaDaPosicao chama `carouselTrackStyle(`", propostaDaPosicao.includes("carouselTrackStyle("));
ok("função EvolucaoScreen (HERO-CARROSSEL) chama `carouselTrackStyle(`", evolucaoScreen.includes("carouselTrackStyle("));

// --- 7. Taxonomia preservada (Decisão 1 do 22-UI-SPEC): peek de 84% só HERO -

const totalPeek84 = (app.match(/flex: "0 0 84%"/g) || []).length;
ok(
  "`flex: \"0 0 84%\"` aparece exatamente 1× (peek de 84% é do HERO-CARROSSEL apenas — chips de filtro e candidatos de opção precisam ficar comparáveis lado a lado)",
  totalPeek84 === 1
);

// --- 8. Sub-variante de foco único é só do HERO ------------------------------

const totalMandatory = (app.match(/"x mandatory"/g) || []).length;
ok('"x mandatory" aparece exatamente 1× (override exclusivo do HERO-CARROSSEL)', totalMandatory === 1);

const totalCenterAlign = (app.match(/scrollSnapAlign: "center"/g) || []).length + (app.match(/carouselItemStyle\("center"\)/g) || []).length;
ok('`scrollSnapAlign: "center"` (ou `carouselItemStyle("center")`) aparece exatamente 1× (o HERO)', totalCenterAlign === 1);

// --- 9. <main> mantém overflowX: "hidden" (FIX-01, Fase 20, fora de escopo) -

ok('`<main>` mantém `overflowX: "hidden"` (FIX-01, Fase 20, fora do escopo do helper)', /<main[^>]*overflowX: "hidden"/.test(app));

// --- Seção B — SYS-02 (plano 22-02): NavIcon generalizado (size/color) e os --
// --- 8 sites de emoji do Perfil/Watchlist/Posições/config trocados por SVG --

const navIconBloco = isolarFuncao("NavIcon");
const modoTrabalhoCard = isolarFuncao("ModoTrabalhoCard");
const ativoCard = isolarFuncao("AtivoCard");
const carteiraScreen = isolarFuncao("CarteiraScreen");
const skillSection = isolarFuncao("SkillSection");

// --- B1. Assinatura do NavIcon aceita `size` e `color` -----------------------

ok('NavIcon aceita `size` na assinatura', /function NavIcon\(\{[^}]*\bsize\b[^}]*\}\)/.test(navIconBloco));
ok('NavIcon aceita `color` na assinatura', /function NavIcon\(\{[^}]*\bcolor\b[^}]*\}\)/.test(navIconBloco));

// --- B2. Cor resolvida com fallback (novo caminho + caminho antigo do BottomNav) --

ok('NavIcon resolve a cor com fallback (`color ||`, o novo caminho)', navIconBloco.includes("color ||"));
ok('NavIcon preserva `active ? T.accent : T.textMuted` (caminho antigo, consumido pelo BottomNav)', navIconBloco.includes("active ? T.accent : T.textMuted"));

// --- B3. <svg> usa width={size}/height={size}, mantém viewBox e aria-hidden --

ok('<svg> do NavIcon usa `width={size}`', navIconBloco.includes("width={size}"));
ok('<svg> do NavIcon usa `height={size}`', navIconBloco.includes("height={size}"));
ok('<svg> do NavIcon mantém `viewBox="0 0 24 24"`', navIconBloco.includes('viewBox="0 0 24 24"'));
ok('<svg> do NavIcon mantém `aria-hidden`', navIconBloco.includes("aria-hidden"));

// --- B4. Mapa `paths` tem os 3 ids novos e continua com os 7 antigos --------

for (const id of ["graduacao", "brilho", "checado"]) {
  ok(`mapa \`paths\` do NavIcon contém o id novo \`${id}:\``, navIconBloco.includes(`${id}:`));
}
for (const id of ["evolucao", "mercado", "radar", "carteira", "opcoes", "perfil", "agente"]) {
  ok(`mapa \`paths\` do NavIcon continua com o id antigo \`${id}:\``, navIconBloco.includes(`${id}:`));
}

// --- B5. `radar: <>` continua verdadeiro (compatibilidade com test_radar.mjs:45) --

ok('`radar: <>` continua verdadeiro (exigência de test_radar.mjs:45)', /radar:\s*<>/.test(navIconBloco));

// --- B6. Emoji zero para os glifos desta onda, sobre App.jsx inteiro --------

ok("zero ocorrência de 🎓 em App.jsx", !app.includes("🎓"));
ok("zero ocorrência de 📈 em App.jsx", !app.includes("📈"));
ok("zero ocorrência de ✨ em App.jsx", !app.includes("✨"));
ok("zero ocorrência de ✅ em App.jsx", !app.includes("✅"));

// --- B7. Fora de escopo preservado: vocabulário tipográfico da casa, não é --
// --- emoji do sistema (22-UI-SPEC.md, Out-of-scope symbols) -----------------

ok("glifo fora de escopo `⚡` continua presente (vocabulário da casa)", app.includes("⚡"));
ok("glifo fora de escopo `✎` continua presente (vocabulário da casa)", app.includes("✎"));
ok("glifo fora de escopo `↻` continua presente (vocabulário da casa)", app.includes("↻"));
ok("glifo fora de escopo `✕` continua presente (vocabulário da casa)", app.includes("✕"));
ok("glifo fora de escopo `✓` continua presente (vocabulário da casa)", app.includes("✓"));
ok("glifo fora de escopo `⚠` continua presente (vocabulário da casa)", app.includes("⚠"));

// --- B8. Pelo menos 8 chamadas <NavIcon id= (BottomNav + 7 sites desta onda) --

ok("há pelo menos 8 chamadas `<NavIcon id=` (BottomNav + sites desta onda)", (app.match(/<NavIcon id=/g) || []).length >= 8);

// --- B9. Cada site nomeado, por assinatura textual estável (nunca por linha) --

ok('recorte de ModoTrabalhoCard contém `id="graduacao"`', modoTrabalhoCard.includes('id="graduacao"'));
ok('recorte de ModoTrabalhoCard mantém o rótulo "Estudo" visível', modoTrabalhoCard.includes("Estudo"));
ok('rótulo "Indicadores" sobreviveu à troca do emoji', app.includes("Indicadores"));
ok('rótulo "Stop/alvo (IA)" sobreviveu à troca do emoji', app.includes("Stop/alvo (IA)"));
ok('rótulo "chave configurada" sobreviveu à troca do emoji', app.includes("chave configurada"));
ok('rótulo "Reanalisar" sobreviveu à troca do emoji', app.includes("Reanalisar"));
ok('a chave de copy `cp.btnAnalise` segue consumida', app.includes("cp.btnAnalise"));
ok('recorte de AtivoCard contém o fallback de sparkline com `id="evolucao"`', ativoCard.includes('id="evolucao"'));
ok('recorte de CarteiraScreen contém o botão de Stop/alvo com `id="evolucao"`', carteiraScreen.includes('id="evolucao"'));

// --- B10. <option> limpo: texto puro, sem emoji (nomeado à parte de B6, para --
// --- a mensagem de falha apontar o site certo) ------------------------------

const idxOptEstudo = app.indexOf('<option value="estudo">');
const idxOptOperador = app.indexOf('<option value="operador">');
if (idxOptEstudo < 0 || idxOptOperador < 0) {
  console.error('FALHOU: <option value="estudo"|"operador"> não encontrado em App.jsx — guardião não pode isolar o select de skill');
  process.exit(1);
}
const optEstudoLine = app.slice(idxOptEstudo, app.indexOf("</option>", idxOptEstudo) + "</option>".length);
const optOperadorLine = app.slice(idxOptOperador, app.indexOf("</option>", idxOptOperador) + "</option>".length);
ok('`<option value="estudo">` contém " · Estudo</option>" e não contém 🎓', optEstudoLine.includes(" · Estudo</option>") && !optEstudoLine.includes("🎓"));
ok('`<option value="operador">` contém " · Operador</option>" e não contém 📈', optOperadorLine.includes(" · Operador</option>") && !optOperadorLine.includes("📈"));
// skillSection isolado acima só para eventual depuração futura — as duas
// linhas de <option> já são suficientes para a asserção, sem depender de
// isolamento de função (o marcador de linha é mais estável para este site).
ok('recorte de SkillSection contém os dois `<option>` do select de skill', skillSection.includes('<option value="estudo">') && skillSection.includes('<option value="operador">'));

// --- B11. Zero dependência de ícone em web/package.json ---------------------

const pkgJson = JSON.parse(readFileSync(join(here, "..", "package.json"), "utf8"));
const allDeps = { ...(pkgJson.dependencies || {}), ...(pkgJson.devDependencies || {}) };
for (const lib of ["lucide-react", "react-icons", "@heroicons/react", "phosphor-react"]) {
  ok(`\`${lib}\` não é dependência de web/package.json`, !(lib in allDeps));
}

// --- Seção C — SYS-02, Radar + varredura final (plano 22-03) ----------------

// C1. A trava definitiva de SYS-02: nenhum pictográfico do bloco de emoji
// resta em App.jsx. Mensagem de falha IMPRIME os glifos encontrados, para o
// próximo agente saber quais sobraram sem ter que caçar.
{
  const pictograficos = app.match(/[\u{1F300}-\u{1FAFF}]/gu);
  ok(
    `varredura Unicode pictográfica em App.jsx dá zero${pictograficos ? " (encontrados: " + JSON.stringify(pictograficos) + ")" : ""}`,
    !pictograficos
  );
}

// C2. `⚪` vive em U+26AA, dentro do bloco 2600-27BF onde a microcópia
// legítima também mora — asserção própria, não varredura de faixa.
ok("`⚪` não aparece mais em App.jsx", !app.includes("⚪"));

// C3. Fora de escopo preservado (asserções POSITIVAS, repetidas aqui de
// propósito porque a Seção C é onde uma varredura de faixa poderia ter
// varrido demais).
ok("glifo fora de escopo `⚡` continua presente (Seção C)", app.includes("⚡"));
ok("glifo fora de escopo `✎` continua presente (Seção C)", app.includes("✎"));
ok("glifo fora de escopo `↻` continua presente (Seção C)", app.includes("↻"));
ok("glifo fora de escopo `✕` continua presente (Seção C)", app.includes("✕"));
ok("glifo fora de escopo `✓` continua presente (Seção C)", app.includes("✓"));
ok("glifo fora de escopo `⚠` continua presente (Seção C)", app.includes("⚠"));
ok("`↻ Releitura após o fechamento` sobrevive (braço irmão do ternário do 📡)", app.includes("↻ Releitura após o fechamento"));
ok("`↻ Última varredura (manual)` sobrevive (braço irmão do ternário do 📡)", app.includes("↻ Última varredura (manual)"));

// C4. O rótulo textual sobreviveu (test_fase4_radar_deepmodal.mjs:25 também exige).
ok("`Varredura automática de hoje` sobrevive", app.includes("Varredura automática de hoje"));

// C5. O 📡 virou reuso, não geometria nova.
const radarScreenBloco = isolarFuncao("RadarScreen");
ok('recorte de RadarScreen contém `<NavIcon id="radar"`', radarScreenBloco.includes('<NavIcon id="radar"'));
ok(
  "mapa `paths` continua com exatamente uma entrada `radar:`",
  (app.match(/^\s*radar:/gm) || []).length === 1
);

// C6. `function TierDot` existe e seu corpo contém <circle>, fill e aria-hidden.
const idxTierDot = app.indexOf("function TierDot");
ok("existe `function TierDot`", idxTierDot >= 0);
let tierDotBloco = "";
if (idxTierDot >= 0) {
  const fimTierDot = app.indexOf("\n}", idxTierDot);
  tierDotBloco = app.slice(idxTierDot, fimTierDot > idxTierDot ? fimTierDot + 2 : idxTierDot + 400);
  ok("`TierDot` contém `<circle`", tierDotBloco.includes("<circle"));
  ok("`TierDot` contém `fill`", tierDotBloco.includes("fill"));
  ok("`TierDot` contém `aria-hidden`", tierDotBloco.includes("aria-hidden"));
} else {
  ok("`TierDot` contém `<circle`", false);
  ok("`TierDot` contém `fill`", false);
  ok("`TierDot` contém `aria-hidden`", false);
}

// C7. Mapa de cor de tier com os quatro literais aprovados, isolado pelo
// recorte de `const TIER_FILL` (da declaração até o `};`). Atenção: #22c55e e
// #ef4444 JÁ existem uma vez cada em MODE_OPERADOR (comentário de prosa,
// verificado por grep em 2026-09-05) — por isso a asserção é sobre o RECORTE
// isolado de TIER_FILL, não sobre o arquivo inteiro.
const idxTierFill = app.indexOf("const TIER_FILL");
ok("existe `const TIER_FILL`", idxTierFill >= 0);
let tierFillBloco = "";
if (idxTierFill >= 0) {
  const fimTierFill = app.indexOf("};", idxTierFill);
  tierFillBloco = app.slice(idxTierFill, fimTierFill > idxTierFill ? fimTierFill + 2 : idxTierFill + 300);
  for (const hex of ["#22c55e", "#f59e0b", "#9ca3af", "#ef4444"]) {
    ok(`recorte de TIER_FILL contém ${hex}`, tierFillBloco.includes(hex));
  }
} else {
  for (const hex of ["#22c55e", "#f59e0b", "#9ca3af", "#ef4444"]) {
    ok(`recorte de TIER_FILL contém ${hex}`, false);
  }
}

// C8. Separação semântica preservada: nem TierDot nem TIER_FILL citam
// T.positive/T.negative/T.warn — verde/vermelho seguem reservados a sinal de
// mercado (ver o comentário de tierOf); o tier é outro eixo.
const recorteTierCombinado = tierFillBloco + tierDotBloco;
ok(
  "verde/vermelho seguem reservados a sinal de mercado — ver o comentário de tierOf; o tier é outro eixo",
  !recorteTierCombinado.includes("T.positive") && !recorteTierCombinado.includes("T.negative") && !recorteTierCombinado.includes("T.warn")
);

// C9. tierOf devolve ids de tier (minúsculas) e continua com os rótulos
// (índice [1] intocável).
const idxTierOf = app.indexOf("function tierOf");
const tierOfBloco = idxTierOf >= 0 ? app.slice(idxTierOf, app.indexOf("\n}", idxTierOf) + 2) : "";
ok('`tierOf` devolve o id `"forte"`', tierOfBloco.includes('"forte"'));
ok('`tierOf` devolve o id `"moderada"`', tierOfBloco.includes('"moderada"'));
ok('`tierOf` devolve o id `"neutra"`', tierOfBloco.includes('"neutra"'));
ok('`tierOf` devolve o id `"fraca"`', tierOfBloco.includes('"fraca"'));
ok('`tierOf` continua com o rótulo `"Forte"`', tierOfBloco.includes('"Forte"'));
ok('`tierOf` continua com o rótulo `"Moderada"`', tierOfBloco.includes('"Moderada"'));
ok('`tierOf` continua com o rótulo `"Neutra"`', tierOfBloco.includes('"Neutra"'));
ok('`tierOf` continua com o rótulo `"Fraca"`', tierOfBloco.includes('"Fraca"'));

// C10. Compatibilidade com test_radar_leitura_rapida.mjs — comentado aqui de
// propósito, para o próximo agente perceber a dependência ANTES de mexer no
// formato da tupla.
ok(
  "compatibilidade com test_radar_leitura_rapida.mjs: `tierLabel = tierOf(r.confluencia)` casa",
  /tierLabel\s*=\s*tierOf\(r\.confluencia\)/.test(app)
);
ok(
  "compatibilidade com test_radar_leitura_rapida.mjs: `confiança {tierLabel` casa",
  /confiança \{tierLabel/.test(app)
);

// C11. tierOf mantém os quatro limiares literais.
ok("`tierOf` mantém o limiar `>= 75`", tierOfBloco.includes(">= 75"));
ok("`tierOf` mantém o limiar `>= 50`", tierOfBloco.includes(">= 50"));
ok("`tierOf` mantém o limiar `> 0`", tierOfBloco.includes("> 0"));
ok("`tierOf` mantém o `return` final", /return \[/.test(tierOfBloco));

// C12. <TierDot tier= aparece na renderização do Radar; índice [0] não é mais
// renderizado como texto cru (filho direto de JSX, precedido por `>`) em
// lugar nenhum. NOTA: o regex isola o caso "texto cru" por estar precedido de
// `>` — sem essa âncora, o padrão bateria também em `tier={tierOf(...)[0]}`,
// que é exatamente o uso correto que este plano introduz (bug encontrado e
// corrigido nesta mesma task, antes de qualquer commit incorreto).
ok("`<TierDot tier=` aparece na renderização do Radar", app.includes("<TierDot tier="));
ok(
  "o índice [0] de `tierOf` não é mais renderizado como texto cru",
  !/>\{tierOf\([^)]*\)\[0\]\}/.test(app)
);

// C13. Código morto removido: o destructure `[tierDot, tierLabel]` da
// Watchlist saiu. Ambos os nomes daquela linha eram mortos (verificado por
// grep em 2026-09-05) — `tierLabel` de RadarScreen (outro escopo) é uma
// declaração DIFERENTE (`const tierLabel = tierOf(r.confluencia)[1];`), que
// sobrevive à Seção C10 acima.
ok("`tierDot` (destructure morto da Watchlist) saiu de App.jsx", !app.includes("tierDot"));

// --- Seção D — SYS-03, sombra do PetFab por tema (plano 22-03) --------------

const petFabBloco = isolarFuncao("PetFab");

// Isolar as duas metades de PALETTE (dark/light) — do "dark: {" (ou "light: {")
// até o fechamento correspondente da chave de primeiro nível dentro de PALETTE.
const idxPaletteDark = app.indexOf("dark: {", app.indexOf("const PALETTE"));
const idxPaletteLight = app.indexOf("light: {", app.indexOf("const PALETTE"));
const paletteDarkBloco = app.slice(idxPaletteDark, app.indexOf("\n  light: {", idxPaletteDark));
const paletteLightBloco = app.slice(idxPaletteLight, app.indexOf("\n};", idxPaletteLight));

// D14. PALETTE.dark e PALETTE.light têm a chave shadowFab.
ok("`PALETTE.dark` contém `shadowFab:`", paletteDarkBloco.includes("shadowFab:"));
ok("`PALETTE.light` contém `shadowFab:`", paletteLightBloco.includes("shadowFab:"));

// D15. O valor em dark é exatamente "rgba(0,0,0,0.45)" — o tema escuro
// preserva a aparência de hoje.
const mDark = paletteDarkBloco.match(/shadowFab:\s*"([^"]*)"/);
const mLight = paletteLightBloco.match(/shadowFab:\s*"([^"]*)"/);
ok(
  '`shadowFab` do tema escuro é exatamente "rgba(0,0,0,0.45)" (o tema escuro não muda de aparência)',
  !!mDark && mDark[1] === "rgba(0,0,0,0.45)"
);

// D16. O valor em light é DIFERENTE do valor em dark — requisito inteiro de
// SYS-03 (nunca um hex fixo que só funciona num tema).
ok(
  "`shadowFab` do tema claro é DIFERENTE do valor do tema escuro",
  !!mLight && !!mDark && mLight[1] !== mDark[1]
);

// D17. O corpo do PetFab contém T.shadowFab dentro de um drop-shadow(.
ok(
  "`PetFab` usa `T.shadowFab` dentro de um `drop-shadow(`",
  /drop-shadow\([^)]*T\.shadowFab/.test(petFabBloco)
);

// D18. O corpo do PetFab não contém mais rgba(0,0,0,0.45) literal.
ok(
  "`PetFab` não contém mais `rgba(0,0,0,0.45)` inline",
  !petFabBloco.includes("rgba(0,0,0,0.45)")
);

// D19. Não colidir com test_pet_ui.mjs (guardião de outra fase, repetido aqui
// com comentário citando test_pet_ui.mjs:99-114).
ok("`PetFab` mantém `<Boris size={40} />` (test_pet_ui.mjs:99-114)", petFabBloco.includes("<Boris size={40} />"));
ok('`PetFab` mantém `width: "54px", height: "54px"` (test_pet_ui.mjs:99-114)', petFabBloco.includes('width: "54px", height: "54px"'));
ok('`PetFab` mantém `background: "transparent"` (test_pet_ui.mjs:99-114)', petFabBloco.includes('background: "transparent"'));
ok('`PetFab` mantém `border: "none"` (test_pet_ui.mjs:99-114)', petFabBloco.includes('border: "none"'));
ok('`PetFab` NÃO contém `borderRadius: "50%"` (test_pet_ui.mjs:99-114)', !petFabBloco.includes('borderRadius: "50%"'));

// D20. PetFab continua na posição fixa de hoje — SYS-03 é só sombra.
ok('`PetFab` mantém `position: "fixed"`', petFabBloco.includes('position: "fixed"'));
ok('`PetFab` mantém `right: "14px"`', petFabBloco.includes('right: "14px"'));
ok('`PetFab` mantém `bottom: "92px"`', petFabBloco.includes('bottom: "92px"'));

if (fails > 0) {
  console.error(`\n${fails} asserção(ões) falharam.`);
}
process.exit(fails);
