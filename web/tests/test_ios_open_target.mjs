// qa/27 (item 2) — Guardião: scripts que abrem o Xcode não podem assumir
// App.xcworkspace como único destino.
//
// BUG: o projeto é 100% SPM (sem CocoaPods/Podfile) — só existe
// ios/App/App.xcodeproj, NUNCA ios/App/App.xcworkspace (esse só existiria
// com CocoaPods). Três scripts (instalar-iphone.sh, setup-ios.sh,
// reparo-plugin-nativo.sh) caíam no fallback `open ios/App/App.xcworkspace`
// quando `npx cap open ios` falhava — arquivo inexistente, comando falha,
// usuário fica sem saber qual arquivo abrir. Este guardião tranca que todo
// script com um fallback de abertura do Xcode também saiba abrir o
// .xcodeproj (não só o .xcworkspace).
// Roda sem build: `node web/tests/test_ios_open_target.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const readScript = (name) => readFileSync(join(here, "..", "..", "scripts", name), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

for (const script of ["instalar-iphone.sh", "setup-ios.sh", "reparo-plugin-nativo.sh"]) {
  const src = readScript(script);
  const mentionsWorkspace = src.includes("App.xcworkspace");
  const mentionsProjectFallback = src.includes("App.xcodeproj");
  // Contrato: se o script menciona xcworkspace (fallback de abertura), ele
  // TEM que também saber abrir/mencionar o xcodeproj — senão um projeto
  // 100% SPM (sem Podfile) fica sem destino válido quando cap open falha.
  ok(`${script}: se menciona App.xcworkspace, também sabe abrir/indicar App.xcodeproj`,
    !mentionsWorkspace || mentionsProjectFallback);
}

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
