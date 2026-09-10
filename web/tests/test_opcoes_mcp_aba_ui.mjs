// aba-opcoes F2 (quick 260910-biz, 2026-09-10) — guardião da TELA da aba
// Opções (`web/src/opcoes/`).
//
// O que ele tranca, em uma frase cada:
//  · os três arquivos não importam `App.jsx` (seria ciclo: App.jsx importa a
//    tela) e trazem o bloco de tokens local, padrão de `pet/BorisChat.jsx`;
//  · a ORDEM dos estados no fonte é carregando → erro → vazio com motivo →
//    dados: vazio pintado antes de carregar afirma "não há nada" sem ninguém
//    ter medido, e é o erro que o princípio 9 do CLAUDE.md existe para pegar;
//  · cada código de degradação do ADR-027 tem seu próprio estado;
//  · "dado em dia" é CONDICIONADO a `frescor.medido` — "não medido" que vira
//    silêncio é lido como "em dia" (ADR-027, Decisão 8);
//  · o `PriceChart` recebe os QUATRO campos de `ind` (chave ausente estoura
//    em `arr[i]`) e as cores das linhas vêm da paleta em HEX, não de `var()`.
//
// Quick 260910-d57 (2026-09-10) — dois defeitos achados ao vivo (produção só
// tinha a Fase 1, `/leitura` 404):
//  · o chip de frescor nascia afirmando "não medido" por DEFAULT, mesmo
//    quando nada tinha sido consultado — agora só existe sob resposta real;
//  · `leitura.erro || status.erro` deixava o 404 mascarar o
//    `mcp_nao_configurado` do `/status`, que é o que diz o que fazer.
//
// Roda sem build: `node web/tests/test_opcoes_mcp_aba_ui.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dir = join(here, "..", "src", "opcoes");
const ler = (f) => readFileSync(join(dir, f), "utf8");

const brutos = {
  "OpcoesScreen.jsx": ler("OpcoesScreen.jsx"),
  "useOpcoesMcp.js": ler("useOpcoesMcp.js"),
  "SetupChart.jsx": ler("SetupChart.jsx"),
};
// Sem comentários: eles citam os mesmos termos ao explicar as decisões, e
// contá-los faria o guardião se auto-invalidar.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const fontes = Object.fromEntries(
  Object.entries(brutos).map(([k, v]) => [k, semComentario(v)]));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const tela = fontes["OpcoesScreen.jsx"];
const chart = fontes["SetupChart.jsx"];

// ---- 1) sem ciclo, com tokens locais ----------------------------------------
for (const [nome, src] of Object.entries(brutos)) {
  ok(`${nome} não importa App.jsx`, !/from\s+["'][^"']*App\.jsx["']/.test(src));
}
// O bloco de tokens é exigido dos DOIS componentes que desenham.
// `useOpcoesMcp.js` é lógica de estado pura — não renderiza nada, e um bloco
// de tokens ali seria código morto que o próximo leitor tomaria por cor em
// uso. O que se exige DELE é o oposto: nenhum acoplamento ao módulo de
// estado (o `store` chega por argumento).
for (const nome of ["OpcoesScreen.jsx", "SetupChart.jsx"]) {
  const src = fontes[nome];
  ok(`${nome} declara o bloco VARKEY/TOKENS/T local`,
     /const VARKEY = /.test(src) && /const TOKENS = \[/.test(src) && /const T = Object\.fromEntries/.test(src));
}
ok("useOpcoesMcp.js recebe o store por ARGUMENTO (não importa persistence.js)",
   /export function useOpcoesMcp\(store, ticker\)/.test(fontes["useOpcoesMcp.js"])
   && !/from ["'][^"']*persistence\.js["']/.test(brutos["useOpcoesMcp.js"]));

// ---- 2) a ordem dos estados no fonte ----------------------------------------
const iCarregando = tela.indexOf("cp.opcoesCarregando");
const iErro = tela.indexOf("mcp_nao_configurado");
const iVazio = tela.indexOf("cp.opcoesEscolherAtivo");
const iDados = tela.indexOf("cp.opcoesLeituraTitulo");
ok("os quatro estados existem", iCarregando >= 0 && iErro >= 0 && iVazio >= 0 && iDados >= 0);
ok("ordem no fonte: carregando → erro → vazio com motivo → dados",
   iCarregando < iErro && iErro < iVazio && iVazio < iDados);

// ---- 3) cada código de degradação tem seu estado ----------------------------
for (const [code, chave] of [
  ["mcp_nao_configurado", "cp.opcoesNaoConfigurado"],
  ["mcp_cota", "cp.opcoesCota"],
  ["mcp_teto_servico", "cp.opcoesCota"],
  ["mcp_indisponivel", "cp.opcoesIndisponivel"],
]) {
  ok(`${code} tem estado próprio (${chave})`, tela.includes(code) && tela.includes(chave));
}
ok("o estado escolhe pelo `erro.code`, não raspando a mensagem",
   /erro\.code ===/.test(tela));
ok("o ramo genérico de erro mostra erro.message com pre-wrap",
   /erro\.message/.test(tela) && /whiteSpace: "pre-wrap"/.test(tela));

// ---- 3b) defeito 2 (260910-d57): erro por ACIONABILIDADE, não por quem
// respondeu primeiro — o 404 da leitura não pode mascarar o
// `mcp_nao_configurado` do `/status`. ----------------------------------------
ok("defeito 2 não voltou: `erro` não é mais `leitura.erro || status.erro` puro",
   !/const erro = leitura\.erro \|\| status\.erro;/.test(tela));
ok("existe helper puro que decide o erro pelo `code` conhecido",
   /function escolherErroOpcoes\(erroLeitura, erroStatus\)/.test(tela)
   && /CODIGOS_ACIONAVEIS/.test(tela));
ok("a lista de códigos acionáveis cobre os quatro estados do ADR-027",
   /CODIGOS_ACIONAVEIS = \[[\s\S]{0,120}mcp_nao_configurado[\s\S]{0,120}mcp_cota[\s\S]{0,120}mcp_teto_servico[\s\S]{0,120}mcp_indisponivel/.test(tela));
ok("o `erro` do cabeçalho vem do helper, não de precedência de chamada",
   /const erro = escolherErroOpcoes\(leitura\.erro, status\.erro\);/.test(tela));

// ---- 4) frescor: "em dia"/"não medido" nunca são default --------------------
const blocoChip = tela.match(/let chip[\s\S]{0,700}/);
ok("bloco do chip de frescor encontrado", !!blocoChip);
ok('"em dia" está condicionado a frescor.medido',
   !!blocoChip && /frescor\.medido/.test(blocoChip[0])
   && /cp\.opcoesFrescorEmDia/.test(blocoChip[0])
   && /cp\.opcoesFrescorAtrasado/.test(blocoChip[0]));
ok("chip nasce nulo — nada é afirmado sobre frescor sem resposta do serviço",
   !!blocoChip && /let chip = null;/.test(blocoChip[0]));
ok('"não medido" só aparece quando frescor.medido === false (deixou de ser o default)',
   !!blocoChip && /frescor\.medido === false/.test(blocoChip[0])
   && /cp\.opcoesFrescorNaoMedido/.test(blocoChip[0]));
ok("defeito 1 não voltou: chip não é mais inicializado incondicionalmente com \"não medido\"",
   !/let chip = cp\.opcoesFrescorNaoMedido \|\| ["']frescor não medido["'];/.test(tela));
ok("o chip só é renderizado no cabeçalho quando existe (nada afirmado sem resposta)",
   /\{chip \? /.test(tela));
ok('a fonte não afirma "mcp.semente.dev" como default sem resposta',
   !/fonte \|\| ["']mcp\.semente\.dev["']/.test(tela));

// ---- sanidade: as regex acima pegam o bug antigo, não viram no-op ----------
// Sem isto, um typo na regex (ou um Unicode diferente) faria os asserts
// "defeito N não voltou" passarem SEMPRE, mesmo com o bug de volta.
const BUG_CHIP = 'let chip = cp.opcoesFrescorNaoMedido || "frescor não medido";';
ok("sanidade: a regex do defeito 1 pega o padrão antigo quando ele existe",
   /let chip = cp\.opcoesFrescorNaoMedido \|\| ["']frescor não medido["'];/.test(BUG_CHIP));
const BUG_ERRO = "const erro = leitura.erro || status.erro;";
ok("sanidade: a regex do defeito 2 pega o padrão antigo quando ele existe",
   /const erro = leitura\.erro \|\| status\.erro;/.test(BUG_ERRO));

// ---- 5) o pregão vive no cabeçalho, fora de qualquer ramo de erro ------------
const cabecalho = tela.match(/const cabecalho = \([\s\S]*?\n  \);/);
ok("bloco do cabeçalho encontrado", !!cabecalho);
ok("o cabeçalho carrega pregão e fonte",
   !!cabecalho && /cp\.opcoesPregaoRotulo/.test(cabecalho[0])
   && /cp\.opcoesFonteRotulo/.test(cabecalho[0]) && /\{pregao \|\| "—"\}/.test(cabecalho[0]));
ok("o cabeçalho é renderizado antes da cadeia de estados",
   tela.indexOf("{cabecalho}") >= 0 && tela.indexOf("{cabecalho}") < iCarregando);

// ---- 6) acessibilidade e layout ---------------------------------------------
ok('há alvo de toque de 44px', /minHeight: "44px"/.test(tela));
ok("há aria-label em botão só-ícone/ação", /aria-label=/.test(tela));
ok("há aria-pressed em seletor", /aria-pressed=/.test(tela));
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} não usa CONTENT_MAX_WIDTH`, !/CONTENT_MAX_WIDTH/.test(src));
}

// ---- 7) SetupChart: adaptação para o PriceChart ------------------------------
ok("SetupChart usa ctx.PriceChart", /ctx && ctx\.PriceChart/.test(chart));
ok("SetupChart tem fallback textual (sem PriceChart ou sem candles)",
   /if \(!Chart \|\| !candles\.length\)/.test(chart));
ok("SetupChart mapeia triggers/trigger_dates para priceLines",
   /g\.triggers/.test(chart) && /g\.trigger_dates/.test(chart) && /priceLines/.test(chart));
for (const campo of ["sma20", "sma50", "bbUpper", "bbLower"]) {
  ok(`SetupChart preenche ind.${campo}`, new RegExp(`${campo}:`).test(chart));
}
ok("o array de preenchimento deriva do comprimento dos candles",
   /const nulos = new Array\(n\)\.fill\(null\)/.test(chart) && /const n = velas\.length/.test(chart));
// A cor da linha tem de ser HEX resolvido: `var(--x)` não resolve em canvas
// (foi o bug real do Modo Operador; test_chart_colors_theme_aware guarda a
// classe do erro no App.jsx, este guarda aqui).
// Recorte no push da linha de preço, não no arquivo inteiro: `color: T.x`
// em DOM (texto, borda) é legítimo — `var()` resolve lá. O que não pode é
// `T.x` dentro do objeto que vai para o canvas do PriceChart.
const pushLinha = chart.match(/linhas\.push\(\{[\s\S]*?\}\);/);
ok("bloco linhas.push encontrado", !!pushLinha);
ok("a cor da linha de disparo NÃO usa T. (var() não resolve em canvas)",
   !!pushLinha && !/color: T\./.test(pushLinha[0]));
ok("a cor do disparo vem de P.accent (paleta em hex)",
   !!pushLinha && /color: P\.accent/.test(pushLinha[0]));

// ---- 8) sem promessa de resultado, sem vocabulário de ordem ------------------
// A tela lê TODO texto longo de `cp.` — os literais que sobram são rótulos
// curtos e mensagens de dado ausente. Nenhum deles pode prometer resultado.
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} sem promessa de resultado`,
     !/probabilidade de sucesso|garantia de lucro|lucro certo|ganho garantido/i.test(src));
}
ok("os textos de estado da tela vêm do dicionário de copy",
   /cp\.opcoesDisclaimer/.test(tela) && /cp\.opcoesSemSetups/.test(tela)
   && /cp\.opcoesNaoAvaliado/.test(tela));

// ---- 9) o motivo do serviço vai verbatim ------------------------------------
ok("o `reason` de setupsNaoAvaliados é repassado à copy sem reescrita",
   /cp\.opcoesNaoAvaliado[\s\S]{0,200}naoAvaliado\.reason/.test(tela));
ok("ausência de avaliação NÃO vira \"não armado\"",
   /sem avaliação hoje/.test(tela));

// ---- 10) as chaves de copy existem nos dois modos ---------------------------
const CHAVES = ["tituloOpcoes", "subtituloOpcoes", "opcoesLeituraTitulo",
  "opcoesSetupsTitulo", "opcoesPregaoRotulo", "opcoesFonteRotulo",
  "opcoesFrescorEmDia", "opcoesFrescorAtrasado", "opcoesFrescorNaoMedido",
  "opcoesSemSetups", "opcoesNaoAvaliado", "opcoesNaoConfigurado", "opcoesCota",
  "opcoesIndisponivel", "opcoesCarregando", "opcoesEscolherAtivo",
  "opcoesDisclaimer", "opcoesGraficoTitulo", "opcoesDisparosRotulo"];
for (const k of CHAVES) {
  ok(`COPY tem ${k} nos dois modos`, !!COPY.estudo[k] && !!COPY.operador[k]);
}
ok("opcoesNaoAvaliado e opcoesCota toleram nulo",
   typeof COPY.estudo.opcoesNaoAvaliado(null) === "string"
   && typeof COPY.operador.opcoesNaoAvaliado(null) === "string"
   && typeof COPY.estudo.opcoesCota(null) === "string"
   && typeof COPY.operador.opcoesCota(null) === "string");

// ---- 11) invalidação de resposta em voo -------------------------------------
const hook = fontes["useOpcoesMcp.js"];
ok("resposta antiga é descartada quando o ticker muda",
   /tickerRef\.current === meu/.test(hook) && /const meu = \+\+tickerRef\.current/.test(hook));
ok("carregando nasce verdadeiro (antes do vazio)",
   /useState\(\{ dados: null, carregando: true, erro: null \}\)/.test(hook));
ok("o gráfico dispara sob demanda, não por efeito",
   /const abrirGrafico = useCallback/.test(hook));

console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
