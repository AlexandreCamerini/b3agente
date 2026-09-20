// Fase 27, plano 27-04 (2026-09-13) — guardião da LEITURA TÉCNICA INTERNA da
// aba Opções e da RÉGUA DE REGIME.
//
// Cada seção nomeia o defeito que ela reprova. Nenhuma delas é decorativa:
//
//  1. **A régua importando `App.jsx`** — ciclo de import (App.jsx importa a
//     aba). O app quebra no boot, não na régua.
//  2. **Um quinto regime nascendo no backend sem cor na tela** — o segmento
//     ficaria com a cor do `indefinido` e mentiria sobre o estado medido. Por
//     isso a lista dos regimes é DERIVADA de `server/app/regime.py`, nunca
//     redigitada aqui (padrão estabelecido na Fase 26: guardião que repete o
//     texto que trava envelhece junto com ele).
//  3. **Hex literal na régua** — cor fora do Brand Book v2, invisível para
//     `test_brand_book_v2_tokens.mjs` (que só lê `App.jsx`).
//  4. **Informação só na cor** — quem não distingue verde de vermelho perde
//     o dado inteiro (princípio 10 do CLAUDE.md).
//  5. **A ARMADILHA DE UNIDADE (correção C6 do plano)** — `hv21Pct` do motor
//     interno vem em PERCENTUAL (31,4) e `behavior.hv21` do serviço MCP vem
//     em FRAÇÃO (0,314). Os dois ficam no MESMO ecrã. Passar um pelo
//     formatador do outro erra por 10× em silêncio, com o mesmo rótulo na
//     tela ("HV 21") e sem nenhum teste vermelho. Aqui a função é
//     EXERCITADA, não grepada — é a diferença entre teste permanente e
//     conferência de uma vez só.
//  6. **Duas réguas de regime (correção C7)** — a tela derivando regime por
//     conta própria produziria um veredito diferente do da linha de
//     tendência logo acima, sobre o MESMO dia e na MESMA tela. O oráculo de
//     VALOR dessa concordância é do backend (`test_opcoes_tecnico.py`, 27-03:
//     o último item da régua é idêntico a `classificar(snap)`); o que se
//     tranca aqui é que a tela não introduza uma terceira régua.
//  7. **Selo "grátis" escrito à mão** — o dia em que a rota passar a custar,
//     ele continuaria dizendo que é de graça (T-27-19).
//  8. **Custo disparando por efeito** — a leitura interna pode sair sozinha
//     SÓ porque declara `custoMcp: 0`; o período dela é fixo porque dois
//     períodos na mesma tela dariam duas leituras do mesmo dia.
//
// Roda sem build: `node web/tests/test_opcoes_leitura_interna_ui.mjs`.
import { readFileSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";
import { formatarVolatilidade, UNIDADES } from "../src/opcoes/unidades.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");
const ler = (p) => readFileSync(p, "utf8");

// Sem comentários: eles citam os mesmos termos ao EXPLICAR as decisões
// ("não passe `hv21Pct` por `fracPct`"), e contá-los faria o guardião se
// auto-invalidar.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");

const bruteRegua = ler(join(dirOpcoes, "ReguaRegime.jsx"));
const regua = semComentario(bruteRegua);
const bruteTela = ler(join(dirOpcoes, "OpcoesScreen.jsx"));
const tela = semComentario(bruteTela);
const hook = semComentario(ler(join(dirOpcoes, "useOpcoesMcp.js")));
// 2026-09-20, Fase 33 (33-05): job 3 ("LEITURA DO ATIVO", os campos hv21/hv63
// do serviço MCP que passam por `fracPct`) saiu de OpcoesScreen.jsx para
// SecaoAnalisar.jsx — a seção 5b (achado além do censo do plano, achado ao
// rodar a suíte completa) precisa ler esta fonte também, senão a sanidade
// "há uso de fracPct" passa por vacuidade (nenhum uso sobrou em `tela`).
const secaoAnalisar = semComentario(ler(join(dirOpcoes, "SecaoAnalisar.jsx")));
const regimePy = ler(join(here, "..", "..", "server", "app", "regime.py"));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) a régua existe, sem ciclo, com tokens locais -----------------------
ok("ReguaRegime.jsx exporta um componente default",
   /export default function ReguaRegime\(/.test(regua));
ok("ReguaRegime.jsx NÃO importa App.jsx (seria ciclo)",
   !/from\s+["'][^"']*App\.jsx["']/.test(bruteRegua));
ok("ReguaRegime.jsx declara o bloco VARKEY/TOKENS/T local",
   /const VARKEY = /.test(regua) && /const TOKENS = \[/.test(regua)
   && /const T = Object\.fromEntries/.test(regua));
ok("ReguaRegime.jsx não usa hex literal (só tokens do Brand Book v2)",
   !/#[0-9a-fA-F]{3,8}\b/.test(bruteRegua));
ok("sanidade: a regex de hex pega o padrão quando ele existe",
   /#[0-9a-fA-F]{3,8}\b/.test('const c = "#34d399";'));

// ---- 2) CORES_DO_REGIME cobre EXATAMENTE os regimes do backend ------------
// DERIVADO da fonte: `server/app/regime.py` é quem define quantos regimes
// existem. Redigitar a lista aqui faria o guardião passar verde no dia em que
// o backend ganhasse um quinto — e o segmento novo cairia na cor do
// `indefinido` sem ninguém ver.
const mRegimes = regimePy.match(/REGIMES\s*=\s*\(([\s\S]*?)\)/);
const REGIMES = mRegimes ? [...mRegimes[1].matchAll(/"([a-z_]+)"/g)].map((m) => m[1]) : [];
ok("a tupla REGIMES foi extraída de server/app/regime.py", REGIMES.length >= 3);
const mCores = regua.match(/CORES_DO_REGIME\s*=\s*\{([\s\S]*?)\}/);
const CORES = mCores ? [...mCores[1].matchAll(/(\w+)\s*:/g)].map((m) => m[1]) : [];
ok("CORES_DO_REGIME foi extraída do fonte da régua", CORES.length >= 3);
ok("CORES_DO_REGIME cobre EXATAMENTE os regimes de regime.py",
   JSON.stringify([...REGIMES].sort()) === JSON.stringify([...CORES].sort()));
// A tabela de rótulos tem de acompanhar o mesmo conjunto: um regime sem
// rótulo apareceria como travessão no lugar do estado que o motor mediu.
for (const modo of ["estudo", "operador"]) {
  const rot = COPY[modo].opcoesRegimeRotulo || {};
  ok(`${modo}: opcoesRegimeRotulo cobre EXATAMENTE os regimes de regime.py`,
     JSON.stringify([...REGIMES].sort()) === JSON.stringify(Object.keys(rot).sort()));
}
// Cor NOVA é o outro lado do mesmo defeito: a tabela só pode apontar para
// token que o bloco local declara.
const mTokens = regua.match(/const TOKENS = \[([\s\S]*?)\]/);
const TOKENS_DECLARADOS = mTokens ? [...mTokens[1].matchAll(/"(\w+)"/g)].map((m) => m[1]) : [];
const CORES_USADAS = mCores ? [...mCores[1].matchAll(/:\s*"(\w+)"/g)].map((m) => m[1]) : [];
ok("as cores extraídas da tabela foram lidas", CORES_USADAS.length === CORES.length);
ok("toda cor da tabela é um token declarado no bloco local (nenhuma cor nova)",
   CORES_USADAS.every((t) => TOKENS_DECLARADOS.includes(t)));

// ---- 3) a informação existe em TEXTO, não só em cor -----------------------
ok("a faixa é uma lista acessível (role=list + role=listitem)",
   /role="list"/.test(regua) && /role="listitem"/.test(regua));
ok("todo segmento carrega aria-label E title (leitor de tela e toque longo)",
   /role="listitem"[^>]*title=\{[^}]*\}[^>]*aria-label=\{/.test(regua));
ok("o rótulo do segmento nomeia dia, regime e força",
   /const descricao = \(item\) =>/.test(regua)
   && /diaCurto\(item && item\.data\)/.test(regua)
   && /rotuloRegime\(item && item\.regime\)/.test(regua)
   && /rotuloForca\(item && item\.forca\)/.test(regua));
ok("o segmento de hoje é destacado por BORDA, não só por cor",
   /item && item\.hoje[\s\S]{0,80}solid \$\{T\.accent\}/.test(regua));
ok("confiabilidade baixa muda a opacidade E entra no rótulo em texto",
   /opacity: incerto \? /.test(regua)
   && /confiavel === false && c\.opcoesRegimeNaoConfiavel/.test(regua));
ok("o rótulo do dia aparece abaixo da faixa (item.data, formatado)",
   /\{diaCurto\(item && item\.data\)\}/.test(regua));
ok("data fora do formato conhecido sai COMO VEIO, nunca virando a data de hoje",
   /return s \|\| "—";/.test(regua) && !/new Date\(/.test(regua));

// ---- 4) régua vazia NÃO é desenhada ---------------------------------------
ok("itens vazio devolve null (7 segmentos \"indefinido\" seriam outra afirmação)",
   /if \(!itens\.length\) return null;/.test(regua));
ok("o motivo da régua vai VERBATIM no rodapé da faixa",
   /regua && regua\.motivo \?/.test(regua) && /\{regua\.motivo\}/.test(regua));
ok("sem segmento, quem fala é o bloco pai, com a chave própria",
   /temRegua \?/.test(tela) && /c\.opcoesReguaSemDados/.test(tela)
   && /motivoDaRegua/.test(tela));

// ---- 5) A ARMADILHA DE UNIDADE (C6) ---------------------------------------
// 5a) a função é EXERCITADA, não grepada.
const a = formatarVolatilidade(31, UNIDADES.pct);
const b = formatarVolatilidade(0.31, UNIDADES.frac);
ok("31 em \"pct\" e 0,31 em \"frac\" dão o MESMO texto", a === b && /\d/.test(a));
ok("31 em \"frac\" NÃO dá o mesmo texto (é o erro de 10×, e ele é visível)",
   formatarVolatilidade(31, UNIDADES.frac) !== a);
const desconhecida = formatarVolatilidade(31, "percent");
ok("unidade desconhecida vira travessão SEM dígito nenhum (nunca um palpite)",
   !/\d/.test(desconhecida) && desconhecida.includes("—"));
ok("unidade ausente (undefined/null/\"\") também não vira número",
   [undefined, null, ""].every((u) => !/\d/.test(formatarVolatilidade(31, u))));
ok("valor ausente vira travessão, nunca 0",
   [null, undefined, NaN].every((v) => formatarVolatilidade(v, UNIDADES.pct) === "—"));

// 5b) lado NEGATIVO: nenhum campo de `tecnico.dados` passa por `fracPct`.
// `fracPct` multiplica por 100 — é o conversor do contrato do SERVIÇO, que
// manda fração. Sobre um campo que já vem em percentual, ele erra por 10×.
const ARG_INTERNO = /^(tecnico|dados)\b|hv21Pct|hv63Pct|atr14Pct/;
const usosFracPct = [
  ...tela.matchAll(/fracPct\(([^)]*)\)/g),
  ...secaoAnalisar.matchAll(/fracPct\(([^)]*)\)/g),
].map((m) => m[1].trim());
ok("há uso de fracPct em OpcoesScreen.jsx/SecaoAnalisar.jsx (o guardião não está vazio)", usosFracPct.length >= 1);
ok("nenhum fracPct recebe campo do bloco interno (unidade trocada = 10×)",
   usosFracPct.every((arg) => !ARG_INTERNO.test(arg)));
ok("sanidade: o teste de argumento REPROVA o campo interno quando ele aparece",
   ARG_INTERNO.test("vol.hv21Pct") && ARG_INTERNO.test("tecnico.dados.volatilidade.hv21Pct")
   && !ARG_INTERNO.test("behavior.hv21"));

// 5c) lado POSITIVO — sem ele a asserção acima passa por vacuidade (basta não
// exibir volatilidade nenhuma). TODA chamada do formatador lê a unidade do
// PRÓPRIO DADO; string literal no segundo argumento é o mesmo defeito escrito
// de outro jeito, porque volta a fixar a escala no front.
const usosFmt = [...tela.matchAll(/formatarVolatilidade\(([^)]*)\)/g)]
  .map((m) => m[1].split(",").map((s) => s.trim()));
ok("a tela usa o formatador em ao menos DUAS linhas (HV 21 e HV 63)", usosFmt.length >= 2);
ok("TODA chamada lê a unidade do próprio dado (nunca uma string literal)",
   usosFmt.every((args) => args.length >= 2 && /\.unidade$/.test(args[1])));
ok("a tela importa o formatador do módulo puro",
   /import \{ formatarVolatilidade \} from "\.\/unidades\.js";/.test(bruteTela));
ok("o módulo de unidades é .js (importável por node) e não .jsx",
   readdirSync(dirOpcoes).includes("unidades.js"));

// ---- 6) CONCORDÂNCIA régua × linha de tendência (C7) -----------------------
ok("a régua é renderizada dentro do bloco interno, lendo dados.regua",
   /<ReguaRegime[^>]*regua=\{dados\.regua\}/.test(tela));
ok("a linha de tendência lê dados.tendencia — a MESMA resposta, classificada uma vez só",
   /const tend = \(dados && dados\.tendencia\) \|\| \{\};/.test(tela)
   && /\(c\.opcoesRegimeRotulo \|\| \{\}\)\[tend\.regime\]/.test(tela));
ok("o bloco interno lê o trio `tecnico` do hook",
   /<LeituraInterna tecnico=\{tecnico\} cp=\{cp\} \/>/.test(tela)
   && /function LeituraInterna\(\{ tecnico, cp \}\)/.test(tela));
// Nenhuma terceira régua: a tela não compara preço com média nem lê limiar de
// ADX. Quem classifica é `regime.classificar`, no backend, uma vez por pregão.
const DERIVA_REGIME = /\b(close|fechamento)\s*[<>]=?[^;\n]*sma|\bsma\d*\s*[<>]=?[^;\n]*(close|fechamento)|\badx\w*\s*[<>]=?\s*\d/i;
for (const arq of readdirSync(dirOpcoes).filter((f) => /\.(js|jsx)$/.test(f))) {
  ok(`${arq} não deriva regime por conta própria (sem segunda régua no front)`,
     !DERIVA_REGIME.test(semComentario(ler(join(dirOpcoes, arq)))));
}
ok("sanidade: a regex de derivação pega o padrão quando ele existe",
   DERIVA_REGIME.test("const alta = close > summary.sma200;")
   && DERIVA_REGIME.test("if (adx14 >= 20) forca = 'forte';"));

// ---- 7) o selo de gratuidade é DERIVADO, nunca escrito ---------------------
ok("o selo sai de `custoMcp === 0` da resposta (T-27-19)",
   /const semCusto = !!dados && dados\.custoMcp === 0;/.test(tela)
   && /\{semCusto \? \(/.test(tela));
ok("o texto do selo vem do copy, nos dois modos",
   /c\.opcoesSemCusto/.test(tela)
   && !!COPY.estudo.opcoesSemCusto && !!COPY.operador.opcoesSemCusto);
ok("os dois modos declaram gratuidade no selo",
   /gr[áa]tis/i.test(COPY.estudo.opcoesSemCusto)
   && /gr[áa]tis/i.test(COPY.operador.opcoesSemCusto));

// ---- 8) custo zero e período FIXO no hook ---------------------------------
ok("o período da leitura é constante NOMEADA, não implícito no backend",
   /const PERIODO_DA_LEITURA = "/.test(hook)
   && /\{ period: PERIODO_DA_LEITURA \}/.test(hook));
ok("o método do store tem UMA porta no efeito (guard sobre a referência)",
   (hook.match(/store\.opcoesTecnico/g) || []).length === 1);
ok("a leitura interna dispara na troca de ticker (é o que a torna imediata)",
   /\}, \[store, ticker\]\);/.test(hook));
ok("o trio `tecnico` é exportado pelo hook", /\n    tecnico,\n/.test(hook));

// ---- 9) as chaves novas existem nos DOIS modos ----------------------------
const CHAVES = ["opcoesInternaTitulo", "opcoesInternaCarimbo", "opcoesInternaCarregando",
  "opcoesInternaErro", "opcoesSemCusto", "opcoesRegimeRotulo", "opcoesForcaRotulo",
  "opcoesRegimeNaoConfiavel", "opcoesReguaTitulo", "opcoesReguaAjuda", "opcoesReguaSemDados"];
for (const k of CHAVES) {
  ok(`COPY tem ${k} nos dois modos`, !!COPY.estudo[k] && !!COPY.operador[k]);
}
for (const modo of ["estudo", "operador"]) {
  const carimbo = COPY[modo].opcoesInternaCarimbo;
  ok(`${modo}: o carimbo é função e tolera ausência dos dois argumentos`,
     typeof carimbo === "function" && typeof carimbo(null, null) === "string");
  // Fonte ausente NUNCA vira um nome de fonte por default — é o mesmo defeito
  // que o cabeçalho da aba já corrigiu ("Fonte: —").
  ok(`${modo}: sem fonte declarada, o carimbo mostra travessão`,
     carimbo(null, null).includes("—"));
  ok(`${modo}: o carimbo nomeia o pregão da leitura`,
     /preg[ãa]o/i.test(carimbo("2026-09-11", "brapi")) && carimbo("2026-09-11", "brapi").includes("2026-09-11"));
  ok(`${modo}: a ajuda da régua nega previsão explicitamente`,
     /previs/i.test(COPY[modo].opcoesReguaAjuda) && /medid/i.test(COPY[modo].opcoesReguaAjuda));
  ok(`${modo}: a ressalva de confiabilidade nomeia as duas janelas`,
     /200/.test(COPY[modo].opcoesRegimeNaoConfiavel) && /50/.test(COPY[modo].opcoesRegimeNaoConfiavel));
}
const chaves = (m) => Object.keys(COPY[m]).filter((k) => k.startsWith("opcoes")).sort();
ok("o conjunto de chaves `opcoes*` continua idêntico nos dois modos",
   JSON.stringify(chaves("estudo")) === JSON.stringify(chaves("operador")));

console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
