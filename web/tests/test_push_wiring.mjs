// FASE 5 — Guardião: wiring nativo do push (APNs) no projeto iOS.
//
// BUG que motivou este teste: o AppDelegate.swift não reencaminhava
// didRegisterForRemoteNotificationsWithDeviceToken ao Capacitor — o
// PushNotifications.register() do JS nunca resolvia e o registro caía no
// timeout de 15s ("tempo esgotado no registro do push"), mesmo com a
// capability e as chaves APNs corretas. Este teste tranca o contrato no
// texto dos arquivos nativos (mesmo padrão dos demais guardians).
// Roda sem build: `node web/tests/test_push_wiring.mjs`.
import { existsSync, readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(join(here, "..", ...p), "utf8");

// `web/ios/` é GITIGNORADA — é gerada pelo `cap sync` e existe só no clone
// principal. Num worktree este guardião estourava ENOENT e derrubava o
// `operar.sh testes` inteiro, escondendo o resultado das outras 39 suítes.
// Pular com aviso mantém o gate honesto onde ele PODE rodar (o clone, que é de
// onde sai a entrega para o iPhone) sem dar falso vermelho onde não pode.
if (!existsSync(join(here, "..", "ios", "App", "App", "AppDelegate.swift"))) {
  console.log("PULOU — projeto iOS ausente (web/ios/ é gitignorada; rode no clone principal, após cap sync).");
  process.exit(0);
}

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

// ---- FASE 8 (A1): opções que o plugin LOCAL de fato reconhece ---------------
// CAUSA-RAIZ: o local-notifications 8.x NÃO mapeia "alert" (cai em
// Unrecognized ⇒ nenhuma apresentação visual em foreground); o push mapeia.
// Contrato: "banner" e "list" explícitos, e NUNCA "alert" no LocalNotifications.
{
  const local = (capCfg.match(/LocalNotifications:\s*{([^}]*)}/s) || [])[1] || "";
  ok("LocalNotifications usa banner+list (reconhecidos pelo plugin)", local.includes('"banner"') && local.includes('"list"'));
  ok("LocalNotifications NÃO usa 'alert' (não mapeado ⇒ banner mudo)", !local.includes('"alert"'));
}

// ---- plugins de notificação seguem no pacote SPM do app iOS ----------------
const spm = read(["ios", "App", "CapApp-SPM", "Package.swift"]);
ok("SPM: CapacitorLocalNotifications no build", spm.includes("CapacitorLocalNotifications"));
ok("SPM: CapacitorPushNotifications no build", spm.includes("CapacitorPushNotifications"));

// ---- entitlement do APNs presente ------------------------------------------
const ent = read(["ios", "App", "App", "App.entitlements"]);
ok("entitlements: aps-environment presente", ent.includes("aps-environment"));

// ---- FASE 8B (R1): a cópia SINCRONIZADA do config não pode ficar para trás --
// O app instalado lê web/ios/App/App/capacitor.config.json (gerado pelo cap
// sync). Se ele divergir do capacitor.config.ts, o aparelho roda config velha
// (foi uma das causas de "notificação não funciona"). Este guardião tranca a
// paridade das presentationOptions nos dois arquivos.
{
  const synced = JSON.parse(read(["ios", "App", "App", "capacitor.config.json"]));
  for (const plugin of ["LocalNotifications", "PushNotifications"]) {
    const opts = ((synced.plugins || {})[plugin] || {}).presentationOptions || [];
    ok(`config SINCRONIZADO: ${plugin} com banner+list (sem 'alert')`,
      opts.includes("banner") && opts.includes("list") && !opts.includes("alert"));
  }

  // ---- qa/27: packageClassList precisa listar as classes nativas ----------
  // BUG que motivou: no repositório tudo bate (Package.swift, AppDelegate,
  // presentationOptions), mas o BINÁRIO instalado no iPhone pode não conter
  // o plugin de verdade quando o cache de resolução de pacotes do Xcode
  // (DerivedData + org.swift.swiftpm) fica preso a uma versão antiga do
  // cap sync. Sintoma no aparelho: o app some de Ajustes -> Notificações e
  // qualquer chamada nativa ao plugin (ex.: Diagnóstico) fica pendurada em
  // vez de responder. Este guardião tranca a PARTE que dá pra travar por
  // código — o resto (cache do Xcode) é responsabilidade de
  // scripts/reparo-plugin-nativo.sh, que roda depois de qualquer cap sync
  // suspeito.
  const classes = synced.packageClassList || [];
  for (const cls of ["LocalNotificationsPlugin", "PushNotificationsPlugin"]) {
    ok(`config SINCRONIZADO: packageClassList inclui ${cls}`, classes.includes(cls));
  }
}

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
