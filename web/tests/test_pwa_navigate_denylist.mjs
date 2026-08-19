// Guardião do navigateFallbackDenylist do PWA (web/vite.config.js).
//
// BUG que motivou este teste: o NavigationRoute padrão do Workbox intercepta
// QUALQUER navegação da mesma origem e serve o shell deste app no lugar da
// árvore estática pretendida — já aconteceu com /admin ("/admin abre o app"
// em vez do portal") e reapareceu com /ios ("/ios abre o app" em vez da
// página de instalação Ad Hoc), reportado ao vivo em produção 2026-08-19.
// Toda árvore estática nova servida na mesma origem (server/admin_dist,
// server/ios_dist, ...) precisa entrar no denylist, senão o service worker a
// sequestra silenciosamente assim que fica ativo no navegador do usuário.
// Roda sem build: `node web/tests/test_pwa_navigate_denylist.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "vite.config.js"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

const m = src.match(/navigateFallbackDenylist:\s*\[([^\]]*)\]/);
ok("navigateFallbackDenylist encontrado em vite.config.js", !!m);
const lista = m ? m[1] : "";

// Uma árvore estática nova entra aqui sempre que main.py ganhar um novo
// app.mount(...) fora do catch-all "/" (web_dist) — hoje: /admin e /ios.
const arvoresEsperadas = ["/^\\/admin/", "/^\\/ios/"];
for (const padrao of arvoresEsperadas) {
  ok(`denylist contém ${padrao}`, lista.includes(padrao));
}

if (fails) {
  console.log(`\n${fails} falha(s).`);
  process.exit(1);
}
console.log("\ntodos os testes passaram.");
