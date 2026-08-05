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
// Roda sem build e sem servidor: `node web/tests/test_vocabulario_espelho.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

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

if (fails) { console.error(`\n${fails} falha(s)`); process.exit(1); }
console.log("\ntodos os testes passaram");
