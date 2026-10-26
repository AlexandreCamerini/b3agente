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
ok("desmarcar gravar vira protecao \"sem\"", /protecaoEscolhida = \(previaOk && gravar\) \|\| previa\.status === "mantem" \? "motor" : "sem"/.test(buy));
ok("labels clicáveis com alvo de 44px", (buy.match(/minHeight: 44[^}]*alignItems: "flex-start"/g) || []).length >= 2);
ok("BuyModal confirma passando a escolha", /A\.confirmBuy\(protecaoEscolhida, previaEnviada\)/.test(buy));
ok("BuyModal não envia stop/alvo ao confirmar (só a previa, para comparar)", !/confirmBuy\([^)]*(\.stop|\.alvo)/.test(buy));

ok("confirmBuy recebe protecao e repassa ao store.buy", /confirmBuy: async \(protecao, previa\)/.test(app) && /store\.buy\(bm\.t, bm\.qty, bm\.meta \|\| undefined, protecao/.test(app));
ok("confirmBuy não abre o StopAlvoModal com protecao \"sem\"", /if \(protecao !== "sem" && !s\.marcos\) \{\s*setStopAlvoFor\(bm\.t\);\s*A\.runStopAlvoFor\(bm\.t\);/.test(confirm));

ok("StopAlvoModal envia recalcular: true", /recalcular: true/.test(stopAlvo));
ok("StopAlvoModal prefere busca.data depois de recalcular", /!recalculado && r\.marcos/.test(stopAlvo));
ok("StopAlvoModal usa modal_recalcular", /"modal_recalcular"/.test(stopAlvo));

ok("api.buy envia protecao só quando definido", /buy: \(t, qty, meta, protecao, previa\)/.test(api) && /protecao \? \{ protecao \}/.test(api) && /protecao === "motor" \? \{ previa: previa \|\| null \}/.test(api));
ok("serverStore e deviceStore repassam protecao", /buy: \(t, qty, meta, protecao, previa\) => api\.buy\(t, qty, meta, protecao, previa\)/.test(pers) && /async buy\(t, qty, meta, protecao, previa\)/.test(pers));
ok("deviceStore legado: \"sem\" não pede marcos; senão compra: true", /protecao === "sem"/.test(pers) && /compra: true/.test(pers));

// ---- Plano 02 (R1-R7) ----
ok("R2: o efeito da prévia depende do preço arredondado, com debounce de 800 ms", /precoPrevia = precoBruto != null \? Math\.round\(precoBruto \* 100\) \/ 100/.test(buy) && /\[t, setupPrevia, recalcTick, precoPrevia, mantemMarcos\]/.test(buy) && /: 800/.test(buy) && /setTimeout\(/.test(buy));
ok("R2: sem preço a prévia está loading, não error", /precoPrevia == null\) \{ setPrevia\(\{ status: "loading"/.test(buy));
ok("R2: autorização zera quando status ou par stop/alvo mudam", /setAutoriza\(false\); \}, \[previa\.status, parPrevia\]/.test(buy));
ok("R1: 409 previa_mudou mantém o modal aberto com prévia nova e aviso", /e\.status === 409 && e\.detail && e\.detail\.code === "previa_mudou"/.test(app) && /reprevia: \{ marcos: e\.detail\.marcos/.test(app) && /setBuyModal\(null\)/.test(confirm) && /setAviso\(reprevia\.mensagem/.test(buy));
ok("R1: o 409 não fecha o modal nem comprou (retorna antes do refresh/flash)", /previa_mudou"\) \{[\s\S]*?\n\s*return;\s*\}\s*\/\/ FIX-C02/.test(confirm));
ok("R1: a previa enviada vem só dos números exibidos e só com gravar marcado", /previaEnviada = previaOk && gravar \? \{ stop: previa\.m\.stop, alvo: previa\.m\.alvo \} : null/.test(buy));
ok("R1: carimbo preço/hora da prévia (princípio 3)", /"compra_previa_carimbo"/.test(buy));
ok("R3: posição com stop e alvo mostra compra_previa_mantem_marcos em vez do checkbox", /compra_previa_mantem_marcos/.test(buy) && /mantemMarcos = !!\(posAtual && posAtual\.stop && posAtual\.alvo\)/.test(buy));
ok("R6: deviceStore sem sessão: protecao ausente segue o caminho antigo (sem compra: true)", /if \(protecao === "motor"\) corpo\.compra = true;/.test(pers) && /protecao == null && meta && meta\.setup/.test(pers));
ok("R3/R1: deviceStore espelha marcos mantidos e o 409 previa_mudou", /compra_marcos_mantidos/.test(pers) && /e\.code = "previa_mudou"/.test(pers) && /e\.status = 409/.test(pers));
ok("R7: a11y — aria-live só no texto de status, não no painel", !/<div aria-live="polite" style=\{\{ marginTop: "12px"/.test(buy) && /<span aria-live="polite"/.test(buy));
ok("R7: motivo visível quando Confirmar está desabilitado por falta de autorização", /"compra_falta_autorizacao"/.test(buy) && /aria-describedby=\{faltaAutorizacao/.test(buy));
ok("R7: guarda de duplo toque ANTES do await store.buy e liberada no catch", /if \(buyEnvioRef\.current\) return;\s*buyEnvioRef\.current = true;[\s\S]*?await store\.buy/.test(confirm) && /catch \(e\) \{\s*buyEnvioRef\.current = false;/.test(confirm));
ok("R7: confirmBuy não abre o StopAlvoModal quando s.marcos veio gravado", /protecao !== "sem" && !s\.marcos/.test(confirm));

if (fails) { console.error("\n" + fails + " falha(s)"); process.exit(1); }
console.log("\ntodos os testes passaram");
