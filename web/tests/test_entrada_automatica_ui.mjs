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

// ---------------------------------------------------- FIX-C23 (2026-08-23) ----
// O toggle mestre "Entrada automática" era o único dos 3 controles gateados
// desta tela (Executar, allocPct, toggle) sem atributo HTML `disabled` real —
// teclado e leitor de tela anunciavam um controle operável que não fazia
// nada. Esta seção trava: (a) o componente Toggle aceita e aplica `disabled`
// de verdade no <button>; (b) o call site de "Entrar automaticamente" passa
// `disabled={!operador}`; (c) o guard `operador &&` do onClick continua
// existindo (defesa em profundidade, o UI-SPEC pede que não seja removido);
// (d) o esmaecimento usa os MESMOS valores numéricos dos irmãos já corretos
// (opacity 0.6 / cursor not-allowed), nunca mudança de cor.
const idxToggleFn = app.indexOf("function Toggle(");
ok("componente Toggle existe em App.jsx", idxToggleFn >= 0);
const fimToggleAprox = app.indexOf("\nfunction ", idxToggleFn + 10);
const toggleFn = app.slice(idxToggleFn, fimToggleAprox > idxToggleFn ? fimToggleAprox : undefined);

ok("a assinatura de Toggle inclui `disabled`",
   /function Toggle\(\{ on, onClick, label, disabled \}\)/.test(toggleFn));
ok("o <button> do Toggle carrega `disabled={disabled}` (atributo HTML real)",
   /<button[^>]*\bdisabled=\{disabled\}/.test(toggleFn));
ok("o Toggle aplica `opacity: disabled ? 0.6 : 1`",
   /opacity:\s*disabled\s*\?\s*0\.6\s*:\s*1/.test(toggleFn));
ok("o Toggle aplica `cursor: disabled ? \"not-allowed\" : \"pointer\"`",
   /cursor:\s*disabled\s*\?\s*"not-allowed"\s*:\s*"pointer"/.test(toggleFn));
// A linha `const s = {...}` é a ÚNICA fonte de bg/border/knob/color — precisa
// seguir 100% baseada em `on`, sem `disabled` aparecer nela (zero regressão
// de cor: o item 6 do contrato do UI-SPEC exige que o visual "off" de hoje
// não mude, só fique esmaecido por opacidade).
const linhaS = (toggleFn.match(/const s = \{[^}]*\};/) || [""])[0];
ok("a linha `const s = {...}` (bg/border/knob/color) existe e é só baseada em `on`", linhaS.length > 0);
ok("o Toggle NÃO referencia `disabled` na linha de cor (esmaecimento é só por opacidade, nunca por cor)",
   linhaS.length > 0 && !/disabled/.test(linhaS));

ok("o call site de \"Entrar automaticamente\" carrega `disabled={!operador}`",
   /<Toggle on=\{!!ag\.entradaAuto && operador\} disabled=\{!operador\}/.test(screen));
ok("o call site mantém o guard `operador &&` no onClick mesmo com `disabled` presente",
   /disabled=\{!operador\} onClick=\{\(\) => operador && putAg\(\{ entradaAuto: !ag\.entradaAuto \}\)\}/.test(screen));
ok("o parágrafo explicativo existente segue no fonte (nenhuma cópia nova trocou o texto)",
   /Disponível no Modo Operador — em Modo Estudo a entrada continua só por aviso/.test(screen));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
