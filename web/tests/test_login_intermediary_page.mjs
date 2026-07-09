// qa/32 — Guardião: (1) sessão restaurada com sucesso não deve deixar o
// usuário preso numa página intermediária "Conectado como X + Entrar" no
// boot (WelcomeAuthScreen). (2) o rótulo de e-mail oculto (relay da Apple)
// não deve soar como erro ("... (e-mail oculto)" como TÍTULO) — o rótulo
// neutro "Sua conta Apple" substitui, mantendo a explicação detalhada do
// relay abaixo (que já existia e não muda).
// Roda sem device nem build: `node web/tests/test_login_intermediary_page.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// 1) Boot gate: o bloco que resolve auth.me() com sucesso precisa fechar o
// portão sozinho (sem esperar um toque em "Entrar").
const m = /const r = await auth\.me\(\);[\s\S]*?return \(\) => \{ alive = false; \};/.exec(src);
ok("useEffect de auth.me() localizado em App.jsx", !!m);
const bootBlock = m ? m[0] : "";
ok("boot gate: marca welcomeShownRef.current = true ao restaurar sessão", /welcomeShownRef\.current = true/.test(bootBlock));
ok("boot gate: fecha o portão (setWelcomeAuthOpen(false)) ao restaurar sessão", /setWelcomeAuthOpen\(false\)/.test(bootBlock));

// 2) Nenhum rótulo de TÍTULO deve usar "(e-mail oculto)" — só o texto
// explicativo (que menciona "Ocultar e-mail" como recurso da Apple, não como
// rótulo alarmante) pode falar do relay.
ok("nenhum rótulo usa mais '(e-mail oculto)' como título", !/\(e-mail oculto\)/.test(src));
ok("rótulo neutro 'Sua conta Apple' está presente (mínimo 3x: modal, welcome, drillrow)",
  (src.match(/"Sua conta Apple"/g) || []).length >= 3);

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
