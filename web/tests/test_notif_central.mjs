// FASE 6 (fix 4) — Guardião: CENTRAL ÚNICA de notificações + permissão real.
//
// BUGS/UX que motivaram este teste:
//  • controles espalhados em 3 telas (Config, Operador IA, Observabilidade);
//  • "Pedir permissão" parecia morto: após UMA negativa o iOS nunca pergunta
//    de novo — o único caminho é Ajustes, e não havia botão para lá.
// Contratos trancados:
//  1) notify.openSettings existe (app-settings: via AppLauncher, degradando
//     com motivo claro sem o plugin) e a dependência está no package.json;
//  2) a Config tem o botão "Abrir Ajustes" no estado denied e "Pedir
//     permissão" só no estado default (não promete o que o iOS não faz);
//  3) o push do servidor (ativar + testar) mora NA central;
//  4) o Operador IA não tem mais botão próprio de push — só o atalho.
// Roda sem build: `node web/tests/test_notif_central.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import * as notify from "../src/notify.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const pkg = JSON.parse(readFileSync(join(here, "..", "package.json"), "utf8"));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) openSettings: contrato executável ----------------------------------
ok("notify.openSettings exportado", typeof notify.openSettings === "function");
const r = await notify.openSettings(); // em Node (não-nativo) degrada para false
ok("openSettings fora do nativo devolve false sem lançar", r === false);
ok("dependência @capacitor/app-launcher no package.json", !!pkg.dependencies["@capacitor/app-launcher"]);

// ---- 2) botões coerentes com os estados REAIS do iOS ------------------------
// FASE 8B (R1): contrato ATUALIZADO — pedir permissão fica disponível em
// default E denied. Depois de reinstalar o app, o iOS pode reportar "denied"
// herdado e o BolsIA some de Ajustes → Notificações até um novo request;
// só oferecer "Abrir Ajustes" criava beco sem saída (a regressão relatada).
ok("'Pedir permissão' disponível quando não concedida (default+denied)", app.includes('perm !== "granted" && perm !== "unsupported" && <button onClick={onRequestPermission}'));
ok("'Abrir Ajustes' no estado denied", app.includes('perm === "denied" && isNative && <button onClick={onOpenSettings}'));
ok("mensagem explica que o iOS só pergunta UMA vez", app.includes("só pergunta UMA vez") || app.includes("não vai perguntar de novo"));

// ---- 3) push do servidor mora na central ------------------------------------
ok("central tem 'Ativar push neste aparelho'", app.includes("Ativar push neste aparelho"));
ok("central tem 'Testar push'", app.includes(">Testar push</button>"));
ok("central registra o token via registerPush", /onAtivarPush[\s\S]{0,200}notify\.registerPush\(\(tk\) => store\.registerPushToken\(tk\)\)/.test(app));
ok("central usa store.pushTest para o teste", /onTestarPush[\s\S]{0,200}store\.pushTest\(\)/.test(app));
ok("push exige permissão concedida (botão desabilitado sem ela)", /onAtivarPush\} disabled=\{pushBusy \|\| perm !== "granted"\}/.test(app));

// ---- 4) Operador IA sem controle duplicado ----------------------------------
ok("Operador IA não tem mais botão próprio de push", !app.includes("Ativar push das ações"));
ok("Operador IA aponta para a central (atalho)", app.includes("A.openNotifCentral()"));
// qa/32: Notificações virou área DEDICADA do Perfil (antes vivia dentro da
// Config) — o atalho passou a navegar direto pra ela em vez de "config".
ok("atalho navega direto para Notificações (perfilView notificacoes)", /openNotifCentral:.*setPerfilView\("notificacoes"\).*setTab\("perfil"\)/.test(app));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
