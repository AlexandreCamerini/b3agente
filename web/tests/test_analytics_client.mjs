// qa/47 (Fase 2) — client SDK de analytics (src/analytics.js): fila local
// persistida, debounce de flush, nunca bloqueia UI mesmo sem rede/sem
// usuário logado. Roda sem build: `node web/tests/test_analytics_client.mjs`.
//
// Polyfill mínimo de localStorage — Node não tem por padrão, e o módulo
// precisa dele pra fila persistida (mesmo backend que persistence.js usa
// pro resto do app). Precisa existir ANTES do import de analytics.js.
const _store = {};
globalThis.localStorage = {
  getItem: (k) => (Object.prototype.hasOwnProperty.call(_store, k) ? _store[k] : null),
  setItem: (k, v) => { _store[k] = String(v); },
  removeItem: (k) => { delete _store[k]; },
};

import { api } from "../src/api.js";
import { track, flush, setAnalyticsUser, _reset } from "../src/analytics.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const queue = () => JSON.parse(localStorage.getItem("b3-analytics-queue") || "[]");

async function withMockApi(impl, fn) {
  const original = api.analyticsEvents;
  api.analyticsEvents = impl;
  try { await fn(); } finally { api.analyticsEvents = original; }
}

async function run() {
  // 1) sem usuário logado (antes do login resolver, ou pós-logout): track()
  // enfileira normalmente, mas flush() NUNCA manda pro servidor — o backend
  // exige Bearer token (require_user) e não há como anexar um.
  _reset();
  let calls = [];
  await withMockApi(async (events) => { calls.push(events); return { accepted: events.length }; }, async () => {
    track("portfolio_view");
    await flush();
    ok("sem usuário: flush não chama a API", calls.length === 0);
    ok("sem usuário: evento fica retido na fila local", queue().length === 1);
  });

  // 2) com usuário, flush esvazia a fila e manda o lote certo, na ordem
  _reset();
  calls = [];
  await withMockApi(async (events) => { calls.push(events); return { accepted: events.length }; }, async () => {
    setAnalyticsUser("u1");
    track("trade_simulated", { side: "buy", ticker: "PETR4" });
    track("session_start");
    await flush();
    ok("com usuário: flush chama a API 1x", calls.length === 1);
    ok("com usuário: lote tem os 2 eventos, na ordem de disparo",
       calls[0].length === 2 && calls[0][0].event === "trade_simulated" && calls[0][1].event === "session_start");
    ok("com usuário: properties chega junto", calls[0][0].properties.ticker === "PETR4");
    ok("com usuário: cada evento carrega ts", typeof calls[0][0].ts === "number" && calls[0][0].ts > 0);
    ok("com usuário: fila local esvazia só depois do servidor confirmar", queue().length === 0);
  });

  // 3) falha de rede/servidor: best-effort — nunca lança, e a fila NÃO é
  // descartada (tenta de novo no próximo flush agendado).
  _reset();
  await withMockApi(async () => { throw new Error("sem rede"); }, async () => {
    setAnalyticsUser("u1");
    track("portfolio_view");
    let threw = false;
    try { await flush(); } catch { threw = true; }
    ok("falha no flush não propaga exceção pro chamador", !threw);
    ok("falha no flush preserva a fila local (nada se perde)", queue().length === 1);
  });

  // 4) teto local: a fila NUNCA cresce sem limite, descarta o mais ANTIGO.
  _reset();
  for (let i = 0; i < 520; i++) track("session_start", { i });
  const q = queue();
  ok("fila local respeita o teto (500)", q.length === 500);
  ok("teto descarta o mais ANTIGO, preserva o mais recente", q[q.length - 1].properties.i === 519);

  // 5) track() com evento inválido nunca lança e nunca enfileira lixo —
  // telemetria não pode ser a causa de um crash de tela.
  _reset();
  let threwInvalid = false;
  try { track(""); track(null); track(undefined); track(42); } catch { threwInvalid = true; }
  ok("track() com evento inválido não lança", !threwInvalid);
  ok("track() com evento inválido não enfileira nada", queue().length === 0);

  // 6) logout (setAnalyticsUser(null)) trava o flush até logar de novo —
  // a fila continua sendo escrita localmente, só não sai do aparelho.
  _reset();
  calls = [];
  await withMockApi(async (events) => { calls.push(events); return { accepted: events.length }; }, async () => {
    setAnalyticsUser("u1");
    setAnalyticsUser(null);
    track("session_end");
    await flush();
    ok("pós-logout: flush não manda nada mesmo com fila pendente", calls.length === 0);
  });

  console.log(fails ? `\n${fails} FALHA(S) NO CLIENT SDK DE ANALYTICS` : "\nCLIENT SDK DE ANALYTICS OK");
  process.exit(fails ? 1 : 0);
}

run();
