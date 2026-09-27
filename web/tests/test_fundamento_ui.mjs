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

// REVERSÃO DELIBERADA (2026-09-26, Fase 42, CHIP-01): FundamentoChip apagado
// — SinalChip peso="contexto" (via LinhaContexto) é a receita única de chip
// de sinal; a GARANTIA original ("chip de fundamento com score A/B/C, sem
// score não renderiza") é preservada, só a implementação mudou.
// 1) componente de contexto que renderiza o fundamento existe.
ok("LinhaContexto (SinalChip label=\"FUNDAMENTO\") definida", /function LinhaContexto\(/.test(app));
ok("FundamentoTabela (métricas) definida", /function FundamentoTabela\(/.test(app));

// REVERSÃO DELIBERADA (2026-09-26, Fase 42, HIER-02): o fundamento no Radar
// não é mais um chip solto na linha antiga — chega via radarVm.sc.fundamento
// e o AtivoCard passa fundamentoCard para LinhaContexto (mesmo componente da
// Watchlist, mesma ordem de leitura).
// 2) fundamento no CARD do Radar: subconjunto explícito de `sc` + fiação do AtivoCard.
ok("radarVm.sc leva fundamento: r.fundamento (subconjunto explícito, ADR-017 Bloco 3)",
  /sc: \{[^}]*fundamento: r\.fundamento/.test(app));
ok("AtivoCard passa fundamento={fundamentoCard} para LinhaContexto",
  /<LinhaContexto regime=\{sc \? sc\.regime : null\} fundamento=\{fundamentoCard\}/.test(app));

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

// REVERSÃO DELIBERADA (2026-09-26, Fase 42, D-16): a GARANTIA "sem cobertura
// não inventa chip" sobrevive — agora expressa como guarda `score &&` em
// LinhaContexto e `f.score &&` em FundamentoTabela (D-16 preservado).
// 6) score sem cobertura NÃO inventa: nenhum dos dois lugares renderiza sem score.
const lc = app.slice(app.indexOf("function LinhaContexto("), app.indexOf("function PlanoOperacionalBloco("));
ok("LinhaContexto só renderiza o chip de fundamento com score && (sem cobertura, sem chip)",
  /\{score && \(/.test(lc));
const ftBody = app.slice(app.indexOf("function FundamentoTabela("), app.indexOf("function LabeledList("));
ok("FundamentoTabela só renderiza o chip de fundamento com f.score && (mesma guarda, sem receita paralela)",
  /\{f\.score && <SinalChip peso="contexto"/.test(ftBody));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
