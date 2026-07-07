// Notificacoes LOCAIS (disparadas pelo proprio app) — sem servidor de push.
// Nativo (iPhone): @capacitor/local-notifications. Web: Notification API.
// PUSH com app fechado (APNs + servidor) fica no backlog de publicacao.
//
// Boas praticas iOS aplicadas pela UI que chama este modulo:
//  - permissao pedida no MOMENTO CERTO (quando o usuario LIGA as notificacoes
//    na Config — o valor fica claro), nunca "de cara";
//  - conteudo curto e acionavel;
//  - preferencias respeitadas (ligar/desligar por tipo na Config).

import { isNative } from "./persistence.js";

let _plugin = null;
let _channelReady = false;

// Diagnóstico (ative com localStorage["b3-debug"]="1" ou window.B3_DEBUG=true).
function ndbg(...a) {
  try {
    if ((typeof window !== "undefined" && window.B3_DEBUG) || (typeof localStorage !== "undefined" && localStorage.getItem("b3-debug"))) {
      console.log("[b3:notify]", ...a);
    }
  } catch { /* ignore */ }
}

// Estado de diagnóstico para inspeção rápida no console: notify.diag().
export async function diag() {
  const out = { isNative, pluginLoaded: false, permission: "?", error: null };
  try {
    if (isNative) {
      const p = await plugin();
      out.pluginLoaded = !!p;
      out.hasSchedule = !!(p && p.schedule);
      out.hasRequest = !!(p && p.requestPermissions);
      // BLOCO 1: o que o SISTEMA (iOS) tem de fato agendado — prova real de que
      // o agendamento nativo foi aceito (independe do estado do WebView).
      const pend = await getPending();
      out.pendingCount = pend.length;
      out.pendingIds = pend.map((n) => n.id);
    } else {
      out.pluginLoaded = typeof Notification !== "undefined";
    }
    out.permission = await getPermission();
  } catch (e) {
    out.error = (e && e.message) || String(e);
  }
  ndbg("diag()", out);
  return out;
}

// BLOCO 1: lista os agendamentos PENDENTES registrados no sistema (nativo).
// No web devolve os timers vivos da aba. Nunca lança.
export async function getPending() {
  try {
    if (isNative) {
      const p = await plugin();
      if (!p || !p.getPending) return [];
      const r = await p.getPending();
      return ((r && r.notifications) || []).map((n) => ({ id: n.id, title: n.title || "", at: (n.schedule && n.schedule.at) || null }));
    }
    return Array.from(_webTimers.keys()).map((id) => ({ id, title: "", at: null }));
  } catch {
    return [];
  }
}

async function plugin() {
  if (!isNative) return null;
  if (_plugin) return _plugin;
  try {
    const mod = await import("@capacitor/local-notifications");
    _plugin = mod.LocalNotifications;
    ndbg("plugin carregado:", !!_plugin, "metodos:", _plugin ? Object.keys(_plugin).join(",") : "—");
  } catch (e) {
    ndbg("FALHA ao importar @capacitor/local-notifications:", (e && e.message) || e);
    _plugin = null;
  }
  return _plugin;
}

// Estado da permissao: "granted" | "denied" | "default" | "unsupported".
export async function getPermission() {
  if (isNative) {
    const p = await plugin();
    if (!p) return "unsupported";
    try {
      const r = await p.checkPermissions();
      return r.display === "granted" ? "granted" : r.display === "denied" ? "denied" : "default";
    } catch {
      return "unsupported";
    }
  }
  if (typeof Notification === "undefined") return "unsupported";
  return Notification.permission; // granted | denied | default
}

// Pede permissao. Chamar a partir de um gesto do usuario (ligar o toggle).
export async function requestPermission() {
  if (isNative) {
    const p = await plugin();
    if (!p) { ndbg("requestPermission: plugin indisponível (import falhou ou app não recompilado)"); return "unsupported"; }
    try {
      const r = await p.requestPermissions();
      ndbg("requestPermissions ->", r);
      return r.display === "granted" ? "granted" : "denied";
    } catch (e) {
      ndbg("requestPermissions erro:", (e && e.message) || e);
      return "unsupported";
    }
  }
  if (typeof Notification === "undefined") return "unsupported";
  try {
    return await Notification.requestPermission();
  } catch {
    return "denied";
  }
}

// BLOCO 1 — ids PERSISTIDOS entre aberturas do app. Com o contador só em
// memória (nascendo sempre em 1), reabrir o app e disparar QUALQUER notificação
// reusava ids de agendamentos pendentes da sessão anterior — e, no iOS, agendar
// com um id já pendente SUBSTITUI o agendamento antigo sem erro (a notificação
// "some" e parece falha de entrega em background). O contador agora vive no
// localStorage; sem storage (ex.: testes em Node), cai no contador em memória.
const _NID_KEY = "b3-notify-nid";
let _id = 1;
function _nextId() {
  let n = _id;
  try {
    if (typeof localStorage !== "undefined") {
      const raw = parseInt(localStorage.getItem(_NID_KEY) || "", 10);
      if (Number.isFinite(raw) && raw > 0) n = raw;
    }
  } catch { /* storage indisponível */ }
  const id = ((n - 1) % 2147483000) + 1; // 1..2147483000
  _id = id + 1;
  try { if (typeof localStorage !== "undefined") localStorage.setItem(_NID_KEY, String(_id)); } catch { /* ignore */ }
  return id;
}
// Apresentação em FOREGROUND (Objetivo 2): no iOS, com o app ABERTO, o banner do
// sistema é suprimido por padrão. Para que teste e eventos apareçam MESMO com o
// app aberto, o app registra um handler que mostra um aviso in-app (toast). A
// notificação do SISTEMA continua disparando (aparece na central/segundo plano).
// O banner nativo em foreground exige o delegate UNUserNotificationCenter
// (willPresent → .banner/.list/.sound) no projeto iOS — documentado no guia.
let _onForeground = null;
export function setForegroundHandler(fn) {
  _onForeground = typeof fn === "function" ? fn : null;
}
function _emitForeground(title, body) {
  try { if (_onForeground) _onForeground(title, body); } catch { /* nunca quebra */ }
}

// Registra o listener nativo de recebimento (debug/telemetria). Idempotente.
let _setupDone = false;
export async function setup() {
  if (_setupDone) return;
  _setupDone = true;
  if (!isNative) return;
  try {
    const p = await plugin();
    if (p && p.addListener) {
      p.addListener("localNotificationReceived", (n) => ndbg("recebida (foreground):", n && n.title));
    }
  } catch (e) { ndbg("setup() falhou:", (e && e.message) || e); }
}
// FASE 4: timers do fallback web (sem service worker, "agendar" vive enquanto a
// aba estiver aberta). No nativo, o agendamento/cancelamento é do plugin.
const _webTimers = new Map();

// Dispara uma notificacao local imediata. title curto; body acionavel.
export async function send(title, body) {
  try {
    if (isNative) {
      const p = await plugin();
      if (!p) return false;
      if (!_channelReady && p.createChannel) {
        try { await p.createChannel({ id: "carteira", name: "Movimentos da carteira", importance: 4 }); } catch { /* iOS ignora */ }
        _channelReady = true;
      }
      // BLOCO 1: entrega IMEDIATA sem campo `schedule`. O agendamento antigo em
      // `at: agora+250ms` podia já estar no PASSADO quando o iOS processava a
      // chamada (ponte JS→nativo + app ocupado) — e agendamento no passado é
      // descartado silenciosamente pelo sistema.
      await p.schedule({
        notifications: [{
          id: _nextId(),
          title,
          body,
          channelId: "carteira",
        }],
      });
      _emitForeground(title, body); // app aberto: garante visibilidade in-app
      return true;
    }
    if (typeof Notification !== "undefined" && Notification.permission === "granted") {
      // eslint-disable-next-line no-new
      new Notification(title, { body });
      return true;
    }
  } catch {
    /* nunca quebra o fluxo do app por causa de notificacao */
  }
  return false;
}

// Conveniencia: dispara apenas se o tipo estiver ligado nas preferencias.
// prefs = config.notif = { enabled, stop, alvo, agente, variacao }
export async function notifyIfEnabled(prefs, type, title, body) {
  if (!prefs || !prefs.enabled) return false;
  if (type && prefs[type] === false) return false;
  return send(title, body);
}

// FASE 4: agenda uma notificacao local para um HORARIO futuro. Retorna o id
// (use para cancelar) ou null. No iOS isso usa o plugin nativo; no web usa um
// setTimeout enquanto a aba viver (sem service worker, nao ha agendamento real).
export async function schedule(title, body, at, id) {
  const req = at instanceof Date ? at : new Date(at);
  // BLOCO 1: horário no passado (ou "agora") é DESCARTADO pelo iOS sem erro.
  // Clampa para pelo menos +1s no futuro — o agendamento sempre é aceito.
  const when = (!Number.isFinite(req.getTime()) || req.getTime() <= Date.now())
    ? new Date(Date.now() + 1000) : req;
  const nid = (id != null ? id : _nextId()) || 1;
  try {
    if (isNative) {
      const p = await plugin();
      if (!p) return null;
      if (!_channelReady && p.createChannel) {
        try { await p.createChannel({ id: "carteira", name: "Movimentos da carteira", importance: 4 }); } catch { /* iOS ignora */ }
        _channelReady = true;
      }
      // allowWhileIdle: entrega no horário mesmo em Doze/idle (Android; iOS ignora).
      await p.schedule({ notifications: [{ id: nid, title, body, channelId: "carteira", schedule: { at: when, allowWhileIdle: true } }] });
      // Foreground: se o app ainda estiver aberto na hora, mostra aviso in-app
      // (o SO já cobre o caso de segundo plano). Timer cancelável junto do nativo.
      const ms = Math.max(0, when.getTime() - Date.now());
      const h = setTimeout(() => { _webTimers.delete(nid); _emitForeground(title, body); }, ms);
      _webTimers.set(nid, h);
      return nid;
    }
    // Web/fallback: timer da aba (sem service worker, o agendamento vive
    // enquanto a aba viver). BLOCO 1: o timer é criado MESMO sem a API
    // Notification ou sem permissão — na hora, tenta o banner do navegador e,
    // se não der, avisa pelo toast in-app (e o contrato fica testável em Node).
    const ms = Math.max(0, when.getTime() - Date.now());
    const handle = setTimeout(() => {
      _webTimers.delete(nid);
      if (typeof Notification !== "undefined" && Notification.permission === "granted") {
        try { new Notification(title, { body }); return; } catch { /* cai no toast */ }
      }
      _emitForeground(title, body);
    }, ms);
    _webTimers.set(nid, handle);
    return nid;
  } catch {
    /* nunca quebra o fluxo do app por causa de notificacao */
  }
  return null;
}

// FASE 4: cancela UMA notificacao agendada (nativo) ou um timer web pendente.
export async function cancel(id) {
  if (id == null) return false;
  try {
    // limpa o timer in-app (criado tanto no web quanto no nativo p/ foreground)
    const h = _webTimers.get(id);
    if (h != null) { clearTimeout(h); _webTimers.delete(id); }
    if (isNative) {
      const p = await plugin();
      if (!p || !p.cancel) return false;
      await p.cancel({ notifications: [{ id }] });
      return true;
    }
    return h != null;
  } catch {
    /* ignore */
  }
  return false;
}

// FASE 4: cancela TODAS as notificacoes locais pendentes.
export async function cancelAll() {
  try {
    if (isNative) {
      const p = await plugin();
      if (!p) return false;
      if (p.getPending && p.cancel) {
        const pend = await p.getPending();
        const list = (pend && pend.notifications) || [];
        if (list.length) await p.cancel({ notifications: list.map((n) => ({ id: n.id })) });
      }
      return true;
    }
    for (const h of _webTimers.values()) clearTimeout(h);
    _webTimers.clear();
    return true;
  } catch {
    /* ignore */
  }
  return false;
}


// FASE 3.3b — push remoto (APNs) para as ações do agente server-side.
// O plugin @capacitor/push-notifications só existe após npm install + cap sync;
// fora do build (ou sem a capability no Xcode) isto degrada com motivo claro.
export async function registerPush(sendTokenToServer) {
  if (!isNative) return { ok: false, reason: "push remoto é do app iOS (web usa o agente em foreground)" };
  let P = null;
  try {
    const mod = await import("@capacitor/push-notifications");
    P = mod.PushNotifications;
  } catch (e) {
    return { ok: false, reason: "plugin de push ausente no build — rode scripts/instalar.sh --iphone (npm install + cap sync) e ative a capability Push no Xcode" };
  }
  try {
    const perm = await P.requestPermissions();
    if (perm.receive !== "granted") return { ok: false, reason: "permissão de notificação negada em Ajustes" };
    return await new Promise((resolve) => {
      P.addListener("registration", async (tk) => {
        try {
          const r = await sendTokenToServer(tk.value);
          resolve({ ok: true, apnsConfigured: !!(r && r.apnsConfigured) });
        } catch (e2) {
          resolve({ ok: false, reason: (e2 && e2.message) || String(e2) });
        }
      });
      P.addListener("registrationError", (err) => resolve({ ok: false, reason: (err && err.error) || "falha no registro APNs" }));
      P.register();
      setTimeout(() => resolve({ ok: false, reason: "tempo esgotado no registro do push" }), 15000);
    });
  } catch (e) {
    return { ok: false, reason: (e && e.message) || String(e) };
  }
}
