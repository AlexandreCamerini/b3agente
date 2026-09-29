// GUARDIÃO DE PARIDADE — vocabulário da estrutura por ativo (Fase 44, D-06/ESTR-06).
//
// `skill_ref.ESTRUTURA_POSICAO` (e os motivos de `skill_ref.OPCOES_LASTREADAS`)
// são a fonte única das frases da leitura de estrutura; `web/src/copy.js`
// (`COPY[modo].estruturaPosicao` / `.opcoesLastreadasMotivo`) é o espelho.
// Este teste lê o .py como TEXTO (nunca importa Python) e compara byte a byte.
// Mesmo idioma de test_vocabulario_espelho.mjs.
//
// Roda isolado, sem build e sem servidor: `node web/tests/test_estrutura_espelho.mjs`.
// Override do fonte Python por B3_SKILL_REF_PATH (só para sabotagem controlada).
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

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
const CHAVES_ESTRUTURA = [
  "nome_call_coberta", "nome_put_protecao", "nome_collar", "nome_fora_da_biblioteca",
  "estado_vigente", "estado_vigente_sem_data", "estado_perto_vencimento",
  "estado_exercicio_provavel", "estado_premio_indisponivel", "estado_vencida",
  "aberta_sem_proposta", "faixa_piso", "faixa_teto", "faixa_sem_piso", "faixa_sem_teto",
  "faixa_vencimentos_diferentes", "faixa_perna_sem_lastro", "faixa_sem_acoes",
  "faixa_dados_insuficientes", "descoberta_put", "stop_protegida", "resultado_incompleto",
  "acao_sem_cotacao", "encerrar_premio_indisponivel", "encerrar_vencida", "origem_last",
];
const CHAVES_MOTIVO = [
  "sem_lastro", "sem_setup", "degradado", "caixa_insuficiente", "sem_contrato_liquido",
  "sem_vencimento_elegivel", "premio_indisponivel", "contrato_fora_da_cadeia", "sem_mercado",
];

if (src) {
  const blocoEstr = blocoDoDict(src, "ESTRUTURA_POSICAO");
  const blocoOpc = blocoDoDict(src, "OPCOES_LASTREADAS");
  ok('skill_ref.py: bloco "ESTRUTURA_POSICAO = {...}" encontrado', !!blocoEstr);
  ok('skill_ref.py: bloco "OPCOES_LASTREADAS = {...}" encontrado', !!blocoOpc);

  const frasesEstruturaJs = [];
  const opcPorModo = {};
  for (const modoPy of ["operador", "educacional"]) {
    const modoJs = MODO_JS[modoPy];

    // --- ESTRUTURA_POSICAO ↔ COPY[modo].estruturaPosicao
    const pares = paresDoModo((blocoEstr && blocoDoModo(blocoEstr, modoPy)) || "");
    const objJs = (COPY[modoJs] && COPY[modoJs].estruturaPosicao) || {};
    ok(`ESTRUTURA_POSICAO["${modoPy}"] parseado com >0 chaves`, Object.keys(pares).length > 0);
    const kPy = Object.keys(pares).sort().join(",");
    const kJs = Object.keys(objJs).sort().join(",");
    ok(`ESTRUTURA_POSICAO["${modoPy}"] ↔ COPY.${modoJs}.estruturaPosicao: mesmo conjunto de chaves`,
       kPy === kJs, `python={${kPy}} js={${kJs}}`);
    ok(`ESTRUTURA_POSICAO["${modoPy}"]: exatamente as ${CHAVES_ESTRUTURA.length} chaves do contrato`,
       kPy === CHAVES_ESTRUTURA.slice().sort().join(","), `real={${kPy}}`);
    for (const [chave, valor] of Object.entries(pares)) {
      ok(`ESTRUTURA_POSICAO["${modoPy}"].${chave} idêntico byte a byte`,
         objJs[chave] === valor, `python="${valor}" js="${objJs[chave]}"`);
    }
    for (const v of Object.values(objJs)) frasesEstruturaJs.push(v);

    // --- motivos de OPCOES_LASTREADAS ↔ COPY[modo].opcoesLastreadasMotivo
    const paresOpc = paresDoModo((blocoOpc && blocoDoModo(blocoOpc, modoPy)) || "");
    opcPorModo[modoPy] = paresOpc;
    const motJs = (COPY[modoJs] && COPY[modoJs].opcoesLastreadasMotivo) || {};
    ok(`OPCOES_LASTREADAS["${modoPy}"] parseado com >0 chaves`, Object.keys(paresOpc).length > 0);
    ok(`COPY.${modoJs}.opcoesLastreadasMotivo: conjunto exato das ${CHAVES_MOTIVO.length} chaves`,
       Object.keys(motJs).sort().join(",") === CHAVES_MOTIVO.slice().sort().join(","),
       `js={${Object.keys(motJs).sort().join(",")}}`);
    for (const chave of CHAVES_MOTIVO) {
      ok(`OPCOES_LASTREADAS["${modoPy}"].${chave} existe no python`, typeof paresOpc[chave] === "string");
      ok(`OPCOES_LASTREADAS["${modoPy}"].${chave} idêntico byte a byte`,
         motJs[chave] === paresOpc[chave], `python="${paresOpc[chave]}" js="${motJs[chave]}"`);
    }

    // (5) D-06: motivos próprios, distintos de sem_setup — nos dois arquivos.
    for (const chave of ["sem_contrato_liquido", "sem_vencimento_elegivel"]) {
      ok(`python ${modoPy}.${chave} ≠ sem_setup`, paresOpc[chave] && paresOpc[chave] !== paresOpc.sem_setup);
      ok(`js ${modoJs}.${chave} ≠ sem_setup`, motJs[chave] && motJs[chave] !== motJs.sem_setup);
    }

    // (6) âncoras proibidas
    const todas = Object.values(objJs).concat(Object.values(motJs)).join("\n");
    ok(`COPY.${modoJs}: sem "trava protetora" / "abate o custo" nas frases novas`,
       !/trava protetora|abate o custo/i.test(todas));
  }

  // (7) Estudo sem verbo de ordem
  ok("estudo.estruturaPosicao sem verbo de ordem (comprar/vender)",
     !/\bcomprar\b|\bvender\b/i.test(Object.values(COPY.estudo.estruturaPosicao).join("\n")));

  // (8) App.jsx não hardcoda frase de estrutura
  for (const f of new Set(frasesEstruturaJs)) {
    if (f.length <= 20) continue;
    ok(`App.jsx não hardcoda "${f.slice(0, 40)}…"`, !app.includes(f));
  }
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
