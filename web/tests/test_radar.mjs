// BLOCO 3 — trava o wiring do Radar no frontend e o guardrail de linguagem:
//  • DISCLAIMERS.radar existe, é educacional e não recomenda operação;
//  • api.js expõe scan() apontando para /api/scan com period na query;
//  • persistence.js expõe scan() nos DOIS stores (mesma interface — invariante);
//  • App.jsx tem a aba/tela Radar, usa o período da config (nunca hardcoded),
//    exibe o disclaimer e o período em uso, e a UI não contém linguagem
//    imperativa de operação ("compre", "venda", "entre agora").
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { DISCLAIMERS } from "../src/disclaimers.js";

const here = dirname(fileURLToPath(import.meta.url));
const src = (f) => readFileSync(join(here, "..", "src", f), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const IMPERATIVE = /\b(compre|venda|entre agora|compra já|venda já)\b/i;

// 1) disclaimer na fonte única
ok("DISCLAIMERS.radar existe", typeof DISCLAIMERS.radar === "string" && DISCLAIMERS.radar.length > 40);
ok("DISCLAIMERS.radar menciona 'sem recomendação'", /sem qualquer recomenda/i.test(DISCLAIMERS.radar));
ok("DISCLAIMERS.radar sem imperativo", !IMPERATIVE.test(DISCLAIMERS.radar));

// 2) camada de API
const apiSrc = src("api.js");
ok("api.js expõe scan()", /scan:\s*\(period\)/.test(apiSrc));
ok("api.scan chama /api/scan", apiSrc.includes('"/api/scan"'));
ok("api.scan envia ?period=", /\/api\/scan.*period=/.test(apiSrc));

// 3) invariante dos dois stores: mesma interface
const persistSrc = src("persistence.js");
const scanDefs = persistSrc.match(/scan[:(]/g) || [];
ok("persistence.js expõe scan nos dois stores", scanDefs.length >= 2);

// 4) App.jsx: aba + tela + período da config + disclaimer
const appSrc = src("App.jsx");
ok("aba radar na navegação", /\[\s*"radar",\s*"Radar"\s*\]/.test(appSrc));
ok("ícone radar no NavIcon", /radar:\s*<>/.test(appSrc));
ok("RadarScreen definida", appSrc.includes("function RadarScreen"));
ok("RadarScreen renderizada na aba", /tab === "radar" && <RadarScreen/.test(appSrc));
ok("período vem da config (candlePeriod)", /RadarScreen[\s\S]{0,600}candlePeriod/.test(appSrc));
ok("período em uso exibido na tela", appSrc.includes("PERÍODO EM USO"));
ok("tela usa DISCLAIMERS.radar", appSrc.includes("DISCLAIMERS.radar"));
ok("varre via store.scan (não bate na api direto)", /store\.scan\(/.test(appSrc));

// 5) guardrail de linguagem na tela Radar (trecho da RadarScreen até a Config)
const radarChunk = appSrc.slice(appSrc.indexOf("function RadarScreen"), appSrc.indexOf("function ConfigScreen"));
ok("trecho da RadarScreen localizado", radarChunk.length > 500);
ok("RadarScreen sem linguagem imperativa", !IMPERATIVE.test(radarChunk));
ok("score rotulado como intensidade", /INTENSIDADE DE SINAIS/.test(radarChunk));

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DO RADAR (WIRING) PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
