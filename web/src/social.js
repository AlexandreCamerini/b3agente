// FASE 4 (Bloco 2) — Ponte NATIVA de login social (Apple + Google).
//
// Contrato (já esperado pelos botões do App.jsx): window.__borisSocial =
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

// ---------------------------------------------------------------------------
// Google no WEB/PWA (2026-08-17) — Google Identity Services (GIS), não o
// plugin Capacitor acima (esse é nativo-only). Backend, rota e contrato de
// `window.__borisSocial` já existiam prontos para isto desde a FASE 4; só
// faltava QUEM registrasse a ponte no navegador.
//
// Apple fica de fora aqui de propósito — login web da Apple exige Services ID
// + Return URL + verificação de domínio (peça de portal, não de código); é
// trabalho separado, avaliado e não incluído nesta entrega.
// ---------------------------------------------------------------------------
const GIS_SRC = "https://accounts.google.com/gsi/client";
let gisLoadP = null;

function loadGis() {
  if (typeof window !== "undefined" && window.google && window.google.accounts && window.google.accounts.id) {
    return Promise.resolve(window.google);
  }
  if (!gisLoadP) {
    gisLoadP = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = GIS_SRC;
      s.async = true;
      s.defer = true;
      s.onload = () => (window.google ? resolve(window.google) : reject(new Error("Google Identity Services carregou sem expor `google.accounts`.")));
      s.onerror = () => reject(new Error("Não consegui carregar o script de login do Google."));
      document.head.appendChild(s);
    }).catch((e) => { gisLoadP = null; throw e; });
  }
  return gisLoadP;
}

// O idToken é um JWT; o SERVIDOR é quem valida assinatura/aud/exp (auth.py).
// Decodificar o payload aqui é só para preencher `name` na primeira conta —
// mesmo papel que o `profile` do plugin nativo já cumpre — nunca é a fonte de
// confiança.
function nomeDoIdToken(idToken) {
  try {
    const payload = idToken.split(".")[1];
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    const claims = JSON.parse(decodeURIComponent(escape(json)));
    return claims.name || [claims.given_name, claims.family_name].filter(Boolean).join(" ").trim() || null;
  } catch {
    return null; // best-effort — sem nome, a conta nasce sem, como já acontecia
  }
}

// Mensagem por BUCKET de motivo (getNotDisplayedReason()/getSkippedReason()),
// não um texto genérico só adivinhando "cookies de terceiros". Valores da doc
// da GIS; qualquer coisa fora da lista cai no default.
const MOTIVO_LEGIVEL = {
  browser_not_supported: "Este navegador não suporta o login rápido do Google — tente o Chrome, ou use o e-mail abaixo.",
  opt_out_or_no_session: "Você não está logado numa conta Google neste navegador — entre no Google primeiro, ou use o e-mail abaixo.",
  secure_http_required: "Conexão insegura — recarregue a página em https e tente de novo.",
  suppressed_by_user: "Você já dispensou o login rápido do Google antes — use o e-mail abaixo, ou limpe os dados do site para tentar de novo.",
  unregistered_origin: "Este endereço não está autorizado no Google Cloud Console (config do app, não sua).",
  missing_client_id: "Login Google mal configurado neste build (client id ausente).",
  invalid_client: "Login Google mal configurado neste build (client id inválido).",
  user_cancel: "Login cancelado.",
  tap_outside: "Login cancelado.",
};

async function signInGoogleWeb() {
  if (!GOOGLE_WEB) {
    throw new Error("Login Google não configurado neste build (VITE_GOOGLE_WEB_CLIENT_ID).");
  }
  const google = await loadGis();
  return new Promise((resolve, reject) => {
    let resolvido = false;
    const encerra = (fn) => { if (resolvido) return; resolvido = true; clearTimeout(watchdog); fn(); };

    // ACHADO AO VIVO (2026-08-17, produção): quando a notificação do prompt()
    // não chega — reproduzido num navegador sem sessão Google nenhuma, GIS
    // logou "Not signed in with the identity provider" e NUNCA chamou o
    // callback de notificação — a Promise ficava presa pra sempre: botão
    // girando, sem erro, sem explicação. O watchdog é a rede de segurança.
    const watchdog = setTimeout(() => {
      encerra(() => reject(new Error("O login do Google não respondeu — tente de novo ou use o e-mail abaixo.")));
    }, 10000);

    google.accounts.id.initialize({
      client_id: GOOGLE_WEB,
      callback: (resp) => {
        encerra(() => {
          if (resp && resp.credential) resolve({ idToken: resp.credential, name: nomeDoIdToken(resp.credential) });
          else reject(new Error("O Google não devolveu o token de identidade."));
        });
      },
      use_fedcm_for_prompt: true,
    });
    // prompt() em resposta a um clique é o caminho recomendado pelo Google
    // para disparar o One Tap a partir de um botão PRÓPRIO (o nosso, estilizado
    // igual ao da Apple) em vez do botão que a GIS renderizaria sozinha.
    //
    // Verificado ao vivo: funciona hoje, MAS o próprio GSI_LOGGER do Google
    // avisa em runtime que isNotDisplayed()/isSkippedMoment() "may stop
    // functioning when FedCM becomes mandatory" — a API de status pós-FedCM
    // ainda não está documentada o bastante pra migrar com confiança.
    google.accounts.id.prompt((notification) => {
      if (resolvido) return; // watchdog ou callback já encerrou — não sobrescreve
      const naoMostrou = notification.isNotDisplayed?.();
      const pulou = notification.isSkippedMoment?.();
      if (!naoMostrou && !pulou) return; // segue esperando — o callback acima ainda pode vir
      const motivo = (naoMostrou ? notification.getNotDisplayedReason?.() : notification.getSkippedReason?.()) || "unknown_reason";
      sdbg("google (web) prompt bloqueado — motivo GIS:", motivo);
      encerra(() => reject(new Error(MOTIVO_LEGIVEL[motivo] || ("O Google bloqueou o login (" + motivo + ") — use o e-mail abaixo."))));
    });
  });
}

export function registerSocialBridge() {
  if (typeof window === "undefined") return false;
  if (!Capacitor.isNativePlatform()) {
    if (!GOOGLE_WEB) { sdbg("web/PWA: VITE_GOOGLE_WEB_CLIENT_ID ausente — ponte não registrada."); return false; }
    window.__borisSocial = {
      google: () => signInGoogleWeb().catch((e) => { sdbg("google (web) FALHOU:", (e && e.message) || e); throw e; }),
    };
    sdbg("ponte registrada (google) via Google Identity Services — web/PWA.");
    return true;
  }
  window.__borisSocial = {
    apple: () => signIn("apple").catch((e) => { sdbg("apple FALHOU:", (e && e.message) || e); throw e; }),
    google: () => signIn("google").catch((e) => { sdbg("google FALHOU:", (e && e.message) || e); throw e; }),
  };
  sdbg("ponte registrada (apple, google) via capgo/social-login.");
  return true;
}
