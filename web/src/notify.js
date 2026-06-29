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

let _id = 1;
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
      await p.schedule({
        notifications: [{
          id: _id++ % 2147483000,
          title,
          body,
          channelId: "carteira",
          schedule: { at: new Date(Date.now() + 250) },
        }],
      });
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
  const when = at instanceof Date ? at : new Date(at);
  const nid = (id != null ? id : (_id++ % 2147483000)) || 1;
  try {
    if (isNative) {
      const p = await plugin();
      if (!p) return null;
      if (!_channelReady && p.createChannel) {
        try { await p.createChannel({ id: "carteira", name: "Movimentos da carteira", importance: 4 }); } catch { /* iOS ignora */ }
        _channelReady = true;
      }
      await p.schedule({ notifications: [{ id: nid, title, body, channelId: "carteira", schedule: { at: when } }] });
      return nid;
    }
    if (typeof Notification !== "undefined") {
      const ms = Math.max(0, when.getTime() - Date.now());
      const handle = setTimeout(() => {
        _webTimers.delete(nid);
        if (Notification.permission === "granted") { try { new Notification(title, { body }); } catch { /* ignore */ } }
      }, ms);
      _webTimers.set(nid, handle);
      return nid;
    }
  } catch {
    /* nunca quebra o fluxo do app por causa de notificacao */
  }
  return null;
}

// FASE 4: cancela UMA notificacao agendada (nativo) ou um timer web pendente.
export async function cancel(id) {
  if (id == null) return false;
  try {
    if (isNative) {
      const p = await plugin();
      if (!p || !p.cancel) return false;
      await p.cancel({ notifications: [{ id }] });
      return true;
    }
    const h = _webTimers.get(id);
    if (h != null) { clearTimeout(h); _webTimers.delete(id); return true; }
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
