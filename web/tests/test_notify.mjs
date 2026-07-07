// Objetivo 2 — trava o contrato de notificações testável fora do device:
//  • gating por preferência/tipo (notifyIfEnabled);
//  • handler de foreground (set/clear) e novos exports;
//  • diag() não quebra no ambiente sem plugin.
import * as notify from "../src/notify.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// novos exports existem
ok("export setForegroundHandler", typeof notify.setForegroundHandler === "function");
ok("export setup", typeof notify.setup === "function");
ok("export notifyIfEnabled", typeof notify.notifyIfEnabled === "function");

// gating: desligado ou tipo off => NÃO notifica (false), sem tentar enviar
const r1 = await notify.notifyIfEnabled({ enabled: false, stop: true }, "stop", "t", "b");
ok("master off => false", r1 === false);
const r2 = await notify.notifyIfEnabled({ enabled: true, stop: false }, "stop", "t", "b");
ok("tipo off => false", r2 === false);
const r3 = await notify.notifyIfEnabled(null, "stop", "t", "b");
ok("prefs nulo => false", r3 === false);
// gate passa (enabled + tipo on): retorna boolean sem lançar (no Node não há
// Notification, então o envio retorna false — o que importa é não quebrar)
const r4 = await notify.notifyIfEnabled({ enabled: true, stop: true }, "stop", "t", "b");
ok("gate aberto => boolean sem throw", typeof r4 === "boolean");

// handler de foreground: set/clear sem throw
let captured = null;
notify.setForegroundHandler((title, body) => { captured = title + "|" + body; });
notify.setForegroundHandler(null);
ok("set/clear handler sem throw", captured === null);

// diag() não quebra fora do device
const d = await notify.diag();
ok("diag retorna objeto", d && typeof d === "object");
ok("diag.isNative definido", "isNative" in d);
ok("diag.permission presente", typeof d.permission === "string");

// setup() é idempotente e não quebra no web
await notify.setup();
await notify.setup();
ok("setup idempotente sem throw", true);


// ---------------------------------------------------------------------------
// BLOCO 1 — novos contratos (ids persistentes, clamp de horário, getPending)
// ---------------------------------------------------------------------------

// getPending exportado e nunca lança (web/Node: devolve os timers vivos)
ok("export getPending", typeof notify.getPending === "function");
const pend0 = await notify.getPending();
ok("getPending devolve array", Array.isArray(pend0));

// schedule devolve ids DISTINTOS em chamadas seguidas (contador não repete;
// no device isso impede que um agendamento novo SUBSTITUA um pendente antigo)
const idA = await notify.schedule("t", "b", new Date(Date.now() + 60000));
const idB = await notify.schedule("t", "b", new Date(Date.now() + 60000));
ok("schedule devolve id", idA != null);
ok("ids consecutivos são distintos", idA !== idB);

// horário no PASSADO é clampado (não descartado): agendamento é aceito
const idPast = await notify.schedule("t", "b", new Date(Date.now() - 5000));
ok("schedule com horário passado ainda agenda (clamp)", idPast != null);

// os agendamentos vivos aparecem no getPending (web: timers da aba)
const pend1 = await notify.getPending();
ok("pendentes registrados após agendar", pend1.length >= 3);

// diag inclui pendingCount quando nativo; no web só não pode quebrar
const d2 = await notify.diag();
ok("diag continua sem lançar após agendamentos", d2 && typeof d2 === "object");

// cancelamento por id limpa o pendente
const cOK = await notify.cancel(idA);
ok("cancel(id) devolve true para pendente vivo", cOK === true);
const pend2 = await notify.getPending();
ok("cancel removeu o id do pendente", !pend2.some((n) => n.id === idA));

// cancelAll zera tudo (higiene entre execuções do teste)
await notify.cancelAll();
const pend3 = await notify.getPending();
ok("cancelAll esvazia os pendentes", pend3.length === 0);

console.log("\n[BLOCO 1] contratos de notificação verificados.");

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DE NOTIFY PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
