// qa/36 (F10.2) — Guardião: integração fundamento × técnica no cliente,
// fiel ao mock aprovado (qa/mocks/fundamento-tecnica-v1.html) e aos
// princípios do gate (fundamento é filtro de qualidade, NUNCA gatilho; só
// rebaixa a confiança, nunca promove; o plano técnico não muda).
// Roda sem build: `node web/tests/test_fundamento_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// 1) componentes de fundamento existem.
ok("FundamentoChip (score A/B/C) definido", /function FundamentoChip\(/.test(app));
ok("FundamentoTabela (métricas) definida", /function FundamentoTabela\(/.test(app));

// 2) chip no CARD do Radar (ao lado da pill de confiança), lendo r.fundamento.
ok("chip de fundamento no card do Radar", /<FundamentoChip f=\{r\.fundamento\} \/>/.test(app));

// 3) seção Fundamento + nota de rebaixamento no N2 (AnalysisView).
const av = app.slice(app.indexOf("function AnalysisView("), app.indexOf("function hasAnalysis("));
ok("seção Fundamento renderizada no N2", /<FundamentoTabela f=\{an\.fundamento\} \/>/.test(av));
ok("nota de rebaixamento de confiança no N2", /an\.rebaixadoPorFundamento/.test(av) && /Confiança rebaixada/.test(av));

// 4) princípios do gate visíveis na copy da tabela.
const ft = app.slice(app.indexOf("function FundamentoTabela("), app.indexOf("function LabeledList("));
ok("copy: 'filtro de qualidade, não é gatilho'", /não é gatilho de compra/.test(ft));
ok("'sem dado' explícito (nunca inferência)", /sem dado/.test(ft) && /fracPct/.test(app));

// 5) estado do cliente propaga os campos novos (seed + resposta do analyze).
ok("estado carrega fundamento/confiancaFinal/rebaixado (2 pontos de montagem)",
  (app.match(/fundamento: [ar]\.fundamento \|\| null/g) || []).length >= 2
  && (app.match(/rebaixadoPorFundamento: !![ar]\.rebaixadoPorFundamento/g) || []).length >= 2);

// 6) score sem cobertura NÃO inventa: chip retorna null sem score.
ok("FundamentoChip não renderiza sem score (ticker sem cobertura)",
  /if \(!f \|\| !f\.score\) return null;/.test(app));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
