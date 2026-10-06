// Quick 261006-oav (2026-10-06) — fila de concorrência e dedupe do gate de opções.
// Roda isolado: `node web/tests/test_fila_gate.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { criarFila, criarGateCacheado, GATE_CONCORRENCIA_MAX } from "../src/filaGate.js";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const tick = () => new Promise((r) => setTimeout(r, 0));

// --- criarFila ---------------------------------------------------------
{
  const fila = criarFila(2);
  let ativos = 0, max = 0;
  const inicio = [];
  const ctrl = [];
  const ps = [];
  for (let i = 0; i < 10; i++) {
    ps.push(fila(() => new Promise((res, rej) => {
      ativos++; max = Math.max(max, ativos); inicio.push(i);
      ctrl.push({ res: () => { ativos--; res(i); }, rej: () => { ativos--; rej(new Error("x" + i)); } });
    })));
  }
  await tick();
  ok("fila: só 2 rodando no início", ativos === 2 && ctrl.length === 2);
  let falhou = null;
  ps[0].catch((e) => { falhou = e.message; });
  ctrl[0].rej();          // a tarefa 0 rejeita: libera o slot
  await tick();
  ok("fila: rejeição libera slot e propaga só ao próprio chamador", falhou === "x0" && ctrl.length === 3);
  let k = 1;
  while (k < ctrl.length) { ctrl[k].res(); k++; await tick(); }
  const rest = await Promise.all(ps.slice(1));
  ok("fila: todas resolvem", rest.length === 9 && rest.every((v, i) => v === i + 1));
  ok("fila: nunca > 2 simultâneos", max <= 2);
  ok("fila: ordem de início FIFO", inicio.join(",") === "0,1,2,3,4,5,6,7,8,9");
}

// --- criarGateCacheado ---------------------------------------------------
{
  let chamadas = 0, ativos = 0, max = 0, t = 0;
  const buscar = async (tk) => {
    chamadas++; ativos++; max = Math.max(max, ativos);
    await new Promise((r) => setTimeout(r, 5));
    ativos--;
    return { ticker: tk, providerStatus: "ok", liquida: true };
  };
  const gate = criarGateCacheado({ buscar, limite: 2, ttlMs: 120000, agora: () => t });
  const [a, b, c] = await Promise.all([gate("PETR4"), gate("PETR4"), gate("PETR4")]);
  ok("dedupe: 3 chamadas do mesmo ticker -> 1 busca", chamadas === 1 && a === b && b === c);
  await gate("PETR4");
  ok("TTL: ok reaproveitado dentro do prazo", chamadas === 1);
  t = 120001;
  await gate("PETR4");
  ok("TTL: rebusca após o prazo", chamadas === 2);
  chamadas = 0; max = 0;
  await Promise.all(Array.from({ length: 12 }, (_, i) => gate("T" + i)));
  ok("12 tickers distintos: máximo simultâneo <= 2", max <= 2 && chamadas === 12);
}
{
  let chamadas = 0;
  const respostas = [{ providerStatus: "degraded" }, { ticker: "X" }, null];
  const gate = criarGateCacheado({ buscar: async () => { chamadas++; return respostas[(chamadas - 1) % 3]; } });
  await gate("A"); await gate("A"); await gate("A");
  ok("degraded / sem providerStatus / nulo NÃO são cacheados", chamadas === 3);
  let n = 0;
  const g2 = criarGateCacheado({ buscar: async () => { n++; if (n === 1) throw new Error("rede"); return { providerStatus: "ok" }; } });
  let erro = false;
  try { await g2("B"); } catch { erro = true; }
  const r = await g2("B");
  ok("erro não é cacheado nem fica preso em voo", erro && r.providerStatus === "ok" && n === 2);
}

// --- guardião estático --------------------------------------------------
{
  const src = readFileSync(join(here, "..", "src", "api.js"), "utf8")
    .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
  ok("api.js: optionsGate passa por criarGateCacheado", /criarGateCacheado\(/.test(src) && /optionsGate:\s*\(t\)\s*=>\s*gateCacheado\(t\)/.test(src));
  ok("GATE_CONCORRENCIA_MAX <= 2", GATE_CONCORRENCIA_MAX <= 2);
  const cnt = (s) => (s.match(/store\.optionsGate\(/g) || []).length;
  const strip = (s) => s.split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
  const app = strip(readFileSync(join(here, "..", "src", "App.jsx"), "utf8"));
  const uop = strip(readFileSync(join(here, "..", "src", "opcoes", "useOpcoesPropostas.js"), "utf8"));
  ok("store.optionsGate( 1x em App.jsx e 1x em useOpcoesPropostas.js", cnt(app) === 1 && cnt(uop) === 1);
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntudo ok");
