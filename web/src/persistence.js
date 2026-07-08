// Camada de persistencia multiplataforma.
//
//  - WEB: a fonte da verdade e o servidor (FastAPI + SQLite). A chave da API
//    fica no servidor e nunca volta ao cliente.
//  - iPHONE (nativo): a fonte da verdade e o PROPRIO APARELHO. Todo o estado
//    (config + chave, skill, watchlist, carteira, historico, agente) e salvo
//    no armazenamento do WebView (localStorage do WKWebView, que persiste entre
//    aberturas do app). O servidor so e usado para cotacoes e analise; para
//    analisar, o aparelho envia a config + chave no corpo da requisicao.
//
// App.jsx fala apenas com `store`; a diferenca de plataforma fica escondida aqui.
import { Capacitor } from "@capacitor/core";
import { api, setApiBase, setNativeMode } from "./api.js";
import { CATALOG, CATALOG_TICKERS, defaultState, defaultSkillText, defaultLlmPrompts } from "./catalog.js";
import { backfillStructural } from "./migrate.js";
// FASE 2: camada de sync (token + cache otimista + fila offline). serverStore
// passa a falar com o servidor ATRAVÉS dela; deviceStore segue local-first.
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
  return {
    isNative: false,
    getState: () => sync.readState(),
    putConfig: (patch) => sync.mutate("putConfig", [patch], optConfig(patch)),
    testConfig: () => api.testConfig(), // exige servidor (testa a chave ao vivo)
    putSkill: (b) => sync.mutate("putSkill", [b], (cur) => ({ ...cur, skill: { ...(cur.skill || {}), ...b } })),
    restoreSkill: () => sync.mutate("restoreSkill", []),
    putWatchlist: (tickers) => sync.mutate("putWatchlist", [tickers], (cur) => ({ ...cur, watchlist: Array.isArray(tickers) ? [...tickers] : (cur.watchlist || []) })),
    addWatchlistTicker: (ticker) => api.addWatchlistTicker(ticker), // servidor valida no Yahoo (exige rede)
    putProfile: (profile) => sync.mutate("putProfile", [profile], (cur) => ({ ...cur, profile: { ...(cur.profile || {}), ...profile } })),
    putLlmPrompts: (patch) => sync.mutate("putLlmPrompts", [patch], (cur) => ({ ...cur, llmPrompts: { ...(cur.llmPrompts || {}), ...patch } })),
    putSnapshot: (snap) => sync.mutate("putSnapshot", [snap]),
    resetPortfolio: () => sync.mutate("resetPortfolio", []),
    getQuotes: () => api.getQuotes(), // servidor conhece watchlist+posicoes
    analyze: (t, opts) => api.analyzeTechnical(t, { model: (opts && opts.model) || "completo", position: (opts && opts.position) || undefined }),
    analyzeStopAlvo: (t, opts) => api.carteiraStopAlvo(t, (opts && opts.prompt) ? { prompt: opts.prompt } : {}),
    technicals: (t, period) => api.technicals(t, period),
    scan: (period, tickers, force) => api.scan(period, tickers, force), // BLOCO 3 + FASE 2 + FASE 4 (1.3: force)
    scanDeep: (body) => api.scanDeep(body),                       // FASE 2 (2.1): N1 deep
    scanDeepEstimate: (p, n, t) => api.scanDeepEstimate(p, n, t), // FASE 2 (2.1): custo antes
    pushAnalysisLog: (t, entry) => api.pushAnalysisLog(t, entry), // FASE 2 (2.5): telemetria didática
    registerPushToken: (token) => api.pushRegisterToken(token),   // FASE 3.3b: APNs (exige conta)
    scanProgress: () => api.scanProgress(),                        // BLOCO B1
    obsLogs: (n, level, cat) => api.obsLogs(n, level, cat),        // FASE 5: logs do servidor
    agentStatus: () => api.agentStatus(),                          // BLOCO D3
    agentLog: (n) => api.agentLog(n),                              // FASE 3: Diário do operador
    agentRunNow: () => api.agentRunNow(),                          // BLOCO D4
    pushTest: () => api.pushTest(),                                // BLOCO E2
    optionsExpirations: (t) => api.optionsExpirations(t),
    optionsChain: (t, expiration) => api.optionsChain(t, expiration),
    analyzeOption: (body) => api.analyzeOption(body),
    cachedTechnicals: (_t, _period) => null,
    buy: (t, qty, meta) => api.buy(t, qty, meta),  // FASE 2 (2.4): mesma interface do deviceStore
    sell: (t, qty) => api.sell(t, qty),
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
    _setDeviceScope: () => {},    // FASE 3: no-op no web (escopo é server-side por token)
    // FASE 2: web não envia semente — o servidor adota o escopo anônimo/global
    // (que contém a chave BYOK, nunca trafegada ao cliente).
    _localSeed: () => null,
  };
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
      if (!doc.config.streak || typeof doc.config.streak !== "object") doc.config.streak = { days: 0, last: "" };
      if (!Array.isArray(doc.equitySnapshots)) doc.equitySnapshots = [];
      if (!doc.config.notif || typeof doc.config.notif !== "object") doc.config.notif = { enabled: false, stop: true, alvo: true, agente: true, variacao: true };
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

  return {
    isNative: true,
    async getState() {
      ensure();
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
      if (patch.theme === "dark" || patch.theme === "light" || patch.theme === "system") c.theme = patch.theme;
      if (typeof patch.userName === "string") c.userName = patch.userName.trim().slice(0, 40);
      if ("onboarded" in patch) c.onboarded = !!patch.onboarded;
      if (typeof patch.candlePeriod === "string" && ["1mo", "3mo", "6mo", "1y", "2y"].includes(patch.candlePeriod)) c.candlePeriod = patch.candlePeriod;
      if (patch.streak && typeof patch.streak === "object") c.streak = { days: parseInt(patch.streak.days, 10) || 0, last: String(patch.streak.last || "") };
      if (patch.notif && typeof patch.notif === "object") {
        const base = (c.notif && typeof c.notif === "object") ? c.notif : { enabled: false, stop: true, alvo: true, agente: true, variacao: true };
        for (const k of ["enabled", "stop", "alvo", "agente", "variacao"]) if (k in patch.notif) base[k] = !!patch.notif[k];
        c.notif = base;
      }
      // FASE 7 (F7.1) — Modo Operador (espelho exato do store.py.set_config):
      // termo primeiro; "operador" só liga com termo já aceito (nunca sem aceite).
      if (patch.operadorTermo && typeof patch.operadorTermo === "object" && patch.operadorTermo.aceitoEm && patch.operadorTermo.versao) {
        c.operadorTermo = { aceitoEm: String(patch.operadorTermo.aceitoEm).slice(0, 40), versao: String(patch.operadorTermo.versao).slice(0, 10) };
      }
      if (patch.appMode === "estudo" || patch.appMode === "operador") {
        if (!(patch.appMode === "operador" && !(c.operadorTermo && typeof c.operadorTermo === "object"))) c.appMode = patch.appMode;
      }
      if (patch.risco && typeof patch.risco === "object") {
        const base = (c.risco && typeof c.risco === "object") ? c.risco : { pctPorTrade: 1.0, capital: null };
        if (typeof patch.risco.pctPorTrade === "number") base.pctPorTrade = Math.max(0.25, Math.min(5, +patch.risco.pctPorTrade.toFixed(2)));
        if (patch.risco.capital === null) base.capital = null;
        else if (typeof patch.risco.capital === "number") base.capital = Math.max(100, Math.min(100000000, +patch.risco.capital.toFixed(2)));
        c.risco = base;
      }
      write();
      setApiBase(doc.config.serverUrl); // se mudou o endereco do Mac, ja passa a valer
      return pub();
    },
    async testConfig() {
      ensure();
      return api.testConfig({ ...doc.config });
    },
    async putSkill(b) {
      ensure();
      if (typeof b.name === "string") doc.skill.name = b.name;
      if (typeof b.text === "string") doc.skill.text = b.text;
      write();
      return pub();
    },
    async restoreSkill() {
      ensure();
      doc.skill.text = defaultSkillText();
      write();
      return pub();
    },
    async putWatchlist(tickers) {
      ensure();
      const set = new Set(tickers);
      doc.watchlist = knownTickers().filter((t) => set.has(t));
      write();
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
    async analyze(t) {
      ensure();
      const account = { cash: doc.cash, budget: doc.config.initialBudget };
      const r = await api.analyzeTechnical(t, { config: doc.config, skill: doc.skill, profile: doc.profile, account, model: (arguments[1] && arguments[1].model) || "completo", position: (arguments[1] && arguments[1].position) || undefined });
      if (!doc.analyses) doc.analyses = {};
      const body = r.markdown || r.text || r.analysis || "";
      doc.analyses[t] = { kpis: r.kpis || null, detail: r.detail || null, proposal: r.proposal || null, markdown: body, text: r.text || r.analysis || "", model: r.model, modelLabel: r.modelLabel, technicalContext: r.technicalContext || null, candlesSentToLLM: r.candlesSentToLLM, at: r.at };
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
      doc.cash = +budget.toFixed(2);
      doc.positions = [];
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
    async scanDeep(body) {
      ensure();
      return api.scanDeep({ ...(body || {}), appMode: doc.config.appMode || "estudo" });
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
    async registerPushToken(token) {
      ensure();
      return api.pushRegisterToken(token);
    },
    async scanProgress() { ensure(); return api.scanProgress(); },   // BLOCO B1
    async obsLogs(n, level, cat) { ensure(); return api.obsLogs(n, level, cat); }, // FASE 5
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
    cachedTechnicals(t, period) {
      return getCachedTech(t, period);
    },
    async aiQuota() {
      ensure();
      return api.aiQuota();
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
      };
    },
    async buy(t, qty, meta) {
      ensure();
      const price = await priceOf(t);
      qty = Math.max(100, Math.round(qty / 100) * 100);
      if (qty * price > doc.cash) throw new Error("Caixa insuficiente.");
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
      const entry = { date: now(), type: "COMPRA", t, qty, price: +price.toFixed(2), pnl: null };
      if (m) { entry.setup = m.setup; entry.snapshotId = m.snapshotId; }
      doc.history.unshift(entry);
      write();
      const out = pub();
      out.priceUsed = +price.toFixed(2);
      return out;
    },
    async sell(t, qty) {
      ensure();
      const pos = doc.positions.find((p) => p.t === t);
      if (!pos) throw new Error("Sem posicao em " + t);
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
      doc.history.unshift({ date: now(), type: "VENDA", t, qty: sold, price: +price.toFixed(2), pnl });
      write();
      const out = pub();
      out.priceUsed = +price.toFixed(2);
      return out;
    },
    async putPosition(t, b) {
      ensure();
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
      const SERVER_KEYS = ["serverEnabled", "mode", "rules", "trailingPct", "maxOpsDia", "maxValorOp", "lastSeenAt"];
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
  async oauth({ provider, idToken } = {}) {
    const body = { provider, idToken };
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
