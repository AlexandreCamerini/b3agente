// STOP/ALVO da posição não pode sumir sozinho. Um `blur` do campo — que pode
// disparar por qualquer interrupção (notificação, troca de app, ligação) sem
// o usuário ter mexido no valor — NÃO PODE apagar a proteção. Limpar de
// propósito agora é uma ação explícita (botão ✕), nunca um efeito colateral
// de sair do campo vazio.
//
// Roda sem build: `node web/tests/test_posicao_stop_alvo.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const m = app.match(/\{editFor === p\.t && \([\s\S]*?Sai do campo para salvar[\s\S]*?\n\s*\)\}/);
const bloco = m ? m[0] : "";
ok("achei o bloco de edição de stop/alvo (editFor === p.t)", !!bloco);

ok("blur com campo VAZIO não chama A.setStop (não apaga sozinho)",
   /onBlur=\{\(e\) => \{ const v = e\.target\.value; if \(v\.trim\(\) !== ""\) A\.setStop\(p\.t, v\); \}\}/.test(bloco));
ok("blur com campo VAZIO não chama A.setAlvo (não apaga sozinho)",
   /onBlur=\{\(e\) => \{ const v = e\.target\.value; if \(v\.trim\(\) !== ""\) A\.setAlvo\(p\.t, v\); \}\}/.test(bloco));

ok("limpar o stop agora é uma ação explícita (botão ✕), só quando há stop pra limpar",
   /\{p\.stop != null && \(\s*\n\s*<button type="button" onClick=\{\(\) => A\.setStop\(p\.t, ""\)\}/.test(bloco));
ok("limpar o alvo agora é uma ação explícita (botão ✕), só quando há alvo pra limpar",
   /\{p\.alvo != null && \(\s*\n\s*<button type="button" onClick=\{\(\) => A\.setAlvo\(p\.t, ""\)\}/.test(bloco));

ok("os inputs de stop/alvo têm key ligada ao valor do servidor (remonta e reflete limpeza/IA)",
   /key=\{"stop-" \+ p\.t \+ "-" \+ \(p\.stop \?\? "vazio"\)\}/.test(bloco)
   && /key=\{"alvo-" \+ p\.t \+ "-" \+ \(p\.alvo \?\? "vazio"\)\}/.test(bloco));

ok("o texto de ajuda já não promete que sair vazio apaga — avisa do jeito certo",
   /deixar vazio não apaga; use ✕ para limpar/.test(bloco));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
