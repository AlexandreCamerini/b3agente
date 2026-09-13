// Fase 26, achado A3 (2026-09-12) — O VOCABULÁRIO POR MODO DA ABA OPÇÕES.
//
// O achado: a aba Opções não teria voz por modo — título e subtítulo fixos,
// enquanto as outras abas trocam de registro entre Estudo (professor) e
// Operador (mesa). A reconferência mostrou que a Fase 24 (`aba-opcoes F2`,
// commit 404f8e6) já havia criado `tituloOpcoes`/`subtituloOpcoes` nos dois
// blocos de `copy.js` e já lia as duas chaves em `OpcoesScreen.jsx` — o
// briefing descrevia a árvore de antes dela. O que FALTAVA era o guardião:
// nada impedia alguém de voltar a escrever o texto direto no JSX, ou de
// colar o mesmo subtítulo nos dois modos, e ninguém veria.
//
// O que este arquivo trava, e por quê:
//
//  1. AS CHAVES EXISTEM NOS DOIS BLOCOS. Chave só no Estudo faz a aba cair no
//     fallback do JSX em Operador — o modo volta a não existir, em silêncio.
//  2. O SUBTÍTULO DIFERE ENTRE OS MODOS. É onde a voz mora: Estudo explica o
//     que a aba mostra, Operador vai direto ao estado. Texto idêntico nos dois
//     é a regra para estado de conta/sistema; este NÃO é um deles.
//  3. O TÍTULO PODE SER IGUAL, DE PROPÓSITO. "Opções" é o nome da coisa nos
//     dois registros — não há sinônimo de mesa para ele (diferente de
//     Watchlist × Monitoramento). Travado como IGUAL para que a divergência,
//     se um dia vier, seja uma decisão e não um acidente.
//  4. `tabOpcoes` (rótulo curto da barra) NÃO MUDA entre os modos. Mexer nele
//     mudaria a barra inferior em produção, e não é o que o achado pede.
//  5. OS DOIS SUBTÍTULOS DIZEM QUE NENHUMA ORDEM SAI DALI. Princípio 1/2 do
//     CLAUDE.md na tela onde a confusão é mais cara: quem vê uma cadeia de
//     opções e um payoff precisa ler, na própria tela, que nada é enviado.
//  6. O JSX LÊ AS CHAVES, não texto fixo.
//
// Roda sem build e sem servidor: `node web/tests/test_vocabulario_opcoes.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const tela = readFileSync(join(here, "..", "src", "opcoes", "OpcoesScreen.jsx"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

const e = COPY.estudo;
const o = COPY.operador;

// ----------------------------------------------------- 1. as chaves existem
for (const [modo, bloco] of [["estudo", e], ["operador", o]]) {
  ok(`COPY.${modo}.tituloOpcoes existe e não é vazio`,
     typeof bloco.tituloOpcoes === "string" && !!bloco.tituloOpcoes.trim());
  ok(`COPY.${modo}.subtituloOpcoes existe e não é vazio`,
     typeof bloco.subtituloOpcoes === "string" && !!bloco.subtituloOpcoes.trim());
}

// ------------------------------------------------- 2. o subtítulo tem voz
ok("o subtítulo da aba Opções DIFERE entre Estudo e Operador",
   e.subtituloOpcoes !== o.subtituloOpcoes,
   "subtítulo igual nos dois modos = a aba perdeu a voz do modo");

// ------------------------------------- 3. o título é igual, por decisão
ok("o título da aba Opções é o MESMO nos dois modos (decisão registrada, não acidente)",
   e.tituloOpcoes === o.tituloOpcoes,
   "se a divergência foi deliberada, atualize este guardião com a nota — não o apague");

// ---------------------------------------- 4. a barra inferior não muda
ok("tabOpcoes (rótulo da barra) é o mesmo nos dois modos",
   e.tabOpcoes === o.tabOpcoes,
   "mudar o rótulo da barra por modo altera a navegação em produção — fora do escopo do A3");

// ------------------------------- 5. nenhuma ordem sai da aba, nos dois modos
const NEGA_ORDEM = /ordem/i;
for (const [modo, bloco] of [["estudo", e], ["operador", o]]) {
  ok(`o subtítulo de ${modo} diz, na própria tela, que nenhuma ordem sai dali`,
     NEGA_ORDEM.test(bloco.subtituloOpcoes),
     "a aba mostra cadeia e payoff; sem essa frase a pessoa pode achar que envia ordem");
}

// ------------------------------------------- 6. o JSX lê as chaves
ok("OpcoesScreen.jsx lê cp.tituloOpcoes (com fallback, nunca texto fixo no lugar da chave)",
   /\{cp\.tituloOpcoes \|\| "Opções"\}/.test(tela));
ok("OpcoesScreen.jsx lê cp.subtituloOpcoes",
   /\{cp\.subtituloOpcoes \|\| ""\}/.test(tela));
ok("o <h1> da aba não tem título escrito à mão",
   !/<h1[^>]*>\s*Opções\s*</.test(tela));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
