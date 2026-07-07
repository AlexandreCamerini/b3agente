// FASE 4 (Bloco 2) — Ponte NATIVA de login social (Apple + Google).
//
// Contrato (já esperado pelos botões do App.jsx): window.__bolsiaSocial =
//   { apple: () => Promise<res>, google: () => Promise<res> }
// onde res = { idToken, name?, authorizationCode? }.
//
// Plugin: @capgo/capacitor-social-login — UM plugin mantido para os dois
// provedores. (Substituiu @codetrix-studio/capacitor-google-auth, abandonado
// no peer do Capacitor 6 — ERESOLVE no Cap 8 — e o apple-sign-in da
// comunidade, para reduzir a superfície a uma dependência só.)
//
// Padrão do projeto (igual ao notify.js): import TARDIO e guardado — no
// navegador/PWA ou sem `cap sync` a ponte não registra e os botões mantêm o
// aviso amigável. Nenhum erro aqui derruba a tela de login.
//
// Configuração (build-time, sem segredo — client_id é público):
//   VITE_GOOGLE_IOS_CLIENT_ID  — OAuth client "iOS" (…apps.googleusercontent.com)
//   VITE_GOOGLE_WEB_CLIENT_ID  — OAuth client "Web"; vira o `aud` do idToken
//                                (o servidor valida contra GOOGLE_CLIENT_ID)
// Apple não precisa de config no cliente em iOS nativo: o `aud` do idToken é
// o próprio bundle id (o servidor valida contra APPLE_CLIENT_ID).
import { Capacitor } from "@capacitor/core";

const sdbg = (...a) => { try { console.log("[social]", ...a); } catch { /* noop */ } };

const GOOGLE_IOS = (import.meta.env && import.meta.env.VITE_GOOGLE_IOS_CLIENT_ID) || "";
const GOOGLE_WEB = (import.meta.env && import.meta.env.VITE_GOOGLE_WEB_CLIENT_ID) || "";

let pluginP = null;
async function plugin() {
  if (!pluginP) {
    pluginP = import("@capgo/capacitor-social-login").then(async (mod) => {
      const { SocialLogin } = mod;
      await SocialLogin.initialize({
        apple: {}, // iOS nativo usa ASAuthorization; nada a configurar aqui
        ...(GOOGLE_IOS && GOOGLE_WEB
          ? { google: { iOSClientId: GOOGLE_IOS, webClientId: GOOGLE_WEB, mode: "online" } }
          : {}),
      });
      return SocialLogin;
    }).catch((e) => { pluginP = null; throw e; });
  }
  return pluginP;
}

// Leitura DEFENSIVA do retorno: cobre variações de nome entre versões do
// plugin ({ result } | direto; idToken|identityToken; profile aninhado).
function extract(raw) {
  const r = (raw && (raw.result || raw)) || {};
  const prof = r.profile || r.user || {};
  const idToken = r.idToken || r.identityToken || (r.authentication && r.authentication.idToken) || null;
  const name = [prof.givenName, prof.familyName].filter(Boolean).join(" ").trim()
    || prof.name || prof.displayName || null;
  const authorizationCode = r.authorizationCode || r.serverAuthCode || null;
  return { idToken, name, authorizationCode };
}

async function signIn(provider) {
  if (provider === "google" && (!GOOGLE_IOS || !GOOGLE_WEB)) {
    throw new Error("Login Google não configurado neste build (VITE_GOOGLE_IOS_CLIENT_ID / VITE_GOOGLE_WEB_CLIENT_ID).");
  }
  const SocialLogin = await plugin();
  const raw = await SocialLogin.login({
    provider,
    options: provider === "apple" ? { scopes: ["email", "name"] } : { scopes: ["email", "profile"] },
  });
  const res = extract(raw);
  if (!res.idToken) {
    sdbg(provider, "retorno sem idToken — formato:", raw && Object.keys(raw.result || raw || {}));
    throw new Error((provider === "apple" ? "A Apple" : "O Google") + " não devolveu o token de identidade.");
  }
  return res;
}

export function registerSocialBridge() {
  if (typeof window === "undefined") return false;
  if (!Capacitor.isNativePlatform()) { sdbg("web/PWA: ponte nativa não registrada (e-mail segue como caminho)."); return false; }
  window.__bolsiaSocial = {
    apple: () => signIn("apple").catch((e) => { sdbg("apple FALHOU:", (e && e.message) || e); throw e; }),
    google: () => signIn("google").catch((e) => { sdbg("google FALHOU:", (e && e.message) || e); throw e; }),
  };
  sdbg("ponte registrada (apple, google) via capgo/social-login.");
  return true;
}
