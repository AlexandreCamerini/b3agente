// Auditoria 2026-08-07 (docs/auditoria-controle-ordens-parametros.md) — o
// Alex reportou "não me deixa mais selecionar o modo executar": o botão
// estava corretamente travado (Modo Estudo), mas a ÚNICA explicação era um
// `title` HTML — invisível em toque (WKWebView não tem hover). E o portão de
// verdade (`appMode`, em Perfil → Modo de trabalho) não tinha link nenhum
// a partir de onde o usuário via a trava.
//
// Este guardião trava dois contratos:
//  1. Os dois pontos que explicam a trava (Executar/sinalizar, Entrada
//     automática) têm um LINK visível pra Perfil — não só texto mudo.
//  2. Toda troca de Modo de trabalho REINICIA o app (reload completo) — não
//     só navega — porque `appMode` é lido de forma independente em mais de
//     10 lugares do código; só um reload garante que todos vejam o modo novo.
//
// Roda sem build: `node web/tests/test_auditoria_modo_link_restart.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- item 1: link visível nos dois pontos que hoje só tinham texto mudo ----
const linksModoOperador = (app.match(/Trocar para Modo Operador →/g) || []).length;
ok("existem os DOIS links \"Trocar para Modo Operador →\" (Executar/sinalizar + Entrada automática)",
   linksModoOperador === 2);
ok("o link chama A.go(\"perfil\") — mesma tela do card Modo de trabalho (+ a tira de status sempre visível, item 3 da auditoria)",
   (app.match(/onClick=\{\(\) => A\.go\("perfil"\)\}/g) || []).length === 3);

// ---- item 2: `title` não é mais a explicação do botão Executar/sinalizar ---
const blocoBotoes = app.slice(app.indexOf('{["executar", "sinalizar"].map'), app.indexOf('{["executar", "sinalizar"].map') + 900);
ok("o botão Executar/sinalizar NÃO depende mais de `title` (invisível em toque)",
   !/title=\{desabilitado \? "Disponível no Modo Operador/.test(blocoBotoes));

// ---- restart completo ao trocar de Modo de trabalho -----------------------
// qa/audit-2026-08-08: janela alargada de 900 -> 1400 — a função ganhou um
// try/catch (sync de appMode com o servidor pode falhar por rede) sem
// mudar o contrato que este guardião prova.
const escolher = app.slice(app.indexOf("const escolher = async (m) =>"), app.indexOf("const escolher = async (m) =>") + 1400);
ok("escolher() localizado", escolher.includes("saveConfig"));
ok("escolher() reinicia o app (reload) em vez de só navegar",
   /setTimeout\(\(\) => window\.location\.reload\(\), 700\)/.test(escolher));
ok("escolher() NÃO navega mais via A.go — o reload substitui a navegação",
   !/A\.go\("evolucao"\)/.test(escolher));

const ativar = app.slice(app.indexOf("const ativar = async () =>"), app.indexOf("const ativar = async () =>") + 700);
ok("ativar() (1ª ativação, com termo) localizado", ativar.includes("operadorTermo"));
ok("ativar() TAMBÉM reinicia o app — mesma garantia da outra porta de entrada pro Operador",
   /setTimeout\(\(\) => window\.location\.reload\(\), 700\)/.test(ativar));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
