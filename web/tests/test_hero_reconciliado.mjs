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
// REVERSÃO DELIBERADA (2026-08-09). Este guardião travava
// `decM = rotuloDec || (kp.recomendacao …)` — a manchete caía na recomendação
// da IA quando não havia plano determinístico. O Radar NUNCA teve esse
// fallback: lá a manchete é sempre `decisaoDoModo(r, operador)`. Resultado: o
// mesmo ativo, no mesmo lugar da tela, saía de fontes diferentes conforme a
// aba — e o usuário lia uma recomendação aqui e outra ali.
// A regra passa a ser: o motor decide, a IA explica (também é o que o
// guardrail regulatório pede). Sem plano, a ausência é DITA.
ok("manchete única: decM vem SÓ do motor determinístico", /const decM = rotuloDec \|\| null;/.test(app));
ok("sem plano, a ausência é dita e não preenchida pela IA", /Sem leitura do motor para este ativo agora/.test(app));
ok("manchete rotula DECISÃO DA MESA (operador) e mostra decM", /"DECISÃO DA MESA"/.test(app) && /fontWeight: 800[^}]*\}\}>\{decM\}</.test(app));

// confluência/fundamento como chips (insumos), não vereditos
ok("confluência é chip de análise", /chip\("confluência"/.test(app));
ok("fundamento é chip de análise", /chip\("fundamento"/.test(app));
ok("direção/convicção/qualidade em chips", /chip\("direção"/.test(app) && /chip\("convicção"/.test(app) && /chip\("qualidade"/.test(app));

// não pode mais existir o veredito concorrente antigo (pill tier+decisão + KpiBlock no card)
ok("removida a pill antiga tier+confluência ao lado da decisão", !/\{tierDot\} \{tierLabel\}\{sc \? " · "/.test(app));
ok("KpiBlock não é mais renderizado no card do ativo", !/an\.kpis && <KpiBlock/.test(app));

// posição no risco: régua reusada + acesso ao candlestick
// A caption aceita string OU nó (a camada de entendimento sublinha o termo
// no card único) — o contrato aqui é a RÉGUA reusada, não a forma da prop.
const reguas = (app.match(/caption=\{?(<span style=\{SUBLINHADO\}>)?"?POSIÇÃO NO RISCO/g) || []).length;
ok("régua POSIÇÃO NO RISCO reusada também no hero (≥2 usos)", reguas >= 2);
ok("acesso ao candlestick por botão (velas → openTech, com guarda)", /onClick=\{\(\) => A\.openTech && A\.openTech\(t\)\}[\s\S]{0,240}Abrir gráfico de velas/.test(app));

// qa/49 (v11, incremento 1): card único <AtivoCard> — a watchlist renderiza
// pelo componente (fonte única), não mais inline. Próximas abas herdam o mesmo.
ok("AtivoCard é o componente único do ativo", /function AtivoCard\(\{ vm/.test(app));
ok("watchlist renderiza via <AtivoCard vm=…>", /<AtivoCard key=\{t\} vm=\{\{/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
