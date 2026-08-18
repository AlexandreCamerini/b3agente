// qa/20 — correções da auditoria App Store aplicáveis por código.
// B1 (instrumento): guarda de BOOT em index.html — JS morrendo antes do React
//     montar pintava TELA PRETA indiagnosticável; agora pinta o erro real.
// B2: manifesto de privacidade com a coleta REAL (login obrigatório ⇒ e-mail,
//     UserID, DeviceID/push e conteúdo do usuário — nada de tracking).
// B5: botão Google some no build nativo sem os client ids (botão visível que
//     falha ao toque = rejeição 2.1).
// R4: strings de permissão de voz entram pelo setup-ios.sh (idempotente).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
const here = dirname(fileURLToPath(import.meta.url));
const lê = (...p) => readFileSync(join(here, ...p), "utf8");
let fails = 0;
const ok = (n, c) => { console.log((c ? "ok " : "FALHOU ") + n); if (!c) fails++; };

// --- B1: guarda de boot -------------------------------------------------------
const idx = lê("..", "index.html");
ok("guarda de BOOT presente no index.html", idx.includes("Guarda de BOOT"));
ok("só age com o #root vazio (depois é o ErrorBoundary)", idx.includes("children.length === 0"));
ok("falha de recurso: só <script> (fonte offline não é erro de boot)",
  idx.includes('tagName === "SCRIPT"'));
ok("painel se remove se o app montar (falso positivo não trava boot saudável)",
  /setTimeout\(function \(\) \{ if \(!rootVazio\(\)\)/.test(idx));
ok("captura unhandledrejection além de error", idx.includes("unhandledrejection"));
ok("guarda vem ANTES do módulo do app", idx.indexOf("Guarda de BOOT") < idx.indexOf('src="/src/main.jsx"'));

// --- B2: manifesto de privacidade --------------------------------------------
const priv = lê("..", "..", "resources", "ios", "PrivacyInfo.xcprivacy");
for (const tipo of ["EmailAddress", "UserID", "DeviceID", "OtherUserContent"]) {
  ok("manifesto declara " + tipo, priv.includes("NSPrivacyCollectedDataType" + tipo));
}
ok("manifesto: nada usado para tracking",
  !priv.includes("<key>NSPrivacyCollectedDataTypeTracking</key>\n      <true/>")
  && priv.includes("<key>NSPrivacyTracking</key>\n  <false/>"));
ok("required-reason do UserDefaults preservada (CA92.1)", priv.includes("CA92.1"));

// --- B5: Google escondido sem config no nativo --------------------------------
// ATUALIZADO 2026-08-17: virou ternário para o web também exigir o PRÓPRIO
// client id (antes bastava `!isNative`, sem checar config nenhuma) — mas a
// garantia que a 2.1 pede (nativo sem os 2 client ids = botão some) é a
// MESMA; só a forma da guarda mudou. Ver test_social_login.mjs para a
// checagem completa do ternário.
const app = lê("..", "src", "App.jsx");
ok("guarda googleOk exige os 2 client ids no NATIVO",
  app.includes("Boolean(import.meta.env?.VITE_GOOGLE_IOS_CLIENT_ID && import.meta.env?.VITE_GOOGLE_WEB_CLIENT_ID)"));
ok("botão Google condicionado à guarda", app.includes("{googleOk && ("));
ok("Apple continua incondicional e primeiro (4.8)",
  app.indexOf("Continuar com a Apple") > 0
  && app.indexOf("Continuar com a Apple") < app.indexOf("Continuar com o Google"));

// --- R4: strings de voz no setup ----------------------------------------------
const setup = lê("..", "..", "scripts", "setup-ios.sh");
ok("setup-ios adiciona NSMicrophoneUsageDescription", setup.includes("NSMicrophoneUsageDescription"));
ok("setup-ios adiciona NSSpeechRecognitionUsageDescription", setup.includes("NSSpeechRecognitionUsageDescription"));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
