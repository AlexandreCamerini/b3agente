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
// Nota 2026-10-12 (quick 261012-09v): GUIA ÚNICO. tourPassos/ajudaSecoes e a tela "Como
// funciona" saíram; o treinamento é o Guia (site/js/telas-data.js, via parseTelasData). Este
// arquivo deixou de extrair/avaliar funções de App.jsx e passou a travar o MESMO contrato no
// guia, sem tela sumir da explicação:
//  · o 1º uso (ABERTURA_PRIMEIRO_USO) abre em Boas-vindas e a tela seguinte é Acompanhar;
//  · Boas-vindas não manda procurar o Radar;
//  · o grupo Opções existe e diz que nenhuma ordem sai dali, que a leitura é de fim de
//    pregão, fala da carteira (não de Watchlist/Monitoramento) e do travessão (nunca zero);
//  · docs/AJUDA.md aponta o Guia (nota datada) e mantém a seção histórica de Opções.
//
// Roda sem build e sem servidor: `node web/tests/test_tour_opcoes.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { parseTelasData } from "../src/guiaDados.js";
import { ABERTURA_PRIMEIRO_USO } from "../src/guiaNav.js";

const here = dirname(fileURLToPath(import.meta.url));
const guia = parseTelasData(readFileSync(join(here, "..", "..", "site", "js", "telas-data.js"), "utf8"));
const ajudaMd = readFileSync(join(here, "..", "..", "docs", "AJUDA.md"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};
const textos = (t) => [t.visao, t.missao, ...t.pontos.map((p) => p.titulo + " " + p.texto)].join(" ");
const porId = (id) => guia.find((t) => t.id === id);

// (a) o 1º uso começa onde o app abre
ok("ABERTURA_PRIMEIRO_USO é a tela 0 do guia", guia[0] && guia[0].id === ABERTURA_PRIMEIRO_USO.id);
ok("a tela 1 do guia é Acompanhar (a tela em que o app abre)", guia[1] && guia[1].id === "acomp" && /Acompanhar/.test(guia[1].titulo));
// (b) o começo não manda procurar outra tela (achado A4, Fase 26)
ok("Boas-vindas não cita o Radar", !/Radar/.test(textos(guia[0])), "apontar outra tela no começo é o defeito do achado A4");
// (f) a tela inicial está coberta
ok("existe a tela Acompanhar (acomp)", !!porId("acomp"));

// (c)(d)(e) Opções
const opcoes = guia.filter((t) => t.grupo === "Opções");
ok("existe a tela opc e o grupo Opções", !!porId("opc") && opcoes.length >= 1);
const txtOpc = opcoes.map(textos).join(" ");
ok("o grupo Opções diz que nenhuma ordem sai dali", /nenhuma ordem/i.test(txtOpc), "a frase impede a leitura errada (princípios 1/2 do CLAUDE.md)");
ok("o grupo Opções avisa que a leitura é de fim de pregão", /fim de pregão/i.test(txtOpc), "princípio 3 do CLAUDE.md");
ok("Fase 48 (2026-10-05): o grupo Opções não cita Watchlist/Monitoramento/lista", !/Watchlist|Monitoramento|da sua lista/i.test(txtOpc));
ok("Fase 48 (2026-10-05): o grupo Opções fala da carteira", /carteira/i.test(txtOpc));
ok("o ponto de Opções diz travessão (nunca como zero)", /travessão[^.]*nunca como zero/.test(textos(porId("opc"))));

// (g) docs/AJUDA.md: nota apontando o guia + seção histórica de Opções preservada
ok("docs/AJUDA.md tem a nota 261012-09v apontando o Guia de treinamento", /261012-09v/.test(ajudaMd) && /Guia de treinamento/.test(ajudaMd));
ok("docs/AJUDA.md mantém a seção histórica de Opções (histórico não se reescreve)", /^## Opções$/m.test(ajudaMd) && /## Opções[\s\S]*?Nenhuma ordem sai desta aba/.test(ajudaMd));
ok("docs/AJUDA.md: Fase 48 (2026-10-05) a seção Opções não cita Watchlist e fala da Carteira",
   (() => { const m = /## Opções([\s\S]*?)\n## /.exec(ajudaMd); return !!m && !/Watchlist/.test(m[1]) && /Carteira/.test(m[1]); })());

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
