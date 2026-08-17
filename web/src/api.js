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
// 2026-08-08: o endereço de produção passou a ser o domínio próprio
// `boris.semente.dev` (decisão do Alex: TODO endpoint sai por ele). A URL
// interna do Railway continua respondendo, mas ninguém no código deve apontar
// para ela — trocar de provedor ou de serviço não pode exigir rebuild do app
// nativo, e o app nativo é justamente quem carrega este valor embutido.
export const PROD_BASE = "https://boris.semente.dev";

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
  // FASE 3.3b + push do gatilho: o corpo carrega TAMBÉM consentimento, modo e
  // universo — no aparelho a config é local e o servidor não tem outra via.
  pushRegisterToken: (token, extra) => req("POST", "/api/push/register-token", { token, ...(extra || {}) }),
  // Camada de entendimento (custo zero: texto determinístico do backend).
  conceitos: (modo, resumido) => req("GET", "/api/conceitos?modo=" + encodeURIComponent(modo || "estudo") + (resumido ? "&resumido=true" : ""), undefined, 15000),
  conceito: (cid, body) => req("POST", "/api/conceito/" + encodeURIComponent(cid), body || {}, 15000),
  // Base de conhecimento (Fase F3): busca pública, custo zero, sem conta —
  // mesma camada que /api/assistente já consulta primeiro por dentro.
  kbBuscar: (q, modo) => req("GET", "/api/kb/buscar?q=" + encodeURIComponent(q || "") + (modo ? "&modo=" + encodeURIComponent(modo) : ""), undefined, 15000),
  // Assistente: a KB responde primeiro (grátis, sem conta); só cai para a
  // LLM (camada PAGA, exige conta) quando ela não cobre — o servidor decide
  // sozinho e devolve `fonte: "kb" | "llm"`.
  assistente: (body) => req("POST", "/api/assistente", body || {}, TIMEOUT_LLM),
  // O PET: resumo determinístico da tela (custo zero; frases prontas do
  // servidor). F4: `tela` escolhe QUAL aba resumir — allowlist é
  // conceitos.PET_TELAS, o mesmo registro do /api/assistente.
  // qa/audit-2026-08-08 (Fase 1): `modo` forçava "estudo" quando ausente —
  // no WEB, `serverStore.petResumo` chama SEM modo de propósito ("pet: modo
  // fica com o servidor"), mas isso mandava `?modo=estudo` explícito mesmo
  // assim, e `get_pet_resumo` dá precedência ao query param sobre
  // `cfg.appMode` — então o resumo (fala/perguntas) do web SEMPRE saía no
  // vocabulário de Estudo, mesmo com a conta em Modo Operador. Mesmo
  // contrato de `timing` acima: omitir o param deixa o servidor decidir
  // pela config do escopo.
  petResumo: (modo, tela) => req("GET", "/api/pet/resumo?tela=" + encodeURIComponent(tela || "mercado") + (modo ? "&modo=" + encodeURIComponent(modo) : ""), undefined, 15000),
  scanProgress: () => req("GET", "/api/scan/progress", undefined, 10000),        // BLOCO B1
  // F1 (timing de entrada): estado determinístico plano diário × barra 15m
  // FECHADA — O(1) no servidor, zero fetch/LLM. iOS manda ?appMode (modo é
  // local-first no aparelho); web omite e o servidor usa a config do escopo.
  timing: (t, appMode) => req("GET", "/api/timing/" + encodeURIComponent(t) + (appMode ? "?appMode=" + encodeURIComponent(appMode) : ""), undefined, 15000),
  agentStatus: () => req("GET", "/api/agent/status", undefined, 15000),          // BLOCO D3
  agentRunNow: () => req("POST", "/api/agent/run-now", {}),                      // BLOCO D4 + FASE 3: responde na hora (ciclo em background)
  agentLog: (n) => req("GET", "/api/agent/log" + (n ? "?n=" + n : "")),           // FASE 3: Diário do operador
  pushTest: () => req("POST", "/api/push/test", {}, 20000),                      // BLOCO E2
  optionsExpirations: (t) => req("GET", "/api/options/expirations/" + encodeURIComponent(t), undefined, 30000),
  optionsChain: (t, expiration) => req("GET", "/api/options/chain/" + encodeURIComponent(t) + (expiration ? "?expiration=" + encodeURIComponent(expiration) : ""), undefined, 30000),
  analyzeOption: (body) => req("POST", "/api/options/analyze", body, TIMEOUT_LLM),
  // v2 (ADR-003/004/005): gate de descobribilidade + carteira simulada de opções.
  optionsGate: (t) => req("GET", "/api/options/gate/" + encodeURIComponent(t), undefined, 30000),
  optionsBuy: (body) => req("POST", "/api/options/buy", body),
  optionsSell: (body) => req("POST", "/api/options/sell", body),
  putOptionPosition: (contractId, b) => req("PUT", "/api/options/position/" + encodeURIComponent(contractId), b),
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
  // F5 (2026-08-02): painel de admin v1 SÓ VER — restrito ao admin (mesmo
  // portão de obsLogs/obsUsage). Usuários, uso de IA, saúde do agente, gate.
  adminSummary: () => req("GET", "/api/admin/summary", undefined, 15000),
  // ADR-008 (controle de utilização): simula (GET) e aplica (POST) o
  // intervalo de atualização do spot da brapi — mesmo portão de admin.
  // GET sem intervaloS devolve a projeção do intervalo vigente.
  brapiProjecao: (intervaloS) => req("GET", "/api/obs/brapi/projecao" + (intervaloS != null ? "?intervaloS=" + encodeURIComponent(intervaloS) : ""), undefined, 15000),
  brapiProjecaoAplicar: (intervaloS) => req("POST", "/api/obs/brapi/projecao", { intervaloS, aplicar: true }, 15000),
  // ADR-014: mint um código de handoff (curto, uso único) trocável pelo
  // web-admin/ embutido no browser in-app — mesmo portão de admin.
  adminMobileHandoff: () => req("POST", "/api/admin/mobile-handoff", {}, 15000),
  // qa/47 (Fase 2): ingest em lote de eventos de comportamento — ver analytics.js.
  analyticsEvents: (events) => req("POST", "/api/analytics/events", { events }, 15000),
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
