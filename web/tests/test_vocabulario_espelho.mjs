// ESPELHO DO VOCABULÁRIO DE ESTADO — o guardião que faltava.
//
// O rótulo de cada estado do timing vive em três lugares:
//   • `skill_ref.TIMING`      — a frase por modo (backend, canônica)
//   • `conceitos.ROTULOS`     — o rótulo citado DENTRO da explicação (backend)
//   • `TIMING_STYLE`          — o rótulo desenhado no badge (App.jsx)
//
// O comentário de `conceitos.ROTULOS` DECLARA que ele espelha `TIMING_STYLE`,
// e até agora ninguém verificava. Divergir aqui produz o pior tipo de erro
// deste produto: a explicação diz «o card troca de "CONDIÇÃO ARMADA" para
// "CONDIÇÃO ATINGIDA"» e o card mostra outra coisa — para a pessoa que
// justamente não sabe se são a mesma coisa.
//
// Com a Fase 0b o push virou o quarto lugar; ele compõe por
// `skill_ref.timing_txt` e nunca escreve redação nova (travado no pytest).
//
// ADR-017 Bloco 3 (Fase 8, Plano 08-01) acrescentou um SEGUNDO espelho: o
// vocabulário do histórico medido por setup (`skill_ref.HISTORICO` /
// `HISTORICO_ROTULO` / `ENTRADA_AUTO`) e seu par em `copy.js` (`COPY[modo].
// historico` / `.historicoRotulo` / `.entradaAuto`). Mesma disciplina: leitura
// de fonte (nunca import de Python), comparação byte a byte, e checagem de
// que `App.jsx` não reintroduz o texto hardcodado.
//
// Roda sem build e sem servidor: `node web/tests/test_vocabulario_espelho.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { COPY } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const conceitos = readFileSync(join(here, "..", "..", "server", "app", "conceitos.py"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};

// TIMING_STYLE: gatilho/armado => [cor, bg, "RÓTULO OPERADOR", "RÓTULO ESTUDO"]
function rotulosDoBadge(estado) {
  const m = app.match(new RegExp(estado + ": \\[[^\\]]*?\"([^\"]+)\", \"([^\"]+)\"\\]"));
  return m ? { operador: m[1], estudo: m[2] } : null;
}
// ROTULOS do backend: {"rotuloArmado": "...", "rotuloAtingido": "..."}
function rotuloDoConceito(modo, chave) {
  const bloco = conceitos.match(new RegExp('"' + modo + '": \\{([\\s\\S]*?)\\},'));
  if (!bloco) return null;
  const m = bloco[1].match(new RegExp('"' + chave + '": "([^"]+)"'));
  return m ? m[1] : null;
}

const armado = rotulosDoBadge("armado");
const gatilho = rotulosDoBadge("gatilho");
ok("TIMING_STYLE tem os rótulos de armado e gatilho", !!armado && !!gatilho);

if (armado && gatilho) {
  // O badge prefixa com um símbolo ("◔ ", "● "); o conceito cita só o texto.
  const limpo = (s) => s.replace(/^[^A-ZÀ-Ú]+/, "").trim();
  const pares = [
    ["educacional", "rotuloArmado", limpo(armado.estudo)],
    ["educacional", "rotuloAtingido", limpo(gatilho.estudo)],
    ["operador", "rotuloArmado", limpo(armado.operador)],
    ["operador", "rotuloAtingido", limpo(gatilho.operador)],
  ];
  for (const [modo, chave, esperado] of pares) {
    const real = rotuloDoConceito(modo, chave);
    ok(`conceitos.ROTULOS[${modo}].${chave} espelha o badge ("${esperado}")`,
       real === esperado, `backend diz "${real}", o badge mostra "${esperado}"`);
  }
}

// A lei de vocabulário por modo: o Estudo descreve CONDIÇÃO, o Operador dá o
// nome de mesa. Trocar isso é o erro que o guardrail de verbo de ordem não
// pegaria (nenhuma das duas tem imperativo).
ok("Estudo fala de CONDIÇÃO, Operador fala de GATILHO/PLANO",
   /CONDIÇÃO ARMADA/.test(app) && /CONDIÇÃO ATINGIDA/.test(app)
   && /PLANO ARMADO/.test(app) && /GATILHO ATINGIDO/.test(app));

// ---------------------------------------------------------------------------
// ADR-017 Bloco 3 — histórico medido por setup (Fase 8, Plano 08-01)
//
// Fonte Python lida como TEXTO (caminho resolvido por new URL, nunca relativo
// ao cwd — scripts/executar.sh roda com cwd=web); aceita override por
// B3_SKILL_REF_PATH, no mesmo idioma de test_rr_min_fonte_unica.mjs — usado
// SÓ pela sabotagem controlada em sandbox, nunca contra o arquivo real do
// servidor.
const caminhoSkillRef = process.env.B3_SKILL_REF_PATH
  ? process.env.B3_SKILL_REF_PATH
  : fileURLToPath(new URL("../../server/app/skill_ref.py", import.meta.url));

let skillRefSrc = "";
try {
  skillRefSrc = readFileSync(caminhoSkillRef, "utf8");
} catch (e) {
  ok(`skill_ref.py legível em ${caminhoSkillRef}`, false, e.message);
}

// Recorta o bloco `NOME = { ... }` do fonte Python — âncora ancorada em
// início de linha, senão "HISTORICO" casaria dentro de "HISTORICO_ROTULO".
function blocoDoDict(src, nome) {
  const m = src.match(new RegExp("^" + nome + " = \\{([\\s\\S]*?)^\\}", "m"));
  return m ? m[1] : null;
}
// Recorta o sub-bloco de um modo ("operador": { ... },) dentro do bloco do dict.
function blocoDoModo(blocoSrc, modo) {
  const m = blocoSrc.match(new RegExp('"' + modo + '":\\s*\\{([\\s\\S]*?)\\n\\s*\\},'));
  return m ? m[1] : null;
}
// Extrai pares "chave": "valor" (sem aspas escapadas internas — as frases
// aprovadas não têm aspas internas).
function paresDoModo(modoSrc) {
  const pares = {};
  const re = /"([a-zA-Z_]+)":\s*"([^"]*)"/g;
  let m;
  while ((m = re.exec(modoSrc))) pares[m[1]] = m[2];
  return pares;
}

const DICTS = ["HISTORICO", "HISTORICO_ROTULO", "ENTRADA_AUTO"];
// Python "educacional" ↔ JS "estudo"; "operador" ↔ "operador".
const MODO_JS = { educacional: "estudo", operador: "operador" };
const CHAVE_JS = { HISTORICO: "historico", HISTORICO_ROTULO: "historicoRotulo", ENTRADA_AUTO: "entradaAuto" };
const CHAVES_ESPERADAS = {
  HISTORICO: ["elegivel", "inelegivel", "insuficiente", "nunca_medido", "aposentado", "desatualizado"],
  HISTORICO_ROTULO: ["elegivel", "inelegivel", "insuficiente", "nunca_medido", "aposentado"],
  ENTRADA_AUTO: ["regra", "contraste", "por_setup_disponivel", "por_setup_bloqueado"],
};

const paresPorDictModo = {}; // paresPorDictModo[NOME][modoPy] = {chave: valor}

if (skillRefSrc) {
  for (const nome of DICTS) {
    const blocoDict = blocoDoDict(skillRefSrc, nome);
    ok(`skill_ref.py: bloco "${nome} = {...}" encontrado`, !!blocoDict);
    paresPorDictModo[nome] = {};
    for (const modoPy of ["operador", "educacional"]) {
      const blocoModo = blocoDict ? blocoDoModo(blocoDict, modoPy) : null;
      const pares = blocoModo ? paresDoModo(blocoModo) : {};
      const nChaves = Object.keys(pares).length;
      // parse mudo é a falha silenciosa que este guardião não pode deixar passar.
      ok(`skill_ref.py: ${nome}["${modoPy}"] parseado com >0 chaves`, nChaves > 0);
      paresPorDictModo[nome][modoPy] = pares;

      const chaveJs = CHAVE_JS[nome];
      const modoJs = MODO_JS[modoPy];
      const objJs = (COPY[modoJs] && COPY[modoJs][chaveJs]) || {};

      // 1) conjunto de chaves idêntico entre Python e JS.
      const chavesPy = Object.keys(pares).sort().join(",");
      const chavesJsStr = Object.keys(objJs).sort().join(",");
      ok(`${nome}["${modoPy}"] ↔ COPY.${modoJs}.${chaveJs}: mesmo conjunto de chaves`,
         chavesPy === chavesJsStr, `python={${chavesPy}} js={${chavesJsStr}}`);

      // 2) cada chave: string idêntica byte a byte.
      for (const chave of Object.keys(pares)) {
        ok(`${nome}["${modoPy}"].${chave} idêntico byte a byte (python ↔ js)`,
           objJs[chave] === pares[chave],
           `python="${pares[chave]}" js="${objJs[chave]}"`);
      }

      // 3) conjunto de chaves exato (contrato do 08-UI-SPEC.md).
      const esperado = CHAVES_ESPERADAS[nome].slice().sort().join(",");
      ok(`${nome}["${modoPy}"]: conjunto de chaves é exatamente o esperado`,
         chavesPy === esperado, `real={${chavesPy}} esperado={${esperado}}`);
    }
  }

  // 4) contraste tem os dois números JUNTOS, nos dois modos, nos dois arquivos —
  // nunca o filtrado (positivo) sozinho.
  for (const modoPy of ["operador", "educacional"]) {
    const contrastePy = paresPorDictModo.ENTRADA_AUTO[modoPy].contraste || "";
    const modoJs = MODO_JS[modoPy];
    const contrasteJs = (COPY[modoJs] && COPY[modoJs].entradaAuto && COPY[modoJs].entradaAuto.contraste) || "";
    ok(`ENTRADA_AUTO["${modoPy}"].contraste (python) tem os dois números juntos`,
       contrastePy.includes("−0,099R") && contrastePy.includes("+0,005R"));
    ok(`COPY.${modoJs}.entradaAuto.contraste (js) tem os dois números juntos`,
       contrasteJs.includes("−0,099R") && contrasteJs.includes("+0,005R"));
  }

  // 5) App.jsx NÃO contém, como literal, nenhum valor do vocabulário novo —
  // texto sensível só pode viver em copy.js.
  for (const nome of DICTS) {
    for (const modoPy of ["operador", "educacional"]) {
      for (const [chave, valor] of Object.entries(paresPorDictModo[nome][modoPy])) {
        if (!valor || valor.trim() === "{" + chave + "}") continue; // ignora placeholder puro
        ok(`App.jsx não hardcoda ${nome}["${modoPy}"].${chave}`, !app.includes(valor));
      }
    }
  }

  // 6) por_setup_disponivel/por_setup_bloqueado preservam os placeholders —
  // apagar um dos dois lados passaria pela comparação de bytes e viraria
  // texto genérico, sem nomear o setup.
  for (const modoPy of ["operador", "educacional"]) {
    const disponivelPy = paresPorDictModo.ENTRADA_AUTO[modoPy].por_setup_disponivel || "";
    const bloqueadoPy = paresPorDictModo.ENTRADA_AUTO[modoPy].por_setup_bloqueado || "";
    const modoJs = MODO_JS[modoPy];
    const ea = (COPY[modoJs] && COPY[modoJs].entradaAuto) || {};
    ok(`ENTRADA_AUTO["${modoPy}"].por_setup_disponivel (python) tem {setup} e {janelaRef}`,
       disponivelPy.includes("{setup}") && disponivelPy.includes("{janelaRef}"));
    ok(`ENTRADA_AUTO["${modoPy}"].por_setup_bloqueado (python) tem {setup}`,
       bloqueadoPy.includes("{setup}"));
    ok(`COPY.${modoJs}.entradaAuto.por_setup_disponivel (js) tem {setup} e {janelaRef}`,
       (ea.por_setup_disponivel || "").includes("{setup}") && (ea.por_setup_disponivel || "").includes("{janelaRef}"));
    ok(`COPY.${modoJs}.entradaAuto.por_setup_bloqueado (js) tem {setup}`,
       (ea.por_setup_bloqueado || "").includes("{setup}"));
  }
}

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
