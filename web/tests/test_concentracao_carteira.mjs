// Plano 04-07 (FIX-C05) — Guardião estático do aviso de concentração alta na
// Carteira: limiar/condição de render, gramática visual (T.warn, não
// T.negative), rótulo, link de drill-down sem contaminar telemetria, ausência
// de bloqueio, e copy espelhada nos dois modos (texto verbatim do UI-SPEC).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- (a) LIMIAR_CONCENTRACAO = 50 e condição de render estrita ------------
ok("LIMIAR_CONCENTRACAO declarado = 50", /const LIMIAR_CONCENTRACAO = 50;/.test(app));
ok("LIMIAR_CONCENTRACAO usado ao menos 2x (declaração + uso)", (app.match(/LIMIAR_CONCENTRACAO/g) || []).length >= 2);
ok("condição de render é conc.pct > LIMIAR_CONCENTRACAO (50% exatos não dispara)",
  app.includes("conc.pct > LIMIAR_CONCENTRACAO"));

// ---- isola o bloco do card de aviso dentro de CarteiraScreen --------------
const iniCarteira = app.indexOf("function CarteiraScreen(");
const iniHistorico = app.indexOf("function HistoricoScreen(");
if (iniCarteira === -1 || iniHistorico === -1 || iniHistorico <= iniCarteira) {
  throw new Error("Não foi possível isolar CarteiraScreen — re-grep necessário (nomes/ordem mudaram).");
}
const blocoCarteira = app.slice(iniCarteira, iniHistorico);
const iniCard = blocoCarteira.indexOf("concentracaoMaxima(data.positions");
if (iniCard === -1) throw new Error("Card de concentração não encontrado em CarteiraScreen.");
// bloco do card: do uso de concentracaoMaxima até o fechamento do IIFE que o renderiza.
const fimCard = blocoCarteira.indexOf("})()}", iniCard);
const blocoCard = blocoCarteira.slice(iniCard, fimCard === -1 ? iniCard + 1500 : fimCard);

// ---- (b) caixa usa T.warn e NÃO T.negative ---------------------------------
ok("card usa T.warn", /T\.warn/.test(blocoCard));
ok("card NÃO usa T.negative (aviso educacional, não erro)", !/T\.negative/.test(blocoCard));

// ---- (c) rótulo CONCENTRAÇÃO ALTA ------------------------------------------
ok("grep único de 'CONCENTRAÇÃO ALTA' em App.jsx", (app.match(/CONCENTRAÇÃO ALTA/g) || []).length === 1);

// ---- (d) link chama abrirVerbete("diversificacao", {ticker, pct}) ---------
ok("A.abrirVerbete existe (ação nova)", /abrirVerbete:\s*\(cid, dados\)/.test(app));
ok("A.abrirVerbete NÃO chama track(", (() => {
  const iniAcao = app.indexOf("abrirVerbete: (cid, dados) =>");
  const linha = app.slice(iniAcao, app.indexOf("\n", iniAcao) + 1);
  return !linha.includes("track(");
})());
ok("A.abrirVerbete NÃO toca em gestoUso", (() => {
  const iniAcao = app.indexOf("abrirVerbete: (cid, dados) =>");
  const linha = app.slice(iniAcao, app.indexOf("\n", iniAcao) + 1);
  return !linha.includes("gestoUso");
})());
ok("card chama A.abrirVerbete('diversificacao', { ticker: ..., pct: ... })",
  /A\.abrirVerbete\("diversificacao",\s*\{\s*ticker:\s*conc\.t,\s*pct:\s*pctArred\s*\}\)/.test(blocoCard));

// ---- (e) nenhum `disabled` novo em CarteiraScreen --------------------------
ok("CarteiraScreen não introduz nenhum `disabled=`", !blocoCarteira.includes("disabled="));

// ---- (f) as 3 chaves de copy nos DOIS modos, texto verbatim do UI-SPEC ----
ok("chave concentracaoTitulo existe nos dois modos", "concentracaoTitulo" in COPY.estudo && "concentracaoTitulo" in COPY.operador);
ok("chave concentracaoCorpo existe nos dois modos", "concentracaoCorpo" in COPY.estudo && "concentracaoCorpo" in COPY.operador);
ok("chave concentracaoLink existe nos dois modos", "concentracaoLink" in COPY.estudo && "concentracaoLink" in COPY.operador);

const corpoEstudo = COPY.estudo.concentracaoCorpo("PETR4", 62);
const corpoOperador = COPY.operador.concentracaoCorpo("PETR4", 62);
ok("corpo do modo estudo é IDÊNTICO byte a byte à copy do UI-SPEC",
  corpoEstudo === "PETR4 sozinho responde por 62% do seu patrimônio simulado. Diversificação reduz o quanto um único evento negativo pode derrubar a carteira inteira — vale estudar o conceito antes de aumentar ainda mais essa posição.");
ok("corpo do modo operador é IDÊNTICO byte a byte à copy do UI-SPEC",
  corpoOperador === "PETR4 concentra 62% da carteira. Acima disso, um único stop ruim carrega peso desproporcional no resultado — considere o tamanho antes do próximo aporte no papel.");
ok("título é o mesmo nos dois modos (rótulo, não voz)", COPY.estudo.concentracaoTitulo === COPY.operador.concentracaoTitulo && COPY.estudo.concentracaoTitulo === "Concentração alta");
ok("link é o mesmo nos dois modos", COPY.estudo.concentracaoLink === COPY.operador.concentracaoLink && COPY.estudo.concentracaoLink === "saiba mais");

// ---- vocabulário de ordem proibido no ramo estudo (mesma disciplina do guardião geral) ----
ok("corpo do modo estudo não usa vocabulário de ordem de operação",
  !/comprar|vender|registrar entrada|registrar saída/i.test(corpoEstudo));

// ---- link só renderiza com a camada de conceitos ligada -------------------
ok("link condicionado a ctx.didatica && ctx.didatica.ligada",
  /ctx\.didatica && ctx\.didatica\.ligada/.test(blocoCard));

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DE CONCENTRAÇÃO NA CARTEIRA PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
