// aba-opcoes F3 (plano 24-02, 2026-09-11) — guardião das DUAS seções novas
// da aba Opções ("Analisar" e "Possibilidades") e do `PayoffChart`.
//
// O irmão `test_opcoes_mcp_aba_ui.mjs` continua trancando a tela da F2 (a
// cadeia de estados principal, o chip de frescor, a escolha de erro por
// código). Este aqui tranca só o que a F3 acrescentou — e, como ele, prova
// o que SÓ se prova lendo o fonte:
//
//  · nenhum arquivo de `web/src/opcoes/` multiplica por lote. A conversão em
//    reais é fechada no backend (`_em_reais`, D-24.2); uma segunda
//    multiplicação aqui DOBRARIA o número na tela, e nenhum teste de render
//    pega isso sem um oráculo de valor;
//  · breakeven nunca encosta num bloco de reais — é preço do ativo, e
//    multiplicado pelo lote viraria um número sem significado exibido como
//    dinheiro;
//  · o custo em chamadas aparece ANTES do disparo. Descobrir que a consulta
//    custou 13 chamadas depois de gastá-las não é aviso, é recibo;
//  · ilimitado não vira teto: nenhum `<path>` preenchido fecha um lado que o
//    serviço declarou sem limite;
//  · nenhuma das quatro chamadas novas dispara por efeito — cada uma consome
//    o cap compartilhado.
//
// Cada regex de defeito carrega asserção de SANIDADE: sem ela, um typo (ou um
// Unicode diferente) faria o assert passar por vacuidade, para sempre.
//
// Roda sem build: `node web/tests/test_opcoes_analisar_ui.mjs`.
import { readFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");
const ler = (p) => readFileSync(p, "utf8");

const ARQUIVOS = ["OpcoesScreen.jsx", "useOpcoesMcp.js", "SetupChart.jsx", "PayoffChart.jsx"];
const brutos = Object.fromEntries(ARQUIVOS.map((f) => [f, ler(join(dirOpcoes, f))]));
// Sem comentários: eles citam os mesmos termos ao EXPLICAR as decisões
// ("não se multiplica pelo lote"), e contá-los faria o guardião se
// auto-invalidar.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const fontes = Object.fromEntries(
  Object.entries(brutos).map(([k, v]) => [k, semComentario(v)]));

const api = semComentario(ler(join(here, "..", "src", "api.js")));
const persistencia = semComentario(ler(join(here, "..", "src", "persistence.js")));

const tela = fontes["OpcoesScreen.jsx"];
const hook = fontes["useOpcoesMcp.js"];
const payoff = fontes["PayoffChart.jsx"];

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) PayoffChart existe, sem ciclo, com tokens locais e os dois ilimitados
ok("PayoffChart.jsx existe", existsSync(join(dirOpcoes, "PayoffChart.jsx")));
ok("PayoffChart exporta o componente",
   /export default function PayoffChart/.test(payoff));
ok("PayoffChart não importa App.jsx (seria ciclo)",
   !/from\s+["'][^"']*App\.jsx["']/.test(brutos["PayoffChart.jsx"]));
ok("PayoffChart não usa lightweight-charts (o eixo X é preço, não tempo)",
   !/lightweight-charts/.test(payoff));
ok("PayoffChart declara o bloco VARKEY/TOKENS/T local",
   /const VARKEY = /.test(payoff) && /const TOKENS = \[/.test(payoff)
   && /const T = Object\.fromEntries/.test(payoff));
ok("PayoffChart trata unlimited_gain E unlimited_loss",
   /unlimited_gain/.test(payoff) && /unlimited_loss/.test(payoff));
ok("o lado sem limite ganha legenda própria, em vez de um número",
   /opcoesGanhoIlimitado/.test(payoff) && /opcoesPerdaIlimitada/.test(payoff));
// Nenhum `fill` a não ser `none`: é o que garante que a curva não seja
// fechada por um retângulo do lado que o serviço declarou ilimitado.
const paths = payoff.match(/<path[^>]*>/g) || [];
ok("há curva desenhada (pelo menos dois <path>)", paths.length >= 2);
ok("nenhum <path> é preenchido — lado ilimitado não aparece fechado",
   paths.every((p) => /fill="none"/.test(p)));
ok("o SVG é acessível (role=img + aria-label + title)",
   /role="img"/.test(payoff) && /aria-label=/.test(payoff) && /<title>/.test(payoff));
ok("o SVG é responsivo (viewBox + preserveAspectRatio + largura 100%)",
   /viewBox=/.test(payoff) && /preserveAspectRatio=/.test(payoff) && /width: "100%"/.test(payoff));

// ---- 2) nenhuma multiplicação por lote em web/src/opcoes/ --------------------
// A conta é do backend, uma vez só. Repetir aqui dobra o número na tela.
const MULT_LOTE = /\*\s*lote\b|\blote\s*\*/;
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} não multiplica por lote`, !MULT_LOTE.test(src));
}
ok("sanidade: a regex de multiplicação por lote pega o padrão quando ele existe",
   MULT_LOTE.test("const bruto = premio * lote;")
   && MULT_LOTE.test("const bruto = lote * premio;"));

// ---- 3) breakeven nunca dentro de um bloco de reais -------------------------
// Breakeven é PREÇO do ativo. O desenho do backend já o mantém FORA de
// `emReais`; aqui se tranca o outro lado: nenhuma expressão da tela mistura
// os dois, que é a forma que o defeito teria (`moeda(emReais.breakeven)` ou
// `breakeven * emReais.lote`).
const REAIS_COM_BREAKEVEN = /emReais[^\n]*breakeven|breakeven[^\n]*emReais/i;
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} não mistura emReais e breakeven na mesma expressão`,
     !REAIS_COM_BREAKEVEN.test(src));
}
ok("sanidade: a regex pega emReais e breakeven juntos quando eles estão",
   REAIS_COM_BREAKEVEN.test("const x = emReais.breakeven * 100;")
   && REAIS_COM_BREAKEVEN.test("const y = breakevens[0] * emReais.lote;"));

// ---- 4) o custo em chamadas aparece ANTES do disparo ------------------------
const iCusto = tela.indexOf("cp.opcoesCustoChamadas");
const iDispara = tela.indexOf("verPossibilidades(");
ok("a tela mostra o custo em chamadas e dispara as possibilidades",
   iCusto >= 0 && iDispara >= 0);
ok("o custo aparece no fonte ANTES do disparo (aviso, não recibo)", iCusto < iDispara);
ok("o custo é 2×N+1 com N ≤ 6, derivado dos vencimentos que a leitura trouxe",
   /Math\.min\(vencimentos\.length, N_MAX_VENCIMENTOS\)/.test(tela)
   && /2 \* N \+ 1/.test(tela) && /const N_MAX_VENCIMENTOS = 6/.test(tela));
ok("sem vencimento, a seção diz o motivo e o botão não fica habilitado",
   /cp\.opcoesSemVencimento/.test(tela) && /disabled=\{!temTese \|\| !loteOk\}/.test(tela));
ok("possibilidades exige TESE: o backend responde 422 tese_ausente sem ela",
   /const temTese = !!tese;/.test(tela));

// ---- 5) cada seção repete carregando → erro → vazio com motivo → dados ------
const iAnalisar = tela.indexOf("cp.opcoesAnalisarTitulo");
const iPossib = tela.indexOf("cp.opcoesPossibilidadesTitulo");
const iSetups = tela.indexOf("cp.opcoesSetupsTitulo");
ok("as duas seções existem, entre a leitura e os setups gravados",
   iAnalisar > 0 && iPossib > iAnalisar && iSetups > iPossib
   && tela.indexOf("cp.opcoesLeituraTitulo") < iAnalisar);

for (const [secao, ini, fim, trio, vazio, dados] of [
  ["Analisar", iAnalisar, iPossib, "proposta", "proposta.dados.motivo", "<PayoffChart"],
  ["Possibilidades", iPossib, iSetups, "possibilidades", "possibilidades.dados.motivo",
    "possibilidades.dados.possibilidades.map"],
]) {
  const bloco = tela.slice(ini, fim);
  const i1 = bloco.indexOf(`${trio}.carregando`);
  const i2 = bloco.indexOf(`${trio}.erro`);
  const i3 = bloco.indexOf(vazio);
  const i4 = bloco.indexOf(dados);
  ok(`${secao}: os quatro estados existem`, i1 >= 0 && i2 >= 0 && i3 >= 0 && i4 >= 0);
  ok(`${secao}: ordem carregando → erro → vazio com motivo → dados`,
     i1 < i2 && i2 < i3 && i3 < i4);
  ok(`${secao}: o erro é escolhido pelo \`code\` (ErroDoMcp), não raspando a mensagem`,
     /<ErroDoMcp erro=/.test(bloco));
}
// A cascata reusada pelas seções cobre os MESMOS quatro códigos do ADR-027
// que a cadeia de estados principal cobre.
const erroDoMcp = tela.slice(tela.indexOf("function ErroDoMcp"));
for (const code of ["mcp_nao_configurado", "mcp_cota", "mcp_teto_servico", "mcp_indisponivel"]) {
  ok(`ErroDoMcp trata ${code}`, erroDoMcp.includes(code));
}
ok("ErroDoMcp cai em erro.message com pre-wrap no caso sem código conhecido",
   /erro\.message/.test(erroDoMcp) && /tom="forte"/.test(erroDoMcp));

// ---- 6) sem promessa de resultado -------------------------------------------
const PROMESSA = /probabilidade de sucesso|chance de lucro|garantia de lucro|lucro certo|ganho garantido/i;
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} sem promessa de resultado`, !PROMESSA.test(src));
}
const novas = Object.keys(COPY.estudo).filter((k) => k.startsWith("opcoes"));
const textoDasChaves = JSON.stringify(novas.map((k) => [COPY.estudo[k], COPY.operador[k]]
  .map((v) => (typeof v === "function" ? v(1) + v(null) : v))));
ok("as chaves opcoes* de copy.js não prometem resultado", !PROMESSA.test(textoDasChaves));
ok("sanidade: a regex de promessa pega o padrão quando ele existe",
   PROMESSA.test("delta é a probabilidade de sucesso da operação"));
// O rótulo PERMITIDO para delta é o da Decisão 10 do ADR-027, e ele é
// aproximação declarada — não probabilidade de ganhar dinheiro.
for (const modo of ["estudo", "operador"]) {
  ok(`${modo}: delta é descrito como aproximação de terminar dentro do dinheiro`,
     /dentro do dinheiro/.test(COPY[modo].opcoesDeltaAjuda)
     && /aproxima/i.test(COPY[modo].opcoesDeltaAjuda));
  ok(`${modo}: a banda é declarada como dispersão, não previsão`,
     /±1σ/.test(COPY[modo].opcoesSigmaAjuda) && /não previsão de preço/.test(COPY[modo].opcoesSigmaAjuda));
  ok(`${modo}: breakeven é declarado como preço que não se multiplica pelo lote`,
     /não se multiplica pelo lote/.test(COPY[modo].opcoesBreakevenAjuda));
  ok(`${modo}: ilimitado é texto, nunca número`,
     typeof COPY[modo].opcoesGanhoIlimitado === "string"
     && typeof COPY[modo].opcoesPerdaIlimitada === "string"
     && !/\d/.test(COPY[modo].opcoesGanhoIlimitado + COPY[modo].opcoesPerdaIlimitada));
}

// ---- 7) as chaves novas existem nos DOIS modos, com o mesmo conjunto --------
const CHAVES_F3 = ["opcoesAnalisarTitulo", "opcoesPossibilidadesTitulo", "opcoesTeseRotulo",
  "opcoesTeseAlta", "opcoesTeseBaixa", "opcoesTeseNeutra", "opcoesLoteRotulo", "opcoesLoteAjuda",
  "opcoesMontarEstrutura", "opcoesVerPossibilidades", "opcoesCustoChamadas", "opcoesVerCadeia",
  "opcoesVerOperaveis", "opcoesCriterioOperaveis", "opcoesSemEstrutura", "opcoesSemVencimento",
  "opcoesBreakevenRotulo", "opcoesBreakevenAjuda", "opcoesCenariosTitulo", "opcoesSigmaAjuda",
  "opcoesDeltaAjuda", "opcoesPorAcaoRotulo", "opcoesEmReaisRotulo", "opcoesGanhoIlimitado",
  "opcoesPerdaIlimitada", "opcoesCadeiaTruncada", "opcoesAlvoRotulo", "opcoesStopRotulo"];
for (const k of CHAVES_F3) {
  ok(`COPY tem ${k} nos dois modos`, !!COPY.estudo[k] && !!COPY.operador[k]);
}
const kEstudo = Object.keys(COPY.estudo).filter((k) => k.startsWith("opcoes")).sort();
const kOperador = Object.keys(COPY.operador).filter((k) => k.startsWith("opcoes")).sort();
ok("o conjunto de chaves opcoes* é IGUAL nos dois modos",
   JSON.stringify(kEstudo) === JSON.stringify(kOperador));
ok("as funções de copy toleram argumento nulo",
   typeof COPY.estudo.opcoesCustoChamadas(null) === "string"
   && typeof COPY.operador.opcoesCustoChamadas(null) === "string"
   && typeof COPY.estudo.opcoesCriterioOperaveis(null) === "string"
   && typeof COPY.operador.opcoesCriterioOperaveis(null) === "string"
   && typeof COPY.estudo.opcoesCadeiaTruncada(null) === "string"
   && typeof COPY.operador.opcoesCadeiaTruncada(null) === "string");
ok("1 contrato = 100 ações aparece na ajuda do lote, nos dois modos",
   /100 ações/.test(COPY.estudo.opcoesLoteAjuda) && /100 ações/.test(COPY.operador.opcoesLoteAjuda));

// ---- 8) nenhuma das quatro chamadas dispara por efeito ----------------------
const METODOS = ["mcpCadeia", "mcpOperaveis", "mcpProposta", "mcpPossibilidades"];
// Corpo de cada `useEffect(` até o fechamento do argumento (heurística
// suficiente: os dois efeitos do arquivo são curtos e seguidos de `}, [`).
const efeitos = hook.split("useEffect(").slice(1).map((t) => t.split("}, [")[0]);
ok("o hook continua com DOIS efeitos (status e troca de ticker)", efeitos.length === 2);
for (const m of METODOS) {
  ok(`nenhum useEffect chama store.${m}`, efeitos.every((corpo) => !corpo.includes(m)));
}
ok("sanidade: a fatia de efeito enxerga o que está dentro dele",
   efeitos.some((corpo) => corpo.includes("store.mcpLeitura")));
for (const acao of ["abrirCadeia", "abrirOperaveis", "montarProposta", "verPossibilidades"]) {
  ok(`o hook exporta a ação ${acao} (sob demanda)`,
     new RegExp(`const ${acao} = useCallback`).test(hook)
     && new RegExp(`\\b${acao}\\b`).test(tela));
}
ok("a troca de ticker limpa os quatro trios (dado de outro ativo não fica na tela)",
   /limparCadeia\(\);/.test(hook) && /limparOperaveis\(\);/.test(hook)
   && /limparProposta\(\);/.test(hook) && /limparPossibilidades\(\);/.test(hook));
ok("cada chamada confere o ticker na volta",
   /tickerRef\.current === meuTicker/.test(hook));

// ---- 9) alvo e stop viajam NOMEADOS ----------------------------------------
// Eles saem daqui como `alvo`/`stop` no corpo e é o BACKEND que os converte
// em `scenarios: [{name: "alvo", underlying: …}]` — mandar `name` do front
// seria outro contrato. O que este guardião tranca é que não virem número
// solto: chave nomeada no corpo, rótulo próprio na tela.
ok("o corpo de possibilidades nomeia alvo e stop",
   /alvo: o\.alvo/.test(hook) && /stop: o\.stop/.test(hook));
ok("a tela manda alvo e stop pelos campos próprios",
   /alvo: alvoNum/.test(tela) && /stop: stopNum/.test(tela));
ok("alvo e stop têm rótulo próprio na tela",
   /cp\.opcoesAlvoRotulo/.test(tela) && /cp\.opcoesStopRotulo/.test(tela));
ok("preço ausente vira ausência do cenário, nunca zero",
   /const alvoNum = ehNum\(num\(alvo\)\) && num\(alvo\) > 0 \? num\(alvo\) : undefined;/.test(tela));

// ---- 10) `null` nunca vira 0 ------------------------------------------------
const OU_ZERO = /\|\|\s*0\b/;
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} sem \`|| 0\` (ausência não é zero)`, !OU_ZERO.test(src));
}
ok("sanidade: a regex de `|| 0` pega o padrão quando ele existe",
   OU_ZERO.test("const v = dados.premio || 0;"));

// ---- 11) as quatro rotas alcançáveis pelos DOIS stores ----------------------
const iServer = persistencia.indexOf("function serverStore");
const iDevice = persistencia.indexOf("function deviceStore");
ok("os dois stores foram encontrados", iServer > 0 && iDevice > iServer);
for (const m of METODOS) {
  ok(`${m} existe no serverStore`, persistencia.slice(iServer, iDevice).includes(m));
  ok(`${m} existe no deviceStore`, persistencia.slice(iDevice).includes(m));
  ok(`${m} existe em api.js`, api.includes(m + ":"));
}
ok("/possibilidades tem timeout maior (até 13 chamadas ao serviço numa só)",
   /mcpPossibilidades: \(body\) => req\("POST", "\/api\/options\/mcp\/possibilidades", body, 60000\)/.test(api));

// ---- 12) alvo de toque e rolagem no container ------------------------------
ok("os botões novos nascem com alvo de toque de 44 px",
   /const BOTAO = \{[\s\S]{0,120}minHeight: "44px"/.test(tela)
   && /const CAMPO = \{[\s\S]{0,120}minHeight: "44px"/.test(tela));
ok("a tabela rola no container, não no body",
   /const ROLAGEM = \{ overflowX: "auto"/.test(tela));

// ---- 13) razão ganho/perda (F-01 do 24-VERIFICATION, plano 24-06) ----------
// O critério 1 do ROADMAP termina em "breakevens e razão ganho/perda", e ela
// não existia em lugar nenhum. Chega PRONTA do backend, adimensional. O que
// este bloco tranca é o que só se prova lendo o fonte: a tela não recalcula a
// razão, não a encosta no bloco de reais (razão não é dinheiro) e não a cala
// quando ela não existe — travessão mudo faria a pessoa achar que o app não
// calculou, e um número faria com que ela decidisse sobre uma razão que não
// existe, que é a pior das três saídas.
const iRazaoAnalisar = tela.slice(iAnalisar, iPossib).indexOf("razaoGanhoPerda");
const iRazaoPossib = tela.slice(iPossib, iSetups).indexOf("razaoGanhoPerda");
ok("a razão é renderizada nas DUAS seções (Analisar e Possibilidades)",
   iRazaoAnalisar >= 0 && iRazaoPossib >= 0);
ok("a razão tem componente próprio, alimentado pelo campo do backend",
   /function RazaoGanhoPerda/.test(tela)
   && /razao=\{proposta\.dados\.razaoGanhoPerda\}/.test(tela)
   && /razao=\{item\.razaoGanhoPerda\}/.test(tela));
ok("sem número, a tela mostra o MOTIVO em vez de calar ou inventar",
   /razao\.motivo/.test(tela) && /ehNum\(razao\.valor\)/.test(tela));
const DIVIDE_RAZAO = /max_gain\s*\/|\/\s*max_loss|ganhoMaximo\s*\/|\/\s*perdaMaxima/;
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} não divide para obter a razão (ela vem pronta do backend)`,
     !DIVIDE_RAZAO.test(src));
}
ok("sanidade: a regex de divisão pega o padrão quando ele existe",
   DIVIDE_RAZAO.test("const r = e.max_gain / e.max_loss;")
   && DIVIDE_RAZAO.test("const r = emReais.ganhoMaximo / emReais.perdaMaxima;"));
// Mesma trava do breakeven, pela mesma razão: a razão é adimensional, e
// dentro de um bloco de reais ela seria lida como dinheiro.
const REAIS_COM_RAZAO = /emReais[^\n]*razaoGanhoPerda|razaoGanhoPerda[^\n]*emReais/i;
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} não mistura emReais e a razão na mesma expressão`,
     !REAIS_COM_RAZAO.test(src));
}
ok("sanidade: a regex pega emReais e a razão juntos quando eles estão",
   REAIS_COM_RAZAO.test("const x = emReais.razaoGanhoPerda;")
   && REAIS_COM_RAZAO.test("const y = razaoGanhoPerda.valor * emReais.lote;"));
for (const modo of ["estudo", "operador"]) {
  ok(`${modo}: a razão tem rótulo e ajuda próprios`,
     typeof COPY[modo].opcoesRazaoRotulo === "string" && !!COPY[modo].opcoesRazaoRotulo
     && typeof COPY[modo].opcoesRazaoAjuda === "string" && !!COPY[modo].opcoesRazaoAjuda);
  ok(`${modo}: a ajuda diz o que a razão é e NEGA a leitura como probabilidade`,
     /cabe na perda máxima/.test(COPY[modo].opcoesRazaoAjuda)
     && /não é probabilidade/.test(COPY[modo].opcoesRazaoAjuda));
}

// ---- 14) a recusa cobrada (F-04 do 24-VERIFICATION, plano 24-07) -----------
// A partir de 2026-09-11 a recusa da tool DEBITA uma chamada do cap do
// usuário — a viagem aconteceu e o serviço já a cobrou do teto compartilhado.
// Cobrar sem dizer que cobrou é a metade do defeito que a pessoa enxerga: a
// cota dela cai e a tela mostra só "o serviço recusou". A frase é do FRONT
// porque é sobre a cota DELA, não sobre o pedido — e por isso tem voz por
// modo, como todo o resto do `copy.js`.
ok("existe componente próprio para a linha da recusa cobrada",
   /function RecusaCobrada/.test(tela));
// A linha só pode aparecer com o campo do backend. Sem ele, a tela não
// afirma nada sobre cota: uma linha incondicional mentiria em todo 422 de
// pedido torto (`kind_invalido`, `lote_invalido`), que é recusa ANTES da rede
// e não custa chamada nenhuma.
ok("a linha é condicionada ao `cobrado` do detail E ao código do erro",
   /erro\.code !== "mcp_erro_de_tool"/.test(tela)
   && /cobrado !== true/.test(tela));
const iRecusa1 = tela.indexOf("<RecusaCobrada");
const iRecusa2 = tela.indexOf("<RecusaCobrada", iRecusa1 + 1);
ok("a linha aparece nos DOIS ramos de erro (cascata principal e ErroDoMcp)",
   iRecusa1 >= 0 && iRecusa2 > iRecusa1);
ok("a linha é discreta (textMuted), não alarme",
   /function RecusaCobrada[\s\S]{0,400}T\.textMuted/.test(tela));
for (const modo of ["estudo", "operador"]) {
  const t = COPY[modo].opcoesRecusaCobrada;
  ok(`${modo}: `+"`opcoesRecusaCobrada` existe e é texto",
     typeof t === "string" && t.length > 20);
  ok(`${modo}: a frase diz que a tentativa consumiu da COTA do dia`,
     /cota/i.test(t || ""));
  ok(`${modo}: a frase diz que o serviço cobra mesmo recusando`,
     /recus/i.test(t || ""));
  ok(`${modo}: a frase não promete devolução nem culpa o usuário`,
     !/estorn|devolv|culpa|erro seu/i.test(t || ""));
}
// Paridade do conjunto `opcoes*` entre os dois modos — chave nova em um só
// ramo deixaria metade da base sem a informação.
const chaves = (m) => Object.keys(COPY[m]).filter((k) => k.startsWith("opcoes")).sort();
ok("o conjunto de chaves `opcoes*` continua idêntico nos dois modos",
   JSON.stringify(chaves("estudo")) === JSON.stringify(chaves("operador")));


console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
