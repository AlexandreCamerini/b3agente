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
//  5) o atalho de notificações (A.openNotifCentral) aponta pra área nova;
//  6) (26-01/A6+A8, 2026-09-13) todo "Perfil → X" citado em prosa — pelas
//     mensagens de cota do `server/app/metering.py` (A6) e pelo `ADDR_HINT`
//     de `web/src/api.js` (A8) — é um tile que EXISTE no PerfilHub — ver
//     seção 7, no fim do arquivo.
//
// ATUALIZAÇÃO 2026-08-12 (qa/45 Decisão 1, pedido do Alex "pode seguir com a
// decisão 1 (as 5 telas)"): reversão deliberada dos nomes de tile trancados
// acima — "Conta & preferências"→"Preferências", "Configurações de IA"→
// "IA & Boris", "Logs & debug"→"Diagnóstico" — e nasce uma tela nova,
// FonteDadosScreen, que herda o bloco SERVIDOR DO APP (saiu de
// LogsDebugScreen, onde configuração de aparelho vivia dentro de um painel de
// diagnóstico) e o bloco FONTE DE COTAÇÕES (saiu de dentro do painel de
// Administração de LogsDebugScreen). Conteúdo idêntico, endereço novo — "nada
// some, tudo migra". Os testes abaixo foram atualizados para os nomes e a
// composição de telas atuais; nenhum conteúdo verificado foi removido, só
// realocado nas asserções que seguem o código.
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
ok("hub: Preferências → config", hub.includes('onOpen("config")') && hub.includes('title="Preferências"'));
ok("hub: IA & Boris → ia", hub.includes('onOpen("ia")') && hub.includes('title="IA & Boris"'));
ok("hub: Notificações → notificacoes", hub.includes('onOpen("notificacoes")') && hub.includes('title="Notificações"'));
ok("hub: Eficiência da IA → eficiencia", hub.includes('onOpen("eficiencia")') && hub.includes('title="Eficiência da IA"'));
ok("hub: Fonte de dados → fonteDados", hub.includes('onOpen("fonteDados")') && hub.includes('title="Fonte de dados"'));
ok("hub: Diagnóstico → logs", hub.includes('onOpen("logs")') && hub.includes('title="Diagnóstico"'));

// ---- 2) Telas novas existem; monólito antigo não existe mais -------------
ok("AiConfigScreen existe", /function AiConfigScreen\(\{ ctx \}\)/.test(app));
ok("NotificacoesScreen existe", /function NotificacoesScreen\(\{ ctx \}\)/.test(app));
ok("EficienciaIAScreen existe", /function EficienciaIAScreen\(\{ ctx \}\)/.test(app));
ok("LogsDebugScreen existe", /function LogsDebugScreen\(\{ ctx \}\)/.test(app));
ok("FonteDadosScreen existe (qa/45 Decisão 1)", /function FonteDadosScreen\(\{ ctx \}\)/.test(app));
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
const logsEnd = app.indexOf("function FonteDadosScreen(");
const logs = app.slice(logsStart, logsEnd);
ok("LogsDebugScreen NÃO tem mais SERVIDOR DO APP (mudou p/ FonteDadosScreen)", !logs.includes("SERVIDOR DO APP"));
ok("LogsDebugScreen NÃO tem mais FONTE DE COTAÇÕES (mudou p/ FonteDadosScreen)", !logs.includes("FONTE DE COTAÇÕES"));
ok("LogsDebugScreen tem DIAGNÓSTICO QA", logs.includes("DIAGNÓSTICO QA"));
ok("LogsDebugScreen tem STATUS DO SERVIDOR", logs.includes("STATUS DO SERVIDOR"));
ok("LogsDebugScreen tem DIÁRIO DO OPERADOR", logs.includes("DIÁRIO DO OPERADOR"));
ok("LogsDebugScreen tem LOGS DO SERVIDOR (detalhado)", logs.includes("LOGS DO SERVIDOR (detalhado)"));

// ---- 4b) FonteDadosScreen herda os dois blocos extraídos (qa/45 Decisão 1) -
const fdStart = app.indexOf("function FonteDadosScreen(");
const fdEnd = app.indexOf("/* BLOCO 3 — Radar de mercado");
const fd = app.slice(fdStart, fdEnd);
ok("FonteDadosScreen localizado", fdStart > -1 && fdEnd > fdStart);
ok("FonteDadosScreen tem SERVIDOR DO APP", fd.includes("SERVIDOR DO APP"));
ok("FonteDadosScreen tem FONTE DE COTAÇÕES", fd.includes("FONTE DE COTAÇÕES"));

// ---- 5) Roteamento cobre as 7 rotas ---------------------------------------
ok("rota: config → ConfigScreen", /perfilView === "config"[\s\S]{0,120}<ConfigScreen ctx=\{ctx\} \/>/.test(app));
ok("rota: ia → AiConfigScreen", /perfilView === "ia"[\s\S]{0,120}<AiConfigScreen ctx=\{ctx\} \/>/.test(app));
ok("rota: notificacoes → NotificacoesScreen", /perfilView === "notificacoes"[\s\S]{0,120}<NotificacoesScreen ctx=\{ctx\} \/>/.test(app));
ok("rota: eficiencia → EficienciaIAScreen", /perfilView === "eficiencia"[\s\S]{0,120}<EficienciaIAScreen ctx=\{ctx\} \/>/.test(app));
ok("rota: fonteDados → FonteDadosScreen", /perfilView === "fonteDados"[\s\S]{0,120}<FonteDadosScreen ctx=\{ctx\} \/>/.test(app));
ok("rota: logs → LogsDebugScreen", /perfilView === "logs"[\s\S]{0,120}<LogsDebugScreen ctx=\{ctx\} \/>/.test(app));

// ---- 6) Atalho de notificações aponta pra área nova -----------------------
ok("openNotifCentral navega para notificacoes", /openNotifCentral:.*setPerfilView\("notificacoes"\).*setTab\("perfil"\)/.test(app));

// ---- 7) "Perfil → X" citado em prosa é um tile que EXISTE -----------------
// NOVO em 26-01/A6 (2026-09-13). O achado: as três mensagens de 402 do
// `metering.py` mandavam a pessoa para "Perfil → Conta & preferências" — tela
// que o qa/45 Decisão 1 renomeou (o bloco de BYOK/modelo vive em "IA & Boris").
// O rename passou silencioso porque NADA cruzava o texto do backend com os
// tiles reais do PerfilHub: o teste acima trava os tiles, o `metering.py` cita
// um caminho em prosa, e os dois nunca se olhavam. Este bloco fecha o par —
// um próximo rename de tile quebra AQUI, em vez de deixar a mensagem de cota
// apontando para um endereço morto.
//
// AMPLIADO em A8 (2026-09-13): `web/src/api.js` (ADDR_HINT) tinha o MESMO
// defeito com outro destino — citava "Perfil → Conta & preferências" quando o
// bloco SERVIDOR DO APP migrou para "Perfil → Fonte de dados" (qa/45 Decisão
// 1). Corrigido junto; o laço abaixo agora cobre as duas fontes em vez de só
// `metering.py`, para que os dois lados do par nunca voltem a divergir sem o
// teste notar.
const metering = readFileSync(join(here, "..", "..", "server", "app", "metering.py"), "utf8");
const apiJs = readFileSync(join(here, "..", "src", "api.js"), "utf8");
const hubTightEnd = app.indexOf("function SetorAlvo(");
ok("PerfilHub delimitado (corpo real, não até MercadoScreen)", hubTightEnd > hubStart);
const tiles = [...app.slice(hubStart, hubTightEnd).matchAll(/title="([^"]+)"/g)].map((m) => m[1]);
ok("PerfilHub expõe tiles com título literal", tiles.length >= 6);

const SETA = "Perfil → ";
function citacoesDe(fonte) {
  const out = [];
  for (let i = fonte.indexOf(SETA); i > -1; i = fonte.indexOf(SETA, i + 1)) {
    const depois = fonte.slice(i + SETA.length);
    out.push({ tile: tiles.find((t) => depois.startsWith(t)), trecho: depois.slice(0, 40) });
  }
  return out;
}

const citacoesMetering = citacoesDe(metering);
ok("metering.py cita as 3 mensagens de cota com caminho do Perfil", citacoesMetering.length === 3);
for (const { tile, trecho } of citacoesMetering) {
  ok(`metering.py → tile real (${tile || "NENHUM: " + JSON.stringify(trecho)})`, !!tile);
}

// Achado A8, ao rodar este guardião pela primeira vez: uma SEGUNDA citação
// stale apareceu de graça — o comentário de `analysisOutcomesStats` ainda
// dizia "(Perfil → Observabilidade)", a tela monolítica que o qa/45 já tinha
// dividido em 6 áreas (item 2 acima). Corrigido para "Eficiência da IA", o
// tile real da estatística que o comentário descreve.
const citacoesApi = citacoesDe(apiJs);
ok("api.js cita 2 caminhos do Perfil (ADDR_HINT + comentário)", citacoesApi.length === 2);
for (const { tile, trecho } of citacoesApi) {
  ok(`api.js → tile real (${tile || "NENHUM: " + JSON.stringify(trecho)})`, !!tile);
}

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
