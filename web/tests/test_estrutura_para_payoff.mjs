// Fase 31 (Plano 04, D-08) — Guardião do adaptador puro
// `estruturaParaPayoff`: identidade numérica campo a campo (entrada ==
// saída, igualdade ESTRITA — tolerância de ponto flutuante aqui esconderia
// exatamente a conta que o adaptador não pode fazer), `null` seguro, e a
// travessia de `null`+`ilimitado` em max_loss (o "null nunca 0.0" do
// repositório atravessando o adaptador).
//
// Mesmo padrão "static source inspection" da casa (test_payoff_
// responsivo.mjs) para a asserção estática de zero aritmética: regex sobre
// o próprio fonte de `estruturaParaPayoff.js`, sem build e sem DOM.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { estruturaParaPayoff } from "../src/opcoes/estruturaParaPayoff.js";

const here = dirname(fileURLToPath(import.meta.url));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- (1) identidade numérica campo a campo, valores "feios" --------------
const estruturaFeia = {
  pernas: [
    { contrato: "PETRA123", tipo: "CALL", lado: "venda", quantidade: 1, strike: 30.5, premio: 1.23 },
  ],
  custo_liquido: 27.37,
  fluxo: "credito",
  ganho_maximo: 123.456,
  perda_maxima: 65.0,
  ganho_ilimitado: false,
  perda_ilimitada: false,
  breakevens: [28.9],
  delta_total: { valor: 0.5, pernas_sem_delta: 0, motivo: null },
  curva: [
    { preco_objeto: 0, resultado: -27.37 },
    { preco_objeto: 28.9, resultado: 0 },
    { preco_objeto: 40, resultado: 123.456 },
  ],
  unidade: "por unidade do objeto (uma ação); multiplique pelo lote se precisar",
};

const r = estruturaParaPayoff(estruturaFeia, "PETR4");

ok("adaptador devolve objeto não-nulo para entrada válida", r !== null && typeof r === "object");
ok("name === segundo argumento (nome), sem transformação", r.name === "PETR4");
ok("legs === pernas, mesmo array, nenhuma perna alterada",
  Array.isArray(r.legs) && r.legs.length === 1 && r.legs[0] === estruturaFeia.pernas[0]);
ok("payoff tem o mesmo número de pontos que curva",
  Array.isArray(r.payoff) && r.payoff.length === estruturaFeia.curva.length);
ok("payoff[i].underlying === curva[i].preco_objeto (identidade estrita, todos os pontos)",
  r.payoff.every((p, i) => p.underlying === estruturaFeia.curva[i].preco_objeto));
ok("payoff[i].result === curva[i].resultado (identidade estrita, todos os pontos)",
  r.payoff.every((p, i) => p.result === estruturaFeia.curva[i].resultado));
ok("breakevens === breakevens, identidade estrita",
  Array.isArray(r.breakevens) && r.breakevens.length === 1 && r.breakevens[0] === 28.9);
ok("net_cost === custo_liquido, identidade estrita (27.37, sem arredondar)",
  r.net_cost === 27.37);
ok("max_gain === ganho_maximo, identidade estrita (123.456, sem arredondar)",
  r.max_gain === 123.456);
ok("max_loss === perda_maxima, identidade estrita (65.0)",
  r.max_loss === 65.0);
ok("unlimited_gain === ganho_ilimitado (false)",
  r.unlimited_gain === false);
ok("unlimited_loss === perda_ilimitada (false)",
  r.unlimited_loss === false);
ok("scenarios NÃO existe no envelope de saída (o motor interno não produz cenários)",
  !("scenarios" in r));

// ---- (2) entrada null/inválida -> null, nunca lança -----------------------
ok("estrutura null -> null", estruturaParaPayoff(null, "PETR4") === null);
ok("estrutura undefined -> null", estruturaParaPayoff(undefined, "PETR4") === null);
ok("estrutura não-objeto (string) -> null", estruturaParaPayoff("nao é objeto", "PETR4") === null);
ok("estrutura sem curva -> null", estruturaParaPayoff({ custo_liquido: 1 }, "PETR4") === null);
ok("estrutura com curva não-array -> null",
  estruturaParaPayoff({ curva: "nao é array" }, "PETR4") === null);
ok("estrutura com curva de 1 ponto -> null (menos de 2 pontos não desenha nada)",
  estruturaParaPayoff({ curva: [{ preco_objeto: 0, resultado: 0 }] }, "PETR4") === null);
ok("estrutura com curva vazia -> null",
  estruturaParaPayoff({ curva: [] }, "PETR4") === null);

// ---- (3) perda_maxima: null + perda_ilimitada: true -> max_loss: null + unlimited_loss: true
const estruturaIlimitada = {
  pernas: [],
  custo_liquido: 5,
  ganho_maximo: 10,
  perda_maxima: null,
  ganho_ilimitado: false,
  perda_ilimitada: true,
  breakevens: [],
  curva: [
    { preco_objeto: 0, resultado: 0 },
    { preco_objeto: 10, resultado: -50 },
  ],
};
const rIlimitada = estruturaParaPayoff(estruturaIlimitada, "VALE3");
ok("perda_maxima: null atravessa como max_loss: null (nunca 0, princípio 4 do CLAUDE.md)",
  rIlimitada !== null && rIlimitada.max_loss === null);
ok("perda_ilimitada: true atravessa como unlimited_loss: true",
  rIlimitada.unlimited_loss === true);

// ---- (4) sanidade: o array de curva original não é mutado -----------------
const curvaOriginal = JSON.stringify(estruturaFeia.curva);
estruturaParaPayoff(estruturaFeia, "PETR4");
ok("a chamada não muta o objeto estrutura de entrada",
  JSON.stringify(estruturaFeia.curva) === curvaOriginal);

// ---- (5) asserção estática: zero aritmética sobre os campos financeiros --
// Mesma técnica de test_payoff_responsivo.mjs (ARITMETICA_FINANCEIRA) —
// regex sobre o próprio fonte do arquivo, sem build. Cobre os nomes PT
// (entrada) e os nomes inglês (saída), porque a proibição vale nos dois
// sentidos: nem o valor de entrada nem o de saída podem ser recalculados.
const caminhoAdaptador = join(here, "..", "src", "opcoes", "estruturaParaPayoff.js");
const fonteAdaptador = readFileSync(caminhoAdaptador, "utf8");
// Filtra linhas de comentário (mesma higiene de test_curadoria_ui.mjs):
// sem isso, o próprio parágrafo do cabeçalho que EXPLICA a proibição
// reprovaria a si mesmo.
const fonteSemComentario = fonteAdaptador
  .split("\n")
  .filter((l) => !/^\s*(\/\/|\*|\/\*)/.test(l))
  .join("\n");
const CAMPOS_FINANCEIROS = [
  "custo_liquido", "ganho_maximo", "perda_maxima", "preco_objeto", "resultado",
  "net_cost", "max_gain", "max_loss",
];
const ARITMETICA_FINANCEIRA = new RegExp(
  `(${CAMPOS_FINANCEIROS.join("|")})\\s*[*/+-]\\s*[\\w.]` +
  `|[\\w.]\\s*[*/+-]\\s*(?:\\w+\\.)?(${CAMPOS_FINANCEIROS.join("|")})`
);
ok("nenhuma aritmética sobre os campos financeiros no fonte do adaptador (exibe/renomeia, não calcula)",
  !ARITMETICA_FINANCEIRA.test(fonteSemComentario));
ok("sanidade: a regex de aritmética financeira pega uma conta inventada (net_cost * 100)",
  ARITMETICA_FINANCEIRA.test("const emCentavos = r.net_cost * 100;"));
ok("sanidade: a regex de aritmética financeira pega a mesma conta com o operador antes (100 * custo_liquido)",
  ARITMETICA_FINANCEIRA.test("const x = 100 * estrutura.custo_liquido;"));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
