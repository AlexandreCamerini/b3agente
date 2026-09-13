// Fase 27, plano 27-02 (2026-09-13) — guardião do UNIVERSO da aba Opções.
//
// O defeito que originou a fase, em uma frase: a aba consultava tickers
// avulsos da watchlist, e os vigias gravados só apareciam com o ticker deles
// aberto. Este arquivo tranca o lado do universo. O irmão
// `test_opcoes_vigias_ui.mjs` tranca o bloco "Seus vigias".
//
// O que cada seção reprova, e por que só se prova lendo o fonte:
//
//  1. UNIVERSO = CARTEIRA (D3 do 27-CONTEXT). Voltar a tela para
//     `ctx.data.watchlist` reabriria o defeito sem quebrar teste de render
//     nenhum: a lista continuaria cheia, só que do universo errado.
//     Watchlist é intenção; posição é lastro, e é o lastro que decide o que
//     dá para montar.
//
//  2. O TICKER CONTINUA NASCENDO VAZIO. Este é o guardião que impede a
//     "correção" óbvia e errada. Selecionar um ativo dispara `mcpLeitura`
//     pelo efeito de troca de ticker (`useOpcoesMcp.js`), e essa chamada
//     custa 3 no cap do ADR-027 — auto-selecionar cobraria 3 consultas de
//     quem só abriu a aba, contra o §3.3 ("custo de MCP só em clique
//     explícito, nunca ao abrir tela"). A aba não abre vazia por causa da
//     LISTA das posições e do bloco "Seus vigias", os dois de custo zero;
//     ela abre sem ATIVO ESCOLHIDO, que é outra coisa (D4).
//
//  3. CARTEIRA VAZIA TEM CAMINHO (D2). Estado vazio sem saída devolve à
//     pessoa a tarefa de descobrir o porquê, e o destino é a Carteira — não
//     o Mercado, não a watchlist —, por decisão explícita do Alex.
//
//  4. LASTRO LIVRE COM FONTE ÚNICA (Task 3 do 27-02). A subtração
//     `qty - qtyTravada` tem UMA implementação no front (`finance.js`,
//     gêmea de `store.qty_livre`); uma segunda aqui divergiria da primeira
//     na correção seguinte, em silêncio, com o mesmo nome na tela.
//
// Roda sem build: `node web/tests/test_opcoes_universo_carteira.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const ler = (...p) => readFileSync(join(here, "..", ...p), "utf8");

const telaBruta = ler("src", "opcoes", "OpcoesScreen.jsx");
const app = ler("src", "App.jsx");

// Sem comentários: eles citam os mesmos termos ao EXPLICAR as decisões
// ("não se recalcula `qty - qtyTravada` aqui"), e contá-los faria o guardião
// se auto-invalidar. Mesma função de `test_opcoes_mcp_aba_ui.mjs`.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const tela = semComentario(telaBruta);

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// ---- 1) o universo é a carteira, e a watchlist saiu de cena ----------------
ok("a tela deriva o universo de ctx.data.positions",
   /ctx\.data\.positions/.test(tela));
ok("a tela NÃO lê mais ctx.data.watchlist (D3: watchlist é intenção, posição é lastro)",
   !/ctx\.data\.watchlist/.test(tela));
ok("existe a constante `carteira`, filtrada por posição com ticker",
   /const carteira = \(\(ctx && ctx\.data && ctx\.data\.positions\) \|\| \[\]\)\.filter/.test(tela));
ok("o seletor de ativos mapeia a CARTEIRA (não uma lista de strings solta)",
   /carteira\.map\(\(p\) =>/.test(tela));
ok("o seletor só aparece com carteira não vazia", /carteira\.length > 0 \? seletor/.test(tela));
ok("sanidade: a regex de watchlist pega o padrão quando ele existe",
   /ctx\.data\.watchlist/.test("const w = (ctx && ctx.data && ctx.data.watchlist) || [];"));

// ---- 2) o ticker continua nascendo VAZIO -----------------------------------
// Forma exata, e não `useState("")` genérico: a tela tem outros estados que
// nascem vazios (tese, vencimento, alvo, stop, painel), e um assert genérico
// continuaria verde com o ticker auto-selecionado.
ok("o ticker nasce vazio — nada de inicializador que escolhe o primeiro ativo",
   /const \[ticker, setTicker\] = useState\(""\);/.test(tela));
// `setTicker` dentro de efeito = auto-seleção por outro caminho, e o custo é
// o mesmo: `mcpLeitura` sai sozinha e debita 3 do cap.
const efeitosDaTela = tela.split("useEffect(").slice(1).map((t) => t.split("}, [")[0]);
ok("nenhum useEffect da tela chama setTicker (auto-seleção por efeito é o mesmo defeito)",
   efeitosDaTela.every((corpo) => !corpo.includes("setTicker")));
const totalSetTicker = (tela.match(/setTicker\(/g) || []).length;
const emEfeito = efeitosDaTela
  .reduce((n, corpo) => n + (corpo.match(/setTicker\(/g) || []).length, 0);
ok("sanidade: existe setTicker FORA de efeito (a escolha manual, em escolherTicker)",
   totalSetTicker - emEfeito >= 1);
ok("escolherTicker continua sendo toggle (desselecionar segue possível)",
   /setTicker\(t === ticker \? "" : t\);/.test(tela));

// ---- 3) carteira vazia: motivo + caminho para a Carteira (D2) --------------
ok("App.jsx expõe ctx.goCarteira", /goCarteira: \(\) =>/.test(app));
ok("goCarteira leva à CARTEIRA (os três setters, como o goAgente)",
   /goCarteira: \(\) => \{ setPerfilView\("hub"\); setTab\("carteira"\); setCarteiraView\("main"\); \}/.test(app));
ok("a tela chama ctx.goCarteira no estado vazio", /ctx\.goCarteira\(\)/.test(tela));
const iVazia = tela.indexOf("cp.opcoesCarteiraVazia");
const iEscolher = tela.indexOf("cp.opcoesEscolherAtivo");
ok("os dois estados vazios existem", iVazia >= 0 && iEscolher >= 0);
ok("carteira vazia vem ANTES de 'escolha um ativo' (sem posição, não há o que escolher)",
   iVazia < iEscolher);
ok("o botão do estado vazio reusa o estilo com alvo de toque de 44 px",
   /\.\.\.BOTAO, width: "100%", marginTop: "12px"[\s\S]{0,120}cp\.opcoesIrParaCarteira/.test(tela));

for (const modo of ["estudo", "operador"]) {
  for (const k of ["opcoesCarteiraVazia", "opcoesIrParaCarteira"]) {
    ok(`COPY.${modo}.${k} existe e não é vazio`,
       typeof COPY[modo][k] === "string" && !!COPY[modo][k].trim());
  }
  ok(`${modo}: opcoesEscolherAtivo não fala mais em watchlist`,
     !/watchlist/i.test(COPY[modo].opcoesEscolherAtivo));
  ok(`${modo}: opcoesEscolherAtivo aponta a CARTEIRA`,
     /carteira/i.test(COPY[modo].opcoesEscolherAtivo));
  ok(`${modo}: o texto de carteira vazia nega a watchlist como substituta (D2)`,
     /watchlist/i.test(COPY[modo].opcoesCarteiraVazia)
     && /lastro/i.test(COPY[modo].opcoesCarteiraVazia));
}
// Voz por modo, como `test_vocabulario_opcoes.mjs` já exige do subtítulo:
// texto idêntico nos dois ramos é a regra para estado de conta/sistema, e
// este não é um deles.
ok("o texto de carteira vazia DIFERE entre Estudo e Operador",
   COPY.estudo.opcoesCarteiraVazia !== COPY.operador.opcoesCarteiraVazia);
ok("o rótulo do botão também tem voz por modo",
   COPY.estudo.opcoesIrParaCarteira !== COPY.operador.opcoesIrParaCarteira);

// ---- 4) lastro livre no cartão, com FONTE ÚNICA ---------------------------
// O número que hoje só aparece na recusa do backend ("Lastro insuficiente:
// N ação(ões) livres de PETR4") passa a aparecer antes da tentativa. O que
// este bloco protege não é a exibição — é a ARITMÉTICA: a subtração
// `qty - qtyTravada` tem UMA implementação no front (`finance.js`, gêmea de
// `store.qty_livre`), e uma segunda aqui divergiria da primeira na correção
// seguinte, em silêncio, com o mesmo nome na tela.
ok("OpcoesScreen.jsx IMPORTA qtyLivre de ../finance.js (linha de import, não identificador solto)",
   /import\s*\{\s*qtyLivre\s*\}\s*from\s*["']\.\.\/finance\.js["']/.test(tela));
ok("e a usa de fato (import sem uso seria fachada)", /qtyLivre\(pos\)/.test(tela));
// Mesma regex de `test_carteira_lastro_ui.mjs`, que já protege App.jsx do
// mesmo defeito. Comentários foram removidos acima: citar `qtyTravada` numa
// EXPLICAÇÃO é legítimo, reimplementar a subtração não é.
ok("OpcoesScreen.jsx NÃO reimplementa a subtração qty - qtyTravada",
   !/qty\s*-\s*\(?[A-Za-z.]*qtyTravada/.test(tela));
ok("sanidade: a regex de subtração pega o padrão quando ele existe",
   /qty\s*-\s*\(?[A-Za-z.]*qtyTravada/.test("const livre = pos.qty - (pos.qtyTravada || 0);"));
ok("o divisor do contrato é constante NOMEADA, espelho de store.py (qty = contratos * 100)",
   /const ACOES_POR_CONTRATO = 100;/.test(tela) && /ACOES_POR_CONTRATO\)/.test(tela));
ok("existe componente próprio para o lastro, alimentado pela posição do ctx",
   /function LastroDoAtivo/.test(tela) && /<LastroDoAtivo pos=\{posicaoSelecionada\}/.test(tela));
ok("ausência de quantidade vira travessão COM motivo, nunca 0",
   /"— " \+ \(c\.opcoesLastroSemDado/.test(tela));
ok("a linha de travadas só aparece quando há travadas (0 travadas seria ruído)",
   /pos\.qtyTravada > 0\) \? pos\.qtyTravada : null/.test(tela));

for (const modo of ["estudo", "operador"]) {
  for (const k of ["opcoesLastroLivre", "opcoesLastroTravado"]) {
    ok(`COPY.${modo}.${k} é função`, typeof COPY[modo][k] === "function");
  }
  for (const k of ["opcoesLastroAjuda", "opcoesLastroSemDado"]) {
    ok(`COPY.${modo}.${k} existe e não é vazio`,
       typeof COPY[modo][k] === "string" && !!COPY[modo][k].trim());
  }
  ok(`${modo}: a ajuda declara a régua 1 contrato = 100 ações`,
     /100 ações/.test(COPY[modo].opcoesLastroAjuda));
  ok(`${modo}: a ajuda diz, na própria tela, que nenhuma ordem sai daqui`,
     /ordem/i.test(COPY[modo].opcoesLastroAjuda));
  ok(`${modo}: o motivo da trava nomeia a call coberta (mesmo vocabulário da Carteira)`,
     /call coberta/i.test(COPY[modo].opcoesLastroTravado(100)));
  ok(`${modo}: sem número, as funções devolvem travessão e não 0`,
     COPY[modo].opcoesLastroLivre(null, null).includes("—")
     && COPY[modo].opcoesLastroTravado(null).includes("—"));
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
