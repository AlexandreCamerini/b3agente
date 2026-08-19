// Fase 3, Task 2 (C-19/REPORT-01, D-02 revisado em 03-CONTEXT.md): card de
// status único no topo de "Operador IA", ANTES de qualquer controle,
// resumindo os 3 interruptores que decidem se uma ordem dispara — Modo do
// app, Operador no servidor, Executar/sinalizar. Guardião estático (regex
// sobre App.jsx, padrão da casa — o módulo importa @capacitor/core e não é
// importável fora do build).
//
// Roda sem build: `node web/tests/test_fase3_c19_card_status.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Isola o corpo de AgenteScreen (mesmo padrão de test_auditoria_status_strip.mjs
// e test_agente_modo_estudo_ui.mjs).
const inicioScreen = app.indexOf("function AgenteScreen(");
if (inicioScreen < 0) { console.error("FALHOU: função AgenteScreen não encontrada em App.jsx"); process.exit(1); }
const fimScreen = app.indexOf("\nfunction ", inicioScreen + 10);
const screen = app.slice(inicioScreen, fimScreen > inicioScreen ? fimScreen : undefined);

// Isola "o bloco do card": do comentário-âncora (marcador estável, único
// nesta tela) até o wrapper do <h1>Operador IA</h1> — se qualquer marcador
// sumir (refatoração futura), o guardião GRITA em vez de virar no-op.
const inicioCard = screen.indexOf("C-19 (REPORT-01)");
const fimCard = screen.indexOf('<div style={{ display: "flex", alignItems: "center", gap: "2px"');
if (inicioCard < 0) { console.error('FALHOU: marcador de início do card ("C-19 (REPORT-01)") não encontrado em AgenteScreen'); process.exit(1); }
if (fimCard < 0 || fimCard <= inicioCard) { console.error("FALHOU: marcador de fim do card (wrapper do <h1>) não encontrado após o início do card"); process.exit(1); }
const bloco = screen.slice(inicioCard, fimCard);

// (a) o card existe e vem ANTES do <h1> "Operador IA" e antes de "OPERADOR NO SERVIDOR"
const idxH1 = screen.indexOf("Operador IA</h1>");
const idxHeroi = screen.indexOf("OPERADOR NO SERVIDOR");
ok("(a) o card existe e vem ANTES do <h1>Operador IA</h1> e antes do card-herói OPERADOR NO SERVIDOR",
   inicioCard >= 0 && inicioCard < idxH1 && inicioCard < idxHeroi);

// (b) os 3 rótulos aparecem no bloco do card
ok('(b) os 3 rótulos aparecem no bloco: "Modo do app", "Operador no servidor", "Executar/sinalizar"',
   bloco.includes("Modo do app:") && bloco.includes("Operador no servidor:") && bloco.includes("Executar/sinalizar:"));

// (c) cada badge lê a fonte canônica (mesmas variáveis já derivadas no topo
// de AgenteScreen, nunca um valor cru/re-derivado)
ok('(c) badge 1 lê `operador` com a expressão literal existente ({operador ? "📈 Operador" : "🎓 Estudo"})',
   /\{operador \? "📈 Operador" : "🎓 Estudo"\}/.test(bloco));
ok("(c) badge 2 lê `ag.serverEnabled && logged` (mesma guarda do card-herói, não serverEnabled cru)",
   /\(ag\.serverEnabled && logged\)/.test(bloco));
ok('(c) badge 3 lê `modoEfetivo === "executar"` (nunca ag.mode cru)',
   /modoEfetivo === "executar"/.test(bloco));

// (d) não lê data.config.appMode — convenção "novo código lê ctx.operador"
ok("(d) o bloco do card NÃO contém `config.appMode` (novo código lê ctx.operador)",
   !bloco.includes("config.appMode"));

// (e) read-only: sem putAg(, setServer( nem <Toggle; único onClick é A.go("perfil")
const onClicks = bloco.match(/onClick=/g) || [];
ok("(e) read-only: nenhum putAg( / setServer( / <Toggle dentro do bloco do card",
   !/putAg\(/.test(bloco) && !/setServer\(/.test(bloco) && !/<Toggle/.test(bloco));
ok('(e) o único onClick do bloco chama A.go("perfil")',
   onClicks.length === 1 && /onClick=\{\(\) => A\.go\("perfil"\)\}/.test(bloco));

// (f) sem accent nos badges — T.accent aparece no máximo 1x no bloco (o link)
const accentHits = (bloco.match(/T\.accent\b/g) || []).length;
ok("(f) T.accent aparece no máximo 1× no bloco do card (reservado ao link \"Trocar modo →\")",
   accentHits <= 1);

// (g) tira única — "Modo do app:" aparece exatamente 1x no corpo de AgenteScreen
// (impede reintroduzir a tira antiga em paralelo ao card novo)
const modoDoAppHits = (screen.match(/Modo do app:/g) || []).length;
ok('(g) "Modo do app:" aparece exatamente 1× no corpo de AgenteScreen (card único, sem tira duplicada)',
   modoDoAppHits === 1);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
