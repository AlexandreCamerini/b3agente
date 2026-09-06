// Fase 3, Task 2 (C-19/REPORT-01, D-02 revisado em 03-CONTEXT.md): card de
// status único no topo de "Operador IA", ANTES de qualquer controle,
// resumindo os 3 interruptores que decidem se uma ordem dispara — Modo do
// app, Operador no servidor, Executar/sinalizar.
//
// REVERSÃO DELIBERADA (2026-09-05, Fase 21 do milestone v1.5, DEDUP-02):
// o card acima foi REMOVIDO de AgenteScreen. Ele era read-only e repetia,
// em texto puro, os três fatos que o card-herói funcional "OPERADOR NO
// SERVIDOR" logo abaixo já mostra de forma acionável (com o toggle real de
// ligar/desligar o agente no servidor e os dois botões Executar/Apenas
// sinalizar). A decisão foi reavaliada e considerada redundância pura, não
// informação nova.
//
// Nenhuma informação SUMIU da tela ao remover o card:
// - "Modo do app" (Estudo/Operador) segue visível em TODA tela pelo chip do
//   Topbar (`App.jsx`, `modeChip={cp.chipModo}`), fora do switch de rotas —
//   não é exclusivo de AgenteScreen, é global.
// - "Operador no servidor" (ligado/desligado) e "Executar/sinalizar" seguem
//   no card-herói "OPERADOR NO SERVIDOR", que os mostra com o toggle real.
// - O link "Trocar modo →" foi relocado para logo abaixo do parágrafo de
//   introdução da tela (mesmo texto, mesmo handler `A.go("perfil")`, mesma
//   cor `T.accent`) — a navegação para o Perfil não foi perdida.
// - As duas linhas de transparência do ADR-017 Bloco 4
//   (`ctx.cp.entradaAuto.regra` / `.contraste`) foram relocadas para dentro
//   do card "ENTRADA AUTOMÁTICA", o único card da tela que trata de entrada
//   automática — lar tematicamente correto.
//
// Este guardião NÃO foi apagado. Por instrução do CLAUDE.md ("Guardiões de
// teste não se apagam — reversão deliberada atualiza o guardião com
// nota."), ele foi REESCRITO para travar o ESTADO NOVO: a não-regressão do
// card removido (ele não pode voltar) e a sobrevivência do que não era
// redundante (o link e a transparência).
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
// e test_agente_modo_estudo_ui.mjs) — se a função sumir, aborta, nunca passa
// em silêncio por marcador ausente.
const inicioScreen = app.indexOf("function AgenteScreen(");
if (inicioScreen < 0) { console.error("FALHOU: função AgenteScreen não encontrada em App.jsx"); process.exit(1); }
const fimScreen = app.indexOf("\nfunction ", inicioScreen + 10);
const screen = app.slice(inicioScreen, fimScreen > inicioScreen ? fimScreen : undefined);

// (1) Não-regressão: o marcador do card removido não pode voltar.
ok('(1) "C-19 (REPORT-01)" NÃO existe mais em AgenteScreen (o card não volta)',
   !screen.includes("C-19 (REPORT-01)"));

// (2) A tira de status "Modo do app:" não existe mais.
ok('(2) "Modo do app:" aparece 0× em AgenteScreen',
   (screen.match(/Modo do app:/g) || []).length === 0);

// (3) A tira de status "Executar/sinalizar:" não existe mais.
ok('(3) "Executar/sinalizar:" aparece 0× em AgenteScreen',
   (screen.match(/Executar\/sinalizar:/g) || []).length === 0);

// (4) O card-herói segue lá e segue mostrando os dois fatos acionáveis.
const idxHeroi = screen.indexOf("OPERADOR NO SERVIDOR");
const heroiAte = idxHeroi >= 0 ? screen.slice(idxHeroi, idxHeroi + 2000) : "";
ok('(4) o card-herói OPERADOR NO SERVIDOR segue presente, com "ATIVO"/"INATIVO" e modoEfetivo === "executar"',
   idxHeroi >= 0 && /ATIVO/.test(heroiAte) && /INATIVO/.test(heroiAte) && /modoEfetivo === "executar"/.test(heroiAte));

// (5) O modo do app segue visível GLOBALMENTE (não em AgenteScreen — no chip
// do Topbar, fora do switch de rotas). Varre o ARQUIVO INTEIRO.
ok('(5) o modo do app segue visível globalmente: `modeChip={cp.chipModo}` existe em App.jsx (Topbar)',
   app.includes("modeChip={cp.chipModo}"));

// (6) O link "Trocar modo →" sobreviveu — mesmo texto, mesmo handler, na
// mesma vizinhança (não precisa ser adjacente byte a byte, só estar no
// mesmo card/bloco).
const trocarHits = (screen.match(/Trocar modo →/g) || []).length;
const idxTrocar = screen.indexOf("Trocar modo →");
const vizinhanca = idxTrocar >= 0 ? screen.slice(Math.max(0, idxTrocar - 400), idxTrocar + 100) : "";
ok('(6) "Trocar modo →" aparece exatamente 1× em AgenteScreen, com onClick={() => A.go("perfil")} na mesma vizinhança',
   trocarHits === 1 && /onClick=\{\(\) => A\.go\("perfil"\)\}/.test(vizinhanca));

// (7) O link relocado está ANTES do card-herói (continua visível sem rolar).
ok("(7) o link está ANTES do card-herói (índice de \"Trocar modo →\" menor que o de \"OPERADOR NO SERVIDOR\")",
   idxTrocar >= 0 && idxHeroi >= 0 && idxTrocar < idxHeroi);

// (8) A transparência do ADR-017 Bloco 4 sobreviveu — relocada, não apagada.
const regraHits = (screen.match(/cp\.entradaAuto\.regra/g) || []).length;
const contrasteHits = (screen.match(/cp\.entradaAuto\.contraste/g) || []).length;
ok("(8) cp.entradaAuto.regra e cp.entradaAuto.contraste aparecem exatamente 1× cada em AgenteScreen",
   regraHits === 1 && contrasteHits === 1);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
