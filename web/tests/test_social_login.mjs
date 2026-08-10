// FASE 4 (Bloco 2) — wiring do login social Apple/Google (plugin capgo).
// Padrão "grep de wiring" do projeto. Roda sem build:
//   node web/tests/test_social_login.mjs
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const R = (p) => readFileSync(join(here, "..", p), "utf8");
const social = R("src/social.js");
const app = R("src/App.jsx");
const mainJsx = R("src/main.jsx");
const pkg = JSON.parse(R("package.json"));

let fails = 0;
const ok = (n, c) => { console.log((c ? "ok " : "FALHOU ") + n); if (!c) fails++; };

// ponte: contrato e resiliência
ok("social.js registra window.__borisSocial", social.includes("window.__borisSocial ="));
ok("ponte só no nativo (isNativePlatform)", social.includes("isNativePlatform()"));
ok("plugin único capgo: import tardio", social.includes('import("@capgo/capacitor-social-login")'));
ok("apple: pede scopes email+name (1º consentimento)", social.includes('["email", "name"]'));
ok("authorizationCode extraído (revoke futuro)", social.includes("r.authorizationCode || r.serverAuthCode"));
ok("google: webClientId = client WEB (aud do idToken)", social.includes("webClientId: GOOGLE_WEB"));
ok("retorno defensivo (result|direto; idToken|identityToken)", social.includes("r.idToken || r.identityToken"));
ok("google: erro acionável quando não configurado", social.includes("VITE_GOOGLE_IOS_CLIENT_ID"));

// boot: main.jsx registra a ponte no nativo sem derrubar o app
ok("main.jsx importa social.js no caminho nativo", mainJsx.includes('import("./social.js")') && mainJsx.includes("registerSocialBridge"));

// App.jsx: aceita string OU objeto e propaga name/authorizationCode
ok("botões aceitam retorno string ou objeto da ponte", app.includes('typeof r === "string" ? { idToken: r }'));
ok("ctx.oauth propaga name e authorizationCode", app.includes("oauth: async ({ provider, idToken, name, authorizationCode })"));
ok("Apple vem ANTES do Google na UI (diretriz 4.8)", app.indexOf("Continuar com a Apple") < app.indexOf("Continuar com o Google") && app.indexOf("Continuar com a Apple") > 0);

// dependências nativas declaradas — e as abandonadas FORA
ok("package.json tem @capgo/capacitor-social-login", !!pkg.dependencies["@capgo/capacitor-social-login"]);
ok("plugins abandonados removidos (codetrix: peer Cap 6 → ERESOLVE no Cap 8)",
  !pkg.dependencies["@codetrix-studio/capacitor-google-auth"] && !pkg.dependencies["@capacitor-community/apple-sign-in"]);

console.log(fails ? `\n${fails} FALHA(S)` : "\nWIRING DO LOGIN SOCIAL OK");
process.exit(fails ? 1 : 0);
