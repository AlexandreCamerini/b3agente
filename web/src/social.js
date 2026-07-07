// FASE 4 (Bloco 2) — Ponte NATIVA de login social (Apple + Google).
//
// Contrato (já esperado pelos botões do App.jsx): window.__bolsiaSocial =
//   { apple: () => Promise<res>, google: () => Promise<res> }
// onde res = { idToken, name?, authorizationCode? }.
//
// Padrão do projeto (igual ao notify.js): plugins Capacitor importados TARDE
// e guardados — no navegador/PWA ou sem `cap sync` a ponte simplesmente não
// registra e os botões mantêm o aviso amigável ("chega em breve"). Nenhum
// erro derruba a tela de login.
//
// Configuração (build-time, sem segredo — client_id é público):
//   VITE_GOOGLE_IOS_CLIENT_ID  — OAuth client "iOS" (…apps.googleusercontent.com)
//   VITE_GOOGLE_WEB_CLIENT_ID  — OAuth client "Web"; vira o `aud` do idToken
//                                (o servidor valida contra GOOGLE_CLIENT_ID)
// Apple não precisa de config no cliente: o `aud` do idToken é o próprio
// bundle id (o servidor valida contra APPLE_CLIENT_ID).
import { Capacitor } from "@capacitor/core";

const sdbg = (...a) => { try { console.log("[social]", ...a); } catch { /* noop */ } };

const GOOGLE_IOS = (import.meta.env && import.meta.env.VITE_GOOGLE_IOS_CLIENT_ID) || "";
const GOOGLE_WEB = (import.meta.env && import.meta.env.VITE_GOOGLE_WEB_CLIENT_ID) || "";

async function appleSignIn() {
  const mod = await import("@capacitor-community/apple-sign-in");
  const { SignInWithApple } = mod;
  const r = await SignInWithApple.authorize({
    // Em iOS nativo o fluxo usa ASAuthorization (clientId/redirectURI são do
    // fallback web e não participam); scopes pedem nome+e-mail — a Apple só
    // os devolve no PRIMEIRO consentimento, por isso repassamos como hint.
    scopes: "email name",
  });
  const res = (r && r.response) || {};
  if (!res.identityToken) throw new Error("A Apple não devolveu o token de identidade.");
  const name = [res.givenName, res.familyName].filter(Boolean).join(" ").trim() || null;
  return { idToken: res.identityToken, name, authorizationCode: res.authorizationCode || null };
}

let googleReady = false;
async function googleSignIn() {
  if (!GOOGLE_IOS || !GOOGLE_WEB) {
    throw new Error("Login Google não configurado neste build (VITE_GOOGLE_IOS_CLIENT_ID / VITE_GOOGLE_WEB_CLIENT_ID).");
  }
  const mod = await import("@codetrix-studio/capacitor-google-auth");
  const { GoogleAuth } = mod;
  if (!googleReady) {
    await GoogleAuth.initialize({
      clientId: GOOGLE_IOS,
      serverClientId: GOOGLE_WEB, // faz o idToken sair com aud = client WEB
      scopes: ["profile", "email"],
      grantOfflineAccess: false,
    });
    googleReady = true;
  }
  const u = await GoogleAuth.signIn();
  const idToken = u && u.authentication && u.authentication.idToken;
  if (!idToken) throw new Error("O Google não devolveu o token de identidade.");
  return { idToken, name: (u && (u.name || u.givenName)) || null, authorizationCode: null };
}

export function registerSocialBridge() {
  if (typeof window === "undefined") return false;
  if (!Capacitor.isNativePlatform()) { sdbg("web/PWA: ponte nativa não registrada (e-mail segue como caminho)."); return false; }
  window.__bolsiaSocial = {
    apple: () => appleSignIn().catch((e) => { sdbg("apple FALHOU:", (e && e.message) || e); throw e; }),
    google: () => googleSignIn().catch((e) => { sdbg("google FALHOU:", (e && e.message) || e); throw e; }),
  };
  sdbg("ponte registrada (apple, google).");
  return true;
}
