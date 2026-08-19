// Auditoria 2026-08-07, itens 3+4 (docs/auditoria-controle-ordens-parametros.md):
// no topo de "Operador IA", ANTES de qualquer controle, uma linha sempre
// visível mostra o Modo do app (Estudo × Operador) com link direto pra
// trocar — a distinção entre "esta tela configura parâmetros" e "o
// interruptor mestre mora em Perfil" ficava só implícita antes.
//
// Roda sem build: `node web/tests/test_auditoria_status_strip.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const inicio = app.indexOf("function AgenteScreen(");
const fimAprox = app.indexOf("\nfunction ", inicio + 10);
const screen = app.slice(inicio, fimAprox > inicio ? fimAprox : undefined);

ok("a tira \"Modo do app\" existe em AgenteScreen, ANTES do card OPERADOR NO SERVIDOR",
   screen.indexOf("Modo do app:") > 0
   && screen.indexOf("Modo do app:") < screen.indexOf("OPERADOR NO SERVIDOR"));
ok("mostra qual dos dois modos está ativo (Operador × Estudo), não um rótulo fixo",
   /\{operador \? "📈 Operador" : "🎓 Estudo"\}/.test(screen));
// 2026-08-18 (fase 3, C-19/REPORT-01): a tira virou um card de 3 badges
// (Modo do app · Operador no servidor · Executar/sinalizar) — os 2 badges
// novos entre "Modo do app:" e o link empurraram a distância pra ~740
// caracteres. Janela alargada pra 800 preservando a INTENÇÃO da asserção
// (o link pro Perfil continua junto do bloco de status); assinatura não
// muda, nenhuma asserção foi removida.
ok("tem o link direto pra Perfil (mesmo destino do link de dentro dos cards)",
   /Modo do app:[\s\S]{0,800}A\.go\("perfil"\)/.test(screen));
ok("a tira aparece SEMPRE (não só quando desabilitado) — diferente dos avisos condicionais abaixo",
   !/\{!operador && \(\s*\n\s*<div style=\{\{ marginTop: "14px", display: "flex".*Modo do app/.test(screen));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
