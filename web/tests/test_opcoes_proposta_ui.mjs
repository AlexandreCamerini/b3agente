// Fase 14 (Plano 06) — Guardião da PROPOSTA LASTREADA na UI: manchete do
// motor (guardrail CVM), split de modo (Estudo explica sem CTA, Operador
// executa), cadeia completa preservada abaixo, gate de dormência, confirmação
// da trava e remoção do par morto setOptionStop/setOptionAlvo (D-1).
// Roda sem build: `node web/tests/test_opcoes_proposta_ui.mjs`.
//
// Task 1 (copy.js): guardião das chaves de rótulo/confirmação das operações
// lastreadas. Task 2/3 completam este arquivo com as asserções de UI
// (leitura estática de App.jsx) depois que o componente existir.
import { COPY } from "../src/copy.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- Task 1: copy.js — chaves das operações lastreadas -----------------
const CHAVES_LASTREADAS = [
  "eyebrowPropostaCall", "eyebrowPropostaPut", "ctaVendaCoberta", "ctaPutProtecao",
  "ctaFecharLastreada", "confirmAbrirCoberta", "confirmFecharCoberta",
  "verCadeiaCompleta", "propostaIndisponivelDegradada", "propostaVaziaTitulo",
];
ok("chaves das operações lastreadas existem nos dois ramos",
  CHAVES_LASTREADAS.every((k) => k in COPY.estudo) && CHAVES_LASTREADAS.every((k) => k in COPY.operador));

ok("COPY.estudo.ctaVendaCoberta não contém vocabulário de ordem",
  !/vender|comprar/i.test(COPY.estudo.ctaVendaCoberta(3, "PETR4", "38,50", "185,00")));
ok("COPY.estudo.ctaPutProtecao não contém vocabulário de ordem",
  !/vender|comprar/i.test(COPY.estudo.ctaPutProtecao(3, "PETR4", "38,50", "185,00")));

const confirmOperador = COPY.operador.confirmAbrirCoberta(2, "PETR4", 200);
ok("confirmAbrirCoberta (operador) declara a trava e a quantidade", confirmOperador.includes("trava") && confirmOperador.includes("200"));

// asserção negativa: nenhuma chave nova compõe a manchete do motor —
// "Se você tivesse" é texto do backend (skill_ref.opcoes_lastreadas_txt),
// nunca duplicado no copy.js.
const todosOsValores = [...Object.values(COPY.estudo), ...Object.values(COPY.operador)]
  .map((v) => (typeof v === "function" ? String(v("X", "Y", "Z", "W")) : String(v)))
  .join(" | ");
ok("nenhuma chave de copy.js carrega a manchete do motor (\"Se você tivesse\")", !todosOsValores.includes("Se você tivesse"));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram (Task 1 — copy.js)");
