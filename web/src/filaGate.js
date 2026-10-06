// Fila de concorrência + dedupe/TTL do gate de liquidez de opções.
//
// 2026-10-06 (quick 261006-oav): incidente da Mesa — N AtivoCards disparavam
// `GET /api/options/gate/<t>` no mount, de uma vez, e a rajada esgotou a cota
// do mydata (o POST /api/options/buy do usuário levou 502). Aqui o front nunca
// tem mais que GATE_CONCORRENCIA_MAX gates em voo, deduplica o mesmo ticker e
// reaproveita resultado "ok" por GATE_TTL_MS.
//
// Por que a fila mora em api.js (e não em App.jsx/useOpcoesPropostas): os
// contadores de `store.optionsGate(` são travados por guardiões estáticos, e a
// paridade deviceStore<->serverStore é preservada porque ambos delegam a
// `api.optionsGate`. O timeout de 30 s da requisição começa quando ela SAI da
// fila (o `buscar` só roda ao ganhar o slot), não enquanto espera.
//
// Módulo PURO: sem import de api/persistence/Capacitor.
export const GATE_CONCORRENCIA_MAX = 2;
export const GATE_TTL_MS = 120000;

export function criarFila(limite) {
  const max = Math.max(1, limite | 0);
  let ativos = 0;
  const espera = [];
  const proximo = () => {
    while (ativos < max && espera.length) {
      const { tarefa, resolve, reject } = espera.shift();
      ativos++;
      let p;
      try { p = Promise.resolve(tarefa()); } catch (e) { p = Promise.reject(e); }
      p.then(resolve, reject).finally(() => { ativos--; proximo(); });
    }
  };
  return (tarefa) => new Promise((resolve, reject) => {
    espera.push({ tarefa, resolve, reject });
    proximo();
  });
}

export function criarGateCacheado({ buscar, limite = GATE_CONCORRENCIA_MAX, ttlMs = GATE_TTL_MS, agora = () => Date.now() }) {
  const fila = criarFila(limite);
  const emVoo = new Map();
  const cache = new Map();
  return (t) => {
    const hit = cache.get(t);
    if (hit && agora() - hit.em < ttlMs) return Promise.resolve(hit.valor);
    if (emVoo.has(t)) return emVoo.get(t);
    const p = fila(() => buscar(t))
      .then((valor) => {
        // Só "ok" é reaproveitado: degradado/erro não se cacheia (espelha A-07 do backend).
        if (valor && valor.providerStatus === "ok") cache.set(t, { em: agora(), valor });
        return valor;
      })
      .finally(() => { emVoo.delete(t); });
    emVoo.set(t, p);
    return p;
  };
}
