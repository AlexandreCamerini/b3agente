// Camada de persistencia multiplataforma.
//
//  - WEB: a fonte da verdade e o servidor (FastAPI + SQLite). A chave da API
//    fica no servidor e nunca volta ao cliente.
//  - iPHONE (nativo): local-first para tudo, com UMA exceção. Config, skill,
//    watchlist, histórico e agente ficam no PRÓPRIO APARELHO (localStorage do
//    WKWebView). Carteira (buy/sell/putPosition) TAMBÉM fica local quando
//    ninguém está logado — mas com CONTA, o servidor é quem executa e devolve
//    o estado confirmado: é o servidor (não o aparelho) que o Operador no
//    servidor lê para vigiar stop/alvo/trailing com o app FECHADO, e um dado
//    que só existe no aparelho é invisível pra ele (bug real, confirmado em
//    2026-08-07 — o Alex configurava stop no iPhone e o servidor nunca via).
//    Sem conta, o servidor só serve cotações e análise; para analisar, o
//    aparelho envia a config + chave no corpo da requisição.
//
// App.jsx fala apenas com `store`; a diferenca de plataforma fica escondida aqui.
import { Capacitor } from "@capacitor/core";
import { api, setApiBase, setNativeMode } from "./api.js";
import { CATALOG, CATALOG_TICKERS, defaultState, defaultSkillText, defaultSkillTextOperador, defaultLlmPrompts, LEGACY_SKILL_TEXTS } from "./catalog.js";
import { backfillStructural, limparCarteiraDemo } from "./migrate.js";
// FASE 13 (13-02, CR-01): gate fail-closed de watchlist no deviceStore —
// mesmos hooks puros que o web/PWA já usa via App.jsx, importados aqui
// direto no store porque no iOS não existe gate autoritativo no servidor
// para watchlist (device é a fonte da verdade); esta checagem local é a
// ÚNICA linha de defesa (ver comentários em putWatchlist/addWatchlistTicker).
import { canAddTicker, canGrowWatchlistTo } from "./plan.js";
// FASE 2: camada de sync (token + cache otimista + fila offline). serverStore
// fala com o servidor ATRAVÉS dela; deviceStore segue local-first, EXCETO a
// carteira quando logado (ver cabeçalho do arquivo).
import * as sync from "./sync.js";

// Normaliza a entrada do usuario igual ao servidor: sem espacos, MAIUSCULAS,
// sem sufixo .SA, mantendo so A-Z0-9. Ex.: "petr4 " -> "PETR4".
function normTicker(s) {
  return String(s == null ? "" : s).toUpperCase().replace(/\s+/g, "").replace(/\.SA/g, "").replace(/[^A-Z0-9]/g, "");
}

// Diagnóstico controlável: ative com localStorage["b3-debug"]="1" ou window.B3_DEBUG=true.
// Loga cada etapa do cadastro (a..h) para identificar onde a cadeia quebra.
function dbgOn() {
  try {
    if (typeof window !== "undefined" && window.B3_DEBUG) return true;
    if (typeof localStorage !== "undefined" && localStorage.getItem("b3-debug")) return true;
  } catch { /* ignore */ }
  return false;
}
function dlog(stage, info) { if (dbgOn()) { try { console.log("[b3:add:" + stage + "]", info == null ? "" : info); } catch { /* ignore */ } } }

// FIX-C02 (Plano 04-05): teto de entradas `status === "rejeitada"` mantidas
// no `history` local — espelho exato de store.py.CAP_REJEICOES (paridade de
// stores, CLAUDE.md).
const CAP_REJEICOES_LOCAL = 100;

// Fase B1: insere/atualiza o snapshot do dia (chave = `data`), sem duplicar.
// FASE 2 (2.4): contexto de ENTRADA registrado na compra (setup do STU da F1)
// — espelho exato de store.py._sanitize_trade_meta: só campos conhecidos,
// tipos validados. Telemetria didática, nunca recomendação.
function sanitizeTradeMeta(meta) {
  if (!meta || typeof meta !== "object") return null;
  const out = {};
  for (const k of ["setup", "lado", "veredito", "snapshotId"]) {
    const v = meta[k];
    if (typeof v === "string" && v.trim()) out[k] = v.trim().slice(0, 80);
  }
  for (const k of ["gatilho", "invalidacao", "confluencia"]) {
    const v = meta[k];
    if (typeof v === "number" && isFinite(v)) out[k] = +v.toFixed(2);
  }
  return Object.keys(out).length ? out : null;
}

function upsertSnapshot(list, snap) {
  const data = String((snap || {}).data || "").trim();
  const arr = Array.isArray(list) ? list : [];
  if (!data) return arr;
  const num = (v) => { const n = Math.round((Number(v) || 0) * 100) / 100; return Number.isFinite(n) ? n : 0; };
  const rec = { data, patrimonio: num((snap || {}).patrimonio), caixa: num((snap || {}).caixa), posicoesValor: num((snap || {}).posicoesValor) };
  const out = arr.filter((s) => s && s.data !== data);
  out.push(rec);
  out.sort((a, b) => (a.data || "").localeCompare(b.data || ""));
  return out.slice(-400);
}

const isNative = (() => {
  try {
    return !!(Capacitor && typeof Capacitor.isNativePlatform === "function" && Capacitor.isNativePlatform());
  } catch {
    return false;
  }
})();

// No mobile, o cliente HTTP exige base absoluta (caminho relativo iria para o
// próprio app, devolvendo HTML). Avisa o api.js para falhar cedo e claro.
setNativeMode(isNative);

// FASE 2: recupera o token de sessão salvo ANTES da primeira chamada, para que
// o getState() inicial já venha no escopo do usuário (web) quando há login.
sync.loadToken();

/* ----------------------------- WEB (servidor) ----------------------------- */
// FASE 2: o serverStore agora fala com o servidor ATRAVÉS da camada de sync.
//  - getState: servidor + cache otimista (boot/queda de rede sem crash).
//  - escritas idempotentes de estado: cache otimista + fila offline (outbox)
//    que reaplica ao reconectar. Servidor é a fonte da verdade (decisão B).
//  - chamadas que EXIGEM servidor (cotação/análise/compra/venda/ciclo) seguem
//    diretas — erro offline é claro, sem fila.
//  - o token de sessão (quando logado) é anexado pelo api.js em toda chamada.
function serverStore() {
  // patch otimista raso da config: nunca guarda apiKey no cache; reflete só o
  // indicador keyStored e campos de exibição. O servidor reconcilia no flush.
  const optConfig = (patch) => (cur) => {
    const c = { ...(cur.config || {}) };
    for (const k of Object.keys(patch || {})) {
      if (k === "apiKey" || k === "clearKey") continue;
      c[k] = patch[k];
    }
    if (typeof patch.apiKey === "string" && patch.apiKey) c.keyStored = true;
    if (patch.clearKey === true) c.keyStored = false;
    return { ...cur, config: c };
  };
  // O STORE dispara o sync sozinho; a UI não sabe que isto existe. Mesmo
  // argumento que criou o `_agendarSyncPrefs` do deviceStore: deixar a UI
  // lembrar de sincronizar é garantir que um dia ela esqueça — e esquecer
  // significa interruptor que o usuário mexeu e que não vale.
  //
  // Nome DIFERENTE do agendador do deviceStore de propósito: o guardião de
  // paridade CONTA os disparos do agendador de lá, e essa contagem não pode
  // ser inflada por código do outro store (nem por este comentário — por isso
  // o nome dele não aparece aqui na forma de chamada).
  //
  // Gatilho ÚNICO (`notif`), e é delimitação, não esquecimento: o web não
  // manda `modo` nem `universo` (autoridade do aparelho), então não há o que
  // sincronizar em troca de appMode, watchlist, compra ou venda — e cada
  // disparo a mais é uma chance a mais de escrever sem autoridade.
  let _prefsTimerWeb = null;
  const _agendarSyncPrefsWeb = () => {
    if (_prefsTimerWeb) clearTimeout(_prefsTimerWeb);
    _prefsTimerWeb = setTimeout(() => {
      _prefsTimerWeb = null;
      _store.syncPushPrefs().catch(() => { /* best-effort, silencioso */ });
    }, 1500);
  };
  const _store = {
    isNative: false,
    getState: () => sync.readState(),
    putConfig: (patch) => {
      const p = sync.mutate("putConfig", [patch], optConfig(patch));
      if (patch && patch.notif && typeof patch.notif === "object") {
        // DEPOIS de a mutação resolver: o `readState()` de dentro do
        // `syncPushPrefs` precisa já enxergar o valor novo, senão o web
        // reenviaria o estado anterior por cima do que acabou de mudar.
        Promise.resolve(p).then(() => { _agendarSyncPrefsWeb(); })
          .catch(() => { /* falha de escrita já sobe pelo `p` devolvido */ });
      }
      return p;
    },
    testConfig: () => api.testConfig(), // exige servidor (testa a chave ao vivo)
    // FASE 8B (R2): a skill é POR MODO — b.modo escolhe a seção no servidor
    putSkill: (b) => sync.mutate("putSkill", [b], (cur) => (b && b.modo === "operador"
      ? { ...cur, skillOperador: { ...(cur.skillOperador || {}), name: b.name, text: b.text } }
      : { ...cur, skill: { ...(cur.skill || {}), name: b.name, text: b.text } })),
    restoreSkill: (modo) => sync.mutate("restoreSkill", [modo]),
    putWatchlist: (tickers) => sync.mutate("putWatchlist", [tickers], (cur) => ({ ...cur, watchlist: Array.isArray(tickers) ? [...tickers] : (cur.watchlist || []) })),
    addWatchlistTicker: (ticker) => api.addWatchlistTicker(ticker), // servidor valida no Yahoo (exige rede)
    putProfile: (profile) => sync.mutate("putProfile", [profile], (cur) => ({ ...cur, profile: { ...(cur.profile || {}), ...profile } })),
    putLlmPrompts: (patch) => sync.mutate("putLlmPrompts", [patch], (cur) => ({ ...cur, llmPrompts: { ...(cur.llmPrompts || {}), ...patch } })),
    putSnapshot: (snap) => sync.mutate("putSnapshot", [snap]),
    resetPortfolio: () => sync.mutate("resetPortfolio", []),
    getQuotes: () => api.getQuotes(), // servidor conhece watchlist+posicoes
    // `promptFp` = identidade da análise já exibida. O servidor compara com a
    // pergunta atual: igual ⇒ devolve `reaproveitada` sem gastar IA; diferente
    // ⇒ a leitura antiga venceu e é refeita. É o que impede análise de outro
    // pregão de ficar no card ao lado do veredito fresco.
    analyze: (t, opts) => api.analyzeTechnical(t, { model: (opts && opts.model) || "completo", position: (opts && opts.position) || undefined, promptFp: (opts && opts.promptFp) || undefined }),
    analyzeStopAlvo: (t, opts) => api.carteiraStopAlvo(t, (opts && opts.prompt) ? { prompt: opts.prompt } : {}),
    technicals: (t, period) => api.technicals(t, period),
    // Plano 04-06 (FIX-C03): dado público de mercado, sem estado local —
    // pass-through puro, igual technicals acima (guardrail de paridade
    // CLAUDE.md: precisa existir nos DOIS stores mesmo sendo idêntico).
    benchmarkIbov: (period) => api.benchmarkIbov(period),
    scan: (period, tickers, force) => api.scan(period, tickers, force), // BLOCO 3 + FASE 2 + FASE 4 (1.3: force)
    scanDeep: (body) => api.scanDeep(body),                       // FASE 2 (2.1): N1 deep
    scanDeepEstimate: (p, n, t) => api.scanDeepEstimate(p, n, t), // FASE 2 (2.1): custo antes
    pushAnalysisLog: (t, entry) => api.pushAnalysisLog(t, entry), // FASE 2 (2.5): telemetria didática
    // `extra` chega `undefined` a partir de `App.jsx` (`registerPushToken(tk)`)
    // e isso está certo: `notify.registerPush` devolve `{ok:false}` fora do
    // nativo ANTES de qualquer chamada, então este caminho nunca roda no web.
    // A paridade que faltava era a do ENVIO da preferência — é o
    // `syncPushPrefs` abaixo, disparado pelo próprio store, que a fecha.
    registerPushToken: (token, extra) => api.pushRegisterToken(token, extra),   // FASE 3.3b: APNs (exige conta)
    // Paridade com o deviceStore: MESMA assinatura (sem argumento) e mesmo
    // contrato — o store monta o corpo, quem chama não precisa saber a forma.
    // Assinaturas diferentes aqui já seriam um bug silencioso: `App.jsx` chama
    // um nome só, e um `{}` faz o servidor não gravar nada devolvendo ok.
    // O push lê uma fonte só (`pushPrefs`), então o web também a alimenta.
    //
    // QUADRO DE AUTORIDADE (260824-kc2) — o web escreve SÓ o que lhe cabe:
    //
    //   `radar`/`execucao`/`protecao` → os DOIS clientes. É controle da CONTA,
    //                                   e o web mostra os mesmos interruptores.
    //   `gatilho`                     → SÓ o aparelho. Só ele registra token
    //                                   APNs (`notify.js`: no web,
    //                                   `registerPush` devolve `{ok:false}`
    //                                   antes de chamar qualquer coisa), então
    //                                   `gatilho` sempre foi, de fato,
    //                                   preferência do aparelho.
    //   `modo`/`universo`             → SÓ o aparelho. Derivam de estado
    //                                   local-first (appMode, watchlist do
    //                                   aparelho, que pode não ser a do
    //                                   servidor).
    //
    // NÃO "complete" este corpo. Se `gatilho` voltar aqui, ele seria derivado
    // do `config.notif` DO SERVIDOR — e para um usuário device-first esse
    // config é o default, que não é ausência de chave: `defaults.py` grava
    // `enabled: False` e `gatilho: False` EXPLÍCITOS. Como `set_prefs` grava
    // por chave, o `gatilho` LIGADO que o iPhone tinha viraria desligado na
    // primeira vez que a pessoa abrisse o app no navegador. Em silêncio, sem
    // nada na tela acusando. Mesma coisa, com sintoma mais discreto, para
    // `modo` e `universo`.
    syncPushPrefs: async () => {
      const s = await sync.readState();
      const c = (s && s.config) || {};
      const n = (c.notif && typeof c.notif === "object") ? c.notif : {};
      return api.pushRegisterToken("", {
        prefs: {
          radar: n.radar !== false,
          execucao: n.execucao !== false,
          protecao: n.protecao !== false,
        },
      });
    },
    // Camada de entendimento: no web o modo vem da config do escopo no servidor.
    conceitos: (modo, resumido) => api.conceitos(modo, resumido),
    conceito: (cid, body) => api.conceito(cid, body),
    kbBuscar: (q, modo) => api.kbBuscar(q, modo),
    assistente: (body) => api.assistente(body),
    petResumo: (tela) => api.petResumo(undefined, tela),           // pet: modo fica com o servidor; F4: tela escolhe a aba

    scanProgress: () => api.scanProgress(),                        // BLOCO B1
    timing: (t) => api.timing(t),                                  // F1: modo vem da config do escopo no servidor
    obsLogs: (n, level, cat) => api.obsLogs(n, level, cat),        // FASE 5: logs do servidor
    adminSummary: () => api.adminSummary(),                        // F5: painel de admin (só ver)
    adminMobileHandoff: () => api.adminMobileHandoff(),            // ADR-014: código de handoff pro web-admin/ embutido
    brapiProjecao: (intervaloS) => api.brapiProjecao(intervaloS),  // ADR-008: simula intervalo→custo/mês
    brapiProjecaoAplicar: (intervaloS) => api.brapiProjecaoAplicar(intervaloS), // ADR-008: aplica o intervalo
    analysisOutcomesStats: (modo) => api.analysisOutcomesStats(modo), // qa/30 (Fase A): eficiência da IA
    aiActivity: () => api.aiActivity(), // qa/45: custo + histórico da IA
    aiModels: () => api.aiModels(), // qa/49: catálogo de modelos + parâmetros
    analysisOutcomesCsv: () => api.analysisOutcomesCsv(),          // qa/35 (P2): export CSV
    agentStatus: () => api.agentStatus(),                          // BLOCO D3
    agentLog: (n) => api.agentLog(n),                              // FASE 3: Diário do operador
    agentRunNow: () => api.agentRunNow(),                          // BLOCO D4
    pushTest: () => api.pushTest(),                                // BLOCO E2
    optionsExpirations: (t) => api.optionsExpirations(t),
    optionsChain: (t, expiration) => api.optionsChain(t, expiration),
    analyzeOption: (body) => api.analyzeOption(body),
    optionsGate: (t) => api.optionsGate(t),                        // v2: gate de descobribilidade
    optionsBuy: (body) => api.optionsBuy(body),                    // v2 (ADR-003/004)
    optionsSell: (body) => api.optionsSell(body),                  // v2 (ADR-005)
    putOptionPosition: (contractId, b) => api.putOptionPosition(contractId, b),
    // Fase 14 (opções lastreadas): proposta é dado de mercado, delega direto.
    // Abrir/fechar mexem em caixa real — chamada DIRETA, nunca sync.mutate/
    // outbox (mesma decisão de buy/sell/cancelPendingOrder: reaplicar de fila
    // offline devolveria caixa duas vezes).
    optionsProposta: (t) => api.optionsProposta(t),
    optionsAbrirLastreada: (body) => api.optionsAbrirLastreada(body),
    optionsFecharLastreada: (body) => api.optionsFecharLastreada(body),
    cachedTechnicals: (_t, _period) => null,
    buy: (t, qty, meta) => api.buy(t, qty, meta),  // FASE 2 (2.4): mesma interface do deviceStore
    sell: (t, qty) => api.sell(t, qty),
    // Fase 2 (MERC-01): roda ANTES do login (D-08) — sem ensure()/sessão,
    // delegação pura. Existe nos DOIS stores só para não abrir exceção ao
    // guardrail de paridade: a UI lê `store.marketStatus()`, nunca `api`
    // direto, para que o guardião de paridade cubra o caminho.
    marketStatus: () => api.marketStatus(),
    // MERC-04: cancelar mexe em caixa real — chamada DIRETA, fora de
    // sync.mutate/outbox (mesma decisão de buy/sell acima): reaplicar de
    // fila offline poderia devolver caixa duas vezes (T-02-20).
    cancelPendingOrder: (id) => api.cancelPendingOrder(id),
    putPosition: (t, b) => sync.mutate("putPosition", [t, b], (cur) => ({
      ...cur,
      positions: (cur.positions || []).map((p) => p.t === t ? {
        ...p,
        stop: ("stop" in b) ? (b.stop === "" || b.stop == null ? null : Number(b.stop)) : p.stop,
        alvo: ("alvo" in b) ? (b.alvo === "" || b.alvo == null ? null : Number(b.alvo)) : p.alvo,
      } : p),
    })),
    // FASE 3 (Operador): mudar `serverEnabled` NUNCA entra na fila otimista —
    // um timeout viraria "ligado" na UI sem o servidor ter ligado (estado
    // fantasma, exatamente o bug relatado). Flag de servidor = chamada LIVE:
    // ou o servidor confirma, ou o erro aparece; os demais parâmetros seguem
    // no caminho otimista normal.
    putAgent: (b) => ("serverEnabled" in (b || {}))
      ? sync.live("putAgent", [b])
      : sync.mutate("putAgent", [b], (cur) => ({ ...cur, agent: { ...(cur.agent || {}), ...b } })),
    cycle: () => api.cycle(),
    aiQuota: () => api.aiQuota(), // FASE 3: cota da IA gerenciada
    // FASE 13 (13-01): {count, limit, planId} — leitura ao vivo, sem cache
    // local (D-05), mesmo padrão de delegação direta de aiQuota acima.
    watchlistQuota: () => api.watchlistQuota(),
    // FIX-C33 (Fase 5): contagem real de análises do mês corrente, para o
    // pré-check de UX do gate (`canAnalyze` em plan.js). NÃO existe um
    // contador próprio aqui — `plan.py` é explícito que a contagem tem de vir
    // do ledger de `metering`, "nunca de um segundo contador paralelo", então
    // este método só lê o mesmo `monthUsed` que `aiQuota()` já expõe. `null`
    // cobre escopo anônimo, campo ausente ou resposta inesperada — nunca um
    // palpite numérico (CLAUDE.md item 4).
    analisesNoMes: async () => {
      const q = await api.aiQuota();
      return (q && typeof q.monthUsed === "number") ? q.monthUsed : null;
    },
    _setDeviceScope: () => {},    // FASE 3: no-op no web (escopo é server-side por token)
    // FASE 2: web não envia semente — o servidor adota o escopo anônimo/global
    // (que contém a chave BYOK, nunca trafegada ao cliente).
    _localSeed: () => null,
  };
  return _store;
}

/* --------------------------- iPHONE (no aparelho) -------------------------- */
// Persistencia 100% no aparelho usando o armazenamento do proprio WebView
// (localStorage do WKWebView, que sobrevive a fechar/reabrir o app). Sincrono,
// sem plugin nativo e sem import dinamico - nada que possa "travar" no boot.
function deviceStore() {
  // FASE 3 (item 1): escopo por usuário NO APARELHO. Anônimo usa a chave BASE
  // (INALTERADA — usuário existente/sem login não migra nada e não corre risco
  // de tela branca). Logado usa um namespace por user_id. Tudo segue em
  // localStorage (NÃO vira SQLite; os dois backends não se unificam).
  const BASE_KEY = "b3-agente-state-v1";
  const SCOPE_KEY = "b3-device-scope-v1"; // lembra qual usuário está ativo no aparelho
  // FASE 6 (fix 1): o endereço do servidor é uma propriedade do APARELHO, não
  // da conta — antes vivia só dentro do doc escopado por usuário e "sumia" ao
  // trocar de escopo (login/logout), obrigando a recadastrar a cada reinício.
  // Agora é espelhado numa chave GLOBAL, lida no boot de qualquer escopo.
  const SRV_KEY = "b3-server-url-v1";
  function readSrvGlobal() {
    try { const v = typeof localStorage !== "undefined" ? localStorage.getItem(SRV_KEY) : null; return typeof v === "string" ? v : null; }
    catch { return null; }
  }
  function writeSrvGlobal(v) {
    try { if (typeof localStorage !== "undefined") localStorage.setItem(SRV_KEY, String(v == null ? "" : v)); } catch { /* ignore */ }
  }
  let deviceUserId = (() => {
    try { return (typeof localStorage !== "undefined" && localStorage.getItem(SCOPE_KEY)) || null; }
    catch { return null; }
  })();
  let doc = null;

  function storageKey() { return deviceUserId ? (BASE_KEY + "::u:" + deviceUserId) : BASE_KEY; }

  function readKey(k) {
    try {
      const raw = typeof localStorage !== "undefined" ? localStorage.getItem(k) : null;
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }
  function read() { return readKey(storageKey()); }
  function write() {
    try {
      if (typeof localStorage !== "undefined") localStorage.setItem(storageKey(), JSON.stringify(doc));
    } catch {
      /* armazenamento cheio/indisponivel: segue em memoria nesta sessao */
    }
  }
  function ensure() {
    if (!doc) {
      let loaded = read();
      // 1º login NO APARELHO: namespace do usuário ainda vazio adota o doc
      // anônimo como semente (decisão B, local-first). NÃO apaga o anônimo.
      if (!loaded && deviceUserId) {
        const anon = readKey(BASE_KEY);
        loaded = anon ? JSON.parse(JSON.stringify(anon)) : null;
      }
      doc = loaded || defaultState();
      // C1: garante a forma estrutural (config/agent/skill objetos; watchlist/
      // positions/history arrays; cash número) ANTES dos backfills abaixo, que
      // assumem doc.config/doc.agent. Evita tela branca em doc antigo/parcial.
      backfillStructural(doc, defaultState());
      limparCarteiraDemo(doc);   // tira a carteira de fábrica não paga de docs antigos
      if (!doc.analyses || typeof doc.analyses !== "object") doc.analyses = {};
      if (typeof doc.config.serverUrl !== "string") doc.config.serverUrl = "";
      // FASE 6 (fix 1): a chave GLOBAL do aparelho vence o doc do escopo —
      // configurado uma vez, vale para anônimo E para qualquer conta.
      { const g = readSrvGlobal(); if (g !== null) doc.config.serverUrl = g; }
      if (!doc.profile || typeof doc.profile !== "object") doc.profile = defaultState().profile;
      if (!Array.isArray(doc.custom)) doc.custom = [];
      if (doc.agent && typeof doc.agent.intervalMin !== "number") doc.agent.intervalMin = 15;
      if (typeof doc.config.initialBudget !== "number") doc.config.initialBudget = (typeof doc.cash === "number" ? doc.cash : 10000);
      if (doc.config.theme == null) doc.config.theme = "dark";
      if (typeof doc.config.userName !== "string") doc.config.userName = "";
      if (typeof doc.config.onboarded !== "boolean") doc.config.onboarded = false;
      if (!["1mo", "3mo", "6mo", "1y", "2y"].includes(doc.config.candlePeriod)) doc.config.candlePeriod = "1y";
      if (typeof doc.config.vozAtiva !== "boolean") doc.config.vozAtiva = true;
      if (typeof doc.config.vozId !== "string") doc.config.vozId = "";
      if (typeof doc.config.fabVisivel !== "boolean") doc.config.fabVisivel = true;
      if (!doc.config.streak || typeof doc.config.streak !== "object") doc.config.streak = { days: 0, last: "" };
      if (!Array.isArray(doc.equitySnapshots)) doc.equitySnapshots = [];
      if (!doc.config.notif || typeof doc.config.notif !== "object") doc.config.notif = { enabled: false, stop: true, alvo: true, agente: true, variacao: true, gatilho: false };
      if (typeof doc.config.notif.gatilho !== "boolean") doc.config.notif.gatilho = false;  // classe nova: opt-in
      if (!Array.isArray(doc.config.conceitosVistos)) doc.config.conceitosVistos = [];      // camada de entendimento
      if (!doc.config.gestoUso || typeof doc.config.gestoUso !== "object") doc.config.gestoUso = { aberturas: 0, gesto: 0, botao: 0 };  // toque longo: dica + medição
      // FASE 8B (R2): skill da mesa — backfill em docs antigos
      if (!doc.skillOperador || typeof doc.skillOperador !== "object" || typeof doc.skillOperador.text !== "string") {
        doc.skillOperador = { name: "Mesa B3 - Operador v1", text: defaultSkillTextOperador() };
      }
      // FIX-C22 (2026-08-23): upgrade de default LEGADO no aparelho — mesmo
      // contrato de `_eh_default_antigo` em server/app/store.py (default
      // antigo SOBE, edição do usuário é INTOCÁVEL). Só troca quando o texto
      // salvo bate byte a byte com uma entrada de `LEGACY_SKILL_TEXTS`; texto
      // que não casa é edição do usuário e fica como está. Fica aqui (mesmo
      // backfill de `skillOperador` acima) porque é o único ponto que roda em
      // TODO doc carregado, antes de qualquer leitura de skill/skillOperador.
      if (doc.skill && typeof doc.skill.text === "string" && LEGACY_SKILL_TEXTS.includes(doc.skill.text)) {
        doc.skill.text = defaultSkillText();
      }
      if (doc.skillOperador && typeof doc.skillOperador.text === "string" && LEGACY_SKILL_TEXTS.includes(doc.skillOperador.text)) {
        doc.skillOperador.text = defaultSkillTextOperador();
      }
      // FASE 7 (F7.1) — Modo Operador: backfill de docs antigos
      if (doc.config.appMode !== "estudo" && doc.config.appMode !== "operador") doc.config.appMode = "estudo";
      if (doc.config.operadorTermo !== null && typeof doc.config.operadorTermo !== "object") doc.config.operadorTermo = null;
      if (!doc.config.risco || typeof doc.config.risco !== "object") doc.config.risco = { pctPorTrade: 1.0, capital: null };
      // FASE 2: coleção de prompts. Backfill da seção e de chaves novas, sem
      // sobrescrever valores que o usuário já editou.
      if (!doc.llmPrompts || typeof doc.llmPrompts !== "object") doc.llmPrompts = {};
      { const defs = defaultLlmPrompts(); for (const k of Object.keys(defs)) if (typeof doc.llmPrompts[k] !== "string") doc.llmPrompts[k] = defs[k]; }
      write();
    }
    setApiBase(doc.config.serverUrl); // aplica o endereco do servidor (Mac) em runtime
    return doc;
  }
  const customTickers = () => (doc.custom || []).map((c) => c.t);
  const knownTickers = () => [...CATALOG_TICKERS, ...customTickers().filter((t) => !CATALOG_TICKERS.includes(t))];
  function pub() {
    const c = { ...doc.config };
    const k = c.apiKey;
    delete c.apiKey;
    c.keyStored = !!k;
    const catalog = [...CATALOG, ...(doc.custom || []).filter((x) => x && x.t && !CATALOG_TICKERS.includes(x.t))];
    return {
      catalog,
      config: c,
      skill: doc.skill,
      skillOperador: doc.skillOperador,  // FASE 8B (R2)
      watchlist: doc.watchlist,
      cash: doc.cash,
      positions: doc.positions,
      history: doc.history,
      agent: doc.agent,
      analyses: doc.analyses || {},
      profile: doc.profile,
      llmPrompts: doc.llmPrompts || defaultLlmPrompts(),
      custom: doc.custom || [],
      equitySnapshots: doc.equitySnapshots || [],
      optionPositions: doc.optionPositions || [],  // v2 (ADR-003)
      // Fase 2 (realismo de mercado, MERC-02..04): ordem colocada fora do
      // pregão fica pendente até a abertura seguinte; caixaReservado é a
      // soma reservada nelas (D-05, debitada do cash na hora do PEDIDO —
      // sem isto o patrimônio pareceria encolher sozinho ao criar a ordem).
      pendingOrders: doc.pendingOrders || [],
      caixaReservado: typeof doc.caixaReservado === "number" ? doc.caixaReservado : 0,
    };
  }
  const symbolsFor = () => [...new Set([...(doc.watchlist || []), ...doc.positions.map((p) => p.t)])].join(",");
  const now = () => {
    const d = new Date();
    const p = (n) => String(n).padStart(2, "0");
    return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`;
  };
  async function priceOf(t) {
    const r = await api.getQuotes(t);
    const price = r && r.quotes && r.quotes[t] ? r.quotes[t].price : null;
    if (price == null) throw new Error("Sem cotacao para " + t);
    return price;
  }

  // FIX-C02 (Plano 04-05): espelho de store.py.registrar_rejeicao — grava o
  // rastro de uma tentativa de ordem que NÃO executou no ramo LOCAL (sem
  // sessão). NÃO toca cash/positions — rejeição não move dinheiro nenhum.
  // `price=null` é aceito e preservado como null (nunca 0.0, convenção da
  // casa/CLAUDE.md item 4). Poda: mantém no máximo CAP_REJEICOES_LOCAL
  // entradas rejeitadas, descartando as mais antigas primeiro — entradas
  // executadas (ou legadas sem `status`) nunca são tocadas (T-04-02).
  // NÃO chama write() (mesmo padrão de _sellOptionLocal, abaixo) — o
  // chamador grava depois de invocar, mantendo um único ponto de persistência
  // por operação.
  function _registrarRejeicaoLocal(tipo, t, qty, price, motivo) {
    doc.history.unshift({ date: now(), type: tipo, t, qty, price: price == null ? null : +price.toFixed(2), pnl: null, status: "rejeitada", motivo, origem: "manual" });
    const rejeitadasIdx = [];
    doc.history.forEach((h, i) => { if (h && h.status === "rejeitada") rejeitadasIdx.push(i); });
    if (rejeitadasIdx.length > CAP_REJEICOES_LOCAL) {
      const descartar = new Set(rejeitadasIdx.slice(CAP_REJEICOES_LOCAL));
      doc.history = doc.history.filter((_, i) => !descartar.has(i));
    }
  }

  // v2 (ADR-003/005): espelho de store.py.sell_option/close_option_vencida —
  // venda TOTAL/PARCIAL de um contrato, `motivo` estruturado desde o início.
  function _sellOptionLocal(pos, price, qty, motivo) {
    let sold = pos.qty;
    if (typeof qty === "number" && qty > 0) sold = Math.min(pos.qty, Math.max(100, Math.round(qty / 100) * 100));
    const pnl = +((price - pos.avg) * sold).toFixed(2);
    if (sold >= pos.qty) {
      doc.optionPositions = (doc.optionPositions || []).filter((p) => p.id !== pos.id);
    } else {
      pos.qty = pos.qty - sold;
    }
    doc.cash = +(doc.cash + sold * price).toFixed(2);
    doc.history.unshift({ date: now(), type: "VENDA", t: pos.id, underlying: pos.underlying, kind: "opcao", qty: sold, price: +price.toFixed(2), pnl, motivo });
    return pnl;
  }

  // v2 (ADR-005): valor intrínseco na liquidação por vencimento — pode ser
  // ZERO (perda total do prêmio). Espelho de agent.intrinseco_opcao.
  function _intrinsecoOpcao(pos, spot) {
    const strike = pos.strike || 0;
    if (pos.optionType === "put") return Math.max(0, strike - spot);
    return Math.max(0, spot - strike);
  }

  // Cache dos dados tecnicos do ativo (no aparelho), separado do doc principal
  // para nao incha-lo. Guarda no maximo as 6 consultas mais recentes.
  const TKEY = "b3-tech-v1";
  function readTech() {
    try {
      const raw = typeof localStorage !== "undefined" ? localStorage.getItem(TKEY) : null;
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }
  function cacheTech(t, data, period) {
    const key = t + "@" + (period || "1y");
    const o = readTech();
    o[key] = { at: Date.now(), data };
    const keys = Object.keys(o).sort((a, b) => o[b].at - o[a].at);
    for (const k of keys.slice(8)) delete o[k];
    try {
      if (typeof localStorage !== "undefined") localStorage.setItem(TKEY, JSON.stringify(o));
    } catch {
      /* armazenamento cheio: ignora */
    }
  }
  function getCachedTech(t, period) {
    const e = readTech()[t + "@" + (period || "1y")];
    return e ? e.data : null;
  }

  // Push do servidor: o que ele precisa saber e não tem como descobrir.
  //
  // DOIS MESTRES, não um (260824-kc2). Conflacioná-los é a regressão exata que
  // este comentário existe para impedir:
  //
  //   `config.notif.enabled`  → mestre das notificações LOCAIS do front
  //                             (stop, alvo, agente, variação), disparadas
  //                             pelo próprio app.
  //   token registrado        → mestre do push do SERVIDOR. Registrar o token
  //   (`pushTokens`)            é um ato explícito e SEPARADO (`onAtivarPush`
  //                             em App.jsx), e é ele o consentimento.
  //
  // `radar`, `execucao` e `protecao` REFINAM o segundo mestre, por isso são
  // opt-out puro (`!== false`) e NUNCA conjunção com `n.enabled`. Se alguém
  // "uniformizar" a regra escrevendo `!!(n.enabled && n.execucao)`, todo
  // usuário que registrou push e nunca ligou o interruptor LOCAL para de
  // receber execução e proteção — coisas que ele recebe hoje, porque até
  // 2026-08-24 esses call sites do servidor não consultavam preferência
  // nenhuma. É tirar notificação de quem já tem.
  //
  // `gatilho` é a exceção HISTÓRICA e fica como está: conjunção E opt-in. É a
  // única classe disparada por evento de MERCADO sobre ativo que a pessoa só
  // acompanha (sem posição), então mora debaixo do interruptor geral.
  //
  // `gatilho`, `modo` e `universo` são autoridade do APARELHO — só ele
  // registra token APNs. O web não escreve nenhum dos três; o quadro completo
  // de autoridade está acima de `serverStore.syncPushPrefs`.
  function _pushPrefsLocais() {
    const c = (doc && doc.config) || {};
    const n = (c.notif && typeof c.notif === "object") ? c.notif : {};
    const uni = [];
    for (const t of (doc.watchlist || [])) if (t && !uni.includes(t)) uni.push(t);
    for (const p of (doc.positions || [])) if (p && p.t && !uni.includes(p.t)) uni.push(p.t);
    return {
      prefs: {
        gatilho: !!(n.enabled && n.gatilho),
        radar: n.radar !== false,
        execucao: n.execucao !== false,
        protecao: n.protecao !== false,
      },
      modo: c.appMode || "estudo",
      universo: uni,
    };
  }

  // O universo muda em watchlist, compra, venda e no interruptor — quatro ou
  // cinco pontos na UI. Deixar a UI lembrar de sincronizar é garantir que um
  // dia ela esqueça, e o esquecimento significa push sobre a lista de ontem:
  // exatamente a falha que este mecanismo existe para matar. Então o STORE
  // dispara sozinho, com debounce (rajada de compras vira uma chamada só) e
  // best-effort (sem rede, o carimbo velho já perde a validade em 7 dias).
  let _prefsTimer = null;
  function _agendarSyncPrefs() {
    if (_prefsTimer) clearTimeout(_prefsTimer);
    _prefsTimer = setTimeout(() => {
      _prefsTimer = null;
      api.pushRegisterToken("", _pushPrefsLocais()).catch(() => { /* silencioso */ });
    }, 1500);
  }

  // Logado: buy/sell/putPosition passam a mão pro servidor (ele calcula preço,
  // executa e é quem o Operador no servidor lê) — isto absorve a resposta
  // CONFIRMADA por ele no doc local, nunca o que o aparelho tinha calculado
  // sozinho. Mesma regra do putAgent: nunca fingir sucesso local.
  function _adotarCarteiraDoServidor(r) {
    if (!r) return;
    if (Array.isArray(r.positions)) doc.positions = r.positions;
    if (Array.isArray(r.optionPositions)) doc.optionPositions = r.optionPositions;
    if (typeof r.cash === "number") doc.cash = r.cash;
    if (Array.isArray(r.history)) doc.history = r.history;
    // Fase 2 (MERC-02..04): sem isto, uma ordem executada/cancelada pelo
    // servidor (ex.: scheduler abriu o pregão) com o app fechado nunca
    // sumiria da tela do iPhone — mesma classe de defeito do
    // qa/audit-2026-08-08 comentado acima para positions/cash/history.
    if (Array.isArray(r.pendingOrders)) doc.pendingOrders = r.pendingOrders;
    if (typeof r.caixaReservado === "number") doc.caixaReservado = r.caixaReservado;
  }

  return {
    isNative: true,
    // qa/audit-2026-08-08: getState() era só leitura LOCAL — nada no app puxava
    // o servidor de volta depois do boot. Toda mutação que acontece só do lado
    // do servidor (Operador autônomo vendendo com o app fechado, opção
    // comprada/vendida antes deste fix, reset feito por outro aparelho da
    // mesma conta) nunca chegava até aqui: a tela ficava com o caixa/posições
    // de antes, indefinidamente, enquanto o Boris (que lê o banco direto)
    // já mostrava o valor real — sintoma "a tela está certa, só o Boris erra"
    // é exatamente essa lacuna. Logado, cada getState() agora confirma
    // cash/posições/histórico com o servidor, best-effort: falha de rede
    // mantém o doc local (offline continua funcionando), nunca trava a tela.
    async getState() {
      ensure();
      if (sync.hasSession()) {
        try {
          const r = await api.getState();
          _adotarCarteiraDoServidor(r);
          write();
        } catch { /* offline: doc local segue valendo */ }
      }
      return pub();
    },
    async putConfig(patch) {
      ensure();
      const c = doc.config;
      for (const k of ["provider", "model", "baseUrl", "serverUrl"]) if (typeof patch[k] === "string") c[k] = patch[k];
      if (typeof patch.serverUrl === "string") writeSrvGlobal(patch.serverUrl); // FASE 6 (fix 1): espelho global do aparelho
      if (patch.keySource === "env" || patch.keySource === "manual") c.keySource = patch.keySource;
      if (typeof patch.apiKey === "string" && patch.apiKey) c.apiKey = patch.apiKey;
      if (patch.clearKey === true) c.apiKey = "";
      if (typeof patch.initialBudget === "number") c.initialBudget = Math.max(100, Math.min(100000000, +patch.initialBudget.toFixed(2)));
      if (typeof patch.maxTokens === "number") c.maxTokens = Math.max(256, Math.min(200000, +Math.round(patch.maxTokens)));
      if (typeof patch.temperature === "number") c.temperature = Math.max(0, Math.min(2, +patch.temperature.toFixed(2)));
      if (patch.theme === "dark" || patch.theme === "light" || patch.theme === "system") c.theme = patch.theme;
      if (typeof patch.userName === "string") c.userName = patch.userName.trim().slice(0, 40);
      if ("onboarded" in patch) c.onboarded = !!patch.onboarded;
      if ("tourSeen" in patch) c.tourSeen = !!patch.tourSeen;  // qa/38 (Help): tour de 1º uso só aparece 1x
      if ("borisIntroVisto" in patch) c.borisIntroVisto = !!patch.borisIntroVisto;  // F6: apresentação do Boris só aparece 1x
      if (typeof patch.candlePeriod === "string" && ["1mo", "3mo", "6mo", "1y", "2y"].includes(patch.candlePeriod)) c.candlePeriod = patch.candlePeriod;
      if (patch.streak && typeof patch.streak === "object") c.streak = { days: parseInt(patch.streak.days, 10) || 0, last: String(patch.streak.last || "") };
      if (patch.notif && typeof patch.notif === "object") {
        const base = (c.notif && typeof c.notif === "object") ? c.notif : { enabled: false, stop: true, alvo: true, agente: true, variacao: true, gatilho: false, radar: true, execucao: true, protecao: true };
        for (const k of ["enabled", "stop", "alvo", "agente", "variacao", "gatilho", "radar", "execucao", "protecao"]) if (k in patch.notif) base[k] = !!patch.notif[k];
        c.notif = base;
        _agendarSyncPrefs();   // o interruptor do push mora no servidor, não aqui
      }
      // Camada de entendimento: espelho EXATO do store.set_config — UNIÃO,
      // nunca substituição (dois aparelhos do mesmo usuário não se apagam).
      if (Array.isArray(patch.conceitosVistos)) {
        const atual = Array.isArray(c.conceitosVistos) ? c.conceitosVistos : [];
        for (const raw of patch.conceitosVistos) {
          const cid = String(raw || "").slice(0, 40);
          if (cid && !atual.includes(cid)) atual.push(cid);
        }
        c.conceitosVistos = atual.slice(0, 200);
      }
      // Toque longo: contadores MONOTÔNICOS (espelho EXATO do store.set_config)
      // — max, nunca substituição: dois aparelhos do mesmo usuário não
      // rebobinam a dica nem a medição um do outro.
      if (patch.gestoUso && typeof patch.gestoUso === "object") {
        const base = (c.gestoUso && typeof c.gestoUso === "object") ? c.gestoUso : { aberturas: 0, gesto: 0, botao: 0 };
        for (const k of ["aberturas", "gesto", "botao"]) {
          const v = patch.gestoUso[k];
          if (typeof v === "number" && isFinite(v)) base[k] = Math.max(base[k] || 0, Math.min(Math.floor(v), 100000));
        }
        c.gestoUso = base;
      }
      // FASE 7 (F7.1) — Modo Operador (espelho exato do store.py.set_config):
      // termo primeiro; "operador" só liga com termo já aceito (nunca sem aceite).
      if (patch.operadorTermo && typeof patch.operadorTermo === "object" && patch.operadorTermo.aceitoEm && patch.operadorTermo.versao) {
        c.operadorTermo = { aceitoEm: String(patch.operadorTermo.aceitoEm).slice(0, 40), versao: String(patch.operadorTermo.versao).slice(0, 10) };
      }
      if (patch.appMode === "estudo" || patch.appMode === "operador") {
        if (!(patch.appMode === "operador" && !(c.operadorTermo && typeof c.operadorTermo === "object"))) c.appMode = patch.appMode;
        _agendarSyncPrefs();   // o vocabulário do push segue o modo do aparelho
      }
      // 2026-08-09: orçamento SÓ no aparelho (local-first, como o resto da
      // config) nunca chegava ao servidor — MAS resetPortfolio() logado abaixo
      // chama api.resetPortfolio(), que roda no servidor e lê o
      // config.initialBudget DE LÁ. Resultado no iOS, só com conta: editar o
      // orçamento no aparelho não tinha efeito nenhum no servidor, e
      // "Recomeçar do zero" reiniciava com o orçamento VELHO (ou o default
      // 10000) que o servidor nunca tinha aprendido — mesma classe de bug do
      // fix de appMode/operadorTermo logo abaixo, achado só depois porque o
      // sintoma ("some para 10000") é indistinguível do bug de debounce já
      // corrigido em App.jsx. `risco.capital==null` também usa initialBudget
      // como fallback em cálculos que rodam NO SERVIDOR (sizing do Operador,
      // scanDeep) — sem isto, aqueles cálculos também usariam o valor errado.
      if (patch.risco && typeof patch.risco === "object") {
        const base = (c.risco && typeof c.risco === "object") ? c.risco : { pctPorTrade: 1.0, capital: null };
        if (typeof patch.risco.pctPorTrade === "number") base.pctPorTrade = Math.max(0.25, Math.min(5, +patch.risco.pctPorTrade.toFixed(2)));
        if (patch.risco.capital === null) base.capital = null;
        else if (typeof patch.risco.capital === "number") base.capital = Math.max(100, Math.min(100000000, +patch.risco.capital.toFixed(2)));
        c.risco = base;
      }
      // Tela de configuração do Boris — espelho exato do store.py.set_config.
      // Sem isto, o campo escrito aqui nunca chegaria no servidor via sync: o
      // MESMO defeito de allowlist que causava o orçamento voltando a 10000.
      if ("vozAtiva" in patch) c.vozAtiva = !!patch.vozAtiva;
      if (typeof patch.vozId === "string") c.vozId = patch.vozId.slice(0, 200);
      if ("fabVisivel" in patch) c.fabVisivel = !!patch.fabVisivel;
      write();
      setApiBase(doc.config.serverUrl); // se mudou o endereco do Mac, ja passa a valer
      // qa/audit-2026-08-08: appMode/operadorTermo eram 100% locais mesmo
      // logado — o servidor nunca aprendia a troca de modo, então toda trava
      // que depende dele (`store.set_agent`: entradaAuto, mode="executar")
      // ficava presa em "estudo" pra sempre, mesmo com o aparelho em
      // Operador. Sincroniza só os DOIS campos que os gates do servidor
      // precisam — nunca a apiKey, que segue exclusiva do aparelho. Erro
      // sobe (sem engolir): os dois chamadores (ModoTrabalhoCard.escolher,
      // TermoOperadorModal.ativar) já fazem `await` antes do reload, então a
      // troca de modo não "termina" sem o servidor confirmar.
      // 2026-08-17: manda SÓ o campo que o chamador realmente mexeu. Antes ia
      // sempre o trio {appMode, operadorTermo, initialBudget}, e o `appMode`
      // de carona era um DESLIGA-EXECUÇÃO silencioso: editar o ORÇAMENTO com
      // o aparelho em Estudo mandava `appMode:"estudo"` ao servidor, que lê
      // isso como SAÍDA do Modo Operador e reescreve `agent.mode` de
      // "executar" para "sinalizar" (store.py, migração silenciosa) — e voltar
      // para Operador NÃO restaura (guardião test_entrar_no_operador_nao_mexe
      // _no_mode_sinalizar). Sintoma: o gatilho avisa e a ordem nunca executa,
      // com o app mostrando "executar" porque localmente está.
      // Guardião: web/tests/test_putconfig_so_o_que_mudou.mjs
      if (sync.hasSession()) {
        const enviar = {};
        if (patch.appMode === "estudo" || patch.appMode === "operador") enviar.appMode = c.appMode;
        if ("operadorTermo" in patch) enviar.operadorTermo = c.operadorTermo;
        if (typeof patch.initialBudget === "number") enviar.initialBudget = c.initialBudget;
        // 260824-kc2: `notif` passa a subir. Sem isto, o `config.notif` do
        // servidor ficaria eternamente no default e o web reenviaria as três
        // classes LIGADAS por cima do que o aparelho desligou. Com isto, o
        // servidor aprende a mudança no MESMO `putConfig` que a fez — não
        // existe janela.
        //
        // CHAVE A CHAVE, nunca o objeto `c.notif` inteiro (o guardião assere a
        // AUSÊNCIA dessa forma, por isso ela não aparece nem aqui em comentário):
        // `c.notif` é o merge do APARELHO, e o deviceStore nunca lê `config` do
        // servidor.
        // Mandar o objeto inteiro faria desligar `radar` no web e, depois,
        // tocar em QUALQUER controle no iPhone reverter a escolha do web — em
        // silêncio, e valendo também para os cinco controles locais. É a mesma
        // disciplina "sem carona" do resto deste bloco, aplicada DENTRO do
        // campo. O backend já faz merge por chave (store.set_config); o
        // problema é o que o cliente manda.
        if (patch.notif && typeof patch.notif === "object") {
          const nEnviar = {};
          for (const k of Object.keys(patch.notif)) if (k in c.notif) nEnviar[k] = c.notif[k];
          if (Object.keys(nEnviar).length) enviar.notif = nEnviar;
        }
        // Ligar "operador" exige o termo no MESMO patch quando o servidor
        // ainda não o tem (store.set_config) — some junto, nunca sozinho.
        if (enviar.appMode === "operador" && !enviar.operadorTermo && c.operadorTermo) {
          enviar.operadorTermo = c.operadorTermo;
        }
        if (Object.keys(enviar).length) await api.putConfig(enviar);
      }
      return pub();
    },
    async testConfig() {
      ensure();
      return api.testConfig({ ...doc.config });
    },
    async putSkill(b) {
      ensure();
      // FASE 8B (R2): b.modo === "operador" edita a skill da MESA
      const alvo = (b && b.modo === "operador") ? doc.skillOperador : doc.skill;
      if (typeof b.name === "string") alvo.name = b.name;
      if (typeof b.text === "string") alvo.text = b.text;
      write();
      return pub();
    },
    async restoreSkill(modo) {
      ensure();
      if (modo === "operador") doc.skillOperador.text = defaultSkillTextOperador();
      else doc.skill.text = defaultSkillText();
      write();
      return pub();
    },
    async putWatchlist(tickers) {
      ensure();
      const set = new Set(tickers);
      const final = knownTickers().filter((t) => set.has(t));
      // FASE 13 (13-02, CR-01/T-13-05): espelho EM MASSA do gate de
      // addWatchlistTicker abaixo — canGrowWatchlistTo (plan.js) espelha
      // can_grow_watchlist_to (plan.py). Só CRESCIMENTO é barrado: remoção e
      // reordenação nunca tocam a rede e nunca falham offline (T-13-07,
      // grandfather clause D-04 da Fase 12 preservada — conta acima do
      // limite não perde ativos).
      if (final.length > (doc.watchlist || []).length) {
        let quota;
        try {
          quota = await api.watchlistQuota();
        } catch {
          // fail-closed (D-04): falha de rede NUNCA segue para a escrita —
          // aqui o cliente é a ÚNICA defesa (diferente de analisesNoMes, que
          // é fail-open porque o servidor barra de qualquer jeito em
          // _gate_analise).
          throw new Error("Não foi possível confirmar o limite do plano agora. Tente de novo.");
        }
        if (!quota || typeof quota.count !== "number") {
          // resposta inválida/não-numérica recebe o MESMO bloqueio da falha
          // de rede — dado inválido bloqueia, nunca fail-open (CLAUDE.md
          // princípio 4).
          throw new Error("Não foi possível confirmar o limite do plano agora. Tente de novo.");
        }
        const r = canGrowWatchlistTo(final.length, { id: quota.planId || "free", maxWatchlist: quota.limit });
        if (!r.ok) throw new Error(r.reason);
      }
      doc.watchlist = final;
      write();
      _agendarSyncPrefs();   // o universo do push é watchlist ∪ posições
      return pub();
    },
    async addWatchlistTicker(ticker) {
      ensure();
      dlog("a-input", ticker);
      const t = normTicker(ticker);
      dlog("b-normalized", t);
      if (!t || t.length < 4) throw new Error("Informe um ticker válido da B3 (ex.: PETR4).");
      // A existência na B3 é confirmada pelo Yahoo (via servidor). Tenta a rota
      // dedicada /api/validate; se o backend não a tiver, cai para /api/quotes
      // (presente em qualquer versão) — assim o cadastro funciona no iPhone
      // mesmo contra um backend mais antigo.
      let info = null;
      try {
        const v = await api.validateTicker(t);
        dlog("d-validate-resp", v);
        info = { t: normTicker(v.t || t), n: v.n || t, price: v.price, change: v.change };
      } catch (e) {
        dlog("d-validate-falhou", e && e.message);
        try {
          const r = await api.getQuotes(t);
          dlog("d-quotes-fallback", r && r.quotes ? Object.keys(r.quotes) : null);
          const q = r && r.quotes ? (r.quotes[t] || r.quotes[normTicker(t)]) : null;
          if (q && q.price != null) info = { t, n: q.name || t, price: q.price, change: q.change };
        } catch (e2) { dlog("d-quotes-falhou", e2 && e2.message); }
        if (!info) {
          const msg = e && e.message ? e.message : "";
          dlog("e-validacao", "rejeitado: " + msg);
          throw new Error(/404|not found|encontrado/i.test(msg) ? "Ticker " + t + " não encontrado na B3. Verifique o código." : (msg || "Não foi possível validar o ticker agora. Tente de novo."));
        }
      }
      dlog("e-validacao", "ok " + info.t);
      // FASE 13 (13-02, CR-01/T-13-05): gate fail-closed ANTES de qualquer
      // mutação de doc — no iOS não existe gate autoritativo no servidor
      // para watchlist (o aparelho é a fonte da verdade, local-first); esta
      // checagem local é a ÚNICA linha de defesa. Diferente de A.analyze
      // (App.jsx) e analisesNoMes, que são fail-open porque o servidor barra
      // de qualquer jeito (_gate_analise) — aqui falhar-aberto reabriria o
      // bypass do CR-01. Ticker já presente não é crescimento: pular o gate
      // (reenviar o mesmo ativo não pode virar erro de limite).
      if (!doc.watchlist.includes(info.t)) {
        let quota;
        try {
          quota = await api.watchlistQuota();
        } catch {
          throw new Error("Não foi possível confirmar o limite do plano agora. Tente de novo.");
        }
        if (!quota || typeof quota.count !== "number") {
          // resposta inválida/não-numérica bloqueia igual à falha de rede —
          // nunca fail-open (CLAUDE.md princípio 4).
          throw new Error("Não foi possível confirmar o limite do plano agora. Tente de novo.");
        }
        // CR-review Fase 13: `quota.count` é a contagem do SERVIDOR — no iOS
        // (local-first) o aparelho nunca envia sua watchlist pro servidor,
        // então `quota.count` está estruturalmente desconectado do tamanho
        // real do doc local (ficaria sempre defasado/zerado, reabrindo o
        // CR-01 em silêncio). O gate precisa comparar o `count` LOCAL —
        // mesmo raciocínio que já vale pra `canGrowWatchlistTo(final.length,
        // ...)` em putWatchlist logo acima; só `limit`/`planId` vêm do
        // servidor (a fonte real do LIMITE, nunca da contagem local).
        const r = canAddTicker(doc.watchlist.length, { id: quota.planId || "free", maxWatchlist: quota.limit });
        if (!r.ok) throw new Error(r.reason);
      }
      if (!CATALOG_TICKERS.includes(info.t) && !(doc.custom || []).some((c) => c.t === info.t)) {
        doc.custom = [...(doc.custom || []), { t: info.t, n: info.n || info.t }];
      }
      if (!doc.watchlist.includes(info.t)) doc.watchlist = [...doc.watchlist, info.t];
      write();
      dlog("f-store-write", { watchlist: doc.watchlist.length, custom: (doc.custom || []).length, contains: doc.watchlist.includes(info.t) });
      const out = pub();
      out.added = { t: info.t, n: info.n || info.t, price: info.price, change: info.change };
      return out;
    },
    async putSnapshot(snap) {
      ensure();
      doc.equitySnapshots = upsertSnapshot(doc.equitySnapshots || [], snap);
      write();
      return pub();
    },
    async putProfile(patch) {
      ensure();
      const p = doc.profile || (doc.profile = defaultState().profile);
      if (["conservador", "moderado", "agressivo"].includes(patch.risco)) p.risco = patch.risco;
      if (["intraday", "swing", "posicao"].includes(patch.horizonte)) p.horizonte = patch.horizonte;
      if (["preservacao", "renda", "crescimento"].includes(patch.objetivo)) p.objetivo = patch.objetivo;
      if (["iniciante", "intermediario", "avancado"].includes(patch.experiencia)) p.experiencia = patch.experiencia;
      if (typeof patch.toleranciaPerdaPct === "number") p.toleranciaPerdaPct = Math.max(0.5, Math.min(20, +patch.toleranciaPerdaPct.toFixed(2)));
      write();
      return pub();
    },
    async putLlmPrompts(patch) {
      // FASE 2: salva/atualiza a coleção de prompts no aparelho. Aceita um
      // objeto { chave: texto, ... } e mescla apenas valores string.
      ensure();
      if (!doc.llmPrompts || typeof doc.llmPrompts !== "object") doc.llmPrompts = {};
      if (patch && typeof patch === "object") {
        for (const k of Object.keys(patch)) {
          if (typeof patch[k] === "string") doc.llmPrompts[k] = patch[k].slice(0, 8000);
        }
      }
      write();
      return pub();
    },
    async getQuotes() {
      ensure();
      return api.getQuotes(symbolsFor());
    },
    async analyze(t, opts) {
      ensure();
      const account = { cash: doc.cash, budget: doc.config.initialBudget };
      // FASE 8B (R2): a skill enviada acompanha o MODO do aparelho (mesa × professor)
      const skillAtiva = doc.config.appMode === "operador" ? doc.skillOperador : doc.skill;
      if (!doc.analyses) doc.analyses = {};
      const guardada = doc.analyses[t] || null;
      // Paridade com o serverStore: o aparelho também manda a identidade do que
      // já exibe, para o servidor decidir reuso × vencimento.
      const r = await api.analyzeTechnical(t, { config: doc.config, skill: skillAtiva, profile: doc.profile, account, model: (opts && opts.model) || "completo", position: (opts && opts.position) || undefined, promptFp: (opts && opts.promptFp) || (guardada && guardada.promptFp) || undefined });
      if (r && r.reaproveitada && guardada) {
        // A pergunta não mudou: a leitura guardada continua sendo a resposta.
        doc.analyses[t] = { ...guardada, at: r.at, snapshotId: r.snapshotId || guardada.snapshotId, snapshotAt: r.snapshotAt || guardada.snapshotAt };
        write();
        return { ...guardada, ...doc.analyses[t], quote: r.quote, reaproveitada: true };
      }
      const body = r.markdown || r.text || r.analysis || "";
      // `snapshotId`/`snapshotAt`/`promptFp` eram DESCARTADOS aqui — o aparelho
      // guardava a análise sem nenhuma marca da idade dela, então no iOS não
      // havia como saber que a leitura era de outro pregão nem reaproveitá-la.
      // FIX-C01 (Plano 04-05): `fonte`/`iaIndisponivel`/`verbetes`/`semDados`
      // também precisam sobreviver ao reload — sem isso o AiNote reabre
      // rotulado "de IA" sobre texto determinístico persistido. O ramo
      // `reaproveitada` acima preserva estes campos automaticamente via
      // `...guardada` (spread), sem precisar de mudança lá.
      doc.analyses[t] = { kpis: r.kpis || null, detail: r.detail || null, proposal: r.proposal || null, markdown: body, text: r.text || r.analysis || "", model: r.model, modelLabel: r.modelLabel, technicalContext: r.technicalContext || null, candlesSentToLLM: r.candlesSentToLLM, snapshotId: r.snapshotId || null, snapshotAt: r.snapshotAt || null, promptFp: r.promptFp || null, at: r.at, fonte: r.fonte || "ia", iaIndisponivel: r.iaIndisponivel || null, verbetes: r.verbetes || [], semDados: !!r.semDados };
      write();
      return r;
    },
    async analyzeStopAlvo(t, opts) {
      // FASE 3: análise individual de stop/alvo da carteira (prompt configurável
      // + BYOK). Não persiste no aparelho — é transitória, para o popup.
      ensure();
      const account = { cash: doc.cash, budget: doc.config.initialBudget };
      const body = { config: doc.config, profile: doc.profile, account };
      if (opts && opts.prompt) body.prompt = opts.prompt;
      return api.carteiraStopAlvo(t, body);
    },
    async resetPortfolio() {
      ensure();
      const budget = typeof doc.config.initialBudget === "number" ? doc.config.initialBudget : 10000;
      if (sync.hasSession()) {
        // qa/audit-2026-08-08: reset só gravava local, mesmo logado — o
        // servidor (e o Operador que lê de lá) nunca soube da carteira zerada.
        const r = await api.resetPortfolio();
        _adotarCarteiraDoServidor(r);
        doc.analyses = {};
        doc.agent.events = [{ time: "Inicio", kind: "info", text: "Carteira reiniciada com o orçamento simulado de R$ " + doc.cash.toFixed(2) + "." }];
        write();
        return pub();
      }
      doc.cash = +budget.toFixed(2);
      doc.positions = [];
      doc.optionPositions = [];  // v2 (ADR-003)
      doc.pendingOrders = [];  // Fase 2 (MERC-02..04)
      doc.caixaReservado = 0;
      doc.history = [];
      doc.analyses = {};
      doc.agent.events = [{ time: "Inicio", kind: "info", text: "Carteira reiniciada com o orçamento simulado de R$ " + budget.toFixed(2) + "." }];
      write();
      return pub();
    },
    async technicals(t, period) {
      ensure();
      const r = await api.technicals(t, period);
      cacheTech(t, r, period); // guarda os dados do ativo no aparelho (por período)
      return r;
    },
    // Plano 04-06 (FIX-C03): dado público de mercado, sem estado local —
    // pass-through puro, mesmo contrato do serverStore (guardrail de
    // paridade CLAUDE.md: precisa existir nos DOIS, senão o app nativo
    // quebra ao abrir o Passo 8).
    benchmarkIbov: (period) => api.benchmarkIbov(period),
    // BLOCO 3: radar. A varredura roda SEMPRE no servidor (universo + cache de
    // candles vivem lá); o aparelho só consome o resultado — mesma interface.
    async scan(period, tickers, force) {
      ensure();
      return api.scan(period, tickers, force); // FASE 4 (1.3): mesma interface nos dois stores
    },
    // FASE 3 (Operador): mesma interface do serverStore — no aparelho o Diário
    // vem do servidor quando logado; sem conta, mostra os eventos locais.
    async agentLog(n) {
      ensure();
      try { return await api.agentLog(n); }
      catch {
        const ev = ((doc.agent || {}).events || []).slice(0, n || 50);
        return { log: ev, total: ev.length, local: true };
      }
    },
    // FASE 2 (2.1): deep do Radar — roda no servidor; o aparelho só consome.
    // FASE 8B (B3): o modo é local-first no iOS — vai explícito no corpo/query
    // (o cache do deep no servidor é por modo; mesa × professor não se misturam).
    // qa/29 (B-model): scanDeep era a ÚNICA chamada de IA que não mandava
    // `config` (doc.config, com o BYOK/modelo do aparelho) — analyze() e
    // analyzeStopAlvo() sempre mandaram. Sem login (scope=None) e sem BYOK
    // no corpo, o servidor cai em `_ai_apply_managed` sem gerenciada
    // disponível e devolve a config vazia recebida → llm.py explode com
    // "Nenhum modelo de IA configurado." Isso é a causa-raiz de "Plano da
    // mesa (IA) não acha o modelo": o clique nunca mandava o modelo do
    // aparelho pro servidor.
    async scanDeep(body) {
      ensure();
      return api.scanDeep({ config: doc.config, ...(body || {}), appMode: doc.config.appMode || "estudo" });
    },
    async scanDeepEstimate(p, n, t) {
      ensure();
      return api.scanDeepEstimate(p, n, t, doc.config.appMode || "estudo");
    },
    // FASE 2 (2.5): no aparelho o histórico de análises vive no doc local
    // (mesma interface do serverStore; cap 20 por ticker).
    async pushAnalysisLog(t, entry) {
      ensure();
      const key = (t || "").toUpperCase();
      const log = (doc.analysisLog && typeof doc.analysisLog === "object") ? doc.analysisLog : {};
      log[key] = ((log[key] || []).concat([entry || {}])).slice(-20);
      doc.analysisLog = log;
      write();
      return pub();
    },
    // FASE 3.3b: o token vai SEMPRE ao servidor (push é da conta).
    // O servidor NÃO enxerga a config deste aparelho — `putConfig` aqui é
    // local, nunca chama a API. Então consentimento, modo e universo só
    // chegam lá por ESTA chamada, e por isso ela os anexa sempre, mesmo
    // quando quem chamou não passou nada.
    async registerPushToken(token, extra) {
      ensure();
      return api.pushRegisterToken(token, { ..._pushPrefsLocais(), ...(extra || {}) });
    },
    // Reenvia só as preferências (token vazio é ignorado no servidor). Chamado
    // quando o interruptor muda ou a watchlist muda — sem isso o servidor
    // continuaria pushando sobre a lista de ontem.
    async syncPushPrefs() { ensure(); return api.pushRegisterToken("", _pushPrefsLocais()); },
    async scanProgress() { ensure(); return api.scanProgress(); },   // BLOCO B1
    // F1: no aparelho o modo é local-first (como no scanDeep) — vai explícito.
    async timing(t) { ensure(); return api.timing(t, doc.config.appMode || "estudo"); },
    // Camada de entendimento: modo local-first, mesma regra do timing.
    async conceitos(modo, resumido) { ensure(); return api.conceitos(modo || doc.config.appMode || "estudo", resumido); },
    async conceito(cid, body) { ensure(); return api.conceito(cid, { modo: doc.config.appMode || "estudo", ...(body || {}) }); },
    // KB: modo local-first, mesma regra do conceitos/timing.
    async kbBuscar(q, modo) { ensure(); return api.kbBuscar(q, modo || doc.config.appMode || "estudo"); },
    // Assistente: no aparelho o MODELO e a CHAVE são locais — o servidor não
    // os tem. Mandar `config` no corpo é o que evita repetir o qa/29
    // ("Nenhum modelo de IA configurado" em produção, só no iPhone).
    async assistente(body) {
      ensure();
      return api.assistente({ modo: doc.config.appMode || "estudo", config: { ...doc.config }, ...(body || {}) });
    },
    async petResumo(tela) { ensure(); return api.petResumo(doc.config.appMode || "estudo", tela); }, // pet: modo local-first (iPhone); F4: tela escolhe a aba
    async obsLogs(n, level, cat) { ensure(); return api.obsLogs(n, level, cat); }, // FASE 5
    async adminSummary() { ensure(); return api.adminSummary(); }, // F5: painel de admin (só ver)
    async adminMobileHandoff() { ensure(); return api.adminMobileHandoff(); }, // ADR-014
    async brapiProjecao(intervaloS) { ensure(); return api.brapiProjecao(intervaloS); }, // ADR-008
    async brapiProjecaoAplicar(intervaloS) { ensure(); return api.brapiProjecaoAplicar(intervaloS); }, // ADR-008
    async analysisOutcomesStats(modo) { ensure(); return api.analysisOutcomesStats(modo); }, // qa/30 (Fase A)
    async aiActivity() { ensure(); return api.aiActivity(); }, // qa/45
    async aiModels() { ensure(); return api.aiModels(); }, // qa/49: catálogo de modelos (deviceStore/nativo)
    async analysisOutcomesCsv() { ensure(); return api.analysisOutcomesCsv(); }, // qa/35 (P2)
    async agentStatus() { ensure(); return api.agentStatus(); },     // BLOCO D3
    async agentRunNow() { ensure(); return api.agentRunNow(); },     // BLOCO D4
    async pushTest() { ensure(); return api.pushTest(); },           // BLOCO E2
    async optionsExpirations(t) {
      ensure();
      return api.optionsExpirations(t);
    },
    async optionsChain(t, expiration) {
      ensure();
      return api.optionsChain(t, expiration);
    },
    async analyzeOption(body) {
      ensure();
      return api.analyzeOption(body);
    },
    // v2 (ADR-003/004): gate/cadeia sempre vêm do servidor (dado de mercado
    // não se duplica no aparelho); compra/venda gravam no doc LOCAL, espelho
    // de store.py.buy_option/sell_option — mesma regra do resto do deviceStore.
    async optionsGate(t) {
      ensure();
      return api.optionsGate(t);
    },
    async optionsBuy(body) {
      ensure();
      // qa/audit-2026-08-08: opções nunca chegavam ao servidor mesmo logado —
      // mesma causa raiz de buy/sell antes de 41fe428, agora fechada aqui.
      if (sync.hasSession()) {
        const r = await api.optionsBuy(body);
        _adotarCarteiraDoServidor(r);
        write();
        const out = pub();
        out.priceUsed = r && r.priceUsed;
        return out;
      }
      const chain = await api.optionsChain(body.underlying, body.expiration);
      if (chain.providerStatus !== "ok") throw new Error("Cotação de opções indisponível no momento — tente novamente.");
      const contrato = [...(chain.calls || []), ...(chain.puts || [])].find((c) => c.contractSymbol === body.contractSymbol);
      if (!contrato) throw new Error("Contrato não encontrado na cadeia atual.");
      const price = contrato.lastPrice;
      if (typeof price !== "number" || price <= 0) throw new Error("Sem prêmio disponível para este contrato.");
      const qty = Math.max(100, Math.round((body.qty || 0) / 100) * 100);
      if (qty * price > doc.cash) throw new Error("Caixa insuficiente.");
      const m = sanitizeTradeMeta(body.meta);
      const cid = body.contractSymbol;
      const ex = (doc.optionPositions || []).find((p) => p.id === cid);
      if (ex) {
        const tot = ex.qty + qty;
        ex.avg = +(((ex.avg * ex.qty) + price * qty) / tot).toFixed(2);
        ex.qty = tot;
        if (m) ex.setupEntrada = m;
      } else {
        const pos = {
          id: cid, underlying: body.underlying, optionType: contrato.optionType, strike: contrato.strike,
          expiration: chain.expiration, qty, avg: +price.toFixed(2), stop: null, alvo: null, abertaEm: now(),
          ivEntrada: contrato.impliedVolatility ?? null, deltaEntrada: null, hv21Entrada: null,
        };
        if (m) pos.setupEntrada = m;
        doc.optionPositions = [...(doc.optionPositions || []), pos];
      }
      doc.cash = +(doc.cash - qty * price).toFixed(2);
      const entry = { date: now(), type: "COMPRA", t: cid, underlying: body.underlying, kind: "opcao", qty, price: +price.toFixed(2), pnl: null };
      if (m) { entry.setup = m.setup; entry.snapshotId = m.snapshotId; }
      doc.history.unshift(entry);
      write();
      const out = pub();
      out.priceUsed = +price.toFixed(2);
      return out;
    },
    async optionsSell(body) {
      ensure();
      if (sync.hasSession()) {
        const r = await api.optionsSell(body);
        _adotarCarteiraDoServidor(r);
        write();
        const out = pub();
        out.priceUsed = r && r.priceUsed;
        return out;
      }
      const pos = (doc.optionPositions || []).find((p) => p.id === body.contractSymbol);
      if (!pos) throw new Error("Sem posição em " + body.contractSymbol);
      const chain = await api.optionsChain(pos.underlying, pos.expiration);
      if (chain.providerStatus !== "ok") throw new Error("Cotação de opções indisponível no momento — tente novamente.");
      const contrato = [...(chain.calls || []), ...(chain.puts || [])].find((c) => c.contractSymbol === body.contractSymbol);
      const price = contrato && contrato.lastPrice;
      if (typeof price !== "number") throw new Error("Sem prêmio disponível para este contrato.");
      _sellOptionLocal(pos, price, typeof body.qty === "number" ? body.qty : null, "manual");
      write();
      const out = pub();
      out.priceUsed = +price.toFixed(2);
      return out;
    },
    async putOptionPosition(contractId, b) {
      ensure();
      if (sync.hasSession()) {
        const r = await api.putOptionPosition(contractId, b);
        _adotarCarteiraDoServidor(r);
        write();
        return pub();
      }
      const pos = (doc.optionPositions || []).find((p) => p.id === contractId);
      if (pos) {
        if ("stop" in b) pos.stop = b.stop === "" || b.stop == null ? null : Number(b.stop);
        if ("alvo" in b) pos.alvo = b.alvo === "" || b.alvo == null ? null : Number(b.alvo);
      }
      write();
      return pub();
    },
    cachedTechnicals(t, period) {
      return getCachedTech(t, period);
    },
    async aiQuota() {
      ensure();
      return api.aiQuota();
    },
    // FASE 13 (13-01/CR-01): igual a aiQuota acima — `max_watchlist` é dado
    // server-authoritative (D-05), e o aparelho NÃO mantém contador nem
    // cópia do limite: nenhum `10` existe no front, o gate fail-closed de
    // putWatchlist/addWatchlistTicker (abaixo) depende desta leitura ao vivo.
    async watchlistQuota() {
      ensure();
      return api.watchlistQuota();
    },
    // FIX-C33 (Fase 5): mesmo contrato de serverStore.analisesNoMes acima —
    // o aparelho NÃO mantém contador próprio de análises; lê o MESMO
    // `monthUsed` do ledger do servidor via aiQuota(). É por isso que o
    // local-first do iPhone abre exceção aqui, igual já abre para aiQuota.
    async analisesNoMes() {
      ensure();
      const q = await api.aiQuota();
      return (q && typeof q.monthUsed === "number") ? q.monthUsed : null;
    },
    // FASE 3 (item 1): troca o escopo local do aparelho (login/logout). Reseta o
    // doc em cache para recarregar do namespace certo no próximo ensure().
    _setDeviceScope(id) {
      const next = id || null;
      if (next === deviceUserId) return;
      deviceUserId = next;
      doc = null;
      try {
        if (typeof localStorage !== "undefined") {
          if (next) localStorage.setItem(SCOPE_KEY, next);
          else localStorage.removeItem(SCOPE_KEY);
        }
      } catch { /* ignore */ }
    },
    // FASE 2: semente do first-login no iOS — envia o doc LOCAL cru (inclui a
    // chave BYOK) para o servidor adotar como base da conta nova. Não trafega
    // pela rede a não ser num login/registro explícito do usuário.
    _localSeed() {
      ensure();
      return {
        config: { ...doc.config },
        skill: doc.skill,
        skillOperador: doc.skillOperador,  // FASE 8B (R2)
        llmPrompts: doc.llmPrompts || defaultLlmPrompts(),
        watchlist: doc.watchlist,
        cash: doc.cash,
        positions: doc.positions,
        history: doc.history,
        agent: doc.agent,
        analyses: doc.analyses || {},
        profile: doc.profile,
        custom: doc.custom || [],
        equitySnapshots: doc.equitySnapshots || [],
        optionPositions: doc.optionPositions || [],  // v2 (ADR-003)
        pendingOrders: doc.pendingOrders || [],  // Fase 2 (MERC-02..04)
        caixaReservado: typeof doc.caixaReservado === "number" ? doc.caixaReservado : 0,
      };
    },
    // Logado: o servidor EXECUTA (preço, cash, posição, histórico) e devolve
    // o estado confirmado — é ele, não o aparelho, que o Operador no servidor
    // consulta. Sem conta: local, como sempre (nada muda pra quem usa sem
    // login). Erro do servidor SOBE (sem try/catch aqui) — a mesma regra do
    // putAgent: nunca fingir sucesso local quando o servidor recusou.
    async buy(t, qty, meta) {
      ensure();
      if (sync.hasSession()) {
        const r = await api.buy(t, qty, meta);
        _adotarCarteiraDoServidor(r);
        write();
        _agendarSyncPrefs();
        const out = pub();
        out.priceUsed = r && r.priceUsed;
        // Fase 2 (02-06): sem isto, o app nativo nunca sabia que uma ordem
        // virou pendente (mercado fechado) — confirmBuy tomava o ramo de
        // execução imediata (abria stop/alvo para uma posição que ainda não
        // existe). pendingOrders/caixaReservado já eram adotados por
        // _adotarCarteiraDoServidor; faltava só este flag da RESPOSTA (não
        // faz parte do doc persistido, por isso pub() não o carrega sozinho).
        out.pendente = !!(r && r.pendente);
        return out;
      }
      const price = await priceOf(t);
      qty = Math.max(100, Math.round(qty / 100) * 100);
      if (qty * price > doc.cash) {
        // FIX-C02 (Plano 04-05): rastro da rejeição ANTES do throw — espelho
        // de store.py.registrar_rejeicao, mesma frase do erro local (motivo
        // e mensagem lançada precisam ser consistentes).
        const motivo = "Caixa insuficiente.";
        _registrarRejeicaoLocal("COMPRA", t, qty, price, motivo);
        write();
        throw new Error(motivo);
      }
      // FASE 2 (2.4): contexto de ENTRADA (setup do STU) — espelho do store.py
      const m = sanitizeTradeMeta(meta);
      const ex = doc.positions.find((p) => p.t === t);
      if (ex) {
        const tot = ex.qty + qty;
        ex.avg = +(((ex.avg * ex.qty) + price * qty) / tot).toFixed(2);
        ex.qty = tot;
        if (m) ex.setupEntrada = m; // última entrada define o contexto
      } else {
        const pos = { t, qty, avg: +price.toFixed(2), stop: null, alvo: null, abertaEm: now() };
        if (m) pos.setupEntrada = m;
        doc.positions.push(pos);
      }
      doc.cash = +(doc.cash - qty * price).toFixed(2);
      const entry = { date: now(), type: "COMPRA", t, qty, price: +price.toFixed(2), pnl: null, status: "executada" };
      if (m) { entry.setup = m.setup; entry.snapshotId = m.snapshotId; }
      doc.history.unshift(entry);
      write();
      _agendarSyncPrefs();   // posição nova entra no universo do push
      const out = pub();
      out.priceUsed = +price.toFixed(2);
      return out;
    },
    async sell(t, qty) {
      ensure();
      if (sync.hasSession()) {
        const r = await api.sell(t, qty);
        _adotarCarteiraDoServidor(r);
        write();
        _agendarSyncPrefs();
        const out = pub();
        out.priceUsed = r && r.priceUsed;
        out.pendente = !!(r && r.pendente); // Fase 2 (02-06): mesmo motivo do buy(), acima.
        return out;
      }
      const pos = doc.positions.find((p) => p.t === t);
      if (!pos) {
        // FIX-C02 (Plano 04-05): rastro da rejeição ANTES do throw — mesma
        // frase do erro local; sem posição, não há preço/lote a registrar
        // (price=null, nunca 0.0, convenção da casa/CLAUDE.md item 4).
        const motivo = "Sem posicao em " + t;
        _registrarRejeicaoLocal("VENDA", t, (typeof qty === "number" && qty > 0) ? qty : null, null, motivo);
        write();
        throw new Error(motivo);
      }
      const price = await priceOf(t);
      // FASE 2 (2.4): venda TOTAL (qty ausente, comportamento original) ou
      // PARCIAL em lotes de 100, com avg preservado — espelho do store.py.
      let sold = pos.qty;
      if (typeof qty === "number" && qty > 0) {
        sold = Math.min(pos.qty, Math.max(100, Math.round(qty / 100) * 100));
      }
      const pnl = +((price - pos.avg) * sold).toFixed(2);
      if (sold >= pos.qty) {
        doc.positions = doc.positions.filter((p) => p.t !== t);
      } else {
        pos.qty = pos.qty - sold;
      }
      doc.cash = +(doc.cash + sold * price).toFixed(2);
      doc.history.unshift({ date: now(), type: "VENDA", t, qty: sold, price: +price.toFixed(2), pnl, status: "executada" });
      write();
      _agendarSyncPrefs();   // posição encerrada sai do universo do push
      const out = pub();
      out.priceUsed = +price.toFixed(2);
      return out;
    },
    // Fase 2 (MERC-01): roda ANTES do login (D-08, badge na tela de entrada)
    // — sem ensure()/sync.hasSession(), não toca no `doc` local. Existe nos
    // DOIS stores só para não abrir exceção ao guardrail de paridade.
    async marketStatus() {
      return api.marketStatus();
    },
    // Fase 2 (MERC-04): COM sessão, delega ao servidor e adota o estado
    // devolvido (caixa/posição já restaurados). SEM sessão, ordem pendente
    // não existe localmente — o backend recusaria com 401 mesmo assim, e
    // duplicar o motor de pendentes em JS seria criar uma segunda fonte de
    // verdade financeira (proibido pelo princípio 5 do CLAUDE.md). Login é
    // obrigatório no produto (App.jsx:669-674), então este ramo é defensivo.
    async cancelPendingOrder(id) {
      ensure();
      if (sync.hasSession()) {
        const r = await api.cancelPendingOrder(id);
        _adotarCarteiraDoServidor(r);
        write();
        return pub();
      }
      throw new Error("Ordens pendentes exigem conta conectada.");
    },
    async putPosition(t, b) {
      ensure();
      if (sync.hasSession()) {
        const r = await api.putPosition(t, b);
        _adotarCarteiraDoServidor(r);
        write();
        return pub();
      }
      const pos = doc.positions.find((p) => p.t === t);
      if (pos) {
        if ("stop" in b) pos.stop = b.stop === "" || b.stop == null ? null : Number(b.stop);
        if ("alvo" in b) pos.alvo = b.alvo === "" || b.alvo == null ? null : Number(b.alvo);
      }
      write();
      return pub();
    },
    async putAgent(b) {
      ensure();
      if (typeof b.autonomous === "boolean") doc.agent.autonomous = b.autonomous;
      if (typeof b.allocPct === "number") doc.agent.allocPct = Math.max(1, Math.min(20, Math.round(b.allocPct)));
      if (typeof b.intervalMin === "number") doc.agent.intervalMin = Math.max(1, Math.min(240, Math.round(b.intervalMin)));
      // FASE 6 (fix 3): parâmetros do OPERADOR NO SERVIDOR. Antes eram
      // DESCARTADOS em silêncio aqui — no iPhone, "Ativar no servidor" nunca
      // chegava ao backend e o toggle "não funcionava". Agora vão por chamada
      // LIVE (erro sobe para a UI; nada de estado fantasma) e o resultado
      // confirmado pelo servidor é espelhado no doc local.
      // F2: trailingMode/trailingAtrMult/trailingLookback entram AQUI ou o
      // usuário nunca consegue escolher o critério — o backend aceita, mas o
      // patch nem sai do app (mesma armadilha que já engoliu o serverEnabled).
      // F3: alvoDinamico entra pela mesma razão.
      const SERVER_KEYS = ["serverEnabled", "mode", "rules", "trailingPct", "trailingMode",
                           "trailingAtrMult", "trailingLookback", "alvoDinamico", "maxOpsDia",
                           "maxValorOp", "intervalMin", "lastSeenAt", "entradaAuto"];
      const sb = {};
      for (const k of SERVER_KEYS) if (k in (b || {})) sb[k] = b[k];
      if (Object.keys(sb).length) {
        if ("serverEnabled" in sb && !sync.hasSession()) {
          throw new Error("Entre na sua conta para ligar o Operador no servidor (ele roda por conta, com o app fechado).");
        }
        const r = await api.putAgent(sb);
        const ag = (r && r.agent) || {};
        for (const k of SERVER_KEYS) if (k in ag) doc.agent[k] = ag[k];
      }
      write();
      return pub();
    },
    async cycle() {
      ensure();
      const r = await api.getQuotes(doc.positions.map((p) => p.t).join(","));
      const quotes = (r && r.quotes) || {};
      const events = [];
      for (const pos of [...doc.positions]) {
        const price = quotes[pos.t] && quotes[pos.t].price;
        if (price == null) continue;
        const breachStop = pos.stop != null && price <= pos.stop;
        const hitAlvo = pos.alvo != null && price >= pos.alvo;
        if (breachStop || hitAlvo) {
          const motivo = breachStop ? "stop atingido" : "alvo atingido";
          if (doc.agent.autonomous) {
            await this.sell(pos.t);
            events.push({ time: "Agora", kind: "buy", text: `Protecao automatica: ${pos.t} vendido (${motivo}) a R$ ${price.toFixed(2)}.` });
          } else {
            events.push({ time: "Agora", kind: "warn", text: `Atencao: ${pos.t} com ${motivo} (R$ ${price.toFixed(2)}). Modo autonomo desligado.` });
          }
        }
      }
      // v2 (ADR-005): optionPositions avaliadas no MESMO ciclo — vencimento
      // tem prioridade sobre stop/alvo. Tratamento simplificado (sem F2/F3/
      // tetos, mesma divergência já documentada do resto deste ciclo), mas
      // SEM esse ramo o usuário majoritariamente-iOS teria contratos vencendo
      // sem liquidar — o motivo pelo qual o ADR exige replicar aqui.
      const opts = doc.optionPositions || [];
      if (opts.length) {
        const pares = [...new Set(opts.map((p) => p.underlying + "|" + p.expiration))];
        const chains = {};
        for (const key of pares) {
          const [underlying, expiration] = key.split("|");
          try { chains[key] = await api.optionsChain(underlying, expiration); }
          catch { chains[key] = null; }
        }
        const hoje = new Date().toISOString().slice(0, 10);
        for (const pos of [...(doc.optionPositions || [])]) {
          const chain = chains[pos.underlying + "|" + pos.expiration];
          if (!chain || chain.providerStatus !== "ok") continue;  // ADR-004: sem cotação confiável, tenta no próximo ciclo
          const spot = chain.underlyingPrice;
          const contrato = [...(chain.calls || []), ...(chain.puts || [])].find((c) => c.contractSymbol === pos.id);
          const price = contrato && contrato.lastPrice;
          if (pos.expiration && pos.expiration <= hoje) {
            if (typeof spot !== "number") continue;
            const intrinseco = _intrinsecoOpcao(pos, spot);
            if (doc.agent.autonomous) {
              _sellOptionLocal(pos, intrinseco, null, "vencimento");
              events.push({ time: "Agora", kind: "warn", text: `Vencimento: ${pos.id} (${pos.underlying}) liquidado pelo intrínseco (R$ ${intrinseco.toFixed(2)}/ação).` });
            } else {
              events.push({ time: "Agora", kind: "warn", text: `Atenção: ${pos.id} (${pos.underlying}) venceu hoje. Modo autônomo desligado — liquide manualmente.` });
            }
            continue;
          }
          if (typeof price !== "number") continue;
          const breachStop = pos.stop != null && price <= pos.stop;
          const hitAlvo = pos.alvo != null && price >= pos.alvo;
          if (breachStop || hitAlvo) {
            const motivo = breachStop ? "stop" : "alvo";
            if (doc.agent.autonomous) {
              _sellOptionLocal(pos, price, null, motivo);
              events.push({ time: "Agora", kind: "buy", text: `Proteção simulada: opção ${pos.id} (${pos.underlying}) vendida (${motivo} atingido) a R$ ${price.toFixed(2)}.` });
            } else {
              events.push({ time: "Agora", kind: "warn", text: `Atenção: opção ${pos.id} com ${motivo} atingido (R$ ${price.toFixed(2)}). Modo autônomo desligado.` });
            }
          }
        }
      }
      if (!events.length) events.push({ time: "Agora", kind: "info", text: "Ciclo executado - posicoes remarcadas a mercado. Nenhum stop/alvo atingido." });
      doc.agent.events = [...events, ...doc.agent.events].slice(0, 50);
      write();
      const out = pub();
      out.quotes = quotes;
      return out;
    },
  };
}

export const store = isNative ? deviceStore() : serverStore();

// FASE 2 — superfície de autenticação (conta OPCIONAL, decisão A). App.jsx fala
// só com `auth`; a diferença web/iOS de semente fica escondida aqui. Em web,
// após login/registro o token passa a valer e getState() devolve o escopo do
// usuário; em iOS o deviceStore segue local-first (a conta habilita identidade
// e cota de IA — a sincronização ampla de seções é da Fase 3).
function _seedBody() {
  try { return (typeof store._localSeed === "function") ? store._localSeed() : null; }
  catch { return null; }
}

// FASE 3 (item 1): no aparelho, alterna o namespace local para o usuário (ou
// anônimo). No-op no web (escopo é server-side via token).
function _deviceScope(id) {
  if (isNative && typeof store._setDeviceScope === "function") store._setDeviceScope(id || null);
}

export const auth = {
  // Carrega o token salvo no boot (idempotente). Retorna se há sessão.
  bootstrap() { sync.loadToken(); return sync.hasSession(); },
  hasSession: () => sync.hasSession(),
  currentToken: () => sync.loadToken(),
  async me() {
    sync.loadToken();
    if (!sync.hasSession()) return null;
    try {
      const r = await api.authMe();
      if (r && r.user) _deviceScope(r.user.id);   // confirma o namespace local
      return r;
    } catch (e) { // sessão inválida/expirada => limpa e segue anônimo
      if (/401|expirad|login/i.test(e && e.message ? e.message : "")) { sync.clearToken(); sync.cacheClear(); return null; }
      throw e;
    }
  },
  async register({ email, password, name } = {}) {
    const body = { email, password, name };
    const seed = _seedBody(); if (seed) body.seed = seed; // iOS: adota o local
    const r = await api.authRegister(body);
    sync.saveToken(r.token); if (r.state) sync.cacheSet(r.state);
    if (r && r.user) _deviceScope(r.user.id);
    return r;
  },
  async login({ email, password } = {}) {
    const body = { email, password };
    const seed = _seedBody(); if (seed) body.seed = seed;
    const r = await api.authLogin(body);
    sync.saveToken(r.token); if (r.state) sync.cacheSet(r.state);
    if (r && r.user) _deviceScope(r.user.id);
    return r;
  },
  // qa/audit-2026-08-08: `name` e `authorizationCode` chegavam de App.jsx mas
  // eram descartados aqui antes de montar `body` — a Apple só manda o nome no
  // 1º consentimento (LOGIN-SOCIAL.md D1) e o authorizationCode é o que
  // habilita o revoke na exclusão de conta (D7); sem os dois, o servidor
  // nunca recebia nenhum dos dois, silenciosamente, desde a FASE 4.
  async oauth({ provider, idToken, name, authorizationCode } = {}) {
    const body = { provider, idToken };
    if (name) body.name = name;
    if (authorizationCode) body.authorizationCode = authorizationCode;
    const seed = _seedBody(); if (seed) body.seed = seed;
    const r = await api.authOAuth(body);
    sync.saveToken(r.token); if (r.state) sync.cacheSet(r.state);
    if (r && r.user) _deviceScope(r.user.id);
    return r;
  },
  async logout() {
    try { await api.authLogout(); } catch { /* best effort */ }
    sync.clearToken(); sync.cacheClear(); sync.outboxClear();
    _deviceScope(null);                  // volta ao namespace anônimo no aparelho
    return { ok: true };
  },
  async deleteAccount() {
    await api.deleteAccount();            // exige sessão; servidor apaga tudo
    sync.clearToken(); sync.cacheClear(); sync.outboxClear();
    _deviceScope(null);
    return { ok: true };
  },
};

export { isNative };
