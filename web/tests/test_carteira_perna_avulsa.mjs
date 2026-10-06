// quick 261006-axi (2026-10-06) — guardião do card de PERNA AVULSA na Carteira.
//
// Defeito: opção comprada cujo ativo-objeto não está em `positions` (PUT
// VALEV731W2 sem VALE3) sumia da Carteira. Agora CarteiraScreen renderiza um
// `CartaoPernaAvulsa` por ticker só com perna, sem fabricar número de ação.
// Guardião de fonte (App.jsx lido sem comentários) + espelho do texto novo.
// Roda sem build: `node web/tests/test_carteira_perna_avulsa.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY, cartaoPosicaoTxt } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const semComentario = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").split("\n").map((l) => l.replace(/(^|\s)\/\/.*$/, "$1")).join("\n");
const app = semComentario(readFileSync(join(here, "..", "src", "App.jsx"), "utf8"));

ok("import de tickersSoComPernas em App.jsx",
  /import\s*\{[^}]*\btickersSoComPernas\b[^}]*\}\s*from\s*["']\.\/estruturaCard\.js["']/.test(app));
ok("CarteiraScreen calcula avulsas = tickersSoComPernas(data.positions, data.optionPositions)",
  /const avulsas = tickersSoComPernas\(data\.positions, data\.optionPositions\);/.test(app));
ok("'Portfólio vazio' só com positions vazio E sem avulsas",
  /data\.positions\.length === 0 && avulsas\.length === 0 && \(/.test(app));
const iMapPos = app.indexOf("data.positions.map((p) =>");
const iAv = app.indexOf("avulsas.map((t) =>");
ok("avulsas.map vem DEPOIS do map de data.positions", iMapPos > 0 && iAv > iMapPos);
ok("<CartaoPernaAvulsa renderizado dentro de avulsas.map", iAv > 0 && app.slice(iAv, iAv + 900).includes("<CartaoPernaAvulsa"));

const iFn = app.indexOf("function CartaoPernaAvulsa(");
const iFim = app.indexOf("\nfunction CartaoPosicao(", iFn);
const corpo = iFn >= 0 && iFim > iFn ? app.slice(iFn, iFim) : "";
ok("corpo de CartaoPernaAvulsa localizado", corpo.length > 200);
ok("CartaoPernaAvulsa NÃO renderiza FaceAcao/ReguaPlano/EditorStopAlvo/BlocoBorisIA/pctDoCapital",
  corpo.length > 0 && !/FaceAcao|ReguaPlano|EditorStopAlvo|BlocoBorisIA|pctDoCapital/.test(corpo));
ok("CartaoPernaAvulsa usa estadoLeitura(true, leitura) e CardPosicaoEstruturada",
  /estadoLeitura\(true, leitura\)/.test(corpo) && /<CardPosicaoEstruturada/.test(corpo));
ok("p sintético: semAcoes: true, avg/stop/alvo null (nunca 0)",
  /semAcoes: true/.test(corpo) && /avg: null/.test(corpo) && /stop: null/.test(corpo) && /alvo: null/.test(corpo));
ok("carregando/falha usam estruturaCardTxt lendo/indisponivel e BotaoAtualizarEstrutura na falha",
  /estruturaCardTxt\(modo, modoLeitura === "carregando" \? "lendo" : "indisponivel"\)/.test(corpo) && /<BotaoAtualizarEstrutura/.test(corpo));

// sanidade: as regexes pegam o padrão quando ele existe (e não passam no vazio)
ok("sanidade: regex do vazio pega o padrão positivo e rejeita o antigo",
  /data\.positions\.length === 0 && avulsas\.length === 0 && \(/.test("{data.positions.length === 0 && avulsas.length === 0 && (")
  && !/data\.positions\.length === 0 && avulsas\.length === 0 && \(/.test("{data.positions.length === 0 && ("));
ok("sanidade: proibidos pegam FaceAcao quando presente", /FaceAcao|ReguaPlano/.test("<FaceAcao p={p} />"));

// espelho do texto novo skill_ref.py <-> copy.js, nos dois modos
const py = readFileSync(join(here, "..", "..", "server", "app", "skill_ref.py"), "utf8");
const literais = [...py.matchAll(/"avulsa_sem_acoes":\s*"([^"]*)"/g)].map((m) => m[1]);
ok("skill_ref.py declara avulsa_sem_acoes nas duas vozes", literais.length === 2);
for (const modo of ["estudo", "operador"]) {
  const t = cartaoPosicaoTxt(modo, "avulsa_sem_acoes");
  ok(`copy.js (${modo}) igual byte a byte ao skill_ref.py`, typeof t === "string" && literais.includes(t) && t === "Sem ações deste ativo: só a opção está aberta.");
  ok(`COPY.${modo}.cartaoPosicao.avulsa_sem_acoes existe`, COPY[modo].cartaoPosicao.avulsa_sem_acoes === t);
  ok(`texto (${modo}) sem número e sem promessa`, !/\d|garant|lucro certo/i.test(t));
}

if (fails) { console.log(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntudo ok");
