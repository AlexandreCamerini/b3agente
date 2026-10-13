// quick 261013-cqk (2026-10-13) — prioridade de atenção e ordenação da lista (puro).
import * as L from "../src/listaPosicoes.js";

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

const P = (o) => ({ t: "UGPA3", qty: 1000, qtyTravada: 0, stop: 10, alvo: 20, ...o });
const est = (o) => ({ estado: "vigente", estadoTexto: "txt", resultado: { incompleto: false }, ...o });
const lp = (o) => ({ preco: 15, posicaoNoPlano: "dentro", ...o });
const pa = (a) => L.prioridadeAtencao(a);

ok("exporta 4 símbolos", L.NIVEIS_ATENCAO && L.CRITERIOS_ORDEM && typeof L.prioridadeAtencao === "function" && typeof L.ordenarLinhas === "function");
ok("CRITERIOS_ORDEM", eq([...L.CRITERIOS_ORDEM], ["atencao", "resultado", "vencimento"]) && Object.isFrozen(L.CRITERIOS_ORDEM));
ok("NIVEIS_ATENCAO congelado", Object.isFrozen(L.NIVEIS_ATENCAO));

let r = pa({ p: P(), estrutura: null, leituraPlano: lp({ posicaoNoPlano: "abaixo_stop" }), situacaoPlano: "ok" });
ok("nível 0 abaixo do stop", r.nivel === 0 && r.chip.tipo === "estado" && r.chip.chave === "estado_abaixo_stop");
r = pa({ p: P(), estrutura: null, leituraPlano: lp({ posicaoNoPlano: "acima_alvo" }), situacaoPlano: "ok" });
ok("nível 0 acima do alvo", r.nivel === 0);
r = pa({ p: P(), estrutura: est({ estado: "vencida", estadoTexto: "Vencida" }), leituraPlano: lp(), situacaoPlano: "ok" });
ok("nível 0 vencida (motor)", r.nivel === 0 && r.chip.chave === "motor");
r = pa({ p: P(), estrutura: est({ estado: "exercicio_provavel", estadoTexto: "Exercício" }), leituraPlano: lp({ proximidade: "perto_stop" }), situacaoPlano: "ok" });
ok("exercício provável + perto_stop -> nível 0", r.nivel === 0 && r.chip.chave === "motor");
r = pa({ p: P(), estrutura: null, leituraPlano: lp({ proximidade: "perto_stop" }), situacaoPlano: "ok" });
ok("nível 1 perto do stop", r.nivel === 1 && r.chip.chave === "estado_perto_stop");
r = pa({ p: P(), estrutura: est(), leituraPlano: lp({ proximidade: "perto_stop" }), situacaoPlano: "ok" });
ok("nível 1 com estrutura vigente", r.nivel === 1);
r = pa({ p: P(), estrutura: est({ estado: "ate_5_dias" }), leituraPlano: lp({ proximidade: "perto_stop" }), situacaoPlano: "ok" });
ok("perto_stop + ate_5_dias -> nível 1, chip perto_stop", r.nivel === 1 && r.chip.chave === "estado_perto_stop");
r = pa({ p: P(), estrutura: est({ estado: "ate_5_dias" }), leituraPlano: lp(), situacaoPlano: "ok" });
ok("nível 2 vence em até 5 dias", r.nivel === 2 && r.chip.tipo === "vencimento");
r = pa({ p: P(), estrutura: est({ estado: "ate_5_dias" }), leituraPlano: lp({ proximidade: "perto_alvo" }), situacaoPlano: "ok" });
ok("perto_alvo + ate_5_dias -> nível 2 vencimento", r.nivel === 2 && r.chip.tipo === "vencimento");
r = pa({ p: P({ stop: null, alvo: null }), estrutura: est({ estado: "ate_5_dias" }), leituraPlano: lp(), situacaoPlano: "ok" });
ok("sem_plano + ate_5_dias -> nível 2", r.nivel === 2);
r = pa({ p: null, estrutura: est({ estado: "ate_5_dias" }), leituraPlano: null, situacaoPlano: "ok" });
ok("avulsa (p nulo) ate_5_dias -> 2", r.nivel === 2 && r.chip.tipo === "vencimento");
r = pa({ p: null, estrutura: est({ estado: "vencida", estadoTexto: "V" }), leituraPlano: null, situacaoPlano: "ok" });
ok("avulsa vencida -> 0", r.nivel === 0);
r = pa({ p: null, estrutura: est(), leituraPlano: null, situacaoPlano: "ok" });
ok("avulsa vigente -> 6, chip null", r.nivel === 6 && r.chip === null);
r = pa({ p: P({ stop: null, alvo: null }), estrutura: null, leituraPlano: lp(), situacaoPlano: "ok" });
ok("nível 3 sem plano", r.nivel === 3 && r.chip.chave === "estado_sem_plano");
r = pa({ p: P({ stop: null }), estrutura: null, leituraPlano: lp(), situacaoPlano: "ok" });
ok("nível 3 falta stop", r.nivel === 3 && r.chip.chave === "estado_falta_stop");
r = pa({ p: P({ alvo: null }), estrutura: null, leituraPlano: lp(), situacaoPlano: "ok" });
ok("nível 3 falta alvo", r.nivel === 3 && r.chip.chave === "estado_falta_alvo");
r = pa({ p: P(), estrutura: null, leituraPlano: lp({ proximidade: "perto_alvo" }), situacaoPlano: "ok" });
ok("nível 4 perto do alvo", r.nivel === 4 && r.chip.chave === "estado_perto_alvo");
r = pa({ p: P(), estrutura: null, leituraPlano: lp({ proximidade: "perto_stop", desatualizada: true }), situacaoPlano: "desatualizada" });
ok("nível 1 suprimido com leitura desatualizada -> nível 5", r.nivel === 5);
r = pa({ p: P(), estrutura: null, leituraPlano: null, situacaoPlano: "carregando" });
ok("nível 5 carregando", r.nivel === 5 && r.chip === null);
r = pa({ p: P(), estrutura: null, leituraPlano: null, situacaoPlano: "falha" });
ok("nível 5 falha", r.nivel === 5);
r = pa({ p: P(), estrutura: null, leituraPlano: lp({ preco: null, posicaoNoPlano: null }), situacaoPlano: "ok" });
ok("nível 5 cotação indisponível", r.nivel === 5 && r.chip.chave === "extra_cotacao_indisponivel");
r = pa({ p: P({ qtyTravada: 1000 }), estrutura: est(), leituraPlano: lp({ proximidade: "perto_stop" }), situacaoPlano: "ok" });
ok("nível 1 suprimido com travadas -> nível 6", r.nivel === 6 && r.chip.chave === "estado_travadas_todas");
r = pa({ p: P(), estrutura: null, leituraPlano: lp(), situacaoPlano: "ok" });
ok("nível 6 dentro do plano", r.nivel === 6 && r.chip.chave === "estado_dentro");
r = pa({ p: P(), estrutura: est(), leituraPlano: lp(), situacaoPlano: "ok" });
ok("nível 6 vigente dentro do plano, chip null", r.nivel === 6 && r.chip === null);
r = pa({});
ok("entrada vazia não quebra", r.nivel === 6);

// ordenação
const ls = [
  { t: "BBB", nivel: 3, resultado: -10, dias: 5 },
  { t: "AAA", nivel: 3, resultado: -10, dias: 5 },
  { t: "CCC", nivel: 0, resultado: null, dias: null },
  { t: "DDD", nivel: 6, resultado: 50, dias: -2 },
  { t: "EEE", nivel: 1, resultado: -200, dias: null },
];
const snap = JSON.stringify(ls);
const ts = (a) => a.map((x) => x.t).join(",");
ok("atencao: nível, depois ticker", ts(L.ordenarLinhas(ls, "atencao")) === "CCC,EEE,AAA,BBB,DDD");
ok("critério inválido == atencao", ts(L.ordenarLinhas(ls, "xyz")) === ts(L.ordenarLinhas(ls, "atencao")) && ts(L.ordenarLinhas(ls)) === ts(L.ordenarLinhas(ls, "atencao")));
ok("resultado: pior no topo, null no fim, empate por ticker", ts(L.ordenarLinhas(ls, "resultado")) === "EEE,AAA,BBB,DDD,CCC");
ok("vencimento: negativa primeiro, null no fim, empate por ticker", ts(L.ordenarLinhas(ls, "vencimento")) === "DDD,AAA,BBB,CCC,EEE");
ok("não muta a entrada", JSON.stringify(ls) === snap);
ok("retorna novo array", L.ordenarLinhas(ls, "atencao") !== ls);
ok("entrada inválida -> []", eq(L.ordenarLinhas(null, "atencao"), []));

process.exit(fails ? 1 : 0);
