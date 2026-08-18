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

// boot: main.jsx registra a ponte SEMPRE (nativo e web), sem derrubar o app
// ATUALIZADO 2026-08-17: import vivia dentro do `if` nativo — Google (GIS) e
// Apple sempre existiram no código, mas o web nunca chamava
// `registerSocialBridge()`, então a ponte nunca registrava e o botão do
// Google sempre caía no "chega em breve", mesmo com VITE_GOOGLE_WEB_CLIENT_ID
// configurado. Import incondicional é a correção; import ainda dentro do
// bloco nativo seria a REGRESSÃO que este teste passa a vigiar.
ok("main.jsx importa social.js incondicionalmente (nativo E web)",
  mainJsx.includes('import("./social.js")') && mainJsx.includes("registerSocialBridge"));
ok("import de social.js está FORA do bloco `if (Capacitor.isNativePlatform())`",
  mainJsx.indexOf('import("./social.js")') < mainJsx.indexOf("if (Capacitor.isNativePlatform())"));

// ---------------------------------------------------------------------------
// Google no WEB/PWA via Google Identity Services (2026-08-17) — Apple web
// fica de fora de propósito (exige Services ID + Return URL + verificação de
// domínio no portal Apple; trabalho separado, não incluído aqui).
// ---------------------------------------------------------------------------
ok("web registra SÓ google (Apple web não foi implementado nesta entrega)",
  /if \(!Capacitor\.isNativePlatform\(\)\) \{[\s\S]{0,400}?window\.__borisSocial = \{\s*google:/.test(social)
  && !/if \(!Capacitor\.isNativePlatform\(\)\) \{[\s\S]{0,400}?apple:/.test(social));
ok("web sem VITE_GOOGLE_WEB_CLIENT_ID não registra ponte (sem botão que falha)",
  social.includes("if (!GOOGLE_WEB) {") && social.includes("ponte não registrada"));
ok("carrega o script oficial do Google Identity Services",
  social.includes("https://accounts.google.com/gsi/client"));
ok("usa FedCM (fim do 3rd-party-cookie prompt legado)",
  social.includes("use_fedcm_for_prompt: true"));
ok("prompt() cancelado/bloqueado rejeita em vez de travar a Promise",
  social.includes("isNotDisplayed") && social.includes("isSkippedMoment"));

// ATUALIZADO 2026-08-17 (achado ao vivo, produção): reproduzindo num
// navegador sem sessão Google, a notificação do prompt() NUNCA chegava — GIS
// logava "Not signed in with the identity provider" e nem o callback nem a
// notificação disparavam. Sem watchdog, a Promise ficava presa pra sempre:
// botão girando, sem erro. E o motivo do bloqueio (getNotDisplayedReason /
// getSkippedReason) era descartado — só a mensagem genérica "cookies de
// terceiros?" chegava ao usuário, sem dizer qual dos ~8 motivos reais era.
ok("watchdog: nunca fica esperando a notificação para sempre",
  social.includes("const watchdog = setTimeout(") && social.includes("10000"));
ok("watchdog é limpo quando a resposta chega primeiro (não vaza timer)",
  social.includes("clearTimeout(watchdog)"));
ok("captura o motivo GRANULAR do bloqueio (não só true/false)",
  social.includes("getNotDisplayedReason") && social.includes("getSkippedReason"));
ok("mapa de mensagem por motivo (não é mais um texto genérico só)",
  social.includes("MOTIVO_LEGIVEL") && social.includes("opt_out_or_no_session") && social.includes("browser_not_supported"));
ok("motivo desconhecido ainda aparece na mensagem (nunca esconde o dado)",
  social.includes('"O Google bloqueou o login (" + motivo + ")'));
ok("nome do idToken é DECODIFICADO, nunca a fonte de confiança (servidor valida)",
  social.includes("nomeDoIdToken") && social.includes("o SERVIDOR é quem valida"));
ok("App.jsx: gate do botão Google é diferente por plataforma (iOS precisa dos 2 client ids; web só do web)",
  app.includes("isNative\n    ? Boolean(import.meta.env?.VITE_GOOGLE_IOS_CLIENT_ID")
  && app.includes(": Boolean(import.meta.env?.VITE_GOOGLE_WEB_CLIENT_ID)"));

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
