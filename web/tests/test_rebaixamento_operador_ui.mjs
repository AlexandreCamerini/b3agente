// Quick 261014-upj (2026-10-14) — aviso de rebaixamento do Operador.
//
// Sair do Modo Operador desliga execução no stop/alvo e entrada automática; a
// volta NÃO religa (decisão travada no servidor). O aviso na tela do Operador
// IA é o que impede o rebaixamento de ser silencioso: condicionado a
// `operador` + marcador do SERVIDOR (`srv.meuRebaixamento`, de
// /api/agent/status), com atalho que grava `mode:"executar"` e copy vindo de
// COPY (nunca literal no App.jsx).
//
// Guardião estático (padrão de test_entrada_automatica_ui.mjs): texto-fonte,
// sem build nem DOM. Roda: `node web/tests/test_rebaixamento_operador_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const inicio = app.indexOf("function AgenteScreen(");
ok("AgenteScreen existe em App.jsx", inicio >= 0);
const fimAprox = app.indexOf("\nfunction ", inicio + 10);
const screen = app.slice(inicio, fimAprox > inicio ? fimAprox : undefined);

// ------------------------------------------------------------ condição do aviso
ok("o marcador vem do SERVIDOR e só em Operador com conta",
   /const reb = operador && logged && srv \? srv\.meuRebaixamento : null;/.test(screen));
ok("a parte da execução só aparece enquanto o servidor ainda está em sinalizar",
   /const rebExec = !!\(reb && reb\.execucao && srv\.meuModo === "sinalizar"\);/.test(screen));
ok("a parte da entrada só aparece enquanto a entrada segue desligada no servidor",
   /const rebEntrada = !!\(reb && reb\.entradaAuto && !srv\.minhaEntradaAuto\);/.test(screen));
ok("o bloco do aviso é condicionado a rebExec || rebEntrada",
   /\{\(rebExec \|\| rebEntrada\) && \(\s*<div role="status" data-testid="aviso-rebaixamento-operador"/.test(screen));

// ------------------------------------------------------------------- atalhos
const ini = screen.indexOf('data-testid="aviso-rebaixamento-operador"');
const aviso = screen.slice(ini, screen.indexOf("{/* qa/34: REGRAS & LIMITES", ini));
ok("atalho \"Religar Executar\" grava mode executar (via escolherModo)",
   /onClick=\{\(\) => escolherModo\("executar"\)\}[\s\S]*?\{cpReb\.botao_religar\}/.test(aviso));
ok("botão secundário mantém sinalizar (escolha explícita limpa o marcador)",
   /onClick=\{\(\) => escolherModo\("sinalizar"\)\}[\s\S]*?\{cpReb\.botao_manter\}/.test(aviso));
ok("só-entrada: botão de ciência grava entradaAuto:false",
   /\{!rebExec && rebEntrada && \(\s*<button onClick=\{cienteEntrada\}/.test(aviso) &&
   /const cienteEntrada = async \(\) => \{\s*try \{ await putAg\(\{ entradaAuto: false \}\); \}/.test(screen));
ok("escolherModo grava e RELÊ o servidor (sem voltar ao estado antigo até o poll)",
   /const escolherModo = async \(m\) => \{\s*try \{ await putAg\(\{ mode: m \}\); \}[\s\S]*?finally \{ loadSrv\(\); \}/.test(screen));
ok("os botões de modo do card-herói usam escolherModo",
   /onClick=\{\(\) => !desabilitado && escolherModo\(m\)\}/.test(screen));
ok("alvos de toque dos botões do aviso ≥ 44px", (aviso.match(/minHeight: "44px"/g) || []).length >= 3);

// ----------------------------------------------------------------------- copy
ok("copy do aviso vem de copyFor(\"operador\").rebaixamentoOperador",
   /const cpReb = copyFor\("operador"\)\.rebaixamentoOperador;/.test(screen));
for (const modo of ["estudo", "operador"]) {
  const c = COPY[modo].rebaixamentoOperador;
  ok(`COPY.${modo}.rebaixamentoOperador existe`, !!c);
  for (const k of ["aviso_titulo", "aviso_execucao", "aviso_entrada", "botao_religar", "botao_manter", "botao_ciente"]) {
    ok(`COPY.${modo}.rebaixamentoOperador.${k} preenchido e não hardcoded no App.jsx`,
       !!(c && c[k]) && !app.includes(c[k]));
  }
}

// ---------------------------------------------- modo exibido = verdade do servidor
ok("modo exibido prefere srv.meuModo com conta (iPhone não relê doc.agent)",
   /const modoServidor = logged && srv && \(srv\.meuModo === "executar" \|\| srv\.meuModo === "sinalizar"\) \? srv\.meuModo : null;/.test(screen));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
