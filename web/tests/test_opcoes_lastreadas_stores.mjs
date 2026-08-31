// Fase 14 (opções lastreadas — venda coberta/put de proteção), Plano 05.
//
// Guardião do espelho deviceStore × store.py da mecânica lastreada e da
// fonte única de qtyLivre. Estilo dos guardiões existentes deste repositório:
// leitura estática de web/src/persistence.js e web/src/finance.js + asserções
// sobre o texto (mesmo padrão de test_fase3_paridade_stores_generica.mjs e
// test_rr_min_fonte_unica.mjs) — não importa persistence.js em runtime (o
// módulo escolhe serverStore/deviceStore por Capacitor.isNativePlatform, que
// não tem um mock trivial de encaixar num teste puramente estático).
//
// Roda sem build: `node web/tests/test_opcoes_lastreadas_stores.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const srcPersistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const srcFinance = readFileSync(join(here, "..", "src", "finance.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// --------------------------------------------------- localizar os dois blocos
const iServer = srcPersistence.indexOf("function serverStore()");
const iDevice = srcPersistence.indexOf("function deviceStore()");
const iExport = srcPersistence.indexOf("export const store");
if (iServer < 0 || iDevice < 0 || iExport < 0) {
  console.error("FALHOU: persistence.js foi reestruturado — function serverStore()/deviceStore()/export const store não encontrados como esperado");
  process.exit(1);
}
const blocoServer = srcPersistence.slice(iServer, iDevice);
const blocoDevice = srcPersistence.slice(iDevice, iExport);

// ------------------------------------------- (1) os três métodos nos DOIS lados
const METODOS = ["optionsProposta", "optionsAbrirLastreada", "optionsFecharLastreada"];
for (const m of METODOS) {
  ok(`serverStore expõe ${m}`, blocoServer.includes(m));
  ok(`deviceStore expõe ${m}`, blocoDevice.includes(m));
}

// ------------------------------------ (2) ramo local de optionsAbrirLastreada
const iAbrirDevice = blocoDevice.indexOf("async optionsAbrirLastreada(body)");
const iFecharDevice = blocoDevice.indexOf("async optionsFecharLastreada(body)");
ok("deviceStore.optionsAbrirLastreada encontrado", iAbrirDevice >= 0);
ok("deviceStore.optionsFecharLastreada encontrado", iFecharDevice >= 0);
const trechoAbrir = (iAbrirDevice >= 0 && iFecharDevice > iAbrirDevice)
  ? blocoDevice.slice(iAbrirDevice, iFecharDevice)
  : "";
ok("ramo local de optionsAbrirLastreada credita o caixa (doc.cash = +(doc.cash + )",
  /doc\.cash\s*=\s*\+\(doc\.cash\s*\+/.test(trechoAbrir));
ok("ramo local de optionsAbrirLastreada debita o caixa (doc.cash = +(doc.cash - )",
  /doc\.cash\s*=\s*\+\(doc\.cash\s*-/.test(trechoAbrir));
ok("ramo local de optionsAbrirLastreada escreve qtyTravada (trava do lastro)",
  /qtyTravada\s*=/.test(trechoAbrir));

// ------------------------------------------------------ (3) FONTE ÚNICA: qtyLivre
ok("finance.js exporta qtyLivre", /export function qtyLivre\(/.test(srcFinance));
ok("persistence.js IMPORTA qtyLivre de ./finance.js",
  /import\s*\{[^}]*qtyLivre[^}]*\}\s*from\s*["']\.\/finance\.js["']/.test(srcPersistence));

const usosQtyLivre = (srcPersistence.match(/\bqtyLivre\s*\(/g) || []).length;
ok(`persistence.js usa qtyLivre em pelo menos dois pontos (achou ${usosQtyLivre} chamada(s))`, usosQtyLivre >= 2);

// negativa: nenhuma subtração crua "qty - ... qtyTravada" escrita à mão —
// tolerante a espaço e a `|| 0` no meio (ex.: `qty - (pos.qtyTravada || 0)`).
const subtracaoCrua = /\bqty\s*-\s*\(?[^)\n]{0,40}qtyTravada/.test(srcPersistence);
ok("persistence.js NÃO contém subtração crua 'qty - ... qtyTravada' (só via qtyLivre)", !subtracaoCrua);

// negativa: nenhum helper privado _qtyLivre (uma terceira aritmética de
// "livre" é exatamente o que a fonte única existe para impedir).
ok("persistence.js NÃO define um helper privado _qtyLivre", !/_qtyLivre\s*[=(]/.test(srcPersistence));

// ------------------------------------------------------ (4) ciclo local — ramo lastro
const iCycle = blocoDevice.indexOf("async cycle()");
ok("deviceStore.cycle encontrado", iCycle >= 0);
const trechoCycle = iCycle >= 0 ? blocoDevice.slice(iCycle) : "";
const iLastroBranch = trechoCycle.indexOf("pos.lastro && typeof pos.lastro");
const iStopAlvoLegado = trechoCycle.indexOf("const breachStop = pos.stop != null && price <= pos.stop;\n          const hitAlvo = pos.alvo != null && price >= pos.alvo;\n          if (breachStop || hitAlvo) {");
ok("ciclo local tem ramo `lastro` no laço de optionPositions", iLastroBranch >= 0);
ok("ramo `lastro` do ciclo vem ANTES do bloco de stop/alvo legado de opção",
  iLastroBranch >= 0 && iStopAlvoLegado >= 0 && iLastroBranch < iStopAlvoLegado);

// ------------------------------------------- (5) nenhum dos três passa por sync.mutate
for (const m of METODOS) {
  ok(`sync.mutate("${m}"` + ") não existe em persistence.js (chamada direta, nunca fila otimista)",
    !srcPersistence.includes(`sync.mutate("${m}"`));
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
