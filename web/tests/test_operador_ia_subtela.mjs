// aba-opcoes F2 (quick 260910-biz, 2026-09-10) — guardião da TROCA DE ABA.
//
// O que ele tranca: "Opções" ocupou o 5º lugar da barra inferior e o
// "Operador IA" virou SUB-TELA do Portfólio (D-0.1 do
// `docs/PLANO-aba-opcoes.md`), pelo mesmo mecanismo que "Histórico" já usava.
// A parte perigosa da mudança não é o que entrou — é o que pode ter FICADO:
// um `tab === "agente"` órfão renderiza uma tela que a barra não alcança
// mais, e o usuário perde o Operador IA sem nenhuma mensagem de erro.
//
// Técnica: leitura estática do fonte (sem build, sem DOM), o padrão da casa.
// Higiene obrigatória: as linhas de COMENTÁRIO saem ANTES de qualquer
// contagem — este próprio arquivo e os comentários de App.jsx citam
// `tab === "agente"` ao explicar a migração, e contá-los faria o guardião
// se auto-invalidar (passaria a reprovar por causa da própria documentação).
//
// Roda sem build: `node web/tests/test_operador_ia_subtela.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const bruto = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

// Remove comentários de bloco e de linha. Grosseiro de propósito: é para
// CONTAGEM, não para reparse — falso negativo aqui (código dentro de string
// com "//") não existe neste arquivo.
const app = bruto
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n")
  .filter((l) => !/^\s*\/\//.test(l))
  .join("\n");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const conta = (re) => (app.match(re) || []).length;

// ---- 1) a barra inferior -----------------------------------------------------
const defs = app.match(/const defs = \[[\s\S]*?\]\];/);
ok("bloco `defs` do BottomNav encontrado", !!defs);
const defsTxt = defs ? defs[0] : "";
ok("defs tem 5 itens", (defsTxt.match(/\["/g) || []).length === 5);
ok('o 5º item é ["opcoes", (cp && cp.tabOpcoes)',
   /\["opcoes", \(cp && cp\.tabOpcoes\)/.test(defsTxt));
ok("as linhas de mercado e radar continuam intactas (test_copy_theme)",
   defsTxt.includes('["mercado", (cp && cp.tituloWatchlist)')
   && defsTxt.includes('["radar", (cp && cp.tabRadar)'));

// ---- 2) nada do arranjo antigo sobrou ---------------------------------------
ok('zero ocorrências de ["agente", "Operador IA"]', conta(/\["agente", "Operador IA"\]/g) === 0);
ok('zero ocorrências de tab === "agente"', conta(/tab === "agente"/g) === 0);

// ---- 3) a tela nova entra pela barra ----------------------------------------
ok('tab === "opcoes" renderiza <OpcoesScreen ctx={ctx} />',
   /\{tab === "opcoes" && <OpcoesScreen ctx=\{ctx\} \/>\}/.test(app));
ok("OpcoesScreen é importado de ./opcoes/OpcoesScreen.jsx",
   /import OpcoesScreen from "\.\/opcoes\/OpcoesScreen\.jsx";/.test(bruto));

// ---- 4) Operador IA como sub-tela do Portfólio -------------------------------
ok('existe o ramo carteiraView === "agente"', /carteiraView === "agente"/.test(app));
// Ancorado no `? (<><BackHeader` de propósito: a PRIMEIRA ocorrência de
// `carteiraView === "agente"` no fonte é o cálculo do `petTela`, que não tem
// (nem deve ter) BackHeader nenhum.
const ramoAgente = app.match(/carteiraView === "agente"\s*\?\s*\(<><BackHeader[\s\S]{0,400}/);
ok("o ramo do agente traz BackHeader e <AgenteScreen ctx={ctx} />",
   !!ramoAgente && /BackHeader/.test(ramoAgente[0]) && /<AgenteScreen ctx=\{ctx\} \/>/.test(ramoAgente[0]));
ok("o BackHeader do agente usa cp.tituloOperadorIA e volta para main",
   !!ramoAgente && /cp\.tituloOperadorIA/.test(ramoAgente[0])
   && /setCarteiraView\("main"\)/.test(ramoAgente[0]));
ok('o comentário do carteiraView declara os três valores',
   /main \| historico \| agente/.test(bruto));

// ---- 5) goAgente é o ponto único --------------------------------------------
ok("goAgente definido exatamente uma vez", conta(/goAgente: \(\) =>/g) === 1);
ok("goAgente leva a carteira + view agente",
   /goAgente: \(\) => \{ setPerfilView\("hub"\); setTab\("carteira"\); setCarteiraView\("agente"\); \}/.test(app));
ok("a linha do Portfólio chama goAgente()", /onClick=\{\(\) => ctx\.goAgente\(\)\}/.test(app));

// ---- 6) a linha de acesso no topo do Portfólio ------------------------------
const linha = app.match(/onClick=\{\(\) => ctx\.goAgente\(\)\}[\s\S]{0,400}/);
ok("a linha usa cp.linkOperadorIA", !!linha && /cp\.linkOperadorIA/.test(linha[0]));
ok("a linha tem alvo de toque de ao menos 48px",
   !!linha && /minHeight: "(4[89]|[5-9]\d|\d{3,})px"/.test(linha[0]));
ok("o botão de histórico continua onde estava",
   /setCarteiraView\("historico"\)/.test(app) && /Ver histórico de operações/.test(app));

// ---- 7) o que NÃO pode ter sido removido ------------------------------------
const navIcon = bruto.match(/const paths = \{[\s\S]*?\n  \};/);
ok("NavIcon.paths encontrado", !!navIcon);
ok("NavIcon.paths mantém os ids `opcoes` E `agente`",
   !!navIcon && /\bopcoes:/.test(navIcon[0]) && /\bagente:/.test(navIcon[0]));
ok("petTela cobre historico, agente e o default carteira",
   /const petTela = tab === "carteira" \? \(carteiraView === "historico" \? "historico" : carteiraView === "agente" \? "agente" : "carteira"\) : tab;/.test(app));
ok('o case "agente" do petSnapshot continua existindo', /case "agente":/.test(app));

// ---- 8) copy nos dois modos --------------------------------------------------
const e = Object.keys(COPY.estudo).sort(), o = Object.keys(COPY.operador).sort();
ok("chaves espelhadas nos dois modos", JSON.stringify(e) === JSON.stringify(o));
for (const k of ["tabOpcoes", "tituloOperadorIA", "linkOperadorIA"]) {
  ok(`COPY tem ${k} nos dois modos`, !!COPY.estudo[k] && !!COPY.operador[k]);
}

// ---- 9) nenhum texto chama mais o Operador IA de "aba" ----------------------
ok('nenhum texto do app diz "aba Operador IA"', !/aba Operador IA/.test(bruto));

console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
