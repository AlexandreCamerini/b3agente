// Fase 46, Plano 04 — carteiraLeitura existe nos DOIS stores e delega a
// api.carteiraLeitura (leitura determinística é do backend; o aparelho não
// duplica cálculo). Roda sem build: node web/tests/test_carteira_leitura_paridade.mjs
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const pers = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const api = readFileSync(join(here, "..", "src", "api.js"), "utf8");

let fails = 0;
const ok = (n, c) => { console.log((c ? "ok " : "FALHOU ") + n); if (!c) fails++; };

const iServer = pers.indexOf("function serverStore()");
const iDevice = pers.indexOf("function deviceStore()");
ok("blocos dos stores localizados", iServer >= 0 && iDevice > iServer);
const server = pers.slice(iServer, iDevice);
const device = pers.slice(iDevice);

ok("serverStore.carteiraLeitura delega a api.carteiraLeitura",
  /carteiraLeitura:\s*\(body\)\s*=>\s*api\.carteiraLeitura\(body\)/.test(server));
ok("deviceStore.carteiraLeitura delega a api.carteiraLeitura",
  /async carteiraLeitura\(body\)\s*\{[^}]*return api\.carteiraLeitura\(body\)/.test(device));
ok("api.js usa POST em /api/carteira/leitura",
  /carteiraLeitura:\s*\(body\)\s*=>\s*req\("POST",\s*"\/api\/carteira\/leitura"/.test(api));

if (fails) { console.log(`${fails} falha(s)`); process.exit(1); }
console.log("OK");
