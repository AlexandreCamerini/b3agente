// Fase 37 (37-02) — Guardião de `formatarRazao()` (uiOpcoes.jsx) e
// `ExplicacaoPayoff`/`montarTexto` (ExplicacaoPayoff.jsx): D-06/D-07 (ordem
// spot-primeiro), EXPL-02 (vocabulário banido) e EXPL-03/D-05 (razão G/P
// nunca formatada duas vezes).
//
// Desvio de infraestrutura, documentado (não estava no censo do plano):
// `node` PURO não conhece a extensão `.jsx` — falha por EXTENSÃO, mesmo em
// arquivo sem sintaxe JSX nenhuma (confirmado empiricamente antes de
// escrever este arquivo). Os dois arquivos-fonte deste guardião (`uiOpcoes.
// jsx`, `ExplicacaoPayoff.jsx`) precisam continuar sendo `.jsx` de verdade
// (são componentes React reais, consumidos por Planos futuros) — a
// alternativa de mover a lógica pura para um `.js` espelho reintroduziria
// exatamente a classe de bug que este plano fecha (duas fontes formatando o
// mesmo número). Resolvido com `_jsx_loader.mjs`, um hook de módulo ESM
// (`node:module` `register()`) que despe a sintaxe JSX via `esbuild`
// (dependência já transitiva do Vite, nenhuma dependência nova) só para
// quem importa um `.jsx` por aqui — o padrão dominante da casa (inspeção
// estática de fonte) continua para o guardião de vocabulário banido abaixo.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { register } from "node:module";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

register("./_jsx_loader.mjs", import.meta.url);

const { formatarRazao } = await import("../src/opcoes/uiOpcoes.jsx");
const ExplicacaoPayoffMod = await import("../src/opcoes/ExplicacaoPayoff.jsx");
const ExplicacaoPayoff = ExplicacaoPayoffMod.default;
const { montarTexto } = ExplicacaoPayoffMod;

const cp = COPY.estudo;

// ---- (1) formatarRazao() — mesma string que RazaoGanhoPerda produzia inline
ok("formatarRazao({valor: 0.67}) === \"1 : 0,67\" (mesma saída inline de RazaoGanhoPerda)",
  formatarRazao({ valor: 0.67, motivo: null }) === "1 : 0,67");
ok("formatarRazao({valor: null, motivo}) retorna o motivo",
  formatarRazao({ valor: null, motivo: "sem breakeven" }) === "sem breakeven");
ok("formatarRazao({valor: null, motivo: null}) retorna travessão",
  formatarRazao({ valor: null, motivo: null }) === "—");
ok("formatarRazao(undefined) não lança, retorna travessão",
  formatarRazao(undefined) === "—");

// ---- (2) ExplicacaoPayoff — guarda-cláusula de segmentos vazio/inválido ---
ok("segmentos: [] -> null (sem crash, sem caixa vazia)",
  ExplicacaoPayoff({ segmentos: [], spot: 10, razao: null, cp }) === null);
ok("segmentos: não-array -> null",
  ExplicacaoPayoff({ segmentos: null, spot: 10, razao: null, cp }) === null);
ok("segmentos: undefined -> null",
  ExplicacaoPayoff({ spot: 10, razao: null, cp }) === null);

// ---- (3) montarTexto — spot no meio, inclinação positiva vem PRIMEIRO ----
const segsMeio = [
  { de: 0, ate: 25, inclinacao: "negativa", ePlato: false },
  { de: 25, ate: 30, inclinacao: "positiva", ePlato: false },
  { de: 30, ate: null, inclinacao: "positiva", ePlato: false },
];
const textoMeio = montarTexto(segsMeio, 28, null, cp);
const linhasMeio = textoMeio.split("\n");
ok("spot no segmento do meio (positiva) gera a 1ª linha com o template certo",
  linhasMeio[0] === cp.opcoesExplicSpotPositiva.replace("{spot}", "28,00"));
ok("2ª linha é o segmento ANTERIOR (índice 0, negativa), ordem original preservada",
  linhasMeio[1] === cp.opcoesExplicOutroNegativa.replace("{de}", "0,00").replace("{ate}", "25,00"));
ok("3ª linha é a cauda (índice 2, ate:null, positiva) — usa CAUDA GANHO, nunca o template finito",
  linhasMeio[2] === cp.opcoesExplicOutroCaudaGanho.replace("{de}", "30,00"));
ok("3ª linha NUNCA usa o template finito 'outro positiva' para o segmento de cauda",
  linhasMeio[2] !== cp.opcoesExplicOutroPositiva.replace("{de}", "30,00").replace("{ate}", "—"));

// ---- (4) spot na PRÓPRIA cauda (ate: null, positiva) — cauda ganho, nunca finito
const segsSpotNaCauda = [
  { de: 0, ate: 20, inclinacao: "negativa", ePlato: false },
  { de: 20, ate: null, inclinacao: "positiva", ePlato: false },
];
const textoCauda = montarTexto(segsSpotNaCauda, 25, null, cp);
const linhasCauda = textoCauda.split("\n");
ok("spot na cauda (positiva) usa opcoesExplicSpotCaudaGanho, NUNCA opcoesExplicSpotPositiva",
  linhasCauda[0] === cp.opcoesExplicSpotCaudaGanho.replace("{spot}", "25,00"));
ok("outro segmento (finito, negativa) aparece depois, ordem original",
  linhasCauda[1] === cp.opcoesExplicOutroNegativa.replace("{de}", "0,00").replace("{ate}", "20,00"));

// ---- (5) spot num platô -------------------------------------------------
const segsPlato = [
  { de: 0, ate: 10, inclinacao: "zero", ePlato: true },
  { de: 10, ate: null, inclinacao: "positiva", ePlato: false },
];
const textoPlato = montarTexto(segsPlato, 5, null, cp);
const linhasPlato = textoPlato.split("\n");
ok("spot num platô finito usa opcoesExplicSpotPlato",
  linhasPlato[0] === cp.opcoesExplicSpotPlato.replace("{spot}", "5,00"));
ok("segmento de cauda restante (fora do platô) usa cauda ganho",
  linhasPlato[1] === cp.opcoesExplicOutroCaudaGanho.replace("{de}", "10,00"));

// ---- (6) razão G/P citada como última linha, via formatarRazao (nunca reformatada)
const textoComRazao = montarTexto(segsMeio, 28, { valor: 0.67, motivo: null }, cp);
ok("com razão numérica, a ÚLTIMA linha do texto contém formatarRazao(razao) (\"1 : 0,67\")",
  textoComRazao.endsWith(formatarRazao({ valor: 0.67, motivo: null })));
const textoSemRazao = montarTexto(segsMeio, 28, { valor: null, motivo: "sem breakeven" }, cp);
ok("sem razão numérica (só motivo), a linha da razão NÃO é citada (comportamento restrito ao caso numérico)",
  textoSemRazao.split("\n").length === linhasMeio.length);

// ---- (7) prova de reuso — RazaoGanhoPerda chama formatarRazao(), nunca reformata
const uiOpcoesSrc = readFileSync(join(here, "..", "src", "opcoes", "uiOpcoes.jsx"), "utf8");
const ocorrenciasExpressaoInline = (uiOpcoesSrc.match(/"1 : " \+ fmt\(razao\.valor\)/g) || []).length;
ok("a expressão \"1 : \" + fmt(razao.valor) aparece EXATAMENTE 1 vez em uiOpcoes.jsx (só dentro de formatarRazao)",
  ocorrenciasExpressaoInline === 1);
const ocorrenciasChamada = (uiOpcoesSrc.match(/formatarRazao\(razao\)/g) || []).length;
ok("RazaoGanhoPerda chama formatarRazao(razao) nos dois ramos (numérico e motivo) — reuso real, não só declaração",
  ocorrenciasChamada >= 2);

// ---- (8) guardião de vocabulário banido (EXPL-02) -------------------------
const BANIDO = /strike|prêmio|premio|delta|theta|volatilidade implícita|exercício|rolagem|\bITM\b|\bOTM\b|\bATM\b|perna/i;

const copySrc = readFileSync(join(here, "..", "src", "copy.js"), "utf8");
const linhasExplic = copySrc.split("\n").filter((l) => /^\s*opcoesExplic\w+:/.test(l));
ok("censo: há pelo menos 22 linhas de chave opcoesExplic* em copy.js (11 templates × 2 modos)",
  linhasExplic.length >= 22);
ok("nenhuma linha de template opcoesExplic* usa vocabulário banido",
  linhasExplic.every((l) => !BANIDO.test(l)));
ok("sanidade: o guardião pega uma linha inventada com vocabulário banido ('delta')",
  BANIDO.test('opcoesExplicSpotPositiva: "o delta muda",'));
ok("sanidade: o guardião pega 'perna' isolado",
  BANIDO.test("essa perna vendida"));

const componenteSrc = readFileSync(join(here, "..", "src", "opcoes", "ExplicacaoPayoff.jsx"), "utf8");
const componenteSemComentario = componenteSrc
  .split("\n")
  .filter((l) => !/^\s*(\/\/|\*|\/\*)/.test(l))
  .join("\n");
ok("ExplicacaoPayoff.jsx não usa vocabulário banido fora de comentário",
  !BANIDO.test(componenteSemComentario));

ok("o texto COMPOSTO (montarTexto, caso real acima) não usa vocabulário banido",
  !BANIDO.test(textoMeio) && !BANIDO.test(textoCauda) && !BANIDO.test(textoPlato));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
