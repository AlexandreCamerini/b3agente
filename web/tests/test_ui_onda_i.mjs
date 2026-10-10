// Onda I (2026-10-10): as telas de Opções não somam padding lateral próprio ao gutter do container
// (App.jsx GUTTER_X). Antes, a raiz de cada tela tinha `padding: "16px"` e o conteúdo ficava ~28pt da
// borda contra 12pt nas outras abas. Vertical 16 mantido; lateral zero.
import { readFileSync } from "node:fs";
let falhas = 0;
const ok = (nome, cond) => { console.log((cond ? "ok " : "FALHOU ") + nome); if (!cond) falhas++; };
const RAIZES = ["HubOpcoes", "ObjetivoAtivo", "EscadaObjetivo", "ConfirmarEstrutura"];
for (const arq of RAIZES) {
  const src = readFileSync(new URL(`../src/opcoes/${arq}.jsx`, import.meta.url), "utf8");
  const raiz = src.match(/<section[^>]*style=\{\{ padding: "16px[^"]*", display: "flex", flexDirection: "column", gap: "16px"/);
  ok(`${arq}: raiz com padding vertical 16 e lateral 0`, !!raiz && raiz[0].includes('padding: "16px 0"'));
  ok(`${arq}: sem raiz com padding "16px" simétrico`, !/<section[^>]*style=\{\{ padding: "16px", display: "flex"/.test(src));
}
if (falhas) { console.log(`\n${falhas} falha(s)`); process.exit(1); }
console.log("\nTUDO OK");
