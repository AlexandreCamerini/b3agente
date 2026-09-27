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

function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(app);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < app.length; i++) {
    if (app[i] === "{") depth++;
    else if (app[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return app.slice(m.index, i);
}
const sinalChip = functionBody("SinalChip") || "";

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
ok("manchete rotula DECISÃO DA MESA (operador) e mostra decM (agora via SinalChip peso=primario)",
  /<SinalChip peso="primario" decision=\{decM\}/.test(app)
  && sinalChip.includes("fontWeight: 800")
  && /\{decision\}/.test(sinalChip));

// REVERSÃO DELIBERADA (2026-09-26, Fase 42, HIER-01/CHIP-01/D-02): manchete
// virou SinalChip primario; confluência saiu dos chips para o anel; chips da
// IA saíram do card (a IA explica no detalhe técnico, não disputa a manchete).
ok("confluência vira anel na manchete (ring={anel} no AtivoCard + rotuloAnel( no AtivoCard)",
  /ring=\{anel\}/.test(app) && /rotuloAnel\(/.test(app));
ok("fundamento é chip de contexto (label=\"FUNDAMENTO\" em LinhaContexto)",
  functionBody("LinhaContexto").includes('label="FUNDAMENTO"'));
ok("prova negativa D-02: corpo do AtivoCard sem kp. (chips da IA saíram do card)",
  !/kp\./.test(functionBody("AtivoCard")));

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
