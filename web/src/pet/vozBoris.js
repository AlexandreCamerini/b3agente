/**
 * vozBoris.js — a voz do Boris, roteada pela plataforma.
 *
 * `web/src/pet/Boris.jsx` já documenta a razão desta separação: o WKWebView
 * do iOS não confia no `speechSynthesis`. Web/PWA continua com a Web Speech
 * API (já testada, já funciona ali); o app nativo Capacitor usa o plugin de
 * TTS nativo (`@capacitor-community/text-to-speech`), que fala de verdade no
 * aparelho. Ambos os lados expõem a MESMA assinatura de `falarTexto`/`calarVoz`
 * que o app já usa — nenhum call site muda.
 *
 * F10-20260809 (tela de configuração do Boris): dois campos de config novos
 * entram por um SETTER externo (`setVozConfig`), não por prop-drilling —
 * mesmo padrão de `setApiBase`/`setAuthToken` em api.js/sync.js. É o jeito
 * de alcançar este módulo sem mudar a assinatura de `falarTexto`/`calarVoz`,
 * que BorisChat.jsx já recebe como import direto (não via ctx).
 */
import { Capacitor } from "@capacitor/core";
import { TextToSpeech } from "@capacitor-community/text-to-speech";

// Safari mata a utterance no GC sem referência viva.
const _vozViva = { u: null };

let _vozAtiva = true;   // "falar ou não" — default LIGADO (comportamento de sempre)
let _vozId = "";        // voiceURI escolhida; "" = deixa a plataforma decidir
let _vozIdxNativo;      // índice resolvido de _vozId pro plugin nativo (fala por índice, não por nome)

// `falarNativo` PRECISA continuar retornando um boolean SÍNCRONO — quem chama
// (`BorisChat.jsx`, `enviarAgora`) usa o retorno na hora pra decidir se volta
// a boca pro estado idle, sem esperar Promise nenhuma. Por isso o índice da
// voz nativa é resolvido AQUI, na troca de config (rara), e cacheado — nunca
// no meio de uma fala (frequente), que exigiria `await` e quebraria o
// contrato síncrono que o resto do app já depende.
export function setVozConfig({ ativa, vozId } = {}) {
  if (typeof ativa === "boolean") _vozAtiva = ativa;
  if (typeof vozId === "string" && vozId !== _vozId) {
    _vozId = vozId;
    _vozIdxNativo = undefined;
    if (Capacitor.isNativePlatform() && vozId) {
      TextToSpeech.getSupportedVoices()
        .then(({ voices }) => {
          const idx = (voices || []).findIndex((v) => v.voiceURI === vozId);
          if (idx >= 0) _vozIdxNativo = idx;
        })
        .catch(() => { /* sem lista de vozes: fala com a voz padrão do sistema */ });
    }
  }
}

function vozesWeb() {
  try {
    const synth = window.speechSynthesis;
    if (!synth) return [];
    return (synth.getVoices() || []).filter((v) => v && /^pt(-|_)BR/i.test(v.lang || ""));
  } catch { return []; }
}

// Lista de vozes pt-BR disponíveis, uniforme entre web e nativo — [{id, nome}].
// `id` é o voiceURI, a mesma chave que `setVozConfig({ vozId })` espera.
// getVoices() no navegador é ASSÍNCRONO na 1ª chamada (evento onvoiceschanged
// dispara depois); por isso aguarda um tick se a lista ainda vier vazia.
export async function listarVozes() {
  if (Capacitor.isNativePlatform()) {
    try {
      const { voices } = await TextToSpeech.getSupportedVoices();
      return (voices || [])
        .filter((v) => v && /^pt(-|_)BR/i.test(v.lang || ""))
        .map((v) => ({ id: v.voiceURI, nome: v.name }));
    } catch { return []; }
  }
  let vs = vozesWeb();
  if (!vs.length && typeof window !== "undefined" && window.speechSynthesis) {
    vs = await new Promise((resolve) => {
      const t = setTimeout(() => resolve(vozesWeb()), 400);
      window.speechSynthesis.onvoiceschanged = () => { clearTimeout(t); resolve(vozesWeb()); };
    });
  }
  return vs.map((v) => ({ id: v.voiceURI, nome: v.name }));
}

function falarWeb(texto, { onStart, onEnd } = {}) {
  try {
    const synth = window.speechSynthesis;
    if (!synth || typeof SpeechSynthesisUtterance === "undefined") { onEnd && onEnd("indisponivel"); return false; }
    synth.cancel();
    const u = new SpeechSynthesisUtterance(String(texto || ""));
    u.lang = "pt-BR";
    // getVoices é assíncrono na 1ª chamada — sem voz explícita (ou sem a
    // escolhida disponível) o sistema escolhe pela `lang`, fallback correto.
    const disponiveis = vozesWeb();
    const escolhida = (_vozId && disponiveis.find((v) => v.voiceURI === _vozId)) || disponiveis[0];
    if (escolhida) u.voice = escolhida;
    u.onstart = () => onStart && onStart();
    u.onend = () => onEnd && onEnd();
    u.onerror = () => onEnd && onEnd("erro");
    _vozViva.u = u;
    synth.speak(u);
    return true;
  } catch { onEnd && onEnd("erro"); return false; }
}

function calarVozWeb() {
  try { if (window.speechSynthesis) window.speechSynthesis.cancel(); } catch { /* melhor mudo que quebrado */ }
}

function falarNativo(texto, { onStart, onEnd } = {}) {
  try {
    onStart && onStart();
    const opts = { text: String(texto || ""), lang: "pt-BR" };
    if (_vozIdxNativo !== undefined) opts.voice = _vozIdxNativo;
    TextToSpeech.speak(opts)
      .then(() => onEnd && onEnd())
      .catch(() => onEnd && onEnd("erro"));
    return true;
  } catch { onEnd && onEnd("erro"); return false; }
}

function calarVozNativo() {
  TextToSpeech.stop().catch(() => { /* melhor mudo que quebrado */ });
}

export function falarTexto(texto, opts = {}) {
  // "falar ou não" desligado: no-op silencioso, mesmo contrato de retorno
  // (false) que o "indisponível" já usava — BorisChat já sabe lidar com isso.
  if (!_vozAtiva) return false;
  return Capacitor.isNativePlatform() ? falarNativo(texto, opts) : falarWeb(texto, opts);
}

export function calarVoz() {
  if (Capacitor.isNativePlatform()) calarVozNativo();
  else calarVozWeb();
}
