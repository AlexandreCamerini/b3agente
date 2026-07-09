// qa/32/33 — Guardião: reorganização do Perfil em áreas dedicadas.
//
// Pedido do Alex: "a aplicação está ficando com muitas funcionalidades...
// deveríamos ter uma área dedicada a Notificações, uma [para] configurações
// de IA, uma [para] eficiência da IA, outra para logs e debug." Aprovado após
// mockup ("vamos seguir"). Contratos trancados:
//  1) PerfilHub oferece as 6 áreas (Conta, Conta & preferências, Config. de
//     IA, Notificações, Eficiência da IA, Logs & debug);
//  2) 4 telas novas existem (AiConfigScreen, NotificacoesScreen,
//     EficienciaIAScreen, LogsDebugScreen) e a antiga ObservabilidadeScreen
//     monolítica não existe mais;
//  3) ConfigScreen (agora só "Conta & preferências") NÃO contém mais as
//     seções que se mudaram — sem duplicação de UI;
//  4) o roteamento (perfilView) cobre as 6 rotas;
//  5) o atalho de notificações (A.openNotifCentral) aponta pra área nova.
// Roda sem device nem build: `node web/tests/test_perfil_reorg.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) PerfilHub: 6 áreas -----------------------------------------------
const hubStart = app.indexOf("function PerfilHub(");
const hubEnd = app.indexOf("function MercadoScreen(");
const hub = app.slice(hubStart, hubEnd);
ok("PerfilHub localizado", hubStart > -1 && hubEnd > hubStart);
ok("hub: Conta (auth)", hub.includes('ctx.openAuth && ctx.openAuth()'));
ok("hub: Conta & preferências → config", hub.includes('onOpen("config")'));
ok("hub: Configurações de IA → ia", hub.includes('onOpen("ia")') && hub.includes('title="Configurações de IA"'));
ok("hub: Notificações → notificacoes", hub.includes('onOpen("notificacoes")') && hub.includes('title="Notificações"'));
ok("hub: Eficiência da IA → eficiencia", hub.includes('onOpen("eficiencia")') && hub.includes('title="Eficiência da IA"'));
ok("hub: Logs & debug → logs", hub.includes('onOpen("logs")') && hub.includes('title="Logs & debug"'));

// ---- 2) Telas novas existem; monólito antigo não existe mais -------------
ok("AiConfigScreen existe", /function AiConfigScreen\(\{ ctx \}\)/.test(app));
ok("NotificacoesScreen existe", /function NotificacoesScreen\(\{ ctx \}\)/.test(app));
ok("EficienciaIAScreen existe", /function EficienciaIAScreen\(\{ ctx \}\)/.test(app));
ok("LogsDebugScreen existe", /function LogsDebugScreen\(\{ ctx \}\)/.test(app));
ok("ObservabilidadeScreen (monólito antigo) não existe mais", !/function ObservabilidadeScreen/.test(app));

// ---- 3) ConfigScreen ficou SLIM (sem duplicar o que se mudou) ------------
const cfgStart = app.indexOf("function ConfigScreen(");
const cfgEnd = app.indexOf("function CatalogModal(");
const cfg = app.slice(cfgStart, cfgEnd);
ok("ConfigScreen localizado", cfgStart > -1 && cfgEnd > cfgStart);
ok("ConfigScreen mantém PERSONALIZAÇÃO", cfg.includes("PERSONALIZAÇÃO"));
ok("ConfigScreen mantém PERÍODO DE DADOS", cfg.includes("PERÍODO DE DADOS"));
ok("ConfigScreen mantém ORÇAMENTO", cfg.includes("ORÇAMENTO DE INVESTIMENTO"));
ok("ConfigScreen mantém PERFIL DO OPERADOR", cfg.includes("PERFIL DO OPERADOR"));
ok("ConfigScreen NÃO tem mais <NotifSection", !cfg.includes("<NotifSection"));
ok("ConfigScreen NÃO tem mais SERVIDOR DO APP", !cfg.includes("SERVIDOR DO APP"));
ok("ConfigScreen NÃO tem mais DIAGNÓSTICO QA", !cfg.includes("DIAGNÓSTICO QA"));
ok("ConfigScreen NÃO tem mais MODELO DE IA DO AGENTE", !cfg.includes("MODELO DE IA DO AGENTE"));
ok("ConfigScreen NÃO tem mais <SkillSection", !cfg.includes("<SkillSection"));
ok("ConfigScreen NÃO tem mais <PromptsSection", !cfg.includes("<PromptsSection"));

// ---- 4) As seções migradas realmente vivem nas telas novas ---------------
const aiStart = app.indexOf("function AiConfigScreen(");
const aiEnd = app.indexOf("function NotificacoesScreen(");
const ai = app.slice(aiStart, aiEnd);
ok("AiConfigScreen tem MODELO DE IA DO AGENTE", ai.includes("MODELO DE IA DO AGENTE"));
ok("AiConfigScreen usa <SkillSection", ai.includes("<SkillSection ctx={ctx}"));
ok("AiConfigScreen usa <PromptsSection", ai.includes("<PromptsSection ctx={ctx}"));

const notifScreenStart = app.indexOf("function NotificacoesScreen(");
const notifScreenEnd = app.indexOf("function EficienciaIAScreen(");
const notifScreen = app.slice(notifScreenStart, notifScreenEnd);
ok("NotificacoesScreen usa <NotifSection", notifScreen.includes("<NotifSection ctx={ctx}"));

const logsStart = app.indexOf("function LogsDebugScreen(");
const logsEnd = app.indexOf("function CatalogModal(");
const logs = app.slice(logsStart, logsEnd);
ok("LogsDebugScreen tem SERVIDOR DO APP", logs.includes("SERVIDOR DO APP"));
ok("LogsDebugScreen tem DIAGNÓSTICO QA", logs.includes("DIAGNÓSTICO QA"));
ok("LogsDebugScreen tem STATUS DO SERVIDOR", logs.includes("STATUS DO SERVIDOR"));
ok("LogsDebugScreen tem DIÁRIO DO OPERADOR", logs.includes("DIÁRIO DO OPERADOR"));
ok("LogsDebugScreen tem LOGS DO SERVIDOR (detalhado)", logs.includes("LOGS DO SERVIDOR (detalhado)"));

// ---- 5) Roteamento cobre as 6 rotas ---------------------------------------
ok("rota: config → ConfigScreen", /perfilView === "config"[\s\S]{0,120}<ConfigScreen ctx=\{ctx\} \/>/.test(app));
ok("rota: ia → AiConfigScreen", /perfilView === "ia"[\s\S]{0,120}<AiConfigScreen ctx=\{ctx\} \/>/.test(app));
ok("rota: notificacoes → NotificacoesScreen", /perfilView === "notificacoes"[\s\S]{0,120}<NotificacoesScreen ctx=\{ctx\} \/>/.test(app));
ok("rota: eficiencia → EficienciaIAScreen", /perfilView === "eficiencia"[\s\S]{0,120}<EficienciaIAScreen ctx=\{ctx\} \/>/.test(app));
ok("rota: logs → LogsDebugScreen", /perfilView === "logs"[\s\S]{0,120}<LogsDebugScreen ctx=\{ctx\} \/>/.test(app));

// ---- 6) Atalho de notificações aponta pra área nova -----------------------
ok("openNotifCentral navega para notificacoes", /openNotifCentral:.*setPerfilView\("notificacoes"\).*setTab\("perfil"\)/.test(app));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
