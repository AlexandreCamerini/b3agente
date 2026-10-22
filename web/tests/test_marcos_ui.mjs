// Fase 50 (plano 50-09) — guardião estático da UI dos marcos do motor:
// modal de stop/alvo sobre store.marcos (D-04/D-10), Aplicar sempre habilitado
// com recusa visível no modal (D-17), toggle de gestão (D-14), estado "plano
// inválido" no card (D-13), rótulos de R:R (D-05) e bloco do plano/régua sem
// alvoSugerido/"ALVO 2:1" (D-18). Roda sem build: `node web/tests/test_marcos_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const aqui = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(aqui, "../src/App.jsx"), "utf8");
const estrutura = readFileSync(join(aqui, "../src/estruturaCard.js"), "utf8");
let fails = 0;
const ok = (name, cond, extra) => { console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || ""))); if (!cond) fails++; };

const iModal = app.indexOf("function StopAlvoModal(");
const fimModal = app.indexOf("\n}\n", iModal);
const modal = app.slice(iModal, fimModal);

// ---- Task 1: modal sobre os marcos do motor --------------------------------
ok("localProposal removida (sem function localProposal)", !/function localProposal/.test(app));
ok("modal busca store.marcos(", /store\.marcos\(/.test(modal));
ok("modal sem 'ESTIMATIVA PELO PERFIL'", !/ESTIMATIVA PELO PERFIL/.test(app));
ok("modal sem setSelPerfil (cenários não selecionáveis)", !/setSelPerfil/.test(app));
ok("Aplicar sem disabled atrelado a canApply (D-17)", !/disabled=\{!canApply\}/.test(app) && !/canApply/.test(modal));
ok("Aplicar sem disabled/aria-disabled no botão do modal", !/onClick=\{apply\}[^>]*disabled/.test(modal) && !/aria-disabled/.test(modal));
ok("recusa do motor dentro do modal (modal_recusa_titulo + role=alert)", /modal_recusa_titulo/.test(modal) && /role="alert"/.test(modal));
ok("modal não lê r.cenarios", !/\.cenarios/.test(modal));
ok("título do modal vem do vocabulário (modal_titulo)", /"modal_titulo"/.test(modal));
ok("applyStopAlvoFor não fecha o modal em erro (onRecusa)", /applyStopAlvoFor: async \(t, stop, alvo, onRecusa\)/.test(app));

// ---- Task 2: toggle, card inválido, rótulos de R:R -------------------------
ok("toggle de gestão no modal (gestao_toggle, gestaoAuto !== false)", /"gestao_toggle"/.test(modal) && /gestaoAuto !== false/.test(modal));
ok("toggle com alvo de toque de 44px", /minHeight: 44[^}]*alignItems: "flex-start"/.test(modal));
ok("rótulo R:R do plano (rr_plano)", /"rr_plano"/.test(app));
ok("rótulo R:R restante (rr_atual) no AtivoCard", /"rr_atual"/.test(app));
ok("compra mostra marcosTexto do servidor", /marcosTexto/.test(app));
ok("estruturaCard: estado_plano_invalido", /estado_plano_invalido/.test(estrutura));

// ---- Task 3: bloco do plano e régua sobre o motor (D-18) -------------------
ok("App.jsx sem alvoSugerido", !/alvoSugerido/.test(app));
ok("App.jsx sem 'ALVO 2:1'", !/ALVO 2:1/.test(app));
ok("App.jsx sem 'Alvo 1 (parcial'", !/Alvo 1 \(parcial/.test(app));
ok("bloco do plano usa bloco_stop/bloco_alvo/bloco_breakeven/bloco_rr", ["bloco_stop", "bloco_alvo", "bloco_breakeven", "bloco_rr"].every((k) => app.includes('"' + k + '"')));
ok("régua usa regua_alvo", /"regua_alvo"/.test(app));


if (fails) { console.error("\n" + fails + " falha(s)"); process.exit(1); }
console.log("\ntodos os testes passaram");
