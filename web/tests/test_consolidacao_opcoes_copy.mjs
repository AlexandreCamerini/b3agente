// Fase 32 (32-01) — 2026-09-15. Guardião do vocabulário novo entregue antes
// de qualquer componente mudar de arquivo (D-01/D-03/D-05).
//
// Por que este arquivo existe, e não uma extensão de um guardião existente:
// `test_vocabulario_opcoes.mjs` só varre `OpcoesScreen.jsx` — as chaves
// `linhaChamadaOpcoes*` desta fase são consumidas em `App.jsx`
// (`CarteiraScreen`, linha de chamada de Posições), fora do escopo daquele
// arquivo. `test_curadoria_ui.mjs` cobre `curadoria*` mas não as chaves
// novas fora do prefixo `curadoria`/`tiraOpcoes`. Sem este guardião, as 9
// chaves novas ficariam sem NENHUMA cobertura de paridade Estudo/Operador.
//
// Padrão "static source inspection" da casa (mesmo de test_curadoria_ui.mjs,
// test_carteira_opcoes_tira.mjs): import direto de COPY, sem build e sem
// DOM. Roda isolado: `node web/tests/test_consolidacao_opcoes_copy.mjs`.
import { COPY } from "../src/copy.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const e = COPY.estudo;
const o = COPY.operador;

// As 9 chaves novas desta fase (32-01) — ver 32-01-PLAN.md Task 1.
const CHAVES_NOVAS = [
  "duasLeiturasIntro",
  "tiraOpcoesSubtitulo",
  "curadoriaErroBusca",
  "curadoriaErroBuscaCta",
  "linhaChamadaOpcoesTexto",
  "linhaChamadaOpcoesVazia",
  "linhaChamadaOpcoesCarregando",
  "linhaChamadaOpcoesErro",
  "linhaChamadaOpcoesAria",
];
// As chaves com CONTEÚDO reescrito nesta fase (chave já existia, valor novo).
const CONTEUDO_REESCRITO = ["tiraOpcoesTitulo", "curadoriaSubtitulo"];
const CHAVES_FUNCAO = ["linhaChamadaOpcoesTexto", "linhaChamadaOpcoesAria"];
const CHAVES_STRING = CHAVES_NOVAS.filter((k) => !CHAVES_FUNCAO.includes(k));

// ---- (1) as 9 chaves novas existem nos dois modos -------------------------
ok("as 9 chaves novas existem em COPY.estudo",
  CHAVES_NOVAS.every((k) => k in e));
ok("as 9 chaves novas existem em COPY.operador",
  CHAVES_NOVAS.every((k) => k in o));

// ---- (2) tipo por chave -----------------------------------------------------
ok("linhaChamadaOpcoesTexto é function nos dois modos",
  typeof e.linhaChamadaOpcoesTexto === "function" && typeof o.linhaChamadaOpcoesTexto === "function");
ok("linhaChamadaOpcoesAria é function nos dois modos",
  typeof e.linhaChamadaOpcoesAria === "function" && typeof o.linhaChamadaOpcoesAria === "function");
ok("as outras 7 chaves novas são string não-vazia nos dois modos",
  CHAVES_STRING.every((k) => typeof e[k] === "string" && e[k].trim().length > 0
    && typeof o[k] === "string" && o[k].trim().length > 0));

// ---- (3) paridade de CONJUNTO por prefixo linhaChamadaOpcoes ---------------
const chavesPorPrefixo = (copy, prefixo) => Object.keys(copy).filter((k) => k.startsWith(prefixo)).sort();
ok("o CONJUNTO de chaves linhaChamadaOpcoes* é idêntico nos dois modos",
  JSON.stringify(chavesPorPrefixo(e, "linhaChamadaOpcoes")) === JSON.stringify(chavesPorPrefixo(o, "linhaChamadaOpcoes")));

// ---- (4) singular/plural de linhaChamadaOpcoesTexto ------------------------
for (const [modo, bloco] of [["estudo", e], ["operador", o]]) {
  ok(`${modo}: linhaChamadaOpcoesTexto(1) contém "1 oportunidade" (singular)`,
    bloco.linhaChamadaOpcoesTexto(1).includes("1 oportunidade"));
  ok(`${modo}: linhaChamadaOpcoesTexto(3) contém "3 oportunidades" (plural)`,
    bloco.linhaChamadaOpcoesTexto(3).includes("3 oportunidades"));
}

// ---- (5) o estado "zero" tem frase própria, não linhaChamadaOpcoesTexto(0) -
for (const [modo, bloco] of [["estudo", e], ["operador", o]]) {
  ok(`${modo}: linhaChamadaOpcoesVazia existe e é diferente de linhaChamadaOpcoesTexto(0)`,
    typeof bloco.linhaChamadaOpcoesVazia === "string"
    && bloco.linhaChamadaOpcoesVazia !== bloco.linhaChamadaOpcoesTexto(0));
}

// ---- (6) erro de busca não reusa a frase de resultado zero -----------------
for (const [modo, bloco] of [["estudo", e], ["operador", o]]) {
  ok(`${modo}: linhaChamadaOpcoesErro é diferente de linhaChamadaOpcoesVazia`,
    bloco.linhaChamadaOpcoesErro !== bloco.linhaChamadaOpcoesVazia);
}

// ---- (7) curadoriaErroBusca é diferente de curadoriaVazio, mesma razão -----
for (const [modo, bloco] of [["estudo", e], ["operador", o]]) {
  ok(`${modo}: curadoriaErroBusca é diferente de curadoriaVazio`,
    bloco.curadoriaErroBusca !== bloco.curadoriaVazio);
}

// ---- (8) duasLeiturasIntro: idêntico nos dois modos, sem hierarquia -------
ok("duasLeiturasIntro é idêntico nos dois modos (decisão registrada, não acidente)",
  e.duasLeiturasIntro === o.duasLeiturasIntro);
ok("duasLeiturasIntro menciona as duas leituras sem hierarquia",
  e.duasLeiturasIntro.includes("nenhuma é mais certa que a outra"));

// ---- (9) as chaves de conteúdo reescrito diferem entre Estudo e Operador --
ok("tiraOpcoesTitulo difere entre Estudo e Operador (voz de professor x voz de mesa)",
  e.tiraOpcoesTitulo !== o.tiraOpcoesTitulo);
ok("tiraOpcoesSubtitulo difere entre Estudo e Operador",
  e.tiraOpcoesSubtitulo !== o.tiraOpcoesSubtitulo);
ok("curadoriaSubtitulo difere entre Estudo e Operador",
  e.curadoriaSubtitulo !== o.curadoriaSubtitulo);

// ---- (10) checklist regulatório: nenhuma palavra da lista PROIBIDAS -------
// Mesma lista PROIBIDAS de test_curadoria_ui.mjs.
const PROIBIDAS = ["garantido", "lucro garantido", "sem risco", "certeza"];
const CHAVES_CHECADAS = [...CHAVES_NOVAS, ...CONTEUDO_REESCRITO];
function textosDaChave(copy, k) {
  const v = copy[k];
  if (typeof v === "function") {
    // linhaChamadaOpcoesTexto(n) e linhaChamadaOpcoesAria(texto) — chama com
    // argumento representativo e varre o retorno também.
    if (k === "linhaChamadaOpcoesTexto") return [v(3)];
    if (k === "linhaChamadaOpcoesAria") return [v("x")];
    return [String(v)];
  }
  return [v || ""];
}
function copySemPromessa(copy) {
  return CHAVES_CHECADAS.every((k) =>
    textosDaChave(copy, k).every((texto) => {
      const low = texto.toLowerCase();
      return PROIBIDAS.every((p) => !low.includes(p));
    }));
}
ok("nenhuma das chaves novas/reescritas de COPY.estudo contém palavra da lista PROIBIDAS",
  copySemPromessa(e));
ok("nenhuma das chaves novas/reescritas de COPY.operador contém palavra da lista PROIBIDAS",
  copySemPromessa(o));

// ---- (11) sanidade da regex de PROIBIDAS -----------------------------------
ok("sanidade: uma string de controle contendo \"lucro garantido\" é detectada",
  PROIBIDAS.some((p) => "esta operação tem lucro garantido".toLowerCase().includes(p)));

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
