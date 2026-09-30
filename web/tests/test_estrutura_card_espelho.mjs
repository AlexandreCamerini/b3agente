// GUARDIÃO DE PARIDADE — vocabulário do card de posição estruturada (Fase 45).
// Guardião não se apaga: reversão deliberada atualiza este arquivo com nota.
//
// `skill_ref.ESTRUTURA_CARD` é a fonte única das frases de voz do card;
// `COPY[modo].estruturaCard` (web/src/copy.js) é o espelho byte a byte. Lê o .py
// como TEXTO (nunca importa Python). Também trava: igualdade Estudo=Operador das
// chaves neutras, âncoras proibidas ("trava protetora"/"abate o custo") e que o
// App.jsx não hardcoda frase de voz. Idioma de test_estrutura_espelho.mjs.
//
// Roda isolado: `node web/tests/test_estrutura_card_espelho.mjs`.
// Override do fonte Python por B3_SKILL_REF_PATH (só para sabotagem controlada).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY, estruturaCardTxt } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};

const caminhoSkillRef = process.env.B3_SKILL_REF_PATH
  ? process.env.B3_SKILL_REF_PATH
  : fileURLToPath(new URL("../../server/app/skill_ref.py", import.meta.url));

let src = "";
try {
  src = readFileSync(caminhoSkillRef, "utf8");
} catch (e) {
  ok(`skill_ref.py legível em ${caminhoSkillRef}`, false, e.message);
}
ok("skill_ref.py não vazio", src.length > 0);

function blocoDoDict(s, nome) {
  const m = s.match(new RegExp("^" + nome + " = \\{([\\s\\S]*?)^\\}", "m"));
  return m ? m[1] : null;
}
function blocoDoModo(bloco, modo) {
  const m = bloco.match(new RegExp('"' + modo + '":\\s*\\{([\\s\\S]*?)\\n\\s*\\},'));
  return m ? m[1] : null;
}
function paresDoModo(modoSrc) {
  const pares = {};
  const re = /"([a-zA-Z_]+)":\s*"([^"]*)"/g;
  let m;
  while ((m = re.exec(modoSrc))) pares[m[1]] = m[2];
  return pares;
}

const MODO_JS = { educacional: "estudo", operador: "operador" };
const CHAVES_CARD = [
  "chip_estrutura", "chip_estrutura_generica", "lendo", "indisponivel",
  "badge_travada_collar", "aviso_sem_stop",
];
const ANCORAS = /trava(\(s\))?\s+protetora|abate\s+o\s+custo/i;

// --- (1) ESTRUTURA_CARD <-> COPY[modo].estruturaCard
const blocoCard = src ? blocoDoDict(src, "ESTRUTURA_CARD") : null;
ok('skill_ref.py: bloco "ESTRUTURA_CARD = {...}" encontrado', !!blocoCard);
const frasesJs = [];
for (const modoPy of ["operador", "educacional"]) {
  const modoJs = MODO_JS[modoPy];
  const pares = paresDoModo((blocoCard && blocoDoModo(blocoCard, modoPy)) || "");
  const objJs = (COPY[modoJs] && COPY[modoJs].estruturaCard) || {};
  const kPy = Object.keys(pares).sort().join(",");
  const kJs = Object.keys(objJs).sort().join(",");
  const kFix = CHAVES_CARD.slice().sort().join(",");
  ok(`ESTRUTURA_CARD["${modoPy}"]: exatamente as ${CHAVES_CARD.length} chaves do contrato`, kPy === kFix, `real={${kPy}}`);
  ok(`COPY.${modoJs}.estruturaCard: mesmo conjunto de chaves`, kJs === kPy, `python={${kPy}} js={${kJs}}`);
  for (const [chave, valor] of Object.entries(pares)) {
    ok(`ESTRUTURA_CARD["${modoPy}"].${chave} idêntico byte a byte`, objJs[chave] === valor,
       `python="${valor}" js="${objJs[chave]}"`);
  }
  for (const v of Object.values(objJs)) frasesJs.push(v);
  ok(`COPY.${modoJs}.estruturaCard sem âncoras proibidas`, !ANCORAS.test(Object.values(objJs).join("\n")));
}
ok("estudo.estruturaCard sem verbo de ordem (comprar/vender)",
   !/\bcomprar\b|\bvender\b/i.test(Object.values(COPY.estudo.estruturaCard).join("\n")));

// --- (2) estruturaCardTxt
ok('estruturaCardTxt("operador","chip_estrutura",{nome:"COLLAR"}) == "ESTRUTURA · COLLAR"',
   estruturaCardTxt("operador", "chip_estrutura", { nome: "COLLAR" }) === "ESTRUTURA · COLLAR");
ok("estruturaCardTxt modo desconhecido cai no estudo",
   estruturaCardTxt("xyz", "chip_estrutura", { nome: "X" }) === "ESTUDO · X");
ok("estruturaCardTxt chave desconhecida -> null", estruturaCardTxt("operador", "nao_existe") === null);
ok("estruturaCardTxt sem vals não interpola",
   estruturaCardTxt("operador", "chip_estrutura") === "ESTRUTURA · {nome}");

// --- (3) chaves neutras idênticas nos dois modos
const E = COPY.estudo, O = COPY.operador;
const NEUTRAS_VALOR = [
  "estruturaResultadoRotulo", "estruturaResultadoSoAcoesRotulo", "estruturaAcoesRotulo",
  "estruturaOpcoesRotulo", "estruturaFaixaTitulo", "estruturaPernasTitulo", "semPiso", "semTeto",
  "ladoVendida", "ladoComprada", "semCotacaoPerna", "chipVenceHoje", "btnEncerrarEstrutura",
  "btnAtualizarEstrutura", "fonteEstruturaSemDado", "estruturaGrupoAria", "estruturaSaidaSemLastro",
  "estruturaVerHistorico",
];
for (const k of NEUTRAS_VALOR) {
  ok(`neutra ${k} existe e é idêntica nos dois modos`,
     typeof E[k] === "string" && E[k].length > 0 && E[k] === O[k], `estudo=${E[k]} operador=${O[k]}`);
}
ok("neutra estruturaLegenda idêntica nos dois modos",
   JSON.stringify(E.estruturaLegenda) === JSON.stringify(O.estruturaLegenda) &&
   Object.keys(E.estruturaLegenda || {}).join(",") === "piso,pm,hoje,teto,stop,alvo");
const NEUTRAS_FN = {
  chipVence: ["25/10", 26], chipVencida: ["25/10"], fonteEstruturaLinha: ["brapi", "14:32"],
  estruturaFaixaAria: ["COLLAR", "Piso R$ 30.", "35,00", "32,00"], encerrarAria: ["PETR4"],
  estruturaPernaLinha: ["CALL", "vendida", "38,50", "25/10"], estruturaPremioLinha: ["1,20", "0,80"],
  estruturaQtdPerna: [10], estruturaLivresLinha: [100, 200],
};
for (const [k, args] of Object.entries(NEUTRAS_FN)) {
  ok(`neutra ${k}() existe e é idêntica nos dois modos`,
     typeof E[k] === "function" && typeof O[k] === "function" && E[k](...args) === O[k](...args) && E[k](...args).length > 0);
}

// --- (4) âncoras nas 5 chaves de collar + "collar" onde manda
const collarE = [E.eyebrowPropostaCollar, E.collarPernasLinha(2, "PETR4", "38,50", "35,00"),
  E.ctaCollarDebito(2, "PETR4", "38,50", "35,00", "120,00"), E.ctaCollarCredito(2, "PETR4", "38,50", "35,00", "120,00"),
  E.confirmAbrirCollar(2, "PETR4", 200)];
const collarO = [O.eyebrowPropostaCollar, O.collarPernasLinha(2, "PETR4", "38,50", "35,00"),
  O.ctaCollarDebito(2, "PETR4", "38,50", "35,00", "120,00"), O.ctaCollarCredito(2, "PETR4", "38,50", "35,00", "120,00"),
  O.confirmAbrirCollar(2, "PETR4", 200)];
ok("chaves de collar do Estudo sem âncoras", !ANCORAS.test(collarE.join(" | ")));
ok("chaves de collar do Operador sem âncoras", !ANCORAS.test(collarO.join(" | ")));
ok("eyebrows dizem COLLAR", /COLLAR/.test(E.eyebrowPropostaCollar) && /COLLAR/.test(O.eyebrowPropostaCollar));
ok("collarPernasLinha diz COLLAR nos dois modos", /COLLAR/.test(collarE[1]) && /COLLAR/.test(collarO[1]));
ok("Operador CTA/confirm dizem collar", /collar/.test(collarO[2]) && /collar/.test(collarO[3]) && /collar/.test(collarO[4]));

// --- (5) App.jsx não hardcoda frases de voz > 20 chars
for (const f of new Set(frasesJs)) {
  if (f.length <= 20) continue;
  ok(`App.jsx não hardcoda "${f.slice(0, 40)}…"`, !app.includes(f));
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
