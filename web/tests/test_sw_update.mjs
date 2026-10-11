// Guardião do helper atualizarServiceWorker (quick 261011-l5x).
// Best-effort: nunca lança, nunca passa de ~ms. Roda sem build.
import { atualizarServiceWorker } from "../src/swUpdate.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const fakeSw = (reg, extra = {}) => ({
  getRegistration: async () => reg,
  addEventListener: (ev, fn) => { if (extra.dispara === ev) setTimeout(fn, 1); },
  removeEventListener: () => {},
});

ok("sem serviceWorker -> sem-sw", (await atualizarServiceWorker(undefined, 30)) === "sem-sw");
ok("sem getRegistration -> sem-sw", (await atualizarServiceWorker({}, 30)) === "sem-sw");
ok("registro null -> sem-sw", (await atualizarServiceWorker(fakeSw(null), 30)) === "sem-sw");
ok("update ok sem installing/waiting -> atualizado",
  (await atualizarServiceWorker(fakeSw({ update: async () => {} }), 30)) === "atualizado");
ok("installing + controllerchange -> atualizado",
  (await atualizarServiceWorker(fakeSw({ update: async () => {}, installing: {} }, { dispara: "controllerchange" }), 200)) === "atualizado");
ok("waiting sem controllerchange -> timeout",
  (await atualizarServiceWorker(fakeSw({ update: async () => {}, waiting: {} }), 30)) === "timeout");
const t0 = Date.now();
const r = await atualizarServiceWorker(fakeSw({ update: () => new Promise(() => {}) }), 30);
ok("update pendurado -> timeout em ~ms", r === "timeout" && Date.now() - t0 < 500);
ok("update rejeita -> erro",
  (await atualizarServiceWorker(fakeSw({ update: async () => { throw new Error("x"); } }), 30)) === "erro");
ok("getRegistration lança -> erro",
  (await atualizarServiceWorker({ getRegistration: async () => { throw new Error("x"); } }, 30)) === "erro");

if (fails) { console.log(`\n${fails} falha(s).`); process.exit(1); }
console.log("\ntodos os testes passaram.");
