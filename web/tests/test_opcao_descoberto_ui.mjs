// FASE 29 Plano 03 — Guardião: UI do flag de opção a descoberto (D1 fricção,
// D2 fence de escopo).
//
// Contratos trancados:
//  1) Fricção (SC-3): ligar o flag exige TermoDescobertoModal com rolagem até
//     o fim + checkbox + versão visível — mesma máquina do TermoOperadorModal
//     (App.jsx:2317), nunca um toque simples.
//  2) O aceite grava termo + flag no MESMO patch de A.saveConfig — os dois
//     stores (29-01/29-02) recusam ligar sem isso.
//  3) Assimetria ligar/desligar: OpcaoDescobertoCard só chama
//     `permitirOpcaoADescoberto: false` (desligar, livre); ligar SEMPRE passa
//     por `setTermoOpen(true)`, nunca `permitirOpcaoADescoberto: true` direto.
//  4) Fence D2: OpcoesCamada (compra a seco em Watchlist/Radar) não migra;
//     OpcoesScreen.jsx/PropostaLastreada.jsx/agent.py ficam intocados por
//     esta fase.
// Roda sem build: `node web/tests/test_opcao_descoberto_ui.mjs` (de dentro de `web/`).
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..", "..");
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const disc = readFileSync(join(here, "..", "src", "disclaimers.js"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// ---- fatiar por marcador de função, não por número de linha ---------------
function sliceFn(src, startMarker, endMarker) {
  const i = src.indexOf(startMarker);
  if (i < 0) return "";
  const j = src.indexOf(endMarker, i + startMarker.length);
  return j < 0 ? src.slice(i) : src.slice(i, j);
}

const modal = sliceFn(app, "function TermoDescobertoModal", "function ProfileTile");
const card = sliceFn(app, "function OpcaoDescobertoCard", "function ConfigScreen");

// ---- Fricção (SC-3) ---------------------------------------------------------
const descM = disc.match(/descobertoTermo:\s*\n\s*"([^"]+)"/);
ok("DISCLAIMERS.descobertoTermo existe com >= 500 chars", !!descM && descM[1].length >= 500,
  descM ? `len=${descM[1].length}` : "regex não casou");
ok("TERMO_DESCOBERTO_VERSAO exportado de disclaimers.js", disc.includes('export const TERMO_DESCOBERTO_VERSAO = "1.0"'));
ok("TERMO_DESCOBERTO_VERSAO importado em App.jsx", /import \{[^}]*TERMO_DESCOBERTO_VERSAO[^}]*\} from "\.\/disclaimers\.js"/.test(app));
ok("modal encontrado (TermoDescobertoModal existe)", modal.length > 0);
ok("máquina de fricção: liTudo + aceito + botão travado", modal.includes("liTudo") && modal.includes("aceito") && modal.includes("disabled={!liTudo || !aceito || busy}"));
ok("fallback de montagem (bug FASE 8B/P2)", modal.includes("scrollHeight - el.clientHeight"));
ok("onScroll com limiar de 12px", modal.includes("onScroll") && modal.includes("clientHeight < 12"));
ok("subtítulo renderiza a versão do termo", modal.includes("TERMO_DESCOBERTO_VERSAO"));
ok("aceite grava termo + flag no MESMO patch de saveConfig",
  modal.includes('A.saveConfig({ descobertoTermo: { aceitoEm: new Date().toISOString(), versao: TERMO_DESCOBERTO_VERSAO }, permitirOpcaoADescoberto: true }'));
ok("modal NÃO recarrega o app (diferente do Modo Operador, de propósito)", !modal.includes("window.location.reload"));

// ---- Assimetria ligar/desligar ----------------------------------------------
ok("card encontrado (OpcaoDescobertoCard existe)", card.length > 0);
ok("caminho de LIGAR abre o modal (setTermoOpen(true))", card.includes("setTermoOpen(true)"));
ok("caminho de DESLIGAR é direto e livre (permitirOpcaoADescoberto: false)", card.includes("permitirOpcaoADescoberto: false"));
ok("card NUNCA liga o flag fora do modal (sem permitirOpcaoADescoberto: true)", !card.includes("permitirOpcaoADescoberto: true"));
ok("card renderizado exatamente 1x em ConfigScreen", (app.match(/<OpcaoDescobertoCard ctx={ctx} \/>/g) || []).length === 1);

// ---- Fence D2 (SC-5) ---------------------------------------------------------
ok("OpcoesCamada continua existindo (compra a seco não migrou)", app.includes("function OpcoesCamada("));
ok("doBuyOption continua chamando A.buyOption", /doBuyOption[\s\S]{0,200}A\.buyOption/.test(app));

const opcoesScreenPath = join(root, "web", "src", "opcoes", "OpcoesScreen.jsx");
const propostaPath = join(root, "web", "src", "opcoes", "PropostaLastreada.jsx");
const agentPath = join(root, "server", "app", "agent.py");
ok("OpcoesScreen.jsx existe no caminho esperado", existsSync(opcoesScreenPath));
ok("PropostaLastreada.jsx existe no caminho esperado", existsSync(propostaPath));
if (existsSync(opcoesScreenPath) && existsSync(propostaPath)) {
  const opcoesScreen = readFileSync(opcoesScreenPath, "utf8");
  const proposta = readFileSync(propostaPath, "utf8");
  ok("OpcoesScreen.jsx NÃO menciona os campos do flag", !opcoesScreen.includes("permitirOpcaoADescoberto") && !opcoesScreen.includes("descobertoTermo"));
  ok("PropostaLastreada.jsx NÃO menciona os campos do flag", !proposta.includes("permitirOpcaoADescoberto") && !proposta.includes("descobertoTermo"));
}
if (existsSync(agentPath)) {
  const agent = readFileSync(agentPath, "utf8");
  ok("agent.py NÃO menciona permitirOpcaoADescoberto (Operador IA não abre a seco)", !agent.includes("permitirOpcaoADescoberto"));
}

// ---- Acessibilidade -----------------------------------------------------------
ok("Toggle do card recebe label (nome acessível do switch)", /<Toggle on={ligado} onClick={onToggle} label="[^"]+"/.test(card));

console.log(fails ? `\n${fails} TESTE(S) FALHARAM` : "\nTODOS OS TESTES DO GUARDIÃO DE UI DE OPÇÃO A DESCOBERTO PASSARAM");
process.exit(fails ? 1 : 0);
