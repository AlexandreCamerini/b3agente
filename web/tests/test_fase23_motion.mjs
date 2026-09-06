// Guardião de MOTION da Fase 23 (v1.5, Redesenho de UI) — os DOIS motions
// com propósito desta fase.
//
// Seção A (MOTION-01, plano 23-01): entrada do card de setup inédito na
// Watchlist/Radar — fade + subida curta, uma vez por ticker por sessão de
// visualização daquela lista.
// Seção B (MOTION-02, plano 23-03): pulso da confirmação de ordem. O plano
// 23-03 vai ESTENDER ESTE MESMO ARQUIVO com essa seção — o próximo agente
// não deve criar um arquivo paralelo.
//
// ILUS-01 (ilustração flat do Boris no modal de introdução, plano 23-02)
// NÃO mora aqui: o guardião dela é `web/tests/test_boris_intro.mjs`,
// ATUALIZADO pelo plano 23-02 (regra do repositório: guardião não se apaga,
// se atualiza com nota).
//
// O gate de `prefers-reduced-motion` é da Fase 20 (`test_fase20_fundacao_
// visual.mjs`, asserção MOTION-03) e é REUSADO, nunca reaberto — a asserção
// de contagem exata (=== 2) abaixo existe para travar isso dos dois lados:
// se um motion novo desta fase escrever um terceiro bloco `@media`, tanto
// este guardião quanto o da Fase 20 acusam a regressão.
//
// Roda sem build: `node web/tests/test_fase23_motion.mjs`. Padrão da casa:
// regex/includes sobre App.jsx lido com readFileSync — o módulo importa
// @capacitor/core e não é importável fora do build (ver
// test_fase22_componentes_compartilhados.mjs, test_fase3_c19_card_status.mjs).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const appPath = join(here, "..", "src", "App.jsx");
const pkgPath = join(here, "..", "package.json");
const raw = readFileSync(appPath, "utf8");
const pkgRaw = readFileSync(pkgPath, "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Remove comentários de linha (//...) antes de contar/buscar ocorrências —
// este plano escreve comentários em português dentro do App.jsx que citam os
// mesmos termos buscados (`card-enter`, `b3cardEnter`, `isNovo`); contagem
// crua se autoinvalidaria (comentário conta como "código" e infla o
// resultado). Copiado de test_fase20_fundacao_visual.mjs:34-42.
function stripLineComments(src) {
  return src
    .split("\n")
    .map((line) => {
      const i = line.indexOf("//");
      return i >= 0 ? line.slice(0, i) : line;
    })
    .join("\n");
}
const app = stripLineComments(raw);

function count(re) {
  const m = app.match(re);
  return m ? m.length : 0;
}

// Isolamento por marcador textual estável, padrão da casa
// (test_fase22_componentes_compartilhados.mjs / test_fase3_c19_card_status.mjs):
// do início do marcador até o próximo `\nfunction `. Aborta com mensagem
// explícita (nunca passa em silêncio) se o marcador sumir — guardião que
// vira no-op em silêncio é pior que guardião ausente.
function isolarFuncao(nome) {
  const marcador = `function ${nome}(`;
  const inicio = app.indexOf(marcador);
  if (inicio < 0) {
    console.error(`FALHOU: ${marcador} não encontrado em App.jsx — guardião não pode isolar o componente`);
    process.exit(1);
  }
  const fim = app.indexOf("\nfunction ", inicio + marcador.length);
  return app.slice(inicio, fim > inicio ? fim : undefined);
}

// --- Seção A — MOTION-01 (plano 23-01): entrada de card inédito ----------

// 1) Keyframe literal, geometria exata (contrato do 23-UI-SPEC.md).
const KEYFRAME_LITERAL = "@keyframes b3cardEnter{ from{ opacity:0; transform:translateY(8px); } to{ opacity:1; transform:translateY(0); } }";
ok("MOTION-01: existe @keyframes b3cardEnter em GlobalStyle() com a geometria exata do contrato", app.includes(KEYFRAME_LITERAL));

// 2) Classe que consome o keyframe, escopada em .b3 — herda o gate de
//    reduced-motion (não é @media novo) e fica fora do alcance de CSS global.
const CLASS_LITERAL = ".b3 .card-enter{ animation:b3cardEnter 200ms ease-out; }";
ok("MOTION-01: existe a classe .b3 .card-enter com 200ms ease-out (escopo .b3: herda o gate de reduced-motion e fica fora do CSS global)", app.includes(CLASS_LITERAL));

// 3) O guardrail do 23-CONTEXT.md: continuam existindo EXATAMENTE dois
//    blocos @media (prefers-reduced-motion: reduce) — mesma forma que
//    test_fase20_fundacao_visual.mjs:143. A Fase 23 reusa a regra da Fase
//    20; motion novo entra como `animation` CSS dentro de `.b3`, nunca como
//    @media novo.
const reducedMotionBlocks = count(/@media \(prefers-reduced-motion: reduce\)\{/g);
ok(
  "MOTION-01: continuam existindo exatamente 2 blocos @media (prefers-reduced-motion: reduce) — a Fase 23 reusa a regra da Fase 20; motion novo entra como `animation` CSS dentro de `.b3`, nunca como @media novo",
  reducedMotionBlocks === 2
);

const mercadoScreen = isolarFuncao("MercadoScreen");
const radarScreen = isolarFuncao("RadarScreen");
const ativoCard = isolarFuncao("AtivoCard");

// 4) MercadoScreen tem um ref de tickers vistos (useRef(new Set())) e um
//    useEffect que faz .add( nesse ref.
ok("MOTION-01: MercadoScreen tem um ref de tickers vistos (useRef(new Set()))", /useRef\(new Set\(\)\)/.test(mercadoScreen));
ok("MOTION-01: MercadoScreen tem um useEffect que adiciona ao ref de vistos (.add()", /useEffect\(\(\) => \{[\s\S]*?\.add\(/.test(mercadoScreen));

// 5) Idem para RadarScreen.
ok("MOTION-01: RadarScreen tem um ref de tickers vistos (useRef(new Set()))", /useRef\(new Set\(\)\)/.test(radarScreen));
ok("MOTION-01: RadarScreen tem um useEffect que adiciona ao ref de vistos (.add()", /useEffect\(\(\) => \{[\s\S]*?\.add\(/.test(radarScreen));

// 6) O ref NÃO é persistido — trava a contagem TOTAL de `localStorage` no
//    arquivo (medida ANTES desta fase: 9 ocorrências, contando ocorrências
//    de token, não linhas — a linha 8593 tem duas na mesma linha). Se essa
//    contagem subir, alguma das duas telas ganhou uma escrita de
//    persistência nova perto do mecanismo de "visto" — o que 23-CONTEXT.md
//    proíbe
//    explicitamente ("reseta ao trocar de tela ou recarregar").
const LOCALSTORAGE_BASELINE = 9;
ok(
  `MOTION-01: nenhuma ocorrência nova de localStorage no arquivo (baseline medido antes da Fase 23: ${LOCALSTORAGE_BASELINE})`,
  count(/localStorage/g) === LOCALSTORAGE_BASELINE
);

// 7) O commit é efeito, nunca render: o `.add(` mora dentro do corpo de um
//    useEffect (índice do .add( maior que o índice do useEffect(() => {
//    mais próximo antes dele) e a chamada do useEffect acontece antes do
//    primeiro `return (` da tela — hooks não podem ser registrados depois
//    do return. Motivo: React.StrictMode (main.jsx) invoca o corpo do
//    componente 2x por render em dev; mutar o Set durante o RENDER (fora de
//    um efeito) faria a 2ª passada ler o ticker como já visto e a animação
//    nunca apareceria.
function verificaCommitEmEfeito(nomeTela, corpo) {
  const idxAdd = corpo.indexOf(".add(");
  // "return (" seguido de quebra de linha é o retorno de JSX da tela — NÃO
  // usar `indexOf("return (")` cru: casa também com "return () => {...}"
  // (retorno de função de limpeza de um useEffect qualquer), que aparece
  // MUITO antes do return de JSX de verdade e produz falso negativo.
  const returnMatch = /return \(\s*\n/.exec(corpo);
  const idxReturn = returnMatch ? returnMatch.index : -1;
  if (idxAdd < 0 || idxReturn < 0) return false;
  const useEffectAntes = corpo.lastIndexOf("useEffect(() => {", idxAdd);
  if (useEffectAntes < 0) return false;
  return useEffectAntes < idxAdd && idxAdd < idxReturn;
}
ok(
  "MOTION-01: em MercadoScreen, o .add( de vistos está dentro de um useEffect e antes do primeiro return da tela (React.StrictMode de main.jsx roda o corpo 2x — commit no render quebraria a entrada em dev)",
  verificaCommitEmEfeito("MercadoScreen", mercadoScreen)
);
ok(
  "MOTION-01: em RadarScreen, o .add( de vistos está dentro de um useEffect e antes do primeiro return da tela (mesma razão do React.StrictMode)",
  verificaCommitEmEfeito("RadarScreen", radarScreen)
);

// 8) A raiz do AtivoCard carrega o className condicional de entrada, na
//    MESMA linha que já identifica o card (id={"ativo-" + t}) — é o único
//    <div> raiz do componente.
const linhaRaizAtivoCard = ativoCard.split("\n").find((l) => l.includes('id={"ativo-" + t}'));
ok(
  "MOTION-01: a raiz do AtivoCard (linha com id={\"ativo-\" + t}) carrega className condicional de entrada (card-enter)",
  !!linhaRaizAtivoCard && linhaRaizAtivoCard.includes("card-enter")
);

// 9) `isNovo` é passado no vm dos DOIS call sites (Watchlist e Radar).
ok("MOTION-01: MercadoScreen passa isNovo no vm do call site do AtivoCard (Watchlist)", /isNovo/.test(mercadoScreen));
ok("MOTION-01: RadarScreen passa isNovo no vm/radarVm do call site do AtivoCard (Radar)", /isNovo/.test(radarScreen));

// 10) Zero dependência de animação nova.
const LIBS_PROIBIDAS = ["framer-motion", "react-spring", "motion", "gsap", "animejs", "react-transition-group"];
LIBS_PROIBIDAS.forEach((lib) => {
  ok(`MOTION-01: nenhuma dependência de animação nova em web/package.json (${lib})`, !pkgRaw.includes(`"${lib}"`));
});

// 11) As três animações infinitas da Fase 20 continuam intactas — a
//     inserção do keyframe novo não pode ter atropelado o bloco vizinho.
ok("MOTION-01: .b3 .spin{ animation:b3spin continua presente (Fase 20 intacta)", app.includes(".b3 .spin{ animation:b3spin"));
ok("MOTION-01: .b3 .sk{ continua presente (Fase 20 intacta)", app.includes(".b3 .sk{"));
ok("MOTION-01: .b3 .tt-track{ animation:b3tt continua presente (Fase 20 intacta)", app.includes(".b3 .tt-track{ animation:b3tt"));

console.log(fails === 0 ? "\nOK — todas as asserções da Seção A (MOTION-01) passaram" : `\n${fails} asserção(ões) falharam`);
process.exit(fails);
