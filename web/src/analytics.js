// qa/47 (Fase 2) — client SDK de telemetria de comportamento. Fila local
// persistida em localStorage (mesmo backend usado pelo resto do app, ver
// persistence.js — sobrevive a fechar/reabrir), flush em batch, NUNCA
// bloqueia UI: track() só enfileira (síncrono, engolindo qualquer erro) e
// agenda um flush; a rede acontece fora do caminho de render.
//
// Regra dura de PII (mesma do backend, server/app/analytics.py): properties
// nunca carrega email, CPF, senha, token ou valor monetário real — quem
// chama track() é responsável por isso; o backend rejeita o lote inteiro se
// escapar algo, mas o objetivo aqui é nunca chegar a enviar.
import { api } from "./api.js";

const QUEUE_KEY = "b3-analytics-queue";
const MAX_QUEUE = 500;          // teto local — nunca cresce sem limite no device
const BATCH_SIZE = 50;          // por chamada de POST /api/analytics/events
const FLUSH_DEBOUNCE_MS = 3000;

let currentUserId = null;
let flushTimer = null;
let flushing = false;

function _readQueue() {
  try {
    const raw = typeof localStorage !== "undefined" ? localStorage.getItem(QUEUE_KEY) : null;
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

function _writeQueue(q) {
  try {
    if (typeof localStorage !== "undefined") localStorage.setItem(QUEUE_KEY, JSON.stringify(q));
  } catch {
    /* telemetria nunca pode quebrar o app */
  }
}

// Chamar logo após login/registro/oauth/restauração de sessão (setAuthUser),
// e com null no logout/exclusão de conta — ver App.jsx.
export function setAnalyticsUser(userId) {
  currentUserId = userId || null;
  if (currentUserId) _scheduleFlush(); // usuário chegou — tenta esvaziar o que ficou represado
}

export function track(event, properties) {
  if (!event || typeof event !== "string") return;
  try {
    const q = _readQueue();
    q.push({ event, properties: properties || {}, ts: Date.now() / 1000 });
    while (q.length > MAX_QUEUE) q.shift(); // fila cheia: descarta o mais ANTIGO, nunca trava
    _writeQueue(q);
  } catch {
    return; // nunca propaga — um erro de storage não pode derrubar quem chamou track()
  }
  _scheduleFlush();
}

function _scheduleFlush() {
  if (flushTimer || typeof setTimeout === "undefined") return;
  flushTimer = setTimeout(() => {
    flushTimer = null;
    flush();
  }, FLUSH_DEBOUNCE_MS);
}

// Exportado para o hook de "app foi para background" (App.jsx) chamar sem
// esperar o debounce — no iOS o processo pode ser encerrado logo depois.
export async function flush() {
  if (flushing || !currentUserId) return; // backend exige login (require_user)
  const q = _readQueue();
  if (!q.length) return;
  flushing = true;
  try {
    const lote = q.slice(0, BATCH_SIZE);
    await api.analyticsEvents(lote);
    _writeQueue(q.slice(lote.length)); // só remove o que o servidor confirmou
    if (q.length > lote.length) _scheduleFlush(); // mais eventos pendentes
  } catch {
    // best-effort: sem rede, sem cota, servidor fora — fila fica intacta
  } finally {
    flushing = false;
  }
}

// Só para testes.
export function _reset() {
  currentUserId = null;
  if (flushTimer) { clearTimeout(flushTimer); flushTimer = null; }
  flushing = false;
  _writeQueue([]);
}
