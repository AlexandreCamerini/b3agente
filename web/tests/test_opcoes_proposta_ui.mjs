// Fase 14 (Plano 06) — Guardião da PROPOSTA LASTREADA na UI: manchete do
// motor (guardrail CVM), split de modo (Estudo explica sem CTA, Operador
// executa), cadeia completa preservada abaixo, gate de dormência, confirmação
// da trava e remoção do par morto setOptionStop/setOptionAlvo (D-1).
// Roda sem build: `node web/tests/test_opcoes_proposta_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

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

// ---- Task 3: leitura estática de App.jsx --------------------------------
// A manchete da proposta vem do backend: `p.manchete` é renderizado direto;
// o front nunca compõe a frase (guardrail CVM, T-14-22).
ok("componente PropostaLastreada existe", /function PropostaLastreada\(\{ r, operador, cp, busy, onAbrir, onFechar, posAberta \}\)/.test(app));
ok("PropostaLastreada vem ANTES de OpcoesCamada no arquivo (definição)",
  app.indexOf("function PropostaLastreada") < app.indexOf("function OpcoesCamada"));

const iPL = app.indexOf("function PropostaLastreada");
const iOC = app.indexOf("function OpcoesCamada");
const propostaFn = app.slice(iPL, iOC);

ok("p.manchete é renderizado direto (sem composição)", /\{p\.manchete\}/.test(propostaFn));
ok("front não compõe a manchete (\"Vender \" + variável)", !/"Vender " \+/.test(app));
ok("front não duplica a frase didática (\"Se você tivesse\")", !app.includes("Se você tivesse"));

// A cadeia sobrevive: OpcoesCamada continua renderizada, e <PropostaLastreada
// aparece ANTES de <OpcoesCamada no arquivo (JSX de uso, não só definição) — D-4.
ok("<OpcoesCamada continua renderizada", /<OpcoesCamada/.test(app));
ok("<PropostaLastreada aparece antes de <OpcoesCamada no JSX de uso",
  app.indexOf("<PropostaLastreada") > -1 && app.indexOf("<PropostaLastreada") < app.indexOf("<OpcoesCamada"));

// Split de modo: CTA só sob `operador`; a frase didática só sob a condição
// contrária — Estudo não recebe botão de executar (T-14-23, defesa em UI).
ok("frase didática condicionada a `!operador`", /\{!operador && \([\s\S]{0,120}\{p\.didatica\}/.test(propostaFn));
ok("CTA (<button) condicionado a `operador`", /\{operador && \([\s\S]{0,60}<button/.test(propostaFn));

// Gate de dormência: a chamada de store.optionsProposta está dentro de
// condição que depende de opGate (D-8 — sem gate de liquidez, nenhuma
// requisição extra).
(() => {
  const i = app.indexOf("store.optionsProposta(t)");
  const antes = app.slice(Math.max(0, i - 200), i);
  ok("store.optionsProposta só dispara sob condição de opGate", i > -1 && /if \(opGate && opGate\.liquida\)/.test(antes));
})();

// Confirmação da trava: existe window.confirm com cp.confirmAbrirCoberta no
// caminho da CALL coberta (T-14-24).
ok("window.confirm com cp.confirmAbrirCoberta existe", /window\.confirm\(cp\.confirmAbrirCoberta\(/.test(app));
ok("window.confirm com cp.confirmFecharCoberta existe", /window\.confirm\(cp\.confirmFecharCoberta\(/.test(app));

// Cor da manchete por polaridade: T.positive/T.negative decidido por
// optionType (via isCall), e a MANCHETE nunca usa T.accent (regra do
// UI-SPEC/hero — App.jsx:768-773).
ok("isCall deriva de optionType === \"call\"", /const isCall = p\.optionType === "call";/.test(propostaFn));
ok("cor da manchete decidida por isCall (T.positive/T.negative)", /const cor = isCall \? T\.positive : T\.negative;/.test(propostaFn));
const linhaManchete = (propostaFn.match(/^.*\{p\.manchete\}.*$/m) || [""])[0];
ok("a linha que renderiza a manchete não usa T.accent", !linhaManchete.includes("T.accent"));

// Código morto removido: setOptionStop/setOptionAlvo não aparecem mais em
// App.jsx; putOptionPosition CONTINUA em persistence.js (o agente ainda usa
// o modelo antigo para trailing das posições legadas).
ok("setOptionStop/setOptionAlvo removidos de App.jsx", !/setOptionStop|setOptionAlvo/.test(app));
ok("putOptionPosition permanece em persistence.js", /putOptionPosition/.test(persistence));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
