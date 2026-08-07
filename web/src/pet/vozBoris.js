/**
 * vozBoris.js — a voz do Boris, roteada pela plataforma.
 *
 * `web/src/pet/Boris.jsx` já documenta a razão desta separação: o WKWebView
 * do iOS não confia no `speechSynthesis`. Web/PWA continua com a Web Speech
 * API (já testada, já funciona ali); o app nativo Capacitor usa o plugin de
 * TTS nativo (`@capacitor-community/text-to-speech`), que fala de verdade no
 * aparelho. Ambos os lados expõem a MESMA assinatura de `falarTexto`/`calarVoz`
 * que o app já usa — nenhum call site muda.
 */
import { Capacitor } from "@capacitor/core";
import { TextToSpeech } from "@capacitor-community/text-to-speech";

// Safari mata a utterance no GC sem referência viva.
const _vozViva = { u: null };

function falarWeb(texto, { onStart, onEnd } = {}) {
  try {
    const synth = window.speechSynthesis;
    if (!synth || typeof SpeechSynthesisUtterance === "undefined") { onEnd && onEnd("indisponivel"); return false; }
    synth.cancel();
    const u = new SpeechSynthesisUtterance(String(texto || ""));
    u.lang = "pt-BR";
    // getVoices é assíncrono na 1ª chamada — sem voz explícita o sistema
    // escolhe pela `lang`, que é o comportamento correto de fallback.
    const voz = (synth.getVoices() || []).find((v) => v && /^pt(-|_)BR/i.test(v.lang || ""));
    if (voz) u.voice = voz;
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
    TextToSpeech.speak({ text: String(texto || ""), lang: "pt-BR" })
      .then(() => onEnd && onEnd())
      .catch(() => onEnd && onEnd("erro"));
    return true;
  } catch { onEnd && onEnd("erro"); return false; }
}

function calarVozNativo() {
  TextToSpeech.stop().catch(() => { /* melhor mudo que quebrado */ });
}

export function falarTexto(texto, opts = {}) {
  return Capacitor.isNativePlatform() ? falarNativo(texto, opts) : falarWeb(texto, opts);
}

export function calarVoz() {
  if (Capacitor.isNativePlatform()) calarVozNativo();
  else calarVozWeb();
}
