// Mapeamento tela do app -> tela do guia (quick 261012-09v). Puro, roda sem build:
// `node web/tests/test_guia_mapa.mjs`. A tabela esperada é LITERAL aqui (não derivada da
// implementação): tela nova em web/src/telas.js ou nível novo em navOpcoes.js reprova até
// ganhar decisão explícita em GUIA_DA_TELA_APP / GUIA_DO_NIVEL_OPCOES.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { TELAS, idsDasTelas } from "../src/telas.js";
import { NIVEIS } from "../src/opcoes/navOpcoes.js";
import { parseTelasData } from "../src/guiaDados.js";
import {
  guiaIdDaTelaApp, novaAberturaBoris, ABERTURA_PRIMEIRO_USO, GUIA_DA_TELA_APP, GUIA_DO_NIVEL_OPCOES,
  estadoInicialGuia, proximo, anterior,
} from "../src/guiaNav.js";

const here = dirname(fileURLToPath(import.meta.url));
let fails = 0;
const ok = (name, cond, extra) => { console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra)); if (!cond) fails++; };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

const guia = parseTelasData(readFileSync(join(here, "..", "..", "site", "js", "telas-data.js"), "utf8"));
const idsGuia = new Set(guia.map((t) => t.id));
const idx = (id) => guia.findIndex((t) => t.id === id);

// 1) toda entrada de TELAS x modo
const ESPERADO_TELA = { evolucao: "acomp", radar: "radar", mercado: "watch", carteira: "port", agente: "opia", historico: null, perfil: null, opcoes: "opc" };
for (const t of TELAS) {
  for (const operador of [false, true]) {
    const r = guiaIdDaTelaApp({ tab: t.subtelaDe || t.id, carteiraView: t.carteiraView || "main", opcoesNivel: "hub", operador });
    ok(`${t.id} (${operador ? "Operador" : "Estudo"}) -> ${ESPERADO_TELA[t.id]}`, r === ESPERADO_TELA[t.id], String(r));
  }
}
ok("a tabela esperada cobre exatamente os ids de TELAS", eq(Object.keys(ESPERADO_TELA).sort(), idsDasTelas().sort()));
ok("GUIA_DA_TELA_APP tem exatamente os ids de TELAS", eq(Object.keys(GUIA_DA_TELA_APP).sort(), idsDasTelas().sort()));

// 2) níveis de Opções x modo
const ESPERADO_NIVEL = { hub: ["opc", "opc"], objetivo: ["opcobj", "opcobj"], escada: ["opcpiso", "opcpiso"], confirmar: ["confest", "opcaberta"], montar: ["opc", "opc"] };
ok("a tabela de níveis cobre exatamente NIVEIS", eq(Object.keys(ESPERADO_NIVEL).sort(), [...NIVEIS].sort()));
ok("GUIA_DO_NIVEL_OPCOES cobre NIVEIS", NIVEIS.every((n) => n in GUIA_DO_NIVEL_OPCOES));
for (const n of NIVEIS) {
  const [est, ope] = ESPERADO_NIVEL[n];
  ok(`opcoes/${n} Estudo -> ${est}`, guiaIdDaTelaApp({ tab: "opcoes", opcoesNivel: n, operador: false }) === est);
  ok(`opcoes/${n} Operador -> ${ope}`, guiaIdDaTelaApp({ tab: "opcoes", opcoesNivel: n, operador: true }) === ope);
}
ok("nível desconhecido cai em opc", guiaIdDaTelaApp({ tab: "opcoes", opcoesNivel: "xyz", operador: false }) === "opc" && guiaIdDaTelaApp({ tab: "opcoes", operador: true }) === "opc");
ok("tab desconhecida -> null", guiaIdDaTelaApp({ tab: "nao-existe" }) === null && guiaIdDaTelaApp() === null && guiaIdDaTelaApp({ tab: "__proto__" }) === null);
ok("carteira/agente e carteira/historico", guiaIdDaTelaApp({ tab: "carteira", carteiraView: "agente" }) === "opia" && guiaIdDaTelaApp({ tab: "carteira", carteiraView: "historico" }) === null);

// 3) todo id não nulo existe nos dados reais do guia
const todos = [...Object.values(GUIA_DA_TELA_APP), ...Object.values(GUIA_DO_NIVEL_OPCOES).flatMap((v) => (typeof v === "object" ? Object.values(v) : [v]))].filter(Boolean);
ok("todo id mapeado existe em telas-data.js", todos.every((id) => idsGuia.has(id)), todos.filter((id) => !idsGuia.has(id)).join(","));

// 4) abertura do 1º uso
ok("ABERTURA_PRIMEIRO_USO = boas, sem visão, n 0", ABERTURA_PRIMEIRO_USO.id === "boas" && ABERTURA_PRIMEIRO_USO.visao === false && ABERTURA_PRIMEIRO_USO.n === 0);
ok("boas é a tela 0 do guia", idx("boas") === 0);

// 5) estadoInicialGuia
const vazio = { v: 2, mis: {}, q: {} };
ok("sem abertura: 1ª não concluída (0), sem aviso", eq(estadoInicialGuia(guia, vazio, null), { tela: 0, ponto: 0, semTour: false }));
const prog2 = { v: 2, mis: { boas: true, acomp: true }, q: { boas: true, acomp: true } };
ok("sem abertura: pula as concluídas", eq(estadoInicialGuia(guia, prog2, null), { tela: 2, ponto: 0, semTour: false }));
const todas = { v: 2, mis: Object.fromEntries(guia.map((t) => [t.id, true])), q: Object.fromEntries(guia.map((t) => [t.id, true])) };
ok("todas concluídas: tela 0", eq(estadoInicialGuia(guia, todas, null), { tela: 0, ponto: 0, semTour: false }));
ok("abertura do Bóris com visão: ponto -1 na tela certa", eq(estadoInicialGuia(guia, vazio, { id: "radar", visao: true, n: 1 }), { tela: idx("radar"), ponto: -1, semTour: false }));
ok("abertura visao:false (1º uso): ponto 0", eq(estadoInicialGuia(guia, prog2, ABERTURA_PRIMEIRO_USO), { tela: 0, ponto: 0, semTour: false }));
ok("abertura com id null: 1ª não concluída + semTour", eq(estadoInicialGuia(guia, prog2, { id: null, visao: true, n: 1 }), { tela: 2, ponto: 0, semTour: true }));
ok("abertura com id inexistente: semTour, nunca índice inválido", eq(estadoInicialGuia(guia, vazio, { id: "zzz", visao: true, n: 1 }), { tela: 0, ponto: 0, semTour: true }));
const semVisao = guia.map((t, i) => (i === 3 ? { ...t, visao: undefined } : t));
ok("tela sem visao: abre no ponto 0 (sem cartão vazio)", eq(estadoInicialGuia(semVisao, vazio, { id: guia[3].id, visao: true, n: 1 }), { tela: 3, ponto: 0, semTour: false }));
ok("telas vazias/inválidas não lançam", eq(estadoInicialGuia([], vazio, null), { tela: 0, ponto: 0, semTour: false }) && estadoInicialGuia(null, null, { id: "x", visao: true, n: 1 }).semTour === true);

// 6) novaAberturaBoris: identidade nova a cada abertura (B1)
const a1 = novaAberturaBoris(null, "opcobj");
const a2 = novaAberturaBoris(a1, "opcobj");
ok("novaAberturaBoris: {id, visao:true, n:1}", eq(a1, { id: "opcobj", visao: true, n: 1 }));
ok("novaAberturaBoris: mesmo id -> n cresce", a2.n === 2 && a2.id === "opcobj");
ok("novaAberturaBoris: id nulo vira null", novaAberturaBoris(a2, undefined).id === null && novaAberturaBoris(a2, undefined).n === 3);
// guia já aberto em outro ponto + nova abertura: o estado anterior não vaza
const aberto = { tela: idx("radar"), ponto: 2 };
const reabre = estadoInicialGuia(guia, vazio, novaAberturaBoris(a1, "opcobj"));
ok("reabertura com guia aberto -> ponto -1 da tela nova", eq(reabre, { tela: idx("opcobj"), ponto: -1, semTour: false }) && aberto.ponto === 2);

// 7) ponto -1 na navegação
ok("proximo: -1 -> 0", eq(proximo({ tela: 3, ponto: -1 }, guia), { tela: 3, ponto: 0 }));
ok("anterior: tela 0 ponto -1 devolve o mesmo", eq(anterior({ tela: 0, ponto: -1 }, guia), { tela: 0, ponto: -1 }));
ok("anterior: tela 2 ponto -1 -> Na prática da tela 1", eq(anterior({ tela: 2, ponto: -1 }, guia), { tela: 1, ponto: guia[1].pontos.length }));
ok("anterior: ponto 0 segue indo à tela anterior", eq(anterior({ tela: 2, ponto: 0 }, guia), { tela: 1, ponto: guia[1].pontos.length }));

if (fails) { console.log(`\n${fails} falha(s).`); process.exit(1); }
console.log("\ntodos os testes passaram.");
