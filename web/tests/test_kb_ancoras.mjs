// Fase 38 (38-05, KB-02) — Guardião estático dos 4 links "saiba mais" fixos
// (D-07/D-08): ANCORAS_KB com as 4 chaves, cada link na tela certa, guardado
// por didatica.ligada + verbeteDoCatalogo, nunca poluindo gestoUso/
// coach_tip_* (T-38-21), e o isolamento de Opções (T-38-18) — nenhum import
// de App.jsx, ConceitoSheet local vinda de entendimento.jsx com fonte="kb".
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { ANCORAS_KB } from "../src/glossario.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const opcoes = readFileSync(join(here, "..", "src", "opcoes", "OpcoesScreen.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- (a) ANCORAS_KB tem exatamente as 4 chaves das abas --------------------
ok("ANCORAS_KB tem exatamente as 4 chaves esperadas",
  Object.keys(ANCORAS_KB).sort().join(",") === ["evolucao", "mercado", "opcoes", "radar"].join(","));
ok("todos os 4 valores de ANCORAS_KB são strings não vazias",
  Object.values(ANCORAS_KB).every((v) => typeof v === "string" && v.length > 0));

// ---- (b) fatia cada tela por marcador de linha (mesmo padrão de -----------
//          test_fase22_componentes_compartilhados.mjs / test_opcoes_subabas_ui.mjs)
function fatiarFuncaoTopo(src, nomeFuncao) {
  const ini = src.indexOf("function " + nomeFuncao + "(");
  if (ini === -1) return "";
  const fim = src.indexOf("\nfunction ", ini + 1);
  return fim > ini ? src.slice(ini, fim) : src.slice(ini);
}

const fatiaEvolucao = fatiarFuncaoTopo(app, "EvolucaoScreen");
const fatiaMercado = fatiarFuncaoTopo(app, "MercadoScreen");
const fatiaRadar = fatiarFuncaoTopo(app, "RadarScreen");

ok("EvolucaoScreen foi localizada e tem corpo (>500 caracteres)", fatiaEvolucao.length > 500);
ok("MercadoScreen foi localizada e tem corpo (>500 caracteres)", fatiaMercado.length > 500);
ok("RadarScreen foi localizada e tem corpo (>500 caracteres)", fatiaRadar.length > 500);

// ---- (c) cada tela chama abrirVerbeteKb(ANCORAS_KB.<aba certa>) -----------
ok("EvolucaoScreen chama A.abrirVerbeteKb(ANCORAS_KB.evolucao)",
  /abrirVerbeteKb\(ANCORAS_KB\.evolucao\)/.test(fatiaEvolucao));
ok("MercadoScreen chama A.abrirVerbeteKb(ANCORAS_KB.mercado)",
  /abrirVerbeteKb\(ANCORAS_KB\.mercado\)/.test(fatiaMercado));
ok("RadarScreen chama ctx.A.abrirVerbeteKb(ANCORAS_KB.radar)",
  /abrirVerbeteKb\(ANCORAS_KB\.radar\)/.test(fatiaRadar));

// ---- (d) cada link é guardado por didatica.ligada + verbeteDoCatalogo( ----
for (const [nome, fatia] of [["EvolucaoScreen", fatiaEvolucao], ["MercadoScreen", fatiaMercado], ["RadarScreen", fatiaRadar]]) {
  ok(`${nome}: link guardado por ctx.didatica.ligada`, /ctx\.didatica && ctx\.didatica\.ligada/.test(fatia));
  ok(`${nome}: link guardado por verbeteDoCatalogo(`, /verbeteDoCatalogo\(ctx\.kbCatalogo,\s*ANCORAS_KB\./.test(fatia));
}

// ---- (e) nenhum dos 4 links usa abrirSetor/openConceito/abrirVerbete( antigo (T-38-21) ----
function blocoDoLink(src, marcador) {
  const ini = src.indexOf(marcador);
  if (ini === -1) return "";
  // Janela fixa em volta do marcador: a linha do JSX condicional tem `)}`
  // no PRÓPRIO onClick (`abrirVerbeteKb(ANCORAS_KB.evolucao)}`), então
  // buscar o primeiro `)}` a partir daqui cortaria antes do `style={{...}}`
  // — janela de tamanho fixo evita esse falso corte.
  return src.slice(Math.max(0, ini - 200), ini + 500);
}
const blocoEvolucao = blocoDoLink(fatiaEvolucao, "ANCORAS_KB.evolucao) && (");
const blocoMercado = blocoDoLink(fatiaMercado, "ANCORAS_KB.mercado) && (");
const blocoRadar = blocoDoLink(fatiaRadar, "ANCORAS_KB.radar) && (");
const blocoOpcoes = (() => {
  const ini = opcoes.indexOf("ANCORAS_KB.opcoes) && (");
  return ini === -1 ? "" : opcoes.slice(Math.max(0, ini - 300), ini + 600);
})();

for (const [nome, bloco] of [["EvolucaoScreen", blocoEvolucao], ["MercadoScreen", blocoMercado], ["RadarScreen", blocoRadar], ["OpcoesScreen", blocoOpcoes]]) {
  ok(`${nome}: bloco do link foi localizado (>50 caracteres)`, bloco.length > 50);
  ok(`${nome}: link não usa abrirSetor`, !/abrirSetor/.test(bloco));
  ok(`${nome}: link não usa openConceito`, !/openConceito/.test(bloco));
  ok(`${nome}: link não usa A.abrirVerbete( antigo (só abrirVerbeteKb/estado local)`, !/A\.abrirVerbete\(/.test(bloco));
}

// ---- (f) estilo do link idêntico ao precedente nas 4 ocorrências ----------
for (const [nome, bloco] of [["EvolucaoScreen", blocoEvolucao], ["MercadoScreen", blocoMercado], ["RadarScreen", blocoRadar], ["OpcoesScreen", blocoOpcoes]]) {
  ok(`${nome}: estilo do link usa color: T.accent, fontWeight: 700, fontSize: "12px"`,
    /color:\s*T\.accent/.test(bloco) && /fontWeight:\s*700/.test(bloco) && /fontSize:\s*"12px"/.test(bloco));
}

// ---- (g) isolamento de OpcoesScreen.jsx (T-38-18) --------------------------
ok("OpcoesScreen.jsx NÃO importa App.jsx", !/from\s+["'][^"']*App\.jsx["']/.test(opcoes));
ok("OpcoesScreen.jsx importa ../entendimento.jsx", /from\s+["']\.\.\/entendimento\.jsx["']/.test(opcoes));
ok("OpcoesScreen.jsx importa ../glossario.js", /from\s+["']\.\.\/glossario\.js["']/.test(opcoes));
ok("OpcoesScreen.jsx importa ConceitoSheet nomeada (não default)", /import\s*\{\s*ConceitoSheet\s*\}\s*from\s*["']\.\.\/entendimento\.jsx["']/.test(opcoes));

// ---- (h) monta <ConceitoSheet com fonte="kb" e kbCatalogo={ctx.kbCatalogo} ----
ok("OpcoesScreen.jsx monta <ConceitoSheet", /<ConceitoSheet/.test(opcoes));
ok('OpcoesScreen.jsx passa fonte="kb" para a ConceitoSheet local',
  (() => {
    const ini = opcoes.indexOf("<ConceitoSheet");
    const fimTag = opcoes.indexOf("/>", ini);
    const tag = fimTag > ini ? opcoes.slice(ini, fimTag) : "";
    return /fonte="kb"/.test(tag) && /kbCatalogo=\{ctx/.test(tag);
  })());

// ---- (i) chip de liquidez (overlay global) continua intocado (T-38-19 vizinho) ----
ok('OpcoesScreen.jsx continua chamando A.abrirVerbete("liquidez-opcao", ...)',
  /abrirVerbete\("liquidez-opcao"/.test(opcoes));

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DE ANCORAS_KB PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
