// FASE 5 — Guardião: wiring nativo do push (APNs) no projeto iOS.
//
// BUG que motivou este teste: o AppDelegate.swift não reencaminhava
// didRegisterForRemoteNotificationsWithDeviceToken ao Capacitor — o
// PushNotifications.register() do JS nunca resolvia e o registro caía no
// timeout de 15s ("tempo esgotado no registro do push"), mesmo com a
// capability e as chaves APNs corretas. Este teste tranca o contrato no
// texto dos arquivos nativos (mesmo padrão dos demais guardians).
// Roda sem build: `node web/tests/test_push_wiring.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(join(here, "..", ...p), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- AppDelegate reencaminha os callbacks do APNs ao Capacitor -------------
const appDelegate = read(["ios", "App", "App", "AppDelegate.swift"]);
ok("AppDelegate: didRegisterForRemoteNotificationsWithDeviceToken presente",
  appDelegate.includes("didRegisterForRemoteNotificationsWithDeviceToken"));
ok("AppDelegate: posta .capacitorDidRegisterForRemoteNotifications",
  appDelegate.includes(".capacitorDidRegisterForRemoteNotifications"));
ok("AppDelegate: didFailToRegisterForRemoteNotificationsWithError presente",
  appDelegate.includes("didFailToRegisterForRemoteNotificationsWithError"));
ok("AppDelegate: posta .capacitorDidFailToRegisterForRemoteNotifications",
  appDelegate.includes(".capacitorDidFailToRegisterForRemoteNotifications"));

// ---- capacitor.config: banner em foreground para local E push --------------
const capCfg = read(["capacitor.config.ts"]);
ok("config: LocalNotifications.presentationOptions", /LocalNotifications:\s*{[^}]*presentationOptions/s.test(capCfg));
ok("config: PushNotifications.presentationOptions", /PushNotifications:\s*{[^}]*presentationOptions/s.test(capCfg));

// ---- plugins de notificação seguem no pacote SPM do app iOS ----------------
const spm = read(["ios", "App", "CapApp-SPM", "Package.swift"]);
ok("SPM: CapacitorLocalNotifications no build", spm.includes("CapacitorLocalNotifications"));
ok("SPM: CapacitorPushNotifications no build", spm.includes("CapacitorPushNotifications"));

// ---- entitlement do APNs presente ------------------------------------------
const ent = read(["ios", "App", "App", "App.entitlements"]);
ok("entitlements: aps-environment presente", ent.includes("aps-environment"));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
