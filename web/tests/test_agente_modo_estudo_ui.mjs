// Fase A do plano (docs/plano-operador-entrada-e-modos.md) — trava
// estrutural do lado da UI: o botão "Executar" (AgenteScreen) não pode
// OFERECER o que o backend (agent.agent_params/store.set_agent) já recusa.
//
// Guardião estático (padrão de test_pet_ui.mjs): confere no texto-fonte de
// App.jsx que o botão tem uma condição de `disabled` ligada a
// `appMode !== "operador"` e que existe um texto explicativo condicional.
//
// Roda sem build: `node web/tests/test_agente_modo_estudo_ui.mjs`.
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

// -------------------------------------------------------- appMode/operador
// qa/audit-2026-08-07 (item 5): fonte única — `ctx.operador` é computado UMA
// vez (junto do resto de `ctx`), não mais redevirado dentro de cada tela.
ok("AgenteScreen lê `operador` de ctx (fonte única, não redevira de data.config)",
   /const \{ operador \} = ctx;/.test(screen));
// FIX-C21 (2026-08-23): a própria montagem de `ctx` deixou de recomputar de
// data.config.appMode — agora deriva da variável local `appMode` (que já
// tem o guard pra data=null no boot, linha 6836 do App.jsx). Assert
// atualizado para a expressão nova; a garantia (ctx expõe `operador`
// corretamente, mesmo no boot) continua a mesma.
ok("ctx expõe `operador` derivado de `appMode` (fonte única, guard pra data=null herdado da derivação local)",
   /operador: appMode === "operador",/.test(app));

// --------------------------------------------------- botão "Executar" preso
ok("o botão \"Executar\" tem uma condição de disabled ligada a appMode !== operador",
   /const desabilitado = m === "executar" && !operador;/.test(screen)
   && /disabled=\{desabilitado\}/.test(screen));
ok("o botão desabilitado não dispara putAg (clique não manda mode=executar em Modo Estudo)",
   /onClick=\{\(\) => !desabilitado && putAg\(\{ mode: m \}\)\}/.test(screen));

// ------------------------------------------------------------ texto explica
ok("existe texto explicando por que \"Executar\" está indisponível fora do Operador",
   /Disponível no Modo Operador — em Modo Estudo o agente só orienta/.test(screen));
ok("o texto explicativo só aparece condicionalmente (!operador), não sempre",
   /\{!operador && \(/.test(screen));
// FIX-C18 (2026-09-06): leitor de tela que navega por botões pulava direto
// pro <button disabled>, sem ouvir o parágrafo de explicação logo abaixo —
// faltava o vínculo semântico aria-describedby -> id. Estas duas asserções
// travam o vínculo nos dois lados (o id no <p>, o ternário no <button>).
ok("o parágrafo de explicação carrega id=\"executar-gate-hint\" (alvo do aria-describedby)",
   /id="executar-gate-hint"/.test(screen));
ok("o botão \"Executar\" aponta aria-describedby para o hint só quando desabilitado (ternário, não atributo solto)",
   /aria-describedby=\{desabilitado \? "executar-gate-hint" : undefined\}/.test(screen));

// --------------------------------------------------- estado defensivo (UI)
ok("o modo exibido (header · badge) cai para \"sinalizar\" fora do Operador, mesmo com mode=\"executar\" salvo",
   /const modoEfetivo = operador \? \(ag\.mode \|\| \(ag\.autonomous \? "executar" : "sinalizar"\)\) : "sinalizar";/.test(screen));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
