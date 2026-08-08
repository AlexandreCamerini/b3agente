// qa/audit-2026-08-08 — Alex relatou ter perdido o histórico da conta logada
// via Apple ("na última atualização"). A investigação achou dois problemas
// distintos na mesma área:
//
// 1. O dado NUNCA foi perdido no servidor (a conta Apple casa por `sub`,
//    estável mesmo com Hide My Email, e o seed do 1º login só roda se a
//    conta ainda estiver vazia — `only_if_empty`). O sintoma era client-side:
//    `getState()` no aparelho só lia local, nunca puxava o servidor de volta
//    — já corrigido antes nesta mesma sessão (ver
//    test_carteira_nativa_sincroniza.mjs) para cash/positions/history.
//
// 2. ESTE guardião prova um bug real e separado, achado na mesma auditoria:
//    `auth.oauth()` em persistence.js recebia `name` e `authorizationCode`
//    de App.jsx mas os descartava ao montar o corpo da requisição — existia
//    desde a FASE 4 (SIWA), não é regressão recente. Efeito: a Apple só manda
//    o nome no 1º consentimento (LOGIN-SOCIAL.md D1) e o `authorizationCode`
//    é o que habilita o revoke na exclusão de conta (D7) — sem os dois
//    chegarem ao servidor, o Perfil nunca mostra o nome e o revoke nunca é
//    registrado, mesmo com tudo configurado certo nos portais Apple/Railway.
//
// Roda sem device nem build: `node web/tests/test_oauth_repassa_name_e_code.mjs`.

globalThis.CapacitorCustomPlatform = { name: "ios" };
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => { mem.set(k, String(v)); },
  removeItem: (k) => { mem.delete(k); },
};

const chamadas = [];
globalThis.fetch = async (url, opts) => {
  const method = (opts && opts.method) || "GET";
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  chamadas.push({ url: String(url), method, body });
  if (/\/api\/auth\/oauth$/.test(url)) {
    return { ok: true, status: 200, text: async () => JSON.stringify({ token: "tok-1", user: { id: "u1" } }) };
  }
  return { ok: true, status: 200, text: async () => JSON.stringify({}) };
};

const { auth } = await import("../src/persistence.js");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

{
  chamadas.length = 0;
  await auth.oauth({ provider: "apple", idToken: "id-tok", name: "Alexandre", authorizationCode: "auth-code-123" });
  const chamada = chamadas.find((c) => /\/api\/auth\/oauth$/.test(c.url));
  ok("auth.oauth chama POST /api/auth/oauth", !!chamada);
  ok("o corpo leva o name (hint do 1º consentimento da Apple)", chamada && chamada.body.name === "Alexandre");
  ok("o corpo leva o authorizationCode (habilita revoke na exclusão de conta)", chamada && chamada.body.authorizationCode === "auth-code-123");
}

{
  // Login recorrente: Apple não reenvia nome/authorizationCode — não pode
  // virar `undefined`/`null` explícito no corpo (o servidor só distingue
  // "ausente" de "string vazia" por `in`/truthy, então nada de mandar a
  // chave com lixo).
  chamadas.length = 0;
  await auth.oauth({ provider: "apple", idToken: "id-tok-2" });
  const chamada = chamadas.find((c) => /\/api\/auth\/oauth$/.test(c.url));
  ok("sem name/authorizationCode (login recorrente), o corpo não leva as chaves",
     chamada && !("name" in chamada.body) && !("authorizationCode" in chamada.body));
}

console.log();
console.log(fails === 0 ? "TODOS OS TESTES DE OAUTH PASSARAM" : fails + " TESTE(S) FALHARAM");
process.exit(fails === 0 ? 0 : 1);
