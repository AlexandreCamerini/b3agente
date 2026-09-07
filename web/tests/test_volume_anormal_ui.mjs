// 2026-09-07 — guardião da célula "VOLUME x MÉDIA (20)" no card técnico.
//
// Contrato: (1) o estado exibido vem SÓ de summary.volState (motor), a UI não
// reclassifica; (2) a cor segue o que o PREÇO fez (volDirecao), nunca o
// tamanho do volume; (3) sem estado a célula declara "sem dado", não herda;
// (4) nenhum texto da UI rotula causa ("baleia") — o dado é agregado, sem
// participante; (5) o modo exemplo (demo.js) espelha os mesmos campos e
// cortes do backend, para o card não mostrar "—" para sempre no demo.
// Roda sem build: `node web/tests/test_volume_anormal_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const demo = readFileSync(join(here, "..", "src", "demo.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok("card tem a célula VOLUME x MÉDIA (20) lendo sm.volRatio20",
   /<IndCell label="VOLUME x MÉDIA \(20\)" value=\{sm\.volRatio20 == null \? null : `\$\{sm\.volRatio20\}×`\}/.test(app));
ok("sub e cor vêm de volSub(sm)/volColor(sm), sem reclassificar na célula",
   /sub=\{volSub\(sm\)\} color=\{volColor\(sm\)\}/.test(app));
ok("volSub usa VOL_STATE_LABEL[sm.volState] — estado do motor, não recalculado",
   /VOL_STATE_LABEL\[sm\.volState\]/.test(app) && !/volRatio20\s*>=\s*2/.test(app));
ok("cor segue o preço (stateColor(sm.volDirecao)), nunca o tamanho do volume",
   /volColor = \(sm\) => \(sm\.volState === "anormal" \|\| sm\.volState === "acima" \? stateColor\(sm\.volDirecao\) : T\.textSecondary\)/.test(app));
ok("sem estado com referência curta declara 'sem dado' em vez de herdar",
   app.includes('"sem dado (referência curta)"'));
ok("nenhum texto da UI rotula causa como baleia/whale",
   !/baleia|whale/i.test(app));

// demo.js espelha os mesmos cortes do backend (indicators.VOL_*)
ok("demo espelha volume relativo: 20 anteriores, atual fora, mínimo 10 de referência",
   /vols\.slice\(Math\.max\(0, n - 21\), Math\.max\(0, n - 1\)\)/.test(demo) && /janela < 10/.test(demo));
ok("demo usa os mesmos cortes 2× / 1,5× / 0,5×",
   /ratio >= 2 \? "anormal" : ratio >= 1\.5 \? "acima" : ratio <= 0\.5 \? "abaixo" : "normal"/.test(demo));
ok("demo injeta volRatio20/volState/volDirecao/volJanela no summary",
   /\.\.\.volumeResumo\(v, c\)/.test(demo));

console.log(fails === 0 ? "TODOS OS TESTES DA UI DE VOLUME ANORMAL PASSARAM" : fails + " TESTE(S) FALHARAM");
process.exit(fails === 0 ? 0 : 1);
