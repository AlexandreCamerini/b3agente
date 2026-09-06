// ADR-017 Bloco 3/4 (Fase 8, Plano 04) — guardião do histórico medido no
// NÍVEL DO SETUP (item de lista "Ver critérios do setup") + da transparência
// do gate de entrada automática, originalmente no card de status único do
// Operador (C-19).
//
// REVERSÃO DELIBERADA (2026-09-05, Fase 21 do milestone v1.5, DEDUP-02): o
// card C-19 foi REMOVIDO de AgenteScreen (era redundante com o card-herói
// funcional "OPERADOR NO SERVIDOR"). As duas frases agregadas
// (cp.entradaAuto.regra/.contraste) que viviam nele foram RELOCADAS para
// dentro do card "ENTRADA AUTOMÁTICA" — o único card da tela que trata de
// entrada automática, lar tematicamente correto. O "Recorte 2" abaixo foi
// REPONTADO do card C-19 para o card ENTRADA AUTOMÁTICA; a asserção (9)
// (App.jsx não hardcoda os valores literais de COPY[modo].entradaAuto)
// segue válida e intacta — prova que a transparência continua vindo de
// copy.js mesmo depois de mudar de lar. Este guardião NÃO foi apagado.
//
// Separado de test_historico_ui.mjs (Plano 08-03) de propósito: aquele
// guardião trava o HistoricoPill no NÍVEL DO TICKER (Radar/Watchlist, chip
// ao lado de melhorSetup); este trava (a) o mesmo componente reusado dentro
// de CADA setup da lista de critérios — com o carimbo de tempo e a linha de
// transparência do gate por setup — e (b) as duas frases agregadas
// (cp.entradaAuto.regra/.contraste), hoje dentro do card ENTRADA
// AUTOMÁTICA. Nenhuma asserção daqui duplica as de lá.
//
// Padrão da casa (test_fase3_c19_card_status.mjs): lê App.jsx como TEXTO
// (sem build, sem DOM), caminhos resolvidos por `new URL(...,
// import.meta.url)` — nunca relativos ao cwd (scripts/executar.sh roda os
// runners com cwd=web). Cada recorte tem abort EXPLÍCITO se o marcador
// sumir — este guardião nunca vira "0 asserções, tudo ok" em silêncio.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const appSrc = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
// comentários filtrados (linha inteira começando com `//`, com indentação
// qualquer) — os comentários novos das Tasks 1/2 citam nominalmente os
// estados e os números do contraste; contar sobre o arquivo bruto se
// auto-invalidaria.
const appSrcSemComentarios = appSrc
  .split("\n")
  .filter((linha) => !/^\s*\/\//.test(linha))
  .join("\n");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const abort = (msg) => { console.error("FALHOU: " + msg); process.exit(1); };

// ---------------------------------------------------------------------
// Recorte 1: item de lista de setup — do início do `.map` sobre `r.setups`
// até o fecho desse `.map` (o `.map` aninhado de `s.criterios` fecha com
// `))}`, não `})}` — arrow de parênteses × arrow de bloco, sem ambiguidade).
// ---------------------------------------------------------------------
const MARCADOR_INICIO_ITEM = "(r.setups || []).map((s, si) => {";
const iniItem = appSrc.indexOf(MARCADOR_INICIO_ITEM);
if (iniItem < 0) abort(`marcador de início do item de setup ("${MARCADOR_INICIO_ITEM}") não encontrado em App.jsx — o .map sobre r.setups mudou de forma; ajuste o guardião antes de prosseguir`);
const MARCADOR_FIM_ITEM = "\n              })}";
const fimItemRel = appSrc.indexOf(MARCADOR_FIM_ITEM, iniItem);
if (fimItemRel < 0) abort("marcador de fim do item de setup (fecho do .map, \"})}\") não encontrado após o início — ajuste o guardião antes de prosseguir");
const itemSetup = appSrc.slice(iniItem, fimItemRel);

// ---------------------------------------------------------------------
// Recorte 2 — REPONTADO (2026-09-05, DEDUP-02): do card C-19 removido para
// o card ENTRADA AUTOMÁTICA, novo lar da transparência do gate. Marcador de
// início: título do card. Marcador de fim: `id="alloc"` (o slider de
// alocação, primeiro elemento logo depois do bloco de texto do card).
// ---------------------------------------------------------------------
const iniScreen = appSrc.indexOf("function AgenteScreen(");
if (iniScreen < 0) abort("função AgenteScreen não encontrada em App.jsx");
const fimScreen = appSrc.indexOf("\nfunction ", iniScreen + 10);
const screen = appSrc.slice(iniScreen, fimScreen > iniScreen ? fimScreen : undefined);
const MARCADOR_INICIO_ENTRADA_AUTO = "ENTRADA AUTOMÁTICA";
const iniCard = screen.indexOf(MARCADOR_INICIO_ENTRADA_AUTO);
if (iniCard < 0) abort(`marcador de início do card ("${MARCADOR_INICIO_ENTRADA_AUTO}") não encontrado em AgenteScreen — se renomeado, este guardião TEM que abortar, nunca passar em silêncio`);
const MARCADOR_FIM_CARD = 'id="alloc"';
const fimCard = screen.indexOf(MARCADOR_FIM_CARD, iniCard);
if (fimCard < 0 || fimCard <= iniCard) abort('marcador de fim do card ENTRADA AUTOMÁTICA (`id="alloc"`, o slider de alocação) não encontrado após o início do card');
const cardEntradaAuto = screen.slice(iniCard, fimCard);
// Não-regressão: o card C-19 removido não pode voltar.
const MARCADOR_C19 = "C-19 (REPORT-01)";

// ======================= NÍVEL SETUP (item de lista) =====================

// (1) HistoricoPill renderizado com s.historico E s.aposentado
ok("item de setup renderiza <HistoricoPill> com historico={s.historico} e aposentado={s.aposentado}",
  /<HistoricoPill\s+historico=\{s\.historico\}\s+aposentado=\{s\.aposentado\}/.test(itemSetup));

// (2) setup aposentado NUNCA esmaecido/riscado/removido — sem line-through
// nem opacity aplicada ao nome
ok("item de setup NÃO contém textDecoration: \"line-through\" (aposentado ≠ apagado, ADR-017 Decisão 1)",
  !itemSetup.includes('textDecoration: "line-through"') && !itemSetup.includes("textDecoration: 'line-through'"));
ok("item de setup NÃO aplica `opacity` ao nome do setup (nenhum esmaecimento do card aposentado)",
  !/opacity\s*:/.test(itemSetup));

// (3) s.confluencia continua a âncora primária — HistoricoPill vem DEPOIS
// dele no fonte do item (UI-SPEC "Focal point")
const idxConfluencia = itemSetup.indexOf("s.confluencia");
const idxPillNoItem = itemSetup.indexOf("<HistoricoPill");
ok("s.confluencia aparece no item de setup", idxConfluencia >= 0);
ok("<HistoricoPill> aparece DEPOIS de s.confluencia no item de setup (âncora primária preservada)",
  idxPillNoItem > idxConfluencia && idxConfluencia >= 0);

// (4) transparência do gate por setup: entradaAutoTxt chamado com s.nome
// como `setup`
ok("item de setup chama entradaAutoTxt(...) passando `setup: s.nome`",
  itemSetup.includes("entradaAutoTxt(") && /setup:\s*s\.nome/.test(itemSetup));

// (5) a linha por setup só existe em Modo Operador — entradaAutoTxt precisa
// estar dentro de um bloco condicionado a `operador &&`
const idxEntradaAutoTxt = itemSetup.indexOf("entradaAutoTxt(");
const janela = idxEntradaAutoTxt >= 0 ? itemSetup.slice(Math.max(0, idxEntradaAutoTxt - 200), idxEntradaAutoTxt) : "";
ok("a chamada de entradaAutoTxt está condicionada a `operador &&` (em Modo Estudo a linha não aparece)",
  idxEntradaAutoTxt >= 0 && /\{operador\s*&&\s*\(/.test(janela));

// (6) nenhuma frase literal do gate por setup hardcodada em App.jsx (tudo
// vem de copy.js via entradaAutoTxt) — checagem no arquivo INTEIRO
ok('App.jsx NÃO contém, literal, "Entrada automática disponível para" (fora de comentário)',
  !appSrcSemComentarios.includes("Entrada automática disponível para"));
ok('App.jsx NÃO contém, literal, "Entrada automática bloqueada para" (fora de comentário)',
  !appSrcSemComentarios.includes("Entrada automática bloqueada para"));

// ============ CARD ENTRADA AUTOMÁTICA (novo lar da transparência do gate) —
// REVERSÃO DELIBERADA 2026-09-05, Fase 21, DEDUP-02: o card C-19 (status do
// Operador) saiu de AgenteScreen; esta seção passou a travar (7) a
// não-regressão dele e (8) a transparência do gate no NOVO recorte. ========

// (7) não-regressão: o card C-19 removido não pode voltar, nem os três
// badges que ele continha.
ok('"C-19 (REPORT-01)" não aparece mais em AgenteScreen (o card não volta)',
  !screen.includes(MARCADOR_C19));
ok('"Modo do app:" não aparece mais em AgenteScreen (badge do card removido)',
  (screen.match(/Modo do app:/g) || []).length === 0);
ok('"Operador no servidor:" não aparece mais em AgenteScreen (badge do card removido)',
  (screen.match(/Operador no servidor:/g) || []).length === 0);
ok('"Executar\\/sinalizar:" não aparece mais em AgenteScreen (badge do card removido)',
  (screen.match(/Executar\/sinalizar:/g) || []).length === 0);

// (8) cp.entradaAuto.regra e .contraste agora renderizados dentro do card
// ENTRADA AUTOMÁTICA (tolera `ctx.cp.entradaAuto...` ou `cp.entradaAuto...`,
// nunca frase hardcodada) — mudou de recorte, não de conteúdo.
ok("card ENTRADA AUTOMÁTICA renderiza cp.entradaAuto.regra", /cp\.entradaAuto\.regra/.test(cardEntradaAuto));
ok("card ENTRADA AUTOMÁTICA renderiza cp.entradaAuto.contraste", /cp\.entradaAuto\.contraste/.test(cardEntradaAuto));

// (9) nenhum valor literal de COPY[modo].entradaAuto (regra/contraste/
// por_setup_*) hardcodado em App.jsx — cobre os dois modos
for (const modo of ["estudo", "operador"]) {
  for (const [chave, valor] of Object.entries(COPY[modo].entradaAuto)) {
    ok(`App.jsx não hardcoda COPY.${modo}.entradaAuto.${chave}`, !appSrc.includes(valor));
  }
}
// números do contraste especificamente (T-08-15 do threat model) — mesmo
// fora do dicionário, nunca podem aparecer soltos fora de comentário
ok('App.jsx NÃO contém, literal, "0,099R" fora de comentário', !appSrcSemComentarios.includes("0,099R"));
ok('App.jsx NÃO contém, literal, "0,005R" fora de comentário', !appSrcSemComentarios.includes("0,005R"));

console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} falha(s)`);
process.exit(fails === 0 ? 0 : 1);
