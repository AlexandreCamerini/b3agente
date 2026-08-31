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

// ---------------------------------------------------------------------------
// REGRESSÃO (Fase 14, Plano 08, Task 2 — SEGUNDO bug real achado ao vivo):
// `radarVm` (RadarScreen) não incluía `cp` — AtivoCard desestrutura `cp` de
// `vm` e repassa incondicionalmente pra <PropostaLastreada>, que lê
// `cp.propostaVaziaTitulo`/`cp.badgeTravada`/etc. sem guarda. Todo card do
// Radar quebrava com "undefined is not an object (evaluating
// 'cp2.propostaVaziaTitulo')". Raiz: AtivoCard é COMPARTILHADO entre duas
// telas (comentário em App.jsx ~3127: "o mesmo card serve Watchlist e
// Radar"), cada uma constrói seu próprio `vm` — a Watchlist (MercadoScreen,
// ~3699) ganhou `cp` no Plano 14-06; o `radarVm` (RadarScreen, ~6334) não.
//
// Isto é a SEGUNDA vez que um campo novo em `vm` fica sem paridade entre os
// dois pontos de construção — a mesma classe do bug já resolvido pelo
// checkpoint anterior (proposta_fechar, backend). O guardião abaixo mede
// estruturalmente (não por lista fixa de nomes) se os campos de `vm` que
// AtivoCard efetivamente LÊ no único trecho que renderiza incondicionalmente
// — o bloco `opGate && opGate.liquida && (...)`, que embala <PropostaLastreada>
// e <OpcoesCamada> — têm paridade entre `MercadoScreen`'s watchlist `vm` e o
// `radarVm` do Radar.
//
// Por que só esse bloco, e não o destructuring inteiro de `vm` (32 campos)?
// Porque a MAIOR parte dos outros campos (rrPos, diasPos, pctCapPos, os,
// buyMeta, expanded, opsOpen, opsSpark, onToggleOps, e o uso de `an` fora do
// bloco de `anVencida`) é, por DESENHO, exclusiva da watchlist: eles só são
// lidos dentro da "cauda" `{!opOpen && (children || (<>...</>))}`, e o Radar
// SEMPRE passa `children` — o curto-circuito nunca deixa esse ramo avaliar em
// Radar, então a ausência desses campos no `radarVm` nunca foi um bug, é
// exatamente como o desenho pretende (o card do Radar é mais enxuto — a
// própria cauda dos filhos plugados pela tela substitui a versão longa).
// Medir paridade nesses campos daria falso positivo permanente (a suíte
// ficaria vermelha sem NENHUM bug real), não uma regressão pega de verdade.
// O bloco opGate.liquida, ao contrário, roda para as DUAS telas sempre que o
// gate de liquidez está ligado — foi ali, e só ali, que a ausência de `cp`
// derrubou o card. Se o próximo campo novo em `vm` for consumido ali dentro,
// este guardião pega — sem precisar saber o nome do campo de antemão.
(() => {
  // Extrai as chaves de um objeto JS a partir do índice do `{` de abertura,
  // respeitando aninhamento de {}/()/[] e literais de string/template —
  // necessário porque `radarVm` tem um objeto aninhado (`sc: { ... }`).
  function objectLiteralKeys(src, openBraceIdx) {
    let depth = 0, i = openBraceIdx, inStr = null, content = null;
    for (; i < src.length; i++) {
      const c = src[i];
      if (inStr) {
        if (c === "\\") { i++; continue; }
        if (c === inStr) inStr = null;
        continue;
      }
      if (c === '"' || c === "'" || c === "`") { inStr = c; continue; }
      if (c === "{") depth++;
      else if (c === "}") { depth--; if (depth === 0) { content = src.slice(openBraceIdx + 1, i); break; } }
    }
    if (content == null) return null;
    const entries = [];
    let cur = "", d2 = 0, inStr2 = null;
    for (let j = 0; j < content.length; j++) {
      const c = content[j];
      if (inStr2) {
        cur += c;
        if (c === "\\") { cur += content[++j] || ""; continue; }
        if (c === inStr2) inStr2 = null;
        continue;
      }
      if (c === '"' || c === "'" || c === "`") { inStr2 = c; cur += c; continue; }
      if (c === "{" || c === "(" || c === "[") { d2++; cur += c; continue; }
      if (c === "}" || c === ")" || c === "]") { d2--; cur += c; continue; }
      if (c === "," && d2 === 0) { entries.push(cur); cur = ""; continue; }
      cur += c;
    }
    if (cur.trim()) entries.push(cur);
    return entries.map((e) => {
      const t = e.trim();
      let m = t.match(/^([A-Za-z_$][\w$]*)\s*:/);
      if (m) return m[1];
      m = t.match(/^([A-Za-z_$][\w$]*)$/);
      return m ? m[1] : null;
    }).filter(Boolean);
  }

  const iAtivoCard = app.indexOf("function AtivoCard(");
  const iMercadoScreen = app.indexOf("function MercadoScreen(");
  ok("função AtivoCard localizada", iAtivoCard > -1);
  ok("função MercadoScreen localizada (delimita o fim de AtivoCard)", iMercadoScreen > iAtivoCard);
  const ativoCardBody = iAtivoCard > -1 && iMercadoScreen > iAtivoCard ? app.slice(iAtivoCard, iMercadoScreen) : "";

  const destrMatch = ativoCardBody.match(/const \{([^}]+)\} = vm;/);
  ok("destructuring de vm em AtivoCard localizado", !!destrMatch);
  const vmFields = destrMatch ? destrMatch[1].split(",").map((s) => s.trim()).filter(Boolean) : [];
  ok("destructuring de vm tem >= 25 campos (parse mudo)", vmFields.length >= 25, String(vmFields.length));

  const iOpGate = ativoCardBody.indexOf("opGate && opGate.liquida && (");
  ok("bloco opGate.liquida localizado em AtivoCard", iOpGate > -1);
  let opGateBlock = "";
  if (iOpGate > -1) {
    const openParenIdx = ativoCardBody.indexOf("(", iOpGate + "opGate && opGate.liquida && ".length - 1);
    let depth = 0, closeIdx = -1;
    for (let i = openParenIdx; i < ativoCardBody.length; i++) {
      const c = ativoCardBody[i];
      if (c === "(") depth++;
      else if (c === ")") { depth--; if (depth === 0) { closeIdx = i; break; } }
    }
    opGateBlock = closeIdx > openParenIdx ? ativoCardBody.slice(openParenIdx, closeIdx + 1) : "";
  }
  ok("bloco opGate.liquida tem conteúdo (parse mudo)", opGateBlock.length > 100, String(opGateBlock.length));
  ok("bloco opGate.liquida referencia PropostaLastreada", opGateBlock.includes("PropostaLastreada"));

  // campos de vm efetivamente lidos dentro do bloco (identificador isolado —
  // nem prefixado por `.` nem colado a outro identificador).
  const camposUsados = vmFields.filter((f) => new RegExp(`(?<![.\\w$])${f}(?![\\w$])`).test(opGateBlock));
  ok("pelo menos 'cp' está entre os campos lidos no bloco (sanity da extração)", camposUsados.includes("cp"), camposUsados.join(","));

  const anchorMercado = "<AtivoCard key={t} vm={{";
  const iMercadoAnchor = app.indexOf(anchorMercado);
  ok("call site da Watchlist (MercadoScreen) localizado", iMercadoAnchor > -1);
  const mercadoKeys = iMercadoAnchor > -1 ? (objectLiteralKeys(app, iMercadoAnchor + anchorMercado.length - 1) || []) : [];
  ok("vm da Watchlist parseado com >= 25 chaves (parse mudo)", mercadoKeys.length >= 25, String(mercadoKeys.length));

  const anchorRadar = "const radarVm = {";
  const iRadarAnchor = app.indexOf(anchorRadar);
  ok("call site do Radar (RadarScreen, radarVm) localizado", iRadarAnchor > -1);
  const radarKeys = iRadarAnchor > -1 ? (objectLiteralKeys(app, iRadarAnchor + anchorRadar.length - 1) || []) : [];
  ok("radarVm parseado com >= 10 chaves (parse mudo)", radarKeys.length >= 10, String(radarKeys.length));

  const faltaNaWatchlist = camposUsados.filter((f) => !mercadoKeys.includes(f));
  const faltaNoRadar = camposUsados.filter((f) => !radarKeys.includes(f));
  ok("todo campo de vm lido no bloco opGate.liquida está no vm da Watchlist",
    faltaNaWatchlist.length === 0, "faltando: " + faltaNaWatchlist.join(", "));
  ok("todo campo de vm lido no bloco opGate.liquida está no radarVm (o bug desta task: faltava 'cp')",
    faltaNoRadar.length === 0, "faltando: " + faltaNoRadar.join(", "));
})();

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
