// Fase 27, plano 27-05 (2026-09-13) — O CUSTO DECLARADO DE CADA CONTROLE DA
// ABA OPÇÕES, CRUZADO COM O `_cap_check` QUE O BACKEND COBRA.
//
// **O defeito que este arquivo fecha.** Até o 27-05, sete dos oito controles da
// aba gastavam cota sem dizer quanto, e o oitavo — a leitura do serviço, a
// chamada mais cara depois de `/possibilidades` — nem controle tinha: saía
// sozinha na troca de ativo, o que com o bloco "Seus vigias" (27-02) virou
// "clicar num vigia custa 3 chamadas e nada na tela avisa". É o critério 4 do
// ROADMAP, e ele era falso.
//
// **Por que o guardião precisa ler os DOIS lados.** O número do custo vive em
// dois lugares por necessidade: a tela precisa dizer o preço ANTES de perguntar
// ao servidor (perguntar quanto custa seria uma chamada para saber o preço de
// uma chamada) e quem cobra de verdade é o backend. Um rótulo redigitado à mão
// envelheceria em SILÊNCIO no dia em que o `_cap_check` de uma rota mudasse — e
// custo declarado errado é pior que custo nenhum, porque é crível. Então este
// arquivo lê a tabela `CUSTO_DA_ACAO` do fonte do front E os `_cap_check(uid, N)`
// do fonte Python, e reprova a suíte quando os dois discordam.
//
// **Por que o mapa abaixo é EXPLÍCITO e não um cruzamento por nome.** Os nomes
// não coincidem, e nunca vão coincidir: `mcpSetupsListar` → `listarVigias`,
// `mcpSetupGrafico` → `grafico`, `mcpSetupCompilar` → `compilar`. Um guardião
// "esperto" que casasse por prefixo passaria a não ver justamente as três
// entradas de nome diferente.
//
// **Por que a cobertura é DERIVADA do fonte do hook.** Uma lista fixa de
// métodos protegeria só o que já existe. O modo de falha aqui é silencioso —
// uma chamada nova que ninguém classificou não quebra nada na tela, só aparece
// no contador da pessoa no fim do dia. Então a lista de chamadas sai do próprio
// `useOpcoesMcp.js`, e método novo sem classificação reprova a suíte.
//
// Roda sem build e sem servidor: `node web/tests/test_opcoes_custo_declarado.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");
const ler = (p) => readFileSync(p, "utf8");

// Sem comentários: eles CITAM os nomes dos métodos e os `_cap_check` ao
// explicar as decisões (a tabela do front tem um comentário de rota por linha),
// e contá-los faria o guardião se auto-invalidar.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").map((l) => l.replace(/\/\/.*$/, "")).join("\n");

const telaBruta = ler(join(dirOpcoes, "OpcoesScreen.jsx"));
const criarBruto = ler(join(dirOpcoes, "CriarSetup.jsx"));
const tela = semComentario(telaBruta);
const criar = semComentario(criarBruto);
const hook = semComentario(ler(join(dirOpcoes, "useOpcoesMcp.js")));
const py = ler(join(here, "..", "..", "server", "app", "options_mcp_api.py"));

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// ---------------------------------------------------------------- o mapa ----
// Método do store (o que o hook chama) → chave em `CUSTO_DA_ACAO` (o que a tela
// declara) → função da rota em `options_mcp_api.py` (quem cobra).
const ACOES = {
  mcpLeitura:        { chave: "leitura",      rota: "leitura" },
  mcpCadeia:         { chave: "cadeia",       rota: "cadeia" },
  mcpOperaveis:      { chave: "operaveis",    rota: "operaveis" },
  mcpProposta:       { chave: "proposta",     rota: "proposta" },
  mcpSetupGrafico:   { chave: "grafico",      rota: "setup_grafico" },
  mcpSetupCompilar:  { chave: "compilar",     rota: "setup_compilar" },
  mcpSetupConfirmar: { chave: "confirmar",    rota: "setup_confirmar" },
  mcpSetupDesativar: { chave: "desativar",    rota: "setup_desativar" },
  mcpSetupsListar:   { chave: "listarVigias", rota: "setups_listar" },
};
// Custo CALCULADO na tela (`2 * N + 1`, N = vencimentos escolhidos): não cabe
// numa tabela de constantes, e já é declarado no próprio controle desde a F3.
const CALCULADO = ["mcpPossibilidades"];
// Custo SEM controle: o frescor do cabeçalho sai no mount e reserva 1 (vira 0
// quando o cache responde). Não vira clique — o gate de frescor precisa existir
// na abertura (ADR-027, Decisão 8) —, então o que resta é DECLARAR, e é isso
// que a asserção da seção 6 exige.
const SEM_CONTROLE = ["mcpStatus"];
// Custo ZERO por contrato da rota: índice local de vigias (27-01) e leitura
// técnica interna (27-03). Proibidos na tabela: declarar custo onde não há
// custo mente para o outro lado.
const SEM_CUSTO = ["mcpVigias", "opcoesTecnico"];

// ------------------------------------ 1) cobertura: nada fica sem classificação
const chamadasDoHook = [...new Set(
  [...hook.matchAll(/store\.([A-Za-z0-9_]+)/g)].map((m) => m[1]))].sort();
ok("sanidade: a extração acha as chamadas de store no hook (senão tudo passaria vazio)",
   chamadasDoHook.length >= 10, `achou ${chamadasDoHook.length}`);
ok("sanidade: a extração enxerga método SEM o prefixo `mcp` (rota barata nasce fora dele)",
   chamadasDoHook.some((m) => !/^mcp/.test(m)));
const classificado = new Set([
  ...Object.keys(ACOES), ...CALCULADO, ...SEM_CONTROLE, ...SEM_CUSTO,
]);
for (const m of chamadasDoHook) {
  ok(`store.${m} está classificado (ACOES | CALCULADO | SEM_CONTROLE | SEM_CUSTO)`,
     classificado.has(m),
     "chamada nova sem custo declarado é o modo de falha silencioso que este arquivo existe para pegar");
}
// O lado inverso: uma classificação que não corresponde a chamada nenhuma é
// entrada morta, e entrada morta vira permissão que ninguém revoga.
for (const m of classificado) {
  ok(`a classificação de ${m} corresponde a uma chamada real do hook`,
     chamadasDoHook.includes(m));
}

// -------------------------------- 2) a tabela do front, lida do próprio fonte
const mTabela = tela.match(/const CUSTO_DA_ACAO = \{([\s\S]*?)\n\};/);
ok("a tela declara a tabela CUSTO_DA_ACAO", !!mTabela);
const CUSTO_DA_ACAO = {};
if (mTabela) {
  for (const m of mTabela[1].matchAll(/([A-Za-z0-9_]+)\s*:\s*(\d+)\s*,/g)) {
    CUSTO_DA_ACAO[m[1]] = Number(m[2]);
  }
}
ok("sanidade: a leitura da tabela devolve as NOVE entradas do mapa",
   Object.keys(CUSTO_DA_ACAO).length === Object.keys(ACOES).length,
   `leu ${Object.keys(CUSTO_DA_ACAO).length}`);

// --------------------------------- 3) front × tabela: toda ação tem entrada
for (const [metodo, { chave }] of Object.entries(ACOES)) {
  ok(`CUSTO_DA_ACAO declara a chave ${chave} (de store.${metodo})`,
     typeof CUSTO_DA_ACAO[chave] === "number");
}

// --------------------------- 4) tabela × backend: o número é o que se cobra
// Corpo da rota = do `async def <rota>(` até o próximo `def`/`async def` em
// coluna zero. O primeiro `_cap_check(uid, N)` do corpo é a reserva da chamada.
const capDaRota = (rota) => {
  const i = py.indexOf(`async def ${rota}(`);
  if (i < 0) return null;
  const resto = py.slice(i + 1);
  const fim = resto.search(/\n(?:async )?def /);
  const corpo = fim >= 0 ? resto.slice(0, fim) : resto;
  const m = corpo.match(/_cap_check\(uid,\s*(\d+)\)/);
  return m ? Number(m[1]) : null;
};
const capDe = Object.fromEntries(
  Object.values(ACOES).map(({ rota }) => [rota, capDaRota(rota)]));
// SANIDADE OBRIGATÓRIA: o extrator precisa achar as NOVE rotas. Sem ela, uma
// rota renomeada no backend viraria "nada a conferir" e a seção inteira
// passaria por vacuidade — que é o contrário do que se quer, já que renomear
// rota é exatamente quando o espelho do front tende a envelhecer.
const achadas = Object.values(capDe).filter((n) => typeof n === "number").length;
ok("sanidade: o extrator achou o _cap_check das NOVE rotas em options_mcp_api.py",
   achadas === Object.keys(ACOES).length,
   `achou ${achadas} de ${Object.keys(ACOES).length}`);
for (const [metodo, { chave, rota }] of Object.entries(ACOES)) {
  ok(`${chave}: a tela declara ${CUSTO_DA_ACAO[chave]} e a rota ${rota} cobra ${capDe[rota]}`,
     typeof capDe[rota] === "number" && CUSTO_DA_ACAO[chave] === capDe[rota],
     `espelho divergente — o front mentiria o preço de store.${metodo}`);
}

// --------------------------------- 5) custo zero NÃO se declara na tabela
for (const m of SEM_CUSTO) {
  const chaveProvavel = m.replace(/^mcp/, "").replace(/^./, (c) => c.toLowerCase());
  ok(`${m} (custo 0 por contrato da rota) fica fora de CUSTO_DA_ACAO`,
     !(m in CUSTO_DA_ACAO) && !(chaveProvavel in CUSTO_DA_ACAO));
}

// ------------------ 6) o custo SEM controle é declarado em algum lugar
// `mcpStatus` não tem botão. Um custo sem controle E sem declaração é o pior
// dos casos: a pessoa vê o contador andar e não tem onde ler o porquê.
ok("o cabeçalho declara o custo do frescor (cp.opcoesCustoFrescor)",
   /cp\.opcoesCustoFrescor/.test(tela));
for (const modo of ["estudo", "operador"]) {
  ok(`COPY.${modo}.opcoesCustoFrescor existe e não é vazio`,
     typeof COPY[modo].opcoesCustoFrescor === "string"
     && !!COPY[modo].opcoesCustoFrescor.trim());
}
// O número da frase ("até 1 chamada") é espelho da reserva da rota `status`.
// Se o backend passar a reservar 2, este assert fica vermelho antes de o texto
// da tela virar mentira.
const capStatus = capDaRota("status");
ok("a rota status reserva 1 chamada (é o `até 1` que o cabeçalho declara)",
   capStatus === 1, `a rota reserva ${capStatus}`);
for (const modo of ["estudo", "operador"]) {
  ok(`${modo}: a frase do frescor diz o número e diz que pode ser zero`,
     /\b1\b/.test(COPY[modo].opcoesCustoFrescor)
     && /cache/i.test(COPY[modo].opcoesCustoFrescor));
}

// ---------------------- 7) o custo CALCULADO tem rótulo, e é expressão
ok("o custo de /possibilidades é derivado (2 * N + 1), não um literal",
   /const chamadasPrevistas = 2 \* N \+ 1;/.test(tela));
ok("e ele chega ao controle pela mesma função de copy",
   /opcoesCustoChamadas[\s\S]{0,80}\(chamadasPrevistas\)/.test(tela));
ok("mcpPossibilidades continua FORA da tabela (o custo dela não é constante)",
   !("possibilidades" in CUSTO_DA_ACAO));

// ------------------------------ 8) TODO controle da tabela tem rótulo na tela
// Forma canônica ÚNICA: `opcoesCustoChamadas(...)`. Duas maneiras de dizer a
// mesma coisa divergem na primeira manutenção feita só numa delas — por isso a
// busca é pela função, e não por "algum texto com o número".
const linhasDeCusto = [...tela.split("\n"), ...criar.split("\n")]
  .filter((l) => l.includes("opcoesCustoChamadas"));
ok("sanidade: há declarações de custo suficientes para cobrir os controles",
   linhasDeCusto.length >= Object.keys(ACOES).length,
   `achou ${linhasDeCusto.length} linha(s)`);
const declara = (chave) => linhasDeCusto.some((l) =>
  l.includes("CUSTO_DA_ACAO." + chave) || l.includes('"' + chave + '"'));
for (const chave of Object.keys(CUSTO_DA_ACAO)) {
  ok(`o controle de ${chave} declara o custo com cp.opcoesCustoChamadas`,
     declara(chave));
}
ok("sanidade: a busca por rótulo NÃO acha uma chave inexistente",
   !declara("chaveQueNaoExiste"));

// ------------- 9) o segundo eixo de custo do compilar (cota de IA) é dito
// `setup_compilar` é o único controle com custo em DOIS eixos: 2 chamadas do
// cap E uma análise da cota de IA (`consumir_analise()`), que tem teto próprio
// e tela própria. Declarar só o primeiro faria o segundo sumir justamente do
// controle que o consome.
ok("o backend do compilar consome uma análise de IA além do cap",
   /consumir_analise\(/.test(py));
ok("o botão de compilar declara o segundo eixo (cp.opcoesCustoAnaliseIA)",
   /opcoesCustoAnaliseIA/.test(criar));
for (const modo of ["estudo", "operador"]) {
  const t = COPY[modo].opcoesCustoAnaliseIA;
  ok(`COPY.${modo}.opcoesCustoAnaliseIA existe e nomeia a análise`,
     typeof t === "string" && /an[áa]lise/i.test(t));
  // Sem número: o teto real vive no gate do `metering` e tem tela própria. Um
  // número redigitado aqui envelheceria em silêncio na próxima mudança de plano.
  ok(`${modo}: a frase da IA não crava o teto da cota`, !/\d+\s*(análises|por dia)/i.test(t));
}

// -------------------------------- 10) a forma de dizer custo é UMA só
// Um segundo vocabulário ("gasta N créditos", "custa N consultas") reabriria o
// defeito pelo outro lado: dois textos para a mesma grandeza divergem, e a
// pessoa passa a não saber qual dos dois é o preço.
for (const modo of ["estudo", "operador"]) {
  ok(`COPY.${modo}.opcoesCustoChamadas é função e tolera nulo`,
     typeof COPY[modo].opcoesCustoChamadas === "function"
     && typeof COPY[modo].opcoesCustoChamadas(null) === "string");
  ok(`${modo}: custo desconhecido vira travessão, nunca um número chutado`,
     !/\d/.test(COPY[modo].opcoesCustoChamadas(null)));
}
// A queda de `CriarSetup` também não inventa número quando a prop não chega.
ok("CriarSetup lê o custo da prop e cai para null (nunca um literal)",
   /const custoDe = \(custos, chave\) => \(custos && typeof custos\[chave\] === "number"/.test(criar));
ok("a tabela chega ao CriarSetup e ao BotaoDesativar por PROP",
   (tela.match(/custos=\{CUSTO_DA_ACAO\}/g) || []).length >= 2);
ok("CriarSetup.jsx não importa a tabela de OpcoesScreen.jsx (seria ciclo)",
   !/from\s+["'][^"']*OpcoesScreen\.jsx["']/.test(criarBruto));

console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
