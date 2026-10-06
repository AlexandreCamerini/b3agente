// Guardião — navegação em profundidade da aba Opções (Fase 48, plano 48-03).
// Guardião não se apaga: reversão deliberada atualiza com nota datada.
// Roda isolado: `node web/tests/test_opcoes_nav_profundidade.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import * as N from "../src/opcoes/navOpcoes.js";

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};
const ABAS = ["oportunidades", "recomendadas", "montar"];
const cart = [{ t: "PETR4" }, { t: "VALE3" }];
const ini = (o) => N.estadoInicialOpcoes({ abas: ABAS, abaInicial: null, abrirTicker: null, memoria: null, carteira: cart, ...o });

const h = ini({});
ok("inicial: hub vazio", JSON.stringify(h) === JSON.stringify({ nivel: "hub", ticker: "", objetivo: null, vencimento: null, degrauId: null, unidade: "total" }), JSON.stringify(h));
ok("abrirTicker na carteira -> objetivo", ini({ abrirTicker: "PETR4" }).nivel === "objetivo" && ini({ abrirTicker: "PETR4" }).ticker === "PETR4");
ok("abrirTicker fora da carteira -> hub", ini({ abrirTicker: "ITUB4" }).nivel === "hub");
const m = ini({ abaInicial: "montar", memoria: { ticker: "VALE3", aba: "oportunidades" } });
ok("abaInicial montar -> montar com ticker lembrado", m.nivel === "montar" && m.ticker === "VALE3", JSON.stringify(m));
ok("abaInicial fora da allowlist -> hub", ini({ abaInicial: "xyz" }).nivel === "hub");

const e0 = { ...h, ticker: "PETR4", objetivo: "renda", vencimento: "2026-11-20", degrauId: "x", nivel: "escada" };
const t1 = N.abrirAtivo(e0, "VALE3");
ok("abrirAtivo outro ticker zera escolhas", t1.nivel === "objetivo" && t1.ticker === "VALE3" && t1.objetivo === null && t1.vencimento === null && t1.degrauId === null);
const t2 = N.abrirAtivo(e0, "PETR4");
ok("abrirAtivo mesmo ticker preserva", t2.objetivo === "renda" && t2.vencimento === "2026-11-20" && t2.degrauId === "x" && t2.nivel === "objetivo");

ok("voltar confirmar->escada->objetivo->hub",
  N.voltar({ ...e0, nivel: "confirmar" }).nivel === "escada" && N.voltar(e0).nivel === "objetivo"
  && N.voltar({ ...e0, nivel: "objetivo" }).nivel === "hub");
ok("voltar montar: com ticker -> objetivo; sem -> hub", N.voltar({ ...e0, nivel: "montar" }).nivel === "objetivo" && N.voltar({ ...h, nivel: "montar" }).nivel === "hub");
ok("voltar hub -> hub", N.voltar(h).nivel === "hub");
const v = N.voltar({ ...e0, nivel: "confirmar" });
ok("voltar nunca apaga escolhas", v.objetivo === "renda" && v.vencimento === "2026-11-20" && v.degrauId === "x");

ok("irConfirmar sem degrau é inalterado", N.irConfirmar({ ...e0, degrauId: null }).nivel === "escada");
ok("irConfirmar com degrau avança", N.irConfirmar(e0).nivel === "confirmar");
ok("trocarUnidade só total|acao", N.trocarUnidade(h, "acao").unidade === "acao" && N.trocarUnidade(h, "x").unidade === "total");
ok("escolherObjetivo inválido inalterado", N.escolherObjetivo(e0, "lixo").objetivo === "renda" && N.escolherObjetivo(e0, "lixo").nivel === "escada");
const eo = N.escolherObjetivo({ ...e0, nivel: "objetivo" }, "collar");
ok("escolherObjetivo diferente zera venc/degrau e vai a escada", eo.objetivo === "collar" && eo.vencimento === null && eo.degrauId === null && eo.nivel === "escada");
ok("escolherVencimento diferente zera degrau; igual preserva", N.escolherVencimento(e0, "2026-12-18").degrauId === null && N.escolherVencimento(e0, "2026-11-20").degrauId === "x");
ok("escolherDegrau grava id", N.escolherDegrau(e0, "y").degrauId === "y");
ok("irMontar -> montar", N.irMontar(e0).nivel === "montar");

const dpv = { "2026-11-20": [{ id: "x" }] };
const s1 = N.selecaoDaCelula({ id: "x", vencimento: "2026-11-20" }, dpv);
ok("selecaoDaCelula com par", s1.vencimento === "2026-11-20" && s1.degrauId === "x" && s1.somenteLeitura === false);
const s2 = N.selecaoDaCelula({ id: "z", vencimento: "2026-11-20" }, dpv);
ok("selecaoDaCelula sem par -> somente leitura", s2.degrauId === null && s2.somenteLeitura === true);

const antes = JSON.stringify(e0);
N.abrirAtivo(e0, "VALE3"); N.voltar(e0); N.escolherDegrau(e0, "q"); N.trocarUnidade(e0, "acao");
ok("não muta a entrada", JSON.stringify(e0) === antes);
ok("NIVEIS", N.NIVEIS.join() === "hub,objetivo,escada,confirmar,montar");

const src = readFileSync(fileURLToPath(new URL("../src/opcoes/navOpcoes.js", import.meta.url)), "utf8")
  .split("\n").map((l) => l.replace(/\/\/.*$/, "")).join("\n");
for (const proibido of ["import React", "from \"react\"", "App.jsx", "fetch(", "store."]) {
  ok(`navOpcoes.js não contém ${proibido}`, !src.includes(proibido));
}

console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
