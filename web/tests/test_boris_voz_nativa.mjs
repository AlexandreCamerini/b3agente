// A VOZ NATIVA DO BORIS — WKWebView no iOS não confia no `speechSynthesis`
// (documentado no cabeçalho de web/src/pet/Boris.jsx). vozBoris.js roteia
// por `Capacitor.isNativePlatform()`: web continua com speechSynthesis;
// nativo usa o plugin @capacitor-community/text-to-speech.
//
// Roda sem build: `node web/tests/test_boris_voz_nativa.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const vozSrc = readFileSync(join(here, "..", "src", "pet", "vozBoris.js"), "utf8");
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const borisChat = readFileSync(join(here, "..", "src", "pet", "BorisChat.jsx"), "utf8");
const pkg = JSON.parse(readFileSync(join(here, "..", "package.json"), "utf8"));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

ok("o plugin de TTS nativo está em package.json (dependencies, não dev)",
   !!(pkg.dependencies && pkg.dependencies["@capacitor-community/text-to-speech"]));

ok("vozBoris.js importa Capacitor e o plugin de TTS",
   /import \{ Capacitor \} from ["']@capacitor\/core["'];/.test(vozSrc)
   && /import \{ TextToSpeech \} from ["']@capacitor-community\/text-to-speech["'];/.test(vozSrc));

ok("falarTexto roteia por Capacitor.isNativePlatform() — nativo vs. web",
   /export function falarTexto\(texto, opts = \{\}\) \{[\s\S]{0,200}return Capacitor\.isNativePlatform\(\) \? falarNativo\(texto, opts\) : falarWeb\(texto, opts\);/.test(vozSrc));

ok("calarVoz também roteia — TextToSpeech.stop() no nativo, speechSynthesis.cancel() no web",
   /export function calarVoz\(\) \{\s*\n\s*if \(Capacitor\.isNativePlatform\(\)\) calarVozNativo\(\);\s*\n\s*else calarVozWeb\(\);/.test(vozSrc));

ok("a rota nativa fala em pt-BR pelo plugin (TextToSpeech.speak)",
   /const opts = \{ text: String\(texto \|\| ""\), lang: "pt-BR" \};[\s\S]{0,120}TextToSpeech\.speak\(opts\)/.test(vozSrc));

// F10-20260809 — tela de config do Boris: 1º e 2º controles (voz, falar/não).
ok("setVozConfig existe e é exportado (setter externo, mesmo padrão de setApiBase/setAuthToken)",
   /export function setVozConfig\(\{ ativa, vozId \} = \{\}\) \{/.test(vozSrc));
ok("falarTexto desliga com _vozAtiva=false (no-op silencioso, sem call site novo)",
   /if \(!_vozAtiva\) return false;/.test(vozSrc));
ok("listarVozes existe e filtra pt-BR nas duas plataformas",
   /export async function listarVozes\(\)/.test(vozSrc)
   && (vozSrc.match(/\/\^pt\(-\|_\)BR\/i/g) || []).length >= 2);
ok("a voz nativa é resolvida por ÍNDICE na troca de config (síncrono no momento de falar) — nunca com await dentro de falarNativo",
   /_vozIdxNativo/.test(vozSrc) && !/async function falarNativo/.test(vozSrc));

ok("a rota web NÃO muda — continua speechSynthesis/SpeechSynthesisUtterance",
   /window\.speechSynthesis/.test(vozSrc) && /new SpeechSynthesisUtterance/.test(vozSrc));

ok("falarNativo/falarWeb preservam a assinatura (texto, {onStart, onEnd}) — nenhum call site muda",
   /function falarNativo\(texto, \{ onStart, onEnd \} = \{\}\)/.test(vozSrc)
   && /function falarWeb\(texto, \{ onStart, onEnd \} = \{\}\)/.test(vozSrc));

// Fase 1 (2026-08-08): PetSheet.ouvir (o botão sobre o resumo) saiu junto com
// o resumo — BorisChat.enviarAgora é o ÚNICO call site de voz que resta,
// mas continua sem caminho novo (mesma falarTexto/calarVoz de sempre).
ok("App.jsx NÃO chama mais falarTexto sozinho fora do BorisChat (o handler `ouvir` do resumo saiu)",
   !/const ouvir = \(\) => \{/.test(app));
ok("BorisChat.enviarAgora continua usando falarTexto/calarVoz — sem novo caminho de voz",
   /const ok = falarTexto \? falarTexto\(resp\.texto, \{/.test(borisChat));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
