// Objetivo 3 — trava as fórmulas financeiras sobre entradas conhecidas.
import { portfolioMetrics, dayReturnPct, equityCurve, markPrice, historicoEstado, historicoDesatualizado } from "../src/finance.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };
const near = (a, b, eps = 1e-9) => Math.abs(a - b) <= eps;

// ---- markPrice ----
ok("markPrice usa cotação > 0", markPrice({ price: 30 }, { avg: 25 }) === 30);
ok("markPrice cai para avg sem cotação", markPrice({}, { avg: 25 }) === 25);
ok("markPrice cai para avg com price 0", markPrice({ price: 0 }, { avg: 25 }) === 25);
ok("markPrice 0 sem avg", markPrice({}, {}) === 0);

// ---- portfolioMetrics ----
{
  const positions = [
    { t: "PETR4", qty: 100, avg: 30 },   // cotação 33 (+2% no dia)
    { t: "VALE3", qty: 50, avg: 60 },    // cotação 54 (-1% no dia)
  ];
  const quotes = {
    PETR4: { price: 33, change: 2 },
    VALE3: { price: 54, change: -1 },
  };
  const m = portfolioMetrics(positions, quotes, 1000);
  // posVal = 100*33 + 50*54 = 3300 + 2700 = 6000
  ok("posVal", near(m.posVal, 6000));
  // cost = 100*30 + 50*60 = 3000 + 3000 = 6000
  ok("cost", near(m.cost, 6000));
  // openPnL = (33-30)*100 + (54-60)*50 = 300 - 300 = 0
  ok("openPnL", near(m.openPnL, 0));
  ok("openPct = 0 (pnl 0)", near(m.openPct, 0));
  // patr = 1000 + 6000 = 7000
  ok("patr", near(m.patr, 7000));
  // dayVal = 100*33*0.02 + 50*54*(-0.01) = 66 - 27 = 39
  ok("dayVal", near(m.dayVal, 39));
}
{
  // sem cotação: marca por avg → posVal = cost, pnl 0, day 0
  const m = portfolioMetrics([{ t: "ITUB4", qty: 10, avg: 20 }], {}, 500);
  ok("sem cotação: posVal = qty*avg", near(m.posVal, 200));
  ok("sem cotação: openPnL 0", near(m.openPnL, 0));
  ok("sem cotação: dayVal 0", near(m.dayVal, 0));
  ok("patr = caixa + custo", near(m.patr, 700));
}
{
  // bordas: vazio, avg 0 (sem div/0), valores nulos
  const m = portfolioMetrics([], {}, 0);
  ok("vazio: tudo 0", m.posVal === 0 && m.patr === 0 && m.openPct === 0);
  const m2 = portfolioMetrics([{ t: "X", qty: 5, avg: 0 }], { X: { price: 10, change: 1 } }, 0);
  ok("avg 0: openPct 0 (sem div/0)", m2.openPct === 0 && isFinite(m2.openPnL));
  const m3 = portfolioMetrics([{ t: "Y", qty: null, avg: null }], { Y: {} }, null);
  ok("nulos: sem NaN", isFinite(m3.posVal) && isFinite(m3.patr) && isFinite(m3.openPnL));
}

// ---- portfolioMetrics: caixa reservado (Fase 2, MERC-02..04, D-05) ----
{
  // retrocompatibilidade: chamada com 3 argumentos (todos os call sites
  // antigos) devolve EXATAMENTE os mesmos números de antes.
  const positions = [{ t: "PETR4", qty: 100, avg: 30 }];
  const quotes = { PETR4: { price: 33, change: 2 } };
  const m3 = portfolioMetrics(positions, quotes, 1000);
  ok("3 argumentos: retrocompatibilidade (patr sem reservado)", near(m3.patr, 1000 + 3300));
}
{
  // conservação: caixa 10000 sem posições, patr == 10000; reservar 3000 numa
  // ordem pendente (cash vira 7000, reservado 3000) não pode encolher o
  // patrimônio exibido — dinheiro simulado não pode sumir da tela (D-05).
  const antes = portfolioMetrics([], {}, 10000);
  ok("conservação: antes da reserva, patr = caixa", near(antes.patr, 10000));
  const depois = portfolioMetrics([], {}, 7000, 3000);
  ok("conservação: depois da reserva, patr = caixa + reservado (dinheiro não some)", near(depois.patr, 10000));
  ok("reservado exposto no retorno", near(depois.reservado, 3000));
}
{
  // 4º argumento com posições: patr = cash + reservado + posVal
  const positions = [{ t: "VALE3", qty: 50, avg: 60 }];
  const quotes = { VALE3: { price: 54, change: -1 } };
  const m = portfolioMetrics(positions, quotes, 5000, 1200);
  // posVal = 50*54 = 2700
  ok("4 argumentos com posições: patr = cash + reservado + posVal", near(m.patr, 5000 + 1200 + 2700));
  ok("reservado exposto", near(m.reservado, 1200));
}
{
  // reservado inválido é tratado como 0, nunca NaN/Infinity
  for (const invalido of [undefined, null, NaN, "abc"]) {
    const m = portfolioMetrics([], {}, 1000, invalido);
    ok("reservado inválido (" + String(invalido) + ") vira 0", m.patr === 1000 && isFinite(m.patr) && m.reservado === 0);
  }
}
{
  // cost/openPnL/openPct/dayVal NÃO mudam com reservado — caixa reservado
  // não é posição e não tem preço de marcação.
  const positions = [{ t: "ITUB4", qty: 10, avg: 20 }];
  const quotes = { ITUB4: { price: 25, change: 3 } };
  const semReservado = portfolioMetrics(positions, quotes, 500);
  const comReservado = portfolioMetrics(positions, quotes, 500, 2000);
  ok("cost inalterado por reservado", near(comReservado.cost, semReservado.cost));
  ok("openPnL inalterado por reservado", near(comReservado.openPnL, semReservado.openPnL));
  ok("openPct inalterado por reservado", near(comReservado.openPct, semReservado.openPct));
  ok("dayVal inalterado por reservado", near(comReservado.dayVal, semReservado.dayVal));
}

// ---- dayReturnPct ----
ok("dayReturnPct base normal", near(dayReturnPct(1039, 39), (39 / 1000) * 100));
ok("dayReturnPct base <= 0 → 0", dayReturnPct(0, 0) === 0);

// ---- equityCurve: consistência com 'vs início' ----
{
  const budget = 10000;
  const snaps = [
    { data: "2026-06-28", patrimonio: 10000 },
    { data: "2026-06-29", patrimonio: 10500 },
    { data: "2026-06-30", patrimonio: 10300 }, // hoje (será substituído pelo ao vivo)
  ];
  const livePatr = 10600; // ao vivo agora
  const ec = equityCurve(snaps, budget, livePatr, "2026-06-30");
  // base = orçamento; fim = ao vivo → retAcum = (10600-10000)/10000 = 6%
  ok("retAcum base orçamento = vs início", near(ec.retAcum, 6));
  // curva começa no orçamento e termina no ao vivo
  ok("curva começa no orçamento", ec.curve[0] === 10000);
  ok("curva termina no ao vivo", ec.curve[ec.curve.length - 1] === 10600);
  ok("dias = nº de snapshots (não conta baseline)", ec.days === 3);
  // pico = 10600; vale após pico não há → dd a partir do trajeto:
  // curva = [10000,10000,10500,10600] → sem queda desde o pico → dd 0
  ok("drawdown 0 em curva monotônica no fim", near(ec.drawdown, 0));
}
{
  // drawdown real: sobe a 12000 e cai a 9000
  const ec = equityCurve(
    [{ data: "d1", patrimonio: 10000 }, { data: "d2", patrimonio: 12000 }, { data: "d3", patrimonio: 9000 }],
    10000, 9000, "d3"
  );
  // curva = [10000, 10000, 12000, 9000]; pico 12000 → (12000-9000)/12000 = 25%
  ok("drawdown desde o pico = 25%", near(ec.drawdown, 25));
  ok("retAcum = (9000-10000)/10000 = -10%", near(ec.retAcum, -10));
}
{
  // sem orçamento: base = 1º snapshot
  const ec = equityCurve([{ data: "d1", patrimonio: 5000 }], 0, 5500, "d2");
  // base 5000; curva [5000, 5500] (append, pois snapshot não é de "d2")
  ok("sem orçamento: base = 1º snapshot", ec.base === 5000);
  ok("sem orçamento: retAcum (5500-5000)/5000 = 10%", near(ec.retAcum, 10));
}
{
  // estados vazios não produzem NaN/Infinity
  const ec = equityCurve([], 10000, 10000, "d");
  ok("vazio+orçamento: curva [orçamento, ao vivo]", ec.curve.length === 2 && ec.curve[0] === 10000);
  ok("vazio: retAcum finito", isFinite(ec.retAcum) && ec.retAcum === 0);
  const ec2 = equityCurve(null, 0, null, null);
  ok("tudo nulo: sem NaN", isFinite(ec2.retAcum) && isFinite(ec2.drawdown));
}

// ---- historicoEstado (ADR-017 Bloco 3, Plano 08-03) ----
// precedência: aposentado > insuficiente > elegivel/inelegivel > nunca_medido
ok("aposentado tem precedência sobre elegivel false", historicoEstado({ elegivel: false }, true) === "aposentado");
ok("aposentado tem precedência mesmo sem historico", historicoEstado(null, true) === "aposentado");
ok("nunca_medido: historico null", historicoEstado(null) === "nunca_medido");
ok("nunca_medido: historico undefined", historicoEstado(undefined) === "nunca_medido");
ok("nunca_medido: entrada malformada (string vazia)", historicoEstado("") === "nunca_medido");
ok("nunca_medido: entrada malformada (número no lugar de objeto)", historicoEstado(42) === "nunca_medido");
ok("insuficiente: insuficiente=true explícito", historicoEstado({ insuficiente: true, elegivel: null }) === "insuficiente");
ok("insuficiente: elegivel null (fora da janela)", historicoEstado({ elegivel: null }) === "insuficiente");
ok("insuficiente: objeto vazio (elegivel undefined)", historicoEstado({}) === "insuficiente");
ok("elegivel: elegivel true", historicoEstado({ elegivel: true, insuficiente: false }) === "elegivel");
ok("inelegivel: elegivel false, insuficiente false", historicoEstado({ elegivel: false, insuficiente: false }) === "inelegivel");

// ---- historicoDesatualizado (ADR-017 Bloco 3, Plano 08-03) ----
ok("sem carimbo nenhum: não degrada (ausência de evidência não é evidência de atraso)",
  historicoDesatualizado({}, "2026-08-17") === false);
ok("sexta → segunda: 1 dia útil, fim de semana não envelhece o dado",
  historicoDesatualizado({ medidoAte: "2026-08-14" }, "2026-08-17") === false);
ok("data no futuro: nunca degrada",
  historicoDesatualizado({ medidoAte: "2026-08-20" }, "2026-08-17") === false);
ok("calculadoEm sem medidoAte, além do limite de 2 dias úteis: degrada",
  historicoDesatualizado({ medidoAte: null, calculadoEm: "2026-08-12T10:00:00Z" }, "2026-08-17") === true);
ok("medidoAte além do limite de 2 dias úteis: degrada",
  historicoDesatualizado({ medidoAte: "2026-08-12" }, "2026-08-17") === true);
ok("data malformada (número no lugar de string): não degrada, sem exceção",
  historicoDesatualizado({ medidoAte: 20260812 }, "2026-08-17") === false);

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DE FINANCE PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
