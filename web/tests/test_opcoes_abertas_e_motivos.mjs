// Quick 260928-u0h (2026-09-28) — guardião: encerramento não é oportunidade
// confirmada + motivo por posição sem card.
//
// Por que existe: o backend monta a proposta de FECHAMENTO em
// `opcoes_lastreadas.proposta_fechar` (main.py, ramo `pos_op_aberta`) sem
// consultar a leitura técnica; ela aparecia sob "confirmadas pela leitura
// técnica" e o subtítulo mentia. E posição sem card sumia sem explicação.
// Roda isolado: `node web/tests/test_opcoes_abertas_e_motivos.mjs`.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { COPY } from "../src/copy.js";
import {
  classificarOportunidades, temEstruturaAberta, fraseDoMotivo, MOTIVOS_SEM_PROPOSTA,
} from "../src/opcoes/classificarOportunidades.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const conc = (extra) => ({ gate: { liquida: true }, proposta: { proposta: { tipo: "call_coberta", manchete: "x" }, ...(extra || {}) } });
const semP = (motivo) => ({ gate: { liquida: true }, proposta: { proposta: null, motivo } });
const pos = (...ts) => ts.map((t) => ({ t }));
const cls = (o) => classificarOportunidades({ carregando: false, optionPositions: [], ...o });
const tk = (l) => l.map((i) => i.p.t);

// ---- comportamento ---------------------------------------------------------
{
  const r = cls({ propostas: { A: conc() }, positions: pos("A"), optionPositions: [{ underlying: "A", lastro: { qty: 100 } }] });
  ok("A: proposta concreta + estrutura lastreada aberta -> abertas, nunca novas",
    tk(r.abertas).join() === "A" && r.novas.length === 0 && r.semProposta.length === 0);
}
{
  const r = cls({ propostas: { B: conc() }, positions: pos("B") });
  ok("B: proposta concreta sem estrutura aberta -> novas", tk(r.novas).join() === "B" && r.abertas.length === 0);
}
{
  const r = cls({ propostas: { B2: conc() }, positions: pos("B2"), optionPositions: [{ underlying: "B2" }] });
  ok("B2: optionPosition sem lastro NAO conta como aberta (espelho do servidor)", tk(r.novas).join() === "B2" && r.abertas.length === 0);
}
{
  const r = cls({ propostas: { C: { gate: { liquida: false, faixa: "SEM MERCADO" }, proposta: null }, D: { gate: { liquida: false, faixa: "OUTRA" }, proposta: null }, E: { gate: { liquida: false }, proposta: null } }, positions: pos("C", "D", "E") });
  ok("C: gate reprovado SEM MERCADO -> sem_mercado", r.semProposta[0].motivo === "sem_mercado");
  ok("C: gate reprovado outra faixa/ausente -> sem_liquidez", r.semProposta[1].motivo === "sem_liquidez" && r.semProposta[2].motivo === "sem_liquidez");
}
for (const m of ["degradado", "sem_lastro", "sem_setup", "sem_vencimento_elegivel", "sem_contrato_liquido", "caixa_insuficiente"]) {
  const r = cls({ propostas: { X: semP(m) }, positions: pos("X") });
  ok("D: motivo do motor " + m + " preservado", r.semProposta.length === 1 && r.semProposta[0].motivo === m);
}
{
  ok("E: motivo desconhecido -> desconhecido", cls({ propostas: { X: semP("xyz") }, positions: pos("X") }).semProposta[0].motivo === "desconhecido");
  ok("E: motivo ausente -> desconhecido", cls({ propostas: { X: { gate: { liquida: true }, proposta: { proposta: null } } }, positions: pos("X") }).semProposta[0].motivo === "desconhecido");
}
{
  ok("F: optionsProposta falhou (proposta null) -> indisponivel",
    cls({ propostas: { X: { gate: { liquida: true }, proposta: null } }, positions: pos("X") }).semProposta[0].motivo === "indisponivel");
  ok("F: gate null -> indisponivel",
    cls({ propostas: { X: { gate: null, proposta: null } }, positions: pos("X") }).semProposta[0].motivo === "indisponivel");
}
{
  ok("G: sem entrada e nao carregando -> indisponivel", cls({ propostas: {}, positions: pos("X") }).semProposta[0].motivo === "indisponivel");
  const r = cls({ propostas: {}, positions: pos("X"), carregando: true });
  ok("G: sem entrada e carregando -> ausente das tres listas", r.abertas.length + r.novas.length + r.semProposta.length === 0);
}
{
  const oa = [{ underlying: "X", lastro: {} }];
  ok("H: aberta + gate reprovado -> aberta_sem_proposta",
    cls({ propostas: { X: { gate: { liquida: false }, proposta: null } }, positions: pos("X"), optionPositions: oa }).semProposta[0].motivo === "aberta_sem_proposta");
  ok("H: aberta + proposta null -> aberta_sem_proposta",
    cls({ propostas: { X: { gate: { liquida: true }, proposta: null } }, positions: pos("X"), optionPositions: oa }).semProposta[0].motivo === "aberta_sem_proposta");
  ok("H: aberta + motivo degradado -> aberta_sem_proposta",
    cls({ propostas: { X: semP("degradado") }, positions: pos("X"), optionPositions: oa }).semProposta[0].motivo === "aberta_sem_proposta");
}
{
  const r = cls({ propostas: { Z: conc(), Y: conc(), W: conc() }, positions: pos("Z", "Y", "W") });
  ok("ordem de saida = ordem de positions", tk(r.novas).join() === "Z,Y,W");
}
{
  let lancou = false;
  try { classificarOportunidades({}); classificarOportunidades(); } catch (_) { lancou = true; }
  ok("entradas ausentes nunca lancam", !lancou);
  ok("temEstruturaAberta: predicado underlying + lastro",
    temEstruturaAberta([{ underlying: "A", lastro: {} }], "A") && !temEstruturaAberta([{ underlying: "A" }], "A") && !temEstruturaAberta(undefined, "A"));
  const mapa = { sem_lastro: "L", desconhecido: "D" };
  ok("fraseDoMotivo: conhecido, desconhecido e mapa ausente",
    fraseDoMotivo(mapa, "sem_lastro") === "L" && fraseDoMotivo(mapa, "xyz") === "D" && fraseDoMotivo(undefined, "x") === "");
}

// ---- copy ------------------------------------------------------------------
const e = COPY.estudo;
const o = COPY.operador;
const CH_STR = ["tiraOpcoesAbertasTitulo", "tiraOpcoesAbertasSubtitulo", "tiraOpcoesNenhumaNova", "tiraOpcoesMotivosTitulo"];
for (const k of [...CH_STR, "tiraOpcoesMotivo"]) ok("chave " + k + " existe nos dois modos", k in e && k in o);
for (const k of CH_STR) {
  ok(k + " string nao vazia e diferente entre modos",
    typeof e[k] === "string" && e[k].length > 0 && typeof o[k] === "string" && o[k].length > 0 && e[k] !== o[k]);
}
const ke = Object.keys(e.tiraOpcoesMotivo || {}).sort();
const ko = Object.keys(o.tiraOpcoesMotivo || {}).sort();
const kc = [...MOTIVOS_SEM_PROPOSTA].sort();
ok("chaves de tiraOpcoesMotivo identicas nos dois modos e = MOTIVOS_SEM_PROPOSTA (11)",
  ke.join() === ko.join() && ke.join() === kc.join() && kc.length === 11);
ok("cada frase de motivo: string nao vazia e difere entre modos",
  kc.every((m) => typeof e.tiraOpcoesMotivo[m] === "string" && e.tiraOpcoesMotivo[m].length > 0
    && typeof o.tiraOpcoesMotivo[m] === "string" && o.tiraOpcoesMotivo[m].length > 0
    && e.tiraOpcoesMotivo[m] !== o.tiraOpcoesMotivo[m]));
ok("desconhecido diz 'Não há dados suficientes para concluir.' nos dois modos",
  e.tiraOpcoesMotivo.desconhecido.includes("Não há dados suficientes para concluir.")
  && o.tiraOpcoesMotivo.desconhecido.includes("Não há dados suficientes para concluir."));
ok("frases de ESTUDO sem COMPRAR/VENDER", !/COMPRAR|VENDER/i.test(JSON.stringify(e.tiraOpcoesMotivo) + CH_STR.map((k) => e[k]).join(" ")));
ok("nenhuma frase com percentual numerico", !/\d+\s*%/.test(JSON.stringify([e.tiraOpcoesMotivo, o.tiraOpcoesMotivo, CH_STR.map((k) => [e[k], o[k]])])));

// ---- estático: componente e fiação ----------------------------------------
const dir = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "opcoes");
const lerSemComentario = (f) => readFileSync(join(dir, f), "utf8")
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const oo = lerSemComentario("OportunidadesOpcoes.jsx");
const aba = lerSemComentario("AbaOportunidades.jsx");
const tela = lerSemComentario("OpcoesScreen.jsx");
ok("componente importa de ./classificarOportunidades.js", /from "\.\/classificarOportunidades\.js"/.test(oo));
for (const k of ["tiraOpcoesAbertasTitulo", "tiraOpcoesAbertasSubtitulo", "tiraOpcoesMotivosTitulo", "tiraOpcoesMotivo"]) {
  ok("componente referencia cp." + k, oo.includes("cp." + k));
}
ok("abertas nunca sob o titulo de oportunidades confirmadas (Abertas antes de tiraOpcoesTitulo)",
  oo.indexOf("cp.tiraOpcoesAbertasTitulo") > -1 && oo.indexOf("cp.tiraOpcoesAbertasTitulo") < oo.indexOf("cp.tiraOpcoesTitulo"));
ok("{pr.manchete} aparece exatamente 1x", (oo.match(/\{pr\.manchete\}/g) || []).length === 1);
ok("componente sem literal de motivo nem SEM MERCADO",
  !MOTIVOS_SEM_PROPOSTA.some((m) => oo.includes('"' + m + '"') || oo.includes("'" + m + "'")) && !oo.includes("SEM MERCADO"));
ok("AbaOportunidades repassa optionPositions={optionPositions}", aba.includes("optionPositions={optionPositions}"));
ok("OpcoesScreen passa optionPositions= ao <AbaOportunidades",
  /<AbaOportunidades[^>]*optionPositions=/.test(tela) || /<AbaOportunidades[\s\S]*?optionPositions=[\s\S]*?\/>/.test(tela));
ok("OpcoesScreen nao importa App.jsx (ADR-027)", !/from "\.\.\/App/.test(tela));

if (fails) process.exit(1);
