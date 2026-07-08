// FASE 6 (fix 1) — Guardião: endereço do servidor com padrão de PRODUÇÃO.
//
// BUG que motivou este teste: sem VITE_API_BASE no build, o app nativo nascia
// SEM endereço de servidor — login/cotações/IA falhavam até o usuário digitar
// a URL, e o valor digitado vivia no doc ESCOPADO por usuário (sumia ao trocar
// login/logout, obrigando a recadastrar a cada reinício).
// Contratos trancados aqui:
//  1) api.js: em modo nativo, base vazia => PROD_BASE (produção embutida);
//     override manual vence; limpar volta à produção; web segue mesma-origem.
//  2) persistence.js: serverUrl é espelhado numa chave GLOBAL do aparelho
//     (b3-server-url-v1), lida no ensure() de QUALQUER escopo.
// Roda sem build: `node web/tests/test_api_base.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { setNativeMode, setApiBase, getApiBase, PROD_BASE } from "../src/api.js";

const here = dirname(fileURLToPath(import.meta.url));
const pers = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// ---- 1) contrato do api.js (comportamento real, em Node) -------------------
ok("PROD_BASE aponta para o Railway de produção", PROD_BASE === "https://b3agente-production.up.railway.app");

// web (não-nativo): vazio = mesma origem
setNativeMode(false);
setApiBase("");
ok("web: base vazia segue mesma origem", getApiBase() === "(mesma origem)");

// nativo: vazio => produção
setNativeMode(true);
setApiBase("");
ok("nativo: base vazia cai na PRODUÇÃO", getApiBase() === PROD_BASE);

// override manual vence
setApiBase("http://192.168.0.12:8787");
ok("nativo: override manual vence", getApiBase() === "http://192.168.0.12:8787");

// limpar o override volta à produção
setApiBase("");
ok("nativo: limpar override volta à produção", getApiBase() === PROD_BASE);

// setNativeMode no boot já aplica o padrão (sem esperar o ensure)
setNativeMode(false); setApiBase("");            // zera
setNativeMode(true);
ok("nativo: setNativeMode aplica produção de imediato", getApiBase() === PROD_BASE);
setNativeMode(false); setApiBase("");            // não vaza p/ outros testes

// ---- 2) espelho GLOBAL do aparelho no persistence.js -----------------------
ok("persistence: chave global b3-server-url-v1 existe", pers.includes('const SRV_KEY = "b3-server-url-v1"'));
ok("persistence: ensure() lê a chave global (qualquer escopo)", pers.includes("readSrvGlobal()") && /const g = readSrvGlobal\(\); if \(g !== null\) doc\.config\.serverUrl = g;/.test(pers));
ok("persistence: putConfig espelha serverUrl no global", pers.includes("writeSrvGlobal(patch.serverUrl)"));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
