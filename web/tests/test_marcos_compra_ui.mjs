// Quick 261026-epr — guardião estático da prévia de proteção na COMPRA:
// BuyModal pede a prévia ao servidor (compra: true), exige autorização explícita
// para entrar sem stop/alvo, confirmBuy não reabre o modal com protecao "sem",
// StopAlvoModal recalcula no preço atual. Roda sem build: node web/tests/test_marcos_compra_ui.mjs
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const aqui = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(aqui, "../src/App.jsx"), "utf8");
const api = readFileSync(join(aqui, "../src/api.js"), "utf8");
const pers = readFileSync(join(aqui, "../src/persistence.js"), "utf8");
let fails = 0;
const ok = (name, cond, extra) => { console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || ""))); if (!cond) fails++; };
const corpo = (ini, fim) => { const i = app.indexOf(ini); return app.slice(i, app.indexOf(fim, i)); };

const buy = corpo("function BuyModal(", "\n}\n");
const stopAlvo = corpo("function StopAlvoModal(", "\n}\n");
const iConfirm = app.indexOf("confirmBuy: async");
const confirm = app.slice(iConfirm, app.indexOf("openTech", iConfirm) > iConfirm ? iConfirm + 4500 : iConfirm + 4500);

ok("BuyModal chama store.marcos com compra: true", /store\.marcos\([^)]*compra: true/.test(buy));
ok("prévia anunciada (aria-live polite)", /aria-live="polite"/.test(buy));
ok("BuyModal usa as chaves do vocabulário (prévia, recalcular, gravar, autorização)",
   ["compra_previa_titulo", "compra_previa_recalcular", "compra_gravar_protecao", "compra_sem_protecao_check", "compra_sem_protecao_motivo"].every((k) => buy.includes('"' + k + '"')));
ok("checkbox de autorização nasce desmarcado", /useState\(false\)/.test(buy) && /setAutoriza/.test(buy));
ok("Confirmar desabilitado sem autorização (faltaAutorizacao)", /faltaAutorizacao = exigeAutorizacao && !autoriza/.test(buy) && /disabled=\{[^}]*faltaAutorizacao/.test(buy));
ok("prévia inválida/erro exige autorização", /exigeAutorizacao = previaFalhou/.test(buy));
ok("desmarcar gravar vira protecao \"sem\"", /protecaoEscolhida = previaOk && gravar \? "motor" : "sem"/.test(buy));
ok("labels clicáveis com alvo de 44px", (buy.match(/minHeight: 44[^}]*alignItems: "flex-start"/g) || []).length >= 2);
ok("BuyModal confirma passando a escolha", /A\.confirmBuy\(protecaoEscolhida\)/.test(buy));
ok("BuyModal não envia stop/alvo ao confirmar", !/confirmBuy\([^)]*(stop|alvo)/.test(buy));

ok("confirmBuy recebe protecao e repassa ao store.buy", /confirmBuy: async \(protecao\)/.test(app) && /store\.buy\(bm\.t, bm\.qty, bm\.meta \|\| undefined, protecao/.test(app));
ok("confirmBuy não abre o StopAlvoModal com protecao \"sem\"", /if \(protecao !== "sem"\) \{\s*setStopAlvoFor\(bm\.t\);\s*A\.runStopAlvoFor\(bm\.t\);/.test(confirm));

ok("StopAlvoModal envia recalcular: true", /recalcular: true/.test(stopAlvo));
ok("StopAlvoModal prefere busca.data depois de recalcular", /!recalculado && r\.marcos/.test(stopAlvo));
ok("StopAlvoModal usa modal_recalcular", /"modal_recalcular"/.test(stopAlvo));

ok("api.buy envia protecao só quando definido", /buy: \(t, qty, meta, protecao\)/.test(api) && /protecao \? \{ protecao \}/.test(api));
ok("serverStore e deviceStore repassam protecao", /buy: \(t, qty, meta, protecao\) => api\.buy\(t, qty, meta, protecao\)/.test(pers) && /async buy\(t, qty, meta, protecao\)/.test(pers) && /api\.buy\(t, qty, meta, protecao\)/.test(pers));
ok("deviceStore legado: \"sem\" não pede marcos; senão compra: true", /protecao === "sem"/.test(pers) && /compra: true/.test(pers));

if (fails) { console.error("\n" + fails + " falha(s)"); process.exit(1); }
console.log("\ntodos os testes passaram");
