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
// FASE 2 (2.3): scan aceita restrição por tickers (watchlist) — assinatura evoluída
ok("api.js expõe scan(period, tickers, force)", /scan:\s*\(period,\s*tickers,\s*force\)/.test(apiSrc)); // FASE 4 (1.3)
ok("api.scan chama /api/scan", apiSrc.includes('"/api/scan"'));
ok("api.scan envia ?period=", /period=/.test(apiSrc.slice(apiSrc.indexOf("scan:"), apiSrc.indexOf("scan:") + 400)));
ok("api.scan envia ?tickers= (FASE 2)", /tickers=/.test(apiSrc.slice(apiSrc.indexOf("scan:"), apiSrc.indexOf("scan:") + 400)));

// 3) invariante dos dois stores: mesma interface
const persistSrc = src("persistence.js");
const scanDefs = persistSrc.match(/scan[:(]/g) || [];
ok("persistence.js expõe scan nos dois stores", scanDefs.length >= 2);

// 4) App.jsx: aba + tela + período da config + disclaimer
const appSrc = src("App.jsx");
// Rodada final (autorizada): rótulo definitivo "Radar" (id preservado).
// qa/34: o rótulo da aba agora fala a língua do modo — cp.tabRadar
// ("Radar" no Estudo × "Mesa" no Operador), com fallback "Radar".
ok("aba radar na navegação (cp.tabRadar, fallback Radar)", /\[\s*"radar",\s*\(cp && cp\.tabRadar\) \|\| "Radar"\s*\]/.test(appSrc));
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
ok("confluência rotulada na tela", /CONFLU/.test(radarChunk));
ok("veredito educacional renderizado", /r\.veredito/.test(radarChunk));
// qa/34: o título e o corpo da seção vêm da fraseologia do modo
// (comoAnalisaTitulo/comoAnalisaCorpo) — antes "COMO O RADAR ANALISA" era
// hardcoded e o corpo ("veredito é sempre de estudo") vazava para o Operador.
ok("seção 'Como o Radar analisa' presente (via copy.js)", /cp\.comoAnalisaTitulo/.test(radarChunk) && /cp\.comoAnalisaCorpo/.test(radarChunk));
ok("checklist de critérios do setup na tela", /criterios/.test(radarChunk) && /Ver critérios do setup/.test(radarChunk));

// BLOCO D — login persistido (e-mail lembrado + AutoFill do Chaveiro)
ok("e-mail lembrado (loadLastEmail) no App.jsx", appSrc.includes("function loadLastEmail"));
// FASE 8B (N3): o formulário de login foi UNIFICADO (AuthForm) — o contrato
// antigo (saveLastEmail em ≥2 formulários) era o sintoma da duplicação.
// Agora: exatamente 1 ponto de persistência, e as DUAS superfícies (Welcome e
// AuthModal) renderizam o MESMO <AuthForm.
ok("salva e-mail em UM ponto único (AuthForm)", (appSrc.match(/saveLastEmail\(email\)/g) || []).length === 1);
ok("Welcome e AuthModal usam o AuthForm único", (appSrc.match(/<AuthForm ctx=\{ctx\} onDone=/g) || []).length === 2);
ok("AutoFill: autocomplete username no e-mail", appSrc.includes('autoComplete="username"'));
ok("AutoFill: current/new-password na senha", appSrc.includes('current-password') && appSrc.includes('new-password'));
ok("nunca persiste a senha", !/localStorage\.setItem\([^)]*password/i.test(appSrc));

// BLOCO A — diagnóstico de notificações na tela
ok("botão Diagnóstico na Config", appSrc.includes(">Diagnóstico<"));
ok("veredito do diagnóstico interpreta plugin fora do build", appSrc.includes("instalar-iphone.sh"));

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DO RADAR (WIRING) PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
