// Camada de SYNC do serverStore (web) — FASE 2.
//
// Decisões: servidor é a FONTE DA VERDADE quando logado (decisão B); cache
// otimista para boot instantâneo e leitura offline; fila offline (outbox) que
// reaplica mutações idempotentes ao reconectar — nada de escrita perdida.
// O token de sessão é persistido aqui e injetado no api.js via setAuthToken.
//
// PURO quanto a plataforma: NÃO importa @capacitor/* — assim roda em node nos
// testes. App.jsx continua falando só com `store`; isto fica escondido.
import { api, setAuthToken } from "./api.js";

const LS = { token: "b3-auth-token-v1", cache: "b3-state-cache-v1", outbox: "b3-outbox-v1" };

function lsGet(k) { try { return typeof localStorage !== "undefined" ? localStorage.getItem(k) : null; } catch { return null; } }
function lsSet(k, v) {
  try {
    if (typeof localStorage === "undefined") return;
    if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v);
  } catch { /* armazenamento cheio/indisponível: segue em memória */ }
}

/* --------------------------------- token --------------------------------- */
export function loadToken() { const t = lsGet(LS.token) || ""; setAuthToken(t); return t; }
export function saveToken(t) { setAuthToken(t || ""); lsSet(LS.token, t || null); }
export function clearToken() { setAuthToken(""); lsSet(LS.token, null); }
export function hasSession() { return !!lsGet(LS.token); }

/* ------------------------------- cache estado ---------------------------- */
export function cacheGet() { try { const r = lsGet(LS.cache); return r ? JSON.parse(r) : null; } catch { return null; } }
export function cacheSet(state) { if (state && typeof state === "object") lsSet(LS.cache, JSON.stringify(state)); return state; }
export function cacheClear() { lsSet(LS.cache, null); }

/* --------------------------------- outbox -------------------------------- */
function outboxRead() { try { const r = lsGet(LS.outbox); const a = r ? JSON.parse(r) : []; return Array.isArray(a) ? a : []; } catch { return []; } }
function outboxWrite(a) { lsSet(LS.outbox, JSON.stringify(a.slice(-200))); }
export function outboxLen() { return outboxRead().length; }
export function outboxClear() { lsSet(LS.outbox, null); }
function enqueue(op) { const a = outboxRead(); a.push({ fn: op.fn, args: op.args || [], at: Date.now() }); outboxWrite(a); }

function isOnline() { try { return typeof navigator === "undefined" || navigator.onLine !== false; } catch { return true; } }
function isNetworkError(e) {
  const m = (e && e.message) || "";
  return /Sem conexão|Tempo esgotado|Failed to fetch|NetworkError|Load failed|Network request failed/i.test(m);
}

// Reaplica a fila na ordem. Para no 1º erro de rede (segue offline); descarta op
// com erro NÃO-transitório (ex.: validação 4xx) para a fila não travar para sempre.
export async function flush() {
  let a = outboxRead();
  while (a.length) {
    const op = a[0];
    const fn = api[op.fn];
    if (typeof fn !== "function") { a = a.slice(1); outboxWrite(a); continue; }
    try {
      await fn(...(op.args || []));
      a = a.slice(1); outboxWrite(a);
    } catch (e) {
      if (isNetworkError(e)) break;
      a = a.slice(1); outboxWrite(a);   // descarta op inválida
    }
  }
  return outboxLen();
}

// MUTAÇÃO idempotente de estado. Online: chama o servidor, atualiza o cache e
// drena a fila. Offline (ou queda na chamada): enfileira, aplica patch otimista
// raso (quando fornecido) e devolve o cache. Erro REAL do servidor é propagado.
export async function mutate(fnName, args, optimistic) {
  if (isOnline()) {
    try {
      const state = await api[fnName](...args);
      cacheSet(state);
      flush().catch(() => {});
      return state;
    } catch (e) {
      if (!isNetworkError(e)) throw e;   // 4xx/5xx do servidor: propaga
      // caiu durante a chamada => trata como offline (cai abaixo)
    }
  }
  enqueue({ fn: fnName, args });
  const cur = cacheGet() || {};
  const next = (typeof optimistic === "function") ? optimistic(cur) : cur;
  return cacheSet(next);
}

// LEITURA de estado. Online: servidor + atualiza cache + drena fila. Offline:
// devolve cache (boot instantâneo, sem crash). Sem cache e offline: tenta o
// servidor mesmo assim (propaga erro acionável do api.js).
export async function readState() {
  if (isOnline()) {
    try { const s = await api.getState(); cacheSet(s); flush().catch(() => {}); return s; }
    catch (e) { if (!isNetworkError(e)) throw e; }
  }
  const c = cacheGet();
  if (c) return c;
  return api.getState();
}

// Chamada que EXIGE servidor (cotação/análise/compra/venda/ciclo): sem fila e
// sem cache — repassa direto e deixa o erro offline ser claro.
export function live(fnName, args) { return api[fnName](...(args || [])); }
