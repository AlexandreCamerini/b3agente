// Cliente da API. Em web usa mesma origem (/api via proxy em dev, ou servido
// pelo backend em produção). No app nativo (iPhone), o endereço do servidor
// (Mac) é configurável na aba Config e aplicado em runtime via setApiBase().
const RAW_BUILD_BASE = (import.meta.env && import.meta.env.VITE_API_BASE) || "";
let runtimeBase = "";
let nativeMode = false; // no iPhone, caminho relativo resolve para o PRÓPRIO app — exigir base absoluta
const TIMEOUT_MS = 15000;
const TIMEOUT_LLM = 90000; // análise/teste da IA demoram

// Mensagem única para o problema de endereçamento do backend no mobile.
const ADDR_HINT = "Configure o endereço do servidor em Perfil → Conta & preferências (ex.: http://SEU_IP:8787) e toque em Testar conexão.";

// FASE 6 (fix 1): URL de PRODUÇÃO embutida como padrão do app NATIVO. Antes,
// sem VITE_API_BASE no build, o iPhone nascia sem endereço — login e tudo o
// mais falhava até o usuário digitar o servidor (e redigitar quando o campo
// se perdia entre escopos). Agora: campo vazio => produção; o campo manual
// vira APENAS override de desenvolvimento (Mac na rede local).
export const PROD_BASE = "https://b3agente-production.up.railway.app";

export function setNativeMode(on) {
  nativeMode = !!on;
  if (nativeMode && !runtimeBase) runtimeBase = PROD_BASE; // padrão imediato no boot
}

// FASE 2 (auth): token de sessão em memória. A PERSISTÊNCIA do token é
// responsabilidade da camada acima (sync.js/persistence.js, via localStorage);
// aqui ele só é anexado como Authorization: Bearer em cada chamada. Sem token =>
// requisições anônimas (escopo legado no servidor) — decisão A.
let authToken = "";
export function setAuthToken(t) { authToken = (typeof t === "string" ? t : "") || ""; }
export function getAuthToken() { return authToken; }

function authHeaders(hasBody) {
  const h = {};
  if (hasBody) h["Content-Type"] = "application/json";
  if (authToken) h["Authorization"] = "Bearer " + authToken;
  return Object.keys(h).length ? h : undefined;
}

function looksLikeLocalHost(u) {
  return /^(localhost|127\.|0\.0\.0\.0|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/i.test(u);
}

function normBase(url) {
  let u = (url || "").trim();
  if (!u) return "";
  if (!/^https?:\/\//i.test(u)) {
    // No mobile, domínio público sem protocolo deve ser HTTPS. IP/localhost mantém HTTP
    // para backend local de desenvolvimento. Evita `b3-production...` virar caminho
    // relativo ou `http://` bloqueado pelo iOS/Railway.
    u = (looksLikeLocalHost(u) ? "http://" : "https://") + u;
  }
  return u.replace(/\/+$/, "").replace(/\/api$/i, ""); // sem barra final, sem /api
}

const BUILD_BASE = normBase(RAW_BUILD_BASE);
runtimeBase = BUILD_BASE;
function asText(v) {
  if (v == null) return "";
  if (typeof v === "string") return v;
  try { return JSON.stringify(v); } catch { return String(v); }
}

function enrichErrorMessage(status, data, path) {
  const detail = data && typeof data === "object" ? (data.detail || data.error || data.message || data._raw) : data;
  const d = detail && typeof detail === "object" ? detail : {};
  const base = d.message || asText(detail) || ("HTTP " + status);
  const where = runtimeBase || "mesma origem";
  const pieces = [base];
  if (d.provider || d.model || d.keySource) {
    pieces.push("Configuração: " + [d.provider ? "provedor=" + d.provider : "", d.model ? "modelo=" + d.model : "", d.keySource ? "chave=" + d.keySource : ""].filter(Boolean).join(", "));
  }
  if (d.action) pieces.push("Como corrigir: " + d.action);
  if (d.hint) pieces.push("Dica: " + d.hint);
  if (status >= 500) pieces.push("Servidor: " + where + path);
  return pieces.filter(Boolean).join("\n");
}

export function describeRuntimeConfig() {
  return { nativeMode, apiBase: getApiBase() };
}


export function setApiBase(url) {
  // Prioridade: override manual > VITE_API_BASE do build > produção (nativo).
  // No web, vazio segue "mesma origem" (o backend serve o próprio app).
  runtimeBase = normBase(url) || BUILD_BASE || (nativeMode ? PROD_BASE : "");
}
export function getApiBase() {
  return runtimeBase || "(mesma origem)";
}

async function fetchWithTimeout(url, opts, timeoutMs = TIMEOUT_MS) {
  const ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
  const timer = ctrl ? setTimeout(() => ctrl.abort(), timeoutMs) : null;
  try {
    return await fetch(url, { ...opts, signal: ctrl ? ctrl.signal : undefined });
  } finally {
    if (timer) clearTimeout(timer);
  }
}

// Leitura robusta do corpo: nunca deixa o .json() do WebView (iOS) estourar um
// erro cru tipo "The string did not match the expected pattern.". Le como texto,
// remove cercas/BOM e tenta extrair o objeto JSON com tolerancia.
async function readBody(res) {
  let text = "";
  try {
    text = await res.text();
  } catch {
    return null;
  }
  if (!text) return null;
  let cleaned = text.replace(/^\uFEFF/, "").trim();
  cleaned = cleaned.replace(/^```(?:json)?/i, "").replace(/```$/i, "").trim();
  try {
    return JSON.parse(cleaned);
  } catch {
    /* tenta extrair o primeiro objeto {...} */
  }
  const start = cleaned.indexOf("{");
  const end = cleaned.lastIndexOf("}");
  if (start !== -1 && end > start) {
    try {
      return JSON.parse(cleaned.slice(start, end + 1));
    } catch {
      /* segue para o fallback bruto */
    }
  }
  return { _raw: cleaned }; // corpo nao-JSON: devolve rotulado, sem quebrar
}

async function req(method, path, body, timeoutMs) {
  // No mobile, base vazia => a chamada iria para o próprio app (HTML), não para
  // o backend. Falha cedo com instrução clara, em vez de quebrar no JSON.parse.
  if (nativeMode && !runtimeBase) {
    throw new Error("Endereço do servidor não configurado. " + ADDR_HINT);
  }
  let res;
  try {
    res = await fetchWithTimeout(
      runtimeBase + path,
      {
        method,
        headers: authHeaders(!!body),
        body: body ? JSON.stringify(body) : undefined,
      },
      timeoutMs
    );
  } catch (e) {
    if (e && (e.name === "AbortError" || /abort/i.test(e.message || ""))) {
      throw new Error("Tempo esgotado ao falar com o servidor (" + getApiBase() + ").");
    }
    throw new Error("Sem conexão com o servidor (" + getApiBase() + ").");
  }
  const data = await readBody(res);
  if (!res.ok) {
    throw new Error(enrichErrorMessage(res.status, data, path));
  }
  if (res.status === 204) return null;
  if (data && data._raw !== undefined && Object.keys(data).length === 1) {
    throw new Error("Resposta do servidor não veio em JSON — o endereço provavelmente aponta para o app, não para o backend. " + ADDR_HINT);
  }
  return data;
}

// Testa um endereço de servidor especifico (sem altera-lo) via /api/health.
export async function testServer(url) {
  const base = normBase(url);
  if (nativeMode && !base && !runtimeBase) {
    return { ok: false, message: "Informe o endereço do servidor (ex.: http://SEU_IP:8787)." };
  }
  let res;
  try {
    res = await fetchWithTimeout((base || runtimeBase) + "/api/health", { method: "GET" });
  } catch (e) {
    if (e && e.name === "AbortError") return { ok: false, message: "Tempo esgotado (servidor fora da rede?)." };
    return { ok: false, message: "Não foi possível conectar (" + (base || getApiBase()) + ")." };
  }
  if (!res.ok) {
    const data = await readBody(res);
    return { ok: false, message: enrichErrorMessage(res.status, data, "/api/health") };
  }
  const j = await readBody(res); // tolerante: não estoura em HTML
  if (j && j._raw !== undefined) {
    return { ok: false, message: "O endereço respondeu, mas não em JSON — provavelmente aponta para o app, não para o backend." };
  }
  return { ok: !!(j && j.ok), message: j && j.ok ? "Servidor respondeu OK." : "Resposta inesperada do endereço." };
}

export const api = {
  getState: () => req("GET", "/api/state"),
  putConfig: (b) => req("PUT", "/api/config", b),
  testConfig: (b) => req("POST", "/api/config/test", b || {}, TIMEOUT_LLM),
  putSkill: (b) => req("PUT", "/api/skill", b),
  restoreSkill: (modo) => req("POST", "/api/skill/restore", modo ? { modo } : {}),
  putWatchlist: (tickers) => req("PUT", "/api/watchlist", { tickers }),
  addWatchlistTicker: (ticker) => req("POST", "/api/watchlist/add", { ticker }),
  validateTicker: (ticker) => req("GET", "/api/validate/" + encodeURIComponent(ticker)),
  putProfile: (profile) => req("PUT", "/api/profile", profile),
  putLlmPrompts: (b) => req("PUT", "/api/llm-prompts", b),
  carteiraStopAlvo: (t, body) => req("POST", "/api/carteira-stopalvo/" + t, body, TIMEOUT_LLM), // FASE 3
  putSnapshot: (snap) => req("POST", "/api/snapshot", snap),
  resetPortfolio: () => req("POST", "/api/reset"),
  getQuotes: (symbols) => req("GET", "/api/quotes" + (symbols ? "?symbols=" + encodeURIComponent(symbols) : "")),
  analyze: (t, body) => req("POST", "/api/analyze/" + t, body, TIMEOUT_LLM),
  technicalModels: () => req("GET", "/api/technical/models"),
  analyzeTechnical: (t, body) => req("POST", "/api/technical/analyze/" + encodeURIComponent(t), body, TIMEOUT_LLM),
  technicals: (t, period) => req("GET", "/api/technicals/" + t + (period ? ("?period=" + encodeURIComponent(period)) : ""), undefined, 30000),
  // BLOCO 3: radar de mercado. Timeout longo — a PRIMEIRA varredura aquece o
  // cache de candles do universo inteiro; as seguintes voltam em segundos.
  scan: (period, tickers, force) => {
    const qs = [];
    if (period) qs.push("period=" + encodeURIComponent(period));
    if (tickers) qs.push("tickers=" + encodeURIComponent(tickers)); // FASE 2: scan restrito (watchlist)
    if (force) qs.push("force=1"); // FASE 4 (1.3): varredura manual recomputa e vira a "do dia"
    return req("GET", "/api/scan" + (qs.length ? "?" + qs.join("&") : ""), undefined, 120000);
  },
  // FASE 2 (2.1): aprofundamento IA do Radar (N1). Estimate mostra o custo em
  // chamadas ANTES de rodar; o deep tem timeout longo (1 chamada de IA por ativo).
  scanDeepEstimate: (period, topN, tickers, appMode) => {
    const q = [];
    if (period) q.push("period=" + encodeURIComponent(period));
    if (topN) q.push("topN=" + encodeURIComponent(topN));
    if (tickers) q.push("tickers=" + encodeURIComponent(tickers));
    if (appMode) q.push("appMode=" + encodeURIComponent(appMode)); // FASE 8B: cache do deep por modo
    return req("GET", "/api/scan/deep/estimate" + (q.length ? "?" + q.join("&") : ""), undefined, 120000);
  },
  scanDeep: (body) => req("POST", "/api/scan/deep", body || {}, 240000),
  pushAnalysisLog: (t, entry) => req("POST", "/api/analysis-log/" + encodeURIComponent(t), entry || {}),   // FASE 2 (2.5)
  pushRegisterToken: (token) => req("POST", "/api/push/register-token", { token }),                        // FASE 3.3b
  scanProgress: () => req("GET", "/api/scan/progress", undefined, 10000),        // BLOCO B1
  agentStatus: () => req("GET", "/api/agent/status", undefined, 15000),          // BLOCO D3
  agentRunNow: () => req("POST", "/api/agent/run-now", {}),                      // BLOCO D4 + FASE 3: responde na hora (ciclo em background)
  agentLog: (n) => req("GET", "/api/agent/log" + (n ? "?n=" + n : "")),           // FASE 3: Diário do operador
  pushTest: () => req("POST", "/api/push/test", {}, 20000),                      // BLOCO E2
  optionsExpirations: (t) => req("GET", "/api/options/expirations/" + encodeURIComponent(t), undefined, 30000),
  optionsChain: (t, expiration) => req("GET", "/api/options/chain/" + encodeURIComponent(t) + (expiration ? "?expiration=" + encodeURIComponent(expiration) : ""), undefined, 30000),
  analyzeOption: (body) => req("POST", "/api/options/analyze", body, TIMEOUT_LLM),
  buy: (t, qty, meta) => req("POST", "/api/buy", meta ? { t, qty, meta } : { t, qty }),   // FASE 2 (2.4): setup de entrada
  sell: (t, qty) => req("POST", "/api/sell", qty ? { t, qty } : { t }),                    // FASE 2 (2.4): venda parcial
  putPosition: (t, b) => req("PUT", "/api/position/" + t, b),
  putAgent: (b) => req("PUT", "/api/agent", b),
  cycle: () => req("POST", "/api/cycle"),
  // FASE 2 (auth multiusuário). register/login podem semear a conta (seed no
  // corpo) — por isso usam o timeout maior.
  authRegister: (body) => req("POST", "/api/auth/register", body, TIMEOUT_LLM),
  authLogin: (body) => req("POST", "/api/auth/login", body, TIMEOUT_LLM),
  authOAuth: (body) => req("POST", "/api/auth/oauth", body, TIMEOUT_LLM),
  authMe: () => req("GET", "/api/auth/me"),
  authLogout: () => req("POST", "/api/auth/logout"),
  deleteAccount: () => req("DELETE", "/api/account"),
  aiQuota: () => req("GET", "/api/ai/quota"), // FASE 3: estado da IA gerenciada (cota/BYOK)
  aiModels: () => req("GET", "/api/ai/models"), // qa/49: catálogo de modelos por provedor + parâmetros
  // FASE 5: observabilidade — logs detalhados do servidor (restrito ao admin).
  obsLogs: (n, level, cat) => {
    const q = [];
    if (n) q.push("n=" + encodeURIComponent(n));
    if (level) q.push("level=" + encodeURIComponent(level));
    if (cat) q.push("cat=" + encodeURIComponent(cat));
    return req("GET", "/api/obs/logs" + (q.length ? "?" + q.join("&") : ""), undefined, 15000);
  },
  // qa/30 (Fase A): autoavaliação da IA — estatísticas do painel "Eficiência
  // da IA" (Perfil → Observabilidade). `modo` opcional filtra estudo/operador.
  analysisOutcomesStats: (modo) => req("GET", "/api/analysis-outcomes/stats" + (modo ? "?modo=" + encodeURIComponent(modo) : ""), undefined, 15000),
  aiActivity: () => req("GET", "/api/ai-activity", undefined, 15000), // qa/45: custo + histórico da IA
  // qa/35 (P2): export CSV da eficiência — TEXTO puro, não passa pelo parse
  // JSON do req() (readBody embrulharia em {_raw}).
  analysisOutcomesCsv: async () => {
    if (nativeMode && !runtimeBase) throw new Error("Endereço do servidor não configurado. " + ADDR_HINT);
    const res = await fetchWithTimeout(runtimeBase + "/api/analysis-outcomes/export.csv", { method: "GET", headers: authHeaders(false) }, 15000);
    if (!res.ok) throw new Error("Export falhou (HTTP " + res.status + ")");
    return res.text();
  },
};
