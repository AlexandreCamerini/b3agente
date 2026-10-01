// Fase 46 (plano 46-07, CART6-03/04) — guardião estático das camadas por modo do
// card aberto: SimuladorEstudo, TermosTocaveis (Estudo), PayoffOperador, GradeConta
// (Operador). Lê App.jsx como TEXTO. Guardião não se apaga; reversão deliberada
// atualiza com nota.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function functionBody(name) {
  const m = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`).exec(src);
  if (!m) return "";
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(m.index, i);
}
const semCom = (b) => b.replace(/\{\/\*[\s\S]*?\*\/\}/g, "").split("\n").filter((l) => !/^\s*\/\//.test(l.trim())).join("\n");

const sim = semCom(functionBody("SimuladorEstudo"));
const termos = semCom(functionBody("TermosTocaveis"));
const payoff = semCom(functionBody("PayoffOperador"));
const grade = semCom(functionBody("GradeConta"));
const opcoes = semCom(functionBody("CardPosicaoEstruturada"));
const cartao = semCom(functionBody("CartaoPosicao"));

const idx = (n) => src.indexOf(`function ${n}(`);
for (const n of ["SimuladorEstudo", "TermosTocaveis", "PayoffOperador", "GradeConta"]) {
  ok(`${n}: 1 definição, antes de LinhaChamadaOpcoes`, (src.match(new RegExp(`^function ${n}\\(`, "gm")) || []).length === 1 && idx(n) < idx("LinhaChamadaOpcoes"));
}

// Mesma regex do adaptador (test_estrutura_para_payoff.mjs), com be/k/valor/preco.
const CAMPOS = ["resultado", "preco", "valor", "be", "k"];
const ARIT = new RegExp(`\\b(${CAMPOS.join("|")})\\b\\s*[*/+-]\\s*[\\w.]|[\\w.]\\s*[*/+-]\\s*(?:\\w+\\.)?\\b(${CAMPOS.join("|")})\\b`);
// Comparação < / > envolvendo be/k/preco/resultado (JSX `<`/`>` de tag não casam: exige operando).
const COMPARA = /\b(be|k|preco|resultado)\b\s*(<=?|>=?)\s*[\w.(]|[\w.)]\s*(<=?|>=?)\s*(?:\w+\.)?\b(be|k|preco|resultado)\b/;
ok("sanidade: ARIT pega conta inventada", ARIT.test("x = ponto.preco * 2") && ARIT.test("y = 1 + c.be"));
ok("sanidade: COMPARA pega comparação inventada", COMPARA.test("if (ponto.preco > c.be)"));

// --- SimuladorEstudo --------------------------------------------------------
ok("Simulador: slider por ÍNDICE (min={0}, step={1}, max pelo tamanho da grade)", /type="range"/.test(sim) && /min=\{0\}/.test(sim) && /step=\{1\}/.test(sim) && /max=\{sim\.pontos\.length - 1\}/.test(sim));
ok("Simulador: lê o ponto por pontoDoIndice( e indiceNomeado(", /pontoDoIndice\(/.test(sim) && /indiceNomeado\(/.test(sim));
ok("Simulador: onChange só troca o índice", /onChange=\{\(ev\) => setIdx\(Number\(ev\.target\.value\)\)\}/.test(sim));
ok("Simulador: aria-label e aria-valuetext", /aria-label=\{cartaoPosicaoTxt\(modo, "sim_aria"/.test(sim) && /aria-valuetext=/.test(sim));
ok("Simulador: chips com aria-pressed por igualdade de índice e minHeight 44", /aria-pressed=\{sel\}/.test(sim) && /const sel = x\.i === idx/.test(sim) && /minHeight:\s*44\b/.test(sim));
ok("Simulador: caixa de zona role=status com texto do backend (zona.texto) e glifo aria-hidden", /role="status"/.test(sim) && /zona\.texto/.test(sim) && /zonaVisual\(/.test(sim));
ok("Simulador: sem rede nem store (fetch(, store.)", !/fetch\(/.test(sim) && !/\bstore\./.test(sim));
ok("Simulador: sem aritmética sobre preco/resultado/be/k", !ARIT.test(sim));
ok("Simulador: sem comparação preço×BE/K", !COMPARA.test(sim));

// --- TermosTocaveis ---------------------------------------------------------
ok("Termos: verbete validado com verbeteDoCatalogo(ctx.kbCatalogo", /verbeteDoCatalogo\(ctx\.kbCatalogo/.test(termos));
ok("Termos: <button só depois do ramo do verbete válido (ramo sem verbete devolve texto)", termos.indexOf("if (!verbeteDoCatalogo(ctx.kbCatalogo, seg.kb)) return <span") > 0 && termos.indexOf("<button", termos.indexOf("if (!verbeteDoCatalogo(")) > termos.indexOf("if (!verbeteDoCatalogo("));
ok("Termos: painel role=status com definição da KB (verbete.texto), 'No seu caso' e Entendi", /role="status"/.test(termos) && /verbete\.texto/.test(termos) && /"no_seu_caso"/.test(termos) && /"entendi"/.test(termos));
ok("Termos: um termo por vez (estado único) + devolve o foco", /useState\(null\)/.test(termos) && /\.focus\(\)/.test(termos));
ok("Termos: sem cálculo do caso => aguardando_calculo", /"aguardando_calculo"/.test(termos));

// --- PayoffOperador ---------------------------------------------------------
ok("Payoff: svg role=img + aria-label do backend", /<svg role="img" aria-label=\{pf\.aria\}/.test(payoff));
ok("Payoff: zero <text no desenho", !/<text\b/.test(payoff));
ok("Payoff: retorna null sem pontos", /pf\.pontos\.length < 2\) return null/.test(payoff) && /!pf \|\|/.test(payoff));
ok("Payoff: mapeamento só em funções de layout xDoGrafico/yDoGrafico", /const xDoGrafico =/.test(payoff) && /const yDoGrafico =/.test(payoff));
ok("Payoff: legenda leg_hoje/leg_be/leg_k/leg_eixo", ["leg_hoje", "leg_be", "leg_k", "leg_eixo"].every((k) => payoff.includes(`"${k}"`)));
ok("Payoff: sem comparação preço×BE/K", !COMPARA.test(payoff));

// --- GradeConta -------------------------------------------------------------
ok("Grade: aria-expanded, conta_sem_formula, colunasDaGrade(", /aria-expanded=/.test(grade) && /"conta_sem_formula"/.test(grade) && /colunasDaGrade\(/.test(grade));
ok("Grade: sem ellipsis, com overflowWrap anywhere", !/ellipsis/.test(grade) && /overflowWrap:\s*"anywhere"/.test(grade));
ok("Grade: sem ⓘ e sem termos tocáveis", !/ⓘ/.test(grade) && !/verbeteDoCatalogo/.test(grade));
ok("Grade: sem aritmética sobre os campos", !ARIT.test(grade));

// --- montagem ---------------------------------------------------------------
ok("Montagem Estudo: SimuladorEstudo só com !operador", /\{!operador && e\.cenarios\.simulador && <SimuladorEstudo/.test(opcoes));
ok("Montagem Operador: PayoffOperador + GradeConta só com operador", /\{operador && e\.cenarios\.payoff && \(/.test(opcoes) && /<PayoffOperador/.test(opcoes) && /<GradeConta/.test(opcoes));
ok("Montagem: sem cenarios segue a caixa sem_cenario", /!e\.cenarios \?/.test(opcoes) && /"sem_cenario"/.test(opcoes));
ok("Montagem: TermosTocaveis só no Estudo, fora do flip, didatica composta ou simples", /\{!operador && <TermosTocaveis didatica=\{e \? e\.didatica : \(leituraPlano \? leituraPlano\.didatica : null\)\}/.test(cartao));

// --- higiene dos 4 componentes ---------------------------------------------
for (const [n, b] of [["Simulador", sim], ["Termos", termos], ["Payoff", payoff], ["Grade", grade]]) {
  ok(`${n}: sem hex literal e sem dangerouslySetInnerHTML`, !/#[0-9a-fA-F]{3,6}\b/.test(b) && !/dangerouslySetInnerHTML/.test(b));
}

// --- PayoffChart da aba Opções intacto --------------------------------------
const chart = readFileSync(join(here, "..", "src", "opcoes", "PayoffChart.jsx"), "utf8");
ok("PayoffChart.jsx não importa nada do card v6", !/^import .*(estruturaCard|cartao_posicao)/m.test(chart));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
