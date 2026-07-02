// Cálculos financeiros determinísticos (sem IA, sem rede) — FONTE ÚNICA usada
// pela Home/Topbar, Carteira e Evolução, para que os números BATAM entre si.
//
// Definições adotadas (Objetivo 3 — auditoria de KPIs):
//  • Preço de marcação: cotação ao vivo quando disponível (> 0); senão, o preço
//    médio da posição (`avg`) como piso estável — evita "tela piscando" para 0
//    enquanto as cotações não chegaram. Em regime (cotações carregadas) o
//    resultado é idêntico ao anterior.
//  • Patrimônio = caixa + Σ (qty × preço).
//  • Resultado aberto (P&L) = Σ (preço − avg) × qty ; % sobre o CUSTO.
//  • Retorno do dia (R$) = Σ qty × preço × (variação%_do_ativo / 100), contando
//    apenas posições com cotação real (com `change`).
//  • Retorno acumulado: base = ORÇAMENTO INICIAL (`initialBudget`). A curva começa
//    no orçamento e termina no patrimônio AO VIVO — assim o número exibido e a
//    curva são o MESMO valor. (Se não houver orçamento, cai para o 1º snapshot.)
//  • Drawdown = maior queda percentual desde o pico, sobre a MESMA curva exibida.

export function markPrice(quote, position) {
  const px = quote && typeof quote.price === "number" && quote.price > 0 ? quote.price : null;
  if (px != null) return px;
  const avg = position && typeof position.avg === "number" ? position.avg : 0;
  return avg;
}

export function portfolioMetrics(positions, quotes, cash) {
  const ps = Array.isArray(positions) ? positions : [];
  const q = quotes || {};
  let posVal = 0, cost = 0, openPnL = 0, dayVal = 0;
  for (const p of ps) {
    const qty = Number(p && p.qty) || 0;
    const quote = q[p && p.t] || {};
    const price = markPrice(quote, p);
    const avg = Number(p && p.avg) || 0;
    posVal += qty * price;
    cost += qty * avg;
    openPnL += (price - avg) * qty;
    if (typeof quote.price === "number" && quote.price > 0 && typeof quote.change === "number") {
      dayVal += qty * quote.price * (quote.change / 100);
    }
  }
  const c = Number(cash) || 0;
  const patr = c + posVal;
  const openPct = cost > 0 ? (openPnL / cost) * 100 : 0;
  return { posVal, cost, openPnL, openPct, dayVal, patr, cash: c };
}

// Retorno do dia em %: variação do patrimônio no dia sobre a base de ontem
// (patr − ganho_do_dia). Seguro contra base <= 0.
export function dayReturnPct(patr, dayVal) {
  const base = patr - dayVal;
  return base > 0 ? (dayVal / base) * 100 : 0;
}

// Curva de capital + retorno acumulado + drawdown, todos consistentes entre si.
// snapshots: [{ data:"YYYY-MM-DD", patrimonio:number }, ...]
export function equityCurve(snapshots, budget, livePatr, todayYmd) {
  const snaps = (Array.isArray(snapshots) ? snapshots : []).filter(
    (s) => s && typeof s.patrimonio === "number" && isFinite(s.patrimonio)
  );
  const series = snaps.map((s) => s.patrimonio);
  const b = Number(budget) || 0;
  const base = b > 0 ? b : (series.length ? series[0] : (Number(livePatr) || 0));

  // série de exibição: baseline (orçamento) → snapshots, com o ÚLTIMO ponto
  // refletindo o patrimônio AO VIVO (substitui o snapshot de hoje; senão anexa).
  let plot = series.slice();
  if (livePatr != null && isFinite(livePatr)) {
    const last = snaps[snaps.length - 1];
    if (last && todayYmd && last.data === todayYmd && plot.length) {
      plot[plot.length - 1] = livePatr;
    } else {
      plot.push(livePatr);
    }
  }
  const curve = b > 0 ? [base, ...plot] : plot;
  const end = curve.length ? curve[curve.length - 1] : base;
  const retAcum = base > 0 ? ((end - base) / base) * 100 : 0;

  let peak = curve.length ? curve[0] : 0, dd = 0;
  for (const v of curve) {
    if (v > peak) peak = v;
    if (peak > 0) { const d = ((peak - v) / peak) * 100; if (d > dd) dd = d; }
  }
  return { curve, series, days: series.length, retAcum, drawdown: dd, base, end };
}
