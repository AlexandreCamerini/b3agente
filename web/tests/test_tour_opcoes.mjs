// Fase 26, achado A4 (2026-09-12) — O TOUR E A AJUDA IGNORAVAM DUAS TELAS.
//
// Os dois defeitos, medidos antes da correção:
//
//  1. O tour abre sobre o "Acompanhar" (`const [tab, setTab] = useState(
//     "evolucao")`) e o primeiro passo do funil mandava a pessoa "Descobrir no
//     Radar" — apontava para outra tela antes de dizer onde ela tinha caído.
//  2. Nem `tourPassos` nem `ajudaSecoes` citavam a aba Opções, que é o 5º item
//     da barra inferior desde a Fase 24. O ícone existia e não tinha
//     explicação em lugar nenhum do app.
//
// O que este guardião trava (contagem + conteúdo, não texto exato — copy pode
// ser reescrita; o que não pode é uma tela sumir da explicação):
//
//  · `tourPassos` tem 6 passos (eram 4: +1 do passo zero, +1 de Opções);
//  · o PRIMEIRO passo nomeia "Acompanhar" e NÃO cita o Radar;
//  · algum passo apresenta a aba Opções;
//  · `ajudaSecoes` tem uma seção da aba Opções, e ela diz que nenhuma ordem
//    sai dali (a tela mostra cadeia e payoff — a frase é o que impede a
//    leitura errada, princípios 1/2 do CLAUDE.md);
//  · `docs/AJUDA.md` espelha a seção nova (a regra está escrita no topo
//    daquele arquivo: "ao mudar um, atualize o outro").
//
// Executa as DUAS funções de verdade, com um `cp` de mentira, em vez de
// casar regex no arquivo: contar passos por regex daria falso verde na
// primeira reorganização do array.
//
// Roda sem build e sem servidor: `node web/tests/test_tour_opcoes.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const ajudaMd = readFileSync(join(here, "..", "..", "docs", "AJUDA.md"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// `App.jsx` importa React/CSS e não é importável aqui — as duas funções são
// puras (recebem `cp`/`operador`, devolvem array), então são extraídas do
// fonte e avaliadas isoladas. Mesma técnica do test_vocabulario_espelho.mjs,
// que também lê fonte em vez de importar.
function extrair(nome, fonte) {
  const i = fonte.indexOf("function " + nome + "(");
  if (i < 0) return null;
  let nivel = 0, dentro = false;
  for (let k = i; k < fonte.length; k++) {
    if (fonte[k] === "{") { nivel++; dentro = true; }
    else if (fonte[k] === "}") { nivel--; if (dentro && nivel === 0) return fonte.slice(i, k + 1); }
  }
  return null;
}

const fonteTour = extrair("tourPassos", app);
const fonteAjuda = extrair("ajudaSecoes", app);
ok("tourPassos foi encontrada em App.jsx", !!fonteTour);
ok("ajudaSecoes foi encontrada em App.jsx", !!fonteAjuda);

const tourPassos = fonteTour ? eval("(" + fonteTour + ")") : null;   // eslint-disable-line no-eval
const ajudaSecoes = fonteAjuda ? eval("(" + fonteAjuda + ")") : null; // eslint-disable-line no-eval

for (const modo of ["estudo", "operador"]) {
  const cp = COPY[modo];
  const passos = tourPassos(cp);
  const texto = (p) => p.join(" ");

  // ------------------------------------------------------------ contagem
  ok(`[${modo}] o tour tem 6 passos (4 antigos + passo zero + Opções)`,
     passos.length === 6, "achou " + passos.length);

  // --------------------------------------- 1. o tour começa onde o app abre
  ok(`[${modo}] o PRIMEIRO passo nomeia "Acompanhar" (a tela em que o app abre)`,
     /Acompanhar/.test(texto(passos[0])),
     "o tour voltou a começar sem dizer onde a pessoa está");
  ok(`[${modo}] o primeiro passo NÃO manda procurar o Radar/Mesa`,
     !new RegExp(cp.tituloRadar).test(texto(passos[0])),
     "apontar outra tela no passo 1 é exatamente o defeito do achado A4");

  // ------------------------------------------- 2. a aba Opções é apresentada
  const rotuloOpc = cp.tituloOpcoes || "Opções";
  ok(`[${modo}] algum passo do tour apresenta a aba ${rotuloOpc}`,
     passos.some((p) => new RegExp(rotuloOpc).test(texto(p))));

  // ------------------------------------------------- 3. a Ajuda cobre a aba
  const secoes = ajudaSecoes(cp, modo === "operador");
  const secaoOpc = secoes.find(([titulo]) => new RegExp(rotuloOpc, "i").test(titulo));
  ok(`[${modo}] ajudaSecoes tem uma seção cujo título nomeia ${rotuloOpc}`, !!secaoOpc);
  if (secaoOpc) {
    ok(`[${modo}] a seção de ${rotuloOpc} diz que nenhuma ordem sai dali`,
       /ordem/i.test(secaoOpc[1].join(" ")),
       "a tela mostra cadeia e payoff; sem a frase, a pessoa pode achar que envia ordem");
    ok(`[${modo}] a seção de ${rotuloOpc} avisa que a leitura é de fim de pregão`,
       /fim de pregão/i.test(secaoOpc[1].join(" ")),
       "princípio 3 do CLAUDE.md: dizer se o dado é tempo real, atrasado ou histórico");
  }
  // A Ajuda já cobria a tela inicial desde sempre — o que faltava era no tour.
  ok(`[${modo}] ajudaSecoes continua com a seção da tela inicial (Acompanhar)`,
     secoes.some(([titulo]) => /Acompanhar/.test(titulo)));
}

// ---------------------------------------------- 4. o espelho em docs/AJUDA.md
ok("docs/AJUDA.md tem a seção da aba Opções (o arquivo declara espelhar ajudaSecoes)",
   /^## Opções$/m.test(ajudaMd));
ok("a seção de docs/AJUDA.md também diz que nenhuma ordem sai da aba",
   /## Opções[\s\S]*?Nenhuma ordem sai desta aba/.test(ajudaMd));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
