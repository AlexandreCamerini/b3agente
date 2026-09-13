// Fase 26, achado A1 (2026-09-12) — A ABA OPÇÕES ERA INVISÍVEL PARA O BORIS.
//
// O defeito, na íntegra: a aba nasceu na Fase 24 (`aba-opcoes F2`) já como 5º
// item do `BottomNav` de `App.jsx`, mas não entrou em NENHUM dos outros dois
// registros de tela que o assistente usa — o `switch (petTela)` do
// `petSnapshot` (caía no `default: return {}`) e a allowlist
// `conceitos.PET_TELAS` do backend (o `/api/assistente` recusava
// `tela: "pet:opcoes"` com 400 "Tela desconhecida." e o
// `/api/pet/resumo?tela=opcoes` caía no fallback de "mercado", devolvendo a
// Watchlist com cara de resposta certa). Nada quebrava, nada logava: o Boris
// só ficava mudo, ou falava da tela errada, na aba mais nova do app.
//
// POR QUE ESTE ARQUIVO EXISTE, E NÃO SÓ UMA LINHA NOVA NO test_pet_ui.mjs:
// acrescentar "opcoes" nas listas escritas à mão conserta ESTA aba e deixa a
// próxima cair no mesmo buraco. O guardião abaixo DERIVA a lista de telas do
// `BottomNav.defs` (a única das cinco listas que ninguém esquece de mexer,
// porque é ela que desenha a barra que a pessoa vê) e exige que cada aba
// derivada exista nos outros dois registros. Tela nova na barra sem snapshot
// e sem allowlist passa a FALHAR em vez de emudecer o assistente.
//
// Isto não substitui o item C3 do `26-CONTEXT.md` (consolidar os cinco
// registros num só, no front) — é a rede de segurança até lá, no mesmo padrão
// de "dois pontos testados" que `defaults.py` × `catalog.js` já usa para
// cruzar JS e Python (nunca import de Python em JS: leitura de fonte).
//
// Roda sem build e sem servidor: `node web/tests/test_pet_opcoes.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const conceitos = readFileSync(join(here, "..", "..", "server", "app", "conceitos.py"), "utf8");
const mainPy = readFileSync(join(here, "..", "..", "server", "app", "main.py"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// ------------------------------------------------- as abas, DERIVADAS da barra
// `const defs = [["evolucao", "Acompanhar"], ["radar", …], …]`
const defsBloco = app.match(/const defs = \[\[([\s\S]*?)\]\];/);
ok("BottomNav.defs foi encontrado em App.jsx (a fonte derivada deste guardião)", !!defsBloco);
const abasDaBarra = defsBloco
  ? [...("[[" + defsBloco[1] + "]]").matchAll(/\["([a-z]+)",/g)].map((m) => m[1])
  : [];
ok("BottomNav.defs tem as 5 abas da barra", abasDaBarra.length === 5, "achou: " + abasDaBarra.join(", "));
ok('"opcoes" está na barra inferior (a aba da Fase 24)', abasDaBarra.includes("opcoes"));

// `perfil` não é item da barra (é destino de navegação, achado B1 do
// 26-CONTEXT) e as sub-telas do Portfólio (`historico`, `agente`) chegam por
// `carteiraView` — as três existem para o pet e são cobertas pelo
// test_pet_ui.mjs. Aqui só o que a barra declara.
const PET_TELAS = (conceitos.match(/PET_TELAS = \(([^)]*)\)/) || [, ""])[1]
  .split(",").map((s) => s.trim().replace(/^"|"$/g, "")).filter(Boolean);
ok("conceitos.PET_TELAS foi lido do backend", PET_TELAS.length >= 7, "achou: " + PET_TELAS.join(", "));

for (const aba of abasDaBarra) {
  // "mercado" é o único sem `case` próprio: o snapshot dele vem do resumo,
  // dentro do PetSheet (regra herdada da F4, documentada em App.jsx).
  if (aba !== "mercado") {
    ok(`a aba "${aba}" da barra tem ramo próprio no switch do petSnapshot`,
       new RegExp(`case "${aba}": \\{`).test(app),
       "sem `case`, o snapshot cai no `default: return {}` e o Boris fala da tela sem dado nenhum");
  }
  ok(`a aba "${aba}" da barra está na allowlist conceitos.PET_TELAS`,
     PET_TELAS.includes(aba),
     "fora da allowlist, /api/assistente responde 400 'Tela desconhecida.'");
}

// --------------------------------------- o resumo de opcoes é dele, não de mercado
ok("o backend tem um ramo de resumo próprio para a aba Opções",
   /def _pet_resumo_opcoes\(/.test(mainPy) && /elif aba == "opcoes":/.test(mainPy),
   "sem ramo próprio, a rota cai no fallback e devolve o resumo de 'mercado'");
const corpoOpcoesPy = (mainPy.match(/def _pet_resumo_opcoes\(([\s\S]*?)\n\n\n/) || [, ""])[1];
ok("o ramo de opcoes NÃO chama o serviço de opções (a família /api/pet/* é custo-zero, ADR-027)",
   !!corpoOpcoesPy && !/mcp_client|options_mcp_api|await /.test(corpoOpcoesPy),
   "puxar a leitura do mcp.semente.dev para cá gastaria orçamento por ABRIR a aba");

// -------------------------------------------- princípio 4: dizer o que não sabe
const caseOpcoes = app.match(/case "opcoes": \{([\s\S]*?)\n      \}/);
ok("o snapshot de opcoes existe no front", !!caseOpcoes);
if (caseOpcoes) {
  ok("o snapshot manda o universo da aba e as posições de opção da carteira",
     /universo:/.test(caseOpcoes[1]) && /posicoesOpcoes:/.test(caseOpcoes[1]));
  ok("o snapshot DECLARA que a seleção da tela não chega nele (princípio 4 — nem null nem omissão)",
     /selecaoDaTela: "não disponível/.test(caseOpcoes[1]),
     "null/omissão seriam lidos como 'a pessoa não escolheu ativo nenhum'");
  ok("o snapshot não inventa ticker/tese/vencimento (estado local de OpcoesScreen)",
     !/\bticker:/.test(caseOpcoes[1]) && !/\btese:/.test(caseOpcoes[1]));
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
