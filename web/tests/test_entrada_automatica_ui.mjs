// Fase C do plano (docs/plano-operador-entrada-e-modos.md) — UI da entrada
// automática: a seção "Entrada automática" só pode OFERECER o que o backend
// (agent.agent_params/store.set_agent, Fase B) já aceita, e o slider
// allocPct (Fase B conectou de verdade) não pode ficar duplicado no card
// "Modo local".
//
// Guardião estático (mesmo padrão de test_agente_modo_estudo_ui.mjs, Fase A):
// confere no texto-fonte de App.jsx, sem build nem DOM.
//
// Roda sem build: `node web/tests/test_entrada_automatica_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Isola o corpo de AgenteScreen para os asserts não vazarem para outra tela.
const inicio = app.indexOf("function AgenteScreen(");
ok("AgenteScreen existe em App.jsx", inicio >= 0);
const fimAprox = app.indexOf("\nfunction ", inicio + 10);
const screen = app.slice(inicio, fimAprox > inicio ? fimAprox : undefined);

// -------------------------------------------------------------- seção existe
ok("existe uma seção \"Entrada automática\" (ENTRADA AUTOMÁTICA) no JSX",
   /ENTRADA AUTOM[ÁA]TICA/.test(screen));

// ------------------------------------------------------- travada fora do Operador
// qa/audit-2026-08-07 (item 5): `operador` agora vem de ctx (fonte única) —
// a seção usa a MESMA variável que o resto de AgenteScreen (é o mesmo escopo
// de função), não uma cópia local.
ok("a seção usa o mesmo `operador` derivado de ctx (fonte única, padrão da Fase A)",
   /const \{ operador \} = ctx;/.test(screen));
ok("o toggle \"Entrar automaticamente\" só liga quando `operador`",
   /<Toggle on=\{!!ag\.entradaAuto && operador\}/.test(screen));
ok("o clique do toggle é guardado por `operador` (não dispara fora do Operador)",
   /onClick=\{\(\) => operador && putAg\(\{ entradaAuto: !ag\.entradaAuto \}\)\}/.test(screen));
ok("o slider allocPct dentro da seção fica desabilitado fora do Operador",
   /<input id="alloc" type="range".*disabled=\{!operador\}/.test(screen));
ok("existe texto explicando que a entrada automática é do Modo Operador (fora dele, só aviso)",
   /Disponível no Modo Operador — em Modo Estudo a entrada continua só por aviso/.test(screen));
ok("o texto explicativo só aparece condicionalmente (!operador), não sempre",
   /\{!operador && \(/.test(screen));

// ----------------------------------------------------------- putAg/entradaAuto
ok("o toggle chama putAg (== A.putAgent) com entradaAuto",
   /putAg\(\{ entradaAuto: !ag\.entradaAuto \}\)/.test(screen));

// --------------------------------------------- allocPct só existe UMA vez, aqui dentro
const idxSecao = screen.indexOf("ENTRADA AUTOMÁTICA");
const idxAlloc = screen.indexOf('id="alloc"');
ok("o slider id=\"alloc\" está DENTRO da seção \"Entrada automática\" (depois do título)",
   idxSecao >= 0 && idxAlloc > idxSecao);
const ocorrenciasAlloc = (screen.match(/id="alloc"/g) || []).length;
ok("o slider id=\"alloc\" não está duplicado em AgenteScreen (só uma ocorrência)",
   ocorrenciasAlloc === 1);
ok("o texto antigo e impreciso do slider (\"Percentual de referência do patrimônio\") não existe mais",
   !/Percentual de referência do patrimônio/.test(app));

// ------------------------------------------------------- trava de segurança (D5)
ok("existe texto sobre a entrada automática só valer para plano de COMPRA (D5 do plano)",
   /entra sozinha em plano de COMPRA/.test(screen));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
