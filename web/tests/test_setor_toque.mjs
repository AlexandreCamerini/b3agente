// Camada de entendimento — TAP + SUBLINHADO (SetorAlvo v2, padrão Duolingo).
//
// A v1 (toque longo) caiu no teste ao vivo: sem indicação ninguém sabia onde
// segurar; segurando em qualquer lugar, fora dos setores respondia a SELEÇÃO
// DE TEXTO; e toque longo só funciona com alvo óbvio. Os contratos da v2:
//
//  1. TOQUE SIMPLES abre a folha — nenhuma máquina de estados, nenhum timer.
//     Regressão a vigiar: GESTO_MS/DicaGesto voltando ao código.
//  2. A INDICAÇÃO É O SUBLINHADO PONTILHADO, um por setor, no termo-âncora.
//  3. O setor mais interno vence (stopPropagation no click) e o toque não
//     vaza para o card por baixo.
//  4. `userSelect: none` nos setores (toque duplo apressado não seleciona);
//     `touchAction` intocado (a rolagem é do sistema).
//  5. Medição: `gesto` = toques no sublinhado, `botao` = sr-only; merge
//     monotônico nos DOIS stores.
//  6. `tela: "setor:<id>"` só quando a folha veio do setor; a cadeia volta a
//     `conceito:<cid>`.
//
// Roda sem build: `node web/tests/test_setor_toque.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const setorAlvo = app.slice(app.indexOf("function SetorAlvo("), app.indexOf("function AssistenteBox("));
ok("SetorAlvo existe e é isolável para as asserções de ausência", setorAlvo.length > 200);

// ------------------------------------------------------------------ o toque
ok("toque SIMPLES abre a folha (onClick, sem timer)",
   /const onClick = \(e\) => \{/.test(setorAlvo) && /abrir\("toque"\)/.test(setorAlvo));
// (onPointerDown segue existindo no arrasto da FOLHA — é outro componente;
// aqui o escopo é o app para os símbolos do toque longo e o SetorAlvo para
// a máquina de pointer.)
ok("zero resíduo do toque longo (GESTO_MS/DicaGesto no app; pointer no setor)",
   !/GESTO_MS|DICA_GESTO|DicaGesto|GESTO_TOLERANCIA/.test(app)
   && !/onPointerDown|onPointerMove|setTimeout/.test(setorAlvo));
ok("o setor mais interno vence e o toque não vaza para o card",
   /e\.stopPropagation\(\);\s*\n\s*abrir\("toque"\);/.test(setorAlvo));
ok("o carimbo da barra é setor DENTRO do badge (caso real de aninhamento)",
   /setorId="timing"/.test(app) && /setorId="barra"/.test(app));
ok("o chip do fundamento é setor DENTRO da linha de análise",
   /setorId="analise"/.test(app) && /setorId="fundamento"/.test(app));

// ------------------------------------------------------------- a indicação
ok("a convenção do sublinhado pontilhado existe e é única",
   /const SUBLINHADO = \{ textDecorationLine: "underline", textDecorationStyle: "dotted"/.test(app));
for (const [onde, padrao] of [
  ["rótulo do badge (com plano)", /\.\.\.\(didaticaOk \? SUBLINHADO : \{\}\) \}\}>\{operador \? rotOp : rotEdu\}/],
  ["carimbo da barra", /fontFamily: MONO, \.\.\.SUBLINHADO \}\}>\s*\n\s*\{\/\* barra de outro dia/],
  ["chips explicáveis (rótulo)", /<span style=\{explicavel \? SUBLINHADO : undefined\}>\{label\}<\/span>/],
  ["caption da régua", /caption=\{<span style=\{SUBLINHADO\}>POSIÇÃO NO RISCO<\/span>\}/],
  ["R:R", /<span style=\{SUBLINHADO\}>R:R<\/span>/],
]) ok(`sublinhado no termo-âncora: ${onde}`, padrao.test(app));
ok("confluência e fundamento pedem o sublinhado no chip",
   /chip\("confluência", \(sc\.confluencia \|\| 0\) \+ "%", T\.accent, true\)/.test(app)
   && /chip\("fundamento", fscore, T\[SCORE_COLOR\[fscore\]\] \|\| T\.textPrimary, true\)/.test(app));

// ------------------------------------------------ seleção de texto e rolagem
ok("userSelect none nos setores (o defeito da v1 não volta)",
   /WebkitTouchCallout: "none", WebkitUserSelect: "none", userSelect: "none"/.test(setorAlvo));
ok("a rolagem NÃO é sequestrada (nenhum touchAction: aplicado no setor)",
   !/touchAction:/.test(setorAlvo));

// -------------------------------------------------- registro vem do backend
ok("o conceito do setor vem do REGISTRO (didatica.setores), nunca de dict do front",
   /didatica\.setores\) \? didatica\.setores\[setorId\] : null/.test(setorAlvo));
ok("sem registro (backend antigo / camada desligada) o setor vira contêiner comum",
   /if \(!cid \|\| !A \|\| !ativo\) return <div style=\{style\}>\{children\}<\/div>;/.test(setorAlvo));
ok("o timing só arma o toque com PLANO (ativo={didaticaOk})",
   /setorId="timing" dados=\{dados\}[\s\S]{0,200}ativo=\{didaticaOk\}/.test(app));

// ------------------------------------------------------------ acessibilidade
ok("cada setor tem caminho nomeado para leitor de tela (sr-only)",
   /aria-label=\{"O que é " \+ rotulo \+ "\?"\} style=\{SR_ONLY\}/.test(setorAlvo)
   && /clipPath: "inset\(50%\)"/.test(app));

// --------------------------------------------------- medição de descoberta
ok("abrirSetor conta toque × botão (o pontilhado está sendo encontrado?)",
   /abrirSetor: \(setorId, cid, dados, origem\)/.test(app)
   && /origem === "toque" \? "gesto" : "botao"/.test(app)
   && /store\.putConfig\(\{ gestoUso: g \}\)/.test(app));
ok("deviceStore espelha gestoUso com merge MONOTÔNICO (max, nunca substituição)",
   /if \(patch\.gestoUso && typeof patch\.gestoUso === "object"\)/.test(persistence)
   && /Math\.max\(base\[k\] \|\| 0, Math\.min\(Math\.floor\(v\), 100000\)\)/.test(persistence));

// -------------------------------------------------- assistente com o setor
ok("a folha carrega o setor de origem e o assistente pergunta de lá",
   /setor=\{conceitoAberto\.setor \|\| null\}/.test(app)
   && /tela: tela \|\| \(setor \? "setor:" \+ setor : "conceito:" \+ cid\)/.test(app));
ok("navegar a cadeia SAI do setor (tela volta a ser o conceito)",
   /trocarConceito: \(cid\) => setConceitoAberto\(\(c\) => \(c \? \{ \.\.\.c, cid, setor: null/.test(app));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
