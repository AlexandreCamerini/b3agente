// C-06 (REPORT-01) — Guardião de `resumoOperacao(h)` (finance.js, escopo
// reduzido): uma frase em português simples por operação EXECUTADA já
// existente no HistoricoScreen. Função pura, determinística, sem inventar
// dado (CLAUDE.md princípio 4/5) — retorna `null` quando falta dado.
// Metade unidade (importa finance.js) + metade estática (grep de App.jsx),
// mesmo formato dos demais guardiões deste plano.
// Roda sem build: `node web/tests/test_c06_resumo_operacao.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { resumoOperacao } from "../src/finance.js";

const here = dirname(fileURLToPath(import.meta.url));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- unidade: resumoOperacao(h) --------------------------------------------

ok("COMPRA executada",
  resumoOperacao({ type: "COMPRA", t: "PETR4", qty: 100, price: 32.5, status: "executada" })
  === "Comprou 100 PETR4 a R$ 32,50.");

ok("VENDA executada com lucro (manual, sem sufixo de motivo)",
  resumoOperacao({ type: "VENDA", t: "PETR4", qty: 100, price: 35, pnl: 250, motivo: "manual", status: "executada" })
  === "Vendeu 100 PETR4 a R$ 35,00, com lucro de R$ 250,00.");

ok("VENDA executada com prejuízo E motivo 'stop'",
  resumoOperacao({ type: "VENDA", t: "VALE3", qty: 50, price: 60, pnl: -120.5, motivo: "stop", status: "executada" })
  === "Vendeu 50 VALE3 a R$ 60,00 no stop, com prejuízo de R$ 120,50.");

ok("VENDA com motivo 'alvo'",
  resumoOperacao({ type: "VENDA", t: "ITUB4", qty: 200, price: 28.9, pnl: 340, motivo: "alvo", status: "executada" })
  === "Vendeu 200 ITUB4 a R$ 28,90 no alvo, com lucro de R$ 340,00.");

ok("VENDA com motivo 'vencimento'",
  resumoOperacao({ type: "VENDA", t: "BBAS3", qty: 10, price: 1234.5, pnl: -5, motivo: "vencimento", status: "executada" })
  === "Vendeu 10 BBAS3 a R$ 1.234,50 no vencimento, com prejuízo de R$ 5,00.");

ok("VENDA sem pnl (defensivo — motor não deveria produzir), com motivo",
  resumoOperacao({ type: "VENDA", t: "PETR4", qty: 100, price: 32.5, pnl: null, motivo: "stop", status: "executada" })
  === "Vendeu 100 PETR4 a R$ 32,50 no stop.");

ok("entrada rejeitada → null",
  resumoOperacao({ type: "VENDA", t: "PETR4", qty: 100, price: 32.5, pnl: -10, status: "rejeitada", motivo: "saldo insuficiente" })
  === null);

ok("entrada LEGADA sem `status` conta como executada → frase gerada",
  resumoOperacao({ type: "COMPRA", t: "PETR4", qty: 100, price: 32.5 })
  === "Comprou 100 PETR4 a R$ 32,50.");

ok("price nulo → null",
  resumoOperacao({ type: "COMPRA", t: "PETR4", qty: 100, price: null, status: "executada" })
  === null);

ok("price NaN → null",
  resumoOperacao({ type: "COMPRA", t: "PETR4", qty: 100, price: NaN, status: "executada" })
  === null);

ok("qty ausente → null",
  resumoOperacao({ type: "COMPRA", t: "PETR4", price: 32.5, status: "executada" })
  === null);

ok("type desconhecido → null (guard clause)",
  resumoOperacao({ type: "SPLIT", t: "PETR4", qty: 100, price: 32.5, status: "executada" })
  === null);

ok("h ausente → null", resumoOperacao(undefined) === null);
ok("h inválido (string) → null", resumoOperacao("não é objeto") === null);

// ---- estático: HistoricoScreen usa resumoOperacao com a gramática certa ---
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

ok("resumoOperacao está no import nomeado de ./finance.js",
  /import \{[^}]*\bresumoOperacao\b[^}]*\} from "\.\/finance\.js";/.test(app));

const iniHistorico = app.indexOf("function HistoricoScreen(");
const fimHistorico = app.indexOf("\nfunction ", iniHistorico + 10);
if (iniHistorico < 0) throw new Error("função HistoricoScreen não encontrada em App.jsx — re-grep necessário.");
const blocoHistorico = app.slice(iniHistorico, fimHistorico > iniHistorico ? fimHistorico : undefined);

ok("o bloco novo está dentro de HistoricoScreen (chama resumoOperacao)", blocoHistorico.includes("resumoOperacao("));
ok("o bloco usa T.textMuted", /T\.textMuted/.test(blocoHistorico));
// isola só o trecho do bloco de resumo (não a tabela inteira, que também usa
// T.textMuted em outros lugares) para garantir que ESSE bloco não usa T.warn.
const iniBlocoResumo = blocoHistorico.indexOf("resumo && (");
const trechoResumo = iniBlocoResumo === -1 ? "" : blocoHistorico.slice(iniBlocoResumo, blocoHistorico.indexOf(")}", iniBlocoResumo));
ok("o bloco de resumo NÃO usa T.warn", trechoResumo.length > 0 && !/T\.warn/.test(trechoResumo));
ok("o bloco é condicionado a !rejeitada", /!rejeitada\s*&&\s*resumo/.test(blocoHistorico));
ok("a linha 'Rejeitada: {h.motivo}' continua presente e intocada", blocoHistorico.includes("Rejeitada: {h.motivo}"));

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DE C-06 (RESUMO DE OPERAÇÃO) PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
