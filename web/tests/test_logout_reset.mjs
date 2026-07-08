// FASE 8 (A3) — Guardião: sair da conta é um RESET completo de escopo.
//
// BUG: o logout limpava token/escopo, mas (a) analysis/expanded/quotes/wlScan/
// destaque continuavam NA MEMÓRIA com dados da conta (e o merge {...seed,
// ...cur} do loadState preservava o antigo); (b) nada levava ao portão de
// entrada — o app "parecia" logado. O mesmo vazamento existia no LOGIN
// (dados do anônimo vazavam para a conta).
// Contratos:
//  1) _resetScopeState existe e limpa os 5 estados derivados + notifRef;
//  2) logout/deleteAccount: reset + loadState + refreshQuotes + welcome reaberto;
//  3) login/register/oauth também resetam (troca de escopo é simétrica);
//  4) persistence.auth.logout segue limpando token+cache+outbox+namespace.
// Roda sem build: `node web/tests/test_logout_reset.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const pers = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function bodyOf(src, anchor) {
  const at = src.indexOf(anchor);
  if (at < 0) return null;
  const open = src.indexOf("{", at + anchor.length);
  let depth = 0;
  for (let i = open; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) return src.slice(open, i + 1); }
  }
  return null;
}

// ---- 1) reset único e completo ---------------------------------------------
const reset = bodyOf(app, "const _resetScopeState = () =>");
ok("_resetScopeState existe", !!reset);
for (const s of ["setAnalysis({})", "setExpanded({})", "setQuotes({})", "setWlScan(null)", 'setDestaque({ stage: "idle" })', "notifRef.current = {}"]) {
  ok("reset limpa " + s.replace(/\(.*/, ""), !!reset && reset.includes(s));
}

// ---- 2) logout e exclusão: reset + recarga + welcome ------------------------
for (const fn of ["logout: async () =>", "deleteAccount: async () =>"]) {
  const b = bodyOf(app, fn);
  const nome = fn.split(":")[0];
  ok(nome + " reseta o escopo", !!b && b.includes("_resetScopeState()"));
  ok(nome + " recarrega estado + cotações", !!b && b.includes("await loadState()") && b.includes("refreshQuotes()"));
  ok(nome + " reabre o portão de entrada", !!b && b.includes("setWelcomeOpen(true)"));
  ok(nome + " zera o usuário", !!b && b.includes("setAuthUser(null)"));
}

// ---- 3) entrada também troca de escopo limpa --------------------------------
for (const fn of ["login: async ({ email, password })", "register: async ({ email, password, name })", "oauth: async ({ provider, idToken"]) {
  const b = bodyOf(app, fn);
  ok(fn.split(":")[0] + " reseta o escopo ao entrar", !!b && b.includes("_resetScopeState()"));
}

// ---- 4) persistence: limpeza de plataforma segue completa -------------------
const plogout = bodyOf(pers, "async logout()");
ok("persistence.logout limpa token+cache+outbox", !!plogout && plogout.includes("sync.clearToken()") && plogout.includes("sync.cacheClear()") && plogout.includes("sync.outboxClear()"));
ok("persistence.logout volta o namespace do aparelho ao anônimo", !!plogout && plogout.includes("_deviceScope(null)"));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
