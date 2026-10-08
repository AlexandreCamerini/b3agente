// Onda E (2026-10-08) — quick 261008-dgv. Regressões vistas no aparelho:
// (1) valores monetários/percentuais nunca quebram linha; (2) "1 dia" no singular e
// a nota "sem piso" não se repete no rodapé da escada (o card já a traz).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { opcoesEscadaTxt } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const ler = (p) => readFileSync(join(here, "..", "src", p), "utf8");
let falhas = 0;
const ok = (n, c) => { if (!c) { falhas++; console.error("FALHOU:", n); } else console.log("ok:", n); };

const app = ler("App.jsx");
const hub = ler("opcoes/HubOpcoes.jsx");
const esc = ler("opcoes/EscadaObjetivo.jsx");

// parte 1 — nowrap
ok("preço do card de ativo: container nowrap + flexShrink 0",
  /textAlign: "right", fontFamily: MONO, minWidth: "72px", flexShrink: 0, whiteSpace: "nowrap"/.test(app));
const g = app.slice(app.indexOf("function GradeConta"), app.indexOf("function LinhaChamadaOpcoes"));
ok("grade de métricas (Perda máx.): valor nowrap", /fmt\(cel\)\}<\/span>/.test(g) && /whiteSpace: "nowrap"[^}]*\}\}>\{fmt\(cel\)\}/.test(g));
ok("card de carteira das Opções: vigias nowrap", /whiteSpace: "nowrap", flexShrink: 0 \}\}>\{opcoesEscadaTxt\(mode, "card_vigias"/.test(hub));
const i = app.indexOf("em carteira · {pos.qty}");
ok("faixa 'em carteira': resultado nowrap", /whiteSpace: "nowrap", flexShrink: 0[^}]*\}\}>\{moneySigned\(pnl\)\}/.test(app.slice(i, i + 600)));

// parte 2 — plural e linha duplicada
for (const modo of ["educacional", "operador"]) {
  ok(`plural 1 dia (${modo})`, opcoesEscadaTxt(modo, "vencimento_dia", { dias: 1 }) === "1 dia");
  ok(`plural n dias (${modo})`, opcoesEscadaTxt(modo, "vencimento_dias", { dias: 3 }) === "3 dias");
}
ok("seletor usa singular para n=1", /v\.dias === 1 \? "vencimento_dia" : "vencimento_dias"/.test(esc));
ok("rodapé duplicado de nota_sem_piso removido (o card traz a coluna)", !/tx\("nota_sem_piso"\)/.test(esc));

if (falhas) { console.error(falhas + " falha(s)"); process.exit(1); }
console.log("test_ui_onda_e: ok");
