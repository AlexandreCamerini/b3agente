// qa/49 (v11, pedido do Alex) — Guardião do HERO RECONCILIADO: o card do ativo
// tem UMA manchete de decisão (a da mesa/plano, com fallback p/ a recomendação da
// IA), e confluência/setup/fundamento viram INSUMOS (chips), nunca vereditos
// concorrentes. Régua de posição reusada; acesso ao candlestick por botão.
// Roda sem build: `node web/tests/test_hero_reconciliado.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// manchete única
ok("manchete única: decM = decisão do plano OU recomendação da IA", /const decM = rotuloDec \|\| \(kp\.recomendacao/.test(app));
ok("manchete rotula DECISÃO DA MESA (operador) e mostra decM", /"DECISÃO DA MESA"/.test(app) && /fontWeight: 800[^}]*\}\}>\{decM\}</.test(app));

// confluência/fundamento como chips (insumos), não vereditos
ok("confluência é chip de análise", /chip\("confluência"/.test(app));
ok("fundamento é chip de análise", /chip\("fundamento"/.test(app));
ok("direção/convicção/qualidade em chips", /chip\("direção"/.test(app) && /chip\("convicção"/.test(app) && /chip\("qualidade"/.test(app));

// não pode mais existir o veredito concorrente antigo (pill tier+decisão + KpiBlock no card)
ok("removida a pill antiga tier+confluência ao lado da decisão", !/\{tierDot\} \{tierLabel\}\{sc \? " · "/.test(app));
ok("KpiBlock não é mais renderizado no card do ativo", !/an\.kpis && <KpiBlock/.test(app));

// posição no risco: régua reusada + acesso ao candlestick
const reguas = (app.match(/caption="POSIÇÃO NO RISCO"/g) || []).length;
ok("régua POSIÇÃO NO RISCO reusada também no hero (≥2 usos)", reguas >= 2);
ok("acesso ao candlestick por botão (velas → openTech)", /aria-label="Abrir gráfico de velas"[\s\S]{0,220}A\.openTech\(t\)|onClick=\{\(\) => A\.openTech\(t\)\}[\s\S]{0,220}Abrir gráfico de velas/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
