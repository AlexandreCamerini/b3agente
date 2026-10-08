// Onda F (2026-10-08) — quick 261008-e9w.
// (1) Mesa: decisão do motor "não operar" => sem anel de % nem linha "N% · Forte — …"; CTA secundária.
// (2) Opções: ganho máximo <= 0 sem barra verde; < 0 em T.negative com nota "se exercida: perda".
// (3) Opções: legenda da régua uma vez no hub; "sem piso" sem duplicata.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { opcoesEscadaTxt } from "../src/copy.js";

const here = dirname(fileURLToPath(import.meta.url));
const ler = (p) => readFileSync(join(here, "..", "src", p), "utf8");
let falhas = 0;
const ok = (n, c) => { if (!c) { falhas++; console.error("FALHOU:", n); } else console.log("ok:", n); };

const app = ler("App.jsx");
const esc = ler("opcoes/EscadaObjetivo.jsx");
const hub = ler("opcoes/HubOpcoes.jsx");
const regua = ler("opcoes/ReguaRegime.jsx");
const tela = ler("opcoes/OpcoesScreen.jsx");
const skill = readFileSync(join(here, "..", "..", "server", "app", "skill_ref.py"), "utf8");

// parte 1 — Mesa
ok("lista DECISOES_NAO_OPERAR", /const DECISOES_NAO_OPERAR = \["NÃO OPERAR", "Não operar"\];/.test(app));
ok("lista casa com chaves de REC_STYLE", app.includes('"NÃO OPERAR": [') && app.includes('"Não operar": ['));
ok("ehNaoOperar", /const ehNaoOperar = \(dec\) => DECISOES_NAO_OPERAR\.includes\(dec\);/.test(app));
const ini = app.indexOf("function AtivoCard(");
const corpo = app.slice(ini, app.indexOf("\nfunction ", ini + 10));
ok("AtivoCard: naoOperar", corpo.includes("const naoOperar = ehNaoOperar(decM);"));
ok("AtivoCard: anel nulo sob naoOperar", /const anel = \(sc && !naoOperar\) \? rotuloAnel\(/.test(corpo));
ok("AtivoCard: ring={anel} preservado", corpo.includes("ring={anel}"));
ok("CTA primária só sem naoOperar",
  corpo.includes("...((ehWatchlist && !naoOperar) ? { border: `1px solid ${T.accent}`, background: T.accent"));
ok("texto da CTA inalterado", corpo.includes("{cp.btnComprar}…</button>"));
ok("carrossel do Resumo sem anel sob não operar",
  app.includes("{!ehNaoOperar(decisaoDoModo(r, operador)) && <ConfluenceRing conf={r.confluencia} size={52} />}"));

// parte 2 — barra <= 0
for (const modo of ["educacional", "operador"]) {
  ok(`nota_ganho_negativo (${modo})`, opcoesEscadaTxt(modo, "nota_ganho_negativo") === "se exercida: perda");
}
ok("skill_ref: nota nos dois modos", (skill.match(/"nota_ganho_negativo": "se exercida: perda",/g) || []).length === 2);
ok("semFill", esc.includes('const semFill = sem || (c.sinal === "positivo" && ehNum(v) && v <= 0);'));
ok("perdaNoGanho", esc.includes('const perdaNoGanho = c.sinal === "positivo" && ehNum(v) && v < 0;'));
ok("fill condicionado a semFill", esc.includes("{semFill ? null : (") && !esc.includes("{sem ? null : ("));
ok("valor em T.negative quando perda", esc.includes("color: perdaNoGanho ? T.negative : T.textPrimary"));
ok("nota renderizada", esc.includes('tx("nota_ganho_negativo")'));

// parte 3 — legendas
ok("ReguaRegime aceita semAjuda", regua.includes("export default function ReguaRegime({ regua, cp, semAjuda })") && regua.includes("{semAjuda ? null : ("));
ok("hub: régua dos cards sem legenda", hub.includes("<ReguaRegime regua={dados.regua} cp={cp} semAjuda />"));
ok("hub: legenda única", (hub.match(/cp\.opcoesReguaAjuda/g) || []).length === 1);
ok("detalhe mantém legenda", tela.includes("<ReguaRegime regua={dados.regua} cp={cp} />"));
ok("sem literal 'sem piso: a queda' em opcoes/*.jsx", ![esc, hub, regua, tela].some((s) => s.includes("sem piso: a queda")));
ok("escada não reintroduz rodapé nota_sem_piso", !esc.includes('tx("nota_sem_piso")'));

if (falhas) { console.error(falhas + " falha(s)"); process.exit(1); }
console.log("test_ui_onda_f: ok");
