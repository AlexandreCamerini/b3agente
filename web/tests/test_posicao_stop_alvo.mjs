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

// Fase 46 (46-06, 2026-10-01): o bloco `{editFor === p.t && (...)}` de dentro de
// CarteiraScreen virou o componente EditorStopAlvo (herdado, mesmo contrato). Os
// dois campos agora saem de UM helper `campo(chave, rotulo, valor, set)`; as
// asserções abaixo são as mesmas de antes, ancoradas no helper + nas duas
// chamadas (stop->A.setStop, alvo->A.setAlvo). Nada afrouxado.
const ini = app.indexOf("function EditorStopAlvo(");
const fim = ini < 0 ? -1 : app.indexOf("\nfunction ", ini + 10);
const bloco = ini < 0 ? "" : app.slice(ini, fim > ini ? fim : undefined);
ok("achei o componente EditorStopAlvo (herdeiro do bloco editFor === p.t)", !!bloco);
ok("o card monta o editor só quando a edição está aberta", /\{editAberto && <EditorStopAlvo p=\{p\} ctx=\{ctx\} \/>\}/.test(app));

ok("os dois campos usam o helper com A.setStop / A.setAlvo e o valor do servidor",
   /campo\("stop", "Stop", p\.stop, A\.setStop\)/.test(bloco) && /campo\("alvo", "Alvo", p\.alvo, A\.setAlvo\)/.test(bloco));

ok("blur com campo VAZIO não chama set (A.setStop/A.setAlvo) — não apaga sozinho",
   /onBlur=\{\(ev\) => \{ const v = ev\.target\.value; if \(v\.trim\(\) !== ""\) set\(p\.t, v\); \}\}/.test(bloco));
ok("nenhum blur chama set sem a guarda de vazio", (bloco.match(/onBlur=/g) || []).length === 1);

ok("limpar é ação explícita (botão ✕), só quando há valor pra limpar (stop e alvo)",
   /\{valor != null && \(\s*\n\s*<button type="button" onClick=\{\(\) => set\(p\.t, ""\)\}/.test(bloco) && />✕</.test(bloco));

ok("os inputs de stop/alvo têm key ligada ao valor do servidor (remonta e reflete limpeza/IA)",
   /key=\{chave \+ "-" \+ p\.t \+ "-" \+ \(valor \?\? "vazio"\)\}/.test(bloco));

ok("o texto de ajuda já não promete que sair vazio apaga — avisa do jeito certo",
   /deixar vazio não apaga; use ✕ para limpar/.test(bloco));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
