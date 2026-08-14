// Cliente HTTP mínimo — sempre mesma origem (servido pelo mesmo backend do
// app consumidor, sob /admin/*), então caminho relativo basta. Sem o suporte
// a base configurável/nativo que web/src/api.js precisa (esta app é só web).
const TOKEN_KEY = "b3-admin-token";
const TIMEOUT_MS = 15000;

export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY) || ""; } catch { return ""; }
}

export function setToken(t) {
  try {
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
  } catch { /* ignore */ }
}

async function req(method, path, body) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  let res;
  try {
    res = await fetch(path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    });
  } catch (e) {
    if (e && e.name === "AbortError") throw new Error("Tempo esgotado ao falar com o servidor.");
    throw new Error("Sem conexão com o servidor.");
  } finally {
    clearTimeout(timer);
  }
  let data = null;
  try { data = await res.json(); } catch { /* resposta sem corpo/JSON */ }
  if (!res.ok) {
    const msg = (data && (data.detail || data.message)) || ("Erro " + res.status);
    const err = new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    err.status = res.status;
    throw err;
  }
  return data;
}

export const api = {
  login: (email, password) => req("POST", "/api/auth/login", { email, password }),
  agentStatus: () => req("GET", "/api/agent/status"),
  obsUsage: () => req("GET", "/api/obs/usage"),
  analyticsSummary: (dias) => req("GET", "/api/analytics/summary" + (dias ? "?dias=" + encodeURIComponent(dias) : "")),
  iaEficiencia: () => req("GET", "/api/analytics/ia-eficiencia"),
};
