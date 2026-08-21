// ADR-017 Bloco 3 (Fase 8, Plano 03) — guardião do contrato visual do
// HistoricoPill (elegibilidade medida do melhor setup, no Radar/Watchlist).
//
// Padrão de test_radar_regime_chip.mjs + test_rr_min_fonte_unica.mjs: lê
// App.jsx como TEXTO (sem build, sem DOM) e importa COPY de copy.js. Caminhos
// resolvidos por `new URL(..., import.meta.url)`, nunca relativos ao cwd
// (scripts/executar.sh roda os runners com cwd=web).
//
// Para os mapas de cor, o corpo de HistoricoPill (+ o objeto de estilo que o
// precede, HISTORICO_PILL_STYLE) é recortado do fonte e as asserções rodam
// DENTRO desse recorte — assertar contra o arquivo inteiro daria
// falso-positivo: `T.negative` aparece em dezenas de outros lugares do app.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const appSrc = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- recorte: HISTORICO_PILL_STYLE + function HistoricoPill { ... } -------
const iniRecorte = appSrc.indexOf("const HISTORICO_PILL_STYLE");
const fimRecorte = appSrc.indexOf("function RadarScreen({ ctx })");
const recorte = (iniRecorte > 0 && fimRecorte > iniRecorte) ? appSrc.slice(iniRecorte, fimRecorte) : "";
ok("recorte de HistoricoPill não veio vazio (âncoras encontradas)", recorte.length > 200);
if (recorte.length <= 200) {
  console.log("\n1 falha(s) — recorte vazio, guardião não pode continuar");
  process.exit(1);
}

// ---- 1) App.jsx contém setupHistorico/setupElegivel no `sc` do radarVm ----
const iniRadarVm = appSrc.indexOf("const radarVm = {");
const fimRadarVm = iniRadarVm > 0 ? appSrc.indexOf(";", iniRadarVm) : -1;
const trechoRadarVm = iniRadarVm > 0 ? appSrc.slice(iniRadarVm, fimRadarVm) : "";
ok("radarVm encontrado em App.jsx", iniRadarVm > 0);
ok("sc do radarVm carrega setupHistorico: r.setupHistorico", trechoRadarVm.includes("setupHistorico: r.setupHistorico"));
ok("sc do radarVm carrega setupElegivel: r.setupElegivel", trechoRadarVm.includes("setupElegivel: r.setupElegivel"));
ok("setupHistorico/setupElegivel estão dentro do objeto `sc:` (não soltos no vm)",
  /sc:\s*\{[^}]*setupHistorico:\s*r\.setupHistorico[^}]*setupElegivel:\s*r\.setupElegivel[^}]*\}/.test(trechoRadarVm));

// ---- 2) linha de chips do Radar renderiza <HistoricoPill DEPOIS do texto
//         de melhorSetup ------------------------------------------------
const idxMelhorSetupRadar = appSrc.indexOf('{r.melhorSetup && <span style={{ fontSize: "11.5px", color: T.textMuted }}>{r.melhorSetup}');
const idxHistoricoPillRadar = appSrc.indexOf("<HistoricoPill historico={r.setupHistorico}");
ok("chip de melhorSetup do Radar encontrado", idxMelhorSetupRadar > 0);
ok("<HistoricoPill.../> wireado no Radar, alimentado por r.setupHistorico/r.setupElegivel", idxHistoricoPillRadar > 0);
ok("HistoricoPill entra DEPOIS do texto de melhorSetup (sinal secundário, nunca antes)",
  idxHistoricoPillRadar > idxMelhorSetupRadar);

// ---- 3) mapa de estilo: elegivel/inelegivel usam positive/negative,
//         nenhum dos dois usa T.accent -----------------------------------
ok("elegivel mapeia para [T.positive, T.positiveTint10]",
  /elegivel:\s*\[T\.positive,\s*T\.positiveTint10\]/.test(recorte));
ok("inelegivel mapeia para [T.negative, T.negativeTint10] (MESMO peso visual do positivo)",
  /inelegivel:\s*\[T\.negative,\s*T\.negativeTint10\]/.test(recorte));
ok("HistoricoPill nunca usa T.accent (elegibilidade é fato, não cor de marca/modo)",
  !recorte.includes("T.accent"));

// ---- 4) insuficiente e nunca_medido usam o par neutro, NUNCA T.negative --
ok("insuficiente mapeia para o par neutro [T.textFaint, T.bgBase]",
  /insuficiente:\s*\[T\.textFaint,\s*T\.bgBase\]/.test(recorte));
ok("nunca_medido mapeia para o par neutro [T.textFaint, T.bgBase]",
  /nunca_medido:\s*\[T\.textFaint,\s*T\.bgBase\]/.test(recorte));

// ---- 5) aposentado é o ÚNICO estado com `dashed` no estilo ---------------
ok("aposentado recebe borda tracejada (1px dashed + T.borderDashed)",
  /if \(estado === "aposentado"\) pillStyle\.border = "1px dashed " \+ T\.borderDashed;/.test(recorte));
const ocorrenciasDashed = (recorte.match(/dashed/g) || []).length;
ok("'dashed' aparece exatamente 1 vez no recorte (só no ramo aposentado)", ocorrenciasDashed === 1);

// ---- 6) nenhum texto de COPY[modo].historico/historicoRotulo aparece
//         literal em App.jsx (o pill lê pelo helper, nunca hardcoda) ------
for (const modo of ["estudo", "operador"]) {
  for (const [chave, valor] of Object.entries(COPY[modo].historico)) {
    ok(`App.jsx não hardcoda COPY.${modo}.historico.${chave}`, !appSrc.includes(valor));
  }
  for (const [chave, valor] of Object.entries(COPY[modo].historicoRotulo)) {
    ok(`App.jsx não hardcoda COPY.${modo}.historicoRotulo.${chave}`, !appSrc.includes(valor));
  }
}

// ---- 7) todo pill carrega aria-label -------------------------------------
ok("o <span> do pill carrega role=\"img\" e aria-label", /role="img" aria-label=\{ariaLabel\}/.test(recorte));

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
