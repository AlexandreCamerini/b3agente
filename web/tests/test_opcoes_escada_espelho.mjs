// GUARDIÃO DE PARIDADE — vocabulário do caminho B (Fase 48, 2026-10-05).
// Guardião não se apaga: reversão deliberada atualiza este arquivo com nota.
//
// `skill_ref.OPCOES_ESCADA` é a fonte única das frases do caminho B da aba
// Opções (objetivo -> escada -> gráfico -> confirmar); `COPY[modo].opcoesEscada`
// (web/src/copy.js) é o espelho byte a byte. Lê o .py como TEXTO (nunca importa
// Python). Também trava: mesmo conjunto de chaves nos dois modos, vocabulário
// proibido (CVM), chaves de Ajuda/tour sem "Watchlist" e ausência de ordem parcial.
//
// Roda isolado: `node web/tests/test_opcoes_escada_espelho.mjs`.
// Prova negativa: B3_SKILL_REF_PATH=/nao/existe.py node web/tests/test_opcoes_escada_espelho.mjs
// deve sair com código 1 (override só para sabotagem controlada).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { COPY, opcoesEscadaTxt } from "../src/copy.js";

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
  const re = /"([a-zA-Z_0-9]+)":\s*"([^"]*)"/g;
  let m;
  while ((m = re.exec(modoSrc))) pares[m[1]] = m[2];
  return pares;
}

const MODO_JS = { educacional: "estudo", operador: "operador" };
const PROIBIDO = /garant|lucro certo|ganhe|proteção total|sem risco|100%/i;
const SITE = /Watchlist|Monitoramento|da sua lista/i;

const bloco = src ? blocoDoDict(src, "OPCOES_ESCADA") : null;
ok('skill_ref.py: bloco "OPCOES_ESCADA = {...}" encontrado', !!bloco);

const chavesPorModo = {};
for (const modoPy of ["educacional", "operador"]) {
  const modoJs = MODO_JS[modoPy];
  const pares = paresDoModo((bloco && blocoDoModo(bloco, modoPy)) || "");
  const objJs = (COPY[modoJs] && COPY[modoJs].opcoesEscada) || {};
  const kPy = Object.keys(pares).sort().join(",");
  const kJs = Object.keys(objJs).sort().join(",");
  chavesPorModo[modoPy] = kPy;
  ok(`OPCOES_ESCADA["${modoPy}"]: >= 90 chaves`, Object.keys(pares).length >= 90, `n=${Object.keys(pares).length}`);
  ok(`COPY.${modoJs}.opcoesEscada: mesmo conjunto de chaves`, kJs === kPy, `python={${kPy}} js={${kJs}}`);
  for (const [chave, valor] of Object.entries(pares)) {
    ok(`OPCOES_ESCADA["${modoPy}"].${chave} idêntico byte a byte`, objJs[chave] === valor,
       `python="${valor}" js="${objJs[chave]}"`);
  }
  const valores = Object.values(objJs);
  ok(`COPY.${modoJs}.opcoesEscada sem vocabulário proibido`, !PROIBIDO.test(valores.join("\n")));
  ok(`COPY.${modoJs}.opcoesEscada sem frase vazia`, valores.every((v) => typeof v === "string" && v.trim().length > 0));
  ok(`COPY.${modoJs}.opcoesEscada sem chave de ordem parcial (C-14)`, !Object.keys(objJs).some((k) => /parcial/i.test(k)));
  ok(`COPY.${modoJs}: frase de risco usa Pior caso / Melhor caso`,
     /^Pior caso/.test(objJs.risco_pior || "") && /^Melhor caso/.test(objJs.risco_melhor || ""));
  ok(`COPY.${modoJs}.opcoesTourPasso existe e sem Watchlist`,
     typeof COPY[modoJs].opcoesTourPasso === "string" && COPY[modoJs].opcoesTourPasso.length > 0 && !SITE.test(COPY[modoJs].opcoesTourPasso));
  ok(`COPY.${modoJs}.opcoesTourPasso preserva fim de pregão e sem ordem`,
     /fim de pregão/.test(COPY[modoJs].opcoesTourPasso) && /sem ordem nenhuma/.test(COPY[modoJs].opcoesTourPasso));
  ok(`COPY.${modoJs}.opcoesAjudaEstuda existe e sem Watchlist`,
     typeof COPY[modoJs].opcoesAjudaEstuda === "string" && COPY[modoJs].opcoesAjudaEstuda.length > 0 && !SITE.test(COPY[modoJs].opcoesAjudaEstuda));
}
ok("mesmo conjunto de chaves nos dois modos (python)", chavesPorModo.educacional === chavesPorModo.operador);

ok('opcoesEscadaTxt("estudo","acao_a",{preco:"38,00"}) interpola',
   opcoesEscadaTxt("estudo", "acao_a", { preco: "38,00" }) === "ação a R$ 38,00");
ok("opcoesEscadaTxt modo desconhecido cai no estudo",
   opcoesEscadaTxt("xyz", "degrau_renda_0") === COPY.estudo.opcoesEscada.degrau_renda_0);
ok("opcoesEscadaTxt chave desconhecida -> null", opcoesEscadaTxt("operador", "nao_existe") === null);
ok("opcoesEscadaTxt sem vals não interpola", opcoesEscadaTxt("operador", "acao_a") === "ação a R$ {preco}");

// Fase 48 gap G-01/G-02 (2026-10-05): vocabulário de vencimento fora da janela e pernas abertas.
const CHAVES_G = ["sem_vencimento_elegivel","sem_vencimento_elegivel_dica","objetivo_indisponivel_ver_motivo","pernas_titulo","pernas_linha","pernas_premio","pernas_resultado","perna_lado_compra","perna_lado_venda","pernas_carregando","pernas_encerrar","pernas_encerrar_aria","pernas_confirmar","pernas_confirmar_sim","pernas_cancelar","pernas_encerrando","pernas_na_estrutura","pernas_vendida_sem_acao"];
for (const m of ["estudo", "operador"]) {
  const o = COPY[m].opcoesEscada;
  ok(`COPY.${m}.opcoesEscada tem as ${CHAVES_G.length} chaves G-01/G-02`, CHAVES_G.every((k) => typeof o[k] === "string" && o[k].length > 0));
}
const fraseG = opcoesEscadaTxt("estudo", "sem_vencimento_elegivel", { ticker: "ITUB4", vencimentos: "09/10", min: 15, max: 60 }) || "";
ok("sem_vencimento_elegivel interpola ticker, datas e janela", ["ITUB4", "09/10", "15", "60"].every((x) => fraseG.includes(x)), fraseG);

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
