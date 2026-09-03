// Fase 17 (Plano 05, FLOW-02/FLOW-03) — Guardião do ACEITE do collar na UI:
// capacidade multiperna declarada pelo cliente, execução disparada SÓ por
// clique confirmado (nunca por efeito/render), Modo Estudo sem botão,
// corpo sem prêmio/strike do cliente (o servidor re-deriva — Plano 17-03),
// paridade dos dois stores, e nenhuma chave de copy.js compondo a manchete
// do motor. Irmão de web/tests/test_opcoes_proposta_ui.mjs (payoff/frescor)
// e web/tests/test_carteira_lastro_ui.mjs (carteira lastreada) — este
// arquivo guarda especificamente o CAMINHO DE ACEITE do collar.
//
// Apagar qualquer guardião abaixo exige nota explícita (regra do
// repositório) — juntos eles cobrem T-17-22..T-17-27 do threat model do
// Plano 17-05.
//
// Roda sem build: `node web/tests/test_opcoes_collar_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const apiJs = readFileSync(join(here, "..", "src", "api.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Extrai o trecho balanceado (parênteses/chaves/colchetes, respeitando
// literais de string/template) a partir do índice de um "(" de abertura —
// mesmo padrão de balanceamento já usado em test_opcoes_proposta_ui.mjs
// (objectLiteralKeys), generalizado para qualquer par de delimitadores.
function extrairBalanceado(src, openIdx) {
  let depth = 0, i = openIdx, inStr = null;
  for (; i < src.length; i++) {
    const c = src[i];
    if (inStr) {
      if (c === "\\") { i++; continue; }
      if (c === inStr) inStr = null;
      continue;
    }
    if (c === '"' || c === "'" || c === "`") { inStr = c; continue; }
    if (c === "(" || c === "{" || c === "[") depth++;
    else if (c === ")" || c === "}" || c === "]") { depth--; if (depth === 0) return src.slice(openIdx, i + 1); }
  }
  return src.slice(openIdx); // não fechou — devolve o resto (guardião reprova por conteúdo ausente)
}

// ---------------------------------------------------------------------------
// 1) capacidade multiperna declarada pelo cliente (FLOW-02/FLOW-03)
// ---------------------------------------------------------------------------
ok("App.jsx declara a capacidade multiperna (store.optionsProposta(t, true))",
  app.includes("store.optionsProposta(t, true)"));
ok("api.js monta ?multiperna=1 quando o parâmetro é passado",
  /multiperna \? "\?multiperna=1" : ""/.test(apiJs));

// ---------------------------------------------------------------------------
// 2) aceite é sempre explícito — nenhuma execução em efeito (T-17-22)
//    "recusar" só é a ausência de clique se nada além do clique puder
//    disparar a execução: varre TODOS os useEffect( de App.jsx e afirma que
//    nenhum bloco balanceado contém abrirCollar.
// ---------------------------------------------------------------------------
(() => {
  const idxs = [];
  const re = /useEffect\(/g;
  let m;
  while ((m = re.exec(app))) idxs.push(m.index + "useEffect".length); // aponta pro "(" de abertura
  ok("pelo menos um useEffect( encontrado em App.jsx (sanity)", idxs.length > 0, String(idxs.length));
  const blocosComAbrirCollar = idxs
    .map((openIdx) => extrairBalanceado(app, openIdx))
    .filter((bloco) => bloco.includes("abrirCollar"));
  ok("nenhum useEffect( contém A.abrirCollar/store.optionsAbrirCollar (execução só por clique)",
    blocosComAbrirCollar.length === 0, `encontrados: ${blocosComAbrirCollar.length}`);
})();

// ---------------------------------------------------------------------------
// 3) confirmação antes de travar lastro (T-17-26)
//    window.confirm(cp.confirmAbrirCollar( aparece exatamente 1x DENTRO DE
//    CADA handler onAbrirLastreada, ANTES da chamada a A.abrirCollar( no
//    mesmo handler. Atualizado na Fase 18 (Plano 02, T-18-06): o caminho de
//    aceite do collar passou a ter DOIS pontos de renderização legítimos —
//    AtivoCard (Watchlist/Radar, original) e PropostaDaPosicao (detalhe
//    dentro do card de Posições) — cada um com sua própria réplica fiel do
//    handler (mesmo corpo, `t` escopado à posição). A asserção de contagem
//    global "exatamente 1x" foi generalizada para "exatamente 1x por
//    handler encontrado", preservando a garantia original (nunca falta
//    confirmação antes da trava) em AMBOS os pontos de entrada.
// ---------------------------------------------------------------------------
(() => {
  const idxs = [];
  const re = /const onAbrirLastreada = async \(\) => \{/g;
  let m;
  while ((m = re.exec(app))) idxs.push(m.index);
  ok("pelo menos um handler onAbrirLastreada localizado", idxs.length > 0, String(idxs.length));
  ok("existem exatamente 2 handlers onAbrirLastreada (AtivoCard + PropostaDaPosicao, Fase 18 Plano 02)", idxs.length === 2, String(idxs.length));

  idxs.forEach((iOnAbrir, n) => {
    // Delimita o handler pelo próximo `const onFecharLastreada` (vizinho
    // imediato, mesmo padrão usado nos outros guardiões deste arquivo).
    const iOnFechar = app.indexOf("const onFecharLastreada", iOnAbrir);
    const handler = iOnFechar > iOnAbrir ? app.slice(iOnAbrir, iOnFechar) : "";
    ok(`handler onAbrirLastreada #${n + 1} tem conteúdo (parse mudo)`, handler.length > 100, String(handler.length));

    const ocorrenciasConfirm = (handler.match(/window\.confirm\(cp\.confirmAbrirCollar\(/g) || []).length;
    ok(`handler onAbrirLastreada #${n + 1}: window.confirm(cp.confirmAbrirCollar( aparece exatamente 1 vez`, ocorrenciasConfirm === 1, String(ocorrenciasConfirm));

    const iConfirm = handler.indexOf("window.confirm(cp.confirmAbrirCollar(");
    const iExec = handler.indexOf("A.abrirCollar(");
    ok(`handler onAbrirLastreada #${n + 1}: confirmação do collar existe dentro do handler`, iConfirm > -1);
    ok(`handler onAbrirLastreada #${n + 1}: A.abrirCollar( existe dentro do handler`, iExec > -1);
    ok(`handler onAbrirLastreada #${n + 1}: confirmação vem ANTES da execução no mesmo handler`, iConfirm > -1 && iExec > -1 && iConfirm < iExec);
  });
})();

// ---------------------------------------------------------------------------
// 4) Modo Estudo não ganha botão no collar (T-17-23)
//    Dentro do slice de PropostaLastreada, existe exatamente UM <button, e
//    ele continua dentro do bloco `{operador && (` — mesma medida do
//    guardião pré-existente em test_opcoes_proposta_ui.mjs, reafirmada
//    especificamente para o caminho do collar (a UI de defesa; o servidor
//    recusa com 403 mesmo se este código tivesse um bug).
// ---------------------------------------------------------------------------
(() => {
  const iPL = app.indexOf("function PropostaLastreada");
  const iOC = app.indexOf("function OpcoesCamada");
  ok("PropostaLastreada localizado antes de OpcoesCamada", iPL > -1 && iOC > iPL);
  const propostaFn = iPL > -1 && iOC > iPL ? app.slice(iPL, iOC) : "";

  ok("PropostaLastreada renderiza o ramo collar (isCollar)", /isCollar/.test(propostaFn));

  const botoes = (propostaFn.match(/<button/g) || []).length;
  ok("exatamente 1 <button dentro de PropostaLastreada (nenhum botão extra pro collar)", botoes === 1, String(botoes));
  ok("o único <button continua condicionado a `operador` (<= 60 chars entre `{operador && (` e `<button`)",
    /\{operador && \([\s\S]{0,60}<button/.test(propostaFn));
})();

// ---------------------------------------------------------------------------
// 5) corpo enviado não carrega prêmio nem strike (T-17-24)
//    O servidor re-deriva a proposta e usa os próprios prêmios (ADR-026,
//    Decisão 2) — mandar prêmio/strike do cliente sugeriria que ele os
//    negocia. O objeto passado a A.abrirCollar( só carrega
//    underlying/pernasContratos(contractSymbol+lado)/contratos/expiration.
// ---------------------------------------------------------------------------
(() => {
  const iExec = app.indexOf("A.abrirCollar(");
  ok("A.abrirCollar( localizado em App.jsx", iExec > -1);
  const openParenIdx = iExec > -1 ? iExec + "A.abrirCollar".length : -1;
  const chamada = openParenIdx > -1 ? extrairBalanceado(app, openParenIdx) : "";
  ok("corpo de A.abrirCollar( extraído (parse mudo)", chamada.length > 20, String(chamada.length));
  ok("corpo enviado NÃO contém a substring \"premio\" (case-insensitive)", !/premio/i.test(chamada));
  ok("corpo enviado NÃO contém a substring \"strike\" (case-insensitive)", !/strike/i.test(chamada));
  ok("corpo enviado carrega contractSymbol + lado por perna", chamada.includes("contractSymbol") && chamada.includes("lado"));
})();

// ---------------------------------------------------------------------------
// 6) paridade dos dois stores (T-17-25)
//    optionsAbrirCollar existe nos DOIS stores; o ramo SEM sessão do
//    deviceStore lança erro nomeado em vez de reimplementar a estrutura —
//    diferente das operações de 1 perna, não há espelho local do collar.
// ---------------------------------------------------------------------------
(() => {
  const ocorrencias = (persistence.match(/optionsAbrirCollar/g) || []).length;
  ok("optionsAbrirCollar aparece pelo menos 2x em persistence.js (um por store)", ocorrencias >= 2, String(ocorrencias));

  const iDevice = persistence.indexOf("function deviceStore()");
  const iExport = persistence.indexOf("export const store");
  ok("bloco de deviceStore localizado", iDevice > -1 && iExport > iDevice);
  const deviceBlock = iDevice > -1 && iExport > iDevice ? persistence.slice(iDevice, iExport) : "";

  const iMetodo = deviceBlock.indexOf("async optionsAbrirCollar(body)");
  ok("optionsAbrirCollar existe dentro de deviceStore", iMetodo > -1);
  const vizinhanca = iMetodo > -1 ? deviceBlock.slice(iMetodo, iMetodo + 800) : "";
  ok("ramo sem sessão de deviceStore.optionsAbrirCollar lança erro nomeado (throw new Error()",
    /throw new Error\(/.test(vizinhanca));
  ok("deviceStore.optionsAbrirCollar NÃO reimplementa a estrutura sem sessão (sem chamada a api.optionsChain dentro deste método)",
    !vizinhanca.includes("api.optionsChain"));
})();

// ---------------------------------------------------------------------------
// 7) front não compõe manchete/didática do collar (T-17-27)
//    As frases canônicas do motor para collar (skill_ref.py) nunca são
//    duplicadas em copy.js — reafirma, para as chaves NOVAS deste plano, a
//    mesma asserção negativa já aplicada às chaves antigas em
//    test_opcoes_proposta_ui.mjs ("Se você tivesse").
// ---------------------------------------------------------------------------
(() => {
  const valoresTeste = [
    COPY.estudo.ctaCollarDebito("X", "Y", "Z", "W", "V"), COPY.operador.ctaCollarDebito(2, "PETR4", "38,50", "35,00", "120,00"),
    COPY.estudo.ctaCollarCredito("X", "Y", "Z", "W", "V"), COPY.operador.ctaCollarCredito(2, "PETR4", "38,50", "35,00", "120,00"),
    COPY.estudo.collarPernasLinha("X", "Y", "Z", "W"), COPY.operador.collarPernasLinha(2, "PETR4", "38,50", "35,00"),
    COPY.estudo.confirmAbrirCollar("X", "Y", "Z"), COPY.operador.confirmAbrirCollar(2, "PETR4", 200),
    COPY.estudo.eyebrowPropostaCollar, COPY.operador.eyebrowPropostaCollar,
  ].join(" | ");
  ok("chaves novas do collar não contêm \"abate o custo\" (manchete do motor)", !valoresTeste.includes("abate o custo"));
  ok("chaves novas do collar não contêm \"Se você tivesse\" (didática do motor)", !valoresTeste.includes("Se você tivesse"));
})();

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
