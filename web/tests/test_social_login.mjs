// FASE 4 (Bloco 2) — wiring do login social Apple/Google.
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
ok("social.js registra window.__bolsiaSocial", /window\.__bolsiaSocial\s*=/.test(social));
ok("ponte só no nativo (isNativePlatform)", /isNativePlatform\(\)/.test(social));
ok("apple: import tardio do plugin da comunidade", /import\("@capacitor-community\/apple-sign-in"\)/.test(social));
ok("apple: pede scopes email name (1º consentimento)", /scopes:\s*"email name"/.test(social));
ok("apple: repassa authorizationCode (revoke futuro)", /authorizationCode:\s*res\.authorizationCode/.test(social));
ok("google: import tardio do plugin", /import\("@codetrix-studio\/capacitor-google-auth"\)/.test(social));
ok("google: serverClientId = client WEB (aud do idToken)", /serverClientId:\s*GOOGLE_WEB/.test(social));
ok("google: erro acionável quando não configurado", /VITE_GOOGLE_IOS_CLIENT_ID/.test(social));

// boot: main.jsx registra a ponte no nativo sem derrubar o app
ok("main.jsx importa social.js no caminho nativo", /import\("\.\/social\.js"\)/.test(mainJsx) && /registerSocialBridge/.test(mainJsx));

// App.jsx: aceita string OU objeto e propaga name/authorizationCode
ok("botões aceitam retorno string ou objeto da ponte", /typeof r === "string" \? \{ idToken: r \}/.test(app));
ok("ctx.oauth propaga name e authorizationCode", /oauth:\s*async \(\{ provider, idToken, name, authorizationCode \}\)/.test(app));
ok("Apple vem ANTES do Google na UI (diretriz 4.8)", app.indexOf("Continuar com a Apple") < app.indexOf("Continuar com o Google") && app.indexOf("Continuar com a Apple") > 0);

// dependências nativas declaradas
ok("package.json tem @capacitor-community/apple-sign-in", !!pkg.dependencies["@capacitor-community/apple-sign-in"]);
ok("package.json tem @codetrix-studio/capacitor-google-auth", !!pkg.dependencies["@codetrix-studio/capacitor-google-auth"]);

console.log(fails ? `\n${fails} FALHA(S)` : "\nWIRING DO LOGIN SOCIAL OK");
process.exit(fails ? 1 : 0);
