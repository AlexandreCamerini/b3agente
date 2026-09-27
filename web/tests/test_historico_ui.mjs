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

// Corpo de função top-level (mesma convenção de test_radar_leitura_rapida.mjs).
function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(appSrc);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < appSrc.length; i++) {
    if (appSrc[i] === "{") depth++;
    else if (appSrc[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return appSrc.slice(m.index, i);
}

// ---- recorte: HISTORICO_PILL_STYLE + function HistoricoPill { ... } -------
const iniRecorte = appSrc.indexOf("const HISTORICO_PILL_STYLE");
const fimRecorte = appSrc.indexOf("function RadarScreen({ ctx })");
const recorte = (iniRecorte > 0 && fimRecorte > iniRecorte) ? appSrc.slice(iniRecorte, fimRecorte) : "";
ok("recorte de HistoricoPill não veio vazio (âncoras encontradas)", recorte.length > 200);
if (recorte.length <= 200) {
  console.log("\n1 falha(s) — recorte vazio, guardião não pode continuar");
  process.exit(1);
}

// ---- recorte: corpo de SinalChip (Fase 42, CHIP-01) — o ramo peso="contexto"
// passou a carregar a borda/glifo/aria-label que antes viviam em HistoricoPill.
// REVERSÃO DELIBERADA (2026-09-26, Fase 42, CHIP-01): o pill passou a ser
// SinalChip peso contexto; contrato de cor/borda/aria idêntico, só mudou de
// casa — as asserções §3(glifo)/§5/§7 abaixo reancoram para este recorte.
const sinalChip = functionBody("SinalChip") || "";
ok("corpo de SinalChip encontrado (âncora para glifo/borda/aria)", sinalChip.length > 200);

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

// ---- 3) mapa de estilo: REVERSÃO DELIBERADA (2026-09-26, Fase 42,
//         COR-01/D-03/D-04): o contrato positive/negative do 08-UI-SPEC foi
//         substituído; a garantia "elegibilidade é fato, não cor de marca"
//         (sem T.accent) permanece. inelegível vira âmbar de honestidade de
//         dado (T.warn/T.warnTint10, fora do canal de VENDER/prejuízo);
//         elegível vira neutro forte, sem verde. ---------------------------
ok("elegivel mapeia para [T.textPrimary, \"transparent\"] (neutro, sem verde)",
  /elegivel:\s*\[T\.textPrimary,\s*"transparent"\]/.test(recorte));
ok("inelegivel mapeia para [T.warn, T.warnTint10] (âmbar de honestidade de dado, fora do canal de VENDER/prejuízo)",
  /inelegivel:\s*\[T\.warn,\s*T\.warnTint10\]/.test(recorte));
ok("HistoricoPill nunca usa T.accent (elegibilidade é fato, não cor de marca/modo)",
  !recorte.includes("T.accent"));
// SC#1 do ROADMAP: HISTORICO_PILL_STYLE (só o objeto, até o primeiro `};`)
// não referencia T.positive nem T.negative.
const iniObjStyle = recorte.indexOf("const HISTORICO_PILL_STYLE");
const fimObjStyle = recorte.indexOf("};", iniObjStyle);
const objStyle = (iniObjStyle >= 0 && fimObjStyle > iniObjStyle) ? recorte.slice(iniObjStyle, fimObjStyle + 2) : "";
ok("recorte do objeto HISTORICO_PILL_STYLE não veio vazio", objStyle.length > 50);
ok("HISTORICO_PILL_STYLE não referencia T.positive nem T.negative (ROADMAP SC#1)",
  !objStyle.includes("T.positive") && !objStyle.includes("T.negative"));
// glifo ✓ decorativo no ramo elegivel, aria-hidden (o texto acessível segue
// vindo de historicoTxt/ariaLabel, nunca do glifo). REVERSÃO DELIBERADA
// (Fase 42, CHIP-01): o glifo mudou de casa, de HistoricoPill para o corpo de
// SinalChip — reancorado em `sinalChip`, não em `recorte`.
ok("ramo elegivel de SinalChip renderiza glifo ✓ decorativo com aria-hidden",
  /estado === "elegivel" && <span aria-hidden="true">✓ <\/span>/.test(sinalChip));

// ---- 4) insuficiente e nunca_medido usam o par neutro, NUNCA T.negative --
ok("insuficiente mapeia para o par neutro [T.textFaint, T.bgBase]",
  /insuficiente:\s*\[T\.textFaint,\s*T\.bgBase\]/.test(recorte));
ok("nunca_medido mapeia para o par neutro [T.textFaint, T.bgBase]",
  /nunca_medido:\s*\[T\.textFaint,\s*T\.bgBase\]/.test(recorte));

// ---- 5) aposentado é o ÚNICO estado com `dashed` no estilo ---------------
// REVERSÃO DELIBERADA (Fase 42, CHIP-01): a borda condicional por estado
// migrou de `pillStyle.border = ...` (HistoricoPill) para a expressão `border`
// dentro do corpo de SinalChip — reancorado em `sinalChip`.
ok("aposentado recebe borda tracejada (1px dashed + T.borderDashed) no corpo de SinalChip",
  /estado === "aposentado" \? "1px dashed " \+ T\.borderDashed/.test(sinalChip));
const ocorrenciasDashed = (sinalChip.match(/dashed/g) || []).length;
ok("'dashed' aparece exatamente 1 vez no corpo de SinalChip (só no ramo aposentado)", ocorrenciasDashed === 1);

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
// REVERSÃO DELIBERADA (Fase 42, CHIP-01): `role="img" aria-label={ariaLabel}`
// agora vive no ramo peso="contexto" de SinalChip; HistoricoPill só precisa
// repassar `estado`/`value`/`ariaLabel` ao SinalChip, sem receita própria.
ok("o corpo de SinalChip carrega role=\"img\" e aria-label", /role="img" aria-label=\{ariaLabel\}/.test(sinalChip));
ok("HistoricoPill repassa estado/value/ariaLabel para <SinalChip peso=\"contexto\">, sem pill paralelo",
  recorte.includes('<SinalChip peso="contexto" estado={estado}'));

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
