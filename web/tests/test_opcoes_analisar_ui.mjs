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
//  · nenhuma chamada NOVA dispara por efeito — cada uma consome o cap
//    compartilhado. Atualizado em 2026-09-13 (Fase 27): a contagem de efeitos
//    virou uma ALLOWLIST nomeada (`EFEITO_PERMITIDO`), porque o bloco "Seus
//    vigias" acrescentou um terceiro efeito legítimo (custo zero) e a
//    contagem falharia sobre uma mudança correta enquanto passava calada
//    sobre uma errada que não mexesse no número — ver a seção 8;
//  · (24-11) nenhum arquivo de `web/src/opcoes/` CALCULA indicador. A leitura
//    vem pronta do serviço, e um hv caseiro aqui divergiria do dele na
//    primeira correção feita de um lado só — em silêncio, porque os dois
//    números teriam o mesmo nome na tela.
//
// Cada regex de defeito carrega asserção de SANIDADE: sem ela, um typo (ou um
// Unicode diferente) faria o assert passar por vacuidade, para sempre.
//
// Roda sem build: `node web/tests/test_opcoes_analisar_ui.mjs`.
import { readFileSync, existsSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");
const ler = (p) => readFileSync(p, "utf8");

// ATUALIZADO 2026-09-19, Fase 33 (33-01): a allowlist `ARQUIVOS` deixa de ser
// lista fixa — varredura de DIRETÓRIO inteiro, mesmo padrão já usado em
// `test_opcoes_subabas_ui.mjs:100-116` e na seção 534-537 mais abaixo NESTE
// MESMO arquivo (a extrapolação é mudança de grau, não de espécie, aqui).
// Lista fixa deixaria os componentes novos das fases 33-02..33-05
// (`SecaoDescobrir`/`SecaoSetups`/`SecaoComparar`/`SecaoAnalisar`, além do
// `SecaoVigias`/`uiOpcoes.jsx` desta fase) fora das regras de lote/
// breakeven/razão/`|| 0` — exatamente a lacuna que a truth do 33-CONTEXT.md
// nomeia. Medido no planejamento: a varredura do diretório inteiro passa
// hoje sem nenhum hit novo, então a mudança não afrouxa nem reprova em falso.
const ARQUIVOS = readdirSync(dirOpcoes).filter((f) => /\.(js|jsx)$/.test(f));
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
const uiOpcoesFonte = fontes["uiOpcoes.jsx"] || "";
// 2026-09-20, Fase 33 (33-04): job 4 ("comparar os vencimentos") saiu de
// OpcoesScreen.jsx para SecaoComparar.jsx — as regras de custo/ordem/razão
// que ancoravam nele passam a ler esta fonte.
const secaoComparar = fontes["SecaoComparar.jsx"] || "";
// 2026-09-20, Fase 33 (33-05): job 3 ("analisar um ticker manualmente") saiu
// de OpcoesScreen.jsx para SecaoAnalisar.jsx — a fatia "Analisar" passa a ser
// este arquivo INTEIRO (mesmo precedente do 33-04 com "Possibilidades"), não
// mais um slice de `tela`.
const secaoAnalisar = fontes["SecaoAnalisar.jsx"] || "";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Sanidade da varredura por diretório (D-02): um `readdirSync` que retornasse
// vazio ou apontasse para o lugar errado faria toda regra de lote/breakeven/
// razão/`|| 0` abaixo passar por vacuidade — nenhum arquivo, nenhuma
// reprovação possível.
ok("achou pelo menos 14 arquivos em web/src/opcoes/ (sanidade da varredura por diretório)",
   ARQUIVOS.length >= 14);

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
// 2026-09-20, Fase 33 (33-04): o controle (custo + disparo) migrou de
// OpcoesScreen.jsx para SecaoComparar.jsx — a garantia se divide em duas,
// sem perder nada: (a) a CONTA (N_MAX_VENCIMENTOS/2*N+1) continua só no
// orquestrador, medida abaixo em `tela`; (b) a ORDEM custo-antes-do-disparo e
// o gate visual são medidos em `secaoComparar`, onde o controle está.
const iCusto = secaoComparar.indexOf("cp.opcoesCustoChamadas");
const iDispara = secaoComparar.indexOf("verPossibilidades(");
ok("a seção mostra o custo em chamadas e dispara as possibilidades",
   iCusto >= 0 && iDispara >= 0);
ok("o custo aparece no fonte ANTES do disparo (aviso, não recibo)", iCusto < iDispara);
ok("o custo é 2×N+1 com N ≤ 6, derivado dos vencimentos que a leitura trouxe (fica no orquestrador)",
   /Math\.min\(vencimentos\.length, N_MAX_VENCIMENTOS\)/.test(tela)
   && /2 \* N \+ 1/.test(tela) && /const N_MAX_VENCIMENTOS = 6/.test(tela));
// NOVA (33-04): "uma conta só" deixa de ser convenção e passa a ser travada —
// a extração TORNA possível (e necessária) proibir a segunda cópia da fórmula
// dentro do componente que só recebe o número pronto. `Math\.min\(` entra na
// mesma proibição: uma reescrita da fórmula com outro nome de variável (ex.:
// `2 * Math.min(vencimentos.length, 6) + 1`) driblaria uma regex que só
// buscasse o literal `2 * N + 1` — achado real da prova negativa (Task 3,
// injeção 2, 2026-09-20).
ok("SecaoComparar.jsx não recalcula o teto nem a fórmula do custo (uma conta só)",
   !/N_MAX_VENCIMENTOS/.test(secaoComparar) && !/2 \* N \+ 1/.test(secaoComparar)
   && !/Math\.min\(/.test(secaoComparar));
ok("sem vencimento, a seção diz o motivo e o botão não fica habilitado",
   /cp\.opcoesSemVencimento/.test(secaoComparar) && /disabled=\{!temTese \|\| !loteOk\}/.test(secaoComparar));
ok("possibilidades exige TESE: o backend responde 422 tese_ausente sem ela",
   /const temTese = !!tese;/.test(tela));

// ---- 5) cada seção repete carregando → erro → vazio com motivo → dados ------
// 2026-09-20, Fase 33 (33-05): job 3 ("analisar") saiu de OpcoesScreen.jsx
// para SecaoAnalisar.jsx — a fatia "Analisar" passa a ser o ARQUIVO
// SecaoAnalisar.jsx inteiro (mesmo precedente do 33-04 com "Possibilidades"/
// SecaoComparar.jsx), não mais um slice de `tela`. O marcador de ordem em
// `tela` troca de `cp.opcoesAnalisarTitulo` (sumiu do arquivo-fonte) para a
// TAG JSX `<SecaoAnalisar`.
//
// A checagem antiga comparava a PRIMEIRA ocorrência de `cp.opcoesLeituraTitulo`
// em `tela` contra `iAnalisar` — hoje essa chave só existe em
// `blocoLeituraDoServico` (o convite da leitura paga, que não se move) e não
// mede mais nada sobre a ordem interna do job 3, que virou uma caixa preta em
// SecaoAnalisar.jsx. Removida sem perder garantia: a ordem que importa (job 3
// → job 4 → job 5) continua travada pelas três tags abaixo.
const iAnalisar = tela.indexOf("<SecaoAnalisar");
const iSecaoComparar = tela.indexOf("<SecaoComparar");
const iSetups = tela.indexOf("<SecaoSetups");
ok("as três seções existem, na ordem job 3 → job 4 → job 5",
   iAnalisar > 0 && iSecaoComparar > iAnalisar && iSetups > iSecaoComparar);

for (const [secao, bloco, trio, vazio, dados] of [
  ["Analisar", secaoAnalisar, "proposta", "proposta.dados.motivo", "<PayoffChart"],
  ["Possibilidades", secaoComparar, "possibilidades", "possibilidades.dados.motivo",
    "possibilidades.dados.possibilidades.map"],
]) {
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
// 2026-09-19, Fase 33 (33-01): `ErroDoMcp` migrou de OpcoesScreen.jsx para
// `uiOpcoes.jsx` — a fatia passa a ler a fonte NOVA. O `-1` silencioso é o
// modo como este guardião ficaria inerte se a função não existisse mais em
// lugar nenhum; por isso a checagem `>= 0` roda ANTES do fatiamento.
const iErroDoMcp = uiOpcoesFonte.indexOf("function ErroDoMcp");
ok("function ErroDoMcp existe em uiOpcoes.jsx (migrou de arquivo nesta fase)", iErroDoMcp >= 0);
const erroDoMcp = iErroDoMcp >= 0 ? uiOpcoesFonte.slice(iErroDoMcp) : "";
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

// ---- 8) nenhuma chamada NOVA dispara por efeito -----------------------------
//
// 2026-09-13 (Fase 27, plano 27-02) — esta seção afirmava
// `efeitos.length === 2`. A contagem foi substituída por uma REGRA, que é o
// que sempre importou: contar efeitos só pegava o defeito por acidente, e o
// que se quer impedir é chamada consumindo cota sem clique.
//
// Motivo da mudança, declarado: o bloco "Seus vigias" acrescentou um TERCEIRO
// `useEffect`, o do índice local. Ele é legítimo — `GET /api/options/vigias`
// custa ZERO no cap, por contrato da rota (27-01) — mas a asserção de
// contagem falharia deterministicamente sobre uma mudança correta, e passaria
// calada sobre uma errada que não mexesse no número de efeitos.
//
// A regra: TODO `store.<método>` que apareça dentro de corpo de `useEffect`
// precisa estar na allowlist abaixo, com o porquê escrito. Chamada nova dentro
// de efeito sem entrar aqui reprova a suíte — que é o modo de falha desejado,
// porque gastar cota sem clique é silencioso na tela e só aparece no contador.
const EFEITO_PERMITIDO = [
  // Exceção PRÉ-EXISTENTE (F2). Custa ATÉ 1 e alimenta o cabeçalho de frescor;
  // o 27-05 passa a declarar esse custo na tela.
  "mcpStatus",
  // Custo ZERO por contrato da rota: lê o índice local do Boris+ e não toca
  // `mcp.semente.dev` (27-01). É o que permite a aba abrir com conteúdo.
  "mcpVigias",
  // 2026-09-13 (Fase 27, plano 27-05) — **`mcpLeitura` SAIU DAQUI.** Ela entrou
  // no 27-02 marcada TRANSITÓRIA, com o plano que a removeria escrito ao lado;
  // o 27-05 executou: a chamada saiu do efeito de troca de ticker e virou
  // `abrirLeitura`, sob clique, com as 3 consultas declaradas no próprio botão.
  // A entrada foi APAGADA, não comentada: allowlist com item morto é permissão
  // que ninguém revoga. `mcpLeitura` está agora em `METODOS`, logo abaixo — e
  // as duas listas são disjuntas por asserção, o que impede a troca pela
  // metade (deixá-la nos dois lados faria o guardião dizer "pode" e "não pode"
  // sobre a mesma chamada).
  //
  // 2026-09-13 (Fase 27, plano 27-04). Custo ZERO por contrato da ROTA:
  // `GET /api/options/tecnico/{ticker}` é interna, devolve `custoMcp: 0` e
  // não toca `mcp.semente.dev` — provado no backend por bomba no
  // `mcp_client.call_tool` (27-03, `test_opcoes_tecnico_rota.py`). É ela que
  // permite escolher um ativo e ter tendência, volatilidade e níveis na hora
  // sem mexer no contador de cota (critério 3 do ROADMAP).
  //
  // Sem prefixo `mcp`, e isso é decisão do 27-03: neste código `mcp*`
  // significa "custa cota". Ver a nota na extração logo abaixo — foi por causa
  // deste item que ela deixou de olhar só para `store.mcp*`.
  "opcoesTecnico",
];
// Lista POSITIVA de quem não pode disparar por efeito. `mcpSetupsListar`
// entrou na Fase 27 (27-02): ela custa 2 e tem UMA porta, o botão "Atualizar"
// do bloco de vigias.
//
// 2026-09-13 (Fase 27, plano 27-05) — **`mcpLeitura` entrou aqui**, vinda da
// allowlist. Ela custa **3** (`_cap_check(uid, 3)` na rota `leitura`), é a
// chamada mais cara da aba fora de `/possibilidades`, e devolvê-la para dentro
// de um `useEffect` reprova esta seção. O que isso protege, em uma frase:
// clicar num cartão de "Seus vigias" troca o ticker, e trocar o ticker não
// pode voltar a custar 3 chamadas em silêncio.
const METODOS = ["mcpCadeia", "mcpOperaveis", "mcpProposta", "mcpPossibilidades",
  "mcpSetupsListar", "mcpLeitura"];
// Um nome nos DOIS lados faria o teste dizer "pode" e "não pode" sobre a mesma
// chamada, e o próximo leitor acreditaria no que lhe conviesse.
ok("EFEITO_PERMITIDO e METODOS são disjuntos",
   EFEITO_PERMITIDO.every((m) => !METODOS.includes(m)));

// Corpo de cada `useEffect(` até o fechamento do argumento (heurística
// suficiente: os efeitos do arquivo são curtos e seguidos de `}, [`).
const efeitos = hook.split("useEffect(").slice(1).map((t) => t.split("}, [")[0]);
// Sanidade: sem ela um typo no fatiador faria tudo passar por vacuidade.
ok("o hook tem ao menos TRÊS efeitos (status, índice de vigias, troca de ticker)",
   efeitos.length >= 3);
// 2026-09-13 (Fase 27, plano 27-04) — a extração passou a olhar TODO
// `store.<método>`, e não só `store.mcp*`.
//
// Medido, não presumido: a allowlist acima ganhou `opcoesTecnico` e, com a
// regex antiga (`store\.(mcp[A-Za-z0-9_]*)`), a entrada nasceria INERTE —
// nenhum método sem o prefixo `mcp` era sequer visto pelo guardião. O buraco
// não é teórico: o 27-03 decidiu, com razão, que `mcp*` neste código
// significa "custa cota", então toda rota barata nasce FORA do prefixo — e
// era justamente essa classe de chamada que atravessava o portão sem ser
// conferida. Uma chamada cara que alguém batizasse sem o prefixo entraria
// num `useEffect` sem reprovar nada.
//
// O que a regra passa a dizer: TODA chamada ao store dentro de efeito precisa
// estar na allowlist, com o porquê escrito — o prefixo do nome não é mais o
// que decide quem é auditado.
const chamadasEmEfeito = [...new Set(
  efeitos.flatMap((corpo) => [...corpo.matchAll(/store\.([A-Za-z0-9_]+)/g)]
    .map((m) => m[1])))];
ok("sanidade: a extração enxerga chamada de store SEM o prefixo `mcp` (senão a allowlist nasceria inerte)",
   chamadasEmEfeito.some((m) => !/^mcp/.test(m)));
ok("sanidade: a extração acha ao menos DOIS store.* distintos dentro de efeitos",
   chamadasEmEfeito.length >= 2);
for (const m of chamadasEmEfeito) {
  ok(`store.${m} dentro de useEffect está na allowlist EFEITO_PERMITIDO`,
     EFEITO_PERMITIDO.includes(m));
}
for (const m of METODOS) {
  ok(`nenhum useEffect chama store.${m}`, efeitos.every((corpo) => !corpo.includes(m)));
}
// 2026-09-13 (Fase 27, plano 27-05) — **a âncora de sanidade mudou de método,
// e a troca é obrigatória.** Ela era `store.mcpLeitura`, que acabou de sair de
// todos os efeitos; mantida como estava, ela ficaria PERMANENTEMENTE FALSA — e
// o resultado não seria um vermelho honesto, seria o oposto: quem a visse
// falhar ia apagá-la, e sem ela um fatiador quebrado (um `"}, ["` que deixasse
// de casar) faria `efeitos` virar lista de corpos vazios e a seção INTEIRA
// passaria por vacuidade, com zero chamadas auditadas.
//
// `store.mcpStatus` é a substituta certa: continua dentro de um `useEffect`
// (é o frescor do cabeçalho, exceção pré-existente declarada na allowlist e,
// desde o 27-05, declarada também na tela) e não tem plano de sair de lá —
// o gate de frescor precisa existir na abertura (ADR-027, Decisão 8).
ok("sanidade: a fatia de efeito enxerga o que está dentro dele",
   efeitos.some((corpo) => corpo.includes("store.mcpStatus")));
// 2026-09-13 (Fase 27, plano 27-05): a leitura paga tem porta própria, e ela é
// um clique. Mesmo par de asserções das quatro ações da F3 logo abaixo —
// existe como `useCallback` no hook E é chamada pela tela; sem o segundo lado,
// um hook que exporta a função e uma tela que nunca a chama passaria verde
// com a leitura inalcançável.
ok("o hook exporta a ação abrirLeitura (a leitura paga, sob demanda)",
   /const abrirLeitura = useCallback/.test(hook) && /\babrirLeitura\b/.test(tela));
ok("a recarga pós-escrita não duplica o corpo da leitura (porta única)",
   /const recarregarLeitura = useCallback\(\(\) => \{ abrirLeitura\(\); \}/.test(hook));
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
//
// 2026-09-20, Fase 33 (33-04) — ACHADO FORA DO CENSO do plano (não estava nos
// itens 4/5/13): o controle de alvo/stop (campos, rótulos e o disparo que os
// nomeia) migrou inteiro para SecaoComparar.jsx, e `alvoNum`/`stopNum` (a
// derivação numérica) foram junto — único consumidor do par desde que o
// disparo saiu de OpcoesScreen.jsx. As quatro asserções abaixo passam a ler
// `secaoComparar`; a garantia (nomeado, nunca número solto) não afrouxa.
ok("o corpo de possibilidades nomeia alvo e stop",
   /alvo: o\.alvo/.test(hook) && /stop: o\.stop/.test(hook));
ok("a seção manda alvo e stop pelos campos próprios",
   /alvo: alvoNum/.test(secaoComparar) && /stop: stopNum/.test(secaoComparar));
ok("alvo e stop têm rótulo próprio na seção",
   /cp\.opcoesAlvoRotulo/.test(secaoComparar) && /cp\.opcoesStopRotulo/.test(secaoComparar));
ok("preço ausente vira ausência do cenário, nunca zero",
   /const alvoNum = ehNum\(num\(alvo\)\) && num\(alvo\) > 0 \? num\(alvo\) : undefined;/.test(secaoComparar));

// ---- 10) `null` nunca vira 0 ------------------------------------------------
// RESOLVIDO (2026-09-16, quick 260916-g6p): o achado de 2026-09-15 (Fase 32,
// 32-02) — CuradoriaEstruturas.jsx/CandidatoOpcao.jsx reprovando esta regra
// por causa do `|| 0` dentro de `porLote`/CTA de collar, com
// PropostaLastreada.jsx (Fase 28) carregando a MESMA cópia fora desta
// allowlist e por isso nunca flagrada — foi fechado corrigindo as TRÊS
// cópias (Task 1 desta quick): o guard passou a ENVOLVER a multiplicação/o
// `Math.abs` (`typeof X === "number" ? ... : null`) em vez do `|| 0` de
// dentro dela. A exceção nomeada por dois arquivos que existia aqui foi
// removida — TODOS os arquivos da allowlist `ARQUIVOS`, incluindo
// `PropostaLastreada.jsx` (agora presente nela), passam pela regra `OU_ZERO`
// sem exceção. Referência à origem preservada: Fase 32, plano 32-02.
const OU_ZERO = /\|\|\s*0\b/;
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} sem \`|| 0\` (ausência não é zero)`, !OU_ZERO.test(src));
}
ok("sanidade: a regex de `|| 0` pega o padrão quando ele existe",
   OU_ZERO.test("const v = dados.premio || 0;"));

// ---- 11) as rotas de METODOS alcançáveis pelos DOIS stores ------------------
// 2026-09-13 (Fase 27): a lista passou a incluir `mcpSetupsListar`, então este
// bloco cobre CINCO rotas — o par de stores e o `api.js`, como antes.
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
// 2026-09-20, Fase 33 (33-05): `CAMPO` (campo de formulário do job 3) e
// `ROLAGEM` (container de tabela de `Pernas`/`TabelaDeOpcoes`, job 3) saíram
// de OpcoesScreen.jsx — único consumidor de cada um era o job 3, extraído
// para SecaoAnalisar.jsx. `BOTAO` continua em OpcoesScreen.jsx (usado por
// `blocoLeituraDoServico`, pela carteira vazia e por SubAbaOperar) — a
// asserção passa a ler os DOIS arquivos, um para cada estilo.
ok("os botões novos nascem com alvo de toque de 44 px",
   /const BOTAO = \{[\s\S]{0,120}minHeight: "44px"/.test(tela)
   && /const CAMPO = \{[\s\S]{0,120}minHeight: "44px"/.test(secaoAnalisar));
ok("a tabela rola no container, não no body",
   /const ROLAGEM = \{ overflowX: "auto"/.test(secaoAnalisar));

// ---- 13) razão ganho/perda (F-01 do 24-VERIFICATION, plano 24-06) ----------
// O critério 1 do ROADMAP termina em "breakevens e razão ganho/perda", e ela
// não existia em lugar nenhum. Chega PRONTA do backend, adimensional. O que
// este bloco tranca é o que só se prova lendo o fonte: a tela não recalcula a
// razão, não a encosta no bloco de reais (razão não é dinheiro) e não a cala
// quando ela não existe — travessão mudo faria a pessoa achar que o app não
// calculou, e um número faria com que ela decidisse sobre uma razão que não
// existe, que é a pior das três saídas.
// 2026-09-20, Fase 33 (33-04): `RazaoGanhoPerda`/`Linha` migraram de
// OpcoesScreen.jsx para uiOpcoes.jsx (job 3 e job 4/SecaoComparar.jsx usam a
// MESMA implementação); `razao={item.razaoGanhoPerda}` migrou junto com o
// bloco "Possibilidades" para SecaoComparar.jsx. A garantia "a razão é
// renderizada nas DUAS seções" continua valendo, agora somando os arquivos.
// 2026-09-20, Fase 33 (33-05): `razao={proposta.dados.razaoGanhoPerda}`
// migrou junto com o job 3 para SecaoAnalisar.jsx — a checagem passa a ler
// esse arquivo em vez de `tela`.
const iRazaoAnalisar = secaoAnalisar.indexOf("razaoGanhoPerda");
const iRazaoPossib = secaoComparar.indexOf("razaoGanhoPerda");
ok("a razão é renderizada nas DUAS seções (Analisar e Possibilidades)",
   iRazaoAnalisar >= 0 && iRazaoPossib >= 0);
ok("a razão tem componente próprio, alimentado pelo campo do backend",
   /function RazaoGanhoPerda/.test(uiOpcoesFonte)
   && /razao=\{proposta\.dados\.razaoGanhoPerda\}/.test(secaoAnalisar)
   && /razao=\{item\.razaoGanhoPerda\}/.test(secaoComparar));
ok("sem número, a seção mostra o MOTIVO em vez de calar ou inventar",
   /razao\.motivo/.test(uiOpcoesFonte) && /ehNum\(razao\.valor\)/.test(uiOpcoesFonte));
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
// 2026-09-19, Fase 33 (33-01): `RecusaCobrada` migrou de OpcoesScreen.jsx
// para `uiOpcoes.jsx`. A definição passa a ser exigida na fonte NOVA.
ok("existe componente próprio para a linha da recusa cobrada",
   /function RecusaCobrada/.test(uiOpcoesFonte));
// A linha só pode aparecer com o campo do backend. Sem ele, a tela não
// afirma nada sobre cota: uma linha incondicional mentiria em todo 422 de
// pedido torto (`kind_invalido`, `lote_invalido`), que é recusa ANTES da rede
// e não custa chamada nenhuma.
ok("a linha é condicionada ao `cobrado` do detail E ao código do erro",
   /erro\.code !== "mcp_erro_de_tool"/.test(uiOpcoesFonte)
   && /cobrado !== true/.test(uiOpcoesFonte));
// A garantia "aparece nos DOIS ramos de erro" sobrevive à migração: 1 uso na
// cascata principal (que continua em OpcoesScreen.jsx, importando o
// componente) + 1 uso DENTRO da própria definição de ErroDoMcp (agora em
// uiOpcoes.jsx) — a soma continua 2, e continua provando as duas portas.
const iRecusaTela = tela.indexOf("<RecusaCobrada");
const iRecusaUi = uiOpcoesFonte.indexOf("<RecusaCobrada");
ok("a linha aparece nos DOIS ramos de erro (1 na cascata principal de OpcoesScreen.jsx + 1 dentro de ErroDoMcp em uiOpcoes.jsx)",
   iRecusaTela >= 0 && iRecusaUi >= 0);
ok("a linha é discreta (textMuted), não alarme",
   /function RecusaCobrada[\s\S]{0,400}T\.textMuted/.test(uiOpcoesFonte));
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
// ---- 15) as lacunas da leitura (24-11, achado ao vivo 2026-09-11) ---------
// Na tela do Alex, cinco campos da LEITURA DO ATIVO mostravam travessão e
// mais nada. Travessão mudo não é estado vazio: a pessoa não sabe se o app
// quebrou, se o ativo é estranho ou se falta dado (princípio 9). A saída
// escolhida foi dizer o motivo — sem preencher o número (seria fabricar,
// princípio 4) e sem recalcular o indicador (seria uma segunda fonte).
// 2026-09-20, Fase 33 (33-05): `LacunasDaLeitura`/`ROTULO_LEITURA` migraram
// de OpcoesScreen.jsx para SecaoAnalisar.jsx (job 3, único consumidor) — as
// checagens abaixo passam a ler esta fonte. O trânsito do dado agora cruza
// DOIS arquivos: OpcoesScreen.jsx lê `l.lacunas` e passa por prop;
// SecaoAnalisar.jsx repassa a prop crua para `<LacunasDaLeitura>`.
ok("existe componente próprio para as lacunas da leitura",
   /function LacunasDaLeitura/.test(secaoAnalisar));
ok("existe UM mapa rótulo↔campo, e ele cobre os cinco campos do achado",
   /const ROTULO_LEITURA = /.test(secaoAnalisar)
   && ["trend", "hv21", "hv63", "distance_from_sma63_pct", "range_63_sessions"]
        .every((c) => new RegExp(c + ":\\s*\"").test(secaoAnalisar)));
// Dois vocabulários divergiriam no primeiro rótulo renomeado, e a explicação
// passaria a nomear um campo que a tabela não mostra com esse nome.
ok("os rótulos do mapa são os MESMOS que a tabela exibe",
   ["Tendência", "HV 21", "HV 63", "Distância da média 63", "Faixa de 63 pregões"]
     .every((r) => (secaoAnalisar.match(new RegExp(r, "g")) || []).length >= 2));
ok("`lacunas` vazio ou ausente não renderiza nada — estado normal é silêncio",
   /function LacunasDaLeitura[\s\S]{0,600}return null;/.test(secaoAnalisar));
ok("a linha é discreta (textMuted), como o carimbo do pregão ao lado",
   /function LacunasDaLeitura[\s\S]{0,700}T\.textMuted/.test(secaoAnalisar));
ok("OpcoesScreen.jsx passa as lacunas do backend por prop para SecaoAnalisar",
   /lacunas=\{l && l\.lacunas\}/.test(tela));
ok("o bloco é renderizado com as lacunas recebidas por prop (sem recalcular)",
   /<LacunasDaLeitura[^>]*lacunas={lacunas}/.test(secaoAnalisar));

// O motivo é do backend e chega pronto. O front junta os RÓTULOS e nada mais:
// interpolá-lo dentro de outra frase aqui seria reescrever o que o serviço (e
// o guardião de texto do backend) já pesaram palavra por palavra.
// 2026-09-20, Fase 33 (33-05): `LacunasDaLeitura` migrou para
// SecaoAnalisar.jsx — a fatia passa a ser lida de lá.
const blocoLacunas = (secaoAnalisar.match(/function LacunasDaLeitura[\s\S]*?\n}/) || [""])[0];
const REESCREVE_MOTIVO = /motivo\s*\+|\+\s*[A-Za-z_$][\w$]*\.motivo|`[^`]*\$\{[^}]*motivo/;
ok("o motivo do backend só entra como ARGUMENTO de `cp.opcoesLacuna`",
   /cp\.opcoesLacuna\(/.test(blocoLacunas) && !REESCREVE_MOTIVO.test(blocoLacunas));
ok("sanidade: a regex pega uma reescrita do motivo",
   REESCREVE_MOTIVO.test('const s = "porque " + x.motivo;')
   && REESCREVE_MOTIVO.test("const s = `porque ${x.motivo}`;"));

// `range_63_sessions` chega SEMPRE como dict — com os dois extremos nulos
// quando a janela de 63 não fechou. Sem esta checagem a tela mostrava
// "— – —": travessão travestido de faixa, que se lê como formatação quebrada
// e não como ausência de dado.
// 2026-09-20, Fase 33 (33-05): `faixa` e o uso `valor={faixa(...)}` migraram
// juntos para SecaoAnalisar.jsx — único consumidor de cada um (job 3). A
// garantia ("UM travessão, nunca '— – —'") não afrouxa por troca de arquivo.
ok("a faixa de 63 usa o helper que devolve UM travessão sem os dois extremos",
   /const faixa = /.test(secaoAnalisar) && /valor={faixa\(behavior\.range_63_sessions\)}/.test(secaoAnalisar));

// A trava central do 24-11 do lado do front: nenhum campo da leitura passou a
// ser CALCULADO aqui. Fonte única — quem calcula é o serviço.
const RECALCULO = /Math\.(sqrt|log|pow|exp)\s*\(|desvio[_ ]?padr[ãa]o|stdev|std_dev|vari[âa]ncia/i;
for (const arq of readdirSync(dirOpcoes).filter((f) => /\.(js|jsx)$/.test(f))) {
  ok(`${arq} não recalcula indicador (nem hv, nem média, nem desvio)`,
     !RECALCULO.test(semComentario(ler(join(dirOpcoes, arq)))));
}
ok("sanidade: a regex pega a assinatura de um hv caseiro",
   RECALCULO.test("const hv = Math.sqrt(variancia) * Math.sqrt(252);")
   && RECALCULO.test("function desvioPadrao(xs) { return 0; }"));

// Sentinela em vez do texto real do backend: copiar a frase para cá criaria
// uma segunda cópia dela, que envelheceria sem ninguém notar. O que se prova
// é o TRÂNSITO — o que entra sai inteiro.
const MOTIVO_SENTINELA = "MOTIVO-VERBATIM-DO-BACKEND";
const AFIRMA_TAMANHO = /\b(tem|t[êe]m|possui|traz|cont[ée]m|apenas|somente|s[óo])\s+\d+\s+preg/i;
for (const modo of ["estudo", "operador"]) {
  const compor = COPY[modo].opcoesLacuna;
  ok(`${modo}: `+"`opcoesLacuna` é função", typeof compor === "function");
  const frase = typeof compor === "function"
    ? compor(["Tendência", "HV 21", "HV 63"], MOTIVO_SENTINELA) : "";
  ok(`${modo}: o motivo do backend aparece VERBATIM`, frase.includes(MOTIVO_SENTINELA));
  ok(`${modo}: os três rótulos aparecem na frase`,
     ["Tendência", "HV 21", "HV 63"].every((r) => frase.includes(r)));
  ok(`${modo}: a frase diz que ninguém estimou nada no lugar`, /estimad/i.test(frase));
  ok(`${modo}: a frase não afirma tamanho de série`, !AFIRMA_TAMANHO.test(frase));
  const uma = typeof compor === "function" ? compor(["HV 63"], MOTIVO_SENTINELA) : "";
  ok(`${modo}: um campo só também produz frase legível`,
     uma.includes("HV 63") && uma.includes(MOTIVO_SENTINELA) && !/ e :|, :/.test(uma));
}
ok("sanidade: a regex de tamanho de série pega a afirmação inventada",
   AFIRMA_TAMANHO.test("a série tem 42 pregões")
   && AFIRMA_TAMANHO.test("o histórico tem 21 pregões"));

// Paridade do conjunto `opcoes*` entre os dois modos — chave nova em um só
// ramo deixaria metade da base sem a informação.
const chaves = (m) => Object.keys(COPY[m]).filter((k) => k.startsWith("opcoes")).sort();
ok("o conjunto de chaves `opcoes*` continua idêntico nos dois modos",
   JSON.stringify(chaves("estudo")) === JSON.stringify(chaves("operador")));


console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
