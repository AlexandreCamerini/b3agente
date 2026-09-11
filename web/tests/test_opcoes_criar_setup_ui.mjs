// aba-opcoes F5 (plano 24-04, 2026-09-11) — guardião da seção "Criar setup".
//
// Os irmãos continuam trancando o que já existia: `test_opcoes_mcp_aba_ui.mjs`
// a tela da F2 (cadeia de estados principal, chip de frescor, erro por
// código) e `test_opcoes_analisar_ui.mjs` as seções da F3 (lote, breakeven,
// custo em chamadas, payoff). Este aqui tranca só o que a F5 acrescentou — e,
// como eles, prova o que SÓ se prova lendo o fonte:
//
//  · a seção de ESCRITA só renderiza sob `opcoes.criar_setup`. Esconder é
//    conveniência (o backend responde 403 sozinho, ADR-013), mas um botão que
//    sempre dá 403 é pior que botão nenhum — e some-lo por engano é o defeito
//    silencioso que nenhum teste de backend pega;
//  · `problems` item a item. Agregar a lista numa frase apagaria a única
//    informação acionável que a pessoa tem para corrigir o setup;
//  · o `cru` da LLM sai como TEXTO, com pre-wrap. É resposta de terceiro
//    renderizada na página: `dangerouslySetInnerHTML` ali seria XSS servido
//    pelo nosso próprio backend;
//  · nenhum vocabulário da DSL vive no front (ENG-06 aplicado à tela): os
//    nomes de indicador e de padrão chegam DENTRO de `conditions`, e copiá-los
//    para cá criaria a segunda cópia que diverge do contrato vivo;
//  · a ressalva do backtest é FIXA, no mesmo bloco dos números — não é
//    tooltip nem fica atrás de um toque. É o texto de maior risco regulatório
//    da fase: contagem de histórico lida como promessa;
//  · o botão de GRAVAR só existe depois do ramo do ensaio bem-sucedido;
//  · desativar exige DOIS toques.
//
// Cada regex de defeito carrega asserção de SANIDADE: sem ela, um typo (ou um
// Unicode diferente) faria o assert passar por vacuidade, para sempre.
//
// Roda sem build: `node web/tests/test_opcoes_criar_setup_ui.mjs`.
import { readFileSync, existsSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const dirOpcoes = join(here, "..", "src", "opcoes");
const ler = (p) => readFileSync(p, "utf8");

// A pasta INTEIRA, e não uma lista fixa: arquivo novo em `web/src/opcoes/`
// entra automaticamente nas regras de vocabulário e de HTML cru. Uma lista
// fixa deixaria o próximo componente fora da varredura em silêncio.
const ARQUIVOS = readdirSync(dirOpcoes).filter((f) => /\.jsx?$/.test(f)).sort();
const brutos = Object.fromEntries(ARQUIVOS.map((f) => [f, ler(join(dirOpcoes, f))]));
// Sem comentários: eles citam os mesmos termos ao EXPLICAR as decisões
// ("nunca `dangerouslySetInnerHTML`", "não é expectativa de retorno"), e
// contá-los faria o guardião se auto-invalidar.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const fontes = Object.fromEntries(
  Object.entries(brutos).map(([k, v]) => [k, semComentario(v)]));

const tela = fontes["OpcoesScreen.jsx"];
const criar = fontes["CriarSetup.jsx"];
const hook = fontes["useOpcoesMcp.js"];
const api = semComentario(ler(join(here, "..", "src", "api.js")));
const persistencia = semComentario(ler(join(here, "..", "src", "persistence.js")));

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) a seção só renderiza com `opcoes.criar_setup` -----------------------
ok("CriarSetup.jsx existe", existsSync(join(dirOpcoes, "CriarSetup.jsx")));
ok("CriarSetup exporta o componente", /export default function CriarSetup/.test(criar));
ok("CriarSetup não importa App.jsx (seria ciclo)",
   !/from\s+["'][^"']*App\.jsx["']/.test(brutos["CriarSetup.jsx"]));
ok("CriarSetup declara o bloco VARKEY/TOKENS/T local",
   /const VARKEY = /.test(criar) && /const TOKENS = \[/.test(criar)
   && /const T = Object\.fromEntries/.test(criar));
const PERMISSAO = /opcoes\.criar_setup/;
ok("a tela cita a permissão `opcoes.criar_setup`", PERMISSAO.test(tela));
ok("a permissão vira um booleano de render (`podeCriarSetup`)",
   /const podeCriarSetup = permissoes\.includes\("opcoes\.criar_setup"\);/.test(tela));
ok("a lista de permissões vem de `ctx.authUser.permissions` (a fonte que o app já usa)",
   /ctx\.authUser && Array\.isArray\(ctx\.authUser\.permissions\)/.test(tela));
ok("sem lista de permissões, falha FECHADO (array vazio, nunca 'libera tudo')",
   /\? ctx\.authUser\.permissions : \[\];/.test(tela));
// O que este par tranca de verdade: a MONTAGEM do componente e o botão de
// desativar estão os DOIS sob a mesma condição. Sem isto, tirar a condição de
// um deles passaria despercebido.
ok("a montagem de <CriarSetup é condicionada a `podeCriarSetup`",
   /\{podeCriarSetup \? \([\s\S]{0,400}<CriarSetup/.test(tela));
ok("o botão de desativar também é condicionado a `podeCriarSetup`",
   /\{podeCriarSetup \? \([\s\S]{0,300}<BotaoDesativar/.test(tela));
ok("sanidade: a regex da permissão pega o literal quando ele existe",
   PERMISSAO.test('permissoes.includes("opcoes.criar_setup")')
   && !PERMISSAO.test('permissoes.includes("obs.ver")'));

// ---- 2) `problems` item a item, nunca agregado ------------------------------
const PROBLEMS_MAP = /problems\.map\(/;
const PROBLEMS_JOIN = /problems\.join\(/;
ok("os problemas do serviço são renderizados item a item (`problems.map(`)",
   PROBLEMS_MAP.test(criar));
ok("os problemas NÃO são agregados numa frase (`problems.join(`)",
   !PROBLEMS_JOIN.test(criar));
ok("cada problema vira um <li> próprio", /<li key=\{i\}[\s\S]{0,200}\{String\(p\)\}<\/li>/.test(criar));
ok("sanidade: as duas regex de `problems` pegam os padrões quando eles existem",
   PROBLEMS_MAP.test("problems.map((p) => p)") && PROBLEMS_JOIN.test('problems.join(", ")'));

// ---- 3) o `cru` da LLM sai escapado, com pre-wrap ---------------------------
const HTML_CRU = /dangerouslySetInnerHTML/;
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} não injeta HTML cru`, !HTML_CRU.test(src));
}
ok("sanidade: a regex de HTML cru pega o padrão quando ele existe",
   HTML_CRU.test("<div dangerouslySetInnerHTML={{ __html: cru }} />"));
ok("o `cru` é renderizado como nó de texto num <pre>", /<pre style=\{CRU\}>\{/.test(criar));
ok("o estilo do `cru` preserva as quebras (pre-wrap)",
   /const CRU = \{[\s\S]{0,80}whiteSpace: "pre-wrap"/.test(criar));

// ---- 4) nenhum vocabulário da DSL hardcodado em web/src/opcoes/ -------------
// Mesma regra do ENG-06 aplicada ao front: indicador, operador e padrão
// chegam DENTRO de `conditions`, vindos do serviço. Uma lista aqui seria a
// segunda cópia do contrato — a que ninguém lembra de atualizar.
const DSL = /crosses_above|bullish_engulfing|rel_volume|inside_bar/;
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} sem vocabulário da DSL hardcodado`, !DSL.test(src));
}
ok("sanidade: a regex de DSL pega o vocabulário quando ele existe",
   DSL.test('if (c.indicator === "crosses_above") return "cruzou para cima";')
   && DSL.test('const p = "bullish_engulfing";'));
ok("as condições são varridas pelas chaves que CHEGARAM, não por uma lista local",
   /Object\.entries\(c\)[\s\S]{0,220}\.map\(\(\[k, v\]\) => k \+ ": " \+ valorDeCampo\(v\)\)/.test(criar));

// ---- 5) a ressalva do backtest é FIXA, junto dos números --------------------
const iBacktest = criar.indexOf("opcoesBacktestTitulo");
const iDisparos = criar.indexOf("opcoesBacktestDisparos");
const iRetorno = criar.indexOf("opcoesBacktestRetorno");
const iRessalva = criar.indexOf("opcoesBacktestRessalva");
ok("o bloco de backtest existe inteiro (título, disparos, retorno e ressalva)",
   iBacktest > 0 && iDisparos > iBacktest && iRetorno > iDisparos && iRessalva > iRetorno);
// "Mesmo bloco" no fonte = dentro da mesma fatia do `{backtest ? (…) : (…)}`.
// Se a ressalva escapasse para fora dela, apareceria sem os números (ou pior:
// os números apareceriam sem ela).
const blocoBacktest = criar.slice(iBacktest, criar.indexOf("</div>", iRessalva));
ok("a ressalva mora no MESMO bloco dos números", blocoBacktest.includes("opcoesBacktestRessalva"));
ok("a ressalva não está atrás de toggle/tooltip/estado",
   !/(mostrarRessalva|tooltip|title=\{[^}]*Ressalva)/i.test(criar));
// Contagem de histórico não é P&L de posição: pintá-la de verde/vermelho já
// seria uma promessa. `T.negative` só aparece em caixa de ERRO e na
// confirmação de desativação, nunca num número de backtest.
ok("nenhum número do backtest ganha cor de ganho ou de perda",
   !/T\.(negative|positive)/.test(blocoBacktest) && !/P\.(up|down|positive|negative)/.test(blocoBacktest));
ok("sanidade: a fatia do backtest enxerga o que está dentro dela",
   blocoBacktest.includes("pregoes_avaliaveis")
   && blocoBacktest.includes("opcoesBacktestDisparos")
   && blocoBacktest.includes("opcoesBacktestRetorno"));

// ---- 6) nenhum texto de expectativa ----------------------------------------
const EXPECTATIVA = /retorno esperado|expectativa de retorno|média de ganho|deve render|vai render/i;
for (const [nome, src] of Object.entries(fontes)) {
  ok(`${nome} sem texto de expectativa de retorno`, !EXPECTATIVA.test(src));
}
// Nas chaves de copy, a ÚNICA ocorrência permitida é a da própria ressalva,
// que NEGA a ideia ("Não é expectativa de retorno").
const CHAVES_F5 = ["opcoesCriarTitulo", "opcoesCriarAjuda", "opcoesCriarPlaceholder",
  "opcoesCriarBotao", "opcoesCriarConfirmar", "opcoesCriarDesativar",
  "opcoesCriarConfirmarDesativacao", "opcoesCriarProblemas", "opcoesCriarCru",
  "opcoesCriarFaltando", "opcoesCriarGravado", "opcoesCriarDesativado",
  "opcoesCriarSemPermissao", "opcoesBacktestTitulo", "opcoesBacktestDisparos",
  "opcoesBacktestRetorno", "opcoesBacktestRessalva", "opcoesDadoAtrasado"];
for (const modo of ["estudo", "operador"]) {
  const semRessalva = CHAVES_F5.filter((k) => k !== "opcoesBacktestRessalva")
    .map((k) => COPY[modo][k])
    .map((v) => (typeof v === "function" ? v("d+5", "1%", "2%", 3) + v(null, null, null, null) : v))
    .join(" ");
  ok(`${modo}: nenhuma chave nova promete retorno`, !EXPECTATIVA.test(semRessalva));
  ok(`${modo}: a ressalva do backtest NEGA expectativa e nega taxa de acerto`,
     /não é expectativa de retorno/i.test(COPY[modo].opcoesBacktestRessalva)
     && /não é taxa de acerto/i.test(COPY[modo].opcoesBacktestRessalva));
}
ok("a ressalva do backtest é IDÊNTICA nos dois modos (é afirmação, não tom)",
   COPY.estudo.opcoesBacktestRessalva === COPY.operador.opcoesBacktestRessalva);
ok("sanidade: a regex de expectativa pega o padrão quando ele existe",
   EXPECTATIVA.test("o retorno esperado desta condição é de 2%")
   && EXPECTATIVA.test("média de ganho por disparo"));

// ---- 7) o botão de GRAVAR só existe depois do ramo do ensaio ----------------
// `opcoesCriarConfirmarDesativacao` CONTÉM `opcoesCriarConfirmar` como
// substring — por isso a busca exclui o sufixo, senão o assert mediria o
// botão errado e passaria (ou falharia) por acidente.
const iDryRun = criar.indexOf('"dry_run"');
const mGravar = /opcoesCriarConfirmar(?!Desativacao)/.exec(criar);
ok("a tela distingue o ensaio (`dry_run`) dos demais estados", iDryRun > 0);
ok("o botão de GRAVAR aparece no fonte DEPOIS do ramo de `dry_run`",
   !!mGravar && mGravar.index > iDryRun);
ok("o que volta para gravar é o MESMO objeto exibido (nada é recompilado)",
   /onConfirmar\(dados\.setup\)/.test(criar));
ok("o disparo de compilar manda só a descrição (o ticker é o do cabeçalho)",
   /store\.mcpSetupCompilar\(\{ descricao: o\.descricao, ticker: alvoAtual \}\)/.test(hook));
ok("gravar e desativar recarregam a leitura do ticker (a lista não fica velha)",
   (hook.match(/recarregarLeitura\(\);/g) || []).length >= 2
   && /const recarregarLeitura = useCallback/.test(hook));
ok("sanidade: a busca do botão de gravar ignora o botão de desativação",
   /opcoesCriarConfirmar(?!Desativacao)/.test("cp.opcoesCriarConfirmar")
   && !/opcoesCriarConfirmar(?!Desativacao)/.test("cp.opcoesCriarConfirmarDesativacao"));

// ---- 8) desativar exige DOIS toques ----------------------------------------
ok("existe o componente de desativação em dois toques", /export function BotaoDesativar/.test(criar));
ok("há um estado intermediário de confirmação", /const \[confirmando, setConfirmando\] = useState\(false\)/.test(criar));
ok("o primeiro toque NÃO age — só arma a confirmação",
   /if \(!confirmando\) \{ setConfirmando\(true\); return; \}/.test(criar));
ok("o segundo toque age e desarma", /setConfirmando\(false\);[\s\S]{0,80}onDesativar\(nome\)/.test(criar));
ok("o botão nomeia o setup para quem usa leitor de tela",
   /aria-label=\{rotulo \+ " " \+ \(nome \|\| ""\)\}/.test(criar));
ok("sanidade: sem o estado intermediário, o assert de dois toques falharia",
   !/const \[confirmando, setConfirmando\] = useState\(false\)/.test("onClick={() => onDesativar(nome)}"));

// ---- 9) chaves `opcoes*` idênticas nos dois modos ---------------------------
for (const k of CHAVES_F5) {
  ok(`COPY tem ${k} nos dois modos`, !!COPY.estudo[k] && !!COPY.operador[k]);
}
const kEstudo = Object.keys(COPY.estudo).filter((k) => k.startsWith("opcoes")).sort();
const kOperador = Object.keys(COPY.operador).filter((k) => k.startsWith("opcoes")).sort();
ok("o conjunto de chaves opcoes* é IGUAL nos dois modos",
   JSON.stringify(kEstudo) === JSON.stringify(kOperador));
ok("as funções novas de copy toleram argumento nulo",
   CHAVES_F5.every((k) => ["estudo", "operador"].every((m) => {
     const v = COPY[m][k];
     return typeof v !== "function" || typeof v(null, null, null, null) === "string";
   })));
// [R-12]: o ramo ESTUDO descreve condição, nunca dá ordem. A seção de criação
// é de ESCRITA, e é aqui que a voz de mesa vazaria primeiro.
ok("nenhuma chave nova do ramo estudo traz vocabulário de ordem",
   !/\bcomprar\b|\bvender\b|\bexecute\b/i.test(
     CHAVES_F5.map((k) => COPY.estudo[k])
       .map((v) => (typeof v === "function" ? v("d+5", "1%", "2%", 3) + v(null, null, null, null) : v))
       .join(" ")));

// ---- 10) as três rotas alcançáveis pelos DOIS stores ------------------------
const METODOS = ["mcpSetupCompilar", "mcpSetupConfirmar", "mcpSetupDesativar"];
const iServer = persistencia.indexOf("function serverStore");
const iDevice = persistencia.indexOf("function deviceStore");
ok("os dois stores foram encontrados", iServer > 0 && iDevice > iServer);
for (const m of METODOS) {
  ok(`${m} existe no serverStore`, persistencia.slice(iServer, iDevice).includes(m));
  ok(`${m} existe no deviceStore`, persistencia.slice(iDevice).includes(m));
  ok(`${m} existe em api.js`, api.includes(m + ":"));
}
// Compilar é a ÚNICA rota da aba que chama LLM — com os 30 s das irmãs, o
// cliente desistiria depois de o servidor já ter gasto a chamada de modelo.
ok("compilar usa TIMEOUT_LLM; confirmar e desativar não",
   /mcpSetupCompilar: \(body\) => req\("POST", "\/api\/options\/mcp\/setups\/compilar", body, TIMEOUT_LLM\)/.test(api)
   && /mcpSetupConfirmar: \(body\) => req\("POST", "\/api\/options\/mcp\/setups\/confirmar", body, 30000\)/.test(api));
ok("o nome do setup é escapado na URL de desativar (é entrada do usuário)",
   /mcpSetupDesativar: \(name\) => req\("POST", "\/api\/options\/mcp\/setups\/" \+ encodeURIComponent\(name\)/.test(api));

// ---- 11) estados, alvo de toque e `null` que não vira 0 --------------------
const iCarregando = criar.indexOf("opcoesCarregando");
const iErro = criar.indexOf("<ErroDaCriacao");
const iEnsaio = criar.indexOf("<Ensaio");
ok("a seção repete a cadeia carregando → erro → dados",
   iCarregando > 0 && iErro > iCarregando && iEnsaio > iErro);
ok("os botões novos nascem com alvo de toque de 44 px",
   /const BOTAO = \{[\s\S]{0,120}minHeight: "44px"/.test(criar));
ok("o campo de descrição tem rótulo real e ajuda associada",
   /<label htmlFor="opcoes-criar-descricao"/.test(criar)
   && /aria-describedby=\{idAjuda\}/.test(criar));
ok("o disparo exige um mínimo de caracteres (LLM paga não se gasta com 'oi')",
   /const MIN_DESCRICAO = \d+;/.test(criar)
   && /descricao\.trim\(\)\.length >= MIN_DESCRICAO/.test(criar));
const OU_ZERO = /\|\|\s*0\b/;
ok("CriarSetup.jsx sem `|| 0` (ausência não é zero)", !OU_ZERO.test(criar));
ok("sanidade: a regex de `|| 0` pega o padrão quando ele existe",
   OU_ZERO.test("const v = backtest.disparos || 0;"));

console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
