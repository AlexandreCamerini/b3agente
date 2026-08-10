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
  // REVERSÃO DELIBERADA (09/08/2026): era `setWelcomeOpen(true)`, o modal de
  // ONBOARDING (orçamento + perfil de risco). Sair da conta caía na tela de
  // configuração inicial em vez da de login. Com o acesso sem conta removido,
  // o portão de LOGIN é o único destino possível — ver `_voltarAoLogin`.
  ok(nome + " volta para o portão de LOGIN", !!b && b.includes("_voltarAoLogin()"));
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

// ---------------------------------------------------------------------------
// Ajuste do Alex (09/08/2026): sair da conta pela Config tem que voltar para a
// TELA DE LOGIN. Ia para `setWelcomeOpen(true)` — o modal de ONBOARDING
// (orçamento + perfil de risco). Quem acabou de sair não está configurando
// nada, e desde a remoção do acesso sem conta o login é a única porta do app.
// ---------------------------------------------------------------------------
{
  const src2 = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
  const ok2 = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

  ok2("existe um caminho único de volta ao login", /const _voltarAoLogin = \(\) => \{/.test(src2));
  ok2("_voltarAoLogin abre o portão de login", /_voltarAoLogin[\s\S]{0,400}?setWelcomeAuthOpen\(true\)/.test(src2));
  ok2("_voltarAoLogin fecha o onboarding", /_voltarAoLogin[\s\S]{0,400}?setWelcomeOpen\(false\)/.test(src2));

  const logout = /logout: async \(\) => \{[\s\S]*?\n    \},/.exec(src2);
  ok2("logout localizado", !!logout);
  ok2("logout NÃO cai mais no onboarding", !!logout && !/setWelcomeOpen\(true\)/.test(logout[0]));
  ok2("logout volta ao login", !!logout && /_voltarAoLogin\(\)/.test(logout[0]));

  const del = /deleteAccount: async \(\) => \{[\s\S]*?\n    \},/.exec(src2);
  ok2("excluir conta também volta ao login",
    !!del && /_voltarAoLogin\(\)/.test(del[0]) && !/setWelcomeOpen\(true\)/.test(del[0]));
}
