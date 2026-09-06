// Fase 2 (02-06, MERC-02..04) — Guardião: ordem pendente na UI.
//
// Cobre o que os planos 02-02/02-04/02-05 deixaram pronto no backend/store
// mas ainda não tinha superfície: o usuário lê ANTES de confirmar que a
// ordem vira pendente e que o caixa/posição é reservado(a) na hora
// (BuyModal/SellModal); a ordem pendente aparece com o valor reservado numa
// seção "Pendentes" no Histórico; e cancelar exige dois passos, com o
// servidor sendo a fonte do estado devolvido (nunca um palpite local).
//
// Padrão de guardião estático (como test_agente_modo_estudo_ui.mjs,
// test_status_mercado_ui.mjs): inspeciona o TEXTO-FONTE de App.jsx/copy.js
// via readFileSync — App.jsx é um único arquivo sem exports internos, então
// nenhum destes componentes é importável isoladamente.
// Roda sem build: `node web/tests/test_ordens_pendentes_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const copySrc = readFileSync(join(here, "..", "src", "copy.js"), "utf8");
const persistenceSrc = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Isola o corpo de uma função top-level de App.jsx pelo balanceamento de
// chaves — mesma técnica de test_status_mercado_ui.mjs (evita depender de
// número de linha, que muda a cada plano anterior mesclado).
function funcBody(nome) {
  const marca = "function " + nome + "(";
  const i = app.indexOf(marca);
  if (i < 0) return "";
  // O corpo abre depois da lista de parâmetros — busca ") {" a partir de `i`
  // para não confundir com a chave de desestruturação `({ ctx })`.
  const sigEnd = app.indexOf(") {", i);
  let d = 0, ini = app.indexOf("{", sigEnd), j = ini;
  for (; j < app.length; j++) {
    if (app[j] === "{") d++;
    else if (app[j] === "}") { d--; if (!d) break; }
  }
  return app.slice(ini, j + 1);
}

const buyModal = funcBody("BuyModal");
const sellModal = funcBody("SellModal");
const historicoScreen = funcBody("HistoricoScreen");

// -------------------------------------------------- Task 1: copy simétrica
const chavesNovas = ["ordemPendentePill", "ordemPendenteAvisoCompra", "ordemPendenteAvisoVenda",
  "mercadoStatusFalhouNaOrdem", "toastOrdemPendente", "toastOrdemPendenteCancelada"];
for (const k of chavesNovas) {
  ok("copy.js: " + k + " existe nos DOIS modos",
    (k in COPY.estudo) && (k in COPY.operador));
}
ok("copy.js: ordemPendenteAvisoCompra aparece 1x por modo (2 no arquivo)",
  (copySrc.match(/ordemPendenteAvisoCompra/g) || []).length === 2);
ok("copy.js: ordemPendenteAvisoVenda aparece 1x por modo (2 no arquivo)",
  (copySrc.match(/ordemPendenteAvisoVenda/g) || []).length === 2);
ok("copy.js: toastOrdemPendente aparece 1x por modo (2 no arquivo)",
  (copySrc.match(/toastOrdemPendente\b/g) || []).length === 2);
ok("copy.js: mercadoStatusFalhouNaOrdem aparece 1x por modo (2 no arquivo)",
  (copySrc.match(/mercadoStatusFalhouNaOrdem/g) || []).length === 2);
// nunca inventar horário: chamado sem argumento não pode citar HH:MM
ok("ordemPendenteAvisoCompra sem abertura não inventa horário (estudo)",
  !/\d\d:\d\d/.test(COPY.estudo.ordemPendenteAvisoCompra(null)));
ok("ordemPendenteAvisoCompra sem abertura não inventa horário (operador)",
  !/\d\d:\d\d/.test(COPY.operador.ordemPendenteAvisoCompra(null)));
ok("ordemPendenteAvisoVenda sem abertura não inventa horário (estudo)",
  !/\d\d:\d\d/.test(COPY.estudo.ordemPendenteAvisoVenda(null)));
ok("ordemPendenteAvisoCompra COM abertura cita o horário recebido",
  COPY.estudo.ordemPendenteAvisoCompra("11:20").includes("11:20"));

// --------------------------------------------- Task 1: BuyModal/SellModal
ok("BuyModal/SellModal leem ctx.mercado (fonte única do plano 02-05, sem 2ª consulta)",
  /const fechado = ctx\.mercado && ctx\.mercado\.aberto === false;/.test(buyModal)
  && /const fechado = ctx\.mercado && ctx\.mercado\.aberto === false;/.test(sellModal));
ok("BuyModal: pill PENDENTE + disclaimer de fechado usam T.warn e ordemPendenteAvisoCompra",
  buyModal.includes("ordemPendenteAvisoCompra") && buyModal.includes("T.warn"));
ok("SellModal: disclaimer de fechado usa ordemPendenteAvisoVenda",
  sellModal.includes("ordemPendenteAvisoVenda"));
ok("BuyModal: pill não aparece quando mercado está aberto (renderização condicional)",
  /\{fechado && <span/.test(buyModal));
ok("SellModal: pill não aparece quando mercado está aberto (renderização condicional)",
  /\{fechado && <span/.test(sellModal));
// status indisponível: aviso + retry, SEM bloquear o Confirmar
ok("BuyModal: status indisponível mostra mercadoStatusFalhouNaOrdem com botão de retry via ctx.recarregarMercado",
  buyModal.includes("statusIndisponivel") && buyModal.includes("mercadoStatusFalhouNaOrdem") && buyModal.includes("ctx.recarregarMercado"));
ok("SellModal: status indisponível mostra mercadoStatusFalhouNaOrdem com botão de retry via ctx.recarregarMercado",
  sellModal.includes("statusIndisponivel") && sellModal.includes("mercadoStatusFalhouNaOrdem") && sellModal.includes("ctx.recarregarMercado"));
// 2026-09-06 (Fase 23, plano 23-03, MOTION-02): o botão ganhou uma SEGUNDA
// condição de disabled (`!!buyModal.confirmado`, guarda de duplo envio
// enquanto o valor pulsa por 120ms) — a asserção original travava a forma
// exata `disabled={!ok}`, que deixou de existir. O que ela protegia
// (status indisponível NÃO desabilita o Confirmar) continua valendo:
// `statusIndisponivel` não entra na expressão do `disabled` em nenhum dos
// dois termos.
ok("BuyModal: o botão Confirmar continua controlado por `ok`/`confirmado` (custo/caixa + duplo envio) — status indisponível não desabilita",
  /disabled=\{!ok \|\| !!buyModal\.confirmado\}/.test(buyModal) && !/disabled=\{[^}]*statusIndisponivel/.test(buyModal));
// rótulo do botão de confirmar não muda em nenhum caso (mesma chave de sempre)
ok("BuyModal/SellModal: rótulo do CTA continua vindo de confirmarCompra/confirmarVenda, sem ramificação",
  buyModal.includes("{ctx.cp.confirmarCompra}") && sellModal.includes("{ctx.cp.confirmarVenda}"));
ok("validação de caixa insuficiente inalterada (cost <= data.cash && q.price != null)",
  /const ok = cost <= data\.cash && q\.price != null;/.test(buyModal));

// --------------------------------------------- Task 1: confirmBuy/confirmSell
const confirmBuy = app.slice(app.indexOf("confirmBuy: async () => {"), app.indexOf("sell: async (t) => {"));
const confirmSell = app.slice(app.indexOf("confirmSell: async () => {"), app.indexOf("refreshWlScan: async () => {"));
ok("confirmBuy existe e usa store.buy",
  confirmBuy.includes("store.buy("));
ok("confirmBuy: pendente ⇒ toastOrdemPendente, SEM abrir stop/alvo",
  /if \(s\.pendente\) \{[\s\S]*?toastOrdemPendente[\s\S]*?\}/.test(confirmBuy));
ok("confirmBuy: setStopAlvoFor/runStopAlvoFor ficam DENTRO do ramo NÃO-pendente (else)",
  /\} else \{[\s\S]*?setStopAlvoFor\(bm\.t\);[\s\S]*?A\.runStopAlvoFor\(bm\.t\);[\s\S]*?\}/.test(confirmBuy));
ok("confirmBuy: track() marca pendente:true/false na propriedade (analítica não confunde pendente com executada)",
  /track\("trade_simulated", \{ side: "buy",[^}]*pendente: !!s\.pendente[^}]*\}\)/.test(confirmBuy));
ok("confirmSell: pendente ⇒ toastOrdemPendente em vez do toast de venda executada",
  /st\.pendente \? cp\.toastOrdemPendente\(sm\.qty, sm\.t\) : cp\.toastVenda\(/.test(confirmSell));
ok("confirmSell: track() também marca pendente:true/false",
  /track\("trade_simulated", \{ side: "sell",[^}]*pendente: !!st\.pendente[^}]*\}\)/.test(confirmSell));

// ------------------------------------------- Task 1 (deviation): paridade
// dos stores — sem isto, o app NATIVO nunca soubesse que uma ordem virou
// pendente (a resposta crua do backend não é adotada por _adotarCarteiraDoServidor,
// que só cobre o que persiste no doc; `pendente` é um flag da RESPOSTA).
ok("deviation (Rule 1): deviceStore.buy propaga r.pendente pra fora (paridade com serverStore)",
  /async buy\(t, qty, meta\) \{[\s\S]*?out\.pendente = !!\(r && r\.pendente\);/.test(persistenceSrc));
ok("deviation (Rule 1): deviceStore.sell propaga r.pendente pra fora (paridade com serverStore)",
  /async sell\(t, qty\) \{[\s\S]*?out\.pendente = !!\(r && r\.pendente\);/.test(persistenceSrc));

// ----------------------------------------------- Task 2: seção Pendentes
ok("HistoricoScreen existe e lê pendingOrders/caixaReservado/T.warn/'Pendentes'",
  historicoScreen.includes("pendingOrders") && historicoScreen.includes("caixaReservado")
  && historicoScreen.includes("T.warn") && historicoScreen.includes("Pendentes"));
ok("Pendentes renderiza só quando length > 0 (sem estado vazio próprio)",
  /\{pendentes\.length > 0 && \(/.test(historicoScreen) && /const pendentes = data\.pendingOrders \|\| \[\];/.test(historicoScreen));
ok("o pill de pendente no HistoricoScreen NÃO usa T.positive/T.negative (não lê como 'já executou')",
  (() => {
    const i = historicoScreen.indexOf("ordemPendentePill");
    const trecho = historicoScreen.slice(Math.max(0, i - 400), i + 50);
    return !/T\.positive|T\.negative/.test(trecho);
  })());
ok("linha com ultimoErro mostra o motivo (princípio 4 — falha de dado não some em silêncio)",
  historicoScreen.includes("o.ultimoErro") && historicoScreen.includes("ultimaTentativaEm"));
ok("grep '3px 9px': pill novo usa o padding padrão da app (App.jsx:935 no UI-SPEC)",
  (app.match(/padding: "3px 9px"/g) || []).length >= 2);

// ---------------------------------------- Task 2: toast de auto-cancelamento
ok("efeito de resumo (agentSummaryDone) filtra por tag === 'pendente-cancelada', não por kind 'warn' solto",
  /const canceladas = news\.filter\(\(e\) => e\.tag === "pendente-cancelada"\);/.test(app));
// NOTA (quick task 260824-i45, item 5, 2026-08-24) — REVERSÃO DELIBERADA.
// A regex exigia `flash(e.text);` SEGUIDO de `notify.send("Boris+", e.text);`.
// O `notify.send` foi removido de propósito: este bloco roda no BOOT, com o app
// em primeiro plano e a QUALQUER HORA, sobre eventos que já aconteceram horas
// antes — era a segunda fonte de "notificação fora do pregão" relatada. A
// informação NÃO se perde: o `flash` continua mostrando in-app e, no nativo, o
// próprio `notify.send` já caía no mesmo `_emitForeground` → handler in-app;
// sumiu só o banner de sistema redundante.
// O que este guardião realmente protege continua travado, e continua capaz de
// falhar: o texto vem do MOTOR (`e.text`), o front nunca recompõe a frase do
// motivo (CLAUDE.md princípio 5). A ausência do banner virou asserção própria,
// para a reversão não poder voltar em silêncio.
ok("toast de auto-cancelamento usa e.text (texto do motor) — sem string literal de motivo no front",
  /for \(const e of canceladas\) \{\s*flash\(e\.text\);/.test(app));
ok("o laço de canceladas NÃO reintroduz banner de sistema (260824-i45, item 5)",
  (() => {
    const i = app.indexOf("for (const e of canceladas) {");
    if (i < 0) return false;
    const j = app.indexOf("}", app.indexOf("flash(e.text);", i));
    return j > i && !app.slice(i, j).includes("notify.send");
  })());
ok("'pendente-cancelada' aparece 1x no arquivo, dentro do recorte que contém agentSummaryDone",
  (() => {
    const count = (app.match(/pendente-cancelada/g) || []).length;
    const i = app.indexOf("agentSummaryDone");
    const j = app.indexOf("pendente-cancelada");
    return count === 1 && i >= 0 && j > i && j < i + 3000;
  })());

// ----------------------------------- Task 3: cancelamento em dois passos
ok("A.cancelPendingOrder chama store.cancelPendingOrder exatamente 1x no arquivo inteiro",
  (app.match(/store\.cancelPendingOrder\(/g) || []).length === 1);
ok("A.cancelPendingOrder adota o estado devolvido (setData) e nunca finge sucesso local",
  /cancelPendingOrder: async \(id\) => \{\s*try \{\s*const s = await store\.cancelPendingOrder\(id\);\s*setData\(s\);/.test(app));
ok("HistoricoScreen: botão gatilho ✕ tem 40px e aria-label por ticker",
  historicoScreen.includes('width: "40px", height: "40px"') && historicoScreen.includes('"Cancelar ordem pendente de " + o.t'));
ok("HistoricoScreen: confirmação de dois passos com os dois textos exigidos",
  historicoScreen.includes("Manter ordem") && historicoScreen.includes("Confirmar cancelamento"));
ok("HistoricoScreen: um `confirmando` por vez (estado local do componente)",
  /const \[confirmando, setConfirmando\] = useState\(null\);/.test(historicoScreen));
ok("HistoricoScreen: nenhum clique único chama cancelPendingOrder — só dentro do bloco de confirmação (confirmando === o.id)",
  /\{confirmando === o\.id && \([\s\S]*?A\.cancelPendingOrder\(o\.id\)[\s\S]*?\)\}/.test(historicoScreen));
ok("HistoricoScreen: botão de confirmar fica desabilitado enquanto a chamada está em voo (enviando)",
  /disabled=\{enviando\}[\s\S]{0,400}Confirmar cancelamento/.test(historicoScreen));
ok("'Manter ordem' aparece 1x no arquivo",
  (app.match(/Manter ordem/g) || []).length === 1);
ok("'Confirmar cancelamento' aparece 1x no arquivo",
  (app.match(/Confirmar cancelamento/g) || []).length === 1);

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
