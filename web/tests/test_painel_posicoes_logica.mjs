// 2026-10-13 (quick 261013-svo) — contadores de atenção, filtro e "Hoje" do painel de Posições (puro).
import * as P from "../src/painelPosicoes.js";
import { cotacaoDoDiaValida, portfolioMetrics, dayReturnPct } from "../src/finance.js";
import { NIVEIS_ATENCAO } from "../src/listaPosicoes.js";

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond ? "" : " — " + (extra || "")));
  if (!cond) fails++;
};
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

ok("exporta 6 símbolos", P.CHAVE_NIVEL && P.NIVEIS_PAINEL && ["resumoAtencao", "filtroVigente", "filtrarPorNivel", "painelHoje"].every((k) => typeof P[k] === "function"));
ok("NIVEIS_PAINEL = RISCO..LEITURA_INDISPONIVEL (DEMAIS fora)", eq([...P.NIVEIS_PAINEL], [0, 1, 2, 3, 4, 5]) && !P.NIVEIS_PAINEL.includes(NIVEIS_ATENCAO.DEMAIS));
ok("CHAVE_NIVEL", eq(P.CHAVE_NIVEL, { 0: "atn_risco", 1: "atn_perto_stop", 2: "atn_vence", 3: "atn_sem_plano", 4: "atn_perto_alvo", 5: "atn_sem_leitura" }));
ok("cotacaoDoDiaValida exportada de finance.js", typeof cotacaoDoDiaValida === "function");
ok("cotacaoDoDiaValida: tabela", cotacaoDoDiaValida({ price: 10, change: 0 }) === true && cotacaoDoDiaValida({ price: 0, change: 1 }) === false
  && cotacaoDoDiaValida({ change: 1 }) === false && cotacaoDoDiaValida({ price: 10, change: "1" }) === false && cotacaoDoDiaValida(null) === false && cotacaoDoDiaValida(undefined) === false);

// --- resumoAtencao
const L = (t, nivel, lendo = false) => ({ t, nivel, lendo });
let r = P.resumoAtencao([L("A", 0), L("B", 0), L("C", 3), L("D", 6)]);
ok("contagem 0,0,3,6 -> [{0,2},{3,1}]", r.estado === "ok" && eq(r.grupos, [{ nivel: 0, n: 2 }, { nivel: 3, n: 1 }]), JSON.stringify(r));
r = P.resumoAtencao([L("A", 4), L("B", 1), L("C", 4)]);
ok("ordem crescente de nível (RISCO primeiro)", eq(r.grupos, [{ nivel: 1, n: 1 }, { nivel: 4, n: 2 }]));
ok("só DEMAIS -> nenhum", P.resumoAtencao([L("A", 6), L("B", 6)]).estado === "nenhum");
ok("uma linha lendo -> lendo", P.resumoAtencao([L("A", 0), L("B", 6, true)]).estado === "lendo");
ok("vazio -> nenhum", P.resumoAtencao([]).estado === "nenhum");
ok("não-array -> nenhum", P.resumoAtencao(null).estado === "nenhum" && P.resumoAtencao(undefined).estado === "nenhum");

// --- filtroVigente
const resOk = P.resumoAtencao([L("A", 0), L("B", 3)]);
ok("filtroVigente nível presente", P.filtroVigente(3, resOk) === 3);
ok("filtroVigente nível 0 presente (zero não é falsy aqui)", P.filtroVigente(0, resOk) === 0);
ok("filtroVigente nível ausente -> null", P.filtroVigente(1, resOk) === null);
ok("filtroVigente com lendo -> null", P.filtroVigente(0, { estado: "lendo" }) === null);
ok("filtroVigente com nenhum -> null", P.filtroVigente(0, { estado: "nenhum" }) === null);
ok("filtroVigente null -> null", P.filtroVigente(null, resOk) === null);

// --- filtrarPorNivel
{
  const linhas = [L("A", 0), L("B", 3), L("C", 0)];
  const antes = JSON.stringify(linhas);
  const f = P.filtrarPorNivel(linhas, 0);
  ok("filtrarPorNivel filtra", eq(f.map((l) => l.t), ["A", "C"]));
  const todas = P.filtrarPorNivel(linhas, null);
  ok("filtrarPorNivel null devolve cópia inteira", eq(todas, linhas) && todas !== linhas);
  ok("filtrarPorNivel não muta", JSON.stringify(linhas) === antes);
}

// --- painelHoje
const rotulo = (s) => (s === "yahoo" ? "Yahoo" : s === "brapi" ? "brapi" : s);
const pos = (t, qty = 100, avg = 10) => ({ t, qty, avg });
const positions = [pos("A"), pos("B"), pos("C"), pos("D"), pos("E")];
const quotes = {
  A: { price: 10, change: 3, source: "yahoo" },
  B: { price: 20, change: 1, source: "yahoo" },
  C: { price: 30, change: -2, source: "yahoo" },
  D: { price: 40, change: 0, source: "yahoo" },
  // E sem cotação
};
const m = portfolioMetrics(positions, quotes, 1000, 0, [], {});
let h = P.painelHoje({ positions, quotes, patr: m.patr, dayVal: m.dayVal, rotuloFonte: rotulo });
ok("altas [+3,+1]", eq(h.altas, [{ t: "A", change: 3 }, { t: "B", change: 1 }]), JSON.stringify(h.altas));
ok("baixas [-2]; change 0 fora", eq(h.baixas, [{ t: "C", change: -2 }]));
ok("semCotacao [E] e texto", eq(h.semCotacao, ["E"]) && h.semCotacaoTxt === "E");
ok("dia.pct === dayReturnPct(patr, dayVal)", h.dia && h.dia.valor === m.dayVal && h.dia.pct === dayReturnPct(m.patr, m.dayVal));
ok("fontes distintas -> uma", eq(h.fontes, ["yahoo"]) && h.tipoFonte === "uma" && h.fontesTxt === "Yahoo");

h = P.painelHoje({ positions, quotes, patr: m.patr, dayVal: m.dayVal, rotuloFonte: rotulo, n: 1 });
ok("n=1 corta", h.altas.length === 1 && h.altas[0].t === "A" && h.baixas.length === 1);

h = P.painelHoje({ positions: [pos("A"), pos("B")], quotes: { A: { price: 10, change: 1, source: "brapi" }, B: { price: 10, change: 1, source: "yahoo" } }, patr: 1000, dayVal: 2, rotuloFonte: rotulo });
ok("fontes brapi+yahoo -> varias", h.tipoFonte === "varias" && h.fontesTxt === "brapi, Yahoo" && eq(h.fontes, ["brapi", "yahoo"]));

h = P.painelHoje({ positions: [pos("A")], quotes: {}, patr: 1000, dayVal: 0, rotuloFonte: rotulo });
ok("nenhuma cotação -> dia null, tipoFonte nenhuma", h.dia === null && h.tipoFonte === "nenhuma" && h.fontesTxt === "" && eq(h.semCotacao, ["A"]));

h = P.painelHoje({ positions: [pos("A"), pos("B")], quotes: { A: { price: 10, change: 1 }, B: { price: 10, change: 2, source: "" } }, patr: 1000, dayVal: 3, rotuloFonte: rotulo });
ok("válidas sem source -> nenhuma fonte informada", h.tipoFonte === "nenhuma" && h.dia !== null);

h = P.painelHoje({ positions: [pos("A"), pos("B")], quotes: { A: { price: 10, change: 2 }, B: { price: 10, change: 2 } }, patr: 1000, dayVal: 4, rotuloFonte: rotulo });
ok("empate de change ordena por ticker", eq(h.altas.map((x) => x.t), ["A", "B"]));

// W1: paridade — cada ticker "válido" de painelHoje contribui para portfolioMetrics.dayVal e os demais não
{
  const ps = [pos("V1"), pos("V2"), pos("Z"), pos("S"), pos("X"), pos("N")];
  const qs = {
    V1: { price: 10, change: 2, source: "yahoo" },
    V2: { price: 20, change: -1, source: "yahoo" },
    Z: { price: 0, change: 5 },
    S: { change: 5 },
    X: { price: 10, change: "5" },
    // N sem cotação
  };
  const base = portfolioMetrics(ps, qs, 0, 0, [], {});
  const h2 = P.painelHoje({ positions: ps, quotes: qs, patr: base.patr, dayVal: base.dayVal, rotuloFonte: rotulo });
  const validos = ps.map((p) => p.t).filter((t) => !h2.semCotacao.includes(t));
  ok("W1: válidos de painelHoje = predicado de finance.js", eq(validos, ps.map((p) => p.t).filter((t) => cotacaoDoDiaValida(qs[t]))) && eq(validos, ["V1", "V2"]));
  const dayDe = (lista) => portfolioMetrics(lista, qs, 0, 0, [], {}).dayVal;
  const contribui = (t) => dayDe(ps) !== dayDe(ps.filter((p) => p.t !== t));
  ok("W1: só os válidos contribuem para dayVal", ps.every((p) => contribui(p.t) === validos.includes(p.t)));
  ok("W1: ranking contém só válidos", h2.altas.every((a) => validos.includes(a.t)) && h2.baixas.every((a) => validos.includes(a.t)));
}

process.exit(fails ? 1 : 0);
