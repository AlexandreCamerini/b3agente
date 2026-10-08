// Onda G (2026-10-08) — quick 261008-iuz.
// (1) Swipe-back de borda tolerante (32/50/60) sem roubar rolagem horizontal/sliders.
// (2) Mais largura útil: gutter 12px (rampa até 18px) + padding lateral de cartão 16px (SP[4]).
// (3) Botão "Registrar saída" com 0 ações livres efetivamente disabled.
import { readFileSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import * as N from "../src/navStack.js";

const here = dirname(fileURLToPath(import.meta.url));
const ler = (p) => readFileSync(join(here, "..", "src", p), "utf8");
let falhas = 0;
const ok = (n, c) => { if (!c) { falhas++; console.error("FALHOU:", n); } else console.log("ok:", n); };

const app = ler("App.jsx");
const recorte = (nome) => {
  const ini = app.indexOf("function " + nome + "(");
  if (ini < 0) return "";
  const fim = app.indexOf("\nfunction ", ini + 10);
  return app.slice(ini, fim < 0 ? undefined : fim);
};

// parte 1 — swipe
ok("BORDA_PX/DX_MIN/DY_MAX = 32/50/60", N.BORDA_PX === 32 && N.DX_MIN === 50 && N.DY_MAX === 60);
ok("gesto tolerante aceito", N.ehGestoVoltarBorda({ x0: 30, y0: 100, x1: 85, y1: 150 }) === true);
ok("fora da borda (x0 33)", N.ehGestoVoltarBorda({ x0: 33, y0: 100, x1: 200, y1: 100 }) === false);
ok("dx 50 não basta", N.ehGestoVoltarBorda({ x0: 10, y0: 100, x1: 60, y1: 100 }) === false);
ok("dx 51 basta", N.ehGestoVoltarBorda({ x0: 10, y0: 100, x1: 61, y1: 100 }) === true);
ok("dy 60 não basta", N.ehGestoVoltarBorda({ x0: 10, y0: 100, x1: 120, y1: 160 }) === false);
ok("closest exclui canvas, range e marcados",
  app.includes('e.target.closest("canvas, input[type=\\"range\\"], [data-sem-gesto-voltar]")'));

const arquivos = [["App.jsx", app]];
for (const f of readdirSync(join(here, "..", "src", "opcoes")).filter((x) => x.endsWith(".jsx"))) {
  arquivos.push(["opcoes/" + f, ler("opcoes/" + f)]);
}
let totalTrilhos = 0;
for (const [nome, src] of arquivos) {
  src.split("\n").forEach((l, i) => {
    if (!l.includes("<div")) return;
    if (!(l.includes("carouselTrackStyle(") || l.includes("style={trilho}") || l.includes("style={ROLAGEM}") || l.includes('overflowX: "auto"'))) return;
    totalTrilhos++;
    ok(`trilho marcado ${nome}:${i + 1}`, l.includes("data-sem-gesto-voltar"));
  });
}
// Plano dizia 12, mas a soma por arquivo (2+1+1+2+2+1+1+1) é 11.
ok("trilhos encontrados >= 11 (era " + totalTrilhos + ")", totalTrilhos >= 11);

// parte 2 — largura
const iSP = app.indexOf("const SP = {");
const iG = app.indexOf("const GUTTER_X = `clamp(${SP[3]}px, calc(100vw - 714px), 18px)`;");
const iC = app.indexOf("const CARD_PAD_X = SP[4];");
ok("GUTTER_X definido após SP", iG > iSP && iSP >= 0);
ok("CARD_PAD_X definido após SP", iC > iSP && iSP >= 0);
ok("sem padding 24px 18px 34px", !app.includes('padding: "24px 18px 34px"'));
const wrap = app.split("\n").find((l) => l.includes('maxWidth: CONTENT_MAX_WIDTH, margin: "0 auto"') && l.includes("translateY")) || "";
ok("wrapper: safe-area esquerda", wrap.includes("paddingLeft: `max(${GUTTER_X}, env(safe-area-inset-left))`"));
ok("wrapper: safe-area direita", wrap.includes("paddingRight: `max(${GUTTER_X}, env(safe-area-inset-right))`"));
ok("wrapper: paddingTop/Bottom", wrap.includes('paddingTop: "24px"') && wrap.includes('paddingBottom: "34px"'));
ok("CONTENT_MAX_WIDTH 1x", (app.match(/const CONTENT_MAX_WIDTH = "720px";/g) || []).length === 1);
ok("maxWidth: CONTENT_MAX_WIDTH 2x", (app.match(/maxWidth: CONTENT_MAX_WIDTH/g) || []).length === 2);
const linhaHero = app.split("\n").find((l) => l.includes('scrollSnapType: "x mandatory"')) || "";
ok("hero: margem negativa = gutter", linhaHero.includes("margin: `0 calc(-1 * ${GUTTER_X})`"));
ok("hero: padding = gutter", linhaHero.includes("padding: `2px ${GUTTER_X} 6px`"));
ok("hero: sem -18px", linhaHero !== "" && !linhaHero.includes("-18px"));
for (const c of ["CapitalCurve", "EvolucaoScreen", "CarteiraScreen", "AgenteScreen", "NotifSection", "SkillSection",
  "PromptsSection", "BorisConfigSection", "PlanoScreen", "AiConfigScreen", "LogsDebugScreen", "FonteDadosScreen",
  "RadarScreen", "OpcaoDescobertoCard", "ConfigScreen"]) {
  const r = recorte(c);
  ok(`recorte ${c} não vazio`, r.length > 200);
  const ruins = [...r.matchAll(/\.\.\.card[^}]{0,80}padding: "\d+px (\d+)px/g)].filter((m) => Number(m[1]) > 16);
  ok(`${c}: sem padding lateral de cartão > 16`, ruins.length === 0);
}
ok("30 usos de CARD_PAD_X", (app.match(/\$\{CARD_PAD_X\}px/g) || []).length === 30);

// parte 3 — botão de saída
const b = recorte("BlocoBorisIA");
ok("BlocoBorisIA recorte", b.length > 200);
ok("disabled={semLivres}", b.includes("disabled={semLivres}"));
ok("aria-disabled", b.includes('aria-disabled={semLivres ? "true" : undefined}'));
ok("opacity 0.6", b.includes("opacity: semLivres ? 0.6 : 1"));
ok("cursor not-allowed", b.includes('cursor: semLivres ? "not-allowed" : "pointer"'));
ok("cor textFaint", b.includes("color: semLivres ? T.textFaint : T.negative"));
const iS = b.indexOf("ctx.A.openSell(p.t)");
const bIni = b.lastIndexOf("<button", iS);
const bFim = b.indexOf("</button>", iS);
const btnSaida = iS < 0 ? "" : b.slice(bIni, bFim);
ok("botão de saída: minHeight 44", btnSaida.includes("minHeight: 44"));
ok("botão de saída: onClick undefined sem livres", btnSaida.includes("onClick={semLivres ? undefined : () => ctx.A.openSell(p.t)}"));
ok("texto da saída inalterado", b.includes('cartaoPosicaoTxt(modo, semLivres ? "saida_sem_livres" : "saida")'));
ok("motivo lastro", b.includes('"saida_motivo_lastro"'));
const iP = b.indexOf("ctx.openStopAlvo(p.t)");
const pIni = b.lastIndexOf("<button", iP);
const pFim = b.indexOf("</button>", iP);
const btnPlano = iP < 0 ? "" : b.slice(pIni, pFim);
ok("botão de plano existe e sem disabled", btnPlano !== "" && !/(?<![-\w])disabled=/.test(btnPlano));

if (falhas) { console.error(falhas + " falha(s)"); process.exit(1); }
console.log("test_ui_onda_g: ok");
