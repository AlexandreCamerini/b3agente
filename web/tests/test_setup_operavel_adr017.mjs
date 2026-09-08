// ADR-017 Decisão 1 — Guardião: `setupOperavel`/`metaDeEntrada` (finance.js)
// e os dois pontos de consumo em App.jsx (grade da watchlist, card do Radar).
//
// ACHADO REAL (ABEV3, 2026-09-07, staging): a compra gravou `setupEntrada`
// internamente contraditório — `setup`/`veredito` de BAIXA (PFR, vindo de
// `sc.melhorSetup`/`sc.veredito`, fonte JÁ filtrada pelo backend) misturados
// com `lado`/`gatilho`/`invalidacao` do Setup 9.2, APOSENTADO e de ALTA
// (vindos de `(sc.setups || [])[0]` cru). Com `se.lado` errado, a avaliação
// em App.jsx (`se.lado === "baixa" ? cur > se.invalidacao : cur <
// se.invalidacao`) INVERTIA a tese: o app mostrava a tese como válida quando
// estava invalidada, e vice-versa.
//
// REGRA (espelho de server/app/setups.py:725, `plano_do_resultado`):
// `operaveis = [s for s in setups_list if not s.get("aposentado")]` — setup
// aposentado nunca vira base de plano operacional, mas continua na lista de
// estudo do Radar (aposentado ≠ apagado).
//
// Roda sem build: `node web/tests/test_setup_operavel_adr017.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { setupOperavel, metaDeEntrada } from "../src/finance.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

// ---------------------------------------------------------------------------
// Parte (a) — unidade de setupOperavel/metaDeEntrada
// ---------------------------------------------------------------------------

// Fixture do achado real: Setup 9.2 (aposentado, alta) e Rompimento (baixa)
// (aposentado, baixa) na frente na lista; PFR (operável, baixa) por último —
// reproduz exatamente a ordem que produziu o meta contraditório em produção.
const setup92 = { nome: "Setup 9.2", lado: "alta", aposentado: true, gatilho: 30.10, invalidacao: 29.50, criterios: [] };
const rompimentoBaixa = { nome: "Rompimento (baixa)", lado: "baixa", aposentado: true, gatilho: 28.00, invalidacao: 28.60, criterios: [] };
const pfr = { nome: "PFR", lado: "baixa", aposentado: false, gatilho: 28.90, invalidacao: 29.40, criterios: [] };
const scAchado = {
  melhorSetup: "PFR",
  veredito: "Estudar baixa",
  confluencia: 70,
  snapshotId: "snap-abev3",
  setups: [setup92, rompimentoBaixa, pfr],
};

const metaAchado = metaDeEntrada(scAchado);
ok("meta do achado real: lado é da baixa (PFR), não do Setup 9.2 (alta)", metaAchado.lado === "baixa");
ok("meta do achado real: setup gravado é PFR", metaAchado.setup === "PFR");
ok("meta do achado real: gatilho/invalidação são os do MESMO elemento PFR (não coincidência de índice)",
  metaAchado.gatilho === pfr.gatilho && metaAchado.invalidacao === pfr.invalidacao);
ok("meta do achado real: nenhum valor do Setup 9.2 vazou",
  metaAchado.gatilho !== setup92.gatilho && metaAchado.invalidacao !== setup92.invalidacao);

// Fallback sem nome: primeiro !aposentado da lista.
const semNome = setupOperavel([setup92, rompimentoBaixa, pfr], null);
ok("fallback sem melhorSetupNome: devolve o primeiro operável (PFR), não setups[0]", semNome === pfr);

// Nome que não casa: cai no primeiro operável, não em setups[0].
const nomeErrado = setupOperavel([setup92, rompimentoBaixa, pfr], "Nome Que Não Existe");
ok("nome sem correspondência: cai no primeiro operável (PFR), não em setups[0] (Setup 9.2)", nomeErrado === pfr);

// Todos aposentados: setupOperavel === null e meta sem lado/gatilho/invalidacao.
const todosAposentados = [setup92, rompimentoBaixa];
ok("todos aposentados: setupOperavel devolve null (aposentado NUNCA é fallback silencioso)",
  setupOperavel(todosAposentados, "Setup 9.2") === null);
const metaVazia = metaDeEntrada({ melhorSetup: "Setup 9.2", veredito: "Estudar alta", confluencia: 40, snapshotId: "x", setups: todosAposentados });
ok("todos aposentados: meta sem chave lado/gatilho/invalidacao (ausente, não null, não 0)",
  !("lado" in metaVazia) && !("gatilho" in metaVazia) && !("invalidacao" in metaVazia));
ok("todos aposentados: meta preserva setup/veredito/confluencia (dados que o backend já filtrou)",
  metaVazia.setup === "Setup 9.2" && metaVazia.veredito === "Estudar alta" && metaVazia.confluencia === 40);

// Entradas degeneradas — nunca lança, sempre null.
let lancouUndefined = false, lancouVazio = false, lancouElementoNulo = false;
try { ok("setupOperavel(undefined, null) === null", setupOperavel(undefined, null) === null); } catch { lancouUndefined = true; }
try { ok("setupOperavel([], 'x') === null", setupOperavel([], "x") === null); } catch { lancouVazio = true; }
try { ok("setupOperavel([null, pfr], null) devolve pfr (guarda contra elemento nulo)", setupOperavel([null, pfr], null) === pfr); } catch { lancouElementoNulo = true; }
ok("nenhuma entrada degenerada lança exceção", !lancouUndefined && !lancouVazio && !lancouElementoNulo);
ok("metaDeEntrada(undefined) não lança e não inventa lado/gatilho/invalidacao", (() => {
  try {
    const m = metaDeEntrada(undefined);
    return !("lado" in m) && !("gatilho" in m) && !("invalidacao" in m);
  } catch { return false; }
})());

// Anti-regressão do bug de inversão: replica a expressão de App.jsx
// (`se.lado === "baixa" ? cur > se.invalidacao : cur < se.invalidacao`) sobre
// o meta produzido. Preço abaixo da invalidação do PFR (setup de BAIXA) deve
// resultar em tese VÁLIDA — era o resultado invertido antes da correção
// (quando `se.lado` vinha do Setup 9.2, de ALTA).
const se = metaAchado;
const curAbaixoDaInvalidacao = pfr.invalidacao - 0.10;
// `inval` reproduz literalmente App.jsx:4423 — true = "invalidado".
const inval = se.lado === "baixa" ? curAbaixoDaInvalidacao > se.invalidacao : curAbaixoDaInvalidacao < se.invalidacao;
const teseValida = !inval;
ok("anti-regressão: preço abaixo da invalidação do PFR (baixa) resulta em tese VÁLIDA (era invertido com Setup 9.2)",
  teseValida === true);

// Com `se.lado` errado (Setup 9.2, de ALTA) sobre o MESMO preço/invalidação,
// o resultado se invertia — é exatamente o bug do achado real.
const seErrado = { lado: setup92.lado, invalidacao: pfr.invalidacao };
const invalErrado = seErrado.lado === "baixa" ? curAbaixoDaInvalidacao > seErrado.invalidacao : curAbaixoDaInvalidacao < seErrado.invalidacao;
ok("prova do bug: com lado do Setup 9.2 (alta) sobre a mesma invalidação, o resultado inverte (era o defeito relatado)",
  invalErrado !== inval);

// ---------------------------------------------------------------------------
// Parte (b) — grep estático de App.jsx (fonte lida com readFileSync)
// ---------------------------------------------------------------------------

// Higiene de grep: filtrar linhas de comentário antes de contar, para que o
// próprio comentário explicativo da correção não valide/invalide a asserção.
const linhasSemComentario = app.split("\n").filter((l) => !l.trim().startsWith("//")).join("\n");

ok("App.jsx NÃO contém mais (sc.setups || [])[0]", !linhasSemComentario.includes("(sc.setups || [])[0]"));
ok("App.jsx NÃO contém mais (r.setups || [])[0]", !linhasSemComentario.includes("(r.setups || [])[0]"));
ok("App.jsx contém metaDeEntrada(sc)", linhasSemComentario.includes("metaDeEntrada(sc)"));
ok("App.jsx contém setupOperavel(r.setups, r.melhorSetup)", linhasSemComentario.includes("setupOperavel(r.setups, r.melhorSetup)"));

const linhaImport = app.split("\n").find((l) => l.includes("from \"./finance.js\""));
ok("setupOperavel e metaDeEntrada são importados de ./finance.js",
  !!linhaImport && linhaImport.includes("setupOperavel") && linhaImport.includes("metaDeEntrada"));

// Guardião de que a correção NÃO virou filtro global — a lista de estudo do
// Radar segue recebendo o array CRU, aposentados incluídos (ADR-017: aposentado
// ≠ apagado).
ok("lista de estudo do Radar segue crua: (r.setups || []).map( ainda existe",
  linhasSemComentario.includes("(r.setups || []).map("));

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
